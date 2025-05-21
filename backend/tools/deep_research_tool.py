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
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.language_models.chat_models import BaseChatModel


from .tavily_search_tool import TavilyAPISearchTool
# fetch_and_parse_url will be imported inside _arun to avoid circular import

from backend.config import settings 
from backend.llm_setup import get_llm 

logger = logging.getLogger(__name__)

# --- Input/Output Schemas ---
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
    desired_report_sections: Optional[List[str]] = Field(
        default=None,
        description="Optional list of desired section titles for the final report, e.g., ['Introduction', 'Key Findings', 'Methodology']."
    )
    max_tokens_per_summary: int = Field(
        default=1500, 
        description="Maximum tokens to aim for when summarizing individual source texts if they are too long."
    )
    max_total_tokens_for_writer: int = Field(
        default=100000, 
        description="Maximum total tokens from (summarized) content to pass to the final report writer LLM."
    )

    # MODIFIED: Add model_json_schema method for Pydantic v2 compatibility
    @classmethod
    def model_json_schema(cls, by_alias: bool = True, ref_template: str = "#/components/schemas/{model}") -> Dict[str, Any]:
        """
        Generates the JSON schema for the Pydantic model.
        This is the Pydantic v2 method name, but we call the v1 equivalent.
        """
        return cls.schema(by_alias=by_alias) # Pydantic v1 uses .schema()

class CuratedSourcesOutput(BaseModel):
    selected_urls: List[str] = Field(description="A list of URLs selected as most promising for deep research.")
    reasoning: Optional[str] = Field(default=None, description="Brief reasoning for the selection (optional).")

    @validator('selected_urls', each_item=True)
    def check_url_format(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Each URL must start with http:// or https://')
        return v

class ReportSection(BaseModel):
    section_title: str = Field(description="The title of this section of the report.")
    section_content: str = Field(description="The Markdown content of this section.")

class DeepResearchReportOutput(BaseModel):
    report_title: str = Field(description="The main title for the research report.")
    executive_summary: str = Field(description="A concise executive summary of the entire report.")
    sections: List[ReportSection] = Field(description="A list of sections, each with a title and content.")

CURATOR_SYSTEM_PROMPT_TEMPLATE = """
You are an expert Research Assistant acting as a Source Curator.
Your task is to analyze a list of web search results (including titles, URLs, and snippets)
and select the most promising and authoritative sources for a deep research report on a given topic.
Topic for the report: "{topic}"
You need to select the top {num_sources_to_deep_dive} URLs.
Prioritize: Primary research, reputable institutions, comprehensive reviews, official reports. Relevance and substance are key.
Avoid: Forums, social media, minor blogs, brief news unless exceptionally relevant. Avoid duplicates or paywalled sites if good alternatives exist.
Respond with a single JSON object matching the following schema: {format_instructions}
Do not include any preamble or explanation outside of the JSON object.
"""

SUMMARIZER_SYSTEM_PROMPT_TEMPLATE = """
You are an expert Research Summarizer. Your task is to read the following text extracted from a web page
and create a concise, factual summary focusing on information relevant to the main research topic: "{topic}".
The summary should highlight key findings, arguments, data points, and examples.
Aim for a summary of approximately {max_tokens_per_summary} tokens (roughly {max_words_per_summary} words).
Ensure the summary is neutral, objective, and based ONLY on the provided text.
Do not add external information or opinions. Output the summary directly as plain text.

Provided Text:
---
{text_to_summarize}
---
Summary:
"""

WRITER_SYSTEM_PROMPT_TEMPLATE = """
You are an expert Research Report Writer. Your task is to synthesize the provided information 
(which may be full texts or summaries from various web sources) into a comprehensive and well-structured 
Markdown report on the topic: "{topic}".

Your report MUST be based ONLY on the "Provided Content" below. Do NOT use any external knowledge or make up information.

Report Structure:
1.  Start with an "Executive Summary" that concisely overviews the main findings.
2.  If `desired_report_sections` are provided (see below), use them. Otherwise, create logical sections based on the content.
    Common sections might include: Introduction, Key Findings, Different Perspectives/Arguments, Methodologies (if applicable), Limitations, and Future Outlook/Conclusion.
3.  For each section, synthesize information from the relevant provided content. Cite multiple sources if they discuss the same point.
4.  Maintain a neutral, objective, and analytical tone suitable for a research report.
5.  The entire output must be a single JSON object matching the schema: {format_instructions}
    Each section's content should be in Markdown.

Desired Report Sections (if any): {desired_report_sections_str}

Provided Content (Summaries or Full Texts from Web Sources):
---
{synthesized_content_for_writer}
---

Now, generate the research report as a JSON object.
"""

class DeepResearchTool(BaseTool):
    name: str = "deep_research_synthesizer"
    description: str = (
        "Performs an in-depth, multi-step research investigation on a given topic. "
        "It conducts a broad web search, curates top sources, then extracts content from these sources, "
        "summarizes if necessary, and synthesizes a comprehensive Markdown report. "
        "Use for complex research questions requiring a detailed overview. "
        "Input is 'topic', optionally 'num_initial_sources_to_consider', 'num_sources_to_deep_dive', "
        "'desired_report_sections', 'max_tokens_per_summary', and 'max_total_tokens_for_writer'."
    )
    args_schema: Type[BaseModel] = DeepResearchToolInput
    
    _tavily_search_tool_instance: Optional[TavilyAPISearchTool] = Field(default=None, exclude=True)
    _curator_llm: Optional[BaseChatModel] = Field(default=None, exclude=True)
    _summarizer_llm: Optional[BaseChatModel] = Field(default=None, exclude=True)
    _writer_llm: Optional[BaseChatModel] = Field(default=None, exclude=True)

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
            logger.info(f"{init_log_prefix} Initializing Curator LLM (uses Planner settings: {settings.planner_provider}::{settings.planner_model_name}).")
            self._curator_llm = get_llm(settings, provider=settings.planner_provider, model_name=settings.planner_model_name, requested_for_role="DeepResearch_Curator")
            
            logger.info(f"{init_log_prefix} Initializing Summarizer LLM (uses Executor default settings: {settings.executor_default_provider}::{settings.executor_default_model_name}).")
            self._summarizer_llm = get_llm(settings, provider=settings.executor_default_provider, model_name=settings.executor_default_model_name, requested_for_role="DeepResearch_Summarizer")

            logger.info(f"{init_log_prefix} Initializing Writer LLM (uses Evaluator settings: {settings.evaluator_provider}::{settings.evaluator_model_name}).")
            self._writer_llm = get_llm(settings, provider=settings.evaluator_provider, model_name=settings.evaluator_model_name, requested_for_role="DeepResearch_Writer")
            
            logger.info(f"{init_log_prefix} All internal LLMs initialized (or attempted).")
        except Exception as e:
            logger.error(f"{init_log_prefix} Failed to initialize one or more internal LLMs: {e}", exc_info=True)
        
        logger.info(f"{init_log_prefix} EXITING __init__.")
    
    def _get_internal_tavily_tool(self) -> TavilyAPISearchTool:
        if self._tavily_search_tool_instance is None:
            raise ToolException("Internal Tavily Search sub-tool for DeepResearchTool is not available (failed initialization or no API key).")
        return self._tavily_search_tool_instance

    def _get_curator_llm(self) -> BaseChatModel:
        if self._curator_llm is None:
            raise ToolException("Curator LLM for DeepResearchTool is not available (failed initialization).")
        return self._curator_llm

    def _get_summarizer_llm(self) -> BaseChatModel:
        if self._summarizer_llm is None:
            raise ToolException("Summarizer LLM for DeepResearchTool is not available.")
        return self._summarizer_llm

    def _get_writer_llm(self) -> BaseChatModel:
        if self._writer_llm is None:
            raise ToolException("Writer LLM for DeepResearchTool is not available.")
        return self._writer_llm

    async def _summarize_content(self, topic: str, text_to_summarize: str, max_tokens: int, url:str) -> str:
        summarizer_llm = self._get_summarizer_llm()
        max_words = max_tokens // 3 if max_tokens > 100 else 250 
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SUMMARIZER_SYSTEM_PROMPT_TEMPLATE),
        ])
        chain = prompt | summarizer_llm | StrOutputParser()
        logger.info(f"DeepResearchTool: Summarizing content from {url} (target ~{max_words} words, max_tokens for summary: {max_tokens}). Input text length: {len(text_to_summarize)}")
        try:
            max_input_chars_for_summarizer = max_tokens * 10 
            summary = await chain.ainvoke({
                "topic": topic,
                "text_to_summarize": text_to_summarize[:max_input_chars_for_summarizer], 
                "max_tokens_per_summary": max_tokens, 
                "max_words_per_summary": max_words    
            })
            logger.info(f"DeepResearchTool: Content from {url} summarized (output length: {len(summary)}).")
            return summary
        except Exception as e:
            logger.error(f"DeepResearchTool: Error summarizing content from {url}: {e}", exc_info=True)
            return f"Error summarizing content from {url}. Original content snippet (first 500 chars): {text_to_summarize[:500]}..."

    async def _arun(
        self,
        topic: str,
        num_initial_sources_to_consider: int = 7, 
        num_sources_to_deep_dive: int = 3,
        desired_report_sections: Optional[List[str]] = None,
        max_tokens_per_summary: int = 1500,
        max_total_tokens_for_writer: int = 100000, 
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any 
    ) -> str:
        from .standard_tools import fetch_and_parse_url 

        logger.info(f"DeepResearchTool: Starting deep research for topic: '{topic}'")
        
        # --- Phase 1: Initial Broad Information Gathering ---
        logger.info(f"DeepResearchTool: Phase 1 - Initial Search. Aiming for ~{num_initial_sources_to_consider} sources.")
        internal_tavily_tool: TavilyAPISearchTool
        try: internal_tavily_tool = self._get_internal_tavily_tool()
        except ToolException as e: return f"Error: Search sub-tool (Tavily) is not available. {e}"
        initial_search_results_data: Union[List[Dict[str, Any]], str]
        try:
            tavily_input_dict = {"query": topic, "max_results": num_initial_sources_to_consider}
            initial_search_results_data = await internal_tavily_tool.arun(
                tavily_input_dict, callbacks=run_manager.get_child() if run_manager else None
            )
            if not isinstance(initial_search_results_data, list):
                logger.warning(f"Tavily search did not return a list. Output: {str(initial_search_results_data)[:300]}")
                return f"Initial web search failed or returned unexpected data: {str(initial_search_results_data)[:300]}"
            logger.info(f"Initial Tavily search completed. Received {len(initial_search_results_data)} structured results.")
        except Exception as e:
            logger.error(f"Error during initial Tavily search for '{topic}': {e}", exc_info=True)
            return f"An unexpected error occurred during the initial research phase: {e}"
        if not initial_search_results_data:
            return f"Initial research phase for '{topic}' yielded no search results. Cannot proceed."

        # --- Phase 2: Source Curation & Selection ---
        logger.info(f"DeepResearchTool: Phase 2 - Source Curation. Selecting top {num_sources_to_deep_dive} sources.")
        curator_llm: BaseChatModel
        try: curator_llm = self._get_curator_llm()
        except ToolException as e: return f"Error: Curator LLM not available for source selection. {e}"
        formatted_search_results_for_prompt = ""
        for i, res_item in enumerate(initial_search_results_data):
            if isinstance(res_item, dict):
                title = res_item.get("title", "N/A"); url = res_item.get("url", "N/A"); snippet = res_item.get("content", "N/A") 
                formatted_search_results_for_prompt += f"Result {i+1}:\nTitle: {title}\nURL: {url}\nSnippet: {snippet}\n---\n"
        if not formatted_search_results_for_prompt: return "Error: No valid initial search results to process for curation."
        curator_parser = JsonOutputParser(pydantic_object=CuratedSourcesOutput)
        curator_prompt = ChatPromptTemplate.from_messages([("system", CURATOR_SYSTEM_PROMPT_TEMPLATE), ("human", "Please select the best sources from these results:\n\n{search_results_text}")])
        curator_chain = curator_prompt | curator_llm | curator_parser
        curated_urls: List[str] = []
        try:
            logger.info(f"Invoking Curator LLM to select sources.")
            actual_num_to_dive = max(1, min(num_sources_to_deep_dive, len(initial_search_results_data)))
            curation_output_dict = await curator_chain.ainvoke({"topic": topic, "num_sources_to_deep_dive": actual_num_to_dive, "search_results_text": formatted_search_results_for_prompt, "format_instructions": curator_parser.get_format_instructions()})
            if isinstance(curation_output_dict, dict) and "selected_urls" in curation_output_dict and isinstance(curation_output_dict["selected_urls"], list):
                 curated_urls = curation_output_dict["selected_urls"]
            else: logger.error(f"Curator LLM returned unexpected output: {type(curation_output_dict)} - {str(curation_output_dict)[:300]}"); return "Error: Source curation failed (LLM output)."
            if not curated_urls: logger.warning("Curator LLM did not select any URLs."); return f"Source curation for '{topic}' did not yield any URLs."
            logger.info(f"Curator LLM selected {len(curated_urls)} URLs: {curated_urls}")
        except Exception as e: logger.error(f"Error during source curation LLM call for '{topic}': {e}", exc_info=True); return f"An error occurred during source curation: {e}"
        
        # --- Phase 3: Deep Content Extraction ---
        logger.info(f"DeepResearchTool: Phase 3 - Deep Content Extraction from {len(curated_urls)} sources.")
        extracted_content_list: List[Dict[str, Any]] = []
        if curated_urls:
            for i, url_to_read in enumerate(curated_urls):
                logger.info(f"Extracting content from URL {i+1}/{len(curated_urls)}: {url_to_read}")
                try:
                    page_content = await fetch_and_parse_url(url_to_read) 
                    status = "error" if page_content.startswith("Error:") else "success"
                    extracted_content_list.append({"url": url_to_read, "status": status, "content": page_content})
                    if status == "success": logger.info(f"Successfully extracted content from {url_to_read} (length: {len(page_content)}).")
                    else: logger.warning(f"Failed to read content from {url_to_read}: {page_content}")
                except Exception as e: logger.error(f"Unexpected error reading URL {url_to_read}: {e}", exc_info=True); extracted_content_list.append({"url": url_to_read, "status": "error", "content": f"Unexpected error: {e}"})
                await asyncio.sleep(0.5) 
        successfully_extracted_sources = [item for item in extracted_content_list if item["status"] == "success"]
        logger.info(f"Content extraction complete. Successfully extracted content from {len(successfully_extracted_sources)}/{len(curated_urls)} URLs.")
        if not successfully_extracted_sources:
            return f"Deep research for '{topic}' failed: No content could be extracted from the curated sources."

        # --- Phase 4: Summarization (if needed) & Synthesis ---
        logger.info("DeepResearchTool: Phase 4 - Content Summarization & Synthesis.")
        content_for_writer = []
        estimated_total_chars = sum(len(source_data["content"]) for source_data in successfully_extracted_sources)
        estimated_total_tokens = estimated_total_chars / 4 
        logger.info(f"DeepResearchTool: Estimated total tokens from full texts: ~{int(estimated_total_tokens)} (based on {estimated_total_chars} chars). Max for writer: {max_total_tokens_for_writer}.")

        if estimated_total_tokens > max_total_tokens_for_writer:
            logger.warning(f"DeepResearchTool: Total estimated tokens ({int(estimated_total_tokens)}) for full texts exceeds writer limit ({max_total_tokens_for_writer}). Summarizing individual sources.")
            summarized_content_for_writer = []
            current_summarized_token_estimate = 0
            for source_data in successfully_extracted_sources:
                if current_summarized_token_estimate + (max_tokens_per_summary * 1.2) < max_total_tokens_for_writer: 
                    summary = await self._summarize_content(topic, source_data["content"], max_tokens_per_summary, source_data["url"])
                    if not summary.startswith("Error summarizing content"):
                        summarized_content_for_writer.append({"url": source_data["url"], "text": summary, "type": "summary"})
                        current_summarized_token_estimate += len(summary) / 4 
                    else:
                        logger.warning(f"Skipping failed summary for {source_data['url']}")
                else:
                    logger.warning(f"DeepResearchTool: Skipping further summaries for {source_data['url']} to stay within total token limit for writer.")
                    break 
            content_for_writer = summarized_content_for_writer
            logger.info(f"DeepResearchTool: Summarization phase complete. Using {len(content_for_writer)} summaries. New estimated token count for writer: ~{int(current_summarized_token_estimate)}")
        else:
            logger.info(f"DeepResearchTool: Total estimated tokens ({int(estimated_total_tokens)}) is within limit. Using full extracted texts for writer.")
            for source_data in successfully_extracted_sources:
                 content_for_writer.append({"url": source_data["url"], "text": source_data["content"], "type": "full_text"})
        
        if not content_for_writer:
             return f"Deep research for '{topic}' failed: No content available for synthesis after summarization/filtering."

        synthesized_content_str_for_prompt = ""
        for i, item in enumerate(content_for_writer):
            synthesized_content_str_for_prompt += f"--- Source {i+1} (Type: {item['type']}, URL: {item['url']}) ---\n{item['text']}\n--- End Source {i+1} ---\n\n"

        writer_llm = self._get_writer_llm()
        writer_parser = JsonOutputParser(pydantic_object=DeepResearchReportOutput) 
        writer_prompt = ChatPromptTemplate.from_messages([
            ("system", WRITER_SYSTEM_PROMPT_TEMPLATE),
            ("human", "Based on the provided system instructions and content, please generate the research report now.")
        ])
        writer_chain = writer_prompt | writer_llm | writer_parser

        logger.info(f"DeepResearchTool: Invoking Report Writer LLM with content from {len(content_for_writer)} sources.")
        try:
            report_data_dict = await writer_chain.ainvoke({
                "topic": topic,
                "desired_report_sections_str": ", ".join(desired_report_sections) if desired_report_sections else "Not specified by user; use logical sections based on content.",
                "synthesized_content_for_writer": synthesized_content_str_for_prompt.strip(),
                "format_instructions": writer_parser.get_format_instructions()
            })
            
            if not isinstance(report_data_dict, dict): 
                logger.error(f"Writer LLM chain returned non-dict: {type(report_data_dict)}. Output: {str(report_data_dict)[:500]}")
                raise ToolException("Report writer returned unexpected data type.")

            report_output = DeepResearchReportOutput(**report_data_dict)

            final_markdown_report = f"# {report_output.report_title}\n\n"
            final_markdown_report += f"## Executive Summary\n{report_output.executive_summary}\n\n"
            for section in report_output.sections:
                final_markdown_report += f"## {section.section_title}\n{section.section_content}\n\n"
            
            final_markdown_report += "## Sources Consulted\n"
            unique_urls_used = {item['url'] for item in content_for_writer} 
            for url_used in sorted(list(unique_urls_used)): 
                final_markdown_report += f"- <{url_used}>\n"

            logger.info(f"DeepResearchTool: Report synthesis complete for topic '{topic}'.")
            return final_markdown_report

        except Exception as e:
            logger.error(f"DeepResearchTool: Error during report synthesis LLM call for '{topic}': {e}", exc_info=True)
            raw_writer_output_attempt = "Could not retrieve raw output due to earlier error or parsing failure."
            if isinstance(e, (json.JSONDecodeError, TypeError)) or "Failed to parse" in str(e).lower() or "Expecting value" in str(e) or "contents is not specified" in str(e): 
                 try:
                    logger.info("Attempting to get raw string output from Writer LLM due to parsing or API error...")
                    raw_writer_output_attempt = await (writer_prompt | writer_llm | StrOutputParser()).ainvoke({
                         "topic": topic,
                         "desired_report_sections_str": ", ".join(desired_report_sections) if desired_report_sections else "Not specified",
                         "synthesized_content_for_writer": synthesized_content_str_for_prompt.strip(),
                         "format_instructions": writer_parser.get_format_instructions() 
                    })
                    logger.error(f"DeepResearchTool: Raw output from Writer LLM on failure: {raw_writer_output_attempt[:1000]}...")
                    return f"Error during final report synthesis (LLM output issue or API error). Raw LLM output started with: {raw_writer_output_attempt[:200]}..."
                 except Exception as raw_e:
                    logger.error(f"DeepResearchTool: Could not get raw output from Writer LLM after parsing failure: {raw_e}")
            return f"An error occurred during the final report synthesis: {type(e).__name__} - {e}. Last attempt to get raw output: {raw_writer_output_attempt[:200]}"


    def _run(self, topic: str, num_initial_sources_to_consider: int = 7, num_sources_to_deep_dive: int = 3, desired_report_sections: Optional[List[str]] = None, max_tokens_per_summary: int = 1500, max_total_tokens_for_writer: int = 100000, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any ) -> str:
        try:
            loop = asyncio.get_event_loop_policy().get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._arun(topic=topic, num_initial_sources_to_consider=num_initial_sources_to_consider, num_sources_to_deep_dive=num_sources_to_deep_dive, desired_report_sections=desired_report_sections, max_tokens_per_summary=max_tokens_per_summary, max_total_tokens_for_writer=max_total_tokens_for_writer, run_manager=run_manager, **kwargs), 
                    loop
                )
                return future.result(timeout=600) 
            else:
                return asyncio.run(self._arun(
                    topic=topic, 
                    num_initial_sources_to_consider=num_initial_sources_to_consider,
                    num_sources_to_deep_dive=num_sources_to_deep_dive,
                    desired_report_sections=desired_report_sections,
                    max_tokens_per_summary=max_tokens_per_summary,
                    max_total_tokens_for_writer=max_total_tokens_for_writer,
                    run_manager=run_manager, **kwargs
                ))
        except Exception as e:
            logger.error(f"DeepResearchTool (_run): Error trying to run async from sync: {e}", exc_info=True)
            return f"Error in sync execution wrapper: {e}"

async def main(): 
    if not (hasattr(settings, 'tavily_api_key') and settings.tavily_api_key):
        print("Test SKIPPED: settings.tavily_api_key not found or not set for DeepResearchTool test.", flush=True)
        return

    print("\n--- Testing DeepResearchTool (Full Workflow) ---", flush=True)
    
    deep_research_tool_instance = None
    try:
        print("Test: Instantiating DeepResearchTool...", flush=True)
        deep_research_tool_instance = DeepResearchTool()
        print("Test: DeepResearchTool instantiated.", flush=True)
        
        if deep_research_tool_instance._tavily_search_tool_instance is None:
            print("Test CRITICAL: DeepResearchTool's internal Tavily tool FAILED to initialize.", flush=True)
            return 
        if deep_research_tool_instance._curator_llm is None:
            print("Test CRITICAL: DeepResearchTool's internal Curator LLM FAILED to initialize.", flush=True)
            return
        if deep_research_tool_instance._summarizer_llm is None:
            print("Test CRITICAL: DeepResearchTool's internal Summarizer LLM FAILED to initialize.", flush=True)
            return
        if deep_research_tool_instance._writer_llm is None:
            print("Test CRITICAL: DeepResearchTool's internal Writer LLM FAILED to initialize.", flush=True)
            return

        test_topic = "Impact of AI on scientific research methodology"
        num_initial = 5
        num_to_dive = 2
        
        print(f"Test Topic: '{test_topic}', num_initial_sources: {num_initial}, num_to_deep_dive: {num_to_dive}", flush=True)
        
        results = await deep_research_tool_instance.arun({ 
            "topic": test_topic,
            "num_initial_sources_to_consider": num_initial,
            "num_sources_to_deep_dive": num_to_dive,
            "max_tokens_per_summary": 500, 
            "max_total_tokens_for_writer": 40000 
        })
        
        print("\nDeepResearchTool Final Report Output:")
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
