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

from .context import RLMContext
from .executor import RLMExecutor

# Use Mentori's session logger for consistent output in Docker
from backend.agents.session_context import get_logger
from backend.agents.prompts import get_rlm_orchestrator_prompt

logger = get_logger(__name__)


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
        num_ctx: int = 24576,
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
            think: Thinking mode for LLM calls. False=disabled, True=enabled,
                   str (e.g. "high")=budget hint. Default False.
            verbose: If True, print per-turn diagnostics to stdout.
            num_ctx: Context window size for Ollama models. Default 24576.
        """
        self.router = model_router
        self.model_identifier = model_identifier
        self.max_turns = max_turns
        self.verify = verify
        self.think = think
        self.verbose = verbose
        self.num_ctx = num_ctx

    async def run(self, task: str, context: RLMContext) -> str:
        """
        Execute the RLM loop until completion.

        Args:
            task: The research task to perform
            context: Initialized RLMContext with documents

        Returns:
            Final result string (report or answer)
        """
        async for event in self.run_stream(task, context):
            if event.type == "final":
                return event.content
            elif event.type == "error":
                raise RuntimeError(event.content)

        raise RuntimeError("RLM loop ended without producing a result")

    async def run_stream(self, task: str, context: RLMContext) -> AsyncGenerator[RLMEvent, None]:
        """
        Execute the RLM loop with streaming events.

        Yields RLMEvent objects for progress tracking.
        """
        # Build system prompt with context (from centralized prompts.py)
        # NOTE: We use .replace() instead of .format() because the prompt
        # contains code examples with {target_doc}, {structure[...]}, etc.
        # that .format() would try to resolve, causing KeyError.
        system_prompt = get_rlm_orchestrator_prompt()
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

        # Quality gate: require minimum work before accepting completion
        MIN_LLM_CALLS = 3  # Minimum llm_summarize/llm_query/llm_extract calls
        MAX_EARLY_REJECTIONS = 3  # After this many rejections, accept anyway
        early_completion_rejections = 0

        for turn in range(self.max_turns):
            print(f"\n{'='*40} RLM Turn {turn + 1}/{self.max_turns} {'='*40}")
            logger.info(f"\n{'='*40} RLM Turn {turn + 1}/{self.max_turns} {'='*40}")

            yield RLMEvent(
                type="progress",
                content=f"Turn {turn + 1}",
                metadata={"turn": turn + 1, "progress": context.get_progress()}
            )

            # Get LLM response using chat endpoint
            # NOTE: We explicitly disable thinking mode (think=False) for RLM because:
            # 1. RLM already has its own "thinking" via the REPL execution loop
            # 2. Some thinking models produce output that Ollama tries to parse as tool calls
            # 3. The iterative code execution IS the reasoning process
            print(f"[Turn {turn+1}] Calling LLM with model: {self.model_identifier}")
            try:
                response = await self.router.chat(
                    model_identifier=self.model_identifier,
                    messages=messages,
                    options={
                        "temperature": 0.2,
                        "num_predict": 8192,
                        "num_ctx": self.num_ctx,
                    },
                    think=self.think  # Configurable; default False (REPL loop is the reasoning mechanism)
                )
                # Chat endpoint returns {"message": {"role": "assistant", "content": "..."}} (Ollama)
                # or {"response": "..."} (Gemini)
                assistant_response = response.get("message", {}).get("content", "") or response.get("response", "")
                # Track tokens from main REPL turns
                turn_tokens = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
                context.total_tokens_used += turn_tokens
                context.llm_calls_made += 1
                # Log errors and empty response diagnostics from Gemini
                if response.get("error"):
                    logger.error(f"[Turn {turn+1}] API ERROR: {response['error']}")
                    print(f"[Turn {turn+1}] API ERROR: {response['error']}")
                empty_reason = response.get("empty_reason")
                if empty_reason:
                    logger.warning(f"[Turn {turn+1}] EMPTY RESPONSE from Gemini: {empty_reason}")
                    print(f"[Turn {turn+1}] EMPTY RESPONSE: {empty_reason}")
                print(f"[Turn {turn+1}] Got response: {len(assistant_response)} chars, {turn_tokens} tokens")

            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                yield RLMEvent(type="error", content=f"LLM error: {str(e)}")
                return

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

            if not code_blocks:
                # No code blocks - prompt LLM to write code
                print(f"[Turn {turn+1}] NO CODE BLOCKS - prompting model to write code")
                logger.warning(f"[Turn {turn+1}] NO CODE BLOCKS found in response!")
                logger.info(f"  Full response: {assistant_response[:500]}")
                messages.append({"role": "assistant", "content": assistant_response})
                messages.append({
                    "role": "user",
                    "content": "Please write Python code in ```repl blocks to proceed with the analysis. "
                               "Start by using list_documents() to see available documents."
                })
                continue

            logger.info(f"[Turn {turn+1}] Found {len(code_blocks)} code block(s)")

            # Limit to first 2 code blocks to prevent runaway generation
            if len(code_blocks) > 2:
                logger.warning(f"[Turn {turn+1}] Trimming {len(code_blocks)} code blocks to 2")
                code_blocks = code_blocks[:2]

            # Execute each code block
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

                output_text = output
                if result is not None:
                    output_text += f"\n→ Result: {result}"

                logger.info(f"[Output {i+1}] {output_text[:300]}{'...' if len(output_text) > 300 else ''}")

                all_outputs.append(f"[Block {i+1}]\n{output_text}")

                yield RLMEvent(type="output", content=output_text)

            # Check for FINAL_VAR AFTER code execution (so report is populated)
            # This handles the case where model puts FINAL_VAR(get_report()) in same block as llm_summarize()
            for code in code_blocks:
                if "FINAL_VAR" in code:
                    logger.info(f"[Turn {turn+1}] FINAL_VAR detected in code block - checking result after execution")
                    final_answer = self._check_final_answer(code, executor)

                    if final_answer:
                        # Check if the report has actual content (not the empty message)
                        is_empty = (
                            not final_answer.strip() or
                            "No report content yet" in final_answer or
                            len(final_answer.strip()) < 50
                        )

                        # QUALITY GATE: Require minimum LLM calls AND real content
                        has_substance = any(
                            len(s.content.strip()) > 50
                            for s in context.report_sections
                        )
                        insufficient_work = (
                            context.llm_calls_made < MIN_LLM_CALLS or not has_substance
                        )

                        if insufficient_work and early_completion_rejections < MAX_EARLY_REJECTIONS:
                            # Not enough work done - reject and ask for more analysis
                            early_completion_rejections += 1
                            logger.warning(f"[Turn {turn+1}] REJECTING early completion - only {context.llm_calls_made} LLM calls "
                                         f"(need {MIN_LLM_CALLS}). Rejection {early_completion_rejections}/{MAX_EARLY_REJECTIONS}")

                            # Add rejection message to prompt more thorough analysis
                            messages.append({"role": "assistant", "content": assistant_response})
                            messages.append({
                                "role": "user",
                                "content": f"INSUFFICIENT ANALYSIS: You've only made {context.llm_calls_made} LLM calls. "
                                          f"You need at least {MIN_LLM_CALLS} calls to llm_summarize/llm_query/llm_extract "
                                          f"before completing. Please continue analyzing the document more thoroughly. "
                                          f"Use llm_summarize() on different sections or pages to gather more information."
                            })
                            break  # Continue to next turn

                        elif insufficient_work and early_completion_rejections >= MAX_EARLY_REJECTIONS:
                            # Hit max rejections - accept whatever we have
                            logger.warning(f"[Turn {turn+1}] Max rejections reached ({MAX_EARLY_REJECTIONS}). "
                                         f"Accepting with {context.llm_calls_made} LLM calls.")
                            # Fall through to acceptance logic below

                        if is_empty and len(context.citations) == 0:
                            # Truly empty - no citations, reject and continue
                            logger.warning(f"[Turn {turn+1}] REJECTING empty final answer - no work done yet!")
                            break  # Continue to next turn

                        elif is_empty and len(context.citations) > 0:
                            # Work was done but report is empty - use deterministic fallback
                            logger.info(f"[Turn {turn+1}] Report empty but have {len(context.citations)} citations - using fallback")
                            auto_report = context.auto_generate_report_from_citations()
                            if auto_report:
                                auto_report = await self._maybe_verify(auto_report, context)
                                logger.info(f"RLM COMPLETE - Auto-generated report from {len(context.citations)} citations")
                                yield RLMEvent(
                                    type="final",
                                    content=auto_report,
                                    metadata={
                                        "turns": turn + 1,
                                        "citations": len(context.citations),
                                        "llm_calls": context.llm_calls_made,
                                        "tokens_used": context.total_tokens_used,
                                        "auto_generated": True
                                    }
                                )
                                return
                        else:
                            # Valid report - optionally verify, then return
                            final_answer = await self._maybe_verify(final_answer, context)
                            logger.info(f"=" * 60)
                            logger.info(f"RLM COMPLETE - Turn {turn + 1}")
                            logger.info(f"Final report length: {len(final_answer)} chars")
                            logger.info(f"Citations: {len(context.citations)}")
                            logger.info(f"LLM calls: {context.llm_calls_made}")
                            logger.info(f"=" * 60)

                            yield RLMEvent(
                                type="final",
                                content=final_answer,
                                metadata={
                                    "turns": turn + 1,
                                    "citations": len(context.citations),
                                    "llm_calls": context.llm_calls_made,
                                    "tokens_used": context.total_tokens_used
                                }
                            )
                            return
                    break  # Only check first FINAL_VAR occurrence

            # Add to conversation
            messages.append({"role": "assistant", "content": assistant_response})

            # Build progress feedback with target document reminder
            progress_content = "Output:\n" + "\n\n".join(all_outputs)
            progress_content += f"\n\n[Progress: {context.llm_calls_made} LLM calls, "
            progress_content += f"{len(context.citations)} citations, "
            progress_content += f"{len(context.report_sections)} report sections]"
            if target_doc_hint:
                progress_content += f"\n\n⚠️ REMEMBER: Your target document is '{target_doc_hint}'. Only analyze this document."

            messages.append({
                "role": "user",
                "content": progress_content
            })

            logger.info(f"[Turn {turn+1} Summary] LLM calls: {context.llm_calls_made}, "
                       f"Citations: {len(context.citations)}, "
                       f"Report sections: {len(context.report_sections)}")

            if self.verbose:
                section_chars = sum(len(s.content) for s in context.report_sections)
                print(f"[VERBOSE Turn {turn+1}] State: llm_calls={context.llm_calls_made}, "
                      f"citations={len(context.citations)}, "
                      f"sections={len(context.report_sections)}, "
                      f"section_chars={section_chars}")

            # Compact history every 5 turns to prevent context window overflow
            if (turn + 1) % 5 == 0:
                messages = self._compact_history(messages, keep_last_n=3)

            # Progressive escalation to force report generation
            if len(context.report_sections) == 0:
                if turn == 5:
                    # Gentle reminder with working code example
                    logger.warning(f"[Turn {turn+1}] No report sections yet - adding code example")
                    doc_hint = f'"{target_doc_hint}"' if target_doc_hint else 'list_documents()[0]["name"]'
                    messages.append({
                        "role": "user",
                        "content": f"You have been searching but haven't saved any findings yet. "
                                   f"You MUST use add_to_report() to save your analysis. "
                                   f"Here is working code you can adapt:\n\n"
                                   f"```repl\n"
                                   f"chunks = search_keyword(\"methods\", doc_name={doc_hint})\n"
                                   f"result = llm_summarize(chunks[:5], task=\"Summarize the methods\")\n"
                                   f"c = cite({doc_hint}, chunks[0].page, chunks[0].text[:100])\n"
                                   f"add_to_report(\"Methods\", result[\"summary\"], result[\"citations\"] + [c])\n"
                                   f"print(\"Saved to report\")\n"
                                   f"```"
                    })
                elif turn == 8:
                    # Strong intervention — inject code directly
                    logger.warning(f"[Turn {turn+1}] Still no report after 8 turns - injecting synthesis prompt")
                    messages.append({
                        "role": "user",
                        "content": "CRITICAL: You have spent 8 turns without saving any report content. "
                                   "You MUST NOW call llm_summarize() on any chunks you have found, "
                                   "then call add_to_report() immediately. "
                                   "Do NOT search any more. Synthesize what you already have."
                    })
                elif turn >= 10:
                    logger.warning(f"[Turn {turn+1}] No report sections after {turn+1} turns - adding reminder")
                    messages.append({
                        "role": "user",
                        "content": "URGENT: Save your findings NOW with add_to_report() or you will run out of turns!"
                    })

            # Final turns warning - force completion
            if turn >= self.max_turns - 2:
                logger.warning(f"[Turn {turn+1}] Approaching max turns - forcing completion")
                if len(context.report_sections) > 0:
                    messages.append({
                        "role": "user",
                        "content": f"FINAL: Only {self.max_turns - turn - 1} turns remaining. "
                                   "Call FINAL_VAR(get_report()) NOW to submit your report."
                    })
                else:
                    # Emergency: synthesize whatever we have
                    doc_hint = f'"{target_doc_hint}"' if target_doc_hint else 'list_documents()[0]["name"]'
                    messages.append({
                        "role": "user",
                        "content": f"EMERGENCY: Last turn. Write this EXACT code:\n\n"
                                   f"```repl\n"
                                   f"chunks = search_keyword(\"\", doc_name={doc_hint})\n"
                                   f"if chunks:\n"
                                   f"    result = llm_summarize(chunks[:10], task=\"Provide a comprehensive summary\")\n"
                                   f"    add_to_report(\"Summary\", result[\"summary\"], result[\"citations\"])\n"
                                   f"FINAL_VAR(get_report())\n"
                                   f"```"
                    })

            # Token budget check
            if context.total_tokens_used > context.max_tokens * 0.9:
                logger.warning("Approaching token budget limit")
                messages.append({
                    "role": "user",
                    "content": "WARNING: Approaching token budget. Please finalize your analysis and call FINAL_VAR(get_report()) soon."
                })

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
            # We have actual report content - return it as partial success
            logger.info("Returning partial report as final result")
            yield RLMEvent(
                type="final",
                content=report + "\n\n---\n*Note: Analysis reached turn limit. Results may be incomplete.*",
                metadata={
                    "turns": self.max_turns,
                    "citations": len(context.citations),
                    "llm_calls": context.llm_calls_made,
                    "tokens_used": context.total_tokens_used,
                    "partial": True
                }
            )
        elif len(context.citations) > 0:
            # DETERMINISTIC FALLBACK: We have citations but LLM forgot to call add_to_report()
            # Auto-generate a report from the collected citations
            logger.warning(f"LLM collected {len(context.citations)} citations but never saved to report!")
            logger.info("Using deterministic fallback: auto-generating report from citations")

            auto_report = context.auto_generate_report_from_citations()
            if auto_report:
                yield RLMEvent(
                    type="final",
                    content=auto_report,
                    metadata={
                        "turns": self.max_turns,
                        "citations": len(context.citations),
                        "llm_calls": context.llm_calls_made,
                        "tokens_used": context.total_tokens_used,
                        "partial": True,
                        "auto_generated": True
                    }
                )
            else:
                yield RLMEvent(
                    type="error",
                    content=f"Maximum turns ({self.max_turns}) reached. Citations collected but report generation failed."
                )
        else:
            # Truly empty - no citations, no report
            yield RLMEvent(
                type="error",
                content=f"Maximum turns ({self.max_turns}) reached without completion. "
                        f"No meaningful analysis was produced (0 citations, 0 report sections)."
            )

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
        # Match ```repl or ```python blocks
        pattern = r'```(?:repl|python)\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        results = []
        for m in matches:
            code = m.strip()
            if not code:
                continue
            # Fix tabs → 4 spaces (common LLM issue)
            code = code.replace('\t', '    ')
            results.append(code)
        return results

    def _check_final_answer(self, text: str, executor: RLMExecutor) -> Optional[str]:
        """
        Check if response contains a final answer.

        Returns the final answer string or None.
        """
        # Check for FINAL_VAR(expression) - handles nested parentheses like get_report()
        # Use balanced parenthesis matching
        final_var_start = text.find('FINAL_VAR(')
        if final_var_start != -1:
            # Find the matching closing paren
            start_idx = final_var_start + len('FINAL_VAR(')
            paren_count = 1
            end_idx = start_idx
            while end_idx < len(text) and paren_count > 0:
                if text[end_idx] == '(':
                    paren_count += 1
                elif text[end_idx] == ')':
                    paren_count -= 1
                end_idx += 1

            if paren_count == 0:
                var_expr = text[start_idx:end_idx - 1].strip()
            else:
                var_expr = None
        else:
            var_expr = None

        if var_expr:
            try:
                # Evaluate the expression in the executor's namespace
                if var_expr == "get_report()":
                    return executor.context.get_report()
                else:
                    result = eval(var_expr, executor.namespace)
                    return str(result)
            except Exception as e:
                logger.error(f"Failed to evaluate FINAL_VAR({var_expr}): {e}")
                return None

        # Check for FINAL(answer) - simple string
        final_match = re.search(r'FINAL\("([^"]+)"\)', text)
        if final_match:
            return final_match.group(1).strip()

        # Check for FINAL('answer') - single quotes
        final_match = re.search(r"FINAL\('([^']+)'\)", text)
        if final_match:
            return final_match.group(1).strip()

        # Check for FINAL("multi-line answer")
        final_match = re.search(r'FINAL\((""".*?"""|\'\'\'.*?\'\'\')\)', text, re.DOTALL)
        if final_match:
            return final_match.group(1).strip('"\' ')

        return None

    def _extract_target_document(self, task: str, context: Optional[RLMContext] = None) -> Optional[str]:
        """
        Extract a target document name from the task if one is specified.

        Looks for patterns like:
        - 'paper X.pdf'
        - 'document "filename.pdf"'
        - 'analyze filename.pdf'
        - topic keywords matching document names/titles (fallback)
        """
        # Look for quoted document names
        quoted_match = re.search(r"['\"]([^'\"]+\.pdf)['\"]", task, re.IGNORECASE)
        if quoted_match:
            return quoted_match.group(1)

        # Look for .pdf filenames
        pdf_match = re.search(r'(\S+\.pdf)', task, re.IGNORECASE)
        if pdf_match:
            return pdf_match.group(1)

        # Fallback: search document names/titles for keywords from the task
        # This helps when users say "the paper about HTS-Flow" instead of "fgene-07-00075.pdf"
        if context and hasattr(context, '_documents') and len(context._documents) > 1:
            task_lower = task.lower()
            # Extract potential topic keywords (capitalized words, hyphenated terms)
            keywords = re.findall(r'\b[A-Z][A-Za-z\-]+(?:\-[A-Za-z]+)*\b', task)
            # Also try hyphenated terms from the task
            keywords += re.findall(r'\b\w+\-\w+\b', task)
            # Remove common non-topic words
            skip = {"summarize", "analyze", "compare", "methods", "results", "paper",
                    "document", "section", "chapters", "index", "papers"}
            keywords = [kw for kw in keywords if kw.lower() not in skip]

            if keywords:
                docs = context.list_documents()
                for kw in keywords:
                    kw_lower = kw.lower()
                    for doc in docs:
                        doc_name = doc.get("name", "").lower()
                        # Check document name and title from DocumentInfo
                        title = ""
                        name_key = doc.get("name", "")
                        if name_key in context._documents:
                            doc_info = context._documents[name_key]
                            title = (doc_info.title or "").lower()
                        if kw_lower in doc_name or kw_lower in title:
                            logger.info(f"Target document matched by keyword '{kw}': {name_key}")
                            return name_key

        return None


    async def _maybe_verify(self, report_text: str, context: RLMContext) -> str:
        """Optionally run verification pass and append summary to report."""
        if not self.verify:
            return report_text

        try:
            from .verification import ReportVerifier

            logger.info("Running verification pass on final report...")
            verifier = ReportVerifier(self.router, self.model_identifier)
            vr = await verifier.verify_report(report_text, context)
            summary = verifier.format_summary(vr)
            return report_text + summary
        except Exception as e:
            logger.error(f"Verification pass failed: {e}")
            return report_text + f"\n\n---\n*Verification failed: {e}*"

    def _compact_history(self, messages: List[Dict], keep_last_n: int = 3) -> List[Dict]:
        """
        Compact conversation history to prevent context window overflow.

        Preserves:
        - System prompt (index 0)
        - Initial task (index 1)
        - Last `keep_last_n` turn-pairs (assistant + user)

        Middle messages are summarised into a single "[HISTORY SUMMARY]" message.
        """
        # Each turn-pair is (assistant, user) → 2 messages per turn
        # Fixed messages: system (0) + initial task (1) = 2
        fixed = 2
        tail_count = keep_last_n * 2  # assistant + user per turn

        # Only compact if there are enough messages to warrant it
        if len(messages) <= fixed + tail_count + 4:
            return messages  # Not enough to compact

        head = messages[:fixed]
        middle = messages[fixed:-tail_count]
        tail = messages[-tail_count:]

        # Build concise summary of middle messages
        summary_parts = []
        for msg in middle:
            role = msg["role"]
            content = msg["content"]
            # Take first 150 chars of each message for the summary
            preview = content[:150].replace("\n", " ")
            if len(content) > 150:
                preview += "..."
            summary_parts.append(f"[{role}] {preview}")

        summary_text = (
            f"[HISTORY SUMMARY — {len(middle)} messages compacted]\n"
            + "\n".join(summary_parts)
        )

        compacted = head + [{"role": "user", "content": summary_text}] + tail

        logger.info(
            f"Compacted history: {len(messages)} → {len(compacted)} messages "
            f"({len(middle)} middle messages summarised)"
        )

        return compacted


class MaxTurnsExceeded(Exception):
    """Raised when max turns is reached without completion."""
    pass
