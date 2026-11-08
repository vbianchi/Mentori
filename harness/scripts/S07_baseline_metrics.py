#!/usr/bin/env python3
"""S07 - Lightweight baseline metrics (ED.2c / R1.5).

Computes four cheap off-the-shelf answer-quality baselines over the 528
answerable generated answers and benchmarks their 6-config rankings against
(a) the triple framework ranking and (b) the judge-pass ranking, then correlates
each baseline per-answer with judge correctness and deterministic concept recall.

Baselines:
  1. ROUGE-L F1          (rouge-score)
  2. METEOR              (nltk, wordnet/punkt)
  3. BERTScore F1        (bert_score, roberta-large, device=mps)
  4. semantic_similarity (bge-m3 cosine, REUSED from master_join column
                          det_semantic_similarity - already a framework component)

Inputs (all trusted, read-only):
  - findings/recompute/master_join.csv          (verified join; 528 answerable rows)
  - <upstream>/publication/results/exp04_generation_latest.json  (generated answer TEXT)
  - <upstream>/publication/data/ground_truth.json                (expected_answer TEXT)

The master_join CSV excludes answer text, so text is re-pulled by
(question_id, config) from the generation JSON and by question_id from
ground_truth.json.

Outputs (findings/recompute/):
  - S07_baseline_scores.csv     per-answer (528 rows) baseline scores + join cols
  - S07_baseline_metrics.json   config means, rankings, rho/tau, correlations, provenance
  - S07_baseline_metrics.md     human-readable summary

Current-key mode, --key v22 (item 15, 9 October 2026; the key moved to v2.3 on 11 October and to v2.4 the same morning, Q50)
-------------------------------------------------------------------------------------------
WHY. The answer key was rebuilt as ground truth v2.2 (frozen 9 October) and corrected to v2.3
(11 October, Q45). ROUGE-L, METEOR and BERTScore are all computed against expected_answer, so
every number above depends on the key and has to be recomputed against the current one. The key
is the judge's, S373_rejudge_v2.AS_V1 (data/ground_truth_v2/ground_truth_v2_4_as_v1.json, written
by S381 --key 2.4): the v1 file format, expected_answer and expected_concepts from the current key
(S373.KEY, data/ground_truth_v2/all_v2_4.json), question and source_files from v1 (on OOD_041 to OOD_050,
source_files from v2.4's evidence, Q56), and the answerable flag from v1 until S381 rebuilds the file for D5 with
v2.4's question_answerable (D5 below).
Reports name the version read from S373.KEY's "version" field. Six questions are dropped (its
"dropped_d7", the same six in v2.2 and v2.3); two of them, CD_015 and SY_010, are among the 88
answerable exp04 questions, so 12 of the 528 rows are skipped and 516 remain. The flag value
stays "v22" and the outputs keep their _v22 names so that downstream paths hold.

D5 (Valerio, 11 October 2026, notes/DECISIONS_2026-10-11.md): the ten false-premise questions
OOD_041 to OOD_050, answer_type "refutation" in S373.KEY, are scored on correctness against their
refutation, which is their expected_answer in S373.AS_V1, and reported as their own group. The
current-key run therefore takes the exp04 rows of master_join.csv whose question S373.AS_V1 flags
answerable, less the dropped questions, not the rows master_join's own flag (v1's) marks answerable.
Each row is labelled with its group: "refutation" for the ten, 60 rows (six configurations each),
and "answerable" for the rest. The run exits unless the rows on which master_join's flag and the
key's differ are exactly the 60 refutation rows, and unless the "answerable" group is master_join's
528 answerable rows less the dropped ones, in the same order (the 516 above). Every score is
computed one group at a time, so the 516 are scored by the same calls as before D5. The CSV gains a
group column; the JSON and Markdown report the 516 where they did and the 60 in a separate
refutation block, never pooled. Until S373.AS_V1 flags the ten answerable (S381's rebuild for D5),
the run exits at the flag check.

HOW. Before anything else the current-key run exits unless S373.AS_V1's source_v<version>_sha256
field (S381's name, from S373.KEY's "version") equals the sha256 of S373.KEY, as S388 checks.
Reproduce before writing: the current-key run then recomputes the v1 numbers from the v1 key and
stops with exit 1 unless ROUGE-L and METEOR equal S07_baseline_scores.csv on all 528 rows exactly
and BERTScore matches it on a fixed 20-row subset to 1e-4 (the tolerance S30 already uses for
the same comparison). Only then does it score the current-key rows: the 516 answerable ones and,
apart, the 60 refutation ones (D5).

    uv run python scripts/S07_baseline_metrics.py                       # v1, unchanged
    uv run python scripts/S07_baseline_metrics.py --key v22 --no-models # ROUGE-L, METEOR only
    uv run python scripts/S07_baseline_metrics.py --key v22 --device cpu            # full
    uv run python scripts/S07_baseline_metrics.py --key v22 --device cpu --gate-only

The current-key outputs never replace a v1 file: S07_baseline_{scores.csv,metrics.json,metrics.md}
gain the suffix _v22 (_v22_nomodel with --no-models), and carry the key path and sha256 (the v1
format file), the source key path, sha256 and version (S373.KEY), the script and the date. Two
things are deliberately left out of these outputs, because their inputs in master_join.csv were
scored against the v1 key: the bge-m3 column (S07 reused the deposited det_semantic_similarity;
its current-key counterpart is bge_sim_cut2000 in S30_baseline_scores_full_v22.csv), and every
comparison with the triple ranking, the judge-pass ranking, judge correctness and concept recall.
They wait for the current-key versions of those columns.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB_DATA, RECOMPUTE, RESULTS, rel   # noqa: E402
import S373_rejudge_v2 as S373   # noqa: E402  (the judge's key: KEY, AS_V1)

MASTER = RECOMPUTE / "master_join.csv"
GEN = RESULTS / "exp04_generation_latest.json"
GT = PUB_DATA / "ground_truth.json"
OUT = RECOMPUTE

CONFIG_ORDER = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]


def shell_date():
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                          capture_output=True, text=True).stdout.strip()


def rank_configs(series_by_config: dict, higher_is_better=True):
    """Return {config: rank} with rank 1 = worst, 6 = best (matches published det_rank)."""
    s = pd.Series(series_by_config)
    ranks = s.rank(method="average", ascending=higher_is_better)
    # ascending=True -> smallest value gets rank 1. We want smallest value = worst = rank 1
    # for higher_is_better, so rank ascending by value gives worst->rank1. Correct.
    return ranks.to_dict()


def spearman_kendall(rank_a: dict, rank_b: dict):
    keys = sorted(set(rank_a) & set(rank_b))
    a = [rank_a[k] for k in keys]
    b = [rank_b[k] for k in keys]
    rho, rho_p = stats.spearmanr(a, b)
    tau, tau_p = stats.kendalltau(a, b)
    return {"spearman_rho": round(float(rho), 4), "spearman_p": round(float(rho_p), 4),
            "kendall_tau": round(float(tau), 4), "kendall_p": round(float(tau_p), 4)}


def main():
    t0 = time.time()
    ts = shell_date()
    print(f"[S07] start {ts}")

    # ---- Load master join, answerable subset ----
    mj = pd.read_csv(MASTER)
    ans = mj[mj["answerable"] == True].copy().reset_index(drop=True)
    assert len(ans) == 528, f"expected 528 answerable rows, got {len(ans)}"

    # ---- Re-pull answer text + expected_answer ----
    gen = json.load(open(GEN))
    gen_text = {(r["question_id"], r["config"]): r["generation"].get("answer", "")
                for r in gen["per_question_results"]}
    gt = json.load(open(GT))
    gt_expected = {q["id"]: q["expected_answer"] for q in gt["questions"]}

    ans["answer_text"] = ans.apply(lambda r: gen_text.get((r["question_id"], r["config"]), ""), axis=1)
    ans["expected_answer"] = ans["question_id"].map(gt_expected)
    n_empty_gen = int((ans["answer_text"].fillna("").str.len() == 0).sum())
    n_missing_gt = int(ans["expected_answer"].isna().sum())
    assert n_empty_gen == 0, f"{n_empty_gen} empty generated answers"
    assert n_missing_gt == 0, f"{n_missing_gt} missing expected answers"
    print(f"[S07] text pulled for {len(ans)} rows (empty gen={n_empty_gen}, missing gt={n_missing_gt})")

    preds = ans["answer_text"].tolist()
    refs = ans["expected_answer"].tolist()

    versions = {"python": sys.version.split()[0], "numpy": np.__version__,
                "pandas": pd.__version__, "scipy": __import__("scipy").__version__}

    # ---- 1. ROUGE-L F1 ----
    from rouge_score import rouge_scorer
    import rouge_score as _rs
    versions["rouge_score"] = getattr(_rs, "__version__", "unknown")
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    rouge_l = [scorer.score(ref, pred)["rougeL"].fmeasure for ref, pred in zip(refs, preds)]
    ans["baseline_rouge_l_f1"] = rouge_l
    print(f"[S07] ROUGE-L done, mean={np.mean(rouge_l):.4f}")

    # ---- 2. METEOR ----
    import nltk
    versions["nltk"] = nltk.__version__
    for pkg in ["wordnet", "punkt", "punkt_tab", "omw-1.4"]:
        try:
            nltk.download(pkg, quiet=True)
        except Exception as e:
            print(f"[S07] nltk download {pkg}: {e}")
    from nltk.translate.meteor_score import meteor_score
    from nltk.tokenize import word_tokenize

    def tok(s):
        try:
            return word_tokenize(s)
        except Exception:
            return s.split()

    meteor = [meteor_score([tok(ref)], tok(pred)) for ref, pred in zip(refs, preds)]
    ans["baseline_meteor"] = meteor
    print(f"[S07] METEOR done, mean={np.mean(meteor):.4f}")

    # ---- 3. BERTScore F1 ----
    bert_model = "roberta-large"
    bert_device = "mps"
    fallback_used = False
    try:
        import bert_score
        from bert_score import score as bert_score_fn
        versions["bert_score"] = getattr(bert_score, "__version__", "unknown")
        import torch
        versions["torch"] = torch.__version__
        if not torch.backends.mps.is_available():
            bert_device = "cpu"
        try:
            P, R, F1 = bert_score_fn(preds, refs, model_type=bert_model, lang="en",
                                     device=bert_device, batch_size=32, verbose=True)
        except Exception as e:
            print(f"[S07] roberta-large failed ({e}); falling back to distilbert-base-uncased")
            fallback_used = True
            bert_model = "distilbert-base-uncased"
            P, R, F1 = bert_score_fn(preds, refs, model_type=bert_model, lang="en",
                                     device=bert_device, batch_size=32, verbose=True)
        bert_f1 = [float(x) for x in F1.tolist()]
    except Exception as e:
        print(f"[S07] BERTScore unavailable entirely: {e}")
        bert_f1 = [float("nan")] * len(preds)
        bert_model = f"UNAVAILABLE ({e})"
    ans["baseline_bertscore_f1"] = bert_f1
    print(f"[S07] BERTScore done (model={bert_model}, device={bert_device}, "
          f"fallback={fallback_used}), mean={np.nanmean(bert_f1):.4f}")

    # ---- 4. bge-m3 semantic similarity (reused) ----
    ans["baseline_semantic_similarity_bge_m3"] = ans["det_semantic_similarity"]

    baselines = {
        "rouge_l_f1": "baseline_rouge_l_f1",
        "meteor": "baseline_meteor",
        "bertscore_f1": "baseline_bertscore_f1",
        "semantic_similarity_bge_m3": "baseline_semantic_similarity_bge_m3",
    }

    # ---- Per-config means ----
    grp = ans.groupby("config")
    config_means = {}
    for name, col in baselines.items():
        config_means[name] = {c: round(float(grp[col].mean()[c]), 6) for c in CONFIG_ORDER}

    # ---- Triple ranking (re-derived from master_join) ----
    # Three prong per-config means: judge_correctness, det_score_correctness, mc_f1.
    # (Verified to reproduce analysis_paper_validation.json kendalls_w.config_details:
    #  judge_mean=judge_correctness, det_mean=det_score_correctness, mc_f1_mean_scaled=mc_f1*5.)
    judge_mean = {c: float(grp["judge_correctness"].mean()[c]) for c in CONFIG_ORDER}
    det_mean = {c: float(grp["det_score_correctness"].mean()[c]) for c in CONFIG_ORDER}
    mc_mean = {c: float(grp["mc_f1"].mean()[c]) for c in CONFIG_ORDER}
    judge_rank = rank_configs(judge_mean)
    det_rank = rank_configs(det_mean)
    mc_rank = rank_configs(mc_mean)
    triple_rank = {c: (judge_rank[c] + det_rank[c] + mc_rank[c]) / 3.0 for c in CONFIG_ORDER}

    # ---- Judge-pass ranking ----
    judge_pass_rate = {c: float(grp["judge_pass"].mean()[c]) for c in CONFIG_ORDER}
    judge_pass_rank = rank_configs(judge_pass_rate)

    # ---- Baseline config rankings + rho/tau vs triple and vs judge-pass ----
    ranking_analysis = {}
    for name, col in baselines.items():
        b_rank = rank_configs(config_means[name])
        ranking_analysis[name] = {
            "config_means": config_means[name],
            "config_rank_1worst_6best": {c: round(b_rank[c], 3) for c in CONFIG_ORDER},
            "config_order_best_to_worst": sorted(CONFIG_ORDER, key=lambda c: -b_rank[c]),
            "vs_triple": spearman_kendall(b_rank, triple_rank),
            "vs_judge_pass": spearman_kendall(b_rank, judge_pass_rank),
        }

    # ---- Answer-level correlations vs judge correctness & concept recall ----
    answer_level = {}
    for name, col in baselines.items():
        sub = ans[[col, "judge_correctness", "det_concept_recall"]].dropna()
        rho_jc, p_jc = stats.spearmanr(sub[col], sub["judge_correctness"])
        rho_cr, p_cr = stats.spearmanr(sub[col], sub["det_concept_recall"])
        answer_level[name] = {
            "n": int(len(sub)),
            "vs_judge_correctness": {"spearman_rho": round(float(rho_jc), 4),
                                     "p_value": round(float(p_jc), 6)},
            "vs_concept_recall": {"spearman_rho": round(float(rho_cr), 4),
                                  "p_value": round(float(p_cr), 6)},
        }

    runtime_s = round(time.time() - t0, 2)

    # ---- Reference / triple ranking context for output ----
    triple_context = {
        "triple_rank_mean_of_prong_ranks_1worst_6best": {c: round(triple_rank[c], 3) for c in CONFIG_ORDER},
        "triple_order_best_to_worst": sorted(CONFIG_ORDER, key=lambda c: -triple_rank[c]),
        "prong_ranks": {
            "judge_correctness": {c: round(judge_rank[c], 1) for c in CONFIG_ORDER},
            "det_score_correctness": {c: round(det_rank[c], 1) for c in CONFIG_ORDER},
            "mc_f1": {c: round(mc_rank[c], 1) for c in CONFIG_ORDER},
        },
        "judge_pass_rate": {c: round(judge_pass_rate[c], 4) for c in CONFIG_ORDER},
        "judge_pass_rank_1worst_6best": {c: round(judge_pass_rank[c], 1) for c in CONFIG_ORDER},
        "judge_pass_order_best_to_worst": sorted(CONFIG_ORDER, key=lambda c: -judge_pass_rank[c]),
    }

    result = {
        "_provenance": {
            "script": "scripts/S07_baseline_metrics.py",
            "generated": ts,
            "wall_clock_runtime_seconds": runtime_s,
            "inputs": [rel(MASTER), rel(GEN), rel(GT)],
            "outputs": [rel(OUT / "S07_baseline_scores.csv"),
                        rel(OUT / "S07_baseline_metrics.json"),
                        rel(OUT / "S07_baseline_metrics.md")],
            "versions": versions,
            "bertscore_model": bert_model,
            "bertscore_device": bert_device,
            "bertscore_fallback_used": fallback_used,
            "n_answers": len(ans),
            "notes": ("ROUGE-L/METEOR/BERTScore computed fresh from generated answer text "
                      "vs expected_answer. semantic_similarity reused from master_join "
                      "det_semantic_similarity (bge-m3 cosine, already a framework component). "
                      "Triple ranking re-derived from master_join as mean of prong ranks "
                      "(judge_correctness, det_score_correctness, mc_f1); verified to reproduce "
                      "analysis_paper_validation.json kendalls_w.config_details."),
        },
        "triple_and_judge_pass_reference": triple_context,
        "baseline_ranking_analysis": ranking_analysis,
        "answer_level_correlations": answer_level,
    }

    (OUT / "S07_baseline_metrics.json").write_text(json.dumps(result, indent=2))

    # ---- Per-answer CSV ----
    csv_cols = ["question_id", "config", "category", "difficulty",
                "baseline_rouge_l_f1", "baseline_meteor", "baseline_bertscore_f1",
                "baseline_semantic_similarity_bge_m3",
                "judge_correctness", "judge_pass", "det_concept_recall", "answer_len_chars"]
    ans[csv_cols].to_csv(OUT / "S07_baseline_scores.csv", index=False)

    # ---- Markdown summary ----
    md = []
    md.append("# S07 - Lightweight baseline metrics (ED.2c / R1.5)\n")
    md.append(f"Generated: {ts}  |  runtime: {runtime_s}s  |  n=528 answerable answers\n")
    md.append(f"BERTScore model: `{bert_model}` (device={bert_device}, fallback={fallback_used})\n")
    md.append("Versions: " + ", ".join(f"{k}={v}" for k, v in versions.items()) + "\n")
    md.append("\n## Triple ranking reference (best -> worst)\n")
    md.append("`" + " > ".join(triple_context["triple_order_best_to_worst"]) + "`\n")
    md.append("Judge-pass ranking (best -> worst): `"
              + " > ".join(triple_context["judge_pass_order_best_to_worst"]) + "`\n")

    md.append("\n## Baseline config means\n")
    md.append("| config | " + " | ".join(baselines) + " |")
    md.append("|---|" + "---|" * len(baselines))
    for c in CONFIG_ORDER:
        row = [c] + [f"{config_means[n][c]:.4f}" for n in baselines]
        md.append("| " + " | ".join(row) + " |")

    md.append("\n## Ranking agreement vs triple and vs judge-pass\n")
    md.append("| baseline | rho_vs_triple | tau_vs_triple | rho_vs_judgepass | tau_vs_judgepass |")
    md.append("|---|---|---|---|---|")
    for n in baselines:
        r = ranking_analysis[n]
        md.append(f"| {n} | {r['vs_triple']['spearman_rho']} | {r['vs_triple']['kendall_tau']} "
                  f"| {r['vs_judge_pass']['spearman_rho']} | {r['vs_judge_pass']['kendall_tau']} |")

    md.append("\n## Baseline config order (best -> worst)\n")
    for n in baselines:
        md.append(f"- **{n}**: " + " > ".join(ranking_analysis[n]["config_order_best_to_worst"]))

    md.append("\n## Answer-level correlations (Spearman, n=528)\n")
    md.append("| baseline | rho vs judge_correctness | rho vs concept_recall |")
    md.append("|---|---|---|")
    for n in baselines:
        a = answer_level[n]
        md.append(f"| {n} | {a['vs_judge_correctness']['spearman_rho']} "
                  f"| {a['vs_concept_recall']['spearman_rho']} |")

    md.append("\n## Interpretation\n")
    rl = ranking_analysis["rouge_l_f1"]["vs_triple"]["spearman_rho"]
    md.append(f"- ROUGE-L config ranking vs triple: rho={rl} "
              f"({'ANTI-correlated (inverts the framework ranking)' if rl < 0 else 'positively correlated'}).")
    md.append("- semantic_similarity (bge-m3) is already a framework component, not an external substitute.")
    (OUT / "S07_baseline_metrics.md").write_text("\n".join(md) + "\n")

    print(f"[S07] DONE in {runtime_s}s")
    print(json.dumps({n: ranking_analysis[n]["vs_triple"] for n in baselines}, indent=1))
    return result


# ────────────────────────────────────────────────────────────────────────────
# current-key mode, --key v22 (item 15, 9 October 2026); main() above is the v1 run, untouched
# ────────────────────────────────────────────────────────────────────────────
GT_V22 = S373.AS_V1    # the judge's key in the v1 format: ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45) (S381 --key 2.4)
V1_SCORES = OUT / "S07_baseline_scores.csv"
N_V1 = 528
N_V22 = 516            # 528 less CD_015 and SY_010 (D7), six configurations each: the group "answerable"
N_REFUTATION = 60      # D5: the ten answer_type "refutation" questions of S373.KEY, six configurations each
GROUPS = ("answerable", "refutation")   # D5: reported apart, never pooled
N_GATE = 20            # model-based reproduction: a fixed, evenly spaced subset of the v1 rows
BERT_TOL = 1e-4        # S30_baseline_input_scope.py docstring: bert_score vs the S07 column


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key_version() -> str:
    """The current key's version as its file states it (S373.KEY "version", "2.4" since 11 October, Q50)."""
    return str(json.loads(S373.KEY.read_text(encoding="utf-8"))["version"])


def require_as_v1_from_key() -> None:
    """S388's check: S373.AS_V1's source_v<version>_sha256 (S381's field for the version in S373.KEY's
    "version") must be the sha256 of S373.KEY. Exits otherwise."""
    kv = key_version()
    src = f"source_v{kv.replace('.', '')}_sha256"
    got = json.loads(S373.AS_V1.read_text(encoding="utf-8")).get(src)
    if got != sha256(S373.KEY):
        sys.exit(f"[S07] FATAL: {S373.AS_V1.name} was built from another key ({src} {str(got)[:12]}), "
                 f"not {S373.KEY.name} v{kv}")


def refutation_ids() -> set:
    """D5: the questions S373.KEY records with answer_type "refutation" (S373.refutation), OOD_041 to
    OOD_050 in v2.4."""
    v2 = {r["id"]: r for r in json.loads(S373.KEY.read_text(encoding="utf-8"))["records"]}
    return {q for q in v2 if S373.refutation(q, v2)}


def select_by_key(mj: pd.DataFrame, key: dict, drop) -> pd.DataFrame:
    """D5: the master_join rows whose question the key flags answerable, less the dropped questions, in
    master_join order, with a column group: "refutation" on refutation_ids(), "answerable" elsewhere.
    master_join's own flag is v1's; exits unless the rows on which it differs from the key's are exactly
    the rows on refutation_ids(), each flagged answerable by the key, and unless they are N_REFUTATION
    rows, each refutation question once in each configuration."""
    ref = refutation_ids()
    kept = mj[~mj["question_id"].isin(set(drop))]
    missing = sorted(set(kept["question_id"]) - set(key))
    assert not missing, f"{len(missing)} questions absent from the key: {missing[:5]}"
    in_key = kept["question_id"].map(lambda q: bool(key[q]["answerable"])).values
    in_mj = (kept["answerable"] == True).values  # noqa: E712
    on_ref = kept["question_id"].isin(ref).values
    differ = sorted(set(kept.loc[in_key != in_mj, "question_id"]))
    if not ((in_key != in_mj) == on_ref).all() or not in_key[on_ref].all():
        sys.exit(f"[S07] FATAL (D5): the rows whose answerable flag differs between master_join and the key are on "
                 f"{differ}, not exactly the {len(ref)} answer_type refutation questions of {S373.KEY.name} "
                 f"({sorted(ref)}), each flagged answerable by the key: rebuild the key with S381 (D5) first")
    pairs = list(zip(kept.loc[on_ref, "question_id"], kept.loc[on_ref, "config"]))
    assert len(pairs) == N_REFUTATION == len(CONFIG_ORDER) * len(ref) and \
        set(pairs) == {(q, c) for q in ref for c in CONFIG_ORDER}, \
        f"expected {N_REFUTATION} rows, each refutation question once per configuration, got {len(pairs)}"
    ans = kept[in_key].copy()
    ans.insert(ans.columns.get_loc("config") + 1, "group",
               np.where(ans["question_id"].isin(ref), "refutation", "answerable"))
    return ans.reset_index(drop=True)


def gate_rows(n: int) -> np.ndarray:
    return np.linspace(0, n - 1, N_GATE).round().astype(int)


def resolve_device(arg: str) -> str:
    if arg != "auto":
        return arg
    import torch
    return "mps" if torch.backends.mps.is_available() else "cpu"


def text_frame(gt_path: Path, drop=(), by_key: bool = False) -> pd.DataFrame:
    """The exp04 rows with answer text and expected answer, joined as main() joins them. Without by_key
    (the v1 reproduction) they are master_join's answerable rows, as main() takes them, and rows of a
    dropped question are removed before the key is consulted. With by_key (the current-key run, D5) they
    are select_by_key's rows, and its "answerable" group must be master_join's 528 answerable rows less
    the dropped ones, in the same order."""
    mj = pd.read_csv(MASTER)
    key = {q["id"]: q for q in json.load(open(gt_path))["questions"]}
    if by_key:
        ans = select_by_key(mj, key, drop)
        before = mj[(mj["answerable"] == True) & ~mj["question_id"].isin(set(drop))]  # noqa: E712
        grp = ans[ans["group"] == "answerable"]
        n_mj = int((mj["answerable"] == True).sum())  # noqa: E712
        assert n_mj == N_V1 and \
            list(zip(grp["question_id"], grp["config"])) == list(zip(before["question_id"], before["config"])), \
            "the answerable group is not master_join's answerable rows less the dropped ones"
    else:
        ans = mj[mj["answerable"] == True].copy()  # noqa: E712
        assert len(ans) == N_V1, f"expected {N_V1} answerable rows, got {len(ans)}"
        ans = ans[~ans["question_id"].isin(set(drop))].reset_index(drop=True)
    gen = json.load(open(GEN))
    gen_text = {(r["question_id"], r["config"]): r["generation"].get("answer", "")
                for r in gen["per_question_results"]}
    missing = sorted(set(ans["question_id"]) - set(key))
    assert not missing, f"{len(missing)} questions absent from {gt_path.name}: {missing[:5]}"
    flag = {q: bool(key[q]["answerable"]) for q in set(ans["question_id"])}
    assert all(flag.values()), "a kept row is not answerable in the key"
    ans["answer_text"] = [gen_text.get((q, c), "") for q, c in zip(ans["question_id"], ans["config"])]
    ans["expected_answer"] = ans["question_id"].map({q: v["expected_answer"] for q, v in key.items()})
    assert (ans["answer_text"].str.len() > 0).all(), "empty generated answer"
    assert ans["expected_answer"].notna().all(), "missing expected answer"
    return ans


def rouge_l(preds, refs, versions) -> np.ndarray:
    from rouge_score import rouge_scorer
    import rouge_score as _rs
    versions["rouge_score"] = getattr(_rs, "__version__", "unknown")
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    return np.array([scorer.score(ref, pred)["rougeL"].fmeasure for ref, pred in zip(refs, preds)])


def meteor(preds, refs, versions) -> np.ndarray:
    import nltk
    versions["nltk"] = nltk.__version__
    for pkg in ["wordnet", "punkt", "punkt_tab", "omw-1.4"]:
        try:
            nltk.download(pkg, quiet=True)
        except Exception as e:
            print(f"[S07] nltk download {pkg}: {e}")
    from nltk.translate.meteor_score import meteor_score
    from nltk.tokenize import word_tokenize

    def tok(s):
        try:
            return word_tokenize(s)
        except Exception:
            return s.split()

    return np.array([meteor_score([tok(ref)], tok(pred)) for ref, pred in zip(refs, preds)])


def bertscore(preds, refs, device, versions) -> np.ndarray:
    """roberta-large F1 with main()'s arguments. No fallback model: a different model would be a
    different metric, so a failure stops the run."""
    import bert_score
    import torch
    from bert_score import score as bert_score_fn
    versions["bert_score"] = getattr(bert_score, "__version__", "unknown")
    versions["torch"] = torch.__version__
    P, R, F1 = bert_score_fn(list(preds), list(refs), model_type="roberta-large", lang="en",
                             device=device, batch_size=32, verbose=False)
    return np.array([float(x) for x in F1.tolist()])


def reproduce_v1(device, with_models: bool, versions) -> dict:
    """Reproduce before writing: the v1 numbers from the v1 key against the committed v1
    artefact. Exits 1 on any mismatch, before a single current-key number is computed."""
    ans = text_frame(GT)
    art = pd.read_csv(V1_SCORES, float_precision="round_trip")
    assert list(zip(art["question_id"], art["config"])) == list(zip(ans["question_id"], ans["config"])), \
        "row order differs from the v1 artefact"
    preds, refs = ans["answer_text"].tolist(), ans["expected_answer"].tolist()
    gate = {"key_v1": rel(GT), "key_v1_sha256": sha256(GT),
            "artefact": rel(V1_SCORES), "artefact_sha256": sha256(V1_SCORES), "n_rows": len(ans)}
    ok = True
    for name, values, col in (("rouge_l_f1", rouge_l(preds, refs, versions), "baseline_rouge_l_f1"),
                              ("meteor", meteor(preds, refs, versions), "baseline_meteor")):
        n_eq = int((values == art[col].values).sum())
        gate[name] = {"n_exactly_equal": n_eq, "of": len(ans),
                      "max_abs_delta": float(np.max(np.abs(values - art[col].values)))}
        ok &= n_eq == len(ans)
        print(f"[S07] gate {name}: {n_eq}/{len(ans)} rows exactly equal to {V1_SCORES.name}")
    if with_models:
        idx = gate_rows(len(ans))
        f1 = bertscore([preds[i] for i in idx], [refs[i] for i in idx], device, versions)
        d = np.abs(f1 - art["baseline_bertscore_f1"].values[idx])
        n_ok = int((d <= BERT_TOL).sum())
        gate["bertscore_f1"] = {"rows": idx.tolist(), "device": device, "tolerance": BERT_TOL,
                                "n_within_tolerance": n_ok, "of": N_GATE,
                                "max_abs_delta": float(d.max())}
        ok &= n_ok == N_GATE
        print(f"[S07] gate bertscore_f1 ({device}): {n_ok}/{N_GATE} rows within {BERT_TOL}, "
              f"max |delta| = {d.max():.2e}")
    gate["passed"] = bool(ok)
    if not ok:
        print("[S07] REPRODUCTION GATE FAILED: the v1 numbers do not reproduce; nothing written")
        sys.exit(1)
    return gate


def config_analysis(ans: pd.DataFrame, baselines: dict) -> dict:
    """Mean, config means, ranks and order of each baseline over the rows given (one group)."""
    grp = ans.groupby("config")
    analysis = {}
    for name, col in baselines.items():
        means = {c: round(float(grp[col].mean()[c]), 6) for c in CONFIG_ORDER}
        r = rank_configs(means)
        analysis[name] = {"mean_all": round(float(ans[col].mean()), 6),
                          "config_means": means,
                          "config_rank_1worst_6best": {c: round(r[c], 3) for c in CONFIG_ORDER},
                          "config_order_best_to_worst": sorted(CONFIG_ORDER, key=lambda c: -r[c])}
    return analysis


def md_tables(analysis: dict, baselines: dict, suffix: str = "") -> list:
    """The config-means table and the config orders of one group, as Markdown lines."""
    md = [f"\n## Baseline config means{suffix}\n",
          "| config | " + " | ".join(baselines) + " |",
          "|---|" + "---|" * len(baselines)]
    for c in CONFIG_ORDER:
        md.append("| " + " | ".join([c] + [f"{analysis[n]['config_means'][c]:.4f}"
                                            for n in baselines]) + " |")
    md.append(f"\n## Baseline config order (best -> worst){suffix}\n")
    for n in baselines:
        md.append(f"- **{n}**: " + " > ".join(analysis[n]["config_order_best_to_worst"]))
    return md


def main_v22(args) -> None:
    t0 = time.time()
    ts = shell_date()
    with_models = not args.no_models
    device = resolve_device(args.device) if with_models else None
    versions = {"python": sys.version.split()[0], "numpy": np.__version__,
                "pandas": pd.__version__, "scipy": __import__("scipy").__version__}
    kv = key_version()
    print(f"[S07] ground truth v{kv} mode ({rel(GT_V22)}), start {ts} (models: {with_models}, device: {device})")
    require_as_v1_from_key()

    gate = reproduce_v1(device, with_models, versions)
    if args.gate_only:
        print("[S07] reproduction gate passed; --gate-only, nothing written")
        return

    key = json.load(open(GT_V22))
    drop = list(key["dropped_d7"])
    mj = pd.read_csv(MASTER)
    in_frame = mj[(mj["answerable"] == True) & mj["question_id"].isin(drop)]  # noqa: E712
    skipped = {q: int(n) for q, n in in_frame.groupby("question_id").size().items()}
    ans = text_frame(GT_V22, drop, by_key=True)
    n_group = {g: int((ans["group"] == g).sum()) for g in GROUPS}
    assert n_group["answerable"] == N_V22 == N_V1 - sum(skipped.values()), \
        f"expected {N_V22} answerable rows after dropping, got {n_group['answerable']}"
    assert n_group["refutation"] == N_REFUTATION and len(ans) == N_V22 + N_REFUTATION, \
        f"expected {N_V22} + {N_REFUTATION} rows, got {n_group}"
    ref_questions = sorted(set(ans.loc[ans["group"] == "refutation", "question_id"]))
    print(f"[S07] v{kv}: {len(ans)} rows {n_group}; skipped {sum(skipped.values())} rows of dropped "
          f"questions {skipped}")

    # one group at a time, so the answerable group is scored by the same calls as before D5
    baselines = {"rouge_l_f1": "baseline_rouge_l_f1", "meteor": "baseline_meteor"}
    if with_models:
        baselines["bertscore_f1"] = "baseline_bertscore_f1"
    parts, analysis = [], {}
    for g in GROUPS:
        sub = ans[ans["group"] == g].copy()
        preds, refs = sub["answer_text"].tolist(), sub["expected_answer"].tolist()
        sub["baseline_rouge_l_f1"] = rouge_l(preds, refs, versions)
        sub["baseline_meteor"] = meteor(preds, refs, versions)
        if with_models:
            sub["baseline_bertscore_f1"] = bertscore(preds, refs, device, versions)
        analysis[g] = config_analysis(sub, baselines)
        parts.append(sub)
    ans = pd.concat(parts).sort_index()     # back to master_join order, which S30 requires row for row

    tag = "_v22" if with_models else "_v22_nomodel"
    f_csv = OUT / f"S07_baseline_scores{tag}.csv"
    f_json = OUT / f"S07_baseline_metrics{tag}.json"
    f_md = OUT / f"S07_baseline_metrics{tag}.md"
    key_sha = sha256(GT_V22)
    runtime_s = round(time.time() - t0, 2)
    result = {
        "_provenance": {
            "script": "scripts/S07_baseline_metrics.py --key v22" + ("" if with_models else " --no-models"),
            "generated": ts,
            "wall_clock_runtime_seconds": runtime_s,
            "key": rel(GT_V22), "key_sha256": key_sha,
            "key_source": rel(S373.KEY), "key_source_sha256": sha256(S373.KEY), "key_version": kv,
            "inputs": [rel(MASTER), rel(GEN), rel(GT_V22)],
            "outputs": [rel(f_csv), rel(f_json), rel(f_md)],
            "versions": versions,
            "bertscore_model": "roberta-large" if with_models else None,
            "bertscore_device": device,
            "bertscore_note": ("bert_score truncates both the answer and the expected answer at "
                               f"512 word pieces; v{kv} expected answers can exceed it, v1 ones "
                               "did not (counts: reference_side in S30_input_scope_v22.json)")
                              if with_models else None,
            "dropped_questions": drop,
            "n_rows_skipped_dropped": sum(skipped.values()),
            "rows_skipped_by_question": skipped,
            "n_answers": n_group["answerable"],     # the n of the tables above, as before D5
            "n_rows_written": len(ans),             # the CSV: both groups
            "n_answers_by_group": n_group,
            "reproduction_gate_v1": gate,
            "not_recomputed": {
                "semantic_similarity_bge_m3": (
                    "S07 v1 reused master_join det_semantic_similarity, scored against the v1 "
                    "key; its current-key counterpart is bge_sim_cut2000 in "
                    "findings/recompute/S30_baseline_scores_full_v22.csv"),
                "triple_ranking_judge_pass_ranking_answer_level_correlations": (
                    "judge_correctness, judge_pass, det_score_correctness, mc_f1 and "
                    "det_concept_recall in master_join.csv were all scored against the v1 key"),
            },
        },
        "baseline_config_analysis": analysis["answerable"],
        "refutation_group": {
            "decision": ("D5 (notes/DECISIONS_2026-10-11.md): the answer_type refutation questions of "
                         f"{rel(S373.KEY)}, scored against their refutation (expected_answer in "
                         f"{rel(GT_V22)}); computed and reported apart from baseline_config_analysis"),
            "questions": ref_questions,
            "n_answers": n_group["refutation"],
            "baseline_config_analysis": analysis["refutation"],
        },
    }
    f_json.write_text(json.dumps(result, indent=2))

    csv_cols = ["question_id", "config", "group", "category", "difficulty", *baselines.values(),
                "answer_len_chars"]
    with open(f_csv, "w") as fh:
        fh.write(f"# generated by {result['_provenance']['script']} on {ts}\n")
        fh.write(f"# key {rel(GT_V22)} sha256 {key_sha} (ground truth v{kv}, {rel(S373.KEY)}); "
                 f"{sum(skipped.values())} rows of "
                 f"dropped questions skipped\n")
        fh.write(f"# group (D5): answerable {n_group['answerable']} rows; refutation {n_group['refutation']} "
                 f"rows on the answer_type refutation questions of {rel(S373.KEY)}\n")
        ans[csv_cols].to_csv(fh, index=False)

    md = [f"# S07 - Lightweight baseline metrics on ground truth v{kv}{'' if with_models else ' (ROUGE-L, METEOR only)'}\n",
          f"Generated: {ts}  |  runtime: {runtime_s}s  |  n={n_group['answerable']} answerable answers "
          f"({sum(skipped.values())} rows of dropped questions skipped)\n",
          f"Key: `{rel(GT_V22)}` sha256 `{key_sha}` (v{kv}, from `{rel(S373.KEY)}`)\n",
          "Reproduction gate (v1 key vs the committed v1 artefact): "
          + "; ".join(f"{n} {gate[n]['n_exactly_equal']}/{gate[n]['of']} exact"
                      for n in ("rouge_l_f1", "meteor"))
          + (f"; bertscore_f1 {gate['bertscore_f1']['n_within_tolerance']}/{N_GATE} within "
             f"{BERT_TOL} ({device})" if with_models else "") + "\n"]
    md += md_tables(analysis["answerable"], baselines)
    md.append(f"\n## The {len(ref_questions)} refutation questions (D5), reported apart\n")
    md.append(f"n={n_group['refutation']} answers on {', '.join(ref_questions)} (answer_type refutation in "
              f"`{rel(S373.KEY)}`), six configurations each, scored against the refutation, their "
              f"expected_answer in the key. Computed separately and not pooled with the "
              f"{n_group['answerable']} above.\n")
    md += md_tables(analysis["refutation"], baselines, ", refutation questions")
    md.append("\n## Not recomputed here\n")
    for k, v in result["_provenance"]["not_recomputed"].items():
        md.append(f"- {k}: {v}")
    f_md.write_text("\n".join(md) + "\n")
    print(f"[S07] wrote {f_csv.name}, {f_json.name}, {f_md.name} in {runtime_s}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--key", choices=["v1", "v22"], default="v1",
                    help="v1 (default) is the original run; v22 scores against the judge's current key "
                         "(S373.AS_V1, ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45))")
    ap.add_argument("--no-models", action="store_true",
                    help="v22 only: ROUGE-L and METEOR, no BERTScore")
    ap.add_argument("--gate-only", action="store_true",
                    help="v22 only: run the v1 reproduction gate and stop")
    ap.add_argument("--device", default="auto",
                    help="v22 only: auto (mps if available, else cpu), cpu, mps or cuda")
    a = ap.parse_args()
    if a.key == "v1":
        if a.no_models or a.gate_only or a.device != "auto":
            ap.error("--no-models, --gate-only and --device apply to --key v22 only")
        main()
    else:
        main_v22(a)
