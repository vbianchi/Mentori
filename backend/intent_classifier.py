import logging
from typing import Dict, Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field # Assuming pydantic_v1 for now, adjust if project migrates

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
    - "Tell me a joke."
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
    llm: BaseChatModel,
    available_tools_summary: Optional[str] = None # Optional, but can provide context
) -> str:
    """
    Classifies the user's intent as either requiring a plan or direct Q&A.

    Args:
        user_query: The user's input query.
        llm: The language model instance to use for classification.
        available_tools_summary: An optional summary of available tools for context.

    Returns:
        A string representing the classified intent (e.g., "PLAN", "DIRECT_QA").
        Defaults to "PLAN" if classification fails or is uncertain.
    """
    logger.info(f"IntentClassifier: Classifying intent for query: {user_query[:100]}...")

    parser = JsonOutputParser(pydantic_object=IntentClassificationOutput)
    format_instructions = parser.get_format_instructions()

    # Constructing the human message part of the prompt
    human_message_content_parts = [f"User Query: \"{user_query}\""]
    if available_tools_summary:
        human_message_content_parts.append(f"\nFor context, the agent has access to tools like: {available_tools_summary}")
    human_message_content_parts.append("\nClassify the intent of the user query.")
    human_message_content = "\n".join(human_message_content_parts)

    prompt = ChatPromptTemplate.from_messages([
        ("system", INTENT_CLASSIFIER_SYSTEM_PROMPT_TEMPLATE),
        ("human", human_message_content)
    ])

    chain = prompt | llm | parser

    try:
        # Provide all required variables for the prompt template
        # The system prompt template uses 'format_instructions'
        # The human prompt template uses 'user_query' and optionally 'available_tools_summary' (handled by f-string)
        # So, the chain.ainvoke needs 'format_instructions' and 'user_query' (and 'available_tools_summary' if it were a direct template var)
        # However, since we construct human_message_content directly, we only need to ensure format_instructions is available for the system prompt.
        # The user_query is part of the human_message_content.
        
        # If ChatPromptTemplate.from_messages is used with f-string formatting within the messages,
        # the variables are already embedded. If it expects explicit variables, they must be passed.
        # For `from_messages([("system", sys_template_str), ("human", human_template_str)])`
        # it expects variables named in the template strings.
        # Here, format_instructions is in the system prompt. user_query is in the human prompt.
        
        # Let's ensure the prompt is constructed correctly for the variables.
        # The system prompt expects "format_instructions".
        # The human prompt is a direct string here, not a template expecting "user_query".
        # To make it cleaner, let's make the human part also a template string.

        human_template = "User Query: \"{user_query}\"\n"
        if available_tools_summary:
            human_template += "\nFor context, the agent has access to tools like: {available_tools_summary}\n"
        human_template += "\nClassify the intent of the user query."

        prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_CLASSIFIER_SYSTEM_PROMPT_TEMPLATE),
            ("human", human_template)
        ])
        chain = prompt | llm | parser # Recreate chain with the new prompt

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
        # Fallback to "PLAN" in case of any error to be safe
        return "PLAN"

if __name__ == '__main__':
    # Example Usage (requires async setup and a mock/real LLM)
    async def test_intent_classifier():
        # This is a placeholder. You'd need to initialize a BaseChatModel (e.g., from llm_setup)
        # and potentially mock settings if get_llm relies on them.
        class MockLLM(BaseChatModel):
            def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                # Simulate LLM response for testing
                intent_response = IntentClassificationOutput(intent="DIRECT_QA", reasoning="Simple question.").json()
                # intent_response = IntentClassificationOutput(intent="PLAN", reasoning="Complex multi-step query.").json()
                return {"generations": [{"text": intent_response}]} # Simplified, actual structure might vary
            async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
                intent_response_json = IntentClassificationOutput(intent="DIRECT_QA", reasoning="Simple question for test.").json()
                # Example for PLAN
                # intent_response_json = IntentClassificationOutput(intent="PLAN", reasoning="Complex query requiring multiple steps for test.").json()
                
                # Simulate the structure that JsonOutputParser expects after LLM call
                # Usually, the LLM's AIMessage content is the JSON string.
                # The parser then takes this string.
                # Here, we directly provide the dict that the parser would produce.
                # For a real LLM, the chain would be: prompt | llm | StrOutputParser() | JsonOutputParser()
                # or prompt | llm (if it outputs JSON directly) | JsonOutputParser()
                
                # Let's simulate what the JsonOutputParser would get from the LLM
                # The LLM (after prompt) would output a message, whose content is the JSON string.
                # The parser then parses this string.
                # For testing the chain `prompt | llm | parser`, the llm mock needs to return an AIMessage
                # whose content is the JSON string.
                from langchain_core.messages import AIMessage
                return AIMessage(content=intent_response_json)


        mock_llm_instance = MockLLM()
        
        queries = [
            "What is photosynthesis?",
            "Find three articles about dark matter, summarize them, and create a presentation.",
            "Tell me a fun fact.",
            "Download the latest sales report, analyze the Q3 data, and generate a bar chart for regional performance."
        ]
        
        tools_summary_example = "- duckduckgo_search: For web searches.\n- write_file: To write files."

        for q in queries:
            intent = await classify_intent(q, mock_llm_instance, tools_summary_example)
            print(f"Query: \"{q}\" -> Classified Intent: {intent}")

    asyncio.run(test_intent_classifier())

