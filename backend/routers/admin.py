# backend/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from backend.database import get_session
from backend.models.user import User
from backend.models.task import Task, Message
from backend.models.config import ModelConfig, UserModelPreference
from backend.models.system_settings import SystemSettings
from backend.auth import get_current_user, get_current_admin_user, get_password_hash
from backend.agents.model_router import ModelRouter
from backend.agents.models.ollama import OllamaClient
from backend.agents.session_context import AGENT_ROLES
from backend.config import settings
from pydantic import BaseModel
import json
import os
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])
model_router = ModelRouter()

# --- Schemas ---
class UserRead(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime
    
class UserCreateAdmin(BaseModel):
    email: str
    password: str
    role: str = "user"

# --- Models Routes ---

@router.get("/models", response_model=List[Dict[str, str]])
async def list_available_models(
    prefix_filter: str = None,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Lists all models available from connected providers.
    Does NOT strictly read from DB, but fetches live from providers.
    """
    # Extract Gemini Key from User Settings if available
    api_keys = current_user.settings.get("api_keys", {})
    gemini_key = api_keys.get("gemini") or api_keys.get("GEMINI_API_KEY")
    
    models = await model_router.list_all_models(api_key=gemini_key)
    if prefix_filter:
        models = [m for m in models if m["id"].startswith(prefix_filter)]
    return models

@router.post("/models/sync")
async def sync_models_to_db(
    force: bool = False,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Fetches live models and updates the ModelConfig table.
    By default only probes NEW models (not in DB yet) to keep sync fast.
    Pass ?force=true to re-probe all models (slower, re-checks thinking capabilities).
    """
    api_keys = current_user.settings.get("api_keys", {})
    gemini_key = api_keys.get("gemini") or api_keys.get("GEMINI_API_KEY")

    live_models = await model_router.list_all_models(api_key=gemini_key)

    added_count = 0
    updated_count = 0
    for m in live_models:
        existing = session.exec(
            select(ModelConfig).where(ModelConfig.model_identifier == m["id"])
        ).first()

        if not existing:
            # Always probe new models to detect thinking support
            capabilities = await model_router.probe_model_capabilities(m["id"])
            new_config = ModelConfig(
                model_identifier=m["id"],
                provider=m["provider"],
                enabled=True,
                supports_thinking=capabilities.get("thinking", False),
                thinking_type=capabilities.get("thinking_type")
            )
            session.add(new_config)
            added_count += 1
        elif force:
            # Only re-probe existing models when admin explicitly requests it
            capabilities = await model_router.probe_model_capabilities(m["id"])
            changed = False
            if capabilities.get("thinking") != existing.supports_thinking:
                existing.supports_thinking = capabilities.get("thinking", False)
                changed = True
            if capabilities.get("thinking_type") != existing.thinking_type:
                existing.thinking_type = capabilities.get("thinking_type")
                changed = True
            if changed:
                session.add(existing)
                updated_count += 1

    session.commit()
    return {"status": "synced", "added": added_count, "updated": updated_count, "total_live": len(live_models)}

@router.get("/models/config")
def get_model_configs(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all model configurations from DB."""
    return session.exec(select(ModelConfig)).all()

class ModelConfigUpdate(BaseModel):
    enabled: bool

@router.put("/models/{config_id}")
def update_model_config(
    config_id: int,
    config_in: ModelConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Enable or disable a specific model."""
    config = session.get(ModelConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
        
    config.enabled = config_in.enabled
    session.add(config)
    session.commit()
    session.refresh(config)
    return config

# --- User Management Routes ---

@router.get("/users", response_model=List[UserRead])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    return session.exec(select(User)).all()

@router.post("/users", response_model=UserRead)
def create_user(
    user_in: UserCreateAdmin,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    existing = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        password_hash=hashed_pw,
        role=user_in.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
        
    session.delete(user)
    session.commit()
    return {"status": "deleted"}

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    role: str, # passed as query param for simplicity or body
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
         raise HTTPException(status_code=400, detail="Cannot change your own role")
         
    user.role = role
    session.add(user)
    session.commit()
    return {"status": "updated", "role": role}

class UserUpdateAdmin(BaseModel):
    email: str | None = None
    role: str | None = None
    password: str | None = None

@router.put("/users/{user_id}")
def update_user_details(
    user_id: str,
    user_in: UserUpdateAdmin,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_in.email:
        # Check uniqueness if email changed
        if user_in.email != user.email:
             existing = session.exec(select(User).where(User.email == user_in.email)).first()
             if existing:
                 raise HTTPException(status_code=400, detail="Email already taken")
        user.email = user_in.email
        
    if user_in.role:
        if user.id == current_user.id and user_in.role != "admin":
             raise HTTPException(status_code=400, detail="Cannot downgrade your own admin account")
        user.role = user_in.role
        
    if user_in.password:
        user.password_hash = get_password_hash(user_in.password)
        
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# --- Data Export ---

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

@router.get("/export")
def export_database(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Exports core tables (Users, Tasks, Messages) to JSON.
    """
    data = {
        "users": [u.dict() for u in session.exec(select(User)).all()],
        "tasks": [t.dict() for t in session.exec(select(Task)).all()],
        "messages": [m.dict() for m in session.exec(select(Message)).all()],
        "model_configs": [mc.dict() for mc in session.exec(select(ModelConfig)).all()]
    }
    
    # Exclude password hashes
    for u in data["users"]:
        u.pop("password_hash", None)
        
    json_str = json.dumps(data, default=json_serial, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=mentori_export_{datetime.now().strftime('%Y%m%d')}.json"}
    )


# ============================================================
# Helper Functions for SystemSettings
# ============================================================

def get_system_setting(session: Session, key: str, default=None):
    """Get a system setting value by key."""
    setting = session.exec(
        select(SystemSettings).where(SystemSettings.key == key)
    ).first()
    return setting.value if setting else default


def set_system_setting(session: Session, key: str, value: Any, user_id: str):
    """Set a system setting value (creates or updates)."""
    setting = session.exec(
        select(SystemSettings).where(SystemSettings.key == key)
    ).first()

    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
        setting.updated_by = user_id
    else:
        setting = SystemSettings(key=key, value=value, updated_by=user_id)

    session.add(setting)
    session.commit()
    return setting


# ============================================================
# Ollama Management Routes
# ============================================================

ollama_client = OllamaClient()


@router.get("/ollama/status")
async def get_ollama_status(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get Ollama status including concurrency settings and loaded models.

    Concurrency settings are read from environment variables (read-only).
    Loaded models are fetched from Ollama /api/ps endpoint.
    """
    # Check Ollama health
    is_healthy = await ollama_client.check_health()

    # Get concurrency settings from environment
    concurrency = {
        "num_parallel": os.environ.get("OLLAMA_NUM_PARALLEL", "4 (default)"),
        "max_loaded_models": os.environ.get("OLLAMA_MAX_LOADED_MODELS", "3 (default)"),
        "keep_alive": os.environ.get("OLLAMA_KEEP_ALIVE", "5m (default)")
    }

    # Get loaded models
    loaded_models = []
    if is_healthy:
        loaded_models = await ollama_client.get_running_models()

    return {
        "ollama_available": is_healthy,
        "base_url": settings.OLLAMA_BASE_URL,
        "concurrency": concurrency,
        "loaded_models": loaded_models
    }


class PreloadRequest(BaseModel):
    models: List[str]
    keep_alive: str = "-1"


@router.post("/ollama/preload")
async def preload_models(
    request: PreloadRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Preload specified models into Ollama memory.

    Args:
        models: List of model identifiers (e.g., ["ollama::llama3.2:latest"])
        keep_alive: Duration to keep models loaded ("-1" = forever)
    """
    if not await ollama_client.check_health():
        raise HTTPException(status_code=503, detail="Ollama is not available")

    results = []
    for model_id in request.models:
        # Extract model name from "ollama::model" format
        if "::" in model_id:
            _, model_name = model_id.split("::", 1)
        else:
            model_name = model_id

        result = await ollama_client.preload_model(model_name, request.keep_alive)
        results.append(result)

    loaded = sum(1 for r in results if r["status"] == "loaded")
    failed = sum(1 for r in results if r["status"] == "failed")

    return {
        "results": results,
        "summary": {"loaded": loaded, "failed": failed}
    }


class UnloadRequest(BaseModel):
    model: str


@router.post("/ollama/unload")
async def unload_model(
    request: UnloadRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Unload a model from Ollama memory."""
    if not await ollama_client.check_health():
        raise HTTPException(status_code=503, detail="Ollama is not available")

    result = await ollama_client.unload_model(request.model)
    return result


@router.get("/ollama/preload-list")
def get_preload_list(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get the list of models configured for preloading and the user model policy."""
    preload_config = get_system_setting(session, "preloaded_models", {"models": []})
    policy = get_system_setting(session, "user_model_policy", "any")

    # Handle both list and dict formats for backwards compatibility
    if isinstance(preload_config, list):
        models = preload_config
    elif isinstance(preload_config, dict):
        models = preload_config.get("models", [])
    else:
        models = []

    return {
        "models": models,
        "policy": policy
    }


class PreloadListUpdate(BaseModel):
    models: List[str]
    policy: str = "any"  # "any", "preloaded_only", "admin_approved"


@router.put("/ollama/preload-list")
def update_preload_list(
    update: PreloadListUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update the preload configuration and user model policy.

    Args:
        models: List of model identifiers to keep preloaded
        policy: User model restriction policy
            - "any": Users can select any enabled model
            - "preloaded_only": Users can only select preloaded models
            - "admin_approved": Users can only select admin-enabled models
    """
    # Validate policy
    valid_policies = ["any", "preloaded_only", "admin_approved"]
    if update.policy not in valid_policies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy. Must be one of: {valid_policies}"
        )

    # Store as dict for future extensibility
    set_system_setting(session, "preloaded_models", {"models": update.models}, current_user.id)
    set_system_setting(session, "user_model_policy", update.policy, current_user.id)

    return {
        "status": "updated",
        "models": update.models,
        "policy": update.policy
    }


# ============================================================
# Admin Agent Roles Routes
# ============================================================

@router.get("/agent-roles")
def get_admin_agent_roles(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get admin-configured recommended agent roles.

    These are the models the admin recommends for each agent role.
    Admins can push these to all users.
    """
    admin_roles = get_system_setting(session, "admin_agent_roles", {})

    # Get the setting record for metadata
    setting = session.exec(
        select(SystemSettings).where(SystemSettings.key == "admin_agent_roles")
    ).first()

    return {
        "roles": admin_roles,
        "available_roles": AGENT_ROLES,
        "updated_at": setting.updated_at.isoformat() if setting else None,
        "updated_by": setting.updated_by if setting else None
    }


class AgentRolesUpdate(BaseModel):
    roles: Dict[str, Optional[str]]


@router.put("/agent-roles")
def update_admin_agent_roles(
    update: AgentRolesUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update admin-recommended agent roles configuration."""
    # Validate role names
    for role in update.roles.keys():
        if role not in AGENT_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role '{role}'. Valid roles: {AGENT_ROLES}"
            )

    set_system_setting(session, "admin_agent_roles", update.roles, current_user.id)

    return {
        "status": "updated",
        "roles": update.roles
    }


class PushRoleRequest(BaseModel):
    role: str
    model: str


@router.post("/agent-roles/push")
def push_role_to_all_users(
    request: PushRoleRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Push a specific role assignment to ALL users.

    This overwrites the specified role in each user's settings.agent_roles.
    Use with caution - affects all users in the system.
    """
    if request.role not in AGENT_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{request.role}'. Valid roles: {AGENT_ROLES}"
        )

    # Get all users
    users = session.exec(select(User)).all()
    affected_count = 0

    for user in users:
        # Ensure settings has agent_roles dict
        if not user.settings:
            user.settings = {}
        if "agent_roles" not in user.settings:
            user.settings["agent_roles"] = {}

        # Update the specific role
        user.settings["agent_roles"][request.role] = request.model

        # SQLModel needs explicit flag for JSON mutation
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "settings")

        session.add(user)
        affected_count += 1

    session.commit()

    # Also update admin_agent_roles
    admin_roles = get_system_setting(session, "admin_agent_roles", {})
    admin_roles[request.role] = request.model
    set_system_setting(session, "admin_agent_roles", admin_roles, current_user.id)

    return {
        "status": "pushed",
        "role": request.role,
        "model": request.model,
        "affected_users": affected_count
    }


class ClearRoleRequest(BaseModel):
    role: str


@router.post("/agent-roles/clear")
def clear_role_from_all_users(
    request: ClearRoleRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Clear a specific role from ALL users.

    This removes (sets to empty string) the specified role from each user's
    settings.agent_roles. Users will fall back to their "default" role.
    """
    if request.role not in AGENT_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{request.role}'. Valid roles: {AGENT_ROLES}"
        )

    # Get all users
    users = session.exec(select(User)).all()
    affected_count = 0

    for user in users:
        if user.settings and "agent_roles" in user.settings:
            if request.role in user.settings["agent_roles"]:
                user.settings["agent_roles"][request.role] = ""

                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(user, "settings")

                session.add(user)
                affected_count += 1

    session.commit()

    # Also clear from admin_agent_roles
    admin_roles = get_system_setting(session, "admin_agent_roles", {})
    if request.role in admin_roles:
        admin_roles[request.role] = ""
        set_system_setting(session, "admin_agent_roles", admin_roles, current_user.id)

    return {
        "status": "cleared",
        "role": request.role,
        "affected_users": affected_count
    }


# ============================================================
# Context Window Setting
# ============================================================

class ContextWindowUpdate(BaseModel):
    tokens: int


@router.get("/context-window")
async def get_context_window(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """Return the admin-configured minimum context window (tokens)."""
    from backend.agents.token_utils import DEFAULT_MIN_CONTEXT_WINDOW
    value = get_system_setting(session, "min_context_window", None)
    tokens = value.get("tokens", DEFAULT_MIN_CONTEXT_WINDOW) if value else DEFAULT_MIN_CONTEXT_WINDOW
    return {"tokens": tokens}


@router.put("/context-window")
async def update_context_window(
    update: ContextWindowUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """Update the minimum context window used for dynamic prompt budgeting."""
    if update.tokens < 4096:
        raise HTTPException(status_code=400, detail="Context window must be at least 4096 tokens.")
    set_system_setting(session, "min_context_window", {"tokens": update.tokens}, current_user.id)
    return {"status": "updated", "tokens": update.tokens}


# ─────────────────────────────────────────────────────────────────────────────
# Telemetry Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/telemetry/summary")
def get_telemetry_summary(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """
    High-level stats across all TelemetrySnapshot rows.
    Returns: total_tasks, total_tokens, avg_tokens_per_task, top_models, top_tools, error_rate, active_users.
    """
    from sqlalchemy import func as sqlfunc
    from backend.models.telemetry import TelemetrySnapshot

    rows = session.exec(select(TelemetrySnapshot)).all()
    if not rows:
        return {
            "total_tasks": 0,
            "total_tokens": 0,
            "avg_tokens_per_task": 0,
            "error_rate": 0.0,
            "active_users": 0,
            "top_models": [],
            "top_tools": [],
        }

    total_tasks = len(rows)
    total_tokens = sum(r.total_tokens for r in rows)
    avg_tokens = total_tokens // total_tasks if total_tasks else 0
    error_tasks = sum(1 for r in rows if r.error_count > 0)
    error_rate = round(error_tasks / total_tasks * 100, 1) if total_tasks else 0.0
    active_users = len({r.user_id for r in rows})

    # Top models by task count
    model_counts: dict = {}
    model_tokens: dict = {}
    for r in rows:
        m = r.model_identifier or "unknown"
        model_counts[m] = model_counts.get(m, 0) + 1
        model_tokens[m] = model_tokens.get(m, 0) + r.total_tokens
    top_models = sorted(
        [
            {
                "model_identifier": m,
                "task_count": model_counts[m],
                "total_tokens": model_tokens[m],
                "avg_tokens": model_tokens[m] // model_counts[m] if model_counts[m] else 0,
            }
            for m in model_counts
        ],
        key=lambda x: x["task_count"],
        reverse=True,
    )[:10]

    # Top tools by call count
    tool_counts: dict = {}
    tool_task_counts: dict = {}
    for r in rows:
        tc = r.tool_calls or {}
        for tool_name, count in tc.items():
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + count
            tool_task_counts[tool_name] = tool_task_counts.get(tool_name, 0) + 1
    top_tools = sorted(
        [
            {
                "tool_name": t,
                "call_count": tool_counts[t],
                "task_count": tool_task_counts[t],
            }
            for t in tool_counts
        ],
        key=lambda x: x["call_count"],
        reverse=True,
    )[:10]

    return {
        "total_tasks": total_tasks,
        "total_tokens": total_tokens,
        "avg_tokens_per_task": avg_tokens,
        "error_rate": error_rate,
        "active_users": active_users,
        "top_models": top_models,
        "top_tools": top_tools,
    }


@router.get("/telemetry/timeline")
def get_telemetry_timeline(
    days: int = 30,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """
    Daily task + token counts for the last N days.
    Returns: list of {date, tasks, tokens, errors}.
    """
    from datetime import timedelta
    from backend.models.telemetry import TelemetrySnapshot

    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = session.exec(
        select(TelemetrySnapshot).where(TelemetrySnapshot.created_at >= cutoff)
    ).all()

    # Build daily buckets
    buckets: dict = {}
    for r in rows:
        day = r.created_at.strftime("%Y-%m-%d")
        if day not in buckets:
            buckets[day] = {"date": day, "tasks": 0, "tokens": 0, "errors": 0}
        buckets[day]["tasks"] += 1
        buckets[day]["tokens"] += r.total_tokens
        buckets[day]["errors"] += r.error_count

    # Return sorted by date ascending
    return sorted(buckets.values(), key=lambda x: x["date"])


@router.get("/telemetry/models")
def get_telemetry_models(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """Per-model aggregates: task_count, total_tokens, avg_tokens."""
    from backend.models.telemetry import TelemetrySnapshot

    rows = session.exec(select(TelemetrySnapshot)).all()
    model_stats: dict = {}
    for r in rows:
        m = r.model_identifier or "unknown"
        if m not in model_stats:
            model_stats[m] = {"model_identifier": m, "task_count": 0, "total_tokens": 0}
        model_stats[m]["task_count"] += 1
        model_stats[m]["total_tokens"] += r.total_tokens

    result = []
    for m, s in model_stats.items():
        s["avg_tokens"] = s["total_tokens"] // s["task_count"] if s["task_count"] else 0
        result.append(s)
    return sorted(result, key=lambda x: x["task_count"], reverse=True)


@router.get("/telemetry/tools")
def get_telemetry_tools(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """Per-tool aggregates: call_count, task_count."""
    from backend.models.telemetry import TelemetrySnapshot

    rows = session.exec(select(TelemetrySnapshot)).all()
    tool_stats: dict = {}
    for r in rows:
        tc = r.tool_calls or {}
        for tool_name, count in tc.items():
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {"tool_name": tool_name, "call_count": 0, "task_count": 0}
            tool_stats[tool_name]["call_count"] += count
            tool_stats[tool_name]["task_count"] += 1
    return sorted(tool_stats.values(), key=lambda x: x["call_count"], reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# MCP Tools Management Endpoints
# ─────────────────────────────────────────────────────────────────────────────

def _get_disabled_tools(session: Session) -> list:
    """Return the list of disabled tool names from SystemSettings."""
    config = get_system_setting(session, "tool_config", {"disabled_tools": []})
    return config.get("disabled_tools", []) if isinstance(config, dict) else []


@router.get("/tools")
def list_mcp_tools(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """
    List all discovered MCP tools with their enabled/disabled status.
    The registry is read from the tool server's in-process module (same Python env).
    """
    from backend.mcp.registry import registry

    disabled = set(_get_disabled_tools(session))

    tools = []
    for name, meta in registry.tools.items():
        tools.append({
            "name": name,
            "description": meta.description[:200] if meta.description else "",
            "category": meta.category or "general",
            "agent_role": meta.agent_role,
            "is_llm_based": meta.is_llm_based,
            "enabled": name not in disabled,
        })

    # Sort by category then name for consistent display
    return sorted(tools, key=lambda t: (t["category"], t["name"]))


@router.put("/tools/{tool_name}/enabled")
def set_tool_enabled(
    tool_name: str,
    update: dict,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
):
    """
    Enable or disable a tool by name.
    Expects body: {"enabled": true/false}
    Changes take effect after restarting the Tool Server.
    """
    from backend.mcp.registry import registry

    if tool_name not in registry.tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found in registry")

    enabled = update.get("enabled", True)
    config = get_system_setting(session, "tool_config", {"disabled_tools": []})
    if not isinstance(config, dict):
        config = {"disabled_tools": []}

    disabled: list = config.get("disabled_tools", [])

    if enabled and tool_name in disabled:
        disabled.remove(tool_name)
    elif not enabled and tool_name not in disabled:
        disabled.append(tool_name)

    config["disabled_tools"] = disabled
    set_system_setting(session, "tool_config", config, current_user.id)

    return {"tool_name": tool_name, "enabled": enabled, "disabled_tools": disabled}


@router.post("/tools/refresh")
def refresh_mcp_tools(
    current_user: User = Depends(get_current_admin_user),
):
    """Re-scan the tools directory and return the updated tool list."""
    from backend.mcp.registry import registry

    registry.discover_tools(force=True)
    return {"status": "refreshed", "tool_count": len(registry.tools)}
