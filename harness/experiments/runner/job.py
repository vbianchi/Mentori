"""F1: the start of every job. A model's text can depend on what the server computed just before (on the Beelink,
15 October: the same prompt gave S440's text only after a fresh load), so every job starts from the same state.

    uv run python -m experiments.runner.job fresh-load --base http://127.0.0.1:<port> --model devstral-small-2:24b \
        --log <server log> [--binary <ollama executable> --machine macos|beelink] --record <file.json>
    uv run python -m experiments.runner.job after-first-call --record <file.json> --log <server log> \
        [--binary <ollama executable> --machine macos|beelink]

fresh-load: unloads every model the server holds, loads the job's model with what a real call sends (D80 V6,
audit F2: the lock's options and its fields truncate, shift, keep_alive and think, as ollama_client sends them; no
prompt, so nothing is generated), then runs check_server with --model. A load that sent only the context and batch
started a --context-shift runner, which the first real call replaced with one no check read. --base has no default
(D92 Q199, audit of 17 October F51: it was 127.0.0.1:11434, the laptop's S2 server). fresh-load itself does not check
whether another job uses the server. Some launchers check before calling it: K1 (k1_lib.sh, server_users.py survey),
S3 (S3_runs/s3_guard.py), G4 (g4_queue.sh port_users), G1 (launch_g1.sh, rerun_d89.sh: no established connection on
11453). K0 (run_k0.sh) checks only that no other RAGChecker process runs on the machine; the S2 launchers
(run_s2_laptop.sh, the Studio's run_s2_variant.sh) check nothing. Writes the record
(what was unloaded, the load request, load time, every check) and exits 1 if a check fails or is pending (a
pending KV-cache check refuses, as judge_passages refuses it), so the job does not start.

after-first-call (D80 V6): once the job's first real call has returned, check_server again on the log since the
load's offset, every check of the load plus one runner only since the load (the runner the load certified is the
one that answered). --also <tag> ... (K1 review F3, 17 October) names the job's embedding models (RAGAS: bge-m3,
which Ollama serves from a runner of its own): run the check once each has been called, and it then expects exactly
one --embedding runner per tag beside the load's, and each tag in /api/ps with the lock's digest. The result goes into the load record ("after_first_call"); on a failure the record's ok turns
false, the function raises SetupError and the command exits 1. No model-scored row is recorded after a failed
certification; what the job wrote before the check stays (check_models has appended the first answer, judge_passages
the first call's line in its calls log and any no_answer row).

The rest of the routine belongs to each job script: items in a fixed order, recorded; a resumed job records where
it resumed; the job ends by re-running its first 10 items after another fresh load and comparing.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

from experiments.runner.check_server import check
from experiments.runner.lock import load


def _post(url: str, body: dict, timeout: float | None = None) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


class SetupError(RuntimeError):
    """The server does not run the job's model as the lock says (D80 V6). The caller makes no further call to that
    model on this load (judge_passages refuses the job, check_models moves to the next model), so no model-scored
    row is recorded after it; rows written before the check stay."""


def load_request(call) -> dict:
    """D80 V6 (audit F2): the load request, with no prompt: model, the options whole and the fields whole, exactly
    as ollama_client.generate and chat send them (payload keys "options" and **call.fields). Whatever decides
    Ollama's runner (num_ctx, num_batch, shift, truncate) is then the same in the load and in the job's calls."""
    return {"model": call.model, "options": dict(call.options), **call.fields}


def fresh_load(base: str, model: str, log: Path, binary: Path | None, machine: str | None) -> dict:
    lock = load()
    judge = model in lock.judges()                         # D85: the main or the second judge
    call = lock.ollama(model, role="judge" if judge else "generator", draw=None if judge else 1)
    rec = {"base": base, "model": call.model, "requested": model, "lock_sha256": lock.sha256,
           "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    held = [m["name"] for m in json.loads(urllib.request.urlopen(f"{base}/api/ps", timeout=30).read())["models"]]
    for name in held:
        _post(f"{base}/api/generate", {"model": name, "keep_alive": 0}, timeout=300)
    rec["unloaded"] = held
    offset = log.stat().st_size                  # the check reads only what this load writes after here
    body = load_request(call)
    rec["load_options_sent"] = body["options"]
    rec["load_fields_sent"] = {k: v for k, v in body.items() if k not in ("model", "options")}
    t0 = time.time()
    _post(f"{base}/api/generate", body)
    rec["load_s"] = round(time.time() - t0, 2)
    rec["log_offset"] = offset
    rec["server_check"] = check(base, log, binary, machine, model, log_offset=offset)
    # D80 V6 (audit F2): a pending check (ok null) is not a pass, as judge_passages refuses it
    rec["ok"] = rec["server_check"]["ok"] is True and not rec["server_check"]["pending"]
    return rec


def after_first_call(rec: dict, log: Path, binary: Path | None, machine: str | None, first: dict | None = None,
                     also: tuple = ()) -> dict:
    """D80 V6 (audit F2): check_server again once the job's first real call has returned (first: its record), on the
    log since the load's offset, with one runner only since the load. Writes rec["after_first_call"] (the check, and
    the first call's status, load_s and request_sha256) and turns rec["ok"] false on a failure or a pending check;
    raises SetupError then."""
    chk = check(rec["base"], log, binary, machine, rec.get("requested", rec["model"]), log_offset=rec["log_offset"],
                after_first_call=True, also=tuple(also))
    chk["also"] = list(also)
    chk["first_call"] = first and {k: first.get(k) for k in ("status", "load_s", "request_sha256", "at")}
    chk["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rec["after_first_call"] = chk
    passed = chk["ok"] is True and not chk["pending"]
    rec["ok"] = bool(rec.get("ok")) and passed
    if not passed:
        bad = {k: v for k, v in chk["checks"].items() if v["ok"] is not True}
        raise SetupError(f"{rec['model']}: the server check after the first call did not pass: {json.dumps(bad)}")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fresh-load")
    f.add_argument("--base", required=True, help="the server to load (no default, D92 Q199, audit of 17 October F51: "
                   "a fresh load unloads every model the server holds, so the server is always named)")
    f.add_argument("--model", required=True)
    f.add_argument("--log", required=True, type=Path)
    f.add_argument("--binary", type=Path)
    f.add_argument("--machine", choices=["macos", "beelink"])
    f.add_argument("--record", required=True, type=Path)
    g = sub.add_parser("after-first-call")
    g.add_argument("--record", required=True, type=Path, help="the fresh-load record; the result is written into it")
    g.add_argument("--log", required=True, type=Path)
    g.add_argument("--binary", type=Path)
    g.add_argument("--machine", choices=["macos", "beelink"])
    g.add_argument("--also", nargs="*", default=[], help="the job's embedding models (K1 review F3): one --embedding "
                   "runner each is expected beside the load's, and each in /api/ps with the lock's digest")
    a = ap.parse_args()
    if a.cmd == "after-first-call":
        rec = json.loads(a.record.read_text())
        try:
            after_first_call(rec, a.log, a.binary, a.machine, also=tuple(a.also))
            refused = None
        except SetupError as e:
            refused = str(e)
        a.record.write_text(json.dumps(rec, indent=1) + "\n")
        print(*[f"{k}: {'ok' if v['ok'] else 'pending' if v['ok'] is None else 'FAIL'}"
                for k, v in rec["after_first_call"]["checks"].items()], sep="\n")
        if refused:
            print(f"REFUSED (setup error): {refused}")
        return 0 if refused is None else 1
    rec = fresh_load(a.base.rstrip("/"), a.model, a.log, a.binary, a.machine)
    a.record.parent.mkdir(parents=True, exist_ok=True)
    a.record.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("model", "unloaded", "load_s", "log_offset", "ok")}),
          *[f"{k}: {'ok' if v['ok'] else 'pending' if v['ok'] is None else 'FAIL'}"
            for k, v in rec["server_check"]["checks"].items()], sep="\n")
    return 0 if rec["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
