"""mentori-cli ask: from the config and the command line to the paper's strategy functions, and back to a record.

    resolve()   the run's settings (model, strategy, switches, paths); refuses a switch the strategy does not have
    dispatch()  calls the paper's strategy function with those settings (exp_01's dispatch, written for one question)
    ask()       departures from the lock, --strict, keys, prompts, the run, the records
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

from mentori_cli import __version__, config as cfgmod, lockfx, paths, prompts as pr

EXPERIMENT = "mentori_cli"
PAPER_VERIFIER = "ollama::gpt-oss:20b"          # exp_01_generation.py VERIFY_MODEL, PipelineConfig.verify_model
QID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ORCH_SWITCH_KEYS = ("analyser", "planner", "supervisor", "synthesiser", "distiller", "distiller_trigger")
ORCH_DEFAULTS = {"analyser": "on", "planner": "on", "supervisor": "on", "synthesiser": "on", "distiller": "on",
                 "distiller_trigger": "threshold"}


class Refused(SystemExit):
    def __init__(self, msg: str):
        super().__init__(f"mentori-cli: REFUSED: {msg}")


def resolve(cfg: dict, *, strategy=None, off=(), rlm_turns=None, prompts_dir=None, model=None, strict=None,
            draw=None) -> dict:
    """The run's settings from the config file, with the command line's options over it."""
    provider, name = model if model else (cfg["model"]["provider"], cfg["model"]["name"])
    strategy = strategy or cfg["run"]["strategy"]
    if strategy not in cfgmod.STRATEGIES:
        raise Refused(f"--strategy {strategy!r}: one of {', '.join(cfgmod.STRATEGIES)}")
    comps = dict(cfg["components"])
    for o in off:
        if o not in cfgmod.OFF_NAMES:
            raise Refused(f"--off {o!r}: one of {', '.join(cfgmod.OFF_NAMES)}")
        comps[o] = "off"
    bad = [k for k in cfgmod.ORCH_COMPONENTS + ("distiller_trigger",) if comps[k] != ORCH_DEFAULTS[k]
           and strategy != "orchestrator"]
    bad += [k for k in cfgmod.RLM_COMPONENTS if comps[k] != "on" and strategy != "rlm"]
    if bad:
        raise Refused(f"{', '.join(bad)} switched off or changed, and strategy {strategy} has no such component "
                      f"({', '.join(cfgmod.ORCH_COMPONENTS)}: orchestrator; {', '.join(cfgmod.RLM_COMPONENTS)}: rlm)")
    turns = rlm_turns if rlm_turns is not None else cfg["run"]["rlm_turns"]
    if rlm_turns is not None and strategy != "rlm":
        raise Refused("--rlm-turns is for strategy rlm")
    if not 1 <= turns <= 100:
        raise Refused("--rlm-turns: from 1 to 100")
    draw_n = draw if draw is not None else cfg["run"]["draw"]
    if isinstance(draw_n, bool) or not isinstance(draw_n, int) or not 1 <= draw_n <= 999:
        raise Refused(f"--draw {draw_n!r}: from 1 to 999 (the lock's draw numbers; the draw is the seed)")
    gen_name = lockfx.ollama_tag(name) if provider == "ollama" else name
    ident = f"{provider}::{gen_name}"
    models_list = lockfx.models_of(cfg, provider, name, strategy)
    arm = f"rlm_{turns}" if strategy == "rlm" else strategy
    models = {"generator": ident}
    servers = None
    verifier = None
    if strategy == "verified_pass":
        v = models_list[1]
        verifier = f"{v['provider']}::{v['name']}"
        models["verifier"] = verifier
        if v["provider"] == "ollama" and v["url"].rstrip("/") != cfg["model"]["server_url"].rstrip("/"):
            servers = {v["name"]: v["url"]}
    if verifier == ident and servers:
        raise Refused("the verifier is the generator's model on another server; one model goes to one server")
    pdir = prompts_dir if prompts_dir is not None else cfgmod.resolve_path(cfg, cfg["run"]["prompts_dir"])
    return {
        "provider": provider, "name": gen_name, "ident": ident, "server_url": cfg["model"]["server_url"],
        "api_key_env": cfg["model"]["api_key_env"], "models_list": models_list, "models": models,
        "servers": servers, "verifier": verifier, "strategy": strategy, "arm": arm, "rlm_turns": turns,
        "components": comps,
        "switches": {k: comps[k] for k in ORCH_SWITCH_KEYS if comps[k] != ORCH_DEFAULTS[k]},
        "quality_gate": comps["rlm_gate"] == "on", "search_tools": comps["rlm_search"] == "on",
        "draw": draw_n,
        "thinking": cfg["run"]["thinking"], "sampling": dict(cfg["sampling"]),
        "strict": cfg["run"]["strict"] if strict is None else strict,
        "store": cfgmod.resolve_path(cfg, cfg["corpus"]["store"]), "index": cfg["corpus"]["index"],
        "out_dir": cfgmod.resolve_path(cfg, cfg["run"]["out_dir"]),
        "prompts_dir": None if pdir is None else Path(pdir),
    }


async def dispatch(st: dict, question: str, mods, retriever, collection_name: str, router, user_id: str,
                   task_id: str | None):
    """One answer by the paper's strategy function for st["strategy"], with the run's switches (exp_01's
    _run_config and exp_03's dispatch_config, for one question). Returns what the function returns."""
    s, gen = st["strategy"], st["ident"]
    if s == "single_pass":
        return await mods.single_pass(question, retriever, collection_name, router, gen)
    if s == "multi_hop":
        return await mods.multi_hop(question, retriever, collection_name, router, gen)
    if s == "rlm":
        return await mods.rlm(question, router, gen, user_id, max_turns=st["rlm_turns"], config_name=st["arm"],
                              index_name=st["index"], quality_gate=st["quality_gate"],
                              search_tools=st["search_tools"])
    if s == "verified_pass":
        return await mods.verified_pass(question, retriever, collection_name, router, gen)
    if s == "orchestrator":
        return await mods.orchestrator(question, user_id, st["index"], task_id, dict(st["switches"]),
                                       collection_name=collection_name)
    raise Refused(f"strategy {s!r}")


def read_questions(question: str | None, questions_file: Path | None) -> list[dict]:
    """[{"id", "question"}]: one question (id q1), or one per line of a JSONL file ({"question": ..., "id": ...};
    id optional, q1, q2, ... by line)."""
    if (question is None) == (questions_file is None):
        raise Refused("give one question, or --questions FILE.jsonl, not both")
    if question is not None:
        if not question.strip():
            raise Refused("the question is empty")
        return [{"id": "q1", "question": question}]
    out, seen = [], set()
    for n, line in enumerate(Path(questions_file).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as e:
            raise Refused(f"{questions_file}:{n} is not JSON ({e})") from None
        q = rec.get("question") if isinstance(rec, dict) else None
        if not isinstance(q, str) or not q.strip():
            raise Refused(f"{questions_file}:{n} has no \"question\"")
        qid = str(rec.get("id") or f"q{len(out) + 1}")
        if not QID.match(qid) or qid in seen:
            raise Refused(f"{questions_file}:{n}: id {qid!r} is not a short name (letters, digits, . _ -) or is "
                          f"used twice")
        seen.add(qid)
        out.append({"id": qid, "question": q})
    if not out:
        raise Refused(f"{questions_file} holds no question")
    return out


def check_keys(st: dict, environ=os.environ) -> str | None:
    """A cloud model's key: present in the environment variable the config names (its NAME only), copied into the
    name the paper's client reads when the two differ. The keys file is never read (inject.block_keys_file). Returns
    the variable's name, never its value."""
    need = {st["provider"]} | ({st["verifier"].split("::")[0]} if st["verifier"] else set())
    used = None
    for provider in sorted(need & set(cfgmod.KEY_ENV)):
        std = cfgmod.KEY_ENV[provider]
        name = (st["api_key_env"] if provider == st["provider"] else "") or std
        if not environ.get(name):
            raise Refused(f"{provider} needs its API key in the environment variable {name} (export {name}=...); "
                          f"the key is never read from a file")
        if name != std:
            environ[std] = environ[name]
        used = name
    return used


def _jsonable(x):
    if is_dataclass(x):
        x = asdict(x)
    return json.loads(json.dumps(x, default=repr))


SENT_KEYS = ("provider", "model", "role", "draw", "candidate", "status", "stop_reason", "options_sent", "fields_sent",
             "model_digest", "server", "ollama_version", "lock_sha256", "prompt_tokens", "output_tokens",
             "thinking_tokens", "wall_s", "error")


def settings_sent(calls: list[dict]) -> list[dict]:
    """Per model call: what was sent (options and fields) and how it ended; prompts and messages left out."""
    return [{k: c.get(k) for k in SENT_KEYS if k in c} for c in calls]


def build_record(q: dict, result: dict, st: dict, lock_info: dict, prompt_info: dict) -> dict:
    gen = _jsonable(result["gen"])
    return {
        "tool": f"mentori-cli {__version__}",
        "question_id": q["id"], "question": q["question"],
        "answer": gen.get("answer") or "",
        "error": gen.get("error"),
        "stop_reason": gen.get("stop_reason") or gen.get("plan_status"),
        "strategy": st["strategy"], "arm": st["arm"],
        "rlm_turns": st["rlm_turns"] if st["strategy"] == "rlm" else None,
        "components": {k: st["components"][k] for k in
                       (ORCH_SWITCH_KEYS if st["strategy"] == "orchestrator"
                        else ("rlm_gate", "rlm_search") if st["strategy"] == "rlm" else ())},
        "reranker": "on (always, as in the paper: D40)",
        "models": dict(st["models"]), "draw": st["draw"],
        "departs_from_lock": list(lock_info["departures"]),
        "lock": {"paper_sha256": lock_info["paper_sha256"], "run_sha256": lock_info["run_sha256"],
                 "path": lock_info["path"]},
        "prompts": {"dir": prompt_info["dir"], "edited": list(prompt_info["edited"]),
                    "sha256": dict(prompt_info["sha256"])},
        "settings_sent": settings_sent(result["calls"]),
        "n_model_calls": len(result["calls"]),
        "sources": result["sources"],
        "store": str(st["store"]), "index": st["index"],
        "run_id": result["run_id"], "sink": result["sink"],
    }


def plan_lock(st: dict, server_state=lockfx.fetch_server_state) -> dict:
    """The lock the run sends and its departures; reads each Ollama server's version and tags (no model call)."""
    raw, paper_d = lockfx.paper_lock(paths.lock_path())
    urls = sorted({m["url"] for m in st["models_list"] if m["provider"] == "ollama"})
    states = {u: server_state(u) for u in urls}
    d, dep = lockfx.effective(paper_d, st["models_list"], st["sampling"], st["thinking"], states)
    import hashlib
    paper_sha = hashlib.sha256(raw).hexdigest()
    run_sha = lockfx.run_sha256(raw, d) if dep else paper_sha
    return {"d": d, "departures": dep, "paper_sha256": paper_sha, "run_sha256": run_sha,
            "path": str(paths.lock_path()), "install": {"d": d, "sha256": run_sha} if dep else None}


GEMINI_WARNING = "Warning: No Gemini API Key provided."   # backend/agents/models/gemini.py, printed by every
                                                          # ModelRouter() when GEMINI_API_KEY is unset


def uses_gemini(st: dict) -> bool:
    return st["provider"] == "gemini" or bool(st["verifier"] and st["verifier"].startswith("gemini::"))


class _GeminiWarningFilter:
    """Stands in for sys.stdout during a run: the paper's Gemini warning line is dropped when no model of the run is
    a Gemini model, and sent to stderr when one is. Every other byte goes to stdout unchanged. The paper's code is
    not changed; only where its printed line goes."""

    def __init__(self, stream, gemini: bool):
        self._s, self._gemini, self._buf = stream, gemini, ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._emit(line + "\n")
        return len(text)

    def _emit(self, line: str) -> None:
        if line.rstrip("\n") == GEMINI_WARNING:
            if self._gemini:
                print(GEMINI_WARNING, file=sys.stderr)
            return
        self._s.write(line)

    def flush(self) -> None:
        if self._buf:
            self._emit(self._buf)
            self._buf = ""
        self._s.flush()

    def __getattr__(self, name):
        return getattr(self._s, name)


class gemini_warning_filtered:
    def __init__(self, st: dict):
        self.gemini = uses_gemini(st)

    def __enter__(self):
        self._old = sys.stdout
        sys.stdout = _GeminiWarningFilter(self._old, self.gemini)
        return self

    def __exit__(self, *exc):
        try:
            sys.stdout.flush()
        finally:
            sys.stdout = self._old
        return False


def ask(cfg: dict, questions: list[dict], *, engine=None, server_state=lockfx.fetch_server_state, out=print,
        environ=os.environ, **opts) -> list[dict]:
    """Answers each question; prints the answer and its JSON record; returns the records."""
    st = resolve(cfg, **opts)
    lock_info = plan_lock(st, server_state)
    if lock_info["departures"]:
        if st["strict"]:
            raise Refused("--strict: this run departs from the paper's lock:\n  " + "\n  ".join(lock_info["departures"])
                          + "\nnothing was sent (run without --strict to run it and mark each record)")
        for line in lock_info["departures"]:
            print(line, file=sys.stderr)
    check_keys(st, environ)
    if engine is None:
        from mentori_cli.engine import MentoriEngine
        engine = MentoriEngine()
    with gemini_warning_filtered(st):
        engine.prepare(st)
        prompt_info = pr.load(st["prompts_dir"], engine.paper_prompts())
        spec = {"lock": lock_info["install"],
                "prompts": {k: prompt_info["used"][k] for k in prompt_info["edited"]},
                "verifier": st["verifier"] if st["verifier"] and st["verifier"] != PAPER_VERIFIER else None}
        engine.install(spec)
        results = asyncio.run(engine.run(questions, st, spec))
    records = []
    for q, result in zip(questions, results):
        rec = build_record(q, result, st, lock_info, prompt_info)
        engine.store_record(result, rec)
        records.append(rec)
        out(f"\n=== {q['id']}: {q['question']}\n")
        out(rec["answer"] if rec["answer"] else f"(no answer: {rec['error']})")
        out("\n--- record")
        out(json.dumps(rec, indent=1, ensure_ascii=False))
    return records
