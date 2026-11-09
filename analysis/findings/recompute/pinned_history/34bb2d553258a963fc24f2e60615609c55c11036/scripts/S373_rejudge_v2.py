#!/usr/bin/env python3
"""S373 - re-judge logged answers against ground truth v2.1, on several Ollama servers at once.

WHY. The answer key behind every judged experiment was written by Gemini from its own summary of each
paper (S362); ground truth v2.1 (data/ground_truth_v2/all_v2_1.json) replaces it once Valerio signs it
off. Every judge score keyed to the old answer must then be recomputed. Valerio's decisions of
8 October fix how: the incumbent judge qwen3-coder:30b with the corrected-rescoring settings, the
second judge gpt-oss:120b at reasoning effort "low" (S366: think false is ignored by gpt-oss and runs
at about medium effort; low is 3.4 times faster and repeats more often), complete answers, and no
call whose prompt or output was cut passing as a score. S366 measured 5 qwen3-coder servers at 1.35 s
and 3 gpt-oss servers at 8.09 s per answer; this script is what runs that.

JUDGES (S141_runner.judge, the prompt templates read from the archived harness, never retyped):
  qwen    qwen3-coder:latest (digest 06c1097efce0), options temperature 0, num_ctx 40960,
          num_predict 1024 (NEW_ARM), think false, no truncation of the answer
  gptoss  gpt-oss:120b, options temperature 0, num_ctx 40960, num_predict 8192 (ROBUSTNESS_ARM),
          think "low", no truncation of the answer
PROMPT (Q51, Valerio, 11 October): the answerable prompt, unless v1 flags the question unanswerable and its v2
answer_type is not "refutation" (judged_answerable). The ten false-premise questions OOD_041 to OOD_050 are judged
with the answerable prompt against the key's refutation and key points, and their key_hash carries the marker
"Q51: answerable prompt". Each row's "answerable" field records the prompt used, not v1's flag.

EVERY CALL RECORDS prompt and output token counts, the stop reason, the raw judge text, the server and
its Ollama version, and its status:
  ok                  scored
  ok_output_limit     the output reached num_predict but the scores parsed; scored, flagged
  output_limit        the output reached num_predict and did not parse; not scored
  out_of_context      the prompt filled the context window (prompt tokens >= num_ctx - 64), so Ollama
                      may have dropped part of it; not scored, whatever the judge returned
  unparseable, error  not scored (the judge retries once, S141_runner.judge)

SOURCES. --source exp04 reads the generation-strategy answers (S21's row reader). --source paper_qa
reads every experiment judged with the harness QA prompt through S374's readers: generation
strategies, corpus scaling, pipeline ablation, naive baseline, retrieval depth, both strategy
replications; --source replication5 the five-model replication alone (its second judge); --source replication2 the
two-model replication alone ("Strategy replication (published)", 809 answers after D7; Q57, 12 October: its second
judge, under the same keys as its rows in paper_qa and paper_qa_rest). --source selection_synth
(added 9 October, item 14): generator selection (exp00 rlm_models, 213 judged answers) and the synthesizer
benchmark (exp07), both judged with the same harness template.
--questions limits a run to a list of question IDs (the overnight run of 8 October: the 74 questions
every check and reviewer passed). Each row records its question's key hash, and resume skips a row
only under the same hash, so editing a record later re-judges that question alone.

    .venv/bin/python scripts/S373_rejudge_v2.py --judge qwen --source exp04 --ports 11451 11452 11453 11454 11455 --n 50 --out test50
    .venv/bin/python scripts/S373_rejudge_v2.py --judge gptoss --source exp04 --ports 11441 11451 11452 --n 50 --out test50

Writes findings/recompute/S373_<judge>_<source>[_<out>].jsonl (resumable: done keys are skipped) and
a .md summary. Changes no answer and no key.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import queue
import statistics
import sys
import threading
import time
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import S21_full_answer_rejudge as S21  # noqa: E402
from machine import PUB, RECOMPUTE, ROOT  # noqa: E402
from S141_runner.judge import NEW_ARM, ROBUSTNESS_ARM, Judge  # noqa: E402
from S141_runner.providers import OllamaProvider  # noqa: E402

KEY = ROOT / "data/ground_truth_v2/all_v2_4.json"     # Q50, 11 October 09:00: v2.3 with the 25 corrections verified in Q49 and
# accepted in Q50
# (S398); v2.3 (S396, Q45) was v2.2 (frozen 9 October, S378) with five corrections. key_hash is per question, so rows
# judged on an earlier key stay valid for the other questions and only the changed questions are judged again. The
# overnight run of 8 October used all_v2_1.json
AS_V1 = ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json"   # the same key in the v1 format (S381 --key 2.4)
V2_INPUTS = ROOT / "data/ground_truth_v2/inputs_v2_1"
V1 = ROOT / "data/replication_inputs/ground_truth.json"
JUDGES = {
    "qwen": {"model": "qwen3-coder:latest", "digest": "06c1097efce0", "options": dict(NEW_ARM), "think": False},
    # gpt-oss:120b with the date in its template fixed at 10 October 2026 (Q31, Valerio, 10 October): its template
    # writes today's date into a header no system message replaces, so the pin is a model copy whose template is the
    # original with {{ currentDate }} replaced (data/judge_system_prompts/gpt-oss_120b.date-2026-10-10.Modelfile,
    # same weights blob). On 10 October it gives the original's text exactly (Mac Studio :11460, 2 of 2 prompts)
    "gptoss": {"model": "gpt-oss:120b-date20261010", "digest": None, "options": dict(ROBUSTNESS_ARM), "think": "low"},
    # the main judge from 9 October (O2, after S376 and S377), with the settings it was calibrated and tested
    # under (Q11): complete answers, num_ctx 32768, num_predict 8192; one request per server (S377: batching
    # changes scores)
    "devstral": {"model": "devstral-small-2:24b", "digest": None,
                 "options": {"temperature": 0, "num_ctx": 32768, "num_predict": 8192}, "think": False},
}
CTX_MARGIN = 64


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def server(port: int, model: str) -> dict:
    base = f"http://127.0.0.1:{port}"
    tags = {m["name"]: m["digest"][:12] for m in get(base + "/api/tags")["models"]}
    return {"port": port, "ollama": get(base + "/api/version")["version"], "model_digest": tags.get(model)}


def key_of(qid: str, v2: dict) -> tuple[str, list[str]]:
    rec = v2[qid]
    ea = rec["short_answer"] + (("\n\n" + rec["synthesis_statement"]) if rec.get("synthesis_statement") else "")
    return ea, [k["phrase"] for k in rec["key_concepts"]]


def refutation(qid: str, v2: dict) -> bool:
    """Q51 (Valerio, 11 October 2026, "Fix it"): the ten false-premise questions, OOD_041 to OOD_050, whose key answer
    refutes the question's premise (answer_type "refutation"). v1 flags them unanswerable, which sent them to the
    decline prompt: it tells the judge the question cannot be answered from the corpus, scores declining 5 and a
    confident answer 0, and never shows the refutation, so a correct answer was scored as a failure. Q13 (9 October)
    meant them to be judged against the paper's refutation; they now are, with the answerable prompt."""
    return v2[qid].get("answer_type") == "refutation"


def judged_answerable(qid: str, v1: dict, v2: dict) -> bool:
    """The prompt a question is judged with: answerable, unless v1 flags it unanswerable and it is not a refutation."""
    return refutation(qid, v2) or v1[qid].get("answerable", True) in (True, "true", "True")


def key_hash(qid: str, v2: dict) -> str:
    """This question's key (answer and concepts) as the judge sees it. A row is done only under the
    same hash, so editing one record re-judges that question's answers and nothing else. For the ten
    refutation questions the prompt is part of it (Q51), so their rows judged with the decline prompt are
    stale; every other question's hash is unchanged."""
    ea, ec = key_of(qid, v2)
    parts = [ea, ec] + (["Q51: answerable prompt"] if refutation(qid, v2) else [])
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()[:16]


def source_exp04(v1: dict, v2: dict) -> list[dict]:
    src = PUB / "results/exp04_generation_latest.json"
    rows = []
    for i, r in enumerate(S21.judged_rows(json.loads(src.read_text()))):
        qid, t = r.get("question_id"), S21.answer_text(r)
        if qid not in v2 or not t:
            continue
        q = json.loads((V2_INPUTS / f"{qid}.json").read_text())["question"]
        ea, ec = key_of(qid, v2)
        rows.append({"key": f"exp04|{r.get('config')}|{qid}|{i}", "source": src.name, "row": i,
                     "question_id": qid, "config": r.get("config"), "question": q,
                     "answerable": judged_answerable(qid, v1, v2),
                     "expected": ea, "concepts": ec, "answer": t})
    return rows


def source_files(labels: tuple[str, ...]):
    """Rows of S374's result files (s374/files.py) whose experiment uses the harness judge prompt.

    s374/files.py globs the upstream results when it is imported, so it is imported when read() runs, not when
    this module is imported (D155: a figure build that imports S373 for KEY or AS_V1 must not list a sibling
    checkout)."""

    def read(v1: dict, v2: dict) -> list[dict]:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "s374"))
        from files import FILES
        from rows import answer, load_rows, qid as row_qid
        out = []
        for label, path in FILES:
            if label not in labels:
                continue
            d, rows = load_rows(path)
            tag = Path(path).name if "S141" not in path else Path(path).parent.name
            for i, r in enumerate(rows):
                qid, t = row_qid(r), answer(r)
                if qid not in v2 or not t or not t.strip():
                    continue
                g = r.get("generation") if isinstance(r.get("generation"), dict) else {}
                ea, ec = key_of(qid, v2)
                out.append({"key": f"{label}|{tag}|{i}", "source": tag, "row": i, "question_id": qid,
                            "config": r.get("config") or g.get("config") or r.get("depth"),
                            "question": json.loads((V2_INPUTS / f"{qid}.json").read_text())["question"],
                            "answerable": judged_answerable(qid, v1, v2),
                            "expected": ea, "concepts": ec, "answer": t})
        return out
    return read


SOURCES = {"exp04": source_exp04,
           "paper_qa": source_files(("Generation strategies (exp04)", "Corpus scaling (exp05)", "Orchestration (exp06)",
                                     "Naive RAG baseline", "Retrieval depth (exp09)", "Strategy replication (published)",
                                     "S141 campaign (strategy replication, multi-generator)")),
           "replication5": source_files(("S141 campaign (strategy replication, multi-generator)",)),
           # Q57 (evening plan of 12 October, 18:55): the two-model replication alone, its second judge, so that
           # gpt-oss scores both replications of J1's published set (809 answers after D7; paper_qa_rest holds the
           # same keys for the main judge)
           "replication2": source_files(("Strategy replication (published)",)),
           # paper_qa without the replication (Q12, 9 October: the Mac Studio judges the replication as one run,
           # the laptop and then the Mac Studio share the rest in shards)
           "paper_qa_rest": source_files(("Generation strategies (exp04)", "Corpus scaling (exp05)", "Orchestration (exp06)",
                                          "Naive RAG baseline", "Retrieval depth (exp09)", "Strategy replication (published)")),
           # item 14, 9 October: both used the same harness judge template (exp00: judge_answer via exp_v4_common;
           # exp07: the same function, but its key lookup was broken, CL-95, and S293/S306 re-judged it against v1)
           "selection_synth": source_files(("Generator selection (exp00 rlm_models)", "Component benchmark: synthesizer (exp07)")),
           # the reanalysis arms whose judge scores the letter and the manuscript print (S141 small-model arm and
           # timing, S314 verified_pass rerun in its judged mode, S357's Gemini arm), 9 October; all judged with the
           # harness template (S141_runner.judge, or the factorial driver's judge_answer for S314)
           "reanalysis": source_files(("S141 mini arm (step 4.3, s50)", "S141 timing (step 4.4)",
                                       "S314 verified_pass rerun (exp05 indexes)", "S357 Gemini paired arm"))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", choices=sorted(JUDGES), required=True)
    ap.add_argument("--source", choices=sorted(SOURCES), required=True)
    ap.add_argument("--ports", nargs="+", type=int, required=True)
    ap.add_argument("--n", type=int, default=None, help="an evenly spread sample, for a test run")
    ap.add_argument("--questions", default=None, help="JSON file {ids: [...]}: judge only these questions")
    ap.add_argument("--out", default=None)
    ap.add_argument("--shard", default=None, help="k/n: judge only the answers whose key hashes to shard k of n "
                    "(splitting one run across machines; each writes its own file, merged afterwards)")
    a = ap.parse_args()
    J = JUDGES[a.judge]
    stem = f"S373_{a.judge}_{a.source}" + (f"_{a.out}" if a.out else "") + (f"_shard{a.shard.replace('/', 'of')}" if a.shard else "")
    jl, md = RECOMPUTE / f"{stem}.jsonl", RECOMPUTE / f"{stem}.md"

    servers = [server(p, J["model"]) for p in a.ports]
    for s in servers:
        if J["digest"] and s["model_digest"] != J["digest"]:
            raise SystemExit(f"FATAL: port {s['port']} has {J['model']} digest {s['model_digest']}, expected {J['digest']}")
    v1 = {q["id"]: q for q in json.loads(V1.read_text())["questions"]}
    v2 = {r["id"]: r for r in json.loads(KEY.read_text())["records"]}
    key_sha = hashlib.sha256(KEY.read_bytes()).hexdigest()
    items = sorted(SOURCES[a.source](v1, v2), key=lambda x: x["key"])
    if a.questions:
        keep = set(json.loads(Path(a.questions).read_text())["ids"])
        items = [x for x in items if x["question_id"] in keep]
    # a question whose wording changed in v2 (OOD_011, CD_015, SY_010, 45_kenya_amr_digital_FR1,
    # 46_methylpipe_CO2, SY_018) has logged answers to the OLD question: judging them against the new key
    # measures nothing, so they are left out until D7 (regenerate or drop) is decided
    changed = {qid for qid, r in v2.items() if r.get("question") and r["question"] != v1[qid]["question"]}
    n0 = len(items)
    items = [x for x in items if x["question_id"] not in changed]
    print(f"left out {n0 - len(items)} answers to the {len(changed)} changed questions {sorted(changed)}", flush=True)
    for x in items:
        x["key_hash"] = key_hash(x["question_id"], v2)
    if a.shard:
        k, n = map(int, a.shard.split("/"))
        items = [x for x in items if int(hashlib.sha256(x["key"].encode()).hexdigest(), 16) % n == k]
    if a.n:
        items = [items[int(j * len(items) / a.n)] for j in range(a.n)]
    done = set()
    if jl.exists():
        done = {(r["key"], r.get("key_hash")) for r in map(json.loads, filter(str.strip, jl.read_text().splitlines()))}
    todo = [x for x in items if (x["key"], x["key_hash"]) not in done]
    print(f"{a.judge} on {a.source}: {len(items)} answers, {len(done)} done, {len(todo)} to judge; "
          f"key sha256 {key_sha[:12]}; servers {servers}", flush=True)

    q: queue.Queue = queue.Queue()
    for x in todo:
        q.put(x)
    lock = threading.Lock()
    num_ctx = J["options"]["num_ctx"]
    by_port = {s["port"]: s for s in servers}

    def worker(port: int) -> None:
        judge = Judge(OllamaProvider(f"http://127.0.0.1:{port}"), J["model"], dict(J["options"]),
                      truncate_chars=None, think=J["think"])
        while True:
            try:
                x = q.get_nowait()
            except queue.Empty:
                return
            t0 = time.time()
            res = judge.score(x["question"], x["expected"], x["concepts"], x["answer"],
                              answerable=x["answerable"], timeout=3600)
            f = res.as_row_fields()
            call = res.call
            tok = (call.tokens if call else {}) or {}
            status = f["judge_status"]
            if (tok.get("prompt") or 0) >= num_ctx - CTX_MARGIN:
                status = "out_of_context"
            elif call is not None and call.length_capped:
                status = "ok_output_limit" if status == "ok" else "output_limit"
            rec = {"key": x["key"], "source": x["source"], "row": x["row"], "question_id": x["question_id"],
                   "config": x["config"], "answerable": x["answerable"], "answer_chars": len(x["answer"]),
                   "judge": J["model"], "options": J["options"], "think": J["think"], "truncate_chars": None,
                   "port": port, "ollama": by_port[port]["ollama"], "model_digest": by_port[port]["model_digest"],
                   "key_sha256": key_sha, "key_hash": x["key_hash"], "status": status,
                   "scores": f.get("judge_scores") if status in ("ok", "ok_output_limit") else None,
                   "prompt_tokens": tok.get("prompt"), "output_tokens": tok.get("completion"),
                   "finish_reason": call.finish_reason if call else None,
                   "raw_text": call.text if call else None, "wall_s": round(time.time() - t0, 2),
                   "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            with lock:
                with jl.open("a") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{port} {x['key']} {rec['wall_s']}s {status}", flush=True)

    t0 = time.time()
    ths = [threading.Thread(target=worker, args=(p,)) for p in a.ports]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    el = time.time() - t0

    recs = [json.loads(l) for l in jl.read_text().splitlines() if l.strip()]
    st = Counter(r["status"] for r in recs)
    pt = [r["prompt_tokens"] or 0 for r in recs]
    ot = [r["output_tokens"] or 0 for r in recs]
    lines = [f"# S373 {a.judge} on {a.source} ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Judge {J['model']}, options {json.dumps(J['options'])}, think {J['think']}, answers complete. "
             f"Key {KEY.relative_to(ROOT)} sha256 {key_sha[:12]}.",
             "Servers: " + ", ".join(f"{s['port']} Ollama {s['ollama']} digest {s['model_digest']}" for s in servers), "",
             f"{len(recs)} answers judged; statuses {dict(st)}.",
             f"Prompt tokens: max {max(pt)} of num_ctx {num_ctx}. Output tokens: max {max(ot)} of num_predict "
             f"{J['options']['num_predict']}, median {statistics.median(ot)}.", ""]
    if todo:
        lines.append(f"This run: {len(todo)} answers in {el / 60:.1f} min on {len(a.ports)} servers, "
                     f"{el / len(todo):.2f} s per answer overall.")
    md.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
