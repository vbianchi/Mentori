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
import ast
import contextlib
import io
import signal
import sys
import threading
import time
import traceback
import json
import re
import logging

from backend.agents import lock_adapter
from experiments.runner import run_context as rc   # importable once lock_adapter has put the repository on sys.path

from .context import RLMContext, ChunkResult, Citation, SEARCH_FUNCTIONS, SearchToolRemoved

logger = logging.getLogger(__name__)

# A refusal by the lock or the run context means the run's own setup is wrong: it ends the run, whatever the
# model's code does with it (Q38, D69; it is never shown to the model as a traceback it could catch and ignore)
SETUP_ERRORS = (lock_adapter.LockError, rc.RunContextError)


class BlockTimeLimit(BaseException):
    """Q5 (D68): raised into a code block whose code time passed RLMExecutor.BLOCK_CODE_LIMIT_S. A BaseException,
    so the model's own `except Exception` does not swallow it."""


class RLMExecutor:
    """
    Executes LLM-generated code in a sandboxed environment.

    The namespace is carefully controlled to only expose safe operations
    that allow document analysis without arbitrary code execution risks.
    """

    # Q5 (D68): a code block may run 120 s of code time (S141 used 120 s). The clock pauses while a sub-call is in
    # flight (LOCK timeout "none"), and every firing is recorded in timer_firings. Replaces MAX_EXECUTION_TIME = 60,
    # which was defined and never used (limits #104). The 50,000-character print cap is removed (D25, cuts.md
    # executor.py:147/:268).
    # On the main thread the clock is a SIGALRM interval timer (as S141's 120 s timer), so it also stops time spent
    # inside library code the block called: a regex the model wrote (search_regex, re). A single C call
    # (sum(range(...))) is stopped as soon as it returns. Q72 (D75): time in search_semantic counts as code time, but
    # the clock never raises inside it (the retriever, the vector store and the one shared reranker stay whole for the
    # next answer): a firing during the search is held and raised as soon as search_semantic returns, as for a single
    # C call; each firing records the block's retrieval seconds (retrieval_s). Off the main thread, where a signal
    # cannot be used, the clock is read at each line of the model's code (never inside a search). Once the limit
    # fires, BlockTimeLimit is raised again at every line of the model's code and every BLOCK_REFIRE_S, so a block
    # whose code catches it still stops.
    BLOCK_CODE_LIMIT_S = 120.0
    BLOCK_REFIRE_S = 1.0

    def __init__(self, context: RLMContext, model_router, model_identifier: str):
        """
        Initialize the executor.

        Args:
            context: The RLMContext managing document state
            model_router: ModelRouter (kept; the sub-calls call lock_adapter directly)
            model_identifier: Model to use for recursive calls
        """
        self.context = context
        self.router = model_router
        self.model_identifier = model_identifier

        # Accumulated output from print statements
        self._output_buffer = io.StringIO()

        # F2 (A10): the final answer a block set with FINAL() or FINAL_VAR(), and the block's error (None if none)
        self.final: Any = None
        self.final_set = False
        self.last_error: Optional[str] = None
        self.setup_error: Optional[BaseException] = None

        # Records (A6/D37): blocks run, Q5 timer firings, failed sub-calls (A5)
        self.n_blocks_run = 0
        self.timer_firings: List[Dict[str, Any]] = []
        self.sub_call_failures: List[Dict[str, Any]] = []

        # Q5 clock of the running block
        self._block_t0: Optional[float] = None
        self._inflight_s = 0.0
        self._inflight_since: Optional[float] = None
        self._fired = False
        self._alarm = False   # True while a block runs under the SIGALRM clock (main thread)
        self._in_block = False
        # Q72 (D75): the block's time in search_semantic, the one in progress, and a firing held until it returns
        self._retrieval_s = 0.0
        self._retrieval_since: Optional[float] = None
        self._held = False
        self.context.retrieval_guard = self._retrieval_guard

        # Build the execution namespace. It persists between blocks as it is (F26, A10: the copy of the first value
        # of each variable, written back at the start of every block, is deleted); _base_keys are the names it
        # starts with, so get_user_variables() returns what the code created
        self.namespace = self._build_namespace()
        self._base_keys = frozenset(self.namespace)

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

            # Search Functions. D80 V5: the RLM's keyword and regex searches rerank (rlm_search_keyword,
            # rlm_search_regex); the context's search_keyword and search_regex stay unreranked for the orchestrator tools
            "search_keyword": self.context.rlm_search_keyword,
            "search_regex": self.context.rlm_search_regex,
            "search_semantic": self.context.search_semantic,

            # LLM Calls (synchronous calls under the lock, lock_adapter.generate)
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

            # F2 (A10): FINAL(x) and FINAL_VAR(x) set the final answer to x as the block runs (FINAL was undefined,
            # and FINAL_VAR was found by scanning the code text and then evaluated a second time)
            "FINAL": self._final,
            "FINAL_VAR": self._final,
        }

        if not getattr(self.context, "search_tools", True):   # a context without the attribute (check_rlm's old ones) is on
            # D239: the search functions are removed (RLMOrchestrator(search_tools=False) ran
            # context.remove_search_tools before this executor was built). Each REPL name is bound to a function that
            # logs the attempt (context.search_attempts, via "repl") and raises SearchToolRemoved, so a call fails
            # visibly in the block's output; the navigation reads and everything else stay as above
            for name in SEARCH_FUNCTIONS:
                namespace[name] = self._removed_search(name)

        return namespace

    def _removed_search(self, name: str) -> Callable:
        """D239: the REPL's stand-in for a removed search function."""
        def removed(*args, **kwargs):
            self.context._refuse_search(name, via="repl")
            raise SearchToolRemoved(f"{name} is not available")   # not reached: _refuse_search raises when search is off
        removed.__name__ = name
        return removed

    def _final(self, value):
        """F2 (A10): set the final answer once per block (a second FINAL in the same block is ignored) and return
        the value. The orchestrator accepts it only from a block that ended with no error."""
        if not self.final_set:
            self.final = value
            self.final_set = True
        return value

    def _safe_print(self, *args, **kwargs):
        """Safe print that captures output, whole (D25: the 50,000-character cap is removed)."""
        output = io.StringIO()
        print(*args, file=output, **kwargs)
        self._output_buffer.write(output.getvalue())

    def _sub_call(self, fn: str, chunks: Optional[List[Any]], prompt: str) -> Dict[str, Any]:
        """One sub-call under the lock (lock_adapter.generate; the lock sets every option, so none is passed:
        cuts.md executor.py:279-492, rlm F13).
        - A6/D37: the passage ids of the chunks it carries are set right before the call ([] when it carries none,
          so an earlier call's passages never reach its record).
        - Q3 (D68): a successful call counts in context.sub_calls_ok, which the quality gate reads. Q65 (D75): a
          successful call whose passage argument was an empty list counts in context.sub_calls_empty instead (a
          call with no passage argument, llm_query(prompt), or with passages given as strings counts as before).
        - A5 (rlm F12): a failed call (LockCallError: status error, stalled, ...) counts in sub_calls_failed, is
          listed in sub_call_failures with its record's seq, and raises into the code block as a traceback; it is
          never returned as "[ERROR] ..." text or "" for the model to save. A LockError or RunContextError is kept
          in setup_error and ends the run (execute_code raises it).
        - D89 (Q145 O3): a Gemini reply Google blocked, or an empty reply that ended with no finishReason, returns
          as empty text (the lock adapter's _finish; D89 also returned a recitation stop so, until D90 below), as
          Mentori's submitted client returned
          it (its own sub-call path, _run_sync_gemini in executor.py at 96e2193:111-116, returned response.text or "",
          and "" after a failed call, :135), so the code goes
          on with "". It still counts in sub_calls_failed, never in sub_calls_ok, and is listed in sub_call_failures
          with its seq and "returned": "empty text", as it was counted before D89 when it raised
          (gemini_client.raised_before_d89), so the quality gate's count is unchanged. A STOP "empty" reply counts
          as before D89 (sub_calls_ok, or sub_calls_empty under Q65).
        - D90 (Q1, Q2): a recitation stop, and a malformed_function_call or malformed_response reply, returns the
          text the stream held (lock_adapter._returned; "" when it held none), so the code goes on with it, as the
          submitted _run_sync_gemini returned response.text or "" whatever the finishReason (96e2193:111-116). Each
          raised before D89 and counts as before (sub_calls_failed, listed with "returned": "empty text" or
          "its text (N characters)"): Rule 10 counts it as a failed call, and the gate counts successful sub-calls
          (Q3, D68).
        - Q5: the block's clock pauses while the call is in flight."""
        ids = [c.chunk_id for c in (chunks or []) if isinstance(c, ChunkResult) and c.chunk_id]
        empty = isinstance(chunks, (list, tuple)) and len(chunks) == 0   # Q65: handed an empty list of passages
        self.context.llm_calls_made += 1
        self._inflight_since = time.monotonic()
        if self._alarm:
            signal.setitimer(signal.ITIMER_REAL, 0)   # Q5: the clock stops while the call is in flight
        try:
            rc.set_passages(ids)
            response = lock_adapter.generate(model_identifier=self.model_identifier, prompt=prompt)
        except lock_adapter.LockCallError as e:
            self.context.sub_calls_failed += 1
            rec = e.record or {}
            self.sub_call_failures.append({"fn": fn, "turn": self.context.current_turn, "seq": rec.get("seq"),
                                           "status": rec.get("status"), "error": rec.get("error")})
            raise
        except SETUP_ERRORS as e:
            self.setup_error = e
            raise
        finally:
            self._inflight_s += time.monotonic() - self._inflight_since
            self._inflight_since = None
            if self._alarm:
                self._arm()   # Q5: the clock goes on with the block's code time left
        rec = response.get("lock_record") or {}
        if rec.get("provider") == "gemini" and lock_adapter.gemini_client.raised_before_d89(rec):
            # D89, D90: returned (empty text, or the text a recitation or malformed reply held), counted as failed as
            # before D89 (when it raised)
            self.context.sub_calls_failed += 1
            text = response.get("response") or ""
            self.sub_call_failures.append({"fn": fn, "turn": self.context.current_turn, "seq": rec.get("seq"),
                                           "status": rec.get("status"), "error": rec.get("error"),
                                           "returned": (f"its text ({len(text)} characters)" if text
                                                        else "empty text")})
        elif empty:
            self.context.sub_calls_empty += 1   # Q65 (D75): it read no passage, so the gate does not count it
        else:
            self.context.sub_calls_ok += 1
        self.context.total_tokens_used += response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
        return response

    # ============== LLM SUB-CALLS ==============
    # The LLM generates sync code, and execute_code runs it on the caller's
    # thread (the RLM loop's event-loop thread). Each sub-call calls
    # lock_adapter.generate there (_sub_call), for every provider, so the run
    # context of the question is the one the call reads.

    def _sync_llm_query(self, prompt: str, context_chunks: List[Any] = None,
                        max_tokens: int = 2000) -> str:
        """
        Synchronous wrapper for LLM query.

        Args:
            prompt: The prompt for the LLM
            context_chunks: Optional list of ChunkResult or strings to include
            max_tokens: accepted and ignored (rlm F13: the lock sets every option; it was a hidden 2,000-token cap)
        """
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

        # Under the lock; a failed call raises into the block (A5)
        return self._sub_call("llm_query", context_chunks, full_prompt).get("response", "")

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

        # Under the lock; a failed call raises into the block (A5), never {"error": ...}
        result_text = self._sub_call("llm_extract", chunks, prompt).get("response", "")

        # F16 (A10, limits #17): the whole JSON object from the first "{", nested objects included (the old
        # pattern kept only the first flat {...}); a reply that does not parse is returned raw, marked as such
        start = result_text.find("{")
        if start != -1:
            try:
                obj, _ = json.JSONDecoder().raw_decode(result_text[start:])
                return obj
            except json.JSONDecodeError:
                pass
        return {"error": "Could not parse extraction result", "raw": result_text}

    def _sync_llm_summarize(self, chunks: List[Any], max_tokens: int = 500,
                            task: str = None) -> Dict[str, Any]:
        """
        Summarize chunks with mandatory citation tracking.

        Args:
            chunks: Chunks to summarize
            max_tokens: accepted and ignored (rlm F13: the lock sets every option; it was a hidden 700-token cap)
            task: Optional specific summarization task

        Returns:
            Dict with 'summary', 'citations', and 'uncited_claims'
        """
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

        # Under the lock; a failed call raises into the block (A5), never "[ERROR] Summarization failed" as a summary
        result_text = self._sub_call("llm_summarize", chunks, prompt).get("response", "")

        # F16 (A10): split on CITATIONS_USED: whether or not SUMMARY: is present, and read the chunk numbers from
        # the first line after it only (it took every number in the rest of the reply, and none without SUMMARY:)
        summary_part, _, cit_part = result_text.partition("CITATIONS_USED:")
        summary = summary_part.replace("SUMMARY:", "").strip()
        cit_lines = cit_part.strip().splitlines()
        citations_used = [int(x) for x in re.findall(r'\d+', cit_lines[0])] if cit_lines else []
        # The uncited-claims check below reads the summary as the model wrote it, with [k] citations: the full stop
        # in a rewritten [paper.pdf:pN] would split a cited sentence and report its tail as uncited (review D1)
        raw_summary = summary

        # Q8 (D68): each inline [k] (or [k, m]) naming chunks of this call is written as [paper.pdf:pN], the format
        # exp1 parses; each call numbered its own chunks 1..n, so [k] named a different source in the Sources list
        def _inline(m):
            nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
            if nums and all(n in chunk_map for n in nums):
                return "".join(f"[{chunk_map[n].doc_name}:p{chunk_map[n].page}]" for n in nums)
            return m.group(0)
        summary = re.sub(r'\[(\d+(?:\s*,\s*\d+)*)\]', _inline, summary)

        # Create Citation objects
        created_citations = []
        for cit_id in citations_used:
            if cit_id in chunk_map:
                chunk = chunk_map[cit_id]
                # The whole chunk is the quote (D25, cuts.md executor.py:518: it kept the first 200 characters)
                citation = self.context.cite(
                    doc_name=chunk.doc_name,
                    page=chunk.page,
                    quote=chunk.text,
                    chunk_idx=chunk.chunk_idx
                )
                created_citations.append(citation)

        # Check for uncited claims (simple heuristic: sentences without [#])
        uncited = []
        sentences = re.split(r'[.!?]+', raw_summary)
        for sent in sentences:
            sent = sent.strip()
            if sent and len(sent) > 30 and '[' not in sent:
                # Potential uncited claim
                uncited.append(sent)

        return {
            "summary": summary,
            "citations": created_citations,
            "uncited_claims": uncited  # every one (D25, cuts.md executor.py:539: it kept the first 5)
        }

    # ============== CODE EXECUTION ==============

    def execute_code(self, code: str) -> Tuple[str, Any]:
        """
        Execute a code block in the sandboxed namespace.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (printed output, last expression result). The result is whole (D25, cuts.md executor.py:616:
            a list or dict was cut to 500 characters). After the call, last_error holds the block's error (None if
            it ran clean) and final / final_set what FINAL() or FINAL_VAR() set in this block.

        Raises:
            LockError or RunContextError (SETUP_ERRORS) raised by a sub-call in this block, even if the block's own
            code caught it (Q38).
        """
        # Clear output buffer and the block's final answer, error and clock
        self._output_buffer = io.StringIO()
        self.final = None
        self.final_set = False
        self.last_error = None
        self.setup_error = None
        self.n_blocks_run += 1
        self._block_t0 = time.monotonic()
        self._inflight_s = 0.0
        self._inflight_since = None
        self._fired = False
        self._retrieval_s = 0.0
        self._retrieval_since = None
        self._held = False

        result = None
        error = None

        try:
            # F1 (A10): parse the block whole with ast. If its last statement is an expression (and the block's last
            # line is not a comment, which keeps the old result None for "y = 5\ny\n# comment"), run the rest and
            # evaluate it as the result; else run the whole block. Splitting off the last text line made a block
            # that ends inside a loop or a multi-line call fail with IndentationError (307 of 481 deposited errors).
            tree = ast.parse(code, "<repl>", "exec")
            lines = code.rstrip().splitlines()
            last_line = lines[-1].lstrip() if lines else ""
            old_trace = sys.gettrace()
            self._in_block = True
            # Q5: the SIGALRM clock on the main thread; elsewhere the clock is read at each line of the block's code
            self._alarm = threading.current_thread() is threading.main_thread()
            if self._alarm:
                old_handler = signal.signal(signal.SIGALRM, self._on_alarm)
                self._arm()
            else:
                sys.settrace(self._trace_call)
            try:
                if tree.body and isinstance(tree.body[-1], ast.Expr) and not last_line.startswith('#'):
                    head = ast.Module(body=tree.body[:-1], type_ignores=[])
                    exec(compile(head, "<repl>", "exec"), self.namespace)
                    result = eval(compile(ast.Expression(body=tree.body[-1].value), "<repl>", "eval"),
                                  self.namespace)
                else:
                    exec(compile(tree, "<repl>", "exec"), self.namespace)
            finally:
                if self._alarm:
                    # A signal still pending here finds no frame of the block's code and raises nothing (_on_alarm)
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, old_handler)
                    self._alarm = False
                self._in_block = False
                sys.settrace(old_trace)

        except SETUP_ERRORS:
            raise
        except BlockTimeLimit as e:
            error = f"Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self._safe_print(error)
        except Exception as e:
            error = f"Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self._safe_print(error)

        if self.setup_error is not None:
            raise self.setup_error   # Q38: the block's code caught it; the run still ends

        if self._fired and error is None:
            # The limit fired and the block's own code caught it (a bare except): the block still counts as failed
            error = (f"Error: BlockTimeLimit: the block passed {self.BLOCK_CODE_LIMIT_S:.0f} s of code time "
                     "(caught by the block's code)")
            self._safe_print(error)
            self.timer_firings[-1]["caught_by_code"] = True
        elif self._fired and self.timer_firings[-1]["raises"] > 1:
            self.timer_firings[-1]["caught_by_code"] = True   # the first raise was caught; a later one ended it

        self.last_error = error
        output = self._output_buffer.getvalue()
        return output, (result if error is None else None)

    def _code_s(self, now: float) -> float:
        """Q5: the running block's code time, its wall time less the time its sub-calls were in flight."""
        inflight = self._inflight_s + (now - self._inflight_since if self._inflight_since is not None else 0.0)
        return (now - self._block_t0) - inflight

    def _arm(self):
        """Q5: arm the SIGALRM clock with the block's code time left (BLOCK_REFIRE_S once the limit has fired)."""
        left = self.BLOCK_REFIRE_S if self._fired else self.BLOCK_CODE_LIMIT_S - self._code_s(time.monotonic())
        signal.setitimer(signal.ITIMER_REAL, max(left, 1e-3))

    def _fire(self, now: float):
        """Q5: record the firing (the first raise into the block) or count a raise after it, and return the error.
        From the first firing on, every line of the model's code raises it again."""
        if not self._fired:
            self._fired = True
            code_s = self._code_s(now)
            retrieval_s = self._retrieval_s + (now - self._retrieval_since if self._retrieval_since is not None
                                               else 0.0)
            self.timer_firings.append({"turn": self.context.current_turn, "block": self.n_blocks_run,
                                       "limit_s": self.BLOCK_CODE_LIMIT_S, "code_s": round(code_s, 3),
                                       "wall_s": round(now - self._block_t0, 3),
                                       "retrieval_s": round(retrieval_s, 3),   # Q72: of code_s, in search_semantic
                                       "caught_by_code": False, "raises": 1})
        else:
            self.timer_firings[-1]["raises"] += 1
        return BlockTimeLimit(f"the block passed {self.BLOCK_CODE_LIMIT_S:.0f} s of code time "
                              f"(sub-call time excluded); it was stopped")

    @staticmethod
    def _repl_frames(frame) -> List[Any]:
        """The frames of the block's code ("<repl>") on the stack from frame down."""
        out = []
        while frame is not None:
            if frame.f_code.co_filename == "<repl>":
                out.append(frame)
            frame = frame.f_back
        return out

    def _fire_into(self, repl_frames) -> BlockTimeLimit:
        """Q5: record the firing and return the error to raise. On the first firing the line trace is switched on
        for the block's frames, so the block's own `except` cannot keep it running; on the main thread the clock
        re-fires every BLOCK_REFIRE_S."""
        err = self._fire(time.monotonic())
        for f in repl_frames:
            f.f_trace = self._trace_line
        sys.settrace(self._trace_call)
        if self._alarm:
            signal.setitimer(signal.ITIMER_REAL, self.BLOCK_REFIRE_S)
        return err

    def _on_alarm(self, signum, frame):
        """Q5, main thread: the SIGALRM handler. Raises BlockTimeLimit into the block's code, or into library code
        the block called, while a frame of the block's code ("<repl>") is on the stack; a signal that arrives after
        the block's code has returned raises nothing. Q72 (D75): a signal that arrives while search_semantic runs is
        held, and _retrieval_guard raises it as the search returns."""
        repl_frames = self._repl_frames(frame)
        if not repl_frames or self._inflight_since is not None:
            return
        if self._retrieval_since is not None:
            self._held = True
            return
        raise self._fire_into(repl_frames)

    @contextlib.contextmanager
    def _retrieval_guard(self):
        """Q72 (D75): search_semantic runs inside this (context.retrieval_guard). Its time counts as the block's code
        time and is summed in _retrieval_s; a firing of the clock during it is held (_on_alarm) and raised here, as
        soon as the search returns, so the clock never raises inside the retriever, the store or the reranker. If the
        search itself raised, a held firing replaces its error: the block was past its limit."""
        if not self._in_block or self._retrieval_since is not None:
            yield   # outside a block, or a search inside a search: nothing to hold
            return
        self._retrieval_since = time.monotonic()
        try:
            yield
        finally:
            self._retrieval_s += time.monotonic() - self._retrieval_since
            self._retrieval_since = None
            if self._held:
                self._held = False
                repl_frames = self._repl_frames(sys._getframe())
                if repl_frames:
                    raise self._fire_into(repl_frames)

    def _trace_call(self, frame, event, arg):
        """Q5: trace only the model's code (frames compiled from "<repl>", its own functions included)."""
        if frame.f_code.co_filename != "<repl>":
            return None
        return self._trace_line

    def _trace_line(self, frame, event, arg):
        """Q5: at each line of the model's code (never while a sub-call is in flight), raise BlockTimeLimit once
        the block's code time passes the limit, and at every line after that."""
        if event == "line" and self._inflight_since is None:
            now = time.monotonic()
            if self._fired or self._code_s(now) > self.BLOCK_CODE_LIMIT_S:
                raise self._fire(now)
        return self._trace_line

    def get_user_variables(self) -> Dict[str, Any]:
        """Get all variables created by user code (the namespace less the names it started with, F26)."""
        return {k: v for k, v in self.namespace.items() if k not in self._base_keys and not k.startswith('_')}
