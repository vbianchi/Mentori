"""Checks for Q150 (D83): every search records its own time, so the latency compared between strategies can be each
answer's own time (its model calls' wall_s plus its search time), clock time still recorded as now. Offline: the
encoders, the vector store, the reranker and the router are stubs; no model is loaded or called; nothing is written
outside a temporary directory.

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_search_timers

1. Unchanged otherwise: on the same stubs and queries, SimpleRetriever.retrieve and the RLM context's search and
   navigation functions return what the pre-Q150 code (PRE_Q150, read with git show) returns, and write the same
   records apart from the new fields (search_s, load_s, loads).
2. The retriever's timer: search_s spans the whole call (every slow stage inside it, the time after it below the
   tolerance); loads names what the call loaded (the encoder's first load, the keyword index's build, the reranker's
   fetch), each with its time, the query's own embedding not counted as a load; load_s is their sum; a second call
   loads nothing; the empty-result and "reranker unavailable" paths record their time too; a call that raises before
   its record records nothing, as before; inside a run context the retrievals.jsonl line holds the same values.
3. The RLM's log: every entry has search_s; the RLM's keyword and regex searches time their hits and their rerank;
   search_semantic times the retriever's call and copies its load_s; a search the block's clock stops as it returns
   (delivered False) is timed too; an unknown paper logs nothing, as before.
4. exp_01 and exp_03: exp_01's single pass and multi-hop (exp1 strategies) store each retrieval's search_s in the
   answer (generation.retrievals) and in retrievals.jsonl; exp_03's naive_rag writes it to retrievals.jsonl only
   (its answer record holds no retrievals), on a line carrying the answer's item_id and run_draw, by which exp_03's
   docstring sums an answer's search time. The tool server's query_documents (full_orchestrator's search, rag_tools)
   writes a retrievals.jsonl line per call with search_s, the answer's item_id and run_draw, and loads.bm25_index on
   every call (it builds a new retriever each time; the encoder and the reranker are the process's). A rerun:
   exp_03's run loop run twice on one sink, a question failing as a setup error in the first run and stored in the
   second, so its key has two attempts' lines; answer_search_s sums only the stored attempt's (the byte span
   generation.retrievals_bytes) and refuses rlm_10. Not tested
   here: the full_orchestrator answer record, which keeps none of these fields (executor.py _tool_record), and the
   RLM context's log inside the tool server's tools, which no record holds (exp_03's docstring). exp_01's and
   exp_03's docstrings state the latency rule.
5. Mutants, each run through the same predicates as sections 2 to 4, which must reject it: a frozen clock in the
   retriever (the section 2 span check and the section 4 tool-server check), a frozen clock in the RLM context (the
   section 3 keyword-search check), a tool server that reuses one retriever (the section 4 check's
   bm25_index-on-every-call rule), and the sum by item_id and run_draw alone (the section 4 rerun rule).
"""

import asyncio
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
tmp = Path(tempfile.mkdtemp(prefix="check_search_timers_")).resolve()
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
os.environ["BACKEND_INTERNAL_URL"] = "http://127.0.0.1:9"
os.environ.pop("MENTORI_RUN_SINK", None)
sys.path.insert(0, str(MENTORI))
sys.path.insert(0, str(MENTORI / "publication" / "scripts"))

from backend.agents.lock_adapter import LockCallError  # noqa: E402
from backend.retrieval import retriever as retriever_mod  # noqa: E402
from backend.retrieval import reranker as rr  # noqa: E402
from backend.retrieval.hybrid_search import metadata_matches  # noqa: E402
from backend.retrieval.retriever import SimpleRetriever  # noqa: E402
from backend.retrieval.rlm import context as rlm_context  # noqa: E402
from backend.retrieval.rlm.context import RLMContext, DocumentInfo  # noqa: E402

import tests.experiments.exp1_rlm_vs_singlepass as exp1  # noqa: E402

from experiments.runner import run_context as rc  # noqa: E402

results = []
NEW = ("search_s", "load_s", "loads")
TOL = 0.02          # seconds a record may be written after its timer stops (no file: a dict append)
PRE_Q150 = "cf6271a"   # the last commit before Q150: retriever.py and rlm/context.py there have no timer


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(fn, kind=Exception):
    try:
        fn()
    except kind as e:
        return e
    return None


def ctx(name, item="Q1"):
    return rc.RunContext(run_id=f"check__{name}", arm="check", item_id=item, draw=1, thinking=None,
                         base_url="http://127.0.0.1:9", sink=tmp / "runs" / name,
                         allowed={"gemini-3-flash-preview": "generator"})


def lines(path: Path) -> list:
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def drop(rec, keys=NEW):
    return {k: v for k, v in rec.items() if k not in keys}


def pre_module(rel, name):
    """The file at PRE_Q150 as a module; raises with the reason when git cannot give it."""
    src = subprocess.run(["git", "-C", str(ROOT), "show", f"{PRE_Q150}:{rel}"], capture_output=True, text=True,
                         check=True).stdout
    mod = types.ModuleType(name)
    mod.__file__ = f"{PRE_Q150}:{rel}"
    sys.modules[name] = mod   # dataclasses resolves the module of its classes by name
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


# ── stubs ──────────────────────────────────────────────────────────────────────────────────────────────────────────
DOCS = [("alpha methods zebra " if i % 3 else "beta results ") + f"chunk {i}" for i in range(40)]
IDS = [f"d{i}" for i in range(40)]
METAS = [{"file_name": "a.pdf" if i % 2 else "b.pdf", "page": 1 + i // 4, "chunk_index": i} for i in range(40)]


class Emb:
    """An encoder; with load_s it starts unloaded (model None) and _ensure_model sleeps load_s, as the real one loads
    on first use; embed_query calls _ensure_model, as the real one does, then sleeps embed_s."""
    def __init__(self, load_s=None, embed_s=0.0, fail=False):
        self.model = None if load_s is not None else object()
        self.load_s, self.embed_s, self.fail, self.loads = load_s, embed_s, fail, 0

    def _ensure_model(self):
        if self.model is None:
            time.sleep(self.load_s)
            self.model, self.loads = object(), self.loads + 1

    def embed_query(self, q):
        self._ensure_model()
        if self.fail:
            raise RuntimeError("encoder failed")
        time.sleep(self.embed_s)
        return [0.0]


class Coll:
    def __init__(self, get_s=0.0):
        self.get_s = get_s

    def get(self):
        time.sleep(self.get_s)
        return {"documents": DOCS, "ids": IDS, "metadatas": METAS}


class VS:
    def __init__(self, search_s=0.0, get_s=0.0, empty=False):
        self.search_s, self.get_s, self.empty = search_s, get_s, empty

    def search(self, query_embedding, n_results, collection_name, where=None):
        time.sleep(self.search_s)
        idx = [] if self.empty else [i for i in range(40) if not where or metadata_matches(METAS[i], where)][:n_results]
        return {"ids": [[IDS[i] for i in idx]], "documents": [[DOCS[i] for i in idx]],
                "distances": [[0.1 + 0.01 * k for k in range(len(idx))]], "metadatas": [[METAS[i] for i in idx]]}

    def count(self, c):
        return 40

    def get_collection(self, c):
        return Coll(self.get_s)


class RR:
    is_available = True

    def __init__(self, rerank_s=0.0, noscore=False):
        self.rerank_s, self.noscore = rerank_s, noscore

    def rerank(self, query, candidates, top_k=10):
        time.sleep(self.rerank_s)
        if self.noscore:
            return candidates[:top_k]
        out = [{**c, "rerank_score": round(1.0 - k * 0.01, 4)} for k, c in enumerate(reversed(candidates))]
        return out[:top_k]


def mk(cls=SimpleRetriever, emb=None, vs=None, reranker="stub", **kw):
    return cls(embedder=emb or Emb(), vector_store=vs or VS(), reranker=RR() if reranker == "stub" else reranker,
               collection_name="c", **kw)


# ═══ 1. unchanged otherwise: the pre-Q150 retriever ═══════════════════════════════════════════════════════════════
QUERIES = [dict(query="alpha methods", top_k=5), dict(query="alpha methods", top_k=15, dense_top_k=100, hybrid_top_k=50),
           dict(query="papers by Valerio Bianchi", top_k=5), dict(query="STAR Aligner Output zebra", top_k=5),
           dict(query="zebra stripes", top_k=5, where={"file_name": "a.pdf"}),
           dict(query="alpha methods", top_k=1, where={"chunk_index": 0}, use_hybrid=False),
           dict(query="beta results", top_k=4, use_hybrid=False)]
try:
    pre_r = pre_module("experiments/mentori/backend/retrieval/retriever.py", "pre_q150_retriever")
    pre_err = None
except Exception as e:
    pre_r, pre_err = None, f"{type(e).__name__}: {e} {(getattr(e, 'stderr', '') or '').strip()}"
if pre_r is None:
    check(f"1 the pre-Q150 retriever ({PRE_Q150}) is readable", False, pre_err)
else:
    new, old = mk(), mk(pre_r.SimpleRetriever)
    same, diffs = True, []
    for q in QUERIES:
        tn, to = [], []
        rn, ro = new.retrieve(trace=tn, **q), old.retrieve(trace=to, **q)
        if rn != ro or [drop(x) for x in tn] != to or any(k in to[0] for k in NEW):
            same = False
            diffs.append(q["query"])
    check(f"1 Q150: retrieve() returns the pre-Q150 ({PRE_Q150}) passages and record on {len(QUERIES)} queries "
          f"(default and Q16 widths, an author query, a filter, one candidate, no hybrid), apart from {NEW}",
          same, diffs)
    tn, to = [], []
    new_e, old_e = mk(vs=VS(empty=True)), mk(pre_r.SimpleRetriever, vs=VS(empty=True))
    check("1 Q150: an empty dense search returns [] and the pre-Q150 record, apart from the new fields",
          new_e.retrieve("alpha", top_k=3, trace=tn) == old_e.retrieve("alpha", top_k=3, trace=to) == []
          and [drop(x) for x in tn] == to)
    tn, to = [], []
    en = raises(lambda: mk(reranker=RR(noscore=True)).retrieve("alpha methods", top_k=5, trace=tn), RuntimeError)
    eo = raises(lambda: mk(pre_r.SimpleRetriever, reranker=RR(noscore=True)).retrieve("alpha methods", top_k=5,
                                                                                       trace=to), RuntimeError)
    check("1 Q150: 'reranker unavailable' raises as before, with the pre-Q150 record apart from the new fields",
          en is not None and str(en) == str(eo) and [drop(x) for x in tn] == to, (en, eo))

# ═══ 2. the retriever's timer ═════════════════════════════════════════════════════════════════════════════════════
def timed_retrieval():
    """A warmed retriever's call with 0.09 s of sleeps (embed, dense search, rerank): its record and outer time."""
    r = mk(emb=Emb(embed_s=0.03), vs=VS(search_s=0.03), reranker=RR(rerank_s=0.03))
    r.retrieve("warm", top_k=3)   # the keyword index is built here, so the next call loads nothing
    tr = []
    t = time.perf_counter()
    r.retrieve("alpha methods", top_k=5, trace=tr)
    return tr[-1], time.perf_counter() - t


def spans_call(rec, outer):
    """Section 2's rule (also run on section 5's mutant): search_s is a float, at least the 0.09 s of sleeps, at most
    the call's outer time and within TOL of it."""
    return isinstance(rec["search_s"], float) and 0.09 <= rec["search_s"] <= outer and outer - rec["search_s"] < TOL


rec, outer = timed_retrieval()
check("2 Q150: search_s is a float that spans the call: at least the embed, dense search and rerank sleeps (0.09 s), "
      f"at most the call's outer time, within {TOL} s of it", spans_call(rec, outer),
      (rec["search_s"], round(outer, 6)))
check("2 Q150: a call that loads nothing records loads {} and load_s 0.0 (a float)",
      rec["loads"] == {} and rec["load_s"] == 0.0 and isinstance(rec["load_s"], float), (rec["loads"], rec["load_s"]))

saved_cls, saved_default = rr.CrossEncoderReranker, rr._default_reranker


class SlowLoadRR(RR):
    def __init__(self):
        time.sleep(0.06)
        super().__init__()


try:
    rr.CrossEncoderReranker, rr._default_reranker = SlowLoadRR, None
    emb = Emb(load_s=0.05, embed_s=0.2)
    rl = mk(emb=emb, vs=VS(get_s=0.04), reranker=None)
    tr = []
    rl.retrieve("alpha methods", top_k=5, trace=tr)
    first = tr[-1]
    rl.retrieve("alpha methods", top_k=5, trace=tr)
    second = tr[-1]
finally:
    rr.CrossEncoderReranker, rr._default_reranker = saved_cls, saved_default
lo = first["loads"]
check("2 Q150: the first call names what it loaded: the encoder (0.05 s), the keyword index (0.04 s), the reranker "
      "(0.06 s), each at least its time",
      set(lo) == {"embedding_model", "bm25_index", "reranker"} and lo["embedding_model"] >= 0.05
      and lo["bm25_index"] >= 0.04 and lo["reranker"] >= 0.06, lo)
check("2 Q150: the query's own embedding (0.2 s) is not counted as the encoder's load, and the encoder loaded once",
      lo["embedding_model"] < 0.2 and emb.loads == 1, (lo["embedding_model"], emb.loads))
check("2 Q150: load_s is the sum of loads, and search_s holds it and the query's embedding",
      first["load_s"] == round(sum(lo.values()), 6) and first["search_s"] >= first["load_s"] + 0.2,
      (first["load_s"], first["search_s"]))
check("2 Q150: the second call loads nothing (loads {}, load_s 0.0) and still times its embedding",
      second["loads"] == {} and second["load_s"] == 0.0 and second["search_s"] >= 0.2, second["search_s"])

tr = []
mk(emb=Emb(embed_s=0.03), vs=VS(empty=True)).retrieve("alpha", top_k=3, trace=tr)
check("2 Q150: an empty dense search records its time", tr and tr[-1]["search_s"] >= 0.03, tr and tr[-1]["search_s"])
tr = []
raises(lambda: mk(reranker=RR(rerank_s=0.03, noscore=True)).retrieve("alpha methods", top_k=5, trace=tr))
check("2 Q150: a 'reranker unavailable' retrieval records its time before it raises",
      tr and tr[-1]["search_s"] >= 0.03, tr and tr[-1]["search_s"])
tr = []
e = raises(lambda: mk(emb=Emb(fail=True)).retrieve("alpha methods", top_k=5, trace=tr), RuntimeError)
check("2 Q150: a call that raises before its record (a failed embed) records nothing, as before", e is not None
      and tr == [], tr)
c2 = ctx("retr")
tr = []
with rc.run(c2):
    mk(reranker=RR(rerank_s=0.02)).retrieve("alpha methods", top_k=3, trace=tr)
rl2 = lines(c2.sink / "retrievals.jsonl")
check("2 Q150: inside a run context the retrievals.jsonl line holds the record's search_s, load_s and loads",
      len(rl2) == 1 and all(rl2[0][k] == tr[0][k] for k in NEW) and rl2[0]["search_s"] >= 0.02,
      rl2 and {k: rl2[0][k] for k in NEW})

# ═══ 3. the RLM's log ═════════════════════════════════════════════════════════════════════════════════════════════
TEXT = {f"{d}{i}": f"methods alpha {d} {i} " + ("methods " * (5 - i)) for d in "ab" for i in range(5)}


class FakeRetriever:
    def __init__(self, sleep_s=0.0, load_s=None):
        self.sleep_s, self.load_s = sleep_s, load_s

    def retrieve(self, query, collection_name=None, top_k=10, where=None, trace=None):
        time.sleep(self.sleep_s)
        if trace is not None:
            rec = {"query": query, "reranked": True, "rerank_skipped": None}
            if self.load_s is not None:
                rec["load_s"] = self.load_s
            trace.append(rec)
        return [{"id": "a1", "text": TEXT["a1"], "score": 0.9, "rerank_score": 0.8,
                 "metadata": {"file_name": "a.pdf", "chunk_index": 1, "page": 1}},
                {"id": "b0", "text": TEXT["b0"], "score": 0.0, "rerank_score": 0.2,
                 "metadata": {"file_name": "b.pdf", "chunk_index": 0, "page": 1}}]


def make_context(module=rlm_context, retriever=None, reranker=None):
    c = module.RLMContext(index_name="check", user_id="u")
    for d in ("a", "b"):
        doc = f"{d}.pdf"
        c._chunks_by_doc[doc] = [{"id": f"{d}{i}", "text": TEXT[f"{d}{i}"], "chunk_idx": i, "page": 1 + i // 2,
                                  "metadata": {"file_name": doc}} for i in range(5)]
        c._documents[doc] = module.DocumentInfo(name=doc, file_path=doc, total_chunks=5, total_pages=3)
    c.n_chunks_loaded = 10
    c._retriever = retriever or FakeRetriever()
    c._reranker = reranker or RR()
    return c


def drive(c):
    """Every logging function of the context once or more; returns what each returned."""
    out = [c.get_chunk("a.pdf", 1), c.get_chunk("zzz.pdf", 1), c.get_chunks_range("a.pdf", 0, 3),
           c.get_chunks_by_page("b.pdf", 2), c.search_keyword("methods"), c.search_regex(r"alpha \w 3"),
           c.rlm_search_keyword("methods", top_k=3), c.rlm_search_regex("methods", top_k=2),
           c.rlm_search_keyword("", doc_name="a.pdf"), c.rlm_search_regex("zzz-none"), c.search_regex("[bad"),
           c.search_semantic("alpha", top_k=2), c.search_semantic("alpha", doc_name="a.pdf")]
    return [x if isinstance(x, str) else [(r.chunk_id, r.score, r.text) for r in x] for x in out]


try:
    pre_c = pre_module("experiments/mentori/backend/retrieval/rlm/context.py", "pre_q150_rlm_context")
    pre_cerr = None
except Exception as e:
    pre_c, pre_cerr = None, f"{type(e).__name__}: {e} {(getattr(e, 'stderr', '') or '').strip()}"
cn = make_context()
got = drive(cn)
if pre_c is None:
    check(f"3 the pre-Q150 RLM context ({PRE_Q150}) is readable", False, pre_cerr)
else:
    co = make_context(pre_c)
    want = drive(co)
    check(f"3 Q150: the RLM context's functions return the pre-Q150 ({PRE_Q150}) results and log the same entries "
          "(fn, arguments, ids, rerank fields, delivered) apart from search_s, and load_s on search_semantic; the "
          "same passages_seen",
          got == want and [drop(x, ("search_s", "load_s")) for x in cn.retrievals] == co.retrievals
          and not any("search_s" in x for x in co.retrievals) and cn.passages_seen == co.passages_seen,
          json.dumps({"n": [len(cn.retrievals), len(co.retrievals)]}))
check("3 Q150: every RLM log entry (11: 3 navigation reads, 4 keyword and regex searches, 2 RLM reranked ones on "
      "no-match and empty-query, 2 semantic) has a float search_s >= 0; an unknown paper and an invalid pattern log "
      "nothing, as before",
      len(cn.retrievals) == 11 and all(isinstance(x.get("search_s"), float) and x["search_s"] >= 0
                                       for x in cn.retrievals),
      [(x["fn"], x.get("search_s")) for x in cn.retrievals])
check("3 Q150: search_semantic's entries carry load_s (None when the retriever's record has none); no other entry has it",
      [x.get("load_s", "absent") for x in cn.retrievals if x["fn"] == "search_semantic"] == [None, None]
      and all("load_s" not in x for x in cn.retrievals if x["fn"] != "search_semantic"))

def slow_keyword_search():
    """The RLM's search_keyword with 0.04 s of hits and a 0.04 s rerank: the context and its log entry."""
    c = make_context(reranker=RR(rerank_s=0.04))
    real_hits = c._keyword_hits

    def slow_hits(*a, **k):
        time.sleep(0.04)
        return real_hits(*a, **k)

    c._keyword_hits = slow_hits
    c.rlm_search_keyword("methods", top_k=3)
    return c, c.retrievals[-1]


def times_hits_and_rerank(entry):
    """Section 3's rule (also run on section 5's mutant): the entry's search_s holds the hits and the rerank."""
    return isinstance(entry.get("search_s"), float) and entry["search_s"] >= 0.08 and entry["reranked"] is True


cs, ks = slow_keyword_search()
check("3 Q150: the RLM's search_keyword times its hits (0.04 s) and its rerank (0.04 s)", times_hits_and_rerank(ks),
      ks["search_s"])
real_regex = cs._regex_hits


def slow_regex(*a, **k):
    time.sleep(0.04)
    return real_regex(*a, **k)


cs._regex_hits = slow_regex
cs.rlm_search_regex("methods", top_k=3)
check("3 Q150: the RLM's search_regex times its hits (0.04 s) and its rerank (0.04 s)",
      cs.retrievals[-1]["search_s"] >= 0.08, cs.retrievals[-1]["search_s"])
cm = make_context(retriever=FakeRetriever(sleep_s=0.05, load_s=0.012))
t = time.perf_counter()
cm.search_semantic("alpha", top_k=2)
outer = time.perf_counter() - t
s = cm.retrievals[-1]
check(f"3 Q150: search_semantic times the retriever's call (0.05 s), within {TOL} s of its outer time, and copies "
      "the retriever's load_s", 0.05 <= s["search_s"] <= outer and outer - s["search_s"] < TOL
      and s["load_s"] == 0.012, (s["search_s"], round(outer, 6), s.get("load_s")))


@contextlib.contextmanager
def firing_guard():
    yield
    raise RuntimeError("held firing")   # as the executor's guard raises a held BlockTimeLimit when the search returns


cg = make_context(retriever=FakeRetriever(sleep_s=0.03))
cg.retrieval_guard = firing_guard
eg = raises(lambda: cg.search_semantic("alpha"), RuntimeError)
cg.retrieval_guard = None
cg._reranker = RR(rerank_s=0.03)
cg.retrieval_guard = firing_guard
ek = raises(lambda: cg.rlm_search_keyword("methods", top_k=3), RuntimeError)
check("3 Q150: a search the block's clock stops as it returns (delivered False) is timed too: search_semantic and "
      "the RLM's search_keyword", eg is not None and ek is not None
      and [x["delivered"] for x in cg.retrievals] == [False, False]
      and cg.retrievals[0]["search_s"] >= 0.03 and cg.retrievals[1]["search_s"] >= 0.03 and cg.passages_seen == [],
      [(x["fn"], x["delivered"], x["search_s"]) for x in cg.retrievals])

# ═══ 4. exp_01 and exp_03 ═════════════════════════════════════════════════════════════════════════════════════════
GEM = "gemini::gemini-3-flash-preview"


class Router:
    """As check_retrieval's stub: each call appends a call record to the run's calls.jsonl and returns the adapter's
    shapes."""
    def __init__(self, replies=None):
        self.replies, self.calls = list(replies or []), []

    def _rec(self, kind, model_identifier, payload, kw):
        self.calls.append(kind)
        rec = rc.append({"model": model_identifier.split("::")[-1], "role": "generator", "status": "ok",
                         "stop_reason": "STOP", "prompt_tokens": 100, "output_tokens": 20, "wall_s": 0.5,
                         "passages": rc.passages(), "error": None})
        return rec, (self.replies.pop(0) if self.replies else "FINAL ANSWER: ok")

    async def generate(self, model_identifier, prompt, **kw):
        rec, text = self._rec("generate", model_identifier, prompt, kw)
        return {"response": text, "thinking": "", "done_reason": "stop", "lock_record": rec}

    async def chat(self, model_identifier, messages, **kw):
        rec, text = self._rec("chat", model_identifier, messages, kw)
        return {"message": {"role": "assistant", "content": text}, "response": text, "done_reason": "stop",
                "lock_record": rec}


c4 = ctx("sp")
with rc.run(c4):
    sp = asyncio.run(exp1._single_pass_rag("alpha methods?", mk(reranker=RR(rerank_s=0.02)), "c", Router(["Ans"]),
                                           GEM))
l4 = lines(c4.sink / "retrievals.jsonl")
check("4 Q150, exp_01 single pass (and matched budget, the same function): the answer's generation.retrievals and "
      "retrievals.jsonl hold the retrieval's search_s (>= its 0.02 s rerank), the same value",
      len(sp.retrievals) == 1 and sp.retrievals[0]["search_s"] >= 0.02 and len(l4) == 1
      and l4[0]["search_s"] == sp.retrievals[0]["search_s"] and sp.latency_s >= sp.retrievals[0]["search_s"],
      (sp.retrievals and sp.retrievals[0].get("search_s"), l4 and l4[0].get("search_s")))
c5 = ctx("mh")
with rc.run(c5):
    mh = asyncio.run(exp1._multi_hop_rag("alpha methods?", mk(reranker=RR(rerank_s=0.01)), "c",
                                         Router(["SEARCH: zebra stripes", "FINAL ANSWER: done"]), GEM))
l5 = lines(c5.sink / "retrievals.jsonl")
check("4 Q150, exp_01 multi-hop: each hop's retrieval holds its search_s, in the answer and in retrievals.jsonl",
      len(mh.retrievals) == 2 == len(l5) and all(x["search_s"] >= 0.01 for x in mh.retrievals)
      and [x["search_s"] for x in l5] == [x["search_s"] for x in mh.retrievals],
      [x.get("search_s") for x in mh.retrievals])
import exp_03_orchestration_ablation as x3  # noqa: E402
c6 = ctx("naive", item="Q6")
with rc.run(c6):
    nv = asyncio.run(x3._naive_rag("alpha methods?", mk(reranker=RR(rerank_s=0.02)), "c", Router(["Ans"])))
l6 = lines(c6.sink / "retrievals.jsonl")
check("4 Q150, exp_03 naive_rag: its retrieval's line in retrievals.jsonl holds search_s, and load_s with the "
      "keyword index this fresh retriever built on its first call",
      len(l6) == 1 and l6[0]["search_s"] >= 0.02 and set(l6[0]["loads"]) == {"bm25_index"}
      and l6[0]["load_s"] == l6[0]["loads"]["bm25_index"] and nv["answer"] == "Ans",
      l6 and {k: l6[0][k] for k in NEW})
check("4 Q150, exp_03 naive_rag: the answer record holds no retrieval (no trace is passed); the line names the "
      "answer by item_id and run_draw, the join exp_03's docstring sums by",
      "retrievals" not in nv and l6 and l6[0]["item_id"] == "Q6" and l6[0]["run_draw"] == 1,
      (sorted(nv), l6 and (l6[0].get("item_id"), l6[0].get("run_draw"))))

# the tool server's query_documents (full_orchestrator's search): a new SimpleRetriever on every call, the process's
# encoder (one Emb, as EmbeddingEngine is one instance per model in a process) and reranker (reranker.get_reranker)
from backend.mcp.custom import rag_tools  # noqa: E402

TOOL_EMB, TOOL_RR = Emb(), RR(rerank_s=0.02)


class ToolRetriever(SimpleRetriever):
    """What query_documents builds, on the stubs: its own keyword index, the shared encoder and reranker."""
    def __init__(self, embedding_model=None, use_reranker=True, reranker=None):
        super().__init__(embedder=TOOL_EMB, vector_store=VS(get_s=0.02), reranker=reranker,
                         use_reranker=use_reranker, collection_name="c")


def tool_server_lines(name, factory=ToolRetriever):
    """Two query_documents calls inside one answer's run context (item Q7, draw 1): its retrievals.jsonl lines."""
    saved_sr, saved_get = retriever_mod.SimpleRetriever, rr.get_reranker
    c = ctx(name, item="Q7")
    try:
        retriever_mod.SimpleRetriever, rr.get_reranker = factory, (lambda: TOOL_RR)
        with rc.run(c):
            for q in ("alpha methods", "zebra stripes"):
                asyncio.run(rag_tools.query_documents(query=q, max_results=3, task_id="t"))
    finally:
        retriever_mod.SimpleRetriever, rr.get_reranker = saved_sr, saved_get
    return lines(c.sink / "retrievals.jsonl")


def tool_lines_ok(ls):
    """Section 4's tool-server rule (also run on section 5's mutants): one line per call, each with search_s at least
    the 0.02 s rerank and the 0.02 s keyword-index build, loads exactly {bm25_index} with load_s its value, and the
    answer's item_id and run_draw."""
    return (len(ls) == 2 and all(isinstance(x.get("search_s"), float) and x["search_s"] >= 0.04
                                 and set(x.get("loads") or {}) == {"bm25_index"} and x["loads"]["bm25_index"] >= 0.02
                                 and x["load_s"] == x["loads"]["bm25_index"] and x["item_id"] == "Q7"
                                 and x["run_draw"] == 1 for x in ls))


l7 = tool_server_lines("tool")
check("4 Q150, the tool server's query_documents (exp_03 full_orchestrator): each call's retrievals.jsonl line holds "
      "search_s, the answer's item_id and run_draw, and loads.bm25_index on every call, the second included (a new "
      "retriever per call); the encoder and the reranker are not loads", tool_lines_ok(l7),
      [{k: x.get(k) for k in ("search_s", "loads", "item_id", "run_draw")} for x in l7])
src01 = (MENTORI / "publication" / "scripts" / "exp_01_generation.py").read_text()
check("4 Q150: exp_01's docstring states the latency rule (clock time kept, own time = calls' wall_s + search_s)",
      "Latency (Q150, D83)" in src01 and "generation.calls[].wall_s" in src01 and "search_s" in src01)
src03 = (MENTORI / "publication" / "scripts" / "exp_03_orchestration_ablation.py").read_text()
check("4 Q150: exp_03's docstring states where an answer's search time is read (retrievals.jsonl inside the "
      "answer's own attempt, by item_id and run_draw; the RLM's log for rlm_10) and what no record holds",
      "Latency (Q150, D83" in src03 and "generation.retrievals_bytes" in src03 and "run_draw the" in src03
      and "answer_search_s" in src03 and "generation.rlm.metadata.retrievals" in src03 and "Not recorded" in src03)

# A rerun at the same key in the same sink: exp_03's real run loop (_run_config) over two questions, run twice on one
# sink. Run 1: question A retrieves (a slow 0.08 s rerank) and then fails as a setup error, so its key stays to do;
# question B retrieves and is stored. Run 2 (the resume): A retrieves again (a 0.01 s rerank) and is stored. A's
# lines in retrievals.jsonl: two, one per attempt; its stored answer's search time must be the second line's only.
from experiments.runner import experiment as ex  # noqa: E402

QS = ex.questions()[:2]
RERUN = {"attempt": 0}


async def rerun_dispatch(config, question, retriever, collection_name, router, user_id, index_name, task_id=None):
    qid = rc.current().item_id
    if qid == QS[0]["id"]:
        RERUN["attempt"] += 1
        mk(reranker=RR(rerank_s=0.08 if RERUN["attempt"] == 1 else 0.01)).retrieve(query="alpha methods", top_k=3,
                                                                                       collection_name="c")
        if RERUN["attempt"] == 1:
            raise x3.rr.ToolRefusal("query_documents: [LOCK REFUSAL] the check's setup error")
    else:
        mk(reranker=RR(rerank_s=0.03)).retrieve(query="zebra stripes", top_k=3, collection_name="c")
    return {"answer": "fine"}


class Args3:
    index = x3.DEFAULT_INDEX
    base_url = "http://127.0.0.1:9"


saved_dispatch = x3.dispatch_config
x3.dispatch_config = rerun_dispatch
try:
    rid3 = x3.run_id_for("naive_rag", x3.DEFAULT_INDEX)
    sink3 = ex.sink(rid3, root=tmp / "x3runs")
    for _ in (1, 2):
        asyncio.run(x3._run_config("naive_rag", rid3, sink3, QS, (1,), Args3, None, None, None, "u"))
finally:
    x3.dispatch_config = saved_dispatch
ans3 = json.loads((sink3 / x3.ANSWERS_FILE).read_text())
rows3 = {r["question_id"]: r for r in ans3["results"]}
l3 = lines(sink3 / "retrievals.jsonl")
a_lines = [x for x in l3 if x["item_id"] == QS[0]["id"] and x["run_draw"] == 1]
b_lines = [x for x in l3 if x["item_id"] == QS[1]["id"]]
ra, rb = rows3.get(QS[0]["id"]), rows3.get(QS[1]["id"])


def own_attempt_ok(search_of):
    """Section 4's rerun rule (also run on section 5's mutant): A's stored search time is its second attempt's line
    alone, not the first (setup error) attempt's, nor their sum; B's is its one line."""
    got_a, got_b = search_of(sink3, ra), search_of(sink3, rb)
    return (got_a == a_lines[1]["search_s"] and got_a < a_lines[0]["search_s"]
            and got_b == b_lines[0]["search_s"]), (got_a, got_b)


rerun_ok, rerun_got = own_attempt_ok(x3.answer_search_s)
check("4 Q150 rerun: a key that failed as a setup error and ran again in the same sink has two retrievals.jsonl "
      "lines with its item_id and run_draw; answer_search_s counts only the stored attempt's (between "
      "generation.retrievals_bytes), not the earlier attempt's 0.08 s line nor their sum",
      len(ans3["setup_errors"]) == 1 and ans3["setup_errors"][0]["question_id"] == QS[0]["id"]
      and ra is not None and rb is not None and len(a_lines) == 2 and len(b_lines) == 1
      and a_lines[0]["search_s"] >= 0.08 and rerun_ok
      and ra["generation"]["retrievals_bytes"][0] >= rb["generation"]["retrievals_bytes"][1],
      (rerun_got, [x["search_s"] for x in a_lines], ra and ra["generation"].get("retrievals_bytes")))
check("4 Q150 rerun: answer_search_s refuses rlm_10 (its search time is its RLM log's)",
      isinstance(raises(lambda: x3.answer_search_s(sink3, {**ra, "config": "rlm_10"}), ValueError), ValueError))


# ═══ 5. mutants ═══════════════════════════════════════════════════════════════════════════════════════════════════
class FrozenTime:
    """time with perf_counter stopped: a timer that never moves."""
    def __getattr__(self, name):
        return getattr(time, name)

    @staticmethod
    def perf_counter():
        return 1000.0


@contextlib.contextmanager
def frozen(module):
    saved = module.time
    module.time = FrozenTime()
    try:
        yield
    finally:
        module.time = saved


with frozen(retriever_mod):
    m_rec, m_outer = timed_retrieval()
check("5 mutant: a frozen clock in the retriever fails section 2's span rule (search_s 0.0)",
      not spans_call(m_rec, m_outer), (m_rec["search_s"], round(m_outer, 6)))
with frozen(rlm_context):
    _, m_entry = slow_keyword_search()
check("5 mutant: a frozen clock in the RLM context fails section 3's keyword-search rule (search_s 0.0)",
      not times_hits_and_rerank(m_entry), m_entry["search_s"])
with frozen(retriever_mod):
    m_l7 = tool_server_lines("tool_frozen")
check("5 mutant: a frozen clock in the retriever fails section 4's tool-server rule",
      len(m_l7) == 2 and not tool_lines_ok(m_l7), [x.get("search_s") for x in m_l7])
reused = []


def one_retriever(**kw):
    """A tool server that builds its retriever once and reuses it: only the first call builds the keyword index."""
    if not reused:
        reused.append(ToolRetriever(**kw))
    return reused[0]


m_l7r = tool_server_lines("tool_reused", one_retriever)
check("5 mutant: a tool server that reuses one retriever fails section 4's bm25_index-on-every-call rule",
      len(m_l7r) == 2 and not tool_lines_ok(m_l7r), [x.get("loads") for x in m_l7r])



def item_draw_sum(sink, result):
    """The rule before the fix: every retrievals.jsonl line with the answer's item_id and run_draw, any attempt."""
    return round(sum(x["search_s"] for x in lines(Path(sink) / "retrievals.jsonl")
                     if x["item_id"] == result["question_id"] and x["run_draw"] == result["draw"]), 6)


m_ok, m_got = own_attempt_ok(item_draw_sum)
check("5 mutant: summing by item_id and run_draw alone (the earlier attempt counted) fails section 4's rerun rule",
      not m_ok, m_got)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
