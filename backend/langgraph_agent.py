# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 5: Sandboxed Workspace)
#
# This version implements the secure, sandboxed workspace architecture.
#
# Key Changes:
# - GraphState now includes `workspace_path` to track the unique, isolated
#   directory for the current task.
# - `prepare_inputs_node` now creates this unique directory upon starting.
# - The `executor_node` is now "sandbox-aware". It automatically injects the
#   `workspace_path` into calls for the new file system tools, ensuring
#   all file operations are securely contained.
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
# We still use the structured planner prompt as it's the most advanced
from .prompts import structured_planner_prompt_template

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    """Represents the state of our graph with sandboxing."""
    input: str
    plan: List[dict]
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    current_step_index: int
    current_tool_call: Optional[dict]
    tool_output: Optional[str]
    history: Annotated[List[str], lambda x, y: x + y]
    # === New: The path to the secure, isolated workspace for this task ===
    workspace_path: str
    step_outputs: Annotated[Dict[int, str], lambda x, y: {**x, **y}]
    answer: str

# --- LLM Provider Helper ---
LLM_CACHE = {}
def get_llm(llm_id_env_var: str, default_llm_id: str):
    llm_id = os.getenv(llm_id_env_var, default_llm_id)
    if llm_id in LLM_CACHE: return LLM_CACHE[llm_id]
    provider, model_name = llm_id.split("::")
    logger.info(f"Initializing LLM for '{llm_id_env_var}': Provider={provider}, Model={model_name}")
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
# Identify which tools need the sandboxed workspace path
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files"}
def format_tools_for_prompt():
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- Graph Nodes ---
def prepare_inputs_node(state: GraphState):
    """Initializes the state and creates the secure workspace for a new run."""
    logger.info("Executing prepare_inputs_node")
    user_message = state['messages'][-1].content
    
    # === Create the sandboxed workspace for this task ===
    task_id = str(uuid.uuid4())
    # Note: In a real multi-user system, this might be /app/workspaces/<user_id>/<task_id>
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)
    logger.info(f"Created sandboxed workspace: {workspace_path}")
    
    return {
        "input": user_message,
        "history": [],
        "current_step_index": 0,
        "step_outputs": {},
        "workspace_path": workspace_path
    }

def structured_planner_node(state: GraphState):
    logger.info("Executing structured_planner_node")
    llm = get_llm("PLANNER_LLM_ID", "gemini::gemini-2.5-flash-preview-05-20")
    prompt = structured_planner_prompt_template.format(input=state["input"], tools=format_tools_for_prompt())
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str)
        if "plan" in parsed_json and isinstance(parsed_json["plan"], list):
            logger.info(f"Generated structured plan: {parsed_json['plan']}")
            return {"plan": parsed_json["plan"]}
        else:
            raise ValueError("The JSON output from the planner is missing the 'plan' key or it is not a list.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing structured plan: {e}\nResponse was:\n{response.content}")
        return {"plan": [{"error": f"Failed to create a valid plan. Reason: {e}"}]}

def controller_node(state: GraphState):
    """Prepares the tool call for the current step."""
    step_index = state["current_step_index"]
    plan = state["plan"]
    logger.info(f"Executing controller_node for step {step_index + 1}/{len(plan)}")
    current_step_details = plan[step_index]
    tool_call = {
        "tool_name": current_step_details.get("tool_name"),
        "tool_input": current_step_details.get("tool_input")
    }
    logger.info(f"Controller prepared tool call: {tool_call}")
    return {"current_tool_call": tool_call}

# === Sandbox-Aware Executor Node ===
async def executor_node(state: GraphState):
    """Executes the tool call within the secure workspace."""
    logger.info("Executing executor_node")
    tool_call = state.get("current_tool_call")
    if not tool_call or not tool_call.get("tool_name"):
        return {"tool_output": "Error: No tool call was provided."}

    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", {})
    tool = TOOL_MAP.get(tool_name)
    
    if not tool:
        return {"tool_output": f"Error: Tool '{tool_name}' not found."}

    # === Security: Inject workspace_path for sandboxed tools ===
    if tool_name in SANDBOXED_TOOLS:
        if isinstance(tool_input, dict):
            tool_input["workspace_path"] = state["workspace_path"]
        else:
            return {"tool_output": f"Error: Tool '{tool_name}' requires a dictionary input."}

    try:
        logger.info(f"Executing tool '{tool_name}' with input: {str(tool_input)[:200]}...")
        # Await the coroutine from the tool
        output = await tool.ainvoke(tool_input)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": str(output)}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}

def evaluator_node(state: GraphState):
    """Evaluates the step outcome and records it."""
    logger.info("Executing evaluator_node")
    tool_output = state.get("tool_output", "")
    is_error = "error" in tool_output.lower() or "failed" in tool_output.lower()
    status = "failure" if is_error else "success"
    current_step_details = state["plan"][state["current_step_index"]]
    history_record = f"--- Step {state['current_step_index'] + 1} ---\nInstruction: {current_step_details.get('instruction')}\nAction: {json.dumps(state.get('current_tool_call'))}\nOutput: {tool_output}\nEvaluation: {status}"
    
    step_output_update = {}
    if status == "success":
        step_id = current_step_details.get("step_id")
        if step_id:
            step_output_update[step_id] = tool_output
    
    return {"history": [history_record], "step_outputs": step_output_update}

def direct_qa_node(state: GraphState):
    logger.info("Executing direct_qa_node")
    llm = get_llm("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

def increment_step_node(state: GraphState):
    return {"current_step_index": state["current_step_index"] + 1}

# --- Conditional Routers ---
def intent_classifier(state: GraphState):
    # Simplified for brevity
    return "structured_planner_node"

def should_continue(state: GraphState):
    if "error" in state.get("tool_output", "").lower():
        return END
    if state["current_step_index"] + 1 >= len(state["plan"]):
        return END
    return "increment_step_node"

# --- Graph Definition ---
def create_agent_graph():
    """Builds the advanced PCEE LangGraph."""
    workflow = StateGraph(GraphState)
    workflow.add_node("prepare_inputs", prepare_inputs_node)
    workflow.add_node("structured_planner_node", structured_planner_node)
    workflow.add_node("controller_node", controller_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("evaluator_node", evaluator_node)
    workflow.add_node("increment_step_node", increment_step_node)
    
    workflow.set_entry_point("prepare_inputs")
    workflow.add_edge("prepare_inputs", "structured_planner_node")
    workflow.add_edge("structured_planner_node", "controller_node")
    workflow.add_edge("controller_node", "executor_node")
    workflow.add_edge("executor_node", "evaluator_node")
    workflow.add_edge("increment_step_node", "controller_node")
    workflow.add_conditional_edges("evaluator_node", should_continue, {END: END, "increment_step_node": "increment_step_node"})
    
    agent = workflow.compile()
    logger.info("Advanced agent graph (Sandboxed) compiled successfully.")
    return agent

agent_graph = create_agent_graph()
