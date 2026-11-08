#!/usr/bin/env python3
r"""S495 - D160 (5), Q16 O-a: the proof that T2's newer judge code scores G1's answers as G1's judge code did.

WHY. T2 (Figure 2 panel f: other generators on G1's six strategies) is judged on the judge code at main
(run_sha256 11e51fde), G1 on the code of commit d0312bc (run_sha256 38ae79ab): experiments/scorers/judge_passages.py
and scripts/S373_rejudge_v2.py changed after d0312bc (3b12d57c, 6c1701ce, 30aba28c; findings/recompute/S3_runs/
README.md, section "T2"). Valerio chose to keep T2 on the new code with a proof on a sample of G1's own answers that
the new code repeats G1's scores (experiments/README.md D160 (5)); panel f then accepts both fingerprints, and only
when this script's verdict exists and passed (S463_fig2_ranking.panel_f_judge_codes).

WHAT IT READS (frozen inputs only, each checked by scripts/fig_repro.py, as S463 rebuild reads them):
  - G1's judged rows: findings/recompute/fig2_inputs/g1_collect.jsonl (2,430 rows, the S3 collect Figure 2 is drawn
    from), every row under run_sha256 38ae79ab;
  - the answers G1 judged: K1's runs (frozen k1_inputs_runs.tar) and, for the 15 answers G1 reran on 18 October
    (keys.txt in the tar), G1R15's runs (frozen fig2_g1r15_inputs.tar). Set FROZEN_TARS to the folder holding the
    tars if it is not ~/Mentori_scratch_keep/frozen_2026-10-26;
  - the judge code: the working tree's (the new code) and `git show d0312bc:<file>` (G1's code).

WHAT A "REQUEST" IS HERE. The (a) call, the plain judge call Figure 2 and panel f read: the JSON body the Ollama
client sends (lock.OllamaCall.payload: model, prompt, stream, options, think, system) and its passages argument
(None for (a)), as each code version's judge_answer(..., variants="a") hands them to generate(). Each version builds
its own call through its own start() (the fresh load and the server checks replaced by stubs offline) and its own
answers through its own run_answers(). The passage texts are not read (G1's Chroma store is not frozen, and the (a)
prompt holds none: judge_passages.prompts() builds (a) from question, key and answer only); each passage's text is
set to "" so the (b) prompt (built, never sent under variants "a") cannot fail. The test that the rebuilt (a) is
G1's own request is the sha256 of its prompt against the prompt_sha256 G1's row records.

COMMANDS (from the repository root, under uv run):

  offline [--out DIR]
      uv run --frozen python scripts/S495_t2_judge_code_proof.py offline
      No model call. (1) Rebuilds both fingerprints from the code: G1's code (d0312bc) must give G1's run_sha256
      38ae79ab and the working tree's T2's 11e51fde, and the other files the judge request goes through (lock.py,
      ollama_client.py, job.py, S141_runner/judge.py, S376, records.py, index_identity.py, LOCK.toml, devstral's
      system prompt) must be byte-equal at d0312bc and now. (2) For every one of G1's 2,425 answers the judge
      scored ((a) ok; the 5 no_answer rows have no call), builds the (a) request with the old and with the new
      code: the two must be byte-identical, the prompt's sha256 must be G1's recorded prompt_sha256, and G1's stored
      judge reply parsed by each version must give G1's stored scores. (3) Draws the sample (below). Writes
      offline.json and sample.jsonl into DIR (default findings/recompute/S495_t2_judge_code_proof/); both carry no
      time, so a second run writes the same bytes (D155). Exit 0 when every check passed, 1 otherwise.

  online --check-dir DIR --log FILE --binary FILE --machine macos|beelink [--out DIR]
      S495_JUDGE_PORT=<port> uv run --frozen python scripts/S495_t2_judge_code_proof.py online --check-dir ... \
          --log <server log> --binary <ollama> --machine macos
      Model calls: the judge port is read from env S495_JUDGE_PORT only (host 127.0.0.1), never from the command
      line, so no port number sits in a command line a guard reads. Runs the offline build first and refuses unless
      it passed and its sample equals DIR/sample.jsonl byte for byte. Then, as judge_passages.py run does: the port's
      107-answer check must cover this server, machine, binary, lock and code (judge_passages.require_check on
      --check-dir: run `judge_passages.py check` there first), a fresh load of devstral (every model on that server
      is unloaded first: use a port no other job is using), then each sampled answer judged once with the new code
      (variants "a", G1's settings from LOCK.toml), its scores compared with G1's stored scores. Writes DIR/online/
      (rows.jsonl, calls.jsonl, the fresh-load record) and DIR/verdict.json: counts, the run_sha256 of both codes,
      sha256 of the sample, rows and calls files, and "passed". Passed = every one of the sampled answers gave a
      judge reply with every score equal to G1's, the same prompt_sha256 as G1's, from the model digest G1's row
      names. Refuses when DIR/verdict.json or DIR/online exists (a verdict is a record: move it away to run again).
      Exit 0 when passed, 1 otherwise. About 32 s per call on the Studio (G1's median (a) call 29.7 s), so about an
      hour for 120 answers.

  selftest
      uv run --frozen python scripts/S495_t2_judge_code_proof_test.py   (the tests live in their own file)

THE SAMPLE: 120 of G1's judged answers, 20 per strategy (single pass, multi-hop, verified pass, RLM-5, RLM-10,
RLM-20), each strategy's 20 split by Rule 8's groups near their share of the 135 questions (86 : 39 : 10 gives
12.7 : 5.8 : 1.5): 13 answerable, 5 not answerable, 2 false premise (rounded up from 1.5 so the group is never a
single answer), so every prompt kind (the answerable prompt, the decline prompt) and every strategy is judged.
Within a strategy and group, the answers whose sha256("S495|" + answer key) is smallest (any draw), so the sample
is fixed by the data, not by a seed. Why 120: the offline check already covers every one
of G1's 2,425 judged answers for the request bytes; what only a model call can show is that the judge repeats G1's
scores now. If the new code changed the score of 2.5% or more of G1's answers, a sample of 120 shows at least one
difference with probability 1 - 0.975^120 = 95.2% (no difference in 120 gives a one-sided 95% upper bound of
1 - 0.05^(1/120) = 2.5% on the share that differs). The 107 calibration answers each T2 port already repeated are
not G1's answers; this sample is.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fig_repro as FR  # noqa: E402

OUT = ROOT / "findings" / "recompute" / "S495_t2_judge_code_proof"
G1_COMMIT = "d0312bc"                    # G1's judge code (S3_runs/README.md "T2"; check_s3_phases.py BASE_COMMIT)
G1_RUN_SHA = "38ae79ab023b97562b69b2875b3c8001b02f887d5578121103b85d4a0b4729da"   # G1's rows (collect sidecar)
T2_RUN_SHA = "11e51fde82185384415ce4d0db1571ab7f442e0def3a6ea2cf81a98d44c1cd8c"   # T2's rows (main's judge code)
PORT_ENV = "S495_JUDGE_PORT"
JP_REL = "experiments/scorers/judge_passages.py"
S373_REL = "scripts/S373_rejudge_v2.py"
# judge_passages.code_identity()'s files, by its keys (template_file is a constant of S141_runner/judge.py)
CODE_FILES = {"judge_passages_py": JP_REL, "s141_judge_py": "scripts/S141_runner/judge.py",
              "s373_rejudge_v2_py": S373_REL, "s376_judge_calibration_py": "scripts/S376_judge_calibration.py",
              "records_py": "experiments/scorers/records.py", "index_identity_py": "experiments/runner/index_identity.py"}
# files a judge request also goes through, which must be the same bytes at G1_COMMIT and now
SAME_FILES = ["experiments/runner/lock.py", "experiments/runner/ollama_client.py", "experiments/runner/job.py",
              "scripts/S141_runner/judge.py", "scripts/S376_judge_calibration.py", "experiments/scorers/records.py",
              "experiments/runner/index_identity.py", "experiments/LOCK.toml",
              "data/judge_system_prompts/devstral-small-2_24b.date-2026-10-10.txt"]
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
PER_STRATEGY = {"answerable": 13, "not_answerable": 5, "false_premise": 2}
SALT = "S495|"
SCRIPT = "scripts/S495_t2_judge_code_proof.py"


class Refused(SystemExit):
    def __init__(self, msg: str):
        super().__init__(f"REFUSED: {msg}")


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def git_show(rel: str, rev: str = G1_COMMIT) -> bytes:
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        raise Refused(f"git show {rev}:{rel} failed: {r.stderr.decode()[:200]}")
    return r.stdout


def module_from(src: str, name: str, path: Path):
    """A module from source text, as if it were the file at path (its ROOT and __file__ are the file's)."""
    m = types.ModuleType(name)
    m.__file__ = str(path)
    sys.modules[name] = m
    exec(compile(src, str(path), "exec"), m.__dict__)
    return m


def load_modules(new_src: str | None = None) -> dict:
    """{"old": judge_passages at G1_COMMIT (with S373 at G1_COMMIT), "new": the working tree's}. new_src: a test may
    give other source text for the new module (a mutant); its code_identity still hashes the files on disk."""
    import S373_rejudge_v2 as s373_now
    new = module_from(new_src if new_src is not None else (ROOT / JP_REL).read_text(), "s495_jp_new", ROOT / JP_REL)
    s373_old = module_from(git_show(S373_REL).decode("utf-8"), "s495_s373_old", ROOT / S373_REL)
    saved = sys.modules.get("S373_rejudge_v2")
    sys.modules["S373_rejudge_v2"] = s373_old            # the old module's `import S373_rejudge_v2 as S373`
    try:
        old = module_from(git_show(JP_REL).decode("utf-8"), "s495_jp_old", ROOT / JP_REL)
    finally:
        sys.modules["S373_rejudge_v2"] = saved if saved is not None else s373_now
    if old.S373 is not s373_old or new.S373 is s373_old:
        raise Refused("the old and new judge modules do not each hold their own S373")
    # The old module's code_identity hashes its __file__, which is the working tree's file: G1's identity is the
    # sha256 of each file as it was at G1_COMMIT.
    now = new.code_identity()
    if set(now) != set(CODE_FILES) | {"template_file"}:
        raise Refused(f"judge_passages.code_identity() names {sorted(now)}, not the files this proof knows")
    then = {k: sha(git_show(p)) for k, p in CODE_FILES.items()} | {"template_file": now["template_file"]}
    old.code_identity = lambda: dict(then)
    return {"old": old, "new": new, "code_now": now, "code_g1": then}


@contextlib.contextmanager
def offline_server(mods: list):
    """No server: each module's fresh_load and generate replaced, the client's own server check (refuse_other_build)
    a no-op. Restored on exit."""
    from experiments.runner import ollama_client as OC
    saved = [(m, m.fresh_load, m.generate) for m in mods]
    checked = OC._checked
    try:
        for m in mods:
            m.fresh_load = lambda base, model, log, binary, machine: {
                "server_check": {"checks": {"binary": {"ok": True, "sha256": "offline"}}}, "load_s": 0.0,
                "unloaded": [], "ok": True}
        OC._checked = lambda *a, **k: None
        yield
    finally:
        for m, fl, gen in saved:
            m.fresh_load, m.generate = fl, gen
        OC._checked = checked


class Capture:
    """generate() as the module calls it: records the request body the client would send and answers with the reply
    set in .reply (G1's stored judge text), so the module parses G1's own reply."""

    def __init__(self):
        self.sent, self.reply = [], ""

    def generate(self, base, call, prompt, passages=None):
        self.sent.append(json.dumps({"payload": call.payload(prompt), "passages": passages}, sort_keys=True,
                                    ensure_ascii=False))
        return {"status": "ok", "text": self.reply, "prompt_tokens": None, "output_tokens": None,
                "stop_reason": "stop", "error": None, "wall_s": 0.0, "load_s": 0.0, "model_digest": call.digest,
                "server": base, "ollama_version": None}


def inputs() -> dict:
    """The frozen inputs, each checked (fig_repro): the collect and its sidecar, K1's and G1R15's run folders."""
    fig2 = FR.check_committed(FR.frozen("fig2"))
    k1 = FR.frozen("k1_inputs_runs", "k1_inputs_runs")
    g1r15 = FR.frozen("fig2_g1r15_inputs", "fig2_g1r15_inputs")
    return {"collect": fig2 / "g1_collect.jsonl", "sidecar": fig2 / "g1_collect.jsonl.json", "k1": k1,
            "g1r15": g1r15 / "runs", "g1r15_keys": g1r15 / "keys.txt"}


def groups() -> dict:
    """{question id: Rule 8 group} from the D5 key (as S463.key_groups)."""
    from experiments.runner.experiment import questions
    from experiments.scorers.records import GROUP_OF_TYPE
    g = {q["id"]: GROUP_OF_TYPE[q["answer_type"]] for q in questions()}
    if Counter(g.values()) != Counter({"answerable": 86, "false_premise": 10, "not_answerable": 39}):
        raise Refused(f"the D5 key gives {dict(Counter(g.values()))}")
    return g


def items_of(m, run_dirs: list[Path]) -> dict:
    """{(run_id, answer_key): x} as the module's own run_answers() builds them, passages unresolved (texts "")."""
    R = m.R
    orig = R.read_run
    R.read_run = lambda run, store=None, **k: orig(run, store=store, resolve=False)
    try:
        out = {}
        for d in run_dirs:
            for x in m.run_answers(d, None, None):
                for c in x["contexts"]:
                    if c.get("text") is None:
                        c["text"] = ""
                out[(x["run_id"], x["answer_key"])] = x
        return out
    finally:
        R.read_run = orig


def sample_of(judged: list[dict], grp: dict) -> list[dict]:
    """PER_STRATEGY answers per strategy and Rule 8 group, smallest sha256(SALT + answer key) first."""
    out = []
    for c in CONFIGS:
        for g, k in PER_STRATEGY.items():
            pool = sorted((r for r in judged if r["config"] == c and grp[r["question_id"]] == g),
                          key=lambda r: sha(SALT + r["answer_key"]))
            if len(pool) < k:
                raise Refused(f"{c} {g}: {len(pool)} judged answers, the sample needs {k}")
            out += pool[:k]
    return out


def build(new_src: str | None = None) -> dict:
    """The offline proof, in memory: {"summary": offline.json's content, "sample": [sample lines], "mods", "items"}."""
    from experiments.runner.lock import load
    mods = load_modules(new_src)
    old, new = mods["old"], mods["new"]
    lock = load()
    inp = inputs()
    side = json.loads(inp["sidecar"].read_text())
    rows = [json.loads(x) for x in inp["collect"].read_text().splitlines() if x.strip()]
    runs = Counter(r.get("run_sha256") for r in rows)
    if set(runs) != {G1_RUN_SHA} or side.get("run_sha256") != G1_RUN_SHA or side.get("rows") != len(rows):
        raise Refused(f"G1's collect rows carry run_sha256 {dict(runs)} (sidecar {side.get('run_sha256')}), "
                      f"not G1's {G1_RUN_SHA[:12]} alone")
    grp = groups()
    rerun = {k.strip() for k in inp["g1r15_keys"].read_text().splitlines() if k.strip()}
    if len(rerun) != 15:
        raise Refused(f"{inp['g1r15_keys']} gives {len(rerun)} rerun keys, want 15")
    same = {p: sha(git_show(p)) == sha((ROOT / p).read_bytes()) for p in SAME_FILES}

    caps = {"old": Capture(), "new": Capture()}
    tmp = Path(tempfile.mkdtemp(prefix="s495_"))
    with offline_server([old, new]):
        calls, idents = {}, {}
        for name, m in (("old", old), ("new", new)):
            ns = types.SimpleNamespace(base="http://127.0.0.1:1", log=None, binary=None, machine="macos", judge="main")
            with contextlib.redirect_stdout(io.StringIO()):
                lk, model, call, _ = m.start(ns, tmp / f"start_{name}", "s495 offline")
            m._AFTER_FIRST.clear()                       # no server: the first call's server re-check is not made
            m.generate = caps[name].generate
            calls[name], idents[name] = call, m.run_identity(lk, call)
        dirs = sorted(p for p in inp["k1"].iterdir() if (p / "answers.jsonl").exists())
        items = {n: {"k1": items_of(m, dirs), "g1r15": items_of(m, sorted(p for p in inp["g1r15"].iterdir()
                                                                         if (p / "answers.jsonl").exists()))}
                 for n, m in (("old", old), ("new", new))}
        judged = [r for r in rows if r["a"]["status"] == "ok"]
        counts, diffs = Counter(), []
        log = tmp / "calls.jsonl"
        for r in judged:
            src = "g1r15" if r["answer_key"] in rerun else "k1"
            got = {}
            for n, m in (("old", old), ("new", new)):
                x = items[n][src].get((r["run_id"], r["answer_key"]))
                if x is None:
                    got[n] = None
                    continue
                caps[n].sent.clear()
                caps[n].reply = r["a"]["text"]
                row = m.judge_answer("http://127.0.0.1:1", calls[n], x, log, {}, "a")
                got[n] = {"sent": list(caps[n].sent), "row": row}
            ok_found = got["old"] is not None and got["new"] is not None
            one = ok_found and len(got["old"]["sent"]) == 1 and len(got["new"]["sent"]) == 1
            ident = one and got["old"]["sent"][0] == got["new"]["sent"][0]
            psha = one and got["new"]["row"]["a"].get("prompt_sha256") == r["a"]["prompt_sha256"] \
                and json.loads(got["new"]["sent"][0])["payload"]["prompt"] is not None \
                and sha(json.loads(got["new"]["sent"][0])["payload"]["prompt"]) == r["a"]["prompt_sha256"]
            s_new = one and got["new"]["row"]["a"]["scores"] == r["a"]["scores"]
            s_old = one and got["old"]["row"]["a"]["scores"] == r["a"]["scores"]
            counts.update(found=ok_found, one_request_each=one, identical=ident, prompt_sha256_g1=psha,
                          scores_new_g1=s_new, scores_old_g1=s_old)
            if one:
                req = json.loads(got["new"]["sent"][0])
                counts.update(no_passages_sent=req["passages"] is None,
                              model_is_lock_judge=req["payload"]["model"] == lock.d["judge"]["model"])
            if not (ident and psha and s_new and s_old) and len(diffs) < 20:
                diffs.append({"answer_key": r["answer_key"], "run_id": r["run_id"], "found": ok_found,
                              "identical": ident, "prompt_sha256_g1": psha, "scores_new": s_new, "scores_old": s_old})
    shutil.rmtree(tmp, ignore_errors=True)
    n = len(judged)
    sample = sample_of(judged, grp)
    lines = [{"run_id": r["run_id"], "answer_key": r["answer_key"], "config": r["config"],
              "question_id": r["question_id"], "draw": r["draw"], "group": grp[r["question_id"]],
              "source": "g1r15" if r["answer_key"] in rerun else "k1", "g1_scores": r["a"]["scores"],
              "g1_prompt_sha256": r["a"]["prompt_sha256"], "g1_model_digest": r["a"]["model_digest"],
              "g1_text_sha256": sha(r["a"]["text"] or "")} for r in sample]
    sample_bytes = "".join(json.dumps(x, sort_keys=True) + "\n" for x in lines).encode("utf-8")
    checks = {"g1_fingerprint_reproduced": idents["old"] == G1_RUN_SHA,
              "t2_fingerprint_reproduced": idents["new"] == T2_RUN_SHA,
              "other_files_unchanged_since_g1": all(same.values()),
              "every_answer_found": counts["found"] == n,
              "one_request_each": counts["one_request_each"] == n,
              "requests_byte_identical": counts["identical"] == n,
              "prompt_sha256_is_g1s": counts["prompt_sha256_g1"] == n,
              "g1_reply_parses_to_g1_scores_new": counts["scores_new_g1"] == n,
              "g1_reply_parses_to_g1_scores_old": counts["scores_old_g1"] == n,
              "no_passages_in_a": counts["no_passages_sent"] == n,
              "model_is_lock_judge": counts["model_is_lock_judge"] == n,
              "sample_size": len(lines) == 6 * sum(PER_STRATEGY.values())}
    label = FR.frozen_label
    summary = {
        "_provenance": {"script": f"{SCRIPT} offline", "script_sha256": FR.sha256_file(ROOT / SCRIPT),
                        "decision": "experiments/README.md D160 (5), Q16 O-a",
                        "inputs": {label(inp["collect"]): FR.sha256_file(inp["collect"]),
                                   label(inp["sidecar"]): FR.sha256_file(inp["sidecar"]),
                                   label(inp["g1r15_keys"]): FR.sha256_file(inp["g1r15_keys"]),
                                   **{label(d / "answers.jsonl"): FR.sha256_file(d / "answers.jsonl")
                                      for d in dirs + sorted(p for p in inp["g1r15"].iterdir()
                                                             if (p / "answers.jsonl").exists())}},
                        "g1_commit": G1_COMMIT, "code_files_g1": mods["code_g1"], "code_files_now": mods["code_now"]},
        "g1_run_sha256": G1_RUN_SHA, "t2_run_sha256": T2_RUN_SHA,
        "run_sha256_rebuilt": {"g1_code": idents["old"], "now_code": idents["new"]},
        "other_files_same_bytes_at_g1_commit": same,
        "rows": len(rows), "judged_a_ok": n, "not_judged": dict(Counter(r["a"]["status"] for r in rows
                                                                         if r["a"]["status"] != "ok")),
        "counts": {k: counts[k] for k in ("found", "one_request_each", "identical", "prompt_sha256_g1",
                                           "scores_new_g1", "scores_old_g1", "no_passages_sent",
                                           "model_is_lock_judge")},
        "differences_first_20": diffs,
        "sample": {"n": len(lines), "per_strategy": PER_STRATEGY, "salt": SALT, "file": "sample.jsonl",
                   "sha256": sha(sample_bytes),
                   "by_config_group": {f"{c}|{g}": sum(1 for x in lines if x["config"] == c and x["group"] == g)
                                       for c in CONFIGS for g in PER_STRATEGY},
                   "by_draw": dict(sorted(Counter(x["draw"] for x in lines).items())),
                   "rule": "per strategy 13 answerable, 5 not answerable, 2 false premise of G1's judged answers, "
                           "smallest sha256('S495|' + answer key) first; 120 answers: a change of the score of 2.5% "
                           "or more of G1's answers shows in the sample with probability 1 - 0.975^120 = 95.2%"},
        "checks": checks, "passed": all(checks.values())}
    return {"summary": summary, "sample": lines, "sample_bytes": sample_bytes, "mods": mods, "items": items,
            "calls": calls, "lock": lock}


def write_offline(res: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "sample.jsonl").write_bytes(res["sample_bytes"])
    (out / "offline.json").write_text(json.dumps(res["summary"], indent=1, sort_keys=False) + "\n")


def cmd_offline(a) -> int:
    res = build()
    write_offline(res, a.out)
    s = res["summary"]
    c = s["counts"]
    print(f"fingerprints: G1's code gives {s['run_sha256_rebuilt']['g1_code'][:12]} (G1 {G1_RUN_SHA[:12]}), the "
          f"working tree's {s['run_sha256_rebuilt']['now_code'][:12]} (T2 {T2_RUN_SHA[:12]}); other files the same "
          f"bytes at {G1_COMMIT}: {sum(s['other_files_same_bytes_at_g1_commit'].values())} of {len(SAME_FILES)}")
    print(f"(a) requests of G1's {s['judged_a_ok']} judged answers: {c['identical']} byte-identical under both codes, "
          f"{c['prompt_sha256_g1']} with G1's recorded prompt_sha256, G1's reply parsed to G1's scores "
          f"{c['scores_new_g1']} (new code) and {c['scores_old_g1']} (old code)")
    print(f"sample: {s['sample']['n']} answers, sha256 {s['sample']['sha256'][:12]}; wrote {a.out / 'offline.json'} "
          f"and {a.out / 'sample.jsonl'}")
    print("OFFLINE " + ("PASSED" if s["passed"] else "NOT PASSED: " + ", ".join(k for k, v in s["checks"].items()
                                                                               if not v)))
    return 0 if s["passed"] else 1


def judge_port() -> str:
    v = os.environ.get(PORT_ENV)
    if not v or not v.isdigit() or not 0 < int(v) < 65536:
        raise Refused(f"set env {PORT_ENV} to the judge server's port (1 to 65535); got {v!r}. The port is never "
                      f"given on the command line")
    return f"http://127.0.0.1:{int(v)}"


def cmd_online(a, res: dict | None = None) -> int:
    base = judge_port()
    out = a.out
    if (out / "verdict.json").exists() or (out / "online").exists():
        raise Refused(f"{out / 'verdict.json'} or {out / 'online'} exists: a verdict is a record; move it away to "
                      f"run again")
    res = res or build()
    s = res["summary"]
    if not s["passed"]:
        raise Refused("the offline proof did not pass: " + ", ".join(k for k, v in s["checks"].items() if not v))
    if not (out / "sample.jsonl").exists() or (out / "sample.jsonl").read_bytes() != res["sample_bytes"]:
        raise Refused(f"{out / 'sample.jsonl'} is missing or not this build's sample: run `offline --out {out}` first")
    new, lock = res["mods"]["new"], res["lock"]
    check = new.require_check(a.check_dir, lock, base, a.machine, a.binary)
    run_dir = out / "online"
    ns = types.SimpleNamespace(base=base, log=a.log, binary=a.binary, machine=a.machine, judge="main")
    lk, model, call, fl = new.start(ns, run_dir, "s495 online")
    rid = new.run_identity(lk, call)
    if rid != T2_RUN_SHA:
        raise Refused(f"the judge code here gives run_sha256 {rid[:12]}, not T2's {T2_RUN_SHA[:12]}")
    calls_f, rows_f = run_dir / "calls.jsonl", run_dir / "rows.jsonl"
    n = eq = ok = psha = dig = txt = 0
    diffs = []
    for i, it in enumerate(res["sample"], 1):
        x = res["items"]["new"][it["source"]][(it["run_id"], it["answer_key"])]
        row = new.judge_answer(base, call, x, calls_f, {}, "a")
        ra = row["a"]
        same = ra["status"] == "ok" and ra["scores"] == it["g1_scores"]
        p_ok, d_ok = ra.get("prompt_sha256") == it["g1_prompt_sha256"], ra.get("model_digest") == it["g1_model_digest"]
        t_ok = sha(ra.get("text") or "") == it["g1_text_sha256"]
        n, eq, ok, psha, dig, txt = (n + 1, eq + same, ok + (ra["status"] == "ok"), psha + p_ok, dig + d_ok,
                                     txt + t_ok)
        line = {"run_id": it["run_id"], "answer_key": it["answer_key"], "config": it["config"], "group": it["group"],
                "status": ra["status"], "scores": ra["scores"], "g1_scores": it["g1_scores"], "equal": same,
                "prompt_sha256_g1": p_ok, "model_digest_g1": d_ok, "identical_text": t_ok,
                "wall_s": ra.get("wall_s"), "run_sha256": rid, "at": row["at"]}
        with rows_f.open("a") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        if not (same and p_ok and d_ok):
            diffs.append(line)
        print(f"{i}/{len(res['sample'])} {it['config']:13s} {it['answer_key']:55s} {ra['status']} "
              f"{'equal' if same else 'DIFFERS'}", flush=True)
    passed = n == len(res["sample"]) > 0 and eq == n and ok == n and psha == n and dig == n
    verdict = {"_provenance": {"script": f"{SCRIPT} online", "script_sha256": FR.sha256_file(ROOT / SCRIPT),
                               "decision": "experiments/README.md D160 (5), Q16 O-a",
                               "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "offline": "offline.json",
                               "inputs": s["_provenance"]["inputs"]},
               "mode": "online", "g1_run_sha256": G1_RUN_SHA, "t2_run_sha256": T2_RUN_SHA, "run_sha256_now": rid,
               "offline_passed": s["passed"], "offline_counts": s["counts"], "offline_judged": s["judged_a_ok"],
               "sample_sha256": s["sample"]["sha256"], "n": n, "calls_ok": ok, "equal_scores": eq,
               "prompt_sha256_g1": psha, "model_digest_g1": dig, "identical_text": txt,
               "differences": diffs, "server": base,
               "model": model, "model_digest": call.digest, "lock_sha256": lk.sha256,
               "check_dir_passed": check.get("passed"), "fresh_load_ok": fl.get("ok"),
               "rows_sha256": FR.sha256_file(rows_f) if rows_f.exists() else None,
               "calls_sha256": FR.sha256_file(calls_f) if calls_f.exists() else None,
               "passed": passed}
    (out / "verdict.json").write_text(json.dumps(verdict, indent=1) + "\n")
    print(f"ONLINE: {eq} of {n} of G1's answers judged again with every score equal to G1's ({ok} calls ok, {psha} "
          f"with G1's prompt_sha256, {dig} from G1's model digest, {txt} with identical judge text); "
          f"{'PASSED' if passed else 'NOT PASSED'}; wrote {out / 'verdict.json'}", flush=True)
    return 0 if passed else 1


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="S495_t2_judge_code_proof.py", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="D160 (5): prove that T2's judge code (run_sha256 11e51fde) scores G1's answers as G1's judge "
                    "code (38ae79ab, commit d0312bc) did. `offline` needs no model; `online` judges the 120-answer "
                    "sample again on the judge port in env " + PORT_ENV + ".",
        epilog="COMMANDS " + __doc__.split("COMMANDS", 1)[1].split("THE SAMPLE", 1)[0].strip() + "\n\nTHE SAMPLE"
        + __doc__.split("THE SAMPLE", 1)[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("offline", help="no model call: fingerprints, every (a) request byte for byte, the sample")
    o.add_argument("--out", type=Path, default=OUT, help=f"where offline.json and sample.jsonl go (default {OUT.relative_to(ROOT)})")
    n = sub.add_parser("online", help=f"judge the sample again on the port in env {PORT_ENV}; writes verdict.json")
    n.add_argument("--check-dir", required=True, type=Path, help="the port's judge_passages.py check folder (107 answers)")
    n.add_argument("--log", required=True, type=Path, help="the judge server's log (the fresh load's checks read it)")
    n.add_argument("--binary", required=True, type=Path, help="the server's ollama executable, checked against LOCK [server]")
    n.add_argument("--machine", required=True, choices=["macos", "beelink"])
    n.add_argument("--out", type=Path, default=OUT, help="the folder holding offline.json and sample.jsonl")
    return p


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    return cmd_offline(a) if a.cmd == "offline" else cmd_online(a)


if __name__ == "__main__":
    sys.exit(main())
