#!/usr/bin/env python3
"""
Figure 6: the coder benchmark, every attempt re-run under the lock (D50, D63, D66, D67)

The V2-8 coder benchmark (objective pass/fail against ground truth, exp_v2_8_coder_benchmark.py) runs every
attempt under experiments/LOCK.toml: the 20 operations of coder_ground_truth.json x 11 configs x each variant
x the draws of Figure 6 (one, D49). No result is copied from an earlier run (D50).

VARIANTS. The ten models of Figure 6 (FIG6_MODELS, D63), each at every thinking setting the lock gives it:
off and default ([thinking]: Figure 6), and the levels of [sampling.thinking_levels] (gpt-oss:20b low, medium
and high; D56). Two settings that send the same request (the seed aside) are one variant, named by the first of
the model's levels, default, off. So a model without a thinking mode, and deepseek-r1 (it always thinks), run
once; gpt-oss:20b runs at low (its off), medium (its default) and high; the others at default and off.
variants() reads this from the lock, and --dry-run prints the list with its attempt count. Each attempt stores its
variant's thinking and thinking_same_as (gpt-oss:20b low: ["off"]), so Figure 6's off and default are read from the
answers.

RUNS. One run per (config, variant): run_id exp_05__<config>__<model>+<thinking>, sink findings/runs/<run_id>/
(calls.jsonl, ctx/, run_identity.json, and answers.json, the run's attempts so far). Each (operation, draw) runs
under its own run context: item_id the operation, the draw, the variant's thinking; the model under test is the
run's coder role, and the lock's judge is allowed as judge (the soft-pass judge). An attempt is keyed
answer_key(config, op_id, draw). The operations are read only when coder_ground_truth.json has the sha256
pinned here, and every data file they name must be in the datasets folder before anything runs.

Usage (from experiments/mentori):
    # The work list and its attempt count; no model call, no sink
    uv run --project . --frozen python publication/scripts/exp_05_coder_benchmark.py --dry-run

    # One variant
    uv run --project . --frozen python publication/scripts/exp_05_coder_benchmark.py \\
        --model ollama::gpt-oss:20b --thinking high --base-url http://127.0.0.1:21441

    # Every thinking setting of one model, 3 operations only (smoke test)
    uv run --project . --frozen python publication/scripts/exp_05_coder_benchmark.py \\
        --model ollama::qwen3-coder:30b --max-ops 3 --base-url http://127.0.0.1:21441

    # Continue the runs of a variant whose sinks hold attempts
    uv run --project . --frozen python publication/scripts/exp_05_coder_benchmark.py \\
        --model ollama::qwen3-coder:30b --resume --base-url http://127.0.0.1:21441

    # Every variant, one after another (resumes)
    uv run --project . --frozen python publication/scripts/exp_05_coder_benchmark.py \\
        --run-all --base-url http://127.0.0.1:21441

LENGTH STOPS (D114 Q29 O2, which replaces D112 Q8's step rule). --length-stop names what an attempt does after a
length stop: "retry" (the default, the code as submitted and as every variant before D114 ran) or "stop" (the attempt
ends at its first length stop, in every config, and is recorded with exec_outcome "length"; see
exp_v2_8_coder_benchmark.LENGTH_STOP). The variant's launcher passes it. Every attempt stores the rule it ran under
(length_stop_rule; attempts stored before the flag existed have none and ran under "retry") and, under "stop", the
length_stop that ended it. Under "stop" each of the variant's sinks it runs gets the file LENGTH_STOP_MARKER (the
D114 deploy writes it into the variant's sinks before the variant is stopped). A variant is refused under "retry" when
any of its sinks, of every config whatever --configs names, holds that file or an attempt stored under "stop"
(check_length_rule; review of 22 October, 1 and 3), so this code never moves a variant back to "retry". The
launchers of the D75 clone refuse such a variant too (run_s2_variant_d101.sh). S447 applies the same rule to every
variant's stored attempts, whichever rule they ran under.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default TOOL_SERVER_URL to localhost when running outside Docker
if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

# Import V2-8 core functions
import tests.experiments_v2.exp_v2_8_coder_benchmark as v28
from tests.experiments_v2.exp_v2_8_coder_benchmark import (
    CONFIG_NAMES,
    ALL_DATASETS,
    ALL_COMPLEXITIES,
    CODER_ROLE,
    _model_slug,
    _dispatch,
    load_ground_truth_ops,
)

from tests.experiments.exp_common import (
    load_intermediate,
    save_intermediate,
)

from backend.agents.model_router import ModelRouter
from backend.agents.lock_adapter import LockCallError
from backend.agents.notebook import import_scan

# exp_v2_8 imports backend.agents.lock_adapter, which puts the repository root on sys.path
from experiments.runner import experiment as ex
from experiments.runner import run_context as rc
from experiments.runner.lock import LockError, load as load_lock

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_05_coder_benchmark")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

V4_RESULTS_DIR = Path(__file__).parent / "results_v4"
V2_RESULTS_DIR = Path(__file__).parent.parent / "experiments_v2" / "results_v2"

EXPERIMENT = "exp_05"
FIGURE = 6
N_TASKS = 20                     # LIST.md, Figure 6: 10 RNA-seq and 10 survival operations
GT_SHA256 = "afcef9ffea67b2ea1659dad7513948693027648f02f887e6db4e07f6ca3b9c35"   # Mentori-paper 83a4091's file
ANSWERS_FILE = "answers.json"    # <sink>/answers.json: the run's attempts so far, read back by --resume

# The ten models of Figure 6 (D63), as the lock names them
FIG6_MODELS = (
    "ollama::qwen3-coder:30b",            # the submission ran qwen3-coder:latest
    "ollama::qwen3-coder-next:q4_K_M",
    "ollama::gpt-oss:20b",                # sent as gpt-oss:20b-date20261010 ([date], D55)
    "ollama::glm-4.7-flash:bf16",         # D61, D64
    "ollama::nemotron-3-nano:30b",
    "ollama::gemma3:27b",
    "ollama::devstral-small-2:24b",
    "ollama::deepseek-r1:70b",
    "gemini::gemini-2.5-pro",
    "gemini::gemini-3-flash-preview",
)


# ─────────────────────────────────────────────────────────────
# Variants, operations and the work list
# ─────────────────────────────────────────────────────────────

def _split(ident: str) -> Tuple[str, str]:
    """(provider, model name) of a Mentori model identifier."""
    provider, sep, name = ident.partition("::")
    if not sep or provider not in ex.PROVIDERS or not name:
        raise ex.ExperimentError(f"{ident!r}: write 'ollama::<tag>' or 'gemini::<model>'")
    return provider, name


def _sent(lock, ident: str, thinking: str) -> Dict[str, Any]:
    """What the lock sends for ident at this thinking setting, the seed left out (the seed is the draw's)."""
    provider, name = _split(ident)
    if provider == "gemini":
        return {k: v for k, v in lock.gemini(name, 1, thinking=thinking).items() if k != "seed"}
    call = lock.ollama(name, role="generator", draw=1, thinking=thinking)
    return {"model": call.model, "fields": dict(call.fields), "system": call.system,
            "options": {k: v for k, v in call.options.items() if k != "seed"}}


def variants(models=FIG6_MODELS) -> List[Dict[str, Any]]:
    """Every (model, thinking) variant of Figure 6, read from the lock (see the module docstring, VARIANTS). Each is
    {model, thinking, same_as (the settings that send the same request), sent, extra (the run_id part)}."""
    lock = load_lock()
    levels = lock.d["sampling"].get("thinking_levels", {})
    out = []
    for ident in models:
        _, name = _split(ident)
        kept: List[Tuple[Dict, Dict]] = []
        for thinking in [*levels.get(name, []), "default", "off"]:
            sent = _sent(lock, ident, thinking)
            twin = next((v for s, v in kept if s == sent), None)
            if twin is not None:
                twin["same_as"].append(thinking)
                continue
            v = {"model": ident, "thinking": thinking, "same_as": [], "sent": sent,
                 "extra": f"{name.replace(':', '-')}+{thinking}"}
            kept.append((sent, v))
            out.append(v)
    return out


def select(all_variants: List[Dict], model: Optional[str] = None, thinking: Optional[str] = None) -> List[Dict]:
    """The variants of model (every model when None), or its one variant at thinking."""
    chosen = [v for v in all_variants if model is None or v["model"] == model]
    if not chosen:
        raise ex.ExperimentError(f"{model!r} is not a Figure 6 model ({', '.join(FIG6_MODELS)})")
    if thinking is None:
        return chosen
    hit = [v for v in chosen if v["thinking"] == thinking]
    if hit:
        return hit
    twin = [v for v in chosen if thinking in v["same_as"]]
    if twin:
        raise ex.ExperimentError(f"{model} at thinking {thinking!r} sends what {twin[0]['thinking']!r} sends: "
                                 f"run --thinking {twin[0]['thinking']}")
    raise ex.ExperimentError(f"{model}: no thinking setting {thinking!r}; its variants are "
                             f"{', '.join(v['thinking'] for v in chosen)}")


def load_ops(max_ops: Optional[int] = None) -> List[Dict[str, Any]]:
    """The 20 operations of coder_ground_truth.json (all datasets and complexities), the first max_ops of them when
    given. Refused when the file's sha256 is not GT_SHA256, when it gives another count, or when a data file an
    operation names is not in the datasets folder."""
    try:
        raw = v28.GT_FILE.read_bytes()
    except FileNotFoundError:
        raise ex.ExperimentError(f"{v28.GT_FILE} is missing (Mentori-paper 83a4091 tracks "
                                 f"tests/experiments_v2/datasets/: the ground truth and its three data files)") from None
    sha = hashlib.sha256(raw).hexdigest()
    if sha != GT_SHA256:
        raise ex.ExperimentError(f"{v28.GT_FILE} has sha256 {sha}, not {GT_SHA256}")
    ops = load_ground_truth_ops(ALL_DATASETS, ALL_COMPLEXITIES)
    if len(ops) != N_TASKS:
        raise ex.ExperimentError(f"{len(ops)} operations in {v28.GT_FILE}, not {N_TASKS}")
    missing = sorted({f for op in ops for f in op["files"].values() if not (v28.DATASETS_DIR / f).is_file()})
    if missing:
        raise ex.ExperimentError(f"data files missing from {v28.DATASETS_DIR}: {missing}")
    return ops[:max_ops] if max_ops else ops


# What an attempt keeps of each of its call records (A6, D37); the records themselves stay whole in the run's
# calls.jsonl, found by ctx_uid and seq
CALL_FIELDS = ("seq", "role", "model", "candidate", "status", "stop_reason", "error", "prompt_tokens",
               "output_tokens", "thinking_tokens", "wall_s", "load_s", "prompt_eval_s", "eval_s", "lock_sha256",
               "options_sent", "call_site")


def attempt_calls(sink: Path, ctx_uid: str) -> List[Dict[str, Any]]:
    """The call records one attempt wrote to <sink>/calls.jsonl (those with its run context's ctx_uid), in seq
    order, each cut down to CALL_FIELDS (a field the record does not carry is None)."""
    path = sink / "calls.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("ctx_uid") == ctx_uid:
            out.append({k: rec.get(k) for k in CALL_FIELDS})
    return sorted(out, key=lambda r: r["seq"])


def options_sent(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every distinct (role, model, options_sent) of the entries' call records, the seed left out (it is the draw's,
    or the candidate's). This replaces the constant "num_ctx": 24576 the report wrote (cuts.md M23, D37): what was
    sent comes from the records."""
    seen = {}
    for e in entries:
        for c in e.get("calls") or []:
            opts = {k: v for k, v in (c.get("options_sent") or {}).items() if k != "seed"}
            key = json.dumps([c.get("role"), c.get("model"), opts], sort_keys=True)
            seen[key] = {"role": c.get("role"), "model": c.get("model"), "options_sent": opts}
    return [seen[k] for k in sorted(seen)]


def work_list(chosen: List[Dict], configs: List[str], ops: List[Dict], draws) -> List[Tuple]:
    """Every attempt: (variant, config, operation, draw)."""
    return [(v, config, op, d) for v in chosen for config in configs for op in ops for d in draws]


def _what_is_sent(v: Dict) -> str:
    s = v["sent"]
    if v["model"].startswith("gemini::"):
        tc = s.get("thinking_config")
        return f"thinking {json.dumps(tc) if tc else 'not sent (Google default)'}, temperature {s['temperature']}"
    think = json.dumps(s["fields"]["think"]) if "think" in s["fields"] else "not sent"
    return f"think {think}, temperature {s['options']['temperature']}"


def print_work_list(chosen: List[Dict], configs: List[str], ops: List[Dict], draws) -> List[Tuple]:
    work = work_list(chosen, configs, ops, draws)
    per = len(configs) * len(ops) * len(draws)
    print(f"Figure 6 work list ({EXPERIMENT}): {len(ops)} operations x {len(configs)} configs x draws "
          f"{list(draws)} = {per} attempts per variant")
    print(f"{'model':34s} {'thinking':8s} {'same as':12s} {'sent (seed aside)':56s} {'attempts':>8s}  run_id extra")
    for v in chosen:
        print(f"{v['model']:34s} {v['thinking']:8s} {','.join(v['same_as']) or '-':12s} {_what_is_sent(v):56s} "
              f"{per:8d}  {v['extra']}")
    print(f"variants: {len(chosen)} of {len({v['model'] for v in chosen})} models; attempts: {len(work)}")
    return work


# ─────────────────────────────────────────────────────────────
# Run one variant
# ─────────────────────────────────────────────────────────────

LENGTH_STOP_MARKER = "LENGTH_STOP_D114"   # in a sink: its variant runs under --length-stop stop (D114 Q29 O2)


def check_length_rule(results: List[Dict[str, Any]], rule: str, rid: str, marked: bool = False) -> None:
    """D114 Q29 O2: refuse to continue under "retry" a run whose stored attempts ran under "stop", or whose variant is
    marked as moved to "stop" (marked: one of its sinks holds LENGTH_STOP_MARKER; moving a variant to "stop" is a
    decision, and a resume without the flag must not undo it). Attempts stored before the flag existed carry no rule
    and ran under "retry". An unknown rule is refused."""
    if rule not in v28.LENGTH_STOP_RULES:
        raise ex.ExperimentError(f"--length-stop {rule!r}: write one of {', '.join(v28.LENGTH_STOP_RULES)}")
    stored = {r.get("length_stop_rule") or "retry" for r in results}
    if rule == "retry" and ("stop" in stored or marked):
        why = f"a sink of its variant holds {LENGTH_STOP_MARKER}" if marked else "it holds attempts stored under stop"
        raise ex.ExperimentError(f"run {rid}: {why} (D114 Q29 O2); continue it with --length-stop stop")


def check_variant_length_rule(extra: str, root: Path, rule: str) -> None:
    """check_length_rule over every config's sink of the variant in root (findings/runs), whatever --configs names,
    reading only the sinks that exist (none is made here)."""
    sinks = [root / ex.run_id(EXPERIMENT, c, extra) for c in CONFIG_NAMES]
    marked = any((s / LENGTH_STOP_MARKER).exists() for s in sinks)
    for s in sinks:
        held = s / ANSWERS_FILE
        check_length_rule(load_intermediate(held)["results"] if held.exists() else [], rule, s.name, marked)


async def run_variant(
    variant: Dict[str, Any],
    configs: List[str],
    ops: List[Dict[str, Any]],
    base_url: str,
    resume: bool = False,
    length_stop: str = "retry",
):
    """Every attempt of one variant: per config one run and sink, per (operation, draw) one run context. length_stop
    is the D114 Q29 O2 rule (see the module docstring, LENGTH STOPS)."""
    gen_model, thinking, extra = variant["model"], variant["thinking"], variant["extra"]
    draws = ex.draws(FIGURE)
    models = {CODER_ROLE: gen_model}

    # Every run's sink is found (or made) and checked before the first attempt
    runs = {}
    for config in configs:
        rid = ex.run_id(EXPERIMENT, config, extra)
        sink = ex.sink(rid)
        answers_file = sink / ANSWERS_FILE
        if answers_file.exists() and not resume:
            raise ex.ExperimentError(f"{answers_file} holds attempts of run {rid}; pass --resume to continue it")
        runs[config] = (rid, sink, answers_file)
    if runs:   # D114 Q29 O2: every config's sink of the variant, in the folder that holds the sinks
        check_variant_length_rule(extra, next(iter(runs.values()))[1].parent, length_stop)
    if length_stop == "stop":
        for rid, sink, _ in runs.values():
            (sink / LENGTH_STOP_MARKER).write_text(f"--length-stop stop ({v28.LENGTH_RULE_DECISION})\n")

    logger.info(f"{'='*60}")
    logger.info(f"Figure 6: Coder Benchmark under the lock")
    logger.info(f"{'='*60}")
    logger.info(f"Model: {gen_model} | Thinking: {thinking} | Draws: {list(draws)}")
    logger.info(f"Operations: {len(ops)} | Configs: {len(configs)}")
    logger.info(f"Total attempts: {len(ops) * len(configs) * len(draws)}")
    logger.info(f"Length stops (D112 Q8): {length_stop} (the rule of D114 Q29 O2)")
    logger.info(f"{'='*60}")

    # D78 Q112: a kernel started as the attempts start theirs must run the harness's interpreter, which the package
    # fingerprint then reads (a setup error otherwise, before any attempt)
    logger.info(f"Kernel interpreter: {await v28.check_kernel_python()}")

    router = ModelRouter()

    base_workspace = PROJECT_ROOT / "data" / "workspace" / "v4_8_benchmark"
    base_workspace.mkdir(parents=True, exist_ok=True)

    all_results = []
    total = len(configs) * len(ops) * len(draws)
    done = 0
    t_start = time.time()

    for config in configs:
        rid, sink, answers_file = runs[config]
        intermediate = load_intermediate(answers_file)
        results = intermediate["results"]
        completed = set(intermediate["completed_keys"])

        for op in ops:
            for draw in draws:
                op_id = op["op_id"]
                key = ex.answer_key(config, op_id, draw)

                if key in completed:
                    done += 1
                    continue

                done += 1
                elapsed = time.time() - t_start
                rate = done / max(elapsed, 1) * 3600
                eta_h = (total - done) / max(rate, 0.01)

                logger.info(
                    f"[{done}/{total}] {config} | {op_id} d{draw} "
                    f"({op['complexity']}) | ETA: {eta_h:.1f}h"
                )

                # The run context of this (operation, draw); checked against the lock and the run's sink
                ctx = ex.context(EXPERIMENT, config, op_id, draw, models, thinking,
                                 base_url=base_url, run=rid, sink=sink)

                # Create workspace with dataset files
                workspace = base_workspace / f"{config}_{op_id}_d{draw}_{uuid.uuid4().hex[:6]}"
                workspace.mkdir(parents=True, exist_ok=True)

                files_dir = workspace / "files"
                files_dir.mkdir(parents=True, exist_ok=True)

                for _key, filename in op["files"].items():
                    shutil.copy2(v28.DATASETS_DIR / filename, files_dir / filename)

                # Run. The session's user is the run id (coder_v2 configs; no database read)
                with rc.run(ctx):
                    rule_token = v28.LENGTH_STOP.set(length_stop)   # D114 Q29 O2, read by every config
                    try:
                        result = await _dispatch(config, op, router, rid, workspace, gen_model=gen_model)
                    except (LockError, rc.RunContextError, import_scan.EnvironmentCheckError):
                        raise   # a refusal, a changed package fingerprint (D75 Q63) or a kernel on another
                                # interpreter (D78 Q112) is our own setup
                    except Exception as e:
                        import traceback
                        logger.error(f"Dispatch failed: {e}\n{traceback.format_exc()}")
                        # A failed model call is the attempt's call_error, with its record in calls.jsonl; anything
                        # else that stopped the attempt is "exception" (A5)
                        result = {
                            "config": config,
                            "passed": False,
                            "field_results": {},
                            "actual_results": {},
                            "exec_error": f"{type(e).__name__}: {e}",
                            "exec_outcome": "call_error" if isinstance(e, LockCallError) else "exception",
                            "latency_s": 0,
                            "n_cells": 0,
                            "n_llm_calls": None,   # not counted when the attempt stopped (A5); n_calls below
                            "n_retries": None,
                            "n_idle_recovered": 0,
                        }
                    finally:
                        v28.LENGTH_STOP.reset(rule_token)

                # The attempt's call records (A6, D37): every call it made, under this context's ctx_uid
                calls = attempt_calls(sink, ctx.ctx_uid)

                entry = {
                    "answer_key": key,
                    "run_id": rid,
                    "op_id": op_id,
                    "draw": draw,
                    "dataset": op["dataset"],
                    "complexity": op["complexity"],
                    "category": op["category"],
                    "config": config,
                    "gen_model": gen_model,
                    "thinking": thinking,
                    "thinking_same_as": list(variant["same_as"]),   # the settings that send the same request
                    "passed": result["passed"],
                    "judge_score": result.get("judge_score"),
                    "judge_comment": result.get("judge_comment"),
                    "field_results": result.get("field_results", {}),
                    "actual_results": result.get("actual_results", {}),
                    "exec_error": result.get("exec_error", ""),
                    "exec_outcome": result.get("exec_outcome"),   # v28.EXEC_OUTCOMES (A5, Q34)
                    # The generated code whole and every generation of the attempt: raw reply, code, block count,
                    # fence case (D69 Q35); exp_05 dropped the code (cuts.md exp_v2_8:891, D37)
                    "code": result.get("code"),
                    "generations": result.get("generations"),
                    "pick": result.get("pick"),                       # free_form_n3_*: 1-3, "unparsed", "combined"
                    "picked_fallback": result.get("picked_fallback"),
                    # coder_v2_*: the evaluator's scores with their status, the cell3 candidates, the timeouts
                    "cell_evaluations": result.get("cell_evaluations"),
                    "cell_candidates": result.get("cell_candidates"),
                    "n_step_exec_timeouts": result.get("n_step_exec_timeouts"),
                    "reexec_outcomes": result.get("reexec_outcomes"),
                    "code_cells": result.get("code_cells"),          # coder_v2_*: the notebook's code, whole
                    "history_log": result.get("history_log"),        # coder_v2_*: plan, steps, summary
                    "introspect_outcome": result.get("introspect_outcome"),
                    # Q34: each extraction and introspection run's outcome (exec_timeout included), in run order
                    "extract_outcomes": result.get("extract_outcomes"),
                    "introspect_outcomes": result.get("introspect_outcomes"),
                    # D72: the attempt's imports (every module its generated code imports), each missing allow-listed
                    # module installed at its pin (requirement, exit status), the missing modules not on the
                    # allow-list, the lines where the code runs a package install itself, the flag for a failure
                    # that is only such a module, and one scan per execution
                    "imports": result.get("imports"),
                    "missing_installed": result.get("missing_installed"),
                    "missing_not_allowed": result.get("missing_not_allowed"),
                    "install_lines": result.get("install_lines"),
                    "missing_library_not_allowed": result.get("missing_library_not_allowed"),
                    "import_scans": result.get("import_scans"),
                    # D75 Q63: the installed packages before and after the attempt (sha256 of the sorted
                    # `uv pip freeze` lines); a change stops the run before the attempt is stored
                    "packages_sha256_before": result.get("packages_sha256_before"),
                    "packages_sha256_after": result.get("packages_sha256_after"),
                    "api_reference": result.get("api_reference"),
                    "api_info": result.get("api_info"),
                    "introspect_output": result.get("introspect_output"),
                    "latency_s": result.get("latency_s", 0),
                    "n_cells": result.get("n_cells", 0),
                    "n_llm_calls": result.get("n_llm_calls"),
                    "n_retries": result.get("n_retries"),
                    "n_idle_recovered": result.get("n_idle_recovered", 0),
                    # D114 Q29 O2: the rule this attempt ran under, and (under "stop") the length stop that ended it
                    "length_stop_rule": length_stop,
                    "length_stop": result.get("length_stop"),
                    "ctx_uid": ctx.ctx_uid,
                    "n_calls": len(calls),                            # from the records, every role
                    "calls": calls,
                }

                results.append(entry)
                completed.add(key)

                save_intermediate(
                    {"results": results, "completed_keys": sorted(completed)},
                    answers_file,
                )

                status = "PASS" if result["passed"] else "FAIL"
                logger.info(
                    f"  -> {status} ({result.get('latency_s', 0):.0f}s)"
                    + (f" | {result.get('exec_error', '')[:80]}" if not result["passed"] else "")
                )

        all_results.extend(results)
        logger.info(f"Completed config: {config}")

    # Generate V4-8 report (the answers stay in each run's sink)
    _generate_v4_8_report(
        all_results, configs, ALL_DATASETS, ALL_COMPLEXITIES, ops,
        gen_model=gen_model, think=thinking,
    )


def outcome_counts(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Counts reported beside each config's pass rate (D75): exec_outcome ("length" included, Q57); the first fence
    tag and fence case of every reply run as code (Q56); the best-of-3 pick, "unparsed" included, of
    free_form_n3_best (pick) and of coder_v2_n1_cell3_best's cells (cell_pick) (Q58); and the status of every coder_v2
    cell evaluation, "unparsed" and "error" included (Q59). Keys are text; a missing value is "none"."""
    def bump(d, k):
        k = "none" if k is None else str(k)
        d[k] = d.get(k, 0) + 1
    out: Dict[str, Dict[str, int]] = {"exec_outcome": {}, "first_fence_tag": {}, "fence_case": {}, "pick": {},
                                      "cell_pick": {}, "cell_evaluation_status": {}}
    for r in results:
        bump(out["exec_outcome"], r.get("exec_outcome"))
        for g in r.get("generations") or []:
            if "fence_case" in g:   # a reply run as code (v28._generation)
                bump(out["first_fence_tag"], g.get("first_fence_tag"))
                bump(out["fence_case"], g.get("fence_case"))
        if r.get("pick") is not None and r.get("pick") != "combined":
            bump(out["pick"], r.get("pick"))
        for c in r.get("cell_candidates") or []:
            if c.get("strategy") == "best_of_3" and "pick" in c:
                bump(out["cell_pick"], c.get("pick"))
        for e in r.get("cell_evaluations") or []:
            bump(out["cell_evaluation_status"], e.get("status"))
    return {k: dict(sorted(v.items())) for k, v in out.items() if v}


def _generate_v4_8_report(
    all_results: List[Dict],
    configs: List[str],
    datasets: List[str],
    complexities: List[str],
    ops: List[Dict],
    gen_model: str = "",
    think: Union[bool, str, None] = None,
):
    """Generate V4-8 JSON + markdown reports (adapted from V2-8)."""
    import statistics

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _pass_rate(results):
        if not results:
            return 0.0
        return round(sum(1 for r in results if r["passed"]) / len(results) * 100, 1)

    def _median_lat(results):
        lats = [r["latency_s"] for r in results if r.get("latency_s", 0) > 0]
        return round(statistics.median(lats), 1) if lats else 0.0

    by_config = defaultdict(list)
    for r in all_results:
        by_config[r["config"]].append(r)

    by_config_complexity = defaultdict(list)
    for r in all_results:
        by_config_complexity[(r["config"], r["complexity"])].append(r)

    by_config_dataset = defaultdict(list)
    for r in all_results:
        by_config_dataset[(r["config"], r["dataset"])].append(r)

    summary = {}
    for config in configs:
        cr = by_config.get(config, [])
        summary[config] = {
            "pass_rate": _pass_rate(cr),
            "median_latency": _median_lat(cr),
            "n": len(cr),
            "by_complexity": {
                cx: {"pass_rate": _pass_rate(by_config_complexity.get((config, cx), [])),
                     "n": len(by_config_complexity.get((config, cx), []))}
                for cx in ALL_COMPLEXITIES
            },
            "by_dataset": {
                ds: {"pass_rate": _pass_rate(by_config_dataset.get((config, ds), [])),
                     "n": len(by_config_dataset.get((config, ds), []))}
                for ds in ALL_DATASETS
            },
            "counts": outcome_counts(cr),   # D75 Q56-Q59: beside the pass rate
        }

    model_slug = _model_slug(gen_model)
    think_suffix = f"_think-{think}" if think else ""

    output = {
        "experiment": "v4_8_coder_benchmark",
        "timestamp": timestamp,
        "gen_model": gen_model,
        "think": str(think) if think else "off",
        # What was sent, read from the call records (cuts.md M23, D37); it wrote "num_ctx": 24576 as a constant
        "options_sent": options_sent(all_results),
        "configs": configs,
        "datasets": datasets,
        "complexities": complexities,
        "n_operations": len(ops),
        "total_evaluations": len(all_results),
        "summary": summary,
        "per_operation_results": all_results,
    }

    V4_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = V4_RESULTS_DIR / f"v4_8_coder_benchmark_{model_slug}{think_suffix}_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    # Also save as _latest
    latest_path = V4_RESULTS_DIR / f"v4_8_coder_benchmark_{model_slug}{think_suffix}_latest.json"
    with open(latest_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"\nV4-8 COMPLETE: {gen_model} think={think}")
    logger.info(f"Results: {json_path}")

    # Print summary table
    print(f"\n{'='*60}")
    print(f"V4-8 Results: {gen_model} think={think if think else 'off'}")
    for o in output["options_sent"]:
        print(f"sent ({o['role']}, {o['model']}): {json.dumps(o['options_sent'], sort_keys=True)}")
    print(f"{'='*60}")
    print(f"{'Config':30s} | {'Pass%':>6s} | {'Med.Lat':>8s} | {'N':>4s}")
    print(f"{'-'*30}-+-{'-'*6}-+-{'-'*8}-+-{'-'*4}")
    for config in configs:
        s = summary.get(config, {})
        print(f"{config:30s} | {s.get('pass_rate',0):5.1f}% | {s.get('median_latency',0):7.1f}s | {s.get('n',0):4d}")
    print()
    # D75 Q56-Q59: the counts reported beside each pass rate
    for config in configs:
        for name, c in summary.get(config, {}).get("counts", {}).items():
            print(f"{config:30s} {name}: {json.dumps(c, sort_keys=True)}")
    print()

    return json_path


# ─────────────────────────────────────────────────────────────
# Run every variant
# ─────────────────────────────────────────────────────────────

async def run_all_variants(
    chosen: List[Dict[str, Any]],
    configs: List[str],
    ops: List[Dict[str, Any]],
    base_url: str,
    resume: bool = False,
    length_stop: str = "retry",
):
    """Run the chosen variants one after another."""
    for v in chosen:
        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting: {v['model']} thinking={v['thinking']}")
        logger.info(f"{'#'*60}\n")

        await run_variant(v, configs=configs, ops=ops, base_url=base_url, resume=resume, length_stop=length_stop)


# ─────────────────────────────────────────────────────────────
# Comparison report: V2-8 vs V4-8
# ─────────────────────────────────────────────────────────────

def generate_comparison_report():
    """Generate a comparison report between V2-8 (num_ctx=2048) and V4-8 (the settings its call records show)."""
    print(f"\n{'='*70}")
    print("V2-8 vs V4-8: Impact of Context Window Correction")
    print(f"{'='*70}\n")

    # Load V2-8 results (first timestamped files)
    v2_data = {}
    for f in sorted(V2_RESULTS_DIR.glob("v2_8_coder_benchmark_*_20260*.json")):
        if "_latest" in f.name or "_intermediate" in f.name:
            continue
        m = re.match(r"v2_8_coder_benchmark_(.+?)_(\d{8}_\d{6})\.json", f.name)
        if m:
            model_key = m.group(1)
            if model_key not in v2_data:  # first = oldest = original run
                data = json.load(open(f))
                per_op = data.get("per_operation_results", [])
                if per_op:
                    v2_data[model_key] = per_op

    # Load V4-8 results
    v4_data = {}
    v4_options = {}
    for f in sorted(V4_RESULTS_DIR.glob("v4_8_coder_benchmark_*_latest.json")):
        m = re.match(r"v4_8_coder_benchmark_(.+?)_latest\.json", f.name)
        if m:
            model_key = m.group(1)
            data = json.load(open(f))
            per_op = data.get("per_operation_results", [])
            if per_op:
                v4_data[model_key] = per_op
                v4_options[model_key] = data.get("options_sent")   # from the call records (M23); None in old files

    if not v4_data:
        print("No V4-8 results found yet. Run experiments first.")
        return

    print(f"{'Model':40s} | {'V2-8':>8s} | {'V4-8':>8s} | {'Delta':>8s} | {'Note':s}")
    print(f"{'-'*40}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*20}")

    for model_key in sorted(set(list(v2_data.keys()) + list(v4_data.keys()))):
        v2_ops = v2_data.get(model_key, [])
        v4_ops = v4_data.get(model_key, [])

        v2_pass = sum(1 for r in v2_ops if r.get("passed")) / max(len(v2_ops), 1) * 100
        v4_pass = sum(1 for r in v4_ops if r.get("passed")) / max(len(v4_ops), 1) * 100

        note = ""

        if v2_ops and v4_ops:
            delta = v4_pass - v2_pass
            delta_str = f"{delta:+.1f}pp"
            print(f"{model_key:40s} | {v2_pass:7.1f}% | {v4_pass:7.1f}% | {delta_str:>8s} | {note}")
        elif v2_ops:
            print(f"{model_key:40s} | {v2_pass:7.1f}% | {'--':>8s} | {'--':>8s} | pending")
        elif v4_ops:
            print(f"{model_key:40s} | {'--':>8s} | {v4_pass:7.1f}% | {'--':>8s} | new")

    print()

    # Save comparison as JSON
    comparison = {
        "experiment": "v4_8_vs_v2_8_comparison",
        "timestamp": datetime.now().isoformat(),
        "description": "V2-8 (Ollama num_ctx 2048) against V4-8 (the options in v4_8_options_sent, from its call records)",
        "models": {},
    }
    for model_key in sorted(set(list(v2_data.keys()) + list(v4_data.keys()))):
        v2_ops = v2_data.get(model_key, [])
        v4_ops = v4_data.get(model_key, [])
        v2_pass = sum(1 for r in v2_ops if r.get("passed")) / max(len(v2_ops), 1) * 100
        v4_pass = sum(1 for r in v4_ops if r.get("passed")) / max(len(v4_ops), 1) * 100
        comparison["models"][model_key] = {
            "v2_8_pass_rate": round(v2_pass, 1) if v2_ops else None,
            "v4_8_pass_rate": round(v4_pass, 1) if v4_ops else None,
            "delta_pp": round(v4_pass - v2_pass, 1) if v2_ops and v4_ops else None,
            # The V2-8 files this comparison reads ran at Ollama num_ctx 2048 and carry no call records, so the label
            # of that arm stays as submitted. Whether the comparison itself goes with the 2,048-token arm (D22) is
            # proposed, not done. What V4-8 sent comes from its file's call records; it wrote 24576 (cuts.md M23, D37)
            "v2_8_num_ctx": 2048 if "gemini" not in model_key else "API",
            "v4_8_options_sent": v4_options.get(model_key),
            "is_gemini": "gemini" in model_key,
            "v2_8_n": len(v2_ops),
            "v4_8_n": len(v4_ops),
        }

    comp_path = V4_RESULTS_DIR / "v4_8_comparison_v2_vs_v4.json"
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"Comparison saved: {comp_path}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Figure 6: the coder benchmark, every attempt under experiments/LOCK.toml (D50, D63, D66)"
    )
    which = parser.add_mutually_exclusive_group()
    which.add_argument(
        "--model", type=str, default=None, choices=FIG6_MODELS,
        help="One Figure 6 model; every thinking setting the lock gives it unless --thinking names one",
    )
    which.add_argument(
        "--run-all", action="store_true",
        help="Every variant of Figure 6, one after another (resumes each run)",
    )
    parser.add_argument(
        "--thinking", type=str, default=None,
        help="One thinking setting of --model, as --dry-run lists them (default, off, low, medium, high)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the work list (variants, what the lock sends, attempt count) and stop: no model call, no sink",
    )
    parser.add_argument(
        "--base-url", type=str, default=None,
        help="The Ollama server of every Ollama call, generator and judge (required for a run)",
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=CONFIG_NAMES,
        help=f"Configs to test (default: all {len(CONFIG_NAMES)})",
    )
    parser.add_argument(
        "--max-ops", type=int, default=None,
        help="Max operations (for smoke tests)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Continue runs whose sinks hold attempts (findings/runs/<run_id>/answers.json)",
    )
    parser.add_argument(
        "--compare", action="store_true",
        help="Generate V2-8 vs V4-8 comparison report",
    )
    parser.add_argument(
        "--length-stop", choices=v28.LENGTH_STOP_RULES, default="retry",
        help="D114 Q29 O2: after a length stop the attempt goes on as submitted (retry, the default) or ends at its "
             "first length stop with exec_outcome length, in every config (stop)",
    )

    args = parser.parse_args()

    if args.thinking is not None and args.model is None:
        parser.error("--thinking names a setting of one model: give --model")
    if args.length_stop != "retry" and (args.run_all or args.thinking is None):
        parser.error("--length-stop stop is set per variant (D114 Q29 O2): give --model and --thinking")

    if args.compare:
        generate_comparison_report()
        return
    if not (args.dry_run or args.run_all or args.model):
        parser.print_help()
        print("\nExamples:")
        print("  --dry-run                                            # The work list and its attempt count")
        print("  --model ollama::qwen3-coder:30b --base-url URL       # Every thinking setting of one model")
        print("  --model ollama::gpt-oss:20b --thinking high --base-url URL")
        print("  --run-all --base-url URL                             # Every variant")
        return

    chosen = select(variants(), args.model, args.thinking)
    ops = load_ops(args.max_ops)
    print_work_list(chosen, args.configs, ops, ex.draws(FIGURE))
    print(f"length stops (D112 Q8): {args.length_stop} (the rule of D114 Q29 O2)")
    if args.dry_run:
        return
    if not args.base_url:
        parser.error("--base-url is required for a run")

    asyncio.run(run_all_variants(
        chosen,
        configs=args.configs,
        ops=ops,
        base_url=args.base_url,
        resume=args.resume or args.run_all,
        length_stop=args.length_stop,
    ))


if __name__ == "__main__":
    main()
