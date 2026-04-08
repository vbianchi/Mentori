# backend/models/audit.py
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional, Dict

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id")
    user_id: str = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str  # "tool_call", "thinking", "code_execution", etc.
    details: Dict = Field(default={}, sa_column=Column(JSON))
