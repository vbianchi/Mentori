# backend/evaluator.py
import logging
from typing import List, Dict, Any, Tuple, Optional

from backend.config import settings
from backend.llm_setup import get_llm
from backend.planner import PlanStep # For type hinting
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field, conlist
from langchain_core.tools import BaseTool


logger = logging.getLogger(__name__)

# --- Pydantic Models for Step Evaluator Output ---
class StepCorrectionOutcome(BaseModel):
    step_achieved_goal: bool = Field(description="Boolean indicating if the step's primary goal was achieved based on the executor's output.")
    assessment_of_step: str = Field(description="Detailed assessment of the step's outcome, explaining why it succeeded or failed. If failed, explain the discrepancy between expected and actual outcome.")
    is_recoverable_via_retry: Optional[bool] = Field(description="If step_achieved_goal is false, boolean indicating if the step might be recoverable with a retry using a modified approach. Null if goal achieved.", default=None)
    suggested_new_tool_for_retry: Optional[str] = Field(description="If recoverable, the suggested tool name for the retry attempt (can be 'None'). Null if not recoverable or goal achieved.", default=None)
    suggested_new_input_instructions_for_retry: Optional[str] = Field(description="If recoverable, new or revised input instructions for the Controller to formulate the tool_input for the retry. Null if not recoverable or goal achieved.", default=None)
    # suggested_revised_step_description: Optional[str] = Field(description="If recoverable, a potentially revised description for the step to guide the retry. Null if not applicable.", default=None)
    confidence_in_correction: Optional[float] = Field(description="If recoverable, confidence (0.0-1.0) in the suggested correction. Null if not recoverable or goal achieved.", default=None)


STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE = """You are an expert Step Evaluator for a research agent.
Your task is to meticulously assess if a single executed plan step achieved its intended goal, based on its output and the original expectations.

**Context for Evaluation:**
- Original User Query: {original_user_query}
- Current Plan Step Being Evaluated:
    - Description: {current_step_description}
    - Expected Outcome (from Planner): {current_step_expected_outcome}
- Controller's Decision for this attempt:
    - Tool Used by Executor: {controller_tool_used}
    - Formulated Input for Executor/Tool: {controller_tool_input}
- Actual Output from Executor/Tool for this attempt:
  ---
  {step_executor_output}
  ---

**Your Evaluation Task:**
1.  Determine `step_achieved_goal` (True/False): Did the `step_executor_output` successfully fulfill the `current_step_expected_outcome`? Be strict.
2.  Provide a detailed `assessment_of_step`: Explain your reasoning for True/False. If False, clearly state what went wrong or what was missing.
3.  If `step_achieved_goal` is False:
    a.  Determine `is_recoverable_via_retry` (True/False): Could a different tool, different tool input, or a slightly modified approach likely succeed on a retry? Consider if the error was transient, a misunderstanding, or a fundamental flaw. Max retries are limited.
    b.  If `is_recoverable_via_retry` is True:
        i.  `suggested_new_tool_for_retry`: From the available tools ({available_tools_summary}), suggest the best tool for a retry (can be 'None' if the LLM should try again directly).
        ii. `suggested_new_input_instructions_for_retry`: Provide clear, revised instructions for the Controller to formulate the new tool input for the retry. This might involve using information from the failed `step_executor_output` if it's partially useful, or completely new instructions.
        iii. `confidence_in_correction`: Your confidence (0.0-1.0) that this suggested retry approach will succeed.

Output ONLY a JSON object adhering to this schema:
{format_instructions}

Do not include any preamble or explanation outside the JSON object.
"""

# --- Pydantic Models for Overall Plan Evaluator Output ---
class EvaluationResult(BaseModel):
    overall_success: bool = Field(description="Boolean indicating if the overall user query was successfully addressed by the executed plan.")
    confidence_score: float = Field(description="A score from 0.0 to 1.0 indicating confidence in the success/failure assessment.")
    assessment: str = Field(description="A concise summary of why the plan succeeded or failed, suitable for user display.")
    suggestions_for_replan: Optional[List[str]] = Field(description="If the plan failed, a list of high-level suggestions for how a new plan might better achieve the goal. Null if successful.", default=None)

OVERALL_EVALUATOR_SYSTEM_PROMPT_TEMPLATE = """You are an expert Overall Plan Evaluator for a research agent.
Your task is to assess if the executed multi-step plan successfully achieved the user's original query, based on a summary of the plan's execution and the final answer produced.

**Context for Overall Evaluation:**
- Original User Query: {original_user_query}
- Summary of Executed Plan Steps & Outcomes:
  ---
  {executed_plan_summary}
  ---
- Final Answer/Output from the last successful step (or error message if plan failed):
  ---
  {final_agent_answer}
  ---

**Your Evaluation Task:**
1.  `overall_success` (True/False): Did the agent, through the executed plan, fully and accurately address all aspects of the `original_user_query`?
2.  `confidence_score` (0.0-1.0): Your confidence in this assessment.
3.  `assessment`: A concise, user-facing explanation of why the plan succeeded or failed. If it failed, briefly explain the core reason.
4.  `suggestions_for_replan` (Optional List[str]): If `overall_success` is False, provide a few high-level, actionable suggestions for how a *new* plan (if the user chooses to re-engage) might better achieve the original goal. These are not detailed steps, but strategic advice.

Output ONLY a JSON object adhering to this schema:
{format_instructions}

Do not include any preamble or explanation outside the JSON object.
"""

async def evaluate_step_outcome_and_suggest_correction(
    original_user_query: str,
    plan_step_being_evaluated: PlanStep,
    controller_tool_used: Optional[str],
    controller_tool_input: Optional[str],
    step_executor_output: str,
    available_tools: List[BaseTool],
    session_data_entry: Dict[str, Any] # <--- ADDED session_data_entry
) -> Optional[StepCorrectionOutcome]:
    """
    Evaluates a single step's outcome and suggests corrections if it failed and is recoverable.
    """
    logger.info(f"Evaluator (Step): Evaluating step '{plan_step_being_evaluated.step_id}: {plan_step_being_evaluated.description[:50]}...'")

    evaluator_llm_id_override = session_data_entry.get("session_evaluator_llm_id")
    evaluator_provider = settings.evaluator_provider
    evaluator_model_name = settings.evaluator_model_name
    if evaluator_llm_id_override:
        try:
            provider_override, model_override = evaluator_llm_id_override.split("::", 1)
            if provider_override in ["gemini", "ollama"] and model_override:
                evaluator_provider, evaluator_model_name = provider_override, model_override
                logger.info(f"Evaluator (Step): Using session override LLM: {evaluator_llm_id_override}")
            else:
                logger.warning(f"Evaluator (Step): Invalid session LLM ID structure '{evaluator_llm_id_override}'. Using system default.")
        except ValueError:
            logger.warning(f"Evaluator (Step): Invalid session LLM ID format '{evaluator_llm_id_override}'. Using system default.")
    
    try:
        evaluator_llm: BaseChatModel = get_llm(
            settings,
            provider=evaluator_provider,
            model_name=evaluator_model_name,
            requested_for_role="StepEvaluator"
        )
        logger.info(f"Evaluator (Step): Using LLM {evaluator_provider}::{evaluator_model_name}")
    except Exception as e:
        logger.error(f"Evaluator (Step): Failed to initialize LLM: {e}", exc_info=True)
        return None # Cannot evaluate without LLM

    parser = JsonOutputParser(pydantic_object=StepCorrectionOutcome)
    format_instructions = parser.get_format_instructions()
    tools_summary_for_eval = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in available_tools])

    prompt = ChatPromptTemplate.from_messages([
        ("system", STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE),
        ("human", "Evaluate the step execution based on the provided context and output your assessment in the specified JSON format.")
    ])
    chain = prompt | evaluator_llm | parser

    try:
        eval_result_dict = await chain.ainvoke({
            "original_user_query": original_user_query,
            "current_step_description": plan_step_being_evaluated.description,
            "current_step_expected_outcome": plan_step_being_evaluated.expected_outcome,
            "controller_tool_used": controller_tool_used or "None",
            "controller_tool_input": controller_tool_input or "None",
            "step_executor_output": step_executor_output,
            "available_tools_summary": tools_summary_for_eval,
            "format_instructions": format_instructions
        })
        
        if isinstance(eval_result_dict, StepCorrectionOutcome):
            eval_outcome = eval_result_dict
        elif isinstance(eval_result_dict, dict):
            eval_outcome = StepCorrectionOutcome(**eval_result_dict)
        else:
            logger.error(f"Step Evaluator LLM call returned an unexpected type: {type(eval_result_dict)}. Content: {eval_result_dict}")
            return None
            
        logger.info(f"Evaluator (Step {plan_step_being_evaluated.step_id}): Achieved Goal: {eval_outcome.step_achieved_goal}, Recoverable: {eval_outcome.is_recoverable_via_retry}")
        return eval_outcome
    except Exception as e:
        logger.error(f"Evaluator (Step): Error during step evaluation for step {plan_step_being_evaluated.step_id}: {e}", exc_info=True)
        return None


async def evaluate_plan_outcome(
    original_user_query: str,
    executed_plan_summary: str, # Summary of all steps, attempts, and outcomes
    final_agent_answer: str, # The final answer/output produced by the agent or last step
    session_data_entry: Dict[str, Any] # <--- ADDED session_data_entry
) -> Optional[EvaluationResult]:
    """
    Evaluates the overall success of the executed plan.
    """
    logger.info(f"Evaluator (Overall Plan): Evaluating outcome for query: {original_user_query[:100]}...")

    evaluator_llm_id_override = session_data_entry.get("session_evaluator_llm_id")
    evaluator_provider = settings.evaluator_provider
    evaluator_model_name = settings.evaluator_model_name
    if evaluator_llm_id_override:
        try:
            provider_override, model_override = evaluator_llm_id_override.split("::", 1)
            if provider_override in ["gemini", "ollama"] and model_override:
                evaluator_provider, evaluator_model_name = provider_override, model_override
                logger.info(f"Evaluator (Overall Plan): Using session override LLM: {evaluator_llm_id_override}")
            else:
                logger.warning(f"Evaluator (Overall Plan): Invalid session LLM ID structure '{evaluator_llm_id_override}'. Using system default.")
        except ValueError:
            logger.warning(f"Evaluator (Overall Plan): Invalid session LLM ID format '{evaluator_llm_id_override}'. Using system default.")

    try:
        evaluator_llm: BaseChatModel = get_llm(
            settings,
            provider=evaluator_provider,
            model_name=evaluator_model_name,
            requested_for_role="OverallPlanEvaluator"
        )
        logger.info(f"Evaluator (Overall Plan): Using LLM {evaluator_provider}::{evaluator_model_name}")
    except Exception as e:
        logger.error(f"Evaluator (Overall Plan): Failed to initialize LLM: {e}", exc_info=True)
        return None

    parser = JsonOutputParser(pydantic_object=EvaluationResult)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages([
        ("system", OVERALL_EVALUATOR_SYSTEM_PROMPT_TEMPLATE),
        ("human", "Evaluate the overall plan execution based on the provided context and output your assessment in the specified JSON format.")
    ])
    chain = prompt | evaluator_llm | parser

    try:
        eval_result_dict = await chain.ainvoke({
            "original_user_query": original_user_query,
            "executed_plan_summary": executed_plan_summary,
            "final_agent_answer": final_agent_answer,
            "format_instructions": format_instructions
        })

        if isinstance(eval_result_dict, EvaluationResult):
            eval_result = eval_result_dict
        elif isinstance(eval_result_dict, dict):
            eval_result = EvaluationResult(**eval_result_dict)
        else:
            logger.error(f"Overall Plan Evaluator LLM call returned an unexpected type: {type(eval_result_dict)}. Content: {eval_result_dict}")
            return None
            
        logger.info(f"Evaluator (Overall Plan): Evaluation complete. Success: {eval_result.overall_success}, Confidence: {eval_result.confidence_score:.2f}")
        return eval_result
    except Exception as e:
        logger.error(f"Evaluator (Overall Plan): Error during overall plan evaluation: {e}", exc_info=True)
        return None

