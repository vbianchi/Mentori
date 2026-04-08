# backend/models/telemetry.py
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional, Dict


class TelemetrySnapshot(SQLModel, table=True):
    """
    One row per completed task turn.
    Populated when a task finishes (success, error, or cancellation).
    Kept even if the parent Task is deleted, for long-term analytics.
    """

    __tablename__ = "telemetry_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Task identity (denormalised — task may be deleted)
    task_id: str = Field(index=True)
    user_id: str = Field(index=True)

    # Timestamps / duration
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = Field(default=None)

    # Model + mode
    model_identifier: str = Field(default="unknown")
    mode: str = Field(default="agentic")  # "chat" | "agentic" | "coder"

    # Token counts for this specific turn
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)

    # Tool usage: {tool_name: call_count}
    tool_calls: Dict = Field(default={}, sa_column=Column(JSON))

    # Quality / error tracking
    error_count: int = Field(default=0)
    step_count: int = Field(default=0)
