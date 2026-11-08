#!/usr/bin/env python3
"""S535: the Supplementary Table of the human evaluation grid (amendment 7, findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md:276-310).

Two commands, from the repository root:
    uv run --frozen python scripts/S535_table_human_grid.py frame            headers and row labels only
    uv run --frozen python scripts/S535_table_human_grid.py fill --results <file> --released <D number>
    uv run --frozen python scripts/S535_table_human_grid.py selftest

`frame` writes every table amendment 7 fixes, each value cell blank, one sheet each:
  Grid          verdict (mean correctness, primary; mean faithfulness, descriptive), judge bar, concept bar, MiniCheck bar,
                human verdict bar, rule: items, accuracy, Cohen's kappa with its interval, balanced accuracy, sensitivity,
                specificity, pass rate.
  McNemar       the same cells, the 2-of-3 rule against each single signal: exact two-sided McNemar test, alpha 0.05.
  Signal pairs  Cohen's kappa between each pair of signals, at each pair of bars.
  ROC           ROC AUC of the number of passing signals, per cell.
It reads nothing but this file's constants, which are amendment 7's words. `fill` writes the same sheets from a results file
of the pre-registered computation, {sheet: {key joined by "|": {column: value}}}; it refuses without --released, and that
word is Valerio's, on P1 (plan.csv H1). No agent opens a rater's packet, and this script holds no path to one. It is tested
on made-up rows only, in its selftest. The workbook carries a Provenance sheet.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro as FR  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Font  # noqa: E402

OUT = ROOT / "findings/figures_provisional/supp_tables"
NAME = "Supplementary Table human evaluation grid"
JUDGE_BARS = (4, 3)                            # amendment 7: 4 primary, 3 relaxed
CONCEPT_BARS = (0.5, 0.33, 0.67, 1)            # 0.5 primary, the others reported
MINICHECK_BARS = (0.5, 0.67, 0.8, 1)           # 0.5 primary, the others reported
HUMAN_BARS = (4, 3)                            # the mean correctness rating, 4 primary, 3 relaxed
RULES = ("at least 1 of 3", "at least 2 of 3", "3 of 3", "judge alone", "concept recall alone", "MiniCheck alone")
VERDICTS = ("mean correctness", "mean faithfulness")     # correctness primary; "the same table with mean faithfulness"
SINGLE = ("judge", "concept recall", "MiniCheck")        # the 2-of-3 rule is tested against each
VALUES = ("items", "accuracy", "cohen_kappa", "kappa_ci95_lo", "kappa_ci95_hi", "balanced_accuracy", "sensitivity",
          "specificity", "pass_rate")
CELL = ["Verdict", "Judge bar", "Concept bar", "MiniCheck bar", "Human verdict bar"]
BARS = list(itertools.product(VERDICTS, JUDGE_BARS, CONCEPT_BARS, MINICHECK_BARS, HUMAN_BARS))
PAIRS = ([("judge", a, "concept recall", b) for a in JUDGE_BARS for b in CONCEPT_BARS]
         + [("judge", a, "MiniCheck", b) for a in JUDGE_BARS for b in MINICHECK_BARS]
         + [("concept recall", a, "MiniCheck", b) for a in CONCEPT_BARS for b in MINICHECK_BARS])
# sheet: (header of the key columns, keys, value columns)
SHEETS = {"Grid": ([*CELL, "Rule"], [(*k, r) for k in BARS for r in RULES], VALUES),
          "McNemar": ([*CELL, "Against"], [(*k, s) for k in BARS for s in SINGLE],
                      ("items", "rule_only_agrees", "signal_only_agrees", "p_exact_two_sided")),
          "Signal pairs": (["Signal", "Bar", "Other signal", "Other bar"], PAIRS,
                           ("items", "cohen_kappa", "kappa_ci95_lo", "kappa_ci95_hi")),
          "ROC": (CELL, BARS, ("items", "roc_auc"))}


def keys() -> list[tuple]:
    return SHEETS["Grid"][1]


def rows(results: dict | None, sheet: str = "Grid") -> list[list]:
    _, ks, vals = SHEETS[sheet]
    out = []
    for k in ks:
        v = ((results or {}).get(sheet) or {}).get("|".join(str(x) for x in k), {})
        out.append([*k, *[v.get(c) for c in vals]])
    return out


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(results: dict | None, out: Path, note: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)
    md = [f"# {NAME}", "", note]
    for name, (key_head, _, vals) in SHEETS.items():
        ws = wb.create_sheet(name)
        head = [*key_head, *vals]
        ws.append(head)
        table = rows(results, name)
        for r in table:
            ws.append(r)
        for c in ws[1]:
            c.font = Font(bold=True)
        md += ["", f"## {name}", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        md += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in table]
    ws = wb.create_sheet("Provenance")
    for k, v in (("script", "scripts/S535_table_human_grid.py"), ("script_sha256", sha(Path(__file__))),
                 ("source", "findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md, amendment 7")):
        ws.append([k, v])
    x = out / f"{NAME}.xlsx"
    wb.save(x)
    FR.deterministic_xlsx(x)
    (out / f"{NAME}.md").write_text("\n".join(md) + "\n")
    return x


NOTE_FRAME = ("Frame: headers and row labels only. Amendment 7 fixes every sheet here, so no cell is chosen after the results "
              "are seen. Grid and ROC: one row per verdict and set of bars. McNemar: the 2-of-3 rule against each single "
              "signal, with alpha 0.05; an item with no MiniCheck value leaves every comparison that uses MiniCheck. Primary "
              "cell: verdict mean correctness, judge bar 4, concept bar 0.5, MiniCheck bar 0.5, human verdict bar 4. Mean "
              "faithfulness as the verdict is descriptive. Judge-human agreement against human-human agreement is reported "
              "apart, not in this table.")


def selftest() -> int:
    made_up = {"Grid": {"|".join(str(x) for x in keys()[0]): {"items": 49, "accuracy": 0.5}}}
    t = rows(made_up)
    n_key = len(SHEETS["Grid"][0])
    ok = [("one row per cell of the grid, for both verdicts", len(t) == 2 * 2 * 4 * 4 * 2 * len(RULES)),
          ("a frame holds no value", all(v is None for name in SHEETS for r in rows(None, name)
                                         for v in r[len(SHEETS[name][0]):])),
          ("a made-up value lands in its own row only", t[0][n_key] == 49 and all(r[n_key] is None for r in t[1:])),
          ("the mean faithfulness verdict has its rows", sum(r[0] == "mean faithfulness" for r in t) == len(t) / 2),
          ("McNemar lists each cell against each single signal", len(rows(None, "McNemar")) == len(BARS) * len(SINGLE)),
          ("every pair of signals is listed", len(PAIRS) == 2 * 4 + 2 * 4 + 4 * 4),
          ("the grid holds the pass rate", "pass_rate" in VALUES)]
    src = Path(__file__).read_text()
    gone = ("response/" + "human_eval_v22", "response/" + "rater_packets", "S5" + "00", "S5" + "01", "S5" + "10", "S5" + "17")
    ok.append(("this file names no packet and no early-look output", not any(g in src for g in gone)))
    with tempfile.TemporaryDirectory() as td:
        ok.append(("fill refuses without --released", main(["fill", "--results", str(Path(td) / "x.json"), "--out", td]) == 2))
    for name, c in ok:
        print(f"  {'PASS' if c else 'FAIL'}  {name}")
    return 0 if all(c for _, c in ok) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("frame")
    f.add_argument("--out", type=Path, default=OUT)
    g = sub.add_parser("fill")
    g.add_argument("--results", type=Path, required=True)
    g.add_argument("--released", default=None, help="the decision number that releases the computation")
    g.add_argument("--out", type=Path, default=OUT)
    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "frame":
        x = write(None, a.out, NOTE_FRAME)
        print(f"wrote {x.name}: " + ", ".join(f"{k} {len(v[1])}" for k, v in SHEETS.items()) + " rows, every value cell blank")
        return 0
    if not a.released:
        print("REFUSED: fill needs --released, Valerio's word on the pre-registered computation (plan.csv H1)", file=sys.stderr)
        return 2
    x = write(json.loads(a.results.read_text()), a.out, f"Released under {a.released}.")
    print(f"wrote {x.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
