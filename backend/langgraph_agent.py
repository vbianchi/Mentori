# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 11.6: Venv-Aware Worker)
#
# This version completes the implementation of per-task virtual environments.
#
# 1. Venv-Aware `worker_node`: The worker node is updated to recognize the
#    new `pip_install` tool as a sandboxed tool. It now correctly passes the
#    task-specific `workspace_path` to it, ensuring that package
#    installations are correctly routed to the appropriate virtual
#    environment. This completes the logic for Phase 11.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
import asyncio
from typing import TypedDict, Annotated, Sequence, List, Optional, Dict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# --- Local Imports ---
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

# --- Constants for Summarization ---
HISTORY_SUMMARY_THRESHOLD = 10
HISTORY_SUMMARY_KEEP_RECENT = 4

# --- Memory Vault Schema Definition ---
class UserProfile(TypedDict, total=False):
    persona: dict
    preferences: dict

class KnowledgeGraphConcept(TypedDict, total=False):
    id: str
    name: str
    type: str
    properties: dict

class KnowledgeGraphRelationship(TypedDict, total=False):
    source: str
    target: str
    label: str

class KnowledgeGraph(TypedDict, total=False):
    concepts: List[KnowledgeGraphConcept]
    relationships: List[KnowledgeGraphRelationship]

class EventOrTask(TypedDict, total=False):
    description: str
    date: str

class WorkspaceFileSummary(TypedDict, total=False):
    filename: str
    summary: str
    status: str

class MemoryVault(TypedDict, total=False):
    user_profile: UserProfile
    knowledge_graph: KnowledgeGraph
    events_and_tasks: List[EventOrTask]
    workspace_summary: List[WorkspaceFileSummary]
    key_observations_and_facts: List[str]


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

# --- LLM Provider Helper ---
LLM_CACHE = {}
def get_llm(state: GraphState, role_env_var: str, default_llm_id: str):
    run_config = state.get("llm_config", {})
    llm_id = run_config.get(role_env_var) or os.getenv(role_env_var, default_llm_id)
    if llm_id in LLM_CACHE: return LLM_CACHE[llm_id]
 
    provider, model_name = llm_id.split("::")
    logger.info(f"Task '{state.get('task_id')}': Initializing LLM for '{role_env_var}': {llm_id}")
    if provider == "gemini": llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif provider == "ollama": llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
    else: raise ValueError(f"Unsupported LLM provider: {provider}")
    LLM_CACHE[llm_id] = llm
    return llm

# --- Tool Management ---
AVAILABLE_TOOLS = get_available_tools()
TOOL_MAP = {tool.name: tool for tool in AVAILABLE_TOOLS}
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files", "workspace_shell"}
def format_tools_for_prompt():
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- History Formatting Helper ---
def _format_messages(messages: Sequence[BaseMessage], is_for_summary=False) -> str:
    formatted_messages = []
    
    start_index = 0
    if not is_for_summary:
        first_human_message_index = next((i for i, msg in enumerate(messages) if isinstance(msg, HumanMessage)), -1)
        if first_human_message_index == -1: return "No conversation history yet."
        start_index = first_human_message_index

    for msg in messages[start_index:]:
        if isinstance(msg, SystemMessage):
            role = "System Summary"
        elif isinstance(msg, HumanMessage):
            role = "Human"
        elif isinstance(msg, AIMessage):
            role = "AI"
        else:
            continue
        formatted_messages.append(f"{role}: {msg.content}")
    
    if not is_for_summary:
        return "\n".join(formatted_messages[:-1]) if len(formatted_messages) > 1 else "No prior conversation history for this task."
    
    return "\n".join(formatted_messages)

# --- Venv Creation Helper ---
async def _create_venv_if_not_exists(workspace_path: str, task_id: str):
    """Creates a virtual environment in the workspace if one doesn't exist."""
    venv_path = os.path.join(workspace_path, ".venv")
    if os.path.isdir(venv_path):
        logger.info(f"Task '{task_id}': Virtual environment already exists. Skipping creation.")
        return

    logger.info(f"Task '{task_id}': Creating virtual environment in '{workspace_path}'")
    command = ["uv", "venv"]
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=workspace_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_message = stderr.decode()
        logger.error(f"Task '{task_id}': Failed to create virtual environment. Error: {error_message}")
    else:
        logger.info(f"Task '{task_id}': Successfully created virtual environment.")


# --- Graph Nodes ---
async def task_setup_node(state: GraphState):
    """Creates the workspace and virtual environment, and initializes state."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing async Task_Setup")
    user_message = state['messages'][-1].content
    
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)
    
    await _create_venv_if_not_exists(workspace_path, task_id)

    initial_vault = {
        "user_profile": { "persona": {}, "preferences": { "formatting_style": "Markdown" } },
        "knowledge_graph": { "concepts": [], "relationships": [] },
        "events_and_tasks": [],
        "workspace_summary": [],
        "key_observations_and_facts": []
    }
    
    return {
        "input": user_message, "history": [], "current_step_index": 0, 
        "step_outputs": {}, "workspace_path": workspace_path, 
        "llm_config": state.get("llm_config", {}), "max_retries": 3,
        "step_retries": 0, "plan_retries": 0, "user_feedback": None,
        "memory_vault": initial_vault
    }

def memory_updater_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing memory_updater_node.")

    llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    
    recent_conversation = f"Human: {state['input']}"

    prompt = memory_updater_prompt_template.format(
        memory_vault_json=json.dumps(state['memory_vault'], indent=2),
        recent_conversation=recent_conversation
    )

    try:
        response = llm.invoke(prompt)
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        updated_vault = json.loads(json_str)
        logger.info(f"Task '{task_id}': Memory Vault updated successfully.")
        return {"memory_vault": updated_vault}
    except Exception as e:
        logger.error(f"Task '{task_id}': CRITICAL: Failed to parse or validate updated memory vault JSON. Error: {e}. Keeping old vault.")
        return {}

def summarize_history_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing summarize_history_node.")
    
    messages = state['messages']
    to_summarize = messages[:-HISTORY_SUMMARY_KEEP_RECENT]
    to_keep = messages[-HISTORY_SUMMARY_KEEP_RECENT:]
    
    conversation_str = _format_messages(to_summarize, is_for_summary=True)
    
    llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    prompt = summarizer_prompt_template.format(conversation=conversation_str)
    
    logger.info(f"Task '{task_id}': Summarizing {len(to_summarize)} messages...")
    summary_response = llm.invoke(prompt)
    summary_text = summary_response.content
    
    summary_message = SystemMessage(content=f"This is a summary of the conversation so far:\n{summary_text}")
    
    new_messages = [summary_message] + to_keep
    
    logger.info(f"Task '{task_id}': History summarized. New message count: {len(new_messages)}")
    return {"messages": new_messages}


def initial_router_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Three-Track Router.")
    llm = get_llm(state, "ROUTER_LLM_ID", "gemini::gemini-1.5-flash-latest")
    
    chat_history = _format_messages(state['messages'])
    memory_vault_str = json.dumps(state.get('memory_vault', {}), indent=2)

    prompt = router_prompt_template.format(
        chat_history=chat_history,
        memory_vault=memory_vault_str,
        input=state["input"], 
        tools=format_tools_for_prompt()
    )
    
    response = llm.invoke(prompt)
    decision = response.content.strip()
    
    logger.info(f"Task '{task_id}': Routing decision: {decision}")

    if "DIRECT_QA" in decision: return {"route": "Editor", "current_track": "DIRECT_QA"}
    if "SIMPLE_TOOL_USE" in decision: return {"route": "Handyman", "current_track": "SIMPLE_TOOL_USE"}
    if "COMPLEX_PROJECT" in decision: return {"route": "Chief_Architect", "current_track": "COMPLEX_PROJECT"}
    
    logger.warning(f"Task '{task_id}': Router gave unexpected response '{decision}'. Defaulting to Editor.")
    return {"route": "Editor", "current_track": "DIRECT_QA"}

def handyman_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Track 2 -> Handyman")
    llm = get_llm(state, "SITE_FOREMAN_LLM_ID", "gemini::gemini-1.5-flash-latest")

    chat_history = _format_messages(state['messages'])
    memory_vault_str = json.dumps(state.get('memory_vault', {}), indent=2)

    prompt = handyman_prompt_template.format(
        chat_history=chat_history,
        memory_vault=memory_vault_str,
        input=state["input"], 
        tools=format_tools_for_prompt()
    )
    
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str)
        return {"current_tool_call": tool_call}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error parsing tool call from Handyman: {e}")
        return {"current_tool_call": {"error": f"Invalid JSON output from Handyman: {e}"}}

def chief_architect_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Track 3 -> Chief_Architect")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")

    chat_history = _format_messages(state['messages'])
    memory_vault_str = json.dumps(state.get('memory_vault', {}), indent=2)
    
    prompt = structured_planner_prompt_template.format(
        chat_history=chat_history,
        memory_vault=memory_vault_str,
        input=state["input"], 
        tools=format_tools_for_prompt()
    )

    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str)
        return {"plan": parsed_json.get("plan", [])}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error parsing structured plan: {e}")
        return {"plan": [{"error": f"Failed to create a valid plan. Reason: {e}"}]}

def human_in_the_loop_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Reached HITL node. Awaiting user feedback.")
    return {}

def site_foreman_node(state: GraphState):
    task_id = state.get("task_id")
    step_index = state["current_step_index"]
    plan = state["plan"]
    if not plan or step_index >= len(plan): return {"current_tool_call": {"error": "Plan is empty or finished."}}
    logger.info(f"Task '{task_id}': Executing Site_Foreman for step {step_index + 1}/{len(plan)}")
    current_step_details = plan[step_index]
    llm = get_llm(state, "SITE_FOREMAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    history_str = "\n".join(state["history"]) if state.get("history") else "No history yet."
    prompt = controller_prompt_template.format(tools=format_tools_for_prompt(), plan=json.dumps(state["plan"], indent=2), history=history_str, current_step=current_step_details.get("instruction", ""))
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str)
        return {"current_tool_call": tool_call}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error parsing tool call from Site Foreman: {e}")
        return {"current_tool_call": {"error": f"Invalid JSON output from Site Foreman: {e}"}}

async def worker_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Worker executing tool call.")
    tool_call = state.get("current_tool_call")
    if not tool_call or "error" in tool_call or not tool_call.get("tool_name"):
        error_msg = tool_call.get("error", "No tool call was provided.")
        return {"tool_output": f"Error: {error_msg}"}
    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", {})
    tool = TOOL_MAP.get(tool_name)
    if not tool: return {"tool_output": f"Error: Tool '{tool_name}' not found."}
    final_args = {}
    if isinstance(tool_input, dict): final_args.update(tool_input)
    else:
        tool_args_schema = tool.args
        if tool_args_schema: final_args[next(iter(tool_args_schema))] = tool_input
        
    # --- THIS IS THE FIX ---
    # We now check for pip_install by name to ensure it gets the workspace path.
    if tool_name in SANDBOXED_TOOLS or tool.name == 'pip_install':
        final_args["workspace_path"] = state["workspace_path"]
        
    try:
        output = await tool.ainvoke(final_args)
        output_str = str(output)
        if state.get("current_track") == "SIMPLE_TOOL_USE":
            history_record = (f"Handyman Action: User requested '{state['input']}'.\n" f"Executed Tool: {json.dumps(tool_call)}\n" f"Result: {output_str}")
            return {"tool_output": output_str, "history": [history_record], "messages": [AIMessage(content=f"Tool execution result: {output_str}")]}
        return {"tool_output": output_str}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}

def project_supervisor_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Project_Supervisor")
    current_step_details = state["plan"][state["current_step_index"]]
    tool_output = state.get("tool_output", "No output from tool.")
    tool_call = state.get("current_tool_call", {})
    llm = get_llm(state, "PROJECT_SUPERVISOR_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = evaluator_prompt_template.format(current_step=current_step_details.get('instruction', ''), tool_call=json.dumps(tool_call), tool_output=tool_output)
    try:
        response = llm.invoke(prompt)
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        evaluation = json.loads(json_str)
    except Exception as e:
        evaluation = {"status": "failure", "reasoning": f"Could not parse evaluation: {e}"}
    history_record = (f"--- Step {state['current_step_index'] + 1} ---\n" f"Instruction: {current_step_details.get('instruction')}\n" f"Action: {json.dumps(tool_call)}\n" f"Output: {tool_output}\n" f"Evaluation: {evaluation.get('status', 'unknown')} - {evaluation.get('reasoning', 'N/A')}")
    updates = {"step_evaluation": evaluation, "history": [history_record]}
    if evaluation.get("status") == "success":
        updates["step_retries"] = 0 
    else:
        updates["step_retries"] = state.get("step_retries", 0) + 1
    return updates

def advance_to_next_step_node(state: GraphState):
    return {"current_step_index": state.get("current_step_index", 0) + 1}

def editor_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Unified Editor generating final answer with full context.")
    llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    
    chat_history_str = _format_messages(state['messages'])
    execution_log_str = "\n".join(state.get("history", []))
    memory_vault_str = json.dumps(state.get('memory_vault', {}), indent=2)

    prompt = final_answer_prompt_template.format(
        input=state["input"], 
        chat_history=chat_history_str,
        execution_log=execution_log_str if execution_log_str else "No tool actions were taken in this turn.",
        memory_vault=memory_vault_str
    )
    
    response_content = llm.invoke(prompt).content

    return {"answer": response_content, "messages": [AIMessage(content=response_content)]}

def correction_planner_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Correction_Planner.")
    failed_step_details = state["plan"][state["current_step_index"]]
    failure_reason = state["step_evaluation"].get("reasoning", "No reason provided.")
    history_str = "\n".join(state["history"])
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = correction_planner_prompt_template.format(plan=json.dumps(state["plan"]), history=history_str, failed_step=failed_step_details.get("instruction"), failure_reason=failure_reason, tools=format_tools_for_prompt())
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        new_step = json.loads(json_str)
        new_plan = state["plan"][:]
        new_plan[state["current_step_index"]] = new_step
        return {"plan": new_plan}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error parsing correction plan: {e}")
        return {}

# --- Conditional Routing Logic ---
def history_management_router(state: GraphState) -> str:
    if len(state['messages']) > HISTORY_SUMMARY_THRESHOLD:
        logger.info(f"Task '{state.get('task_id')}': History length ({len(state['messages'])}) exceeds threshold. Routing to summarizer.")
        return "summarize_history_node"
    logger.info(f"Task '{state.get('task_id')}': History length ({len(state['messages'])}) is within threshold. Skipping summarizer.")
    return "initial_router_node"

def route_logic(state: GraphState) -> str:
    return state.get("route", "Editor")

def after_worker_router(state: GraphState) -> str:
    if state.get("current_track") == "SIMPLE_TOOL_USE": return "Editor"
    return "Project_Supervisor"

def after_plan_creation_router(state: GraphState) -> str:
    if state.get("user_feedback") == "approve": return "Site_Foreman"
    return "Editor"

def after_plan_step_router(state: GraphState) -> str:
    evaluation = state.get("step_evaluation", {})
    if evaluation.get("status") == "failure":
        if state["step_retries"] < state["max_retries"]: return "Correction_Planner"
        return "Editor"
    if state["current_step_index"] + 1 >= len(state.get("plan", [])): return "Editor"
    return "Advance_To_Next_Step"

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("Task_Setup", task_setup_node)
    workflow.add_node("Memory_Updater", memory_updater_node)
    workflow.add_node("summarize_history_node", summarize_history_node)
    workflow.add_node("initial_router_node", initial_router_node)
    workflow.add_node("Handyman", handyman_node)
    workflow.add_node("Chief_Architect", chief_architect_node)
    workflow.add_node("human_in_the_loop_node", human_in_the_loop_node)
    workflow.add_node("Site_Foreman", site_foreman_node)
    workflow.add_node("Worker", worker_node)
    workflow.add_node("Project_Supervisor", project_supervisor_node)
    workflow.add_node("Advance_To_Next_Step", advance_to_next_step_node)
    workflow.add_node("Editor", editor_node)
    workflow.add_node("Correction_Planner", correction_planner_node)
    
    workflow.set_entry_point("Task_Setup")
    workflow.add_edge("Task_Setup", "Memory_Updater")
    
    workflow.add_conditional_edges(
        "Memory_Updater",
        history_management_router,
        {
            "summarize_history_node": "summarize_history_node",
            "initial_router_node": "initial_router_node"
        }
    )
    workflow.add_edge("summarize_history_node", "initial_router_node")
    
    workflow.add_conditional_edges(
        "initial_router_node", route_logic,
        {"Editor": "Editor", "Handyman": "Handyman", "Chief_Architect": "Chief_Architect"}
    )

    workflow.add_edge("Handyman", "Worker")
    workflow.add_conditional_edges(
        "Worker", after_worker_router,
        {"Editor": "Editor", "Project_Supervisor": "Project_Supervisor"}
    )
    
    workflow.add_edge("Chief_Architect", "human_in_the_loop_node")
    workflow.add_conditional_edges("human_in_the_loop_node", after_plan_creation_router, {
        "Site_Foreman": "Site_Foreman", "Editor": "Editor"
    })
    
    workflow.add_edge("Site_Foreman", "Worker")
    workflow.add_edge("Advance_To_Next_Step", "Site_Foreman")
    workflow.add_edge("Correction_Planner", "Site_Foreman")
    workflow.add_conditional_edges("Project_Supervisor", after_plan_step_router, {
        "Editor": "Editor", "Advance_To_Next_Step": "Advance_To_Next_Step",
        "Correction_Planner": "Correction_Planner"
    })

    workflow.add_edge("Editor", END)

    agent = workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["human_in_the_loop_node"]
    )
    logger.info("ResearchAgent graph compiled with definitive Memory Vault architecture.")
    return agent

agent_graph = create_agent_graph()
