# backend/models/task.py
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional, Dict

class Task(SQLModel, table=True):
    id: str = Field(primary_key=True)  # UUID
    user_id: str = Field(foreign_key="user.id")
    title: str = ""
    mode: str = "chat"  # "chat" or "agentic"
    model_identifier: str  # Active model for this task
    workspace_path: str  # /workspace/{user_id}/{task_id}/
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata_blob: Dict = Field(default={}, sa_column=Column(JSON))
    display_id: Optional[str] = Field(default=None) # Random alphanumeric ID for UI (e.g., "a7k9m2p4")
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    sort_order: int = Field(default=0)  # User-defined sort order (lower = higher in list)

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id")
    role: str  # "user", "assistant", "system", "tool"
    content: str
    metadata_blob: Dict = Field(default={}, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sequence: int  # Order within task
