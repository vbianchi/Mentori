"""
Shared infrastructure for V2 paper experiments.

Extends exp_common with:
- compute_pass_rate(results, threshold=3) → float
- compute_refusal_rate(results) → float
- format_v2_table(rows, headers) → markdown string
- Standardized V2 result saving and report generation

All V2 experiments use:
- Primary metric: % of questions with correctness ≥ threshold (pass rate)
- Secondary metrics: mean score, median latency, source coverage
"""

import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Re-export everything from exp_common for convenience
from tests.experiments.exp_common import (
    JUDGE_MODEL,
    GEN_MODEL,
    JUDGE_OPTIONS,
    JUDGE_THINK,
    INDEX_MAP,
    ADMIN_EMAILS,
    find_admin_user_id,
    check_index_exists,
    configure_gemini_from_admin,
    setup_retriever,
    setup_pipeline,
    load_ground_truth,
    load_intermediate,
    save_intermediate,
    result_key,
    judge_answer,
    parse_judge_scores,
    save_final_results,
    aggregate_scores,
    EXPERIMENTS_DIR as V1_EXPERIMENTS_DIR,
    RESULTS_DIR as V1_RESULTS_DIR,
)

# V2-specific paths
V2_DIR = Path(__file__).parent
V2_RESULTS_DIR = V2_DIR / "results_v2"

# V1 results (for post-hoc reuse)
V1_RESULTS = V1_EXPERIMENTS_DIR / "results"

# Default pass threshold
DEFAULT_PASS_THRESHOLD = 3


# ─────────────────────────────────────────────────────────────
# Pass rate computation
# ─────────────────────────────────────────────────────────────

def compute_pass_rate(
    results: List[Dict],
    score_key: str = "correctness",
    threshold: int = DEFAULT_PASS_THRESHOLD,
    judge_key: Optional[str] = None,
) -> float:
    """Compute % of questions that pass (score >= threshold).

    Args:
        results: List of per-question result dicts
        score_key: Which score dimension to check (default: correctness)
        threshold: Minimum score to count as pass (default: 3)
        judge_key: If scores are nested under judge_scores[judge_key],
                   specify the judge key. If None, looks in judge_scores
                   dict directly or in the top-level result.

    Returns:
        Float between 0.0 and 100.0 (percentage)
    """
    passes = 0
    total = 0

    for r in results:
        score = _extract_score(r, score_key, judge_key)
        if score is not None:
            total += 1
            if score >= threshold:
                passes += 1

    if total == 0:
        return 0.0
    return round((passes / total) * 100, 1)


def compute_refusal_rate(
    results: List[Dict],
    threshold: int = DEFAULT_PASS_THRESHOLD,
    judge_key: Optional[str] = None,
) -> float:
    """Compute % of unanswerable questions correctly refused.

    Uses refusal_accuracy score from the unanswerable judge prompt.
    A score >= threshold means the system correctly refused to answer.

    Returns:
        Float between 0.0 and 100.0 (percentage)
    """
    return compute_pass_rate(
        results,
        score_key="refusal_accuracy",
        threshold=threshold,
        judge_key=judge_key,
    )


def compute_median_latency(results: List[Dict]) -> float:
    """Compute median latency in seconds from results."""
    latencies = []
    for r in results:
        gen = r.get("generation", {})
        lat = gen.get("latency_s")
        if lat and lat > 0:
            latencies.append(lat)
    if not latencies:
        return 0.0
    return round(statistics.median(latencies), 1)


def compute_mean_source_coverage(results: List[Dict]) -> float:
    """Compute mean source coverage from citation metrics."""
    coverages = []
    for r in results:
        cit = r.get("citation_metrics", {})
        cov = cit.get("source_coverage")
        if cov is not None:
            coverages.append(cov)
    if not coverages:
        return 0.0
    return round(statistics.mean(coverages), 2)


def compute_mean_score(
    results: List[Dict],
    score_key: str = "correctness",
    judge_key: Optional[str] = None,
) -> float:
    """Compute mean score for a dimension."""
    scores = []
    for r in results:
        score = _extract_score(r, score_key, judge_key)
        if score is not None:
            scores.append(score)
    if not scores:
        return 0.0
    return round(statistics.mean(scores), 2)


def _extract_score(
    result: Dict,
    score_key: str,
    judge_key: Optional[str] = None,
) -> Optional[int]:
    """Extract a score from a result dict, handling various nesting patterns."""
    # Pattern 1: result["judge_scores"][judge_key][score_key]
    judge_scores = result.get("judge_scores", {})
    if judge_key and judge_key in judge_scores:
        val = judge_scores[judge_key].get(score_key)
        if val is not None:
            return int(val)

    # Pattern 2: result["judge_scores"][score_key] (flat judge scores)
    if score_key in judge_scores:
        return int(judge_scores[score_key])

    # Pattern 3: result["answer_scores"][score_key] (exp4 style)
    answer_scores = result.get("answer_scores", {})
    if score_key in answer_scores:
        return int(answer_scores[score_key])

    # Pattern 4: Try all judge keys if no specific one given
    if not judge_key:
        for jk, jv in judge_scores.items():
            if isinstance(jv, dict) and score_key in jv:
                return int(jv[score_key])

    return None


# ─────────────────────────────────────────────────────────────
# Aggregate V2 metrics for a group of results
# ─────────────────────────────────────────────────────────────

def aggregate_v2_metrics(
    results: List[Dict],
    threshold: int = DEFAULT_PASS_THRESHOLD,
    judge_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute all V2 metrics for a group of results.

    Returns dict with:
        pass_rate, mean_correctness, refusal_rate, median_latency,
        source_coverage, n_total, n_answerable, n_unanswerable
    """
    answerable = [r for r in results if r.get("answerable", True)]
    unanswerable = [r for r in results if not r.get("answerable", True)]

    return {
        "pass_rate": compute_pass_rate(answerable, threshold=threshold, judge_key=judge_key),
        "mean_correctness": compute_mean_score(answerable, "correctness", judge_key),
        "refusal_rate": compute_refusal_rate(unanswerable, threshold=threshold, judge_key=judge_key),
        "median_latency": compute_median_latency(results),
        "source_coverage": compute_mean_source_coverage(results),
        "n_total": len(results),
        "n_answerable": len(answerable),
        "n_unanswerable": len(unanswerable),
    }


# ─────────────────────────────────────────────────────────────
# Detect judge key from results
# ─────────────────────────────────────────────────────────────

def detect_judge_key(results: List[Dict]) -> Optional[str]:
    """Auto-detect the judge key name from result data.

    Returns the judge short name (e.g. 'gpt-oss_20b') or None if scores
    are stored flat (not nested under judge names).
    """
    for r in results:
        js = r.get("judge_scores", {})
        # If judge_scores contains nested dicts with correctness, it's keyed by judge
        for k, v in js.items():
            if isinstance(v, dict) and "correctness" in v:
                return k
        # If it has correctness directly, it's flat
        if "correctness" in js:
            return None
    return None


# ─────────────────────────────────────────────────────────────
# Table formatting
# ─────────────────────────────────────────────────────────────

def format_v2_table(
    headers: List[str],
    rows: List[List[str]],
    alignments: Optional[List[str]] = None,
) -> str:
    """Format a markdown table.

    Args:
        headers: Column header strings
        rows: List of rows, each a list of cell strings
        alignments: Optional list of 'l', 'r', 'c' per column

    Returns:
        Markdown table string
    """
    if not alignments:
        alignments = ["l"] * len(headers)

    # Build separator
    sep_parts = []
    for a in alignments:
        if a == "r":
            sep_parts.append("---:")
        elif a == "c":
            sep_parts.append(":---:")
        else:
            sep_parts.append("---")

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(sep_parts) + " |")
    for row in rows:
        # Pad row to match headers
        padded = list(row) + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(padded[:len(headers)]) + " |")

    return "\n".join(lines)


def format_pct(value: float) -> str:
    """Format a percentage value for tables."""
    return f"{value:.0f}%"


def format_latency(value: float) -> str:
    """Format latency in seconds for tables."""
    return f"{value:.0f}s"


def format_score(value: float) -> str:
    """Format a mean score for tables."""
    return f"{value:.2f}"


# ─────────────────────────────────────────────────────────────
# V2 result saving
# ─────────────────────────────────────────────────────────────

def save_v2_results(data: Dict[str, Any], prefix: str) -> tuple:
    """Save V2 results as JSON + latest symlink.

    Returns (json_path, latest_path).
    """
    V2_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = V2_RESULTS_DIR / f"{prefix}_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    latest_path = V2_RESULTS_DIR / f"{prefix}_latest.json"
    with open(latest_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return json_path, latest_path


def save_v2_markdown(content: str, prefix: str) -> Path:
    """Save V2 markdown report.

    Returns the markdown file path.
    """
    V2_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    md_path = V2_RESULTS_DIR / f"{prefix}_{timestamp}.md"
    md_path.write_text(content)

    return md_path


# ─────────────────────────────────────────────────────────────
# Load V1 results for post-hoc analysis
# ─────────────────────────────────────────────────────────────

def load_v1_results(filename: str) -> Dict[str, Any]:
    """Load a V1 experiment result file by name.

    Args:
        filename: Just the filename, e.g. 'exp2_results_20260211_174232.json'

    Returns:
        Parsed JSON dict
    """
    path = V1_RESULTS / filename
    if not path.exists():
        raise FileNotFoundError(f"V1 result file not found: {path}")
    with open(path) as f:
        return json.load(f)


def find_v1_latest(prefix: str) -> Optional[Path]:
    """Find the latest V1 result file for a given prefix."""
    latest = V1_RESULTS / f"{prefix}_results_latest.json"
    if latest.exists():
        return latest
    # Fallback: find most recent timestamped file
    candidates = sorted(V1_RESULTS.glob(f"{prefix}_results_*.json"), reverse=True)
    candidates = [c for c in candidates if "latest" not in c.name]
    return candidates[0] if candidates else None
