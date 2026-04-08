"""
RLM Context - Manages the REPL state for document interaction.

The context provides functions for the LLM to interact with documents
WITHOUT seeing all content directly. This prevents hallucination by
forcing explicit retrieval and citation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import re
import json
import logging

logger = logging.getLogger(__name__)


class CitationType(str, Enum):
    """Distinguishes corpus provenance citations from intra-document references."""
    CORPUS = "corpus"                # "this info came from paper1.pdf, page 5"
    INTRA_DOCUMENT = "intra_document"  # "(Smith et al., 2020)" preserved verbatim


@dataclass
class Citation:
    """A citation reference to source material."""
    doc_name: str
    page: int
    chunk_idx: int
    quote: str  # Exact text being cited
    context: str = ""  # Surrounding text for verification
    timestamp: datetime = field(default_factory=datetime.now)
    citation_type: CitationType = CitationType.CORPUS
    verified: bool = True
    # Intra-document citation fields
    intra_ref_text: str = ""  # Verbatim reference, e.g. "(Smith et al., 2020)"
    intra_ref_authors: List[str] = field(default_factory=list)
    intra_ref_year: str = ""

    def to_inline(self) -> str:
        """Format as inline citation.

        Intra-document citations are preserved verbatim.
        Corpus citations are formatted as numbered [N] references
        (the number is assigned externally during report generation).
        """
        if self.citation_type == CitationType.INTRA_DOCUMENT:
            return self.intra_ref_text
        return f"[{self.doc_name}:p{self.page}]"

    def to_reference(self) -> str:
        """Format as reference list entry."""
        verified_tag = "" if self.verified else " (unverified)"
        return f"- {self.doc_name}, page {self.page}: \"{self.quote[:100]}...\"{verified_tag}"


@dataclass
class ChunkResult:
    """A chunk returned from search/retrieval."""
    doc_name: str
    chunk_idx: int
    text: str
    page: int
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        preview = self.text[:100].replace('\n', ' ')
        return f"Chunk({self.doc_name}[{self.chunk_idx}], p{self.page}): \"{preview}...\""

    def __getitem__(self, key):
        """Allow dict-like AND slice access for LLM compatibility."""
        # Support slicing: chunk[:200] → self.text[:200]
        if isinstance(key, (int, slice)):
            return self.text[key]
        # Map common LLM-expected keys to actual attributes
        key_mapping = {
            'content': 'text',
            'text': 'text',
            'doc_name': 'doc_name',
            'chunk_idx': 'chunk_idx',
            'page': 'page',
            'score': 'score',
            'metadata': 'metadata',
        }
        actual_key = key_mapping.get(key, key)
        if hasattr(self, actual_key):
            return getattr(self, actual_key)
        raise KeyError(f"ChunkResult has no key '{key}'. Available: {list(key_mapping.keys())}")

    def __str__(self):
        """Return chunk text for string operations."""
        return self.text

    def __len__(self):
        """Return text length."""
        return len(self.text)


@dataclass
class DocumentInfo:
    """Information about a document in the index."""
    name: str
    file_path: str
    total_chunks: int
    total_pages: int
    title: Optional[str] = None
    author: Optional[str] = None
    sections: List[Dict] = field(default_factory=list)  # TOC structure


@dataclass
class ReportSection:
    """A section of the accumulated report."""
    title: str
    content: str
    citations: List[Citation]
    order: int


@dataclass
class RLMContext:
    """
    Manages the REPL state for an RLM session.

    This is the 'environment' that the LLM interacts with through code.
    All document access goes through explicit function calls, ensuring
    the LLM can only work with content it explicitly retrieves.
    """

    index_name: str
    user_id: str

    # Lazy-loaded document data
    _documents: Dict[str, DocumentInfo] = field(default_factory=dict)
    _chunks_by_doc: Dict[str, List[Dict]] = field(default_factory=dict)
    _chunk_cache: Dict[str, str] = field(default_factory=dict)
    _initialized: bool = False

    # Tracking
    citations: List[Citation] = field(default_factory=list)
    report_sections: List[ReportSection] = field(default_factory=list)
    processed_sections: Set[str] = field(default_factory=set)

    # Token/cost tracking
    total_tokens_used: int = 0
    max_tokens: int = 1_000_000
    llm_calls_made: int = 0

    # Retriever reference (set during initialization)
    _retriever: Any = None
    _vector_store: Any = None
    _collection_name: str = ""

    @classmethod
    async def from_index(cls, index_name: str, user_id: str, max_tokens: int = 1_000_000) -> "RLMContext":
        """
        Create context from an existing document index.

        Args:
            index_name: Name of the UserCollection to load
            user_id: User ID for access control
            max_tokens: Maximum token budget for this session
        """
        from backend.retrieval.models import UserCollection, IndexStatus
        from backend.retrieval.vector_store import VectorStore
        from backend.retrieval.retriever import SimpleRetriever
        from backend.database import engine
        from sqlmodel import Session, select

        context = cls(
            index_name=index_name,
            user_id=user_id,
            max_tokens=max_tokens
        )

        # Load index metadata
        with Session(engine) as session:
            idx = session.exec(
                select(UserCollection)
                .where(UserCollection.user_id == user_id)
                .where(UserCollection.name == index_name)
            ).first()

            if not idx:
                raise ValueError(f"Index '{index_name}' not found for user")

            if idx.status != IndexStatus.READY:
                raise ValueError(f"Index '{index_name}' is not ready (status: {idx.status})")

            context._collection_name = idx.vector_db_collection_name
            embedding_model = idx.embedding_model  # Use collection's embedding model

        context._vector_store = VectorStore(collection_name=context._collection_name)
        
        # Estimate if corpus > 20 papers (assuming ~40 chunks per paper = 800 chunks)
        chunk_count = context._vector_store.count(context._collection_name)
        use_reranker = chunk_count > 800
        if use_reranker:
            logger.info(f"Large corpus detected ({chunk_count} chunks). Enabling reranker for RLMContext.")
        
        # Initialize retriever with the correct embedding model and reranker setting
        context._retriever = SimpleRetriever(embedding_model=embedding_model, use_reranker=use_reranker)

        # Load document metadata
        await context._load_documents()
        context._initialized = True

        logger.info(f"RLMContext initialized: {len(context._documents)} documents, "
                   f"{sum(d.total_chunks for d in context._documents.values())} total chunks")

        return context

    async def _load_documents(self):
        """Load document metadata from vector store."""
        import os

        # Get all metadata from collection
        logger.info(f"Loading documents from collection '{self._collection_name}'")
        try:
            collection = self._vector_store.get_collection(self._collection_name)
            all_data = collection.get(include=["metadatas", "documents"])
        except Exception as e:
            logger.error(f"Failed to get collection '{self._collection_name}': {e}")
            return

        metadatas = all_data.get("metadatas", [])
        documents = all_data.get("documents", [])
        ids = all_data.get("ids", [])

        logger.info(f"Found {len(documents)} chunks in collection '{self._collection_name}'")

        if not documents:
            logger.warning(f"Collection '{self._collection_name}' is empty - no documents found")
            return

        # Check for empty documents
        empty_count = sum(1 for d in documents if not d or not d.strip())
        if empty_count > 0:
            logger.warning(f"{empty_count}/{len(documents)} chunks have empty text")

        # Aggregate by source document
        doc_chunks: Dict[str, List[Dict]] = {}

        for i, (meta, text, chunk_id) in enumerate(zip(metadatas, documents, ids)):
            source = meta.get("file_path") or meta.get("source") or "unknown"
            doc_name = meta.get("file_name") or os.path.basename(source)

            if doc_name not in doc_chunks:
                doc_chunks[doc_name] = []

            doc_chunks[doc_name].append({
                "id": chunk_id,
                "text": text,
                "chunk_idx": meta.get("chunk_index", i),
                "page": meta.get("page", 1),
                "metadata": meta
            })

        # Create DocumentInfo for each
        for doc_name, chunks in doc_chunks.items():
            # Sort chunks by index
            chunks.sort(key=lambda c: c["chunk_idx"])

            # Extract document metadata from first chunk
            first_meta = chunks[0]["metadata"]
            pages = set(c["page"] for c in chunks)

            self._documents[doc_name] = DocumentInfo(
                name=doc_name,
                file_path=first_meta.get("file_path", ""),
                total_chunks=len(chunks),
                total_pages=max(pages) if pages else 1,
                title=first_meta.get("title"),
                author=first_meta.get("author"),
                sections=[]  # TODO: Extract TOC structure
            )

            self._chunks_by_doc[doc_name] = chunks

    # ============== NAVIGATION FUNCTIONS ==============

    def list_documents(self) -> List[Dict]:
        """
        List all documents in the index.

        Returns:
            List of document info dicts with name, chunks, pages
        """
        return [
            {
                "name": doc.name,
                "chunks": doc.total_chunks,
                "pages": doc.total_pages,
                "title": doc.title,
                "author": doc.author
            }
            for doc in self._documents.values()
        ]

    def get_document_structure(self, doc_name: str) -> Dict:
        """
        Get the structure (sections/TOC) of a document.

        For now, returns chunk-based structure. Future: parse actual TOC.
        """
        if doc_name not in self._documents:
            return {"error": f"Document '{doc_name}' not found"}

        doc = self._documents[doc_name]
        chunks = self._chunks_by_doc[doc_name]

        # Group chunks by page
        pages = {}
        for chunk in chunks:
            page = chunk["page"]
            if page not in pages:
                pages[page] = {"page": page, "chunks": [], "preview": ""}
            pages[page]["chunks"].append(chunk["chunk_idx"])
            if not pages[page]["preview"]:
                pages[page]["preview"] = chunk["text"][:200]

        return {
            "name": doc_name,
            "total_chunks": doc.total_chunks,
            "total_pages": doc.total_pages,
            "pages": list(pages.values()),
            "sections": doc.sections  # Empty for now, future: parsed TOC
        }

    def get_chunk(self, doc_name: str, chunk_idx: int) -> str:
        """
        Get a specific chunk by document name and index.

        Args:
            doc_name: Name of the document
            chunk_idx: Index of the chunk (0-based)

        Returns:
            The chunk text, or error message
        """
        if doc_name not in self._chunks_by_doc:
            return f"[ERROR] Document '{doc_name}' not found"

        chunks = self._chunks_by_doc[doc_name]

        # Find chunk with matching index
        for chunk in chunks:
            if chunk["chunk_idx"] == chunk_idx:
                return chunk["text"]

        return f"[ERROR] Chunk {chunk_idx} not found in '{doc_name}' (has {len(chunks)} chunks)"

    def get_chunks_range(self, doc_name: str, start: int, end: int) -> List[ChunkResult]:
        """
        Get a range of chunks from a document.

        Args:
            doc_name: Document name
            start: Starting chunk index (inclusive)
            end: Ending chunk index (exclusive)

        Returns:
            List of ChunkResult objects
        """
        if doc_name not in self._chunks_by_doc:
            return []

        chunks = self._chunks_by_doc[doc_name]
        results = []

        for chunk in chunks:
            idx = chunk["chunk_idx"]
            if start <= idx < end:
                results.append(ChunkResult(
                    doc_name=doc_name,
                    chunk_idx=idx,
                    text=chunk["text"],
                    page=chunk["page"],
                    metadata=chunk["metadata"]
                ))

        return sorted(results, key=lambda r: r.chunk_idx)

    def get_chunks_by_page(self, doc_name: str, page: int) -> List[ChunkResult]:
        """Get all chunks from a specific page."""
        if doc_name not in self._chunks_by_doc:
            return []

        return [
            ChunkResult(
                doc_name=doc_name,
                chunk_idx=c["chunk_idx"],
                text=c["text"],
                page=c["page"],
                metadata=c["metadata"]
            )
            for c in self._chunks_by_doc[doc_name]
            if c["page"] == page
        ]

    # ============== SEARCH FUNCTIONS ==============

    def search_keyword(self, keyword: str, doc_name: str = None,
                       case_sensitive: bool = False) -> List[ChunkResult]:
        """
        Fast keyword search across chunks (no LLM, just string matching).

        Args:
            keyword: Keyword to search for
            doc_name: Optional - limit search to specific document
            case_sensitive: Whether to match case

        Returns:
            List of matching ChunkResult objects
        """
        results = []
        search_term = keyword if case_sensitive else keyword.lower()

        docs_to_search = [doc_name] if doc_name else self._chunks_by_doc.keys()

        for dname in docs_to_search:
            if dname not in self._chunks_by_doc:
                continue

            for chunk in self._chunks_by_doc[dname]:
                text = chunk["text"]
                compare_text = text if case_sensitive else text.lower()

                if search_term in compare_text:
                    results.append(ChunkResult(
                        doc_name=dname,
                        chunk_idx=chunk["chunk_idx"],
                        text=text,
                        page=chunk["page"],
                        score=compare_text.count(search_term),  # Simple relevance
                        metadata=chunk["metadata"]
                    ))

        return sorted(results, key=lambda r: -r.score)

    def search_regex(self, pattern: str, doc_name: str = None) -> List[ChunkResult]:
        """
        Regex search across chunks.

        Args:
            pattern: Regex pattern to match
            doc_name: Optional - limit to specific document

        Returns:
            Matching chunks with match information
        """
        results = []
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return []

        docs_to_search = [doc_name] if doc_name else self._chunks_by_doc.keys()

        for dname in docs_to_search:
            if dname not in self._chunks_by_doc:
                continue

            for chunk in self._chunks_by_doc[dname]:
                text = chunk["text"]
                matches = list(regex.finditer(text))

                if matches:
                    results.append(ChunkResult(
                        doc_name=dname,
                        chunk_idx=chunk["chunk_idx"],
                        text=text,
                        page=chunk["page"],
                        score=len(matches),
                        metadata={
                            **chunk["metadata"],
                            "matches": [m.group() for m in matches[:5]]
                        }
                    ))

        return sorted(results, key=lambda r: -r.score)

    def search_semantic(self, query: str, top_k: int = 10,
                        doc_name: str = None) -> List[ChunkResult]:
        """
        Semantic search using embeddings.

        Args:
            query: Natural language query
            top_k: Number of results to return
            doc_name: Optional - filter to specific document

        Returns:
            Ranked list of relevant chunks
        """
        # Build filter if doc_name specified
        where_filter = None
        if doc_name:
            where_filter = {"file_name": doc_name}

        # Use retriever for semantic search
        results = self._retriever.retrieve(
            query=query,
            collection_name=self._collection_name,
            top_k=top_k,
            where=where_filter
        )

        return [
            ChunkResult(
                doc_name=r["metadata"].get("file_name", "unknown"),
                chunk_idx=r["metadata"].get("chunk_index", 0),
                text=r["text"],
                page=r["metadata"].get("page", 1),
                score=r.get("score", 0),
                metadata=r["metadata"]
            )
            for r in results
        ]

    # ============== CITATION FUNCTIONS ==============

    def cite(self, doc_name: str, page: int, quote: str,
             chunk_idx: int = None) -> Citation:
        """
        Register a citation to source material.

        Args:
            doc_name: Document being cited
            page: Page number
            quote: Exact text being cited (for verification)
            chunk_idx: Optional chunk index

        Returns:
            Citation object
        """
        # Verify quote exists in document (anti-hallucination check)
        verified = False
        actual_chunk_idx = chunk_idx

        if doc_name in self._chunks_by_doc:
            for chunk in self._chunks_by_doc[doc_name]:
                if quote[:50] in chunk["text"]:  # Check first 50 chars
                    verified = True
                    actual_chunk_idx = chunk["chunk_idx"]
                    break

        if not verified:
            logger.warning(f"Citation quote not found in source: {quote[:50]}...")

        citation = Citation(
            doc_name=doc_name,
            page=page,
            chunk_idx=actual_chunk_idx or 0,
            quote=quote,
            context="",
            citation_type=CitationType.CORPUS,
            verified=verified,
        )

        self.citations.append(citation)
        return citation

    def extract_intra_citations(
        self, doc_name: str, chunk_text: str, page: int, chunk_idx: int
    ) -> List[Citation]:
        """
        Extract intra-document citations (author-year, numbered refs) from chunk text.

        Uses the existing CitationExtractor from parsers/citations.py to find
        references like "(Smith et al., 2020)" and wraps them as
        Citation(citation_type=INTRA_DOCUMENT).

        Returns:
            List of intra-document Citation objects (also appended to self.citations)
        """
        from backend.retrieval.parsers.citations import CitationExtractor

        extractor = CitationExtractor()
        raw_citations = extractor.extract_citations(chunk_text)

        intra_citations = []
        for raw in raw_citations:
            if raw["type"] == "author-year":
                cit = Citation(
                    doc_name=doc_name,
                    page=page,
                    chunk_idx=chunk_idx,
                    quote=chunk_text[max(0, raw["start"] - 40):raw["end"] + 40],
                    citation_type=CitationType.INTRA_DOCUMENT,
                    intra_ref_text=raw["text"],
                    intra_ref_authors=raw.get("authors", []),
                    intra_ref_year=raw.get("year", ""),
                    verified=True,
                )
                self.citations.append(cit)
                intra_citations.append(cit)

        return intra_citations

    def get_citations(self) -> List[Citation]:
        """Get all accumulated citations."""
        return self.citations

    def get_citations_for_doc(self, doc_name: str) -> List[Citation]:
        """Get citations for a specific document."""
        return [c for c in self.citations if c.doc_name == doc_name]

    # ============== REPORT BUILDING ==============

    def add_to_report(self, section: str, content: str,
                      citations: List[Citation] = None):
        """
        Add a section to the accumulated report.

        Args:
            section: Section title
            content: Section content (should include inline citations)
            citations: Citations used in this section
        """
        self.report_sections.append(ReportSection(
            title=section,
            content=content,
            citations=citations or [],
            order=len(self.report_sections)
        ))
        self.processed_sections.add(section)

        logger.info(f"Added report section: {section} ({len(content)} chars)")

    def auto_generate_report_from_citations(self) -> str:
        """
        DETERMINISTIC FALLBACK: Auto-generate a report from collected citations.

        Called when:
        - We have citations but no report sections
        - The LLM forgot to call add_to_report()

        This ensures we never lose work done by the LLM.
        """
        if not self.citations:
            return None

        # Group citations by document
        from collections import defaultdict
        by_doc = defaultdict(list)
        for cit in self.citations:
            by_doc[cit.doc_name].append(cit)

        report_parts = ["## Auto-Generated Summary\n"]
        report_parts.append("*This report was automatically generated from collected citations because the analysis did not complete normally.*\n")

        for doc_name, cits in by_doc.items():
            report_parts.append(f"\n### From: {doc_name}\n")

            # Group by page
            by_page = defaultdict(list)
            for c in cits:
                by_page[c.page].append(c)

            for page, page_cits in sorted(by_page.items()):
                report_parts.append(f"\n**Page {page}:**\n")
                for c in page_cits:
                    # Show the quoted content
                    quote_preview = c.quote[:300] + "..." if len(c.quote) > 300 else c.quote
                    report_parts.append(f"- {quote_preview}\n")

        report_parts.append("\n---\n## References\n")
        seen = set()
        for cit in self.citations:
            key = (cit.doc_name, cit.page)
            if key not in seen:
                seen.add(key)
                report_parts.append(cit.to_reference())

        return "\n".join(report_parts)

    def get_report(self) -> str:
        """Get the accumulated report as markdown with dual citation formatting.

        Corpus citations are numbered [1], [2], ... with a Sources section.
        Intra-document citations (author-year) are preserved verbatim inline.
        """
        if not self.report_sections:
            return "No report content yet."

        sections = sorted(self.report_sections, key=lambda s: s.order)

        report_parts = []
        # Collect only corpus citations for the numbered Sources section
        corpus_citations: List[Citation] = []

        for section in sections:
            report_parts.append(f"## {section.title}\n\n{section.content}\n")
            for cit in section.citations:
                if cit.citation_type == CitationType.CORPUS and cit not in corpus_citations:
                    corpus_citations.append(cit)

        # Also include any standalone corpus citations not tied to a section
        for cit in self.citations:
            if cit.citation_type == CitationType.CORPUS and cit not in corpus_citations:
                corpus_citations.append(cit)

        # Build numbered Sources section for corpus citations
        if corpus_citations:
            report_parts.append("\n---\n## Sources (from your corpus)\n")
            seen = set()
            idx = 1
            for cit in corpus_citations:
                key = (cit.doc_name, cit.page, cit.quote[:50])
                if key in seen:
                    continue
                seen.add(key)
                verified_tag = "" if cit.verified else " (unverified)"
                quote_preview = cit.quote[:120].replace("\n", " ")
                report_parts.append(
                    f"[{idx}] {cit.doc_name}, page {cit.page}: "
                    f"\"{quote_preview}...\"{verified_tag}"
                )
                idx += 1

        return "\n".join(report_parts)

    def get_progress(self) -> Dict:
        """Get processing progress information."""
        total_docs = len(self._documents)
        total_chunks = sum(d.total_chunks for d in self._documents.values())

        return {
            "documents": total_docs,
            "total_chunks": total_chunks,
            "sections_processed": len(self.processed_sections),
            "citations_collected": len(self.citations),
            "tokens_used": self.total_tokens_used,
            "tokens_remaining": self.max_tokens - self.total_tokens_used,
            "llm_calls": self.llm_calls_made
        }

    # ============== UTILITIES ==============

    def get_context_summary(self) -> str:
        """Get a summary of the context for the LLM system prompt."""
        docs = self.list_documents()
        total_chunks = sum(d["chunks"] for d in docs)

        doc_list = "\n".join([
            f"  - {d['name']}: {d['chunks']} chunks, {d['pages']} pages"
            + (f" — \"{d['title']}\"" if d.get('title') else "")
            for d in docs
        ])

        return f"""Index: {self.index_name}
Documents: {len(docs)}
Total chunks: {total_chunks}

Available documents:
{doc_list}"""
