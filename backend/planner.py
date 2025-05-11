# backend/planner.py
import logging
from typing import List, Dict, Any, Tuple, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

logger = logging.getLogger(__name__)

# Define the structure for a single step in the plan
class PlanStep(BaseModel):
    step_id: int = Field(description="A unique sequential identifier for this step, starting from 1.")
    description: str = Field(description="A concise, human-readable description of what this single sub-task aims to achieve.")
    tool_to_use: Optional[str] = Field(description="The exact name of the tool to be used for this step, if any. Must be one of the available tools or 'None'.")
    tool_input_instructions: Optional[str] = Field(description="Specific instructions or key parameters for the tool_input, if a tool is used. This is not the full tool input itself, but guidance for forming it.")
    expected_outcome: str = Field(description="What is the expected result or artifact from completing this step successfully?")

# Define the structure for the overall plan
class AgentPlan(BaseModel):
    human_readable_summary: str = Field(description="A brief, conversational summary of the overall plan for the user.")
    steps: List[PlanStep] = Field(description="A list of detailed steps to accomplish the user's request.")


# MODIFIED: Renamed to indicate it's a template and added placeholders for all variables
PLANNER_SYSTEM_PROMPT_TEMPLATE = """You are an expert planning assistant for a research agent. Your goal is to take a user's complex request and break it down into a sequence of logical, actionable sub-tasks.

The research agent has access to the following tools:
{available_tools_summary}

For each sub-task in the plan:
1.  Provide a clear `description` of what the sub-task aims to achieve.
2.  If a tool is needed, specify the exact `tool_to_use` from the list of available tools. If no tool is directly needed for a step (e.g., the LLM itself will perform the reasoning or summarization as part of a later step), use "None".
3.  Provide brief `tool_input_instructions` highlighting key parameters or data the tool might need. This is NOT the full tool input, but guidance for the agent when it forms the tool input later. For example, if downloading a file, mention the expected filename.
4.  State the `expected_outcome` of successfully completing the step (e.g., "File 'data.csv' downloaded to workspace", "Summary of article written to 'summary.txt'").

Additionally, provide a `human_readable_summary` of the entire plan that can be shown to the user for confirmation.

Ensure the output is a JSON object that strictly adheres to the following JSON schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object.
"""

async def generate_plan(
    user_query: str,
    llm: BaseChatModel,
    available_tools_summary: str
) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
    """
    Generates a multi-step plan based on the user query using an LLM.
    """
    logger.info(f"Generating plan for user query: {user_query[:100]}...")

    parser = JsonOutputParser(pydantic_object=AgentPlan)
    format_instructions = parser.get_format_instructions() # Get format instructions from the parser

    # MODIFIED: The prompt template now explicitly defines all its input variables
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT_TEMPLATE), # System prompt is now a template string
        ("human", "{user_query}")                  # Human prompt also uses a placeholder
    ])

    # The chain will expect 'user_query', 'available_tools_summary', and 'format_instructions'
    chain = prompt_template | llm | parser

    try:
        logger.debug(f"Planner prompt input variables: {prompt_template.input_variables}")
        # MODIFIED: Provide all expected input variables to ainvoKe
        planned_result = await chain.ainvoke({
            "user_query": user_query,
            "available_tools_summary": available_tools_summary,
            "format_instructions": format_instructions
        })

        if isinstance(planned_result, AgentPlan): # If Pydantic model is returned directly by some LLM/parser versions
            agent_plan = planned_result
        elif isinstance(planned_result, dict): # Standard case for JsonOutputParser
            agent_plan = AgentPlan(**planned_result)
        else:
            logger.error(f"Planner LLM call returned an unexpected type: {type(planned_result)}. Content: {planned_result}")
            return None, None

        human_summary = agent_plan.human_readable_summary
        structured_steps = [step.dict() for step in agent_plan.steps]

        logger.info(f"Plan generated successfully. Summary: {human_summary}")
        logger.debug(f"Structured plan: {structured_steps}")
        return human_summary, structured_steps

    except Exception as e:
        logger.error(f"Error during plan generation: {e}", exc_info=True)
        # Attempt to get raw output for debugging if parsing failed
        try:
            raw_output_chain = prompt_template | llm | StrOutputParser()
            raw_output = await raw_output_chain.ainvoke({
                "user_query": user_query,
                "available_tools_summary": available_tools_summary,
                "format_instructions": format_instructions
            })
            logger.error(f"Raw LLM output during planning error: {raw_output}")
        except Exception as raw_e:
            logger.error(f"Failed to get raw LLM output during planning error: {raw_e}")
        return None, None

if __name__ == '__main__':
    # This is a placeholder for testing the planner module directly.
    # You'll need to set up a mock LLM or a real LLM instance.
    # Example (requires a compatible LLM and config):
    # from backend.config import settings
    # from backend.llm_setup import get_llm
    # import asyncio

    # async def test_planner():
    #     # Ensure your .env is set up for this to work with a real LLM
    #     try:
    #         test_llm = get_llm(settings, settings.default_provider, settings.default_model_name)
    #     except Exception as e:
    #         logger.error(f"Could not initialize LLM for testing: {e}")
    #         return

    #     query = "Find recent papers on CRISPR side effects, download the top 3 PDFs, summarize each, and combine summaries into a report."
    #     # Construct a more realistic tools summary if needed by the prompt
    #     tools_summary = "- duckduckgo_search: For web searches.\n- web_page_reader: To read content from URLs.\n- pubmed_search: For PubMed searches.\n- read_file: To read files from workspace.\n- write_file: To write files to workspace.\n- workspace_shell: To execute shell commands.\n- Python_REPL: To execute Python code."
        
    #     summary, plan = await generate_plan(query, test_llm, tools_summary)

    #     if summary and plan:
    #         print("---- Human Readable Summary ----")
    #         print(summary)
    #         print("\n---- Structured Plan ----")
    #         for i, step_data in enumerate(plan): # Iterate over list of dicts
    #             print(f"Step {i+1}:")
    #             print(f"  Description: {step_data.get('description')}")
    #             print(f"  Tool: {step_data.get('tool_to_use')}")
    #             print(f"  Input Instructions: {step_data.get('tool_input_instructions')}")
    #             print(f"  Expected Outcome: {step_data.get('expected_outcome')}")
    #     else:
    #         print("Failed to generate a plan.")

    # if __name__ == '__main__':
    #    asyncio.run(test_planner())
    pass
