import logging
from typing import List, Dict, Any, Tuple, Optional

from backend.config import settings
from backend.llm_setup import get_llm
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import asyncio

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
2.  If a tool is needed, specify the exact `tool_to_use` from the list of available tools. If no tool is directly needed for a step (e.g., the LLM itself will perform the reasoning, summarization, or content generation), use "None".
    For such "No Tool" steps that involve the LLM generating structured text output (e.g., a Markdown table, a JSON object, a detailed list, or a multi-paragraph formatted text segment): if the required output is complex, multi-part, or has a specific intricate format, consider breaking the generation into two or more distinct "No Tool" steps if it promotes clarity and reliability. For example:
    * An initial step to generate the core data or content elements (perhaps as a list of facts, key-value pairs, or plain sentences). The `expected_outcome` for this step would be this intermediate data.
    * A subsequent step to take this intermediate data (which will be available from the previous step's output) and format it into the final desired complex structure (e.g., the Markdown table, the JSON object). The `expected_outcome` here would be the final formatted string.
    This approach can improve the reliability of generating complex outputs.
3.  Provide brief `tool_input_instructions` highlighting key parameters or data the tool might need. This is NOT the full tool input, but guidance for the agent when it forms the tool input later. For example, if downloading a file, mention the expected filename.
4.  State the `expected_outcome` of successfully completing the step (e.g., "File 'data.csv' downloaded to workspace", "Summary of article written to 'summary.txt'"). If this step's output is primarily intended as direct, raw input for a *subsequent processing step* in your plan (like parsing, further analysis, or summarization by a later step), the `expected_outcome` should clearly state that this raw, unprocessed data (e.g., "The full text content of the file 'report.txt' is returned", "The complete list of search results is made available") is the deliverable for this current step.

**Handling Multi-Part User Queries for Final Output:**
If the original user query explicitly or implicitly asks for multiple distinct pieces of information to be delivered in the final response (e.g., "tell me X, and also provide Y"), ensure your plan includes all necessary steps to gather or generate each piece of information. **Crucially, after all individual pieces of information have been gathered by preceding steps and need to be presented to the user as a combined answer, you MUST add a final "No Tool" step. The objective of this final step is to synthesize these pieces into a single, coherent, and comprehensive final answer.**
-   The `description` for this final synthesis step should clearly state that it's combining the necessary prior outputs to fully address the user's original request.
-   The `tool_input_instructions` should guide the LLM on which prior step outputs need to be synthesized, for example: "Combine the result from Step X [e.g., the extracted fact about AD-003's MechanismOfAction] and the result from Step Y [e.g., the one-sentence summary of the file 'alz_candidates.md'] into a complete answer to the user's original query: '{user_query}'".
-   The `expected_outcome` for this synthesis step should be: "A single, consolidated final answer addressing all parts of the user's original request is generated and ready to be presented."

Additionally, provide a `human_readable_summary` of the entire plan that can be shown to the user for confirmation.
Ensure the output is a JSON object that strictly adheres to the following JSON schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object."""

async def generate_plan(
    user_query: str,
    available_tools_summary: str
) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
    """
    Generates a multi-step plan based on the user query using an LLM.
    Fetches its own LLM based on settings.
    """
    logger.info(f"Planner: Generating plan for user query: {user_query[:100]}...")

    try:
        planner_llm: BaseChatModel = get_llm(
            settings,
            provider=settings.planner_provider,
            model_name=settings.planner_model_name,
            requested_for_role="Planner"
        ) # type: ignore
        logger.info(f"Planner: Using LLM {settings.planner_provider}::{settings.planner_model_name}")
    except Exception as e:
        logger.error(f"Planner: Failed to initialize LLM: {e}", exc_info=True)
        return None, None

    parser = JsonOutputParser(pydantic_object=AgentPlan)
    format_instructions = parser.get_format_instructions()

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT_TEMPLATE),
        ("human", "{user_query}") # user_query will be passed in .ainvoke()
    ])

    chain = prompt_template | planner_llm | parser

    try:
        logger.debug(f"Planner prompt input variables: {prompt_template.input_variables}")
        # Pass user_query directly here as it's used in the new prompt section for synthesis
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
        structured_steps = []
        for i, step_model in enumerate(agent_plan.steps):
            step_dict = step_model.dict()
            step_dict['step_id'] = i + 1 
            structured_steps.append(step_dict)


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
    async def test_planner_multi_output():
        query_multi_part = """Generate a list of 3 hypothetical drug candidates for treating Alzheimer's disease, including DrugID, MechanismOfAction, and DevelopmentStage, as a Markdown table. Save this to 'drugs.md'. Then, read 'drugs.md' and tell me the MechanismOfAction for DrugID 'AD-002'. Finally, also tell me how many drugs are listed in 'drugs.md'."""
        tools_summary = "- write_file: To write files to workspace.\n- read_file: To read files from workspace."
        
        print(f"\n--- Testing Planner with Multi-Output Query ---")
        print(f"Query: {query_multi_part}")
        summary, plan = await generate_plan(query_multi_part, tools_summary)

        if summary and plan:
            print("---- Human Readable Summary ----")
            print(summary)
            print("\n---- Structured Plan ----")
            for i, step_data in enumerate(plan):
                if isinstance(step_data, dict):
                    print(f"Step {step_data.get('step_id', i+1)}:")
                    print(f"  Description: {step_data.get('description')}")
                    print(f"  Tool: {step_data.get('tool_to_use')}")
                    print(f"  Input Instructions: {step_data.get('tool_input_instructions')}")
                    print(f"  Expected Outcome: {step_data.get('expected_outcome')}")
                else:
                    print(f"Step {i+1}: Invalid step data format: {step_data}")
        else:
            print("Failed to generate a plan for multi-output query.")

    asyncio.run(test_planner_multi_output())
