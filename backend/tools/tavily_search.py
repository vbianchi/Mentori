# -----------------------------------------------------------------------------
# Mentor::i Tool: Tavily Web Search (Robust)
#
# CORRECTION: The tool is now explicitly configured with a Pydantic args_schema
# to enforce the input argument name `query`. This prevents the planner from
# hallucinating incorrect argument names like `search_query`. The tool's name
# has also been simplified to `web_search` for clearer prompting.
# -----------------------------------------------------------------------------

import logging
import os
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# This is the variable that the `__init__.py` loader will look for.
tool: BaseTool = None

# --- Pydantic Schema for a Consistent Interface ---
class WebSearchInput(BaseModel):
    """Input for the web search tool."""
    query: str = Field(description="The search query to send to the search engine.")

# --- Tool Initialization ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY not set. The web_search tool will be disabled.")
else:
    try:
        # Instantiate the Tavily search tool
        search_tool = TavilySearchResults(
            max_results=5,
            args_schema=WebSearchInput # Enforce the schema
        )
        
        # Override the default name and description for better prompting
        search_tool.name = "web_search"
        search_tool.description = "A tool to search the internet for up-to-date information, news, and articles. Use it to find information on any topic."
        
        # Assign the initialized tool to the 'tool' variable.
        tool = search_tool
        
    except Exception as e:
        logger.error(f"Failed to initialize TavilySearchResults tool: {e}", exc_info=True)
        tool = None

# Safeguard to ensure the 'tool' variable exists for the loader.
if 'tool' not in globals():
    tool = None
