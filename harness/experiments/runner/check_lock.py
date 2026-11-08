"""Checks for experiments/runner/lock.py; it is used for nothing until these pass.

    uv run python -m experiments.runner.check_lock

First it reproduces a known request: the judge call of S440's lock pass, which gave the Studio's scores
on 107 of 107 answers on the Studio, the laptop and (95 of 107) the Beelink. Then it checks that the
lock's refusals fire. D81 (Q136): the retry seed rule computes as stated and is refused without its key, on scratch
locks made from LOCK.toml with and without the line. D85: the second judge (qwen3.8:27b) builds the main judge's request
with its own digest, a model that is neither judge is refused as judge, and qwen3.8 is refused as scorer.
"""

import json
import sys
from pathlib import Path

from experiments.runner.lock import LOCK, Lock, LockError, load

ROOT = Path(__file__).resolve().parents[2]
S440 = ROOT / "findings/recompute/S440_judge_lock_check.jsonl"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def refuses(fn):
    try:
        fn()
    except LockError as e:
        return str(e)
    return None


lock = load()

# 1. reproduce: the options and request fields S440's lock pass sent, row by row
rows = [json.loads(x) for x in S440.read_text().splitlines()]
lock_rows = [r for r in rows if r["pass"] == "lock"]
judge = lock.ollama("devstral-small-2:24b", role="judge")
sent = {json.dumps(r["options"], sort_keys=True) for r in lock_rows}
fields = {json.dumps(r["request_fields"], sort_keys=True) for r in lock_rows}
check("S440 lock pass: one set of options", len(sent) == 1 and len(fields) == 1, f"{len(lock_rows)} rows")
s440 = json.loads(sent.pop())
check("judge options equal S440's apart from num_predict 16,384 (O3)",
      {**s440, "num_predict": 16384} == judge.options and s440["num_predict"] == -1, json.dumps(judge.options))
longest = max(r["output_tokens"] or 0 for r in lock_rows)
check("no S440 judge reply came near 16,384 tokens, so O3 changes none of them", longest < 16384, f"longest {longest}")
want = json.loads(fields.pop())
check("judge truncate and shift equal S440's",
      all(judge.fields[k] == v for k, v in want.items()) and set(want) == {"truncate", "shift"}, json.dumps(want))
check("judge sends think false, as S440's Judge(think=False)", judge.fields.get("think") is False)
sys.path.insert(0, str(ROOT / "scripts"))
from S141_runner.providers import pinned_system  # noqa: E402
check("judge system prompt is S440's date-fixed one", judge.system == pinned_system("devstral-small-2:24b"))
check("devstral as generator also gets it", lock.ollama("devstral-small-2:24b", draw=1).system == judge.system)
check("judge digest is the one S440 loaded",
      {r["model_digest"] for r in lock_rows} == {judge.digest[:12]}, judge.digest[:12])

# 2. per-model values
g = lock.ollama("gemma3:27b", draw=2)
check("gemma3 sampling and seed", g.options == {"num_ctx": 131072, "num_predict": -1, "num_batch": 1024,
      "temperature": 1.0, "top_p": 0.95, "top_k": 64, "min_p": 0.0, "repeat_penalty": 1.0,
      "presence_penalty": 0.0, "seed": 2} and "think" not in g.fields, json.dumps(g.options))
check("llama3:8b at its own context", lock.ollama("llama3:8b", draw=1).options["num_ctx"] == 8192)
check("glm-4.7-flash:bf16 as generator thinks by default (D66), with glm's thinking-mode values",
      lock.ollama("glm-4.7-flash:bf16", draw=1).fields["think"] is True
      and lock.ollama("glm-4.7-flash:bf16", draw=1).options["temperature"] == 0.7)
check("glm-4.7-flash:bf16 with thinking off: think false, glm's ordinary values",
      lock.ollama("glm-4.7-flash:bf16", draw=1, thinking="off").fields["think"] is False
      and lock.ollama("glm-4.7-flash:bf16", draw=1, thinking="off").options["temperature"] == 1.0)
check("gemma3 (no thinking mode) as generator sends no think", "think" not in lock.ollama("gemma3:27b", draw=1).fields)
check("deepseek-r1 as generator always thinks", lock.ollama("deepseek-r1:70b", draw=1).fields["think"] is True)
check("glm-4.7-flash Q4 is refused (D64)", bool(refuses(lambda: lock.ollama("glm-4.7-flash:latest", draw=1))))
sc = lock.ollama("devstral-small-2:24b", role="scorer")
check("scorer sends exactly the judge's request", sc.options == judge.options and sc.fields == judge.fields
      and sc.system == judge.system, json.dumps(sc.options))
go = lock.ollama("gpt-oss:20b", draw=1)
check("gpt-oss:20b runs as its date-fixed copy, at its default medium as generator (D66)", go.model == "gpt-oss:20b-date20261010"
      and go.digest.startswith("41bf45e8998c") and go.fields["think"] == "medium" and go.system is None, go.model)
check("gpt-oss:120b as generator also at its default medium", lock.ollama("gpt-oss:120b", draw=1).fields["think"] == "medium")
check("gpt-oss:20b with thinking off runs at its lowest level, low", lock.ollama("gpt-oss:20b", draw=1, thinking="off").fields["think"] == "low")
check("gpt-oss:20b sampling row still applies", go.options["top_k"] == 0 and go.options["temperature"] == 1.0)
check("gpt-oss:20b thinking on = medium, its default", lock.ollama("gpt-oss:20b", draw=1, thinking=True).fields["think"] == "medium")
check("Gemini thinking on sends no thinking setting", "thinking_config" not in lock.gemini("gemini-2.5-pro", 1, thinking=True))
check("one rule per role (D66): generators default, instruments off",
      lock.d["thinking"]["generator"] == "default" and lock.d["thinking"]["instrument"] == "off")
check("Gemini as generator sends no thinking setting (Google's default)", "thinking_config" not in lock.gemini("gemini-3-flash-preview", 1))
check("an instrument refuses thinking", bool(refuses(lambda: lock.ollama("devstral-small-2:24b", role="judge", thinking="default"))))
gb = lock.ollama("glm-4.7-flash:bf16", draw=1, thinking=True)
check("glm-4.7-flash:bf16 runs with glm's rows (thinking on: 0.7, 1.0)", gb.digest.startswith("b0f42cc1a612")
      and gb.options["temperature"] == 0.7 and gb.options["top_p"] == 1.0 and gb.fields["think"] is True, json.dumps(gb.options))
check("gpt-oss:20b at thinking level high", lock.ollama("gpt-oss:20b", draw=1, thinking="high").fields["think"] == "high")
check("refuses a level the lock does not name", bool(refuses(lambda: lock.ollama("gpt-oss:20b", draw=1, thinking="max"))))
check("the plain gpt-oss:20b build is refused", bool(refuses(lambda: lock.check_digest("gpt-oss:20b", "f38aa0c53da5"))))
q = lock.ollama("qwen3.5:122b", draw=1, thinking=True)
check("qwen3.5:122b thinking-on row", q.options["temperature"] == 0.6 and q.options["presence_penalty"] == 0.0
      and q.fields["think"] is True, json.dumps(q.options))
check("every call: truncate false, shift false", all(
      c.fields["truncate"] is False and c.fields["shift"] is False for c in (judge, g, q)))

# 3. refusals
check("refuses qwen3.5:35b (no digest)", bool(refuses(lambda: lock.ollama("qwen3.5:35b", draw=1))))
check("refuses a generator call without a draw", bool(refuses(lambda: lock.ollama("gemma3:27b"))))
check("refuses another model as judge", bool(refuses(lambda: lock.ollama("gemma3:27b", role="judge"))))
check("refuses thinking where the lock has no thinking-on row",
      bool(refuses(lambda: lock.ollama("gemma3:27b", draw=1, thinking=True))))
check("refuses a digest the lock does not name",
      bool(refuses(lambda: lock.check_digest("gemma3:27b", "1fb5619173ca"))))
check("accepts the digest the lock names", refuses(lambda: lock.check_digest("gemma3:27b", "8dda00f4f636")) is None)
proposed = LOCK.read_bytes().replace(b'status = "agreed"', b'status = "proposed"', 1)
check("refuses a lock that is not agreed", bool(refuses(lambda: Lock(proposed))))
check("Anthropic: the dated model id, temperature 1.0, max_tokens 64000", lock.anthropic("claude-haiku-4-5") == {"model": "claude-haiku-4-5-20251001", "temperature": 1.0, "max_tokens": 64000})
gm = lock.gemini("gemini-3-flash-preview", draw=3, thinking="off")
check("gemini config", gm["thinking_config"] == {"thinking_level": "minimal"} and gm["seed"] == 3
      and gm["max_output_tokens"] == 65536, json.dumps(gm))

# 4. per-candidate seed (Q32, D68): candidate k of a step inside draw d sends d * 1000 + k
c3 = lock.ollama("qwen3-coder:30b", draw=2, candidate=3)
c0 = lock.ollama("qwen3-coder:30b", draw=2)
check("candidate 3 of draw 2 sends seed 2003, no candidate sends 2", c3.options["seed"] == 2003 and c0.options["seed"] == 2
      and c3.candidate == 3 and c0.candidate is None, f"{c3.options['seed']}, {c0.options['seed']}")
check("a candidate changes the seed and nothing else", {**c3.options, "seed": 2} == c0.options and c3.fields == c0.fields)
re = lock.ollama(c3.requested or c3.model, role=c3.role, draw=c3.draw, thinking=c3.thinking, candidate=c3.candidate)
check("a call rebuilt from its own fields, candidate included (as ollama_client._checked does) sends the same request",
      (re.model, re.options, re.fields, re.system) == (c3.model, c3.options, c3.fields, c3.system))
check("the judge refuses a candidate", bool(refuses(lambda: lock.ollama("devstral-small-2:24b", role="judge", candidate=1))))
check("a scorer refuses a candidate", bool(refuses(lambda: lock.ollama("devstral-small-2:24b", role="scorer", candidate=1))))
check("a candidate without a draw is refused, by the candidate rule",
      "candidate" in (refuses(lambda: lock.ollama("qwen3-coder:30b", candidate=1)) or ""))
check("candidates 0, 1000, True and '3' are refused (k is an integer from 1 to 999)",
      all(refuses(lambda k=k: lock.ollama("qwen3-coder:30b", draw=1, candidate=k)) for k in (0, 1000, True, "3")))
check("draws 0, -1, 1000, True and 2.9 are refused, with or without a candidate (d is an integer from 1 to 999)",
      all(refuses(lambda d=d, k=k: lock.ollama("qwen3-coder:30b", draw=d, candidate=k))
          for d in (0, -1, 1000, True, 2.9) for k in (None, 1)))
check("Gemini refuses draw 0 with candidate 3 (it would send seed 3, draw 3's)",
      bool(refuses(lambda: lock.gemini("gemini-3-flash-preview", 0, candidate=3))))
noseed = Lock(LOCK.read_bytes().replace(b'seed = "draw"                  # the draw number (1, 2, 3)', b'seed = "none"', 1))
check("a generator refuses a [generation] seed other than 'draw' (it would send no seed)",
      noseed.d["generation"]["seed"] == "none" and bool(refuses(lambda: noseed.ollama("qwen3-coder:30b", draw=1))))
check("Gemini candidate 3 of draw 2 sends seed 2003, no candidate sends 2",
      lock.gemini("gemini-3-flash-preview", 2, candidate=3)["seed"] == 2003 and lock.gemini("gemini-3-flash-preview", 2)["seed"] == 2)

# 6. D81 (Q136): retry r of a call sends its own seed + 1,000,000 * r ([generation] retry_seed), on scratch locks made
# from LOCK.toml with the line and without it (the coordinator adds the line to LOCK.toml between runs)
import re as _re  # noqa: E402

RETRY_LINE = (b'retry_seed = "seed + 1000000 * retry"   # D81 (Q136): retry r (1 to 3) of a call that failed with a '
              b'transient error sends its own seed + 1000000 * r\n')
_raw = LOCK.read_bytes()
_without = _re.sub(rb"(?m)^retry_seed = .*\n", b"", _raw)
with_retry = Lock(_re.sub(rb'(?m)^think = "off"', lambda m: RETRY_LINE + m.group(0), _without, count=1), LOCK)
without_retry = Lock(_without, LOCK)
check("the scratch locks: one with [generation] retry_seed, one without",
      with_retry.d["generation"].get("retry_seed") == "seed + 1000000 * retry"
      and "retry_seed" not in without_retry.d["generation"], with_retry.sha256[:12])
r1 = with_retry.ollama("qwen3-coder:30b", draw=2, retry=1)
r3c = with_retry.ollama("qwen3-coder:30b", draw=2, candidate=3, retry=3)
first = with_retry.ollama("qwen3-coder:30b", draw=2)
check("retry 1 of draw 2 sends 1000002; retry 3 of candidate 3 of draw 2 sends 3002003; the first try sends 2",
      r1.options["seed"] == 1000002 and r3c.options["seed"] == 3002003 and first.options["seed"] == 2
      and r1.retry == 1 and first.retry is None, f"{r1.options['seed']}, {r3c.options['seed']}")
check("a retry changes the seed and nothing else", {**r1.options, "seed": 2} == first.options
      and (r1.fields, r1.system, r1.model, r1.digest) == (first.fields, first.system, first.model, first.digest))
rr = with_retry.ollama(r3c.requested or r3c.model, role=r3c.role, draw=r3c.draw, thinking=r3c.thinking,
                       candidate=r3c.candidate, retry=r3c.retry)
check("a retried call rebuilt from its own fields (as ollama_client._checked does) sends the same request",
      (rr.model, rr.options, rr.fields, rr.system) == (r3c.model, r3c.options, r3c.fields, r3c.system))
_seeds = {}
for _d in range(1, 1000):
    for _k in [None] + list(range(1, 1000)):
        for _r in (None, 1, 2, 3):
            _seeds[with_retry._seed(_d, _k, _r)] = (_d, _k, _r)
check("every (draw 1-999, candidate none or 1-999, retry none or 1-3) has its own seed, every retry seed above "
      "999,999", len(_seeds) == 999 * 1000 * 4 and min(s for s, v in _seeds.items() if v[2]) == 1000001,
      f"{len(_seeds)} seeds")
e = refuses(lambda: without_retry.ollama("qwen3-coder:30b", draw=2, retry=1))
check("a lock without retry_seed refuses a retry, naming D81", bool(e) and "D81" in e and "retry_seed" in e, e)
check("a lock without retry_seed still sends the first try (seed 2) and a candidate (2003)",
      without_retry.ollama("qwen3-coder:30b", draw=2).options["seed"] == 2
      and without_retry.ollama("qwen3-coder:30b", draw=2, candidate=3).options["seed"] == 2003)
other = Lock(_re.sub(rb'(?m)^think = "off"', lambda m: b'retry_seed = "draw * 1000 + 900 + retry"\n' + m.group(0),
                     _without, count=1), LOCK)
check("a retry_seed rule this reader does not know is refused (the first proposed form, which collides)",
      bool(refuses(lambda: other.ollama("qwen3-coder:30b", draw=2, retry=1))))
check("retries 0, 4, True and '1' are refused (r is an integer from 1 to 3)",
      all(refuses(lambda r=r: with_retry.ollama("qwen3-coder:30b", draw=1, retry=r)) for r in (0, 4, True, "1")))
check("the judge and a scorer refuse a retry number",
      bool(refuses(lambda: with_retry.ollama("devstral-small-2:24b", role="judge", retry=1)))
      and bool(refuses(lambda: with_retry.ollama("devstral-small-2:24b", role="scorer", retry=1))))
check("LOCK.toml as it stands: " + ("has retry_seed" if "retry_seed" in lock.d["generation"] else
      "no retry_seed yet, so a retry is refused until the coordinator adds the line"),
      ("retry_seed" in lock.d["generation"]) == (refuses(lambda: lock.ollama("qwen3-coder:30b", draw=1, retry=1))
                                                  is None))

# 5. [retrieval] (Q20, D68): Mentori's in-process encoders, pinned to a snapshot, local files only
ret = lock.retrieval()
check("[retrieval] names the embedding encoder and the reranker", set(ret) == {"embedding", "reranker"}
      and ret["embedding"]["hf_repo"] == "BAAI/bge-m3" and ret["reranker"]["hf_repo"] == "BAAI/bge-reranker-v2-m3", json.dumps(sorted(ret)))
check("each revision is a 40-hex commit, local_files_only true, a device named",
      all(len(r["revision"]) == 40 and all(ch in "0123456789abcdef" for ch in r["revision"])
          and r["local_files_only"] is True and r["device"] for r in ret.values()))
def retrieval_refused(old: bytes, new: bytes) -> bool:
    return bool(refuses(lambda: Lock(LOCK.read_bytes().replace(old, new, 1)).retrieval()))


rev = ret["embedding"]["revision"].encode()
check("retrieval() refuses revision 'main', local_files_only false and a row that is not a table",
      retrieval_refused(b'revision = "' + rev + b'"', b'revision = "main"')
      and retrieval_refused(b"local_files_only = true", b"local_files_only = false")
      and retrieval_refused(b"[retrieval]\n", b'[retrieval]\nnote = "x"\n'))
from huggingface_hub.constants import HF_HUB_CACHE  # noqa: E402  (honours HF_HOME and HF_HUB_CACHE)
hub = Path(HF_HUB_CACHE)
for role, r in ret.items():
    repo = hub / f"models--{r['hf_repo'].replace('/', '--')}"
    if not repo.exists():       # only a machine that runs Mentori holds the cache (the Studio, the laptop)
        print(f"SKIP {role}: no {repo} on this machine")
        continue
    snap = repo / "snapshots" / r["revision"]
    weights = [f for f in ("pytorch_model.bin", "model.safetensors") if (snap / f).exists()]
    check(f"{role}: this machine's cache holds the lock's snapshot with its weights", bool(weights),
          f"{snap.name[:12]} {', '.join(weights) or 'no weights file'}")
    ref = repo / "refs" / "main"
    main = ref.read_text().strip() if ref.exists() else None
    print(f"INFO {role}: refs/main is {main[:12] if main else None}"
          + ("" if main == r["revision"] else f", not the lock's {r['revision'][:12]} (a pinned load reads the snapshot)"))

# 7. D85 (Valerio, 17 October): qwen3.8:27b, GGUF build, is the second judge; devstral stays the main judge and the
# only scorer. Both judges are instruments at the [judge] settings.
Q38, Q38_DIGEST = "qwen3.8:27b", "aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813"
check("the judges are devstral (main) then qwen3.8:27b (second)", lock.judges() == ("devstral-small-2:24b", Q38),
      repr(lock.judges()))
q8 = lock.ollama(Q38, role="judge")
check("second judge: temperature 0, num_predict 16,384, num_ctx 131,072, num_batch 1,024, no seed",
      q8.options == {"num_ctx": 131072, "num_predict": 16384, "num_batch": 1024, "temperature": 0}, json.dumps(q8.options))
check("second judge sends think false, truncate false, shift false, keep_alive 24h",
      q8.fields == {"truncate": False, "shift": False, "keep_alive": "24h", "think": False}, json.dumps(q8.fields))
check("second judge sends the main judge's options and fields exactly", q8.options == judge.options
      and q8.fields == judge.fields)
check("second judge runs as itself with the GGUF digest, no date-fixed system prompt", q8.model == Q38
      and q8.digest == Q38_DIGEST and q8.system is None and q8.role == "judge" and q8.draw is None, q8.digest[:12])
check("second judge: the GGUF digest is accepted, the Studio's MLX build 47951e4a6661 refused (D47)",
      refuses(lambda: lock.check_digest(Q38, Q38_DIGEST[:12])) is None
      and bool(refuses(lambda: lock.check_digest(Q38, "47951e4a6661"))))
check("a digest prefix under 12 hex characters is refused, 12 and 64 accepted (O1, 17 October)",
      all(refuses(lambda p=p: lock.check_digest(Q38, p)) for p in ("a", Q38_DIGEST[:1], Q38_DIGEST[:11], ""))
      and refuses(lambda: lock.check_digest(Q38, Q38_DIGEST[:12])) is None
      and refuses(lambda: lock.check_digest(Q38, Q38_DIGEST)) is None
      and bool(refuses(lambda: lock.check_digest(Q38, Q38_DIGEST[:12].upper()))))
check("second judge refuses thinking, a candidate and a retry",
      all(refuses(f) for f in (lambda: lock.ollama(Q38, role="judge", thinking="default"),
                               lambda: lock.ollama(Q38, role="judge", candidate=1),
                               lambda: with_retry.ollama(Q38, role="judge", retry=1))))
q8r = lock.ollama(q8.requested or q8.model, role=q8.role, draw=q8.draw, thinking=q8.thinking)
check("a second-judge call rebuilt from its own fields (as ollama_client._checked does) sends the same request",
      (q8r.model, q8r.options, q8r.fields, q8r.system) == (q8.model, q8.options, q8.fields, q8.system))
e = refuses(lambda: lock.ollama("qwen3-coder:30b", role="judge"))
check("a model that is neither judge is refused as judge (qwen3-coder:30b, in [models]), naming both judges",
      bool(e) and "devstral-small-2:24b" in e and Q38 in e, e)
check("qwen3.8 cannot be built as scorer; devstral still can",
      bool(refuses(lambda: lock.ollama(Q38, role="scorer")))
      and refuses(lambda: lock.ollama("devstral-small-2:24b", role="scorer")) is None)
check("qwen3.8 cannot be built as generator (no [sampling.models] row)",
      bool(refuses(lambda: lock.ollama(Q38, draw=1))))
check("qwen3.8 has no [exceptions] row and sends [generation] num_ctx (its context, 262,144 by /api/show on 17 October, "
      "is not read here)",
      Q38 not in lock.d.get("exceptions", {}) and "qwen3.8" not in lock.d.get("exceptions", {})
      and q8.options["num_ctx"] == lock.d["generation"]["num_ctx"])
_no_second = Lock(_re.sub(rb"(?m)^second_model = .*\n", b"", _raw), LOCK)
check("a lock without second_model: one judge, and qwen3.8 is refused as judge",
      _no_second.judges() == ("devstral-small-2:24b",) and bool(refuses(lambda: _no_second.ollama(Q38, role="judge"))))
_same = Lock(_raw.replace(b'second_model = "qwen3.8:27b"', b'second_model = "devstral-small-2:24b"', 1), LOCK)
check("a second_model equal to the main judge is refused", bool(refuses(_same.judges))
      and bool(refuses(lambda: _same.ollama("devstral-small-2:24b", role="judge"))))
_nodigest = Lock(_raw.replace(b'second_model = "qwen3.8:27b"', b'second_model = "qwen3.5:35b"', 1), LOCK)
check("a second judge with no digest in [models] cannot run",
      "no digest" in (refuses(lambda: _nodigest.ollama("qwen3.5:35b", role="judge")) or ""))
_latest = Lock(_raw.replace(b'second_model = "qwen3.8:27b"', b'second_model = "devstral-small-2:24b:latest"', 1), LOCK)
check("a second_model that is the main judge's tag plus ':latest' is refused", bool(refuses(_latest.judges))
      and bool(refuses(lambda: _latest.ollama("devstral-small-2:24b:latest", role="judge"))))
_DEV_DIGEST = lock._run_tag("devstral-small-2:24b")[1]
_alias = Lock(_raw.replace(b'second_model = "qwen3.8:27b"', b'second_model = "devstral-alias:24b"', 1).replace(
    b'\n"qwen3.8:27b"', b'\n"devstral-alias:24b" = { digest = "' + _DEV_DIGEST.encode() + b'", machines = ["beelink"] }'
    b'\n"qwen3.8:27b"', 1), LOCK)
check("a second_model under another tag with the main judge's digest is refused",
      _alias._run_tag("devstral-alias:24b")[1] == _DEV_DIGEST and bool(refuses(_alias.judges))
      and bool(refuses(lambda: _alias.ollama("devstral-alias:24b", role="judge"))))

print(f"{sum(results)} of {len(results)} checks pass; lock sha256 {lock.sha256[:12]}")
sys.exit(0 if all(results) else 1)
