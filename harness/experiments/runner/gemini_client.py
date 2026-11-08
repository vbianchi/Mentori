"""One Gemini call under the lock, streamed, with the record D37 asks for.

    rec = generate(load(), "gemini-3-flash-preview", draw=1, prompt=prompt)   # generator: Google's default thinking
    rec = chat(load(), "gemini-3-flash-preview", draw=1, messages=msgs, tools=tools)

The request carries every value of cfg (temperature, top_p, top_k, max_output_tokens, seed and, for thinking off,
the lowest thinking setting) and nothing else, so Google's defaults apply wherever nothing is sent: thinking on (no
thinking setting), safety settings (none sent, in generate and chat) and, in chat with tools, the function-calling
mode (no toolConfig, so Google's AUTO). Mentori's gemini.py sent neither safety settings nor a toolConfig either.
The seed is lock.gemini(model, draw, thinking, candidate): the draw, or draw * 1000 + k for candidate k (Q32).
A caller's stall_s replaces the lock's; the record then has test_override true and stall_s as used.

The call streams (streamGenerateContent, SSE), so there is no total timeout and no limit before the first chunk;
after it, a gap of [generation] stall_s seconds with no new chunk ends it as "stalled" (Q2). Status: "ok" when
Gemini's finishReason is STOP, "length" when it is MAX_TOKENS (thinking and answer together filled max_output_tokens), otherwise the finishReason in lower
case (recitation, malformed_function_call, ...) or "error" with the HTTP reason. Thinking tokens are recorded apart.

Blocks and empty replies (D83 Q145; Google's enums at ai.google.dev/api/generate-content, read 17 October):
- "blocked": Google blocked the prompt (promptFeedback.blockReason, sent with no candidate) or stopped the answer for
  a content rule (finishReason in BLOCK_FINISH). block_reason is Google's value, block_source "prompt" or "answer";
  stop_reason stays the finishReason as sent (None for a blocked prompt).
- "empty": no answer text (blank once stripped) and no function call, ended either by finishReason STOP (stop_reason
  "STOP"; before Q145 stored as "ok": 835 gemini-2.5-pro step calls in Figure 6, COUNTERCHECKS.md:370-374) or by a
  stream that closed cleanly after at least one chunk with no finishReason, no block reason and no part at all
  (stop_reason None; D89, Q145 O3: before D89 status "error", "the stream ended without a finishReason"; the shape of
  the 44 G6 calls and the G1 verified pass on 19_hpai_canada_TE3, every one with 0 parts, the card's "replies from
  Gemini with no text and no reason").
- A stream that ends with no finishReason and no block but holds any part (text, a thought, a signature or a function
  call: cut short), or that sent no chunk at all, stays "error" ("the stream ended without a finishReason"), with what
  Google did send kept beside it.
What a caller does with these is the caller's; this client only labels and records. The lock adapter and the authors'
RLM adapter return (D89, D90): a blocked or empty reply as empty text (EMPTY_TEXT_STATUSES); a recitation stop (D90
Q1), a malformed_function_call or malformed_response reply (D90 Q2) and a reply ended for language, other,
unexpected_tool_call or too_many_tool_calls (D92 Q188) with what the stream held (PASSED_ON_STATUSES).
Mentori's submitted Gemini client read no finishReason before it took the reply: chat_completion passed on every text
part and function call the reply held (models/gemini.py:327-347), generate_completion response.text or ""
(:166-176), "" with an empty_reason when nothing was there (:348-365, :46-110), never an error.
Every record carries session_id, code_commit and code_dirty (D92 Q199; ollama_client.provenance). Every record keeps
prompt_feedback (the last promptFeedback in the stream, as sent, else None), last_candidates (the last chunk's
candidates, as sent, parts included) and finish_message (the candidate's finishMessage, else None), so a later case
explains itself instead of being guessed at analysis time.

chat takes Ollama/OpenAI-shaped messages and maps them (G3, Q28): every system message goes into systemInstruction
(joined by a blank line, in order), user -> role "user", assistant -> role "model" with its text and one
functionCall part per tool call, or, when the message carries "_gemini_parts", those parts sent unchanged (thought
signatures included); tool -> role "user" with one functionResponse part {"name", "response": {"result": content}},
one turn per tool message and no id, as Mentori's gemini.py _build_contents sends them. Also as Mentori: a model turn
with no text and no tool call is sent as the text "[Empty]", a user turn with no text as " ". Tools in Ollama/OpenAI
function shape become functionDeclarations, their parameters sent as "parameters", unchanged.

Both record: text (non-thought text parts), thinking_text (the thought parts' text; Gemini returns it only when
includeThoughts is set, which the lock does not send), tool_calls (functionCall parts as {"id", "name",
"arguments"}, id as Gemini returned it, else None), raw_parts (every part of every chunk, as returned, in order, for
a caller to echo back as "_gemini_parts"). raw_parts keeps thought parts, so a caller that echoes them sends any
thought text back unchanged, as Google asks for thought signatures. request_sha256 is the sha256 of the exact bytes
posted; error_body is Google's whole error reply (an HTTP error's body, or the error line in the stream).

Retries (Q29): HTTP 429, 500 and 503 only, only when no chunk has arrived, 5 attempts at most, waiting
2, 4, 8, 16 s before attempts 2 to 5. Every attempt is in rec["attempts"] (attempt, waited_before_s, http_code,
status, error, error_body, wall_s). An error after the first chunk is never retried. wall_s covers every attempt
and wait; first_chunk_s is counted from the start of the attempt that streamed.

The key is read from GEMINI_API_KEY, else from ~/.config/mentori-runs/keys.env; it is never written to a record.
"""

from __future__ import annotations

import copy
import hashlib
import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

from experiments.runner.ollama_client import _arm, provenance

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"
KEYS = Path.home() / ".config" / "mentori-runs" / "keys.env"   # one file per machine, outside every repository, mode 600
RETRY_CODES = (429, 500, 503)
BACKOFF_S = (2, 4, 8, 16)                  # waits before attempts 2, 3, 4, 5
# D83 Q145: the finishReasons Google gives for an answer stopped by a content rule (safety, blocklist, prohibited
# content, personal data, image safety, the escalation filter). RECITATION keeps its own status, grouped with the
# blocks when failures are counted (D89, Q145 O1; experiments/LIST.md Rule 10).
BLOCK_FINISH = ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY", "IMAGE_PROHIBITED_CONTENT",
                "ESCALATION")
# D89 (Q145 O3): the statuses a caller returns to the system as empty text (no text, no tool call, no parts to echo
# for a block; an empty reply's own blank text), as Mentori's submitted Gemini client returned a reply with no text
# and no function call (models/gemini.py:166-176, :348-365), never an error
EMPTY_TEXT_STATUSES = ("empty", "blocked")
# D90 (Q1, Q2): the statuses a caller returns with what the stream held (text, thought text, function calls, parts):
# a recitation stop passes on the text Google sent before stopping (Q1); a malformed reply goes on as the submitted
# client took it, every text part and function call the reply held (models/gemini.py:327-347), "" when it held none
# (Q2). D92 Q188 (audit F28): the same for the four other reasons Google gives for ending a reply, language, other,
# unexpected_tool_call and too_many_tool_calls (ai.google.dev/api/generate-content FinishReason, read 18 October), by
# the same argument: the submitted client read no finishReason before it took the reply. The record keeps the status,
# the finishReason and finishMessage. Every other status a finishReason gives (finish_reason_unspecified, image_other,
# no_image, image_recitation, missing_thought_signature, pup_limited_disabled, continuation) still raises in the
# callers, as do error and stalled.
PASSED_ON_STATUSES = ("recitation", "malformed_function_call", "malformed_response",
                      "language", "other", "unexpected_tool_call", "too_many_tool_calls")
OTHER_REASON_STATUSES = ("language", "other", "unexpected_tool_call", "too_many_tool_calls")   # D92 Q188
RETURNED_STATUSES = EMPTY_TEXT_STATUSES + PASSED_ON_STATUSES   # every status a caller returns besides ok and length


def raised_before_d89(rec: dict) -> bool:
    """A reply that raised before D89 and now returns to the caller: blocked, recitation, malformed_function_call,
    malformed_response (D90), language, other, unexpected_tool_call, too_many_tool_calls (D92 Q188), or an "empty"
    reply that ended with no finishReason (status "error" before D89). The
    sub-call failure counters (the Mentori RLM's sub_calls_failed, which keeps it out of the quality gate's
    sub_calls_ok, and the authors' RLM's calls.sub_failed) count these as they did before D89 and D90; the decisions
    changed what the system receives, not what those counters count (Rule 10 counts each as a failed call; the gate
    counts successful sub-calls, Q3 D68). Whether a no-finishReason empty reply should count toward the gate is
    proposed, not done. A STOP "empty" reply returned "" before D89 too and is not one of these."""
    st = rec.get("status")
    return st in ("blocked",) + PASSED_ON_STATUSES or (st == "empty" and rec.get("stop_reason") is None)
_open = urllib.request.urlopen             # the HTTP layer; check_gemini replaces it with a fake
_sleep = time.sleep


def key(name: str) -> str:
    """An API key from the environment, else from KEYS (NAME=value lines). Shared with the Anthropic client."""
    k = os.environ.get(name)
    if not k and KEYS.exists():
        for line in KEYS.read_text().splitlines():
            if line.startswith(name + "="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        raise RuntimeError(f"no {name} in the environment or in {KEYS}")
    return k


def _key() -> str:
    return key("GEMINI_API_KEY")


def generation_config(cfg: dict) -> dict:
    """The lock's Gemini settings in the REST API's field names."""
    g = {"temperature": cfg["temperature"], "topP": cfg["top_p"], "topK": cfg["top_k"],
         "maxOutputTokens": cfg["max_output_tokens"], "seed": cfg["seed"]}
    t = cfg.get("thinking_config")
    if t is not None:
        g["thinkingConfig"] = ({"thinkingLevel": t["thinking_level"]} if "thinking_level" in t
                               else {"thinkingBudget": t["thinking_budget"]})
    return g


def function_declarations(tools: list[dict]) -> list[dict]:
    """Ollama/OpenAI tools ({"type": "function", "function": {...}} or the bare function dict) as Gemini
    functionDeclarations; name, description and parameters are copied unchanged."""
    out = []
    for t in tools:
        f = t.get("function", t)
        if not f.get("name"):
            raise ValueError(f"a tool without a name: {t!r}")
        d = {"name": f["name"]}
        for k in ("description", "parameters"):
            if f.get(k) is not None:
                d[k] = f[k]
        out.append(d)
    return out


def _args(a):
    """OpenAI sends arguments as a JSON string, Ollama as an object; Gemini takes the object."""
    return json.loads(a) if isinstance(a, str) else (a if a is not None else {})


def to_contents(messages: list[dict]) -> tuple[dict | None, list[dict]]:
    """Ollama/OpenAI messages as (systemInstruction, contents). Raises ValueError on what it cannot map
    (an unknown role, images, a tool message whose function name cannot be found), never drops it."""
    system, contents, names_by_id = [], [], {}
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if m.get("images"):
            raise ValueError("images in a message are not mapped for Gemini yet")
        if role == "system":
            system.append(content or "")
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content or " "}]})       # Mentori's placeholder
        elif role == "assistant":
            for tc in m.get("tool_calls") or []:
                if tc.get("id"):
                    names_by_id[tc["id"]] = tc.get("function", tc).get("name")
            if m.get("_gemini_parts"):
                parts = m["_gemini_parts"]                         # as Gemini returned them, signatures included
            else:
                parts = [{"text": content}] if content else []
                for tc in m.get("tool_calls") or []:
                    f = tc.get("function", tc)
                    parts.append({"functionCall": {"name": f["name"], "args": _args(f.get("arguments"))}})
                if not parts:
                    parts = [{"text": "[Empty]"}]                  # Mentori's placeholder
            contents.append({"role": "model", "parts": parts})
        elif role == "tool":
            name = m.get("name") or m.get("tool_name") or names_by_id.get(m.get("tool_call_id"))
            if not name:
                raise ValueError(f"a tool message with no function name: {m!r}")
            contents.append({"role": "user", "parts": [{"functionResponse": {"name": name,
                                                                             "response": {"result": content}}}]})
        else:
            raise ValueError(f"no Gemini mapping for role {role!r}")
    si = {"parts": [{"text": "\n\n".join(system)}]} if system else None
    return si, contents


def _http_error(e: urllib.error.HTTPError) -> tuple[str, str]:
    """(error, error_body): "HTTP code: Google's message", and the whole reply body as received."""
    body = e.read().decode("utf-8", "replace")
    msg = body
    try:
        msg = json.loads(body).get("error", {}).get("message", body)
    except (ValueError, AttributeError):
        pass
    return f"HTTP {e.code}: {msg}", body


def _attempt(req, rec: dict, stall_s: float, out: dict) -> tuple[int | None, str | None]:
    """One streamed request. Fills out (text, thought, calls, raw, last) and rec; returns (http_code, error) of an
    HTTP error, else (None, None)."""
    t0 = time.time()
    try:
        with _open(req, timeout=None) as r:                       # no limit before the first chunk (Q2)
            for raw in r:
                if rec["first_chunk_s"] is None:
                    rec["first_chunk_s"] = round(time.time() - t0, 3)
                    _arm(r, stall_s)
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                chunk = json.loads(line[5:])
                if "error" in chunk:                               # an error sent inside the stream
                    err = chunk["error"]
                    rec.update(status="error", error=f"in stream: {err.get('code')} {err.get('message', err)}"
                               if isinstance(err, dict) else f"in stream: {err}", error_body=line[5:].strip())
                    break
                if chunk.get("promptFeedback") is not None:          # Q145: Google's word on the prompt, kept
                    rec["prompt_feedback"] = chunk["promptFeedback"]
                if chunk.get("candidates") is not None:
                    rec["last_candidates"] = chunk["candidates"]
                cand = (chunk.get("candidates") or [{}])[0]
                if cand.get("finishMessage") is not None:
                    rec["finish_message"] = cand["finishMessage"]
                for p in (cand.get("content") or {}).get("parts") or []:
                    out["raw"].append(p)
                    if "functionCall" in p:
                        fc = p["functionCall"]
                        out["calls"].append({"id": fc.get("id"), "name": fc.get("name"),
                                             "arguments": fc.get("args", {})})
                    elif p.get("thought"):
                        out["thought"].append(p.get("text", ""))
                    else:
                        out["text"].append(p.get("text", ""))
                if cand.get("finishReason"):
                    rec["stop_reason"] = cand["finishReason"]
                rec["model_version"] = chunk.get("modelVersion", rec["model_version"])
                out["last"] = chunk
    except urllib.error.HTTPError as e:
        err, body = _http_error(e)
        rec.update(status="error", error=err, error_body=body)
        return e.code, rec["error"]                                # _call retries it only before the first chunk
    except (socket.timeout, TimeoutError):
        rec.update(status="stalled", error=f"no new chunk for {stall_s:.0f} s")
    except (urllib.error.URLError, OSError, http.client.HTTPException, ValueError, AttributeError, TypeError) as e:
        # refused, reset, a stream cut mid-chunk (IncompleteRead), a bad JSON line, a chunk of the wrong shape
        rec.update(status="error", error=f"{type(e).__name__}: {e}")
    finally:
        out["attempt_s"] = round(time.time() - t0, 3)
    return None, None


def _call(model: str, payload: dict, rec: dict, stall_s: float) -> dict:
    """Sends payload with the Q29 retry rule and completes rec."""
    data = json.dumps(payload).encode()
    rec["request_sha256"] = hashlib.sha256(data).hexdigest()       # the exact bytes posted
    req = urllib.request.Request(API.format(model=model), data=data,
                                 headers={"Content-Type": "application/json", "x-goog-api-key": _key()})
    t0 = time.time()
    out = {}
    for n in range(1, len(BACKOFF_S) + 2):
        wait = BACKOFF_S[n - 2] if n > 1 else 0
        if wait:
            _sleep(wait)
        out = {"text": [], "thought": [], "calls": [], "raw": [], "last": None}
        rec.update(status=None, error=None, error_body=None, prompt_feedback=None, last_candidates=None,
                   finish_message=None)
        code, err = _attempt(req, rec, stall_s, out)
        rec["attempts"].append({"attempt": n, "waited_before_s": wait, "http_code": code, "status": rec["status"]
                                or "streamed", "error": rec["error"], "error_body": rec["error_body"],
                                "wall_s": out["attempt_s"]})
        if code not in RETRY_CODES or rec["first_chunk_s"] is not None:
            break
    rec["wall_s"] = round(time.time() - t0, 3)
    rec.update(text="".join(out["text"]), thinking_text="".join(out["thought"]), tool_calls=out["calls"],
               raw_parts=out["raw"])
    if out["last"] is not None:
        u = out["last"].get("usageMetadata") or {}
        rec.update(prompt_tokens=u.get("promptTokenCount"), output_tokens=u.get("candidatesTokenCount"),
                   thinking_tokens=u.get("thoughtsTokenCount"), total_tokens=u.get("totalTokenCount"))
    if rec["status"] is None:
        sr = rec["stop_reason"]
        blocked = (rec["prompt_feedback"] or {}).get("blockReason")
        if blocked:                                                 # Q145: the prompt was blocked, no candidate
            rec.update(status="blocked", block_reason=blocked, block_source="prompt",
                       error=f"Google blocked the prompt: {blocked}"
                       + (f" ({rec['prompt_feedback']['blockReasonMessage']})"
                          if rec["prompt_feedback"].get("blockReasonMessage") else ""))
        elif sr in BLOCK_FINISH:                                    # Q145: the answer was stopped by a content rule
            rec.update(status="blocked", block_reason=sr, block_source="answer",
                       error=f"Google stopped the answer: {sr}"
                       + (f" ({rec['finish_message']})" if rec["finish_message"] else ""))
        elif sr == "STOP" and not rec["text"].strip() and not rec["tool_calls"]:
            rec["status"] = "empty"                                 # Q145: STOP with nothing in it, once "ok"
        elif sr is None and out["last"] is not None and not out["raw"]:
            rec["status"] = "empty"                                 # D89: no finishReason, no part at all, once "error"
        else:
            rec["status"] = ("ok" if sr == "STOP" else "length" if sr == "MAX_TOKENS"
                             else sr.lower() if sr else "error")
        if sr is None and not blocked and rec["status"] == "error":
            rec["error"] = "the stream ended without a finishReason"
    rec["attempts"][-1].update(status=rec["status"], error=rec["error"])
    return rec


def _settings(lock, model, draw, thinking, candidate, stall_s, test_override_cfg) -> tuple[dict, float, bool]:
    """(cfg, stall_s, test_override): cfg from lock.gemini unless test_override_cfg (a check script's deliberate
    change); stall_s from [generation] unless the caller passes another value. Either override is recorded."""
    cfg = test_override_cfg if test_override_cfg is not None else lock.gemini(model, draw, thinking, candidate)
    locked = lock.d["generation"]["stall_s"]
    stall = stall_s if stall_s is not None else locked
    return cfg, stall, test_override_cfg is not None or stall != locked


def _record(model, draw, candidate, thinking, gen, override, stall_s, lock, passages) -> dict:
    return {"model": model, "provider": "gemini", "draw": draw, "candidate": candidate, "thinking": thinking,
            "options_sent": gen, "test_override": override, "stall_s": stall_s, "system_sent": None,
            "request_sha256": None, "lock_sha256": lock.sha256, "passages": passages,
            "status": None, "stop_reason": None, "error": None, "error_body": None,
            "prompt_feedback": None, "last_candidates": None, "finish_message": None, "block_reason": None,
            "block_source": None,
            "text": "", "thinking_text": "", "tool_calls": [], "raw_parts": [], "model_version": None,
            "prompt_tokens": None, "output_tokens": None, "thinking_tokens": None, "total_tokens": None,
            "wall_s": None, "first_chunk_s": None, "attempts": [], "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            **provenance()}                                        # D92 Q199: session_id, code_commit, code_dirty


def generate(lock, model: str, draw: int, prompt: str, thinking: bool | str | None = None, system: str | None = None,
             passages: list | None = None, stall_s: float | None = None, test_override_cfg: dict | None = None,
             candidate: int | None = None) -> dict:
    """The settings come from lock.gemini(model, draw, thinking, candidate); test_override_cfg (a check script's
    deliberate change) replaces them and is written into the record."""
    cfg, stall_s, override = _settings(lock, model, draw, thinking, candidate, stall_s, test_override_cfg)
    gen = generation_config(cfg)
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gen}
    if system is not None:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    rec = _record(model, draw, candidate, thinking, gen, override, stall_s, lock, passages)
    rec["system_sent"] = system
    return _call(model, payload, rec, stall_s)


def chat(lock, model: str, draw: int, messages: list[dict], tools: list[dict] | None = None,
         thinking: bool | str | None = None, passages: list | None = None, stall_s: float | None = None,
         test_override_cfg: dict | None = None, candidate: int | None = None) -> dict:
    """Multi-turn generateContent with optional function calling. Settings as generate. The record adds
    contents_sent and tools_sent (the request's contents and functionDeclarations, whole, as copies, so a caller
    that later changes its messages does not change the record)."""
    cfg, stall_s, override = _settings(lock, model, draw, thinking, candidate, stall_s, test_override_cfg)
    gen = generation_config(cfg)
    si, contents = to_contents(messages)
    payload = {"contents": contents, "generationConfig": gen}
    if si is not None:
        payload["systemInstruction"] = si
    decls = function_declarations(tools) if tools else None
    if decls:
        payload["tools"] = [{"functionDeclarations": decls}]
    rec = _record(model, draw, candidate, thinking, gen, override, stall_s, lock, passages)
    rec.update(system_sent=si["parts"][0]["text"] if si else None, contents_sent=copy.deepcopy(contents),
               tools_sent=copy.deepcopy(decls))
    return _call(model, payload, rec, stall_s)
