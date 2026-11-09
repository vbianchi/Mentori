#!/usr/bin/env python3
"""S512 (plan row S6; D182): S3's judge on the 132 questions whose judge prompt key v2.5 changed, on key v2.5.

WHY. D182 (experiments/README.md:1309-1316) sets S6's load: the answers to the 132 questions whose expected answer or
expected concepts differ between key v2.4 and key v2.5 are judged again on v2.5. The S3 judging reads its key from a
module constant (scripts/S373_rejudge_v2.py:70, all_v2_4.json) and has no option for another; v2.5 exists only as
data/ground_truth_v2/ground_truth_v2_5_as_v1.json. Changing S373.KEY, or judge_passages.py, would change
judge_passages.code_identity, so every S3 clone's kept check and every row's run_sha256 (panel f's two fingerprints,
38ae79ab and 11e51fde, among them). This script changes neither: it imports S3's judge (judge_passages.py) and changes
only the key, to v2.5, and the question list, to the 132.

WHAT IS THE SAME AS S3 (experiments/scorers/judge_passages.py, read, not copied):
  - the answers: judge_passages.run_answers (records.py reads the run, the passages resolved through the store, Rule 8's
    group checked against S373.judged_answerable);
  - the prompts and calls: judge_passages.safe_prompts, judge_answer, judge_call (call (a), the archived prompt; call
    (b), the same with the passages block; LOCK.toml [judge] settings through ollama_client; the parser that never
    invents a score; one more try on a failed or unparseable call);
  - the phases (--variants a, --draws), the row format, resume (latest_rows, is_done), one writer per out
    (hold_writer), one judge per folder (refuse_other_judge), the fresh load and server checks (start), the recheck and
    the summary (recheck, finish), and the run's last line run_s3.sh reads;
  - the command lines of `check` and `run`, so findings/recompute/S3_runs/run_s3.sh drives it with S3_JP set to this
    file, units and claims shared as for any S3 set (s3_guard.py SETS "S6<set>").

WHAT DIFFERS, and nothing else:
  - the key: expected answer and concepts from ground_truth_v2_5_as_v1.json (sha256 pinned, as S508 pins it), key_hash
    by S373's formula on that text (the Q51 marker for the refutation questions, S373.refutation on all_v2_4.json,
    whose answer types v2.5 does not change). The prompt rule stays S373.judged_answerable, which equals v2.5's
    answerable flag on all 244 questions (checked on every read). On the 112 unchanged questions v2.5's text, so
    key_hash and every prompt, equal v2.4's (selftest);
  - the questions: the 132 whose expected_answer or expected_concepts differ between the v2.4 and v2.5 as_v1 files
    (S504's judge_prompt_changes rule, scripts/S504_key_v2_5.py:765-781), recomputed on every read from both files under
    their sha256 pins and held to N_CHANGED and CHANGED_SHA256. The filter is applied after judge_passages.select, so a
    --keys file (G1R15) is checked against the whole run as in S3;
  - run_sha256: sha256 of judge_passages.run_identity and this script's code_identity (judge_passages' code identity,
    this file, the two keys' and the 132's sha256), so a row of S6 never resumes or joins a v2.4 row;
  - the reference of the check (README.md:75-79, reproduce before writing): S3's check compares the 107 calibration
    answers on key v2.4 with S440's stored lock pass. On v2.5, 69 of the 107 (10 of 15 questions) have another prompt,
    so no stored score exists for them. `calibrate` makes the v2.5 reference once (Q15 of 30 October, O2 of
    findings/recompute/rerun_effort_2026-10-30/rerun_effort.md): the 107 judged twice, each pass after its own fresh
    load; it passes only if every call is ok, the 38 answers whose prompt v2.5 leaves unchanged equal S440's stored
    lock pass in both passes (this machine, server, lock and code reproduce the stored reference), and all 107 give the
    same scores in both passes. Then it writes the reference (REFERENCE) and this port's passed check. `check` on any
    other port judges the 107 once and compares every score with the reference;
  - STORED (S373's pre-lock devstral rows, judge_passages.STORED) is not read: those prompts carry key v2.4, and every
    one of the 132 has another prompt on v2.5 (selftest), so no stored score can match; a_equals_stored is null on
    every row;
  - every row also carries "key_version": "v2.5"; the summary an "s6" block.

THE SECOND JUDGE (D85; LOCK.toml [models] qwen3.8:27b: the Beelink only). --judge second as in S3: its check is D85's
repeat check on the 107 calibration answers on v2.5 (two passes, every score equal, temperature 0 and think false
sent); its rows carry the "judge" tag; its outs and check dir are its own (run_s3.sh S3_JUDGE=second).

GUARDS. `run` refuses an --out with no path part beginning "out_s6_" (S6's outs, s3_guard.py SETS), so a v2.5 row
never lands in a v2.4 out; a check dir whose repro_check.json is not S6's (another kind, judge code, lock, machine,
server or reference); a reference whose sha256 is not the one the check compared with; --arm (S6 reads runs only).
judge_passages.py refuses S6's check in turn (its code identity differs). run_s3.sh refuses an S6 set unless S3_JP is
this file, and a v2.4 set when it is (s3_guard.py set, the sixth field).

    uv run --frozen python scripts/S512_s6_rejudge_v25.py selftest [--run <run> [--store <dir>]]
    uv run --frozen python scripts/S512_s6_rejudge_v25.py calibrate --base http://127.0.0.1:11434 --log <server log> \
        --binary <ollama> --machine macos --out <check dir> [--n N]          (N < 107: a smoke, writes no reference)
    uv run --frozen python scripts/S512_s6_rejudge_v25.py check --base ... --log ... --binary ... --machine ... \
        --out <check dir> [--n N] [--judge main|second]
    uv run --frozen python scripts/S512_s6_rejudge_v25.py run --base ... --log ... --binary ... --machine ... \
        --check-dir <check dir> --run <run> --out <.../out_s6_<set>/judge/<run>> [judge_passages run's options]

Writes: calibrate and check, as judge_passages check (repro_check.json, repro_check_rows.jsonl, check_calls.jsonl,
fresh_load_*.json in the check dir); calibrate also REFERENCE and its sidecar <REFERENCE>.json; run, as judge_passages
run (judge_passages.jsonl and the rest in --out). No model call in selftest. Exit codes as judge_passages.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import S141_runner.judge as J  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402
from experiments.runner.lock import load  # noqa: E402
from experiments.scorers import judge_passages as JP  # noqa: E402

KEY25 = ROOT / "data/ground_truth_v2/ground_truth_v2_5_as_v1.json"
KEY25_SHA256 = "a42161841980792f5da521819c97b16dc54999b45838b8eb87cd4315f798270a"   # amendment 9; S504 --final; S508
KEY24 = ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json"                  # S373.AS_V1, the v1 form of S373.KEY
KEY24_SHA256 = "e971de522df6fab54a070e44736b6cb28a5ebd26bab07ca9e1513230bb86f4ef"
N_CHANGED = 132                                                                     # D182; S504 judge_prompt_changes
CHANGED_SHA256 = "c1759aaeaefad9d775d734451fa9c95550a76fdeb8363e0003c1d13e9a6f9d61"  # sha256 of json.dumps(sorted ids)
REFERENCE = ROOT / "findings/recompute/S512_s6_v25/calibration_v25_lock.jsonl"     # `calibrate` writes it once
S508_ROWS = ROOT / "findings/recompute/S508_judge_49_v25/rows.jsonl"                 # selftest's reproduce of the key path
OUT_MARK = "out_s6_"                                                                # S6's outs (s3_guard.py SETS)
KEY_VERSION = "v2.5"
SCRIPT = "scripts/S512_s6_rejudge_v25.py"
CHECK_N = JP.CHECK_N
KINDS = {"main": ("s6_calibrate", "s6_check"), "second": ("s6_repeat",)}


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8", "surrogatepass") if isinstance(b, str) else b).hexdigest()


# ---------------------------------------------------------------- the key and the 132

_KEYS: dict = {}


def keys() -> tuple[dict, dict]:
    """(v2.4 as_v1, v2.5 as_v1) by question id, each file under its sha256 pin; read once per process."""
    if not _KEYS:
        for name, path, want in (("k24", KEY24, KEY24_SHA256), ("k25", KEY25, KEY25_SHA256)):
            raw = path.read_bytes()
            if sha(raw) != want:
                raise SystemExit(f"REFUSED: {path.name} sha256 {sha(raw)[:12]} is not the pinned {want[:12]}")
            _KEYS[name] = {q["id"]: q for q in json.loads(raw)["questions"]}
        if set(_KEYS["k24"]) != set(_KEYS["k25"]):
            raise SystemExit("REFUSED: keys v2.4 and v2.5 hold different question ids")
    return _KEYS["k24"], _KEYS["k25"]


def changed_ids() -> list[str]:
    """The questions whose judge prompt v2.5 changes: expected_answer or expected_concepts differ from v2.4."""
    k24, k25 = keys()
    ids = sorted(q for q in k25 if k25[q]["expected_answer"] != k24[q]["expected_answer"]
                 or k25[q]["expected_concepts"] != k24[q]["expected_concepts"])
    if len(ids) != N_CHANGED or sha(json.dumps(ids)) != CHANGED_SHA256:
        raise SystemExit(f"REFUSED: {len(ids)} changed questions (sha256 {sha(json.dumps(ids))[:12]}), not the "
                         f"{N_CHANGED} pinned ({CHANGED_SHA256[:12]})")
    return ids


def v2_records() -> dict:
    """S373's v2-format key (all_v2_4.json): only for S373.refutation and S373.judged_answerable, which read its
    answer types; v2.5 changes no answer type, question or answerable flag (selftest)."""
    return {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}


def key_of25(qid: str) -> tuple[str, list[str]]:
    """Expected answer and concepts as the judge sees them, from key v2.5 (as S508 reads them, S508:124-126)."""
    q = keys()[1][qid]
    return q["expected_answer"], list(q["expected_concepts"])


def key_hash25(qid: str, v2: dict) -> str:
    """S373.key_hash's formula (S373_rejudge_v2.py:125-132) on v2.5's text: equal to S373's on every unchanged question."""
    ea, ec = key_of25(qid)
    parts = [ea, ec] + (["Q51: answerable prompt"] if S373.refutation(qid, v2) else [])
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()[:16]


def item_sha(x: dict) -> str:
    """judge_passages' item_sha256 (judge_passages.py:583-586), the same fields in the same order."""
    return sha(json.dumps([x[k] for k in ("question", "expected", "concepts", "answer", "gen_error", "answerable",
                                          "key_hash")]
                          + [[c.get("source"), c.get("chunk_idx"), c["text"]] for c in x["contexts"]],
                          ensure_ascii=False))


def rekey(items: list[dict]) -> list[dict]:
    """judge_passages.run_answers' items with key v2.5 in place of v2.4: expected, concepts, key_hash, item_sha256.
    The prompt rule judge_passages chose (S373.judged_answerable) must equal v2.5's answerable flag."""
    _, k25 = keys()
    v2 = v2_records()
    out = []
    for x in items:
        qid = x["question_id"]
        if qid not in k25:
            raise SystemExit(f"REFUSED: {qid} is not in key v2.5")
        if x["answerable"] != (k25[qid]["answerable"] in (True, "true", "True")):
            raise SystemExit(f"REFUSED: {qid}: the judge's prompt rule says answerable {x['answerable']}, key v2.5 "
                             f"{k25[qid]['answerable']}")
        y = dict(x)
        y["expected"], y["concepts"] = key_of25(qid)
        y["key_hash"] = key_hash25(qid, v2)
        y["item_sha256"] = item_sha(y)
        out.append(y)
    return out


def run_answers(run: Path, rows_sel: str | None, store: Path | None) -> list[dict]:
    """Every answer of the run as judge_passages.run_answers reads it, on key v2.5 (the 132 are taken by select)."""
    return rekey(JP.run_answers(run, rows_sel, store))


def only_changed(items: list[dict]) -> list[dict]:
    ch = set(changed_ids())
    return [x for x in items if x["question_id"] in ch]


def select(items: list[dict], draws, keys_: list[str] | None, answered_only: bool) -> list[dict]:
    """judge_passages.select (draws, --keys checked against the whole run, answered only), then the 132."""
    return only_changed(JP.select(items, draws, keys_, answered_only))


# ---------------------------------------------------------------- identity

def code_identity() -> dict:
    return {"judge_passages": JP.code_identity(), "s512_py": sha(Path(__file__).read_bytes()),
            "key25_sha256": KEY25_SHA256, "key24_sha256": KEY24_SHA256, "changed_sha256": CHANGED_SHA256}


def run_identity(lock, call) -> str:
    return sha(json.dumps({"judge_passages_run_identity": JP.run_identity(lock, call), "s6": code_identity()},
                          sort_keys=True))


# ---------------------------------------------------------------- calibration on v2.5

def calib_items() -> list[dict]:
    """S376's 107 calibration answers (S376.answers_and_key, the check's own items) on key v2.5. S376's key text must
    equal key v2.4's as_v1 for every item (the bridge: S376 reads all_v2_4.json), its answerable flag key v2.5's;
    key_hash by S376's formula (sha256 of [expected, concepts], 16 characters). Each item says whether v2.5 changed
    its prompt."""
    import S376_judge_calibration as S376
    k24, k25 = keys()
    ch = set(changed_ids())
    out = []
    for x in S376.answers_and_key():
        qid = x["question_id"]
        if (x["expected"], x["concepts"]) != (k24[qid]["expected_answer"], list(k24[qid]["expected_concepts"])):
            raise SystemExit(f"REFUSED: {x['answer_key']}: S376's key text is not key v2.4's as_v1")
        if x["answerable"] != (k25[qid]["answerable"] in (True, "true", "True")):
            raise SystemExit(f"REFUSED: {x['answer_key']}: S376's answerable flag is not key v2.5's")
        ea, ec = key_of25(qid)
        y = dict(x, expected=ea, concepts=ec, changed=qid in ch,
                 key_hash=hashlib.sha256(json.dumps([ea, ec], ensure_ascii=False).encode()).hexdigest()[:16])
        if not y["changed"] and y["key_hash"] != x["key_hash"]:
            raise SystemExit(f"REFUSED: {x['answer_key']}: an unchanged question with another key hash")
        out.append(y)
    if len(out) != CHECK_N:
        raise SystemExit(f"REFUSED: expected the {CHECK_N} calibration answers, got {len(out)}")
    return out


def s440_lock() -> dict:
    """answer_key -> S440's stored lock-pass row (the last per answer key wins, as judge_passages check reads it)."""
    return {r["answer_key"]: r for r in JP.read_rows(JP.S440_LEDGER) if r["pass"] == "lock"}


def dims(answerable: bool) -> tuple:
    return J.ANSWERABLE_DIMS if answerable else J.UNANSWERABLE_DIMS


def same_scores(res: dict, ref_scores: dict | None, answerable: bool) -> bool:
    return res["status"] == "ok" and res["scores"] == {d: (ref_scores or {}).get(d) for d in dims(answerable)}


def prompt_of(x: dict) -> str:
    return J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)


def judge_pass(a, out: Path, items: list[dict], log: Path, variant: str, what: str) -> tuple[list, dict, tuple]:
    """One pass of the calibration answers after its own fresh load: (results, fresh load, (lock, model, call))."""
    lock, model, call, fl = JP.start(a, out, what)
    base = a.base.rstrip("/")
    got = []
    for i, x in enumerate(items, 1):
        res = JP.judge_call(base, call, prompt_of(x), x["answerable"], None, log,
                            {"answer": x["answer_key"], "variant": variant, "key_hash": x["key_hash"]})
        got.append(res)
        print(f"{what} {i}/{len(items)} {x['answer_key']:45s} {'v2.5 changed' if x['changed'] else 'unchanged':12s} "
              f"{res['status']} {res['wall_s']} s", flush=True)
    return got, fl, (lock, model, call)


def check_record(kind: str, a, lock, model, call, fl: dict, sent: dict, rows: list, passed: bool, n: int,
                 extra: dict) -> dict:
    """repro_check.json in judge_passages check's keys (require_check reads the same ones) plus S6's own."""
    eq = sum(r["equal"] for r in rows)
    return {"_provenance": {"script": f"{SCRIPT} {kind}", "inputs": [str(KEY25), "S376.answers_and_key"],
                            "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
            "kind": kind, "key_version": KEY_VERSION, "key25_sha256": KEY25_SHA256, "n": n, "equal_scores": eq,
            "identical_text": sum(bool(r.get("same_text")) for r in rows), "full_sample": n == CHECK_N,
            "passed": passed, "differences": [r for r in rows if not r["equal"]], "lock_sha256": lock.sha256,
            "model": model, "server": a.base.rstrip("/"), "ollama_version": sent.get("ollama_version"),
            "model_digest": sent.get("model_digest"), "options_sent": sent.get("options_sent"),
            "fields_sent": sent.get("fields_sent"), "system_prompt_sha256": call.system and sha(call.system),
            "system_sent_sha256": sent.get("system_sent") and sha(sent["system_sent"]),
            "machine_identity": fl["machine_identity"], "server_checks": fl["server_check"]["checks"],
            "code": code_identity(), "fresh_load_ok": fl["ok"], **extra}


def write_check(out: Path, summary: dict, rows: list) -> None:
    (out / "repro_check.json").write_text(json.dumps(summary, indent=1) + "\n")
    with (out / "repro_check_rows.jsonl").open("w") as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def refuse_kept_check(out: Path) -> None:
    if (out / "repro_check.json").exists():
        raise SystemExit(f"REFUSED: {out} already holds a check (repro_check.json); a check dir holds one check, so "
                         f"move it aside to check again")


def cmd_calibrate(a) -> int:
    """The v2.5 reference (once, main judge): two passes of the 107, the 38 unchanged equal to S440 in both, all 107
    equal across the passes, every call ok and sent at temperature 0 with think false. Writes this port's check and,
    when it passed on all 107, the reference."""
    a.judge = "main"
    out, ref_f = a.out, a.reference
    if ref_f.exists():
        raise SystemExit(f"REFUSED: {ref_f} exists: the v2.5 reference is made once (move it aside to make another, "
                         f"Valerio's call)")
    model = JP.judge_of(load(), "main")
    JP.refuse_other_judge(out, model)
    refuse_kept_check(out)
    items = calib_items()
    items = items[: a.n] if a.n else items
    s440 = s440_lock()
    for x in items:
        r = s440.get(x["answer_key"])
        if not x["changed"] and (r is None or r["key_hash"] != x["key_hash"]):
            raise SystemExit(f"REFUSED: {x['answer_key']} (unchanged on v2.5) has no S440 lock-pass row under the same key")
    log = out / "check_calls.jsonl"
    passes, fls = [], []
    n0 = len(JP.read_rows(log))
    for p in (1, 2):
        got, fl, (lock, model, call) = judge_pass(a, out, items, log, f"a_calibrate_{p}", f"calibrate pass {p}")
        passes.append(got)
        fls.append(fl)
    sent = JP.read_rows(log)[n0:]
    rows = []
    for x, r1, r2 in zip(items, *passes):
        s = (s440.get(x["answer_key"]) or {}).get("scores")
        across = r1["status"] == "ok" and r2["status"] == "ok" and r1["scores"] == r2["scores"]
        vs440 = None if x["changed"] else (same_scores(r1, s, x["answerable"]) and same_scores(r2, s, x["answerable"]))
        rows.append({"answer_key": x["answer_key"], "question_id": x["question_id"], "changed": x["changed"],
                     "key_hash": x["key_hash"], "status": [r1["status"], r2["status"]], "scores": r2["scores"],
                     "first_scores": r1["scores"], "equal_across_passes": across, "equal_s440": vs440,
                     "equal": across and vs440 is not False, "same_text": r1["text"] == r2["text"],
                     "raw_text": r2["text"], "prompt_sha256": r2["prompt_sha256"],
                     "prompt_tokens": r2["prompt_tokens"], "output_tokens": [r1["output_tokens"], r2["output_tokens"]],
                     "wall_s": [r1["wall_s"], r2["wall_s"]]})
    n = len(rows)
    all_ok = all(s == "ok" for r in rows for s in r["status"])
    t0 = bool(sent) and all(JP.sent_t0_think_off(r) for r in sent)
    one_lock = all(r.get("lock_sha256") == lock.sha256 for r in sent)
    same_machine = fls[0]["machine_identity"] == fls[1]["machine_identity"]
    unchanged = [r for r in rows if not r["changed"]]
    passed = (n == CHECK_N and all(r["equal"] for r in rows) and all_ok and t0 and one_lock and same_machine
              and all(f["ok"] for f in fls))
    summary = check_record("s6_calibrate", a, lock, model, call, fls[0], sent[-1] if sent else {}, rows, passed, n, {
        "reference": "made by this calibrate: the 107 on key v2.5, two passes after their own fresh loads",
        "reference_sha256": None, "unchanged": len(unchanged),
        "unchanged_equal_s440": sum(r["equal_s440"] is True for r in unchanged),
        "changed": n - len(unchanged), "equal_across_passes": sum(r["equal_across_passes"] for r in rows),
        "all_calls_ok": all_ok, "calls_read": len(sent), "sent_temperature_0_think_false": t0,
        "one_lock_both_passes": one_lock, "same_machine_both_passes": same_machine,
        "server_checks_pass_2": fls[1]["server_check"]["checks"]})
    if passed:
        ref_f.parent.mkdir(parents=True, exist_ok=True)
        raw = "".join(json.dumps({"pass": "lock_v25", "answer_key": r["answer_key"], "question_id": r["question_id"],
                                  "changed": r["changed"], "key_hash": r["key_hash"], "scores": r["scores"],
                                  "raw_text": r["raw_text"], "prompt_sha256": r["prompt_sha256"],
                                  "model": model, "model_digest": summary["model_digest"],
                                  "lock_sha256": lock.sha256}, ensure_ascii=False) + "\n" for r in rows)
        ref_f.write_text(raw)
        summary["reference_sha256"] = sha(raw.encode())
        side = {"_provenance": {"script": f"{SCRIPT} calibrate", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "inputs": {str(KEY25.relative_to(ROOT)): KEY25_SHA256,
                                           str(JP.S440_LEDGER.relative_to(ROOT)): sha(JP.S440_LEDGER.read_bytes())},
                                "check_dir": str(out)},
                "rows": n, "sha256": summary["reference_sha256"], "changed": n - len(unchanged),
                "unchanged_equal_s440": summary["unchanged_equal_s440"], "machine_identity": fls[0]["machine_identity"],
                "server": a.base.rstrip("/"), "model_digest": summary["model_digest"], "lock_sha256": lock.sha256,
                "code": code_identity()}
        ref_f.with_name(ref_f.name + ".json").write_text(json.dumps(side, indent=1) + "\n")
    write_check(out, summary, rows)
    print(f"REPRODUCTION: {sum(r['equal'] for r in rows)} of {n} answers equal (v2.5 calibration): "
          f"{summary['unchanged_equal_s440']} of {len(unchanged)} unchanged equal to S440's stored lock pass in both "
          f"passes, {summary['equal_across_passes']} of {n} equal across two fresh loads; every call sent temperature "
          f"0 and think false: {t0}; {'PASSED, reference written to ' + str(ref_f) if passed else 'NOT PASSED' + ('' if n == CHECK_N else ' (a smoke sample, no reference)')}",
          flush=True)
    return 0 if passed or (n < CHECK_N and all(r["equal"] for r in rows) and all_ok and t0) else 1


def read_reference(ref_f: Path) -> tuple[dict, str]:
    if not ref_f.exists():
        raise SystemExit(f"REFUSED: no v2.5 reference at {ref_f}: run `calibrate` once on one port first, or copy the "
                         f"reference it wrote (README \"S6, key v2.5\")")
    raw = ref_f.read_bytes()
    rows = {r["answer_key"]: r for r in map(json.loads, filter(str.strip, raw.decode().splitlines()))}
    if len(rows) != CHECK_N or any(r.get("pass") != "lock_v25" for r in rows.values()):
        raise SystemExit(f"REFUSED: {ref_f} is not a full v2.5 reference ({len(rows)} rows)")
    return rows, sha(raw)


def cmd_check(a) -> int:
    """Main judge: the 107 on key v2.5, once after a fresh load, every score equal to the reference. Second judge:
    D85's repeat check on key v2.5."""
    which = JP.judge_arg(a)
    out = a.out
    JP.refuse_other_judge(out, JP.judge_of(load(), which))
    refuse_kept_check(out)
    if which != "main":
        return cmd_check_repeat(a)
    ref, ref_sha = read_reference(a.reference)
    items = calib_items()
    for x in items:
        r = ref.get(x["answer_key"])
        if r is None or r["key_hash"] != x["key_hash"]:
            raise SystemExit(f"REFUSED: {x['answer_key']} has no reference row under the same v2.5 key")
    items = items[: a.n] if a.n else items
    log = out / "check_calls.jsonl"
    n0 = len(JP.read_rows(log))
    got, fl, (lock, model, call) = judge_pass(a, out, items, log, "a_check", "check")
    sent = JP.read_rows(log)[n0:]
    rows = []
    for x, res in zip(items, got):
        r = ref[x["answer_key"]]
        rows.append({"answer_key": x["answer_key"], "changed": x["changed"], "status": res["status"],
                     "scores": res["scores"], "stored": r["scores"],
                     "equal": same_scores(res, r["scores"], x["answerable"]),
                     "same_text": res["text"] == (r.get("raw_text") or ""), "prompt_tokens": res["prompt_tokens"],
                     "output_tokens": res["output_tokens"], "wall_s": res["wall_s"], "load_s": res["load_s"]})
    n = len(rows)
    passed = n == CHECK_N and all(r["equal"] for r in rows)
    summary = check_record("s6_check", a, lock, model, call, fl, sent[-1] if sent else {}, rows, passed, n, {
        "reference": str(a.reference), "reference_sha256": ref_sha, "all_calls_ok": all(r["status"] == "ok" for r in rows),
        "changed": sum(r["changed"] for r in rows)})
    write_check(out, summary, rows)
    print(f"REPRODUCTION: {summary['equal_scores']} of {n} answers with every score equal to the v2.5 reference "
          f"({ref_sha[:12]}); {summary['identical_text']} of {n} identical judge text; "
          f"{'PASSED' if passed else 'NOT PASSED' + ('' if n == CHECK_N else ' (a smoke sample)')}", flush=True)
    return 0 if passed or (n < CHECK_N and summary["equal_scores"] == n) else 1


def cmd_check_repeat(a) -> int:
    """D85's repeat check of the second judge, on key v2.5 (judge_passages.cmd_check_repeat's rule)."""
    out = a.out
    items = calib_items()
    items = items[: a.n] if a.n else items
    log = out / "check_calls.jsonl"
    n0 = len(JP.read_rows(log))
    passes, fls = [], []
    for p in (1, 2):
        got, fl, (lock, model, call) = judge_pass(a, out, items, log, f"a_check_{p}", f"check pass {p}")
        passes.append(got)
        fls.append(fl)
    sent = JP.read_rows(log)[n0:]
    rows = []
    for x, r1, r2 in zip(items, *passes):
        same = r1["status"] == "ok" and r2["status"] == "ok" and r1["scores"] == r2["scores"]
        rows.append({"answer_key": x["answer_key"], "changed": x["changed"], "status": [r1["status"], r2["status"]],
                     "scores": r2["scores"], "first_scores": r1["scores"], "equal": same, "same_text": r1["text"] == r2["text"],
                     "wall_s": [r1["wall_s"], r2["wall_s"]]})
    n = len(rows)
    all_ok = all(s == "ok" for r in rows for s in r["status"])
    t0 = bool(sent) and all(JP.sent_t0_think_off(r) for r in sent)
    one_lock = all(r.get("lock_sha256") == lock.sha256 for r in sent)
    same_machine = fls[0]["machine_identity"] == fls[1]["machine_identity"]
    passed = n == CHECK_N and all(r["equal"] for r in rows) and all_ok and t0 and one_lock and same_machine
    summary = check_record("s6_repeat", a, lock, model, call, fls[0], sent[-1] if sent else {}, rows, passed, n, {
        "judge": "second", "reference": "D85 repeat check on key v2.5", "reference_sha256": None,
        "all_calls_ok": all_ok, "sent_temperature_0_think_false": t0, "one_lock_both_passes": one_lock,
        "same_machine_both_passes": same_machine, "server_checks_pass_2": fls[1]["server_check"]["checks"]})
    write_check(out, summary, rows)
    print(f"REPRODUCTION: {summary['equal_scores']} of {n} answers with every score equal in two passes of {model} "
          f"(D85 repeat check, key v2.5); every call sent temperature 0 and think false: {t0}; "
          f"{'PASSED' if passed else 'NOT PASSED' + ('' if n == CHECK_N else ' (a smoke sample)')}", flush=True)
    return 0 if passed or (n < CHECK_N and all(r["equal"] for r in rows) and all_ok and t0) else 1


def require_check(check_dir: Path, lock, base: str, machine: str, binary: Path, judge: str, ref_f: Path) -> dict:
    """judge_passages.require_check's test with S6's code identity, plus: the check is S6's (kind), and for the main
    judge the reference in this clone is the one the check compared with (or made)."""
    f = check_dir / "repro_check.json"
    if not f.exists():
        raise SystemExit(f"REFUSED: no reproduction check in {check_dir}; run `calibrate` (once) or `check` first "
                         f"(README.md:75-79)")
    c = json.loads(f.read_text())
    if c.get("kind") not in KINDS[judge]:
        raise SystemExit(f"REFUSED: {f} is not an S6 check for the {judge} judge (kind {c.get('kind')!r}); S6 needs "
                         f"one of {KINDS[judge]}")
    from experiments.runner.ollama_client import server_state
    model = JP.judge_of(lock, judge)
    call = lock.ollama(model, role="judge")
    version, digest = server_state(base, call.model)
    want = {"passed": True, "full_sample": True, "model": model, "lock_sha256": lock.sha256, "server": base,
            "ollama_version": version, "model_digest": digest, "options_sent": call.options,
            "system_prompt_sha256": call.system and sha(call.system),
            "system_sent_sha256": call.system and sha(call.system),
            "machine_identity": {"hostname": JP.socket.gethostname(), "machine": machine,
                                 "binary_sha256": sha(binary.read_bytes())},
            "code": code_identity(), "key25_sha256": KEY25_SHA256}
    if judge == "main":
        want["reference_sha256"] = read_reference(ref_f)[1]
    bad = {k: (c.get(k), v) for k, v in want.items() if c.get(k) != v}
    if bad:
        raise SystemExit(f"REFUSED: the reproduction check does not cover this run (check value, now): {bad}")
    return c


# ---------------------------------------------------------------- run

def refuse_out(out: Path) -> None:
    if not any(p.startswith(OUT_MARK) for p in out.resolve().parts):
        raise SystemExit(f"REFUSED: {out} is not under an S6 out (a folder named {OUT_MARK}<set>, s3_guard.py SETS): "
                         f"a v2.5 row never goes into a v2.4 out")


def cmd_run(a) -> int:
    """judge_passages.cmd_run with the answers on key v2.5 and the 132, S6's run identity and check, no STORED."""
    if a.arm is not None:
        raise SystemExit("REFUSED: S6 reads runs only (--run), not --arm")
    refuse_out(a.out)
    base = a.base.rstrip("/")
    lock0 = load()
    which = JP.judge_arg(a)
    model0 = JP.judge_of(lock0, which)
    check = require_check(a.check_dir, lock0, base, a.machine, a.binary, which, a.reference)
    call0 = lock0.ollama(model0, role="judge")
    run_sha = run_identity(lock0, call0)
    jtag = JP.judge_tag(which, model0, call0)
    keys_ = [k for k in a.keys.read_text().splitlines() if k.strip()] if a.keys else None
    items = select(run_answers(a.run, a.rows, a.store), a.draws, keys_, a.answered_only)
    for x in items:                                       # every prompt pair is built and verified before any call
        if JP.answered(x):
            JP.safe_prompts(x)
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    JP.hold_writer(out)
    JP.refuse_other_judge(out, model0)
    res_f, log = out / "judge_passages.jsonl", out / "judge_passages_calls.jsonl"
    mine = {JP.ident(x): x["item_sha256"] for x in items}
    latest = JP.latest_rows(res_f, mine, run_sha, out)
    done = {k for k, d in latest.items() if JP.is_done(d, a.variants)}
    todo = [x for x in items if JP.ident(x) not in done][: a.limit]
    if not todo:                                          # nothing to judge: no fresh load, nothing unloaded
        return finish(a, out, res_f, mine, run_sha, items, None, jtag, check)
    stored: dict = {}                                     # S373's v2.4 prompts: none can match a v2.5 prompt (docstring)
    lock, model, call, fl = JP.start(a, out, "run")
    if lock.sha256 != lock0.sha256 or run_identity(lock, call) != run_sha:
        raise SystemExit("REFUSED: the lock or the code changed while the run started")
    header = {"_provenance": {"script": f"{SCRIPT} run", "inputs": [str(a.run), str(KEY25)],
                              "started": time.strftime("%Y-%m-%dT%H:%M:%S")},
              "model": model, "model_digest": call.digest, "lock_sha256": lock.sha256, "options": call.options,
              "fields": call.fields, "system_prompt_sha256": call.system and sha(call.system), "base": base,
              "machine_identity": fl["machine_identity"], "run_sha256": run_sha,
              "check": {k: check.get(k) for k in ("kind", "n", "equal_scores", "identical_text", "lock_sha256",
                                                  "model_digest", "reference_sha256")},
              "code": code_identity(), "block_head": JP.BLOCK_HEAD, "begin": JP.BEGIN, "end": JP.END,
              "anchor": JP.ANCHOR, "row_range": a.rows, "variants": a.variants, "draws": a.draws,
              "keys": a.keys and str(a.keys), "answered_only": a.answered_only, "rows": len(items),
              "already_done": len(done), "to_do": len(todo), "key_version": KEY_VERSION,
              "questions": {"changed": N_CHANGED, "sha256": CHANGED_SHA256},
              "a_to_reuse": sum(1 for x in todo if a.variants == "ab" and JP.reusable_a(latest.get(JP.ident(x)))),
              "with_stored_score": 0}
    with (out / "judge_passages_headers.jsonl").open("a") as fh:
        fh.write(json.dumps(header, ensure_ascii=False) + "\n")
    print(f"S6 judge on key v2.5 ({'(a) only, (b) deferred' if a.variants == 'a' else '(a) and (b)'}): {len(items)} "
          f"answers to the {N_CHANGED} questions, {len(done)} done, {len(todo)} to judge with {model} "
          f"({header['a_to_reuse']} with their (a) reused)", flush=True)
    for x in todo:
        row = JP.judge_answer(base, call, x, log, stored, a.variants, latest.get(JP.ident(x)))
        row["lock_sha256"], row["run_sha256"], row["key_version"] = lock.sha256, run_sha, KEY_VERSION
        if jtag is not None:
            row["judge"] = jtag
        with res_f.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['at']} {x['config']:13s} {x['question_id']:28s} a {row['a']['status']} "
              f"F={row['faithfulness_a']}  b {row['b']['status']} F={row['faithfulness_b']}  {row['wall_s']} s",
              flush=True)
    rechecked = None
    if not a.no_recheck:
        rechecked = JP.recheck(a, base, items, res_f, out, stored, run_sha)
    return finish(a, out, res_f, mine, run_sha, items, rechecked, jtag, check)


def finish(a, out: Path, res_f: Path, mine: dict, run_sha: str, items: list, rechecked, jtag, check: dict) -> int:
    """judge_passages.finish (its summary and the last line run_s3.sh reads), then S6's block in the summary."""
    rc = JP.finish(a, out, res_f, mine, run_sha, items, rechecked, jtag)
    f = out / "judge_passages_summary.json"
    s = json.loads(f.read_text())
    s["s6"] = {"script": SCRIPT, "key_version": KEY_VERSION, "key25_sha256": KEY25_SHA256,
               "questions": N_CHANGED, "questions_sha256": CHANGED_SHA256,
               "check_kind": check.get("kind"), "reference_sha256": check.get("reference_sha256"),
               "stored": "not read: S373's stored scores are of key v2.4 prompts"}
    f.write_text(json.dumps(s, indent=1) + "\n")
    return rc


# ---------------------------------------------------------------- offline

def selftest(a) -> int:
    """Offline proofs on the real keys (and, with --run, a run): no server, no call."""
    from collections import Counter
    k24, k25 = keys()
    v2 = v2_records()
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}
    ch = changed_ids()
    bad = []
    by = Counter(("concepts" if k25[q]["expected_concepts"] != k24[q]["expected_concepts"] else "")
                 + ("+answer" if k25[q]["expected_answer"] != k24[q]["expected_answer"] else "") for q in ch)
    for q in k25:
        if (k24[q]["question"], k24[q]["answerable"]) != (k25[q]["question"], k25[q]["answerable"]):
            bad.append(f"{q}: question text or answerable flag changed")
        if S373.judged_answerable(q, v1, v2) != (k25[q]["answerable"] in (True, "true", "True")):
            bad.append(f"{q}: S373.judged_answerable differs from v2.5's flag")
        if S373.key_of(q, v2) != (k24[q]["expected_answer"], list(k24[q]["expected_concepts"])):
            bad.append(f"{q}: S373.key_of (all_v2_4) differs from the v2.4 as_v1 text")
        same = key_hash25(q, v2) == S373.key_hash(q, v2)
        if same == (q in ch):
            bad.append(f"{q}: key_hash25 {'equals' if same else 'differs from'} S373's although "
                       f"{'changed' if q in ch else 'unchanged'}")
        if q in ch:
            p4 = J.build_prompt(k25[q]["question"], *S373.key_of(q, v2), "an answer", True, None)
            p5 = J.build_prompt(k25[q]["question"], *key_of25(q), "an answer", True, None)
            if p4 == p5:
                bad.append(f"{q}: changed, but its v2.5 prompt equals its v2.4 prompt")
    # reproduce (README.md:75-79): S508 judged 49 items on v2.5 (committed rows); its key_hash is sha256 of
    # [expected, concepts, answerable] read straight from the v2.5 file (S508:129). This path's text must give it.
    s508 = JP.read_rows(S508_ROWS)
    s508_eq = sum(sha(json.dumps([*key_of25(d["question_id"]), True], ensure_ascii=False))[:16] == d["key_hash"]
                  for d in s508)
    cal = calib_items()
    s440 = s440_lock()
    cal_unch = [x for x in cal if not x["changed"]]
    cal_eq = sum(s440.get(x["answer_key"], {}).get("key_hash") == x["key_hash"] for x in cal_unch)
    print(json.dumps({"changed": len(ch), "changed_sha256": sha(json.dumps(ch)), "by_field": dict(by),
                      "refutations_in_changed": sorted(q for q in ch if S373.refutation(q, v2)),
                      "s508_rows": len(s508), "s508_key_hash_equal": s508_eq,
                      "calibration": len(cal), "calibration_changed": len(cal) - len(cal_unch),
                      "calibration_changed_questions": len({x["question_id"] for x in cal if x["changed"]}),
                      "calibration_unchanged_key_hash_equal_s440": cal_eq, "problems": bad[:10]}))
    ok = not bad and s508_eq == len(s508) == 49 and cal_eq == len(cal_unch)
    if a.run:
        items = run_answers(a.run, None, a.store)
        sel = select(items, None, None, False)
        n_b = 0
        for x in sel:
            if JP.answered(x):
                pa, pb, _, _ = JP.safe_prompts(x)
                n_b += pb is not None
        print(json.dumps({"run": str(a.run), "answers": len(items), "on_the_132": len(sel),
                          "by_draw": dict(Counter(x["draw"] for x in sel)), "answered": sum(map(JP.answered, sel)),
                          "b_prompts": n_b}))
    print(f"S512 SELFTEST {'PASSED' if ok else 'NOT PASSED'}: {len(ch)} questions changed ({dict(by)}); key_hash on "
          f"v2.5 equals S373's on the {len(k25) - len(ch)} unchanged and differs on the {len(ch)}; the S508 key path "
          f"reproduced on {s508_eq} of {len(s508)} rows; {len(cal) - len(cal_unch)} of {len(cal)} calibration answers "
          f"changed, {cal_eq} of {len(cal_unch)} unchanged under S440's key hash"
          + ("" if not bad else f"; {len(bad)} problems, first: {bad[0]}"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("calibrate", "check", "run"):
        p = sub.add_parser(name)
        p.add_argument("--base", default="http://127.0.0.1:11434")
        p.add_argument("--log", required=True, type=Path, help="the server's log, for the fresh load's checks")
        p.add_argument("--binary", required=True, type=Path, help="the server's executable, checked against [server]")
        p.add_argument("--machine", required=True, choices=["macos", "beelink"])
        p.add_argument("--out", required=True, type=Path)
        p.add_argument("--judge", choices=list(JP.JUDGES), default="main")
        p.add_argument("--reference", type=Path, default=REFERENCE, help="the v2.5 reference (calibrate writes it)")
    for name in ("calibrate", "check"):
        sub.choices[name].add_argument("--n", type=int, default=0, help="first n answers only: a smoke test")
    r = sub.choices["run"]
    r.add_argument("--check-dir", required=True, type=Path)
    r.add_argument("--limit", type=int)
    r.add_argument("--rows", help="START:END of the run's answers in its fixed order")
    r.add_argument("--no-recheck", action="store_true")
    r.add_argument("--variants", choices=["ab", "a"], default="ab")
    r.add_argument("--draws", type=lambda v: [int(d) for d in v.split(",")])
    r.add_argument("--keys", type=Path)
    r.add_argument("--answered-only", action="store_true")
    s = sub.add_parser("selftest")
    for p in (r, s):
        src = p.add_mutually_exclusive_group(required=p is r)
        src.add_argument("--arm", type=Path, help="refused: S6 reads runs only")
        src.add_argument("--run", type=Path)
        p.add_argument("--store", type=Path)
    a = ap.parse_args(argv)
    return {"calibrate": cmd_calibrate, "check": cmd_check, "run": cmd_run, "selftest": selftest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
