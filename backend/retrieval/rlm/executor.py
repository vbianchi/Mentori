"""
RLM Executor - Executes LLM-generated code in a sandboxed REPL.

The executor provides a restricted namespace where the LLM can:
1. Access document navigation functions
2. Perform searches (keyword, regex, semantic)
3. Make recursive LLM calls on specific content
4. Track citations
5. Build the output report
"""

from typing import Dict, Any, Callable, Tuple, List, Optional
import io
import sys
import traceback
import json
import re
import asyncio
import threading
import logging
from contextlib import redirect_stdout, redirect_stderr

from .context import RLMContext, ChunkResult, Citation

logger = logging.getLogger(__name__)

# ── Dedicated background event loop for sync→async bridging ──
# A single loop runs in a daemon thread. All sync wrappers schedule
# coroutines onto this loop via run_coroutine_threadsafe, avoiding
# the "Future attached to a different loop" error that occurs when
# asyncio.run() creates throwaway loops in ThreadPoolExecutor.
_bg_loop: asyncio.AbstractEventLoop = None
_bg_thread: threading.Thread = None
_bg_lock = threading.Lock()


def _get_bg_loop() -> asyncio.AbstractEventLoop:
    """Return (and lazily start) the shared background event loop."""
    global _bg_loop, _bg_thread
    if _bg_loop is not None and _bg_loop.is_running():
        return _bg_loop
    with _bg_lock:
        if _bg_loop is not None and _bg_loop.is_running():
            return _bg_loop
        _bg_loop = asyncio.new_event_loop()
        _bg_thread = threading.Thread(
            target=_bg_loop.run_forever, daemon=True, name="rlm-bg-loop"
        )
        _bg_thread.start()
    return _bg_loop


def _run_async(coro) -> Any:
    """Run an async coroutine from sync code using the shared background loop."""
    loop = _get_bg_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()  # blocks until done


_SYNC_GEMINI_MAX_RETRIES = 5
_SYNC_GEMINI_BASE_DELAY = 5  # seconds
_SYNC_GEMINI_RETRYABLE = {"500", "503", "429", "INTERNAL", "UNAVAILABLE", "RESOURCE_EXHAUSTED"}


def _is_retryable_sync(exc: Exception) -> bool:
    """Check if a sync Gemini exception is retryable."""
    msg = str(exc)
    return any(code in msg for code in _SYNC_GEMINI_RETRYABLE)


def _run_sync_gemini(model: str, prompt: str, options: dict = None) -> dict:
    """Make a synchronous Gemini call from REPL context with retry logic.

    Uses the sync API (client.models.generate_content) instead of the async
    API (client.aio.models) to avoid event-loop conflicts when called from
    within asyncio.gather batches.

    Includes retry with exponential backoff for transient errors (500, 503, 429),
    matching the retry behavior of the async GeminiClient.
    """
    import time as _time
    from google import genai
    from google.genai import types
    from backend.config import settings

    # Lazy singleton client for sync sub-calls
    if not hasattr(_run_sync_gemini, "_client"):
        api_key = settings.GEMINI_API_KEY
        _run_sync_gemini._client = genai.Client(api_key=api_key) if api_key else None

    client = _run_sync_gemini._client
    if client is None:
        return {"error": "No Gemini API key", "response": ""}

    # Strip gemini:: prefix
    if "::" in model:
        model = model.split("::", 1)[1]

    # Match the router's behavior: do NOT pass temperature or max_output_tokens
    # to Gemini. The router.generate → gemini.generate_completion path passes
    # only model + prompt + system (no options). Restricting these params was
    # causing short/degraded answers compared to the router path.
    config = types.GenerateContentConfig()

    last_exc = None
    for attempt in range(_SYNC_GEMINI_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model, contents=prompt, config=config,
            )
            text = ""
            try:
                text = response.text or ""
            except (ValueError, AttributeError):
                pass
            result = {"response": text}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                result["prompt_eval_count"] = getattr(um, "prompt_token_count", 0) or 0
                result["eval_count"] = getattr(um, "candidates_token_count", 0) or 0
            return result
        except Exception as e:
            last_exc = e
            if attempt < _SYNC_GEMINI_MAX_RETRIES and _is_retryable_sync(e):
                delay = _SYNC_GEMINI_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"[RLM sync Gemini] Retryable error (attempt {attempt+1}/"
                    f"{_SYNC_GEMINI_MAX_RETRIES+1}): {e}. Retrying in {delay}s..."
                )
                _time.sleep(delay)
            else:
                break

    logger.error(f"[RLM sync Gemini] EXCEPTION after {attempt+1} attempts: {last_exc}")
    return {"error": str(last_exc), "response": ""}


class RLMExecutor:
    """
    Executes LLM-generated code in a sandboxed environment.

    The namespace is carefully controlled to only expose safe operations
    that allow document analysis without arbitrary code execution risks.
    """

    # Maximum output length to prevent runaway prints
    MAX_OUTPUT_LENGTH = 50000

    # Maximum execution time per code block
    MAX_EXECUTION_TIME = 60  # seconds

    def __init__(self, context: RLMContext, model_router, model_identifier: str):
        """
        Initialize the executor.

        Args:
            context: The RLMContext managing document state
            model_router: ModelRouter for LLM calls
            model_identifier: Model to use for recursive calls
        """
        self.context = context
        self.router = model_router
        self.model_identifier = model_identifier

        # Accumulated output from print statements
        self._output_buffer = io.StringIO()

        # Variables created by LLM code (persistent across executions)
        self._user_namespace: Dict[str, Any] = {}

        # Build the execution namespace
        self.namespace = self._build_namespace()

    def _build_namespace(self) -> Dict[str, Any]:
        """
        Build the restricted namespace available to LLM code.

        Only safe, document-related functions are exposed.
        """
        namespace = {
            # Context reference (read-only access to state)
            "context": self.context,

            # Document Navigation
            "list_documents": self.context.list_documents,
            "get_document_structure": self.context.get_document_structure,
            "get_chunk": self.context.get_chunk,
            "get_chunks_range": self.context.get_chunks_range,
            "get_chunks_by_page": self.context.get_chunks_by_page,

            # Search Functions
            "search_keyword": self.context.search_keyword,
            "search_regex": self.context.search_regex,
            "search_semantic": self.context.search_semantic,

            # LLM Calls (wrapped for async handling)
            "llm_query": self._sync_llm_query,
            "llm_extract": self._sync_llm_extract,
            "llm_summarize": self._sync_llm_summarize,

            # Citation Tracking
            "cite": self.context.cite,
            "get_citations": self.context.get_citations,

            # Report Building
            "add_to_report": self.context.add_to_report,
            "get_report": self.context.get_report,
            "get_progress": self.context.get_progress,

            # Safe Builtins
            "print": self._safe_print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "reversed": reversed,
            "min": min,
            "max": max,
            "sum": sum,
            "any": any,
            "all": all,
            "abs": abs,
            "round": round,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "type": type,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,

            # Safe Modules
            "json": json,
            "re": re,

            # Data Classes (for type hints)
            "ChunkResult": ChunkResult,
            "Citation": Citation,

            # FINAL_VAR: identity function so LLM code doesn't error
            # The orchestrator detects FINAL_VAR in the code text and
            # evaluates the expression separately; this just prevents NameError.
            "FINAL_VAR": lambda x: x,
        }

        # Merge user-created variables
        namespace.update(self._user_namespace)

        return namespace

    def _safe_print(self, *args, **kwargs):
        """Safe print that captures output."""
        output = io.StringIO()
        print(*args, file=output, **kwargs)
        text = output.getvalue()

        # Truncate if too long
        current_len = len(self._output_buffer.getvalue())
        if current_len + len(text) > self.MAX_OUTPUT_LENGTH:
            remaining = self.MAX_OUTPUT_LENGTH - current_len
            if remaining > 0:
                text = text[:remaining] + "\n[OUTPUT TRUNCATED]"
            else:
                return

        self._output_buffer.write(text)

    # ============== SYNC WRAPPERS FOR ASYNC LLM CALLS ==============
    # The LLM generates sync code, but our LLM calls are async.
    # These wrappers handle the async execution.

    def _sync_llm_query(self, prompt: str, context_chunks: List[Any] = None,
                        max_tokens: int = 2000) -> str:
        """
        Synchronous wrapper for LLM query.

        Args:
            prompt: The prompt for the LLM
            context_chunks: Optional list of ChunkResult or strings to include
            max_tokens: Maximum response tokens
        """
        return _run_async(self._async_llm_query(prompt, context_chunks, max_tokens))

    async def _async_llm_query(self, prompt: str, context_chunks: List[Any] = None,
                               max_tokens: int = 2000) -> str:
        """
        Make a recursive LLM call with optional context chunks.

        Args:
            prompt: The task/question for the LLM
            context_chunks: Chunks to include in the prompt
            max_tokens: Max response length
        """
        self.context.llm_calls_made += 1

        # Build the full prompt with context
        full_prompt = prompt

        if context_chunks:
            chunks_text = []
            for i, chunk in enumerate(context_chunks):
                if isinstance(chunk, ChunkResult):
                    chunks_text.append(
                        f"[Chunk {i+1} - {chunk.doc_name} p{chunk.page}]\n{chunk.text}"
                    )
                elif isinstance(chunk, str):
                    chunks_text.append(f"[Chunk {i+1}]\n{chunk}")
                else:
                    chunks_text.append(f"[Chunk {i+1}]\n{str(chunk)}")

            context_section = "\n\n---\n\n".join(chunks_text)
            full_prompt = f"""Context:
{context_section}

---

Task: {prompt}"""

        # Make the LLM call
        # Use sync Gemini to avoid event-loop conflicts in concurrent contexts
        try:
            if "gemini" in self.model_identifier:
                response = _run_sync_gemini(
                    self.model_identifier, full_prompt,
                    {"temperature": 0.1, "num_predict": max_tokens},
                )
            else:
                response = await self.router.generate(
                    model_identifier=self.model_identifier,
                    prompt=full_prompt,
                    options={
                        "temperature": 0.1,
                        "num_predict": max_tokens,
                        "num_ctx": 24576,
                    }
                )

            result = response.get("response", "")

            # Track tokens
            tokens_used = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
            self.context.total_tokens_used += tokens_used

            return result

        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return f"[ERROR] LLM call failed: {str(e)}"

    def _sync_llm_extract(self, chunks: List[Any], schema: Dict[str, str],
                          task: str = None) -> Dict[str, Any]:
        """
        Extract structured information from chunks.

        Args:
            chunks: Chunks to extract from
            schema: Dict describing what to extract, e.g. {"methods": "str", "sample_size": "int"}
            task: Optional specific extraction task

        Returns:
            Dict with extracted fields
        """
        return _run_async(self._async_llm_extract(chunks, schema, task))

    async def _async_llm_extract(self, chunks: List[Any], schema: Dict[str, str],
                                 task: str = None) -> Dict[str, Any]:
        """Extract structured data from chunks."""
        self.context.llm_calls_made += 1

        # Build extraction prompt
        schema_desc = "\n".join([f"- {k}: {v}" for k, v in schema.items()])

        chunks_text = []
        for i, chunk in enumerate(chunks):
            if isinstance(chunk, ChunkResult):
                chunks_text.append(f"[{i+1}] {chunk.text}")
            else:
                chunks_text.append(f"[{i+1}] {str(chunk)}")

        prompt = f"""Extract the following information from the text below.

Fields to extract:
{schema_desc}

{"Additional instructions: " + task if task else ""}

Text:
{chr(10).join(chunks_text)}

Output as JSON with the requested fields. If a field cannot be found, use null.
Include a "source_chunks" field listing which chunk numbers contained the information."""

        try:
            if "gemini" in self.model_identifier:
                response = _run_sync_gemini(
                    self.model_identifier, prompt,
                    {"temperature": 0.1},
                )
            else:
                response = await self.router.generate(
                    model_identifier=self.model_identifier,
                    prompt=prompt,
                    options={"temperature": 0.1, "num_ctx": 24576}
                )

            result_text = response.get("response", "{}")

            # Track tokens
            tokens_used = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
            self.context.total_tokens_used += tokens_used

            # Parse JSON from response
            json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Could not parse extraction result", "raw": result_text}

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {"error": str(e)}

    def _sync_llm_summarize(self, chunks: List[Any], max_tokens: int = 500,
                            task: str = None) -> Dict[str, Any]:
        """
        Summarize chunks with mandatory citation tracking.

        Args:
            chunks: Chunks to summarize
            max_tokens: Max summary length
            task: Optional specific summarization task

        Returns:
            Dict with 'summary', 'citations', and 'uncited_claims'
        """
        return _run_async(self._async_llm_summarize(chunks, max_tokens, task))

    async def _async_llm_summarize(self, chunks: List[Any], max_tokens: int = 500,
                                   task: str = None) -> Dict[str, Any]:
        """Summarize with citation tracking."""
        self.context.llm_calls_made += 1

        # Build chunks with clear identifiers for citation
        chunks_with_ids = []
        chunk_map = {}  # id -> ChunkResult for citation creation

        for i, chunk in enumerate(chunks):
            chunk_id = i + 1
            if isinstance(chunk, ChunkResult):
                chunks_with_ids.append(
                    f"[{chunk_id}] (Source: {chunk.doc_name}, Page {chunk.page})\n{chunk.text}"
                )
                chunk_map[chunk_id] = chunk
            else:
                chunks_with_ids.append(f"[{chunk_id}]\n{str(chunk)}")

        prompt = f"""Summarize the following content. You MUST cite your sources.

Content:
{chr(10).join(chunks_with_ids)}

{"Task: " + task if task else "Write a concise summary."}

IMPORTANT RULES:
1. After EVERY factual claim, add a citation in [#] format (e.g., "The study found X [1][2]")
2. Only include information from the provided chunks
3. If you cannot find information for something, say "Not found in source material"

Output format:
SUMMARY:
[Your summary with inline citations like [1], [2], etc.]

CITATIONS_USED:
[List the chunk numbers you cited, comma-separated]"""

        try:
            if "gemini" in self.model_identifier:
                response = _run_sync_gemini(
                    self.model_identifier, prompt,
                    {"temperature": 0.2, "num_predict": max_tokens + 200},
                )
            else:
                response = await self.router.generate(
                    model_identifier=self.model_identifier,
                    prompt=prompt,
                    options={"temperature": 0.2, "num_predict": max_tokens + 200, "num_ctx": 24576}
                )

            result_text = response.get("response", "")

            # Track tokens
            tokens_used = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
            self.context.total_tokens_used += tokens_used

            # Parse the response
            summary = result_text
            citations_used = []

            if "SUMMARY:" in result_text:
                parts = result_text.split("CITATIONS_USED:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                if len(parts) > 1:
                    cit_text = parts[1].strip()
                    citations_used = [int(x.strip()) for x in re.findall(r'\d+', cit_text)]

            # Create Citation objects
            created_citations = []
            for cit_id in citations_used:
                if cit_id in chunk_map:
                    chunk = chunk_map[cit_id]
                    # Extract a relevant quote
                    quote = chunk.text[:200] if len(chunk.text) > 200 else chunk.text
                    citation = self.context.cite(
                        doc_name=chunk.doc_name,
                        page=chunk.page,
                        quote=quote,
                        chunk_idx=chunk.chunk_idx
                    )
                    created_citations.append(citation)

            # Check for uncited claims (simple heuristic: sentences without [#])
            uncited = []
            sentences = re.split(r'[.!?]+', summary)
            for sent in sentences:
                sent = sent.strip()
                if sent and len(sent) > 30 and '[' not in sent:
                    # Potential uncited claim
                    uncited.append(sent)

            return {
                "summary": summary,
                "citations": created_citations,
                "uncited_claims": uncited[:5]  # Limit to first 5
            }

        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return {
                "summary": f"[ERROR] Summarization failed: {str(e)}",
                "citations": [],
                "uncited_claims": []
            }

    # ============== CODE EXECUTION ==============

    def execute_code(self, code: str) -> Tuple[str, Any]:
        """
        Execute a code block in the sandboxed namespace.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (printed output, last expression result)
        """
        # Clear output buffer
        self._output_buffer = io.StringIO()

        # Refresh namespace with any user variables
        self.namespace.update(self._user_namespace)

        result = None
        error = None

        try:
            # Compile the code
            # Try as expression first (to capture return value)
            try:
                compiled = compile(code, "<repl>", "eval")
                result = eval(compiled, self.namespace)
            except SyntaxError:
                # Not a single expression - try to execute statements and evaluate last line
                lines = code.strip().split('\n')

                # Execute all but the last line
                if len(lines) > 1:
                    setup_code = '\n'.join(lines[:-1])
                    compiled = compile(setup_code, "<repl>", "exec")
                    exec(compiled, self.namespace)

                    # Try to evaluate the last line as an expression
                    last_line = lines[-1].strip()
                    if last_line and not last_line.startswith('#'):
                        try:
                            compiled_last = compile(last_line, "<repl>", "eval")
                            result = eval(compiled_last, self.namespace)
                        except SyntaxError:
                            # Last line is also a statement, just execute it
                            compiled_last = compile(last_line, "<repl>", "exec")
                            exec(compiled_last, self.namespace)
                else:
                    # Single statement, just execute
                    compiled = compile(code, "<repl>", "exec")
                    exec(compiled, self.namespace)

            # Capture any new variables created
            for key, value in self.namespace.items():
                if key not in self._build_namespace() and not key.startswith('_'):
                    self._user_namespace[key] = value

        except Exception as e:
            error = f"Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self._safe_print(error)

        output = self._output_buffer.getvalue()

        # If result is meaningful, show it
        if result is not None and not error:
            if isinstance(result, (list, dict)) and len(str(result)) > 500:
                result_preview = str(result)[:500] + "..."
            else:
                result_preview = result
            return output, result_preview

        return output, result

    def get_user_variables(self) -> Dict[str, Any]:
        """Get all variables created by user code."""
        return self._user_namespace.copy()
