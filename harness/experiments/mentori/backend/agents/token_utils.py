# backend/agents/token_utils.py
"""
Token budget utilities for model-aware context management.

Instead of hardcoded character thresholds, all token-budget decisions go through
this module so that a single admin setting (`min_context_window`) controls the
behaviour across the whole pipeline.

Usage::

    from backend.agents.token_utils import estimate_tokens, safe_char_budget

    if estimate_tokens(text) > safe_char_budget(fraction=0.5):
        # truncate or distill
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default minimum context window (tokens).
# Overridden at runtime by the SystemSettings key "min_context_window".
# 128 K is the conservative floor based on models commonly deployed with Mentori
# (gpt-oss:20b = 128K, deepseek-R1 = 128K, qwen3:30b = 256K, etc.)
# ---------------------------------------------------------------------------
DEFAULT_MIN_CONTEXT_WINDOW = 131_072  # 128 K tokens

# Safety fraction — how much of the context window we actually use.
# Leaves room for the system prompt, tool schemas, conversation history, etc.
DEFAULT_SAFETY_FRACTION = 0.80


def estimate_tokens(text: str) -> int:
    """
    Fast heuristic: ~4 chars per token (accurate ±20% for English/code).

    For Ollama-hosted models we cannot call the tokenizer directly without
    loading the model's vocab, so this heuristic is the pragmatic choice.
    It is consistently used everywhere so any systematic error cancels out.
    """
    return max(0, len(text) // 4)


def get_min_context_window() -> int:
    """
    Return the admin-configured minimum context window (in tokens).

    Reads from the `SystemSettings` table (key = "min_context_window").
    Falls back to DEFAULT_MIN_CONTEXT_WINDOW if the setting is absent or
    the DB is unreachable.

    The value should be the *smallest* context window among the models
    assigned to the orchestrator, editor, and supervisor roles — the roles
    that receive accumulated step results and synthesis prompts.
    """
    try:
        from sqlmodel import Session, select
        from backend.database import engine
        from backend.models.system_settings import SystemSettings

        with Session(engine) as session:
            setting = session.exec(
                select(SystemSettings).where(
                    SystemSettings.key == "min_context_window"
                )
            ).first()
            if setting and isinstance(setting.value, dict):
                tokens = setting.value.get("tokens")
                if isinstance(tokens, int) and tokens > 0:
                    return tokens
    except Exception as e:
        logger.debug(f"token_utils: could not read min_context_window from DB: {e}")

    return DEFAULT_MIN_CONTEXT_WINDOW


def safe_char_budget(
    fraction: Optional[float] = None,
    min_context_window: Optional[int] = None,
) -> int:
    """
    Return the number of characters that safely fit in the context window.

    Args:
        fraction: Fraction of the context window to use (default 0.80).
        min_context_window: Override the DB lookup (useful in tests or when
                            the value has already been fetched).

    Returns:
        Character budget as an integer.
    """
    if fraction is None:
        fraction = DEFAULT_SAFETY_FRACTION
    if min_context_window is None:
        min_context_window = get_min_context_window()

    safe_tokens = int(min_context_window * fraction)
    return safe_tokens * 4  # chars ≈ tokens × 4
