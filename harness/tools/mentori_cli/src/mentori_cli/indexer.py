"""mentori-cli index: a store from a folder of PDFs, with the paper's own index builder.

The work is experiments/reuse_demo/build_index.py's ingest(): Mentori's run_ingestion_job with the paper's chunking
(512 tokens, 50 overlap) and bge-m3 on the CPU at the lock's revision (experiments/reuse_demo/GUIDE.md, step 3). No
language model is called. The paper's gate (rebuild the paper's 20-paper index and match it before building) is not
run here; experiments/reuse_demo/GUIDE.md step 3 shows how to run it.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from mentori_cli import __version__, paths


def build(corpus: Path, store: Path, index: str) -> dict:
    corpus, store = Path(corpus).expanduser().resolve(), Path(store).expanduser().resolve()
    paths.setup_sys_path()                      # experiments.reuse_demo from the repository
    from mentori_cli import inject
    inject.offline_encoders()                   # only with HF_HUB_OFFLINE set (inject.py)
    from experiments.reuse_demo import build_index as bi
    files = bi.corpus_files(corpus, None)       # every PDF of the folder, sorted by name
    store = bi.fresh_store(store)               # a new folder; an existing one is refused
    desc = (f"mentori-cli index: {len(files)} papers ({corpus}). Embedding: {bi.EMBEDDING_MODEL}, "
            f"Chunking: SimpleChunker({bi.CHUNK_SIZE}, {bi.CHUNK_OVERLAP})")
    t0 = time.time()
    res = bi.ingest(store, index, files, desc)
    ok = (res.get("status") == "READY" and not res.get("file_errors")
          and res.get("documents_registered") == len(files) and res.get("identity") is not None)
    record = {"tool": f"mentori-cli {__version__}", "ok": ok, "index": index, "store": str(store),
              "corpus": str(corpus), "files": bi.file_list(files), "result": res, "wall_s": round(time.time() - t0, 1),
              "lock_sha256": hashlib.sha256(paths.lock_path().read_bytes()).hexdigest(),
              "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "host": os.uname().nodename}
    (store / "index_record.json").write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def fetch_encoders() -> list[str]:
    """Downloads the two encoders the lock names ([retrieval]: bge-m3 and bge-reranker-v2-m3) at the lock's
    revisions into the Hugging Face cache, where the paper's code loads them from (local files only)."""
    import tomllib
    from huggingface_hub import snapshot_download
    rows = tomllib.loads(paths.lock_path().read_text(encoding="utf-8"))["retrieval"]
    out = []
    for role in ("embedding", "reranker"):
        r = rows[role]
        out.append(snapshot_download(repo_id=r["hf_repo"], revision=r["revision"]))
    return out
