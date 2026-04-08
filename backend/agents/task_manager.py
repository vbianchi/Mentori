import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, AsyncGenerator, Optional, Union
import json

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import SessionContext
from backend.agents.content_filter import filter_event
from backend.logging_config import logger
from backend.agents.orchestrator.schemas import CollaborationContext, CollaborationResponse

# Import orchestrator (lazy to avoid circular imports)
def _get_orchestrated_chat():
    from backend.agents.orchestrator.engine import orchestrated_chat
    return orchestrated_chat

# Import coder loop (lazy to avoid circular imports)
def _get_coder_loop():
    from backend.agents.notebook.coder_loop import coder_loop
    return coder_loop


def _get_coder_loop_v2():
    from backend.agents.notebook.coder_v2 import coder_loop_v2
    return coder_loop_v2


# Feature flag for coder V2 (orchestrator-style)
# Set to True to use the new structured approach
USE_CODER_V2 = True

class TaskManager:
    """
    Singleton to manage background chat tasks and event broadcasting.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        # Active background tasks: {task_id: asyncio.Task}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Subscriber queues for each task: {task_id: List[asyncio.Queue]}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        
        # Live State Tracking for reconnection: {task_id: dict}
        self.task_states: Dict[str, Dict] = {}
        
    async def start_chat_task(
        self,
        task_id: str,
        model_router: ModelRouter,
        model_identifier: str,
        messages: List[Dict[str, str]],
        session_context: SessionContext,
        max_steps: int = 10,
        think: bool = False,
        display_model: str = None,
        token_budget: Optional[int] = None
    ):
        """
        Start a background chat task.

        DEPRECATED: This method now redirects to start_orchestrated_task.
        The legacy chat_loop has been removed in favor of the orchestrator.
        """
        logger.warning(f"start_chat_task is deprecated, redirecting to orchestrator for task {task_id}")
        await self.start_orchestrated_task(
            task_id=task_id,
            model_router=model_router,
            model_identifier=model_identifier,
            messages=messages,
            session_context=session_context,
            max_steps=max_steps,
            think=think,
            display_model=display_model,
            token_budget=token_budget
        )

    async def start_orchestrated_task(
        self,
        task_id: str,
        model_router: ModelRouter,
        model_identifier: str,
        messages: List[Dict[str, str]],
        session_context: SessionContext,
        max_steps: int = 10,
        think: Union[bool, str] = False,
        display_model: str = None,
        token_budget: Optional[int] = None
    ):
        """
        Start a background orchestrated chat task (new multi-agent system).

        Uses the orchestrator engine instead of the legacy chat_loop.
        """
        if task_id in self.active_tasks:
            if not self.active_tasks[task_id].done():
                logger.warning(f"Task {task_id} is already running. Ignoring start request.")
                return

        # Create background task
        coro = self._run_orchestrated_loop(
            task_id,
            model_router,
            model_identifier,
            messages,
            session_context,
            max_steps,
            think,
            display_model,
            token_budget
        )

        task = asyncio.create_task(coro)
        self.active_tasks[task_id] = task

        # Cleanup when done
        task.add_done_callback(lambda t: self._cleanup_task(task_id))

        logger.info(f"Started orchestrated background task for {task_id}")

    async def start_coder_task(
        self,
        task_id: str,
        model_router: ModelRouter,
        model_identifier: str,
        messages: List[Dict[str, str]],
        session_context: SessionContext,
        max_steps: int = 100,
        think: Union[bool, str] = False,
        display_model: str = None,
    ):
        """
        Start a background coder task (notebook-based coding).

        Uses the coder_loop which operates on a Jupyter notebook,
        executing cells iteratively.
        """
        if task_id in self.active_tasks:
            if not self.active_tasks[task_id].done():
                logger.warning(f"Task {task_id} is already running. Ignoring start request.")
                return

        # Create background task
        coro = self._run_coder_loop(
            task_id,
            model_router,
            model_identifier,
            messages,
            session_context,
            max_steps,
            think,
            display_model,
        )

        task = asyncio.create_task(coro)
        self.active_tasks[task_id] = task

        # Cleanup when done
        task.add_done_callback(lambda t: self._cleanup_task(task_id))

        logger.info(f"Started coder background task for {task_id}")

    async def _run_coder_loop(
        self,
        task_id: str,
        model_router: ModelRouter,
        model_identifier: str,
        messages: List[Dict[str, str]],
        session_context: SessionContext,
        max_steps: int = 100,
        think: Union[bool, str] = False,
        display_model: str = None,
    ):
        """
        Drives the coder_loop generator and broadcasts events.
        """
        # Init State
        self.task_states[task_id] = {
            "content": "",
            "thinking": "",
            "tool_calls": [],
            "current_agent_role": "coder",
            "current_model": None,
            "tokens": {"input": 0, "output": 0, "total": 0},
            "mode": "coder",
            "notebook_name": None,
            "cancelled": False,
            "step_counter": 0,  # Track step numbers for consistent display
            "step_count": 0,
            "error_count": 0,
        }

        history_log = []
        pending_tool_calls = []  # Track tool calls for current assistant turn
        persisted_count = 0  # Track incremental persistence
        _start_time = datetime.utcnow()

        try:
            # Use V2 (orchestrator-style) or V1 (ReAct-style) based on flag
            if USE_CODER_V2:
                coder_loop = _get_coder_loop_v2()
                logger.info(f"Using Coder V2 (orchestrator-style) for task {task_id}")
            else:
                coder_loop = _get_coder_loop()
                logger.info(f"Using Coder V1 (ReAct-style) for task {task_id}")

            async for event in coder_loop(
                model_router=model_router,
                model_identifier=model_identifier,
                messages=messages,
                session_context=session_context,
                max_steps=max_steps,
                think=think,
                display_model=display_model,
                history_log=history_log,  # V2 uses this for history
            ):
                # Update State based on event type
                etype = event.get("type")
                state = self.task_states[task_id]

                if etype == "chunk":
                    state["content"] += event.get("content", "")
                elif etype == "thinking_chunk":
                    state["thinking"] += event.get("content", "")
                elif etype == "tool_call":
                    tool_info = {
                        "name": event.get("tool_name"),
                        "arguments": event.get("arguments")
                    }
                    state["tool_calls"].append(tool_info)
                    # V1 only: track pending tool calls for history pairing
                    if not USE_CODER_V2:
                        pending_tool_calls.append(tool_info)

                elif etype == "tool_result":
                    # V2 manages its own history via step_complete events.
                    # Only V1 needs per-tool-call history entries.
                    if USE_CODER_V2:
                        pass  # Just broadcast, V2 handles its own history
                    else:
                        # V1: save assistant message with tool calls and tool result to history
                        tool_name = event.get("tool_name")
                        tool_result = event.get("result", "")

                        # Find matching tool call
                        matching_tool = None
                        for tc in pending_tool_calls:
                            if tc["name"] == tool_name:
                                matching_tool = tc
                                break

                        if matching_tool:
                            # Increment step counter
                            state["step_counter"] = state.get("step_counter", 0) + 1
                            step_id = f"coder_step_{state['step_counter']}"

                            # Save assistant message with this tool call
                            history_log.append({
                                "role": "assistant",
                                "content": state["content"],
                                "thinking": state.get("thinking", ""),
                                "tool_calls": [{
                                    "function": {
                                        "name": matching_tool["name"],
                                        "arguments": matching_tool["arguments"]
                                    }
                                }],
                                "metadata_blob": {
                                    "mode": "coder",
                                    "phase": "executing",
                                    "tool_name": tool_name,
                                    "step_id": step_id,
                                    "notebook_name": state.get("notebook_name"),
                                    "agent_role": "coder",
                                    "agent_name": "Coder Agent",
                                    "model_name": state.get("current_model"),
                                }
                            })

                            # Save tool result
                            history_log.append({
                                "role": "tool",
                                "content": tool_result,
                                "metadata_blob": {
                                    "mode": "coder",
                                    "tool_name": tool_name,
                                }
                            })

                            # Remove from pending
                            pending_tool_calls.remove(matching_tool)

                            # Flush to DB after each tool completion
                            persisted_count = self._persist_incremental(
                                task_id, history_log, session_context, persisted_count
                            )

                            # Reset content for next turn
                            state["content"] = ""
                            state["thinking"] = ""

                elif etype == "session_info":
                    if "session_info" in event:
                        state["current_model"] = event["session_info"].get("model")
                        state["notebook_name"] = event["session_info"].get("notebook_name")
                elif etype == "notebook_loaded":
                    state["notebook_name"] = event.get("notebook_name")
                elif etype == "token_usage":
                    usage = event.get("token_usage", {})
                    state["tokens"]["input"] += usage.get("input", 0)
                    state["tokens"]["output"] += usage.get("output", 0)
                    state["tokens"]["total"] += usage.get("total", 0)

                # V2-specific events
                # Note: algorithm_generated event is NOT saved to history here
                # because coder_v2.py already saves it directly to history_log
                elif etype == "algorithm_generated":
                    # Just pass through to frontend - history is saved in coder_v2.py
                    pass
                elif etype == "analysis_complete":
                    state["classification"] = event.get("classification")
                elif etype == "step_started":
                    state["current_step"] = event.get("step_number")
                    state["step_counter"] = event.get("step_number", state.get("step_counter", 0))
                elif etype == "step_complete":
                    state["step_count"] = state.get("step_count", 0) + 1
                    step_num = event.get("step_number")
                    cell_id = event.get("cell_id")
                    score = event.get("score", 0)
                    # Save step completion to history
                    history_log.append({
                        "role": "assistant",
                        "content": f"Step {step_num} completed (score: {score})",
                        "metadata_blob": {
                            "mode": "coder_v2",
                            "phase": "executing",
                            "step_number": step_num,
                            "cell_id": cell_id,
                            "score": score,
                            "agent_role": "coder",
                            "agent_name": "Coder Agent",
                        }
                    })
                    # Flush after each step completion
                    persisted_count = self._persist_incremental(
                        task_id, history_log, session_context, persisted_count
                    )
                elif etype == "cell_evaluation":
                    # Just pass through to frontend
                    pass
                elif etype == "step_retry":
                    # Just pass through to frontend
                    pass
                elif etype == "documentation_created":
                    exports = event.get("exports", {})
                    for fmt, path in exports.items():
                        history_log.append({
                            "role": "assistant",
                            "content": f"Exported notebook to {fmt}: {path}",
                            "metadata_blob": {
                                "mode": "coder_v2",
                                "phase": "documentation",
                                "export_format": fmt,
                                "export_path": path,
                            }
                        })
                    # Flush documentation entries
                    persisted_count = self._persist_incremental(
                        task_id, history_log, session_context, persisted_count
                    )

                elif etype == "complete":
                    # Add final assistant message to history for persistence
                    if state["content"]:
                        history_log.append({
                            "role": "assistant",
                            "content": state["content"],
                            "thinking": state.get("thinking", ""),
                            "metadata_blob": {
                                "mode": "coder",
                                "phase": "synthesizing",
                                "notebook_name": state.get("notebook_name"),
                                "agent_role": "coder",
                                "agent_name": "Coder Agent",
                                "model_name": state.get("current_model"),
                            }
                        })

                # Broadcast event
                await self.broadcast_event(task_id, event)

        except asyncio.CancelledError:
            logger.info(f"Coder task {task_id} cancelled by user, saving partial history...")
            await self.broadcast_event(task_id, {"type": "cancelled", "reason": "Task stopped by user"})
            if task_id in self.task_states:
                self.task_states[task_id]["error_count"] = self.task_states[task_id].get("error_count", 0) + 1
        except Exception as e:
            logger.error(f"Error in coder task {task_id}: {e}", exc_info=True)
            await self.broadcast_event(task_id, {"type": "error", "message": str(e)})
            if task_id in self.task_states:
                self.task_states[task_id]["error_count"] = self.task_states[task_id].get("error_count", 0) + 1
        finally:
            # Flush any remaining entries not yet persisted + update tokens
            remaining = history_log[persisted_count:]
            accumulated_tokens = self.task_states.get(task_id, {}).get("tokens", {})
            if remaining or accumulated_tokens:
                self._persist_history(task_id, remaining, session_context, accumulated_tokens)
            logger.info(f"Persisted {len(history_log)} total history entries for coder task {task_id} ({persisted_count} incremental + {len(remaining)} final)")
            self._write_telemetry_snapshot(task_id, session_context, accumulated_tokens, _start_time)

    async def _run_orchestrated_loop(
        self,
        task_id: str,
        model_router: ModelRouter,
        model_identifier: str,
        messages: List[Dict[str, str]],
        session_context: SessionContext,
        max_steps: int = 10,
        think: Union[bool, str] = False,
        display_model: str = None,
        token_budget: Optional[int] = None
    ):
        """
        Drives the orchestrated_chat generator and broadcasts events.
        """
        # Init State
        self.task_states[task_id] = {
            "content": "",
            "thinking": "",
            "tool_calls": [],
            "current_agent_role": None,
            "current_model": None,
            "tokens": {"input": 0, "output": 0, "total": 0},
            "orchestrated": True,
            "phase": "starting",
            "plan": None,
            "collaboration_ctx": CollaborationContext(),  # Initialize context
            "cancelled": False,  # Cancellation flag
            "step_count": 0,
            "error_count": 0,
        }

        history_log = []  # Moved outside try to be accessible in finally
        persisted_count = 0  # Track how many entries have been flushed to DB
        _start_time = datetime.utcnow()
        try:
            orchestrated_chat = _get_orchestrated_chat()
            collaboration_ctx = self.task_states[task_id]["collaboration_ctx"]

            async for event in orchestrated_chat(
                model_router=model_router,
                model_identifier=model_identifier,
                messages=messages,
                session_context=session_context,
                max_steps=max_steps,
                think=think,
                display_model=display_model,
                history_log=history_log,
                token_budget=token_budget,
                collaboration_context=collaboration_ctx,  # Pass context
            ):
                # Update State based on event type
                etype = event.get("type")
                state = self.task_states[task_id]

                if etype == "chunk":
                    state["content"] += event.get("content", "")
                elif etype == "orchestrator_thinking":
                    state["thinking"] += event.get("content", "")
                    state["phase"] = event.get("phase", state["phase"])
                elif etype == "orchestrator_thinking_start":
                    state["phase"] = event.get("phase", "thinking")
                    # Flush when transitioning to planning (analysis entries are done)
                    if event.get("phase") == "planning":
                        persisted_count = self._persist_incremental(
                            task_id, history_log, session_context, persisted_count
                        )
                elif etype == "plan_generated":
                    state["plan"] = event.get("plan")
                    state["phase"] = "executing"
                    # Flush plan entry
                    persisted_count = self._persist_incremental(
                        task_id, history_log, session_context, persisted_count
                    )
                elif etype == "step_start":
                    # Track current step
                    state["current_step"] = event.get("step_id")
                    state["current_agent_role"] = event.get("agent_role")
                elif etype == "step_complete":
                    state["step_count"] = state.get("step_count", 0) + 1
                    # Flush step + tool result entries
                    persisted_count = self._persist_incremental(
                        task_id, history_log, session_context, persisted_count
                    )
                elif etype == "supervisor_evaluation":
                    # Flush supervisor evaluation entry
                    persisted_count = self._persist_incremental(
                        task_id, history_log, session_context, persisted_count
                    )
                elif etype == "tool_call":
                    state["tool_calls"].append(event.get("tool_call", event))
                elif etype == "session_info":
                    if "session_info" in event:
                        state["current_agent_role"] = event["session_info"].get("agent_role")
                        state["current_model"] = event["session_info"].get("model")
                elif etype == "token_usage":
                    usage = event.get("token_usage", {})
                    state["tokens"]["input"] += usage.get("input", 0)
                    state["tokens"]["output"] += usage.get("output", 0)
                    state["tokens"]["total"] += usage.get("total", 0)
                elif etype == "direct_answer_mode":
                    state["phase"] = "direct_answer"
                elif etype == "complete":
                    state["phase"] = "complete"

                # Broadcast event
                await self.broadcast_event(task_id, event)

        except asyncio.CancelledError:
            # User pressed STOP - broadcast cancelled event but still persist
            logger.info(f"Task {task_id} cancelled by user, saving partial history...")
            await self.broadcast_event(task_id, {"type": "cancelled", "reason": "Task stopped by user"})
            if task_id in self.task_states:
                self.task_states[task_id]["error_count"] = self.task_states[task_id].get("error_count", 0) + 1
            # Don't re-raise - let finally handle persistence
        except Exception as e:
            logger.error(f"Error in orchestrated task {task_id}: {e}", exc_info=True)
            await self.broadcast_event(task_id, {"type": "error", "message": str(e)})
            if task_id in self.task_states:
                self.task_states[task_id]["error_count"] = self.task_states[task_id].get("error_count", 0) + 1
        finally:
            # Flush any remaining entries not yet persisted + update tokens
            remaining = history_log[persisted_count:]
            accumulated_tokens = self.task_states.get(task_id, {}).get("tokens", {})
            if remaining or accumulated_tokens:
                self._persist_history(task_id, remaining, session_context, accumulated_tokens)
            logger.info(f"Persisted {len(history_log)} total history entries for task {task_id} ({persisted_count} incremental + {len(remaining)} final)")
            self._write_telemetry_snapshot(task_id, session_context, accumulated_tokens, _start_time)

    async def broadcast_event(self, task_id: str, event: Dict[str, Any]):
        """
        Send event to all active subscribers for this task.
        Applies content filtering before broadcasting.
        """
        if task_id not in self.subscribers:
            return

        # Filter sensitive content (API keys, etc.) before broadcasting
        event = filter_event(event)

        json_event = json.dumps(event)
        
        # Copy list to iterate safely
        queues = self.subscribers[task_id][:]
        for q in queues:
            try:
                await q.put(json_event)
            except Exception as e:
                logger.error(f"Failed to put to queue: {e}")

    async def subscribe(self, task_id: str) -> AsyncGenerator[str, None]:
        """
        Yields SSE formatted events for a task.
        """
        queue = asyncio.Queue()
        
        if task_id not in self.subscribers:
            self.subscribers[task_id] = []
        self.subscribers[task_id].append(queue)
        
        # Send Sync Event if task is active
        if task_id in self.task_states:
            state = self.task_states[task_id]
            # Construct sync event
            sync_event = {
                "type": "sync_state",
                "content": state["content"],
                "thinking": state["thinking"],
            }
            if state.get("current_agent_role"):
                sync_event["agent_role"] = state["current_agent_role"]
            if state.get("current_model"):
                sync_event["model"] = state["current_model"]
            # Include orchestrator state for proper frontend handling
            if state.get("orchestrated"):
                sync_event["orchestrated"] = True
                sync_event["phase"] = state.get("phase")
                if state.get("current_step"):
                    sync_event["step_id"] = state["current_step"]
            if state.get("mode") == "coder":
                sync_event["mode"] = "coder"

            yield json.dumps(sync_event)
        
        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            if task_id in self.subscribers:
                if queue in self.subscribers[task_id]:
                    self.subscribers[task_id].remove(queue)
                if not self.subscribers[task_id]:
                    del self.subscribers[task_id]

    def _cleanup_task(self, task_id):
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        if task_id in self.task_states:
            del self.task_states[task_id]
        logger.info(f"Background task {task_id} finished/cleaned up.")

    def _write_telemetry_snapshot(self, task_id, session_context, accumulated_tokens, start_time):
        """
        Write a TelemetrySnapshot record when a task turn finishes.
        Called from finally blocks in _run_orchestrated_loop and _run_coder_loop.
        Never raises — telemetry must not break the main flow.
        """
        try:
            from backend.database import engine
            from backend.models.telemetry import TelemetrySnapshot
            from sqlmodel import Session

            state = self.task_states.get(task_id, {})

            # Count tool calls by name
            tool_calls_list = state.get("tool_calls", [])
            tool_call_counts: Dict[str, int] = {}
            for tc in tool_calls_list:
                name = (
                    tc.get("name")
                    or tc.get("tool_name")
                    or (tc.get("tool_call") or {}).get("name")
                    or "unknown"
                )
                tool_call_counts[name] = tool_call_counts.get(name, 0) + 1

            duration = (datetime.utcnow() - start_time).total_seconds() if start_time else None
            tokens = accumulated_tokens or {}

            snap = TelemetrySnapshot(
                task_id=task_id,
                user_id=session_context.user_id,
                created_at=datetime.utcnow(),
                model_identifier=session_context.model_identifier or "unknown",
                mode=session_context.mode or "agentic",
                input_tokens=tokens.get("input", 0),
                output_tokens=tokens.get("output", 0),
                total_tokens=tokens.get("total", 0),
                tool_calls=tool_call_counts,
                duration_seconds=duration,
                step_count=state.get("step_count", 0),
                error_count=state.get("error_count", 0),
            )

            with Session(engine) as db_session:
                db_session.add(snap)
                db_session.commit()

            logger.info(
                f"[TELEMETRY] Snapshot written for task {task_id}: "
                f"{snap.total_tokens} tokens, {snap.step_count} steps, "
                f"{len(tool_call_counts)} distinct tools, {duration:.1f}s"
                if duration else
                f"[TELEMETRY] Snapshot written for task {task_id}: "
                f"{snap.total_tokens} tokens, {snap.step_count} steps"
            )
        except Exception as e:
            logger.warning(f"[TELEMETRY] Failed to write snapshot for {task_id}: {e}")

    def _persist_history(self, task_id, history_log, session_context, accumulated_tokens=None):
        # Need to import DB stuff inside method to avoid circular imports or context issues
        from sqlmodel import Session, select
        from backend.database import engine
        from backend.models.task import Message, Task

        # Replicates logic from tasks.py persistence
        if not history_log and not accumulated_tokens:
            return

        msg_count = len(history_log)
        tokens_updated = False

        try:
            with Session(engine) as session:
                # Get last sequence
                last_msg = session.exec(select(Message).where(Message.task_id == task_id).order_by(Message.sequence.desc())).first()
                next_seq = (last_msg.sequence + 1) if last_msg else 1

                resolved_model = session_context.agent_roles.get("_resolved_model")
                resolved_role = session_context.agent_roles.get("_resolved_role")

                for msg_data in history_log:
                    # Fix: Prefer existing metadata_blob if present to preserve phase/plan info
                    # Otherwise construct basic metadata from msg_data fields
                    metadata = msg_data.get("metadata_blob", {}).copy()
                    
                    # Ensure model/role are set (if not already in blob)
                    if "model" not in metadata:
                        metadata["model"] = resolved_model
                    if "agent_role" not in metadata:
                        metadata["agent_role"] = resolved_role
                        
                    # Merge specific fields from msg_data if they exist and aren't in metadata yet
                    if "thinking" in msg_data and "thinking" not in metadata: 
                        metadata["thinking"] = msg_data["thinking"]
                    if "tool_calls" in msg_data and "tool_calls" not in metadata: 
                        metadata["tool_calls"] = msg_data["tool_calls"]
                    if "name" in msg_data and "tool_name" not in metadata: 
                        metadata["tool_name"] = msg_data["name"]

                    new_msg = Message(
                        task_id=task_id,
                        role=msg_data["role"],
                        content=msg_data.get("content", "") or "",
                        sequence=next_seq,
                        metadata_blob=metadata
                    )
                    session.add(new_msg)
                    next_seq += 1

                # Update Task token counts (accumulate, don't replace)
                if accumulated_tokens:
                    task = session.get(Task, task_id)
                    if task:
                        task.input_tokens = (task.input_tokens or 0) + accumulated_tokens.get("input", 0)
                        task.output_tokens = (task.output_tokens or 0) + accumulated_tokens.get("output", 0)
                        task.total_tokens = (task.total_tokens or 0) + accumulated_tokens.get("total", 0)
                        session.add(task)
                        tokens_updated = True

                session.commit()

            # Log AFTER session is closed to avoid database lock conflicts
            logger.info(f"[BG_PERSIST] Saved {msg_count} messages for {task_id}")
            if tokens_updated:
                logger.info(f"[BG_PERSIST] Updated task tokens: +{accumulated_tokens}")
        except Exception as e:
            logger.error(f"[BG_PERSIST] Failed to save history: {e}")

    def _persist_incremental(self, task_id, history_log, session_context, start_idx):
        """Persist new history entries since last flush. Returns new start_idx."""
        if start_idx >= len(history_log):
            return start_idx

        from sqlmodel import Session, select
        from backend.database import engine
        from backend.models.task import Message

        new_entries = history_log[start_idx:]
        try:
            with Session(engine) as session:
                last_msg = session.exec(
                    select(Message).where(Message.task_id == task_id)
                    .order_by(Message.sequence.desc())
                ).first()
                next_seq = (last_msg.sequence + 1) if last_msg else 1

                resolved_model = session_context.agent_roles.get("_resolved_model")
                resolved_role = session_context.agent_roles.get("_resolved_role")

                for msg_data in new_entries:
                    metadata = msg_data.get("metadata_blob", {}).copy()
                    if "model" not in metadata:
                        metadata["model"] = resolved_model
                    if "agent_role" not in metadata:
                        metadata["agent_role"] = resolved_role
                    if "thinking" in msg_data and "thinking" not in metadata:
                        metadata["thinking"] = msg_data["thinking"]
                    if "tool_calls" in msg_data and "tool_calls" not in metadata:
                        metadata["tool_calls"] = msg_data["tool_calls"]
                    if "name" in msg_data and "tool_name" not in metadata:
                        metadata["tool_name"] = msg_data["name"]

                    new_msg = Message(
                        task_id=task_id,
                        role=msg_data["role"],
                        content=msg_data.get("content", "") or "",
                        sequence=next_seq,
                        metadata_blob=metadata
                    )
                    session.add(new_msg)
                    next_seq += 1

                session.commit()

            logger.debug(f"[INCR_PERSIST] Flushed {len(new_entries)} entries for {task_id} (idx {start_idx}→{len(history_log)})")
        except Exception as e:
            logger.error(f"[INCR_PERSIST] Failed to flush history: {e}")
            # Don't update start_idx on failure so they'll be retried
            return start_idx

        return len(history_log)

    def set_collaboration_response(self, task_id: str, response: CollaborationResponse):
        """
        Inject a user response into a paused task to resume execution.
        """
        logger.info(f"[COLLAB] set_collaboration_response called for task {task_id}")
        logger.info(f"[COLLAB] Response: action={response.action}, tool={response.tool_name}, response={str(response.response)[:100]}")

        if task_id not in self.task_states:
             logger.warning(f"[COLLAB] Task {task_id} not found in task_states. Available: {list(self.task_states.keys())}")
             return False

        state = self.task_states[task_id]
        logger.info(f"[COLLAB] Task state keys: {list(state.keys())}")

        if "collaboration_ctx" not in state:
             logger.warning(f"[COLLAB] Task {task_id} does not have collaboration_ctx")
             return False

        ctx: CollaborationContext = state["collaboration_ctx"]
        logger.info(f"[COLLAB] Before set: response_ready.is_set() = {ctx.response_ready.is_set()}")

        # Set the response and signal the waiting task
        ctx.pending_response = response
        ctx.response_ready.set()

        logger.info(f"[COLLAB] After set: response_ready.is_set() = {ctx.response_ready.is_set()}")
        logger.info(f"[COLLAB] Resumed task {task_id} with collaboration response: {response.action}")
        return True

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task. Sets the cancelled flag and wakes up any waiting coroutines.

        Returns True if task was found and cancelled, False otherwise.
        """
        if task_id not in self.task_states:
            logger.warning(f"Task {task_id} not found when trying to cancel")
            return False

        state = self.task_states[task_id]
        state["cancelled"] = True

        # If task is waiting on collaboration, wake it up so it can check cancellation
        if "collaboration_ctx" in state:
            ctx: CollaborationContext = state["collaboration_ctx"]
            # Create a cancellation response
            cancel_response = CollaborationResponse(
                response="Task cancelled by user",
                tool_name="cancel",
                task_id=task_id,
                action="abort"
            )
            ctx.pending_response = cancel_response
            ctx.response_ready.set()

        # Also cancel the asyncio task if it exists
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if not task.done():
                task.cancel()

        logger.info(f"Cancelled task {task_id}")
        return True

    def is_cancelled(self, task_id: str) -> bool:
        """
        Check if a task has been cancelled.

        Returns True if task is cancelled, False otherwise.
        """
        if task_id not in self.task_states:
            return False
        return self.task_states[task_id].get("cancelled", False)

task_manager = TaskManager()
