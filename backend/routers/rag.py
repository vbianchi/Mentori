from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Dict, Optional
import uuid
import datetime
import logging

logger = logging.getLogger(__name__)

from backend.database import get_session
from backend.auth import get_current_user
from backend.models.user import User
from backend.retrieval.models import UserCollection, IndexStatus
from backend.retrieval.jobs import run_ingestion_job, calculate_estimation
from pydantic import BaseModel

router = APIRouter(prefix="/rag/indexes", tags=["rag"])

# Secondary router for non-index RAG endpoints (mounted separately in main.py)
rag_meta_router = APIRouter(prefix="/rag", tags=["rag"])

# --- Models ---

class IndexCreate(BaseModel):
    name: str
    description: str | None = None
    file_paths: List[str]
    # Ingestion settings
    use_vlm: bool = False  # VLM-assisted page analysis (~5 min per page)
    chunk_size: int = 512  # Target chunk size in tokens (V2-3: simple_512 MRR=0.988)
    chunk_overlap: int = 2  # Number of overlapping sentences
    chunking_strategy: str = "simple"  # "simple" (token-based) or "semantic" (spaCy sentence grouping)
    embedding_model: str = "BAAI/bge-m3"  # V2-1: BGE-M3 wins; SPECTER2 collapses at scale

class IndexUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class IngestionMetrics(BaseModel):
    """Progress metrics during ingestion."""
    total_files: int = 0
    processed_files: int = 0
    status: str = "pending"  # pending, starting, processing, completed
    total_chunks: int = 0
    documents_registered: int = 0
    failed_files: int = 0
    file_errors: List[Dict[str, str]] = []
    # Current file progress
    current_file: str | None = None
    current_file_status: str | None = None
    # VLM extraction stats
    total_figures: int = 0
    total_tables: int = 0
    total_references: int = 0
    vlm_model: str | None = None

class IndexResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    estimated_time_seconds: int
    created_at: datetime.datetime
    file_count: int
    file_paths: List[str]
    error_message: str | None = None
    ocr_tool: str | None = None
    transcriber_model: str | None = None
    metrics: Optional[IngestionMetrics] = None
    # Ingestion settings
    use_vlm: bool = False
    chunk_size: int = 512
    chunk_overlap: int = 2
    chunking_strategy: str = "simple"
    embedding_model: str = "BAAI/bge-m3"


def _build_metrics(raw_metrics: dict) -> Optional[IngestionMetrics]:
    """Convert raw metrics dict from DB to IngestionMetrics model."""
    if not raw_metrics:
        return None
    return IngestionMetrics(
        total_files=raw_metrics.get("total_files", 0),
        processed_files=raw_metrics.get("processed_files", 0),
        status=raw_metrics.get("status", "pending"),
        total_chunks=raw_metrics.get("total_chunks", 0),
        documents_registered=raw_metrics.get("documents_registered", 0),
        failed_files=raw_metrics.get("failed_files", 0),
        file_errors=raw_metrics.get("file_errors", []),
        current_file=raw_metrics.get("current_file"),
        current_file_status=raw_metrics.get("current_file_status"),
        total_figures=raw_metrics.get("total_figures", 0),
        total_tables=raw_metrics.get("total_tables", 0),
        total_references=raw_metrics.get("total_references", 0),
        vlm_model=raw_metrics.get("vlm_model")
    )

import json

@router.post("/", response_model=IndexResponse, status_code=202)
def create_index(
    index_in: IndexCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new search index and start ingestion in the background.
    """
    from backend.mcp.custom.file_ops import _validate_path, SecurityError
    
    # 0. Resolve Paths (Frontend sends relative, we need absolute for Docker)
    resolved_paths = []
    for rel_path in index_in.file_paths:
        try:
            # This resolves "papers/doc.pdf" -> "/app/workspace/USER_ID/papers/doc.pdf"
            # It also ensures security (cant access ../../)
            abs_path = _validate_path(rel_path, current_user.id)
            if not abs_path.exists():
                # We won't block creation, but we log it. The job will report it as failed.
                # Or we could raise 400 here if we want strict validation.
                # Let's trust the job's granular error reporting we just built.
                pass
            resolved_paths.append(str(abs_path))
        except SecurityError:
             logger.warning(f"Security Warning: Skipping unsafe path {rel_path}")
        except Exception as e:
             logger.warning(f"Path Resolution Error for {rel_path}: {e}")

    # 1. Create DB Entry
    index_id = str(uuid.uuid4())
    # Estimate based on the *resolved* paths so file size checks work
    estimate = calculate_estimation(resolved_paths)
    
    # FIX: Explicitly serialize JSON to bypass property setter ambiguity during init/add
    new_index = UserCollection(
        id=index_id,
        user_id=current_user.id,
        name=index_in.name,
        description=index_in.description,
        status=IndexStatus.PENDING,
        estimated_time_seconds=estimate,
        file_paths_json=json.dumps(resolved_paths), # Store ABSOLUTE paths
        # User-configurable ingestion settings
        use_vlm=index_in.use_vlm,
        chunk_size=index_in.chunk_size,
        chunk_overlap=index_in.chunk_overlap,
        chunking_strategy=index_in.chunking_strategy,
        embedding_model=index_in.embedding_model
    )

    session.add(new_index)
    session.commit()
    session.refresh(new_index)

    # 2. Dispatch Background Job with user settings
    ingestion_settings = {
        "use_vlm": index_in.use_vlm,
        "chunk_size": index_in.chunk_size,
        "chunk_overlap": index_in.chunk_overlap,
        "chunking_strategy": index_in.chunking_strategy,
        "embedding_model": index_in.embedding_model
    }
    background_tasks.add_task(run_ingestion_job, index_id, resolved_paths, ingestion_settings)
    
    # Initial metrics for new index
    initial_metrics = IngestionMetrics(
        total_files=len(index_in.file_paths),
        processed_files=0,
        status="pending"
    )

    return IndexResponse(
        id=new_index.id,
        name=new_index.name,
        description=new_index.description,
        status=new_index.status,
        estimated_time_seconds=new_index.estimated_time_seconds,
        created_at=new_index.created_at,
        file_count=len(index_in.file_paths),
        file_paths=index_in.file_paths,
        ocr_tool=new_index.ocr_tool,
        transcriber_model=new_index.transcriber_model,
        metrics=initial_metrics,
        use_vlm=new_index.use_vlm,
        chunk_size=new_index.chunk_size,
        chunk_overlap=new_index.chunk_overlap,
        chunking_strategy=new_index.chunking_strategy,
        embedding_model=new_index.embedding_model
    )

@router.get("/", response_model=List[IndexResponse])
def list_indexes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List all user indexes."""
    indexes = session.exec(
        select(UserCollection)
        .where(UserCollection.user_id == current_user.id)
        .order_by(UserCollection.created_at.desc())
    ).all()
    
    return [
        IndexResponse(
            id=idx.id,
            name=idx.name,
            description=idx.description,
            status=idx.status,
            estimated_time_seconds=idx.estimated_time_seconds,
            created_at=idx.created_at,
            file_count=len(idx.file_paths),
            file_paths=idx.file_paths,
            error_message=idx.error_message,
            ocr_tool=idx.ocr_tool,
            transcriber_model=idx.transcriber_model,
            metrics=_build_metrics(idx.metrics),
            use_vlm=idx.use_vlm,
            chunk_size=idx.chunk_size,
            chunk_overlap=idx.chunk_overlap,
            chunking_strategy=idx.chunking_strategy,
            embedding_model=idx.embedding_model
        ) for idx in indexes
    ]

@router.delete("/{index_id}")
def delete_index(
    index_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete an index."""
    index = session.exec(
        select(UserCollection)
        .where(UserCollection.id == index_id, UserCollection.user_id == current_user.id)
    ).first()
    
    if not index:
        raise HTTPException(status_code=404, detail="Index not found")
        
    # TODO: Clean up ChromaDB collection (future improvement)
    # import chromadb...
    
    session.delete(index)
    session.commit()

    return {"ok": True}

@router.patch("/{index_id}", response_model=IndexResponse)
def update_index(
    index_id: str,
    index_in: IndexUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update an index's name and/or description."""
    index = session.exec(
        select(UserCollection)
        .where(UserCollection.id == index_id, UserCollection.user_id == current_user.id)
    ).first()

    if not index:
        raise HTTPException(status_code=404, detail="Index not found")

    if index_in.name is not None:
        index.name = index_in.name
    if index_in.description is not None:
        index.description = index_in.description

    session.add(index)
    session.commit()
    session.refresh(index)

    return IndexResponse(
        id=index.id,
        name=index.name,
        description=index.description,
        status=index.status,
        estimated_time_seconds=index.estimated_time_seconds,
        created_at=index.created_at,
        file_count=len(index.file_paths),
        file_paths=index.file_paths,
        error_message=index.error_message,
        ocr_tool=index.ocr_tool,
        transcriber_model=index.transcriber_model,
        metrics=_build_metrics(index.metrics),
        use_vlm=index.use_vlm,
        chunk_size=index.chunk_size,
        chunk_overlap=index.chunk_overlap,
        chunking_strategy=index.chunking_strategy,
        embedding_model=index.embedding_model
    )


@router.post("/{index_id}/reindex", status_code=202)
def reindex(
    index_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Re-run ingestion on an existing index using its original settings."""
    index = session.exec(
        select(UserCollection)
        .where(UserCollection.id == index_id, UserCollection.user_id == current_user.id)
    ).first()

    if not index:
        raise HTTPException(status_code=404, detail="Index not found")

    index.status = IndexStatus.PENDING
    index.error_message = None
    index.metrics_json = "{}"
    session.add(index)
    session.commit()

    ingestion_settings = {
        "use_vlm": index.use_vlm,
        "chunk_size": index.chunk_size,
        "chunk_overlap": index.chunk_overlap,
        "chunking_strategy": index.chunking_strategy,
        "embedding_model": index.embedding_model
    }
    background_tasks.add_task(run_ingestion_job, index_id, index.file_paths, ingestion_settings)

    return {"ok": True, "status": "PENDING"}


# ── Meta endpoints (embedding models, etc.) ──────────────────────────────────

@rag_meta_router.get("/embedding-models")
def list_embedding_models():
    """Return the list of supported embedding models for the frontend dropdown."""
    from backend.retrieval.embeddings import get_available_models
    return get_available_models()
