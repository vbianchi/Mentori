#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "ragchecker==0.1.9",
#   "en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl",
# ]
# [tool.uv]
# exclude-newer = "2026-10-14T00:00:00Z"
# ///
"""Offline checks of ragchecker_run.py --order (O1 of 16 October, D80 V10; plan row K0). No server, no model call:
RAGChecker 0.1.9 and RefChecker run for real (their own prompts, batching and label merging), and
ollama_client.chat is replaced by a fake model whose checking label is a fixed function of the (claim, passage) it
reads from the prompt, so a reply returned to the wrong prompt changes a label.

    uv run --script experiments/scorers/check_ragchecker_order.py

What is checked:
  claims    unchanged: the newest committed scorer without --order and this one, both on the --arm path with the same fake model, send the
            same messages in the same order, one prompt per batch, and write the same rows; the call records differ
            only by the four fields --order adds (order, orig_index, batch, batch_len) and the header by two
  passage   the same prompts byte for byte as claims (as a multiset), sent in another order, grouped by passage
            (consecutive checking prompts of a step share their text up to '### Claim:', one group change per passage
            boundary); every label RefChecker stores equals the fake model's label for that (claim, passage); rows,
            claims, labels and metrics equal claims order's; orig_index of every call is the place RefChecker gave
            that prompt (claim index * passages + passage index on a retrieved step)
  mutants   two copies of the scorer with one line changed must each fail: replies returned in send order (M1), and
            orig_index recorded as the send position (M2)
  units     send_order on duplicate passages, a single prompt, prompts without '### Claim:'
  seed      (D83, Q144) the scorer refuses to start, with a message naming PYTHONHASHSEED and before writing anything,
            when PYTHONHASHSEED is unset or "1", or is "0" but not applied (python -E, python -R); under
            `uv run --script` it refuses without the variable and passes the gate with it; every header records
            pythonhashseed "0" and hash_randomization 0; two fresh processes under PYTHONHASHSEED=0 run RAGChecker's
            four checking steps in the same order, and six processes under seeds 1 to 6, the gate bypassed, run them
            in more than one order (so the variable is what fixes it); mutants M3 (the gate not called) and M4 (the
            interpreter flag not checked) must each fail

This check needs PYTHONHASHSEED=0 itself, since it runs the scorer's main() in its own process: started without it,
it starts itself again with it (and says so).

Fixtures: two answers, one with 5 response claims, 3 reference claims and 4 passages, one with a passage whose text
appears twice (two passages, one group).
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import types
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.runner.ollama_client import canonical_sha256  # noqa: E402

SCORER = ROOT / "experiments" / "scorers" / "ragchecker_run.py"
RESULTS: list[bool] = []
LABELS3 = ("Entailment", "Neutral", "Contradiction")
NEW_FIELDS = ("order", "orig_index", "batch", "batch_len")
REF_RE = re.compile(r"### Reference:\n(.*)\n\n### Claim:\n(.*?)\n\nYour answer", re.S)
TOK_RE = re.compile(r"\bTOK_[A-Za-z0-9]+\b")


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    return bool(ok)


def label_of(claim: str, reference: str) -> str:
    """The fake model's checking label: a fixed function of the claim and the passage it is checked against."""
    return LABELS3[hashlib.sha256(f"{claim}\x00{reference}".encode()).digest()[0] % 3]


class FakeModel:
    """Stands in for ollama_client.chat. Extraction: one triplet per distinct TOK_ word of the text to extract from
    (the part of the prompt after its last few-shot example is not needed: only the fixtures hold TOK_ words).
    Checking: label_of(claim, passage) parsed from RefChecker's own prompt."""

    def __init__(self):
        self.sent: list[list[dict]] = []

    def __call__(self, base, call, messages, **kw):
        msgs = [dict(m) for m in messages]
        self.sent.append(msgs)
        text = msgs[-1]["content"]
        m = REF_RE.search(text)
        if m:
            reply = label_of(m.group(2).strip(), m.group(1))
        else:
            toks = list(dict.fromkeys(TOK_RE.findall(text)))
            reply = "\n".join(f'("{t}", "is", "fact")' for t in toks)
        return {"status": "ok", "stop_reason": "stop", "error": None, "text": reply, "messages_sha256":
                canonical_sha256(msgs), "prompt_tokens": len(text) // 4, "output_tokens": 1, "wall_s": 0.0,
                "prompt_eval_s": 0.0, "eval_s": 0.0, "load_s": 0.0, "options_sent": {}, "model_digest": "fake"}


class FakeLock:
    sha256 = "FAKELOCK"
    d = {"scorers": {"model": "fake-model", "ragchecker_claims_per_call": 1}}

    def ollama(self, model, role=None):
        return types.SimpleNamespace(digest="fakedigest", options={"temperature": 0}, fields={"think": False},
                                     system=None)


PASSAGES_A = [f"Passage {k}: TOK_pass{k} is described here with its own words, number {k}." for k in range(4)]
PASSAGES_B = ["Passage X: the shared text.", "Passage Y: another text.", "Passage X: the shared text."]
ARM = {"per_question_results": [
    {"config": "cfg_a", "question_id": "QA", "question": "What is in the papers?",
     "contexts": [{"source": f"paper{k}.pdf", "chunk_idx": k, "text": t} for k, t in enumerate(PASSAGES_A)],
     "generation": {"answer": "The answer holds TOK_r1, TOK_r2, TOK_r3, TOK_r4 and TOK_r5."}},
    {"config": "cfg_b", "question_id": "QB", "question": "What else is in the papers?",
     "contexts": [{"source": f"p{k}.pdf", "chunk_idx": k, "text": t} for k, t in enumerate(PASSAGES_B)],
     "generation": {"answer": "Here TOK_s1 and TOK_s2 and TOK_s3."}},
]}
GT = {"questions": [{"id": "QA", "expected_answer": "The reference holds TOK_g1, TOK_g2 and TOK_g3."},
                    {"id": "QB", "expected_answer": "The reference holds TOK_h1 and TOK_h2."}]}


def load_module(name: str, source: str):
    """A copy of the scorer from source text, imported under its own name (so the old scorer, this file and the mutants coexist)."""
    path = Path(tempfile.mkdtemp()) / f"{name}.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, out: Path, order: str | None, tmp: Path):
    """The module's main() on the --arm fixture with the fake model and lock; returns (sent, rows, calls, headers)."""
    fake = FakeModel()
    mod.chat, mod.load = fake, (lambda: FakeLock())
    arm, gt = tmp / "arm.json", tmp / "gt.json"
    arm.write_text(json.dumps(ARM))
    gt.write_text(json.dumps(GT))
    argv = ["ragchecker_run.py", "--base", "http://fake", "--arm", str(arm), "--gt", str(gt), "--out", str(out)]
    if order is not None:
        argv += ["--order", order]
    saved = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = mod.main()
    finally:
        sys.argv = saved
    assert rc == 0
    rows = [json.loads(x) for x in (out / "ragchecker.jsonl").read_text().splitlines()]
    calls = [json.loads(x) for x in (out / "ragchecker_calls.jsonl").read_text().splitlines()]
    headers = [json.loads(x) for x in (out / "ragchecker_headers.jsonl").read_text().splitlines()]
    return fake.sent, rows, calls, headers


def strip_times(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in ("wall_s", "at")}


def parsed(msgs) -> tuple[str, str] | None:
    m = REF_RE.search(msgs[-1]["content"])
    return (m.group(2).strip(), m.group(1)) if m else None


def expected_labels(row: dict, passages: list[str], reference: str) -> dict:
    rc, gc = [str(c) for c in row["response_claims"]], [str(c) for c in row["gt_answer_claims"]]
    return {"retrieved2response": [[label_of(c, p) for p in passages] for c in rc],
            "retrieved2answer": [[label_of(c, p) for p in passages] for c in gc],
            "answer2response": [label_of(c, reference) for c in rc],
            "response2answer": [label_of(c, row_answer(row)) for c in gc]}


def row_answer(row: dict) -> str:
    return next(r["generation"]["answer"] for r in ARM["per_question_results"] if r["question_id"] == row["question_id"])


def labels_right(rows: list[dict]) -> tuple[bool, str]:
    """Every label RefChecker stored equals the fake model's label for its (claim, passage)."""
    bad = []
    for row in rows:
        r = next(x for x in ARM["per_question_results"] if x["question_id"] == row["question_id"])
        ref = next(q["expected_answer"] for q in GT["questions"] if q["id"] == row["question_id"])
        want = expected_labels(row, [c["text"] for c in r["contexts"]], ref)
        for k, v in want.items():
            if row.get(k) != v:
                bad.append(f"{row['question_id']} {k}")
    return not bad, ", ".join(bad[:4])


def orig_index_right(rows: list[dict], calls: list[dict], sent: list) -> tuple[bool, str]:
    """On a retrieved step (batch_len = claims x passages), orig_index = claim index * passages + passage index of the
    prompt actually sent with that record."""
    bad, n_checked = [], 0
    for rec, msgs in zip(calls, sent):
        if rec["stage"] != "check" or rec["batch_len"] == 1 and rec["order"] == "claims":
            continue
        row = next(r for r in rows if f"{r['config']}|{r['question_id']}" == rec["answer"])
        arm = next(x for x in ARM["per_question_results"] if x["question_id"] == row["question_id"])
        passages = [c["text"] for c in arm["contexts"]]
        claim, ref = parsed(msgs)
        for claims in ([str(c) for c in row["response_claims"]], [str(c) for c in row["gt_answer_claims"]]):
            if rec["batch_len"] == len(claims) * len(passages) and claim in claims and ref in passages:
                ci = claims.index(claim)
                ok = any(rec["orig_index"] == ci * len(passages) + pi for pi, p in enumerate(passages) if p == ref)
                n_checked += 1
                if not ok:
                    bad.append(f"seq {rec['seq']} orig_index {rec['orig_index']}")
                break
    return (not bad and n_checked > 0), f"{n_checked} retrieved-step calls checked" + (f"; {bad[:3]}" if bad else "")


def grouped_by_passage(calls: list[dict], sent: list) -> tuple[bool, str]:
    """Within each multi-prompt batch, prompts sharing a group key are contiguous, and the batch holds as many groups
    as distinct passages."""
    from collections import defaultdict
    by = defaultdict(list)
    for rec, msgs in zip(calls, sent):
        if rec["stage"] == "check" and rec["batch_len"] > 1:
            by[(rec["answer"], rec["batch"])].append(parsed(msgs)[1])
    if not by:
        return False, "no multi-prompt batch"
    for key, refs in by.items():
        runs = [r for i, r in enumerate(refs) if i == 0 or refs[i - 1] != r]
        if len(runs) != len(set(refs)):
            return False, f"{key}: {len(runs)} runs for {len(set(refs))} passages"
    return True, f"{len(by)} batches"


def before_order() -> tuple[str, str]:
    """(commit, source) of the newest committed ragchecker_run.py without --order: the code claims order must equal."""
    rel = str(SCORER.relative_to(ROOT))
    commits = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H", "--", rel], capture_output=True, text=True,
                             check=True).stdout.split()
    for c in commits:
        src = subprocess.run(["git", "-C", str(ROOT), "show", f"{c}:{rel}"], capture_output=True, text=True,
                             check=True).stdout
        if '"--order"' not in src:
            return c, src
    raise SystemExit("no committed ragchecker_run.py without --order")


SEED_FIELDS = ("pythonhashseed", "hash_randomization")
STEPS = ("answer2response", "response2answer", "retrieved2response", "retrieved2answer")


def seed_env(value: str | None) -> dict:
    """This process's environment with PYTHONHASHSEED set to value, or removed (None); ROOT on PYTHONPATH, so a mutant
    copy of the scorer outside the repository imports the repository's experiments package."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONHASHSEED"}
    if value is not None:
        env["PYTHONHASHSEED"] = value
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def scorer_argv(out: Path) -> list[str]:
    """Arguments under which a scorer that passes the gate stops at once on the missing --gt, never at a model call
    (and the base is a closed port)."""
    return ["--base", "http://127.0.0.1:9", "--arm", str(out.parent / "no_arm.json"),
            "--gt", str(out.parent / "no_gt.json"), "--out", str(out)]


def run_scorer(cmd: list[str], seed: str | None, out: Path) -> tuple[int, str, str]:
    """(return code, stderr, its last line) of the command given scorer_argv(out), under PYTHONHASHSEED=seed."""
    out.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(cmd + scorer_argv(out), env=seed_env(seed), capture_output=True, text=True, cwd=out.parent)
    return p.returncode, p.stderr, (p.stderr.strip().splitlines() or [""])[-1]


def refused(cmd: list[str], seed: str | None, out: Path) -> tuple[bool, str]:
    """The command exits non-zero with the REFUSED message naming PYTHONHASHSEED and creates no --out directory."""
    rc, _, tail = run_scorer(cmd, seed, out)
    return rc != 0 and tail.startswith("REFUSED: PYTHONHASHSEED") and not out.exists(), f"rc {rc}: {tail[:110]}"


def passes_gate(cmd: list[str], seed: str | None, out: Path) -> tuple[bool, str]:
    """The command gets past the gate: no REFUSED, and it stops on the missing --gt file."""
    rc, err, tail = run_scorer(cmd, seed, out)
    return "REFUSED" not in err and "FileNotFoundError" in tail and "no_gt.json" in tail, f"rc {rc}: {tail[:110]}"


def step_of(msgs: list[dict], question_id: str) -> str:
    """RAGChecker's checking step of one checking prompt, from what it checks against what (evaluator.check_claims):
    answer2response, response claims against the reference; response2answer, reference claims against the response;
    retrieved2response and retrieved2answer, response or reference claims against a passage."""
    claim, ref = parsed(msgs)
    answer = next(r["generation"]["answer"] for r in ARM["per_question_results"] if r["question_id"] == question_id)
    gt = next(q["expected_answer"] for q in GT["questions"] if q["id"] == question_id)
    from_response = bool(set(TOK_RE.findall(claim)) & set(TOK_RE.findall(answer)))
    if ref.strip() == gt:
        return "answer2response"
    if ref.strip() == answer:
        return "response2answer"
    return "retrieved2response" if from_response else "retrieved2answer"


def steps_seen(calls: list[dict], sent: list) -> dict:
    """Per answer, the checking steps in the order their first call was sent."""
    seen: dict = {}
    for rec, msgs in zip(calls, sent):
        if rec["stage"] == "check":
            q = rec["answer"].split("|", 1)[1]
            st = step_of(msgs, q)
            if st not in seen.setdefault(rec["answer"], []):
                seen[rec["answer"]].append(st)
    return seen


def child_steps(seed: str, gate: bool) -> dict:
    """A fresh process under PYTHONHASHSEED=seed scores the fixture in the claims order (fake model) and returns the
    order of its checking steps per answer; gate=False replaces the scorer's gate by the state it records, to show what
    an unfixed seed does."""
    cmd = [sys.executable, str(Path(__file__).resolve()), "--child-steps"] + ([] if gate else ["--no-gate"])
    p = subprocess.run(cmd, env=seed_env(seed), capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"child under PYTHONHASHSEED={seed} failed: {p.stderr.strip()[-300:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def child_main(gate: bool) -> int:
    new = load_module("rc_child", SCORER.read_text())
    if not gate:
        new.require_hash_seed = new.hash_seed_state
    with tempfile.TemporaryDirectory() as td:
        sent, _, calls, _ = run(new, Path(td) / "out", "claims", Path(td))
    print(json.dumps(steps_seen(calls, sent)))
    return 0


def main() -> int:
    if "--child-steps" in sys.argv:
        return child_main(gate="--no-gate" not in sys.argv)
    if os.environ.get("PYTHONHASHSEED") != "0" or sys.flags.hash_randomization != 0:
        print("started without PYTHONHASHSEED=0: starting again with it (the scorer's main() runs in this process)",
              flush=True)
        env = {**os.environ, "PYTHONHASHSEED": "0"}
        os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]], env)
    cur = SCORER.read_text()
    base_commit, head = before_order()
    print(f"baseline: ragchecker_run.py at {base_commit[:10]}, the newest commit of it without --order")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        new = load_module("rc_new", cur)

        # ---- units
        so = new.send_order
        p = lambda ref, c: f"head\n### Reference:\n{ref}\n\n### Claim:\n{c}\n\nYour answer"   # noqa: E731
        batch = [p(r, c) for c in ("c0", "c1") for r in ("X", "Y", "X")]
        check("send_order passage: duplicate passage texts form one group, stable inside it",
              so(batch, "passage") == [0, 2, 3, 5, 1, 4], str(so(batch, "passage")))
        check("send_order claims: RefChecker's own order", so(batch, "claims") == list(range(6)))
        check("send_order: a single prompt and prompts without '### Claim:' keep their order",
              so(["a"], "passage") == [0] and so(["b", "a", "b"], "passage") == [0, 2, 1]
              and so(["x1", "x2"], "passage") == [0, 1])
        check("batch_size_checker: 1 for claims, one batch per step for passage",
              new.batch_size_checker("claims") == 1 and new.batch_size_checker("passage") >= 10**6)

        # ---- claims: the scorer before --order and this file
        old = load_module("rc_head", head)
        s_old, r_old, c_old, h_old = run(old, tmp / "head", None, tmp)
        s_cl, r_cl, c_cl, h_cl = run(new, tmp / "claims", "claims", tmp)
        s_def, r_def, _, _ = run(new, tmp / "default", None, tmp)
        check("claims: the scorer before --order and this one send the same messages in the same order",
              s_old == s_cl and len(s_cl) > 0, f"{len(s_cl)} calls")
        check("claims is the default", s_def == s_cl and [strip_times(r) for r in r_def] == [strip_times(r) for r in r_cl])
        check("claims: every batch holds one prompt (batch_size_checker 1, as before)",
              all(r["batch_len"] == 1 and r["orig_index"] == 0 and r["order"] == "claims" for r in c_cl))
        check("claims: rows equal the old scorer's (times aside)",
              [strip_times(r) for r in r_old] == [strip_times(r) for r in r_cl])
        drop = lambda r: {k: v for k, v in r.items() if k not in NEW_FIELDS}                    # noqa: E731
        check("claims: call records equal the old scorer's but for order, orig_index, batch, batch_len",
              [drop(r) for r in c_cl] == c_old and all(set(r) - set(o) == set(NEW_FIELDS) for r, o in zip(c_cl, c_old)))
        hd = lambda h: {k: v for k, v in h.items() if k != "_provenance"}                         # noqa: E731
        added = ("order", "batch_size_checker") + SEED_FIELDS
        check("claims: header equals the old scorer's but for order, batch_size_checker, pythonhashseed, "
              "hash_randomization",
              [{k: v for k, v in hd(h).items() if k not in added} for h in h_cl]
              == [hd(h) for h in h_old] and h_cl[0]["order"] == "claims" and h_cl[0]["batch_size_checker"] == 1)
        ok, why = labels_right(r_cl)
        check("claims: every stored label is the fake model's label for its (claim, passage)", ok, why)

        # ---- passage
        s_pa, r_pa, c_pa, h_pa = run(new, tmp / "passage", "passage", tmp)
        ms = lambda s: Counter(json.dumps(m, sort_keys=True) for m in s)                          # noqa: E731
        check("passage: the same prompts byte for byte as claims (multiset)", ms(s_pa) == ms(s_cl), f"{len(s_pa)} calls")
        check("passage: the send order differs from claims", s_pa != s_cl)
        ok, why = grouped_by_passage(c_pa, s_pa)
        check("passage: each step's prompts are sent grouped by passage", ok, why)
        ok, why = labels_right(r_pa)
        check("passage: every stored label is the fake model's label for its (claim, passage)", ok, why)
        check("passage: rows (claims, labels, metrics, status) equal claims order's",
              [strip_times(r) for r in r_pa] == [strip_times(r) for r in r_cl])
        ok, why = orig_index_right(r_pa, c_pa, s_pa)
        check("passage: orig_index is the place RefChecker gave the prompt sent", ok, why)
        check("passage: header records order passage and one batch per step",
              h_pa[0]["order"] == "passage" and h_pa[0]["batch_size_checker"] == new.ONE_BATCH)
        check("passage: records carry order passage", all(r["order"] == "passage" for r in c_pa))

        # ---- seed (D83, Q144)
        check("seed: every header records pythonhashseed '0' and hash_randomization 0",
              all(h.get("pythonhashseed") == "0" and h.get("hash_randomization") == 0 for h in h_cl + h_pa),
              f"{len(h_cl) + len(h_pa)} headers")
        for name, env, flags in (("PYTHONHASHSEED unset", None, []), ("PYTHONHASHSEED=1", "1", []),
                                 ("PYTHONHASHSEED=0 under python -E", "0", ["-E"]),
                                 ("PYTHONHASHSEED=0 under python -R", "0", ["-R"])):
            ok, why = refused([sys.executable, *flags, str(SCORER)], env, tmp / f"refuse_{len(RESULTS)}")
            check(f"seed: refused with {name}, before writing anything", ok, why)
        ok, why = refused(["uv", "run", "--script", str(SCORER)], None, tmp / "refuse_uv")
        check("seed: refused under uv run --script without PYTHONHASHSEED", ok, why)
        ok, why = passes_gate(["uv", "run", "--script", str(SCORER)], "0", tmp / "gate_uv")
        check("seed: passes the gate under PYTHONHASHSEED=0 uv run --script (then stops on the missing --gt)", ok, why)
        seed0 = [child_steps("0", gate=True) for _ in range(2)]
        check("seed: two processes under PYTHONHASHSEED=0 run the four checking steps in one order, on both answers",
              seed0[0] == seed0[1] and all(len(v) == 4 for v in seed0[0].values()) and len(seed0[0]) == 2,
              f"{next(iter(seed0[0].values()))}")
        others = [child_steps(str(k), gate=False) for k in range(1, 7)]
        check("seed: under PYTHONHASHSEED 1 to 6, the gate bypassed, the steps run in more than one order",
              all(all(len(v) == 4 for v in o.values()) for o in others)
              and len({json.dumps(o, sort_keys=True) for o in others}) > 1,
              f"{len({json.dumps(o, sort_keys=True) for o in others})} distinct orders in 6 processes")

        # ---- mutants: each must fail at least one of the checks above
        def mutant(name, old_line, new_line):
            assert cur.count(old_line) == 1, f"mutation site not found once: {old_line!r}"
            mod = load_module(name, cur.replace(old_line, new_line))
            s, r, c, _ = run(mod, tmp / name, "passage", tmp)
            caught = [not labels_right(r)[0], [strip_times(x) for x in r] != [strip_times(x) for x in r_cl],
                      not orig_index_right(r, c, s)[0]]
            return any(caught), caught

        caught, why = mutant("rc_m1", "            texts[i] = given\n",
                             "            texts[texts.index(None)] = given\n")
        check("mutant M1 (replies returned in send order) is caught", caught, f"labels, rows, orig_index: {why}")
        caught, why = mutant("rc_m2", "order=order, orig_index=i,",
                             "order=order, orig_index=send_order(prompts, order).index(i),")
        check("mutant M2 (orig_index recorded as the send position) is caught", caught, f"labels, rows, orig_index: {why}")

        def seed_mutant(name, old_line, new_line, env, flags):
            assert cur.count(old_line) == 1, f"mutation site not found once: {old_line!r}"
            path = tmp / name / "ragchecker_run.py"
            path.parent.mkdir()
            path.write_text(cur.replace(old_line, new_line))
            return passes_gate([sys.executable, *flags, str(path)], env, tmp / name / "out")

        # caught: the mutant gets past the gate where the scorer is refused (the copy imports the repository's
        # experiments package through PYTHONPATH, so -R, which keeps PYTHONPATH, stands for the flag case here)
        ok, why = seed_mutant("rc_m3", "    require_hash_seed()                                  # D83",
                              "    pass                                                 # D83", None, [])
        check("mutant M3 (the gate not called) is caught: it runs on with PYTHONHASHSEED unset", ok, why)
        ok, why = seed_mutant("rc_m4", ' or s["hash_randomization"] != 0:', ":", "0", ["-R"])
        check("mutant M4 (only the variable checked, not the interpreter's flag) is caught: it runs on under "
              "PYTHONHASHSEED=0 python -R", ok, why)

    n = sum(RESULTS)
    print(f"check_ragchecker_order: {n}/{len(RESULTS)} passed")
    return 0 if n == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
