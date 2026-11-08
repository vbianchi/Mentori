# backend/agents/models/utils.py
"""
Centralized Model Identifier Parsing Utilities.

MODEL IDENTIFIER FORMAT:
    provider::model_name[think:level]

Examples:
    - ollama::llama3.2:latest           -> No thinking
    - ollama::qwen3:8b[think:true]      -> Boolean thinking (think=True)
    - ollama::gpt-oss:20b[think:low]    -> Level thinking (think="low")
    - ollama::gpt-oss:20b[think:medium] -> Level thinking (think="medium")
    - ollama::gpt-oss:20b[think:high]   -> Level thinking (think="high")
    - gemini::gemini-1.5-flash          -> No thinking (Gemini provider)

THINKING RULES:
    1. No suffix              -> think=False
    2. [think:true]           -> think=True (boolean mode)
    3. [think:low|medium|high] -> think="low"|"medium"|"high" (level mode)

This module is the SINGLE SOURCE OF TRUTH for model identifier parsing.
All other modules should import from here instead of implementing their own parsing.
"""

from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class ParsedModelIdentifier:
    """Result of parsing a model identifier string."""
    provider: str           # "ollama", "gemini", etc.
    model_name: str         # Clean model name without suffix
    think: Union[bool, str, None]  # False, True, "low", "medium", "high", or None
    original: str           # Original identifier string

    @property
    def full_identifier(self) -> str:
        """Returns provider::model_name (without think suffix)."""
        return f"{self.provider}::{self.model_name}"

    @property
    def is_thinking_model(self) -> bool:
        """Returns True if model has any thinking mode enabled."""
        return self.think is not None and self.think is not False

    @property
    def thinking_type(self) -> Optional[str]:
        """Returns 'boolean', 'level', or None."""
        if self.think is True:
            return "boolean"
        elif isinstance(self.think, str):
            return "level"
        return None


def parse_model_identifier(model_identifier: str) -> ParsedModelIdentifier:
    """
    Parse a model identifier string into its components.

    This is the CANONICAL parsing function - use this everywhere.

    Args:
        model_identifier: String like "ollama::llama3.2:latest[think:high]"

    Returns:
        ParsedModelIdentifier with all components extracted

    Examples:
        >>> parse_model_identifier("ollama::llama3.2:latest")
        ParsedModelIdentifier(provider='ollama', model_name='llama3.2:latest', think=False, ...)

        >>> parse_model_identifier("ollama::gpt-oss:20b[think:high]")
        ParsedModelIdentifier(provider='ollama', model_name='gpt-oss:20b', think='high', ...)

        >>> parse_model_identifier("ollama::qwen3:8b[think:true]")
        ParsedModelIdentifier(provider='ollama', model_name='qwen3:8b', think=True, ...)
    """
    original = model_identifier
    think: Union[bool, str, None] = False

    # 1. Extract provider (default to "ollama" if not specified)
    if "::" in model_identifier:
        provider, model_name = model_identifier.split("::", 1)
    else:
        provider = "ollama"
        model_name = model_identifier

    provider = provider.lower()

    # 2. Extract think suffix if present: [think:value]
    if "[" in model_name and "]" in model_name:
        bracket_start = model_name.index("[")
        bracket_end = model_name.index("]")
        suffix = model_name[bracket_start + 1:bracket_end].lower()

        # Remove the suffix from model name
        model_name = model_name[:bracket_start]

        # Parse the suffix
        if suffix.startswith("think:"):
            value = suffix.replace("think:", "").strip()
            if value == "true":
                think = True
            elif value == "false":
                think = False
            elif value in ("low", "medium", "high"):
                think = value
            else:
                # Unknown value, treat as boolean true
                think = True
        elif suffix == "think":
            # Just [think] without value means true
            think = True

    return ParsedModelIdentifier(
        provider=provider,
        model_name=model_name.strip(),
        think=think,
        original=original
    )


def extract_think_param(model_identifier: str) -> Union[bool, str]:
    """
    Quick utility to just get the think parameter from a model identifier.

    Args:
        model_identifier: Full model string

    Returns:
        False, True, or "low"/"medium"/"high"
    """
    parsed = parse_model_identifier(model_identifier)
    return parsed.think if parsed.think is not None else False


def strip_model_suffix(model_identifier: str) -> str:
    """
    Remove the [think:...] suffix from a model identifier.

    Args:
        model_identifier: Full model string like "ollama::model[think:high]"

    Returns:
        Clean identifier like "ollama::model"
    """
    parsed = parse_model_identifier(model_identifier)
    return parsed.full_identifier


def get_clean_model_name(model_identifier: str) -> str:
    """
    Get just the model name without provider or suffix.

    Args:
        model_identifier: Full model string

    Returns:
        Just the model name (e.g., "llama3.2:latest")
    """
    parsed = parse_model_identifier(model_identifier)
    return parsed.model_name
