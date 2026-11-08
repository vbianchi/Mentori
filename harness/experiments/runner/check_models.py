"""C5: every Ollama model in LOCK.toml [models] loads at the lock's context and answers under the lock, on one server.

    uv run python -m experiments.runner.check_models --base http://127.0.0.1:11441 --log <server log> \
        --binary <ollama executable> --machine macos --out <dir>

For each model this machine holds (by [models] machines): a fresh load (experiments/runner/job.py: unload all, load
at the lock's context, check_server with --model), then one short prompt as generator at the maker's default
(D66), and, where the model has a thinking mode that can be turned off, once more with thinking off. Records:
<out>/models.jsonl, one line per call with the D37 record plus the load check. A model that fails to load, fails
the server check, or answers with any status other than ok is reported; nothing stops the remaining models.
After a model's first answer the server is checked again (job.py after_first_call, D80 V6): a failure is reported
as a setup error, written into the model's loads.jsonl line, and the model's remaining call is not made.

Questions it answers before any run depends on them: does each model fit and load at 131,072 tokens of context
(or its own maximum, [exceptions]) with the q8_0 cache; does thinking come back when it should and stay away when
it is off; what does one call cost in load, prompt and generation time.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from experiments.runner.job import after_first_call, fresh_load
from experiments.runner.lock import LockError, load
from experiments.runner.ollama_client import generate

PROMPT = ("In two sentences: what does the STAR aligner do in an RNA-seq pipeline, and what file does it "
          "produce for the next step?")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:11441")
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--binary", type=Path)
    ap.add_argument("--machine", default="macos")
    ap.add_argument("--holder", default="studio", help="the [models] machines name of this machine")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    lock = load()
    base = a.base.rstrip("/")
    a.out.mkdir(parents=True, exist_ok=True)
    out = a.out / "models.jsonl"
    copies = {v: k for k, v in lock.d.get("date", {}).get("model_copy", {}).items()}
    tags = [copies.get(t, t) for t, row in lock.d["models"].items()
            if a.holder in row["machines"] and t != lock.d["scorers"]["embedding"]]
    bad = []
    for model in tags:
        try:
            load_rec = fresh_load(base, model, a.log, a.binary, a.machine)
        except Exception as e:                                   # noqa: BLE001 - recorded, next model
            load_rec = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        modes = [None]                                       # None: the generator rule, the maker's default
        try:
            lock.ollama(model, draw=1)
        except LockError:
            if model not in lock.judges():
                raise
            modes = ["judge"]                                # D85: a judge with no generator row answers as judge
        try:
            if lock.ollama(model, draw=1, thinking="off").fields != lock.ollama(model, draw=1).fields:
                modes.append("off")
        except LockError:
            pass
        for mode in modes if load_rec.get("ok") else []:
            call = lock.ollama(model, role="judge") if mode == "judge" else lock.ollama(model, draw=1, thinking=mode)
            mode = mode or "default"
            rec = generate(base, call, PROMPT)
            rec.update(check="C5", thinking_mode=mode, load_check_ok=load_rec["ok"],
                       thinking_returned=bool(rec["thinking_text"].strip()))
            with out.open("a") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{time.strftime('%H:%M:%S')} {model:28s} {mode:8s} {rec['status']:8s} think-text "
                  f"{'yes' if rec['thinking_returned'] else 'no ':3s} prompt {rec['prompt_tokens']} out "
                  f"{rec['output_tokens']} load {rec['load_s']} s wall {rec['wall_s']} s", flush=True)
            if rec["status"] != "ok":
                bad.append(f"{model} {mode}: {rec['status']} {rec['error']}")
            if "after_first_call" not in load_rec:          # D80 V6: the runner that answered is the one checked
                try:
                    after_first_call(load_rec, a.log, a.binary, a.machine, first=rec)
                except Exception as e:                       # noqa: BLE001 - SetupError or the check's own error
                    load_rec["ok"] = False
                    load_rec.setdefault("after_first_call", {"ok": False, "error": f"{type(e).__name__}: {e}"})
                    bad.append(f"{model}: setup error after the first call: {e}")
                    print(f"{time.strftime('%H:%M:%S')} {model:28s} REFUSED (setup error) {e}", flush=True)
                    break
        if not load_rec.get("ok") and "after_first_call" not in load_rec:
            failed = {k: v for k, v in (load_rec.get("server_check") or {}).get("checks", {}).items() if not v["ok"]}
            bad.append(f"{model}: load or server check failed {load_rec.get('error') or failed}")
            print(f"{time.strftime('%H:%M:%S')} {model:28s} LOAD FAILED {load_rec.get('error') or failed}", flush=True)
        with (a.out / "loads.jsonl").open("a") as fh:
            fh.write(json.dumps({"model": model, **load_rec}, ensure_ascii=False) + "\n")
    print(f"C5 DONE: {len(tags)} models, {len(bad)} problems", *bad, sep="\n", flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
