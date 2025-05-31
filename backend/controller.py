# backend/controller.py
import logging
from typing import List, Dict, Any, Tuple, Optional
import json
import re
import traceback

from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks.base import BaseCallbackHandler


from backend.config import settings
from backend.llm_setup import get_llm
from backend.planner import PlanStep
from backend.callbacks import LOG_SOURCE_CONTROLLER


logger = logging.getLogger(__name__)

class ControllerOutput(BaseModel):
    tool_name: Optional[str] = Field(description="The exact name of the tool to use, or 'None' if no tool is directly needed for this step. Must be one of the available tools.")
    tool_input: Optional[str] = Field(default=None, description="The precise, complete input string for the chosen tool, or a concise summary/directive for the LLM if tool_name is 'None'. Can be explicitly 'None' or null if the step description and expected outcome are self-sufficient for a 'None' tool LLM action.")
    confidence_score: float = Field(description="A score from 0.0 to 1.0 indicating the controller's confidence in this tool/input choice for the step. 1.0 is high confidence.")
    reasoning: str = Field(description="Brief explanation of why this tool/input was chosen or why no tool is needed.")

CONTROLLER_SYSTEM_PROMPT_TEMPLATE = """You are an expert "Controller" for a research agent.
Your role is to analyze a single step from a pre-defined plan and decide the BEST action for the "Executor" (a ReAct agent) to take for that step.
**Current Task Context:**
- Original User Query: {original_user_query}
- Current Plan Step Description: {current_step_description}
- Expected Outcome for this Step: {current_step_expected_outcome}
- Tool suggested by Planner (can be overridden): {planner_tool_suggestion}
- Planner's input instructions (guidance, not literal input): {planner_tool_input_instructions}

**Available Tools for the Executor:**
{available_tools_summary}

**Output from the PREVIOUS successful plan step (if available and relevant for the current step):**
{previous_step_output_context}

**Your Task:**
Based on ALL the above information, determine the most appropriate `tool_name` and formulate the precise `tool_input`.
**Key Considerations:**
1.  **Tool Selection:**
    * If the Planner's `tool_suggestion` is appropriate and aligns with the step description and available tools, prioritize it.
    * If the Planner's suggestion is 'None' or unsuitable, you MUST select an appropriate tool from the `Available Tools` list if one is clearly needed to achieve the `expected_outcome`.
    * If the step is purely analytical, requires summarization of previous context/memory, or involves creative generation that the LLM can do directly (and no tool is a better fit), set `tool_name` to "None".
2.  **Tool Input Formulation:**
    * If a tool is chosen, `tool_input` MUST be the exact, complete, and correctly formatted string the tool expects.
    * **CRUCIAL: If a tool's description (from `Available Tools` above) explicitly states its input MUST be a JSON string (e.g., it mentions "Input MUST be a JSON string matching...schema..."), then your `tool_input` field MUST be that exact, complete, and valid JSON string. Do not provide just the raw content for one of its keys; provide the full JSON structure as a string (e.g., "{{\\"query\\": \\"actual research query\\", \\"num_sources_to_deep_dive\\": 3}}").**
    * **CRUCIAL: If `previous_step_output_context` is provided AND the `current_step_description` or `planner_tool_input_instructions` clearly indicate that the current step should use the output of the previous step (e.g., "write the generated poem", "summarize the search results", "use the extracted data"), you MUST use the content from `previous_step_output_context` to form the `tool_input` (e.g., for `write_file`, the content part of the input) or as the direct basis for a "None" tool generation.
    * Do NOT re-generate information or create new example content if it's already present in `previous_step_output_context` and is meant to be used by the current step.**
    * If `tool_name` is "None", `tool_input` should be a concise summary of what the Executor LLM should generate or reason about to achieve the `expected_outcome`.
    * It can be explicitly `null` or a string "None" if the description and expected outcome are self-sufficient for the LLM, especially if `previous_step_output_context` contains the necessary data for the LLM to work on directly.
3.  **Confidence Score:** Provide a `confidence_score` (0.0 to 1.0) for your decision.
4.  **Reasoning:** Briefly explain your choices, including how you used (or why you didn't use) the `previous_step_output_context`.
Output ONLY a JSON object adhering to this schema:
{format_instructions}

Do not include any preamble or explanation outside the JSON object.
If you determine an error or impossibility in achieving the step as described, set tool_name to "None", tool_input to a description of the problem, confidence_score to 0.0, and explain in reasoning.
"""

def escape_template_curly_braces(text: Optional[str]) -> str:
    """Escapes single curly braces to be literal in LangChain templates."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return text.replace("{", "{{").replace("}", "}}")

async def validate_and_prepare_step_action(
    original_user_query: str,
    plan_step: PlanStep,
    available_tools: List[BaseTool],
    session_data_entry: Dict[str, Any],
    previous_step_output: Optional[str] = None,
    callback_handler: Optional[BaseCallbackHandler] = None
) -> Tuple[Optional[str], Optional[str], str, float]:
    """
    Uses an LLM to validate the current plan step and determine the precise tool and input.
    """
    logger.info(f"Controller: Validating plan step ID {plan_step.step_id}: '{plan_step.description[:100]}...' (Planner suggestion: {plan_step.tool_to_use})")
    if previous_step_output:
        logger.info(f"Controller: Received previous_step_output (first 100 chars): {previous_step_output[:100]}...")

    callbacks_for_invoke: List[BaseCallbackHandler] = []
    if callback_handler:
        callbacks_for_invoke.append(callback_handler)
        logger.critical(f"CRITICAL_DEBUG: CONTROLLER - validate_and_prepare_step_action received callback_handler: {type(callback_handler).__name__}")
    else:
        logger.critical("CRITICAL_DEBUG: CONTROLLER - validate_and_prepare_step_action received NO callback_handler.")


    controller_llm_id_override = session_data_entry.get("session_controller_llm_id")
    controller_provider = settings.controller_provider
    controller_model_name = settings.controller_model_name
    if controller_llm_id_override:
        try:
            provider_override, model_override = controller_llm_id_override.split("::", 1)
            if provider_override in ["gemini", "ollama"] and model_override:
                controller_provider, controller_model_name = provider_override, model_override
                logger.info(f"Controller: Using session override LLM: {controller_llm_id_override}")
            else:
                logger.warning(f"Controller: Invalid structure or unknown provider in session LLM ID '{controller_llm_id_override}'. Using system default.")
        except ValueError:
            logger.warning(f"Controller: Invalid session LLM ID format '{controller_llm_id_override}'. Using system default.")

    try:
        logger.critical(f"CRITICAL_DEBUG: CONTROLLER - About to call get_llm. Callbacks_for_invoke: {[type(cb).__name__ for cb in callbacks_for_invoke] if callbacks_for_invoke else 'None'}")
        controller_llm: BaseChatModel = get_llm(
            settings,
            provider=controller_provider,
            model_name=controller_model_name,
            requested_for_role=LOG_SOURCE_CONTROLLER,
            callbacks=callbacks_for_invoke
        )
        logger.info(f"Controller: Using LLM {controller_provider}::{controller_model_name}")
    except Exception as e:
        logger.error(f"Controller: Failed to initialize LLM: {e}", exc_info=True)
        return None, None, f"Error in Controller: LLM initialization failed: {e}", 0.0

    parser = JsonOutputParser(pydantic_object=ControllerOutput)
    format_instructions = parser.get_format_instructions()

    tools_summary_list = []
    for tool in available_tools:
        # <<< --- MODIFIED LINE: Use full tool.description --- >>>
        tools_summary_list.append(f"- {tool.name}: {tool.description}")
        # <<< --- END MODIFIED LINE --- >>>
    tools_summary_for_controller = "\n".join(tools_summary_list)
    logger.debug(f"Controller: Tools summary for LLM prompt:\n{tools_summary_for_controller}")


    previous_step_output_context_str = "Not applicable (this is the first step or previous step had no direct output, or its output was not relevant to pass)."
    if previous_step_output is not None:
        previous_step_output_context_str = f"The direct output from the PREVIOUS successfully completed step was:\n---\n{previous_step_output}\n---"

    prompt = ChatPromptTemplate.from_messages([
        ("system", CONTROLLER_SYSTEM_PROMPT_TEMPLATE),
        ("human", "Analyze the current plan step and provide your output in the specified JSON format.")
    ])

    raw_llm_output_chain = prompt | controller_llm | StrOutputParser()
    controller_result_dict_raw = ""

    escaped_original_user_query = escape_template_curly_braces(original_user_query)
    escaped_current_step_description = escape_template_curly_braces(plan_step.description)
    escaped_current_step_expected_outcome = escape_template_curly_braces(plan_step.expected_outcome)
    escaped_planner_tool_suggestion = escape_template_curly_braces(plan_step.tool_to_use or "None")
    escaped_planner_tool_input_instructions = escape_template_curly_braces(plan_step.tool_input_instructions or "None")
    escaped_tools_summary = escape_template_curly_braces(tools_summary_for_controller)
    escaped_previous_step_output_context = escape_template_curly_braces(previous_step_output_context_str)

    try:
        input_dict_for_llm = {
            "original_user_query": escaped_original_user_query,
            "current_step_description": escaped_current_step_description,
            "current_step_expected_outcome": escaped_current_step_expected_outcome,
            "planner_tool_suggestion": escaped_planner_tool_suggestion,
            "planner_tool_input_instructions": escaped_planner_tool_input_instructions,
            "available_tools_summary": escaped_tools_summary,
            "previous_step_output_context": escaped_previous_step_output_context,
            "format_instructions": format_instructions
        }
        debug_dict_str_repr = {
            k: (str(v)[:100] + '...' if len(str(v)) > 100 else str(v))
            for k, v in input_dict_for_llm.items()
        }
        logger.debug(f"Controller: Input dictionary for LLM (first 100 chars of each value): {debug_dict_str_repr}")

        controller_result_dict_raw = await raw_llm_output_chain.ainvoke(
            input_dict_for_llm,
            config=RunnableConfig(
                callbacks=callbacks_for_invoke,
                metadata={"component_name": LOG_SOURCE_CONTROLLER}
            )
        )
        logger.debug(f"Controller: Raw LLM output string before stripping: '{controller_result_dict_raw}'")

        cleaned_json_string = controller_result_dict_raw.strip()
        if cleaned_json_string.startswith("```json"):
            cleaned_json_string = cleaned_json_string[len("```json"):].strip()
        if cleaned_json_string.startswith("```"):
            cleaned_json_string = cleaned_json_string[len("```"):].strip()
        if cleaned_json_string.endswith("```"):
            cleaned_json_string = cleaned_json_string[:-len("```")].strip()

        logger.debug(f"Controller: Cleaned JSON string for parsing: '{cleaned_json_string}'")
        controller_result_dict = json.loads(cleaned_json_string)

        parsed_tool_name = controller_result_dict.get("tool_name")
        parsed_tool_input = controller_result_dict.get("tool_input")

        if parsed_tool_name == "None" or parsed_tool_name is None:
            if not isinstance(parsed_tool_input, (str, type(None))):
                logger.warning(f"Controller: tool_name is 'None', but tool_input was type {type(parsed_tool_input)} ('{parsed_tool_input}'). Forcing to None for Pydantic.")
                controller_result_dict["tool_input"] = None
            elif parsed_tool_input == "None":
                 controller_result_dict["tool_input"] = None
        elif parsed_tool_name and parsed_tool_input is None :
            logger.warning(f"Controller: tool_name is '{parsed_tool_name}', but tool_input was None. This might be an issue for the tool. Proceeding.")
        elif parsed_tool_name and not isinstance(parsed_tool_input, str):
            logger.warning(f"Controller: tool_name is '{parsed_tool_name}', but tool_input was type {type(parsed_tool_input)} ('{parsed_tool_input}'). Attempting to stringify.")
            try:
                controller_result_dict["tool_input"] = str(parsed_tool_input)
            except Exception:
                 logger.error(f"Controller: Could not convert tool_input to string for tool '{parsed_tool_name}'. Input was: {parsed_tool_input}")
                 return None, None, f"Error in Controller: tool_input for tool '{parsed_tool_name}' could not be converted to string.", 0.0

        controller_output = ControllerOutput(**controller_result_dict)

        tool_name = controller_output.tool_name if controller_output.tool_name != "None" else None
        tool_input = controller_output.tool_input
        reasoning = controller_output.reasoning
        confidence = controller_output.confidence_score

        logger.info(f"Controller LLM decided: Tool='{tool_name}', Tool Input='{tool_input}', Confidence={confidence:.2f}")

        logger.info(f"Controller validation complete for step {plan_step.step_id}. Tool: '{tool_name}', Input (summary): '{str(tool_input)[:100]}...', Confidence: {confidence:.2f}")
        return tool_name, tool_input, reasoning, confidence

    except json.JSONDecodeError as json_err:
        logger.error(f"Controller: Failed to parse LLM output as JSON. Cleaned string was: '{cleaned_json_string if 'cleaned_json_string' in locals() else 'Error before cleaning'}'. Error: {json_err}", exc_info=True)
        reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]*)"', controller_result_dict_raw, re.IGNORECASE)
        error_reasoning = f"LLM output was not valid JSON. {reasoning_match.group(1) if reasoning_match else 'Could not extract reasoning.'}"
        return None, None, f"Error in Controller: LLM output parsing failed (not valid JSON). Reasoning hint: {error_reasoning}", 0.0
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Controller: Error during step validation or Pydantic parsing: {e}. Raw output was: {controller_result_dict_raw}\nTraceback:\n{tb_str}", exc_info=False)
        error_detail = f"Exception: {type(e).__name__} at line {e.__traceback__.tb_lineno if e.__traceback__ else 'N/A'}. Raw LLM output might have been: {str(controller_result_dict_raw)[:500]}..."
        return None, None, f"Error in Controller: {error_detail}", 0.0
