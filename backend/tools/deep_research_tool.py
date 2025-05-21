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
from pydantic.v1 import BaseModel, Field, root_validator, validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models.chat_models import BaseChatModel


from .tavily_search_tool import TavilyAPISearchTool
# MODIFIED: Removed top-level import of fetch_and_parse_url
# from .standard_tools import fetch_and_parse_url 

from backend.config import settings 
from backend.llm_setup import get_llm 

logger = logging.getLogger(__name__)

class DeepResearchToolInput(BaseModel):
    topic: str = Field(description="The core research topic or question for the deep investigation.")
    num_initial_sources_to_consider: int = Field(
        default=7, 
        description="Approximate number of initial search results to consider from the first web search pass."
    )
    num_sources_to_deep_dive: int = Field(
        default=3,
        description="Number of top sources to select for in-depth content extraction and analysis."
    )
    # desired_report_sections: Optional[List[str]] = Field(default=None, ...) 

    @classmethod
    def model_json_schema(cls, by_alias: bool = True, ref_template: str = "#/components/schemas/{model}") -> Dict[str, Any]:
        return cls.schema(by_alias=by_alias)

class CuratedSourcesOutput(BaseModel):
    selected_urls: List[str] = Field(description="A list of URLs selected as most promising for deep research.")
    reasoning: Optional[str] = Field(default=None, description="Brief reasoning for the selection (optional).")

    @validator('selected_urls', each_item=True)
    def check_url_format(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Each URL must start with http:// or https://')
        return v

CURATOR_SYSTEM_PROMPT_TEMPLATE = """
You are an expert Research Assistant acting as a Source Curator.
Your task is to analyze a list of web search results (including titles, URLs, and snippets)
and select the most promising and authoritative sources for a deep research report on a given topic.

Topic for the report: "{topic}"

You need to select the top {num_sources_to_deep_dive} URLs.
Prioritize:
- Primary research articles (e.g., from scientific journals, university sites).
- Reputable news organizations or institutions providing in-depth analysis.
- Comprehensive reviews or official reports.
- Relevance and substance indicated by the title and snippet.

Avoid:
- Forum discussions, social media, minor blog posts, or very brief news updates unless they seem exceptionally unique and relevant.
- Duplicate content or near-duplicates if distinguishable.
- URLs that seem broken or lead to paywalls if alternatives are available.

Based on the provided search results below, return your selection.
You MUST respond with a single JSON object matching the following schema:
{format_instructions}
Do not include any preamble or explanation outside of the JSON object.
"""

class DeepResearchTool(BaseTool):
    name: str = "deep_research_synthesizer"
    description: str = (
        "Performs an in-depth, multi-step research investigation on a given topic. "
        "It conducts a broad web search, curates top sources, then extracts content from these sources. "
        "Future steps will synthesize this into a comprehensive report. "
        "Use for complex research questions. Input is 'topic', optionally 'num_initial_sources_to_consider' and 'num_sources_to_deep_dive'."
    )
    args_schema: Type[BaseModel] = DeepResearchToolInput
    
    _tavily_search_tool_instance: Optional[TavilyAPISearchTool] = Field(default=None, exclude=True)
    _curator_llm: Optional[BaseChatModel] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True 

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs) 
        init_log_prefix = "DeepResearchTool (__init__):"
        logger.info(f"{init_log_prefix} ENTERING __init__.")
        
        if hasattr(settings, 'tavily_api_key') and settings.tavily_api_key:
            try:
                self._tavily_search_tool_instance = TavilyAPISearchTool()
                logger.info(f"{init_log_prefix} Internal TavilyAPISearchTool instantiated.")
            except Exception as e:
                logger.error(f"{init_log_prefix} Failed to instantiate internal TavilyAPISearchTool: {e}", exc_info=True)
        else:
            logger.warning(f"{init_log_prefix} Tavily API key not found. Tavily search sub-tool will be unavailable.")

        try:
            logger.info(f"{init_log_prefix} Initializing Curator LLM using Planner's settings ({settings.planner_provider}::{settings.planner_model_name}).")
            self._curator_llm = get_llm(
                settings,
                provider=settings.planner_provider, 
                model_name=settings.planner_model_name,
                requested_for_role="DeepResearch_Curator"
            )
            logger.info(f"{init_log_prefix} Curator LLM initialized.")
        except Exception as e:
            logger.error(f"{init_log_prefix} Failed to initialize Curator LLM: {e}", exc_info=True)
        
        logger.info(f"{init_log_prefix} EXITING __init__.")
    
    def _get_internal_tavily_tool(self) -> TavilyAPISearchTool:
        if self._tavily_search_tool_instance is None:
            raise ToolException("Internal Tavily Search sub-tool for DeepResearchTool is not available (failed initialization or no API key).")
        return self._tavily_search_tool_instance

    def _get_curator_llm(self) -> BaseChatModel:
        if self._curator_llm is None:
            raise ToolException("Curator LLM for DeepResearchTool is not available (failed initialization).")
        return self._curator_llm

    async def _arun(
        self,
        topic: str,
        num_initial_sources_to_consider: int = 7, 
        num_sources_to_deep_dive: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any 
    ) -> str:
        # MODIFIED: Import fetch_and_parse_url here to avoid circular import at module level
        from .standard_tools import fetch_and_parse_url

        logger.info(f"DeepResearchTool: Starting deep research for topic: '{topic}'")
        
        # --- Phase 1: Initial Broad Information Gathering ---
        logger.info(f"DeepResearchTool: Phase 1 - Initial Search. Aiming for ~{num_initial_sources_to_consider} sources.")
        internal_tavily_tool: TavilyAPISearchTool
        try:
            internal_tavily_tool = self._get_internal_tavily_tool()
        except ToolException as e:
            return f"Error: Search sub-tool (Tavily) is not available. {e}"

        initial_search_results_data: Union[List[Dict[str, Any]], str]
        try:
            tavily_input_dict = {"query": topic, "max_results": num_initial_sources_to_consider}
            initial_search_results_data = await internal_tavily_tool.arun(
                tavily_input_dict, 
                callbacks=run_manager.get_child() if run_manager else None
            )
            if not isinstance(initial_search_results_data, list):
                logger.warning(f"DeepResearchTool: Tavily search did not return a list. Output: {str(initial_search_results_data)[:300]}")
                return f"Initial web search failed or returned unexpected data: {str(initial_search_results_data)[:300]}"
            logger.info(f"DeepResearchTool: Initial Tavily search completed. Received {len(initial_search_results_data)} structured results.")
        except Exception as e:
            logger.error(f"DeepResearchTool: Error during initial Tavily search for '{topic}': {e}", exc_info=True)
            return f"An unexpected error occurred during the initial research phase: {e}"

        if not initial_search_results_data:
            return f"Initial research phase for '{topic}' yielded no search results. Cannot proceed."

        # --- Phase 2: Source Curation & Selection ---
        logger.info(f"DeepResearchTool: Phase 2 - Source Curation. Selecting top {num_sources_to_deep_dive} sources.")
        curator_llm: BaseChatModel
        try:
            curator_llm = self._get_curator_llm()
        except ToolException as e:
            return f"Error: Curator LLM not available for source selection. {e}"

        formatted_search_results_for_prompt = ""
        for i, res_item in enumerate(initial_search_results_data):
            title = res_item.get("title", "N/A")
            url = res_item.get("url", "N/A")
            snippet = res_item.get("content", "N/A") 
            formatted_search_results_for_prompt += f"Result {i+1}:\nTitle: {title}\nURL: {url}\nSnippet: {snippet}\n---\n"
        
        curator_parser = JsonOutputParser(pydantic_object=CuratedSourcesOutput)
        curator_prompt = ChatPromptTemplate.from_messages([
            ("system", CURATOR_SYSTEM_PROMPT_TEMPLATE),
            ("human", "Please select the best sources from these results:\n\n{search_results_text}")
        ])
        curator_chain = curator_prompt | curator_llm | curator_parser
        curated_urls: List[str] = []
        try:
            logger.info(f"DeepResearchTool: Invoking Curator LLM to select sources.")
            curation_output = await curator_chain.ainvoke({
                "topic": topic,
                "num_sources_to_deep_dive": num_sources_to_deep_dive,
                "search_results_text": formatted_search_results_for_prompt,
                "format_instructions": curator_parser.get_format_instructions(),
            })
            if isinstance(curation_output, CuratedSourcesOutput):
                 curated_urls = curation_output.selected_urls
            elif isinstance(curation_output, dict) and "selected_urls" in curation_output:
                 curated_urls = curation_output["selected_urls"]
            else:
                logger.error(f"DeepResearchTool: Curator LLM returned unexpected output format: {type(curation_output)} - {str(curation_output)[:300]}")
                return "Error: Source curation failed due to unexpected LLM output format."
            if not curated_urls:
                logger.warning("DeepResearchTool: Curator LLM did not select any URLs.")
                return f"Source curation for '{topic}' did not yield any URLs to proceed with."
            logger.info(f"DeepResearchTool: Curator LLM selected {len(curated_urls)} URLs for deep dive: {curated_urls}")
        except Exception as e:
            logger.error(f"DeepResearchTool: Error during source curation LLM call for '{topic}': {e}", exc_info=True)
            return f"An error occurred during source curation: {e}"
        
        # --- Phase 3: Deep Content Extraction ---
        logger.info(f"DeepResearchTool: Phase 3 - Deep Content Extraction from {len(curated_urls)} sources.")
        extracted_content_list: List[Dict[str, Any]] = []
        if not curated_urls:
            logger.warning("DeepResearchTool: No URLs were curated. Skipping content extraction.")
        else:
            for i, url_to_read in enumerate(curated_urls):
                logger.info(f"DeepResearchTool: Extracting content from URL {i+1}/{len(curated_urls)}: {url_to_read}")
                try:
                    page_content = await fetch_and_parse_url(url_to_read)
                    if page_content.startswith("Error:"):
                        logger.warning(f"DeepResearchTool: Failed to read content from {url_to_read}: {page_content}")
                        extracted_content_list.append({"url": url_to_read, "status": "error", "content": page_content})
                    else:
                        logger.info(f"DeepResearchTool: Successfully extracted content from {url_to_read} (length: {len(page_content)}).")
                        extracted_content_list.append({"url": url_to_read, "status": "success", "content": page_content})
                except Exception as e:
                    logger.error(f"DeepResearchTool: Unexpected error reading URL {url_to_read}: {e}", exc_info=True)
                    extracted_content_list.append({"url": url_to_read, "status": "error", "content": f"Unexpected error: {e}"})
                await asyncio.sleep(0.5) 

        successfully_extracted_count = sum(1 for item in extracted_content_list if item["status"] == "success")
        logger.info(f"DeepResearchTool: Content extraction phase complete. Successfully extracted content from {successfully_extracted_count}/{len(curated_urls)} URLs.")
        
        return (f"Deep research for '{topic}': Initial search found {len(initial_search_results_data)} sources. "
                f"Curator selected {len(curated_urls)} URLs. "
                f"Content extraction attempted for {len(curated_urls)} URLs, succeeded for {successfully_extracted_count}. "
                f"Next step: Information Synthesis.")

    def _run(self, topic: str, num_initial_sources_to_consider: int = 7, num_sources_to_deep_dive: int = 3, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any ) -> str:
        try:
            loop = asyncio.get_event_loop_policy().get_event_loop()
            if loop.is_running():
                logger.warning("DeepResearchTool._run called from within a running event loop.")
                future = asyncio.run_coroutine_threadsafe(
                    self._arun(topic=topic, num_initial_sources_to_consider=num_initial_sources_to_consider, num_sources_to_deep_dive=num_sources_to_deep_dive, run_manager=run_manager, **kwargs), 
                    loop
                )
                return future.result(timeout=300) 
            else:
                return asyncio.run(self._arun(
                    topic=topic, 
                    num_initial_sources_to_consider=num_initial_sources_to_consider,
                    num_sources_to_deep_dive=num_sources_to_deep_dive,
                    run_manager=run_manager, **kwargs
                ))
        except Exception as e:
            logger.error(f"DeepResearchTool (_run): Error trying to run async from sync: {e}", exc_info=True)
            return f"Error in sync execution wrapper: {e}"

async def main(): 
    if not (hasattr(settings, 'tavily_api_key') and settings.tavily_api_key):
        print("Test SKIPPED: settings.tavily_api_key not found or not set for DeepResearchTool test.", flush=True)
        return

    print("\n--- Testing DeepResearchTool (Phases 1-3: Search, Curation, Extraction) ---", flush=True)
    
    deep_research_tool_instance = None
    try:
        print("Test: Instantiating DeepResearchTool...", flush=True)
        deep_research_tool_instance = DeepResearchTool()
        print("Test: DeepResearchTool instantiated.", flush=True)
        
        if deep_research_tool_instance._tavily_search_tool_instance is None:
            print("Test CRITICAL: DeepResearchTool's internal Tavily tool FAILED to initialize. Check __init__ logs.", flush=True)
            return 
        if deep_research_tool_instance._curator_llm is None:
            print("Test CRITICAL: DeepResearchTool's internal Curator LLM FAILED to initialize. Check __init__ logs.", flush=True)
            return

        test_topic = "Recent breakthroughs in quantum entanglement for communication"
        num_initial = 5 
        num_to_dive = 2 
        print(f"Test Topic: '{test_topic}', num_initial_sources: {num_initial}, num_to_deep_dive: {num_to_dive}", flush=True)
        
        results = await deep_research_tool_instance.arun({ 
            "topic": test_topic,
            "num_initial_sources_to_consider": num_initial,
            "num_sources_to_deep_dive": num_to_dive
        })
        
        print("\nDeepResearchTool Output:")
        print(results, flush=True)

    except Exception as e:
        print(f"Error during DeepResearchTool test: {type(e).__name__} - {e}", flush=True)
        traceback.print_exc()
    print("---------------------------------------------", flush=True)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
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
    
    asyncio.run(main())
