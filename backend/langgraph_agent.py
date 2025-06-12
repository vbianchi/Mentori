# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 7: Stateful Workspaces)
#
# This version makes the agent fully stateful by using the task_id passed
# from the server to create persistent workspaces.
#
# 1. GraphState now includes `task_id: str`.
# 2. `task_setup_node` no longer generates a random UUID. It uses the
#    injected `task_id` to ensure that all work for a given task occurs in
#    the same sandboxed directory.
# 3. Logging is enhanced to include the `task_id` for better traceability.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
from typing import TypedDict, Annotated, Sequence, List, Optional, Dict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END

# --- Local Imports ---
from .tools import get_available_tools
from .prompts import structured_planner_prompt_template, controller_prompt_template, evaluator_prompt_template, final_answer_prompt_template

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    """Represents the state of our graph."""
    input: str
    task_id: str # Added task_id to the state
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

# --- Graph Nodes (with "Company Model" Names) ---
def task_setup_node(state: GraphState):
    """The "Onboarding Manager" - Creates the workspace and initializes state."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Task_Setup")
    user_message = state['messages'][-1].content
    
    # --- THE CHANGE: Use the provided task_id to create the workspace path ---
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)
    logger.info(f"Task '{task_id}': Ensured sandboxed workspace exists: {workspace_path}")
    
    initial_llm_config = state.get("llm_config", {})
    return {"input": user_message, "history": [], "current_step_index": 0, "step_outputs": {}, "workspace_path": workspace_path, "llm_config": initial_llm_config}

def chief_architect_node(state: GraphState):
    """The "Chief Architect" - Generates the structured plan."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Chief_Architect")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = structured_planner_prompt_template.format(input=state["input"], tools=format_tools_for_prompt())
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str)
        logger.info(f"Task '{task_id}': Generated structured plan: {json.dumps(parsed_json.get('plan'), indent=2)}")
        return {"plan": parsed_json.get("plan", [])}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error parsing structured plan: {e}\nResponse was:\n{response.content}")
        return {"plan": [{"error": f"Failed to create a valid plan. Reason: {e}"}]}

def site_foreman_node(state: GraphState):
    """The "Site Foreman" - Prepares the tool call for the current step."""
    task_id = state.get("task_id")
    step_index = state["current_step_index"]
    plan = state["plan"]
    logger.info(f"Task '{task_id}': Executing Site_Foreman for step {step_index + 1}/{len(plan)}")
    current_step_details = plan[step_index]
    llm = get_llm(state, "SITE_FOREMAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    history_str = "\n".join(state["history"]) if state.get("history") else "No history yet."
    prompt = controller_prompt_template.format(
        tools=format_tools_for_prompt(),
        plan=json.dumps(state["plan"], indent=2),
        history=history_str,
        current_step=current_step_details.get("instruction", "")
    )
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str)
        logger.info(f"Task '{task_id}': Site Foreman prepared tool call: {tool_call}")
        return {"current_tool_call": tool_call}
    except json.JSONDecodeError as e:
        logger.error(f"Task '{task_id}': Error parsing tool call from Site Foreman: {e}\nResponse was:\n{response.content}")
        return {"current_tool_call": {"error": "Invalid JSON output from Site Foreman."}}

async def worker_node(state: GraphState):
    """The "Worker" - Executes the tool call."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Worker")
    tool_call = state.get("current_tool_call")
    if not tool_call or not tool_call.get("tool_name"): return {"tool_output": "Error: No tool call was provided."}
    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", {})
    tool = TOOL_MAP.get(tool_name)
    if not tool: return {"tool_output": f"Error: Tool '{tool_name}' not found."}

    final_args = {}
    if isinstance(tool_input, dict): final_args.update(tool_input)
    else:
        tool_args_schema = tool.args
        if tool_args_schema: final_args[next(iter(tool_args_schema))] = tool_input

    if tool_name in SANDBOXED_TOOLS:
        final_args["workspace_path"] = state["workspace_path"]

    try:
        logger.info(f"Task '{task_id}': Worker executing tool '{tool_name}' with args: {final_args}")
        output = await tool.ainvoke(final_args)
        logger.info(f"Task '{task_id}': Tool '{tool_name}' executed successfully.")
        return {"tool_output": str(output)}
    except Exception as e:
        logger.error(f"Task '{task_id}': Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}

def project_supervisor_node(state: GraphState):
    """The "Project Supervisor" - Evaluates the step and records history."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Project_Supervisor")
    current_step_details = state["plan"][state["current_step_index"]]
    tool_output = state.get("tool_output", "No output from tool.")
    tool_call = state.get("current_tool_call", {})

    llm = get_llm(state, "PROJECT_SUPERVISOR_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = evaluator_prompt_template.format(
        current_step=current_step_details.get('instruction', ''),
        tool_call=json.dumps(tool_call),
        tool_output=tool_output
    )

    try:
        response = llm.invoke(prompt)
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        evaluation = json.loads(json_str)
        logger.info(f"Task '{task_id}': Step evaluation from Project Supervisor: {evaluation}")
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Task '{task_id}': Error parsing evaluation from Project Supervisor: {e}\nResponse was:\n{response.content}")
        evaluation = {"status": "failure", "reasoning": "Could not parse Project Supervisor output."}

    history_record = (
        f"--- Step {state['current_step_index'] + 1} ---\n"
        f"Instruction: {current_step_details.get('instruction')}\n"
        f"Action: {json.dumps(tool_call)}\n"
        f"Output: {tool_output}\n"
        f"Evaluation: {evaluation.get('status', 'unknown')} - {evaluation.get('reasoning', 'N/A')}"
    )

    step_output_update = {}
    if evaluation.get("status") == "success":
        step_id = current_step_details.get("step_id")
        if step_id: step_output_update[step_id] = tool_output

    return {"step_evaluation": evaluation, "history": [history_record], "step_outputs": step_output_update}

def advance_to_next_step_node(state: GraphState):
    """The "Clerk" - Increments the step index."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Advancing to next step")
    return {"current_step_index": state["current_step_index"] + 1}

def librarian_node(state: GraphState):
    """The "Librarian" - Directly calls an LLM for a simple question."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Librarian (Direct QA)")
    llm = get_llm(state, "LIBRARIAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

def editor_node(state: GraphState):
    """The "Editor" - Synthesizes the final answer."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing Editor")
    llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    history_str = "\n".join(state["history"])
    prompt = final_answer_prompt_template.format(
        input=state["input"],
        history=history_str
    )
    response = llm.invoke(prompt)
    logger.info(f"Task '{task_id}': Editor generated final answer: {response.content[:200]}...")
    return {"answer": response.content}


# --- Conditional Routers ---
def router(state: GraphState):
    """The Router - Routes the workflow based on user intent."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Executing The Router")
    llm = get_llm(state, "ROUTER_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = f"You are a router. Classify the user's last message. Respond with 'AGENT_ACTION' for a complex task that requires planning, or 'DIRECT_QA' for a simple question that can be answered directly.\n\nUser message: '{state['input']}'"
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Task '{task_id}': Routing decision: {decision}")
    return "Chief_Architect" if "AGENT_ACTION" in decision else "Librarian"

def after_plan_step_router(state: GraphState):
    """Routes the workflow after a plan step is evaluated."""
    task_id = state.get("task_id")
    logger.info(f"Task '{task_id}': Router checking if plan should continue or finalize.")
    evaluation = state.get("step_evaluation", {})

    if evaluation.get("status") == "failure":
        logger.warning(f"Task '{task_id}': Step failed. Reason: {evaluation.get('reasoning', 'N/A')}. Routing to Editor.")
        return "Editor"

    if state["current_step_index"] + 1 >= len(state.get("plan", [])):
        logger.info(f"Task '{task_id}': Plan is complete. Routing to Editor.")
        return "Editor"

    return "Advance_To_Next_Step"

# --- Graph Definition ---
def create_agent_graph():
    """Builds the ResearchAgent's LangGraph."""
    workflow = StateGraph(GraphState)
    
    workflow.add_node("Task_Setup", task_setup_node)
    workflow.add_node("Librarian", librarian_node)
    workflow.add_node("Chief_Architect", chief_architect_node)
    workflow.add_node("Site_Foreman", site_foreman_node)
    workflow.add_node("Worker", worker_node)
    workflow.add_node("Project_Supervisor", project_supervisor_node)
    workflow.add_node("Advance_To_Next_Step", advance_to_next_step_node)
    workflow.add_node("Editor", editor_node)

    workflow.set_entry_point("Task_Setup")

    workflow.add_conditional_edges("Task_Setup", router, {
        "Librarian": "Librarian",
        "Chief_Architect": "Chief_Architect"
    })

    workflow.add_edge("Chief_Architect", "Site_Foreman")
    workflow.add_edge("Site_Foreman", "Worker")
    workflow.add_edge("Worker", "Project_Supervisor")
    workflow.add_edge("Advance_To_Next_Step", "Site_Foreman")

    workflow.add_conditional_edges("Project_Supervisor", after_plan_step_router, {
        "Editor": "Editor",
        "Advance_To_Next_Step": "Advance_To_Next_Step"
    })

    workflow.add_edge("Librarian", END)
    workflow.add_edge("Editor", END)

    agent = workflow.compile()
    logger.info("ResearchAgent graph compiled successfully with 'Company Model' names.")
    return agent

agent_graph = create_agent_graph()
