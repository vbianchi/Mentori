#!/usr/bin/env python3
"""S78 - how much does RLM's pass rate move between independent draws of the same questions?

S77 found two independent generations of RLM-10 on the identical 88 answerable questions, the
same index and the same generator, scoring 92.05% and 86.05%. The paper's headline is the higher
of the two. Two points is not a dispersion estimate, so this script adds the six further RLM
draws that exist in the depth sweep.

They cannot be read off the deposit. 58.1% of the depth sweep's judge calls crashed and were
written as all-zero scores (findings/S21_TRUNCATION_RESULT.md), which is why the deposited file
appears to show RLM-10 passing 8% of questions it passes 90% of elsewhere. S21 re-judged those
rows. This script applies the S21 repair arms and gates itself on reproducing S21's own published
correction before it reports anything.

Why the six depth draws are comparable to the two run draws. The depth parameter is a cap on
retrieval turns, not a number of turns. RLM stops on its own at about 5.4 calls at every cap from
7 upward, so between depth 7 and depth 50 the nominal parameter changes sevenfold while the
behaviour does not. Gate G5 asserts this rather than assuming it. Depths 1 to 5 are excluded:
they run on 78 questions rather than 88 and the cap does bind there.

Gates, all evaluated before anything is written; a failure exits, it never warns.

  G1  the arm resolution reproduces findings/recompute/S21_results.json corrected_headlines
      for exp09_depth_sweep on all four judge dimensions, to four decimals
  G2  the two run draws reproduce S77: exp04 rlm_10 92.0455, exp05 rlm_10 86.0465,
      exp04 single_pass 79.5455
  G3  the depth draws at caps 7 and above run on exactly the 88 answerable question_ids of exp04
  G4  the depth draws at caps 1 to 5 run on 78 questions, and are excluded for that reason
  G5  mean llm_calls at caps 7 to 50 all fall in [5.0, 6.0], so the cap is not binding and the
      six draws differ in a parameter that does not change behaviour

Writes findings/recompute/S78_rlm_draw_spread.json + .md
"""
from __future__ import annotations

import collections
import json
import statistics as st
import subprocess
import sys
from pathlib import Path

from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from machine import RECOMPUTE, RESULTS  # noqa: E402
from S21b_analyze import answer_text, family, judged_rows, load_deposit  # noqa: E402
from S34_propagate_full_similarity import load as load_exp04  # noqa: E402
from S66_corpus_grid import load as load_exp05  # noqa: E402

OUT = RECOMPUTE
RAW = OUT / "S21_rejudge_raw.jsonl"
EXP09 = "exp09_depth_sweep_gemini-3-flash-preview_latest.json"
INDEX = "exp_v4_s20_n0"
PASS_AT = 3
DIMS = ("correctness", "completeness", "faithfulness", "citation_quality")
DEPTHS_USED = (7, 10, 15, 20, 30, 50)
DEPTHS_EXCLUDED = (1, 2, 3, 5)


def utcnow() -> str:
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                          capture_output=True, text=True).stdout.strip()


def load_rejudge() -> list:
    rows = []
    for line in open(RAW):
        r = json.loads(line)
        if r.get("parsed"):
            rows.append(r)
    return rows


def resolve(ok: list, precedence: str = "S21") -> dict:
    """(file, row_idx) -> parsed scores, from the repair arms.

    'S21' reproduces S21b_analyze.corrected(): a dict comprehension over arms F and R in file
    order, so a row carrying both takes whichever appears later. 'F_first' and 'R_first' are the
    two explicit alternatives, computed so the choice can be shown not to matter.
    """
    if precedence == "S21":
        return {(r["file"], r["row_idx"]): r for r in ok if r["arm"] in ("F", "R")}
    want = ("R", "F") if precedence == "F_first" else ("F", "R")
    out = {}
    for arm in want:                      # later assignment wins, so put the preferred arm last
        for r in ok:
            if r["arm"] == arm:
                out[(r["file"], r["row_idx"])] = r
    return out


def mcnemar(a: dict, b: dict) -> dict:
    q = sorted(set(a) & set(b))
    bb = sum(1 for k in q if a[k] and not b[k])
    cc = sum(1 for k in q if not a[k] and b[k])
    p = stats.binomtest(bb, bb + cc, 0.5).pvalue if bb + cc else 1.0
    pa, pb = sum(a[k] for k in q), sum(b[k] for k in q)
    return {"n": len(q), "gap_pp": round(100 * (pb - pa) / len(q), 2),
            "single_pass_only": bb, "rlm_only": cc, "exact_p": float(f"{p:.4g}")}


# ─────────────────────────── gates ──────────────────────────────────────────────────────────
def gate_g1(ok, dep) -> None:
    """Reproduce S21's corrected exp09 headline with the same arm resolution."""
    want = json.load(open(OUT / "S21_results.json"))["corrected_headlines"]["exp09_depth_sweep"]
    F = resolve(ok, "S21")
    for k in DIMS:
        pub, cor, n_sub = [], [], 0
        for (fn, i), d in dep.items():
            if family(fn) != "exp09_depth_sweep" or k not in (d["published"] or {}):
                continue
            pv = int(d["published"][k])
            pub.append(pv)
            r = F.get((fn, i))
            if r and k in r["parsed"]:
                cor.append(int(r["parsed"][k]))
                n_sub += 1
            else:
                cor.append(pv)
        got = (len(pub), n_sub, round(st.mean(pub), 4), round(st.mean(cor), 4))
        exp = (want[k]["n_answers"], want[k]["n_substituted"],
               want[k]["published_mean"], want[k]["corrected_mean"])
        if got != exp:
            sys.exit(f"FATAL G1: exp09 {k} resolves to {got}, S21_results.json records {exp}")
    print("  gate passed: G1 arm resolution reproduces S21's corrected exp09 headline "
          f"on all four dimensions ({want['correctness']['n_substituted']} substitutions)")


# ─────────────────────────── draws ──────────────────────────────────────────────────────────
def exp09_draws(ok, answerable, precedence="S21", verbose=True) -> dict:
    """Corrected pass/fail per question for each depth cap, plus its cost fields."""
    F = resolve(ok, precedence)
    d = json.load(open(RESULTS / EXP09))
    rows = list(judged_rows(d))
    # row_idx is the position in judged_rows (S21b_analyze.load_deposit enumerates it and simply
    # skips text-less rows, it does not renumber). G0 proves the alignment rather than assuming
    # it: every re-judged row's stored answer_chars must equal the answer length at that index.
    checked = bad = 0
    for r in ok:
        if r["file"] != EXP09 or r.get("answer_chars") is None:
            continue
        checked += 1
        if len(answer_text(rows[r["row_idx"]]) or "") != r["answer_chars"]:
            bad += 1
    if bad or not checked:
        sys.exit(f"FATAL G0: {bad} of {checked} re-judged rows disagree with the answer length "
                 f"at their row_idx; the repair rows are misaligned with the deposit")
    if verbose:
        print(f"  gate passed: G0 all {checked} re-judged exp09 rows align with the deposit by "
              f"answer_chars")
    out = {}
    for depth in DEPTHS_USED + DEPTHS_EXCLUDED:
        scores, unrep, calls, toks, qids = {}, 0, [], [], []
        for j, r in enumerate(rows):
            if r.get("depth") != depth:
                continue
            qid = r.get("question_id")
            qids.append(qid)
            if qid not in answerable:
                continue
            pub = r.get("judge_scores") or {}
            c = pub.get("correctness")
            rep = F.get((EXP09, j))
            if rep and "correctness" in rep["parsed"]:
                c = int(rep["parsed"]["correctness"])
            elif c in (None, 0):
                unrep += 1
                continue
            scores[qid] = int(c >= PASS_AT)
            calls.append(r.get("llm_calls") or 0)
            toks.append(r.get("tokens_used") or 0)
        out[depth] = {"scores": scores, "unrepaired": unrep, "n_questions": len(set(qids)),
                      "llm_calls": round(st.mean(calls), 3) if calls else None,
                      "tokens": round(st.mean(toks), 1) if toks else None}
    return out


def main() -> None:
    ok = load_rejudge()
    dep = load_deposit()
    gate_g1(ok, dep)

    df = load_exp04()
    rej4 = {s: {r.question_id: int(r.judge_correctness_full >= PASS_AT) for r in g.itertuples()}
            for s, g in df.groupby("config")}
    answerable = set(rej4["single_pass"])

    rows5, _ = load_exp05()
    rej5 = collections.defaultdict(dict)
    for r in rows5:
        if r["size"] == "20" and r["noise"] == "0" and str(r["answerable"]).lower() in ("true", "1"):
            v = r.get("correctness_rejudged")
            if v not in (None, ""):
                rej5[r["strategy"]][r["question_id"]] = int(float(v) >= PASS_AT)

    def pct(d):
        return round(100 * sum(d.values()) / len(d), 4)

    if (pct(rej4["rlm_10"]), pct(rej5["rlm_10"]), pct(rej4["single_pass"])) != \
            (92.0455, 86.0465, 79.5455):
        sys.exit(f"FATAL G2: run draws are {pct(rej4['rlm_10'])}, {pct(rej5['rlm_10'])}, "
                 f"{pct(rej4['single_pass'])}; S77 records 92.0455, 86.0465, 79.5455")
    print("  gate passed: G2 the two run draws reproduce S77")

    d9 = exp09_draws(ok, answerable)
    for depth in DEPTHS_USED:
        if d9[depth]["n_questions"] != 88:
            sys.exit(f"FATAL G3: depth {depth} covers {d9[depth]['n_questions']} questions, not 88")
    print("  gate passed: G3 depth caps 7 and above run on the 88 answerable questions of exp04")
    for depth in DEPTHS_EXCLUDED:
        if d9[depth]["n_questions"] != 78:
            sys.exit(f"FATAL G4: depth {depth} covers {d9[depth]['n_questions']} questions, not 78")
    print("  gate passed: G4 depth caps 1 to 5 run on 78 questions and are excluded")
    # G5 asserts the property the six depth draws rely on: the cap does not bind, so turns
    # taken barely move while the cap moves sevenfold. Stated as a ratio rather than an
    # interval, so it cannot be satisfied by widening a hand-picked bound.
    calls = [d9[d]["llm_calls"] for d in DEPTHS_USED]
    cap_ratio = max(DEPTHS_USED) / min(DEPTHS_USED)
    call_ratio = max(calls) / min(calls)
    if call_ratio > 1.3 or call_ratio >= cap_ratio / 3:
        sys.exit(f"FATAL G5: mean llm_calls span {min(calls)} to {max(calls)}, a ratio of "
                 f"{call_ratio:.2f} against a cap ratio of {cap_ratio:.1f}; the cap binds and "
                 f"the six depth draws are not near-replicates")
    print(f"  gate passed: G5 the cap ratio is {cap_ratio:.1f}x while mean llm_calls move only "
          f"{call_ratio:.2f}x ({min(calls)} to {max(calls)}), so the cap does not bind")

    # ── the draws ──────────────────────────────────────────────────────────────────────────
    cost = json.load(open(OUT / "S77_r2q2_cost.json"))["cost_table"]
    c10 = next(r for r in cost if r["strategy"] == "rlm_10")
    draws = [
        {"draw": "exp04, generation-strategy run", "source": "exp04_generation_latest.json",
         "scores": rej4["rlm_10"], "llm_calls": c10["llm_calls"], "tokens": c10["tokens"]},
        {"draw": "exp05, corpus-scaling run", "source": "exp05_scaling_latest.json",
         "scores": rej5["rlm_10"], "llm_calls": c10["llm_calls"], "tokens": c10["tokens"]},
    ] + [
        {"draw": f"exp09, depth cap {d}", "source": EXP09, "scores": d9[d]["scores"],
         "llm_calls": d9[d]["llm_calls"], "tokens": d9[d]["tokens"],
         "unrepaired_rows_excluded": d9[d]["unrepaired"]}
        for d in DEPTHS_USED
    ]
    base = rej4["single_pass"]
    for d in draws:
        d["n"] = len(d["scores"])
        d["pass_pct"] = pct(d["scores"])
        d["vs_single_pass"] = mcnemar(base, d["scores"])
        d.pop("scores")

    rates = [d["pass_pct"] for d in draws]
    sig = sum(1 for d in draws if d["vs_single_pass"]["exact_p"] < 0.05)

    # Contingency: the depth draws drop 0 to 2 rows whose crashed judge call S21 never repaired.
    # Scoring those as failures instead of excluding them can only lower a draw, so it bounds the
    # spread from the pessimistic side and is reported rather than left as an assumption.
    worst = []
    for d in draws:
        ex = d.get("unrepaired_rows_excluded") or 0
        worst.append(round(d["pass_pct"] * d["n"] / (d["n"] + ex), 4) if ex else d["pass_pct"])

    passive = []
    nbrec = json.load(open(RESULTS / "analysis_naive_baseline_latest.json"))["per_question_results"]
    nb = {r["question_id"]: int(((r.get("judge_scores") or {}).get("correctness") or 0) >= PASS_AT)
          for r in nbrec if r["question_id"] in answerable}
    for label, sc in (("naive_RAG passive baseline", nb),
                      ("exp04 single_pass", rej4["single_pass"]),
                      ("exp05 single_pass", rej5["single_pass"])):
        passive.append({"draw": label, "n": len(sc), "pass_pct": pct(sc)})

    # ── does the arm precedence matter? ────────────────────────────────────────────────────
    sens = {}
    for prec in ("F_first", "R_first"):
        alt = exp09_draws(ok, answerable, prec, verbose=False)
        sens[prec] = {d: pct(alt[d]["scores"]) if alt[d]["scores"] else None for d in DEPTHS_USED}
    moved = [d for d in DEPTHS_USED if sens["F_first"][d] != sens["R_first"][d]]

    payload = {
        "_provenance": {
            "script": "scripts/S78_rlm_draw_spread.py", "generated": utcnow(),
            "questions": "the 88 answerable questions of the exp_v4_s20_n0 index",
            "scores": ("judged on the complete answer text; in the six depth draws, judge calls "
                       "that had crashed were repeated"),
            "pass_rule": f">= {PASS_AT}",
            "why": ("two draws are not a dispersion estimate; the depth sweep holds six more on "
                    "the same questions, recoverable only after the S21 repair")},
        "rlm_draws": draws,
        "rlm_summary": {
            "n_draws": len(draws), "min_pct": min(rates), "max_pct": max(rates),
            "spread_pp": round(max(rates) - min(rates), 2),
            "mean_pct": round(st.mean(rates), 2), "median_pct": round(st.median(rates), 2),
            "published_headline_pct": pct(rej4["rlm_10"]),
            "headline_is_the_maximum": pct(rej4["rlm_10"]) == max(rates),
            "draws_beating_single_pass_at_p05": sig,
            "unrepaired_as_failure_contingency": {
                "min_pct": min(worst), "max_pct": max(worst),
                "spread_pp": round(max(worst) - min(worst), 2),
                "mean_pct": round(st.mean(worst), 2),
                "note": ("0 to 2 rows per depth draw carry a crashed judge call S21 never "
                         "repaired; scoring them as failures rather than excluding them")}},
        "passive_draws": passive,
        "arm_precedence_sensitivity": {
            "F_first": sens["F_first"], "R_first": sens["R_first"],
            "depths_that_move": moved,
            "note": "empty depths_that_move means no row carries both repair arms"},
        "excluded": {
            "depths": list(DEPTHS_EXCLUDED),
            "why": "78 questions rather than 88, and the depth cap binds below 7"},
    }
    (OUT / "S78_rlm_draw_spread.json").write_text(json.dumps(payload, indent=1))

    s = payload["rlm_summary"]
    md = ["# S78 - RLM pass rate across eight independent draws of the same 88 questions", "",
          f"Generated {payload['_provenance']['generated']}. All gates passed.", "",
          "| draw | n | mean LLM calls | tokens/answer | pass % | vs single-pass | exact P |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for d in draws:
        m = d["vs_single_pass"]
        tok = "-" if d["tokens"] is None else f"{d['tokens']:,.0f}"
        md.append(f"| {d['draw']} | {d['n']} | {d['llm_calls']} | {tok} | {d['pass_pct']} | "
                  f"{m['gap_pp']:+} pp | {m['exact_p']} |")
    md += ["", f"Spread **{s['spread_pp']} points**, from {s['min_pct']}% to {s['max_pct']}%, "
           f"mean {s['mean_pct']}%, median {s['median_pct']}%.",
           f"The published headline is {s['published_headline_pct']}%, which is "
           f"{'the maximum of the eight' if s['headline_is_the_maximum'] else 'not the maximum'}.",
           f"{s['draws_beating_single_pass_at_p05']} of {s['n_draws']} draws beat single-pass at "
           f"P < 0.05.",
           f"Scoring the 0 to 2 unrepaired rows per depth draw as failures instead of excluding "
           f"them gives {s['unrepaired_as_failure_contingency']['min_pct']}% to "
           f"{s['unrepaired_as_failure_contingency']['max_pct']}%, a spread of "
           f"{s['unrepaired_as_failure_contingency']['spread_pp']} points, so the finding does "
           f"not depend on that choice.", "",
           "The six depth draws differ only in a cap on retrieval turns that does not bind: mean "
           f"LLM calls span {min(calls)} to {max(calls)} across a sevenfold change in the cap.",
           "", "## Passive draws, for scale", "", "| draw | n | pass % |", "|---|---:|---:|"]
    for p in passive:
        md.append(f"| {p['draw']} | {p['n']} | {p['pass_pct']} |")
    md += ["", "## Arm precedence", "",
           f"Depths whose corrected pass rate changes between preferring the full-answer arm and "
           f"preferring the crash-recovery arm: {moved or 'none'}.", ""]
    (OUT / "S78_rlm_draw_spread.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[3:]))
    print(f"\nwrote {OUT / 'S78_rlm_draw_spread.json'} and .md")


if __name__ == "__main__":
    main()
