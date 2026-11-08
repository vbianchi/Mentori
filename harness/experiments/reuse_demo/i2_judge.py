#!/usr/bin/env python3
"""The lock's judge on the I2 answers, against a curated key in place of v2.4, through the paper's own judge code (I2,
D160 (14) Q-I2d O-a; i2_plan.md A4).

    uv run python experiments/reuse_demo/i2_judge.py selftest --run findings/recompute/I2_runs/sinks/exp_01__single_pass__i2_plant5
    uv run python experiments/reuse_demo/i2_judge.py status --check-dir <judge check dir>      # offline: does it cover?
    uv run python experiments/reuse_demo/i2_judge.py run --run <sink> --base http://127.0.0.1:11434 \
        --log /opt/homebrew/var/log/ollama.log --binary /opt/homebrew/opt/ollama/bin/ollama --machine macos \
        --check-dir <judge check dir> --out findings/recompute/I2_runs/judge          # sends --variants a (D161 (7))

WHAT IT RUNS. experiments/scorers/judge_passages.py, unchanged: its run (the reproduction check it requires, the fresh
load and server checks, the archived prompt and parser, the retry rule, the recheck after another fresh load, the
writer lock, the rows, headers and summary), its selftest and its prompts. Editing judge_passages.py would change the
code fingerprint every S3 row carries (its code_identity), so it is not edited; this wrapper changes, inside its own
process only, where the key comes from:
  - judge_passages.run_answers is replaced by key_run_answers below: the same reading of a run (records.read_run,
    the answer's passages resolved through the index the run recorded) and the same item fields and item_sha256,
    with the expected answer, concepts, prompt rule and key_hash taken from the curated key by S373's own functions
    (key_of: the short answer plus the synthesis statement where there is one, and the concept phrases;
    judged_answerable: the answerable prompt unless the key marks the question not answerable and it is not a
    refutation, Q51; key_hash). For the plant key: PB_001 to PB_003 and PB_004 (a refutation) get the answerable
    prompt, PB_005 the decline prompt.
  - records.key_questions (Rule 8's groups, the question text when a record lacks it) returns the curated key's
    questions; records.group_of then places each by its answer type as for v2.4 (refutation: false_premise).
  - S373.KEY names the curated key, so the header judge_passages writes lists it among its inputs.
  - judge_passages.STORED is emptied: its stored devstral scores are of the paper's answers, so no I2 prompt has one
    (every row's a_equals_stored is null, as for a second judge).
The check that `run` requires is judge_passages.py's own `check` (the 107 calibration answers of S440 on this machine,
server, Ollama version, model digest, lock and code); it is run with judge_passages.py itself, never through this
wrapper, and this wrapper's code is not part of it. Each start appends one line to <out>/i2_judge_header.jsonl: this
file's and plant_key.py's sha256, the key's path and sha256, the run.

K1 (D160 (14), Q-I2e). judge_passages' run begins with a fresh load, which unloads every model of the server, K1's
too. `run` refuses while a K1 launcher runs on this machine (K1_PATTERN, the pattern t2_lib.sh uses for the laptop),
before anything is read or loaded. selftest and status make no server contact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from experiments.reuse_demo import plant_key  # noqa: E402

K1_PATTERN = r"[r]un_k1_laptop\.sh|[k]1_autorestart"     # findings/recompute/T2_runs/t2_lib.sh, laptop K1_RUNNING
K1_PATTERN_VAR = "I2_K1_PATTERN"                         # tests name a pattern of their own; never set it for a run
HEADER = "i2_judge_header.jsonl"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def k1_running(pattern: str | None = None) -> bool:
    pattern = pattern or os.environ.get(K1_PATTERN_VAR) or K1_PATTERN
    return subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode == 0


def install(key: plant_key.Key):
    """Points judge_passages, records and S373 at the curated key inside this process (module docstring). Returns
    judge_passages."""
    from experiments.scorers import judge_passages as JP
    from experiments.scorers import records as R
    S373 = JP.S373
    kq, v2, v1 = key.key_questions(), key.v2(), key.v1()
    R.key_questions = lambda: kq

    def key_run_answers(run: Path, rows_sel: str | None, store: Path | None) -> list[dict]:
        """judge_passages.run_answers with the curated key (the same fields, item_sha256 and refusals)."""
        try:
            recs = R.read_run(run, store=store)
        except R.RecordsError as e:
            raise SystemExit(f"REFUSED: {e}") from None
        if rows_sel:
            s, e = (int(x) if x else None for x in rows_sel.split(":"))
            recs = recs[s:e]
        out = []
        for r in recs:
            qid = r["question_id"]
            if qid not in v2:
                raise SystemExit(f"REFUSED: {qid} is not in the key {key.path.name}")
            answerable = S373.judged_answerable(qid, v1, v2)
            if answerable != (r["group"] != "not_answerable"):
                raise SystemExit(f"REFUSED: {qid}: the judge's prompt rule says answerable {answerable}, Rule 8's "
                                 f"group is {r['group']}")
            ea, ec = S373.key_of(qid, v2)
            x = {"key": f"{r['run_id']}|{r['answer_key']}", "config": r["config"], "question_id": qid,
                 "draw": r["draw"], "question": r["question"], "expected": ea, "concepts": ec,
                 "answerable": answerable, "key_hash": S373.key_hash(qid, v2),
                 "answer": r["answer"] if r["status"] == "ok" else "", "gen_error": r["error"],
                 "contexts": r["passages"] or [], "contexts_capture": r["passages_kind"], "run_id": r["run_id"],
                 "answer_key": r["answer_key"], "passages_kind": r["passages_kind"]}
            x["item_sha256"] = JP.sha(json.dumps([x[k] for k in ("question", "expected", "concepts", "answer",
                                                                  "gen_error", "answerable", "key_hash")]
                                                 + [[c.get("source"), c.get("chunk_idx"), c["text"]]
                                                    for c in x["contexts"]], ensure_ascii=False))
            out.append(x)
        return out

    JP.run_answers = key_run_answers
    JP.STORED = []
    S373.KEY = key.path
    return JP


def header_line(key: plant_key.Key, argv: list[str]) -> dict:
    return {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "script": "experiments/reuse_demo/i2_judge.py",
            "i2_judge_py_sha256": sha(Path(__file__).read_bytes()),
            "plant_key_py_sha256": sha((HERE / "plant_key.py").read_bytes()), "key": key.describe(), "argv": argv}


def status(check_dir: Path) -> int:
    """Offline: whether the judge check in check_dir can cover a run with today's code (its code identity and lock);
    the server, digest and machine are compared by `run` itself (require_check)."""
    from experiments.runner.lock import load
    from experiments.scorers import judge_passages as JP
    f = Path(check_dir) / "repro_check.json"
    if not f.exists():
        print(f"NO CHECK in {check_dir}: run judge_passages.py check on the server first (README.md:75-79)")
        return 1
    c = json.loads(f.read_text())
    now = JP.code_identity()
    code_diff = sorted(k for k in set(now) | set(c.get("code") or {}) if (c.get("code") or {}).get(k) != now.get(k))
    lock_ok = c.get("lock_sha256") == load().sha256
    ok = c.get("passed") is True and c.get("full_sample") is True and not code_diff and lock_ok
    print(f"check {f}: passed {c.get('passed')}, full sample {c.get('full_sample')}, host "
          f"{(c.get('machine_identity') or {}).get('hostname')}, server {c.get('server')}, model {c.get('model')}; "
          f"code differs in {code_diff or 'nothing'}; lock {'same' if lock_ok else 'differs'}: "
          + ("COVERS (code and lock)" if ok else "DOES NOT COVER a run now"))
    return 0 if ok else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("cmd", choices=["selftest", "status", "run", "block"])
    pre.add_argument("--key", type=Path, default=plant_key.KEY)
    pre.add_argument("--key-sha256", default=None)
    pre.add_argument("--check-dir", type=Path)
    a, rest = pre.parse_known_args(argv)
    if a.cmd == "status":
        if a.check_dir is None:
            raise SystemExit("status needs --check-dir")
        return status(a.check_dir)
    pin = a.key_sha256
    if pin is None:
        if Path(a.key).resolve() != plant_key.KEY.resolve():
            raise SystemExit("--key names another key: give its --key-sha256")
        pin = plant_key.KEY_SHA256
    try:
        key = plant_key.load(a.key, pin)
    except plant_key.KeyProblem as e:
        raise SystemExit(f"REFUSED: {e}") from None
    if a.cmd == "run" and k1_running():
        raise SystemExit("REFUSED: a K1 launcher runs on this machine; the judge's fresh load would unload its model "
                         "(module docstring, K1); nothing read or loaded")
    JP = install(key)
    jp_argv = [a.cmd] + (["--check-dir", str(a.check_dir)] if a.check_dir is not None else []) + rest
    if a.cmd == "run":
        # argparse also takes "--judge=second" and an unambiguous prefix ("--jud second"): refuse every form
        if any(x.split("=", 1)[0] in ("--judge", "--judg", "--jud", "--ju", "--j") for x in jp_argv):
            raise SystemExit("REFUSED: I2 is judged by the main judge only (D160 (14) Q-I2d: the judge); no --judge")
        # D161 (7) N7 O-a: the plain call (a) only; judge_passages' own default is ab, so a is sent unless given
        # ("--v" to "--variants" are the prefixes argparse takes: no other run option starts with --v)
        given = []
        for i, x in enumerate(jp_argv):
            name, eq, val = x.partition("=")
            if len(name) >= 3 and "--variants".startswith(name):
                given.append(val if eq else (jp_argv[i + 1] if i + 1 < len(jp_argv) else ""))
        if any(v != "a" for v in given):
            raise SystemExit("REFUSED: I2 is judged with the plain call only (D161 (7) N7 O-a): --variants a, not "
                             + ", ".join(repr(v) for v in given if v != "a"))
        if not given:
            jp_argv += ["--variants", "a"]
        out = None
        for i, x in enumerate(jp_argv):
            if x == "--out" and i + 1 < len(jp_argv):
                out = Path(jp_argv[i + 1])
        if out is None or "--run" not in jp_argv:
            raise SystemExit("run needs --run <sink> and --out <dir>")
        out.mkdir(parents=True, exist_ok=True)
        with (out / HEADER).open("a") as fh:
            fh.write(json.dumps(header_line(key, argv), ensure_ascii=False) + "\n")
    elif "--arm" in jp_argv:
        raise SystemExit("REFUSED: I2 reads runs (--run), not harness arm files")
    sys.argv = ["experiments/scorers/judge_passages.py"] + jp_argv
    return JP.main()


if __name__ == "__main__":
    sys.exit(main())
