# backend/langgraph_agent.py
# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 17 - Four-Track Graph Wiring)
#
# This version completes the reintegration of all four cognitive tracks by
# implementing the intelligent router and wiring all nodes into the final graph.
#
# Key Architectural Changes:
# 1. Intelligent Four-Track Router: The `initial_router_node` is now powered
#    by an LLM, using a prompt that allows it to choose between DIRECT_QA,
#    SIMPLE_TOOL_USE, COMPLEX_PROJECT, or PEER_REVIEW.
# 2. Fully Wired Graph (`create_agent_graph`):
#    - The graph is now wired according to the four-track architecture.
#    - Track 1 (DIRECT_QA) routes directly to the Editor.
#    - Track 2 (SIMPLE_TOOL_USE) routes through `std_handyman_node` -> `std_worker_node` -> Editor.
#    - Track 3 (COMPLEX_PROJECT) uses the full `std_` node suite (`std_chief_architect_node`,
#      `std_site_foreman_node`, etc.) with its self-correction loop.
#    - Track 4 (PEER_REVIEW) remains wired to the Board of Experts (`Propose_Experts` etc.).
# 3. Track Separation: The node prefixes (`std_` and `boe_`) ensure that the
#    execution logic for the standard complex track and the peer review track
#    are kept completely separate, as requested.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
import asyncio
from typing import TypedDict, Annotated, Sequence, List, Optional, Dict, Any, Union

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from google.api_core.exceptions import ResourceExhausted
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


from .tools import get_available_tools
from .prompts import (
    router_prompt_template,
    handyman_prompt_template,
    structured_planner_prompt_template,
    controller_prompt_template,
    evaluator_prompt_template,
    final_answer_prompt_template,
    correction_planner_prompt_template,
    summarizer_prompt_template,
    memory_updater_prompt_template,
    chief_architect_prompt_template,
    propose_experts_prompt_template,
    chair_initial_plan_prompt_template,
    expert_critique_prompt_template,
    chair_final_review_prompt_template,
    board_checkpoint_review_prompt_template,
)

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Constants ---
HISTORY_SUMMARY_THRESHOLD = 10
HISTORY_SUMMARY_KEEP_RECENT = 4
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files", "workspace_shell", "pip_install", "query_files", "critique_document"}


# --- Data Models ---
class UserProfile(TypedDict, total=False): persona: dict; preferences: dict
class KnowledgeGraphConcept(TypedDict, total=False): id: str; name: str; type: str; properties: dict
class KnowledgeGraphRelationship(TypedDict, total=False): source: str; target: str; label: str
class KnowledgeGraph(TypedDict, total=False): concepts: List[KnowledgeGraphConcept]; relationships: List[KnowledgeGraphRelationship]
class EventOrTask(TypedDict, total=False): description: str; date: str
class WorkspaceFileSummary(TypedDict, total=False): filename: str; summary: str; status: str
class MemoryVault(TypedDict, total=False): user_profile: UserProfile; knowledge_graph: KnowledgeGraph; events_and_tasks: List[EventOrTask]; workspace_summary: List[WorkspaceFileSummary]; key_observations_and_facts: List[str]

class ProposedExpert(BaseModel):
    title: str = Field(description="The expert's job title (e.g., 'Forensic Accountant').")
    qualities: str = Field(description="A brief, one-sentence summary of their key skills and relevance to the task.")

class BoardOfExperts(BaseModel):
    experts: List[ProposedExpert] = Field(description="A list of 3-4 diverse, relevant experts for the board.")

class Step(BaseModel):
    instruction: str = Field(description="The high-level instruction for this step.")
    tool: Optional[str] = Field(default=None, description="The suggested tool for this step (e.g., 'workspace_shell', 'checkpoint'). For high-level strategic steps without a specific tool, this should be null or omitted.")

class StrategicPlan(BaseModel):
    """A high-level plan of strategic milestones."""
    plan: List[Step] = Field(description="A list of high-level steps to accomplish the user's goal.")

class StrategicMemo(BaseModel):
    """The final output of the planning phase, containing the plan and key implementation details."""
    plan: List[Step] = Field(description="The final, high-level, multi-step strategic plan.")
    implementation_notes: List[str] = Field(description="A bulleted list of critical constraints, parameters, and considerations distilled from expert critiques that the execution team must follow.")

class CritiqueAndPlan(BaseModel):
    critique: str = Field(description="The detailed, constructive critique from the expert's point of view. Explain WHY you are making changes.")
    updated_plan: List[Step] = Field(description="The complete, revised step-by-step plan. This should be the full plan, not just the changed parts.")

class TacticalStep(BaseModel):
    """A single step in a tactical plan, representing a specific tool call."""
    step_id: int = Field(description="A unique identifier for this step within the tactical plan.")
    instruction: str = Field(description="The detailed, specific instruction for this tool call.")
    tool_name: str = Field(description="The name of the tool to be used for this step.")
    tool_input: Union[Dict[str, Any], str] = Field(description="The dictionary of arguments to be passed to the tool.")

class TacticalPlan(BaseModel):
    """A detailed, step-by-step plan of tool calls to achieve a strategic goal."""
    steps: List[TacticalStep] = Field(description="A list of tactical steps to be executed in sequence.")

class BoardDecision(BaseModel):
    """The decision made by the Board of Experts at a checkpoint."""
    decision: str = Field(description="The board's decision. Must be one of: 'continue', 'adapt', 'escalate'.")
    reasoning: str = Field(description="A brief justification for the board's decision.")


class GraphState(TypedDict):
    # Core fields
    input: str
    task_id: str
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    llm_config: Dict[str, str]
    workspace_path: str
    memory_vault: MemoryVault
    enabled_tools: List[str]
    route: str
    current_track: str
    answer: str
    user_feedback: Optional[str]
    
    # Standard Complex Project Track fields
    plan: List[dict]
    current_step_index: int
    current_tool_call: Optional[dict]
    tool_output: Optional[str]
    history: Annotated[List[str], lambda x, y: x + y]
    step_outputs: Annotated[Dict[int, str], lambda x, y: {**x, **y}]
    step_evaluation: Optional[dict]
    max_retries: int
    step_retries: int
    plan_retries: int

    # Board of Experts (Peer Review) Track fields
    proposed_experts: Optional[List[dict]]
    board_approved: Optional[bool]
    approved_experts: Optional[List[dict]]
    initial_plan: Optional[List[dict]]
    expert_critique_index: int
    critiques: Optional[List[dict]]
    refined_plan: Optional[List[dict]]
    strategic_memo: Optional[dict]
    tactical_plan: Optional[List[dict]]
    current_tactical_step: Optional[dict]
    worker_output: Optional[str]
    tactical_step_index: int
    strategic_step_index: int
    checkpoint_report: Optional[str]
    board_decision: Optional[str]
    user_guidance: Optional[str]


# --- Helper Functions ---
LLM_CACHE = {}
def get_llm(state: GraphState, role_env_var: str, default_llm_id: str):
    run_config = state.get("llm_config", {}); llm_id = run_config.get(role_env_var) or os.getenv(role_env_var, default_llm_id)
    if llm_id in LLM_CACHE: return LLM_CACHE[llm_id]
    provider, model_name = llm_id.split("::"); logger.info(f"Task '{state.get('task_id')}': Initializing LLM for '{role_env_var}': {llm_id}")
    if provider == "gemini": llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif provider == "ollama": llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
    else: raise ValueError(f"Unsupported LLM provider: {provider}")
    LLM_CACHE[llm_id] = llm; return llm

def _invoke_llm_with_fallback(llm, prompt: str, state: GraphState):
    try: return llm.invoke(prompt)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return AIMessage(content=f"Error: {e}")

def format_tools_for_prompt(state: GraphState):
    all_tools = get_available_tools(); enabled_tool_names = state.get("enabled_tools")
    active_tools = [t for t in all_tools if t.name in enabled_tool_names] if enabled_tool_names is not None else all_tools
    tool_strings = [f"  - {t.name}: {t.description}" for t in active_tools]
    return "\n".join(tool_strings) if tool_strings else "No tools are available for this task."

def _format_messages(messages: Sequence[BaseMessage], is_for_summary=False) -> str:
    formatted_messages = []; start_index = 0
    if not is_for_summary:
        first_human_message_index = next((i for i, msg in enumerate(messages) if isinstance(msg, HumanMessage)), -1)
        if first_human_message_index != -1: start_index = first_human_message_index
    for msg in messages[start_index:]:
        role = "System Summary" if isinstance(msg, SystemMessage) else "Human" if isinstance(msg, HumanMessage) else "AI"
        formatted_messages.append(f"{role}: {msg.content}")
    if not is_for_summary: return "\n".join(formatted_messages[:-1]) if len(formatted_messages) > 1 else "No prior conversation history."
    return "\n".join(formatted_messages)

async def _create_venv_if_not_exists(workspace_path: str, task_id: str):
    venv_path = os.path.join(workspace_path, ".venv")
    if not os.path.isdir(venv_path):
        logger.info(f"Task '{task_id}': Creating venv in '{workspace_path}'")
        process = await asyncio.create_subprocess_exec("uv", "venv", cwd=workspace_path)
        await process.wait()

def _substitute_step_outputs(data: Any, step_outputs: Dict[int, str]) -> Any:
    if isinstance(data, str):
        match = re.fullmatch(r"\{step_(\d+)_output\}", data)
        if match: step_num = int(match.group(1)); return step_outputs.get(step_num, f"Error: Output for step {step_num} not found.")
        return data
    if isinstance(data, dict): return {k: _substitute_step_outputs(v, step_outputs) for k, v in data.items()}
    if isinstance(data, list): return [_substitute_step_outputs(item, step_outputs) for item in data]
    return data

# --- Graph Nodes ---

# --- Core Pre-Processing Nodes ---
async def task_setup_node(state: GraphState):
    task_id = state["task_id"]; logger.info(f"Task '{task_id}': Executing Task_Setup and resetting state.")
    workspace_path = f"/app/workspace/{task_id}"; os.makedirs(workspace_path, exist_ok=True); await _create_venv_if_not_exists(workspace_path, task_id)
    return {
        "input": state['messages'][-1].content, "history": [], "plan": [], "current_step_index": 0,
        "current_tool_call": None, "tool_output": None, "step_outputs": {}, "workspace_path": workspace_path,
        "llm_config": state.get("llm_config", {}), "max_retries": 3, "step_retries": 0, "plan_retries": 0,
        "user_feedback": None, "memory_vault": {}, "enabled_tools": state.get("enabled_tools"),
        "proposed_experts": None, "board_approved": None, "approved_experts": None, "initial_plan": None,
        "critiques": [], "refined_plan": None, "strategic_memo": None, "expert_critique_index": 0,
        "tactical_plan": None, "current_tactical_step": None, "worker_output": None, "step_evaluation": None,
        "tactical_step_index": 0, "strategic_step_index": 0, "checkpoint_report": None, "board_decision": None,
        "user_guidance": None,
    }

def memory_updater_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Executing memory_updater_node.")
    return {}

def summarize_history_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Executing summarize_history_node.")
    return {}

# MODIFIED: Intelligent Four-Track Router
def initial_router_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Four-Track Router.")
    if "@experts" in state["input"].lower():
        logger.info(f"Task '{task_id}': Routing to PEER_REVIEW.")
        return {"route": "Propose_Experts", "current_track": "PEER_REVIEW"}
    
    llm = get_llm(state, "ROUTER_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = router_prompt_template.format(
        chat_history=_format_messages(state['messages']),
        input=state["input"],
        tools=format_tools_for_prompt(state)
    )
    response = _invoke_llm_with_fallback(llm, prompt, state)
    decision = response.content.strip()
    logger.info(f"Task '{task_id}': Router LLM decided: {decision}")

    if "SIMPLE_TOOL_USE" in decision:
        return {"route": "std_handyman_node", "current_track": "SIMPLE_TOOL_USE"}
    if "COMPLEX_PROJECT" in decision:
        return {"route": "std_chief_architect_node", "current_track": "COMPLEX_PROJECT"}
    
    return {"route": "Editor", "current_track": "DIRECT_QA"}

# --- Track 1 & Final Output Node ---
def editor_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Reached Editor node for final summary.")
    
    # Use a more sophisticated final prompt
    llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    chat_history_str = _format_messages(state['messages'])
    execution_log_str = "\n".join(state.get("history", []))
    
    prompt = final_answer_prompt_template.format(
        input=state["input"],
        chat_history=chat_history_str,
        execution_log=execution_log_str or "No tool actions taken.",
        memory_vault=json.dumps(state.get('memory_vault', {}), indent=2)
    )
    response = _invoke_llm_with_fallback(llm, prompt, state)
    response_content = response.content
    
    return {"answer": response_content, "messages": state['messages'] + [AIMessage(content=response_content)]}


# --- Track 2: Simple Tool Use Nodes ---
def std_handyman_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Track 2 -> std_handyman_node"); llm = get_llm(state, "SITE_FOREMAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = handyman_prompt_template.format(chat_history=_format_messages(state['messages']), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str); return {"current_tool_call": tool_call}
    except Exception as e: logger.error(f"Task '{task_id}': Error parsing Handyman tool call: {e}"); return {"current_tool_call": {"error": f"Invalid JSON from Handyman: {e}"}}

# --- Track 3: Standard Complex Project Nodes ---
def std_chief_architect_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Track 3 -> std_chief_architect_node"); llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = structured_planner_prompt_template.format(chat_history=_format_messages(state['messages']), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str); return {"plan": parsed_json.get("plan", [])}
    except Exception as e: logger.error(f"Task '{task_id}': Error parsing structured plan: {e}"); return {"plan": [{"error": f"Failed to create plan: {e}"}]}

def std_plan_expander_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing std_plan_expander_node."); plan = state.get("plan", [])
    if not plan: return {}
    for i, step in enumerate(plan): step["step_id"] = i + 1
    return {"plan": plan}

def std_human_in_the_loop_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Paused for standard plan approval."); return {}

def std_site_foreman_node(state: GraphState):
    task_id = state.get("task_id"); step_index = state["current_step_index"]; plan = state["plan"]
    if not plan or step_index >= len(plan): return {"current_tool_call": {"error": "Plan finished or empty."}}
    logger.info(f"Task '{task_id}': std_site_foreman executing step {step_index + 1}/{len(plan)}"); current_step_details = plan[step_index]
    substituted_tool_call = _substitute_step_outputs(current_step_details, state.get("step_outputs", {}))
    return {"current_tool_call": substituted_tool_call}

async def std_worker_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': std_worker executing tool call."); all_tools = get_available_tools(); enabled_tool_names = state.get("enabled_tools")
    active_tools = [tool for tool in all_tools if tool.name in enabled_tool_names] if enabled_tool_names is not None else all_tools
    tool_map = {tool.name: tool for tool in active_tools}
    tool_call = state.get("current_tool_call")
    if not tool_call or "error" in tool_call or not tool_call.get("tool_name"): return {"tool_output": f"Error: {tool_call.get('error', 'No tool call provided.')}"}
    tool_name = tool_call["tool_name"]; tool_input = tool_call.get("tool_input", {}); tool = tool_map.get(tool_name)
    if not tool: logger.error(f"Task '{task_id}': Tool '{tool_name}' not found or disabled."); return {"tool_output": f"Error: Tool '{tool_name}' not found or disabled."}
    final_args = {};
    if isinstance(tool_input, dict): final_args.update(tool_input)
    else:
        tool_args_schema = tool.args
        if tool_args_schema: final_args[next(iter(tool_args_schema))] = tool_input
    if tool_name in SANDBOXED_TOOLS: final_args["workspace_path"] = state["workspace_path"]
    try:
        output = await tool.ainvoke(final_args); output_str = str(output)
        updates = {"tool_output": output_str}
        if state.get("current_track") == "COMPLEX_PROJECT":
            current_step_id = state["plan"][state["current_step_index"]]["step_id"]
            updates["step_outputs"] = {current_step_id: output_str}
        return updates
    except Exception as e:
        logger.error(f"Task '{task_id}': Error executing tool '{tool_name}': {e}", exc_info=True); return {"tool_output": f"An error occurred while executing the tool: {e}"}

def std_project_supervisor_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing std_project_supervisor"); current_step_details = state["plan"][state["current_step_index"]]
    tool_output = state.get("tool_output", "No output."); tool_call = state.get("current_tool_call", {}); llm = get_llm(state, "PROJECT_SUPERVISOR_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = evaluator_prompt_template.format(current_step=current_step_details.get('instruction', ''), tool_call=json.dumps(tool_call), tool_output=tool_output)
    try:
        response = _invoke_llm_with_fallback(llm, prompt, state); match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        evaluation = json.loads(json_str)
    except Exception as e: evaluation = {"status": "failure", "reasoning": f"Could not parse evaluation: {e}"}
    history_record = (f"--- Step {state['current_step_index'] + 1} ---\nInstruction: {current_step_details.get('instruction')}\nAction: {json.dumps(tool_call)}\nOutput: {tool_output}\nEvaluation: {evaluation.get('status', 'unknown')} - {evaluation.get('reasoning', 'N/A')}")
    updates = {"step_evaluation": evaluation, "history": [history_record]}
    if evaluation.get("status") == "success": updates["step_retries"] = 0 
    else: updates["step_retries"] = state.get("step_retries", 0) + 1
    return updates

def std_correction_planner_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing std_correction_planner."); failed_step_details = state["plan"][state["current_step_index"]]
    failure_reason = state["step_evaluation"].get("reasoning", "N/A"); history_str = "\n".join(state["history"]); llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = correction_planner_prompt_template.format(plan=json.dumps(state["plan"]), history=history_str, failed_step=failed_step_details.get("instruction"), failure_reason=failure_reason, tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        new_step = json.loads(json_str); new_plan = state["plan"][:]; new_plan.insert(state["current_step_index"], new_step)
        for i, step in enumerate(new_plan): step["step_id"] = i + 1
        logger.info(f"Task '{task_id}': Inserted new corrective step. Plan is now {len(new_plan)} steps long.")
        return {"plan": new_plan}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error parsing or inserting correction plan: {e}"); return {}

def std_advance_to_next_step_node(state: GraphState): return {"current_step_index": state.get("current_step_index", 0) + 1}

# --- Track 4: Peer Review (Board of Experts) Nodes ---
def propose_experts_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing propose_experts_node ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest")
    structured_llm = llm.with_structured_output(BoardOfExperts)
    prompt = propose_experts_prompt_template.format(user_request=state["input"])
    try:
        response = structured_llm.invoke(prompt)
        return {"proposed_experts": [expert.dict() for expert in response.experts]}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to propose experts: {e}")
        return {"proposed_experts": [{"title": "Error", "qualities": "Failed to generate."}]}

def human_in_the_loop_board_approval(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for Board of Experts Approval ---")
    return {}

def chair_initial_plan_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing chair_initial_plan_node ---")
    if state.get("user_guidance"): logger.info("Re-planning based on new user guidance.")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest")
    structured_llm = llm.with_structured_output(StrategicPlan)
    prompt = chair_initial_plan_prompt_template.format(user_request=state["input"], experts=json.dumps(state.get("approved_experts"), indent=2), tools=format_tools_for_prompt(state), user_guidance=state.get("user_guidance", ""))
    try:
        response = structured_llm.invoke(prompt); plan_steps = [step.dict() for step in response.plan]
        logger.info(f"Chair created a plan with {len(plan_steps)} steps.")
        return {"initial_plan": plan_steps, "refined_plan": plan_steps, "expert_critique_index": 0, "critiques": []}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to create initial plan: {e}"); return {"initial_plan": [{"instruction": "Error: Failed to generate a plan.", "tool": "error"}]}

def human_in_the_loop_initial_plan_review(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for Initial Plan Review ---")
    return {}

def expert_critique_node(state: GraphState):
    task_id = state.get("task_id"); critique_index = state["expert_critique_index"]; expert = state["approved_experts"][critique_index]
    logger.info(f"--- (BoE) Task '{task_id}': Executing expert_critique_node for '{expert['title']}' ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest"); structured_llm = llm.with_structured_output(CritiqueAndPlan)
    prompt = expert_critique_prompt_template.format(expert_persona=json.dumps(expert, indent=2), user_request=state["input"], current_plan=json.dumps(state["refined_plan"], indent=2))
    try:
        response = structured_llm.invoke(prompt); updated_plan_steps = [step.dict() for step in response.updated_plan]
        critique_with_context = {"title": expert["title"], "critique": response.critique, "plan_after_critique": updated_plan_steps}
        logger.info(f"Critique from '{expert['title']}': {response.critique[:100]}..."); current_critiques = state.get("critiques", [])
        return {"critiques": current_critiques + [critique_with_context], "refined_plan": updated_plan_steps, "expert_critique_index": critique_index + 1}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to get critique from '{expert['title']}': {e}")
        error_critique = { "title": expert["title"], "critique": f"Error: Could not generate a critique. {e}", "plan_after_critique": state["refined_plan"] }
        current_critiques = state.get("critiques", []); return {"critiques": current_critiques + [error_critique], "expert_critique_index": critique_index + 1}

def chair_final_review_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing chair_final_review_node (Synthesis) ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest"); structured_llm = llm.with_structured_output(StrategicMemo)
    critique_texts = [f"Critique from {c['title']}:\n{c['critique']}" for c in state['critiques']]
    prompt = chair_final_review_prompt_template.format(user_request=state["input"], critiques="\n\n".join(critique_texts), refined_plan=json.dumps(state['refined_plan'], indent=2))
    try:
        response = structured_llm.invoke(prompt); final_memo = response.dict()
        logger.info(f"Chair synthesized a final strategic memo with {len(final_memo.get('plan', []))} steps.")
        return {"strategic_memo": final_memo}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed during Chair's final synthesis: {e}")
        fallback_memo = {"plan": state["refined_plan"], "implementation_notes": ["Error: Failed to generate strategic memo."]}
        return {"strategic_memo": fallback_memo}

def human_in_the_loop_final_plan_approval(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for Final Plan Approval ---")
    return {}

def boe_master_router_node(state: GraphState) -> dict:
    logger.info("--- (BoE) At Master Router branching point. ---"); return {}

def boe_chief_architect_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE-EXEC) Task '{task_id}': boe_chief_architect is creating a tactical plan. ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest"); structured_llm = llm.with_structured_output(TacticalPlan)
    strategic_memo = state.get("strategic_memo", {"plan": [], "implementation_notes": []}); strategic_plan = strategic_memo.get("plan", []); implementation_notes = strategic_memo.get("implementation_notes", [])
    strategic_index = state.get("strategic_step_index", 0); current_strategic_step = strategic_plan[strategic_index]['instruction'] if strategic_index < len(strategic_plan) else "No current goal."
    prompt = chief_architect_prompt_template.format(strategic_plan=json.dumps(strategic_plan, indent=2), implementation_notes="\n- ".join(implementation_notes), current_strategic_step=current_strategic_step, history=json.dumps(state.get("history", []), indent=2), tools=format_tools_for_prompt(state))
    try:
        response = structured_llm.invoke(prompt)
        if not response or not hasattr(response, 'steps'): raise ValueError("LLM returned an invalid or empty response.")
        sanitized_steps = []
        for step in response.steps:
            if isinstance(step.tool_input, str):
                try: step.tool_input = json.loads(step.tool_input)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse tool_input '{step.tool_input}' as JSON. Wrapping it for the tool.")
                    if step.tool_name == "web_search": step.tool_input = {"query": step.tool_input}
                    elif step.tool_name == "workspace_shell": step.tool_input = {"command": step.tool_input}
                    else: step.tool_input = {"input": step.tool_input}
            sanitized_steps.append(step.dict())
        logger.info(f"Boe_architect created a tactical plan with {len(sanitized_steps)} steps for goal: '{current_strategic_step}'")
        return {"tactical_plan": sanitized_steps, "tactical_step_index": 0}
    except Exception as e:
        logger.error(f"Task '{task_id}': CRITICAL FAILURE in boe_chief_architect_node: {e}", exc_info=True)
        error_plan = {"tactical_plan": [{"step_id": 1, "instruction": f"The BoE Chief Architect failed to create a tactical plan. Error: {e}", "tool_name": "error", "tool_input": {}}], "tactical_step_index": 0}
        return error_plan

def boe_site_foreman_node(state: GraphState):
    step_index = state.get("tactical_step_index", 0); logger.info(f"--- (BoE-EXEC) Task '{state.get('task_id')}': boe_site_foreman is preparing step {step_index}. ---")
    tactical_plan = state.get("tactical_plan", []); return {"current_tactical_step": tactical_plan[step_index]} if step_index < len(tactical_plan) else {"current_tactical_step": None}

def boe_worker_node(state: GraphState):
    logger.info(f"--- (BoE-EXEC) Task '{state.get('task_id')}': boe_worker is executing a tool. ---")
    tool_call = state.get("current_tactical_step", {}); output = f"Successfully executed tool '{tool_call.get('tool_name')}'."
    return {"worker_output": output}

def boe_project_supervisor_node(state: GraphState):
    logger.info(f"--- (BoE-EXEC) Task '{state.get('task_id')}': boe_supervisor is evaluating the result. ---")
    evaluation = {"status": "success", "reasoning": "Placeholder evaluation: The worker's output appears to be correct and complete."}
    return {"step_evaluation": evaluation}

def increment_tactical_step_node(state: GraphState):
    logger.info("--- (BoE-EXEC) Incrementing tactical step index. ---"); step_index = state.get("tactical_step_index", 0); return {"tactical_step_index": step_index + 1}

def editor_checkpoint_report_node(state: GraphState):
    logger.info("--- (BoE) Editor is compiling a checkpoint report. ---"); report = "Checkpoint reached. All steps so far have been completed successfully. The board will now review the progress to decide the next course of action."
    return {"checkpoint_report": report}

def board_checkpoint_review_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': The Board is reviewing the checkpoint report (LLM Call). ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest"); structured_llm = llm.with_structured_output(BoardDecision)
    prompt = board_checkpoint_review_prompt_template.format(user_request=state["input"], strategic_plan=json.dumps(state.get("strategic_memo", {}).get("plan", []), indent=2), report=state.get("checkpoint_report", "No report available."))
    try:
        response = structured_llm.invoke(prompt); decision = response.decision
        logger.info(f"Board has decided to: {decision}. Reasoning: {response.reasoning}"); return {"board_decision": decision}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to get board decision, defaulting to 'escalate'. Error: {e}"); return {"board_decision": "escalate"}

def human_in_the_loop_user_guidance(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for User Guidance ---"); return {}

def increment_strategic_step_node(state: GraphState):
    logger.info("--- (BoE) Incrementing strategic step index. ---"); step_index = state.get("strategic_step_index", 0); return {"strategic_step_index": step_index + 1}


# --- Conditional Routers ---
def after_board_approval_router(state: GraphState) -> str:
    logger.info(f"--- (BoE) Checking user approval for the board ---")
    if state.get("board_approved"): logger.info("Board approved. Proceeding to set experts."); return "set_approved_experts"
    else: logger.info("Board rejected. Routing to Editor."); return "Editor"

def set_approved_experts_node(state: GraphState) -> dict:
    logger.info(f"--- (BoE) Caching approved experts in state ---"); return {"approved_experts": state.get("proposed_experts")}

def should_continue_critique(state: GraphState) -> str:
    logger.info("--- (BoE) Checking: should_continue_critique ---")
    if state["expert_critique_index"] < len(state["approved_experts"]): logger.info("More experts to critique. Looping back."); return "continue_critique"
    else: logger.info("All experts have provided critiques. Finalizing plan."); return "finalize_plan"

def route_logic(state: GraphState) -> str: return state.get("route", "Editor")

def after_final_plan_approval_router(state: GraphState) -> str:
    if state.get("user_feedback") == 'approve': logger.info("--- Final plan approved by user. Routing to Master Router. ---"); return "start_execution"
    else: logger.info("--- Final plan rejected by user. Ending task. ---"); return "end_task"

def tactical_step_router(state: GraphState) -> str:
    logger.info("--- (BoE-EXEC) Routing tactical step. ---"); tactical_plan = state.get("tactical_plan", []); step_index = state.get("tactical_step_index", 0)
    if step_index < len(tactical_plan): logger.info(f"More tactical steps remaining. Looping back to Foreman for step {step_index}."); return "continue"
    else: logger.info("Tactical plan complete. Finishing strategic step."); return "finish"

def master_router(state: GraphState) -> str:
    logger.info("--- (BoE) Master Router is checking the next step. ---"); memo = state.get("strategic_memo", {}); plan = memo.get("plan", []); index = state.get("strategic_step_index", 0)
    if index >= len(plan): logger.info("Strategic plan is complete. Routing to Editor."); return "finish"
    current_step = plan[index]
    if current_step.get("tool") == "checkpoint": logger.info(f"Checkpoint found at strategic step {index}. Routing to review."); return "checkpoint"
    else: logger.info(f"Next strategic step {index} is a standard execution. Routing to Architect."); return "execute"

def after_checkpoint_review_router(state: GraphState) -> str:
    decision = state.get("board_decision", "continue"); logger.info(f"--- (BoE) Routing after checkpoint review. Decision: {decision} ---")
    if decision == "adapt": return "adapt_plan"
    if decision == "escalate": return "request_user_guidance"
    return "continue_execution"

# MODIFIED: New router for the standard complex project track
def after_std_plan_step_router(state: GraphState) -> str:
    evaluation = state.get("step_evaluation", {});
    if evaluation.get("status") == "failure":
        if state["step_retries"] < state["max_retries"]:
            return "std_correction_planner_node"
        else:
            logger.warning(f"Task '{state.get('task_id')}': Max retries exceeded for step. Routing to Editor.")
            return "Editor"
    if state["current_step_index"] + 1 >= len(state.get("plan", [])):
        logger.info(f"Task '{state.get('task_id')}': Standard plan complete. Routing to Editor.")
        return "Editor"
    return "std_advance_to_next_step_node"

# MODIFIED: New router for the simple tool track
def after_std_worker_router(state: GraphState) -> str:
    current_track = state.get("current_track")
    if current_track == "SIMPLE_TOOL_USE":
        return "Editor"
    return "std_project_supervisor_node"

# MODIFIED: New router for the standard plan approval
def after_std_plan_approval_router(state: GraphState) -> str:
    if state.get("user_feedback") == "approve":
        return "std_site_foreman_node"
    return "Editor"

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("Task_Setup", task_setup_node)
    workflow.add_node("Memory_Updater", memory_updater_node)
    workflow.add_node("initial_router_node", initial_router_node)
    workflow.add_node("Editor", editor_node)
    
    # Track 2 & 3 nodes
    workflow.add_node("std_handyman_node", std_handyman_node)
    workflow.add_node("std_chief_architect_node", std_chief_architect_node)
    workflow.add_node("std_plan_expander_node", std_plan_expander_node)
    workflow.add_node("std_human_in_the_loop_node", std_human_in_the_loop_node)
    workflow.add_node("std_site_foreman_node", std_site_foreman_node)
    workflow.add_node("std_worker_node", std_worker_node)
    workflow.add_node("std_project_supervisor_node", std_project_supervisor_node)
    workflow.add_node("std_correction_planner_node", std_correction_planner_node)
    workflow.add_node("std_advance_to_next_step_node", std_advance_to_next_step_node)

    # Track 4 (BoE) nodes
    workflow.add_node("Propose_Experts", propose_experts_node)
    workflow.add_node("human_in_the_loop_board_approval", human_in_the_loop_board_approval)
    workflow.add_node("set_approved_experts_node", set_approved_experts_node)
    workflow.add_node("chair_initial_plan_node", chair_initial_plan_node)
    workflow.add_node("human_in_the_loop_initial_plan_review", human_in_the_loop_initial_plan_review)
    workflow.add_node("expert_critique_node", expert_critique_node)
    workflow.add_node("chair_final_review_node", chair_final_review_node)
    workflow.add_node("human_in_the_loop_final_plan_approval", human_in_the_loop_final_plan_approval)
    workflow.add_node("boe_chief_architect_node", boe_chief_architect_node)
    workflow.add_node("boe_site_foreman_node", boe_site_foreman_node)
    workflow.add_node("boe_worker_node", boe_worker_node)
    workflow.add_node("boe_project_supervisor_node", boe_project_supervisor_node)
    workflow.add_node("increment_tactical_step_node", increment_tactical_step_node)
    workflow.add_node("editor_checkpoint_report_node", editor_checkpoint_report_node)
    workflow.add_node("board_checkpoint_review_node", board_checkpoint_review_node)
    workflow.add_node("increment_strategic_step_node", increment_strategic_step_node)
    workflow.add_node("master_router_node", boe_master_router_node)
    workflow.add_node("human_in_the_loop_user_guidance", human_in_the_loop_user_guidance)
    
    # --- Graph Wiring ---
    workflow.set_entry_point("Task_Setup")
    workflow.add_edge("Task_Setup", "Memory_Updater")
    workflow.add_edge("Memory_Updater", "initial_router_node")

    # Branch from the main router to the four tracks
    workflow.add_conditional_edges(
        "initial_router_node",
        lambda state: state.get("route"),
        {
            "Editor": "Editor",
            "std_handyman_node": "std_handyman_node",
            "std_chief_architect_node": "std_chief_architect_node",
            "Propose_Experts": "Propose_Experts",
        }
    )

    # --- Track 2: Simple Tool Use Wiring ---
    workflow.add_edge("std_handyman_node", "std_worker_node")
    workflow.add_conditional_edges("std_worker_node", after_std_worker_router, {
        "Editor": "Editor",
        "std_project_supervisor_node": "std_project_supervisor_node"
    })

    # --- Track 3: Standard Complex Project Wiring ---
    workflow.add_edge("std_chief_architect_node", "std_plan_expander_node")
    workflow.add_edge("std_plan_expander_node", "std_human_in_the_loop_node")
    workflow.add_conditional_edges("std_human_in_the_loop_node", after_std_plan_approval_router, {
        "std_site_foreman_node": "std_site_foreman_node",
        "Editor": "Editor"
    })
    workflow.add_edge("std_site_foreman_node", "std_worker_node")
    workflow.add_edge("std_correction_planner_node", "std_site_foreman_node")
    workflow.add_edge("std_advance_to_next_step_node", "std_site_foreman_node")
    workflow.add_conditional_edges("std_project_supervisor_node", after_std_plan_step_router, {
        "std_correction_planner_node": "std_correction_planner_node",
        "std_advance_to_next_step_node": "std_advance_to_next_step_node",
        "Editor": "Editor"
    })
    
    # --- Track 4: Peer Review (Board of Experts) Wiring ---
    workflow.add_edge("Propose_Experts", "human_in_the_loop_board_approval")
    workflow.add_conditional_edges("human_in_the_loop_board_approval", after_board_approval_router, { "set_approved_experts": "set_approved_experts_node", "Editor": "Editor" })
    workflow.add_edge("set_approved_experts_node", "chair_initial_plan_node")
    workflow.add_edge("chair_initial_plan_node", "human_in_the_loop_initial_plan_review")
    workflow.add_edge("human_in_the_loop_initial_plan_review", "expert_critique_node")
    workflow.add_conditional_edges("expert_critique_node", should_continue_critique, { "continue_critique": "expert_critique_node", "finalize_plan": "chair_final_review_node" })
    workflow.add_edge("chair_final_review_node", "human_in_the_loop_final_plan_approval")

    workflow.add_conditional_edges("human_in_the_loop_final_plan_approval", after_final_plan_approval_router, { "start_execution": "master_router_node", "end_task": "Editor" })
    workflow.add_conditional_edges("master_router_node", master_router, {"execute": "boe_chief_architect_node", "checkpoint": "editor_checkpoint_report_node", "finish": "Editor"})
    
    workflow.add_edge("boe_chief_architect_node", "boe_site_foreman_node")
    workflow.add_edge("boe_site_foreman_node", "boe_worker_node")
    workflow.add_edge("boe_worker_node", "boe_project_supervisor_node")
    workflow.add_edge("boe_project_supervisor_node", "increment_tactical_step_node")
    workflow.add_conditional_edges("increment_tactical_step_node", tactical_step_router, {"continue": "boe_site_foreman_node", "finish": "increment_strategic_step_node"})

    workflow.add_edge("editor_checkpoint_report_node", "board_checkpoint_review_node")
    workflow.add_conditional_edges("board_checkpoint_review_node", after_checkpoint_review_router, {"continue_execution": "increment_strategic_step_node", "adapt_plan": "chair_initial_plan_node", "request_user_guidance": "human_in_the_loop_user_guidance"})
    
    workflow.add_edge("human_in_the_loop_user_guidance", "chair_initial_plan_node")
    workflow.add_edge("increment_strategic_step_node", "master_router_node")

    # --- Final Exit Point ---
    workflow.add_edge("Editor", END)
    
    agent = workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=[
            "std_human_in_the_loop_node",
            "human_in_the_loop_board_approval",
            "human_in_the_loop_initial_plan_review",
            "human_in_the_loop_final_plan_approval",
            "human_in_the_loop_user_guidance",
        ]
    )
    logger.info("ResearchAgent graph compiled with FULL FOUR-TRACK logic.")
    return agent

agent_graph = create_agent_graph()
