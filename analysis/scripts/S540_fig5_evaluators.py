#!/usr/bin/env python3
"""S540 - the evaluators against the judge: K1's final rows, rho with a resample box, within-question rho (Figure 5 e,
Supplementary Figure 18). A library for S497 and S542, with three commands of its own.

WHY. fig5.md section 7, readers R1, R5, R6, R10. D200's Figure 5 e and Supplementary Figure 18 set RAGAS, RAGChecker and
the simple evaluators against the judge, answer by answer. S473.read_k1 cannot read K1's final rows: it lacks
studio_11451 (S473.K1_WORKERS) and refuses a key in two folders.

WHAT THE CODE DOES.
  read_k1_final(k1_dir)   R1. assignment.collect(k1_dir, base, chain) reads every worker of the amendment chain, the
                          latest row per answer. Then each row of beelink_112 replaces its answer's row, as the 28 October
                          draft's data.py did: collect() does not read that folder (K1 README, D112 Q7). Refused, with
                          gate on, unless collect's "missing" is empty for both tools (for RAGChecker, but for the
                          questions whose not-done answers all failed twice by a length stop, which D110 counts as done:
                          d110_done; 3 Nov, 5 answers of 4 questions on the final rows), each tool has 576 rows, and each
                          tool has 4 rows in beelink_112, each replacing a row whose status is no_answer. gate=False is for
                          a test on partial rows and is never passed by a figure.
  tool_values(k1)         per (config, question) of draw 1, the RAGAS scores of a row with status ok or ok_with_nulls and
                          the RAGChecker metrics of a row with status ok, as "ragas:<name>" and "rc:<name>". Any other
                          status gives no values.
  rho_box(points)         R5. S473.answer_rho's statistic (Spearman's rho over all answers; 10,000 question resamples
                          from S473.boot_rows, every answer of a question drawn together; 2.5th and 97.5th percentiles;
                          a resample with one distinct value on either side left out), plus the 25th, 50th and 75th
                          percentiles of the resample values. It computes each resample's rho from weighted average
                          ranks, which equal scipy's ranks on the repeated answers, because S473's python loop takes
                          seconds per row. check_rho_box holds it to answer_rho.
  within_rho(points)      R6. Ranks each signal within a question (average ties, as a share of that question's pairs),
                          centres on the question's mean, and takes Pearson's r over all pairs, as a11.py:11-15. A
                          question with one pair adds nothing, since its centred ranks are 0.
  second_judge_rows(...)  R10. It refuses unless S518's second_judge.json exists, is tracked and unchanged at HEAD, the
                          D195 line stands in experiments/README.md, and the word passed names a decision in
                          experiments/README.md. It takes only rows carrying the second judge's tag (the collect's
                          judge "model"); a failed answer (no_answer) takes the judge's 0, as answer_table does.
  second_judge_final()    D267 (rulings page 6 Nov, FIG5E: O1). S518's two inputs found by role in second_judge.json and
                          held to its sha256, each read by second_judge_rows under D267, the key v2.5 row where one
                          exists, else the key v2.4 base row, as S518.merge. second_judge_table joins draw 1 to the
                          table of answers; S497 calls both for Figure 5 e's last row.
  answer_table(...)       one dict per draw-1 answerable answer with the judge's scores and every other score, read from
                          the rows S497 has already chosen and filtered. A failed answer takes the judge's 0, as
                          S473.compute does.

COMMANDS. No model call. `pull` runs only where it may reach the machines: the integrator's.
    uv run --frozen python scripts/S540_fig5_evaluators.py selftest
    uv run --frozen python scripts/S540_fig5_evaluators.py timing [--k1 <folder>]
        writes findings/recompute/S540_timing.json: the median wall_s per RAGAS metric and per RAGChecker answer, draw 1,
        answerable answers, status ok or ok_with_nulls, with provenance (Reviewer 1, P5.13; on no panel).
    uv run --frozen python scripts/S540_fig5_evaluators.py pull --to <new folder>
        read-only copies through S473.fetch: L1 from the Studio, K1's six workers, and K1's beelink_112; then K1's
        assignment.json and amendments.json from this repository's findings/recompute/K1, which read_k1_final needs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCRIPT = "scripts/S540_fig5_evaluators.py"
REC = ROOT / "findings" / "recompute"
README = ROOT / "experiments" / "README.md"
S518_DIR = REC / "S518_split_confirmation"
RELEASE = S518_DIR / "second_judge.json"       # R10: exists only after S518 ran on Valerio's word
TIMING = REC / "S540_timing.json"
DECISION = "**D195**"                          # S518's own test that the decision stands
SECOND_JUDGE = "qwen3.8:27b"                   # LOCK.toml [judge] second_model
PLANNED_K1 = 576                               # S473.read_k1's "planned": 96 questions x 6 strategies, draw 1
Q7_WORKER = "beelink_112"
Q7_REPLACED = 4
Q7_WAS = "no_answer"
N_ANSWERABLE_ANSWERS = 516

RAGAS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall", "factual_correctness")
RC = ("precision", "recall", "f1", "claim_recall", "context_precision", "context_utilization",
      "noise_sensitivity_in_relevant", "noise_sensitivity_in_irrelevant", "hallucination", "self_knowledge",
      "faithfulness")
OVERLAP = ("rouge_l_f1", "meteor", "number_overlap", "semantic_similarity")   # the same four as Supplementary Figure 3
# Figure 5 e's rows, in order: (label, group, score key). D267 (rulings page 6 Nov, FIG5E: O1): the last row is the
# second judge's score of the same kind as the judge signal it is set against, "second:correctness" against the
# judge's correctness and "second:faithfulness" against its faithfulness (second_judge_table); without those columns
# in the table the row stays blank with HELD as its source.
SECOND_KEY = "second:{signal}"
SECOND_DECISION = "D267"                       # the decision that records Valerio's word for R10 (FIG5E: O1)
ROWS_5E =(("RAGAS faithfulness", "RAGAS", "ragas:faithfulness"),
           ("RAGAS factual correctness", "RAGAS", "ragas:factual_correctness"),
           ("RAGChecker faithfulness", "RAGChecker", "rc:faithfulness"),
           ("RAGChecker F1", "RAGChecker", "rc:f1"),
           ("ROUGE-L", "simple", "ov:rouge_l_f1"),
           ("METEOR", "simple", "ov:meteor"),
           ("Number overlap", "simple", "ov:number_overlap"),
           ("bge-m3 similarity", "simple", "ov:semantic_similarity"),
           ("Concepts", "signal", "concept"),
           ("Papers", "signal", "papers"),
           ("Second judge", "second judge", SECOND_KEY))
HELD = "held, D195"
# Supplementary Figure 18 a's rows, the scores not in Figure 5 e
ROWS_S15 = (("answer relevancy", "RAGAS", "ragas:answer_relevancy"),
            ("context precision", "RAGAS", "ragas:context_precision"),
            ("context recall", "RAGAS", "ragas:context_recall"),
            ("precision", "RAGChecker", "rc:precision"),
            ("recall", "RAGChecker", "rc:recall"),
            ("claim recall", "RAGChecker", "rc:claim_recall"),
            ("context precision", "RAGChecker", "rc:context_precision"),
            ("context utilization", "RAGChecker", "rc:context_utilization"),
            ("noise sensitivity, relevant", "RAGChecker", "rc:noise_sensitivity_in_relevant"),
            ("noise sensitivity, irrelevant", "RAGChecker", "rc:noise_sensitivity_in_irrelevant"),
            ("hallucination", "RAGChecker", "rc:hallucination"),
            ("self-knowledge", "RAGChecker", "rc:self_knowledge"))
LOWER_BETTER = frozenset({"rc:hallucination", "rc:self_knowledge", "rc:noise_sensitivity_in_relevant",
                          "rc:noise_sensitivity_in_irrelevant"})           # data.py LOWER_BETTER
JUDGE_SIGNALS = (("correctness", "Judge correctness"), ("faithfulness", "Judge faithfulness"))


# what no new script of this build reads (build_order.md section 5). Built from parts, so this file does not name them.
BLIND = ("out_" + "t2", "out_s6_" + "t2", "mentori-runs-s6-" + "second", "response/" + "human_eval", "response/" + "rater",
         "response/" + "internal_review", "response/" + "concept_match", "all_v2_1_" + "signoff", "S3" + "54",
         "S5" + "00", "S5" + "01", "S5" + "10", "S5" + "17", "resubmission/" + "11_internal", ".config/" + "mentori-runs",
         "rec_" + "main", "recom" + "mend.md")


def blind_hits(path) -> list:
    """Which of BLIND a script's source names."""
    src = Path(path).read_text()
    return [b for b in BLIND if b in src]


class Refused(SystemExit):
    pass


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def s473():
    return _load("S473", ROOT / "scripts" / "S473_fig5_panels.py")


def assignment():
    from experiments.scorers import assignment as A
    return A


def jl(p) -> list:
    with open(p) as fh:
        return [json.loads(x) for x in fh if x.strip()]


def sha256_file(p) -> str:
    return s473().FR.sha256_file(p)


# ---------------------------------------------------------------------------------------------------------------
# R1: K1's final rows
# ---------------------------------------------------------------------------------------------------------------
def read_k1_final(k1_dir, gate: bool = True) -> dict:
    """The module docstring's read_k1_final. k1_dir holds assignment.json, amendments.json, one folder per worker and
    beelink_112. Returns {"rows": {tool: {(config, question, draw): row}}, "missing", "replaced", "files"}."""
    A = assignment()
    k1_dir = Path(k1_dir)
    try:
        base = A.load(k1_dir / "assignment.json")
        chain = A.load_chain(k1_dir / "amendments.json", base)
        got = A.collect(k1_dir, base, chain)
    except A.AssignmentError as e:
        raise Refused(f"K1 collect refused: {e}; nothing written") from None
    rows, replaced, files = {}, {}, {}
    for tool, rel in A.ROWS.items():
        latest = {(r["config"], r["question_id"], r["draw"]): r for r in got["rows"][tool]}
        q7f = k1_dir / Q7_WORKER / rel
        q7 = jl(q7f) if q7f.exists() else []
        done = []
        for r in q7:
            k = (r["config"], r["question_id"], r["draw"])
            was = (latest.get(k) or {}).get("status")
            if gate and was != Q7_WAS:
                raise Refused(f"K1 {tool}: {Q7_WORKER}'s row of {k} replaces a row of status {was!r}, not {Q7_WAS}")
            latest[k] = r
            done.append({"answer": list(k), "was": was, "now": r.get("status")})
        rows[tool], replaced[tool] = latest, done
        for p in sorted(k1_dir.glob(f"*/{rel}")):
            files[p.relative_to(k1_dir).as_posix()] = sha256_file(p)
    length_done = d110_done(k1_dir, rows["ragchecker"], got["missing"]["ragchecker"], A)
    if gate:
        left = {t: [q for q in v if not (t == "ragchecker" and q in length_done["questions"])]
                for t, v in got["missing"].items()}
        bad = [f"{t}: {len(v)} questions missing, first {v[0]}" for t, v in left.items() if v]
        bad += [f"{t}: {len(rows[t])} rows, planned {PLANNED_K1}" for t in rows if len(rows[t]) != PLANNED_K1]
        bad += [f"{t}: {len(replaced[t])} {Q7_WORKER} rows, want {Q7_REPLACED}" for t in rows
                if len(replaced[t]) != Q7_REPLACED]
        if bad:
            raise Refused("K1's final rows: " + "; ".join(bad) + "; nothing written")
    return {"rows": rows, "missing": got["missing"], "replaced": replaced, "files": files, "head": got["head"],
            "length_done": length_done["answers"]}


LENGTH_STOP = "model call length"              # ragchecker_run.py's error text for a reply at the lock's num_predict


def d110_done(k1_dir, latest: dict, missing: list, A) -> dict:
    """D110 (Valerio, 21 October, Q25): a RAGChecker answer whose latest two rows are both failed by a length stop counts
    as done and is not retried; its latest row stays "failed", so it has no value (ragchecker_run.py length_twice).
    assignment.collect's DONE set does not apply D110, so it lists such a question as missing. Returns the missing
    questions whose every not-done draw-1 answer meets D110 ("questions") and those answers ("answers"). A question with
    any other not-done answer is left out, so the gate still refuses it."""
    hist: dict = {}
    for p in sorted(Path(k1_dir).glob(f"*/{A.ROWS['ragchecker']}")):
        for r in jl(p):
            hist.setdefault((r["config"], r["question_id"], r["draw"]), []).append(r)
    done_q, answers = [], []
    for q in missing:
        bad = [k for k, r in latest.items() if k[1] == q and r.get("status") not in A.DONE_RC]
        twice = [k for k in bad if len(hist.get(k, [])) >= 2 and all(
            x.get("status") == "failed" and LENGTH_STOP in str(x.get("error")) for x in hist[k][-2:])]
        if bad and twice == bad:
            done_q.append(q)
            answers += [list(k) for k in bad]
    return {"questions": done_q, "answers": sorted(answers)}


def tool_values(k1: dict) -> dict:
    """Per (config, question) of draw 1, "ragas:<name>" and "rc:<name>" values. A null score stays absent."""
    out: dict = {}
    for (c, q, d), r in k1["rows"]["ragas"].items():
        if d == 1 and r.get("status") in ("ok", "ok_with_nulls"):
            for m in RAGAS:
                v = (r.get("scores") or {}).get(m)
                if v is not None:
                    out.setdefault((c, q), {})[f"ragas:{m}"] = float(v)
    for (c, q, d), r in k1["rows"]["ragchecker"].items():
        if d == 1 and r.get("status") == "ok":
            for m in RC:
                v = (r.get("metrics") or {}).get(m)
                if v is not None:
                    out.setdefault((c, q), {})[f"rc:{m}"] = float(v)
    return out


def row_groups(k1: dict) -> dict:
    """K1's status count per tool, by group, for the notes."""
    from collections import Counter
    return {t: {f"{g} {s}": n for (g, s), n in sorted(Counter((r.get("group"), r.get("status")) for r in v.values()
                                                              ).items(), key=str)} for t, v in k1["rows"].items()}


# ---------------------------------------------------------------------------------------------------------------
# R5, R6: the statistics
# ---------------------------------------------------------------------------------------------------------------
def _weighted_ranks(val_idx, weights, n_values):
    """Average ranks of each answer in each resample, weights (resamples x answers) the times each answer is repeated.
    val_idx: each answer's index among the sorted distinct values."""
    import numpy as np
    n_res, n = weights.shape
    cnt = np.zeros((n_res, n_values))
    for j in range(n_values):
        cnt[:, j] = weights[:, val_idx == j].sum(axis=1)
    cum = np.cumsum(cnt, axis=1)
    rank = cum - (cnt - 1) / 2                  # scipy's average rank of each distinct value among the repeats
    return rank[:, val_idx]


def rho_box(points: list) -> dict:
    """R5, points [(question, x, y)]; the module docstring. Fewer than 3 points gives Nones, as answer_rho."""
    import numpy as np
    S473 = s473()
    if len(points) < 3:
        return {"rho": None, "lo": None, "hi": None, "q25": None, "median": None, "q75": None, "answers": len(points),
                "questions": len({q for q, _, _ in points})}
    qs = sorted({q for q, _, _ in points})
    index = {q: i for i, q in enumerate(qs)}
    q_i = np.array([index[q] for q, _, _ in points])
    x = np.array([p[1] for p in points], float)
    y = np.array([p[2] for p in points], float)
    rho = S473.spearman(x, y)
    w = np.asarray(S473.boot_rows(len(qs)), float)[:, q_i]      # resamples x answers
    ux, ix = np.unique(x, return_inverse=True)
    uy, iy = np.unique(y, return_inverse=True)
    rx, ry = _weighted_ranks(ix, w, len(ux)), _weighted_ranks(iy, w, len(uy))
    tot = w.sum(axis=1, keepdims=True)
    mx, my = (w * rx).sum(axis=1, keepdims=True) / tot, (w * ry).sum(axis=1, keepdims=True) / tot
    dx, dy = rx - mx, ry - my
    cov = (w * dx * dy).sum(axis=1)
    vx, vy = (w * dx * dx).sum(axis=1), (w * dy * dy).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        res = cov / np.sqrt(vx * vy)
    # a resample with one distinct value on a side has zero variance there and is undefined, as answer_rho leaves it
    res[(vx <= 1e-9) | (vy <= 1e-9)] = np.nan
    good = res[~np.isnan(res)]
    lo, hi = (float(np.percentile(good, 2.5)), float(np.percentile(good, 97.5))) if len(good) else (None, None)
    q25, med, q75 = (float(v) for v in np.percentile(good, [25, 50, 75])) if len(good) else (None, None, None)
    return {"rho": rho, "lo": lo, "hi": hi, "q25": q25, "median": med, "q75": q75, "answers": len(points),
            "questions": len(qs), "resamples_undefined": int(np.isnan(res).sum())}


def check_rho_box(points: list, tol: float = 1e-9) -> str:
    """R5's gate: rho_box gives S473.answer_rho's rho, lo and hi on the same points."""
    a, b = s473().answer_rho(points), rho_box(points)
    bad = [k for k in ("rho", "lo", "hi") if abs(a[k] - b[k]) > tol]
    if bad or a["resamples_undefined"] != b["resamples_undefined"]:
        raise Refused(f"rho_box differs from S473.answer_rho on {bad or 'the undefined resamples'}: {a} against {b}")
    return (f"rho_box equals S473.answer_rho's rho, interval and undefined resamples on {len(points)} answers, "
            f"{a['questions']} questions (tolerance {tol})")


def within_rho(points: list):
    """R6, points [(question, x, y)]; the module docstring. None when nothing varies within a question."""
    import numpy as np
    from scipy.stats import rankdata
    by: dict = {}
    for q, x, y in points:
        by.setdefault(q, []).append((x, y))
    ax, ay = [], []
    for _q, v in sorted(by.items()):
        rx, ry = rankdata([a for a, _ in v]) / len(v), rankdata([b for _, b in v]) / len(v)
        ax += list(rx - rx.mean())
        ay += list(ry - ry.mean())
    ax, ay = np.array(ax), np.array(ay)
    if len(ax) < 3 or ax.std() == 0 or ay.std() == 0:
        return None
    return float(np.corrcoef(ax, ay)[0, 1])


# ---------------------------------------------------------------------------------------------------------------
# the table of answers: every score of a draw-1 answerable answer
# ---------------------------------------------------------------------------------------------------------------
def answer_table(read_cells: dict, faith_rows: dict, l3_rows: dict, l1_stages: dict, k1: dict, groups: dict,
                 configs) -> list:
    """One dict per draw-1 answerable answer, on the rows S497 chose: the judge's plain call (a failed answer scores 0,
    Rule 10, as S473.compute), the call with passages (status ok only), concept recall, Papers precision from the papers
    stage, MiniCheck F1 against the key, the four simple scores and K1's values. A missing value is None."""
    tv = tool_values(k1)
    out = []
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    for q in qa:
        for c in configs:
            k = (c, q, 1)
            cell = read_cells.get(k) or {}
            j = cell["score"] if cell.get("kind") == "scored" else 0 if cell.get("kind") == "failed" else None
            st, fv, _ = faith_rows.get(k, (None, None, None))
            l3 = l3_rows.get(k)
            conc = l3["concept_recall_loose"] if l3 and l3["status"] in ("ok", "no_answer", "error") else None
            sig = lambda s: ((l1_stages[s].get(k) or {}).get("signals") or {})   # noqa: E731
            row = {"config": c, "question_id": q, "correctness": j, "faithfulness": fv if st == "ok" else None,
                   "concept": conc, "papers": sig("papers").get("precision"), "key_f1": sig("key").get("f1")}
            for m in OVERLAP:
                row[f"ov:{m}"] = sig("overlap").get(m)
            row.update(tv.get((c, q), {}))
            out.append(row)
    return out


def pairs(table: list, signal: str, score: str) -> list:
    """All answers holding both values, as [(question, judge value, score)]."""
    return [(r["question_id"], r[signal], r[score]) for r in table
            if r.get(signal) is not None and r.get(score) is not None]


def evaluator_rows(table: list, rows=ROWS_5E, drawn=None) -> list:
    """One record per (row, judge signal) in the columns of sheet Fig. 5e. A row with no score key, or left out of
    drawn, keeps its label with blank values and HELD as its source."""
    out = []
    for label, group, key in rows:
        for sig, sig_label in JUDGE_SIGNALS:
            rec = {"row": label, "family": group, "judge_signal": sig_label, "rho": None, "resample_q25": None,
                   "resample_median": None, "resample_q75": None, "interval_lo": None, "interval_hi": None,
                   "within_question_rho": None, "answers": None, "questions": None, "source": HELD}
            k = key.format(signal=sig) if key is not None else None
            if k is not None and (drawn is None or label in drawn) and (key != SECOND_KEY
                                                                         or any(k in r for r in table)):
                p = pairs(table, sig, k)
                b = rho_box(p)
                rec.update(rho=b["rho"], resample_q25=b["q25"], resample_median=b["median"], resample_q75=b["q75"],
                           interval_lo=b["lo"], interval_hi=b["hi"], within_question_rho=within_rho(p),
                           answers=b["answers"], questions=b["questions"], source=k)
            out.append(rec)
    return out


# ---------------------------------------------------------------------------------------------------------------
# R10: never called; tested on made-up rows
# ---------------------------------------------------------------------------------------------------------------
def _git(root, *a):
    return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)


def _committed(path: Path, root: Path) -> bool:
    rel = Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    return bool(_git(root, "ls-files", "--", rel).stdout.strip()) and not _git(root, "status", "--porcelain", "--",
                                                                                rel).stdout.strip()


def second_judge_rows(collect, word, *, release: Path = RELEASE, readme: Path = README, root: Path = ROOT) -> dict:
    """R10; the module docstring. collect: a jsonl of the second judge's rows, frozen after S518's run. word: the id of
    the decision that records Valerio's word (for example "D201"). Returns {(config, question, draw): {"correctness":
    value or None, "faithfulness": value or None}}. Nothing is opened before the four checks pass."""
    if not word or not re.fullmatch(r"D\d+", str(word)):
        raise Refused("second judge: no decision named: Valerio's word comes first (D195)")
    text = Path(readme).read_text()
    if DECISION not in text:
        raise Refused("second judge: D195 no longer stands in experiments/README.md; S518's condition fails")
    if f"**{word}**" not in text:
        raise Refused(f"second judge: experiments/README.md records no decision {word}")
    if not Path(release).exists():
        raise Refused(f"second judge: {Path(release).name} does not exist: S518 has not run")
    if not _committed(Path(release), root):
        raise Refused(f"second judge: {Path(release).name} is not committed and unchanged")
    out = {}
    for r in jl(collect):
        j = r.get("judge")
        tag = j.get("model") if isinstance(j, dict) else j          # s3_guard collect: {"which", "model", "digest"}
        if tag != SECOND_JUDGE:
            raise Refused(f"second judge: a row with judge tag {tag!r} in {Path(collect).name}")
        k = (r["config"], r["question_id"], r["draw"])
        if k in out:
            raise Refused(f"second judge: {k} doubled in {Path(collect).name}")
        a, b = r.get("a") or {}, r.get("b") or {}
        # D267: an answer that failed (no_answer) takes the judge's 0, as answer_table and S473.compute do (Rule 10)
        out[k] = {
            "correctness": ((a.get("scores") or {}).get("correctness") if a.get("status") == "ok"
                            else 0 if a.get("status") == "no_answer" else None),
            "faithfulness": (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None}
    return out


SECOND_ROLES = ("base", "collect")             # second_judge.json "inputs": key v2.4 base, key v2.5 collect


def second_judge_final(word=SECOND_DECISION, *, release: Path = RELEASE, readme: Path = README,
                       root: Path = ROOT) -> dict:
    """D267: the second judge's rows on the final key, as S518 read them for second_judge.json: its two inputs ("base",
    key v2.4; "collect", key v2.5), each found by its role in second_judge.json's "inputs" and held to the sha256
    recorded there, read by second_judge_rows; the key v2.5 row where one exists, else the base row (S518.merge).
    Refuses a collect row not tagged key v2.5. Returns {"rows", "inputs", "v25_rows", "base_rows"}."""
    rows_by, inputs = {}, []
    if not Path(release).exists():
        raise Refused(f"second judge: {Path(release).name} does not exist: S518 has not run")
    rec = {i["role"]: i for i in json.loads(Path(release).read_text()).get("inputs", [])}
    for role in SECOND_ROLES:
        if role not in rec:
            raise Refused(f"second judge: {Path(release).name} records no {role!r} input")
        p = Path(root) / rec[role]["path"]
        if sha256_file(p) != rec[role]["sha256"]:
            raise Refused(f"second judge: {rec[role]['path']} is not the file S518 read (sha256)")
        if role == "collect" and any(r.get("key_version") != "v2.5" for r in jl(p)):
            raise Refused(f"second judge: {rec[role]['path']} holds a row that is not key v2.5")
        rows_by[role] = second_judge_rows(p, word, release=release, readme=readme, root=root)
        inputs.append({"role": role, "path": rec[role]["path"], "sha256": rec[role]["sha256"]})
    final = {**rows_by["base"], **rows_by["collect"]}
    return {"rows": final, "inputs": inputs, "base_rows": len(rows_by["base"]), "v25_rows": len(rows_by["collect"])}


def second_judge_table(table: list, rows: dict) -> list:
    """The table of answers with each draw-1 answer's second-judge correctness and faithfulness as
    "second:correctness" and "second:faithfulness", for 5e's last row (SECOND_KEY)."""
    out = []
    for r in table:
        s = rows.get((r["config"], r["question_id"], 1)) or {}
        out.append({**r, **{SECOND_KEY.format(signal=sig): s.get(sig) for sig, _ in JUDGE_SIGNALS}})
    return out


# ---------------------------------------------------------------------------------------------------------------
# one writer for Supplementary Figures 4 and 18 to 20 (14 to 17 before D257)
# ---------------------------------------------------------------------------------------------------------------
def write_supp(out, n: int, tag: str, stamp: str, page, sheets: dict, legend: str, caption: str, *, script: str,
               imports: tuple, inputs: dict, notes: str | None = None, state: dict | None = None) -> None:
    """The plate, its data workbook and caption, the numbers and provenance files S448 reads and the legend, into a
    staging folder, then moved over this figure's earlier files. page: S497.Page. Nothing here holds a time, a git state
    or a temporary path. tag: "provisional, <k> of <m>", the same in every name."""
    S473 = s473()
    FR, S457 = S473.FR, S473.S457
    out = Path(out).resolve()
    base, data = f"Supplementary Figure {n} ({tag})", f"Supplementary Figure {n} data ({tag})"
    cap = f"Supplementary Figure {n} data caption ({tag}).md"
    nums, prov = f"supplementary_figure{n}_numbers.json", f"supplementary_figure{n}_provenance.json"
    stage = out.with_name(out.name + ".staging")
    import shutil
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    try:
        paths = {k: stage / f"{base}.{k}" for k in ("pdf", "svg", "png")}
        S457.finish_plate(page.fig, page.w, page.h, paths, title=f"Supplementary Figure {n}")
        FR.check_pdf_deterministic(paths["pdf"])
        FR.check_svg_deterministic(paths["svg"])
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
        for name, sh in sheets.items():
            ws = wb.create_sheet(name)
            ws.append(sh["columns"])
            for r in sh["rows"]:
                if len(r) != len(sh["columns"]):
                    raise Refused(f"{name}: a row of {len(r)} cells under {len(sh['columns'])} columns")
                ws.append(r)
        wb.save(stage / f"{data}.xlsx")
        FR.deterministic_xlsx(stage / f"{data}.xlsx")
        (stage / cap).write_text(caption)
        (stage / nums).write_text(json.dumps({"stamp": stamp, "what": f"Supplementary Figure {n}, data values and printed "
                                              "numbers (S448 R8 compares the workbook with this file)",
                                              "sheets": sheets, "printed": page.printed}, indent=1, default=float) + "\n")
        (stage / "legend_draft.md").write_text(f"# Supplementary Figure {n}, title and legend (draft)\n\nWritten by "
                                               f"`{script} figure`. Data stamp: {stamp}.\n\n{legend}\n")
        if notes:
            (stage / "methods_notes.md").write_text(f"# Supplementary Figure {n}, notes for the Methods\n\nWritten by "
                                                    f"`{script} figure`.\n\n{notes}\n")
        if state is not None:
            (stage / f"supplementary_figure{n}_state.json").write_text(json.dumps(state, indent=1, default=float) + "\n")
        files = {p.name: FR.sha256_file(p) for p in sorted(stage.iterdir())}
        (stage / prov).write_text(json.dumps({
            "provenance": {"script": script, "script_sha256": FR.sha256_file(ROOT / script),
                           "imports_sha256": {m: FR.sha256_file(ROOT / "scripts" / m) for m in imports},
                           "command": f"uv run --frozen python {script} figure"},
            "stamp": stamp, "page_mm": [page.w, page.h], "inputs_sha256": dict(sorted(inputs.items())),
            "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "sha256": FR.sha256_file(S457.FIGURE_LOCK),
                            "status": S457.FLOCK.get("status")},
            "files": files}, indent=1, default=str) + "\n")
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    out.mkdir(parents=True, exist_ok=True)
    for pat in (f"Supplementary Figure {n}*", f"supplementary_figure{n}_*", "legend_draft.md", "methods_notes.md"):
        for p in out.glob(pat):
            p.unlink()
    for p in stage.iterdir():
        shutil.move(str(p), out / p.name)
    stage.rmdir()
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: {base}")


# ---------------------------------------------------------------------------------------------------------------
# timing and pull
# ---------------------------------------------------------------------------------------------------------------
def timing(k1: dict, groups: dict | None = None) -> dict:
    """Medians of K1's wall_s: per RAGAS metric (its row's wall_s holds one value per metric) and per RAGChecker answer
    (one value per row), draw 1, answerable answers, status ok or ok_with_nulls."""
    per: dict = {}
    for r in k1["rows"]["ragas"].values():
        if r.get("group") == "answerable" and r.get("draw") == 1 and r.get("status") in ("ok", "ok_with_nulls"):
            for m, v in (r.get("wall_s") or {}).items():
                if v is not None:
                    per.setdefault(m, []).append(float(v))
    rc = [float(r["wall_s"]) for r in k1["rows"]["ragchecker"].values()
          if r.get("group") == "answerable" and r.get("draw") == 1 and r.get("status") == "ok"
          and r.get("wall_s") is not None]
    return {"ragas_median_s_per_metric": {m: statistics.median(v) for m, v in sorted(per.items())},
            "ragas_answers_per_metric": {m: len(v) for m, v in sorted(per.items())},
            "ragchecker_median_s_per_answer": statistics.median(rc) if rc else None,
            "ragchecker_answers": len(rc)}


def write_timing(k1_dir, out: Path = TIMING) -> dict:
    k1 = read_k1_final(k1_dir)
    res = timing(k1)
    head = _git(ROOT, "rev-parse", "HEAD").stdout.strip()
    rec = {"_provenance": {"script": SCRIPT, "script_sha256": sha256_file(ROOT / SCRIPT), "git_head": head,
                           "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                           "command": f"uv run --frozen python {SCRIPT} timing", "inputs_sha256": k1["files"]}, **res}
    Path(out).write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def pull(to) -> None:
    """Read-only copies, as S473.pull reads them: S473.fetch on each machine. S473 stays unchanged."""
    S473 = s473()
    to = Path(to).expanduser().resolve()
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty: pull into a new folder")
    k1 = "findings/recompute/" + "K1"
    workers = {w: (m, f"{c}/{k1}/{w}") for w, (m, c) in S473.K1_WORKERS.items()}
    workers["studio_1145" + "1"] = ("studio", f"projects/mentori-runs-k1-1145{1}/{k1}/studio_1145{1}")
    workers[Q7_WORKER] = ("beelink", f"projects/mentori-runs-k1-q7/{k1}/{Q7_WORKER}")
    logs = {"k1": {}}
    for w, (machine, base) in workers.items():
        logs["k1"][w] = S473.fetch(machine, [[f"{base}/{f}", f] for f in S473.K1_FILES], [], to / "k1" / w)
    l1 = "projects/mentori-runs-l1/findings/recompute/L1"
    logs["l1"] = S473.fetch("studio", [[f"{l1}/header.json", "header.json"]],
                            [[f"{l1}/{s}", s, ["*.jsonl"]] for s in ("key", "papers", "overlap")], to / "l1")
    import shutil
    for n in ("assignment.json", "amendments.json"):
        shutil.copy(REC / "K1" / n, to / "k1" / n)
    (to / "PULL.json").write_text(json.dumps({"script": SCRIPT, "ended_utc": S473.utc_now(), "logs": logs}, indent=1)
                                  + "\n")
    print(f"pulled into {to}: K1 {len(logs['k1'])} workers, L1 {len(logs['l1']['files'])} files")


# ---------------------------------------------------------------------------------------------------------------
# selftest: made-up rows only; the gate on S473's e rows is run by S497's selftest, on the frozen rows
# ---------------------------------------------------------------------------------------------------------------
def selftest() -> int:
    import random
    rng = random.Random(192)
    fails = 0

    def check(name, good):
        nonlocal fails
        fails += 0 if good else 1
        print(f"  {'PASS' if good else 'FAIL'}    {name}")
    pts = [(f"q{i // 6}", rng.randint(0, 5), rng.random()) for i in range(120)]
    try:
        print(f"  PASS    {check_rho_box(pts)}")
    except Refused as e:
        fails += 1
        print(f"  FAIL    {e}")
    tied = [(f"q{i // 6}", i % 3, (i // 2) % 4) for i in range(60)]
    try:
        print(f"  PASS    {check_rho_box(tied)}")
    except Refused as e:
        fails += 1
        print(f"  FAIL    tied values: {e}")
    same = [(f"q{i // 6}", v := rng.random(), v) for i in range(120)]
    check("within_rho: two identical columns give 1", abs(within_rho(same) - 1) < 1e-12)
    rows = [(q, x) for q in range(400) for x in [rng.random() for _ in range(6)]]
    by: dict = {}
    for q, x in rows:
        by.setdefault(q, []).append(x)
    shuffled = []
    for q, v in by.items():
        w = list(v)
        rng.shuffle(w)
        shuffled += [(q, a, b) for a, b in zip(v, w)]
    check("within_rho: a column shuffled within each question gives about 0", abs(within_rho(shuffled)) < 0.05)
    print(f"selftest: {'all pass' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    t = sub.add_parser("timing")
    t.add_argument("--k1", help="a folder as fig5_d200_inputs/k1 (default that frozen folder)")
    p = sub.add_parser("pull")
    p.add_argument("--to", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "pull":
        pull(a.to)
        return 0
    k1 = Path(a.k1) if a.k1 else s473().FR.frozen("fig5_d200", "k1")
    print(json.dumps(write_timing(k1), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
