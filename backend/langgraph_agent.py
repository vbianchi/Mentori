# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 7: Naming Refactor)
#
# This version standardizes the naming of all agent nodes and their
# configurations to align with the "Company Model" (e.g., Chief_Architect).
#
# 1. Node functions and graph definitions now consistently use the new names.
#    - `final_answer_agent_node` is renamed to `editor_node`.
# 2. All `get_llm` calls now use the new environment variable keys
#    (e.g., `CHIEF_ARCHITECT_LLM_ID`).
# 3. All agent roles are now configurable with their own LLM.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
import uuid
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
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    """Represents the state of our graph."""
    input: str
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
    logger.info(f"Initializing LLM for '{role_env_var}': {llm_id}")
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
    logger.info("Executing Task_Setup")
    user_message = state['messages'][-1].content
    task_id = str(uuid.uuid4())
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)
    logger.info(f"Created sandboxed workspace: {workspace_path}")
    initial_llm_config = state.get("llm_config", {})
    return {"input": user_message, "history": [], "current_step_index": 0, "step_outputs": {}, "workspace_path": workspace_path, "llm_config": initial_llm_config}

def chief_architect_node(state: GraphState):
    """The "Chief Architect" - Generates the structured plan."""
    logger.info("Executing Chief_Architect")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = structured_planner_prompt_template.format(input=state["input"], tools=format_tools_for_prompt())
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str)
        logger.info(f"Generated structured plan: {json.dumps(parsed_json.get('plan'), indent=2)}")
        return {"plan": parsed_json.get("plan", [])}
    except Exception as e:
        logger.error(f"Error parsing structured plan: {e}\nResponse was:\n{response.content}")
        return {"plan": [{"error": f"Failed to create a valid plan. Reason: {e}"}]}

def site_foreman_node(state: GraphState):
    """The "Site Foreman" - Prepares the tool call for the current step."""
    step_index = state["current_step_index"]
    plan = state["plan"]
    logger.info(f"Executing Site_Foreman for step {step_index + 1}/{len(plan)}")
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
        logger.info(f"Site Foreman prepared tool call: {tool_call}")
        return {"current_tool_call": tool_call}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing tool call from Site Foreman: {e}\nResponse was:\n{response.content}")
        return {"current_tool_call": {"error": "Invalid JSON output from Site Foreman."}}

async def worker_node(state: GraphState):
    """The "Worker" - Executes the tool call."""
    logger.info("Executing Worker")
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
        logger.info(f"Worker executing tool '{tool_name}' with args: {final_args}")
        output = await tool.ainvoke(final_args)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": str(output)}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}

def project_supervisor_node(state: GraphState):
    """The "Project Supervisor" - Evaluates the step and records history."""
    logger.info("Executing Project_Supervisor")
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
        logger.info(f"Step evaluation from Project Supervisor: {evaluation}")
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error parsing evaluation from Project Supervisor: {e}\nResponse was:\n{response.content}")
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
    logger.info("Advancing to next step")
    return {"current_step_index": state["current_step_index"] + 1}

def librarian_node(state: GraphState):
    """The "Librarian" - Directly calls an LLM for a simple question."""
    logger.info("Executing Librarian (Direct QA)")
    llm = get_llm(state, "LIBRARIAN_LLM_ID", "gemini::gemini-1.5-flash-latest")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

def editor_node(state: GraphState):
    """The "Editor" - Synthesizes the final answer."""
    logger.info("Executing Editor")
    llm = get_llm(state, "EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
    history_str = "\n".join(state["history"])
    prompt = final_answer_prompt_template.format(
        input=state["input"],
        history=history_str
    )
    response = llm.invoke(prompt)
    logger.info(f"Editor generated final answer: {response.content[:200]}...")
    return {"answer": response.content}


# --- Conditional Routers ---
def router(state: GraphState):
    """The Router - Routes the workflow based on user intent."""
    logger.info("Executing The Router")
    llm = get_llm(state, "ROUTER_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = f"You are a router. Classify the user's last message. Respond with 'AGENT_ACTION' for a complex task that requires planning, or 'DIRECT_QA' for a simple question that can be answered directly.\n\nUser message: '{state['input']}'"
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Routing decision: {decision}")
    return "Chief_Architect" if "AGENT_ACTION" in decision else "Librarian"

def after_plan_step_router(state: GraphState):
    """Routes the workflow after a plan step is evaluated."""
    logger.info("Router: Checking if plan should continue or finalize.")
    evaluation = state.get("step_evaluation", {})

    if evaluation.get("status") == "failure":
        logger.warning(f"Step failed. Reason: {evaluation.get('reasoning', 'N/A')}. Routing to Editor.")
        return "Editor"

    if state["current_step_index"] + 1 >= len(state.get("plan", [])):
        logger.info("Plan is complete. Routing to Editor.")
        return "Editor"

    return "Advance_To_Next_Step"

# --- Graph Definition ---
def create_agent_graph():
    """Builds the ResearchAgent's LangGraph."""
    workflow = StateGraph(GraphState)
    
    # Add nodes with their "Company Model" names
    workflow.add_node("Task_Setup", task_setup_node)
    workflow.add_node("Librarian", librarian_node)
    workflow.add_node("Chief_Architect", chief_architect_node)
    workflow.add_node("Site_Foreman", site_foreman_node)
    workflow.add_node("Worker", worker_node)
    workflow.add_node("Project_Supervisor", project_supervisor_node)
    workflow.add_node("Advance_To_Next_Step", advance_to_next_step_node)
    workflow.add_node("Editor", editor_node)

    # Set entry point and define edges
    workflow.set_entry_point("Task_Setup")

    # This is the initial classification of the user's request
    workflow.add_conditional_edges("Task_Setup", router, {
        "Librarian": "Librarian",
        "Chief_Architect": "Chief_Architect"
    })

    # This is the main execution loop
    workflow.add_edge("Chief_Architect", "Site_Foreman")
    workflow.add_edge("Site_Foreman", "Worker")
    workflow.add_edge("Worker", "Project_Supervisor")
    workflow.add_edge("Advance_To_Next_Step", "Site_Foreman") # The loop back

    # This router decides whether to continue the loop or finish
    workflow.add_conditional_edges("Project_Supervisor", after_plan_step_router, {
        "Editor": "Editor",
        "Advance_To_Next_Step": "Advance_To_Next_Step"
    })

    # These are the terminal edges
    workflow.add_edge("Librarian", END)
    workflow.add_edge("Editor", END)

    agent = workflow.compile()
    logger.info("ResearchAgent graph compiled successfully with 'Company Model' names.")
    return agent

agent_graph = create_agent_graph()
