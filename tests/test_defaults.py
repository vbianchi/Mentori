"""
tests/test_defaults.py

Validates that all data-driven default values (P0-A, P1-A, P1-B, P1-D) are
correctly set across the codebase.  No LLM calls or network access required.

Motivation:
  V2-1 — BAAI/bge-m3 wins (MRR=0.918); SPECTER2 collapses at scale (0.406)
  V2-3 — simple_512 wins (MRR=0.988); semantic chunking 14× more fragments
  V2-5 — rlm_10 degrades gracefully; rlm_20 collapses to 10% at s100
"""

import inspect
import pytest


# ── P0-A: SPECTER2 removed as default embedding model ───────────────────────

def test_user_collection_embedding_model_default():
    """UserCollection.embedding_model must default to BAAI/bge-m3, not SPECTER2."""
    from backend.retrieval.models import UserCollection
    col = UserCollection(user_id="u1", name="test")
    assert col.embedding_model == "BAAI/bge-m3", (
        f"Expected BAAI/bge-m3, got {col.embedding_model!r}. "
        "SPECTER2 collapses at scale (V2-1 MRR=0.406 at 30 papers)."
    )


def test_user_collection_chunk_size_default():
    """UserCollection.chunk_size must default to 512 tokens (V2-3 optimal)."""
    from backend.retrieval.models import UserCollection
    col = UserCollection(user_id="u1", name="test")
    assert col.chunk_size == 512, (
        f"Expected 512, got {col.chunk_size}. "
        "V2-3 shows simple_512 achieves MRR=0.988."
    )


def test_user_collection_chunking_strategy_default():
    """UserCollection.chunking_strategy must default to 'simple' (V2-3 winner)."""
    from backend.retrieval.models import UserCollection
    col = UserCollection(user_id="u1", name="test")
    assert col.chunking_strategy == "simple", (
        f"Expected 'simple', got {col.chunking_strategy!r}. "
        "V2-3: semantic chunking 14× more fragments than simple."
    )


# ── P1-A: EmbeddingEngine default model ─────────────────────────────────────

def test_embedding_engine_default_model():
    """EmbeddingEngine default model_name must be BAAI/bge-m3."""
    from backend.retrieval.embeddings import EmbeddingEngine
    sig = inspect.signature(EmbeddingEngine.__init__)
    default = sig.parameters["model_name"].default
    assert default == "BAAI/bge-m3", (
        f"Expected BAAI/bge-m3, got {default!r}. "
        "V2-1: BGE-M3 wins at MRR=0.918 across all corpus sizes."
    )


def test_embedding_engine_model_registry_contains_bge_m3():
    """EMBEDDING_MODELS registry must include BAAI/bge-m3."""
    from backend.retrieval.embeddings import EMBEDDING_MODELS
    assert "BAAI/bge-m3" in EMBEDDING_MODELS, "BAAI/bge-m3 not in EMBEDDING_MODELS registry."


def test_embedding_engine_specter2_marked_as_scientific():
    """SPECTER2 must still be in registry (available) but category=scientific."""
    from backend.retrieval.embeddings import EMBEDDING_MODELS
    assert "allenai/specter2" in EMBEDDING_MODELS, "allenai/specter2 removed from registry."
    assert EMBEDDING_MODELS["allenai/specter2"]["category"] == "scientific"


# ── P1-B: jobs.py ingestion settings defaults ───────────────────────────────

def test_jobs_ingestion_defaults_embedding():
    """run_ingestion_job default embedding_model must be BAAI/bge-m3."""
    from backend.retrieval import jobs
    src = inspect.getsource(jobs.run_ingestion_job)
    assert '"embedding_model": "BAAI/bge-m3"' in src, (
        "jobs.run_ingestion_job default ingestion_settings must set "
        'embedding_model to "BAAI/bge-m3".'
    )


def test_jobs_ingestion_defaults_chunk_size():
    """run_ingestion_job default chunk_size must be 512."""
    from backend.retrieval import jobs
    src = inspect.getsource(jobs.run_ingestion_job)
    assert '"chunk_size": 512' in src, (
        "jobs.run_ingestion_job default ingestion_settings must set chunk_size to 512."
    )


def test_jobs_ingestion_defaults_chunking_strategy():
    """run_ingestion_job default chunking_strategy must be 'simple'."""
    from backend.retrieval import jobs
    src = inspect.getsource(jobs.run_ingestion_job)
    assert '"chunking_strategy": "simple"' in src, (
        "jobs.run_ingestion_job default ingestion_settings must set "
        'chunking_strategy to "simple".'
    )


# ── P1-B: SmartIngestor defaults ────────────────────────────────────────────

def test_smart_ingestor_default_embedding_model():
    """SmartIngestor default embedding_model must be BAAI/bge-m3."""
    from backend.retrieval.smart_ingestor import SmartIngestor
    sig = inspect.signature(SmartIngestor.__init__)
    default = sig.parameters["embedding_model"].default
    assert default == "BAAI/bge-m3", (
        f"Expected BAAI/bge-m3, got {default!r}."
    )


def test_smart_ingestor_default_chunk_size():
    """SmartIngestor default chunk_size must be 512."""
    from backend.retrieval.smart_ingestor import SmartIngestor
    sig = inspect.signature(SmartIngestor.__init__)
    default = sig.parameters["chunk_size"].default
    assert default == 512, f"Expected 512, got {default}."


def test_smart_ingestor_default_chunking_strategy():
    """SmartIngestor default chunking_strategy must be 'simple'."""
    from backend.retrieval.smart_ingestor import SmartIngestor
    sig = inspect.signature(SmartIngestor.__init__)
    default = sig.parameters["chunking_strategy"].default
    assert default == "simple", f"Expected 'simple', got {default!r}."


# ── P1-D: deep_research_rlm turn cap ────────────────────────────────────────

def test_deep_research_rlm_max_turns_default():
    """deep_research_rlm max_turns default must be 10 (V2-5: rlm_20 collapses)."""
    from backend.mcp.custom import rag_tools
    sig = inspect.signature(rag_tools.deep_research_rlm)
    default = sig.parameters["max_turns"].default
    assert default == 10, (
        f"Expected max_turns=10, got {default}. "
        "V2-5: rlm_20 degrades to 10% at s100; rlm_10 holds at 30%."
    )


# ── P1-D: query_documents retrieval_mode parameter ──────────────────────────

def test_query_documents_has_retrieval_mode_param():
    """query_documents must accept a retrieval_mode parameter."""
    from backend.mcp.custom import rag_tools
    sig = inspect.signature(rag_tools.query_documents)
    assert "retrieval_mode" in sig.parameters, (
        "query_documents is missing the retrieval_mode parameter."
    )


def test_query_documents_retrieval_mode_default():
    """query_documents retrieval_mode must default to 'single_pass'."""
    from backend.mcp.custom import rag_tools
    sig = inspect.signature(rag_tools.query_documents)
    default = sig.parameters["retrieval_mode"].default
    assert default == "single_pass", (
        f"Expected 'single_pass', got {default!r}."
    )
