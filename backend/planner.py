import logging
from typing import List, Dict, Any, Tuple, Optional

# MODIFIED: Import settings and get_llm
from backend.config import settings
from backend.llm_setup import get_llm
from langchain_core.language_models.chat_models import BaseChatModel # Still needed for type hinting
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import asyncio # For the test block

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


PLANNER_SYSTEM_PROMPT_TEMPLATE = """You are an expert planning assistant for a research agent.
Your goal is to take a user's complex request and break it down into a sequence of logical, actionable sub-tasks.
The research agent has access to the following tools:
{available_tools_summary}

For each sub-task in the plan:
1.  Provide a clear `description` of what the sub-task aims to achieve.
2.  If a tool is needed, specify the exact `tool_to_use` from the list of available tools. If no tool is directly needed for a step (e.g., the LLM itself will perform the reasoning or summarization as part of a later step), use "None".
3.  Provide brief `tool_input_instructions` highlighting key parameters or data the tool might need. This is NOT the full tool input, but guidance for the agent when it forms the tool input later. For example, if downloading a file, mention the expected filename.
4.  State the `expected_outcome` of successfully completing the step (e.g., "File 'data.csv' downloaded to workspace", "Summary of article written to 'summary.txt'"). **If this step's output is primarily intended as direct, raw input for a *subsequent processing step* in your plan (like parsing, further analysis, or summarization by a later step), the `expected_outcome` should clearly state that this raw, unprocessed data (e.g., "The full text content of the file 'report.txt' is returned", "The complete list of search results is made available") is the deliverable for this current step.**
Additionally, provide a `human_readable_summary` of the entire plan that can be shown to the user for confirmation.
Ensure the output is a JSON object that strictly adheres to the following JSON schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object."""

async def generate_plan(
    user_query: str,
    # MODIFIED: Removed llm as an argument
    available_tools_summary: str
) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
    """
    Generates a multi-step plan based on the user query using an LLM.
    Fetches its own LLM based on settings.
    """
    logger.info(f"Planner: Generating plan for user query: {user_query[:100]}...")

    # MODIFIED: Get the LLM for the Planner from settings
    try:
        planner_llm: BaseChatModel = get_llm(
            settings,
            provider=settings.planner_provider,
            model_name=settings.planner_model_name,
            requested_for_role="Planner" # ADDED: Role context
        ) # type: ignore
        logger.info(f"Planner: Using LLM {settings.planner_provider}::{settings.planner_model_name}")
    except Exception as e:
        logger.error(f"Planner: Failed to initialize LLM: {e}", exc_info=True)
        return None, None

    parser = JsonOutputParser(pydantic_object=AgentPlan)
    format_instructions = parser.get_format_instructions()

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT_TEMPLATE),
        ("human", "{user_query}")
    ])

    chain = prompt_template | planner_llm | parser

    try:
        logger.debug(f"Planner prompt input variables: {prompt_template.input_variables}")
        planned_result_dict = await chain.ainvoke({
            "user_query": user_query,
            "available_tools_summary": available_tools_summary,
            "format_instructions": format_instructions
        })

        if isinstance(planned_result_dict, AgentPlan):
            agent_plan = planned_result_dict
        elif isinstance(planned_result_dict, dict):
            agent_plan = AgentPlan(**planned_result_dict)
        else:
            logger.error(f"Planner LLM call returned an unexpected type: {type(planned_result_dict)}. Content: {planned_result_dict}")
            return None, None

        human_summary = agent_plan.human_readable_summary
        structured_steps = [step.dict() for step in agent_plan.steps]

        logger.info(f"Planner: Plan generated successfully. Summary: {human_summary}")
        logger.debug(f"Planner: Structured plan: {structured_steps}")
        return human_summary, structured_steps

    except Exception as e:
        logger.error(f"Planner: Error during plan generation: {e}", exc_info=True)
        try:
            error_chain = prompt_template | planner_llm | StrOutputParser() # type: ignore
            raw_output = await error_chain.ainvoke({
                "user_query": user_query,
                "available_tools_summary": available_tools_summary,
                "format_instructions": format_instructions
            })
            logger.error(f"Planner: Raw LLM output on error: {raw_output}")
        except Exception as raw_e:
            logger.error(f"Planner: Failed to get raw LLM output on error: {raw_e}")
        return None, None

if __name__ == '__main__':
    async def test_planner():
        # This test now relies on settings from config.py for the planner LLM
        
        query = "Find recent papers on CRISPR side effects, download the top 3 PDFs, summarize each, and combine summaries into a report."
        tools_summary = "- duckduckgo_search: For web searches.\n- web_page_reader: To read content from URLs.\n- pubmed_search: For PubMed searches.\n- read_file: To read files from workspace.\n- write_file: To write files to workspace.\n- workspace_shell: To execute shell commands.\n- Python_REPL: To execute Python code."
        
        # generate_plan now fetches its own LLM
        summary, plan = await generate_plan(query, tools_summary)

        if summary and plan:
            print("---- Human Readable Summary ----")
            print(summary)
            print("\n---- Structured Plan ----")
            for i, step_data in enumerate(plan):
                # Ensure step_data is a dict before using .get()
                if isinstance(step_data, dict):
                    print(f"Step {step_data.get('step_id', i+1)}:") # Use step_id if available
                    print(f"  Description: {step_data.get('description')}")
                    print(f"  Tool: {step_data.get('tool_to_use')}")
                    print(f"  Input Instructions: {step_data.get('tool_input_instructions')}")
                    print(f"  Expected Outcome: {step_data.get('expected_outcome')}")
                else:
                    print(f"Step {i+1}: Invalid step data format: {step_data}")

        else:
            print("Failed to generate a plan.")

    asyncio.run(test_planner())