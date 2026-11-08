#!/usr/bin/env python3
"""S542 - Supplementary Figure 18: RAGAS and RAGChecker against the judge and the three signals (D200 RS1 a).

WHY. Build spec fig5.md section 6. The draft of 28 October had four panels; RS1 a keeps its c and d, as a and b here.

WHAT THE CODE DOES. It reads S497.d200_data, so every value is the table of answers Figure 5 e reads: draw 1, answerable
answers, the judge rows through judge_rows_v25, K1's final rows, L1's overlap rows, concept recall and the claim filter.
  a  thirteen rows, the scores not in Figure 5 e, two columns as 5e: rho with the judge's correctness and faithfulness
     from S540.evaluator_rows: a box of the resample quartiles, whiskers at the 2.5th and 97.5th percentiles, and an open
     mark for the within-question rho. All pairs where both values exist. The thirteenth row is S596's windowed BERTScore
     F1 (D274, rulings page 6 Nov RUN-BERTSCORE: O1), read from its committed rows.jsonl and joined on (strategy,
     question, draw 1); before anything is drawn, S540.evaluator_rows on the joined table must equal S596's own
     evaluator_rows.json fig5e_form, or the run is refused (bert_join).
  b  twenty rows of rank tiles, from rank_rows (R8). One set of questions for every row: those whose six draw-1 answers
     hold the judge's score and all 18 other scores. Per row a mean per strategy; rankdata, ties sharing the mean rank;
     1 best; a lower-is-better score ranked on minus its mean. The judge's two rows are the pass share at 4 and at 3.
     The printed column is Spearman's rho between the row's six ranks and the row "judge, 4 or more", two decimals, no
     interval, since six items are coarse. A row whose ranks do not vary has no rho and prints nothing.
A negative rho prints with U+2212 from two sheet columns, order_sign and order_size (build order F6).

    uv run --frozen python scripts/S542_supp_evaluators.py figure [--out <folder>]

With minicheck_filter's heading rule unset it exits 2, as that module does, and writes nothing.
"""
from __future__ import annotations

import argparse
import importlib.util
import statistics
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
SCRIPT = "scripts/S542_supp_evaluators.py"
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig18_evaluators"
N = 18                                             # D302 (cited since D299; 15 before D257)
W, H = 183.0, 115.0                               # D274: 107 mm before the BERTScore row
IMPORTS = ("S497_fig5_d166.py", "S540_fig5_evaluators.py", "house_style.py", "figure_names.py", "minicheck_filter.py",
           "S473_fig5_panels.py", "S457_fig2_panels.py", "S463_fig2_ranking.py", "fig_repro.py", "judge_rows_v25.py",
           "S564_claimify_selection.py")
JUDGE_4, JUDGE_3 = "judge, 4 or more", "judge, 3 or more"
BERT_DIR = ROOT / "findings" / "recompute" / "S596_windowed_bertscore"
BERT_KEY, BERT_S596_LABEL = "bs:windowed_f1", "BERTScore (windowed)"     # S596.KEY and S596.LABEL
BERT_ROW = ("BERTScore, windowed", "BERTScore", BERT_KEY)               # D274; a one-row group: no rotated label


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S497 = _load("S497", ROOT / "scripts" / "S497_fig5_d166.py")
hs, S540, S473 = S497.hs, S497.S540, S497.S473
CONFIGS, LABEL = S497.CONFIGS, S497.LABEL
ROWS_A = (*S540.ROWS_S15, BERT_ROW)                                     # Supplementary Figure 18 a's rows
RAGAS_ROWS = (("faithfulness", "ragas:faithfulness"), ("answer relevancy", "ragas:answer_relevancy"),
              ("context precision", "ragas:context_precision"), ("context recall", "ragas:context_recall"),
              ("factual correctness", "ragas:factual_correctness"))
RC_ROWS = (("precision", "rc:precision"), ("recall", "rc:recall"), ("F1", "rc:f1"), ("claim recall", "rc:claim_recall"),
           ("context precision", "rc:context_precision"), ("context utilization", "rc:context_utilization"),
           ("noise sensitivity, relevant", "rc:noise_sensitivity_in_relevant"),
           ("noise sensitivity, irrelevant", "rc:noise_sensitivity_in_irrelevant"),
           ("hallucination", "rc:hallucination"), ("self-knowledge", "rc:self_knowledge"),
           ("faithfulness", "rc:faithfulness"))
# (family, label, value key); the judge's two rows are read from correctness
RANK_ROWS = (("judge", JUDGE_4, "pass4"), ("judge", JUDGE_3, "pass3"), ("signal", "Concepts", "concept"),
             ("signal", "Papers", "papers"),
             *(("RAGAS", lab, k) for lab, k in RAGAS_ROWS), *(("RAGChecker", lab, k) for lab, k in RC_ROWS))
TOOL_KEYS = tuple(k for _, k in (*RAGAS_ROWS, *RC_ROWS))
OTHER_18 = ("concept", "papers") + TOOL_KEYS


def rank_rows(table: list, configs=CONFIGS, rows=RANK_ROWS, lower_better=S540.LOWER_BETTER) -> dict:
    """R8; the module docstring. table: S540.answer_table's rows (or made-up ones). Returns {"questions", "rows": [one
    dict per row with "family", "metric", "means", "ranks", "order_rho"]}."""
    import numpy as np
    from scipy.stats import rankdata
    by: dict = {}
    for r in table:
        by.setdefault(r["question_id"], {})[r["config"]] = r
    keep = sorted(q for q, d in by.items() if all(
        c in d and d[c].get("correctness") is not None and all(d[c].get(k) is not None for k in OTHER_18) for c in configs))
    out = []
    for fam, lab, key in rows:
        vals = {c: [] for c in configs}
        for q in keep:
            for c in configs:
                r = by[q][c]
                v = (r["correctness"] >= S473.PASS_T if key == "pass4" else
                     r["correctness"] >= S473.PASS_RELAXED if key == "pass3" else r[key])
                vals[c].append(float(v))
        means = {c: float(np.mean(vals[c])) if vals[c] else float("nan") for c in configs}
        sign = 1 if key in lower_better else -1
        rk = rankdata([sign * means[c] for c in configs], method="average")
        out.append({"family": fam, "metric": lab, "key": key, "means": means,
                    "ranks": {c: float(x) for c, x in zip(configs, rk)}})
    base = [out[0]["ranks"][c] for c in configs]
    for r in out:
        own = [r["ranks"][c] for c in configs]
        r["order_rho"] = None if len(set(own)) < 2 or len(set(base)) < 2 else S473.spearman(own, base)
    return {"questions": len(keep), "rows": out}


def bert_join(table: list, bert_dir: Path = BERT_DIR) -> tuple:
    """D274: S596's windowed F1 joined to the table. Refuses when a table answer has no S596 row, when the counts
    differ, or when S540.evaluator_rows on the joined table does not reproduce S596's fig5e_form record for record.
    Returns (joined table, {path: sha256})."""
    import hashlib
    import json
    rows_p, ev_p = bert_dir / "rows.jsonl", bert_dir / "evaluator_rows.json"
    rows = [json.loads(x) for x in rows_p.read_text().splitlines() if x.strip()]
    by = {(r["config"], r["question_id"]): r["f1"] for r in rows if r["draw"] == 1}
    if len(by) != len(rows) or len(rows) != len(table):
        raise S540.Refused(f"S596: {len(rows)} rows for {len(table)} table answers; nothing written")
    miss = [(r["config"], r["question_id"]) for r in table if (r["config"], r["question_id"]) not in by]
    if miss:
        raise S540.Refused(f"S596: {len(miss)} table answers have no windowed BERTScore row, first {miss[0]}")
    joined = [{**r, BERT_KEY: by[(r["config"], r["question_id"])]} for r in table]
    want = json.loads(ev_p.read_text())["fig5e_form"]
    got = S540.evaluator_rows(joined, rows=((BERT_S596_LABEL, "simple", BERT_KEY),))
    if got != want:
        raise S540.Refused("S596: evaluator_rows on the joined table differs from evaluator_rows.json; nothing written")
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731
    return joined, {rel(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (rows_p, ev_p)}


def sheets(dat: dict, e_rows: list, ranks: dict) -> dict:
    a = {"columns": S497.SHEET_COLS["e"], "rows": [[r[k] for k in S497.SHEET_COLS["e"]] for r in e_rows]}
    b = {"columns": ["family", "metric", "strategy", "mean", "rank", "rank_text", "questions", "order_rho", "order_sign",
                     "order_size"], "rows": []}
    for r in ranks["rows"]:
        rho = r["order_rho"]
        for c in CONFIGS:
            b["rows"].append([r["family"], r["metric"], LABEL[c], r["means"][c], r["ranks"][c],
                              S497.rank_text(r["ranks"][c]), ranks["questions"], rho,
                              None if rho is None else (hs.MINUS if rho < -0.005 else ""),
                              None if rho is None else abs(rho)])
    cols = ["strategy", "question_id", "correctness", "faithfulness", "concept", "papers", *TOOL_KEYS, BERT_KEY]
    per = {"columns": cols, "rows": [[LABEL[r["config"]]] + [r.get(k) for k in cols[1:]] for r in dat["table"]]}
    return {f"Supplementary Fig. {N}a": a, f"Supplementary Fig. {N}b": b, f"Supplementary Fig. {N} answers": per}


def draw(e_rows: list, ranks: dict, sheet_b: dict):
    hs.apply_rc("S542")
    pl = S497.Page(W, H)
    tw = hs._text_width_mm
    # a
    ly, labr, x_c, cw, gap, rtop, pitch = 2.9, 41.0, 43.0, 24.0, 3.4, 4.7, 7.84
    rows = ROWS_A
    n = len(rows)
    pl.letter(0, ly, "a")
    lim = S497._e_limits(e_rows)
    ticks = [t for t in (-0.5, 0, 0.5, 1) if lim[0] <= t <= lim[1]]
    for k, (_, head) in enumerate(S540.JUDGE_SIGNALS):
        x = x_c + k * (cw + gap)
        pl.t(x + cw / 2, ly, head, ha="center")
        ax = pl.ax(x, rtop, cw, n * pitch, lim, (n, 0))
        ax.set_xticks(ticks, [hs.fmt_num(t, 1).rstrip("0").rstrip(".") if t % 1 else hs.fmt_num(t) for t in ticks])
        hs.reference_line(ax, 0)
        for i, (_label, group, _key) in enumerate(rows):
            r = e_rows[2 * i + k]
            hs.boxplot(ax, i + 0.5, stats={"q1": r["resample_q25"], "median": r["resample_median"],
                                           "q3": r["resample_q75"], "whisker_low": r["interval_lo"],
                                           "whisker_high": r["interval_hi"]}, dots=False, zorder=3)
            if r["within_question_rho"] is not None:
                ax.plot([r["within_question_rho"]], [i + 0.5], ls="none", marker="o", ms=hs.MARK_MM / hs.MM_PT,
                        mfc=hs.WHITE, mec=hs.BLACK, mew=0.5, zorder=8, clip_on=False)
            if i and rows[i - 1][1] != group:
                ax.plot(lim, [i, i], color=hs.GREY["line"], lw=hs.LW["divider"], zorder=0, clip_on=False)
    start = 0
    for i, (label, group, _key) in enumerate(rows):
        pl.t(labr, rtop + (i + 0.5) * pitch, label, ha="right", va="center_baseline")
        if i and rows[i - 1][1] != group:
            if i - start > 1:
                pl.t(2.2, rtop + start * pitch + (i - start) * pitch / 2, rows[i - 1][1], rotation=90, ha="center",
                     va="center")
            start = i
            pl.pg.plot([0.6, labr + 1.0], [rtop + i * pitch] * 2, color=hs.GREY["line"], lw=hs.LW["divider"], zorder=0,
                       solid_capstyle="butt", clip_on=False)
    if n - start > 1:
        pl.t(2.2, rtop + start * pitch + (n - start) * pitch / 2, rows[-1][1], rotation=90, ha="center", va="center")
    y_ax = rtop + n * pitch + 7.0
    pl.t(x_c + cw + gap / 2, y_ax, "Spearman's \u03c1 with the judge, per answer", ha="center")
    hs.key(pl.fig, [("open", (hs.BLACK, "o"), "within one question")], centre_x=20.0, y=y_ax)
    # b
    let, labr, x0, tw_, th, head, xend = 97.0, 137.0, 137.0, 6.0, 3.8, 19.4, 182.4
    top = 3.4 + head
    x_end_t = x0 + 6 * tw_
    pl.letter(let, ly, "b")
    # the rank key, centred above the tiles
    kw = 3.0
    total = tw("Rank") + 1.2 + 6 * kw
    kx = x0 + 3 * tw_ - total / 2
    pl.t(kx, ly, "Rank")
    kx += tw("Rank") + 1.2
    for r in range(1, 7):
        fc = hs.cividis_value(7 - r, 1, 6)
        pl.rect(kx, ly - 2.4, kw, 3.1, fc)
        pl.t(kx + kw / 2, ly, str(r), ha="center", color=hs.ink_on(fc), why="a rank in the key")
        kx += kw
    for j, c in enumerate(CONFIGS):
        pl.t(x0 + (j + 0.5) * tw_, top - 0.9, LABEL[c], rotation=90, ha="center", va="bottom")
    pl.t((x_end_t + xend) / 2 - 2.0, top - 0.9, "Order against", rotation=90, ha="center", va="bottom")
    pl.t((x_end_t + xend) / 2 + 2.0, top - 0.9, "judge", rotation=90, ha="center", va="bottom")
    row_i = 0
    rr = ranks["rows"]
    gstart = 0
    for i, r in enumerate(rr):
        y = top + i * th
        pl.t(labr - 0.8, y + th / 2, r["metric"], ha="right", va="center_baseline", why="the pass mark of the row")
        for j, c in enumerate(CONFIGS):
            v = r["ranks"][c]
            fc = hs.cividis_value(7 - v, 1, 6)
            pl.rect(x0 + j * tw_, y, tw_, th, fc, ec=hs.WHITE, lw=0.5)
            pl.t(x0 + (j + 0.5) * tw_, y + th / 2, S497.rank_text(v), ha="center", va="center_baseline",
                 color=hs.ink_on(fc), printed={"sheet": f"Supplementary Fig. {N}b", "row": row_i + j,
                                               "format": "{rank_text}"})
        if r["order_rho"] is not None:
            rho = sheet_b["rows"][row_i]
            s = f"{rho[8]}{S497.S457.half_up(rho[9], 2)}"
            pl.t(xend, y + th / 2, s, ha="right", va="center_baseline",
                 printed={"sheet": f"Supplementary Fig. {N}b", "row": row_i, "format": "{order_sign}{order_size:.2f}"})
        row_i += 6
        if i and rr[i - 1]["family"] != r["family"]:
            pl.pg.plot([let + 0.6, xend], [y, y], color=hs.GREY["line"], lw=hs.LW["divider"], zorder=3,
                       solid_capstyle="butt", clip_on=False)
            if rr[i - 1]["family"] in ("RAGAS", "RAGChecker"):
                pl.t(let + 2.2, top + (gstart + i) * th / 2, rr[i - 1]["family"], rotation=90, ha="center", va="center")
            gstart = i
    pl.t(let + 2.2, top + (gstart + len(rr)) * th / 2, rr[-1]["family"], rotation=90, ha="center", va="center")
    bad = hs.check_figure_colours(pl.fig)
    if bad:
        raise S540.Refused(f"Supplementary Figure {N}: colours outside the house palette: {bad}")
    return pl


def not_answerable_rows(k1: dict) -> int:
    """K1's draw-1 rows, either tool, on a question outside the answerable group: the false-premise answers."""
    return len({k for rows in k1["rows"].values() for k, r in rows.items()
                if k[2] == 1 and r.get("group") not in (None, "answerable")})


def texts(dat: dict, e_rows: list, ranks: dict, n_out: int, k_all: int) -> dict:
    table = dat["table"]
    q = len({r["question_id"] for r in table})
    low = [r["ragas:faithfulness"] for r in table if r.get("ragas:faithfulness") is not None
           and r["correctness"] is not None and r["correctness"] <= 2]
    high = [r["ragas:faithfulness"] for r in table if r.get("ragas:faithfulness") is not None
            and r["correctness"] is not None and r["correctness"] >= S473.PASS_T]
    x, y = (S497.S457.half_up(statistics.median(v), 2) for v in (low, high))
    bert = [r for r in e_rows if r["source"] == BERT_KEY]
    bert_n = {r["judge_signal"]: r["answers"] for r in bert}
    legend = (f"**Supplementary Figure {N} | RAGAS, RAGChecker and BERTScore against the judge and the three signals.** "
              "Answers of "
              f"the six strategies to the answerable questions, draw 1 (n = {len(table)} answers, {q} questions; "
              f"{k_all} hold the judge's score and every RAGAS and RAGChecker score, the other {len(table) - k_all} lack "
              "one or more of them). RAGAS "
              f"and RAGChecker ran on devstral-small-2:24b at the judge's settings. **a**, Spearman's \u03c1 of the "
              f"{len(ROWS_A)} scores not in Figure 6e with the judge's correctness and faithfulness, each over the "
              f"answers holding both values (the answers per \u03c1 are in sheet a's answers column): box, "
              "quartiles of 10,000 question resamples; whiskers, two-sided 95% percentile interval; open mark, \u03c1 "
              "among the answers to one question. A negative \u03c1 means agreement for hallucination, self-knowledge and both noise "
              f"sensitivities. BERTScore is the F1 of roberta-large over windows of at most 510 word pieces, each "
              f"starting 255 pieces after the last, so no answer or key is cut (n = {bert_n['Judge correctness']} "
              f"answers with correctness, {bert_n['Judge faithfulness']} with faithfulness). "
              f"**b**, Strategy rank by each score (1, best; ties share the mean rank) on n = {ranks['questions']} "
              f"questions; right, Spearman's \u03c1 of each row's ranks with the judge's at {S473.PASS_T} or more.")
    notes = (f"- Ranks in b are draw 1 on {ranks['questions']} questions, so they can differ from Figure 6b, which uses "
             "three draws.\n- The Concepts and Papers rows meet the letter's promise of a comparison with \"our three "
             "signals\" (Reviewer 1, Comment 1.2).\n- The "
             f"{n_out} false-premise answers are out of both panels (FF27 a).\n"
             "- FF27 a names no statistic for the order column; Spearman's rho is one of the two the letter's method uses.\n"
             "- The BERTScore row in a is S596's windowed F1 (findings/recompute/S596_windowed_bertscore, 510-piece "
             "windows at stride 255, roberta-large); D274 places it here and leaves Figure 6e as D200 drew it. It is not "
             "in b, whose question set needs every score of the 20 rank rows.\n"
             f"- Median RAGAS faithfulness is {x} at judge score 2 or less and {y} at {S473.PASS_T} or more (a result, "
             "so out of the legend since S3, 7 November; for the text).")
    return {"legend": legend, "notes": notes}


def figure(out, set_dir=None) -> None:
    with tempfile.TemporaryDirectory(prefix="S542_") as t:
        R, dat, srcs, d200 = S497.d200_data(Path(t), set_dir)
        table, bert_sha = bert_join(dat["table"])
        e_rows = S540.evaluator_rows(table, ROWS_A)
        ranks = rank_rows(table)
        sh = sheets(dat, e_rows, ranks)
        k = sum(1 for r in table if r.get("correctness") is not None and all(r.get(x) is not None for x in TOOL_KEYS))
        m = S473.PLANNED["papers"]
        tag = f"provisional, {k} of {m}"
        stamp = (f"PROVISIONAL: {k} of {m} draw-1 answerable answers have the judge's score and all {len(TOOL_KEYS)} tool "
                 "scores; "
                 f"RAGAS {len(R['k1']['rows']['ragas'])} and RAGChecker {len(R['k1']['rows']['ragchecker'])} rows (K1); "
                 f"ranks on {ranks['questions']} questions")
        T = texts(dat, e_rows, ranks, not_answerable_rows(R["k1"]), k)
        pl = draw(e_rows, ranks, sh[f"Supplementary Fig. {N}b"])
        cap = (f"# Supplementary Figure {N} data, caption\n\n**Supplementary Figure {N} data.** Provisional. Data stamp: "
               f"{stamp}. Sheet a: per score and judge signal rho, the resample quartiles and percentiles, the "
               "within-question rho and the pairs used. Sheet b: per row and strategy the mean, rank and order against the "
               f"judge. Sheet answers: the answers' judge scores, Concepts, Papers, {len(TOOL_KEYS)} tool scores and the windowed "
               "BERTScore F1. Generated by "
               f"`uv run --frozen python {SCRIPT} figure`.\n")
        S540.write_supp(out, N, tag, stamp, pl, sh, T["legend"], cap, script=SCRIPT, imports=IMPORTS,
                        inputs={**srcs["sha"], **d200["sha"], **bert_sha}, notes=T["notes"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("figure")
    f.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    S473.FR.pin_hash_seed()
    figure(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
