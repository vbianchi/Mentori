# backend/mcp/agent_tools.py
"""
Agent-specific tool filtering and access control.

This module provides per-agent tool access control to ensure:
1. The orchestrator doesn't have direct code execution tools
2. The coder has its own set of tools
3. Each agent role gets only the tools it needs
"""

from typing import Dict, List, Set, Optional
from backend.mcp.registry import registry, ToolRegistry
from backend.mcp.decorator import ToolMetadata


# Define which tools each agent role can access
# None = all tools, empty set = no MCP tools, set of names = specific tools

AGENT_TOOL_ACCESS = {
    # Lead researcher (orchestrator) - general purpose, NO direct code execution
    "lead_researcher": {
        "allowed": None,  # Allow all tools by default
        "denied": {
            "execute_python",  # Use coder mode instead
            "write_code",      # Use coder mode instead
        },
        "message_for_denied": {
            "execute_python": "For code execution, please use Coder Mode (click the robot icon or say 'switch to coder mode').",
            "write_code": "For writing code files, please use Coder Mode (click the robot icon).",
        }
    },

    # Coder - notebook-based coding (uses internal tools, not MCP)
    "coder": {
        "allowed": {
            # Coder primarily uses internal notebook tools, but can use:
            "install_package",    # For dependency management
            "web_search",         # For looking up documentation
            # Notebook MCP tools — coder can read/write cells directly,
            # using NotebookManager (preserves newlines, proper nbformat)
            "list_notebooks",
            "read_notebook",
            "get_notebook_cell",
            "write_notebook_cell",
            "add_notebook_cell",
        },
        "denied": None,
    },

    # Handyman - system operations
    "handyman": {
        "allowed": {
            "run_bash",
            "install_package",
            "read_file",
            "list_directory",
            "write_file",
        },
        "denied": None,
    },

    # Vision - image analysis
    "vision": {
        "allowed": {
            "analyze_image",
            "read_file",
        },
        "denied": None,
    },

    # Editor - document editing (future)
    "editor": {
        "allowed": None,
        "denied": None,
    },
}


class AgentToolRegistry:
    """
    Provides agent-specific tool filtering.

    Wraps the main ToolRegistry and filters tools based on agent role.
    """

    def __init__(self, tool_registry: ToolRegistry = None):
        """
        Initialize with the main tool registry.

        Args:
            tool_registry: The main ToolRegistry instance (defaults to global registry)
        """
        self._registry = tool_registry or registry

    def get_tools_for_agent(self, agent_role: str) -> List[ToolMetadata]:
        """
        Get filtered list of tools for a specific agent role.

        Args:
            agent_role: The agent role (e.g., "lead_researcher", "coder", "handyman")

        Returns:
            List of ToolMetadata for tools this agent can access
        """
        # Ensure tools are discovered
        if not self._registry.tools:
            self._registry.discover_tools()

        # Get access rules for this agent
        access_rules = AGENT_TOOL_ACCESS.get(agent_role, {"allowed": None, "denied": None})
        allowed = access_rules.get("allowed")
        denied = access_rules.get("denied") or set()

        filtered_tools = []

        for name, metadata in self._registry.tools.items():
            # Check if tool is explicitly denied
            if name in denied:
                continue

            # Check if tool is in allowed set (if specified)
            if allowed is not None and name not in allowed:
                continue

            filtered_tools.append(metadata)

        return filtered_tools

    def get_tool_schemas_for_agent(self, agent_role: str) -> List[Dict]:
        """
        Get tool schemas formatted for LLM consumption.

        Args:
            agent_role: The agent role

        Returns:
            List of tool schema dicts suitable for LLM tools parameter
        """
        tools = self.get_tools_for_agent(agent_role)
        return [
            {
                "type": "function",
                "function": tool.schema
            }
            for tool in tools
        ]

    def is_tool_allowed(self, tool_name: str, agent_role: str) -> bool:
        """
        Check if a specific tool is allowed for an agent.

        Args:
            tool_name: Name of the tool
            agent_role: The agent role

        Returns:
            True if the tool is allowed for this agent
        """
        access_rules = AGENT_TOOL_ACCESS.get(agent_role, {"allowed": None, "denied": None})
        allowed = access_rules.get("allowed")
        denied = access_rules.get("denied") or set()

        # Check if denied
        if tool_name in denied:
            return False

        # Check if allowed (if whitelist specified)
        if allowed is not None:
            return tool_name in allowed

        return True

    def get_denial_message(self, tool_name: str, agent_role: str) -> Optional[str]:
        """
        Get a helpful message when a tool is denied.

        Args:
            tool_name: Name of the denied tool
            agent_role: The agent role that was denied

        Returns:
            Helpful message or None if no specific message
        """
        access_rules = AGENT_TOOL_ACCESS.get(agent_role, {})
        messages = access_rules.get("message_for_denied", {})
        return messages.get(tool_name)

    def list_all_agents(self) -> List[str]:
        """Get list of all defined agent roles."""
        return list(AGENT_TOOL_ACCESS.keys())

    def get_tools_summary(self, agent_role: str) -> Dict:
        """
        Get a summary of tools available to an agent.

        Args:
            agent_role: The agent role

        Returns:
            Dict with tool counts and categories
        """
        tools = self.get_tools_for_agent(agent_role)

        categories = {}
        for tool in tools:
            cat = tool.category or "general"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool.name)

        return {
            "agent_role": agent_role,
            "total_tools": len(tools),
            "categories": categories,
            "tool_names": [t.name for t in tools]
        }


# Global instance for convenience
agent_tool_registry = AgentToolRegistry()


def get_tools_for_agent(agent_role: str) -> List[ToolMetadata]:
    """Convenience function to get tools for an agent."""
    return agent_tool_registry.get_tools_for_agent(agent_role)


def get_tool_schemas_for_agent(agent_role: str) -> List[Dict]:
    """Convenience function to get tool schemas for an agent."""
    return agent_tool_registry.get_tool_schemas_for_agent(agent_role)


def is_tool_allowed(tool_name: str, agent_role: str) -> bool:
    """Convenience function to check tool access."""
    return agent_tool_registry.is_tool_allowed(tool_name, agent_role)
