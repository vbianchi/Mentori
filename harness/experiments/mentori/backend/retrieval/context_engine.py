"""
Context Engine - Smart query routing for RAG.

Analyses a user query and decides which retrieval strategy to use:
  METADATA_LOOKUP  → inspect_document_index  (author / title queries)
  TRIAGE           → paper_triage            (rank/filter documents by relevance)
  CROSS_DOC        → cross_document_analysis (per-document iteration, 100% coverage)
  SIMPLE_RAG       → query_documents         (factual point queries)
  RLM_ANALYSIS     → deep_research_rlm       (multi-doc synthesis, summaries)
  TWO_PASS         → deep_research_rlm + verification  (when user asks for verified info)

Routing is deterministic (no LLM call); it extends the existing
`query_refinement.classify_query()` with collection-size awareness
and user preference overrides.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from backend.retrieval.query_refinement import classify_query, QueryType

logger = logging.getLogger(__name__)


class Strategy:
    """Strategy constants."""
    METADATA_LOOKUP = "metadata_lookup"
    SIMPLE_RAG = "simple_rag"
    RLM_ANALYSIS = "rlm_analysis"
    TWO_PASS = "two_pass"
    CROSS_DOC = "cross_document"
    TRIAGE = "triage"
    CORPUS_ANALYSIS = "corpus_analysis"


@dataclass
class RoutingDecision:
    """Outcome of the routing logic."""
    strategy: str
    tool_name: str  # MCP tool to invoke
    suggested_params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


# Keywords that signal the user wants deep / cross-document analysis
_DEEP_KEYWORDS = re.compile(
    r"\b(compare|contrast|summarize|synthesize|across|between|overview|"
    r"strengths|weaknesses|gaps|limitations|methods?\s+used|"
    r"comprehensive|systematic|all\s+papers?|every\s+paper?)\b",
    re.IGNORECASE,
)

# Keywords that signal the user wants verified / high-confidence output
_VERIFY_KEYWORDS = re.compile(
    r"\b(verify|verified|verification|fact[- ]?check|double[- ]?check|evidence[- ]?based)\b",
    re.IGNORECASE,
)

# Keywords for metadata / catalogue queries.
# NOTE: keep patterns specific — avoid matching common words like "title" or "author"
# in content queries ("under its respective title", "each paper's findings").
_METADATA_KEYWORDS = re.compile(
    r"\b(who\s+wrote|"
    r"list\s+(all\s+)?(documents?|papers?|files?)|"
    r"what\s+papers?\s+(are|do|exist|have)|"
    r"which\s+files?\s+(are|do|exist)|"
    r"show\s+me\s+the\s+index|"
    r"what\s+is\s+in(\s+the)?\s+index|"
    r"what\s+(?:is\s+)?the\s+(?:paper\s+)?title|"
    r"show\s+(?:all\s+)?titles?|"
    r"list\s+titles?)\b",
    re.IGNORECASE,
)

# Keywords that signal cross-document (per-document iteration) analysis
_CROSS_DOC_KEYWORDS = re.compile(
    r"\b(compare\s+across|all\s+papers?|every\s+paper|each\s+document|"
    r"per[- ]document|per[- ]paper|table\s+of|extract\s+from\s+all|"
    r"systematic\s+review|across\s+all|from\s+each|each\s+paper|"
    r"every\s+document|all\s+documents)\b",
    re.IGNORECASE,
)

# Keywords that signal paper triage / relevance ranking
_TRIAGE_KEYWORDS = re.compile(
    r"\b(which\s+papers?\s+(are|is)\s+(most\s+)?relevant|"
    r"rank\s+(the\s+)?(papers?|documents?)|"
    r"triage|filter\s+documents?|most\s+relevant|"
    r"relevant\s+papers?|relevant\s+to)\b",
    re.IGNORECASE,
)

# Keywords for full-corpus per-paper NARRATIVE analysis.
# Fires on "findings from each paper", "analyze all papers", "what does each paper say".
# Must be checked BEFORE _CROSS_DOC_KEYWORDS because CROSS_DOC has broad patterns
# (each\s+paper, from\s+each) that would otherwise capture these queries first.
# Does NOT overlap with CROSS_DOC "compare/extract/table" framing.
_CORPUS_ANALYSIS_KEYWORDS = re.compile(
    r"\b("
    r"(?:main\s+|key\s+)?findings?\s+(?:from|of|in)\s+each|"
    r"analyze\s+(?:the\s+|all\s+)?(?:papers?|documents?|corpus)|"
    r"what\s+(?:are\s+the\s+)?(?:main\s+)?findings?\s+(?:from|in)\s+each|"
    r"what\s+does\s+each\s+(?:paper|document)\s+(?:say|find|report|show)|"
    r"what\s+do\s+(?:the\s+)?papers?\s+(?:each\s+)?(?:say|find|report|show)|"
    r"summarize\s+each\s+(?:paper|document)|"
    r"per[- ]paper\s+(?:findings?|summary|analysis)|"
    r"analysis\s+of\s+(?:the\s+)?(?:whole\s+|entire\s+)?corpus"
    r")\b",
    re.IGNORECASE,
)


class ContextEngine:
    """
    Deterministic query router for the RAG pipeline.

    Usage::

        engine = ContextEngine()
        decision = engine.route(
            query="Compare the methods across all papers",
            collection_size=120,
        )
        # decision.strategy == "rlm_analysis"
        # decision.tool_name == "deep_research_rlm"
    """

    def route(
        self,
        query: str,
        collection_size: int = 0,
        user_preference: Optional[str] = None,
    ) -> RoutingDecision:
        """
        Route a query to the best retrieval strategy.

        Args:
            query: The user's natural-language query.
            collection_size: Number of chunks in the target collection
                (0 means unknown).
            user_preference: Optional override — "auto" (default), "simple",
                "deep", or "verified".

        Returns:
            RoutingDecision with strategy, tool name, and suggested params.
        """
        # Hard user overrides
        if user_preference == "simple":
            return self._simple_rag(query, reason="user requested simple mode")
        if user_preference == "deep":
            return self._rlm(query, reason="user requested deep mode")
        if user_preference == "verified":
            return self._two_pass(query, reason="user requested verified mode")

        # Step 1 — Use existing query classifier
        query_type, meta = classify_query(query)

        # Step 2 — Metadata / catalogue queries
        # Only use METADATA_LOOKUP if both the query classifier AND our keyword
        # check agree. The classifier can over-trigger on proper-noun-like
        # scientific terms (e.g. "CRISPR" detected as author name).
        if _METADATA_KEYWORDS.search(query):
            return RoutingDecision(
                strategy=Strategy.METADATA_LOOKUP,
                tool_name="inspect_document_index",
                suggested_params={},
                reasoning="Query asks about document metadata (author, title, listing).",
            )
        if query_type == QueryType.METADATA and meta.get("query_subtype") == "author_search":
            # Only trust author_search if there's an explicit metadata keyword too,
            # otherwise fall through to content-based routing.
            pass  # fall through

        # Step 3 — Triage / relevance ranking
        if _TRIAGE_KEYWORDS.search(query):
            return self._triage(query, reason="Query asks to rank or filter documents by relevance.")

        # Step 3a — Full corpus per-paper narrative analysis
        # Checked before CROSS_DOC because CROSS_DOC patterns are broader.
        if _CORPUS_ANALYSIS_KEYWORDS.search(query):
            return self._corpus_analysis(
                query, reason="Query asks for per-paper findings/analysis across the corpus."
            )

        # Step 4 — Cross-document (per-document iteration) analysis
        if _CROSS_DOC_KEYWORDS.search(query):
            return self._cross_doc(query, reason="Query requires per-document extraction across the entire corpus.")

        # Step 5 — Verification request
        if _VERIFY_KEYWORDS.search(query):
            return self._two_pass(query, reason="Query contains verification language.")

        # Step 6 — Deep / multi-doc queries
        if query_type == QueryType.COMPLEX or _DEEP_KEYWORDS.search(query):
            return self._rlm(
                query,
                reason="Query requires cross-document or deep analysis.",
                collection_size=collection_size,
            )

        # Step 7 — Large collection heuristic
        # If the collection is very large, even a "simple" factual query might
        # benefit from RLM to avoid shallow/noisy results.
        if collection_size > 500:
            return self._rlm(
                query,
                reason=f"Large collection ({collection_size} chunks) — RLM for precision.",
                collection_size=collection_size,
            )

        # Default: simple RAG
        return self._simple_rag(query, reason="Factual point query — simple RAG sufficient.")

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _simple_rag(query: str, reason: str) -> RoutingDecision:
        return RoutingDecision(
            strategy=Strategy.SIMPLE_RAG,
            tool_name="query_documents",
            suggested_params={"max_results": 5},
            reasoning=reason,
        )

    @staticmethod
    def _rlm(
        query: str,
        reason: str,
        collection_size: int = 0,
    ) -> RoutingDecision:
        # Adjust max_turns based on collection size
        if collection_size > 300:
            max_turns = 20
        elif collection_size > 100:
            max_turns = 15
        else:
            max_turns = 10

        return RoutingDecision(
            strategy=Strategy.RLM_ANALYSIS,
            tool_name="deep_research_rlm",
            suggested_params={"max_turns": max_turns, "verify": False},
            reasoning=reason,
        )

    @staticmethod
    def _two_pass(query: str, reason: str) -> RoutingDecision:
        return RoutingDecision(
            strategy=Strategy.TWO_PASS,
            tool_name="deep_research_rlm",
            suggested_params={"max_turns": 15, "verify": True},
            reasoning=reason,
        )

    @staticmethod
    def _cross_doc(query: str, reason: str) -> RoutingDecision:
        return RoutingDecision(
            strategy=Strategy.CROSS_DOC,
            tool_name="cross_document_analysis",
            suggested_params={},
            reasoning=reason,
        )

    @staticmethod
    def _triage(query: str, reason: str) -> RoutingDecision:
        return RoutingDecision(
            strategy=Strategy.TRIAGE,
            tool_name="paper_triage",
            suggested_params={},
            reasoning=reason,
        )

    @staticmethod
    def _corpus_analysis(query: str, reason: str) -> RoutingDecision:
        return RoutingDecision(
            strategy=Strategy.CORPUS_ANALYSIS,
            tool_name="analyze_corpus",
            suggested_params={},
            reasoning=reason,
        )
