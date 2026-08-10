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

from tests.experiments.exp_common import (
    GEN_MODEL,
    find_admin_user_id,
    configure_gemini_from_admin,
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

    # Try to get docstring
    if hasattr(_obj, '__doc__') and _obj.__doc__:
        _info["docstring"] = _obj.__doc__[:500]

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
    expected_json = json.dumps(ground_truth)

    code = f"""
import json as _json
import pandas as _pd
import numpy as _np

_gt_keys = {keys_json}
_expected = {expected_json}
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

async def _execute_and_collect(kernel, code: str, timeout: int = 120) -> Dict[str, Any]:
    """Execute code in kernel and collect all outputs."""
    stdout_parts = []
    stderr_parts = []
    errors = []
    results = []

    async for output in kernel.execute(code, timeout=timeout):
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

    return {
        "stdout": "".join(stdout_parts),
        "stderr": "".join(stderr_parts),
        "errors": errors,
        "results": results,
        "success": len(errors) == 0,
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
                    if isinstance(expected_val, int):
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

    response = await router.generate(
        model_identifier=gen_model,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": 16000},
        think=think,
    )

    # Check for API errors (e.g. Gemini returns {"error": "..."})
    if "error" in response and "response" not in response:
        return {
            "config": "free_form",
            "passed": False,
            "field_results": {},
            "actual_results": {},
            "exec_error": f"LLM API error: {response['error']}",
            "latency_s": time.time() - t0,
        }

    code_text = response.get("response", response.get("message", {}).get("content", ""))
    if not code_text:
        code_text = str(response)

    # Extract code block
    code_match = re.search(r'```python\s*(.*?)```', code_text, re.DOTALL)
    code = code_match.group(1).strip() if code_match else code_text.strip()

    # Execute in kernel
    nb_path = str(workspace / "free_form.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}

    try:
        await kernel.start()

        # Execute the generated code
        exec_out = await _execute_and_collect(kernel, code, timeout=120)
        if not exec_out["success"]:
            exec_error = "; ".join(
                f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
            )
        else:
            # Run extraction code
            extraction = build_extraction_code(op["ground_truth"])
            extract_out = await _execute_and_collect(kernel, extraction, timeout=30)

            actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
            verification = verify_results(
                actual_results, op["ground_truth"], op["tolerance"]
            )
    except Exception as e:
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
        "code": code[:4000],
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
    n_candidates = 3
    config_name = f"free_form_n3_{strategy}"

    required_vars = _build_required_variables_section(op["ground_truth"])
    prompt = FREE_FORM_SYSTEM.replace("{prompt}", op["prompt"])
    prompt = prompt.replace("{file_descriptions}", _file_descriptions(op))
    prompt = prompt.replace("{required_variables}", required_vars)

    # Generate N candidate scripts
    candidates = []
    for i in range(n_candidates):
        response = await router.generate(
            model_identifier=gen_model,
            prompt=prompt,
            options={"temperature": 0.7, "num_predict": 16000},
            think=think,
        )
        # Check for API errors
        if "error" in response and "response" not in response:
            return {
                "config": config_name,
                "passed": False,
                "field_results": {},
                "actual_results": {},
                "exec_error": f"LLM API error: {response['error']}",
                "latency_s": time.time() - t0,
            }
        code_text = response.get("response", response.get("message", {}).get("content", ""))
        if not code_text:
            code_text = str(response)
        code_match = re.search(r'```python\s*(.*?)```', code_text, re.DOTALL)
        code = code_match.group(1).strip() if code_match else code_text.strip()
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
        judge_response = await router.generate(
            model_identifier=gen_model,
            prompt=judge_prompt,
            options={"temperature": 0.0, "num_predict": 100},
            think=think,
        )
        judge_text = judge_response.get("response", "").strip()
        # Parse judge's pick (1, 2, or 3)
        pick_match = re.search(r'[123]', judge_text)
        picked = int(pick_match.group()) if pick_match else 1
        picked = max(1, min(picked, n_candidates))
        code = candidates[picked - 1]
        logger.debug(f"  Judge picked candidate {picked}")
    else:  # combined
        judge_prompt = JUDGE_COMBINE.format(
            n=n_candidates,
            prompt=op["prompt"],
            file_descriptions=_file_descriptions(op),
            required_variables=required_vars,
            candidates_section=candidates_section,
        )
        judge_response = await router.generate(
            model_identifier=gen_model,
            prompt=judge_prompt,
            options={"temperature": 0.1, "num_predict": 16000},
            think=think,
        )
        code_text = judge_response.get("response", "")
        code_match = re.search(r'```python\s*(.*?)```', code_text, re.DOTALL)
        code = code_match.group(1).strip() if code_match else code_text.strip()
        logger.debug(f"  Judge wrote combined script ({len(code)} chars)")

    # Execute the winning/combined script
    nb_path = str(workspace / f"{config_name}.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}

    try:
        await kernel.start()
        exec_out = await _execute_and_collect(kernel, code, timeout=120)
        if not exec_out["success"]:
            exec_error = "; ".join(
                f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
            )
        else:
            extraction = build_extraction_code(op["ground_truth"])
            extract_out = await _execute_and_collect(kernel, extraction, timeout=30)
            actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
            verification = verify_results(
                actual_results, op["ground_truth"], op["tolerance"]
            )
    except Exception as e:
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
        "code": code[:4000],
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
    from backend.database import engine as db_engine
    from backend.models.user import User
    from sqlmodel import Session, select

    t0 = time.time()
    config_name = f"coder_v2_n{n_candidates}"
    if cell_strategy != "single":
        config_name += f"_cell3_{cell_strategy.replace('best_of_3', 'best').replace('combined', 'combined')}"

    # Monkeypatch N_CANDIDATES
    original_n = algo_module.N_CANDIDATES
    algo_module.N_CANDIDATES = n_candidates

    task_id = str(uuid.uuid4())

    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()

    ctx = SessionContext(
        user_id=user_id,
        user_email=user.email if user else "admin@mentori",
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
    n_retries = 0
    n_llm_calls = 0
    n_idle_recovered = 0

    try:
        async for event in coder_loop_v2(
            model_router=router,
            model_identifier=gen_model,
            messages=messages,
            session_context=ctx,
            max_steps=20,
            think=think if think is not None else False,
            history_log=history_log,
            cell_strategy=cell_strategy,
        ):
            event_type = event.get("type", "")
            events.append(event_type)

            if event_type == "complete":
                answer = event.get("content", "")
            elif event_type == "chunk":
                answer += event.get("content", "")
            elif event_type == "error":
                exec_error = event.get("content", str(event))
            elif event_type == "step_failed":
                # Collect step execution errors
                step_err = event.get("error", str(event))
                if exec_error:
                    exec_error += f" | Step failed: {step_err}"
                else:
                    exec_error = f"Step failed: {step_err}"
            elif event_type == "cell_retry":
                n_retries += 1
            elif event_type == "idle_cell_recovered":
                n_idle_recovered += 1
            # Count LLM calls from token usage events
            if event_type == "token_usage":
                n_llm_calls += 1

    except Exception as e:
        exec_error = str(e)
        logger.error(f"coder_v2 error: {e}")
    finally:
        # Shut down the session kernel spawned by coder_loop_v2 to avoid
        # "Parent appears to have exited" warnings from IPython.
        try:
            await KernelRegistry.stop_all()
        except Exception:
            pass

    # Restore N_CANDIDATES
    algo_module.N_CANDIDATES = original_n

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
                    # Re-execute each code cell to rebuild the namespace
                    for i, cell in enumerate(code_cells):
                        source = "".join(cell.get("source", []))
                        if source.strip():
                            await _execute_and_collect(fresh_kernel, source, timeout=60)

                    # Now run the extraction code in the populated namespace
                    extraction = build_extraction_code(op["ground_truth"])
                    extract_out = await _execute_and_collect(fresh_kernel, extraction, timeout=30)
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
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            exec_error = exec_error or f"Verification: {e}"

    latency = time.time() - t0

    # Judge Evaluation (if failed)
    judge_score = "PASS" if verification["passed"] else "FAIL"
    judge_comment = ""
    if not verification["passed"]:
        judge_score, judge_comment = await _evaluate_failed_result(
            op, actual_results, exec_error or str(verification["field_results"]), router
        )

    # Count code cells in the notebook
    n_cells = 0
    if nb_files:
        try:
            import nbformat
            nb = nbformat.read(str(nb_files[0]), as_version=4)
            n_cells = sum(1 for c in nb.cells if c.cell_type == "code")
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
        "n_candidates": n_candidates,
        "n_cells": n_cells,
        "n_llm_calls": n_llm_calls,
        "n_retries": n_retries,
        "n_idle_recovered": n_idle_recovered,
    }


async def _evaluate_failed_result(
    op: Dict, actual_results: Dict, error_msg: str, router: ModelRouter,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Tuple[str, str]:
    """Run LLM judge to evaluate if a failure is a 'soft pass'."""
    try:
        logger.info("Evaluating failed result with LLM judge...")
        prompt = JUDGE_EVALUATE_RESULT.format(
            prompt=op["prompt"],
            ground_truth=json.dumps(op["ground_truth"], indent=2, default=str),
            actual_results=json.dumps(actual_results, indent=2, default=str),
            error_message=error_msg[:2000]
        )
        response = await router.generate(
            model_identifier=gen_model,
            prompt=prompt,
            options={"temperature": 0.0, "num_predict": 200},
            think=think,
        )
        text = response.get("response", "").strip()
        logger.info(f"Judge response: {text}")

        score_match = re.search(r"SCORE:\s*(PASS_WITH_RESERVE|FAIL)", text)
        score = score_match.group(1) if score_match else "FAIL"

        comment_match = re.search(r"COMMENT:\s*(.*)", text, re.DOTALL)
        comment = comment_match.group(1).strip() if comment_match else text

        return score, comment
    except Exception as e:
        logger.warning(f"Judge evaluation failed: {e}")
        return "FAIL", f"Judge error: {e}"


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
    """Build human-readable API reference from introspection results."""
    lines = []
    for item in api_info:
        if "error" in item:
            lines.append(f"- {item['module']}.{item['object']}: [error: {item['error']}]")
            continue
        obj_name = f"{item['module']}.{item['object']}"
        if item.get("methods"):
            lines.append(f"- {obj_name} methods: {', '.join(item['methods'][:20])}")
        if item.get("attributes"):
            lines.append(f"- {obj_name} attributes: {', '.join(item['attributes'][:20])}")
        if item.get("docstring"):
            lines.append(f"  Docstring: {item['docstring'][:200]}...")
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

    # Step 1: Ask LLM to identify what to introspect
    analysis_prompt = INTROSPECT_ANALYSIS_PROMPT.format(prompt=op["prompt"])
    analysis_response = await router.generate(
        model_identifier=gen_model,
        prompt=analysis_prompt,
        options={"temperature": 0.1, "num_predict": 16000},
        think=think,
    )
    n_llm_calls += 1

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
                intro_out = await _execute_and_collect(kernel, introspect_code, timeout=30)
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
            options={"temperature": 0.1, "num_predict": 16000},
            think=think,
        )
        n_llm_calls += 1

        code_text = response.get("response", "")
        code_match = re.search(r'```python\s*(.*?)```', code_text, re.DOTALL)
        code = code_match.group(1).strip() if code_match else code_text.strip()

        # Step 4: Execute and verify
        exec_out = await _execute_and_collect(kernel, code, timeout=120)

        actual_results = {}
        exec_error = ""
        verification = {"passed": False, "field_results": {}}

        if not exec_out["success"]:
            exec_error = "; ".join(
                f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
            )
        else:
            extraction = build_extraction_code(op["ground_truth"])
            extract_out = await _execute_and_collect(kernel, extraction, timeout=30)
            actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
            verification = verify_results(
                actual_results, op["ground_truth"], op["tolerance"]
            )

    except Exception as e:
        exec_error = str(e)
        actual_results = {}
        verification = {"passed": False, "field_results": {}}
        code = ""
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
        "code": code[:4000] if code else "",
        "api_info": api_info[:5],  # Truncate for storage
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
    max_retries: int = 2,
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

    # Step 1: Initial generation
    response = await router.generate(
        model_identifier=gen_model,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": 16000},
        think=think,
    )
    n_llm_calls += 1

    code_text = response.get("response", "")
    code_match = re.search(r'```python\s*(.*?)```', code_text, re.DOTALL)
    code = code_match.group(1).strip() if code_match else code_text.strip()

    nb_path = str(workspace / "error_recovery_introspect.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}
    introspect_output = ""

    try:
        await kernel.start()

        for attempt in range(max_retries + 1):
            # Execute the code
            exec_out = await _execute_and_collect(kernel, code, timeout=120)

            if exec_out["success"]:
                # Success - extract results
                extraction = build_extraction_code(op["ground_truth"])
                extract_out = await _execute_and_collect(kernel, extraction, timeout=30)
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
            intro_out = await _execute_and_collect(kernel, introspect_code, timeout=30)
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
                options={"temperature": 0.1, "num_predict": 16000},
                think=think,
            )
            n_llm_calls += 1

            retry_text = retry_response.get("response", "")
            code_match = re.search(r'```python\s*(.*?)```', retry_text, re.DOTALL)
            code = code_match.group(1).strip() if code_match else retry_text.strip()

            # Reset kernel for clean retry
            await kernel.stop()
            await kernel.start()

    except Exception as e:
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
        "code": code[:4000],
        "introspect_output": introspect_output[:1000] if introspect_output else "",
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

    # Step 1: Thinker generates introspection code
    thinker_prompt = THINKER_RESEARCH_PROMPT.format(prompt=op["prompt"])
    thinker_response = await router.generate(
        model_identifier=gen_model,
        prompt=thinker_prompt,
        options={"temperature": 0.2, "num_predict": 16000},
        think=think,
    )
    n_llm_calls += 1

    thinker_text = thinker_response.get("response", "")
    code_match = re.search(r'```python\s*(.*?)```', thinker_text, re.DOTALL)
    introspect_code = code_match.group(1).strip() if code_match else ""

    nb_path = str(workspace / "thinker_coder_split.ipynb")
    kernel = NotebookKernel(nb_path, str(workspace))

    actual_results = {}
    exec_error = ""
    verification = {"passed": False, "field_results": {}}
    api_reference = ""
    code = ""

    try:
        await kernel.start()

        # Step 2: Execute introspection code
        introspect_output = ""
        if introspect_code:
            intro_out = await _execute_and_collect(kernel, introspect_code, timeout=30)
            introspect_output = intro_out["stdout"][:3000]  # Limit size

        # Step 3: Thinker summarizes API reference
        if introspect_output:
            summary_prompt = THINKER_API_SUMMARY_PROMPT.format(
                introspect_output=introspect_output
            )
            summary_response = await router.generate(
                model_identifier=gen_model,
                prompt=summary_prompt,
                options={"temperature": 0.1, "num_predict": 16000},
                think=think,
            )
            n_llm_calls += 1
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
            options={"temperature": 0.1, "num_predict": 16000},
            think=think,
        )
        n_llm_calls += 1

        code_text = coder_response.get("response", "")
        code_match = re.search(r'```python\s*(.*?)```', code_text, re.DOTALL)
        code = code_match.group(1).strip() if code_match else code_text.strip()

        # Step 5: Execute and verify
        # Reset kernel for clean execution
        await kernel.stop()
        await kernel.start()

        exec_out = await _execute_and_collect(kernel, code, timeout=120)

        if not exec_out["success"]:
            exec_error = "; ".join(
                f"{e['ename']}: {e['evalue']}" for e in exec_out["errors"]
            )
        else:
            extraction = build_extraction_code(op["ground_truth"])
            extract_out = await _execute_and_collect(kernel, extraction, timeout=30)
            actual_results = _parse_benchmark_output(extract_out["stdout"]) or {}
            verification = verify_results(
                actual_results, op["ground_truth"], op["tolerance"]
            )

    except Exception as e:
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
        "code": code[:4000] if code else "",
        "api_reference": api_reference[:1000],
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
    max_retries: int = 2,
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

    # Step 1: Ask LLM to identify what to introspect
    analysis_prompt = INTROSPECT_ANALYSIS_PROMPT.format(prompt=op["prompt"])
    analysis_response = await router.generate(
        model_identifier=gen_model,
        prompt=analysis_prompt,
        options={"temperature": 0.1, "num_predict": 16000},
        think=think,
    )
    n_llm_calls += 1

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
                intro_out = await _execute_and_collect(kernel, introspect_code, timeout=30)
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
            options={"temperature": 0.1, "num_predict": 16000},
            think=think,
        )
        n_llm_calls += 1

        code_text = response.get("response", "")
        code_match = re.search(r'```python\s*(.*?)```', code_text, re.DOTALL)
        code = code_match.group(1).strip() if code_match else code_text.strip()

        # Step 4: Execute with retry loop
        for attempt in range(max_retries + 1):
            # Reset kernel for clean execution
            await kernel.stop()
            await kernel.start()

            exec_out = await _execute_and_collect(kernel, code, timeout=120)

            if exec_out["success"]:
                # Success - extract results
                extraction = build_extraction_code(op["ground_truth"])
                extract_out = await _execute_and_collect(kernel, extraction, timeout=30)
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
            intro_out = await _execute_and_collect(kernel, introspect_code, timeout=30)
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
                options={"temperature": 0.1, "num_predict": 16000},
                think=think,
            )
            n_llm_calls += 1

            retry_text = retry_response.get("response", "")
            code_match = re.search(r'```python\s*(.*?)```', retry_text, re.DOTALL)
            code = code_match.group(1).strip() if code_match else retry_text.strip()

    except Exception as e:
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
        "code": code[:4000] if code else "",
        "api_reference": api_reference[:1000] if api_reference else "",
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

async def _dispatch(
    config: str,
    op: Dict,
    router: ModelRouter,
    user_id: str,
    workspace: Path,
    gen_model: str = GEN_MODEL,
    think: Union[bool, str, None] = None,
) -> Dict[str, Any]:
    """Dispatch to the right config runner."""
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
    # Resolve model: CLI override > default
    active_model = gen_model or GEN_MODEL

    # Configure Gemini API key if needed
    if active_model.startswith("gemini::"):
        if not configure_gemini_from_admin():
            logger.error("Gemini model requested but no API key found in admin settings")
            return

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
                    "n_llm_calls": 0,
                    "n_retries": 0,
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
                "n_llm_calls": result.get("n_llm_calls", 0),
                "n_retries": result.get("n_retries", 0),
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
