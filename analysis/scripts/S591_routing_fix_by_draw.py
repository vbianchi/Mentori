#!/usr/bin/env python3
"""S591 - the routing fix against the full pipeline and no analyser, per draw: refused out-of-scope questions,
answerable questions passed at judge score 4 and 3, and the question counts, on draw 1 (all 135 questions), on draw 1
of D98's subset, on draws 2 and 3 (D98's subset) and on draws 2 and 3 together; with the paired comparison of the
routing fix and the full pipeline.

WHY. findings/audits/audit_2026-11-06/ablation_fruit.md (R3) counted the routing fix's refusals on draws 2 and 3 by hand
from findings/recompute/fig4_g9_inputs/out_s6_g7_g3/; Valerio (6 November, about 01:00): "make sure all the numbers
are coming from scripts". S480 (scripts/S480_fig4_recount.py) counts draw 1 and, on draws 1 to 3, only the answerable
passes ("draw_counts"). This script adds the rest as a new output, so no committed file moves: it edits neither S480 nor
S472 (S472 refuses a recount whose script_sha256 is not S480's at HEAD, and both scripts' sha256 are in Figure 4's
provenance), it imports S480 for every read and count, and it writes only --out.

WHAT IT READS. Every input through S480: the frozen defaults of S480.FROZEN (records, G3 collect with G9's rows
fig4_g9_inputs, G1 collect, RLM-10 answers, G9 answers, fig3_s6_inputs), each checked against S480.FROZEN_PIN by
S480.frozen_default; the judge rows S480.read_v25 chooses (scripts/judge_rows_v25.py: an answer's key v2.5 row where one
exists): draw 1 on all 135 questions, and its 'draw' cells (S480.draw_cells: D98's 45 questions, draws 1 to 3, S6G7G3's
rows at draws 2 and 3 of a G7 set-up).

WHAT IT COUNTS (S480's rules, its constants): refused, a not-answerable question whose row is "ok" with a
refusal_accuracy of S480.REFUSED_T (3) or more; passed at t, an answerable question "ok" with a correctness of t or
more (S480.PASS_T, 4 and 3). A row "no_answer" counts in n and fails; a row neither scored nor no_answer is left out of
n (as S480.count_draws). Draws 2+3: the sums over the two draws (n answers; questions, the distinct questions).

THE COMPARISON (routing fix minus full pipeline). On the answerable questions at 4 and at 3: S472's draw-1 method
(scripts/S472_fig4_panels.py, statistics()), with S463's own functions (scripts/S463_fig2_ranking.py: shares, pairs,
pair; Rule 2's interval, Rule 3's exact two-sided sign-flip P) and S472's Holm (S472.holm, written out here as holm())
over S472.FAMILY, the five orchestrator set-ups; on draws 2+3 a question's share is its mean over the two draws, as
S463.shares computes it for more than one draw. On the out-of-scope questions each set-up's refusal rate and Rule 2
interval (S463.shares at S463.REFUSAL_T, S463.summarise), as S472 computes them on draw 1. S472 has no paired test of
refusal, so none is computed here and the output says so.

REPRODUCES FIRST (README.md:75-79; a difference exits 2, nothing written):
  (1) the draw-1 counts equal KNOWN: refused 2 (full pipeline), 37 (no analyser), 38 (routing fix) of 39; passed at 4
      65 (full pipeline), 60 (routing fix) of 86;
  (2) every draw-1 count computed here equals S480's own count (S480.count, the "counts" of S480's output) on the same
      rows, and equals the committed findings/recompute/S480_fig4_recount.json, whose "inputs" sha256 must equal the
      files read here;
  (3) the answerable passes per draw equal the committed recount's "draw_counts";
  (4) the draw-1 comparison equals Figure 4's committed Source Data numbers
      (findings/figures_provisional/fig4/figure4_numbers.json): sheet Fig. 4a 'setup' rows at thresholds 4 and 3
      (passed, questions, pass_rate, interval, minus_full, its interval, p_sign_flip, p_holm) and sheet Fig. 4b 'setup'
      rows (questions, refused, refusal_rate, interval), for the three set-ups;
  (5) the draw-1 cells of D98's subset equal the draw-1 rows on all 135 questions.

COMMANDS (uv run only; no model call):
  uv run --frozen python scripts/S591_routing_fix_by_draw.py
      runs the selftest first (quietly; nothing written if it fails), then writes
      findings/recompute/S591_routing_fix_by_draw/routing_fix_by_draw.json and .md (provenance header: script sha256,
      the command, S480's, S463's and judge_rows_v25's sha256, every input's path and sha256, no git HEAD or time).
  uv run --frozen python scripts/S591_routing_fix_by_draw.py selftest
      made-up rows: tabulate and compare by hand, a no_answer in n and failing, an unscored row out of n, Holm, and the
      reproduction gate refusing one changed known value. Last line "selftest: <k> of <k> checks pass".
"""
import argparse
import contextlib
import hashlib
import io
import json
import platform
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import S480_fig4_recount as R  # noqa: E402  (every read and count; S480 imports no figure script)

SCRIPT = "scripts/S591_routing_fix_by_draw.py"
OUT = ROOT / "findings" / "recompute" / "S591_routing_fix_by_draw"
RECOUNT = ROOT / "findings" / "recompute" / "S480_fig4_recount.json"
FIG4_NUMBERS = ROOT / "findings" / "figures_provisional" / "fig4" / "figure5_numbers.json"   # D283: Figure 5 (4 until 6 Nov)
FULL, NO_AN, FIX = "full_orchestrator", "orch_no_analyser", "orch_factual_to_documents"
SHOWN = [FULL, NO_AN, FIX]
LABEL = {FULL: "full pipeline", NO_AN: "no analyser", FIX: "routing fix"}
# S472.FAMILY (scripts/S472_fig4_panels.py: ORCH[1:], Rule 12's zero branch), written out, not imported
FAMILY = ["orch_no_analyser", "orch_no_planner", "orch_no_supervisor", "orch_no_synthesiser",
          "orch_factual_to_documents"]
VIEWS = [("1", "draw 1, all questions", (1,), "all"), ("1s", "draw 1, D98's subset", (1,), "subset"),
         ("2", "draw 2, D98's subset", (2,), "subset"), ("3", "draw 3, D98's subset", (3,), "subset"),
         ("2+3", "draws 2 and 3, D98's subset", (2, 3), "subset")]
# the draw-1 numbers the audit and Figure 4's legend print (ablation_fruit.md; fig4/legend_draft.md)
KNOWN = {(FULL, "refused"): 2, (NO_AN, "refused"): 37, (FIX, "refused"): 38,
         (FULL, "pass_4"): 65, (FIX, "pass_4"): 60, ("n", "not_answerable"): 39, ("n", "answerable"): 86}


class NotReproduced(Exception):
    pass


def sha256_file(p) -> str:
    return R.sha256_file(Path(p))


def cell(a: dict, group: str) -> dict:
    """S480.kind_of as an S463 cell (S472.judge_cell's mapping): scored; no_answer = failed (in n, a fail);
    anything else unscored (out of n)."""
    kind, v = R.kind_of(a or {}, group)
    return {"kind": "scored", "score": v} if kind == "scored" else {"kind": "failed" if kind == "no_answer" else
                                                                     "unscored"}


def build_cells(judged: dict, draw_cells: dict, groups: dict, subset: list, setups) -> dict:
    """{(config, question, draw): cell}: draw 1 of every question from judged (S480.read_v25's draw-1 rows), draws 2
    and 3 from draw_cells (S480.draw_cells). Gate (5): a draw-1 cell of the subset in draw_cells must equal judged."""
    out = {}
    for (c, q), a in judged.items():
        if c in setups:
            out[(c, q, 1)] = cell(a, groups[q])
    for (c, q, d), a in draw_cells.items():
        if c not in setups:
            continue
        x = cell(a, groups[q])
        if d == 1:
            if out.get((c, q, 1)) != x:
                raise NotReproduced(f"{c} {q}: the draw-1 'draw' cell {x} is not the draw-1 row {out.get((c, q, 1))}")
            continue
        if q not in subset:
            raise NotReproduced(f"{c} {q} draw {d}: not a question of D98's subset")
        out[(c, q, d)] = x
    return out


def tabulate(cells: dict, groups: dict, order: list, subset: list, setups) -> dict:
    """{config: {view: counts}}: refused (of the not-answerable answers in n), passed at 4 and 3 (of the answerable
    answers in n), the answers in n and the distinct questions they hold."""
    out = {}
    for c in setups:
        out[c] = {}
        for key, _, draws, qs in VIEWS:
            pool = order if qs == "all" else subset
            row = {}
            for g, metric in (("not_answerable", [("refused", R.REFUSED_T)]),
                              ("answerable", [(f"pass_{t}", t) for t in R.PASS_T])):
                ans = [(q, d) for q in pool if groups[q] == g for d in draws
                       if (c, q, d) in cells and cells[(c, q, d)]["kind"] != "unscored"]
                for name, t in metric:
                    row[name] = sum(1 for q, d in ans if cells[(c, q, d)]["kind"] == "scored"
                                    and cells[(c, q, d)]["score"] >= t)
                row[f"{g}_answers"] = len(ans)
                row[f"{g}_questions"] = len({q for q, _ in ans})
            out[c][key] = row
    return out


def holm(ps: dict) -> dict:
    """S472.holm, written out: the i-th smallest P (from 0) times (m - i), capped at 1, kept from falling below the one
    before it."""
    out, run, order = {}, 0.0, sorted(ps, key=lambda c: (ps[c], c))
    for i, c in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * ps[c]))
        out[c] = run
    return out


def s463():
    import S463_fig2_ranking as m
    return m


@contextlib.contextmanager
def s463_configs(configs):
    """S472.s463_configs: S463's statistics run over its module-level CONFIGS, set for the call and put back."""
    m = s463()
    old = m.CONFIGS
    m.CONFIGS = list(configs)
    try:
        yield m
    finally:
        m.CONFIGS = old


def compare(cells: dict, groups: dict, qids: list, draws, setups) -> dict:
    """S472.statistics' method on the given questions and draws: per threshold 4 and 3 each shown set-up's pass rate and
    Rule 2 interval, and each set-up of FAMILY minus the full pipeline (S463.pairs, S463.pair: mean per-question
    difference, Rule 2 interval, exact two-sided sign-flip P), Holm over FAMILY; on the not-answerable questions each
    shown set-up's refusal rate and Rule 2 interval at S463.REFUSAL_T. No paired test of refusal (S472 has none)."""
    ans = [q for q in qids if groups[q] == "answerable"]
    na = [q for q in qids if groups[q] == "not_answerable"]
    draws = list(draws)
    out = {"pass": {}, "refusal": {}}
    with s463_configs(setups) as m:
        for t in R.PASS_T:
            sh = m.shares(cells, ans, draws, t)
            sm = m.summarise(sh, ans, draws)
            pr = m.pairs(sh, ans)
            vs = {c: dict(m.pair(pr, c, FULL)) for c in setups if c != FULL}
            hp = holm({c: vs[c]["p"] for c in FAMILY})
            out["pass"][str(t)] = {
                "rate": {c: {k: sm[c][k] for k in ("rate", "lo", "hi", "questions_with_share")} for c in SHOWN},
                "fix_minus_full": {"d": vs[FIX]["d"], "lo": vs[FIX]["lo"], "hi": vs[FIX]["hi"],
                                   "p_sign_flip": vs[FIX]["p"], "p_holm": hp[FIX], "questions": vs[FIX]["questions"],
                                   "fix_higher": vs[FIX]["a_higher"], "full_higher": vs[FIX]["b_higher"]},
                "holm_family_p": {c: vs[c]["p"] for c in FAMILY}}
        shr = m.shares(cells, na, draws, m.REFUSAL_T)
        smr = m.summarise(shr, na, draws)
        out["refusal"] = {c: {k: smr[c][k] for k in ("rate", "lo", "hi", "questions_with_share", "zero_bound",
                                                     "full_bound")} for c in SHOWN}
        out["refusal_paired_test"] = ("none: S472 computes no paired test of refusal on draw 1 (statistics(): rate "
                                      "and interval only), so none is computed here")
    return out


def check_known(tab: dict) -> list[str]:
    """Gate (1): draw 1 against KNOWN."""
    probs = []
    for (c, f), v in KNOWN.items():
        got = (tab[FULL]["1"][f"{f}_answers"] if c == "n" else tab[c]["1"][f])
        if got != v:
            probs.append(f"{c} {f}: {got} here, known {v}")
    return probs


def check_recount(tab: dict, counts: dict, label: str) -> list[str]:
    """Gate (2): draw 1 against S480's counts (counts: S480.count's output, or the committed recount's)."""
    probs = []
    pairs = (("refused", "not_answerable_refused_3"), ("pass_4", "answerable_pass_4"), ("pass_3", "answerable_pass_3"),
             ("not_answerable_answers", "not_answerable_judged"), ("answerable_answers", "answerable_judged"))
    for c in SHOWN:
        for mine, theirs in pairs:
            if tab[c]["1"][mine] != counts[c][theirs]:
                probs.append(f"{c} {mine}: {tab[c]['1'][mine]} here, {label} {theirs} {counts[c][theirs]}")
    return probs


def check_draw_counts(tab: dict, draw_counts: dict) -> list[str]:
    """Gate (3): the answerable passes per draw against the committed recount's draw_counts ({c|d|t: [k, n]})."""
    probs = []
    for c in SHOWN:
        for key, d in (("1s", 1), ("2", 2), ("3", 3)):
            for t in R.PASS_T:
                got = [tab[c][key][f"pass_{t}"], tab[c][key]["answerable_answers"]]
                if got != draw_counts[f"{c}|{d}|{t}"]:
                    probs.append(f"{c} draw {d} at {t}: {got} here, draw_counts {draw_counts[f'{c}|{d}|{t}']}")
    return probs


def check_fig4(cmp1: dict, tab: dict, numbers: dict) -> list[str]:
    """Gate (4): the draw-1 comparison against Figure 5's committed Source Data (exact equality)."""
    sh = numbers["sheets"]

    def rows(name):
        s = sh[name]
        return [dict(zip(s["columns"], r)) if isinstance(r, list) else r for r in s["rows"]]
    probs = []
    a = {(r["config"], r["threshold"]): r for r in rows("Fig. 5a") if r.get("row") == "setup"}
    b = {r["config"]: r for r in rows("Fig. 5b") if r.get("row") == "setup"}
    for c in SHOWN:
        for t in R.PASS_T:
            r, mine = a[(c, t)], cmp1["pass"][str(t)]["rate"][c]
            want = {"passed": r["passed"], "questions": r["questions"], "pass_rate": r["pass_rate"],
                    "interval_low": r["interval_low"], "interval_high": r["interval_high"]}
            got = {"passed": tab[c]["1"][f"pass_{t}"], "questions": mine["questions_with_share"],
                   "pass_rate": mine["rate"], "interval_low": mine["lo"], "interval_high": mine["hi"]}
            if c == FIX:
                f = cmp1["pass"][str(t)]["fix_minus_full"]
                want.update(minus_full=r["minus_full"], minus_full_low=r["minus_full_low"],
                            minus_full_high=r["minus_full_high"], p_sign_flip=r["p_sign_flip"], p_holm=r["p_holm"])
                got.update(minus_full=f["d"], minus_full_low=f["lo"], minus_full_high=f["hi"],
                           p_sign_flip=f["p_sign_flip"], p_holm=f["p_holm"])
            for k in want:
                if got[k] != want[k]:
                    probs.append(f"Fig. 5a {c} at {t} {k}: {got[k]} here, Source Data {want[k]}")
        r, mine = b[c], cmp1["refusal"][c]
        for k, g in (("questions", mine["questions_with_share"]), ("refused", tab[c]["1"]["refused"]),
                     ("refusal_rate", mine["rate"]), ("interval_low", mine["lo"]), ("interval_high", mine["hi"])):
            if g != r[k]:
                probs.append(f"Fig. 5b {c} {k}: {g} here, Source Data {r[k]}")
    return probs


def read_all():
    """S480.main's reads on the frozen defaults: (order, groups, judged draw 1, draw cells, subset, S480's counts,
    the inputs {name: path}, the setups judged)."""
    ins = {k: R.frozen_default(k) for k in ("records", "collect", "rlm_collect", "rlm_answers", "g9", "s6_g1")}
    order, groups, types = R.key_groups()
    recs, files = R.read_g3_records(ins["records"], order, types)
    rr, rlm_p, man = R.read_rlm_records(ins["rlm_answers"], order)
    recs.update(rr)
    rg9, g9_files, _ = R.read_g9_records(ins["g9"], order, types, groups)
    recs.update(rg9)
    g3c, g1c = ins["collect"], ins["rlm_collect"]
    g3_sets = R.G3 + R.STRESS
    setups = R.G3 + R.STRESS + [R.RLM]
    j3, side3, _ = R.read_collect(g3c, "G3", g3_sets, groups)
    j1, side1, _ = R.read_collect(g1c, "G1", [R.RLM], groups)
    judged, jrec = R.read_v25(g3c, g1c, groups, j3, j1, ins["s6_g1"], g3_sets)
    counts = R.count(order, groups, recs, judged, setups)
    draws = jrec.get("draws")
    if not draws:
        raise R.Fail("no out_s6_g7_g3 beside the collect: no draws 2 and 3")
    inputs = {f"answers_json:{c}": files[c] for c in R.G3}
    inputs.update({f"answers_json:{c}": g9_files[c] for c in R.STRESS})
    inputs.update({"g3_collect": g3c, "g3_collect_sidecar": side3, "g1_collect": g1c, "g1_collect_sidecar": side1,
                   "rlm_answers_jsonl": rlm_p, "s6_g1_sums": ins["s6_g1"] / "SHA256SUMS"})
    return order, groups, judged, draws["cells"], draws["subset"], counts, inputs, man


def run(order, groups, judged, draw_cells, subset, counts, recount, numbers, setups):
    """The counts, the comparisons and every gate; raises NotReproduced on a difference."""
    cells = build_cells(judged, draw_cells, groups, subset, setups)
    tab = tabulate(cells, groups, order, subset, setups)
    cmp_ = {key: compare(cells, groups, order if qs == "all" else subset, draws, setups)
            for key, _, draws, qs in VIEWS}
    probs = check_known(tab) + check_recount(tab, counts, "S480.count") \
        + check_recount(tab, recount["counts"], "committed recount") \
        + check_draw_counts(tab, recount["draw_counts"]) + check_fig4(cmp_["1"], tab, numbers)
    if probs:
        raise NotReproduced("; ".join(probs))
    return tab, cmp_


def pct(x):
    if x is None:
        return "n/a"
    v = round(100 * x, 1)
    return f"{0.0 if v == 0 else v:.1f}"      # no "-0.0"


def markdown(doc: dict) -> str:
    pv = doc["provenance"]
    L = ["# Routing fix by draw (S591)", "",
         "<!-- provenance", json.dumps(pv, indent=1), "-->", "",
         f"Written by `{pv['script']}` (sha256 `{pv['script_sha256'][:12]}`): `{pv['command']}`. No model call. "
         "Rows: S480's (judge_rows_v25: key v2.5 where S6 judged). Refused: refusal accuracy 3 or more; passed: "
         "correctness 4 (3) or more; a no_answer row counts and fails. Draws 2 and 3 are on D98's subset (13 "
         "out-of-scope, 29 answerable questions); 2+3 sums both draws (n answers).", "",
         "## Counts", "",
         "| set-up | view | refused | out-of-scope n | passed at 4 | passed at 3 | answerable n |",
         "|---|---|---|---|---|---|---|"]
    for c in SHOWN:
        for key, name, _, _ in VIEWS:
            r = doc["counts"][c][key]
            L.append(f"| {LABEL[c]} | {name} | {r['refused']} | {r['not_answerable_answers']} | {r['pass_4']} | "
                     f"{r['pass_3']} | {r['answerable_answers']} |")
    L += ["", "## Routing fix minus full pipeline (answerable, points)", "",
          "Method: S472's draw-1 method (S463.pairs: mean per-question difference, Rule 2 interval, exact two-sided "
          "sign-flip P), Holm over the five orchestrator set-ups; on 2+3 a question's share is its mean over both "
          "draws.", "",
          "| view | threshold | difference | 95% interval | P | Holm P | questions |", "|---|---|---|---|---|---|---|"]
    for key, name, _, _ in VIEWS:
        for t in R.PASS_T:
            f = doc["comparison"][key]["pass"][str(t)]["fix_minus_full"]
            L.append(f"| {name} | {t} | {pct(f['d'])} | {pct(f['lo'])} to {pct(f['hi'])} | {f['p_sign_flip']:.4g} | "
                     f"{f['p_holm']:.4g} | {f['questions']} |")
    L += ["", "## Refusal rate (out of scope, %, Rule 2 interval)", "",
          "No paired test of refusal: S472 computes none on draw 1, so none is computed here.", "",
          "| view | " + " | ".join(LABEL[c] for c in SHOWN) + " |", "|---|" + "---|" * len(SHOWN)]
    for key, name, _, _ in VIEWS:
        L.append(f"| {name} | " + " | ".join(
            f"{pct(r['rate'])} ({pct(r['lo'])} to {pct(r['hi'])})" for r in
            (doc["comparison"][key]["refusal"][c] for c in SHOWN)) + " |")
    L += ["", f"Reproduced first: {doc['reproduced']}", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------
# selftest: made-up rows, counts and comparisons worked by hand
# ---------------------------------------------------------------------------------------------------------------
def fixture():
    """Six set-ups (full, the five of FAMILY), questions a1 to a4 answerable, n1 n2 not answerable; draws 1 to 3."""
    groups = {"a1": "answerable", "a2": "answerable", "a3": "answerable", "a4": "answerable",
              "n1": "not_answerable", "n2": "not_answerable"}
    order = list(groups)
    subset = ["a1", "a2", "n1"]
    ok = lambda g, v: {"status": "ok", "scores": {"correctness" if g == "answerable" else "refusal_accuracy": v}}  # noqa
    setups = [FULL] + FAMILY
    judged, dc = {}, {}
    for c in setups:
        fix = c == FIX
        for q in order:
            g = groups[q]
            v = (3 if fix else 1) if g == "not_answerable" else (5 if q in ("a1", "a2") else 3)
            judged[(c, q)] = ok(g, v)
        judged[(c, "a4")] = {"status": "no_answer"} if fix else judged[(c, "a4")]
        for q in subset:
            for d in (1, 2, 3):
                dc[(c, q, d)] = judged[(c, q)]
        if fix:
            dc[(c, "a1", 2)] = ok("answerable", 2)            # the fix fails a1 on draw 2
            dc[(c, "a2", 3)] = {"status": "error"}            # unscored: out of n
        else:
            dc[(c, "n1", 3)] = ok("not_answerable", 4)        # full refuses n1 on draw 3
    return order, groups, judged, dc, subset, setups


def selftest(quiet=False) -> bool:
    res = []

    def check(name, ok, detail=""):
        res.append(bool(ok))
        if not quiet or not ok:
            print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail)[:300] if detail and not ok else ''}")
    order, groups, judged, dc, subset, setups = fixture()
    cells = build_cells(judged, dc, groups, subset, setups)
    tab = tabulate(cells, groups, order, subset, setups)
    check("draw 1, all: full refuses 0 of 2, passes 2 at 4 and 4 at 3 of 4",
          tab[FULL]["1"] == {"refused": 0, "not_answerable_answers": 2, "not_answerable_questions": 2, "pass_4": 2,
                             "pass_3": 4, "answerable_answers": 4, "answerable_questions": 4}, tab[FULL]["1"])
    check("draw 1, all: the fix refuses 2 of 2; a no_answer counts in n and fails (pass_3 3 of 4)",
          (tab[FIX]["1"]["refused"], tab[FIX]["1"]["pass_3"], tab[FIX]["1"]["answerable_answers"]) == (2, 3, 4),
          tab[FIX]["1"])
    check("draw 2: the fix passes 1 of 2 at 4 (a1 scored 2); draw 3: an unscored row is out of n (1 of 1)",
          (tab[FIX]["2"]["pass_4"], tab[FIX]["2"]["answerable_answers"], tab[FIX]["3"]["pass_4"],
           tab[FIX]["3"]["answerable_answers"]) == (1, 2, 1, 1), (tab[FIX]["2"], tab[FIX]["3"]))
    check("draws 2+3 are the sums: fix 2 of 3 at 4 over 2 questions; full refuses 1 of 2 (n1 on draw 3)",
          (tab[FIX]["2+3"]["pass_4"], tab[FIX]["2+3"]["answerable_answers"], tab[FIX]["2+3"]["answerable_questions"],
           tab[FULL]["2+3"]["refused"], tab[FULL]["2+3"]["not_answerable_answers"]) == (2, 3, 2, 1, 2), tab[FIX]["2+3"])
    c23 = compare(cells, groups, subset, (2, 3), setups)
    f = c23["pass"]["4"]["fix_minus_full"]
    check("2+3 comparison by hand: a1 share 1/2 vs 1, a2 1 vs 1: difference -0.25, sign-flip P 1.0 (one nonzero), "
          "Holm 1.0", (f["d"], f["p_sign_flip"], f["p_holm"], f["questions"], f["full_higher"]) == (-0.25, 1.0, 1.0, 2, 1),
          f)
    check("refusal rate on 2+3: full 0.5 (n1 refused on one of two draws), fix 1.0 with its one-sided bound",
          c23["refusal"][FULL]["rate"] == 0.5 and c23["refusal"][FIX]["rate"] == 1.0
          and c23["refusal"][FIX]["full_bound"] is not None and "none" in c23["refusal_paired_test"])
    check("holm by hand: 0.01, 0.04, 0.03 -> 0.03, 0.06, 0.06",
          holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06})
    bad = dict(dc)
    bad[(FULL, "a1", 1)] = {"status": "ok", "scores": {"correctness": 1}}
    try:
        build_cells(judged, bad, groups, subset, setups)
        msg = ""
    except NotReproduced as e:
        msg = str(e)
    check("gate (5): a draw-1 'draw' cell other than the draw-1 row is refused", "is not the draw-1 row" in msg, msg)
    t = {c: {"1": {"refused": KNOWN.get((c, "refused"), 0), "pass_4": KNOWN.get((c, "pass_4"), 0),
                   "answerable_answers": 86, "not_answerable_answers": 39}} for c in SHOWN}
    ok0 = check_known(t) == []
    t[FIX]["1"]["refused"] = 37
    check("gate (1): the known draw-1 values pass; one changed (routing fix refused 37) is named",
          ok0 and check_known(t) == ["orch_factual_to_documents refused: 37 here, known 38"], check_known(t))
    n = sum(res)
    print(f"selftest: {n} of {len(res)} checks pass")
    return n == len(res)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["selftest"]:
        return 0 if selftest() else 1
    if not selftest(quiet=True):
        print("REFUSED: the selftest fails, nothing written (run `selftest` to see which check)", file=sys.stderr)
        return 1
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(OUT), help="the folder written (routing_fix_by_draw.json and .md)")
    a = ap.parse_args(argv)
    out = Path(a.out).expanduser().resolve()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            order, groups, judged, draw_cells, subset, counts, inputs, man = read_all()
    except (R.Fail, R.FR.FrozenInputError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    recount = json.loads(RECOUNT.read_text())
    numbers = json.loads(FIG4_NUMBERS.read_text())
    try:
        diff = [k for k, p in inputs.items() if (recount["inputs"].get(k) or {}).get("sha256") != sha256_file(p)]
        if diff or set(recount["inputs"]) != set(inputs):
            raise NotReproduced(f"the committed recount was made from other files: {diff or 'other names'}")
        tab, cmp_ = run(order, groups, judged, draw_cells, subset, counts, recount, numbers,
                        [FULL] + FAMILY)
    except NotReproduced as e:
        print(f"REPRODUCTION FAILED, nothing written: {e}", file=sys.stderr)
        return 2
    command = ["uv", "run", "--frozen", "python", SCRIPT]
    doc = {"what": "Refused out-of-scope questions and answerable passes at 4 and 3, per set-up and draw (1 on all "
                   "questions; 1, 2, 3 and 2+3 on D98's subset), and the routing fix minus the full pipeline",
           "provenance": {"script": SCRIPT, "script_sha256": sha256_file(__file__), "command": shlex.join(command),
                          "imports": {"scripts/S480_fig4_recount.py": sha256_file(ROOT / "scripts/S480_fig4_recount.py"),
                                      "scripts/S463_fig2_ranking.py": sha256_file(ROOT / "scripts/S463_fig2_ranking.py"),
                                      "scripts/judge_rows_v25.py": sha256_file(ROOT / "scripts/judge_rows_v25.py")},
                          "frozen_defaults": {k: f"{v[0]}:{v[1]}" for k, v in R.FROZEN.items()},
                          "python": platform.python_version(), "model_calls": 0},
           "inputs": {k: {"path": R.rel(p), "sha256": sha256_file(p)} for k, p in inputs.items()},
           "known_inputs": {n: {"path": R.rel(p), "sha256": sha256_file(p)} for n, p in
                            (("s480_recount", RECOUNT), ("figure4_numbers", FIG4_NUMBERS), ("rlm_manifest", man),
                             ("d98_subset", R.D98_SUBSET))},
           "rules": {"refused_threshold": R.REFUSED_T, "pass_thresholds": list(R.PASS_T),
                     "views": {k: n for k, n, _, _ in VIEWS}, "holm_family": FAMILY,
                     "no_answer": "in n, a fail", "unscored": "out of n"},
           "reproduced": "draw 1 equal to KNOWN (refused 2, 37, 38 of 39; passed at 4 65, 60 of 86), to S480.count "
                         "and the committed S480 recount (inputs sha256 equal), its draw_counts on draws 1 to 3, and "
                         "Figure 5's Source Data (Fig. 5a and 5b setup rows, comparison and Holm P included)",
           "counts": {c: tab[c] for c in SHOWN},
           "comparison": cmp_}
    out.mkdir(parents=True, exist_ok=True)
    (out / "routing_fix_by_draw.json").write_text(json.dumps(doc, indent=1, default=str) + "\n")
    (out / "routing_fix_by_draw.md").write_text(markdown(doc))
    print(doc["reproduced"])
    for c in SHOWN:
        print(f"{LABEL[c]:14s} " + "  ".join(
            f"[{k}] refused {r['refused']}/{r['not_answerable_answers']} pass4 {r['pass_4']}/{r['answerable_answers']}"
            f" pass3 {r['pass_3']}" for k, r in tab[c].items()))
    for key, *_ in VIEWS:
        f4 = cmp_[key]["pass"]["4"]["fix_minus_full"]
        print(f"fix minus full at 4 [{key}]: {pct(f4['d'])} ({pct(f4['lo'])} to {pct(f4['hi'])}), "
              f"P {f4['p_sign_flip']:.4g}, Holm {f4['p_holm']:.4g}, n {f4['questions']}")
    print(f"wrote {R.rel(out / 'routing_fix_by_draw.json')} and .md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
