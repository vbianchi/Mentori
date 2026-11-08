"""
RLM Context - Manages the REPL state for document interaction.

The context provides functions for the LLM to interact with documents
WITHOUT seeing all content directly. This prevents hallucination by
forcing explicit retrieval and citation.
"""

from dataclasses import dataclass, field
import contextlib
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import re
import json
import logging
import time

from backend.retrieval.query_refinement import classify_query, QueryType

logger = logging.getLogger(__name__)

# Q9 (D68): the Sources list of a report shows a 120-character preview of each quote, the answer's stated display
# format; the whole quote is kept on the Citation and in the run's metadata (RLMContext.citations_record).
SOURCES_PREVIEW_CHARS = 120

# D80 V5 (audit F6): every search the RLM makes reranks its hits and returns this many, search_semantic's default
# top_k (the number of passages its retriever's reranker returns). The RLM's search_keyword and search_regex
# (rlm_search_keyword, rlm_search_regex, the functions its REPL exposes) take the same top_k
SEARCH_TOP_K = 10
# D80 V5: the rerank fields of a navigation function's record (it reads chunks by position, with no query to rerank)
NOT_RERANKED = {"reranked": False, "rerank_skipped": "navigation"}
# D80 V5 covers RLM retrievals only: search_keyword and search_regex called from outside the RLM's REPL (the
# orchestrator tools cross_document_analysis and paper_triage, rag_tools.py) return every match as at HEAD, unreranked
NOT_RLM = {"reranked": False, "rerank_skipped": "not_rlm"}

# D239 (arm B, a proof of concept): an RLM run can have its search functions removed (RLMOrchestrator(search_tools=
# False), which calls remove_search_tools). These are the REPL's names of the removed functions and of the navigation
# reads it keeps. Off, a call of a removed function, by its REPL name or through the context (context.search_semantic,
# context.rlm_search_keyword, context._retriever, ...), raises SearchToolRemoved, which the block's output shows as its
# error, and is logged in search_attempts.
SEARCH_FUNCTIONS = ("search_keyword", "search_regex", "search_semantic")
NAVIGATION_FUNCTIONS = ("list_documents", "get_document_structure", "get_chunk", "get_chunks_range",
                        "get_chunks_by_page")
# D240 (G17, review M1 of 89d0b958): the attributes that cannot be set or deleted once remove_search_tools ran
# (RLMContext.__setattr__, __delattr__); the latch itself is one of them
SEARCH_LOCKED_ATTRS = frozenset({"search_tools", "_retriever", "_reranker", "_vector_store", "_search_removed"})


class SearchToolRemoved(NameError):
    """D239: a call of a search function in an RLM run whose search functions are removed. A NameError, as a call of
    a name the REPL does not define would be; an Exception, so the block's output shows it as the block's error."""


class _RemovedSearchObject:
    """D239: stands in for the context's retriever, reranker and vector store once the search functions are removed;
    any attribute read is logged and refused, so the REPL's code cannot search through them."""

    def __init__(self, context: "RLMContext", name: str):
        object.__setattr__(self, "_ctx", context)
        object.__setattr__(self, "_name", name)

    def __getattr__(self, attr):
        if attr.startswith("__"):   # Python's own protocol lookups (copy, pickle, ...) are not a search
            raise AttributeError(attr)
        self._ctx._refuse_search(f"{self._name}.{attr}", via=f"context.{self._name}")

    def __setattr__(self, attr, value):
        self._ctx._refuse_search(f"{self._name}.{attr}", via=f"context.{self._name}")

    def __repr__(self):
        return f"<removed {self._name} (D239)>"


def shared_reranker():
    """The process's one CrossEncoderReranker (D40, rlm F29; A4): reranker.get_reranker(), the instance the passive
    strategies use too, so a process running both (exp1, exp_01) loads the model once. Built once under its lock;
    a failed load raises (CrossEncoderReranker, A4), so no RLM run goes on without reranking."""
    from backend.retrieval.reranker import get_reranker
    return get_reranker()


def _what(x) -> str:
    """Q141 (D83): how a refused citations value is named in add_to_report's error."""
    return "None" if x is None else f"{'an' if type(x).__name__[0] in 'aeiouAEIOU' else 'a'} {type(x).__name__}"


def _check_report_citations(citations) -> None:
    """Q141 (D83): add_to_report's citations must be None or a list whose every item is a Citation (what cite()
    returns). Anything else raises TypeError naming every bad item, before anything is saved."""
    if citations is None:
        return
    if isinstance(citations, Citation):
        raise TypeError("add_to_report: citations is a single Citation, not a list; pass it as [c]. "
                        "Nothing was saved.")
    if not isinstance(citations, list):
        raise TypeError(f"add_to_report: citations is {_what(citations)}, not a list of Citations from cite(). "
                        "Nothing was saved.")
    bad = [f"citations[{i}] is {_what(c)}, not a Citation from cite()"
           for i, c in enumerate(citations) if not isinstance(c, Citation)]
    # Q141 round 2 (D83): a corpus Citation built in the code (Citation(...)) whose fields get_report() cannot use
    bad += [p for i, c in enumerate(citations) if isinstance(c, Citation) and c.citation_type == CitationType.CORPUS
            for p in _sources_problems(c.doc_name, c.page, c.quote, f"citations[{i}].")]
    if bad:
        raise TypeError(f"add_to_report: {'; '.join(bad)}. Nothing was saved.")


def _page_order(item):
    """Q141 round 2 review D2: the sort key of auto_generate_report_from_citations' (page, citations) pairs. Numbers
    sort first in their own order (so int pages keep the order sorted() gave), then any other page by type name and
    text, so None, a str and an int in one document compare without a TypeError outside the sandbox."""
    page = item[0]
    if isinstance(page, (int, float)) and not isinstance(page, bool):
        return (0, page, "")
    return (1, type(page).__name__, str(page))


def _range_as_list(v):
    """G19 arm B (gemma3:27b rlm_10_nosearch, CD_014, 5 Nov): the model's code called
    get_chunks_by_page(doc, range(1, 6)); _seen logged page=range(1, 6) in retrievals, and the answer record could not
    be written as JSON (run_context._dumps), which stopped the run. A range the code passes is recorded as its list
    (range(1, 6) as [1, 2, 3, 4, 5]); every other value is recorded as it was."""
    return list(v) if isinstance(v, range) else v


def _sources_problems(doc_name, page, quote, prefix: str = "") -> List[str]:
    """Q141 round 2 (D83): what in a corpus citation's doc_name, page and quote makes get_report() fail, each named.
    get_report() lists every corpus citation, cite()'s included, in its Sources list once a section is saved: it
    de-duplicates on the key (doc_name, page, quote), which must be hashable, and previews the quote with
    quote[:SOURCES_PREVIEW_CHARS].replace("\\n", " "), which only text supports. The same two operations are tried
    here, so exactly what fails there is refused. A hashable doc_name or page of any type is accepted (get_report()
    writes it with an f-string): None or a str page render without failing, as on 87ad4a0 (every stored G1 citation
    has an int page). The rule refuses what fails for certain once a section is saved; with no section saved,
    get_report() returns 'No report content yet.' and a JSON-writable non-text quote (None, a number, a list) went
    through on 87ad4a0, so the refusal is slightly wider there (no stored answer is affected: every stored quote is a
    str).
    G1 rlm_10 on CD_007, draw 3: cite("06_star_aligner.pdf", 0, citation) with each Citation llm_summarize returned
    as the quote; get_report() then raised "unhashable type: 'Citation'" at every call, the orchestrator's own at the
    final answer included, which stopped the strategy."""
    problems = []
    for name, v, kind in (("doc_name", doc_name, "a str"), ("page", page, "an int")):
        try:
            hash(v)
        except Exception:
            problems.append(f"{prefix}{name} is {_what(v)}, which the report's Sources list cannot use (give {kind})")
    try:
        hash(quote)
        quote[:SOURCES_PREVIEW_CHARS].replace("\n", " ")
    except Exception:
        problems.append(f"{prefix}quote is {_what(quote)}, not the quoted text (give a str)"
                        + (" (llm_summarize has already cited its chunks: pass its citations to add_to_report as "
                           "they are)" if isinstance(quote, Citation) else ""))
    return problems


def _collapse_ws(text) -> str:
    """Q10 (D68): the text with every run of whitespace collapsed to one space, the only normalisation cite() applies."""
    return " ".join(str(text).split())


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
    # The index id of the chunk the quote was found in ("" when unverified): the passage id of D37
    chunk_id: str = ""

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
        # D25 (cuts.md context.py:56): the whole quote, without the "..." that was added to every quote
        return f"- {self.doc_name}, page {self.page}: \"{self.quote}\"{verified_tag}"


@dataclass
class ChunkResult:
    """A chunk returned from search/retrieval."""
    doc_name: str
    chunk_idx: int
    text: str
    page: int
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    # The chunk's id in the index (the passage id of D37); "" for a chunk the index did not give an id
    chunk_id: str = ""

    def __repr__(self):
        # D25 (cuts.md context.py:70): a printed list of chunks shows each chunk's whole text
        return f"Chunk({self.doc_name}[{self.chunk_idx}], p{self.page}): \"{self.text}\""

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
    llm_calls_made: int = 0   # every model call attempted: root turns and sub-calls (the stored llm_calls)

    # Q3 (D68): the quality gate counts successful sub-calls only, in their own counters. Q65 (D75): a successful
    # sub-call whose passage argument was an empty list (llm_summarize or llm_extract on a search that found nothing,
    # llm_query with context_chunks=[]) is counted in sub_calls_empty, not in sub_calls_ok
    sub_calls_ok: int = 0
    sub_calls_failed: int = 0
    sub_calls_empty: int = 0

    # A6/D37: what the code was given. passages_seen holds the index id of every chunk a function returned to
    # the code, in the order first seen; retrievals logs each call (function, query, document, ids, turn). Q125
    # (D78): each entry carries delivered; a search the block's clock stopped as it returned is logged with
    # delivered False and its ids stay out of passages_seen (the code never received them)
    passages_seen: List[str] = field(default_factory=list)
    retrievals: List[Dict[str, Any]] = field(default_factory=list)
    current_turn: int = 0     # set by the orchestrator before each turn, for the retrieval log
    # Q72 (D75): set by RLMExecutor; a context manager search_semantic runs inside, so the block's clock never raises
    # inside the retriever, the vector store or the shared reranker (None: no clock, as outside an executor)
    retrieval_guard: Any = None
    n_chunks_loaded: int = 0  # records F29
    # D239: False once remove_search_tools ran (the run's search functions removed); search_attempts logs each refused
    # call: the turn, the function, and how it was reached (via "repl", the REPL's name, or "context.<attribute>")
    search_tools: bool = True
    search_attempts: List[Dict[str, Any]] = field(default_factory=list)

    # Retriever reference (set during initialization)
    _retriever: Any = None
    _reranker: Any = None     # D80 V5: the retriever's reranker (shared_reranker()), for search_keyword and search_regex
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

        # D40: the RLM always reranks (it reranked only above 800 chunks; the Figure 2 index has 778), with the
        # process's one reranker (rlm F29), which raises if its model does not load
        # D80 V5: the same instance reranks search_keyword's and search_regex's hits
        context._reranker = shared_reranker()
        context._retriever = SimpleRetriever(embedding_model=embedding_model, use_reranker=True,
                                             reranker=context._reranker)

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
        # A5 (records F29): a failed collection read raises; it no longer leaves the RLM to run over zero documents
        collection = self._vector_store.get_collection(self._collection_name)
        all_data = collection.get(include=["metadatas", "documents"])

        metadatas = all_data.get("metadatas", [])
        documents = all_data.get("documents", [])
        ids = all_data.get("ids", [])
        self.n_chunks_loaded = len(documents)

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

    def remove_search_tools(self) -> None:
        """D239: remove this context's search functions for the rest of its life (one answer's run). After it,
        search_keyword, rlm_search_keyword, search_regex, rlm_search_regex, search_semantic and their helpers raise
        SearchToolRemoved, and the retriever, the reranker and the vector store are replaced by objects that refuse any
        use; the navigation reads, the sub-calls, cite and the report are unchanged. The documents were loaded before
        (from_index), so nothing the navigation reads needs is removed."""
        if self.__dict__.get("_search_removed", False):   # D240 (G17): once is for the context's life
            return
        self.search_tools = False
        self._retriever = _RemovedSearchObject(self, "_retriever")
        self._reranker = _RemovedSearchObject(self, "_reranker")
        self._vector_store = _RemovedSearchObject(self, "_vector_store")
        # D240 (G17, review M1 of 89d0b958): the latch. From here __setattr__ and __delattr__ refuse (log and raise)
        # any write or delete of SEARCH_LOCKED_ATTRS, so the REPL's `context.search_tools = True` (or `del
        # context.search_tools`, which would fall back to the class default True) cannot turn search back on, nor can
        # it put a retriever back; _refuse_search reads the latch as well as search_tools
        object.__setattr__(self, "_search_removed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        """D240 (G17): after remove_search_tools, a write of a SEARCH_LOCKED_ATTRS attribute is a search attempt:
        logged in search_attempts (via "context.<name>") and refused with SearchToolRemoved. Every other write, and
        every write before the removal (a run with search, every run before D239), is a plain attribute write."""
        if name in SEARCH_LOCKED_ATTRS and self.__dict__.get("_search_removed", False):
            self._refuse_search(f"{name} =", via=f"context.{name}")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        """D240 (G17): as __setattr__, for del."""
        if name in SEARCH_LOCKED_ATTRS and self.__dict__.get("_search_removed", False):
            self._refuse_search(f"del {name}", via=f"context.{name}")
        object.__delattr__(self, name)

    def _refuse_search(self, fn: str, via: str = "repl") -> None:
        """D239: when the search functions are removed, log the attempt (search_attempts) and raise SearchToolRemoved;
        otherwise return (every run before D239). D240 (G17): removed means search_tools False or the latch set by
        remove_search_tools, so the attribute alone cannot reopen search."""
        if self.search_tools and not self.__dict__.get("_search_removed", False):
            return
        self.search_attempts.append({"turn": self.current_turn, "fn": fn, "via": via})
        raise SearchToolRemoved(
            f"{fn} is not available: the search functions ({', '.join(SEARCH_FUNCTIONS)}) are removed in this run. "
            f"Read the documents with {', '.join(NAVIGATION_FUNCTIONS)}.")

    def _seen(self, fn: str, ids: List[str], delivered: bool = True, t0: Optional[float] = None, **call) -> None:
        """A6/D37: log one function's return to the code (its arguments and the chunk ids it returned) and add the
        ids to passages_seen, in the order first seen. Q125 (D78): delivered False logs the call only (a search the
        block's clock stopped before the code received its result); its ids do not enter passages_seen. Q150 (D83):
        t0 is the time.perf_counter() reading at the start of the logging function; the entry's search_s is the
        seconds from it to this log, rounded to the microsecond (None when no t0 is given). Every function of this
        file that logs passes it: the searches (search_semantic, search_keyword, search_regex and the RLM's
        reranked two, hits and rerank both counted) and the navigation reads (get_chunk, get_chunks_range,
        get_chunks_by_page)."""
        search_s = round(time.perf_counter() - t0, 6) if t0 is not None else None
        call = {k: _range_as_list(v) for k, v in call.items()}   # G19 B (5 Nov): a range argument, as its list
        ids = [i for i in ids if i]
        if delivered:
            for i in ids:
                if i not in self.passages_seen:
                    self.passages_seen.append(i)
        self.retrievals.append({"turn": self.current_turn, "fn": fn, **call, "ids": ids, "delivered": delivered,
                                "search_s": search_s})

    def _rerank_hits(self, query: str, hits: List["ChunkResult"], top_k: int):
        """D80 V5 (audit F6): a search's hits reranked by search_semantic's rule (retriever.retrieve, step 4): the one
        shared reranker scores the candidates against the query string the model passed, and the top_k best are
        returned in its order. The candidates are the first FUSED_WIDTH x top_k hits in the search's own order
        (keyword count; regex match count), the width search_semantic's reranker scores (retriever.py FUSED_WIDTH);
        n_hits records every match, n_candidates those kept, rerank_capped whether the cap removed any. As there,
        an author query (D70, query_refinement.classify_query) and a single candidate are not reranked (an author
        query's candidates are cut to top_k). D80 V5 round 3: an empty or whitespace-only query (the orchestrator's
        emergency nudge writes search_keyword("", doc_name=...), orchestrator.py; "" matches every chunk, as does
        an empty regex pattern) has nothing to rerank against: every hit is returned in the search's own order, as
        before V5, neither capped nor cut to top_k, recorded reranked False, rerank_skipped "empty_query",
        n_candidates = n_hits, candidate_width None, rerank_capped False. Returns (hits, the retrieval record's
        rerank fields)."""
        self._refuse_search("_rerank_hits", via="context._rerank_hits")   # D239
        from backend.retrieval.retriever import FUSED_WIDTH
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError(f"top_k must be a positive integer, got {top_k!r}")
        if isinstance(query, str) and not query.strip():
            return hits, {"top_k": top_k, "n_hits": len(hits), "n_candidates": len(hits), "candidate_width": None,
                          "rerank_capped": False, "reranked": False, "rerank_skipped": "empty_query",
                          "rerank_scores": None}
        width = FUSED_WIDTH * top_k
        n_hits, hits = len(hits), hits[:width]
        rec = {"top_k": top_k, "n_hits": n_hits, "n_candidates": len(hits), "candidate_width": width,
               "rerank_capped": n_hits > width, "reranked": False, "rerank_skipped": None, "rerank_scores": None}
        query_type, query_meta = classify_query(query)
        if not hits:
            rec["rerank_skipped"] = "no_candidates"
            return hits, rec
        if query_type == QueryType.METADATA and query_meta.get("query_subtype") == "author_search":
            rec["rerank_skipped"] = "author_query"
            return hits[:top_k], rec
        if len(hits) == 1:
            rec["rerank_skipped"] = "single_candidate"
            return hits, rec
        if self._reranker is None:
            self._reranker = shared_reranker()
        candidates = [{"id": h.chunk_id, "text": h.text, "score": h.score, "metadata": h.metadata, "hit": k}
                      for k, h in enumerate(hits)]
        out = self._reranker.rerank(query=query, candidates=candidates, top_k=top_k)
        if not all("rerank_score" in r for r in out):
            raise RuntimeError(f"reranker unavailable: {len(out)} hits came back without rerank scores (D80 V5)")
        rec.update(reranked=True, rerank_scores=[r["rerank_score"] for r in out])
        return [hits[r["hit"]] for r in out], rec

    def _reranked_search(self, fn: str, rerank_query: str, hits: List["ChunkResult"], top_k: int,
                         t0: Optional[float] = None, **call) -> List["ChunkResult"]:
        """D80 V5: rerank a search's hits (_rerank_hits) and log the search. The rerank runs inside the executor's
        retrieval guard, as search_semantic does (Q72: its time is code time, the block's clock never raises inside
        the reranker); a held firing raised as it returns logs the search with delivered False (Q125). Q150: t0, the
        search's start (before its hits were found), goes to the log (_seen)."""
        self._refuse_search("_reranked_search", via="context._reranked_search")   # D239
        out, rec = None, None
        try:
            with (self.retrieval_guard or contextlib.nullcontext)():
                out, rec = self._rerank_hits(rerank_query, hits, top_k)
        except BaseException:
            if rec is not None:   # the rerank returned; the held firing stopped the block before the code had it
                self._seen(fn, [r.chunk_id for r in out], delivered=False, t0=t0, **call, **rec)
            raise
        self._seen(fn, [r.chunk_id for r in out], t0=t0, **call, **rec)
        return out

    def citations_record(self) -> List[Dict[str, Any]]:
        """Every citation with its whole quote (Q9: the answer shows a preview, the record the whole quote)."""
        return [{"doc_name": c.doc_name, "page": _range_as_list(c.page), "chunk_idx": c.chunk_idx, "chunk_id": c.chunk_id,
                 "quote": c.quote, "verified": c.verified, "citation_type": c.citation_type.value}
                for c in self.citations]

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

        # Group chunks by page. D25 (cuts.md context.py:323, O5 default): the 200-character preview of each page's
        # first chunk is removed; the structure lists pages and chunk indexes, and the text is read with get_chunk
        pages = {}
        for chunk in chunks:
            page = chunk["page"]
            if page not in pages:
                pages[page] = {"page": page, "chunks": []}
            pages[page]["chunks"].append(chunk["chunk_idx"])

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
        t0 = time.perf_counter()   # Q150 (D83): the read's time, in its log entry
        if doc_name not in self._chunks_by_doc:
            return f"[ERROR] Document '{doc_name}' not found"

        chunks = self._chunks_by_doc[doc_name]

        # Find chunk with matching index
        for chunk in chunks:
            if chunk["chunk_idx"] == chunk_idx:
                self._seen("get_chunk", [chunk["id"]], t0=t0, doc_name=doc_name, chunk_idx=chunk_idx, **NOT_RERANKED)
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
        t0 = time.perf_counter()   # Q150 (D83)
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
                    metadata=chunk["metadata"],
                    chunk_id=chunk["id"]
                ))

        results = sorted(results, key=lambda r: r.chunk_idx)
        self._seen("get_chunks_range", [r.chunk_id for r in results], t0=t0, doc_name=doc_name, start=start, end=end,
                   **NOT_RERANKED)
        return results

    def get_chunks_by_page(self, doc_name: str, page: int) -> List[ChunkResult]:
        """Get all chunks from a specific page."""
        t0 = time.perf_counter()   # Q150 (D83)
        if doc_name not in self._chunks_by_doc:
            return []

        results = [
            ChunkResult(
                doc_name=doc_name,
                chunk_idx=c["chunk_idx"],
                text=c["text"],
                page=c["page"],
                metadata=c["metadata"],
                chunk_id=c["id"]
            )
            for c in self._chunks_by_doc[doc_name]
            if c["page"] == page
        ]
        self._seen("get_chunks_by_page", [r.chunk_id for r in results], t0=t0, doc_name=doc_name, page=page,
                   **NOT_RERANKED)
        return results

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
            List of matching ChunkResult objects: every match, in order of the keyword's count, unreranked. This is
            the search the orchestrator tools call (D80 V5 covers RLM retrievals only); the RLM's REPL exposes
            rlm_search_keyword under this name
        """
        self._refuse_search("search_keyword", via="context.search_keyword")   # D239
        t0 = time.perf_counter()   # Q150 (D83)
        results = self._keyword_hits(keyword, doc_name, case_sensitive)
        self._seen("search_keyword", [r.chunk_id for r in results], t0=t0, query=keyword, doc_name=doc_name,
                   **NOT_RLM)
        return results

    def rlm_search_keyword(self, keyword: str, doc_name: str = None,
                           case_sensitive: bool = False, top_k: int = SEARCH_TOP_K) -> List[ChunkResult]:
        """
        D80 V5 (audit F6): search_keyword as the RLM's REPL exposes it. The matches (search_keyword's, in order of
        the keyword's count) are reranked against the keyword the model passed, as search_semantic's hits are, and
        the top_k best are returned (_rerank_hits: at most FUSED_WIDTH x top_k candidates, the first in that order).

        Args:
            keyword: Keyword to search for
            doc_name: Optional - limit search to specific document
            case_sensitive: Whether to match case
            top_k: the number of reranked hits returned (search_semantic's default)
        """
        self._refuse_search("search_keyword", via="context.rlm_search_keyword")   # D239
        t0 = time.perf_counter()   # Q150 (D83): the hits and their rerank
        results = self._keyword_hits(keyword, doc_name, case_sensitive)
        return self._reranked_search("search_keyword", keyword, results, top_k, t0=t0, query=keyword,
                                     doc_name=doc_name)

    def _keyword_hits(self, keyword: str, doc_name: str = None, case_sensitive: bool = False) -> List[ChunkResult]:
        """Every chunk holding the keyword, in order of its count (Mentori's keyword search)."""
        self._refuse_search("_keyword_hits", via="context._keyword_hits")   # D239
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
                        metadata=chunk["metadata"],
                        chunk_id=chunk["id"]
                    ))

        return sorted(results, key=lambda r: -r.score)

    def search_regex(self, pattern: str, doc_name: str = None) -> List[ChunkResult]:
        """
        Regex search across chunks.

        Args:
            pattern: Regex pattern to match
            doc_name: Optional - limit to specific document

        Returns:
            Matching chunks with match information, every match in order of the match count, unreranked (D80 V5
            covers RLM retrievals only; the RLM's REPL exposes rlm_search_regex under this name)
        """
        self._refuse_search("search_regex", via="context.search_regex")   # D239
        t0 = time.perf_counter()   # Q150 (D83)
        results = self._regex_hits(pattern, doc_name)
        if results is None:
            return []
        self._seen("search_regex", [r.chunk_id for r in results], t0=t0, query=pattern, doc_name=doc_name, **NOT_RLM)
        return results

    def rlm_search_regex(self, pattern: str, doc_name: str = None, top_k: int = SEARCH_TOP_K) -> List[ChunkResult]:
        """
        D80 V5 (audit F6): search_regex as the RLM's REPL exposes it. The matches (search_regex's, in order of the
        match count) are reranked against the pattern string the model passed, as search_semantic's hits are, and the
        top_k best are returned (_rerank_hits: at most FUSED_WIDTH x top_k candidates, the first in that order).

        Args:
            pattern: Regex pattern to match
            doc_name: Optional - limit to specific document
            top_k: the number of reranked hits returned (search_semantic's default)
        """
        self._refuse_search("search_regex", via="context.rlm_search_regex")   # D239
        t0 = time.perf_counter()   # Q150 (D83): the hits and their rerank
        results = self._regex_hits(pattern, doc_name)
        if results is None:
            return []
        return self._reranked_search("search_regex", pattern, results, top_k, t0=t0, query=pattern,
                                     doc_name=doc_name)

    def _regex_hits(self, pattern: str, doc_name: str = None) -> Optional[List[ChunkResult]]:
        """Every chunk the pattern matches, in order of the match count (Mentori's regex search); None for an
        invalid pattern (logged, and the search returns [] unlogged, as at HEAD)."""
        self._refuse_search("_regex_hits", via="context._regex_hits")   # D239
        results = []
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return None

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
                            # D25 (cuts.md context.py:481): every match, not the first 5
                            "matches": [m.group() for m in matches]
                        },
                        chunk_id=chunk["id"]
                    ))

        return sorted(results, key=lambda r: -r.score)

    def search_semantic(self, query: str, top_k: int = SEARCH_TOP_K,
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
        # Q72 (D75): the whole search runs inside the executor's retrieval guard (its time counts as code time; a
        # firing of the block's clock is held until the search returns). Q125 (D78): the search is logged after the
        # guard; if the guard raises the held firing, the code never receives the passages, so the search is logged
        # with delivered False and its ids stay out of passages_seen
        self._refuse_search("search_semantic", via="context.search_semantic")   # D239
        t0 = time.perf_counter()   # Q150 (D83): the whole search (the retriever's call and the filter after it)
        chunks, call = None, None
        try:
            with (self.retrieval_guard or contextlib.nullcontext)():
                # Build filter if doc_name specified
                where_filter = None
                if doc_name:
                    where_filter = {"file_name": doc_name}

                # Use retriever for semantic search. D80 V5: its record (trace) gives why it did not rerank
                trace: List[Dict[str, Any]] = []
                results = self._retriever.retrieve(
                    query=query,
                    collection_name=self._collection_name,
                    top_k=top_k,
                    where=where_filter,
                    trace=trace
                )

                # Q14 (D68): the document filter applies to keyword (BM25) hits too. retrieve() applies `where` to
                # the keyword search, and drops and counts any fused passage outside it (retriever.py,
                # docs_outside_filter in its record; cc02cff); this guard drops and counts any that still reach the RLM
                # (rlm F9: the fusion added BM25-only hits from the whole collection), so outside_filter is 0 whenever
                # the retriever's filter works.
                # D80 V5: whether the retriever reranked is read before this filter, so a reranked search the filter
                # empties is recorded as reranked (not as one with no candidates). D80 V5 round 3, the label when a
                # Q14 filter empties a fused result that was not reranked: the retriever's step 4 reranks only above
                # one candidate and labels both zero and one "single_candidate" (retriever.py:336). So when the
                # retriever's own Q14 filter (its step 3) drops every fused passage, or when this guard drops a
                # single unreranked passage, search_semantic returns nothing and is recorded reranked False,
                # rerank_skipped "single_candidate" (the retriever's label, read from trace), outside_filter 0 or 1
                # respectively (the retriever's own count is its record's docs_outside_filter). "no_candidates" is
                # written only when the trace gives no reason and nothing came back (the retriever's dense search
                # found nothing and it returned early, rerank_skipped None)
                reranked = any("rerank_score" in r for r in results)
                n_retrieved = len(results)
                outside_filter = 0
                if doc_name:
                    kept = [r for r in results if r["metadata"].get("file_name") == doc_name]
                    outside_filter = len(results) - len(kept)
                    results = kept

                chunks = [
                    ChunkResult(
                        doc_name=r["metadata"].get("file_name", "unknown"),
                        chunk_idx=r["metadata"].get("chunk_index", 0),
                        text=r["text"],
                        page=r["metadata"].get("page", 1),
                        score=r.get("score", 0),
                        metadata=r["metadata"],
                        chunk_id=r.get("id", "")
                    )
                    for r in results
                ]
                # Q150: load_s, the part of the retriever's search_s spent loading (its record; the RLM's per-answer
                # retriever builds its keyword index on its first search)
                call = dict(query=query, doc_name=doc_name, top_k=top_k, outside_filter=outside_filter,
                            load_s=(trace[-1].get("load_s") if trace else None), reranked=reranked,
                            rerank_skipped=None if reranked else
                            ((trace[-1].get("rerank_skipped") if trace else None)
                             or ("no_candidates" if n_retrieved == 0 else "not_reranked")))
        except BaseException:
            if call is not None:   # the search returned; the held firing stopped the block before the code had it
                self._seen("search_semantic", [c.chunk_id for c in chunks], delivered=False, t0=t0, **call)
            raise
        self._seen("search_semantic", [c.chunk_id for c in chunks], t0=t0, **call)
        return chunks

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

        Q141 round 2 (D83): a citation get_report() cannot list (a page that cannot be hashed, a quote that is not
        text: a Citation, a list, None, an int, a tuple, ...; a doc_name that cannot be hashed, which reaches this
        point only with a quote that is empty after whitespace is collapsed, since otherwise the document lookup
        raises TypeError as it did before) is not kept: cite() raises TypeError naming each bad argument
        (_sources_problems). The model's code block gets it as its output, as any other error of a tool call, and
        can correct it. Before, such a citation was kept and get_report() failed on it at every call once a section
        was saved, the orchestrator's own call at the final answer included, which stopped the whole run (G1 rlm_10,
        CD_007 draw 3: a Citation passed as the quote). A hashable doc_name or page of any other type is cited as
        before.

        Residual, left as it is: a Citation changed after it is made (c.quote = x), or a non-Citation appended to
        get_citations() or context.citations, is not checked and still fails get_report() as before. Mixed page
        types (None or a str beside an int) in one document no longer stop auto_generate_report_from_citations,
        which sorts with _page_order (review D2).
        """
        # Verify quote exists in document (anti-hallucination check). Q10 (D68): the whole quote must occur in a
        # chunk after whitespace is collapsed on both sides (it checked the first 50 characters, so an empty quote
        # was verified)
        verified = False
        actual_chunk_idx = chunk_idx
        chunk_id = ""
        q = _collapse_ws(quote)

        if q and doc_name in self._chunks_by_doc:
            for chunk in self._chunks_by_doc[doc_name]:
                if "_collapsed" not in chunk:
                    chunk["_collapsed"] = _collapse_ws(chunk["text"])
                if q in chunk["_collapsed"]:
                    verified = True
                    actual_chunk_idx = chunk["chunk_idx"]
                    chunk_id = chunk["id"]
                    break

        if not verified:
            logger.warning(f"Citation quote not found in source: {str(quote)[:50]}...")

        citation = Citation(
            doc_name=doc_name,
            page=page,
            chunk_idx=actual_chunk_idx or 0,
            quote=quote,
            context="",
            citation_type=CitationType.CORPUS,
            verified=verified,
            chunk_id=chunk_id,
        )

        # Q141 round 2 (D83): checked here, just before the citation is kept, so every call cite() refused before
        # (an unhashable doc_name with a non-empty quote fails the document lookup above) fails as before
        problems = _sources_problems(doc_name, page, quote)
        if problems:
            raise TypeError(f"cite: {'; '.join(problems)}. Nothing was cited.")
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
            citations: Citations used in this section: None, or a list whose every item is a Citation

        Q141 (D83): any other citations argument (a list holding None or any other non-Citation, a bare Citation, a
        string, a tuple or any other type) saves nothing and raises TypeError naming the bad item. The model's code
        block gets it as its output, as any other error of a tool call (RLMExecutor.execute_code), and can correct
        it. Before Q141 a list holding a non-Citation (or a bare Citation, or a non-empty string) was saved as given,
        and get_report() then failed on it at every later call, the orchestrator's own call at the final answer
        included, which stopped the whole run (G1 rlm_5 and rlm_10 on 16_ppr_ethiopia_TE3, draw 3: [None, None]).
        Q141 round 2: a corpus Citation in the list whose doc_name, page or quote get_report() cannot use (one built
        in the code with Citation(...), since cite() refuses those) is refused the same way, named as
        citations[i].quote and so on (_sources_problems). The content argument is not checked: stored G1 answers saved a list or a dict as a section's content and
        ended normally (the orchestrator's final check read content.strip() only until the first section with text),
        so a content check would change answers already stored (Q141 fix round review, 17 October). D92 Q184 (audit
        F1): the final check reads each section as str(content), as get_report() prints it, so a section whose
        content is not text (saved alone or first) no longer stops the run there. A content of None or a number is
        still saved and then fails the log line's len(content) with a TypeError, which the model's code block gets as
        its output, as the submitted add_to_report did (96e2193 context.py:615-633).

        Residual, left as it is (O2 of the Q141 fix round): the list passed as citations is saved itself, not a
        copy, so code that appends a non-Citation to that list after the call (cits.append(None)) still reaches
        get_report() and fails it as before Q141. Saving a copy would close that route but change the Sources of
        every answer whose code appends valid Citations to the list after saving it, which get_report() now lists.
        """
        _check_report_citations(citations)
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

            # Q141 round 2 review D2: a page key every type sorts by (numbers first, in their order, then the rest by
            # type and text), so a None or str page beside an int one no longer stops the run here, outside the
            # sandbox; with every page an int (all stored G1 citations) the order is the one sorted() gave before
            for page, page_cits in sorted(by_page.items(), key=_page_order):
                report_parts.append(f"\n**Page {page}:**\n")
                for c in page_cits:
                    # Show the quoted content, whole (D25, cuts.md context.py:669)
                    report_parts.append(f"- {c.quote}\n")

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
                # D25 (rlm F15): de-duplicated on the whole quote, so quotes sharing their first 50 characters stay
                key = (cit.doc_name, cit.page, cit.quote)
                if key in seen:
                    continue
                seen.add(key)
                verified_tag = "" if cit.verified else " (unverified)"
                # Q9 (D68): the stated 120-character preview; the whole quote is in citations_record()
                quote_preview = cit.quote[:SOURCES_PREVIEW_CHARS].replace("\n", " ")
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
