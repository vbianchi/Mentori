"""
Smart Ingestor - Orchestrates the full ingestion pipeline.

Flow: FileRouter -> PageAnalyzer -> DocumentAggregator -> Registry + VectorStore

This replaces the simple text-blob ingestion with comprehensive VLM-based extraction.
Every page is analyzed by VLM to extract:
- Metadata (title, authors, abstract, keywords, DOI)
- Figure descriptions
- Table descriptions
- Equations
- References (parsed bibliography)

Enables:
- "find papers by author X" via Document Registry
- Reference resolution: [1] -> "Smith et al. (2023) 'Title'"
- Rich figure/table search: "paper with heatmap showing gene expression"
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from backend.retrieval.schema.document import DocumentMetadata, DocumentType
from backend.retrieval.schema.registry import DocumentRegistry
from backend.retrieval.file_router import FileRouter
from backend.retrieval.extractors.pdf_metadata import PDFMetadataExtractor
from backend.retrieval.extractors.page_analyzer import PageAnalyzer, create_page_analyzer
from backend.retrieval.extractors.document_aggregator import DocumentAggregator
from backend.retrieval.chunking import SimpleChunker
from backend.retrieval.semantic_chunker import SemanticChunker
from backend.retrieval.embeddings import EmbeddingEngine
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.parsers.pdf import PDFParser
from backend.retrieval.agents.transcriber import AgentFactory, TranscriberAgent
import tempfile
import os
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class SmartIngestor:
    """
    Orchestrates document ingestion with metadata extraction.

    Flow:
    1. FileRouter detects file type
    2. Appropriate Extractor extracts metadata
    3. Document registered in Registry (SQLite)
    4. Content chunked and embedded
    5. Chunks stored in VectorStore with doc_id reference

    This enables:
    - Fast metadata queries via Registry: "find papers by Valerio Bianchi"
    - Content queries via Vector Store: "what is the IC50 of drug X"
    - Hybrid queries: Filter by author, then search within their papers
    """

    def __init__(
        self,
        registry: DocumentRegistry,
        vector_store: VectorStore,
        embedder: Optional[EmbeddingEngine] = None,
        chunker=None,
        agent_roles: Optional[Dict[str, str]] = None,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 2,
        chunking_strategy: str = "simple",
        embedding_model: str = "BAAI/bge-m3",
        device: str = "auto",
    ):
        """
        Initialize smart ingestor.

        Args:
            registry: Document registry for metadata storage
            vector_store: Vector store for chunks
            embedder: Embedding engine (default: create new with BGE-M3)
            chunker: Chunker instance (default: create from chunking_strategy)
            agent_roles: Agent config for VLM extraction
            collection_name: Default collection name
            user_id: User ID for all documents
            chunk_size: Chunk size — tokens for "simple", characters for "semantic"
                        Default 512 tokens (V2-3: simple_512 MRR=0.988)
            chunk_overlap: Overlap between chunks (sentences for semantic, tokens for simple)
            chunking_strategy: "simple" (default, V2-3 winner) or "semantic"
            embedding_model: HuggingFace model name. Default BAAI/bge-m3 (V2-1 winner)
            device: Device for embeddings ('cpu', 'cuda', 'mps', 'auto')
        """
        self.registry = registry
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        self.embedding_model = embedding_model

        # Initialize embedder with experiment-validated default
        self.embedder = embedder or EmbeddingEngine(model_name=embedding_model, device=device)

        # Initialize chunker: simple wins by 16% MRR over semantic (V2-3)
        if chunker:
            self.chunker = chunker
        elif chunking_strategy == "semantic":
            self.chunker = SemanticChunker(
                target_chunk_size=chunk_size,
                overlap_sentences=chunk_overlap,
            )
        else:
            self.chunker = SimpleChunker(
                chunk_size=chunk_size,
                chunk_overlap=50,
            )
        self.agent_roles = agent_roles
        self.collection_name = collection_name
        self.user_id = user_id

        # Initialize extractors lazily
        self._pdf_extractor = None
        self._pdf_parser = None
        self._page_analyzer: Optional[PageAnalyzer] = None
        self._aggregator = DocumentAggregator()
        self._transcriber_agent: Optional[TranscriberAgent] = None

    async def _get_transcriber_agent(self) -> Optional[TranscriberAgent]:
        """Lazy initialization of transcriber agent."""
        if self._transcriber_agent is None and self.agent_roles:
            self._transcriber_agent = await AgentFactory.get_transcriber(self.agent_roles)
        return self._transcriber_agent

    @property
    def pdf_extractor(self) -> PDFMetadataExtractor:
        """Lazy initialization of PDF extractor (fallback)."""
        if self._pdf_extractor is None:
            self._pdf_extractor = PDFMetadataExtractor(agent_roles=self.agent_roles)
        return self._pdf_extractor

    @property
    def pdf_parser(self) -> PDFParser:
        """Lazy initialization of PDF parser."""
        if self._pdf_parser is None:
            self._pdf_parser = PDFParser(extract_citations=True)
        return self._pdf_parser

    async def _get_page_analyzer(self) -> Optional[PageAnalyzer]:
        """Lazy initialization of page analyzer."""
        if self._page_analyzer is None and self.agent_roles:
            self._page_analyzer = await create_page_analyzer(self.agent_roles)
        return self._page_analyzer

    async def ingest_file(
        self,
        file_path: str,
        use_vlm: bool = False,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        refine_type: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest a single file.

        Args:
            file_path: Path to file
            use_vlm: Whether to use VLM for metadata extraction and scanned PDF transcription
            collection_name: Override default collection
            user_id: Override default user
            refine_type: Whether to refine doc_type based on content

        Returns:
            Ingestion result with doc_id, metadata, chunk_count
        """
        collection = collection_name or self.collection_name
        user = user_id or self.user_id

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Step 1: Detect file type
        doc_type, mime_type = FileRouter.detect_type(file_path)
        logger.info(f"Processing: {path.name} (type: {doc_type.value}, use_vlm={use_vlm})")

        # Check if supported
        if not FileRouter.is_supported(file_path):
            logger.warning(f"Unsupported file type: {doc_type.value} for {path.name}")
            return {
                "doc_id": None,
                "file_path": file_path,
                "file_name": path.name,
                "error": f"Unsupported file type: {doc_type.value}",
                "chunk_count": 0
            }

        # Step 2: Extract metadata
        metadata = await self._extract_metadata(
            file_path, doc_type, use_vlm, collection, user
        )

        # Step 2.5: Optionally refine type based on content
        if refine_type and doc_type == DocumentType.PAPER:
            parsed = self.pdf_parser.parse(file_path)
            refined_type = FileRouter.classify_by_content(file_path, parsed['text'][:2000])
            if refined_type != doc_type:
                logger.info(f"Refined type from {doc_type.value} to {refined_type.value}")
                metadata.doc_type = refined_type

        # Step 3: Register in registry
        doc_id = self.registry.register(metadata)
        logger.info(f"Registered: {metadata.file_name} as {doc_id}")

        # Step 4: Extract and chunk content
        chunks = await self._extract_chunks(file_path, metadata.doc_type, metadata, use_vlm)

        # Step 5: Embed and store chunks
        chunk_count = 0
        if chunks:
            chunk_count = await self._store_chunks(chunks, metadata)

        # Build result with comprehensive metadata
        confidence = metadata.extraction_confidence
        result = {
            "doc_id": doc_id,
            "file_path": file_path,
            "file_name": metadata.file_name,
            "doc_type": metadata.doc_type.value,
            "title": metadata.title,
            "authors": metadata.authors,
            "chunk_count": chunk_count,
            "page_count": metadata.page_count,
            "has_abstract": metadata.has_abstract,
            "has_tables": metadata.has_tables,
            "has_figures": metadata.has_figures,
            # New comprehensive fields
            "figure_count": len(metadata.figures),
            "table_count": len(metadata.tables),
            "reference_count": len(metadata.references),
            "vlm_model": metadata.vlm_model,
            "extraction_confidence": confidence.overall if confidence else None,
        }

        logger.info(
            f"Ingested: {metadata.file_name} | "
            f"Type: {metadata.doc_type.value} | "
            f"Title: {metadata.title[:50] if metadata.title else 'N/A'}... | "
            f"Authors: {len(metadata.authors)} | "
            f"Figs: {len(metadata.figures)} | Tables: {len(metadata.tables)} | "
            f"Refs: {len(metadata.references)} | Chunks: {chunk_count}"
        )

        return result

    async def _extract_metadata(
        self,
        file_path: str,
        doc_type: DocumentType,
        use_vlm: bool,
        collection_name: Optional[str],
        user_id: Optional[str]
    ) -> DocumentMetadata:
        """
        Extract metadata using comprehensive per-page VLM analysis.

        New pipeline:
        1. PageAnalyzer processes every page with VLM
        2. DocumentAggregator merges results with OCR validation
        3. Falls back to regex-based extraction if VLM unavailable
        """
        path = Path(file_path)

        if doc_type in [DocumentType.PAPER, DocumentType.REPORT, DocumentType.GRANT,
                        DocumentType.MEETING, DocumentType.PRESENTATION]:

            # Try comprehensive VLM analysis first
            if use_vlm:
                page_analyzer = await self._get_page_analyzer()

                if page_analyzer:
                    return await self._extract_with_page_analyzer(
                        file_path=file_path,
                        page_analyzer=page_analyzer,
                        collection_name=collection_name,
                        user_id=user_id
                    )

            # Fall back to legacy extractor (regex-based)
            logger.info(f"Using legacy extractor for {path.name}")
            return await self.pdf_extractor.extract(
                file_path,
                use_vlm=False,  # Already tried VLM above
                collection_name=collection_name,
                user_id=user_id
            )
        else:
            # Basic metadata for unsupported types
            return DocumentMetadata(
                file_path=str(path.absolute()),
                file_name=path.name,
                doc_type=doc_type,
                collection_name=collection_name,
                user_id=user_id
            )

    async def _extract_with_page_analyzer(
        self,
        file_path: str,
        page_analyzer: PageAnalyzer,
        collection_name: Optional[str],
        user_id: Optional[str]
    ) -> DocumentMetadata:
        """
        Extract metadata using comprehensive per-page VLM analysis.

        Analyzes every page to extract:
        - Metadata (title, authors, abstract, keywords, DOI)
        - Figure descriptions
        - Table descriptions
        - Equations
        - References
        """
        import hashlib

        path = Path(file_path)

        # Get OCR text for validation
        parsed = self.pdf_parser.parse(file_path)
        ocr_texts = [page['text'] for page in parsed.get('pages', [])]

        # Compute file hash
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        file_hash = hash_md5.hexdigest()

        # Analyze all pages with VLM
        logger.info(f"Analyzing {len(ocr_texts)} pages with VLM for {path.name}")
        try:
            page_results = await page_analyzer.analyze_pdf(file_path, ocr_texts)
        except Exception as e:
            logger.error(f"VLM analysis failed for {path.name}: {e}")
            # Return empty page results - chunking will still work from OCR
            page_results = []

        # Check how many pages successfully extracted metadata
        pages_with_metadata = sum(1 for p in page_results if p.title or p.authors or p.figures or p.tables)
        logger.info(
            f"VLM extracted metadata from {pages_with_metadata}/{len(page_results)} pages for {path.name}"
        )

        # Log token usage
        token_usage = page_analyzer.get_token_usage()
        logger.info(
            f"VLM token usage for {path.name}: "
            f"input={token_usage['input']}, output={token_usage['output']}"
        )

        # Get VLM model name for tracking
        vlm_model = page_analyzer.model_name

        # Aggregate results into unified metadata
        metadata = self._aggregator.aggregate(
            page_results=page_results,
            file_path=str(path.absolute()),
            file_name=path.name,
            vlm_model=vlm_model,
            file_hash=file_hash,
            user_id=user_id,
            collection_name=collection_name
        )

        confidence_str = f"{metadata.extraction_confidence.overall:.2f}" if metadata.extraction_confidence else "N/A"
        logger.info(
            f"VLM extraction complete for {path.name}: "
            f"title='{metadata.title[:50] if metadata.title else 'N/A'}...', "
            f"authors={len(metadata.authors)}, "
            f"figures={len(metadata.figures)}, "
            f"tables={len(metadata.tables)}, "
            f"references={len(metadata.references)}, "
            f"confidence={confidence_str}"
        )

        return metadata

    async def _extract_chunks(
        self,
        file_path: str,
        doc_type: DocumentType,
        metadata: DocumentMetadata,
        use_vlm: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract and chunk document content with citation resolution.

        Args:
            file_path: Path to the file
            doc_type: Document type
            metadata: Document metadata
            use_vlm: Whether to use VLM for scanned PDF transcription

        IMPORTANT: This uses OCR text extraction (pdf_parser) by default.
        VLM transcription for scanned PDFs only happens if use_vlm=True.
        """

        if doc_type in [DocumentType.PAPER, DocumentType.REPORT, DocumentType.GRANT,
                        DocumentType.MEETING, DocumentType.PRESENTATION]:
            parsed = self.pdf_parser.parse(file_path)
            logger.info(f"OCR extracted {len(parsed.get('pages', []))} pages, {len(parsed.get('text', ''))} chars from {Path(file_path).name}")

            # Check for scanned PDF - only use VLM transcription if use_vlm is enabled
            if parsed.get("is_scanned") and use_vlm:
                transcriber = await self._get_transcriber_agent()
                if transcriber:
                    logger.info(f"Engaging Transcriber Agent for scanned document: {Path(file_path).name}")
                    try:
                        parsed = await self._transcribe_scanned_pdf(file_path, parsed, transcriber)
                    except Exception as e:
                        logger.error(f"Failed to transcribe scanned PDF: {e}")
                        # Continue with whatever text we have (or empty)
            elif parsed.get("is_scanned"):
                logger.info(f"Scanned PDF detected but VLM disabled - using basic OCR text for {Path(file_path).name}")

            # Build metadata prefix for searchability
            prefix = self._build_chunk_prefix(metadata)

            all_chunks = []
            for page in parsed['pages']:
                page_num = page['page_number']
                page_text = page.get('text', '')
                if not page_text.strip():
                    logger.debug(f"Page {page_num} has no text, skipping")
                    continue

                page_chunks = self.chunker.chunk_text(
                    text=page_text,
                    page_num=page_num
                )
                for chunk in page_chunks:
                    # Build chunk with context, citations, and figure/table info
                    chunk['text_with_prefix'] = self._build_chunk_with_context(
                        chunk_text=chunk['text'],
                        page_num=page_num,
                        metadata=metadata,
                        prefix=prefix
                    )
                    chunk['doc_id'] = metadata.doc_id
                all_chunks.extend(page_chunks)

            logger.info(f"Created {len(all_chunks)} chunks from OCR text for {Path(file_path).name}")
            return all_chunks

        # Future: Add more extractors for other types
        logger.warning(f"No content extractor for {doc_type.value}")
        return []

    async def _store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        metadata: DocumentMetadata
    ) -> int:
        """Embed and store chunks in vector store."""

        if not chunks:
            logger.warning(f"No chunks to store for {metadata.file_name}")
            return 0

        texts = [c['text_with_prefix'] for c in chunks]

        # Verify texts are not empty
        non_empty = sum(1 for t in texts if t and t.strip())
        if non_empty == 0:
            logger.error(f"All {len(texts)} chunks have empty text for {metadata.file_name}")
            return 0

        logger.info(f"Embedding {len(texts)} chunks ({non_empty} non-empty) for {metadata.file_name}")

        # Embed in batches if needed
        embeddings = self.embedder.embed_documents(texts)

        # Build metadata for each chunk
        chunk_metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                "doc_id": metadata.doc_id,
                "file_path": metadata.file_path,
                "file_name": metadata.file_name,
                "doc_type": metadata.doc_type.value,
                "page": chunk.get('page_num', 0),
                "chunk_index": i,  # CRITICAL: RLM context needs this for navigation
                "chunk_type": chunk.get('type', 'content'),
                # Denormalized for vector store filtering
                "authors": ", ".join(metadata.authors) if metadata.authors else "",
                "title": metadata.title or "",
            }
            chunk_metadatas.append(chunk_meta)

        # Store in vector store
        logger.info(f"Storing {len(texts)} chunks in collection '{self.collection_name}'")
        self.vector_store.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
            collection_name=self.collection_name
        )

        logger.info(f"Successfully stored {len(chunks)} chunks for {metadata.file_name} in '{self.collection_name}'")
        return len(chunks)

    def _build_chunk_prefix(self, metadata: DocumentMetadata) -> str:
        """
        Build searchable prefix from metadata.

        This prefix is prepended to each chunk so that embeddings
        capture document-level context (title, authors, etc.).
        """
        parts = []

        if metadata.title:
            parts.append(f"Document: {metadata.title}")

        if metadata.authors:
            parts.append(f"Authors: {', '.join(metadata.authors)}")

        parts.append(f"Type: {metadata.doc_type.value}")

        if metadata.paper_metadata and metadata.paper_metadata.journal:
            parts.append(f"Journal: {metadata.paper_metadata.journal}")

        return " | ".join(parts)

    def _build_chunk_with_context(
        self,
        chunk_text: str,
        page_num: int,
        metadata: DocumentMetadata,
        prefix: str
    ) -> str:
        """
        Build chunk text with context and resolved citations.

        If the document has parsed references, citation markers like [1]
        are expanded to include the reference info.
        """
        # Add prefix
        text_with_prefix = f"{prefix}\n\n{chunk_text}"

        # Resolve citations if we have references
        if metadata.references:
            text_with_prefix = metadata.resolve_citations(text_with_prefix)

        # Add figure/table context if this page has them
        page_figures = [f for f in metadata.figures if f.page == page_num]
        page_tables = [t for t in metadata.tables if t.page == page_num]

        if page_figures:
            fig_context = "; ".join(
                f"{f.figure_id}: {f.description[:100]}" for f in page_figures if f.description
            )
            if fig_context:
                text_with_prefix += f"\n\n[Figures on this page: {fig_context}]"

        if page_tables:
            table_context = "; ".join(
                f"{t.table_id}: {t.description[:100]}" for t in page_tables if t.description
            )
            if table_context:
                text_with_prefix += f"\n\n[Tables on this page: {table_context}]"

        return text_with_prefix

    async def _transcribe_scanned_pdf(
        self,
        file_path: str,
        parsed_result: Dict[str, Any],
        transcriber: TranscriberAgent
    ) -> Dict[str, Any]:
        """
        Transcribe a scanned PDF using the Transcriber Agent.
        
        Args:
            file_path: Path to PDF
            parsed_result: Original parse result (with empty/garbage text)
            transcriber: The agent to use
            
        Returns:
            Updated parse result with transcribed text
        """
        import asyncio
        
        try:
            # Convert PDF to images
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(file_path, dpi=200)
                logger.info(f"Transcribing {len(images)} pages for {Path(file_path).name}...")
                
                new_pages = []
                full_text_list = []
                
                for i, image in enumerate(images):
                    page_num = i + 1
                    page_path = os.path.join(temp_dir, f"page_{page_num}.png")
                    image.save(page_path, "PNG")
                    
                    # Call Transcriber
                    # Add delay to avoid overwhelming local LLM
                    if i > 0:
                        await asyncio.sleep(2)
                        
                    page_md = await transcriber.transcribe_page(page_path)
                    
                    # Store result
                    new_pages.append({
                        "page_number": page_num,
                        "text": page_md,
                        "char_count": len(page_md)
                    })
                    full_text_list.append(page_md)
                    
                    logger.info(f"Transcribed page {page_num}/{len(images)}")
                
                # Update result
                parsed_result["pages"] = new_pages
                parsed_result["text"] = "\n\n".join(full_text_list)
                parsed_result["is_scanned"] = False # Handled
                
                return parsed_result
                
        except Exception as e:
            logger.error(f"Transcriber logic failed: {e}")
            raise

    async def ingest_batch(
        self,
        file_paths: List[str],
        use_vlm: bool = True,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest multiple files.

        Args:
            file_paths: List of file paths
            use_vlm: Whether to use VLM
            collection_name: Collection name
            user_id: User ID

        Returns:
            Summary with results for each file
        """
        results = []
        successful = 0
        failed = 0

        for path in file_paths:
            try:
                result = await self.ingest_file(
                    path,
                    use_vlm=use_vlm,
                    collection_name=collection_name,
                    user_id=user_id
                )
                results.append(result)
                if result.get('doc_id'):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to ingest {path}: {e}")
                results.append({
                    "file_path": path,
                    "file_name": Path(path).name,
                    "error": str(e),
                    "chunk_count": 0
                })
                failed += 1

        return {
            "total": len(file_paths),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def reingest_all(
        self,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        use_vlm: bool = True
    ) -> Dict[str, Any]:
        """
        Re-ingest all documents in a collection.

        Useful when upgrading the extraction logic.

        Args:
            collection_name: Collection to re-ingest
            user_id: User ID filter

        Returns:
            Summary of re-ingestion
        """
        # Get all documents from registry
        docs = self.registry.get_all_documents(
            collection_name=collection_name,
            user_id=user_id,
            limit=10000  # Reasonable limit
        )

        file_paths = [doc['file_path'] for doc in docs if Path(doc['file_path']).exists()]

        logger.info(f"Re-ingesting {len(file_paths)} documents...")

        return await self.ingest_batch(
            file_paths,
            use_vlm=use_vlm,
            collection_name=collection_name,
            user_id=user_id
        )


# Factory function for easy instantiation
def create_smart_ingestor(
    db_path: str,
    collection_name: str,
    user_id: str,
    agent_roles: Optional[Dict[str, str]] = None,
    chroma_path: Optional[str] = None
) -> SmartIngestor:
    """
    Factory function to create a configured SmartIngestor.

    Args:
        db_path: Path to SQLite registry database
        collection_name: Name of the collection
        user_id: User ID
        agent_roles: Optional agent configuration for VLM
        chroma_path: Optional path to ChromaDB (uses default if None)

    Returns:
        Configured SmartIngestor instance
    """
    registry = DocumentRegistry(db_path)

    if chroma_path:
        vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=chroma_path
        )
    else:
        vector_store = VectorStore(collection_name=collection_name)

    return SmartIngestor(
        registry=registry,
        vector_store=vector_store,
        agent_roles=agent_roles,
        collection_name=collection_name,
        user_id=user_id
    )
