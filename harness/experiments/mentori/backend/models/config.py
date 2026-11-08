# backend/models/config.py
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional, Dict

class ModelConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_identifier: str  # e.g., "ollama::llama3:70b"
    provider: str          # "ollama", "gemini", "openai", "claude"
    default_settings: Dict = Field(default={}, sa_column=Column(JSON))
    enabled: bool = True
    supports_thinking: bool = Field(default=False)
    # thinking_type: None (no thinking), "boolean" (true/false), or "level" (low/medium/high for gpt-oss)
    thinking_type: Optional[str] = Field(default=None)
    admin_notes: str = ""

class UserModelPreference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    model_identifier: str
    custom_settings: Dict = Field(default={}, sa_column=Column(JSON))
