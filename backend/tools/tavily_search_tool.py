import asyncio
import logging
from typing import Optional, List, Type, Any, Dict, Union
import urllib.parse 
from pathlib import Path 
import sys 
import traceback
# import json # No longer needed as TavilySearchResults returns list[dict]

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic.v1 import BaseModel, Field, root_validator 

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
        "Input should be a search query string. Optionally, 'max_results' can be specified. "
        "Returns a list of search result objects, each containing 'title', 'url', and 'content' (snippet)."
    )
    args_schema: Type[BaseModel] = TavilySearchInput
    
    _tavily_search_instance: Optional[TavilySearchResults] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs) 
        
        init_log_prefix = "TavilyAPISearchTool (__init__):"
        logger.info(f"{init_log_prefix} ENTERING __init__ (after super).")
        
        api_key_from_settings: Optional[str] = None
        settings_has_key_attr = hasattr(settings, 'tavily_api_key')
        logger.info(f"{init_log_prefix} hasattr(settings, 'tavily_api_key') -> {settings_has_key_attr}")

        if settings_has_key_attr:
            api_key_from_settings = settings.tavily_api_key
            logger.info(f"{init_log_prefix} Value of settings.tavily_api_key: '{str(api_key_from_settings)[:7]}...' (type: {type(api_key_from_settings)})")
        else:
            logger.warning(f"{init_log_prefix} 'settings' object does NOT have 'tavily_api_key' attribute.")

        if api_key_from_settings and isinstance(api_key_from_settings, str) and api_key_from_settings.strip():
            logger.info(f"{init_log_prefix} Tavily API key IS present. Attempting instantiation of TavilySearchResults.")
            try:
                logger.info(f"{init_log_prefix} Instantiating TavilySearchResults...")
                # Get max_results from kwargs if provided during TavilyAPISearchTool instantiation,
                # otherwise TavilySearchResults will use its own default.
                # The 'max_results' from args_schema is handled per-call in _run/_arun.
                tavily_max_results_init = kwargs.get("tavily_init_max_results", 5) # Default for the instance
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

    def _format_results_to_string(self, results_list: List[Dict[str, Any]]) -> str:
        if not results_list or not isinstance(results_list, list): 
            logger.warning(f"TavilyAPISearchTool (_format_results_to_string): Expected a list of results, got {type(results_list)}. Returning as is or empty.")
            return str(results_list) if results_list else "No relevant search results found."
        
        formatted_strings = []
        for i, res in enumerate(results_list):
            if not isinstance(res, dict): 
                logger.warning(f"TavilyAPISearchTool (_format_results_to_string): Expected a dict for result item, got {type(res)}. Skipping item.")
                continue
            title = res.get("title", "N/A")
            url = res.get("url", "N/A")
            content = res.get("content", "N/A") 
            
            if not isinstance(content, str):
                content = str(content)
            content = content.replace("\n", " ").strip()
            
            formatted_strings.append(
                f"Search Result {i + 1}:\nTitle: {title}\nURL: {url}\nSnippet: {content}"
            )
        return "\n\n===\n\n".join(formatted_strings) if formatted_strings else "No relevant search results found."

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
            
            tool_input_dict = {"query": query}
            if max_results is not None: # Allow overriding max_results per call
                tool_input_dict["max_results"] = max_results
            
            # MODIFIED: TavilySearchResults.run() returns List[Dict[str, Any]]
            results_data = tavily_instance.run(tool_input=tool_input_dict) 
            
            if isinstance(results_data, list):
                logger.info(f"TavilyAPISearchTool (_run): Successfully received {len(results_data)} results.")
                return results_data # Return the list of dicts
            elif isinstance(results_data, str): 
                logger.warning(f"TavilyAPISearchTool (_run): Tavily tool returned a string (possibly error): {results_data[:200]}")
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
            
            tool_input_dict = {"query": query}
            if max_results is not None: # Allow overriding max_results per call
                tool_input_dict["max_results"] = max_results

            # MODIFIED: TavilySearchResults.arun() returns List[Dict[str, Any]]
            results_data = await tavily_instance.arun(tool_input=tool_input_dict)

            if isinstance(results_data, list):
                logger.info(f"TavilyAPISearchTool (_arun): Successfully received {len(results_data)} results.")
                return results_data # Return the list of dicts
            elif isinstance(results_data, str): 
                logger.warning(f"TavilyAPISearchTool (_arun): Tavily tool returned a string (possibly error): {results_data[:200]}")
                return results_data
            else:
                logger.error(f"TavilyAPISearchTool (_arun): Unexpected type from Tavily tool: {type(results_data)}")
                return "Error: Unexpected result type from asynchronous Tavily search."
                
        except ToolException: raise
        except Exception as e: 
            logger.error(f"TavilyAPISearchTool (_arun): Error during async search for '{query}': {e}", exc_info=True)
            raise ToolException(f"Error performing asynchronous Tavily search: {e}")

async def main_test_tavily_wrapper_tool():
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
        
        if tool_instance._tavily_search_instance is None:
            print("Test (Wrapper) CRITICAL: _tavily_search_instance is None after __init__. Check __init__ print/log messages.", flush=True)
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
                # print(f"   Snippet: {item.get('content', 'N/A')[:100]}...") # Optionally print snippet
        else:
            print("Received non-list data (might be an error string):")
            print(results_data)

    except Exception as e:
        print(f"Test (Wrapper) CRITICAL ERROR: {type(e).__name__} - {e}", flush=True)
        traceback.print_exc() 
    print("---------------------------------", flush=True)

if __name__ == "__main__":
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
