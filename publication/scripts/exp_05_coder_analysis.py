#!/usr/bin/env python3
"""V4-8 Deep Analysis: Thinking mode impact, V2/V4 cross-validation, error taxonomy.

Merges workstreams WS1 (deep analysis), WS6 (cross-validation), WS7 (post-processing), WS8 (validation).

Usage:
    uv run python publication/scripts/exp_05_coder_analysis.py              # full analysis
    uv run python publication/scripts/exp_05_coder_analysis.py --validate   # data validation only
    uv run python publication/scripts/exp_05_coder_analysis.py --partial    # include intermediate results
"""

import argparse
import json
import logging
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent / "results_v4"
V2_RESULTS_DIR = Path(__file__).parent.parent / "experiments_v2" / "results_v2"

ALL_CONFIGS = [
    "free_form", "free_form_n3_best", "free_form_n3_combined",
    "coder_v2_n1", "coder_v2_n1_cell3_best", "coder_v2_n1_cell3_combined",
    "coder_v2_n3",
    "introspect_then_code", "error_recovery_introspect", "thinker_coder_split",
    "introspect_with_recovery",
]
ALL_OPS = 20
TOTAL_PER_MODEL = ALL_OPS * len(ALL_CONFIGS)  # 220

RNG = np.random.default_rng(42)
N_BOOTSTRAP = 10_000


# ─── Data Loading ───────────────────────────────────────────────────────────

def _parse_model_key_from_filename(filename: str, prefix: str) -> Tuple[str, str]:
    """Extract model_key and think from filename.

    Returns (model_key, think) where think is '' for off/None.
    """
    # Strip prefix and suffix
    name = filename
    for sfx in ("_latest.json", ".json"):
        if name.endswith(sfx):
            name = name[: -len(sfx)]
    if name.startswith(prefix):
        name = name[len(prefix):]

    # Extract think suffix
    m = re.search(r"_think-(\w+)$", name)
    if m:
        think = m.group(1)
        model_key = name[: m.start()]
    else:
        think = ""
        model_key = name

    # Normalize think
    if think.lower() in ("off", "none", "not_set", "false"):
        think = ""

    return model_key, think


def _model_label(model_key: str, think: str) -> str:
    """Human-readable model label."""
    if think:
        return f"{model_key}[think:{think}]"
    return model_key


def load_v4_8_results(include_partial: bool = False) -> Dict[str, List[Dict]]:
    """Load V4-8 results grouped by model label.

    Loads completed (_latest.json) first, then intermediate if include_partial.
    Deduplicates by (model, think, config, op_id).
    """
    seen = {}  # (model_key, think, config, op_id) -> source
    by_model = defaultdict(list)

    # 1. Load completed results (authoritative)
    for f in sorted(RESULTS_DIR.glob("v4_8_coder_benchmark_*_latest.json")):
        data = json.load(open(f))
        ops = data.get("per_operation_results", [])
        model_key, think = _parse_model_key_from_filename(f.name, "v4_8_coder_benchmark_")
        # Override with metadata if present
        if data.get("think") and data["think"] not in ("off", "None"):
            think = str(data["think"])
        label = _model_label(model_key, think)
        for r in ops:
            key = (model_key, think, r["config"], r["op_id"])
            if key not in seen:
                seen[key] = ("done", f.name)
                r["_think"] = think
                r["_model_label"] = label
                by_model[label].append(r)

    if not include_partial:
        logger.info(f"Loaded {sum(len(v) for v in by_model.values())} results from "
                     f"{len(by_model)} completed models")
        return dict(by_model)

    # 2. Load intermediate results
    for f in sorted(RESULTS_DIR.glob("v4_8_intermediate_*.json")):
        data = json.load(open(f))
        ops = data.get("results", data.get("per_operation_results", []))
        model_key, think = _parse_model_key_from_filename(f.name, "v4_8_intermediate_")
        label = _model_label(model_key, think)
        added = 0
        for r in ops:
            key = (model_key, think, r["config"], r["op_id"])
            if key not in seen:
                seen[key] = ("partial", f.name)
                r["_think"] = think
                r["_model_label"] = label
                by_model[label].append(r)
                added += 1
        if added:
            logger.info(f"  +{added} partial results from {f.name}")

    logger.info(f"Loaded {sum(len(v) for v in by_model.values())} total results from "
                 f"{len(by_model)} models (completed + partial)")
    return dict(by_model)


def load_v2_8_results() -> Dict[str, List[Dict]]:
    """Load V2-8 results grouped by model label."""
    by_model = defaultdict(list)
    for f in sorted(V2_RESULTS_DIR.glob("v2_8_coder_benchmark_*_latest.json")):
        data = json.load(open(f))
        ops = data.get("per_operation_results", [])
        model_key, think = _parse_model_key_from_filename(f.name, "v2_8_coder_benchmark_")
        if data.get("think") and data["think"] not in ("off", "None"):
            think = str(data["think"])
        label = _model_label(model_key, think)
        for r in ops:
            r["_think"] = think
            r["_model_label"] = label
            by_model[label].append(r)
    logger.info(f"Loaded V2-8: {sum(len(v) for v in by_model.values())} results from "
                 f"{len(by_model)} models")
    return dict(by_model)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _pass_rate(results: List[Dict]) -> float:
    if not results:
        return 0.0
    return round(sum(1 for r in results if r.get("passed")) / len(results) * 100, 1)


def _median_latency(results: List[Dict]) -> float:
    lats = [r["latency_s"] for r in results if r.get("latency_s", 0) > 0]
    return round(statistics.median(lats), 1) if lats else 0.0


def mcnemar_test(pass_a: np.ndarray, pass_b: np.ndarray) -> Dict:
    """McNemar's test for paired binary outcomes."""
    pass_a, pass_b = np.asarray(pass_a, dtype=bool), np.asarray(pass_b, dtype=bool)
    b = int(np.sum(pass_a & ~pass_b))  # a passed, b failed
    c = int(np.sum(~pass_a & pass_b))  # a failed, b passed
    n_disc = b + c
    if n_disc == 0:
        return {"b": b, "c": c, "n_discordant": 0, "statistic": 0, "p_value": 1.0, "method": "no_discordant"}
    if n_disc < 25:
        p_value = float(stats.binomtest(b, n_disc, 0.5).pvalue)
        method = "exact_binomial"
        statistic = b
    else:
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)
        p_value = float(1 - stats.chi2.cdf(chi2, 1))
        method = "chi2_continuity"
        statistic = float(chi2)
    return {"b": b, "c": c, "n_discordant": n_disc, "statistic": statistic,
            "p_value": round(p_value, 6), "method": method}


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, n_boot: int = N_BOOTSTRAP) -> Dict:
    """Bootstrap CI for difference in means, paired by index."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    observed = float(np.mean(a) - np.mean(b))
    n = len(a)
    boot_diffs = np.empty(n_boot)
    for i in range(n_boot):
        idx = RNG.integers(0, n, size=n)
        boot_diffs[i] = np.mean(a[idx]) - np.mean(b[idx])
    lo = float(np.percentile(boot_diffs, 2.5))
    hi = float(np.percentile(boot_diffs, 97.5))
    p_value = float(np.mean(boot_diffs <= 0)) if observed > 0 else float(np.mean(boot_diffs >= 0))
    return {"observed_diff": round(observed, 4), "ci_lower": round(lo, 4),
            "ci_upper": round(hi, 4), "ci_level": 0.95, "bootstrap_p": round(p_value, 4), "n": n}


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for two proportions."""
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


# ─── WS8: Validation ───────────────────────────────────────────────────────

def validate_results(v4_data: Dict[str, List[Dict]], v2_data: Dict[str, List[Dict]]) -> Dict:
    """Validate V4-8 (and optionally V2-8) data integrity."""
    issues = []

    for label, ops in v4_data.items():
        n = len(ops)

        # Check expected count (220 for complete models)
        if n < TOTAL_PER_MODEL:
            issues.append({"model": label, "type": "incomplete",
                           "detail": f"{n}/{TOTAL_PER_MODEL} results"})

        # Check for duplicates
        keys = [(r["config"], r["op_id"]) for r in ops]
        dupes = [k for k, cnt in Counter(keys).items() if cnt > 1]
        if dupes:
            issues.append({"model": label, "type": "duplicates",
                           "detail": f"{len(dupes)} duplicate (config, op_id) pairs"})

        # Check all configs present
        configs_found = set(r["config"] for r in ops)
        missing_configs = set(ALL_CONFIGS) - configs_found
        if missing_configs:
            issues.append({"model": label, "type": "missing_configs",
                           "detail": f"Missing: {sorted(missing_configs)}"})

        # Check all ops present
        op_ids = set(r["op_id"] for r in ops)
        if len(op_ids) < ALL_OPS:
            issues.append({"model": label, "type": "missing_ops",
                           "detail": f"Only {len(op_ids)}/{ALL_OPS} unique op_ids"})

        # Sanity: passed=True with exec_error
        bad_pass = [r for r in ops if r.get("passed") and r.get("exec_error")]
        if bad_pass:
            issues.append({"model": label, "type": "passed_with_error",
                           "detail": f"{len(bad_pass)} results have passed=True with exec_error"})

        # Latency sanity (0 or >600s is suspicious)
        bad_lat = [r for r in ops if r.get("latency_s", 0) <= 0 or r.get("latency_s", 0) > 600]
        if bad_lat:
            issues.append({"model": label, "type": "latency_anomaly",
                           "detail": f"{len(bad_lat)} results with latency <=0 or >600s"})

    result = {
        "analysis": "v4_8_data_validation",
        "timestamp": datetime.now().isoformat(),
        "n_models": len(v4_data),
        "total_results": sum(len(v) for v in v4_data.values()),
        "n_issues": len(issues),
        "issues": issues,
        "v2_8_models": len(v2_data),
        "v2_8_total": sum(len(v) for v in v2_data.values()),
    }

    # Print summary
    logger.info(f"Validation: {result['n_models']} models, {result['total_results']} results, "
                f"{result['n_issues']} issues")
    for iss in issues:
        logger.warning(f"  [{iss['type']}] {iss['model']}: {iss['detail']}")

    return result


# ─── WS7: V2/V4 Cross-validation ───────────────────────────────────────────

def compute_v2_v4_comparison(v4_data: Dict[str, List[Dict]],
                              v2_data: Dict[str, List[Dict]]) -> Dict:
    """Compare V2-8 vs V4-8 pass rates with paired McNemar tests."""
    comparison = {
        "experiment": "v4_8_vs_v2_8_comparison",
        "timestamp": datetime.now().isoformat(),
        "hypothesis": "think:high recovers from 6.2% with proper num_ctx",
        "models": {},
    }

    # Build lookup: normalize model labels for matching across V2/V4
    all_labels = sorted(set(list(v4_data.keys()) + list(v2_data.keys())))

    for label in all_labels:
        v2_ops = v2_data.get(label, [])
        v4_ops = v4_data.get(label, [])

        v2_pr = _pass_rate(v2_ops) if v2_ops else None
        v4_pr = _pass_rate(v4_ops) if v4_ops else None

        entry: Dict[str, Any] = {
            "v2_8_pass_rate": v2_pr,
            "v4_8_pass_rate": v4_pr,
            "delta_pp": round(v4_pr - v2_pr, 1) if v2_pr is not None and v4_pr is not None else None,
            "v2_8_num_ctx": "API" if "gemini" in label.lower() else 2048,
            "v4_8_num_ctx": "API" if "gemini" in label.lower() else 24576,
            "is_gemini": "gemini" in label.lower(),
            "v2_8_n": len(v2_ops),
            "v4_8_n": len(v4_ops),
        }

        # Paired McNemar if both have data
        if v2_ops and v4_ops:
            # Build paired arrays on matched (config, op_id)
            v2_map = {(r["config"], r["op_id"]): r.get("passed", False) for r in v2_ops}
            v4_map = {(r["config"], r["op_id"]): r.get("passed", False) for r in v4_ops}
            common = sorted(set(v2_map.keys()) & set(v4_map.keys()))
            if len(common) >= 5:
                v2_arr = np.array([v2_map[k] for k in common], dtype=bool)
                v4_arr = np.array([v4_map[k] for k in common], dtype=bool)
                entry["paired_n"] = len(common)
                entry["mcnemar"] = mcnemar_test(v4_arr, v2_arr)
                entry["bootstrap_ci"] = bootstrap_diff_ci(
                    v4_arr.astype(float), v2_arr.astype(float)
                )
                h = cohens_h(v4_arr.mean(), v2_arr.mean())
                entry["cohens_h"] = round(h, 4)

        comparison["models"][label] = entry

    # Print summary table
    logger.info("\n=== V2-8 vs V4-8 Comparison ===")
    logger.info(f"{'Model':<45} {'V2-8':>7} {'V4-8':>7} {'Delta':>8} {'p-value':>10}")
    logger.info("-" * 80)
    for label in sorted(comparison["models"].keys()):
        m = comparison["models"][label]
        v2_s = f"{m['v2_8_pass_rate']:.1f}%" if m["v2_8_pass_rate"] is not None else "N/A"
        v4_s = f"{m['v4_8_pass_rate']:.1f}%" if m["v4_8_pass_rate"] is not None else "N/A"
        delta_s = f"{m['delta_pp']:+.1f}pp" if m["delta_pp"] is not None else "N/A"
        p_s = f"{m['mcnemar']['p_value']:.4f}" if "mcnemar" in m else "—"
        logger.info(f"{label:<45} {v2_s:>7} {v4_s:>7} {delta_s:>8} {p_s:>10}")

    return comparison


# ─── WS1: Deep Analysis ────────────────────────────────────────────────────

def analyze_thinking_mode_impact(v4_data: Dict[str, List[Dict]]) -> Dict:
    """Analyze thinking mode impact for models with multiple think variants.

    Groups: gpt-oss (off/low/med/high), glm (off/on), nemotron (off/on), gemma (off/on).
    """
    # Identify think variant groups by base model
    groups = defaultdict(dict)  # base_model -> {think_level: [results]}
    for label, ops in v4_data.items():
        # Parse base model and think from label
        m = re.match(r"^(.+?)\[think:(.+?)\]$", label)
        if m:
            base, think = m.group(1), m.group(2)
        else:
            base, think = label, "off"
        groups[base][think] = ops

    # Only analyze models with 2+ variants
    groups = {b: vs for b, vs in groups.items() if len(vs) >= 2}

    results = {}
    for base, variants in sorted(groups.items()):
        model_result = {
            "variants": {},
            "comparisons": [],
        }
        off_ops = variants.get("off")

        for think, ops in sorted(variants.items()):
            pr = _pass_rate(ops)
            model_result["variants"][think] = {
                "pass_rate": pr,
                "n": len(ops),
                "median_latency": _median_latency(ops),
            }

            # Per-config breakdown
            by_cfg = defaultdict(list)
            for r in ops:
                by_cfg[r["config"]].append(r)
            model_result["variants"][think]["by_config"] = {
                cfg: _pass_rate(recs) for cfg, recs in sorted(by_cfg.items())
            }

        # Pairwise: each think variant vs off (if off exists)
        if off_ops:
            off_map = {(r["config"], r["op_id"]): r.get("passed", False) for r in off_ops}
            for think, ops in sorted(variants.items()):
                if think == "off":
                    continue
                think_map = {(r["config"], r["op_id"]): r.get("passed", False) for r in ops}
                common = sorted(set(off_map.keys()) & set(think_map.keys()))
                if len(common) < 5:
                    continue
                off_arr = np.array([off_map[k] for k in common], dtype=bool)
                think_arr = np.array([think_map[k] for k in common], dtype=bool)
                mcn = mcnemar_test(think_arr, off_arr)
                model_result["comparisons"].append({
                    "baseline": "off",
                    "variant": think,
                    "delta_pp": round((_pass_rate(ops) - _pass_rate(off_ops)), 1),
                    "paired_n": len(common),
                    "mcnemar": mcn,
                    "cohens_h": round(cohens_h(think_arr.mean(), off_arr.mean()), 4),
                })

        results[base] = model_result

    logger.info(f"\n=== Thinking Mode Impact ({len(results)} model groups) ===")
    for base, mr in results.items():
        variants_str = ", ".join(
            f"{t}={v['pass_rate']:.1f}%" for t, v in sorted(mr["variants"].items())
        )
        logger.info(f"  {base}: {variants_str}")
        for c in mr["comparisons"]:
            sig = "*" if c["mcnemar"]["p_value"] < 0.05 else ""
            logger.info(f"    {c['variant']} vs off: {c['delta_pp']:+.1f}pp "
                         f"(p={c['mcnemar']['p_value']:.4f}{sig}, h={c['cohens_h']:.3f})")

    return {
        "analysis": "thinking_mode_impact",
        "timestamp": datetime.now().isoformat(),
        "n_model_groups": len(results),
        "models": results,
    }


def analyze_config_model_interaction(v4_data: Dict[str, List[Dict]]) -> Dict:
    """Which configs are universally good vs model-dependent?"""
    # Build config x model pass rate matrix
    matrix = {}  # config -> {model: pass_rate}
    for label, ops in v4_data.items():
        by_cfg = defaultdict(list)
        for r in ops:
            by_cfg[r["config"]].append(r)
        for cfg, recs in by_cfg.items():
            if cfg not in matrix:
                matrix[cfg] = {}
            matrix[cfg][label] = _pass_rate(recs)

    config_stats = {}
    for cfg in ALL_CONFIGS:
        rates = list(matrix.get(cfg, {}).values())
        if not rates:
            continue
        config_stats[cfg] = {
            "mean_pass_rate": round(np.mean(rates), 1),
            "std_pass_rate": round(np.std(rates), 1),
            "min": round(min(rates), 1),
            "max": round(max(rates), 1),
            "cv": round(np.std(rates) / np.mean(rates), 3) if np.mean(rates) > 0 else None,
            "n_models": len(rates),
            "per_model": matrix[cfg],
        }

    # Rank by mean pass rate
    ranked = sorted(config_stats.items(), key=lambda x: x[1]["mean_pass_rate"], reverse=True)

    # Chi-square test for config x model interaction
    # Build contingency: configs (rows) x models (cols) -> pass count
    models = sorted(v4_data.keys())
    configs_with_data = [c for c in ALL_CONFIGS if c in matrix]
    contingency = []
    for cfg in configs_with_data:
        row = []
        for model in models:
            ops_for = [r for r in v4_data[model] if r["config"] == cfg]
            row.append(sum(1 for r in ops_for if r.get("passed")))
        contingency.append(row)

    chi2_result = None
    if len(contingency) >= 2 and len(contingency[0]) >= 2:
        chi2, p, dof, _ = stats.chi2_contingency(contingency)
        chi2_result = {"chi2": round(chi2, 2), "p_value": round(p, 6), "dof": dof}

    logger.info(f"\n=== Config x Model Interaction ===")
    logger.info(f"{'Config':<35} {'Mean':>7} {'Std':>6} {'Min':>6} {'Max':>6}")
    logger.info("-" * 65)
    for cfg, s in ranked:
        logger.info(f"{cfg:<35} {s['mean_pass_rate']:>6.1f}% {s['std_pass_rate']:>5.1f} "
                     f"{s['min']:>5.1f}% {s['max']:>5.1f}%")
    if chi2_result:
        logger.info(f"Chi-square interaction: chi2={chi2_result['chi2']}, "
                     f"p={chi2_result['p_value']}, dof={chi2_result['dof']}")

    return {
        "analysis": "config_model_interaction",
        "timestamp": datetime.now().isoformat(),
        "ranked_configs": [{"config": c, **s} for c, s in ranked],
        "chi2_interaction": chi2_result,
    }


def analyze_complexity_scaling(v4_data: Dict[str, List[Dict]]) -> Dict:
    """Simple/medium/complex pass rates per model."""
    results = {}
    for label, ops in sorted(v4_data.items()):
        by_cx = defaultdict(list)
        for r in ops:
            cx = r.get("complexity", "unknown")
            by_cx[cx].append(r)

        results[label] = {
            cx: {"pass_rate": _pass_rate(recs), "n": len(recs)}
            for cx, recs in sorted(by_cx.items())
        }

        # Degradation: complex vs simple
        simple_pr = results[label].get("simple", {}).get("pass_rate", 0)
        complex_pr = results[label].get("complex", {}).get("pass_rate", 0)
        results[label]["degradation_pp"] = round(complex_pr - simple_pr, 1)

    logger.info(f"\n=== Complexity Scaling ===")
    logger.info(f"{'Model':<45} {'Simple':>8} {'Medium':>8} {'Complex':>8} {'Degrad':>8}")
    logger.info("-" * 82)
    for label in sorted(results.keys()):
        r = results[label]
        s = r.get("simple", {}).get("pass_rate", 0)
        m = r.get("medium", {}).get("pass_rate", 0)
        c = r.get("complex", {}).get("pass_rate", 0)
        logger.info(f"{label:<45} {s:>7.1f}% {m:>7.1f}% {c:>7.1f}% {r['degradation_pp']:>+7.1f}")

    return {
        "analysis": "complexity_scaling",
        "timestamp": datetime.now().isoformat(),
        "per_model": results,
    }


def analyze_error_taxonomy(v4_data: Dict[str, List[Dict]]) -> Dict:
    """Classify exec_error strings into categories."""
    def classify_error(err: str) -> str:
        if not err:
            return "none"
        err_lower = err.lower()
        if "timeout" in err_lower or "timed out" in err_lower:
            return "timeout"
        if "syntaxerror" in err_lower or "syntax error" in err_lower:
            return "syntax"
        if "kernel" in err_lower and ("crash" in err_lower or "restart" in err_lower or "dead" in err_lower):
            return "kernel_crash"
        if "empty" in err_lower or "no code" in err_lower or "no output" in err_lower:
            return "empty_output"
        if "nameerror" in err_lower or "importerror" in err_lower or "modulenotfound" in err_lower:
            return "import_error"
        if "typeerror" in err_lower or "valueerror" in err_lower or "keyerror" in err_lower:
            return "runtime_type"
        if "filenotfounderror" in err_lower:
            return "file_not_found"
        if "error" in err_lower or "exception" in err_lower or "traceback" in err_lower:
            return "runtime_other"
        return "other"

    results = {}
    for label, ops in sorted(v4_data.items()):
        failed = [r for r in ops if not r.get("passed")]
        errors = Counter()
        for r in failed:
            cat = classify_error(r.get("exec_error", ""))
            errors[cat] += 1

        results[label] = {
            "total": len(ops),
            "failed": len(failed),
            "fail_rate": round(len(failed) / len(ops) * 100, 1) if ops else 0,
            "error_distribution": dict(errors.most_common()),
        }

    logger.info(f"\n=== Error Taxonomy ===")
    for label in sorted(results.keys()):
        r = results[label]
        if r["failed"] == 0:
            continue
        dist = ", ".join(f"{k}:{v}" for k, v in r["error_distribution"].items())
        logger.info(f"  {label}: {r['failed']}/{r['total']} failed — {dist}")

    return {
        "analysis": "error_taxonomy",
        "timestamp": datetime.now().isoformat(),
        "per_model": results,
    }


def analyze_latency_efficiency(v4_data: Dict[str, List[Dict]]) -> Dict:
    """Median latency per model, pass-per-second, Pareto frontier."""
    results = {}
    for label, ops in sorted(v4_data.items()):
        lats = [r["latency_s"] for r in ops if r.get("latency_s", 0) > 0]
        pr = _pass_rate(ops)
        med_lat = statistics.median(lats) if lats else 0
        # Pass-per-second: how many passes per second of total compute
        total_time = sum(lats)
        n_pass = sum(1 for r in ops if r.get("passed"))
        pps = n_pass / total_time if total_time > 0 else 0

        results[label] = {
            "pass_rate": pr,
            "median_latency_s": round(med_lat, 1),
            "total_compute_s": round(total_time, 1),
            "n_passed": n_pass,
            "passes_per_second": round(pps, 4),
            "n": len(ops),
        }

    # Compute Pareto frontier (maximize pass_rate, minimize latency)
    points = [(label, r["pass_rate"], r["median_latency_s"]) for label, r in results.items()]
    points.sort(key=lambda x: (-x[1], x[2]))  # sort by pass_rate desc, latency asc
    pareto = []
    best_lat = float("inf")
    for label, pr, lat in points:
        if lat < best_lat:
            pareto.append(label)
            best_lat = lat

    for label in results:
        results[label]["is_pareto"] = label in pareto

    logger.info(f"\n=== Latency Efficiency ===")
    logger.info(f"{'Model':<45} {'Pass%':>7} {'Med Lat':>8} {'Pass/s':>8} {'Pareto':>7}")
    logger.info("-" * 78)
    for label in sorted(results.keys(), key=lambda l: results[l]["pass_rate"], reverse=True):
        r = results[label]
        p = "***" if r["is_pareto"] else ""
        logger.info(f"{label:<45} {r['pass_rate']:>6.1f}% {r['median_latency_s']:>7.1f}s "
                     f"{r['passes_per_second']:>7.4f} {p:>7}")

    return {
        "analysis": "latency_efficiency",
        "timestamp": datetime.now().isoformat(),
        "per_model": results,
        "pareto_frontier": pareto,
    }


# ─── Main Report ────────────────────────────────────────────────────────────

def generate_full_report(v4_data: Dict[str, List[Dict]],
                          v2_data: Dict[str, List[Dict]]) -> Dict:
    """Run all analyses and save results."""
    report = {
        "experiment": "v4_8_preliminary_analysis",
        "timestamp": datetime.now().isoformat(),
        "n_v4_models": len(v4_data),
        "n_v4_results": sum(len(v) for v in v4_data.values()),
        "n_v2_models": len(v2_data),
        "n_v2_results": sum(len(v) for v in v2_data.values()),
    }

    # Run all analyses
    report["validation"] = validate_results(v4_data, v2_data)
    report["thinking_mode"] = analyze_thinking_mode_impact(v4_data)
    report["config_interaction"] = analyze_config_model_interaction(v4_data)
    report["complexity"] = analyze_complexity_scaling(v4_data)
    report["error_taxonomy"] = analyze_error_taxonomy(v4_data)
    report["latency_efficiency"] = analyze_latency_efficiency(v4_data)

    # Save preliminary analysis
    out_path = RESULTS_DIR / "v4_8_preliminary_analysis.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"\nSaved: {out_path}")

    # Cross-validation (separate file for Rmd compatibility)
    comparison = compute_v2_v4_comparison(v4_data, v2_data)
    comp_path = RESULTS_DIR / "v4_8_comparison_v2_vs_v4.json"
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2, default=str)
    logger.info(f"Saved: {comp_path}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="V4-8 Deep Analysis: thinking mode, cross-validation, error taxonomy"
    )
    parser.add_argument("--validate", action="store_true",
                        help="Run data validation only")
    parser.add_argument("--partial", action="store_true",
                        help="Include intermediate (in-progress) results")
    args = parser.parse_args()

    v4_data = load_v4_8_results(include_partial=args.partial)
    v2_data = load_v2_8_results()

    if not v4_data:
        logger.error("No V4-8 results found!")
        sys.exit(1)

    if args.validate:
        result = validate_results(v4_data, v2_data)
        out = RESULTS_DIR / "v4_8_validation.json"
        with open(out, "w") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Saved: {out}")
        sys.exit(0 if result["n_issues"] == 0 else 1)

    generate_full_report(v4_data, v2_data)


if __name__ == "__main__":
    main()
