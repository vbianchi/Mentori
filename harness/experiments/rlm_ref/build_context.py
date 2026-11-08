"""B4 context: the text the authors' RLM reads (D73 Q43), built once into a file the adapter loads.

    uv run --project experiments/rlm_ref --frozen python experiments/rlm_ref/build_context.py \
        [--store ~/projects/Mentori-paper/data/chroma_db] [--collection collection_f4ccdbe5-0aad-4e95-9d19-042d148730bc]

WHAT. The 778 chunks of index exp_v4_s20_n0 (the 20-paper index of Figures 2 to 4), grouped by their file_name
metadata and joined per paper in chunk_index order, with each repeated chunker overlap removed. The result is a list of
20 strings, one per paper in file-name order, which the adapter passes to the package as `context`.

SOURCE. The laptop's copy of the Studio store (byte-identical for every (file, chunk_index, text sha256) triple, checked
by the coordinator on 15 October), read through sqlite3 with mode=ro&immutable=1, so nothing in the store is written,
not even a lock or journal file. Chroma keeps each chunk's text and metadata in embedding_metadata (key
"chroma:document" for the text), which is what Mentori's collection.get() returns. The chunk manifest (one line
"file<TAB>chunk_index<TAB>sha256(text)" per chunk, sorted) is hashed into the provenance, so a run on another copy of
the store can be compared without the text.

EACH CHUNK starts with the indexer's header "Document: <title> | Type: <doc_type>\\n\\n", the same for every chunk of a
paper (checked; the script refuses otherwise). The header is removed from every chunk and written once at the top of
the paper, after a line naming the file: "File: <file_name>\\n" + header + joined body. Without this, the header would
sit 778 times inside running sentences (it is not text of the paper).

OVERLAPS. Mentori's chunker (backend/retrieval/chunking.py:85-115) tokenises the whole paper, takes 512-token windows
that start 462 tokens apart (a 50-token overlap) and trims a window back to its last sentence end (". ", ".\\n", "! ",
"!\\n", "? ", "?\\n") when that end lies in the window's last 20%, then strips whitespace. So a chunk repeats the end of
the one before it: the whole 50-token overlap, a part of it (the window was trimmed by fewer than 50 tokens), or none
(trimmed by more: the text in between is in no chunk, S141 M5). The duplicated text is found as the longest suffix of
chunk i's body that equals a prefix of chunk i+1's body; no token count is assumed. A match is removed only when it has
one of the shapes the chunker can make:
  - whole_next: chunk i+1 lies wholly inside the end of chunk i (a last window shorter than the overlap);
  - sentence_end: the match ends where chunk i was trimmed, i.e. at '.', '!' or '?' followed in chunk i+1 by a space
    or a newline;
  - long: 50 characters or more (an untrimmed window's 50 tokens; a chance repeat of 50 characters across a join
    does not occur).
A shorter match of any other shape (a chance repeat such as the letter 't', or '.' followed by a digit) is kept in the
text and listed under rejected_matches. Removing an overlap joins body_i + body_{i+1}[L:], so the whitespace after the
overlap is the paper's own. A join with no removable overlap is joined with one newline and listed under
joins_without_overlap. The chunker runs once per page (S141 C16 and M5), so most such joins are page ends: chunk i is a
page's last window, which is shorter than a full window and overlaps nothing, and chunk i+1 starts the next page
(03_nfcore_framework.pdf chunk 30 starts with the next page's running head, "NAR Genomics and Bioinformatics , 2024,
Vol. 6, No. 2", then "efficiently.", which continues the last words of chunk 29, "smaller systems more"); no text is
missing there. The others follow a full window trimmed by more than the overlap, where the text between is in no chunk
(S141 M5). joins_without_overlap_after_sentence_end counts the joins whose chunk i ends a sentence; it mixes both kinds
(a page can end on a sentence), and this script, which counts characters and not tokens, does not tell them apart.

OUTPUT. findings/recompute/B4_rlm_ref_context.json: provenance, per-paper counts (chunks, characters removed as headers
and as overlaps, joins of each kind, joins without overlap, every removed overlap shorter than 20 characters, every
rejected match), the context's sha256 (of its canonical JSON: json.dumps(context, ensure_ascii=False,
separators=(",", ":")) in UTF-8) and the context itself. The file's own sha256 goes to the .sha256 file beside it.

REPRODUCE BEFORE WRITING. The script writes nothing unless the store gives the known shape: 778 chunks, 20 papers,
chunk_index 0..n-1 without gaps per paper, one header per paper.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import platform
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "findings" / "recompute" / "B4_rlm_ref_context.json"
STORE = Path.home() / "projects" / "Mentori-paper" / "data" / "chroma_db"
COLLECTION = "collection_f4ccdbe5-0aad-4e95-9d19-042d148730bc"   # exp_v4_s20_n0 on the laptop copy
STUDIO_COLLECTION = "collection_ee5fcaee-b9ad-41ce-8c24-a1d387230382"   # the same index in the Studio store
INDEX = "exp_v4_s20_n0"
N_CHUNKS, N_PAPERS = 778, 20          # D73 Q43; S141_TRUNCATION_AUDIT.md M5
HEADER = re.compile(r"Document: (.*?) \| Type: (.*?)\n\n")
LONG_CHARS = 50
SHORT_LIST = 20                       # removed overlaps shorter than this are listed by text


class ContextError(Exception):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def context_sha256(context: list[str]) -> str:
    return sha256_bytes(json.dumps(context, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def read_chunks(store: Path, collection: str) -> list[dict]:
    """Every chunk of the collection: text and metadata, read-only."""
    db = store / "chroma.sqlite3"
    con = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    try:
        ids = con.execute("select id from collections where name = ?", (collection,)).fetchall()
        if len(ids) != 1:
            raise ContextError(f"{collection}: {len(ids)} collections of that name in {db}")
        rows = con.execute(
            "select e.id, e.embedding_id, em.key, em.string_value, em.int_value, em.float_value, em.bool_value "
            "from embeddings e join segments s on s.id = e.segment_id join embedding_metadata em on em.id = e.id "
            "where s.collection = ? and s.scope = 'METADATA'", (ids[0][0],)).fetchall()
    finally:
        con.close()
    by_id: dict = collections.defaultdict(dict)
    for rid, eid, key, sv, iv, fv, bv in rows:
        value = next((v for v in (sv, iv, fv, bv) if v is not None), None)
        if key in by_id[rid]:
            raise ContextError(f"chunk {eid}: metadata key {key!r} twice")
        by_id[rid][key] = value
        by_id[rid]["_embedding_id"] = eid
    return list(by_id.values())


def overlap_kind(a: str, b: str, n: int) -> str | None:
    """The chunker shape of a suffix/prefix match of n characters between bodies a and b, or None (a chance repeat)."""
    if n == len(b):
        return "whole_next"
    if b[n - 1] in ".!?" and b[n] in " \n":
        return "sentence_end"
    if n >= LONG_CHARS:
        return "long"
    return None


def match(a: str, b: str) -> tuple[int, str | None, list[int]]:
    """(characters to remove, kind, every longer match rejected): the longest suffix of a equal to a prefix of b
    that has a chunker shape."""
    rejected = []
    for n in range(min(len(a), len(b)), 0, -1):
        if a.endswith(b[:n]):
            kind = overlap_kind(a, b, n)
            if kind:
                return n, kind, rejected
            rejected.append(n)
    return 0, None, rejected


def build(chunks: list[dict]) -> tuple[list[str], list[dict], str]:
    if len(chunks) != N_CHUNKS:
        raise ContextError(f"{len(chunks)} chunks, not {N_CHUNKS}")
    by_paper: dict = collections.defaultdict(list)
    for c in chunks:
        if not isinstance(c.get("file_name"), str) or not isinstance(c.get("chunk_index"), int):
            raise ContextError(f"chunk {c.get('_embedding_id')}: no file_name or integer chunk_index")
        if not isinstance(c.get("chroma:document"), str):
            raise ContextError(f"chunk {c.get('_embedding_id')}: no text")
        by_paper[c["file_name"]].append(c)
    if len(by_paper) != N_PAPERS:
        raise ContextError(f"{len(by_paper)} papers, not {N_PAPERS}")
    manifest = sorted(f"{c['file_name']}\t{c['chunk_index']}\t{sha256_bytes(c['chroma:document'].encode('utf-8'))}"
                      for c in chunks)
    context, papers = [], []
    for name in sorted(by_paper):
        cs = sorted(by_paper[name], key=lambda c: c["chunk_index"])
        if [c["chunk_index"] for c in cs] != list(range(len(cs))):
            raise ContextError(f"{name}: chunk_index is not 0..{len(cs) - 1}")
        headers, bodies = set(), []
        for c in cs:
            t = c["chroma:document"]
            m = HEADER.match(t)
            if not m:
                raise ContextError(f"{name} chunk {c['chunk_index']}: no indexer header")
            headers.add(m.group(0))
            bodies.append(t[m.end():])
        if len(headers) != 1:
            raise ContextError(f"{name}: {len(headers)} different headers")
        header = headers.pop()
        text, removed, kinds = bodies[0], 0, collections.Counter()
        without, short, rejected_all, without_after_end = [], [], [], 0
        for i, (a, b) in enumerate(zip(bodies, bodies[1:])):
            n, kind, rejected = match(a, b)
            for r in rejected:
                rejected_all.append({"after_chunk": i, "chars": r, "text": b[:r]})
            if n:
                kinds[kind] += 1
                removed += n
                text += b[n:]
                if n < SHORT_LIST:
                    short.append({"after_chunk": i, "chars": n, "kind": kind, "text": b[:n]})
            else:
                kinds["none"] += 1
                without.append(i)
                if a.rstrip()[-1:] in (".", "!", "?"):
                    without_after_end += 1
                text += "\n" + b
        paper = f"File: {name}\n{header}{text}"
        context.append(paper)
        chunk_chars = sum(len(c["chroma:document"]) for c in cs)
        header_removed = len(header) * (len(cs) - 1)
        added = len(paper) - len(text) - len(header)          # the "File: ...\n" line
        newlines = len(without)
        if len(paper) != chunk_chars - header_removed - removed + added + newlines:
            raise ContextError(f"{name}: the character account does not close")
        papers.append({
            "file_name": name, "header": header, "n_chunks": len(cs), "chunk_chars": chunk_chars,
            "header_chars_removed": header_removed, "overlap_chars_removed": removed,
            "joins": len(cs) - 1, "joins_by_kind": dict(sorted(kinds.items())),
            "joins_without_overlap": without, "joins_without_overlap_after_sentence_end": without_after_end,
            "removed_overlaps_under_20_chars": short,
            "rejected_matches": rejected_all, "text_chars": len(paper),
            "text_sha256": sha256_bytes(paper.encode("utf-8")),
        })
    return context, papers, sha256_bytes(("\n".join(manifest) + "\n").encode("utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--store", type=Path, default=STORE)
    ap.add_argument("--collection", default=COLLECTION)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    given = list(sys.argv[1:] if argv is None else argv)
    store = args.store.expanduser()
    chunks = read_chunks(store, args.collection)
    context, papers, manifest_sha = build(chunks)
    db = store / "chroma.sqlite3"
    total = lambda k: sum(p[k] for p in papers)   # noqa: E731
    kinds = collections.Counter()
    for p in papers:
        kinds.update(p["joins_by_kind"])
    doc = {
        "provenance": {
            "script": "experiments/rlm_ref/build_context.py",
            "script_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "command": "uv run --project experiments/rlm_ref --frozen python experiments/rlm_ref/build_context.py"
                       + "".join(" " + a for a in given),
            "written_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "python": platform.python_version(), "machine": platform.node(),
            "decision": "D73 Q43 (experiments/README.md)",
            "index": INDEX,
            "store": str(store).replace(str(Path.home()), "~"),
            "store_sqlite_sha256": sha256_bytes(db.read_bytes()),
            "collection": args.collection, "studio_collection": STUDIO_COLLECTION,
            "read": "sqlite3 file:chroma.sqlite3?mode=ro&immutable=1, table embedding_metadata (METADATA segment)",
            "chunk_manifest_sha256": manifest_sha,
            "chunk_manifest_form": "sorted lines file_name<TAB>chunk_index<TAB>sha256(utf-8 text), each ending in \\n",
            "paper_form": "File: <file_name>\\n + the indexer header once + the bodies joined in chunk_index order",
            "overlap_rule": "longest suffix of chunk i equal to a prefix of chunk i+1, removed when whole_next, "
                            "sentence_end or long (>= 50 characters); see the script's docstring",
            "join_without_overlap": "one newline",
            "context_sha256_form": "sha256 of json.dumps(context, ensure_ascii=False, separators=(',', ':')) in UTF-8",
        },
        "summary": {
            "papers": len(papers), "chunks": total("n_chunks"), "chunk_chars": total("chunk_chars"),
            "header_chars_removed": total("header_chars_removed"),
            "overlap_chars_removed": total("overlap_chars_removed"), "joins": total("joins"),
            "joins_by_kind": dict(sorted(kinds.items())),
            "joins_without_overlap": sum(len(p["joins_without_overlap"]) for p in papers),
            "joins_without_overlap_after_sentence_end": total("joins_without_overlap_after_sentence_end"),
            "rejected_matches": sum(len(p["rejected_matches"]) for p in papers),
            "context_chars": sum(len(t) for t in context),
        },
        "context_sha256": context_sha256(context),
        "papers": papers,
        "context": context,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(doc, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    tmp = args.out.with_suffix(".json.tmp")
    tmp.write_bytes(raw)
    os.replace(tmp, args.out)
    file_sha = sha256_bytes(raw)
    args.out.with_suffix(".json.sha256").write_text(f"{file_sha}  {args.out.name}\n")
    s = doc["summary"]
    print(f"wrote {args.out.relative_to(ROOT)} ({len(raw):,} bytes), sha256 {file_sha}")
    print(f"context_sha256 {doc['context_sha256']}; {s['papers']} papers, {s['chunks']} chunks, {s['joins']} joins "
          f"{s['joins_by_kind']}; removed {s['overlap_chars_removed']:,} overlap and {s['header_chars_removed']:,} "
          f"header characters; context {s['context_chars']:,} characters; {s['rejected_matches']} rejected matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
