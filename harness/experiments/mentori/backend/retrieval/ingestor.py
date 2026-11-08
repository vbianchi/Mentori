"""
Document Ingestor for RAG

Orchestrates the full ingestion pipeline:
Parse → Chunk → Embed → Store
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from backend.retrieval.embeddings import EmbeddingEngine
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.chunking import SimpleChunker, MarkdownChunker
from backend.retrieval.semantic_chunker import SemanticChunker
from backend.retrieval.parsers.pdf import PDFParser
from backend.retrieval.parsers.ocr import OCRParser
from backend.retrieval.parsers.tables import TableParser
from backend.retrieval.planner import DocumentAnalyzer
from backend.retrieval.validation import HybridValidator
import tempfile
import aiofiles
import os

logger = logging.getLogger(__name__)


class _SemanticChunkerAdapter:
    """
    Adapter that makes SemanticChunker output compatible with SimpleIngestor.

    SemanticChunker returns: {"text", "page_num", "type", "char_count", ...}
    SimpleIngestor expects:  {"text", "metadata", "tokens"}
    """

    def __init__(self, semantic_chunker):
        self._chunker = semantic_chunker

    def chunk_text(self, text: str, base_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Chunk text and normalize output format for SimpleIngestor."""
        raw_chunks = self._chunker.chunk_with_headings(text)

        normalized = []
        for i, chunk in enumerate(raw_chunks):
            chunk_text = chunk.get("text", "")
            if not chunk_text.strip():
                continue

            # Estimate tokens (~4 chars per token)
            token_estimate = max(1, len(chunk_text) // 4)

            meta = dict(base_metadata or {})
            meta["chunk_index"] = i
            meta["page"] = chunk.get("page_num", 1)
            meta["chunk_type"] = chunk.get("type", "content")
            if chunk.get("section_heading"):
                meta["section_heading"] = chunk["section_heading"]

            normalized.append({
                "text": chunk_text,
                "metadata": meta,
                "tokens": token_estimate,
            })

        return normalized


class SimpleIngestor:
    """
    Orchestrates document ingestion pipeline.

    Pipeline:
    1. Parse document (extract text + metadata)
    2. Chunk text (split into embeddings-sized pieces)
    3. Embed chunks (convert to vectors)
    4. Store in vector DB (with metadata)

    Features:
    - Supports PDF and text files
    - Automatic file type detection
    - Progress tracking
    - Error handling per document
    - Batch processing
    """

    def __init__(
        self,
        embedder: Optional[EmbeddingEngine] = None,
        vector_store: Optional[VectorStore] = None,
        chunker: Optional[SimpleChunker] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        collection_name: str = "default",
        transcriber=None,
        use_semantic_chunking: bool = True
    ):
        """
        Initialize ingestor.

        Args:
            embedder: Embedding engine. Created if None.
            vector_store: Vector store. Created if None.
            chunker: Text chunker. Created if None.
            chunk_size: Tokens per chunk
            chunk_overlap: Token overlap between chunks
            collection_name: Default collection for storage
            use_semantic_chunking: If True and no custom chunker, use SemanticChunker
                instead of SimpleChunker. SemanticChunker preserves sentence boundaries
                and document structure for better retrieval quality.
        """
        # Initialize components
        self.embedder = embedder or EmbeddingEngine()
        self.vector_store = vector_store or VectorStore(
            collection_name=collection_name
        )
        if chunker:
            self.chunker = chunker
        elif use_semantic_chunking:
            self._semantic_chunker = SemanticChunker(
                target_chunk_size=chunk_size,
                overlap_sentences=chunk_overlap,
            )
            # Wrap SemanticChunker so ingest_file can call .chunk_text() uniformly
            self.chunker = _SemanticChunkerAdapter(self._semantic_chunker)
        else:
            self.chunker = SimpleChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        # Phase 3: Transcriber Injection
        self.transcriber = transcriber

        # Initialize parsers
        self.pdf_parser = PDFParser()
        self.ocr_parser = OCRParser()

        # Table parser requires Java - make optional
        try:
            self.table_parser = TableParser()
        except Exception as e:
            logger.warning(f"TableParser initialization failed (Java required): {e}")
            logger.warning("Table extraction will be disabled. Install Java for full functionality.")
            self.table_parser = None

        self.planner = DocumentAnalyzer()
        
        # Phase 3: The Team
        # self.transcriber is already set above
        self.validator = HybridValidator()

        self.collection_name = collection_name

        logger.info("Initialized SimpleIngestor")

    async def ingest_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest a single file.

        Args:
            file_path: Path to file
            metadata: Additional metadata to attach
            collection_name: Target collection. None = use default.

        Returns:
            Ingestion result with statistics
        """
        path = Path(file_path)
        collection = collection_name or self.collection_name

        logger.info(f"Ingesting: {path.name}")

        try:
            # Step 1: Analyze Document (Planning Phase)
            planning_vars = {"strategy": "default"}
            processed_text = ""
            parsed_metadata = {}
            
            # Simple file type check
            suffix = path.suffix.lower()
            
            if suffix == ".pdf":
                # Run the planner
                strategy = self.planner.analyze(file_path)
                logger.info(f"Ingestion Strategy for {path.name}: Scanned={strategy.is_scanned}, Est. Tokens={strategy.estimated_tokens}")
                
                # Phase 3: Transcriber Agent Path
                if self.transcriber and (strategy.is_scanned or len(strategy.ocr_pages) > 0):
                    logger.info("⚡️ Complex Document detected. Engaging Transcriber Agent.")
                    full_text_transcribed = []
                    
                    from pdf2image import convert_from_path
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            images = convert_from_path(file_path, dpi=300)
                            for i, image in enumerate(images):
                                # Page logic: If mixed, we might only want to transcribe specific pages
                                # For now, transcribe all pages if document is marked scanned/complex
                                page_num = i + 1
                                img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                                image.save(img_path, "PNG")
                                
                                # Transcribe (VLM)
                                vlm_text = await self.transcriber.transcribe_page(img_path)
                                
                                # Grounding (OCR)
                                import pytesseract
                                ocr_text = pytesseract.image_to_string(image)
                                
                                # Validate
                                final_text = self.validator.validate(vlm_text, ocr_text)
                                full_text_transcribed.append(final_text)
                                
                        processed_text = "\n\n".join(full_text_transcribed)
                        parsed_metadata = {"ingestion_strategy": "vision_agent"}
                        
                    except Exception as e:
                        logger.error(f"Transcriber Agent failed: {e}. Falling back to standard pipeline.")
                        raise e 
                        
                else:
                    # Execute Standard Plan (Phase 2 Logic)
                    full_text_parts = []
                    
                    # 1. Text Pages
                    text_pages = [p.page_num for p in strategy.page_strategies if p.action == "text"]
                    if text_pages:
                        logger.info(f"Extracting text from {len(text_pages)} pages")
                        text_result = self.pdf_parser.parse_pages(file_path, page_numbers=text_pages)
                        for p in text_result:
                            full_text_parts.append(p["text"])
                            
                    # 2. OCR Pages
                    ocr_pages = [p.page_num for p in strategy.page_strategies if p.action == "ocr"]
                    if ocr_pages:
                        logger.info(f"Running OCR on {len(ocr_pages)} pages")
                        ocr_result = self.ocr_parser.parse(file_path, page_numbers=ocr_pages)
                        for p in ocr_result:
                            full_text_parts.append(p["text"])
                            
                    # 3. Table Extraction (optional - requires Java)
                    if not strategy.is_scanned and self.table_parser is not None:
                        tables = self.table_parser.parse(file_path)
                        if tables:
                            logger.info(f"Extracted {len(tables)} tables")
                            for t in tables:
                                full_text_parts.append(f"\n\n--- Table {t['table_index']+1} ---\n{t['markdown']}\n------------------\n")
                    
                    processed_text = "\n\n".join(full_text_parts)
                    parsed_metadata = {"ingestion_strategy": "hybrid"}
                        

            else:
                 # Standard text file
                 parsed = await self._parse_file(file_path)
                 processed_text = parsed["text"]
                 parsed_metadata = parsed.get("metadata", {})

            # Step 2: Chunk text
            if not processed_text.strip():
                 logger.warning(f"No text content in {path.name}")
                 return {
                     "status": "skipped",
                     "reason": "No text content extracted",
                     "file_name": path.name
                 }

            base_metadata = {
                "file_name": path.name,
                "file_path": str(path),
                "file_size": path.stat().st_size,
                **(metadata or {}),
                **parsed_metadata
            }

            chunks = self.chunker.chunk_text(processed_text, base_metadata)

            if not chunks:
                logger.warning(f"No chunks extracted from {path.name}")
                return {
                    "status": "skipped",
                    "reason": "No chunks generated",
                    "file_name": path.name
                }

            # Step 3: Embed chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedder.embed_documents(
                chunk_texts,
                show_progress=False
            )

            # Step 4: Store in vector DB
            # Clean metadata (remove None values - ChromaDB doesn't accept them)
            chunk_metadatas = [self._clean_metadata(chunk["metadata"]) for chunk in chunks]
            ids = self.vector_store.add_documents(
                texts=chunk_texts,
                embeddings=embeddings,
                metadatas=chunk_metadatas,
                collection_name=collection
            )

            result = {
                "status": "success",
                "file_name": path.name,
                "num_chunks": len(chunks),
                "total_tokens": sum(chunk["tokens"] for chunk in chunks),
                "num_pages": 0, # TODO: Track pages from planner
                "collection": collection,
                "chunk_ids": ids
            }

            logger.info(f"✓ Ingested {path.name}: {len(chunks)} chunks, "
                       f"{result['total_tokens']} tokens")

            return result

        except Exception as e:
            logger.error(f"Failed to ingest {path.name}: {e}")
            return {
                "status": "error",
                "file_name": path.name,
                "error": str(e)
            }

    async def _parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse file based on extension.

        Args:
            file_path: Path to file

        Returns:
            Parsed content with metadata
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self.pdf_parser.parse(file_path)
        elif suffix in [".txt", ".md"]:
            # Plain text
            text = path.read_text(encoding="utf-8")
            return {
                "text": text,
                "metadata": {},
                "num_pages": 0
            }
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    @staticmethod
    def _clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean metadata by removing None values.

        ChromaDB doesn't accept None values in metadata.

        Args:
            metadata: Raw metadata dict

        Returns:
            Cleaned metadata dict with no None values
        """
        return {k: v for k, v in metadata.items() if v is not None}

    def ingest_directory(
        self,
        directory_path: str,
        pattern: str = "*.*",
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest all files in a directory.

        Args:
            directory_path: Path to directory
            pattern: Glob pattern for files (e.g., "*.pdf")
            metadata: Base metadata for all files
            collection_name: Target collection

        Returns:
            Summary of ingestion results
        """
        path = Path(directory_path)

        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")

        # Find all matching files
        files = list(path.glob(pattern))

        if not files:
            logger.warning(f"No files matching '{pattern}' in {directory_path}")
            return {
                "status": "no_files",
                "directory": str(path),
                "pattern": pattern
            }

        logger.info(f"Ingesting {len(files)} files from {path.name}")

        results = []
        for file_path in files:
            result = self.ingest_file(
                str(file_path),
                metadata=metadata,
                collection_name=collection_name
            )
            results.append(result)

        # Summarize
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]

        summary = {
            "status": "completed",
            "directory": str(path),
            "total_files": len(files),
            "successful": len(successful),
            "failed": len(failed),
            "total_chunks": sum(r.get("num_chunks", 0) for r in successful),
            "total_tokens": sum(r.get("total_tokens", 0) for r in successful),
            "results": results
        }

        logger.info(f"✓ Ingested directory: {len(successful)}/{len(files)} files, "
                   f"{summary['total_chunks']} chunks")

        return summary

    def get_ingestion_stats(
        self,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for ingested documents.

        Args:
            collection_name: Target collection

        Returns:
            Statistics dictionary
        """
        collection = collection_name or self.collection_name

        count = self.vector_store.count(collection)

        return {
            "collection": collection,
            "total_chunks": count,
            "embedding_dimension": self.embedder.get_dimension(),
            "model_name": self.embedder.get_model_name()
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path as PathlibPath

    # Add project root to path for standalone execution
    sys.path.insert(0, str(PathlibPath(__file__).parent.parent.parent))

    if len(sys.argv) < 2:
        print("Usage: python ingestor.py <file_or_directory>")
        sys.exit(1)

    target = sys.argv[1]
    path = Path(target)

    # Initialize ingestor
    ingestor = SimpleIngestor(collection_name="test_ingest")

    # Ingest
    if path.is_file():
        result = ingestor.ingest_file(str(path))
        print(f"\nResult: {result}")
    elif path.is_dir():
        result = ingestor.ingest_directory(str(path), pattern="*.pdf")
        print(f"\nSummary:")
        print(f"  Files: {result['successful']}/{result['total_files']}")
        print(f"  Chunks: {result['total_chunks']}")
        print(f"  Tokens: {result['total_tokens']}")
    else:
        print(f"Error: {target} not found")
        sys.exit(1)

    # Show stats
    stats = ingestor.get_ingestion_stats()
    print(f"\nCollection stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Model: {stats['model_name']}")
    print(f"  Dimension: {stats['embedding_dimension']}")
