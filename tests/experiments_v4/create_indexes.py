"""
Create V4 Experiment Indexes (Factorial Design)

Creates 12 BGE-M3 indexes for the V4 factorial experimental design:

| Index Name     | Core Papers | Noise Ratio | Noise Papers | Total |
|----------------|-------------|-------------|--------------|-------|
| exp_v4_s5_n0   | 5           | 0x          | 0            | 5     |
| exp_v4_s5_n1   | 5           | 1x          | 5            | 10    |
| exp_v4_s5_n3   | 5           | 3x          | 15           | 20    |
| exp_v4_s10_n0  | 10          | 0x          | 0            | 10    |
| exp_v4_s10_n1  | 10          | 1x          | 10           | 20    |
| exp_v4_s10_n3  | 10          | 3x          | 30           | 40    |
| exp_v4_s20_n0  | 20          | 0x          | 0            | 20    |
| exp_v4_s20_n1  | 20          | 1x          | 20           | 40    |
| exp_v4_s20_n3  | 20          | 3x          | 60           | 80    |
| exp_v4_s50_n0  | 50          | 0x          | 0            | 50    |
| exp_v4_s50_n1  | 50          | 1x          | 50           | 100   |
| exp_v4_s50_n3  | 50          | 3x          | 150          | 200   |

All indexes use:
- Embedding: BAAI/bge-m3 (1024 dims)
- Chunking: SimpleChunker(512, 50) — token-based
- Same admin user_id

Core papers are nested: Core_5 ⊂ Core_10 ⊂ Core_20 ⊂ Core_50
Papers are stored in datasets/v4_papers/core/ with ID prefixes (01_xxx.pdf, 02_xxx.pdf, etc.)
Noise papers are in datasets/v4_papers/noise/

Usage:
    uv run python tests/experiments_v4/create_indexes.py
    uv run python tests/experiments_v4/create_indexes.py --indexes exp_v4_s5_n0 exp_v4_s10_n1
    uv run python tests/experiments_v4/create_indexes.py --core-sizes 5 10 --noise-ratios 0 1
    uv run python tests/experiments_v4/create_indexes.py --dry-run
    uv run python tests/experiments_v4/create_indexes.py --list
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("create_indexes")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

# V4 dataset directories
DATASETS_DIR = PROJECT_ROOT / "datasets"
V4_PAPERS_DIR = DATASETS_DIR / "v4_papers"
CORE_PAPERS_DIR = V4_PAPERS_DIR / "core"
NOISE_PAPERS_DIR = V4_PAPERS_DIR / "noise"
RESULTS_DIR = PROJECT_ROOT / "tests" / "experiments_v4" / "results_v4"

EMBEDDING_MODEL = "BAAI/bge-m3"
CHUNK_SIZE = 512       # tokens (SimpleChunker)
CHUNK_OVERLAP = 50     # tokens

ADMIN_EMAILS = ["admin@wur.nl", "admin@mentori"]

# Factorial design parameters
CORE_SIZES = [5, 10, 20, 50]
NOISE_RATIOS = [0, 1, 3]  # 0x, 1x, 3x multiplier

# Core paper ID ranges for nested subsets
# Core_5: Bioinformatics foundation (papers 1-5)
# Core_10: Full bioinformatics (papers 1-10)
# Core_20: Bioinformatics + Veterinary Epidemiology (papers 1-20)
# Core_50: All papers
CORE_5_IDS = [1, 2, 3, 4, 5]
CORE_10_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
CORE_20_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
# Core_50 uses all available papers


def _detect_device() -> str:
    """Detect best available compute device."""
    import torch
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _device_label(device: str) -> str:
    """Human-readable device label."""
    labels = {
        "mps": "Apple Metal GPU (MPS)",
        "cuda": "NVIDIA GPU (CUDA)",
        "cpu": "CPU",
    }
    return labels.get(device, device)


def get_index_name(core_size: int, noise_ratio: int) -> str:
    """Generate index name from factorial parameters."""
    return f"exp_v4_s{core_size}_n{noise_ratio}"


def build_index_configs() -> dict:
    """Build all 12 factorial index configurations."""
    configs = {}
    for core_size in CORE_SIZES:
        for noise_ratio in NOISE_RATIOS:
            name = get_index_name(core_size, noise_ratio)
            noise_papers = core_size * noise_ratio
            configs[name] = {
                "core_size": core_size,
                "noise_ratio": noise_ratio,
                "noise_papers": noise_papers,
                "total": core_size + noise_papers,
            }
    return configs


# Build the factorial configuration
INDEX_CONFIGS = build_index_configs()


# ─────────────────────────────────────────────────────────────
# Helper: find admin user
# ─────────────────────────────────────────────────────────────

def _find_admin_user_id() -> str:
    from backend.database import engine
    from backend.models.user import User
    from sqlmodel import Session, select

    with Session(engine) as session:
        for email in ADMIN_EMAILS:
            user = session.exec(
                select(User).where(User.email == email)
            ).first()
            if user:
                return str(user.id)

    raise RuntimeError(f"No admin user found. Tried: {ADMIN_EMAILS}")


# ─────────────────────────────────────────────────────────────
# Build paper lists for factorial design
# ─────────────────────────────────────────────────────────────

def _get_all_core_papers() -> Dict[int, Path]:
    """Get all core papers indexed by their ID.

    Papers are named with ID prefixes: 01_name.pdf, 02_name.pdf, etc.
    """
    papers = {}
    if not CORE_PAPERS_DIR.exists():
        logger.warning(f"Core papers directory not found: {CORE_PAPERS_DIR}")
        return papers

    for pdf in CORE_PAPERS_DIR.glob("*.pdf"):
        # Extract ID from filename (e.g., "01_nfcore_framework.pdf" -> 1)
        name = pdf.name
        if "_" in name:
            try:
                paper_id = int(name.split("_")[0])
                papers[paper_id] = pdf
            except ValueError:
                logger.warning(f"Could not parse ID from: {name}")

    return papers


def _get_core_papers(core_size: int) -> List[str]:
    """Get core papers for a given size level.

    Core papers are nested: Core_5 ⊂ Core_10 ⊂ Core_20 ⊂ Core_50
    Papers are selected by ID based on predefined subsets.
    """
    all_papers = _get_all_core_papers()

    # Select IDs based on core size
    if core_size == 5:
        target_ids = CORE_5_IDS
    elif core_size == 10:
        target_ids = CORE_10_IDS
    elif core_size == 20:
        target_ids = CORE_20_IDS
    else:
        # Core_50: use all available papers
        target_ids = sorted(all_papers.keys())

    # Get paper paths for target IDs
    papers = []
    for paper_id in target_ids:
        if paper_id in all_papers:
            papers.append(str(all_papers[paper_id]))
        else:
            logger.warning(f"Paper ID {paper_id} not found in core papers")

    # Verify we have enough papers
    if len(papers) < core_size:
        logger.warning(
            f"Requested {core_size} core papers but only {len(papers)} available."
        )

    return papers[:core_size]


def _get_noise_papers(count: int) -> List[str]:
    """Get noise papers from the noise pool.

    Returns first N papers from datasets/v4_papers/noise/ (sorted for determinism).
    """
    if not NOISE_PAPERS_DIR.exists():
        logger.warning(f"Noise papers directory not found: {NOISE_PAPERS_DIR}")
        return []

    all_noise = sorted(NOISE_PAPERS_DIR.glob("*.pdf"))

    if len(all_noise) < count:
        logger.warning(
            f"Requested {count} noise papers but only {len(all_noise)} available."
        )
        count = len(all_noise)

    return [str(p) for p in all_noise[:count]]


def _get_file_list(index_name: str) -> List[str]:
    """Get the full file list for an index config."""
    config = INDEX_CONFIGS[index_name]
    core_size = config["core_size"]
    noise_papers = config["noise_papers"]

    # Core papers (nested subsets)
    core_paths = _get_core_papers(core_size)

    # Noise papers (first N from pool)
    noise_paths = _get_noise_papers(noise_papers)

    return core_paths + noise_paths


# ─────────────────────────────────────────────────────────────
# Check existing indexes
# ─────────────────────────────────────────────────────────────

def _check_existing_indexes(user_id: str) -> Dict[str, dict]:
    """Check which experiment indexes already exist in the DB."""
    from backend.database import engine
    from backend.retrieval.models import UserCollection
    from sqlmodel import Session, select

    existing = {}
    with Session(engine) as session:
        for name in INDEX_CONFIGS:
            collection = session.exec(
                select(UserCollection)
                .where(UserCollection.user_id == user_id)
                .where(UserCollection.name == name)
            ).first()
            if collection:
                existing[name] = {
                    "id": collection.id,
                    "status": collection.status.value,
                    "embedding_model": collection.embedding_model,
                    "chunks": collection.metrics.get("total_chunks", "?"),
                    "vector_db_collection_name": collection.vector_db_collection_name,
                }

    return existing


# ─────────────────────────────────────────────────────────────
# Create a single index
# ─────────────────────────────────────────────────────────────

async def create_single_index(
    index_name: str,
    user_id: str,
    force: bool = False,
    device: str = "cpu",
) -> dict:
    """Create a single experiment index.

    Returns dict with creation result (id, status, chunks, time).
    """
    from backend.database import engine
    from backend.retrieval.models import UserCollection, IndexStatus
    from backend.retrieval.jobs import run_ingestion_job
    from sqlmodel import Session, select

    config = INDEX_CONFIGS[index_name]
    file_list = _get_file_list(index_name)

    # Verify files exist
    missing = [f for f in file_list if not os.path.exists(f)]
    if missing:
        return {"index": index_name, "error": f"{len(missing)} files not found", "missing": missing[:5]}

    # Check if already exists
    with Session(engine) as session:
        existing = session.exec(
            select(UserCollection)
            .where(UserCollection.user_id == user_id)
            .where(UserCollection.name == index_name)
        ).first()

        if existing:
            if not force:
                return {
                    "index": index_name,
                    "status": "skipped",
                    "reason": f"Already exists (status={existing.status.value}, "
                              f"chunks={existing.metrics.get('total_chunks', '?')}). "
                              f"Use --force to recreate.",
                    "id": existing.id,
                }
            else:
                # Delete existing collection from ChromaDB
                if existing.vector_db_collection_name:
                    try:
                        from backend.retrieval.vector_store import VectorStore
                        vs = VectorStore()
                        vs.client.delete_collection(existing.vector_db_collection_name)
                        logger.info(f"Deleted ChromaDB collection: {existing.vector_db_collection_name}")
                    except Exception as e:
                        logger.warning(f"Could not delete ChromaDB collection: {e}")

                # Delete DB record
                session.delete(existing)
                session.commit()
                logger.info(f"Deleted existing DB record for {index_name}")

    # Create new UserCollection
    collection_id = str(uuid.uuid4())
    description = (
        f"V4 experiment index: {config['core_size']} core + {config['noise_papers']} noise = "
        f"{config['total']} papers. Embedding: {EMBEDDING_MODEL}, "
        f"Chunking: SimpleChunker({CHUNK_SIZE}, {CHUNK_OVERLAP})"
    )

    with Session(engine) as session:
        collection = UserCollection(
            id=collection_id,
            user_id=user_id,
            name=index_name,
            description=description,
            status=IndexStatus.PENDING,
            file_paths_json=json.dumps([os.path.basename(f) for f in file_list]),
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            embedding_model=EMBEDDING_MODEL,
        )
        session.add(collection)
        session.commit()

    logger.info(
        f"Created UserCollection: {index_name} (id={collection_id[:8]}..., "
        f"{len(file_list)} files)"
    )

    # Run ingestion
    started_at = datetime.now()
    t0 = time.time()
    ingestion_settings = {
        "use_vlm": False,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "embedding_model": EMBEDDING_MODEL,
    }

    await run_ingestion_job(
        collection_id=collection_id,
        file_paths=file_list,
        ingestion_settings=ingestion_settings,
        use_smart_ingestor=True,
        device=device,
    )
    elapsed = time.time() - t0
    finished_at = datetime.now()

    # Read final status
    with Session(engine) as session:
        collection = session.exec(
            select(UserCollection).where(UserCollection.id == collection_id)
        ).first()

        result = {
            "index": index_name,
            "id": collection_id,
            "status": collection.status.value if collection else "UNKNOWN",
            "total_files": len(file_list),
            "core_papers": config["core_size"],
            "noise_papers": config["noise_papers"],
            "total_chunks": collection.metrics.get("total_chunks", 0) if collection else 0,
            "documents_registered": collection.metrics.get("documents_registered", 0) if collection else 0,
            "file_errors": len(collection.metrics.get("file_errors", [])) if collection else 0,
            "vector_db_collection": collection.vector_db_collection_name if collection else None,
            "embedding_model": EMBEDDING_MODEL,
            "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_s": round(elapsed, 1),
        }

        if collection and collection.metrics.get("file_errors"):
            result["error_details"] = collection.metrics["file_errors"]

        return result


# ─────────────────────────────────────────────────────────────
# Print helpers
# ─────────────────────────────────────────────────────────────

def print_status(existing: Dict[str, dict]):
    """Print current index status table."""
    print(f"\n{'='*80}")
    print("V4 EXPERIMENT INDEX STATUS")
    print(f"{'='*80}")
    print(f"{'Index':<16} | {'Status':<12} | {'Chunks':>8} | {'Embedding':<20} | {'ID':<12}")
    print("-" * 80)

    for name in INDEX_CONFIGS:
        if name in existing:
            info = existing[name]
            print(
                f"{name:<16} | {info['status']:<12} | {str(info['chunks']):>8} | "
                f"{info['embedding_model']:<20} | {info['id'][:12]}"
            )
        else:
            print(
                f"{name:<16} | {'NOT CREATED':<12} | {'-':>8} | "
                f"{'-':<20} | {'-':<12}"
            )

    print()


def print_dry_run():
    """Print what would be created."""
    all_core = _get_all_core_papers()
    all_noise = list(NOISE_PAPERS_DIR.glob("*.pdf")) if NOISE_PAPERS_DIR.exists() else []

    print(f"\n{'='*80}")
    print("DRY RUN — V4 Index Creation Plan")
    print(f"{'='*80}\n")

    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Chunking: SimpleChunker({CHUNK_SIZE}, {CHUNK_OVERLAP})")
    print(f"Core papers directory: {CORE_PAPERS_DIR}")
    print(f"Noise papers directory: {NOISE_PAPERS_DIR}")
    print(f"Core papers available: {len(all_core)}")
    print(f"Noise papers available: {len(all_noise)}\n")

    print("Core paper subsets:")
    print(f"  Core_5:  {len(_get_core_papers(5))} papers - IDs {CORE_5_IDS}")
    print(f"  Core_10: {len(_get_core_papers(10))} papers - IDs {CORE_10_IDS}")
    print(f"  Core_20: {len(_get_core_papers(20))} papers - IDs {CORE_20_IDS[:10]}...")
    print(f"  Core_50: {len(_get_core_papers(50))} papers - all available")

    print(f"\nIndexes to create:")
    print(f"{'Index':<16} | {'Core':>6} | {'Noise':>6} | {'Total':>6} | {'Est. Size':>10}")
    print("-" * 60)

    for name, cfg in INDEX_CONFIGS.items():
        file_list = _get_file_list(name)
        total_size_mb = sum(
            Path(f).stat().st_size / (1024 * 1024)
            for f in file_list if Path(f).exists()
        )
        missing = len([f for f in file_list if not Path(f).exists()])
        missing_str = f" ({missing} missing)" if missing > 0 else ""
        print(
            f"{name:<16} | {cfg['core_size']:>6} | {cfg['noise_papers']:>6} | "
            f"{cfg['total']:>6} | {total_size_mb:>8.1f} MB{missing_str}"
        )

    print()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="Create V4 experiment indexes (factorial design)"
    )
    parser.add_argument(
        "--indexes",
        nargs="+",
        choices=list(INDEX_CONFIGS.keys()),
        default=None,
        help="Specific indexes to create (default: all)",
    )
    parser.add_argument(
        "--core-sizes",
        nargs="+",
        type=int,
        choices=CORE_SIZES,
        default=None,
        help="Filter by core sizes (e.g., --core-sizes 5 10)",
    )
    parser.add_argument(
        "--noise-ratios",
        nargs="+",
        type=int,
        choices=NOISE_RATIOS,
        default=None,
        help="Filter by noise ratios (e.g., --noise-ratios 0 1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recreate indexes even if they already exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without doing anything",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List current index status and exit",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "mps", "cuda", "auto"],
        default="cpu",
        help="Device for embedding model (default: cpu). MPS/CUDA can cause OOM with large models like BGE-M3.",
    )
    args = parser.parse_args()

    # Dry run doesn't need DB
    if args.dry_run:
        print_dry_run()
        return

    # All other modes need admin user
    user_id = _find_admin_user_id()
    logger.info(f"Admin user ID: {user_id}")

    # List mode
    if args.list:
        existing = _check_existing_indexes(user_id)
        print_status(existing)
        return

    # Determine which indexes to create
    if args.indexes:
        indexes_to_create = args.indexes
    else:
        indexes_to_create = []
        for name, cfg in INDEX_CONFIGS.items():
            if args.core_sizes and cfg["core_size"] not in args.core_sizes:
                continue
            if args.noise_ratios and cfg["noise_ratio"] not in args.noise_ratios:
                continue
            indexes_to_create.append(name)

    if not indexes_to_create:
        print("No indexes matched the filter criteria.")
        return

    existing = _check_existing_indexes(user_id)
    device = args.device
    detected = _detect_device()

    print(f"\n{'='*80}")
    print("V4 EXPERIMENT INDEX CREATION")
    print(f"{'='*80}")
    print(f"Embedding: {EMBEDDING_MODEL}")
    print(f"Chunking: SimpleChunker({CHUNK_SIZE}, {CHUNK_OVERLAP})")
    print(f"Compute:  {_device_label(device)} (detected: {_device_label(detected)})")
    print(f"User:     {user_id}")
    print(f"Indexes:  {', '.join(indexes_to_create)}")
    print(f"Started:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.force:
        print("Mode:     FORCE (recreating existing indexes)")
    print(f"{'='*80}\n")

    # Create indexes sequentially (they share the embedding model in memory)
    results = []
    total_t0 = time.time()

    for i, index_name in enumerate(indexes_to_create, 1):
        cfg = INDEX_CONFIGS[index_name]
        print(f"\n[{i}/{len(indexes_to_create)}] Creating {index_name} "
              f"({cfg['core_size']} core + {cfg['noise_papers']} noise = {cfg['total']} papers)...")

        result = await create_single_index(
            index_name=index_name,
            user_id=user_id,
            force=args.force,
            device=args.device,
        )
        results.append(result)

        status = result.get("status", "unknown")
        if status == "skipped":
            print(f"  -> SKIPPED: {result['reason']}")
        elif "error" in result:
            print(f"  -> ERROR: {result['error']}")
        else:
            print(
                f"  -> {status} | {result.get('total_chunks', 0)} chunks | "
                f"{result.get('documents_registered', 0)} docs | "
                f"{result.get('elapsed_s', 0):.0f}s"
            )
            print(
                f"     started: {result.get('started_at', '?')} | "
                f"finished: {result.get('finished_at', '?')}"
            )
            if result.get("file_errors", 0) > 0:
                print(f"     WARNING: {result['file_errors']} file errors")

    total_elapsed = time.time() - total_t0

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Index':<16} | {'Status':<10} | {'Chunks':>8} | {'Docs':>6} | {'Errors':>6} | {'Time':>8}")
    print("-" * 70)

    for r in results:
        if r.get("status") == "skipped":
            print(f"{r['index']:<16} | {'SKIPPED':<10} | {'-':>8} | {'-':>6} | {'-':>6} | {'-':>8}")
        elif "error" in r:
            print(f"{r['index']:<16} | {'ERROR':<10} | {'-':>8} | {'-':>6} | {'-':>6} | {'-':>8}")
        else:
            print(
                f"{r['index']:<16} | {r['status']:<10} | "
                f"{r.get('total_chunks', 0):>8} | "
                f"{r.get('documents_registered', 0):>6} | "
                f"{r.get('file_errors', 0):>6} | "
                f"{r.get('elapsed_s', 0):>7.0f}s"
            )

    print(f"\nCompute device: {_device_label(args.device)}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")

    # Save JSON results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RESULTS_DIR / f"create_indexes_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "user_id": user_id,
            "embedding_model": EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "compute_device": args.device,
            "compute_device_label": _device_label(args.device),
            "core_sizes": CORE_SIZES,
            "noise_ratios": NOISE_RATIOS,
            "results": results,
            "total_elapsed_s": round(total_elapsed, 1),
        }, f, indent=2)
    print(f"\nResults JSON: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
