#!/usr/bin/env python3
"""S578 (D249 O2, G19): the reading of G19's four arms on gemma3:27b, draw 1, D239 amended's 46 questions.

WHAT IT READS. R Mentori RLM-10 (stored: T2's answers to D98's 29, T2X's to the other 17), A the package RLM, B Mentori
RLM-10 with its search tools off, C with its quality gate off (findings/recompute/G19_runs/README.md). Per answer:
  - pass at 4 and at 3: the judge row's cell by Figure 3's Rule 10 (S463.cell_of; S571.pass_of: a failed answer
    counts as a fail, an unscored one is left out). R's rows are the stored ones (T2: S518_inputs/gemma3/collect.jsonl,
    set S6WT2LGEMMA; T2X: its t2xgemma collect, S574); A's, B's and C's are S579's (out_s6_w_g19, devstral, key v2.5);
  - concept recall: S577's rows (D181 reading, as S573 for G17), 0 for a failed answer (Rule 10, as S575);
  - S571's measures, by S571's own functions: mentori_trace for R, B and C (sub-calls the gate counts, sub-calls with
    paper text, root turns, distinct papers among passages_seen through S511.paper_map, gate rejections, stop reason,
    words), package_trace for A (the same columns from the package's call records and B4_rlm_ref_context.json; an
    Ollama attempt that was retried, b4.retried, is left out first, as the adapter's own counts leave it out,
    adapter.py:1408); every key paper (S511's definition); model calls and tokens (S571.calls_cost; A: calls made, tokens
    over every attempt sent, retried attempts counted apart); wall time (generation.latency_s; A: wall_s); failed.
THE READING (D239 amended, D249 O2: "judged and read as O1"). A table arm x question type (one-paper 20, many-paper
26, all 46) x measure (pass rates as S571 --g17's table: an unscored answer left out, counted). Then, read as O1 with
O1's own reader (scripts/S576_d249_hypotheses.py, imported, nothing of it changed): per question one value per arm by
O1's rule (S575.values, S576_d249.per_answer: a failed answer passes nothing and scores concept recall 0, an unscored
judge cell counts as not passing); the paired contrasts A, B, C against R and B, C against A (S576_d249.diff_interval:
mean difference, Rule 2's 95% percentile interval, S463.interval, 10,000 question resamples, seed 20261013, and how many
questions each side is higher on); D249's five hypotheses, H1 to H5 as D249 states them, by S576_d249.evaluate with
verdict=False (its parts, its H4 statistic and interval), with O1's arm names mapped: control = R, package = A, search
off = B, gate off = C. On one draw each arm's per-question mean is its one answer's value. Read DESCRIPTIVELY: one
draw, a replication on another generator, not a test (D249 O2). Each part is reported as "direction as H<n>" or not
(the sign of the value against the stated direction), and an "interval containing 0" part as whether the interval
contains 0. No part is called held, and no P value is computed.

REPRODUCE FIRST (README.md:75-79), before anything is read for A, B or C:
  - S518's stored reading of R's T2 rows: the T2 collect given is the file findings/recompute/S518_split_confirmation/
    gemma3.json records as its collect (sha256), S518's own read_rows, merge and analyse on it give gemma3.json's stored
    result exactly (D_one, D_many, I with their intervals and P), and every R cell read here (S463.cell_of) equals
    S518.read_rows' cell for the same key, kind and score;
  - T2X's: every R cell read from the T2X collect equals S518.t2x_cells' (D241's checks: one lock, one run_sha256, the
    main judge's digest, set whole:t2x*, the 17, draw 1);
  - the answer judged is the answer read: for every answer of every arm, S512.run_answers' item_sha256 (key v2.5) on the
    sink read equals the judge row's item_sha256;
  - concept recall: S577's header carries both its reproduce results (exp_01 path = L3_d181, package path = L2_d181),
    and every S577 row is the answer read (answer_sha256). Neither S518 nor T2X stored a concept recall for R (they
    store judge rows only), so R's concept recall is reproduced through the path that made it, not against a stored R
    value.
Any difference refuses and nothing is written.

    uv run --frozen python scripts/S578_g19_reading.py --reproduce-only [--r-collect-t2x F]
    uv run --frozen python scripts/S578_g19_reading.py --runs-root ~/s3_inputs/g19 --r-t2 <sink> --r-t2x <sink> \
        --manifest <g19_stored_R.json> --judge <out_s6_w_g19> --r-collect-t2x <t2xgemma_collect.jsonl> \
        --concept-recall findings/recompute/G19_concept_recall/concept_recall.jsonl [--store ~/l1_inputs/store] [--out DIR]
    uv run --frozen python scripts/S578_g19_reading_test.py           (made-up rows; no model call)

Writes findings/recompute/G19_reading/: reading.json (provenance, reproduce, table, contrasts, hypotheses, every answer's
row), reading.md (the tables), header.json (provenance). No model call.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
for p in (str(SCRIPTS), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import S463_fig2_ranking as S463  # noqa: E402
import S518_split_confirmation as S518  # noqa: E402
import S571_rlm_reading as M  # noqa: E402
import S577_g19_concept_recall as CR  # noqa: E402

GC = CR.GC
S511 = S518.S511
SCRIPT = "scripts/S578_g19_reading.py"
OUT = ROOT / "findings" / "recompute" / "G19_reading"
S518_GEMMA3 = ROOT / "findings" / "recompute" / "S518_split_confirmation" / "gemma3.json"
T2_COLLECT = ROOT / "findings" / "recompute" / "S518_inputs" / "gemma3" / "collect.jsonl"
CONTEXT = M.CONTEXT
STORE = Path.home() / "l1_inputs" / "store"
ARMS = CR.ARMS                                     # R, A, B, C
LABEL = CR.LABEL
SET = "whole:g19"                                  # S579's scope on its rows
# What a wrapper for another generator sets (S595 for G20, D260); G19's values here
S518_SOURCE = "gemma3"                             # S518's source name for R's generator (S518.SOURCES)
DECISION = "D249 O2"
TITLE = "G19 reading (D249 O2): gemma3:27b, draw 1, the 46 questions of D239 amended"
CODE_NOTE = ("R ran at T2's code (99bbc951), A, B and C at G19's PIN, so B and C differ from R in code as well as in "
             "their switch (G19_runs/README.md R1).")
GROUPS = ("one", "many", "all")
GROUP_LABEL = {"one": "one-paper", "many": "many-paper", "all": "all"}
PAIRS = [("A", "R"), ("B", "R"), ("C", "R"), ("B", "A"), ("C", "A")]
MEASURES = ("sub_calls_ok", "sub_calls_with_paper_text", "n_papers", "root_turns", "words", "model_calls", "tokens",
            "wall_s")
CODE_DEPS = ("scripts/S578_g19_reading.py", "scripts/S577_g19_concept_recall.py", "scripts/S579_g19_judge.py",
             "scripts/S576_d249_hypotheses.py", "scripts/S575_g17_contrasts.py",
             "scripts/S571_rlm_reading.py", "scripts/S463_fig2_ranking.py", "scripts/S518_split_confirmation.py",
             "scripts/S511_g2_matched_budget.py", "scripts/S512_s6_rejudge_v25.py",
             "findings/recompute/G19_runs/g19_check.py")


class Refused(Exception):
    pass


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def read_jsonl(path) -> list:
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


# ---------------------------------------------------------------------------------------------------------------
# reproduce: R's judge cells as S518 read them
# ---------------------------------------------------------------------------------------------------------------
def reproduce_s518(collect: Path, t2x: Path | None = None, stored: Path | None = None) -> dict:
    """The T2 collect (and, when gemma3.json records one, the T2X collect) are the ones S518 read for gemma3, and
    S518's reading of them, as its `run --t2x` merges them (53dfa9c5), gives its stored result exactly."""
    stored = Path(stored or S518_GEMMA3)
    st = json.loads(stored.read_text())
    want = next((x["sha256"] for x in st.get("inputs") or [] if x.get("role") == "collect"), None)
    got = sha256_file(collect)
    if got != want:
        raise Refused(f"{collect} (sha256 {got[:12]}) is not the collect {rel(stored)} records ({str(want)[:12]})")
    qs = S511.questions()
    cells, rows = S518.merge({}, S518.read_rows(Path(collect), qs))
    want_x = next((x["sha256"] for x in st.get("inputs") or [] if x.get("role") == "t2x collect"), None)
    got_x = None
    if want_x:
        if t2x is None:
            raise Refused(f"{rel(stored)} records a T2X collect ({want_x[:12]}): give --r-collect-t2x")
        got_x = sha256_file(t2x)
        if got_x != want_x:
            raise Refused(f"{t2x} (sha256 {got_x[:12]}) is not the T2X collect {rel(stored)} records ({want_x[:12]})")
        extra, x_info = S518.t2x_cells(Path(t2x), qs, S518_SOURCE, set(cells))
        cells.update(extra)
        rows.update(x_info, rows_used=len(cells))
    res = S518.analyse(cells, qs)
    if res != st["result"] or rows != st["rows"]:
        raise Refused(f"S518's reading of {collect} is not {rel(stored)}'s stored result")
    return {"stored": rel(stored), "stored_sha256": sha256_file(stored), "collect_sha256": got,
            "t2x_collect_sha256": got_x, "rows": rows,
            "equal": ["one_paper", "many_paper", "interaction"],
            "what": f"S518.read_rows, merge and analyse on the T2 collect = {stored.name}'s stored result (D_one, D_many, "
                    "I, intervals, P), exactly"}


def collect_rows(path: Path, run_id: str, qids, what: str) -> dict:
    """{question: row} of one run at draw 1 on key v2.5 from an s3_guard collect; refuses a doubled or missing key."""
    out = {}
    for r in read_jsonl(path):
        if r.get("run_id") != run_id or int(r.get("draw", 0)) != GC.DRAW or r.get("question_id") not in qids:
            continue
        if r.get("key_version") != "v2.5":
            raise Refused(f"{what}: {r.get('answer_key')} is a key {r.get('key_version')} row, not v2.5")
        if r["question_id"] in out:
            raise Refused(f"{what}: {r.get('answer_key')} has two rows")
        out[r["question_id"]] = r
    missing = sorted(set(qids) - set(out))
    if missing:
        raise Refused(f"{what}: {len(missing)} of R's keys have no row (first {missing[0]})")
    return out


def cell(row: dict, qs: dict) -> dict:
    c, why = S463.cell_of(row, qs[row["question_id"]]["group"])
    if c is None:
        raise Refused(f"{row.get('answer_key')}: {why}")
    return c


def same_cell(a: dict, b: dict) -> bool:
    return a["kind"] == b["kind"] and a.get("score") == b.get("score")


def r_judge(t2_collect: Path, t2x_collect: Path | None, q: dict, qs: dict) -> tuple[dict, dict]:
    """R's rows ({question: judge row}) and the reproduce of S518's reading of them (module docstring)."""
    rid = GC.run_id("R")
    rep = {"s518": reproduce_s518(t2_collect, t2x_collect)}
    s518_t2 = S518.read_rows(Path(t2_collect), qs)
    rows = collect_rows(t2_collect, rid, set(q["t2_d98"]), "R T2 collect")
    bad = [i for i, r in rows.items() if not same_cell(cell(r, qs), s518_t2[("rlm_10", i, 1)][0])]
    if bad:
        raise Refused(f"R T2: {len(bad)} cells differ from S518.read_rows' (first {bad[0]})")
    rep["t2_cells_equal_s518"] = len(rows)
    if t2x_collect is not None:
        mine, info = S518.t2x_cells(Path(t2x_collect), qs, S518_SOURCE, set(s518_t2))
        x = collect_rows(t2x_collect, rid, set(q["t2x"]), "R T2X collect")
        bad = [i for i, r in x.items() if ("rlm_10", i, 1) not in mine or not same_cell(cell(r, qs), mine[("rlm_10", i, 1)])]
        if bad:
            raise Refused(f"R T2X: {len(bad)} cells differ from S518.t2x_cells' (first {bad[0]})")
        rows.update(x)
        rep["t2x_cells_equal_s518_t2x_cells"] = len(x)
        rep["t2x_collect_sha256"] = sha256_file(t2x_collect)
    return rows, rep


# ---------------------------------------------------------------------------------------------------------------
# A, B, C: S579's rows
# ---------------------------------------------------------------------------------------------------------------
def main_judge_digest() -> str:
    import tomllib
    lock = tomllib.loads((ROOT / "experiments" / "LOCK.toml").read_text())
    return lock["models"][lock["judge"]["model"]]["digest"]


def new_judge(judge: Path, q: dict) -> dict:
    """{arm: {question: row}} for A, B, C from S579's out (S463.latest_by_ident), each row of set whole:g19, key v2.5,
    the main judge, one lock and one run_sha256 over all."""
    import lock_equiv
    runs = {GC.run_id(a): a for a in ("A", "B", "C")}
    digest = main_judge_digest()
    out = {a: {} for a in ("A", "B", "C")}
    locks, shas = set(), set()
    for r in S463.latest_by_ident(Path(judge)).values():
        a = runs.get(r.get("run_id"))
        if a is None:
            raise Refused(f"{judge}: a row of run {r.get('run_id')}, not one of G19's three")
        if r.get("questions") != SET or r.get("key_version") != "v2.5" or int(r.get("draw", 0)) != 1:
            raise Refused(f"{r.get('answer_key')}: set {r.get('questions')}, key {r.get('key_version')}, draw "
                          f"{r.get('draw')}: not S579's")
        no_call = (r.get("a") or {}).get("status") == "no_answer" and "model_digest" not in (r.get("a") or {})
        if (not no_call and (r.get("a") or {}).get("model_digest") != digest) or r.get("judge") not in (None, "main"):
            raise Refused(f"{r.get('answer_key')}: not the main judge's row")
        if r.get("answer_key") != GC.answer_key(a, r["question_id"]) or r["question_id"] not in q["kind"]:
            raise Refused(f"{r.get('answer_key')}: not a key of {a}")
        locks.add(r.get("lock_sha256"))
        shas.add(r.get("run_sha256"))
        out[a][r["question_id"]] = r
    if len(locks) != 1 or not locks <= lock_equiv.EQUIVALENT or len(shas) != 1:
        raise Refused(f"{judge}: rows under {len(locks)} locks ({sorted(str(x)[:8] for x in locks)}) and {len(shas)} "
                      f"run_sha256, not one lock lock_equiv accepts and one run_sha256")
    for a, rows in out.items():
        missing = sorted(set(q["ids"]) - set(rows))
        if missing:
            raise Refused(f"{a}: {len(missing)} of the 46 have no judge row (first {missing[0]})")
    return out


def answer_items(sink: Path, store: Path | None) -> dict:
    """{answer_key: item_sha256} as S512 builds the judge's item (key v2.5) from a sink."""
    import S512_s6_rejudge_v25 as S512
    return {x["answer_key"]: x["item_sha256"] for x in S512.run_answers(Path(sink), None, store)}


def check_judged_is_read(arms: dict, judged: dict, store: Path | None) -> dict:
    """Every answer read is the answer judged (S512's item_sha256 on the sink = the row's)."""
    cache, n = {}, 0
    for a in ARMS:
        for i, x in arms[a].items():
            sink = x["sink"]
            if sink not in cache:
                cache[sink] = answer_items(sink, None if a == "A" else store)
            got, want = cache[sink].get(x["answer_key"]), judged[a][i].get("item_sha256")
            if got is None or got != want:
                raise Refused(f"{a} {x['answer_key']}: the judge row's item_sha256 {str(want)[:12]} is not the answer "
                              f"read ({str(got)[:12]})")
            n += 1
    return {"answers": n, "what": "S512.run_answers' item_sha256 (key v2.5) on each sink read = the judge row's"}


# ---------------------------------------------------------------------------------------------------------------
# concept recall: S577's rows
# ---------------------------------------------------------------------------------------------------------------
def concept_recall(path: Path, arms: dict) -> tuple[dict, dict]:
    """{arm: {question: S577 row}}; S577's header must carry both reproduce results, every row its answer."""
    header = json.loads((Path(path).parent / "header.json").read_text())
    rep = header.get("reproduce") or {}
    for k in ("exp_01", "package"):
        v = rep.get(k) or {}
        if not v.get("compared") or v.get("equal") != v.get("compared"):
            raise Refused(f"{path}: S577's header has no passed {k} reproduce")
    out = {a: {} for a in ARMS}
    for r in read_jsonl(path):
        a, i = r["arm"], r["question_id"]
        if a not in out or i not in arms[a] or r["answer_key"] != arms[a][i]["answer_key"]:
            raise Refused(f"{path}: row {r.get('answer_key')} of arm {a} is not an answer read here")
        rec = arms[a][i]["rec"]
        text = (rec.get("answer") if a == "A" else (rec.get("generation") or {}).get("answer")) or ""
        if r["answer_sha256"] != hashlib.sha256(text.encode()).hexdigest():
            raise Refused(f"{path}: {r['answer_key']} was scored on another answer")
        out[a][i] = r
    for a in ARMS:
        if set(out[a]) != set(arms[a]):
            raise Refused(f"{path}: {a} has {len(out[a])} rows, not {len(arms[a])}")
    return out, {"rows": str(path), "rows_sha256": sha256_file(path), "header_reproduce": rep}


# ---------------------------------------------------------------------------------------------------------------
# traces: S571's functions
# ---------------------------------------------------------------------------------------------------------------
def paper_map(ids: set) -> dict:
    return S511.paper_map(ids)


def paper_index():
    ctx = json.loads(CONTEXT.read_text())
    return M.PaperIndex(M.context_texts(ctx)), sha256_file(CONTEXT)


def package_rows(arm_a: dict) -> dict:
    """{question: (answer record, its kept call records, retried attempts)} from A's calls.jsonl."""
    need = {x["rec"]["ctx_uid"]: x["rec"] for x in arm_a.values()}
    sink = next(iter(arm_a.values()))["sink"]
    with open(Path(sink) / "calls.jsonl", encoding="utf-8") as f:
        by_ctx = M.calls_by_ctx(f, need)
    out = {}
    for i, x in arm_a.items():
        rec = x["rec"]
        calls = by_ctx[rec["ctx_uid"]]
        kept = [c for c in calls if not (c.get("b4") or {}).get("retried")]
        listed = sorted(rec["calls"]["seqs"])
        if sorted(c["seq"] for c in calls) != listed:
            raise Refused(f"{x['answer_key']}: its call records are not the seqs it lists")
        out[i] = (rec, calls, kept)
    return out


def traces(arms: dict, qs: dict) -> dict:
    """{(arm, question): S571's measures for that answer}."""
    from experiments.runner.gemini_client import raised_before_d89
    ids = {p for a in ("R", "B", "C") for x in arms[a].values()
           for p in ((((x["rec"].get("generation") or {}).get("rlm") or {}).get("metadata") or {}).get("passages_seen")
                     or [])}
    pmap = paper_map(ids)
    out = {}
    for a in ("R", "B", "C"):
        for i, x in arms[a].items():
            rec = x["rec"]
            g = rec.get("generation") or {}
            md = (g.get("rlm") or {}).get("metadata") or {}
            t = M.mentori_trace(rec, pmap)
            t.update(M.calls_cost(g.get("calls") or []), wall_s=g.get("latency_s"), retried_attempts=None,
                     search_attempts=(md.get("search_tools") or {}).get("n_attempts"), forced_final=None)
            out[(a, i)] = t
    pindex, ctx_sha = paper_index()
    for i, (rec, calls, kept) in package_rows(arms["A"]).items():
        if (rec.get("context") or {}).get("file_sha256") != ctx_sha:
            raise Refused(f"{rec['answer_key']}: its context file is not {rel(CONTEXT)}")
        t = M.package_trace({**rec, "calls": {**rec["calls"], "seqs": sorted(c["seq"] for c in kept)}}, kept, pindex,
                            raised_before_d89)
        t.update(model_calls=len(kept), tokens=M.calls_cost(calls)["tokens"], wall_s=rec.get("wall_s"),
                 retried_attempts=len(calls) - len(kept), search_attempts=None, rejections=None)
        out[("A", i)] = t
    for (a, i), t in out.items():
        key_papers = set(qs[i]["papers"])
        t["every_key_paper"] = key_papers <= set(t["papers"])
        t["key_papers"] = sorted(key_papers)
    return out


# ---------------------------------------------------------------------------------------------------------------
# the reading
# ---------------------------------------------------------------------------------------------------------------
def answer_rows(arms, q, qs, judged, crs, tr) -> list:
    rows = []
    for a in ARMS:
        for i in q["ids"]:
            c = cell(judged[a][i], qs)
            failed = CR.failed_of(a, arms[a][i]["rec"])
            crv = crs[a][i]["concept_recall"]
            if crv is None and not failed:              # review F2: as S576, a scored answer must carry concept recall
                raise SystemExit(f"REFUSED: {a} {i} did not fail but has no concept recall; nothing written")
            t = tr[(a, i)]
            rows.append({"arm": a, "question_id": i, "kind": q["kind"][i], "answer_key": arms[a][i]["answer_key"],
                         "source": arms[a][i]["source"], "cell": c["kind"], "score": c.get("score"),
                         "pass4": M.pass_of(c, 4), "pass3": M.pass_of(c, 3), "failed": failed,
                         "concept_recall": 0.0 if failed else float(crv),
                         **{k: v for k, v in t.items() if k not in ("papers_deep_by_repeats_only",)}})
    return rows


def table(rows: list) -> list:
    out = []
    for a in ARMS:
        for g in GROUPS:
            rs = [r for r in rows if r["arm"] == a and (g == "all" or r["kind"] == g)]
            row = {"arm": a, "label": LABEL[a], "group": g, "answers": len(rs)}
            for t in (4, 3):
                v = [r[f"pass{t}"] for r in rs if r[f"pass{t}"] is not None]
                row[f"pass{t}_pct"] = 100 * sum(v) / len(v) if v else None
                row[f"pass{t}_answers_read"] = len(v)
            row["unscored"] = sum(1 for r in rs if r["cell"] == "unscored")
            row["concept_recall_mean"] = sum(r["concept_recall"] for r in rs) / len(rs) if rs else None
            row["concept_recall"] = M.quart([r["concept_recall"] for r in rs])
            for m in MEASURES:
                row[m] = M.quart([r.get(m) for r in rs if r.get(m) is not None])
            row["every_key_paper"] = [sum(1 for r in rs if r["every_key_paper"]), len(rs)]
            row["failed"] = sum(1 for r in rs if r["failed"])
            row["stop_reasons"] = dict(sorted(Counter(str(r["stop_reason"]) for r in rs).items()))
            row["failed_by_stop_reason"] = dict(sorted(Counter(str(r["stop_reason"]) for r in rs if r["failed"]).items()))
            row["sub_calls_under_3"] = sum(1 for r in rs if (r.get("sub_calls_ok") or 0) < M.MIN_LLM_CALLS)
            if a != "A":
                row["gate_rejected_once"] = sum(1 for r in rs if (r.get("rejections") or 0) >= 1)
            else:
                row["forced_final"] = sum(1 for r in rs if r.get("forced_final"))
                row["retried_attempts"] = sum(r.get("retried_attempts") or 0 for r in rs)
            if a == "B":
                row["search_attempts_total"] = sum(r.get("search_attempts") or 0 for r in rs)
                row["answers_with_search_attempt"] = sum(1 for r in rs if r.get("search_attempts"))
            out.append(row)
    return out


def d249():
    """D249 O1's reader (scripts/S576_d249_hypotheses.py): its contrasts, H4 statistic and hypothesis parts are used
    here unchanged, so G19 is read as O1 (D249 O2); its verdicts are not (evaluate(verdict=False))."""
    import S576_d249_hypotheses as D
    return D


ARM_D249 = {"R": "ctrl", "A": "package", "B": "search_off", "C": "gate_off"}     # O1's arm names
D249_ARM = {v: k for k, v in ARM_D249.items()}


def values(rows: list, arm: str) -> dict:
    """{question: {"group", "pass4", "cr"}} by O1's rule (S576_d249.per_answer, S575.values): a failed answer passes
    nothing and scores concept recall 0; an unscored judge cell counts as not passing (counted in the table)."""
    return {r["question_id"]: {"group": r["kind"], "pass4": 0 if r["failed"] else int(r["pass4"] or 0),
                               "cr": 0.0 if r["failed"] else float(r["concept_recall"])}
            for r in rows if r["arm"] == arm}


def contrasts(rows: list) -> list:
    """a minus b per question, S576_d249.diff_interval (S575's contrast without its P value)."""
    D = d249()
    v = {a: values(rows, a) for a in ARMS}
    return [{"a": a, "b": b, "group": g, "metric": m, **D.diff_interval(v[a], v[b], g, m)}
            for a, b in PAIRS for g in GROUPS for m in ("pass4", "cr")]


def reading_of(h: str, x: dict) -> tuple[bool, str]:
    """The descriptive reading of one part on one draw: the direction D249 states (below, above), or whether the
    interval contains 0 where D249 states that (contains)."""
    v, (lo, hi) = x["diff"], x["ci95"]
    if x["criterion"] == "below":
        return v < 0, f"direction as {h}" if v < 0 else f"direction not as {h}"
    if x["criterion"] == "above":
        return v > 0, f"direction as {h}" if v > 0 else f"direction not as {h}"
    ok = lo <= 0 <= hi
    return ok, f"interval contains 0, as {h} states" if ok else f"interval excludes 0, not as {h} states"


def part_text(p: dict) -> str:
    m = "concept recall" if p["metric"] == "cr" else "pass at 4 (points)"
    if p["kind"] == "h4":
        a = D249_ARM[p["a"]]
        return f"(R minus {a}) on one-paper minus (R minus {a}) on many-paper, {m}"
    return f"{LABEL[D249_ARM[p['a']]]} minus {LABEL[D249_ARM[p['b']]]}, {m}, {p['group']} {p['n_questions']}"


def hypotheses(rows: list) -> list:
    """S576_d249.evaluate(verdict=False) on the draw-1 values (one answer per arm and question, so the per-question
    mean of O1 is the answer's value), each part with its descriptive reading."""
    D = d249()
    res = D.evaluate({ARM_D249[a]: values(rows, a) for a in ARMS}, verdict=False)
    out = []
    for h, x in res.items():
        for p in x["parts"]:
            ok, words = reading_of(h, p)
            out.append({"hypothesis": h, "wording": x["wording"], "text": part_text(p), **p, "value": p["diff"],
                        "as_stated": ok, "reading": words})
    return out


# ---------------------------------------------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------------------------------------------
def git(*args) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout


def provenance(argv: list, shas: dict) -> dict:
    return {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
            "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "git_head": git("rev-parse", "HEAD").strip(),
            "dependencies_changed_from_head": sorted(ln[3:] for ln in git("status", "--porcelain", "--",
                                                                            *CODE_DEPS).splitlines() if ln.strip()),
            "code_sha256": {d: sha256_file(ROOT / d) for d in CODE_DEPS if (ROOT / d).exists()},
            "command": " ".join([f"uv run --frozen python {SCRIPT}"] + list(argv)), "inputs_sha256": shas,
            "decision": DECISION, "draw": 1, "boot": S463.N_BOOT, "seed": S463.SEED}


def fq(t, nd=0) -> str:
    return M.fq(t, nd)


def write_md(R: dict, path: Path) -> None:
    pv = R["_provenance"]
    pct = lambda v: "n/a" if v is None else f"{v:.1f}%"  # noqa: E731
    L = [f"# {TITLE}", "",
         f"Written by `{pv['command']}` at {pv['at']} (HEAD {pv['git_head'][:8]}; code dependencies changed from HEAD: "
         f"{', '.join(pv['dependencies_changed_from_head']) or 'none'}). One draw, descriptive: no hypothesis is held "
         f"or not held here, and no P value is computed ({DECISION}: a replication on another generator, not a test). "
         f"{CODE_NOTE}", "", "## Reproduced first", ""]
    rp = R["reproduce"]
    L += [f"- {rp['judge']['s518']['what']} ({rp['judge']['s518']['stored']}).",
          f"- R's T2 cells equal S518.read_rows' for {rp['judge']['t2_cells_equal_s518']} keys; R's T2X cells equal "
          f"S518.t2x_cells' for {rp['judge'].get('t2x_cells_equal_s518_t2x_cells')} keys.",
          f"- The answer judged is the answer read for {rp['judged_is_read']['answers']} answers (S512 item_sha256).",
          f"- Concept recall (S577): exp_01 path {rp['concept_recall']['header_reproduce']['exp_01']['equal']} of "
          f"{rp['concept_recall']['header_reproduce']['exp_01']['compared']} equal L3_d181; package path "
          f"{rp['concept_recall']['header_reproduce']['package']['equal']} of "
          f"{rp['concept_recall']['header_reproduce']['package']['compared']} equal L2_d181. S518 and T2X stored no "
          "concept recall for R.", "",
          "## By arm and question type", "",
          "Pass at 4 and 3: share of answers scoring at least 4 (3), failed answers as fails, unscored left out. Concept "
          "recall: mean, failed answers 0. Other cells: median [quartile 25, quartile 75] over answers (S571's "
          "definitions; papers for R, B, C are those among the passages returned to the code, an upper bound; for A "
          "those matched in a successful sub-call's prompt).", "",
          "| Arm | Type | Answers | Pass at 4 | Pass at 3 | Concept recall | Sub-calls | With paper text | Papers | "
          "Every key paper | Root turns | Words | Model calls | Tokens | Wall s | Failed | Unscored |",
          "|---|---|---:|---:|---:|---:|---|---|---|---|---|---|---|---|---|---:|---:|"]
    for r in R["table"]:
        L.append(f"| {r['label']} | {GROUP_LABEL[r['group']]} | {r['answers']} | {pct(r['pass4_pct'])} | "
                 f"{pct(r['pass3_pct'])} | {r['concept_recall_mean']:.3f} | {fq(r['sub_calls_ok'])} | "
                 f"{fq(r['sub_calls_with_paper_text'])} | {fq(r['n_papers'])} | {r['every_key_paper'][0]}/"
                 f"{r['every_key_paper'][1]} | {fq(r['root_turns'])} | {fq(r['words'])} | {fq(r['model_calls'])} | "
                 f"{fq(r['tokens'])} | {fq(r['wall_s'])} | {r['failed']} | {r['unscored']} |")
    L += ["", "Stop reasons (all answers; failed answers in brackets):", ""]
    for r in R["table"]:
        if r["group"] != "all":
            continue
        extra = []
        if "gate_rejected_once" in r:
            extra.append(f"gate rejected at least once {r['gate_rejected_once']}")
        if "search_attempts_total" in r:
            extra.append(f"refused search attempts {r['search_attempts_total']} in {r['answers_with_search_attempt']} "
                         "answers")
        if "forced_final" in r:
            extra.append(f"forced final {r['forced_final']}, retried attempts {r['retried_attempts']}")
        extra.append(f"under 3 sub-calls {r['sub_calls_under_3']}")
        L.append(f"- {r['label']}: " + ", ".join(f"{k} {v}" for k, v in r["stop_reasons"].items())
                 + f" ({', '.join(f'{k} {v}' for k, v in r['failed_by_stop_reason'].items()) or 'none failed'}); "
                 + "; ".join(extra))
    L += ["", "## Paired contrasts, a minus b per question (read as O1)", "",
          "Per question one value per arm by O1's rule (a failed answer passes nothing and scores concept recall 0; an "
          "unscored judge cell counts as not passing). Pass at 4 in points, concept recall as a share; mean difference "
          "with Rule 2's 95% percentile interval (S576_d249.diff_interval: 10,000 question resamples, seed 20261013), "
          "descriptive; questions where a or b is higher.", "",
          "| a | b | Type | Metric | n | Mean a | Mean b | a - b | 95% interval | a higher | b higher |",
          "|---|---|---|---|---:|---:|---:|---:|---|---:|---:|"]
    for c in R["contrasts"]:
        if not c["n_questions"]:
            continue
        f = "{:.1f}" if c["metric"] == "pass4" else "{:.3f}"
        L.append(f"| {c['a']} | {c['b']} | {GROUP_LABEL[c['group']]} | {c['metric']} | {c['n_questions']} | "
                 f"{f.format(c['mean_a'])} | {f.format(c['mean_b'])} | {f.format(c['diff'])} | "
                 f"{f.format(c['ci95'][0])} to {f.format(c['ci95'][1])} | {c['a_higher']} | {c['b_higher']} |")
    L += ["", "## D249's hypotheses, read on one draw", "",
          "As D249 states them (package = A, control = R, search off = B, gate off = C), read descriptively: whether the "
          "difference has the direction D249 states, or whether the interval contains 0 where D249 states that. Not a "
          "test (D249 O2).", ""]
    for h, w in R["hypotheses_text"].items():
        L.append(f"- **{h}** (D249): {w}.")
    L += ["", "Computed by O1's reader, S576_d249.evaluate(verdict=False), on the draw-1 values.", "",
          "| Hypothesis | Part | Contrast | Value | 95% interval | Stated | Reading |", "|---|---|---|---:|---|---|---|"]
    for p in R["hypotheses"]:
        f = "{:.1f}" if p["metric"] == "pass4" else "{:.3f}"
        L.append(f"| {p['hypothesis']} | {p['part']} | {p['text']} | {f.format(p['value'])} | {f.format(p['ci95'][0])} "
                 f"to {f.format(p['ci95'][1])} | {p['criterion']} 0 | {p['reading']} |")
    path.write_text("\n".join(L) + "\n")


def build(a) -> dict:
    q = CR.questions()
    qs = S511.questions()
    judged_r, rep_r = r_judge(a.r_collect_t2, a.r_collect_t2x, q, qs)
    arms, inputs = CR.read_arms(a.runs_root, a.r_t2, a.r_t2x, a.manifest, q)
    judged = {"R": judged_r, **new_judge(a.judge, q)}
    rep_items = check_judged_is_read(arms, judged, a.store)
    crs, rep_cr = concept_recall(a.concept_recall, arms)
    tr = traces(arms, qs)
    rows = answer_rows(arms, q, qs, judged, crs, tr)
    cs = contrasts(rows)
    inputs.update({str(a.r_collect_t2): sha256_file(a.r_collect_t2), str(a.r_collect_t2x): sha256_file(a.r_collect_t2x),
                   str(a.concept_recall): sha256_file(a.concept_recall), str(CONTEXT): sha256_file(CONTEXT)})
    for f in sorted(Path(a.judge).glob("judge/*/judge_passages.jsonl")):
        inputs[str(f)] = sha256_file(f)
    for x in arms["A"].values():
        inputs[str(Path(x["sink"]) / "calls.jsonl")] = sha256_file(Path(x["sink"]) / "calls.jsonl")
        break
    return {"reproduce": {"judge": rep_r, "judged_is_read": rep_items, "concept_recall": rep_cr},
            "arms": LABEL, "questions": {"n": len(q["ids"]), "one": len(q["one_paper"]), "many": len(q["many_paper"]),
                                         "sha256": q["sha256"]},
            "hypotheses_text": d249().WORDING, "table": table(rows), "contrasts": cs, "hypotheses": hypotheses(rows),
            "answers": rows, "_inputs": inputs}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs-root", type=Path)
    ap.add_argument("--r-t2", type=Path)
    ap.add_argument("--r-t2x", type=Path)
    ap.add_argument("--manifest", type=Path, default=GC.MANIFEST)
    ap.add_argument("--judge", type=Path, help="S579's out_s6_w_g19 folder")
    ap.add_argument("--r-collect-t2", type=Path, default=T2_COLLECT)
    ap.add_argument("--r-collect-t2x", type=Path, help="T2X's t2xgemma_collect.jsonl")
    ap.add_argument("--concept-recall", type=Path, default=CR.OUT / "concept_recall.jsonl")
    ap.add_argument("--store", type=Path, default=STORE, help="the Chroma folder exp_01's passage ids resolve against")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--reproduce-only", action="store_true")
    a = ap.parse_args(argv)
    for k in ("runs_root", "r_t2", "r_t2x", "manifest", "judge", "r_collect_t2", "r_collect_t2x", "concept_recall",
              "store", "out"):
        if getattr(a, k) is not None:
            setattr(a, k, getattr(a, k).expanduser())
    errors = (Refused, CR.Refused, GC.Refused, S518.Refused, S511.Refused, M.Refused, S463.Refused)
    try:
        if a.reproduce_only:
            _, rep = r_judge(a.r_collect_t2, a.r_collect_t2x, CR.questions(), S511.questions())
            print(f"reproduced: {rep['s518']['what']}")
            print(f"reproduced: R's T2 cells equal S518.read_rows' for {rep['t2_cells_equal_s518']} keys"
                  + (f"; R's T2X cells equal S518.t2x_cells' for {rep['t2x_cells_equal_s518_t2x_cells']} keys"
                     if "t2x_cells_equal_s518_t2x_cells" in rep else " (no --r-collect-t2x: T2X's 17 not read)"))
            return 0
        need = [k for k in ("runs_root", "r_t2", "r_t2x", "judge", "r_collect_t2x") if getattr(a, k) is None]
        if need:
            raise Refused(f"--{', --'.join(n.replace('_', '-') for n in need)} required")
        R = build(a)
    except errors as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    except SystemExit as e:                       # S512's own refusals (run_answers) raise SystemExit
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    pv = provenance(argv, R.pop("_inputs"))
    R = {"_provenance": pv, **R}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "reading.json").write_text(json.dumps(R, indent=1, default=list) + "\n")
    write_md(R, a.out / "reading.md")
    (a.out / "header.json").write_text(json.dumps(pv, indent=1) + "\n")
    for p in R["hypotheses"]:
        print(f"{p['hypothesis']}: {p['part']}: {p['value']:.3f} [{p['ci95'][0]:.3f}, {p['ci95'][1]:.3f}], {p['reading']}")
    print(f"wrote {rel(a.out)} ({len(R['answers'])} answers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
