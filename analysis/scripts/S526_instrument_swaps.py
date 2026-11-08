#!/usr/bin/env python3
"""S526 - the swaps behind the thesis (D194): how far each change of measure or set-up moves RLM-10 minus single pass.

WHY. D194 builds the abstract and Discussion on "how a RAG system is implemented and measured moves results more than
the choice of strategy". Its numbers came from two scratch scripts, findings/audits/rerun_story_2026-11-01/scripts/
instr.py and recount3.py, which hard-coded the laptop path and read the live S6 clone (tracked-scripts audit, row 1).
This script is their port: same calculations, repository paths, frozen inputs, a provenance block and the gates kept.

WHAT IT COMPUTES. "Gap" is RLM-10 minus single pass, in points, on the same questions. A swap holds the answers fixed and
changes one thing. compare() gives both arms' means per strategy, the gap in each arm, the change in the gap with a 95%
interval (10,000 resamples of the questions, seed 20261013), both rankings, their Spearman correlation and the winners.
  judge      pass mark 3, 4 or 5; plain call against the call with passages; old judge against devstral
  MiniCheck  against the key against the papers (precision, as stored); source-list lines kept or dropped, by filtered(),
             the approximate filter of instr.py, draw 1. scripts/minicheck_filter.py is the final rule and is not used here
  signal     judge pass at 4 against concept recall (D181, key v2.5)
  RLM        Mentori RLM against the package at caps 5, 10, 20 (concept recall, D181)
  key        v2.4 against v2.5, judge and concepts
  ladder     recount3.py's pass rates: April answers with April's judge, April answers with devstral on key v2.4, and
             the re-run, each at marks 4 and 3 on all 86, the 60 one-paper and the 26 many-paper questions; concept
             recall and MiniCheck on the April answers; G4 at 5, 10, 20 and 50 papers

LEFT OUT OF THE PORT. instr.py's "S404" block (four judges on older answers, lines 362-399): it is not behind any number
of the thesis, and S405 is that comparison's committed source. No score of a second judge enters this script.

WHAT IT READS. The files class Inputs records, each hashed into the provenance: frozen sets through fig_repro.frozen (the S6
rows from findings/recompute/fig3_s6_inputs/, S528's freeze), tracked outputs by repository path, the W-question list
copied from the plate of 1 November, inputs/W_questions_d166.json, because S497 will rebuild that plate, and the two key
files experiment.questions and scaling_questions open (KEY_V24, KEY_D5), which set the question sets. No T2 row, second-judge
row, rater file or live clone: an audit hook refuses them (S521.FORBIDDEN_RE plus the closed scratch files of the
rerun story), and the test greps this source.

REPRODUCE BEFORE WRITING (README.md:75-79). Nothing is written unless reproduce() holds: instr.py's 12 pass rates and the
pooled Papers median on the W set, then every row of TARGETS: +15.4, +10.9, 17.6, 33.7 and 83.3 with their intervals.

WRITES. results.json (provenance, gates, the thesis numbers, every swap, the ladder) and results.md, under --out, default
findings/recompute/S526_instrument_swaps/. No date and no commit in them, so one set of inputs gives one set of bytes.

    uv run --frozen python scripts/S526_instrument_swaps.py [--out DIR]
    uv run --frozen python scripts/S526_instrument_swaps_test.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent
for _p in (str(SCRIPTS), str(REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fig_repro as FR  # noqa: E402
import S521_valerio_reading_pack as S521  # noqa: E402  (its closed-path list; S521 imports only the standard library)

SCRIPT = "scripts/S526_instrument_swaps.py"
COMMAND = "uv run --frozen python scripts/S526_instrument_swaps.py"
RECOMPUTE = REPO / "findings/recompute"
OUT = RECOMPUTE / "S526_instrument_swaps"
W_FILE = OUT / "inputs/W_questions_d166.json"
SEED, B = 20261013, 10000                       # instruments.md:3
S = ["single_pass", "verified_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20"]
CAPS = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50]
CLOSED_SCRATCH = re.compile(r"rerun_story_2026-11-01/(recommend\.md|scripts/rec_)")
KEY_FILE, G1_COLLECT, G4_COLLECT, S6_COLLECT = ("l1/key/key.shard0of1.jsonl", "g1_collect.jsonl", "g4_collect.jsonl",
                                                "s6_g1_collect.jsonl")
TRACKED = {"S406": "S406_exp04_per_answer_v24.csv", "S281": "S281_exp04_per_answer.csv",
           "L3": "L3/concept_recall.jsonl", "L3_d181": "L3_d181/concept_recall.jsonl",
           "L2": "L2_d135_d181/concept_recall.jsonl", "L2_loose": "L2_d135/concept_recall.jsonl",
           "L2_g7": "L2_d135_d181_g7/concept_recall_g7.jsonl"}
WANT_PASS = {4: dict(single_pass=83.3, verified_pass=82.9, multi_hop=79.5, rlm_10=74.8, rlm_5=71.7, rlm_20=71.3),
             3: dict(single_pass=93.4, verified_pass=93.0, multi_hop=95.0, rlm_10=92.2, rlm_5=93.4, rlm_20=93.8)}
WANT_MEDIAN = (495, 0.6562)                     # instruments.md:30, Figure 5b


class GateFail(Exception):
    """A number did not reproduce; nothing is written (exit 1)."""


class Refused(Exception):
    """A closed path or an unexpected row (exit 2)."""


def closed(path) -> bool:
    text = os.fsdecode(path) if isinstance(path, (bytes, os.PathLike)) else str(path)
    return S521.is_forbidden(text) or bool(CLOSED_SCRATCH.search(text))


_guard_on = False


def install_guard() -> None:
    """From here on, opening a closed path raises in this process."""
    global _guard_on
    if _guard_on:
        return

    def hook(event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)) and closed(args[0]):
            raise Refused(f"guard: {os.fsdecode(args[0])} is closed to this script")

    sys.addaudithook(hook)
    _guard_on = True


# ---------------------------------------------------------------- the calculations of instr.py
def boot(vals, fn=np.mean):
    vals = np.asarray(vals, float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(vals), (B, len(vals)))
    est = vals[idx].mean(axis=1)
    return round(float(vals.mean()), 2), round(float(np.percentile(est, 2.5)), 2), round(float(np.percentile(est, 97.5)), 2)


def rank_desc(d):
    """1 = highest; ties share the mean rank."""
    keys = list(d)
    vals = np.array([d[k] for k in keys])
    return {k: 1 + (vals > d[k]).sum() + ((vals == d[k]).sum() - 1) / 2 for k in keys}


def spearman(a, b):
    k = list(a)
    x = np.array([rank_desc(a)[i] for i in k])
    y = np.array([rank_desc(b)[i] for i in k])
    if x.std() == 0 or y.std() == 0:
        return None
    return round(float(np.corrcoef(x, y)[0, 1]), 3)


def table(mat, qs):
    """mat[(q, config)] -> value; the mean per strategy over qs."""
    return {c: float(np.mean([mat[(q, c)] for q in qs])) for c in S}


def compare(res, name, A, B_, qs, pair=("rlm_10", "single_pass"), noise=None):
    """A, B_: {(question, config): value in points}; qs: the paired questions. One row of res."""
    ta, tb = table(A, qs), table(B_, qs)
    da = np.array([A[(q, pair[0])] - A[(q, pair[1])] for q in qs])
    db = np.array([B_[(q, pair[0])] - B_[(q, pair[1])] for q in qs])
    shift = {c: round(tb[c] - ta[c], 1) for c in S}
    out = {"name": name, "n_q": len(qs), "A": {k: round(v, 1) for k, v in ta.items()},
           "B": {k: round(v, 1) for k, v in tb.items()}, "shift_per_strategy": shift,
           "abs_mean_shift": round(float(np.mean([abs(v) for v in shift.values()])), 1),
           "contrast": f"{pair[0]} minus {pair[1]}", "contrast_A": boot(da), "contrast_B": boot(db),
           "contrast_change_B_minus_A": boot(db - da),
           "rank_A": {k: float(v) for k, v in sorted(rank_desc(ta).items(), key=lambda x: x[1])},
           "rank_B": {k: float(v) for k, v in sorted(rank_desc(tb).items(), key=lambda x: x[1])},
           "spearman_rank_A_B": spearman(ta, tb), "winner_A": max(ta, key=ta.get), "winner_B": max(tb, key=tb.get),
           "rank_moves_sum": float(sum(abs(rank_desc(ta)[c] - rank_desc(tb)[c]) for c in S))}
    if noise is not None:
        out["noise"] = noise
    res[name] = out
    return out


def score(r, call, dim):
    x = r.get(call) or {}
    if x.get("status") == "ok" and x.get("scores"):
        return x["scores"].get(dim)
    return None


def passmat(rows, thr, qs, call="a", draws=(1, 2, 3), left_out_missing=False):
    """{(q, config): % of draws at or above thr}. A missing score counts as a fail unless left_out_missing."""
    m = {}
    for q in qs:
        for c in S:
            v = []
            for d in draws:
                s = score(rows[(q, c, d)], call, "correctness")
                if s is None:
                    if left_out_missing:
                        continue
                    v.append(0.0)
                else:
                    v.append(100.0 if s >= thr else 0.0)
            m[(q, c)] = float(np.mean(v)) if v else np.nan
    return m


def per_draw_contrast(fn, qs, pair=("rlm_10", "single_pass"), draws=(1, 2, 3)):
    out, vecs = {}, {}
    for d in draws:
        m = fn(d)
        v = np.array([m[(q, pair[0])] - m[(q, pair[1])] for q in qs])
        vecs[d] = v
        out[d] = round(float(v.mean()), 1)
    return {"per_draw": out, "range": round(max(out.values()) - min(out.values()), 1)}, vecs


def kname(q, c, d):
    return f"exp_v4_s20_n0|{c}|{q}|d{d}"


SRC_HEAD = re.compile(r"^[\W_]*(sources?|references?)\b.{0,40}$", re.I)
NUM_LINE = re.compile(r"^\W*\[?\d+\]?[\.\)]?\s+.*(\.pdf|Document:|page \d|\(unverified\)|\(verified\))", re.I)
SRC_LINE2 = re.compile(r"^\[\d+\]")


def filtered(items, text="claim"):
    """instr.py's approximate filter: drop the trailing source list, from the first heading 'Sources ...' or the first
    numbered source line that begins a run of short or '[n] ' lines, after the first fifth, to the end."""
    cut = None
    for i, it in enumerate(items):
        t = (it.get(text) or "").strip()
        if SRC_HEAD.match(t) or (NUM_LINE.match(t) and i >= len(items) * 0.2 and all(
                SRC_LINE2.match((x.get(text) or "").strip()) or SRC_HEAD.match((x.get(text) or "").strip())
                or len(x.get(text) or "") < 80 for x in items[i:])):
            cut = i
            break
    keep = items if cut is None else items[:cut]
    return keep, len(items) - len(keep)


def mc_tables(papers, keyr, qs):
    M = {k: {} for k in ("papers_prec", "key_prec", "key_f1", "key_rec", "papers_prec_nosrc", "key_prec_nosrc")}
    drop = collections.defaultdict(lambda: [0, 0])
    for q in qs:
        for c in S:
            k = kname(q, c, 1)
            p, r = papers.get(k), keyr.get(k)
            if p is not None and p["signals"].get("precision") is not None:
                M["papers_prec"][(q, c)] = 100 * p["signals"]["precision"]
                pc = p["detail"].get("per_claim") or []
                keep, dr = filtered(pc)
                drop[c][0] += dr
                drop[c][1] += len(pc)
                if keep:
                    M["papers_prec_nosrc"][(q, c)] = 100 * sum(1 for x in keep if x["supported"]) / len(keep)
            if r is not None and r["signals"].get("precision") is not None:
                M["key_prec"][(q, c)] = 100 * r["signals"]["precision"]
                if r["signals"].get("f1") is not None:
                    M["key_f1"][(q, c)] = 100 * r["signals"]["f1"]
                if r["signals"].get("recall") is not None:
                    M["key_rec"][(q, c)] = 100 * r["signals"]["recall"]
                keep, _ = filtered(r["detail"].get("precision_details") or [], text="sentence")
                if keep:
                    M["key_prec_nosrc"][(q, c)] = 100 * sum(1 for x in keep if x["supported"]) / len(keep)
    return M, {k: round(v[0] / max(v[1], 1), 3) for k, v in drop.items()}


def conceptmat(src, field, qs, draws=(1, 2, 3)):
    m = {}
    for q in qs:
        for c in S:
            v = [src[(q, c, d)].get(field) for d in draws]
            m[(q, c)] = 100 * float(np.mean([0.0 if x is None else float(x) for x in v]))
    return m


def l2vec(src, sysn, cap, qs, draws=(1, 2, 3), field="concept_recall"):
    out = []
    for q in qs:
        v = [src[(sysn, cap, q, d)].get(field) for d in draws if (sysn, cap, q, d) in src]
        out.append(100 * float(np.mean([0.0 if x is None else float(x) for x in v])))
    return np.array(out)


# ---------------------------------------------------------------- inputs
def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(x for x in f if not x.startswith("#")))


class Inputs:
    """Every file this script reads, with its sha256 for the provenance."""

    def __init__(self):
        self.sha = {}

    def frozen(self, set_name, rel_path):
        """A committed frozen set's file: fig_repro.frozen checks a set with its own SHA256SUMS, check_committed the rest."""
        p = FR.frozen(set_name, rel_path)
        if not (RECOMPUTE / f"{set_name}_inputs" / "SHA256SUMS").exists():
            FR.check_committed(p)
        for f in ([p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file())):
            self.sha[FR.frozen_label(f)] = FR.sha256_file(f)
        return p

    def tracked(self, path: Path):
        self.sha[path.relative_to(REPO).as_posix()] = FR.sha256_file(path)
        return path


def only_main_judge(rows, where):
    """No row of a second judge reaches a calculation: a main-judge row carries no "judge" field (judge_rows_v25.check_v24)."""
    bad = [r.get("answer_key") for r in rows if r.get("judge") is not None]
    if bad:
        raise Refused(f"{where}: {len(bad)} rows name a judge, first {bad[:2]}")
    return rows


def concept_index(rows):
    return {(r["question_id"], r["config"], int(r["draw"])): r for r in rows}


def l2_index(rows):
    return {(r["system"], int(r["cap"]), r["question_id"], int(r["draw"])): r for r in rows}


# ---------------------------------------------------------------- the ladder of recount3.py
def rate(rows, col, thr, qset, cfg="config"):
    """% at or above thr per strategy, and how many rows; a blank is left out, as recount3.py did."""
    res = {}
    for st in S:
        v = [float(r[col]) >= thr for r in rows if r[cfg] == st and r["question_id"] in qset
             and r[col] not in ("", None, "NA", "None")]
        res[st] = (round(100 * sum(v) / len(v), 1), len(v)) if v else None
    return res


def mean_col(rows, col, qset):
    res = {}
    for st in S:
        v = [float(r[col]) for r in rows if r["config"] == st and r["question_id"] in qset
             and r[col] not in ("", None, "NA", "None")]
        res[st] = round(100 * sum(v) / len(v), 1) if v else None
    return res


def ladder(rows406, rows281, g4, sets):
    from experiments.runner import experiment as ex
    out = {"april_answers_devstral_v24": {}, "april_answers_april_judge": {}}
    col281 = [c for c in rows281[0] if "correct" in c.lower()][0]                 # correctness_published
    out["april_judge_column"] = col281
    for name, qset in sets.items():
        out["april_answers_devstral_v24"][name] = {thr: rate(rows406, "judge_correctness", thr, qset) for thr in (4, 3)}
        out["april_answers_april_judge"][name] = {thr: rate(rows281, col281, thr, qset) for thr in (4, 3)}
    everything = sets["all86"]
    out["april_concept_recall_v24"] = {c: mean_col(rows406, c, everything)
                                       for c in ("det_concept_recall", "det_concept_recall_loose")}
    out["april_minicheck"] = {c: mean_col(rows406, c, everything)
                              for c in ("mc_key_precision", "mc_key_s19_precision", "mc_source_k3_precision",
                                        "mc_source_fulldoc_precision")}
    grid = {}
    for core in (5, 10, 20, 50):
        sq = ex.scaling_questions(core)
        per = [q["id"] for q in sq["per_size"] if q["answer_type"] in ("extractive", "synthesis")]
        perone = {q["id"] for q in sq["per_size"] if q["answer_type"] == "extractive"}
        for noise in ("n0", "n1", "n3"):
            idx = f"exp_v4_s{core}_{noise}"
            for thr in (4, 3):
                cell = {}
                for st in ("single_pass", "rlm_10", "verified_pass"):
                    v = []
                    for r in g4:
                        if r["run_id"].endswith(idx) and r["config"] == st and r["question_id"] in per:
                            s = ((r.get("a") or {}).get("scores") or {}).get("correctness")
                            v.append(1 if s is not None and s >= thr else 0)
                    cell[st] = (round(100 * sum(v) / len(v), 1), len(v)) if v else None
                grid[f"{idx} at {thr}"] = {"questions": len(per), "one_paper": len(perone), "pass": cell}
    out["g4_in_scope_answerable"] = grid
    return out


# ---------------------------------------------------------------- everything
def compute(inp: Inputs) -> dict:
    res = {}
    key_rows = read_jsonl(inp.frozen("fig5_1028", KEY_FILE))
    group = {r["question_id"]: r["group"] for r in key_rows}
    Q86 = sorted(q for q, g in group.items() if g == "answerable")
    ONE = [q for q in Q86 if not re.match(r"^(CD|SY)_", q)]
    MANY = [q for q in Q86 if re.match(r"^(CD|SY)_", q)]
    if (len(Q86), len(ONE), len(MANY)) != (86, 60, 26):
        raise GateFail(f"questions: {len(Q86)}, {len(ONE)}, {len(MANY)}, want 86, 60, 26")

    g1 = only_main_judge(read_jsonl(inp.frozen("fig2", G1_COLLECT)), G1_COLLECT)
    AA = {(r["question_id"], r["config"], int(r["draw"])): r for r in g1}
    pm = lambda thr, **k: passmat(AA, thr, k.pop("qs", Q86), **k)            # noqa: E731

    res["pass_table_at_4"] = {k: round(v, 1) for k, v in table(pm(4), Q86).items()}
    res["pass_table_at_3"] = {k: round(v, 1) for k, v in table(pm(3), Q86).items()}
    P4, P3, P5 = pm(4), pm(3), pm(5)
    NOISE_J4, vec_j4 = per_draw_contrast(lambda d: pm(4, draws=(d,)), Q86)
    NOISE_J3, vec_j3 = per_draw_contrast(lambda d: pm(3, draws=(d,)), Q86)
    res["noise_judge4_strategy_per_draw"] = {c: [round(float(np.mean([pm(4, draws=(d,))[(q, c)] for q in Q86])), 1)
                                                 for d in (1, 2, 3)] for c in S}
    res["noise_judge4_contrast"] = NOISE_J4
    res["noise_judge3_contrast"] = NOISE_J3
    pairs = [(1, 2), (1, 3), (2, 3)]
    res["noise_judge4_draw_pairs"] = {f"d{i}-d{j}": boot(vec_j4[i] - vec_j4[j]) for i, j in pairs}
    res["noise_judge3_draw_pairs"] = {f"d{i}-d{j}": boot(vec_j3[i] - vec_j3[j]) for i, j in pairs}

    # pass mark
    compare(res, "pass mark 4 to 3, all 86", P4, P3, Q86, noise=NOISE_J4)
    compare(res, "pass mark 4 to 3, one-paper 60", P4, P3, ONE)
    compare(res, "pass mark 4 to 3, many-paper 26", P4, P3, MANY)
    compare(res, "pass mark 4 to 5, all 86", P4, P5, Q86)

    # plain call against the call with passages
    Pb4, Pb3 = pm(4, call="b", left_out_missing=True), pm(3, call="b", left_out_missing=True)
    compare(res, "judge plain to passages, pass at 4", P4, Pb4, Q86, noise=NOISE_J4)
    compare(res, "judge plain to passages, pass at 3", P3, Pb3, Q86, noise=NOISE_J3)
    compare(res, "judge plain to passages, one-paper, pass at 4", P4, Pb4, ONE)
    compare(res, "judge plain to passages, many-paper, pass at 4", P4, Pb4, MANY)

    def dimmat(dim, call, draws=(1, 2, 3), scale=20.0):
        m = {}
        for q in Q86:
            for c in S:
                v = [score(AA[(q, c, d)], call, dim) for d in draws]
                v = [x for x in v if x is not None]
                m[(q, c)] = float(np.mean(v)) * scale if v else np.nan
        return m

    for dim in ("faithfulness", "citation_quality", "correctness", "completeness"):
        a, b = dimmat(dim, "a"), dimmat(dim, "b")
        qs = [q for q in Q86 if all(not np.isnan(a[(q, c)]) and not np.isnan(b[(q, c)]) for c in S)]
        compare(res, f"judge plain to passages, mean {dim} (0-100 scale, score x 20)", a, b, qs)
        for call in ("a", "b"):
            pd = {}
            for d in (1, 2, 3):
                m = dimmat(dim, call, (d,))
                q2 = [q for q in Q86 if not np.isnan(m[(q, "rlm_10")]) and not np.isnan(m[(q, "single_pass")])]
                pd[d] = round(float(np.mean([m[(q, "rlm_10")] - m[(q, "single_pass")] for q in q2])), 1)
            res[f"per_draw_rlm10_minus_sp_{dim}_{call}"] = pd

    # MiniCheck against the key and the papers
    papers = {}
    pdir = inp.frozen("fig5_1028", "l1/papers")
    for f in sorted(pdir.glob("*.jsonl")):
        for r in read_jsonl(f):
            papers[r["answer_key"]] = r
    keyr = {r["answer_key"]: r for r in key_rows}
    MC, dropshare = mc_tables(papers, keyr, Q86)
    res["minicheck_source_lines_dropped_share_of_claims"] = dropshare
    Wq = [q for q in Q86 if all((q, c) in MC["papers_prec"] and (q, c) in MC["key_prec"] for c in S)]
    WqF = [q for q in Wq if all((q, c) in MC["key_f1"] for c in S)]
    Wq2 = [q for q in Wq if all((q, c) in MC["papers_prec_nosrc"] and (q, c) in MC["key_prec_nosrc"] for c in S)]
    res["minicheck_paired_questions"] = len(Wq)
    res["minicheck_paired_questions_nosrc"] = len(Wq2)
    W_fig = set(json.loads(inp.tracked(W_FILE).read_text())["W_questions"])
    res["W_fig_n"] = len(W_fig)
    pool = [MC["papers_prec"][(q, c)] for q in sorted(W_fig) for c in S if (q, c) in MC["papers_prec"]]
    res["gate_papers_median_on_W"] = (len(pool), round(float(np.median(pool)) / 100, 4))

    def mck(d, field="precision"):
        m = {}
        for q in Q86:
            for c in S:
                v = keyr[kname(q, c, d)]["signals"].get(field)
                m[(q, c)] = 100 * v if v is not None else np.nan
        return m

    per = {}
    for d in (1, 2, 3):
        m = mck(d)
        good = [q for q in Q86 if not np.isnan(m[(q, "rlm_10")]) and not np.isnan(m[(q, "single_pass")])]
        per[d] = round(float(np.mean([m[(q, "rlm_10")] - m[(q, "single_pass")] for q in good])), 1)
    NOISE_MC = {"per_draw": per, "range": round(max(per.values()) - min(per.values()), 1)}
    res["noise_mc_key_precision_contrast"] = NOISE_MC
    res["noise_mc_key_precision_strategy_means"] = {
        d: {c: round(float(np.mean([v for q in Q86 if not np.isnan(v := mck(d)[(q, c)])])), 1) for c in S} for d in (1, 2, 3)}

    compare(res, "MiniCheck key to papers precision, as stored (draw 1)", MC["key_prec"], MC["papers_prec"], Wq, noise=NOISE_MC)
    compare(res, "MiniCheck key to papers precision, source lists dropped (draw 1)", MC["key_prec_nosrc"],
            MC["papers_prec_nosrc"], Wq2, noise=NOISE_MC)
    compare(res, "MiniCheck key F1 to papers precision, as stored (draw 1)", MC["key_f1"], MC["papers_prec"], WqF)
    compare(res, "MiniCheck papers precision, source lists kept to dropped", MC["papers_prec"], MC["papers_prec_nosrc"], Wq2)
    compare(res, "MiniCheck key to papers, as stored, verified_pass minus rlm_10", MC["key_prec"], MC["papers_prec"], Wq,
            pair=("verified_pass", "rlm_10"))
    compare(res, "MiniCheck key to papers, source dropped, one-paper", MC["key_prec_nosrc"], MC["papers_prec_nosrc"],
            [q for q in Wq2 if q in ONE])
    compare(res, "MiniCheck key to papers, source dropped, many-paper", MC["key_prec_nosrc"], MC["papers_prec_nosrc"],
            [q for q in Wq2 if q in MANY])
    xs = [(MC["key_prec"][(q, c)], MC["papers_prec"][(q, c)]) for q in Wq for c in S]
    res["minicheck_answer_pearson"] = round(float(np.corrcoef(np.array(xs).T)[0, 1]), 3)

    # the submitted answers
    rows406_all = read_csv(inp.tracked(RECOMPUTE / TRACKED["S406"]))
    rows406 = [r for r in rows406_all if r["group"] == "answerable"]
    res["s406_answerable"] = len(rows406)

    def s406mat(col, tf=float):
        return {(r["question_id"], r["config"]): tf(r[col]) for r in rows406 if r[col] not in ("", "None", "nan")}

    K = s406mat("mc_key_precision", lambda x: 100 * float(x))
    KF = s406mat("mc_key_f1", lambda x: 100 * float(x))
    P3k = s406mat("mc_source_k3_precision", lambda x: 100 * float(x))
    qe = [q for q in sorted({q for q, _ in K}) if all((q, c) in K and (q, c) in P3k and (q, c) in KF for c in S)]
    compare(res, "exp04 MiniCheck key precision to source k3 precision", K, P3k, qe)
    compare(res, "exp04 MiniCheck key F1 to source k3 precision", KF, P3k, qe)
    compare(res, "exp04 MiniCheck key F1 to source k3, verified_pass minus rlm_10", KF, P3k, qe, pair=("verified_pass", "rlm_10"))

    # old judge against devstral, same answers
    rows281 = read_csv(inp.tracked(RECOMPUTE / TRACKED["S281"]))
    oldpub = {(r["question_id"], r["config"]): float(r["correctness_published"]) for r in rows281}
    oldcor = {(r["question_id"], r["config"]): float(r["correctness_corrected"]) for r in rows281}
    dev = {(r["question_id"], r["config"]): float(r["judge_correctness"]) for r in rows406
           if r["judge_correctness"] not in ("", "None")}
    common = [q for q in sorted({q for q, _ in dev} & {q for q, _ in oldcor})
              if all((q, c) in dev and (q, c) in oldcor for c in S)]
    res["old_judge_common_questions"] = len(common)
    for thr in (3, 4):
        mk = lambda m: {k: 100.0 if v >= thr else 0.0 for k, v in m.items()}   # noqa: E731
        compare(res, f"old judge (corrected state, key v1) to devstral (key v2.4), exp04, pass at {thr}", mk(oldcor), mk(dev), common)
        compare(res, f"old judge (published, key v1) to devstral (key v2.4), exp04, pass at {thr}", mk(oldpub), mk(dev), common)
        compare(res, f"old judge to devstral, exp04, verified_pass minus rlm_10, at {thr}", mk(oldcor), mk(dev), common,
                pair=("verified_pass", "rlm_10"))
        d4, r4 = mk(dev), pm(thr)
        qq = [q for q in Q86 if all((q, c) in d4 for c in S)]
        compare(res, f"submitted answers (exp04) to re-run (G1 3 draws), devstral v2.4, pass at {thr}", d4, r4, qq,
                noise=NOISE_J4 if thr == 4 else NOISE_J3)

    # key v2.4 to v2.5: the frozen S6G1 rows, read as s3_guard collect kept them (latest row, the G1R15 reruns replacing)
    s6rows = only_main_judge(read_jsonl(inp.frozen("fig3_s6", S6_COLLECT)), S6_COLLECT)
    if {r.get("key_version") for r in s6rows} != {"v2.5"}:
        raise Refused("a row of the S6 collect is not on key v2.5")
    s6 = {(r["question_id"], r["config"], int(r["draw"])): r for r in s6rows}
    res["s6_rows_answers"] = len(s6)
    res["s6_latest_at"] = max(r["at"] for r in s6rows if r.get("at"))
    changed_all = {k[0] for k in s6}
    CH = [q for q in Q86 if q in changed_all and all((q, c, d) in s6 for c in S for d in (1, 2, 3))]
    res["s6_changed_answerable_complete"] = len(CH)
    res["s6_changed_all_questions"] = len(changed_all)
    res["s6_unchanged_answerable"] = len([q for q in Q86 if q not in changed_all])
    res["s6_a_status"] = dict(collections.Counter((r.get("a") or {}).get("status") for r in s6.values()))
    res["s6_answer_key_mismatch"] = sum(1 for k, r in s6.items() if k in AA and AA[k]["answer_key"] != r["answer_key"])

    def passmat_v25(thr, qs, draws=(1, 2, 3)):
        m = {}
        for q in qs:
            for c in S:
                v = []
                for d in draws:
                    s = score(s6.get((q, c, d)) or AA[(q, c, d)], "a", "correctness")
                    v.append(0.0 if s is None else (100.0 if s >= thr else 0.0))
                m[(q, c)] = float(np.mean(v))
        return m

    for thr in (4, 3):
        nz, _ = per_draw_contrast(lambda d: pm(thr, qs=CH, draws=(d,)), CH)
        compare(res, f"key v2.4 to v2.5, judge plain, changed answerable, pass at {thr}", pm(thr, qs=CH), passmat_v25(thr, CH), CH, noise=nz)
        compare(res, f"key v2.4 to v2.5, judge plain, all 86, pass at {thr}", pm(thr), passmat_v25(thr, Q86), Q86,
                noise=NOISE_J4 if thr == 4 else NOISE_J3)
        compare(res, f"key v2.4 to v2.5, judge plain, one-paper, pass at {thr}", pm(thr), passmat_v25(thr, Q86), ONE)
        compare(res, f"key v2.4 to v2.5, judge plain, many-paper, pass at {thr}", pm(thr), passmat_v25(thr, Q86), MANY)
        nz2 = {}
        for d in (1, 2, 3):
            m = passmat_v25(thr, Q86, draws=(d,))
            nz2[d] = round(float(np.mean([m[(q, "rlm_10")] - m[(q, "single_pass")] for q in Q86])), 1)
        res[f"noise_v25_contrast_at_{thr}"] = {"per_draw": nz2, "range": round(max(nz2.values()) - min(nz2.values()), 1)}
        res[f"v25_pass_table_at_{thr}"] = {k: round(v, 1) for k, v in table(passmat_v25(thr, Q86), Q86).items()}

    # concept recall
    L3 = concept_index(read_jsonl(inp.tracked(RECOMPUTE / TRACKED["L3"])))
    L3d = concept_index(read_jsonl(inp.tracked(RECOMPUTE / TRACKED["L3_d181"])))
    c24, c25b, c25 = (conceptmat(L3, "concept_recall_loose", Q86), conceptmat(L3d, "concept_recall_loose_base", Q86),
                      conceptmat(L3d, "concept_recall", Q86))
    nzc = {}
    for d in (1, 2, 3):
        m = conceptmat(L3d, "concept_recall", Q86, draws=(d,))
        nzc[d] = round(float(np.mean([m[(q, "rlm_10")] - m[(q, "single_pass")] for q in Q86])), 1)
    NOISE_C = {"per_draw": nzc, "range": round(max(nzc.values()) - min(nzc.values()), 1)}
    res["noise_concept_d181_contrast"] = NOISE_C
    compare(res, "concept v2.4 loose to v2.5 D181, all 86", c24, c25, Q86, noise=NOISE_C)
    compare(res, "concept v2.4 loose to v2.5 loose base (key only), all 86", c24, c25b, Q86, noise=NOISE_C)
    compare(res, "concept v2.5 loose base to v2.5 D181 (question rule only), all 86", c25b, c25, Q86, noise=NOISE_C)
    compare(res, "concept v2.4 loose to v2.5 D181, changed judge questions", c24, c25, CH, noise=NOISE_C)
    compare(res, "concept v2.4 loose to v2.5 D181, one-paper", c24, c25, ONE)
    compare(res, "concept v2.4 loose to v2.5 D181, many-paper", c24, c25, MANY)
    compare(res, "signal swap: judge pass at 4 to concept recall D181, all 86", P4, c25, Q86, noise=NOISE_J4)
    compare(res, "signal swap: judge pass at 4 to concept recall D181, one-paper", P4, c25, ONE)
    compare(res, "signal swap: judge pass at 4 to concept recall D181, many-paper", P4, c25, MANY)

    # the two RLMs
    L2rows = read_jsonl(inp.tracked(RECOMPUTE / TRACKED["L2"]))
    L2 = l2_index(L2rows)
    L2l_rows = read_jsonl(inp.tracked(RECOMPUTE / TRACKED["L2_loose"]))
    res["l2_loose_fields"] = [k for k in L2l_rows[-1] if "concept" in k]
    res["g7_rows"] = len({(r.get("system"), int(r["cap"]), r["question_id"], int(r["draw"]))
                          for r in read_jsonl(inp.tracked(RECOMPUTE / TRACKED["L2_g7"]))})
    l2 = lambda sysn, cap, qs=Q86, draws=(1, 2, 3): l2vec(L2, sysn, cap, qs, draws)   # noqa: E731
    rl = {}
    for cap in CAPS:
        g5, g6 = l2("G5", cap, draws=(1,)), l2("G6", cap)
        g6d = [l2("G6", cap, draws=(d,)) for d in (1, 2, 3)]
        rl[cap] = {"G5_d1": round(float(g5.mean()), 1), "G6_3d": round(float(g6.mean()), 1), "G5_minus_G6": boot(g5 - g6),
                   "G6_by_draw": [round(float(x.mean()), 1) for x in g6d],
                   "G5_d1_minus_G6_d1": round(float((g5 - g6d[0]).mean()), 1),
                   "G5_minus_G6_one": boot(l2("G5", cap, ONE, (1,)) - l2("G6", cap, ONE)),
                   "G5_minus_G6_many": boot(l2("G5", cap, MANY, (1,)) - l2("G6", cap, MANY))}
    res["rlm_by_cap_d181"] = rl
    m = conceptmat(L3d, "concept_recall", Q86)
    for cap, conf in ((5, "rlm_5"), (10, "rlm_10"), (20, "rlm_20")):
        v = np.array([m[(q, conf)] for q in Q86])
        sp = np.array([m[(q, "single_pass")] for q in Q86])
        vone, vmany = (np.array([m[(q, conf)] for q in x]) for x in (ONE, MANY))
        spone, spmany = (np.array([m[(q, "single_pass")] for q in x]) for x in (ONE, MANY))
        g6, g5 = l2("G6", cap), l2("G5", cap, draws=(1,))
        row = {"G1_mentori_3d": round(float(v.mean()), 1), "G6_package_3d": round(float(g6.mean()), 1),
               "SP": round(float(sp.mean()), 1), "G1_minus_G6": boot(v - g6), "G1_minus_SP": boot(v - sp),
               "G6_minus_SP": boot(g6 - sp), "interaction": boot((v - sp) - (g6 - sp)),
               "one_paper": {"G1": round(float(vone.mean()), 1), "G6": round(float(l2("G6", cap, ONE).mean()), 1),
                             "SP": round(float(spone.mean()), 1), "G1_minus_G6": boot(vone - l2("G6", cap, ONE)),
                             "G6_minus_SP": boot(l2("G6", cap, ONE) - spone)},
               "many_paper": {"G1": round(float(vmany.mean()), 1), "G6": round(float(l2("G6", cap, MANY).mean()), 1),
                              "SP": round(float(spmany.mean()), 1), "G1_minus_G6": boot(vmany - l2("G6", cap, MANY)),
                              "G6_minus_SP": boot(l2("G6", cap, MANY) - spmany)}}
        vd = [np.array([100 * float(L3d[(q, conf, d)].get("concept_recall") or 0) for q in Q86]) for d in (1, 2, 3)]
        gd = [l2("G6", cap, draws=(d,)) for d in (1, 2, 3)]
        row["same_software_G1_d1_minus_G5_d1"] = boot(vd[0] - g5)
        row["G1_draws"] = [round(float(x.mean()), 1) for x in vd]
        row["G6_draws"] = [round(float(x.mean()), 1) for x in gd]
        row["gap_by_draw"] = [round(float((vd[i] - gd[i]).mean()), 1) for i in range(3)]
        res[f"rlm_G1_vs_G6_cap{cap}_d181"] = row

    # rank noise and winners
    def tb_draw(fn, d):
        mm = fn(d)
        return {c: float(np.nanmean([mm[(q, c)] for q in Q86])) for c in S}

    j4 = lambda d: pm(4, draws=(d,))                                        # noqa: E731
    j3 = lambda d: pm(3, draws=(d,))                                        # noqa: E731
    cd = lambda d: conceptmat(L3d, "concept_recall", Q86, draws=(d,))       # noqa: E731
    rn = {"judge_4": [spearman(tb_draw(j4, i), tb_draw(j4, j)) for i, j in pairs],
          "judge_3": [spearman(tb_draw(j3, i), tb_draw(j3, j)) for i, j in pairs],
          "concept_d181": [spearman(tb_draw(cd, i), tb_draw(cd, j)) for i, j in pairs],
          "mc_key_precision": [spearman(tb_draw(mck, i), tb_draw(mck, j)) for i, j in pairs]}
    rn["winner_by_draw_judge4"] = {d: max(tb_draw(j4, d), key=tb_draw(j4, d).get) for d in (1, 2, 3)}
    rn["winner_by_draw_concept"] = {d: max(tb_draw(cd, d), key=tb_draw(cd, d).get) for d in (1, 2, 3)}
    t4, t3 = table(P4, Q86), table(P3, Q86)
    rn["top2_gap_judge4"] = sorted(t4.values())[-1] - sorted(t4.values())[-2]
    rn["spread_judge3"] = max(t3.values()) - min(t3.values())
    rn["spread_judge4"] = max(t4.values()) - min(t4.values())
    res["rank_noise"] = rn

    def wvs(name, mat, qs):
        t = table(mat, qs)
        o = sorted(t, key=t.get, reverse=True)
        res["winner_gap " + name] = {"winner": o[0], "runner_up": o[1], "gap": boot([mat[(q, o[0])] - mat[(q, o[1])] for q in qs]),
                                     "n": len(qs)}

    for name, mat, qs in (("judge 4", P4, Q86), ("judge 3", P3, Q86), ("judge 5", P5, Q86), ("judge passages 4", Pb4, Q86),
                          ("concept d181", c25, Q86), ("mc papers", MC["papers_prec"], Wq),
                          ("mc papers nosrc", MC["papers_prec_nosrc"], Wq2), ("mc key prec", MC["key_prec"], Wq),
                          ("mc key f1", MC["key_f1"], WqF)):
        wvs(name, mat, qs)
    for nm, mat, qs in (("judge 4", P4, Q86), ("concept d181", c25, Q86), ("mc papers", MC["papers_prec"], Wq),
                        ("mc papers nosrc", MC["papers_prec_nosrc"], Wq2)):
        res["contrast set " + nm] = {"rlm10-sp": boot([mat[(q, "rlm_10")] - mat[(q, "single_pass")] for q in qs]),
                                     "vp-rlm10": boot([mat[(q, "verified_pass")] - mat[(q, "rlm_10")] for q in qs]),
                                     "mh-sp": boot([mat[(q, "multi_hop")] - mat[(q, "single_pass")] for q in qs]),
                                     "vp-sp": boot([mat[(q, "verified_pass")] - mat[(q, "single_pass")] for q in qs]), "n": len(qs)}
    compare(res, "signal swap: judge pass at 4 to MiniCheck papers source dropped, draw 1", pm(4, draws=(1,)),
            MC["papers_prec_nosrc"], Wq2)
    plat = [10, 15, 20, 30, 50]
    g5p = np.mean([l2("G5", c, draws=(1,)) for c in plat], axis=0)
    g6p = np.mean([l2("G6", c) for c in plat], axis=0)
    res["plateau_G5_d1_minus_G6_caps10to50_d181"] = {
        "G5": round(float(g5p.mean()), 1), "G6": round(float(g6p.mean()), 1), "diff": boot(g5p - g6p),
        "one": boot((g5p - g6p)[[Q86.index(q) for q in ONE]]), "many": boot((g5p - g6p)[[Q86.index(q) for q in MANY]])}
    res["cap10_G6_group_draws"] = {"one": [round(float(l2("G6", 10, ONE, (d,)).mean()), 1) for d in (1, 2, 3)],
                                   "many": [round(float(l2("G6", 10, MANY, (d,)).mean()), 1) for d in (1, 2, 3)]}
    res["concept_d181_means"] = {k: round(v, 1) for k, v in table(c25, Q86).items()}

    # recount3.py's ladder
    from experiments.runner import experiment as ex
    for key_file in (ex.KEY_V24, ex.KEY_D5):             # what ex.questions and ex.scaling_questions open
        inp.tracked(key_file)
    ansq = {q["id"]: q for q in ex.questions() if q.get("answer_type") in ("extractive", "synthesis")}
    one = {q for q, v in ansq.items() if v["answer_type"] == "extractive"}
    if one != set(ONE) or set(ansq) - one != set(MANY):
        raise GateFail("the one-paper and many-paper sets of the key rows and of the runner differ")
    g4 = only_main_judge(read_jsonl(inp.frozen("fig3", G4_COLLECT)), G4_COLLECT)
    res["ladder"] = ladder(rows406_all, rows281, g4, {"all86": set(Q86), "one60": set(ONE), "many26": set(MANY)})
    return res


# ---------------------------------------------------------------- reproduce first
SIGNAL = "signal swap: judge pass at 4 to concept recall D181, all 86"
SOURCES = "MiniCheck papers precision, source lists kept to dropped"
TARGETS = (   # name, how to read it from the results, the value, its interval, where it stands
    ("judge to concepts, change in the gap", lambda r: r[SIGNAL]["contrast_change_B_minus_A"], 15.4, (6.8, 24.3), "instruments.md:7"),
    ("judge to concepts, noise", lambda r: (r[SIGNAL]["noise"]["range"],), 3.5, None, "instruments.md:7"),
    ("judge to concepts, one-paper", lambda r: r[SIGNAL.replace("all 86", "one-paper")]["contrast_change_B_minus_A"], 28.3,
     (18.7, 38.0), "instruments.md:7"),
    ("Mentori minus package, cap 10", lambda r: r["rlm_G1_vs_G6_cap10_d181"]["G1_minus_G6"], 10.9, (4.8, 16.7), "instruments.md:8"),
    ("source lists, change in the gap", lambda r: r[SOURCES]["contrast_change_B_minus_A"], 17.6, (15.0, 20.3), "instruments.md:11"),
    ("single pass, April answers, devstral, at 4",
     lambda r: (r["ladder"]["april_answers_devstral_v24"]["all86"][4]["single_pass"][0],), 33.7, None, "compare.md:29"),
    ("single pass, re-run, at 4", lambda r: (r["pass_table_at_4"]["single_pass"],), 83.3, None, "compare.md:29"),
)
HALF = 0.051                                     # a value printed to one decimal place


def reproduce(res: dict, targets=TARGETS, want_pass=None, want_median=WANT_MEDIAN) -> list[dict]:
    """Every gate, or GateFail. instr.py's gates (12 pass rates, the Papers median on the W set), then TARGETS."""
    gates, bad = [], []

    def gate(name, got, want, source):
        ok = abs(got - want) < HALF if isinstance(want, float) else got == want
        gates.append({"gate": name, "got": got, "want": want, "pass": bool(ok), "source": source})
        if not ok:
            bad.append(name)

    for thr, want in (want_pass or WANT_PASS).items():
        for c, v in want.items():
            gate(f"G1 pass rate {c} at {thr}", res[f"pass_table_at_{thr}"][c], v, "ranking_report.md (instr.py's gate)")
    gate("papers median, answers", res["gate_papers_median_on_W"][0], want_median[0], "instruments.md:30")
    n = res["gate_papers_median_on_W"][1]
    gates.append({"gate": "papers median", "got": n, "want": want_median[1], "pass": abs(n - want_median[1]) < 5e-5,
                  "source": "instruments.md:30"})
    if not gates[-1]["pass"]:
        bad.append("papers median")
    for name, read, value, interval, source in targets:
        got = read(res)
        gate(name, float(got[0]), float(value), source)
        if interval is not None:
            gate(name + ", lower", float(got[1]), float(interval[0]), source)
            gate(name + ", upper", float(got[2]), float(interval[1]), source)
    if bad:
        raise GateFail(f"{len(bad)} of {len(gates)} gates differ, nothing written: " + "; ".join(
            f"{g['gate']} got {g['got']}, want {g['want']}" for g in gates if not g["pass"]))
    return gates


# ---------------------------------------------------------------- writing
def thesis(res: dict) -> dict:
    t = {}
    for name, read, _, _, source in TARGETS:
        got = read(res)
        t[name] = {"value": got[0], "interval_95": list(got[1:3]) if len(got) == 3 else None, "first_stated_at": source}
    return t


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, float) and o != o:
        return None
    return o


def markdown(doc: dict) -> str:
    lines = ["# The swaps behind the thesis", "",
             f"Written by {SCRIPT}, sha256 {doc['_provenance']['script_sha256'][:16]}. Gap: RLM-10 minus single pass, in points. "
             f"Intervals: {B:,} question resamples, seed {SEED}. Every gate passed before this was written: "
             f"{sum(g['pass'] for g in doc['gates'])} of {len(doc['gates'])}.", "",
             "## The numbers the thesis states", "", "| Number | Value | 95% interval | First stated at |", "|---|---:|---|---|"]
    for k, v in doc["thesis"].items():
        iv = "" if v["interval_95"] is None else f"{v['interval_95'][0]} to {v['interval_95'][1]}"
        lines.append(f"| {k} | {v['value']} | {iv} | {v['first_stated_at']} |")
    lines += ["", "## Every swap", "", "| Swap | Questions | Gap before | Gap after | Change | 95% interval | Noise |",
              "|---|---:|---:|---:|---:|---|---:|"]
    for k, v in doc["swaps"].items():
        if isinstance(v, dict) and "contrast_change_B_minus_A" in v:
            c = v["contrast_change_B_minus_A"]
            noise = v.get("noise", {}).get("range", "")
            lines.append(f"| {k} | {v['n_q']} | {v['contrast_A'][0]} | {v['contrast_B'][0]} | {c[0]} | {c[1]} to {c[2]} | {noise} |")
    return "\n".join(lines) + "\n"


def write(out: Path, doc: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, text in (("results.json", json.dumps(doc, indent=1, sort_keys=True) + "\n"), ("results.md", markdown(doc))):
        tmp = out / f".{name}.tmp"
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, out / name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    install_guard()
    try:
        inp = Inputs()
        res = compute(inp)
        gates = reproduce(res)
        doc = {"_provenance": {"script": SCRIPT, "script_sha256": FR.sha256_file(Path(__file__)), "command": COMMAND,
                               "ported_from": ["findings/audits/rerun_story_2026-11-01/scripts/instr.py",
                                               "findings/audits/rerun_story_2026-11-01/scripts/recount3.py"],
                               "inputs_sha256": dict(sorted(inp.sha.items()))},
               "gates": gates, "thesis": thesis(res), "swaps": clean({k: v for k, v in res.items() if k != "ladder"}),
               "ladder": clean(res["ladder"])}
        write(a.out, doc)
    except GateFail as e:
        print(f"GATE FAILED, nothing written: {e}", file=sys.stderr)
        return 1
    except (Refused, S521.Refused, FR.FrozenInputError) as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    print(f"{sum(g['pass'] for g in gates)} of {len(gates)} gates passed")
    for k, v in doc["thesis"].items():
        print(f"  {k}: {v['value']}" + (f" ({v['interval_95'][0]} to {v['interval_95'][1]})" if v["interval_95"] else ""))
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
