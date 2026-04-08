# backend/models/system_settings.py
"""
System-wide settings for admin configuration.

Stores key-value pairs for:
- admin_agent_roles: Recommended models per agent role
- preloaded_models: List of models to keep warm in Ollama
- user_model_policy: Restriction policy for user model selection
"""
from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict, Any
from datetime import datetime


class SystemSettings(SQLModel, table=True):
    """
    Key-value store for system-wide admin configuration.

    Keys:
        - admin_agent_roles: Dict[str, str] mapping role -> model_identifier
        - preloaded_models: List[str] of model identifiers to keep warm
        - user_model_policy: str ("any", "preloaded_only", "admin_approved")
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # User ID of admin who last updated
