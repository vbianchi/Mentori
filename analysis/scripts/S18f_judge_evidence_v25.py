#!/usr/bin/env python3
"""S18f (key v2.5): the judge-evidence experiment S18e ran again with S512's judge call on key v2.5.

WHY. S18e (scripts/S18e_judge_evidence_devstral.py, findings/recompute/S18e_results.md) re-judged S18's 528 answerable
exp04 answers with devstral-small-2:24b on key v2.4, with S373's own call settings (num_ctx 32768 for arm A, 65536 for
the evidence arms, num_predict 8192). The paper's judge is now S512's: key v2.5 and LOCK.toml [judge] (num_ctx 131072,
num_predict 16384, temperature 0, think false, truncate false, shift false). This script is S18e under that judge.

WHAT IS S18e's, unchanged:
  - the answers: exp04's answerable answers as S18e.load reads them (S18b's reading), the complete answer;
  - the question set: S18's frozen 62 "full" questions (S18_frozen_analysis_set.json, sha256 checked), less D7
    (S373.AS_V1 "dropped_d7": CD_015), less any question key v2.5 drops (not in ground_truth_v2_5_as_v1.json, or not
    answerable there). The plan and the results name each question removed and why;
  - the evidence blocks, by S18e.build_blocks: S18b.build_evidence's whole text for a "full" question, and for the one
    "selected" block the chunk subset S18e recovers from S18's deposited prompt sha256 (no bge-m3). Gate G3 (S18e's)
    rebuilds every deposited S18 prompt of arms B, B2, C and D byte for byte from these blocks, so each block is the one
    S18b sent; G6 holds each block's sha256 equal to S18e's ledger (S18e_devstral.jsonl evidence_sha256);
  - the donors, S18b.mismatch_partner on S18's sizing and order (G6 holds them equal to S18e's arm D rows);
  - the prompt layout: S18b.build_prompt, the "## Source Material" section inserted before "## Generated Answer";
  - the analysis: S18c.compare (share scored faithfulness 5, question-cluster bootstrap of 2,000 resamples, seed 42,
    TOST at 5 points on faithfulness), C vs D primary, S18e's 3-point rule on B vs B2.

WHAT CHANGES, and nothing else:
  - the key: expected answer and concepts from key v2.5 as S512 reads them (S512.key_of25, file sha256 pinned there),
    key_hash by S512.key_hash25. The question text is key v2.5's (G7: equal to the one S18e sent for every question);
  - the judge call: S512's. Every call goes through judge_passages.judge_call with lock.ollama([judge] model,
    role="judge") after judge_passages.start (fresh load, server checks, the check again after the first call), and
    `run` refuses unless S512.require_check passes on --check-dir (a passed S512 check or calibrate on this port, under
    this lock, code, server, binary and machine, against the v2.5 reference). The prompt sent is the plain call (S512's
    call (a): S141_runner.judge.build_prompt on key v2.5; G5 holds arm B equal to it byte for byte), with S18b's
    evidence section added for C and D. No cut anywhere: a prompt longer than num_ctx fails visibly (an HTTP error,
    truncate false), a reply that reaches num_predict is status "length" and is never scored;
  - the arms. B no evidence; C the question's own source block; D the wrong-paper block; B2 B again (the noise floor;
    every run starts with a fresh load, so B2 never replays B's cache). Arm A is dropped: in S18e it was B at num_ctx
    32768 instead of 65536, the only difference between them; under the lock every call has num_ctx 131072, so A's
    prompt and options would be B's byte for byte (S18e measured A vs B 366 of 366 identical).

GATES, first in every subcommand, no model call. Nothing is planned, judged or written unless all pass:
  G1, G2, G3  S18e's (S18e.gate_numbers, S18e.gate_prompts): the frozen set's sha256; S18c.compare reproduces
              S18_results_full.json and the printed S18 numbers; every deposited S18 prompt rebuilt byte for byte.
  G4  S18b's template is the archived one judge_passages sends (J._template).
  G5  every arm B prompt is S512's plain call on key v2.5; every C and D prompt is B with one section (S18b's head,
      the block, a blank line) inserted at the template's "## Generated Answer", and removing it gives B.
  G6  every block sha256 and every donor equal S18e's ledger, for every source S18e sent.
  G7  the set is the frozen 62 less D7 less v2.5's drops; v2.5's question text is the one S18e sent; v2.5 answerable.
  G8  reproduce before writing (README.md:75-79): on every question v2.5 leaves unchanged, every prompt of B, C, D
      equals S18e's prompt of the same arm byte for byte (S18e_devstral.jsonl prompt_sha256; B2 shares B's prompt).
`analyze` also reproduces S18e_results.json's shares and contrasts from S18e's ledger with this file's analysis code
before it writes anything.

    uv run --frozen python scripts/S18f_judge_evidence_v25.py plan [--shards N] [--no-exact] [--models-dir DIR]
    uv run --frozen python scripts/S18f_judge_evidence_v25.py run --arm B|C|D|B2 --base URL --log LOG --binary BIN \\
        --machine macos|beelink --shard I/N --check-dir DIR --out DIR [--limit N] [--no-recheck]
    uv run --frozen python scripts/S18f_judge_evidence_v25.py analyze DIR [DIR ...]

SHARDS. --shard I/N (0 <= I < N) takes the questions whose position in the sorted question list is I modulo N, all six
answers of each; every item is in exactly one shard (selftest). A run writes <out>/<arm>_shard<I>of<N>/ (one writer,
judge_passages.hold_writer): judge_evidence_v25.jsonl (one row per call: item sha256, run sha256, scores, stop reason,
tokens), the call log, the headers, the fresh-load records, the recheck and a summary. Resumable: a row counts as done
when its status is ok under the same item_sha256 and run_sha256; a row of the same item under another item or run
sha256 refuses the run (one file, one definition). item_sha256 holds the arm, question, config, answer, key hash,
evidence source and block sha256, and the prompt's sha256; run_sha256 holds the lock, the options, fields and system
prompt sent, and the code that defines a call (call_code_identity: judge_passages, S18b, S18e, S512 and S18's inputs),
not this file, so an edit to the analysis leaves judged rows usable. A run that judged ends with a recheck: another
fresh load, the first RECHECK_N ok items judged again, any difference exits 1.

Writes: plan, findings/recompute/S18f_v25_plan.{json,md}; analyze, findings/recompute/S18f_v25_results.{json,md}
(refused while any arm lacks an ok row for any of its items). The "_v25" stem keeps them apart from
experiments/scorers/judge_evidence.py (D96's S18f), which writes S18f_plan, S18f_tokens and S18f_results.
plan and analyze make no network call.
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
for _p in (str(ROOT / "scripts"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import S141_runner.judge as J  # noqa: E402
import S18b_rejudge as S18b  # noqa: E402
import S18c_analyze as S18c  # noqa: E402
import S18e_judge_evidence_devstral as X  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402
import S512_s6_rejudge_v25 as S512  # noqa: E402
from experiments.runner.lock import load  # noqa: E402
from experiments.scorers import judge_passages as JP  # noqa: E402

SCRIPT = "scripts/S18f_judge_evidence_v25.py"
RECOMPUTE = ROOT / "findings/recompute"
S18E_LEDGER = RECOMPUTE / "S18e_devstral.jsonl"
S18E_RESULTS = RECOMPUTE / "S18e_results.json"
PLAN_STEM, RESULTS_STEM = "S18f_v25_plan", "S18f_v25_results"
ARMS = ("B", "C", "D", "B2")
EVIDENCE = {"B": None, "C": "correct", "D": "mismatch", "B2": None}
CONTRASTS = (("B", "B2", "noise floor: identical inputs, two runs"),
             ("C", "B", "evidence effect, total"),
             ("D", "B", "irrelevant-text effect: same bulk, wrong paper"),
             ("C", "D", "PRIMARY: evidence content effect"))
NOISE_PP = 3.0                                  # S18e's resolvability rule: |B - B2| within 3 points
ANCHOR = JP.ANCHOR                              # "## Generated Answer\n", where S18b inserts its section
ROWS, CALLS, HEADERS = "judge_evidence_v25.jsonl", "judge_evidence_v25_calls.jsonl", "judge_evidence_v25_headers.jsonl"
RECHECK_N = 10
KEY_VERSION = "v2.5"
SENTINEL = "\x00S18f25\x00"


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8", "surrogatepass") if isinstance(b, str) else b).hexdigest()


def file_sha(p: Path) -> str:
    return X.file_sha(p)


def is_true(v) -> bool:
    return v in (True, "true", "True")


# ---------------------------------------------------------------- the set, the key, the prompts

def question_set(S: dict) -> dict:
    """S18's frozen 62, less D7, less what key v2.5 drops (absent, or not answerable)."""
    _, k25 = S512.keys()
    frozen = sorted(S["frozen"]["primary_set_full"])
    d7 = sorted(set(frozen) & set(S["dropped"]))
    rest = [q for q in frozen if q not in d7]
    v25_drop = {q: ("not in key v2.5" if q not in k25 else "not answerable in key v2.5")
                for q in rest if q not in k25 or not is_true(k25[q]["answerable"])}
    qids = [q for q in rest if q not in v25_drop]
    return {"frozen": frozen, "dropped_d7": d7, "dropped_v25": v25_drop, "qids": qids}


def q25(qid: str) -> dict:
    ea, ec = S512.key_of25(qid)
    return {"question": S512.keys()[1][qid]["question"], "expected_answer": ea, "expected_concepts": ec}


def section_head(template: str) -> str:
    """The text S18b.build_prompt puts before the evidence, cut out of its own output."""
    p = S18b.build_prompt(template, {"question": "q", "expected_answer": "e", "expected_concepts": []}, "a", SENTINEL, None)
    head = p.split(SENTINEL)[0]
    return head[head.index("## Source Material"):]


def anchor_at(template: str, q: dict) -> int:
    """Where the template's "## Generated Answer" lands in a prompt of q (independent of the answer)."""
    head = template[:template.index(ANCHOR)]
    text = ", ".join(q["expected_concepts"]) if q["expected_concepts"] else "N/A"
    return len(head.replace("{question}", q["question"]).replace("{expected_answer}", q["expected_answer"] or "")
               .replace("{expected_concepts}", text))


def donor_of(S: dict, qid: str, arm: str) -> str | None:
    kind = EVIDENCE[arm]
    return X.donor(S, qid, kind) if kind else None


def item_sha(it: dict) -> str:
    return sha(json.dumps([it[k] for k in ("arm", "question_id", "config", "answer_sha256", "key_hash",
                                           "evidence_source_qid", "evidence_sha256", "prompt_sha256")]))


def build_items(S: dict, blocks: dict, qids: list[str]) -> tuple[list[dict], list]:
    """Every call, arm-major, question then config; with G5's per-prompt checks."""
    template = S["template"]
    head = section_head(template)
    v2 = S512.v2_records()
    items, bad = [], []
    for arm in ARMS:
        for qid in qids:
            q = q25(qid)
            kh = S512.key_hash25(qid, v2)
            k = anchor_at(template, q)
            src = donor_of(S, qid, arm)
            b = blocks[src] if src else None
            for cfg in S["configs"]:
                ans = S["answers"][(qid, cfg)]
                noev = S18b.build_prompt(template, q, ans, "", None)
                if noev != J.build_prompt(q["question"], q["expected_answer"], q["expected_concepts"], ans, True, None):
                    bad.append(("B is not S512's plain call", arm, qid, cfg))
                if noev[k:k + len(ANCHOR)] != ANCHOR:
                    bad.append(("anchor not at the template's place", arm, qid, cfg))
                if b is None:
                    p = noev
                else:
                    p = S18b.build_prompt(template, q, ans, b["text"], None)
                    section = head + b["text"] + "\n\n"
                    if p != noev[:k] + section + noev[k:] or p[:k] + p[k + len(section):] != noev:
                        bad.append(("not B plus one section at the anchor", arm, qid, cfg))
                it = {"key": f"S18f25|{arm}|exp04|{cfg}|{qid}", "arm": arm, "question_id": qid, "config": cfg,
                      "key_hash": kh, "answer_sha256": sha(ans), "answer_chars": len(ans),
                      "evidence": EVIDENCE[arm], "evidence_source_qid": src,
                      "evidence_mode": b["mode"] if b else None, "evidence_sha256": b["sha256"] if b else None,
                      "evidence_chars": len(b["text"]) if b else 0,
                      "evidence_files": list(S["sizing"][src]["source_files"]) if src else None,
                      "prompt": p, "prompt_sha256": sha(p), "prompt_chars": len(p), "noev_chars": len(noev)}
                it["item_sha256"] = item_sha(it)
                items.append(it)
    return items, bad


def s18e_rows() -> list[dict]:
    return [json.loads(line) for line in S18E_LEDGER.open() if line.strip()]


def prepare(limit: int = 20_000_000) -> dict:
    """Load, build the blocks and the items, run every gate. Raises SystemExit on any failed gate."""
    t0 = time.time()
    S = X.load()
    qs = question_set(S)
    s18_set = set(qs["frozen"])
    checks = X.gate_numbers(S)
    srcs = {X.donor(S, q, kind) for q in s18_set for kind in ("correct", "mismatch")}
    blocks = X.build_blocks(S, srcs, limit, None)
    g3, g3n = X.gate_prompts(S, s18_set, blocks)
    checks += g3
    checks.append(("G4 S18b's template is the archived one judge_passages sends",
                   S["template"] == J._template("ANSWERABLE_JUDGE_PROMPT"), f"sha256 {sha(S['template'])[:12]}"))
    unbuilt = sorted(s for s in srcs if blocks[s]["text"] is None)
    checks.append(("G3 every block built without bge-m3", not unbuilt, f"unbuilt {unbuilt}"))
    if unbuilt:
        return _fail(checks)
    items, bad = build_items(S, blocks, qs["qids"])
    checks.append(("G5 B is S512's plain call on key v2.5; C and D are B plus one section at the anchor", not bad,
                   f"{len(items)} prompts; problems {len(bad)}" + (f", first {bad[:2]}" if bad else "")))
    # G6: blocks and donors against S18e's ledger
    led = s18e_rows()
    ev_seen, ev_bad, d_seen, d_bad = 0, [], 0, []
    for r in led:
        s = r.get("evidence_source_qid")
        if r["arm"] in ("C", "D") and s in blocks:
            ev_seen += 1
            if blocks[s]["sha256"] != r["evidence_sha256"]:
                ev_bad.append(s)
        if r["arm"] == "D" and r["question_id"] in s18_set:
            d_seen += 1
            if X.donor(S, r["question_id"], "mismatch") != s:
                d_bad.append(r["question_id"])
    checks.append(("G6 every block's sha256 equals S18e's evidence_sha256", ev_seen > 0 and not ev_bad,
                   f"{ev_seen} S18e rows; differing {sorted(set(ev_bad))}"))
    checks.append(("G6 every donor equals S18e's arm D donor", d_seen > 0 and not d_bad,
                   f"{d_seen} S18e rows; differing {sorted(set(d_bad))}"))
    # G7: the set and the question text
    _, k25 = S512.keys()
    qtext = [q for q in qs["qids"] if X.v22(q, S["v2"])["question"] != k25[q]["question"]]
    checks.append(("G7 the set: S18's frozen 62 less D7 less key v2.5's drops",
                   len(qs["frozen"]) == 62 and len(qs["qids"]) == 62 - len(qs["dropped_d7"]) - len(qs["dropped_v25"]),
                   f"{len(qs['qids'])} questions; D7 {qs['dropped_d7']}; v2.5 {qs['dropped_v25'] or 'none'}"))
    checks.append(("G7 key v2.5's question text is the one S18e sent", not qtext, f"differing {qtext}"))
    # G8: unchanged questions reproduce S18e's prompts byte for byte
    changed = set(S512.changed_ids())
    s18e_p = {(r["arm"], r["question_id"], r["config"]): r["prompt_sha256"] for r in led}
    n_eq, n_ne, n_ch_eq = 0, [], 0
    for it in items:
        arm = "B" if it["arm"] == "B2" else it["arm"]
        want = s18e_p.get((arm, it["question_id"], it["config"]))
        if it["question_id"] in changed:
            n_ch_eq += want == it["prompt_sha256"]
            continue
        if want == it["prompt_sha256"]:
            n_eq += 1
        else:
            n_ne.append(it["key"])
    unch = sorted({it["question_id"] for it in items} - changed)
    checks.append(("G8 on the questions v2.5 leaves unchanged, every prompt equals S18e's byte for byte",
                   n_eq > 0 and not n_ne and n_ch_eq == 0,
                   f"{len(unch)} unchanged questions, {n_eq} prompts equal, {len(n_ne)} differ; "
                   f"{len(set(qs['qids']) & changed)} changed questions, {n_ch_eq} of their prompts equal S18e's (0 expected)"))
    if not all(ok for _, ok, _ in checks):
        return _fail(checks)
    for name, ok, note in checks:
        print(f"  ok    {name}: {note}", flush=True)
    print(f"GATE PASSED ({len(checks)} checks, {time.time() - t0:.0f} s)", flush=True)
    return {"S": S, "qs": qs, "blocks": blocks, "items": items, "checks": checks, "g3n": g3n,
            "changed": sorted(set(qs["qids"]) & changed), "unchanged": unch, "s": round(time.time() - t0, 1)}


def _fail(checks: list) -> dict:
    for name, ok, note in checks:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {note}", flush=True)
    raise SystemExit("GATE FAILED: nothing planned, judged or written")


# ---------------------------------------------------------------- shards, identity

def parse_shard(s: str) -> tuple[int, int]:
    try:
        i, n = (int(v) for v in s.split("/"))
    except ValueError:
        raise SystemExit(f"REFUSED: --shard {s!r} is not I/N") from None
    if n < 1 or not 0 <= i < n:
        raise SystemExit(f"REFUSED: --shard {s!r}: need 0 <= I < N")
    return i, n


def shard(items: list[dict], qids: list[str], i: int, n: int) -> list[dict]:
    """The items of the questions at positions i, i + n, ... of the sorted question list (all six answers each)."""
    pos = {q: k for k, q in enumerate(sorted(qids))}
    return [it for it in items if pos[it["question_id"]] % n == i]


def call_code_identity() -> dict:
    """What defines a judged call besides its prompt (whose sha256 is in item_sha256): the judge call and parser
    (judge_passages), the evidence layout and donor rule (S18b), the block builder (S18e), the key (S512) and S18's
    inputs. Not this file."""
    return {"judge_passages": JP.code_identity(), "s512": S512.code_identity(),
            "s18b_rejudge_py": file_sha(Path(S18b.__file__)), "s18e_py": file_sha(Path(X.__file__)),
            "s18_docs": file_sha(X.DOCS), "s18_chunks": file_sha(X.CHUNKS), "s18_manifest": file_sha(X.MANIFEST),
            "exp04": file_sha(X.EXP04)}


def run_identity(lock, call) -> str:
    return sha(json.dumps({"lock": lock.sha256, "options": call.options, "fields": call.fields,
                           "system": call.system and sha(call.system), "model": call.model,
                           "code": call_code_identity()}, sort_keys=True))


# ---------------------------------------------------------------- the run (judge injected, so the selftest fakes it)

def read_rows(f: Path) -> list[dict]:
    return JP.read_rows(f)


def latest_rows(f: Path, mine: dict, run_sha: str) -> dict:
    """key -> latest row of each item in mine (key -> item_sha256); a row of one of them under another item or run
    sha256 refuses."""
    latest = {}
    for d in read_rows(f):
        k = d.get("key")
        if k not in mine:
            continue
        if d.get("item_sha256") != mine[k] or d.get("run_sha256") != run_sha:
            raise SystemExit(f"REFUSED: {f} already holds {k} judged on another item or run (item "
                             f"{str(d.get('item_sha256'))[:12]}, run {str(d.get('run_sha256'))[:12]}); use a new --out")
        latest[k] = d
    return latest


def make_row(it: dict, res: dict, run_sha: str, extra: dict) -> dict:
    row = {k: it[k] for k in ("key", "arm", "question_id", "config", "key_hash", "answer_sha256", "answer_chars",
                              "evidence", "evidence_source_qid", "evidence_mode", "evidence_sha256", "evidence_chars",
                              "prompt_sha256", "prompt_chars", "item_sha256")}
    row.update({"run_sha256": run_sha, "key_version": KEY_VERSION, "source": X.EXP04.name, "answerable": True})
    for k in ("status", "scores", "stop_reason", "prompt_tokens", "output_tokens", "attempts", "error", "wall_s",
              "load_s", "model_digest", "server", "ollama_version"):
        row[k] = res.get(k)
    row["faithfulness"] = (res.get("scores") or {}).get("faithfulness") if res.get("status") == "ok" else None
    row["raw_text"] = res.get("text")
    if res.get("prompt_sha256") is not None and res["prompt_sha256"] != it["prompt_sha256"]:
        raise SystemExit(f"REFUSED: the prompt sent for {it['key']} is not the item's")
    row.update(extra)
    row["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return row


def execute(items: list[dict], out: Path, run_sha: str, opener, limit: int | None = None,
            recheck_n: int = RECHECK_N, extra: dict | None = None) -> int:
    """Judge every item of this shard whose latest row is not ok. opener(what) makes a fresh load and returns
    judge(item) -> judge_passages.judge_call's result. Then the recheck. Exit 0 only when every item is ok and the
    recheck (if any) gave the same statuses and scores."""
    out.mkdir(parents=True, exist_ok=True)
    res_f = out / ROWS
    mine = {it["key"]: it["item_sha256"] for it in items}
    if len(mine) != len(items):
        raise SystemExit("REFUSED: two items share a key")
    latest = latest_rows(res_f, mine, run_sha)
    todo = [it for it in items if (latest.get(it["key"]) or {}).get("status") != "ok"][:limit]
    print(f"S18f v2.5: {len(items)} items, {len(items) - sum(1 for it in items if (latest.get(it['key']) or {}).get('status') != 'ok')} "
          f"done, {len(todo)} to judge", flush=True)
    rechecked = None
    if todo:
        judge = opener("run")
        for it in todo:
            row = make_row(it, judge(it), run_sha, extra or {})
            with res_f.open("a") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"{row['at']} {row['arm']:2s} {row['config']:13s} {row['question_id']:28s} {row['status']} "
                  f"F={row['faithfulness']} prompt {row['prompt_tokens']} out {row['output_tokens']} "
                  f"stop {row['stop_reason']} {row['wall_s']} s", flush=True)
        if recheck_n:
            rechecked = recheck(items, out, run_sha, opener, recheck_n)
    return finish(items, out, run_sha, rechecked)


def recheck(items: list[dict], out: Path, run_sha: str, opener, n: int) -> dict:
    """Another fresh load; the first n items with an ok row judged again; equal only if status and scores match."""
    latest = latest_rows(out / ROWS, {it["key"]: it["item_sha256"] for it in items}, run_sha)
    picked = [it for it in items if (latest.get(it["key"]) or {}).get("status") == "ok"][:n]
    if not picked:
        return {"n": 0, "equal": 0, "passed": None}
    judge = opener("recheck")
    eq = 0
    for it in picked:
        res = judge(it)
        prev = latest[it["key"]]
        same = res.get("status") == prev["status"] and res.get("scores") == prev["scores"]
        eq += same
        with (out / "judge_evidence_v25_recheck.jsonl").open("a") as fh:
            fh.write(json.dumps({"key": it["key"], "item_sha256": it["item_sha256"], "run_sha256": run_sha,
                                 "equal": same, "now": res.get("scores"), "now_status": res.get("status"),
                                 "written": prev["scores"], "at": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
    res = {"n": len(picked), "equal": eq, "passed": eq == len(picked), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    print(f"RECHECK: {eq} of {len(picked)} items give the same status and scores after a fresh load; "
          f"{'PASSED' if res['passed'] else 'NOT PASSED'}", flush=True)
    return res


def finish(items: list[dict], out: Path, run_sha: str, rechecked: dict | None) -> int:
    latest = latest_rows(out / ROWS, {it["key"]: it["item_sha256"] for it in items}, run_sha)
    st = Counter((latest.get(it["key"]) or {}).get("status", "not judged") for it in items)
    not_ok = sum(v for k, v in st.items() if k != "ok")
    summary = {"_provenance": {"script": f"{SCRIPT} run", "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
               "run_sha256": run_sha, "items": len(items), "status": dict(st), "not_ok": not_ok,
               "max_prompt_tokens": max([d.get("prompt_tokens") or 0 for d in latest.values()], default=None),
               "recheck": rechecked}
    (out / "judge_evidence_v25_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"SUMMARY: {dict(st)}; {not_ok} of {len(items)} not ok", flush=True)
    if rechecked is not None and rechecked.get("passed") is False:
        print("S18F V25 SHARD NOT PASSED: the recheck differs", flush=True)
        return 1
    if not_ok:
        print(f"S18F V25 SHARD ENDED: {not_ok} items not ok (tried again on resume)", flush=True)
        return 1
    print("S18F V25 SHARD DONE", flush=True)
    return 0


def cmd_run(a) -> int:
    i, n = parse_shard(a.shard)
    base = a.base.rstrip("/")
    a.judge = "main"
    lock0 = load()
    model = JP.judge_of(lock0, "main")
    check = S512.require_check(a.check_dir, lock0, base, a.machine, a.binary, "main", a.reference)
    call0 = lock0.ollama(model, role="judge")
    run_sha = run_identity(lock0, call0)
    P = prepare()
    items = shard([it for it in P["items"] if it["arm"] == a.arm], P["qs"]["qids"], i, n)
    out = a.out / f"{a.arm}_shard{i}of{n}"
    out.mkdir(parents=True, exist_ok=True)
    JP.hold_writer(out)
    JP.refuse_other_judge(out, model)
    log = out / CALLS

    def opener(what: str):
        lock, model_, call, fl = JP.start(a, out, what)
        if lock.sha256 != lock0.sha256 or run_identity(lock, call) != run_sha:
            raise SystemExit("REFUSED: the lock or the code changed while the run started")
        header = {"_provenance": {"script": f"{SCRIPT} run", "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                  "inputs": {X.rel(p): file_sha(p) for p in
                                             (X.EXP04, X.FROZEN, X.DOCS, X.CHUNKS, X.MANIFEST, S512.KEY25, S18E_LEDGER)}},
                  "what": what, "arm": a.arm, "shard": [i, n], "model": model_, "model_digest": call.digest,
                  "lock_sha256": lock.sha256, "options": call.options, "fields": call.fields,
                  "system_prompt_sha256": call.system and sha(call.system), "base": base,
                  "machine_identity": fl["machine_identity"], "run_sha256": run_sha, "code": call_code_identity(),
                  "s18f_py": file_sha(Path(__file__)), "key_version": KEY_VERSION,
                  "check": {k: check.get(k) for k in ("kind", "n", "equal_scores", "lock_sha256", "model_digest",
                                                      "reference_sha256")},
                  "items": len(items)}
        with (out / HEADERS).open("a") as fh:
            fh.write(json.dumps(header, ensure_ascii=False) + "\n")

        def judge(it: dict) -> dict:
            passages = ([{"source": f, "chunk_idx": None, "evidence_block": it["evidence_mode"]}
                         for f in it["evidence_files"]] if it["evidence_files"] else None)
            return JP.judge_call(base, call, it["prompt"], True, passages, log,
                                 {"answer": it["key"], "variant": f"S18f25_{it['arm']}", "item_sha256": it["item_sha256"]})
        return judge

    return execute(items, out, run_sha, opener, a.limit, 0 if a.no_recheck else RECHECK_N,
                   {"lock_sha256": lock0.sha256, "shard": f"{i}/{n}"})


# ---------------------------------------------------------------- plan (no model call)

def exact_counter(models_dir: Path):
    """judge_evidence.py's tokenizer for the locked devstral GGUF, checked against Ollama's stored counts (one offset)."""
    from experiments.scorers import judge_evidence as JE
    lock = load()
    model = lock.d["judge"]["model"]
    blob, prov = JE.model_blob(model, lock.d["models"][model]["digest"], models_dir)
    tk = JE.tokenizer(JE.gguf_kv(blob))
    v = JE.validate(tk)
    if not v["passed"]:
        return None, {"passed": False, "validation": {k: v[k] for k in ("s440", "s18e", "rows", "offset")}}
    off = v["offset"]
    cache: dict[str, int] = {}

    def count(p: str) -> int:
        h = sha(p)
        if h not in cache:
            cache[h] = len(tk.encode(p, add_special_tokens=False).ids) + off
        return cache[h]
    return count, {"passed": True, "offset": off, "rows": v["rows"], "source": prov}


def estimated_tokens(items: list[dict]) -> dict:
    """Without the tokenizer: S18e's measured prompt tokens for the same arm, question and config, plus the character
    difference at S18e's own characters per token for the no-evidence prompt (median over its B rows)."""
    led = s18e_rows()
    by = {(r["arm"], r["question_id"], r["config"]): r for r in led if r.get("prompt_tokens")}
    cpt = sorted(r["prompt_chars"] / r["prompt_tokens"] for r in led if r["arm"] == "B" and r.get("prompt_tokens"))
    cpt = cpt[len(cpt) // 2]
    out = {}
    for it in items:
        r = by.get(("B" if it["arm"] == "B2" else it["arm"], it["question_id"], it["config"]))
        if r is not None:
            out[it["key"]] = round(r["prompt_tokens"] + (it["prompt_chars"] - r["prompt_chars"]) / cpt)
    return {"tokens": out, "chars_per_token": cpt}


def cmd_plan(a) -> int:
    P = prepare()
    items, qs = P["items"], P["qs"]
    lock = load()
    call = lock.ollama(lock.d["judge"]["model"], role="judge")
    num_ctx, num_predict = call.options["num_ctx"], call.options["num_predict"]
    tok_src, counts = "estimate", None
    if not a.no_exact:
        try:
            count, tprov = exact_counter(a.models_dir)
        except SystemExit as e:
            count, tprov = None, {"passed": False, "error": str(e)}
        if count is not None:
            counts = {it["key"]: count(it["prompt"]) for it in items}
            tok_src = f"exact: the locked GGUF's tokenizer plus {tprov['offset']} (checked on {tprov['rows']} stored calls)"
    else:
        tprov = {"passed": None, "note": "--no-exact"}
    est = estimated_tokens(items)
    if counts is None:
        counts = est["tokens"]
    per_arm, shards = {}, {}
    for arm in ARMS:
        xs = [it for it in items if it["arm"] == arm]
        ts = [(counts.get(it["key"]), it) for it in xs]
        top_t, top = max(ts, key=lambda t: t[0] or 0)
        per_arm[arm] = {"items": len(xs), "questions": len({it["question_id"] for it in xs}),
                        "max_prompt_chars": max(it["prompt_chars"] for it in xs), "max_prompt_tokens": top_t,
                        "max_at": top["key"], "over_num_ctx": sum(1 for t, _ in ts if t is not None and t >= num_ctx),
                        "over_num_ctx_less_num_predict": sum(1 for t, _ in ts if t is not None and t + num_predict > num_ctx),
                        "estimate_max_tokens": max(est["tokens"].get(it["key"], 0) for it in xs)}
    for i in range(a.shards):
        sx = shard(items, qs["qids"], i, a.shards)
        shards[f"{i}/{a.shards}"] = {"questions": len({it["question_id"] for it in sx}),
                                     "items_per_arm": len(sx) // len(ARMS),
                                     "prompt_chars_per_arm": {arm: sum(it["prompt_chars"] for it in sx if it["arm"] == arm)
                                                              for arm in ARMS}}
    _, k25 = S512.keys()
    src_diff = sorted(q for q in qs["qids"] if list(k25[q].get("source_files") or []) != list(P["S"]["sizing"][q]["source_files"]))
    res = {"_provenance": {"script": f"{SCRIPT} plan", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "lock_sha256": lock.sha256, "run_sha256": run_identity(lock, call), "code": call_code_identity(),
                           "s18f_py": file_sha(Path(__file__)),
                           "inputs": {X.rel(p): file_sha(p) for p in
                                      (X.EXP04, X.FROZEN, X.DOCS, X.CHUNKS, X.MANIFEST, S512.KEY25, S18E_LEDGER)},
                           "gate_s": P["s"]},
           "gate": [{"check": c, "pass": ok, "note": nt} for c, ok, nt in P["checks"]],
           "judge": call.model, "options": call.options, "fields": call.fields,
           "questions": len(qs["qids"]), "configs": P["S"]["configs"], "answers_per_arm": len(qs["qids"]) * len(P["S"]["configs"]),
           "dropped_d7": qs["dropped_d7"], "dropped_v25": qs["dropped_v25"],
           "questions_v25_changed": len(P["changed"]), "questions_v25_unchanged": len(P["unchanged"]),
           "v25_source_files_differ_from_s18_sizing": src_diff,
           "arm_A": "dropped: under the lock A's prompt and options are B's byte for byte (S18e's A differed from B only in num_ctx)",
           "calls": len(items), "per_arm": per_arm, "shards": shards, "tokens": tok_src, "tokenizer": tprov,
           "estimate_chars_per_token": est["chars_per_token"],
           "blocks": {k: {kk: vv for kk, vv in v.items() if kk != "text"} for k, v in P["blocks"].items()
                      if k in {it["evidence_source_qid"] for it in items}},
           "items": [{k: v for k, v in it.items() if k != "prompt"} | {"prompt_tokens": counts.get(it["key"])} for it in items]}
    a.dest_dir.mkdir(parents=True, exist_ok=True)
    (a.dest_dir / f"{PLAN_STEM}.json").write_text(json.dumps(res, indent=1) + "\n")
    L = [f"# S18f plan: S18e's arms on key v2.5 with S512's judge call ({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"Gate passed ({len(P['checks'])} checks; no model call). {len(qs['qids'])} questions, "
         f"{res['answers_per_arm']} answers per arm, {len(items)} calls in arms {', '.join(ARMS)}. Removed from S18's "
         f"frozen 62: D7 {qs['dropped_d7']}; key v2.5 {qs['dropped_v25'] or 'none'}. Key v2.5 changes the prompt of "
         f"{len(P['changed'])} of the {len(qs['qids'])} questions; the other {len(P['unchanged'])} reproduce S18e's "
         f"prompts byte for byte (G8).", "",
         f"Judge {call.model}, {json.dumps(call.options)}, {json.dumps(call.fields)}. Tokens: {tok_src}.", "",
         "| arm | items | max prompt characters | max prompt tokens | over num_ctx | over num_ctx less num_predict |",
         "|---|---|---|---|---|---|"]
    for arm, v in per_arm.items():
        L.append(f"| {arm} | {v['items']} | {v['max_prompt_chars']:,} | {v['max_prompt_tokens']:,} | {v['over_num_ctx']} | "
                 f"{v['over_num_ctx_less_num_predict']} |")
    L += ["", f"Shards of {a.shards}: " + "; ".join(f"{k} {v['questions']} questions" for k, v in shards.items()) + ".",
          f"Arm A: {res['arm_A']}.",
          f"Questions whose key v2.5 source files differ from S18's sizing (the blocks stay S18's): {src_diff or 'none'}.",
          "", f"Full rows: findings/recompute/{PLAN_STEM}.json."]
    (a.dest_dir / f"{PLAN_STEM}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


# ---------------------------------------------------------------- analysis

def analysis(by: dict, keys: list, contrasts=CONTRASTS, arms=ARMS) -> dict:
    """S18c's numbers on by[(arm, qid, config)] = {"parsed": scores}: shares scored 5, the contrasts (S18c.compare),
    the noise rule and B/B2 identity."""
    shares = {arm: dict(zip(("share5", "n"), X.share5(by, arm, keys))) for arm in arms}
    cons = [S18c.compare(by, ax, ay, keys, lab) for ax, ay, lab in contrasts]
    nf = next((c["dims"]["faithfulness"] for c in cons if c["contrast"] == "B vs B2"), None)
    resolvable = None if not nf or not nf.get("n") else abs(nf["share5_diff_pp"]) <= NOISE_PP
    bb2 = [k for k in keys if ("B",) + k in by and ("B2",) + k in by]
    same = sum(1 for k in bb2 if all(by[("B",) + k]["parsed"][d] == by[("B2",) + k]["parsed"][d] for d in S18c.DIMS))
    return {"share5_faithfulness": shares, "contrasts": cons, "resolvable_noise_under_3pp": resolvable,
            "b_b2_identical_all_four_dims": {"answers": len(bb2), "identical": same}}


def reproduce_s18e(S: dict) -> tuple[bool, str]:
    """This file's analysis on S18e's ledger, read as S18e.analyze reads it, against S18e_results.json."""
    dep = json.loads(S18E_RESULTS.read_text())
    qids = sorted(set(S["frozen"]["primary_set_full"]) - set(S["dropped"]))
    cur = {q: S373.key_hash(q, S["v2"]) for q in qids}
    by = {}
    for r in sorted(s18e_rows(), key=lambda r: r.get("at", "")):
        if r.get("status") not in X.OK or r.get("key_hash") != cur.get(r.get("question_id")):
            continue
        sc = r.get("scores") or {}
        if not all(isinstance(sc.get(d), int) for d in J.ANSWERABLE_DIMS):
            continue
        by.setdefault((r["arm"], r["question_id"], r["config"]), {"parsed": sc})
    keys = [(q, c) for q in qids for c in S["configs"]]
    mine = analysis(by, keys, X.CONTRASTS, X.ORDER)
    mine = json.loads(json.dumps(mine))
    ok_c = mine["contrasts"] == dep["contrasts"]
    ok_s = mine["share5_faithfulness"] == dep["share5_faithfulness"]
    ok_r = mine["resolvable_noise_under_3pp"] == dep["resolvable_noise_under_3pp"]
    ok_b = mine["b_b2_identical_all_four_dims"] == dep["b_b2_identical_all_four_dims"]
    cd = next(c for c in mine["contrasts"] if c["contrast"] == "C vs D")["dims"]["faithfulness"]
    return ok_c and ok_s and ok_r and ok_b, (f"{len(keys)} answers; contrasts {ok_c}, shares {ok_s}, noise rule {ok_r}, "
                                             f"B/B2 {ok_b}; C vs D {cd['share5_diff_pp']} {cd['share5_diff_ci95_pp']}")


def collect(dirs: list[Path], items: list[dict]) -> dict:
    """The latest row of every item found under dirs; refuses a row of a known key with another item_sha256 and rows
    of more than one run_sha256."""
    mine = {it["key"]: it for it in items}
    files = sorted({f for d in dirs for f in Path(d).rglob(ROWS)})
    latest, stale, other, runs, ok_files = {}, [], 0, Counter(), {}
    for f in files:
        for r in read_rows(f):
            it = mine.get(r.get("key"))
            if it is None:
                other += 1
                continue
            if r.get("item_sha256") != it["item_sha256"]:
                stale.append(r["key"])
                continue
            runs[r.get("run_sha256")] += 1
            prev = latest.get(r["key"])
            if r.get("status") == "ok":
                ok_files.setdefault(r["key"], set()).add(f)
            if prev is None or prev.get("status") != "ok":   # an ok row is kept; a later row replaces a non-ok one
                latest[r["key"]] = r
    twice = sorted(k for k, fs in ok_files.items() if len(fs) > 1)
    if twice:
        raise SystemExit(f"REFUSED: {len(twice)} items have ok rows in more than one file (first {twice[0]}); "
                         "one shard layout per arm; nothing written")
    bad = [str(f) for d in dirs for f in Path(d).rglob("judge_evidence_v25_summary.json")
           if (json.loads(f.read_text()).get("recheck") or {}).get("passed") is False]
    if bad:
        raise SystemExit(f"REFUSED: {len(bad)} shards failed their recheck (first {bad[0]}); nothing written")
    if stale:
        raise SystemExit(f"REFUSED: {len(stale)} rows were judged on another item (first {stale[0]}); nothing written")
    if len(runs) > 1:
        raise SystemExit(f"REFUSED: rows of {len(runs)} run_sha256 values ({dict(runs)}); one run definition only")
    return {"files": files, "latest": latest, "other_rows": other, "run_sha256": next(iter(runs), None)}


def by_from(latest: dict, items: list[dict]) -> tuple[dict, dict]:
    by, health = {}, {}
    for arm in ARMS:
        xs = [it for it in items if it["arm"] == arm]
        st = Counter((latest.get(it["key"]) or {}).get("status", "not judged") for it in xs)
        ok = 0
        for it in xs:
            r = latest.get(it["key"])
            sc = (r or {}).get("scores") or {}
            if r and r.get("status") == "ok" and all(isinstance(sc.get(d), int) for d in J.ANSWERABLE_DIMS):
                by[(arm, it["question_id"], it["config"])] = {"parsed": sc, "row": r}
                ok += 1
        rs = [latest[it["key"]] for it in xs if it["key"] in latest]
        health[arm] = {"expected": len(xs), "counted": ok, "statuses": dict(st),
                       "max_prompt_tokens": max([r.get("prompt_tokens") or 0 for r in rs], default=None),
                       "stop_reasons": dict(Counter(r.get("stop_reason") for r in rs)),
                       "dates": dict(Counter(str(r.get("at", ""))[:10] for r in rs))}
    return by, health


def cmd_analyze(a) -> int:
    P = prepare()
    S, items, qs = P["S"], P["items"], P["qs"]
    ok, note = reproduce_s18e(S)
    print(f"  {'ok  ' if ok else 'FAIL'}  REPRODUCE this analysis on S18e's ledger gives S18e_results.json: {note}", flush=True)
    if not ok:
        print("ANALYZE REFUSED: the analysis code does not reproduce S18e's results; nothing written")
        return 1
    col = collect(a.dirs, items)
    by, health = by_from(col["latest"], items)
    short = {arm: h for arm, h in health.items() if h["counted"] != h["expected"]}
    if short:
        for arm, h in short.items():
            print(f"  arm {arm}: {h['counted']} of {h['expected']} items ok; statuses {h['statuses']}")
        print("ANALYZE REFUSED: an arm is incomplete; nothing written")
        return 1
    keys = [(q, c) for q in qs["qids"] for c in S["configs"]]
    res_a = analysis(by, keys)
    lock = load()
    dep = json.loads(S18E_RESULTS.read_text())
    res = {"_provenance": {"script": f"{SCRIPT} analyze", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "s18f_py": file_sha(Path(__file__)), "lock_sha256_now": lock.sha256,
                           "rows_files": {str(f): file_sha(f) for f in col["files"]}, "run_sha256": col["run_sha256"],
                           "rows_of_other_items": col["other_rows"],
                           "reproduction": {"s18e_results_json": file_sha(S18E_RESULTS), "passed": ok, "note": note},
                           "gate": [{"check": c, "pass": g, "note": nt} for c, g, nt in P["checks"]]},
           "key_version": KEY_VERSION, "judge": "devstral-small-2:24b (LOCK.toml [judge], S512's call)",
           "analysis_set": {"questions": len(qs["qids"]), "answers": len(keys), "frozen_set_sha256": X.FROZEN_SHA,
                            "dropped_d7": qs["dropped_d7"], "dropped_v25": qs["dropped_v25"],
                            "questions_v25_changed": len(P["changed"])},
           "health": health, **res_a,
           "s18e_v24": {"share5_faithfulness": dep["share5_faithfulness"],
                        "contrasts": {c["contrast"]: {k: c["dims"]["faithfulness"].get(k) for k in
                                                      ("n", "share5_x", "share5_y", "share5_diff_pp", "share5_diff_ci95_pp")}
                                      for c in dep["contrasts"]}}}
    a.dest_dir.mkdir(parents=True, exist_ok=True)
    out = a.dest_dir / f"{RESULTS_STEM}.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    sh = res_a["share5_faithfulness"]
    L = [f"# S18f results: devstral-small-2:24b on key v2.5, S512's call ({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"{len(qs['qids'])} questions, {len(keys)} answers per arm (S18's frozen set less D7 {qs['dropped_d7']}, less key "
         f"v2.5's drops {qs['dropped_v25'] or 'none'}). Rows: {len(col['files'])} files, run_sha256 {str(col['run_sha256'])[:12]}.",
         f"This analysis code reproduces S18e_results.json from S18e's ledger: {note}.",
         f"Noise floor within {NOISE_PP:g} points: {res_a['resolvable_noise_under_3pp']}. B and B2 identical on all four "
         f"dimensions: {res_a['b_b2_identical_all_four_dims']['identical']} of {res_a['b_b2_identical_all_four_dims']['answers']}.", "",
         "| arm | counted | 5/5 faithfulness | max prompt tokens | S18e (v2.4) |", "|---|---|---|---|---|"]
    for arm in ARMS:
        h = health[arm]
        old = dep["share5_faithfulness"].get(arm, {}).get("share5")
        L.append(f"| {arm} | {h['counted']} of {h['expected']} | {100 * sh[arm]['share5']:.2f}% | {h['max_prompt_tokens']} | "
                 f"{'' if old is None else f'{100 * old:.2f}%'} |")
    L += ["", "| contrast | n | 5/5 x | 5/5 y | difference, points | 95% CI | TOST equivalent at 5 |", "|---|---|---|---|---|---|---|"]
    for c in res_a["contrasts"]:
        f = c["dims"]["faithfulness"]
        if f.get("n"):
            L.append(f"| {c['contrast']} ({c['label']}) | {f['n']} | {100 * f['share5_x']:.2f}% | {100 * f['share5_y']:.2f}% | "
                     f"{f['share5_diff_pp']} | {f['share5_diff_ci95_pp']} | {(f.get('tost') or {}).get('equivalent')} |")
    L += ["", f"Full statistics: findings/recompute/{RESULTS_STEM}.json."]
    (a.dest_dir / f"{RESULTS_STEM}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--shards", type=int, default=4)
    p.add_argument("--no-exact", action="store_true", help="skip the tokenizer; estimate from S18e's measured tokens")
    p.add_argument("--models-dir", type=Path, default=Path("~/.ollama/models").expanduser())
    p.add_argument("--dest-dir", type=Path, default=RECOMPUTE)
    r = sub.add_parser("run")
    r.add_argument("--arm", required=True, choices=ARMS)
    r.add_argument("--base", required=True, help="the judge's server (no default)")
    r.add_argument("--log", required=True, type=Path, help="the server's log, for the fresh load's checks")
    r.add_argument("--binary", required=True, type=Path)
    r.add_argument("--machine", required=True, choices=["macos", "beelink"])
    r.add_argument("--shard", required=True, help="I/N, 0 <= I < N")
    r.add_argument("--check-dir", required=True, type=Path, help="a passed S512 check or calibrate for this port")
    r.add_argument("--reference", type=Path, default=S512.REFERENCE, help="S512's v2.5 reference")
    r.add_argument("--out", required=True, type=Path)
    r.add_argument("--limit", type=int)
    r.add_argument("--no-recheck", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("dirs", nargs="+", type=Path)
    z.add_argument("--dest-dir", type=Path, default=RECOMPUTE)
    a = ap.parse_args(argv)
    if a.cmd == "plan" and a.shards < 1:
        ap.error("--shards must be at least 1")
    return {"plan": cmd_plan, "run": cmd_run, "analyze": cmd_analyze}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
