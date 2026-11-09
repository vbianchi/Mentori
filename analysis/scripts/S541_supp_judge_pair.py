#!/usr/bin/env python3
"""S541 - Supplementary Figure 4: judge 1 against judge 2 on every metric, drawn from the committed rows of both judges.

WHY. D187 (9) asks for "judge 1 against judge 2 on every metric". The panel list is the mock-up's proposal
(plan_final.json, Supp 4). Build spec fig5.md section 5. D195 held this plate until S518 had run on the second judge;
the D195 note of 2 November about 20:46 (experiments/README.md) records that all five sources have run and that their
scores may now be read. D205 (1) lifted D198 O4's hold on the second judge's multi-hop, RLM-5 and RLM-20 calls of the
local generators, so no cell is planned as "Judge 1 alone" any more.

WHAT IT READS (each file committed and unchanged at HEAD, and equal to its pin; nothing else under findings/recompute):
  judge 1, devstral-small-2:24b, on gemini-3-flash-preview's answers (G1):
    findings/recompute/fig2_inputs/g1_collect.jsonl            key v2.4, all answers (S511.G1_COLLECT_SHA, the file
                                                               S518's gate and Figure 3 read)
    findings/recompute/fig3_s6_inputs/s6_g1_collect.jsonl      key v2.5, the changed questions (fig3_s6_inputs/SHA256SUMS,
                                                               S528's frozen set, read by S463 and S472)
  judge 2, qwen3.8:27b, on the same answers:
    findings/recompute/S518_inputs/second_judge/g1_second_v24_collect.jsonl   key v2.4 (S518's --base)
    findings/recompute/S518_inputs/second_judge/s6g1_second_collect.jsonl     key v2.5 (S518's --collect)
                                                               each pinned by that folder's SHA256SUMS and by the sha256
                                                               S518's committed second_judge.json records for it
  panel b, the other four generators of T2 (audit 6 Nov A4):
    judge 1: judge_rows_v25.t2_source (the reader Supplementary Figure 6 reads: S518_inputs/claude-haiku-4-5,
             S518_inputs/gemini-2.5-pro, t2_local_v25_inputs), every file held to its SHA256SUMS line; the rows are
             re-read here for the pairing, and their cells must equal t2_source's
    judge 2: findings/recompute/t2_second_inputs/ (S592's frozen copy of S9's rows, SHA256SUMS): claude-haiku-4-5 key
             v2.4 (t2_second_v24_collect.jsonl) with key v2.5 on the changed questions (s6t2_second_collect.jsonl);
             gemini-2.5-pro (t2g_second_collect.jsonl), gemma3:27b (t2lgemma_second_collect.jsonl) and qwen3-coder:30b
             (t2lqcoder_second_collect.jsonl), whole key v2.5. Every row: the second judge's tag and LOCK.toml's digest
             for it, a lock lock_equiv accepts, the generator's run ids, key checks as judge_rows_v25 makes them
  findings/recompute/S518_split_confirmation/second_judge.json  the reproduction target for judge 2 (below)
  findings/figures_provisional/fig3_strategies/figure3_numbers.json   the reproduction target for judge 1 (below)
  The question groups are S511.questions() (Rule 8 on the runner's D5 key: 86 answerable, 39 out of scope, 10 false
  premise). Rows on the final key: a key v2.5 row where one exists, else the key v2.4 row (S518.merge's rule, D185 (2)).
  Both judges must hold the same answers: the same (config, question, draw) and, for each, the same item_sha256,
  answer_key, passages and prompt; a row of judge 2 must carry the second judge's tag, a row of judge 1 none.

REPRODUCE FIRST (README.md:75-79). Before anything is drawn:
  judge 1: the pass rate at correctness 4 of each of the six strategies over the 86 answerable questions and 3 draws
           equals Figure 3a's committed "strategy" rows (figure3_numbers.json, sheet Fig. 3a, threshold 4, group all);
  judge 2: S518.analyse on these cells (RLM-10 against single pass) equals S518's committed second_judge.json result;
  the statistics: each kappa's point value equals scikit-learn's cohen_kappa_score on the same pairs, and each rho box
  passes S540.check_rho_box (S473.answer_rho on the same points).
  panel b: the T2 reader, run on gemini-3-flash-preview's own rows of both judges, gives its ten b rows exactly as the
           G1 reader above gives them (pass_rates), value for value.

WHAT IS DRAWN.
  a  six 6 x 6 grids, one per metric: per cell the share (%) of the metric's answers with that pair of scores, cividis
     0 to 40% (clipped above), the share printed (half up, whole percent). Correctness, Completeness, Faithfulness and
     Citation quality from call (a); Faithfulness with passages, the faithfulness of call (b) (the passages in the
     prompt; judge_passages.py); these five on the 86 answerable questions, 6 strategies, 3 draws (1,548 answers).
     Refusal: the refusal score (refusal_accuracy) of call (a) on the 39 out-of-scope questions (702 answers). A failed
     answer (no answer stored) scores 0 under both judges (Rule 10; S473.compute, as S540.answer_table). An answer
     either judge failed to score (a judge-call failure, or (b) deferred) is left out of that metric and counted.
  b  five facets (the strategies other than single pass), five generator rows: the pass-rate difference (correctness
     4 or more, pooled over questions and draws) from single pass, judge 1 filled, judge 2 open. Each strategy is set
     against single pass on the same (question, draw) answers, the answerable questions only: the local generators'
     RLM strategies hold D98's 45 questions, gemini-2.5-pro's draws 2 and 3 the same 45, so pooling single pass over
     all its answers would compare different questions (for gemini-3-flash-preview and claude-haiku-4-5 every
     strategy holds every answer, and the pairing changes nothing). An answer pair enters both judges' rates or
     neither: a pair either judge failed to score is left out and counted. A failed answer (no answer, judge 1's
     no_answer) that the second judge never called (S9 makes no call for an answer with no text) is a fail under both
     (Rule 10). A cell is drawn only when every pair has both judges' rows; a cell with no second-judge rows
     (gemini-2.5-pro's multi-hop, RLM-5 and RLM-20: S6WT2G judged single pass, verified pass and RLM-10, D198 O4) or
     with a pair missing its second-judge row stays empty, its sheet rows saying why and how many.
  c  four facets (Weighted kappa: quadratic weights on 0 to 5, the protocol's statistic; Spearman's rho; Kappa at 4 and
     Kappa at 3: Cohen's kappa on score at or above the mark), six metric rows, Refusal in Kappa at 4 only: box,
     quartiles of 10,000 question resamples (S473.boot_rows, every answer of a question drawn together); whiskers,
     the 2.5th and 97.5th percentiles. A resample on which a statistic is undefined is left out and counted.

    uv run --frozen python scripts/S541_supp_judge_pair.py figure [--out <folder>]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
SCRIPT = "scripts/S541_supp_judge_pair.py"
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig4_judge_pair"
N = 4                                              # D257 (14 before)
W, H = 183.0, 106.9
METRICS = ("Correctness", "Completeness", "Faithfulness", "Faithfulness with passages", "Citation quality", "Refusal")
# (call, score key, question group) per metric
SOURCE = {"Correctness": ("a", "correctness", "answerable"), "Completeness": ("a", "completeness", "answerable"),
          "Faithfulness": ("a", "faithfulness", "answerable"),
          "Faithfulness with passages": ("b", "faithfulness", "answerable"),
          "Citation quality": ("a", "citation_quality", "answerable"),
          "Refusal": ("a", "refusal_accuracy", "not_answerable")}
FLASH = "gemini-3-flash-preview"
GENERATORS = (FLASH, "gemini-2.5-pro", "claude-haiku-4-5", "gemma3:27b", "qwen3-coder:30b, same family")
# D291 (Valerio, 7 Nov): the plate and the legend print the paper's name; rows, keys and Source Data keep the API id
GEN_DISPLAY = {FLASH: "gemini-3-flash"}
NO_J2 = "empty: no second-judge rows of this strategy"
INCOMPLETE = "empty: {n} answer pairs without a second-judge row"
STATS = ("Weighted kappa", "Spearman's rho", "Kappa at 4", "Kappa at 3")
REFUSAL_ONLY = "Kappa at 4"
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
SECOND = "qwen3.8:27b"                                    # LOCK.toml [judge] second_model
PASS, SHARE_TOP = 4, 40.0
REC = ROOT / "findings" / "recompute"
J1_V24 = REC / "fig2_inputs" / "g1_collect.jsonl"
J1_V25 = REC / "fig3_s6_inputs" / "s6_g1_collect.jsonl"
J1_V25_SUMS = REC / "fig3_s6_inputs" / "SHA256SUMS"
J2_DIR = REC / "S518_inputs" / "second_judge"
J2_V24 = J2_DIR / "g1_second_v24_collect.jsonl"
J2_V25 = J2_DIR / "s6g1_second_collect.jsonl"
S518_RESULT = REC / "S518_split_confirmation" / "second_judge.json"
FIG3_NUMBERS = ROOT / "findings" / "figures_provisional" / "fig3_strategies" / "figure3_numbers.json"
IMPORTS = ("S497_fig5_d166.py", "S540_fig5_evaluators.py", "house_style.py", "figure_names.py", "S457_fig2_panels.py",
           "fig_repro.py", "S511_g2_matched_budget.py", "S518_split_confirmation.py", "S473_fig5_panels.py",
           "judge_rows_v25.py", "S512_s6_rejudge_v25.py", "S373_rejudge_v2.py", "lock_equiv.py")
T2_SECOND = REC / "t2_second_inputs"            # S592 (audit 6 Nov A4)
GEN_SRC = {FLASH: "gemini-3-flash-preview", "gemini-2.5-pro": "gemini-2.5-pro", "claude-haiku-4-5": "claude-haiku-4-5",
           "gemma3:27b": "gemma3", "qwen3-coder:30b, same family": "qwen3-coder"}   # GENERATORS -> t2_source name
SECOND_SPECS = {                                 # judge 2's files per generator: base (key v2.4), v25 and its kind
    "gemini-3-flash-preview": {"tag": "", "base": J2_V24, "v25": J2_V25, "kind": "v2.5 changed"},
    "claude-haiku-4-5": {"tag": "+claude-haiku-4-5", "base": T2_SECOND / "t2_second_v24_collect.jsonl",
                         "v25": T2_SECOND / "s6t2_second_collect.jsonl", "kind": "v2.5 changed"},
    "gemini-2.5-pro": {"tag": "+gemini-2.5-pro", "base": None, "v25": T2_SECOND / "t2g_second_collect.jsonl",
                       "kind": "whole:t2g"},
    "gemma3": {"tag": "+gemma3-27b", "base": None, "v25": T2_SECOND / "t2lgemma_second_collect.jsonl",
               "kind": "whole:t2lgemma"},
    "qwen3-coder": {"tag": "+qwen3-coder-30b", "base": None, "v25": T2_SECOND / "t2lqcoder_second_collect.jsonl",
                    "kind": "whole:t2lqcoder"},
}
TIE = ("answer_key", "item_sha256", "n_passages", "passage_chars", "answerable_prompt", "run_id", "key_hash")


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S497 = _load("S497", ROOT / "scripts" / "S497_fig5_d166.py")
hs, FN, S540, S473 = S497.hs, S497.FN, S497.S540, S497.S473
S518 = _load("S518", ROOT / "scripts" / "S518_split_confirmation.py")
S511 = S518.S511
Refused = S540.Refused
import judge_rows_v25 as JR  # noqa: E402
STRATS = FN.STRATEGIES[1:]
LABEL = dict(zip(CONFIGS, FN.STRATEGIES))


# ---------------------------------------------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------------------------------------------
def _rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def _sums(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            out[name.strip()] = h
    return out


def pins() -> dict:
    """{path: sha256} of every file read, each held to its pin and to its commit."""
    rec = json.loads(S518_RESULT.read_text())
    s518_in = {r["path"]: r["sha256"] for r in rec["inputs"]}
    j2 = _sums(J2_DIR / "SHA256SUMS")
    want = {J1_V24: S511.G1_COLLECT_SHA, J1_V25: _sums(J1_V25_SUMS)[J1_V25.name],
            J2_V24: j2[J2_V24.name], J2_V25: j2[J2_V25.name]}
    for p in (J2_V24, J2_V25):
        if s518_in.get(_rel(p)) != want[p]:
            raise Refused(f"{_rel(p)}: SHA256SUMS and S518's second_judge.json record different sha256")
    out = {}
    for p in (J1_V24, J1_V25, J2_V24, J2_V25, S518_RESULT, FIG3_NUMBERS):
        if not S540._committed(p, ROOT):
            raise Refused(f"{_rel(p)} is not committed and unchanged at HEAD")
        h = S511.sha256_file(p)
        if p in want and h != want[p]:
            raise Refused(f"{_rel(p)}: sha256 {h[:12]} is not its pin {want[p][:12]}")
        out[_rel(p)] = h
    return out


def _rows(path: Path, judge: str) -> dict:
    rows = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        tag = (r.get("judge") or {}).get("model") if isinstance(r.get("judge"), dict) else r.get("judge")
        if (judge == "1" and tag is not None) or (judge == "2" and tag != SECOND):
            raise Refused(f"{path.name}: a row with judge tag {tag!r} read as judge {judge}")
        k = (r["config"].split("+")[0], r["question_id"], int(r["draw"]))
        if k in rows:
            raise Refused(f"{path.name}: {k} doubled")
        rows[k] = r
    if len({r.get("lock_sha256") for r in rows.values()}) != 1:
        raise Refused(f"{path.name}: rows under more than one lock")
    return rows


def final_rows(v24: Path, v25: Path, judge: str) -> tuple[dict, int]:
    base, over = _rows(v24, judge), _rows(v25, judge)
    if any(r.get("key_version") is not None for r in base.values()):
        raise Refused(f"{v24.name}: a key v2.4 file holds a row with a key_version")
    if any(r.get("key_version") != "v2.5" for r in over.values()):
        raise Refused(f"{v25.name}: a row that is not key v2.5")
    if not set(over) <= set(base):
        raise Refused(f"{v25.name}: an answer that the v2.4 file does not hold")
    return {**base, **over}, len(over)


def read() -> dict:
    """Both judges' final-key rows of G1, checked to hold the same answers."""
    j1, n1 = final_rows(J1_V24, J1_V25, "1")
    j2, n2 = final_rows(J2_V24, J2_V25, "2")
    if set(j1) != set(j2) or n1 != n2:
        raise Refused(f"the judges hold different answers ({len(j1)} and {len(j2)}; v2.5 {n1} and {n2})")
    bad = [k for k in j1 if any(j1[k].get(f) != j2[k].get(f) for f in TIE)]
    if bad:
        raise Refused(f"{len(bad)} answers differ between the judges' rows, first {bad[0]}")
    qs = S511.questions()
    for (c, q, d), r in j1.items():
        if c not in CONFIGS or d not in (1, 2, 3) or q not in qs:
            raise Refused(f"an answer outside G1's 6 x 135 x 3: {(c, q, d)}")
        if bool(r.get("answerable_prompt")) != (qs[q]["group"] != "not_answerable"):
            raise Refused(f"{(c, q, d)}: prompt and Rule 8 group {qs[q]['group']} disagree")
    if len(j1) != len(CONFIGS) * len(qs) * 3:
        raise Refused(f"{len(j1)} answers, not {len(CONFIGS) * len(qs) * 3}")
    return {"1": j1, "2": j2, "qs": qs, "v25_rows": n1}


def score(r: dict, call: str, key: str):
    """('scored', v), ('failed', 0) or ('unscored', why), by Rule 10 (S518.read_rows, S463.cell_of)."""
    st = (r.get(call) or {}).get("status")
    if st == "ok":
        v = ((r[call].get("scores")) or {}).get(key)
        if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 5:
            raise Refused(f"{r['answer_key']}: ({call}) {key} is {v!r}")
        return "scored", v
    if st == "no_answer":
        return "failed", 0
    if st in S511.JUDGE_FAILED or st in ("deferred",):
        return "unscored", st
    raise Refused(f"{r['answer_key']}: ({call}) status {st!r}")


def pairs(R: dict, metric: str) -> tuple[list, Counter]:
    """[(question, judge 1, judge 2)] for one metric, and the answers left out by why."""
    call, key, group = SOURCE[metric]
    out, left = [], Counter()
    for k in sorted(R["1"]):
        if R["qs"][k[1]]["group"] != group:
            continue
        (s1, v1), (s2, v2) = score(R["1"][k], call, key), score(R["2"][k], call, key)
        if (s1 == "failed") != (s2 == "failed"):
            raise Refused(f"{k}: a failed answer under one judge only")
        if s1 == "unscored" or s2 == "unscored":
            left[f"judge 1 {v1}" if s1 == "unscored" else f"judge 2 {v2}"] += 1
            continue
        out.append((k[1], v1, v2))
    return out, left


# ---------------------------------------------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------------------------------------------
def _kappa(O, Wd):
    import numpy as np
    n = O.sum(axis=(1, 2))
    E = O.sum(axis=2)[:, :, None] * O.sum(axis=1)[:, None, :] / n[:, None, None]
    num, den = (Wd * O).sum(axis=(1, 2)), (Wd * E).sum(axis=(1, 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        k = 1 - num / den
    k[den <= 1e-12] = np.nan
    return k


def kappa_box(points: list, kind: str, mark: int | None = None) -> dict:
    """Cohen's kappa (kind 'quadratic' on 0 to 5, or 'binary' on score >= mark) and its question-resample box."""
    import numpy as np
    from sklearn.metrics import cohen_kappa_score
    if kind == "quadratic":
        K, f = 6, (lambda v: v)
        Wd = np.array([[(i - j) ** 2 for j in range(K)] for i in range(K)], float)
    else:
        K, f = 2, (lambda v: int(v >= mark))
        Wd = 1.0 - np.eye(2)
    qs = sorted({q for q, _, _ in points})
    ix = {q: i for i, q in enumerate(qs)}
    C = np.zeros((len(qs), K * K))
    for q, x, y in points:
        C[ix[q], f(x) * K + f(y)] += 1
    point = float(_kappa(C.sum(axis=0).reshape(1, K, K), Wd)[0])
    xs, ys = [f(x) for _, x, _ in points], [f(y) for _, _, y in points]
    ref = float(cohen_kappa_score(xs, ys, labels=list(range(K)), weights="quadratic" if kind == "quadratic" else None))
    if abs(point - ref) > 1e-9:
        raise Refused(f"kappa {kind} {mark}: {point} is not scikit-learn's {ref}")
    w = np.asarray(S473.boot_rows(len(qs)), float)
    res = _kappa((w @ C).reshape(-1, K, K), Wd)
    good = res[~np.isnan(res)]
    lo, hi = (float(v) for v in np.percentile(good, [2.5, 97.5]))
    q25, med, q75 = (float(v) for v in np.percentile(good, [25, 50, 75]))
    return {"value": point, "lo": lo, "hi": hi, "q25": q25, "median": med, "q75": q75, "answers": len(points),
            "questions": len(qs), "resamples_undefined": int(np.isnan(res).sum())}


def rho_box(points: list) -> dict:
    S540.check_rho_box(points)                     # refuses unless rho_box equals S473.answer_rho on these points
    r = S540.rho_box(points)
    return {"value": r["rho"], "lo": r["lo"], "hi": r["hi"], "q25": r["q25"], "median": r["median"], "q75": r["q75"],
            "answers": r["answers"], "questions": r["questions"], "resamples_undefined": r["resamples_undefined"]}


def stat(points: list, st: str) -> dict:
    if st == "Weighted kappa":
        return kappa_box(points, "quadratic")
    if st == "Spearman's rho":
        return rho_box(points)
    return kappa_box(points, "binary", int(st.split()[-1]))


def pass_rates(rows: dict, qs: dict) -> dict:
    """{config: (passes, answers)} at correctness >= PASS over the answerable questions (failed = fail; unscored out)."""
    out = {}
    for c in CONFIGS:
        k = n = 0
        for (cc, q, _d), r in rows.items():
            if cc != c or qs[q]["group"] != "answerable":
                continue
            s, v = score(r, "a", "correctness")
            if s == "unscored":
                continue
            k, n = k + int(s == "scored" and v >= PASS), n + 1
        out[c] = (k, n)
    return out


def reproduce(R: dict) -> dict:
    """README.md:75-79: judge 1 against Figure 3a, judge 2 against S518, before any number is written."""
    fig3 = json.loads(FIG3_NUMBERS.read_text())["sheets"]["Fig. 3a"]
    cols = fig3["columns"]
    want = {}
    for row in fig3["rows"]:
        x = dict(zip(cols, row))
        if x["row_kind"] == "strategy" and x["threshold"] == PASS and x["question_group"] == "all":
            want[x["strategy"]] = x["pass_rate_pct"]
    got1 = pass_rates(R["1"], R["qs"])
    for c in CONFIGS:
        k, n = got1[c]
        if c not in want or abs(100 * k / n - want[c]) > 1e-6:
            raise Refused(f"judge 1 {c}: pass rate {100 * k / n} is not Figure 3a's {want.get(c)}")
    cells = {}
    for (c, q, d), r in R["2"].items():
        if c not in (S518.A, S518.B) or R["qs"][q]["kind"] not in ("one", "many"):
            continue
        s, v = score(r, "a", "correctness")
        cells[(c, q, d)] = {"kind": "scored", "score": v} if s == "scored" else \
            {"kind": "failed"} if s == "failed" else {"kind": "unscored", "why": v}
    got2 = S518.analyse(cells, R["qs"])
    ref = json.loads(S518_RESULT.read_text())["result"]
    for part in ("one_paper", "many_paper"):
        for f in ("questions", "d", "lo", "hi"):
            if abs(float(got2[part][f]) - float(ref[part][f])) > 1e-12:
                raise Refused(f"judge 2: S518 {part} {f} {got2[part][f]} is not the committed {ref[part][f]}")
    if got2["interaction"]["reading"] != ref["interaction"]["reading"]:
        raise Refused("judge 2: S518's reading differs from the committed one")
    return {"judge_1": "six pass rates at 4 equal Figure 3a's committed strategy rows",
            "judge_2": "S518 D_one, D_many and their intervals equal second_judge.json"}


# ---------------------------------------------------------------------------------------------------------------
# panel b: T2's rows of both judges, per generator (audit 6 Nov A4)
# ---------------------------------------------------------------------------------------------------------------
def _jr(fn, *a, **k):
    try:
        return fn(*a, **k)
    except JR.Refused as e:
        raise Refused(str(e)) from e


def _second_digest() -> str:
    import tomllib
    lock = tomllib.loads((ROOT / "experiments" / "LOCK.toml").read_text())
    return lock["models"][SECOND]["digest"]


def _check_second(rows: dict, path: Path, kind: str, tag: str) -> None:
    """Judge 2's rows of one collect: the second judge's digest, then judge_rows_v25's row checks (key v2.4 or key v2.5
    changed: t2_check_rows; whole key: the same checks for S512's whole-key scope), on the rows without their judge
    tag (the module's checks refuse a tagged row; the tag was checked by _rows)."""
    want = _second_digest()
    for k, d in rows.items():
        if (d.get("judge") or {}).get("digest") != want or (d.get("a") or {}).get("model_digest") not in (None, want):
            raise Refused(f"{path.name} {k}: the second judge's digest is not LOCK.toml's {want[:12]}")
    plain = {k: {f: v for f, v in d.items() if f != "judge"} for k, d in rows.items()}
    if kind in (JR.V24, JR.V25_CHANGED):
        _jr(JR.t2_check_rows, plain, path, kind, tag)
        return
    _, k25 = JR.S512.keys()
    v2 = JR.S512.v2_records()
    for k, d in plain.items():
        _jr(JR._row_common, k, d, str(path))
        q = d["question_id"]
        if not str(d.get("run_id", "")).endswith(tag) or str(d.get("config", "")).split("+")[0] not in CONFIGS:
            raise Refused(f"{path.name} {k}: run {d.get('run_id')!r} is not of generator {tag!r}")
        if d.get("key_version") != JR.S512.KEY_VERSION or d.get("questions") != kind:
            raise Refused(f"{path.name} {k}: key_version {d.get('key_version')!r}, questions {d.get('questions')!r}")
        if q not in k25 or JR.S512.key_hash25(q, v2) != d.get("key_hash"):
            raise Refused(f"{path.name} {k}: key_hash {d.get('key_hash')} is not S512.key_hash25")
        if bool(d.get("answerable_prompt")) != (k25[q]["answerable"] in (True, "true", "True")):
            raise Refused(f"{path.name} {k}: answerable_prompt {d.get('answerable_prompt')}")
    runs = {d.get("run_sha256") for d in rows.values()}
    side = json.loads(path.with_name(path.name + ".json").read_text())
    if len(runs) != 1 or side.get("rows") != len(rows) or side.get("run_sha256") != next(iter(runs)):
        raise Refused(f"{path.name}: {len(runs)} run_sha256 values, or its sidecar disagrees")


def _merge(base: dict, over: dict, where: str) -> dict:
    """The key v2.5 row where one exists, else the key v2.4 row (D185 (2)); both rows of one answer agree in TIE."""
    for k in set(base) & set(over):
        diff = [f for f in JR.TIE if base[k].get(f) != over[k].get(f)]
        if diff:
            raise Refused(f"{where} {k}: the v2.5 row and the v2.4 row differ in {diff}")
    return {**base, **over}


def t2_first(name: str) -> tuple[dict, dict]:
    """Judge 1's final-key rows of one generator {(config, question, draw): row} and the files read; their cells equal
    judge_rows_v25.t2_source's (the reader Supplementary Figure 6 reads), cell for cell."""
    src = _jr(JR.t2_source, name)
    sp = JR.T2_SOURCES[name]
    rows = _merge(_rows(Path(sp["base"]), "1") if sp.get("base") else {}, _rows(Path(sp["v25"]), "1"), f"judge 1 {name}")
    cells = {k: _jr(JR.t2_cell, d) for k, d in rows.items()}
    if cells != src["cells"]:
        raise Refused(f"judge 1 {name}: the rows read here give other cells than judge_rows_v25.t2_source")
    return rows, {_rel(Path(p)): h for p, h in src["files"].items()}


def t2_second(name: str) -> tuple[dict, dict]:
    """Judge 2's final-key rows of one generator and the files read (each held to its SHA256SUMS line)."""
    sp = SECOND_SPECS[name]
    files, base = {}, {}
    for p in (sp["base"], sp["v25"]):
        if p is not None:
            files[_rel(p)] = _jr(JR.held_sha, p)
    over = _rows(sp["v25"], "2")
    _check_second(over, sp["v25"], sp["kind"], sp["tag"])
    if sp["base"] is not None:
        base = _rows(sp["base"], "2")
        _check_second(base, sp["base"], JR.V24, sp["tag"])
    return _merge(base, over, f"judge 2 {name}"), files


def t2_cells(R1: dict, R2: dict, qs: dict) -> tuple[list, dict]:
    """Panel b's rows of one generator (a list of [strategy label, judge, difference, rate, single-pass rate, pairs,
    state]) and its counts. Each strategy against single pass on the same (question, draw), answerable only."""
    out, info = [], {}
    j2_cfgs = {c for c, _, _ in R2}
    for cfg in CONFIGS[1:]:
        tally = {j: [0, 0] for j in ("1", "2")}          # passes of the strategy, passes of single pass
        n, left, no_call, missing, no_sp = 0, Counter(), 0, 0, 0
        for (c, q, d) in sorted(R1):
            if c != cfg or qs[q]["group"] != "answerable":
                continue
            ks = ((c, q, d), ("single_pass", q, d))
            if ks[1] not in R1:
                no_sp += 1
                continue
            s = {}
            for k in ks:
                s1 = score(R1[k], "a", "correctness")
                if k in R2:
                    s2 = score(R2[k], "a", "correctness")
                    if (s1[0] == "failed") != (s2[0] == "failed"):
                        raise Refused(f"{k}: a failed answer under one judge only")
                elif s1[0] == "failed":
                    s2, no_call = ("failed", 0), no_call + 1
                else:
                    s2 = None
                s[k] = (s1, s2)
            if any(v[1] is None for v in s.values()):
                missing += 1
                continue
            bad = [f"judge {j + 1} {v[j][1]}" for v in s.values() for j in (0, 1) if v[j][0] == "unscored"]
            if bad:
                left[bad[0]] += 1
                continue
            n += 1
            for j in (0, 1):
                tally[str(j + 1)][0] += int(s[ks[0]][j][0] == "scored" and s[ks[0]][j][1] >= PASS)
                tally[str(j + 1)][1] += int(s[ks[1]][j][0] == "scored" and s[ks[1]][j][1] >= PASS)
        info[cfg] = {"pairs": n, "left_out": dict(sorted(left.items())), "failed_cells_no_judge2_call": no_call,
                     "pairs_without_judge2_row": missing, "strategy_answers_without_single_pass": no_sp}
        if cfg not in j2_cfgs:
            state = NO_J2
        elif missing:
            state = INCOMPLETE.format(n=missing)
        else:
            state = "drawn"
        for j in ("1", "2"):
            if state != "drawn" or not n:
                out.append([LABEL[cfg], f"Judge {j}", None, None, None, n if state != NO_J2 else None, state])
                continue
            p, p0 = 100.0 * tally[j][0] / n, 100.0 * tally[j][1] / n
            out.append([LABEL[cfg], f"Judge {j}", p - p0, p, p0, n, state])
    return out, info


def t2_read() -> dict:
    """Both judges' T2 rows of every generator of panel b, and the files read."""
    out, files = {}, {}
    for g in GENERATORS:
        name = GEN_SRC[g]
        R1, f1 = t2_first(name)
        R2, f2 = t2_second(name)
        files.update(f1)
        files.update(f2)
        extra = sorted(set(R2) - set(R1))
        out[g] = {"1": R1, "2": R2, "judge2_only": len(extra)}
    return {"gens": out, "files": files}


def reproduce_b(R: dict, T: dict) -> str:
    """The T2 reader on gemini-3-flash-preview gives the G1 reader's ten b rows, value for value."""
    rates = {j: pass_rates(R[j], R["qs"]) for j in ("1", "2")}
    got, _ = t2_cells(T["gens"][FLASH]["1"], T["gens"][FLASH]["2"], R["qs"])
    for cfg in CONFIGS[1:]:
        for j in ("1", "2"):
            (k, n), (k0, n0) = rates[j][cfg], rates[j]["single_pass"]
            want = [100.0 * k / n - 100.0 * k0 / n0, 100.0 * k / n, 100.0 * k0 / n0, n]
            row = next(r for r in got if r[0] == LABEL[cfg] and r[1] == f"Judge {j}")
            if row[2:6] != want or n != n0:
                raise Refused(f"b: the T2 reader gives {row[2:6]} for {FLASH} {cfg} judge {j}, the G1 reader {want}")
    return f"the T2 reader gives {FLASH}'s ten b rows exactly as the G1 reader"


# ---------------------------------------------------------------------------------------------------------------
# sheets
# ---------------------------------------------------------------------------------------------------------------
def compute(R: dict, T: dict) -> dict:
    a = {"columns": ["metric", "judge_1_score", "judge_2_score", "share_of_answers_pct", "answers"], "rows": []}
    c = {"columns": ["metric", "statistic", "value", "resample_q25", "resample_median", "resample_q75", "interval_lo",
                     "interval_hi", "answers", "questions", "resamples_undefined"], "rows": []}
    info = {}
    for m in METRICS:
        pts, left = pairs(R, m)
        cnt = Counter((x, y) for _, x, y in pts)
        n = len(pts)
        for j2 in range(6):
            for j1 in range(6):
                k = cnt.get((j1, j2), 0)
                a["rows"].append([m, j1, j2, 100.0 * k / n, k])
        info[m] = {"answers": n, "questions": len({q for q, _, _ in pts}), "left_out": dict(sorted(left.items()))}
        for st in STATS:
            if m == "Refusal" and st != REFUSAL_ONLY:
                continue
            s = stat(pts, st)
            if s["lo"] < 0 or s["hi"] > 1:
                raise Refused(f"{m}, {st}: interval {s['lo']:.3f} to {s['hi']:.3f} leaves the 0 to 1 axis (fig5.md:147)")
            c["rows"].append([m, st, s["value"], s["q25"], s["median"], s["q75"], s["lo"], s["hi"], s["answers"],
                              s["questions"], s["resamples_undefined"]])
    b = {"columns": ["generator", "strategy", "judge", "pass_rate_difference_pp", "pass_rate_pct",
                     "single_pass_pass_rate_pct", "answers", "state"], "rows": []}
    b_info = {}
    for g in GENERATORS:
        rows, b_info[g] = t2_cells(T["gens"][g]["1"], T["gens"][g]["2"], R["qs"])
        b_info[g] = {"strategies": b_info[g], "judge2_rows_without_judge1_row": T["gens"][g]["judge2_only"]}
        b["rows"] += [[g, *r] for r in rows]
    for r in b["rows"]:
        if r[3] is not None and not -40 <= r[3] <= 40:
            raise Refused(f"b: {r[:3]} at {r[3]:.1f} pp leaves the -40 to +40 axis (fig5.md:146)")
    return {"sheets": {f"Supplementary Fig. {N}a": a, f"Supplementary Fig. {N}b": b, f"Supplementary Fig. {N}c": c},
            "info": info, "b_info": b_info}


# ---------------------------------------------------------------------------------------------------------------
# drawing (fig5.md section 5's layout; positions as the frame)
# ---------------------------------------------------------------------------------------------------------------
def draw(sheets: dict):
    hs.apply_rc("S541")
    pl = S497.Page(W, H)
    tw = hs._text_width_mm
    A, B, C = (sheets[f"Supplementary Fig. {N}{p}"] for p in "abc")
    # a
    ly, cw, th, x0, gap = 2.9, 4.1, 3.5, 9.0, 5.2
    grid = 6 * cw
    yt = ly + 1.4
    pl.letter(0, ly, "a")
    for i, row in enumerate(A["rows"]):
        m, j1, j2, share = row[0], row[1], row[2], row[3]
        x = x0 + METRICS.index(m) * (grid + gap)
        yy = yt + (5 - j2) * th
        fill = hs.cividis_value(share, 0.0, SHARE_TOP)
        pl.rect(x + j1 * cw, yy, cw, th, fill, ec=hs.WHITE, lw=0.5)
        pl.t(x + (j1 + 0.5) * cw, yy + th / 2, hs.fmt_num(share), color=hs.ink_on(fill), ha="center",
             va="center_baseline", printed={"sheet": f"Supplementary Fig. {N}a", "row": i,
                                            "format": "{share_of_answers_pct:.0f}"})
    for m, name in enumerate(METRICS):
        x = x0 + m * (grid + gap)
        pl.t(x + grid / 2, ly, name, ha="center")
        for i in range(6):
            if m == 0:
                pl.t(x - 0.8, yt + (5 - i) * th + th / 2, str(i), ha="right", va="center_baseline",
                     why="a score of judge 2")
        for j in range(6):
            pl.t(x + (j + 0.5) * cw, yt + 6 * th + 3.3, str(j), ha="center", why="a score of judge 1")
    pl.t(1.8, yt + 3 * th, "Judge 2 score", rotation=90, ha="left", va="center", why="the second judge's name on the plate")
    pl.t(x0 + (6 * grid + 5 * gap) / 2, yt + 6 * th + 7.0, "Judge 1 score; each cell, share of answers (%)", ha="center",
         why="the main judge's name on the plate")
    # b
    y1 = yt + 6 * th + 7.0 + 3.2
    ly = y1 + 2.9
    pl.letter(0, ly, "b")
    labr = 2.4 + max(tw(GEN_DISPLAY.get(g, g)) for g in GENERATORS) + 0.3
    xb, g2 = labr + 1.8, 3.0
    w = (182.2 - xb - 4 * g2) / 5
    mid = xb + (5 * w + 4 * g2) / 2
    items = (("Judge 1", True), ("Judge 2", False))
    size, ggap = hs.KEY_MARK_MM, 3.0
    total = sum(size + 0.8 + tw(t) for t, _ in items) + ggap
    kx = mid - total / 2
    for text, filled in items:
        pl.pg.plot([kx + size / 2], [ly - 1.0], ls="none", marker="o", ms=size / hs.MM_PT, mec=hs.BLACK, mew=0.5,
                   mfc=hs.BLACK if filled else hs.WHITE, clip_on=False)
        pl.t(kx + size + 0.8, ly, text, why="the judge's name in the key")
        kx += size + 0.8 + tw(text) + ggap
    p, rt = 3.8, ly + 5.4
    for k, s in enumerate(STRATS):
        x = xb + k * (w + g2)
        pl.t(x + w / 2, ly + 3.7, s, ha="center", why="strategy name")
        ax = pl.ax(x, rt, w, 5 * p, (-40, 40), (5, 0))
        ax.set_xticks([-30, 0, 30], [hs.fmt_num(-30), "0", hs.fmt_num(30, sign=True)])
        hs.reference_line(ax, 0)
        for r in B["rows"]:
            if r[1] != s or r[3] is None:
                continue
            i = GENERATORS.index(r[0])
            filled = r[2] == "Judge 1"
            ax.plot([r[3]], [i + 0.5], ls="none", marker="o", ms=hs.ESTIMATE_MM / hs.MM_PT, mec=hs.BLACK, mew=0.5,
                    mfc=hs.BLACK if filled else hs.WHITE, zorder=6 if not filled else 5, clip_on=False)
    for i, g in enumerate(GENERATORS):
        pl.t(labr, rt + (i + 0.5) * p, GEN_DISPLAY.get(g, g), ha="right", va="center_baseline", why="generator's name")
    pl.t(mid, rt + 5 * p + 7.0, "Pass-rate difference from single pass (percentage points)", ha="center")
    # c
    y2 = rt + 5 * p + 7.0 + 3.2
    ly = y2 + 2.9
    pl.letter(0, ly, "c")
    labr = 2.4 + max(tw(m) for m in METRICS) + 0.3
    xc, g3 = labr + 1.8, 3.4
    wc = (182.2 - xc - 3 * g3) / 4
    p, rt = 3.5, ly + 1.8
    for k, st in enumerate(STATS):
        x = xc + k * (wc + g3)
        pl.t(x + wc / 2, ly, st.replace("rho", "ρ"), ha="center", why="the pass mark of the statistic")
        ax = pl.ax(x, rt, wc, 6 * p, (0, 1), (6, 0))
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        for r in C["rows"]:
            if r[1] != st:
                continue
            i = METRICS.index(r[0])
            hs.boxplot(ax, i + 0.5, stats={"q1": r[3], "median": r[4], "q3": r[5], "whisker_low": r[6],
                                           "whisker_high": r[7]}, dots=False, zorder=3)
    for i, m in enumerate(METRICS):
        pl.t(labr, rt + (i + 0.5) * p, m, ha="right", va="center_baseline")
    pl.t(xc + (4 * wc + 3 * g3) / 2, rt + 6 * p + 7.0, "Agreement of judge 1 and judge 2", ha="center",
         why="the judges' names on the plate")
    bad = hs.check_figure_colours(pl.fig)
    if bad:
        raise Refused(f"Supplementary Figure {N}: colours outside the house palette: {bad}")
    return pl


def _and(xs: list) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def b_clause(b_rows: list) -> str:
    """Panel b's empty cells, in the legend's words (editor row 45, 8 Nov: no n in a panel without derived statistics)."""
    drawn = [r for r in b_rows if r[-1] == "drawn"]
    if not drawn:
        raise Refused("b: no cell drawn")
    empty = {}
    for r in b_rows:
        if r[-1] != "drawn" and r[2] == "Judge 2":
            why = "no second-judge rows" if r[-1] == NO_J2 else "answers without a second-judge row"
            empty.setdefault((r[0].split(",")[0], why), []).append(r[1].replace("Multi-hop", "multi-hop"))
    return "".join(f" Empty, {why}: {g}'s {_and(s)}." for (g, why), s in empty.items())


def legend(info: dict, b_rows: list) -> str:
    nq, nq_ref = info["Correctness"]["questions"], info["Refusal"]["questions"]
    return (f"**Supplementary Figure {N} | Two judges on the same answers, every metric.** Judge 1, devstral-small-2:24b; "
            f"judge 2, qwen3.8:27b, at the same settings, both on the final key. RLM-5, RLM-10 and RLM-20 are our "
            f"RLM. **a**, Scores of the two judges on the same answers, one grid per metric: {GEN_DISPLAY[FLASH]}'s "
            f"answers to the {nq} answerable questions, six strategies, three draws; for refusal, its answers to the "
            f"{nq_ref} out-of-scope questions. Columns, judge 1's score (0 to 5); rows, judge 2's score; cell number and "
            f"colour (dark blue, low; yellow, high), share of the metric's answers (%). Faithfulness with passages, the "
            f"judge's prompt also holds the retrieved passages. A failed answer scores 0 under both judges; an answer "
            f"either judge failed to score is left out of that metric. **b**, Change in pass rate (correctness 4 or "
            f"more) from single pass, in percentage points, for each generator (rows) and strategy (columns); single "
            f"pass taken on the same questions and draws as the strategy. Filled dot, judge 1; open dot, judge 2, drawn "
            f"over the filled dot where the two coincide; vertical line, no change.{b_clause(b_rows)} 'Same family', "
            f"qwen3-coder:30b is of judge 2's model family. **c**, Agreement of the two judges per metric (rows): "
            f"quadratic-weighted kappa on scores 0 to 5, Spearman's ρ, and Cohen's kappa on pass or fail at marks 4 "
            f"and 3 (refusal, kappa at 4 only), each over 10,000 resamples of the questions. Box, quartiles; line, "
            f"median; whiskers, two-sided 95% percentile interval; n = {nq} questions (refusal, {nq_ref}).")


def figure(out) -> None:
    inputs = pins()
    R = read()
    gates = reproduce(R)
    T = t2_read()
    sub = JR.S512.G7_SUBSET                      # D98's 45, read by S512's whole-key scope checks (pinned there)
    T["files"][_rel(sub)] = S511.sha256_file(sub)
    if T["files"][_rel(sub)] != JR.S512.G7_SUBSET_SHA256:
        raise Refused(f"{_rel(sub)}: sha256 is not S512.G7_SUBSET_SHA256")
    for p, h in T["files"].items():
        if not S540._committed(ROOT / p, ROOT):
            raise Refused(f"{p} is not committed and unchanged at HEAD")
        if inputs.get(p, h) != h:
            raise Refused(f"{p}: two sha256 values")
        inputs[p] = h
    inputs = dict(sorted(inputs.items()))
    gates["panel_b"] = reproduce_b(R, T)
    res = compute(R, T)
    planned = S473.PLANNED["judge"]
    drawn = res["info"]["Correctness"]["answers"] + sum(res["info"]["Correctness"]["left_out"].values())
    tag = f"provisional, {drawn} of {planned}"
    empty = sorted({f"{r[0].split(',')[0]} {r[1]}" for r in res["sheets"][f"Supplementary Fig. {N}b"]["rows"]
                    if r[-1] != "drawn"})
    stamp = (f"PROVISIONAL: {drawn:,} of {planned:,} gemini-3-flash-preview answers drawn under both judges, from the "
             "committed rows (S518_inputs/second_judge, fig2_inputs, fig3_s6_inputs); panel b from T2's rows of both "
             "judges (judge_rows_v25.t2_source; t2_second_inputs, S592)"
             + (f", empty: {', '.join(empty)}" if empty else "") + "; reproduced first: " + "; ".join(gates.values()))
    caption = (f"# Supplementary Figure {N} data, caption\n\n**Supplementary Figure {N} data.** Provisional. Data stamp: "
               f"{stamp}. One sheet per panel: a, one row per score pair and metric (share of the metric's answers and "
               f"their count); b, one row per generator, strategy and judge (rows marked empty hold no value); c, one "
               f"row per metric and statistic (value, resample quartiles, two-sided 95% interval, answers, questions, "
               f"resamples on which the statistic is undefined). Generated by `uv run --frozen python {SCRIPT} "
               f"figure`.\n")
    state = {"answers_per_metric": res["info"], "v25_rows_per_judge": R["v25_rows"], "reproduced": gates,
             "panel_b": res["b_info"]}
    b_rows = res["sheets"][f"Supplementary Fig. {N}b"]["rows"]
    S540.write_supp(out, N, tag, stamp, draw(res["sheets"]), res["sheets"], legend(res["info"], b_rows), caption,
                    script=SCRIPT, imports=IMPORTS, inputs=inputs, state=state)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("figure")
    f.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    S473.FR.pin_hash_seed()
    try:
        figure(a.out)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
