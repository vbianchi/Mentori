"""Checks for the RLM fixes (track RLM; D31, D40, D67 A10, D68 Q1-Q14, Q29, D75 Q65-Q74, D78 Q122, Q123, Q125, D80 V4, V5) in experiments/mentori/backend/retrieval/rlm/,
the RLM prompt (backend/agents/prompts.py) and the two RLM drivers (exp_02_scaling_generate_rlm.py, exp_06_depth_sweep.py).

Offline: no model, no index, no database. The sub-calls' lock_adapter.generate and the root turns' router are stubbed
(scripted replies; each stub reads run_context.passages() as the adapter would), and the RLMContext is built in memory
with a fake retriever. Run from the repository root inside the Mentori copy's environment:

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_rlm

What it pins (rlm.md finding, decision):
 1 executor: F1 ast exec with the comment guard; F26 no stale write-back; F2 FINAL/FINAL_VAR set once, the sub-call
   inside FINAL_VAR made once, not set from a comment; D25 whole print output, whole results and whole chunk reprs;
   Q5 the 120 s code-time limit (shortened here) fires on code, never during a sub-call, and is recorded, also when
   the block's code catches it; A5 a failed sub-call raises into the block and is recorded, a LockError ends the
   run even when the code catches it; D89 a Gemini block in a sub-call returns '' into the code, which goes on, and
   counts as failed, as does an empty reply with no finishReason (a STOP empty one as ok, as before); D90 a recitation
   stop and a malformed_function_call or malformed_response reply return the text they held ('' when none) into the
   code, which goes on, and count as failed, listed with what they returned;
   A6 set_passages before every sub-call; F16
   nested JSON and the CITATIONS_USED rule; Q8 [paper.pdf:pN] citations; D25 whole quotes and every uncited claim.
 2 context: Q10 whole-quote cite with whitespace collapsed; Q9 the 120-character Sources preview and whole quotes in
   the record; F15 the whole-quote de-duplication; D25 no page preview, every regex match; Q14 the document filter
   on keyword hits; A6 passages_seen; D40 always rerank with one shared reranker that raises on a failed load.
 3 orchestrator: Q1 pin only on a .pdf name; F19 fence regex; Q4 every block, stop at the final; F3 short answers;
   Q3 the gate counts successful sub-calls only; F11 one copy of a rejected reply; Q7 checks after prose turns;
   Q2/Q13 rescue templates; Q6 no budget warning; F5 no compaction; Q11 the turn-limit note; every stop reason;
   A5 call_error; Q38 LockError ends the run; root turns carry passages []; the metadata keys; RLMResult survives
   json, deepcopy and dataclasses.asdict.
 4 verification (verify=True): [paper.pdf:pN] mapping, whole quotes, a failed verifier call is status error.
 5 prompt: Q12 rule removed, Q13 no text slicing.
 6 drivers: Q29 no whole-answer retry, no text-pattern error check; exp_06 stores the record and stops on setup
   errors; limits #147 merge refuses two different rows for one key; exp_02 resumes every stored answer as done.
 7 round 3 (D75): Q65 a sub-call handed an empty list of passages is not counted by the gate (sub_calls_empty);
   Q66 the refusal names what it counts, the progress line stays Mentori's; Q67 no list slices in the example or
   the rescue messages; Q68 the unpinned turn-6 example summarises for the question under Findings, the pinned one
   stays Mentori's; Q69 rule 2 stays; Q70 the blocks a final answer skipped are named when the run goes on; Q71 a
   prose FINAL(...) is not an answer; Q72 search_semantic's time counts, the clock never raises inside it and each
   firing records retrieval_s; Q73 the drivers store only an answer or an RLMRunError and stop on anything else
   (exp_06, exp1, a slip while exp1 builds the record included; exp_01, exp_02 and exp_03 let it through); Q74 exp1 stores len(passages_seen) as retrieved_passages. Q73 and Q74 check driver files outside
   the RLM area: they fail until those shared changes are applied.
 8 round 4 (D78): Q122 the refusal names the calls handed an empty list as not counted (only when there are any);
   Q123 the prompt documents llm_query(prompt, context_chunks=None); Q125 a search the block's clock stopped as it
   returned is logged with delivered False and its ids stay out of passages_seen, a delivered one is delivered True.
 9 D80: V4 (audit F7) a root reply that stopped at the output limit runs none of its code blocks (1,500 in the
   check), stays whole in the history, is followed by CUT_REPLY_NOTE and is counted in length_turns and
   length_blocks_not_run; V5 (audit F6) the REPL's search_keyword and search_regex (rlm_search_keyword,
   rlm_search_regex) rerank their hits with the context's one reranker (the real CrossEncoderReranker.rerank around a
   stub model), against the string the model passed, keep search_semantic's top_k (10), its candidate width (at most
   FUSED_WIDTH x top_k = 20 candidates, the first in the search's own order, the cap recorded) and its exceptions
   (one hit, no hit, a D70 author query), run the rerank in the retrieval guard (Q72, Q125), and every retrieval
   records reranked and rerank_skipped; search_semantic records the retriever's own reason not to rerank, and a
   reranked search the Q14 filter empties as reranked; the orchestrator tools cross_document_analysis and
   paper_triage, run whole, get the pre-V5 search_keyword results (context.py at the pinned commit 7c34a1b, read
   with git show; unreadable, the checks that need it fail and the rest run). Round 3: an empty or whitespace-only
   query to the REPL's search_keyword or search_regex (the emergency nudge's search_keyword("", doc_name=X)) returns
   every match as before V5, recorded rerank_skipped empty_query; the cap checks use a fixture whose keyword order is
   not document order; the context's own search_regex matches the pre-V5 one; a fused result a Q14 filter empties
   before any rerank is recorded with the retriever's label single_candidate.
10 D83 Q141: add_to_report accepts citations None or a list of Citations only; [None], [None, None], [cite, None], a
   ChunkResult in the list, a bare Citation, a string, '', a tuple and a dict each raise a TypeError naming the bad
   item and save nothing, get_report() unchanged; None, [], a list and the default are saved as before. The G1 case
   ([None, None]) replayed on the fixed code and on the code that ran G1 (11137f9, where it was saved and get_report()
   raised the AttributeError the model saw); in a code block the refusal is the block's output and the next block
   recovers; in the RLM loop the run ends with an answer. content is not checked (stored G1 answers saved a list or a
   dict as content and ended normally): a list and a dict after a text section are saved as before. The O2 residual
   (a non-Citation appended to the saved list after the call) pinned as it stands and as add_to_report's docstring
   states it.
11 D83 Q141 round 2: cite() refuses, just before it keeps a citation, exactly what get_report() cannot list (an
   unhashable doc_name or page, a quote that is not text): each refused type named, nothing cited, get_report()
   working, and on the code that ran G1 rlm_10 (87ad4a0) the same call cited and get_report() then failing; every
   allowed type (int, None, str, float, tuple and bool pages; None, int and tuple doc_names; empty, str-subclass and
   multi-line quotes; an unknown paper) gives the same citation record and the same report as on 87ad4a0; an
   unhashable doc_name with a quote still fails at the document lookup with 87ad4a0's error. add_to_report refuses a
   corpus Citation built in the code with such fields and accepts a well-formed one and an intra-document one. The
   CD_007 call replayed at context level, in a code block (the next block recovers) and in the RLM loop (fixed code:
   final answer; 87ad4a0: "unhashable type: 'Citation'" out of the run). The residuals (a Citation changed after
   cite(), a None appended to get_citations()) pinned as cite()'s docstring states them.
12 D92 Q184 (audit F1): the final check reads each report section as str(content), as get_report() prints it: a list,
   a dict and an empty list saved as the only section, then FINAL_VAR(get_report()), end the run with the report as
   the answer; None and a number are saved, raise add_to_report's TypeError into the block (as the submitted
   add_to_report did) and the next turn ends the run; the list case on the orchestrator before Q184 (09f02b8, git
   show) stops the run with the AttributeError; old and new line agree on every 1- to 3-section sequence where the
   old one returned.
"""

import asyncio
import contextlib
import copy
import io
import dataclasses
import importlib
import inspect
import json
import os
import sys
import tempfile
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
tmp = Path(tempfile.mkdtemp(prefix="check_rlm_")).resolve()
# Mentori's settings read these at import: a scratch database, workspace and vector store, never the copy's own
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
sys.path.insert(0, str(MENTORI))
sys.path.insert(0, str(MENTORI / "publication" / "scripts"))

from backend.agents import lock_adapter as la  # noqa: E402
from backend.agents.prompts import get_rlm_orchestrator_prompt  # noqa: E402
from backend.retrieval.rlm import context as rlm_context  # noqa: E402
from backend.retrieval.rlm import executor as rlm_executor  # noqa: E402
from backend.retrieval.rlm import orchestrator as rlm_orch  # noqa: E402
from backend.retrieval.rlm.context import RLMContext, DocumentInfo, ChunkResult, ReportSection  # noqa: E402
from backend.retrieval.rlm.executor import RLMExecutor, BlockTimeLimit  # noqa: E402
from backend.retrieval.reranker import CrossEncoderReranker as RealCrossEncoderReranker  # noqa: E402
from backend.retrieval.rlm.orchestrator import (RLMOrchestrator, RLMResult, RLMRunError, STOP_REASONS,  # noqa: E402
                                                TURN_LIMIT_NOTE)

from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError  # noqa: E402

GEM = "gemini::gemini-3-flash-preview"
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return e
    return None


def ctx(item="Q1"):
    return rc.RunContext(run_id="check-rlm", arm="rlm_5", item_id=item, draw=1, thinking=None,
                         base_url="http://127.0.0.1:9", sink=tmp / "sink", allowed={"gemini-3-flash-preview":
                                                                                     "generator"},
                         agent_roles={"generator": GEM})


# ── the in-memory index: a.pdf (3 chunks, pages 1-2) and b.pdf (1 chunk) ──
TEXT = {
    "a0": "Sample size was 24 patients.\nThe   methods used fastp for trimming of reads before alignment.",
    "a1": "Results show 12 differentially expressed genes. methods appear twice: methods.",
    "a2": "A third chunk on page two with the word methods in it and a long tail " + "x" * 300,
    "b0": "Another paper about salmon quantification methods.",
}


class FakeRetriever:
    """retrieve() returns a.pdf's a1 and b.pdf's b0 (a BM25-only hit from another paper), with rerank scores, and
    appends its record to trace as SimpleRetriever does."""
    def retrieve(self, query, collection_name=None, top_k=10, where=None, trace=None):
        if trace is not None:
            trace.append({"query": query, "reranked": True, "rerank_skipped": None})
        return [{"id": "a1", "text": TEXT["a1"], "score": 0.9, "rerank_score": 0.8,
                 "metadata": {"file_name": "a.pdf", "chunk_index": 1, "page": 1}},
                {"id": "b0", "text": TEXT["b0"], "score": 0.0, "rerank_score": 0.2,
                 "metadata": {"file_name": "b.pdf", "chunk_index": 0, "page": 1}}]


class FakeCrossEncoder:
    """The model inside a CrossEncoderReranker (D80 V5): predict scores each (query, text) pair with score(query,
    text) and logs the pairs; busy_s spins in predict, as a slow model would."""
    max_length = 10 ** 6

    def __init__(self, score, busy_s=0.0):
        self.score, self.busy_s, self.pairs, self.finished, self.interrupted = score, busy_s, [], 0, 0

    def tokenizer(self, *t, truncation=False):
        return {"input_ids": " ".join(t).split()}

    def predict(self, pairs):
        t = time.monotonic()
        try:
            while time.monotonic() - t < self.busy_s:
                pass
        except BaseException:
            self.interrupted += 1
            raise
        self.finished += 1
        self.pairs.extend(tuple(p) for p in pairs)
        return [self.score(q, x) for q, x in pairs]


def fake_reranker(score=lambda q, x: x.lower().count(q.lower()), busy_s=0.0):
    """The real CrossEncoderReranker (its rerank method) around FakeCrossEncoder. The default score is the query's
    count in the text, which keeps the keyword search's own order on the fixture."""
    r = object.__new__(RealCrossEncoderReranker)
    r.model, r.model_name, r.is_available = FakeCrossEncoder(score, busy_s), "fake", True
    return r


def make_context():
    c = RLMContext(index_name="check", user_id="u")
    chunks = {"a.pdf": [("a0", 0, 1), ("a1", 1, 1), ("a2", 2, 2)], "b.pdf": [("b0", 0, 1)]}
    for doc, rows in chunks.items():
        c._chunks_by_doc[doc] = [{"id": i, "text": TEXT[i], "chunk_idx": k, "page": p, "metadata": {"file_name": doc}}
                                 for i, k, p in rows]
        c._documents[doc] = DocumentInfo(name=doc, file_path=doc, total_chunks=len(rows),
                                         total_pages=max(p for _, _, p in rows),
                                         title="In vitro study" if doc == "a.pdf" else "Using salmon")
    c.n_chunks_loaded = 4
    c._retriever = FakeRetriever()
    c._reranker = fake_reranker()   # D80 V5: search_keyword and search_regex rerank
    return c


# ── stubs: sub-calls (lock_adapter.generate) and root turns (router.chat / router.generate) ──
SUB = []          # each sub-call: (prompt, passages)
SUB_REPLIES = []  # scripted: a str, an exception instance, or a callable(prompt) -> str


def fake_generate(model_identifier, prompt, **kw):
    SUB.append((prompt, rc.passages()))
    r = SUB_REPLIES.pop(0) if SUB_REPLIES else "ok"
    if isinstance(r, BaseException):
        raise r
    if callable(r):
        r = r(prompt)
    if isinstance(r, dict):                         # D89: a whole adapter return, lock_record included
        return r
    return {"response": r, "eval_count": 5, "prompt_eval_count": 7}


la.generate = fake_generate   # rlm/executor.py calls lock_adapter.generate through the module


def call_error(seq=7):
    return la.LockCallError({"seq": seq, "status": "error", "error": "HTTP 503", "model": "gemini-3-flash-preview"})


class FakeRouter:
    def __init__(self, replies, gen_replies=()):
        self.replies, self.gen_replies = list(replies), list(gen_replies)
        self.seen = []        # (messages copy, passages) per root call
        self.gen_seen = []    # (prompt, passages) per router.generate (the verifier)

    async def chat(self, model_identifier, messages, think=None, **kw):
        self.seen.append(([dict(m) for m in messages], rc.passages(), kw))
        r = self.replies.pop(0) if self.replies else "I am thinking."
        if isinstance(r, BaseException):
            raise r
        done = "stop"   # as lock_adapter.chat: "stop" or "length"; a reply given as (text, done_reason) sets it
        if isinstance(r, tuple):
            r, done = r
        return {"message": {"role": "assistant", "content": r}, "response": r, "done_reason": done, "eval_count": 1,
                "prompt_eval_count": 1}

    async def generate(self, model_identifier, prompt, **kw):
        self.gen_seen.append((prompt, rc.passages(), kw))
        r = self.gen_replies.pop(0) if self.gen_replies else "VERDICT: YES\nREASON: fine"
        if isinstance(r, BaseException):
            raise r
        return {"response": r}


def block(code):
    return f"```repl\n{code}\n```"


def run(replies, max_turns=5, task="What sample size did the study use?", verify=False, gen_replies=(),
        context=None):
    """One RLM run on the stubs. Returns (result or exception, router, context)."""
    context = context or make_context()
    router = FakeRouter(replies, gen_replies)
    orch = RLMOrchestrator(router, GEM, max_turns=max_turns, verify=verify)

    async def go():
        with rc.run(ctx()):
            try:
                return await orch.run(task, context)
            except Exception as e:
                return e
    with contextlib.redirect_stdout(io.StringIO()):   # the orchestrator's per-turn prints
        return asyncio.run(go()), router, context


SUMMARY_REPLY = ("SUMMARY:\nThe sample size was 24 [1]. Methods used fastp [1, 2].\nCITATIONS_USED:\n1, 2\n"
                 "\nUnrelated 9 10")
WORK = ('ch = search_keyword("methods", doc_name="a.pdf")\n'
        'r1 = llm_summarize(ch, task="t")\nr2 = llm_summarize(ch, task="t")\nr3 = llm_summarize(ch, task="t")\n'
        'add_to_report("Methods", r1["summary"], r1["citations"])')

# ═════════════════════════════ 1. executor ═════════════════════════════
with rc.run(ctx()):
    c = make_context()
    ex = RLMExecutor(c, None, GEM)

    out, res = ex.execute_code("res = [1, 2]\nfor r in res:\n    print(r)")
    check("1 F1 a block ending inside a for loop runs", ex.last_error is None and out == "1\n2\n", repr(out))
    out, res = ex.execute_code("d = dict(\n    a=1,\n    b=2)\nprint(d['b'])")
    check("1 F1 a block ending in a multi-line call runs", ex.last_error is None and out == "2\n", repr(out))
    out, res = ex.execute_code("dict(\n    a=1)")
    check("1 F1 a multi-line last expression is the result", res == {"a": 1}, repr(res))
    out, res = ex.execute_code("y = 5\ny\n# trailing comment")
    check("1 F1 comment guard: a trailing comment line keeps the result None", res is None and ex.last_error is None)
    out, res = ex.execute_code("y = 5\ny")
    check("1 F1 a last expression is the result", res == 5)

    ex.execute_code("x = 1")
    out, _ = ex.execute_code("x = 2; print(x)")
    out, _ = ex.execute_code("print(x)")
    check("1 F26 a reassigned variable keeps its new value in the next block", out == "2\n", repr(out))
    check("1 F26 get_user_variables reads the live namespace", ex.get_user_variables().get("x") == 2
          and "llm_query" not in ex.get_user_variables())
    ex.execute_code("del x")
    ex.execute_code("print(x)")
    check("1 F26 a deleted variable stays deleted", "NameError" in (ex.last_error or ""))
    check("1 F26 _user_namespace is gone", not hasattr(ex, "_user_namespace"))

    ex.execute_code('FINAL("short answer")')
    check("1 F2 FINAL() is defined and sets the final answer", ex.final_set and ex.final == "short answer"
          and ex.last_error is None)
    ex.execute_code('FINAL("a")\nFINAL("b")')
    check("1 F2 the final answer is set once per block", ex.final == "a")
    ex.execute_code('# FINAL_VAR(get_report())\nprint("no final")')
    check("1 F2 FINAL_VAR in a comment sets nothing", not ex.final_set)
    ex.execute_code('print("no final here")')
    check("1 F2 a block without FINAL clears the previous block's final", not ex.final_set and ex.final is None)
    n0 = len(SUB)
    SUB_REPLIES[:] = ["the sub-call answer"]
    ex.execute_code('FINAL_VAR(llm_query("q"))')
    check("1 F2 FINAL_VAR(llm_query(...)) makes the sub-call once", len(SUB) - n0 == 1
          and ex.final == "the sub-call answer", f"{len(SUB) - n0} calls")
    ex.execute_code('FINAL_VAR("x")\nprint(undefined_name)')
    check("1 F2 a final set in a block that then errors is marked by last_error", ex.final_set
          and "NameError" in (ex.last_error or ""))

    out, _ = ex.execute_code('print("z" * 60000)\nprint(undefined_name)')
    check("1 D25 print output is whole (no 50,000 cap) and a later traceback is shown",
          len(out) > 60000 and "NameError" in out and "OUTPUT TRUNCATED" not in out, f"{len(out)} chars")
    _, res = ex.execute_code("list(range(400))")
    check("1 D25 a returned list is whole (no 500-character cut)", res == list(range(400)))
    ch = ChunkResult(doc_name="a.pdf", chunk_idx=2, text=TEXT["a2"], page=2, chunk_id="a2")
    check("1 D25 a chunk's repr shows its whole text", TEXT["a2"] in repr(ch))

    # Q5: the code-time limit, shortened for the check
    ex.BLOCK_CODE_LIMIT_S = 0.3
    nf = len(ex.timer_firings)
    out, _ = ex.execute_code("while True:\n    pass")
    check("1 Q5 a block past the code-time limit is stopped and recorded",
          "BlockTimeLimit" in (ex.last_error or "") and len(ex.timer_firings) == nf + 1
          and ex.timer_firings[-1]["code_s"] >= 0.3, json.dumps(ex.timer_firings[-1:]))
    SUB_REPLIES[:] = [lambda p: (__import__("time").sleep(0.6), "slow")[1]]
    nf = len(ex.timer_firings)
    out, _ = ex.execute_code('r = llm_query("slow")\nfor i in range(1000):\n    pass\nprint(r)')
    check("1 Q5 the clock pauses while a sub-call is in flight (0.6 s call, 0.3 s limit)",
          ex.last_error is None and out == "slow\n" and len(ex.timer_firings) == nf, repr(ex.last_error))
    nf = len(ex.timer_firings)
    out, _ = ex.execute_code("try:\n    while True:\n        pass\nexcept:\n    pass\nprint('after')")
    check("1 Q5 a firing the block's code catches still fails the block and is recorded",
          "BlockTimeLimit" in (ex.last_error or "") and "after" not in out and len(ex.timer_firings) == nf + 1
          and ex.timer_firings[-1]["caught_by_code"] is True and ex.timer_firings[-1]["raises"] >= 2,
          json.dumps(ex.timer_firings[-1:]))
    nf = len(ex.timer_firings)
    t = __import__("time").monotonic()
    out, _ = ex.execute_code("n = 0\nwhile True:\n    try:\n        while True:\n            n += 1\n"
                             "    except BaseException:\n        n += 1")
    check("1 Q5 a block that catches every firing in a loop still stops",
          "BlockTimeLimit" in (ex.last_error or "") and len(ex.timer_firings) == nf + 1
          and __import__("time").monotonic() - t < 5, json.dumps(ex.timer_firings[-1:]))
    # review defect 2: time inside library code the block called counts and is stopped there (main thread, SIGALRM)
    nf = len(ex.timer_firings)
    t = __import__("time").monotonic()
    out, _ = ex.execute_code("m = re.search(r'(a+)+$', 'a' * 32 + 'b')")
    el = __import__("time").monotonic() - t
    check("1 Q5 a catastrophic regex (library code) is stopped at the limit",
          "BlockTimeLimit" in (ex.last_error or "") and len(ex.timer_firings) == nf + 1 and el < 2,
          f"{el:.2f} s {json.dumps(ex.timer_firings[-1:])}")
    nf = len(ex.timer_firings)
    out, _ = ex.execute_code("x = sum(range(2 * 10**8))\nprint('after')")
    check("1 Q5 a long single C call is stopped as it returns, before the next line",
          "BlockTimeLimit" in (ex.last_error or "") and "after" not in out and len(ex.timer_firings) == nf + 1,
          repr((ex.last_error or "")[:80]))
    import signal as _signal
    check("1 Q5 the clock is disarmed and SIGALRM's handler restored after the block",
          _signal.getitimer(_signal.ITIMER_REAL) == (0.0, 0.0)
          and _signal.getsignal(_signal.SIGALRM) in (_signal.SIG_DFL, None), str(_signal.getsignal(_signal.SIGALRM)))
    out, _ = ex.execute_code("print('next block runs')")
    check("1 Q5 the next block runs normally", out == "next block runs\n" and ex.last_error is None)
    check("1 Q5 the limit is 120 s, MAX_EXECUTION_TIME is gone", RLMExecutor.BLOCK_CODE_LIMIT_S == 120.0
          and not hasattr(RLMExecutor, "MAX_EXECUTION_TIME") and not hasattr(RLMExecutor, "MAX_OUTPUT_LENGTH"))
    ex.BLOCK_CODE_LIMIT_S = 120.0

    # A5: a failed sub-call raises into the block, recorded
    SUB_REPLIES[:] = [call_error(7)]
    out, _ = ex.execute_code('r = llm_summarize([get_chunks_range("a.pdf", 0, 1)[0]], task="t")\nprint(r)')
    check("1 A5 a failed sub-call raises LockCallError into the block (a traceback, no '[ERROR]' text)",
          "LockCallError" in out and "[ERROR]" not in out and c.sub_calls_failed == 1
          and ex.sub_call_failures[-1]["seq"] == 7 and ex.sub_call_failures[-1]["fn"] == "llm_summarize",
          json.dumps(ex.sub_call_failures))
    SUB_REPLIES[:] = [LockError("model not allowed")]
    e = raises(LockError, lambda: ex.execute_code('try:\n    llm_query("x")\nexcept Exception:\n    pass'))
    check("1 Q38 a LockError in a sub-call ends the run even when the block's code catches it", e is not None)

    # A6: passages set before every sub-call
    SUB_REPLIES[:] = [SUMMARY_REPLY, "plain"]
    n0 = len(SUB)
    ex.execute_code('ch = get_chunks_range("a.pdf", 0, 2)\nr = llm_summarize(ch, task="t")\nq = llm_query("x")')
    check("1 A6 a sub-call carrying chunks has their ids as passages; one carrying none has []",
          SUB[n0][1] == ["a0", "a1"] and SUB[n0 + 1][1] == [], f"{SUB[n0][1]} {SUB[n0 + 1][1]}")
    r = ex.namespace["r"]
    check("1 F16 CITATIONS_USED: only its first line is read", [x.chunk_id for x in r["citations"]] == ["a0", "a1"],
          str([x.chunk_id for x in r["citations"]]))
    check("1 Q8 inline [k] and [k, m] are written as [paper.pdf:pN]",
          "24 [a.pdf:p1]." in r["summary"] and "fastp [a.pdf:p1][a.pdf:p1]." in r["summary"]
          and "[1]" not in r["summary"], r["summary"])
    check("1 D25 llm_summarize quotes the whole chunk (no 200-character cut), verified",
          r["citations"][1].quote == TEXT["a1"] and all(x.verified for x in r["citations"]))
    check("1 Q3 successful sub-calls are counted apart from failed ones", c.sub_calls_ok >= 3
          and c.sub_calls_failed == 1, f"ok {c.sub_calls_ok} failed {c.sub_calls_failed}")

    # D89 (Q145 O3): a Gemini block, a recitation or an empty reply with no finishReason returns to the code as ""
    # (lock_adapter._finish) and the code goes on; each counts as failed, as when it raised before D89, never as ok;
    # a STOP empty reply counts as before (ok), so the quality gate's count is what it was before D89
    # D90 (Q1, Q2): a recitation stop and a malformed reply return what they held (lock_adapter._returned) and count
    # as failed, as when they raised before D89
    def d89(status, stop, seq, text=""):
        return {"response": text, "eval_count": 0, "prompt_eval_count": 7, "done_reason": "stop",
                "lock_record": {"provider": "gemini", "status": status, "stop_reason": stop, "seq": seq,
                                "error": None if status == "empty" else f"fake {status}"}}
    ok0, failed0, n_fail0 = c.sub_calls_ok, c.sub_calls_failed, len(ex.sub_call_failures)
    SUB_REPLIES[:] = [d89("blocked", "SAFETY", 21), d89("recitation", "RECITATION", 22, "half"),
                      d89("empty", "STOP", 23), d89("empty", None, 24),
                      d89("malformed_function_call", "MALFORMED_FUNCTION_CALL", 25),
                      d89("malformed_response", "MALFORMED_RESPONSE", 26, "partial")]
    out, _ = ex.execute_code('a = llm_query("x")\nb = llm_query("y")\nd = llm_query("z")\ne = llm_query("w")\n'
                             'f = llm_query("v")\ng = llm_query("u")\n'
                             'print(repr(a), repr(b), repr(d), repr(e), repr(f), repr(g), "went on")')
    check("1 D89, D90 a blocked, a recitation, two empty and two malformed sub-calls return into the code ('' for the "
          "block, the empty ones and the malformed call with no text; the recitation's and the malformed reply's "
          "text), which goes on",
          out == "'' 'half' '' '' '' 'partial' went on\n" and ex.last_error is None, repr(out))
    check("1 D89, D90 the blocked, the recitation, the no-finishReason empty and both malformed sub-calls count in "
          "sub_calls_failed, listed with their seqs and what they returned, as before D89; the STOP empty one counts "
          "in sub_calls_ok, as before",
          c.sub_calls_failed == failed0 + 5 and c.sub_calls_ok == ok0 + 1
          and [(f["seq"], f["status"], f.get("returned")) for f in ex.sub_call_failures[n_fail0:]]
          == [(21, "blocked", "empty text"), (22, "recitation", "its text (4 characters)"), (24, "empty", "empty text"),
              (25, "malformed_function_call", "empty text"), (26, "malformed_response", "its text (7 characters)")],
          f"ok {c.sub_calls_ok - ok0} failed {c.sub_calls_failed - failed0} {ex.sub_call_failures[n_fail0:]}")
    c.sub_calls_ok, c.sub_calls_failed = ok0, failed0     # the later checks count from the state before
    del ex.sub_call_failures[n_fail0:]
    SUB_REPLIES[:] = ["SUMMARY:\nFastp was used for trimming of the reads [1] and it was run with default settings "
                      "throughout. This long sentence carries no citation at all here.\nCITATIONS_USED: 1"]
    ex.execute_code('ch = get_chunks_range("a.pdf", 0, 2)\nr = llm_summarize(ch)')
    r = ex.namespace["r"]
    check("1 review D1 a cited sentence is not reported as uncited after the [paper.pdf:pN] rewrite",
          r["uncited_claims"] == ["This long sentence carries no citation at all here"]
          and "[a.pdf:p1]" in r["summary"], str(r["uncited_claims"]))
    SUB_REPLIES[:] = ["Text without the label [1].\nCITATIONS_USED: 2"]
    ex.execute_code('ch = get_chunks_range("a.pdf", 0, 2)\nr = llm_summarize(ch)')
    r = ex.namespace["r"]
    check("1 F16 CITATIONS_USED is read without SUMMARY:", [x.chunk_id for x in r["citations"]] == ["a1"]
          and r["summary"] == "Text without the label [a.pdf:p1].", repr(r["summary"]))
    many = " ".join(f"Uncited sentence number {i} with enough length to count." for i in range(8))
    SUB_REPLIES[:] = [f"SUMMARY: {many}\nCITATIONS_USED: none"]
    ex.execute_code('r = llm_summarize(["plain text"])')
    check("1 D25 every uncited claim is returned (no [:5])", len(ex.namespace["r"]["uncited_claims"]) == 8)
    SUB_REPLIES[:] = ['Here: {"a": {"b": 1}, "c": [1, 2]} and more text', "no json at all"]
    ex.execute_code('e1 = llm_extract(["t"], schema={"a": "dict"})\ne2 = llm_extract(["t"], schema={"a": "x"})')
    check("1 F16 llm_extract keeps nested JSON (raw_decode from the first '{')",
          ex.namespace["e1"] == {"a": {"b": 1}, "c": [1, 2]}, repr(ex.namespace["e1"]))
    check("1 F16 an unparsed extraction is returned raw and marked", ex.namespace["e2"].get("raw") == "no json at all"
          and "error" in ex.namespace["e2"])
    check("1 F13 sub-calls pass no options (the lock sets them)",
          "options=" not in inspect.getsource(RLMExecutor._sub_call).split('"""')[-1])

# ═════════════════════════════ 2. context ═════════════════════════════
with rc.run(ctx()):
    c = make_context()
    check("2 Q10 an empty quote is not verified", c.cite("a.pdf", 1, "").verified is False)
    check("2 Q10 the whole quote must match: a right start with an invented tail is not verified",
          c.cite("a.pdf", 1, TEXT["a0"][:60] + " and an invented tail").verified is False)
    q = "Sample size was 24   patients. The methods used\nfastp"
    cit = c.cite("a.pdf", 1, q)
    check("2 Q10 whitespace is collapsed on both sides", cit.verified and cit.chunk_id == "a0")
    check("2 Q10 no other normalisation (an ellipsis is not forgiven)",
          c.cite("a.pdf", 1, "Sample size was ... patients").verified is False)
    long1 = TEXT["a2"]
    c.citations.clear()
    c1 = c.cite("a.pdf", 2, long1)
    c2 = c.cite("a.pdf", 2, long1[:60])
    c.report_sections.append(ReportSection(title="S", content="body", citations=[c1, c2], order=0))
    rep = c.get_report()
    src = [ln for ln in rep.splitlines() if ln.startswith("[")]
    check("2 F15 quotes sharing their first 50 characters are both listed (whole-quote de-duplication)",
          len(src) == 2, str(len(src)))
    check("2 Q9 the Sources list shows the 120-character preview",
          all(len(ln.split(': "', 1)[1]) <= rlm_context.SOURCES_PREVIEW_CHARS + 4 for ln in src)
          and rlm_context.SOURCES_PREVIEW_CHARS == 120)
    check("2 Q9 the record keeps the whole quote", c.citations_record()[0]["quote"] == long1
          and c.citations_record()[0]["chunk_id"] == "a2")
    auto = c.auto_generate_report_from_citations()
    check("2 D25 the fallback dump and its references carry whole quotes", auto.count(long1) == 2, "")
    s = c.get_document_structure("a.pdf")
    check("2 D25 get_document_structure has no 200-character preview", all("preview" not in p for p in s["pages"]))
    rr = c.search_regex(r"x")
    check("2 D25 search_regex keeps every match (not the first 5)",
          max(len(x.metadata["matches"]) for x in rr) >= 300)
    sem = c.search_semantic("anything", doc_name="a.pdf")
    check("2 Q14 search_semantic(doc_name=X) drops keyword hits from other papers and counts them",
          [x.doc_name for x in sem] == ["a.pdf"] and c.retrievals[-1]["outside_filter"] == 1
          and c.retrievals[-1]["reranked"] is True, json.dumps(c.retrievals[-1]))
    sem_all = c.search_semantic("anything")
    check("2 Q14 without doc_name every paper's hits are returned", [x.doc_name for x in sem_all] == ["a.pdf", "b.pdf"])
    c.passages_seen.clear()
    c.search_keyword("methods", doc_name="a.pdf")
    c.get_chunk("b.pdf", 0)
    check("2 A6 passages_seen holds the ids of the chunks returned to the code, once each, in order",
          c.passages_seen == ["a1", "a0", "a2", "b0"], str(c.passages_seen))

    # D40: one shared reranker; a failed load raises
    src_from_index = inspect.getsource(RLMContext.from_index)
    check("2 D40 from_index always reranks with the shared reranker (no 800-chunk rule)",
          "use_reranker=True" in src_from_index and "context._reranker = shared_reranker()" in src_from_index
          and "reranker=context._reranker" in src_from_index and "> 800" not in src_from_index)
    # The real reranker module with its model class stubbed: get_reranker() builds it (a load failure raises, A4)
    from backend.retrieval import reranker as rr
    saved = rr.CrossEncoderReranker, rr._default_reranker
    for loads in (False, True):
        built = []

        class CrossEncoderReranker:  # noqa: N801
            def __init__(self, _l=loads, _b=built):
                if not _l:
                    raise RuntimeError("model did not load")
                _b.append(self)
        rr.CrossEncoderReranker, rr._default_reranker = CrossEncoderReranker, None
        if not loads:
            check("2 D40 a reranker that does not load raises", raises(RuntimeError, rlm_context.shared_reranker))
        else:
            a, b = rlm_context.shared_reranker(), rlm_context.shared_reranker()
            check("2 D40 review D2 one reranker instance for the process, the passive strategies' get_reranker()",
                  a is b is rr.get_reranker() and len(built) == 1)
    rr.CrossEncoderReranker, rr._default_reranker = saved

# ═════════════════════════════ 3. orchestrator ═════════════════════════════
o = RLMOrchestrator(None, GEM)
c = make_context()
check("3 Q1 no pin from a capitalised word ('In' is in a.pdf's title)",
      o._extract_target_document("In which year was the study run?", c) is None)
check("3 Q1 a .pdf name still pins", o._extract_target_document("Summarize paper 'b.pdf' please", c) == "b.pdf")
check("3 F19 ```Python with trailing spaces and ```py with CRLF are code blocks",
      o._extract_code_blocks("```Python  \nprint(1)\n```\ntext\n```py\r\nx = 2\n```") == ["print(1)", "x = 2"])
check("3 F2 the code-text scanners are gone", not hasattr(RLMOrchestrator, "_check_final_answer")
      and not hasattr(RLMOrchestrator, "_compact_history"))

# Q4: every block, in order; stop at the block that sets the final answer
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([block('print("A")') + block('print("B")') + block('print("C")'),
                      block(WORK) + block('FINAL_VAR(get_report())') + block('print("NEVER")')],
                     max_turns=3)
check("3 Q4 all three blocks of a reply run (not the first 2)", "[Block 3]\nC" in router.seen[1][0][-1]["content"],
      router.seen[1][0][-1]["content"][:80])
check("3 Q4 blocks after the one that sets the final answer do not run",
      isinstance(res, RLMResult) and res.metadata["n_code_blocks_run"] == 5 and res.metadata["stop_reason"] == "final",
      f"{type(res).__name__} {getattr(res, 'metadata', {}).get('n_code_blocks_run')}")
check("3 review defect 3 the progress line shows Mentori's count, every model call (1 root turn, no sub-call)",
      "[Progress: 1 LLM calls, " in router.seen[1][0][-1]["content"], router.seen[1][0][-1]["content"][-80:])
check("3 Q8 the answer's citations are [paper.pdf:pN]", "[a.pdf:p1]" in res and "## Sources" in res)
check("3 A6 root turns carry passages [] (not the last sub-call's)", all(p == [] for _, p, _ in router.seen),
      str([p for _, p, _ in router.seen]))
check("3 F13 root turns pass no options (cuts.md orchestrator.py:162)",
      all("options" not in kw for _, _, kw in router.seen))
MD_KEYS = {"stop_reason", "turns", "rejections", "sub_calls_ok", "sub_calls_failed", "n_code_blocks_run", "nudges",
           "passages_seen", "timer_firings", "call_error", "citations", "retrievals", "max_turns"}
check("3 A6 the metadata carries every key of the interface", MD_KEYS <= set(res.metadata),
      str(sorted(MD_KEYS - set(res.metadata))))
check("3 A6 passages_seen in the metadata", res.metadata["passages_seen"] == ["a1", "a0", "a2"]
      and res.metadata["sub_calls_ok"] == 3 and res.metadata["turns"] == 2)
check("3 RLMResult is a str that survives json, deepcopy and dataclasses.asdict",
      json.loads(json.dumps({"a": res}))["a"] == str(res) and copy.deepcopy(res).metadata == res.metadata
      and dataclasses.asdict(dataclasses.make_dataclass("G", [("answer", str)])(res))["answer"] == str(res))

# F3 + Q3 + F11: a short answer without sub-calls is rejected (by the gate, not by its length), then accepted
short = 'FINAL_VAR("The papers do not report this.")'
res, router, c = run([block(short)] * 4, max_turns=5)
hist = router.seen[1][0]
check("3 Q3 three prose-free turns without sub-calls do not pass the gate (rejection 1)",
      "INSUFFICIENT ANALYSIS: You have made 0 calls to llm_summarize/llm_query/llm_extract. You need at least 3"
      in hist[-1]["content"])
check("3 F11 a rejected reply is in the history once, its rejection in the same message as its output",
      sum(1 for m in hist if m["role"] == "assistant") == 1 and hist[-1]["content"].startswith("Output:"),
      str([m["role"] for m in hist]))
check("3 F3 a 31-character answer is accepted after the rejections (final_after_max_rejections)",
      isinstance(res, RLMResult) and str(res) == "The papers do not report this."
      and res.metadata["stop_reason"] == "final_after_max_rejections" and res.metadata["rejections"] == 3,
      repr(res)[:80])
res, router, c = run([block(WORK + '\nFINAL("Short: 24 patients [a.pdf:p1].")')], max_turns=5)
check("3 F3 a short answer after 3 sub-calls is accepted at once (stop_reason final)",
      isinstance(res, RLMResult) and str(res) == "Short: 24 patients [a.pdf:p1]."
      and res.metadata["stop_reason"] == "final" and res.metadata["rejections"] == 0)
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([block('FINAL_VAR("")'), block('FINAL(None)'),
                      block(WORK + '\nFINAL("Short: 24 patients [a.pdf:p1].")')], max_turns=5)
check("3 review defect 4 a final answer of '' or None is passed over (no rejection, the run goes on), counted",
      isinstance(res, RLMResult) and res.metadata["stop_reason"] == "final" and res.metadata["rejections"] == 0
      and res.metadata["blank_finals_skipped"] == 2 and res.metadata["turns"] == 3
      and "INSUFFICIENT" not in router.seen[1][0][-1]["content"],
      f"{type(res).__name__} {json.dumps({k: getattr(res, 'metadata', {}).get(k) for k in ('stop_reason', 'rejections', 'blank_finals_skipped', 'turns')})}")
res, router, c = run([block('add_to_report("S", "   ", [])\nFINAL_VAR(get_report())')] * 6, max_turns=6)
check("3 F3 a get_report() answer whose sections are all empty counts as empty",
      isinstance(res, RLMRunError) and res.metadata["empty_finals_dropped"] >= 1
      and res.metadata["stop_reason"] == "max_turns_partial" or
      (isinstance(res, RLMResult) and res.metadata["stop_reason"] == "max_turns_partial"),
      f"{type(res).__name__} {getattr(res, 'metadata', {}).get('stop_reason')}")

# Q7, Q2, Q13, Q6, F5: prose turns get the end-of-turn checks
res, router, c = run(["Let me think."] * 12, max_turns=12)
last_msgs = router.seen[-1][0]
kinds = [n["kind"] for n in res.metadata["nudges"]]
check("3 Q7 a prose turn still gets the last-turn message (emergency)", "emergency" in kinds
      and "turn6_example" in kinds and "turn9_critical" in kinds, str(kinds))
emerg = [m["content"] for m in last_msgs if m["content"].startswith("EMERGENCY")]
example = [m["content"] for m in last_msgs if m["content"].startswith("You have been searching")]
check("3 Q2 unpinned rescue searches with the question across all papers",
      emerg and "search_semantic('What sample size did the study use?')" in emerg[0]
      and "list_documents()[0]" not in emerg[0] and "list_documents()[0]" not in example[0])
check("3 Q13 rescue and example code teach no text slicing", "[:100]" not in example[0]
      and "chunks[0].text)" in example[0])
check("3 F5 no history compaction (no [HISTORY SUMMARY], every turn kept)",
      not any("HISTORY SUMMARY" in m["content"] for m in last_msgs)
      and sum(1 for m in last_msgs if m["role"] == "assistant") == 11)
check("3 max_turns_empty: no answer, RLMRunError with the record", isinstance(res, RLMRunError)
      and res.metadata["stop_reason"] == "max_turns_empty" and res.metadata["turns"] == 12)
c2 = make_context()
c2.max_tokens = 1
res, router, _ = run(["prose"] * 2, max_turns=2, context=c2)
check("3 Q6 no token-budget warning", not any("token budget" in m["content"] for m in router.seen[-1][0]))
res, router, c = run(["prose"] * 3, max_turns=3, task="Summarize b.pdf methods")
emerg = [m["content"] for m in router.seen[-1][0] if m["content"].startswith("EMERGENCY")]
check("3 Q2 a pinned run's rescue keeps its document", emerg and 'doc_name="b.pdf"' in emerg[0]
      and res.metadata["target_document"] == "b.pdf")

# Q11 and the other stop reasons
res, router, c = run([block(WORK)] + ["prose"] * 2, max_turns=3)
check("3 Q11 max_turns_partial keeps the turn-limit note in the answer and records it",
      isinstance(res, RLMResult) and res.endswith(TURN_LIMIT_NOTE) and res.metadata["stop_reason"] ==
      "max_turns_partial" and res.metadata["turn_limit_note"] is True)
res, router, c = run([block('cite("a.pdf", 1, "Sample size was 24 patients.")')] + ["prose"], max_turns=2)
check("3 max_turns_auto_generated", isinstance(res, RLMResult)
      and res.metadata["stop_reason"] == "max_turns_auto_generated" and "Auto-Generated" in res)
res, router, c = run([block('r = [llm_query("q") for _ in range(3)]\ncite("a.pdf", 1, "Sample size was 24 patients.")'
                            '\nFINAL_VAR(get_report())')] * 4, max_turns=5)
check("3 auto_generated (citations, no section: rejected 3 times as before, then the dump)",
      isinstance(res, RLMResult) and res.metadata["stop_reason"] == "auto_generated"
      and res.metadata["rejections"] == 3 and res.metadata["accepted_after_max_rejections"] is True,
      f"{type(res).__name__} {getattr(res, 'metadata', {}).get('stop_reason')}")
res, router, c = run([block('print(1)'), call_error(42)], max_turns=4)
check("3 A5 a failed root call ends the run: call_error, no answer, the call's seq recorded",
      isinstance(res, RLMRunError) and res.metadata["stop_reason"] == "call_error"
      and res.metadata["call_error"]["seq"] == 42 and res.metadata["turns"] == 2,
      f"{type(res).__name__} {getattr(res, 'metadata', {}).get('call_error')}")
res, router, c = run([LockError("not allowed")], max_turns=2)
check("3 Q38 a LockError on a root call is raised, not recorded as an answer", isinstance(res, LockError))
SUB_REPLIES[:] = [LockError("refused")]
res, router, c = run([block('try:\n    llm_query("x")\nexcept Exception as e:\n    print("caught")')], max_turns=2)
check("3 Q38 a LockError in a sub-call ends the run", isinstance(res, LockError), type(res).__name__)
SUB_REPLIES[:] = [call_error(9)]
res, router, c = run([block('r = llm_query("x")'), "prose"], max_turns=2)
check("3 A5 a failed sub-call is in the record and the run goes on",
      isinstance(res, RLMRunError) and res.metadata["sub_calls_failed"] == 1
      and res.metadata["sub_call_failures"][0]["seq"] == 9 and "LockCallError" in router.seen[1][0][-2]["content"]
      + router.seen[1][0][-1]["content"] and res.metadata["code_block_errors"] == 1)
check("3 every stop reason is named", set(STOP_REASONS) == {"final", "final_after_max_rejections", "auto_generated",
      "max_turns_partial", "max_turns_auto_generated", "max_turns_empty", "call_error"})

# ═════════════════════════════ 4. verification (verify=True) ═════════════════════════════
fin = block(WORK + '\nFINAL_VAR(get_report())')
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([fin], max_turns=3, verify=True, gen_replies=["VERDICT: YES\nREASON: ok"] * 2)
v = res.metadata["verify"]
check("4 the verifier maps [paper.pdf:pN] to the collected citations", v and v["verified"] == 2 and v["errors"] == 0
      and "## Verification Summary" in res, json.dumps({k: v[k] for k in ("total_claims", "verified", "no_citation")})
      if v else "none")
check("4 the verifier's prompt carries whole quotes and its call the cited chunk ids as passages",
      TEXT["a1"] in router.gen_seen[0][0] and sorted(router.gen_seen[0][1]) == ["a0", "a1"] and not router.gen_seen[0][2],
      str(router.gen_seen[0][1]))
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([fin], max_turns=3, verify=True, gen_replies=[call_error(5), "VERDICT: NO\nREASON: no"])
v = res.metadata["verify"]
check("4 A5 a failed verifier call is status error with its seq, kept out of unverified and the confidence",
      v["errors"] == 1 and v["unverified"] == 1 and v["failed_claims"][0]["error"]["seq"] == 5
      and v["failed_claims"][0]["confidence"] is None and v["overall_confidence"] == 0.0, json.dumps(v)[:200])

# ═════════════════════════════ 5. prompt ═════════════════════════════
p = get_rlm_orchestrator_prompt()
check("5 Q12 the 'avoid complex for-loops' rule is removed", "for-loops" not in p and "5. When finished" in p)
check("5 Q13 the worked example teaches no text slicing", "text[:" not in p and "chunks[0].text)" in p)

# ═════════════════════════════ 6. drivers ═════════════════════════════
e6 = importlib.import_module("exp_06_depth_sweep")
e2 = importlib.import_module("exp_02_scaling_generate_rlm")
check("6 Q29 exp_06 has no whole-run retry", not hasattr(e6, "MAX_RETRIES") and not hasattr(e6, "run_rlm_with_retry")
      and "for attempt" not in inspect.getsource(e6))
check("6 Q29 exp_02 has no whole-answer retry and no answer-text error check",
      not any(hasattr(e2, n) for n in ("MAX_RETRIES_PER_QUESTION", "ERROR_PATTERNS", "_detect_answer_error"))
      and "for attempt" not in inspect.getsource(e2))
check("6 limits #127 exp_02 resumes every stored answer as done (a failed one included)",
      'for r in existing_results:\n                existing_keys.add(r["answer_key"])' in inspect.getsource(e2.run_generation))


async def _fake_from_index(index_name, user_id, max_tokens=1_000_000):
    return make_context()

e6.RLMContext.from_index = staticmethod(_fake_from_index)


def drive6(replies, depth=3):
    router = FakeRouter(replies)

    async def go():
        with rc.run(ctx()):
            return await e6.run_rlm("What sample size?", router, GEM, "u", depth, "idx")
    with contextlib.redirect_stdout(io.StringIO()):
        return asyncio.run(go())


SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
r6 = drive6([fin])
check("6 exp_06 stores the answer with its record and stop reason", r6["stop_reason"] == "final" and r6["rlm"]
      and r6["rlm"]["sub_calls_ok"] == 3 and r6["retrieved_passages"] == 3 and r6["error"] is None
      and "setup_s" in r6, json.dumps({k: r6[k] for k in ("stop_reason", "retrieved_passages", "error")}))
r6 = drive6(["prose"] * 2, depth=2)
check("6 exp_06 stores a run that ended with no answer: answer '', error, record", r6["answer"] == ""
      and r6["stop_reason"] == "max_turns_empty" and r6["error"].startswith("max_turns_empty")
      and r6["rlm"]["turns"] == 2)
e = None
try:
    drive6([LockError("refused")])
except LockError as x:
    e = x
check("6 Q38 exp_06 stops on a LockError (nothing stored)", e is not None)

# review D3: exp_02 sees a setup failure even where exp1's _run_rlm stores it as the answer's error
async def _no_index(*a, **k):
    raise RuntimeError("D40: the reranker did not load")


def drive2(replies, from_index):
    saved_from, saved_run = RLMContext.__dict__["from_index"], RLMOrchestrator.__dict__["run"]
    RLMContext.from_index = staticmethod(from_index)

    async def go():
        with rc.run(ctx()), e2._setup_failures() as s:
            try:
                g = await e2.generate_one_rlm("What sample size?", FakeRouter(replies), GEM, "u", 2, "idx", "rlm_2")
            except BaseException as x:   # once exp1's _run_rlm lets setup errors raise
                g = x
        return g, s
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            g, s = asyncio.run(go())
        restored = RLMOrchestrator.__dict__["run"] is saved_run and isinstance(RLMContext.__dict__["from_index"],
                                                                                staticmethod)
        return g, s, restored
    finally:
        RLMContext.from_index = saved_from


g, s, restored = drive2([], _no_index)
check("6 review D3 exp_02 collects a failed index or reranker load (from_index), and restores the methods",
      len(s) == 1 and isinstance(s[0], RuntimeError) and restored, f"{s} {type(g).__name__}")
g, s, restored = drive2([LockError("refused")], _fake_from_index)
check("6 review D3 exp_02 collects a LockError from the RLM run (Q38)", len(s) == 1 and isinstance(s[0], LockError),
      f"{s} {type(g).__name__}")
g, s, restored = drive2(["prose"] * 2, _fake_from_index)
check("6 review D3 an answer that ended with no answer (RLMRunError) is not a setup failure",
      s == [] and not isinstance(g, BaseException) and restored, f"{s} {getattr(g, 'error', g)}")
src2 = inspect.getsource(e2.run_generation)
check("6 review D3 exp_02 raises a collected setup failure before storing the answer, saving earlier answers first",
      "if setup:\n                raise setup[0]" in src2 and src2.index("raise setup[0]") < src2.index("results.append")
      and "except BaseException:\n            _save(results)\n            raise" in src2)

# limits #147: the merge refuses two different rows for one key
rd = tmp / "results_v4"
rd.mkdir()
e6.RESULTS_DIR = rd
row = {"answer_key": "rlm_3|Q1|d1", "question_id": "Q1", "depth": 3, "draw": 1, "answer": "x", "error": None,
       "latency_s": 1.0}
for name, rows in (("v4_9_depth_sweep_m_a.json", [row]), ("v4_9_depth_sweep_m_latest.json", [row])):
    (rd / name).write_text(json.dumps({"results": rows}))
e6.merge_results("gemini::m")
check("6 limits #147 equal rows for one key merge (a run file and its _latest)",
      json.loads((rd / "v4_9_depth_sweep_m_merged.json").read_text())["n_results"] == 1)
(rd / "v4_9_depth_sweep_m_b.json").write_text(json.dumps({"results": [{**row, "answer": "", "error": "boom"}]}))
e = raises(SystemExit, lambda: e6.merge_results("gemini::m"))
check("6 limits #147 two different rows for one key refuse the merge and are listed",
      e is not None and "rlm_3|Q1|d1" in str(e), str(e)[:120])

# ═════════════════════════════ 7. round 3 (D75, Q65-Q74) ═════════════════════════════
import threading  # noqa: E402
import time  # noqa: E402

# Q65: a sub-call handed an empty list of passages is counted apart; the gate does not count it
with rc.run(ctx()):
    c = make_context()
    ex = RLMExecutor(c, None, GEM)
    SUB_REPLIES[:] = []
    ex.execute_code('e = search_keyword("zzz-not-there")\nr1 = llm_summarize(e)\nr2 = llm_extract(e, schema={"a": "str"})'
                    '\nq1 = llm_query("combine", context_chunks=[])')
    check("7 Q65 llm_summarize, llm_extract and llm_query on an empty list are sub_calls_empty, not sub_calls_ok",
          ex.last_error is None and c.sub_calls_empty == 3 and c.sub_calls_ok == 0 and c.llm_calls_made == 3,
          f"empty {c.sub_calls_empty} ok {c.sub_calls_ok} calls {c.llm_calls_made} {ex.last_error}")
    ex.execute_code('q2 = llm_query("combine the summaries")\nr3 = llm_summarize(["passage text as a string"])\n'
                    'r4 = llm_summarize(search_keyword("methods", doc_name="a.pdf"))')
    check("7 Q65 llm_query(prompt) with no context, passages as strings and a found list still count",
          c.sub_calls_ok == 3 and c.sub_calls_empty == 3, f"ok {c.sub_calls_ok} empty {c.sub_calls_empty}")

# Q65 + Q66: the live case, three summaries of which two read nothing: refused, and the refusal names its count
EMPTY_TWO = ('ch = search_keyword("methods", doc_name="a.pdf")\nr1 = llm_summarize(ch, task="t")\n'
             'e = search_keyword("best practices")\nr2 = llm_summarize(e, task="t")\nr3 = llm_summarize(e, task="t")\n'
             'add_to_report("Methods", r1["summary"], r1["citations"])\nFINAL_VAR(get_report())')
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([block(EMPTY_TWO)] + ["prose"] * 3, max_turns=4)
msg = router.seen[1][0][-1]["content"]
check("7 Q65 a final after one real and two empty summaries is refused, the empties recorded",
      isinstance(res, RLMResult) and res.metadata["rejections"] == 1 and res.metadata["sub_calls_ok"] == 1
      and res.metadata["sub_calls_empty"] == 2 and res.metadata["stop_reason"] == "max_turns_partial",
      json.dumps({k: getattr(res, "metadata", {}).get(k) for k in ("rejections", "sub_calls_ok", "sub_calls_empty",
                                                                    "stop_reason")}))
check("7 Q66 the refusal's first sentence names what it counts ('1 call to llm_summarize/llm_query/llm_extract'), "
      "Q122 the two empty ones named as not counted",
      "INSUFFICIENT ANALYSIS: You have made 1 call to llm_summarize/llm_query/llm_extract (2 more were given an empty "
      "list of passages and do not count). You need at least 3 calls to llm_summarize/llm_query/llm_extract before "
      "completing." in msg and "LLM calls. " not in msg, msg[-400:])
check("7 Q66 the progress line stays Mentori's count of every model call (1 root turn + 3 sub-calls)",
      "[Progress: 4 LLM calls, " in msg, msg[-400:])

# Q67, Q68: the turn-6 example and the last-turn rescue, unpinned and pinned
res, router, c = run(["prose"] * 7, max_turns=7)
msgs = [m["content"] for m in router.seen[-1][0]]
ex6 = [m for m in msgs if m.startswith("You have been searching")]
em = [m for m in msgs if m.startswith("EMERGENCY")]
check("7 Q67 the unpinned example and rescue summarise the whole list (no chunks[:5], no chunks[:10])",
      ex6 and em and "chunks[:" not in ex6[0] and "chunks[:" not in em[0]
      and "result = llm_summarize(chunks, task=" in ex6[0]
      and 'result = llm_summarize(chunks, task="Provide a comprehensive summary")' in em[0], (ex6 or [""])[0][-300:])
check("7 Q68 the unpinned turn-6 example's task is the question, its section 'Findings'",
      ex6 and "result = llm_summarize(chunks, task='What sample size did the study use?')" in ex6[0]
      and 'add_to_report("Findings", ' in ex6[0] and "Summarize the methods" not in ex6[0]
      and 'add_to_report("Methods"' not in ex6[0], (ex6 or [""])[0][-300:])
res, router, c = run(["prose"] * 7, max_turns=7, task="Summarize b.pdf methods")
msgs = [m["content"] for m in router.seen[-1][0]]
ex6 = [m for m in msgs if m.startswith("You have been searching")]
em = [m for m in msgs if m.startswith("EMERGENCY")]
check("7 Q68 the pinned turn-6 example stays Mentori's ('Summarize the methods', 'Methods'), without the slice",
      ex6 and 'chunks = search_keyword("methods", doc_name="b.pdf")' in ex6[0]
      and 'result = llm_summarize(chunks, task="Summarize the methods")' in ex6[0]
      and 'add_to_report("Methods", ' in ex6[0], (ex6 or [""])[0][-300:])
check("7 Q67 the pinned rescue summarises every passage its search returned",
      em and 'search_keyword("", doc_name="b.pdf")' in em[0] and "llm_summarize(chunks, task=" in em[0]
      and "chunks[:" not in em[0], (em or [""])[0][-200:])

# Q67, Q69: the prompt
p = get_rlm_orchestrator_prompt()
check("7 Q67 the prompt's worked example has no list slice",
      "chunks[:" not in p and 'result = llm_summarize(chunks, task="Summarize the methods section")' in p
      and 'result2 = llm_summarize(results_chunks, task="Summarize the results")' in p)
check("7 Q69 rule 2 and 'one ```repl block per turn' stay as Mentori wrote them",
      "2. Use ONLY ONE code block per response. Do not write multiple blocks." in p
      and "Write one ```repl block per turn." in p)

# Q70: the blocks a refused final answer skipped are named
res, router, c = run([block('print("A")') + block('FINAL_VAR(get_report())') + block('print("C")')
                      + block('print("D")')] + ["prose"] * 3, max_turns=4)
msg = router.seen[1][0][-1]["content"]
check("7 Q70 a refused final in block 2 of 4: '[Blocks 3-4 not run: block 2 set the final answer]'",
      "[Blocks 3-4 not run: block 2 set the final answer]" in msg and "[Block 3]" not in msg
      and "INSUFFICIENT ANALYSIS" in msg and msg.index("not run") < msg.index("[Progress:"), msg[:300])
res, router, c = run([block('FINAL_VAR(get_report())') + block('print("B")')] + ["prose"] * 3, max_turns=4)
msg = router.seen[1][0][-1]["content"]
check("7 Q70 one skipped block: '[Block 2 not run: block 1 set the final answer]'",
      "[Block 2 not run: block 1 set the final answer]" in msg, msg[:200])
res, router, c = run([block('print("A")') + block('FINAL_VAR(get_report())')] + ["prose"] * 3, max_turns=4)
check("7 Q70 a final in the last block names nothing", "not run" not in router.seen[1][0][-1]["content"])

# Q71: a reply with no code block is never searched for FINAL(...)
res, router, c = run(["FINAL(Sarek uses Nextflow and containers to make runs reproducible.)"], max_turns=1)
check("7 Q71 a prose FINAL(...) is not an answer: no_code nudge, no answer",
      isinstance(res, RLMRunError) and res.metadata["stop_reason"] == "max_turns_empty"
      and [n["kind"] for n in res.metadata["nudges"]][:1] == ["no_code"], type(res).__name__)


# Q72: search_semantic's time counts as code time, the clock never raises inside it, retrieval_s in each firing
class SlowRetriever(FakeRetriever):
    """A retriever that spends busy_s of Python time in retrieve() (a frame the alarm could raise into)."""
    def __init__(self, busy_s):
        self.busy_s, self.finished, self.interrupted = busy_s, 0, 0

    def retrieve(self, *a, **k):
        t = time.monotonic()
        try:
            while time.monotonic() - t < self.busy_s:
                pass
        except BaseException:
            self.interrupted += 1
            raise
        self.finished += 1
        return super().retrieve(*a, **k)


def slow_executor(busy_s, limit=0.3):
    c = make_context()
    c._retriever = SlowRetriever(busy_s)
    ex = RLMExecutor(c, None, GEM)
    ex.BLOCK_CODE_LIMIT_S = limit
    return c, ex


with rc.run(ctx()):
    c, ex = slow_executor(0.6)
    out, _ = ex.execute_code('ch = search_semantic("q")\nprint("after")')
    f = ex.timer_firings[-1] if ex.timer_firings else {}
    check("7 Q72 main thread: a firing during search_semantic is held, raised as it returns (retriever whole)",
          "BlockTimeLimit" in (ex.last_error or "") and "after" not in out and c._retriever.finished == 1
          and c._retriever.interrupted == 0 and len(ex.timer_firings) == 1 and len(c.retrievals) == 1,
          json.dumps(ex.timer_firings))
    check("7 Q72 the firing records the block's retrieval seconds", f.get("retrieval_s", 0) >= 0.5
          and f.get("code_s", 0) >= 0.5, json.dumps(f))
    out, _ = ex.execute_code('print("next")')
    check("7 Q72 the next block runs normally, the clock disarmed", out == "next\n" and ex.last_error is None
          and __import__("signal").getitimer(__import__("signal").ITIMER_REAL) == (0.0, 0.0))
    c, ex = slow_executor(0.2)
    out, _ = ex.execute_code('ch = search_semantic("q")\nn = 0\nwhile True:\n    n += 1')
    f = ex.timer_firings[-1] if ex.timer_firings else {}
    check("7 Q72 retrieval time counts: 0.2 s of search + loop fires at 0.3 s of code time (retrieval_s ~0.2)",
          "BlockTimeLimit" in (ex.last_error or "") and 0.15 <= f.get("retrieval_s", 0) < 0.3
          and f.get("wall_s", 9) < 0.45 and c._retriever.interrupted == 0, json.dumps(f))
    c, ex = slow_executor(0.05)
    out, _ = ex.execute_code('ch = search_semantic("q")\nprint(len(ch))')
    check("7 Q72 a search under the limit runs and records no firing", out == "2\n" and ex.timer_firings == [])

    c, ex = slow_executor(0.6)
    box = {}

    def _in_thread():
        box["r"] = ex.execute_code('ch = search_semantic("q")\nprint("after")')
    th = threading.Thread(target=_in_thread)
    th.start()
    th.join(10)
    check("7 Q72 off the main thread (line clock): never raises inside the search, raised at the next line",
          "BlockTimeLimit" in (ex.last_error or "") and "after" not in box.get("r", ("",))[0]
          and c._retriever.finished == 1 and c._retriever.interrupted == 0
          and ex.timer_firings and ex.timer_firings[-1]["retrieval_s"] >= 0.5, json.dumps(ex.timer_firings))
    c, ex = slow_executor(0.0)
    ex.execute_code("while True:\n    pass")
    check("7 Q72 a firing with no search records retrieval_s 0.0", ex.timer_firings
          and ex.timer_firings[-1]["retrieval_s"] == 0.0, json.dumps(ex.timer_firings))

# Q73, Q74: the drivers (files outside the RLM area; these fail until the shared changes are applied)
e1 = importlib.import_module("tests.experiments.exp1_rlm_vs_singlepass")
e = None
try:
    drive6([KeyError("a slip in our own code")])
except KeyError as x:
    e = x
except Exception as x:   # noqa: BLE001
    e = x
check("7 Q73 exp_06: an exception that is not an RLMRunError stops the script, nothing stored",
      isinstance(e, KeyError), f"{type(e).__name__ if e else 'stored as the answer error'}")


def drive1(replies):
    async def go():
        with rc.run(ctx()):
            return await e1._run_rlm("What sample size?", FakeRouter(replies), GEM, "u", max_turns=3,
                                     config_name="rlm_3")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return asyncio.run(go())
    except BaseException as x:   # noqa: BLE001
        return x


g = drive1([KeyError("a slip in our own code")])
check("7 Q73 exp1 _run_rlm: an exception that is not an RLMRunError raises (not stored as gen.error)",
      isinstance(g, BaseException), getattr(g, "error", type(g).__name__))
g = drive1(["prose"] * 3)
check("7 Q73 exp1 _run_rlm still stores an RLMRunError (max_turns_empty) as the answer's error",
      not isinstance(g, BaseException) and g.stop_reason == "max_turns_empty" and (g.error or "").startswith(
          "RLMRunError"), getattr(g, "error", type(g).__name__))
saved_from = RLMContext.__dict__["from_index"]
RLMContext.from_index = staticmethod(_no_index)
try:
    g = drive1(["prose"])
finally:
    RLMContext.from_index = saved_from
check("7 Q73 exp1 _run_rlm: a failed index or reranker load raises (not stored as gen.error)",
      isinstance(g, BaseException) and "reranker did not load" in str(g), getattr(g, "error", type(g).__name__))
# A slip after the run returned, while the record is built: _process_one's `except Exception` would store a plain
# exception as a failed answer, so it must arrive as an RLMStop (one of exp1's STOPS)
saved_with_calls = getattr(e1, "_with_calls")


def _slip(gen, log):
    raise KeyError("misspelt key while building the run record")


e1._with_calls = _slip
try:
    SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
    g = drive1([fin])
finally:
    e1._with_calls = saved_with_calls
check("7 Q73 exp1 _run_rlm: a slip while building the record raises an RLMStop (one of STOPS), not a plain error",
      isinstance(g, getattr(e1, "STOPS", ())) and isinstance(g.__cause__, KeyError), repr(g)[:160])
# exp_03's rlm_10 arm calls exp1's _run_rlm: its RLMStop must pass its `except Exception` (stored, marked done)
m3 = importlib.import_module("exp_03_orchestration_ablation")
src3 = inspect.getsource(m3)
i_setup = src3.find("except SETUP_ERRORS as e:")
i_stop = src3.find("except RLMStop:", i_setup)
i_exc = src3.find("except Exception as e:", i_setup)
check("7 Q73 exp_03 lets exp1's RLMStop end the run (re-raised before `except Exception`), never stored",
      getattr(m3, "RLMStop", None) is getattr(e1, "RLMStop", False) and -1 < i_setup < i_stop < i_exc
      and "raise" in src3[i_stop:i_exc], f"setup {i_setup} stop {i_stop} exception {i_exc}")
for mod in ("exp_01_generation", "exp_02_scaling_factorial"):
    m = importlib.import_module(mod)
    src = inspect.getsource(m)
    check(f"7 Q73 {mod} lets exp1's stops (lock refusals and RLMStop) end the run, never stored as an answer",
          getattr(m, "STOPS", None) is getattr(e1, "STOPS", False) and "RLMStop" in str(getattr(e1, "STOPS", ""))
          and "except STOPS:" in inspect.getsource(m._process_one) and "isinstance(result, STOPS)" in src
          and "isinstance(result, REFUSALS)" not in src)
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
g = drive1([fin])
check("7 Q74 exp1 stores len(passages_seen) as retrieved_passages, the citation count as its own field",
      not isinstance(g, BaseException) and g.retrieved_passages == len(g.rlm["passages_seen"]) == 3
      and g.rlm["citations"] is not None,
      f"retrieved {getattr(g, 'retrieved_passages', None)} seen {len((getattr(g, 'rlm', None) or {}).get('passages_seen') or [])}")

# ═════════════════════════════ 8. round 4 (D78, Q122, Q123, Q125) ═════════════════════════════
# Q122: one empty summary is named in the singular; a refusal with no empty call carries no clause
ONE_EMPTY = ('ch = search_keyword("methods", doc_name="a.pdf")\nr1 = llm_summarize(ch, task="t")\n'
             'r2 = llm_summarize(ch, task="t")\ne = search_keyword("best practices")\nr3 = llm_summarize(e, task="t")\n'
             'add_to_report("Methods", r1["summary"], r1["citations"])\nFINAL_VAR(get_report())')
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([block(ONE_EMPTY)] + ["prose"] * 3, max_turns=4)
msg = router.seen[1][0][-1]["content"]
check("8 Q122 two real and one empty summary: '2 calls ... (1 more was given an empty list of passages and does not "
      "count)'", "INSUFFICIENT ANALYSIS: You have made 2 calls to llm_summarize/llm_query/llm_extract (1 more was given "
      "an empty list of passages and does not count). You need at least 3" in msg, msg[-400:])
res, router, c = run([block(short)] * 4, max_turns=5)
check("8 Q122 no empty call: no clause", "llm_summarize/llm_query/llm_extract. You need at least 3"
      in router.seen[1][0][-1]["content"] and "empty list" not in router.seen[1][0][-1]["content"])

# Q123: the prompt documents llm_query's real default
p = get_rlm_orchestrator_prompt()
check("8 Q123 the prompt documents llm_query(prompt, context_chunks=None), not context_chunks=[]",
      "llm_query(prompt, context_chunks=None) → returns string answer" in p and "context_chunks=[]" not in p
      and inspect.signature(RLMExecutor._sync_llm_query).parameters["context_chunks"].default is None)

# Q125: a search the block's clock stopped as it returned is logged undelivered, its ids kept out of passages_seen
with rc.run(ctx()):
    c, ex = slow_executor(0.6)
    out, _ = ex.execute_code('ch = search_semantic("q")\nprint("after")')
    r = c.retrievals[-1] if c.retrievals else {}
    check("8 Q125 a search stopped by the held firing: logged with delivered False, its ids not in passages_seen",
          "BlockTimeLimit" in (ex.last_error or "") and len(c.retrievals) == 1 and r.get("fn") == "search_semantic"
          and r.get("delivered") is False and len(r.get("ids") or []) == 2 and c.passages_seen == [],
          json.dumps({"retrievals": c.retrievals, "seen": c.passages_seen}))
    c, ex = slow_executor(0.05)
    out, _ = ex.execute_code('ch = search_semantic("q")\nk = search_keyword("methods", doc_name="a.pdf")\n'
                             'print(len(ch))')
    check("8 Q125 a search under the limit, and every other function, is logged delivered True, its ids seen",
          out == "2\n" and [r.get("delivered") for r in c.retrievals] == [True, True]
          and set(c.retrievals[0]["ids"]) <= set(c.passages_seen) and len(c.passages_seen) >= 2,
          json.dumps({"retrievals": c.retrievals, "seen": c.passages_seen}))
    c, ex = slow_executor(0.6)
    ex.execute_code('try:\n    ch = search_semantic("q")\nexcept BaseException:\n    pass\nprint("caught")')
    check("8 Q125 the block's own except does not make the stopped search delivered",
          [r.get("delivered") for r in c.retrievals] == [False] and c.passages_seen == [],
          json.dumps({"retrievals": c.retrievals, "seen": c.passages_seen}))

# ═════════════════════════════ 9. D80 (V4, audit F7; V5, audit F6) ═════════════════════════════
# V4: a root reply that stopped at the output limit runs none of its code blocks; the model is told; the turn counts
check("9 D80 V4 the message after a cut reply, word for word",
      rlm_orch.CUT_REPLY_NOTE == "Your previous reply was cut off by the output limit, so none of its code was run.")
check("9 D80 V4 the adapter returns done_reason 'length' for a length stop (Ollama length, Gemini MAX_TOKENS)",
      la._finish({"status": "length"}) == "length" and la._finish({"status": "ok"}) == "stop"
      and '"length" if sr == "MAX_TOKENS"' in Path(ROOT / "experiments/runner/gemini_client.py").read_text())
RUNAWAY = "".join(block(f'add_to_report("S{k}", "ran", [])\nprint("RAN {k}")') for k in range(1500))
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([(RUNAWAY, "length"), block(WORK + '\nFINAL_VAR(get_report())')], max_turns=3)
hist = router.seen[1][0]
check("9 D80 V4 a cut reply with 1,500 code blocks runs none of them; the answer still finishes",
      isinstance(res, RLMResult) and res.metadata["stop_reason"] == "final"
      and res.metadata["n_code_blocks_run"] == 1 and [s.title for s in c.report_sections] == ["Methods"],
      f"{type(res).__name__} {json.dumps({k: getattr(res, 'metadata', {}).get(k) for k in ('stop_reason', 'n_code_blocks_run')})}")
check("9 D80 V4 the cut reply stays whole in the history, followed by the cut message alone (no block output)",
      hist[-2] == {"role": "assistant", "content": RUNAWAY} and hist[-1] == {"role": "user", "content":
      rlm_orch.CUT_REPLY_NOTE} and not any("RAN " in m["content"] for m in hist if m["role"] == "user"),
      json.dumps([m["role"] for m in hist]))
check("9 D80 V4 the run record counts the length turn, the blocks not run, and the nudge",
      res.metadata["length_turns"] == 1 and res.metadata["length_blocks_not_run"] == 1500
      and {"turn": 1, "kind": "length_cut"} in res.metadata["nudges"],
      json.dumps({k: res.metadata.get(k) for k in ("length_turns", "length_blocks_not_run", "nudges")}))
SUB_REPLIES[:] = []
res, router, c = run([("".join(block(f'print("RAN {k}")') for k in range(3)), "stop"), "prose"], max_turns=2)
check("9 D80 V4 control: the same kind of reply with done_reason stop runs every block, length_turns 0",
      isinstance(res, RLMRunError) and res.metadata["n_code_blocks_run"] == 3 and res.metadata["length_turns"] == 0
      and any("RAN 2" in m["content"] for m in router.seen[1][0] if m["role"] == "user"),
      json.dumps({k: getattr(res, "metadata", {}).get(k) for k in ("n_code_blocks_run", "length_turns")}))
res, router, c = run([("cut prose, no code", "length")] * 2, max_turns=2)
kinds = [n["kind"] for n in res.metadata["nudges"]]
check("9 D80 V4 a cut reply without code is a length turn too, and the end-of-turn checks still run after it",
      res.metadata["length_turns"] == 2 and res.metadata["length_blocks_not_run"] == 0
      and kinds.count("length_cut") == 2 and "emergency" in kinds and "no_code" not in kinds
      and res.metadata["stop_reason"] == "max_turns_empty", str(kinds))

# V5: every search the RLM makes reranks with the one reranker, search_semantic's top_k and the query string the model
# passed. D80 V5 covers RLM retrievals only: the REPL's search_keyword and search_regex are the context's
# rlm_search_keyword and rlm_search_regex; the context's own search_keyword and search_regex stay as before V5 (7c34a1b).
# Every record read below uses .get, so a record missing a field fails its check and the later checks still run.
def last(c, n=1):
    """The last n retrieval records, padded with {} at the front when fewer were written."""
    return ([{}] * n + list(c.retrievals))[-n:]


check("9 D80 V5 the REPL's search_keyword and search_regex take search_semantic's top_k (10); the context's own "
      "search_keyword and search_regex keep the pre-V5 signature (no top_k)",
      rlm_context.SEARCH_TOP_K == 10
      and all(inspect.signature(getattr(RLMContext, f)).parameters["top_k"].default == 10
              for f in ("search_semantic", "rlm_search_keyword", "rlm_search_regex"))
      and all("top_k" not in inspect.signature(getattr(RLMContext, f)).parameters
              for f in ("search_keyword", "search_regex")))
_ns = RLMExecutor(make_context(), None, GEM).namespace
check("9 D80 V5 the REPL exposes rlm_search_keyword and rlm_search_regex under the names search_keyword and "
      "search_regex, and search_semantic as before",
      getattr(_ns["search_keyword"], "__func__", None) is RLMContext.rlm_search_keyword
      and getattr(_ns["search_regex"], "__func__", None) is RLMContext.rlm_search_regex
      and getattr(_ns["search_semantic"], "__func__", None) is RLMContext.search_semantic,
      str({k: getattr(_ns[k], "__name__", "?") for k in ("search_keyword", "search_regex", "search_semantic")}))


def many_context(busy_s=0.0, n=12, counts=None):
    """n chunks of m.pdf, all holding "methods"; k<i> holds it counts[i] times, by default n - i (k00 n times, the last
    once: the keyword order is k00, k01, ...), and each holds "chunk <i>" once (the regex order of r"chunk \\d+" is
    document order). The reranker scores chunk k<i> as i, the reverse of the default keyword order."""
    counts = counts or {i: n - i for i in range(n)}
    c = make_context()
    c._chunks_by_doc["m.pdf"] = [{"id": f"k{i:02d}", "text": "methods " * counts[i] + f"chunk {i}", "chunk_idx": i,
                                  "page": 1, "metadata": {"file_name": "m.pdf"}} for i in range(n)]
    c._documents["m.pdf"] = DocumentInfo(name="m.pdf", file_path="m.pdf", total_chunks=n, total_pages=1)
    by_text = {ch["text"]: int(ch["id"][1:]) for ch in c._chunks_by_doc["m.pdf"]}
    c._reranker = fake_reranker(lambda q, x: float(by_text.get(x, -1)), busy_s)
    return c


def order_context():
    """D80 V5 round 3: 25 chunks of m.pdf whose keyword order is not document order. The last chunk, k24, holds
    "methods" 30 times (first in the search's own order), k01 once (last), every other k<i> 25 - i times: the keyword
    and regex order of "methods" is k24, k00, k02, k03, ..., k23, k01, document order k00, k01, ..., k24. A cap in
    the search's order keeps k24 and drops k01; a cap in document order would keep k01 and drop k24."""
    return many_context(n=25, counts={**{i: 25 - i for i in range(25)}, 24: 30, 1: 1})


def ids_of(hits):
    return [h.chunk_id for h in hits]


def text_of(c, cid):
    return next(ch["text"] for ch in c._chunks_by_doc["m.pdf"] if ch["id"] == cid)


with rc.run(ctx()):
    c = many_context()
    hits = c.rlm_search_keyword("methods", doc_name="m.pdf")
    r, = last(c)
    want = [f"k{i:02d}" for i in range(11, 1, -1)]
    check("9 D80 V5 the RLM's search_keyword: 12 hits come back in the reranker's order, the top 10",
          ids_of(hits) == want and r.get("ids") == want and c.passages_seen == want, str(ids_of(hits)))
    check("9 D80 V5 the RLM's search_keyword reranks against the keyword the model passed, every hit scored once",
          {q for q, _ in c._reranker.model.pairs} == {"methods"} and len(c._reranker.model.pairs) == 12)
    check("9 D80 V5 the record: reranked True, 12 hits, 12 candidates (under the cap of 20), top_k 10, the scores",
          r.get("fn") == "search_keyword" and r.get("reranked") is True and r.get("rerank_skipped", 0) is None
          and r.get("n_hits") == 12 and r.get("n_candidates") == 12 and r.get("candidate_width") == 20
          and r.get("rerank_capped") is False and r.get("top_k") == 10
          and r.get("rerank_scores") == [float(i) for i in range(11, 1, -1)]
          and r.get("query") == "methods" and r.get("delivered") is True, json.dumps(r))
    c = many_context()
    hits = c.rlm_search_regex(r"chunk \d+")
    r, = last(c)
    check("9 D80 V5 the RLM's search_regex reranks against the pattern string, top 10, recorded",
          ids_of(hits) == want and {q for q, _ in c._reranker.model.pairs} == {r"chunk \d+"}
          and r.get("fn") == "search_regex" and r.get("reranked") is True and (r.get("n_candidates") or 0) >= 12,
          json.dumps(r)[:300])

    # (b) the cap: at most FUSED_WIDTH x top_k candidates, the first in the search's own order (keyword count, regex
    # match count), as search_semantic. order_context() tells that order from document order: its late chunk k24 has
    # the highest count, its early chunk k01 the lowest
    from backend.retrieval.retriever import FUSED_WIDTH
    c = order_context()
    hits = c.rlm_search_keyword("methods", doc_name="m.pdf")
    r, = last(c)
    scored = {x for _, x in c._reranker.model.pairs}
    keyword_first20 = ["k24", "k00"] + [f"k{i:02d}" for i in range(2, 20)]
    check("9 D80 V5 cap: the RLM's search_keyword with 25 hits scores only the first FUSED_WIDTH x top_k = 20 in "
          "keyword order (k24, k00, k02..k19): the late highest-count k24 is a candidate, the early lowest-count k01 "
          "(beyond the width in keyword order, inside it in document order) is not",
          FUSED_WIDTH == 2 and scored == {text_of(c, i) for i in keyword_first20}
          and text_of(c, "k24") in scored and text_of(c, "k01") not in scored and len(c._reranker.model.pairs) == 20
          and ids_of(hits) == ["k24"] + [f"k{i:02d}" for i in range(19, 10, -1)], str(ids_of(hits)))
    check("9 D80 V5 cap: the record holds n_hits 25, n_candidates 20, candidate_width 20 and rerank_capped True",
          r.get("n_hits") == 25 and r.get("n_candidates") == 20 and r.get("candidate_width") == 20
          and r.get("rerank_capped") is True and r.get("reranked") is True, json.dumps(r)[:400])
    c = order_context()
    hits = c.rlm_search_regex("methods", doc_name="m.pdf", top_k=3)
    r, = last(c)
    scored = {x for _, x in c._reranker.model.pairs}
    check("9 D80 V5 cap: the RLM's search_regex with top_k 3 scores the first 6 hits in match-count order (k24, k00, "
          "k02..k05; not k01, which document order would keep), returns the top 3 of those, records the cap",
          scored == {text_of(c, i) for i in ("k24", "k00", "k02", "k03", "k04", "k05")}
          and text_of(c, "k01") not in scored and ids_of(hits) == ["k24", "k05", "k04"] and r.get("n_hits") == 25
          and r.get("n_candidates") == 6 and r.get("candidate_width") == 6 and r.get("rerank_capped") is True,
          json.dumps(r)[:400])
    c = order_context()
    author = c.rlm_search_regex("methods|papers by", doc_name="m.pdf")
    r, = last(c)
    check("9 D80 V5 cap: an author query's 25 hits are cut to top_k from the capped candidates in match-count order "
          "(k24, k00, k02..k09), unscored",
          ids_of(author) == ["k24", "k00"] + [f"k{i:02d}" for i in range(2, 10)] and c._reranker.model.pairs == []
          and r.get("rerank_skipped") == "author_query" and r.get("n_candidates") == 20
          and r.get("rerank_capped") is True, json.dumps(r)[:400])

    # (a, round 3) an empty or whitespace-only query is not reranked or capped: every match as before V5, recorded
    # empty_query. The orchestrator's emergency nudge writes search_keyword("", doc_name=...) (orchestrator.py)
    def pre_v5_order(c, key):
        """Every m.pdf chunk in the order the pre-V5 search returns it for a query matching every chunk: score `key`
        descending, a stable sort over document order (Mentori's sorted(..., key=-score))."""
        return [ch["id"] for ch in sorted(c._chunks_by_doc["m.pdf"], key=lambda ch: -key(ch["text"].lower()))]

    for fn, q, key in (("search_keyword", "", lambda t: t.count("")), ("search_keyword", " ", lambda t: t.count(" ")),
                       ("search_regex", "", lambda t: len(t) + 1), ("search_regex", " ", lambda t: t.count(" "))):
        c = order_context()
        got = getattr(c, "rlm_" + fn)(q, doc_name="m.pdf")
        r, = last(c)
        want_all = pre_v5_order(c, key)
        check(f"9 D80 V5 round 3: the RLM's {fn}({q!r}) returns every match (25) in the pre-V5 order, unreranked and "
              "uncapped (more than FUSED_WIDTH x top_k = 20), recorded reranked False, rerank_skipped empty_query",
              ids_of(got) == want_all and len(got) == 25 and c._reranker.model.pairs == []
              and r.get("fn") == fn and r.get("reranked") is False and r.get("rerank_skipped") == "empty_query"
              and r.get("n_hits") == len(want_all) and r.get("n_candidates") == len(want_all)
              and r.get("rerank_capped") is False and r.get("candidate_width", 0) is None
              and r.get("ids") == want_all and r.get("delivered") is True,
              json.dumps({"got": ids_of(got)[:8], "n": len(got), "r": {k: v for k, v in r.items() if k != "ids"}}))
    c = order_context()
    ex = RLMExecutor(c, None, GEM)
    ex.execute_code('chunks = search_keyword("", doc_name="m.pdf")\nprint(len(chunks))')
    r, = last(c)
    check("9 D80 V5 round 3: the emergency nudge's code, search_keyword(\"\", doc_name=X), run in the REPL gets all 25 "
          "chunks of the paper, as before V5",
          ex.last_error is None and len(ex.namespace.get("chunks") or []) == 25 and c._reranker.model.pairs == []
          and r.get("rerank_skipped") == "empty_query" and len(c.passages_seen) == 25,
          json.dumps({"err": ex.last_error, "r": {k: v for k, v in r.items() if k != "ids"}})[:400])

    c = many_context()
    one = c.rlm_search_keyword("Sample size")
    none = c.rlm_search_keyword("zzz-not-there")
    author = c.rlm_search_regex("methods|papers by", doc_name="m.pdf")   # classify_query reads "papers by" as D70's
    r1, r0, ra = last(c, 3)
    check("9 D80 V5 search_semantic's exceptions: one hit, no hit and an author query (D70) are not reranked; the "
          "author query's 12 hits are cut to 10 in the search's own order",
          ids_of(one) == ["a0"] and r1.get("rerank_skipped") == "single_candidate" and r1.get("reranked") is False
          and none == [] and r0.get("rerank_skipped") == "no_candidates" and ra.get("rerank_skipped") == "author_query"
          and ra.get("reranked") is False and ids_of(author) == [f"k{i:02d}" for i in range(10)]
          and c._reranker.model.pairs == [],
          json.dumps([r1, r0, ra])[:300])
    c = make_context()
    ex = RLMExecutor(c, None, GEM)
    ex.execute_code('a = get_chunk("a.pdf", 0)\nb = get_chunks_range("a.pdf", 0, 2)\nd = get_chunks_by_page("a.pdf", 1)\n'
                    'e = search_keyword("methods")\nf = search_regex("salmon")\ng = search_semantic("q")')
    check("9 D80 V5 every retrieval records reranked and rerank_skipped; navigation (no query) is 'navigation'",
          ex.last_error is None and [x.get("fn") for x in c.retrievals] == ["get_chunk", "get_chunks_range",
          "get_chunks_by_page", "search_keyword", "search_regex", "search_semantic"]
          and [x.get("reranked") for x in c.retrievals] == [False, False, False, True, False, True]
          and [x.get("rerank_skipped", 0) for x in c.retrievals] == ["navigation"] * 3 + [None, "single_candidate", None],
          json.dumps([(x.get("fn"), x.get("reranked"), x.get("rerank_skipped")) for x in c.retrievals]))
    # Q72/Q125 hold for the new rerank: a firing during it is held, raised as it returns, the search undelivered
    c = many_context(busy_s=0.6)
    ex = RLMExecutor(c, None, GEM)
    ex.BLOCK_CODE_LIMIT_S = 0.3
    out, _ = ex.execute_code('k = search_keyword("methods", doc_name="m.pdf")\nprint("after")')
    r, = last(c)
    check("9 D80 V5 the keyword rerank runs in the retrieval guard: never interrupted, the firing raised as it "
          "returns, the search logged undelivered", "BlockTimeLimit" in (ex.last_error or "") and "after" not in out
          and c._reranker.model.finished == 1 and c._reranker.model.interrupted == 0 and r.get("delivered") is False
          and r.get("reranked") is True and c.passages_seen == [] and ex.timer_firings
          and ex.timer_firings[-1]["retrieval_s"] >= 0.5, json.dumps({"r": r, "f": ex.timer_firings})[:300])

    # (c) search_semantic's record: the retriever's own reason not to rerank, and a reranked search the Q14 doc
    # filter empties
    class TracedRetriever:
        """retrieve() returns `rows` and appends `rec` to trace, as SimpleRetriever does."""
        def __init__(self, rows, rec):
            self.rows, self.rec = rows, rec

        def retrieve(self, query, collection_name=None, top_k=10, where=None, trace=None):
            if trace is not None:
                trace.append(dict(self.rec))
            return [dict(x) for x in self.rows]

    B = [{"id": f"b{i}", "text": f"salmon text {i}", "score": 0.5, "hybrid_score": 0.5,
          "metadata": {"file_name": "b.pdf", "chunk_index": i, "page": 1}} for i in range(2)]
    c = make_context()
    c._retriever = TracedRetriever(B, {"reranked": False, "rerank_skipped": "author_query"})
    got = c.search_semantic("papers by Smith")
    r, = last(c)
    check("9 D80 V5 search_semantic: when the retriever did not rerank (its trace gives author_query), the record "
          "says reranked False and rerank_skipped author_query", ids_of(got) == ["b0", "b1"]
          and r.get("reranked") is False and r.get("rerank_skipped") == "author_query", json.dumps(r)[:300])
    c = make_context()
    c._retriever = TracedRetriever([{**x, "rerank_score": 0.7 - 0.1 * i} for i, x in enumerate(B)],
                                   {"reranked": True, "rerank_skipped": None})
    got = c.search_semantic("salmon", doc_name="a.pdf")
    r, = last(c)
    check("9 D80 V5 search_semantic: a reranked search the Q14 doc filter empties is recorded as reranked (True, "
          "rerank_skipped None), with outside_filter 2, not as 'no_candidates'",
          got == [] and r.get("outside_filter") == 2 and r.get("reranked") is True
          and r.get("rerank_skipped", 0) is None and r.get("ids") == [], json.dumps(r)[:300])
    c = make_context()
    c._retriever = TracedRetriever([], {"reranked": False, "rerank_skipped": None})
    got = c.search_semantic("nothing")
    r, = last(c)
    check("9 D80 V5 search_semantic: a retriever that returned nothing is recorded as 'no_candidates'",
          got == [] and r.get("reranked") is False and r.get("rerank_skipped") == "no_candidates", json.dumps(r))
    # (e, round 3) a fused result emptied by a Q14 filter before any rerank: the retriever's step 4 labels zero and one
    # candidate alike "single_candidate" (retriever.py:336), and search_semantic records that label
    recs = []
    for rows, doc in (([], "a.pdf"), (B[:1], "a.pdf")):   # the retriever's own filter emptied it; this guard drops one
        c = make_context()
        c._retriever = TracedRetriever(rows, {"reranked": False, "rerank_skipped": "single_candidate"})
        got = c.search_semantic("salmon", doc_name=doc)
        recs.append((got, *last(c)))
    check("9 D80 V5 round 3 search_semantic: a fused result a Q14 filter empties before any rerank is recorded "
          "reranked False, rerank_skipped 'single_candidate' (the retriever's label), outside_filter 0 when the "
          "retriever's filter emptied it and 1 when this guard dropped the single passage",
          [(g, r.get("reranked"), r.get("rerank_skipped"), r.get("outside_filter")) for g, r in recs]
          == [([], False, "single_candidate", 0), ([], False, "single_candidate", 1)],
          json.dumps([r for _, r in recs])[:400])

# (a) the orchestrator tools cross_document_analysis and paper_triage call the context's search_keyword, which returns
# the pre-V5 result: every match in order of the keyword's count, unreranked and uncapped. Each tool runs whole (its
# model calls stubbed); every search_keyword result it received is compared with the pre-V5 RLMContext.search_keyword
# on the same chunks. Round 3 (c): the pre-V5 context.py is read with git show from the pinned commit PRE_V5, never
# from HEAD (which moves with every commit); if it cannot be read (no .git, no git, the commit missing) the checks that
# compare with it fail with the reason and the rest still run
import subprocess  # noqa: E402

PRE_V5 = "7c34a1b"   # a commit before D80 V5 (context.py there is byte-identical to b989806's, the last commit before V5)
PRE_V5_PATH = "experiments/mentori/backend/retrieval/rlm/context.py"
try:
    _pre_src = subprocess.run(["git", "-C", str(ROOT), "show", f"{PRE_V5}:{PRE_V5_PATH}"],
                              capture_output=True, text=True, check=True).stdout
    pre_context = types.ModuleType("pre_v5_rlm_context")
    pre_context.__file__ = f"{PRE_V5}:{PRE_V5_PATH}"
    sys.modules["pre_v5_rlm_context"] = pre_context   # dataclasses resolves the module of its classes by name
    exec(compile(_pre_src, pre_context.__file__, "exec"), pre_context.__dict__)
    pre_error = None
except Exception as e:   # recorded as a FAIL of each check that needs it, never a crash
    pre_context = None
    pre_error = (f"pre-V5 context.py ({PRE_V5}:{PRE_V5_PATH}) unavailable: {type(e).__name__}: {e} "
                 f"{(getattr(e, 'stderr', '') or '').strip()}").strip()


def pre_v5(c):
    """A pre-V5 RLMContext over c's chunks; raises (with the reason) when the pre-V5 code could not be read."""
    if pre_context is None:
        raise RuntimeError(pre_error)
    h = pre_context.RLMContext(index_name="check", user_id="u")
    h._chunks_by_doc, h._documents = c._chunks_by_doc, c._documents
    return h


def tool_context():
    """30 chunks per paper: each holds the words of the task and query, k00 the most often; the reranker ranks the
    last chunk first, so a reranked or capped result would differ from the pre-V5 one."""
    c = make_context()
    words = "flow cytometry protocol methods"
    for doc in ("t1.pdf", "t2.pdf"):
        c._chunks_by_doc[doc] = [{"id": f"{doc[:2]}k{i:02d}", "text": (words + " ") * (30 - i) + f"part {i}",
                                  "chunk_idx": i, "page": 1 + i // 5, "metadata": {"file_name": doc}}
                                 for i in range(30)]
        c._documents[doc] = DocumentInfo(name=doc, file_path=doc, total_chunks=30, total_pages=6)
    for doc in ("a.pdf", "b.pdf"):
        del c._chunks_by_doc[doc], c._documents[doc]
    c.n_chunks_loaded = 60
    c._reranker = fake_reranker(lambda q, x: float(len(x) and -x.count(" ")))
    return c


class ToolRouter:
    """The tools' ModelRouter: chat returns a JSON reply (a relevance score, or an extraction)."""
    async def chat(self, model_identifier, messages, **kw):
        text = messages[-1]["content"]
        r = '{"relevance": 5, "reason": "stub"}' if "Rate the relevance" in text else '{"methods": "stub"}'
        return {"message": {"role": "assistant", "content": r}, "done_reason": "stop"}


def run_tool(name, **kw):
    """Runs rag_tools.<name> on tool_context(), logging each search_keyword call's arguments and the result it got."""
    from backend.mcp.custom import rag_tools
    from backend.agents import model_router
    c, log = tool_context(), []
    orig = c.search_keyword

    def logged(*a, **k):
        out = orig(*a, **k)
        log.append((a, k, list(out)))
        return out
    c.search_keyword = logged

    async def from_index(*a, **k):
        return c
    saved = RLMContext.__dict__["from_index"], model_router.ModelRouter
    RLMContext.from_index, model_router.ModelRouter = staticmethod(from_index), ToolRouter
    try:
        with rc.run(rc.RunContext(run_id="check-rlm-tools", arm="tools", item_id="Q1", draw=1, thinking=None,
                                  base_url="http://127.0.0.1:9", sink=tmp / "sink_tools",
                                  allowed={"gemini-3-flash-preview": "generator"}, agent_roles={"editor": GEM})):
            fn = getattr(rag_tools, name)
            out = asyncio.run(getattr(fn, "__wrapped__", fn)(index_name="check", user_id="u", **kw))
    finally:
        RLMContext.from_index, model_router.ModelRouter = saved
    return c, log, out


def head_results(c, log):
    """The pre-V5 RLMContext.search_keyword (PRE_V5) on the same chunks, for each logged call."""
    h = pre_v5(c)
    return [h.search_keyword(*a, **k) for a, k, _ in log]


def same(got, head):
    key = lambda r: (r.doc_name, r.chunk_idx, r.text, r.page, r.score, r.chunk_id)   # noqa: E731
    return [key(r) for r in got] == [key(r) for r in head]


for tool, kw in (("cross_document_analysis", dict(task="flow cytometry protocol methods")),
                 ("paper_triage", dict(query="flow cytometry protocol methods", top_k=0))):
    try:
        c, log, out = run_tool(tool, **kw)
        heads = head_results(c, log)
        err = None
    except Exception as e:   # a tool that cannot run fails its check; the later checks still run
        c, log, out, heads, err = None, [], "", [], f"{type(e).__name__}: {e}"
    check(f"9 D80 V5 {tool} calls search_keyword and gets the pre-V5 ({PRE_V5}) results (every match in keyword "
          "order, 30 per paper, no rerank, no cap)",
          err is None and len(log) >= 2 and all(len(got) == 30 for _, _, got in log)
          and all(same(got, h) for (_, _, got), h in zip(log, heads)) and c._reranker.model.pairs == []
          and all(r.get("fn") != "search_keyword" or (r.get("reranked") is False
                                                       and r.get("rerank_skipped") == "not_rlm")
                  for r in c.retrievals) and not str(out).startswith("[Error]"),
          err or json.dumps({"calls": len(log), "lens": [len(g) for _, _, g in log],
                             "first": [r.chunk_id for r in (log[0][2] if log else [])][:5],
                             "head": [r.chunk_id for r in (heads[0] if heads else [])][:5],
                             "out": str(out)[:200]}))

# (d, round 3) the context's own search_regex (outside the RLM; D80 V5 covers RLM retrievals only) against the pre-V5
# search_regex (PRE_V5) on the same chunks: the same chunks, order, scores and matches, the same retrieval records plus
# NOT_RLM's two fields, the same passages_seen; an invalid pattern returns [] unlogged in both
REGEX_CASES = (("methods", "m.pdf"), ("methods", None), (r"chunk \d+", None), ("", "m.pdf"), (" ", None),
               ("salmon|sample", None), ("zzz-not-there", None), ("[unclosed", None), ("methods", "missing.pdf"))


def full_key(r):
    return (r.doc_name, r.chunk_idx, r.text, r.page, r.score, r.chunk_id, json.dumps(r.metadata, sort_keys=True))


try:
    c = order_context()
    h = pre_v5(c)
    pairs = [(c.search_regex(p, doc_name=d), h.search_regex(p, doc_name=d)) for p, d in REGEX_CASES]
    err = None
except Exception as e:   # the pre-V5 code unavailable, or the search raising: a FAIL, the run goes on
    c, h, pairs, err = None, None, [], f"{type(e).__name__}: {e}"
not_rlm = rlm_context.NOT_RLM
check(f"9 D80 V5 round 3: the context's own search_regex (outside the RLM) returns the pre-V5 ({PRE_V5}) result on "
      f"{len(REGEX_CASES)} patterns (25 matches in match-count order, uncapped; '' and ' ' matching every chunk; no "
      "match; an invalid pattern, [] unlogged; a missing paper): same chunks, order, scores and matches, the same "
      "records plus reranked False and rerank_skipped not_rlm (and Q150's search_s), the same passages_seen, no "
      "reranker call",
      err is None and len(pairs) == len(REGEX_CASES) and len(pairs[0][0]) == 25 and len(pairs[3][0]) == 25
      and pairs[7] == ([], []) and all([full_key(r) for r in g] == [full_key(r) for r in p] for g, p in pairs)
      and len(h.retrievals) == len(REGEX_CASES) - 1
      and [{k: v for k, v in r.items() if k not in not_rlm and k != "search_s"} for r in c.retrievals] == h.retrievals
      and all(isinstance(r.get("search_s"), float) for r in c.retrievals)   # Q150 (D83): every entry is timed
      and all({k: r.get(k) for k in not_rlm} == not_rlm for r in c.retrievals)
      and c.passages_seen == h.passages_seen and c._reranker.model.pairs == [],
      err or json.dumps({"lens": [(len(g), len(p)) for g, p in pairs], "n_rec": [len(c.retrievals), len(h.retrievals)],
                         "first": [ids_of(g)[:4] for g, _ in pairs[:2]], "pre": [ids_of(p)[:4] for _, p in pairs[:2]]}))

# ═════════════════════════════ 10. D83 Q141 ═════════════════════════════
# add_to_report accepts citations None or a list whose every item is a Citation; anything else saves nothing and
# raises a TypeError naming the bad item, which the code block returns to the model as its output. The failing G1 case
# (rlm_5 and rlm_10, 16_ppr_ethiopia_TE3 draw 3: add_to_report(..., [cite_gifted, cite_age]) with both None) is
# replayed on the code that ran it (PRE_Q141, the Studio's G1 commit; context.py there is HEAD's before Q141) and on
# the fixed code
PRE_Q141 = "11137f9"


def section_state(c):
    return ([(s.title, s.content, list(s.citations), s.order) for s in c.report_sections], set(c.processed_sections))


def refused(c, cits, expect):
    """add_to_report("S", "text", cits) on c: (TypeError raised whose message holds every string in expect, nothing
    saved, get_report() unchanged and working, detail). Never raises, so every case reports."""
    try:
        before, rep0 = section_state(c), c.get_report()
        e = raises(TypeError, lambda: c.add_to_report("S", "text", cits))
        msg = str(e) if e else "no TypeError"
        return (e is not None and all(x in msg for x in expect) and "Nothing was saved" in msg
                and section_state(c) == before and c.get_report() == rep0), msg
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


with rc.run(ctx()):
    c0 = make_context()
    c1, c2 = c0.cite("a.pdf", 1, "Sample size was 24 patients."), c0.cite("b.pdf", 1, "salmon quantification")
    for name, cits, expect in [
            ("[None]", [None], ["citations[0] is None, not a Citation from cite()"]),
            ("[None, None] (the G1 case)", [None, None], ["citations[0] is None, not a Citation from cite()",
                                                          "citations[1] is None, not a Citation from cite()"]),
            ("[cite(...), None]", [c1, None], ["citations[1] is None, not a Citation from cite()"]),
            ("a ChunkResult in the list", [c1, ChunkResult("a.pdf", 0, "t", 1)],
             ["citations[1] is a ChunkResult, not a Citation from cite()"]),
            ("a bare Citation", c1, ["citations is a single Citation, not a list; pass it as [c]"]),
            ("a string", "c1", ["citations is a str, not a list of Citations from cite()"]),
            ("an empty string", "", ["citations is a str, not a list"]),
            ("a tuple of Citations", (c1, c2), ["citations is a tuple, not a list"]),
            ("a dict", {"citations": [c1]}, ["citations is a dict, not a list"])]:
        c = make_context()   # a context of its own per case, holding one section saved first
        c.citations = [c1, c2]
        c.add_to_report("Kept", "a section saved first", [c1])
        ok, msg = refused(c, cits, expect)
        check(f"10 Q141 add_to_report refuses {name}: TypeError naming the bad item, nothing saved, get_report() works",
              ok, msg)
    try:
        e = raises(TypeError, lambda: make_context().add_to_report("S", "text", [c1, None]))
    except Exception as e_:   # the mutant: no TypeError, so nothing to name
        e = None
    check("10 Q141 only the bad item is named ([cite(...), None] names citations[1], not citations[0])",
          e is not None and "citations[0]" not in str(e), str(e))

    c = make_context()
    c1, c2 = c.cite("a.pdf", 1, "Sample size was 24 patients."), c.cite("b.pdf", 1, "salmon quantification")
    lst = [c1, c2]
    errs = [raises(Exception, f) for f in (lambda: c.add_to_report("None", "t0", None),
                                           lambda: c.add_to_report("Empty", "t1", []),
                                           lambda: c.add_to_report("Two", "t2", lst),
                                           lambda: c.add_to_report("Default", "t3"))]
    rep = c.get_report()
    check("10 Q141 the valid cases are unchanged: None, [], a list of Citations and the default are saved as before "
          "(None and [] as [], the list itself kept), and get_report() numbers the Sources",
          errs == [None] * 4 and [s.title for s in c.report_sections] == ["None", "Empty", "Two", "Default"]
          and [s.citations for s in c.report_sections][:2] == [[], []] and c.report_sections[2].citations is lst
          and c.report_sections[3].citations == [] and "[1] a.pdf, page 1" in rep and "[2] b.pdf, page 1" in rep
          and c.processed_sections == {"None", "Empty", "Two", "Default"}, repr(errs) + " " + rep[-200:])

    # the replay: the G1 call on the fixed code saves nothing and get_report() still works; on PRE_Q141's code it was
    # saved and get_report() raised the error the model saw on turns 1 to 4
    c = make_context()
    cite_gifted = None
    cite_age = None
    e = raises(TypeError, lambda: c.add_to_report("Risk Factors for PPR Seropositivity", "content",
                                                  [cite_gifted, cite_age]))
    rep_err = raises(Exception, c.get_report)
    check("10 Q141 replay of the G1 case on the fixed code: add_to_report(..., [None, None]) raises, stores nothing, "
          "and get_report() works",
          e is not None and c.report_sections == [] and c.processed_sections == set() and rep_err is None
          and c.get_report() == "No report content yet.", str(e))
    try:
        _src = subprocess.run(["git", "-C", str(ROOT), "show", f"{PRE_Q141}:{PRE_V5_PATH}"],
                              capture_output=True, text=True, check=True).stdout
        old = types.ModuleType("pre_q141_rlm_context")
        old.__file__ = f"{PRE_Q141}:{PRE_V5_PATH}"
        sys.modules["pre_q141_rlm_context"] = old
        exec(compile(_src, old.__file__, "exec"), old.__dict__)
        h = old.RLMContext(index_name="check", user_id="u")
        h.add_to_report("Risk Factors for PPR Seropositivity", "content", [None, None])
        old_err = raises(Exception, h.get_report)
        detail = f"{type(old_err).__name__}: {old_err}"
        ok = (len(h.report_sections) == 1 and isinstance(old_err, AttributeError)
              and "'NoneType' object has no attribute 'citation_type'" in str(old_err))
    except Exception as ex_:
        ok, detail = False, f"pre-Q141 context.py ({PRE_Q141}) unavailable: {type(ex_).__name__}: {ex_}"
    check(f"10 Q141 the replay on the code that ran G1 ({PRE_Q141}) saved the section and get_report() raised "
          "\"'NoneType' object has no attribute 'citation_type'\" (the failure this fixes)", ok, detail)

    # through the executor: the error is the block's output, as any tool error, and the next block runs
    c = make_context()
    ex = RLMExecutor(c, None, GEM)
    out, res = ex.execute_code('cite_gifted = None\ncite_age = None\n'
                               'add_to_report("Risk", "content", [cite_gifted, cite_age])\nprint("after")')
    check("10 Q141 in a code block the refusal is an ordinary execution error: in last_error and in the output the "
          "model reads, the rest of the block not run, nothing saved",
          ex.last_error is not None and "TypeError: add_to_report: citations[0] is None, not a Citation from cite()"
          in out and "citations[1] is None" in out and "after" not in out and c.report_sections == [], out[:300])
    out, res = ex.execute_code('add_to_report("Risk", "content", [])\nFINAL_VAR(get_report())')
    check("10 Q141 the next block corrects the call, saves the section and sets get_report() as the final answer",
          ex.last_error is None and ex.final_set and ex.final.startswith("## Risk") and len(c.report_sections) == 1,
          repr(ex.last_error))

# the whole loop: turn 1 does the work and makes the G1 call, turn 2 reads the error and saves the section
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([block(WORK + '\ncite_gifted = None\ncite_age = None\n'
                                   'add_to_report("Risk", "content", [cite_gifted, cite_age])'),
                      block('add_to_report("Risk", "content", [])\nFINAL_VAR(get_report())')], max_turns=5)
seen2 = router.seen[1][0][-1]["content"] if len(router.seen) > 1 else ""
check("10 Q141 the RLM loop with the G1 call: the model reads the error naming citations[0] on the next turn and the "
      "run ends with an answer (stop_reason final), not a stop",
      isinstance(res, RLMResult) and res.metadata["stop_reason"] == "final" and res.metadata["code_block_errors"] == 1
      and "citations[0] is None, not a Citation from cite()" in seen2
      and [s.title for s in c.report_sections] == ["Methods", "Risk"],
      f"{type(res).__name__}: {str(res)[:200]} {getattr(res, 'metadata', {}).get('stop_reason')}")

# content is not checked (Q141 fix round review, 17 October): stored G1 answers (rlm_10 12_hpai_netherlands_CO2 d1,
# rlm_20 12_hpai_netherlands_CO2 d1 and CD_004 d3) saved a list or a dict as content after a text section and ended
# normally, so a check would change answers already stored. Pinned: such content is saved as before.
with rc.run(ctx()):
    c0 = make_context()
    c1 = c0.cite("a.pdf", 1, "Sample size was 24 patients.")
    c = make_context()
    c.citations = [c1]
    c.add_to_report("Kept", "a section saved first", [c1])
    errs = [raises(Exception, f) for f in (lambda: c.add_to_report("L", ["a list"], [c1]),
                                           lambda: c.add_to_report("D", {"k": "a dict"}, [c1]))]
    check("10 Q141 content is not checked: a list and a dict after a text section are saved as before (stored G1 "
          "answers did this) and get_report() and the orchestrator's content.strip() over the sections still work",
          errs == [None, None] and [s.title for s in c.report_sections] == ["Kept", "L", "D"]
          and raises(Exception, c.get_report) is None
          and any(s.content.strip() for s in c.report_sections), repr(errs))
    _ctx_src0 = (MENTORI / "backend" / "retrieval" / "rlm" / "context.py").read_text()
    check("10 Q141 context.py has no content check", "_check_report_content" not in _ctx_src0)

    # the O2 residual, pinned as it stands: the list passed is saved itself, so a non-Citation appended to it after
    # the call still reaches get_report() (documented in add_to_report's docstring)
    c = make_context()
    cits = [c1]
    c.add_to_report("S", "t", cits)
    cits.append(None)
    e = raises(Exception, c.get_report)
    check("10 Q141 residual O2 as documented: a None appended to the saved list after the call still fails "
          "get_report() (the list is saved itself, not a copy)",
          isinstance(e, AttributeError) and c.report_sections[0].citations is cits, repr(e))
    _ctx_src = (MENTORI / "backend" / "retrieval" / "rlm" / "context.py").read_text()
    check("10 Q141 the O2 residual is stated in add_to_report's docstring",
          "Residual, left as it is (O2 of the Q141 fix round)" in _ctx_src)

# ═════════════════════════════ 11. D83 Q141 round 2 ═════════════════════════════
# G1 rlm_10 stopped on CD_007, draw 3 (Studio, 17 October 12:21, at 87ad4a0): the model's code ran
#     for citation in star_methods["citations"]:
#         cite("06_star_aligner.pdf", 0, citation)
# so each Citation llm_summarize returned became the quote of a new citation; get_report() lists every corpus
# citation in its Sources list, keyed on (doc_name, page, quote), and raised "unhashable type: 'Citation'" at every
# call, the orchestrator's own at the final answer included (orchestrator.py:426), which stopped the strategy. cite()
# now refuses, inside the sandbox, exactly the arguments get_report() fails on (an unhashable doc_name or page, a
# quote that is not text); add_to_report refuses a corpus Citation built in the code with such fields. Replayed on
# the code that ran it (PRE_Q141B) and on the fixed code.
PRE_Q141B = "87ad4a0"


def load_old_context(commit, name):
    """context.py at commit as a module of its own, or (None, reason)."""
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{PRE_V5_PATH}"],
                             capture_output=True, text=True, check=True).stdout
        mod = types.ModuleType(name)
        mod.__file__ = f"{commit}:{PRE_V5_PATH}"
        sys.modules[name] = mod
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
        return mod, None
    except Exception as e:
        return None, f"context.py at {commit} unavailable: {type(e).__name__}: {e}"


old_b, old_b_err = load_old_context(PRE_Q141B, "pre_q141b_rlm_context")


def old_context():
    """make_context()'s index on PRE_Q141B's RLMContext."""
    h = old_b.RLMContext(index_name="check", user_id="u")
    c = make_context()
    h._chunks_by_doc = copy.deepcopy(c._chunks_by_doc)
    h._documents = {k: old_b.DocumentInfo(**dataclasses.asdict(v)) for k, v in c._documents.items()}
    h.n_chunks_loaded, h._retriever, h._reranker = c.n_chunks_loaded, c._retriever, c._reranker
    return h


def with_section(c, doc_name, page, quote):
    """cite(doc_name, page, quote) after a section is saved, then get_report(): (cite error, report or the error
    get_report raised, citations_record)."""
    c.add_to_report("Kept", "a section saved first", [])
    e = raises(Exception, lambda: c.cite(doc_name, page, quote))
    try:
        rep = c.get_report()
    except Exception as ex_:
        rep = ex_
    return e, rep, c.citations_record()


class StrSub(str):
    pass


with rc.run(ctx()):
    # the CD_007 call, at context level: a Citation from llm_summarize passed as cite()'s quote
    c = make_context()
    star = {"citations": [c.cite("a.pdf", 1, "Sample size was 24 patients."), c.cite("b.pdf", 1, "salmon quantification")]}
    c.add_to_report("STAR Aligner Mapping", "summary", star["citations"])
    n0, rep0 = len(c.citations), c.get_report()
    e = raises(TypeError, lambda: [c.cite("06_star_aligner.pdf", 0, citation) for citation in star["citations"]])
    check("11 Q141b replay of the CD_007 call on the fixed code: cite(doc, 0, <Citation>) raises a TypeError naming the "
          "quote as a Citation (with the hint), cites nothing, and get_report() is unchanged and works",
          e is not None and "cite: quote is a Citation, not the quoted text (give a str)" in str(e)
          and "llm_summarize has already cited its chunks" in str(e) and "Nothing was cited." in str(e)
          and len(c.citations) == n0 and c.get_report() == rep0, str(e))
    if old_b is not None:
        h = old_context()
        hs = {"citations": [h.cite("a.pdf", 1, "Sample size was 24 patients."), h.cite("b.pdf", 1, "salmon quantification")]}
        h.add_to_report("STAR Aligner Mapping", "summary", hs["citations"])
        for citation in hs["citations"]:
            h.cite("06_star_aligner.pdf", 0, citation)
        old_err = raises(Exception, h.get_report)
        ok, detail = (len(h.citations) == 4 and isinstance(old_err, TypeError)
                      and "unhashable type: 'Citation'" in str(old_err)), f"{type(old_err).__name__}: {old_err}"
    else:
        ok, detail = False, old_b_err
    check(f"11 Q141b the same call on the code that ran G1 rlm_10 ({PRE_Q141B}) kept both citations and get_report() "
          "raised \"unhashable type: 'Citation'\" (the stop this fixes)", ok, detail)

    # each refused type: refused on the fixed code (named, nothing cited, get_report() works), and on PRE_Q141B's
    # code cited and then failing get_report() once a section is saved (so only what crashes is refused). An
    # unhashable doc_name reaches the check only with a quote that is empty after whitespace is collapsed (else the
    # document lookup raises, as before: pinned below), so its cases quote " "
    cit0 = make_context().cite("a.pdf", 1, "Sample size was 24 patients.")
    REFUSED = [("quote", "a Citation", cit0), ("quote", "a list", ["Sample size"]), ("quote", "a dict", {"q": "x"}),
               ("quote", "a set", {"x"}), ("quote", "None", None), ("quote", "an int", 24), ("quote", "a float", 2.2),
               ("quote", "a tuple", ("x",)), ("quote", "a bytes", b"x"), ("quote", "a bool", True),
               ("doc_name", "a list", ["a.pdf"]), ("doc_name", "a dict", {"a": 1}), ("doc_name", "a set", {"a.pdf"}),
               ("doc_name", "a Citation", cit0), ("page", "a list", [1]), ("page", "a dict", {"p": 1}),
               ("page", "a set", {1}), ("page", "a Citation", cit0)]
    for arg, what, v in REFUSED:
        args = {"doc_name": "a.pdf", "page": 1, "quote": " " if arg == "doc_name" else "Sample size was 24 patients.",
                arg: v}
        c = make_context()
        e, rep, rec = with_section(c, args["doc_name"], args["page"], args["quote"])
        new_ok = (isinstance(e, TypeError) and f"cite: {arg} is {what}" in str(e) and "Nothing was cited." in str(e)
                  and rec == [] and isinstance(rep, str) and rep.startswith("## Kept"))
        if old_b is not None:
            oe, orep, _ = with_section(old_context(), args["doc_name"], args["page"], args["quote"])
            old_ok, odetail = oe is None and isinstance(orep, Exception), f"old: {type(orep).__name__}: {orep}"
        else:
            old_ok, odetail = False, old_b_err
        check(f"11 Q141b cite() refuses {arg} as {what}: TypeError naming it, nothing cited, get_report() works; on "
              f"{PRE_Q141B} it was cited and get_report() failed", new_ok and old_ok, f"new: {e}; {odetail}")

    e = raises(TypeError, lambda: make_context().cite("a.pdf", [1], None))
    e2 = raises(TypeError, lambda: make_context().cite(["a.pdf"], {"p": 1}, ""))
    check("11 Q141b every bad argument is named in one error (page and quote; doc_name and page)",
          e is not None and all(x in str(e) for x in ("page is a list", "quote is None"))
          and e2 is not None and all(x in str(e2) for x in ("doc_name is a list", "page is a dict")), f"{e} | {e2}")

    # an unhashable doc_name with a quote: the document lookup raises as on PRE_Q141B, the same error (what the model
    # read in any stored answer that did this), nothing cited, the new check never reached
    for what, d in (("a list", ["a.pdf"]), ("a Citation", cit0)):
        c = make_context()
        e = raises(Exception, lambda: c.cite(d, 1, cit0 if what == "a Citation" else "Sample size"))
        if old_b is not None:
            h = old_context()
            oe = raises(Exception, lambda: h.cite(d, 1, cit0 if what == "a Citation" else "Sample size"))
            ok = (type(e) is type(oe) is TypeError and str(e) == str(oe) and str(e).startswith("unhashable type")
                  and c.citations == [] and h.citations == [])
            detail = f"new {e!r}, old {oe!r}"
        else:
            ok, detail = False, old_b_err
        check(f"11 Q141b cite() with doc_name {what} and a quote fails at the document lookup with the same error as on "
              f"{PRE_Q141B} (not the new message), nothing cited", ok, detail)

    # the allowed types: cited and reported exactly as on PRE_Q141B's code (record and report text equal)
    ALLOWED = [("an int page", "a.pdf", 1, "Sample size was 24 patients."), ("page None", "a.pdf", None, "x"),
               ("a str page", "a.pdf", "1", "x"), ("a float page", "a.pdf", 1.0, "x"),
               ("a tuple page", "a.pdf", (1, 2), "x"), ("a bool page", "a.pdf", True, "x"),
               ("doc_name None", None, 1, "x"), ("an int doc_name", 3, 1, "x"),
               ("a tuple doc_name", ("a.pdf",), 1, "x"), ("an empty quote", "a.pdf", 1, ""),
               ("a str subclass quote", "a.pdf", 1, StrSub("Sample size was 24 patients.")),
               ("an unknown paper", "z.pdf", 1, "x"), ("a quote with newlines", "b.pdf", 1, "salmon\nquantification")]
    for what, d, p, q in ALLOWED:
        e, rep, rec = with_section(make_context(), d, p, q)
        if old_b is not None:
            oe, orep, orec = with_section(old_context(), d, p, q)
            ok = e is None and oe is None and isinstance(rep, str) and rep == orep and rec == orec and len(rec) == 1
            detail = f"{e!r} {oe!r} {rep[-120:] if isinstance(rep, str) else rep!r}"
        else:
            ok, detail = False, old_b_err
        check(f"11 Q141b cite() accepts {what} as before: the same citation record and the same report as on "
              f"{PRE_Q141B}", ok, detail)

    # the one case where a refused quote did not fail get_report(): no section ever saved (get_report() returns before
    # the Sources list). The scan of every stored G1 RLM answer found no such cite() (every recorded quote is a str)
    if old_b is not None:
        h = old_context()
        h.cite("a.pdf", 0, h.cite("a.pdf", 1, "Sample size was 24 patients."))
        ok = h.get_report() == "No report content yet."
    else:
        ok = False
    check(f"11 Q141b pinned: on {PRE_Q141B} a Citation quote with no section saved left get_report() working ('No "
          "report content yet.'); the fixed cite() refuses it all the same (the stored-answer scan found none)",
          ok and raises(TypeError, lambda: make_context().cite("a.pdf", 0, cit0)) is not None)

    # add_to_report: a corpus Citation built in the code with fields get_report() cannot use
    C = rlm_context.Citation
    good = C("a.pdf", 1, 0, "Sample size was 24 patients.")
    for name, cits, expect in [
            ("a quote list", [C("a.pdf", 1, 0, ["x"])], "citations[0].quote is a list, not the quoted text"),
            ("a doc_name list", [C(["a.pdf"], 1, 0, "x")], "citations[0].doc_name is a list"),
            ("a dict page after a good one", [good, C("a.pdf", {"p": 1}, 0, "x")], "citations[1].page is a dict"),
            ("a Citation quote", [C("a.pdf", 1, 0, good)], "citations[0].quote is a Citation")]:
        c = make_context()
        c.add_to_report("Kept", "a section saved first", [])
        ok, msg = refused(c, cits, [expect])
        check(f"11 Q141b add_to_report refuses a Citation built with {name}: TypeError naming the field, nothing saved, "
              "get_report() works", ok and (cits[0] is not good or "citations[0]" not in msg), msg)
    c = make_context()
    intra = C("a.pdf", 1, 0, None, citation_type=rlm_context.CitationType.INTRA_DOCUMENT, intra_ref_text="(X, 2020)")
    errs = [raises(Exception, lambda: c.add_to_report("Good", "t", [good])),
            raises(Exception, lambda: c.add_to_report("Intra", "t", [intra]))]
    rep = c.get_report()
    check("11 Q141b add_to_report accepts a well-formed Citation built in the code (listed in the Sources) and an "
          "intra-document Citation with any quote (get_report() never reads it)",
          errs == [None, None] and "[1] a.pdf, page 1: \"Sample size was 24 patients....\"" in rep
          and len(c.report_sections) == 2, f"{errs!r} {rep[-200:]}")
    if old_b is not None:
        h = old_context()
        h.add_to_report("S", "t", [old_b.Citation("a.pdf", 1, 0, ["x"])])
        ok = isinstance(raises(Exception, h.get_report), TypeError)
    else:
        ok = False
    check(f"11 Q141b on {PRE_Q141B} such a Citation was saved and get_report() failed (what the refusal prevents)", ok)

    # the refusal mirrors get_report(): the same key and the same preview expression in both
    _src11 = (MENTORI / "backend" / "retrieval" / "rlm" / "context.py").read_text()
    try:
        _gr, _sp, _ci = (inspect.getsource(f) for f in (RLMContext.get_report, rlm_context._sources_problems,
                                                         RLMContext.cite))
    except Exception as ex_:   # a replaced function has no source: a FAIL, never a crash
        _gr = _sp = _ci = f"{type(ex_).__name__}: {ex_}"
    check("11 Q141b _sources_problems tries get_report()'s own operations: the key (doc_name, page, quote) hashed, "
          "the quote previewed with quote[:SOURCES_PREVIEW_CHARS].replace(\"\\n\", \" \")",
          "key = (cit.doc_name, cit.page, cit.quote)" in _gr and "if key in seen:" in _gr
          and 'cit.quote[:SOURCES_PREVIEW_CHARS].replace("\\n", " ")' in _gr
          and 'quote[:SOURCES_PREVIEW_CHARS].replace("\\n", " ")' in _sp and "hash(v)" in _sp and "hash(quote)" in _sp
          and "problems = _sources_problems(doc_name, page, quote)" in _ci, _sp[:200])

    # through the executor: the CD_007 block as the model wrote it; the refusal is the block's output
    SUB_REPLIES[:] = [SUMMARY_REPLY]
    c = make_context()
    ex = RLMExecutor(c, None, GEM)
    out, res = ex.execute_code(
        'ch = search_keyword("methods", doc_name="a.pdf")\n'
        'star_methods = llm_summarize(ch, task="Identify technical challenges STAR addresses")\n'
        'for citation in star_methods["citations"]:\n'
        '    cite("06_star_aligner.pdf", 0, citation) # No page info available, using 0\n'
        'add_to_report("STAR Aligner Mapping", star_methods["summary"], star_methods["citations"])\n'
        'print("Initial summaries added to report.")')
    check("11 Q141b in a code block (the CD_007 block) the refusal is an ordinary execution error: in last_error and "
          "in the output the model reads, the rest of the block not run, only llm_summarize's own citations kept",
          ex.last_error is not None and "TypeError: cite: quote is a Citation, not the quoted text" in out
          and "Initial summaries added to report." not in out and c.report_sections == []
          and len(c.citations) == 2 and all(isinstance(x.quote, str) for x in c.citations), out[-400:])
    out, res = ex.execute_code('add_to_report("STAR Aligner Mapping", star_methods["summary"], '
                               'star_methods["citations"])\nFINAL_VAR(get_report())')
    check("11 Q141b the next block saves the section with llm_summarize's citations and sets get_report() as the final "
          "answer, its Sources numbered",
          ex.last_error is None and ex.final_set and ex.final.startswith("## STAR Aligner Mapping")
          and "[1] a.pdf, page 1" in ex.final, repr(ex.last_error))

# the whole loop, the same replies on both codes: turn 1 does the work and makes the CD_007 calls (on a list holding a
# cite() of its own first, since llm_summarize on PRE_Q141B's context makes no citation: the executor's
# isinstance(chunk, ChunkResult) tests the fixed module's class), turn 2 gives a
# final answer. Fixed code: the model reads the refusal and the run ends with an answer. PRE_Q141B: the orchestrator's
# get_report() at the final answer raises outside the sandbox (orchestrator.py:426), the stop of G1 rlm_10
CD007 = [block(WORK + '\ncits = [cite("a.pdf", 1, "Sample size was 24 patients.")] + r1["citations"]\n'
                      'for citation in cits:\n    cite("06_star_aligner.pdf", 0, citation)'),
         block('FINAL("STAR maps spliced reads; Salmon quantifies with bias models.")')]
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run(list(CD007), max_turns=5)
seen2 = router.seen[1][0][-1]["content"] if len(router.seen) > 1 else ""
check("11 Q141b the RLM loop with the CD_007 calls on the fixed code: the model reads the error naming the quote on "
      "the next turn and the run ends with an answer (stop_reason final), not a stop",
      isinstance(res, RLMResult) and res.metadata["stop_reason"] == "final" and res.metadata["code_block_errors"] == 1
      and "cite: quote is a Citation, not the quoted text" in seen2 and [s.title for s in c.report_sections] == ["Methods"],
      f"{type(res).__name__}: {str(res)[:200]} {getattr(res, 'metadata', {}).get('stop_reason')}")
if old_b is not None:
    SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
    res_o, router_o, h = run(list(CD007), max_turns=5, context=old_context())
    ok = isinstance(res_o, TypeError) and "unhashable type: 'Citation'" in str(res_o) and len(router_o.seen) == 2
    detail = f"{type(res_o).__name__}: {str(res_o)[:200]}"
else:
    ok, detail = False, old_b_err
check(f"11 Q141b the same loop on {PRE_Q141B}'s context: turn 1 runs without error, and the final answer on turn 2 "
      "raises \"unhashable type: 'Citation'\" out of the run (the G1 rlm_10 stop)", ok, detail)

# residuals, pinned as they stand and as cite()'s docstring states them
with rc.run(ctx()):
    c = make_context()
    c.add_to_report("S", "t", [])
    x = c.cite("a.pdf", 1, "Sample size was 24 patients.")
    x.quote = ["changed after"]
    e1 = raises(Exception, c.get_report)
    c = make_context()
    c.add_to_report("S", "t", [])
    c.get_citations().append(None)
    e2 = raises(Exception, c.get_report)
    check("11 Q141b residual as documented: a Citation changed after cite() (c.quote = a list) and a None appended to "
          "get_citations() still fail get_report(); cite()'s docstring states both",
          isinstance(e1, TypeError) and isinstance(e2, AttributeError)
          and "Residual, left as it is: a Citation changed after it is made" in inspect.getsource(RLMContext.cite),
          f"{e1!r} {e2!r}")

# Q141 round 2 review D2: mixed page types in one document no longer stop auto_generate_report_from_citations
# (sorted with _page_order); with int pages only, the order is sorted()'s
from backend.retrieval.rlm.context import Citation as _Cit, _page_order as _po
with rc.run(ctx()):
    c = make_context()
    c.citations = [_Cit("a.pdf", p, "q%s" % i, 0) for i, p in enumerate([3, None, 1, "2"])]
    e = raises(Exception, c.auto_generate_report_from_citations)
    _ints = [(5, 1), (2, 1), (9, 1), (0, 1)]
    check("11 Q141 round 2 D2: None, a str and int pages in one document: auto_generate_report_from_citations works, "
          "int pages first in order; int pages alone keep sorted()'s order",
          e is None and sorted(_ints, key=_po) == sorted(_ints), repr(e))

# ═════════════════════════════ 12. D92 Q184 ═════════════════════════════
# The final check reads each report section as str(content), as get_report() prints it (audit F1). A section whose
# content is a list, a dict, None or a number, saved alone, no longer stops the run at the final answer. The same list
# run on the orchestrator before Q184 (PRE_Q184, read with git show, never HEAD) pins the fault it fixes. The old and
# new line give the same value on every sequence of sections where the old line did not raise (exhaustive below), so
# a stored answer, made only on runs where it did not raise, cannot change.
PRE_Q184 = "09f02b8"   # the last commit before Q184; orchestrator.py there is 7c868d8's
PRE_Q184_PATH = "experiments/mentori/backend/retrieval/rlm/orchestrator.py"
try:
    _src184 = subprocess.run(["git", "-C", str(ROOT), "show", f"{PRE_Q184}:{PRE_Q184_PATH}"],
                             capture_output=True, text=True, check=True).stdout
    pre_orch = types.ModuleType("backend.retrieval.rlm._orchestrator_pre_q184")
    pre_orch.__file__, pre_orch.__package__ = f"{PRE_Q184}:{PRE_Q184_PATH}", "backend.retrieval.rlm"
    sys.modules[pre_orch.__name__] = pre_orch
    exec(compile(_src184, pre_orch.__file__, "exec"), pre_orch.__dict__)
    pre184_error = None
except Exception as e:   # a FAIL of the checks that need it, never a crash
    pre_orch, pre184_error = None, f"{PRE_Q184}:{PRE_Q184_PATH} unavailable: {type(e).__name__}: {e}"


def run_with(orch_cls, replies, max_turns=5):
    """run() with another orchestrator class (the pre-Q184 one)."""
    context = make_context()
    router = FakeRouter(replies)
    orch = orch_cls(router, GEM, max_turns=max_turns, verify=False)

    async def go():
        with rc.run(ctx()):
            try:
                return await orch.run("What sample size did the study use?", context)
            except Exception as e:
                return e
    with contextlib.redirect_stdout(io.StringIO()):
        return asyncio.run(go()), router, context


WORK_NO_REPORT = ('ch = search_keyword("methods", doc_name="a.pdf")\n'
                  'r1 = llm_summarize(ch, task="t")\nr2 = llm_summarize(ch, task="t")\n'
                  'r3 = llm_summarize(ch, task="t")\n')
_src_now = (MENTORI / "backend" / "retrieval" / "rlm" / "orchestrator.py").read_text()
check("12 Q184 the final check reads str(content) (and the verbose count len(str(content))); no s.content.strip() "
      "or len(s.content) is left",
      "any(str(s.content).strip() for s in context.report_sections)" in _src_now
      and "len(str(s.content))" in _src_now and "s.content.strip()" not in _src_now
      and "len(s.content)" not in _src_now)

for label, content_src, shown in (("a list", '["gene A", "gene B"]', "['gene A', 'gene B']"),
                                  ("a dict", '{"gene": "A"}', "{'gene': 'A'}"),
                                  ("an empty list", '[]', "[]")):
    SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
    res, router, c = run([block(WORK_NO_REPORT + f'add_to_report("Genes", {content_src})\nFINAL_VAR(get_report())')])
    check(f"12 Q184 {label} saved as the only section, then FINAL_VAR(get_report()): the run ends with the report as "
          "the answer (stop_reason final), the section printed as str(content)",
          isinstance(res, RLMResult) and res.metadata["stop_reason"] == "final" and f"## Genes\n\n{shown}\n" in str(res),
          f"{type(res).__name__}: {str(res)[:160]!r}")

# None and a number: add_to_report saves the section, then its log line's len(content) raises TypeError into the
# block (as the submitted add_to_report did); the next turn's FINAL_VAR(get_report()) ends the run
for label, content_src, shown in (("None", "None", "None"), ("a number", "5", "5")):
    SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
    res, router, c = run([block(WORK_NO_REPORT + f'add_to_report("Count", {content_src})'),
                          block('FINAL_VAR(get_report())')])
    check(f"12 Q184 {label} as content: saved, the block's error is add_to_report's TypeError (submitted behaviour), "
          "and the next turn's FINAL_VAR(get_report()) ends the run with the section printed",
          isinstance(res, RLMResult) and res.metadata["stop_reason"] == "final"
          and res.metadata["code_block_errors"] == 1 and f"## Count\n\n{shown}\n" in str(res)
          and len(c.report_sections) == 1,
          f"{type(res).__name__}: {str(res)[:160]!r}")

# the fault, on the code before Q184: the list case stops the whole run with the AttributeError
if pre_orch is None:
    check("12 Q184 the list case on the pre-Q184 orchestrator", False, pre184_error)
else:
    SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
    res, router, c = run_with(pre_orch.RLMOrchestrator,
                              [block(WORK_NO_REPORT + 'add_to_report("Genes", ["gene A", "gene B"])\n'
                                                      'FINAL_VAR(get_report())')])
    check(f"12 Q184 the same list on the orchestrator at {PRE_Q184} (before Q184): the run stops with "
          "AttributeError 'list' object has no attribute 'strip' (audit F1), no answer",
          isinstance(res, AttributeError) and "'list' object has no attribute 'strip'" in str(res), repr(res)[:200])

# exhaustive: every sequence of 1 to 3 sections over these contents; wherever the old line returns, the new returns
# the same value, except where a blank bytes section is read: the old line read bytes with bytes.strip() (b"" empty),
# the new reads its printed text "b''" (not empty), so old False and new True there and nowhere else; the old line
# raises exactly when a section with no strip (not str, not bytes) comes before the first section with text
import itertools  # noqa: E402
_contents = ["", "  ", "text", ["a"], [], {"k": 1}, None, 5, b"", b"text"]
_same = _raised = _total = _bytes = 0
_bad = []
for n in (1, 2, 3):
    for seq in itertools.product(_contents, repeat=n):
        secs = [ReportSection(title=f"s{i}", content=x, citations=[], order=i) for i, x in enumerate(seq)]
        _total += 1
        try:
            old = any(s.content.strip() for s in secs)
        except AttributeError:
            _raised += 1
            first_text = next((i for i, x in enumerate(seq) if isinstance(x, (str, bytes)) and x.strip()), len(seq))
            if all(isinstance(x, (str, bytes)) for x in seq[:first_text]):
                _bad.append(("raised with only str or bytes before the first text section", seq))
            continue
        new = any(str(s.content).strip() for s in secs)
        _same += old == new
        if old != new:
            if old is False and new is True and b"" in seq:
                _bytes += 1
            else:
                _bad.append((old, new, seq))
check(f"12 Q184 old and new final check agree on every sequence where the old one returned ({_same} of "
      f"{_total - _raised}) except the {_bytes} where a blank bytes section (b\"\") is read: old empty, new its printed "
      f"text b''; {_raised} of {_total} sequences raised on the old line, each with a section that has no strip "
      "before the first section with text)", not _bad and _bytes > 0 and _same + _bytes == _total - _raised,
      repr(_bad[:3]))

# ═════════════════════════════ 13. D240 (G17): search off cannot be turned back on ═════════════════════════════
# Review M1 of 89d0b958: the REPL could set context.search_tools = True. remove_search_tools now latches: a write or a
# delete of search_tools, _retriever, _reranker, _vector_store (or the latch) is a logged, refused search attempt
from backend.retrieval.rlm.context import SearchToolRemoved, SEARCH_LOCKED_ATTRS  # noqa: E402

with rc.run(ctx()):
    c = make_context()
    c.search_tools = False
    c.search_tools = True
    c._retriever = FakeRetriever()
    ex = RLMExecutor(c, None, GEM)
    out, _ = ex.execute_code('r = search_keyword("methods", doc_name="a.pdf")\nprint(len(r))')
    check("13 D240 default (search on): the attributes are plain (set False then True), searches run, no attempt "
          "logged", ex.last_error is None and out.strip() not in ("", "0") and c.search_attempts == []
          and not c.__dict__.get("_search_removed", False), f"{out!r} {ex.last_error} {c.search_attempts}")

    c = make_context()
    c.remove_search_tools()
    ex = RLMExecutor(c, None, GEM)
    out, _ = ex.execute_code("context.search_tools = True")
    check("13 D240 M1 the REPL's `context.search_tools = True` fails as SearchToolRemoved and search stays off",
          "SearchToolRemoved" in (ex.last_error or "") and c.search_tools is False,
          f"{(ex.last_error or '')[:80]!r} {c.search_tools}")
    check("13 D240 M1 the write is logged as a search attempt (via context.search_tools)",
          c.search_attempts[-1:] == [{"turn": c.current_turn, "fn": "search_tools =", "via": "context.search_tools"}],
          str(c.search_attempts))
    out, _ = ex.execute_code('r = context.search_keyword("methods", doc_name="a.pdf")')
    check("13 D240 M1 after the refused write, a search through the context is still refused",
          "SearchToolRemoved" in (ex.last_error or "") and c.search_attempts[-1]["fn"] == "search_keyword")
    ex.execute_code("del context.search_tools")
    check("13 D240 M1 `del context.search_tools` (which would read the class default True) is refused",
          "SearchToolRemoved" in (ex.last_error or "") and c.__dict__.get("search_tools") is False
          and c.search_attempts[-1]["fn"] == "del search_tools", f"{(ex.last_error or '')[:80]!r}")
    for attr in ("_retriever", "_reranker", "_vector_store", "_search_removed"):
        ex.execute_code(f"context.{attr} = None")
        check(f"13 D240 M1 `context.{attr} = None` is refused and logged",
              "SearchToolRemoved" in (ex.last_error or "") and c.search_attempts[-1]["fn"] == f"{attr} ="
              and c.__dict__.get("_search_removed") is True and type(getattr(c, attr, None)).__name__ != "NoneType",
              f"{(ex.last_error or '')[:80]!r} {c.search_attempts[-1:]}")
    ex.execute_code('object.__setattr__(context, "search_tools", True)\nr = context.rlm_search_keyword("methods")')
    check("13 D240 M1 even a raw object.__setattr__ of search_tools leaves search refused (the latch is read too)",
          "SearchToolRemoved" in (ex.last_error or "") and c.search_attempts[-1]["fn"] == "search_keyword",
          f"{(ex.last_error or '')[:80]!r} {c.search_attempts[-1:]}")
    object.__setattr__(c, "search_tools", False)
    n0 = len(c.search_attempts)
    c.remove_search_tools()
    check("13 D240 a second remove_search_tools is a no-op (nothing refused, nothing logged)",
          len(c.search_attempts) == n0 and c.search_tools is False)
    out, _ = ex.execute_code('print(get_chunk("a.pdf", 0)[:6])\nc2 = get_chunks_range("a.pdf", 0, 2)\nprint(len(c2))')
    check("13 D240 navigation reads still work after the refused writes", ex.last_error is None and "Sample" in out,
          f"{out!r} {(ex.last_error or '')[:80]!r}")
    check("13 D240 the locked attributes are the four of the removal plus the latch",
          SEARCH_LOCKED_ATTRS == {"search_tools", "_retriever", "_reranker", "_vector_store", "_search_removed"})


def run_off(replies, max_turns=5):
    """One RLM run with RLMOrchestrator(search_tools=False) on the stubs: (result or exception, router, context)."""
    context = make_context()
    router = FakeRouter(replies)
    orch = RLMOrchestrator(router, GEM, max_turns=max_turns, search_tools=False)

    async def go():
        with rc.run(ctx()):
            try:
                return await orch.run("What sample size did the study use?", context)
            except Exception as e:
                return e
    with contextlib.redirect_stdout(io.StringIO()):
        return asyncio.run(go()), router, context


NAV_WORK = ('ch = get_chunks_range("a.pdf", 0, 2)\n'
            'r1 = llm_summarize(ch, task="t")\nr2 = llm_summarize(ch, task="t")\nr3 = llm_summarize(ch, task="t")\n'
            'add_to_report("Methods", r1["summary"], r1["citations"])')
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run_off([block("context.search_tools = True\n") + block('r = search_keyword("methods")'),
                          block(NAV_WORK) + block("FINAL_VAR(get_report())")])
md = getattr(res, "metadata", {}) or {}
st = md.get("search_tools") or {}
fns = [a["fn"] for a in st.get("attempts", [])]
check("13 D240 M1 an off run where the REPL sets context.search_tools = True and then searches: both refused, both "
      "in the record's attempts, no search retrieval, the run still answers",
      isinstance(res, RLMResult) and st.get("on") is False and fns == ["search_tools =", "search_keyword"]
      and st.get("n_attempts") == 2 and c.search_tools is False
      and not [x for x in md.get("retrievals", []) if x.get("fn") in rlm_context.SEARCH_FUNCTIONS],
      f"{type(res).__name__} {fns} {md.get('stop_reason')}")
res, router, c = run([block(WORK) + block("FINAL_VAR(get_report())")])
check("13 D240 a default run (search on) has no search_tools key and no latch", isinstance(res, RLMResult)
      and "search_tools" not in res.metadata and not c.__dict__.get("_search_removed", False))

# ═════════════════ 14. a range passed by the model's code is recorded as a list (G19 B, 5 Nov) ═════════════════
# G19 arm B (gemma3:27b rlm_10_nosearch) on CD_014: the code called get_chunks_by_page(target_brucellosis,
# range(1, 6)). _seen logged page=range(1, 6) in context.retrievals, the answer record could not be written
# (run_context._dumps: "Object of type range is not JSON serializable") and the run stopped after 33 of 46 answers.
c = make_context()
ex = RLMExecutor(c, None, GEM)
with rc.run(ctx()):
    ex.execute_code('p = get_chunks_by_page("a.pdf", range(1, 3))\nk = search_keyword("methods", doc_name=range(2))\n'
                    'q = cite("a.pdf", range(1, 3), "Sample size was 24 patients.")\n'
                    'n = get_chunks_by_page("a.pdf", 1)')
check("14 a range argument of a logged call is recorded as its list; an int page as before",
      ex.last_error is None and [x["fn"] for x in c.retrievals] == ["get_chunks_by_page", "search_keyword",
                                                                    "get_chunks_by_page"]
      and c.retrievals[0]["page"] == [1, 2] and c.retrievals[1]["doc_name"] == [0, 1] and c.retrievals[-1]["page"] == 1
      and c.retrievals[-1]["ids"] == ["a0", "a1"],
      f"{ex.last_error} {[(x['fn'], x.get('page'), x.get('doc_name'), x['ids']) for x in c.retrievals]}")
check("14 a range page given to cite() is recorded as its list in citations_record",
      [r["page"] for r in c.citations_record()] == [[1, 2]], repr(c.citations_record()))
SUB_REPLIES[:] = [SUMMARY_REPLY] * 3
res, router, c = run([block('p = get_chunks_by_page("a.pdf", range(1, 6))\n' + WORK) + block("FINAL_VAR(get_report())")])
try:
    rc._dumps(res.metadata)
    dumped = True
except rc.RunContextError as e:
    dumped = str(e)
check("14 the run's metadata with that call is JSON for run_context (the record G19 B could not write)",
      isinstance(res, RLMResult) and dumped is True
      and [x.get("page") for x in res.metadata["retrievals"] if x["fn"] == "get_chunks_by_page"] == [[1, 2, 3, 4, 5]],
      f"{type(res).__name__} {dumped}")

print(f"{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
