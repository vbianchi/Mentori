"""Checks for experiments/runner/gemini_client.py (offline checks, then live calls to Google, a few hundred tokens each).

    uv run --no-sync python -m experiments.runner.check_gemini [--offline]

--offline runs 1 to 3, 10, 11 and 12 only (no Google call, no key).

Offline (a fake HTTP layer, no network, no key):
1. Message mapping: system messages -> systemInstruction, user -> user, assistant -> model with functionCall parts,
   assistant with _gemini_parts -> those parts unchanged, tool -> functionResponse (name from the message or from the
   tool call id), one turn per tool message, Mentori's placeholders for empty turns, images refused;
   tools -> functionDeclarations.
2. Stream reading: thought text, text, functionCall parts (with their id) and raw parts land in thinking_text, text,
   tool_calls and raw_parts; the request carries the lock's settings, systemInstruction and tools; request_sha256 is
   the hash of the bytes posted; contents_sent is a copy; a caller's stall_s and a candidate are recorded.
3. Retry rule (Q29): 503 then 429 then a stream is retried with waits 2 and 4 s, Google's error body kept; five 503s
   stop after 5 attempts with waits 2, 4, 8, 16 s and status error; 400 and a refused connection are not retried; an
   HTTP 503 raised after the first chunk, a 503 sent inside the stream after the first chunk, a reset and a stream cut
   mid-chunk (IncompleteRead) are not retried and keep the record; generate follows the same rule. Every attempt is in
   the record.
10. Blocks and empty replies (D83 Q145): a prompt blocked by promptFeedback (no candidate) is "blocked" with
   block_reason, block_source "prompt", the whole promptFeedback and Google's message kept; a SAFETY finish is
   "blocked" with block_source "answer", stop_reason SAFETY and finishMessage kept; STOP with no parts, and STOP with
   blank text, is "empty"; STOP with only a function call is "ok"; RECITATION keeps its own status; a stream with no
   finishReason and no block that read a chunk with no part in it is "empty" with stop_reason None and no error (D89,
   Q145 O3; "error" before D89), its last candidates kept; one that holds any part (text, or only a thought), or that
   sent no chunk, stays "error" ("the stream ended without a finishReason"); an ok record carries all five new
   fields, with prompt_feedback, block_reason, block_source and finish_message None and last_candidates kept (not
   None); a block after a 503 is retried once (2 s), its attempts read error then blocked, and the record holds the
   streamed attempt's promptFeedback. Not tested: gemini_client._call's per-attempt reset of prompt_feedback,
   last_candidates and finish_message, which no retry can reach (a retry follows only an attempt that read no chunk,
   so those fields are still None; deleting the reset leaves every check passing).
11. D89 (Q145 O1, O3) and D90 (Q1, Q2): the shapes the callers return as empty text (a blocked prompt, a blocked
   answer, an empty reply with STOP and with no finishReason) each carry a status in EMPTY_TEXT_STATUSES, and the
   shapes they return with what the stream held (a recitation stop after streamed text, a malformed_function_call
   with and without text, a malformed_response after streamed text) a status in PASSED_ON_STATUSES with the streamed
   text kept in the record; each with Google's reason (block_reason and block_source, or stop_reason and
   finishMessage); ok, length, other finishReasons (OTHER, LANGUAGE, UNEXPECTED_TOOL_CALL) and error are in neither;
   raised_before_d89 is true for blocked, recitation, both malformed statuses and a no-finishReason empty reply only;
   the three tuples are exactly as decided. D92 Q188: language, other, unexpected_tool_call and too_many_tool_calls
   (after streamed text, and other with no part) are in PASSED_ON_STATUSES with the text and reason kept, and
   raised_before_d89 is true for them; the seven reasons Q188 does not name (finish_reason_unspecified, image_other,
   no_image, image_recitation, missing_thought_signature, pup_limited_disabled, continuation) are in neither tuple.
12. D92 Q199: a generate and a chat record carry session_id, code_commit and code_dirty (ollama_client.provenance).
   What a caller then does is checked where the caller is: check_adapter (the lock adapter returns empty text and the
   record keeps the status), check_orchestrator (exp_03's failed_calls and a step's failed_tool_calls count all four),
   check_rlm (Mentori's RLM sub-calls) and check_rlm_ref (the authors' RLM).
Live:
4. Reproduce: the generation settings sent equal the lock's [gemini] values, in the REST API's names.
5. A short call with thinking off returns status ok, the model version, and token counts including thinking.
6. The same call with the same seed, twice: whether the text repeats is reported (Gemini's seed is best effort,
   so this is information, not a pass condition).
7. An answer that fills a small output comes back as status "length" (this call alone sets maxOutputTokens 16;
   it checks the recording, not a setting).
8. Thinking on sends no thinking setting.
9. Two turns of chat with one tool declared: the first records tool_calls and raw_parts; the second sends the
   functionResponse back with the raw parts echoed as _gemini_parts and ends with status ok.
"""

import hashlib
import http.client
import io
import json
import sys
import urllib.error

from experiments.runner import gemini_client as gc
from experiments.runner.gemini_client import chat, function_declarations, generate, generation_config, to_contents
from experiments.runner.lock import load

OFFLINE = "--offline" in sys.argv[1:]
MODEL = "gemini-3-flash-preview"
PROMPT = "In one sentence: what does the STAR aligner do in an RNA-seq pipeline?"
lock = load()
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


# 1. Message mapping
TOOL = {"type": "function", "function": {"name": "gene_length", "description": "Length of a human gene in base pairs.",
        "parameters": {"type": "object", "properties": {"gene": {"type": "string"}}, "required": ["gene"]}}}
echoed = [{"text": "Checking.", "thoughtSignature": "c2lnLWE="},
          {"functionCall": {"name": "gene_length", "args": {"gene": "TP53"}}, "thoughtSignature": "c2lnLWI="}]
msgs = [{"role": "system", "content": "Be brief."}, {"role": "system", "content": "Use tools."},
        {"role": "user", "content": "How long is TP53?"},
        {"role": "assistant", "content": "Checking.", "_gemini_parts": echoed,
         "tool_calls": [{"function": {"name": "gene_length", "arguments": {"gene": "TP53"}}}]},
        {"role": "tool", "name": "gene_length", "content": "19149"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"id": "c1", "function": {"name": "gene_length", "arguments": "{\"gene\": \"BRCA1\"}"}},
            {"id": "c2", "function": {"name": "gene_length", "arguments": {"gene": "MYC"}}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "125951"},
        {"role": "tool", "tool_call_id": "c2", "content": "7631"},
        {"role": "assistant", "content": ""}, {"role": "user", "content": ""}]
si, contents = to_contents(msgs)
check("system messages -> systemInstruction, no system turn",
      si == {"parts": [{"text": "Be brief.\n\nUse tools."}]} and all(c["role"] in ("user", "model") for c in contents),
      json.dumps(si))
check("user -> role user", contents[0] == {"role": "user", "parts": [{"text": "How long is TP53?"}]})
check("assistant with _gemini_parts -> those parts sent unchanged", contents[1] == {"role": "model", "parts": echoed})
check("tool -> functionResponse, name from the message",
      contents[2] == {"role": "user", "parts": [{"functionResponse": {"name": "gene_length",
                                                                      "response": {"result": "19149"}}}]})
check("assistant tool_calls -> functionCall parts (JSON-string arguments parsed)",
      contents[3] == {"role": "model", "parts": [{"functionCall": {"name": "gene_length", "args": {"gene": "BRCA1"}}},
                                                 {"functionCall": {"name": "gene_length", "args": {"gene": "MYC"}}}]})
check("consecutive tool messages -> one turn each (as Mentori), names from the tool call ids",
      len(contents) == 8 and [c["role"] for c in contents[4:6]] == ["user", "user"]
      and [c["parts"] for c in contents[4:6]] == [
          [{"functionResponse": {"name": "gene_length", "response": {"result": r}}}] for r in ("125951", "7631")])
check("empty turns -> Mentori's placeholders ([Empty] for model, a space for user)",
      contents[6:] == [{"role": "model", "parts": [{"text": "[Empty]"}]}, {"role": "user", "parts": [{"text": " "}]}])
try:
    to_contents([{"role": "user", "content": "x", "images": ["aGk="]}])
    check("images are refused, never dropped", False)
except ValueError:
    check("images are refused, never dropped", True)
check("tools -> functionDeclarations", function_declarations([TOOL]) == [TOOL["function"]])


# 2 and 3. A fake HTTP layer
class FakeResponse:
    def __init__(self, lines, fail_after=None, exc=None):
        self.lines, self.fail_after = lines, fail_after
        self.exc = exc if exc is not None else ConnectionResetError("reset by peer")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        for i, line in enumerate(self.lines):
            if self.fail_after is not None and i == self.fail_after:
                raise self.exc
            yield line


def sse(*chunks):
    return [f"data: {json.dumps(c)}\n".encode() for c in chunks] + [b"\n"]


STREAM = sse({"candidates": [{"content": {"role": "model", "parts": [{"text": "Weighing it. ", "thought": True}]}}],
              "modelVersion": "fake-1"},
             {"candidates": [{"content": {"role": "model", "parts": [{"text": "Calling."}]}}]},
             {"candidates": [{"content": {"role": "model", "parts": [
                 {"functionCall": {"name": "gene_length", "args": {"gene": "TP53"}, "id": "call_1"},
                  "thoughtSignature": "c2ln"}]},
                 "finishReason": "STOP"}],
              "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "thoughtsTokenCount": 7,
                                "totalTokenCount": 22}})


def error_json(code):
    return json.dumps({"error": {"code": code, "message": f"fake {code}", "status": "UNAVAILABLE",
                                 "details": [{"retryDelay": "3s"}]}})


def http_error(code):
    return urllib.error.HTTPError(gc.API, code, "err", {}, io.BytesIO(error_json(code).encode()))


def fake(script):
    """Replaces the HTTP layer: each request takes the next item (an exception to raise or a FakeResponse)."""
    sent, slept = [], []
    posted.clear()

    def opener(req, timeout=None):
        posted.append(req.data)
        sent.append(json.loads(req.data))
        item = script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item
    gc._open, gc._sleep, gc._arm, gc._key = opener, slept.append, lambda r, s: None, lambda: "offline"
    return sent, slept


posted = []                                       # the exact bytes of each fake request
saved = (gc._open, gc._sleep, gc._arm, gc._key)
try:
    sent, slept = fake([FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL], thinking="off")
    check("stream read into text, thinking_text, tool_calls, raw_parts",
          r["status"] == "ok" and r["text"] == "Calling." and r["thinking_text"] == "Weighing it. "
          and r["tool_calls"] == [{"id": "call_1", "name": "gene_length", "arguments": {"gene": "TP53"}}]
          and r["raw_parts"] == [p for c in STREAM[:3] for p in json.loads(c[5:])["candidates"][0]["content"]["parts"]]
          and r["thinking_tokens"] == 7 and len(r["attempts"]) == 1, json.dumps(r["attempts"]))
    check("request carries the lock's settings, systemInstruction and tools",
          sent[0]["generationConfig"] == generation_config(lock.gemini(MODEL, 1, "off"))
          and sent[0]["systemInstruction"] == {"parts": [{"text": "Be brief.\n\nUse tools."}]}
          and sent[0]["tools"] == [{"functionDeclarations": [TOOL["function"]]}]
          and r["tools_sent"] == [TOOL["function"]] and r["contents_sent"] == sent[0]["contents"])
    check("request_sha256 is the sha256 of the bytes posted",
          r["request_sha256"] == hashlib.sha256(posted[0]).hexdigest(), r["request_sha256"])
    check("lock's stall_s recorded, no override", r["stall_s"] == lock.d["generation"]["stall_s"]
          and r["test_override"] is False and r["candidate"] is None, f"stall_s {r['stall_s']}")

    sent, slept = fake([FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs, tools=[TOOL], thinking="off")
    echoed[0]["text"] = "changed after the call"
    check("contents_sent is a copy: changing the caller's _gemini_parts later leaves the record as sent",
          r["contents_sent"][1]["parts"][0]["text"] == "Checking." and sent[0]["contents"] == r["contents_sent"])
    echoed[0]["text"] = "Checking."

    sent, slept = fake([FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3], thinking="off", stall_s=5, candidate=2)
    check("a caller's stall_s sets test_override and is recorded; candidate k sends seed draw * 1000 + k",
          r["stall_s"] == 5 and r["test_override"] is True and r["candidate"] == 2
          and sent[0]["generationConfig"]["seed"] == 1002, f"seed {sent[0]['generationConfig']['seed']}")

    sent, slept = fake([http_error(503), http_error(429), FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
    check("503, 429, then a stream: retried, waits 2 and 4 s, status ok",
          r["status"] == "ok" and slept == [2, 4] and [a["http_code"] for a in r["attempts"]] == [503, 429, None]
          and [a["status"] for a in r["attempts"]] == ["error", "error", "ok"]
          and r["attempts"][0]["error"] == "HTTP 503: fake 503" and r["attempts"][0]["error_body"] == error_json(503)
          and r["error_body"] is None, json.dumps(r["attempts"]))

    sent, slept = fake([http_error(503) for _ in range(6)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("five 503s: 5 attempts, waits 2, 4, 8, 16 s, status error",
          r["status"] == "error" and len(sent) == 5 and slept == [2, 4, 8, 16] and len(r["attempts"]) == 5
          and r["error"] == "HTTP 503: fake 503" and r["error_body"] == error_json(503),
          f"{r['status']} {len(sent)} requests, waits {slept}")

    sent, slept = fake([http_error(400), FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("400 is not retried", r["status"] == "error" and len(sent) == 1 and slept == []
          and r["attempts"][0]["http_code"] == 400, r["error"])

    sent, slept = fake([urllib.error.URLError("refused"), FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("a refused connection is not retried", r["status"] == "error" and len(sent) == 1 and slept == [], r["error"])

    sent, slept = fake([FakeResponse(STREAM, fail_after=1), FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("a reset after the first chunk is not retried, the part read is kept",
          r["status"] == "error" and len(sent) == 1 and r["thinking_text"] == "Weighing it. "
          and len(r["raw_parts"]) == 1, r["error"])

    sent, slept = fake([FakeResponse(STREAM, fail_after=1, exc=http_error(503)), FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("HTTP 503 raised after the first chunk is not retried (the first-chunk guard)",
          r["status"] == "error" and len(sent) == 1 and slept == [] and r["attempts"][0]["http_code"] == 503
          and r["error"] == "HTTP 503: fake 503" and len(r["raw_parts"]) == 1, r["error"])

    sent, slept = fake([FakeResponse(STREAM[:1] + [f"data: {error_json(503)}\n".encode()]), FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("a 503 sent inside the stream after the first chunk is not retried, its body kept",
          r["status"] == "error" and len(sent) == 1 and slept == [] and r["error_body"] == error_json(503)
          and r["error"].startswith("in stream: 503"), r["error"])

    sent, slept = fake([FakeResponse(STREAM, fail_after=2, exc=http.client.IncompleteRead(b"da", 40)),
                        FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("a stream cut mid-chunk (IncompleteRead) ends as error with the record kept",
          r["status"] == "error" and len(sent) == 1 and r["text"] == "Calling." and len(r["attempts"]) == 1
          and r["error"].startswith("IncompleteRead"), r["error"])

    sent, slept = fake([http_error(500), FakeResponse(STREAM)])
    r = generate(lock, MODEL, 1, "x")
    check("generate follows the same rule (500 then a stream)",
          r["status"] == "ok" and slept == [2] and [a["http_code"] for a in r["attempts"]] == [500, None]
          and bool(r["tool_calls"]) and bool(r["raw_parts"]), json.dumps(r["attempts"]))

    # 10. Blocks and empty replies (D83 Q145)
    NEW = ("prompt_feedback", "last_candidates", "finish_message", "block_reason", "block_source")
    USAGE = {"promptTokenCount": 8738, "totalTokenCount": 8738}            # the recorded shape: prompt = total
    FEEDBACK = {"blockReason": "PROHIBITED_CONTENT", "blockReasonMessage": "fake message",
                "safetyRatings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "probability": "LOW"}]}
    sent, slept = fake([FakeResponse(sse({"promptFeedback": FEEDBACK, "usageMetadata": USAGE,
                                          "modelVersion": "fake-1"}))])
    r = generate(lock, MODEL, 1, "x")
    check("10 a prompt blocked by promptFeedback: status blocked, block_reason, source prompt, feedback kept",
          r["status"] == "blocked" and r["block_reason"] == "PROHIBITED_CONTENT" and r["block_source"] == "prompt"
          and r["prompt_feedback"] == FEEDBACK and r["stop_reason"] is None and r["last_candidates"] is None
          and r["error"] == "Google blocked the prompt: PROHIBITED_CONTENT (fake message)"
          and r["attempts"][-1]["status"] == "blocked" and r["prompt_tokens"] == r["total_tokens"] == 8738,
          f"{r['status']} {r['error']}")

    CAND = {"content": {"role": "model", "parts": []}, "finishReason": "SAFETY", "finishMessage": "fake stop",
            "safetyRatings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "probability": "HIGH",
                               "blocked": True}]}
    sent, slept = fake([FakeResponse(sse({"candidates": [CAND], "usageMetadata": USAGE}))])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("10 a SAFETY finish: status blocked, source answer, stop_reason SAFETY, finishMessage and candidates kept",
          r["status"] == "blocked" and r["block_reason"] == "SAFETY" and r["block_source"] == "answer"
          and r["stop_reason"] == "SAFETY" and r["finish_message"] == "fake stop" and r["last_candidates"] == [CAND]
          and r["prompt_feedback"] is None and r["error"] == "Google stopped the answer: SAFETY (fake stop)",
          f"{r['status']} {r['error']}")

    EMPTY = {"content": {"role": "model"}, "finishReason": "STOP"}
    sent, slept = fake([FakeResponse(sse({"candidates": [EMPTY], "usageMetadata": USAGE}))])
    r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
    check("10 STOP with no parts: status empty, stop_reason STOP, no error, candidates kept",
          r["status"] == "empty" and r["stop_reason"] == "STOP" and r["error"] is None and r["raw_parts"] == []
          and r["last_candidates"] == [EMPTY] and r["block_reason"] is None, f"{r['status']} {r['error']}")

    sent, slept = fake([FakeResponse(sse({"candidates": [{"content": {"role": "model", "parts": [{"text": " \n"}]},
                                                          "finishReason": "STOP"}]}))])
    r = generate(lock, MODEL, 1, "x")
    check("10 STOP with blank text: status empty", r["status"] == "empty" and r["text"] == " \n", r["status"])

    sent, slept = fake([FakeResponse(sse({"candidates": [{"content": {"role": "model", "parts": [
        {"functionCall": {"name": "gene_length", "args": {"gene": "TP53"}}}]}, "finishReason": "STOP"}]}))])
    r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
    check("10 STOP with only a function call: status ok", r["status"] == "ok" and len(r["tool_calls"]) == 1,
          r["status"])

    sent, slept = fake([FakeResponse(sse({"candidates": [{"content": {"role": "model", "parts": [{"text": "a"}]},
                                                          "finishReason": "RECITATION"}]}))])
    r = generate(lock, MODEL, 1, "x")
    check("10 RECITATION keeps its own status (not blocked)",
          r["status"] == "recitation" and r["block_reason"] is None, r["status"])

    NOFIN = {"content": {"role": "model", "parts": []}}
    sent, slept = fake([FakeResponse(sse({"candidates": [NOFIN], "usageMetadata": USAGE}))])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("10 D89 no finishReason, no block, nothing in it (the 19_hpai shape, prompt = total): status empty, "
          "stop_reason None, no error, last candidates kept",
          r["status"] == "empty" and r["stop_reason"] is None and r["error"] is None
          and r["last_candidates"] == [NOFIN] and r["prompt_feedback"] is None and r["block_reason"] is None
          and r["prompt_tokens"] == r["total_tokens"] == 8738 and r["attempts"][-1]["status"] == "empty",
          f"{r['status']} {r['error']}")

    sent, slept = fake([FakeResponse(sse({"candidates": [{"content": {"role": "model", "parts": [{"text": "half"}]}}],
                                          "usageMetadata": USAGE}))])
    r = generate(lock, MODEL, 1, "x")
    check("10 D89 no finishReason with text in it (cut short): status error as before D89",
          r["status"] == "error" and r["error"] == "the stream ended without a finishReason" and r["text"] == "half",
          f"{r['status']} {r['error']}")

    THOUGHT = {"content": {"role": "model", "parts": [{"text": "x", "thought": True}]}}
    sent, slept = fake([FakeResponse(sse({"candidates": [THOUGHT], "usageMetadata": USAGE}))])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("10 D89 no finishReason with only a thought part in it (cut short, no visible text): status error, not "
          "empty (the empty rule needs no part at all, as all 44 stored cases had)",
          r["status"] == "error" and r["error"] == "the stream ended without a finishReason"
          and r["raw_parts"] == [{"text": "x", "thought": True}], f"{r['status']} {r['error']}")

    sent, slept = fake([FakeResponse([b"\n"])])
    r = generate(lock, MODEL, 1, "x")
    check("10 D89 a stream that sent no chunk: status error, not empty",
          r["status"] == "error" and r["error"] == "the stream ended without a finishReason"
          and r["first_chunk_s"] is not None and r["model_version"] is None, f"{r['status']} {r['error']}")

    sent, slept = fake([FakeResponse(STREAM)])
    r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
    check("10 an ok record carries the five new fields: feedback, block reason, block source and finish message "
          "None, last candidates kept",
          r["status"] == "ok" and all(k in r for k in NEW) and r["prompt_feedback"] is None
          and r["block_reason"] is None and r["block_source"] is None and r["finish_message"] is None
          and r["last_candidates"] is not None,
          json.dumps({k: r.get(k) for k in NEW if k != "last_candidates"}))

    sent, slept = fake([http_error(503), FakeResponse(sse({"promptFeedback": FEEDBACK}))])
    r = generate(lock, MODEL, 1, "x")
    check("10 a block after a 503: blocked, retried once, the attempts show error then blocked, feedback kept",
          r["status"] == "blocked" and slept == [2] and [a["status"] for a in r["attempts"]] == ["error", "blocked"]
          and r["prompt_feedback"] == FEEDBACK and r["block_source"] == "prompt",
          json.dumps([a["status"] for a in r["attempts"]]))

    # 11. D89 and D90: the shapes a caller returns as empty text or with what the stream held, each with Google's
    # reason in the record
    shapes = {
        "blocked prompt": ([FakeResponse(sse({"promptFeedback": FEEDBACK, "usageMetadata": USAGE}))],
                           lambda r: r["status"] == "blocked" and r["block_source"] == "prompt"
                           and r["block_reason"] == "PROHIBITED_CONTENT" and r["prompt_feedback"] == FEEDBACK),
        "blocked answer": ([FakeResponse(sse({"candidates": [CAND], "usageMetadata": USAGE}))],
                           lambda r: r["status"] == "blocked" and r["block_source"] == "answer"
                           and r["block_reason"] == "SAFETY" and r["finish_message"] == "fake stop"),
        "empty reply (STOP)": ([FakeResponse(sse({"candidates": [EMPTY], "usageMetadata": USAGE}))],
                               lambda r: r["status"] == "empty" and r["stop_reason"] == "STOP"),
        "empty reply (no finishReason)": ([FakeResponse(sse({"candidates": [NOFIN], "usageMetadata": USAGE}))],
                                          lambda r: r["status"] == "empty" and r["stop_reason"] is None),
    }
    def stopped(finish, msg, *parts):
        """a stream that sends parts, then a chunk with finishReason finish and no part"""
        return [FakeResponse(sse(*([{"candidates": [{"content": {"role": "model", "parts": [p]}}]} for p in parts]
                                   + [{"candidates": [{"content": {"role": "model", "parts": []},
                                                       "finishReason": finish, "finishMessage": msg}],
                                       "usageMetadata": USAGE}])))]
    passed = {
        "recitation after streamed text": (stopped("RECITATION", "fake recitation", {"text": "half "}, {"text": "an"}),
                                           lambda r: r["status"] == "recitation" and r["stop_reason"] == "RECITATION"
                                           and r["finish_message"] == "fake recitation" and r["text"] == "half an"
                                           and r["block_reason"] is None and r["error"] is None),
        "malformed_function_call, no part": ([FakeResponse(sse({"candidates": [{"content": {"role": "model"},
                                                                                "finishReason": "MALFORMED_FUNCTION_CALL",
                                                                                "finishMessage": "fake malformed"}]}))],
                                             lambda r: r["status"] == "malformed_function_call"
                                             and r["stop_reason"] == "MALFORMED_FUNCTION_CALL" and r["text"] == ""
                                             and r["finish_message"] == "fake malformed" and r["raw_parts"] == []),
        "malformed_function_call after streamed text": (stopped("MALFORMED_FUNCTION_CALL", None, {"text": "I call "}),
                                                        lambda r: r["status"] == "malformed_function_call"
                                                        and r["text"] == "I call " and len(r["raw_parts"]) == 1),
        "malformed_response after streamed text": (stopped("MALFORMED_RESPONSE", "fake bad", {"text": "partial"}),
                                                   lambda r: r["status"] == "malformed_response"
                                                   and r["stop_reason"] == "MALFORMED_RESPONSE"
                                                   and r["text"] == "partial" and r["finish_message"] == "fake bad"),
    }
    for fr in ("LANGUAGE", "OTHER", "UNEXPECTED_TOOL_CALL", "TOO_MANY_TOOL_CALLS"):    # D92 Q188
        passed[f"{fr.lower()} after streamed text (Q188)"] = (
            stopped(fr, f"fake {fr.lower()}", {"text": "some "}, {"text": "text"}),
            lambda r, fr=fr: r["status"] == fr.lower() and r["stop_reason"] == fr and r["text"] == "some text"
            and r["finish_message"] == f"fake {fr.lower()}" and r["error"] is None)
    passed["other, no part (Q188)"] = ([FakeResponse(sse({"candidates": [{"content": {"role": "model"},
                                                                          "finishReason": "OTHER"}]}))],
                                       lambda r: r["status"] == "other" and r["text"] == "" and r["raw_parts"] == [])
    for name, (script, reason_kept) in shapes.items():
        sent, slept = fake(script)
        r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
        check(f"11 D89 {name}: status {r['status']} is one the callers return as empty text, Google's reason kept",
              r["status"] in gc.EMPTY_TEXT_STATUSES and r["status"] not in gc.PASSED_ON_STATUSES and reason_kept(r),
              f"{r['status']} {r['error']}")
    for name, (script, kept) in passed.items():
        sent, slept = fake(script)
        r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
        check(f"11 D90 {name}: status {r['status']} is one the callers return with what the stream held, the text "
              "and Google's reason kept",
              r["status"] in gc.PASSED_ON_STATUSES and r["status"] not in gc.EMPTY_TEXT_STATUSES and kept(r),
              f"{r['status']} {r['text']!r} {r['error']}")
    others = {"ok": STREAM, "length": sse({"candidates": [{"content": {"role": "model", "parts": [{"text": "a"}]},
                                                           "finishReason": "MAX_TOKENS"}]})}
    for fr in ("FINISH_REASON_UNSPECIFIED", "IMAGE_OTHER", "NO_IMAGE", "IMAGE_RECITATION", "MISSING_THOUGHT_SIGNATURE",
               "PUP_LIMITED_DISABLED", "CONTINUATION"):     # the finish reasons D92 Q188 does not name
        others[fr.lower()] = sse({"candidates": [{"content": {"role": "model"}, "finishReason": fr}]})
    for want, lines in others.items():
        sent, slept = fake([FakeResponse(lines)])
        r = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
        check(f"11 D90, D92 {want} is in neither tuple (ok and length return as they are; any other status raises "
              "in the callers)", r["status"] == want and r["status"] not in gc.RETURNED_STATUSES, r["status"])
    sent, slept = fake([http_error(400)])
    r = chat(lock, MODEL, 1, msgs[:3])
    check("11 D89 an HTTP error is not returned", r["status"] == "error"
          and r["status"] not in gc.RETURNED_STATUSES, r["status"])
    rb = gc.raised_before_d89
    check("11 D90, D92 raised_before_d89 (the sub-call failure counters): blocked, recitation, both malformed "
          "statuses, the four Q188 reasons and a no-finishReason empty reply yes; a STOP empty reply, ok, length, "
          "error and an unnamed reason (no_image) no",
          rb({"status": "blocked", "stop_reason": "SAFETY"}) and rb({"status": "recitation", "stop_reason": "RECITATION"})
          and rb({"status": "malformed_function_call", "stop_reason": "MALFORMED_FUNCTION_CALL"})
          and rb({"status": "malformed_response", "stop_reason": "MALFORMED_RESPONSE"})
          and rb({"status": "empty", "stop_reason": None}) and not rb({"status": "empty", "stop_reason": "STOP"})
          and all(rb({"status": st, "stop_reason": st.upper()}) for st in gc.OTHER_REASON_STATUSES)
          and not any(rb({"status": st, "stop_reason": None}) for st in ("ok", "length", "error", "no_image")))
    check("11 D90, D92 EMPTY_TEXT_STATUSES is exactly empty and blocked, PASSED_ON_STATUSES exactly recitation, "
          "malformed_function_call, malformed_response and the four Q188 reasons, RETURNED_STATUSES the two together",
          gc.EMPTY_TEXT_STATUSES == ("empty", "blocked")
          and gc.PASSED_ON_STATUSES == ("recitation", "malformed_function_call", "malformed_response",
                                        "language", "other", "unexpected_tool_call", "too_many_tool_calls")
          and gc.OTHER_REASON_STATUSES == ("language", "other", "unexpected_tool_call", "too_many_tool_calls")
          and gc.RETURNED_STATUSES == gc.EMPTY_TEXT_STATUSES + gc.PASSED_ON_STATUSES,
          f"{gc.EMPTY_TEXT_STATUSES} {gc.PASSED_ON_STATUSES}")
    # 12. D92 Q199: every record names its session and code; generate, chat and the RLM adapter's send_chat all
    # build it with _record, so one generate and one chat cover it
    from experiments.runner import ollama_client as oc
    want = oc.provenance()
    sent, slept = fake([FakeResponse(STREAM)])
    rg = gc.generate(lock, MODEL, 1, "hi")
    sent, slept = fake([FakeResponse(STREAM)])
    rcx = chat(lock, MODEL, 1, msgs[:3], tools=[TOOL])
    import re as _re
    check("12 D92 Q199 a generate and a chat record carry session_id (host:pid:UTC start:8 hex, this process's), "
          "code_commit (40 hex, git rev-parse HEAD) and code_dirty (a bool), the values ollama_client.provenance gives",
          all({k: r.get(k) for k in want} == want for r in (rg, rcx))
          and _re.fullmatch(r".+:\d+:\d{8}T\d{6}Z:[0-9a-f]{8}", want["session_id"] or "") is not None
          and f":{__import__('os').getpid()}:" in want["session_id"]
          and _re.fullmatch(r"[0-9a-f]{40}", want["code_commit"] or "") is not None
          and isinstance(want["code_dirty"], bool), json.dumps(want))
finally:
    gc._open, gc._sleep, gc._arm, gc._key = saved

if OFFLINE:
    print(f"{sum(results)} of {len(results)} checks pass (offline: no Google call)")
    sys.exit(0 if all(results) else 1)

# 4 to 8. Live, generate
cfg = lock.gemini(MODEL, draw=1, thinking="off")
g = generation_config(cfg)
check("settings sent are the lock's", g == {"temperature": 1.0, "topP": 0.95, "topK": 64, "maxOutputTokens": 65536,
      "seed": 1, "thinkingConfig": {"thinkingLevel": "minimal"}}, json.dumps(g))

a = generate(lock, MODEL, 1, PROMPT, thinking="off")
check("short call, thinking off", a["status"] == "ok" and a["text"].strip() != "" and a["model_version"] is not None,
      f"{a['status']} {a['model_version']} prompt {a['prompt_tokens']} out {a['output_tokens']} "
      f"thinking {a['thinking_tokens']} {a['wall_s']} s, {len(a['attempts'])} attempt(s)")
b = generate(lock, MODEL, 1, PROMPT, thinking="off")
print(f"INFO same seed twice, same text: {a['text'] == b['text']}")

short = {**cfg, "max_output_tokens": 16}
c = generate(lock, MODEL, 1, "Count from 1 to 200, one number per line.", test_override_cfg=short)
check("output limit recorded as length", c["status"] == "length", f"{c['status']} {c['output_tokens']} tokens")

on = lock.gemini(MODEL, draw=1)                  # generator rule: Google's default (D66)
check("thinking on sends no thinking setting", "thinkingConfig" not in generation_config(on))
d = generate(lock, MODEL, 1, PROMPT)
check("short call, thinking on (Google's default)", d["status"] == "ok",
      f"{d['status']} thinking {d['thinking_tokens']} tokens {d['wall_s']} s")

# 9. Live, two turns of chat with one tool (thinking at Google's default, the generator rule)
turn1 = [{"role": "system", "content": "Answer gene questions with the gene_length tool; never guess a length."},
         {"role": "user", "content": "How long is the human TP53 gene? Call the tool, then answer in one sentence."}]
e = chat(lock, MODEL, 1, turn1, tools=[TOOL])
check("chat turn 1 records tool_calls and raw_parts",
      e["status"] == "ok" and len(e["tool_calls"]) >= 1 and e["tool_calls"][0]["name"] == "gene_length"
      and len(e["raw_parts"]) >= 1, f"{e['status']} calls {json.dumps(e['tool_calls'])} raw parts "
      f"{len(e['raw_parts'])} thinking {e['thinking_tokens']} {e['wall_s']} s")
print(f"INFO turn 1 raw parts carry a thoughtSignature: {any('thoughtSignature' in p for p in e['raw_parts'])}")
if e["tool_calls"]:
    print(f"INFO turn 1 tool call ids: {[tc['id'] for tc in e['tool_calls']]}")
    turn2 = turn1 + [{"role": "assistant", "content": e["text"], "_gemini_parts": e["raw_parts"],
                      "tool_calls": [{"id": tc["id"], "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                                     for tc in e["tool_calls"]]}] + [
        {"role": "tool", "tool_call_id": tc["id"], "name": tc["name"], "content": "19149 bp"} for tc in e["tool_calls"]]
    f = chat(lock, MODEL, 1, turn2, tools=[TOOL])
    check("chat turn 2 (functionResponse, raw parts echoed) ends ok", f["status"] == "ok" and f["text"].strip() != "",
          f"{f['status']} {f['error']} text {len(f['text'])} chars, {f['wall_s']} s")
    print(f"INFO turn 2 answer mentions 19149: {'19149' in f['text'].replace(',', '')}")
else:
    check("chat turn 2 (functionResponse, raw parts echoed) ends ok", False, "turn 1 made no tool call")

print(f"{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
