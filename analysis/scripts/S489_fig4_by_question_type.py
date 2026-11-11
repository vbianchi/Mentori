"""S489: Figure 4's pass counts split by question type, current draw 1 and the resubmission (inventory A15, F14; D155).

One command, from the repository root:
    uv run python scripts/S489_fig4_by_question_type.py            reproduce, then write
    uv run python scripts/S489_fig4_by_question_type.py --check    reproduce, then compare with the committed output only

Promoted from the 24 October scratch drafts fig4_alt/prep.py (the judge join), bytype.py (the split of the current
draw 1) and bytype_resub.py (the same split on the resubmission's answers). Exploratory: REVIEW_LOG.md:56-61 marks the
split "settle on draws 2 and 3 before any claim". Like S480, this script imports nothing from S463, S472 or S457 and
computes no statistic: it reads the raw files and counts. Reads only committed files:
    findings/recompute/fig4_inputs/g3_collect.jsonl (+ .json)   frozen set "fig4": S3's judge rows of G3's eight set-ups
    findings/recompute/fig2_inputs/g1_collect.jsonl (+ .json)   frozen set "fig2": S3's judge rows of G1 (RLM-10)
    findings/recompute/fig3_s6_inputs (S528, its own SHA256SUMS) frozen set "fig3_s6": RLM-10's key v2.5 rows (D201)
    findings/recompute/frozen_inputs/SHA256SUMS                 each collect and sidecar must have its listed sha256
    experiments.runner.experiment.questions()                    the D5 key: group (Rule 8) and answer_type per question
    findings/figures_provisional/fig4/Source Data Fig. 5.xlsx   the plate's numbers (sheet Fig. 4a)
    findings/recompute/S281_exp06_per_answer.csv                the resubmission's answers (judge qwen3-coder:30b)
    findings/recompute/S281_exp06_per_config.csv                its per-set-up pass rate and mean (S281)

D188 (Valerio, 31 October: every figure moves to key v2.5): the cells are read twice. The collects' key v2.4 rows
give the v2.4 cells; scripts/judge_rows_v25.py (read_v25, imported directly; it imports no figure script) gives the
cells Figure 4 draws: an answer's key v2.5 row (S512's re-judging of the 132 changed questions: out_s6_g3 beside the
frozen G3 collect, out_s6_g1 with out_s6_g1r15 in the frozen fig3_s6 set) where one exists, else its key v2.4 row,
which must be the v2.4 cell. Gates (1) and (3) hold the drawn cells to the plate; gate (4) holds the split of the v2.4
cells to the stated values (computed on v2.4, the anchors). numbers.json writes the split of both (current_draw1 drawn,
current_draw1_v24) and the reader's record (header.judge_rows_v25: per set the answers from key v2.5 and those
awaiting S6, provisional while any is). Until S6G3 sits beside the G3 collect, G3's 480 draw-1 answers of the 60 changed
questions await S6; RLM-10's 60 come from key v2.5, as Figure 4 draws them. S281_exp06_per_answer.csv (the resubmission) is the
submitted paper's qwen3-coder:30b judging and is read as it stands, a historical comparison (whether to re-judge it is
an open question for Valerio).

The cell of one draw-1 answer, as S463.read_collect and S480 map a judge row: (a) "ok" with the group's score is
scored; "no_answer" is a failed answer (Rule 10: a fail); any other status, or "ok" without the score, is unscored and
left out. A question passes at threshold t when it is scored t or more.

D201 Q2 (Valerio, 2 November 2026, yes; build order Q2, spec fig4.md:168). Two changes to the gates, dated here:
  (a) Figure 4's sheet 4a now holds 11 set-ups. nine_rows() takes the rows of G9's two stress set-ups (STRESS, by name)
      out of what gates (1) and (3) read, and numbers.json records how many rows it set aside
      (header.sheet_rows_set_aside). This script's nine stay checked row for row. Any other set-up on the sheet stays in
      and fails gate (1), so the filter cannot hide a set-up it does not name.
  (b) RLM-10's key v2.5 rows are read from the frozen fig3_s6 set (S6_G1, as S472 and S480 read them, S528: out_s6_g1 with
      out_s6_g1r15 after phase 3), where read_v25 used to look beside the G1 collect and found nothing, so it compared
      the plate's v2.5 rows with v2.4 cells. A set that leaves any RLM-10 answer of a changed question without a key
      v2.5 row is refused, with no key v2.4 fallback, as S480 refuses it.

REPRODUCE FIRST (any difference exits 2, nothing written):
  (1) every 'tile' row of sheet Fig. 4a (nine set-ups x 86 answerable questions: judge_kind and correctness) equals
      the cell read here, and every 'setup' row's passed and questions at thresholds 4 and 3 equal the counts here;
  (2) the resubmission: S281_exp06_per_config.csv's ans_n, ans_pass_pct_corrected and ans_mean_corrected per set-up,
      recomputed from S281_exp06_per_answer.csv's answerable rows by S281's own rule (pass at correctness_corrected 3
      or more, a blank counting as 0 over all n; mean over the non-blank, both rounded to 4 places).
THE SPLIT IS CHECKED BEFORE WRITING (D160 (6), Q18: "S489 refuses to write when a check fails"; any failure exits 2,
nothing written):
  (3) per set-up and threshold of the current draw 1, the extractive and synthesis passes and judged answers sum to
      sheet Fig. 4a's 'setup' row (passed, questions), and each type's questions equal the D5 key's count of that type
      among the 86; for the resubmission, each type's questions equal the key's count among the questions of the 86
      it answered;
  (4) every value REVIEW_LOG.md:56-69 or the inventory's F14 states (LOG_CURRENT, LOG_PHASES_OFF, LOG_RESUB) equals
      the split computed here (the current draw 1's on the v2.4 cells, D188). They were computed by the 24 October scratch drafts with this method on these answers
      (same-method anchors; the audit of 27 Oct, fig4_6 F3), so a difference is a defect, not a finding;
  (5) the selftest (below) passes: read_v25 on the frozen collects gives the v2.4 cells wherever no v2.5 row exists
      and refuses a v2.4 row that is not the cell read; the gates pass on the unchanged inputs and refuse each mutant.
Then it writes findings/recompute/S489_fig4_by_question_type/numbers.json (no time in it, so a rerun is byte-equal):
per set-up, passed of judged among the extractive and among the synthesis questions of the 86, at 4 and at 3, for the
current draw 1 (nine set-ups) and the resubmission (its four set-ups, on the questions of the 86 it answered, typed by
the D5 key), each beside the value REVIEW_LOG.md:56-69 or the inventory's F14 states, and whether they are equal.

    uv run python scripts/S489_fig4_by_question_type.py selftest     the gates and their mutants, nothing written
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import fig_repro  # noqa: E402
import judge_rows_v25 as JR  # noqa: E402  (D188: key v2.5 rows where S6 judged; it imports no figure script)

G3_COLLECT = fig_repro.frozen("fig4", "g3_collect.jsonl")
G1_COLLECT = fig_repro.frozen("fig2", "g1_collect.jsonl")
S6_G1 = fig_repro.frozen("fig3_s6", ".")                         # D201 Q2 (b): S528's set, as S472 and S480 read it
SUMS = REPO / "findings/recompute/frozen_inputs/SHA256SUMS"
PLATE = REPO / "findings/figures_provisional/fig4"
SD_GLOB = "Source Data Fig. 5.xlsx"   # Q9 (11 Nov): no suffix; D283: Figure 5 (4 until 6 Nov)
RESUB = REPO / "findings/recompute/S281_exp06_per_answer.csv"
RESUB_CFG = REPO / "findings/recompute/S281_exp06_per_config.csv"
RERUN_SH = REPO / "findings/recompute/G1_runs/rerun_d89.sh"      # G1's 15 reruns (D93 Q-c), S463.RERUN_SH
OUT = REPO / "findings/recompute/S489_fig4_by_question_type"

INDEX = "exp_v4_s20_n0"
G3 = ["raw_gemini", "naive_rag", "full_orchestrator", "orch_no_analyser", "orch_no_planner", "orch_no_supervisor",
      "orch_no_synthesiser", "orch_factual_to_documents"]          # S472.SETUPS (preflight.sh WAVE1)
RLM = "rlm_10"
ALL = G3 + [RLM]
STRESS = ("orch_distil_every_step", "orch_distil_every_step_f1")   # G9 (D163): on sheet 4a, not in this split (D201 Q2)
LABEL = {"raw_gemini": "no retrieval", "naive_rag": "naive RAG", "full_orchestrator": "full pipeline",
         "orch_no_analyser": "analyser off", "orch_no_planner": "planner off", "orch_no_supervisor": "supervisor off",
         "orch_no_synthesiser": "synthesiser off", "orch_factual_to_documents": "routing fix", RLM: "RLM-10"}
RUN_OF = {**{c: f"exp_03__{c}__{INDEX}" for c in G3}, RLM: f"exp_01__{RLM}__{INDEX}"}
SCORE_OF_GROUP = {"answerable": "correctness", "false_premise": "correctness", "not_answerable": "refusal_accuracy"}
THRESHOLDS = (4, 3)            # D154: 4 is the pass rate, 3 the relaxed threshold
TYPES = ("extractive", "synthesis")
RESUB_PASS = 3                 # scripts/S281_corrected_figure_tables.py:54
RESUB_CONFIGS = ["raw_gemini", "naive_rag", "full_orchestrator", "rlm_10"]
TOL = 1e-9

# The values stated in REVIEW_LOG.md:56-69 (inventory F14 names extractive 55 / 58 / 44, synthesis 10 / 15 / 22 and
# routing fix 44 of 60), computed by the scratch drafts with this method: gate (4) refuses to write when one differs
# (D160 (6), Q18). {(setup, type, t): passed}.
LOG_CURRENT = {("full_orchestrator", "extractive", 4): 55, ("naive_rag", "extractive", 4): 58,
               (RLM, "extractive", 4): 44, ("full_orchestrator", "synthesis", 4): 10,
               ("naive_rag", "synthesis", 4): 15, (RLM, "synthesis", 4): 22,
               ("orch_factual_to_documents", "extractive", 4): 44,
               ("raw_gemini", "extractive", 3): 37, ("naive_rag", "extractive", 3): 60,
               ("full_orchestrator", "extractive", 3): 58, (RLM, "extractive", 3): 54,
               ("raw_gemini", "synthesis", 3): 25, ("naive_rag", "synthesis", 3): 22,
               ("full_orchestrator", "synthesis", 3): 26, (RLM, "synthesis", 3): 26,
               ("raw_gemini", "extractive", 4): 21, ("raw_gemini", "synthesis", 4): 11}
LOG_PHASES_OFF = {"extractive": [46, 50], "synthesis": [16, 19]}    # REVIEW_LOG.md:57-58 "phases off 46 to 50", "16 to 19"
LOG_RESUB = {(c, t, th): v for th, vals in ((3, {"raw_gemini": (51, 26), "naive_rag": (47, 21),
                                                 "full_orchestrator": (30, 17), RLM: (57, 22)}),
                                            (4, {"raw_gemini": (31, 26), "naive_rag": (33, 15),
                                                 "full_orchestrator": (21, 16), RLM: (51, 17)}))
             for c, (e, s) in vals.items() for t, v in (("extractive", e), ("synthesis", s))}
PHASES_OFF = ["orch_no_analyser", "orch_no_planner", "orch_no_supervisor", "orch_no_synthesiser"]


class Refused(Exception):
    pass


def sha256_file(p: Path) -> str:
    return fig_repro.sha256_file(p)


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(REPO))


def listed_sha() -> dict:
    out = {}
    for ln in SUMS.read_text().splitlines():
        if ln.strip():
            h, name = ln.split(None, 1)
            out[name.strip()] = h
    return out


def check_frozen(p: Path, sums: dict) -> str:
    h = sha256_file(p)
    want = sums.get(rel(p))
    if want is None:
        raise Refused(f"{rel(p)} is not listed in {rel(SUMS)}")
    if h != want:
        raise Refused(f"{rel(p)} sha256 {h[:12]}, {rel(SUMS)} lists {want[:12]}")
    return h


def key():
    from experiments.runner.experiment import questions
    from experiments.scorers.records import GROUP_OF_TYPE
    qs = questions()
    groups = {q["id"]: GROUP_OF_TYPE[q["answer_type"]] for q in qs}
    types = {q["id"]: q["answer_type"] for q in qs}
    if len(qs) != 135 or Counter(groups.values()) != Counter({"answerable": 86, "false_premise": 10,
                                                               "not_answerable": 39}):
        raise Refused(f"the D5 key gives {len(qs)} questions {dict(Counter(groups.values()))}, want 135 (86/10/39)")
    return [q["id"] for q in qs], groups, types


def read_collect(p: Path, want_set: str, configs: list, groups: dict) -> tuple[dict, str]:
    """{(config, question): cell} of the draw-1 rows of configs; S480.read_collect's checks."""
    side_p = p.with_name(p.name + ".json")
    side = json.loads(side_p.read_text())
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    if side.get("rows") != len(rows):
        raise Refused(f"{rel(side_p)}: {side.get('rows')} rows, {rel(p)} holds {len(rows)}")
    if side.get("set") != want_set:
        raise Refused(f"{rel(side_p)}: set {side.get('set')!r}, want {want_set!r}")
    runs = Counter(r.get("run_sha256") for r in rows)
    if len(runs) != 1 or side.get("run_sha256") not in runs:
        raise Refused(f"{rel(p)}: run_sha256 values {dict(runs)}, sidecar {side.get('run_sha256')}")
    seen, out = set(), {}
    for i, r in enumerate(rows, 1):
        k = (r.get("config"), r.get("question_id"), r.get("draw"))
        if k in seen:
            raise Refused(f"{rel(p)}: row {i} repeats {k}")
        seen.add(k)
        c, q, d = k
        if c not in configs or d != 1:
            continue
        if q not in groups or r.get("answer_key") != f"{INDEX}|{c}|{q}|d1" or r.get("run_id") != RUN_OF[c]:
            raise Refused(f"{rel(p)}: row {i} {k}: answer_key {r.get('answer_key')!r}, run_id {r.get('run_id')!r}")
        if bool(r.get("answerable_prompt")) != (groups[q] != "not_answerable"):
            raise Refused(f"{rel(p)}: row {i} {k}: judged with the other group's prompt")
        out[(c, q)] = cell_of(r.get("a") or {}, groups[q])
    missing = [(c, q) for c in configs for q in groups if (c, q) not in out]
    if missing:
        raise Refused(f"{rel(p)}: {len(missing)} draw-1 answers have no row, first {missing[0]}")
    return out, side["run_sha256"]


def rerun_keys(path: Path = RERUN_SH) -> list[str]:
    """G1's 15 rerun answer keys from rerun_d89.sh's KEYS, as S463.rerun_keys reads them (copied, not imported)."""
    keys = ["|".join(f[1:5]) for f in (ln.strip().split("|") for ln in path.read_text().splitlines())
            if len(f) == 6 and f[0].startswith("exp_01__")]
    if len(keys) != 15 or len(set(keys)) != 15:
        raise Refused(f"{rel(path)}: {len(keys)} rerun keys, want 15 distinct")
    return keys


def read_v25(groups: dict, old: dict, s6_g1: Path = S6_G1) -> tuple[dict, dict]:
    """D188: the draw-1 cells of the nine set-ups on the rows scripts/judge_rows_v25.py chooses (an answer's key v2.5
    row, S512, where one exists, else its key v2.4 row), as S472 draws them. G3: out_g3 beside the frozen collect,
    out_s6_g3 beside it, else under s6_g1 (D203), when present (out_s6_g7_g3, draws 2 and 3, is not read), G3's per-configuration rule, draw 1
    of the eight set-ups read. G1: out and out_g1r15 beside the frozen G1 collect (the 15 reruns held to out_g1r15),
    out_s6_g1 with out_s6_g1r15 under s6_g1 (default the frozen fig3_s6 set, D201 Q2), which must be present, every
    draw, then RLM-10's draw 1, every answer of a changed question from key v2.5 (no v2.4 fallback, as S480). An S6 out
    is collected by s3_guard.py collect into a temporary file. Every v2.4 cell chosen must equal old (read_collect's
    cell). Returns ({(config, question): cell}, the record: per set the answers from v2.5 and awaiting S6, provisional)."""
    import contextlib
    import io
    import tempfile
    try:
        with tempfile.TemporaryDirectory(prefix="S489_s6_") as td:
            def loaded(srcs, collect, keys=None):
                out = [JR.read_source(srcs[0], collect, replace_keys=keys)]
                s6 = srcs[1]
                if s6["present"]:
                    dest = Path(td) / f"{s6['name']}.jsonl"
                    with contextlib.redirect_stdout(io.StringIO()) as buf:
                        rc = JR.guard().collect(s6["outs"], s6.get("replace"), dest, s6["set"])
                    if rc:
                        raise Refused(f"s3_guard collect refused {s6['name']}: {buf.getvalue().strip()[-300:]}")
                    out.append(JR.read_source(s6, dest, replace_keys=keys))
                return out
            s3 = JR.sources(G3_COLLECT.parent, "G3")
            s3_frozen = JR.sources(s6_g1, "G3")[1]   # D203: out_s6_g3 frozen beside S6G1 (S528 --add), as S472 and S480
            if not s3[1]["present"] and s3_frozen["present"]:
                s3 = [s3[0], s3_frozen, s3[2]]
            s1 = [JR.sources(G1_COLLECT.parent, "G1")[0], JR.sources(s6_g1, "G1")[1]]      # D201 Q2 (b)
            if not s1[1]["present"]:
                raise Refused(f"judge_rows_v25 G1: {s1[1]['missing']} not under {s6_g1}: RLM-10 is read on key v2.5 only")
            a3 = [{"run_id": RUN_OF[c], "config": c, "question_id": q, "draw": 1, "answer_key": f"{INDEX}|{c}|{q}|d1"}
                  for c in G3 for q in sorted(groups)]
            ch3 = JR.choose(a3, loaded(s3, G3_COLLECT), g7_configs=JR.g7_configs("G3"),
                            read_only=lambda d: d.get("draw") == 1 and d.get("config") in G3)
            keys = rerun_keys()
            L1 = loaded(s1, G1_COLLECT, keys)
            a1 = [{k: d[k] for k in ("run_id", "config", "question_id", "draw", "answer_key")}
                  for d in L1[0].rows.values()]
            ch1 = JR.choose(a1, L1, all_draws=True)
    except JR.Refused as e:
        raise Refused(f"judge_rows_v25: {e}") from None
    cells, rec = {}, {}
    for name, ch, cfgs, srcs in (("G3", ch3, G3, s3), ("G1", ch1, [RLM], s1)):
        n25 = n_await = 0
        for c in cfgs:
            for q in sorted(groups):
                v = ch[(RUN_OF[c], c, q, 1)]
                if v["row"] is None:
                    raise Refused(f"judge_rows_v25 {name}: {c} {q} draw 1: no judge row chosen ({v['status']})")
                cell = cell_of(v["row"].get("a") or {}, groups[q])
                if v["status"] != "v2.5" and cell != old[(c, q)]:
                    raise Refused(f"judge_rows_v25 {name}: {c} {q} draw 1: the v2.4 row chosen is not the row read")
                cells[(c, q)] = cell
                n25 += v["status"] == "v2.5"
                n_await += v["status"] == "v2.4 awaiting S6"
        if name == "G1" and n_await:
            raise Refused(f"judge_rows_v25 G1: {n_await} RLM-10 answers of changed questions have no key v2.5 row under "
                          f"{s6_g1}: no key v2.4 fallback")
        rec[name] = {"s6_absent": [Path(m).name for m in srcs[1]["missing"]], "from_v25": n25, "awaiting_s6": n_await,
                     "run_sha256": {n: x["run_sha256"] for n, x in ch["_sources"].items()}}
    rec["provisional"] = rec["G3"]["awaiting_s6"] + rec["G1"]["awaiting_s6"] > 0
    return cells, rec


def cell_of(a: dict, group: str) -> dict:
    st = a.get("status")
    if st == "ok":
        v = (a.get("scores") or {}).get(SCORE_OF_GROUP[group])
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return {"kind": "scored", "score": v}
        return {"kind": "unscored", "score": None}
    if st == "no_answer":
        return {"kind": "failed", "score": None}
    return {"kind": "unscored", "score": None}


def passed(cell: dict, t: int):
    """1, 0, or None (left out): S463.shares on one draw."""
    if cell["kind"] == "scored":
        return int(cell["score"] >= t)
    if cell["kind"] == "failed":
        return 0
    return None


def source_data(path: Path) -> dict:
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Fig. 5a"]
    rows = list(ws.iter_rows(values_only=True))
    return [{k: (None if v == "" else v) for k, v in zip(rows[0], r)} for r in rows[1:]]


def nine_rows(sd: list) -> tuple[list, int]:
    """D201 Q2 (a): the 'tile' and 'setup' rows of G9's two stress set-ups left out of sheet 4a's rows, by name, and how
    many went. Every other row stays, so a set-up neither named here nor one of the nine still fails gate (1)."""
    keep = [r for r in sd if not (r.get("row") in ("tile", "setup") and r.get("config") in STRESS)]
    return keep, len(sd) - len(keep)


def num_eq(a, b) -> bool:
    if a is None or b is None:
        return a is b
    return math.isclose(float(a), float(b), abs_tol=TOL, rel_tol=0)


# ------------------------------------------------------------------------------------------------ the two gates
def gate_current(cells: dict, groups: dict, sd: list) -> tuple[list, int]:
    bad, n = [], 0
    answerable = [q for q in groups if groups[q] == "answerable"]
    tiles = {(r["config"], r["question_id"]): r for r in sd if r["row"] == "tile"}
    if set(tiles) != {(c, q) for c in ALL for q in answerable}:
        bad.append(f"sheet Fig. 5a holds {len(tiles)} tiles, not the nine set-ups x 86 answerable questions")
    for (c, q), w in tiles.items():
        cell = cells.get((c, q))
        if cell is None:
            continue
        n += 2
        if cell["kind"] != w["judge_kind"]:
            bad.append(f"tile {c} {q}: judge_kind Source Data {w['judge_kind']!r}, read {cell['kind']!r}")
        if not num_eq(cell["score"], w["correctness"]):
            bad.append(f"tile {c} {q}: correctness Source Data {w['correctness']!r}, read {cell['score']!r}")
    setups = {(r["config"], r["threshold"]): r for r in sd if r["row"] == "setup"}
    if set(setups) != {(c, t) for c in ALL for t in THRESHOLDS}:
        bad.append(f"sheet Fig. 5a setup rows {sorted(setups)} are not nine set-ups x thresholds {THRESHOLDS}")
    for (c, t), w in setups.items():
        v = [passed(cells[(c, q)], t) for q in answerable if (c, q) in cells]
        v = [x for x in v if x is not None]
        n += 2
        if sum(v) != w["passed"]:
            bad.append(f"setup {c} at {t}: passed Source Data {w['passed']}, counted {sum(v)}")
        if len(v) != w["questions"]:
            bad.append(f"setup {c} at {t}: questions Source Data {w['questions']}, counted {len(v)}")
    return bad, n


def read_resub() -> list:
    return list(csv.DictReader(open(RESUB, newline="")))


def gate_resub(rows: list) -> tuple[list, int]:
    bad, n = [], 0
    want = {r["config"]: r for r in csv.DictReader(open(RESUB_CFG, newline=""))}
    if sorted(want) != sorted(RESUB_CONFIGS):
        bad.append(f"{rel(RESUB_CFG)} set-ups {sorted(want)}, want {sorted(RESUB_CONFIGS)}")
    for c, w in want.items():
        R = [r for r in rows if r["config"] == c and r["half"] == "answerable"]
        cor = [None if r["correctness_corrected"] in ("", "None") else float(r["correctness_corrected"]) for r in R]
        got = {"ans_n": len(R),
               "ans_pass_pct_corrected": round(100 * sum(1 for x in cor if (x or 0) >= RESUB_PASS) / len(R), 4),
               "ans_mean_corrected": round(sum(x for x in cor if x is not None) / len([x for x in cor if x is not None]),
                                           4)}
        for k, v in got.items():
            n += 1
            if not num_eq(v, float(w[k])):
                bad.append(f"resubmission {c} {k}: {rel(RESUB_CFG)} {w[k]}, recomputed {v}")
    return bad, n


# ------------------------------------------------------------------------------------------------ the split
def split_current(cells: dict, groups: dict, types: dict) -> dict:
    out = {}
    for c in ALL:
        e = {"setup": LABEL[c]}
        for typ in TYPES:
            qs = [q for q in groups if groups[q] == "answerable" and types[q] == typ]
            for t in THRESHOLDS:
                v = [passed(cells[(c, q)], t) for q in qs]
                v = [x for x in v if x is not None]
                e[f"{typ}_pass{t}"] = {"passed": sum(v), "judged": len(v), "questions": len(qs)}
        out[c] = e
    return out


def split_resub(rows: list, groups: dict, types: dict) -> tuple[dict, dict]:
    out = {}
    R = [r for r in rows if r["half"] == "answerable"]
    in86 = sorted({r["question_id"] for r in R if groups.get(r["question_id"]) == "answerable"})
    outside = sorted({r["question_id"] for r in R} - set(in86))
    for c in RESUB_CONFIGS:
        e = {}
        for typ in TYPES:
            qs = [q for q in in86 if types[q] == typ]
            for t in THRESHOLDS:
                v = []
                for r in R:
                    if r["config"] == c and r["question_id"] in qs:
                        x = r["correctness_corrected"]
                        if x not in ("", "None"):
                            v.append(int(float(x) >= t))
                e[f"{typ}_pass{t}"] = {"passed": sum(v), "judged": len(v), "questions": len(qs)}
        out[c] = e
    return out, {"answerable_rows_questions": len({r['question_id'] for r in R}), "in_the_86": len(in86),
                 "outside_the_86": outside, "in86_ids": in86}


def compare(cur: dict, res: dict) -> dict:
    rows = []
    for (c, typ, t), v in sorted(LOG_CURRENT.items()):
        got = cur[c][f"{typ}_pass{t}"]["passed"]
        rows.append({"run": "current draw 1", "setup": LABEL[c], "type": typ, "threshold": t, "computed": got,
                     "of": cur[c][f"{typ}_pass{t}"]["judged"], "stated": v, "equal": got == v})
    for typ, (lo, hi) in LOG_PHASES_OFF.items():
        got = sorted(cur[c][f"{typ}_pass4"]["passed"] for c in PHASES_OFF)
        rows.append({"run": "current draw 1", "setup": "phases off (range over the four)", "type": typ,
                     "threshold": 4, "computed": [got[0], got[-1]], "stated": [lo, hi],
                     "equal": [got[0], got[-1]] == [lo, hi]})
    for (c, typ, t), v in sorted(LOG_RESUB.items()):
        got = res[c][f"{typ}_pass{t}"]["passed"]
        rows.append({"run": "resubmission", "setup": LABEL[c], "type": typ, "threshold": t, "computed": got,
                     "of": res[c][f"{typ}_pass{t}"]["judged"], "stated": v, "equal": got == v})
    return {"source": "REVIEW_LOG.md:56-69 (findings/audits/figures_review_2026-10-22); inventory F14 names the "
                      "score-4 draw-1 values extractive 55 / 58 / 44 (full pipeline / naive RAG / RLM-10), synthesis "
                      "10 / 15 / 22 and routing fix 44 of 60",
            "rows": rows, "equal": sum(r["equal"] for r in rows), "of": len(rows)}


def gate_split(cur: dict, res: dict, res_q: dict, groups: dict, types: dict, sd: list) -> tuple[list, int]:
    """Gate (3): the split adds up to the plate's totals, and each type holds the key's questions of that type."""
    bad, n = [], 0
    answerable = [q for q in groups if groups[q] == "answerable"]
    key_n = Counter(types[q] for q in answerable)
    setups = {(r["config"], r["threshold"]): r for r in sd if r["row"] == "setup"}
    for c in ALL:
        for t in THRESHOLDS:
            w = setups.get((c, t))
            parts = [cur[c][f"{typ}_pass{t}"] for typ in TYPES]
            n += 2 + len(TYPES)
            if w is None:
                bad.append(f"split {c} at {t}: no sheet Fig. 5a setup row")
                continue
            if sum(x["passed"] for x in parts) != w["passed"]:
                bad.append(f"split {c} at {t}: extractive + synthesis passed {sum(x['passed'] for x in parts)}, "
                           f"sheet Fig. 5a {w['passed']}")
            if sum(x["judged"] for x in parts) != w["questions"]:
                bad.append(f"split {c} at {t}: extractive + synthesis judged {sum(x['judged'] for x in parts)}, "
                           f"sheet Fig. 5a {w['questions']}")
            for typ, x in zip(TYPES, parts):
                if x["questions"] != key_n[typ]:
                    bad.append(f"split {c} at {t}: {typ} questions {x['questions']}, the D5 key {key_n[typ]}")
    in86 = [q for q in answerable if q in set(res_q.get("in86_ids", []))]
    res_n = Counter(types[q] for q in in86)
    for c in RESUB_CONFIGS:
        for typ in TYPES:
            for t in THRESHOLDS:
                n += 1
                if res[c][f"{typ}_pass{t}"]["questions"] != res_n[typ]:
                    bad.append(f"resubmission split {c} {typ} at {t}: questions "
                               f"{res[c][f'{typ}_pass{t}']['questions']}, the key's {res_n[typ]} of those answered")
    return bad, n


def gate_anchors(cmp: dict) -> tuple[list, int]:
    """Gate (4): every stated value (REVIEW_LOG.md:56-69, inventory F14) equals the split computed here."""
    return ([f"{r['run']} {r['setup']} {r['type']} at {r['threshold']}: computed {r['computed']}, stated {r['stated']}"
             for r in cmp["rows"] if not r["equal"]], len(cmp["rows"]))


def build() -> tuple[dict, list, dict]:
    sums = listed_sha()
    inputs = {}
    for p in (G3_COLLECT, G3_COLLECT.with_name(G3_COLLECT.name + ".json"), G1_COLLECT,
              G1_COLLECT.with_name(G1_COLLECT.name + ".json")):
        inputs[rel(p)] = check_frozen(p, sums)
    order, groups, types = key()
    g3, g3run = read_collect(G3_COLLECT, "G3", G3, groups)
    g1, g1run = read_collect(G1_COLLECT, "G1", [RLM], groups)
    if g3run != g1run:
        raise Refused(f"G3's judge rows are under run_sha256 {g3run[:12]}, RLM-10's under {g1run[:12]}")
    cells_v24 = {**g3, **g1}
    cells, jrec = read_v25(groups, cells_v24)                # D188: the cells the plate draws
    wbs = sorted(glob.glob(str(PLATE / SD_GLOB)))
    if len(wbs) != 1:
        raise Refused(f"expected one Source Data workbook in {rel(PLATE)}, found {len(wbs)}")
    sd_path = Path(wbs[0])
    sd, set_aside = nine_rows(source_data(sd_path))          # D201 Q2 (a)
    bad1, n1 = gate_current(cells, groups, sd)
    resub = read_resub()
    bad2, n2 = gate_resub(resub)
    counts = {"Fig. 5a": n1, "S281_exp06_per_config": n2}
    if bad1 or bad2:
        return {}, bad1 + bad2, counts
    for p in (sd_path, RESUB, RESUB_CFG, REPO / "experiments/runner/experiment.py", RERUN_SH,
              REPO / "scripts/judge_rows_v25.py", S6_G1 / "SHA256SUMS"):
        inputs[rel(p)] = sha256_file(p)
    cur = split_current(cells, groups, types)
    cur24 = split_current(cells_v24, groups, types)
    res, res_q = split_resub(resub, groups, types)
    cmp = compare(cur24, res)                                # gate (4): the stated values are v2.4's (anchors)
    bad3, n3 = gate_split(cur, res, res_q, groups, types, sd)
    bad4, n4 = gate_anchors(cmp)
    counts.update({"split sums and types": n3, "stated values (REVIEW_LOG, F14)": n4})
    if bad3 or bad4:
        return {}, bad3 + bad4, counts
    res_q = {k: v for k, v in res_q.items() if k != "in86_ids"}
    n_types = Counter(types[q] for q in groups if groups[q] == "answerable")
    doc = {"header": {"script": rel(Path(__file__)), "script_sha256": sha256_file(Path(__file__)),
                      "command": "uv run python scripts/S489_fig4_by_question_type.py",
                      "inputs": inputs, "judge_run_sha256": g3run,
                      "judge_rows_v25": {"what": "D188: current_draw1 is on the draw-1 rows scripts/judge_rows_v25.py "
                                                 "chooses (key v2.5 where S6 judged, else key v2.4), as Figure 5 "
                                                 "draws them; current_draw1_v24 and compare on the collects' key "
                                                 "v2.4 rows", **jrec,
                                         "cells_differ_from_v24": sum(cells[k] != cells_v24[k] for k in cells)},
                      "sheet_rows_set_aside": {"rows": set_aside, "set_ups": list(STRESS), "why": "D201 Q2: G9's two "
                                               "stress set-ups are on sheet 4a and outside this split's nine"},
                      "reproduced": {"values_equal": sum(counts.values()), "per_source": counts, "mismatches": 0},
                      "exploratory": "REVIEW_LOG.md:56-61: settle on draws 2 and 3 before any claim"},
           "rule": {"current": "draw 1; a question passes at t when the judge scores it t or more; a failed answer "
                               "(no text) is a fail; an unscored judge row is left out (S463.shares, S480)",
                    "resubmission": "S281_exp06_per_answer.csv, half 'answerable', correctness_corrected (judge "
                                    "qwen3-coder:30b, the submitted answers); a blank score left out; only the "
                                    "questions in the D5 key's 86 answerable, typed by the key"},
           "answerable_by_type": dict(n_types),
           "current_draw1": cur, "current_draw1_v24": cur24,
           "resubmission": res, "resubmission_questions": res_q,
           "compare": cmp}
    return doc, [], counts


def selftest(quiet: bool = False) -> bool:
    """Gate (5): the gates pass on the unchanged inputs, and each mutant (a changed cell, a changed resubmission row,
    a split with the types swapped or at the wrong threshold, a split one pass off a stated value) is refused."""
    import copy

    def say(x):
        if not quiet:
            print(x)
    _, groups, types = key()
    g3, _ = read_collect(G3_COLLECT, "G3", G3, groups)
    g1, _ = read_collect(G1_COLLECT, "G1", [RLM], groups)
    cells24 = {**g3, **g1}
    cells, jrec = read_v25(groups, cells24)
    # D188, D201 Q2 (b): G3's 480 draw-1 answers of the 60 changed questions await S6 (no out_s6_g3 beside the frozen
    # collect) and RLM-10's 60 come from key v2.5 (the frozen fig3_s6 set), 9 x 60 = 540 in all
    n_ch = len(ALL) * len(set(groups) & set(JR.S512.changed_ids()))      # 9 x 60 = 540
    ok25 = (sum(cells[k] != cells24[k] for k in cells) <= jrec["G3"]["from_v25"] + jrec["G1"]["from_v25"]
            and jrec["G3"]["awaiting_s6"] + jrec["G1"]["awaiting_s6"] + jrec["G3"]["from_v25"] + jrec["G1"]["from_v25"]
            == n_ch and set(cells) == set(cells24) and jrec["G1"]["from_v25"] == n_ch // len(ALL)
            and jrec["G1"]["awaiting_s6"] == 0)
    say(f"  {'PASS' if ok25 else 'FAIL'}  judge_rows_v25 (D188): {jrec['G3']['from_v25'] + jrec['G1']['from_v25']} "
        f"cells from key v2.5, {jrec['G3']['awaiting_s6'] + jrec['G1']['awaiting_s6']} awaiting S6 of the {n_ch} answers "
        f"of changed questions; RLM-10's {jrec['G1']['from_v25']} from the frozen fig3_s6 set; every other cell the "
        f"v2.4 cell")
    try:                                          # a v2.4 row chosen that is not the cell read_collect gave
        moved = copy.deepcopy(cells24)
        k0 = next(k for k in sorted(moved) if moved[k]["kind"] == "scored")
        moved[k0]["score"] = -1
        read_v25(groups, moved)
        ok_moved = False
    except Refused as e:
        ok_moved = "not the row read" in str(e)
    say(f"  {'PASS' if ok_moved else 'FAIL'}  judge_rows_v25 (D188): read_v25 refuses a v2.4 row chosen that is not "
        f"the cell read")
    try:                                          # D201 Q2 (b): a folder with no out_s6_g1, the old look-up's result
        read_v25(groups, cells24, G1_COLLECT.parent)
        ok_old = False
    except Refused as e:
        ok_old = "key v2.5 only" in str(e)
    say(f"  {'PASS' if ok_old else 'FAIL'}  D201 Q2 (b): a folder without out_s6_g1 is refused (no key v2.4 fallback), "
        f"so a read that falls back beside the G1 collect fails")
    ok25 = ok25 and ok_moved and ok_old
    wbs = sorted(glob.glob(str(PLATE / SD_GLOB)))
    if len(wbs) != 1:
        say(f"  FAIL  expected one Source Data workbook in {rel(PLATE)}, found {len(wbs)}")
        return False
    sheet = source_data(Path(wbs[0]))
    sd, n_aside = nine_rows(sheet)
    n_stress = sum(1 for r in sheet if r.get("row") in ("tile", "setup") and r.get("config") in STRESS)
    ok_aside = n_aside == n_stress and {r["config"] for r in sd if r.get("row") in ("tile", "setup")} == set(ALL)
    say(f"  {'PASS' if ok_aside else 'FAIL'}  D201 Q2 (a): {n_aside} rows of the two stress set-ups set aside, the "
        f"nine stay")
    resub = read_resub()
    ans = sorted(q for q in groups if groups[q] == "answerable")
    cur = split_current(cells, groups, types)
    cur24 = split_current(cells24, groups, types)
    res, res_q = split_resub(resub, groups, types)
    cmp = compare(cur24, res)
    unchanged = [gate_current(cells, groups, sd), gate_resub(resub), gate_split(cur, res, res_q, groups, types, sd),
                 gate_anchors(cmp)]
    ok = not any(b for b, _ in unchanged) and ok25 and ok_aside
    say(f"  {'PASS' if ok else 'FAIL'}  unchanged: {sum(n for _, n in unchanged)} values, "
        f"{sum(len(b) for b, _ in unchanged)} differ")

    def killed(name, bad):
        say(f"  {'killed' if bad else 'SURVIVED'}  {name} ({len(bad)} differ)")
        return bool(bad)

    def cur_mut(name, f):
        c = copy.deepcopy(cells)
        f(c)
        return killed(name, gate_current(c, groups, sd)[0])

    def res_mut(name, f):
        r = copy.deepcopy(resub)
        f(r)
        return killed(name, gate_resub(r)[0])

    def score_down(c):                            # a full-pipeline 4 read as 3
        q = next(q for q in ans if c[("full_orchestrator", q)].get("score") == 4)
        c[("full_orchestrator", q)]["score"] = 3

    def rlm_failed(c):                            # an RLM-10 scored answer read as failed
        q = next(q for q in ans if c[("rlm_10", q)]["kind"] == "scored")
        c[("rlm_10", q)] = {"kind": "failed", "score": None}

    def unscored(c):                              # a routing-fix answer read as unscored
        q = next(q for q in ans if c[("orch_factual_to_documents", q)]["kind"] == "scored")
        c[("orch_factual_to_documents", q)] = {"kind": "unscored", "score": None}

    def drop(c):                                  # one naive RAG answer missing
        del c[("naive_rag", ans[0])]

    def resub_score(r):                           # a resubmission 5 read as 2
        x = next(x for x in r if x["half"] == "answerable" and x["config"] == "full_orchestrator"
                 and x["correctness_corrected"] == "5")
        x["correctness_corrected"] = "2"

    def resub_drop(r):                            # one resubmission answer missing
        i = next(i for i, x in enumerate(r) if x["half"] == "answerable" and x["config"] == "naive_rag")
        del r[i]

    # the split itself (audit 27 Oct, fig4_6 F3: `types[q] != typ` survived the old test): the types swapped
    swapped = {q: ({"extractive": "synthesis", "synthesis": "extractive"}.get(t, t)) for q, t in types.items()}
    cur_sw = split_current(cells, groups, swapped)
    cur24_sw = split_current(cells24, groups, swapped)
    res_sw, res_q_sw = split_resub(resub, groups, swapped)
    # the split at the wrong threshold: each set-up's pass at 4 read at 3
    cur_t = copy.deepcopy(cur)
    for c in ALL:
        for typ in TYPES:
            cur_t[c][f"{typ}_pass4"] = cur_t[c][f"{typ}_pass3"]
    # a computed split one pass off a stated value (the full pipeline's extractive passes at 4, F14's 55)
    cur_m = copy.deepcopy(cur24)
    cur_m["full_orchestrator"]["extractive_pass4"]["passed"] += 1
    res_m = copy.deepcopy(res)                    # and a resubmission split one pass off its stated value
    c_r, typ_r, t_r = sorted(LOG_RESUB)[0]
    res_m[c_r][f"{typ_r}_pass{t_r}"]["passed"] += 1
    # D201 Q2 (a): the filter sets aside the two named set-ups and nothing else. An eleventh set-up it does not name, a
    # nine-set-up row it drops, and a change to one of the nine's rows must each still fail gate (1).
    other = [dict(r, config="orch_other") if r.get("config") == STRESS[0] else r for r in sheet]
    lost = [r for r in sheet if not (r.get("row") == "tile" and r.get("config") == "naive_rag"
                                     and r.get("question_id") == ans[0])]
    wrong = [dict(r, correctness=-1) if r.get("row") == "tile" and r.get("config") == RLM
             and r.get("question_id") == ans[0] else r for r in sheet]
    k = [killed("a set-up the filter does not name stays on the sheet", gate_current(cells, groups, nine_rows(other)[0])[0]),
         killed("a tile of the nine missing after the filter", gate_current(cells, groups, nine_rows(lost)[0])[0]),
         killed("a tile of the nine changed after the filter", gate_current(cells, groups, nine_rows(wrong)[0])[0]),
         killed("the eleven-set-up sheet with no filter", gate_current(cells, groups, sheet)[0]),
         cur_mut("score_down", score_down), cur_mut("rlm_failed", rlm_failed), cur_mut("unscored", unscored),
         cur_mut("drop", drop), res_mut("resub_score", resub_score), res_mut("resub_drop", resub_drop),
         killed("split with the types swapped (gate 3)", gate_split(cur_sw, res_sw, res_q_sw, groups, types, sd)[0]),
         killed("split with the types swapped (gate 4)", gate_anchors(compare(cur24_sw, res_sw))[0]),
         killed("split at 3 written as 4 (gate 3)", gate_split(cur_t, res, res_q, groups, types, sd)[0]),
         killed("a current split one pass off its stated value (gate 4)", gate_anchors(compare(cur_m, res))[0]),
         killed("a resubmission split one pass off its stated value (gate 4)", gate_anchors(compare(cur24, res_m))[0])]
    say(f"mutants: {sum(k)} of {len(k)} killed")
    return ok and all(k)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", nargs="?", choices=["selftest"], help="selftest: the gates and their mutants only")
    ap.add_argument("--check", action="store_true", help="compare with the committed output, write nothing")
    a = ap.parse_args(argv)
    try:
        if a.mode == "selftest":
            ok = selftest()
            print("S489 selftest PASS" if ok else "S489 selftest FAIL")
            return 0 if ok else 1
        # D160 (6), Q18: the selftest first; nothing is written when it fails
        if not selftest(quiet=True):
            print("REFUSED: the selftest fails, nothing written (run `selftest` to see which check)", file=sys.stderr)
            return 2
        doc, bad, counts = build()
    except (Refused, fig_repro.FrozenInputError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    if bad:
        print(f"REPRODUCTION FAILED ({len(bad)} differ of {sum(counts.values())}), nothing written:", file=sys.stderr)
        for b in bad[:20]:
            print("  " + b, file=sys.stderr)
        return 2
    print(f"reproduced: {sum(counts.values())} values equal "
          f"({', '.join(f'{k} {v}' for k, v in counts.items())}); 0 mismatches")
    text = json.dumps(doc, indent=1) + "\n"
    target = OUT / "numbers.json"
    if a.check:
        ok = target.exists() and target.read_text() == text
        print(f"{rel(target)} {'byte-equal' if ok else 'DIFFERS'}")
        return 0 if ok else 1
    OUT.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    c = doc["compare"]
    print(f"compared with REVIEW_LOG / F14: {c['equal']} of {c['of']} equal")
    for r in c["rows"]:
        if not r["equal"]:
            print(f"  differs: {r}")
    print(f"wrote {rel(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
