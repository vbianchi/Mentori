import logging
from typing import List, Dict, Any, Tuple, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from backend.planner import PlanStep # Assuming PlanStep is in backend.planner

logger = logging.getLogger(__name__)

class ValidatedStepAction(BaseModel):
    """
    Defines the structured output for the Controller/Validator LLM.
    It specifies the tool to use and the precise input for that tool.
    """
    tool_name: Optional[str] = Field(description="The exact name of the tool to be used for this step. Must be one of the available tools or 'None' if no tool is directly applicable for this step (e.g., the step is purely analytical or relies on the LLM's internal knowledge).")
    tool_input: Optional[str] = Field(description="The precise, ready-to-use input string for the chosen tool. If 'tool_name' is 'None', this should also be 'None' or an empty string.")
    reasoning: str = Field(description="Brief reasoning for choosing this tool and formulating this input, or why no tool is needed.")
    confidence_score: float = Field(description="A score from 0.0 to 1.0 indicating the LLM's confidence in this action being correct and optimal for the given step description. 1.0 is highest confidence.", ge=0.0, le=1.0)

# System prompt for the Controller/Validator LLM
CONTROLLER_SYSTEM_PROMPT_TEMPLATE = """You are an expert Controller/Validator AI. Your task is to analyze a single step from a high-level plan and determine the most appropriate tool and the precise input for that tool to successfully execute the step.

You will be given:
1.  The user's original high-level query (for overall context).
2.  The specific plan step's description, any tool suggested by the planner, and any input instructions from the planner.
3.  A list of available tools with their names, descriptions, and expected input formats/schemas.

Your responsibilities:
-   Carefully analyze the plan step's description and the planner's suggestions.
-   From the list of available tools, select the *most suitable* tool for the described step.
    - If the planner suggested a tool, verify if it's the best fit. You can change it if a different tool is more appropriate.
    - If the planner suggested 'None' or no tool, decide if a tool is truly necessary. If the step is purely analytical, requires commonsense reasoning, or involves summarizing information already in the conversation history (which the agent has access to), then 'None' might be correct.
-   If a tool is chosen, formulate the *exact and complete input string* that tool expects. Pay close attention to the tool's input schema/description.
    - For example, if a 'write_file' tool expects 'filename:::content', your output for 'tool_input' must be in that exact format.
    - If a search tool expects a simple query string, provide that query.
-   Provide a brief `reasoning` for your choice of tool and the formulated input.
-   Provide a `confidence_score` (0.0 to 1.0) for your proposed action.

Available tools:
{available_tools_details}

Respond with a single JSON object matching the following schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object.
"""

async def validate_and_prepare_step_action(
    original_user_query: str,
    plan_step: PlanStep,
    available_tools: List[BaseTool],
    llm: BaseChatModel
) -> Tuple[Optional[str], Optional[str], str, float]:
    """
    Validates a plan step and prepares the precise tool and input using an LLM.

    Args:
        original_user_query: The initial query from the user for broader context.
        plan_step: The specific PlanStep object from the planner.
        available_tools: A list of BaseTool objects available to the agent.
        llm: The language model instance to use for validation and input formulation.

    Returns:
        A tuple: (tool_name, tool_input, message, confidence_score).
        'tool_name' and 'tool_input' are None if no tool is to be used or on error.
        'message' contains reasoning or an error description.
        'confidence_score' is the LLM's confidence in its output.
    """
    logger.info(f"Controller: Validating plan step ID {plan_step.step_id}: '{plan_step.description[:100]}...' (Planner suggestion: {plan_step.tool_to_use})")

    available_tools_details = "\n".join(
        [f"- Name: {tool.name}\n  Description: {tool.description}\n  Input Schema: {str(tool.args)}" for tool in available_tools]
    )

    parser = JsonOutputParser(pydantic_object=ValidatedStepAction)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages([
        ("system", CONTROLLER_SYSTEM_PROMPT_TEMPLATE),
        ("human", "Original User Query (for context): {original_user_query}\n\n"
                  "Current Plan Step Details:\n"
                  "- Step ID: {step_id}\n"
                  "- Description: {step_description}\n"
                  "- Planner's Suggested Tool: {planner_tool_suggestion}\n"
                  "- Planner's Input Instructions: {planner_input_instructions}\n\n"
                  "Analyze this step and determine the precise action (tool and input).")
    ])

    chain = prompt | llm | parser

    try:
        controller_result_dict = await chain.ainvoke({
            "original_user_query": original_user_query,
            "step_id": plan_step.step_id,
            "step_description": plan_step.description,
            "planner_tool_suggestion": plan_step.tool_to_use or "None",
            "planner_input_instructions": plan_step.tool_input_instructions or "None",
            "available_tools_details": available_tools_details,
            "format_instructions": format_instructions
        })

        # The parser should return a dict if using JsonOutputParser directly
        # If it returns the Pydantic object, convert it
        if isinstance(controller_result_dict, ValidatedStepAction):
             validated_action = controller_result_dict
        else:
            validated_action = ValidatedStepAction(**controller_result_dict)


        tool_name = validated_action.tool_name if validated_action.tool_name and validated_action.tool_name.lower() != 'none' else None
        tool_input = validated_action.tool_input if tool_name else None # Input is None if tool is None

        # Basic validation: if a tool is named, its input should exist (unless tool specifically takes no input)
        # More advanced validation could check tool_name against available_tools again, but LLM should handle this.
        if tool_name and tool_input is None:
            # Check if the chosen tool actually expects no input.
            # This requires inspecting the tool's args_schema or description.
            # For now, we'll trust the LLM if it says a tool needs no input, but log a warning.
            target_tool_obj = next((t for t in available_tools if t.name == tool_name), None)
            if target_tool_obj and target_tool_obj.args_schema and not tool_input: # If tool has schema but no input given
                 logger.warning(f"Controller LLM suggested tool '{tool_name}' but provided no input, and tool has an args_schema. Reasoning: {validated_action.reasoning}")
                 # Potentially override to an error or let it proceed if LLM is confident.
                 # For now, we proceed but the reasoning should explain this.

        logger.info(f"Controller validation complete for step {plan_step.step_id}. Tool: '{tool_name}', Input: '{str(tool_input)[:100]}...', Confidence: {validated_action.confidence_score:.2f}")
        logger.debug(f"Controller reasoning: {validated_action.reasoning}")

        return tool_name, tool_input, validated_action.reasoning, validated_action.confidence_score

    except Exception as e:
        logger.error(f"Controller: Error during validation/preparation for step {plan_step.step_id}: {e}", exc_info=True)
        # Attempt to get raw output for debugging if JSON parsing failed
        try:
            error_chain = prompt | llm | StrOutputParser()
            raw_output = await error_chain.ainvoke({
                "original_user_query": original_user_query,
                "step_id": plan_step.step_id,
                "step_description": plan_step.description,
                "planner_tool_suggestion": plan_step.tool_to_use or "None",
                "planner_input_instructions": plan_step.tool_input_instructions or "None",
                "available_tools_details": available_tools_details,
                "format_instructions": format_instructions
            })
            logger.error(f"Controller: Raw LLM output on error: {raw_output}")
        except Exception as raw_e:
            logger.error(f"Controller: Failed to get raw LLM output on error: {raw_e}")
        return None, None, f"Error in Controller: {str(e)}", 0.0

if __name__ == '__main__':
    # Placeholder for testing - Requires async setup and mock/real LLM, tools.
    # Example of how you might test it (conceptual)
    async def test_controller():
        from backend.llm_setup import get_llm
        from backend.config import settings
        from langchain_core.tools import tool

        @tool
        def example_search_tool(query: str) -> str:
            """Searches the web for the query."""
            return f"Search results for '{query}'"

        @tool
        def example_write_file_tool(filename: str, content: str) -> str:
            """Writes content to a file. Input format: 'filename:::content'"""
            return f"Successfully wrote to {filename}"


        mock_llm = get_llm(settings, settings.default_provider, settings.default_model_name) # Replace with actual or mock
        mock_tools = [example_search_tool, example_write_file_tool]

        test_plan_step = PlanStep(
            step_id=1,
            description="Search for recent news on AI.",
            tool_to_use="example_search_tool", # Planner's suggestion
            tool_input_instructions="Focus on AI advancements in 2024.",
            expected_outcome="A list of news articles about AI in 2024."
        )
        user_q = "What's new in AI?"

        tool_name, tool_input, message, confidence = await validate_and_prepare_step_action(
            user_q, test_plan_step, mock_tools, mock_llm
        )

        print("--- Controller Test Result ---")
        print(f"Tool Name: {tool_name}")
        print(f"Tool Input: {tool_input}")
        print(f"Message/Reasoning: {message}")
        print(f"Confidence: {confidence}")

    # To run this test:
    # import asyncio
    # asyncio.run(test_controller())
    pass
