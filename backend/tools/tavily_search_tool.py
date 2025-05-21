import asyncio
import logging
from typing import Optional, List, Type, Any, Dict
import urllib.parse 
from pathlib import Path 

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic.v1 import BaseModel, Field, root_validator 

from langchain_community.tools.tavily_search import TavilySearchResults

# Import settings to check for API key
from backend.config import settings 

logger = logging.getLogger(__name__)

class TavilySearchInput(BaseModel):
    query: str = Field(description="The search query string.")

class TavilyAPISearchTool(BaseTool):
    name: str = "tavily_search_api" 
    description: str = (
        "A search engine optimized for comprehensive, accurate, and trusted results using the Tavily API. "
        "Useful for when you need to answer questions about current events, recent information, "
        "or general knowledge questions that require up-to-date information from the web. "
        "Input should be a single search query string."
    )
    args_schema: Type[BaseModel] = TavilySearchInput
    _tavily_search_instance: Any = None 

    class Config:
        arbitrary_types_allowed = True

    @root_validator(pre=True)
    def check_api_key_and_initialize(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("TavilyAPISearchTool: Root validator 'check_api_key_and_initialize' called.")
        
        api_key_from_settings: Optional[str] = None
        if hasattr(settings, 'tavily_api_key'): 
            api_key_from_settings = settings.tavily_api_key
        
        if api_key_from_settings:
            logger.info(f"TavilyAPISearchTool: Tavily API key found via settings: '{str(api_key_from_settings)[:7]}...'")
            try:
                logger.info("TavilyAPISearchTool: Attempting to instantiate TavilySearchResults in root_validator...")
                instance = TavilySearchResults(
                    max_results=values.get("num_results", 3), 
                    tavily_api_key=api_key_from_settings 
                )
                values["_tavily_search_instance"] = instance
                logger.info("TavilyAPISearchTool: TavilySearchResults instance CREATED and assigned to values in root_validator.")
            except BaseException as e: 
                logger.critical(
                    f"TAVILY_CRITICAL_INIT_FAILURE (in root_validator): Failed to initialize TavilySearchResults. "
                    f"Error Type: {type(e).__name__}, Error: {e}", 
                    exc_info=True
                )
                values["_tavily_search_instance"] = None
                # raise e # Keep commented out for now
        else:
            logger.warning(
                "TavilyAPISearchTool: Tavily API key (settings.tavily_api_key) is NOT SET or is empty in root_validator. "
                "The TavilyAPISearchTool may not function. Instance set to None."
            )
            values["_tavily_search_instance"] = None
        return values
    
    def _get_tavily_instance(self) -> TavilySearchResults:
        if self._tavily_search_instance is None:
            logger.error("TavilyAPISearchTool: _tavily_search_instance is None. This indicates a failure during tool instantiation (check root_validator logs for TAVILY_CRITICAL_INIT_FAILURE).")
            raise ToolException("Tavily Search API tool is not configured: API key missing or initialization error during tool setup.")
        
        if not isinstance(self._tavily_search_instance, TavilySearchResults):
            logger.error(f"TavilyAPISearchTool: _tavily_search_instance is not a TavilySearchResults instance. Actual Type: {type(self._tavily_search_instance)}. This is unexpected.")
            raise ToolException(f"Tavily Search API tool instance is of an unexpected type: {type(self._tavily_search_instance)}")
        return self._tavily_search_instance

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any) -> str:
        logger.info(f"TavilyAPISearchTool (_run): Searching for '{query}'")
        try:
            tavily_instance = self._get_tavily_instance()
            result = tavily_instance.run(tool_input=query) 
            return str(result)
        except ToolException: raise
        except Exception as e:
            logger.error(f"TavilyAPISearchTool (_run): Error during search for '{query}': {e}", exc_info=True)
            raise ToolException(f"Error performing Tavily search: {e}")

    async def _arun(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any) -> str:
        logger.info(f"TavilyAPISearchTool (_arun): Asynchronously searching for '{query}'")
        try:
            tavily_instance = self._get_tavily_instance()
            result = await tavily_instance.arun(query=query) 
            return str(result)
        except ToolException: raise
        except Exception as e:
            logger.error(f"TavilyAPISearchTool (_arun): Error during async search for '{query}': {e}", exc_info=True)
            raise ToolException(f"Error performing asynchronous Tavily search: {e}")

async def main_test_tavily_direct_instantiation():
    """Tests direct instantiation and use of langchain_community.tools.TavilySearchResults."""
    print("\n--- Direct Test for langchain_community.tools.TavilySearchResults ---")
    
    if not hasattr(settings, 'tavily_api_key') or not settings.tavily_api_key:
        print("Test SKIPPED: settings.tavily_api_key not found or not set in the loaded config. Check .env and config.py.")
        return

    api_key = settings.tavily_api_key
    print(f"Test: Using Tavily API Key from settings: '{api_key[:7]}...'")

    try:
        print("Test: Attempting direct instantiation of TavilySearchResults...")
        direct_tavily_tool_instance = TavilySearchResults(
            tavily_api_key=api_key,
            max_results=3 
        )
        print(f"Test: Direct TavilySearchResults instantiated successfully: {type(direct_tavily_tool_instance)}")
        
        test_query = "What is the Tavily API?"
        print(f"Test: Querying (async with direct instance): '{test_query}'")
        
        # MODIFIED: Pass query as a dictionary to arun for BaseTool compatibility
        results_async = await direct_tavily_tool_instance.arun({"query": test_query}) 
        print("\nTest Async Results (from direct instance):")
        print(results_async)

    except Exception as e:
        print(f"Test CRITICAL ERROR during direct instantiation or arun of TavilySearchResults: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc() 
    print("---------------------------------")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - Line %(lineno)d - %(message)s'
    )
    try:
        from backend.config import settings as loaded_settings_for_test
        globals()['settings'] = loaded_settings_for_test 
        if not hasattr(loaded_settings_for_test, 'tavily_api_key'):
            print("CRITICAL: 'settings' from backend.config does not have 'tavily_api_key' attribute after import for test.")
        elif not loaded_settings_for_test.tavily_api_key:
            print("WARNING: TAVILY_API_KEY is not set in the loaded settings from backend.config for test.")
    except ImportError:
        print("CRITICAL: Could not import settings from backend.config for test. Ensure paths are correct.")
        sys.exit(1) # Use sys.exit for cleaner exit in main script
    except AttributeError:
        print("CRITICAL: 'settings' object imported from backend.config is missing 'tavily_api_key' for test. Check config.py.")
        sys.exit(1)

    asyncio.run(main_test_tavily_direct_instantiation())
