import logging
from typing import List, Dict, Any, Optional, Union

from backend.config import settings
from backend.llm_setup import get_llm
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic.v1 import BaseModel, Field # Compatibility with Pydantic v1
import asyncio

from backend.planner import PlanStep
from langchain_core.tools import BaseTool


logger = logging.getLogger(__name__)

class EvaluationResult(BaseModel):
    """
    Defines the structured output for the Overall Plan Evaluator LLM.
    """
    overall_success: bool = Field(description="Boolean indicating if the overall original user goal was successfully achieved.")
    assessment: str = Field(description="A concise, human-readable summary of the outcome, explaining why it was or wasn't successful.")
    missing_information: Optional[List[str]] = Field(description="If not successful, a list of specific pieces of information or actions that are still missing or were incorrect.", default=None)
    suggestions_for_replan: Optional[List[str]] = Field(description="If not successful, actionable suggestions for how the plan could be improved or what steps to try next.", default=None)
    confidence_score: float = Field(description="A score from 0.0 to 1.0 indicating the LLM's confidence in this evaluation.", ge=0.0, le=1.0)

EVALUATOR_SYSTEM_PROMPT_TEMPLATE = """You are an expert AI Evaluator. Your task is to assess whether a research agent successfully achieved the user's original goal based on a summary of the executed plan and its outcomes.

You will be given:
1.  The user's original high-level query/goal.
2.  A summary of the executed plan, including:
    - Each step's description.
    - The tool used (if any) and its input.
    - The observed output or result of each step.
    - Any errors encountered during any step.
3.  The final answer or result provided by the agent to the user.

Your responsibilities:
-   Carefully compare the final outcome and the executed steps against the user's original query/goal.
-   Determine if the goal was fully and accurately achieved (`overall_success`).
-   Provide a concise `assessment` explaining your reasoning.
-   If the goal was not fully achieved or if there were significant issues:
    - Identify any `missing_information` or parts of the goal that were not addressed.
    - Provide actionable `suggestions_for_replan` that could help achieve the goal if the agent were to try again (e.g., "Consider using tool X for Y", "The summary for Z was incomplete, try to extract more details", "The Python script failed with error A, it needs to be debugged by checking B").
-   Provide a `confidence_score` (0.0 to 1.0) for your evaluation.

Respond with a single JSON object matching the following schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object.
Focus on the substance of the results, not just whether tools ran without crashing. Did the agent *actually* answer the user's request or complete the task as intended?
"""

class StepCorrectionOutcome(BaseModel):
    """
    Defines the structured output for the Step Evaluator LLM.
    It assesses a single step's outcome and suggests corrections if it failed.
    """
    step_achieved_goal: bool = Field(description="Boolean indicating if this specific step's intended goal was successfully achieved based on its output.")
    assessment_of_step: str = Field(description="A concise, human-readable assessment of this step's outcome, explaining why it succeeded or failed relative to its specific goal.")
    is_recoverable_via_retry: bool = Field(description="If the step failed (step_achieved_goal is false), boolean indicating if the failure seems correctable with a retry using modified parameters or a different tool for THIS SAME STEP. Set to false if the step seems fundamentally flawed, the error is external/unfixable by the agent (e.g. a website is truly down, a file genuinely doesn't exist and shouldn't), or if the step actually succeeded despite minor issues.")
    suggested_new_tool_for_retry: Optional[str] = Field(default=None, description="If is_recoverable_via_retry is true, the name of the tool (from available tools) that should be used for the retry attempt of THIS step. Can be the same as the original tool, a different tool, or 'None' if the retry should be a direct LLM response. If is_recoverable_via_retry is false, this should be null.")
    suggested_new_input_instructions_for_retry: Optional[str] = Field(default=None, description="If is_recoverable_via_retry is true, specific, concise instructions or key parameters for the Controller to formulate the tool_input for the retry attempt of THIS step. This is guidance, not the full input. If is_recoverable_via_retry is false, this should be null.")
    confidence_in_correction: Optional[float] = Field(default=None, description="If is_recoverable_via_retry is true, a score from 0.0 to 1.0 indicating confidence in the suggested correction. If false, this should be null.", ge=0.0, le=1.0)


STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE = """You are an expert AI Step Evaluator. Your task is to assess the outcome of a single step executed by a research agent and, if it failed, determine if it's recoverable and suggest a specific correction for retrying *only that step*.

You will be given:
1.  The user's original high-level query (for overall context).
2.  The specific plan step's description and its expected outcome.
3.  The tool that was attempted for the step (if any) and the input it received.
4.  The actual output or error message from executing that step.
5.  A list of available tools the agent can use.

Your responsibilities:
-   `step_achieved_goal`: Determine if the step's specific goal (as per its description and expected outcome) was met by the actual output.
-   `assessment_of_step`: Briefly explain your reasoning.
-   If `step_achieved_goal` is false:
    -   `is_recoverable_via_retry`: Decide if the failure is likely correctable by retrying *this same step* with a different tool or modified input. Consider if the error was due to a bad tool choice, incorrect input formulation, or a minor, fixable issue. Do not suggest retry if the problem is external (e.g., website down, file truly doesn't exist and shouldn't, or a service is rate-limiting you) or if the step's logic is fundamentally flawed for the overall goal. **If the error message clearly indicates an external, temporary issue like a 'rate limit', 'Ratelimit', 'service unavailable', or HTTP status codes like 429, 503 for a web-based tool, consider `is_recoverable_via_retry` as `false` for an *immediate* retry, as retrying the same action instantly is unlikely to succeed.**
    -   If `is_recoverable_via_retry` is true:
        -   `suggested_new_tool_for_retry`: Specify the exact name of the tool (from the available list or 'None') to use for the retry.
        -   `suggested_new_input_instructions_for_retry`: Provide concise instructions for the Controller to formulate the input for the retry. E.g., "Search for 'X Y Z' instead of 'A B C'", "Ensure the filename is 'data.csv'", "Use the full URL found in the previous step's output."
        -   `confidence_in_correction`: Your confidence (0.0-1.0) that this suggested correction will lead to success for this step.
    -   If `is_recoverable_via_retry` is false, `suggested_new_tool_for_retry`, `suggested_new_input_instructions_for_retry`, and `confidence_in_correction` should be null.

Available tools for suggestion:
{available_tools_details}

Respond with a single JSON object matching the following schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object.
Focus on the direct outcome of THIS step versus its specific goal.
"""

async def evaluate_plan_outcome(
    original_user_query: str,
    executed_plan_summary: str,
    final_agent_answer: str
) -> Optional[EvaluationResult]:
    # ... (existing content - no changes needed) ...
    logger.info(f"Evaluator (Overall Plan): Evaluating outcome for query: {original_user_query[:100]}...")
    logger.debug(f"Evaluator (Overall Plan): Executed Plan Summary:\n{executed_plan_summary}")
    logger.debug(f"Evaluator (Overall Plan): Final Agent Answer:\n{final_agent_answer}")

    try:
        evaluator_llm: BaseChatModel = get_llm(
            settings,
            provider=settings.evaluator_provider,
            model_name=settings.evaluator_model_name
        ) # type: ignore
        logger.info(f"Evaluator (Overall Plan): Using LLM {settings.evaluator_provider}::{settings.evaluator_model_name}")
    except Exception as e:
        logger.error(f"Evaluator (Overall Plan): Failed to initialize LLM: {e}", exc_info=True)
        return None

    parser = JsonOutputParser(pydantic_object=EvaluationResult)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages([
        ("system", EVALUATOR_SYSTEM_PROMPT_TEMPLATE),
        ("human", "User's Original Query/Goal:\n{original_user_query}\n\n"
                  "Summary of Executed Plan and Outcomes:\n{executed_plan_summary}\n\n"
                  "Final Answer Provided by Agent:\n{final_agent_answer}\n\n"
                  "Please evaluate the outcome.")
    ])

    chain = prompt | evaluator_llm | parser

    try:
        evaluation_result_dict = await chain.ainvoke({
            "original_user_query": original_user_query,
            "executed_plan_summary": executed_plan_summary,
            "final_agent_answer": final_agent_answer,
            "format_instructions": format_instructions
        })

        if isinstance(evaluation_result_dict, EvaluationResult):
            evaluation = evaluation_result_dict
        else:
            evaluation = EvaluationResult(**evaluation_result_dict)

        logger.info(f"Evaluator (Overall Plan): Evaluation complete. Success: {evaluation.overall_success}, Confidence: {evaluation.confidence_score:.2f}")
        logger.debug(f"Evaluator (Overall Plan): Assessment: {evaluation.assessment}")
        if evaluation.suggestions_for_replan:
            logger.debug(f"Evaluator (Overall Plan): Suggestions: {evaluation.suggestions_for_replan}")
        return evaluation

    except Exception as e:
        logger.error(f"Evaluator (Overall Plan): Error during evaluation: {e}", exc_info=True)
        try:
            error_chain = prompt | evaluator_llm | StrOutputParser() # type: ignore
            raw_output = await error_chain.ainvoke({
                "original_user_query": original_user_query,
                "executed_plan_summary": executed_plan_summary,
                "final_agent_answer": final_agent_answer,
                "format_instructions": format_instructions
            })
            logger.error(f"Evaluator (Overall Plan): Raw LLM output on error: {raw_output}")
        except Exception as raw_e:
            logger.error(f"Evaluator (Overall Plan): Failed to get raw LLM output on error: {raw_e}")
        return None

async def evaluate_step_outcome_and_suggest_correction(
    original_user_query: str,
    plan_step_being_evaluated: PlanStep,
    controller_tool_used: Optional[str],
    controller_tool_input: Optional[str],
    step_executor_output: str,
    available_tools: List[BaseTool]
) -> Optional[StepCorrectionOutcome]:
    # ... (existing content - no changes needed) ...
    logger.info(f"Evaluator (Step): Evaluating step '{plan_step_being_evaluated.step_id}: {plan_step_being_evaluated.description[:50]}...'")
    logger.debug(f"Evaluator (Step): Original User Query: {original_user_query[:100]}...")
    logger.debug(f"Evaluator (Step): Step Description: {plan_step_being_evaluated.description}")
    logger.debug(f"Evaluator (Step): Expected Outcome: {plan_step_being_evaluated.expected_outcome}")
    logger.debug(f"Evaluator (Step): Attempted Tool (Controller): {controller_tool_used}")
    logger.debug(f"Evaluator (Step): Attempted Tool Input (Controller): {str(controller_tool_input)[:100]}...")
    logger.debug(f"Evaluator (Step): Actual Executor Output: {step_executor_output[:200]}...")

    try:
        step_evaluator_llm: BaseChatModel = get_llm(
            settings,
            provider=settings.evaluator_provider,
            model_name=settings.evaluator_model_name
        ) # type: ignore
        logger.info(f"Evaluator (Step): Using LLM {settings.evaluator_provider}::{settings.evaluator_model_name}")
    except Exception as e:
        logger.error(f"Evaluator (Step): Failed to initialize LLM: {e}", exc_info=True)
        return None

    available_tools_details = "\n".join(
        [f"- Name: {tool.name}\n  Description: {tool.description}" for tool in available_tools]
    )

    parser = JsonOutputParser(pydantic_object=StepCorrectionOutcome)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages([
        ("system", STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE),
        ("human", "Original User Query (for overall context):\n{original_user_query}\n\n"
                  "Plan Step Being Evaluated:\n"
                  "- Step ID: {step_id}\n"
                  "- Description: {step_description}\n"
                  "- Expected Outcome: {expected_outcome}\n\n"
                  "Details of This Attempt:\n"
                  "- Tool Attempted (by Controller): {attempted_tool}\n"
                  "- Tool Input Given (by Controller): {attempted_tool_input}\n"
                  "- Actual Output/Error from Executor: {actual_executor_output}\n\n"
                  "Please evaluate this step's outcome and suggest a correction if it failed and is recoverable.")
    ])

    chain = prompt | step_evaluator_llm | parser

    try:
        step_evaluation_dict = await chain.ainvoke({
            "original_user_query": original_user_query,
            "step_id": plan_step_being_evaluated.step_id,
            "step_description": plan_step_being_evaluated.description,
            "expected_outcome": plan_step_being_evaluated.expected_outcome,
            "attempted_tool": controller_tool_used or "None",
            "attempted_tool_input": controller_tool_input or "N/A",
            "actual_executor_output": step_executor_output,
            "available_tools_details": available_tools_details,
            "format_instructions": format_instructions
        })

        if isinstance(step_evaluation_dict, StepCorrectionOutcome):
            step_outcome = step_evaluation_dict
        else:
            step_outcome = StepCorrectionOutcome(**step_evaluation_dict)

        logger.info(f"Evaluator (Step {plan_step_being_evaluated.step_id}): Achieved Goal: {step_outcome.step_achieved_goal}, Recoverable: {step_outcome.is_recoverable_via_retry if not step_outcome.step_achieved_goal else 'N/A'}")
        logger.debug(f"Evaluator (Step {plan_step_being_evaluated.step_id}): Assessment: {step_outcome.assessment_of_step}")
        if not step_outcome.step_achieved_goal and step_outcome.is_recoverable_via_retry:
            logger.debug(f"Evaluator (Step {plan_step_being_evaluated.step_id}): Suggestion: Tool='{step_outcome.suggested_new_tool_for_retry}', Input Hint='{step_outcome.suggested_new_input_instructions_for_retry}', Confidence={step_outcome.confidence_in_correction}")
        return step_outcome

    except Exception as e:
        logger.error(f"Evaluator (Step {plan_step_being_evaluated.step_id}): Error during step evaluation: {e}", exc_info=True)
        try:
            error_chain = prompt | step_evaluator_llm | StrOutputParser() # type: ignore
            raw_output = await error_chain.ainvoke({
                "original_user_query": original_user_query,
                "step_id": plan_step_being_evaluated.step_id,
                "step_description": plan_step_being_evaluated.description,
                "expected_outcome": plan_step_being_evaluated.expected_outcome,
                "attempted_tool": controller_tool_used or "None",
                "attempted_tool_input": controller_tool_input or "N/A",
                "actual_executor_output": step_executor_output,
                "available_tools_details": available_tools_details,
                "format_instructions": format_instructions
            })
            logger.error(f"Evaluator (Step {plan_step_being_evaluated.step_id}): Raw LLM output on error: {raw_output}")
        except Exception as raw_e:
            logger.error(f"Evaluator (Step {plan_step_being_evaluated.step_id}): Failed to get raw LLM output on error: {raw_e}")
        return None


if __name__ == '__main__':
    async def test_overall_evaluator():
        # ... (existing test - no changes needed) ...
        test_query = "Find the latest 2 papers on PubMed about 'mRNA vaccine stability', read the abstract of the first result, and write a short summary of that abstract to a file named 'summary.txt'."
        test_plan_summary = """
Step 1: Executed pubmed_search with input 'mRNA vaccine stability latest 2'. Output: Found 2 papers: [Paper A, Paper B].
Step 2: Executed web_page_reader for Paper B's abstract. Output: Abstract of Paper B...
Step 3: Executed write_file with input 'summary.txt:::Summary of Paper B abstract...'. Output: Successfully wrote file: 'summary.txt'.
Step 4: Attempted to run python script for word cloud. Error: ModuleNotFoundError: No module named 'wordcloud'.
        """
        test_final_answer = "I have found two papers and saved a summary of the second paper's abstract to summary.txt. I could not generate the word cloud."
        evaluation = await evaluate_plan_outcome(test_query, test_plan_summary, test_final_answer)
        if evaluation:
            print("\n--- Overall Plan Evaluation Result ---")
            print(f"Overall Success: {evaluation.overall_success}")
            print(f"Assessment: {evaluation.assessment}")
            print(f"Confidence: {evaluation.confidence_score}")
            if evaluation.missing_information: print(f"Missing Info: {evaluation.missing_information}")
            if evaluation.suggestions_for_replan: print(f"Suggestions for Re-plan: {evaluation.suggestions_for_replan}")
        else: print("Overall Plan Evaluation failed.")

    async def test_step_evaluator():
        # ... (existing test - no changes needed) ...
        class MockTool(BaseTool):
            name: str
            description: str
            args_schema: Optional[Any] = None # type: ignore
            def _run(self, *args: Any, **kwargs: Any) -> Any: raise NotImplementedError()
            async def _arun(self, *args: Any, **kwargs: Any) -> Any: raise NotImplementedError()

        mock_tools_list = [
            MockTool(name="duckduckgo_search", description="Web search tool."),
            MockTool(name="write_file", description="Writes content to a file. Input: 'filename:::content'."),
            MockTool(name="read_file", description="Reads content from a file. Input: 'filename'.")
        ]

        test_orig_query = "Search for AI news and write it to news.txt"
        test_step = PlanStep(
            step_id=1,
            description="Search for recent news about Artificial Intelligence.",
            tool_to_use="duckduckgo_search",
            tool_input_instructions="Focus on general AI advancements.",
            expected_outcome="A list of recent news articles about AI."
        )
        test_executor_output_failed_recoverable = "Error: duckduckgo_search failed because the query 'Artificial Intelligence' was too broad. Try a more specific query."
        print(f"\n--- Step Evaluator Test 1 (Failed, Recoverable) ---")
        outcome1 = await evaluate_step_outcome_and_suggest_correction(
            original_user_query=test_orig_query,
            plan_step_being_evaluated=test_step,
            controller_tool_used="duckduckgo_search",
            controller_tool_input="Artificial Intelligence",
            step_executor_output=test_executor_output_failed_recoverable,
            available_tools=mock_tools_list
        )
        if outcome1: print(outcome1.json(indent=2))
        else: print("Step Evaluation 1 failed to produce an outcome.")

        test_executor_output_succeeded = "Found 3 news articles: 1. AI in healthcare... 2. New LLM released... 3. AI ethics discussion..."
        print(f"\n--- Step Evaluator Test 2 (Succeeded) ---")
        outcome2 = await evaluate_step_outcome_and_suggest_correction(
            original_user_query=test_orig_query,
            plan_step_being_evaluated=test_step,
            controller_tool_used="duckduckgo_search",
            controller_tool_input="recent AI advancements",
            step_executor_output=test_executor_output_succeeded,
            available_tools=mock_tools_list
        )
        if outcome2: print(outcome2.json(indent=2))
        else: print("Step Evaluation 2 failed to produce an outcome.")

        test_step_write = PlanStep(
            step_id=2,
            description="Write the found news to 'news.txt'.",
            tool_to_use="write_file",
            tool_input_instructions="Content should be the search results.",
            expected_outcome="File 'news.txt' created with AI news."
        )
        test_executor_output_failed_unrecoverable = "Error: write_file failed. Disk full."
        print(f"\n--- Step Evaluator Test 3 (Failed, Unrecoverable) ---")
        outcome3 = await evaluate_step_outcome_and_suggest_correction(
            original_user_query=test_orig_query,
            plan_step_being_evaluated=test_step_write,
            controller_tool_used="write_file",
            controller_tool_input="news.txt:::AI news...",
            step_executor_output=test_executor_output_failed_unrecoverable,
            available_tools=mock_tools_list
        )
        if outcome3: print(outcome3.json(indent=2))
        else: print("Step Evaluation 3 failed to produce an outcome.")

    async def run_all_tests():
        await test_overall_evaluator()
        await test_step_evaluator()

    asyncio.run(run_all_tests())
