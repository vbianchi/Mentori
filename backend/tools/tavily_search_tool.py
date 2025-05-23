# backend/tools/tavily_search_tool.py
import asyncio
import logging
from typing import Optional, List, Type, Any, Dict, Union
import urllib.parse
from pathlib import Path
import sys
import traceback
import json

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic.v1 import BaseModel, Field # Ensure Pydantic v1 is used
from langchain_community.tools.tavily_search import TavilySearchResults

from backend.config import settings

logger = logging.getLogger(__name__)

class TavilySearchInput(BaseModel):
    query: str = Field(description="The search query string.")
    max_results: Optional[int] = Field(default=5, description="Maximum number of search results to return.")

    @classmethod
    def model_json_schema(cls, by_alias: bool = True, ref_template: str = "#/components/schemas/{model}") -> Dict[str, Any]:
        return cls.schema(by_alias=by_alias)

class TavilyAPISearchTool(BaseTool):
    name: str = "tavily_search_api"
    description: str = (
        "A search engine optimized for comprehensive, accurate, and trusted results using the Tavily API. "
        "Useful for when you need to answer questions about current events, recent information, "
        "or general knowledge questions that require up-to-date information from the web. "
        "Input MUST be a JSON string matching the TavilySearchInput schema (e.g., '{\"query\": \"your search query\", \"max_results\": 5}'), or a dictionary with 'query' and optional 'max_results' keys. "
        "Returns a list of search result objects, each containing 'title', 'url', and 'content' (snippet)."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    _tavily_search_instance: Optional[TavilySearchResults] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # ... (init logic remains the same as in tavily_test_script_fix_004) ...
        init_log_prefix = "TavilyAPISearchTool (__init__):"
        logger.info(f"{init_log_prefix} ENTERING __init__ (after super).")

        api_key_from_settings: Optional[str] = None
        settings_has_key_attr = hasattr(settings, 'tavily_api_key')

        if settings_has_key_attr:
            api_key_from_settings = settings.tavily_api_key
        else:
            logger.warning(f"{init_log_prefix} 'settings' object does NOT have 'tavily_api_key' attribute.")

        if api_key_from_settings and isinstance(api_key_from_settings, str) and api_key_from_settings.strip():
            logger.info(f"{init_log_prefix} Tavily API key IS present. Attempting instantiation of TavilySearchResults.")
            try:
                tavily_max_results_init = kwargs.get("tavily_init_max_results", 5)
                self._tavily_search_instance = TavilySearchResults(
                    max_results=tavily_max_results_init,
                    tavily_api_key=api_key_from_settings
                )
                logger.info(f"{init_log_prefix} self._tavily_search_instance ASSIGNED successfully. Type: {type(self._tavily_search_instance)}")
            except BaseException as e:
                logger.critical(f"{init_log_prefix} CRITICAL FAILURE: Failed to initialize TavilySearchResults. Error Type: {type(e).__name__}, Error: {e}", exc_info=True)
                self._tavily_search_instance = None
        else:
            logger.warning(f"{init_log_prefix} Tavily API key is MISSING, empty, or not a string in settings. Instance set to None.")
            self._tavily_search_instance = None
        logger.info(f"{init_log_prefix} EXITING __init__.")


    def _get_tavily_instance(self) -> TavilySearchResults:
        if self._tavily_search_instance is None:
            logger.error("TavilyAPISearchTool: _get_tavily_instance() found _tavily_search_instance is None. Check __init__ logs.")
            raise ToolException("Tavily Search API tool is not configured: API key missing or initialization error during tool setup (see __init__ logs).")
        return self._tavily_search_instance

    # MODIFIED: _arun signature and logic to directly use parsed args
    async def _arun(
        self,
        query: str, # Directly use 'query' as per args_schema
        max_results: Optional[int] = None, # Directly use 'max_results'
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any # To catch any other unexpected kwargs from BaseTool
    ) -> Union[List[Dict[str, Any]], str]:
        actual_query = query
        actual_max_results = max_results

        logger.info(f"TavilyAPISearchTool (_arun): Asynchronously searching for query: '{actual_query}', max_results: {actual_max_results}")

        try:
            tavily_instance = self._get_tavily_instance()

            # Prepare the input for the underlying TavilySearchResults tool
            tavily_tool_call_input = {"query": actual_query} # Pass query to the underlying tool

            # Set max_results on the TavilySearchResults instance for this call
            # The TavilySearchResults tool uses an instance variable for max_results.
            original_max_results = tavily_instance.max_results
            if actual_max_results is not None:
                tavily_instance.max_results = actual_max_results
            # else: it will use its existing default or the one set in __init__

            results_data = await tavily_instance.arun(
                tool_input=tavily_tool_call_input, # Langchain's Tavily tool expects a dict with 'query' or just the query string.
                callbacks=run_manager.get_child() if run_manager else None
            )

            # Reset max_results to its original value if it was changed
            if actual_max_results is not None:
                tavily_instance.max_results = original_max_results


            if isinstance(results_data, list):
                logger.info(f"TavilyAPISearchTool (_arun): Successfully received {len(results_data)} results for query '{actual_query}'.")
                return results_data
            elif isinstance(results_data, str): # Should ideally not happen if query is successful
                logger.warning(f"TavilyAPISearchTool (_arun): Tavily tool returned a string (possibly error for query '{actual_query}'): {results_data[:200]}")
                return results_data # Return error string from Tavily
            else:
                logger.error(f"TavilyAPISearchTool (_arun): Unexpected type {type(results_data)} from Tavily tool for query '{actual_query}'.")
                return f"Error: Unexpected result type {type(results_data)} from Tavily search."

        except ToolException: # Re-raise ToolExceptions from _get_tavily_instance
            raise
        except Exception as e:
            logger.error(f"TavilyAPISearchTool (_arun): Error during async search for '{actual_query}': {e}", exc_info=True)
            raise ToolException(f"Error performing asynchronous Tavily search for '{actual_query}': {e}") from e

    def _run(
        self,
        query: str, # MODIFIED: Reflect args_schema
        max_results: Optional[int] = None, # MODIFIED: Reflect args_schema
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> Union[List[Dict[str, Any]], str]:
        logger.warning("TavilyAPISearchTool (_run): Synchronous execution invoked. Attempting to run async logic.")
        # The input to _run is now expected to be unpacked by BaseTool.run
        # from a dict matching args_schema.
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                logger.info("TavilyAPISearchTool (_run): No current event loop, creating a new one.")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                logger.info("TavilyAPISearchTool (_run): Event loop is running. Using run_coroutine_threadsafe.")
                future = asyncio.run_coroutine_threadsafe(
                    self._arun(query=query, max_results=max_results, run_manager=run_manager, **kwargs), loop
                )
                return future.result(timeout=60)
            else:
                logger.info("TavilyAPISearchTool (_run): Event loop is not running. Using asyncio.run().")
                return loop.run_until_complete(self._arun(query=query, max_results=max_results, run_manager=run_manager, **kwargs))
        except Exception as e:
            logger.error(f"TavilyAPISearchTool (_run): Error trying to run async from sync: {e}", exc_info=True)
            return f"Error in sync execution wrapper: {type(e).__name__} - {e}"


async def main_test_tavily_wrapper_tool():
    print("\n--- Testing TavilyAPISearchTool (Our Wrapper) ---", flush=True)

    if not hasattr(settings, 'tavily_api_key') or not settings.tavily_api_key:
        print("Test SKIPPED: settings.tavily_api_key not found or not set for wrapper test.", flush=True)
        return

    tool_instance = TavilyAPISearchTool()
    if tool_instance._tavily_search_instance is None:
        print("Test (Wrapper) CRITICAL: _tavily_search_instance is None after __init__.", flush=True)
        return

    # Test Case 1: Simulating AgentExecutor passing JSON string (which BaseTool.arun parses)
    test_query1 = "What is the Tavily API used for?"
    test_max_results1 = 2
    tool_call_input_str1 = json.dumps({"query": test_query1, "max_results": test_max_results1})
    print(f"Test (Wrapper): Querying (async) with JSON string input: '{tool_call_input_str1}'", flush=True)
    results_data1 = await tool_instance.arun(tool_call_input_str1) # Pass JSON string

    print("\nTest Async Results (from JSON string input - should be List[Dict]):")
    if isinstance(results_data1, list):
        print(f"Received a list with {len(results_data1)} items.")
        for i, item in enumerate(results_data1):
            print(f"Result {i+1}: Title='{item.get('title', 'N/A')}', URL='{item.get('url', 'N/A')}'")
    else:
        print("Received non-list data (might be an error string):")
        print(results_data1)

    # Test Case 2: Passing a dictionary directly to arun (BaseTool.arun should handle this)
    test_query2 = "LangChain Pydantic v1 vs v2"
    test_max_results2 = 1
    tool_call_input_dict2 = {"query": test_query2, "max_results": test_max_results2}
    print(f"\nTest (Wrapper): Querying (async) with DICT input: '{tool_call_input_dict2}'", flush=True)
    results_data2 = await tool_instance.arun(tool_call_input_dict2) # Pass dict

    print("\nTest Async Results (from DICT input - should be List[Dict]):")
    if isinstance(results_data2, list):
        print(f"Received a list with {len(results_data2)} items.")
        for i, item in enumerate(results_data2):
            print(f"Result {i+1}: Title='{item.get('title', 'N/A')}', URL='{item.get('url', 'N/A')}'")
    else:
        print("Received non-list data (might be an error string):")
        print(results_data2)

    # Test Case 3: Query only, max_results should use default from args_schema or TavilySearchResults
    test_query3 = "latest advancements in quantum computing"
    tool_call_input_dict3 = {"query": test_query3} # No max_results
    print(f"\nTest (Wrapper): Querying (async) with DICT input (query only): '{tool_call_input_dict3}'", flush=True)
    results_data3 = await tool_instance.arun(tool_call_input_dict3)

    print("\nTest Async Results (query only - should be List[Dict]):")
    if isinstance(results_data3, list):
        print(f"Received a list with {len(results_data3)} items (expected default count).")
        for i, item in enumerate(results_data3):
            print(f"Result {i+1}: Title='{item.get('title', 'N/A')}', URL='{item.get('url', 'N/A')}'")
    else:
        print("Received non-list data (might be an error string):")
        print(results_data3)

if __name__ == "__main__":
    # ... (main block remains the same as in tavily_test_script_fix_004) ...
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - Line %(lineno)d - %(message)s'
    )
    try:
        from backend.config import settings as loaded_settings_for_main_test
        globals()['settings'] = loaded_settings_for_main_test
        if not hasattr(loaded_settings_for_main_test, 'tavily_api_key') or not loaded_settings_for_main_test.tavily_api_key:
             print("CRITICAL __main__: 'settings' from backend.config does not have 'tavily_api_key'.", flush=True)
             sys.exit(1)
    except ImportError:
        print("CRITICAL __main__: Could not import settings from backend.config.", flush=True)
        sys.exit(1)
    asyncio.run(main_test_tavily_wrapper_tool())
