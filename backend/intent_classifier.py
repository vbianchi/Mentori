import logging
from typing import Dict, Any, Optional

# MODIFIED: Import settings and get_llm
from backend.config import settings
from backend.llm_setup import get_llm
from langchain_core.language_models.chat_models import BaseChatModel # Still needed for type hinting if get_llm returns it
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field 
import asyncio # For the test block

logger = logging.getLogger(__name__)

class IntentClassificationOutput(BaseModel):
    """
    Defines the structured output for the Intent Classifier LLM.
    """
    intent: str = Field(description="The classified intent. Must be one of ['PLAN', 'DIRECT_QA'].")
    reasoning: Optional[str] = Field(description="Brief reasoning for the classification.", default=None)

INTENT_CLASSIFIER_SYSTEM_PROMPT_TEMPLATE = """You are an expert AI assistant responsible for classifying user intent.
Your goal is to determine if a user's query requires a multi-step plan involving tools and complex reasoning, or if it's a simple question/statement that can be answered directly or via a single tool use (like a quick web search).

Available intents:
-   "PLAN": Use this if the query implies a multi-step process, requires breaking down into sub-tasks, involves creating or manipulating multiple pieces of data, or clearly needs a sequence of tool uses. Examples:
    - "Research the latest treatments for X, summarize them, and write a report."
    - "Find three recent news articles about Y, extract key points from each, and compare them."
    - "Download the data from Z, process it, and generate a plot."
-   "DIRECT_QA": Use this if the query is a straightforward question, a request for a simple definition or explanation, a request for brainstorming, a simple calculation, or a conversational remark that doesn't require a complex plan. The agent can likely answer this using its internal knowledge or a single quick tool use (like a web search for a current fact). Examples:
    - "What is the capital of France?"
    - "Explain the concept of X in simple terms."
    - "Tell me a fun fact."
    - "What's the weather like today?" (implies a single tool use)
    - "Can you help me brainstorm ideas for a project about Y?"
    - "Thanks, that was helpful!"

Consider the complexity and the likely number of distinct operations or tool uses implied by the query.

Respond with a single JSON object matching the following schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object.
"""

async def classify_intent(
    user_query: str,
    # MODIFIED: Removed llm as an argument, it will be fetched internally
    available_tools_summary: Optional[str] = None 
) -> str:
    """
    Classifies the user's intent as either requiring a plan or direct Q&A.
    It now fetches its own LLM based on settings.

    Args:
        user_query: The user's input query.
        available_tools_summary: An optional summary of available tools for context.

    Returns:
        A string representing the classified intent (e.g., "PLAN", "DIRECT_QA").
        Defaults to "PLAN" if classification fails or is uncertain.
    """
    logger.info(f"IntentClassifier: Classifying intent for query: {user_query[:100]}...")

    # MODIFIED: Get the LLM for intent classification from settings
    try:
        intent_llm: BaseChatModel = get_llm(
            settings, 
            provider=settings.intent_classifier_provider, 
            model_name=settings.intent_classifier_model_name
        ) # type: ignore 
        logger.info(f"IntentClassifier: Using LLM {settings.intent_classifier_provider}::{settings.intent_classifier_model_name}")
    except Exception as e:
        logger.error(f"IntentClassifier: Failed to initialize LLM for intent classification: {e}", exc_info=True)
        logger.warning("IntentClassifier: Defaulting to 'PLAN' intent due to LLM initialization error.")
        return "PLAN"

    parser = JsonOutputParser(pydantic_object=IntentClassificationOutput)
    format_instructions = parser.get_format_instructions()
    
    human_template = "User Query: \"{user_query}\"\n"
    if available_tools_summary:
        human_template += "\nFor context, the agent has access to tools like: {available_tools_summary}\n"
    human_template += "\nClassify the intent of the user query."

    prompt = ChatPromptTemplate.from_messages([
        ("system", INTENT_CLASSIFIER_SYSTEM_PROMPT_TEMPLATE),
        ("human", human_template)
    ])
    chain = prompt | intent_llm | parser

    try:
        invoke_params = {
            "user_query": user_query,
            "format_instructions": format_instructions
        }
        if available_tools_summary:
            invoke_params["available_tools_summary"] = available_tools_summary
            
        classification_result_dict = await chain.ainvoke(invoke_params)

        if isinstance(classification_result_dict, IntentClassificationOutput):
            classified_output = classification_result_dict
        else:
            classified_output = IntentClassificationOutput(**classification_result_dict)

        intent = classified_output.intent.upper()
        reasoning = classified_output.reasoning or "No reasoning provided."
        logger.info(f"IntentClassifier: Classified intent as '{intent}'. Reasoning: {reasoning}")

        if intent in ["PLAN", "DIRECT_QA"]:
            return intent
        else:
            logger.warning(f"IntentClassifier: LLM returned an unknown intent '{intent}'. Defaulting to 'PLAN'.")
            return "PLAN"

    except Exception as e:
        logger.error(f"IntentClassifier: Error during intent classification: {e}", exc_info=True)
        try:
            error_chain = prompt | intent_llm | StrOutputParser() # type: ignore
            raw_output_params = {
                "user_query": user_query,
                "format_instructions": format_instructions
            }
            if available_tools_summary:
                raw_output_params["available_tools_summary"] = available_tools_summary
            raw_output = await error_chain.ainvoke(raw_output_params)
            logger.error(f"IntentClassifier: Raw LLM output on error: {raw_output}")
        except Exception as raw_e:
            logger.error(f"IntentClassifier: Failed to get raw LLM output during error: {raw_e}")
        logger.warning("IntentClassifier: Defaulting to 'PLAN' intent due to classification error.")
        return "PLAN"

if __name__ == '__main__':
    async def test_intent_classifier():
        # This test now relies on settings from config.py for the intent classifier LLM
        # Ensure your .env is configured, especially INTENT_CLASSIFIER_LLM_ID or DEFAULT_LLM_ID
        
        queries = [
            "What is photosynthesis?",
            "Find three articles about dark matter, summarize them, and create a presentation.",
            "Tell me a fun fact.",
            "Download the latest sales report, analyze the Q3 data, and generate a bar chart for regional performance."
        ]
        
        tools_summary_example = "- duckduckgo_search: For web searches.\n- write_file: To write files."

        for q in queries:
            # classify_intent now fetches its own LLM
            intent = await classify_intent(q, tools_summary_example)
            print(f"Query: \"{q}\" -> Classified Intent: {intent}")

    asyncio.run(test_intent_classifier())
