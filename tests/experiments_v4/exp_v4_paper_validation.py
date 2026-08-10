#!/usr/bin/env python3
"""
V4 Paper Validation Metrics
===========================
Computes evaluation metrics to validate claims against published methodological papers.

Metrics computed:
1. TPR/TNR (Ye/Jain agreeableness)
2. ECE (Tian overconfidence)
3. Bootstrap 95% CIs (Lee correct reporting)
4. Kendall's W (Kulkarni concordance)
5. Length-controlled scores (Dubois verbosity)
6. Misinformation oversight cases (Chen)
7. Concept recall vs judge Spearman (RocketEval)
8. Discrimination comparison (Jing NLI vs LLM)
9. ROUGE-L comparison (Janiak illusion of progress)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import numpy as np
from scipy import stats

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RESULTS_DIR = Path(__file__).resolve().parent / "results_v4"
GT_PATH = Path(__file__).resolve().parents[2] / "datasets" / "ground_truth_v4.json"
OUTPUT_PATH = RESULTS_DIR / "v4_paper_validation.json"

DIMS = ["correctness", "completeness", "faithfulness", "citation_quality"]
CONFIGS = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]


def load_data():
    """Load all required data files."""
    gen = json.load(open(RESULTS_DIR / "v4_4_generation_latest.json"))
    det = json.load(open(RESULTS_DIR / "v4_deterministic_latest.json"))
    mc = json.load(open(RESULTS_DIR / "v4_4_minicheck_latest.json"))
    gt = json.load(open(GT_PATH))

    # Build lookup dicts keyed by (question_id, config)
    det_lookup = {}
    for r in det["per_result"]:
        det_lookup[(r["question_id"], r["config"])] = r

    mc_lookup = {}
    for r in mc["per_result"]:
        mc_lookup[(r["question_id"], r["config"])] = r

    gen_lookup = {}
    gt_lookup = {}
    for r in gen["per_question_results"]:
        gen_lookup[(r["question_id"], r["config"])] = r

    for q in gt["questions"]:
        gt_lookup[q["id"]] = q

    return gen, det, mc, gt, det_lookup, mc_lookup, gen_lookup, gt_lookup


# ============================================================
# 1. TPR/TNR (Ye/Jain agreeableness)
# ============================================================
def compute_tpr_tnr(det_lookup):
    """Compare judge scores vs deterministic scores for agreement analysis."""
    results = {}
    for dim in DIMS:
        tp = fn = tn = fp = 0
        for key, r in det_lookup.items():
            if not r.get("answerable", True):
                continue
            det_score = r.get("deterministic_scores", {}).get(dim)
            judge_score = r.get("judge_scores", {}).get(dim)
            if det_score is None or judge_score is None:
                continue
            actual_pos = det_score >= 3
            judge_pos = judge_score >= 3
            if actual_pos and judge_pos:
                tp += 1
            elif actual_pos and not judge_pos:
                fn += 1
            elif not actual_pos and judge_pos:
                fp += 1
            else:
                tn += 1
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        bacc = (tpr + tnr) / 2
        results[dim] = {
            "tp": tp, "fn": fn, "tn": tn, "fp": fp,
            "tpr": round(tpr, 4), "tnr": round(tnr, 4),
            "balanced_accuracy": round(bacc, 4),
            "n": tp + fn + tn + fp,
        }
    return results


# ============================================================
# 2. ECE (Tian overconfidence)
# ============================================================
def compute_ece(det_lookup, mc_lookup):
    """Expected Calibration Error for judge faithfulness vs MiniCheck precision."""
    bins = defaultdict(list)  # judge_score -> list of minicheck precisions

    for key, r in det_lookup.items():
        if not r.get("answerable", True):
            continue
        judge_faith = r.get("judge_scores", {}).get("faithfulness")
        if judge_faith is None:
            continue
        mc_r = mc_lookup.get(key)
        if mc_r is None:
            continue
        mc_prec = mc_r.get("minicheck", {}).get("precision")
        if mc_prec is None:
            continue
        bins[int(judge_faith)].append(mc_prec)

    bin_details = {}
    total_samples = sum(len(v) for v in bins.values())
    ece = 0.0

    for score in sorted(bins.keys()):
        precs = bins[score]
        n = len(precs)
        avg_accuracy = np.mean(precs)
        confidence = score / 5.0
        gap = abs(avg_accuracy - confidence)
        weight = n / total_samples if total_samples > 0 else 0
        ece += weight * gap
        bin_details[str(score)] = {
            "n": n,
            "avg_minicheck_precision": round(float(avg_accuracy), 4),
            "confidence": round(confidence, 4),
            "gap": round(float(gap), 4),
            "weight": round(weight, 4),
        }

    return {
        "ece": round(float(ece), 4),
        "total_samples": total_samples,
        "bins": bin_details,
    }


# ============================================================
# 3. Bootstrap 95% CIs (Lee correct reporting)
# ============================================================
def compute_bootstrap_cis(det_lookup, n_boot=1000, seed=42):
    """Bootstrap confidence intervals for each config x dimension."""
    rng = np.random.RandomState(seed)
    results = {}

    for config in CONFIGS:
        results[config] = {}
        for dim in DIMS:
            scores = []
            for key, r in det_lookup.items():
                if r["config"] != config or not r.get("answerable", True):
                    continue
                s = r.get("deterministic_scores", {}).get(dim)
                if s is not None:
                    scores.append(s)
            if not scores:
                results[config][dim] = {"mean": None, "ci_lower": None, "ci_upper": None, "n": 0}
                continue
            scores = np.array(scores, dtype=float)
            boot_means = np.array([
                rng.choice(scores, size=len(scores), replace=True).mean()
                for _ in range(n_boot)
            ])
            ci_lower = float(np.percentile(boot_means, 2.5))
            ci_upper = float(np.percentile(boot_means, 97.5))
            results[config][dim] = {
                "mean": round(float(scores.mean()), 4),
                "ci_lower": round(ci_lower, 4),
                "ci_upper": round(ci_upper, 4),
                "ci_width": round(ci_upper - ci_lower, 4),
                "n": len(scores),
            }
    return results


# ============================================================
# 4. Kendall's W (Kulkarni concordance)
# ============================================================
def compute_kendalls_w(det_lookup, mc_lookup):
    """Concordance among deterministic, judge, and MiniCheck rankings of configs."""
    # Compute per-config means for each method
    det_means = defaultdict(list)
    judge_means = defaultdict(list)
    mc_f1_means = defaultdict(list)

    for key, r in det_lookup.items():
        if not r.get("answerable", True):
            continue
        config = r["config"]
        det_corr = r.get("deterministic_scores", {}).get("correctness")
        judge_corr = r.get("judge_scores", {}).get("correctness")
        if det_corr is not None:
            det_means[config].append(det_corr)
        if judge_corr is not None:
            judge_means[config].append(judge_corr)

        mc_r = mc_lookup.get(key)
        if mc_r:
            f1 = mc_r.get("minicheck", {}).get("f1")
            if f1 is not None:
                mc_f1_means[config].append(f1 * 5)  # scale to 0-5

    # Build ranking matrix (methods x configs)
    config_list = [c for c in CONFIGS if c in det_means]
    n_configs = len(config_list)

    method_scores = {}
    method_scores["deterministic"] = [np.mean(det_means[c]) for c in config_list]
    method_scores["judge"] = [np.mean(judge_means[c]) for c in config_list]
    method_scores["minicheck_f1"] = [np.mean(mc_f1_means[c]) if c in mc_f1_means else 0 for c in config_list]

    # Convert to ranks
    n_methods = 3
    rank_matrix = np.zeros((n_methods, n_configs))
    for i, method in enumerate(["deterministic", "judge", "minicheck_f1"]):
        scores = method_scores[method]
        rank_matrix[i] = stats.rankdata(scores)

    # Kendall's W = 12 * S / (k^2 * (n^3 - n))
    k = n_methods  # number of raters
    n = n_configs   # number of items
    rank_sums = rank_matrix.sum(axis=0)
    mean_rank_sum = rank_sums.mean()
    S = np.sum((rank_sums - mean_rank_sum) ** 2)
    W = 12 * S / (k ** 2 * (n ** 3 - n))

    # Build per-config details
    config_details = {}
    for i, c in enumerate(config_list):
        config_details[c] = {
            "det_mean": round(float(method_scores["deterministic"][i]), 4),
            "judge_mean": round(float(method_scores["judge"][i]), 4),
            "mc_f1_mean_scaled": round(float(method_scores["minicheck_f1"][i]), 4),
            "det_rank": float(rank_matrix[0, i]),
            "judge_rank": float(rank_matrix[1, i]),
            "mc_f1_rank": float(rank_matrix[2, i]),
        }

    return {
        "kendalls_w": round(float(W), 4),
        "concordant": W > 0.8,
        "interpretation": "strong" if W > 0.8 else "moderate" if W > 0.6 else "weak",
        "n_configs": n_configs,
        "n_methods": n_methods,
        "config_details": config_details,
    }


# ============================================================
# 5. Length-controlled scores (Dubois verbosity)
# ============================================================
def compute_length_controlled(gen_lookup, det_lookup):
    """Check if RLM advantage persists after controlling for answer length."""
    # Collect word counts and judge scores for answerable questions
    data_by_config = defaultdict(lambda: {"word_counts": [], "scores": {d: [] for d in DIMS}})
    all_wc = []
    all_scores = {d: [] for d in DIMS}
    all_configs_label = []

    for key, r in gen_lookup.items():
        if not r.get("answerable", True):
            continue
        answer = r.get("generation", {}).get("answer", "")
        if not answer:
            continue
        wc = len(answer.split())
        config = r["config"]
        judge = r.get("judge_scores", {})

        data_by_config[config]["word_counts"].append(wc)
        all_wc.append(wc)
        all_configs_label.append(config)

        for dim in DIMS:
            s = judge.get(dim)
            if s is not None:
                data_by_config[config]["scores"][dim].append(s)
                all_scores[dim].append(s)

    # OLS: judge_correctness ~ word_count
    wc_arr = np.array(all_wc, dtype=float)
    corr_arr = np.array(all_scores["correctness"][:len(wc_arr)], dtype=float)

    # Simple OLS
    n = min(len(wc_arr), len(corr_arr))
    wc_arr = wc_arr[:n]
    corr_arr = corr_arr[:n]
    configs_arr = all_configs_label[:n]

    slope, intercept, r_value, p_value, std_err = stats.linregress(wc_arr, corr_arr)
    predicted = intercept + slope * wc_arr
    residuals = corr_arr - predicted

    # Per-config residual means
    config_residuals = defaultdict(list)
    config_original = defaultdict(list)
    for i in range(n):
        config_residuals[configs_arr[i]].append(residuals[i])
        config_original[configs_arr[i]].append(corr_arr[i])

    original_ranking = sorted(CONFIGS, key=lambda c: np.mean(config_original[c]) if config_original[c] else 0, reverse=True)
    residual_ranking = sorted(CONFIGS, key=lambda c: np.mean(config_residuals[c]) if config_residuals[c] else 0, reverse=True)

    # Spearman: word_count vs each dimension
    spearman_results = {}
    for dim in DIMS:
        dim_scores = np.array(all_scores[dim][:len(wc_arr)], dtype=float)
        nn = min(len(wc_arr), len(dim_scores))
        if nn > 2:
            rho, pval = stats.spearmanr(wc_arr[:nn], dim_scores[:nn])
            spearman_results[dim] = {"rho": round(float(rho), 4), "p_value": round(float(pval), 6)}
        else:
            spearman_results[dim] = {"rho": None, "p_value": None}

    # RLM configs
    rlm_configs = {"rlm_5", "rlm_10", "rlm_20"}
    rlm_still_wins_original = original_ranking[0] in rlm_configs
    rlm_still_wins_residual = residual_ranking[0] in rlm_configs

    config_detail = {}
    for c in CONFIGS:
        config_detail[c] = {
            "mean_word_count": round(float(np.mean(data_by_config[c]["word_counts"])), 1) if data_by_config[c]["word_counts"] else None,
            "original_mean_correctness": round(float(np.mean(config_original[c])), 4) if config_original[c] else None,
            "residual_mean_correctness": round(float(np.mean(config_residuals[c])), 4) if config_residuals[c] else None,
        }

    return {
        "ols_slope": round(float(slope), 6),
        "ols_intercept": round(float(intercept), 4),
        "ols_r_squared": round(float(r_value ** 2), 4),
        "ols_p_value": round(float(p_value), 6),
        "original_ranking": original_ranking,
        "residual_ranking": residual_ranking,
        "rlm_wins_original": rlm_still_wins_original,
        "rlm_wins_after_length_control": rlm_still_wins_residual,
        "spearman_wordcount_vs_dim": spearman_results,
        "config_details": config_detail,
        "n": int(n),
    }


# ============================================================
# 6. Misinformation oversight cases (Chen)
# ============================================================
def compute_oversight(det_lookup, mc_lookup):
    """Find cases where judge says faithful but evidence says otherwise."""
    oversight_cases = []
    total_high_faith = 0

    for key, r in det_lookup.items():
        if not r.get("answerable", True):
            continue
        judge_faith = r.get("judge_scores", {}).get("faithfulness")
        if judge_faith is None or judge_faith < 4:
            continue
        total_high_faith += 1

        mc_r = mc_lookup.get(key)
        obj = r.get("objective_metrics", {})
        mc_prec = mc_r.get("minicheck", {}).get("precision") if mc_r else None
        concept_recall = obj.get("concept_recall")

        is_oversight = False
        if mc_prec is not None and mc_prec <= 0.1:
            is_oversight = True
        if concept_recall is not None and concept_recall < 0.3:
            is_oversight = True

        if is_oversight:
            oversight_cases.append({
                "question_id": r["question_id"],
                "config": r["config"],
                "judge_faithfulness": judge_faith,
                "minicheck_precision": mc_prec,
                "concept_recall": concept_recall,
            })

    rate = len(oversight_cases) / total_high_faith if total_high_faith > 0 else 0.0
    return {
        "total_oversight_cases": len(oversight_cases),
        "total_high_faithfulness": total_high_faith,
        "oversight_rate": round(float(rate), 4),
        "examples": oversight_cases[:10],
    }


# ============================================================
# 7. Concept recall vs judge Spearman (RocketEval)
# ============================================================
def compute_concept_recall_spearman(det_lookup):
    """Spearman correlation between concept_recall and judge scores."""
    concept_recalls = []
    judge_correctness = []
    judge_completeness = []

    for key, r in det_lookup.items():
        if not r.get("answerable", True):
            continue
        cr = r.get("objective_metrics", {}).get("concept_recall")
        jc = r.get("judge_scores", {}).get("correctness")
        jcomp = r.get("judge_scores", {}).get("completeness")
        if cr is None:
            continue
        if jc is not None:
            concept_recalls.append(cr)
            judge_correctness.append(jc)
        if jcomp is not None:
            judge_completeness.append(jcomp)

    results = {}
    if len(concept_recalls) > 2:
        rho_corr, p_corr = stats.spearmanr(concept_recalls[:len(judge_correctness)], judge_correctness)
        results["vs_correctness"] = {"rho": round(float(rho_corr), 4), "p_value": round(float(p_corr), 6), "n": len(judge_correctness)}

        rho_comp, p_comp = stats.spearmanr(concept_recalls[:len(judge_completeness)], judge_completeness)
        results["vs_completeness"] = {"rho": round(float(rho_comp), 4), "p_value": round(float(p_comp), 6), "n": len(judge_completeness)}
    else:
        results["vs_correctness"] = {"rho": None, "p_value": None, "n": 0}
        results["vs_completeness"] = {"rho": None, "p_value": None, "n": 0}

    return results


# ============================================================
# 8. Discrimination comparison (Jing NLI vs LLM)
# ============================================================
def compute_discrimination(det_lookup, mc_lookup):
    """Compare std dev of per-config means across methods for faithfulness."""
    judge_means = defaultdict(list)
    det_means = defaultdict(list)
    mc_means = defaultdict(list)

    for key, r in det_lookup.items():
        if not r.get("answerable", True):
            continue
        config = r["config"]
        jf = r.get("judge_scores", {}).get("faithfulness")
        df = r.get("deterministic_scores", {}).get("faithfulness")
        if jf is not None:
            judge_means[config].append(jf)
        if df is not None:
            det_means[config].append(df)

        mc_r = mc_lookup.get(key)
        if mc_r:
            f1 = mc_r.get("minicheck", {}).get("f1")
            if f1 is not None:
                mc_means[config].append(f1 * 5)

    config_list = [c for c in CONFIGS if c in judge_means]

    judge_cfg_means = [np.mean(judge_means[c]) for c in config_list]
    det_cfg_means = [np.mean(det_means[c]) for c in config_list]
    mc_cfg_means = [np.mean(mc_means[c]) for c in config_list if c in mc_means]

    return {
        "judge_faithfulness_std": round(float(np.std(judge_cfg_means)), 4) if judge_cfg_means else None,
        "deterministic_faithfulness_std": round(float(np.std(det_cfg_means)), 4) if det_cfg_means else None,
        "minicheck_f1_scaled_std": round(float(np.std(mc_cfg_means)), 4) if mc_cfg_means else None,
        "judge_config_means": {c: round(float(np.mean(judge_means[c])), 4) for c in config_list},
        "det_config_means": {c: round(float(np.mean(det_means[c])), 4) for c in config_list},
        "mc_config_means": {c: round(float(np.mean(mc_means[c])), 4) for c in config_list if c in mc_means},
        "most_discriminative": max(
            [("judge", np.std(judge_cfg_means) if judge_cfg_means else 0),
             ("deterministic", np.std(det_cfg_means) if det_cfg_means else 0),
             ("minicheck", np.std(mc_cfg_means) if mc_cfg_means else 0)],
            key=lambda x: x[1]
        )[0],
    }


# ============================================================
# 9. ROUGE-L comparison (Janiak illusion of progress)
# ============================================================
def compute_rouge(gen_lookup, gt_lookup):
    """ROUGE-L between generated and expected answers."""
    try:
        from rouge_score import rouge_scorer
    except ImportError:
        return {"skipped": True, "reason": "rouge_score package not available"}

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

    config_scores = defaultdict(list)
    sem_sim_scores = defaultdict(list)

    for key, r in gen_lookup.items():
        if not r.get("answerable", True):
            continue
        qid = r["question_id"]
        config = r["config"]
        answer = r.get("generation", {}).get("answer", "")
        if not answer:
            continue
        gt_q = gt_lookup.get(qid)
        if not gt_q or not gt_q.get("expected_answer"):
            continue

        rouge_result = scorer.score(gt_q["expected_answer"], answer)
        config_scores[config].append(rouge_result["rougeL"].fmeasure)

    # Compute per-config means
    config_means = {c: round(float(np.mean(config_scores[c])), 4) for c in CONFIGS if config_scores[c]}

    # Discrimination = range of means
    if config_means:
        means_list = list(config_means.values())
        rouge_range = max(means_list) - min(means_list)
        rouge_std = float(np.std(means_list))
    else:
        rouge_range = 0
        rouge_std = 0

    return {
        "skipped": False,
        "config_means": config_means,
        "range": round(float(rouge_range), 4),
        "std": round(float(rouge_std), 4),
        "interpretation": "ROUGE-L has limited discrimination" if rouge_range < 0.05 else "ROUGE-L shows some discrimination",
    }


# ============================================================
# Main
# ============================================================
def print_report(results):
    """Print a comprehensive report."""
    print("=" * 80)
    print("V4 PAPER VALIDATION METRICS REPORT")
    print(f"Generated: {results['timestamp']}")
    print("=" * 80)

    # 1. TPR/TNR
    print("\n--- 1. TPR/TNR (Ye/Jain Agreeableness) ---")
    print(f"{'Dimension':<20} {'TPR':>8} {'TNR':>8} {'BAcc':>8} {'N':>6}")
    for dim in DIMS:
        d = results["tpr_tnr"][dim]
        print(f"{dim:<20} {d['tpr']:>8.4f} {d['tnr']:>8.4f} {d['balanced_accuracy']:>8.4f} {d['n']:>6}")

    # 2. ECE
    print("\n--- 2. ECE (Tian Overconfidence) ---")
    ece = results["ece"]
    print(f"ECE = {ece['ece']:.4f} (total samples: {ece['total_samples']})")
    print(f"{'Bin':>4} {'N':>6} {'Avg MC Prec':>12} {'Confidence':>12} {'Gap':>8}")
    for bin_score, d in sorted(ece["bins"].items()):
        print(f"{bin_score:>4} {d['n']:>6} {d['avg_minicheck_precision']:>12.4f} {d['confidence']:>12.4f} {d['gap']:>8.4f}")

    # 3. Bootstrap CIs
    print("\n--- 3. Bootstrap 95% CIs (Lee Correct Reporting) ---")
    print(f"{'Config':<16} {'Dim':<20} {'Mean':>6} {'CI Lower':>9} {'CI Upper':>9} {'Width':>7}")
    for config in CONFIGS:
        for dim in DIMS:
            d = results["bootstrap_cis"][config][dim]
            if d["mean"] is not None:
                print(f"{config:<16} {dim:<20} {d['mean']:>6.2f} {d['ci_lower']:>9.4f} {d['ci_upper']:>9.4f} {d['ci_width']:>7.4f}")

    # 4. Kendall's W
    print("\n--- 4. Kendall's W (Kulkarni Concordance) ---")
    kw = results["kendalls_w"]
    print(f"W = {kw['kendalls_w']:.4f} ({kw['interpretation']}), concordant: {kw['concordant']}")
    print(f"{'Config':<16} {'Det Mean':>9} {'Judge Mean':>11} {'MC F1*5':>9} {'Det Rank':>9} {'Judge Rank':>11} {'MC Rank':>9}")
    for c in CONFIGS:
        if c in kw["config_details"]:
            d = kw["config_details"][c]
            print(f"{c:<16} {d['det_mean']:>9.4f} {d['judge_mean']:>11.4f} {d['mc_f1_mean_scaled']:>9.4f} {d['det_rank']:>9.1f} {d['judge_rank']:>11.1f} {d['mc_f1_rank']:>9.1f}")

    # 5. Length-controlled
    print("\n--- 5. Length-Controlled Scores (Dubois Verbosity) ---")
    lc = results["length_controlled"]
    print(f"OLS: correctness = {lc['ols_intercept']:.4f} + {lc['ols_slope']:.6f} * word_count")
    print(f"R² = {lc['ols_r_squared']:.4f}, p = {lc['ols_p_value']:.6f}, n = {lc['n']}")
    print(f"\nOriginal ranking:  {' > '.join(lc['original_ranking'])}")
    print(f"Residual ranking:  {' > '.join(lc['residual_ranking'])}")
    print(f"RLM wins (original): {lc['rlm_wins_original']}")
    print(f"RLM wins (length-controlled): {lc['rlm_wins_after_length_control']}")
    print(f"\n{'Config':<16} {'Mean WC':>8} {'Orig Corr':>10} {'Resid Corr':>11}")
    for c in CONFIGS:
        d = lc["config_details"][c]
        wc = f"{d['mean_word_count']:.1f}" if d["mean_word_count"] else "N/A"
        oc = f"{d['original_mean_correctness']:.4f}" if d["original_mean_correctness"] else "N/A"
        rc = f"{d['residual_mean_correctness']:.4f}" if d["residual_mean_correctness"] else "N/A"
        print(f"{c:<16} {wc:>8} {oc:>10} {rc:>11}")
    print(f"\nSpearman word_count vs dimensions:")
    for dim, d in lc["spearman_wordcount_vs_dim"].items():
        rho = f"{d['rho']:.4f}" if d["rho"] is not None else "N/A"
        pv = f"{d['p_value']:.6f}" if d["p_value"] is not None else "N/A"
        print(f"  {dim:<20} rho={rho}  p={pv}")

    # 6. Oversight
    print("\n--- 6. Misinformation Oversight (Chen) ---")
    ov = results["oversight"]
    print(f"Oversight cases: {ov['total_oversight_cases']} / {ov['total_high_faithfulness']} (rate: {ov['oversight_rate']:.4f})")
    if ov["examples"]:
        print("Examples:")
        for ex in ov["examples"][:5]:
            mc_p = f"{ex['minicheck_precision']:.4f}" if ex["minicheck_precision"] is not None else "N/A"
            cr = f"{ex['concept_recall']:.4f}" if ex["concept_recall"] is not None else "N/A"
            print(f"  {ex['question_id']:<25} {ex['config']:<16} judge_faith={ex['judge_faithfulness']} mc_prec={mc_p} cr={cr}")

    # 7. Concept recall Spearman
    print("\n--- 7. Concept Recall vs Judge (RocketEval) ---")
    cr = results["concept_recall_spearman"]
    for target, d in cr.items():
        rho = f"{d['rho']:.4f}" if d["rho"] is not None else "N/A"
        pv = f"{d['p_value']:.6f}" if d["p_value"] is not None else "N/A"
        print(f"  concept_recall {target}: rho={rho}, p={pv}, n={d['n']}")

    # 8. Discrimination
    print("\n--- 8. Discrimination Comparison (Jing) ---")
    disc = results["discrimination"]
    print(f"  Judge faithfulness std:       {disc['judge_faithfulness_std']}")
    print(f"  Deterministic faithfulness std: {disc['deterministic_faithfulness_std']}")
    print(f"  MiniCheck F1 (scaled) std:    {disc['minicheck_f1_scaled_std']}")
    print(f"  Most discriminative method:   {disc['most_discriminative']}")

    # 9. ROUGE-L
    print("\n--- 9. ROUGE-L Comparison (Janiak) ---")
    rouge = results["rouge_l"]
    if rouge.get("skipped"):
        print(f"  SKIPPED: {rouge['reason']}")
    else:
        print(f"  Range of config means: {rouge['range']:.4f}")
        print(f"  Std of config means:   {rouge['std']:.4f}")
        print(f"  Interpretation:        {rouge['interpretation']}")
        for c, m in rouge["config_means"].items():
            print(f"    {c:<16} ROUGE-L = {m:.4f}")

    print("\n" + "=" * 80)
    print(f"Results saved to: {OUTPUT_PATH}")
    print("=" * 80)


def main():
    print("Loading data...")
    gen, det, mc, gt, det_lookup, mc_lookup, gen_lookup, gt_lookup = load_data()
    print(f"  Generation results: {len(gen['per_question_results'])}")
    print(f"  Deterministic results: {len(det['per_result'])}")
    print(f"  MiniCheck results: {len(mc['per_result'])}")
    print(f"  Ground truth questions: {len(gt['questions'])}")

    results = {
        "experiment": "v4_paper_validation",
        "timestamp": datetime.now().isoformat(),
    }

    print("\n1. Computing TPR/TNR...")
    results["tpr_tnr"] = compute_tpr_tnr(det_lookup)

    print("2. Computing ECE...")
    results["ece"] = compute_ece(det_lookup, mc_lookup)

    print("3. Computing Bootstrap CIs...")
    results["bootstrap_cis"] = compute_bootstrap_cis(det_lookup)

    print("4. Computing Kendall's W...")
    results["kendalls_w"] = compute_kendalls_w(det_lookup, mc_lookup)

    print("5. Computing Length-Controlled Scores...")
    results["length_controlled"] = compute_length_controlled(gen_lookup, det_lookup)

    print("6. Computing Oversight Cases...")
    results["oversight"] = compute_oversight(det_lookup, mc_lookup)

    print("7. Computing Concept Recall Spearman...")
    results["concept_recall_spearman"] = compute_concept_recall_spearman(det_lookup)

    print("8. Computing Discrimination Comparison...")
    results["discrimination"] = compute_discrimination(det_lookup, mc_lookup)

    print("9. Computing ROUGE-L...")
    results["rouge_l"] = compute_rouge(gen_lookup, gt_lookup)

    # Save (handle numpy types)
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)

    print_report(results)


if __name__ == "__main__":
    main()
