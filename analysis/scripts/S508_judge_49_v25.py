#!/usr/bin/env python3
"""S508 - the lock's judge on the 49 rated answers, on key v2.5 (D183 FD11 c).

WHY. FD11 c (Valerio, 30 October): the judge scores set against the raters in Figure 2 are the lock's call on key
v2.5 only; S373's pre-lock rows (num_ctx 32,768, key v2.4) are dropped. The raters read key v2.5 under amendment 9
(findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md, drafted). The 49 answers keep no passage text (the deposited exp04 file
stores a passage count only: findings/recompute/rerun_effort_2026-10-30/rerun_effort.md, section (c)), so only the
plain call (a) is made: 49 calls.

THE CALL. Exactly the S3 judging's plain call (a): experiments/scorers/judge_passages.py judge_call, which sends
experiments/runner/ollama_client.generate with lock.ollama(LOCK.toml [judge] model, role="judge"); the prompt is
scripts/S141_runner/judge.py build_prompt (the archived template under its sha256 pin, the whole answer, no cut), the
answerable template on all 49; the parser never invents a score; a failed or unparseable call is tried once more.
This script sets no setting of its own.

THE ITEMS. Read as S08's join reads them, without any rating: S08.reconstruct_sample() (the seed-42 sample of the
deposited exp04 answers, E001 to E050: question id, strategy, question and answer text), less the item S385's master
record excludes (E038, SY_010, D7), each question id checked against S385's record
(findings/recompute/S385_human_eval_master_v22.json, question_ids). Expected answer and key concepts from key v2.5
(data/ground_truth_v2/ground_truth_v2_5_as_v1.json, sha256 pinned below as amendment 9 states it). Gates, before any
call: 49 items on 36 questions; every question answerable in v2.5; the exp04 question equals the key's; v2.5's expected
answer equals v2.3's (the raters' packets, S385 --key 2.3) character for character, as amendment 9 says. Nothing under
response/ is read.

THE ROUTINE (experiments/runner/job.py, F1; README.md:75-79 "reproduce before writing").
  1. require a passed 107-answer reproduction check of judge_passages (`judge_passages.py check`) in --check-dir for
     this machine, server, Ollama version, model digest, lock, options, system prompt and judge code
     (judge_passages.require_check);
  2. a fresh load and the server checks (judge_passages.start: job.py fresh_load, check_server; after the first call
     job.py after_first_call);
  3. the items in E-number order, each row written when its call returns; resumable: an item whose latest row is ok
     under the same item_sha256 and run_sha256 is skipped; a row of the same item under another item or run sha256
     refuses the run (one file never mixes two definitions);
  4. unless --no-recheck: another fresh load, the first RECHECK_N judged items judged again and compared (status and
     every score); a difference exits 1. The recheck first marks recheck_summary.json as started (passed null), so a
     recheck cut off part-way leaves no passed recheck behind.
  5. "S508 DONE" (exit 0) only when all 49 items are judged ok AND recheck_summary.json holds a passed recheck of this
     run_sha256 made after all 49 were judged. A run that finds every item done but no such recheck (a run cut off
     during the recheck, or an earlier --limit run whose recheck saw fewer items) makes the recheck itself, as
     --recheck-only does; with --no-recheck it prints "S508 NOT RECHECKED" and exits 1. --recheck-only judges no item:
     it refuses while items are left, and otherwise makes the recheck (again, even after a passed one).

    uv run --frozen python scripts/S508_judge_49_v25.py --dry-run
    uv run --frozen python scripts/S508_judge_49_v25.py --base http://127.0.0.1:11434 \
        --log /opt/homebrew/var/log/ollama.log --binary /opt/homebrew/bin/ollama --machine macos \
        --check-dir <a judge_passages check dir of this server>

SECOND JUDGE (D273, rulings 6 Nov SUPP3-B O1, D274). --judge second sends LOCK.toml [judge] second_model (qwen3.8:27b) in
the same call at the same [judge] settings (judge_passages.judge_of, lock.ollama role "judge"): the same items, the same
prompts, the same parser, the same routine; its --check-dir must hold a passed check of the second judge on this server
(judge_passages.py check --judge second, D85's repeat check). It writes to findings/recompute/S508_judge_49_v25_second/
(--out), one judge per folder: a folder whose headers name another model refuses. --judge main (the default) is the run
above, unchanged.

    uv run --frozen python scripts/S508_judge_49_v25.py --judge second --base http://127.0.0.1:11434 \
        --log <that server's log> --binary <ollama> --machine macos --check-dir <a passed second-judge check there>

Writes findings/recompute/S508_judge_49_v25/: rows.jsonl (one line per judged item: eval_id, question_id, strategy,
the judge's scores and text, tokens, timings, status, item_sha256, run_sha256, lock_sha256), calls.jsonl (every call
record, judge_passages' format), headers.jsonl (one line per start), fresh_load_*.json, recheck.jsonl,
recheck_summary.json and summary.json (provenance: this script's sha256, every input's sha256, the lock, the check it
relied on, counts). Judge scores only; no human rating is read or written, so the folder is committable. Exit codes:
0 done (all 49 ok and a passed recheck after them), 1 a refusal, a failed or missing recheck or items left unjudged,
75 another process writes the folder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import S08_human_eval_analysis as S08  # noqa: E402
import S141_runner.judge as J  # noqa: E402
from experiments.scorers import judge_passages as JP  # noqa: E402
from experiments.runner.lock import load  # noqa: E402
from machine import rel  # noqa: E402

KEY25 = ROOT / "data/ground_truth_v2/ground_truth_v2_5_as_v1.json"
KEY25_SHA256 = "a42161841980792f5da521819c97b16dc54999b45838b8eb87cd4315f798270a"    # amendment 9; S504 --final
KEY23 = ROOT / "data/ground_truth_v2/ground_truth_v2_3_as_v1.json"                  # the raters' (S385 --key 2.3)
KEY24 = ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json"                  # S373's, for the changed flag
S385_RECORD = ROOT / "findings/recompute/S385_human_eval_master_v22.json"
OUT = ROOT / "findings/recompute/S508_judge_49_v25"
OUT_SECOND = ROOT / "findings/recompute/S508_judge_49_v25_second"   # --judge second (D274)
N_ITEMS, N_QUESTIONS = 49, 36
RECHECK_N = 10
FINAL = {"ok"}
SCRIPT = "scripts/S508_judge_49_v25.py"


class Refused(Exception):
    pass


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8", "surrogatepass") if isinstance(b, str) else b).hexdigest()


def items_49() -> tuple[list[dict], dict]:
    """The 49 rated answers with key v2.5, in E-number order, and the inputs read (path -> sha256). No rating read."""
    raw25 = KEY25.read_bytes()
    if sha(raw25) != KEY25_SHA256:
        raise Refused(f"{KEY25.name} sha256 {sha(raw25)[:12]} is not amendment 9's {KEY25_SHA256[:12]}")
    k25 = {q["id"]: q for q in json.loads(raw25)["questions"]}
    k23 = {q["id"]: q for q in json.loads(KEY23.read_text())["questions"]}
    k24 = {q["id"]: q for q in json.loads(KEY24.read_text())["questions"]}
    rec = json.loads(S385_RECORD.read_text())
    excluded = {e["eval_id"] for e in rec["excluded"]}
    out = []
    for s in S08.reconstruct_sample():
        e, qid = s["eval_id"], s["question_id"]
        if e in excluded:
            continue
        if rec["question_ids"].get(e) != qid:
            raise Refused(f"{e}: S385's record names {rec['question_ids'].get(e)}, the reconstruction {qid}")
        q = k25.get(qid)
        if q is None:
            raise Refused(f"{e}: {qid} is not in key v2.5")
        if q.get("answerable") not in (True, "true", "True"):
            raise Refused(f"{e}: {qid} is not answerable in key v2.5; the answerable prompt would be wrong")
        if q["question"].strip() != s["question"]:
            raise Refused(f"{e}: the exp04 question differs from key v2.5's question text")
        if q["expected_answer"] != k23[qid]["expected_answer"]:
            raise Refused(f"{e}: {qid}'s expected answer in v2.5 differs from v2.3's (the raters'); amendment 9 says "
                          f"they are equal")
        x = {"eval_id": e, "question_id": qid, "config": s["config"], "category": s["category"],
             "question": s["question"], "answer": s["generated_answer"], "expected": q["expected_answer"],
             "concepts": list(q["expected_concepts"]), "answerable": True,
             "key_changed_from_v2_4": (q["expected_concepts"] != k24[qid]["expected_concepts"]
                                       or q["expected_answer"] != k24[qid]["expected_answer"])}
        x["key_hash"] = sha(json.dumps([x["expected"], x["concepts"], x["answerable"]], ensure_ascii=False))[:16]
        x["item_sha256"] = sha(json.dumps([x[k] for k in ("question", "expected", "concepts", "answer", "answerable")],
                                          ensure_ascii=False))
        out.append(x)
    if len(out) != N_ITEMS or len({x["question_id"] for x in out}) != N_QUESTIONS:
        raise Refused(f"{len(out)} items on {len({x['question_id'] for x in out})} questions, not "
                      f"{N_ITEMS} on {N_QUESTIONS}")
    if any(not x["answer"].strip() for x in out):
        raise Refused("an item has no answer text")
    inputs = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (KEY25, KEY23, KEY24, S385_RECORD)}
    inputs[rel(Path(S08.GEN_JSON))] = sha(Path(S08.GEN_JSON).read_bytes())
    return out, inputs


def prompt(x: dict) -> str:
    return J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)


def read_rows(path: Path) -> list[dict]:
    return list(map(json.loads, filter(str.strip, path.read_text().splitlines()))) if path.exists() else []


def code_sha() -> dict:
    return {SCRIPT: sha((ROOT / SCRIPT).read_bytes()), "judge_passages": JP.code_identity()}


def latest(rows_f: Path, items: list[dict], run_sha: str) -> dict:
    """eval_id -> latest row; refuses a row of one of these items judged on another item text, key, lock or code."""
    mine = {x["eval_id"]: x["item_sha256"] for x in items}
    out = {}
    for d in read_rows(rows_f):
        if d["eval_id"] not in mine:
            raise Refused(f"{rows_f} holds {d['eval_id']}, not one of the 49")
        if d.get("item_sha256") != mine[d["eval_id"]] or d.get("run_sha256") != run_sha:
            raise Refused(f"{rows_f} holds {d['eval_id']} judged on another item, key, lock or code (item "
                          f"{str(d.get('item_sha256'))[:12]}, run {str(d.get('run_sha256'))[:12]}); use a new --out")
        out[d["eval_id"]] = d
    return out


def judge_one(base: str, call, x: dict, log: Path, variant: str) -> dict:
    p = prompt(x)
    res = JP.judge_call(base, call, p, True, None, log,
                        {"answer": x["eval_id"], "variant": variant, "key_hash": x["key_hash"],
                         "item_sha256": x["item_sha256"]})
    return {"eval_id": x["eval_id"], "question_id": x["question_id"], "config": x["config"],
            "category": x["category"], "key_changed_from_v2_4": x["key_changed_from_v2_4"], "key_hash": x["key_hash"],
            "item_sha256": x["item_sha256"], "answer_chars": len(x["answer"]), "status": res["status"],
            "scores": res["scores"], "justification": res["justification"], "text": res["text"],
            "judge_model": call.model, "attempts": res["attempts"], "prompt_sha256": res["prompt_sha256"], "prompt_chars": res["prompt_chars"],
            "prompt_tokens": res["prompt_tokens"], "output_tokens": res["output_tokens"],
            "stop_reason": res["stop_reason"], "error": res["error"], "wall_s": res["wall_s"], "load_s": res["load_s"],
            "model_digest": res["model_digest"], "server": res["server"], "ollama_version": res["ollama_version"],
            "at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def dry_run(items: list[dict], inputs: dict, which: str = "main") -> int:
    lock = load()
    call = lock.ollama(JP.judge_of(lock, which), role="judge")
    sizes = []
    print(f"S508 dry run: {len(items)} items, key v2.5 {KEY25_SHA256[:12]}, judge {call.model} at the lock's "
          f"settings {call.options} {call.fields}; no server contacted, no call made")
    for x in items:
        p = prompt(x)
        sizes.append(len(p))
        print(f"  {x['eval_id']} {x['question_id']:30s} {x['config']:14s} prompt {len(p):6d} chars, answer "
              f"{len(x['answer']):6d}, concepts {len(x['concepts']):2d}, key changed from v2.4: "
              f"{'yes' if x['key_changed_from_v2_4'] else 'no'}")
    print(f"prompts: {len(sizes)}, total {sum(sizes):,} chars, largest {max(sizes):,}, smallest {min(sizes):,}; "
          f"items whose key changed from v2.4: {sum(x['key_changed_from_v2_4'] for x in items)}; strategies "
          f"{dict(Counter(x['config'] for x in items))}")
    print("inputs: " + ", ".join(f"{k} {v[:12]}" for k, v in inputs.items()))
    return 0


def recheck_state(out: Path, run_sha: str) -> dict | None:
    """recheck_summary.json if it belongs to this run_sha256, else None."""
    f = out / "recheck_summary.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text())
    return d if d.get("run_sha256") == run_sha else None


def recheck_valid(st: dict | None) -> bool:
    """A recheck that lets S508 say DONE: passed, and made after all 49 items were judged ok."""
    return bool(st) and st.get("passed") is True and st.get("after_complete") is True


def recheck(a, base: str, items: list[dict], rows_f: Path, out: Path, run_sha: str) -> dict:
    """F1: after another fresh load, the first RECHECK_N judged items judged again and compared with what was written.
    recheck_summary.json is marked started (passed null) before the first call, so a cut-off leaves no pass behind."""
    (out / "recheck_summary.json").write_text(json.dumps(
        {"n": 0, "equal": 0, "passed": None, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "run_sha256": run_sha,
         "note": "started; a recheck cut off here never finished"}, indent=1) + "\n")
    lock, model, call, fl = JP.start(a, out, "recheck")
    last = latest(rows_f, items, run_sha)
    after_complete = all(x["eval_id"] in last and last[x["eval_id"]]["status"] in FINAL for x in items)
    picked = [x for x in items if x["eval_id"] in last][:RECHECK_N]
    n = eq = 0
    for x in picked:
        now = judge_one(base, call, x, out / "recheck_calls.jsonl", "recheck")
        prev = last[x["eval_id"]]
        same = now["status"] == prev["status"] and now["scores"] == prev["scores"]
        n, eq = n + 1, eq + same
        with (out / "recheck.jsonl").open("a") as fh:
            fh.write(json.dumps({"eval_id": x["eval_id"], "item_sha256": x["item_sha256"], "run_sha256": run_sha,
                                 "equal": same, "now": now["scores"], "written": prev["scores"],
                                 "same_text": now["text"] == prev["text"], "at": now["at"]}) + "\n")
        print(f"recheck {x['eval_id']} {'equal' if same else 'DIFFERS'}", flush=True)
    res = {"n": n, "equal": eq, "passed": (eq == n) if n else None, "run_sha256": run_sha,
           "after_complete": after_complete, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (out / "recheck_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"RECHECK: {eq} of {n} items give the same status and scores after a fresh load; "
          f"{ {True: 'PASSED', False: 'NOT PASSED', None: 'nothing to recheck'}[res['passed']] }", flush=True)
    return res


DECISION = {"main": "D183 FD11 c: the lock's plain judge call on key v2.5, the 49 rated answers",
            "second": "D273, SUPP3-B O1, D274: the lock's second judge, the same plain call on key v2.5, the 49 rated "
                      "answers"}


def summarise(out: Path, items: list[dict], inputs: dict, run_sha: str, lock_sha: str, check: dict | None,
              argv: list[str], a_judge=None) -> int:
    """summary.json; the recheck is read from recheck_summary.json (this run_sha256's), never carried forward."""
    rows = latest(out / "rows.jsonl", items, run_sha)
    ok = [d for d in rows.values() if d["status"] in FINAL]
    rechecked = recheck_state(out, run_sha)
    summary = {"_provenance": {"script": SCRIPT, "script_sha256": sha((ROOT / SCRIPT).read_bytes()),
                               "command": "uv run --frozen python " + " ".join([SCRIPT] + argv),
                               "written": time.strftime("%Y-%m-%dT%H:%M:%S"), "inputs": inputs,
                               "decision": DECISION[getattr(a_judge, "judge", "main")],
                               "code": code_sha()},
               "key": {"path": str(KEY25.relative_to(ROOT)), "sha256": KEY25_SHA256},
               "judge": {"call": "judge_passages.judge_call, plain call (a), no passages", "lock_sha256": lock_sha,
                         "run_sha256": run_sha,
                         **({} if getattr(a_judge, "judge", "main") == "main" else
                            {"which": a_judge.judge, "model": JP.judge_of(load(), a_judge.judge)})},
               "check": check, "items": len(items), "rows": len(rows), "ok": len(ok),
               "status": dict(Counter(d["status"] for d in rows.values())),
               "left": [x["eval_id"] for x in items if x["eval_id"] not in rows or rows[x["eval_id"]]["status"] not in FINAL],
               "complete": len(ok) == len(items), "recheck": rechecked,
               "models": dict(Counter(d["model_digest"] for d in rows.values())),
               "servers": dict(Counter(d["server"] for d in rows.values())),
               "items_key_changed_from_v2_4": sum(x["key_changed_from_v2_4"] for x in items)}
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"SUMMARY: {len(ok)} of {len(items)} items judged ok; status {summary['status']}; recheck "
          f"{'none' if not rechecked else str(rechecked['equal']) + ' of ' + str(rechecked['n'])}", flush=True)
    if rechecked is not None and rechecked.get("passed") is False:
        print("S508 NOT PASSED: the recheck differs", flush=True)
        return 1
    if not summary["complete"]:
        print(f"S508 NOT COMPLETE: {len(summary['left'])} items left ({', '.join(summary['left'][:8])}); run again "
              f"to resume", flush=True)
        return 1
    if not recheck_valid(rechecked):
        print("S508 NOT RECHECKED: all items judged, but no passed recheck made after all of them (run again without "
              "--no-recheck, or with --recheck-only)", flush=True)
        return 1
    print("S508 DONE", flush=True)
    return 0


def run(a, items: list[dict], inputs: dict, argv: list[str]) -> int:
    base = a.base.rstrip("/")
    lock0 = load()
    model0 = JP.judge_of(lock0, a.judge)
    call0 = lock0.ollama(model0, role="judge")
    other = sorted({h.get("model") for h in read_rows(a.out / "headers.jsonl")} - {model0, None})
    if other:
        raise Refused(f"{a.out} holds rows of the judge {', '.join(other)}, not {model0}; one judge per folder")
    check = JP.require_check(a.check_dir, lock0, base, a.machine, a.binary, a.judge)
    run_sha = sha(json.dumps({"judge_passages_run_identity": JP.run_identity(lock0, call0), "s508": code_sha(),
                              "key25": KEY25_SHA256}, sort_keys=True))
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    JP.hold_writer(out)
    rows_f = out / "rows.jsonl"
    done = {e for e, d in latest(rows_f, items, run_sha).items() if d["status"] in FINAL}
    left = [x for x in items if x["eval_id"] not in done]
    todo = left[: a.limit]
    check_brief = {k: check.get(k) for k in ("n", "equal_scores", "identical_text", "lock_sha256", "model_digest",
                                             "server", "machine_identity")}
    check_brief["dir"] = str(a.check_dir)
    if a.recheck_only:
        if left:
            raise Refused(f"--recheck-only: {len(left)} items are not judged ok yet (first {left[0]['eval_id']}); "
                          f"run without --recheck-only to judge them")
        print(f"S508 --recheck-only: all {len(done)} items judged; rechecking {RECHECK_N} after a fresh load", flush=True)
        recheck(a, base, items, rows_f, out, run_sha)
        return summarise(out, items, inputs, run_sha, lock0.sha256, check_brief, argv, a)
    if not todo:
        if recheck_valid(recheck_state(out, run_sha)) or a.no_recheck:
            print(f"S508: all {len(done)} items already judged under this run; no fresh load, nothing unloaded")
            return summarise(out, items, inputs, run_sha, lock0.sha256, check_brief, argv, a)
        print(f"S508: all {len(done)} items already judged under this run, but no passed recheck after them (a run "
              f"cut off during the recheck?): rechecking now, as --recheck-only", flush=True)
        recheck(a, base, items, rows_f, out, run_sha)
        return summarise(out, items, inputs, run_sha, lock0.sha256, check_brief, argv, a)
    lock, model, call, fl = JP.start(a, out, "S508")
    if lock.sha256 != lock0.sha256 or call.options != call0.options or call.fields != call0.fields:
        raise Refused("the lock changed while the run started")
    header = {"_provenance": {"script": SCRIPT, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "inputs": inputs},
              "model": model, "model_digest": call.digest, "lock_sha256": lock.sha256, "options": call.options,
              "fields": call.fields, "system_prompt_sha256": call.system and sha(call.system), "base": base,
              "machine_identity": fl.get("machine_identity"), "run_sha256": run_sha, "check": check_brief,
              "code": code_sha(), "items": len(items), "already_done": len(done), "to_do": len(todo)}
    with (out / "headers.jsonl").open("a") as fh:
        fh.write(json.dumps(header, ensure_ascii=False) + "\n")
    print(f"S508: {len(items)} items, {len(done)} done, {len(todo)} to judge with {model} (lock {lock.sha256[:12]})",
          flush=True)
    for k, x in enumerate(todo, 1):
        row = judge_one(base, call, x, out / "calls.jsonl", "a")
        row["lock_sha256"], row["run_sha256"] = lock.sha256, run_sha
        with rows_f.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['at']} {k}/{len(todo)} {x['eval_id']} {x['question_id']:28s} {x['config']:14s} {row['status']} "
              f"{row['wall_s']} s", flush=True)
    if not a.no_recheck:
        recheck(a, base, items, rows_f, out, run_sha)
    return summarise(out, items, inputs, run_sha, lock.sha256, check_brief, argv, a)


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="print the 49 prompts' sizes; no server, no call")
    ap.add_argument("--base", help="the judge's Ollama server, e.g. http://127.0.0.1:11434 (no default)")
    ap.add_argument("--log", type=Path, help="that server's log, for the fresh load's checks")
    ap.add_argument("--binary", type=Path, help="that server's executable, checked against LOCK.toml [server]")
    ap.add_argument("--machine", choices=["macos", "beelink"])
    ap.add_argument("--check-dir", type=Path, help="a passed judge_passages.py check of this server and code")
    ap.add_argument("--out", type=Path, default=None, help=f"default {OUT.name} (main) or {OUT_SECOND.name} (second)")
    ap.add_argument("--judge", choices=["main", "second"], default="main",
                    help="main: LOCK.toml [judge] model (default); second: [judge] second_model (D274)")
    ap.add_argument("--limit", type=int, help="judge at most this many items (a smoke test; resumes later)")
    ap.add_argument("--no-recheck", action="store_true")
    ap.add_argument("--recheck-only", action="store_true",
                    help="judge no item: with all 49 judged ok, make the recheck (refused while items are left)")
    a = ap.parse_args(argv)
    if a.recheck_only and (a.no_recheck or a.limit is not None):
        ap.error("--recheck-only takes neither --no-recheck nor --limit")
    if not a.dry_run:
        miss = [f"--{k.replace('_', '-')}" for k in ("base", "log", "binary", "machine", "check_dir")
                if getattr(a, k) is None]
        if miss:
            ap.error(f"a run needs {', '.join(miss)} (or --dry-run)")
    a.out = a.out or (OUT if a.judge == "main" else OUT_SECOND)
    if a.judge == "second" and a.out.resolve() == OUT.resolve():
        ap.error("--judge second never writes into the main judge's folder")
    return a


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    a = parse(argv)
    try:
        items, inputs = items_49()
        if a.dry_run:
            return dry_run(items, inputs, a.judge)
        return run(a, items, inputs, argv)
    except Refused as e:
        print(f"REFUSED: {e}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
