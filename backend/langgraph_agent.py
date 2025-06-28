# backend/langgraph_agent.py
# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 17 - BoE Interrupt Implementation)
#
# This version refactors the Board of Experts (BoE) track by integrating its
# nodes directly into the main graph. This simplifies the architecture and
# allows for native handling of user interrupts.
#
# Key Architectural Changes:
# 1. BoE Nodes Integrated: The nodes from the now-deleted
#    `board_of_experts_graph.py` (propose_experts_node, etc.) are now
#    defined directly within this file.
# 2. First User Interrupt: The main graph is compiled with
#    `interrupt_before=["human_in_the_loop_board_approval"]`. This makes
#    the graph run the `propose_experts_node` and then pause execution,
#    waiting for the user to approve the proposed board.
# 3. New Conditional Edge: A new router, `after_board_approval_router`,
#    is added to check the user's feedback (`board_approved` in the state)
#    and either proceed with the plan or route to the Editor if rejected.
# 4. State Expansion: `GraphState` is updated with `board_approved` to
#    manage the user's decision from the new interrupt point.
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
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field


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

class GraphState(TypedDict):
    # Core state
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

    # State for Tracks 2 & 3
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
    user_feedback: Optional[str]

    # State for Track 4 (Board of Experts)
    proposed_experts: Optional[List[dict]]
    board_approved: Optional[bool]
    initial_plan: Optional[List[dict]]
    critiques: Optional[List[str]]
    final_plan: Optional[List[dict]]
    execution_history: Optional[List[str]]
    checkpoint_report: Optional[str]
    user_guidance: Optional[str]
    board_decision: Optional[str]

# --- Prompts ---
propose_experts_prompt_template = PromptTemplate.from_template(
"""You are a master project manager. Based on the user's request, your job is to assemble a small, elite "Board of Experts" to oversee the project.
**User Request:**
{user_request}
**Instructions:**
1.  Analyze the user's request to understand the core domains of expertise required.
2.  Propose a board of 3 to 4 diverse and relevant expert personas.
3.  For each expert, provide a clear title and a concise summary of their essential qualities.
4.  Return the board as a structured JSON object."""
)

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
    try:
        return llm.invoke(prompt)
    except ResourceExhausted as e:
        task_id = state.get("task_id", "N/A"); logger.warning(f"Task '{task_id}': LLM call failed: {e}. Retrying with fallback.")
        fallback_llm_id = os.getenv("DEFAULT_LLM_ID", "gemini::gemini-1.5-flash-latest"); logger.info(f"Task '{task_id}': Fallback: {fallback_llm_id}")
        try:
            provider, model_name = fallback_llm_id.split("::")
            if provider == "gemini": fallback_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
            elif provider == "ollama": fallback_llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
            else: return AIMessage(content=f"LLM call failed, fallback '{fallback_llm_id}' invalid. Error: {e}")
            return fallback_llm.invoke(prompt)
        except Exception as fallback_e:
            logger.error(f"Task '{task_id}': Fallback LLM call failed: {fallback_e}")
            return AIMessage(content=f"LLM call failed, fallback also failed. Error: {e}")

def format_tools_for_prompt(state: GraphState):
    all_tools = get_available_tools(); enabled_tool_names = state.get("enabled_tools")
    active_tools = [t for t in all_tools if t.name in enabled_tool_names] if enabled_tool_names is not None else all_tools
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
    return {
        "input": user_message, "history": [], "current_step_index": 0, "step_outputs": {}, 
        "workspace_path": workspace_path, "llm_config": state.get("llm_config", {}), 
        "max_retries": 3, "step_retries": 0, "plan_retries": 0, "user_feedback": None, 
        "memory_vault": initial_vault, "enabled_tools": state.get("enabled_tools"),
        "proposed_experts": None, "board_approved": None, "initial_plan": None, 
        "critiques": [], "final_plan": None, "execution_history": [], 
        "checkpoint_report": None, "user_guidance": None, "board_decision": None
    }

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
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Four-Track Router.");
    if "@experts" in state["input"].lower():
        logger.info(f"Task '{task_id}': Routing to Propose_Experts.")
        return {"route": "Propose_Experts", "current_track": "BOARD_OF_EXPERTS_PROJECT"}
    llm = get_llm(state, "ROUTER_LLM_ID", "gemini::gemini-1.5-flash-latest")
    router_prompt = router_prompt_template.format(chat_history=_format_messages(state['messages']), memory_vault=json.dumps(state.get('memory_vault', {}), indent=2), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, router_prompt, state); decision = response.content.strip();
    if "BOARD_OF_EXPERTS_PROJECT" in decision: return {"route": "Propose_Experts", "current_track": "BOARD_OF_EXPERTS_PROJECT"}
    if "SIMPLE_TOOL_USE" in decision: return {"route": "Handyman", "current_track": "SIMPLE_TOOL_USE"}
    if "COMPLEX_PROJECT" in decision: return {"route": "Chief_Architect", "current_track": "COMPLEX_PROJECT"}
    return {"route": "Editor", "current_track": "DIRECT_QA"}

def propose_experts_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing propose_experts_node ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest")
    structured_llm = llm.with_structured_output(BoardOfExperts)
    prompt = propose_experts_prompt_template.format(user_request=state["input"])
    try:
        response = structured_llm.invoke(prompt)
        proposed_experts = [expert.dict() for expert in response.experts]
        return {"proposed_experts": proposed_experts}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to get structured output for experts: {e}")
        return {"proposed_experts": [{"title": "General Analyst", "qualities": "Error during generation."}]}

def human_in_the_loop_board_approval(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for Board of Experts Approval ---")
    return {}

def chair_initial_plan_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing Placeholder: chair_initial_plan_node ---")
    return {"answer": "Board has been approved. The Chair would now create a plan."}

def handyman_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Track 2 -> Handyman"); llm = get_llm(state, "SITE_FOREMAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = handyman_prompt_template.format(chat_history=_format_messages(state['messages']), memory_vault=json.dumps(state.get('memory_vault', {}), indent=2), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        return {"current_tool_call": json.loads(json_str)}
    except Exception as e: return {"current_tool_call": {"error": f"Invalid JSON from Handyman: {e}"}}

def chief_architect_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Track 3 -> Chief_Architect"); llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = structured_planner_prompt_template.format(chat_history=_format_messages(state['messages']), memory_vault=json.dumps(state.get('memory_vault', {}), indent=2), input=state["input"], tools=format_tools_for_prompt(state))
    response = _invoke_llm_with_fallback(llm, prompt, state)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL); json_str = match.group(1).strip() if match else response.content.strip()
        return {"plan": json.loads(json_str).get("plan", [])}
    except Exception as e: return {"plan": [{"error": f"Failed to create plan: {e}"}]}

def plan_expander_node(state: GraphState):
    plan = state.get("plan", []); [step.update({"step_id": i + 1}) for i, step in enumerate(plan)]
    return {"plan": plan} if plan else {}

def human_in_the_loop_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Reached HITL node."); return {}

def _substitute_step_outputs(data: Any, step_outputs: Dict[int, str]) -> Any:
    if isinstance(data, str):
        match = re.fullmatch(r"\{step_(\d+)_output\}", data)
        if match: return step_outputs.get(int(match.group(1)), f"Error: Output for step {match.group(1)} not found.")
        return data
    if isinstance(data, dict): return {k: _substitute_step_outputs(v, step_outputs) for k, v in data.items()}
    if isinstance(data, list): return [_substitute_step_outputs(item, step_outputs) for item in data]
    return data

def site_foreman_node(state: GraphState):
    # Unchanged
    return {}

async def worker_node(state: GraphState):
    # Unchanged
    return {}

def project_supervisor_node(state: GraphState):
    # Unchanged
    return {}

def advance_to_next_step_node(state: GraphState): return {"current_step_index": state.get("current_step_index", 0) + 1}

def correction_planner_node(state: GraphState):
    # Unchanged
    return {}
    
def editor_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Unified Editor generating final answer.")
    if (final_answer := state.get("answer")) is not None:
         return {"answer": final_answer, "messages": [AIMessage(content=final_answer)]}
    llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    architect_history = state.get("history") or []
    boe_history = state.get("execution_history") or []
    combined_history = architect_history + boe_history
    chat_history_str = _format_messages(state['messages']); execution_log_str = "\n".join(combined_history); memory_vault_str = json.dumps(state.get('memory_vault', {}), indent=2)
    prompt = final_answer_prompt_template.format(input=state["input"], chat_history=chat_history_str, execution_log=execution_log_str or "No actions taken.", memory_vault=memory_vault_str)
    response = _invoke_llm_with_fallback(llm, prompt, state); response_content = response.content; 
    return {"answer": response_content, "messages": [AIMessage(content=response_content)]}

# --- Conditional Routers ---
def after_board_approval_router(state: GraphState) -> str:
    logger.info(f"--- (BoE) Checking user approval for the board ---")
    if state.get("board_approved"):
        logger.info("Board approved. Proceeding to planning.")
        return "chair_initial_plan_node"
    else:
        logger.info("Board rejected. Routing to Editor.")
        return "Editor"

def route_logic(state: GraphState) -> str: return state.get("route", "Editor")
def after_worker_router(state: GraphState) -> str: return "Editor" if state.get("current_track") == "SIMPLE_TOOL_USE" else "Project_Supervisor"
def after_plan_creation_router(state: GraphState) -> str: return "Site_Foreman" if state.get("user_feedback") == "approve" else "Editor"
def after_plan_step_router(state: GraphState) -> str:
    # Unchanged
    return "Editor"

def history_management_router(state: GraphState) -> str: return "summarize_history_node" if len(state['messages']) > HISTORY_SUMMARY_THRESHOLD else "initial_router_node"

def create_agent_graph():
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("Task_Setup", task_setup_node)
    workflow.add_node("Memory_Updater", memory_updater_node)
    workflow.add_node("summarize_history_node", summarize_history_node)
    workflow.add_node("initial_router_node", initial_router_node)
    workflow.add_node("Editor", editor_node)
    
    # BoE Track Nodes
    workflow.add_node("Propose_Experts", propose_experts_node)
    workflow.add_node("human_in_the_loop_board_approval", human_in_the_loop_board_approval)
    workflow.add_node("chair_initial_plan_node", chair_initial_plan_node)

    # Other Track Nodes
    workflow.add_node("Handyman", handyman_node)
    workflow.add_node("Chief_Architect", chief_architect_node)
    workflow.add_node("Plan_Expander", plan_expander_node)
    workflow.add_node("human_in_the_loop_node", human_in_the_loop_node)
    
    # Set up flow
    workflow.set_entry_point("Task_Setup")
    workflow.add_edge("Task_Setup", "Memory_Updater")
    workflow.add_conditional_edges("Memory_Updater", history_management_router, {"summarize_history_node": "summarize_history_node", "initial_router_node": "initial_router_node"})
    workflow.add_edge("summarize_history_node", "initial_router_node")

    # Main routing from initial router
    workflow.add_conditional_edges("initial_router_node", route_logic, {
        "Editor": "Editor",
        "Handyman": "Handyman",
        "Chief_Architect": "Chief_Architect",
        "Propose_Experts": "Propose_Experts"
    })

    # BoE Track Flow
    workflow.add_edge("Propose_Experts", "human_in_the_loop_board_approval")
    workflow.add_conditional_edges("human_in_the_loop_board_approval", after_board_approval_router, {
        "chair_initial_plan_node": "chair_initial_plan_node",
        "Editor": "Editor",
    })
    workflow.add_edge("chair_initial_plan_node", "Editor")

    # Other tracks... (simplified for this example)
    workflow.add_edge("Handyman", "Editor")
    workflow.add_edge("Chief_Architect", "human_in_the_loop_node")
    workflow.add_edge("human_in_the_loop_node", "Editor") # Simplified

    workflow.add_edge("Editor", END)
    
    agent = workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=[
            "human_in_the_loop_node",
            "human_in_the_loop_board_approval",
        ]
    )
    logger.info("ResearchAgent graph compiled with BoE approval interrupt.")
    return agent

agent_graph = create_agent_graph()
