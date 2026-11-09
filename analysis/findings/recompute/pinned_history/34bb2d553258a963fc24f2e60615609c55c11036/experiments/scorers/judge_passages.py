#!/usr/bin/env python3
"""B7 (D35): the lock's judge on answers that store their passages, twice per answer: (a) as today, (b) with the passages.

D35 (O32): "Figure 5 compares the signals against the key and against the papers; the judge's faithfulness is
re-scored with the passages in its prompt." The judge today never sees a passage, so its Faithfulness ("Are all
claims grounded in source material") has no source material to read. This script runs, per answer:

  (a) today's judge, unchanged: the archived prompt (scripts/S141_runner/judge.py build_prompt, which reads the
      template out of recovered_harness/tests/experiments_v4/exp_common.py under a sha256 pin; the copy in
      experiments/mentori is byte-identical), the whole answer, key v2.4 and the Q51 prompt rule
      (scripts/S373_rejudge_v2.py key_of, judged_answerable, key_hash), the parser that never invents a score
      (S141_runner.judge parse_scores).
  (b) the same prompt with one block added: the answer's stored passages, each sent whole as stored (LOCK.toml
      [text] judge_input = "whole"; what was stored can itself be a slice, the row's contexts_capture says so, and
      the text the judge reads makes no claim either way), between "## Expected Concepts" and "## Generated Answer"
      (BLOCK_* below). Removing the block from (b) gives (a) byte for byte; every answer is checked for that before
      its calls. The rubric is not changed. An answer whose passage contains the block's own marker gets (b)
      refused_marker (its (a) still runs).

Every call goes through experiments/runner/ollama_client.generate with lock.ollama(<[judge] model>, role="judge"):
the script sets no setting of its own. Each call writes the D37 record (ollama_client's record plus the answer,
variant, attempt, prompt sha256 and the parsed scores) to <out>/judge_passages_calls.jsonl.

STATUS of one variant: ok (the call stopped on its own and a score parsed); unparseable (no score in the reply);
length, stalled, error, cancelled (ollama_client's call status; never scored: a reply that reaches [judge]
num_predict is a runaway loop, LOCK.toml [judge]); not_applicable ((b) on the decline prompt, which has no
faithfulness dimension: open question); no_passages ((b) on an answer that stores none); deferred ((b) not asked
yet, --variants a: PHASES below). As today
(S141_runner.judge.Judge.score) a failed or unparseable call is tried once more; an HTTP 4xx (such as a prompt
longer than the context, truncate false) is not, since it would fail the same way.

REPRODUCE BEFORE WRITING (README.md:75-79), at two levels.
  check  runs path (a) on the 107 calibration answers of S440 (S376.answers_and_key, the same prompts) and compares
         every score with the stored lock pass of S440 (findings/recompute/S440_judge_lock_check.jsonl, the Studio;
         the laptop's and the Studio's agree 107 of 107). It passes only if all 107 have every score equal and every
         call is ok. `run` refuses to start unless a passed check exists in --check-dir for the same machine
         (hostname, --machine, the binary's sha256), server, Ollama version, model digest, lock sha256, options and
         system prompt sent, and the same code (code_identity: this file, S141_runner/judge.py, S373_rejudge_v2.py,
         S376_judge_calibration.py, the archived template).
  run    per answer: when S373 stored a devstral score for the identical (a) prompt under the current key
         (STORED: findings/recompute/S373_devstral_reanalysis.jsonl, at settings S440 found equal to the lock's),
         (a) must equal it, or (b) is withheld for that answer (status withheld_a_differs, tried again on resume) and
         the run exits 1. a_equals_stored is on every row (null: no stored score for that prompt).

    uv run python experiments/scorers/judge_passages.py selftest --arm <results.json>
    uv run python experiments/scorers/judge_passages.py check --base http://127.0.0.1:11434 --log <server log> \
        --binary <ollama> --machine macos --out <check dir> [--n N] [--judge main|second]
                                                                              (N < 107: a smoke test, unlocks nothing)
    uv run python experiments/scorers/judge_passages.py run --base http://127.0.0.1:11434 --log <server log> \
        --binary <ollama> --machine macos --check-dir <check dir> --arm <results.json> --out <dir> \
        [--limit N] [--rows START:END] [--no-recheck] [--variants a|ab] [--draws 1|2,3] [--keys <file>] \
        [--answered-only] [--judge main|second]
    uv run python experiments/scorers/judge_passages.py block --arm <results.json> --row I   (prints (b)'s added text)
    (run, selftest and block take --run <run sink or results file> [--store <chroma dir>] in place of --arm)

Both check and run start with experiments/runner/job.py fresh-load (F1), which unloads every model the server holds
(another client's too), and refuse to start unless every server check passed: a pending check (KV-cache line not
yet in the log) refuses as a failure does. On a shared server a failed or pending "loaded"/"kv_cache" check is
tried again after a new fresh load, at most FRESH_LOAD_TRIES loads in all. After the first judge call of each fresh
load the server is checked again (job.py after_first_call, D80 V6: one runner only since the load, every check
passed), written into that load's fresh_load_*.json, and a failure refuses the job (setup error). No model-scored row
precedes that check; a no_answer row, which makes no judge call, can be written before it.
The arm format is the harness's results.json (per_question_results with question_id, config, question, generation
{answer, error} and contexts [{source, chunk_idx, text}]), as experiments/scorers/ragchecker_run.py reads it.
--run <run> in place of --arm (run, selftest, block; audit of 16 October F5): the answers of one run as
experiments/scorers/records.py reads them (a sink or results file of exp_01, exp_02, exp_03, exp_06 or the authors'
RLM), the passages being what the generator saw, resolved from ids to text through the index the run recorded
(--store: the Chroma directory, default the one recorded). The prompts, rubric, parser and statuses are the --arm
path's; the prompt rule (S373.judged_answerable) must agree with Rule 8's group from the D5 key, or the run is
refused. Such a row also carries run_id, answer_key and passages_kind, and is identified by (run_id, config,
question_id, draw), so one --out can hold several runs. An answer whose record lists no passages gets (b) no_passages.
code_identity covers records.py and experiments/runner/index_identity.py.

Output, one line per answer: <out>/judge_passages.jsonl with both score sets (a and b), their status, tokens and
stop reasons. A row is identified by (config, question_id, draw, item_sha256), item_sha256 being the sha256 of
everything that enters its prompts (question, key, answer, prompt rule, passages); every row also carries run_sha256
(lock, code, system prompt). On resume a row counts as done only when its item_sha256 and run_sha256 are this
run's and both variants ended in a final status (FINAL); `run` refuses an --out holding a row of the same (config,
question_id, draw) with another item_sha256 or run_sha256 (another arm, answer, key, lock or block wording), so
one file never mixes two definitions. Each start appends its settings to <out>/judge_passages_headers.jsonl.
Unless --no-recheck, a run that judged answers ends as F1 asks (experiments/runner/job.py:11-12): another fresh
load, the first RECHECK_N answers that reached the model judged again, both variants compared with what it wrote
(<out>/judge_passages_recheck.jsonl, summary in judge_passages_recheck_summary.json); any difference exits 1.
With --variants a the recheck makes only the (a) call and compares (a) only (D112 Q13, audit A21-23): an answer
whose row a phase 3 already completed holds (b) ok, which a plain-call recheck cannot repeat; its lines carry
"compared": "a".
<out>/judge_passages_summary.json counts the statuses, the stored-score comparison and the (b) replies whose
faithfulness did not parse.

PHASES (D94, Valerio 18 October: Figure 2's ranking needs only (a), so it comes first). `run --variants a` makes only
the (a) call. Where a full run would make a (b) call, the row stores (b) as {"status": "deferred"} (not FINAL, so a
full run does it later); where a full run makes no (b) call (no_answer, not_applicable, no_passages, refused_marker,
withheld_a_differs) the row stores what a full run stores. Such a row's (a) is final and is read as any row's (a).
A later `run` (--variants ab, the default) on the same --out, for an answer whose latest row has (a) ok and (b)
deferred under the same item_sha256 and run_sha256, makes only the (b) call: the new row carries that (a), its stored
score comparison and "a_reused": {"at", "wall_s"} of the row it came from, and is otherwise the row a full run writes.
A row's (a) never mixes two definitions: the reuse needs the same item_sha256 and run_sha256, which --variants does not
enter. A --variants a run counts a row done when its (a) is final, whatever its (b) holds (a (b) that failed in a
phase 3 is tried again only by a run with (b), as a full run's resume would, (a) included), except (b)
withheld_a_differs (is_done). The latest row of an answer is its row (read_rows order), so a reader that takes the latest row per ident
reads the full rows once phase 3 has ended, and before that the phase-1 and phase-2 rows, whose (b) says "deferred".
  --draws 1 or 2,3       only the answers of those draws (the phases' order: draw 1 first)
  --keys <file>          only the answer keys listed (one per line; --run only; D93 Q-c's separate pass of G1's 15
                         reruns); a listed key the run does not hold is refused
  --answered-only        leaves out the answers with no answer text or a generation error (no judge call either way):
                         for a snapshot of a run still writing, whose failed answers may yet be retried; the final pass,
                         after the run has ended, is made without it so those rows are written
One writer per --out: `run` holds an exclusive lock on <out>/.writer.lock (fcntl.flock, released when the process
ends however it ends) and exits WRITER_BUSY (75) without a call when another process holds it. A `run` with nothing
to judge makes no fresh load (nothing unloaded) and writes its summary.

JUDGE (D85; D112 Q5). --judge main, the default, is LOCK.toml [judge] model (devstral-small-2:24b), everything as
above. --judge second is [judge] second_model (qwen3.8:27b): the same [judge] settings (lock.ollama role "judge";
no system prompt, as [date] names none for it), its digest from [models], which the client checks against the
server's. Its check cannot compare with S440, whose stored scores are devstral's, so it is D85's repeat check: the
107 calibration answers judged twice, each pass after its own fresh load; it passes only if every answer gives the
same scores in both passes, every call is ok, and every call record sent temperature 0 and think false (D112 Q18
(3)). Its run compares no (a) with STORED (devstral's judgments): a_equals_stored is null on every row. Its run
identity names the model, so its rows never resume or join devstral's, and check and run refuse a folder whose
repro_check.json or judge_passages_headers.jsonl names the other judge: the two judges' check dirs and outs never mix.
Each of its rows, and its summary, also carries "judge": {"which": "second", "model", "digest": the lock's [models]
digest the server was checked against}, so a row with no judge call (no_answer) names its judge too; the main judge's
rows and summary are written as before (no "judge" key).
Every fresh load (check, run, recheck; either judge) is preceded by the client's own call check
(experiments/runner/ollama_client._checked: the lock's Ollama version, and the server's digest for the tag against
[models] by lock.check_digest, D91), so a server holding another build under the tag (the Studio's qwen3.8:27b is the
MLX build 47951e4a6661, which D47 keeps out of every run) is refused before anything is unloaded or loaded.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from experiments.runner import machine_load  # noqa: E402
from experiments.runner.job import SetupError, after_first_call, fresh_load  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402
from experiments.runner.ollama_client import generate  # noqa: E402
import S141_runner.judge as J  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402
from experiments.scorers import records as R  # noqa: E402  (--run: F5, F39)

S440_LEDGER = ROOT / "findings/recompute/S440_judge_lock_check.jsonl"   # the Studio's lock pass: the stored scores
# devstral's stored judgments of answers that carry passages, with the S373 source that rebuilds their prompts
STORED = [(ROOT / "findings/recompute/S373_devstral_reanalysis.jsonl", "reanalysis")]
CHECK_N = 107
RECHECK_N = 10
FRESH_LOAD_TRIES = 3
_AFTER_FIRST: dict = {}   # D80 V6: set by start(), emptied by the first judge call after it
ANCHOR = "## Generated Answer\n"                                        # where (b)'s block goes, in the answerable prompt
FINAL = {"ok", "not_applicable", "no_passages", "no_answer", "refused_marker"}
DEFERRED = "deferred"                                                  # (b) not asked yet (--variants a, PHASES)
WRITER_BUSY = 75                                                       # exit: another process writes this --out
_WRITER: list = []                                                     # the open lock file, held until exit
JUDGES = {"main": "model", "second": "second_model"}                   # --judge -> its LOCK.toml [judge] key (D85)

# (b)'s added text. The block is BLOCK_HEAD, then one BEGIN/text/END group per passage separated by a blank line,
# then a blank line, so the next line is ANCHOR as in (a).
BLOCK_HEAD = ("## Source Material\n"
              "The passages retrieved for this question, as stored with the answer, each between its BEGIN and "
              "END lines.\n\n")
BEGIN = "<<<BEGIN PASSAGE {i} | source: {source}{chunk}>>>\n"
END = "\n<<<END PASSAGE {i}>>>"


class MarkerInPassage(ValueError):
    """A stored passage holds the block's own marker: that answer's (b) is refused, the rest of the run goes on."""


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8", "surrogatepass") if isinstance(b, str) else b).hexdigest()


def code_identity() -> dict:
    """The code that builds and scores a judge call; the run refuses a check made with other code. The system prompt
    and options sent are compared apart (require_check), since the lock's sha256 covers the system prompt's path only."""
    return {"judge_passages_py": sha(Path(__file__).read_bytes()),
            "s141_judge_py": sha((ROOT / "scripts/S141_runner/judge.py").read_bytes()),
            "s373_rejudge_v2_py": sha((ROOT / "scripts/S373_rejudge_v2.py").read_bytes()),
            "s376_judge_calibration_py": sha((ROOT / "scripts/S376_judge_calibration.py").read_bytes()),
            "template_file": J.V4_COMMON_SHA256,
            # --run reads its answers and passages through these two (F5)
            "records_py": sha((ROOT / "experiments/scorers/records.py").read_bytes()),
            "index_identity_py": sha((ROOT / "experiments/runner/index_identity.py").read_bytes())}


def block(contexts: list[dict]) -> str:
    parts = []
    for i, c in enumerate(contexts, 1):
        text = c["text"]
        if "<<<BEGIN PASSAGE" in text or "<<<END PASSAGE" in text:
            raise MarkerInPassage(f"passage {i} contains the block's own marker; (b) refused for this answer")
        chunk = "" if c.get("chunk_idx") is None else f" | chunk {c['chunk_idx']}"
        parts.append(BEGIN.format(i=i, source=c.get("source"), chunk=chunk) + text + END.format(i=i))
    return BLOCK_HEAD + "\n\n".join(parts) + "\n\n"


def prompts(question: str, expected: str, concepts: list, answer: str, answerable: bool,
            contexts: list[dict] | None) -> tuple[str, str | None, str | None]:
    """(a) exactly as today; (b) the same with the block inserted before ANCHOR, or None. Asserts that removing the
    block from (b) gives (a) byte for byte, and that ANCHOR found in (a) is the template's, not text from the key."""
    a = J.build_prompt(question, expected, concepts, answer, answerable, truncate_chars=None)
    if not answerable or not contexts:
        return a, None, None
    tmpl = J._template("ANSWERABLE_JUDGE_PROMPT")
    head = tmpl[:tmpl.index(ANCHOR)]
    text = ", ".join(concepts) if concepts else "N/A"
    head = head.replace("{question}", question).replace("{expected_answer}", expected).replace("{expected_concepts}", text)
    k = len(head)
    if a[:k] != head or a[k:k + len(ANCHOR)] != ANCHOR:
        raise ValueError("the anchor in (a) is not where the template puts it")
    blk = block(contexts)
    b = a[:k] + blk + a[k:]
    if b[:k] + b[k + len(blk):] != a or b.count(BLOCK_HEAD) != 1:
        raise ValueError("(b) minus its block is not (a)")
    return a, b, blk


def busy_runners() -> int | None:
    """Model runners on this machine that used CPU in the 1 s just before the call (CPU time grew by at least 0.1 s):
    experiments/runner/machine_load.busy_here, where this count now lives (D83 Q146). Measured as a difference, not
    with ps %cpu: macOS reports %cpu as a decaying average over up to a minute (man ps), so the runner of the call that
    just ended still showed as busy (113 of 113 calls on 16 October recorded 1). One call at a time, so the server we
    call is idle in the window and this counts the others' work. Where ps shows no ollama serve the count is taken
    from Windows' process list (the Beelink, whose server WSL's ps cannot see, where ps alone gave 0 whatever ran), or
    is None when neither can be read. Since D89 A1 no judge call uses it: the client records the latest reading of its
    sampler (experiments/runner/machine_load.py); verifier_ports keeps it for a client without that build."""
    return machine_load.busy_here()[0]


def judge_call(base: str, call, prompt: str, answerable: bool, passages: list | None, log: Path, extra: dict) -> dict:
    """One judged variant, as S141_runner.judge.Judge.score: tried once more on a failed or unparseable call."""
    dims = J.ANSWERABLE_DIMS if answerable else J.UNANSWERABLE_DIMS
    for attempt in (1, 2):
        rec = generate(base, call, prompt, passages=passages)      # Q146: the client's sampler (D89 A1)
        scores, mode = J.parse_scores(rec["text"], answerable) if rec["status"] == "ok" else ({}, "none")
        parsed = any(scores.get(d) is not None for d in dims)
        status = rec["status"] if rec["status"] != "ok" else ("ok" if parsed else "unparseable")
        rec.update(extra, attempt=attempt, prompt_sha256=sha(prompt), prompt_chars=len(prompt), judge_status=status,
                   parse_mode=mode, scores={d: scores.get(d) for d in dims} if parsed else None,
                   justification=scores.get("justification") if parsed else None)
        with log.open("a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if _AFTER_FIRST:                                  # D80 V6: the runner that answered is the one checked
            certify_first_call(rec)
        retry = status == "unparseable" or (status in ("error", "stalled") and not str(rec["error"]).startswith("HTTP 4"))
        if not retry:
            break
    return {"status": status, "scores": rec["scores"], "justification": rec["justification"], "text": rec["text"],
            "attempts": attempt, "prompt_tokens": rec["prompt_tokens"], "output_tokens": rec["output_tokens"],
            "stop_reason": rec["stop_reason"], "error": rec["error"], "prompt_sha256": rec["prompt_sha256"],
            "prompt_chars": rec["prompt_chars"], "wall_s": rec["wall_s"], "load_s": rec["load_s"],
            "model_digest": rec["model_digest"],
            "server": rec["server"], "ollama_version": rec["ollama_version"]}


def certify_first_call(rec: dict) -> None:
    """D80 V6 (audit F2): check_server again after the first judge call of a fresh load, into that load's record
    file; a failure refuses the job (setup error). That call's own line in the calls log is written first. No
    model-scored row precedes the check: a row with a judge call is written only after its answer's calls return,
    so after this one. A no_answer row (no answer text, or a generation error) makes no judge call and can be
    written before it."""
    s = dict(_AFTER_FIRST)
    _AFTER_FIRST.clear()
    try:
        after_first_call(s["fl"], s["a"].log, s["a"].binary, s["a"].machine, first=rec)
    except SetupError as e:
        raise SystemExit(f"REFUSED (setup error): {e}") from None
    finally:
        s["path"].write_text(json.dumps(s["fl"], indent=1) + "\n")


def judge_of(lock, which: str = "main") -> str:
    """--judge (D85; D112 Q5): "main", the default, is [judge] model; "second" is [judge] second_model. Either is sent
    at the [judge] settings by lock.ollama(role="judge"), with its own digest from [models]."""
    if which not in JUDGES:
        raise SystemExit(f"REFUSED: --judge {which!r} is not one of {', '.join(JUDGES)}")
    model = lock.d["judge"].get(JUDGES[which])
    if not model or model not in lock.judges():
        raise SystemExit(f"REFUSED: LOCK.toml [judge] names no {JUDGES[which]} (--judge {which})")
    return model


def judge_arg(a) -> str:
    """The --judge of a namespace; "main" for a caller that has none (judge_evidence.py passes its own)."""
    return getattr(a, "judge", None) or "main"


def refuse_other_judge(out: Path, model: str) -> None:
    """One judge per folder (D112 Q5): a check dir whose repro_check.json, or an --out whose headers, name another
    judge model is refused before anything is loaded or written there."""
    names = set()
    f = out / "repro_check.json"
    if f.exists():
        names.add(json.loads(f.read_text()).get("model"))
    names |= {h.get("model") for h in read_rows(out / "judge_passages_headers.jsonl")}
    other = sorted(n for n in names if n is not None and n != model)
    if other:
        raise SystemExit(f"REFUSED: {out} holds the judge {', '.join(other)}'s check or rows, not {model}'s; "
                         f"each judge has its own check dir and out")


def refuse_other_build(base: str, call) -> None:
    """D47, D91: before the fresh load, which unloads every model the server holds and loads this one, the server must
    run the lock's Ollama version and hold the judge's tag under the lock's [models] digest. The test is the one every
    call already passes (experiments/runner/ollama_client._checked: lock.check_digest on the server's /api/tags
    digest), made here before the load: the Studio's qwen3.8:27b is the MLX build 47951e4a6661 (README.md D85), so
    --judge second there is refused with nothing unloaded or loaded."""
    from experiments.runner import ollama_client as OC
    try:
        OC._checked(base, call.model, call)
    except LockError as e:
        raise SystemExit(f"REFUSED (D47, D91): {e}; nothing unloaded or loaded") from None


def judge_tag(which: str, model: str, call) -> dict | None:
    """The "judge" a second judge's rows and summary carry (None for the main judge, whose rows are as before)."""
    return None if which == "main" else {"which": which, "model": model, "digest": call.digest}


def start(a, out: Path, what: str) -> tuple:
    lock = load()
    model = judge_of(lock, judge_arg(a))
    call = lock.ollama(model, role="judge")
    refuse_other_build(a.base.rstrip("/"), call)
    out.mkdir(parents=True, exist_ok=True)
    # A server another client also calls (laptop, 16 October) can load its own model between this load and the
    # check, which then fails on "loaded" or reads that model's KV-cache lines. Only those two checks are retried
    # (FRESH_LOAD_TRIES loads in all, 30 s apart); a version, binary or settings failure refuses at once. Each
    # fresh load unloads every model the server holds, the other client's included (job.py:39-41), so the retries
    # are few. A pending check (ok null: the KV-cache line not yet in the log) counts as not passed. Every attempt
    # is written; the job starts only on a load whose every check passed, the binary check included.
    for attempt in range(1, FRESH_LOAD_TRIES + 1):
        fl = fresh_load(a.base.rstrip("/"), model, a.log, a.binary, a.machine)
        fl["attempt"] = attempt
        fl_path = out / f"fresh_load_{time.strftime('%Y%m%dT%H%M%S')}.json"
        fl_path.write_text(json.dumps(fl, indent=1) + "\n")
        checks = fl["server_check"]["checks"]
        failed = {k for k, v in checks.items() if v["ok"] is not True}
        passed = not failed and checks.get("binary", {}).get("ok") is True
        if passed or not failed <= {"loaded", "kv_cache"} or attempt == FRESH_LOAD_TRIES:
            break
        print(f"{what}: fresh load {attempt} not passed on {sorted(failed)} (another client's model?); again in 30 s",
              flush=True)
        time.sleep(30)
    if not passed:
        raise SystemExit(f"REFUSED: the server check did not pass after the fresh load (failed or pending, or no binary "
                         f"check): {json.dumps(fl['server_check'])}")
    fl["machine_identity"] = {"hostname": socket.gethostname(), "machine": a.machine,
                              "binary_sha256": checks["binary"]["sha256"]}
    print(f"{what}: fresh load of {call.model} in {fl['load_s']} s, unloaded {fl['unloaded']}; server checks "
          + ", ".join(f"{k} ok" for k in checks), flush=True)
    _AFTER_FIRST.update(fl=fl, a=a, path=fl_path)
    return lock, model, call, fl


# ---------------------------------------------------------------- check

def cmd_check(a) -> int:
    import S376_judge_calibration as S376
    out = a.out
    which = judge_arg(a)
    refuse_other_judge(out, judge_of(load(), which))
    if which != "main":
        return cmd_check_repeat(a)
    lock, model, call, fl = start(a, out, "check")
    items = S376.answers_and_key()
    if len(items) != CHECK_N:
        raise SystemExit(f"REFUSED: expected the {CHECK_N} calibration answers, got {len(items)}")
    items = items[: a.n] if a.n else items
    ref = {r["answer_key"]: r for r in map(json.loads, filter(str.strip, S440_LEDGER.read_text().splitlines()))
           if r["pass"] == "lock"}
    log = out / "check_calls.jsonl"
    rows, base = [], a.base.rstrip("/")
    for i, x in enumerate(items, 1):
        r = ref.get(x["answer_key"])
        if r is None or r["key_hash"] != x["key_hash"]:
            raise SystemExit(f"REFUSED: {x['answer_key']} has no S440 lock-pass row under the same key")
        p = J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)
        res = judge_call(base, call, p, x["answerable"], None, log, {"answer": x["answer_key"], "variant": "a_check"})
        same = res["status"] == "ok" and res["scores"] == {d: (r["scores"] or {}).get(d)
                                                          for d in (J.ANSWERABLE_DIMS if x["answerable"] else J.UNANSWERABLE_DIMS)}
        rows.append({"answer_key": x["answer_key"], "status": res["status"], "scores": res["scores"],
                     "stored": r["scores"], "equal": same, "same_text": res["text"] == (r.get("raw_text") or ""),
                     "prompt_tokens": res["prompt_tokens"], "output_tokens": res["output_tokens"], "wall_s": res["wall_s"],
                     "load_s": res["load_s"]})
        print(f"check {i}/{len(items)} {x['answer_key']:45s} {res['status']} {'equal' if same else 'DIFFERS'} "
              f"{res['wall_s']} s", flush=True)
    n, eq = len(rows), sum(r["equal"] for r in rows)
    st = sum(r["same_text"] for r in rows)
    first = rows and json.loads((log.read_text().splitlines() or ["{}"])[-1])
    summary = {"_provenance": {"script": "experiments/scorers/judge_passages.py check", "inputs": [str(S440_LEDGER),
                                                                                                 "S376.answers_and_key"],
                               "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
               "reference": "S440 lock pass (Studio), findings/recompute/S440_judge_lock_check.jsonl",
               "n": n, "equal_scores": eq, "identical_text": st, "full_sample": n == CHECK_N,
               "all_calls_ok": all(r["status"] == "ok" for r in rows),
               "passed": n == CHECK_N and eq == n and all(r["status"] == "ok" for r in rows),
               "differences": [r for r in rows if not r["equal"]],
               "answers_whose_call_loaded_the_model": sum((r["load_s"] or 0) > 1 for r in rows),
               "lock_sha256": lock.sha256, "model": model, "server": base, "ollama_version": first.get("ollama_version"),
               "model_digest": first.get("model_digest"), "options_sent": first.get("options_sent"),
               "fields_sent": first.get("fields_sent"), "system_prompt_sha256": call.system and sha(call.system),
               "system_sent_sha256": first.get("system_sent") and sha(first["system_sent"]),
               "machine_identity": fl["machine_identity"], "server_checks": fl["server_check"]["checks"],
               "code": code_identity(), "fresh_load_ok": fl["ok"]}
    (out / "repro_check.json").write_text(json.dumps(summary, indent=1) + "\n")
    with (out / "repro_check_rows.jsonl").open("w") as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    print(f"REPRODUCTION: {eq} of {n} answers with every score equal to S440's stored lock pass; {st} of {n} identical "
          f"judge text; {'PASSED' if summary['passed'] else 'NOT PASSED' + ('' if n == CHECK_N else ' (a smoke sample)')}",
          flush=True)
    return 0 if summary["passed"] or (n < CHECK_N and eq == n) else 1


def sent_t0_think_off(rec: dict) -> bool:
    """D112 Q18 (3): the call record says it sent temperature 0 and think false."""
    return (rec.get("options_sent") or {}).get("temperature") == 0 and (rec.get("fields_sent") or {}).get("think") is False


def cmd_check_repeat(a) -> int:
    """D85's check of the second judge (--judge second): no stored score of it exists, so the 107 calibration answers
    are judged twice, each pass after its own fresh load, and compared answer by answer. Passes only if all 107 give
    every score equal in both passes, every call is ok, and every call record of the check sent temperature 0 and
    think false. Writes the same repro_check.json keys as `check`, so require_check reads it the same way."""
    import S376_judge_calibration as S376
    out = a.out
    items = S376.answers_and_key()
    if len(items) != CHECK_N:
        raise SystemExit(f"REFUSED: expected the {CHECK_N} calibration answers, got {len(items)}")
    items = items[: a.n] if a.n else items
    log = out / "check_calls.jsonl"
    base = a.base.rstrip("/")
    passes, sent, fls = [], [], []
    for p in (1, 2):
        lock, model, call, fl = start(a, out, f"check pass {p}")
        fls.append(fl)
        n0 = len(read_rows(log))
        got = []
        for i, x in enumerate(items, 1):
            q = J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)
            res = judge_call(base, call, q, x["answerable"], None, log, {"answer": x["answer_key"],
                                                                         "variant": f"a_check_{p}"})
            got.append(res)
            print(f"check pass {p} {i}/{len(items)} {x['answer_key']:45s} {res['status']} {res['wall_s']} s", flush=True)
        sent += read_rows(log)[n0:]
        passes.append(got)
    rows = []
    for x, r1, r2 in zip(items, *passes):
        same = r1["status"] == "ok" and r2["status"] == "ok" and r1["scores"] == r2["scores"]
        rows.append({"answer_key": x["answer_key"], "status": [r1["status"], r2["status"]], "scores": r2["scores"],
                     "first_scores": r1["scores"], "equal": same, "same_text": r1["text"] == r2["text"],
                     "prompt_tokens": r2["prompt_tokens"], "output_tokens": [r1["output_tokens"], r2["output_tokens"]],
                     "wall_s": [r1["wall_s"], r2["wall_s"]], "load_s": [r1["load_s"], r2["load_s"]]})
    n, eq = len(rows), sum(r["equal"] for r in rows)
    st = sum(r["same_text"] for r in rows)
    all_ok = all(s == "ok" for r in rows for s in r["status"])
    t0 = bool(sent) and all(sent_t0_think_off(r) for r in sent)
    one_lock = all(r.get("lock_sha256") == lock.sha256 for r in sent)
    same_machine = fls[0]["machine_identity"] == fls[1]["machine_identity"]
    first = sent[-1] if sent else {}
    summary = {"_provenance": {"script": "experiments/scorers/judge_passages.py check --judge second",
                               "inputs": ["S376.answers_and_key"], "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
               "reference": "D85 repeat check: the second judge's own first pass, after its own fresh load",
               "judge": "second", "n": n, "equal_scores": eq, "identical_text": st, "full_sample": n == CHECK_N,
               "all_calls_ok": all_ok, "calls_read": len(sent), "sent_temperature_0_think_false": t0,
               "one_lock_both_passes": one_lock, "same_machine_both_passes": same_machine,
               "passed": n == CHECK_N and eq == n and all_ok and t0 and one_lock and same_machine,
               "differences": [r for r in rows if not r["equal"]],
               "lock_sha256": lock.sha256, "model": model, "server": base, "ollama_version": first.get("ollama_version"),
               "model_digest": first.get("model_digest"), "options_sent": first.get("options_sent"),
               "fields_sent": first.get("fields_sent"), "system_prompt_sha256": call.system and sha(call.system),
               "system_sent_sha256": first.get("system_sent") and sha(first["system_sent"]),
               "machine_identity": fls[0]["machine_identity"], "server_checks": fls[0]["server_check"]["checks"],
               "server_checks_pass_2": fls[1]["server_check"]["checks"],
               "code": code_identity(), "fresh_load_ok": all(f["ok"] for f in fls)}
    (out / "repro_check.json").write_text(json.dumps(summary, indent=1) + "\n")
    with (out / "repro_check_rows.jsonl").open("w") as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    print(f"REPRODUCTION: {eq} of {n} answers with every score equal in two passes of {model} (D85 repeat check); "
          f"{st} of {n} identical judge text; every call sent temperature 0 and think false: {t0}; "
          f"{'PASSED' if summary['passed'] else 'NOT PASSED' + ('' if n == CHECK_N else ' (a smoke sample)')}",
          flush=True)
    return 0 if summary["passed"] or (n < CHECK_N and eq == n and all_ok and t0 and one_lock and same_machine) else 1


def require_check(check_dir: Path, lock, base: str, machine: str, binary: Path, judge: str = "main") -> dict:
    """The check must have run on this machine (hostname, --machine, the sha256 of the binary given now), this
    server, Ollama version, model digest, lock, options and system prompt, and this code, for this judge (--judge)."""
    f = check_dir / "repro_check.json"
    if not f.exists():
        raise SystemExit(f"REFUSED: no reproduction check in {check_dir}; run `check` first (README.md:75-79)")
    c = json.loads(f.read_text())
    from experiments.runner.ollama_client import server_state
    model = judge_of(lock, judge)
    call = lock.ollama(model, role="judge")
    version, digest = server_state(base, call.model)
    want = {"passed": True, "full_sample": True, "model": model, "lock_sha256": lock.sha256, "server": base,
            "ollama_version": version, "model_digest": digest, "options_sent": call.options,
            "system_prompt_sha256": call.system and sha(call.system),
            "system_sent_sha256": call.system and sha(call.system),
            "machine_identity": {"hostname": socket.gethostname(), "machine": machine,
                                 "binary_sha256": sha(binary.read_bytes())},
            "code": code_identity()}
    bad = {k: (c.get(k), v) for k, v in want.items() if c.get(k) != v}
    if bad:
        raise SystemExit(f"REFUSED: the reproduction check does not cover this run (check value, now): {bad}")
    return c


# ---------------------------------------------------------------- answers

def answers(arm: Path, rows_sel: str | None) -> list[dict]:
    v2 = {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}
    rows = json.loads(arm.read_text())["per_question_results"]
    if rows_sel:
        s, e = (int(x) if x else None for x in rows_sel.split(":"))
        rows = rows[s:e]
    out = []
    for r in rows:
        qid = r["question_id"]
        if qid not in v2:
            raise SystemExit(f"REFUSED: {qid} is not in key v2.4")
        ea, ec = S373.key_of(qid, v2)
        gen = r.get("generation") or {}
        x = {"key": f"{r['config']}|{qid}|{r.get('draw')}", "config": r["config"], "question_id": qid,
             "draw": r.get("draw"), "question": r["question"], "expected": ea, "concepts": ec,
             "answerable": S373.judged_answerable(qid, v1, v2), "key_hash": S373.key_hash(qid, v2),
             "answer": gen.get("answer") or "", "gen_error": gen.get("error"),
             "contexts": r.get("contexts") or [], "contexts_capture": r.get("contexts_capture")}
        # everything that enters the two prompts; a row of another arm, answer, key or passage set differs here
        x["item_sha256"] = sha(json.dumps([x[k] for k in ("question", "expected", "concepts", "answer", "gen_error",
                                                           "answerable", "key_hash")]
                                          + [[c.get("source"), c.get("chunk_idx"), c["text"]] for c in x["contexts"]],
                                          ensure_ascii=False))
        out.append(x)
    ids = [(x["config"], x["question_id"], x["draw"]) for x in out]
    if len(set(ids)) != len(ids):
        raise SystemExit("REFUSED: the arm holds two answers with the same (config, question_id, draw)")
    return out


def run_answers(run: Path, rows_sel: str | None, store: Path | None) -> list[dict]:
    """--run (F5): the answers of one run as experiments/scorers/records.py reads them, in answers()'s form plus
    run_id, answer_key and passages_kind. The prompt rule is answers()'s (S373.judged_answerable, which the check
    reproduces); it must agree with Rule 8's group from the D5 key (LIST.md:328-330), or the run is refused."""
    v2 = {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}
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
            raise SystemExit(f"REFUSED: {qid} is not in key v2.4")
        answerable = S373.judged_answerable(qid, v1, v2)
        if answerable != (r["group"] != "not_answerable"):
            raise SystemExit(f"REFUSED: {qid}: the judge's prompt rule says answerable {answerable}, Rule 8's group "
                             f"is {r['group']}")
        ea, ec = S373.key_of(qid, v2)
        x = {"key": f"{r['run_id']}|{r['answer_key']}", "config": r["config"], "question_id": qid, "draw": r["draw"],
             "question": r["question"], "expected": ea, "concepts": ec, "answerable": answerable,
             "key_hash": S373.key_hash(qid, v2), "answer": r["answer"] if r["status"] == "ok" else "",
             "gen_error": r["error"], "contexts": r["passages"] or [], "contexts_capture": r["passages_kind"],
             "run_id": r["run_id"], "answer_key": r["answer_key"], "passages_kind": r["passages_kind"]}
        x["item_sha256"] = sha(json.dumps([x[k] for k in ("question", "expected", "concepts", "answer", "gen_error",
                                                           "answerable", "key_hash")]
                                          + [[c.get("source"), c.get("chunk_idx"), c["text"]] for c in x["contexts"]],
                                          ensure_ascii=False))
        out.append(x)
    return out


def stored_scores() -> dict[str, dict]:
    """sha256 of an (a) prompt -> devstral's stored judgment of exactly that prompt (STORED ledgers; per ledger key
    the latest ok row under the current key; the prompt rebuilt from S373's own source reader). S440 found S373's
    settings (num_ctx 32,768, num_predict 8,192) and the lock's give equal scores and text on 107 of 107."""
    v2 = {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}
    out = {}
    for ledger, source in STORED:
        latest = {}
        for r in map(json.loads, filter(str.strip, ledger.read_text().splitlines())):
            if r["status"] == "ok" and r["key_hash"] == S373.key_hash(r["question_id"], v2) and (
                    r["key"] not in latest or r["at"] > latest[r["key"]]["at"]):
                latest[r["key"]] = r
        for x in S373.SOURCES[source](v1, v2):
            r = latest.get(x["key"])
            if r is None:
                continue
            p = sha(J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None))
            ref = {"scores": r["scores"], "ledger": ledger.name, "key": r["key"], "at": r["at"],
                   "ollama": r["ollama"], "options": r["options"]}
            if p in out and out[p]["scores"] != r["scores"]:
                ref = {"scores": None, "conflict": [out[p], ref]}   # one prompt stored with two scores: no reference
            out[p] = ref
    return out


def safe_prompts(x: dict) -> tuple[str, str | None, str | None, str | None]:
    """prompts(), with a marker in a passage refusing only that answer's (b): (a, b, block, refusal)."""
    try:
        return (*prompts(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], x["contexts"]),
                None)
    except MarkerInPassage as e:
        return J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None), \
            None, None, str(e)


def reusable_a(prev: dict | None) -> bool:
    """PHASES: a row whose (a) a full run takes over, making only the (b) call (same item and run: the caller's test)."""
    return bool(prev) and prev["a"]["status"] == "ok" and prev["b"]["status"] == DEFERRED


def judge_answer(base: str, call, x: dict, log: Path, stored: dict | None, variants: str = "ab",
                 prev: dict | None = None) -> dict:
    """One answer's row. variants "a": the (b) call a full run would make is not made, (b) stored as deferred.
    prev: the answer's latest row, when reusable_a(prev) under the same item and run (cmd_run checks those)."""
    row = {"question_id": x["question_id"], "config": x["config"], "draw": x["draw"], "key_hash": x["key_hash"],
           "item_sha256": x["item_sha256"], "answerable_prompt": x["answerable"], "n_passages": len(x["contexts"]),
           "passage_chars": sum(len(c["text"]) for c in x["contexts"]), "contexts_capture": x["contexts_capture"],
           "a_stored": None, "a_equals_stored": None}
    if "run_id" in x:                                     # --run rows only; an --arm row is written as before
        row.update(run_id=x["run_id"], answer_key=x["answer_key"], passages_kind=x["passages_kind"])
    t0 = time.time()
    if not x["answer"].strip() or x["gen_error"]:
        row.update(a={"status": "no_answer"}, b={"status": "no_answer"}, error=x["gen_error"] or "no answer stored")
    else:
        pa, pb, blk, refusal = safe_prompts(x)
        extra = {"answer": x["key"], "key_hash": x["key_hash"], "item_sha256": x["item_sha256"]}
        if variants == "ab" and reusable_a(prev):
            # PHASES: (a) was judged by an earlier --variants a run of this --out, same answer, lock and code
            row["a"], row["a_stored"], row["a_equals_stored"] = prev["a"], prev["a_stored"], prev["a_equals_stored"]
            row["a_reused"] = {"at": prev["at"], "wall_s": prev["wall_s"]}
        else:
            row["a"] = judge_call(base, call, pa, x["answerable"], None, log, {**extra, "variant": "a"})
            ref = (stored or {}).get(sha(pa))
            if ref is not None and ref["scores"] is not None:
                row["a_stored"] = ref
                row["a_equals_stored"] = row["a"]["status"] == "ok" and row["a"]["scores"] == ref["scores"]
        if refusal:
            row["b"] = {"status": "refused_marker", "error": refusal}
        elif pb is None:
            row["b"] = {"status": "not_applicable" if not x["answerable"] else "no_passages"}
        elif row["a_equals_stored"] is False:
            # (a) did not reproduce devstral's stored score of this very prompt: no new number is written for it
            row["b"] = {"status": "withheld_a_differs"}
        elif variants == "a":
            row["b"] = {"status": DEFERRED}                   # PHASES: the (b) call a full run makes here, not made
        else:
            ids = [{"source": c.get("source"), "chunk_idx": c.get("chunk_idx"), "chars": len(c["text"]),
                    "sha256": sha(c["text"])} for c in x["contexts"]]
            row["b"] = judge_call(base, call, pb, True, ids, log, {**extra, "variant": "b"})
            row["block_sha256"] = sha(blk)
    for v in ("a", "b"):
        row[f"faithfulness_{v}"] = (row[v].get("scores") or {}).get("faithfulness")
    row["b_faithfulness_missing"] = row["b"]["status"] == "ok" and row["faithfulness_b"] is None
    row["wall_s"] = round(time.time() - t0, 1)
    row["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return row


def ident(d: dict) -> tuple:
    # --run rows also carry run_id (F55: one --out may hold several runs, e.g. exp_02's indexes); --arm rows as before
    if d.get("run_id") is not None:
        return d["run_id"], d["config"], d["question_id"], d["draw"]
    return d["config"], d["question_id"], d["draw"]


def run_identity(lock, call) -> str:
    """Everything outside the answer that decides what a row's calls sent: lock, code, system prompt, options, and
    for any judge other than [judge] model the model (--judge second: D112 Q5; the main judge's identity is as before)."""
    d = {"lock": lock.sha256, "code": code_identity(), "options": call.options, "fields": call.fields,
         "system": call.system and sha(call.system)}
    if (call.requested or call.model) != lock.d["judge"]["model"]:
        d["judge"] = call.requested or call.model
    return sha(json.dumps(d, sort_keys=True))


def read_rows(res_f: Path) -> list[dict]:
    return list(map(json.loads, filter(str.strip, res_f.read_text().splitlines()))) if res_f.exists() else []


def answered(x: dict) -> bool:
    return bool(x["answer"].strip()) and not x["gen_error"]


def select(items: list[dict], draws: list[int] | None, keys: list[str] | None, answered_only: bool) -> list[dict]:
    """PHASES: the answers of the draws named, of the answer keys named (one file may list several runs' keys: every
    key of a config this run holds must be there), and with answered_only only those with an answer and no generation
    error."""
    if keys is not None:
        held, configs = {x.get("answer_key") for x in items}, {x["config"] for x in items}
        missing = [k for k in keys if k.split("|")[-3:-2] and k.split("|")[-3] in configs and k not in held]
        if missing:
            raise SystemExit(f"REFUSED: {len(missing)} of the {len(keys)} keys named are not in the run (first "
                             f"{missing[0]!r})")
        want = set(keys)
        items = [x for x in items if x.get("answer_key") in want]
    if draws is not None:
        items = [x for x in items if x["draw"] in draws]
    return [x for x in items if answered(x)] if answered_only else items


def is_done(d: dict, variants: str) -> bool:
    """A row needs no call in a run of these variants. "ab": both final. "a" (phases 1 and 2): (a) final, whatever (b)
    holds (deferred, final, or a (b) that failed in a phase 3, which only a run with (b) tries again, so a phase-1
    resume never overwrites it with "deferred"; review of 18 October F3), except withheld_a_differs, whose (a) is
    tried again on resume as in a full run."""
    if d["a"]["status"] not in FINAL:
        return False
    if variants == "a":
        return d["b"]["status"] != "withheld_a_differs"
    return d["b"]["status"] in FINAL


def latest_rows(res_f: Path, mine: dict, run_sha: str, out: Path) -> dict:
    """ident -> the latest row of each answer in mine (ident -> item_sha256); refuses a row of one of them judged on
    another answer, key, passage set, lock or code (so one file never mixes two definitions)."""
    latest = {}
    for d in read_rows(res_f):
        if ident(d) not in mine:                          # another --rows, --draws or --keys selection: not this run's
            continue
        if d.get("item_sha256") != mine[ident(d)] or d.get("run_sha256") != run_sha:
            raise SystemExit(f"REFUSED: {out} already holds {ident(d)} judged on another answer, key, passage set, lock "
                             f"or code (item {d.get('item_sha256')}, run {d.get('run_sha256')}); use a new --out")
        latest[ident(d)] = d
    return latest


def hold_writer(out: Path) -> None:
    """One writer per --out (PHASES): an exclusive flock on <out>/.writer.lock for this process's life; exit
    WRITER_BUSY when another process holds it."""
    fh = (out / ".writer.lock").open("a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(f"WRITER BUSY: another process writes {out} (its .writer.lock is held); nothing done", flush=True)
        sys.exit(WRITER_BUSY)
    _WRITER.append(fh)


def cmd_run(a) -> int:
    base = a.base.rstrip("/")
    lock0 = load()
    which = judge_arg(a)
    model0 = judge_of(lock0, which)
    check = require_check(a.check_dir, lock0, base, a.machine, a.binary, which)
    run_sha = run_identity(lock0, lock0.ollama(model0, role="judge"))
    jtag = judge_tag(which, model0, lock0.ollama(model0, role="judge"))
    if a.keys and not a.run:
        raise SystemExit("REFUSED: --keys needs --run (an --arm row has no answer key)")
    keys = [k for k in a.keys.read_text().splitlines() if k.strip()] if a.keys else None
    items = run_answers(a.run, a.rows, a.store) if a.run else answers(a.arm, a.rows)
    items = select(items, a.draws, keys, a.answered_only)
    for x in items:                                       # every prompt pair is built and verified before any call
        if answered(x):
            safe_prompts(x)
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    hold_writer(out)
    refuse_other_judge(out, model0)
    res_f, log = out / "judge_passages.jsonl", out / "judge_passages_calls.jsonl"
    mine = {ident(x): x["item_sha256"] for x in items}
    latest = latest_rows(res_f, mine, run_sha, out)
    done = {k for k, d in latest.items() if is_done(d, a.variants)}
    todo = [x for x in items if ident(x) not in done][: a.limit]
    if not todo:                                          # nothing to judge: no fresh load, nothing unloaded
        return finish(a, out, res_f, mine, run_sha, items, None, jtag)
    stored = stored_scores() if which == "main" else {}  # STORED is devstral's: no reference for the second judge
    lock, model, call, fl = start(a, out, "run")
    if lock.sha256 != lock0.sha256 or run_identity(lock, call) != run_sha:
        raise SystemExit("REFUSED: the lock or the code changed while the run started")
    header = {"_provenance": {"script": "experiments/scorers/judge_passages.py run", "inputs": [str(a.run or a.arm), str(S373.KEY)]
                              + [str(p) for p, _ in STORED], "started": time.strftime("%Y-%m-%dT%H:%M:%S")},
              "model": model, "model_digest": call.digest, "lock_sha256": lock.sha256, "options": call.options,
              "fields": call.fields, "system_prompt_sha256": call.system and sha(call.system), "base": base,
              "machine_identity": fl["machine_identity"], "run_sha256": run_sha,
              "check": {k: check[k] for k in ("n", "equal_scores", "identical_text", "lock_sha256", "model_digest")},
              "code": code_identity(), "block_head": BLOCK_HEAD, "begin": BEGIN, "end": END, "anchor": ANCHOR,
              "row_range": a.rows, "variants": a.variants, "draws": a.draws, "keys": a.keys and str(a.keys),
              "answered_only": a.answered_only, "rows": len(items), "already_done": len(done), "to_do": len(todo),
              "a_to_reuse": sum(1 for x in todo if a.variants == "ab" and reusable_a(latest.get(ident(x)))),
              "with_stored_score": sum(1 for x in items if answered(x) and sha(safe_prompts(x)[0]) in stored)}
    with (out / "judge_passages_headers.jsonl").open("a") as fh:
        fh.write(json.dumps(header, ensure_ascii=False) + "\n")
    print(f"judge with passages ({'(a) only, (b) deferred' if a.variants == 'a' else '(a) and (b)'}): {len(items)} "
          f"answers, {len(done)} done, {len(todo)} to judge with {model} ({header['a_to_reuse']} with their (a) "
          f"reused); {header['with_stored_score']} have a stored devstral score for their (a) prompt", flush=True)
    for x in todo:
        row = judge_answer(base, call, x, log, stored, a.variants, latest.get(ident(x)))
        row["lock_sha256"], row["run_sha256"] = lock.sha256, run_sha
        if jtag is not None:                              # the second judge's rows name it; the main judge's as before
            row["judge"] = jtag
        with res_f.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['at']} {x['config']:13s} {x['question_id']:28s} a {row['a']['status']} "
              f"F={row['faithfulness_a']} stored={'-' if row['a_equals_stored'] is None else row['a_equals_stored']}  "
              f"b {row['b']['status']} F={row['faithfulness_b']}  {row['wall_s']} s", flush=True)
    rechecked = None
    if todo and not a.no_recheck:
        rechecked = recheck(a, base, items, res_f, out, stored, run_sha)
    return finish(a, out, res_f, mine, run_sha, items, rechecked, jtag)


def finish(a, out: Path, res_f: Path, mine: dict, run_sha: str, items: list[dict], rechecked: dict | None,
           jtag: dict | None = None) -> int:
    """The summary of this selection's rows and the run's last line (run_s3.sh reads it). jtag: the second judge's
    "judge" (judge_tag), written into the summary; None (the main judge) writes the summary as before."""
    rows = {ident(d): d for d in read_rows(res_f) if d.get("run_sha256") == run_sha and ident(d) in mine}
    from collections import Counter
    summary = {"_provenance": {"script": "experiments/scorers/judge_passages.py run", "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
               "run_sha256": run_sha, "variants": a.variants, "draws": a.draws, "keys": a.keys and str(a.keys),
               "answered_only": a.answered_only, "answers": len(items), "rows": len(rows),
               "to_do": sum(1 for x in items if ident(x) not in rows or not is_done(rows[ident(x)], a.variants)),
               "status_a": dict(Counter(d["a"]["status"] for d in rows.values())),
               "status_b": dict(Counter(d["b"]["status"] for d in rows.values())),
               "a_equals_stored": dict(Counter(str(d.get("a_equals_stored")) for d in rows.values())),
               "b_faithfulness_missing": sum(bool(d.get("b_faithfulness_missing")) for d in rows.values()),
               "recheck": rechecked}
    if jtag is not None:
        summary["judge"] = jtag
    (out / "judge_passages_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"SUMMARY: (a) {summary['status_a']}; (b) {summary['status_b']}; (a) against stored "
          f"{summary['a_equals_stored']}; (b) ok without faithfulness {summary['b_faithfulness_missing']}", flush=True)
    failed = []
    if summary["a_equals_stored"].get("False"):
        failed.append(f"{summary['a_equals_stored']['False']} answers whose (a) differs from the stored score")
    if rechecked is not None and rechecked["passed"] is False:
        failed.append(f"the recheck ({rechecked['equal']} of {rechecked['n']} equal)")
    if failed:
        print("JUDGE WITH PASSAGES NOT PASSED: " + "; ".join(failed), flush=True)
        return 1
    print("JUDGE PLAIN CALL DONE ((b) deferred)" if a.variants == "a" else "JUDGE WITH PASSAGES DONE", flush=True)
    return 0


def recheck(a, base: str, items: list[dict], res_f: Path, out: Path, stored: dict, run_sha: str) -> dict:
    """F1 (job.py:11-12): after another fresh load, the job's first RECHECK_N answers that reached the model, judged
    again and compared with what it wrote. Passes only if every one gives the same status and scores in (a) and (b).
    With --variants a only (a) is compared (D112 Q13, audit A21-23): the recheck makes no (b) call, and a row a phase 3
    completed in the same out holds a (b) the plain call cannot repeat."""
    lock, model, call, fl = start(a, out, "recheck")
    latest = {ident(d): d for d in read_rows(res_f) if d.get("run_sha256") == run_sha}
    picked = [x for x in items if ident(x) in latest and latest[ident(x)]["a"]["status"] != "no_answer"][:RECHECK_N]
    compared = "a" if a.variants == "a" else "ab"
    n = eq = 0
    for x in picked:
        prev = latest[ident(x)]
        row = judge_answer(base, call, x, out / "judge_passages_recheck_calls.jsonl", stored, a.variants)
        same = all(row[v].get("scores") == prev[v].get("scores") and row[v]["status"] == prev[v]["status"]
                   for v in compared)
        n, eq = n + 1, eq + same
        line = {"key": x["key"], "item_sha256": x["item_sha256"], "run_sha256": run_sha, "equal": same,
                "now": {v: row[v].get("scores") for v in "ab"},
                "written": {v: prev[v].get("scores") for v in "ab"}, "at": row["at"]}
        if compared == "a":
            line["compared"] = "a"
        with (out / "judge_passages_recheck.jsonl").open("a") as fh:
            fh.write(json.dumps(line) + "\n")
    res = {"n": n, "equal": eq, "passed": (eq == n) if n else None, "run_sha256": run_sha, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if compared == "a":
        res["compared"] = "a"
    (out / "judge_passages_recheck_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"RECHECK: {eq} of {n} answers give the same {'(a)' if compared == 'a' else '(a) and (b)'} scores after a fresh load; "
          f"{ {True: 'PASSED', False: 'NOT PASSED', None: 'nothing to recheck'}[res['passed']] }", flush=True)
    return res


# ---------------------------------------------------------------- offline

def cmd_selftest(a) -> int:
    items = run_answers(a.run, None, a.store) if a.run else answers(a.arm, None)
    n_b = n_refused = 0
    longest = 0
    for x in items:
        pa, pb, blk, refusal = safe_prompts(x)
        n_refused += bool(refusal)
        assert pa == J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)
        if pb is not None:
            n_b += 1
            assert pb.replace(blk, "", 1) == pa
            assert all(c["text"] in pb for c in x["contexts"]), "a passage is not whole in (b)"
            assert pb.index(blk) < pb.index(ANCHOR) and pb.count(ANCHOR) >= 1
            longest = max(longest, len(pb))
    print(f"SELFTEST: {len(items)} answers; (a) equals the archived build_prompt on all; {n_b} (b) prompts, each (a) "
          f"plus one block before '## Generated Answer', every passage whole; longest (b) {longest:,} characters; {n_refused} refused for a marker in a passage")
    return 0


def cmd_block(a) -> int:
    x = (run_answers(a.run, None, a.store) if a.run else answers(a.arm, None))[a.row]
    pa, pb, blk, refusal = safe_prompts(x)
    sys.stdout.write(blk if blk is not None else f"(no block: {refusal or 'decline prompt or no passages'})\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "run"):
        p = sub.add_parser(name)
        p.add_argument("--base", default="http://127.0.0.1:11434")
        p.add_argument("--log", required=True, type=Path, help="the server's log, for the fresh load's checks")
        p.add_argument("--binary", required=True, type=Path, help="the server's executable, checked against [server]")
        p.add_argument("--machine", required=True, choices=["macos", "beelink"])
        p.add_argument("--out", required=True, type=Path)
        p.add_argument("--judge", choices=list(JUDGES), default="main",
                       help="main: LOCK.toml [judge] model (default); second: [judge] second_model (D85, D112 Q5)")
    sub.choices["check"].add_argument("--n", type=int, default=0, help="first n answers only: a smoke test")
    r = sub.choices["run"]
    r.add_argument("--check-dir", required=True, type=Path)
    r.add_argument("--limit", type=int)
    r.add_argument("--rows", help="START:END of the arm's answers in its fixed order")
    r.add_argument("--no-recheck", action="store_true")
    r.add_argument("--variants", choices=["ab", "a"], default="ab", help="a: the plain call only, (b) deferred (PHASES)")
    r.add_argument("--draws", type=lambda v: [int(d) for d in v.split(",")], help="e.g. 1 or 2,3 (PHASES)")
    r.add_argument("--keys", type=Path, help="a file of answer keys, one per line: only those answers (--run)")
    r.add_argument("--answered-only", action="store_true", help="leave out answers with no answer or an error")
    s = sub.add_parser("selftest")
    b = sub.add_parser("block")
    b.add_argument("--row", type=int, default=0)
    for p in (r, s, b):                                  # --run (F5): a run's answers, read by records.py
        src = p.add_mutually_exclusive_group(required=True)
        src.add_argument("--arm", type=Path)
        src.add_argument("--run", type=Path, help="a run's sink or results file (experiments/scorers/records.py)")
        p.add_argument("--store", type=Path, help="--run: the Chroma directory to resolve passage ids against "
                       "(default: the store the run recorded)")
    a = ap.parse_args()
    return {"check": cmd_check, "run": cmd_run, "selftest": cmd_selftest, "block": cmd_block}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
