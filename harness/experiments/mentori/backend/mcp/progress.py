"""
Tool Progress Emitter

Allows MCP tools (running on the tool server) to emit real-time progress
events that flow through the backend WebSocket to the frontend StepCard.

Architecture:
  Tool Server → HTTP POST /tasks/{task_id}/progress → Backend broadcasts
  via task_manager → Frontend Dashboard receives via SSE/WebSocket.

Progress is nice-to-have — if the POST fails, the tool continues normally.
"""

import os

import httpx

from backend.agents.session_context import get_logger

logger = get_logger(__name__)

# Resolve backend URL: tool-server needs to reach the backend.
# In Docker: http://backend:8766   Locally: http://localhost:8766
_BACKEND_URL = os.getenv("BACKEND_INTERNAL_URL", "http://localhost:8766")


async def emit_progress(
    task_id: str,
    tool_name: str,
    message: str,
    phase: str = "",
    step: int = 0,
    total_steps: int = 0,
) -> None:
    """
    Fire-and-forget progress event to the backend.

    Args:
        task_id: The task ID (UUID) this tool call belongs to.
        tool_name: Name of the running tool (e.g. "cross_document_analysis").
        message: Human-readable progress message.
        phase: Optional phase label (e.g. "extraction", "synthesis").
        step: Current step number (1-based).
        total_steps: Total expected steps (0 if unknown).
    """
    if not task_id:
        return

    url = f"{_BACKEND_URL}/tasks/{task_id}/progress"
    payload = {
        "tool_name": tool_name,
        "message": message,
        "phase": phase,
        "step": step,
        "total_steps": total_steps,
    }

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.debug(f"[PROGRESS] POST returned {resp.status_code}")
    except Exception:
        # Fire-and-forget: never let progress reporting break the tool
        pass
