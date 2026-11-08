"""Checks for B4, the authors' RLM adapter (experiments/rlm_ref/adapter.py, run_rlm_ref.py, build_context.py; D73).

    uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.check_rlm_ref           # offline
    uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.check_rlm_ref --live    # + the smoke

Offline: no Google call and no key. gemini_client's HTTP layer is replaced by a fake Gemini that answers from a script
(root turns by their "Turn i/N" line, sub-calls by a marker in the prompt), and GEMINI_API_KEY is set to a fake value,
which is the value the key scan looks for. Docker must run (the model's code runs in the sandbox image, as in a real
run); every run writes into a temporary runs root.
 1 package and patches: rlms 0.1.3 installed and pinned by its wheel hash in uv.lock; dotenv disabled; the package's
   own clients refused; the container script carries the raising sub-call functions and no client timeout (and a
   different package text is refused); comms_utils waits without limit; the proxy binds 127.0.0.1 and a container
   reaches it; the sandbox's own "pip install -q dill requests" succeeds with no network.
 2 corpus: the context file loads (20 papers, both sha256s), a tampered copy is refused, the sandbox's repr forms.
 3 records: every call is one runner record with the lock's Gemini settings (no thinking setting: Google's default),
   call kind, turn, block, batch slot, cap, draw and question; root turns carry passages [] and their messages, a
   sub-call its prompt; seqs are complete; the answer record's tokens equal the records' sums.
 4 cap in prompt: each root turn's last message is "Turn i/N" for the run's cap (3 and 5).
 5 errors raised into the code (Q47): a sub-call that stops on the output limit, or fails, raises LLMQueryError
   inside the container; the model's code can catch it, an uncaught one is a traceback the next turn shows; a batch
   with one failure raises with the other responses kept; each failure is recorded with its status.
 6 the forced final answer at the cap (turn cap + 1, call forced_final, last message the package's assistant turn);
   a root call that fails ends the question as root_call_failed with its record; a root call cut by the output limit
   is recorded with status length, its text is the next turn's assistant message and the answer counts it (D75 Q48);
   a cut reply goes back as google-genai 2.30.1's response.text would give it (Q114): '' for an empty text part (the
   recorded shape of 01_sarek_CO2 d1), None for no text part, which the package's code-block search raises on.
 7 key scan: a sub-call reply holding the key stops the run (KeyLeakError, even though the model's code catches the
   error), nothing holding the key is written; the container sees no key in its environment or files.
 8 traces: the corpus is never written into a trace (repr(context) becomes a corpus reference), long strings go to
   blobs once, sub-call seqs sit under their code block.
 9 run script: guards (caps and draws per set, the depth sweep is the named set of 86 and no other count, a limit
   from 1), resume skips stored answers; the 86 ids equal the deposit's depth sweep less CD_015 and SY_010 (D75 Q50).
10 image and sandbox: the image is IMAGE_ID and any other is refused, nothing built; on b4-sandbox no laptop port
   outside the proxy range, the VM's ssh or a private address is reachable (with a control on Docker's default
   network, which reaches a loopback listener of the check's own), the internet is; the package's
   container runs there with its labels; a killed run's containers and workspaces are removed.
11 patch 7: the script runs from stdin as /workspace/_exec.py; a symlink planted there is written through by the
   package's execute_code (the control) and not by the patched one.
12 message lists as the authors' client maps them: roles to_contents refuses are sent as user turns, an empty model
   turn as an empty text part, a prompt that cannot be sent is a recorded error raised into the code.
13 Ctrl-C during a code block stops the run with nothing stored and no container left.
14 D89 (Q145 O3), D90 (Q1, Q2) and D92 (Q185, Q187, Q188), without Docker (run first, so it reports even when Docker
   is stopped): through LockedGemini and gemini_client over a fake HTTP layer, a blocked prompt, an answer blocked
   after streamed text, an empty reply with no finishReason or STOP, a recitation, three malformed shapes (no part,
   text, and the G6 shape of a '' text part beside a thought signature) and the four Q188 reasons (language, other,
   unexpected_tool_call, too_many_tool_calls) each return, nothing raised, the record keeping the status and the
   reason: a root turn gets package_text of the parts passed on (Q185: None with no text part, '' for a '' text part,
   a blocked reply None), a sub-call the record's text ('' when none); a closing call with no text part gets None and
   closing_answer gives the stored ''; a status error still raises RootCallError at the root and SubCallError in a
   sub-call; calls.sub_failed counts every returned status but the STOP empty one, as before D89; rebuild_from_closing
   (Q187) sets the stored answer from the closing call's record and refuses every answer it cannot rebuild exactly.
Live (--live): the smoke, cap 1, one question, draw --live-draw, real Gemini; then design R2 on the most recent smoke
answer that reached the cap: its forced final messages sent again as the package sends them and with the closing
message as a user turn (an answer is an ok reply with text and no code block).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import importlib.metadata
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FAKE_KEY = "AIzaFAKE-b4-check-key-0123456789abcdef"
_saved_env = {k: os.environ.get(k) for k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY")}
os.environ["GEMINI_API_KEY"] = FAKE_KEY              # offline, the scan looks for this value; no real key is read
os.environ.pop("ANTHROPIC_API_KEY", None)

from experiments.rlm_ref import adapter as ad  # noqa: E402
from experiments.rlm_ref import run_rlm_ref as runner  # noqa: E402
from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import gemini_client as gc  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return e
    except Exception as e:                          # noqa: BLE001
        return f"wrong exception {type(e).__name__}: {e}"
    return None


# ---------------------------------------------------------------- the fake Gemini

class FakeResponse:
    def __init__(self, lines):
        self.lines = lines

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        yield from self.lines


def sse(text, finish, prompt_tokens, output_tokens, thinking_tokens):
    """text: the reply's one text part, or a list of parts sent as given (a recorded shape)."""
    parts = text if isinstance(text, list) else [{"text": text}]
    chunk = {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": finish}],
             "modelVersion": "fake-gemini", "usageMetadata": {
                 "promptTokenCount": prompt_tokens, "candidatesTokenCount": output_tokens,
                 "thoughtsTokenCount": thinking_tokens,
                 "totalTokenCount": prompt_tokens + output_tokens + thinking_tokens}}
    return [f"data: {json.dumps(chunk)}\n".encode(), b"\n"]


def http_error(code):
    body = json.dumps({"error": {"code": code, "message": f"fake {code}", "status": "INVALID_ARGUMENT"}})
    return urllib.error.HTTPError(gc.API, code, "err", {}, io.BytesIO(body.encode()))


class FakeGemini:
    """root(turn, cap, forced) -> reply text, an int (an HTTP error) or (text or a list of parts, finishReason);
    sub-calls answer by marker."""

    def __init__(self, root):
        self.root, self.requests, self.lock = root, [], threading.Lock()

    def __call__(self, req, timeout=None):
        payload = json.loads(req.data)
        with self.lock:
            self.requests.append(payload)
        if "systemInstruction" in payload and len(payload["contents"]) > 1:
            last = payload["contents"][-1]
            text = last["parts"][0].get("text", "")
            forced = last["role"] == "model"
            turn = cap = None
            for c in reversed(payload["contents"]):
                t = c["parts"][0].get("text", "") if c["role"] == "user" else ""
                if "Turn " in t:
                    num = t.rsplit("Turn ", 1)[1].split(":")[0]
                    turn, cap = (int(x) for x in num.split("/"))
                    break
            reply = self.root(turn, cap, forced, text)
            if isinstance(reply, int):
                raise http_error(reply)
            if isinstance(reply, tuple):
                return FakeResponse(sse(reply[0], reply[1], 1000, 65000, 536))
            return FakeResponse(sse(reply, "STOP", 1000, 100, 50))
        prompt = payload["contents"][0]["parts"][0]["text"]
        if "SUB-LENGTH" in prompt:
            return FakeResponse(sse("a long partial answer", "MAX_TOKENS", 30, 65000, 536))
        if "SUB-ERROR" in prompt:
            raise http_error(400)
        if "SUB-KEY" in prompt:
            return FakeResponse(sse(f"here it is: {FAKE_KEY}", "STOP", 30, 10, 2))
        if "SUB-EMPTY" in prompt:
            return FakeResponse(sse("", "STOP", 30, 0, 2))
        return FakeResponse(sse("ok:" + prompt.split("SUB-OK", 1)[-1].strip(), "STOP", 30, 10, 2))


@contextlib.contextmanager
def fake_gemini(root):
    fake = FakeGemini(root)
    saved = (gc._open, gc._arm, gc._key, gc._sleep)
    gc._open, gc._arm, gc._key, gc._sleep = fake, (lambda r, s: None), (lambda: FAKE_KEY), (lambda s: None)
    try:
        yield fake
    finally:
        gc._open, gc._arm, gc._key, gc._sleep = saved


def repl(code: str) -> str:
    return f"Planning.\n```repl\n{code}\n```"


QUESTION = {"id": "01_sarek_FR1", "question": "Which workflow manager does Sarek use?"}


def run_one(tmp: Path, name: str, cap: int, root, draw: int = 1, question=QUESTION):
    """One question through ad.run_question in its own run under tmp; returns (record or exception, sink, fake)."""
    rid = ex.run_id("b4check", f"cap{cap}", name)
    sink = ex.sink(rid, root=tmp)
    ctx = ex.context("b4check", f"cap{cap}", question["id"], draw, {"rlm_ref": ad.IDENT},
                     base_url=runner.BASE_URL, run=rid, sink=sink, judge=False)
    with fake_gemini(root) as fake:
        with rc.run(ctx):
            try:
                rec = ad.run_question(ctx, question, cap, BUNDLE, IMAGE, "check", f"cap{cap}",
                                      ex.answer_key(f"cap{cap}", question["id"], draw))
            except Exception as e:                  # noqa: BLE001
                rec = e
    return rec, sink, fake


def lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def main() -> int:
    global BUNDLE, IMAGE
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the temporary runs root")
    ap.add_argument("--live-draw", type=int, default=1, help="the smoke's draw (another draw is another answer key)")
    args = ap.parse_args()
    global LIVE_DRAW
    LIVE_DRAW = args.live_draw
    tmp = Path(tempfile.mkdtemp(prefix="check_rlm_ref_", dir=ROOT / "experiments" / "rlm_ref")).resolve()
    try:
        d89(tmp)
        if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
            print("FAIL Docker is not running (colima start); sections 1 to 13 not run")
            return 1
        offline(tmp)
        if args.live:
            live()
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print(f"kept {tmp}")
    n_ok = sum(results)
    print(f"\n{n_ok}/{len(results)} checks passed")
    return 0 if n_ok == len(results) else 1


def d89(tmp: Path) -> None:
    """14. D89 (Q145 O3) through LockedGemini, no Docker: what goes back to the package, what the record keeps."""
    usage = {"promptTokenCount": 9533, "totalTokenCount": 9533}        # the recorded 19_hpai shape: prompt = total
    part = {"content": {"role": "model", "parts": [{"text": "half an answer"}]}}
    sig = {"text": "", "thoughtSignature": "c2ln"}                  # the recorded G6 shape: '' beside a signature
    end = lambda reason, parts=(): {"candidates": [{"content": {"role": "model", "parts": list(parts)},  # noqa: E731
                                                     "finishReason": reason}]}
    # name: (chunks, what a root turn gets, what a sub-call gets, what the record keeps). D92 Q185: a root reply goes
    # back as package_text of the parts passed on (None with no text part); a sub-call as the record's text
    shapes = {
        "blocked prompt": ([{"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"}, "usageMetadata": usage}],
                           None, "", lambda r: r["status"] == "blocked" and r["block_reason"] == "PROHIBITED_CONTENT"
                           and r["block_source"] == "prompt"),
        "blocked answer": ([{"candidates": [part]}, end("SAFETY")],
                           None, "", lambda r: r["status"] == "blocked" and r["block_source"] == "answer"
                           and r["text"] == "half an answer"),
        "recitation": ([{"candidates": [part]}, end("RECITATION")],
                       "half an answer", "half an answer", lambda r: r["status"] == "recitation"
                       and r["stop_reason"] == "RECITATION" and r["text"] == "half an answer"),
        "empty, no finishReason": ([{"candidates": [{"content": {"role": "model", "parts": []}}],
                                     "usageMetadata": usage}],
                                   None, "", lambda r: r["status"] == "empty" and r["stop_reason"] is None
                                   and r["error"] is None),
        "empty STOP, blank text": ([end("STOP", [{"text": " "}])],
                                   " ", " ", lambda r: r["status"] == "empty" and r["stop_reason"] == "STOP"),
        "malformed_function_call, no part": ([{"candidates": [{"content": {"role": "model"},
                                                               "finishReason": "MALFORMED_FUNCTION_CALL"}],
                                               "usageMetadata": usage}],
                                             None, "", lambda r: r["status"] == "malformed_function_call"
                                             and r["stop_reason"] == "MALFORMED_FUNCTION_CALL" and r["raw_parts"] == []),
        "malformed_response after streamed text": ([{"candidates": [part]}, end("MALFORMED_RESPONSE")],
                                                   "half an answer", "half an answer",
                                                   lambda r: r["status"] == "malformed_response"
                                                   and r["text"] == "half an answer"),
        "malformed_response, a '' text part beside a thought signature (G6's 4)":
            ([end("MALFORMED_RESPONSE", [sig])], "", "",
             lambda r: r["status"] == "malformed_response" and r["raw_parts"] == [sig] and r["text"] == ""),
        "language after streamed text (Q188)": ([{"candidates": [part]}, end("LANGUAGE")],
                                                "half an answer", "half an answer",
                                                lambda r: r["status"] == "language" and r["stop_reason"] == "LANGUAGE"),
        "other, no part (Q188)": ([end("OTHER")], None, "",
                                  lambda r: r["status"] == "other" and r["stop_reason"] == "OTHER"),
        "unexpected_tool_call after streamed text (Q188)": ([{"candidates": [part]}, end("UNEXPECTED_TOOL_CALL")],
                                                            "half an answer", "half an answer",
                                                            lambda r: r["status"] == "unexpected_tool_call"),
        "too_many_tool_calls, no part (Q188)": ([end("TOO_MANY_TOOL_CALLS")], None, "",
                                                lambda r: r["status"] == "too_many_tool_calls"),
    }

    def serve(chunks):
        gc._open = lambda req, timeout=None: FakeResponse([f"data: {json.dumps(c)}\n".encode() for c in chunks]
                                                          + [b"\n"])
    saved = (gc._open, gc._arm, gc._key, gc._sleep)
    gc._arm, gc._key, gc._sleep = (lambda r, s: None), (lambda: FAKE_KEY), (lambda s: None)
    subs = []
    try:
        for root in (True, False):
            for i, (name, (chunks, want_root, want_sub, kept)) in enumerate(shapes.items()):
                want = want_root if root else want_sub
                rid = ex.run_id("b4check", "cap5", f"d89{'r' if root else 's'}{i}")
                sink = ex.sink(rid, root=tmp)
                ctx = ex.context("b4check", "cap5", "19_hpai_canada_TE3", 1, {"rlm_ref": ad.IDENT},
                                 base_url=runner.BASE_URL, run=rid, sink=sink, judge=False)
                s = ad.Session(ctx, 5, "19_hpai_canada_TE3", sink)
                serve(chunks)
                prompt = ([{"role": "system", "content": "s"}, {"role": "user", "content": "Turn 1/5: go"}]
                          if root else "SUB d89")
                try:
                    got = ad.LockedGemini(s)._call(prompt, None, False, root)
                except Exception as e:                  # noqa: BLE001
                    got = e
                rec = lines(sink / "calls.jsonl")[-1]
                check(f"14 D89, D90, D92 {'root' if root else 'sub-call'}, {name}: goes back to the package as "
                      f"{want!r}, nothing raised; the record keeps status {rec['status']} and the reason",
                      (got is None if want is None else got == want) and kept(rec) and rec["b4"]["call"] == ("root" if root else "sub")
                      and s.fatal is None and s.calls[-1]["status"] == rec["status"], f"{got!r} {rec['status']}")
                if not root:
                    subs.append(s.calls[-1])
        statuses = ["blocked", "blocked", "recitation", "empty", "empty", "malformed_function_call",
                    "malformed_response", "malformed_response", "language", "other", "unexpected_tool_call",
                    "too_many_tool_calls"]
        check("14 D89, D90, D92 Q188 calls.sub_failed (adapter.sub_failed) over those twelve sub-calls counts all but "
              "the STOP empty one: the two blocks, the recitation, the no-finishReason empty reply, the three malformed "
              "replies and the four other reasons, as before D89 when each raised",
              ad.sub_failed(subs) == 11 and [c["status"] for c in subs] == statuses,
              f"{ad.sub_failed(subs)} {[(c['status'], c['stop_reason']) for c in subs]}")

        def session(tag):
            rid = ex.run_id("b4check", "cap5", tag)
            sink = ex.sink(rid, root=tmp)
            ctx = ex.context("b4check", "cap5", "19_hpai_canada_TE3", 1, {"rlm_ref": ad.IDENT},
                             base_url=runner.BASE_URL, run=rid, sink=sink, judge=False)
            return ad.Session(ctx, 5, "19_hpai_canada_TE3", sink), sink
        # D90: the closing call at the cap (forced_final, the package's answer, rlm/core/rlm.py:673-695)
        s, sink = session("d90ff")
        s.forced = True
        serve(shapes["malformed_response after streamed text"][0])
        try:
            got = ad.LockedGemini(s)._call([{"role": "user", "content": "Turn 5/5: go"}], None, False, True)
        except Exception as e:                      # noqa: BLE001
            got = e
        rec = lines(sink / "calls.jsonl")[-1]
        check("14 D90 a malformed_response closing call (forced_final) goes back with the text it held, the package's "
              "answer; the record keeps the status",
              got == "half an answer" and rec["b4"]["call"] == "forced_final" and rec["status"] == "malformed_response"
              and s.fatal is None, f"{got!r} {rec['b4']['call']} {rec['status']}")
        # D92 Q185: a closing call with no text part goes back as None, the package's answer, which run_question
        # stores as ""; closing_answer gives the same "" from the stored record
        s, sink = session("q185ff")
        s.forced = True
        serve(shapes["malformed_function_call, no part"][0])
        try:
            got = ad.LockedGemini(s)._call([{"role": "user", "content": "Turn 5/5: go"}], None, False, True)
        except Exception as e:                      # noqa: BLE001
            got = e
        rec = lines(sink / "calls.jsonl")[-1]
        check("14 D92 Q185 a closing call with no text part goes back as None (the package's own client's "
              "response.text); closing_answer(record) is the \"\" run_question stores",
              got is None and rec["b4"]["call"] == "forced_final" and ad.closing_answer(rec) == "", f"{got!r}")
        # what still raises: a stream that ended without a finishReason but held a part (status error)
        cut = [{"candidates": [part]}]
        s, sink = session("q188err")
        serve(cut)
        e = raises(ad.RootCallError, lambda: ad.LockedGemini(s)._call(
            [{"role": "user", "content": "Turn 1/5: go"}], None, False, True))
        check("14 D92 a root reply with status error (no finishReason, a part held) still raises RootCallError",
              isinstance(e, ad.RootCallError) and lines(sink / "calls.jsonl")[-1]["status"] == "error", repr(e)[:100])
        s, sink = session("q188errs")
        serve(cut)
        e = raises(ad.SubCallError, lambda: ad.LockedGemini(s)._call("SUB d90", None, False, False))
        check("14 D92 a sub-call with status error still raises SubCallError into the code",
              isinstance(e, ad.SubCallError), repr(e)[:100])

        # D92 Q187: rebuild_from_closing on a stored-shape answer (forced_final_failed at a malformed closing call)
        def call(seq, kind, status, parts, stop=None):
            return {"seq": seq, "ctx_uid": "u1", "status": status, "stop_reason": stop, "raw_parts": parts,
                    "text": "".join(p.get("text", "") for p in parts), "b4": {"call": kind}}
        ans = {"answer_key": "cap1|Q|d1", "ctx_uid": "u1", "seq": 9, "answer": "", "status": "failed",
               "stop_reason": "forced_final_failed", "error": "root call forced_final turn 2: status malformed_response",
               "forced_final": True, "forced_final_has_code": False, "calls": {"seqs": [1, 2, 3]},
               "lock_sha256": "8fa06e43", "adapter_sha256": "old"}
        code_reply = [{"text": "Answer.\n```repl\nprint(1)\n```"}]
        good = [call(1, "root", "ok", [{"text": "t"}], "STOP"), call(2, "sub", "ok", [{"text": "s"}], "STOP"),
                call(3, "forced_final", "malformed_response", code_reply, "MALFORMED_RESPONSE")]
        r = ad.rebuild_from_closing(ans, good, {"script": "check"})
        check("14 D92 Q187 rebuild_from_closing: the answer is the closing call's text, status ok, stop_reason turn_cap, "
              "error None, forced_final_has_code from the package's parser; every other field as stored; rebuilt "
              "names the seq, the call's status and the stored values",
              r["answer"] == code_reply[0]["text"] and r["status"] == "ok" and r["stop_reason"] == "turn_cap"
              and r["error"] is None and r["forced_final_has_code"] is True
              and {k: v for k, v in r.items() if k not in ad.REBUILT_FIELDS + ("rebuilt",)}
              == {k: v for k, v in ans.items() if k not in ad.REBUILT_FIELDS}
              and r["rebuilt"]["from_call_seq"] == 3 and r["rebuilt"]["call_status"] == "malformed_response"
              and r["rebuilt"]["as_stored"]["stop_reason"] == "forced_final_failed" and r["rebuilt"]["script"] == "check",
              json.dumps(r["rebuilt"])[:200])
        blank = good[:2] + [call(3, "forced_final", "malformed_response", [sig], "MALFORMED_RESPONSE")]
        r2 = ad.rebuild_from_closing(ans, blank, {})
        refusals = [raises(ValueError, f) for f in (
            lambda: ad.rebuild_from_closing({**ans, "stop_reason": "root_call_failed"}, good, {}),
            lambda: ad.rebuild_from_closing(ans, good[:2], {}),
            lambda: ad.rebuild_from_closing(ans, [good[0], call(2, "sub", "malformed_response", [], "MALFORMED_RESPONSE"),
                                                  good[2]], {}),
            lambda: ad.rebuild_from_closing(ans, good[:2] + [call(3, "forced_final", "error", [])], {}),
            lambda: ad.rebuild_from_closing(ans, [call(1, "root", "recitation", [part["content"]["parts"][0]],
                                                       "RECITATION")] + good[1:], {}))]
        check("14 D92 Q187 rebuild_from_closing: a '' closing reply gives the answer \"\"; it refuses an answer not "
              "forced_final_failed, calls that are not the answer's, a sub-call D90 now returns, a closing call whose "
              "status still raises, and an earlier root call D89 now returns",
              r2["answer"] == "" and r2["forced_final_has_code"] is False and all(refusals),
              repr([type(e).__name__ if e else None for e in refusals]))
        # closing_answer reads what LockedGemini._call hands the package for that status: package_text of the parts
        # passed on for a returned status and for length, the record's text for ok. Each record here has a text
        # field that differs from its parts' text, so reading the wrong one shows (in a stored record they agree)
        parts = [{"text": "plan", "thought": True}, {"text": "from the parts"}]
        diff = lambda st, stop: {**call(3, "forced_final", st, parts, stop), "text": "from the record"}  # noqa: E731
        got = {st: ad.closing_answer(diff(st, st.upper())) for st in gc.PASSED_ON_STATUSES + ("empty",)}
        got["length"] = ad.closing_answer(diff("length", "MAX_TOKENS"))
        got["blocked"] = ad.closing_answer(diff("blocked", "SAFETY"))
        got["ok"] = ad.closing_answer(diff("ok", "STOP"))
        check("14 D92 Q187 closing_answer gives package_text of the parts passed on (thought parts left out) for every "
              "returned status and for length, \"\" for a blocked reply (no parts passed on), the record's text for ok",
              all(got[st] == "from the parts" for st in gc.PASSED_ON_STATUSES + ("empty", "length"))
              and got["blocked"] == "" and got["ok"] == "from the record", json.dumps(got)[:300])
    finally:
        gc._open, gc._arm, gc._key, gc._sleep = saved


def offline(tmp: Path) -> None:
    global BUNDLE, IMAGE
    lock = load()
    # 1. package and patches
    lockfile = (ROOT / "experiments" / "rlm_ref" / "uv.lock").read_text()
    check("rlms 0.1.3 installed, its wheel pinned by sha256 in uv.lock",
          importlib.metadata.version("rlms") == "0.1.3" and f"sha256:{ad.PACKAGE['wheel_sha256']}" in lockfile)
    import dotenv
    check("patch 0: dotenv.load_dotenv is a no-op", dotenv.load_dotenv() is False)
    import rlm.clients as rlm_clients
    from rlm.core import comms_utils, rlm as rlm_core
    from rlm.environments import docker_repl
    e = raises(LockError, lambda: rlm_clients.get_client("gemini", {"model_name": ad.MODEL}))
    check("patch 1: the package's own clients are refused", isinstance(e, LockError), str(e)[:80])
    e = raises(ad.SetupError, lambda: rlm_core.get_client("gemini", {"model_name": ad.MODEL}))
    check("patch 1: get_client outside a question is refused", isinstance(e, ad.SetupError))
    script = docker_repl._build_exec_script("x = 1", 4321, 1)
    check("patch 2/3: the container script has no client timeout and raising sub-call functions",
          "_LLM_TIMEOUT = None" in script and "_RLM_TIMEOUT = None" in script and "_LLM_TIMEOUT = 600" not in script
          and "class LLMQueryError" in script and 'f"Error: {e}"' not in script and script.count("def llm_query(") == 1)
    saved = ad._orig["build_exec_script"]
    ad._orig["build_exec_script"] = lambda *a, **k: saved(*a, **k).replace("_RLM_TIMEOUT = 3600", "_RLM_TIMEOUT = 36")
    e = raises(ad.SetupError, lambda: docker_repl._build_exec_script("x = 1", 4321, 1))
    ad._orig["build_exec_script"] = saved
    check("patch 3: a container script that differs from rlms 0.1.3's is refused", isinstance(e, ad.SetupError))
    seen = {}
    saved_sr = ad._orig["socket_request"]
    ad._orig["socket_request"] = lambda address, data, timeout=300: seen.setdefault("timeout", timeout) or {}
    comms_utils.send_lm_request(("127.0.0.1", 1), comms_utils.LMRequest(prompt="x"), timeout=300)
    ad._orig["socket_request"] = saved_sr
    check("patch 2: a sub-call socket waits without limit (the package passes 300 s)",
          "timeout" in seen and seen["timeout"] is None, repr(seen))
    IMAGE = ad.ensure_image()
    check("sandbox image: the pinned IMAGE_ID, labelled with sandbox/'s inputs",
          IMAGE["image_id"] == ad.IMAGE_ID and IMAGE["b4.base"] == ad.BASE_IMAGE, IMAGE["image_id"][:19])
    e = raises(ad.SetupError, lambda: ad.ensure_image("sha256:" + "0" * 64))
    check("sandbox image: any other id is refused and nothing is built", isinstance(e, ad.SetupError)
          and "never builds" in str(e), str(e)[:100])
    IMAGE["network"] = ad.ensure_network(IMAGE["image_id"])
    probe = ad.probe_network(IMAGE["image_id"])
    check("patch 6: from b4-sandbox no laptop port (outside the proxy range), the VM's ssh or a private address is "
          "reachable", probe["targets"] >= 3 and not probe["open"]
          and all(v == "ConnectionRefusedError" for v in probe["results"].values()),
          f"{probe['targets']} targets: {sorted(set(probe['results'].values()))}")
    check("patch 6: the probe's canary (a listener of its own) was refused before any real port was tried",
          probe.get("canary") == "refused")
    import socket
    canary = socket.socket()
    canary.bind(("127.0.0.1", 0))
    canary.listen(1)
    try:                                            # the control: a listener of our own, never a real service
        p = subprocess.run(["docker", "run", "--rm", "--add-host", "host.docker.internal:host-gateway",
                            IMAGE["image_id"], "python", "-c", ad._PROBE,
                            json.dumps([["host.docker.internal", canary.getsockname()[1]]])],
                           capture_output=True, text=True)
    finally:
        canary.close()
    check("patch 6 control: the same probe on Docker's default network reaches a laptop loopback listener, so the "
          "refusals above are the firewall's", '"open"' in p.stdout, p.stdout.strip() or p.stderr[-200:])
    p = subprocess.run(["docker", "run", "--rm", "--network", ad.NETWORK, IMAGE["image_id"], "python", "-c",
                        ad._PROBE, json.dumps([["pypi.org", 443]])], capture_output=True, text=True)
    check("patch 6 (information): the public internet stays reachable from the sandbox, as in the package's default",
          '"open"' in p.stdout, p.stdout.strip() or p.stderr[-200:])
    e = raises(ad.SetupError, lambda: ad._sandbox_run_args(["docker", "run", "-d", "--rm", "--privileged"]))
    check("patch 6: a docker run of another shape is refused", isinstance(e, ad.SetupError))
    stale_ws = tmp / "stale" / "docker_ws"
    for d in ("p999999", "docker_repl_old", f"p{os.getpid()}"):
        (stale_ws / d).mkdir(parents=True, exist_ok=True)
    cid = subprocess.run(["docker", "run", "-d", "--rm", "--network", ad.NETWORK, "--label", "b4.sandbox=1",
                          "--label", "b4.pid=999999", IMAGE["image_id"], "tail", "-f", "/dev/null"],
                         capture_output=True, text=True).stdout.strip()
    gone = ad.clean_stale(tmp / "stale")
    left = subprocess.run(["docker", "ps", "-aq", "--filter", f"id={cid}"], capture_output=True, text=True).stdout
    check("clean_stale: a dead run's container and workspaces are removed, a live process's workspace kept",
          cid[:12] in [g[:12] for g in gone["containers_removed"]] and not left.strip()
          and sorted(gone["workspaces_removed"]) == ["docker_repl_old", "p999999"]
          and (stale_ws / f"p{os.getpid()}").is_dir(), json.dumps(gone))
    p = subprocess.run(["docker", "run", "--rm", "--network", "none", IMAGE["image_id"], "sh", "-c",
                        "pip install -q --disable-pip-version-check dill requests 2>/dev/null; echo exit=$?; "
                        "python -c 'import dill, requests; print(dill.__version__, requests.__version__)'"],
                       capture_output=True, text=True)
    check("the sandbox's own 'pip install -q dill requests' succeeds with no network (nothing downloaded)",
          "exit=0" in p.stdout and "0.4.1 2.34.2" in p.stdout, p.stdout.strip().replace("\n", " | "))
    env = docker_repl.DockerREPL(image=IMAGE["image_id"], lm_handler_address=None)
    try:
        host, port = env.proxy_server.server_address
        r = subprocess.run(["docker", "exec", env.container_id, "python", "-c",
                            f"import requests; print(requests.post('http://host.docker.internal:{port}/x', json={{}}, "
                            f"timeout=10).status_code)"], capture_output=True, text=True)
        check("patch 4: the proxy binds 127.0.0.1 on a proxy port and the container on b4-sandbox reaches it",
              host == "127.0.0.1" and ad.PROXY_PORTS[0] <= port <= ad.PROXY_PORTS[1] and r.stdout.strip() == "404",
              f"{host}:{port} -> {r.stdout.strip() or r.stderr[-200:]}")
        info = json.loads(subprocess.run(["docker", "inspect", env.container_id, "--format", "{{json .}}"],
                                         capture_output=True, text=True).stdout)
        labels = info["Config"]["Labels"]
        check("patch 6: the package's container runs on b4-sandbox with the run labels and nothing else added",
              list(info["NetworkSettings"]["Networks"]) == [ad.NETWORK] and labels.get("b4.sandbox") == "1"
              and labels.get("b4.pid") == str(os.getpid()) and info["HostConfig"]["Privileged"] is False
              and info["HostConfig"]["ExtraHosts"] == ["host.docker.internal:host-gateway"],
              f"{list(info['NetworkSettings']['Networks'])} {labels}")
        r = env.execute_code("import sys\nprint(sys.argv[0], sys.path[0], __name__)\n1/0")
        check("patch 7: the script runs from stdin as /workspace/_exec.py (argv, sys.path, traceback with its source "
              "line) and the host writes no _exec.py",
              r.stdout.strip() == "/workspace/_exec.py /workspace __main__"
              and 'File "/workspace/_exec.py"' in r.stderr and "exec(code, combined, combined)" in r.stderr
              and "ZeroDivisionError" in r.stderr and not (Path(env.temp_dir) / "_exec.py").exists(),
              (r.stdout + " | " + r.stderr)[-300:])
    finally:
        env.cleanup()

    # 2. corpus
    BUNDLE = ad.load_context()
    doc = json.loads(Path(ROOT / BUNDLE["file"]).read_text())
    check("context file: 20 named papers, file sha256 = its .sha256, context_sha256 recomputed",
          len(BUNDLE["context"]) == 20 and all(t.startswith("File: ") for t in BUNDLE["context"])
          and doc["summary"]["chunks"] == 778, f"context {BUNDLE['context_sha256'][:12]}, file {BUNDLE['file_sha256'][:12]}")
    bad = tmp / "tampered.json"
    d2 = copy.deepcopy(doc)
    d2["context"][0] = d2["context"][0] + " "
    raw = (json.dumps(d2, ensure_ascii=False, indent=1) + "\n").encode()
    bad.write_bytes(raw)
    bad.with_suffix(".json.sha256").write_text(f"{ad.sha256_bytes(raw)}  tampered.json\n")
    e = raises(ad.SetupError, lambda: ad.load_context(bad))
    check("a context whose text differs from its context_sha256 is refused", isinstance(e, ad.SetupError))
    new = ad.add_sandbox_forms(BUNDLE, IMAGE)
    check("the sandbox's repr(context) and each paper's repr are corpus forms", new == 0,
          f"{new} forms differ between the host's Python and the sandbox's")

    # 3-5, 8. a normal question at cap 3
    def root_a(turn, cap, forced, text):
        if turn == 1:
            return repl("print(type(context).__name__, len(context))\nr = llm_query('SUB-OK hello')\nprint(r)\n"
                        "big = context[0]\nprint(len(big))\nlong = 'z' * 5000")
        if turn == 2:
            return repl("try:\n    llm_query('SUB-LENGTH please')\nexcept Exception as e:\n"
                        "    print('CAUGHT', type(e).__name__, e)\n"
                        "rs = llm_query_batched(['SUB-OK a', 'SUB-OK b'])\nprint(rs)\n"
                        "try:\n    llm_query_batched(['SUB-OK c', 'SUB-LENGTH d'])\nexcept Exception as e:\n"
                        "    print('BATCH', type(e).__name__, e.responses)\n"
                        "print('EMPTY', repr(llm_query('SUB-EMPTY')))") + "\n" + repl("llm_query('SUB-ERROR')")
        return repl("answer['content'] = 'final from code'\nanswer['ready'] = True")

    rec, sink, fake = run_one(tmp, "a", 3, root_a)
    ok = isinstance(rec, dict)
    check("question at cap 3 ends with the code's answer", ok and rec["stop_reason"] == "answer_ready"
          and rec["answer"] == "final from code" and rec["turns_used"] == 3, repr(rec)[:300] if not ok else "")
    calls = lines(sink / "calls.jsonl")
    roots = [c for c in calls if c["b4"]["call"] == "root"]
    subs = [c for c in calls if c["b4"]["call"] == "sub"]
    gem = lock.gemini(ad.MODEL, 1)
    want_opts = gc.generation_config(gem)
    check("records: one per call, seqs 1..n (concurrent batch calls may reach the file out of seq order), run "
          "context fields added", ok and sorted(c["seq"] for c in calls) == list(range(1, len(calls) + 1)) and len(roots) == 3 and len(subs) == 8
          and all(c["item_id"] == QUESTION["id"] and c["run_draw"] == 1 for c in calls), f"{len(roots)} root, {len(subs)} sub")
    check("records: the lock's Gemini settings, seed = draw, no thinking setting (Google's default, D66)",
          all(c["options_sent"] == want_opts and "thinkingConfig" not in c["options_sent"]
              and c["lock_sha256"] == lock.sha256 and c["provider"] == "gemini" and c["role"] == "generator"
              for c in calls), json.dumps(want_opts))
    check("records: root turns carry passages [] and messages_sent; sub-calls prompt_sent and passages None",
          all(c["passages"] == [] and isinstance(c["messages_sent"], list) for c in roots)
          and all(c["passages"] is None and isinstance(c["prompt_sent"], str) for c in subs))
    blocks = {(c["b4"]["turn"], c["b4"]["block"]) for c in subs}
    batched = sorted((c["b4"]["batch_id"], c["b4"]["batch_index"], c["prompt_sent"]) for c in subs
                     if c["b4"]["batch_id"] is not None)
    check("records: sub-calls carry their turn and code block; batched prompts their batch slot",
          blocks == {(1, 1), (2, 1), (2, 2)} and batched == [(1, 0, "SUB-OK a"), (1, 1, "SUB-OK b"),
                                                            (2, 0, "SUB-OK c"), (2, 1, "SUB-LENGTH d")],
          f"{sorted(blocks)}; {batched}")
    check("records: cap, draw and question in every record",
          all(c["b4"]["cap"] == 3 and c["b4"]["draw"] == 1 and c["b4"]["question_id"] == QUESTION["id"] for c in calls))
    lasts = [c["messages_sent"][-1]["content"] for c in roots]
    check("cap in prompt: each root turn ends with 'Turn i/3'", [x.split("\n")[-1] for x in lasts]
          == ["Turn 1/3:", "Turn 2/3:", "Turn 3/3:"], repr([x[-12:] for x in lasts]))
    trace = json.loads((sink / rec["trace"]["path"]).read_text()) if ok else {}
    out2 = trace["iterations"][1]["code_blocks"][0]["stdout"] if ok else ""
    check("Q47: a sub-call stopped on the output limit raises LLMQueryError inside the container, which the code can "
          "catch", "CAUGHT LLMQueryError sub-call stopped on the output limit" in out2, out2[:160])
    length = [c for c in subs if c["status"] == "length"]
    check("Q47: each stopped sub-call is recorded with status length",
          len(length) == 2 and all(c["stop_reason"] == "MAX_TOKENS" for c in length) and rec["calls"]["sub_length"] == 2)
    check("Q47: a batch with one stopped prompt raises with the other responses kept",
          "BATCH LLMQueryError ['ok:c', None]" in out2 and "['ok:a', 'ok:b']" in out2, out2[-200:])
    check("an ok sub-call's empty text reaches the code as '' (the package made it 'Error: None')",
          "EMPTY ''" in out2)
    err2 = trace["iterations"][1]["code_blocks"][1]["stderr"] if ok else ""
    nxt = roots[2]["messages_sent"][-2]["content"] if ok else ""
    check("Q47: a failed sub-call (HTTP 400) left uncaught is a traceback the next turn shows",
          "LLMQueryError" in err2 and "status error" in err2 and "LLMQueryError" in nxt
          and any(c["status"] == "error" for c in subs), err2[-160:])
    check("answer record: tokens are the sums of the records (the package's usage is not used)",
          ok and rec["tokens"]["total"]["prompt_tokens"] == sum(c["prompt_tokens"] or 0 for c in calls)
          and rec["tokens"]["total"]["output_tokens"] == sum(c["output_tokens"] or 0 for c in calls)
          and rec["tokens"]["total"]["thinking_tokens"] == sum(c["thinking_tokens"] or 0 for c in calls)
          and sorted(rec["calls"]["seqs"]) == sorted(c["seq"] for c in calls))
    answers = lines(sink / "answers.jsonl")
    check("answer record in answers.jsonl with stop reason, lock hash, latency, passages, context and sandbox",
          len(answers) == 1 and answers[0]["lock_sha256"] == lock.sha256 and answers[0]["wall_s"] > 0
          and answers[0]["passages"]["context_sha256"] == BUNDLE["context_sha256"]
          and answers[0]["sandbox"]["image_id"] == IMAGE["image_id"] and answers[0]["patches"] == list(ad.PATCHES))
    loc1 = trace["iterations"][0]["code_blocks"][0]["locals"] if ok else {}
    check("trace: repr(context) is a corpus reference, never the corpus",
          loc1.get("context") == {"corpus": BUNDLE["context_sha256"], "form": "repr(context)"}
          and loc1.get("context_0") == loc1.get("context")
          and isinstance(loc1.get("big"), dict) and loc1["big"].get("form") == "repr", json.dumps(loc1)[:300])
    strings = []

    def walk(o):
        if isinstance(o, str):
            strings.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(trace)
    check("trace: no paper's text in any string of the trace", ok and not any(
        t[200:400] in x for t in BUNDLE["context"] for x in strings),
        f"{len(strings)} strings, longest {max(map(len, strings), default=0):,} characters")
    check("trace: sub-call seqs sit under their code block, root seqs under their turn",
          ok and trace["iterations"][0]["root_call_seq"] == roots[0]["seq"]
          and trace["iterations"][1]["code_blocks"][0]["sub_call_seqs"]
          == sorted(c["seq"] for c in subs if (c["b4"]["turn"], c["b4"]["block"]) == (2, 1)))

    # 4. another cap
    rec5, sink5, _ = run_one(tmp, "b", 5, lambda t, c, f, x: repl("answer['content'] = 'x'\nanswer['ready'] = True"))
    r5 = [c for c in lines(sink5 / "calls.jsonl") if c["b4"]["call"] == "root"]
    check("cap in prompt: a cap-5 run says 'Turn 1/5'", r5 and r5[0]["messages_sent"][-1]["content"].endswith("Turn 1/5:"))

    # 6. forced final; a failing root call
    rec_f, sink_f, fake_f = run_one(tmp, "c", 1, lambda t, c, f, x: "the forced answer" if f
                                    else repl("print(len(context))"))
    cf = lines(sink_f / "calls.jsonl")
    ok = isinstance(rec_f, dict)
    check("forced final at the cap: turn cap+1, call forced_final, ends on the package's assistant turn",
          ok and rec_f["stop_reason"] == "turn_cap" and rec_f["answer"] == "the forced answer"
          and [c["b4"]["call"] for c in cf] == ["root", "forced_final"] and cf[1]["b4"]["turn"] == 2
          and cf[1]["messages_sent"][-1] == {"role": "assistant", "content": "Please provide a final answer to the "
                                                                             "user's question based on the information provided."},
          repr(rec_f)[:200] if not ok else "")
    rec_e, sink_e, _ = run_one(tmp, "d", 3, lambda t, c, f, x: repl("print(1)") if t == 1 else 400)
    ce = lines(sink_e / "calls.jsonl")
    check("a root call that fails ends the question as root_call_failed, with its record",
          isinstance(rec_e, dict) and rec_e["stop_reason"] == "root_call_failed" and rec_e["answer"] == ""
          and ce[-1]["status"] == "error" and ce[-1]["b4"]["turn"] == 2 and rec_e["status"] == "failed",
          repr(rec_e)[:200])

    # D75 Q48: a root reply cut by the output limit goes on to the next turn; the length stop is recorded and counted
    cut = "Let me look.\n```repl\nprint('CUT-' + 'RAN')\n```\nand then the reply was cut mid"
    rec_l, sink_l, fake_l = run_one(tmp, "l", 3, lambda t, c, f, x: (cut, "MAX_TOKENS") if t == 1
                                    else repl("answer['content'] = 'after the cut'\nanswer['ready'] = True"))
    cl = lines(sink_l / "calls.jsonl")
    nxt = cl[1]["messages_sent"] if len(cl) > 1 else []
    check("Q48: a root call cut by the output limit is recorded with status length and the question goes on",
          isinstance(rec_l, dict)
          and [(c["b4"]["call"], c["status"]) for c in cl] == [("root", "length"), ("root", "ok")]
          and cl[0]["stop_reason"] == "MAX_TOKENS" and rec_l["stop_reason"] == "answer_ready"
          and rec_l["answer"] == "after the cut" and rec_l["status"] == "ok" and rec_l["calls"]["root_length"] == 1
          and rec_l["calls"]["sub_length"] == 0, repr(rec_l)[:300])
    check("Q48: the cut text is the next turn's assistant message and its code block ran",
          any(m["role"] == "assistant" and m["content"] == cut for m in nxt)
          and any("CUT-RAN" in m["content"] for m in nxt if m["role"] == "user"),
          json.dumps([m["role"] for m in nxt]))
    check("Q48: a root call that is not cut counts no root_length",
          isinstance(rec_e, dict) and rec_e["calls"]["root_length"] == 0 and isinstance(rec_f, dict)
          and rec_f["calls"]["root_length"] == 0)
    rec_m, sink_m, _ = run_one(tmp, "m", 1, lambda t, c, f, x: ("the cut forced answer", "MAX_TOKENS") if f
                               else repl("print(1)"))
    cm = lines(sink_m / "calls.jsonl")
    check("Q48: a forced final reply cut by the output limit is the answer, recorded with status length",
          isinstance(rec_m, dict) and rec_m["stop_reason"] == "turn_cap" and rec_m["answer"] == "the cut forced answer"
          and cm[-1]["b4"]["call"] == "forced_final" and cm[-1]["status"] == "length"
          and rec_m["calls"]["root_length"] == 1, repr(rec_m)[:200])
    rec_r, sink_r, _ = run_one(tmp, "r", 3, lambda t, c, f, x: repl("print(1)") if t == 1 else ("x", "RECITATION"))
    check("Q48: any other status that is not ok still ends the question as root_call_failed",
          isinstance(rec_r, dict) and rec_r["stop_reason"] == "root_call_failed" and rec_r["answer"] == ""
          and lines(sink_r / "calls.jsonl")[-1]["status"] == "recitation", repr(rec_r)[:200])

    rec_g, sink_g, _ = run_one(tmp, "g", 1, lambda t, c, f, x: 400 if f else repl("print(1)"))
    check("a forced final call that fails ends the question as forced_final_failed, with its record",
          isinstance(rec_g, dict) and rec_g["stop_reason"] == "forced_final_failed" and rec_g["answer"] == ""
          and lines(sink_g / "calls.jsonl")[-1]["b4"]["call"] == "forced_final", repr(rec_g)[:200])

    # D78 Q114: a cut root reply goes back as google-genai 2.30.1's response.text gives it for the recorded parts
    from google.genai import types as gtypes
    sig = "U0lHTkFUVVJF"                              # a thought signature (base64), as the recorded reply carries
    empty_part = [{"text": "", "thoughtSignature": sig}]   # 01_sarek_CO2 d1's cut root reply (cap 1, depth sweep)
    no_text = [{"thoughtSignature": sig}]
    shapes = [empty_part, no_text, [], [{"text": "plan", "thought": True}],
              [{"text": "plan", "thought": True, "thoughtSignature": sig}, {"text": "a"}, {"text": ""}, {"text": "b"}]]
    pkg = [gtypes.GenerateContentResponse.model_validate_json(json.dumps(
        {"candidates": [{"content": {"role": "model", "parts": p}, "finishReason": "MAX_TOKENS"}]})).text
        for p in shapes]
    mine = [ad.package_text(p) for p in shapes]
    check("Q114: package_text equals google-genai's response.text on five part shapes ('' for an empty text part, "
          "None for none)", importlib.metadata.version("google-genai") == "2.30.1" and mine == pkg
          and mine == ["", None, None, None, "ab"], f"{mine} vs {pkg}")
    rec_q, sink_q, _ = run_one(tmp, "q", 1, lambda t, c, f, x: "the forced answer" if f else (empty_part, "MAX_TOKENS"))
    cq = lines(sink_q / "calls.jsonl")
    nq = cq[1]["messages_sent"] if len(cq) > 1 else []
    check("Q114: a cut root reply with one empty text part goes back as '' (the next turn's assistant message) and "
          "the question goes on", isinstance(rec_q, dict) and cq[0]["status"] == "length" and cq[0]["text"] == ""
          and cq[0]["raw_parts"] == empty_part and nq[-2] == {"role": "assistant", "content": ""}
          and rec_q["stop_reason"] == "turn_cap" and rec_q["answer"] == "the forced answer"
          and rec_q["calls"]["root_length"] == 1, repr(rec_q)[:300])
    rec_n, sink_n, _ = run_one(tmp, "n", 3, lambda t, c, f, x: (no_text, "MAX_TOKENS") if t == 1 else repl("print(1)"))
    cn = lines(sink_n / "calls.jsonl")
    check("Q114: a cut root reply with no text part goes back as None; the package's code-block search raises and "
          "the answer is stored failed with that error",
          isinstance(rec_n, dict) and [(c["b4"]["call"], c["status"]) for c in cn] == [("root", "length")]
          and rec_n["status"] == "failed" and rec_n["stop_reason"] == "error" and rec_n["answer"] == ""
          and (rec_n["error"] or "").startswith("TypeError: expected string or bytes-like object")
          and rec_n["calls"]["root_length"] == 1, repr(rec_n)[:300])
    rec_o, sink_o, _ = run_one(tmp, "o", 1, lambda t, c, f, x: (no_text, "MAX_TOKENS") if f else repl("print(1)"))
    co = lines(sink_o / "calls.jsonl")
    check("Q114: a cut closing reply with no text part is the package's answer None, stored as '' (never 'None'), "
          "counted in root_length", isinstance(rec_o, dict) and rec_o["stop_reason"] == "turn_cap"
          and rec_o["answer"] == "" and co[-1]["b4"]["call"] == "forced_final" and co[-1]["status"] == "length"
          and rec_o["calls"]["root_length"] == 1, repr(rec_o)[:300])

    # 3b. message lists as the authors' client maps them (send_chat); nothing the model's code sends stops the run
    check("send_chat: the package's own root messages map exactly as gemini_client.to_contents maps them",
          all(gc.to_contents(c["messages_sent"]) == ({"parts": [{"text": c["system_sent"]}]}, c["contents_sent"])
              for c in roots), f"{len(roots)} root turns")
    rec_h, sink_h, _ = run_one(tmp, "h", 2, lambda t, c, f, x: "done" if f else repl(
        "for name, p in [('model', [{'role': 'model', 'content': 'SUB-OK m'}]),\n"
        "                ('norole', [{'content': 'SUB-OK n'}]),\n"
        "                ('tool', [{'role': 'tool', 'content': 'SUB-OK t'}]),\n"
        "                ('images', [{'role': 'user', 'content': 'SUB-OK i', 'images': ['x']}]),\n"
        "                ('empty', [{'role': 'user', 'content': 'SUB-OK e'}, {'role': 'assistant', 'content': ''},\n"
        "                           {'role': 'user', 'content': 'next'}]),\n"
        "                ('none', [{'role': 'user', 'content': None}]),\n"
        "                ('dict', {'prompt': 'x'})]:\n"
        "    try:\n        print(name, repr(llm_query(p)))\n"
        "    except Exception as e:\n        print(name, 'RAISED', type(e).__name__, e)"))
    ch = [c for c in lines(sink_h / "calls.jsonl") if c["b4"]["call"] == "sub" and c["b4"]["turn"] == 1]   # turn 2 repeats
    th = json.loads((sink_h / rec_h["trace"]["path"]).read_text()) if isinstance(rec_h, dict) else {}
    outh = th["iterations"][0]["code_blocks"][0]["stdout"] if th else ""
    check("F1: roles the runner's to_contents refuses (model, none, tool, images) are sent as the authors' client "
          "sends them (user turns, role and content only) and the run goes on",
          isinstance(rec_h, dict) and rec_h["stop_reason"] == "turn_cap"
          and all(f"{n} 'ok:{m}'" in outh for n, m in (("model", "m"), ("norole", "n"), ("tool", "t"), ("images", "i")))
          and [c["contents_sent"] for c in ch[:4]] == [[{"role": "user", "parts": [{"text": f"SUB-OK {m}"}]}]
                                                       for m in "mnti"], (repr(rec_h)[:200] + " | " + outh)[:400])
    check("F3: an empty model turn is sent as the authors' client sends it, an empty text part (not '[Empty]')",
          len(ch) > 4 and ch[4]["contents_sent"][1] == {"role": "model", "parts": [{"text": ""}]}, json.dumps(
              ch[4]["contents_sent"] if len(ch) > 4 else None))
    ns = [c for c in ch if c["b4"]["not_sent"]]
    check("F1: a prompt the authors' client could not send raises LLMQueryError into the code and is recorded as "
          "not sent (status error, no request)",
          "none RAISED LLMQueryError" in outh and "dict RAISED LLMQueryError" in outh and len(ns) == 2
          and all(c["status"] == "error" and c["error"].startswith("not sent:") and c["request_sha256"] is None
                  and c["attempts"] == [] for c in ns) and ns[1]["prompt_given"] == {"prompt": "x"},
          json.dumps([(c["error"], c.get("prompt_given")) for c in ns])[:300])

    # Ctrl-C inside a code block stops the run and stores nothing
    import signal
    timer = threading.Timer(8, lambda: os.kill(os.getpid(), signal.SIGINT))
    timer.start()
    try:
        rec_i, sink_i, _ = run_one(tmp, "i", 3, lambda t, c, f, x: repl("import time\ntime.sleep(30)\nprint('woke')"))
    except KeyboardInterrupt as e:
        rec_i, sink_i = e, tmp / ex.run_id("b4check", "cap3", "i")
    finally:
        timer.cancel()
    left = subprocess.run(["docker", "ps", "-q", "--filter", "label=b4.sandbox=1", "--filter",
                           f"label=b4.pid={os.getpid()}"], capture_output=True, text=True).stdout.strip()
    check("F2: Ctrl-C during a code block raises KeyboardInterrupt, stores no answer and leaves no container",
          isinstance(rec_i, KeyboardInterrupt) and not lines(sink_i / "answers.jsonl") and not left,
          f"{type(rec_i).__name__}: {str(rec_i)[:120]}; containers left: {left!r}")

    # patch 7: model code that replaces _exec.py with a symlink cannot make the host write through it
    def planter(t, c, f, x):
        return "done" if f else (repl("import os\np = '/workspace/_exec.py'\nif os.path.lexists(p):\n    os.remove(p)\n"
                                      "os.symlink('../../../victim.txt', p)\nprint('linked')") + "\n" + repl("print('second block')"))
    patched = docker_repl.DockerREPL.execute_code
    docker_repl.DockerREPL.execute_code = ad._orig["execute_code"]         # the control: the package's own
    try:
        _, sink_s0, _ = run_one(tmp, "s0", 2, planter)
    finally:
        docker_repl.DockerREPL.execute_code = patched
    rec_s, sink_s, _ = run_one(tmp, "s", 2, planter)
    victim0, victim = sink_s0 / "victim.txt", sink_s / "victim.txt"
    check("patch 7 control: with the package's execute_code, the host writes through the planted symlink",
          victim0.exists() and "def llm_query" in victim0.read_text(), f"victim exists: {victim0.exists()}")
    check("patch 7: with the patch, a symlink planted at /workspace/_exec.py is never written through by the host",
          isinstance(rec_s, dict) and not victim.exists(), f"{repr(rec_s)[:120]}; victim exists: {victim.exists()}")

    # 7. key scan; no key in the container
    rec_k, sink_k, _ = run_one(tmp, "e", 3, lambda t, c, f, x: repl(
        "import os\nprint(sorted(k for k in os.environ if 'KEY' in k or 'GEMINI' in k))\n"
        "print(os.path.exists(os.path.expanduser('~/.config/mentori-runs/keys.env')))\n"
        "try:\n    llm_query('SUB-KEY now')\nexcept Exception as e:\n    print('caught', e)"))
    written = "".join(p.read_text(errors="replace") for p in sink_k.rglob("*") if p.is_file())
    check("key scan: a reply holding the key stops the run although the code caught the error",
          isinstance(rec_k, ad.KeyLeakError) and FAKE_KEY not in str(rec_k), repr(rec_k)[:160])
    check("key scan: nothing written holds the key; no answer and no trace for the question",
          FAKE_KEY not in written and not lines(sink_k / "answers.jsonl") and not (sink_k / "traces").exists())
    e = raises(ad.KeyLeakError, lambda: ad.scan(f"x{FAKE_KEY}y", "a test"))
    check("key scan: the error never prints the key", isinstance(e, ad.KeyLeakError) and FAKE_KEY not in str(e))
    rec_n, sink_n, _ = run_one(tmp, "f", 1, lambda t, c, f, x: "done" if f else repl(
        "import os, glob\nprint('ENV', sorted(k for k in os.environ if 'API' in k or 'GEMINI' in k or 'ANTHROPIC' in k))\n"
        "print('FILES', glob.glob('/root/.config/**', recursive=True), glob.glob('/workspace/*'))"))
    tn = json.loads((sink_n / rec_n["trace"]["path"]).read_text()) if isinstance(rec_n, dict) else {}
    outn = tn["iterations"][0]["code_blocks"][0]["stdout"] if tn else ""
    check("the container has no key in its environment and no key file", "ENV []" in outn
          and "mentori-runs" not in outn, outn.strip()[:200])

    # 8. blobs
    want = repr("z" * 5000)
    h = ad.sha256_text(want)
    blob = sink / "blobs" / f"{h}.txt"
    check("trace: a string of 4,096 characters or more is written once as a blob and referenced",
          loc1.get("long") == {"blob": h, "chars": len(want)} and blob.exists() and blob.read_text() == want
          and len(list((sink / "blobs").glob("*.txt"))) == 1, json.dumps(loc1.get("long")))

    # 9. run script
    e = raises(SystemExit, lambda: runner.main(["--cap", "7", "--draw", "1", "--dry-run"]))
    check("run script: all135 refuses a depth-sweep cap", isinstance(e, SystemExit))
    for n in ("15", "77", "88", "96"):
        e = raises(SystemExit, lambda: runner.main(["--cap", "7", "--draw", "1", "--question-set", "depth_sweep86",
                                                    "--n-questions", n, "--dry-run"]))
        check(f"run script: the depth caps refuse --n-questions {n} (D75 Q50: the named set of 86 only)",
              isinstance(e, SystemExit) and "86" in str(e), str(e)[:80])
    e = raises(SystemExit, lambda: runner.main(["--cap", "7", "--draw", "1", "--question-set", "depth_sweep",
                                                "--dry-run"]))
    check("run script: the per-category depth_sweep set is gone", isinstance(e, SystemExit))
    e = raises(SystemExit, lambda: runner.main(["--cap", "5", "--draw", "1", "--question-set", "depth_sweep86",
                                                "--dry-run"]))
    check("run script: depth_sweep86 refuses Figure 2's caps", isinstance(e, SystemExit))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runner.main(["--cap", "7", "--draw", "1", "--question-set", "depth_sweep86", "--dry-run",
                     "--runs-root", str(tmp)])
    check("run script: the depth caps run b4_rlm_ref__cap7__depthsweep86, 86 answers",
          buf.getvalue().startswith("b4_rlm_ref__cap7__depthsweep86: 86 answers"), buf.getvalue().splitlines()[0])
    qs86 = runner.depth_sweep86_questions()
    cats = {c: sum(q["category"] == c for q in qs86) for c in runner.CATEGORIES}
    check("run script: depth_sweep86 is 86 answerable v2.4 questions, 20/20/20/17/9 by category, in the key's order",
          len(qs86) == 86 and all(q["answerable"] for q in qs86) and list(cats.values()) == [20, 20, 20, 17, 9]
          and [q["id"] for q in qs86] == [q["id"] for q in ex.questions() if q["id"] in set(runner.DEPTH_SWEEP86)],
          json.dumps(cats))
    dep = ROOT / runner.DEPTH_SWEEP_DEPOSIT
    if dep.exists():
        dep_sha = ad.sha256_bytes(dep.read_bytes())
        dep_ids = list(dict.fromkeys(r["question_id"] for r in json.loads(dep.read_text())["results"]))
        check("run script: DEPTH_SWEEP86 is the deposit's depth sweep (88 ids) less CD_015 and SY_010, in its order",
              dep_sha == runner.DEPTH_SWEEP_DEPOSIT_SHA256 and len(dep_ids) == 88
              and [i for i in dep_ids if i not in runner.DEPTH_SWEEP_DROPPED] == list(runner.DEPTH_SWEEP86)
              and all(i in dep_ids for i in runner.DEPTH_SWEEP_DROPPED)
              and not ({q["id"] for q in ex.questions()} & set(runner.DEPTH_SWEEP_DROPPED)),
              f"deposit sha256 {dep_sha[:12]}, {len(dep_ids)} ids")
    else:
        print(f"SKIP the deposit {runner.DEPTH_SWEEP_DEPOSIT} is not in this tree (zenodo/ is not in git)")
    e = raises(SystemExit, lambda: runner.main(["--cap", "5", "--draw", "4", "--dry-run"]))
    check("run script: Figure 2's draws only", isinstance(e, SystemExit))
    took = {}
    for d in ("2", "3", "4"):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            took[d] = raises(SystemExit, lambda d=d: runner.main(["--cap", "7", "--draw", d, "--question-set",
                                                                  "depth_sweep86", "--dry-run", "--runs-root", str(tmp)]))
    check("run script: the depth caps run Figure 3's draws 2 and 3 (D78 Q116) and refuse draw 4",
          ex.draws(3) == (1, 2, 3) and took["2"] is None and took["3"] is None and isinstance(took["4"], SystemExit),
          repr(took)[:200])
    for lim in ("0", "-1"):
        e = raises(SystemExit, lambda: runner.main(["--cap", "5", "--draw", "1", "--limit", lim, "--dry-run"]))
        check(f"run script: --limit {lim} is refused (it would drop questions silently)", isinstance(e, SystemExit)
              and "limit" in str(e), str(e)[:80])
    rid = ex.run_id(runner.EXPERIMENT, "cap1", "smoke")
    sdir = ex.sink(rid, root=tmp)
    (sdir / "answers.jsonl").write_text(json.dumps({"answer_key": ex.answer_key("cap1", "01_sarek_CO2", 1)}) + "\n")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runner.main(["--smoke", "--cap", "1", "--draw", "1", "--limit", "1", "--runs-root", str(tmp)])
    check("run script: resume skips an answer already in answers.jsonl", "1 done, 0 to run" in buf.getvalue(),
          buf.getvalue().strip())


def live() -> None:
    """The smoke: cap 1, the first question, draw --live-draw, real Gemini, into findings/runs/b4_rlm_ref__cap1__smoke/;
    then the R2 probe."""
    for k, v in _saved_env.items():                  # the real keys again (environment, else keys.env)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    ad._keys = None
    rid = ex.run_id(runner.EXPERIMENT, "cap1", "smoke")
    sink = ex.RUNS / rid
    key = ex.answer_key("cap1", "01_sarek_CO2", LIVE_DRAW)
    rc_ = runner.main(["--smoke", "--cap", "1", "--draw", str(LIVE_DRAW), "--limit", "1"])
    answers = lines(sink / "answers.jsonl")
    mine = [a for a in answers if a["answer_key"] == key]
    check("live: the smoke ran", rc_ == 0 and len(mine) == 1, f"{len(answers)} answers in {sink}")
    if not mine:
        return
    a = mine[0]
    calls = [c for c in lines(sink / "calls.jsonl") if c["ctx_uid"] == a["ctx_uid"]]   # this answer's context
    forced = [c for c in calls if c["b4"]["call"] == "forced_final"]
    print(f"     answer {a['answer_key']}: stop {a['stop_reason']}, {a['turns_used']} turn(s), "
          f"{a['calls']['sub']} sub-calls, tokens {a['tokens']['total']}, {a['wall_s']} s")
    if forced:
        f = forced[0]
        print(f"     forced final call seq {f['seq']}: status {f['status']}, finishReason {f['stop_reason']}, "
              f"{f['output_tokens']} answer tokens, code block: {'```' in (f['text'] or '')}, "
              f"text {f['text'][:300]!r}")
    print(f"     records: {sink / 'calls.jsonl'}, {sink / 'answers.jsonl'}, {sink / a['trace']['path']}")
    check("live: the answer record names the pinned image and the sandbox network",
          a["sandbox"]["image_id"] == ad.IMAGE_ID and a["sandbox"]["network"]["network"] == ad.NETWORK
          and a["patches"] == list(ad.PATCHES))
    r2_probe(sink)


CLOSING = "Please provide a final answer to the user's question based on the information provided."


def is_answer(rec: dict) -> bool:
    """An ok reply with text and no code block."""
    return rec["status"] == "ok" and rec["text"].strip() != "" and "```" not in rec["text"]


def r2_probe(sink: Path) -> None:
    """Design R2: does Gemini 3 answer the package's closing turn? Built on the most recent smoke answer that reached
    the cap (stop turn_cap or forced_final_failed): its forced final call's messages, exactly as the package sent them
    (the last turn, its code output, then the closing message as an assistant turn, rlm/core/rlm.py:678-684), sent
    again through send_chat under the lock, once as the package sends them and once with the closing message as a
    user turn. Each is key-scanned and recorded in <sink>/r2_probe.jsonl. An answer is an ok reply with text and no
    code block."""
    capped = [a for a in lines(sink / "answers.jsonl") if a["stop_reason"] in ("turn_cap", "forced_final_failed")]
    if not capped:
        check("live R2 probe: a smoke answer reached the cap", False, "none did; rerun the smoke with another draw")
        return
    a = capped[-1]
    ff = [c for c in lines(sink / "calls.jsonl") if c["ctx_uid"] == a["ctx_uid"] and c["b4"]["call"] == "forced_final"]
    msgs = ff[0]["messages_sent"]
    if msgs[-1] != {"role": "assistant", "content": CLOSING}:
        check("live R2 probe: the forced final call ends on the package's closing assistant turn", False)
        return
    lock = load()
    ctx = ex.context(runner.EXPERIMENT, "cap1", a["question_id"], a["draw"], {"rlm_ref": ad.IDENT},
                     base_url=runner.BASE_URL, run=ex.run_id(runner.EXPERIMENT, "cap1", "smoke"), sink=sink,
                     judge=False)
    out = {}
    print(f"     R2 built on {a['answer_key']} (stop {a['stop_reason']}; its forced final seq {ff[0]['seq']}: status "
          f"{ff[0]['status']}, an answer: {is_answer(ff[0])})")
    with rc.run(ctx):
        for shape, last in (("package", msgs[-1]), ("user_turn", {"role": "user", "content": CLOSING})):
            sent = copy.deepcopy(msgs[:-1]) + [last]
            rec = ad.send_chat(lock, a["draw"], sent, thinking=ff[0]["thinking"])
            rec = {**rec, "provider": "gemini", "role": "generator", "messages_sent": sent,
                   "b4": {"call": "r2_probe", "shape": shape, "after_forced_final_seq": ff[0]["seq"],
                          "answer_key": a["answer_key"]}}
            ad._scan_obj(rec, f"the R2 probe record ({shape})")
            rec = rc.append(rec, file="r2_probe.jsonl")
            out[shape] = rec
            print(f"     R2 {shape}: seq {rec['seq']}, status {rec['status']}, finishReason {rec['stop_reason']}, "
                  f"{rec['output_tokens']} answer / {rec['thinking_tokens']} thinking tokens, code block: "
                  f"{'```' in rec['text']}, text {rec['text'][:160]!r}")
    check("live R2 (information, design R2): Gemini 3 answers the package's closing turn after a cap-hit (ok, text, "
          "no code block)", is_answer(out["package"]),
          f"package shape: {out['package']['status']}, answer {is_answer(out['package'])}; as a user turn: "
          f"{out['user_turn']['status']}, answer {is_answer(out['user_turn'])}")


LIVE_DRAW = 1
BUNDLE: dict = {}
IMAGE: dict = {}

if __name__ == "__main__":
    sys.exit(main())
