# backend/tools/tavily_search_tool.py
import asyncio
import logging
from typing import Optional, List, Type, Any, Dict, Union
import urllib.parse
from pathlib import Path
import sys
import traceback

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field # Using Pydantic v2

from langchain_community.tools.tavily_search import TavilySearchResults

from backend.config import settings

logger = logging.getLogger(__name__)

class TavilySearchInput(BaseModel):
    query: str = Field(description="The search query string.")
    max_results: Optional[int] = Field(default=5, description="Maximum number of search results to return.")

    @classmethod
    def model_json_schema(cls, by_alias: bool = True, ref_template: str = "#/components/schemas/{model}") -> Dict[str, Any]:
        return super().model_json_schema(by_alias=by_alias, ref_template=ref_template)


class TavilyAPISearchTool(BaseTool):
    name: str = "tavily_search_api"
    description: str = (
        "A search engine optimized for comprehensive, accurate, and trusted results using the Tavily API. "
        "Useful for when you need to answer questions about current events, recent information, "
        "or general knowledge questions that require up-to-date information from the web. "
        "Input should be a JSON string with a 'query' (string, required) and optional 'max_results' (integer). "
        "Returns a list of search result objects, each containing 'title', 'url', and 'content' (snippet)."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    tavily_search_instance_internal: Optional[TavilySearchResults] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True
    # For Pydantic v2, if Config class is not automatically handled by BaseTool's metaclass:
    # model_config = {"arbitrary_types_allowed": True}


    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        init_log_prefix = "TavilyAPISearchTool (__init__):"
        logger.info(f"{init_log_prefix} ENTERING __init__ (after super).")
        api_key_from_settings: Optional[str] = None
        settings_has_key_attr = hasattr(settings, 'tavily_api_key')
        if settings_has_key_attr: api_key_from_settings = settings.tavily_api_key
        if api_key_from_settings and isinstance(api_key_from_settings, str) and api_key_from_settings.strip():
            try:
                tavily_max_results_init = kwargs.get("tavily_init_max_results", 5)
                self.tavily_search_instance_internal = TavilySearchResults(
                    max_results=tavily_max_results_init,
                    tavily_api_key=api_key_from_settings
                )
                logger.info(f"{init_log_prefix} self.tavily_search_instance_internal ASSIGNED successfully.")
            except BaseException as e:
                logger.critical(f"{init_log_prefix} CRITICAL FAILURE initializing TavilySearchResults: {e}", exc_info=True)
                self.tavily_search_instance_internal = None
        else:
            logger.warning(f"{init_log_prefix} Tavily API key MISSING or invalid. Instance set to None.")
            self.tavily_search_instance_internal = None
        logger.info(f"{init_log_prefix} EXITING __init__.")

    def _get_tavily_instance(self) -> TavilySearchResults:
        if self.tavily_search_instance_internal is None:
            logger.error("TavilyAPISearchTool: _get_tavily_instance() found internal instance is None.")
            raise ToolException("Tavily Search API tool is not configured or failed initialization.")
        return self.tavily_search_instance_internal

    def _run(
        self,
        query: str,
        max_results: Optional[int] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> Union[List[Dict[str, Any]], str]:
        logger.info(f"TavilyAPISearchTool (_run): Synchronously searching for '{query}', max_results: {max_results}")
        try:
            tavily_instance = self._get_tavily_instance()
            # Call the underlying tool's run method correctly
            results_data = tavily_instance.run(tool_input=query) # <<< Corrected: use tool_input

            if isinstance(results_data, list):
                logger.info(f"TavilyAPISearchTool (_run): Successfully received {len(results_data)} results from Tavily.")
                if max_results is not None and len(results_data) > max_results:
                    results_data = results_data[:max_results]
                    logger.info(f"TavilyAPISearchTool (_run): Sliced results to {len(results_data)} based on max_results={max_results}.")
                return results_data
            elif isinstance(results_data, str):
                logger.warning(f"TavilyAPISearchTool (_run): Tavily tool returned a string: {results_data[:200]}")
                return results_data
            else:
                logger.error(f"TavilyAPISearchTool (_run): Unexpected type from Tavily tool: {type(results_data)}")
                return "Error: Unexpected result type from Tavily search."
        except ToolException: raise
        except Exception as e:
            logger.error(f"TavilyAPISearchTool (_run): Error during search for '{query}': {e}", exc_info=True)
            raise ToolException(f"Error performing Tavily search: {e}")

    async def _arun(
        self,
        query: str,
        max_results: Optional[int] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> Union[List[Dict[str, Any]], str]:
        logger.info(f"TavilyAPISearchTool (_arun): Asynchronously searching for '{query}', max_results: {max_results}")
        try:
            tavily_instance = self._get_tavily_instance()
            # <<< --- CORRECTED LINE --- >>>
            results_data = await tavily_instance.arun(tool_input=query)
            # <<< --- END CORRECTED LINE --- >>>

            if isinstance(results_data, list):
                logger.info(f"TavilyAPISearchTool (_arun): Successfully received {len(results_data)} results from Tavily.")
                if max_results is not None and len(results_data) > max_results:
                    results_data = results_data[:max_results]
                    logger.info(f"TavilyAPISearchTool (_arun): Sliced results to {len(results_data)} based on max_results={max_results}.")
                return results_data
            elif isinstance(results_data, str):
                logger.warning(f"TavilyAPISearchTool (_arun): Tavily tool returned a string: {results_data[:200]}")
                return results_data
            else:
                logger.error(f"TavilyAPISearchTool (_arun): Unexpected type from Tavily tool: {type(results_data)}")
                return "Error: Unexpected result type from asynchronous Tavily search."
        except ToolException: raise
        except Exception as e:
            logger.error(f"TavilyAPISearchTool (_arun): Error during async search for '{query}': {e}", exc_info=True)
            raise ToolException(f"Error performing asynchronous Tavily search: {e}")

async def main_test_tavily_wrapper_tool():
    # ... (main test function remains the same) ...
    print("\n--- Testing TavilyAPISearchTool (Our Wrapper) ---", flush=True)
    if not hasattr(settings, 'tavily_api_key') or not settings.tavily_api_key:
        print("Test SKIPPED: settings.tavily_api_key not found or not set for wrapper test.", flush=True)
        return
    print(f"Test (Wrapper): Found Tavily API Key in settings: '{settings.tavily_api_key[:7]}...'")
    tool_instance = None
    try:
        print("Test (Wrapper): Instantiating TavilyAPISearchTool...", flush=True)
        tool_instance = TavilyAPISearchTool()
        print("Test (Wrapper): TavilyAPISearchTool instantiated.", flush=True)
        if tool_instance.tavily_search_instance_internal is None:
            print("Test (Wrapper) CRITICAL: tavily_search_instance_internal is None after __init__. Check __init__ print/log messages.", flush=True)
            return
        test_query = "What is the Tavily API used for?"
        test_max_results = 2
        print(f"Test (Wrapper): Querying (async): '{test_query}' with max_results={test_max_results}", flush=True)
        results_data = await tool_instance.arun({"query": test_query, "max_results": test_max_results})
        print("\nTest Async Results (from wrapper - should be List[Dict]):")
        if isinstance(results_data, list):
            print(f"Received a list with {len(results_data)} items.")
            for i, item in enumerate(results_data):
                print(f"Result {i+1}: Title='{item.get('title', 'N/A')}', URL='{item.get('url', 'N/A')}'")
        else:
            print("Received non-list data (might be an error string):")
            print(results_data)
    except Exception as e:
        print(f"Test (Wrapper) CRITICAL ERROR: {type(e).__name__} - {e}", flush=True)
        traceback.print_exc()
    print("---------------------------------", flush=True)

if __name__ == "__main__":
    # ... (main block remains the same) ...
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - Line %(lineno)d - %(message)s'
    )
    try:
        from backend.config import settings as loaded_settings_for_main_test
        globals()['settings'] = loaded_settings_for_main_test
        if not hasattr(loaded_settings_for_main_test, 'tavily_api_key'):
             print("CRITICAL __main__: 'settings' from backend.config does not have 'tavily_api_key'.", flush=True)
             sys.exit(1)
        elif not loaded_settings_for_main_test.tavily_api_key:
            print("WARNING __main__: TAVILY_API_KEY is not set in the loaded settings from backend.config.", flush=True)
    except ImportError:
        print("CRITICAL __main__: Could not import settings from backend.config.", flush=True)
        sys.exit(1)
    except AttributeError:
        print("CRITICAL __main__: 'settings' object imported from backend.config is missing 'tavily_api_key'. Check config.py.", flush=True)
        sys.exit(1)
    asyncio.run(main_test_tavily_wrapper_tool())
