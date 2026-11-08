#!/usr/bin/env python3
"""S516 - the generation-strategy experiment (exp04) answer by answer on ground truth v2.5: S406's table of the 516
answerable answers with D181's concept recall on key v2.5 beside S406's key v2.4 columns, each of these marked where
v2.5 changed what it was scored against.

WHY. D188 (experiments/README.md "D188", Valerio, 31 October: "every figure using v2.4 needs to move to v2.5"): every
number read from a key moves to key v2.5. S487 (Figure 5's agreement numbers, inventory row F10) reads S406's exp04
table (findings/recompute/S406_exp04_per_answer_v24.csv), whose every key column is on v2.4. This script writes the
table S487 reads for its v2.5 numbers. It computes one thing, D181's concept recall (scripts/d181_concept_recall.py,
string matching, no model), and carries S406's other columns unchanged with a mark on the answers whose v2.4 value v2.5
makes stale.

WHAT v2.5 CHANGED FOR exp04 (S512.keys(), the v1-format keys the judge reads, both pinned by S512): on the 86
answerable questions, the expected_concepts of 54 and the expected_answer of one (CD_006); no other field. Hence:
  concept recall      on every answer: computed here on v2.5 (D181).
  judge scores        S406's devstral scores on key v2.4. The judge reads the question's key entry, and S512's changed
                      set (the questions whose judge fields v2.5 changed, S512.changed_ids()) holds 54 of the 86:
                      judge_pending_v25 is 1 on their 324 answers (6 strategies each), whose v2.5 judging no run holds
                      (no S6 set covers exp04). The other 192 answers' v2.4 scores are the v2.5 scores.
  MiniCheck against   mc_key_* (S384) scores the answer against the expected_answer (S384_exp04_minicheck_key_v22.py:7,
  the key, and the    on key v2.4: S384_exp04_minicheck_key_v22.md:7), and det_score_correctness_simfull (S382) is
  deterministic       0.6 x bge-m3 similarity to the expected_answer + 0.4 x number overlap with it. Both change only
  correctness         where the expected_answer changed: answer_key_pending_v25 is 1 on CD_006's 6 answers.
  MiniCheck against the papers (S19 source top 3) uses no field of the key (S406's docstring, S19:305-307): carried.

REPRODUCE BEFORE WRITING (README.md:75-79). Before anything is written, on key v2.4:
  R1 S406's csv has the sha256 its json records for it, and its "# key" line names the two v2.4 key files with the
     sha256 they have.
  R2 d181_concept_recall.spec_failures() is empty (S505's own cases and D181's).
  R3 d181_concept_recall.gate_m4 (G-C): score() with the questions reproduces S505's stored M4 loose_Qneed_b on the
     516 answerable exp04 answers of the frozen deposit file on key v2.4, per strategy and over all (0.4749 on 516).
  R4 the answers scored are S406's: exp04_population() (the frozen deposit file, the 135 questions, Rule 8's
     answerable group) gives exactly S406's 516 answerable (config, question) pairs, each text's length S406's
     answer_chars.
  The D12 loose base on the v2.4 concepts equals S406's det_concept_recall_loose (O30's union, which also counts the
  deposited scorer's per-concept matches) on most answers, not all; the count is reported and is no gate.
Then key v2.5: d181_concept_recall.the_key_v25 (pinned a4216184; same question ids, texts, answerable flags and
dropped_d7 as v2.4), and score(text, v2.5 concepts, v2.5 question text, None) per answer. An answer with no concept
counted under D181 (b) stops the run.

OUTPUT findings/recompute/S516_exp04_per_answer_v25.csv (comment lines, then one row per answerable answer in S406's
order) and S516_exp04_per_answer_v25.json (provenance: script, inputs and code sha256, the command, no time; the
gates; counts; the csv's sha256 under outputs_sha256). Columns:
  question_id, config, group, answer_type, answer_chars, status     S406's
  judge_correctness, judge_faithfulness, judge_key_version, judge_pending_v25
  det_score_correctness_simfull, mc_key_precision, mc_key_recall, mc_key_f1, answer_key_pending_v25
  mc_source_k3_precision, mc_source_k3_n_claims                     S406's (no key)
  det_concept_recall_loose_v24                                      S406's det_concept_recall_loose (key v2.4)
  concept_recall_d181, d181_n_concepts, d181_n_counted, d181_found   D181 on key v2.5 (this script)
  concept_recall_loose_base_v25, concept_recall_exact_base_v25       D12's loose matcher and its exact rule on the v2.5
                                                                     concepts, every concept counted (score()'s base)

    uv run python scripts/S516_exp04_per_answer_v25.py            writes the two files
    uv run python scripts/S516_exp04_per_answer_v25.py --check    builds them again, requires both byte-equal
Calls no model and opens no connection. d181_concept_recall imports S505, which sets two KMP_* variables in this
process's environment; this script starts no child process.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ME = "S516"
SCRIPT = "scripts/S516_exp04_per_answer_v25.py"
COMMAND = f"uv run python {SCRIPT}"
REC = ROOT / "findings" / "recompute"
S406_CSV = REC / "S406_exp04_per_answer_v24.csv"
S406_JSON = REC / "S406_exp04_per_answer_v24.json"
KEY24_FILES = (ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json", ROOT / "data/ground_truth_v2/all_v2_4.json")
OUT_CSV = REC / "S516_exp04_per_answer_v25.csv"
OUT_JSON = REC / "S516_exp04_per_answer_v25.json"
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
N_ANSWERABLE, N_QUESTIONS = 516, 86
CARRIED = ("question_id", "config", "group", "answer_type", "answer_chars", "status", "judge_correctness",
           "judge_faithfulness", "det_score_correctness_simfull", "mc_key_precision", "mc_key_recall", "mc_key_f1",
           "mc_source_k3_precision", "mc_source_k3_n_claims")
COLUMNS = ("question_id", "config", "group", "answer_type", "answer_chars", "status",
           "judge_correctness", "judge_faithfulness", "judge_key_version", "judge_pending_v25",
           "det_score_correctness_simfull", "mc_key_precision", "mc_key_recall", "mc_key_f1", "answer_key_pending_v25",
           "mc_source_k3_precision", "mc_source_k3_n_claims", "det_concept_recall_loose_v24",
           "concept_recall_d181", "d181_n_concepts", "d181_n_counted", "d181_found",
           "concept_recall_loose_base_v25", "concept_recall_exact_base_v25")


class Refused(SystemExit):
    def __init__(self, msg: str):
        super().__init__(f"{ME} REFUSED, nothing written: {msg}")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def rel(p: Path) -> str:
    return Path(p).resolve().relative_to(ROOT).as_posix()


def read_s406() -> tuple[list[dict], list[str], dict]:
    """S406's csv rows (as text), its comment lines and the R1 record."""
    raw = S406_CSV.read_bytes()
    text = raw.decode("utf-8")
    comments = [ln for ln in text.splitlines() if ln.startswith("#")]
    rows = list(csv.DictReader(io.StringIO("\n".join(ln for ln in text.splitlines() if not ln.startswith("#")))))
    recorded = json.loads(S406_JSON.read_text()).get("provenance", {}).get("outputs_sha256", {}).get(rel(S406_CSV))
    key_line = [c for c in comments if c.startswith("# key ")]
    named = re.findall(r"(data/\S+\.json) sha256 ([0-9a-f]{64})", key_line[0]) if len(key_line) == 1 else []
    have = {rel(p): sha256_file(p) for p in KEY24_FILES}
    if recorded != sha256_bytes(raw):
        raise Refused(f"R1: {rel(S406_CSV)} has sha256 {sha256_bytes(raw)[:12]}, {rel(S406_JSON)} records "
                      f"{str(recorded)[:12]}")
    if sorted(p for p, _ in named) != sorted(have) or any(have[p] != h for p, h in named):
        raise Refused(f"R1: {rel(S406_CSV)}'s '# key' line does not name the two v2.4 key files with their sha256")
    return rows, comments, {"name": "R1", "message": f"{rel(S406_CSV)} sha256 {sha256_bytes(raw)[:12]} as "
                                                     f"{rel(S406_JSON)} records; its '# key' line names "
                                                     f"{', '.join(sorted(have))} with the sha256 they have"}


def build() -> tuple[bytes, bytes]:
    """The csv and json bytes (module docstring), after R1 to R4."""
    import d181_concept_recall as D181
    import S470_l1_signals as S470
    import S512_s6_rejudge_v25 as S512
    from experiments.scorers import records
    gates = []
    rows, _, g1 = read_s406()
    gates.append(g1)
    bad = D181.spec_failures()
    if bad:
        raise Refused(f"R2: D181's rule cases fail: {bad[:3]}")
    gates.append({"name": "R2", "message": f"d181_concept_recall.spec_failures(): none ({len(D181.SPEC_CASES)} D181 "
                                           f"cases and S505's own)"})
    key24 = S470.the_key()
    try:
        m4 = D181.gate_m4(key24, records.group_of)
    except D181.GateFail as e:
        raise Refused(f"R3: {e}") from None
    gates.append({"name": "R3", "message": f"S505's M4 {D181.M4_COLUMN} reproduced on key v2.4: "
                                           + ", ".join(f"{s} {v[0]} on {v[1]}" for s, v in m4["reproduced"].items()),
                  "reference": m4["reference"], "reference_sha256": m4["reference_sha256"]})
    A = [r for r in rows if r["group"] == "answerable"]
    at = {(r["config"], r["question_id"]): r for r in A}
    pop = {(a["strategy"], a["question_id"]): a for a in D181.exp04_population(key24, records.group_of)}
    if len(A) != N_ANSWERABLE or len(at) != N_ANSWERABLE or set(at) != set(pop):
        raise Refused(f"R4: S406 holds {len(A)} answerable rows on {len(at)} pairs; the deposit's population "
                      f"{len(pop)}; {len(set(at) ^ set(pop))} pairs in one only")
    off = [k for k in at if len(pop[k]["text"]) != int(at[k]["answer_chars"])]
    if off:
        raise Refused(f"R4: {len(off)} answers' text length is not S406's answer_chars, first {off[0]}")
    base_eq = sum(1 for k, r in at.items()
                  if abs(D181.score(pop[k]["text"], pop[k]["concepts"], "", None)["concept_recall_loose_base"]
                         - float(r["det_concept_recall_loose"])) < 1e-9)
    gates.append({"name": "R4", "message": f"exp04_population() gives S406's {N_ANSWERABLE} answerable (config, "
                                           f"question) pairs one for one, each text's length S406's answer_chars"})
    key25 = D181.the_key_v25(key24)
    k24, k25 = S512.keys()
    changed = set(S512.changed_ids())
    qs = sorted({q for _, q in at})
    if len(qs) != N_QUESTIONS:
        raise Refused(f"{len(qs)} answerable questions, want {N_QUESTIONS}")
    diff_fields = Counter(f for q in qs for f in set(k24[q]) | set(k25[q]) if k24[q].get(f) != k25[q].get(f))
    answer_changed = {q for q in qs if k24[q].get("expected_answer") != k25[q].get("expected_answer")}
    out, none = [], []
    for r in A:                                           # S406's order
        k = (r["config"], r["question_id"])
        q = key25["questions"][r["question_id"]]
        s = D181.score(pop[k]["text"], q["expected_concepts"], q["question"], None)
        if s["concept_recall"] is None:
            none.append(k)
            continue
        row = {c: r[c] for c in CARRIED}
        row.update(judge_key_version="2.4", judge_pending_v25=int(r["question_id"] in changed),
                   answer_key_pending_v25=int(r["question_id"] in answer_changed),
                   det_concept_recall_loose_v24=r["det_concept_recall_loose"],
                   concept_recall_d181=repr(s["concept_recall"]), d181_n_concepts=s["n_concepts"],
                   d181_n_counted=s["n_counted"], d181_found=s["found"],
                   concept_recall_loose_base_v25=repr(s["concept_recall_loose_base"]),
                   concept_recall_exact_base_v25=repr(s["concept_recall_exact_base"]))
        out.append(row)
    if none:
        raise Refused(f"{len(none)} answers have no concept counted under D181 (b) on key v2.5, first {none[0]}")
    jp = [r for r in out if r["judge_pending_v25"]]
    kp = [r for r in out if r["answer_key_pending_v25"]]
    per = {c: [float(r["concept_recall_d181"]) for r in out if r["config"] == c] for c in CONFIGS}
    head = [f"# generated by {SCRIPT}; command {COMMAND}; provenance in {OUT_JSON.name}",
            f"# key {key25['path']} sha256 {key25['sha256']} (ground truth v2.5)",
            f"# one row per answerable exp04 answer ({len(out)}); concept_recall_d181 and the d181_ and _v25 columns "
            f"on key v2.5 (D181, computed here); the judge, MiniCheck-against-the-key and deterministic columns are "
            f"S406's on key v2.4: judge_pending_v25 1 on the {len(jp)} answers of the {len({r['question_id'] for r in jp})} "
            f"questions whose judge fields v2.5 changed (S512.changed_ids), answer_key_pending_v25 1 on the {len(kp)} "
            f"answers of {', '.join(sorted(answer_changed))}, whose expected_answer v2.5 changed"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(out)
    csv_bytes = ("\n".join(head) + "\n" + buf.getvalue()).encode("utf-8")
    inputs = [S406_CSV, S406_JSON, *KEY24_FILES, D181.KEY25, D181.EXP04, D181.S505_RESULTS]
    doc = {"provenance": {"script": SCRIPT, "script_sha256": sha256_file(ROOT / SCRIPT), "command": COMMAND,
                          "inputs_sha256": {rel(p): sha256_file(p) for p in inputs},
                          "code_sha256": {**D181.code_sha256(),
                                          "scripts/S512_s6_rejudge_v25.py": sha256_file(ROOT / "scripts/S512_s6_rejudge_v25.py")},
                          "model_calls": 0, "no_time": "no time is written, so two runs give the same bytes"},
           "what": "S406's 516 answerable exp04 answers with D181's concept recall on key v2.5 (module docstring)",
           "gates": gates,
           "key": {"v2.5": {"path": key25["path"], "sha256": key25["sha256"]},
                   "fields_v25_changed_on_the_86": dict(sorted(diff_fields.items())),
                   "expected_answer_changed": sorted(answer_changed),
                   "judge_changed_questions": len({r["question_id"] for r in jp})},
           "counts": {"rows": len(out), "judge_pending_v25": len(jp), "answer_key_pending_v25": len(kp),
                      "d12_loose_base_v24_equal_to_s406_loose": f"{base_eq} of {len(out)} (O30's union in S406 also "
                                                               f"counts the deposited scorer's per-concept matches; "
                                                               f"no gate)",
                      "concept_recall_d181_mean": {c: round(sum(v) / len(v), 6) for c, v in per.items()},
                      "concept_recall_d181_mean_all": round(sum(sum(v) for v in per.values()) / len(out), 6)},
           "outputs_sha256": {rel(OUT_CSV): sha256_bytes(csv_bytes)}}
    return csv_bytes, (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="build again and require both files byte-equal")
    a = ap.parse_args(argv)
    csv_b, json_b = build()
    if a.check:
        same = OUT_CSV.is_file() and OUT_CSV.read_bytes() == csv_b and OUT_JSON.is_file() and \
            OUT_JSON.read_bytes() == json_b
        print(f"{ME} check: {rel(OUT_CSV)} and {OUT_JSON.name} {'byte-equal' if same else 'DIFFER'}")
        return 0 if same else 1
    for p, b in ((OUT_CSV, csv_b), (OUT_JSON, json_b)):
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_bytes(b)
    for p in (OUT_CSV, OUT_JSON):
        os.replace(p.with_name(p.name + ".tmp"), p)
    doc = json.loads(json_b)
    for g in doc["gates"]:
        print(f"  ok {g['name']}  {g['message']}")
    print(f"{ME}: wrote {rel(OUT_CSV)} ({doc['counts']['rows']} rows, sha256 {sha256_bytes(csv_b)[:12]}) and "
          f"{OUT_JSON.name}; judge pending on v2.5 {doc['counts']['judge_pending_v25']}, answer key pending "
          f"{doc['counts']['answer_key_pending_v25']}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
