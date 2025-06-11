# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Dynamic LLM Configuration)
#
# This version refactors the agent to accept per-run LLM configurations.
#
# Key Changes:
# - GraphState now includes `llm_config` to hold model overrides for a run.
# - The `get_llm` function is now much smarter. It first checks the state's
#   `llm_config` for an override. If none is found, it falls back to the
#   .env file's default. This makes the agent's model selection dynamic.
# - All nodes that call `get_llm` now pass the `state` to it.
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
from .prompts import structured_planner_prompt_template

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    input: str
    plan: List[dict]
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    # === New: A dictionary to hold the LLM configuration for this specific run ===
    llm_config: Dict[str, str]
    current_step_index: int
    current_tool_call: Optional[dict]
    tool_output: Optional[str]
    history: Annotated[List[str], lambda x, y: x + y]
    workspace_path: str
    step_outputs: Annotated[Dict[int, str], lambda x, y: {**x, **y}]
    answer: str

# --- LLM Provider Helper (Upgraded) ---
LLM_CACHE = {}

def get_llm(state: GraphState, role_env_var: str, default_llm_id: str):
    """
    Smarter factory function to get the appropriate LLM.
    It prioritizes the per-run configuration from the state, then falls
    back to the environment variables.
    """
    llm_id = default_llm_id
    
    # 1. Check for a per-run override from the UI
    run_config = state.get("llm_config", {})
    if run_config and run_config.get(role_env_var):
        llm_id = run_config[role_env_var]
        logger.info(f"Using per-run LLM override for '{role_env_var}': {llm_id}")
    else:
        # 2. Fall back to the .env file
        llm_id = os.getenv(role_env_var, default_llm_id)

    # Use caching to avoid re-initializing models constantly
    if llm_id in LLM_CACHE:
        return LLM_CACHE[llm_id]

    provider, model_name = llm_id.split("::")
    logger.info(f"Initializing LLM for '{role_env_var}': Provider={provider}, Model={model_name}")
    
    if provider == "gemini":
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif provider == "ollama":
        llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
        
    LLM_CACHE[llm_id] = llm
    return llm

# --- Tool Management ---
AVAILABLE_TOOLS = get_available_tools()
TOOL_MAP = {tool.name: tool for tool in AVAILABLE_TOOLS}
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files", "workspace_shell"}
def format_tools_for_prompt():
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- Graph Nodes ---
def task_setup_node(state: GraphState):
    logger.info("Executing Task_Setup")
    user_message = state['messages'][-1].content
    task_id = str(uuid.uuid4())
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)
    logger.info(f"Created sandboxed workspace: {workspace_path}")
    # Ensure llm_config exists, even if empty
    initial_llm_config = state.get("llm_config", {})
    return {"input": user_message, "history": [], "current_step_index": 0, "step_outputs": {}, "workspace_path": workspace_path, "llm_config": initial_llm_config}

def chief_architect_node(state: GraphState):
    logger.info("Executing Chief_Architect")
    llm = get_llm(state, "PLANNER_LLM_ID", "gemini::gemini-2.5-flash-preview-05-20")
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
    # This node doesn't call an LLM, so no changes needed
    # ... (rest of the function is the same)
    step_index = state["current_step_index"]
    plan = state["plan"]
    logger.info(f"Executing Site_Foreman for step {step_index + 1}/{len(plan)}")
    current_step_details = plan[step_index]
    raw_tool_input = current_step_details.get("tool_input", {})
    hydrated_tool_input = raw_tool_input
    if isinstance(raw_tool_input, str):
        placeholders = re.findall(r"\{step_(\d+)_output\}", raw_tool_input)
        for step_num_str in placeholders:
            step_num = int(step_num_str)
            if step_num in state["step_outputs"]:
                hydrated_tool_input = hydrated_tool_input.replace(f"{{step_{step_num}_output}}", state["step_outputs"][step_num])
    tool_call = {"tool_name": current_step_details.get("tool_name"), "tool_input": hydrated_tool_input}
    logger.info(f"Controller prepared tool call: {tool_call}")
    return {"current_tool_call": tool_call}

async def worker_node(state: GraphState):
    # This node doesn't call an LLM, so no changes needed
    # ... (rest of the function is the same)
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
    if tool_name in SANDBOXED_TOOLS: final_args["workspace_path"] = state["workspace_path"]
    try:
        logger.info(f"Worker executing tool '{tool_name}' with args: {final_args}")
        output = await tool.ainvoke(final_args)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": str(output)}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}

def project_supervisor_node(state: GraphState):
    # This node doesn't call an LLM, so no changes needed for now
    # We could make this one dynamic in the future too
    logger.info("Executing Project_Supervisor")
    tool_output = state.get("tool_output", "")
    is_error = "error" in tool_output.lower() or "failed" in tool_output.lower()
    status = "failure" if is_error else "success"
    current_step_details = state["plan"][state["current_step_index"]]
    history_record = f"--- Step {state['current_step_index'] + 1} ---\nInstruction: {current_step_details.get('instruction')}\nAction: {json.dumps(state.get('current_tool_call'))}\nOutput: {tool_output}\nEvaluation: {status}"
    step_output_update = {}
    if status == "success":
        step_id = current_step_details.get("step_id")
        if step_id: step_output_update[step_id] = tool_output
    return {"history": [history_record], "step_outputs": step_output_update}

def advance_to_next_step_node(state: GraphState):
    logger.info("Advancing to next step")
    return {"current_step_index": state["current_step_index"] + 1}

def librarian_node(state: GraphState):
    logger.info("Executing Librarian (Direct QA)")
    llm = get_llm(state, "DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

# --- Conditional Routers ---
def intent_classifier(state: GraphState):
    logger.info("Classifying intent")
    llm = get_llm(state, "INTENT_CLASSIFIER_LLM_ID", "gemini::gemini-1.5-flash")
    prompt = f"Classify the user's last message. Respond with 'AGENT_ACTION' for a task, or 'DIRECT_QA' for a simple question.\n\nUser message: '{state['input']}'"
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Intent classified as: {decision}")
    return "Chief_Architect" if "AGENT_ACTION" in decision else "Librarian"

def should_continue(state: GraphState):
    # ... (rest of the function is the same)
    logger.info("Router: Checking if we should continue")
    tool_output = state.get("tool_output", "")
    if "error" in tool_output.lower() or "failed" in tool_output.lower():
        logger.warning(f"Step failed. Ending execution.")
        return END
    if state["current_step_index"] + 1 >= len(state.get("plan", [])):
        logger.info("Plan is complete. Ending execution.")
        return END
    return "Advance_To_Next_Step"

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("Task_Setup", task_setup_node)
    workflow.add_node("Librarian", librarian_node)
    workflow.add_node("Chief_Architect", chief_architect_node)
    workflow.add_node("Site_Foreman", site_foreman_node)
    workflow.add_node("Worker", worker_node)
    workflow.add_node("Project_Supervisor", project_supervisor_node)
    workflow.add_node("Advance_To_Next_Step", advance_to_next_step_node)
    
    workflow.set_entry_point("Task_Setup")
    
    workflow.add_conditional_edges("Task_Setup", intent_classifier, {"Librarian": "Librarian", "Chief_Architect": "Chief_Architect"})
    
    workflow.add_edge("Chief_Architect", "Site_Foreman")
    workflow.add_edge("Site_Foreman", "Worker")
    workflow.add_edge("Worker", "Project_Supervisor")
    workflow.add_edge("Advance_To_Next_Step", "Site_Foreman")
    
    workflow.add_conditional_edges("Project_Supervisor", should_continue, {END: END, "Advance_To_Next_Step": "Advance_To_Next_Step"})
    
    workflow.add_edge("Librarian", END)

    agent = workflow.compile()
    logger.info("Advanced agent graph (Dynamic LLM) compiled successfully.")
    return agent

agent_graph = create_agent_graph()
