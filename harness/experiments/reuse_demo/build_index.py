#!/usr/bin/env python3
"""Build a search index from a folder of PDFs, exactly as the paper built its indexes (I2, D160 (14); i2_plan.md A2).

    # what it would do: the files and their sha256, the store; no model, nothing written
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/build_index.py plan \
        --corpus experiments/reuse_demo/corpus/core --manifest experiments/reuse_demo/corpus_papers.csv

    # 1. the gate: rebuild the paper's 20-paper index into a new scratch store; it must match the recorded one
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/build_index.py gate \
        --papers-dir ~/projects/Mentori-paper/datasets/v4_papers/core --store ~/paper_store_i2/gate_s20

    # 2. the index of a new corpus, into a new store (refused unless step 1 passed with this same code)
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/build_index.py build \
        --corpus experiments/reuse_demo/corpus/core --manifest experiments/reuse_demo/corpus_papers.csv \
        --index i2_plant5 --store ~/paper_store_i2/original

WHAT IT DOES. The steps of the paper's index builder, recovered_harness/tests/experiments_v4/create_indexes.py
create_single_index (lines 287-420): a UserCollection row (chunk size 512, overlap 50, embedding BAAI/bge-m3), then
Mentori's run_ingestion_job with use_vlm False and the smart ingestor (SmartIngestor: text extraction, the
SimpleChunker at 512 tokens with 50 overlap, bge-m3 embeddings into Chroma), on the CPU. The encoder is the snapshot
LOCK.toml [retrieval] embedding names (revision, local files only, device cpu): Mentori's embeddings.py loads only
that one and refuses any other model or device. With VLM off and an admin user whose settings name no agent roles,
the ingestion calls no language model (jobs.py reads agent_roles from the user's settings; smart_ingestor.py:276 asks
a VLM only when use_vlm is true); bge-m3 is the only model it runs.

THE STORE. Every run makes a new store, a folder holding mentori_app.db (the users and indexes) and chroma_db (the
chunks and their vectors); a folder that already exists is refused, never written into. The store is created by
Mentori's own init_db() (its tables and its default admin user, admin@mentori, whose settings are empty), with
DATABASE_URL and CHROMA_PERSIST_DIRECTORY pointing into the folder and the folder as working directory (Mentori's
settings read a .env from the working directory; the new folder has none).

THE GATE (README.md:75-79, "reproduce before writing"). Before a new corpus is indexed, `gate` rebuilds the paper's
own index exp_v4_s20_n0 from its 20 core PDFs (papers 01 to 20 by their file name prefix, in that order, as
create_indexes.py _get_core_papers(20) lists them) into a scratch store and compares the result with the identity
recorded for the index every Figure 2 answer was made on (findings/recompute/K0/bundle/sink/index_identity.jsonl:1;
experiments/runner/index_identity.py): GATE_CHUNKS chunks and chunk_manifest_sha256 GATE_MANIFEST (the sorted lines
file name, chunk index and sha256 of each chunk's text). It passes only when both are equal, the index is READY, all 20
files were registered and no file failed. Vectors are not compared (index_identity hashes texts only). The verdict
goes to --record (default findings/recompute/I2_runs/index_gate.json) with the code identity (CODE: this file and the
Mentori files that chunk and embed, with the lock's [retrieval] embedding row). `build` refuses unless that record
passed under the same code identity, so a change to the chunker or the encoder needs a new gate.

THE FILES. `build` indexes every PDF of --corpus, sorted by file name. --manifest (the corpus_papers.csv of
download_papers.py, D74): its rows of bucket "core" must name exactly those files, else the build is refused. Each
file's sha256 is recorded.

OUTPUT. The store, and --record (default findings/recompute/I2_runs/index_<index>.json): the index identity
(index_identity.identity: collection, chunk count, id_text_sha256, chunk_manifest_sha256), the ingestion metrics
(chunks, documents, file errors), the files with their sha256, the code identity, the lock sha256, the gate record's
sha256, the free memory at the start and the wall time. A build with any file error is written as failed and exits 1.

MEASURED WITHOUT THE ENCODER (27 October, laptop): ingest with bge-m3 stood in by vectors of ones (check_i2.py part
C; the chunk texts do not depend on the vectors) gives the gate's 778 chunks and chunk manifest b9affe3f..., so the
gate passes on the chunking; and the plant corpus gives 222 chunks from 5 files, chunk_manifest_sha256
2cf6bf6f04f64a4c5bbdd1d4abb5c9dcdb5969b6a3c750e1a305cc9f96449615 (PLANT_MANIFEST). launch_i2.sh index-build passes it
as --expect-manifest, so a real build that gives other chunk texts is written as failed.

MEMORY (D160 (14)). Refused at the start when free memory is under --min-free-gb (default 2; i2_memory.py); bge-m3 on
the CPU takes about 2 to 3 GB while it embeds (UNVERIFIED on the laptop; the Studio's 20-paper build took 117 s,
findings/recompute/S141_create_indexes_rebuild.json).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MENTORI = ROOT / "experiments" / "mentori"
sys.path.insert(0, str(ROOT))
from experiments.reuse_demo import i2_memory  # noqa: E402

I2_RUNS = ROOT / "findings" / "recompute" / "I2_runs"
GATE_RECORD = I2_RUNS / "index_gate.json"
GATE_INDEX = "exp_v4_s20_n0"
GATE_IDS = tuple(range(1, 21))                         # create_indexes.py CORE_20_IDS
GATE_CHUNKS = 778
GATE_MANIFEST = "b9affe3fecad2245d24c8ed2379dd700d6d1041473595d1c7e738bccad9d51e2"
GATE_SOURCE = "findings/recompute/K0/bundle/sink/index_identity.jsonl:1"
PLANT_MANIFEST = "2cf6bf6f04f64a4c5bbdd1d4abb5c9dcdb5969b6a3c750e1a305cc9f96449615"   # i2_plant5, 222 chunks (docstring)
EMBEDDING_MODEL = "BAAI/bge-m3"                       # create_indexes.py EMBEDDING_MODEL
CHUNK_SIZE, CHUNK_OVERLAP = 512, 50                   # create_indexes.py CHUNK_SIZE, CHUNK_OVERLAP
DEVICE = "cpu"                                        # LOCK.toml [retrieval] embedding device (D69)
CODE = ("experiments/reuse_demo/build_index.py",
        "experiments/mentori/backend/retrieval/jobs.py",
        "experiments/mentori/backend/retrieval/smart_ingestor.py",
        "experiments/mentori/backend/retrieval/chunking.py",
        "experiments/mentori/backend/retrieval/embeddings.py",
        "experiments/mentori/backend/retrieval/vector_store.py",
        "experiments/mentori/backend/database.py",
        "experiments/runner/index_identity.py")


class Refused(SystemExit):
    def __init__(self, msg: str):
        super().__init__(f"REFUSED: {msg}")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lock_embedding_row() -> dict:
    """LOCK.toml [retrieval] embedding, read with the standard library's TOML reader."""
    import tomllib
    return tomllib.loads((ROOT / "experiments" / "LOCK.toml").read_text())["retrieval"]["embedding"]


def code_identity() -> dict:
    """sha256 of every file in CODE, and the lock's [retrieval] embedding row."""
    out = {f: sha256_file(ROOT / f) for f in CODE}
    out["lock_retrieval_embedding"] = lock_embedding_row()
    return out


def gate_files(papers_dir: Path) -> list[Path]:
    """The 20 core PDFs of exp_v4_s20_n0, in create_indexes.py's order (ids 1 to 20 by the file name's prefix)."""
    by_id = {}
    for p in Path(papers_dir).glob("*.pdf"):
        head = p.name.split("_", 1)[0]
        if "_" in p.name and head.isdigit():
            if int(head) in by_id:
                raise Refused(f"{papers_dir}: two PDFs with id {int(head)}")
            by_id[int(head)] = p
    missing = [i for i in GATE_IDS if i not in by_id]
    if missing:
        raise Refused(f"{papers_dir}: no PDF for core paper ids {missing}")
    return [by_id[i] for i in GATE_IDS]


def corpus_files(corpus: Path, manifest: Path | None) -> list[Path]:
    """Every PDF of corpus, sorted by name; with a manifest, its core rows must name exactly these files."""
    files = sorted(Path(corpus).glob("*.pdf"), key=lambda p: p.name)
    if not files:
        raise Refused(f"{corpus} holds no PDF")
    if manifest is not None:
        with open(manifest, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        if not rows or "filename" not in rows[0]:
            raise Refused(f"{manifest}: no 'filename' column")
        named = sorted(r["filename"] for r in rows if r.get("bucket", "core") == "core")
        if named != [p.name for p in files]:
            raise Refused(f"{manifest} names {named}, the folder holds {[p.name for p in files]}")
    return files


def file_list(files: list[Path]) -> list[dict]:
    return [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in files]


def fresh_store(store: Path) -> Path:
    """A new, empty store folder; an existing path is refused."""
    store = Path(store).expanduser().resolve()
    if store.exists():
        raise Refused(f"{store} exists; every build makes a new store (move it aside to rebuild)")
    store.mkdir(parents=True)
    return store


def memory_or_refuse(floor_gb: float) -> float | None:
    low, r = i2_memory.under(floor_gb)
    if low:
        raise Refused(f"free memory {r if r is None else round(r, 2)} GB is under the floor of {floor_gb} GB (D160 (14))")
    return r


def prepare(store: Path, index_name: str, files: list[Path], description: str) -> tuple[str, str]:
    """The store's tables and admin user (Mentori's init_db) and the index's UserCollection row, as create_single_index
    writes it: (collection_id, user_id). No model. Runs in Mentori's environment; the store's environment is set before
    Mentori is imported."""
    os.environ["DATABASE_URL"] = f"sqlite:///{store}/mentori_app.db"
    os.environ["CHROMA_PERSIST_DIRECTORY"] = str(store / "chroma_db")
    os.chdir(store)                                    # Mentori's settings read .env from here: the new folder has none
    sys.path.insert(0, str(MENTORI))
    from backend.config import settings
    if (settings.DATABASE_URL != os.environ["DATABASE_URL"]
            or settings.CHROMA_PERSIST_DIRECTORY != os.environ["CHROMA_PERSIST_DIRECTORY"]):
        raise Refused("Mentori's settings were read before the store was set (backend.config imported too early)")
    from backend.database import engine, init_db
    from backend.models.user import User
    from backend.retrieval.models import UserCollection, IndexStatus
    from sqlmodel import Session, select

    init_db()
    with Session(engine) as session:
        admins = session.exec(select(User).where(User.role == "admin")).all()
        if len(admins) != 1 or admins[0].settings:
            raise Refused(f"the new store has {len(admins)} admin users, or its admin's settings are not empty")
        user_id = str(admins[0].id)
    collection_id = str(uuid.uuid4())
    with Session(engine) as session:
        session.add(UserCollection(id=collection_id, user_id=user_id, name=index_name, description=description,
                                   status=IndexStatus.PENDING,
                                   file_paths_json=json.dumps([p.name for p in files]),
                                   chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
                                   embedding_model=EMBEDDING_MODEL))
        session.commit()
    return collection_id, user_id


def ingest(store: Path, index_name: str, files: list[Path], description: str) -> dict:
    """create_single_index's steps in a new store (module docstring): prepare(), then Mentori's run_ingestion_job;
    returns the collection's metrics and the index identity. The store is the working directory while Mentori runs
    (its logging and settings use it); the caller's working directory is put back after."""
    files = [Path(p).resolve() for p in files]           # read from the store's folder
    store = Path(store).resolve()
    old = os.getcwd()
    try:
        return _ingest(store, index_name, files, description)
    finally:
        os.chdir(old)


def _ingest(store: Path, index_name: str, files: list[Path], description: str) -> dict:
    collection_id, user_id = prepare(store, index_name, files, description)
    from backend.database import engine
    from backend.retrieval.models import UserCollection
    from backend.retrieval.jobs import run_ingestion_job
    from sqlmodel import Session, select
    from experiments.runner import index_identity as ii
    t0 = time.time()
    asyncio.run(run_ingestion_job(collection_id=collection_id, file_paths=[str(p) for p in files],
                                  ingestion_settings={"use_vlm": False, "chunk_size": CHUNK_SIZE,
                                                      "chunk_overlap": CHUNK_OVERLAP,
                                                      "embedding_model": EMBEDDING_MODEL},
                                  use_smart_ingestor=True, device=DEVICE))
    wall = round(time.time() - t0, 1)
    with Session(engine) as session:
        c = session.exec(select(UserCollection).where(UserCollection.id == collection_id)).first()
        status = c.status.value if c else None
        metrics = dict(c.metrics) if c else {}
        collection = c.vector_db_collection_name if c else None
    ident = ii.identity(store / "chroma_db", collection, index_name) if status == "READY" and collection else None
    return {"status": status, "collection": collection, "collection_id": collection_id, "user_id": user_id,
            "total_chunks": metrics.get("total_chunks"), "documents_registered": metrics.get("documents_registered"),
            "file_errors": metrics.get("file_errors") or [], "wall_s": wall, "identity": ident}


def gate_verdict(res: dict, n_files: int) -> tuple[bool, list[str]]:
    """The gate's test of a rebuilt exp_v4_s20_n0 (module docstring, THE GATE)."""
    bad = []
    ident = res.get("identity") or {}
    if res.get("status") != "READY":
        bad.append(f"status {res.get('status')!r}, not READY")
    if res.get("file_errors"):
        bad.append(f"{len(res['file_errors'])} file errors")
    if res.get("documents_registered") != n_files:
        bad.append(f"{res.get('documents_registered')} of {n_files} documents registered")
    if ident.get("n_chunks") != GATE_CHUNKS or res.get("total_chunks") != GATE_CHUNKS:
        bad.append(f"{ident.get('n_chunks')} chunks in Chroma, {res.get('total_chunks')} by the job; the paper's index "
                   f"has {GATE_CHUNKS}")
    if ident.get("chunk_manifest_sha256") != GATE_MANIFEST:
        bad.append(f"chunk_manifest_sha256 {ident.get('chunk_manifest_sha256')}, the paper's is {GATE_MANIFEST}")
    return not bad, bad


def write_json(path: Path, obj: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def require_gate(record: Path) -> dict:
    """The gate record, passed and made with this code (code_identity); refused otherwise."""
    if not Path(record).exists():
        raise Refused(f"no gate record at {record}: run `gate` first (README.md:75-79)")
    g = json.loads(Path(record).read_text())
    if g.get("passed") is not True:
        raise Refused(f"the gate at {record} did not pass: {g.get('problems')}")
    now = code_identity()
    if g.get("code") != now:
        diff = sorted(k for k in set(now) | set(g.get("code") or {}) if (g.get("code") or {}).get(k) != now.get(k))
        raise Refused(f"the gate at {record} was made with other code ({diff}); run `gate` again")
    return g


def provenance(cmd: str) -> dict:
    return {"script": "experiments/reuse_demo/build_index.py " + cmd, "argv": sys.argv[1:],
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "host": os.uname().nodename,
            "lock_sha256": sha256_file(ROOT / "experiments" / "LOCK.toml")}


def cmd_plan(a) -> int:
    files = corpus_files(a.corpus, a.manifest)
    print(f"corpus {a.corpus}: {len(files)} PDFs")
    for f in file_list(files):
        print(f"  {f['file']}  {f['bytes']:>10,} bytes  sha256 {f['sha256'][:16]}")
    print(f"store {a.store}: " + ("EXISTS (a build would refuse)" if a.store and Path(a.store).expanduser().exists()
                                  else "new" if a.store else "not given"))
    g = Path(a.gate_record)
    print(f"gate record {g}: " + ("missing" if not g.exists() else
                                  f"passed {json.loads(g.read_text()).get('passed')}"))
    r = i2_memory.free_gb()
    print("free memory " + ("unknown" if r is None else f"{r:.2f} GB") + f" (floor {a.min_free_gb} GB)")
    return 0


def cmd_gate(a, ingest_fn=ingest) -> int:
    files = gate_files(a.papers_dir)
    listed = file_list(files)
    free = memory_or_refuse(a.min_free_gb)
    store = fresh_store(a.store)
    desc = (f"V4 experiment index: 20 core + 0 noise = 20 papers. Embedding: {EMBEDDING_MODEL}, "
            f"Chunking: SimpleChunker({CHUNK_SIZE}, {CHUNK_OVERLAP})")         # create_indexes.py's description
    code = code_identity()
    res = ingest_fn(store, GATE_INDEX, files, desc)
    ok, problems = gate_verdict(res, len(files))
    write_json(a.record, {"_provenance": provenance("gate"), "passed": ok, "problems": problems,
                          "want": {"n_chunks": GATE_CHUNKS, "chunk_manifest_sha256": GATE_MANIFEST,
                                   "source": GATE_SOURCE},
                          "got": res, "store": str(store), "files": listed, "code": code,
                          "free_gb_at_start": free})
    print(f"GATE {'PASSED' if ok else 'NOT PASSED'}: {GATE_INDEX} rebuilt in {store}: "
          f"{(res.get('identity') or {}).get('n_chunks')} chunks, manifest "
          f"{str((res.get('identity') or {}).get('chunk_manifest_sha256'))[:12]}; record {a.record}"
          + ("" if ok else f"; {problems}"))
    return 0 if ok else 1


def cmd_build(a, ingest_fn=ingest) -> int:
    files = corpus_files(a.corpus, a.manifest)
    listed = file_list(files)
    gate = require_gate(a.gate_record)
    free = memory_or_refuse(a.min_free_gb)
    record = Path(a.record or I2_RUNS / f"index_{a.index}.json")
    if record.exists():
        raise Refused(f"{record} exists: an index record is never overwritten")
    store = fresh_store(a.store)
    desc = (f"Reuse index: {len(files)} papers ({a.corpus}). Embedding: {EMBEDDING_MODEL}, "
            f"Chunking: SimpleChunker({CHUNK_SIZE}, {CHUNK_OVERLAP})")
    res = ingest_fn(store, a.index, files, desc)
    ok = (res.get("status") == "READY" and not res.get("file_errors")
          and res.get("documents_registered") == len(files) and res.get("identity") is not None
          and res["identity"]["n_chunks"] == res.get("total_chunks"))
    expect = None
    if a.expect_manifest:
        got = (res.get("identity") or {}).get("chunk_manifest_sha256")
        expect = {"chunk_manifest_sha256": a.expect_manifest, "got": got, "equal": got == a.expect_manifest}
        ok = ok and expect["equal"]
    write_json(record, {"_provenance": provenance("build"), "ok": ok, "index": a.index, "store": str(store),
                        "corpus": str(a.corpus), "manifest": a.manifest and str(a.manifest),
                        "manifest_sha256": a.manifest and sha256_file(a.manifest), "files": listed, "result": res,
                        "code": code_identity(), "gate_record": str(a.gate_record),
                        "gate_record_sha256": sha256_file(a.gate_record), "gate_passed_at": gate["_provenance"]["at"],
                        "expected": expect, "free_gb_at_start": free})
    ident = res.get("identity") or {}
    print(f"BUILD {'DONE' if ok else 'FAILED'}: index {a.index} in {store}: {res.get('status')}, "
          f"{ident.get('n_chunks')} chunks from {res.get('documents_registered')} of {len(files)} files, "
          f"{len(res.get('file_errors') or [])} file errors; record {record}")
    return 0 if ok else 1


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Build a search index as the paper did (module docstring).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "gate", "build"):
        p = sub.add_parser(name)
        p.add_argument("--min-free-gb", type=float, default=i2_memory.FLOOR_GB)
        p.add_argument("--gate-record", type=Path, default=GATE_RECORD)
    for name in ("plan", "build"):
        sub.choices[name].add_argument("--corpus", type=Path, required=True, help="a folder of PDFs")
        sub.choices[name].add_argument("--manifest", type=Path, help="corpus_papers.csv: must name the folder's PDFs")
    sub.choices["plan"].add_argument("--store", type=Path)
    g = sub.choices["gate"]
    g.add_argument("--papers-dir", type=Path, required=True, help="the paper's core PDFs (01_ to 20_ at least)")
    g.add_argument("--store", type=Path, required=True, help="a new folder for the scratch store")
    g.add_argument("--record", type=Path, default=GATE_RECORD)
    b = sub.choices["build"]
    b.add_argument("--index", required=True, help="the index name the runs will ask for (e.g. i2_plant5)")
    b.add_argument("--store", type=Path, required=True, help="a new folder for the store")
    b.add_argument("--record", type=Path, help="default findings/recompute/I2_runs/index_<index>.json")
    b.add_argument("--expect-manifest", help="the chunk_manifest_sha256 the build must give (I2: PLANT_MANIFEST, measured "
                   "with the encoder stood in); a build that differs is written as failed")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    a = parse_args(argv)
    return {"plan": cmd_plan, "gate": cmd_gate, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
