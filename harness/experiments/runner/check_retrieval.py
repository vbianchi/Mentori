"""Checks for the retrieval and passive-strategy fixes (Figures 2 and 3; A4, A5, A6, D25, D37, D40, D51, D69, D70,
Q14, Q16, Q17, Q18, Q21, Q27, Q37). Offline: the encoders, the vector store and the router are stubs; nothing is
downloaded and no model is called. With --models, also loads the two real encoders from the lock's snapshots (local
cache only) and scores three passages.

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_retrieval [--models]

1. query_refinement (D70, Q95): a 2 to 4 word capitalised query is a factual query ("STAR Aligner Output"); "papers by
   ...", "who wrote ...", "author of ...", "written by", "by me" stay author searches; Q95 (D75): five patterns, and
   "find ... reported from STAR", "list ... used by Sarek", "title of the Sarek paper" are content searches.
2. hybrid_search (Q14): metadata_matches on Chroma's operators, an unknown operator refused; RRF with where keeps
   BM25 hits inside the filter only, and the trace has the weights, the BM25 width and the excluded count.
3. retriever (A4, D40, Q16, D70, limits #10/#123): use_reranker False refused; default widths 3k/2k and Q16 widths
   passed through; the -5 cut gone (a passage scored -9 stays); a reranker failure raises; one candidate unscored and
   kept; an author query not reranked and recorded; results without rerank scores raise "reranker unavailable";
   where applied to keyword hits (docs_outside_filter 0); a fused passage outside the filter is dropped and counted
   (Q14); the fused width is recorded without hybrid too; the record (query_type, widths, reranked, passage ids)
   goes to trace and, inside a run context, to <sink>/retrievals.jsonl; the shared reranker (get_reranker) is used.
4. reranker and embeddings (Q20, Q37, D69, A4, D25): built from the lock's [retrieval] rows (hf_repo, revision,
   local_files_only True, device cpu); another model or device refused; a load or predict failure raises (no
   download fallback, no reranking off); a pair or text over the encoder limit raises; get_reranker is one instance.
5. response_cache (Q27, D69): works outside a run; inside a run context, or with MENTORI_RUN_SINK set, get misses and
   set stores nothing.
6. chunk_verifier (A5, records F17, limits #78, D25): verdicts matched by id; a missing id, an unknown label and an
   unparsed reply are UNVERIFIED with their fail_open_reason; duplicates counted; an empty reply is status empty;
   passages whole in the prompt; no options sent; the call's record carries the passage ids; a failed call is status
   error, every passage UNVERIFIED; filter_relevant keeps UNVERIFIED (fail-open, recorded; Q78, D75);
   verifier_status_report counts verified-pass answers by verifier status and lists those not ok (Q78).
7. pipeline (Q16, Q17, Q18, D25, A5): widths 100/50/15 reach the retriever; the verifier rejecting all gives the
   5-passage fallback, recorded; an unparsed reply and a failed verifier call keep every passage, no fallback, the
   status recorded; passages whole and set before generation; no options; a failed generator call is the error and
   the answer is empty.
8. exp1 strategies (D25, A5, A6, Q21, Q38, limits #2/#116): single pass sends whole passages, records ids, tokens
   from the call records, top_k parameter (D51); a failed call leaves the answer empty; multi-hop pairs each search
   with its own count, after 5 searches runs one closing turn with no sixth search (6 calls, 5 retrievals), the
   closing prompt; a closing SEARCH request stores no answer, closing prose is the answer; Q151 (D83): a reply cut by
   the output limit runs no search and is never the answer, the next hop shows the same passages with the cut in its
   search log, the cut hops are counted (length_turns), a cut closing reply is closing_length; the verified pass stores
   widths, verdicts and fallback; _run_rlm stores the RLM metadata and an RLMRunError's, counts citations as
   submitted, and lets a lock refusal through; failed_answer and the exp_01/exp_02 exception paths keep the calls
   made and store None for unknown counts; exp_01/exp_02 let a refusal through; a resume under another plan is
   refused (D51).
9. The inline judges are unreachable (A7): tests/experiments_v4/exp_common.judge_answer and exp1's _judge_answer
   raise, exp1's run_experiment refuses, and no entry point under publication/scripts calls an inline judge.
10. matched_budget (D51, Q79 to Q81 of D75): targets by question and over all, the CLI's scope per question by
    default (Q79); a max_turns_empty answer is a source, call_error, a setup error and a call without prompt_tokens
    are excluded (Q80); choose_top_k, the floor at 10 and floor_bound listed (Q81), plan(), reached(); exp_01 refuses
    matched_budget without a plan, and a plan missing a question.
"""

import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
tmp = Path(tempfile.mkdtemp(prefix="check_retrieval_")).resolve()
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
os.environ.pop("MENTORI_RUN_SINK", None)
sys.path.insert(0, str(MENTORI))
sys.path.insert(0, str(MENTORI / "publication" / "scripts"))

ap = argparse.ArgumentParser()
ap.add_argument("--models", action="store_true", help="also load the real encoders from the local cache")
a = ap.parse_args()

from backend.agents.lock_adapter import LockCallError  # noqa: E402
from backend.retrieval import embeddings as emb  # noqa: E402
from backend.retrieval import reranker as rr  # noqa: E402
from backend.retrieval import response_cache as cache_mod  # noqa: E402
from backend.retrieval.chunk_verifier import ChunkVerifier, UNVERIFIED, FAIL_OPEN_REASONS, verifier_status_report  # noqa: E402,E501
from backend.retrieval.hybrid_search import RRFHybridSearch, metadata_matches  # noqa: E402
from backend.retrieval.pipeline import PipelineConfig, ScientificRAGPipeline, VERIFY_FALLBACK_N  # noqa: E402
from backend.retrieval.query_refinement import QueryType, classify_query  # noqa: E402
from backend.retrieval.retriever import SimpleRetriever  # noqa: E402

import tests.experiments.exp1_rlm_vs_singlepass as exp1  # noqa: E402
from backend.retrieval.rlm.orchestrator import RLMRunError  # noqa: E402
import tests.experiments_v4.exp_common as v4  # noqa: E402

from experiments.runner import matched_budget as mb  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import load  # noqa: E402

lock = load()
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(fn, kind=Exception):
    try:
        fn()
    except kind as e:
        return e
    return None


def ctx(name="t", item="Q1"):
    return rc.RunContext(run_id=f"check__{name}", arm="check", item_id=item, draw=1, thinking=None,
                         base_url="http://127.0.0.1:9", sink=tmp / "runs" / name,
                         allowed={"gemini-3-flash-preview": "generator", "gpt-oss:20b": "generator"})


def lines(path: Path) -> list:
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


# ── 1. query_refinement (D70) ─────────────────────────────────────────────────────────────────────────────────────
for q in ("STAR Aligner Output", "DESeq2 Normalization Method", "Salmon Quasi-Mapping", "Valerio Bianchi"):
    t, m = classify_query(q)
    check(f"D70: {q!r} is not an author search", t != QueryType.METADATA and m.get("query_subtype") != "author_search",
          f"{t}/{m.get('query_subtype')}")
for q in ("papers by Valerio Bianchi", "who wrote the fastp paper", "author of the Sarek paper",
          "find the pipeline written by Ewels", "papers by me"):
    t, m = classify_query(q)
    check(f"D70: {q!r} stays an author search", t == QueryType.METADATA and m["query_subtype"] == "author_search")
for q in ("find the mapping rate reported from STAR", "list variant callers used by Sarek", "title of the Sarek paper"):
    t, m = classify_query(q)
    check(f"Q95 (D75): {q!r} is a content search, not an author search",
          t != QueryType.METADATA and m.get("query_subtype") != "author_search", f"{t}/{m.get('query_subtype')}")
import inspect  # noqa: E402
from backend.retrieval import query_refinement as qr_mod  # noqa: E402
meta_block = inspect.getsource(qr_mod.classify_query).split("metadata_patterns = [")[1].split("    ]")[0]
meta_pats = [x.strip() for x in meta_block.splitlines() if x.strip().startswith("r'")]
check("Q95 (D75): classify_query has five author patterns; Mentori's patterns 2 and 5 are gone",
      len(meta_pats) == 5 and not any("look" in x or "title" in x for x in meta_pats), meta_pats)

# ── 2. hybrid_search (Q14) ────────────────────────────────────────────────────────────────────────────────────────
md = {"file_name": "a.pdf", "page": 3}
check("metadata_matches: equality, $eq, $in, $gte, $and, $or",
      metadata_matches(md, {"file_name": "a.pdf"}) and metadata_matches(md, {"page": {"$gte": 3}})
      and metadata_matches(md, {"file_name": {"$in": ["a.pdf", "b.pdf"]}})
      and metadata_matches(md, {"$and": [{"file_name": "a.pdf"}, {"page": {"$eq": 3}}]})
      and metadata_matches(md, {"$or": [{"file_name": "b.pdf"}, {"page": 3}]})
      and not metadata_matches(md, {"file_name": "b.pdf"}) and not metadata_matches(md, {"page": {"$lt": 3}}))
check("metadata_matches: an unknown operator is refused",
      raises(lambda: metadata_matches(md, {"page": {"$regex": "x"}}), ValueError) is not None)

# "zebra" in 10 b.pdf chunks and in a.pdf's d0 only (a term in half the chunks has a BM25 IDF of 0)
DOCS = [f"chunk {i} " + ("zebra stripes in the savanna" if i % 4 == 1 or i == 0 else "alpha beta gamma methods")
        for i in range(40)]
IDS = [f"d{i}" for i in range(40)]
METAS = [{"file_name": "b.pdf" if i % 2 else "a.pdf", "page": i // 2, "chunk_index": i} for i in range(40)]
h = RRFHybridSearch()
h.index_documents(DOCS, IDS, METAS)
dense = [{"id": IDS[i], "text": DOCS[i], "metadata": METAS[i], "score": 0.9 - i / 100} for i in range(0, 40, 2)][:6]
tr = {}
fused = h.search("zebra", dense, top_k=8, where={"file_name": "a.pdf"}, trace=tr)
check("Q14: BM25 keeps only chunks inside the filter (no b.pdf hit fuses in)",
      all(r["metadata"]["file_name"] == "a.pdf" for r in fused), [r["id"] for r in fused])
check("Q14: the fusion trace has the weights, BM25 width and excluded count",
      tr.get("sparse_top_k") == 20 and tr.get("n_sparse_excluded_by_filter") == 20 and tr.get("n_sparse") == 1
      and "weights" in tr, tr)
fused_nf = h.search("zebra", dense, top_k=8)
check("without a filter BM25 hits from b.pdf fuse in (the case Q14 fixes)",
      any(r["metadata"]["file_name"] == "b.pdf" for r in fused_nf))


# ── 3. retriever (A4, D40, Q16, D70, limits #10/#123) ────────────────────────────────────────────────────────────
class StubEmb:
    def embed_query(self, q):
        return [0.0]


class StubCollection:
    def get(self):
        return {"documents": DOCS, "ids": IDS, "metadatas": METAS}


class StubVS:
    def __init__(self):
        self.calls = []

    def search(self, query_embedding, n_results, collection_name, where=None):
        self.calls.append({"n_results": n_results, "where": where})
        idx = [i for i in range(40) if not where or metadata_matches(METAS[i], where)][:n_results]
        return {"ids": [[IDS[i] for i in idx]], "documents": [[DOCS[i] for i in idx]],
                "distances": [[0.1 + 0.01 * k for k in range(len(idx))]], "metadatas": [[METAS[i] for i in idx]]}

    def count(self, c):
        return 40

    def get_collection(self, c):
        return StubCollection()


class StubRR:
    is_available = True

    def __init__(self, mode="ok"):
        self.mode, self.seen = mode, []

    def rerank(self, query, candidates, top_k=10):
        self.seen.append(len(candidates))
        if self.mode == "raise":
            raise RuntimeError("predict failed")
        if self.mode == "noscore":
            return candidates[:top_k]
        out = [{**c, "rerank_score": -9.0 + k * 0.001} for k, c in enumerate(candidates)]
        return sorted(out, key=lambda r: r["rerank_score"], reverse=True)[:top_k]


def retr(mode="ok", use_reranker=True, rr_=None):
    vs = StubVS()
    r = SimpleRetriever(embedder=StubEmb(), vector_store=vs, reranker=rr_ or StubRR(mode), collection_name="c",
                        use_reranker=use_reranker)
    return r, vs


r, vs = retr(use_reranker=False)
check("D40: a retriever built with use_reranker=False is refused",
      raises(lambda: r.retrieve("alpha methods", top_k=5), ValueError) is not None)
r, vs = retr()
check("D40: retrieve(use_reranker=False) is refused",
      raises(lambda: r.retrieve("alpha methods", top_k=5, use_reranker=False), ValueError) is not None)
trace = []
res = r.retrieve("alpha methods", top_k=5, trace=trace)
check("default widths: dense 3 x top_k, fused 2 x top_k reach the reranker",
      vs.calls[-1]["n_results"] == 15 and r._reranker.seen[-1] == 10, (vs.calls[-1], r._reranker.seen))
check("A4: the -5 cut is gone (every passage scored -9 stays)", len(res) == 5 and all(x["rerank_score"] < -5
                                                                                       for x in res))
rec = trace[-1]
check("record: query_type, widths, reranked, ids", rec["query_type"] == QueryType.FACTUAL and rec["dense_top_k"] == 15
      and rec["hybrid_top_k"] == 10 and rec["reranked"] is True and rec["passages"] == [x["id"] for x in res]
      and rec["sparse_top_k"] == 30 and rec["n_returned"] == 5, {k: rec[k] for k in ("dense_top_k", "hybrid_top_k",
                                                                                       "reranked", "sparse_top_k")})
trace = []
r.retrieve("alpha methods", top_k=15, dense_top_k=100, hybrid_top_k=50, trace=trace)
check("Q16: dense 100 and fused 50 reach the retriever and are recorded",
      vs.calls[-1]["n_results"] == 100 and r._reranker.seen[-1] == 40 and trace[-1]["dense_top_k"] == 100
      and trace[-1]["hybrid_top_k"] == 50, (vs.calls[-1], r._reranker.seen[-1]))
r2, _ = retr("raise")
check("A4: a reranker failure raises", raises(lambda: r2.retrieve("alpha methods", top_k=5), RuntimeError) is not None)
r3, _ = retr("noscore")
e = raises(lambda: r3.retrieve("alpha methods", top_k=5), RuntimeError)
check("limits #10/#123: results without rerank scores raise 'reranker unavailable'",
      e is not None and "reranker unavailable" in str(e), e)
trace = []
one = r.retrieve("alpha methods", top_k=1, where={"chunk_index": 0}, use_hybrid=False, trace=trace)
check("limits #10/#123: a single candidate is kept unfiltered and recorded as not reranked",
      len(one) == 1 and trace[-1]["reranked"] is False and trace[-1]["rerank_skipped"] == "single_candidate",
      trace[-1]["rerank_skipped"])
check("the fused width is recorded without hybrid too (it cuts the dense list)", trace[-1]["hybrid_top_k"] == 2,
      trace[-1]["hybrid_top_k"])
trace = []
au = r.retrieve("papers by Valerio Bianchi", top_k=5, trace=trace)
check("D70: an explicit author query is not reranked, and recorded", trace[-1]["query_type"] == QueryType.METADATA
      and trace[-1]["rerank_skipped"] == "author_query" and trace[-1]["reranked"] is False)
trace = []
cap = r.retrieve("STAR Aligner Output zebra", top_k=5, trace=trace)
check("D70: a short capitalised query reranks", trace[-1]["reranked"] is True
      and trace[-1]["query_type"] == QueryType.FACTUAL)
trace = []
f = r.retrieve("zebra stripes", top_k=5, where={"file_name": "a.pdf"}, trace=trace)
check("Q14: where applies to keyword hits (nothing outside the filter)",
      all(x["metadata"]["file_name"] == "a.pdf" for x in f) and trace[-1]["docs_outside_filter"] == 0
      and trace[-1]["n_sparse_excluded_by_filter"] == 20, trace[-1]["n_sparse_excluded_by_filter"])

class LooseVS(StubVS):
    """A dense search that ignores the filter, as a Chroma that read the filter differently would."""

    def search(self, query_embedding, n_results, collection_name, where=None):
        return super().search(query_embedding, n_results, collection_name, where=None)


r5 = SimpleRetriever(embedder=StubEmb(), vector_store=LooseVS(), reranker=StubRR(), collection_name="c")
trace = []
f5 = r5.retrieve("alpha methods", top_k=5, where={"file_name": "a.pdf"}, trace=trace)
check("Q14: a fused passage outside the filter is dropped and counted, the retrieval goes on",
      f5 and all(x["metadata"]["file_name"] == "a.pdf" for x in f5) and trace[-1]["docs_outside_filter"] > 0
      and len(trace[-1]["outside_filter_ids"]) == trace[-1]["docs_outside_filter"],
      (trace[-1]["docs_outside_filter"], trace[-1]["n_fused"]))
c1 = ctx("retr")
with rc.run(c1):
    r.retrieve("alpha methods", top_k=3)
rl = lines(c1.sink / "retrievals.jsonl")
check("D37/D70: inside a run context the retrieval is a line of retrievals.jsonl with query_type",
      len(rl) == 1 and rl[0]["query_type"] == QueryType.FACTUAL and rl[0]["item_id"] == "Q1"
      and len(rl[0]["passages"]) == 3)
r4 = SimpleRetriever(embedder=StubEmb(), vector_store=StubVS(), collection_name="c")
sentinel = StubRR()
rr._default_reranker = sentinel
check("A4: a retriever with no reranker given uses the process's shared one (get_reranker)",
      r4._get_reranker() is sentinel)
rr._default_reranker = None


# ── 4. reranker and embeddings (Q20, Q37, D69, A4, D25) ───────────────────────────────────────────────────────────
spec_r, spec_e = lock.retrieval()["reranker"], lock.retrieval()["embedding"]


class Tok:
    def __init__(self, n=None):
        self.n = n

    def __call__(self, *t, truncation=True):
        n = self.n if self.n is not None else sum(len(x.split()) for x in t) + 2
        return {"input_ids": [0] * n}


class FakeCE:
    made = []
    fail_load = False

    def __init__(self, name, device=None, revision=None, local_files_only=None):
        if FakeCE.fail_load:
            raise OSError("not in the cache")
        FakeCE.made.append({"name": name, "device": device, "revision": revision, "local_files_only": local_files_only})
        self.tokenizer, self.max_length, self.fail = Tok(), 8192, False

    def predict(self, pairs):
        if self.fail:
            raise RuntimeError("predict failed")
        return [float(len(p[1])) / 100 for p in pairs]


rr.CrossEncoder = FakeCE
x = rr.CrossEncoderReranker()
check("Q37/D69: the reranker loads the lock's snapshot (repo, revision, local files only, cpu)",
      FakeCE.made[-1] == {"name": spec_r["hf_repo"], "device": "cpu", "revision": spec_r["revision"],
                          "local_files_only": True}, FakeCE.made[-1])
check("Q20: another reranker model is refused",
      raises(lambda: rr.CrossEncoderReranker("ncbi/MedCPT-Cross-Encoder"), RuntimeError) is not None)
FakeCE.fail_load = True
check("A4: a load failure raises (reranking is never turned off)",
      raises(lambda: rr.CrossEncoderReranker(), OSError) is not None)
FakeCE.fail_load = False
cands = [{"id": "a", "text": "short"}, {"id": "b", "text": "a much longer passage text"}]
out = x.rerank("q", cands, top_k=2)
check("rerank scores and orders", [o["id"] for o in out] == ["b", "a"] and all("rerank_score" in o for o in out))
x.model.fail = True
check("A4: a predict failure raises", raises(lambda: x.rerank("q", cands), RuntimeError) is not None)
x.model.fail, x.model.tokenizer = False, Tok(9000)
check("D25: a pair over the reranker's limit raises", raises(lambda: x.rerank("q", cands), ValueError) is not None)
rr._default_reranker = None
check("A4: get_reranker returns one instance", rr.get_reranker() is rr.get_reranker())
rr._default_reranker = None


class FakeST:
    made = []
    fail_load = False

    def __init__(self, name, device=None, revision=None, local_files_only=None):
        if FakeST.fail_load:
            raise OSError("not in the cache")
        FakeST.made.append({"name": name, "device": device, "revision": revision, "local_files_only": local_files_only})
        self.tokenizer, self.max_seq_length = Tok(), 8192

    def get_sentence_embedding_dimension(self):
        return 1024

    def encode(self, x, **kw):
        return [0.0]


emb.SentenceTransformer = FakeST
emb._embedding_cache.clear()
e1 = emb.EmbeddingEngine("BAAI/bge-m3")
e1.embed_query("STAR aligner")
check("Q37/D69: the embedder loads the lock's snapshot (repo, revision, local files only, cpu)",
      FakeST.made[-1] == {"name": spec_e["hf_repo"], "device": "cpu", "revision": spec_e["revision"],
                          "local_files_only": True} and e1.device == "cpu", FakeST.made[-1])
emb._embedding_cache.clear()
check("Q20: another embedding model is refused",
      raises(lambda: emb.EmbeddingEngine("all-MiniLM-L6-v2").get_dimension(), RuntimeError) is not None)
emb._embedding_cache.clear()
check("Q37: another device is refused",
      raises(lambda: emb.EmbeddingEngine("BAAI/bge-m3", device="mps").get_dimension(), RuntimeError) is not None)
emb._embedding_cache.clear()
FakeST.fail_load, n_before = True, len(FakeST.made)
check("Q20: a snapshot missing from the cache raises, with no download attempt",
      raises(lambda: emb.EmbeddingEngine("BAAI/bge-m3").get_dimension(), OSError) is not None
      and len(FakeST.made) == n_before)
FakeST.fail_load = False
emb._embedding_cache.clear()
e2 = emb.EmbeddingEngine("BAAI/bge-m3")
e2._ensure_model()
e2.model.tokenizer = Tok(9000)
check("D25/M12: a text over the embedder's limit raises",
      raises(lambda: e2.embed_documents(["x"]), ValueError) is not None
      and raises(lambda: e2.embed_query("x"), ValueError) is not None)
emb._embedding_cache.clear()

# ── 5. response_cache (Q27, D69) ──────────────────────────────────────────────────────────────────────────────────
c = cache_mod.ResponseCache()
c.set("q", "idx", ["idx"], "reply")
check("outside a run the cache works", c.get("q", "idx", ["idx"]) == "reply")
with rc.run(ctx("cache")):
    c.set("q2", "idx", ["idx"], "reply2")
    check("Q27: inside a run context get misses", c.get("q", "idx", ["idx"]) is None)
check("Q27: inside a run context set stores nothing", c.get("q2", "idx", ["idx"]) is None)
os.environ["MENTORI_RUN_SINK"] = str(tmp)
check("Q27: with MENTORI_RUN_SINK set (the tool server) the cache is off", c.get("q", "idx", ["idx"]) is None)
os.environ.pop("MENTORI_RUN_SINK")


# ── stub router (as the adapter: appends a call record, returns the adapter's shapes) ───────────────────────────
class Router:
    def __init__(self, replies=None, fail_at=None, tokens=(100, 20), cut_at=()):
        self.replies, self.fail_at, self.tokens, self.calls = list(replies or []), fail_at, tokens, []
        self.cut_at = set(cut_at)   # call numbers whose reply stops at the output limit (status length, Q151)

    def _done(self):
        return "length" if len(self.calls) in self.cut_at else "stop"

    def _rec(self, kind, model_identifier, payload, kw):
        n = len(self.calls) + 1
        self.calls.append({"kind": kind, "model": model_identifier, "payload": payload, "kw": kw,
                           "passages": rc.passages()})
        status = "error" if self.fail_at == n else "length" if n in self.cut_at else "ok"
        rec = rc.append({"model": model_identifier.split("::")[-1], "role": "generator", "status": status,
                         "stop_reason": None if status == "error" else "MAX_TOKENS" if status == "length" else "STOP",
                         "prompt_tokens": None if status == "error" else self.tokens[0],
                         "output_tokens": None if status == "error" else self.tokens[1], "passages": rc.passages(),
                         "error": "boom" if status == "error" else None})
        if status == "error":
            raise LockCallError(rec)
        return rec, (self.replies.pop(0) if self.replies else "FINAL ANSWER: ok")

    async def generate(self, model_identifier, prompt, **kw):
        rec, text = self._rec("generate", model_identifier, prompt, kw)
        return {"response": text, "thinking": "", "done_reason": self._done(), "lock_record": rec}

    async def chat(self, model_identifier, messages, **kw):
        rec, text = self._rec("chat", model_identifier, messages, kw)
        return {"message": {"role": "assistant", "content": text}, "response": text, "done_reason": self._done(),
                "lock_record": rec}


LONG = "x" * 1500 + " end-of-passage"
CHUNKS = [{"id": f"u{i}", "text": f"passage {i} " + LONG, "metadata": {"file_name": f"f{i % 2}.pdf", "page": i}}
          for i in range(6)]

# ── 6. chunk_verifier (A5, records F17, D25) ──────────────────────────────────────────────────────────────────────
reply = json.dumps([{"id": 2, "label": "IRRELEVANT", "reason": "r2"}, {"id": 1, "label": "relevant", "reason": "r1"},
                    {"id": 4, "label": "MAYBE", "reason": "r4"}, {"id": 4, "label": "RELEVANT", "reason": "dup"},
                    {"id": 9, "label": "RELEVANT"}, {"id": 5, "label": "PARTIAL"}, {"id": 6, "label": "PARTIAL"}])
router = Router([reply])
with rc.run(ctx("verify")):
    v = asyncio.run(ChunkVerifier(router).verify("q?", CHUNKS))
labels = [x.label for x in v.verified]
check("F17: verdicts matched by id, not position (id 2 before id 1 in the reply)", labels[0] == "RELEVANT"
      and labels[1] == "IRRELEVANT", labels)
check("A5/F17: a passage with no verdict is UNVERIFIED, 'missing verdict' (id 3)", labels[2] == UNVERIFIED
      and v.verified[2].fail_open_reason == "missing verdict")
check("A5/F17: an unknown label is UNVERIFIED, 'unknown label' (id 4, first verdict kept)", labels[3] == UNVERIFIED
      and v.verified[3].fail_open_reason == "unknown label" and v.duplicate_ids == [4], v.duplicate_ids)
check("F17: a passage with a verdict has no fail_open_reason; the record carries it",
      v.verified[0].fail_open_reason is None and v.to_record()["verdicts"][2]["fail_open_reason"] == "missing verdict")
check("F17: filter_relevant keeps RELEVANT and UNVERIFIED (fail-open, recorded), drops IRRELEVANT and PARTIAL",
      [c["id"] for c in ChunkVerifier(None).filter_relevant(v)] == ["u0", "u2", "u3"],
      [c["id"] for c in ChunkVerifier(None).filter_relevant(v)])
check("an id naming no passage is listed", v.unmatched_ids == [9], v.unmatched_ids)
check("status ok, counts and per-passage record", v.status == "ok" and v.counts()[UNVERIFIED] == 2
      and v.to_record()["verdicts"][0]["uid"] == "u0" and v.to_record()["verdicts"][0]["label_raw"] == "relevant")
sent = router.calls[0]
check("D25: every passage whole in the verifier prompt", all(c["text"] in sent["payload"] for c in CHUNKS))
check("cuts: the verifier sends no options", sent["kw"] == {}, sent["kw"])
check("D37: the verifier call's record carries the passage ids", sent["passages"] == [c["id"] for c in CHUNKS])
for txt, status in (("", "empty"), ("I cannot decide.", "unparsed")):
    with rc.run(ctx("verify2")):
        v2 = asyncio.run(ChunkVerifier(Router([txt])).verify("q?", CHUNKS))
    check(f"A5: a {status} reply leaves every passage UNVERIFIED, '{FAIL_OPEN_REASONS[status]}'", v2.status == status
          and all(x.label == UNVERIFIED and x.fail_open_reason == FAIL_OPEN_REASONS[status] for x in v2.verified),
          v2.status)
with rc.run(ctx("verify3")):
    v3 = asyncio.run(ChunkVerifier(Router(fail_at=1)).verify("q?", CHUNKS))
check("limits #78: a failed verifier call returns status error with its record, every passage UNVERIFIED",
      v3.status == "error" and v3.error and v3.call_record.get("status") == "error"
      and all(x.label == UNVERIFIED and x.fail_open_reason == "verifier call failed" for x in v3.verified)
      and v3.to_record()["error"] == v3.error, v3.status)
check("Q78 (D75): filter_relevant keeps every passage of a failed verifier call (fail-open as Mentori built it)",
      [c["id"] for c in ChunkVerifier(None).filter_relevant(v3)] == [c["id"] for c in CHUNKS])
vp_recs = [{"answer_key": f"k{i}", "question_id": f"Q{i}", "draw": 1, "config": "verified_pass",
            "generation": {"config": "verified_pass", "verification": vv.to_record()}}
           for i, vv in enumerate((v, v2, v3))]
vp_recs += [{"answer_key": "k9", "question_id": "Q9", "draw": 1, "config": "verified_pass",
             "generation": {"config": "verified_pass", "verification": None, "error": "reranker unavailable"}},
            {"answer_key": "s1", "question_id": "Q1", "draw": 1, "config": "single_pass",
             "generation": {"config": "single_pass"}}]
vsr = verifier_status_report(vp_recs)
check("Q78 (D75): verifier_status_report counts verified-pass answers by status and lists those not ok",
      vsr["n_verified_pass"] == 4 and vsr["status_counts"] == {"error": 1, "ok": 1, "unparsed": 1}
      and [x["answer_key"] for x in vsr["not_ok"]] == ["k1", "k2"] and vsr["no_verification"] == ["k9"], vsr)
# a key stored twice: an attempt whose verifier failed (generator then failed too), then the retry with status ok
retry = [{**vp_recs[2], "answer_key": "k0", "question_id": "Q0", "generation": {**vp_recs[2]["generation"],
                                                                               "error": "generator failed"}},
         vp_recs[0]]
vsr2 = verifier_status_report(retry)
check("Q78 (D75): verifier_status_report counts a key's last line only (an earlier failed attempt is not an answer)",
      vsr2["n_verified_pass"] == 1 and vsr2["status_counts"] == {"ok": 1} and vsr2["not_ok"] == [], vsr2)


from experiments.runner.lock import LockError  # noqa: E402


class RefusingRouter:
    async def generate(self, **kw):
        raise LockError("refused")


with rc.run(ctx("verify4")):
    e = raises(lambda: asyncio.run(ChunkVerifier(RefusingRouter()).verify("q?", CHUNKS)), LockError)
check("Q38: a lock refusal in the verifier is not caught", e is not None)


# ── 7. pipeline (Q16, Q17, Q18, D25, A5) ──────────────────────────────────────────────────────────────────────────
class PRetriever:
    def __init__(self):
        self.kw = None

    def retrieve(self, **kw):
        self.kw = kw
        if kw.get("trace") is not None:
            kw["trace"].append({"dense_top_k": kw["dense_top_k"], "hybrid_top_k": kw["hybrid_top_k"],
                                "top_k": kw["top_k"], "reranked": True})
        return [dict(c) for c in CHUNKS]


none_ok = json.dumps([{"id": i, "label": "IRRELEVANT"} for i in range(1, 7)])
pr = PRetriever()
cfg = PipelineConfig.verified()
cfg.gen_model = "gemini::gemini-3-flash-preview"
router = Router([none_ok, "the answer [f0.pdf:0]"])
with rc.run(ctx("pipe")):
    res = asyncio.run(ScientificRAGPipeline(pr, "c", router, cfg).answer("q?"))
check("Q16: dense 100, fused 50, reranked 15 reach the retriever",
      pr.kw["dense_top_k"] == 100 and pr.kw["hybrid_top_k"] == 50 and pr.kw["top_k"] == 15, pr.kw)
check("Q16: the result records the widths used", res.retrieval["dense_top_k"] == 100
      and res.retrieval["hybrid_top_k"] == 50)
check("Q18: the verifier is gpt-oss:20b", router.calls[0]["model"] == "ollama::gpt-oss:20b")
check("Q17: the verifier rejecting all gives the first 5, recorded",
      res.verify_fallback is True and res.passages == [c["id"] for c in CHUNKS[:VERIFY_FALLBACK_N]])
g = router.calls[1]
check("D25: the generation prompt has every passage whole", all(c["text"] in g["payload"]
                                                               for c in CHUNKS[:VERIFY_FALLBACK_N]))
check("D37: the generation call's record carries the passage ids", g["passages"] == res.passages)
check("cuts: the generator sends no options", g["kw"] == {})
check("the answer and both calls are recorded", res.answer == "the answer [f0.pdf:0]" and len(res.calls) == 2
      and res.verified_chunks[0]["text"] == CHUNKS[0]["text"])
with rc.run(ctx("pipe2")):
    res2 = asyncio.run(ScientificRAGPipeline(PRetriever(), "c", Router([none_ok], fail_at=2), cfg).answer("q?"))
check("A5: a failed generator call is the error, the answer empty", res2.answer == "" and res2.error
      and res2.calls[-1]["status"] == "error")
with rc.run(ctx("pipe3")):
    res3 = asyncio.run(ScientificRAGPipeline(PRetriever(), "c", Router(fail_at=1), cfg).answer("q?"))
check("limits #78/F17: a failed verifier call is recorded, every passage reaches the generator, no fallback",
      res3.answer == "FINAL ANSWER: ok" and res3.error is None and res3.verification["status"] == "error"
      and res3.verify_fallback is False and res3.passages == [c["id"] for c in CHUNKS]
      and [c["status"] for c in res3.calls] == ["error", "ok"], (res3.error, res3.verification["status"]))
with rc.run(ctx("pipe4")):
    res4 = asyncio.run(ScientificRAGPipeline(PRetriever(), "c", Router(["no verdicts here", "ans"]), cfg).answer("q?"))
check("F17: an unparsed verifier reply keeps every passage UNVERIFIED, no fallback (as a failed call)",
      res4.verification["status"] == "unparsed" and res4.verify_fallback is False
      and res4.passages == [c["id"] for c in CHUNKS] and res4.answer == "ans")


# ── 8. exp1 strategies ────────────────────────────────────────────────────────────────────────────────────────────
class ERetriever:
    def __init__(self):
        self.queries = []

    def retrieve(self, query, top_k, collection_name=None, trace=None, **kw):
        self.queries.append((query, top_k))
        out = [{"id": f"{len(self.queries)}-{i}", "text": f"text {i} " + LONG,
                "metadata": {"file_name": "a.pdf", "page": i}} for i in range(min(top_k, 3))]
        if trace is not None:
            trace.append({"query": query, "query_type": "factual", "reranked": True,
                          "passages": [o["id"] for o in out]})
        return out


GEM = "gemini::gemini-3-flash-preview"
er = ERetriever()
router = Router(["Answer [a.pdf:1]"])
c8 = ctx("sp")
with rc.run(c8):
    sp = asyncio.run(exp1._single_pass_rag("Q?", er, "c", router, GEM))
check("D25: single pass sends every passage whole", LONG in router.calls[0]["payload"]
      and router.calls[0]["payload"].count("end-of-passage") == 3)
check("D37: single pass records the passage ids, on the call and the answer",
      router.calls[0]["passages"] == sp.passages == ["1-0", "1-1", "1-2"])
check("A6: tokens from the call records (not word counts)", sp.prompt_tokens == 100 and sp.output_tokens == 20
      and sp.tokens_used == 120 and sp.llm_calls == 1 and sp.calls[0]["seq"] == 1, (sp.tokens_used, sp.llm_calls))
check("no options sent; top_k recorded; retrieval record kept", router.calls[0]["kw"] == {} and sp.top_k == 10
      and sp.retrievals[0]["reranked"] is True and sp.stop_reason == "ok")
with rc.run(ctx("sp2")):
    sp2 = asyncio.run(exp1._single_pass_rag("Q?", ERetriever(), "c", Router(fail_at=1), GEM))
check("A5: a failed single-pass call leaves the answer empty with the error", sp2.answer == "" and sp2.error
      and sp2.stop_reason == "error" and sp2.calls_without_tokens == 1)
with rc.run(ctx("mbk")):
    mbr = asyncio.run(exp1._single_pass_rag("Q?", er, "c", Router(), GEM, top_k=37, config_name="matched_budget",
                                            matched_budget={"top_k": 37}))
check("D51: single pass takes a top_k (the matched-budget arm)", er.queries[-1] == ("Q?", 37)
      and mbr.config == "matched_budget" and mbr.matched_budget == {"top_k": 37})

er = ERetriever()
router = Router([f"SEARCH: query {n}" for n in range(2, 7)] + ["FINAL ANSWER: closed [a.pdf:1]"])
with rc.run(ctx("mh")):
    mh = asyncio.run(exp1._multi_hop_rag("Q?", er, "c", router, GEM))
check("Q21: after 5 searches one closing turn answers (6 calls)", mh.llm_calls == 6 and len(mh.hops) == 6
      and mh.hops[-1]["closing"] and mh.answer == "closed [a.pdf:1]" and mh.stop_reason == "closing_final_answer",
      (mh.llm_calls, mh.stop_reason))
closing_prompt = router.calls[-1]["payload"][1]["content"]
check("Q21: the closing prompt says no more searches and asks for the FINAL ANSWER",
      "no more searches are available" in closing_prompt and "provide your FINAL ANSWER." in closing_prompt
      and "request another SEARCH" not in closing_prompt)
check("Q21 (Q76, D75: MULTI_HOP_CLOSING_SEARCH False): the closing turn runs no sixth search and shows hop 5's passages",
      exp1.MULTI_HOP_CLOSING_SEARCH is False and len(er.queries) == 5 and len(mh.retrievals) == 5
      and mh.retrieved_passages == 15 and mh.hops[-1]["query"] is None and mh.hops[-1]["requested_query"] == "query 6"
      and mh.hops[-1]["passages"] == mh.hops[-2]["passages"] and "(Search #5)" in closing_prompt
      and "Turn 5: Searched 'query 5'" in closing_prompt, (len(er.queries), mh.hops[-1]["requested_query"]))
second = router.calls[1]["payload"][1]["content"]
check("limits #2/#116: the log pairs each search with its own count",
      "Turn 1: Searched 'Q?' — found 3 passages" in second, re.findall(r"Turn 1: .*", second))
check("D25/D37: multi-hop passages whole and ids on each call", LONG in router.calls[0]["payload"][1]["content"]
      and router.calls[2]["passages"] == ["3-0", "3-1", "3-2"] and mh.passages == ["5-0", "5-1", "5-2"]
      and router.calls[5]["passages"] == ["5-0", "5-1", "5-2"])
check("no options or think sent by multi-hop", all(c["kw"] == {} for c in router.calls))
check("tokens over the 6 call records", mh.prompt_tokens == 600 and mh.output_tokens == 120)
with rc.run(ctx("mh2")):
    mh2 = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c",
                                          Router([f"SEARCH: q{n}" for n in range(5)] + ["Not enough yet.\nSEARCH: more"]), GEM))
check("Q21 (Q77, D75): a closing reply that still asks for a search stores no answer, named",
      mh2.stop_reason == "closing_search_request" and mh2.answer == "" and mh2.error is None
      and mh2.hops[-1]["reply"] == "Not enough yet.\nSEARCH: more")
with rc.run(ctx("mh2b")):
    mh2b = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c",
                                           Router([f"SEARCH: q{n}" for n in range(5)] + ["closing prose"]), GEM))
check("Q21 (Q77, D75): closing prose with no marker is the answer, as no_protocol",
      mh2b.stop_reason == "closing_no_protocol" and mh2b.answer == "closing prose")
with rc.run(ctx("mh3")):
    mh3 = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c", Router(["SEARCH: a", "SEARCH: b"], fail_at=2),
                                          GEM))
check("A5: a failed multi-hop call leaves the answer empty with the error", mh3.answer == "" and mh3.error
      and mh3.stop_reason == "error" and mh3.llm_calls == 2)
with rc.run(ctx("mh4")):
    mh4 = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c", Router(["plain prose"]), GEM))
check("no protocol: the reply is the answer, as Mentori did", mh4.answer == "plain prose"
      and mh4.stop_reason == "no_protocol")
research = "Answer text.\nFurther research: replication in other herds is needed."
with rc.run(ctx("mh5")):
    mh5 = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c", Router([research]), GEM))
check("Q77 (D75): 'research:' inside a line is not a search; the whole reply is the answer (no_protocol)",
      mh5.stop_reason == "no_protocol" and mh5.answer == research, (mh5.stop_reason, mh5.answer))
er6 = ERetriever()
with rc.run(ctx("mh6")):
    mh6 = asyncio.run(exp1._multi_hop_rag("Q?", er6, "c", Router(["SEARCH:\nSarek CO2 per sample",
                                                                  "FINAL ANSWER: done"]), GEM))
check("Q77 (D75): SEARCH: at the start of a line with the query on the next line is a search for that query",
      [q for q, _ in er6.queries] == ["Q?", "Sarek CO2 per sample"] and mh6.stop_reason == "final_answer",
      er6.queries)

# Q151 (D83): a multi-hop reply cut by the output limit is handled as the RLM's D80 V4: nothing in it is acted on (no
# search, no answer), the next hop shows the same passages with the cut in its search log, and the hop is counted
LOOP = "Thinking.\nSEARCH: " + " ".join(["interwoven", "interlocked"] * 50)
CUT_LINE = "Your reply was cut off by the output limit, so none of it was used and no search was run from it."
check("Q151: the cut note as written", exp1.MULTI_HOP_CUT_NOTE == CUT_LINE)
check("Q151 control: no cut reply, length_turns 0 and no hop marked", mh.length_turns == 0
      and all(h["length_cut"] is False for h in mh.hops), mh.length_turns)
er7, r7 = ERetriever(), Router(["SEARCH: q2", LOOP, "SEARCH: q3", "FINAL ANSWER: done [a.pdf:1]"], cut_at={2})
with rc.run(ctx("mh7")):
    mh7 = asyncio.run(exp1._multi_hop_rag("Q?", er7, "c", r7, GEM))
p3, p4 = r7.calls[2]["payload"][1]["content"], r7.calls[3]["payload"][1]["content"]
check("Q151: no search runs from a cut reply (searches Q?, q2, q3; the loop is never a query)",
      [q for q, _ in er7.queries] == ["Q?", "q2", "q3"] and len(mh7.retrievals) == 3, er7.queries)
check("Q151: the hop after the cut runs no search and shows the cut hop's passages again, numbered as that search",
      mh7.hops[2]["query"] is None and mh7.hops[2]["requested_query"] is None
      and mh7.hops[2]["passages"] == mh7.hops[1]["passages"] == ["2-0", "2-1", "2-2"]
      and r7.calls[2]["passages"] == ["2-0", "2-1", "2-2"] and "(Search #2)" in p3, mh7.hops[2])
check("Q151: the next hop is told: its search log gives the cut hop's search, then the cut note",
      f"Turn 2: Searched 'q2' \u2014 found 3 passages. {CUT_LINE}" in p3
      and "Turn 1: Searched 'Q?' \u2014 found 3 passages" in p3, re.findall(r"Turn \d: .*", p3))
check("Q151: a hop that ran no search logs none when it asks for one; the next hop searches it as Search #3",
      "Turn 3:" not in p4 and CUT_LINE in p4 and "(Search #3)" in p4 and mh7.hops[3]["query"] == "q3",
      re.findall(r"Turn \d: .*", p4))
check("Q151: the cut hop is counted and marked, its reply kept whole, its call status length",
      mh7.length_turns == 1 and [h["length_cut"] for h in mh7.hops] == [False, True, False, False]
      and mh7.hops[1]["reply"] == LOOP and mh7.hops[1]["call"]["status"] == "length"
      and mh7.stop_reason == "final_answer" and mh7.answer == "done [a.pdf:1]" and mh7.llm_calls == 4,
      (mh7.length_turns, mh7.stop_reason))
check("Q151: length_turns is stored with the answer (asdict) and read back",
      exp1.asdict(mh7)["length_turns"] == 1 and exp1.GenerationResult(**exp1.asdict(mh7)).length_turns == 1)
with rc.run(ctx("mh8")):
    mh8 = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c",
                                          Router(["FINAL ANSWER: half an ans", "FINAL ANSWER: whole"], cut_at={1}), GEM))
check("Q151: a FINAL ANSWER in a cut reply is not the answer (as a cut RLM reply runs no FINAL); the next hop's is",
      mh8.answer == "whole" and mh8.stop_reason == "final_answer" and mh8.length_turns == 1, (mh8.answer,))
with rc.run(ctx("mh9")):
    mh9 = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c", Router(["cut prose", "plain prose"], cut_at={1}),
                                          GEM))
check("Q151: a cut reply with no marker is not taken as the answer (no_protocol) either",
      mh9.answer == "plain prose" and mh9.stop_reason == "no_protocol" and mh9.hops[0]["length_cut"], mh9.answer)
er10, r10 = ERetriever(), Router([f"SEARCH: q{n}" for n in range(2, 6)] + [LOOP, "FINAL ANSWER: closed"], cut_at={5})
with rc.run(ctx("mh10")):
    mh10 = asyncio.run(exp1._multi_hop_rag("Q?", er10, "c", r10, GEM))
p6 = r10.calls[5]["payload"][1]["content"]
check("Q151: a cut at hop 5 (G1's five closing_final_answer cases): the closing turn answers, told of the cut, "
      "with nothing requested", len(er10.queries) == 5 and mh10.hops[-1]["closing"]
      and mh10.hops[-1]["requested_query"] is None and mh10.hops[-1]["passages"] == mh10.hops[-2]["passages"]
      and f"Turn 5: Searched 'q5' \u2014 found 3 passages. {CUT_LINE}" in p6 and "no more searches" in p6
      and mh10.stop_reason == "closing_final_answer" and mh10.answer == "closed" and mh10.length_turns == 1,
      (mh10.stop_reason, mh10.hops[-1]["requested_query"]))
with rc.run(ctx("mh11")):
    mh11 = asyncio.run(exp1._multi_hop_rag("Q?", ERetriever(), "c",
                                           Router([f"SEARCH: q{n}" for n in range(5)] + ["FINAL ANSWER: cut"],
                                                  cut_at={6}), GEM))
check("Q151: a cut closing reply stores no answer, named closing_length (no error: the call returned)",
      mh11.stop_reason == "closing_length" and mh11.answer == "" and mh11.error is None and mh11.length_turns == 1
      and mh11.hops[-1]["length_cut"] and mh11.llm_calls == 6, (mh11.stop_reason, mh11.answer))
er12, r12 = ERetriever(), Router(["SEARCH: a", "SEARCH: b", "FINAL ANSWER: x"], cut_at={1, 2})
with rc.run(ctx("mh12")):
    mh12 = asyncio.run(exp1._multi_hop_rag("Q?", er12, "c", r12, GEM))
p12 = r12.calls[2]["payload"][1]["content"]
check("Q151: two cuts in a row: one search only, both logged, the second without a search, counted twice",
      [q for q, _ in er12.queries] == ["Q?"] and f"Turn 1: Searched 'Q?' \u2014 found 3 passages. {CUT_LINE}" in p12
      and f"Turn 2: {CUT_LINE}" in p12 and "(Search #1)" in p12 and mh12.length_turns == 2
      and mh12.answer == "x", re.findall(r"Turn \d: .*", p12))
with rc.run(ctx("sp_cut")):
    sp_cut = asyncio.run(exp1._single_pass_rag("Q?", ERetriever(), "c", Router(["half"], cut_at={1}), GEM))
check("Q151 leaves single pass as it was: a cut reply is its answer with stop_reason length, no length_turns",
      sp_cut.answer == "half" and sp_cut.stop_reason == "length" and sp_cut.length_turns is None)

exp1_pipeline_retriever = PRetriever()
with rc.run(ctx("vp")):
    vp = asyncio.run(exp1._verified_pass_rag("q?", exp1_pipeline_retriever, "c", Router([none_ok, "ans"]), GEM))
check("verified pass: widths, verdicts, fallback and tokens stored", vp.retrievals[0]["dense_top_k"] == 100
      and vp.verification["counts"]["IRRELEVANT"] == 6 and vp.verify_fallback is True and vp.llm_calls == 2
      and vp.prompt_tokens == 200 and vp.answer == "ans" and vp.stop_reason == "ok")


class FakeResult(str):
    def __new__(cls, s, md):
        o = str.__new__(cls, s)
        o.metadata = md
        return o


FakeRunError = RLMRunError   # Q73 (D75): exp1 stores only a real RLMRunError; anything else raises RLMStop


META = {"stop_reason": "final", "turns": 4, "rejections": 1, "sub_calls_ok": 3, "sub_calls_failed": 0,
        "sub_calls_empty": 1, "n_code_blocks_run": 5, "nudges": [], "passages_seen": ["p1", "p2"], "timer_firings": [], "extra": 1}


class FakeCtx:
    citations = [1, 2, 3]

    @classmethod
    async def from_index(cls, index_name, user_id):
        return cls()


class FakeOrch:
    mode = "ok"

    def __init__(self, **kw):
        pass

    async def run(self, task, context):
        if FakeOrch.mode == "ok":
            return FakeResult("report", META)
        if FakeOrch.mode == "refuse":
            raise FakeOrch.exc
        raise FakeRunError("no answer", {**META, "stop_reason": "max_turns_empty"})


exp1.RLMContext, exp1.RLMOrchestrator = FakeCtx, FakeOrch
with rc.run(ctx("rlm")):
    rl1 = asyncio.run(exp1._run_rlm("q?", Router(), GEM, "u", max_turns=10, config_name="rlm_10"))
check("_run_rlm stores the RLM metadata (the RLM track's interface)",
      rl1.answer == "report" and all(rl1.rlm[k] == META[k] for k in exp1.RLM_FIELDS) and rl1.rlm["metadata"] == META
      and rl1.stop_reason == "final" and rl1.rlm["citations"] == 3)
check("Q74 (D75): RLM retrieved_passages and passages are passages_seen; the citation count stays in rlm",
      rl1.retrieved_passages == 2 and rl1.passages == ["p1", "p2"] and rl1.rlm["citations"] == 3,
      rl1.retrieved_passages)
FakeOrch.mode = "fail"
with rc.run(ctx("rlm2")):
    rl2 = asyncio.run(exp1._run_rlm("q?", Router(), GEM, "u", max_turns=10, config_name="rlm_10"))
check("A5: an RLM run with no answer is the error, with its metadata", rl2.answer == "" and "no answer" in rl2.error
      and rl2.stop_reason == "max_turns_empty")
for refusal in (LockError("model not in the lock"), rc.RunContextError("no context")):
    FakeOrch.mode, FakeOrch.exc = "refuse", refusal
    with rc.run(ctx("rlm3")):
        e = raises(lambda: asyncio.run(exp1._run_rlm("q?", Router(), GEM, "u", max_turns=10, config_name="rlm_10")),
                   type(refusal))
    check(f"Q38: _run_rlm lets a {type(refusal).__name__} through (a setup error, never a stored answer)",
          e is refusal)
FakeOrch.mode, FakeOrch.exc = "refuse", KeyError("a slip in our own code")
with rc.run(ctx("rlm4")):
    e = raises(lambda: asyncio.run(exp1._run_rlm("q?", Router(), GEM, "u", max_turns=10, config_name="rlm_10")),
               exp1.RLMStop)
check("Q73 (D75): any other exception of the RLM run raises RLMStop (nothing stored)",
      e is not None and isinstance(e.__cause__, KeyError) and exp1.RLMStop in exp1.STOPS)
FakeOrch.mode = "ok"


# failed_answer and the entry points' exception paths (A5, D37, Q38)
class FailingRetriever(ERetriever):
    """Hop 1 retrieves; hop 2's retrieval raises (as 'reranker unavailable' would)."""

    def retrieve(self, query, top_k, collection_name=None, trace=None, **kw):
        if self.queries:
            raise RuntimeError("reranker unavailable: 10 results came back without rerank scores")
        return super().retrieve(query, top_k, collection_name, trace, **kw)


with rc.run(ctx("fa")):
    log = exp1._AnswerCalls()
    e = raises(lambda: asyncio.run(exp1._multi_hop_rag("Q?", FailingRetriever(), "c", Router(["SEARCH: more"]), GEM)))
    fa = exp1.failed_answer("multi_hop", GEM, e, log, 1.5)
check("A5/D37: failed_answer keeps the calls made before the raise, unknown counts None",
      fa.answer == "" and "reranker unavailable" in fa.error and fa.llm_calls == 1 and fa.prompt_tokens == 100
      and fa.retrieved_passages is None and fa.tokens_used == 120 and fa.latency_s == 1.5,
      (fa.llm_calls, fa.tokens_used, fa.retrieved_passages))
fa0 = exp1.failed_answer("multi_hop", GEM, RuntimeError("x"), None, None)
check("A5: failed_answer without call records stores None, never 0", fa0.llm_calls is None and fa0.tokens_used is None
      and fa0.retrieved_passages is None and fa0.latency_s is None)

# ── 9. inline judges unreachable (A7) ────────────────────────────────────────────────────────────────────────────
check("A7: tests/experiments_v4/exp_common.judge_answer raises (its 3,000 cut and 0-on-error unreachable)",
      raises(lambda: asyncio.run(v4.judge_answer("q", "e", [], "x" * 5000, router=None)), RuntimeError) is not None)
check("A7: exp1's _judge_answer raises", raises(lambda: asyncio.run(exp1._judge_answer("q", "e", [], "x", None, "m")),
                                                RuntimeError) is not None)
check("A7/A9: exp1 as a script refuses to run", raises(lambda: asyncio.run(exp1.run_experiment(["m"], ["single_pass"])),
                                                       SystemExit) is not None)
callers = []
for p in sorted((MENTORI / "publication" / "scripts").glob("*.py")):
    for n, line in enumerate(p.read_text().splitlines(), 1):
        if re.search(r"\bjudge_answer\s*\(", line) and not line.lstrip().startswith(("def ", "#")):
            callers.append(f"{p.name}:{n}")
entry = {"exp_01_generation.py", "exp_02_scaling_factorial.py"}
check("A7: neither entry point calls an inline judge", not [c for c in callers if c.split(":")[0] in entry], callers)
print(f"     (inline judge calls elsewhere under publication/scripts, all reaching the raising judge: {callers})")

# ── 10. matched_budget (D51) ──────────────────────────────────────────────────────────────────────────────────────
run = tmp / "runs_mb" / "exp_01__rlm_10__s20"
run.mkdir(parents=True)
ans, calls = [], []
spec = {("A", 1): [100, 200], ("A", 2): [400], ("A", 3): [1000], ("B", 1): [50], ("B", 2): [None, 70], ("C", 1): [5],
        ("D", 1): [900, 1100], ("E", 1): [300], ("F", 1): [20]}
# C: a setup error (no stop_reason); D: ran to its turn limit with nothing (max_turns_empty, error stored, count
# complete); E: a failed root call (call_error); F: no error, stop_reason final
stops = {"C": (None, "boom"), "D": ("max_turns_empty", "RLMRunError: no answer"),
         "E": ("call_error", "RLMRunError: call failed"), "F": ("final", None)}
for (qid, d), toks in spec.items():
    uid = f"{qid}{d}"
    stop, err = stops.get(qid, ("final", None))
    ans.append({"answer_key": f"s20|rlm_10|{qid}|d{d}", "question_id": qid, "draw": d, "ctx_uid": uid,
                "generation": {"error": err, "stop_reason": stop}})
    calls += [{"ctx_uid": uid, "prompt_tokens": t} for t in toks]
calls.append({"ctx_uid": "other", "prompt_tokens": 10 ** 6})
(run / "answers.jsonl").write_text("".join(json.dumps(x) + "\n" for x in ans))
(run / "calls.jsonl").write_text("".join(json.dumps(x) + "\n" for x in calls))
src, excl = mb.answer_inputs(run)
check("D51: an answer's input tokens are its calls' prompt_tokens summed",
      [x["input_tokens"] for x in src["A"]] == [300, 400, 1000] and [x["input_tokens"] for x in src["B"]] == [50])
check("Q80 (D75): a max_turns_empty answer is a source with its whole count (2,000), stop_reason kept",
      [(x["input_tokens"], x["stop_reason"]) for x in src["D"]] == [(2000, "max_turns_empty")] and "F" in src, src.get("D"))
check("Q80 (D75): call_error, a setup error and a call lacking prompt_tokens are excluded, with the reason",
      sorted(x["answer_key"] for x in excl) == ["s20|rlm_10|B|d2", "s20|rlm_10|C|d1", "s20|rlm_10|E|d1"]
      and "call_error" in next(x["reason"] for x in excl if x["question_id"] == "E"), excl)
tq, ta = mb.targets(src, "question"), mb.targets(src, "all")
check("D51: targets, median by question and over all", tq["A"]["target_tokens"] == 400
      and tq["B"]["target_tokens"] == 50 and ta["A"]["target_tokens"] == ta["B"]["target_tokens"] == 350,
      (tq["A"]["target_tokens"], ta["A"]["target_tokens"]))
check("Q80: the target's sources carry their stop_reason", tq["D"]["sources"][0]["stop_reason"] == "max_turns_empty")
mb_cli = __import__("argparse")
_saved_parse = mb_cli.ArgumentParser.parse_args
_seen_args = {}


def _capture(self, argv=None, namespace=None):
    ns = _saved_parse(self, argv, namespace)
    _seen_args.update(vars(ns))
    raise SystemExit(0)


mb_cli.ArgumentParser.parse_args = _capture
raises(lambda: mb.main(["plan", "--rlm-run", "x", "--out", str(tmp / "never.json")]), SystemExit)
mb_cli.ArgumentParser.parse_args = _saved_parse
check("Q79 (D75): the plan's scope is per question unless asked otherwise", _seen_args.get("scope") == "question"
      and mb.DEFAULT_SCOPE == "question", _seen_args.get("scope"))
seen = []


def cnt(k):
    seen.append(k)
    return 30 * k


ck = mb.choose_top_k(cnt, 1000, 10, 200)
check("D51: choose_top_k finds the smallest top_k reaching the target, each count once",
      ck["top_k"] == 34 and ck["planned_tokens"] == 1020 and ck["target_reached"] and len(seen) == len(set(seen)), ck)
ck2 = mb.choose_top_k(lambda k: 3 * k, 10 ** 6, 10, 50)
check("D51: a target the collection cannot reach gives the collection size, flagged",
      ck2["top_k"] == 50 and ck2["target_reached"] is False)
doc = mb.plan(run, "question", [{"id": "A", "question": "qa"}, {"id": "B", "question": "qb"},
                                {"id": "Z", "question": "qz"}],
              lambda q, k: [{"id": str(i)} for i in range(k)], lambda q, res: "w " * (len(res) * 10),
              lambda p: len(p.split()), 500, {"index": "s20"})
check("D51: plan() writes top_k, target, sources and probes per question; no target listed",
      doc["questions"]["A"]["top_k"] == 40 and doc["questions"]["B"]["top_k"] == 10 and doc["no_target"] == ["Z"]
      and doc["questions"]["A"]["sources"][0]["answer_key"] == "s20|rlm_10|A|d1" and doc["kind"] ==
      "matched_budget_plan", {k: v["top_k"] for k, v in doc["questions"].items()})
check("Q81 (D75): the floor stays at 10; a question whose 10 passages exceed the target is floor_bound and listed",
      doc["k_min"] == 10 and doc["questions"]["B"]["floor_bound"] is True and doc["questions"]["A"]["floor_bound"] is False
      and doc["floor_bound"] == [{"question_id": "B", "target_tokens": 50, "planned_tokens": 100, "tokens_at_9": 90}]
      and doc["questions"]["B"]["probes"] == {"9": 90, "10": 100}, doc["floor_bound"])
# count(k) = 5.5 k (integer): B's target 50 lies between count(9) = 49 and count(10) = 55, so 10 is the smallest top_k
# with no floor at all; the floor did not bind
doc2 = mb.plan(run, "question", [{"id": "B", "question": "qb"}], lambda q, k: [{"id": str(i)} for i in range(k)],
               lambda q, res: "w " * (len(res) * 11), lambda p: len(p.split()) // 2, 500, {"index": "s20"})
check("Q81 (D75): top_k 10 above a target that 9 passages miss is not floor_bound (count(9) kept in probes)",
      doc2["questions"]["B"]["top_k"] == 10 and doc2["questions"]["B"]["planned_tokens"] == 55
      and doc2["questions"]["B"]["probes"] == {"9": 49, "10": 55} and doc2["questions"]["B"]["floor_bound"] is False
      and doc2["floor_bound"] == [], doc2["questions"]["B"])
arm = tmp / "runs_mb" / "exp_01__matched_budget__s20"
arm.mkdir(parents=True)
(arm / "answers.jsonl").write_text(json.dumps({"answer_key": "s20|matched_budget|A|d1", "question_id": "A",
                                               "draw": 1, "ctx_uid": "m1", "generation": {"top_k": 40}}) + "\n")
(arm / "calls.jsonl").write_text(json.dumps({"ctx_uid": "m1", "prompt_tokens": 417}) + "\n")
rd = mb.reached(doc, arm)
check("D51: reached() reads the arm's generation call's prompt_tokens", rd["answers"][0]["reached_tokens"] == 417
      and rd["answers"][0]["target_tokens"] == 400 and rd["answers"][0]["planned_top_k"] == 40)

import exp_01_generation as e01  # noqa: E402
qs = [{"id": "A"}, {"id": "B"}]
check("exp_01: matched_budget without a plan is refused",
      raises(lambda: e01.load_budget_plan(None, ["matched_budget"], qs), SystemExit) is not None)
pp = tmp / "plan.json"
pp.write_text(json.dumps({"kind": "matched_budget_plan", "questions": {"A": {"top_k": 12}}}))
check("exp_01: a plan missing a question of the run is refused",
      raises(lambda: e01.load_budget_plan(pp, ["matched_budget"], qs), SystemExit) is not None)
pp.write_text(json.dumps({"kind": "matched_budget_plan", "questions": {"A": {"top_k": 12}, "B": {"top_k": 30}}}))
lp = e01.load_budget_plan(pp, ["matched_budget"], qs)
check("exp_01: a whole plan loads with its sha256", lp["questions"]["B"]["top_k"] == 30 and len(lp["sha256"]) == 64)
check("exp_01: matched_budget is not a default config", "matched_budget" not in e01.CONFIG_NAMES)
mbs = tmp / "mb_answers.jsonl"
mbs.write_text(json.dumps({"generation": {"matched_budget": {"plan_sha256": "a" * 64}}}) + "\n")
check("D51: a matched-budget run under the same plan resumes",
      raises(lambda: e01.check_plan_matches(mbs, "a" * 64), SystemExit) is None)
e = raises(lambda: e01.check_plan_matches(mbs, "b" * 64), SystemExit)
check("D51: a matched-budget resume under another plan is refused", e is not None and "one plan" in str(e))
check("D51: no stored answers, nothing to compare", raises(lambda: e01.check_plan_matches(tmp / "none.jsonl", "b"),
                                                            SystemExit) is None)

import exp_02_scaling_factorial as e02  # noqa: E402


async def raising_config(**kw):
    """A strategy that makes one call, then raises as the retriever would (reranker unavailable)."""
    await Router().generate(model_identifier=GEM, prompt="p")
    raise RuntimeError("reranker unavailable: 10 results came back without rerank scores")


async def refusing_config(**kw):
    raise LockError("model not in the lock")


q1 = {"id": "Q1", "question": "q?", "answerable": True, "category": "factual_recall"}
for mod, name in ((e01, "exp_01"), (e02, "exp_02")):
    saved = mod._run_config
    mod._run_config = raising_config
    kw = dict(config="single_pass", q=q1, ctx=ctx(f"{name}_fail"), retriever=None, collection_name="c", router=None,
              user_id="u", index_name="exp_v4_s20_n0")
    if mod is e02:
        kw["draw"] = 1
    out = asyncio.run(mod._process_one(**kw))
    g = out if mod is e01 else exp1.GenerationResult(**out["generation"])
    check(f"{name}: a raising strategy stores the calls it made and None for unknown counts (A5, D37)",
          g.answer == "" and "reranker unavailable" in g.error and g.llm_calls == 1 and g.tokens_used == 120
          and g.retrieved_passages is None and g.latency_s is not None, (g.llm_calls, g.tokens_used,
                                                                         g.retrieved_passages))
    mod._run_config = refusing_config
    kw["ctx"] = ctx(f"{name}_refuse")
    check(f"{name}: a lock refusal leaves _process_one (Q38: a setup error, not a stored answer)",
          raises(lambda: asyncio.run(mod._process_one(**kw)), LockError) is not None)
    mod._run_config = saved

# ── models (--models): the real encoders from the lock's snapshots, local cache only ─────────────────────────────
if a.models:
    import importlib
    importlib.reload(rr)
    importlib.reload(emb)
    real = rr.CrossEncoderReranker()
    scored = real.rerank("Which aligner does nf-core/rnaseq use by default?",
                         [{"id": "1", "text": "STAR is the default aligner of nf-core/rnaseq."},
                          {"id": "2", "text": "The weather in Wageningen was mild."},
                          {"id": "3", "text": "Salmon quantifies transcripts."}], top_k=3)
    check("models: the real reranker loads from the lock's snapshot on cpu and scores",
          scored[0]["id"] == "1" and str(real.model.device) == "cpu", [(s["id"], round(s["rerank_score"], 3))
                                                                         for s in scored])
    emb._embedding_cache.clear()
    real_e = emb.EmbeddingEngine("BAAI/bge-m3")
    v = real_e.embed_query("STAR aligner output")
    check("models: the real embedder loads from the lock's snapshot on cpu", real_e.device == "cpu"
          and real_e.get_dimension() == 1024 and len(v) == 1024)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
