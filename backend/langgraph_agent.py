# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 17 - Correction Insertion)
#
# This version significantly improves the self-correction mechanism. Instead of
# overwriting a failed step, the agent now inserts a new corrective step
# before it, preserving the original intent of the plan.
#
# Key Architectural Changes:
# 1. Smarter `correction_planner_node`:
#    - It now uses `list.insert()` to add a new corrective step at the
#      current index rather than overwriting it.
#    - After insertion, it iterates through the rest of the plan and
#      updates the `step_id` of all subsequent steps to maintain sequential
#      numbering. This is critical for the UI and for data piping.
# 2. Preserved Intent: This change ensures that after fixing a problem (like
#    installing a missing library), the agent will then retry the original
#    step that failed, making the process more logical and robust.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
import asyncio
from typing import TypedDict, Annotated, Sequence, List, Optional, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from google.api_core.exceptions import ResourceExhausted


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
    memory_updater_prompt_template
)

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
HISTORY_SUMMARY_THRESHOLD = 10
HISTORY_SUMMARY_KEEP_RECENT = 4
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files", "workspace_shell", "pip_install", "query_files", "critique_document"}


# (Memory Vault Schemas remain unchanged)
class UserProfile(TypedDict, total=False): persona: dict; preferences: dict
class KnowledgeGraphConcept(TypedDict, total=False): id: str; name: str; type: str; properties: dict
class KnowledgeGraphRelationship(TypedDict, total=False): source: str; target: str; label: str
class KnowledgeGraph(TypedDict, total=False): concepts: List[KnowledgeGraphConcept]; relationships: List[KnowledgeGraphRelationship]
class EventOrTask(TypedDict, total=False): description: str; date: str
class WorkspaceFileSummary(TypedDict, total=False): filename: str; summary: str; status: str
class MemoryVault(TypedDict, total=False): user_profile: UserProfile; knowledge_graph: KnowledgeGraph; events_and_tasks: List[EventOrTask]; workspace_summary: List[WorkspaceFileSummary]; key_observations_and_facts: List[str]

# --- Agent State Definition ---
class GraphState(TypedDict):
    input: str
    task_id: str
    plan: List[dict]
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    llm_config: Dict[str, str]
    current_step_index: int
    current_tool_call: Optional[dict]
    tool_output: Optional[str]
    history: Annotated[List[str], lambda x, y: x + y]
    workspace_path: str
    step_outputs: Annotated[Dict[int, str], lambda x, y: {**x, **y}]
    step_evaluation: Optional[dict]
    answer: str
    max_retries: int
    step_retries: int
    plan_retries: int
    user_feedback: Optional[str]
    memory_vault: MemoryVault
    route: str
    current_track: str
    enabled_tools: List[str]

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
    """
    Invokes the given LLM with a prompt. If a ResourceExhausted error
    (Google API rate limit) is caught, it retries the call once using the
    globally defined DEFAULT_LLM_ID.
    """
    try:
        return llm.invoke(prompt)
    except ResourceExhausted as e:
        task_id = state.get("task_id", "N/A")
        logger.warning(f"Task '{task_id}': LLM call failed with rate limit error: {e}. Attempting fallback.")
        
        fallback_llm_id = os.getenv("DEFAULT_LLM_ID", "gemini::gemini-1.5-flash-latest")
        logger.info(f"Task '{task_id}': Switching to fallback LLM: {fallback_llm_id}")
        
        try:
            provider, model_name = fallback_llm_id.split("::")
            if provider == "gemini":
                fallback_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
            elif provider == "ollama":
                fallback_llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
            else:
                return AIMessage(content=f"LLM call failed due to rate limits, and the fallback model '{fallback_llm_id}' is not a valid configuration. Original error: {e}")
            
            return fallback_llm.invoke(prompt)
        except Exception as fallback_e:
            logger.error(f"Task '{task_id}': Fallback LLM call also failed: {fallback_e}")
            return AIMessage(content=f"LLM call failed due to rate limits, and the fallback attempt also failed. Original error: {e}")


def format_tools_for_prompt(state: GraphState):
    all_tools = get_available_tools(); enabled_tool_names = state.get("enabled_tools")
    if enabled_tool_names is None: active_tools = all_tools
    else: active_tools = [tool for tool in all_tools if tool.name in enabled_tool_names]
    tool_strings = []
    for tool in active_tools:
        tool_string = f"  - {tool.name}: {tool.description}"
        if tool.args_schema:
            schema_props = tool.args_schema.schema().get('properties', {}); args_info = []
            for arg_name, arg_props in schema_props.items(): args_info.append(f"{arg_name} ({arg_props.get('type', 'any')}): {arg_props.get('description', '')}")
            if args_info: tool_string += " Arguments: [" + ", ".join(args_info) + "]"
        tool_strings.append(tool_string)
    return "\n".join(tool_strings) if tool_strings else "No tools are available for this task."

def _format_messages(messages: Sequence[BaseMessage], is_for_summary=False) -> str:
    formatted_messages = []; start_index = 0
    if not is_for_summary:
        first_human_message_index = next((i for i, msg in enumerate(messages) if isinstance(msg, HumanMessage)), -1)
        if first_human_message_index == -1: return "No conversation history yet."
        start_index = first_human_message_index
    for msg in messages[start_index:]:
        if isinstance(msg, SystemMessage): role = "System Summary"
        elif isinstance(msg, HumanMessage): role = "Human"
        elif isinstance(msg, AIMessage): role = "AI"
        else: continue
        formatted_messages.append(f"{role}: {msg.content}")
    if not is_for_summary: return "\n".join(formatted_messages[:-1]) if len(formatted_messages) > 1 else "No prior conversation history."
    return "\n".join(formatted_messages)

async def _create_venv_if_not_exists(workspace_path: str, task_id: str):
    venv_path = os.path.join(workspace_path, ".venv");
    if os.path.isdir(venv_path): logger.info(f"Task '{task_id}': Venv exists."); return
    logger.info(f"Task '{task_id}': Creating venv in '{workspace_path}'")
    process = await asyncio.create_subprocess_exec("uv", "venv", cwd=workspace_path, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0: logger.error(f"Task '{task_id}': Failed to create venv. Error: {stderr.decode()}")
    else: logger.info(f"Task '{task_id}': Successfully created venv.")

# --- Graph Nodes ---
async def task_setup_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Task_Setup"); user_message = state['messages'][-1].content
    workspace_path = f"/app/workspace/{task_id}"; os.makedirs(workspace_path, exist_ok=True); await _create_venv_if_not_exists(workspace_path, task_id)
    initial_vault = {"user_profile": {"persona": {},"preferences": {"formatting_style": "Markdown"}}, "knowledge_graph": {"concepts": [],"relationships": []},"events_and_tasks": [],"workspace_summary": [],"key_observations_and_facts": []}
    return {"input": user_message, "history": [], "current_step_index": 0, "step_outputs": {}, "workspace_path": workspace_path, "llm_config": state.get("llm_config", {}), "max_retries": 3, "step_retries": 0, "plan_retries": 0, "user_feedback": None, "memory_vault": initial_vault, "enabled_tools": state.get("enabled_tools")}

def memory_updater_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing memory_updater_node."); llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    prompt = memory_updater_prompt_template.format(memory_vault_json=json.dumps(state['memory_vault'], indent=2), recent_conversation=f"Human: {state['input']}")
    try:
        response = _invoke_llm_with_fallback(llm, prompt, state); match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        updated_vault = json.loads(json_str); logger.info(f"Task '{task_id}': Memory Vault updated."); return {"memory_vault": updated_vault}
    except Exception as e: logger.error(f"Task '{task_id}': Failed to parse memory vault JSON. Error: {e}. Keeping old vault."); return {}

def summarize_history_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing summarize_history_node."); messages = state['messages']; to_summarize = messages[:-HISTORY_SUMMARY_KEEP_RECENT]; to_keep = messages[-HISTORY_SUMMARY_KEEP_RECENT:]
    conversation_str = _format_messages(to_summarize, is_for_summary=True); llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest"); prompt = summarizer_prompt_template.format(conversation=conversation_str)
    response = _invoke_llm_with_fallback(llm, prompt, state); summary_text = response.content; summary_message = SystemMessage(content=f"Summary of conversation:\n{summary_text}"); new_messages = [summary_message] + to_keep; logger.info(f"Task '{task_id}': History summarized."); return {"messages": new_messages}

def initial_router_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Three-Track Router."); llm = get_llm(state, "ROUTER_LLM_ID", "gemini::gemini-1.5-flash-latest")
    router_prompt = router_prompt_template.format(chat_history=_format_messages(state['messages']), memory_vault=json.dumps(state.get('memory_vault', {}), indent=2), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, router_prompt, state); decision = response.content.strip(); logger.info(f"Task '{task_id}': Initial routing decision from LLM: {decision}")
    
    if "SIMPLE_TOOL_USE" in decision:
        return {"route": "Handyman", "current_track": "SIMPLE_TOOL_USE"}
    if "COMPLEX_PROJECT" in decision: 
        return {"route": "Chief_Architect", "current_track": "COMPLEX_PROJECT"}
    
    logger.info(f"Task '{task_id}': Routing to DIRECT_QA."); 
    return {"route": "Editor", "current_track": "DIRECT_QA"}

def handyman_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Track 2 -> Handyman"); llm = get_llm(state, "SITE_FOREMAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = handyman_prompt_template.format(chat_history=_format_messages(state['messages']), memory_vault=json.dumps(state.get('memory_vault', {}), indent=2), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str); return {"current_tool_call": tool_call}
    except Exception as e: logger.error(f"Task '{task_id}': Error parsing Handyman tool call: {e}"); return {"current_tool_call": {"error": f"Invalid JSON from Handyman: {e}"}}

def chief_architect_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Track 3 -> Chief_Architect"); llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = structured_planner_prompt_template.format(chat_history=_format_messages(state['messages']), memory_vault=json.dumps(state.get('memory_vault', {}), indent=2), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str); return {"plan": parsed_json.get("plan", [])}
    except Exception as e: logger.error(f"Task '{task_id}': Error parsing structured plan: {e}"); return {"plan": [{"error": f"Failed to create plan: {e}"}]}

def plan_expander_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Plan_Expander."); plan = state.get("plan", [])
    if not plan: return {}
    
    for i, step in enumerate(plan):
        step["step_id"] = i + 1
        
    return {"plan": plan}

def human_in_the_loop_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Reached HITL node."); return {"enabled_tools": state.get("enabled_tools")}

def _substitute_step_outputs(data: Any, step_outputs: Dict[int, str]) -> Any:
    if isinstance(data, str):
        match = re.fullmatch(r"\{step_(\d+)_output\}", data)
        if match: step_num = int(match.group(1)); return step_outputs.get(step_num, f"Error: Output for step {step_num} not found.")
        return data
    if isinstance(data, dict): return {k: _substitute_step_outputs(v, step_outputs) for k, v in data.items()}
    if isinstance(data, list): return [_substitute_step_outputs(item, step_outputs) for item in data]
    return data

def site_foreman_node(state: GraphState):
    task_id = state.get("task_id"); step_index = state["current_step_index"]; plan = state["plan"]
    if not plan or step_index >= len(plan): return {"current_tool_call": {"error": "Plan finished or empty."}}
    logger.info(f"Task '{task_id}': Site_Foreman executing step {step_index + 1}/{len(plan)}"); current_step_details = plan[step_index]
    history_summary = "\n".join([f"Step {s['step_id']}: {s['instruction']}" for s in plan[:step_index]])
    llm = get_llm(state, "SITE_FOREMAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = controller_prompt_template.format(tools=format_tools_for_prompt(state), plan=json.dumps(plan, indent=2), history=history_summary, current_step=current_step_details.get("instruction", ""))
    try:
        response = _invoke_llm_with_fallback(llm, prompt, state); match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str); substituted_tool_call = _substitute_step_outputs(tool_call, state.get("step_outputs", {})); return {"current_tool_call": substituted_tool_call}
    except Exception as e: logger.error(f"Task '{task_id}': Error in Foreman: {e}"); return {"current_tool_call": {"error": f"Invalid JSON or substitution error: {e}"}}

async def worker_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Worker executing tool call."); all_tools = get_available_tools(); enabled_tool_names = state.get("enabled_tools")
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
        
        if state.get("current_track") == "COMPLEX_PROJECT":
            current_step_id = state["plan"][state["current_step_index"]]["step_id"]
            step_outputs = {current_step_id: output_str}
            return {"tool_output": output_str, "step_outputs": step_outputs}

        elif state.get("current_track") == "SIMPLE_TOOL_USE":
            history_record = (f"Handyman Action: User requested '{state['input']}'.\nExecuted Tool: {json.dumps(tool_call)}\nResult: {output_str}")
            return {"tool_output": output_str, "history": [history_record], "messages": [AIMessage(content=f"Tool execution result: {output_str}")]}
            
        return {"tool_output": output_str}

    except Exception as e:
        logger.error(f"Task '{task_id}': Error executing tool '{tool_name}': {e}", exc_info=True); return {"tool_output": f"An error occurred while executing the tool: {e}"}

def project_supervisor_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Project_Supervisor"); current_step_details = state["plan"][state["current_step_index"]]
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

def advance_to_next_step_node(state: GraphState): return {"current_step_index": state.get("current_step_index", 0) + 1}

def editor_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Unified Editor generating final answer."); llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    chat_history_str = _format_messages(state['messages']); execution_log_str = "\n".join(state.get("history", [])); memory_vault_str = json.dumps(state.get('memory_vault', {}), indent=2)
    prompt = final_answer_prompt_template.format(input=state["input"], chat_history=chat_history_str, execution_log=execution_log_str or "No tool actions taken.", memory_vault=memory_vault_str)
    response = _invoke_llm_with_fallback(llm, prompt, state); response_content = response.content; return {"answer": response_content, "messages": [AIMessage(content=response_content)]}

# --- MODIFIED: The correction planner now inserts a step instead of replacing it ---
def correction_planner_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Correction_Planner."); failed_step_details = state["plan"][state["current_step_index"]]
    failure_reason = state["step_evaluation"].get("reasoning", "N/A"); history_str = "\n".join(state["history"]); llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = correction_planner_prompt_template.format(plan=json.dumps(state["plan"]), history=history_str, failed_step=failed_step_details.get("instruction"), failure_reason=failure_reason, tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        new_step = json.loads(json_str)
        
        # Create a copy of the plan to modify
        new_plan = state["plan"][:]
        # Insert the new corrective step *before* the failed step
        new_plan.insert(state["current_step_index"], new_step)
        
        # Re-number all steps in the plan to maintain sequential integrity
        for i, step in enumerate(new_plan):
            step["step_id"] = i + 1
            
        logger.info(f"Task '{task_id}': Inserted new corrective step. Plan is now {len(new_plan)} steps long.")
        return {"plan": new_plan}

    except Exception as e:
        logger.error(f"Task '{task_id}': Error parsing or inserting correction plan: {e}");
        # Return an empty dictionary to indicate no change to the plan
        return {}


# --- MODIFIED: The router no longer advances the step after a correction ---
def after_plan_step_router(state: GraphState) -> str:
    evaluation = state.get("step_evaluation", {});
    if evaluation.get("status") == "failure":
        if state["step_retries"] < state["max_retries"]:
            # On failure, go to the correction planner. The index is NOT advanced.
            return "Correction_Planner"
        else:
            logger.warning(f"Task '{state.get('task_id')}': Max retries exceeded for step. Routing to Editor.")
            return "Editor"

    # On success, check if we are at the end of the plan
    if state["current_step_index"] + 1 >= len(state.get("plan", [])):
        logger.info(f"Task '{state.get('task_id')}': Plan complete. Routing to Editor.")
        return "Editor"
    
    # If successful and not at the end, advance to the next step
    return "Advance_To_Next_Step"

def history_management_router(state: GraphState) -> str: return "summarize_history_node" if len(state['messages']) > HISTORY_SUMMARY_THRESHOLD else "initial_router_node"
def route_logic(state: GraphState) -> str: return state.get("route", "Editor")
def after_worker_router(state: GraphState) -> str: return "Editor" if state.get("current_track") == "SIMPLE_TOOL_USE" else "Project_Supervisor"
def after_plan_creation_router(state: GraphState) -> str: return "Site_Foreman" if state.get("user_feedback") == "approve" else "Editor"

def create_agent_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("Task_Setup", task_setup_node); workflow.add_node("Memory_Updater", memory_updater_node); workflow.add_node("summarize_history_node", summarize_history_node)
    workflow.add_node("initial_router_node", initial_router_node); workflow.add_node("Handyman", handyman_node); workflow.add_node("Chief_Architect", chief_architect_node)
    workflow.add_node("Plan_Expander", plan_expander_node); workflow.add_node("human_in_the_loop_node", human_in_the_loop_node); workflow.add_node("Site_Foreman", site_foreman_node)
    workflow.add_node("Worker", worker_node); workflow.add_node("Project_Supervisor", project_supervisor_node); workflow.add_node("Advance_To_Next_Step", advance_to_next_step_node)
    workflow.add_node("Editor", editor_node); workflow.add_node("Correction_Planner", correction_planner_node)
    workflow.set_entry_point("Task_Setup"); workflow.add_edge("Task_Setup", "Memory_Updater")
    workflow.add_conditional_edges("Memory_Updater", history_management_router, {"summarize_history_node": "summarize_history_node", "initial_router_node": "initial_router_node"})
    workflow.add_edge("summarize_history_node", "initial_router_node")
    workflow.add_conditional_edges("initial_router_node", route_logic, {"Editor": "Editor", "Handyman": "Handyman", "Chief_Architect": "Chief_Architect"})
    workflow.add_edge("Handyman", "Worker"); workflow.add_conditional_edges("Worker", after_worker_router, {"Editor": "Editor", "Project_Supervisor": "Project_Supervisor"})
    workflow.add_edge("Chief_Architect", "Plan_Expander"); workflow.add_edge("Plan_Expander", "human_in_the_loop_node")
    workflow.add_conditional_edges("human_in_the_loop_node", after_plan_creation_router, {"Site_Foreman": "Site_Foreman", "Editor": "Editor"})
    workflow.add_edge("Site_Foreman", "Worker")
    
    # --- MODIFIED: The edge from the Correction Planner goes directly back to the Foreman ---
    # This ensures the newly inserted step is executed immediately without advancing the index.
    workflow.add_edge("Correction_Planner", "Site_Foreman")
    
    workflow.add_edge("Advance_To_Next_Step", "Site_Foreman")
    workflow.add_conditional_edges("Project_Supervisor", after_plan_step_router, {"Editor": "Editor", "Advance_To_Next_Step": "Advance_To_Next_Step", "Correction_Planner": "Correction_Planner"})
    workflow.add_edge("Editor", END)
    agent = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["human_in_the_loop_node"])
    logger.info("ResearchAgent graph compiled with improved correction logic."); return agent

agent_graph = create_agent_graph()
