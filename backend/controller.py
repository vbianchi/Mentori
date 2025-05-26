# backend/controller.py
import logging
from typing import List, Dict, Any, Tuple, Optional
import json 
import re 

# LangChain Imports
from langchain_core.tools import BaseTool 
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field 

# Project Imports
from backend.config import settings
from backend.llm_setup import get_llm
from backend.planner import PlanStep 


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
    * If a tool is chosen, `tool_input` MUST be the exact, complete, and correctly formatted string the tool expects. Use the Planner's `input_instructions` as guidance.
    * **CRUCIAL: If `previous_step_output_context` is provided AND the `current_step_description` or `planner_tool_input_instructions` clearly indicate that the current step should use the output of the previous step (e.g., "write the generated poem", "summarize the search results", "use the extracted data"), you MUST use the content from `previous_step_output_context` to form the `tool_input` (e.g., for `write_file`, the content part of the input) or as the direct basis for a "None" tool generation. Do NOT re-generate information or create new example content if it's already present in `previous_step_output_context` and is meant to be used by the current step.**
    * If `tool_name` is "None", `tool_input` should be a concise summary of what the Executor LLM should generate or reason about to achieve the `expected_outcome`. It can be explicitly `null` or a string "None" if the description and expected outcome are self-sufficient for the LLM, especially if `previous_step_output_context` contains the necessary data for the LLM to work on directly.
3.  **Confidence Score:** Provide a `confidence_score` (0.0 to 1.0) for your decision.
4.  **Reasoning:** Briefly explain your choices, including how you used (or why you didn't use) the `previous_step_output_context`.

Output ONLY a JSON object adhering to this schema:
{format_instructions}

Do not include any preamble or explanation outside the JSON object.
If you determine an error or impossibility in achieving the step as described, set tool_name to "None", tool_input to a description of the problem, confidence_score to 0.0, and explain in reasoning.
"""


async def validate_and_prepare_step_action(
    original_user_query: str,
    plan_step: PlanStep,
    available_tools: List[BaseTool],
    session_data_entry: Dict[str, Any], 
    previous_step_output: Optional[str] = None 
) -> Tuple[Optional[str], Optional[str], str, float]:
    """
    Uses an LLM to validate the current plan step and determine the precise tool and input.
    """
    logger.info(f"Controller: Validating plan step ID {plan_step.step_id}: '{plan_step.description[:100]}...' (Planner suggestion: {plan_step.tool_to_use})")
    if previous_step_output:
        logger.info(f"Controller: Received previous_step_output (first 100 chars): {previous_step_output[:100]}...")

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
        controller_llm: BaseChatModel = get_llm(
            settings,
            provider=controller_provider,
            model_name=controller_model_name,
            requested_for_role="Controller"
        ) 
        logger.info(f"Controller: Using LLM {controller_provider}::{controller_model_name}")
    except Exception as e:
        logger.error(f"Controller: Failed to initialize LLM: {e}", exc_info=True)
        return None, None, f"Error in Controller: LLM initialization failed: {e}", 0.0

    parser = JsonOutputParser(pydantic_object=ControllerOutput)
    format_instructions = parser.get_format_instructions()
    
    tools_summary_for_controller = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in available_tools])
    
    previous_step_output_context_str = "Not applicable (this is the first step or previous step had no direct output, or its output was not relevant to pass)."
    if previous_step_output is not None: 
        previous_step_output_context_str = f"The direct output from the PREVIOUS successfully completed step was:\n---\n{previous_step_output}\n---"

    prompt = ChatPromptTemplate.from_messages([
        ("system", CONTROLLER_SYSTEM_PROMPT_TEMPLATE),
        ("human", "Analyze the current plan step and provide your output in the specified JSON format.") 
    ])

    raw_llm_output_chain = prompt | controller_llm | StrOutputParser()
    controller_result_dict_raw = "" 

    try:
        controller_result_dict_raw = await raw_llm_output_chain.ainvoke({
            "original_user_query": original_user_query,
            "current_step_description": plan_step.description,
            "current_step_expected_outcome": plan_step.expected_outcome,
            "planner_tool_suggestion": plan_step.tool_to_use or "None",
            "planner_tool_input_instructions": plan_step.tool_input_instructions or "None",
            "available_tools_summary": tools_summary_for_controller,
            "previous_step_output_context": previous_step_output_context_str, 
            "format_instructions": format_instructions
        })
        logger.debug(f"Controller: Raw LLM output string before stripping: '{controller_result_dict_raw}'")
        
        # --- MODIFICATION: Strip Markdown ```json ... ``` wrapper ---
        cleaned_json_string = controller_result_dict_raw.strip()
        if cleaned_json_string.startswith("```json"):
            cleaned_json_string = cleaned_json_string[len("```json"):].strip()
        if cleaned_json_string.startswith("```"): # Handle case where only ``` is present
            cleaned_json_string = cleaned_json_string[len("```"):].strip()
        if cleaned_json_string.endswith("```"):
            cleaned_json_string = cleaned_json_string[:-len("```")].strip()
        
        logger.debug(f"Controller: Cleaned JSON string for parsing: '{cleaned_json_string}'")
        # --- END MODIFICATION ---
        
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

        logger.info(f"Controller validation complete for step {plan_step.step_id}. Tool: '{tool_name}', Input: '{str(tool_input)[:100]}...', Confidence: {confidence:.2f}")
        return tool_name, tool_input, reasoning, confidence

    except json.JSONDecodeError as json_err: 
        logger.error(f"Controller: Failed to parse LLM output as JSON. Cleaned string was: '{cleaned_json_string if 'cleaned_json_string' in locals() else 'Error before cleaning'}'. Error: {json_err}", exc_info=True)
        reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]*)"', controller_result_dict_raw, re.IGNORECASE) # Use original raw for reasoning
        error_reasoning = f"LLM output was not valid JSON. {reasoning_match.group(1) if reasoning_match else 'Could not extract reasoning.'}"
        return None, None, f"Error in Controller: LLM output parsing failed (not valid JSON). Reasoning hint: {error_reasoning}", 0.0
    except Exception as e: 
        logger.error(f"Controller: Error during step validation or Pydantic parsing: {e}. Raw output was: {controller_result_dict_raw}", exc_info=True)
        error_detail = f"Exception: {type(e).__name__}. Raw LLM output might have been: {str(controller_result_dict_raw)[:500]}..."
        return None, None, f"Error in Controller: {error_detail}", 0.0

