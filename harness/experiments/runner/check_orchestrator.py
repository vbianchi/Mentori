"""Checks for the orchestrator track (Figure 4; plan rows B5 and part of B2): the cuts, failures and records of
experiments/mentori/backend/agents/orchestrator/, the query tools in backend/mcp/custom/rag_tools.py, the refusal marker
of backend/tool_server.py, and publication/scripts/exp_03_orchestration_ablation.py. Offline: a fake model router (the
lock adapter is not called), a fake MCP session, a fake retriever; no model, no Ollama, no key.

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_orchestrator

1. Cuts (D25, cuts.md): the conversation context, the supervisor's prompt and its previous steps, the micro-adjust
   prompt, the coder's previous results, the distiller's input and the librarian's final answer are whole; the
   distiller and the librarian send no caller options; no rag_tools model call passes options; the cut sites cuts.md
   names in rag_tools and exp_03 are gone; deep_research's prompts and plan split use real newlines (M24).
2. Q23/Q24: synthesis reads a step's last attempt, with no Summary line; the supervisor reads content, not summary.
3. Q25: a failed or empty distillation passes the whole observation and records it; the threshold is 0.40 x the lock's
   num_ctx x 4 = 209,712 characters; D52's distiller switch "off" never distils and records it; "F1" sends exp_04b's
   prompt F1, byte for byte.
4. Failures (A5, limits.md Class X): the analyser, planner, supervisor (score None in the record, Mentori's control
   flow kept), micro-adjustment, synthesis and direct answer record a failed or unparsed call; synthesis failure is an
   error event, never a chunk; a lock refusal (LockError) raises through each of them (Q38).
5. Q38/Q39 in the executor: a tool result with isError and the tool server's marker raises ToolRefusal; isError
   without it is recorded (is_error) and the step goes on as Mentori's recovery expects; the model calls a tool made
   (calls.jsonl) and query_documents' returned passages are attached to the step; the tool server's wrapper marks a
   refusal (its cause kept) and passes any other exception unchanged.
6. The engine end to end on fakes: memory_context_injected recorded; one step retried after a low score gives two
   record_step events (attempt_no 1 and 2), synthesis reads attempt 2 only, the complete event carries plan_status
   "completed" and answer_source "content"; the thinking fallback gives answer_source "thinking_fallback" (Q26); the
   memory consolidation's task is kept in MEMORY_TASKS and returns its outcome; a refusal in a tool leaves
   orchestrated_chat as ToolRefusal; passages (A6) set before the supervisor and synthesis calls.
7. rag_tools: inside a run the query cache is neither read nor written, outside one it is (Q27); query_documents
   reranks (use_reranker True, the shared reranker; D40) and records the passages it returned; deep_research splits
   its plan on newlines into max_depth queries and names the passages before its verify call.
8. exp_03: an error never becomes the answer; a refusal is a setup error kept out of completed_keys; any other failure
   is stored with an empty answer and marked done; llm_calls comes from the call records; each answer gets a fresh
   workspace; error events and plan_status are stored; the D52 configs carry their switches. D89 (Q145 O1, O2,
   LIST.md Rule 10) and D90: a Gemini "empty" or "blocked" call record (returned to Mentori as empty text) and a
   "recitation", "malformed_function_call" or "malformed_response" one (returned with the text it held) is counted in
   an answer's failed_calls and a step's failed_tool_calls, as "error" is; "ok" and "length" are not; the answer's
   calls list keeps each call's status, so blocks, recitation stops and malformed replies can be grouped.
9. Review fixes. A4: a reranker load failure leaves query_documents and smart_query as RerankerLoadError, crosses the
   tool server with RUN_STOP_MARKER, raises RunStop in the executor, and exp_03 records it and stops the run. A5: text
   or thinking streamed before a synthesis or direct-answer error is never the answer (engine and exp_03). An empty
   plan is plan_status "failed"; an unreachable tool server is a setup error; rlm_10 stores the whole
   GenerationResult; file_count is the index's documents counted (limits.md #132); injected names overwritten values;
   to_record gives distill_failed (Q25) and executions; since() skips a partial line; read_document vision mode reads
   every page (#31) and summarize_document_pages returns the summaries (#39); web_search re-raises refusals and gives
   no score to a failed filter call; memory reads Mentori's "content" key (M1 as built).
10. Round 3 (D75, Q82 to Q94). The D52 switches (schemas.ORCHESTRATOR_SWITCHES; a misnamed one stops the run):
   analyser off makes no analyser call and plans every question (Q83); analyser factual_to_documents sends Mentori's
   prompt with only the direct-answer list changed (Q87); planner off runs one fixed smart_query(question, index) step by
   the editor (Q84); supervisor off evaluates and retries nothing and records the silent pre-check (Q85); synthesiser off
   answers with format_steps_with_results (Q86). Q88: the supervisor's Previous Steps leave out the attempt judged.
   Q89: a later step reads an earlier step's last attempt. Q90: an unknown plan role runs as default, recorded. Q91:
   Mentori's soft-failure label is unchanged against the copy at 96e2193, with tool_error_text and short_phrase_fired
   beside it. Q82: the every_step stress trigger, the over-threshold flag, and orchestrator/distiller_firing.py's count.
   Q92: memory as built, the defect stated. Q93: an unreachable tool server raises RunStop and exp_03 stops the run.
   Q94: a failed save stops the run.
11. Round 4 (D78). Q126: the supervisor is passed every stored result but the attempt judged, so it shows the
   PREVIOUS_STEPS_SHOWN (3) results before it. Q127: the factual_to_documents prompt's task sentence names the direct-
   answer cases instead of "or if you can answer directly from your knowledge"; the rest is Mentori's. Q128: a tool call
   whose MCP connection closed (McpError CONNECTION_CLOSED, anyio's closed-stream errors) checks the tool server once and
   raises RunStop when it does not answer; when it answers, and for any other error, Mentori's recovery (a failed step)
   stays; the check itself is GET /sse answering 200 with the endpoint event.
12. D79 Q135 (O1). mcp's sse_client and ClientSession are anyio task groups, so an exception leaving the engine's
   session arrives in an ExceptionGroup, nested once per group. The engine re-raises a group whose one leaf is a stop
   exp_03 classifies (SETUP_ERRORS: SetupError with ToolRefusal and RunStop, LockError, RunContextError) as that leaf,
   its own cause kept, else with the group as its cause; any other group leaves unchanged. Against a real FastMCP SSE
   tool server on a free local port, killed while a tool call is in flight: the caller sees RunStop (McpError
   CONNECTION_CLOSED its cause), and exp_03 records a setup error and stops the run.
13. D83 Q147. exp_03's --question-ids names the questions a run asks: the named ones of the 135, in the key's order
   whatever the order named; an id not among the 135, an id named twice, and --question-ids with --max-questions are
   refused. The smoke's rule (findings/recompute/G3_runs/smoke_ids.py) gives 3 answerable and 2 not-answerable
   questions, the first of each in the key's order, and a dry run with them lists 5 answers per config.
"""

import asyncio
import inspect
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
tmp = Path(tempfile.mkdtemp(prefix="check_orchestrator_")).resolve()
# Mentori's settings read these at import: a scratch database, workspace and vector store, never the copy's own
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
os.environ["BACKEND_INTERNAL_URL"] = "http://127.0.0.1:9"
sys.path.insert(0, str(MENTORI))
sys.path.insert(0, str(MENTORI / "publication" / "scripts"))

from backend.agents import lock_adapter as la  # noqa: E402
from backend.agents.session_context import (  # noqa: E402
    SessionContext, TOOL_REFUSAL_MARKER, RUN_STOP_MARKER, RerankerLoadError)
from backend.agents.orchestrator import engine as eng  # noqa: E402
from backend.agents.orchestrator import executor as exe  # noqa: E402
from backend.agents.orchestrator import observation_distiller as od  # noqa: E402
from backend.agents.orchestrator import planner as pl  # noqa: E402
from backend.agents.orchestrator import supervisor as sv  # noqa: E402
from backend.agents.orchestrator import synthesizer as sy  # noqa: E402
from backend.agents.orchestrator import memory as mem  # noqa: E402
from backend.agents.orchestrator import coder as cd  # noqa: E402
from backend.agents.orchestrator import prompts as op  # noqa: E402
from backend.agents.orchestrator import run_records as rr  # noqa: E402
from backend.agents.orchestrator.schemas import (  # noqa: E402
    PlanStep, StepResult, OrchestratorState, ExecutionPlan, SupervisorEvaluation)
from backend.agents.orchestrator import schemas as SCH  # noqa: E402
from backend.mcp.custom import rag_tools  # noqa: E402
from backend import tool_server as ts  # noqa: E402

from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402

import backend.retrieval.models  # noqa: E402,F401  (registers the collection tables)
import backend.models.task  # noqa: E402,F401
import backend.models.log  # noqa: E402,F401  (task_logs, which Mentori's DatabaseHandler writes; R3)
from backend.database import engine as db_engine  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
SQLModel.metadata.create_all(db_engine)   # the scratch database, empty (Mentori's logging writes task_logs there)

lock = load()
results = []
GEN = "gemini::gemini-3-flash-preview"


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def ctx_for(item="Q1", draw=1, sink=None, run_id="check_orch"):
    return rc.RunContext(run_id=run_id, arm="orch", item_id=item, draw=draw, thinking=None,
                         base_url="http://127.0.0.1:9", sink=sink or (tmp / run_id),
                         allowed={"gemini-3-flash-preview": "generator"},
                         agent_roles={r: GEN for r in ("lead_researcher", "supervisor", "librarian", "coder",
                                                       "editor", "handyman", "default")})


def run(coro):
    return asyncio.run(coro)


async def collect(agen):
    return [e async for e in agen]


class FakeRouter:
    """The router's three methods, answered by `script(kind, text)`; every call is kept with the passages the run
    context holds at that moment. A reply that is an exception is raised."""

    def __init__(self, script):
        self.script = script
        self.calls = []

    def _reply(self, method, messages=None, prompt=None, **kw):
        text = prompt if prompt is not None else "\n".join(m.get("content", "") for m in messages)
        self.calls.append({"method": method, "text": text, "kw": kw, "passages": rc.passages()})
        out = self.script(method, text)
        if isinstance(out, BaseException):
            raise out
        return out if isinstance(out, dict) else {"content": out}

    async def chat_stream(self, model_identifier, messages, tools=None, options=None, think=None):
        out = self._reply("chat_stream", messages, options=options, think=think)
        line = {"role": "assistant", "content": out.get("content", "")}
        if out.get("thinking"):
            line["thinking"] = out["thinking"]
        yield json.dumps({"message": line})
        yield json.dumps({"done": True, "done_reason": "stop", "prompt_eval_count": 1, "eval_count": 1})

    async def chat(self, model_identifier, messages, tools=None, options=None, think=None):
        out = self._reply("chat", messages, options=options, think=think)
        return {"message": {"role": "assistant", "content": out.get("content", "")}, "prompt_eval_count": 1,
                "eval_count": 1}

    async def generate(self, model_identifier, prompt, system=None, options=None, think=None):
        out = self._reply("generate", prompt=prompt, options=options, think=think)
        return {"response": out.get("content", ""), "prompt_eval_count": 1, "eval_count": 1}


class Text:
    def __init__(self, text):
        self.text = text


class McpResult:
    def __init__(self, text, is_error=False):
        self.content = [Text(text)]
        self.isError = is_error


def session(**kw):
    base = dict(user_id="u1", user_email="a@b", user_role="admin", task_id="t1", workspace_path=str(tmp / "ws_t1"),
                model_identifier=GEN, agent_roles={r: GEN for r in ("lead_researcher", "supervisor", "librarian",
                                                                     "coder", "editor", "handyman", "default")})
    base.update(kw)
    return SessionContext(**base)


def step(**kw):
    base = dict(step_id="step_1", description="look up", agent_role="editor", tool_name="smart_query",
                tool_args={"query": "q"}, expected_output="facts", reasoning="r")
    base.update(kw)
    return PlanStep(**base)


# ── 1, 2. Cuts and the last attempt ──────────────────────────────────────────
long_user, long_tool = "U" * 3000, "T" * 1500
cc = op.format_conversation_context([{"role": "user", "content": long_user},
                                     {"role": "tool", "name": "x", "content": long_tool}])
check("1 conversation context: a 3,000-character message and a 1,500-character tool result whole",
      long_user in cc and long_tool in cc and "..." not in cc)

attempts = [{"step_id": "step_1", "success": False, "content": "FIRST-ATTEMPT", "summary": "S1"},
            {"step_id": "step_1", "success": True, "content": "SECOND-ATTEMPT", "summary": "S2"}]
sw = op.format_steps_with_results([step()], attempts)
check("2 Q23: synthesis reads the last attempt", "SECOND-ATTEMPT" in sw and "FIRST-ATTEMPT" not in sw)
check("2 Q24: no Summary line in the synthesis prompt", "Summary:" not in sw)
check("2 last_attempt returns the last result of a step id", op.last_attempt(attempts, "step_1")["content"]
      == "SECOND-ATTEMPT" and op.last_attempt(attempts, "step_9") is None)

with rc.run(ctx_for()):
    big = "B" * 15000
    prev = [{"step_id": "step_0", "success": True, "content": "PREV-CONTENT-" + "p" * 300, "summary": "PREVSUM",
             "passage_ids": ["p0"], "distilled": False}]
    res = StepResult(step_id="step_1", success=True, content=big, summary="SUMMARY-ONLY", passage_ids=["a", "b"])
    fr = FakeRouter(lambda m, t: '{"quality_score": 80, "issues": []}')
    ev = run(sv.evaluate_step_quality(step(tool_args={"query": "q"}), res, "goal", prev, fr, GEN))
    p = fr.calls[0]["text"]
    check("1 supervisor: the step's 15,000-character content whole (was cut at 10,000)", big in p)
    check("1/Q24 supervisor: previous steps show their whole content, not the summary",
          prev[0]["content"] in p and "PREVSUM" not in p)
    check("6 A6: the supervisor's call names the passages of the content it holds",
          fr.calls[0]["passages"] == ["p0", "a", "b"], fr.calls[0]["passages"])
    check("4 supervisor ok: status ok, the model's score in the record", ev.status == "ok"
          and ev.to_dict()["quality_score"] == 80)

    fr = FakeRouter(lambda m, t: "not json at all")
    ev = run(sv.evaluate_step_quality(step(), res, "goal", [], fr, GEN))
    d = ev.to_dict()
    check("4 supervisor unparsed: status unparsed, quality_score None, control_score 60 (Mentori's flow)",
          d["status"] == "unparsed" and d["quality_score"] is None and d["control_score"] == 60
          and not ev.should_retry and not ev.should_escalate)
    fr = FakeRouter(lambda m, t: '{"issues": []}')
    ev = run(sv.evaluate_step_quality(step(), res, "goal", [], fr, GEN))
    check("4 supervisor JSON without quality_score: unparsed, from_dict's 50 drives the retry as before",
          ev.status == "unparsed" and ev.to_dict()["quality_score"] is None and ev.should_retry)
    fr = FakeRouter(lambda m, t: RuntimeError("boom"))
    ev = run(sv.evaluate_step_quality(step(), res, "goal", [], fr, GEN))
    d = ev.to_dict()
    check("4 supervisor error: status error, quality_score None, control_score 50, error kept",
          d["status"] == "error" and d["quality_score"] is None and d["control_score"] == 50
          and "boom" in (d["error"] or ""))
    fr = FakeRouter(lambda m, t: LockError("not allowed"))
    try:
        run(sv.evaluate_step_quality(step(), res, "goal", [], fr, GEN))
        check("4 supervisor: a lock refusal raises (Q38)", False)
    except LockError:
        check("4 supervisor: a lock refusal raises (Q38)", True)

    fr = FakeRouter(lambda m, t: '{"adjusted_args": {"query": "q2"}, "adjustment_type": "query_broadening"}')
    adj = run(sv.suggest_micro_adjustment(step(), res, ["x"], [], fr, GEN))
    p = fr.calls[0]["text"]
    check("1/Q24 micro-adjust: the step's content whole in place of the summary's 500 characters",
          big in p and "SUMMARY-ONLY" not in p and adj.status == "ok")
    fr = FakeRouter(lambda m, t: RuntimeError("down"))
    adj = run(sv.suggest_micro_adjustment(step(), res, ["x"], [], fr, GEN))
    check("4 micro-adjust error recorded, arguments kept (Mentori's recovery)",
          adj.status == "error" and adj.adjusted_args == step().tool_args and adj.to_dict()["status"] == "error")

    obvious = sv._detect_obvious_failure(StepResult(step_id="s", success=False, content="x",
                                                    summary="", error="E" * 300))
    check("1 M2: the heuristic's issue carries the whole tool error (was 100 characters)",
          ("E" * 300) in obvious.issues[0] and obvious.status == "heuristic")

    # coder
    fr = FakeRouter(lambda m, t: '{"steps": ["a"]}')
    prev3 = [{"step_id": f"s{i}", "content": "C" * 900 + str(i), "passage_ids": [f"x{i}"]} for i in range(4)]
    run(cd.design_algorithm(step(agent_role="coder"), prev3, "goal", fr, GEN, session()))
    check("1 M8 coder: previous results whole (were cut at 500 characters), the last 3",
          all(("C" * 900 + str(i)) in fr.calls[0]["text"] for i in (1, 2, 3))
          and ("C" * 900 + "0") not in fr.calls[0]["text"])
    fr = FakeRouter(lambda m, t: LockError("no"))
    try:
        run(cd.design_algorithm(step(agent_role="coder"), [], "goal", fr, GEN, session()))
        check("4 coder: a lock refusal raises (Q38)", False)
    except LockError:
        check("4 coder: a lock refusal raises (Q38)", True)

# ── 3. The distiller ──────────────────────────────────────────────────────────
check("3 threshold: 0.40 x LOCK num_ctx x 4 = 209,712 characters",
      od._distill_threshold_chars() == int(lock.d["generation"]["num_ctx"] * 0.4) * 4 == 209712)
with rc.run(ctx_for()):
    raw = "R" * 210000
    fr = FakeRouter(lambda m, t: "DISTILLED")
    out = {}
    got = run(od.distill_observation("smart_query", raw, fr, GEN, outcome=out, passages=["p1"]))
    check("3 the distiller reads the whole observation (was cut at 12,000) and sends no options",
          raw in fr.calls[0]["text"] and fr.calls[0]["kw"].get("options") is None, len(fr.calls[0]["text"]))
    check("3 distilled: status distilled, A6 passages named", out["status"] == "distilled" and "DISTILLED" in got
          and fr.calls[0]["passages"] == ["p1"])
    for reply, status in ((RuntimeError("down"), "failed"), ("", "empty")):
        out = {}
        got = run(od.distill_observation("smart_query", raw, FakeRouter(lambda m, t, r=reply: r), GEN, outcome=out))
        check(f"3 Q25: a {status} distillation passes the whole observation and records {status}",
              got == raw and out["status"] == status)
    async def sink_event(e):
        return None
    out = {}
    got = run(od.distill_observation("smart_query", raw, FakeRouter(lambda m, t: "DISTILLED"), GEN,
                                     event_callback=sink_event, outcome=out))
    check("3 with an event callback (token usage emitted), the outcome is still recorded",
          out.get("status") == "distilled" and "DISTILLED" in got, out)
    out = {}
    run(mem.consolidate_session_memory("t1", "u1", tmp / "memws3", "q", None, [], "a",
                                       FakeRouter(lambda m, t: '{"user_intent": "i"}'), GEN,
                                       event_callback=sink_event, outcome=out))
    check("4 memory with an event callback: the outcome is still recorded (unparsed: M1 as built)",
          out == {"status": "unparsed", "error": None}, out)
    out = {}
    got = run(od.distill_observation("x", "short", FakeRouter(lambda m, t: "no"), GEN, outcome=out))
    check("3 below the threshold: returned unchanged, no call", got == "short" and out["status"] == "below_threshold")
    try:
        run(od.distill_observation("x", raw, FakeRouter(lambda m, t: LockError("no")), GEN))
        check("3 the distiller: a lock refusal raises (Q38)", False)
    except LockError:
        check("3 the distiller: a lock refusal raises (Q38)", True)
    fr = FakeRouter(lambda m, t: "D")
    run(od.distill_observation("smart_query", raw, fr, GEN, variant="F1"))
    check("3 D52 F1: the distiller sends prompt F1 with the whole observation",
          "Here are examples of good distillations" in fr.calls[0]["text"] and raw in fr.calls[0]["text"])
try:
    import exp_04b_distiller_ablation as e4b
    obs = "The study found 42.0% (n=7) in 01_x.pdf. " * 20
    check("3 D52 F1: byte for byte exp_04b's prompt F1 (an observation under 12,000 characters)",
          od.distiller_prompt("smart_query", obs, "F1") == e4b.build_prompt("F1", "smart_query", obs))
    check("3 Mentori's prompt unchanged: exp_04b's baseline equals the distiller's 'on' prompt",
          od.distiller_prompt("smart_query", obs, "on") == e4b.build_prompt("baseline", "smart_query", obs))
    big = obs * 40   # 33,600 characters: exp_04b sends the observation whole too (audit F4)
    check("3 D52 F1: byte for byte exp_04b's prompt F1 on an observation over 12,000 characters, sent whole",
          len(big) > 12000 and od.distiller_prompt("smart_query", big, "F1")
          == e4b.build_prompt("F1", "smart_query", big) and big in e4b.build_prompt("F1", "smart_query", big))
except Exception as e:  # noqa: BLE001
    check("3 D52 F1: exp_04b importable for the byte comparison", False, f"{type(e).__name__}: {e}")

# ── 4. Planner, synthesis, memory failures ───────────────────────────────────
with rc.run(ctx_for()):
    msgs = [{"role": "user", "content": "What is X?"}]
    a = run(pl.analyze_query(FakeRouter(lambda m, t: RuntimeError("x")), GEN, msgs, [], session()))
    check("4 analyser error: Mentori's needs_plan kept, status error recorded",
          a.decision == "needs_plan" and a.status == "error" and "x" in a.error)
    a = run(pl.analyze_query(FakeRouter(lambda m, t: "direct_answer please"), GEN, msgs, [], session()))
    check("4 analyser unparsed: Mentori's guess kept, status unparsed", a.decision == "direct_answer"
          and a.status == "unparsed")
    fr = FakeRouter(lambda m, t: '{"decision": "needs_plan"}')
    run(pl.analyze_query(fr, GEN, msgs, [], session()))
    check("6 A6: the analyser's call names no passage", fr.calls[0]["passages"] == [])
    pln = run(pl.generate_plan(FakeRouter(lambda m, t: RuntimeError("p")), GEN, msgs, [], session()))
    check("4 planner error: empty plan (Mentori), generation_status error", pln.steps == []
          and pln.generation_status == "error" and pln.to_dict()["generation_status"] == "error")
    reply = "no plan here " * 40
    pln = run(pl.generate_plan(FakeRouter(lambda m, t: reply), GEN, msgs, [], session()))
    check("4 planner unparsed: generation_status unparsed, the whole reply kept (was 200 characters)",
          pln.generation_status == "unparsed" and reply in pln.reasoning)
    try:
        run(pl.generate_plan(FakeRouter(lambda m, t: LockError("no")), GEN, msgs, [], session()))
        check("4 planner: a lock refusal raises (Q38)", False)
    except LockError:
        check("4 planner: a lock refusal raises (Q38)", True)

    st = OrchestratorState(task_id="t1", user_query="q")
    st.plan = ExecutionPlan(plan_id="p", goal="g", steps=[step()], reasoning="")
    st.step_results = [{"step_id": "step_1", "content": "C", "success": True, "passage_ids": ["z1"],
                        "distilled": False}]
    evs = run(collect(sy.synthesize_answer(st, FakeRouter(lambda m, t: RuntimeError("synth down")), GEN, session())))
    check("4 synthesis error: an error event, no chunk (was '[Error during synthesis: ...]' as answer text)",
          not any(e["type"] == "chunk" for e in evs) and evs[-1]["type"] == "error"
          and evs[-1]["phase"] == "synthesis" and "synth down" in evs[-1]["error"])
    fr = FakeRouter(lambda m, t: "ANSWER")
    evs = run(collect(sy.synthesize_answer(st, fr, GEN, session())))
    check("6 A6: the synthesis call names the passages of the attempts it reads", fr.calls[0]["passages"] == ["z1"])
    st2 = OrchestratorState(task_id="t1", user_query="q")
    evs = run(collect(sy.synthesize_answer(st2, FakeRouter(lambda m, t: "x"), GEN, session())))
    check("4 synthesis without results: an error event, not the apology text as answer",
          [e["type"] for e in evs] == ["error"] and evs[0]["status"] == "no_results")
    evs = run(collect(sy.generate_direct_answer(FakeRouter(lambda m, t: RuntimeError("d")), GEN, msgs, session())))
    check("4 direct answer error: an error event, no chunk", [e["type"] for e in evs] == ["error"])
    try:
        run(collect(sy.synthesize_answer(st, FakeRouter(lambda m, t: LockError("no")), GEN, session())))
        check("4 synthesis: a lock refusal raises (Q38)", False)
    except LockError:
        check("4 synthesis: a lock refusal raises (Q38)", True)

    fr = FakeRouter(lambda m, t: '{"user_intent": "I", "key_findings": []}')
    out = {}
    fa = "F" * 2000
    run(mem.consolidate_session_memory("t1", "u1", tmp / "memws", "q" * 300, None, [], fa, fr, GEN, outcome=out))
    check("1 memory: the librarian gets the whole final answer (was 500), no options, A6 no passage",
          fa in fr.calls[0]["text"] and fr.calls[0]["kw"].get("options") is None and fr.calls[0]["passages"] == [])
    check("4 M1 memory: Mentori's key 'content' kept (class C under Q22 O2), so router.generate's reply is unread: "
          "status unparsed, the whole query saved",
          out["status"] == "unparsed" and mem.TaskMemoryVault("t1", "u1", tmp / "memws").load().sessions[-1]
          .user_intent == "q" * 300)
    out = {}
    run(mem.consolidate_session_memory("t1", "u1", tmp / "memws2", "q" * 300, None, [], fa,
                                       FakeRouter(lambda m, t: RuntimeError("lib")), GEN, outcome=out))
    check("4 memory: a failed librarian call is recorded, Mentori's fallback (whole query) saved",
          out["status"] == "error" and mem.TaskMemoryVault("t1", "u1", tmp / "memws2").load().sessions[-1].user_intent
          == "q" * 300)

# ── 5. Executor and tool server ──────────────────────────────────────────────
class FakeMcp:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        out = self.reply(name, arguments, len(self.calls))
        if isinstance(out, BaseException):
            raise out
        return out


with rc.run(ctx_for(item="QX", sink=tmp / "exec_sink")) as c:
    refusal_text = f"Error executing tool smart_query: {TOOL_REFUSAL_MARKER} LockError: role 'editor' missing"
    try:
        run(collect(exe.execute_step(step(), FakeRouter(lambda m, t: ""), session(), FakeMcp(
            lambda n, a, k: McpResult(refusal_text, True)), [])))
        check("5 Q38: a refusal result raises ToolRefusal", False)
    except rr.ToolRefusal as e:
        check("5 Q38: a refusal result raises ToolRefusal", TOOL_REFUSAL_MARKER in str(e))

    def tool_reply(n, a, k):
        # what the tool server writes during the call: one model call record and query_documents' passages
        rc.append({"status": "error", "model": "gemini-3-flash-preview", "error": "stalled", "call_site": "tool"})
        rc.append({"kind": "route", "tool": "smart_query", "route": {"tool_name": "query_documents"}},
                  file=rr.TOOL_RECORDS)
        rc.append({"kind": "returned_passages", "passages": ["id1", "id2"]}, file=rr.TOOL_RECORDS)
        return McpResult("Error executing tool smart_query: boom", True)
    evs = run(collect(exe.execute_step(step(), FakeRouter(lambda m, t: ""), session(), FakeMcp(tool_reply), [],
                                       attempt_no=2)))
    res = [e for e in evs if e["type"] == "_step_result"][0]["result"]
    rec = res.to_record()
    check("5 Q39: isError without the marker goes on; recorded is_error, attempt_no 2",
          rec["is_error"] and rec["attempt_no"] == 2 and res.content.startswith("Error executing tool"))
    check("5 Q39: the failed model call inside the tool is on the step with its status",
          rec["failed_tool_calls"] == 1 and rec["tool_calls"][0]["status"] == "error")
    check("5 records F14: routing and the passages query_documents returned whole",
          rec["routing"] == {"tool_name": "query_documents"} and rec["passage_ids"] == ["id1", "id2"]
          and res.to_dict()["passage_ids"] == ["id1", "id2"])
    check("5 records: the step keeps the tool's arguments and the raw output",
          rec["tool_args"] == {"query": "q"} and rec["raw_content"] == res.content)

    big_out = "Z" * 210000
    for switch, distilled in (("off", False), ("on", True)):
        fr = FakeRouter(lambda m, t: "SHORT")
        evs = run(collect(exe.execute_step(step(), fr, session(orchestrator_switches={"distiller": switch}),
                                           FakeMcp(lambda n, a, k: McpResult(big_out)), [])))
        r = [e for e in evs if e["type"] == "_step_result"][0]["result"]
        ok = (r.content == big_out and r.distill["status"] == "switched_off" and not fr.calls) if switch == "off" \
            else (r.distilled and r.distill["status"] == "distilled" and len(fr.calls) == 1)
        check(f"3 D52 distiller switch {switch!r}", ok, r.distill)

    run_ctx = rc.RunContext(run_id="check_orch", arm="orch", item_id=None, draw=None, thinking=None,
                            base_url="http://127.0.0.1:9", sink=tmp / "check_orch", allowed={"x": "judge"})

    async def tool_ok(task_id: str = None):
        raise LockError("model not allowed")
    w = ts.in_run("tool_ok", tool_ok, run_ctx)
    try:
        run(w())
        check("5 tool server: a refusal (no task_id) is marked", False)
    except ts.LockRefusal as e:
        check("5 tool server: a call with no task_id is refused with the marker, cause RunContextError",
              str(e).startswith(TOOL_REFUSAL_MARKER) and isinstance(e.__cause__, rc.RunContextError))

    def tool_plain():
        raise ValueError("plain failure")
    w = ts.in_run("tool_plain", tool_plain, run_ctx)
    try:
        w()
    except Exception as e:  # noqa: BLE001
        check("5 tool server: any other exception passes unchanged (no marker; Q39)",
              type(e) is ValueError and TOOL_REFUSAL_MARKER not in str(e))

    def tool_refuse():
        raise LockError("no role")
    w = ts.in_run("tool_refuse", tool_refuse, run_ctx)
    try:
        w()
    except ts.LockRefusal as e:
        check("5 tool server: a LockError from the tool is marked, its cause kept",
              TOOL_REFUSAL_MARKER in str(e) and isinstance(e.__cause__, LockError))

    from mcp.server.fastmcp import FastMCP
    srv = FastMCP("check")
    srv.tool(name="tool_refuse")(ts.in_run("tool_refuse", tool_refuse, run_ctx))
    try:
        run(srv.call_tool("tool_refuse", {}))
        check("5 tool server: FastMCP's error text carries the marker", False)
    except Exception as e:  # noqa: BLE001
        check("5 tool server: FastMCP's error text carries the marker (the text the client reads)",
              str(e).startswith("Error executing tool tool_refuse: " + TOOL_REFUSAL_MARKER), str(e))
    check("5 run_records.is_refusal_result reads isError and the marker",
          rr.is_refusal_result(McpResult(refusal_text, True)) and not rr.is_refusal_result(McpResult(refusal_text))
          and not rr.is_refusal_result(McpResult("Error executing tool x: other", True)))

    # A4 (D67): a reranker load failure crosses the tool server unchanged, with RUN_STOP_MARKER in FastMCP's text
    def tool_rerank():
        raise RerankerLoadError(OSError("weights missing"))
    srv.tool(name="tool_rerank")(ts.in_run("tool_rerank", tool_rerank, run_ctx))
    try:
        run(srv.call_tool("tool_rerank", {}))
        check("5 A4: a reranker load failure reaches the client with RUN_STOP_MARKER", False)
    except Exception as e:  # noqa: BLE001
        check("5 A4: a reranker load failure reaches the client with RUN_STOP_MARKER, not the refusal marker",
              str(e).startswith("Error executing tool tool_rerank: " + RUN_STOP_MARKER)
              and TOOL_REFUSAL_MARKER not in str(e), str(e))
    stop_text = f"Error executing tool smart_query: {RUN_STOP_MARKER} RerankerLoadError: OSError: weights missing"
    try:
        run(collect(exe.execute_step(step(), FakeRouter(lambda m, t: ""), session(), FakeMcp(
            lambda n, a, k: McpResult(stop_text, True)), [])))
        check("5 A4: the executor raises RunStop on the run-stop marker", False)
    except rr.RunStop as e:
        check("5 A4: the executor raises RunStop on the run-stop marker (a SetupError, not a ToolRefusal)",
              isinstance(e, rr.SetupError) and not isinstance(e, rr.ToolRefusal) and RUN_STOP_MARKER in str(e))
    check("5 run_records.is_run_stop_result reads isError and the marker",
          rr.is_run_stop_result(McpResult(stop_text, True)) and not rr.is_run_stop_result(McpResult(stop_text))
          and not rr.is_run_stop_result(McpResult(refusal_text, True)))

    # D8: a session value that overwrote a value the plan gave is named in injected (names only)
    import types  # noqa: E402
    from backend.agents.session_context import set_session_context  # noqa: E402
    from backend.mcp.registry import registry  # noqa: E402

    def fake_tool(query: str, user_id: str = None, task_id: str = None):
        return ""
    registry.tools["fake_injected"] = types.SimpleNamespace(func=fake_tool, secrets=[])
    set_session_context(session())
    evs = run(collect(exe.execute_step(step(tool_name="fake_injected", tool_args={"query": "q", "user_id": "PLAN"}),
                                       FakeRouter(lambda m, t: ""), session(), FakeMcp(lambda n, a, k: McpResult("ok")),
                                       [])))
    rec = [e for e in evs if e["type"] == "_step_result"][0]["result"].to_record()
    check("5 D8: injected names a plan value the session overwrote (user_id) and one it added (task_id), not query",
          rec["injected"] == ["task_id", "user_id"] and rec["tool_args"]["user_id"] == "PLAN", rec["injected"])
    registry.tools.pop("fake_injected", None)
    set_session_context(None)

    check("5 Q25 (D4): to_record gives distill_failed for a failed or empty distillation, not for a distilled one",
          StepResult(step_id="s", success=True, content="c", summary="", distill={"status": "failed"})
          .to_record()["distill_failed"] is True
          and StepResult(step_id="s", success=True, content="c", summary="", distill={"status": "empty"})
          .to_record()["distill_failed"] is True
          and StepResult(step_id="s", success=True, content="c", summary="", distill={"status": "distilled"})
          .to_record()["distill_failed"] is False
          and StepResult(step_id="s", success=True, content="c", summary="").to_record()["distill_failed"] is False)
    check("5 records F14 (D7): a coder step's runs are in executions, routing stays smart_query's route",
          "executions" in StepResult(step_id="s", success=True, content="c", summary="").to_record()
          and "coder_executions" not in inspect.getsource(cd) and 'rec["executions"] = executions'
          in inspect.getsource(cd))

    # R2: a byte offset that falls inside a line drops that line's tail instead of parsing it
    rc.append({"kind": "first"}, file="r2.jsonl")
    mid = rr.offset("r2.jsonl") - 5
    rc.append({"kind": "second"}, file="r2.jsonl")
    got = rr.since("r2.jsonl", mid)
    check("5 R2: since() from inside a line skips the fragment and reads the next whole line",
          [g["kind"] for g in got] == ["second"], got)
    check("5 R2: since() from a line start reads that line", [g["kind"] for g in rr.since("r2.jsonl", 0)]
          == ["first", "second"])


# ── 6. The engine on fakes ───────────────────────────────────────────────────
class FakeTool:
    def __init__(self, name):
        self.name, self.description, self.inputSchema = name, "d", {"properties": {}}


class FakeClientSession:
    tool_reply = None

    def __init__(self, r, w):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def initialize(self):
        return None

    async def list_tools(self):
        class R:
            tools = [FakeTool("smart_query")]
        return R()

    async def call_tool(self, name, arguments):
        return FakeClientSession.tool_reply(name, arguments)


class FakeSse:
    def __init__(self, url, **kw):
        FakeSse.kw = kw

    async def __aenter__(self):
        return (None, None)

    async def __aexit__(self, *a):
        return False


class NoCancel:
    def is_cancelled(self, task_id):
        return False


eng.sse_client = FakeSse
eng.ClientSession = FakeClientSession
eng._get_task_manager = lambda: NoCancel()
PLAN = json.dumps({"goal": "g", "reasoning": "r", "steps": [
    {"step_id": "step_1", "description": "find", "agent_role": "editor", "tool_name": "smart_query",
     "tool_args": {"query": "q", "index_name": "idx"}, "expected_output": "o", "reasoning": "r"}]})


def engine_script(synth_reply):
    scores = iter([40, 90])

    def script(method, text):
        if "query analyzer" in text:
            return '{"decision": "needs_plan", "complexity": "simple", "reasoning": "r"}'
        if "<task_context>" in text:
            return PLAN
        if "quality-focused Supervisor" in text:
            return json.dumps({"quality_score": next(scores), "issues": ["thin"]})
        if "suggesting targeted improvements" in text:
            return '{"adjusted_args": {"query": "q broader"}, "adjustment_type": "query_broadening"}'
        if method == "generate":   # the librarian
            return '{"user_intent": "i"}'
        return synth_reply
    return script


async def engine_run(fr, sc):
    events = [e async for e in eng.orchestrated_chat(fr, GEN, [{"role": "user", "content": "What is X?"}], sc)]
    task = eng.MEMORY_TASKS.pop(sc.task_id, None)
    return events, (await task if task else None)


with rc.run(ctx_for(item="QE", sink=tmp / "engine_sink")):
    calls = iter(["ATTEMPT-ONE-OUTPUT", "ATTEMPT-TWO-OUTPUT"])
    FakeClientSession.tool_reply = lambda n, a: McpResult(next(calls))
    fr = FakeRouter(engine_script("THE ANSWER"))
    sc = session(task_id="tE", workspace_path=str(tmp / "ws_engine"))
    events, mem_out = run(engine_run(fr, sc))
    types = [e["type"] for e in events]
    steps = [e["step"] for e in events if e["type"] == "record_step"]
    complete = [e for e in events if e["type"] == "complete"][0]
    synth = [c for c in fr.calls if "ATTEMPT-" in c["text"] and "quality-focused" not in c["text"]
             and "targeted improvements" not in c["text"] and c["method"] == "chat_stream"]
    check("6 limits.md #142: the engine opens the tool server's stream with no read timeout",
          FakeSse.kw.get("sse_read_timeout", "unset") is None)
    check("6 Q22: record_memory carries the memory context injected (a fresh workspace: none)",
          [e for e in events if e["type"] == "record_memory"][0]["memory_context_injected"]
          == "(No previous sessions in this task)")
    check("6 record_analysis and record_plan", "record_analysis" in types and
          [e for e in events if e["type"] == "record_plan"][0]["steps_planned"] == 1)
    check("6 Q23: two attempts recorded, attempt_no 1 and 2, raw output of each",
          [s["attempt_no"] for s in steps] == [1, 2]
          and [s["raw_content"] for s in steps] == ["ATTEMPT-ONE-OUTPUT", "ATTEMPT-TWO-OUTPUT"]
          and steps[1]["tool_args"] == {"query": "q broader", "index_name": "idx"})
    check("6 Q23: synthesis reads attempt 2 only", len(synth) == 1 and "ATTEMPT-TWO-OUTPUT" in synth[0]["text"]
          and "ATTEMPT-ONE-OUTPUT" not in synth[0]["text"])
    sup = [e for e in events if e["type"] == "supervisor_evaluation"]
    check("6 supervisor evaluations carry status and attempt_no", [(s["attempt_no"], s["quality_score"],
          s["status"]) for s in sup] == [(1, 40, "ok"), (2, 90, "ok")], sup)
    check("6 complete: plan_status completed, answer_source content, the answer is the synthesis text",
          complete["plan_status"] == "completed" and complete["answer_source"] == "content"
          and complete["content"] == "THE ANSWER")
    check("6 the memory consolidation is kept (MEMORY_TASKS) and returns its outcome (unparsed: M1 as built)",
          mem_out == {"status": "unparsed", "error": None}, mem_out)

    calls = iter(["OUT"] * 4)
    FakeClientSession.tool_reply = lambda n, a: McpResult(next(calls))
    fr = FakeRouter(engine_script({"content": "", "thinking": "THOUGHTS"}))
    events, _ = run(engine_run(fr, session(task_id="tF", workspace_path=str(tmp / "ws_f"))))
    complete = [e for e in events if e["type"] == "complete"][0]
    check("6 Q26: the thinking fallback is kept and recorded", complete["answer_source"] == "thinking_fallback"
          and complete["content"] == "THOUGHTS")

    FakeClientSession.tool_reply = lambda n, a: McpResult(
        f"Error executing tool smart_query: {TOOL_REFUSAL_MARKER} LockError: x", True)
    try:
        run(engine_run(FakeRouter(engine_script("A")), session(task_id="tG", workspace_path=str(tmp / "ws_g"))))
        check("6 Q38: a refusal inside a tool leaves orchestrated_chat", False)
    except rr.ToolRefusal:
        check("6 Q38: a refusal inside a tool leaves orchestrated_chat", True)

    # limits.md Class X (defect 7): an empty plan is plan_status "failed" on its error event
    def empty_plan(method, text):
        return "not a plan" if "<task_context>" in text else engine_script("A")(method, text)
    events, _ = run(engine_run(FakeRouter(empty_plan), session(task_id="tH", workspace_path=str(tmp / "ws_h"))))
    err = [e for e in events if e["type"] == "error"]
    check("6 an empty plan: error event with plan_status failed, no complete event",
          err and err[0]["phase"] == "planning" and err[0]["plan_status"] == "failed"
          and not [e for e in events if e["type"] == "complete"], err)

    # A5 (D2): thinking streamed before a failed synthesis call never becomes the answer
    class ThinkThenFail(FakeRouter):
        async def chat_stream(self, model_identifier, messages, tools=None, options=None, think=None):
            text = "\n".join(m.get("content", "") for m in messages)
            if "quality-focused" in text or "query analyzer" in text or "<task_context>" in text \
                    or "targeted improvements" in text:
                async for line in super().chat_stream(model_identifier, messages, tools, options, think):
                    yield line
                return
            yield json.dumps({"message": {"role": "assistant", "thinking": "HALF-THOUGHT"}})
            raise RuntimeError("stream dropped")
    calls = iter(["OUT"] * 4)
    FakeClientSession.tool_reply = lambda n, a: McpResult(next(calls))
    events, _ = run(engine_run(ThinkThenFail(engine_script("A")), session(task_id="tI",
                                                                          workspace_path=str(tmp / "ws_i"))))
    complete = [e for e in events if e["type"] == "complete"][0]
    check("6 A5: after a synthesis error the thinking fallback is not taken (answer empty, answer_source None)",
          complete["content"] == "" and complete["answer_source"] is None
          and any(e["type"] == "error" and e.get("phase") == "synthesis" for e in events))

    # defect 3 and Q93 (D75): an unreachable tool server is an error event of phase tool_server, then RunStop
    class DeadSse(FakeSse):
        async def __aenter__(self):
            raise ConnectionError("refused")
    eng.sse_client = DeadSse

    async def dead_run():
        seen = []
        try:
            async for e in eng.orchestrated_chat(FakeRouter(engine_script("A")), GEN,
                                                 [{"role": "user", "content": "What is X?"}],
                                                 session(task_id="tJ", workspace_path=str(tmp / "ws_j"))):
                seen.append(e)
        except rr.RunStop as e:
            return seen, e
        return seen, None
    events, stop = run(dead_run())
    eng.sse_client = FakeSse
    err = [e for e in events if e["type"] == "error"]
    check("6 an unreachable tool server: error event phase tool_server", err and err[0]["phase"] == "tool_server",
          err)
    check("10 Q93: an unreachable tool server then raises RunStop (a SetupError) with the cause",
          isinstance(stop, rr.RunStop) and isinstance(stop, rr.SetupError) and "refused" in str(stop)
          and isinstance(stop.__cause__, ConnectionError), stop)
REAL_CHAT = eng.orchestrated_chat   # section 8 replaces it with a fake; section 10 drives the real one

# ── 7. rag_tools ─────────────────────────────────────────────────────────────
import backend.retrieval.reranker as rk  # noqa: E402
import backend.retrieval.retriever as rt  # noqa: E402

cache_calls = []
rag_tools.response_cache.get = lambda *a, **k: cache_calls.append("get") or None
rag_tools.response_cache.set = lambda *a, **k: cache_calls.append("set")
SHARED = object()
rk.get_reranker = lambda: SHARED
built = []


class FakeRetriever:
    def __init__(self, **kw):
        built.append(kw)

    def retrieve(self, query, collection_name, top_k):
        return [{"id": f"id-{query}-{i}", "text": f"passage {i} of {query} " + "w" * 1500,
                 "metadata": {"file_name": "a.pdf", "page": i}} for i in range(top_k)]


rt.SimpleRetriever = FakeRetriever
rag_tools.__dict__.pop("SimpleRetriever", None)
with rc.run(ctx_for(item="QR", sink=tmp / "rag_sink")):
    run(rag_tools.query_documents(query="q", max_results=3, task_id="t"))
    check("7 Q27: inside a run the cache is neither read nor written", cache_calls == [])
    check("7 D40: query_documents reranks with the process's one reranker",
          built[-1].get("use_reranker") is True and built[-1].get("reranker") is SHARED)
    recs = rr.since(rr.TOOL_RECORDS, 0)
    check("7 A6: query_documents records the passages it returned", recs[-1]["kind"] == "returned_passages"
          and recs[-1]["passages"] == ["id-q-0", "id-q-1", "id-q-2"])
run(rag_tools.query_documents(query="q", max_results=3, task_id="t"))
check("7 Q27: outside a run (the web app) the cache is used as before", cache_calls == ["get", "set"])


def failing_reranker():
    raise OSError("cross-encoder weights missing")


rk.get_reranker = failing_reranker
with rc.run(ctx_for(item="QR2", sink=tmp / "rag_sink")):
    try:
        out = run(rag_tools.query_documents(query="q", max_results=3, task_id="t"))
        check("7 A4: a reranker load failure leaves query_documents (not '[Error] Query failed')", False, out[:80])
    except RerankerLoadError as e:
        check("7 A4: a reranker load failure leaves query_documents as RerankerLoadError with the run-stop marker",
              str(e).startswith(RUN_STOP_MARKER) and isinstance(e.__cause__, OSError))
rk.get_reranker = lambda: SHARED
smart_src = inspect.getsource(rag_tools.smart_query.__wrapped__ if hasattr(rag_tools.smart_query, "__wrapped__")
                              else rag_tools.smart_query)
check("7 A4: smart_query re-raises a reranker load failure from the tool it dispatched to",
      "except (LockError, rc.RunContextError, RerankerLoadError):" in smart_src)

import backend.agents.model_router as mr  # noqa: E402
deep = FakeRouter(lambda m, t: "first query\nsecond query\nthird query\nfourth query" if "Research Planner" in t
                  else "facts")
mr.ModelRouter = lambda: deep
with rc.run(ctx_for(item="QD", sink=tmp / "deep_sink")):
    run(rag_tools.deep_research(topic="T", user_id="u", task_id="t", max_depth=3))
    verify = [c for c in deep.calls if "Analyze these search results" in c["text"]]
    check("7 M24: the plan splits on newlines into max_depth queries", [c["text"].split("'")[1] for c in verify]
          == ["first query", "second query", "third query"], [c["text"][:60] for c in verify])
    check("7 M24: no literal backslash-n in any deep_research prompt",
          all("\\n" not in c["text"] for c in deep.calls))
    check("7 D25: the verify prompt holds the search results whole (were cut at 2,000 characters)",
          len(verify[0]["text"]) > 15 * 1500 and all(c["kw"].get("options") is None for c in deep.calls))
    check("7 A6: the verify call names the passages query_documents returned; plan and synthesis none",
          verify[0]["passages"] == [f"id-first query-{i}" for i in range(15)]
          and deep.calls[0]["passages"] == [] and deep.calls[-1]["passages"] == [])

src = inspect.getsource(rag_tools)
check("1 rag_tools: no model call passes options (cuts.md :627 :672 :702 :1481 :1538 :1770 :2052 :2137)",
      "options=" not in src)
for pat, where in ((r"raw_results\[:2000\]", "rag_tools.py:662"), (r"quote\[:500\]", ":1023"),
                   (r"chunk\.text\[:200\]", ":1509"), (r"cit\.quote\[:100\]", ":1594"), (r"val\[:60\]", ":1574"),
                   (r"doc_name\[:30\]", ":1569"), (r"c\.text\[:300\]", ":1755"), (r"text\[:max_per_paper\]", ":2112"),
                   (r"text_content\[:50000\]", ":547"), (r"chunk_count > 800", ":206 (D40)"),
                   (r"last_page=5", "read_document vision mode (limits.md #31)"),
                   (r"Stopped after 5 pages", "read_document vision mode note (limits.md #31)"),
                   (r"Summarization Complete", "summarize_document_pages stub (limits.md #39)")):
    check(f"1 rag_tools cut gone: {where}", not re.search(pat, src))
from backend.mcp.custom import web_search as wsm  # noqa: E402
wsrc = inspect.getsource(wsm)
handlers = len(re.findall(r"\n( *)except Exception", wsrc))
reraised = len(re.findall(r"except \(LockError, rc\.RunContextError\):\n *raise[^\n]*\n *except Exception", wsrc))
check("4 Q38 web_search: every model-call handler re-raises a lock refusal first (4 of them)",
      reraised == 4, f"{reraised} re-raise before {handlers} 'except Exception'")
check("4 A5 web_search: a failed filter call gives no score (relevance None, not 50)",
      '"relevance": None' in wsrc and '"relevance": 50' not in wsrc)
osrc = "".join(inspect.getsource(m) for m in (sv, cd, op, od, mem, eng, exe))
for pat, where in ((r"content\[:10000\]", "supervisor.py:272"), (r"summary\[:100\]", "supervisor.py:145"),
                   (r"summary\[:500\]", "supervisor.py:423"), (r"raw_content\[:12000\]", "observation_distiller:121"),
                   (r"final_answer\[:500\]", "memory.py:472"), (r'\)\[:1000\]', "engine.py:986"),
                   (r"content\[:2000\]", "prompts.py:806"), (r'get\("content", ""\)\[:500\]', "coder.py:126/:283"),
                   (r"DISTILL_MAX_OUTPUT_TOKENS", "observation_distiller.py:43")):
    check(f"1 orchestrator cut gone: {where}", not re.search(pat, osrc))

# ── 8. exp_03 ────────────────────────────────────────────────────────────────
import exp_03_orchestration_ablation as x  # noqa: E402
from experiments.runner import experiment as ex  # noqa: E402
DISPATCH = x.dispatch_config   # the real one; drive() below replaces it

check("8 D52: the defined set-ups are configs with their switches",
      {k: x.ORCHESTRATOR_CONFIGS.get(k) for k in ("full_orchestrator", "orch_no_distiller", "orch_distiller_f1")}
      == {"full_orchestrator": {}, "orch_no_distiller": {"distiller": "off"}, "orch_distiller_f1": {"distiller": "F1"}}
      and set(x.TOOL_CONFIGS) == set(x.ORCHESTRATOR_CONFIGS)
      and all(c in x.CONFIG_NAMES or c in x.STRESS_CONFIG_NAMES for c in x.ORCHESTRATOR_CONFIGS))
check("8 Q82 (D75): the every-step stress conditions are configs left out of the default run list",
      x.ORCHESTRATOR_CONFIGS.get("orch_distil_every_step") == {"distiller_trigger": "every_step"}
      and x.ORCHESTRATOR_CONFIGS.get("orch_distil_every_step_f1") == {"distiller": "F1", "distiller_trigger": "every_step"}
      and not set(x.STRESS_CONFIG_NAMES) & set(x.CONFIG_NAMES), x.STRESS_CONFIG_NAMES)
_bad = {}
for _c, _sw in x.ORCHESTRATOR_CONFIGS.items():
    try:
        SCH.resolve_switches(_sw)
    except SCH.SwitchError as _e:
        _bad[_c] = str(_e)
check("8 D52 (D75): every exp_03 orchestrator config names only defined switches and values", not _bad, _bad)
_d52 = [{"analyser": "off"}, {"planner": "off"}, {"supervisor": "off"}, {"synthesiser": "off"},
        {"analyser": "factual_to_documents"}]
_missing = [sw for sw in _d52 if sw not in x.ORCHESTRATOR_CONFIGS.values()]
check("8 D52 (D75): every D52 set-up (analyser, planner, supervisor, synthesiser off; factual_to_documents) is an "
      "exp_03 config in the default run list",
      not _missing and all(c in x.CONFIG_NAMES for c, sw in x.ORCHESTRATOR_CONFIGS.items() if sw in _d52), _missing)
xsrc = inspect.getsource(x)
check("8 exp_03 cuts gone: r['text'][:800], options=, 'Error: {e}' as answer, the shared v4_6_temp workspace",
      '[:800]' not in xsrc and "options=" not in xsrc and 'f"Error: {e}"' not in xsrc and "v4_6_temp" not in xsrc)


class Args:
    index = x.DEFAULT_INDEX
    base_url = "http://127.0.0.1:9"


root = tmp / "runs"
questions = ex.questions()[:4]


async def drive(config, behaviour):
    """_run_config over 4 questions, draw 1, with dispatch_config replaced by `behaviour`."""
    x.dispatch_config = behaviour
    rid = x.run_id_for(config, x.DEFAULT_INDEX)
    sink = ex.sink(rid, root=root)
    await x._run_config(config, rid, sink, questions, (1,), Args, None, None, None, "u")
    return json.loads((sink / x.ANSWERS_FILE).read_text())


async def behaviour(config, question, retriever, collection_name, router, user_id, index_name, task_id=None):
    qid = rc.current().item_id
    rc.append({"status": "ok", "model": "gemini-3-flash-preview", "call_site": "fake", "prompt_tokens": 10,
               "output_tokens": 5, "wall_s": 1.0})
    if qid == questions[0]["id"]:
        rc.append({"status": "error", "model": "gemini-3-flash-preview", "call_site": "fake", "error": "x"})
        raise la.LockCallError({"status": "error", "error": "x", "model": "m", "seq": 2})
    if qid == questions[1]["id"]:
        raise LockError("role 'vision' missing")
    if qid == questions[2]["id"]:
        raise rr.ToolRefusal("smart_query: [LOCK REFUSAL] ...")
    return {"answer": "fine", "llm_calls": 99}


data = run(drive("raw_gemini", behaviour))
rows = {r["question_id"]: r for r in data["results"]}
r0 = rows.get(questions[0]["id"])
check("8 A5/Q30: a failed call is stored with an empty answer, its error, marked done",
      r0 is not None and r0["generated_answer"] == "" and "LockCallError" in r0["error"]
      and r0["error_kind"] == "exception" and r0["answer_key"] in data["completed_keys"])
setup = {s["question_id"]: s for s in data["setup_errors"]}
check("8 Q38: a LockError and a ToolRefusal are setup errors, kept out of completed_keys",
      set(setup) == {questions[1]["id"], questions[2]["id"]}
      and all(s["answer_key"] not in data["completed_keys"] for s in setup.values())
      and all(s["error_kind"] == "setup_error" for s in setup.values()))
r3 = rows.get(questions[3]["id"])
check("8 A6: llm_calls from the call records (1), not the strategy's own count (99, kept as llm_calls_reported)",
      r3["generation"]["llm_calls"] == 1 and r3["generation"]["llm_calls_reported"] == 99
      and r0["generation"]["llm_calls"] == 2 and r0["generation"]["failed_calls"] == 1)

# D89 (Q145 O2, LIST.md Rule 10), D90: in Figure 4 an empty Gemini reply is a failed call, as a block, a recitation
# and a malformed reply are
Q145_CALLS = [{"status": s, "provider": "gemini", "seq": i}
              for i, s in enumerate(("ok", "length", "empty", "blocked", "recitation", "malformed_function_call",
                                     "malformed_response", "error"), 1)]
_since = x.rr.since
x.rr.since = lambda file, start: [dict(c) for c in Q145_CALLS]
try:
    q145_gen = x._calls_of_answer(0)
finally:
    x.rr.since = _since
check("8 D89, D90: an answer's failed_calls counts empty, blocked, recitation, both malformed statuses and error, "
      "not ok or length (8 calls, 6 failed), each call's status kept for the grouping",
      q145_gen["llm_calls"] == 8 and q145_gen["failed_calls"] == 6
      and [c.get("status") for c in q145_gen["calls"]] == [c["status"] for c in Q145_CALLS],
      f"{q145_gen['failed_calls']} failed")
q145_step = StepResult(step_id="s", success=True, content="", summary="", tool_calls=[dict(c) for c in Q145_CALLS])
check("8 D89, D90: a step's failed_tool_calls counts empty, blocked, recitation, both malformed statuses and error, "
      "not ok or length (6)",
      q145_step.to_record()["failed_tool_calls"] == 6, str(q145_step.to_record()["failed_tool_calls"]))


async def fake_chat(*a, **k):
    for e in FAKE_EVENTS:
        yield e


import backend.agents.orchestrator.engine as eng2  # noqa: E402
eng2.orchestrated_chat = fake_chat

# limits.md #132 (defect 5): the planner's file_count is the index's documents counted, here on a fake collection
import backend.retrieval.vector_store as vsm  # noqa: E402


class FakeVectorStore:
    def __init__(self, collection_name=None, **kw):
        self.name = collection_name

    def get_collection(self, name):
        metas = {"col23": [{"file_name": f"p{i}.pdf"} for i in range(23)] + [{"file_path": "/a/p0.pdf"}],
                 "empty": []}[name]

        class C:
            def get(self, include):
                return {"metadatas": metas}
        return C()


real_vs = vsm.VectorStore
vsm.VectorStore = FakeVectorStore
check("8 limits.md #132: file_count counts the index's documents (23 named papers; a path naming one of them adds none)",
      x._index_file_count("col23") == 23)
try:
    x._index_file_count("empty")
    check("8 limits.md #132: an empty collection is a setup error", False)
except rr.SetupError:
    check("8 limits.md #132: an empty collection is a setup error (get_collection creates a missing one)", True)
vsm.VectorStore = real_vs
counted = []
x._index_file_count = lambda name: counted.append(name) or 23
FAKE_EVENTS = [
    {"type": "record_memory", "workspace": "w", "memory_context_injected": "(No previous sessions in this task)",
     "sessions": 0, "error": None},
    {"type": "record_plan", "plan": {"status": "pending"}, "generation_status": "unparsed", "steps_planned": 0},
    {"type": "error", "phase": "planning", "plan_status": "failed", "message": "Failed to generate a valid plan."},
]


async def orch_answer(task):
    with rc.run(ctx_for(item="QO", sink=tmp / "orch_sink")):
        return await x._full_orchestrator("What is X?", "u", x.DEFAULT_INDEX, task, {"distiller": "off"})

o = run(orch_answer("v4_6_orch_QO_d1"))
check("8 F12: an orchestrator error event is recorded, the answer stays empty",
      o["answer"] == "" and o["error_kind"] == "orchestrator_error" and o["errors"][0]["phase"] == "planning"
      and o["plan_status"] == "failed")
check("8 Q22: memory_context_injected and the fresh workspace recorded, the switches stored",
      o["memory_context_injected"] == "(No previous sessions in this task)" and o["switches"] == {"distiller": "off"}
      and Path(o["workspace"]).name == "v4_6_orch_QO_d1")
FAKE_EVENTS = [{"type": "chunk", "content": "Part one. "}, {"type": "error", "phase": "executing", "message": "m"},
               {"type": "chunk", "content": "Part two."},
               {"type": "complete", "plan_status": "failed", "answer_source": "content"}]
o = run(orch_answer("v4_6_orch_QO_d1"))
check("8 the answer is the synthesis chunks only; errors beside it; plan_status stored",
      o["answer"] == "Part one. Part two." and o["error"] is None and len(o["errors"]) == 1
      and o["plan_status"] == "failed" and o["answer_source"] == "content")
check("8 Q22: a second attempt of the same answer gets its own workspace", Path(o["workspace"]).name
      == "v4_6_orch_QO_d1__r2")

# D2: text streamed before a synthesis error is not the answer
FAKE_EVENTS = [{"type": "chunk", "content": "Partial text "},
               {"type": "error", "phase": "synthesis", "message": "stream dropped"},
               {"type": "complete", "plan_status": "completed", "answer_source": "content"}]
o = run(orch_answer("v4_6_orch_QP_d1"))
check("8 A5 (D2): after a synthesis error the answer is empty, the streamed text kept as partial_answer",
      o["answer"] == "" and o["partial_answer"] == "Partial text " and o["error"] == "stream dropped"
      and o["error_kind"] == "orchestrator_error")
FAKE_EVENTS = [{"type": "error", "phase": "direct_answer", "message": "d"}, {"type": "chunk", "content": "x"}]
o = run(orch_answer("v4_6_orch_QP2_d1"))
check("8 A5 (D2): a direct-answer error likewise", o["answer"] == "" and o["error"] == "d")

# defect 3: an unreachable tool server is a setup error
FAKE_EVENTS = [{"type": "error", "phase": "tool_server", "message": "Failed to connect to Tool Server: refused"}]
try:
    run(orch_answer("v4_6_orch_QS_d1"))
    check("8 Q38 (defect 3): an unreachable tool server raises SetupError", False)
except rr.SetupError as e:
    check("8 Q38 (defect 3): an unreachable tool server raises SetupError, not a stored failure", "refused" in str(e))
check("8 limits.md #132: _full_orchestrator asks for the file count of the collection it is given",
      counted and counted[-1] is None)


# A4: a RunStop is recorded as a setup error and stops the run
async def stop_behaviour(config, question, retriever, collection_name, router, user_id, index_name, task_id=None):
    raise rr.RunStop("query_documents: [RUN STOP] RerankerLoadError: OSError: weights missing")
try:
    run(drive("naive_rag", stop_behaviour))
    check("8 A4: RunStop stops the run", False)
except SystemExit as e:
    data = json.loads((ex.sink(x.run_id_for("naive_rag", x.DEFAULT_INDEX), root=root) / x.ANSWERS_FILE).read_text())
    check("8 A4: RunStop is recorded as a setup error and stops the run at the first question",
          len(data["setup_errors"]) == 1 and data["completed_keys"] == [] and "stopped" in str(e), str(e))


# defect 1: rlm_10 stores the whole GenerationResult
from tests.experiments.exp1_rlm_vs_singlepass import GenerationResult  # noqa: E402


async def fake_rlm(question, router, model, user_id, **kw):
    return GenerationResult(answer="rlm answer", latency_s=1.0, llm_calls=3, tokens_used=10, retrieved_passages=4,
                            config="rlm_10", gen_model=model, stop_reason="final", passages=["a", "b"],
                            rlm={"stop_reason": "final", "rejections": 1}, retrievals=[{"k": 1}])
x._run_rlm = fake_rlm
with rc.run(ctx_for(item="QRLM", sink=tmp / "rlm_sink")):
    g = run(DISPATCH("rlm_10", "Q?", None, "col", None, "u", x.DEFAULT_INDEX))
check("8 A6 (defect 1): rlm_10 keeps stop_reason, passages, retrievals and the RLM's metadata",
      g["answer"] == "rlm answer" and g["stop_reason"] == "final" and g["passages"] == ["a", "b"]
      and g["rlm"] == {"stop_reason": "final", "rejections": 1} and g["retrievals"] == [{"k": 1}]
      and g["error_kind"] is None and g["word_count"] == 2, sorted(g))

# ── 10. Round 3 (D75): Q82 to Q94, the D52 phase switches ─────────────────────
import subprocess  # noqa: E402
from backend.agents.orchestrator.prompts import (  # noqa: E402
    ORCHESTRATOR_ANALYZER_PROMPT, ANALYZER_FACTUAL_TO_DOCUMENTS, _ANALYZER_DIRECT_LIST, _ANALYZER_DIRECT_LIST_FACTUAL)
sys.path.insert(0, str(MENTORI / "orchestrator"))
import distiller_firing as dfire  # noqa: E402

eng.orchestrated_chat = REAL_CHAT
eng.sse_client = FakeSse

# switches
check("10 D52: resolve_switches gives Mentori as built for an empty set-up",
      SCH.resolve_switches({}) == {"analyser": "on", "planner": "on", "supervisor": "on", "synthesiser": "on",
                                   "distiller": "on", "distiller_trigger": "threshold"})
for bad in ({"planer": "off"}, {"planner": "of"}):
    try:
        SCH.resolve_switches(bad)
        check(f"10 D52: a misnamed switch {bad} is refused", False)
    except SCH.SwitchError:
        check(f"10 D52: a misnamed switch {bad} is refused", True)

PLAN2 = json.dumps({"goal": "g", "reasoning": "r", "steps": [
    {"step_id": "step_1", "description": "find", "agent_role": "editor", "tool_name": "smart_query",
     "tool_args": {"query": "q1", "index_name": "idx"}, "expected_output": "o", "reasoning": "r"},
    {"step_id": "step_2", "description": "more", "agent_role": "editor", "tool_name": "smart_query",
     "tool_args": {"query": "q2 {{step_1.result}}", "index_name": "idx"}, "expected_output": "o", "reasoning": "r"}]})


def script2(plan=PLAN, synth="THE ANSWER", scores=(40, 90, 90, 90)):
    it = iter(scores)

    def script(method, text):
        if "query analyzer" in text:
            return '{"decision": "needs_plan", "complexity": "simple", "reasoning": "r"}'
        if "<task_context>" in text:
            return plan
        if "quality-focused Supervisor" in text:
            return json.dumps({"quality_score": next(it), "issues": ["thin"]})
        if "suggesting targeted improvements" in text:
            return '{"adjusted_args": {"query": "q broader"}, "adjustment_type": "query_broadening"}'
        if method == "generate":
            return '{"user_intent": "i"}'
        return synth
    return script


def kinds(fr):
    """Which phase each model call of a run was (by its prompt)."""
    out = []
    for c in fr.calls:
        t = c["text"]
        out.append("analyser" if "query analyzer" in t else "planner" if "<task_context>" in t else
                   "supervisor" if "quality-focused Supervisor" in t else
                   "micro_adjust" if "suggesting targeted improvements" in t else
                   "librarian" if c["method"] == "generate" else "synthesis")
    return out


TOOL_ARGS = []


def replies(*texts):
    it = iter(texts)

    def reply(n, a):
        TOOL_ARGS.append((n, dict(a)))
        return McpResult(next(it))
    return reply


def by_type(events, t):
    return [e for e in events if e["type"] == t]


with rc.run(ctx_for(item="Q10", sink=tmp / "r3_sink")):
    # Q88: the attempt being judged is not repeated under Previous Steps Context
    FakeClientSession.tool_reply = replies("ATTEMPT-ONE-OUTPUT", "ATTEMPT-TWO-OUTPUT")
    fr = FakeRouter(script2())
    events, _ = run(engine_run(fr, session(task_id="t88", workspace_path=str(tmp / "ws_88"))))
    sup = [c["text"] for c in fr.calls if "quality-focused Supervisor" in c["text"]]
    prev1 = sup[0].split("## Previous Steps Context")[1].split("## Your Evaluation Task")[0]
    prev2 = sup[1].split("## Previous Steps Context")[1].split("## Your Evaluation Task")[0]
    check("10 Q88: the first attempt is judged once (under Actual Result), not again under Previous Steps Context",
          sup[0].count("ATTEMPT-ONE-OUTPUT") == 1 and "(No previous steps)" in prev1, prev1)
    check("10 Q88: judging the retry, the earlier rejected attempt stays in Previous Steps, the current does not",
          "ATTEMPT-ONE-OUTPUT" in prev2 and "ATTEMPT-TWO-OUTPUT" not in prev2 and sup[1].count("ATTEMPT-TWO-OUTPUT") == 1)
    # Q88, Q126 (D78): with 5 stored results (step_5 being judged) Mentori showed step_3, step_4 and step_5 again;
    # now the three results before the attempt, step_2, step_3 and step_4 (PREVIOUS_STEPS_SHOWN = 3), and never step_5
    five = [{"step_id": f"step_{i}", "content": f"OUT-{i}", "success": True} for i in range(1, 6)]
    shown_now = [r["step_id"] for r in eng._supervisor_previous(five)[-sv.PREVIOUS_STEPS_SHOWN:]]
    summary5 = sv._format_previous_steps_summary(eng._supervisor_previous(five))
    check("11 Q126: with 5 stored results the supervisor shows step_2, step_3 and step_4 (3 before the attempt)",
          shown_now == ["step_2", "step_3", "step_4"] and sv.PREVIOUS_STEPS_SHOWN == 3
          and all(f"OUT-{i}" in summary5 for i in (2, 3, 4)) and "OUT-1" not in summary5 and "OUT-5" not in summary5,
          shown_now)
    check("10 Q88: with 1 or 2 stored results the window is the earlier result or none",
          eng._supervisor_previous(five[:1]) == [] and eng._supervisor_previous(five[:2]) == five[:1])
    check("11 Q126: with 4 stored results all 3 earlier ones are shown; with 3, the 2 earlier ones",
          eng._supervisor_previous(five[:4]) == five[:3] and eng._supervisor_previous(five[:3]) == five[:2])

    # Q83: analyser off
    FakeClientSession.tool_reply = replies("OUT-A", "OUT-B")
    fr = FakeRouter(script2())
    events, _ = run(engine_run(fr, session(task_id="t83", workspace_path=str(tmp / "ws_83"),
                                           orchestrator_switches={"analyser": "off"})))
    ra = by_type(events, "record_analysis")[0]
    check("10 Q83 analyser off: no analyser call, analysis switched_off, every question to the planner and the tools",
          "analyser" not in kinds(fr) and "planner" in kinds(fr) and ra["status"] == "switched_off"
          and ra["decision"] == "needs_plan" and by_type(events, "complete")[0]["content"] == "THE ANSWER", kinds(fr))

    # Q87: the analyser with the repaired prompt
    fr = FakeRouter(script2())
    run(pl.analyze_query(fr, GEN, [{"role": "user", "content": "What is the chemical formula for water?"}], [],
                         session(), prompt_variant="factual_to_documents"))
    t = fr.calls[0]["text"]
    gk = "General knowledge questions you can answer without searching"
    check("10 Q87: the repaired prompt drops the general-knowledge line and sends every factual question to the documents",
          gk not in t and "Every factual question, whether or not it is about the subject" in t
          and "Greetings" in t and "Meta questions" in t and "Simple clarifications" in t
          and "Conversation continuations" not in t and "Follow-up questions about information" not in t)
    check("10 Q87, Q127: outside the direct-answer list and the task sentence the prompt is Mentori's, byte for byte",
          ANALYZER_FACTUAL_TO_DOCUMENTS.replace(_ANALYZER_DIRECT_LIST_FACTUAL, _ANALYZER_DIRECT_LIST)
          .replace(op._ANALYZER_TASK_FACTUAL, op._ANALYZER_TASK)
          == ORCHESTRATOR_ANALYZER_PROMPT and gk in ORCHESTRATOR_ANALYZER_PROMPT)
    own = "or if you can answer directly from your knowledge"
    check("11 Q127: the factual_to_documents task sentence names the direct-answer cases; Mentori's keeps its own",
          "## Your Task\nDecide if this query needs a multi-step plan with tools, or is one of the direct-answer cases "
          "listed below.\n" in t and own not in t and own in ORCHESTRATOR_ANALYZER_PROMPT, t[:400])
    fr = FakeRouter(script2())
    FakeClientSession.tool_reply = replies("OUT-A", "OUT-B")
    events, _ = run(engine_run(fr, session(task_id="t87", workspace_path=str(tmp / "ws_87"),
                                           orchestrator_switches={"analyser": "factual_to_documents"})))
    an = [c["text"] for c in fr.calls if "query analyzer" in c["text"]]
    check("10 Q87 in the engine: the analyser runs (a call, status ok) with the repaired prompt",
          len(an) == 1 and gk not in an[0] and by_type(events, "record_analysis")[0]["status"] == "ok")
    fr = FakeRouter(script2())
    FakeClientSession.tool_reply = replies("OUT-A", "OUT-B")
    run(engine_run(fr, session(task_id="t87b", workspace_path=str(tmp / "ws_87b"))))
    check("10 Q87: the full pipeline still sends Mentori's prompt",
          gk in [c["text"] for c in fr.calls if "query analyzer" in c["text"]][0])

    # Q84: planner off
    TOOL_ARGS.clear()
    FakeClientSession.tool_reply = replies("OUT-A")
    fr = FakeRouter(script2(scores=(90,)))
    q = "What does the CO2 paper report?"
    sc = session(task_id="t84", workspace_path=str(tmp / "ws_84"), orchestrator_switches={"planner": "off"},
                 rag_preferences={"default_index": "exp_v4_s20_n0"})
    events = run(collect(eng.orchestrated_chat(fr, GEN, [{"role": "user", "content": q}], sc)))
    eng.MEMORY_TASKS.pop("t84", None)
    rp = by_type(events, "record_plan")[0]
    rs = [e["step"] for e in by_type(events, "record_step")]
    check("10 Q84 planner off: no planner call; one fixed step smart_query(question, index) by the editor, mode default",
          "planner" not in kinds(fr) and rp["generation_status"] == "switched_off" and rp["steps_planned"] == 1
          and TOOL_ARGS == [("smart_query", {"query": q, "index_name": "exp_v4_s20_n0"})]
          and len(rs) == 1 and rs[0]["agent_role"] == "editor" and rs[0]["tool_name"] == "smart_query"
          and rp["plan"]["goal"] == q, (kinds(fr), TOOL_ARGS))
    check("10 Q84 planner off: the rest of the pipeline runs (analyser, supervisor, synthesis)",
          kinds(fr)[:1] == ["analyser"] and "supervisor" in kinds(fr) and "synthesis" in kinds(fr)
          and by_type(events, "complete")[0]["content"] == "THE ANSWER")
    try:
        eng.fixed_plan("q", session(rag_preferences={}, available_indexes=[]))
        check("10 Q84: a session with no index is a setup error", False)
    except rr.SetupError:
        check("10 Q84: a session with no index is a setup error", True)
    check("10 Q84: the fixed plan falls back to the first available index",
          eng.fixed_plan("q", session(available_indexes=[{"name": "idxA"}])).steps[0].tool_args
          == {"query": "q", "index_name": "idxA"})

    # Q85: supervisor off (an empty first result: the pre-check would retry it)
    TOOL_ARGS.clear()
    FakeClientSession.tool_reply = replies("", "OUT-B")
    fr = FakeRouter(script2(plan=PLAN2))
    events, _ = run(engine_run(fr, session(task_id="t85", workspace_path=str(tmp / "ws_85"),
                                           orchestrator_switches={"supervisor": "off"})))
    se = by_type(events, "supervisor_evaluation")
    rs = [e["step"] for e in by_type(events, "record_step")]
    check("10 Q85 supervisor off: no evaluation, no micro-adjustment, no retry; each step runs once, the plan completes",
          "supervisor" not in kinds(fr) and "micro_adjust" not in kinds(fr)
          and [(r["step_id"], r["attempt_no"]) for r in rs] == [("step_1", 1), ("step_2", 1)]
          and by_type(events, "complete")[0]["plan_status"] == "completed", kinds(fr))
    check("10 Q85: each attempt records status switched_off and what the text pre-check would have said",
          [s["status"] for s in se] == ["switched_off", "switched_off"] and se[0]["quality_score"] is None
          and se[0]["heuristic"]["should_retry"] is True and se[0]["heuristic"]["issues"] == ["Result is empty"]
          and se[1]["heuristic"] is None, se)

    # Q86: synthesiser off (step_1 retried: its last attempt is read; two steps joined in plan order)
    FakeClientSession.tool_reply = replies("ATTEMPT-ONE-OUTPUT", "ATTEMPT-TWO-OUTPUT", "STEP-TWO-OUTPUT")
    fr = FakeRouter(script2(plan=PLAN2))
    events, _ = run(engine_run(fr, session(task_id="t86", workspace_path=str(tmp / "ws_86"),
                                           orchestrator_switches={"synthesiser": "off"})))
    comp = by_type(events, "complete")[0]
    rs = [e["step"] for e in by_type(events, "record_step")]
    steps86 = [PlanStep.from_dict(s) for s in json.loads(PLAN2)["steps"]]
    expected = op.format_steps_with_results(steps86, [{"step_id": r["step_id"], "success": r["success"],
                                                       "content": r["content"]} for r in rs])
    check("10 Q86 synthesiser off: no synthesis call; the answer is format_steps_with_results, answer_source steps_text",
          "synthesis" not in kinds(fr) and comp["content"] == expected and comp["answer_source"] == "steps_text"
          and [c["content"] for c in by_type(events, "chunk")] == [expected], kinds(fr))
    check("10 Q86: the last attempt of step_1, then step_2, in plan order; the rejected attempt left out",
          "ATTEMPT-TWO-OUTPUT" in expected and "ATTEMPT-ONE-OUTPUT" not in expected
          and expected.index("### step_1") < expected.index("ATTEMPT-TWO-OUTPUT") < expected.index("### step_2")
          < expected.index("STEP-TWO-OUTPUT"))

    # Q89: a later step reads the last attempt of an earlier one (the retry above: step_2's argument)
    check("10 Q89 in the engine: step_2's {{step_1.result}} is the retried attempt, not the rejected one",
          rs[-1]["tool_args"]["query"] == "q2 ATTEMPT-TWO-OUTPUT", rs[-1]["tool_args"])
    got = exe.resolve_step_arguments(step(tool_args={"query": "summarize {{step_1.result}}", "n": 3}),
                                     [{"step_id": "step_1", "content": "OLD"}, {"step_id": "step_0", "content": "Z"},
                                      {"step_id": "step_1", "content": "NEW"}])
    check("10 Q89: resolve_step_arguments uses the last attempt", got == {"query": "summarize NEW", "n": 3}, got)

    # Q90: a role the run does not know is looked up as default and recorded
    evs = run(collect(exe.execute_step(step(agent_role="researcher"), FakeRouter(lambda m, t: ""), session(),
                                       FakeMcp(lambda n, a, k: McpResult("fine")), [])))
    r90 = [e for e in evs if e["type"] == "_step_result"][0]["result"].to_record()
    check("10 Q90: an unknown role ('researcher') runs as 'default', recorded; the tool runs, no setup error",
          r90["agent_role_used"] == "default" and r90["success"] and step(agent_role="researcher").agent_role
          == "researcher", r90["agent_role_used"])
    evs = run(collect(exe.execute_step(step(agent_role="editor"), FakeRouter(lambda m, t: ""), session(),
                                       FakeMcp(lambda n, a, k: McpResult("fine")), [])))
    check("10 Q90: a known role is used as written",
          [e for e in evs if e["type"] == "_step_result"][0]["result"].to_record()["agent_role_used"] == "editor")
    PLAN90 = PLAN.replace('"agent_role": "editor"', '"agent_role": "researcher"')
    FakeClientSession.tool_reply = replies("OUT-A")
    events, _ = run(engine_run(FakeRouter(script2(plan=PLAN90, scores=(90,))),
                               session(task_id="t90", workspace_path=str(tmp / "ws_90"))))
    rs = [e["step"] for e in by_type(events, "record_step")]
    check("10 Q90 in the engine: the step record keeps the role as written and the role used",
          rs[0]["agent_role"] == "researcher" and rs[0]["agent_role_used"] == "default"
          and by_type(events, "complete")[0]["content"] == "THE ANSWER")

with rc.run(rc.RunContext(run_id="check_orch", arm="orch", item_id="Q90b", draw=1, thinking=None,
                          base_url="http://127.0.0.1:9", sink=tmp / "r3_nodefault",
                          allowed={"gemini-3-flash-preview": "generator"}, agent_roles={"editor": GEN})):
    try:
        run(collect(exe.execute_step(step(agent_role="researcher"), FakeRouter(lambda m, t: ""), session(),
                                     FakeMcp(lambda n, a, k: McpResult("fine")), [])))
        check("10 Q90: a run that names no 'default' role still refuses (a setup error)", False)
    except LockError:
        check("10 Q90: a run that names no 'default' role still refuses (a setup error)", True)

# Q91: Mentori's check unchanged, the truth beside it
orig = subprocess.run(["git", "-C", str(ROOT), "show",
                       "96e2193:experiments/mentori/backend/agents/orchestrator/executor.py"],
                      capture_output=True, text=True, check=True).stdout
src91 = orig[orig.index("def _detect_error_in_result"):orig.index("def _generate_result_summary")]
ns91 = {"re": re, "Optional": __import__("typing").Optional}
exec(src91, ns91)
PREFIX = "**Strategy**: simple_rag → `query_documents`\n**Reason**: factual question\n\n"
samples = ["", "Error: boom", "error - x", "Failed: y", "[Error] Query failed: timeout", PREFIX + "[Error] Query failed: t",
           "The gene was not found in the 2019 samples", "We could not confirm it", "HTTP 503 from upstream",
           "status code: 404", "x error", "A long answer " * 60 + "not found", "fine result", "Unable to parse"]
check("10 Q91: Mentori's check gives the label it gave as copied (83a4091), on 14 inputs",
      all(exe._detect_error_in_result(t) == ns91["_detect_error_in_result"](t) for t in samples))
check("10 Q91: tool_error_text reads '[Error]' at the start, after smart_query's prefix",
      exe.tool_error_text("[Error] Query failed: x") and exe.tool_error_text(PREFIX + "[Error] Query failed: x")
      and not exe.tool_error_text(PREFIX + "Found 5 passages. [Error] later") and not exe.tool_error_text("fine")
      and not exe.tool_error_text(None))
with rc.run(ctx_for(item="Q91", sink=tmp / "r3_q91")):
    def rec91(text):
        evs = run(collect(exe.execute_step(step(), FakeRouter(lambda m, t: ""), session(),
                                           FakeMcp(lambda n, a, k: McpResult(text)), [])))
        return [e for e in evs if e["type"] == "_step_result"][0]["result"].to_record()
    a91 = rec91(PREFIX + "[Error] Query failed: timeout")
    b91 = rec91("The gene was not found in the 2019 samples")
    c91 = rec91(PREFIX + "Found 5 passages about the gene.")
    check("10 Q91: a tool error through smart_query keeps Mentori's label (success) and is flagged tool_error_text",
          a91["success"] and a91["tool_error_text"] and not a91["short_phrase_fired"] and a91["error_check_pattern"] is None)
    check("10 Q91: a short answer holding 'not found' keeps Mentori's label (failed) and is flagged short_phrase_fired",
          not b91["success"] and b91["short_phrase_fired"] and b91["error_check_pattern"] == "short_phrase"
          and not b91["tool_error_text"])
    check("10 Q91: an ordinary result carries neither flag",
          c91["success"] and not c91["tool_error_text"] and not c91["short_phrase_fired"])

# Q82: the stress trigger and the firing count
with rc.run(ctx_for(item="Q82", sink=tmp / "r3_q82")):
    def rec82(text, switches):
        fr = FakeRouter(lambda m, t: "SHORT")
        evs = run(collect(exe.execute_step(step(), fr, session(orchestrator_switches=switches),
                                           FakeMcp(lambda n, a, k: McpResult(text)), [])))
        return [e for e in evs if e["type"] == "_step_result"][0]["result"].to_record(), fr
    r, fr = rec82("S" * 8073, {})
    check("10 Q82: as built, an 8,073-character output is not distilled and is recorded under the threshold",
          r["distill"] is None and not r["over_distill_threshold"] and not fr.calls)
    r, fr = rec82("Z" * 210000, {"distiller": "off"})
    check("10 Q82: over the threshold is recorded under distiller off too",
          r["over_distill_threshold"] and r["distill"]["status"] == "switched_off" and not fr.calls)
    for variant, marker in (("on", "Summarize the observation above"), ("F1", "Here are examples of good distillations")):
        r, fr = rec82("S" * 8073, {"distiller": variant, "distiller_trigger": "every_step"})
        check(f"10 Q82 stress condition: every_step distils an 8,073-character output with prompt {variant!r}",
              r["distilled"] and r["distill"]["trigger"] == "every_step" and r["distill"]["variant"] == variant
              and not r["over_distill_threshold"] and len(fr.calls) == 1 and marker in fr.calls[0]["text"])
    r, fr = rec82("", {"distiller_trigger": "every_step"})
    check("10 Q82 stress condition: an empty output is not sent to the distiller", not fr.calls and r["distill"] is None)

fx = tmp / "q82_answers.json"
fx.write_text(json.dumps({"results": [
    {"answer_key": "k1", "generation": {"steps": [{"step_id": "step_1", "attempt_no": 1, "raw_content": "a" * 8073,
                                                   "over_distill_threshold": False, "distill": None}]}},
    {"answer_key": "k2", "generation": {"steps": [{"step_id": "step_1", "attempt_no": 1, "raw_content": "b" * 1200}]}},
    {"answer_key": "k3", "generation": {"error": "x"}}]}))
c82 = dfire.count(fx)
check("10 Q82 distiller_firing: zero steps over 209,712 characters, largest step output named",
      c82["threshold_chars"] == 209712 and c82["answers"] == 3 and c82["step_attempts"] == 2
      and c82["steps_over_threshold"] == 0 and not c82["distiller_fired_in_mentori_as_built"]
      and c82["largest_step_output"] == {"chars": 8073, "answer_key": "k1", "step_id": "step_1", "attempt_no": 1}, c82)
fx.write_text(json.dumps({"results": [{"answer_key": "k1", "generation": {"steps": [
    {"step_id": "step_1", "raw_content": "c" * 209713, "distill": {"status": "distilled"}}]}}]}))
c82 = dfire.count(fx)
check("10 Q82 distiller_firing: a record without the flag is counted from its raw_content length",
      c82["steps_over_threshold"] == 1 and c82["distiller_fired_in_mentori_as_built"]
      and c82["distill_status"] == {"distilled": 1})

# Q92: the memory defect kept and stated
check("10 Q92: memory as built (reads 'content'; unparsed) and the defect stated in the engine's record description",
      'response.get("content", "")' in inspect.getsource(mem) and "Q92" in eng.__doc__
      and "never uses the librarian's reply" in eng.__doc__)

# a misnamed switch stops the run
try:
    with rc.run(ctx_for(item="QSW", sink=tmp / "r3_sw")):
        run(collect(eng.orchestrated_chat(FakeRouter(script2()), GEN, [{"role": "user", "content": "q"}],
                                          session(task_id="tsw", orchestrator_switches={"supervisr": "off"}))))
    check("10 D52: a set-up with a misnamed switch stops the run (RunStop)", False)
except rr.RunStop as e:
    check("10 D52: a set-up with a misnamed switch stops the run (RunStop)", "supervisr" in str(e))

# Q93 through exp_03: the first unreachable tool server stops the run, the question stays to do
eng.sse_client = DeadSse
try:
    run(drive("full_orchestrator", DISPATCH))
    check("10 Q93 exp_03: an unreachable tool server stops the run", False)
except SystemExit as e:
    d93 = json.loads((ex.sink(x.run_id_for("full_orchestrator", x.DEFAULT_INDEX), root=root) / x.ANSWERS_FILE)
                     .read_text())
    check("10 Q93 exp_03: an unreachable tool server stops the run at the first question, recorded as a setup error",
          len(d93["setup_errors"]) == 1 and d93["completed_keys"] == [] and d93["results"] == []
          and "RunStop" in d93["setup_errors"][0]["error"] and "stopped" in str(e), str(e))
eng.sse_client = FakeSse

# Q94 (as built): a failure outside the answer (the save) stops the run
real_save = x.save_intermediate


def failing_save(*a, **k):
    raise OSError("disk full")


async def ok_behaviour(config, question, retriever, collection_name, router, user_id, index_name, task_id=None):
    return {"answer": "fine"}
x.save_intermediate = failing_save
try:
    run(drive("rlm_10", ok_behaviour))
    check("10 Q94: a failed save stops the run (not logged and skipped)", False)
except OSError as e:
    check("10 Q94: a failed save stops the run (not logged and skipped)", "disk full" in str(e))
x.save_intermediate = real_save

# ── 11. Round 4 (D78) ─────────────────────────────────────────────────────────────────────────────────────────
# Q128: a tool call whose connection closed checks the tool server once; RunStop when it does not answer
import anyio  # noqa: E402
from mcp.shared.exceptions import McpError  # noqa: E402
from mcp.types import CONNECTION_CLOSED, ErrorData  # noqa: E402
from backend.config import settings as mentori_settings  # noqa: E402

closed = McpError(ErrorData(code=CONNECTION_CLOSED, message="Connection closed"))
real_answers = exe._tool_server_answers
PROBES = []


def server_answers(up):
    async def fake(*a, **k):
        PROBES.append(up)
        return up
    return fake


with rc.run(ctx_for(item="Q128", sink=tmp / "r4_sink")):
    for err, label in ((closed, "McpError CONNECTION_CLOSED"), (anyio.ClosedResourceError(), "ClosedResourceError"),
                       (anyio.BrokenResourceError(), "BrokenResourceError")):
        PROBES.clear()
        exe._tool_server_answers = server_answers(False)
        try:
            run(collect(exe.execute_step(step(), FakeRouter(lambda m, t: ""), session(),
                                         FakeMcp(lambda n, a, k, e=err: e), [])))
            check(f"11 Q128: {label} with a tool server that does not answer raises RunStop", False)
        except rr.RunStop as e:
            check(f"11 Q128: {label} with a tool server that does not answer raises RunStop (checked once), the cause "
                  f"kept", PROBES == [False] and isinstance(e, rr.SetupError) and e.__cause__ is err
                  and "does not answer" in str(e), str(e))
    PROBES.clear()
    exe._tool_server_answers = server_answers(True)
    evs = run(collect(exe.execute_step(step(), FakeRouter(lambda m, t: ""), session(), FakeMcp(lambda n, a, k: closed),
                                       [])))
    res128 = [e for e in evs if e["type"] == "_step_result"][0]["result"]
    check("11 Q128: a closed connection with a tool server that answers keeps Mentori's recovery (a failed step)",
          PROBES == [True] and [e["type"] for e in evs if e["type"] == "step_failed"] == ["step_failed"]
          and res128.success is False and "Connection closed" in (res128.error or ""), [e["type"] for e in evs])
    PROBES.clear()
    exe._tool_server_answers = server_answers(False)
    evs = run(collect(exe.execute_step(step(), FakeRouter(lambda m, t: ""), session(),
                                       FakeMcp(lambda n, a, k: ValueError("bad argument")), [])))
    check("11 Q128: any other error keeps Mentori's recovery and checks no server",
          PROBES == [] and any(e["type"] == "step_failed" for e in evs)
          and not exe._transport_error(McpError(ErrorData(code=-32602, message="invalid params"))))
    exe._tool_server_answers = real_answers


# The check itself: GET /sse answers 200 with the endpoint event (a dead port, a server that sends it, one that does not)
async def _sse_stub(lines):
    async def handle(reader, writer):
        await reader.readuntil(b"\r\n\r\n")
        writer.write(b"HTTP/1.1 200 OK\r\ncontent-type: text/event-stream\r\ncache-control: no-cache\r\n\r\n"
                     + "".join(f"{x}\r\n" for x in lines).encode())
        await writer.drain()
        await asyncio.sleep(0.5)
        writer.close()
    return await asyncio.start_server(handle, "127.0.0.1", 0)


async def _probe(lines):
    srv = await _sse_stub(lines)
    port = srv.sockets[0].getsockname()[1]
    mentori_settings.TOOL_SERVER_URL = f"http://127.0.0.1:{port}"
    try:
        return await exe._tool_server_answers(timeout_s=2.0)
    finally:
        srv.close()


url_before = mentori_settings.TOOL_SERVER_URL
try:
    up = run(_probe(["event: endpoint", "data: /messages/?session_id=x", ""]))
    silent = run(_probe([": ping"] * 6))
    with __import__("socket").socket() as so:
        so.bind(("127.0.0.1", 0))
        dead_port = so.getsockname()[1]
    mentori_settings.TOOL_SERVER_URL = f"http://127.0.0.1:{dead_port}"
    dead = run(exe._tool_server_answers(timeout_s=2.0))
finally:
    mentori_settings.TOOL_SERVER_URL = url_before
check("11 Q128: the check answers True for GET /sse with the endpoint event, False without it and on a closed port",
      up is True and silent is False and dead is False, f"up {up} silent {silent} dead {dead}")

# ── 12. D79 Q135 (O1): a stop leaves orchestrated_chat unwrapped ─────────────────────────────────────────────────
import socket  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
from mcp import ClientSession as RealClientSession  # noqa: E402
from mcp.client.sse import sse_client as real_sse_client  # noqa: E402


async def through(exc):
    """What leaves the engine's unwrapping when `exc` is raised inside it."""
    try:
        async with eng._stop_unwrapped():
            raise exc
    except BaseException as e:
        return e


def leaves(e):
    return [x for s in e.exceptions for x in leaves(s)] if isinstance(e, BaseExceptionGroup) else [e]


stop = rr.RunStop("tool server: gone")
g = ExceptionGroup("outer", [ExceptionGroup("inner", [stop])])
out = run(through(g))
check("12 Q135: a stop nested in two groups leaves as itself, the group its cause, its traceback kept",
      out is stop and out.__cause__ is g and "through" in [f.name for f in traceback.extract_tb(out.__traceback__)])
for cls in (rr.ToolRefusal, rr.SetupError, LockError, rc.RunContextError):
    s = cls("x")
    check(f"12 Q135: a lone {cls.__name__} in a group leaves as itself", run(through(ExceptionGroup("g", [s]))) is s)
s, c = rr.RunStop("y"), ConnectionError("refused")
s.__cause__ = c
g = ExceptionGroup("g", [s])
out = run(through(g))
check("12 Q135: a stop with its own cause keeps it; the group is its context",
      out is s and out.__cause__ is c and out.__context__ is g)
for label, g in (("two stops", ExceptionGroup("g", [rr.RunStop("a"), rr.ToolRefusal("b")])),
                 ("a stop and another error", ExceptionGroup("g", [rr.RunStop("a"), OSError("b")])),
                 ("a nested stop and another error", ExceptionGroup("g", [ExceptionGroup("i", [rr.RunStop("a")]),
                                                                          OSError("b")])),
                 ("one error that is no stop", ExceptionGroup("g", [ValueError("v")])),
                 ("a KeyboardInterrupt", BaseExceptionGroup("g", [KeyboardInterrupt()]))):
    check(f"12 Q135: a group of {label} leaves unchanged", run(through(g)) is g)
s = rr.RunStop("plain")
check("12 Q135: a stop not in a group leaves unchanged, no cause added", run(through(s)) is s and s.__cause__ is None)


# The engine on fakes that are anyio task groups, as mcp's sse_client and ClientSession are
def fails_on_cancel():
    async def child():
        try:
            await anyio.sleep_forever()
        except anyio.get_cancelled_exc_class():
            raise OSError("stream reader failed")
    return child


class GroupSse(FakeSse):
    child = None   # a task started in the group; fails_on_cancel() makes a second leaf

    async def __aenter__(self):
        self.tg = anyio.create_task_group()
        await self.tg.__aenter__()
        if GroupSse.child:
            self.tg.start_soon(GroupSse.child)
        return (None, None)

    async def __aexit__(self, *a):
        return await self.tg.__aexit__(*a)


class GroupClientSession(FakeClientSession):
    async def __aenter__(self):
        self.tg = anyio.create_task_group()
        await self.tg.__aenter__()
        return self

    async def __aexit__(self, *a):
        return await self.tg.__aexit__(*a)


async def caught(agen):
    seen = []
    try:
        async for e in agen:
            seen.append(e)
    except BaseException as e:
        return seen, e
    return seen, None


def engine_caught(task_id, router=None):
    with rc.run(ctx_for(item=task_id, sink=tmp / "q135_sink")):
        return run(caught(eng.orchestrated_chat(router or FakeRouter(engine_script("A")), GEN,
                                                [{"role": "user", "content": "What is X?"}],
                                                session(task_id=task_id, workspace_path=str(tmp / f"ws_{task_id}")))))


eng.sse_client, eng.ClientSession = GroupSse, GroupClientSession
FakeClientSession.tool_reply = lambda n, a: McpResult(
    f"Error executing tool smart_query: {TOOL_REFUSAL_MARKER} LockError: x", True)
_, e135 = engine_caught("t135a")
check("12 Q135: a refusal inside a tool leaves orchestrated_chat as ToolRefusal through two task groups",
      type(e135) is rr.ToolRefusal and isinstance(e135.__cause__, BaseExceptionGroup)
      and leaves(e135.__cause__) == [e135], repr(e135))
GroupSse.child = fails_on_cancel()
_, e135 = engine_caught("t135b")
GroupSse.child = None
check("12 Q135: a refusal beside another error leaves as the group, both leaves in it",
      isinstance(e135, BaseExceptionGroup) and sorted(type(x).__name__ for x in leaves(e135))
      == ["OSError", "ToolRefusal"], repr(e135))


class FailingTaskManager:
    def is_cancelled(self, task_id):
        raise KeyError("task table")
eng._get_task_manager = lambda: FailingTaskManager()
_, e135 = engine_caught("t135c")
eng._get_task_manager = lambda: NoCancel()
check("12 Q135: an error that is no stop leaves as before, in its group",
      isinstance(e135, BaseExceptionGroup) and [type(x) for x in leaves(e135)] == [KeyError], repr(e135))

# A real FastMCP SSE tool server, on a free local port, killed while smart_query is in flight
SERVER = tmp / "q135_tool_server.py"
SERVER.write_text(
    "import sys, pathlib, anyio\n"
    "from mcp.server.fastmcp import FastMCP\n"
    "port, marker = int(sys.argv[1]), pathlib.Path(sys.argv[2])\n"
    "srv = FastMCP('q135', host='127.0.0.1', port=port, log_level='WARNING')\n"
    "@srv.tool()\n"
    "async def smart_query(query: str = '', index_name: str = '') -> str:\n"
    "    marker.write_text('in flight')\n"
    "    await anyio.sleep(120)\n"
    "    return 'never'\n"
    "srv.run(transport='sse')\n")


def free_port():
    while True:
        with socket.socket() as so:
            so.bind(("127.0.0.1", 0))
            port = so.getsockname()[1]
        if port != 11434:
            return port


def start_tool_server():
    """The server, answering GET /sse; a thread kills it (SIGKILL) once its smart_query is in flight."""
    port = free_port()
    marker = tmp / f"q135_in_flight_{port}"
    proc = subprocess.Popen([sys.executable, str(SERVER), str(port), str(marker)], stdout=subprocess.DEVNULL,
                            stderr=open(tmp / f"q135_server_{port}.log", "w"))
    mentori_settings.TOOL_SERVER_URL = f"http://127.0.0.1:{port}"
    deadline = time.time() + 60
    while not run(exe._tool_server_answers(timeout_s=1.0)):
        if proc.poll() is not None or time.time() > deadline:
            proc.kill()
            raise RuntimeError(f"Q135 tool server on port {port} did not start: {tmp}/q135_server_{port}.log")
        time.sleep(0.2)

    def kill_in_flight():
        while not marker.exists() and proc.poll() is None:
            time.sleep(0.05)
        proc.kill()
    threading.Thread(target=kill_in_flight, daemon=True).start()
    return proc


eng.sse_client, eng.ClientSession = real_sse_client, RealClientSession
url_before = mentori_settings.TOOL_SERVER_URL
proc = start_tool_server()
try:
    _, e135 = engine_caught("t135d")
finally:
    proc.kill()
    proc.wait()
check("12 Q135 real SSE: a tool server killed mid-call leaves orchestrated_chat as RunStop, unwrapped, McpError "
      "CONNECTION_CLOSED its cause",
      type(e135) is rr.RunStop and isinstance(e135.__cause__, McpError)
      and e135.__cause__.error.code == CONNECTION_CLOSED and isinstance(e135.__context__, BaseExceptionGroup)
      and "execute_step" in [f.name for f in traceback.extract_tb(e135.__traceback__)]
      and "RunStop" in "".join(traceback.format_exception(e135)), repr(e135))

real_router = x.ModelRouter
x.ModelRouter = lambda: FakeRouter(engine_script("A"))
proc = start_tool_server()
try:
    run(drive("orch_no_distiller", DISPATCH))
    check("12 Q135 real SSE exp_03: a tool server killed mid-call stops the run", False)
except SystemExit as e:
    d135 = json.loads((ex.sink(x.run_id_for("orch_no_distiller", x.DEFAULT_INDEX), root=root) / x.ANSWERS_FILE)
                      .read_text())
    check("12 Q135 real SSE exp_03: a tool server killed mid-call is a setup error and stops the run at the first "
          "question, no answer stored",
          len(d135["setup_errors"]) == 1 and d135["setup_errors"][0]["error"].startswith("RunStop: tool server:")
          and d135["completed_keys"] == [] and d135["results"] == [] and "stopped" in str(e),
          d135["setup_errors"] or d135["results"][:1])
finally:
    proc.kill()
    proc.wait()
    x.ModelRouter = real_router
    mentori_settings.TOOL_SERVER_URL = url_before
    eng.sse_client, eng.ClientSession = FakeSse, FakeClientSession

# ── 13. D83 Q147: --question-ids and the smoke's rule ───────────────────────
import contextlib  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402


class QArgs:
    index = x.DEFAULT_INDEX
    max_questions = None
    draws = [1]
    configs = ["raw_gemini", "full_orchestrator"]
    sink_root = tmp / "q147_dry"

    def __init__(self, ids=None, max_questions=None):
        self.question_ids, self.max_questions = ids, max_questions


_key_order = [q["id"] for q in ex.questions()]
_got = [q["id"] for q in x._questions(QArgs(["OOD_002", "01_sarek_TE3", "OOD_001", "01_sarek_CO2"]))]
check("13 Q147: --question-ids asks the named questions in the key's order, whatever the order named",
      _got == ["01_sarek_CO2", "01_sarek_TE3", "OOD_001", "OOD_002"]
      and _got == [i for i in _key_order if i in set(_got)], _got)
check("13 Q147: without --question-ids or --max-questions the run asks all 135",
      [q["id"] for q in x._questions(QArgs())] == _key_order and len(_key_order) == 135)


def _refusal(args):
    try:
        x._questions(args)
    except SystemExit as e:
        return str(e)
    return None


_r = [_refusal(QArgs(["NOPE", "01_sarek_CO2"])), _refusal(QArgs(["OOD_001", "OOD_001"])),
      _refusal(QArgs(["OOD_001"], max_questions=2))]
check("13 Q147: an unknown id, an id named twice and --question-ids with --max-questions are refused",
      _r[0] is not None and "NOPE" in _r[0] and _r[1] is not None and "OOD_001" in _r[1].split("];")[-1]
      and _r[2] is not None and "one way" in _r[2], _r)
_src = inspect.getsource(x.main)
check("13 Q147: the CLI defines --question-ids (one or more ids)",
      'parser.add_argument("--question-ids", nargs="+"' in _src)
_spec = importlib.util.spec_from_file_location("g3_smoke_ids", ROOT / "findings/recompute/G3_runs/smoke_ids.py")
smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(smoke)
_sq = smoke.smoke_questions()
_first_a = [q["id"] for q in ex.questions() if q["answerable"]][:3]
_first_n = [q["id"] for q in ex.questions() if not q["answerable"]][:2]
check("13 Q147: the smoke's rule gives the first 3 answerable and the first 2 not-answerable questions, as stated",
      [q["id"] for q in _sq] == _first_a + _first_n == list(smoke.EXPECTED)
      and [q["answerable"] for q in _sq] == [True, True, True, False, False], [q["id"] for q in _sq])
_out = io.StringIO()
with contextlib.redirect_stdout(_out):
    x.run_dry(QArgs(list(smoke.EXPECTED)))
_lines = _out.getvalue().splitlines()
check("13 Q147: a dry run with the smoke's ids lists 5 answers per config, draw 1, writing nothing",
      sum(1 for ln in _lines if ln.strip().startswith("todo ")) == 10
      and all(f"|{i}|d1" in _out.getvalue() for i in smoke.EXPECTED) and not (tmp / "q147_dry").exists(),
      _lines[:3])

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
