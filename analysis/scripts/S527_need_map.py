#!/usr/bin/env python3
"""S527 - the Discussion's map of needs (D194 Q2): for each need, what the data support, each number with its source.

WHY. D194 asks for a table in the Discussion that maps each need to what the data support, descriptive, tempered by
findings/audits/rerun_story_2026-11-01/attack.md. No script built it (tracked-scripts audit, row 6). The rows are attack.md's
rows that survived it, by its verdict: KEEP and WEAKEN are here, DROP is left out and merged rows are folded into their
target. Two rows are not verdict rows: N13 is attack.md's action A2 and N14 comes from D194 Q4.

WHAT A CELL HOLDS. A sentence, the values it read, each with its file and key, and stands_on, the key, draws and questions
those values rest on, read from the same sources so that a rebuilt source changes them. wording_from says whose sentence it is:
  ATTACK    attack.md's sentence: N1, N2, N6, N8, with N1's and N6's number read from data
  COMPUTED  this script's sentence, picked by the values: N4, N5, N11
  OWN       this script's sentence, built on the reason attack.md gives: N3, N7, N12, M1, M2, M3
No cell recommends an option. N5 and N11 do say which strategy a rule or a signal placed highest, with the rule's result or
the gap and its interval beside it. The Discussion's writer takes the sentence from here and checks it against attack.md.

WHAT IT READS. Only the committed outputs in SOURCES, each hashed into the provenance, and minicheck_filter's HEADING_RULE
for M3's sentence. No scratch script or scratch output.

BLANK CELLS. A cell that needs a blind row has no read function, so no code path can give it a value: `depends_on` names
what it waits for and `blank` says why. T2's generators and the second judge stay closed until S518 runs on Valerio's word
(D195). A cell waiting for something else (G10, G11, K1) is blank the same way, with its own reason. An audit hook refuses
the closed paths (S521.FORBIDDEN_RE, the rerun story's rec_ files and recommend.md, S483, S518), and the test greps this source.

CLAIM GATES. CLAIMS holds each fixed sentence to the values under it: N2, N3, N6, N7, N8, N11 and N12. A sentence its values
no longer carry stops the run and nothing is written, so a result that flips on rebuild cannot keep the old sentence. The
tests are in claim_* below; ALPHA and HALF are their two cut-offs. M1 and M2 have no such gate: they say what a measure is.

REPRODUCE BEFORE WRITING (README.md:75-79). Each row of KNOWN is a value already stated (attack.md, framing.md, compare.md)
and STATED_ON holds the sha256 its source had then. A value that equals the stated one is a gate held, whether or not the
source's bytes have moved since (source_moved says which). A value that differs on an unchanged source fails and nothing is
written. A value that differs on a rebuilt source goes under gates_to_restate in the output, printed, for a person to
restate. With no gate held nothing is written, so a map never reaches the Discussion tied to no known number.

WRITES need_map.json and need_map.md under --out, default findings/recompute/S527_need_map/. No date and no commit, so one
set of inputs gives one set of bytes.

    uv run --frozen python scripts/S527_need_map.py [--out DIR]
    uv run --frozen python scripts/S527_need_map_test.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent
for _p in (str(SCRIPTS), str(REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import fig_repro as FR  # noqa: E402
import figure_names as FN  # noqa: E402
import minicheck_filter as MF  # noqa: E402  (M3 says whether its heading rule is set; the module reads no file at import)
import S526_instrument_swaps as S526  # noqa: E402  (its closed-path check; S526 reads nothing at import)

SCRIPT = "scripts/S527_need_map.py"
COMMAND = "uv run --frozen python scripts/S527_need_map.py"
OUT = REPO / "findings/recompute/S527_need_map"
SOURCES = {"S511": "findings/recompute/S511_g2_budget/results.json",
           "S511 text": "findings/recompute/S511_g2_budget/results.md",        # the one place S511 names the key of its pass table
           "S526": "findings/recompute/S526_instrument_swaps/results.json",
           "ranking": "findings/figures_provisional/fig3_strategies/ranking.json",
           "fig4": f"findings/figures_provisional/fig4/figure{FN.FIG_PIPELINE}_numbers.json",
           "fig6": "findings/figures_provisional/fig6/fig6_numbers.json",
           "G4": "findings/recompute/G4_fig3c_d185/verdicts.json"}
CLOSED_MORE = re.compile(r"S483|S518")
BLIND = "D195: closed until S518 runs on Valerio's word"
MARK = 4                 # the judge's pass mark every cell reads, as attack.md's rows do
REFUSAL_MARK = 3         # the refusal score Figure 3's refusal keys are counted at
ALPHA = 0.05             # a claim of no clear change needs P at or above this
HALF = 0.5               # "much of" and "mostly" need at least this share
ATTACK, COMPUTED, OWN = ("attack.md's sentence", "this script's, picked by the values", "this script's, on attack.md's reason")
STRATEGY = dict(zip(("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"), FN.STRATEGIES))


class Refused(Exception):
    """A closed path, or a blank cell that holds a value."""


class GateFail(Exception):
    """A stated value did not reproduce on the file it was stated on: nothing written."""


def closed(path) -> bool:
    text = os.fsdecode(path) if isinstance(path, (bytes, os.PathLike)) else str(path)
    return S526.closed(text) or bool(CLOSED_MORE.search(text))


_guard_on = False


def install_guard() -> None:
    global _guard_on
    if _guard_on:
        return

    def hook(event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)) and closed(args[0]):
            raise Refused(f"guard: {os.fsdecode(args[0])} is closed to this script")

    sys.addaudithook(hook)
    _guard_on = True


class Sources:
    """The committed outputs, each read once, with its sha256."""

    def __init__(self, repo: Path = REPO, sources: dict = SOURCES):
        self.repo, self.paths, self.docs, self.sha = repo, sources, {}, {}

    def __getitem__(self, name):
        if name not in self.docs:
            p = self.repo / self.paths[name]
            text = p.read_text(encoding="utf-8")
            self.docs[name] = json.loads(text) if p.suffix == ".json" else text
            self.sha[self.paths[name]] = FR.sha256_file(p)
        return self.docs[name]


def v(s: Sources, name: str, *key, scale=1.0, nd=1, label=None, unit="%"):
    """One value: the number at key in source name, with its file and key."""
    x = s[name]
    for k in key:
        x = x[k]
    return {"label": label or " ".join(str(k) for k in key), "value": round(x * scale, nd) if isinstance(x, float) else x,
            "unit": unit, "source": s.paths[name], "key": " / ".join(str(k) for k in key)}


def rate(s, group, arm, label):
    return v(s, "S511", "pass", str(MARK), group, arm, "rate", scale=100, label=label)


def chi(s, group, which, label):
    return v(s, "S526", "swaps", "rlm_G1_vs_G6_cap10_d181", group, which, label=label)


def found(pattern: str, text: str, where: str) -> tuple:
    """The groups of pattern in text. A source that stops stating this refuses, so no cell prints a statement it cannot read."""
    m = re.search(pattern, text)
    if m is None:
        raise Refused(f"{where} no longer matches {pattern}")
    return m.groups()


def draws(keys) -> str:
    """The draws a source lists: one draw, a first and last draw, or a list when they are not in a run."""
    ds = sorted(int(k) for k in keys)
    if len(ds) == 1:
        return f"draw {ds[0]}"
    return f"draws {ds[0]} to {ds[-1]}" if ds == list(range(ds[0], ds[-1] + 1)) else "draws " + ", ".join(map(str, ds))


def one_key(s, prefix: str) -> str:
    """The one S526 row whose name starts with prefix; its name is where S526 states the row's draw or question set."""
    hits = [k for k in s["S526"]["swaps"] if k.startswith(prefix)]
    if len(hits) != 1:
        raise Refused(f"{SOURCES['S526']}: {len(hits)} rows start with {prefix!r}")
    return hits[0]


def signal_swap(s, group: str) -> str:
    return one_key(s, f"signal swap: judge pass at {MARK} to concept recall D181, {group}")


def papers_key(s) -> str:
    return one_key(s, "MiniCheck key to papers precision, as stored")


def source_lines_key(s) -> str:
    return one_key(s, "MiniCheck papers precision, source lists kept to dropped")


def judge_basis(s, group: str) -> str:
    """S511's pass table: the key its results.md names, the draws and questions its row for group holds."""
    key, = found(r"plain call \(a\), (key v[\d.]+)", s["S511 text"], SOURCES["S511 text"])
    row = s["S511"]["pass"][str(MARK)][group]["rlm_10"]
    return f"judge on {key}, {draws(row['per_draw'])}, {row['questions']} questions"


def concept_basis(s, group: str) -> str:
    sw = s["S526"]["swaps"]
    key, = found(r"(?m)^concept v[\d.]+ loose to (v[\d.]+) D181, all", "\n".join(sw), SOURCES["S526"])
    return f"concept recall on key {key}, {draws(sw['noise_concept_d181_contrast']['per_draw'])}, {sw[signal_swap(s, group)]['n_q']} questions"


def interval_level(s) -> str:
    """The level of S526's intervals, from the field that holds them."""
    return found(r"interval_(\d+)", " ".join(next(iter(s["S526"]["thesis"].values()))), SOURCES["S526"])[0]


def ranking_basis(s) -> str:
    return draws(s["ranking"]["draws"])


def judge_gap(s, group: str) -> tuple:
    """RLM-10 minus single pass by the judge at MARK, with S511's interval, in points."""
    p = next(x for x in s["S511"]["pairs"][str(MARK)][group] if (x["a"], x["b"]) == ("rlm_10", "single_pass"))
    return 100 * p["d"], 100 * p["lo"], 100 * p["hi"]


def concept_gap(s, group: str) -> tuple:
    """RLM-10 minus single pass by concept recall, with S526's interval, in points."""
    return tuple(s["S526"]["swaps"][signal_swap(s, group)]["contrast_B"])


def fmt_gap(gap: tuple) -> str:
    return f"{gap[0]:+.1f} ({gap[1]:+.1f} to {gap[2]:+.1f})"


# ---------------------------------------------------------------- the cells
def c_overall(s):
    a = rate(s, "all answerable", "matched_budget", "one call at RLM-10's budget")
    return (f"Given RLM-10's tokens per question, one call passed {a['value']}%.",
            [a, rate(s, "all answerable", "single_pass", "single pass"), rate(s, "all answerable", "rlm_10", "RLM-10")],
            judge_basis(s, "all answerable"))


def c_one(s):
    return ("RLM-10 lost by the judge, not by concept recall.",
            [rate(s, "one-paper", "single_pass", f"single pass, judge at {MARK}"), rate(s, "one-paper", "rlm_10", f"RLM-10, judge at {MARK}"),
             chi(s, "one_paper", "SP", "single pass, concept recall"), chi(s, "one_paper", "G1", "RLM-10, concept recall")],
            f"{judge_basis(s, 'one-paper')}; {concept_basis(s, 'one-paper')}")


def c_many(s):
    return ("On many-paper questions the judge and concept recall agree, and reading more text explains much of RLM-10's gain.",
            [rate(s, "many-paper", "single_pass", f"single pass, judge at {MARK}"), rate(s, "many-paper", "rlm_10", f"RLM-10, judge at {MARK}"),
             rate(s, "many-paper", "matched_budget", f"one call at RLM-10's budget, judge at {MARK}"),
             chi(s, "many_paper", "SP", "single pass, concept recall"), chi(s, "many_paper", "G1", "RLM-10, concept recall")],
            f"{judge_basis(s, 'many-paper')}; {concept_basis(s, 'many-paper')}")


def support_wording(mean: float, lo: float, hi: float) -> str:
    """attack.md's row 5, held to the paired interval: no claim of a rise, or of none, that the interval does not carry."""
    if lo <= 0 <= hi:
        return "No clear rise in support from verification."
    return f"Verification moved support by {mean:+.1f} points."


def c_support(s):
    k = ("swaps", papers_key(s), "B")
    d = ("swaps", "contrast set mc papers", "vp-sp")
    sw = s["S526"]["swaps"]["contrast set mc papers"]
    mean, lo, hi = (sw["vp-sp"][i] for i in range(3))
    draw, = found(r"\((draw \d+)\)", papers_key(s), SOURCES["S526"])
    return (support_wording(mean, lo, hi), [
        v(s, "S526", *k, "verified_pass", label="verified pass, Papers precision"),
        v(s, "S526", *k, "single_pass", label="single pass, Papers precision"),
        v(s, "S526", *d, 0, label="verified pass minus single pass", unit="points"),
        v(s, "S526", *d, 1, label=f"its {interval_level(s)}% interval, lower end, two-sided", unit="points"),
        v(s, "S526", *d, 2, label=f"its {interval_level(s)}% interval, upper end, two-sided", unit="points")],
        f"{draw}, {sw['n']} questions with a value in every strategy")


def refusal_wording(done: list) -> str:
    """Who refused every out-of-scope answer, of the strategies this cell reads; the names as figure_names prints them."""
    if not done:
        return "No strategy here refused every out-of-scope answer, by judge score."
    names = " and ".join(done)
    return f"{names[0].upper()}{names[1:]} refused every out-of-scope answer, by judge score."


def c_refusal(s):
    rows, done, questions = [], [], set()
    for arm in ("single_pass", "verified_pass", "rlm_10"):
        key = f"{FN.NOT_ANSWERABLE_KEY}|refusal_accuracy {REFUSAL_MARK} or more|{arm}"
        r = s["ranking"]["keys"][key]
        passed, total = len(r["pass"]), sum(len(x) for x in r.values())
        rows.append({"label": f"{STRATEGY[arm]}, answers refusing, refusal score {REFUSAL_MARK} or more", "value": passed, "unit": f"of {total}",
                     "source": s.paths["ranking"], "key": f"keys / {key}"})
        questions |= {k.split("|")[2] for x in r.values() for k in x}
        if passed == total:
            done.append(STRATEGY[arm])
    top = s["ranking"]["rule6_refusal"]["highest"]
    tied = "".join(f", tied with {STRATEGY[x]}" for x in top["tied_with"])
    rows.append({"label": f"not told apart from {STRATEGY[top['strategy']]}, the highest{tied}", "value": [STRATEGY[x] for x in top["not_separated_from"]],
                 "unit": "", "source": s.paths["ranking"], "key": "rule6_refusal / highest / not_separated_from"})
    new, old = found(r"an answer's (key v[\d.]+) row .*? where one exists, else its (key v[\d.]+) row", s["ranking"]["judge_rows"]["reader"], SOURCES["ranking"])
    return refusal_wording(done), rows, f"{ranking_basis(s)}, {len(questions)} questions; each answer's {new} row where one exists, else its {old} row"


def large_grid(s) -> dict:
    return {c: s["G4"]["claims"][c]["failures_in"][f"score{MARK}"]["cells"] for c in s["G4"]["claims"]}


def c_large(s):
    grid = large_grid(s)
    name = next(c for c in grid["S1"] if c.endswith(", 0x"))
    k = ("claims", "S1", "failures_in", f"score{MARK}", "cells", name)
    family = sum(len(x) for x in grid.values())
    old, new = found(r"from a (key v[\d.]+) row .*? questions (key v[\d.]+) changed", s["G4"]["awaiting_s6"]["what"], SOURCES["G4"])
    return (f"{name.split()[0]} core papers, the largest tested.", [
        v(s, "G4", *k, "single_pass", scale=100, label=f"single pass, judge at {MARK}"), v(s, "G4", *k, "rlm_10", scale=100, label=f"RLM-10, judge at {MARK}"),
        v(s, "G4", *k, "P_bonferroni", nd=3, label=f"P, Bonferroni over {family} cells, two-sided", unit=""),
        v(s, "G4", "awaiting_s6", "answers", label=f"answers still read from {old}", unit="answers")],
        f"{s['G4']['rests_on']}, {grid['S1'][name]['n']} questions; {new} where S6 has judged, else {old}")


def c_cost(s):
    k = ("cost", "answerable")
    return ("Time per answer, with verified pass's time mostly spent waiting.", [
        v(s, "ranking", *k, "single_pass", "clock_s", "mean", label="single pass, seconds", unit="s"),
        v(s, "ranking", *k, "verified_pass", "clock_s", "mean", label="verified pass, seconds", unit="s"),
        v(s, "ranking", *k, "verified_pass", "wait_s", "mean", label="of which waiting", unit="s"),
        v(s, "ranking", *k, "rlm_10", "clock_s", "mean", label="RLM-10, seconds", unit="s")],
        f"{ranking_basis(s)}, {s['ranking']['cost']['answerable']['verified_pass']['questions']} questions")


def c_code(s):
    k = ("claims_support", "mcnemar_best_of_3_vs_free_form")
    return ("Best-of-3 showed no clear gain.", [v(s, "fig6", *k, "pairs", label="pairs", unit="pairs"),
                                                v(s, "fig6", *k, "a_only", label="pass with best-of-3 only", unit="pairs"),
                                                v(s, "fig6", *k, "b_only", label="pass with free-form only", unit="pairs"),
                                                v(s, "fig6", *k, "p_two_sided", nd=2, label="P, McNemar, two-sided", unit="")],
            s["fig6"]["stamp"].removeprefix("PROVISIONAL: "))


def signals(s) -> list:
    """(row of S526, the signal's name, draws as S526 states them) for the three signals."""
    sw, papers = s["S526"]["swaps"], papers_key(s)
    draw, = found(r"\((draw \d+)\)", papers, SOURCES["S526"])
    return [(f"winner_gap judge {MARK}", f"the judge at {MARK}", draws(sw["rank_noise"]["winner_by_draw_judge4"])),
            ("winner_gap concept d181", "concept recall", draws(sw["rank_noise"]["winner_by_draw_concept"])),
            ("winner_gap mc papers", FN.PAPERS_PRECISION, draw)]


def c_triangulation(s):
    rows, gaps = [], []
    for key, name, _ in signals(s):
        row = s["S526"]["swaps"][key]
        mean, lo, hi = row["gap"]
        gaps.append((lo, hi))
        rows.append({"label": f"highest by {name}", "unit": "", "source": SOURCES["S526"], "key": f"swaps / {key}",
                     "value": f"{STRATEGY[row['winner']]}, {mean:.1f} points ahead of {STRATEGY[row['runner_up']]} ({interval_level(s)}% interval {lo:+.1f} to {hi:+.1f}, two-sided)"})
    tail = ", and no signal separates its highest from the next" if all(lo <= 0 <= hi for lo, hi in gaps) else ""
    return (f"Signals differ on which strategy is highest{tail}.", rows,
            "; ".join(f"{name}: {d}, {s['S526']['swaps'][key]['n']} questions" for key, name, d in signals(s)))


def orchestrator_rows(s) -> tuple:
    sheet = s["fig4"]["sheets"][f"Fig. {FN.FIG_PIPELINE}a"]
    col = {c: i for i, c in enumerate(sheet["columns"])}
    rows = [r for r in sheet["rows"] if "orchestrator set-up" in str(r[col["role"]]) and r[col["threshold"]] == MARK
            and r[col["row"]] == "setup"]   # the sheet also holds per-draw rows of the same set-ups, with no interval
    if not rows:
        raise Refused(f"{SOURCES['fig4']}: no orchestrator set-up at mark {MARK} in Fig. {FN.FIG_PIPELINE}a")
    return rows, col


ORCH_NAMES = {"orch_no_analyser": FN.NO_ANALYSER, "orch_no_planner": FN.NO_PLANNER, "orch_no_supervisor": FN.NO_SUPERVISOR,
              "orch_no_synthesiser": FN.NO_SYNTHESIZER, "orch_factual_to_documents": FN.ROUTING_FIX}


def c_orchestrator(s):
    """Each end is one set-up's interval against the full pipeline, so the two ends name two set-ups: no interval runs between them."""
    rows, col = orchestrator_rows(s)
    low = min(rows, key=lambda r: r[col["minus_full_low"]])
    high = max(rows, key=lambda r: r[col["minus_full_high"]])
    key = f"sheets / Fig. {FN.FIG_PIPELINE}a / minus_full_low and minus_full_high, orchestrator set-ups, judge at {MARK}"
    name = lambda r: ORCH_NAMES.get(r[col["config"]], r[col["setup"]])
    stamp = s["fig4"]["stamp"]
    draw, = found(r"(draw \d+) of", stamp, SOURCES["fig4"])
    keys, = found(r"(key v[\d.]+[^;]*)", stamp, SOURCES["fig4"])
    return ("No clear change in any orchestrator set-up; the intervals are wide.", [
        {"label": f"lowest end of any interval, from {name(low)}", "value": round(100 * low[col["minus_full_low"]], 1), "unit": "points", "source": SOURCES["fig4"], "key": key},
        {"label": f"highest end of any interval, from {name(high)}", "value": round(100 * high[col["minus_full_high"]], 1), "unit": "points", "source": SOURCES["fig4"], "key": key},
        {"label": "set-ups, each against the full pipeline", "value": len(rows), "unit": "set-ups", "source": SOURCES["fig4"], "key": key}],
        f"{draw}, {rows[0][col['questions']]} questions; {keys}")


def c_measure_judge(s):
    return ("Separates question types, which is not the same as being right.",
            [rate(s, "one-paper", "rlm_10", "RLM-10, one-paper"), rate(s, "many-paper", "rlm_10", "RLM-10, many-paper")],
            f"{judge_basis(s, 'one-paper')}; {judge_basis(s, 'many-paper')}")


def c_measure_concepts(s):
    k = ("swaps", signal_swap(s, "all"))
    return ("Reads whether the key's concepts are stated. Descriptive.", [
        v(s, "S526", *k, "contrast_A", 0, label=f"RLM-10 minus single pass, judge at {MARK}", unit="points"),
        v(s, "S526", *k, "contrast_B", 0, label="RLM-10 minus single pass, concept recall", unit="points")],
        concept_basis(s, "all"))


def papers_wording(heading_rule) -> str:
    state = "unset" if heading_rule is None else "set"
    return f"Provisional: the stored values count source-list lines as claims. D172's filter (minicheck_filter.py) is not applied here, and its heading rule is {state}."


def c_measure_papers(s):
    k = ("swaps", source_lines_key(s), "contrast_change_B_minus_A")
    draw, = found(r"\((draw \d+)\)", papers_key(s), SOURCES["S526"])
    return (papers_wording(MF.HEADING_RULE), [
        v(s, "S526", *k, 0, label="change in RLM-10 minus single pass when S526 drops source-list lines", unit="points")],
        f"{draw}, {s['S526']['swaps'][source_lines_key(s)]['n_q']} questions, S526's approximate filter")


# ---------------------------------------------------------------- the sentences held to their values: (does it hold, what was read)
def claim_one(s):
    judge, concept = judge_gap(s, "one-paper"), concept_gap(s, "one-paper")
    return judge[2] < 0 <= concept[2], f"RLM-10 minus single pass, judge {fmt_gap(judge)}, concept recall {fmt_gap(concept)}"


def claim_many(s):
    judge, concept = judge_gap(s, "many-paper"), concept_gap(s, "many-paper")
    g = s["S511"]["gap_closed"][str(MARK)]["many-paper"]
    named = (g["mid"], g["low"], g["high"]) == ("matched_budget", "single_pass", "rlm_10")
    return (named and judge[1] > 0 and concept[1] > 0 and g["ratio"] >= HALF,
            f"RLM-10 minus single pass, judge {fmt_gap(judge)}, concept recall {fmt_gap(concept)}; share of the gap one call closes {g['ratio']:.2f}")


def claim_large(s):
    grid = large_grid(s)
    core = {c: max(int(n.split()[0]) for n in grid[c]) for c in grid}
    family = sum(len(x) for x in grid.values())
    adjusted = all(abs(min(1.0, x["P"] * family) - x["P_bonferroni"]) < 1e-9 for cells in grid.values() for x in cells.values())
    return adjusted and core["S1"] > core["S2"], f"largest core size {core['S1']} against {core['S2']}; Bonferroni family {family}"


def claim_cost(s):
    row = s["ranking"]["cost"]["answerable"]["verified_pass"]
    share = row["wait_s"]["mean"] / row["clock_s"]["mean"]
    return share >= HALF, f"waiting is {share:.2f} of verified pass's time"


def claim_code(s):
    p = s["fig6"]["claims_support"]["mcnemar_best_of_3_vs_free_form"]["p_two_sided"]
    return p >= ALPHA, f"P {p:.2f}"


def claim_signals(s):
    winners = [s["S526"]["swaps"][key]["winner"] for key, _, _ in signals(s)]
    return len(set(winners)) > 1, ", ".join(winners)


def claim_orchestrator(s):
    rows, col = orchestrator_rows(s)
    lows, highs, holm = ([r[col[c]] for r in rows] for c in ("minus_full_low", "minus_full_high", "p_holm"))
    return (max(lows) <= 0 <= min(highs) and min(holm) >= ALPHA,
            f"{len(rows)} set-ups, largest lower end {100 * max(lows):+.1f}, smallest upper end {100 * min(highs):+.1f}, smallest Holm P {min(holm):.2f}")


CLAIMS = (("N2", "RLM-10 is below single pass by the judge, and not below it by concept recall", claim_one),
          ("N3", "both signals put RLM-10 above single pass, and one call at its budget closes at least half the judge's gap", claim_many),
          ("N6", "the cell's core size is the largest in the grid, and its P is adjusted over the whole grid", claim_large),
          ("N7", "at least half of verified pass's time is waiting", claim_cost),
          ("N8", f"best-of-3 against free-form has P at or above {ALPHA}", claim_code),
          ("N11", "the three signals do not all name one strategy", claim_signals),
          ("N12", f"every orchestrator set-up's interval holds zero and its Holm P is at or above {ALPHA}", claim_orchestrator))


def claim_gates(s: Sources, claims=CLAIMS) -> list:
    """Each fixed sentence against the values under it. A sentence its values do not carry stops the run."""
    rows, bad = [], []
    for cell, test, fn in claims:
        holds, got = fn(s)
        (rows if holds else bad).append({"cell": cell, "test": test, "got": got})
    if bad:
        raise GateFail("; ".join(f"{b['cell']}'s sentence is not carried by its values: {b['test']}, got {b['got']}" for b in bad))
    return rows


T2 = "T2's generators"
SECOND = "the second judge"
CELLS = (   # id, table, need, the row behind it, whose sentence, read function or None, depends_on, blank reason
    ("N1", "needs", "Any question, with the budget to read widely", "attack.md row 1, WEAKEN", ATTACK, c_overall, (), None),
    ("N2", "needs", "One-paper questions", "attack.md rows 2 and 3, WEAKEN", ATTACK, c_one, (), None),
    ("N3", "needs", "Many-paper questions", "attack.md row 4, KEEP, exploratory", OWN, c_many, (), None),
    ("N4", "needs", "Answers supported by the papers", "attack.md row 5, WEAKEN", COMPUTED, c_support, (), None),
    ("N5", "needs", "Declining what the papers cannot answer", "attack.md row 6, WEAKEN", COMPUTED, c_refusal, (), None),
    ("N6", "needs", "A large corpus", "attack.md row 7, KEEP", ATTACK, c_large, (), None),
    ("N7", "needs", "Time per answer", "attack.md row 8, KEEP, no best", OWN, c_cost, (), None),
    ("N8", "needs", "Code", "attack.md row 9, WEAKEN", ATTACK, c_code, (), None),
    ("N9", "needs", "The choice of generator", "attack.md row 10, KEEP until T2", None, None, (T2,), f"Needs {T2}. {BLIND}."),
    ("N10", "needs", "The choice of judge", "attack.md row 12, KEEP, no pick", None, None, (SECOND,), f"Needs {SECOND}. {BLIND}."),
    ("N11", "needs", "More than one signal", "attack.md row 13, WEAKEN", COMPUTED, c_triangulation, (), None),
    ("N12", "needs", "An orchestrated pipeline", "attack.md row 15, WEAKEN", OWN, c_orchestrator, (), None),
    ("N13", "needs", "A flat wide call, fixed in advance", "not a verdict row: attack.md's action A2", None, None, ("G10's judge rows",),
     "G10 is not judged yet (D196): no committed output holds its pass rates."),
    ("N14", "needs", "The old 800-character cut under the lock", "not in attack.md: D194 Q4", None, None, ("G11's judge rows",),
     "G11 is not judged yet (D196): no committed output holds its pass rates."),
    ("M1", "measures", "Judge correctness", "attack.md second table, WEAKEN", OWN, c_measure_judge, (), None),
    ("M2", "measures", "Concepts", "attack.md second table, KEEP", OWN, c_measure_concepts, (), None),
    ("M3", "measures", "Papers", "attack.md second table, WEAKEN", OWN, c_measure_papers, (), None),
    ("M4", "measures", "METEOR", "attack.md second table, WEAKEN", None, None, ("a tracked output of the evaluator comparison",),
     "Its number stands only in a scratch output (ev_fast.py), and this script reads none."),
    ("M5", "measures", "Citations", "attack.md second table, WEAKEN", None, None, (SECOND,), f"Its number comes from S483's composite, closed here beside {SECOND}. {BLIND}."),
    ("M6", "measures", "Refusal score", "attack.md second table, KEEP", None, None, ("the same values as N5",), "The only signal for this need, by design; its values are N5's."),
    ("M7", "measures", "RAGChecker", "attack.md second table, WEAKEN", None, None, ("K1's pull",), "K1's rows are partial until the pull (build_order.md section 7)."),
)

KNOWN = (   # cell, label, value, where it was stated, the source it was stated on (STATED_ON holds that source's sha256)
    ("N1", "one call at RLM-10's budget", 94.6, "attack.md row 1", "S511"),
    ("N2", f"single pass, judge at {MARK}", 97.2, "framing.md R1", "S511"),
    ("N2", f"RLM-10, judge at {MARK}", 70.6, "framing.md R1", "S511"),
    ("N3", f"single pass, judge at {MARK}", 51.3, "framing.md R1", "S511"),
    ("N3", f"RLM-10, judge at {MARK}", 84.6, "framing.md R1", "S511"),
    ("N3", f"one call at RLM-10's budget, judge at {MARK}", 85.9, "framing.md R1", "S511"),
    ("N7", "verified pass, seconds", 372.4, "attack.md row 8", "ranking"),
    ("N7", "of which waiting", 275.3, "attack.md row 8", "ranking"),
    ("N8", "P, McNemar, two-sided", 0.38, "compare.md, code generation", "fig6"),
    ("N12", f"lowest end of any interval, from {FN.ROUTING_FIX}", -18.6, "attack.md row 15", "fig4"),
    ("N12", f"highest end of any interval, from {FN.NO_SYNTHESIZER}", 14.0, "attack.md row 15", "fig4"),
)
STATED_ON = {  # the sha256 each source had when these values were stated, HEAD of 1 November
    "S511": "ebdefda28e790a4bd3bc67dc5130c2ac51f78c470027713f2b6c8a72755e2603",
    "ranking": "588163237a55cab09dd2e49aea14df8860220672e5c1403bc30934dcfaf3b027",
    "fig6": "4271738947a9397ffad5d42241b03f06cc48e311d18f87478ef031e06bb072ea",
    "fig4": "4b006766b75e5815281732e565aef94613af0f3ece45cbcee17e7a6862f31dce",
}


def build(s: Sources) -> list[dict]:
    out = []
    for cid, table, need, row, wording_from, read, depends_on, blank in CELLS:
        cell = {"id": cid, "table": table, "need": need, "attack_row": row, "wording_from": wording_from, "stands_on": None,
                "depends_on": list(depends_on), "blank": blank, "wording": None, "values": []}
        if read is not None:
            if blank is not None or depends_on:
                raise Refused(f"{cid}: a blank cell has a read function")
            cell["wording"], cell["values"], cell["stands_on"] = read(s)
        out.append(cell)
    return out


def check_blanks(cells: list[dict]) -> None:
    """A cell with a blank reason holds nothing, and every cell that waits for a blind row has one."""
    for c in cells:
        if c["blank"] is not None and (c["values"] or c["wording"]):
            raise Refused(f"{c['id']}: a blank cell holds a value")
        if c["blank"] is None and not c["values"]:
            raise Refused(f"{c['id']}: no value and no reason")
        if (T2 in c["depends_on"] or SECOND in c["depends_on"]) and c["blank"] is None:
            raise Refused(f"{c['id']}: waits for a blind row and is not blank")


def reproduce(cells: list[dict], s: Sources, known=KNOWN, stated_on=None) -> tuple[list, list]:
    """(gates that held, gates to restate). The module docstring, REPRODUCE BEFORE WRITING."""
    stated_on = STATED_ON if stated_on is None else stated_on
    by = {(c["id"], x["label"]): x["value"] for c in cells for x in c["values"]}
    held, restate, bad = [], [], []
    for cid, label, want, where, src in known:
        s[src]
        moved = bool(stated_on.get(src)) and not s.sha[s.paths[src]].startswith(stated_on[src])
        row = {"cell": cid, "label": label, "want": want, "got": by.get((cid, label)), "stated_at": where, "source": s.paths[src], "source_moved": moved}
        if row["got"] == want:
            held.append(row)
        elif moved:
            restate.append(row)
        else:
            bad.append(row)
    if bad:
        raise GateFail("; ".join(f"{b['cell']} {b['label']}: got {b['got']}, want {b['want']}" for b in bad))
    if not held:
        raise GateFail(f"no stated value reproduced: {len(restate)} to restate and no gate held, so nothing ties this map to a known number")
    return held, restate


def markdown(doc: dict) -> str:
    def rows(table):
        out = []
        for c in doc["cells"]:
            if c["table"] != table:
                continue
            if c["blank"]:
                out.append(f"| {c['id']} | {c['need']} | blank | {c['blank']} | | | {c['attack_row']} |")
                continue
            vals = "; ".join(f"{x['label']}: {', '.join(x['value']) if isinstance(x['value'], list) else x['value']}"
                             f"{' ' + x['unit'] if x['unit'] else ''}" for x in c["values"])
            out.append(f"| {c['id']} | {c['need']} | {c['wording']} | {vals}. | {c['stands_on']} | {c['wording_from']} | {c['attack_row']} |")
        return out

    head = ["| | Need | What the data support | Values | Stands on | Whose sentence | Row behind it |", "|---|---|---|---|---|---|---|"]
    src = sorted({x["source"] for c in doc["cells"] for x in c["values"]})
    return "\n".join(["# The map of needs (D194 Q2)", "", f"Written by {SCRIPT}, sha256 {doc['_provenance']['script_sha256'][:16]}. Descriptive: "
                      "no cell recommends an option. N5 and N11 say which strategy a rule or a signal placed highest. Whose sentence says whether "
                      "the words are attack.md's or this script's. Every value's key is in need_map.json.", "",
                      f"{len(doc['claim_gates'])} sentences held to their values, {len(doc['gates'])} stated values held, "
                      f"{len(doc['gates_to_restate'])} to restate.", "",
                      "## Needs", "", *head, *rows("needs"), "", "## Measures", "", *head, *rows("measures"), "", "## Sources", "", *[f"- {x}" for x in src], ""])


def write(out: Path, doc: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, text in (("need_map.json", json.dumps(doc, indent=1, sort_keys=True) + "\n"), ("need_map.md", markdown(doc))):
        tmp = out / f".{name}.tmp"
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, out / name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    install_guard()
    try:
        s = Sources()
        cells = build(s)
        check_blanks(cells)
        claims = claim_gates(s)
        held, restate = reproduce(cells, s)
        doc = {"_provenance": {"script": SCRIPT, "script_sha256": FR.sha256_file(Path(__file__)), "command": COMMAND,
                               "inputs_sha256": dict(sorted(s.sha.items()))},
               "claim_gates": claims, "gates": held, "gates_to_restate": restate, "cells": cells}
        write(a.out, doc)
    except GateFail as e:
        print(f"GATE FAILED, nothing written: {e}", file=sys.stderr)
        return 1
    except (Refused, S526.Refused, S526.S521.Refused) as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    print(f"{sum(1 for c in cells if not c['blank'])} cells with values, {sum(1 for c in cells if c['blank'])} blank; "
          f"{len(claims)} sentences held to their values; {len(held)} stated values held "
          f"({sum(r['source_moved'] for r in held)} on a rebuilt source), {len(restate)} to restate")
    for r in restate:
        print(f"  to restate: {r['cell']} {r['label']}, {r['want']} on a rebuilt {r['source']}")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
