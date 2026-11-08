#!/usr/bin/env python3
"""S533: the Supplementary Table of the 66 questions in scope at every corpus size (supp.md section 12; D185 (1)).

One command, from the repository root:
    uv run --frozen python scripts/S533_table_66_questions.py [--out <folder>]
    uv run --frozen python scripts/S533_table_66_questions_test.py

Reads findings/recompute/G4_fig3c_d185/q66_tables.json and refusal_tables.json, both written by S514 g4c from G4's draw 1,
and prints what they hold. Three groups, each on its own, never pooled (D185 (1)):
  Block 1, the 22 answerable questions: pass rate at scores 4 and 3 with Rule 2's two-sided 95% interval, per strategy and
    size, failed answers in.
  Block 2, the 39 out-of-scope questions: refused rate with its interval, or at 100% the one-sided lower bound (Rule 9,
    D133), per strategy and size, then per 0, 1 and 3 distractor papers per core paper.
  Last row: the 5 false-premise questions, a pointer to Supplementary Figure 4c (supp.md C5).
A run-to-run column: on the pooled rows, the lowest to the highest rate over the draws in each group's `noise` block, on
D98's subset. It stays blank while `noise` holds one draw (S6G7G4 phase 2, D199). The workbook carries a Provenance sheet.

REPRODUCE FIRST: 22, 39 and 5 question ids, 24 rows per group, the two tables agree on the 39, and the answers awaiting S6G4
add to the table's own count. Any difference exits 2 and nothing is written. No model call; no T2 row, no second-judge row.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro as FR  # noqa: E402
import figure_names as FN  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Font  # noqa: E402

Q66 = ROOT / "findings/recompute/G4_fig3c_d185/q66_tables.json"
REFUSAL = ROOT / "findings/recompute/G4_fig3c_d185/refusal_tables.json"
OUT = ROOT / "findings/figures_provisional/supp_tables"
NAME = "Supplementary Table 66 questions"
STRATS = {"single_pass": "single pass", "multi_hop": "multi-hop", "verified_pass": "verified pass", "rlm_5": "RLM-5",
          "rlm_10": "RLM-10", "rlm_20": "RLM-20"}
SIZES = (5, 10, 20, 50)
WANT_IDS = {"answerable": 22, "not_answerable": 39, "false_premise": 5}
HEAD1 = ["Group", "Core papers", "Strategy", "Questions", "Pass rate 4+ (%)", "Interval 4+ (two-sided 95%)", "Pass rate 3+ (%)",
         "Interval 3+ (two-sided 95%)", "Answers awaiting S6G4", "Run to run"]
HEAD2 = ["Group", "Core papers", "Distractors per core paper", "Strategy", "Questions", "Refused (%)", "Interval or bound",
         "Answers awaiting S6G4", "Run to run"]


class Refused(Exception):
    """Refused before anything is written (exit 2)."""


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pct(v) -> str:
    return f"{v:.1f}"


def interval(e: dict) -> str:
    return f"{pct(e['ci95_pct'][0])} to {pct(e['ci95_pct'][1])}"


def refused_cell(e: dict) -> str:
    """Rule 9, D133: at 100% the one-sided lower bound, at 0% the upper, else the interval."""
    if e.get("full_one_sided_lower_bound_pct") is not None:
        return f"one-sided lower bound {pct(e['full_one_sided_lower_bound_pct'])}"
    if e.get("zero_one_sided_upper_bound_pct") is not None:
        return f"one-sided upper bound {pct(e['zero_one_sided_upper_bound_pct'])}"
    return interval(e)


def gate(q: dict, r: dict) -> None:
    got = {k: len(q["ids"][k]) for k in WANT_IDS}
    if got != WANT_IDS:
        raise Refused(f"question ids {got}, want {WANT_IDS}")
    for g in ("answerable", "not_answerable"):
        keys = {(e["core_papers"], e["strategy"]) for e in q[g]["main"]}
        if len(q[g]["main"]) != 24 or keys != {(c, s) for c in SIZES for s in STRATS}:
            raise Refused(f"{g}: {len(q[g]['main'])} rows, not the 24 of six strategies at four sizes")
    if r["main"] != q["not_answerable"]["main"]:
        raise Refused("refusal_tables.json and q66_tables.json differ on the 39")
    aw = q["answerable"]["awaiting_s6"]
    if sum(aw.get("by_unit", {}).values()) != aw["answers"]:
        raise Refused("the answers awaiting S6G4 do not add to the table's count")


def run_cell(noise: dict, core: int, strategy: str, rate) -> str | None:
    """The lowest to the highest rate of one strategy and size over the draws of a `noise` block; blank on one draw."""
    if len(noise) < 2:
        return None
    vals = [rate(next(e for e in noise[d]["tables"] if (e["core_papers"], e["strategy"]) == (core, strategy)))
            for d in sorted(noise)]
    return f"{pct(min(vals))} to {pct(max(vals))} over {len(vals)} draws"


def build_rows(q: dict) -> tuple[list, list, dict]:
    aw = q["answerable"]["awaiting_s6"]["by_unit"]
    aw2 = q["not_answerable"]["awaiting_s6"]["by_unit"]
    def rate1(e):
        return e["pooled_over_ratios"]["score4"]["failures_in"]["rate_pct"]

    def rate2(e):
        return e["pooled_over_ratios"]["failures_in"]["rate_pct"]
    b1 = []
    for e in q["answerable"]["main"]:
        p = e["pooled_over_ratios"]
        s4, s3 = p["score4"]["failures_in"], p["score3"]["failures_in"]
        wait = sum(v for k, v in aw.items() if k.startswith(f"{e['strategy']} exp_v4_s{e['core_papers']}_"))
        b1.append(["22 answerable questions", e["core_papers"], STRATS[e["strategy"]], s4["questions"], pct(s4["rate_pct"]),
                   interval(s4), pct(s3["rate_pct"]), interval(s3), wait,
                   run_cell(q["answerable"]["noise"], e["core_papers"], e["strategy"], rate1)])
    b2 = []
    for e in q["not_answerable"]["main"]:
        f = e["pooled_over_ratios"]["failures_in"]
        wait = sum(v for k, v in aw2.items() if k.startswith(f"{e['strategy']} exp_v4_s{e['core_papers']}_"))
        b2.append([f"39 {FN.OUT_OF_SCOPE_QUESTIONS}", e["core_papers"], "pooled", STRATS[e["strategy"]], f["questions"],
                   pct(f["rate_pct"]), refused_cell(f), wait,
                   run_cell(q["not_answerable"]["noise"], e["core_papers"], e["strategy"], rate2)])
        for x in e["per_index"]:
            f2 = x["failures_in"]
            b2.append([f"39 {FN.OUT_OF_SCOPE_QUESTIONS}", e["core_papers"], x["distractor_ratio"], STRATS[e["strategy"]], f2["questions"],
                       pct(f2["rate_pct"]), refused_cell(f2), aw2.get(f"{e['strategy']} {x['index']}", 0), None])
    return b1, b2, {"awaiting": q["answerable"]["awaiting_s6"]["answers"]}


def write(b1: list, b2: list, info: dict, out: Path) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Answerable"
    ws.append(HEAD1)
    for r in b1:
        ws.append(r)
    ws2 = wb.create_sheet("Out of scope")
    ws2.append(HEAD2)
    for r in b2:
        ws2.append(r)
    ws2.append(["The 5 false-premise questions: Supplementary Figure 4c"])
    for w in (ws, ws2):
        for c in w[1]:
            c.font = Font(bold=True)
    ws3 = wb.create_sheet("Provenance")
    for k, v in (("script", "scripts/S533_table_66_questions.py"), ("script_sha256", sha(Path(__file__))),
                 ("command", "uv run --frozen python scripts/S533_table_66_questions.py"),
                 ("q66_tables.json sha256", sha(Q66)), ("refusal_tables.json sha256", sha(REFUSAL))):
        ws3.append([k, v])
    x = out / f"{NAME}.xlsx"
    wb.save(x)
    FR.deterministic_xlsx(x)
    note = (f"Draw 1 of corpus scaling, gemini-3-flash-preview, judged by devstral-small-2:24b. Groups are never pooled. "
            f"Refused: a refusal accuracy of 3 or more under the decline prompt. Each interval is two-sided 95% (percentile "
            f"bootstrap, 10,000 resamples of the questions); at 100% refused the cell gives the one-sided lower bound, at 0% "
            f"the one-sided upper bound. Provisional: {info['awaiting']} answerable answers await S6G4 and are read on key "
            f"v2.4 until it ends. Run to run gives the lowest to the highest rate over the draws on the fixed third of each "
            f"group, and stays blank until a second draw is read. Failed answers are kept in every rate, as not passed and "
            f"not refused.")
    md = [f"# {NAME}", "", note, "", "| " + " | ".join(HEAD1) + " |", "|" + "---|" * len(HEAD1)]
    md += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in b1]
    md += ["", "| " + " | ".join(HEAD2) + " |", "|" + "---|" * len(HEAD2)]
    md += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in b2]
    md += ["", "The 5 false-premise questions: Supplementary Figure 4c."]
    m = out / f"{NAME}.md"
    m.write_text("\n".join(md) + "\n")
    return x, m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    try:
        q, r = json.loads(Q66.read_text()), json.loads(REFUSAL.read_text())
        gate(q, r)
        b1, b2, info = build_rows(q)
    except Refused as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    x, m = write(b1, b2, info, a.out)
    print(f"wrote {x.name} and {m.name}: {len(b1)} answerable rows, {len(b2)} out-of-scope rows; provisional, "
          f"{info['awaiting']} answers await S6G4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
