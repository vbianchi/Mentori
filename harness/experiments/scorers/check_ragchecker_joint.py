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
"""Offline checks of ragchecker_run.py's guarded joint check (D103; JOINT in its docstring). No server, no model call:
RAGChecker 0.1.9 and RefChecker run for real, and ollama_client.chat is the fake model of check_ragchecker_order.py
(a checking label that is a fixed function of the (claim, passage) it reads), extended to answer joint prompts: it
reads each numbered claim and the passage from the joint prompt and replies in a chosen way (right, numbered out of
order, a label missing, an extra number, a claim twice, a line of prose, inside a code fence).

    uv run --script experiments/scorers/check_ragchecker_joint.py

What is checked:
  one claim   at one claim per call (the lock's value) the scorer sends what the newest committed scorer without the
              joint check sends, byte for byte and in the same order, in both --order claims and --order passage, and
              writes the same rows, call records and headers (times aside)
  joint       at 5 claims per call (--joint-test --order passage): every label RefChecker stores is the fake model's
              label for its (claim, passage); rows (claims, labels, metrics, status) equal the one-claim rows; fewer
              checking calls; every prompt's code in check_modes; a reply numbered out of order is read by number
  guard       every joint reply that does not give exactly one valid label per numbered claim is rejected, and each of
              its claims is asked alone with RefChecker's own one-claim prompt (so no label is padded, cut or matched by
              position), with the reason in the call records; the labels stay right
  refusals    another claims-per-call than the lock's without --joint-test, --joint-test with --order claims or with
              one claim, and RefChecker's own joint check (make_evaluator joint=True), each refused before a write
  units       parse_joint and split_single (a prompt rebuilt byte for byte; a passage that holds '### Claim:')
  mutants     each guard branch: padding a missing label, a claim labelled twice, an extra number, a line of prose,
              labels matched by position, a rejected chunk not asked again, the joint path reached at one claim, and
              RefChecker's own joint check let through; each must fail its case

Needs PYTHONHASHSEED=0 (the scorer's main() runs in this process): started without it, it starts itself again with it.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCORER = ROOT / "experiments" / "scorers" / "ragchecker_run.py"
ORDER = ROOT / "experiments" / "scorers" / "check_ragchecker_order.py"
RESULTS: list[bool] = []
JOINT_RE = re.compile(r"### Reference:\n(.*)\n\n### Claims:\n(.*?)\n\nThere are (\d+) claims", re.S)


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))
    return bool(ok)


def load(name: str, path_or_source) -> object:
    src = path_or_source.read_text() if isinstance(path_or_source, Path) else path_or_source
    path = Path(tempfile.mkdtemp()) / f"{name}.py"
    path.write_text(src)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


O = load("rc_order_check", ORDER)          # the order check's fixtures and fake model (its main() is not run)
OTHER = {"Entailment": "Contradiction", "Neutral": "Entailment", "Contradiction": "Neutral"}


class JointFake(O.FakeModel):
    """The order check's fake model, also answering joint prompts. modes: how each joint call in turn is answered
    (cycled): good, swap (right labels, lines in reverse order), missing (the last line left out), extra (a number past
    the last), dup (claim 1 labelled again, wrongly, at the end), prose (a line of prose first), fence (inside ```)."""

    def __init__(self, modes=("good",)):
        super().__init__()
        self.modes, self.joint, self.bad = list(modes), 0, 0

    def __call__(self, base, call, messages, **kw):
        text = messages[-1]["content"]
        m = JOINT_RE.search(text)
        if not m:
            return super().__call__(base, call, messages, **kw)
        self.sent.append([dict(x) for x in messages])
        ref, k = m.group(1), int(m.group(3))
        claims = [re.sub(r"^\d+\. ", "", ln).strip() for ln in m.group(2).split("\n")]
        assert len(claims) == k, (k, claims)
        labels = [O.label_of(c, ref) for c in claims]
        mode = self.modes[self.joint % len(self.modes)]
        self.joint += 1
        self.bad += mode not in ("good", "swap", "fence")
        lines = [f"{n}: {lab}" for n, lab in enumerate(labels, 1)]
        if mode == "swap":
            lines = lines[::-1]
        elif mode == "missing":
            lines = lines[:-1]
        elif mode == "extra":
            lines.append(f"{k + 1}: Contradiction")
        elif mode == "dup":
            lines.append(f"1: {OTHER[labels[0]]}")
        elif mode == "prose":
            lines = ["Here are the labels:"] + lines
        elif mode == "fence":
            lines = ["```"] + lines + ["```"]
        reply = "\n".join(lines)
        return {"status": "ok", "stop_reason": "stop", "error": None, "text": reply,
                "messages_sha256": O.canonical_sha256(messages), "prompt_tokens": len(text) // 4, "output_tokens": k,
                "wall_s": 0.0, "prompt_eval_s": 0.0, "eval_s": 0.0, "load_s": 0.0, "options_sent": {},
                "model_digest": "fake"}


def run(mod, out: Path, tmp: Path, args: list[str], fake=None):
    """main() of a scorer module on the order check's --arm fixture with a fake model; (rc, sent, rows, calls,
    headers, stdout)."""
    fake = fake or JointFake()
    mod.chat, mod.load = fake, (lambda: O.FakeLock())
    arm, gt = tmp / "arm.json", tmp / "gt.json"
    arm.write_text(json.dumps(O.ARM))
    gt.write_text(json.dumps(O.GT))
    argv = ["ragchecker_run.py", "--base", "http://fake", "--arm", str(arm), "--gt", str(gt), "--out", str(out), *args]
    saved, buf = sys.argv, io.StringIO()
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            try:
                rc = mod.main()
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 1
                print(e.code)
    finally:
        sys.argv = saved
    read = lambda f: [json.loads(x) for x in (out / f).read_text().splitlines()] if (out / f).exists() else []  # noqa: E731
    return rc, fake.sent, read("ragchecker.jsonl"), read("ragchecker_calls.jsonl"), read("ragchecker_headers.jsonl"), buf.getvalue()


def before_joint() -> tuple[str, str]:
    """(commit, source) of the newest committed ragchecker_run.py without the joint check: what one claim per call
    must equal."""
    rel = str(SCORER.relative_to(ROOT))
    commits = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H", "--", rel], capture_output=True, text=True,
                             check=True).stdout.split()
    for c in commits:
        src = subprocess.run(["git", "-C", str(ROOT), "show", f"{c}:{rel}"], capture_output=True, text=True,
                             check=True).stdout
        if "claims_per_call(" not in src:
            return c, src
    raise SystemExit("no committed ragchecker_run.py without the joint check")


ROW_JOINT = ("claims_per_call", "check_modes", "checked_jointly", "checked_alone", "checked_alone_after_rejection",
             "not_rebuilt", "joint_calls", "joint_rejected")
SCORED = ("response_claims", "gt_answer_claims", "answer2response", "response2answer", "retrieved2response",
          "retrieved2answer", "metrics", "status")


def scored(rows: list[dict]) -> list[dict]:
    return [{k: r.get(k) for k in ("question_id", "config", *SCORED)} for r in rows]


def main() -> int:
    if os.environ.get("PYTHONHASHSEED") != "0" or sys.flags.hash_randomization != 0:
        print("started without PYTHONHASHSEED=0: starting again with it", flush=True)
        os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                  {**os.environ, "PYTHONHASHSEED": "0"})
    cur = SCORER.read_text()
    base_commit, base_src = before_joint()
    print(f"baseline: ragchecker_run.py at {base_commit[:10]}, the newest commit of it without the joint check")
    new = load("rc_joint_new", SCORER)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # ---- one claim per call: what is sent, rows, calls and headers equal the committed scorer's
        old = load("rc_joint_old", base_src)
        hd = lambda hs: [{k: v for k, v in h.items() if k != "_provenance"} for h in hs]            # noqa: E731
        st = lambda rs: [O.strip_times(r) for r in rs]                                              # noqa: E731

        def one_claim_equal(mod) -> bool:
            ok = True
            for order in ("claims", "passage"):
                ro = run(old, tmp / f"old_{order}_{len(RESULTS)}", tmp, ["--order", order])
                rn = run(mod, tmp / f"new_{order}_{len(RESULTS)}", tmp, ["--order", order])
                ok &= (ro[0] == rn[0] == 0 and ro[1] == rn[1] and len(rn[1]) > 0 and st(ro[2]) == st(rn[2])
                       and ro[3] == rn[3] and hd(ro[4]) == hd(rn[4]))
            return ok
        check(f"one claim per call: the same messages in the same order, the same rows, call records and headers as the "
              f"scorer at {base_commit[:10]}, in --order claims and --order passage", one_claim_equal(new))
        r1 = run(new, tmp / "one_passage", tmp, ["--order", "passage"])
        check("one claim per call: no row, call record or header carries a joint field",
              not any(k in r for r in r1[2] for k in ROW_JOINT) and not any("claims_per_call" in c for c in r1[3])
              and not any("guarded_joint" in h for h in r1[4]))
        r1c = run(new, tmp / "one_cpc1", tmp, ["--order", "passage", "--claims-per-call", "1"])
        check("--claims-per-call 1 (the lock's value) is the one-claim path: the same messages and rows",
              r1c[0] == 0 and r1c[1] == r1[1] and st(r1c[2]) == st(r1[2]))

        # ---- joint, right replies
        def joint(mod, modes, name):
            fake = JointFake(modes)
            res = run(mod, tmp / name, tmp, ["--order", "passage", "--claims-per-call", "5", "--joint-test"], fake)
            return res, fake
        (rc, sent, rows, calls, heads, out), fake = joint(new, ("good",), "joint_good")
        ok, why = O.labels_right(rows)
        check("joint (5 per call): every stored label is the fake model's label for its (claim, passage)", rc == 0 and ok,
              f"rc {rc} {why} {out[-200:]}")
        check("joint: claims, labels, metrics and status equal the one-claim rows", scored(rows) == scored(r1[2]))
        n_one = sum(r["checking_calls"] for r in r1[2])
        n_joint = sum(r["checking_calls"] for r in rows)
        check("joint: fewer checking calls than one claim per call", 0 < n_joint < n_one, f"{n_joint} against {n_one}")
        codes = [m for r in rows for b in r["check_modes"] for m in b["modes"]]
        check("joint: every checking prompt has a code (J, A); the counts add up; no rejection; header and records say so",
              codes and set(c[0] for c in codes) <= {"J", "A"} and all(
                  r["checked_jointly"] + r["checked_alone"] == sum(len(b["modes"]) for b in r["check_modes"])
                  and r["joint_rejected"] == 0 for r in rows)
              and heads[-1].get("claims_per_call") == 5 and heads[-1].get("guarded_joint") is True
              and heads[-1].get("joint_test") is True and heads[-1].get("joint_check") is False
              and any(c["stage"] == "check_joint" and c["joint"]["accepted"] for c in calls))
        check("joint: no joint call holds more than 5 claims; each holds claims of one passage",
              all(c["joint"]["n"] <= 5 and len(c["orig_index"]) == c["joint"]["n"] for c in calls if c["stage"] == "check_joint"))
        (rc, sent, rows_s, calls_s, _, _), _ = joint(new, ("swap",), "joint_swap")
        ok, why = O.labels_right(rows_s)
        check("joint: replies numbered in reverse order are read by number (labels right, none rejected)",
              rc == 0 and ok and sum(r["joint_rejected"] for r in rows_s) == 0, why)
        (rc, _, rows_f, _, _, _), _ = joint(new, ("fence",), "joint_fence")
        check("joint: a reply inside a code fence is read (labels right, none rejected)",
              rc == 0 and O.labels_right(rows_f)[0] and sum(r["joint_rejected"] for r in rows_f) == 0)

        # ---- the guard: every bad reply rejected, its claims asked alone, labels right
        BAD = ("missing", "extra", "dup", "prose")

        def guard_case(mod, name):
            (rc, sent, rows, calls, _, _), fake = joint(mod, ("good",) + BAD, name)
            rej = [c for c in calls if c["stage"] == "check_joint" and not c["joint"]["accepted"]]
            alone = [c for c in calls if str(c.get("single_why", "")).startswith("joint call ")]
            ok = (rc == 0 and O.labels_right(rows)[0] and fake.bad > 0 and len(rej) == fake.bad
                  and sum(r["joint_rejected"] for r in rows) == fake.bad
                  and len(alone) == sum(c["joint"]["n"] for c in rej)
                  and sum(r["checked_alone_after_rejection"] for r in rows) == len(alone)
                  and scored(rows) == scored(r1[2]))
            return ok, f"rc {rc}, {fake.bad} bad replies, {len(rej)} rejected, {len(alone)} asked alone"
        ok, why = guard_case(new, "joint_guard")
        check("guard: each bad joint reply (a label missing, an extra number, a claim twice, prose) is rejected and "
              "each of its claims asked alone; labels and rows equal the one-claim rows", ok, why)
        (_, _, _, calls_g, _, _), _ = joint(new, ("missing",), "joint_missing")
        whys = {c["joint"]["why"] for c in calls_g if c["stage"] == "check_joint"}
        check("guard: the reason is recorded on the joint call and on each claim asked alone",
              any(w and w.startswith("no label for claim") for w in whys)
              and all(c.get("single_why", "").startswith("joint call ") for c in calls_g
                      if c["stage"] == "check" and "single_why" in c and "rejected" in c["single_why"]))
        alone_prompts = {json.dumps(m) for c, m in zip(calls_g, joint(new, ("missing",), "joint_missing2")[0][1])
                         if c["stage"] == "check"}
        one_prompts = {json.dumps(m) for c, m in zip(r1[3], r1[1]) if c["stage"] == "check"}
        check("guard: a claim asked alone is sent RefChecker's own one-claim prompt, byte for byte",
              alone_prompts and alone_prompts <= one_prompts, f"{len(alone_prompts - one_prompts)} not in the one-claim set")

        # ---- refusals (before any write)
        def refused(args, name):
            rc, _, _, _, _, out = run(new, tmp / name, tmp, args)
            return rc != 0 and "REFUSED" in out and not (tmp / name).exists()
        check("refused: --claims-per-call 5 without --joint-test", refused(["--order", "passage", "--claims-per-call", "5"], "rf1"))
        check("refused: --joint-test with --order claims", refused(["--claims-per-call", "5", "--joint-test"], "rf2"))
        check("refused: --joint-test with one claim per call", refused(["--order", "passage", "--joint-test"], "rf3"))
        check("refused: --claims-per-call 0", refused(["--order", "passage", "--claims-per-call", "0", "--joint-test"], "rf4"))

        def rc_joint_refused(mod):
            try:
                mod.make_evaluator(lambda **k: k, "m", "claims", True, None)
            except SystemExit as e:
                return "REFUSED" in str(e)
            return False
        check("refused: RefChecker's own joint check (make_evaluator joint=True)", rc_joint_refused(new))

        # ---- units
        pj = new.parse_joint
        check("parse_joint: right, any case, '.' or ')' after the number, bold, a final full stop",
              pj("1: Entailment\n2: neutral\n3. CONTRADICTION\n**4) Neutral.**", 4)[0]
              == ["Entailment", "Neutral", "Contradiction", "Neutral"])
        check("parse_joint: a label missing, an extra number, a claim twice, prose, a label word not in the three, "
              "an empty reply: each rejected with a reason",
              all(pj(t, 2) == (None, pj(t, 2)[1]) and pj(t, 2)[1] for t in
                  ("1: Entailment", "1: Entailment\n2: Neutral\n3: Neutral", "1: Entailment\n1: Neutral\n2: Neutral",
                   "Labels:\n1: Entailment\n2: Neutral", "1: Entailment\n2: Supported", "")))
        from refchecker.checker.checker_prompts import LLM_CHECKING_PROMPT_Q
        p = LLM_CHECKING_PROMPT_Q.format(question="Q?", reference="a passage\n\n### Claim:\nnot a claim", claim="['a', 'b', 'c']")
        check("split_single: a one-claim prompt rebuilds byte for byte, even when its passage holds '### Claim:'",
              new.split_single(p) == ("q", "Q?", "a passage\n\n### Claim:\nnot a claim", "['a', 'b', 'c']"))
        check("split_single: a prompt that is not RefChecker's template does not rebuild (None)",
              new.split_single(p.replace("only a single word", "one word")) is None)

        # ---- mutants
        def mutant(name, old_s, new_s):
            assert cur.count(old_s) == 1, f"mutation site not found once: {old_s[:70]!r}"
            return load(name, cur.replace(old_s, new_s))

        def caught(name, ok_case):
            check(f"mutant ({name}): its case fails on it", not ok_case)

        pad = mutant("m_pad", '''    if missing:
        return None, f"no label for claim {', '.join(map(str, missing))}"
    return [got[n] for n in range(1, k + 1)], None''', '''    return [got.get(n, "Neutral") for n in range(1, k + 1)], None''')
        caught("a missing label padded with Neutral, as RefChecker's joint check", guard_case(pad, "m_pad")[0])
        dup = mutant("m_dup", "        if n in got:\n", "        if False:\n")
        caught("a claim labelled twice accepted", guard_case(dup, "m_dup")[0])
        extra = mutant("m_extra", "        if not 1 <= n <= k:\n", "        if False:\n")
        caught("a number past the last accepted", guard_case(extra, "m_extra")[0])
        prose = mutant("m_prose", '''        if not m:
            return None, f"a line that is not''', '''        if not m:
            continue
            return None, f"a line that is not''')
        caught("a line of prose accepted", guard_case(prose, "m_prose")[0])
        pos = mutant("m_pos", "        got[n] = m[2].title()\n", "        got[len(got) + 1] = m[2].title()\n")
        caught("labels matched by position, not by number (the swap case: labels right, none rejected)",
               (lambda r: r[0][0] == 0 and O.labels_right(r[0][2])[0]
                and sum(x["joint_rejected"] for x in r[0][2]) == 0)(joint(pos, ("swap",), "m_pos")))
        noask = mutant("m_noask", '''                    back[i], modes[i] = one(prompts, i, f"joint call {seq} rejected: {why}"), f"R{seq}"''',
                       '''                    back[i], modes[i] = "Neutral", f"R{seq}"''')
        caught("a rejected chunk's claims not asked again", guard_case(noask, "m_noask")[0])
        at1 = mutant("m_at1", "    if per_call > 1:\n        return make_joint_llm(",
                     "    if per_call >= 1:\n        return make_joint_llm(")
        caught("the joint path reached at one claim per call", one_claim_equal(at1))
        rcj = mutant("m_rcj", "    if joint:\n        raise SystemExit(\"REFUSED: RefChecker's own joint check",
                     "    if False:\n        raise SystemExit(\"REFUSED: RefChecker's own joint check")
        caught("RefChecker's own joint check let through", rc_joint_refused(rcj))

    n = sum(RESULTS)
    print(f"check_ragchecker_joint: {n}/{len(RESULTS)} passed")
    return 0 if n == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
