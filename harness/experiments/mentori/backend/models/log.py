from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class TaskLog(SQLModel, table=True):
    __tablename__ = "task_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str
    message: str
    metadata_blob: Optional[str] = None # JSON string for extra fields
