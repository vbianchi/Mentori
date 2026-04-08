"""
Debug Logger for Message Flow Analysis

This module provides detailed logging of the complete message flow
during chat interactions. It captures everything the model sees,
its responses, tool calls, and how context evolves across turns.

Usage:
    Set environment variable: MENTORI_DEBUG_FLOW=1
    Logs are written to: /workspace_data/debug_flow_{task_id}.log
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Check if debug mode is enabled
DEBUG_FLOW_ENABLED = os.environ.get("MENTORI_DEBUG_FLOW", "0") == "1"

logger = logging.getLogger(__name__)


class MessageFlowDebugger:
    """
    Captures and logs the complete message flow for debugging.
    """

    def __init__(self, task_id: str, output_dir: str = "/workspace_data"):
        self.task_id = task_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / f"debug_flow_{task_id}.log"
        self.step_count = 0
        self.enabled = DEBUG_FLOW_ENABLED

        if self.enabled:
            self._write_header()

    def _write_header(self):
        """Write the log file header."""
        with open(self.log_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write(f"MESSAGE FLOW DEBUG LOG\n")
            f.write(f"Task ID: {self.task_id}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

    def _append(self, content: str):
        """Append content to the log file."""
        if not self.enabled:
            return
        with open(self.log_file, "a") as f:
            f.write(content)

    def log_initial_messages(self, messages: List[Dict[str, Any]]):
        """Log the initial messages sent to the model."""
        if not self.enabled:
            return

        self._append("\n" + "=" * 80 + "\n")
        self._append("INITIAL MESSAGES (what model receives at start)\n")
        self._append("=" * 80 + "\n\n")

        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            self._append(f"--- Message {i + 1} [{role.upper()}] ---\n")

            # Truncate very long content but note the full length
            self._append(content + "\n")

            self._append("\n")

        self._append(f"Total messages: {len(messages)}\n")
        self._append(f"Total content length: {sum(len(m.get('content', '')) for m in messages)} chars\n\n")

    def log_step_start(self, step: int, current_messages: List[Dict[str, Any]]):
        """Log the start of a new step/turn."""
        if not self.enabled:
            return

        self.step_count = step

        self._append("\n" + "#" * 80 + "\n")
        self._append(f"STEP {step} - MODEL INVOCATION\n")
        self._append("#" * 80 + "\n\n")

        self._append(f"Timestamp: {datetime.now().isoformat()}\n")
        self._append(f"Messages in context: {len(current_messages)}\n\n")

        # Show the last few messages (most relevant context)
        self._append("--- RECENT CONTEXT (last 5 messages) ---\n\n")
        for msg in current_messages[-5:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls")
            name = msg.get("name")  # For tool messages

            self._append(f"[{role.upper()}]")
            if name:
                self._append(f" (tool: {name})")
            self._append(":\n")

            # Show content
            self._append(f"  {content}\n")

            # Show tool calls if present
            if tool_calls:
                self._append(f"  Tool calls: {json.dumps(tool_calls, indent=2)}\n")

            self._append("\n")

    def log_model_response(self, full_content: str, full_thinking: str, tool_calls: List[Dict]):
        """Log what the model returned."""
        if not self.enabled:
            return

        self._append("--- MODEL RESPONSE ---\n\n")

        # Thinking (from Ollama's think feature)
        if full_thinking:
            self._append(f"[INTERNAL THINKING] ({len(full_thinking)} chars):\n")
            self._append(full_thinking + "\n")
            self._append("\n")

        # Visible content
        self._append(f"[VISIBLE CONTENT] ({len(full_content)} chars):\n")
        self._append(full_content + "\n\n")

        # Check for visible thinking patterns in content
        thinking_patterns = [
            "[Thinking Process]:",
            "<thinking>",
            "**Thinking:**"
        ]
        found_patterns = [p for p in thinking_patterns if p in full_content]
        if found_patterns:
            self._append(f"WARNING: Found visible thinking patterns in content: {found_patterns}\n\n")

        # Tool calls
        if tool_calls:
            self._append(f"[TOOL CALLS] ({len(tool_calls)} calls):\n")
            for tc in tool_calls:
                self._append(f"  - {tc.get('function', {}).get('name', 'unknown')}\n")
                args = tc.get('function', {}).get('arguments', {})
                self._append(f"    Arguments: {json.dumps(args, indent=4)}\n")
            self._append("\n")

    def log_content_stripping(self, original: str, stripped: str):
        """Log what was stripped from content before adding to context."""
        if not self.enabled:
            return

        self._append("--- CONTENT STRIPPING ---\n\n")
        self._append(f"Original length: {len(original)}\n")
        self._append(f"Stripped length: {len(stripped)}\n")
        self._append(f"Removed: {len(original) - len(stripped)} chars\n\n")

        if original != stripped:
            self._append("Original content:\n")
            self._append(original + "\n\n")
            self._append("Stripped content:\n")
            self._append(stripped + "\n\n")

    def log_message_added_to_context(self, message: Dict[str, Any], context_type: str = "current_messages"):
        """Log when a message is added to the context."""
        if not self.enabled:
            return

        role = message.get("role", "unknown")
        content = message.get("content", "")

        self._append(f"--- ADDED TO {context_type.upper()} ---\n")
        self._append(f"Role: {role}\n")
        self._append(f"Content length: {len(content)}\n")
        if message.get("tool_calls"):
            self._append(f"Tool calls: {len(message['tool_calls'])}\n")
        if message.get("name"):
            self._append(f"Tool name: {message['name']}\n")
        self._append("\n")

    def log_tool_execution(self, tool_name: str, arguments: Dict, result: str):
        """Log tool execution details."""
        if not self.enabled:
            return

        self._append(f"--- TOOL EXECUTION: {tool_name} ---\n\n")
        self._append(f"Arguments:\n{json.dumps(arguments, indent=2)}\n\n")
        self._append(f"Result ({len(result)} chars):\n")
        self._append(result + "\n")
        self._append("\n")

    def log_history_loading(self, history_msgs: List[Any], stripped_count: int):
        """Log what was loaded from DB and stripped."""
        if not self.enabled:
            return

        self._append("\n" + "=" * 80 + "\n")
        self._append("HISTORY LOADING FROM DATABASE\n")
        self._append("=" * 80 + "\n\n")

        self._append(f"Total messages loaded: {len(history_msgs)}\n")
        self._append(f"Messages with thinking stripped: {stripped_count}\n\n")

        # Show each message
        for i, m in enumerate(history_msgs):
            role = getattr(m, 'role', 'unknown')
            content = getattr(m, 'content', '') or ''
            seq = getattr(m, 'sequence', i)

            self._append(f"[{seq}] {role.upper()}: {len(content)} chars\n")

            # Check for thinking patterns
            if "[Thinking Process]:" in content:
                self._append(f"    WARNING: Contains [Thinking Process]: pattern!\n")
                # Show first occurrence
                idx = content.find("[Thinking Process]:")
                self._append(f"    Preview: ...{content[max(0,idx-20):idx+100]}...\n")

        self._append("\n")

    def log_step_end(self, has_tool_calls: bool, is_final: bool):
        """Log the end of a step."""
        if not self.enabled:
            return

        self._append(f"--- STEP {self.step_count} END ---\n")
        self._append(f"Had tool calls: {has_tool_calls}\n")
        self._append(f"Is final response: {is_final}\n")
        self._append("\n")

    def log_final_summary(self, total_steps: int, total_tool_calls: int):
        """Log a final summary."""
        if not self.enabled:
            return

        self._append("\n" + "=" * 80 + "\n")
        self._append("FINAL SUMMARY\n")
        self._append("=" * 80 + "\n\n")
        self._append(f"Total steps: {total_steps}\n")
        self._append(f"Total tool calls: {total_tool_calls}\n")
        self._append(f"Completed: {datetime.now().isoformat()}\n")
        self._append(f"Log file: {self.log_file}\n")

        logger.info(f"[DEBUG_FLOW] Log written to: {self.log_file}")


# Global instance placeholder
_debugger_instance: Optional[MessageFlowDebugger] = None


def get_debugger(task_id: str) -> MessageFlowDebugger:
    """Get or create a debugger instance for the given task."""
    global _debugger_instance
    if _debugger_instance is None or _debugger_instance.task_id != task_id:
        _debugger_instance = MessageFlowDebugger(task_id)
    return _debugger_instance


def is_debug_enabled() -> bool:
    """Check if debug flow logging is enabled."""
    return DEBUG_FLOW_ENABLED
