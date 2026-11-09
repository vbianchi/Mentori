"""The identity of the index a run retrieves from, so a scorer can turn the run's passage ids back into text (F5).

    from experiments.runner import index_identity as ii
    ii.record(sink, "exp_v4_s20_n0", collection_name)      # at run start: one line of <sink>/index_identity.jsonl
    ident = ii.held(sink)                                    # the scorer: the one identity the run recorded, or None
    chunks = ii.resolve(ident)                               # {chroma id: {"text", "file_name", "chunk_index"}}

WHY (audit of 16 October, F5). exp_01, exp_02, exp_03 and exp_06 store the passages an answer's generator saw as Chroma
ids only (GenerationResult.passages, the RLM's passages_seen, naive RAG's passage ids), and nothing a run wrote named
the index's content: run_identity.json holds run_id, arm, allowed, agent_roles, thinking and tools
(experiment.py IDENTITY), and an index_name names an index that can be rebuilt under the same name with new ids. The ids
are random per build (uuid4), so they resolve only against the very collection the run read.

WHAT IS RECORDED. At run start each experiment script appends one line to <sink>/index_identity.jsonl (FILE): the index
name, the Chroma collection name and id, the store directory, the number of chunks, and two content hashes read from
the store's chroma.sqlite3 (table embedding_metadata, key "chroma:document" for a chunk's text, which is what
collection.get() and a query return; the same read as experiments/rlm_ref/build_context.py read_chunks):
  id_text_sha256         sha256 of the sorted lines "<chroma id>\\t<sha256 of the chunk's UTF-8 text>\\n": the exact
                         id -> text map, which is what a scorer needs
  chunk_manifest_sha256  sha256 of the sorted lines "<file_name>\\t<chunk_index>\\t<sha256 of the text>\\n", the form of
                         B4_rlm_ref_context.json's provenance, so two copies of a store (other ids, same text) compare
A resumed run appends another line; held() refuses a sink whose lines name two different contents. The read is
read-only (sqlite mode=ro), nothing in the store is written. Embeddings are not hashed: the identity is for turning ids
into text, not for repeating a retrieval.

Standard library only: the experiment scripts call record() in Mentori's environment, the scorers resolve() in theirs.
"""

from __future__ import annotations

import collections
import hashlib
import json
import os
import socket
import sqlite3
import time
from pathlib import Path

FILE = "index_identity.jsonl"
SAME = ("index_name", "collection", "n_chunks", "id_text_sha256", "chunk_manifest_sha256")   # what two lines must share
FORMS = {"id_text_sha256": "sha256 of the sorted lines '<chroma id>\\t<sha256(utf-8 text)>\\n'",
         "chunk_manifest_sha256": "sha256 of the sorted lines '<file_name>\\t<chunk_index>\\t<sha256(utf-8 text)>\\n' "
                                  "(experiments/rlm_ref/build_context.py chunk_manifest_sha256)"}


class IndexIdentityError(Exception):
    pass


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def _connect(store: Path, immutable: bool) -> sqlite3.Connection:
    db = Path(store).expanduser() / "chroma.sqlite3"
    if not db.exists():
        raise IndexIdentityError(f"{db} does not exist")
    return sqlite3.connect(f"file:{db}?mode=ro{'&immutable=1' if immutable else ''}", uri=True)


def collections_in(store: Path, immutable: bool = False) -> list[str]:
    con = _connect(store, immutable)
    try:
        return [r[0] for r in con.execute("select name from collections order by name")]
    finally:
        con.close()


def read_chunks(store: Path, collection: str, immutable: bool = False) -> tuple[str, dict]:
    """(collection id, {chroma id: {"text", "file_name", "chunk_index"}}) of every chunk of the collection, read-only.
    A chunk without a text, or with a metadata key twice, is refused."""
    con = _connect(store, immutable)
    try:
        ids = con.execute("select id from collections where name = ?", (collection,)).fetchall()
        if len(ids) != 1:
            raise IndexIdentityError(f"{collection}: {len(ids)} collections of that name in {store}")
        rows = con.execute(
            "select e.id, e.embedding_id, em.key, em.string_value, em.int_value, em.float_value, em.bool_value "
            "from embeddings e join segments s on s.id = e.segment_id join embedding_metadata em on em.id = e.id "
            "where s.collection = ? and s.scope = 'METADATA' and em.key in ('chroma:document', 'file_name', "
            "'chunk_index')", (ids[0][0],)).fetchall()
    finally:
        con.close()
    meta: dict = collections.defaultdict(dict)
    eid_of: dict = {}
    for rid, eid, key, sv, iv, fv, bv in rows:
        if key in meta[rid]:
            raise IndexIdentityError(f"{collection}: chunk {eid} has metadata key {key!r} twice")
        meta[rid][key] = next((v for v in (sv, iv, fv, bv) if v is not None), None)
        eid_of[rid] = eid
    out = {}
    for rid, m in meta.items():
        eid = eid_of[rid]
        if not isinstance(m.get("chroma:document"), str):
            raise IndexIdentityError(f"{collection}: chunk {eid} has no text (chroma:document)")
        if eid in out:
            raise IndexIdentityError(f"{collection}: id {eid} twice")
        out[eid] = {"text": m["chroma:document"], "file_name": m.get("file_name"), "chunk_index": m.get("chunk_index")}
    return ids[0][0], out


def hashes(chunks: dict) -> dict:
    """n_chunks, id_text_sha256 and chunk_manifest_sha256 of {id: {"text", "file_name", "chunk_index"}} (FORMS)."""
    th = {i: _sha(c["text"]) for i, c in chunks.items()}
    ids = "".join(sorted(f"{i}\t{th[i]}\n" for i in chunks))
    manifest = "".join(sorted(f"{c['file_name']}\t{c['chunk_index']}\t{th[i]}\n" for i, c in chunks.items()))
    return {"n_chunks": len(chunks), "id_text_sha256": _sha(ids), "chunk_manifest_sha256": _sha(manifest)}


def identity(store: Path, collection: str, index_name: str, immutable: bool = False) -> dict:
    cid, chunks = read_chunks(store, collection, immutable)
    if not chunks:
        raise IndexIdentityError(f"{collection} in {store} holds no chunk")
    return {"index_name": index_name, "collection": collection, "collection_id": cid,
            "store": str(Path(store).expanduser().resolve()), **hashes(chunks), "forms": FORMS}


def record(sink: Path, index_name: str, collection: str, store: Path | None = None, script: str | None = None) -> dict:
    """Appends this run start's index identity to <sink>/index_identity.jsonl and returns it. store: the Chroma
    directory (default: Mentori's settings.CHROMA_PERSIST_DIRECTORY, read in Mentori's environment)."""
    if store is None:
        store = mentori_store()
    line = {**identity(Path(store), collection, index_name), "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "host": socket.gethostname(), "pid": os.getpid(), "script": script}
    Path(sink).mkdir(parents=True, exist_ok=True)
    with open(Path(sink) / FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return line


def record_index(sink: Path, index_name: str, user_id: str, script: str | None = None) -> dict:
    """record() for a script that holds an index name and not its collection (exp_06: the RLM loads the index by
    name, RLMContext.from_index): the collection is looked up as Mentori looks it up (UserCollection of user_id)."""
    return record(sink, index_name, collection_of(user_id, index_name), script=script)


def mentori_store() -> Path:
    """Mentori's Chroma directory (VectorStore's default, backend/retrieval/vector_store.py:49). Mentori's env only."""
    from backend.config import settings                     # noqa: PLC0415 - Mentori's environment
    return Path(settings.CHROMA_PERSIST_DIRECTORY)


def collection_of(user_id: str, index_name: str) -> str:
    """The Chroma collection of a user's index, as exp_common.setup_retriever reads it. Mentori's env only."""
    from backend.database import engine                    # noqa: PLC0415 - Mentori's environment
    from backend.retrieval.models import UserCollection     # noqa: PLC0415
    from sqlmodel import Session, select                    # noqa: PLC0415
    with Session(engine) as session:
        idx = session.exec(select(UserCollection).where(UserCollection.user_id == user_id)
                           .where(UserCollection.name == index_name)).first()
    if idx is None:
        raise IndexIdentityError(f"index {index_name!r} not found for user {user_id}")
    return idx.vector_db_collection_name


def held(sink: Path) -> dict | None:
    """The index identity a run recorded (its last line), or None when it recorded none. Refused when its lines
    differ on SAME: the run started on two contents, so one id need not mean one text across its answers."""
    path = Path(sink) / FILE
    if not path.exists():
        return None
    lines = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip():
            try:
                lines.append(json.loads(raw))
            except ValueError as e:
                raise IndexIdentityError(f"{path}:{n} is not an index identity ({e})") from None
    if not lines:
        return None
    kinds = {tuple(d.get(k) for k in SAME) for d in lines}
    if len(kinds) != 1:
        raise IndexIdentityError(f"{path} records {len(kinds)} different index contents across the run's starts; "
                                 f"its passage ids cannot be resolved to one text")
    return lines[-1]


def resolve(ident: dict, store: Path | None = None, immutable: bool = False) -> tuple[dict, dict]:
    """({chroma id: chunk}, where) for a recorded identity: the collection of that name in store (default: the store
    the run recorded), else the one collection of the store with the same id_text_sha256. Refused unless the
    collection read now has exactly the recorded id_text_sha256, so every id resolves to the text the run read."""
    store = Path(store or ident["store"]).expanduser()
    names = collections_in(store, immutable)
    tried = []
    for name in ([ident["collection"]] if ident["collection"] in names else []) + \
                [n for n in names if n != ident["collection"]]:
        _, chunks = read_chunks(store, name, immutable)
        h = hashes(chunks)
        if h["id_text_sha256"] == ident["id_text_sha256"]:
            return chunks, {"store": str(store), "collection": name, **h}
        tried.append(f"{name} ({h['n_chunks']} chunks, id_text {h['id_text_sha256'][:12]})")
    raise IndexIdentityError(f"no collection of {store} has the run's id_text_sha256 {ident['id_text_sha256'][:12]} "
                             f"(index {ident['index_name']}, collection {ident['collection']}); read: "
                             f"{', '.join(tried) or 'none'}")
