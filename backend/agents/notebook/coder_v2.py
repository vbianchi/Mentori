"""
Notebook Coder V2 - Orchestrator-Style Main Loop.

Replaces the ReAct-based coder_loop.py with a structured, phase-based approach:

Phase 0: Analysis - Classify request (trivial/modify/complex/clarification)
Phase 1: Algorithm - Generate and materialize as first cell
Phase 2: Execution - For each step: execute -> evaluate -> retry?
Phase 3: Documentation - Export notebook to HTML/Markdown
Phase 4: Memory - Save with cell registry for follow-up queries

Key difference from coder_loop.py:
- CODE controls iteration over steps, not the agent
- Each phase has a simple, focused prompt
- Cell registry enables instant lookup in follow-up queries
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agents.model_router import ModelRouter
    from backend.agents.session_context import SessionContext

from backend.agents.notebook.analyzer import analyze_request, AnalysisResult
from backend.agents.notebook.algorithm import generate_algorithm
from backend.agents.notebook.environment import gather_environment
from backend.agents.notebook.cell_evaluator import evaluate_cell, CellEvaluation
from backend.agents.notebook.step_executor import execute_step, StepExecutionResult
from backend.agents.notebook.cell_registry import (
    CellRegistry,
    CellRegistryEntry,
    extract_keywords,
)
from backend.agents.notebook.documentation import (
    export_notebook,
    add_summary_cell,
    save_report,
    check_nbconvert_available,
)
from backend.agents.notebook.manager import NotebookManager
from backend.agents.notebook.kernel import KernelRegistry
from backend.agents.notebook.schema import Algorithm, NotebookState
from backend.agents.notebook.prompts_v2 import (
    MODIFICATION_PROMPT,
    build_kernel_state_summary,
)
from backend.agents.orchestrator.memory import (
    TaskMemoryVault,
    SessionMemory,
    _estimate_tokens,
)

logger = logging.getLogger(__name__)


async def coder_loop_v2(
    model_router: "ModelRouter",
    model_identifier: str,
    messages: List[Dict[str, str]],
    session_context: "SessionContext",
    max_steps: int = 20,
    think: bool = False,
    history_log: Optional[List[Dict]] = None,
    display_model: Optional[str] = None,
    cell_strategy: str = "single",
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Orchestrator-style coder loop.

    Phases:
    0. Analysis - Trivial vs complex request
    1. Algorithm - Generate and materialize as first cell
    2. Execution - For each step: execute -> evaluate -> retry?
    3. Documentation - Export notebook
    4. Memory - Save with cell registry

    Args:
        model_router: Router for LLM calls
        model_identifier: Model to use for coding
        messages: Conversation history
        session_context: Current session context
        max_steps: Maximum algorithm steps to execute
        think: Whether to enable extended thinking
        history_log: List to append history entries
        display_model: Model name for UI display

    Yields:
        SSE events for UI updates
    """
    start_time = time.time()

    import logging
    logging.getLogger(__name__).info(f"CODER_V2: Entering coder_loop_v2 with request messages={len(messages)}")
    print(f"DEBUG: Entering coder_loop_v2 with request messages={len(messages)}")

    # Initialize workspace and managers
    workspace_path = Path(session_context.workspace_path)
    notebook_manager = NotebookManager(workspace_path, session_context.task_id)
    kernel_registry = KernelRegistry()

    # Ensure output directory exists
    output_dir = workspace_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load memory vault and cell registry
    vault = TaskMemoryVault(
        task_id=session_context.task_id,
        user_id=session_context.user_id,
        workspace_path=workspace_path,
    ).load()

    memory_context = vault.get_context_for_injection()
    cell_registry_data = vault.load_cell_registry()
    cell_registry = CellRegistry.from_dict(cell_registry_data) if cell_registry_data else CellRegistry()

    if vault.sessions:
        logger.info(f"Loaded memory vault: {len(vault.sessions)} sessions, registry: {len(cell_registry)} cells")

    # Load or create notebook
    notebook = notebook_manager.get_or_create_default()
    print("DEBUG: Notebook loaded")
    kernel = await kernel_registry.get_kernel(
        str(notebook.path),
        str(workspace_path),
    )
    print("DEBUG: Kernel retrieved")

    # Get current states
    notebook_state = notebook_manager.get_notebook_state(notebook)
    print("DEBUG: Notebook state retrieved")
    kernel_state = await kernel.get_kernel_variables()
    print("DEBUG: Kernel variables retrieved")

    # Extract user request
    user_request = _extract_user_query(messages)
    print(f"DEBUG: User request extracted: {user_request}")

    # Emit session info
    nb_name = notebook.name if hasattr(notebook, 'name') else "main.ipynb"
    nb_path = str(notebook.path) if hasattr(notebook, 'path') else ""
    nb_cell_count = len(notebook.cells) if hasattr(notebook, 'cells') else 0

    print("DEBUG: Yielding first session_info event")
    yield {
        "type": "session_info",
        "session_info": {
            "mode": "coder_v2",
            "model": display_model or model_identifier,
            "notebook_name": nb_name,
            "notebook_path": nb_path,
            "cell_count": nb_cell_count,
        }
    }

    print("DEBUG: Processing cells data for notebook UI sync")
    cells_data = []
    for cell in notebook.cells:
        cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
        c_type = cell.cell_type if hasattr(cell, 'cell_type') else cell.get('cell_type', 'code')
        c_source = cell.source if hasattr(cell, 'source') else cell.get('source', '')
        c_status = cell.status if hasattr(cell, 'status') else cell.get('status', 'idle')
        c_exec_count = cell.execution_count if hasattr(cell, 'execution_count') else cell.get('execution_count', None)
        c_outputs = []
        raw_outputs = cell.outputs if hasattr(cell, 'outputs') else cell.get('outputs', [])
        for o in raw_outputs:
            c_outputs.append(o.to_dict() if hasattr(o, 'to_dict') else o)
        cells_data.append({
            "id": cid,
            "cell_type": c_type,
            "source": c_source,
            "status": c_status,
            "execution_count": c_exec_count,
            "outputs": c_outputs,
        })

    print(f"DEBUG: Yielding notebook_loaded with {len(cells_data)} cells")
    yield {
        "type": "notebook_loaded",
        "notebook_name": nb_name,
        "notebook_path": nb_path,
        "cell_count": nb_cell_count,
        "cells": cells_data,
    }

    if nb_cell_count > 0:
        logger.info(f"Sent notebook_loaded with {nb_cell_count} existing cells to frontend")

    # Emit memory context if available
    if cell_registry:
        print("DEBUG: Yielding memory_loaded")
        yield {
            "type": "memory_loaded",
            "session_count": len(vault.sessions),
            "cell_registry_count": len(cell_registry),
        }

    # Create async event queue for streaming
    event_queue: asyncio.Queue = asyncio.Queue()

    async def emit_event(event: Dict[str, Any]):
        await event_queue.put(event)

    # ========================================
    # PHASE 0: REQUEST ANALYSIS
    # ========================================
    print("DEBUG: Yielding analysis status")
    yield {"type": "status", "status": "Analyzing", "detail": "Understanding your request..."}

    print("DEBUG: Calling analyze_request")
    try:
        analysis = await analyze_request(
            user_request=user_request,
            notebook_state=notebook_state.to_dict() if notebook_state else None,
            memory_context=memory_context,
            cell_registry=cell_registry if cell_registry else None,
            model_router=model_router,
            model_identifier=model_identifier,
        )
        print(f"DEBUG: analyze_request finished with classification: {analysis.classification}")
    except Exception as e:
        print(f"DEBUG: analyze_request CRASHED: {e}")
        raise

    import logging
    print("DEBUG: Calling logger.info for analysis finished")
    logging.getLogger(__name__).info(f"CODER_V2: Analysis finished with classification: {analysis.classification}")
    logger.info(f"Analysis: {analysis.classification} (intent: {analysis.detected_intent})")

    print("DEBUG: Yielding analysis_complete event")
    yield {
        "type": "analysis_complete",
        "classification": analysis.classification,
        "detected_intent": analysis.detected_intent,
        "relevant_cells": analysis.relevant_cells,
    }
    print("DEBUG: Successfully yielded analysis_complete event")

    # Handle clarification needed
    if analysis.needs_clarification:
        print("DEBUG: Needs clarification, yielding complete and returning")
        yield {
            "type": "clarification_needed",
            "question": analysis.clarification_question,
        }
        yield {"type": "complete", "status": "needs_clarification"}
        return

    print("DEBUG: Moving directly to TRIVIAL REQUEST PATH")
    print(f"DEBUG: analysis.is_trivial={analysis.is_trivial}, analysis.is_modify={analysis.is_modify}")
    # ========================================
    # TRIVIAL REQUEST PATH
    # ========================================
    if analysis.is_trivial:
        # Only attempt trivial execution if there are cells to work with
        if notebook.cells and analysis.relevant_cells:
            yield {"type": "status", "status": "Executing", "detail": "Running simple operation..."}

            # Use generator to stream cell events in real-time
            result = None
            async for event in _execute_trivial_request_generator(
                analysis=analysis,
                notebook=notebook,
                notebook_manager=notebook_manager,
                kernel=kernel,
            ):
                if event.get("type") == "_trivial_result":
                    result = event["result"]
                else:
                    # Yield cell events immediately for real-time streaming
                    yield event

            if result and result.get("success"):
                yield {"type": "status", "status": "Ready", "detail": "Done."}
                yield {"type": "complete", "trivial": True}
                return

        # No cells or trivial execution failed - fall through to complex path
        logger.info("Trivial path has no cells to work with, falling back to complex")
        analysis = AnalysisResult(
            classification="complex",
            detected_intent=analysis.detected_intent,
            relevant_cells=[],
            modification_target=None,
            clarification_question=None,
            confidence=0.5,
        )

    # ========================================
    # MODIFICATION REQUEST PATH
    # ========================================
    if analysis.is_modify and analysis.modification_target:
        yield {"type": "status", "status": "Modifying", "detail": "Updating cell..."}

        result = await _execute_modification(
            analysis=analysis,
            notebook=notebook,
            cell_registry=cell_registry,
            notebook_manager=notebook_manager,
            kernel=kernel,
            model_router=model_router,
            model_identifier=model_identifier,
            event_callback=emit_event,
        )

        # Drain events
        while not event_queue.empty():
            yield await event_queue.get()

        # Only complete if modification actually succeeded
        if result.get("success"):
            # Update cell registry
            if result.get("cell_id"):
                _update_registry_for_modification(
                    cell_registry=cell_registry,
                    cell_id=result["cell_id"],
                    user_request=user_request,
                )
                vault.save_cell_registry(cell_registry.to_dict())

            yield {"type": "status", "status": "Ready", "detail": "Done."}
            yield {"type": "complete", "modified": True, "cell_id": result.get("cell_id")}
            return

        # Modification failed, fall through to algorithm generation
        logger.info("Modification failed, falling through to algorithm generation")

    # ========================================
    # PHASE 0.5: ENVIRONMENT GATHERING
    # ========================================
    print("DEBUG: Reached PHASE 0.5: ENVIRONMENT GATHERING")
    print("DEBUG: Yielding gathering status")
    yield {"type": "status", "status": "Gathering", "detail": "Gathering environment information..."}

    print("DEBUG: Making files directory")
    # Ensure files directory exists (like orchestrator does)
    (workspace_path / "files").mkdir(parents=True, exist_ok=True)

    print("DEBUG: Calling gather_environment")
    try:
        environment_context = gather_environment(workspace_path, user_request)
        print(f"DEBUG: gather_environment returned {len(environment_context)} chars")
    except Exception as e:
        print(f"DEBUG: gather_environment CRASHED: {e}")
        raise
    logger.info(f"Environment context: {len(environment_context)} chars")

    # ========================================
    # PHASE 1: ALGORITHM GENERATION
    # ========================================
    print("DEBUG: Reached PHASE 1: ALGORITHM GENERATION")
    yield {"type": "status", "status": "Planning", "detail": "Creating algorithm..."}
    print("DEBUG: Yielded Planning status")
    yield {"type": "orchestrator_thinking_start", "phase": "planning"}
    print("DEBUG: Yielded orchestrator_thinking_start")

    # Status callback pushes to the event queue for real-time streaming
    async def _planning_status(detail: str):
        await event_queue.put({"type": "status", "status": "Planning", "detail": detail})

    # Run algorithm generation in a task so we can drain events in real-time
    algorithm_result: List[Optional[Algorithm]] = [None]

    async def _run_algorithm_generation():
        print("DEBUG: Inside _run_algorithm_generation task")
        algorithm_result[0] = await generate_algorithm(
            model_router=model_router,
            model_identifier=model_identifier,
            user_request=user_request,
            notebook_state=notebook_state,
            kernel_state=kernel_state,
            memory_context=memory_context,
            status_callback=_planning_status,
            environment_context=environment_context,
        )
        print("DEBUG: Finished generate_algorithm")

    print("DEBUG: Creating task _run_algorithm_generation")
    gen_task = asyncio.create_task(_run_algorithm_generation())

    print("DEBUG: Draining status events while algorithm generates")
    # Drain status events while algorithm generates
    while not gen_task.done():
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=0.5)
            yield event
        except asyncio.TimeoutError:
            continue

    await gen_task  # Ensure completion / propagate exceptions

    # Drain remaining events
    while not event_queue.empty():
        yield await event_queue.get()

    algorithm = algorithm_result[0]

    if not algorithm or not algorithm.steps:
        yield {"type": "error", "message": "Failed to generate algorithm. Please try rephrasing your request."}
        return

    # Materialize algorithm as first markdown cell
    algorithm_content = algorithm.to_markdown_cell()
    algorithm_cell = notebook.add_cell(algorithm_content, "markdown", position=0)
    notebook_manager.save_notebook(notebook)

    logger.info(f"Algorithm generated: {len(algorithm.steps)} steps")

    yield {
        "type": "algorithm_generated",
        "algorithm": algorithm.to_dict(),
        "cell_id": algorithm_cell.id if hasattr(algorithm_cell, 'id') else algorithm_cell.get('id', ''),
    }

    yield {
        "type": "cell_added",
        "cell_id": algorithm_cell.id if hasattr(algorithm_cell, 'id') else algorithm_cell.get('id', ''),
        "cell_type": "markdown",
        "index": 0,
        "source": algorithm_content,
    }

    # Save to history
    if history_log is not None:
        history_log.append({
            "role": "assistant",
            "content": algorithm_content,
            "metadata_blob": {
                "phase": "planning",
                "mode": "coder_v2",
                "algorithm": algorithm.to_dict(),
            }
        })

    # Limit steps if needed
    if len(algorithm.steps) > max_steps:
        logger.warning(f"Algorithm has {len(algorithm.steps)} steps, limiting to {max_steps}")
        algorithm.steps = algorithm.steps[:max_steps]

    # ========================================
    # PHASE 2: STEP-BY-STEP EXECUTION
    # ========================================
    yield {"type": "status", "status": "Executing", "detail": f"Running {len(algorithm.steps)} steps..."}

    import logging
    logging.getLogger(__name__).info(f"CODER_V2: algorithm steps length is {len(algorithm.steps)}")

    step_results: List[StepExecutionResult] = []
    total_retries = 0

    for step in algorithm.steps:
        # Check for cancellation between steps
        current_task = asyncio.current_task()
        if current_task and current_task.cancelled():
            logger.info(f"Coder loop cancelled at step {step.step_number}")
            yield {"type": "status", "status": "Cancelled", "detail": "Task cancelled by user."}
            return

        yield {
            "type": "step_started",
            "step_number": step.step_number,
            "description": step.description,
            "expected_output": step.expected_output,
            "total_steps": len(algorithm.steps),
        }

        # Execute step
        execution_result = None
        evaluation = None  # Initialize before loop
        retry_feedback = None
        max_retries = 3
        retry_count = 0
        cell_id = None  # Initialize before loop to avoid UnboundLocalError

        while retry_count <= max_retries:
            # Execute the step with full algorithm context
            import logging
            logging.getLogger(__name__).info(f"CODER_V2: Yielding async from execute_step for step {step.step_number}")
            async for event in execute_step(
                step=step,
                notebook=notebook,
                notebook_manager=notebook_manager,
                kernel=kernel,
                model_router=model_router,
                model_identifier=model_identifier,
                previous_results=step_results,
                algorithm=algorithm,
                retry_feedback=retry_feedback,
                event_callback=emit_event,
                environment_context=environment_context,
                cell_strategy=cell_strategy,
            ):
                if event.get("type") == "_step_result":
                    execution_result = event["result"]
                else:
                    yield event

            # Drain queued events
            while not event_queue.empty():
                yield await event_queue.get()

            if not execution_result or not execution_result.cells_created:
                yield {
                    "type": "step_failed",
                    "step_number": step.step_number,
                    "error": execution_result.error_message if execution_result else "No cells created",
                }
                break

            # Get the main cell for evaluation — pick the last EXECUTED cell
            # (not the last created, which may never have been executed due to LLM errors)
            main_cell = None
            for candidate in reversed(execution_result.cells_created):
                c_status = getattr(candidate, 'status', None) or (candidate.get('status') if isinstance(candidate, dict) else None)
                c_outputs = getattr(candidate, 'outputs', None) or (candidate.get('outputs', []) if isinstance(candidate, dict) else [])
                if c_status != 'idle' or c_outputs:
                    main_cell = candidate
                    break

            if not main_cell:
                # No cell was executed — the LLM wrote code but errored before calling
                # execute_cell (malformed tool call, XML/JSON parse error, etc.).
                # The code is valid; try to execute the idle cells directly before
                # burning a full LLM retry.
                logger.warning(
                    f"Step {step.step_number}: all {len(execution_result.cells_created)} "
                    "cells are idle/unexecuted — attempting direct execution"
                )
                recovered = None
                for cell in execution_result.cells_created:
                    source = cell.source if hasattr(cell, 'source') else cell.get('source', '')
                    if not source.strip():
                        continue
                    cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
                    try:
                        outputs = []
                        async for output in kernel.execute(source):
                            outputs.append(output)
                            yield {
                                "type": "cell_event",
                                "event": {
                                    "type": "output",
                                    "cell_id": cid,
                                    "output": output.to_dict() if hasattr(output, 'to_dict') else output,
                                },
                            }
                        has_error = any(
                            (getattr(o, 'output_type', None) or (o.get('output_type', '') if isinstance(o, dict) else '')) == 'error'
                            for o in outputs
                        )
                        if hasattr(cell, 'outputs'):
                            cell.outputs = outputs
                            cell.status = 'error' if has_error else 'success'
                        else:
                            cell['outputs'] = [o.to_dict() if hasattr(o, 'to_dict') else o for o in outputs]
                            cell['status'] = 'error' if has_error else 'success'
                        recovered = cell
                        logger.info(
                            f"Step {step.step_number}: direct execution of idle cell "
                            f"{cid[:8]} succeeded ({len(outputs)} outputs)"
                        )
                    except Exception as exc:
                        logger.warning(
                            f"Step {step.step_number}: direct execution of idle cell "
                            f"{cid[:8]} failed: {exc}"
                        )

                if recovered is not None:
                    notebook_manager.save_notebook(notebook)
                    main_cell = recovered
                    yield {
                        "type": "idle_cell_recovered",
                        "step_number": step.step_number,
                        "cell_id": recovered.id if hasattr(recovered, 'id') else recovered.get('id', ''),
                    }
                    # Fall through to evaluation below
                else:
                    # Direct execution failed — fall back to delete-and-LLM-retry
                    for cell in execution_result.cells_created:
                        cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
                        try:
                            notebook.delete_cell(cid)
                            yield {"type": "cell_deleted", "cell_id": cid, "reason": "never_executed"}
                        except Exception:
                            pass
                    notebook_manager.save_notebook(notebook)
                    execution_result.cells_created = []
                    if retry_count < max_retries:
                        retry_count += 1
                        total_retries += 1
                        retry_feedback = "Cell was created but could not be executed. Try again with simpler code in a single cell."
                        yield {
                            "type": "step_retry",
                            "step_number": step.step_number,
                            "attempt": retry_count,
                            "max_retries": max_retries,
                            "feedback": retry_feedback,
                        }
                        logger.info(f"Retrying step {step.step_number} (attempt {retry_count}): direct execution also failed")
                        continue
                    else:
                        break

            # Debug: Log cell state before evaluation
            main_cell_id = main_cell.id if hasattr(main_cell, 'id') else main_cell.get('id', 'unknown')
            main_cell_outputs = main_cell.outputs if hasattr(main_cell, 'outputs') else main_cell.get('outputs', [])
            logger.info(f"Before evaluate_cell: cell_id={main_cell_id[:8]}, outputs_count={len(main_cell_outputs) if main_cell_outputs else 0}, cells_created_count={len(execution_result.cells_created)}")

            # ========================================
            # EVALUATION
            # ========================================
            evaluation = await evaluate_cell(
                cell=main_cell,
                step=step,
                model_router=model_router,
                model_identifier=model_identifier,
                vision_model=session_context.agent_roles.get("vision"),
            )

            yield {
                "type": "cell_evaluation",
                "cell_id": main_cell.id if hasattr(main_cell, 'id') else main_cell.get('id', ''),
                "step_number": step.step_number,
                "score": evaluation.score,
                "meets_expectations": evaluation.meets_expectations,
                "should_retry": evaluation.should_retry,
                "feedback": evaluation.feedback,
                "issues": evaluation.issues,
            }

            # Check if acceptable
            if evaluation.is_acceptable:
                break

            # Retry if needed
            if evaluation.should_retry and retry_count < max_retries:
                retry_count += 1
                total_retries += 1
                retry_feedback = evaluation.feedback

                # Clean up failed cells BEFORE retrying so they don't accumulate
                if execution_result and execution_result.cells_created:
                    logger.info(f"Cleaning up {len(execution_result.cells_created)} cells before retry {retry_count}")
                    for cell in execution_result.cells_created:
                        cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
                        try:
                            notebook.delete_cell(cid)
                            yield {
                                "type": "cell_deleted",
                                "cell_id": cid,
                                "reason": "cleanup_before_retry"
                            }
                        except Exception as e:
                            logger.warning(f"Failed to delete cell {cid}: {e}")
                    notebook_manager.save_notebook(notebook)
                    execution_result.cells_created = []

                yield {
                    "type": "step_retry",
                    "step_number": step.step_number,
                    "attempt": retry_count,
                    "max_retries": max_retries,
                    "feedback": retry_feedback,
                }

                logger.info(f"Retrying step {step.step_number} (attempt {retry_count}): {retry_feedback}")
            else:
                # Max retries reached or critical failure
                # Clean up failed cells
                if execution_result and execution_result.cells_created and not evaluation.is_acceptable:
                     logger.info(f"Auto-cleanup: Deleting {len(execution_result.cells_created)} failed cells for step {step.step_number}")
                     for cell in execution_result.cells_created:
                         cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
                         try:
                             notebook.delete_cell(cid)
                             yield {
                                 "type": "cell_deleted",
                                 "cell_id": cid,
                                 "reason": "cleanup_failed_step"
                             }
                         except Exception as e:
                             logger.warning(f"Failed to delete cell {cid}: {e}")

                     notebook_manager.save_notebook(notebook)
                     execution_result.cells_created = []

                break

        # Update cell registry
        if execution_result and execution_result.cells_created:
            main_cell = execution_result.cells_created[-1]
            cell_id = main_cell.id if hasattr(main_cell, 'id') else main_cell.get('id', '')
            cell_source = main_cell.source if hasattr(main_cell, 'source') else main_cell.get('source', '')
            cell_outputs = main_cell.outputs if hasattr(main_cell, 'outputs') else main_cell.get('outputs', [])

            keywords = extract_keywords(
                step_description=step.description,
                step_keywords=step.keywords if hasattr(step, 'keywords') else [],
                cell_source=cell_source,
                cell_outputs=[o.to_dict() if hasattr(o, 'to_dict') else o for o in cell_outputs],
                variables_created=execution_result.variables_created,
            )

            registry_entry = CellRegistryEntry(
                cell_id=cell_id,
                algorithm_step=step.step_number,
                purpose=step.description,
                expected_output=step.expected_output or "",
                actual_output_summary=_summarize_cell_output(main_cell),
                keywords=keywords,
                variables_created=execution_result.variables_created,
                files_created=execution_result.files_created,
                evaluation_score=evaluation.score if evaluation else 0,
                created_at=datetime.now(),
                retry_count=retry_count,
            )
            cell_registry.add_entry(registry_entry)

        step_results.append(execution_result)

        yield {
            "type": "step_complete",
            "step_number": step.step_number,
            "cell_id": cell_id if execution_result and execution_result.cells_created else None,
            "score": evaluation.score if evaluation else 0,
            "variables_created": execution_result.variables_created if execution_result else [],
            "files_created": execution_result.files_created if execution_result else [],
        }

        # Save to history
        if history_log is not None and execution_result:
            history_log.append({
                "role": "assistant",
                "content": f"Step {step.step_number}: {step.description}",
                "metadata_blob": {
                    "phase": "executing",
                    "mode": "coder_v2",
                    "step_number": step.step_number,
                    "cell_id": cell_id if execution_result.cells_created else None,
                    "score": evaluation.score if evaluation else 0,
                }
            })

    execution_time = time.time() - start_time

    # ========================================
    # PHASE 3: DOCUMENTATION
    # ========================================
    yield {"type": "status", "status": "Documenting", "detail": "Creating summary..."}

    # Add summary cell
    try:
        summary_cell = await add_summary_cell(
            notebook=notebook,
            notebook_manager=notebook_manager,
            algorithm=algorithm,
            cell_registry=cell_registry,
            execution_time=execution_time,
        )
        summary_cell_id = summary_cell.id if hasattr(summary_cell, 'id') else summary_cell.get('id', '')
        summary_source = summary_cell.source if hasattr(summary_cell, 'source') else summary_cell.get('source', '')
        yield {
            "type": "cell_added",
            "cell_id": summary_cell_id,
            "cell_type": "markdown",
            "index": len(notebook.cells) - 1,
            "source": summary_source,
        }
    except Exception as e:
        logger.warning(f"Failed to add summary cell: {e}")

    # Export notebook to HTML and Markdown for sharing
    exports = {}
    try:
        # notebook.path is relative like "notebooks/main.ipynb"
        notebook_path = workspace_path / notebook.path
        logger.info(f"Export: notebook_path={notebook_path}, exists={notebook_path.exists()}")
        if notebook_path.exists() and check_nbconvert_available():
            exports = await export_notebook(notebook_path, output_dir, formats=["html", "markdown"])
            logger.info(f"Export result: {exports}")
            if exports:
                yield {
                    "type": "documentation_created",
                    "exports": {fmt: str(path) for fmt, path in exports.items()},
                }
                logger.info(f"Exported notebook to: {list(exports.values())}")
        else:
            logger.warning(f"Notebook path does not exist: {notebook_path}")
    except Exception as e:
        logger.warning(f"Failed to export notebook: {e}", exc_info=True)

    # Save detailed report
    try:
        report_path = await save_report(
            algorithm=algorithm,
            cell_registry=cell_registry,
            notebook_path=workspace_path / notebook.path,
            output_dir=output_dir,
        )
        if report_path:
             yield {
                 "type": "report_created",
                 "path": str(report_path),
                 "name": report_path.name
             }
             # Add to artifacts list for memory
             exports["report"] = report_path
    except Exception as e:
        logger.warning(f"Failed to save report: {e}")

    # ========================================
    # PHASE 4: MEMORY CONSOLIDATION
    # ========================================
    yield {"type": "status", "status": "Saving", "detail": "Consolidating memory..."}

    # Save cell registry
    vault.save_cell_registry(cell_registry.to_dict())

    # Create session memory
    session_id = f"{len(vault.sessions) + 1:03d}"

    # Build cell purposes for quick lookup
    cell_purposes = {
        entry.cell_id[:8]: entry.purpose
        for entry in cell_registry.entries.values()
    }

    # Build artifacts list
    artifacts = []
    for entry in cell_registry.entries.values():
        for f in entry.files_created:
            artifacts.append({
                "path": f,
                "description": f"Created by Step {entry.algorithm_step}: {entry.purpose}",
            })

    # Add notebook as artifact
    artifacts.append({
        "path": str(notebook.path) if hasattr(notebook, 'path') else "notebooks/main.ipynb",
        "description": f"Notebook with {len(notebook.cells if hasattr(notebook, 'cells') else [])} cells",
    })

    # Add exports as artifacts
    for fmt, path in exports.items():
        artifacts.append({
            "path": str(path),
            "description": f"Notebook exported as {fmt.upper()}",
        })

    session = SessionMemory(
        session_id=session_id,
        timestamp=datetime.now(),
        user_query=user_request,
        user_intent=analysis.detected_intent,
        plan_summary=algorithm.task_summary,
        actions_taken=[
            {
                "tool": "execute_step",
                "summary": f"Step {r.tool_calls_made} calls" if r else "Failed",
                "success": r.success if r else False,
            }
            for r in step_results
        ],
        artifacts_created=artifacts,
        documents_accessed=[],
        key_findings=[],
        open_questions=[],
        token_count=_estimate_tokens(json.dumps(cell_registry.to_dict())),
        session_mode="coder",
        cell_registry=cell_registry.to_dict(),
        cell_purposes=cell_purposes,
    )

    vault.save_session(session)
    logger.info(f"Saved coder session {session_id} with {len(cell_registry)} cells in registry")

    # Build summary for UI
    logger.info("Building execution summary for UI...")
    successful_steps = sum(1 for r in step_results if r and r.success)
    all_files_created = []
    for entry in cell_registry.entries.values():
        all_files_created.extend(entry.files_created)

    summary_data = {
        "task_summary": algorithm.task_summary,
        "steps_completed": successful_steps,
        "total_steps": len(algorithm.steps),
        "cells_created": sum(len(r.cells_created) for r in step_results if r),
        "files_created": all_files_created,
        "exports": {fmt: str(path) for fmt, path in exports.items()},
        "execution_time": round(execution_time, 1),
        "notebook_path": str(notebook.path) if hasattr(notebook, 'path') else "notebooks/main.ipynb",
    }
    logger.info(f"Emitting execution_summary event: {summary_data}")

    # Emit summary event for UI
    yield {
        "type": "execution_summary",
        "summary": summary_data,
    }
    logger.info("execution_summary event emitted successfully")

    # Save summary to history for reconstruction
    if history_log is not None:
        history_log.append({
            "role": "assistant",
            "content": f"Completed: {algorithm.task_summary}",
            "metadata_blob": {
                "phase": "summary",
                "mode": "coder_v2",
                "summary": summary_data,
            }
        })

    # Final status
    yield {"type": "status", "status": "Ready", "detail": "Done."}
    yield {"type": "fs_update", "path": "/"}
    yield {
        "type": "complete",
        "steps_completed": len(step_results),
        "total_steps": len(algorithm.steps),
        "cells_created": sum(len(r.cells_created) for r in step_results if r),
        "total_retries": total_retries,
        "execution_time": execution_time,
        "cell_registry_size": len(cell_registry),
    }


def _extract_user_query(messages: List[Dict[str, str]]) -> str:
    """Extract the most recent user query from messages."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


async def _execute_trivial_request_generator(
    analysis: AnalysisResult,
    notebook: Any,
    notebook_manager: "NotebookManager",
    kernel: Any,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a trivial request and yield events for real-time streaming.

    Yields cell_event dicts during execution, then yields _trivial_result at the end.
    """
    # If we have relevant cells, try to execute them
    if analysis.relevant_cells:
        cell_id = analysis.relevant_cells[0]

        # Find the cell
        for cell in notebook.cells:
            cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
            if cell_id and (cid == cell_id or cid.startswith(cell_id)):
                # Execute it
                source = cell.source if hasattr(cell, 'source') else cell.get('source', '')

                # Emit execution start
                yield {
                    "type": "cell_event",
                    "event": {
                        "type": "execution_start",
                        "cell_id": cid,
                    }
                }

                outputs = []
                async for output in kernel.execute(source):
                    outputs.append(output)
                    # Emit output event immediately for real-time streaming
                    yield {
                        "type": "cell_event",
                        "event": {
                            "type": "output",
                            "cell_id": cid,
                            "output": output.to_dict() if hasattr(output, 'to_dict') else output,
                        }
                    }

                # Update cell
                if hasattr(cell, 'outputs'):
                    cell.outputs = outputs
                    cell.status = 'success'
                else:
                    cell['outputs'] = outputs
                    cell['status'] = 'success'

                # Check for errors in outputs
                for output in outputs:
                    output_type = output.output_type if hasattr(output, 'output_type') else output.get('output_type', '')
                    if output_type == 'error':
                        if hasattr(cell, 'status'):
                            cell.status = 'error'
                        else:
                            cell['status'] = 'error'
                        break

                notebook_manager.save_notebook(notebook)

                # Emit completion
                status = cell.status if hasattr(cell, 'status') else cell.get('status', 'success')
                yield {
                    "type": "cell_event",
                    "event": {
                        "type": "execution_complete",
                        "cell_id": cid,
                        "status": status,
                        "has_images": any(
                            (hasattr(o, 'data') and any(k.startswith('image/') for k in (o.data or {}).keys()))
                            or (isinstance(o, dict) and any(k.startswith('image/') for k in o.get('data', {}).keys()))
                            for o in outputs
                        ),
                    }
                }

                # Yield final result
                yield {"type": "_trivial_result", "result": {"success": True, "cell_id": cid}}
                return

    # No relevant cells found
    yield {"type": "_trivial_result", "result": {"success": False, "error": "Could not find cell to execute"}}


async def _execute_modification(
    analysis: AnalysisResult,
    notebook: Any,
    cell_registry: CellRegistry,
    notebook_manager: "NotebookManager",
    kernel: Any,
    model_router: "ModelRouter",
    model_identifier: str,
    event_callback: Any,
) -> Dict[str, Any]:
    """Execute a modification request on an existing cell."""
    cell_id = analysis.modification_target

    # Find the cell
    target_cell = None
    for cell in notebook.cells:
        cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
        if cid == cell_id or cid.startswith(cell_id):
            target_cell = cell
            cell_id = cid  # Use full ID
            break

    if not target_cell:
        return {"success": False, "error": f"Cell {cell_id} not found"}

    # Get cell info from registry
    registry_entry = cell_registry.get_entry(cell_id)
    cell_purpose = registry_entry.purpose if registry_entry else "Unknown"
    cell_source = target_cell.source if hasattr(target_cell, 'source') else target_cell.get('source', '')
    cell_output = _summarize_cell_output(target_cell)

    # Get kernel state
    kernel_state = await kernel.get_kernel_variables()

    # Build modification prompt
    prompt = MODIFICATION_PROMPT.format(
        user_request=analysis.detected_intent,
        cell_id=cell_id[:8],
        cell_source=cell_source,
        cell_purpose=cell_purpose,
        cell_output=cell_output,
        kernel_state=build_kernel_state_summary(kernel_state.to_dict() if kernel_state else {}),
    )

    # Call LLM to get modified code
    try:
        response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 3000},
        )

        response_text = ""
        if isinstance(response, dict):
            msg = response.get("message", {})
            response_text = msg.get("content", "") if isinstance(msg, dict) else response.get("response", "")

        # Extract code from response
        import re
        code_match = re.search(r'```python\s*(.*?)```', response_text, re.DOTALL)
        if code_match:
            new_source = code_match.group(1).strip()
        else:
            # Try to find raw code (no markdown wrapping)
            new_source = response_text.strip()
            # If it doesn't look like code, fail
            if not any(kw in new_source for kw in ['import ', 'def ', '=', 'print', 'plt.', 'sns.']):
                return {"success": False, "error": "LLM did not produce valid code for modification"}

        # Apply the edit
        if hasattr(target_cell, 'source'):
            target_cell.source = new_source
            target_cell.outputs = []
            target_cell.status = 'idle'
        else:
            target_cell['source'] = new_source
            target_cell['outputs'] = []
            target_cell['status'] = 'idle'

        notebook_manager.save_notebook(notebook)

        # Emit cell_edited event
        if event_callback:
            await event_callback({
                "type": "cell_edited",
                "cell_id": cell_id,
                "source": new_source,
            })

        # Re-execute the modified cell
        outputs = []
        async for output in kernel.execute(new_source):
            outputs.append(output)
            if event_callback:
                await event_callback({
                    "type": "cell_event",
                    "event": {
                        "type": "output",
                        "cell_id": cell_id,
                        "output": output.to_dict() if hasattr(output, 'to_dict') else output,
                    }
                })

        # Update cell with outputs
        has_error = False
        if hasattr(target_cell, 'outputs'):
            target_cell.outputs = outputs
            target_cell.status = 'success'
        else:
            target_cell['outputs'] = [o.to_dict() if hasattr(o, 'to_dict') else o for o in outputs]
            target_cell['status'] = 'success'

        for output in outputs:
            output_type = output.output_type if hasattr(output, 'output_type') else output.get('output_type', '')
            if output_type == 'error':
                if hasattr(target_cell, 'status'):
                    target_cell.status = 'error'
                else:
                    target_cell['status'] = 'error'
                has_error = True
                break

        notebook_manager.save_notebook(notebook)

        if event_callback:
            await event_callback({
                "type": "cell_event",
                "event": {
                    "type": "execution_complete",
                    "cell_id": cell_id,
                    "status": "error" if has_error else "success",
                }
            })

        return {"success": not has_error, "cell_id": cell_id}

    except Exception as e:
        logger.error(f"Modification failed: {e}")
        return {"success": False, "error": str(e)}


def _update_registry_for_modification(
    cell_registry: CellRegistry,
    cell_id: str,
    user_request: str,
) -> None:
    """Update registry entry after modification."""
    entry = cell_registry.get_entry(cell_id)
    if entry:
        # Add modification note to purpose
        entry.purpose = f"{entry.purpose} (modified: {user_request[:50]})"
        cell_registry.update_entry(entry)


def _summarize_cell_output(cell: Any) -> str:
    """Create brief summary of cell outputs."""
    outputs = cell.outputs if hasattr(cell, 'outputs') else cell.get('outputs', [])

    summaries = []
    for output in outputs[:3]:
        if hasattr(output, 'output_type'):
            output_type = output.output_type
        elif isinstance(output, dict):
            output_type = output.get('output_type', 'unknown')
        else:
            continue

        if output_type == 'stream':
            text = (output.text if hasattr(output, 'text') else output.get('text', '')) or ''
            summaries.append(text[:100])
        elif output_type == 'execute_result':
            summaries.append("[result displayed]")
        elif output_type == 'display_data':
            summaries.append("[visualization]")
        elif output_type == 'error':
            ename = output.ename if hasattr(output, 'ename') else output.get('ename', 'Error')
            summaries.append(f"[error: {ename}]")

    return " ".join(summaries) if summaries else "No output"
