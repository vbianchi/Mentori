"""R1: before any job, check that an Ollama server runs as LOCK.toml [server] says. A job does not start on a failure.

    uv run python -m experiments.runner.check_server --base http://127.0.0.1:11434 --log <server log> \
        [--binary <ollama executable> --machine macos|beelink] [--model <tag>]

Checks, each from the server itself, never from the environment of the process that launched it (memory: on
9 October ps showed settings Ollama ignored):
  version     /api/version is [server] ollama_version
  binary      with --binary: its sha256 is [server] binary_sha256 for --machine
  settings    the log's last "server config" line has OLLAMA_NUM_PARALLEL:1, OLLAMA_FLASH_ATTENTION:true and
              OLLAMA_KV_CACHE_TYPE:q8_0, and no "invalid environment variable" follows it
  model       with --model (after the job's fresh load, experiments/runner/job.py): /api/ps holds the tag with the
              lock's digest and context. The KV-cache lines this load wrote (the log after the offset the load
              started at) must all read "1/1 seqs" and "K (q8_0)", the largest "(<num_ctx> cells" (sliding-window
              models, gemma3 and gpt-oss, write a second, smaller line). The server writes its runner's lines in
              batches, sometimes only when the next model loads (Studio, 15 October), so the check waits 20 s and,
              if no line has come, records kv_cache as pending (ok null). A pending check is not a pass (D80 V6,
              audit F2): the check fails, as judge_passages refuses it; run check_server again with --since-offset
              (the offset is in the load record) to settle it later.
  runner      with --model and --since-offset (D80 V6, audit F2): the first "starting llama-server" line after the
              offset (the load's runner, whose KV-cache lines are read) has -c <num_ctx>, -np <num_parallel> and
              -b <num_batch>, and, with [server] shift false, no --context-shift. With --after-first-call (job.py,
              once the job's first real call has returned): exactly one runner started after the offset, so the
              runner the load certified is the one that answered; a second start means the first call replaced it.
              With --also <tag> ... (K1 review F3, 17 October: RAGAS embeds through bge-m3, which Ollama serves from
              a runner of its own): exactly one more runner per tag, each an --embedding runner with -np
              <num_parallel> and a weights blob other than the load's runner's, so the load's runner still answered
              and nothing else started.
  also_loaded with --also: /api/ps holds each tag with the lock's digest, and nothing but the job's model and
              these tags.
Prints one JSON object (every check, passed or not) and exits 1 if any check fails or is pending.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from experiments.runner.lock import load

KV = re.compile(r"\(\s*(\d+) cells,\s+\d+ layers,\s+(\d+)/(\d+) seqs\), K \((\w+)\)")   # sizes are space-padded: "(  8192 cells"
# D145 (Valerio, 26 October): Ollama 0.40.2 builds a speculative-decoding draft context for a model whose weights carry
# a multi-token-prediction layer (qwen3.8:27b, LOCK [judge] not_sent), with its own KV cache whose type Ollama fixes
# (f16, one layer). The KV lines after this marker are the draft's: recorded, not held to the lock's kv_cache_type; the
# target's lines before it are held as before. D85's 107-answer repeat check tests whether the draft changes a score.
MTP_DRAFT = "creating MTP draft context against the target model"
RUNNER = re.compile(r'msg="starting llama-server" cmd="((?:[^"\\]|\\.)*)"')   # D80 V6: the runner's command line


def runner_flags(cmd: str) -> dict:
    """What a runner start line names (D80 V6): its weights blob, context, parallel slots, batch, context shift, and
    whether it is an embedding runner (--embedding; K1 review F3)."""
    arg = lambda f: (re.search(rf"(?:^|\s){re.escape(f)}\s+(\S+)", cmd) or [None, None])[1]   # noqa: E731
    blob = re.search(r"--model\s+\S*?sha256-([0-9a-f]{12})", cmd)
    return {"blob": blob and blob[1], "c": arg("-c"), "np": arg("-np"), "b": arg("-b"),
            "context_shift": "--context-shift" in cmd.split(), "embedding": "--embedding" in cmd.split()}


def _get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def _read(log: Path, offset: int = 0) -> str:
    """The log from a byte offset (job.py takes it from the file size). Read as bytes: a text read turns the Windows
    log's CRLF into LF, so a byte offset used on the text overshoots by one character per line (Beelink, 15 October)."""
    return log.read_bytes()[offset:].decode(errors="replace")


def check(base: str, log: Path, binary: Path | None = None, machine: str | None = None,
          model: str | None = None, log_offset: int | None = None, kv_only: bool = False,
          after_first_call: bool = False, also: tuple = ()) -> dict:
    lock = load()
    if also and not (after_first_call and model is not None and log_offset is not None and not kv_only):
        raise ValueError("also needs after_first_call, a model and a log offset")
    s = lock.d["server"]
    out = {"base": base, "log": str(log), "lock_sha256": lock.sha256, "after_first_call": after_first_call, "checks": {}}
    c = out["checks"]
    if not kv_only:
        v = _get(f"{base}/api/version")["version"]
        c["version"] = {"ok": v == s["ollama_version"], "served": v, "lock": s["ollama_version"]}
    if binary is not None and not kv_only:
        h = hashlib.sha256(binary.read_bytes()).hexdigest()
        want = s["binary_sha256"].get(machine or "")
        c["binary"] = {"ok": h == want, "sha256": h, "lock": want, "machine": machine}
    text = _read(log)
    i = text.rfind('msg="server config"')
    if kv_only:
        since = text[i:] if i >= 0 else ""
    elif i < 0:
        c["settings"] = {"ok": False, "error": "no server config line in the log"}
        since = ""
    else:
        line = text[i:text.find("\n", i)]
        want = {"OLLAMA_NUM_PARALLEL": "1", "OLLAMA_FLASH_ATTENTION": "true", "OLLAMA_KV_CACHE_TYPE": s["kv_cache_type"]}
        got = {k: (re.search(rf"\b{k}:(\S+)", line) or [None, None])[1] for k in want}
        since = text[i:]
        bad_env = "invalid environment variable" in since
        c["settings"] = {"ok": got == want and not bad_env, "served": got, "lock": want,
                         "invalid_environment_variable": bad_env}
    if model is not None:
        judge = model in lock.judges()                     # D85: the main or the second judge
        want_call = lock.ollama(model, role="judge" if judge else "generator", draw=None if judge else 1)
        expect_ctx = want_call.options["num_ctx"]
        tag, digest = lock._run_tag(model)
        if not kv_only:
            ps = {m["name"]: m for m in _get(f"{base}/api/ps")["models"]}
            m = ps.get(tag)
            c["loaded"] = {"ok": bool(m) and m["digest"] == digest and m.get("context_length") == expect_ctx,
                           "tag": tag, "digest": m and m["digest"], "context_length": m and m.get("context_length"),
                           "lock_digest": digest, "lock_num_ctx": expect_ctx}
            if also:                                        # K1 review F3: the job's second model (RAGAS: bge-m3)
                want_also = dict(lock._run_tag(x) for x in also)
                c["also_loaded"] = {"ok": all(t in ps and d and ps[t]["digest"] == d for t, d in want_also.items())
                                          and set(ps) <= {tag, *want_also},
                                    "held": {n: x["digest"] for n, x in ps.items()}, "lock": want_also}
        kv = []
        for _ in range(20):
            fresh = _read(log, log_offset) if log_offset is not None else since
            end = fresh.find("load_model: initializing") if log_offset is not None else -1
            if log_offset is not None and end < 0:          # this load's block is not complete in the log yet
                time.sleep(1)
                continue
            block = fresh[:end] if end >= 0 else fresh
            cut = block.find(MTP_DRAFT)                    # D145: qwen3.8's MTP draft context, built after the target's
            kv, draft = (KV.findall(block[:cut]), KV.findall(block[cut:])) if cut >= 0 else (KV.findall(block), [])
            break
        if kv:
            lines = [{"cells": int(cl), "seqs": f"{u}/{sq}", "k_type": k} for cl, u, sq, k in kv]
            main = max(lines, key=lambda x: x["cells"])
            c["kv_cache"] = {"ok": main["cells"] == expect_ctx and all(x["seqs"] == "1/1" and x["k_type"] == s["kv_cache_type"]
                                                                       for x in lines),
                             "main_cells": main["cells"], "lines": lines,
                             "read": "this load's lines" if log_offset is not None else "every load since the server config"}
            if draft:                                       # recorded, not held to the lock's type (D145)
                c["kv_cache"]["mtp_draft_lines"] = [{"cells": int(cl), "seqs": f"{u}/{sq}", "k_type": k}
                                                    for cl, u, sq, k in draft]
        else:
            c["kv_cache"] = {"ok": None, "pending": True, "log_offset": log_offset,
                             "note": "no KV-cache line from this load yet; settle with --since-offset"}
        if log_offset is not None:                          # D80 V6 (audit F2): the runner's own flags
            starts = [runner_flags(x) for x in RUNNER.findall(fresh)]
            want = {"c": str(expect_ctx), "np": str(s["num_parallel"]), "b": str(want_call.options["num_batch"])}
            first = starts[0] if starts else None
            flags_ok = bool(first) and {k: first[k] for k in want} == want and (s["shift"] or not first["context_shift"])
            # after the first call: the load's runner, and one --embedding runner per tag in also (K1 review F3).
            # D99 (O1, 19 Oct): a later start of the load's own model with the load's flags is a reload (keep_alive
            # expired before the first call, G4 port 11456 on 19 Oct) and passes; one with other flags fails.
            same = lambda x: not x["embedding"] and {k: x[k] for k in (*want, "blob", "context_shift")} == \
                {k: first[k] for k in (*want, "blob", "context_shift")}   # noqa: E731
            reloads = [x for x in starts[1:] if same(x)] if first else []
            others = [x for x in starts[1:] if not same(x)] if first else starts
            extra_ok = len({x["blob"] for x in others}) == len(also) and all(
                x["embedding"] and x["np"] == str(s["num_parallel"]) and x["blob"] != first["blob"] for x in others)
            c["runner"] = {"ok": flags_ok and (extra_ok or not after_first_call), "starts": starts,
                           "reloads": len(reloads), "lock": {**want, "shift": s["shift"]},
                           "read": (f"every runner since the load (one expected, plus one --embedding runner for "
                                    f"each of {list(also)}; a reload with the load's flags passes, D99)" if also else
                                    "every runner since the load (one expected; a reload with the load's flags passes, D99)")
                                   if after_first_call else "the load's runner (the first after the offset)"}
    # D80 V6 (audit F2): a pending check (ok null) fails, as judge_passages refuses it; it was a pass here
    out["ok"] = all(x["ok"] is True for x in c.values())
    out["pending"] = [k for k, x in c.items() if x["ok"] is None]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:11434")
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--binary", type=Path)
    ap.add_argument("--machine", choices=["macos", "beelink"])
    ap.add_argument("--model")
    ap.add_argument("--since-offset", type=int, help="read only the log after this byte offset (a load record's)")
    ap.add_argument("--kv-only", action="store_true", help="with --since-offset: settle a pending KV-cache check only")
    ap.add_argument("--after-first-call", action="store_true",
                    help="with --since-offset: one runner only since the load (D80 V6; job.py after-first-call)")
    ap.add_argument("--also", nargs="*", default=[], help="with --after-first-call: the job's embedding models (K1 "
                    "review F3), each allowed one --embedding runner and required in /api/ps")
    a = ap.parse_args()
    out = check(a.base.rstrip("/"), a.log, a.binary, a.machine, a.model, log_offset=a.since_offset, kv_only=a.kv_only,
                after_first_call=a.after_first_call, also=tuple(a.also))
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
