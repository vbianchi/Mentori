#!/usr/bin/env python3
"""S393 - early claims check: do the current answer key and the devstral judge reverse a claim of the paper?

WHY. Valerio decides on Sunday 11 October whether to ask for time (notes/planning/SUBMISSION_PLAN_2026-10-09.md,
"What decides Sunday afternoon", point 4: "Nothing in the re-judged numbers reverses a claim of the paper. A
reversal means rewriting text, not only updating numbers"). The re-judge that decides it (S373, devstral-small-2:24b
on the judge's key S373.KEY, ground truth v2.2 from 9 October and v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45), item 11) is partial while it
runs. Reports name the key version read from S373.KEY's "version" field (KV below); output field names keep v22. This script takes the paper's main judge-based claims, the
ones notes/planning/PHASE3_WORKLIST.md marks category d and the S318/S323 registries bind to a script, and recomputes
each on the rows already judged, with the statistic of the script that prints the published value. Per claim it
says holds, weakens, reverses, or not enough data, with the coverage of the rows it rests on. It is meant to be run
again as the ledgers fill; at full coverage its verdicts are the answer to point 4.

HOW.
  New scores. Every production S373 ledger of the main judge, S373_devstral_<source>[_shard<k>of<N>].jsonl: this
    machine's, and the Mac Studio's, copied read-only with scp into a temporary directory that is deleted at the end
    (never into the repository); the second judge's, S373_gptoss_<source>.jsonl, the same way, for J1 and the
    answer-shift table only. Side ledgers (_probe*, _test50, any other _<out>) are never read. A shard still running
    on the Beelink is not read until S380 fetches its ledger to this machine. A final line without a newline is a row being
    written and is skipped. A row counts only if its status is ok or ok_output_limit, its key_hash is the current
    hash of its question (S373.key_hash on S373.KEY, data/ground_truth_v2/all_v2_4.json since 11 October, Q50) and its
    question is not one of the six dropped under D7 (S373.AS_V1 "dropped_d7", ground_truth_v2_4_as_v1.json, whose
    source_v<version>_sha256 must be the sha256 of S373.KEY). A row on one of the ten false-premise questions
    (TEN: answer_type "refutation" in S373.KEY, OOD_041 to OOD_050; Q51 and D5, Valerio, 11 October) enters no
    claim's table: S373 judges them with the answerable prompt against the refutation, and the rows of exp04 and
    exp06 go to their own group (The ten, below). Rows on the same answer key
    from several files or machines collapse to one (S390); two scored rows with different scores are listed as
    conflicts and the earlier is kept. Each key is resolved through S374's reader (scripts/s374) to the answer it
    scores, or, for S373's own exp04 source (keys exp04|config|question|i), through S21's row reader as S373 does;
    the row's question and answer_chars must match that answer (S388 rule 5), or the row is dropped. One answer
    reached under two keys (exp04 in both the exp04 and the paper_qa sources) counts once, the first read.
  Original scores. The deposited qwen3-coder:30b scores in the state the paper prints them: exp04 and exp06 from
    S281.corrected_rows (the complete-answer re-judge); the naive RAG baseline's deposited scores, as S78 reads them;
    MiniCheck precision against the source papers per exp04 answer from S19_minicheck_source_k3.jsonl (no judge, no
    key, so the same value under both judges); exp05 from S66.load
    (correctness_rejudged; the verified_pass arm is left out, since the paper uses the S314 rerun's answers there
    and no claim below compares it); the depth sweep's RLM draws from S78's loaders; the strategy replication from
    findings/recompute/S141_phase5_tidy_corrected.csv and S320_replication_two_tidy.csv (both judges); the depth
    sweep's concept recall from the deposit and S383 (v1 and current-key _v22 columns). The S382 and S383 CSVs record
    the key they were scored against in their '#' lines above the header (S382: key_sha256 in a '# {json}' line;
    S383: the sha256 on its '# key v<version>: <path> sha256 <hex>' line, the '# key v1 (gate)' line being the v1
    key). The current-key column of a file is used only when that recorded sha256 is the sha256 of S373.AS_V1;
    otherwise the claim that rests on it (E11 on S382, D1 on S383) is "not enough data: <file> was scored on
    another key" and its current-key value is not computed. Their v1 columns, which the gate reads, do not depend
    on the current key and are read either way.
  Claims. CLAIMS below. Each is one function on a table of per-answer scores, run unchanged on the original and on
    the new scores. R1 and S3 run the bootstrap code of scripts/S320_strategy_replication.R and
    scripts/S67_corpus_two_axis_model.R, copied into Rscript below (same seed, same 10,000 resamples): R1 on a CSV of
    the rows in S320's row order; S3 rebuilds S67's data step in R and takes each row's pass value from a CSV by key.
  Five results per claim:
    (a) published      the function on the original scores, all rows, as the paper was computed
    (b) original, D7   the same with the six D7 questions dropped (the effect of D7 alone)
    (b') original, D7 and Q51   (b) with the ten false-premise questions removed from the refusal units, the rows
                       not answerable (drop_q51): refusal is measured only on the out-of-domain questions with no
                       answer in the papers (D5). The original judge scored the ten for refusal only, so this removes
                       all their rows, in exp04 and exp06; E6 and P4 are the claims that change. For every other claim
                       (b') is (b): the ten are in no other claim's units.
    (c) original, matched rows    only the answers the new judge has scored, on the original scores, within (b')
    (d) devstral, current key, matched rows   the same answers on the new scores
  Coverage = units in (c) over units in (b'): answers, or question pairs for a paired test, or rows of the model. Each
    line also gives the questions the matched units come from and, for the replication, the generators: the Mac
    Studio judges the replication in S373's key order, one generator after another, so its rows are not a random
    sample of the claim's units.
  Verdict. Every claim has a rule (RULES in each claim) that takes a result and a reference result. Below full
    coverage the verdict is the rule on (d) with (c) as the reference: the same answers under the two scorings, so
    a matched subset that happens to show a smaller or larger effect than the published one moves the reference with
    it. (The rule on (d) with the published value as reference is reported beside it, not used.) Guards, in order:
    either side below the claim's minimum count (each claim's ok), or (c) reversing the claim against the published
    value: "not enough data"; (c) only weakening it: only a "reverses" in (d) stands, anything else is "not enough
    data"; a claim of no difference (S2, E10) cannot be confirmed on a sample, so "holds" needs 80% coverage; a
    claim made for every generator (R1, R3) "holds" only once all seven have data, since the Mac Studio reaches
    them one after another (the calibration found the miss this prevents). Every verdict below full coverage is
    provisional and carries its coverage. At full coverage (c) is (b') and the
    verdict is the rule on (d) with the published value as reference, so D7, Q51 and the new scores count together;
    column (b) shows what D7 does alone, column (b') what D7 and the removal of the ten do together.
  The ten (Q51, D5). They have a correct answer in the papers, the refutation. Beside each claim whose published
    units include them (E6 and P4, out-of-domain refusal) they are reported as their own group, per configuration of
    the claim: on the original scores, the share refused (refusal accuracy 3 or more, the published scoring, judged
    with the decline prompt); on the new scores, the share passed (correctness 3 or more against the refutation,
    the answerable prompt), on the answers the new judge has scored whose length matches the original's. No rule
    decides on the group.
  No-judge claims. The depth saturation (D1) and the concept-recall ranking (E11) use no judge: concept recall
    against the key. Their current-key values are complete (S383, S382), so coverage is 100% and the verdict is
    final, once the file was scored on the current key (Original scores, above).
  Calibration (--calibrate). Real independent score sets stand in for the new judge, and the claims are re-run on
    random subsets of their answers (5%, 15% and 40%, 20 draws each; and, for the replication, the first 5%, 15%
    and 40% in S373's key order, the way the Mac Studio fills it). Each subset's verdict is compared with the verdict
    the same stand-in gives on all its answers. Stand-ins: the original gpt-oss:120b scores as the main judge for R1
    to R3 (an independent judge, all replication answers); the two original judges swapped for J1 (a planted
    reversal: a check that the reversal is found, not a test of false alarms); qwen3-coder's re-judge of 8 October
    on ground truth v2.1 (S373_qwen_paper_qa.jsonl, 74 questions, complete answers) for the claims on exp04, exp05,
    exp06, the naive baseline and the depth draws, where the reference "published" value is the original on the
    stand-in's own answers. Stand-in B is merged without the key-hash check, so its rows on the ten (decline prompt,
    v2.1) are read; they leave the refusal units as in the main run, and the stand-ins run on (b'). A provisional
    verdict more severe than the all-answers verdict is a false alarm; less
    severe, a miss. A claim the original scores do not give on a stand-in's own answers is untestable there and left
    out of the summary. Writes S393_early_claims_calibration.{json,md}; the main report cites it, and marks it stale
    when this script has changed since.
GATE (reproduce before writing). (a) must reproduce every published value of every claim at its printed precision,
  and the two R statistics must reproduce findings/recompute/S320_strategy_replication.json and
  S67_corpus_two_axis_model.json to the stored decimals; E11 must reproduce S04b's stored concept recall per strategy.
  Any failure exits before anything is written. --calibrate runs the same gate first.
Loads no model and calls no LLM; the GPUs are not touched. Reads no human rating and nothing under response/.

    uv run python scripts/S393_early_claims.py [--no-remote]
    uv run python scripts/S393_early_claims.py --calibrate

Writes findings/recompute/S393_early_claims.json and findings/recompute/S393_early_claims.md: per claim the five
results, coverage, sample and verdict, and for E6 and P4 the ten's group; the ledgers read, with sha256; where the Mac Studio's replication ledger stands
in S373's order; and, on the matched answers, how far each per-answer indicator moves between the two judges (exact
McNemar), which is not a claim.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "s374"))
from machine import RECOMPUTE, RESULTS, ROOT, shown  # noqa: E402
import stats_full as sf  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402

AS_V1 = S373.AS_V1   # the judge's key in the v1 format: ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45) (S381 --key 2.4)
KV = "v" + str(json.loads(S373.KEY.read_text(encoding="utf-8"))["version"])   # the current key's label, "v2.4"
_KEY_RECORDS = {r["id"]: r for r in json.loads(S373.KEY.read_text(encoding="utf-8"))["records"]}
TEN = frozenset(q for q in _KEY_RECORDS if S373.refutation(q, _KEY_RECORDS))   # Q51, D5: OOD_041 to OOD_050
T141 = RECOMPUTE / "S141_phase5_tidy_corrected.csv"
T320 = RECOMPUTE / "S320_replication_two_tidy.csv"
S320J = RECOMPUTE / "S320_strategy_replication.json"
S67J = RECOMPUTE / "S67_corpus_two_axis_model.json"
S383C = RECOMPUTE / "S383_depth_concept_recall_v22.csv"
S19S = RECOMPUTE / "S19_minicheck_source_k3.jsonl"
S382C = RECOMPUTE / "S382_exp04_objective_v22.csv"
S04B = RECOMPUTE / "S04b_counts_audit.json"
DETERM = RESULTS / "analysis_deterministic_latest.json"
QWEN821 = RECOMPUTE / "S373_qwen_paper_qa.jsonl"       # calibration stand-in: qwen3-coder on v2.1, 8 October
OUT_JSON = RECOMPUTE / "S393_early_claims.json"
OUT_MD = RECOMPUTE / "S393_early_claims.md"
CAL_JSON = RECOMPUTE / "S393_early_claims_calibration.json"
CAL_MD = RECOMPUTE / "S393_early_claims_calibration.md"
NED = "not enough data"

STUDIO = {"ssh": ["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", "bioinfo-001@10.15.212.253"],
          "scp": ["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes"],
          "host": "bioinfo-001@10.15.212.253", "repo": "/Users/bioinfo-001/projects/Mentori-reanalysis"}
OK = ("ok", "ok_output_limit")
STRATS = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
PAIR = ["single_pass", "rlm_10"]
TEN_CLAIMS = {"E6": ("exp04", tuple(STRATS)),                                     # the refusal claims whose published
              "P4": ("exp06", ("raw_gemini", "naive_rag", "full_orchestrator"))}  # units hold the ten: table, configurations
TEN_CFG = {exp: set(cfgs) for exp, cfgs in TEN_CLAIMS.values()}                  # the configurations the group reports
REF = "gemini-3-flash-preview"
DEPTHS = (7, 10, 15, 20, 30, 50)          # S78.DEPTHS_USED: the depth caps that do not bind
FIG4 = ["raw_gemini", "naive_rag", "rlm_10", "full_orchestrator"]
LABELS = {"Generation strategies (exp04)": "exp04", "Corpus scaling (exp05)": "exp05", "Orchestration (exp06)": "exp06",
          "Naive RAG baseline": "naive", "Retrieval depth (exp09)": "exp09",
          "Strategy replication (published)": "rep", "S141 campaign (strategy replication, multi-generator)": "rep"}
TWO_FILES = {"reviewer_strategy_replication.json": "qwen3-coder:30b",
             "reviewer_strategy_replication_122b.json": "qwen3.5:122b"}
SCORE_FIELDS = ("cor", "fai", "ref", "p3", "main", "second")
SEVERITY = {"holds": 0, "weakens": 1, "reverses": 2}
R_BOOT = 10000


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def recorded_key_sha(path: Path) -> set[str]:
    """The current-key sha256 values a scored CSV records in its '#' lines above the header: key_sha256 of a
    '# {json}' line (S382), and the first sha256 of a '# key ...' line other than '# key v1 (gate)' (S383)."""
    out = set()
    with path.open() as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            body = line[1:].strip()
            if body.startswith("{"):
                v = json.loads(body).get("key_sha256")
                if v:
                    out.add(v)
            elif body.startswith("key ") and not body.startswith("key v1 (gate)"):
                m = re.search(r" sha256 ([0-9a-f]{64})", body)
                if m:
                    out.add(m.group(1))
    return out


def stale_key(path: Path) -> str | None:
    """None when path records exactly one key sha256 and it is the sha256 of S373.AS_V1; else why a claim
    cannot use its current-key column."""
    return None if recorded_key_sha(path) == {sha256(AS_V1)} else f"{path.name} was scored on another key"


def worst(*vs: str) -> str:
    return max(vs, key=lambda v: SEVERITY[v])


def magnitude(x: float, pub: float) -> str:
    """A claimed positive effect x against its published size: below zero reverses, under half weakens."""
    if x < 0:
        return "reverses"
    return "holds" if x > 0 and x >= pub / 2 else "weakens"


def pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def pfmt(p) -> str:
    if p is None:
        return "n/a"
    return "< 0.001" if p < 0.001 else (f"{p:.3f}" if p < 0.01 else f"{p:.2f}")


# ── the new judge's ledgers ───────────────────────────────────────────────────────────────────────

def production(name: str, judge: str) -> str | None:
    m = re.fullmatch(rf"S373_{judge}_(.+)\.jsonl", name)
    if not m:
        return None
    rest = m.group(1)
    for src in S373.SOURCES:
        if rest == src or re.fullmatch(re.escape(src) + r"_shard\d+of\d+", rest):
            return src
    return None


def read_ledger(path: Path, machine: str, origin: str) -> dict:
    data = path.read_bytes()
    text = data.decode("utf-8")
    lines = text.split("\n")
    partial = 0
    if lines and lines[-1] != "":
        partial = 1                       # a row being written: no newline yet
    rows = []
    for line in lines[:-1]:
        if line.strip():
            rows.append(json.loads(line))
    return {"file": origin, "machine": machine, "sha256": hashlib.sha256(data).hexdigest(), "rows_read": len(rows),
            "partial_last_line_skipped": partial, "rows": rows}


def ledgers(judge: str, remote: bool, tmp: Path) -> tuple[list[dict], list[str]]:
    out, notes = [], []
    for p in sorted(RECOMPUTE.glob(f"S373_{judge}_*.jsonl")):
        if production(p.name, judge):
            out.append(read_ledger(p, "laptop", str(p.relative_to(ROOT))))
    if not remote:
        notes.append("Mac Studio not read (--no-remote)")
        return out, notes
    rdir = f"{STUDIO['repo']}/findings/recompute"
    try:
        r = subprocess.run(STUDIO["ssh"] + [f"cd {rdir} && ls S373_{judge}_*.jsonl 2>/dev/null; true"],
                           capture_output=True, text=True, timeout=90, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        notes.append("Mac Studio unreachable (ssh timed out); its ledgers are not counted")
        return out, notes
    if r.returncode != 0:
        notes.append(f"Mac Studio unreachable (ssh exit {r.returncode}); its ledgers are not counted")
        return out, notes
    for name in r.stdout.split():
        if not production(name, judge):
            continue
        dst = tmp / f"studio_{name}"
        c = subprocess.run(STUDIO["scp"] + [f"{STUDIO['host']}:{rdir}/{name}", str(dst)],
                           capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
        if c.returncode != 0:
            notes.append(f"Mac Studio {name}: scp failed ({c.stderr.strip()[:120]}); not counted")
            continue
        out.append(read_ledger(dst, "studio", f"studio:findings/recompute/{name}"))
    return out, notes


def merge(files: list[dict], hashes: dict | None, d7: set) -> tuple[dict, dict, list]:
    """S390's rule: current key hash, a scored status, one row per answer key; plus D7 and conflicts. hashes None
    (the calibration stand-in only) skips the key-hash check."""
    best: dict = {}
    seen_unscored: set = set()
    st = Counter()
    conflicts = []
    for f in files:
        for r in f["rows"]:
            q = r.get("question_id")
            if q in d7:
                st["on a D7 question"] += 1
                continue
            if hashes is not None and r.get("key_hash") != hashes.get(q):
                st["stale key hash"] += 1
                continue
            if r.get("status") not in OK or not isinstance(r.get("scores"), dict):
                seen_unscored.add(r["key"])
                continue
            prev = best.get(r["key"])
            if prev is None:
                best[r["key"]] = r
            elif prev["scores"] == r["scores"]:
                st["duplicate, same scores"] += 1
                if r.get("at", "") < prev.get("at", ""):
                    best[r["key"]] = r
            else:
                conflicts.append({"key": r["key"], "a": prev["scores"], "b": r["scores"]})
                if r.get("at", "") < prev.get("at", ""):
                    best[r["key"]] = r
    st["judged without a score (no scored row)"] = len(seen_unscored - set(best))
    st["scored answers"] = len(best)
    return best, dict(st), conflicts


class Resolver:
    """Ledger key -> the answer it scores, through S374's reader (the reader S373 itself uses)."""

    def __init__(self):
        from files import FILES
        self.paths = {}
        for label, p in FILES:
            if label in LABELS:
                tag = Path(p).name if "S141" not in p else Path(p).parent.name
                self.paths[(label, tag)] = p
        self.cache: dict = {}
        self.arm2gen = {}
        with T141.open() as fh:
            for r in csv.DictReader(fh):
                self.arm2gen[r["arm"]] = r["generator"]

    def rows(self, p):
        if p not in self.cache:
            from rows import load_rows
            self.cache[p] = load_rows(p)[1]
        return self.cache[p]

    def exp04_source(self, parts: list[str], r: dict):
        """S373's --source exp04 keys exp04|config|question|i: row i of S21.judged_rows of the exp04 file."""
        if "exp04src" not in self.cache:
            src = S373.PUB / "results/exp04_generation_latest.json"
            self.cache["exp04src"] = list(S373.S21.judged_rows(json.loads(src.read_text())))   # S373: enumerate()
        rows = self.cache["exp04src"]
        _, cfg, q, i = parts
        i = int(i)
        if i >= len(rows):
            return None, "answer changed since judged"
        row = rows[i]
        if (row.get("question_id") != q or q != r["question_id"] or row.get("config") != cfg
                or len(S373.S21.answer_text(row) or "") != r["answer_chars"]):
            return None, "answer changed since judged"
        return "exp04", (cfg, q)

    def unit(self, key: str, r: dict):
        """(experiment, unit key) or (None, reason)."""
        from rows import answer, qid as row_qid
        parts = key.split("|")
        if parts[0] == "exp04" and len(parts) == 4:
            return self.exp04_source(parts, r)
        if len(parts) != 3:
            return None, f"key format not recognised ({len(parts)} fields)"
        label, tag, i = parts
        exp = LABELS.get(label)
        if exp is None:
            return None, f"source not used here: {label}"
        p = self.paths.get((label, tag))
        if p is None:
            return None, f"no result file for {label} {tag}"
        rows = self.rows(p)
        i = int(i)
        if i >= len(rows):
            return None, "answer changed since judged"
        row = rows[i]
        if row_qid(row) != r["question_id"] or len(answer(row) or "") != r["answer_chars"]:
            return None, "answer changed since judged"
        q = r["question_id"]
        if exp in ("exp04", "exp06"):
            return exp, (row.get("config") or (row.get("generation") or {}).get("config"), q)
        if exp == "exp05":
            m = re.fullmatch(r"exp_v4_s(\d+)_n(\d+)", row["index_name"])
            return exp, (m.group(1), m.group(2), row["config"], q)
        if exp == "naive":
            return exp, q
        if exp == "exp09":
            model = tag[len("exp09_depth_sweep_"):-len("_merged.json")]
            if model != REF:
                return None, "depth sweep, not gemini-3-flash"
            return exp, (int(row["depth"]), q)
        if tag in TWO_FILES:
            return exp, (TWO_FILES[tag], 1, row["config"], q)
        m = re.fullmatch(r"(.+)__draw(\d)", tag)
        if not m:
            return None, "replication side arm (thinking off)"
        return exp, (self.arm2gen[m.group(1)], int(m.group(2)), row["config"], q)


def new_tables(best_main: dict, best_second: dict, res: "Resolver | None" = None,
               ten_label: str = "their own group") -> tuple[dict, Counter, dict]:
    """The claims' tables on the new scores, the rows not mapped, and the ten's group. Every row on TEN is in no
    claim's table and is counted in drop: under ten_label when it is an exp04 or exp06 row in a configuration the group
    reports (TEN_CFG), and then kept in G; as "used by no claim" otherwise. The calibration's stand-ins pass a
    ten_label that says their group is not reported."""
    res = res or Resolver()
    T = {k: {} for k in ("exp04", "exp05", "exp06", "naive", "exp09", "rep")}
    G = {"exp04": {}, "exp06": {}}
    drop = Counter()
    for judge, best in (("main", best_main), ("second", best_second)):
        via: dict = {}
        for key, r in best.items():
            exp, u = res.unit(key, r)
            if exp is None:
                drop[f"{judge}: {u}"] += 1
                continue
            if judge == "second" and exp != "rep":
                continue
            if (exp, u) in via:                    # the same answer under a second key (exp04 and paper_qa sources)
                drop[f"{judge}: same answer under a second key, first kept"
                     f"{'' if via[(exp, u)] == r['scores'] else ' (scores differ)'}"] += 1
                continue
            via[(exp, u)] = r["scores"]
            sc, ans, ch = r["scores"], bool(r["answerable"]), r["answer_chars"]
            c = sc.get("correctness")
            if r["question_id"] in TEN:            # Q51, D5: in no claim's table; the group reports TEN_CFG's rows
                grouped = exp in TEN_CFG and u[0] in TEN_CFG[exp]
                drop[f"{judge}: on one of the ten (Q51), " + (ten_label if grouped else "used by no claim")] += 1
                if grouped:
                    G[exp][u] = {"ans": ans, "chars": ch, "cor": c if ans else None,
                                 "fai": sc.get("faithfulness") if ans else None,
                                 "ref": sc.get("refusal_accuracy") if not ans else None}
                continue
            if exp in ("exp04", "exp06"):
                T[exp][u] = {"ans": ans, "chars": ch, "cor": c if ans else None, "fai": sc.get("faithfulness") if ans else None,
                             "ref": sc.get("refusal_accuracy") if not ans else None}
            elif not ans or c is None:
                continue
            elif exp == "exp05":
                if u[2] != "verified_pass":
                    T[exp][u] = {"ans": True, "cor": c}
            elif exp == "naive":
                T[exp][u] = {"ans": True, "chars": ch, "cor": c}
            elif exp == "exp09":
                if u[0] in DEPTHS:
                    T[exp][u] = {"ans": True, "chars": ch, "p3": int(c >= 3)}
            else:
                row = T["rep"].setdefault(u, {"ans": True, "chars": ch, "main": None, "second": None})
                row[judge] = int(c >= 3)
    return T, drop, G


# ── the original scores ───────────────────────────────────────────────────────────────────────────

def original_tables() -> dict:
    import S21b_analyze as S21b
    import S281_corrected_figure_tables as S281
    import S66_corpus_grid as S66
    import S78_rlm_draw_spread as S78
    dep, _ = S281.corrected_rows()
    T = {k: {} for k in ("exp04", "exp05", "exp06", "naive", "exp09", "rep")}
    for (fname, _i), r in dep.items():
        pub, cor = r["published"] or {}, r["corrected"] or {}
        if not pub:
            continue
        ans = "refusal_accuracy" not in pub          # S281's own split of the two halves
        if fname in (S281.EXP04, S281.EXP06):
            exp = "exp04" if fname == S281.EXP04 else "exp06"
            k = (r["config"], r["question_id"])
            assert k not in T[exp], f"duplicate {exp} key {k}"
            T[exp][k] = {"ans": ans, "chars": r.get("chars"), "cor": cor.get("correctness") if ans else None,
                         "fai": cor.get("faithfulness") if ans else None,
                         "ref": (cor.get("refusal_accuracy") or 0) if not ans else None}   # S281: (x or 0) >= 3
        elif fname == "analysis_naive_baseline_latest.json" and ans:
            T["naive"][r["question_id"]] = {"ans": True, "chars": r.get("chars"), "cor": pub.get("correctness") or 0}  # S78
    src = {}
    for line in open(S19S):                         # MiniCheck against the source papers: no judge, no key
        d = json.loads(line)
        src[(d["config"], d["question_id"])] = float(d["precision"])
    for k, v in T["exp04"].items():
        if v["ans"]:
            v["msrc"] = src.get(k)
    rows5, _ = S66.load()
    for r in rows5:
        if r["answerable"] == "1" and S66.scoreable(r) and r["strategy"] != "verified_pass":
            T["exp05"][(r["size"], r["noise"], r["strategy"], r["question_id"])] = {"ans": True,
                                                                                     "cor": int(r["correctness_rejudged"])}
    answerable = {q for (c, q), v in T["exp04"].items() if v["ans"] and c == "single_pass"}
    d9 = S78.exp09_draws(S78.load_rejudge(), answerable, verbose=False)
    lat = json.load(open(RESULTS / S78.EXP09))
    chars9 = {(r.get("depth"), r.get("question_id")): len(S21b.answer_text(r) or "") for r in S21b.judged_rows(lat)}
    for depth in DEPTHS:
        for q, p in d9[depth]["scores"].items():
            T["exp09"][(depth, q)] = {"ans": True, "chars": chars9.get((depth, q)), "p3": int(p)}
    order = 0
    with T141.open() as fh:
        for r in csv.DictReader(fh):
            if r["answerable"] != "1":
                continue
            sc = r["scored"] == "1"
            T["rep"][(r["generator"], int(r["draw"]), r["strategy"], r["question_id"])] = {
                "ans": True, "order": order, "chars": int(r["answer_chars"]) if r["answer_chars"] else None,
                "main": int(r["passed_incumbent_corrected"]) if sc else None,
                "second": int(r["passed_robustness"]) if sc else None}
            order += 1
    with T320.open() as fh:
        for r in csv.DictReader(l for l in fh if not l.startswith("#")):
            T["rep"][(r["generator"], int(r["draw"]), r["strategy"], r["question_id"])] = {
                "ans": True, "order": order, "chars": int(r["answer_chars"]) if r["answer_chars"] else None,
                "main": int(r["passed_incumbent_corrected"]) if r["scored"] == "1" else None,
                "second": int(r["passed_robustness"]) if r["scored_robustness"] == "1" else None}
            order += 1
    return T


def drop_d7(T: dict, d7: set) -> dict:
    def q(k):
        return k if isinstance(k, str) else k[-1]
    return {e: {k: v for k, v in t.items() if q(k) not in d7} for e, t in T.items()}


def drop_q51(T: dict) -> dict:
    """Column (b'): the rows on TEN that are refusal units (not answerable) removed, as drop_d7 removes D7's
    questions. On the original scores these are all the ten's rows (exp04 and exp06 only)."""
    def q(k):
        return k if isinstance(k, str) else k[-1]
    return {e: {k: v for k, v in t.items() if not (q(k) in TEN and not v["ans"])} for e, t in T.items()}


def ten_group(orig: dict, G: dict, exp: str, cfgs: tuple) -> dict:
    """The ten beside a refusal claim, per configuration: the original share refused (refusal accuracy 3 or more,
    as S281 counts it) on all their rows, and the new share passed (correctness 3 or more, against the refutation)
    on the rows the new judge has scored whose answer length matches the original's (match's rule)."""
    out = {"questions": sorted(TEN), "by_config": {}, "new_dropped_for_length": 0, "new_without_correctness": 0}
    for cfg in cfgs:
        o = {k: v for k, v in orig[exp].items() if k[0] == cfg and k[1] in TEN}
        ref = [(v["ref"] or 0) >= 3 for v in o.values() if not v["ans"] and v.get("ref") is not None]
        cor, fai5 = [], []
        for k, a in o.items():
            b = G[exp].get(k)
            if b is None:
                continue
            if a.get("chars") is not None and b.get("chars") is not None and a["chars"] != b["chars"]:
                out["new_dropped_for_length"] += 1
                continue
            if not b["ans"] or b.get("cor") is None:
                out["new_without_correctness"] += 1         # no correctness score (a decline-prompt row on the ten
                                                            # fails merge's key-hash check, so none arrives here)
                continue
            cor.append(b["cor"] >= 3)
            if b.get("fai") is not None:
                fai5.append(b["fai"] == 5)
        out["by_config"][cfg] = {"original_n": len(ref), "original_refused": sum(ref),
                                 "new_n": len(cor), "new_passed": sum(cor), "new_faith_5": sum(fai5),
                                 "new_faith_n": len(fai5)}
    bc = out["by_config"].values()
    out["units_original"] = sum(x["original_n"] for x in bc)
    out["units_new"] = sum(x["new_n"] for x in bc)
    out["coverage"] = out["units_new"] / out["units_original"] if out["units_original"] else 0.0
    return out


def match(A: dict, B: dict) -> tuple[dict, dict, Counter]:
    """Per table: the keys both hold, whose answers are the same length; a score field stays only where both
    hold it. Structural fields (answerable, row order) come from the original."""
    MA, MB, bad = {}, {}, Counter()
    for e in A:
        ma, mb = {}, {}
        for k, a in A[e].items():
            b = B[e].get(k)
            if b is None:
                continue
            if a.get("chars") is not None and b.get("chars") is not None and a["chars"] != b["chars"]:
                bad[e] += 1
                continue
            ra, rb = dict(a), dict(a)
            for f in SCORE_FIELDS:
                if f in a or f in b:
                    va, vb = a.get(f), b.get(f)
                    if va is None or vb is None:
                        ra[f] = rb[f] = None
                    else:
                        rb[f] = vb
            ma[k], mb[k] = ra, rb
        MA[e], MB[e] = ma, mb
    return MA, MB, bad


# ── R: the two bootstraps, copied from the scripts that print them ────────────────────────────────

R_S320 = r'''
# Copied from scripts/S320_strategy_replication.R (cell_lab to analyse). The data step is replaced by a CSV in
# S320's row order (five-model rows, then two-model rows) carrying one judge's pass and scored flags. Added only
# for sparse subsets: an empty bootstrap gives NA intervals and the verdict "not computable".
suppressPackageStartupMessages({ library(jsonlite) })
a <- commandArgs(trailingOnly = TRUE)
d <- read.csv(a[1], stringsAsFactors = FALSE)
R_BOOT <- as.integer(a[3])
SEED <- 20260722; MARGIN_PP <- 10; REF <- "gemini-3-flash-preview"; PAIR <- c("single_pass", "rlm_10")
d <- subset(d, strategy %in% PAIR)
GENS <- sort(unique(d$generator))
cell_lab <- as.vector(outer(GENS, PAIR, function(a, b) paste(a, b, sep = "|")))
cell <- as.integer(factor(paste(d$generator, d$strategy, sep = "|"), levels = cell_lab))
NB <- length(cell_lab)
ii <- function(g, s) match(paste(g, s, sep = "|"), cell_lab)
qids <- unique(d$question_id); idx_by_q <- split(seq_len(nrow(d)), d$question_id)
make <- function(col, scol) {
  p <- ifelse(is.na(d[[col]]), 0L, as.integer(d[[col]]))
  sc <- as.integer(d[[scol]])
  list(pass1 = p == 1L & sc == 1L, scored1 = sc == 1L)
}
rates <- function(v, idx) {
  num <- tabulate(cell[idx][v$pass1[idx]], NB)
  den <- tabulate(cell[idx][v$scored1[idx]], NB)
  ifelse(den > 0, 100 * num / den, NA_real_)
}
delta_of <- function(r) setNames(vapply(GENS, function(g)
  unname(r[ii(g, PAIR[2])] - r[ii(g, PAIR[1])]), numeric(1)), GENS)
did_from <- function(r) { x <- delta_of(r); x - x[[REF]] }
boot_did <- function(v, R) {
  set.seed(SEED)
  keep <- matrix(NA_real_, nrow = R, ncol = length(GENS), dimnames = list(NULL, GENS))
  for (b in seq_len(R)) {
    idx <- unlist(idx_by_q[sample(qids, length(qids), replace = TRUE)], use.names = FALSE)
    r <- rates(v, idx); if (anyNA(r)) next
    keep[b, ] <- did_from(r)
  }
  keep[stats::complete.cases(keep), , drop = FALSE]
}
verdict <- function(g, ci) {
  if (g == REF) return("reference")
  if (anyNA(ci)) return("not computable")
  if (ci[1] > -MARGIN_PP && ci[2] < MARGIN_PP) return("EQUIVALENT")
  if (ci[1] > MARGIN_PP || ci[2] < -MARGIN_PP) return("DIFFERENT")
  "INCONCLUSIVE"
}
analyse <- function(col, scol) {
  v <- make(col, scol)
  rr <- rates(v, seq_len(nrow(d)))
  delta <- delta_of(rr); obs <- did_from(rr)
  K <- boot_did(v, R_BOOT)
  out <- lapply(GENS, function(g) {
    ci <- if (nrow(K) > 0) unname(quantile(K[, g], c(0.025, 0.975))) else c(NA_real_, NA_real_)
    list(single_pass_pct = round(rr[ii(g, PAIR[1])], 2), rlm_10_pct = round(rr[ii(g, PAIR[2])], 2),
         delta_pp = round(unname(delta[[g]]), 2), did_pp = round(unname(obs[[g]]), 2),
         ci_pp = round(ci, 2), verdict = verdict(g, ci)) })
  names(out) <- GENS
  c(list(n_reps = nrow(K)), out)
}
write(toJSON(analyse("pass", "scored"), auto_unbox = TRUE, digits = NA, na = "null"), a[2])
'''

R_S67 = r'''
# Copied from scripts/S67_corpus_two_axis_model.R: the data step (tidy and re-judged files, the chunk merge that
# fixes the row order, the valid rows, mk() at its defaults) and cluster_boot(), verbatim. The pass column is then
# replaced, row by row, from a CSV keyed question_id|strategy|index_name; rows the CSV does not hold are dropped.
# Added only for sparse subsets: fewer than 20 usable resamples give NA.
suppressPackageStartupMessages({ library(jsonlite) })
a <- commandArgs(trailingOnly = TRUE)
source(a[1])
RECOMPUTE <- mentori_recompute(); PAPER_RES <- mentori_results()
TIDY <- file.path(RECOMPUTE, "S11_exp05_tidy.csv"); REJUDG <- file.path(RECOMPUTE, "S11_exp05_tidy_rejudged.csv")
SEED <- 20260722; PAIR <- c("single_pass", "rlm_10")
df <- read.csv(TIDY, comment.char = "#", stringsAsFactors = FALSE)
rj <- read.csv(REJUDG, comment.char = "#", stringsAsFactors = FALSE)
k1 <- paste(df$question_id, df$strategy, df$index_name, sep = "|")
k2 <- paste(rj$question_id, rj$strategy, rj$index_name, sep = "|")
m <- match(k1, k2)
df$correctness_rj <- ifelse(is.na(m), df$correctness, rj$correctness[m])
chunks <- do.call(rbind, lapply(list.files(PAPER_RES, "^create_indexes_.*json$", full.names = TRUE), function(f) {
  r <- fromJSON(f)$results
  data.frame(index_name = r$index, chunks = r$total_chunks, stringsAsFactors = FALSE)
}))
chunks <- chunks[!duplicated(chunks$index_name), ]
df <- merge(df, chunks, by = "index_name", all.x = TRUE)
valid <- df$answerable == 1 & df$empty == 0 & df$unjudged == 0
d <- df
d$pass <- ifelse(valid, as.integer(d$correctness_rj >= 3), NA_integer_)
d <- subset(d, !is.na(pass) & strategy %in% PAIR)
alt <- read.csv(a[2], stringsAsFactors = FALSE)
i <- match(paste(d$question_id, d$strategy, d$index_name, sep = "|"), alt$key)
d <- d[!is.na(i), ]
d$pass <- alt$pass[i[!is.na(i)]]
d$strategy <- factor(d$strategy, levels = PAIR)
d$log_core_c  <- log(d$size) - mean(log(d$size))
d$log_noise_c <- log(1 + d$noise) - mean(log(1 + d$noise))
cluster_boot <- function(d, form, R, batches = 10) {
  set.seed(SEED)
  qids <- unique(d$question_id)
  idx_by_q <- split(seq_len(nrow(d)), d$question_id)
  X <- model.matrix(as.formula(form), data = d)
  y <- d$pass
  keep <- matrix(NA_real_, nrow = R, ncol = ncol(X), dimnames = list(NULL, colnames(X)))
  for (b in seq_len(R)) {
    samp <- sample(qids, length(qids), replace = TRUE)
    idx <- unlist(idx_by_q[samp], use.names = FALSE)
    fitb <- tryCatch(suppressWarnings(glm.fit(X[idx, , drop = FALSE], y[idx],
                                              family = binomial())), error = function(e) NULL)
    if (!is.null(fitb) && all(is.finite(fitb$coefficients))) keep[b, ] <- fitb$coefficients
  }
  keep <- keep[stats::complete.cases(keep), , drop = FALSE]
  ints <- grep(":", colnames(keep), value = TRUE)
  if (nrow(keep) < 20) {
    out <- lapply(ints, function(cn) list(est = NA, ci = c(NA, NA)))
    names(out) <- ints
    return(c(list(n_reps = nrow(keep)), out))
  }
  out <- lapply(ints, function(cn) {
    v <- keep[, cn]
    bnd <- function(p) unname(quantile(v, p))
    grp <- cut(seq_along(v), breaks = batches, labels = FALSE)
    mcse <- function(p) round(sd(tapply(v, grp, quantile, probs = p)) / sqrt(batches), 3)
    list(est = round(median(v), 3), ci = round(c(bnd(0.025), bnd(0.975)), 3),
         mcse_lo = mcse(0.025), mcse_hi = mcse(0.975))
  })
  names(out) <- ints
  c(list(n_reps = nrow(keep)), out)
}
res <- cluster_boot(d, "pass ~ strategy * (log_core_c + log_noise_c)", as.integer(a[4]))
res$n <- nrow(d); res$n_questions <- length(unique(d$question_id))
write(toJSON(res, auto_unbox = TRUE, digits = NA, na = "null"), a[3])
'''

_R_CACHE: dict = {}


def rscript(code: str, rows: list[list], header: list[str], extra: list[str]) -> dict:
    """Run one of the R blocks on a CSV of rows; cached on the exact input."""
    body = "\n".join(",".join(str(x) for x in r) for r in rows)
    key = hashlib.sha256((code + "|".join(extra) + body).encode()).hexdigest()
    if key in _R_CACHE:
        return json.loads(_R_CACHE[key])
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "s393.R").write_text(code)
        (td / "in.csv").write_text(",".join(header) + "\n" + body + "\n")
        out = td / "out.json"
        args = [a.format(csv=td / "in.csv", out=out) for a in extra]
        r = subprocess.run(["Rscript", str(td / "s393.R"), *args], capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            raise SystemExit(f"FATAL: Rscript failed:\n{r.stderr[-2000:]}")
        res = json.loads(out.read_text())
    _R_CACHE[key] = json.dumps(res)
    return res


# ── the claims ────────────────────────────────────────────────────────────────────────────────────

def _pmap(T, exp, cfg, thr=3, field="cor", ans=True):
    return {q: (v[field] or 0) >= thr for (c, q), v in T[exp].items()
            if c == cfg and v["ans"] == ans and v.get(field) is not None}


def _nq(*maps) -> int:
    """Distinct questions behind one or more {question: ...} maps."""
    return len(set().union(*[set(m) for m in maps]))


def e1(T):
    k = {s: _pmap(T, "exp04", s) for s in STRATS}
    n = {s: len(v) for s, v in k.items()}
    out = {"units": sum(n.values()), "ok": min(n.values()) >= 10, "n_questions": _nq(*k.values()),
           **{f"{s}_n": n[s] for s in STRATS}}
    if min(n.values()) == 0:
        return out
    r = {s: sum(v.values()) / n[s] for s, v in k.items()}
    out.update({f"{s}_rate": r[s] for s in STRATS})
    others = [s for s in STRATS if s != "rlm_10"]
    out["rlm_10_rank"] = 1 + sum(r[o] > r["rlm_10"] for o in others)
    out["rlm_10_tied"] = any(r[o] == r["rlm_10"] for o in others)
    others = [s for s in STRATS if s != "verified_pass"]
    out["verified_rank_from_bottom"] = 1 + sum(r[o] < r["verified_pass"] for o in others)
    out["verified_tied"] = any(r[o] == r["verified_pass"] for o in others)
    return out


def v_e1(res, pub):
    def part(rank, tied):
        return "holds" if rank == 1 and not tied else ("weakens" if rank <= 3 else "reverses")
    return worst(part(res["rlm_10_rank"], res["rlm_10_tied"]),
                 part(res["verified_rank_from_bottom"], res["verified_tied"]))


def h_e1(res):
    if "rlm_10_rate" not in res:
        return f"{res['units']} answers"
    return (f"RLM-10 {pct(res['rlm_10_rate'])} (rank {res['rlm_10_rank']}{', tied' if res['rlm_10_tied'] else ''}), "
            f"verification {pct(res['verified_pass_rate'])} (rank {res['verified_rank_from_bottom']} from bottom"
            f"{', tied' if res['verified_tied'] else ''}); n {min(res[f'{s}_n'] for s in STRATS)} to "
            f"{max(res[f'{s}_n'] for s in STRATS)} per strategy")


def paired04(a, b, thr=3, min_pairs=10):
    def run(T):
        pa, pb = _pmap(T, "exp04", a, thr), _pmap(T, "exp04", b, thr)
        q = sorted(pa.keys() & pb.keys())
        out = {"units": len(q), "ok": len(q) >= min_pairs, "n_questions": len(q)}
        if not q:
            return out
        m = sf.mcnemar_from_vectors([pa[k] for k in q], [pb[k] for k in q], (a, b))
        out.update({"n_pairs": len(q), "rate_a": m[f"rate_{a}"], "rate_b": m[f"rate_{b}"], "diff": m["diff"],
                    "a_only": m[f"{a}_only"], "b_only": m[f"{b}_only"], "discordant": m["discordant"], "P": m["P"],
                    "cohens_h": m["cohens_h"], "baseline_correct": sum(pa[k] for k in q)})
        if m["discordant"]:
            out["harmful"] = m[f"{a}_only"] / m["discordant"]
        else:
            out["ok"] = False
        if out["baseline_correct"]:
            out["degraded"] = m[f"{a}_only"] / out["baseline_correct"]
        return out
    return run


def v_flip(res, pub):
    if res["harmful"] > 0.5:
        return "holds" if res["P"] < 0.05 else "weakens"
    return "reverses"


def h_flip(res):
    if "harmful" not in res:
        return f"{res['units']} question pairs, {res.get('discordant', 0)} discordant"
    return (f"{res['a_only']} of {res['discordant']} changed outcomes harmful ({pct(res['harmful'])}), P {pfmt(res['P'])}; "
            f"{res['a_only']} of {res['baseline_correct']} correct answers degraded ({pct(res.get('degraded'))}); "
            f"{res['n_pairs']} pairs")


def v_better(res, pub):
    if res["diff"] < 0:
        return "reverses"
    return "holds" if res["diff"] > 0 and res["P"] < 0.05 else "weakens"


def h_better(res):
    if "diff" not in res:
        return f"{res['units']} question pairs"
    return (f"{pct(res['rate_a'])} against {pct(res['rate_b'])}, difference {100 * res['diff']:+.1f} pp, "
            f"P {pfmt(res['P'])}, h {res['cohens_h']:.2f}; {res['n_pairs']} pairs")


def e6(T):
    k = {s: _pmap(T, "exp04", s, field="ref", ans=False) for s in STRATS}
    n = {s: len(v) for s, v in k.items()}
    out = {"units": sum(n.values()), "ok": n["rlm_10"] >= 10 and n["multi_hop"] >= 10, "n_questions": _nq(*k.values()),
           **{f"{s}_n": n[s] for s in STRATS}}
    out.update({f"{s}_rate": sum(v.values()) / n[s] for s, v in k.items() if n[s]})
    if n["rlm_10"] and n["multi_hop"]:
        out["gap"] = out["rlm_10_rate"] - out["multi_hop_rate"]
    else:
        out["ok"] = False
    return out


def h_e6(res):
    if "gap" not in res:
        return f"{res['units']} out-of-domain answers"
    return (f"RLM-10 refuses {pct(res['rlm_10_rate'])} (n {res['rlm_10_n']}), multi-hop {pct(res['multi_hop_rate'])} "
            f"(n {res['multi_hop_n']}); verification {pct(res.get('verified_pass_rate'))}, RLM-20 {pct(res.get('rlm_20_rate'))}")


def e7(T):
    kv = [(k, v) for k, v in T["exp04"].items() if v["ans"] and v.get("cor") is not None and v.get("fai") is not None]
    rows = [v for _, v in kv]
    zero = [v for v in rows if v["cor"] == 0]
    out = {"units": len(rows), "n_correctness_0": len(zero), "ok": len(zero) >= 10,
           "n_questions": len({k[1] for k, _ in kv}), "of_which_faith_5": sum(v["fai"] == 5 for v in zero)}
    if rows:
        out["share5_all"] = sum(v["fai"] == 5 for v in rows) / len(rows)
        out["n_faith_5"] = sum(v["fai"] == 5 for v in rows)
    if zero:
        out["share"] = out["of_which_faith_5"] / len(zero)
    else:
        out["ok"] = False
    return out


def v_e7(res, pub):
    if res["share"] > 0.5:
        return "holds"
    return "weakens" if res["share"] >= pub["share"] / 2 else "reverses"


def h_e7(res):
    s = f"{res['of_which_faith_5']} of {res['n_correctness_0']} 'completely incorrect' rated 5/5 faithful"
    if "share" in res:
        s += f" ({pct(res['share'])})"
    if "share5_all" in res:
        s += f"; 5/5 on {pct(res['share5_all'])} of {res['units']} answers"
    return s


def _faith(T):
    return [v for v in T["exp04"].values() if v["ans"] and v.get("fai") is not None]


def _faith_q(T) -> int:
    return len({k[1] for k, v in T["exp04"].items() if v["ans"] and v.get("fai") is not None})


def e8(T):
    rows = _faith(T)
    out = {"units": len(rows), "ok": len(rows) >= 10, "n_questions": _faith_q(T),
           "n_faith_5": sum(v["fai"] == 5 for v in rows)}
    if rows:
        out["share"] = out["n_faith_5"] / len(rows)
        out["by_score"] = dict(sorted(Counter(int(v["fai"]) for v in rows).items()))
    else:
        out["ok"] = False
    return out


def v_e8(res, pub):
    return "holds" if res["share"] >= 0.75 else ("weakens" if res["share"] >= 0.5 else "reverses")


def h_e8(res):
    if "share" not in res:
        return f"{res['units']} answers"
    return f"5/5 faithfulness on {res['n_faith_5']} of {res['units']} answers ({pct(res['share'])}); scores {res['by_score']}"


def e9(T):
    rows = _faith(T)
    at5 = [v["msrc"] for v in rows if v["fai"] == 5 and v.get("msrc") is not None]
    out = {"units": len(rows), "n_at5": len(at5), "ok": len(at5) >= 10, "n_questions": _faith_q(T)}
    if at5:
        out["below_half"] = sum(x < 0.5 for x in at5)
        out["share"] = out["below_half"] / len(at5)
        srt = sorted(at5)
        out["median"] = (srt[(len(srt) - 1) // 2] + srt[len(srt) // 2]) / 2
        out["mean"] = sum(at5) / len(at5)
    else:
        out["ok"] = False
    return out


def h_e9(res):
    if "share" not in res:
        return f"{res['units']} answers, {res['n_at5']} at 5/5"
    return (f"{res['below_half']} of {res['n_at5']} answers rated 5/5 have source-grounded precision below 0.50 "
            f"({pct(res['share'])}); median {res['median']:.2f}, mean {res['mean']:.2f}")


def e10(T):
    rows = [v for v in _faith(T) if v["fai"] >= 3 and v.get("msrc") is not None]
    out = {"units": len(_faith(T)), "n_top3": len(rows), "ok": len(rows) >= 10, "n_questions": _faith_q(T)}
    if len(rows) >= 3 and len({v["fai"] for v in rows}) > 1:
        r = sf.spearman([v["fai"] for v in rows], [v["msrc"] for v in rows])
        out.update(rho=r["rho"], P=r["P"])
    else:
        out["ok"] = False
    return out


def v_e10(res, pub):
    return "reverses" if res["rho"] > 0 and res["P"] < 0.05 else "holds"


def h_e10(res):
    if "rho" not in res:
        return f"{res['n_top3']} answers at faithfulness 3 to 5"
    return f"Spearman rho {res['rho']:+.2f}, P {pfmt(res['P'])}, over {res['n_top3']} answers at faithfulness 3 to 5"


def _cell05(T, core, noise):
    a = {q: v["cor"] >= 3 for (s, n, st, q), v in T["exp05"].items()
         if s == core and n == noise and st == "single_pass" and v["cor"] is not None}
    b = {q: v["cor"] >= 3 for (s, n, st, q), v in T["exp05"].items()
         if s == core and n == noise and st == "rlm_10" and v["cor"] is not None}
    q = sorted(a.keys() & b.keys())
    if not q:
        return None
    a_only = sum(a[k] and not b[k] for k in q)
    b_only = sum(b[k] and not a[k] for k in q)
    both = sum(a[k] and b[k] for k in q)
    m = sf.mcnemar_paired(a_only, b_only, both, len(q) - a_only - b_only - both, ("single_pass", "rlm_10"))
    return {"n": len(q), "single_pass": m["rate_single_pass"], "rlm_10": m["rate_rlm_10"], "sp_minus_rlm": m["diff"],
            "P": m["P"], "P_bonferroni": min(1.0, 12 * m["P"])}


def _q05(T, cells: list[tuple[str, str]]) -> int:
    """Questions with both strategies scored in at least one of the given (core, noise) cells."""
    have = defaultdict(set)
    for (s, n, st, q), v in T["exp05"].items():
        if (s, n) in cells and st in PAIR and v["cor"] is not None:
            have[(s, n, q)].add(st)
    return len({k[2] for k, sts in have.items() if len(sts) == 2})


def s1(T):
    cells = {n: _cell05(T, "50", n) for n in ("0", "1", "3")}
    units = sum(c["n"] for c in cells.values() if c)
    out = {"units": units, "ok": all(c and c["n"] >= 10 for c in cells.values()),
           "n_questions": _q05(T, [("50", n) for n in ("0", "1", "3")]),
           "cells": {f"50 core, {n}x": c for n, c in cells.items()}}
    return out


def v_s1(res, pub):
    cs = [c for c in res["cells"].values()]
    if any(c["sp_minus_rlm"] < 0 for c in cs):
        return "reverses"
    if all(c["sp_minus_rlm"] > 0 and c["P_bonferroni"] < 0.05 for c in cs):
        return "holds"
    return "weakens"


def h_cells(res):
    parts = []
    for name, c in res["cells"].items():
        if c is None:
            parts.append(f"{name}: no pairs")
        else:
            parts.append(f"{name}: {pct(c['single_pass'])} vs {pct(c['rlm_10'])}, Bonferroni P {pfmt(c['P_bonferroni'])} "
                         f"(n {c['n']})")
    return "; ".join(parts)


def s2(T):
    cells = {f"{c} core, {n}x": _cell05(T, c, n) for c in ("5", "10", "20") for n in ("0", "1", "3")}
    got = {k: c for k, c in cells.items() if c}
    # minimum: one cell with 10 pairs (a single pair used to pass); "holds" also needs 80% coverage (null claim)
    return {"units": sum(c["n"] for c in got.values()), "ok": any(c["n"] >= 10 for c in got.values()), "cells": cells,
            "n_questions": _q05(T, [(c, n) for c in ("5", "10", "20") for n in ("0", "1", "3")]),
            "n_cells": len(got), "n_significant": sum(c["P_bonferroni"] < 0.05 for c in got.values()),
            "min_P_bonferroni": min((c["P_bonferroni"] for c in got.values()), default=None)}


def v_s2(res, pub):
    return "reverses" if res["n_significant"] else "holds"


def h_s2(res):
    return (f"{res['n_significant']} of {res['n_cells']} cells with Bonferroni P < 0.05 (smallest "
            f"{pfmt(res['min_P_bonferroni'])}); {res['units']} pairs")


def s3(T):
    rows = [(k, v) for k, v in T["exp05"].items() if k[2] in PAIR and v["cor"] is not None]
    out = {"units": len(rows), "n_questions": len({k[3] for k, _ in rows})}
    out["ok"] = out["units"] >= 200 and out["n_questions"] >= 20
    if not out["ok"]:
        return out
    body = [[f"{k[3]}|{k[2]}|exp_v4_s{k[0]}_n{k[1]}", int(v["cor"] >= 3)] for k, v in sorted(rows)]
    res = rscript(R_S67, body, ["key", "pass"], [str(HERE / "machine.R"), "{csv}", "{out}", str(R_BOOT)])
    c, n = res["strategyrlm_10:log_core_c"], res["strategyrlm_10:log_noise_c"]
    out.update(n_reps=res["n_reps"], core_est=c["est"], core_ci=c["ci"], noise_est=n["est"], noise_ci=n["ci"],
               n_rows=res["n"])
    if c["est"] is None:
        out["ok"] = False
    return out


def v_s3(res, pub):
    if res["core_est"] >= 0:
        return "reverses"
    core_sig = res["core_ci"][1] < 0
    noise_null = res["noise_ci"][0] <= 0 <= res["noise_ci"][1]
    return "holds" if core_sig and noise_null else "weakens"


def h_s3(res):
    if "core_est" not in res:
        return f"{res['units']} rows, {res['n_questions']} questions"
    return (f"strategy x log(core) {res['core_est']:+.2f} [{res['core_ci'][0]:+.2f}, {res['core_ci'][1]:+.2f}], "
            f"x log(1+noise) {res['noise_est']:+.2f} [{res['noise_ci'][0]:+.2f}, {res['noise_ci'][1]:+.2f}]; "
            f"{res['n_rows']} rows, {res['n_reps']:,} resamples")


def _rate06(T, cfg, field, ans):
    v = _pmap(T, "exp06", cfg, field=field, ans=ans)
    return (sum(v.values()) / len(v) if v else None), len(v)


def _q06(T, cfgs, field, ans) -> int:
    return _nq(*[_pmap(T, "exp06", c, field=field, ans=ans) for c in cfgs])


def p_gap(hi, lo, field="cor", ans=True):
    def run(T):
        (rh, nh), (rl, nl) = _rate06(T, hi, field, ans), _rate06(T, lo, field, ans)
        out = {"units": nh + nl, "ok": nh >= 10 and nl >= 10, "rate_hi": rh, "rate_lo": rl, "n_hi": nh, "n_lo": nl,
               "n_questions": _q06(T, (hi, lo), field, ans)}
        if rh is not None and rl is not None:
            out["gap"] = rh - rl
        else:
            out["ok"] = False
        return out
    return run


def h_gap(names):
    def run(res):
        if "gap" not in res:
            return f"{res['units']} answers"
        return (f"{names[0]} {pct(res['rate_hi'])} (n {res['n_hi']}), {names[1]} {pct(res['rate_lo'])} (n {res['n_lo']}), "
                f"gap {100 * res['gap']:+.1f} pp")
    return run


def p4(T):
    r = {c: _rate06(T, c, "ref", False) for c in ("raw_gemini", "naive_rag", "full_orchestrator")}
    out = {"units": sum(n for _, n in r.values()), "ok": all(n >= 10 for _, n in r.values()),
           "n_questions": _q06(T, tuple(r), "ref", False),
           **{f"{c}_rate": x for c, (x, _) in r.items()}, **{f"{c}_n": n for c, (_, n) in r.items()}}
    if all(x is not None for x, _ in r.values()):
        out["gap_naive_raw"] = r["naive_rag"][0] - r["raw_gemini"][0]
        out["gap_naive_full"] = r["naive_rag"][0] - r["full_orchestrator"][0]
    else:
        out["ok"] = False
    return out


def v_p4(res, pub):
    return worst(magnitude(res["gap_naive_raw"], pub["gap_naive_raw"]),
                 magnitude(res["gap_naive_full"], pub["gap_naive_full"]))


def h_p4(res):
    return (f"refusal: closed-book {pct(res.get('raw_gemini_rate'))} (n {res['raw_gemini_n']}), naive RAG "
            f"{pct(res.get('naive_rag_rate'))} (n {res['naive_rag_n']}), full orchestrator "
            f"{pct(res.get('full_orchestrator_rate'))} (n {res['full_orchestrator_n']})")


def _draws(T):
    rlm = {"exp04 RLM-10": _pmap(T, "exp04", "rlm_10"),
           "exp05 RLM-10": {q: v["cor"] >= 3 for (s, n, st, q), v in T["exp05"].items()
                            if s == "20" and n == "0" and st == "rlm_10" and v["cor"] is not None}}
    for d in DEPTHS:
        rlm[f"exp09 cap {d}"] = {q: bool(v["p3"]) for (dd, q), v in T["exp09"].items() if dd == d and v["p3"] is not None}
    passive = {"naive RAG": {q: v["cor"] >= 3 for q, v in T["naive"].items() if v["cor"] is not None},
               "exp04 single-pass": _pmap(T, "exp04", "single_pass"),
               "exp05 single-pass": {q: v["cor"] >= 3 for (s, n, st, q), v in T["exp05"].items()
                                     if s == "20" and n == "0" and st == "single_pass" and v["cor"] is not None}}
    return rlm, passive


def n1(T):
    rlm, passive = _draws(T)
    alld = {**rlm, **passive}
    out = {"units": sum(len(v) for v in alld.values()), "ok": all(len(v) >= 10 for v in alld.values()),
           "n_min": min(len(v) for v in alld.values()), "n_questions": _nq(*alld.values())}
    if any(not v for v in alld.values()):
        out["ok"] = False
        return out
    r = {k: 100 * sum(v.values()) / len(v) for k, v in rlm.items()}
    p = {k: 100 * sum(v.values()) / len(v) for k, v in passive.items()}
    out.update(rlm_pct=r, passive_pct=p, rlm_min=min(r.values()), rlm_max=max(r.values()),
               rlm_spread=max(r.values()) - min(r.values()), rlm_median=sorted(r.values())[3] / 2 + sorted(r.values())[4] / 2,
               passive_spread=max(p.values()) - min(p.values()))
    return out


def v_n1(res, pub):
    return "holds" if res["passive_spread"] < res["rlm_spread"] else "reverses"


def h_n1(res):
    if "rlm_spread" not in res:
        return f"{res['units']} draw answers, smallest draw n {res['n_min']}"
    return (f"passive runs spread {res['passive_spread']:.1f} pp, RLM runs {res['rlm_spread']:.1f} pp "
            f"({res['rlm_min']:.1f}% to {res['rlm_max']:.1f}%); smallest draw n {res['n_min']}")


def n2(T):
    rlm, passive = _draws(T)
    out = {"units": sum(len(v) for v in rlm.values()), "ok": all(len(v) >= 10 for v in rlm.values()),
           "n_min": min(len(v) for v in rlm.values()), "n_questions": _nq(*rlm.values())}
    if any(not v for v in rlm.values()):
        out["ok"] = False
        return out
    r = {k: sum(v.values()) / len(v) for k, v in rlm.items()}
    out["rank"] = 1 + sum(x > r["exp04 RLM-10"] for k, x in r.items() if k != "exp04 RLM-10")
    out["tied"] = any(x == r["exp04 RLM-10"] for k, x in r.items() if k != "exp04 RLM-10")
    out["exp04_rlm10"] = r["exp04 RLM-10"]
    base = passive["exp04 single-pass"]
    sig = 0
    for k, v in rlm.items():
        q = sorted(base.keys() & v.keys())
        if q and sf.mcnemar_from_vectors([base[x] for x in q], [v[x] for x in q])["P"] < 0.05:
            sig += 1
    out["n_beating_single_pass_p05"] = sig
    return out


def v_n2(res, pub):
    rank = res["rank"]
    return "holds" if rank == 1 and not res["tied"] else ("weakens" if rank <= 4 else "reverses")


def h_n2(res):
    if "rank" not in res:
        return f"{res['units']} draw answers, smallest draw n {res['n_min']}"
    return (f"exp04 RLM-10 {pct(res['exp04_rlm10'])} ranks {res['rank']} of 8{' (tied)' if res['tied'] else ''}; "
            f"{res['n_beating_single_pass_p05']} of 8 draws beat single-pass at P < 0.05")


def _rep_cells(T, field="main"):
    cnt = defaultdict(lambda: [0, 0])
    for (g, _d, s, _q), v in T["rep"].items():
        if s in PAIR and v.get(field) is not None:
            cnt[(g, s)][0] += v[field]
            cnt[(g, s)][1] += 1
    return cnt


def _rep_sample(T, keep) -> dict:
    """Generators (answers each) and questions behind the replication rows a claim uses."""
    ks = [k for k, v in T["rep"].items() if keep(k, v)]
    return {"generators": dict(sorted(Counter(k[0] for k in ks).items())), "n_questions": len({k[3] for k in ks})}


def _pair_main(k, v) -> bool:
    return k[2] in PAIR and v.get("main") is not None


def _deltas(T, min_n):
    cnt = _rep_cells(T)
    gens = sorted({g for g, _ in cnt})
    out = {}
    for g in gens:
        (ks, ns), (kr, nr) = cnt[(g, "single_pass")], cnt[(g, "rlm_10")]
        if ns >= min_n and nr >= min_n:
            out[g] = {"single_pass_pct": 100 * ks / ns, "rlm_10_pct": 100 * kr / nr,
                      "delta_pp": 100 * kr / nr - 100 * ks / ns, "n_sp": ns, "n_rlm": nr}
    return out, cnt


def r1(T):
    rows = sorted(((k, v) for k, v in T["rep"].items() if k[2] in PAIR), key=lambda kv: kv[1]["order"])
    cnt = _rep_cells(T)
    gens = sorted(g for g in {k[0] for k, _ in rows} if all(cnt[(g, s)][1] >= 10 for s in PAIR))
    out = {"units": sum(n for (g, s), (k, n) in cnt.items() if g in gens), "generators_used": gens,
           "ok": REF in gens and len(gens) >= 2, **_rep_sample(T, _pair_main)}
    if not out["ok"]:
        out["units"] = sum(n for (_k, n) in cnt.values())
        return out
    body = [[k[3], k[0], k[1], k[2], v["main"] if v["main"] is not None else 0, int(v["main"] is not None)]
            for k, v in rows if k[0] in gens]
    res = rscript(R_S320, body, ["question_id", "generator", "draw", "strategy", "pass", "scored"],
                  ["{csv}", "{out}", str(R_BOOT)])
    out["n_reps"] = res.pop("n_reps")
    out["by_generator"] = res
    return out


def v_r1(res, pub):
    changed = []
    for g, r in res["by_generator"].items():
        ref = pub["by_generator"].get(g)
        if g == REF or r["verdict"] == "not computable" or ref is None or ref["verdict"] == "not computable":
            continue
        a, b = ref["verdict"], r["verdict"]
        if {a, b} == {"EQUIVALENT", "DIFFERENT"}:
            return "reverses"
        if a != b:
            changed.append(g)
    return "weakens" if changed else "holds"


def h_r1(res):
    if "by_generator" not in res:
        return f"{res['units']} scored answers; reference or a second generator below 10 per cell"
    vs = Counter(r["verdict"] for g, r in res["by_generator"].items() if g != REF)
    eq = [g for g, r in res["by_generator"].items() if r["verdict"] == "EQUIVALENT"]
    df = [g for g, r in res["by_generator"].items() if r["verdict"] == "DIFFERENT"]
    return (f"{len(res['by_generator']) - 1} generators against gemini: equivalent {', '.join(eq) or 'none'}; "
            f"different {', '.join(df) or 'none'}; inconclusive {vs.get('INCONCLUSIVE', 0)}"
            f"{'; not computable ' + str(vs['not computable']) if vs.get('not computable') else ''}; "
            f"{res['n_reps']:,} resamples")


def r2(T):
    d, cnt = _deltas(T, 1)
    ns, nr = cnt[(REF, "single_pass")][1], cnt[(REF, "rlm_10")][1]
    out = {"units": ns + nr, "ok": ns >= 10 and nr >= 10, **_rep_sample(T, lambda k, v: k[0] == REF and _pair_main(k, v))}
    if REF in d:
        out.update(d[REF])
    else:
        out["ok"] = False
    return out


def v_r2(res, pub):
    return magnitude(res["delta_pp"], pub["delta_pp"])


def h_r2(res):
    if "delta_pp" not in res:
        return f"{res['units']} gemini answers"
    return (f"gemini-3-flash RLM-10 {res['rlm_10_pct']:.1f}% (n {res['n_rlm']}) minus single-pass "
            f"{res['single_pass_pct']:.1f}% (n {res['n_sp']}) = {res['delta_pp']:+.1f} pp")


def r3(T):
    d, cnt = _deltas(T, 10)
    out = {"units": sum(x["n_sp"] + x["n_rlm"] for x in d.values()), "ok": len(d) >= 2,
           "deltas": {g: x["delta_pp"] for g, x in d.items()}, **_rep_sample(T, _pair_main)}
    if len(d) == 7:
        out["two_most_negative"] = sorted(sorted(d, key=lambda g: d[g]["delta_pp"])[:2])
    return out


def v_r3(res, pub):
    flips, zero = [], []
    for g, x in res["deltas"].items():
        p = pub["deltas"][g]
        if (p > 0 and x < 0) or (p < 0 and x > 0):
            flips.append(g)
        elif x == 0:
            zero.append(g)
    if flips:
        return "reverses"
    if zero or ("two_most_negative" in res and res["two_most_negative"] != pub["two_most_negative"]):
        return "weakens"
    return "holds"


def h_r3(res):
    if not res["deltas"]:
        return f"{res['units']} answers; no generator with 10 per cell"
    s = ", ".join(f"{g} {x:+.1f}" for g, x in sorted(res["deltas"].items()))
    if "two_most_negative" in res:
        s += f"; most negative {' and '.join(res['two_most_negative'])}"
    return f"RLM-10 minus single-pass (pp): {s}"


def j1(T):
    both = lambda k, v: v.get("main") is not None and v.get("second") is not None  # noqa: E731
    rows = [v for k, v in T["rep"].items() if both(k, v)]
    out = {"units": len(rows), "ok": len(rows) >= 50, **_rep_sample(T, both)}
    if len(rows) < 2:
        out["ok"] = False
        return out
    a, b = [bool(v["main"]) for v in rows], [bool(v["second"]) for v in rows]
    m = sf.mcnemar_from_vectors(a, b, ("main", "second"))
    out.update(rate_main=m["rate_main"], rate_second=m["rate_second"], gap=m["rate_main"] - m["rate_second"],
               main_only=m["main_only"], second_only=m["second_only"], disagreements=m["discordant"])
    if len(set(a)) > 1 or len(set(b)) > 1:
        k = sf.cohens_kappa(a, b)
        out.update(agreement=k["agreement"], kappa=k["kappa"])
    return out


def v_j1(res, pub):
    return magnitude(res["gap"], pub["gap"])


def h_j1(res):
    if "gap" not in res:
        return f"{res['units']} answers scored by both judges"
    return (f"second judge passes {pct(res['rate_second'])}, main {pct(res['rate_main'])}; agreement "
            f"{pct(res.get('agreement'))}, kappa {res.get('kappa', float('nan')):.2f}; {res['main_only']} of "
            f"{res['disagreements']} disagreements passed by the main judge only; n {res['units']:,}")


# ── D1: the depth saturation, concept recall (no judge) ──────────────────────────────────────────

def d1_all(d7: set) -> dict:
    import S184_depth_share_2x2 as S184
    raw = json.load(open(S184.PRIMARY))["results"]
    records = [r for r in raw if r.get("depth") is not None and r.get("question_id") is not None
               and r.get("concept_recall") is not None]
    per_q = defaultdict(set)
    for r in records:
        per_q[r["question_id"]].add(int(r["depth"]))
    all_depths = {int(r["depth"]) for r in records}
    every = {q for q, ds in per_q.items() if ds == all_depths}       # S184: the balanced set, on the full records
    stale = stale_key(S383C)
    s383 = {}
    with S383C.open() as fh:
        for r in csv.DictReader(l for l in fh if not l.startswith("#")):
            if r["model"] == REF:
                s383[(int(r["depth"]), r["question_id"])] = r

    def shares(recs, qset):
        c = S184.cell(recs, qset, "crashes_out")
        lo, se = c["fits"]["logistic"]["share_at_depth_7"], c["fits"]["satexp"]["share_at_depth_7"]
        return {"units": c["n_records"], "ok": True, "n_questions": c["n_questions"], "logistic": lo, "satexp": se,
                "min_share": min(lo, se), "max_share": max(lo, se),
                "mean_cr_7_to_50": sum(c["per_depth_mean"][d] for d in DEPTHS) / len(DEPTHS)}

    def with_col(col):
        out = []
        for r in records:
            if r["question_id"] in d7:
                continue
            v = s383[(int(r["depth"]), r["question_id"])][col]
            out.append(dict(r, concept_recall=float(v)))
        return out

    return {"published": shares(records, every), "d7": shares(with_col("concept_recall_v1"), every - d7),
            "v22": ({"units": 0, "ok": False, "stale": stale, "recorded_key_sha256": sorted(recorded_key_sha(S383C))}
                    if stale else shares(with_col("concept_recall_v22"), every - d7))}


def e11_all(d7: set) -> dict:
    """MT-07 'whereas RLM-20 achieved the highest concept recall': mean concept recall per strategy over the
    answerable exp04 answers. Published: the deposit, as S04b reads it. D7: the same, the kept answers. v22 (the
    current key): S382, only when S382 records the sha256 of S373.AS_V1 (stale_key); else not computed."""
    dep = json.load(open(DETERM))["per_result"]
    v1 = {}
    for r in dep:
        if r["answerable"]:                                   # S04b's filter
            k = (r["config"], r["question_id"])
            assert k not in v1, f"duplicate deterministic row {k}"
            v1[k] = float(r["objective_metrics"]["concept_recall"])
    stale = stale_key(S382C)
    v22, v1_s382 = {}, {}
    with S382C.open() as fh:
        for r in csv.DictReader(l for l in fh if not l.startswith("#")):
            if r.get("group", "answerable") != "answerable":     # D5: S382's refutation rows have no v1 value
                continue
            v22[(r["config"], r["question_id"])] = float(r["concept_recall_v22"])
            v1_s382[(r["config"], r["question_id"])] = float(r["concept_recall_v1"])

    def ranking(vals: dict) -> dict:
        per = defaultdict(list)
        for (c, _q), x in vals.items():
            per[c].append(x)
        mean = {s: sum(per[s]) / len(per[s]) for s in STRATS}
        return {"units": len(vals), "ok": True, "n_questions": len({q for _c, q in vals}),
                "n_per_strategy": {s: len(per[s]) for s in STRATS}, "mean": mean,
                "ranking": sorted(STRATS, key=lambda s: -mean[s]),
                "rlm_20_rank": 1 + sum(mean[o] > mean["rlm_20"] for o in STRATS if o != "rlm_20"),
                "rlm_20_tied": any(mean[o] == mean["rlm_20"] for o in STRATS if o != "rlm_20"),
                "rlm_20_minus_rlm_10": mean["rlm_20"] - mean["rlm_10"]}

    kept = {k: x for k, x in v1.items() if k[1] not in d7}
    out = {"published": ranking(v1), "d7": ranking(kept),
           "v22": ({"units": 0, "ok": False, "stale": stale, "recorded_key_sha256": sorted(recorded_key_sha(S382C))}
                   if stale else ranking({k: v22[k] for k in kept}))}
    out["published"]["s382_v1_equals_deposit"] = (set(v1_s382) == set(kept)
                                                  and all(abs(v1_s382[k] - kept[k]) < 1e-12 for k in kept))
    return out


def v_e11(res, pub):
    if res["rlm_20_rank"] == 1 and not res["rlm_20_tied"]:
        return "holds"
    return "reverses" if res["mean"]["rlm_10"] > res["mean"]["rlm_20"] else "weakens"


def h_e11(res):
    m = res["mean"]
    return (f"RLM-20 {100 * m['rlm_20']:.1f}%, RLM-10 {100 * m['rlm_10']:.1f}% (RLM-20 minus RLM-10 "
            f"{100 * res['rlm_20_minus_rlm_10']:+.2f} pp; RLM-20 ranks {res['rlm_20_rank']}); top "
            f"{res['ranking'][0]}; {res['units']} answers")


def v_d1(res, pub):
    return "holds" if res["min_share"] >= 0.75 else ("weakens" if res["min_share"] >= 0.5 else "reverses")


def h_d1(res):
    return (f"7 turns reach {pct(res['logistic'])} (logistic) and {pct(res['satexp'])} (saturating exponential) "
            f"of the fitted gain; mean concept recall at caps 7 to 50 {res['mean_cr_7_to_50']:.2f}; "
            f"{res['n_questions']} questions, {res['units']} records")


# ── the registry of claims ────────────────────────────────────────────────────────────────────────

def _close(got, want, places):
    return got is not None and round(got, places) == want


CLAIMS = [
    {"id": "E1", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results: 'Among iterative strategies, RLM-10 achieved the highest' and 'Conversely, passage "
              "verification, which filters' (MT-07, MT-08)",
     "claim": "RLM-10 has the highest pass rate of the six strategies (92.0%) and passage verification the lowest (67.0%)",
     "statistic": "pass rate per strategy, judge correctness 3 or more on complete answers, Wilson intervals "
                  "(S281, S318 fig2a_wilson)",
     "rule": "holds: RLM-10 first and verification last, untied; weakens: either falls to rank 2 or 3 (from its end) "
             "or ties; reverses: either reaches the other half of the ranking",
     "f": e1, "v": v_e1, "h": h_e1,
     "gate": lambda r: [("rlm_10 %", _close(100 * r["rlm_10_rate"], 92.0, 1)),
                        ("verified %", _close(100 * r["verified_pass_rate"], 67.0, 1)),
                        ("n 88 each", all(r[f"{s}_n"] == 88 for s in STRATS)),
                        ("ranks", r["rlm_10_rank"] == 1 and r["verified_rank_from_bottom"] == 1)]},
    {"id": "E2", "exp": "Generation strategies (exp04)",
     "where": "Abstract 'Passage verification before generation is counterproductive'; Main Text 'At the primary "
              "correctness threshold' (AB-02, MT-09, MT-76)",
     "claim": "passage verification is counterproductive: 15 of 19 changed outcomes go from correct to incorrect (78.9%, "
              "McNemar P = 0.019), degrading 15 of 70 correct answers (21.4%)",
     "statistic": "exact McNemar, single-pass against passage verification paired by question, threshold 3; harmful "
                  "share = single-pass-only / discordant (S281, S318 flip_t3)",
     "rule": "holds: harmful share above 50% and P < 0.05; weakens: above 50%, P >= 0.05; reverses: 50% or below "
             "(the plan's own reversal criterion)",
     "f": paired04("single_pass", "verified_pass", 3), "v": v_flip, "h": h_flip,
     "gate": lambda r: [("15 of 19", (r["a_only"], r["discordant"]) == (15, 19)), ("78.9%", _close(100 * r["harmful"], 78.9, 1)),
                        ("P 0.019", _close(r["P"], 0.019, 3)), ("70 correct", r["baseline_correct"] == 70),
                        ("21.4%", _close(100 * r["degraded"], 21.4, 1))]},
    {"id": "E3", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results: 'Under a stricter threshold (judge score' (MT-10)",
     "claim": "at threshold 4, 15 of 18 changes reduce accuracy (83.3%, P = 0.0075), impairing 15 of 47 correct answers (31.9%)",
     "statistic": "as E2 at threshold 4 (S318 flip_t4)",
     "rule": "as E2",
     "f": paired04("single_pass", "verified_pass", 4), "v": v_flip, "h": h_flip,
     "gate": lambda r: [("15 of 18", (r["a_only"], r["discordant"]) == (15, 18)), ("83.3%", _close(100 * r["harmful"], 83.3, 1)),
                        ("P 0.0075", _close(r["P"], 0.0075, 4)), ("47 correct", r["baseline_correct"] == 47),
                        ("31.9%", _close(100 * r["degraded"], 31.9, 1))]},
    {"id": "E4", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results: 'Overall, RLM-10's pass rate significantly outperformed' (MT-11)",
     "claim": "RLM-10's pass rate significantly exceeds passage verification's (McNemar P < 0.001, Cohen's h = 0.65)",
     "statistic": "exact McNemar, RLM-10 against passage verification paired by question (S318 rlm10_vs_verified)",
     "rule": "holds: RLM-10 higher and P < 0.05; weakens: higher or equal, P >= 0.05; reverses: lower",
     "f": paired04("rlm_10", "verified_pass"), "v": v_better, "h": h_better,
     "gate": lambda r: [("P < 0.001", r["P"] < 0.001), ("h 0.65", _close(r["cohens_h"], 0.65, 2))]},
    {"id": "E5", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Discussion: 'At the scale of the generation-strategy experiment' (MT-83, the deployment guidance)",
     "claim": "RLM-10 exceeds single-pass retrieval by 12.5 percentage points (McNemar P = 0.019)",
     "statistic": "exact McNemar, RLM-10 against single-pass paired by question (S318 rlm10_vs_single_s20)",
     "rule": "as E4",
     "f": paired04("rlm_10", "single_pass"), "v": v_better, "h": h_better,
     "gate": lambda r: [("n 88", r["n_pairs"] == 88), ("12.5 pp", _close(100 * r["diff"], 12.5, 1)),
                        ("P 0.019", _close(r["P"], 0.019, 3))]},
    {"id": "E6", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results: 'Multi-hop retrieval correctly refused 40.0%' and 'Passage verification and RLM-20 "
              "achieved the highest refusal' (MT-15, MT-16)",
     "claim": "RLM-10 refuses 82.0% of out-of-domain questions against 40.0% for multi-hop",
     "statistic": "share of out-of-domain answers with judge refusal accuracy 3 or more, per strategy, Wilson (S281, "
                  "S318 fig2d_wilson)",
     "rule": "on the gap RLM-10 minus multi-hop: holds at half the reference gap or more; weakens below half; reverses below "
             "zero. From column (b') on, the out-of-domain questions with no answer in the papers (D5): the ten "
             "false-premise questions are out of the units on both sides and reported as their own group",
     "f": e6, "v": lambda r, p: magnitude(r["gap"], p["gap"]), "h": h_e6,
     "gate": lambda r: [("rlm_10 82.0", _close(100 * r["rlm_10_rate"], 82.0, 1)),
                        ("multi_hop 40.0", _close(100 * r["multi_hop_rate"], 40.0, 1)),
                        ("verified 86.0", _close(100 * r["verified_pass_rate"], 86.0, 1)),
                        ("rlm_20 86.0", _close(100 * r["rlm_20_rate"], 86.0, 1)),
                        ("n 50, RLM-5 47", r["rlm_10_n"] == 50 and r["rlm_5_n"] == 47)]},
    {"id": "E7", "exp": "Generation strategies (exp04)",
     "where": "Abstract 'it rates over half of the answers it calls completely incorrect as perfectly faithful'; Main Text "
              "'Within the full 528-answer corpus' and 'showed a ceiling effect, with 80.3%' (AB-03, MT-53, MT-49)",
     "claim": "the judge rates over half of the answers it scores completely incorrect (correctness 0) as perfectly "
              "faithful: 33 of 56; 80.3% of all answers get 5/5",
     "statistic": "cross-tabulation of judge correctness 0 against judge faithfulness 5 over the answerable answers "
                  "(S37 zero_cost, S236)",
     "rule": "holds: above 50%; weakens: at or below 50% but at least half the reference share; reverses: below that",
     "f": e7, "v": v_e7, "h": h_e7,
     "gate": lambda r: [("33 of 56", (r["of_which_faith_5"], r["n_correctness_0"]) == (33, 56)),
                        ("80.3% at 5/5", _close(100 * r["share5_all"], 80.3, 1)), ("424 of 528", (r["n_faith_5"], r["units"]) == (424, 528))]},
    {"id": "E8", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results 'Faithfulness scoring by the LLM judge showed a ceiling effect, with 80.3%'; Discussion "
              "'The judge rated 80.3% of answers as perfectly faithful' (MT-49, MT-79, MT-79a)",
     "claim": "the judge's faithfulness score sits at a ceiling: 80.3% of the answers get 5/5",
     "statistic": "share of answerable answers with judge faithfulness 5 (S236, S37)",
     "rule": "holds: 75% or more at 5/5; weakens: 50% to 75%; reverses: under 50% (the maximum is no longer the score "
             "most answers get)",
     "f": e8, "v": v_e8, "h": h_e8,
     "gate": lambda r: [("424 of 528", (r["n_faith_5"], r["units"]) == (424, 528)), ("80.3%", _close(100 * r["share"], 80.3, 1))]},
    {"id": "E9", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results 'Source-grounded precision spanned 0.00 to 1.00 (median 0.57), with 38.0%'; Discussion "
              "'38.0% of the answers it rated 5/5 had fewer than half their statements supported' (MT-56, MT-79)",
     "claim": "of the answers the judge rates 5/5 for faithfulness, 38.0% (161 of 424) have fewer than half their "
              "statements supported by the source papers (median precision 0.57)",
     "statistic": "MiniCheck precision against the source papers (top-3 passages; no judge, no key) over the judge's "
                  "5/5 subset; share below 0.50 (S19 source k3, S236)",
     "rule": "holds: the share is at least half the reference one; weakens: below that (the statistic has no "
             "reversal of its own; E10 carries the direction)",
     "f": e9, "v": lambda r, p: "holds" if r["share"] >= p["share"] / 2 else "weakens", "h": h_e9,
     "gate": lambda r: [("161 of 424", (r["below_half"], r["n_at5"]) == (161, 424)), ("38.0%", _close(100 * r["share"], 38.0, 1)),
                        ("median 0.57", _close(r["median"], 0.57, 2))]},
    {"id": "E10", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results 'Across the top three score tiers (scores 3 to 5, 500 answers), this association "
              "disappeared' (MT-58, MT-79a)",
     "claim": "among answers the judge scores 3 to 5 for faithfulness, its score is unrelated to source-grounded "
              "precision (Spearman rho = 0.05, P = 0.24, 500 answers)",
     "statistic": "Spearman rank correlation of judge faithfulness with MiniCheck source precision over the answers at "
                  "faithfulness 3 or more (S19, S21, S318 nli_precision_vs_faithfulness_top3)",
     "rule": "a claim of no association: reverses if rho > 0 with P < 0.05; holds otherwise, but only at 80% coverage "
             "or more",
     "null": True, "f": e10, "v": v_e10, "h": h_e10,
     "gate": lambda r: [("n 500", r["n_top3"] == 500), ("rho 0.05", _close(r["rho"], 0.05, 2)), ("P 0.24", _close(r["P"], 0.24, 2))]},
    {"id": "E11", "exp": "Generation strategies (exp04)",
     "where": "Main Text, Results 'Among iterative strategies, RLM-10 achieved the highest pass rate (92.0%; Fig. 2a), "
              "whereas RLM-20 achieved the highest concept recall (72.3%; Fig. 2b)' (MT-07; the answer to Reviewer 3, "
              "Major Point 3, LT-70; worklist F6)",
     "claim": "RLM-20 has the highest concept recall of the six strategies (72.3%; RLM-10 72.1%), in contrast with the "
              "pass rate, where RLM-10 leads",
     "statistic": "mean concept recall (deterministic, against the key) per strategy over the answerable answers "
                  f"(S04b concept_recall_pct_answerable_n88; {KV} from S382; no judge)",
     "rule": "holds: RLM-20 first, untied; reverses: RLM-10 above RLM-20 (the sentence's contrast inverts: RLM-10 "
             "leads on both); weakens: RLM-20 below another strategy, or tied. No judge: S382 scores every exp04 "
             f"answer against {KV}, so coverage is 100% and the matched columns are the D7 columns",
     "f": None, "nojudge": e11_all, "v": v_e11, "h": h_e11,
     "gate": lambda r: [("S04b per strategy", all(round(100 * r["mean"][s], 2) == json.loads(S04B.read_text())
                                                   ["2_generation_strategies"]["concept_recall_pct_answerable_n88"][s]
                                                   for s in STRATS)),
                        ("72.3", _close(100 * r["mean"]["rlm_20"], 72.3, 1)), ("rank 1", r["rlm_20_rank"] == 1),
                        ("n 88 each", all(n == 88 for n in r["n_per_strategy"].values())),
                        ("S382 v1 column is the deposit", r["s382_v1_equals_deposit"])]},
    {"id": "S1", "exp": "Corpus scaling (exp05)",
     "where": "Main Text, Results 'At 50 core papers, however, single-pass retrieval surpassed RLM-10'; Discussion "
              "'At 50 core papers, single-pass retrieval was more accurate at all three' (MT-27, MT-85; the "
              "recommendation of single-pass at about fifty papers)",
     "claim": "at 50 core papers single-pass beats RLM-10 at all three noise ratios (0x: 83.2% against 62.8%, 20.4 pp, "
              "Bonferroni P < 0.001 in each)",
     "statistic": "exact McNemar per index configuration on questions both strategies answered, Bonferroni x12 (S66, "
                  "S318 scaling_s50_n0 and suppfig8)",
     "rule": "holds: single-pass ahead in all three, each Bonferroni P < 0.05; weakens: ahead in all three, not all "
             "significant; reverses: behind in any",
     "f": s1, "v": v_s1, "h": h_cells,
     "gate": lambda r: [("0x 83.2 vs 62.8", _close(100 * r["cells"]["50 core, 0x"]["single_pass"], 83.2, 1)
                         and _close(100 * r["cells"]["50 core, 0x"]["rlm_10"], 62.8, 1)),
                        ("0x 20.4 pp", _close(100 * r["cells"]["50 core, 0x"]["sp_minus_rlm"], 20.4, 1)),
                        ("1x 19.6, 3x 20.7", _close(100 * r["cells"]["50 core, 1x"]["sp_minus_rlm"], 19.6, 1)
                         and _close(100 * r["cells"]["50 core, 3x"]["sp_minus_rlm"], 20.7, 1)),
                        ("n 196/199/198", [r["cells"][f"50 core, {n}x"]["n"] for n in "013"] == [196, 199, 198]),
                        ("Bonferroni < 0.001", all(c["P_bonferroni"] < 0.001 for c in r["cells"].values()))]},
    {"id": "S2", "exp": "Corpus scaling (exp05)",
     "where": "Main Text, Results 'we found no credible evidence of a performance difference between RLM-10 and "
              "single-pass retrieval across 5, 10 or 20 core papers' (MT-26, MT-84)",
     "claim": "no credible difference between RLM-10 and single-pass at 5, 10 or 20 core papers at any noise ratio "
              "(Bonferroni P = 1.00 in all nine cells)",
     "statistic": "as S1, the nine cells at 5, 10 and 20 core papers",
     "rule": "a claim of no difference: reverses if any cell reaches Bonferroni P < 0.05; holds otherwise, but only "
             "at 80% coverage or more; minimum one cell with 10 pairs",
     "null": True, "f": s2, "v": v_s2, "h": h_s2,
     "gate": lambda r: [("nine cells", r["n_cells"] == 9), ("all Bonferroni 1.00", all(_close(c["P_bonferroni"], 1.0, 2)
                                                                                    for c in r["cells"].values())),
                        ("n per cell", [r["cells"][f"{c} core, {n}x"]["n"] for c in ("5", "10", "20") for n in "013"]
                         == [19, 20, 20, 42, 43, 41, 86, 87, 88])]},
    {"id": "S3", "exp": "Corpus scaling (exp05)",
     "where": "Main Text, Results 'Across all twelve configurations, the population-average interaction' and "
              "'Strategy ranking therefore follows the volume of target evidence' (MT-28, MT-28a)",
     "claim": "the strategy x log(core papers) interaction is -0.83 (95% CI -1.43 to -0.27) while strategy x "
              "log(1 + noise) is -0.07 (-0.27 to +0.13): the ranking follows the target evidence, not index size",
     "statistic": "logistic GLM pass ~ strategy * (log core + log(1 + noise)), cluster bootstrap over questions, "
                  "10,000 resamples, seed 20260722, median and percentile interval (S67 primary_bootstrap, in R)",
     "rule": "holds: core interval wholly below zero and noise interval across zero; weakens: core estimate negative "
             "otherwise; reverses: core estimate zero or above",
     "f": s3, "v": v_s3, "h": h_s3,
     "gate": lambda r: [("S67 core", r["core_est"] == -0.828 and r["core_ci"] == [-1.427, -0.268]),
                        ("S67 noise", r["noise_est"] == -0.073 and r["noise_ci"] == [-0.273, 0.126]),
                        ("S67 file", _s67_file_matches(r)), ("10,000", r["n_reps"] == 10000)]},
    {"id": "D1", "exp": "Retrieval depth (exp09)",
     "where": "Abstract 'Iterative retrieval gains little beyond about seven turns'; Main Text 'For gemini-3-flash, "
              "75.9% to 84.0% of achievable recall gains' and Discussion 'Concept recall saturated with retrieval "
              "depth' (AB-02a, MT-03a, MT-21, MT-77)",
     "claim": "seven turns realise 75.9% to 84.0% of the achievable concept-recall gain (logistic and saturating "
              "exponential fits, the questions answered at every depth, turn-cap crashes set aside)",
     "statistic": "S184 balanced set, crashes out: fits to the per-depth mean concept recall, share of the fitted gain "
                  "from depth 1 reached at depth 7 (no judge: concept recall against the key)",
     "rule": "on the smaller of the two shares: holds at 75% or more; weakens from 50% to 75%; reverses below 50%. No "
             f"judge: S383 scores every record against {KV}, so coverage is 100% and the matched columns are the D7 columns",
     "f": None, "nojudge": d1_all, "v": v_d1, "h": h_d1,
     "gate": lambda r: [("logistic 0.7588", _close(r["logistic"], 0.7588, 4)), ("satexp 0.8399", _close(r["satexp"], 0.8399, 4)),
                        ("78 questions", r["n_questions"] == 78)]},
    {"id": "P1", "exp": "Pipeline ablation (exp06)",
     "where": "Main Text, Results 'Full orchestration combining planning, supervision' and 'Pipeline complexity did not "
              "produce monotonic improvements' (MT-39, MT-35a)",
     "claim": "full orchestration lowers the pass rate to 55.7%, 36.4 pp below RLM-10 alone (92.0%)",
     "statistic": "pass rate per configuration, judge correctness 3 or more on complete answers, Wilson (S281, S318 fig4a_wilson)",
     "rule": "on the gap RLM-10 minus full orchestration: holds at half the reference gap or more; weakens below; reverses below zero",
     "f": p_gap("rlm_10", "full_orchestrator"), "v": lambda r, p: magnitude(r["gap"], p["gap"]),
     "h": h_gap(("RLM-10", "full orchestrator")),
     "gate": lambda r: [("92.0", _close(100 * r["rate_hi"], 92.0, 1)), ("55.7", _close(100 * r["rate_lo"], 55.7, 1)),
                        ("36.4 pp", _close(100 * r["gap"], 36.4, 1)), ("n 88", (r["n_hi"], r["n_lo"]) == (88, 88))]},
    {"id": "P2", "exp": "Pipeline ablation (exp06)",
     "where": "Main Text, Results 'Adding naive RAG reduced the answerable pass rate' (MT-37, MT-36)",
     "claim": "adding naive RAG lowers the answerable pass rate from 89.8% (closed book) to 78.4% (11.4 pp)",
     "statistic": "as P1",
     "rule": "on the gap closed book minus naive RAG, as P1",
     "f": p_gap("raw_gemini", "naive_rag"), "v": lambda r, p: magnitude(r["gap"], p["gap"]),
     "h": h_gap(("closed book", "naive RAG")),
     "gate": lambda r: [("89.8", _close(100 * r["rate_hi"], 89.8, 1)), ("78.4", _close(100 * r["rate_lo"], 78.4, 1)),
                        ("11.4 pp", _close(100 * r["gap"], 11.4, 1))]},
    {"id": "P3", "exp": "Pipeline ablation (exp06)",
     "where": "Main Text, Results 'RLM-10 reached a 92.0% pass rate (2.3 percentage points above' (MT-38)",
     "claim": "RLM-10 is 2.3 pp above the closed-book baseline (92.0% against 89.8%)",
     "statistic": "as P1",
     "rule": "on the gap RLM-10 minus closed book, as P1",
     "f": p_gap("rlm_10", "raw_gemini"), "v": lambda r, p: magnitude(r["gap"], p["gap"]),
     "h": h_gap(("RLM-10", "closed book")),
     "gate": lambda r: [("2.3 pp", _close(100 * r["gap"], 2.3, 1))]},
    {"id": "P4", "exp": "Pipeline ablation (exp06)",
     "where": "Main Text, Results 'while failing to refuse any of the 50 OOD questions' and 'establishing an 86.0% "
              "refusal rate'; Discussion 'retrieval is a necessary but insufficient safety layer' (MT-36, MT-37, MT-86)",
     "claim": "without retrieval no out-of-domain question is refused (0 of 50); naive RAG refuses 86.0% (43 of 50) "
              "and the full orchestrator 3 of 50",
     "statistic": "share of out-of-domain answers with judge refusal accuracy 3 or more, per configuration (S281)",
     "rule": "on both gaps, naive RAG minus closed book and naive RAG minus full orchestrator: the worse of the two, "
             "each as P1. From column (b') on, as E6: the ten false-premise questions are out of the units and "
             "reported as their own group",
     "f": p4, "v": v_p4, "h": h_p4,
     "gate": lambda r: [("closed book 0 of 50", r["raw_gemini_rate"] == 0 and r["raw_gemini_n"] == 50),
                        ("naive 86.0", _close(100 * r["naive_rag_rate"], 86.0, 1)),
                        ("full 3 of 50", round(r["full_orchestrator_rate"] * 50) == 3 and r["full_orchestrator_n"] == 50)]},
    {"id": "N1", "exp": "Naive RAG baseline, with the RLM draws",
     "where": "Main Text, Results 'Three runs of passive retrieval, one naive RAG and two single-pass, varied by 2.3' "
              "and 'Across eight runs of RLM on the same 88 questions' (MT-12, MT-13)",
     "claim": "the three passive-retrieval runs (naive RAG, exp04 and exp05 single-pass) vary by 2.3 pp while eight "
              "RLM runs range from 76.7% to 92.0%",
     "statistic": "pass rate per run on the 20-paper index, judge correctness 3 or more; spread = highest minus lowest (S78)",
     "rule": "holds: the passive spread is below the RLM spread; reverses otherwise",
     "f": n1, "v": v_n1, "h": h_n1,
     "gate": lambda r: [("passive 2.27", _close(r["passive_spread"], 2.27, 2)),
                        ("RLM 76.7442 to 92.0455", _close(r["rlm_min"], 76.7442, 4) and _close(r["rlm_max"], 92.0455, 4)),
                        ("median 82.76", _close(r["rlm_median"], 82.76, 2))]},
    {"id": "N2", "exp": "Naive RAG baseline, with the RLM draws",
     "where": "Main Text, Results 'The RLM-10 run of this experiment was the highest of the eight'; Discussion 'only "
              "this one separated from single-pass at the 5% level' (MT-14, MT-84)",
     "claim": "the generation-strategy RLM-10 run is the highest of the eight RLM runs, and the only one that beats "
              "single-pass at P < 0.05",
     "statistic": "as N1; exact McNemar of each RLM run against exp04 single-pass (S78)",
     "rule": "on the rank of the exp04 run: holds first and untied; weakens 2 to 4; reverses 5 to 8 (the count of "
             "runs beating single-pass is reported beside it)",
     "f": n2, "v": v_n2, "h": h_n2,
     "gate": lambda r: [("rank 1", r["rank"] == 1 and not r["tied"]), ("1 of 8", r["n_beating_single_pass_p05"] == 1)]},
    {"id": "R1", "exp": "Strategy replication (seven generators)",
     "where": "Main Text, Results 'Under qwen3-coder:30b, glm-4.7-flash:30b and qwen3.5:122b met' and Discussion 'of the "
              "six other models, two met the equivalence criterion under one judge' (MT-32, MT-88, LT-50)",
     "claim": "under the main judge glm-4.7-flash and qwen3.5:122b meet equivalence with gemini-3-flash, nemotron-3-nano "
              "rejects it, claude-haiku-4-5, gemma3:27b and qwen3-coder:30b are inconclusive",
     "statistic": "RLM-10 minus single-pass per generator, differenced against gemini-3-flash, cluster bootstrap over "
                  "questions (10,000, seed 20260722), 10 pp margin (S320, in R)",
     "rule": "per generator with data, against the reference verdict: reverses if any verdict moves between equivalent "
             "and different; weakens if any moves to or from inconclusive; holds if none moves, and below full "
             "coverage only once all seven generators have data (a claim for every generator)",
     "every": lambda r: len(r.get("by_generator") or {}) == 7,
     "f": r1, "v": v_r1, "h": h_r1,
     "gate": lambda r: [("S320 exact", _s320_matches(r))]},
    {"id": "R2", "exp": "Strategy replication (seven generators)",
     "where": "Main Text, Results 'For gemini-3-flash, RLM-10 exceeded single-pass by 6.4' (MT-34)",
     "claim": "for gemini-3-flash over three draws, RLM-10 exceeds single-pass by 6.4 pp under the main judge",
     "statistic": "pass rate difference over the scored answers of three draws (S320 delta_pp)",
     "rule": "holds at half the reference difference or more; weakens below; reverses below zero",
     "f": r2, "v": v_r2, "h": h_r2,
     "gate": lambda r: [("6.39", _close(r["delta_pp"], 6.39, 2))]},
    {"id": "R3", "exp": "Strategy replication (seven generators)",
     "where": "Supplementary Fig. 5a; letter, Reviewer 2 Comment 2 'Nemotron and qwen3-coder:30b have the two most "
              "negative differences' (LT-49, LT-50)",
     "claim": "the strategy order per generator: RLM-10 above single-pass for five of seven generators, below for "
              "nemotron-3-nano and qwen3-coder:30b, which have the two most negative differences",
     "statistic": "RLM-10 minus single-pass pass rate per generator (S320 delta_pp)",
     "rule": "per generator with 10 answers per cell: reverses if any sign flips; weakens if a difference is zero or "
             "(with all seven) the two most negative change; holds otherwise, and below full coverage only once all "
             "seven generators have data (a claim for every generator)",
     "every": lambda r: len(r.get("deltas") or {}) == 7,
     "f": r3, "v": v_r3, "h": h_r3,
     "gate": lambda r: [("S320 deltas", _s320_deltas(r)),
                        ("two most negative", r.get("two_most_negative") == ["nemotron-3-nano:30b", "qwen3-coder:30b"])]},
    {"id": "J1", "exp": "Strategy replication, both judges",
     "where": "Main Text, Results 'The second judge was stricter, passing 40.3%' (MT-48, MT-47)",
     "claim": "the second judge (gpt-oss:120b) is stricter than the main judge: 40.3% of answers passed against 72.6%; "
              "agreement 67.7% of 8,379 answers, kappa 0.41",
     "statistic": "pass rates of the two judges on the answers both scored, Cohen's kappa, exact McNemar (S141, S318 "
                  "judge_two_judge_kappa)",
     "rule": "on the gap main minus second judge: holds at half the reference gap or more; weakens below; reverses "
             "below zero. New scores: devstral and gpt-oss:120b at effort low, both on the current key. gpt-oss's "
             "scores are the rows of its production ledgers that are present, S373_gptoss_replication5.jsonl (the "
             "five-model replication, item 12) and S373_gptoss_replication2.jsonl (the two-model replication, Q57), so "
             "J1's coverage has a ceiling, the answers of its units with a current gpt-oss score, given on its line",
     "f": j1, "v": v_j1, "h": h_j1,
     "gate": lambda r: [("n 8,379", r["units"] == 8379), ("67.7%", _close(100 * r["agreement"], 67.7, 1)),
                        ("kappa 0.41", _close(r["kappa"], 0.41, 2)), ("72.6 / 40.3", _close(100 * r["rate_main"], 72.6, 1)
                                                                       and _close(100 * r["rate_second"], 40.3, 1)),
                        ("2,708 of 2,710", (r["main_only"], r["disagreements"]) == (2708, 2710))]},
]


def _s320_matches(r) -> bool:
    pub = json.loads(S320J.read_text())["qwen3_coder_30b"]
    if r.get("n_reps") != pub["n_reps"]:
        return False
    for g, want in pub.items():
        if g == "n_reps":
            continue
        got = r["by_generator"].get(g)
        if got is None:
            return False
        for f in ("single_pass_pct", "rlm_10_pct", "delta_pp", "did_pp"):
            if abs(got[f] - want[f]) > 1e-9:
                return False
        if [round(x, 2) for x in got["ci_pp"]] != [round(x, 2) for x in want["ci_pp"]] or got["verdict"] != want["verdict"]:
            return False
    return True


def _s320_deltas(r) -> bool:
    pub = json.loads(S320J.read_text())["qwen3_coder_30b"]
    return len(r["deltas"]) == 7 and all(_close(r["deltas"][g], pub[g]["delta_pp"], 2) for g in r["deltas"])


def _s67_file_matches(r) -> bool:
    b = json.loads(S67J.read_text())["primary_bootstrap"]
    c, n = b["strategyrlm_10:log_core_c"], b["strategyrlm_10:log_noise_c"]
    return (r["core_est"], r["core_ci"], r["noise_est"], r["noise_ci"]) == (c["est"], c["ci"], n["est"], n["ci"])


def answer_shift(M1: dict, MDV: dict) -> list[dict]:
    """On the matched answers: the same per-answer indicator under the original and the new scores, paired. Not a
    claim: it shows how far individual answers move and whether the move is beyond noise (exact McNemar)."""
    spec = [("exp04", "pass (correctness >= 3)", lambda v: v["ans"] and v.get("cor") is not None, lambda v: v["cor"] >= 3),
            ("exp04", "faithfulness 5/5", lambda v: v["ans"] and v.get("fai") is not None, lambda v: v["fai"] == 5),
            ("exp04", "refusal (out of domain, no answer in the papers, >= 3)", lambda v: not v["ans"] and v.get("ref") is not None,
             lambda v: v["ref"] >= 3),
            ("exp05", "pass", lambda v: v.get("cor") is not None, lambda v: v["cor"] >= 3),
            ("exp06", "pass", lambda v: v["ans"] and v.get("cor") is not None, lambda v: v["cor"] >= 3),
            ("exp06", "refusal (out of domain, no answer in the papers, >= 3)", lambda v: not v["ans"] and v.get("ref") is not None,
             lambda v: v["ref"] >= 3),
            ("naive", "pass", lambda v: v.get("cor") is not None, lambda v: v["cor"] >= 3),
            ("exp09", "pass (gemini, caps 7 to 50)", lambda v: v.get("p3") is not None, lambda v: bool(v["p3"])),
            ("rep", "pass, main judge", lambda v: v.get("main") is not None, lambda v: bool(v["main"])),
            ("rep", f"pass, second judge (gpt-oss v1 against gpt-oss {KV})", lambda v: v.get("second") is not None,
             lambda v: bool(v["second"]))]
    out = []
    for exp, what, keep, ind in spec:
        ks = [k for k, v in M1[exp].items() if keep(v)]
        if not ks:
            out.append({"table": exp, "indicator": what, "n": 0})
            continue
        a, b = [ind(M1[exp][k]) for k in ks], [ind(MDV[exp][k]) for k in ks]
        m = sf.mcnemar_from_vectors(a, b, ("original", "new"))
        out.append({"table": exp, "indicator": what, "n": len(ks), "original": m["rate_original"], "new": m["rate_new"],
                    "original_only": m["original_only"], "new_only": m["new_only"], "P": m["P"],
                    "n_questions": len({k if isinstance(k, str) else k[-1] for k in ks}),
                    "generators": dict(sorted(Counter(k[0] for k in ks).items())) if exp == "rep" else None})
    return out


def rep_order(res: Resolver, studio_rows: list[dict] | None) -> dict:
    """Where the Mac Studio's replication5 ledger stands in S373's own order: S373 sorts the source's items by key
    and leaves out the questions whose wording changed (its main()), and the Mac Studio works through that list in
    order. Returns the S141 replication units in that order, the first gemini-3-flash item, and how far the
    ledger has got."""
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}
    v2 = {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}
    items = sorted(S373.SOURCES["replication5"](v1, v2), key=lambda x: x["key"])
    changed = {q for q, r in v2.items() if r.get("question") and r["question"] != v1[q]["question"]}
    items = [x for x in items if x["question_id"] not in changed]
    keys, units, gens, side = [], [], [], {}
    for i, x in enumerate(items):
        tag = x["key"].split("|")[1]
        m = re.fullmatch(r"(.+)__draw(\d)", tag)
        gens.append(res.arm2gen.get(m.group(1)) if m else None)
        if not m and tag not in side:
            side[tag] = i                      # a side arm (thinking off): judged in turn, used by no claim
        exp, u = res.unit(x["key"], {"question_id": x["question_id"], "answer_chars": len(x["answer"])})
        keys.append(x["key"])
        units.append(u if exp == "rep" else None)
    first = {}
    for i, g in enumerate(gens):
        if g is not None and g not in first:
            first[g] = i
    out = {"n_items": len(items), "first_item_of_generator": dict(sorted(first.items(), key=lambda kv: kv[1])),
           "first_item_of_side_arm": side, "units_in_order": units, "changed_questions_left_out": sorted(changed)}
    if studio_rows is not None:
        pos = {k: i for i, k in enumerate(keys)}
        idx = sorted(pos[r["key"]] for r in studio_rows if r.get("key") in pos)
        out["studio"] = {"rows": len(studio_rows), "distinct_items": len(set(idx)),
                         "furthest_item": idx[-1] if idx else None,
                         "contiguous_from_start": next((i for i, j in enumerate(sorted(set(idx))) if i != j),
                                                       len(set(idx))),
                         "items_to_first_gemini": (first.get(REF, 0) - (idx[-1] + 1)) if idx else first.get(REF)}
    return out


def decide(c: dict, pub: dict, m1: dict, dv: dict, coverage: float) -> tuple[str, dict]:
    """The verdict (docstring, Verdict) and its parts. Below full coverage the reference for (d) is (c), the same
    answers on the original scores; at full coverage it is the published value."""
    v1m = c["v"](m1, pub) if m1.get("ok") else None
    v_abs = c["v"](dv, pub) if dv.get("ok") else None
    v_rel = c["v"](dv, m1) if (m1.get("ok") and dv.get("ok") and v1m != "reverses") else None
    parts = {"original_matched_against_published": v1m, "new_against_original_matched": v_rel,
             "new_against_published": v_abs}
    if coverage >= 1.0:
        return (v_abs or NED), parts
    if v1m is None or v_rel is None or v1m == "reverses":
        return NED, parts
    if v1m == "weakens" and v_rel != "reverses":
        return NED, parts
    if c.get("null") and v_rel == "holds" and coverage < 0.8:
        return NED, parts
    if c.get("every") and v_rel == "holds" and not c["every"](dv):
        return NED, parts                        # a claim for every generator holds only once every one is in
    return v_rel, parts


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if hasattr(o, "item"):
        o = o.item()
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return o


def gate(d7: set) -> tuple[dict, dict, dict, dict, list, int]:
    """The original tables, the no-judge claims, every claim's published result, and the gate's failures."""
    ORIG = original_tables()
    ORIG7 = drop_d7(ORIG, d7)
    nj = {c["id"]: c["nojudge"](d7) for c in CLAIMS if c.get("nojudge")}
    pubs, fails, n = {}, [], 0
    for c in CLAIMS:
        print(f"  gate {c['id']} ...", flush=True)
        pub = nj[c["id"]]["published"] if c["id"] in nj else c["f"](ORIG)
        for name, good in c["gate"](pub):
            n += 1
            if not good:
                fails.append(f"{c['id']} {name}")
        pubs[c["id"]] = pub
    return ORIG, ORIG7, nj, pubs, fails, n


def sample_text(r: dict) -> str:
    s = []
    if r.get("n_questions") is not None:
        s.append(f"{r['n_questions']} questions")
    g = r.get("generators")
    if g:
        s.append("generators " + ", ".join(f"{k} {v:,}" for k, v in g.items()))
    return "; ".join(s)


def script_sha() -> str:
    return sha256(Path(__file__).resolve())


# ── calibration: independent score sets standing in for the new judge ────────────────────────────────

CAL_LEVELS = (0.05, 0.15, 0.40)
CAL_DRAWS = 20


def _keep_random(M: dict, p: float, seed: str) -> dict:
    return {e: {k for k in t if int(hashlib.sha256(f"{seed}|{e}|{k!r}".encode()).hexdigest()[:12], 16)
                < p * 16 ** 12} for e, t in M.items()}


def _keep_keyorder(M: dict, p: float, order: list) -> dict:
    """The first share p of the S141 replication rows in S373's key order (the Mac Studio's order); the published
    one-draw replication (laptop shards, random by key hash) at random."""
    keep = _keep_random(M, p, "keyorder")
    rep = M["rep"]
    seq = [u for u in order if u is not None and u in rep]
    s141 = set(seq)
    keep["rep"] = {k for k in keep["rep"] if k not in s141} | set(seq[:math.ceil(p * len(seq))])
    return keep


def _sub(M: dict, keep: dict) -> dict:
    return {e: {k: v for k, v in t.items() if k in keep[e]} for e, t in M.items()}


def _classify(v: str, truth: str) -> str:
    if v == NED:
        return "not enough data"
    if truth not in SEVERITY:
        return "untestable"
    if v == truth:
        return "agrees"
    return "false alarm" if SEVERITY[v] > SEVERITY[truth] else "miss"


def calibrate(ORIG7: dict, d7: set, order: list, res: Resolver, pubs: dict) -> dict:
    """ORIG7: column (b'), the original tables after D7 and drop_q51 (main passes ORIG7Q)."""
    by_id = {c["id"]: c for c in CLAIMS}
    standins = []
    sa = {e: {} for e in ORIG7}
    sa["rep"] = {k: {**v, "main": v["second"], "second": None} for k, v in ORIG7["rep"].items()}
    standins.append(("A", "original gpt-oss:120b scores as the main judge (independent judge, every replication answer)",
                     sa, ["R1", "R2", "R3"], True))
    sw = {e: {} for e in ORIG7}
    sw["rep"] = {k: {**v, "main": v["second"], "second": v["main"]} for k, v in ORIG7["rep"].items()}
    standins.append(("A'", "the two original judges swapped (a planted reversal of J1)", sw, ["J1"], True))
    led = read_ledger(QWEN821, "laptop", str(QWEN821.relative_to(ROOT)))
    best_q, st_q, conf_q = merge([led], None, d7)
    sb, drop_b, _ten_b = new_tables(best_q, {}, res, ten_label="set aside (stand-in, no group)")   # F10: its rows on
    # the ten are kept out of every table, as in the main run, and no group is reported for a stand-in
    sb["rep"] = {}
    standins.append(("B", "qwen3-coder re-judge of 8 October on ground truth v2.1 (S373_qwen_paper_qa.jsonl: 74 "
                          "questions, complete answers, every paper_qa table but the replication)", sb,
                     ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "S1", "S2", "S3", "P1", "P2", "P3",
                      "P4", "N1", "N2"], False))
    out = {"levels": list(CAL_LEVELS), "draws": CAL_DRAWS, "standins": []}
    for name, desc, S, ids, keyorder in standins:
        U1, US, _bad = match(ORIG7, S)
        print(f"calibration {name}: {sum(len(t) for t in U1.values()):,} answers", flush=True)
        rows = []
        for cid in ids:
            c = by_id[cid]
            m1u, dvu = c["f"](U1), c["f"](US)
            if not (m1u.get("ok") and dvu.get("ok")):
                truth = "not computable on the stand-in"
            elif c["v"](m1u, pubs[cid]) != "holds":     # the original on these answers does not give the claim
                truth = f"untestable (original here: {c['v'](m1u, pubs[cid])})"
            else:
                truth = decide(c, m1u, m1u, dvu, 1.0)[0]
            rows.append({"id": cid, "units": m1u.get("units", 0), "truth": truth,
                         "original_on_standin": c["h"](m1u) if m1u.get("ok") else "too few",
                         "standin_all": c["h"](dvu) if dvu.get("ok") else "too few",
                         "runs": {}, "_ref": m1u})
        modes = [("random", lambda p, j: _keep_random(U1, p, f"cal{j}"), CAL_DRAWS)]
        if keyorder:
            modes.append(("key order", lambda p, j: _keep_keyorder(U1, p, order), 1))
        for mode, keep_of, draws in modes:
            for p in CAL_LEVELS:
                tally = {r["id"]: Counter() for r in rows}
                verdicts = {r["id"]: Counter() for r in rows}
                for j in range(draws):
                    keep = keep_of(p, j)
                    A, B = _sub(U1, keep), _sub(US, keep)
                    for r in rows:
                        c = by_id[r["id"]]
                        m1, dv = c["f"](A), c["f"](B)
                        cov = m1["units"] / r["units"] if r["units"] else 0.0
                        v = decide(c, r["_ref"], m1, dv, min(cov, 0.999))[0] if r["_ref"].get("ok") else NED
                        verdicts[r["id"]][v] += 1
                        tally[r["id"]][_classify(v, r["truth"])] += 1
                for r in rows:
                    r["runs"][f"{mode} {int(100 * p)}%"] = {"draws": draws, "verdicts": dict(verdicts[r["id"]]),
                                                             "classified": dict(tally[r["id"]])}
                print(f"  {name} {mode} {int(100 * p)}% done", flush=True)
        for r in rows:
            r.pop("_ref")
        out["standins"].append({"name": name, "description": desc, "claims": rows,
                                "answers": {e: len(t) for e, t in U1.items() if t},
                                **({"merge": st_q, "not_mapped": dict(drop_b), "conflicts": len(conf_q)}
                                   if name == "B" else {})})
    tot = Counter()
    for s in out["standins"]:
        if s["name"] == "A'":
            continue
        for r in s["claims"]:
            if r["truth"] not in SEVERITY:
                continue
            for k, run in r["runs"].items():
                for cls, n in run["classified"].items():
                    tot[(k, cls)] += n
    out["summary_null_standins"] = {f"{k} | {cls}": n for (k, cls), n in sorted(tot.items())}
    return out


def calibration_markdown(C: dict) -> str:
    pv = C["_provenance"]
    L = ["# S393 calibration: do provisional verdicts on partial data agree with the verdict on all the data?", "",
         f"- script: scripts/S393_early_claims.py --calibrate; sha256 {pv['script_sha256'][:12]}; generated "
         f"{pv['generated']}; runtime {pv['runtime_s']} s",
         f"- {C['draws']} random draws at each of {', '.join(f'{int(100 * p)}%' for p in C['levels'])} of each "
         "stand-in's answers (each answer kept with that probability, as the laptop shards pick answers by key hash); "
         "for the replication also the first share in S373's key order (one draw: the Mac Studio's order)",
         "- truth: the verdict the same code gives with the stand-in's scores on all its answers. A provisional "
         "verdict more severe than the truth is a false alarm, less severe a miss.",
         "- the reference for the stand-in's verdicts is the original scores on the stand-in's own answers, so the "
         "truth measures the stand-in against the original, not the stand-in's coverage. Where the original scores on "
         "the stand-in's answers do not themselves give the claim (its rule against the published value is not "
         "'holds'), the claim is untestable on that stand-in and left out of the summary", ""]
    for s in C["standins"]:
        L += [f"## Stand-in {s['name']}: {s['description']}", "",
              f"Answers per table: {json.dumps(s['answers'])}.", ""]
        runs = list(s["claims"][0]["runs"]) if s["claims"] else []
        L += ["| Claim | Units | Truth (all stand-in answers) | " + " | ".join(runs) + " |",
              "|---|---:|---|" + "---|" * len(runs)]
        for r in s["claims"]:
            cells = []
            for k in runs:
                cl = r["runs"][k]["classified"]
                bits = [f"{cl.get(x, 0)} {x}" for x in ("agrees", "not enough data", "false alarm", "miss", "untestable")
                        if cl.get(x)]
                cells.append(", ".join(bits))
            L.append(f"| {r['id']} | {r['units']:,} | {r['truth']} | " + " | ".join(cells) + " |")
        L += ["", "Values on all the stand-in's answers (original, then stand-in):", ""]
        for r in s["claims"]:
            L.append(f"- {r['id']}: original {r['original_on_standin']}; stand-in {r['standin_all']}")
        L.append("")
    L += ["## Summary over stand-ins A and B, testable claims only (A' is a planted reversal, left out)", "",
          "| Sampling | Class | Count |", "|---|---|---:|"]
    for k, n in C["summary_null_standins"].items():
        a, b = k.split(" | ")
        L.append(f"| {a} | {b} | {n} |")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-remote", action="store_true", help="read this machine's ledgers only")
    ap.add_argument("--calibrate", action="store_true", help="run the calibration with stand-in judges and exit")
    a = ap.parse_args()
    t0 = time.time()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    v2 = {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}
    hashes = {q: S373.key_hash(q, v2) for q in v2}
    as_v1 = json.loads(AS_V1.read_text())
    key_sha = sha256(S373.KEY)
    src = f"source_{KV.replace('.', '')}_sha256"         # the field S381 writes for this key version
    if as_v1.get(src) != key_sha:
        raise SystemExit(f"FATAL: {AS_V1.name} was not built from the current {S373.KEY.name} (its {src})")
    d7 = set(as_v1["dropped_d7"])

    # ── gate: every claim's published values from the original scores ─────────────────────────
    ORIG, ORIG7, nj, pubs, fails, nchecks = gate(d7)
    if fails:
        print("FATAL: the published values do not come back from the original scores:")
        for f in fails:
            print("  " + f)
        return 1
    print(f"gate passed: every claim reproduces its published values ({nchecks} checks)", flush=True)
    ORIG7Q = drop_q51(ORIG7)                     # column (b'): the ten out of the refusal units (Q51, D5)
    res = Resolver()

    if a.calibrate:
        order = rep_order(res, None)["units_in_order"]
        C = calibrate(ORIG7Q, d7, order, res, pubs)
        C["_provenance"] = {"script": "scripts/S393_early_claims.py --calibrate", "script_sha256": script_sha(),
                            "generated": stamp, "runtime_s": round(time.time() - t0, 1),
                            "inputs": [{"file": shown(p), "sha256": sha256(p)} for p in
                                       (QWEN821, T141, T320, S373.KEY, AS_V1)],
                            "gate": f"the {nchecks} checks of the main run passed first"}
        CAL_JSON.write_text(json.dumps(clean(C), indent=1, ensure_ascii=False) + "\n")
        CAL_MD.write_text(calibration_markdown(clean(C)) + "\n")
        print(calibration_markdown(clean(C)))
        return 0

    tmp = Path(tempfile.mkdtemp(prefix="s393_"))
    try:
        main_files, notes = ledgers("devstral", not a.no_remote, tmp)
        second_files, notes2 = ledgers("gptoss", not a.no_remote, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    best_main, st_main, conf_main = merge(main_files, hashes, d7)
    best_second, st_second, conf_second = merge(second_files, hashes, d7)
    by_label = Counter(k.split("|")[0] for k in best_main)
    print(f"devstral: {len(best_main):,} scored answers on the current key from {len(main_files)} ledgers; "
          f"gpt-oss: {len(best_second):,}", flush=True)

    NEW, drop, G = new_tables(best_main, best_second, res)
    M1, MDV, chars_bad = match(ORIG7Q, NEW)
    studio_rep = [r for f in main_files if f["machine"] == "studio"
                  and production(Path(f["file"]).name, "devstral") == "replication5" for r in f["rows"]]
    order = rep_order(res, studio_rep if any(f["machine"] == "studio" for f in main_files) else None)
    both_orig = {k for k, v in ORIG7["rep"].items() if v.get("main") is not None and v.get("second") is not None}
    j1_ceiling = sum(1 for k in both_orig if (NEW["rep"].get(k) or {}).get("second") is not None)

    out_claims = []
    for c in CLAIMS:
        print(f"  {c['id']} ...", flush=True)
        pub = pubs[c["id"]]
        if c["id"] in nj:
            r7, m1, dv = nj[c["id"]]["d7"], nj[c["id"]]["d7"], nj[c["id"]]["v22"]
            r7q = r7       # D1's records hold no out-of-domain question; E11 reads the deposit's answerable rows only
        else:
            r7, r7q, m1, dv = c["f"](ORIG7), c["f"](ORIG7Q), c["f"](M1), c["f"](MDV)
        cov = (m1["units"] / r7q["units"]) if r7q.get("units") else 0.0
        v7 = c["v"](r7, pub) if r7.get("ok") else None
        v7q = c["v"](r7q, pub) if r7q.get("ok") else None
        same_q51 = clean(r7q) == clean(r7)
        verdict, parts = decide(c, pub, m1, dv, cov)
        stale = dv.get("stale")                  # a no-judge claim whose file was scored on another key
        rec = {"id": c["id"], "experiment": c["exp"], "where": c["where"], "claim": c["claim"],
               "statistic": c["statistic"], "rule": c["rule"], "no_judge": bool(c.get("nojudge")),
               "coverage": {"units_matched": m1.get("units", 0), "units_needed": r7q.get("units", 0), "share": cov},
               "sample": sample_text(m1),
               "published": {"value": c["h"](pub), "result": pub},
               "original_d7": {"value": c["h"](r7), "verdict": v7, "result": r7},
               "original_d7_q51": {"value": c["h"](r7q), "verdict": v7q, "same_as_d7": same_q51,
                                   "result": None if same_q51 else r7q},
               "original_matched": {"value": c["h"](m1), "verdict": parts["original_matched_against_published"],
                                    "result": m1},
               "devstral_v22_matched": {"value": stale or c["h"](dv), "verdict_against_original_matched":
                                        parts["new_against_original_matched"],
                                        "verdict_against_published": parts["new_against_published"], "result": dv},
               "verdict": verdict, "verdict_reason": stale, "provisional": cov < 1.0,
               "d7_alone": v7 if v7 not in (None, "holds") else None,
               "d7_q51_alone": v7q if (not same_q51 and v7q not in (None, "holds")) else None}
        if c["id"] in TEN_CLAIMS:
            rec["ten_group"] = ten_group(ORIG7, G, *TEN_CLAIMS[c["id"]])
        if c["id"] == "J1":
            rec["coverage"]["ceiling_until_item_12"] = {"units": j1_ceiling,
                                                        "share": j1_ceiling / r7["units"] if r7.get("units") else 0.0}
        out_claims.append(rec)

    cal = None
    if CAL_JSON.exists():
        C = json.loads(CAL_JSON.read_text())
        cal = {"file": shown(CAL_JSON), "sha256": sha256(CAL_JSON), "generated": C["_provenance"]["generated"],
               "current": C["_provenance"]["script_sha256"] == script_sha(),
               "summary_null_standins": C["summary_null_standins"]}

    inputs = [S373.KEY, AS_V1, T141, T320, S320J, S67J, S383C, S382C, S04B, S19S, RECOMPUTE / "S21_rejudge_raw.jsonl",
              RECOMPUTE / "S11_exp05_tidy.csv", RECOMPUTE / "S11_exp05_tidy_rejudged.csv",
              RESULTS / "exp04_generation_latest.json", RESULTS / "exp05_scaling_latest.json",
              RESULTS / "exp06_orchestration_ablation_latest.json", RESULTS / "analysis_naive_baseline_latest.json",
              DETERM, RESULTS / "exp09_depth_sweep_gemini-3-flash-preview_latest.json",
              RESULTS / "exp09_depth_sweep_gemini-3-flash-preview_merged.json"]
    order_out = {k: v for k, v in order.items() if k != "units_in_order"}
    payload = {
        "_provenance": {
            "script": "scripts/S393_early_claims.py", "script_sha256": script_sha(), "generated": stamp,
            "runtime_s": round(time.time() - t0, 1),
            "key": {"file": str(S373.KEY.relative_to(ROOT)), "sha256": key_sha, "version": KV}, "d7": sorted(d7),
            "q51": sorted(TEN),
            "inputs": [{"file": shown(p), "sha256": sha256(p)} for p in inputs],
            "ledgers_main": [{k: v for k, v in f.items() if k != "rows"} for f in main_files],
            "ledgers_second": [{k: v for k, v in f.items() if k != "rows"} for f in second_files],
            "notes": notes + notes2, "remote": not a.no_remote,
            "gate": f"every claim's published values reproduced from the original scores ({nchecks} checks) before "
                    "anything was written",
        },
        "merge": {"devstral": st_main, "gptoss": st_second, "conflicts_devstral": conf_main[:50],
                  "conflicts_gptoss": conf_second[:50], "n_conflicts": [len(conf_main), len(conf_second)],
                  "scored_by_source_label": dict(by_label), "not_mapped": dict(drop),
                  "matched_answers_dropped_for_length": dict(chars_bad),
                  "matched_answers": {e: len(t) for e, t in M1.items()},
                  "original_answers_after_d7": {e: len(t) for e, t in ORIG7.items()},
                  "original_answers_after_d7_q51": {e: len(t) for e, t in ORIG7Q.items()}},
        "replication_order": order_out,
        "claims": out_claims,
        "answer_shift": answer_shift(M1, MDV),
        "calibration": cal,
    }
    OUT_JSON.write_text(json.dumps(clean(payload), indent=1, ensure_ascii=False) + "\n")
    OUT_MD.write_text(markdown(clean(payload)) + "\n")
    print(markdown(clean(payload)))
    return 0


def markdown(P: dict) -> str:
    pv, mg = P["_provenance"], P["merge"]
    cl = P["claims"]
    vc = Counter(c["verdict"] for c in cl)
    led = pv["ledgers_main"]
    L = [f"# S393, early claims check: do the {KV} key and the devstral judge reverse a claim?", "",
         f"- script: scripts/S393_early_claims.py (sha256 {pv['script_sha256'][:12]}); generated {pv['generated']}; "
         f"runtime {pv['runtime_s']} s",
         f"- key: {pv['key']['file']} sha256 {pv['key']['sha256'][:12]}; D7 drops {', '.join(pv['d7'])}",
         f"- Q51 and D5: the ten false-premise questions ({pv['q51'][0]} to {pv['q51'][-1]}, answer_type refutation) "
         "are out of every claim's units from the Q51 column on, and E6 and P4 report them as their own group",
         f"- new scores: devstral-small-2:24b, {mg['devstral'].get('scored answers', 0):,} scored answers on the current "
         f"key from {len(led)} ledgers ({', '.join(f['file'] + ' ' + f['sha256'][:10] + ' (' + format(f['rows_read'], ',') + ' rows)' for f in led)}); "
         f"gpt-oss:120b (J1 and the answer-shift table only), {mg['gptoss'].get('scored answers', 0):,}",
         f"- {pv['gate']}, including S320 and S67 in R and S04b's concept recall"]
    for n in pv["notes"]:
        L.append(f"- note: {n}")
    L.append("- read: this machine's production ledgers and the Mac Studio's (scp, read-only); a shard still running on "
             "the Beelink counts once S380 fetches it" if pv.get("remote", True) else
             "- read: this machine's production ledgers only (--no-remote)")
    L += ["", "**PARTIAL DATA.** Every verdict below 100% coverage rests only on the answers scored on the current key "
          "and is provisional; its coverage and the questions (and, for the replication, "
          "the generators) behind it are printed on its line. \"not enough data\" means the rows judged so far cannot "
          "show the claim either way. D1 and E11 use no judge and are complete, unless their line says the file was "
          "scored on another key.", "",
          f"Verdicts: holds {vc.get('holds', 0)}, weakens {vc.get('weakens', 0)}, reverses {vc.get('reverses', 0)}, "
          f"not enough data {vc.get(NED, 0)} (of {len(cl)} claims).", "",
          "| ID | Claim | Published (original, all rows) | Original after D7 [rule] | (b') Original after D7 and Q51 [rule] | "
          "Coverage (matched of needed; sample) | "
          f"Original, matched rows [rule vs published] | devstral {KV}, matched rows [rule vs original matched; vs "
          "published] | Verdict |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in cl:
        cv = c["coverage"]
        dvm = c["devstral_v22_matched"]
        cov = f"{cv['units_matched']:,} of {cv['units_needed']:,} ({100 * cv['share']:.1f}%)"
        if c["sample"]:
            cov += f"; {c['sample']}"
        if "ceiling_until_item_12" in cv:
            ce = cv["ceiling_until_item_12"]
            cov += f"; ceiling until item 12: {ce['units']:,} ({100 * ce['share']:.1f}%)"
        tail = ""
        if c["provisional"]:
            tail = f" (provisional, {100 * cv['share']:.1f}% coverage)"
        elif c.get("verdict_reason"):
            tail = f": {c['verdict_reason']}"
        elif c["no_judge"]:
            tail = " (complete, no judge)"
        if c["d7_alone"]:
            tail += f"; D7 alone: {c['d7_alone']}"
        if c["d7_q51_alone"]:
            tail += f"; D7 and Q51: {c['d7_q51_alone']}"
        q51 = c["original_d7_q51"]
        q51_cell = "as D7" if q51["same_as_d7"] else f"{q51['value']} [{q51['verdict'] or 'n/a'}]"
        L.append(f"| {c['id']} | {c['claim']} | {c['published']['value']} | {c['original_d7']['value']} "
                 f"[{c['original_d7']['verdict'] or 'n/a'}] | {q51_cell} | {cov} | {c['original_matched']['value']} "
                 f"[{c['original_matched']['verdict'] or 'too few'}] | {dvm['value']} "
                 f"[{dvm['verdict_against_original_matched'] or 'n/a'}; {dvm['verdict_against_published'] or 'too few'}] "
                 f"| **{c['verdict']}**{tail} |")
    L += ["", "Brackets give a rule applied to one column. Below full coverage the verdict is the rule on the devstral "
          "column with the original matched column as reference (first bracket of the devstral column), guarded by "
          "the original matched column's own verdict; the second bracket, against the published value, is shown and "
          "not used, since a matched subset need not show the published effect. At full coverage the verdict is the "
          "rule against the published value. Coverage counts against the Q51 column, which is the D7 column except "
          "where a claim's units held the ten (E6 and P4).", ""]
    tg = [c for c in cl if c.get("ten_group")]
    if tg:
        L += ["## The ten false-premise questions, their own group (Q51, D5)", "",
              "They have a correct answer in the papers, the refutation, and are out of the refusal units above. "
              "Original: the share refused (refusal accuracy 3 or more, the published scoring, decline prompt), all "
              f"their rows. devstral {KV}: the share passed (correctness 3 or more against the refutation, answerable "
              "prompt), on the answers scored so far whose length matches the original's; the last column, the share "
              "with faithfulness 5 among those that carry a faithfulness score. No rule decides on the group.", "",
              "| Claim | Configuration | Original: refused | New: passed against the refutation | New: faithfulness 5/5 |",
              "|---|---|---:|---:|---:|"]
        for c in tg:
            g = c["ten_group"]
            for cfg, x in g["by_config"].items():
                L.append(f"| {c['id']} | {cfg} | {x['original_refused']} of {x['original_n']} | "
                         f"{x['new_passed']} of {x['new_n']} | {x['new_faith_5']} of {x['new_faith_n']} |")
        L.append("")
        for c in tg:
            g = c["ten_group"]
            L.append(f"- {c['id']}: {g['units_new']:,} of {g['units_original']:,} answers on the ten scored "
                     f"({100 * g['coverage']:.1f}%); dropped for length {g['new_dropped_for_length']}, scored without a "
                     f"correctness score {g['new_without_correctness']}")
        L.append("")
    ro = P["replication_order"]
    fi = ro["first_item_of_generator"]
    L += ["## Where the Mac Studio's replication ledger stands", "",
          f"S373 sorts the {ro['n_items']:,} replication5 items by key (left out: the questions whose wording changed, "
          f"{', '.join(ro['changed_questions_left_out'])}) and judges them in that order. First item of each generator's "
          "drawn arms, the rows the claims use (0-based): " + "; ".join(f"{g} {i:,}" for g, i in fi.items()) + ". "
          "Side arms, judged in turn and used by no claim: "
          + "; ".join(f"{t} from {i:,}" for t, i in ro["first_item_of_side_arm"].items()) + "."]
    if ro.get("studio"):
        s = ro["studio"]
        L.append(f"The Mac Studio's ledger holds {s['rows']:,} rows on {s['distinct_items']:,} distinct items, contiguous "
                 f"from item 0 to item {s['contiguous_from_start'] - 1:,}, the furthest at item {s['furthest_item']:,}: "
                 f"{s['items_to_first_gemini']:,} items before the first {REF} item a claim uses. R1 and R2 need "
                 f"{REF} rows.")
    else:
        L.append("The Mac Studio's ledger was not read in this run.")
    L += ["", "## How far individual matched answers move", "",
          "The same answers under the original scores (qwen3-coder:30b, v1 key) and the new ones (devstral-small-2:24b, "
          f"{KV} key); exact McNemar on the paired indicator. Not a claim: it shows whether a shift on the matched rows "
          "is beyond noise, and on which sample.", "",
          "| Table | Indicator | Matched answers | Questions | Generators | Original | New | Original only | New only | McNemar P |",
          "|---|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for x in P["answer_shift"]:
        if not x["n"]:
            L.append(f"| {x['table']} | {x['indicator']} | 0 | | | | | | | |")
        else:
            gens = ", ".join(f"{g} {n:,}" for g, n in (x.get("generators") or {}).items())
            L.append(f"| {x['table']} | {x['indicator']} | {x['n']:,} | {x['n_questions']} | {gens} | "
                     f"{pct(x['original'])} | {pct(x['new'])} | {x['original_only']} | {x['new_only']} | {pfmt(x['P'])} |")
    L += ["", "## Calibration", ""]
    cal = P.get("calibration")
    if not cal:
        L.append("Not run (uv run python scripts/S393_early_claims.py --calibrate).")
    else:
        L.append(f"{cal['file']} (sha256 {cal['sha256'][:12]}, generated {cal['generated']})"
                 f"{'' if cal['current'] else ': STALE, the script has changed since; rerun --calibrate'}. "
                 "Provisional verdicts on stand-ins A and B (independent score sets), testable claims only, against the "
                 "verdict the same stand-in gives on all its answers:")
        L += ["", "| Sampling | Class | Count |", "|---|---|---:|"]
        for k, n in cal["summary_null_standins"].items():
            a, b = k.split(" | ")
            L.append(f"| {a} | {b} | {n} |")
    L += ["", "## Where each claim is printed, its statistic and its rule", ""]
    for c in cl:
        L += [f"**{c['id']}** ({c['experiment']}). {c['where']}.", f"- statistic: {c['statistic']}",
              f"- rule: {c['rule']}", ""]
    L += ["## The rows behind the new scores", "",
          "| Source label | devstral answers scored on the current key |", "|---|---:|"]
    for k, v in sorted(mg["scored_by_source_label"].items()):
        L.append(f"| {k} | {v:,} |")
    L += ["", f"Merge, devstral: {json.dumps(mg['devstral'])}. Conflicting scores on one key: {mg['n_conflicts'][0]} "
          f"(devstral), {mg['n_conflicts'][1]} (gpt-oss).",
          f"Not mapped to a claim's table: {json.dumps(mg['not_mapped']) or 'none'}.",
          f"Matched answers dropped because the two answer lengths differ: {json.dumps(mg['matched_answers_dropped_for_length'])}.",
          f"Matched answers per table: {json.dumps(mg['matched_answers'])}; original answers after D7: "
          f"{json.dumps(mg['original_answers_after_d7'])}; after D7 and Q51: "
          f"{json.dumps(mg['original_answers_after_d7_q51'])}.", "",
          "## What this check does not cover", "",
          "- The second judge's verdicts in the replication (MT-33). R1 to R3 are computed on the main judge's scores "
          f"only; gpt-oss:120b's rows on {KV} enter J1 and the answer-shift table only, and J1's line gives how many of "
          "its answers have one (its ceiling).",
          "- The judge-evidence experiment (S18: 81.7% against 82.5%, 26.1%): S18e re-runs it with devstral "
          "(findings/recompute/S18e_results.md), and this script does not read it.",
          "- The three-signal ranking (Kendall's W, the shared component, the baseline metrics against it, MT-61 to "
          f"MT-66) and MiniCheck against the key: they need S382, S384 and S30 on {KV} joined to the devstral exp04 scores.",
          "- The depth curves of Fig. 3b,c and their fits (MT-22 to MT-24): four of nine are judge scores, three of them "
          "cannot be re-judged (F1, Q10).",
          f"- Concept-recall levels printed elsewhere (worklist F6: every level moves on {KV}); E11 covers only the "
          "ranking claim of MT-07, D1 only the saturation shares.",
          "- Generator selection, the synthesizer benchmark and the reanalysis arms (S141 small-model arm, S314 "
          "verified-pass rerun, S357 Gemini arm): their sources (selection_synth, reanalysis) are judged, and no claim "
          "here reads them.",
          "- The supervisor correlation (MT-41, Q5) and RAGAS (MT-67 to MT-74, item 16).",
          "- Other judge-based claims that S373 rows could re-check but this script does not: the false-premise "
          "counts (MT-18, MT-19, MT-87, printed by S296), the distractor-noise claims (MT-29, MT-30, printed by S66; "
          "the exp05 out-of-domain rows are not read, so MT-30 cannot be computed here), refusal validity (MT-60), "
          "the refusal ranking of MT-16 (E6 gates it but no rule decides it), and MT-57, MT-59, MT-95 and MT-96."]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
