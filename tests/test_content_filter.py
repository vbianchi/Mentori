"""Tests for the content filter module."""

import pytest
from backend.agents.content_filter import filter_content, filter_event, FilterResult


class TestFilterContent:
    """Tests for the filter_content function."""

    def test_empty_text(self):
        """Empty text should return unchanged."""
        result = filter_content("")
        assert result.filtered_text == ""
        assert result.violations == []
        assert not result.had_violations

    def test_none_text(self):
        """None text should return unchanged."""
        result = filter_content(None)
        assert result.filtered_text is None
        assert result.violations == []

    def test_no_sensitive_content(self):
        """Normal text should pass through unchanged."""
        text = "This is a normal message about Python programming."
        result = filter_content(text)
        assert result.filtered_text == text
        assert result.violations == []
        assert not result.had_violations

    def test_openai_key_detection(self):
        """OpenAI API keys should be redacted."""
        text = "My key is sk-abcdefghijklmnopqrstuvwxyz12345678"
        result = filter_content(text)
        assert "sk-" not in result.filtered_text
        assert "[REDACTED_OPENAI_KEY]" in result.filtered_text
        assert "openai_key" in result.violations
        assert result.had_violations

    def test_openai_proj_key_detection(self):
        """OpenAI project keys should be redacted."""
        text = "Use this key: sk-proj-ABC123xyz_this-is-a-project-key"
        result = filter_content(text)
        assert "sk-proj-" not in result.filtered_text
        assert "[REDACTED_OPENAI_KEY]" in result.filtered_text
        assert result.had_violations

    def test_anthropic_key_detection(self):
        """Anthropic API keys should be redacted."""
        text = "Anthropic key: sk-ant-api03-abcdefghijklmnopqrstuvwxyz"
        result = filter_content(text)
        assert "sk-ant-" not in result.filtered_text
        assert "[REDACTED_ANTHROPIC_KEY]" in result.filtered_text
        assert result.had_violations

    def test_aws_key_detection(self):
        """AWS access keys should be redacted."""
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = filter_content(text)
        assert "AKIA" not in result.filtered_text
        assert "[REDACTED_AWS_KEY]" in result.filtered_text
        assert result.had_violations

    def test_google_api_key_detection(self):
        """Google API keys should be redacted."""
        # Google API keys are 39 chars: AIza + 35 alphanumeric/dash/underscore
        text = "Google key: AIzaSyC1234567890abcdefghijklmnopqrstuv"
        result = filter_content(text)
        assert "AIza" not in result.filtered_text
        assert "[REDACTED_GOOGLE_KEY]" in result.filtered_text
        assert result.had_violations

    def test_github_token_detection(self):
        """GitHub tokens should be redacted."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        result = filter_content(text)
        assert "ghp_" not in result.filtered_text
        assert "[REDACTED_GITHUB_TOKEN]" in result.filtered_text
        assert result.had_violations

    def test_tavily_key_detection(self):
        """Tavily API keys should be redacted."""
        text = "TAVILY_API_KEY=tvly-abcdefghijklmnopqrstuvwx"
        result = filter_content(text)
        assert "tvly-" not in result.filtered_text
        assert "[REDACTED_TAVILY_KEY]" in result.filtered_text
        assert result.had_violations

    def test_multiple_keys_detection(self):
        """Multiple keys in same text should all be redacted."""
        text = """
        OPENAI_API_KEY=sk-abc123xyz789def456ghi012jkl345mno
        AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
        """
        result = filter_content(text)
        assert "sk-" not in result.filtered_text
        assert "AKIA" not in result.filtered_text
        assert len(result.violations) == 2
        assert result.had_violations


class TestFilterEvent:
    """Tests for the filter_event function."""

    def test_chunk_event_filtered(self):
        """Chunk events should have content filtered."""
        event = {
            "type": "chunk",
            "content": "Your key is sk-abc123xyz789def456ghi012jkl345mno"
        }
        filtered = filter_event(event)
        assert "sk-" not in filtered["content"]
        assert "[REDACTED_OPENAI_KEY]" in filtered["content"]

    def test_tool_result_event_filtered(self):
        """Tool result events should have content filtered."""
        event = {
            "type": "tool_result",
            "tool_result": {
                "name": "some_tool",
                "content": "Found key: sk-abc123xyz789def456ghi012jkl345mno"
            }
        }
        filtered = filter_event(event)
        assert "sk-" not in filtered["tool_result"]["content"]

    def test_thinking_chunk_filtered(self):
        """Thinking chunks should be filtered."""
        event = {
            "type": "thinking_chunk",
            "content": "I see the API key sk-abc123xyz789def456ghi012jkl345mno"
        }
        filtered = filter_event(event)
        assert "sk-" not in filtered["content"]

    def test_other_events_unchanged(self):
        """Non-content events should pass through unchanged."""
        event = {
            "type": "status",
            "status": "processing"
        }
        filtered = filter_event(event)
        assert filtered == event

    def test_event_without_content(self):
        """Events without content field should pass through."""
        event = {
            "type": "chunk"
        }
        filtered = filter_event(event)
        assert filtered == event
