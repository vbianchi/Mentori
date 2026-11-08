#!/usr/bin/env python3
"""S388 - the S373 re-judge ledgers merged under the current answer key (S373.KEY) and split by experiment.

The key is ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45), v2.2 before.

WHY. S373 writes one ledger per judge, source and shard (S380 cuts the main judge's run into shards
spread over three machines), and every row records the per-question key hash it was judged under.
The resubmission ships the judged answers per experiment (Valerio, 9 October: "the results of the
~50,000 evaluations divided by experiment"), so the rows that count must be picked out of those
ledgers by one rule, checked against the answers they claim to score, and filed under the experiment
they belong to. D3 (9 October): the merged ledgers ship; the shard and run ledgers stay in the
repository, hashed here.

HOW. Imports, never retypes: S373.KEY, S373.AS_V1, S373.key_hash, S373.SOURCES and S373.JUDGES. D7 (the
six questions whose text changed) comes from S373.AS_V1 "dropped_d7" (ground_truth_v2_4_as_v1.json since
11 October), whose source_v<version>_sha256 field (S381's name for it: source_v23_sha256 for v2.3, the
version read from S373.KEY's "version" field) must be the key's sha256. Reports name that version;
the output names keep _v22 so that downstream paths (S08, S347, S389) hold.
  inputs      production ledgers S373_<judge>_<source>[_shard<k>of<n>].jsonl. Side files (_test50,
              _probeLaptop, any other _<out>) are never merged; their current-key rows are compared
              with the production rows on the same key and the agreement is reported
  per row, in order
    1  an exp04-form key (exp04|...) is dropped: the same answers carry the label "Generation
       strategies (exp04)" under another key. A production exp04-source ledger holding rows under
       the current key fails the run
    2  a D7 question is dropped
    3  a key_hash other than the current one is dropped as "stale key"
    4  a key not in the expected set of the ledger's source fails the run
    5  (question_id, answer_chars) must equal the current reader's item for that key, so a row index
       that now names another answer fails the run. One exception, named in CHANGED_ANSWERS: a result
       file whose answers the reader changed after rows were judged (the S374 fix of 9 October 22:45);
       its rows that fail 4 or 5 are dropped as "answer changed since judged" and count as missing
    6  duplicates on (judge, key): identical scores collapse to the earliest `at`; two scored rows
       with different scores are a conflict, listed, exit 1. A scored row supersedes an unscored one
       (counted); two unscored rows collapse to the earliest
  growing files: each ledger is read once; a final line without a newline is skipped and counted
  as "being written"
  machine per file, never per port (11434 is used on the Mac Studio and on the laptop): shard
  ledgers from the S380 status files and the "<machine> shard <source>:<k> done" lines of the S380
  run logs; unsharded ledgers from the table UNSHARDED below, with its reasons; anything else is
  "unattributed"
  reproduce before writing: the expected answer counts per source and per label, and the
  current-key row counts of the two ledgers surveyed on 9 October (pinned by sha256), must come
  out before anything is written, and the replication2 source (the two-model replication alone, read
  for gpt-oss's ledger S373_gptoss_replication2.jsonl, Q57) must equal paper_qa_rest's answers of that
  label, key by key. The survey counted rows under the v2.2 key hashes; the gate
  counts under S373.KEY against the count pinned for that key's version. Both ledgers gave the same
  counts under v2.3 (6,557 and 3,139: none of their current-key rows is on a question v2.3 changed);
  under v2.4 (Q50, 11 October) the qwen ledger gave 5,879 (678 of its rows are on 8 of the 25 questions
  v2.4 changed), and gives 5,507 since Q51 (11 October 13:30): its 372 rows on the ten false-premise questions
  OOD_041 to OOD_050 were judged with the decline prompt, and their key_hash now carries the Q51 marker (D5,
  O38). The gpt-oss ledger was restarted on Ollama 0.40.2 (Q32) and no longer has the surveyed
  sha256, so its pin does not apply and has no v2.4 count
Outputs, rows verbatim (the input lines byte for byte, sorted by key):
  <out>/S388_rejudge_v22/<slug>/<judge>.jsonl     slug = one of the twelve experiments, or reanalysis_arms
  <out>/S388_rejudge_v22.json and .md             provenance and coverage

    uv run python scripts/S388_merge_rejudge_v22.py [--out DIR] [--final]
Coverage counts SCORED keys: an expected answer is covered when its chosen row has status ok or
ok_output_limit. A row with any other status (error, out_of_context, output_limit, ...) is counted as
"judged without a score", never as covered, and listed by key.
--final also requires: every expected key of every experiment and arm has a scored main-judge row
(the keys without one are listed as failures, with the status of their row or "no row"), none of its
rows is unattributed, and every S380 status file records `finished`.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import S373_rejudge_v2 as S373  # noqa: E402
from machine import RECOMPUTE, ROOT  # noqa: E402

AS_V1 = S373.AS_V1   # the judge's key in the v1 format: ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45) (S381 --key 2.4)
OK = ("ok", "ok_output_limit")
MAIN_JUDGE = "devstral"            # the main judge from 9 October (S373.JUDGES, O2)
MAIN_SOURCES = ("paper_qa_rest", "replication5", "selection_synth", "reanalysis")

# The S374 label of a key (its first field) and the experiment folder it is filed under. Experiments
# 02 (retrieval optimisation), 09 (distiller intervention) and 10 (code generation) have no label:
# they are not scored against the answer key (S375).
LABEL_TO_SLUG = {
    "Generator selection (exp00 rlm_models)": "01_model_selection",
    "Generation strategies (exp04)": "03_generation_strategies",
    "Retrieval depth (exp09)": "04_retrieval_depth",
    "Corpus scaling (exp05)": "05_corpus_scaling",
    "Orchestration (exp06)": "06_pipeline_ablation",
    "Naive RAG baseline": "07_naive_rag_baseline",
    "Component benchmark: synthesizer (exp07)": "08_component_benchmarks",
    "Strategy replication (published)": "11_strategy_replication_two_models",
    "S141 campaign (strategy replication, multi-generator)": "12_strategy_replication_five_models",
    "S141 mini arm (step 4.3, s50)": "reanalysis_arms",
    "S141 timing (step 4.4)": "reanalysis_arms",
    "S314 verified_pass rerun (exp05 indexes)": "reanalysis_arms",
    "S357 Gemini paired arm": "reanalysis_arms",
}
SLUGS = ["01_model_selection", "02_retrieval_optimisation", "03_generation_strategies", "04_retrieval_depth",
         "05_corpus_scaling", "06_pipeline_ablation", "07_naive_rag_baseline", "08_component_benchmarks",
         "09_distiller_intervention", "10_code_generation", "11_strategy_replication_two_models",
         "12_strategy_replication_five_models", "reanalysis_arms"]

# Known numbers, reproduced before anything is written (survey of 9 October, 22:10). The S374 reader fix of
# 22:45 (aa64ff2: the llama3:8b depth file stores each answer as a GenerationResult repr; 18 of its 57 answers
# are empty and are no longer items) moved retrieval depth from 1,280 to 1,262 (S390, ed75af5), and paper_qa and
# paper_qa_rest by the same 18.
KNOWN_SOURCE = {"paper_qa": 26127, "paper_qa_rest": 13249, "replication5": 12878, "selection_synth": 1652,
                "reanalysis": 4515,
                # Q57 (12 October): the two-model replication alone, for the second judge; S373's reader gives 809
                # after D7, as KNOWN_LABEL's "Strategy replication (published)"
                "replication2": 809}
KNOWN_LABEL = {"Generation strategies (exp04)": 807, "Corpus scaling (exp05)": 9696, "Orchestration (exp06)": 540,
               "Naive RAG baseline": 135, "Retrieval depth (exp09)": 1262, "Strategy replication (published)": 809,
               "S141 campaign (strategy replication, multi-generator)": 12878,
               "Generator selection (exp00 rlm_models)": 213, "Component benchmark: synthesizer (exp07)": 1439,
               "S141 mini arm (step 4.3, s50)": 2390, "S141 timing (step 4.4)": 298,
               "S357 Gemini paired arm": 180, "S314 verified_pass rerun (exp05 indexes)": 1647}
# ledger -> (sha256 of the file as surveyed, lines, {key version: rows under that key's hashes})
KNOWN_LEDGER = {
    "S373_qwen_paper_qa.jsonl": ("f37c9561f5d49563493224e935d1ef6f2ea9600da8fe3ee9376466f1e6277c7e", 6782,
                                 {"2.2": 6557, "2.3": 6557, "2.4": 5507}),   # v2.4: 5,879 before Q51 less 372 on OOD_041-050 (O38)
    "S373_gptoss_replication5.jsonl": ("346fd7d891c496f1871d7155a85a911d5483e17e211d827c6fbee2307607d7ef", 3235,
                                       {"2.2": 3139, "2.3": 3139}),
}

# Unsharded ledgers: the machine each ran on, with the reason. Valerio's port map (9 October): Mac Studio
# 11434, 11441, 11451 to 11455; laptop and Beelink 11434.
UNSHARDED = {
    "S373_qwen_paper_qa.jsonl": ("studio", "the overnight run of 8 to 9 October ran on the Mac Studio, ports 11451 "
                                            "to 11455 (Valerio's port map, 9 October)"),
    "S373_gptoss_replication5.jsonl": ("studio", "ran on the Mac Studio, restarted on Ollama 0.40.2 (Q32), on ports 11441, "
                                                 "11454 and 11455 since 11 October (D4)"),
    "S373_devstral_replication5.jsonl": ("studio", "runs on the Mac Studio (Q12, 9 October: the Mac Studio judges the "
                                                   "five-model replication as one run)"),
    "S373_devstral_paper_qa_probeLaptop.jsonl": ("laptop", "the laptop probe of 9 October, 19:37, named by its --out "
                                                           "tag; a side file, never merged"),
    "S373_devstral_reanalysis.jsonl": ("studio", "runs on the Mac Studio (port 11460 since 11 October, chain_f); "
                                                 "S402 registers the same owner"),
    "S373_gptoss_replication2.jsonl": ("studio", "runs on the Mac Studio, ports 11441, 11454 and 11455 (Q57, evening plan "
                                                 "of 12 October: the ports and the pinned gpt-oss copy of D4)"),
}
# Result files whose answers the reader changed after some rows were judged: a row from such a file that fails
# rule 4 or 5 is dropped as "answer changed since judged" instead of failing the run, and counts as missing until
# it is judged again. Any other mismatch still fails the run.
CHANGED_ANSWERS = {"exp09_depth_sweep_llama3-8b_merged.json":
                   "the S374 reader fix of 9 October 22:45 (aa64ff2, F10): rows judged before it scored the "
                   "GenerationResult repr, not the answer (plan item 11b re-judges the devstral ones)"}
PORTS = {"studio": {11434, 11441, 11451, 11452, 11453, 11454, 11455}, "laptop": {11434}, "beelink": {11434}}

PROD = re.compile(r"^S373_(qwen|gptoss|devstral)_(paper_qa|paper_qa_rest|replication5|replication2|selection_synth|reanalysis)"
                  r"(?:_shard(\d+)of(\d+))?\.jsonl$")
LOG_DONE = re.compile(r"^(\w+) shard (\w+):(\d+) done\b")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_once(p: Path) -> tuple[bytes, list[bytes], bool]:
    """(bytes read, complete lines, whether a final line without newline was skipped)."""
    b = p.read_bytes()
    parts = b.split(b"\n")
    partial = parts[-1] != b""
    return b, [x for x in parts[:-1] if x.strip()], partial


def classify(name: str) -> dict | None:
    m = PROD.match(name)
    if m:
        return {"role": "production", "judge": m.group(1), "source": m.group(2),
                "shard": [int(m.group(3)), int(m.group(4))] if m.group(3) else None}
    m = re.match(r"^S373_(qwen|gptoss|devstral)_(.+)\.jsonl$", name)
    if not m:
        return None
    rest = m.group(2)
    for src in sorted(S373.SOURCES, key=len, reverse=True):
        if rest == src:
            return {"role": "production_" + src, "judge": m.group(1), "source": src, "shard": None}
        if rest.startswith(src + "_"):
            return {"role": "side", "judge": m.group(1), "source": src, "shard": None, "out": rest[len(src) + 1:]}
    return {"role": "unknown", "judge": m.group(1), "source": None, "shard": None}


def s380_claims(rec: Path) -> tuple[dict, list[dict]]:
    """shard ledger name -> {"done": set(machines), "running": set, "failed": set}; and the status files read."""
    claims: dict[str, dict[str, set]] = defaultdict(lambda: {"done": set(), "running": set(), "failed": set()})
    status_files = []
    sources_n: dict[tuple[str, str], set[int]] = defaultdict(set)
    for p in sorted(rec.glob("S380_*_status.json")):
        judge = p.name.split("_")[1]
        d = json.loads(p.read_text(encoding="utf-8"))
        status_files.append({"file": p.name, "judge": judge, "started": d.get("started"),
                             "finished": d.get("finished"), "commit": d.get("commit"),
                             "sha256": sha256_bytes(p.read_bytes())})
        n_of = {s: int(n) for s, n in d.get("sources", [])}
        for s, n in n_of.items():
            sources_n[(judge, s)].add(n)
        for state in ("done", "running", "failed"):
            for k, v in (d.get(state) or {}).items():
                m = re.match(r"^(\w+):(\d+)$", k)
                if not m or m.group(1) not in n_of:
                    continue
                name = f"S373_{judge}_{m.group(1)}_shard{m.group(2)}of{n_of[m.group(1)]}.jsonl"
                for e in (v if isinstance(v, list) else [v]):
                    if isinstance(e, dict) and e.get("machine"):
                        claims[name][state].add(e["machine"])
    logs = []
    for p in sorted(rec.glob("S380_*_run.log")):
        judge = p.name.split("_")[1]
        n_lines = 0
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = LOG_DONE.match(ln)
            if not m:
                continue
            ns = sources_n.get((judge, m.group(2)), set())
            if len(ns) != 1:
                continue
            name = f"S373_{judge}_{m.group(2)}_shard{m.group(3)}of{next(iter(ns))}.jsonl"
            claims[name]["done"].add(m.group(1))
            n_lines += 1
        logs.append({"file": p.name, "judge": judge, "done_lines": n_lines, "sha256": sha256_bytes(p.read_bytes())})
    return claims, status_files + logs


def machine_of(name: str, info: dict, claims: dict) -> tuple[str, str]:
    if name in UNSHARDED:
        return UNSHARDED[name]
    if info.get("shard"):
        c = claims.get(name)
        if c:
            for state in ("done", "running", "failed"):
                if len(c[state]) == 1:
                    return next(iter(c[state])), f"S380 {state} record"
                if len(c[state]) > 1:
                    return "unattributed", f"several machines claim it ({state}): {sorted(c[state])}"
        return "unattributed", "no S380 status or log line names this shard"
    return "unattributed", "not in the table of unsharded ledgers and not a shard"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=RECOMPUTE, help="output folder (default findings/recompute)")
    ap.add_argument("--final", action="store_true", help="also require complete, attributed main-judge coverage")
    a = ap.parse_args()
    out = a.out.resolve()

    # ---- the key, D7 and the expected answers ---------------------------------------------------------
    key_bytes = S373.KEY.read_bytes()
    key_sha = sha256_bytes(key_bytes)
    key_doc = json.loads(key_bytes)
    kv = str(key_doc["version"])
    src = f"source_v{kv.replace('.', '')}_sha256"        # the field S381 writes for this key version
    as_v1 = json.loads(AS_V1.read_text(encoding="utf-8"))
    if as_v1.get(src) != key_sha:
        raise SystemExit(f"FATAL: {AS_V1.name} was built from another key ({src} {str(as_v1.get(src))[:12]}), "
                         f"not {S373.KEY.name} v{kv} ({key_sha[:12]})")
    d7 = set(as_v1["dropped_d7"])
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text(encoding="utf-8"))["questions"]}
    v2 = {r["id"]: r for r in key_doc["records"]}
    cur = {q: S373.key_hash(q, v2) for q in v2}

    expected: dict[str, dict[str, dict]] = {}
    for src in KNOWN_SOURCE:
        items = [x for x in S373.SOURCES[src](v1, v2) if x["question_id"] not in d7]
        expected[src] = {x["key"]: {"question_id": x["question_id"], "answer_chars": len(x["answer"])} for x in items}
    fails: list[str] = []
    for src, n in KNOWN_SOURCE.items():
        if len(expected[src]) != n:
            fails.append(f"reproduce: source {src} has {len(expected[src])} expected answers, known {n}")
    if set(expected["paper_qa"]) != set(expected["paper_qa_rest"]) | set(expected["replication5"]) \
            or set(expected["paper_qa_rest"]) & set(expected["replication5"]):
        fails.append("reproduce: paper_qa is not exactly paper_qa_rest plus replication5")
    two = "Strategy replication (published)"
    if {k: v for k, v in expected["paper_qa_rest"].items() if k.split("|")[0] == two} != expected["replication2"]:
        fails.append(f"reproduce: replication2 is not exactly paper_qa_rest's {two!r} answers")
    by_label = Counter(k.split("|")[0] for src in MAIN_SOURCES for k in expected[src])
    for label, n in KNOWN_LABEL.items():
        if by_label.get(label) != n:
            fails.append(f"reproduce: label {label!r} has {by_label.get(label)} expected answers, known {n}")
    for label in by_label:
        if label not in LABEL_TO_SLUG:
            fails.append(f"label {label!r} maps to no experiment")

    # ---- read every ledger once --------------------------------------------------------------------------
    claims, s380_files = s380_claims(RECOMPUTE)
    inputs: dict[str, dict] = {}
    kept: dict[str, dict[str, list[tuple[dict, bytes, str]]]] = defaultdict(lambda: defaultdict(list))
    side_rows: dict[str, list[dict]] = {}
    for p in sorted(Path(x) for x in glob.glob(str(RECOMPUTE / "S373_*.jsonl"))):
        info = classify(p.name)
        if info is None:
            continue
        b, lines, partial = read_once(p)
        mach, why = machine_of(p.name, info, claims)
        rec = {**info, "sha256": sha256_bytes(b), "bytes_read": len(b), "lines_read": len(lines),
               "being_written": int(partial), "kept": 0, "dropped": Counter(), "machine": mach,
               "machine_reason": why, "servers": Counter(), "rows_key_sha256": Counter(), "port_check": []}
        inputs[p.name] = rec
        rows = []
        for raw in lines:
            r = json.loads(raw)
            rows.append((r, raw))
            rec["servers"][(r.get("port"), r.get("ollama"), r.get("model_digest"))] += 1
        known = KNOWN_LEDGER.get(p.name)
        if known and rec["sha256"] == known[0]:
            n_cur = sum(1 for r, _ in rows if r.get("key_hash") == cur.get(r.get("question_id")))
            if kv not in known[2]:
                fails.append(f"reproduce: {p.name} has no count pinned for key v{kv}")
            elif len(rows) != known[1] or n_cur != known[2][kv]:
                fails.append(f"reproduce: {p.name} has {len(rows)} rows, {n_cur} under the current key v{kv}; "
                             f"known {known[1]} and {known[2][kv]}")
            rec["reproduced"] = {"lines": len(rows), "current_key_rows": n_cur}
        elif known:
            rec["reproduced"] = "not applicable: the ledger changed since the survey of 9 October"
        for port, *_ in rec["servers"]:
            if mach in PORTS and port not in PORTS[mach]:
                rec["port_check"].append(f"port {port} is not in the {mach}'s port map")
        if info["role"] == "side":
            side_rows[p.name] = [r for r, _ in rows if r.get("key_hash") == cur.get(r.get("question_id"))
                                 and r.get("question_id") not in d7]
            rec["dropped"]["side file, never merged"] = len(rows)
            continue
        if info["role"].startswith("production_exp04"):
            n_cur = sum(1 for r, _ in rows if r.get("key_hash") == cur.get(r.get("question_id")))
            if n_cur:
                fails.append(f"{p.name}: a production exp04-source ledger holds {n_cur} rows under the current key")
            rec["dropped"]["exp04-source ledger"] = len(rows)
            continue
        if info["role"] != "production":
            rec["dropped"]["not a production ledger"] = len(rows)
            continue
        exp_src = expected[info["source"]]
        for r, raw in rows:
            k, qid = r.get("key", ""), r.get("question_id")
            if k.startswith("exp04|"):
                rec["dropped"]["exp04-form key"] += 1
            elif qid in d7:
                rec["dropped"]["D7 question"] += 1
            elif r.get("key_hash") != cur.get(qid):
                rec["dropped"]["stale key"] += 1
            elif k not in exp_src or (qid, r.get("answer_chars")) != (exp_src[k]["question_id"],
                                                                      exp_src[k]["answer_chars"]):
                tag = k.split("|")[1] if k.count("|") >= 2 else ""
                if tag in CHANGED_ANSWERS:
                    rec["dropped"]["answer changed since judged"] += 1
                elif k not in exp_src:
                    fails.append(f"{p.name}: key {k!r} is not in the expected set of source {info['source']}")
                else:
                    fails.append(f"{p.name}: key {k!r} names {(qid, r.get('answer_chars'))}, the reader gives "
                                 f"{(exp_src[k]['question_id'], exp_src[k]['answer_chars'])}")
            else:
                rec["kept"] += 1
                rec["rows_key_sha256"][(r.get("key_sha256") or "")[:12]] += 1
                kept[info["judge"]][k].append((r, raw, p.name))

    # ---- duplicates ------------------------------------------------------------------------------------
    chosen: dict[str, dict[str, tuple[dict, bytes, str]]] = defaultdict(dict)
    dup = Counter()
    conflicts = []
    for judge, keys in kept.items():
        for k, cands in keys.items():
            cands = sorted(cands, key=lambda c: c[0].get("at") or "")
            scored = [c for c in cands if c[0].get("status") in OK]
            if len(cands) > 1:
                dup["keys with more than one row"] += 1
            if scored:
                distinct = {json.dumps(c[0].get("scores"), sort_keys=True) for c in scored}
                if len(distinct) > 1:
                    conflicts.append({"judge": judge, "key": k, "rows": [{"file": c[2], "at": c[0].get("at"),
                                                                           "scores": c[0].get("scores")} for c in scored]})
                    continue
                if len(scored) > 1:
                    dup["identical scored rows collapsed"] += len(scored) - 1
                if len(cands) > len(scored):
                    dup["unscored rows superseded by a scored row"] += len(cands) - len(scored)
                chosen[judge][k] = scored[0]
            else:
                if len(cands) > 1:
                    dup["unscored rows collapsed"] += len(cands) - 1
                chosen[judge][k] = cands[0]
    for c in conflicts:
        fails.append(f"conflict: {c['judge']} {c['key']} scored differently in {[x['file'] for x in c['rows']]}")

    # ---- side files against production ----------------------------------------------------------------
    side_agreement = {}
    for name, rows in side_rows.items():
        judge = inputs[name]["judge"]
        agg = Counter()
        for r in rows:
            c = chosen.get(judge, {}).get(r.get("key"))
            if c is None:
                agg["no production row on the same key"] += 1
            elif r.get("status") in OK and c[0].get("status") in OK:
                agg["identical scores" if r.get("scores") == c[0].get("scores") else "different scores"] += 1
            else:
                agg["one of the two unscored"] += 1
        side_agreement[name] = {"current_key_rows": len(rows), **agg}

    if fails:
        print("REFUSED, nothing written:")
        print("  " + "\n  ".join(fails[:60]))
        return 1

    # ---- coverage per experiment and judge ---------------------------------------------------------------
    judge_sources: dict[str, set[str]] = defaultdict(set)
    for name, rec in inputs.items():
        if rec["role"] == "production":
            judge_sources[rec["judge"]].add(rec["source"])
    judge_sources[MAIN_JUDGE] |= set(MAIN_SOURCES)
    experiments: dict[str, dict] = {s: {} for s in SLUGS}
    for judge in sorted(judge_sources):
        exp_keys: dict[str, set[str]] = defaultdict(set)
        for src in judge_sources[judge]:
            for k in expected[src]:
                exp_keys[LABEL_TO_SLUG[k.split("|")[0]]].add(k)
        rows_by_slug: dict[str, list[dict]] = defaultdict(list)
        for k, (r, _, _) in chosen.get(judge, {}).items():
            rows_by_slug[LABEL_TO_SLUG[k.split("|")[0]]].append(r)
        for slug in SLUGS:
            if slug not in exp_keys and slug not in rows_by_slug:
                continue
            rows = rows_by_slug.get(slug, [])
            want = exp_keys.get(slug, set())
            n_exp = len(want)
            st = Counter(r.get("status") for r in rows)
            scored_keys = {r["key"] for r in rows if r.get("status") in OK} & want
            not_scored = {r["key"]: r.get("status") for r in rows if r["key"] in want and r.get("status") not in OK}
            no_row = sorted(want - {r["key"] for r in rows})
            experiments[slug][judge] = {
                "model": S373.JUDGES[judge]["model"], "expected": n_exp, "rows": len(rows),
                "scored": len(scored_keys),
                "unscored": {s: n for s, n in st.items() if s not in OK},
                "missing": len(no_row),
                "not_scored": len(no_row) + len(not_scored),
                "coverage": round(len(scored_keys) / n_exp, 4) if n_exp else None,
                "unscored_keys": dict(sorted(not_scored.items())[:200]),
                "no_row_keys": no_row[:200],
                "labels": dict(Counter(r["key"].split("|")[0] for r in rows)),
            }

    machines = defaultdict(Counter)
    for judge, keys in chosen.items():
        for k, (r, _, f) in keys.items():
            machines[judge][inputs[f]["machine"]] += 1

    not_scored = {s: v[MAIN_JUDGE]["not_scored"] for s, v in experiments.items() if MAIN_JUDGE in v}
    final = {"main_judge_complete": all(n == 0 for n in not_scored.values()),
             "main_judge_not_scored": {s: n for s, n in not_scored.items() if n},
             "main_judge_unscored_rows": {s: v[MAIN_JUDGE]["unscored"] for s, v in experiments.items()
                                          if MAIN_JUDGE in v and v[MAIN_JUDGE]["unscored"]},
             "main_judge_unattributed_rows": machines[MAIN_JUDGE].get("unattributed", 0),
             "s380_status_finished": all(f.get("finished") for f in s380_files if f["file"].endswith("_status.json"))}
    final["passes"] = final["main_judge_complete"] and final["main_judge_unattributed_rows"] == 0 \
        and final["s380_status_finished"]

    # ---- write ----------------------------------------------------------------------------------------
    tree = out / "S388_rejudge_v22"
    tree.mkdir(parents=True, exist_ok=True)
    for old in sorted(tree.rglob("*.jsonl")):
        old.unlink()
    outputs = {}
    for judge, keys in sorted(chosen.items()):
        per: dict[str, list[tuple[str, bytes]]] = defaultdict(list)
        for k, (_, raw, _) in keys.items():
            per[LABEL_TO_SLUG[k.split("|")[0]]].append((k, raw))
        for slug, rows in sorted(per.items()):
            f = tree / slug / f"{judge}.jsonl"
            f.parent.mkdir(parents=True, exist_ok=True)
            data = b"".join(raw + b"\n" for _, raw in sorted(rows))
            f.write_bytes(data)
            outputs[f"{slug}/{judge}.jsonl"] = {"rows": len(rows), "sha256": sha256_bytes(data)}
    for d in sorted(tree.iterdir(), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    def jsonable(rec: dict) -> dict:
        r = dict(rec)
        r["dropped"] = dict(r["dropped"])
        r["servers"] = [[p, o, d, n] for (p, o, d), n in sorted(r["servers"].items(), key=lambda x: str(x[0]))]
        r["rows_key_sha256"] = dict(r["rows_key_sha256"])
        return r

    prov = {
        "_provenance": {
            "script": "scripts/S388_merge_rejudge_v22.py",
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "command": "uv run python scripts/S388_merge_rejudge_v22.py" + (" --final" if a.final else ""),
            "key": str(S373.KEY.relative_to(ROOT)), "key_sha256": key_sha, "key_version": kv,
            "d7": sorted(d7), "d7_source": f"{AS_V1.relative_to(ROOT)} dropped_d7",
            "as_v1_sha256": sha256_bytes(AS_V1.read_bytes()),
            "main_judge": MAIN_JUDGE, "main_judge_sources": list(MAIN_SOURCES),
            "rows_verbatim": "every output line is an input line byte for byte; outputs sorted by key",
            "changed_answers": CHANGED_ANSWERS,
        },
        "reproduced": {"sources": {s: len(expected[s]) for s in KNOWN_SOURCE},
                       "labels": {lbl: by_label[lbl] for lbl in KNOWN_LABEL},
                       "ledgers": {n: inputs[n].get("reproduced") for n in KNOWN_LEDGER if n in inputs}},
        "label_to_slug": LABEL_TO_SLUG,
        "inputs": {n: jsonable(r) for n, r in inputs.items()},
        "s380_records": s380_files,
        "side_agreement": side_agreement,
        "duplicates": dict(dup),
        "conflicts": conflicts,
        "experiments": {s: v for s, v in experiments.items() if v},
        "outputs": outputs,
        "machines": {j: dict(c) for j, c in machines.items()},
        "final": final,
    }
    (out / "S388_rejudge_v22.json").write_text(json.dumps(prov, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    md = [f"# S388 re-judge ledgers under the v{kv} key, by experiment ({prov['_provenance']['generated']})", "",
          f"Key `{prov['_provenance']['key']}` (v{kv}) sha256 {key_sha[:12]}; D7 drops {', '.join(sorted(d7))}. "
          f"Rows are copied verbatim from the S373 ledgers into `S388_rejudge_v22/<experiment>/<judge>.jsonl`.", "",
          "## Coverage", "",
          "Coverage is scored keys of expected keys: a key counts only when its row has status ok or ok_output_limit. "
          "Judged without a score: rows whose status is anything else, by status. No row: expected keys no ledger "
          "holds yet.", "",
          "| Experiment | Judge | Expected | Rows | Scored | Judged without a score | No row | Coverage (scored) |",
          "|---|---|---:|---:|---:|---|---:|---:|"]
    for slug, v in prov["experiments"].items():
        for judge, e in v.items():
            cov = f"{100 * e['coverage']:.1f}%" if e["coverage"] is not None else "-"
            md.append(f"| {slug} | {e['model']} | {e['expected']:,} | {e['rows']:,} | {e['scored']:,} | "
                      f"{e['unscored'] or '-'} | {e['missing']:,} | {cov} |")
    md += ["", "## Inputs", "", "| Ledger | Role | Lines | Being written | Kept | Dropped | Machine | Servers |",
           "|---|---|---:|---:|---:|---|---|---|"]
    for n, r in inputs.items():
        srv = "; ".join(f"{p} Ollama {o} digest {d} ({c})" for (p, o, d), c in r["servers"].items())
        md.append(f"| {n} | {r['role']} | {r['lines_read']:,} | {r['being_written']} | {r['kept']:,} | "
                  f"{dict(r['dropped']) or '-'} | {r['machine']} ({r['machine_reason']}) | {srv} |")
    md += ["", f"Duplicates: {dict(dup) or 'none'}. Conflicts: {len(conflicts)}.",
           f"Side files against production: {side_agreement or 'none'}.",
           f"Rows per machine: { {j: dict(c) for j, c in machines.items()} }.",
           f"Final check (--final): {final}.", ""]
    (out / "S388_rejudge_v22.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:10 + sum(len(v) for v in prov["experiments"].values())]))
    print(f"wrote {tree} and S388_rejudge_v22.{{json,md}} in {out}")
    if a.final and not final["passes"]:
        print(f"FINAL FAILED: {final}")
        for slug, v in prov["experiments"].items():
            e = v.get(MAIN_JUDGE)
            if e and e["not_scored"]:
                print(f"  {slug}: {e['not_scored']:,} expected keys without a scored row ({e['missing']:,} with no row; "
                      f"judged without a score: {e['unscored'] or 'none'}); first of them: "
                      f"{(list(e['unscored_keys'].items()) + [(k, 'no row') for k in e['no_row_keys']])[:5]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
