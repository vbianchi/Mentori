# backend/agents/notebook/coder_loop.py
"""
Main coder agent loop with notebook integration.

This is a specialized ReAct loop where the agent operates on
a Jupyter notebook, adding and executing cells iteratively.
"""

import json
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Union, Optional

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import (
    SessionContext,
    set_session_context,
    get_logger
)
from backend.agents.notebook.schema import NotebookState, Algorithm, KernelState
from backend.agents.notebook.kernel import KernelRegistry
from backend.agents.notebook.manager import NotebookManager
from backend.agents.notebook.tools import CoderTools, CODER_TOOLS_SCHEMA, ToolResult
from backend.agents.notebook.prompts import build_coder_system_prompt, build_memory_context
from backend.agents.notebook.algorithm import (
    generate_algorithm,
    should_generate_algorithm
)
from backend.agents.notebook.supervisor import CoderSupervisor
from backend.agents.notebook.task_supervisor import TaskSupervisor
from backend.agents.orchestrator.memory import TaskMemoryVault
from pathlib import Path

logger = get_logger(__name__)


async def coder_loop(
    model_router: ModelRouter,
    model_identifier: str,
    messages: List[Dict[str, str]],
    session_context: SessionContext,
    max_steps: int = 100,
    think: Union[bool, str] = False,
    display_model: str = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Coder agent loop with notebook integration.

    This loop:
    1. Loads or creates a notebook for the task
    2. Provides the agent with notebook manipulation tools
    3. Streams execution events (cell added, executing, output, etc.)
    4. Persists notebook state after each operation

    Args:
        model_router: Router for LLM calls
        model_identifier: Model to use (e.g., "ollama::qwen3:8b")
        messages: Conversation history (user/assistant messages)
        session_context: Session context with workspace path, task ID, etc.
        max_steps: Maximum ReAct iterations
        think: Whether to enable thinking mode
        display_model: Model name for display (optional)

    Yields:
        Event dictionaries for SSE streaming
    """
    # 0. Set session context
    set_session_context(session_context)

    workspace_path = session_context.workspace_path
    task_id = session_context.task_id

    logger.info(f"Starting coder loop for task {task_id}")

    # 1. Initialize notebook manager and load/create notebook
    notebook_manager = NotebookManager(workspace_path, task_id)

    try:
        notebook = notebook_manager.get_or_create_default()
    except Exception as e:
        logger.error(f"Failed to initialize notebook: {e}")
        yield {"type": "error", "message": f"Failed to initialize notebook: {e}"}
        return

    # 1b. Load memory vault for session context
    user_id = session_context.user_id or "default"
    memory_vault = TaskMemoryVault(
        task_id=task_id,
        user_id=user_id,
        workspace_path=Path(workspace_path)
    ).load()

    memory_context = memory_vault.get_context_for_injection()
    if memory_context and memory_context != "(No previous sessions in this task)":
        logger.info(f"Loaded memory vault: {len(memory_vault.sessions)} sessions")
    else:
        memory_context = ""

    # 2. Initialize tools
    tools = CoderTools(notebook_manager, notebook)

    # 2b. Initialize supervisor for quality evaluation
    # Get vision model from agent roles for plot validation (optional)
    agent_roles = session_context.agent_roles or {}
    vision_model = agent_roles.get("vision")  # User-configured vision model

    supervisor = CoderSupervisor(
        model_router=model_router,
        model_identifier=model_identifier,
        max_retries=3,
        vision_model_identifier=vision_model  # Use user's vision agent for plot validation
    )

    # Task supervisor will be initialized after algorithm generation
    task_supervisor = None

    # 3. Yield session info
    yield {
        "type": "session_info",
        "session_info": {
            "mode": "coder",
            "model": display_model or model_identifier,
            "notebook_name": notebook.name,
            "notebook_path": notebook.path,
            "total_cells": len(notebook.cells)
        }
    }

    # Send existing cells for notebook viewer
    cells_data = []
    for cell in notebook.cells:
        cell_data = {
            "id": cell.id,
            "cell_type": cell.cell_type,
            "source": cell.source,
            "status": cell.status,
            "execution_count": cell.execution_count,
            "outputs": [o.to_dict() for o in cell.outputs]
        }
        cells_data.append(cell_data)

    yield {
        "type": "notebook_loaded",
        "notebook_name": notebook.name,
        "notebook_path": notebook.path,
        "cell_count": len(notebook.cells),
        "cells": cells_data
    }

    # 4. Build initial notebook state
    notebook_state = notebook_manager.get_notebook_state(notebook)

    # 5. Algorithm generation phase (for complex requests)
    algorithm = None
    user_request = ""

    # Extract user request from messages
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_request = msg.get("content", "")
            break

    if user_request and should_generate_algorithm(user_request):
        logger.info("Generating algorithm for complex request...")

        yield {
            "type": "algorithm_start",
            "message": "Planning approach..."
        }

        try:
            # Get kernel state for algorithm planning
            kernel = await KernelRegistry.get_kernel(
                notebook_manager.get_full_notebook_path(notebook.name),
                notebook_manager.get_workspace_path()
            )
            kernel_state = await kernel.get_kernel_variables()

            algorithm = await generate_algorithm(
                model_router=model_router,
                model_identifier=model_identifier,
                user_request=user_request,
                notebook_state=notebook_state,
                kernel_state=kernel_state
            )

            if algorithm:
                yield {
                    "type": "algorithm_complete",
                    "algorithm": algorithm.to_dict()
                }
                logger.info(f"Algorithm generated: {len(algorithm.steps)} steps")
            else:
                yield {
                    "type": "algorithm_skipped",
                    "reason": "Could not parse algorithm"
                }

        except Exception as e:
            logger.warning(f"Algorithm generation failed: {e}")
            yield {
                "type": "algorithm_skipped",
                "reason": str(e)
            }

    # 5b. Initialize task supervisor (with algorithm if available)
    task_supervisor = TaskSupervisor(
        model_router=model_router,
        model_identifier=model_identifier,
        algorithm=algorithm
    )

    # 6. Build system prompt with notebook state, kernel state, and optional algorithm
    # Get kernel state if not already fetched during algorithm generation
    kernel_state = None
    try:
        kernel = await KernelRegistry.get_kernel(
            notebook_manager.get_full_notebook_path(notebook.name),
            notebook_manager.get_workspace_path()
        )
        kernel_state = await kernel.get_kernel_variables()
    except Exception as e:
        logger.warning(f"Could not get kernel state: {e}")

    system_prompt = build_coder_system_prompt(
        notebook_state,
        kernel_state=kernel_state,
        algorithm=algorithm
    )

    # Inject memory context if available
    if memory_context:
        memory_section = build_memory_context(memory_context)
        system_prompt = system_prompt + "\n" + memory_section

    # Build conversation with system prompt
    current_messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add conversation history
    for msg in messages:
        current_messages.append(msg)

    step_count = 0
    cumulative_tokens = 0

    # 7. Main ReAct loop
    while step_count < max_steps:
        step_count += 1

        logger.debug(f"Coder loop step {step_count}")

        full_content = ""
        full_thinking = ""
        tool_calls = []

        # 6. Call LLM
        try:
            async for chunk in model_router.chat_stream(
                model_identifier=model_identifier,
                messages=current_messages,
                tools=CODER_TOOLS_SCHEMA,
                think=think
            ):
                try:
                    data = json.loads(chunk)

                    if "message" in data:
                        delta = data["message"]

                        # Content streaming
                        if "content" in delta and delta["content"]:
                            c = delta["content"]
                            full_content += c
                            yield {"type": "chunk", "content": c}

                        # Thinking streaming
                        if "thinking" in delta and delta["thinking"]:
                            full_thinking += delta["thinking"]
                            yield {"type": "thinking_chunk", "content": delta["thinking"]}

                        # Tool calls
                        if "tool_calls" in delta:
                            for tc in delta["tool_calls"]:
                                tool_calls.append(tc)

                    # Token usage
                    usage_data = None
                    if "usage" in data:
                        usage_data = data["usage"]
                    elif data.get("done") is True and "eval_count" in data:
                        usage_data = {
                            "input_tokens": data.get("prompt_eval_count", 0),
                            "output_tokens": data.get("eval_count", 0),
                            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                        }

                    if usage_data:
                        t_in = usage_data.get("input_tokens", usage_data.get("prompt_tokens", 0))
                        t_out = usage_data.get("output_tokens", usage_data.get("completion_tokens", 0))
                        t_total = usage_data.get("total_tokens", t_in + t_out)
                        cumulative_tokens += t_total

                        yield {
                            "type": "token_usage",
                            "token_usage": {
                                "input": t_in,
                                "output": t_out,
                                "total": t_total
                            }
                        }

                except json.JSONDecodeError:
                    pass

        except asyncio.CancelledError:
            logger.warning("Coder loop cancelled")
            # Save notebook before exit
            notebook_manager.save_notebook(tools.notebook)
            raise

        except Exception as e:
            logger.error(f"LLM error: {e}")
            yield {"type": "error", "message": f"LLM error: {e}"}
            return

        # 7. Handle tool calls
        if tool_calls:
            # Add assistant message with tool calls to context
            # Include thinking for persistence (so it can be shown on task reload)
            assistant_msg = {
                "role": "assistant",
                "content": full_content,
                "tool_calls": tool_calls,
                "thinking": full_thinking if full_thinking else None
            }
            current_messages.append(assistant_msg)

            # Execute each tool
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                tool_args_raw = tc["function"]["arguments"]

                # Parse arguments
                if isinstance(tool_args_raw, str):
                    try:
                        tool_args = json.loads(tool_args_raw)
                    except json.JSONDecodeError:
                        tool_args = {}
                else:
                    tool_args = tool_args_raw

                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                yield {
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "arguments": tool_args
                }

                # Execute the tool
                tool_result_content = ""

                try:
                    if tool_name == "execute_cell":
                        # execute_cell is a generator - stream events
                        cell_id = tool_args.get("cell_id")
                        execution_status = None
                        execution_output = ""

                        async for event in tools.execute_cell(**tool_args):
                            yield {
                                "type": "cell_event",
                                "event": event
                            }

                            # Build result content from execution complete event
                            if event.get("type") == "execution_complete":
                                execution_status = event.get("status")
                                execution_output = event.get("output_summary", "")
                                has_images = event.get("has_images", False)

                                if execution_status == "success":
                                    tool_result_content = f"**Execution successful**\n\n```text\n{execution_output}\n```"
                                    if has_images:
                                        tool_result_content += "\n\n*(Image(s) generated)*"
                                else:
                                    error = event.get("error", "Unknown error")
                                    tool_result_content = f"**Execution failed**\n\n```text\n{error}\n```"

                        # Supervisor evaluation after cell execution
                        if cell_id and execution_status:
                            cell = tools.notebook.get_cell(cell_id)
                            if cell:
                                yield {
                                    "type": "supervisor_evaluating",
                                    "cell_id": cell_id
                                }

                                evaluation = await supervisor.evaluate(cell)

                                yield {
                                    "type": "supervisor_evaluation",
                                    "cell_id": cell_id,
                                    "evaluation": evaluation.to_dict()
                                }

                                # Record evaluation in task supervisor for progress tracking
                                source_summary = cell.source[:100] + "..." if len(cell.source) > 100 else cell.source
                                task_supervisor.record_cell_evaluation(
                                    cell_id=cell_id,
                                    source_summary=source_summary,
                                    evaluation=evaluation
                                )

                                # Add evaluation feedback to tool result
                                tool_result_content += f"\n\n{evaluation.to_feedback_string()}"

                                # Automatic Cleanup: Delete cell if it failed significantly
                                # Delete if it has an error or score is very low (< 40)
                                should_auto_delete = (execution_status == "error") or (evaluation.score < 40)

                                if should_auto_delete:
                                    logger.info(f"Auto-deleting failed cell {cell_id[:8]} (status={execution_status}, score={evaluation.score})")
                                    
                                    # Perform deletion
                                    await tools.delete_cell(cell_id=cell_id)
                                    
                                    yield {
                                        "type": "cell_deleted",
                                        "cell_id": cell_id,
                                        "reason": "quality_check_failed"
                                    }
                                    
                                    tool_result_content += f"\n\n❌ **AUTOMATIC CLEANUP**: This cell was DELETED because it failed to execute or had critical issues.\n\n**Action Required**: You must REWRITE this cell from scratch with fixes. Do not try to edit it (it is gone)."
                                
                                # If not deleted but improvement needed (score 40-50, or warnings)
                                elif evaluation.should_retry:
                                    retry_count = supervisor.get_retry_count(cell_id)
                                    tool_result_content += f"\n\n⚠️ **Retry suggested** ({retry_count}/3). Please fix the issues using edit_cell and re-execute."

                    elif tool_name == "add_cell":
                        result = await tools.add_cell(**tool_args)
                        tool_result_content = result.to_llm_string()

                        if result.success:
                            yield {
                                "type": "cell_added",
                                "cell_id": result.data["cell_id"],
                                "cell_type": result.data["cell_type"],
                                "index": result.data["index"],
                                "source": tool_args.get("source", "")
                            }

                    elif tool_name == "edit_cell":
                        result = await tools.edit_cell(**tool_args)
                        tool_result_content = result.to_llm_string()

                        if result.success:
                            # Reset retry count when cell is edited
                            edited_cell_id = tool_args.get("cell_id")
                            if edited_cell_id:
                                supervisor.reset_retry_count(edited_cell_id)

                            yield {
                                "type": "cell_edited",
                                "cell_id": edited_cell_id,
                                "source": tool_args.get("source", "")
                            }

                    elif tool_name == "delete_cell":
                        result = await tools.delete_cell(**tool_args)
                        tool_result_content = result.to_llm_string()

                        if result.success:
                            yield {
                                "type": "cell_deleted",
                                "cell_id": tool_args.get("cell_id")
                            }

                    elif tool_name == "get_notebook_state":
                        result = await tools.get_notebook_state()
                        tool_result_content = result.message  # Use formatted string

                        yield {
                            "type": "notebook_state",
                            "state": result.data
                        }

                    elif tool_name == "get_kernel_state":
                        result = await tools.get_kernel_state()
                        tool_result_content = result.message  # Use formatted string

                        yield {
                            "type": "kernel_state",
                            "state": result.data
                        }

                    elif tool_name == "get_cell":
                        result = await tools.get_cell(**tool_args)
                        tool_result_content = result.message  # Use formatted string

                        yield {
                            "type": "cell_content",
                            "cell_id": tool_args.get("cell_id"),
                            "cell": result.data if result.success else None,
                            "error": result.error
                        }

                    elif tool_name == "create_notebook":
                        result = await tools.create_notebook(**tool_args)
                        tool_result_content = result.to_llm_string()

                        if result.success:
                            # Update local reference
                            notebook = tools.notebook

                            yield {
                                "type": "notebook_created",
                                "notebook_name": result.data["notebook_name"],
                                "notebook_path": result.data["notebook_path"]
                            }

                    elif tool_name == "switch_notebook":
                        result = await tools.switch_notebook(**tool_args)
                        tool_result_content = result.to_llm_string()

                        if result.success:
                            # Update local reference
                            notebook = tools.notebook

                            yield {
                                "type": "notebook_switched",
                                "notebook_name": result.data["notebook_name"],
                                "notebook_path": result.data["notebook_path"]
                            }

                    elif tool_name == "write_file":
                        result = await tools.write_file(**tool_args)
                        tool_result_content = result.to_llm_string()

                        if result.success:
                            yield {
                                "type": "file_written",
                                "path": result.data["path"],
                                "bytes_written": result.data["bytes_written"]
                            }

                    elif tool_name == "read_file":
                        result = await tools.read_file(**tool_args)
                        tool_result_content = result.to_llm_string()

                        if result.success:
                            yield {
                                "type": "file_read",
                                "path": result.data["path"],
                                "size": result.data["size"]
                            }

                    elif tool_name == "analyze_notebook":
                        result = await tools.analyze_notebook(**tool_args)
                        tool_result_content = result.message if result.success else result.to_llm_string()

                        yield {
                            "type": "notebook_analysis",
                            "analysis": result.data if result.success else None,
                            "error": result.error
                        }

                    elif tool_name == "final_answer":
                        # Handle task completion signal
                        result = await tools.final_answer(**tool_args)
                        tool_result_content = result.to_llm_string()

                        summary = tool_args.get("summary", "Task completed")
                        outputs = tool_args.get("outputs", [])

                        yield {
                            "type": "task_complete",
                            "summary": summary,
                            "outputs": outputs
                        }
                        
                        # Generate final validation report
                        if task_supervisor:
                            try:
                                final_report = task_supervisor.compile_final_report()
                                # Yield the report as a separate artifact or message
                                yield {
                                    "type": "final_report",
                                    "report": final_report
                                }
                                # Append to summary for persistence
                                summary += "\n\n" + final_report
                            except Exception as e:
                                logger.error(f"Failed to generate final report: {e}")

                        # Yield tool_result so frontend can update step card status
                        yield {
                            "type": "tool_result",
                            "tool_name": tool_name,
                            "result": tool_result_content[:500]
                        }

                        # Add tool result and complete immediately
                        tool_msg = {
                            "role": "tool",
                            "name": tool_name,
                            "content": tool_result_content
                        }
                        current_messages.append(tool_msg)

                        # Save notebook and exit loop
                        notebook_manager.save_notebook(tools.notebook)

                        yield {
                            "type": "notebook_saved",
                            "notebook_path": tools.notebook.path
                        }

                        yield {
                            "type": "complete",
                            "total_steps": step_count,
                            "total_tokens": cumulative_tokens,
                            "final_answer": summary
                        }

                        # Save session memory (background task)
                        librarian_model = agent_roles.get("librarian", model_identifier)
                        final_notebook_state = notebook_manager.get_notebook_state(tools.notebook)

                        try:
                            await consolidate_coder_session_memory(
                                task_id=task_id,
                                user_id=user_id,
                                workspace_path=workspace_path,
                                user_query=user_request,
                                algorithm=algorithm,
                                notebook_state=final_notebook_state,
                                kernel_state=kernel_state,
                                final_summary=summary,
                                model_router=model_router,
                                librarian_model=librarian_model,
                            )
                        except Exception as e:
                            logger.warning(f"Memory consolidation failed: {e}")

                        # Exit the loop completely
                        return

                    else:
                        tool_result_content = f"Unknown tool: {tool_name}"
                        logger.warning(f"Unknown tool called: {tool_name}")

                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    tool_result_content = f"Error executing {tool_name}: {e}"

                # Add tool result to messages
                tool_msg = {
                    "role": "tool",
                    "name": tool_name,
                    "content": tool_result_content
                }
                current_messages.append(tool_msg)

                yield {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "result": (tool_result_content or "")[:500]  # Truncate for SSE
                }

            # Save notebook after tool batch
            notebook_manager.save_notebook(tools.notebook)

            yield {
                "type": "notebook_saved",
                "notebook_path": tools.notebook.path
            }

            # Continue loop for next iteration
            continue

        else:
            # 8. No tool calls - final response
            logger.info("Coder loop completed - final response")

            # Add assistant message to context (for history)
            # Include thinking for persistence (so it can be shown on task reload)
            assistant_msg = {
                "role": "assistant",
                "content": full_content,
                "thinking": full_thinking if full_thinking else None
            }
            current_messages.append(assistant_msg)

            # Save final notebook state
            notebook_manager.save_notebook(tools.notebook)

            yield {
                "type": "notebook_saved",
                "notebook_path": tools.notebook.path
            }

            yield {
                "type": "complete",
                "total_steps": step_count,
                "total_tokens": cumulative_tokens
            }

            # Save session memory (background task)
            librarian_model = agent_roles.get("librarian", model_identifier)
            final_notebook_state = notebook_manager.get_notebook_state(tools.notebook)

            try:
                await consolidate_coder_session_memory(
                    task_id=task_id,
                    user_id=user_id,
                    workspace_path=workspace_path,
                    user_query=user_request,
                    algorithm=algorithm,
                    notebook_state=final_notebook_state,
                    kernel_state=kernel_state,
                    final_summary=full_content,
                    model_router=model_router,
                    librarian_model=librarian_model,
                )
            except Exception as e:
                logger.warning(f"Memory consolidation failed: {e}")

            break

    else:
        # Max steps reached
        logger.warning(f"Coder loop reached max steps ({max_steps})")

        yield {
            "type": "warning",
            "message": f"Reached maximum steps ({max_steps}). The task may be incomplete."
        }

        yield {
            "type": "complete",
            "total_steps": step_count,
            "total_tokens": cumulative_tokens
        }

    # Return conversation for persistence
    # Note: The caller should extract messages for database storage


def extract_messages_for_persistence(current_messages: List[Dict]) -> List[Dict]:
    """
    Extract messages suitable for database persistence.

    Removes system prompt and tool messages, keeping user/assistant turns.
    """
    persist_messages = []

    for msg in current_messages:
        role = msg.get("role")

        if role == "system":
            continue  # Don't persist system prompt

        if role == "tool":
            # Persist tool outputs so context is preserved on refresh
            persist_messages.append({
                "role": "tool",
                "name": msg.get("name"),
                "content": msg.get("content", ""),
                "tool_call_id": msg.get("tool_call_id"),  # If available
                "metadata": {"mode": "coder"}
            })
            continue

        if role in ("user", "assistant"):
            persist_messages.append({
                "role": role,
                "content": msg.get("content", ""),
                "tool_calls": msg.get("tool_calls"),  # Persist tool calls in assistant message
                "thinking": msg.get("thinking"),  # Persist thinking for reconstruction
                # Flag coder messages
                "metadata": {"mode": "coder"}
            })

    return persist_messages


async def consolidate_coder_session_memory(
    task_id: str,
    user_id: str,
    workspace_path: str,
    user_query: str,
    algorithm: Optional[Algorithm],
    notebook_state: NotebookState,
    kernel_state: Optional[KernelState],
    final_summary: str,
    model_router: ModelRouter,
    librarian_model: str,
) -> None:
    """
    Run the Librarian agent to consolidate a coder session into memory.

    This runs in the background after the coder task completes.
    """
    from pathlib import Path
    from datetime import datetime
    from backend.agents.orchestrator.memory import (
        TaskMemoryVault,
        SessionMemory,
        _estimate_tokens,
        _extract_json_from_response,
    )
    from backend.agents.notebook.prompts import CODER_LIBRARIAN_PROMPT

    # Build algorithm summary
    if algorithm:
        algorithm_summary = f"Goal: {algorithm.task_summary}\nSteps:\n"
        algorithm_summary += "\n".join(f"- {s.description}" for s in algorithm.steps)
    else:
        algorithm_summary = "No algorithm (simple request)"

    # Build cells summary
    cells_summary = []
    for cell in notebook_state.cells_summary:
        status = "✅" if cell.get("status") == "success" else "❌" if cell.get("error") else "⚪"
        source_preview = cell.get("source", "")[:80].replace("\n", " ")
        cells_summary.append(f"{status} Cell {cell.get('id', '?')[:8]}: {source_preview}")
    cells_str = "\n".join(cells_summary) if cells_summary else "No cells"

    # Build prompt
    prompt = CODER_LIBRARIAN_PROMPT.format(
        user_query=user_query,
        algorithm_summary=algorithm_summary,
        cells_summary=cells_str,
        final_summary=final_summary[:500] if final_summary else "Task completed"
    )

    # Call Librarian model
    try:
        response = await model_router.chat(
            model_identifier=librarian_model,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,
                "num_predict": 800
            }
        )

        # Handle various response formats
        if isinstance(response, dict):
            # Standard dictionary response
            if "message" in response and "content" in response["message"]:
                response_text = response["message"]["content"]
            elif "response" in response:
                response_text = response["response"]
            else:
                response_text = str(response)
        else:
            # Object response (fallback)
            response_text = response.content if hasattr(response, 'content') else str(response)

        memory_data = _extract_json_from_response(response_text)

        if not memory_data:
            logger.warning("Librarian response was not valid JSON, using fallback")
            memory_data = {
                "user_intent": user_query[:100],
                "accomplished": ["Coder session completed"],
                "notebook_info": {
                    "name": notebook_state.notebook_name,
                    "cells_count": notebook_state.total_cells
                },
                "artifacts": [],
                "key_findings": [],
                "open_questions": []
            }

    except Exception as e:
        logger.error(f"Librarian LLM call failed: {e}")
        memory_data = {
            "user_intent": user_query[:100],
            "accomplished": ["Coder session completed (memory consolidation failed)"],
            "notebook_info": {
                "name": notebook_state.notebook_name,
                "cells_count": notebook_state.total_cells
            },
            "artifacts": [],
            "key_findings": [],
            "open_questions": []
        }

    # Load existing vault
    vault = TaskMemoryVault(
        task_id=task_id,
        user_id=user_id,
        workspace_path=Path(workspace_path)
    ).load()

    # Generate session ID
    session_id = f"{len(vault.sessions) + 1:03d}"

    # Extract artifacts from memory data
    artifacts = memory_data.get("artifacts", [])
    # Add notebook as artifact
    artifacts.append({
        "path": notebook_state.notebook_path,
        "description": f"Jupyter notebook with {notebook_state.total_cells} cells"
    })

    # Build actions from cells
    actions = []
    for cell in notebook_state.cells_summary:
        if cell.get("cell_type") == "code":
            status = "success" if cell.get("status") == "success" else "failed"
            source_preview = cell.get("source", "")[:50].replace("\n", " ")
            actions.append({
                "tool": "execute_cell",
                "summary": f"Executed: {source_preview}...",
                "success": cell.get("status") == "success"
            })

    # Create session memory
    session = SessionMemory(
        session_id=session_id,
        timestamp=datetime.now(),
        user_query=user_query,
        user_intent=memory_data.get("user_intent", user_query[:100]),
        plan_summary=algorithm.task_summary if algorithm else "Direct coding",
        actions_taken=actions,
        artifacts_created=artifacts,
        documents_accessed=[],  # Coder doesn't access documents
        key_findings=memory_data.get("key_findings", []),
        open_questions=memory_data.get("open_questions", []),
        token_count=_estimate_tokens(json.dumps(memory_data))
    )

    # Save to vault
    vault.save_session(session)

    logger.info(f"Saved coder session {session_id} to memory vault")
