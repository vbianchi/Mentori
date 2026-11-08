"""
RLM Orchestrator - Main execution loop for Recursive Language Model.

The orchestrator:
1. Initializes the REPL environment with document context
2. Prompts the LLM to write code for document analysis
3. Executes code blocks and feeds output back to LLM
4. Continues until FINAL() answer or max turns reached
"""

import re
from typing import Optional, AsyncGenerator, Dict, Any, List, Union
from dataclasses import dataclass

from .context import RLMContext, SEARCH_FUNCTIONS, NAVIGATION_FUNCTIONS
from .executor import RLMExecutor

# Use Mentori's session logger for consistent output in Docker
from backend.agents.session_context import get_logger
from backend.agents.prompts import get_rlm_orchestrator_prompt
from backend.agents.lock_adapter import LockCallError
from experiments.runner import run_context as rc   # on sys.path once lock_adapter is imported

logger = get_logger(__name__)

# A6/D37 (rlm F21): how a run ended. The first five return an answer; the last two end with no answer (A5: a
# failure is recorded, never stored as an answer): run() raises RLMRunError carrying the same metadata.
STOP_REASONS = ("final", "final_after_max_rejections", "auto_generated", "max_turns_partial",
                "max_turns_auto_generated", "max_turns_empty", "call_error")

# Q11 (D68): kept in the judged answer, what Mentori returns at its turn limit; the stop reason records it
TURN_LIMIT_NOTE = "\n\n---\n*Note: Analysis reached turn limit. Results may be incomplete.*"

# D80 V4 (audit F7): the message sent after a root reply that stopped at the output limit (done_reason "length":
# Ollama's length, Gemini's MAX_TOKENS). None of that reply's code blocks runs; the turn is counted in length_turns
CUT_REPLY_NOTE = "Your previous reply was cut off by the output limit, so none of its code was run."

# Quality gate, stated count rules (rlm "Limits that stay as stated decisions")
MIN_LLM_CALLS = 3          # Q3 (D68): successful llm_summarize/llm_query/llm_extract sub-calls, not root turns;
                           # Q65 (D75): not those handed an empty list of passages (sub_calls_empty)
MAX_EARLY_REJECTIONS = 3   # after this many rejections a final answer is accepted (final_after_max_rejections)

# D238 (G14, a proof-of-concept ablation): RLMOrchestrator(quality_gate=False) turns the quality gate off. Off, no final
# answer is ever refused by it: insufficient_work is False whatever sub_calls_ok and has_substance are, so no rejection
# message is sent, rejections stays 0 and no answer ends final_after_max_rejections. What runs after the gate is
# unchanged: a final answer that is empty with no citation is still passed over (empty_finals_dropped), one empty with
# citations is still auto-generated (auto_generated), the turn limit and every nudge are as before. The default, True,
# is the gate every run had. An off run's record carries GATE_OFF_RECORD under "quality_gate"; a gated run's record
# has no such key, so its record is as before.
GATE_OFF_RECORD = {"on": False, "decision": "D238", "min_llm_calls": MIN_LLM_CALLS,
                   "max_early_rejections": MAX_EARLY_REJECTIONS}

# D239 (arm B, a proof of concept): RLMOrchestrator(search_tools=False) removes the RLM's search functions. At the start
# of the run it calls context.remove_search_tools(): the REPL's search_keyword, search_regex and search_semantic (the
# rlm_ wrappers and the context's own searches) raise SearchToolRemoved and are logged in context.search_attempts; the
# navigation reads stay. The system prompt is prompts.RLM_ORCHESTRATOR_PROMPT_NOSEARCH (prompts.RLM_NOSEARCH_PROMPT_EDITS),
# and the two nudges whose code calls a search (turn6_example, emergency) write navigation reads instead
# (_nosearch_find). Everything else is as before, the quality gate included. The default, True, is every run before
# D239. An off run's record carries SEARCH_OFF_RECORD plus "attempts" and "n_attempts" under "search_tools"; an on run's
# record has no such key, so its record is as before.
SEARCH_OFF_RECORD = {"on": False, "decision": "D239", "removed": list(SEARCH_FUNCTIONS),
                     "kept": list(NAVIGATION_FUNCTIONS)}


class RLMResult(str):
    """The answer of an RLM run: a str (callers that store the answer string keep working) with .metadata, the
    run's record (A6/D37; keys in RLMOrchestrator._metadata)."""

    def __new__(cls, answer: str, metadata: Optional[Dict[str, Any]] = None):
        obj = super().__new__(cls, answer)
        obj.metadata = metadata or {}
        return obj

    def __reduce__(self):
        return (RLMResult, (str(self), self.metadata))


class RLMRunError(RuntimeError):
    """A run that ended with no answer (stop_reason max_turns_empty or call_error). .metadata is the run's record,
    in the same shape as RLMResult.metadata."""

    def __init__(self, message: str, metadata: Dict[str, Any]):
        super().__init__(message)
        self.metadata = metadata


@dataclass
class RLMEvent:
    """Event emitted during RLM execution for streaming progress."""
    type: str  # "thinking", "code", "output", "progress", "final", "error"
    content: str
    metadata: Dict[str, Any] = None


class RLMOrchestrator:
    """
    Main RLM execution loop.

    Coordinates the interaction between LLM code generation and
    the REPL environment for systematic document analysis.

    Note: System prompt is now centralized in backend/agents/prompts.py
    """

    def __init__(
        self,
        model_router,
        model_identifier: str,
        max_turns: int = 20,
        verify: bool = False,
        think: Union[bool, str, None] = False,
        verbose: bool = False,
        quality_gate: bool = True,
        search_tools: bool = True,
    ):
        """
        Initialize the orchestrator.

        Args:
            model_router: ModelRouter instance for LLM calls
            model_identifier: Model to use (e.g., "ollama::llama3")
            max_turns: Maximum REPL iterations
            verify: If True, run a verification pass on the final report.
                    This approximately doubles the LLM cost but flags
                    unsupported claims.
            think: recorded as caller_asked in each root call's record and never sent (the lock sets thinking, D66)
            verbose: If True, print per-turn diagnostics to stdout.
            quality_gate: True (the default, every run before D238): a final answer is refused while fewer than
                    MIN_LLM_CALLS sub-calls succeeded or it has no substance, up to MAX_EARLY_REJECTIONS times. False
                    (D238, G14 only): never refused by the gate (GATE_OFF_RECORD, above); recorded in the run's record.
            search_tools: True (the default, every run before D239): the REPL has its search functions. False (D239,
                    arm B only): they are removed, the prompt and the two search nudges name none of them
                    (SEARCH_OFF_RECORD, above); recorded in the run's record with every refused attempt.
        num_ctx is deleted (cuts.md orchestrator.py:51): the lock sets the context.
        """
        if not isinstance(quality_gate, bool):
            raise TypeError(f"quality_gate must be True or False, got {quality_gate!r}")
        if not isinstance(search_tools, bool):
            raise TypeError(f"search_tools must be True or False, got {search_tools!r}")
        self.router = model_router
        self.model_identifier = model_identifier
        self.max_turns = max_turns
        self.verify = verify
        self.think = think
        self.verbose = verbose
        self.quality_gate = quality_gate
        self.search_tools = search_tools

    async def run(self, task: str, context: RLMContext) -> RLMResult:
        """
        Execute the RLM loop until completion.

        Args:
            task: The research task to perform
            context: Initialized RLMContext with documents

        Returns:
            RLMResult: the answer (a str) with .metadata, the run's record (stop_reason final,
            final_after_max_rejections, auto_generated, max_turns_partial or max_turns_auto_generated).

        Raises:
            RLMRunError (with .metadata) when the run ends with no answer: stop_reason max_turns_empty or call_error
            (a root call that failed, A5). LockError and RunContextError are not caught (Q38): they end the run.
        """
        async for event in self.run_stream(task, context):
            if event.type == "final":
                return RLMResult(event.content, event.metadata)
            elif event.type == "error":
                raise RLMRunError(event.content, event.metadata)

        raise RuntimeError("RLM loop ended without producing a result")

    def _metadata(self, stop_reason: str, context: RLMContext, executor: RLMExecutor, st: Dict[str, Any],
                  target_doc: Optional[str], **extra) -> Dict[str, Any]:
        """The run's record (A6/D37, rlm F21), returned with the answer or carried by RLMRunError:
        stop_reason (STOP_REASONS); turns (root calls made) and max_turns; rejections (quality-gate rejections),
        empty_finals_dropped (empty final answers with no citation, passed over as before), blank_finals_skipped
        (a final answer of "" or None, passed over before the gate as before) and
        accepted_after_max_rejections; length_turns (D80 V4: root replies cut by the output limit, whose code did
        not run) and length_blocks_not_run (the code blocks those replies held); sub_calls_ok, sub_calls_failed
        and sub_call_failures (fn, turn, record seq,
        status, error); sub_calls_empty (Q65: successful sub-calls handed an empty list of passages, not counted by
        the gate); n_code_blocks_run and code_block_errors; nudges (turn and kind of every message the loop
        added); passages_seen (index ids of every chunk returned to the code) and retrievals (each call: turn, fn,
        query, doc_name, ids, delivered, reranked and rerank_skipped (D80 V5); for search_semantic outside_filter
        and top_k; for the RLM's search_keyword and search_regex top_k, n_hits, n_candidates (at most candidate_width, FUSED_WIDTH x top_k, except an empty query: every hit, rerank_skipped "empty_query"), rerank_capped and rerank_scores; Q150, D83: search_s on every entry, the seconds the logging function took, and for search_semantic load_s, the retriever's load seconds within it); timer_firings (Q5; retrieval_s, Q72);
        citations (whole quotes); report_sections; target_document (Q1: only an explicit .pdf name);
        turn_limit_note (Q11); call_error (turn, seq, status, error of the failed root call); verify; llm_calls
        and tokens_used (every call, root and sub); n_documents_loaded and n_chunks_loaded (records F29); quality_gate
        (D238), GATE_OFF_RECORD, only when the gate is off (a gated run's record has no such key); search_tools
        (D239), SEARCH_OFF_RECORD with attempts (every refused call: turn, fn, via) and n_attempts, only when the
        search functions are removed (an on run's record has no such key)."""
        if stop_reason not in STOP_REASONS:
            raise ValueError(f"stop_reason {stop_reason!r} is not one of {STOP_REASONS}")
        md = {
            "stop_reason": stop_reason,
            "turns": st["turns"],
            "max_turns": self.max_turns,
            "rejections": st["rejections"],
            "empty_finals_dropped": st["empty_finals_dropped"],
            "blank_finals_skipped": st["blank_finals_skipped"],
            "accepted_after_max_rejections": False,
            "length_turns": st["length_turns"],
            "length_blocks_not_run": st["length_blocks_not_run"],
            "sub_calls_ok": context.sub_calls_ok,
            "sub_calls_failed": context.sub_calls_failed,
            "sub_calls_empty": context.sub_calls_empty,
            "sub_call_failures": list(executor.sub_call_failures),
            "n_code_blocks_run": executor.n_blocks_run,
            "code_block_errors": st["code_block_errors"],
            "nudges": list(st["nudges"]),
            "passages_seen": list(context.passages_seen),
            "retrievals": list(context.retrievals),
            "timer_firings": list(executor.timer_firings),
            "citations": context.citations_record(),
            "report_sections": len(context.report_sections),
            "target_document": target_doc,
            "turn_limit_note": False,
            "call_error": None,
            "verify": None,
            "llm_calls": context.llm_calls_made,
            "tokens_used": context.total_tokens_used,
            "n_documents_loaded": len(context._documents),
            "n_chunks_loaded": context.n_chunks_loaded,
        }
        if not self.quality_gate:
            md["quality_gate"] = dict(GATE_OFF_RECORD)   # D238: an off run's record says so in every answer
        if not self.search_tools:
            # D239: an off run's record says so in every answer, with each refused attempt
            md["search_tools"] = {**SEARCH_OFF_RECORD, "removed": list(SEARCH_OFF_RECORD["removed"]),
                                  "kept": list(SEARCH_OFF_RECORD["kept"]),
                                  "attempts": [dict(a) for a in context.search_attempts],
                                  "n_attempts": len(context.search_attempts)}
        md.update(extra)
        return md

    async def run_stream(self, task: str, context: RLMContext) -> AsyncGenerator[RLMEvent, None]:
        """
        Execute the RLM loop with streaming events.

        Yields RLMEvent objects for progress tracking.
        """
        # Build system prompt with context (from centralized prompts.py)
        # NOTE: We use .replace() instead of .format() because the prompt
        # contains code examples with {target_doc}, {structure[...]}, etc.
        # that .format() would try to resolve, causing KeyError.
        if not self.search_tools:
            context.remove_search_tools()   # D239: before the executor builds its namespace (executor._build_namespace)
        system_prompt = get_rlm_orchestrator_prompt(search_tools=self.search_tools)
        system_prompt = system_prompt.replace("{context_summary}", context.get_context_summary())
        # FILE_ORGANIZATION_RULES not needed for RLM (it works in a REPL, not filesystem)
        system_prompt = system_prompt.replace("{FILE_ORGANIZATION_RULES}", "")

        # Initialize executor
        executor = RLMExecutor(context, self.router, self.model_identifier)

        # Extract target document from task if mentioned
        target_doc_hint = self._extract_target_document(task, context)
        task_content = f"Task: {task}"
        if target_doc_hint:
            task_content += f"\n\n⚠️ TARGET DOCUMENT: {target_doc_hint}\nYou MUST only analyze this specific document. Do NOT switch to other documents."

        # Conversation history
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_content}
        ]

        yield RLMEvent(type="progress", content="Starting RLM analysis...",
                       metadata={"turn": 0, "task": task})

        logger.info(f"=" * 60)
        logger.info(f"RLM STARTING - Task: {task[:100]}...")
        logger.info(f"Model: {self.model_identifier}")
        logger.info(f"Max turns: {self.max_turns}")
        logger.info(f"Documents: {len(context._documents)}")
        logger.info(f"=" * 60)

        # The run's counters for its record (_metadata)
        st = {"turns": 0, "rejections": 0, "empty_finals_dropped": 0, "blank_finals_skipped": 0,
              "code_block_errors": 0, "nudges": [], "length_turns": 0, "length_blocks_not_run": 0}

        def meta(stop_reason: str, **extra) -> Dict[str, Any]:
            return self._metadata(stop_reason, context, executor, st, target_doc_hint, **extra)

        def nudge(turn_no: int, kind: str, content: str) -> None:
            """A message the loop adds to the history, recorded in nudges."""
            messages.append({"role": "user", "content": content})
            st["nudges"].append({"turn": turn_no, "kind": kind})

        for turn in range(self.max_turns):
            print(f"\n{'='*40} RLM Turn {turn + 1}/{self.max_turns} {'='*40}")
            logger.info(f"\n{'='*40} RLM Turn {turn + 1}/{self.max_turns} {'='*40}")
            context.current_turn = turn + 1

            yield RLMEvent(
                type="progress",
                content=f"Turn {turn + 1}",
                metadata={"turn": turn + 1, "progress": context.get_progress()}
            )

            # Get LLM response using chat endpoint, under the lock (router.chat -> lock_adapter.achat). No options
            # are passed (cuts.md orchestrator.py:162); think is recorded as caller_asked and never sent.
            print(f"[Turn {turn+1}] Calling LLM with model: {self.model_identifier}")
            st["turns"] = turn + 1
            context.llm_calls_made += 1
            try:
                # A6/D37: a root turn carries no passage list of its own (what the code printed is in the
                # record's messages_sent), so the last sub-call's passages do not reach its record
                rc.set_passages([])
                response = await self.router.chat(
                    model_identifier=self.model_identifier,
                    messages=messages,
                    think=self.think  # recorded as caller_asked, not sent
                )
            except LockCallError as e:
                # A5 (rlm F12): a failed root call ends the run with stop_reason call_error and no answer. A
                # LockError or RunContextError is not caught: it ends the run (Q38).
                rec = e.record or {}
                logger.error(f"LLM call failed: {e}")
                yield RLMEvent(type="error", content=f"LLM error: {str(e)}", metadata=meta(
                    "call_error", call_error={"turn": turn + 1, "seq": rec.get("seq"), "status": rec.get("status"),
                                              "error": rec.get("error")}))
                return
            # Chat returns {"message": {"role": "assistant", "content": "..."}, "response": "..."} for every provider
            assistant_response = response.get("message", {}).get("content", "") or response.get("response", "")
            # Track tokens from main REPL turns
            turn_tokens = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
            context.total_tokens_used += turn_tokens
            print(f"[Turn {turn+1}] Got response: {len(assistant_response)} chars, {turn_tokens} tokens")

            # Log the LLM response
            logger.info(f"[LLM Response] ({len(assistant_response)} chars)")
            logger.info(f"  Preview: {assistant_response[:200].replace(chr(10), ' ')}...")

            if self.verbose:
                print(f"[VERBOSE Turn {turn+1}] Response length: {len(assistant_response)} chars")
                print(f"[VERBOSE Turn {turn+1}] Response preview: {assistant_response[:300]}...")

            yield RLMEvent(type="thinking", content=assistant_response[:500] + "..." if len(assistant_response) > 500 else assistant_response)

            # Extract code blocks
            code_blocks = self._extract_code_blocks(assistant_response)
            print(f"[Turn {turn+1}] Extracted {len(code_blocks)} code blocks")
            print(f"[Turn {turn+1}] Response preview: {assistant_response[:300]}...")

            if response.get("done_reason") == "length":
                # D80 V4 (audit F7): a reply cut by the output limit is incomplete; none of its blocks runs (1,517
                # blocks of one cut Gemini reply overflowed the next call's input). The reply stays in the history
                # whole, the model is told, and the turn is counted; the end-of-turn checks below still run
                logger.warning(f"[Turn {turn+1}] Reply cut by the output limit - {len(code_blocks)} code block(s) "
                               f"not run")
                st["length_turns"] += 1
                st["length_blocks_not_run"] += len(code_blocks)
                messages.append({"role": "assistant", "content": assistant_response})
                nudge(turn + 1, "length_cut", CUT_REPLY_NOTE)
            elif not code_blocks:
                # No code blocks - prompt LLM to write code. Q7 (D68): the end-of-turn checks below run after this
                # turn too (the old `continue` skipped them, so a prose reply could miss the last-turn message)
                print(f"[Turn {turn+1}] NO CODE BLOCKS - prompting model to write code")
                logger.warning(f"[Turn {turn+1}] NO CODE BLOCKS found in response!")
                logger.info(f"  Full response: {assistant_response[:500]}")
                messages.append({"role": "assistant", "content": assistant_response})
                nudge(turn + 1, "no_code",
                      "Please write Python code in ```repl blocks to proceed with the analysis. "
                      "Start by using list_documents() to see available documents.")
            else:
                ended = None
                async for ev in self._run_blocks(turn, code_blocks, assistant_response, messages, context,
                                                 executor, st, target_doc_hint, meta):
                    if ev.type == "_done":
                        ended = ev   # the last event of _run_blocks
                    else:
                        yield ev
                if ended is not None and ended.metadata:
                    yield ended.metadata["event"]
                    return

            self._end_of_turn_checks(turn, context, target_doc_hint, task, nudge)

        # Max turns reached - check if we have meaningful content
        logger.warning(f"=" * 60)
        logger.warning(f"RLM MAX TURNS REACHED ({self.max_turns})")
        logger.warning(f"Final stats: LLM calls={context.llm_calls_made}, "
                      f"Citations={len(context.citations)}, "
                      f"Report sections={len(context.report_sections)}")
        logger.warning(f"=" * 60)

        report = context.get_report()
        has_report_sections = len(context.report_sections) > 0 and "No report content yet" not in report

        if has_report_sections:
            # We have actual report content - return it as partial success, with the turn-limit note (Q11)
            logger.info("Returning partial report as final result")
            yield RLMEvent(type="final", content=report + TURN_LIMIT_NOTE,
                           metadata=meta("max_turns_partial", turn_limit_note=True))
        elif len(context.citations) > 0:
            # DETERMINISTIC FALLBACK: We have citations but LLM forgot to call add_to_report()
            # Auto-generate a report from the collected citations
            logger.warning(f"LLM collected {len(context.citations)} citations but never saved to report!")
            logger.info("Using deterministic fallback: auto-generating report from citations")
            yield RLMEvent(type="final", content=context.auto_generate_report_from_citations(),
                           metadata=meta("max_turns_auto_generated"))
        else:
            # Truly empty - no citations, no report: no answer (A5)
            yield RLMEvent(
                type="error",
                content=f"Maximum turns ({self.max_turns}) reached without completion. "
                        f"No meaningful analysis was produced (0 citations, 0 report sections).",
                metadata=meta("max_turns_empty")
            )

    async def _run_blocks(self, turn, code_blocks, assistant_response, messages, context, executor, st,
                          target_doc_hint, meta):
        """Run one reply's code blocks, check a final answer, and add the reply and its output to the history.
        Yields the code and output events; the last event is type "_done", whose metadata["event"] is the run's
        final event when the run ends here (else metadata is None)."""
        logger.info(f"[Turn {turn+1}] Found {len(code_blocks)} code block(s)")

        # Q4 (D68): every block of the reply runs, in order, up to and including the one that sets the final
        # answer (only the first 2 ran, while the whole reply entered the history)
        all_outputs = []
        for i, code in enumerate(code_blocks):
            print(f"[Turn {turn+1}] Executing code block {i+1}:")
            print(f"  Code: {code[:150]}...")
            logger.info(f"[Code Block {i+1}]\n{code[:300]}{'...' if len(code) > 300 else ''}")

            yield RLMEvent(type="code", content=code,
                           metadata={"block": i + 1, "total": len(code_blocks)})

            output, result = executor.execute_code(code)
            print(f"[Turn {turn+1}] Execution output: {output[:200] if output else '(empty)'}...")
            print(f"[Turn {turn+1}] Execution result: {result}")
            if executor.last_error is not None:
                st["code_block_errors"] += 1

            output_text = output
            if result is not None:
                output_text += f"\n→ Result: {result}"

            logger.info(f"[Output {i+1}] {output_text[:300]}{'...' if len(output_text) > 300 else ''}")

            all_outputs.append(f"[Block {i+1}]\n{output_text}")

            yield RLMEvent(type="output", content=output_text)

            if executor.final_set:
                # Q4: the blocks after the one that set the final answer do not run (F2). Q70 (D75): if the run goes
                # on (the final is refused or passed over), the message the model reads says which blocks never ran
                if i + 1 < len(code_blocks):
                    rest = (f"Block {i + 2}" if i + 2 == len(code_blocks)
                            else f"Blocks {i + 2}-{len(code_blocks)}")
                    all_outputs.append(f"[{rest} not run: block {i + 1} set the final answer]")
                break

        # F2 (A10): the final answer is what FINAL() or FINAL_VAR() set while the block ran (executor.final), read
        # once, and accepted only from a block that ended with no error. The code text is no longer scanned and
        # FINAL_VAR's expression is no longer evaluated a second time.
        rejection = None
        blank_final = executor.final_set and executor.last_error is None and executor.final in (None, "")
        if blank_final:
            # A final answer of "" or None is passed over and the run goes on, as Mentori's `if final_answer:` did
            # (review of F2/F3: it is not a rejection and does not end the run); counted in blank_finals_skipped
            logger.warning(f"[Turn {turn+1}] Final answer set to {executor.final!r} - passed over")
            st["blank_finals_skipped"] += 1
        elif executor.final_set and executor.last_error is None:
            logger.info(f"[Turn {turn+1}] Final answer set by the code - checking it")
            final = executor.final
            final_answer = "" if final is None else (final if isinstance(final, str) else str(final))

            # F3 (A10): an answer is empty only if it has no text; a get_report() answer only if no report
            # section has text (answers under 50 characters were rejected, and only a section over 50
            # characters counted as substance)
            final_from_get_report = final_answer == context.get_report()
            # D92 Q184 (audit F1): each section is read as the printed report shows it, str(content), as
            # get_report() prints it (f"{section.content}"), so a list, a dict, None or a number saved with
            # add_to_report counts by its printed text. Before Q184 the line called .strip() on the content and
            # stopped the run with an AttributeError on any such section it reached. For a str, str(content) is
            # content, and any() stops at the first section with text, so on a run the old line did not stop the value
            # is the same, with one exception: bytes, which the old line read with bytes.strip(), so a blank bytes
            # section (b"") counted as empty there and counts now as its printed text "b''". No G1 log or answer holds
            # the AttributeError (D92 Q184); check_rlm section 12 lists both cases.
            sections_have_text = any(str(s.content).strip() for s in context.report_sections)
            is_empty = (not sections_have_text) if final_from_get_report else not final_answer.strip()
            has_substance = (not is_empty) or sections_have_text

            # QUALITY GATE (Q3): successful sub-calls only, and real content. D238: off (quality_gate False), it never
            # refuses, so the answer goes straight to the checks below as an accepted one
            insufficient_work = self.quality_gate and (context.sub_calls_ok < MIN_LLM_CALLS or not has_substance)

            if insufficient_work and st["rejections"] < MAX_EARLY_REJECTIONS:
                # Not enough work done - reject and ask for more analysis. F11 (A10): the rejection follows the
                # reply's output in one message; the reply is no longer added to the history twice.
                st["rejections"] += 1
                logger.warning(f"[Turn {turn+1}] REJECTING early completion - only {context.sub_calls_ok} "
                               f"sub-calls (need {MIN_LLM_CALLS}). Rejection {st['rejections']}/"
                               f"{MAX_EARLY_REJECTIONS}")
                # Q66 (D75): the first sentence names what the gate counts (it said "LLM calls", the label of the
                # progress line's different count). Q122 (D78): calls handed an empty list are named as not counted
                n_ok, n_empty = context.sub_calls_ok, context.sub_calls_empty
                empty_note = (f" ({n_empty} more {'was' if n_empty == 1 else 'were'} given an empty list of passages "
                              f"and do{'es' if n_empty == 1 else ''} not count)") if n_empty > 0 else ""
                rejection = (f"INSUFFICIENT ANALYSIS: You have made {n_ok} call{'' if n_ok == 1 else 's'} to "
                             f"llm_summarize/llm_query/llm_extract{empty_note}. "
                             f"You need at least {MIN_LLM_CALLS} calls to llm_summarize/llm_query/llm_extract "
                             f"before completing. Please continue analyzing the document more thoroughly. "
                             f"Use llm_summarize() on different sections or pages to gather more information.")
                st["nudges"].append({"turn": turn + 1, "kind": "rejection"})
            else:
                after_max = insufficient_work   # max rejections reached: accept whatever we have
                if after_max:
                    logger.warning(f"[Turn {turn+1}] Max rejections reached ({MAX_EARLY_REJECTIONS}). "
                                   f"Accepting with {context.sub_calls_ok} sub-calls.")

                if is_empty and len(context.citations) == 0:
                    # Truly empty - no citations: passed over, the run goes on (as before), counted
                    logger.warning(f"[Turn {turn+1}] REJECTING empty final answer - no work done yet!")
                    st["empty_finals_dropped"] += 1

                elif is_empty:
                    # Work was done but report is empty - use deterministic fallback
                    logger.info(f"[Turn {turn+1}] Report empty but have {len(context.citations)} citations - "
                                f"using fallback")
                    auto_report = context.auto_generate_report_from_citations()
                    auto_report, verify = await self._maybe_verify(auto_report, context)
                    logger.info(f"RLM COMPLETE - Auto-generated report from {len(context.citations)} citations")
                    yield RLMEvent(type="_done", content="", metadata={"event": RLMEvent(
                        type="final", content=auto_report,
                        metadata=meta("auto_generated", accepted_after_max_rejections=after_max,
                                      verify=verify))})
                    return
                else:
                    # Valid report - optionally verify, then return
                    final_answer, verify = await self._maybe_verify(final_answer, context)
                    logger.info(f"=" * 60)
                    logger.info(f"RLM COMPLETE - Turn {turn + 1}")
                    logger.info(f"Final report length: {len(final_answer)} chars")
                    logger.info(f"Citations: {len(context.citations)}")
                    logger.info(f"LLM calls: {context.llm_calls_made}")
                    logger.info(f"=" * 60)
                    yield RLMEvent(type="_done", content="", metadata={"event": RLMEvent(
                        type="final", content=final_answer,
                        metadata=meta("final_after_max_rejections" if after_max else "final",
                                      accepted_after_max_rejections=after_max, verify=verify))})
                    return

        # Add to conversation, once (F11)
        messages.append({"role": "assistant", "content": assistant_response})

        # Build progress feedback with target document reminder. The LLM-call count shown is Mentori's, every model
        # call (root turns and sub-calls), as get_progress() gives it; Q3 changed only the gate and its message
        progress_content = "Output:\n" + "\n\n".join(all_outputs)
        progress_content += f"\n\n[Progress: {context.llm_calls_made} LLM calls, "
        progress_content += f"{len(context.citations)} citations, "
        progress_content += f"{len(context.report_sections)} report sections]"
        if target_doc_hint:
            progress_content += f"\n\n⚠️ REMEMBER: Your target document is '{target_doc_hint}'. Only analyze this document."
        if rejection:
            progress_content += f"\n\n{rejection}"

        messages.append({
            "role": "user",
            "content": progress_content
        })

        logger.info(f"[Turn {turn+1} Summary] LLM calls: {context.llm_calls_made}, "
                    f"Citations: {len(context.citations)}, "
                    f"Report sections: {len(context.report_sections)}")

        if self.verbose:
            section_chars = sum(len(str(s.content)) for s in context.report_sections)   # D92 Q184, as above
            print(f"[VERBOSE Turn {turn+1}] State: llm_calls={context.llm_calls_made}, "
                  f"citations={len(context.citations)}, "
                  f"sections={len(context.report_sections)}, "
                  f"section_chars={section_chars}")

        yield RLMEvent(type="_done", content="", metadata=None)

    def _end_of_turn_checks(self, turn: int, context: RLMContext, target_doc_hint: Optional[str], task: str,
                            nudge) -> None:
        """The messages added after a turn, after every turn (Q7, D68). History compaction is deleted (F5, D25:
        earlier turns were cut to 150-character previews) and so is the token-budget warning (Q6, D68: the context
        limit bounds the run and fails visibly). The escalation and last-turn messages are stated count rules.
        Their code examples teach no text slicing (Q13, D68: chunks[0].text, not chunks[0].text[:100]) and no list
        slicing (Q67, D75: llm_summarize(chunks, ...), not chunks[:5] or chunks[:10]). With no pinned document they
        search with the question's text across all papers (Q2, D68: they used the first document of the index), and
        the turn-6 example summarises for the question under 'Findings' (Q68, D75); a pinned run keeps Mentori's
        'Summarize the methods' under 'Methods'."""
        # Progressive escalation to force report generation
        if len(context.report_sections) == 0:
            if turn == 5:
                # Gentle reminder with working code example
                logger.warning(f"[Turn {turn+1}] No report sections yet - adding code example")
                if target_doc_hint:
                    find = f'chunks = search_keyword("methods", doc_name="{target_doc_hint}")\n'
                    doc = f'"{target_doc_hint}"'
                    summ, section = '"Summarize the methods"', '"Methods"'
                else:
                    find = f"chunks = search_semantic({task!r})\n"
                    doc = "chunks[0].doc_name"
                    summ, section = repr(task), '"Findings"'   # Q68 (D75): the task is the question
                if not self.search_tools:
                    find = self._nosearch_find("turn6_example", target_doc_hint)   # D239
                nudge(turn + 1, "turn6_example",
                      f"You have been searching but haven't saved any findings yet. "
                      f"You MUST use add_to_report() to save your analysis. "
                      f"Here is working code you can adapt:\n\n"
                      f"```repl\n"
                      f"{find}"
                      f"result = llm_summarize(chunks, task={summ})\n"
                      f"c = cite({doc}, chunks[0].page, chunks[0].text)\n"
                      f"add_to_report({section}, result[\"summary\"], result[\"citations\"] + [c])\n"
                      f"print(\"Saved to report\")\n"
                      f"```")
            elif turn == 8:
                # Strong intervention — inject code directly
                logger.warning(f"[Turn {turn+1}] Still no report after 8 turns - injecting synthesis prompt")
                nudge(turn + 1, "turn9_critical",
                      "CRITICAL: You have spent 8 turns without saving any report content. "
                      "You MUST NOW call llm_summarize() on any chunks you have found, "
                      "then call add_to_report() immediately. "
                      "Do NOT search any more. Synthesize what you already have.")
            elif turn >= 10:
                logger.warning(f"[Turn {turn+1}] No report sections after {turn+1} turns - adding reminder")
                nudge(turn + 1, "urgent",
                      "URGENT: Save your findings NOW with add_to_report() or you will run out of turns!")

        # Final turns warning - force completion
        if turn >= self.max_turns - 2:
            logger.warning(f"[Turn {turn+1}] Approaching max turns - forcing completion")
            if len(context.report_sections) > 0:
                nudge(turn + 1, "final_warning",
                      f"FINAL: Only {self.max_turns - turn - 1} turns remaining. "
                      "Call FINAL_VAR(get_report()) NOW to submit your report.")
            else:
                # Emergency: synthesize whatever we have
                if target_doc_hint:
                    find = f'chunks = search_keyword("", doc_name="{target_doc_hint}")\n'
                else:
                    find = f"chunks = search_semantic({task!r})\n"
                if not self.search_tools:
                    find = self._nosearch_find("emergency", target_doc_hint)   # D239
                nudge(turn + 1, "emergency",
                      f"EMERGENCY: Last turn. Write this EXACT code:\n\n"
                      f"```repl\n"
                      f"{find}"
                      f"if chunks:\n"
                      f"    result = llm_summarize(chunks, task=\"Provide a comprehensive summary\")\n"
                      f"    add_to_report(\"Summary\", result[\"summary\"], result[\"citations\"])\n"
                      f"FINAL_VAR(get_report())\n"
                      f"```")

    @staticmethod
    def _nosearch_find(kind: str, target_doc_hint: Optional[str]) -> str:
        """D239: the first line of a nudge's code when the search functions are removed; it reads with navigation
        functions what the search line found. With a pinned document: turn6_example's search_keyword("methods") becomes
        the document's first ten chunks (get_chunks_range 0 to 10); emergency's search_keyword("") (every chunk of the
        document) becomes every chunk of the document, page by page. With no pinned document, both nudges'
        search_semantic(<the question>) becomes the first page of every document. The rest of each nudge is unchanged."""
        if kind not in ("turn6_example", "emergency"):
            raise ValueError(f"no search-off line for nudge {kind!r}")
        if target_doc_hint:
            if kind == "turn6_example":
                return f'chunks = get_chunks_range("{target_doc_hint}", 0, 10)\n'
            return (f'chunks = [c for p in get_document_structure("{target_doc_hint}")["pages"] '
                    f'for c in get_chunks_by_page("{target_doc_hint}", p["page"])]\n')
        return 'chunks = [c for d in list_documents() for c in get_chunks_by_page(d["name"], 1)]\n'

    def _format_messages(self, messages: List[Dict]) -> str:
        """Format messages for LLM prompt."""
        formatted = []
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            if role == "SYSTEM":
                formatted.append(f"{content}")
            elif role == "USER":
                formatted.append(f"\n---\nUSER: {content}")
            else:
                formatted.append(f"\n---\nASSISTANT: {content}")

        return "\n".join(formatted)

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract ```repl code blocks from text."""
        # F19 (A10): ```repl, ```python or ```py, in any case, with spaces or a carriage return before the newline
        # (it matched only ```repl or ```python followed directly by \n)
        pattern = r'```(?:repl|python|py)[ \t]*\r?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        results = []
        for m in matches:
            code = m.strip()
            if not code:
                continue
            # Fix tabs → 4 spaces (common LLM issue)
            code = code.replace('\t', '    ')
            results.append(code)
        return results

    def _extract_target_document(self, task: str, context: Optional[RLMContext] = None) -> Optional[str]:
        """
        Extract a target document name from the task if one is specified.

        Looks for patterns like:
        - 'paper X.pdf'
        - 'document "filename.pdf"'
        - 'analyze filename.pdf'

        Q1 (D68): a document is pinned only when the task names a .pdf file. The fallback that matched any
        capitalised word of the task inside document names and titles is deleted ("In" matched 02_snakemake.pdf,
        so 25 of 138 deposit questions outside the out-of-domain set were pinned to the wrong paper; rlm F4).
        """
        # Look for quoted document names
        quoted_match = re.search(r"['\"]([^'\"]+\.pdf)['\"]", task, re.IGNORECASE)
        if quoted_match:
            return quoted_match.group(1)

        # Look for .pdf filenames
        pdf_match = re.search(r'(\S+\.pdf)', task, re.IGNORECASE)
        if pdf_match:
            return pdf_match.group(1)

        return None

    async def _maybe_verify(self, report_text: str, context: RLMContext):
        """Optionally run verification pass and append summary to report. Returns (text, verify record or None).
        A5 (cuts.md F13): a failed verification pass is recorded in the verify record (error) and the report is
        returned without a summary; "*Verification failed: ...*" is no longer appended to the answer. A LockError
        or RunContextError is not caught (Q38)."""
        if not self.verify:
            return report_text, None

        from .verification import ReportVerifier
        from .executor import SETUP_ERRORS

        try:
            logger.info("Running verification pass on final report...")
            verifier = ReportVerifier(self.router, self.model_identifier)
            vr = await verifier.verify_report(report_text, context)
            summary = verifier.format_summary(vr)
            return report_text + summary, verifier.record(vr)
        except SETUP_ERRORS:
            raise
        except Exception as e:
            logger.error(f"Verification pass failed: {e}")
            return report_text, {"error": f"{type(e).__name__}: {e}"}


class MaxTurnsExceeded(Exception):
    """Raised when max turns is reached without completion."""
    pass
