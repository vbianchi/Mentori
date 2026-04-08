# backend/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from backend.database import get_session
from backend.models.user import User
from backend.models.system_settings import SystemSettings
from backend.auth import get_current_user
from pydantic import BaseModel
from backend.models.config import ModelConfig

router = APIRouter(prefix="/users", tags=["users"])

# --- Schemas ---
class UserRead(BaseModel):
    id: str
    email: str
    role: str
    profile_image: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    preferences: str | None = None
    settings: dict

class UserUpdate(BaseModel):
    settings: dict | None = None
    profile_image: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    preferences: str | None = None

class ModelRead(BaseModel):
    id: int
    model_identifier: str
    provider: str
    enabled: bool
    supports_thinking: bool = False
    thinking_type: str | None = None

# --- Helper Functions ---
def get_system_setting(session: Session, key: str, default=None):
    """Get a system setting value by key."""
    setting = session.exec(
        select(SystemSettings).where(SystemSettings.key == key)
    ).first()
    return setting.value if setting else default


# --- Routes ---
@router.get("/models", response_model=List[ModelRead])
def list_available_models(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List models available to the user based on admin policy.

    Policy options:
        - "any": All enabled models
        - "preloaded_only": Only models in the preload list
        - "admin_approved": Same as "any" (enabled models)
    """
    policy = get_system_setting(session, "user_model_policy", "any")

    if policy == "preloaded_only":
        # Get preloaded models list
        preload_config = get_system_setting(session, "preloaded_models", {"models": []})

        # Handle both list and dict formats
        if isinstance(preload_config, list):
            preloaded_models = preload_config
        elif isinstance(preload_config, dict):
            preloaded_models = preload_config.get("models", [])
        else:
            preloaded_models = []

        if not preloaded_models:
            # If no preloaded models configured, return all enabled (fallback)
            return session.exec(select(ModelConfig).where(ModelConfig.enabled == True)).all()

        # Filter to only preloaded models that are also enabled
        return session.exec(
            select(ModelConfig)
            .where(ModelConfig.enabled == True)
            .where(ModelConfig.model_identifier.in_(preloaded_models))
        ).all()

    # "any" or "admin_approved" - return all enabled models
    return session.exec(select(ModelConfig).where(ModelConfig.enabled == True)).all()

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me/settings", response_model=UserRead)
def update_user_settings(
    settings_in: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Merge existing settings with new ones
    if settings_in.settings:
        current_user.settings = {**current_user.settings, **settings_in.settings}
    if settings_in.profile_image is not None:
        current_user.profile_image = settings_in.profile_image
    if settings_in.first_name is not None:
        current_user.first_name = settings_in.first_name
    if settings_in.last_name is not None:
        current_user.last_name = settings_in.last_name
    if settings_in.preferences is not None:
        current_user.preferences = settings_in.preferences
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user
