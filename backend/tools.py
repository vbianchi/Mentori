# backend/tools.py
import logging
from langchain_community.tools import ShellTool # Use the built-in tool

logger = logging.getLogger(__name__)

# Initialize the built-in Shell Tool
# It runs commands in a subprocess and returns the output.
# Be cautious about security implications of allowing arbitrary shell commands.
shell_tool = ShellTool()

# You can customize its description to help the LLM understand when to use it
shell_tool.description = (
    "Use this tool to execute shell commands in a Linux-like environment. "
    "Input should be a valid shell command string. "
    "The tool returns the stdout of the command. Handle errors appropriately. "
    "Use it for tasks like listing files (ls), checking versions (python --version), "
    "reading file contents (cat), etc. Do NOT use it for long-running processes."
)

# List of tools the agent can use
agent_tools = [shell_tool]

# Example of adding another tool later (e.g., web search)
# from langchain_community.tools import DuckDuckGoSearchRun
# search_tool = DuckDuckGoSearchRun()
# agent_tools.append(search_tool)

logger.info(f"Initialized tools: {[tool.name for tool in agent_tools]}")

