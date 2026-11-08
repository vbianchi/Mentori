#!/usr/bin/env python3
"""S281 - the corrected score tables every affected figure needs, in one place.

The figure audit of 20 September found eleven panels drawn on the published score state: exp04
(Fig 2a, 2c, 2d, 2e and all of Fig 5), exp06 (Fig 4a to 4c), exp05 (Fig 3e, 3f) and Supp_Fig_ED6.
None of them can be redrawn because the corrected per-config and per-answer tables do not exist:
findings/recompute/ holds the pooled effects and the letter's own cells, not a figure-ready table.

This builds them, by the same alignment the re-judge used. scripts/S21b_analyze.py::load_deposit
keys every judged row (file, row_idx); the arm F rows of S21_rejudge_raw.jsonl replace the
published scores at those keys, and everything else carries over. That is the state the letter
calls the complete-answer re-judge.

Writes, into findings/recompute/:
  S281_exp04_per_answer.csv    528 answerable answers x four dimensions, published and corrected
  S281_exp04_per_config.csv    pass rate, mean correctness, OOD refusal at >= 3, per strategy
  S281_exp06_per_config.csv    the same for the orchestration ablation
  S281_exp06_per_answer.csv    the ablation answer by answer, both halves, for Figure 4c
  S281_exp05_ood.csv           the out-of-domain half of exp05, which S11's tidy file omits
  S281_tables.json             the gates, the row counts and every cell, for provenance

Gated against what is already known, so a silent regression fails the run:
  G1  exp04 corrected pass rates reproduce S77_r2q2_cost.json (79.5, 77.3, 67.0, 88.6, 92.0, 86.4)
  G2  exp04 corrected mean correctness reproduces S21_results.json (3.642)
  G3  exp06 corrected mean correctness reproduces S21_results.json (3.4403)
  G4  the exp04 answerable set is 528 answers over 88 questions and six strategies
  G5  exp05's out-of-domain half is the 3,589 rows S66 gates as the unanswerable set
  G6  every one of the 528 answers is in S30_baseline_scores_full.csv, which carries the
      deterministic signal, MiniCheck and the reference-based baselines for the same answers
  G7  that file's complete-answer judge correctness agrees with the re-judge, answer by answer

    uv run python scripts/S281_corrected_figure_tables.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import S21b_analyze as S21b  # noqa: E402
from exp05_final import rerun_rows  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "findings" / "recompute"
DIMS = ("correctness", "completeness", "faithfulness", "citation_quality")
UNANS = ("refusal_accuracy", "hallucination_avoidance", "explanation_quality")
EXP04, EXP05 = "exp04_generation_latest.json", "exp05_scaling_latest.json"
EXP06 = "exp06_orchestration_ablation_latest.json"
PASS = 3


def corrected_rows():
    """(file, row_idx) -> row with published and corrected scores, for every judged row."""
    dep = S21b.load_deposit()
    raw = [json.loads(l) for l in open(REC / "S21_rejudge_raw.jsonl")]
    fixed = {(r["file"], r["row_idx"]): r["parsed"]
             for r in raw if r.get("arm") == "F" and r.get("parsed") and not r.get("error")}
    out = {}
    for key, row in dep.items():
        new = dict(row)
        new["corrected"] = fixed.get(key, row["published"])
        new["was_rejudged"] = key in fixed
        out[key] = new
    return out, len(fixed)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


def per_config(rows, answerable: bool):
    by = defaultdict(list)
    for r in rows:
        by[r["config"]].append(r)
    out = {}
    for cfg, rs in sorted(by.items()):
        dim = "correctness" if answerable else "refusal_accuracy"
        pub = [r["published"].get(dim) for r in rs]
        cor = [r["corrected"].get(dim) for r in rs]
        out[cfg] = {
            "n": len(rs),
            "pass_pct_published": round(100 * sum(1 for x in pub if (x or 0) >= PASS) / len(rs), 4),
            "pass_pct_corrected": round(100 * sum(1 for x in cor if (x or 0) >= PASS) / len(rs), 4),
            "mean_published": mean(pub),
            "mean_corrected": mean(cor),
            "n_rejudged": sum(1 for r in rs if r["was_rejudged"]),
        }
    return out


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})


def main() -> int:
    dep, n_fixed = corrected_rows()
    print(f"  {len(dep):,} judged rows in the deposit, {n_fixed} replaced by the complete-answer "
          "re-judge")

    def rows_of(fname, answerable):
        return [dict(v, file=k[0], row_idx=k[1]) for k, v in dep.items()
                if k[0] == fname and bool(v["published"]) and
                (("refusal_accuracy" in v["published"]) != answerable)]

    exp04_ans = rows_of(EXP04, True)
    exp04_ood = rows_of(EXP04, False)
    exp06_ans = rows_of(EXP06, True)
    exp06_ood = rows_of(EXP06, False)
    exp05_ood = rows_of(EXP05, False)

    fails = []
    if len(exp04_ans) != 528 or len({r["question_id"] for r in exp04_ans}) != 88 \
            or len({r["config"] for r in exp04_ans}) != 6:                          # G4
        fails.append(f"G4 exp04 answerable is {len(exp04_ans)} rows, "
                     f"{len({r['question_id'] for r in exp04_ans})} questions, "
                     f"{len({r['config'] for r in exp04_ans})} strategies")

    c04, c06 = per_config(exp04_ans, True), per_config(exp06_ans, True)
    r04, r06 = per_config(exp04_ood, False), per_config(exp06_ood, False)
    want04 = {"single_pass": 79.5, "multi_hop": 77.3, "verified_pass": 67.0,
              "rlm_5": 88.6, "rlm_10": 92.0, "rlm_20": 86.4}
    for cfg, want in want04.items():                                                # G1
        got = c04.get(cfg, {}).get("pass_pct_corrected")
        if got is None or abs(round(got, 1) - want) > 0.06:
            fails.append(f"G1 exp04 {cfg} corrected pass rate is {got}, S77 says {want}")
    pooled04 = mean([r["corrected"].get(d) for r in exp04_ans for d in ("correctness",)])
    if pooled04 is None or abs(pooled04 - 3.642) > 0.002:                           # G2
        fails.append(f"G2 exp04 pooled corrected correctness is {pooled04}, S21 says 3.642")
    pooled06 = mean([r["corrected"].get("correctness") for r in exp06_ans])
    if pooled06 is None or abs(pooled06 - 3.4403) > 0.002:                          # G3
        fails.append(f"G3 exp06 pooled corrected correctness is {pooled06}, S21 says 3.4403")
    # 3,589 is the count S66 gates as "the unmatched rows are exactly the unanswerable set";
    # it is not 12 x 6 x 50, because some configurations are short of rows in the deposit.
    if len(exp05_ood) != 3589:                                                       # G5
        fails.append(f"G5 exp05 out-of-domain rows are {len(exp05_ood)}, and S66 gates 3,589")

    for f in fails:
        print("  REFUSED " + f)
    if fails:
        print(f"\nGATES FAILED: {len(fails)}; nothing written")
        return 1
    print(f"  gates passed: exp04 {len(exp04_ans)} answerable and {len(exp04_ood)} out-of-domain, "
          f"exp06 {len(exp06_ans)} and {len(exp06_ood)}, exp05 out-of-domain {len(exp05_ood)}")

    per_answer = []
    for r in sorted(exp04_ans, key=lambda r: (r["config"], r["question_id"])):
        row = {"question_id": r["question_id"], "config": r["config"], "chars": r["chars"],
               "was_rejudged": int(r["was_rejudged"])}
        for d in DIMS:
            row[f"{d}_published"] = r["published"].get(d)
            row[f"{d}_corrected"] = r["corrected"].get(d)
        row["pass_published"] = int((r["published"].get("correctness") or 0) >= PASS)
        row["pass_corrected"] = int((r["corrected"].get("correctness") or 0) >= PASS)
        per_answer.append(row)

    # Old data beside new: the per-answer baseline file carries the deterministic signal in both
    # states, the published and complete-answer judge correctness, MiniCheck and the four
    # reference-based baselines, all on the same 528 answers. Figure 5c and Supp_Fig_ED6 need the
    # deterministic side, so one table carries both rather than two that can drift apart.
    base = {(r["question_id"], r["config"]): r
            for r in csv.DictReader(open(REC / "S30_baseline_scores_full.csv"))}
    carry = ["det_score_correctness", "det_score_correctness_fullsim", "det_score_faithfulness",
             "det_score_faithfulness_fullsim", "det_concept_recall", "det_semantic_similarity",
             "mc_f1", "judge_correctness", "judge_correctness_full", "answer_len_chars"]
    missing = [r for r in per_answer if (r["question_id"], r["config"]) not in base]
    if missing:                                                                      # G6
        fails.append(f"G6 {len(missing)} of {len(per_answer)} answers are not in "
                     "S30_baseline_scores_full.csv")
        print(f"  REFUSED G6 {len(missing)} answers unmatched in the baseline table")
        return 1
    for r in per_answer:
        b = base[(r["question_id"], r["config"])]
        for k in carry:
            r[k] = b.get(k)
        # the judge correctness the baseline file carries must agree with the re-judge, or the two
        # sources disagree about the same answer
        if b.get("judge_correctness_full") and r["correctness_corrected"] is not None:
            if abs(float(b["judge_correctness_full"]) - float(r["correctness_corrected"])) > 0.001:
                fails.append(f"G7 {r['question_id']}/{r['config']}: baseline judge "
                             f"{b['judge_correctness_full']} against re-judge "
                             f"{r['correctness_corrected']}")
    if fails:
        for f in fails[:6]:
            print("  REFUSED " + f)
        print(f"\nGATES FAILED: {len(fails)}; nothing written")
        return 1
    write_csv(REC / "S281_exp04_per_answer.csv", per_answer, list(per_answer[0]))

    def config_rows(ans, ood):
        out = []
        for cfg in sorted(ans):
            out.append({"config": cfg, **{f"ans_{k}": v for k, v in ans[cfg].items()},
                        **{f"ood_{k}": v for k, v in ood.get(cfg, {}).items()}})
        return out

    # exp06 answer by answer, both halves. Figure 4c shows the judge's score on each answer rather
    # than a bar at the mean, which is the editor's item 5, and that needs the per-answer table.
    exp06_rows = []
    tagged = ([("answerable", r) for r in exp06_ans]
              + [("out_of_domain", r) for r in exp06_ood])
    for half, r in sorted(tagged, key=lambda t: (t[1]["config"], t[0], t[1]["question_id"])):
        row = {"question_id": r["question_id"], "config": r["config"],
               "half": half,
               "chars": r["chars"], "was_rejudged": int(r["was_rejudged"])}
        for d in DIMS:
            row[f"{d}_published"] = r["published"].get(d)
            row[f"{d}_corrected"] = r["corrected"].get(d)
        row["pass_published"] = int((r["published"].get("correctness") or 0) >= PASS)
        row["pass_corrected"] = int((r["corrected"].get("correctness") or 0) >= PASS)
        exp06_rows.append(row)
    n_ans6 = sum(1 for r in exp06_rows if r["half"] == "answerable")
    if n_ans6 != len(exp06_ans) or len(exp06_rows) != len(exp06_ans) + len(exp06_ood):   # G8
        print(f"  REFUSED G8 exp06 per-answer table is {len(exp06_rows)} rows, expected "
              f"{len(exp06_ans) + len(exp06_ood)}")
        return 1
    write_csv(REC / "S281_exp06_per_answer.csv", exp06_rows, list(exp06_rows[0]))

    rows04 = config_rows(c04, r04)
    rows06 = config_rows(c06, r06)
    write_csv(REC / "S281_exp04_per_config.csv", rows04, list(rows04[0]))
    write_csv(REC / "S281_exp06_per_config.csv", rows06, list(rows06[0]))

    # exp05's verified_pass rows are the rerun with the verifier working (scripts/exp05_final.py)
    final_vp = rerun_rows()

    def refusal05(r):
        fv = final_vp.get((r.get("index_name"), r["question_id"])) if r["config"] == "verified_pass" else None
        return fv["judge_scores"].get("refusal_accuracy") if fv else r["corrected"].get("refusal_accuracy")
    ood05 = [{"question_id": r["question_id"], "config": r["config"],
              "index": r.get("index_name") or r.get("depth"),
              "refusal_published": r["published"].get("refusal_accuracy"),
              "refusal_corrected": refusal05(r),
              "was_rejudged": int(r["was_rejudged"] or r["config"] == "verified_pass")}
             for r in sorted(exp05_ood, key=lambda r: (r["config"], r["question_id"]))]
    if sum(1 for r in ood05 if r["config"] == "verified_pass") != 600:                  # G6
        raise SystemExit("G6 exp05 verified_pass out-of-domain rows are not the rerun's 600")
    write_csv(REC / "S281_exp05_ood.csv", ood05, list(ood05[0]))

    (REC / "S281_tables.json").write_text(json.dumps(
        {"_provenance": {"script": "scripts/S281_corrected_figure_tables.py",
                         "state": "deposited scores with the complete-answer re-judge substituted",
                         "rejudged_rows_applied": n_fixed,
                         "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
         "exp04": {"answerable_rows": len(exp04_ans), "ood_rows": len(exp04_ood),
                   "per_config": c04, "ood_per_config": r04, "pooled_correctness": pooled04},
         "exp06": {"answerable_rows": len(exp06_ans), "ood_rows": len(exp06_ood),
                   "per_config": c06, "ood_per_config": r06, "pooled_correctness": pooled06},
         "exp05": {"ood_rows": len(exp05_ood)},
         "gates_passed": ["G1 exp04 pass rates reproduce S77", "G2 exp04 mean correctness 3.642",
                          "G3 exp06 mean correctness 3.4403", "G4 exp04 is 528 = 88 x 6",
                          "G5 exp05 out-of-domain rows are 3,589",
                          "G8 exp06 per-answer table carries both halves"]},
        indent=1) + "\n")

    print("\n  exp04, pass rate published -> corrected:")
    for cfg in sorted(c04):
        print(f"    {cfg:14s} {c04[cfg]['pass_pct_published']:6.1f} -> "
              f"{c04[cfg]['pass_pct_corrected']:6.1f}   ({c04[cfg]['n_rejudged']} re-judged)")
    print("  exp06, pass rate published -> corrected:")
    for cfg in sorted(c06):
        print(f"    {cfg:18s} {c06[cfg]['pass_pct_published']:6.1f} -> "
              f"{c06[cfg]['pass_pct_corrected']:6.1f}   ({c06[cfg]['n_rejudged']} re-judged)")
    print(f"\n  wrote five tables and {(REC / 'S281_tables.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
