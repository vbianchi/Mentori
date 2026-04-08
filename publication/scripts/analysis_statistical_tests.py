#!/usr/bin/env python3
"""
V4 Statistical Significance Tests for Mentori Paper
====================================================

Computes statistical tests for all key paper claims:
1. Self-correction vs retrieval-grounded (Finding 1)
2. Compute saturation (Finding 2)
3. Strategy x corpus crossover (Finding 4)
4. Noise robustness (Finding 5)
5. Faithfulness construct mismatch (Finding 10)
6. Kendall's W concordance
7. OOD refusal rate
8. ROUGE-L / length-bias correlation

Usage:
    uv run python publication/scripts/analysis_statistical_tests.py
"""

import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RESULTS_DIR = Path(__file__).parent / "results_v4"
V44_FILE = RESULTS_DIR / "v4_4_generation_latest.json"
V45_FILES = [
    RESULTS_DIR / "v4_5_intermediate.json",
    RESULTS_DIR / "v4_5_intermediate_s20.json",
    RESULTS_DIR / "v4_5_intermediate_s50.json",
]
MINICHECK_FILE = RESULTS_DIR / "v4_4_minicheck_latest.json"
PAPER_VAL_FILE = RESULTS_DIR / "v4_paper_validation.json"
OUTPUT_FILE = RESULTS_DIR / "v4_statistical_tests.json"

RNG = np.random.default_rng(42)
N_BOOTSTRAP = 10_000
PASS_THRESHOLD = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict | None:
    if not path.exists():
        print(f"  [SKIP] {path.name} not found")
        return None
    with open(path) as f:
        return json.load(f)


def bootstrap_ci(data: np.ndarray, stat_fn=np.mean, n_boot: int = N_BOOTSTRAP,
                 ci: float = 0.95) -> dict:
    """Bootstrap confidence interval for a statistic."""
    data = np.asarray(data, dtype=float)
    observed = float(stat_fn(data))
    boot_stats = np.empty(n_boot)
    n = len(data)
    for i in range(n_boot):
        sample = data[RNG.integers(0, n, size=n)]
        boot_stats[i] = stat_fn(sample)
    alpha = (1 - ci) / 2
    lo, hi = float(np.percentile(boot_stats, 100 * alpha)), float(np.percentile(boot_stats, 100 * (1 - alpha)))
    return {"observed": observed, "ci_lower": lo, "ci_upper": hi, "ci_level": ci, "n": n}


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, stat_fn=np.mean,
                      n_boot: int = N_BOOTSTRAP, ci: float = 0.95) -> dict:
    """Bootstrap CI for the difference stat_fn(a) - stat_fn(b), paired by index."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    assert len(a) == len(b), "Arrays must be same length for paired bootstrap"
    observed = float(stat_fn(a) - stat_fn(b))
    n = len(a)
    boot_diffs = np.empty(n_boot)
    for i in range(n_boot):
        idx = RNG.integers(0, n, size=n)
        boot_diffs[i] = stat_fn(a[idx]) - stat_fn(b[idx])
    alpha = (1 - ci) / 2
    lo = float(np.percentile(boot_diffs, 100 * alpha))
    hi = float(np.percentile(boot_diffs, 100 * (1 - alpha)))
    p_value = float(np.mean(boot_diffs <= 0)) if observed > 0 else float(np.mean(boot_diffs >= 0))
    return {"observed_diff": observed, "ci_lower": lo, "ci_upper": hi, "ci_level": ci,
            "bootstrap_p": p_value, "n": n}


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for two proportions."""
    return 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))


def mcnemar_test(pass_a: np.ndarray, pass_b: np.ndarray) -> dict:
    """McNemar's test for paired binary outcomes."""
    pass_a, pass_b = np.asarray(pass_a, dtype=bool), np.asarray(pass_b, dtype=bool)
    # b = a passed, b failed;  c = a failed, b passed
    b = int(np.sum(pass_a & ~pass_b))
    c = int(np.sum(~pass_a & pass_b))
    # exact binomial (Edwards) when b+c < 25, otherwise chi-square
    n_disc = b + c
    if n_disc == 0:
        return {"b": b, "c": c, "n_discordant": 0, "statistic": 0, "p_value": 1.0, "method": "no_discordant"}
    if n_disc < 25:
        p_value = float(stats.binomtest(b, n_disc, 0.5).pvalue)
        method = "exact_binomial"
        statistic = b
    else:
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)  # continuity correction
        p_value = float(1 - stats.chi2.cdf(chi2, 1))
        method = "chi2_continuity"
        statistic = float(chi2)
    return {"b": b, "c": c, "n_discordant": n_disc, "statistic": statistic,
            "p_value": p_value, "method": method}


def fisher_z_test(r: float, n: int) -> dict:
    """Test whether correlation r is significantly different from zero using Fisher z-transform."""
    z = 0.5 * math.log((1 + r) / (1 - r)) if abs(r) < 1 else float('inf') * np.sign(r)
    se = 1 / math.sqrt(n - 3) if n > 3 else float('inf')
    z_stat = z / se
    p_value = float(2 * stats.norm.sf(abs(z_stat)))
    ci_z_lo = z - 1.96 * se
    ci_z_hi = z + 1.96 * se
    ci_r_lo = float(math.tanh(ci_z_lo))
    ci_r_hi = float(math.tanh(ci_z_hi))
    return {"r": r, "n": n, "fisher_z": float(z), "z_statistic": float(z_stat),
            "p_value": p_value, "ci_r_lower": ci_r_lo, "ci_r_upper": ci_r_hi}


# ---------------------------------------------------------------------------
# Build per-question lookup from V4-4
# ---------------------------------------------------------------------------

def build_v44_question_map(v44_data: dict) -> dict:
    """Returns {question_id: {config: result_dict}}"""
    qmap: dict = defaultdict(dict)
    for r in v44_data["per_question_results"]:
        qid = r["question_id"]
        cfg = r["config"]
        qmap[qid][cfg] = r
    return dict(qmap)


def get_pass_array(qmap: dict, config: str, answerable_only: bool = True) -> tuple[list[str], np.ndarray]:
    """Return (question_ids, pass_binary_array) for a config."""
    qids, vals = [], []
    for qid, cfgs in sorted(qmap.items()):
        if config not in cfgs:
            continue
        r = cfgs[config]
        if answerable_only and not r.get("answerable", True):
            continue
        score = r["judge_scores"]["correctness"]
        qids.append(qid)
        vals.append(1 if score >= PASS_THRESHOLD else 0)
    return qids, np.array(vals)


def get_score_array(qmap: dict, config: str, dimension: str = "correctness",
                    answerable_only: bool = True) -> tuple[list[str], np.ndarray]:
    """Return (question_ids, score_array) for a config and dimension."""
    qids, vals = [], []
    for qid, cfgs in sorted(qmap.items()):
        if config not in cfgs:
            continue
        r = cfgs[config]
        if answerable_only and not r.get("answerable", True):
            continue
        qids.append(qid)
        vals.append(r["judge_scores"][dimension])
    return qids, np.array(vals, dtype=float)


# ---------------------------------------------------------------------------
# Build V4-5 combined data
# ---------------------------------------------------------------------------

def load_v45_all() -> list[dict]:
    """Load and merge all V4-5 intermediate results."""
    all_results = []
    for f in V45_FILES:
        d = load_json(f)
        if d and "results" in d:
            all_results.extend(d["results"])
    return all_results


def parse_index(name: str) -> tuple[int, int]:
    """exp_v4_s20_n3 -> (20, 3)"""
    parts = name.replace("exp_v4_", "").split("_")
    s = int(parts[0].replace("s", ""))
    n = int(parts[1].replace("n", ""))
    return s, n


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_1_selfcorrection_vs_rlm(v44_data: dict) -> dict:
    """Finding 1: Self-correction (verified_pass) vs retrieval-grounded (rlm_10)."""
    print("\n=== Test 1: Self-correction vs Retrieval-grounded ===")
    qmap = build_v44_question_map(v44_data)

    qids_rlm, pass_rlm = get_pass_array(qmap, "rlm_10")
    qids_vp, pass_vp = get_pass_array(qmap, "verified_pass")

    # Ensure paired: same question set
    common = sorted(set(qids_rlm) & set(qids_vp))
    idx_rlm = {q: i for i, q in enumerate(qids_rlm)}
    idx_vp = {q: i for i, q in enumerate(qids_vp)}
    paired_rlm = np.array([pass_rlm[idx_rlm[q]] for q in common])
    paired_vp = np.array([pass_vp[idx_vp[q]] for q in common])

    pr_rlm = float(np.mean(paired_rlm))
    pr_vp = float(np.mean(paired_vp))
    gap = pr_rlm - pr_vp

    # Bootstrap CI for gap
    boot_ci = bootstrap_diff_ci(paired_rlm, paired_vp, stat_fn=np.mean)

    # McNemar's test
    mcn = mcnemar_test(paired_rlm, paired_vp)

    # Cohen's h
    h = cohens_h(pr_rlm, pr_vp)

    # Also test correctness scores
    _, scores_rlm = get_score_array(qmap, "rlm_10")
    _, scores_vp = get_score_array(qmap, "verified_pass")
    wilcoxon = stats.wilcoxon(scores_rlm[:len(common)], scores_vp[:len(common)], alternative='two-sided')

    result = {
        "description": "Self-correction (verified_pass) vs retrieval-grounded (rlm_10) pass rate gap",
        "n_paired": len(common),
        "pass_rate_rlm_10": round(pr_rlm, 4),
        "pass_rate_verified_pass": round(pr_vp, 4),
        "gap_pp": round(gap * 100, 1),
        "bootstrap_ci": {k: round(v, 4) if isinstance(v, float) else v for k, v in boot_ci.items()},
        "mcnemar": {k: round(v, 6) if isinstance(v, float) else v for k, v in mcn.items()},
        "cohens_h": round(h, 4),
        "effect_interpretation": "large" if abs(h) >= 0.8 else "medium" if abs(h) >= 0.5 else "small",
        "wilcoxon_scores": {
            "statistic": float(wilcoxon.statistic),
            "p_value": float(wilcoxon.pvalue),
        },
    }

    print(f"  Pass rates: rlm_10={pr_rlm:.1%}, verified_pass={pr_vp:.1%}, gap={gap*100:.1f}pp")
    print(f"  Bootstrap 95% CI for gap: [{boot_ci['ci_lower']*100:.1f}, {boot_ci['ci_upper']*100:.1f}]pp")
    print(f"  McNemar p={mcn['p_value']:.4g}, Cohen's h={h:.3f} ({result['effect_interpretation']})")
    print(f"  Wilcoxon signed-rank p={wilcoxon.pvalue:.4g}")
    return result


def test_2_compute_saturation(v44_data: dict) -> dict:
    """Finding 2: Compute saturation across rlm_5, rlm_10, rlm_20."""
    print("\n=== Test 2: Compute Saturation (RLM iterations) ===")
    qmap = build_v44_question_map(v44_data)

    configs = ["rlm_5", "rlm_10", "rlm_20"]
    score_arrays = {}
    pass_arrays = {}
    for cfg in configs:
        _, scores = get_score_array(qmap, cfg)
        _, passes = get_pass_array(qmap, cfg)
        score_arrays[cfg] = scores
        pass_arrays[cfg] = passes

    # Kruskal-Wallis (non-parametric, doesn't assume normality)
    kw = stats.kruskal(*[score_arrays[c] for c in configs])

    # Friedman test (repeated measures non-parametric) — all same questions
    common_qids = None
    for cfg in configs:
        qids, _ = get_score_array(qmap, cfg)
        s = set(qids)
        common_qids = s if common_qids is None else common_qids & s
    common_qids = sorted(common_qids)  # type: ignore

    aligned = {}
    for cfg in configs:
        qids, scores = get_score_array(qmap, cfg)
        qid_to_score = dict(zip(qids, scores))
        aligned[cfg] = np.array([qid_to_score[q] for q in common_qids])

    friedman = stats.friedmanchisquare(*[aligned[c] for c in configs])

    # Pairwise Wilcoxon with Bonferroni
    pairs = [("rlm_5", "rlm_10"), ("rlm_10", "rlm_20"), ("rlm_5", "rlm_20")]
    pairwise = {}
    for a, b in pairs:
        w = stats.wilcoxon(aligned[a], aligned[b], alternative='two-sided')
        p_bonf = min(float(w.pvalue) * len(pairs), 1.0)
        boot = bootstrap_diff_ci(aligned[a], aligned[b], stat_fn=np.mean)
        pairwise[f"{a}_vs_{b}"] = {
            "wilcoxon_statistic": float(w.statistic),
            "wilcoxon_p_raw": float(w.pvalue),
            "wilcoxon_p_bonferroni": round(p_bonf, 6),
            "mean_diff": round(float(np.mean(aligned[a]) - np.mean(aligned[b])), 4),
            "bootstrap_ci_diff": {k: round(v, 4) if isinstance(v, float) else v for k, v in boot.items()},
        }

    # Pass rate CIs
    pass_rate_cis = {}
    for cfg in configs:
        ci = bootstrap_ci(pass_arrays[cfg], stat_fn=np.mean)
        pass_rate_cis[cfg] = {k: round(v, 4) if isinstance(v, float) else v for k, v in ci.items()}

    result = {
        "description": "Compute saturation: rlm_5 vs rlm_10 vs rlm_20",
        "n_common_questions": len(common_qids),
        "kruskal_wallis": {"statistic": float(kw.statistic), "p_value": float(kw.pvalue)},
        "friedman": {"statistic": float(friedman.statistic), "p_value": float(friedman.pvalue)},
        "pairwise_bonferroni": pairwise,
        "pass_rate_bootstrap_ci": pass_rate_cis,
        "mean_correctness": {cfg: round(float(np.mean(score_arrays[cfg])), 4) for cfg in configs},
    }

    print(f"  Mean correctness: " + ", ".join(f"{c}={np.mean(score_arrays[c]):.2f}" for c in configs))
    print(f"  Kruskal-Wallis H={kw.statistic:.3f}, p={kw.pvalue:.4g}")
    print(f"  Friedman chi2={friedman.statistic:.3f}, p={friedman.pvalue:.4g}")
    for pair_name, pair_res in pairwise.items():
        print(f"  {pair_name}: diff={pair_res['mean_diff']:.3f}, p_bonf={pair_res['wilcoxon_p_bonferroni']:.4g}")
    return result


def test_3_strategy_corpus_crossover(v45_results: list[dict]) -> dict | None:
    """Finding 4: Strategy x corpus size interaction."""
    print("\n=== Test 3: Strategy x Corpus Size Crossover ===")
    if not v45_results:
        print("  [SKIP] No V4-5 data available")
        return None

    # Build pass rates per (config, corpus_size)
    cell_passes: dict[tuple[str, int], list[int]] = defaultdict(list)
    cell_scores: dict[tuple[str, int], list[float]] = defaultdict(list)

    for r in v45_results:
        if not r.get("answerable", True):
            continue
        js = r.get("judge_scores", {})
        if "correctness" not in js:
            continue
        idx = r["index_name"]
        s, n_ratio = parse_index(idx)
        cfg = r["config"]
        score = js["correctness"]
        cell_passes[(cfg, s)].append(1 if score >= PASS_THRESHOLD else 0)
        cell_scores[(cfg, s)].append(float(score))

    # Get available sizes and configs
    all_sizes = sorted(set(s for _, s in cell_passes.keys()))
    all_configs = sorted(set(c for c, _ in cell_passes.keys()))

    print(f"  Available sizes: {all_sizes}")
    print(f"  Available configs: {all_configs}")

    # Two-way interaction: for each pair of configs at each size, track pass rate
    # Use bootstrap to test interaction
    # Interaction = is the difference between two strategies constant across corpus sizes?
    rlm_configs = [c for c in all_configs if c.startswith("rlm")]
    non_rlm_configs = [c for c in all_configs if not c.startswith("rlm")]

    # Pass rates table
    pass_rate_table = {}
    for cfg in all_configs:
        pass_rate_table[cfg] = {}
        for s in all_sizes:
            key = (cfg, s)
            if key in cell_passes:
                arr = np.array(cell_passes[key])
                ci = bootstrap_ci(arr, stat_fn=np.mean)
                pass_rate_table[cfg][f"s{s}"] = {
                    "pass_rate": round(float(np.mean(arr)), 4),
                    "ci_lower": round(ci["ci_lower"], 4),
                    "ci_upper": round(ci["ci_upper"], 4),
                    "n": len(arr),
                }

    # Interaction test: compare rlm_10 advantage over single_pass across sizes
    interaction_tests = {}
    if "rlm_10" in all_configs and "single_pass" in all_configs:
        sizes_with_both = [s for s in all_sizes
                           if ("rlm_10", s) in cell_passes and ("single_pass", s) in cell_passes]
        if len(sizes_with_both) >= 2:
            diffs_by_size = {}
            for s in sizes_with_both:
                rlm_arr = np.array(cell_passes[("rlm_10", s)])
                sp_arr = np.array(cell_passes[("single_pass", s)])
                # Not paired (different n may differ), use independent bootstrap
                rlm_pr = float(np.mean(rlm_arr))
                sp_pr = float(np.mean(sp_arr))
                diff = rlm_pr - sp_pr
                # Bootstrap CI for difference
                boot_diffs = []
                for _ in range(N_BOOTSTRAP):
                    b_rlm = float(np.mean(RNG.choice(rlm_arr, size=len(rlm_arr), replace=True)))
                    b_sp = float(np.mean(RNG.choice(sp_arr, size=len(sp_arr), replace=True)))
                    boot_diffs.append(b_rlm - b_sp)
                boot_diffs = np.array(boot_diffs)
                diffs_by_size[f"s{s}"] = {
                    "rlm_10_pr": round(rlm_pr, 4),
                    "single_pass_pr": round(sp_pr, 4),
                    "diff_pp": round(diff * 100, 1),
                    "ci_lower": round(float(np.percentile(boot_diffs, 2.5)) * 100, 1),
                    "ci_upper": round(float(np.percentile(boot_diffs, 97.5)) * 100, 1),
                }
            interaction_tests["rlm_10_vs_single_pass_by_size"] = diffs_by_size

            # Formal interaction: is the diff at smallest size != diff at largest size?
            s_min, s_max = sizes_with_both[0], sizes_with_both[-1]
            rlm_min = np.array(cell_passes[("rlm_10", s_min)])
            sp_min = np.array(cell_passes[("single_pass", s_min)])
            rlm_max = np.array(cell_passes[("rlm_10", s_max)])
            sp_max = np.array(cell_passes[("single_pass", s_max)])

            boot_interaction = []
            for _ in range(N_BOOTSTRAP):
                d_min = float(np.mean(RNG.choice(rlm_min, len(rlm_min), replace=True))) - \
                        float(np.mean(RNG.choice(sp_min, len(sp_min), replace=True)))
                d_max = float(np.mean(RNG.choice(rlm_max, len(rlm_max), replace=True))) - \
                        float(np.mean(RNG.choice(sp_max, len(sp_max), replace=True)))
                boot_interaction.append(d_max - d_min)
            boot_interaction = np.array(boot_interaction)
            obs_interaction = (float(np.mean(rlm_max)) - float(np.mean(sp_max))) - \
                              (float(np.mean(rlm_min)) - float(np.mean(sp_min)))
            interaction_tests["crossover_interaction"] = {
                "description": f"Difference in rlm_10 advantage: s{s_max} minus s{s_min}",
                "observed_pp": round(obs_interaction * 100, 1),
                "ci_lower_pp": round(float(np.percentile(boot_interaction, 2.5)) * 100, 1),
                "ci_upper_pp": round(float(np.percentile(boot_interaction, 97.5)) * 100, 1),
                "significant": bool(
                    np.percentile(boot_interaction, 2.5) > 0 or np.percentile(boot_interaction, 97.5) < 0
                ),
            }

    result = {
        "description": "Strategy x corpus size interaction (V4-5)",
        "n_results": len(v45_results),
        "sizes": all_sizes,
        "configs": all_configs,
        "pass_rate_table": pass_rate_table,
        "interaction_tests": interaction_tests,
    }

    # Print summary
    print(f"  Pass rate table (answerable only):")
    header = "  {:>15s}".format("Config") + "".join(f"  s{s:>3d}" for s in all_sizes)
    print(header)
    for cfg in all_configs:
        row = f"  {cfg:>15s}"
        for s in all_sizes:
            key = f"s{s}"
            if key in pass_rate_table.get(cfg, {}):
                pr = pass_rate_table[cfg][key]["pass_rate"]
                row += f"  {pr*100:5.1f}"
            else:
                row += "    --"
        print(row)

    return result


def test_4_noise_robustness(v45_results: list[dict]) -> dict | None:
    """Finding 5: Noise robustness across n0, n1, n3."""
    print("\n=== Test 4: Noise Robustness ===")
    if not v45_results:
        print("  [SKIP] No V4-5 data available")
        return None

    # Group by (config, corpus_size, noise_ratio)
    cell_passes: dict[tuple[str, int, int], list[int]] = defaultdict(list)

    for r in v45_results:
        if not r.get("answerable", True):
            continue
        js = r.get("judge_scores", {})
        if "correctness" not in js:
            continue
        s, n = parse_index(r["index_name"])
        cfg = r["config"]
        score = js["correctness"]
        cell_passes[(cfg, s, n)].append(1 if score >= PASS_THRESHOLD else 0)

    # Available noise levels per corpus size
    all_keys = set(cell_passes.keys())
    sizes = sorted(set(s for _, s, _ in all_keys))
    noises = sorted(set(n for _, _, n in all_keys))
    configs = sorted(set(c for c, _, _ in all_keys))

    print(f"  Sizes: {sizes}, Noise levels: {noises}, Configs: {configs}")

    # For each size, compare n0 vs n1 vs n3
    noise_tests = {}
    for s in sizes:
        available_noises = [n for n in noises if any((c, s, n) in cell_passes for c in configs)]
        if len(available_noises) < 2:
            continue

        # Aggregate across configs at this size
        agg_by_noise: dict[int, list[int]] = defaultdict(list)
        for n in available_noises:
            for c in configs:
                key = (c, s, n)
                if key in cell_passes:
                    agg_by_noise[n].extend(cell_passes[key])

        noise_prs = {}
        for n in available_noises:
            arr = np.array(agg_by_noise[n])
            ci = bootstrap_ci(arr, stat_fn=np.mean)
            noise_prs[f"n{n}"] = {
                "pass_rate": round(float(np.mean(arr)), 4),
                "ci_lower": round(ci["ci_lower"], 4),
                "ci_upper": round(ci["ci_upper"], 4),
                "n": len(arr),
            }

        # Pairwise comparisons (n0 vs n1, n0 vs n3, etc.)
        pairwise = {}
        noise_pairs = [(available_noises[i], available_noises[j])
                       for i in range(len(available_noises))
                       for j in range(i + 1, len(available_noises))]
        for n_a, n_b in noise_pairs:
            arr_a = np.array(agg_by_noise[n_a])
            arr_b = np.array(agg_by_noise[n_b])
            pr_a = float(np.mean(arr_a))
            pr_b = float(np.mean(arr_b))
            diff = pr_a - pr_b
            # Bootstrap CI
            boot_diffs = []
            for _ in range(N_BOOTSTRAP):
                b_a = float(np.mean(RNG.choice(arr_a, len(arr_a), replace=True)))
                b_b = float(np.mean(RNG.choice(arr_b, len(arr_b), replace=True)))
                boot_diffs.append(b_a - b_b)
            boot_diffs_arr = np.array(boot_diffs)
            # Mann-Whitney U
            mw = stats.mannwhitneyu(arr_a, arr_b, alternative='two-sided')
            p_bonf = min(float(mw.pvalue) * len(noise_pairs), 1.0)

            pairwise[f"n{n_a}_vs_n{n_b}"] = {
                "diff_pp": round(diff * 100, 1),
                "ci_lower_pp": round(float(np.percentile(boot_diffs_arr, 2.5)) * 100, 1),
                "ci_upper_pp": round(float(np.percentile(boot_diffs_arr, 97.5)) * 100, 1),
                "mannwhitney_U": float(mw.statistic),
                "mannwhitney_p_raw": float(mw.pvalue),
                "mannwhitney_p_bonferroni": round(p_bonf, 6),
            }

        noise_tests[f"s{s}"] = {"pass_rates": noise_prs, "pairwise": pairwise}

    result = {
        "description": "Noise robustness: pass rate change across noise ratios",
        "sizes": sizes,
        "noise_levels": noises,
        "per_size": noise_tests,
    }

    for s_key, s_data in noise_tests.items():
        print(f"  {s_key}:")
        for n_key, n_data in s_data["pass_rates"].items():
            print(f"    {n_key}: {n_data['pass_rate']*100:.1f}% [{n_data['ci_lower']*100:.1f}, {n_data['ci_upper']*100:.1f}]")
        for pair_key, pair_data in s_data["pairwise"].items():
            print(f"    {pair_key}: {pair_data['diff_pp']:+.1f}pp, p_bonf={pair_data['mannwhitney_p_bonferroni']:.4g}")

    return result


def test_5_faithfulness_mismatch(minicheck_data: dict | None) -> dict | None:
    """Finding 10: Faithfulness construct mismatch (MiniCheck precision vs judge faithfulness)."""
    print("\n=== Test 5: Faithfulness Construct Mismatch ===")
    if minicheck_data is None:
        print("  [SKIP] No MiniCheck data")
        return None

    mc_precisions = []
    judge_faithfulness = []
    mc_recalls = []
    judge_correctness = []

    for r in minicheck_data["per_result"]:
        mc_precisions.append(r["minicheck"]["precision"])
        mc_recalls.append(r["minicheck"]["recall"])
        judge_faithfulness.append(r["judge_scores"]["faithfulness"])
        judge_correctness.append(r["judge_scores"]["correctness"])

    mc_prec = np.array(mc_precisions)
    j_faith = np.array(judge_faithfulness)
    mc_rec = np.array(mc_recalls)
    j_corr = np.array(judge_correctness)

    # Spearman correlations
    rho_prec_faith, p_prec_faith = stats.spearmanr(mc_prec, j_faith)
    rho_rec_corr, p_rec_corr = stats.spearmanr(mc_rec, j_corr)
    rho_prec_corr, p_prec_corr = stats.spearmanr(mc_prec, j_corr)

    n = len(mc_prec)

    # Fisher z-transform for rho_prec_faith (the key claim: rho=0.099 not sig different from 0?)
    fisher_prec_faith = fisher_z_test(float(rho_prec_faith), n)
    fisher_rec_corr = fisher_z_test(float(rho_rec_corr), n)

    # Bootstrap CI for correlations
    def spearman_rho(x, y):
        return float(stats.spearmanr(x, y).correlation)

    boot_prec_faith = []
    boot_rec_corr = []
    for _ in range(N_BOOTSTRAP):
        idx = RNG.integers(0, n, size=n)
        boot_prec_faith.append(spearman_rho(mc_prec[idx], j_faith[idx]))
        boot_rec_corr.append(spearman_rho(mc_rec[idx], j_corr[idx]))

    boot_prec_faith = np.array(boot_prec_faith)
    boot_rec_corr = np.array(boot_rec_corr)

    result = {
        "description": "Faithfulness construct mismatch: MiniCheck precision vs judge faithfulness",
        "n": n,
        "minicheck_precision_vs_judge_faithfulness": {
            "spearman_rho": round(float(rho_prec_faith), 4),
            "p_value": float(p_prec_faith),
            "fisher_z": fisher_prec_faith,
            "bootstrap_ci": [round(float(np.percentile(boot_prec_faith, 2.5)), 4),
                             round(float(np.percentile(boot_prec_faith, 97.5)), 4)],
        },
        "minicheck_recall_vs_judge_correctness": {
            "spearman_rho": round(float(rho_rec_corr), 4),
            "p_value": float(p_rec_corr),
            "fisher_z": fisher_rec_corr,
            "bootstrap_ci": [round(float(np.percentile(boot_rec_corr, 2.5)), 4),
                             round(float(np.percentile(boot_rec_corr, 97.5)), 4)],
        },
        "minicheck_precision_vs_judge_correctness": {
            "spearman_rho": round(float(rho_prec_corr), 4),
            "p_value": float(p_prec_corr),
        },
        "interpretation": (
            "MiniCheck precision has near-zero correlation with judge faithfulness, "
            "confirming they measure different constructs. MiniCheck recall correlates "
            "with judge correctness, suggesting the judge's 'faithfulness' dimension "
            "actually measures answer presence, not factual grounding."
        ),
    }

    print(f"  MC precision vs judge faithfulness: rho={rho_prec_faith:.4f}, p={p_prec_faith:.4g}")
    print(f"    Fisher z CI: [{fisher_prec_faith['ci_r_lower']:.4f}, {fisher_prec_faith['ci_r_upper']:.4f}]")
    print(f"    Bootstrap CI: [{np.percentile(boot_prec_faith, 2.5):.4f}, {np.percentile(boot_prec_faith, 97.5):.4f}]")
    print(f"  MC recall vs judge correctness: rho={rho_rec_corr:.4f}, p={p_rec_corr:.4g}")
    return result


def test_6_kendalls_w(paper_val_data: dict | None) -> dict | None:
    """Test 6: Kendall's W concordance with p-value."""
    print("\n=== Test 6: Kendall's W Concordance ===")
    if paper_val_data is None or "kendalls_w" not in paper_val_data:
        print("  [SKIP] No paper validation data")
        return None

    kw_data = paper_val_data["kendalls_w"]
    W = kw_data["kendalls_w"]
    k = kw_data["n_methods"]  # number of raters
    n = kw_data["n_configs"]  # number of items being ranked

    # Chi-square approximation for Kendall's W
    chi2 = k * (n - 1) * W
    df = n - 1
    p_value = float(1 - stats.chi2.cdf(chi2, df))

    # Extract ranks for bootstrap
    config_details = kw_data["config_details"]
    rank_matrix = []  # k raters x n items
    configs = sorted(config_details.keys())
    for method in ["det_rank", "judge_rank", "mc_f1_rank"]:
        ranks = [config_details[c][method] for c in configs]
        rank_matrix.append(ranks)
    rank_matrix = np.array(rank_matrix)  # shape (k, n)

    # Bootstrap CI for W
    def compute_w(rank_mat):
        k_r, n_r = rank_mat.shape
        rank_sums = rank_mat.sum(axis=0)
        mean_rank_sum = np.mean(rank_sums)
        ss = np.sum((rank_sums - mean_rank_sum) ** 2)
        w = 12 * ss / (k_r ** 2 * (n_r ** 3 - n_r))
        return float(w)

    boot_ws = []
    for _ in range(N_BOOTSTRAP):
        # Resample items (columns) with replacement
        idx = RNG.integers(0, n, size=n)
        boot_ranks = rank_matrix[:, idx]
        # Re-rank within each rater
        reranked = np.zeros_like(boot_ranks)
        for r_idx in range(k):
            reranked[r_idx] = stats.rankdata(boot_ranks[r_idx])
        boot_ws.append(compute_w(reranked))

    boot_ws = np.array(boot_ws)

    result = {
        "description": "Kendall's W concordance across 3 evaluation methods",
        "W": round(W, 4),
        "k_raters": k,
        "n_items": n,
        "chi2_statistic": round(chi2, 4),
        "df": df,
        "p_value": p_value,
        "significant_at_005": p_value < 0.05,
        "bootstrap_ci_W": [round(float(np.percentile(boot_ws, 2.5)), 4),
                           round(float(np.percentile(boot_ws, 97.5)), 4)],
        "interpretation": kw_data["interpretation"],
    }

    print(f"  W={W:.4f}, chi2={chi2:.3f}, df={df}, p={p_value:.4g}")
    print(f"  Bootstrap 95% CI for W: [{np.percentile(boot_ws, 2.5):.4f}, {np.percentile(boot_ws, 97.5):.4f}]")
    print(f"  Interpretation: {kw_data['interpretation']} concordance")
    return result


def test_7_ood_refusal(v44_data: dict) -> dict:
    """Test 7: OOD refusal rate — exact binomial CI for 0% hallucination."""
    print("\n=== Test 7: OOD Refusal Rate ===")
    qmap = build_v44_question_map(v44_data)

    configs = list(v44_data["config_metrics"].keys())
    ood_results = {}

    for cfg in configs:
        n_refused = 0
        n_ood = 0
        for qid, cfgs in qmap.items():
            if cfg not in cfgs:
                continue
            r = cfgs[cfg]
            if r.get("answerable", True):
                continue
            n_ood += 1
            js = r["judge_scores"]
            # OOD questions use refusal_accuracy / hallucination_avoidance instead of correctness
            if "refusal_accuracy" in js:
                # refusal_accuracy >= 4 means correctly refused
                if js["refusal_accuracy"] >= 4:
                    n_refused += 1
            elif "correctness" in js:
                # Fallback: low correctness = refused
                if js["correctness"] <= 1:
                    n_refused += 1

        if n_ood > 0:
            refusal_rate = n_refused / n_ood
            hallucination_rate = 1 - refusal_rate
            n_hallucinated = n_ood - n_refused

            # Exact binomial CI for hallucination rate (Clopper-Pearson)
            ci = stats.binom.interval(0.95, n_ood, hallucination_rate) if hallucination_rate > 0 else (0, 0)
            # Use beta distribution for proper CI
            alpha_ci = 0.05
            if n_hallucinated == 0:
                ci_lower = 0.0
                ci_upper = float(1 - (alpha_ci / 2) ** (1 / n_ood))
            elif n_hallucinated == n_ood:
                ci_lower = float((alpha_ci / 2) ** (1 / n_ood))
                ci_upper = 1.0
            else:
                ci_lower = float(stats.beta.ppf(alpha_ci / 2, n_hallucinated, n_ood - n_hallucinated + 1))
                ci_upper = float(stats.beta.ppf(1 - alpha_ci / 2, n_hallucinated + 1, n_ood - n_hallucinated))

            ood_results[cfg] = {
                "n_ood": n_ood,
                "n_refused": n_refused,
                "n_hallucinated": n_hallucinated,
                "refusal_rate": round(refusal_rate, 4),
                "hallucination_rate": round(hallucination_rate, 4),
                "halluc_ci_lower": round(ci_lower, 4),
                "halluc_ci_upper": round(ci_upper, 4),
            }

    result = {
        "description": "OOD refusal rate with exact binomial CI (Clopper-Pearson)",
        "per_config": ood_results,
    }

    for cfg, d in ood_results.items():
        print(f"  {cfg}: refusal={d['refusal_rate']:.1%}, halluc={d['hallucination_rate']:.1%} "
              f"CI=[{d['halluc_ci_lower']:.1%}, {d['halluc_ci_upper']:.1%}], "
              f"n={d['n_ood']}")
    return result


def test_8_length_bias(paper_val_data: dict | None) -> dict | None:
    """Test 8: Length bias / ROUGE-L inverse correlation."""
    print("\n=== Test 8: Length Bias & Word Count Correlations ===")
    if paper_val_data is None or "length_controlled" not in paper_val_data:
        print("  [SKIP] No paper validation data")
        return None

    lc = paper_val_data["length_controlled"]

    # We have correlations from the paper validation
    # Test if each correlation is significant using Fisher z
    corr_tests = {}
    n = lc["n"]

    for dim, data in lc["spearman_wordcount_vs_dim"].items():
        rho = data["rho"]
        fz = fisher_z_test(rho, n)
        corr_tests[dim] = {
            "spearman_rho": rho,
            "original_p": data["p_value"],
            "fisher_z_test": fz,
        }

    # R-squared interpretation
    r_sq = lc["ols_r_squared"]
    r_sq_ci_lo = max(0, r_sq - 1.96 * math.sqrt(4 * r_sq * (1 - r_sq) ** 2 / (n - 2)))
    r_sq_ci_hi = min(1, r_sq + 1.96 * math.sqrt(4 * r_sq * (1 - r_sq) ** 2 / (n - 2)))

    result = {
        "description": "Length bias: word count vs judge scores, OLS R-squared",
        "n": n,
        "ols_r_squared": r_sq,
        "ols_r_squared_ci": [round(r_sq_ci_lo, 4), round(r_sq_ci_hi, 4)],
        "ols_p_value": lc["ols_p_value"],
        "ranking_preserved": lc["rlm_wins_after_length_control"],
        "correlation_tests": corr_tests,
        "interpretation": (
            f"R-squared={r_sq:.3f} means word count explains only {r_sq*100:.1f}% of score variance. "
            f"RLM strategies win both before and after length control. "
            f"Citation quality has NEGATIVE correlation with length (rho={lc['spearman_wordcount_vs_dim']['citation_quality']['rho']:.3f})."
        ),
    }

    print(f"  OLS R-squared: {r_sq:.4f}, p={lc['ols_p_value']:.4g}")
    print(f"  Ranking preserved after length control: {lc['rlm_wins_after_length_control']}")
    for dim, d in corr_tests.items():
        print(f"  {dim}: rho={d['spearman_rho']:.4f}, p={d['original_p']:.4g}, "
              f"Fisher CI=[{d['fisher_z_test']['ci_r_lower']:.4f}, {d['fisher_z_test']['ci_r_upper']:.4f}]")

    return result


def test_extra_all_configs_vs_baseline(v44_data: dict) -> dict:
    """Extra: All configs vs single_pass baseline with multiple comparison correction."""
    print("\n=== Extra: All Configs vs single_pass Baseline ===")
    qmap = build_v44_question_map(v44_data)
    configs = ["multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]

    # Paired scores against single_pass
    _, base_scores = get_score_array(qmap, "single_pass")
    _, base_pass = get_pass_array(qmap, "single_pass")

    comparisons = {}
    for cfg in configs:
        _, cfg_scores = get_score_array(qmap, cfg)
        _, cfg_pass = get_pass_array(qmap, cfg)
        n = min(len(base_scores), len(cfg_scores))

        # Wilcoxon signed-rank
        w = stats.wilcoxon(cfg_scores[:n], base_scores[:n], alternative='two-sided')
        p_bonf = min(float(w.pvalue) * len(configs), 1.0)

        # Bootstrap CI for pass rate diff
        boot = bootstrap_diff_ci(cfg_pass[:n], base_pass[:n], stat_fn=np.mean)

        # Cohen's h for pass rates
        h = cohens_h(float(np.mean(cfg_pass[:n])), float(np.mean(base_pass[:n])))

        comparisons[cfg] = {
            "mean_diff_correctness": round(float(np.mean(cfg_scores[:n]) - np.mean(base_scores[:n])), 4),
            "wilcoxon_p_raw": float(w.pvalue),
            "wilcoxon_p_bonferroni": round(p_bonf, 6),
            "pass_rate_diff_pp": round(boot["observed_diff"] * 100, 1),
            "pass_rate_ci_pp": [round(boot["ci_lower"] * 100, 1), round(boot["ci_upper"] * 100, 1)],
            "cohens_h": round(h, 4),
            "n": n,
        }

        sig = "*" if p_bonf < 0.05 else ""
        print(f"  {cfg} vs single_pass: diff={comparisons[cfg]['mean_diff_correctness']:+.3f}, "
              f"p_bonf={p_bonf:.4g}{sig}, h={h:.3f}")

    return {
        "description": "All configs vs single_pass baseline, Bonferroni-corrected",
        "baseline": "single_pass",
        "comparisons": comparisons,
    }


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def print_summary_table(results: dict):
    """Print a clean summary table of all statistical tests."""
    print("\n" + "=" * 90)
    print("STATISTICAL SIGNIFICANCE SUMMARY TABLE")
    print("=" * 90)
    print(f"{'Test':<45s} {'Statistic':<18s} {'p-value':<12s} {'Sig?':<6s} {'Effect':<10s}")
    print("-" * 90)

    rows = []

    # Test 1
    if "test_1" in results and results["test_1"]:
        t = results["test_1"]
        rows.append((
            "T1: rlm_10 vs verified_pass (McNemar)",
            f"gap={t['gap_pp']:+.1f}pp",
            f"{t['mcnemar']['p_value']:.4g}",
            "YES" if t["mcnemar"]["p_value"] < 0.05 else "no",
            f"h={t['cohens_h']:.3f}",
        ))
        rows.append((
            "T1: rlm_10 vs verified_pass (Wilcoxon)",
            f"W={t['wilcoxon_scores']['statistic']:.0f}",
            f"{t['wilcoxon_scores']['p_value']:.4g}",
            "YES" if t["wilcoxon_scores"]["p_value"] < 0.05 else "no",
            "",
        ))

    # Test 2
    if "test_2" in results and results["test_2"]:
        t = results["test_2"]
        rows.append((
            "T2: RLM saturation (Friedman)",
            f"chi2={t['friedman']['statistic']:.2f}",
            f"{t['friedman']['p_value']:.4g}",
            "YES" if t["friedman"]["p_value"] < 0.05 else "no",
            "",
        ))
        for pair, d in t["pairwise_bonferroni"].items():
            rows.append((
                f"  {pair} (Wilcoxon+Bonf)",
                f"diff={d['mean_diff']:+.3f}",
                f"{d['wilcoxon_p_bonferroni']:.4g}",
                "YES" if d["wilcoxon_p_bonferroni"] < 0.05 else "no",
                "",
            ))

    # Test 3
    if "test_3" in results and results["test_3"]:
        t = results["test_3"]
        if "crossover_interaction" in t.get("interaction_tests", {}):
            ci = t["interaction_tests"]["crossover_interaction"]
            rows.append((
                "T3: Strategy x corpus interaction",
                f"diff={ci['observed_pp']:+.1f}pp",
                f"CI:[{ci['ci_lower_pp']:.1f},{ci['ci_upper_pp']:.1f}]",
                "YES" if ci["significant"] else "no",
                "",
            ))

    # Test 4
    if "test_4" in results and results["test_4"]:
        t = results["test_4"]
        for s_key, s_data in t["per_size"].items():
            for pair_key, pair_data in s_data["pairwise"].items():
                rows.append((
                    f"T4: {s_key} {pair_key} (MW+Bonf)",
                    f"diff={pair_data['diff_pp']:+.1f}pp",
                    f"{pair_data['mannwhitney_p_bonferroni']:.4g}",
                    "YES" if pair_data["mannwhitney_p_bonferroni"] < 0.05 else "no",
                    "",
                ))

    # Test 5
    if "test_5" in results and results["test_5"]:
        t = results["test_5"]
        d1 = t["minicheck_precision_vs_judge_faithfulness"]
        rows.append((
            "T5: MC_prec vs judge_faith (rho!=0?)",
            f"rho={d1['spearman_rho']:.4f}",
            f"{d1['p_value']:.4g}",
            "YES" if d1["p_value"] < 0.05 else "no",
            f"CI:{d1['bootstrap_ci']}",
        ))
        d2 = t["minicheck_recall_vs_judge_correctness"]
        rows.append((
            "T5: MC_recall vs judge_corr (rho!=0?)",
            f"rho={d2['spearman_rho']:.4f}",
            f"{d2['p_value']:.4g}",
            "YES" if d2["p_value"] < 0.05 else "no",
            f"CI:{d2['bootstrap_ci']}",
        ))

    # Test 6
    if "test_6" in results and results["test_6"]:
        t = results["test_6"]
        rows.append((
            "T6: Kendall's W (chi2 approx)",
            f"W={t['W']:.4f}",
            f"{t['p_value']:.4g}",
            "YES" if t["p_value"] < 0.05 else "no",
            t["interpretation"],
        ))

    # Test 7
    if "test_7" in results and results["test_7"]:
        t = results["test_7"]
        for cfg, d in t["per_config"].items():
            if d["n_ood"] > 0:
                rows.append((
                    f"T7: OOD halluc {cfg}",
                    f"{d['hallucination_rate']:.1%} ({d['n_hallucinated']}/{d['n_ood']})",
                    f"CI:[{d['halluc_ci_lower']:.1%},{d['halluc_ci_upper']:.1%}]",
                    "---",
                    "",
                ))

    # Test 8
    if "test_8" in results and results["test_8"]:
        t = results["test_8"]
        for dim, d in t["correlation_tests"].items():
            sig = "YES" if d["original_p"] < 0.05 else "no"
            rows.append((
                f"T8: wordcount vs {dim}",
                f"rho={d['spearman_rho']:.4f}",
                f"{d['original_p']:.4g}",
                sig,
                f"CI:[{d['fisher_z_test']['ci_r_lower']:.3f},{d['fisher_z_test']['ci_r_upper']:.3f}]",
            ))

    # Print all rows
    for row in rows:
        print(f"{row[0]:<45s} {row[1]:<18s} {row[2]:<12s} {row[3]:<6s} {row[4]:<10s}")

    print("=" * 90)
    print(f"Total tests: {len(rows)}")
    sig_count = sum(1 for r in rows if r[3] == "YES")
    print(f"Significant at alpha=0.05: {sig_count}/{len([r for r in rows if r[3] in ('YES','no')])}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Mentori V4 Statistical Significance Tests")
    print("=" * 50)

    # Load data
    print("\nLoading data files...")
    v44_data = load_json(V44_FILE)
    if v44_data is None:
        print("FATAL: V4-4 generation data not found")
        sys.exit(1)

    v45_results = load_v45_all()
    minicheck_data = load_json(MINICHECK_FILE)
    paper_val_data = load_json(PAPER_VAL_FILE)

    print(f"  V4-4: {len(v44_data['per_question_results'])} results")
    print(f"  V4-5: {len(v45_results)} results")
    print(f"  MiniCheck: {minicheck_data['n_scored'] if minicheck_data else 0} results")
    print(f"  Paper validation: {'loaded' if paper_val_data else 'not found'}")

    results = {}

    # Test 1: Self-correction vs retrieval-grounded
    results["test_1"] = test_1_selfcorrection_vs_rlm(v44_data)

    # Test 2: Compute saturation
    results["test_2"] = test_2_compute_saturation(v44_data)

    # Test 3: Strategy x corpus crossover
    results["test_3"] = test_3_strategy_corpus_crossover(v45_results)

    # Test 4: Noise robustness
    results["test_4"] = test_4_noise_robustness(v45_results)

    # Test 5: Faithfulness construct mismatch
    results["test_5"] = test_5_faithfulness_mismatch(minicheck_data)

    # Test 6: Kendall's W
    results["test_6"] = test_6_kendalls_w(paper_val_data)

    # Test 7: OOD refusal
    results["test_7"] = test_7_ood_refusal(v44_data)

    # Test 8: Length bias
    results["test_8"] = test_8_length_bias(paper_val_data)

    # Extra: all vs baseline
    results["extra_vs_baseline"] = test_extra_all_configs_vs_baseline(v44_data)

    # Summary table
    print_summary_table(results)

    # Save
    output = {
        "experiment": "v4_statistical_tests",
        "n_bootstrap": N_BOOTSTRAP,
        "pass_threshold": PASS_THRESHOLD,
        "rng_seed": 42,
        "data_sources": {
            "v44": str(V44_FILE.name),
            "v45_files": [f.name for f in V45_FILES],
            "minicheck": str(MINICHECK_FILE.name) if minicheck_data else None,
            "paper_validation": str(PAPER_VAL_FILE.name) if paper_val_data else None,
        },
        "tests": results,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
