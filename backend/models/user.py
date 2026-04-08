# backend/models/user.py
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional, Dict
import uuid

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = "user"  # "user" or "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_image: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferences: Optional[str] = None  # User context/preferences for AI personalization
    settings: Dict = Field(default={}, sa_column=Column(JSON))
