#!/usr/bin/env python3
"""S376 - judge calibration re-run against ground truth v2.1 (A6), with the defects of the original fixed.

WHY. The paper chose its judge (qwen3-coder) by scoring 107 answers with 19 candidate judges and
correlating each judge's scores with two reference measures computed against the answer key
(exp_v4_0_judge_scoring.py, exp_v4_0_objective_metrics.py). Both sides used the old key, which ground
truth v2.1 replaces. An audit on 9 October found, and Valerio ruled on the same day:
  B1  a failed or unparsed judge call was scored 0 on every dimension and entered the correlations
      (glm-4.7-flash 10, olmo-3 7, qwen3:235b 6 of 107): here such calls are UNSCORED, and each
      judge's scoring rate is reported, since a judge must be able to score every answer
  B2  the judge saw the first 3,000 characters of the answer (more than half of the 107 answers are
      longer), the similarity reference the first 2,000 of answer and key: here complete answers
  B3  think false is ignored by gpt-oss: both gpt-oss judges run at effort "low", as the second judge
      of the paper now does; every other judge runs with think false
  B4  six of the eight answer generators are also judge candidates: all scores are kept, and the
      analysis reports the ranking with and without each judge's own answers
  B5  bootstrap intervals over the 107 answers (analysis step)
  infra_error: an empty reply from the server (no tokens, no stop reason) is retried twice and then
      recorded as infra_error, which is not the judge's failure and not part of its scoring rate; three
      in a row stop that judge. Before each judge the server is emptied of resident models.
  same settings for every judge: temperature 0, num_ctx 32768 (the smallest native context among
  the judges, mistral and gemma3n), num_predict 8192 (qwen3:235b and olmo-3 exceed 1,024)
The 19 original judges are the selection. gemma4:26b, gemma4:31b and qwen3.8:27b-mlx run alongside as
a later check that reopens the choice only on an indisputable win (O9, fixed before the run).

The judge prompt is the archived harness template (S141_runner.judge.build_prompt reads it from
exp_common.py), unchanged.

    .venv/bin/python scripts/S376_judge_calibration.py judge --ports 11451 11452 11453
Writes findings/recompute/S376_judge_calibration.jsonl (resumable by judge and answer, under the same
per-question key hash) and a .md summary of scoring rates and limits. The analysis is a separate step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import queue
import sys
import threading
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB, RECOMPUTE, ROOT  # noqa: E402
from S141_runner.judge import Judge  # noqa: E402
from S141_runner.providers import OllamaProvider  # noqa: E402

KEY = ROOT / "data/ground_truth_v2/all_v2_4.json"   # Q50, 11 October 09:00: v2.4, the key the judge uses (S373.KEY); the
# 16 answers on its two questions v2.4 changed (02_snakemake_FR1, 06_star_aligner_TE3) are judged again. Q45: v2.3, whose
# 20 answers on its three changed calibration questions were judged again. Q14, 9 October: calibrate on the final key. The first run
# (9 October, 09:08-17:25) used all_v2_1.json; its rows stay in the ledger, and resume by key hash re-judges only
# the answers whose question's key changed in v2.2 (S376b keeps the rows scored against the current key)
ANSWERS = PUB / "results/exp00_phase2_latest.json"
OUT = RECOMPUTE / "S376_judge_calibration.jsonl"
OPTIONS = {"temperature": 0, "num_ctx": 32768, "num_predict": 8192}
CTX_MARGIN = 64
SELECTION = ["qwen3:235b", "gemma3:27b-it-qat", "qwen3.5:122b", "llama3.2:latest", "ministral-3:3b",
             "gemma3:latest", "gpt-oss:120b", "mistral:latest", "olmo-3:latest", "ministral-3:8b",
             "qwen3-coder-next:q4_K_M", "gemma3n:latest", "ministral-3:14b", "deepseek-r1:70b",
             "gpt-oss:20b", "devstral-small-2:24b", "gemma3:27b", "qwen3-coder:latest", "glm-4.7-flash:latest"]
LATER = ["gemma4:26b", "gemma4:31b", "qwen3.8:27b-mlx"]
THINK = {"gpt-oss:120b": "low", "gpt-oss:20b": "low"}


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def unload(port: int, model: str) -> None:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/generate", data=json.dumps({"model": model, "keep_alive": 0}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=120).read()
    except Exception:  # noqa: BLE001 - unloading is housekeeping
        pass


def unload_all(port: int) -> None:
    """Free the server before a judge loads: a model resident from an earlier run (keep-alive 24h on the
    overnight servers) once took the Mac Studio past its 512 GB and every qwen3:235b call came back
    empty with a Metal "Compute error" (9 October, first attempt)."""
    for m in get(f"http://127.0.0.1:{port}/api/ps")["models"]:
        unload(port, m["name"])


def loaded_digest(port: int, model: str) -> str | None:
    """The digest of the model the server has loaded. The model list (/api/tags) can name one model twice
    with two digests, a manifest list and its entry (devstral-small-2:24b on 0.40.1), so it cannot say
    which ran; the S376 ledger of 9 October carries the list's value, afc64477bb4b for devstral, where
    the server had loaded 33af3142213a (the same 15 GB model file)."""
    for m in get(f"http://127.0.0.1:{port}/api/ps")["models"]:
        if m["name"] == model:
            return m["digest"][:12]
    return None


def answers_and_key() -> list[dict]:
    v2 = {r["id"]: r for r in json.loads(KEY.read_text())["records"]}
    rows = [r for r in json.loads(ANSWERS.read_text())["per_question_results"] if r.get("completed") and r.get("final_answer")]
    out = []
    for r in rows:
        rec = v2[r["question_id"]]
        ea = rec["short_answer"] + (("\n\n" + rec["synthesis_statement"]) if rec.get("synthesis_statement") else "")
        ec = [k["phrase"] for k in rec["key_concepts"]]
        out.append({"answer_key": f"{r['model']}|{r['question_id']}", "generator": r["model"], "question_id": r["question_id"],
                    "question": r["question"], "answerable": r.get("answerable", True) in (True, "true", "True"),
                    "expected": ea, "concepts": ec, "answer": r["final_answer"],
                    "key_hash": hashlib.sha256(json.dumps([ea, ec], ensure_ascii=False).encode()).hexdigest()[:16]})
    return out


def judge(a) -> int:
    items = answers_and_key()
    assert len(items) == 107, f"expected the 107 completed answers, got {len(items)}"
    judges = SELECTION + LATER
    if a.judges:   # a subset, in the order given (10 October: the ranking-relevant judges before the slow ones)
        unknown = [m for m in a.judges if m not in judges]
        if unknown:
            raise SystemExit(f"FATAL: not calibration judges: {unknown}")
        judges = list(a.judges)
    for p in a.ports:
        tags = {m["name"] for m in get(f"http://127.0.0.1:{p}/api/tags")["models"]}
        missing = [m for m in judges if m not in tags]
        if missing:
            raise SystemExit(f"FATAL: port {p} lacks {missing}")
    done = set()
    if OUT.exists():
        done = {(r["judge"], r["answer_key"], r["key_hash"]) for r in map(json.loads, filter(str.strip, OUT.read_text().splitlines()))}
    q: queue.Queue = queue.Queue()
    for m in (judges if a.judges else sorted(judges, key=lambda m: m != "qwen3:235b")):   # default: the slowest first
        todo = [x for x in items if (m, x["answer_key"], x["key_hash"]) not in done]
        if todo:
            q.put((m, todo))
    lock = threading.Lock()
    print(f"{len(judges)} judges x {len(items)} answers; {len(done)} done; settings {OPTIONS}", flush=True)

    def worker(port: int) -> None:
        version = get(f"http://127.0.0.1:{port}/api/version")["version"]
        while True:
            try:
                m, todo = q.get_nowait()
            except queue.Empty:
                return
            unload_all(port)
            j = Judge(OllamaProvider(f"http://127.0.0.1:{port}", keep_alive="30m"), m, dict(OPTIONS),
                      truncate_chars=None, think=THINK.get(m, False))
            t_m = time.time()
            infra_streak = 0
            for x in todo:
                t0 = time.time()
                for attempt in range(3):
                    res = j.score(x["question"], x["expected"], x["concepts"], x["answer"], answerable=x["answerable"], timeout=3600)
                    call = res.call
                    # an empty reply with no stop reason and no tokens is the server failing, not the judge
                    infra = call is not None and not (call.text or "").strip() and not call.finish_reason \
                        and not (call.tokens or {}).get("completion")
                    if not infra:
                        break
                    time.sleep(30)
                f = res.as_row_fields()
                tok = (call.tokens if call else {}) or {}
                status = f["judge_status"]
                if infra:
                    status = "infra_error"
                    infra_streak += 1
                else:
                    infra_streak = 0
                if (tok.get("prompt") or 0) >= OPTIONS["num_ctx"] - CTX_MARGIN:
                    status = "out_of_context"
                elif call is not None and call.length_capped:
                    status = "ok_output_limit" if status == "ok" else "output_limit"
                rec = {"judge": m, "group": "selection" if m in SELECTION else "later_check", "think": THINK.get(m, False),
                       "answer_key": x["answer_key"], "generator": x["generator"], "question_id": x["question_id"],
                       "answer_chars": len(x["answer"]), "key_hash": x["key_hash"], "options": OPTIONS,
                       "port": port, "ollama": version, "model_digest": loaded_digest(port, m), "status": status,
                       "scores": f.get("judge_scores") if status in ("ok", "ok_output_limit") else None,
                       "attempts": f.get("judge_attempts"), "error_class": f.get("judge_error_class"),
                       "prompt_tokens": tok.get("prompt"), "output_tokens": tok.get("completion"),
                       "finish_reason": call.finish_reason if call else None,
                       "raw_text": call.text if call else None, "wall_s": round(time.time() - t0, 2),
                       "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                with lock:
                    with OUT.open("a") as fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"{port} {m} {x['answer_key']} {rec['wall_s']}s {status}", flush=True)
                if infra_streak >= 3:
                    print(f"{port} {m} STOPPED: the server returned empty replies three answers in a row", flush=True)
                    break
            print(f"{port} {m} done: {len(todo)} answers in {(time.time() - t_m) / 60:.1f} min", flush=True)
            unload(port, m)

    t0 = time.time()
    ths = [threading.Thread(target=worker, args=(p,)) for p in a.ports]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    recs = [json.loads(l) for l in OUT.read_text().splitlines() if l.strip()]
    by = defaultdict(list)
    for r in recs:
        by[r["judge"]].append(r)
    lines = [f"# S376 judge calibration, judging step ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Answers: {ANSWERS.name}, the 107 completed. Key {KEY.relative_to(ROOT)}. Settings {json.dumps(OPTIONS)}; "
             f"think false except gpt-oss (low). Complete answers. Run time {(time.time() - t0) / 60:.0f} min.", "",
             "| Judge | Group | Digest | Scored | Not scored (status) | Max prompt tokens | Max output tokens |",
             "|---|---|---|---:|---|---:|---:|"]
    for m in judges:
        rs = by.get(m, [])
        st = Counter(r["status"] for r in rs)
        scored = sum(r["scores"] is not None for r in rs)
        lines.append(f"| {m} | {'selection' if m in SELECTION else 'later check'} | {rs[0]['model_digest'] if rs else ''} | "
                     f"{scored} of {len(rs)} | {', '.join(f'{k} {v}' for k, v in st.items() if k not in ('ok', 'ok_output_limit')) or 'none'} | "
                     f"{max((r['prompt_tokens'] or 0) for r in rs) if rs else ''} | {max((r['output_tokens'] or 0) for r in rs) if rs else ''} |")
    (RECOMPUTE / "S376_judge_calibration.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["judge"])
    ap.add_argument("--ports", nargs="+", type=int, required=True)
    ap.add_argument("--judges", nargs="+", default=None, help="only these judges, in this order (resume as usual)")
    a = ap.parse_args()
    return judge(a)


if __name__ == "__main__":
    raise SystemExit(main())
