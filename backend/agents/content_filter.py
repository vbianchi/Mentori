"""
Output content filter - detects and redacts sensitive patterns (API keys).

This module provides real-time filtering of streamed content to prevent
accidental exposure of API keys and other secrets in chat responses.
"""
import re
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

# API key patterns to detect and redact
# Ordered by specificity (most specific first to avoid partial matches)
PATTERNS = {
    # OpenAI keys (sk-proj-* is the newer format)
    "openai_proj": re.compile(r'\b(sk-proj-[A-Za-z0-9_-]{20,})\b'),
    "openai_key": re.compile(r'\b(sk-[A-Za-z0-9]{20,})\b'),

    # Anthropic keys
    "anthropic_key": re.compile(r'\b(sk-ant-[A-Za-z0-9_-]{20,})\b'),

    # AWS keys
    "aws_access_key": re.compile(r'\b(AKIA[0-9A-Z]{16})\b'),

    # Google API keys
    "google_api_key": re.compile(r'\b(AIza[A-Za-z0-9_-]{35})\b'),

    # GitHub tokens
    "github_token": re.compile(r'\b(ghp_[A-Za-z0-9]{36})\b'),
    "github_token_classic": re.compile(r'\b(github_pat_[A-Za-z0-9_]{22,})\b'),

    # Tavily API key (commonly used in Mentori)
    "tavily_key": re.compile(r'\b(tvly-[A-Za-z0-9]{20,})\b'),

    # Generic patterns for common key formats in code examples
    # Be careful with these - they can have false positives
    "generic_bearer": re.compile(r'(Bearer\s+[A-Za-z0-9_-]{20,})', re.IGNORECASE),
}

REDACTIONS = {
    "openai_proj": "[REDACTED_OPENAI_KEY]",
    "openai_key": "[REDACTED_OPENAI_KEY]",
    "anthropic_key": "[REDACTED_ANTHROPIC_KEY]",
    "aws_access_key": "[REDACTED_AWS_KEY]",
    "google_api_key": "[REDACTED_GOOGLE_KEY]",
    "github_token": "[REDACTED_GITHUB_TOKEN]",
    "github_token_classic": "[REDACTED_GITHUB_TOKEN]",
    "tavily_key": "[REDACTED_TAVILY_KEY]",
    "generic_bearer": "[REDACTED_BEARER_TOKEN]",
}


@dataclass
class FilterResult:
    """Result of content filtering."""
    filtered_text: str
    violations: List[str]
    had_violations: bool


def filter_content(text: str) -> FilterResult:
    """
    Filter sensitive content from text.

    Args:
        text: Input text to filter

    Returns:
        FilterResult with filtered text and list of detected pattern names
    """
    if not text:
        return FilterResult(filtered_text=text, violations=[], had_violations=False)

    violations = []
    filtered = text

    for name, pattern in PATTERNS.items():
        if pattern.search(filtered):
            violations.append(name)
            filtered = pattern.sub(REDACTIONS[name], filtered)

    had_violations = len(violations) > 0

    if had_violations:
        logger.warning(f"Content filter triggered: {violations}")

    return FilterResult(
        filtered_text=filtered,
        violations=violations,
        had_violations=had_violations
    )


def filter_event(event: dict) -> dict:
    """
    Filter sensitive content from a chat event.

    Handles different event types:
    - chunk: Filter the content field
    - tool_result: Filter the tool_result.content field
    - thinking_chunk: Filter the content field
    - Other events: Pass through unchanged

    Args:
        event: Chat event dictionary

    Returns:
        Event with filtered content (modifies in place for efficiency)
    """
    event_type = event.get("type")

    if event_type == "chunk":
        content = event.get("content")
        if content:
            result = filter_content(content)
            event["content"] = result.filtered_text

    elif event_type == "tool_result":
        tool_result = event.get("tool_result", {})
        content = tool_result.get("content")
        if content and isinstance(content, str):
            result = filter_content(content)
            tool_result["content"] = result.filtered_text

    elif event_type == "thinking_chunk":
        content = event.get("content")
        if content:
            result = filter_content(content)
            event["content"] = result.filtered_text

    return event
