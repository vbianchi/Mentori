"""Offline checks for experiments/runner/job.py and check_server.py (D80 V6, audit F2). No model call, no server.

    uv run python -m experiments.runner.check_job

A stub server on 127.0.0.1 (a free port) answers like Ollama 0.40.2 and writes a server log the way the Studio's
logs read (findings/recompute/AUDIT_2026-10-16/COUNTERCHECKS.md A6): a request whose runner key (num_ctx, num_batch,
shift; shift unset means true) differs from the loaded runner's starts a new runner, with a "starting llama-server"
line that carries --context-shift unless shift is false, then its KV-cache lines and "load_model: initializing".

1. The load request is what a call sends: the options and fields of ollama_client's generate and chat payloads.
2. runner_flags reads the laptop's and the Beelink's runner lines; -ub is not read as -b.
3. fresh_load under the lock (the judge, and gpt-oss:20b through its date-fixed copy) sends shift and truncate false,
   and every check passes with one unflagged runner; a real call through ollama_client then starts no runner, and
   after_first_call passes and is recorded.
4. A runner started after the load (the first call replaced it) fails after_first_call with SetupError; the
   command line (fresh-load, then after-first-call --record) exits 0, or 1 on a replaced runner.
5. A pending KV-cache check (no block in the log) fails check_server and fresh_load.
6. judge_passages and check_models run after_first_call after their first real call, and refuse on a failure.
7. A runner started with a wrong -c, a wrong -np or a wrong -b (each alone) fails the runner check and the load.
8. judge_passages.start() arms the after-first-call hook (stubs: the server, and the binary check); the first
   judge_call fires it and the second does not.
9. check_models makes no further call for a model once after_first_call has refused it (the break at
   check_models.py:84): one prompted call per model, where models with a thinking-off mode otherwise make two.
10. K1 review F3 (17 October): a job that also embeds (RAGAS: bge-m3, a runner of its own). after_first_call with
   also=(bge-m3,) passes with the load's runner plus one --embedding runner and both models in /api/ps, and fails
   without also (the race F3 describes), before the embedding runner has started, on a replaced load runner beside
   the embedding one, on a second runner that is not an embedding runner, and with a third model in /api/ps; the
   command line takes --also.
Each fix is also run as a mutant (the old source line put back): the case that guards it must then fail, so no
case passes vacuously.
"""

import json
import re
import sys
import tempfile
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import experiments.runner.check_server as cs  # noqa: E402
import experiments.runner.job as job  # noqa: E402
from experiments.runner.lock import load  # noqa: E402
from experiments.runner.ollama_client import generate  # noqa: E402

results = []
lock = load()
JUDGE = lock.d["judge"]["model"]
NOSLEEP = types.SimpleNamespace(sleep=lambda s: None)       # check_server waits 20 x 1 s for a pending block
cs.time = NOSLEEP


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def mutant(mod, old: str, new: str):
    """mod's source with one line changed (old must occur once), as a new module."""
    src = Path(mod.__file__).read_text()
    assert src.count(old) == 1, f"{mod.__name__}: mutant anchor not found once: {old[:60]}"
    m = types.ModuleType(mod.__name__ + "_mutant")
    m.__file__ = mod.__file__
    exec(compile(src.replace(old, new), mod.__file__, "exec"), m.__dict__)
    if hasattr(m, "time") and m.__name__.startswith("experiments.runner.check_server"):
        m.time = NOSLEEP
    return m


# ---------------------------------------------------------------- stub server and log

class Server:
    """One stub Ollama: its log file, the runner it holds, and what it was sent."""

    def __init__(self, logdir: Path, write_block: bool = True):
        self.log = logdir / "server.log"
        self.log.write_text('time=2026-10-16T20:00:00.000+02:00 level=INFO source=routes.go:2005 msg="server config" '
                            'env="map[OLLAMA_FLASH_ATTENTION:true OLLAMA_KV_CACHE_TYPE:q8_0 OLLAMA_NUM_PARALLEL:1 OLLAMA_SCHED_SPREAD:false]"\n')
        self.write_block, self.runner, self.tag, self.posts, self.n = write_block, None, None, [], 0
        self.bad = {}                    # V6 case 7: a flag the runner line prints wrong ("c", "np" or "b")
        self.extra = {}                  # case 10: other models /api/ps holds (an embedding runner's, a stranger's)
        tags = dict(lock.d["models"])
        srv = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, objs):
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                for o in objs:
                    self.wfile.write((json.dumps(o) + "\n").encode())

            def do_GET(self):
                if self.path == "/api/version":
                    return self._send([{"version": lock.d["server"]["ollama_version"]}])
                if self.path == "/api/tags":
                    return self._send([{"models": [{"name": t, "digest": r["digest"]} for t, r in tags.items()]}])
                held = [] if srv.runner is None else [{"name": srv.tag, "digest": tags[srv.tag]["digest"],
                                                        "context_length": srv.runner[0]}]
                held += [{"name": t, "digest": tags[t]["digest"], "context_length": 8192} for t in srv.extra]
                return self._send([{"models": held}])

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                srv.posts.append(body)
                if body.get("keep_alive") == 0 and "prompt" not in body and "messages" not in body:
                    srv.runner = srv.tag = None
                    return self._send([{"model": body["model"], "done": True, "done_reason": "unload"}])
                o = body.get("options") or {}
                key = (o.get("num_ctx", 4096), o.get("num_batch", 512), body.get("shift", True))
                if (srv.runner, srv.tag) != (key, body["model"]):
                    srv.start(body["model"], key)
                if not body.get("prompt") and "messages" not in body:
                    return self._send([{"model": body["model"], "done": True, "done_reason": "load"}])
                return self._send([{"response": '{"faithfulness": 4}', "done": False},
                                   {"response": "", "done": True, "done_reason": "stop", "prompt_eval_count": 5,
                                    "eval_count": 3, "load_duration": 1_000_000}])

        self.http = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.http.server_address[1]}"
        threading.Thread(target=self.http.serve_forever, daemon=True).start()

    def start(self, tag: str, key: tuple, write_block: bool | None = None):
        """A runner start as the log shows it (laptop server-2.log line 17, flags only). self.bad changes what the
        line prints for -c, -np or -b, and nothing else (KV-cache lines and /api/ps keep the key's context)."""
        ctx, batch, shift = key
        self.n += 1
        c_, np_, b_ = self.bad.get("c", ctx), self.bad.get("np", 1), self.bad.get("b", batch)
        flags = f"-c {c_} -np {np_} --log-verbosity 4 --flash-attn auto -b {b_} -ub {batch}" + (
            " --context-shift --keep 4" if shift else "")
        lines = [f'time=2026-10-16T20:00:{self.n:02d}.000+02:00 level=INFO source=llama_server.go:436 '
                 f'msg="starting llama-server" cmd="/opt/ollama/llama-server --model /m/blobs/sha256-'
                 f'{self.n:012x}{"0" * 52} --port 5{self.n:04d} --host 127.0.0.1 {flags}"']
        if self.write_block if write_block is None else write_block:
            lines += [f"llama_kv_cache: size = 20480.00 MiB ({ctx:6d} cells,  40 layers,  1/1 seqs), "
                      "K (q8_0): 10240.00 MiB, V (q8_0): 10240.00 MiB",
                      f"srv    load_model: initializing, n_slots = 1, n_ctx_slot = {ctx}, kv_unified = 'false'"]
        with self.log.open("a") as fh:
            fh.write("\n".join(lines) + "\n")
        self.runner, self.tag = key, tag

    def start_embedding(self, tag: str):
        """An embedding runner's start (Studio serve_11451.log, 15 October 15:52:07, bge-m3: -c 8192 -np 1 --embedding
        -b 2048), its own blob; /api/ps then holds tag beside the job's model."""
        self.n += 1
        with self.log.open("a") as fh:
            fh.write(f'time=2026-10-16T20:01:{self.n:02d}.000+02:00 level=INFO source=llama_server.go:436 '
                     f'msg="starting llama-server" cmd="/opt/ollama/llama-server --model /m/blobs/sha256-'
                     f'{self.n:012x}{"0" * 52} --port 6{self.n:04d} --host 127.0.0.1 -c 8192 -np 1 --log-verbosity 4 '
                     f'--cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on --embedding -b 2048 -ub 2048 '
                     f'--context-shift --keep 4"\n')
        self.extra[tag] = True

    def close(self):
        self.http.shutdown()


tmp = Path(tempfile.mkdtemp(prefix="check_job_"))


def server(name: str, **kw) -> Server:
    d = tmp / name
    d.mkdir()
    return Server(d, **kw)


# ---------------------------------------------------------------- 1. the load request is what a call sends

for model, kw in ((JUDGE, {"role": "judge"}), ("gpt-oss:20b", {"draw": 1}), ("qwen3-coder:30b", {"draw": 1})):
    call = lock.ollama(model, **kw)
    body, gen = job.load_request(call), call.payload("x")
    chat_keys = {"model": call.model, "options": dict(call.options), **call.fields}   # ollama_client.chat:234
    check(f"1 {model}: the load sends the generate payload's options and fields whole, and no prompt",
          {k: v for k, v in gen.items() if k not in ("prompt", "stream", "system")} == body == chat_keys
          and body["shift"] is False and body["truncate"] is False and "prompt" not in body,
          json.dumps({k: v for k, v in body.items() if k != "options"}))
old_load = job.load_request(lock.ollama(JUDGE, role="judge"))
m_load = mutant(job, '    return {"model": call.model, "options": dict(call.options), **call.fields}',
                '    return {"model": call.model, "keep_alive": call.fields["keep_alive"], '
                '"options": {k: call.options[k] for k in ("num_ctx", "num_batch")}}')
check("1 mutant (job.py:45-46 before D80): the old load request lacks shift and truncate",
      "shift" not in m_load.load_request(lock.ollama(JUDGE, role="judge")) and "shift" in old_load)

# ---------------------------------------------------------------- 2. runner_flags

LAPTOP = ('/Applications/Ollama.app/Contents/Resources/llama-server --model /Users/v/.ollama/models/blobs/sha256-'
          'c580819bed79c92d01a42227bd6d8fd66b9ec60d5329f5eb73f812f156af7807 --port 52164 --host 127.0.0.1 --no-webui '
          '--offline -c 131072 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template '
          'chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4')
BEELINK = ('C:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\lib\\ollama\\llama-server.exe --model '
           'C:\\Users\\Valerio\\.ollama\\models\\blobs\\sha256-33af3142213a0000 --port 61000 -c 131072 -np 1 '
           '--flash-attn on -b 1024 -ub 1024')
check("2 runner_flags reads the laptop line (server-2.log:17)", cs.runner_flags(LAPTOP) ==
      {"blob": "c580819bed79", "c": "131072", "np": "1", "b": "1024", "context_shift": True, "embedding": False},
      cs.runner_flags(LAPTOP))
check("2 runner_flags reads a Beelink-form line (audit components.json, 17:36:12)", cs.runner_flags(BEELINK) ==
      {"blob": "33af3142213a", "c": "131072", "np": "1", "b": "1024", "context_shift": False, "embedding": False})
check("2 -ub alone is not read as -b, --cache-type-k not as -c",
      cs.runner_flags("x --cache-type-k q8_0 -ub 512") == {"blob": None, "c": None, "np": None, "b": None,
                                                           "context_shift": False, "embedding": False})
BEELINK_EMB = ('C:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\lib\\ollama\\llama-server.exe --model '
               'C:\\Users\\Valerio\\.ollama\\models\\blobs\\sha256-daec91ffb5dd0c27411bd71f29932917c49cf529a641d0168496c3a501e3062c '
               '--port 55739 --host 127.0.0.1 --no-webui --offline -c 8192 -np 1 --log-verbosity 4 --no-log-prefix '
               '--no-log-timestamps --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on --embedding -b 2048 -ub 2048 '
               '--context-shift --keep 4')
check("2 runner_flags reads the Beelink's bge-m3 runner line (server log, 15 October 11:59:08) as an embedding runner",
      cs.runner_flags(BEELINK_EMB) == {"blob": "daec91ffb5dd", "c": "8192", "np": "1", "b": "2048",
                                       "context_shift": True, "embedding": True}, cs.runner_flags(BEELINK_EMB))

# ---------------------------------------------------------------- 3. and 4. fresh load, first call, after it

for model, kw in ((JUDGE, {"role": "judge"}), ("gpt-oss:20b", {"draw": 1})):
    s = server(f"ok_{model.replace(':', '_')}")
    s.start("llama3:8b", (8192, 512, True))                           # another model held before the job
    rec = job.fresh_load(s.base, model, s.log, None, None)
    sc = rec["server_check"]["checks"]
    check(f"3 {model}: fresh_load unloads, sends shift and truncate false, and passes every check",
          rec["ok"] is True and rec["unloaded"] == ["llama3:8b"] and rec["load_fields_sent"]["shift"] is False
          and rec["load_fields_sent"]["truncate"] is False and set(sc) == {"version", "settings", "loaded", "kv_cache",
                                                                            "runner"}
          and sc["runner"]["starts"][0]["context_shift"] is False, json.dumps({k: v["ok"] for k, v in sc.items()}))
    first = generate(s.base, lock.ollama(model, **kw), "a real call")
    job.after_first_call(rec, s.log, None, None, first=first)
    af = rec["after_first_call"]
    check(f"3 {model}: the first real call starts no runner; after_first_call passes and is recorded",
          first["status"] == "ok" and af["ok"] is True and len(af["checks"]["runner"]["starts"]) == 1
          and af["first_call"]["request_sha256"] == first["request_sha256"] and rec["ok"] is True)
    s.close()

# mutant: the old load request. The load's runner carries --context-shift (fresh_load fails on "runner") and the first
# call replaces it (after_first_call fails): the two failures F2 describes
s = server("mutant_load")
m_load.check = cs.check
rec = m_load.fresh_load(s.base, JUDGE, s.log, None, None)
check("3 mutant (old load request): fresh_load fails on the --context-shift runner",
      rec["ok"] is False and rec["server_check"]["checks"]["runner"]["ok"] is False
      and rec["server_check"]["checks"]["kv_cache"]["ok"] is True)
generate(s.base, lock.ollama(JUDGE, role="judge"), "a real call")
try:
    job.after_first_call(rec, s.log, None, None)
    raised = False
except job.SetupError:
    raised = True
check("3 mutant (old load request): the first call starts a second runner; after_first_call raises SetupError",
      raised and len(rec["after_first_call"]["checks"]["runner"]["starts"]) == 2 and rec["ok"] is False)
s.close()

# 4. a correct runner replaced after the load (a second start line); the one-runner rule alone catches it
s = server("replaced")
rec = job.fresh_load(s.base, JUDGE, s.log, None, None)
s.start(lock.ollama(JUDGE, role="judge").model, (131072, 1024, False))
try:
    job.after_first_call(rec, s.log, None, None)
    raised = None
except job.SetupError as e:
    raised = str(e)
check("4 a second runner since the load: after_first_call raises SetupError, record ok false",
      raised and "runner" in raised and rec["ok"] is False and rec["after_first_call"]["checks"]["runner"]["ok"] is False)
m_one = mutant(cs, '"ok": flags_ok and (extra_ok or not after_first_call)', '"ok": flags_ok')
chk = m_one.check(s.base, s.log, None, None, JUDGE, log_offset=rec["log_offset"], after_first_call=True)
check("4 mutant (no one-runner rule): the replaced runner passes, so case 4 guards the rule", chk["ok"] is True)
s.close()

# 4. the command line: job.py after-first-call --record, on a load record written by job.py fresh-load
codes = {}
for name, replace_runner in (("cli_ok", False), ("cli_replaced", True)):
    s = server(name)
    recf = tmp / f"{name}.json"
    argv = sys.argv
    try:
        sys.argv = ["job", "fresh-load", "--base", s.base, "--model", JUDGE, "--log", str(s.log), "--record", str(recf)]
        rc_load = job.main()
        if replace_runner:
            s.start(lock.ollama(JUDGE, role="judge").model, (131072, 1024, False))
        sys.argv = ["job", "after-first-call", "--record", str(recf), "--log", str(s.log)]
        codes[name] = (rc_load, job.main(), json.loads(recf.read_text()))
    finally:
        sys.argv = argv
        s.close()
check("4 job.py after-first-call: exit 0 and the result in the record; a replaced runner exits 1, record ok false",
      codes["cli_ok"][:2] == (0, 0) and codes["cli_ok"][2]["after_first_call"]["ok"] is True
      and codes["cli_replaced"][:2] == (0, 1) and codes["cli_replaced"][2]["ok"] is False
      and codes["cli_replaced"][2]["after_first_call"]["checks"]["runner"]["ok"] is False)

# ---------------------------------------------------------------- 5. a pending KV-cache check refuses

s = server("pending", write_block=False)
chk_rec = job.fresh_load(s.base, JUDGE, s.log, None, None)
sc = chk_rec["server_check"]
check("5 a pending KV-cache check fails check_server and fresh_load",
      sc["checks"]["kv_cache"]["ok"] is None and sc["pending"] == ["kv_cache"] and sc["ok"] is False
      and chk_rec["ok"] is False)
OLD_RULE = ('    out["ok"] = all(x["ok"] is True for x in c.values())',
            '    out["ok"] = all(x["ok"] is not False for x in c.values())')
m_pend = mutant(cs, *OLD_RULE)
check("5 mutant (check_server.py:106 before D80): the pending check passes, so case 5 guards the rule",
      m_pend.check(s.base, s.log, None, None, JUDGE, log_offset=chk_rec["log_offset"])["ok"] is True)
m_job = mutant(job, "from experiments.runner.check_server import check", "check = None")
m_job.check = m_pend.check
check("5 job.py refuses a pending check by itself (with the check_server mutant)",
      m_job.fresh_load(s.base, JUDGE, s.log, None, None)["ok"] is False)
m_job2 = mutant(job, '    rec["ok"] = rec["server_check"]["ok"] is True and not rec["server_check"]["pending"]',
                '    rec["ok"] = rec["server_check"]["ok"]')
m_job2.check = m_pend.check
check("5 mutant (both job.py:50 and check_server.py:106 before D80): the pending load passes",
      m_job2.fresh_load(s.base, JUDGE, s.log, None, None)["ok"] is True)
s.close()

# ---------------------------------------------------------------- 7. a wrong -c, -np or -b fails the runner check

CMP = "{k: first[k] for k in want} == want"                          # check_server's runner flag comparison
for flag, wrong in (("c", 65536), ("np", 4), ("b", 512)):
    s = server(f"wrong_{flag}")
    s.bad = {flag: wrong}
    rec = job.fresh_load(s.base, JUDGE, s.log, None, None)
    sc = rec["server_check"]["checks"]
    check(f"7 a runner started with -{flag} {wrong}: the runner check fails, every other check passes, load not ok",
          sc["runner"]["ok"] is False and sc["runner"]["starts"][0][flag] == str(wrong)
          and all(v["ok"] is True for k, v in sc.items() if k != "runner") and rec["ok"] is False,
          json.dumps({k: v["ok"] for k, v in sc.items()}))
    m_flag = mutant(cs, CMP, f"{{k: first[k] for k in want if k != {flag!r}}} == "
                             f"{{k: v for k, v in want.items() if k != {flag!r}}}")
    chk = m_flag.check(s.base, s.log, None, None, JUDGE, log_offset=rec["log_offset"])
    check(f"7 mutant (-{flag} not compared): the wrong -{flag} passes, so its case guards it", chk["ok"] is True)
    s.close()

# ---------------------------------------------------------------- 6. the jobs call it

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("judge_passages", ROOT / "experiments/scorers/judge_passages.py")
jp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jp)
jp.busy_runners = lambda: None                                 # ps and a sleep; not what is checked here
call = lock.ollama(JUDGE, role="judge")
for name, replace_runner in (("passes", False), ("refuses", True)):
    s = server(f"jp_{name}")
    fl = job.fresh_load(s.base, JUDGE, s.log, None, None)
    path = tmp / f"jp_{name}_fresh_load.json"
    jp._AFTER_FIRST.update(fl=fl, a=types.SimpleNamespace(log=s.log, binary=None, machine=None), path=path)
    if replace_runner:
        s.start(call.model, (131072, 1024, False))
    calls = tmp / f"jp_{name}_calls.jsonl"
    try:
        jp.judge_call(s.base, call, "prompt", True, None, calls, {"variant": "a"})
        out = "returned"
    except SystemExit as e:
        out = str(e)
    written = json.loads(path.read_text())
    if replace_runner:
        check("6 judge_passages: a runner replaced after the load refuses the job (setup error) at the first call",
              out.startswith("REFUSED (setup error)") and written["after_first_call"]["ok"] is False
              and written["ok"] is False and len(calls.read_text().splitlines()) == 1, out[:80])
    else:
        check("6 judge_passages: the first judge call runs after_first_call into the load record, once",
              out == "returned" and written["after_first_call"]["ok"] is True and not jp._AFTER_FIRST
              and len(calls.read_text().splitlines()) >= 1)
    s.close()
m_jp = mutant(types.SimpleNamespace(__name__="judge_passages", __file__=str(ROOT / "experiments/scorers/judge_passages.py")),
              "        if _AFTER_FIRST:                                  # D80 V6",
              "        if False:                                  # D80 V6")
m_jp.busy_runners = lambda: None
s = server("jp_mutant")
fl = job.fresh_load(s.base, JUDGE, s.log, None, None)
m_jp._AFTER_FIRST.update(fl=fl, a=types.SimpleNamespace(log=s.log, binary=None, machine=None), path=tmp / "m.json")
s.start(call.model, (131072, 1024, False))
try:
    m_jp.judge_call(s.base, call, "prompt", True, None, tmp / "m_calls.jsonl", {"variant": "a"})
    out = "returned"
except SystemExit as e:
    out = str(e)
check("6 mutant (judge_call without the hook): the replaced runner goes unrefused", out == "returned")
s.close()


def c5(mod, name: str, replace_on_first_call: bool) -> tuple[int, list[dict]]:
    """check_models main on a stub; replace_on_first_call: a second runner starts at each model's first answer."""
    s = server(name)
    if replace_on_first_call:
        replaced = set()

        class Hook(list):
            def append(self, body):                                    # the handler records every POST here first
                super().append(body)
                if body.get("prompt") and body["model"] not in replaced:
                    replaced.add(body["model"])
                    s.start(body["model"], s.runner)                   # same key: a replacement the log shows
        s.posts = Hook(s.posts)
    out = tmp / f"{name}_out"
    argv = sys.argv
    sys.argv = ["check_models", "--base", s.base, "--log", str(s.log), "--out", str(out)]
    try:
        rc = mod.main()
    finally:
        sys.argv = argv
        s.close()
    prompts = {}                                                       # case 9: the prompted calls per model
    for body in s.posts:
        if body.get("prompt"):
            prompts[body["model"]] = prompts.get(body["model"], 0) + 1
    c5.prompts = prompts
    return rc, [json.loads(x) for x in (out / "loads.jsonl").read_text().splitlines()]


import experiments.runner.check_models as cm  # noqa: E402

rc, loads = c5(cm, "c5_ok", False)
check(f"6 check_models: every model's first answer is followed by a passing after_first_call ({len(loads)} models)",
      rc == 0 and loads and all(x["after_first_call"]["ok"] is True and x["ok"] is True for x in loads))
two = sorted(m for m, n in c5.prompts.items() if n == 2)            # the models with a thinking-off call
check(f"9 check_models: models with a thinking-off mode make 2 calls when nothing is refused ({len(two)} models)",
      two and all(n in (1, 2) for n in c5.prompts.values()), ", ".join(two))
rc, loads = c5(cm, "c5_replaced", True)
check("6 check_models: a runner replaced at the first answer is a setup error for every model, C5 exits 1",
      rc == 1 and loads and all(x["after_first_call"]["ok"] is False and x["ok"] is False for x in loads))
check("9 check_models: after a refused after_first_call no further call is made for that model (one call each)",
      len(c5.prompts) == len(loads) and all(n == 1 for n in c5.prompts.values()), json.dumps(c5.prompts))
m_cm = mutant(cm, '            if "after_first_call" not in load_rec:          # D80 V6',
              '            if False:          # D80 V6')
rc, loads = c5(m_cm, "c5_mutant", True)
check("6 mutant (check_models without the hook): the replaced runners go unreported, C5 exits 0",
      rc == 0 and all("after_first_call" not in x for x in loads))
m_cm2 = mutant(cm, "                    break\n", "                    pass\n")
rc, loads = c5(m_cm2, "c5_mutant_nobreak", True)
check("9 mutant (no break at check_models.py:84): the thinking-off call is made after the refusal",
      rc == 1 and all(c5.prompts.get(m) == 2 for m in two), json.dumps(c5.prompts))

# ---------------------------------------------------------------- 8. start() arms the hook, the first judge_call fires it


def jp_start(mod, name: str) -> tuple:
    """mod.start on a stub server (fresh_load stubbed only for the binary check, which needs the real executable);
    then two judge calls. Returns (after_first_call calls after start, after call 1, after call 2), the hook state
    after start, and the load record file start wrote."""
    s = server(name)
    n = []
    mod.fresh_load = lambda base, model, log, binary, machine: {
        **(r := job.fresh_load(base, model, log, None, None)),
        "server_check": {**r["server_check"], "checks": {**r["server_check"]["checks"], "binary": {
            "ok": True, "sha256": "stub", "lock": "stub", "machine": machine}}}}
    mod.after_first_call = lambda rec, log, binary, machine, first=None: (    # binary: as the fresh_load stub
        n.append(1), job.after_first_call(rec, log, None, None, first=first))[1]
    mod.busy_runners = lambda: None
    mod._AFTER_FIRST.clear()
    out = tmp / f"{name}_out"
    a = types.SimpleNamespace(base=s.base, log=s.log, binary=Path("stub"), machine="macos")
    try:
        _, _, call_, fl_ = mod.start(a, out, "check")
        armed = dict(mod._AFTER_FIRST)
        counts = [len(n)]
        for i in (1, 2):
            mod.judge_call(s.base, call_, f"prompt {i}", True, None, out / "calls.jsonl", {"variant": "a"})
            counts.append(len(n))
    finally:
        s.close()
    files = sorted(out.glob("fresh_load_*.json"))
    return counts, armed, fl_, files, out


counts, armed, fl8, files, out8 = jp_start(jp, "jp_start")
rec8 = json.loads(files[-1].read_text()) if files else {}
first8 = json.loads((out8 / "calls.jsonl").read_text().splitlines()[0])
check("8 judge_passages.start() arms the hook (its load record, args and file); the first judge_call fires it, once",
      counts == [0, 1, 1] and armed.get("fl") is fl8 and armed.get("path") == files[-1] and not jp._AFTER_FIRST
      and rec8.get("after_first_call", {}).get("ok") is True
      and rec8["after_first_call"]["first_call"]["request_sha256"] == first8["request_sha256"], counts)
m_jp2 = mutant(types.SimpleNamespace(__name__="judge_passages", __file__=str(ROOT / "experiments/scorers/judge_passages.py")),
               "    _AFTER_FIRST.update(fl=fl, a=a, path=fl_path)\n", "    pass\n")
counts, armed, _, files, _ = jp_start(m_jp2, "jp_start_mutant")
check("8 mutant (start() without arming): no judge_call runs after_first_call, so case 8 guards the arming",
      counts == [0, 0, 0] and not armed and "after_first_call" not in json.loads(files[-1].read_text()), counts)

# ---------------------------------------------------------------- 10. a job that also embeds (K1 review F3)

EMB = lock.d["scorers"]["embedding"]


def afc(name, steps, also=(EMB,)):
    """A judge load, its first real call, then steps(s); after_first_call with also. (record, error or None)."""
    s = server(name)
    rec = job.fresh_load(s.base, JUDGE, s.log, None, None)
    first = generate(s.base, lock.ollama(JUDGE, role="judge"), "a real call")
    steps(s)
    try:
        job.after_first_call(rec, s.log, None, None, first=first, also=also)
        err = None
    except job.SetupError as e:
        err = str(e)
    s.close()
    return rec, err


rec, err = afc("emb_ok", lambda s: s.start_embedding(EMB))
af = rec["after_first_call"]
check("10 load runner plus one --embedding runner, both models in /api/ps: after_first_call with also passes",
      err is None and af["ok"] is True and af["also"] == [EMB] and [x["embedding"] for x in af["checks"]["runner"]["starts"]]
      == [False, True] and af["checks"]["also_loaded"]["ok"] is True and rec["ok"] is True, err)
rec, err = afc("emb_no_also", lambda s: s.start_embedding(EMB), also=())
check("10 the same server without also fails on the runner check (the race of F3: a healthy RAGAS stopped)",
      err is not None and rec["after_first_call"]["checks"]["runner"]["ok"] is False and "also_loaded" not in
      rec["after_first_call"]["checks"])
rec, err = afc("emb_not_yet", lambda s: None)
check("10 with also, before the embedding runner has started: fails (the launcher waits for the first embedding call)",
      err is not None and rec["after_first_call"]["checks"]["runner"]["ok"] is False
      and rec["after_first_call"]["checks"]["also_loaded"]["ok"] is False)
rec, err = afc("emb_replaced", lambda s: (s.start(lock.ollama(JUDGE, role="judge").model, (131072, 1024, False)),
                                          s.start_embedding(EMB)))
check("10 with also, the load's runner replaced beside the embedding runner (3 starts): fails on the runner check",
      err is not None and rec["after_first_call"]["checks"]["runner"]["ok"] is False
      and len(rec["after_first_call"]["checks"]["runner"]["starts"]) == 3)
rec, err = afc("emb_wrong_kind", lambda s: (s.start(lock.ollama(JUDGE, role="judge").model, (131072, 1024, False)),
                                            s.extra.update({EMB: True})))
check("10 with also, a second runner that is not an embedding runner (the load's replaced): fails on the runner check",
      err is not None and rec["after_first_call"]["checks"]["runner"]["ok"] is False
      and rec["after_first_call"]["checks"]["also_loaded"]["ok"] is True)
m_emb = mutant(cs, 'x["embedding"] and x["np"]', 'x["np"]')
s = server("emb_wrong_kind_mutant")
rec = job.fresh_load(s.base, JUDGE, s.log, None, None)
s.start(lock.ollama(JUDGE, role="judge").model, (131072, 1024, False))
s.extra[EMB] = True
chk = m_emb.check(s.base, s.log, None, None, JUDGE, log_offset=rec["log_offset"], after_first_call=True, also=(EMB,))
s.close()
check("10 mutant (no --embedding requirement): the replaced load runner passes, so the case above guards it",
      chk["ok"] is True)
rec, err = afc("emb_stranger", lambda s: (s.start_embedding(EMB), s.extra.update({"llama3:8b": True})))
check("10 with also, a third model in /api/ps: fails on also_loaded, the runner check passes",
      err is not None and rec["after_first_call"]["checks"]["also_loaded"]["ok"] is False
      and rec["after_first_call"]["checks"]["runner"]["ok"] is True)
try:
    cs.check("http://127.0.0.1:1", tmp / "none.log", also=(EMB,))
    refused = False
except ValueError:
    refused = True
check("10 also without after_first_call, a model and a log offset is refused", refused)
s = server("emb_cli")
recf = tmp / "emb_cli.json"
argv = sys.argv
try:
    sys.argv = ["job", "fresh-load", "--base", s.base, "--model", JUDGE, "--log", str(s.log), "--record", str(recf)]
    rc_load = job.main()
    s.start_embedding(EMB)
    sys.argv = ["job", "after-first-call", "--record", str(recf), "--log", str(s.log), "--also", EMB]
    rc_af = job.main()
    sys.argv = ["job", "after-first-call", "--record", str(recf), "--log", str(s.log)]
    rc_af_no = job.main()
finally:
    sys.argv = argv
    s.close()
check("10 job.py after-first-call --also bge-m3:latest exits 0 on that server, and 1 without --also",
      (rc_load, rc_af, rc_af_no) == (0, 0, 1), (rc_load, rc_af, rc_af_no))

# ---------------------------------------------------------------- 11. D145: an MTP draft context's own KV cache

def kv_block(draft_marker: bool) -> Path:
    f = Path(tempfile.mkdtemp(prefix="check_job_mtp_")) / "server.log"
    f.write_text("llama_kv_cache: size = 4352.00 MiB (131072 cells,  16 layers,  1/1 seqs), K (q8_0): 2176.00 MiB, "
                 "V (q8_0): 2176.00 MiB\n"
                 + ("common_speculative_init_result: creating MTP draft context against the target model 'C:\\b'\n"
                    if draft_marker else "")
                 + "llama_kv_cache: size =  512.00 MiB (131072 cells,   1 layers,  1/1 seqs), K (f16):  256.00 MiB, "
                   "V (f16):  256.00 MiB\n"
                 "srv    load_model: initializing, n_slots = 1, n_ctx_slot = 131072, kv_unified = 'false'\n")
    return f

kv_ok = cs.check("http://127.0.0.1:9", kv_block(True), model=JUDGE, log_offset=0, kv_only=True)["checks"]["kv_cache"]
kv_no = cs.check("http://127.0.0.1:9", kv_block(False), model=JUDGE, log_offset=0, kv_only=True)["checks"]["kv_cache"]
check("11 D145: an f16 cache after the MTP draft marker is recorded as the draft's and the target's q8_0 cache passes; "
      "the same f16 line without the marker fails",
      kv_ok["ok"] is True and kv_ok["mtp_draft_lines"] == [{"cells": 131072, "seqs": "1/1", "k_type": "f16"}]
      and kv_no["ok"] is False, (kv_ok, kv_no))
m_mtp = mutant(cs, 'MTP_DRAFT = "creating MTP draft context against the target model"', 'MTP_DRAFT = "never in a log"')
check("11 mutant (no draft marker recognised): the draft's f16 line fails the check, so case 11 guards the rule",
      m_mtp.check("http://127.0.0.1:9", kv_block(True), model=JUDGE, log_offset=0, kv_only=True)
      ["checks"]["kv_cache"]["ok"] is False)

print(f"{sum(results)} of {len(results)} checks pass; lock sha256 {lock.sha256[:12]}")
sys.exit(0 if all(results) else 1)
