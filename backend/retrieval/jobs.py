import logging
import os
from pathlib import Path
from typing import List, Optional
from sqlmodel import Session, select

from backend.database import engine
from backend.retrieval.models import UserCollection, IndexStatus
from backend.retrieval.ingestor import SimpleIngestor
from backend.config import settings

logger = logging.getLogger(__name__)

# Registry database location (one per user)
# NOTE: Put registries INSIDE chroma_db so it's persisted via Docker volume mount
REGISTRY_DIR = os.path.join(settings.CHROMA_PERSIST_DIRECTORY, "registries")


def get_user_registry_path(user_id: str) -> str:
    """Get path to user's document registry database."""
    user_dir = os.path.join(REGISTRY_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "document_registry.db")


def _write_collection(collection_id: str, *, status: Optional[IndexStatus] = None,
                      metrics_update: Optional[dict] = None, **field_updates):
    """
    Open a fresh session, apply updates to a collection, and commit immediately.
    Using a fresh session per write avoids SQLAlchemy identity-map confusion
    across async await boundaries in long-running background jobs.
    """
    with Session(engine) as session:
        coll = session.exec(
            select(UserCollection).where(UserCollection.id == collection_id)
        ).first()
        if not coll:
            logger.warning(f"_write_collection: collection {collection_id} not found")
            return
        if status is not None:
            coll.status = status
        if metrics_update is not None:
            current = coll.metrics  # fresh read via @property
            current.update(metrics_update)
            coll.metrics = current  # write via @setter
        for k, v in field_updates.items():
            setattr(coll, k, v)
        session.add(coll)
        session.commit()

import fitz

# Estimation constants
SECONDS_PER_MB_TEXT = 2.0
SECONDS_PER_MB_OCR = 20.0
OVERHEAD_SECONDS = 5.0

def is_likely_scanned(file_path: str) -> bool:
    """Quick check of first page to see if it's scanned."""
    try:
        doc = fitz.open(file_path)
        if len(doc) > 0:
            text = doc[0].get_text()
            if len(text.strip()) < 50: # Low density threshold
                return True
        doc.close()
    except:
        pass
    return False

def calculate_estimation(file_paths: List[str]) -> int:
    """Calculate estimated processing time in seconds."""
    total_seconds = 0
    
    for fp in file_paths:
        try:
            p = Path(fp)
            if not p.exists():
                continue
                
            size_mb = p.stat().st_size / (1024 * 1024)
            
            # Simple heuristic
            is_scanned = False
            if p.suffix.lower() == ".pdf":
                 is_scanned = is_likely_scanned(fp)
                 
            rate = SECONDS_PER_MB_OCR if is_scanned else SECONDS_PER_MB_TEXT
            total_seconds += (size_mb * rate)
            
        except Exception:
            pass
            
    return int(total_seconds + OVERHEAD_SECONDS)

from backend.models.user import User
from backend.retrieval.agents.transcriber import AgentFactory
from backend.retrieval.schema.registry import DocumentRegistry
from backend.retrieval.smart_ingestor import SmartIngestor
from backend.retrieval.vector_store import VectorStore
import asyncio

async def run_ingestion_job(
    collection_id: str,
    file_paths: List[str],
    ingestion_settings: dict = None,
    use_smart_ingestor: bool = True,
    device: str = "auto",
):
    """
    Background task to ingest documents into a UserCollection.

    Args:
        collection_id: The collection ID to ingest into
        file_paths: List of file paths to ingest
        ingestion_settings: User-configurable settings dict containing:
            - use_vlm: bool - Whether to use VLM for page analysis
            - chunk_size: int - Target chunk size in characters
            - chunk_overlap: int - Number of overlapping sentences
            - embedding_model: str - Embedding model to use
        use_smart_ingestor: If True, use SmartIngestor with metadata extraction (default).
                           If False, fall back to SimpleIngestor.
    """
    # Default settings if not provided
    # Defaults motivated by experiment results:
    #   embedding_model: BAAI/bge-m3 (V2-1: MRR=0.918, best at all scales)
    #   chunking_strategy: simple (V2-3: simple_512 MRR=0.988 vs semantic=0.827)
    #   chunk_size: 512 tokens (V2-3: optimal token count for SimpleChunker)
    if ingestion_settings is None:
        ingestion_settings = {
            "use_vlm": False,
            "chunk_size": 512,
            "chunk_overlap": 2,
            "chunking_strategy": "simple",
            "embedding_model": "BAAI/bge-m3"
        }

    use_vlm = ingestion_settings.get("use_vlm", False)
    chunk_size = ingestion_settings.get("chunk_size", 512)
    chunk_overlap = ingestion_settings.get("chunk_overlap", 2)
    chunking_strategy = ingestion_settings.get("chunking_strategy", "simple")
    embedding_model = ingestion_settings.get("embedding_model", "BAAI/bge-m3")

    # --- 1. Read initial collection info (short-lived session) ---
    with Session(engine) as session:
        collection = session.exec(
            select(UserCollection).where(UserCollection.id == collection_id)
        ).first()
        if not collection:
            logger.error(f"Collection {collection_id} not found for job.")
            return
        collection_name = collection.name
        collection_user_id = collection.user_id

    est_time = calculate_estimation(file_paths)

    # --- 2. Mark PROCESSING with initial metrics ---
    _write_collection(collection_id,
        status=IndexStatus.PROCESSING,
        metrics_update={
            "total_files": len(file_paths),
            "processed_files": 0,
            "status": "starting",
            "file_errors": [],
            "total_chunks": 0,
            "documents_registered": 0,
            "current_file": f"Initializing ({len(file_paths)} files queued)...",
            "current_file_status": "loading",
        },
        estimated_time_seconds=est_time,
    )
    logger.info(f"Starting ingestion job for collection {collection_name} ({collection_id}). Est: {est_time}s")

    try:
        # --- 3. Configure Team ---
        transcriber_agent = None
        transcriber_model_name = None
        agent_roles = {}

        with Session(engine) as session:
            user = session.get(User, collection_user_id)
            if user and user.settings:
                agent_roles = user.settings.get("agent_roles", {})

        if agent_roles:
            transcriber_agent = await AgentFactory.get_transcriber(agent_roles)
            if transcriber_agent:
                transcriber_role = agent_roles.get("transcriber", "")
                if "::" in transcriber_role:
                    transcriber_model_name = transcriber_role.split("::", 1)[1]
                logger.info(f"Deployed Transcriber Agent: {transcriber_model_name}")

        # --- 4. Show "loading embedding model" before expensive init ---
        _write_collection(collection_id, metrics_update={
            "current_file": f"Loading embedding model ({embedding_model.split('/')[-1]})...",
            "current_file_status": "loading",
        })

        chroma_collection_name = f"collection_{collection_id}"

        # --- 5. Initialize Ingestor (loads embedding model into RAM) ---
        if use_smart_ingestor:
            registry_path = get_user_registry_path(collection_user_id)
            registry = DocumentRegistry(registry_path)
            vector_store = VectorStore(collection_name=chroma_collection_name)
            ingestor = SmartIngestor(
                registry=registry,
                vector_store=vector_store,
                agent_roles=agent_roles if agent_roles else None,
                collection_name=chroma_collection_name,
                user_id=collection_user_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunking_strategy=chunking_strategy,
                embedding_model=embedding_model,
                device=device,
            )
            logger.info(f"Using SmartIngestor: VLM={use_vlm}, chunking={chunking_strategy}, "
                        f"chunk_size={chunk_size}, embedding={embedding_model}")
        else:
            ingestor = SimpleIngestor(
                collection_name=chroma_collection_name,
                transcriber=transcriber_agent,
            )
            logger.info("Using legacy SimpleIngestor")

        # --- 6. Ingest files ---
        total_chunks = 0
        documents_registered = 0
        file_errors = []
        processed_count = 0
        total_figures = 0
        total_tables = 0
        total_references = 0
        vlm_model_used = transcriber_model_name

        for fp in file_paths:
            file_name = os.path.basename(fp)

            _write_collection(collection_id, metrics_update={
                "current_file": file_name,
                "current_file_status": "starting",
            })

            if not os.path.exists(fp):
                file_errors.append({"file": file_name, "error": "File not found"})
                processed_count += 1
                continue

            try:
                if use_smart_ingestor:
                    _write_collection(collection_id, metrics_update={
                        "current_file": file_name,
                        "current_file_status": "analyzing with VLM" if use_vlm else "extracting metadata",
                    })

                    result = await ingestor.ingest_file(
                        fp,
                        use_vlm=use_vlm,
                        collection_name=chroma_collection_name,
                        user_id=collection_user_id,
                    )

                    if result.get("doc_id"):
                        chunks_added = result.get("chunk_count", 0)
                        total_chunks += chunks_added
                        documents_registered += 1
                        total_figures += result.get("figure_count", 0)
                        total_tables += result.get("table_count", 0)
                        total_references += result.get("reference_count", 0)
                        if result.get("vlm_model"):
                            vlm_model_used = result.get("vlm_model")
                        logger.info(
                            f"Ingested: {result.get('file_name')} | "
                            f"Title: {result.get('title', 'N/A')[:30]}... | "
                            f"Chunks: {chunks_added}"
                        )
                    else:
                        error_msg = result.get("error", "Unknown ingestion error")
                        file_errors.append({"file": file_name, "error": error_msg})
                        logger.error(f"Ingestion failed for {fp}: {error_msg}")
                else:
                    result = await ingestor.ingest_file(fp)
                    if result.get("status") == "success":
                        total_chunks += result.get("num_chunks", 0)
                    else:
                        error_msg = result.get("error", "Unknown ingestion error")
                        file_errors.append({"file": file_name, "error": error_msg})
                        logger.error(f"Ingestion failed for {fp}: {error_msg}")

            except Exception as e:
                file_errors.append({"file": file_name, "error": str(e)})
                logger.error(f"Exception during ingestion of {fp}: {e}")

            # CHECKPOINT: write progress after each file
            processed_count += 1
            _write_collection(collection_id, metrics_update={
                "processed_files": processed_count,
                "status": "processing",
                "total_chunks": total_chunks,
                "documents_registered": documents_registered,
                "file_errors": file_errors,
                "current_file": file_name,
                "current_file_status": "completed",
                "total_figures": total_figures,
                "total_tables": total_tables,
                "total_references": total_references,
                "vlm_model": vlm_model_used,
            })

        # --- 7. Finalize ---
        final_status = IndexStatus.FAILED if total_chunks == 0 else IndexStatus.READY
        if total_chunks == 0:
            logger.warning(f"Job finished but index is empty. Marking as FAILED. Errors: {file_errors}")

        _write_collection(collection_id,
            status=final_status,
            metrics_update={
                "processed_files": processed_count,
                "status": "completed",
                "total_chunks": total_chunks,
                "documents_registered": documents_registered,
                "file_errors": file_errors,
                "failed_files": len(file_errors),
                "current_file": None,
                "current_file_status": "done",
                "total_figures": total_figures,
                "total_tables": total_tables,
                "total_references": total_references,
                "vlm_model": vlm_model_used,
            },
            vector_db_collection_name=chroma_collection_name,
            ocr_tool="pymupdf",
            transcriber_model=vlm_model_used if (use_vlm and vlm_model_used) else "None",
            **({"error_message": f"Index is empty. {len(file_errors)} files failed."} if total_chunks == 0 else {}),
        )
        logger.info(
            f"Job complete for {collection_name}. Status: {final_status}. "
            f"Chunks: {total_chunks}, Docs: {documents_registered}"
        )

    except Exception as e:
        logger.exception(f"Job crashed for collection {collection_id}")
        _write_collection(collection_id,
            status=IndexStatus.FAILED,
            error_message=f"System Error: {str(e)}",
        )
