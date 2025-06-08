# -----------------------------------------------------------------------------
# ResearchAgent Tool: Tavily Web Search
#
# This tool allows the agent to search the web using the Tavily API.
# It follows the plug-and-play contract by defining a `tool` variable
# that the __init__.py loader can discover.
#
# Requires:
# - TAVILY_API_KEY environment variable to be set.
# -----------------------------------------------------------------------------

import logging
import os
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# This is the variable that the `__init__.py` loader will look for.
tool: BaseTool = None

# --- Tool Initialization ---
# We wrap the initialization in a try/except block to handle cases
# where the required API key is not set. This prevents the entire
# application from crashing if a single tool is misconfigured.

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY not set. The Tavily search tool will be disabled.")
else:
    try:
        # Instantiate the Tavily search tool provided by LangChain.
        # max_results can be tuned to control how much information is returned.
        search_tool = TavilySearchResults(max_results=5)
        
        # The default name and description are already quite good, but they can be
        # customized here if needed for better prompting. For example:
        # search_tool.name = "web_search"
        # search_tool.description = "A tool to search the internet for up-to-date information."
        
        # Assign the initialized tool to the 'tool' variable.
        tool = search_tool
        
    except Exception as e:
        logger.error(f"Failed to initialize TavilySearchResults tool: {e}", exc_info=True)
        # Ensure 'tool' is None if initialization fails.
        tool = None

# --- Self-Correction/Example for Loader ---
# To ensure this file is a valid tool module, the 'tool' variable must exist.
# The code above handles this, but as a safeguard:
if 'tool' not in globals():
    tool = None
