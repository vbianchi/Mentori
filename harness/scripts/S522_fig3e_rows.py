#!/usr/bin/env python3
"""S522 - the rows of Figure 3f (corpus size; 3e before D218), from S514 g4c's folder.

    uv run --frozen python scripts/S522_fig3e_rows.py [--g4 <S514 g4c folder>] [--out <folder>]
    uv run --frozen python scripts/S522_fig3e_rows_test.py

WHAT IT READS, each by its sha256 in header.json: from findings/recompute/G4_fig3c_d185/ (or --g4), grid_pairs.jsonl,
noise_pairs.jsonl, other_pairs.jsonl, other_noise_pairs.jsonl, q66_tables.json, refusal-free parts of header.json (the
draw-1 units, the status counts, the draws read); the committed Supplementary Figure 17 numbers and provenance. It opens
no generation record, no judge out and no file of a T2 generator or of the second judge. It sends no model call.

WHAT IT WRITES into findings/recompute/fig3e/ (or --out): tables.json and header.json, no write time in either. The
header records the command as this run gave it (command_line) and each input's sha256; a --g4 folder outside the repository
is named "<--g4>", so no machine folder enters the record.

Each block is a list of question sets, one per core-paper size:
  All in scope           every covered question of the size (grid_pairs.jsonl, covered true): 22, 44, 86 and 86;
  The same 22            the 22 answerable questions of q66_tables.json "ids";
  Refusal, the same 39   the 39 of q66_tables.json "ids", from other_pairs.jsonl.
A cell is S484.pooled(by, strategy, "single_pass", the size's three indexes, 1): the strategy minus single pass over every
(index, question) pair where both have a value, at judge score 4 for the first two blocks. On the third the value is
"refused" (refusal score 3 or more; a failed answer is not refused, Rule 10). Its interval resamples questions, each
carrying its summed difference and pair count, through S463.interval (10,000 resamples, seed 20261013, percentiles 2.5
and 97.5). A strategy with a unit not complete at a size has a row with no value (S484.drawn_by_size).
RLM-10 has two more rows in the first block, its one-paper and many-paper questions by S511.questions() kind (n 15, 30,
60, 60 and 7, 14, 26, 26).

THE GREY ROW (run-to-run, fig3.md Q1's default, O1). For each block and size, for each of the five strategies: its
difference at each draw read, by the same pooling, on D98's subset of the block's questions (noise_pairs.jsonl and
other_noise_pairs.jsonl: 6, 14, 29, 29; 6; 13 questions; S514 writes a draw there only when all 72 units are complete),
then its highest minus its lowest. The cell is the median of those five ranges. It stays empty while fewer than two
draws are read, or while the block's rows hold a draw-1 answer awaiting S6, since the range would then mix a key change
with run-to-run noise (S514:1091-1093). The reason is written in its "withheld" field.

REPRODUCE FIRST (README.md:75-79): any difference exits 1 with nothing written.
  (1) the first block at every size equals S484.compute's panel a cells with column single pass on the same rows, and,
      when the Supplementary Figure 17 provenance records the sha256 of the grid_pairs.jsonl read here, the committed
      sheet Supplementary Fig. 17a;
  (2) the second block's rates equal q66_tables.json answerable.main[...].pooled_over_ratios.score4, where no cell of
      the 22 is missing at that size and strategy;
  (3) the third block's rates equal not_answerable.main[...].pooled_over_ratios.failures_in in the same way.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCRIPT = "scripts/S522_fig3e_rows.py"
OUT = ROOT / "findings" / "recompute" / "fig3e"
DEFAULT_G4 = ROOT / "findings" / "recompute" / "G4_fig3c_d185"
PLANNED_G4 = 11682 + 6480                      # fig3.md section 3: G4 draw 1, then draws 2 and 3 of D98's subset
BLOCKS = ("All in scope", "The same 22", "Refusal, the same 39")
ALL, SAME, REFUSAL = BLOCKS
N_WANT = {ALL: {5: 22, 10: 44, 20: 86, 50: 86}, SAME: dict.fromkeys((5, 10, 20, 50), 22),
          REFUSAL: dict.fromkeys((5, 10, 20, 50), 39)}
N_SPLIT_WANT = {"one": {5: 15, 10: 30, 20: 60, 50: 60}, "many": {5: 7, 10: 14, 20: 26, 50: 26}}
N_NOISE_WANT = {ALL: {5: 6, 10: 14, 20: 29, 50: 29}, SAME: dict.fromkeys((5, 10, 20, 50), 6),
                REFUSAL: dict.fromkeys((5, 10, 20, 50), 13)}
FIVE = ("multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
SPLIT_STRATEGY = "rlm_10"
AWAIT = "v2.4 awaiting S6"
TOL = 1e-9
FIG9 = ROOT / "findings" / "figures_provisional" / "supp_fig17_corpus"


class Refused(Exception):
    """An input is not what this script was written for, or a known value did not reproduce."""


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def modules():
    """S484, S514 and S511, imported here so a test of this file's small functions needs none of them."""
    S484 = _load("S484", ROOT / "scripts" / "S484_supp_fig4_corpus.py")
    S514 = _load("S514", ROOT / "scripts" / "S514_fig3_d185.py")
    S511 = _load("S511", ROOT / "scripts" / "S511_g2_matched_budget.py")
    return S484, S514, S511


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p) -> str:
    p = Path(p).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def shown(p, folder) -> str:
    """How header.json names an input: repository-relative, or "<--g4>/<name>" for a --g4 folder outside the repository,
    since a machine's folder says nothing to a reader of the record."""
    p = Path(p).resolve()
    return rel(p) if p.is_relative_to(ROOT) else f"<--g4>/{p.relative_to(Path(folder).resolve())}"


def command_line(g4, out) -> str:
    """The command this run was, in header.json: an argument at its default is left out, a repository path is relative,
    and a --g4 folder outside the repository is named as such (its files stand under inputs_sha256 by sha256)."""
    c = f"uv run --frozen python {SCRIPT}"
    if Path(g4).resolve() != DEFAULT_G4.resolve():
        c += " --g4 " + (rel(g4) if Path(g4).resolve().is_relative_to(ROOT) else "<a folder outside the repository>")
    if Path(out).resolve() != OUT.resolve():
        c += " --out " + (rel(out) if Path(out).resolve().is_relative_to(ROOT) else "<a folder outside the repository>")
    return c


def rows_of(p: Path) -> list:
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def d_parts(d) -> tuple:
    """(d_sign, d_size_pp): build_order F6's two columns, read back as "{d_sign}{d_size_pp:.0f}". The sign is U+2212, "+"
    or nothing when the printed number is 0."""
    if d is None:
        return None, None
    size = abs(d)
    if round(size, 9) < 0.5:
        return "", size
    return ("+" if d > 0 else "−"), size


def table(rows, value="pass", covered_only=True) -> dict:
    """(index, strategy) -> {question: (value, value at score 4)} as S484.table holds it. value "pass": (pass3, pass4);
    "refused": (refused, refused), k = 1 reading the second."""
    by = collections.defaultdict(dict)
    for r in rows:
        if covered_only and not r["covered"]:
            continue
        for s, c in r["cells"].items():
            by[(r["index"], s)][r["question_id"]] = ((c["pass3"], c["pass4"]) if value == "pass"
                                                     else (c["refused"], c["refused"]))
    return by


def only(by, qids) -> dict:
    return collections.defaultdict(dict, {k: {q: v for q, v in d.items() if q in qids} for k, d in by.items()})


def awaiting_answers(rows, idxs, s, qids) -> int:
    """Answers of this cell, of the strategy and of single pass, read from a key v2.4 row of a question v2.5 changed."""
    return sum(1 for r in rows if r["index"] in idxs and r["question_id"] in qids and r.get("covered", True)
               for c in (s, "single_pass") if r["key_versions"].get(c) == AWAIT)


def cell_row(block, core, s, group, m, qids, rows, idxs) -> dict:
    """One cell of the sheet from S484.pooled's result m; a strategy not drawn at the size (m None) has no value."""
    base = {"row_kind": "cell", "block": block, "core_papers": core, "strategy": s, "question_group": group}
    if m is None or not m["n_pairs"]:
        return {**base, "n_questions": None, "n_pairs": None, "pass_strategy_pct": None, "pass_single_pass_pct": None,
                "d_pp": None, "ci95_lo_pp": None, "ci95_hi_pp": None, "interval_excludes_0": None,
                "awaiting_s6_answers": None, "d_sign": None, "d_size_pp": None}
    lo, hi = m["ci95_pp"]
    sign, size = d_parts(m["d_pp"])
    return {**base, "n_questions": m["n_questions"], "n_pairs": m["n_pairs"], "pass_strategy_pct": m["pass_a_pct"],
            "pass_single_pass_pct": m["pass_b_pct"], "d_pp": m["d_pp"], "ci95_lo_pp": lo, "ci95_hi_pp": hi,
            "interval_excludes_0": "yes" if (lo > 0 or hi < 0) else "no",
            "awaiting_s6_answers": awaiting_answers(rows, idxs, s, qids), "d_sign": sign, "d_size_pp": size}


def noise_for(S484, rows_by_draw: dict, block, core, qids_of, idxs, value, covered_only) -> list:
    """The grey row's strategy rows of one block and size: each strategy's difference per draw on the subset, its
    range; the row's "withheld" says why it has none."""
    draws = sorted(rows_by_draw)
    out = []
    for s in FIVE:
        per, n, await1 = {}, None, 0
        for d in draws:
            rows = [r for r in rows_by_draw[d] if r["index"] in idxs and r["question_id"] in qids_of]
            by = only(table(rows, value, covered_only), qids_of)
            m = S484.pooled(by, s, "single_pass", idxs, 1)
            per[str(d)] = m["d_pp"] if m["n_pairs"] else None
            n = m.get("n_questions", n)
            if d == 1:
                await1 = awaiting_answers(rows, idxs, s, qids_of)
        have = [v for v in per.values() if v is not None]
        why = (f"no run-to-run reading yet: draws read {draws}" if len(draws) < 2 else
               f"draw 1 holds {await1} answers awaiting S6: the range would mix a key change with run-to-run noise"
               if await1 else "a draw has no value" if len(have) != len(draws) else None)
        out.append({"row_kind": "run-to-run strategy", "block": block, "core_papers": core, "strategy": s,
                    "n_questions": n, "d_pp_by_draw": json.dumps(per, sort_keys=True),
                    "range_pp": max(have) - min(have) if why is None else None, "withheld": why})
    return out


def noise_cell(rows5: list) -> dict:
    """The grey cell: the median of the five strategies' ranges, or none with the first reason a range is withheld."""
    b = rows5[0]
    v = [r["range_pp"] for r in rows5]
    why = next((r["withheld"] for r in rows5 if r["withheld"]), None)
    m = None if why else statistics.median(v)
    return {"row_kind": "run-to-run cell", "block": b["block"], "core_papers": b["core_papers"],
            "n_questions": b["n_questions"], "median_range_pp": m, "withheld": why}


def build(g4: Path, modules_=None) -> tuple:
    """(tables, header inputs, reproduced lines), or Refused."""
    S484, S514, S511 = modules_ or modules()
    g4 = Path(g4)
    files = {n: g4 / n for n in ("grid_pairs.jsonl", "noise_pairs.jsonl", "other_pairs.jsonl",
                                 "other_noise_pairs.jsonl", "q66_tables.json", "header.json")}
    miss = [n for n, p in files.items() if not p.is_file()]
    if miss:
        raise Refused(f"{rel(g4)} holds no {miss}: run scripts/S514_fig3_d185.py g4c first")
    grid = rows_of(files["grid_pairs.jsonl"])
    other = [r for r in rows_of(files["other_pairs.jsonl"]) if r["group"] == "not_answerable"]
    noise = rows_of(files["noise_pairs.jsonl"])
    onoise = [r for r in rows_of(files["other_noise_pairs.jsonl"]) if r["group"] == "not_answerable"]
    q66 = json.loads(files["q66_tables.json"].read_text())
    hdr = json.loads(files["header.json"].read_text())
    units = hdr["units_draw1"]
    drawn = S484.drawn_by_size(units)
    ids22, ids39 = set(q66["ids"]["answerable"]), set(q66["ids"]["not_answerable"])
    kinds = S511.questions()
    sizes, ratios = S484.SIZES, S484.RATIOS
    by_pass = table(grid)
    by_ref = table(other, "refused", covered_only=False)
    covered = {c: {q for (i, s), d in by_pass.items() if S484.idx_name(c, 0) == i and s == "single_pass" for q in d}
               for c in sizes}
    cells, ns = [], []
    for block in BLOCKS:
        for c in sizes:
            idxs = [S484.idx_name(c, r) for r in ratios]
            qids = covered[c] if block == ALL else ids22 if block == SAME else ids39
            if len(qids) != N_WANT[block][c]:
                raise Refused(f"{block} at {c} core papers: {len(qids)} questions, want {N_WANT[block][c]}")
            ns.append({"row_kind": "n", "block": block, "core_papers": c, "question_group": "all",
                       "n_questions": len(qids)})
            by = only(by_ref if block == REFUSAL else by_pass, qids)
            rows = other if block == REFUSAL else grid
            for s in FIVE:
                m = S484.pooled(by, s, "single_pass", idxs, 1) if s in drawn[c] else None
                cells.append(cell_row(block, c, s, "all", m, qids, rows, idxs))
                if block == ALL and s == SPLIT_STRATEGY:
                    for kind in ("one", "many"):
                        sub = {q for q in qids if kinds[q]["kind"] == kind}
                        if len(sub) != N_SPLIT_WANT[kind][c]:
                            raise Refused(f"{kind}-paper at {c} core papers: {len(sub)} questions, want "
                                          f"{N_SPLIT_WANT[kind][c]}")
                        ns.append({"row_kind": "n", "block": block, "core_papers": c, "question_group": kind,
                                   "n_questions": len(sub)})
                        mk = S484.pooled(only(by, sub), s, "single_pass", idxs, 1) if s in drawn[c] else None
                        cells.append(cell_row(block, c, s, kind, mk, sub, rows, idxs))
    lines = reproduce(S484, grid, units, cells, q66, sha(files["grid_pairs.jsonl"]))
    # the grey row
    n_draw = sorted({r["draw"] for r in noise})
    if n_draw != sorted({r["draw"] for r in onoise}):
        raise Refused(f"noise_pairs.jsonl reads draws {n_draw}, other_noise_pairs.jsonl "
                      f"{sorted({r['draw'] for r in onoise})}")
    sub_st, sub_cell = [], []
    for block in BLOCKS:
        src = onoise if block == REFUSAL else noise
        by_draw = {d: [r for r in src if r["draw"] == d] for d in n_draw}
        for c in sizes:
            idxs = [S484.idx_name(c, r) for r in ratios]
            qs = ({r["question_id"] for rows in by_draw.values() for r in rows if r["core_papers"] == c
                   and r.get("covered", True) and r["question_id"] in (covered[c] if block == ALL else
                                                                       ids22 if block == SAME else ids39)})
            if len(qs) != N_NOISE_WANT[block][c]:
                raise Refused(f"the grey row of {block} at {c} core papers: {len(qs)} questions, want "
                              f"{N_NOISE_WANT[block][c]}")
            five = noise_for(S484, by_draw, block, c, qs, idxs, "refused" if block == REFUSAL else "pass",
                             block != REFUSAL)
            sub_st += five
            sub_cell.append(noise_cell(five))
    st = hdr["choice_report"]["by_status"]
    k = st.get("v2.4", 0) + st.get("v2.5", 0)
    tables = {"cells": cells, "n": ns, "noise_strategy": sub_st, "noise_cell": sub_cell, "draws_read": n_draw,
              "ratios": list(ratios), "g4_answers_final_key": k, "g4_answers_planned": PLANNED_G4,
              "g4_by_status": st, "awaiting_s6_cells": sum(e["awaiting_s6_answers"] or 0 for e in cells)}
    return tables, {shown(p, g4): sha(p) for p in files.values()}, lines


def reproduce(S484, grid, units, cells, q66, grid_sha) -> list:
    """The three checks of the module docstring; refuses on the first difference."""
    lines = []
    _, mine, _ = S484.compute(S484.table(grid), units)
    ref = {(e["core_papers"], e["row_strategy"]): e for e in mine["a"] if e["column_strategy"] == "single_pass"}
    n = 0
    for e in cells:
        if e["block"] != ALL or e["question_group"] != "all" or e["d_pp"] is None:
            continue
        x = ref.get((e["core_papers"], e["strategy"]))
        if x is None:
            raise Refused(f"check (1): {e['core_papers']} {e['strategy']} is not in S484.compute's cells")
        for a, b in (("n_pairs", "n_pairs"), ("pass_strategy_pct", "pass_row_pct"), ("pass_single_pass_pct",
                     "pass_column_pct"), ("d_pp", "d_pp"), ("ci95_lo_pp", "ci95_lo_pp"), ("ci95_hi_pp", "ci95_hi_pp")):
            n += 1
            if abs(float(e[a]) - float(x[b])) > TOL:
                raise Refused(f"check (1): {e['core_papers']} {e['strategy']} {a} {e[a]}, S484.compute {x[b]}")
    lines.append(f"(1) block 1: {n} values equal S484.compute's panel a cells with column single pass")
    # D302 (7 Nov): S484's plate (Supplementary Figure 17) is dropped, so its committed sheet is compared only where it
    # is still on disk; check (1) above holds the cells to S484.compute either way
    pf = FIG9 / "supplementary_figure17_provenance.json"
    prov = json.loads(pf.read_text()) if pf.exists() else None
    rec = ((prov or {}).get("inputs_sha256") or {}).get("findings/recompute/G4_fig3c_d185/grid_pairs.jsonl")
    if prov is None:
        lines.append("(1) no committed sheet Supplementary Fig. 17a to compare: S484's plate was dropped (D302)")
    elif rec == grid_sha:
        sh = json.loads((FIG9 / "supplementary_figure17_numbers.json").read_text())["sheets"]["Supplementary Fig. 17a"]
        rows = [dict(zip(sh["columns"], r)) for r in sh["rows"]]
        got = {(r["core_papers"], r["row_strategy"]): r for r in rows if r["column_strategy"] == "single_pass"}
        m = 0
        for e in cells:
            if e["block"] == ALL and e["question_group"] == "all" and e["d_pp"] is not None:
                x = got[(e["core_papers"], e["strategy"])]
                m += 1
                if abs(float(e["d_pp"]) - float(x["d_pp"])) > 1e-6 or abs(e["ci95_lo_pp"] - x["ci95_lo_pp"]) > 1e-6:
                    raise Refused(f"check (1): {e['core_papers']} {e['strategy']} differs from Supplementary Fig. 17a")
        lines.append(f"(1) block 1: {m} cells equal the committed sheet Supplementary Fig. 17a (its recorded grid_pairs "
                     f"sha256 is the one read)")
    else:
        lines.append("(1) the committed sheet Supplementary Fig. 17a is not compared: its provenance records another "
                     "grid_pairs.jsonl")
    for block, part, key, what in ((SAME, "answerable", "score4", "(2)"), (REFUSAL, "not_answerable", "failures_in", "(3)")):
        tab = {(e["core_papers"], e["strategy"]): e for e in q66[part]["main"]}
        n = 0
        for e in cells:
            if e["block"] != block or e["question_group"] != "all" or e["d_pp"] is None:
                continue
            for s, col in ((e["strategy"], "pass_strategy_pct"), ("single_pass", "pass_single_pass_pct")):
                t = tab[(e["core_papers"], s)]["pooled_over_ratios"]
                r = t["score4"]["failures_in"] if key == "score4" else t["failures_in"]
                if r.get("questions_without_value") or e["n_pairs"] != e["n_questions"] * len(S484.RATIOS):
                    continue
                n += 1
                if abs(r["rate_pct"] - e[col]) > TOL:
                    raise Refused(f"check {what}: {block} {e['core_papers']} {s}: {e[col]}, q66_tables {r['rate_pct']}")
        lines.append(f"{what} {block}: {n} rates equal q66_tables.json's pooled_over_ratios where no cell is missing")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--g4", type=Path, default=DEFAULT_G4)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    try:
        tables, inputs, lines = build(a.g4)
    except Refused as e:
        print(f"REFUSED (nothing written): {e}")
        return 1
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "tables.json").write_text(json.dumps(tables, indent=1, sort_keys=True) + "\n")
    (a.out / "header.json").write_text(json.dumps(
        {"script": SCRIPT, "script_sha256": sha(Path(__file__)), "command": command_line(a.g4, a.out),
         "model_calls": 0, "inputs_sha256": inputs, "reproduced": lines, "draws_read": tables["draws_read"],
         "provisional": True, "tables_sha256": sha(a.out / "tables.json")}, indent=1, sort_keys=True) + "\n")
    for x in lines:
        print(x)
    print(f"wrote {rel(a.out)}: {len(tables['cells'])} cells, draws read {tables['draws_read']}, "
          f"{tables['g4_answers_final_key']:,} of {PLANNED_G4:,} G4 answers read from their final-key row")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
