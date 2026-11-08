#!/usr/bin/env python3
"""
V2-8: Coder Benchmark with Objective Verification

Definitive coder benchmark with pass/fail verification against ground truth.
No LLM judge — all metrics are computed by comparing numerical outputs
to precomputed ground truth values with tolerances.

Configs:
  1. free_form:     Single LLM call → code → execute in kernel → verify
  2. coder_v2_n1:   coder_loop_v2 with N_CANDIDATES=1 → verify
  3. coder_v2_n3:   coder_loop_v2 with N_CANDIDATES=3 → verify

Datasets: airway (bioinformatics), lung_cancer (survival/epidemiology)
20 operations total (v4.0), 3 complexity tiers (simple/medium/complex)

Usage:
    uv run python tests/experiments_v2/exp_v2_8_coder_benchmark.py
    uv run python tests/experiments_v2/exp_v2_8_coder_benchmark.py --configs free_form coder_v2_n3
    uv run python tests/experiments_v2/exp_v2_8_coder_benchmark.py --datasets airway
    uv run python tests/experiments_v2/exp_v2_8_coder_benchmark.py --complexity simple medium
    uv run python tests/experiments_v2/exp_v2_8_coder_benchmark.py --resume
    uv run python tests/experiments_v2/exp_v2_8_coder_benchmark.py --max-ops 3
"""

import argparse
import asyncio
import json
import logging
import os
import re
import shutil
import statistics
import sys
import time
import uuid
from collections import defaultdict
from contextlib import ExitStack
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default TOOL_SERVER_URL to localhost when running outside Docker
if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

from backend.agents.model_router import ModelRouter
from backend.agents import lock_adapter
from backend.agents.notebook import import_scan
from backend.agents.notebook import kernel as kernel_module
from backend.agents.notebook.kernel import EXEC_TIMEOUT, is_exec_timeout
from backend.agents.notebook.step_executor import parse_stated_pick
# lock_adapter puts the repository root on sys.path, so experiments.runner imports from here on
from experiments.runner import run_context as rc
from experiments.runner.lock import LockError

# A lock refusal or a missing run context is our own setup, never a failed attempt (D69 Q38); so is a package
# fingerprint that changed or could not be taken (D75 Q63)
SETUP_ERRORS = (LockError, rc.RunContextError, import_scan.EnvironmentCheckError)

from tests.experiments.exp_common import (
    GEN_MODEL,
    find_admin_user_id,
    load_intermediate, save_intermediate,
    RESULTS_DIR as V1_RESULTS_DIR,
)
from tests.experiments_v2.exp_v2_common import (
    save_v2_results, save_v2_markdown,
    format_v2_table, format_pct, format_latency,
    V2_RESULTS_DIR,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_v2_8")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

DATASETS_DIR = Path(__file__).parent / "datasets"
GT_FILE = DATASETS_DIR / "coder_ground_truth.json"
INTERMEDIATE_FILE = V2_RESULTS_DIR / "v2_8_intermediate.json"  # legacy default, overridden per-model in run_experiment

CONFIG_NAMES = [
    "free_form", "free_form_n3_best", "free_form_n3_combined",
    "coder_v2_n1", "coder_v2_n1_cell3_best", "coder_v2_n1_cell3_combined",
    "coder_v2_n3",
    # New algorithms with introspection/documentation lookup
    "introspect_then_code",
    "error_recovery_introspect",
    "thinker_coder_split",
    # Combined best approach: pre-emptive introspection + error recovery + common pitfalls
    "introspect_with_recovery",
]
ALL_DATASETS = ["airway", "lung_cancer"]
ALL_COMPLEXITIES = ["simple", "medium", "complex"]
CODER_ROLE = "coder"   # the agent role the run context names for the model under test (_dispatch)

# Counts of the benchmark as submitted, kept and stated (fix_design/limits.md Class M, "named parameters to keep and
# state", rows 46-154): candidates of free_form_n3_*, the steps of a coder_v2 plan, and code repairs of
# error_recovery_introspect and introspect_with_recovery.
N_FREE_FORM_CANDIDATES = 3
CODER_V2_MAX_STEPS = 20
MAX_RECOVERY_RETRIES = 2

# Outcomes of running a script (A5, Q34): "ok"; "error" (the code raised); "exec_timeout" (the EXEC_TIMEOUT limit
# fired, its own outcome); "not_run" (the reply held no code, nothing ran); "length" (the reply whose code would run
# ended on the length stop, so nothing ran, D75 Q57); "call_error" (a model call failed before the code could run);
# "exception" (anything else that stopped the attempt); "step_failed" (coder_v2 configs: a step failed or coder_v2
# reported an error, so the notebook is not re-run for verification, as submitted).
EXEC_OUTCOMES = ("ok", "error", "exec_timeout", "not_run", "length", "call_error", "exception", "step_failed")

# What an attempt does after a length stop, set per variant by its entry point (exp_05 --length-stop, which its
# launcher passes). "retry" is the code as submitted and as every variant before D114 ran: a call that ended on
# "length" is handled as the config handles it (a reply run as code runs nothing, D75 Q57; any other reply is read on,
# and a coder_v2 step goes on, is retried or fails as any other). "stop" (D114 Q29 O2, Valerio 22 October, which
# replaces D112 Q8's step rule; S2 nemotron-3-nano:30b off from then on): an attempt ends at its first length stop and
# is recorded as "length", in every config. A length stop is a generator call of the attempt whose record has status
# or stop_reason "length" (_is_length; the soft-pass judge, role judge, is an instrument and never counts). In the
# seven configs whose calls the harness makes itself, _generation raises LengthStopEnd right after that call, so no
# later call is made, and _dispatch records the attempt (_length_end_result). In the four coder_v2 configs Mentori's
# coder_loop_v2 makes the calls, so the attempt's own call records are read at each event the loop yields
# (_LengthRecords): the attempt ends at the first event after its first length stop, and once more when the loop
# ends (_run_coder_v2). Every generator call coder_v2 asks for after that stop, before the event, in a planning task
# the loop started (coder_v2.py:389), a cell candidate or a transient retry, is refused before anything is sent
# (_LengthGate, through run_context's call gate: no request, no record; Mentori handles the refusal as a failed
# call), and the planning task is awaited before the attempt is stored, so no call of the attempt runs into the next
# one (review of 22 October, F1, F3). Either way the
# attempt stores exec_outcome "length", passed False, no verification, and its length_stop record (the first length
# stop's seq and call site, where the attempt ended). S447 applies the same rule to every variant's stored attempts:
# it reads an attempt up to its first length stop only (S447 apply_length_rule), so the calls made past it here count
# for nothing there either.
LENGTH_STOP_RULES = ("retry", "stop")
LENGTH_STOP: ContextVar[str] = ContextVar("exp_v2_8_length_stop", default="retry")
LENGTH_RULE_DECISION = "D114 Q29 O2"


def _is_length(record: Dict[str, Any]) -> bool:
    """D114 Q29 O2: a generator call that ended on the length stop (S447 call_flags reads the same two fields)."""
    return record.get("role") == "generator" and (record.get("status") == "length"
                                                  or record.get("stop_reason") == "length")


class LengthStopEnd(Exception):
    """D114 Q29 O2, "stop": a generator call of the attempt ended on "length", so the attempt ends here. Raised by
    _generation in the configs whose calls the harness makes; every config passes it on (PASS_THROUGH) to _dispatch,
    which records the attempt as "length" (_length_end_result). generation is the stage's _generation entry."""

    def __init__(self, generation: Dict[str, Any], record: Dict[str, Any]):
        self.generation = generation
        self.first = {"seq": record.get("seq"), "call_site": record.get("call_site")}
        super().__init__(f"{generation.get('stage')}: the reply ended on the length stop (seq {self.first['seq']})")


# What every config passes on to its caller instead of recording it as the attempt's exec_error: a setup error, and
# the D114 Q29 O2 length stop
PASS_THROUGH = SETUP_ERRORS + (LengthStopEnd,)


class LengthStopRefused(Exception):
    """D114 Q29 O2, "stop", coder_v2 configs: a generator call asked for after the attempt's first length stop,
    refused by _LengthGate before anything is sent (no request, no record). Not a setup error: Mentori handles it as a
    failed call (a failed plan candidate, cell candidate or step), and the attempt ends at coder_loop_v2's next event.
    Its text names none of the transient failures step_executor retries."""


class _LengthGate:
    """D114 Q29 O2: run_context's call gate for one coder_v2 attempt under "stop". after() notes the attempt's first
    generator record that ended on "length" (_is_length, its own ctx_uid, calls.jsonl); from then on before() refuses
    every generator call made in the attempt's context (LengthStopRefused), in the attempt's task, in its worker
    threads and in a task it started, also after the attempt's own task has moved on. The soft-pass judge (role judge)
    is never refused."""

    def __init__(self):
        self.uid = rc.current().ctx_uid
        self.ended = False
        self.refused = 0

    def before(self, tag: str, role: str) -> None:
        if self.ended and role == "generator":
            self.refused += 1
            raise LengthStopRefused(f"{tag}: not sent, the attempt ended at its first length stop "
                                    f"({LENGTH_RULE_DECISION})")

    def after(self, line: Dict[str, Any], file: str) -> None:
        if file == "calls.jsonl" and line.get("ctx_uid") == self.uid and _is_length(line):
            self.ended = True


GATED_TASK_WAIT_S = 600   # how long _run_coder_v2 waits for a task its attempt started (refused calls end it at once)


async def _await_gated_tasks(gate: "_LengthGate", before: set) -> int:
    """D114 Q29 O2 (review of 22 October, F1): the tasks the attempt started that still run when it ends (coder_v2's
    planning task, which closing the loop does not cancel), awaited so they end inside the attempt. Only tasks whose
    context holds this attempt's gate are awaited; every generator call they ask for is refused, so they end at once.
    One still running after GATED_TASK_WAIT_S is cancelled, with a warning. Returns how many were awaited."""
    me = asyncio.current_task()
    tasks = [t for t in asyncio.all_tasks() - before
             if t is not me and not t.done() and rc.gate_in(t.get_context()) is gate]
    if tasks:
        done, pending = await asyncio.wait(tasks, timeout=GATED_TASK_WAIT_S)
        for t in pending:
            logger.warning(f"D114: a task of the ended attempt still runs after {GATED_TASK_WAIT_S} s; cancelled")
            t.cancel()
    return len(tasks)

# Which code runs (D69 Q35, with D75 Q56), decided by the reply's first ```. The opening fence is a ``` whose tag
# (the rest of its line) names Python by its first word: python, py or python3, in any letter case, attributes after
# it allowed ("```python title=a.py") (D75 Q56); a bare ``` is also an opening fence when only blank space comes
# before it in the reply, since a fence at the very top cannot close code that does not exist (D75 Q56). When the
# first ``` is an opening fence, the block from the line after it to the next ``` runs ("first_block"); a block
# closed on the fence's own line ("```python x = 1```") runs what stands between the tag and the closing ```, as
# the pattern before D75 did. When the first ``` is anything else (a bare ``` after text, or another tag), the reply
# has no opening fence (the prompt ends on an open ```python fence and the model continued the code): the reply up to
# that ``` runs, and the closing fence and anything after it, a later example block included, are cut
# ("no_opening_fence", D69). With no ``` at all the whole reply runs ("no_fence"). An opening fence that is never
# closed is "unclosed_block": it runs from the line after the fence to the end of the reply (D75 Q57, for a reply
# that ended on "stop"). Every generation stores the raw reply, the code whole, the block count (blocks whose fence
# names Python, a one-line block and a \r\n line end included), the case, and the text after the first ``` on its
# line (first_fence_tag: "python", "py", "" for a bare fence; None with no fence).
_PY_TAGS = ("python", "py", "python3")
_PY_BLOCK = re.compile(r'```[ \t]*(?:python3|python|py)(?=[\s`])(.*?)```', re.DOTALL | re.IGNORECASE)


def _fence(reply: str, first: int) -> Tuple[str, str, Optional[str]]:
    """The reply's first ``` (at index first): its stored tag (the rest of its line, stripped), the tag's first word
    in lower case ("" for a bare fence), and the code between the tag and a closing ``` on the same line (None when
    the line does not close the block)."""
    line = reply[first + 3:].split("\n", 1)[0]
    head, closed, _ = line.partition("```")
    words = head.split()
    lang = words[0].lower() if words else ""
    inline = None
    if closed:
        inline = head.strip()[len(words[0]):].strip() if words else ""
    return line.strip(), lang, inline


def _opens_code(reply: str, first: int, lang: str) -> bool:
    """D75 Q56: the reply's first ``` (at index first, lang its tag's first word) opens a code block."""
    if lang in _PY_TAGS:
        return True
    return lang == "" and not reply[:first].strip()


def extract_code(reply: Optional[str]) -> Dict[str, Any]:
    """The code to run from a model's reply, by the rule above, with what the record keeps: raw_reply, code (whole;
    it was stored cut to 4,000 characters, cuts.md exp_v2_8:891), n_blocks, fence_case, first_fence_tag and
    code_status ("ok"; "empty_reply" or "empty_code": nothing runs, A5, where the empty reply's str(response) used to
    run as code). A reply that ended on "length" is decided by _generation, which has its stop reason (D75 Q57)."""
    reply = reply or ""
    blocks = _PY_BLOCK.findall(reply)
    first = reply.find("```")
    tag, lang, inline = (None, "", None) if first < 0 else _fence(reply, first)
    if first < 0:
        code, case = reply.strip(), "no_fence"
    elif _opens_code(reply, first, lang) and inline is not None:
        code, case = inline, "first_block"
    elif _opens_code(reply, first, lang):
        line_end = reply.find("\n", first)
        start = len(reply) if line_end < 0 else line_end + 1
        close = reply.find("```", start)
        if close >= 0:
            code, case = reply[start:close].strip(), "first_block"
        else:
            code, case = reply[start:].strip(), "unclosed_block"
    else:
        code, case = reply[:first].strip(), "no_opening_fence"
    status = "empty_reply" if not reply.strip() else "empty_code" if not code else "ok"
    return {"raw_reply": reply, "code": code, "n_blocks": len(blocks), "fence_case": case,
            "first_fence_tag": tag, "code_status": status}


def _generation(stage: str, response: Dict[str, Any], code: bool = True) -> Dict[str, Any]:
    """One model call of an attempt as the answer stores it (A6, D37): the stage, the stop reason, the seq of its
    record in the run's calls.jsonl, and either extract_code(reply) (a reply that is run as code) or the raw reply
    whole (a reply that is read, not run: an analysis, a pick, an API summary).

    D75 Q57: a reply run as code that ended on "length" (the context filled, or Gemini's output limit) runs nothing,
    whatever its fences: its code_status is "length" (the code extract_code found is still stored), and the attempt
    whose code it was is recorded with exec_outcome "length" (_not_run), never as a coding error (LOCK.toml truncate
    and shift false: a length failure shows as length)."""
    reply = response.get("response", "") or ""
    record = response.get("lock_record") or {}
    out = {"stage": stage, "stop_reason": response.get("done_reason"), "call_seq": record.get("seq")}
    out.update(extract_code(reply) if code else {"raw_reply": reply})
    if code and out["stop_reason"] == "length":
        out["code_status"] = "length"
    if LENGTH_STOP.get() == "stop" and _is_length({"role": "generator", **record,
                                                   "stop_reason": record.get("stop_reason") or out["stop_reason"]}):
        raise LengthStopEnd(out, record)   # D114 Q29 O2: the attempt ends at its first length stop
    return out


def _not_run(code_status: str) -> Tuple[str, str]:
    """(exec_outcome, exec_error) of an attempt whose code does not run: "length" when its reply ended on the length
    stop (D75 Q57), else "not_run" (no code in the reply, A5)."""
    if code_status == "length":
        return "length", "no code run: the reply ended on the length stop (D75 Q57)"
    return "not_run", f"no code to run: {code_status}"


def _outcome_of_exception(e: BaseException) -> str:
    """The exec outcome of an exception that stopped an attempt: a failed model call is "call_error" (its record,
    with the call's status, is in calls.jsonl), anything else "exception"."""
    return "call_error" if isinstance(e, lock_adapter.LockCallError) else "exception"


def _model_slug(model_identifier: str) -> str:
    """Convert model identifier to a filesystem-safe slug.

    Examples:
        ollama::qwen3-coder:latest  -> qwen3-coder
        gemini::gemini-2.5-pro-preview-05-06 -> gemini-2.5-pro-preview
        ollama::gpt-oss:20b -> gpt-oss-20b
    """
    # Strip provider prefix
    name = model_identifier.split("::", 1)[-1] if "::" in model_identifier else model_identifier
    # Strip :latest suffix
    if name.endswith(":latest"):
        name = name[:-7]
    # Replace colons with dashes (e.g. gpt-oss:20b -> gpt-oss-20b)
    name = name.replace(":", "-")
    # Truncate long preview suffixes (keep first 30 chars)
    if len(name) > 30:
        name = name[:30].rstrip("-")
    return name

FREE_FORM_SYSTEM = """You are a scientific Python programmer. Write a complete, self-contained
Python script to accomplish the following task.

Rules:
- Data files are in the `files/` subdirectory of the current working directory
- Use pandas, numpy, scipy, scikit-learn, lifelines, statsmodels as needed
- Print results clearly with variable names
- The script must be executable as-is
- IMPORTANT: You MUST store your final results in the exact variable names listed below

## Data Files Available
{file_descriptions}

## Task
{prompt}

## Required Output Variables
{required_variables}

## Python Code
```python
"""

JUDGE_PICK_BEST = """You are a code review judge. You are given {n} candidate Python scripts
that attempt the same scientific computing task.

Your job: Pick the BEST candidate — the one most likely to produce correct results.

Evaluate each candidate on:
1. Correctness of the approach (right algorithm, right column names, right data handling)
2. Syntactic correctness (will it run without errors?)
3. Proper use of required output variable names
4. Edge case handling

## Task Description
{prompt}

## Data Files
{file_descriptions}

## Required Output Variables
{required_variables}

{candidates_section}

Respond with ONLY the number of the best candidate (1, 2, or 3). Nothing else.
"""

JUDGE_COMBINE = """You are a code synthesis judge. You are given {n} candidate Python scripts
that attempt the same scientific computing task.

Your job: Write a FINAL, improved version that combines the best ideas from all candidates.
Cherry-pick the best approach, correct column names, proper algorithms, and edge case handling.

## Task Description
{prompt}

## Data Files
{file_descriptions}

## Required Output Variables
{required_variables}

{candidates_section}

Write the final synthesized Python script. Output ONLY the code, no explanation.
```python
"""

JUDGE_EVALUATE_RESULT = """You are a fair and nuanced scientific judge.
A Python script was executed to solve a task, but the results failed exact verification against the ground truth.
Your job is to evaluate if the failure is a "soft pass" (valid approach, just slightly different values/format) or a "hard fail" (wrong result).

## Task
{prompt}

## Ground Truth
{ground_truth}

## Actual Results (Extracted)
{actual_results}

## Verification Failure / Error Details
{error_message}

## Instructions
1. Compare Actual Results vs Ground Truth.
2. If the numbers are extremely close (precision nuance) or the format is just slightly different (e.g. integer vs float), or if the script calculated a valid alternative interpretation, mark it as PASS_WITH_RESERVE.
3. If the results are wrong, missing, or the script crashed, mark it as FAIL.
4. Provide a very brief comment explaining your decision.

Output format:
SCORE: [PASS_WITH_RESERVE | FAIL]
COMMENT: [Brief explanation]
"""

# ─────────────────────────────────────────────────────────────
# NEW ALGORITHM PROMPTS: Introspection & Thinker-Coder
# ─────────────────────────────────────────────────────────────

INTROSPECT_ANALYSIS_PROMPT = """Analyze this scientific computing task and identify the Python libraries/classes/functions that will be needed.

## Task
{prompt}

## Instructions
List each library/class/function that the task requires. Be specific about:
1. Which library (lifelines, scipy, pandas, sklearn, etc.)
2. Which specific class or function (e.g., CoxPHFitter, KaplanMeierFitter, ttest_ind)
3. Any specific methods that will be called on these objects

Output a JSON array of objects to introspect:
```json
[
  {{"module": "lifelines", "object": "CoxPHFitter", "methods": ["fit", "summary", "params_"]}},
  {{"module": "scipy.stats", "object": "ttest_ind", "methods": []}}
]
```

Only output the JSON array, nothing else.
"""

INTROSPECT_CODE_TEMPLATE = """
# Introspection cell - gather API information
import json as _json
_api_info = []

{introspect_blocks}

print("__API_INFO__")
print(_json.dumps(_api_info, indent=2))
print("__API_END__")
"""

INTROSPECT_BLOCK_TEMPLATE = """
try:
    from {module} import {object}
    _obj = {object}
    _info = {{"module": "{module}", "object": "{object}", "methods": [], "attributes": []}}

    # Get methods and attributes (exclude private)
    for _name in dir(_obj):
        if _name.startswith('_'):
            continue
        _attr = getattr(_obj, _name, None)
        if callable(_attr):
            _info["methods"].append(_name)
        else:
            _info["attributes"].append(_name)

    # Try to get docstring (whole: cuts.md exp_v2_8:264, D25; it was cut to 500 characters)
    if hasattr(_obj, '__doc__') and _obj.__doc__:
        _info["docstring"] = _obj.__doc__

    _api_info.append(_info)
except Exception as _e:
    _api_info.append({{"module": "{module}", "object": "{object}", "error": str(_e)}})
"""

FREE_FORM_WITH_API_SYSTEM = """You are a scientific Python programmer. Write a complete, self-contained
Python script to accomplish the following task.

Rules:
- Data files are in the `files/` subdirectory of the current working directory
- Use pandas, numpy, scipy, scikit-learn, lifelines, statsmodels as needed
- Print results clearly with variable names
- The script must be executable as-is
- IMPORTANT: You MUST store your final results in the exact variable names listed below

## Data Files Available
{file_descriptions}

## Task
{prompt}

## Required Output Variables
{required_variables}

## API Reference (from actual library introspection)
The following API information was gathered by running Python introspection on the actual installed libraries.
Use this information to ensure you call methods/attributes correctly:

{api_reference}

## Python Code
```python
"""

# D75 Q61: the recovery retry gets the error's name and message ("ename: evalue") plus the introspection, not the
# traceback and not the earlier code, as submitted (cuts.md M25 is design, not a cut); stated in Methods.
ERROR_RECOVERY_INTROSPECT_PROMPT = """The code execution failed with this error:
{error_message}

I ran introspection on the failing object to find the correct API:
{introspect_output}

Based on this information, fix the code. The correct attribute/method to use is likely visible in the introspection output above.

## Data Files Available
{file_descriptions}

## Task
{prompt}

## Required Output Variables
{required_variables}

Write the corrected Python code:
```python
"""

THINKER_RESEARCH_PROMPT = """You are a research assistant. Your job is to identify what API documentation
the coder will need to complete this task correctly.

## Task
{prompt}

## Instructions
1. Identify which Python libraries will be needed (lifelines, scipy, pandas, sklearn, etc.)
2. For each library, identify the key classes/functions
3. Write Python code that will introspect these objects and print their available methods/attributes

Output Python code that prints API information for each needed component:
```python
"""

THINKER_API_SUMMARY_PROMPT = """Based on the introspection output below, write a concise API reference
that a coder can use to write correct code.

## Introspection Output
{introspect_output}

## Instructions
Write a clear, concise API reference focusing on:
1. The correct method/attribute names (not outdated ones)
2. Method signatures if available
3. Any important notes from docstrings

Output format:
## API Reference
- `ClassName.method_name()` - brief description
- `ClassName.attribute_name` - brief description
...

Be concise but complete. This will be used by a coder to write correct Python code.
"""

# Combined algorithm prompt with common pitfalls
INTROSPECT_WITH_RECOVERY_SYSTEM = """You are a scientific Python programmer. Write a complete, self-contained
Python script to accomplish the following task.

Rules:
- Data files are in the `files/` subdirectory of the current working directory
- Use pandas, numpy, scipy, scikit-learn, lifelines, statsmodels as needed
- Print results clearly with variable names
- The script must be executable as-is
- IMPORTANT: You MUST store your final results in the exact variable names listed below

## CRITICAL: Common API Pitfalls to Avoid
{common_pitfalls}

## API Reference (from actual library introspection)
The following API information was gathered by running Python introspection on the actual installed libraries.
{api_reference}

## Data Files Available
{file_descriptions}

## Task
{prompt}

## Required Output Variables
{required_variables}

## Python Code
```python
"""

# Common API pitfalls that models frequently get wrong
COMMON_PITFALLS = """
### lifelines library (survival analysis)
- CoxPHFitter: Use `cph.summary` DataFrame to access statistics, NOT `cph.p_values_` (deprecated)
  - p-values: `cph.summary['p']` or `cph.summary.loc['covariate', 'p']`
  - hazard ratios: `cph.summary['exp(coef)']` or `np.exp(cph.params_['covariate'])`
  - coefficients: `cph.params_` or `cph.summary['coef']`
- Schoenfeld residuals test: Use `proportional_hazard_test(cph, df, time_transform='rank')`
  - Returns a DataFrame with columns: test_statistic, p, name
  - Access p-value for a covariate: `result.summary.loc['covariate', 'p']`
- Stratified Cox: Use `strata=['column_name']` parameter in CoxPHFitter.fit()

### scipy.stats
- ttest_ind returns (statistic, pvalue) - access with .statistic and .pvalue attributes or indexing

### statsmodels
- For OLS/GLM: Use `model.fit()` then access `results.pvalues`, `results.params`
- mannwhitneyu: returns (statistic, pvalue) tuple
"""


# ─────────────────────────────────────────────────────────────
# Ground truth loading
# ─────────────────────────────────────────────────────────────

def load_ground_truth_ops(
    datasets: List[str],
    complexities: List[str],
    max_ops: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Load operations from ground truth, filtered by dataset and complexity."""
    with open(GT_FILE) as f:
        gt = json.load(f)

    ops = []
    for ds_name, ds in gt["datasets"].items():
        if ds_name not in datasets:
            continue
        for op_id, op in ds["operations"].items():
            if op.get("complexity", "medium") not in complexities:
                continue
            ops.append({
                "op_id": op_id,
                "dataset": ds_name,
                "prompt": op["prompt"],
                "ground_truth": op["ground_truth"],
                "tolerance": op["tolerance"],
                "category": op.get("category", ""),
                "complexity": op.get("complexity", "medium"),
                "files": ds.get("files", {}),
                "dataset_description": ds.get("description", ""),
            })

    if max_ops:
        ops = ops[:max_ops]
    return ops


def _file_descriptions(op: Dict) -> str:
    """Build file description string for the prompt."""
    lines = []
    for key, filename in op["files"].items():
        lines.append(f"- {filename} ({key})")
    return "\n".join(lines) if lines else "None"


# ─────────────────────────────────────────────────────────────
# Verification engine
# ─────────────────────────────────────────────────────────────

def verify_results(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    tolerance: Any,
) -> Dict[str, Any]:
    """Compare actual results against ground truth.

    Returns dict with:
        passed: bool (all fields match)
        field_results: {field: {expected, actual, passed, error}}
    """
    field_results = {}
    all_pass = True

    for key, expected_val in expected.items():
        actual_val = actual.get(key)
        field_pass = False
        error = ""

        if actual_val is None:
            error = "missing"
        elif isinstance(expected_val, list):
            # Set overlap comparison
            field_pass, error = _verify_set(actual_val, expected_val, tolerance)
        elif isinstance(expected_val, (int, float)):
            field_pass, error = _verify_numeric(
                actual_val, expected_val, tolerance, key
            )
        else:
            # String or other exact match
            field_pass = str(actual_val) == str(expected_val)
            if not field_pass:
                error = f"expected {expected_val}, got {actual_val}"

        if not field_pass:
            all_pass = False

        field_results[key] = {
            "expected": expected_val,
            "actual": actual_val,
            "passed": field_pass,
            "error": error,
        }

    return {"passed": all_pass, "field_results": field_results}


def _verify_numeric(
    actual: Any, expected: float, tolerance: Any, key: str
) -> tuple:
    """Verify a numeric value against tolerance."""
    try:
        actual_f = float(actual)
    except (TypeError, ValueError):
        return False, f"not numeric: {actual}"

    if tolerance == "exact":
        passed = actual_f == expected
        return passed, "" if passed else f"expected {expected}, got {actual_f}"

    # Per-field tolerance (dict)
    if isinstance(tolerance, dict):
        tol = tolerance.get(key, 0.01)
    else:
        tol = tolerance

    # Handle per-field "exact" tolerance
    if tol == "exact":
        passed = actual_f == expected
        return passed, "" if passed else f"expected {expected}, got {actual_f}"

    tol = float(tol)
    diff = abs(actual_f - expected)
    passed = diff <= tol
    return passed, "" if passed else f"|{actual_f} - {expected}| = {diff:.6f} > {tol}"


def _verify_set(actual: Any, expected: list, tolerance: Any) -> tuple:
    """Verify set/list overlap."""
    if not isinstance(actual, list):
        try:
            actual = list(actual)
        except (TypeError, ValueError):
            return False, f"not a list: {actual}"

    if tolerance == "set_overlap_8_of_10":
        overlap = len(set(actual) & set(expected))
        passed = overlap >= 8
        return passed, "" if passed else f"overlap={overlap}/10, need 8"

    # Exact set match
    passed = set(actual) == set(expected)
    return passed, "" if passed else f"sets differ"


def build_extraction_code(ground_truth: Dict[str, Any]) -> str:
    """Build Python code that extracts result values from the kernel namespace.

    The extraction code introspects all variables in the namespace,
    looks for matches by name patterns, and outputs JSON.
    """
    keys = list(ground_truth.keys())
    keys_json = json.dumps(keys)
    # Q4 (Valerio, 24 Oct): the expected values reach the kernel as a JSON string parsed there. Written into the code
    # as JSON, a boolean was the text `false`, a NameError in Python, so the extraction ran nothing for an operation
    # with a boolean field (lung_9_schoenfeld's any_violation): every attempt of it failed, in the submitted harness too
    expected_json = repr(json.dumps(ground_truth))

    code = f"""
import json as _json
import pandas as _pd
import numpy as _np

_gt_keys = {keys_json}
_expected = _json.loads({expected_json})
_results = {{}}

def _extract_value(_v):
    # Safely extract a Python-native value from a variable
    try:
        if isinstance(_v, (int, float, str, bool)):
            return _v
        if isinstance(_v, _np.integer):
            return int(_v)
        if isinstance(_v, _np.floating):
            return float(_v)
        if hasattr(_v, 'item'):
            return _v.item()
        if isinstance(_v, _pd.DataFrame):
            return _v.shape[0]  # Return row count for DataFrames
        if isinstance(_v, _pd.Series):
            if len(_v) == 1:
                return _v.iloc[0]
            return len(_v)  # likely a count
        if isinstance(_v, (list, tuple)) and len(_v) > 0:
            return list(_v)
        if hasattr(_v, 'tolist'):
            return _v.tolist()
        return _v
    except:
        return str(_v)

# Get all user-defined variables (exclude private/system)
_all_vars = {{k: v for k, v in dict(globals()).items()
             if not k.startswith('_') and k not in ('In', 'Out', 'get_ipython', 'exit', 'quit')}}

# Strategy 1: Exact name matches (highest priority)
for _k in _gt_keys:
    if _k in _all_vars:
        _results[_k] = _extract_value(_all_vars[_k])

# Strategy 2: Substring matches (bidirectional)
for _k in _gt_keys:
    if _k in _results:
        continue
    for _vname, _vval in sorted(_all_vars.items(), key=lambda x: len(x[0])):
        _kl = _k.lower().replace('_', '')
        _vl = _vname.lower().replace('_', '')
        if _kl in _vl or _vl in _kl:
            _results[_k] = _extract_value(_vval)
            break

# Strategy 3: For numeric expected values, scan all scalars for close matches
for _k in _gt_keys:
    if _k in _results:
        continue
    _exp = _expected[_k]
    if not isinstance(_exp, (int, float)):
        continue
    for _vname, _vval in _all_vars.items():
        try:
            _fval = float(_vval) if isinstance(_vval, (int, float, _np.integer, _np.floating)) else None
            if _fval is None and hasattr(_vval, 'item'):
                _fval = float(_vval.item())
            if _fval is not None and abs(_fval - _exp) / max(abs(_exp), 1e-9) < 0.1:
                _results[_k] = _fval
                break
        except:
            pass

# Strategy 4: DataFrame shape inference for dimension-related keys
_dim_row_keys = {{'genes', 'n_patients', 'metadata_rows', 'n_events'}}
_dim_col_keys = {{'samples', 'n_variables'}}
for _k in _gt_keys:
    if _k in _results:
        continue
    if _k not in _dim_row_keys and _k not in _dim_col_keys:
        continue
    # Collect all DataFrames
    _dfs = {{_vn: _vv for _vn, _vv in _all_vars.items() if isinstance(_vv, _pd.DataFrame)}}
    if not _dfs:
        continue
    # Try to find a DataFrame whose name matches part of the key
    _best_df = None
    _kparts = _k.lower().replace('_', ' ').split()
    for _vn, _vv in _dfs.items():
        _vnl = _vn.lower()
        if any(_part in _vnl for _part in _kparts if len(_part) > 2):
            _best_df = _vv
            break
    # Fallback: for 'genes' use the largest DataFrame, for 'metadata_rows' the smallest
    if _best_df is None:
        _sorted_dfs = sorted(_dfs.values(), key=lambda d: d.shape[0])
        if _k in {{'metadata_rows', 'n_patients', 'n_events'}}:
            _best_df = _sorted_dfs[0]  # smallest
        else:
            _best_df = _sorted_dfs[-1]  # largest
    if _k in _dim_row_keys:
        _results[_k] = _best_df.shape[0]
    elif _k in _dim_col_keys:
        _results[_k] = _best_df.shape[1]

# Output as JSON for parsing
print("__BENCHMARK_RESULTS__")
print(_json.dumps(_results, default=str))
print("__BENCHMARK_END__")
"""
    return code


# ─────────────────────────────────────────────────────────────
# Kernel helpers
# ─────────────────────────────────────────────────────────────

# The outcome of every extraction and introspection run of the current attempt (Q34: an EXEC_TIMEOUT that fires there
# is recorded too, not only one in the generated script). _dispatch sets the list and stores it in the result as
# extract_outcomes and introspect_outcomes, in run order.
_SUPPORT_RUNS: ContextVar[Optional[List[Dict[str, str]]]] = ContextVar("exp_v2_8_support_runs", default=None)


async def _execute_and_collect(kernel, code: str, timeout: int = EXEC_TIMEOUT,
                               stage: Optional[str] = None) -> Dict[str, Any]:
    """Execute code in kernel and collect all outputs. Every site runs at EXEC_TIMEOUT (Q34, D68; they ran 120 s for
    a script, 30 s for extraction and introspection, 60 s for re-execution). outcome is "ok", "error" or
    "exec_timeout" (the limit fired: its own outcome, Q34). stage "extraction" or "introspection" adds the outcome to
    the attempt's _SUPPORT_RUNS. Only code with no stage, the generated code, is import-scanned (D72): extraction and
    introspection are the harness's own code."""
    stdout_parts = []
    stderr_parts = []
    errors = []
    results = []
    timed_out = False

    async for output in kernel.execute(code, timeout=timeout, generated=stage is None):
        timed_out = timed_out or is_exec_timeout(output)
        if output.output_type == "stream":
            if output.stream_name == "stderr":
                stderr_parts.append(output.text or "")
            else:
                stdout_parts.append(output.text or "")
        elif output.output_type == "error":
            errors.append({
                "ename": output.ename,
                "evalue": output.evalue,
                "traceback": output.traceback,
            })
        elif output.output_type == "execute_result":
            results.append(output.data)

    outcome = "exec_timeout" if timed_out else "error" if errors else "ok"
    support_runs = _SUPPORT_RUNS.get()
    if stage is not None and support_runs is not None:
        support_runs.append({"stage": stage, "outcome": outcome})
    return {
        "stdout": "".join(stdout_parts),
        "stderr": "".join(stderr_parts),
        "errors": errors,
        "results": results,
        "success": len(errors) == 0,
        "timed_out": timed_out,
        "outcome": outcome,
    }


def _parse_benchmark_output(stdout: str) -> Optional[Dict[str, Any]]:
    """Parse benchmark results from kernel stdout."""
    match = re.search(
        r'__BENCHMARK_RESULTS__\s*(.*?)\s*__BENCHMARK_END__',
        stdout,
        re.DOTALL,
    )
    if not match:
        return None
    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None


def _extract_from_notebook_cells(
    nb_path: str, ground_truth: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse notebook cell outputs to extract result values.

    Fallback strategy for coder_v2 which stores results in cell outputs
    rather than top-level kernel variables.
    """
    import nbformat

    results = {}
    try:
        nb = nbformat.read(nb_path, as_version=4)
    except Exception as e:
        logger.warning(f"Could not read notebook {nb_path}: {e}")
        return results

    # Collect all text output from executed cells
    all_output_text = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            text = ""
            if output.get("output_type") == "stream":
                text = output.get("text", "")
            elif output.get("output_type") == "execute_result":
                text = output.get("data", {}).get("text/plain", "")
            if text:
                all_output_text.append(text)

    combined_output = "\n".join(all_output_text)

    # For each ground truth key, search for it in the output
    for key, expected_val in ground_truth.items():
        if key in results:
            continue

        # Look for patterns like "key = value", "key: value", "key  value"
        for pattern in [
            rf'\b{re.escape(key)}\s*[=:]\s*([^\n,\]]+)',
            rf'\b{key.replace("_", " ")}\s*[=:]\s*([^\n,\]]+)',
        ]:
            match = re.search(pattern, combined_output, re.IGNORECASE)
            if match:
                val_str = match.group(1).strip()
                try:
                    if isinstance(expected_val, bool):
                        # Q4 (24 Oct): before int, since a bool is an int; "False" went to int(float()), which raised
                        low = val_str.lower()
                        if low not in ("true", "false"):
                            continue
                        results[key] = low == "true"
                    elif isinstance(expected_val, int):
                        results[key] = int(float(val_str))
                    elif isinstance(expected_val, float):
                        results[key] = float(val_str)
                    else:
                        results[key] = val_str
                except (ValueError, TypeError):
                    continue
                break

    return results


# ─────────────────────────────────────────────────────────────
# Config 1: Free-form (single LLM call + kernel)
# ─────────────────────────────────────────────────────────────

def _build_required_variables_section(ground_truth: Dict[str, Any]) -> str:
    """Build a prompt section listing required output variable names."""
    lines = ["You MUST store your final results in these exact variable names:"]
    for key, val in ground_truth.items():
        if isinstance(val, list):
            lines.append(f"- `{key}` = a Python list")
        elif isinstance(val, bool):
            lines.append(f"- `{key}` = a boolean (True or False)")
        elif isinstance(val, float):
            lines.append(f"- `{key}` = a single numeric value (float)")
        elif isinstance(val, int):
            lines.append(f"- `{key}` = a single numeric value (int)")
        else:
            lines.append(f"- `{key}` = result value")
    return "\n".join(lines)


async def _run_free_form(
    op: Dict,
    router: ModelRouter,
    workspace: Path,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Dict[str, Any]:
    """Generate code via single LLM call, execute in kernel, verify."""
    from backend.agents.notebook.kernel import NotebookKernel

    t0 = time.time()

    # Generate code with required variable names
    required_vars = _build_required_variables_section(op["ground_truth"])
    prompt = FREE_FORM_SYSTEM.replace("{prompt}", op["prompt"])
    prompt = prompt.replace("{file_descriptions}", _file_descriptions(op))
    prompt = prompt.replace("{required_variables}", required_vars)

    # No options (cuts.md exp_v2_8:827, D25): the lock sets every setting. A failed call raises LockCallError, which
    # the entry point records as the attempt's call_error (A5)
    response = await router.generate(
        model_identifier=gen_model,
        prompt=prompt,
        think=think,
    )
    gen = _generation("code", response)
    code = gen["code"]

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}

    if gen["code_status"] != "ok":
        # An empty reply (or a reply with no code) runs nothing; it used to run str(response) as code (A5). A reply
        # that ended on the length stop runs nothing either, recorded as "length" (D75 Q57)
        exec_outcome, exec_error = _not_run(gen["code_status"])
    else:
        # Execute in kernel
        nb_path = str(workspace / "free_form.ipynb")
        kernel = NotebookKernel(nb_path, str(workspace))
        try:
            await kernel.start()

            # Execute the generated code
            exec_out = await _execute_and_collect(kernel, code)
            exec_outcome = exec_out["outcome"]
            if not exec_out["success"]:
                exec_error = "; ".join(
                    f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
                )
            else:
                # Run extraction code
                extraction = build_extraction_code(op["ground_truth"])
                extract_out = await _execute_and_collect(kernel, extraction, stage="extraction")

                actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
                verification = verify_results(
                    actual_results, op["ground_truth"], op["tolerance"]
                )
        except PASS_THROUGH:
            raise
        except Exception as e:
            exec_outcome = _outcome_of_exception(e)
            exec_error = str(e)
        finally:
            await kernel.stop()

    # Judge Evaluation (if failed)
    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, exec_error or str(verification["field_results"]), router
        )

    return {
        "config": "free_form",
        "code": code,                       # whole (cuts.md exp_v2_8:891, D37)
        "generations": [gen],
        "exec_outcome": exec_outcome,
        "passed": verification["passed"],
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": verification["field_results"],
        "actual_results": actual_results,
        "exec_error": exec_error,
        "latency_s": time.time() - t0,
        "n_cells": 1,
        "n_llm_calls": 1,
        "n_retries": 0,
    }


async def _run_free_form_n3(
    op: Dict,
    router: ModelRouter,
    workspace: Path,
    strategy: str = "best",  # "best" or "combined"
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Dict[str, Any]:
    """Generate N scripts, judge picks best or combines, execute winner."""
    from backend.agents.notebook.kernel import NotebookKernel

    t0 = time.time()
    n_candidates = N_FREE_FORM_CANDIDATES
    config_name = f"free_form_n3_{strategy}"

    required_vars = _build_required_variables_section(op["ground_truth"])
    prompt = FREE_FORM_SYSTEM.replace("{prompt}", op["prompt"])
    prompt = prompt.replace("{file_descriptions}", _file_descriptions(op))
    prompt = prompt.replace("{required_variables}", required_vars)

    # Generate N candidate scripts. Candidate k (1-based) of the draw sends seed draw * 1000 + k (Q32, D68), so the
    # three requests differ in their seed; with one seed for all three they would come out identical.
    # No options (cuts.md exp_v2_8:931, D25). An empty candidate stays empty (it was str(response), A5).
    candidates = []
    generations = []
    for i in range(n_candidates):
        with lock_adapter.candidate(i + 1):
            response = await router.generate(
                model_identifier=gen_model,
                prompt=prompt,
                think=think,
            )
        gen = _generation(f"candidate_{i + 1}", response)
        generations.append(gen)
        code = gen["code"]
        candidates.append(code)
        logger.debug(f"  Candidate {i+1} generated ({len(code)} chars)")

    # Build candidates section for judge
    candidates_section = ""
    for i, c in enumerate(candidates, 1):
        candidates_section += f"## Candidate {i}\n```python\n{c}\n```\n\n"

    # Judge: pick best or combine
    if strategy == "best":
        judge_prompt = JUDGE_PICK_BEST.format(
            n=n_candidates,
            prompt=op["prompt"],
            file_descriptions=_file_descriptions(op),
            required_variables=required_vars,
            candidates_section=candidates_section,
        )
        # The pick is part of the method, so it runs as the generator (D66, limits.md Class S); no options
        # (cuts.md exp_v2_8:969)
        judge_response = await router.generate(
            model_identifier=gen_model,
            prompt=judge_prompt,
            think=think,
        )
        generations.append(_generation("pick", judge_response, code=False))
        judge_text = judge_response.get("response", "").strip()
        # Only a stated pick counts (Class X, limits.md exp_v2_8:972-976; D75 Q58: a first line naming exactly one
        # candidate number in range): the first digit 1 to 3 anywhere in the text is no longer read. An unparsed
        # reply is recorded as pick "unparsed", and candidate 1 runs as Mentori's fallback, recorded as
        # picked_fallback 1 (D75 Q58: kept, the count reported per model beside the best-of-3 pass rates).
        picked = parse_stated_pick(judge_text, n_candidates)
        if picked is None:
            pick, picked_fallback, picked = "unparsed", 1, 1
        else:
            pick, picked_fallback = picked, None
        code = candidates[picked - 1]
        code_status = generations[picked - 1]["code_status"]
        logger.debug(f"  Judge picked candidate {pick}")
    else:  # combined
        judge_prompt = JUDGE_COMBINE.format(
            n=n_candidates,
            prompt=op["prompt"],
            file_descriptions=_file_descriptions(op),
            required_variables=required_vars,
            candidates_section=candidates_section,
        )
        # No options (cuts.md exp_v2_8:990); the combined script is extracted by the D69 Q35 rule
        judge_response = await router.generate(
            model_identifier=gen_model,
            prompt=judge_prompt,
            think=think,
        )
        gen = _generation("combine", judge_response)
        generations.append(gen)
        code, code_status = gen["code"], gen["code_status"]
        pick, picked_fallback = "combined", None
        logger.debug(f"  Judge wrote combined script ({len(code)} chars)")

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}

    if code_status != "ok":
        exec_outcome, exec_error = _not_run(code_status)   # nothing to run (A5), or the length stop (D75 Q57)
    else:
        # Execute the winning/combined script
        nb_path = str(workspace / f"{config_name}.ipynb")
        kernel = NotebookKernel(nb_path, str(workspace))
        try:
            await kernel.start()
            exec_out = await _execute_and_collect(kernel, code)
            exec_outcome = exec_out["outcome"]
            if not exec_out["success"]:
                exec_error = "; ".join(
                    f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
                )
            else:
                extraction = build_extraction_code(op["ground_truth"])
                extract_out = await _execute_and_collect(kernel, extraction, stage="extraction")
                actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
                verification = verify_results(
                    actual_results, op["ground_truth"], op["tolerance"]
                )
        except PASS_THROUGH:
            raise
        except Exception as e:
            exec_outcome = _outcome_of_exception(e)
            exec_error = str(e)
        finally:
            await kernel.stop()

    # Judge Evaluation (if failed)
    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, exec_error or str(verification["field_results"]), router
        )

    # n_llm_calls: N candidates + 1 judge
    n_llm_calls = n_candidates + 1

    return {
        "config": config_name,
        "code": code,                       # whole (cuts.md exp_v2_8:1038, D37)
        "generations": generations,         # every candidate, and the pick or combine reply, whole
        "pick": pick,                       # 1 to 3, "unparsed" or "combined"
        "picked_fallback": picked_fallback,
        "exec_outcome": exec_outcome,
        "n_candidates": n_candidates,
        "strategy": strategy,
        "passed": verification["passed"],
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": verification["field_results"],
        "actual_results": actual_results,
        "exec_error": exec_error,
        "latency_s": time.time() - t0,
        "n_cells": 1,
        "n_llm_calls": n_llm_calls,
        "n_retries": 0,
    }


# ─────────────────────────────────────────────────────────────
# Configs 2-3: coder_v2 with N_CANDIDATES monkeypatch
# ─────────────────────────────────────────────────────────────

def _step_failure_reason(step_number: Any, cell_evaluations: List[Dict[str, Any]]) -> str:
    """D75 Q101: the reason a coder_v2 step failed when its step_failed event carries no error text. coder_v2 sends
    that event with error None when the step's execution created no cell and raised nothing (coder_v2.py:512-518);
    the reason written is the status and feedback of the step's last cell evaluation, which sent it to that
    execution. A step with no evaluation (its first execution created no cell) says so; another step's evaluation is
    never written as this step's reason."""
    same = [e for e in cell_evaluations if e.get("step_number") == step_number]
    if not same:
        return f"step {step_number}: no cell created, no error text, no evaluation of this step"
    last = same[-1]
    return (f"step {step_number}: no cell created after its last evaluation (status {last.get('status')}, "
            f"feedback: {last.get('feedback')})")


class _LengthRecords:
    """D114 Q29 O2: the length stops of the current attempt, read from its own call records as they are written: the
    lines of <sink>/calls.jsonl that carry its ctx_uid and are a generator call that ended on "length" (_is_length).
    It reads from the file's size at the attempt's start, only whole lines, and changes nothing: no call is wrapped, so
    every record (its call_site included) is written as without the rule."""

    def __init__(self):
        ctx = rc.current()
        self.path, self.uid = ctx.sink / "calls.jsonl", ctx.ctx_uid
        self.offset = self.path.stat().st_size if self.path.exists() else 0
        self.stops: List[Dict[str, Any]] = []

    def count(self) -> int:
        """The attempt's length stops so far (the records written up to now)."""
        if self.path.exists():
            with open(self.path, "rb") as f:
                f.seek(self.offset)
                data = f.read()
            end = data.rfind(b"\n") + 1
            self.offset += end
            for line in data[:end].splitlines():
                rec = json.loads(line)
                if rec.get("ctx_uid") == self.uid and _is_length(rec):
                    self.stops.append({"seq": rec.get("seq"), "call_site": rec.get("call_site")})
        return len(self.stops)


def _length_note(length_stop: Dict[str, Any]) -> str:
    """The exec_error text of an attempt ended by its first length stop (D114 Q29 O2)."""
    first, step = length_stop["first"], length_stop.get("step_number")
    return (f"the attempt ended at its first length stop (seq {first['seq']}, {first['call_site']}), at "
            f"{length_stop['ended_at']}{f' of step {step}' if step is not None else ''} ({LENGTH_RULE_DECISION})")


async def _length_end_result(config: str, op: Dict, router: ModelRouter, stop: LengthStopEnd,
                             latency_s: float) -> Dict[str, Any]:
    """D114 Q29 O2: the result of an attempt that a config (one whose calls the harness makes) ended at its first
    length stop (LengthStopEnd): exec_outcome "length", not passed, nothing run after the stop; the soft-pass judge
    reads the note, as it reads any failed attempt's error. The stage's generation is stored; the attempt's every call
    is in its records (exp_05 stores them with the entry)."""
    length_stop = {"rule": "stop", "decision": LENGTH_RULE_DECISION, "ended_at": stop.generation.get("stage"),
                   "step_number": None, "first": dict(stop.first), "n": 1, "calls_refused": 0}
    note = _length_note(length_stop)
    judge_score, judge_comment = await _evaluate_failed_result(op, {}, note, router)
    return {
        "config": config,
        "code": stop.generation.get("code") or "",
        "generations": [stop.generation],
        "exec_outcome": "length",
        "passed": False,
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": {},
        "actual_results": {},
        "exec_error": note,
        "latency_s": latency_s,
        "n_cells": 0,
        "n_llm_calls": None,   # not counted when the attempt ended early; exp_05's n_calls counts the records
        "n_retries": None,
        "length_stop_rule": "stop",
        "length_stop": length_stop,
    }


async def _run_coder_v2(
    op: Dict,
    router: ModelRouter,
    user_id: str,
    workspace: Path,
    n_candidates: int = 3,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
    cell_strategy: str = "single",
) -> Dict[str, Any]:
    """Run coder_loop_v2 with specified N_CANDIDATES, then verify."""
    import backend.agents.notebook.algorithm as algo_module
    from backend.agents.notebook.coder_v2 import coder_loop_v2
    from backend.agents.notebook.kernel import KernelRegistry
    from backend.agents.session_context import SessionContext

    t0 = time.time()
    config_name = f"coder_v2_n{n_candidates}"
    if cell_strategy != "single":
        config_name += f"_cell3_{cell_strategy.replace('best_of_3', 'best').replace('combined', 'combined')}"

    # Monkeypatch N_CANDIDATES
    original_n = algo_module.N_CANDIDATES
    algo_module.N_CANDIDATES = n_candidates

    task_id = str(uuid.uuid4())

    # No database read: the session's user is the id the entry point passes (its run id) and the address Mentori
    # fell back to when the database had no such user. coder_v2 uses them as labels only (the memory vault's
    # metadata); the copy has no database, so the read raised "no such table: user" on every coder_v2 attempt.
    ctx = SessionContext(
        user_id=user_id,
        user_email="admin@mentori",
        user_role="admin",
        task_id=task_id,
        task_display_id=task_id[:8],
        task_title=f"V2-8: {op['op_id']}",
        workspace_path=str(workspace),
        model_identifier=gen_model,
        mode="coder",
        api_keys={},
    )

    # Build prompt without file paths — let environment gathering phase discover them
    messages = [{"role": "user", "content": op["prompt"]}]
    history_log = []

    events = []
    answer = ""
    exec_error = ""
    # D75 Q101 changes only the record: the soft-pass judge reads exec_error as it was written before (a step_failed
    # with no error text as "Step failed: None"), so its score does not move; judged_error is that text
    judged_error = ""
    exec_outcome = None
    n_retries = 0              # coder_v2's "step_retry" events; it counted "cell_retry", which coder_v2 never emits
    n_idle_recovered = 0
    cell_evaluations = []      # every evaluation: step, score (None unless status "ok"), status (A5)
    cell_candidates = []       # cell3 strategies: the candidates, the judge's reply and its pick
    n_step_exec_timeouts = 0   # step cells whose run hit EXEC_TIMEOUT (Q34)
    reexec_outcomes = []       # the outcome of each code cell when the notebook is re-run for verification
    code_sources = []          # the notebook's code cells whole, the code this attempt generated (D37)

    # D114 Q29 O2: under "stop" the attempt's own call records are read at each event coder_loop_v2 yields (it runs
    # only when the next event is asked for, so nothing is called while an event is handled), and once more after
    # the loop; the attempt ends at the first event after its first length stop
    length_rule = LENGTH_STOP.get()
    if length_rule not in LENGTH_STOP_RULES:
        raise LockError(f"length-stop rule {length_rule!r} is not one of {LENGTH_STOP_RULES}; nothing was run")
    watch = _LengthRecords() if length_rule == "stop" else None
    gate = _LengthGate() if watch is not None else None   # refuses the attempt's generator calls after its first stop
    tasks_before = asyncio.all_tasks() if gate is not None else set()
    gated = ExitStack()
    length_stop = None

    def ended_at(where: str, step_number: Any) -> Dict[str, Any]:
        return {"rule": length_rule, "decision": LENGTH_RULE_DECISION, "ended_at": where,
                "step_number": step_number, "first": dict(watch.stops[0]), "n": len(watch.stops),
                "calls_refused": gate.refused}

    loop = coder_loop_v2(
        model_router=router,
        model_identifier=gen_model,
        messages=messages,
        session_context=ctx,
        max_steps=CODER_V2_MAX_STEPS,
        think=think if think is not None else False,
        history_log=history_log,
        cell_strategy=cell_strategy,
    )

    if gate is not None:
        gated.enter_context(rc.gate(gate))   # before the loop runs: what it starts sees the gate too

    try:
        async for event in loop:
            event_type = event.get("type", "")
            events.append(event_type)
            if watch is not None and watch.count():
                # D114 Q29 O2: the attempt holds a length stop, so it ends at this event (handled, then the loop is
                # closed: no retry, no later step)
                length_stop = ended_at(event_type, event.get("step_number"))
            if event_type == "cell_evaluation":
                cell_evaluations.append({k: event.get(k) for k in (
                    "step_number", "cell_id", "score", "status", "meets_expectations", "should_retry", "feedback",
                    "issues")})
            elif event_type == "cell_candidates":
                cell_candidates.append({k: v for k, v in event.items() if k != "type"})
            elif event_type == "cell_event":
                inner = event.get("event") or {}
                if inner.get("type") == "output" and is_exec_timeout(inner.get("output")):
                    n_step_exec_timeouts += 1

            if event_type == "complete":
                answer = event.get("content", "")
            elif event_type == "chunk":
                answer += event.get("content", "")
            elif event_type == "error":
                exec_error = judged_error = event.get("content", str(event))
            elif event_type == "step_failed":
                # Collect step execution errors. A step that failed its own evaluation without raising carries no
                # error text (it wrote "Step failed: None"): the record writes the last evaluation's status and
                # feedback in its place (D75 Q101); the outcome and the judge's input are unchanged
                step_err = event.get("error", str(event))
                judged_error += f"{' | ' if judged_error else ''}Step failed: {step_err}"
                if step_err is None:
                    step_err = _step_failure_reason(event.get("step_number"), cell_evaluations)
                exec_error += f"{' | ' if exec_error else ''}Step failed: {step_err}"
            elif event_type == "step_retry" and length_stop is None:
                n_retries += 1   # a retry the length stop ends before it is made is not counted
            elif event_type == "idle_cell_recovered":
                n_idle_recovered += 1

            if length_stop is not None:
                break   # the attempt ends here: the loop is closed below

    except (LockError, rc.RunContextError):
        raise   # a refusal is our own setup (D69 Q38), never the attempt's exec_error
    except Exception as e:
        exec_outcome = _outcome_of_exception(e)
        exec_error = judged_error = str(e)
        logger.error(f"coder_v2 error: {e}")
    finally:
        if watch is not None:
            try:
                await loop.aclose()   # D114 Q29 O2: coder_loop_v2 stopped where the attempt ended; nothing more is called
            except Exception as e:
                logger.warning(f"coder_v2 loop did not close cleanly: {e}")
        # Shut down the session kernel spawned by coder_loop_v2 to avoid
        # "Parent appears to have exited" warnings from IPython.
        try:
            await KernelRegistry.stop_all()
        except Exception:
            pass
        if gate is not None:
            try:
                await _await_gated_tasks(gate, tasks_before)   # D114 Q29 O2: they end inside the attempt
            finally:
                gated.close()

    # Restore N_CANDIDATES
    algo_module.N_CANDIDATES = original_n

    if watch is not None and length_stop is None and watch.count():
        # D114 Q29 O2: a length stop in the loop's last calls (no event after it), or before an exception ended it
        length_stop = ended_at("loop_end" if exec_outcome is None else "exception", None)
    if length_stop is not None:
        length_stop["calls_refused"] = gate.refused   # with those refused after the event, in the awaited tasks

    if length_stop is not None:
        # D114 Q29 O2: the first length stop is the attempt's outcome; exec_error keeps what coder_v2 reported (the
        # soft-pass judge reads that, as for any failed attempt) and names the stop; no verification follows
        note = _length_note(length_stop)
        exec_outcome = "length"
        exec_error += f"{' | ' if exec_error else ''}{note}"
        judged_error = judged_error or note

    # Verify: re-execute notebook cells in a fresh kernel for extraction
    actual_results = {}
    verification = {"passed": False, "field_results": {}}

    # Find the notebook path used by coder_v2
    nb_dir = workspace / "notebooks"
    nb_files = sorted(nb_dir.glob("*.ipynb"), key=lambda p: p.stat().st_mtime, reverse=True) if nb_dir.exists() else []

    if nb_files and not exec_error:
        nb_path = str(nb_files[0])
        try:
            # Stop any existing kernel for this path first
            try:
                await KernelRegistry.stop_kernel(nb_path)
            except Exception:
                pass

            # Read the notebook to get all code cells
            import nbformat
            nb = nbformat.read(nb_path, as_version=4)
            code_cells = [c for c in nb.cells if c.cell_type == "code"]

            if code_cells:
                # Start a fresh kernel and re-execute all code cells
                from backend.agents.notebook.kernel import NotebookKernel
                fresh_kernel = NotebookKernel(nb_path, str(workspace))
                await fresh_kernel.start()

                try:
                    # Re-execute each code cell to rebuild the namespace, at EXEC_TIMEOUT (Q34; it was 60 s). The
                    # attempt's exec outcome is that of this re-run: exec_timeout when a cell hit the limit, error
                    # when a cell raised, else ok (each cell's outcome is kept in reexec_outcomes)
                    reexec_outcomes = []
                    for i, cell in enumerate(code_cells):
                        source = "".join(cell.get("source", []))
                        if source.strip():
                            reexec_outcomes.append((await _execute_and_collect(fresh_kernel, source))["outcome"])
                    exec_outcome = ("exec_timeout" if "exec_timeout" in reexec_outcomes
                                    else "error" if "error" in reexec_outcomes else "ok")

                    # Now run the extraction code in the populated namespace
                    extraction = build_extraction_code(op["ground_truth"])
                    extract_out = await _execute_and_collect(fresh_kernel, extraction, stage="extraction")
                    actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
                finally:
                    await fresh_kernel.stop()

            # Fallback: if kernel extraction found nothing, parse notebook cell outputs
            if not actual_results:
                logger.info(f"Kernel extraction empty, trying notebook cell output parsing")
                actual_results = _extract_from_notebook_cells(
                    nb_path, op["ground_truth"]
                )

            verification = verify_results(
                actual_results, op["ground_truth"], op["tolerance"]
            )
        except PASS_THROUGH:
            raise
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            exec_error = exec_error or f"Verification: {e}"
            judged_error = judged_error or f"Verification: {e}"
            exec_outcome = "exception"

    if exec_outcome is None:
        # coder_v2 reported a failed step or an error (no re-run for verification, as submitted), or there was no
        # notebook or no code cell to re-run (A5)
        exec_outcome = "step_failed" if exec_error else "not_run"

    latency = time.time() - t0

    # Judge Evaluation (if failed)
    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, judged_error or str(verification["field_results"]), router
        )

    # Count code cells in the notebook
    n_cells = 0
    if nb_files:
        try:
            import nbformat
            nb = nbformat.read(str(nb_files[0]), as_version=4)
            n_cells = sum(1 for c in nb.cells if c.cell_type == "code")
            # also when a step failed and the notebook was not re-run
            code_sources = ["".join(c.get("source", [])) for c in nb.cells if c.cell_type == "code"]
        except Exception:
            pass

    return {
        "config": config_name,
        "passed": verification["passed"],
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": verification["field_results"],
        "actual_results": actual_results,
        "exec_error": exec_error,
        "latency_s": latency,
        "event_types": events,
        "exec_outcome": exec_outcome,
        "reexec_outcomes": reexec_outcomes,
        "code_cells": code_sources,
        # coder_v2's own history: the plan, each step with its score, the summary (records.md :226, D37); it was
        # built and never stored. default=str keeps any value json cannot write as its text
        "history_log": json.loads(json.dumps(history_log, default=str)),
        "cell_evaluations": cell_evaluations,
        "cell_candidates": cell_candidates,
        "n_step_exec_timeouts": n_step_exec_timeouts,
        "n_candidates": n_candidates,
        "n_cells": n_cells,
        # coder_v2 emits no per-call event (it counted "token_usage", which only coder_loop emits, so it stored 0):
        # not counted here, None (A5); exp_05's n_calls counts the attempt's call records
        "n_llm_calls": None,
        "n_retries": n_retries,
        "n_idle_recovered": n_idle_recovered,
        "length_stop_rule": length_rule,   # D114 Q29 O2
        "length_stop": length_stop,        # under "stop": the event it ended at, its step, the first length stop,
                                           # the generator calls refused after it
    }


async def _evaluate_failed_result(
    op: Dict, actual_results: Dict, error_msg: str, router: ModelRouter,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Tuple[str, str]:
    """Run LLM judge to evaluate if a failure is a 'soft pass'.

    The judge is the lock's ([judge] model, D68 Q33), called in the judge role; gen_model no longer names it.
    The score is "PASS_WITH_RESERVE" or "FAIL" as the judge states it, "unparsed" when its reply states neither, and
    "error" when the call failed (Class X, limits.md exp_v2_8:1281-1290; both were "FAIL"). The verdict never
    decides passed.
    """
    try:
        logger.info("Evaluating failed result with LLM judge...")
        prompt = JUDGE_EVALUATE_RESULT.format(
            prompt=op["prompt"],
            ground_truth=json.dumps(op["ground_truth"], indent=2, default=str),
            actual_results=json.dumps(actual_results, indent=2, default=str),
            error_message=error_msg,   # whole (cuts.md exp_v2_8:1270, D25; it was cut to 2,000 characters)
        )
        # Role "judge": the lock sends its judge's settings (temperature 0, thinking off) and refuses any other
        # model. think is recorded as caller_asked, never sent; no options (cuts.md exp_v2_8:1275).
        with lock_adapter.judge():
            response = await router.generate(
                model_identifier="ollama::" + lock_adapter.load().d["judge"]["model"],
                prompt=prompt,
                think=think,
            )
        text = response.get("response", "").strip()
        logger.info(f"Judge response: {text}")

        score_match = re.search(r"SCORE:\s*(PASS_WITH_RESERVE|FAIL)", text)
        score = score_match.group(1) if score_match else "unparsed"

        comment_match = re.search(r"COMMENT:\s*(.*)", text, re.DOTALL)
        comment = comment_match.group(1).strip() if comment_match else text

        return score, comment
    except (LockError, rc.RunContextError):
        raise   # a refusal is our own setup (D69 Q38), never a judge score
    except Exception as e:
        logger.warning(f"Judge evaluation failed: {e}")
        return "error", f"Judge error: {type(e).__name__}: {e}"


# ─────────────────────────────────────────────────────────────
# NEW ALGORITHMS: Introspection-based approaches
# ─────────────────────────────────────────────────────────────

def _parse_api_info(stdout: str) -> List[Dict]:
    """Extract API info JSON from introspection output."""
    match = re.search(r'__API_INFO__\s*(.*?)\s*__API_END__', stdout, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return []


def _build_api_reference(api_info: List[Dict]) -> str:
    """Build human-readable API reference from introspection results: every method and attribute and the whole
    docstring (cuts.md M19, limits.md #43, D25; it listed 20 methods, 20 attributes and 200 characters of the
    docstring, in the prompts of introspect_then_code, error_recovery_introspect and introspect_with_recovery).

    D75 Q60: an entry is labelled by its module when it has one ("lifelines.KaplanMeierFitter", as before), else by
    the object's type (the recovery introspection's entry for a variable of the script, {"object": "kmf", "type":
    "KaplanMeierFitter"}, is "kmf (a KaplanMeierFitter)"); an error entry with neither (the recovery introspection's
    {"error": ...}) is "introspection error: ...". It read item['module'] for every entry and raised KeyError
    'module' on the latter two, so the two recovery configs ended as "exception" before their retry."""
    def label(item: Dict[str, Any]) -> Optional[str]:
        if item.get("module"):
            return f"{item['module']}.{item.get('object')}"
        if item.get("type"):
            return f"{item.get('object')} (a {item['type']})"
        return item.get("object")

    lines = []
    for item in api_info:
        obj_name = label(item)
        if "error" in item:
            lines.append(f"- {obj_name}: [error: {item['error']}]" if obj_name
                         else f"- [introspection error: {item['error']}]")
            continue
        obj_name = obj_name or "(unnamed object)"
        if item.get("methods"):
            lines.append(f"- {obj_name} methods: {', '.join(item['methods'])}")
        if item.get("attributes"):
            lines.append(f"- {obj_name} attributes: {', '.join(item['attributes'])}")
        if item.get("docstring"):
            lines.append(f"  Docstring: {item['docstring']}")
    return "\n".join(lines) if lines else "(no API info available)"


def _identify_failing_object(error_msg: str) -> Optional[Dict]:
    """Parse an AttributeError to identify the object and missing attribute."""
    # Pattern: 'ClassName' object has no attribute 'attr_name'
    match = re.search(r"'(\w+)'\s+object has no attribute\s+'(\w+)'", error_msg)
    if match:
        return {"class_name": match.group(1), "missing_attr": match.group(2)}
    # Pattern: AttributeError: ClassName has no attribute 'attr_name'
    match = re.search(r"AttributeError:\s+(\w+)\s+has no attribute\s+'(\w+)'", error_msg)
    if match:
        return {"class_name": match.group(1), "missing_attr": match.group(2)}
    return None


async def _run_introspect_then_code(
    op: Dict,
    router: ModelRouter,
    workspace: Path,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Dict[str, Any]:
    """
    Algorithm 1: Introspect-Then-Code

    Step 1: Ask LLM to identify needed libraries/classes from the prompt
    Step 2: Run introspection code in kernel to get actual API info
    Step 3: Generate code with API reference injected into prompt
    Step 4: Execute and verify
    """
    from backend.agents.notebook.kernel import NotebookKernel

    t0 = time.time()
    n_llm_calls = 0
    generations = []

    # Step 1: Ask LLM to identify what to introspect (no options: cuts.md exp_v2_8:827, D25)
    analysis_prompt = INTROSPECT_ANALYSIS_PROMPT.format(prompt=op["prompt"])
    analysis_response = await router.generate(
        model_identifier=gen_model,
        prompt=analysis_prompt,
        think=think,
    )
    n_llm_calls += 1
    generations.append(_generation("analysis", analysis_response, code=False))

    analysis_text = analysis_response.get("response", "")

    # Parse the JSON array
    to_introspect = []
    json_match = re.search(r'\[.*\]', analysis_text, re.DOTALL)
    if json_match:
        try:
            to_introspect = json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Step 2: Build and execute introspection code
    nb_path = str(workspace / "introspect_then_code.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    api_info = []
    exec_outcome = None
    code = ""
    try:
        await kernel.start()

        if to_introspect:
            introspect_blocks = ""
            for item in to_introspect:
                module = item.get("module", "")
                obj = item.get("object", "")
                if module and obj:
                    introspect_blocks += INTROSPECT_BLOCK_TEMPLATE.format(
                        module=module, object=obj
                    )

            if introspect_blocks:
                introspect_code = INTROSPECT_CODE_TEMPLATE.format(
                    introspect_blocks=introspect_blocks
                )
                intro_out = await _execute_and_collect(kernel, introspect_code, stage="introspection")
                api_info = _parse_api_info(intro_out["stdout"])

        # Step 3: Generate code with API reference
        api_reference = _build_api_reference(api_info)
        required_vars = _build_required_variables_section(op["ground_truth"])

        prompt = FREE_FORM_WITH_API_SYSTEM.replace("{prompt}", op["prompt"])
        prompt = prompt.replace("{file_descriptions}", _file_descriptions(op))
        prompt = prompt.replace("{required_variables}", required_vars)
        prompt = prompt.replace("{api_reference}", api_reference)

        response = await router.generate(
            model_identifier=gen_model,
            prompt=prompt,
            think=think,
        )
        n_llm_calls += 1
        gen = _generation("code", response)
        generations.append(gen)
        code = gen["code"]

        actual_results = {}
        exec_error = ""
        verification = {"passed": False, "field_results": {}}

        # Step 4: Execute and verify (an empty reply runs nothing, A5)
        if gen["code_status"] != "ok":
            exec_outcome, exec_error = _not_run(gen["code_status"])   # A5; "length", D75 Q57
        else:
            exec_out = await _execute_and_collect(kernel, code)
            exec_outcome = exec_out["outcome"]

            if not exec_out["success"]:
                exec_error = "; ".join(
                    f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
                )
            else:
                extraction = build_extraction_code(op["ground_truth"])
                extract_out = await _execute_and_collect(kernel, extraction, stage="extraction")
                actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
                verification = verify_results(
                    actual_results, op["ground_truth"], op["tolerance"]
                )

    except PASS_THROUGH:
        raise
    except Exception as e:
        exec_outcome = _outcome_of_exception(e)
        exec_error = str(e)
        actual_results = {}
        verification = {"passed": False, "field_results": {}}
        # the generated code is kept (it was reset to ""); it stays in generations as well (D37)
    finally:
        await kernel.stop()

    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, exec_error or str(verification["field_results"]), router
        )

    return {
        "config": "introspect_then_code",
        "code": code,                       # whole (cuts.md exp_v2_8:1461, D37)
        "generations": generations,
        "exec_outcome": exec_outcome,
        "api_info": api_info,               # whole (cuts.md M5; it kept the first 5)
        "passed": verification["passed"],
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": verification["field_results"],
        "actual_results": actual_results,
        "exec_error": exec_error,
        "latency_s": time.time() - t0,
        "n_cells": 1,
        "n_llm_calls": n_llm_calls,
        "n_retries": 0,
    }


async def _run_error_recovery_introspect(
    op: Dict,
    router: ModelRouter,
    workspace: Path,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
    max_retries: int = MAX_RECOVERY_RETRIES,
) -> Dict[str, Any]:
    """
    Algorithm 2: Error Recovery with Introspection

    Step 1: Generate code normally (free_form)
    Step 2: Execute
    Step 3: If AttributeError/TypeError, introspect the failing object
    Step 4: Retry generation with introspection info
    Step 5: Execute and verify
    """
    from backend.agents.notebook.kernel import NotebookKernel

    t0 = time.time()
    n_llm_calls = 0
    n_retries = 0

    required_vars = _build_required_variables_section(op["ground_truth"])
    prompt = FREE_FORM_SYSTEM.replace("{prompt}", op["prompt"])
    prompt = prompt.replace("{file_descriptions}", _file_descriptions(op))
    prompt = prompt.replace("{required_variables}", required_vars)

    # Step 1: Initial generation (no options: cuts.md exp_v2_8:1508, D25)
    response = await router.generate(
        model_identifier=gen_model,
        prompt=prompt,
        think=think,
    )
    n_llm_calls += 1
    gen = _generation("code", response)
    generations = [gen]
    code = gen["code"]

    nb_path = str(workspace / "error_recovery_introspect.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}
    introspect_output = ""
    exec_outcome = None

    try:
        await kernel.start()

        for attempt in range(max_retries + 1):
            # A reply with no code runs nothing and ends the attempt (A5; it ran str(response) or "")
            if gen["code_status"] != "ok":
                exec_outcome, exec_error = _not_run(gen["code_status"])   # A5; "length", D75 Q57
                break

            # Execute the code
            exec_out = await _execute_and_collect(kernel, code)
            exec_outcome = exec_out["outcome"]

            if exec_out["success"]:
                # Success - extract results
                extraction = build_extraction_code(op["ground_truth"])
                extract_out = await _execute_and_collect(kernel, extraction, stage="extraction")
                actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
                verification = verify_results(
                    actual_results, op["ground_truth"], op["tolerance"]
                )
                break

            # Check if it's an AttributeError we can recover from
            exec_error = "; ".join(
                f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
            )

            if attempt >= max_retries:
                break

            # Look for AttributeError pattern
            failing_info = _identify_failing_object(exec_error)
            if not failing_info:
                # Not a recoverable error
                break

            n_retries += 1
            class_name = failing_info["class_name"]

            # Run introspection on the failing class
            introspect_code = f"""
import json as _json
_api_info = []
try:
    # Try common library imports
    for _mod in ['lifelines', 'scipy.stats', 'sklearn', 'pandas', 'statsmodels.api']:
        try:
            _m = __import__(_mod, fromlist=[''])
            if hasattr(_m, '{class_name}'):
                _obj = getattr(_m, '{class_name}')
                _info = {{"module": _mod, "object": "{class_name}", "methods": [], "attributes": []}}
                for _name in dir(_obj):
                    if _name.startswith('_'):
                        continue
                    _attr = getattr(_obj, _name, None)
                    if callable(_attr):
                        _info["methods"].append(_name)
                    else:
                        _info["attributes"].append(_name)
                _api_info.append(_info)
                break
        except:
            pass
    # Also try to introspect any existing instance in namespace
    for _vname, _vval in dict(globals()).items():
        if type(_vval).__name__ == '{class_name}':
            _info = {{"object": _vname, "type": "{class_name}", "methods": [], "attributes": []}}
            for _name in dir(_vval):
                if _name.startswith('_'):
                    continue
                _attr = getattr(_vval, _name, None)
                if callable(_attr):
                    _info["methods"].append(_name)
                else:
                    _info["attributes"].append(_name)
            _api_info.append(_info)
            break
except Exception as _e:
    _api_info.append({{"error": str(_e)}})

print("__API_INFO__")
print(_json.dumps(_api_info, indent=2))
print("__API_END__")
"""
            intro_out = await _execute_and_collect(kernel, introspect_code, stage="introspection")
            api_info = _parse_api_info(intro_out["stdout"])
            introspect_output = _build_api_reference(api_info)

            # Retry with error context (include file info to avoid FileNotFoundError)
            retry_prompt = ERROR_RECOVERY_INTROSPECT_PROMPT.format(
                error_message=exec_error,
                introspect_output=introspect_output,
                prompt=op["prompt"],
                file_descriptions=_file_descriptions(op),
                required_variables=required_vars,
            )
            retry_response = await router.generate(
                model_identifier=gen_model,
                prompt=retry_prompt,
                think=think,
            )
            n_llm_calls += 1
            gen = _generation(f"retry_{n_retries}", retry_response)
            generations.append(gen)
            code = gen["code"]

            # Reset kernel for clean retry
            await kernel.stop()
            await kernel.start()

    except PASS_THROUGH:
        raise
    except Exception as e:
        exec_outcome = _outcome_of_exception(e)
        exec_error = str(e)
    finally:
        await kernel.stop()

    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, exec_error or str(verification["field_results"]), router
        )

    return {
        "config": "error_recovery_introspect",
        "code": code,                       # whole (cuts.md exp_v2_8:1646, D37): the last code generated
        "generations": generations,         # the first code and every repair, whole
        "exec_outcome": exec_outcome,
        "introspect_output": introspect_output,   # whole (cuts.md M5; it kept 1,000 characters)
        "passed": verification["passed"],
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": verification["field_results"],
        "actual_results": actual_results,
        "exec_error": exec_error,
        "latency_s": time.time() - t0,
        "n_cells": 1,
        "n_llm_calls": n_llm_calls,
        "n_retries": n_retries,
    }


async def _run_thinker_coder_split(
    op: Dict,
    router: ModelRouter,
    workspace: Path,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Dict[str, Any]:
    """
    Algorithm 3: Thinker-Coder Split

    Step 1: THINKER model analyzes task, generates introspection code
    Step 2: Execute introspection to get actual API info
    Step 3: THINKER summarizes API reference
    Step 4: CODER generates code with API reference
    Step 5: Execute and verify
    """
    from backend.agents.notebook.kernel import NotebookKernel

    t0 = time.time()
    n_llm_calls = 0

    # Step 1: Thinker generates introspection code (no options: cuts.md exp_v2_8:1687, D25). Its prompt also ends
    # on an open ```python fence, so the D69 Q35 rule applies (with no ```python block it ran nothing)
    thinker_prompt = THINKER_RESEARCH_PROMPT.format(prompt=op["prompt"])
    thinker_response = await router.generate(
        model_identifier=gen_model,
        prompt=thinker_prompt,
        think=think,
    )
    n_llm_calls += 1
    thinker_gen = _generation("introspection_code", thinker_response)
    generations = [thinker_gen]
    introspect_code = thinker_gen["code"]

    nb_path = str(workspace / "thinker_coder_split.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}
    api_reference = ""
    code = ""
    exec_outcome = None
    introspect_outcome = None

    try:
        await kernel.start()

        if thinker_gen["code_status"] == "length":
            # D75 Q57: the thinker's introspection code is a reply run as code; it ended on the length stop, so
            # nothing runs and the attempt is a length failure (no API summary, no coder call)
            introspect_outcome = "length"
            exec_outcome, exec_error = _not_run("length")
        else:
            # Step 2: Execute introspection code
            introspect_output = ""
            if introspect_code:
                intro_out = await _execute_and_collect(kernel, introspect_code, stage="introspection")
                introspect_outcome = intro_out["outcome"]
                introspect_output = intro_out["stdout"]  # whole (cuts.md exp_v2_8:1712, D25; it was 3,000 characters)

            # Step 3: Thinker summarizes API reference
            if introspect_output:
                summary_prompt = THINKER_API_SUMMARY_PROMPT.format(
                    introspect_output=introspect_output
                )
                summary_response = await router.generate(
                    model_identifier=gen_model,
                    prompt=summary_prompt,
                    think=think,
                )
                n_llm_calls += 1
                generations.append(_generation("api_summary", summary_response, code=False))
                api_reference = summary_response.get("response", "")
            else:
                api_reference = "(No API information gathered)"

            # Step 4: Coder generates code with API reference
            required_vars = _build_required_variables_section(op["ground_truth"])
            coder_prompt = FREE_FORM_WITH_API_SYSTEM.replace("{prompt}", op["prompt"])
            coder_prompt = coder_prompt.replace("{file_descriptions}", _file_descriptions(op))
            coder_prompt = coder_prompt.replace("{required_variables}", required_vars)
            coder_prompt = coder_prompt.replace("{api_reference}", api_reference)

            coder_response = await router.generate(
                model_identifier=gen_model,
                prompt=coder_prompt,
                think=think,
            )
            n_llm_calls += 1
            gen = _generation("code", coder_response)
            generations.append(gen)
            code = gen["code"]

            # Step 5: Execute and verify (an empty reply runs nothing, A5)
            if gen["code_status"] != "ok":
                exec_outcome, exec_error = _not_run(gen["code_status"])   # A5; "length", D75 Q57
            else:
                # Reset kernel for clean execution
                await kernel.stop()
                await kernel.start()

                exec_out = await _execute_and_collect(kernel, code)
                exec_outcome = exec_out["outcome"]

                if not exec_out["success"]:
                    exec_error = "; ".join(
                        f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
                    )
                else:
                    extraction = build_extraction_code(op["ground_truth"])
                    extract_out = await _execute_and_collect(kernel, extraction, stage="extraction")
                    actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
                    verification = verify_results(
                        actual_results, op["ground_truth"], op["tolerance"]
                    )

    except PASS_THROUGH:
        raise
    except Exception as e:
        exec_outcome = _outcome_of_exception(e)
        exec_error = str(e)
    finally:
        await kernel.stop()

    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, exec_error or str(verification["field_results"]), router
        )

    return {
        "config": "thinker_coder_split",
        "code": code,                       # whole (cuts.md exp_v2_8:1782, D37)
        "generations": generations,
        "exec_outcome": exec_outcome,
        "introspect_outcome": introspect_outcome,   # the thinker's introspection code (exec_timeout included, Q34)
        "api_reference": api_reference,     # whole (cuts.md M5; it kept 1,000 characters)
        "passed": verification["passed"],
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": verification["field_results"],
        "actual_results": actual_results,
        "exec_error": exec_error,
        "latency_s": time.time() - t0,
        "n_cells": 1,
        "n_llm_calls": n_llm_calls,
        "n_retries": 0,
    }


async def _run_introspect_with_recovery(
    op: Dict,
    router: ModelRouter,
    workspace: Path,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
    max_retries: int = MAX_RECOVERY_RETRIES,
) -> Dict[str, Any]:
    """
    Algorithm 4: Introspect-With-Recovery (Combined Best Approach)

    Combines pre-emptive introspection with error recovery:
    Step 1: Ask LLM to identify needed libraries/classes
    Step 2: Run introspection to get actual API info
    Step 3: Generate code with API reference + common pitfalls
    Step 4: Execute and verify
    Step 5: If error, introspect the failing object specifically and retry
    """
    from backend.agents.notebook.kernel import NotebookKernel

    t0 = time.time()
    n_llm_calls = 0
    n_retries = 0

    required_vars = _build_required_variables_section(op["ground_truth"])
    file_descs = _file_descriptions(op)

    # Step 1: Ask LLM to identify what to introspect (no options: cuts.md exp_v2_8:1829, D25)
    analysis_prompt = INTROSPECT_ANALYSIS_PROMPT.format(prompt=op["prompt"])
    analysis_response = await router.generate(
        model_identifier=gen_model,
        prompt=analysis_prompt,
        think=think,
    )
    n_llm_calls += 1
    generations = [_generation("analysis", analysis_response, code=False)]
    exec_outcome = None

    analysis_text = analysis_response.get("response", "")
    to_introspect = []
    json_match = re.search(r'\[.*\]', analysis_text, re.DOTALL)
    if json_match:
        try:
            to_introspect = json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    nb_path = str(workspace / "introspect_with_recovery.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    api_info = []
    api_reference = ""
    code = ""
    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}

    try:
        await kernel.start()

        # Step 2: Build and execute introspection code
        if to_introspect:
            introspect_blocks = ""
            for item in to_introspect:
                module = item.get("module", "")
                obj = item.get("object", "")
                if module and obj:
                    introspect_blocks += INTROSPECT_BLOCK_TEMPLATE.format(
                        module=module, object=obj
                    )

            if introspect_blocks:
                introspect_code = INTROSPECT_CODE_TEMPLATE.format(
                    introspect_blocks=introspect_blocks
                )
                intro_out = await _execute_and_collect(kernel, introspect_code, stage="introspection")
                api_info = _parse_api_info(intro_out["stdout"])

        api_reference = _build_api_reference(api_info)

        # Step 3: Generate code with API reference AND common pitfalls
        prompt = INTROSPECT_WITH_RECOVERY_SYSTEM.replace("{prompt}", op["prompt"])
        prompt = prompt.replace("{file_descriptions}", file_descs)
        prompt = prompt.replace("{required_variables}", required_vars)
        prompt = prompt.replace("{api_reference}", api_reference if api_reference else "(No specific API info gathered)")
        prompt = prompt.replace("{common_pitfalls}", COMMON_PITFALLS)

        response = await router.generate(
            model_identifier=gen_model,
            prompt=prompt,
            think=think,
        )
        n_llm_calls += 1
        gen = _generation("code", response)
        generations.append(gen)
        code = gen["code"]

        # Step 4: Execute with retry loop
        for attempt in range(max_retries + 1):
            # A reply with no code runs nothing and ends the attempt (A5)
            if gen["code_status"] != "ok":
                exec_outcome, exec_error = _not_run(gen["code_status"])   # A5; "length", D75 Q57
                break

            # Reset kernel for clean execution
            await kernel.stop()
            await kernel.start()

            exec_out = await _execute_and_collect(kernel, code)
            exec_outcome = exec_out["outcome"]

            if exec_out["success"]:
                # Success - extract results
                extraction = build_extraction_code(op["ground_truth"])
                extract_out = await _execute_and_collect(kernel, extraction, stage="extraction")
                actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
                verification = verify_results(
                    actual_results, op["ground_truth"], op["tolerance"]
                )
                break

            # Get the error
            exec_error = "; ".join(
                f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
            )

            if attempt >= max_retries:
                break

            # Step 5: Error recovery - check if we can introspect the failing object
            failing_info = _identify_failing_object(exec_error)
            if not failing_info:
                # Not a recoverable error type
                break

            n_retries += 1
            class_name = failing_info["class_name"]

            # Introspect the specific failing class
            introspect_code = f"""
import json as _json
_api_info = []
try:
    for _mod in ['lifelines', 'lifelines.statistics', 'scipy.stats', 'sklearn', 'pandas', 'statsmodels.api']:
        try:
            _m = __import__(_mod, fromlist=[''])
            if hasattr(_m, '{class_name}'):
                _obj = getattr(_m, '{class_name}')
                _info = {{"module": _mod, "object": "{class_name}", "methods": [], "attributes": []}}
                for _name in dir(_obj):
                    if _name.startswith('_'):
                        continue
                    _attr = getattr(_obj, _name, None)
                    if callable(_attr):
                        _info["methods"].append(_name)
                    else:
                        _info["attributes"].append(_name)
                _api_info.append(_info)
                break
        except:
            pass
    # Also try to get docstring hints
    for _vname, _vval in dict(globals()).items():
        if type(_vval).__name__ == '{class_name}':
            _info = {{"object": _vname, "type": "{class_name}", "methods": [], "attributes": []}}
            for _name in dir(_vval):
                if _name.startswith('_'):
                    continue
                _attr = getattr(_vval, _name, None)
                if callable(_attr):
                    _info["methods"].append(_name)
                else:
                    _info["attributes"].append(_name)
            _api_info.append(_info)
            break
except Exception as _e:
    _api_info.append({{"error": str(_e)}})

print("__API_INFO__")
print(_json.dumps(_api_info, indent=2))
print("__API_END__")
"""
            intro_out = await _execute_and_collect(kernel, introspect_code, stage="introspection")
            new_api_info = _parse_api_info(intro_out["stdout"])
            new_api_reference = _build_api_reference(new_api_info)

            # Retry with enhanced context (include ALL context)
            retry_prompt = ERROR_RECOVERY_INTROSPECT_PROMPT.format(
                error_message=exec_error,
                introspect_output=new_api_reference + "\n\n" + COMMON_PITFALLS,
                prompt=op["prompt"],
                file_descriptions=file_descs,
                required_variables=required_vars,
            )
            retry_response = await router.generate(
                model_identifier=gen_model,
                prompt=retry_prompt,
                think=think,
            )
            n_llm_calls += 1
            gen = _generation(f"retry_{n_retries}", retry_response)
            generations.append(gen)
            code = gen["code"]

    except PASS_THROUGH:
        raise
    except Exception as e:
        exec_outcome = _outcome_of_exception(e)
        exec_error = str(e)
    finally:
        await kernel.stop()

    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, exec_error or str(verification["field_results"]), router
        )

    return {
        "config": "introspect_with_recovery",
        "code": code,                       # whole (cuts.md exp_v2_8:2012, D37): the last code generated
        "generations": generations,         # the analysis, the first code and every repair, whole
        "exec_outcome": exec_outcome,
        "api_reference": api_reference,     # whole (cuts.md M5; it kept 1,000 characters)
        "passed": verification["passed"],
        "judge_score": judge_score,
        "judge_comment": judge_comment,
        "field_results": verification["field_results"],
        "actual_results": actual_results,
        "exec_error": exec_error,
        "latency_s": time.time() - t0,
        "n_cells": 1,
        "n_llm_calls": n_llm_calls,
        "n_retries": n_retries,
    }


# ─────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────

# D78 Q112: the interpreter the benchmark's kernel reports about itself, set by check_kernel_python (run at the start
# of each variant, exp_05 run_variant); the package fingerprint (D75 Q63) reads this interpreter
_KERNEL_PYTHON: Optional[str] = None


async def check_kernel_python() -> str:
    """D78 Q112: start a kernel as an attempt starts one (spec 'python3', offline), read the interpreter it reports
    about itself (the import probe's sys.executable), stop it, and refuse it as a setup error
    (import_scan.KernelInterpreterMismatch) unless it is exactly the harness's interpreter. Sets and returns
    _KERNEL_PYTHON; a kernel that does not answer the probe is a setup error as well (EnvironmentCheckError)."""
    global _KERNEL_PYTHON
    import tempfile
    from backend.agents.notebook.kernel import NotebookKernel
    _KERNEL_PYTHON = None
    work = tempfile.mkdtemp(prefix="mentori_kernel_python_")
    kernel = NotebookKernel(str(Path(work) / "kernel_python.ipynb"), work)
    try:
        token = kernel_module.OFFLINE.set(True)
        try:
            await kernel.start()
        finally:
            kernel_module.OFFLINE.reset(token)
        reported = (await kernel._probe_imports([]))["executable"]
    except Exception as e:
        raise import_scan.EnvironmentCheckError(f"D78 Q112: the kernel did not report its interpreter: "
                                                f"{type(e).__name__}: {e}") from e
    finally:
        await kernel.stop()
        shutil.rmtree(work, ignore_errors=True)
    import_scan.check_kernel_python(reported, sys.executable)
    _KERNEL_PYTHON = reported
    return reported


async def _dispatch(
    config: str,
    op: Dict,
    router: ModelRouter,
    user_id: str,
    workspace: Path,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Dict[str, Any]:
    """Dispatch to the right config runner.

    Runs inside the run context its entry point set for this attempt (publication/scripts/exp_05_coder_benchmark.py):
    the context's item is the operation, its arm the config, and gen_model the model the run names for the coder
    role. The draw and the thinking setting come from that context; think is recorded as caller_asked and never sent.
    Anything else is refused before the attempt starts.
    """
    ctx = rc.current()   # RunContextError outside a run
    if ctx.item_id != op["op_id"] or ctx.arm != config:
        raise rc.RunContextError(f"the run context is item {ctx.item_id!r} of arm {ctx.arm!r} (run {ctx.run_id}); "
                                 f"this attempt is {op['op_id']!r} of config {config!r}")
    if gen_model != rc.agent_model(CODER_ROLE):   # LockError when the run names no coder
        raise LockError(f"gen_model {gen_model!r} is not the run's {CODER_ROLE} ({rc.agent_model(CODER_ROLE)!r}, "
                        f"run {ctx.run_id})")
    runs: List[Dict[str, str]] = []
    scans: List[Dict[str, Any]] = []
    # D75 Q63: the packages of the interpreter that runs the generated code before the attempt; every kernel of the
    # attempt starts offline. D78 Q112: that interpreter is the one the kernel reported about itself at the variant's
    # start (check_kernel_python, here once per process when nothing ran it), the harness's or the run stopped there
    python = _KERNEL_PYTHON or await check_kernel_python()
    packages_before = import_scan.fingerprint(python)
    token = _SUPPORT_RUNS.set(runs)
    scan_token = import_scan.SCANS.set(scans)   # D72: every execution of generated code is import-scanned
    offline_token = kernel_module.OFFLINE.set(True)
    t0 = time.time()
    try:
        try:
            result = await _run_config(config, op, router, user_id, workspace, gen_model, think)
        except LengthStopEnd as stop:
            # D114 Q29 O2 ("stop"): the config's first length stop ended the attempt; recorded as "length"
            result = await _length_end_result(config, op, router, stop, time.time() - t0)
    finally:
        kernel_module.OFFLINE.reset(offline_token)
        import_scan.SCANS.reset(scan_token)
        _SUPPORT_RUNS.reset(token)
        # D75 Q63: a change stops the run as a setup error (EnvironmentChanged), never an attempt's outcome
        packages_after = import_scan.fingerprint(python)
        import_scan.check_unchanged(packages_before, packages_after,
                                    f"attempt {op['op_id']} of {config} (run {ctx.run_id})")
        # D78 Q112: every kernel the attempt probed ran the fingerprinted interpreter, or the run stops
        import_scan.check_scans_python(scans, python, f"attempt {op['op_id']} of {config} (run {ctx.run_id})")
    # D75 Q63: the fingerprint is recorded with the attempt (sha256 of the sorted `uv pip freeze` lines), before and
    # after, so each record names the environment that ran it
    result["packages_sha256_before"] = import_scan.fingerprint_sha256(packages_before)
    result["packages_sha256_after"] = import_scan.fingerprint_sha256(packages_after)
    # Q34: the outcome of each extraction and introspection run, exec_timeout included, beside exec_outcome
    result["extract_outcomes"] = [r["outcome"] for r in runs if r["stage"] == "extraction"]
    result["introspect_outcomes"] = [r["outcome"] for r in runs if r["stage"] == "introspection"]
    # D72: imports, missing_installed, missing_not_allowed, install_lines, missing_library_not_allowed and
    # import_scans (one record per execution of generated code: modules, classification, any install, the run's first
    # error, its kernel run). An attempt that failed and whose final executions (the ones that set exec_outcome: the
    # last script run, coder_v2's re-run) raised only a ModuleNotFoundError for a not_allowed module stays the
    # model's failure (exec_outcome as computed, "error" for a script) with missing_library_not_allowed True
    result.update(import_scan.attempt_fields(scans, passed=result.get("passed"),
                                             exec_outcome=result.get("exec_outcome")))
    return result


async def _run_config(config: str, op: Dict, router: ModelRouter, user_id: str, workspace: Path, gen_model: str,
                      think: Union[bool, str, None]) -> Dict[str, Any]:
    """The runner of one config (the dispatch of the submitted benchmark)."""
    if config == "free_form":
        return await _run_free_form(op, router, workspace, gen_model=gen_model, think=think)
    elif config == "free_form_n3_best":
        return await _run_free_form_n3(op, router, workspace, strategy="best", gen_model=gen_model, think=think)
    elif config == "free_form_n3_combined":
        return await _run_free_form_n3(op, router, workspace, strategy="combined", gen_model=gen_model, think=think)
    elif config == "coder_v2_n1":
        return await _run_coder_v2(op, router, user_id, workspace, n_candidates=1, gen_model=gen_model, think=think)
    elif config == "coder_v2_n1_cell3_best":
        return await _run_coder_v2(op, router, user_id, workspace, n_candidates=1, cell_strategy="best_of_3", gen_model=gen_model, think=think)
    elif config == "coder_v2_n1_cell3_combined":
        return await _run_coder_v2(op, router, user_id, workspace, n_candidates=1, cell_strategy="combined", gen_model=gen_model, think=think)
    elif config == "coder_v2_n3":
        return await _run_coder_v2(op, router, user_id, workspace, n_candidates=3, gen_model=gen_model, think=think)
    # New algorithms with introspection/documentation lookup
    elif config == "introspect_then_code":
        return await _run_introspect_then_code(op, router, workspace, gen_model=gen_model, think=think)
    elif config == "error_recovery_introspect":
        return await _run_error_recovery_introspect(op, router, workspace, gen_model=gen_model, think=think)
    elif config == "thinker_coder_split":
        return await _run_thinker_coder_split(op, router, workspace, gen_model=gen_model, think=think)
    elif config == "introspect_with_recovery":
        return await _run_introspect_with_recovery(op, router, workspace, gen_model=gen_model, think=think)
    else:
        raise ValueError(f"Unknown config: {config}")


# ─────────────────────────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────────────────────────

async def run_experiment(
    configs: List[str],
    datasets: List[str],
    complexities: List[str],
    max_ops: Optional[int] = None,
    resume: bool = False,
    gen_model: Optional[str] = None,
    think: Union[bool, str, None] = None,
):
    """Run the coder benchmark experiment."""
    # Not an entry point under the lock: it sets no run context, so _dispatch would refuse every attempt and the loop
    # below would store each refusal as a failed attempt. Figure 6 runs through exp_05_coder_benchmark.py.
    raise SystemExit("exp_v2_8 sets no run context; run Figure 6 through "
                     "publication/scripts/exp_05_coder_benchmark.py")
    # Resolve model: CLI override > default
    active_model = gen_model or GEN_MODEL

    ops = load_ground_truth_ops(datasets, complexities, max_ops)
    if not ops:
        logger.error("No operations match the given filters.")
        return

    logger.info(f"Model: {active_model} | Think: {think if think else 'off'}")
    logger.info(f"Operations: {len(ops)}")
    logger.info(f"Configs: {configs}")
    logger.info(f"Datasets: {datasets}")
    logger.info(f"Complexities: {complexities}")

    user_id = find_admin_user_id()
    router = ModelRouter()

    base_workspace = PROJECT_ROOT / "data" / "workspace" / "v2_8_benchmark"
    base_workspace.mkdir(parents=True, exist_ok=True)

    # Per-model intermediate file to allow parallel runs
    V2_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    model_slug = _model_slug(active_model)
    think_suffix = f"_think-{think}" if think else ""
    intermediate_file = V2_RESULTS_DIR / f"v2_8_intermediate_{model_slug}{think_suffix}.json"
    intermediate = load_intermediate(intermediate_file) if resume else {
        "results": [], "completed_keys": []
    }
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    total = len(configs) * len(ops)
    done = 0

    for config in configs:
        for op in ops:
            op_id = op["op_id"]
            key = f"{config}::{op_id}"

            if key in completed:
                done += 1
                continue

            done += 1
            logger.info(
                f"[{done}/{total}] {config} | {op_id} "
                f"({op['complexity']}) | {op['dataset']}"
            )

            # Create workspace with dataset files
            workspace = base_workspace / f"{config}_{op_id}_{uuid.uuid4().hex[:6]}"
            workspace.mkdir(parents=True, exist_ok=True)

            # Copy dataset files to workspace/files/ (where coder expects them)
            files_dir = workspace / "files"
            files_dir.mkdir(parents=True, exist_ok=True)
            for _key, filename in op["files"].items():
                src = DATASETS_DIR / filename
                if src.exists():
                    shutil.copy2(src, files_dir / filename)

            # Run
            try:
                result = await _dispatch(config, op, router, user_id, workspace, gen_model=active_model, think=think)
            except Exception as e:
                logger.error(f"Dispatch failed: {e}")
                result = {
                    "config": config,
                    "passed": False,
                    "field_results": {},
                    "actual_results": {},
                    "exec_error": str(e),
                    "latency_s": 0,
                    "n_cells": 0,
                    "n_llm_calls": None,   # not counted when the attempt stopped (A5); calls.jsonl has its calls
                    "n_retries": None,
                    "n_idle_recovered": 0,
                }

            entry = {
                "op_id": op_id,
                "dataset": op["dataset"],
                "complexity": op["complexity"],
                "category": op["category"],
                "config": config,
                "gen_model": active_model,
                "passed": result["passed"],
                "judge_score": result.get("judge_score"),
                "judge_comment": result.get("judge_comment"),
                "field_results": result.get("field_results", {}),
                "actual_results": result.get("actual_results", {}),
                "exec_error": result.get("exec_error", ""),
                "latency_s": result.get("latency_s", 0),
                "n_cells": result.get("n_cells", 0),
                "n_llm_calls": result.get("n_llm_calls"),
                "n_retries": result.get("n_retries"),
                "n_idle_recovered": result.get("n_idle_recovered", 0),
            }

            all_results.append(entry)
            completed.add(key)

            save_intermediate(
                {"results": all_results, "completed_keys": list(completed)},
                intermediate_file,
            )

            # Log result
            status = "PASS" if result["passed"] else "FAIL"
            logger.info(
                f"  -> {status} ({result.get('latency_s', 0):.0f}s)"
                + (f" | {result.get('exec_error', '')[:80]}" if not result["passed"] else "")
            )

        logger.info(f"Completed config: {config}")

    # ── Generate report ──
    _generate_report(all_results, configs, datasets, complexities, ops, gen_model=active_model, think=think)

    # Clean up intermediate
    if intermediate_file.exists():
        intermediate_file.unlink()


# ─────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────

def _generate_report(
    all_results: List[Dict],
    configs: List[str],
    datasets: List[str],
    complexities: List[str],
    ops: List[Dict],
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
):
    """Generate JSON + markdown reports."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Aggregate metrics ──

    def _pass_rate(results: List[Dict]) -> float:
        if not results:
            return 0.0
        return round(sum(1 for r in results if r["passed"]) / len(results) * 100, 1)

    def _median_lat(results: List[Dict]) -> float:
        lats = [r["latency_s"] for r in results if r.get("latency_s", 0) > 0]
        return round(statistics.median(lats), 1) if lats else 0.0

    # By config
    by_config = defaultdict(list)
    for r in all_results:
        by_config[r["config"]].append(r)

    # By config x complexity
    by_config_complexity = defaultdict(list)
    for r in all_results:
        by_config_complexity[(r["config"], r["complexity"])].append(r)

    # By config x dataset
    by_config_dataset = defaultdict(list)
    for r in all_results:
        by_config_dataset[(r["config"], r["dataset"])].append(r)

    # ── JSON output ──
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
        }

    output = {
        "experiment": "v2_8_coder_benchmark",
        "timestamp": timestamp,
        "gen_model": gen_model,
        "think": str(think) if think else "off",
        "configs": configs,
        "datasets": datasets,
        "complexities": complexities,
        "n_operations": len(ops),
        "total_evaluations": len(all_results),
        "summary": summary,
        "per_operation_results": all_results,
    }

    # Build filename prefix with model slug for easy identification
    model_slug = _model_slug(gen_model)
    think_suffix = f"_think-{think}" if think else ""
    file_prefix = f"v2_8_coder_benchmark_{model_slug}{think_suffix}"

    json_path, _ = save_v2_results(output, file_prefix)

    # ── Markdown ──
    md = [
        "# V2-8: Coder Benchmark",
        "",
        f"Generated: {datetime.now().isoformat()}",
        f"Model: `{gen_model}` | Think: `{think if think else 'off'}`",
        f"Operations: {len(ops)} | Evaluations: {len(all_results)}",
        "",
    ]

    # Table 1: By config
    md.append("## Overall Pass Rate by Config")
    md.append("")
    headers = ["Config", "Pass Rate", "Med. Latency", "N"]
    rows = []
    for config in configs:
        s = summary.get(config, {})
        rows.append([
            config,
            format_pct(s.get("pass_rate", 0)),
            format_latency(s.get("median_latency", 0)),
            str(s.get("n", 0)),
        ])
    md.append(format_v2_table(headers, rows, ["l", "r", "r", "r"]))
    md.append("")

    # Table 2: By config x complexity
    md.append("## Pass Rate by Complexity")
    md.append("")
    headers = ["Config"] + [f"{cx} (n)" for cx in ALL_COMPLEXITIES]
    rows = []
    for config in configs:
        row = [config]
        for cx in ALL_COMPLEXITIES:
            info = summary.get(config, {}).get("by_complexity", {}).get(cx, {})
            pr = info.get("pass_rate", 0)
            n = info.get("n", 0)
            row.append(f"{pr:.0f}% ({n})" if n > 0 else "-")
        rows.append(row)
    md.append(format_v2_table(headers, rows, ["l"] + ["r"] * len(ALL_COMPLEXITIES)))
    md.append("")

    # Table 3: By config x dataset
    md.append("## Pass Rate by Dataset")
    md.append("")
    headers = ["Config"] + [f"{ds} (n)" for ds in ALL_DATASETS]
    rows = []
    for config in configs:
        row = [config]
        for ds in ALL_DATASETS:
            info = summary.get(config, {}).get("by_dataset", {}).get(ds, {})
            pr = info.get("pass_rate", 0)
            n = info.get("n", 0)
            row.append(f"{pr:.0f}% ({n})" if n > 0 else "-")
        rows.append(row)
    md.append(format_v2_table(headers, rows, ["l"] + ["r"] * len(ALL_DATASETS)))
    md.append("")

    # Table 4: Per-operation detail
    md.append("## Per-Operation Results")
    md.append("")
    headers = ["Operation", "Complexity", "Config", "Pass", "Latency", "Judge Score", "Judge Comment", "Error"]
    rows = []
    for r in sorted(all_results, key=lambda x: (x["op_id"], x["config"])):
        status = "PASS" if r["passed"] else "FAIL"
        err = r.get("exec_error", "")[:40]
        # Clean judge comment for markdown table
        judge_comment = r.get("judge_comment", "").replace("\n", " ")[:60]
        if len(r.get("judge_comment", "")) > 60:
            judge_comment += "..."

        rows.append([
            r["op_id"],
            r["complexity"],
            r["config"],
            status,
            f"{r.get('latency_s', 0):.0f}s",
            r.get("judge_score", "-"),
            judge_comment,
            err,
        ])
    md.append(format_v2_table(headers, rows, ["l", "l", "l", "c", "r", "l", "l", "l"]))
    md.append("")

    # Field-level failures
    failures = [r for r in all_results if not r["passed"] and r.get("field_results")]
    if failures:
        md.append("## Field-Level Failures")
        md.append("")
        for r in failures:
            md.append(f"### {r['op_id']} ({r['config']})")
            for field, info in r["field_results"].items():
                if not info.get("passed"):
                    md.append(
                        f"- **{field}**: expected={info.get('expected')}, "
                        f"actual={info.get('actual')}, error={info.get('error')}"
                    )
            md.append("")

    md_content = "\n".join(md)
    md_path = save_v2_markdown(md_content, file_prefix)

    print(f"\n{'='*70}")
    print("V2-8 COMPLETE: Coder Benchmark")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(md_content[:3000])


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V2-8: Coder Benchmark with Objective Verification"
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=CONFIG_NAMES,
        help=f"Configs to test (default: {CONFIG_NAMES})",
    )
    parser.add_argument(
        "--datasets", nargs="+", default=ALL_DATASETS,
        choices=ALL_DATASETS,
        help=f"Datasets to test (default: {ALL_DATASETS})",
    )
    parser.add_argument(
        "--complexity", nargs="+", default=ALL_COMPLEXITIES,
        choices=ALL_COMPLEXITIES,
        help=f"Complexity tiers to include (default: {ALL_COMPLEXITIES})",
    )
    parser.add_argument(
        "--max-ops", type=int, default=None,
        help="Max operations to test (for smoke tests)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from intermediate checkpoint",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help=f"Model identifier (default: {GEN_MODEL}). "
             "Examples: ollama::qwen3-coder:latest, gemini::gemini-2.5-pro-preview-05-06",
    )
    parser.add_argument(
        "--think", type=str, nargs="?", const="True", default=None,
        help="Enable thinking/reasoning. Use --think for boolean True, "
             "or --think low/medium/high for gpt-oss style levels.",
    )

    args = parser.parse_args()

    # Parse think argument: "True"/"False" -> bool, "low"/"medium"/"high" -> str
    think_val = None
    if args.think is not None:
        if args.think.lower() in ("true", "1", "yes"):
            think_val = True
        elif args.think.lower() in ("false", "0", "no"):
            think_val = False
        else:
            think_val = args.think.lower()  # "low", "medium", "high"

    asyncio.run(run_experiment(
        configs=args.configs,
        datasets=args.datasets,
        complexities=args.complexity,
        max_ops=args.max_ops,
        resume=args.resume,
        gen_model=args.model,
        think=think_val,
    ))


if __name__ == "__main__":
    main()
