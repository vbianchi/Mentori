#!/usr/bin/env python3
"""Generate answers to a curated key's questions with Figure 2's strategies, through the paper's own exp_01 (I2, D160 (14)).

    # the work list: no model call, no file written
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/i2_generate.py --dry-run
    # the smoke (launch_i2.sh smoke runs this): PB_001, single pass, draw 1, its own .smoke run
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/i2_generate.py \
        --configs single_pass --smoke --ollama-url http://127.0.0.1:11499
    # one config, three draws (launch_i2.sh run starts one such process at a time)
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/i2_generate.py \
        --configs rlm_10 --draws 1 2 3 --ollama-url http://127.0.0.1:11499

WHAT IT RUNS. experiments/mentori/publication/scripts/exp_01_generation.py, Figure 2's generation script, loaded from
its file and run through its own run_experiment and dry_run: the same strategies (single_pass, multi_hop, rlm_5,
rlm_10, rlm_20, verified_pass; D160 (14) Q-I2b O-b), the same generator (gemini::gemini-3-flash-preview, D27), the
same verifier, the lock, the run contexts, the rolling pools, the answer records and the resume rules. exp_01 is not
edited. Three things differ, each set only inside this process:
  1. THE QUESTIONS. exp_01's run_questions is replaced by one that returns the curated key's questions (plant_key.py:
     key_v1_1.json by default, sha256-pinned, in the runner's FIELDS form), the first one only with --smoke. exp_01
     reads its questions through run_questions alone (dry_run and run_experiment). --question-ids-file is not taken.
  2. THE INDEX. --index (default i2_plant5, built by build_index.py) in place of exp_v4_s20_n0. exp_01's main() would
     refuse an index that is not a 20-paper one (the 135 questions are in scope at 20 papers, D48); this driver calls
     run_experiment directly, so that check, which is about the paper's key, does not apply. Run ids are exp_01's:
     exp_01__<config>__<index>[.smoke]; answer keys <index>|<config>|<question_id>|d<draw>. The index name keeps
     them apart from every paper run.
  3. THE SINKS AND THE MEMORY RULE. --sink-root (default findings/recompute/I2_runs/sinks; --smoke:
     findings/recompute/I2_runs/smoke_sinks), never findings/runs. Before each answer starts, free memory is read
     (i2_memory.py); under --min-free-gb (default 2, D160 (14) Q-I2e O-a) the answer is not started: exp_01's
     _process_one is wrapped so that it raises MemoryFloor, which is added to exp_01's STOPS, so exp_01's pool starts
     no other answer, stores the answers already in flight and ends the run (Q38's path for a lock refusal: nothing
     is stored for the key that did not start). The process exits EXIT_MEMORY; --resume starts it again later.
     A sampler reads free memory every --sample-s seconds for the whole process and the lowest reading goes into the
     process's record line (--record-file, default findings/recompute/I2_runs/i2_generate.jsonl), with
     memory_ok = the lowest reading stayed at or above the floor. launch_i2.sh run refuses unless the smoke's line
     has memory_ok true (Q-I2e: generate only with 2 GB free after the smoke).
ONE PROCESS AT A TIME (Q-I2e). The process holds an exclusive lock on findings/recompute/I2_runs/.i2_generate.lock for
its life; a second one exits EXIT_BUSY before reading anything.

K1's GUARD. The laptop's K1 launcher counts any process whose command line matches exp_[0-9]+...\\.py or names its
port as a user of its Ollama server (findings/recompute/K1/run_k1_laptop.sh:18). This driver loads exp_01 from its
file with importlib under the name i2_exp01, so no command line names it; the five configs without a verifier name
--ollama-url http://127.0.0.1:11499, where nothing listens, as T2 does (findings/recompute/T2_runs/t2_lib.sh), and make
no Ollama call (the generator is Gemini; the encoders run in-process on the CPU, LOCK [retrieval]). verified_pass
calls its verifier gpt-oss:20b on --ollama-url, so it waits until the laptop's K1 share ends (launch_i2.sh).

Exit codes: 0 done; 1 exp_01's own refusals (SystemExit); EXIT_MEMORY 4 stopped for memory; EXIT_BUSY 75 another
I2 generation process holds the lock.
"""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from experiments.reuse_demo import i2_memory, plant_key  # noqa: E402

MENTORI = ROOT / "experiments" / "mentori"
SCRIPTS = MENTORI / "publication" / "scripts"
EXP01 = SCRIPTS / "exp_01_generation.py"
I2_RUNS = ROOT / "findings" / "recompute" / "I2_runs"
SINKS = I2_RUNS / "sinks"
SMOKE_SINKS = I2_RUNS / "smoke_sinks"
RECORD_FILE = I2_RUNS / "i2_generate.jsonl"
LOCK_FILE = I2_RUNS / ".i2_generate.lock"
DEFAULT_INDEX = "i2_plant5"
NO_SERVER_URL = "http://127.0.0.1:11499"     # nothing listens there (t2_lib.sh NO_SERVER_URL)
NO_SERVER_CONFIGS = ("single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20")
EXIT_MEMORY = 4
EXIT_BUSY = 75
MODULE_NAME = "i2_exp01"


class MemoryFloor(RuntimeError):
    """Free memory under the floor before an answer started (D160 (14)): the run stops as on a lock refusal."""


def load_exp01(path: Path = EXP01):
    """exp_01 loaded from its file under MODULE_NAME (no command line names it; module docstring, K1's GUARD)."""
    for p in (str(SCRIPTS), str(MENTORI)):
        if p not in sys.path:
            sys.path.insert(0, p)
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    for name in ("run_questions", "run_experiment", "dry_run", "_process_one", "STOPS", "CONFIG_NAMES"):
        if not hasattr(mod, name):
            raise SystemExit(f"REFUSED: exp_01 has no {name}; this driver was written against the exp_01 that has it")
    return mod


def plant_questions(key: plant_key.Key):
    """exp_01's run_questions for the key (module docstring, 1): (questions, None); --max-questions n keeps the first n."""
    def run_questions(max_questions, question_ids_file, draws):
        if question_ids_file is not None:
            raise SystemExit("--question-ids-file is not an I2 option (the key's questions run); nothing run")
        qs = key.questions()
        return (qs[:max_questions] if max_questions else qs), None
    return run_questions


def install(mod, key: plant_key.Key, floor_gb: float, reader=None) -> dict:
    """Replaces exp_01's run_questions with the key's and wraps _process_one with the memory rule (module docstring).
    reader: (floor) -> (under, reading), default i2_memory.under. Returns the counters the record line reports."""
    seen = {"checks": 0, "stopped": None}
    mod.run_questions = plant_questions(key)
    original = getattr(mod._process_one, "_i2_original", mod._process_one)   # installed again: wrap exp_01's own

    async def guarded(*args, **kw):
        low, r = (reader or i2_memory.under)(floor_gb)
        seen["checks"] += 1
        if low:
            q = kw.get("q") or {}
            msg = (f"free memory {'unknown' if r is None else f'{r:.2f} GB'} is under the floor of {floor_gb} GB "
                   f"before {kw.get('config')} {q.get('id')} d{getattr(kw.get('ctx'), 'draw', '?')} started "
                   f"(D160 (14)); nothing stored for it, the run stops after the answers in flight")
            seen["stopped"] = msg
            raise MemoryFloor(msg)
        return await original(*args, **kw)

    guarded._i2_original = original
    mod._process_one = guarded
    if MemoryFloor not in mod.STOPS:
        mod.STOPS = (*mod.STOPS, MemoryFloor)
    return seen


def hold_lock(path: Path | None = None):
    """The one-process lock (module docstring; default LOCK_FILE); exits EXIT_BUSY when another process holds it."""
    path = Path(path or LOCK_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(f"BUSY: another I2 generation process holds {path}; nothing done", flush=True)
        sys.exit(EXIT_BUSY)
    return fh


def write_record(path: Path, line: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="I2: exp_01 on a curated key's questions (module docstring).")
    ap.add_argument("--configs", nargs="+", default=list(NO_SERVER_CONFIGS),
                    choices=["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"],
                    help="default: the five configs without a verifier (verified_pass needs its server)")
    ap.add_argument("--draws", nargs="+", type=int, default=[1, 2, 3], choices=[1, 2, 3])
    ap.add_argument("--smoke", action="store_true", help="the first question, draw 1, its own .smoke runs")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--skip-failed", action="store_true")
    ap.add_argument("--ollama-url", default=None, help="the verifier's server; the five other configs name "
                    f"{NO_SERVER_URL}, where nothing listens")
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--sink-root", type=Path, default=None)
    ap.add_argument("--key", type=Path, default=plant_key.KEY)
    ap.add_argument("--key-sha256", default=None, help="the key's pin (default: plant_key.KEY_SHA256 for the "
                    "plant key; another key needs its own)")
    ap.add_argument("--min-free-gb", type=float, default=i2_memory.FLOOR_GB)
    ap.add_argument("--sample-s", type=float, default=5.0)
    ap.add_argument("--record-file", type=Path, default=RECORD_FILE)
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args(argv)


def key_of_args(a) -> plant_key.Key:
    pin = a.key_sha256
    if pin is None:
        if Path(a.key).resolve() != plant_key.KEY.resolve():
            raise SystemExit("--key names another key: give its --key-sha256 (the run pins the key it reads)")
        pin = plant_key.KEY_SHA256
    try:
        return plant_key.load(a.key, pin)
    except plant_key.KeyProblem as e:
        raise SystemExit(f"REFUSED: {e}") from None


def main(argv=None, load=load_exp01) -> int:
    a = parse_args(argv)
    key = key_of_args(a)
    draws = (1,) if a.smoke else tuple(sorted(set(a.draws)))
    max_q = 1 if a.smoke else None
    root = a.sink_root or (SMOKE_SINKS if a.smoke else SINKS)
    if a.dry_run:
        mod = load()
        install(mod, key, a.min_free_gb)
        mod.dry_run(a.configs, max_q, a.index, draws, sink_root=root, skip_failed=a.skip_failed)
        return 0
    if not a.ollama_url:
        raise SystemExit("--ollama-url is required for a run (exp_01's run contexts name a server)")
    if "verified_pass" not in a.configs and a.ollama_url.rstrip("/") != NO_SERVER_URL:
        raise SystemExit(f"--ollama-url {a.ollama_url}: the configs {a.configs} make no Ollama call and name "
                         f"{NO_SERVER_URL}, where nothing listens (module docstring, K1's GUARD)")
    lock_fh = hold_lock()
    low, free0 = i2_memory.under(a.min_free_gb)
    line = {"job": "i2_generate", "start": time.strftime("%Y-%m-%dT%H:%M:%S"), "host": os.uname().nodename,
            "pid": os.getpid(), "smoke": a.smoke, "configs": a.configs, "draws": list(draws), "index": a.index,
            "sink_root": str(root), "key": key.describe(), "ollama_url": a.ollama_url, "resume": a.resume,
            "skip_failed": a.skip_failed, "floor_gb": a.min_free_gb,
            "free_gb_at_start": None if free0 is None else round(free0, 3)}
    if low:
        line.update(end=line["start"], exit=EXIT_MEMORY, memory_ok=False,
                    stopped=f"free memory {free0} GB under the floor of {a.min_free_gb} GB at the start")
        write_record(a.record_file, line)
        print(f"REFUSED: {line['stopped']}; nothing started", flush=True)
        return EXIT_MEMORY
    mod = load()
    seen = install(mod, key, a.min_free_gb)
    sampler = i2_memory.Sampler(a.sample_s).start()
    code, err = 0, None
    try:
        asyncio.run(mod.run_experiment(configs=a.configs, base_url=a.ollama_url, max_questions=max_q,
                                       resume=a.resume, index_name=a.index, draws=draws, sink_root=root,
                                       skip_failed=a.skip_failed))
    except MemoryFloor as e:
        code, err = EXIT_MEMORY, str(e)
    except SystemExit as e:
        code, err = (e.code if isinstance(e.code, int) else 1), (None if isinstance(e.code, int) else str(e.code))
    except BaseException as e:   # recorded, then raised again
        line.update(end=time.strftime("%Y-%m-%dT%H:%M:%S"), exit="exception", error=f"{type(e).__name__}: {e}",
                    memory=sampler.stop(), memory_checks=seen["checks"])
        write_record(a.record_file, line)
        raise
    mem = sampler.stop()
    line.update(end=time.strftime("%Y-%m-%dT%H:%M:%S"), exit=code, error=err, memory=mem,
                memory_checks=seen["checks"], stopped=seen["stopped"],
                memory_ok=mem["min_free_gb"] is not None and mem["min_free_gb"] >= a.min_free_gb
                and mem["unknown_samples"] == 0 and seen["stopped"] is None)
    write_record(a.record_file, line)
    print(f"I2 generation ended: exit {code}; lowest free memory {mem['min_free_gb']} GB (floor {a.min_free_gb}); "
          f"memory_ok {line['memory_ok']}" + (f"; {err}" if err else ""), flush=True)
    lock_fh.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
