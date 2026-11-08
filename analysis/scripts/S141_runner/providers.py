"""S141 step 1.2 — the provider layer. Every call returns what was sent and what came back.

This is where Rule 3 is actually earned. The archive's accounting is not merely incomplete, it is
four different quantities sharing one column name (`exp1:228,333,415,428`): a word count for
single_pass, `llm_calls * 1500` for multi_hop, a real counter for RLM, and literal `0` for
verified_pass. Nothing records which. On the Gemini path, `gemini.py:181-184` reads only prompt and
candidate counts and coerces a missing one to zero with `or 0`, so a reasoning-heavy call is stored
as though it were cheap, and an answer whose count the provider omitted is stored as zero output.

So every provider here returns the same `CallRecord`, and the record distinguishes three states that
the archive collapses into one: a value the provider gave us, a value it omitted, and zero.

What is recorded on every call, without exception:

  options_sent      the dict as actually sent, not as declared. The pre-registration's own sampling
                    table is wrong in three places, so declared values are not evidence
  finish_reason     ollama `done_reason`, gemini `finishReason`, anthropic `stop_reason`
  tokens            prompt / completion / reasoning / total with a provenance label
  durations         ollama's four server-side timings, absent elsewhere and marked so
  latency_s         wall clock measured here, which is the only timing comparable across providers
  raw               the entire response. Disk is cheaper than a repeat run

Nothing in this module edits the archive. The Ollama and Gemini providers speak to the same HTTP
endpoints the harness speaks to, with the same payload shape; the Anthropic provider is new code,
which is the one addition the handoff permits.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .store import ABSENT, MEASURED, PARTIAL

GENERATION_TIMEOUT_S = 1800.0   # pitfall 18. The archive's 300 s is unreachable from the router.

# The date, pinned (Q31, Valerio, 10 October 2026). These models' Ollama templates write today's date (and
# yesterday's) into a built-in system prompt whenever a request carries none, so a judge call made on another day
# reads different text. Each such call now carries that same built-in system prompt with the dates fixed at
# 10 and 9 October 2026, read from data/judge_system_prompts/ (extracted from the templates of Ollama 0.40.2). On
# 10 October this renders exactly what the template rendered by default: checked on the Mac Studio (:11460),
# equal prompt token counts and identical text, devstral 3 of 3. gpt-oss puts the date in a header a system
# message cannot replace; it is pinned by its own model copy (S373 JUDGES). MENTORI_JUDGE_DATE_UNPINNED=1 turns
# the pin off, for the date test only (S377 date11oct).
PINNED_DATE = "2026-10-10"
_PIN_DIR = Path(__file__).resolve().parents[2] / "data" / "judge_system_prompts"
PINNED_SYSTEM_MODELS = ("devstral-small-2:24b", "ministral-3:3b", "ministral-3:8b", "ministral-3:14b")
_pinned_cache: dict[str, str] = {}


def pinned_system(model: str) -> str | None:
    """The built-in system prompt of `model` with the date pinned, or None when no pin applies."""
    if model not in PINNED_SYSTEM_MODELS or os.environ.get("MENTORI_JUDGE_DATE_UNPINNED") == "1":
        return None
    if model not in _pinned_cache:
        _pinned_cache[model] = (_PIN_DIR / f"{model.replace(':', '_')}.date-{PINNED_DATE}.txt").read_text()
    return _pinned_cache[model]


@dataclass
class CallRecord:
    """One provider call. Complete enough to audit without re-running it."""

    provider: str
    model: str
    options_sent: dict[str, Any]
    timeout_s: float
    latency_s: float
    ok: bool
    text: str | None = None
    empty_completion: bool = False
    finish_reason: str | None = None
    length_capped: bool = False          # P3: the cap actually bound on this call
    model_version: str | None = None     # resolved id; for cloud models this is the digest analogue
    tokens: dict[str, Any] = field(default_factory=dict)
    durations: dict[str, Any] = field(default_factory=dict)
    error: str | None = None             # an error CLASS. Never "".
    raw: dict[str, Any] = field(default_factory=dict)

    def as_row_fields(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "gen_model_called": self.model,
            "model_version": self.model_version,
            "options_sent": self.options_sent,
            "timeout_s": self.timeout_s,
            "latency_s": round(self.latency_s, 3),
            "answer": self.text,
            "empty_completion": self.empty_completion,
            "finish_reason": self.finish_reason,
            "length_capped": self.length_capped,
            "tokens": self.tokens,
            "server_durations": self.durations,
            **({"error": self.error} if self.error else {}),
        }


def _post(url: str, payload: dict, headers: dict, timeout: float) -> tuple[int, dict, str | None]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.load(r), None
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        try:
            return e.code, json.loads(body), f"HTTPError:{e.code}"
        except Exception:
            return e.code, {"error": body}, f"HTTPError:{e.code}"
    except TimeoutError:
        return 0, {}, "Timeout"
    except Exception as exc:  # noqa: BLE001
        # An error CLASS, never an empty string. 229 deposited rows carry `error: ""`, which every
        # aggregator downstream reads as success.
        return 0, {}, f"{type(exc).__name__}"


def _present(d: dict, key: str) -> bool:
    """Absent is not zero. `omitempty` on the ollama side and a missing key on the gemini side both
    mean the provider did not tell us, and both must survive into the record as such."""
    return key in d and d[key] is not None


class OllamaProvider:
    """Speaks to /api/generate exactly as `OllamaClient.generate_completion` does (ollama.py:128-139),
    with the timeout the router cannot pass and full accounting the harness never reads."""

    name = "ollama"

    def __init__(self, base_url: str, keep_alive: str = "24h"):
        self.base_url = base_url.rstrip("/")
        self.keep_alive = keep_alive

    def generate(self, model: str, prompt: str, options: dict[str, Any],
                 think: bool | str = False, timeout: float = GENERATION_TIMEOUT_S) -> CallRecord:
        payload = {"model": model, "prompt": prompt, "stream": False,
                   "options": dict(options), "keep_alive": self.keep_alive, "think": think}
        system = pinned_system(model)
        if system is not None:
            payload["system"] = system
        t0 = time.time()
        status, body, err = _post(f"{self.base_url}/api/generate", payload, {}, timeout)
        latency = time.time() - t0

        if status != 200 or err:
            return CallRecord(self.name, model, dict(options), timeout, latency, ok=False,
                              error=err or f"HTTP{status}", raw=body,
                              tokens={"provenance": ABSENT})

        text = body.get("response", "")
        prompt_tok = body.get("prompt_eval_count") if _present(body, "prompt_eval_count") else None
        out_tok = body.get("eval_count") if _present(body, "eval_count") else None
        missing = [k for k, v in (("prompt", prompt_tok), ("completion", out_tok)) if v is None]

        if missing:
            tokens = {"provenance": PARTIAL, "prompt": prompt_tok, "completion": out_tok,
                      "reasoning": None, "total": None, "missing": missing,
                      "note": "ollama omits a zero count under omitempty"}
        else:
            # Ollama returns no total; the sum is ours and is labelled as such rather than passed
            # off as a provider figure.
            tokens = {"provenance": MEASURED, "prompt": prompt_tok, "completion": out_tok,
                      "reasoning": 0, "total": prompt_tok + out_tok,
                      "total_source": "sum_of_parts", "reasoning_source": "not_applicable"}

        durations = {k: body.get(k) if _present(body, k) else None for k in
                     ("total_duration", "load_duration", "prompt_eval_duration", "eval_duration")}
        durations["units"] = "nanoseconds"

        finish = body.get("done_reason") if _present(body, "done_reason") else None
        return CallRecord(
            self.name, model, dict(options), timeout, latency, ok=True, text=text,
            empty_completion=not text.strip(), finish_reason=finish,
            length_capped=(finish == "length"), model_version=model,
            tokens=tokens, durations=durations, raw=body)


class GeminiProvider:
    """Records the third token bucket the archived client discards.

    Measured on this project: 7 prompt + 1,438 reasoning + 294 completion tokens on a real RAG
    prompt — 83% of billed output invisible to `gemini.py`, which never reads
    `thoughtsTokenCount`."""

    name = "gemini"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, model: str, prompt: str, options: dict[str, Any],
                 timeout: float = GENERATION_TIMEOUT_S) -> CallRecord:
        gen_cfg: dict[str, Any] = {}
        if "num_predict" in options:
            gen_cfg["maxOutputTokens"] = options["num_predict"]
        if "temperature" in options:
            gen_cfg["temperature"] = options["temperature"]
        for k in ("thinkingConfig", "topK", "topP"):
            if k in options:
                gen_cfg[k] = options[k]

        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen_cfg}
        t0 = time.time()
        status, body, err = _post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            payload, {"x-goog-api-key": self.api_key}, timeout)
        latency = time.time() - t0

        if status != 200 or err:
            return CallRecord(self.name, model, gen_cfg, timeout, latency, ok=False,
                              error=err or f"HTTP{status}", raw=body,
                              tokens={"provenance": ABSENT})

        cand = (body.get("candidates") or [{}])[0]
        text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts") or [])
        u = body.get("usageMetadata", {})
        p_tok = u.get("promptTokenCount") if _present(u, "promptTokenCount") else None
        c_tok = u.get("candidatesTokenCount") if _present(u, "candidatesTokenCount") else None
        r_tok = u.get("thoughtsTokenCount") if _present(u, "thoughtsTokenCount") else 0
        t_tok = u.get("totalTokenCount") if _present(u, "totalTokenCount") else None

        missing = [n for n, v in (("prompt", p_tok), ("completion", c_tok), ("total", t_tok))
                   if v is None]
        if missing:
            tokens = {"provenance": PARTIAL, "prompt": p_tok, "completion": c_tok,
                      "reasoning": r_tok, "total": t_tok, "missing": missing,
                      "note": "gemini omits candidatesTokenCount on some thinking calls; "
                              "measured on 2 of 20"}
        else:
            tokens = {"provenance": MEASURED, "prompt": p_tok, "completion": c_tok,
                      "reasoning": r_tok, "total": t_tok, "total_source": "provider"}

        finish = cand.get("finishReason")
        return CallRecord(
            self.name, model, gen_cfg, timeout, latency, ok=True, text=text,
            empty_completion=not text.strip(), finish_reason=finish,
            length_capped=(finish == "MAX_TOKENS"),
            model_version=body.get("modelVersion"),
            tokens=tokens, durations={"provenance": ABSENT, "note": "gemini returns no server timings"},
            raw=body)


class AnthropicProvider:
    """New code — the one addition the handoff permits, and the only call path written from scratch.

    It therefore does what the archived providers fail to do: it accepts an options dict and applies
    it. `ModelRouter.generate` drops options on the gemini branch (`model_router.py:215-221`), which
    is why the reference arm ran at the API default temperature. Claude gets its options, Gemini does
    not, and that asymmetry is recorded per row rather than hidden."""

    name = "anthropic"
    API = "https://api.anthropic.com/v1/messages"
    VERSION = "2023-06-01"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, model: str, prompt: str, options: dict[str, Any],
                 timeout: float = GENERATION_TIMEOUT_S) -> CallRecord:
        sent: dict[str, Any] = {"max_tokens": options.get("num_predict", 8192)}
        if "temperature" in options:
            sent["temperature"] = options["temperature"]
        if "thinking" in options:
            sent["thinking"] = options["thinking"]

        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], **sent}
        t0 = time.time()
        status, body, err = _post(
            self.API, payload,
            {"x-api-key": self.api_key, "anthropic-version": self.VERSION}, timeout)
        latency = time.time() - t0

        if status != 200 or err:
            return CallRecord(self.name, model, sent, timeout, latency, ok=False,
                              error=err or f"HTTP{status}", raw=body,
                              tokens={"provenance": ABSENT})

        text = "".join(b.get("text", "") for b in body.get("content", [])
                       if b.get("type") == "text")
        u = body.get("usage", {})
        p_tok = u.get("input_tokens") if _present(u, "input_tokens") else None
        c_tok = u.get("output_tokens") if _present(u, "output_tokens") else None
        missing = [n for n, v in (("prompt", p_tok), ("completion", c_tok)) if v is None]

        if missing:
            tokens = {"provenance": PARTIAL, "prompt": p_tok, "completion": c_tok,
                      "reasoning": None, "total": None, "missing": missing}
        else:
            tokens = {"provenance": MEASURED, "prompt": p_tok, "completion": c_tok,
                      "reasoning": 0, "total": p_tok + c_tok, "total_source": "sum_of_parts",
                      "reasoning_source": "extended thinking not enabled"}

        stop = body.get("stop_reason")
        return CallRecord(
            self.name, model, sent, timeout, latency, ok=True, text=text,
            empty_completion=not text.strip(), finish_reason=stop,
            length_capped=(stop == "max_tokens"),
            model_version=body.get("model"),   # resolves the alias, e.g. claude-haiku-4-5-20251001
            tokens=tokens,
            durations={"provenance": ABSENT, "note": "anthropic returns no server timings"},
            raw=body)


def build(spec: str, *, gemini_key: str | None = None, anthropic_key: str | None = None,
          ollama_url: str | None = None):
    """Resolve a `provider::model` identifier the way ModelRouter does, plus `anthropic::`."""
    provider, _, model = spec.partition("::")
    if not model:
        raise ValueError(f"model identifier must be 'provider::model', got {spec!r}")
    if provider == "ollama":
        return OllamaProvider(ollama_url or os.environ.get("OLLAMA_BASE_URL",
                                                           "http://127.0.0.1:11434")), model
    if provider == "gemini":
        return GeminiProvider(gemini_key or ""), model
    if provider == "anthropic":
        return AnthropicProvider(anthropic_key or ""), model
    raise ValueError(f"unknown provider: {provider!r}")
