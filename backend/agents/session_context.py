"""
Session Context for Mentori Agent Execution

Provides immutable context for the current request, including:
- User identity
- Task information
- Workspace paths
- Model configuration
- Automatic logging context

All fields are deterministic and should NEVER come from agent reasoning.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from contextvars import ContextVar
import logging

# Thread-local storage for current session context
_session_context: ContextVar[Optional['SessionContext']] = ContextVar('session_context', default=None)


# Valid agent role names
AGENT_ROLES = ["lead_researcher", "supervisor", "librarian", "coder", "handyman", "editor", "transcriber", "vision", "default"]


@dataclass(frozen=True)
class SessionContext:
    """
    Immutable context for a chat session.

    All fields are derived from the authenticated request and should
    NEVER be provided by or modifiable by the agent.
    """
    # Identity (from authenticated user)
    user_id: str
    user_email: str
    user_role: str

    # User profile (for AI personalization)
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
    user_preferences: Optional[str] = None  # User context/preferences for AI

    # Task (from URL path /tasks/{task_id}/chat)
    task_id: str = ""              # UUID
    task_display_id: str = ""      # Human-readable (e.g., "abc123")
    task_title: str = ""
    workspace_path: str = ""

    # Model configuration (from task settings)
    model_identifier: str = ""
    mode: str = "chat"  # "chat" or "agentic"

    # User settings (safe subset for tool execution)
    api_keys: Dict[str, str] = field(default_factory=dict)
    rag_preferences: Dict[str, any] = field(default_factory=dict)

    # Agent role bindings (from user.settings.agent_roles)
    agent_roles: Dict[str, str] = field(default_factory=dict)

    # Orchestrator settings
    require_plan_approval: bool = False

    # User's available RAG indexes (for document queries)
    # List of dicts with: {"name": str, "description": str, "status": str, "file_count": int}
    available_indexes: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def user_display_name(self) -> str:
        """Get the user's display name (first + last name or email)."""
        if self.user_first_name and self.user_last_name:
            return f"{self.user_first_name} {self.user_last_name}"
        elif self.user_first_name:
            return self.user_first_name
        return self.user_email.split('@')[0]  # Fallback to email username

    @property
    def log_context(self) -> dict:
        """
        Standard logging context for all operations in this session.

        Format: {"user_id": uuid, "task_id": "task_abc123"}
        Used by: logger.info("msg", extra=ctx.log_context)
        """
        return {
            "user_id": self.user_id,
            "task_id": f"task_{self.task_display_id}"
        }

    @property
    def log_prefix(self) -> str:
        """
        Human-readable log prefix.

        Format: "[user@email.com | task_abc123]"
        Used for: Manual log formatting when needed
        """
        return f"[{self.user_email} | task_{self.task_display_id}]"

    def __str__(self) -> str:
        return f"SessionContext(user={self.user_email}, task={self.task_display_id}, model={self.model_identifier})"

    def get_model_for_role(self, role: str) -> Optional[str]:
        """
        Get the model identifier assigned to a specific agent role.

        Args:
            role: One of AGENT_ROLES (e.g., "editor", "coder", "default")

        Returns:
            Model identifier (e.g., "ollama::llama3") or None if not configured
        """
        return self.agent_roles.get(role) or None


# ============================================================================
# Agent Role Resolution
# ============================================================================

def resolve_model_for_chat(agent_roles: Dict[str, str], preferred_role: str = "lead_researcher") -> tuple[str, str]:
    """
    Resolve which model to use for chat based on agent role configuration.

    For basic chat mode, we use the Lead Researcher agent with fallback to Default.

    Args:
        agent_roles: Dict mapping role names to model identifiers
        preferred_role: The preferred role to use (default: "lead_researcher")

    Returns:
        Tuple of (model_identifier, resolved_role) or (None, None) if no model configured

    Raises:
        ValueError: If neither preferred role nor default role is configured
    """
    # Try preferred role first (e.g., "lead_researcher")
    model = agent_roles.get(preferred_role)
    if model and model.strip():
        return model, preferred_role

    # Fallback to default
    default_model = agent_roles.get("default")
    if default_model and default_model.strip():
        return default_model, "default"

    # No model configured
    return None, None


def validate_agent_config(agent_roles: Dict[str, str]) -> tuple[bool, str]:
    """
    Validate that the user has configured at least a default agent.

    Args:
        agent_roles: Dict mapping role names to model identifiers

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not agent_roles:
        return False, "No agent roles configured. Please go to Settings → Agent Roles and assign at least a Default agent."

    # Check if at least default is set
    default_model = agent_roles.get("default")
    if not default_model or not default_model.strip():
        # Check if any other role is set
        has_any_role = any(
            agent_roles.get(role) and agent_roles.get(role).strip()
            for role in AGENT_ROLES if role != "default"
        )
        if not has_any_role:
            return False, "No agent roles configured. Please go to Settings → Agent Roles and assign at least a Default agent."

    return True, ""


# ============================================================================
# Context Management (Thread-local storage)
# ============================================================================

def set_session_context(ctx: SessionContext):
    """
    Set the session context for the current request/task.

    This stores the context in thread-local storage so it can be
    accessed anywhere in the call stack without explicit passing.

    Usage:
        # In endpoint (tasks.py):
        ctx = SessionContext(user_id=..., task_id=..., ...)
        set_session_context(ctx)

        # Deep in retrieval stack:
        ctx = get_session_context()
        logger.info("Indexing document", extra=ctx.log_context)
    """
    _session_context.set(ctx)

    # Also set up the logging adapter for convenience
    _setup_logging_adapter(ctx)


def get_session_context() -> Optional[SessionContext]:
    """
    Get the current session context from thread-local storage.

    Returns None if not in a request context (e.g., background jobs).
    """
    return _session_context.get()


def require_session_context() -> SessionContext:
    """
    Get the current session context, raising if not available.

    Use this when session context is required for security.
    """
    ctx = _session_context.get()
    if ctx is None:
        raise RuntimeError(
            "No session context available. "
            "This function must be called within a request handler."
        )
    return ctx


# ============================================================================
# Logging Integration
# ============================================================================

def _setup_logging_adapter(ctx: SessionContext):
    """
    Configure the root logger to automatically inject session context.

    After calling this, all logger.info() calls in this thread will
    automatically include user_id and task_id without needing extra={}.
    """
    # This is handled by our custom LoggerAdapter below
    pass


class SessionContextAdapter(logging.LoggerAdapter):
    """
    Logging adapter that automatically injects session context.

    Usage:
        logger = get_logger(__name__)
        logger.info("Starting ingestion")  # Automatically includes user_id, task_id
    """

    def process(self, msg, kwargs):
        """Inject session context into all log calls."""
        ctx = get_session_context()

        if ctx:
            # Merge with any explicit extra provided
            extra = kwargs.get('extra', {})
            extra.update(ctx.log_context)
            kwargs['extra'] = extra

        return msg, kwargs


def get_logger(name: str) -> logging.LoggerAdapter:
    """
    Get a context-aware logger that automatically injects session info.

    Usage:
        # At top of file:
        logger = get_logger(__name__)

        # Later (inside request handler):
        logger.info("Processing document")
        # Output: 10:30:15 - user@email.com - task_abc123 - [INFO] - Processing document
    """
    base_logger = logging.getLogger(name)
    return SessionContextAdapter(base_logger, {})


# ============================================================================
# Tool Execution Helpers
# ============================================================================

def inject_session_secrets(
    agent_args: dict,
    tool_signature: 'inspect.Signature',
    tool_secrets: list
) -> dict:
    """
    Automatically inject session context into tool arguments.

    Security Rules:
    1. Session context ALWAYS overrides agent-provided values
    2. Only inject if tool's signature expects the parameter
    3. Log security warnings when agent tries to override

    Args:
        agent_args: Arguments provided by agent in tool call
        tool_signature: inspect.signature() of the tool function
        tool_secrets: List of secret parameter names (from @mentori_tool)

    Returns:
        Final kwargs with session values injected
    """
    ctx = get_session_context()
    if not ctx:
        # No session context (e.g., CLI script) - return as-is
        return agent_args.copy()

    final_kwargs = agent_args.copy()
    logger = get_logger(__name__)
    injected = []

    # Map of parameter names to session values
    injection_map = {
        "user_id": ctx.user_id,
        "user_email": ctx.user_email,
        "user_role": ctx.user_role,
        "task_id": ctx.task_id,
        "task_display_id": ctx.task_display_id,
        "workspace_path": ctx.workspace_path,
        "model_identifier": ctx.model_identifier,
    }

    # Map agent role model parameters to their values
    # e.g., "vision_model" -> ctx.agent_roles.get("vision")
    agent_role_model_map = {
        "vision_model": ctx.agent_roles.get("vision") or ctx.agent_roles.get("default"),
        "coder_model": ctx.agent_roles.get("coder") or ctx.agent_roles.get("default"),
        "handyman_model": ctx.agent_roles.get("handyman") or ctx.agent_roles.get("default"),
        "editor_model": ctx.agent_roles.get("editor") or ctx.agent_roles.get("default"),
        "supervisor_model": ctx.agent_roles.get("supervisor") or ctx.agent_roles.get("default"),
        "default_model": ctx.agent_roles.get("default"),
    }

    # Inject if parameter exists in function signature
    for param_name, value in injection_map.items():
        if param_name in tool_signature.parameters:
            # Security check: Detect if agent tried to override
            if param_name in final_kwargs and final_kwargs[param_name] != value:
                logger.warning(
                    f"[SECURITY] Agent attempted to override {param_name}='{final_kwargs[param_name]}', "
                    f"enforcing session value: '{value}'"
                )

            final_kwargs[param_name] = value
            injected.append(param_name)

    # Inject agent role models if parameter exists in function signature
    for param_name, value in agent_role_model_map.items():
        if param_name in tool_signature.parameters and value:
            # Security check: Detect if agent tried to override
            if param_name in final_kwargs and final_kwargs[param_name] != value:
                logger.warning(
                    f"[SECURITY] Agent attempted to override {param_name}='{final_kwargs[param_name]}', "
                    f"enforcing session value: '{value}'"
                )
            
            final_kwargs[param_name] = value
            injected.append(f"{param_name} (agent role)")

    # Inject API keys from user settings or environment
    import os
    import re
    for secret_name in tool_secrets:
        api_key_value = None
        source = None

        # 1. Try User Settings (Priority)
        if secret_name in ctx.api_keys:
            raw_value = ctx.api_keys[secret_name]
            if raw_value:
                # CRITICAL: Robust stripping - handles unicode whitespace, newlines, tabs,
                # non-breaking spaces, zero-width chars, etc. Users copy-paste API keys
                # with invisible characters that .strip() doesn't catch.
                api_key_value = re.sub(r'[\s\u00a0\u200b\u200c\u200d\ufeff]+', '', raw_value)
                source = "user_settings"
                # Debug: Log key info (first/last 4 chars only for security)
                if len(api_key_value) > 8:
                    key_preview = f"{api_key_value[:4]}...{api_key_value[-4:]}"
                else:
                    key_preview = "***"
                logger.info(f"[SECRET_INJECT] {secret_name}: raw_len={len(raw_value)}, clean_len={len(api_key_value)}, preview={key_preview}")

        # 2. Fallback to Environment Variables
        if not api_key_value:
            raw_env = os.environ.get(secret_name)
            if raw_env:
                # Also apply robust stripping to env vars
                api_key_value = re.sub(r'[\s\u00a0\u200b\u200c\u200d\ufeff]+', '', raw_env)
                source = "environment"
                logger.info(f"[SECRET_INJECT] {secret_name}: loaded from environment, len={len(api_key_value)}")

        if api_key_value:
            # ALWAYS overwrite - LLM might provide partial/wrong keys
            if secret_name in final_kwargs:
                logger.warning(f"[SECRET_INJECT] Overwriting LLM-provided {secret_name} with secure value")
            final_kwargs[secret_name] = api_key_value
            injected.append(f"{secret_name} (API key from {source})")
        elif not api_key_value:
            logger.warning(f"[SECRET_INJECT] API key '{secret_name}' NOT FOUND in user settings or environment.")

    if injected:
        logger.debug(f"Auto-injected: {', '.join(injected)}")

    return final_kwargs


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: How to use in an endpoint
    from datetime import datetime

    # 1. Build context from request
    ctx = SessionContext(
        user_id="user-uuid-123",
        user_email="vale@lab.org",
        user_role="user",
        task_id="task-uuid-456",
        task_display_id="abc123",
        task_title="Research Analysis",
        workspace_path="/workspace/user-uuid-123/task_abc123",
        model_identifier="ollama::llama3:70b",
        mode="agentic",
        api_keys={"TAVILY_API_KEY": "secret-key"},
        rag_preferences={"max_results": 10}
    )

    # 2. Set context for this request
    set_session_context(ctx)

    # 3. Use context-aware logger anywhere
    logger = get_logger(__name__)
    logger.info("Starting analysis")
    # Output: 10:30:15 - vale@lab.org - task_abc123 - [INFO] - Starting analysis

    # 4. Deep in the stack (e.g., retrieval layer)
    def some_deep_function():
        ctx = get_session_context()
        if ctx:
            logger = get_logger(__name__)
            logger.info(f"Processing for user {ctx.user_email}")
            # Automatically includes context!

    some_deep_function()
