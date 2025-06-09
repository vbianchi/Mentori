# -----------------------------------------------------------------------------
# ResearchAgent Core Agent
#
# FINAL FIX: The executor_node is now fully robust. It can handle cases
# where the planner provides a simple string as input for a structured,
# sandboxed tool (e.g., `tool_input: "hello.py"` for `read_file`).
#
# The logic now checks the input type. If it's not a dictionary, it
# intelligently wraps the input into the expected dictionary format (e.g.,
# `{"file_path": "hello.py"}`) before injecting the `workspace_path`.
# This makes the agent resilient to planner variations and completes the
# stabilization of the core tool-using loop.
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
    current_step_index: int
    current_tool_call: Optional[dict]
    tool_output: Optional[str]
    history: Annotated[List[str], lambda x, y: x + y]
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
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files", "workspace_shell"}
def format_tools_for_prompt():
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- Graph Nodes ---
def prepare_inputs_node(state: GraphState):
    logger.info("Executing prepare_inputs_node")
    user_message = state['messages'][-1].content
    task_id = str(uuid.uuid4())
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)
    logger.info(f"Created sandboxed workspace: {workspace_path}")
    return {"input": user_message, "history": [], "current_step_index": 0, "step_outputs": {}, "workspace_path": workspace_path}

def structured_planner_node(state: GraphState):
    logger.info("Executing structured_planner_node")
    llm = get_llm("PLANNER_LLM_ID", "gemini::gemini-1.5-flash-latest")
    prompt = structured_planner_prompt_template.format(input=state["input"], tools=format_tools_for_prompt())
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str)
        if "plan" in parsed_json and isinstance(parsed_json["plan"], list):
            logger.info(f"Generated structured plan: {json.dumps(parsed_json['plan'], indent=2)}")
            return {"plan": parsed_json["plan"]}
        else:
            raise ValueError("The JSON output from the planner is missing the 'plan' key or it is not a list.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing structured plan: {e}\nResponse was:\n{response.content}")
        return {"plan": [{"error": f"Failed to create a valid plan. Reason: {e}"}]}

def controller_node(state: GraphState):
    step_index = state["current_step_index"]
    plan = state["plan"]
    logger.info(f"Executing controller_node for step {step_index + 1}/{len(plan)}")
    current_step_details = plan[step_index]
    tool_call = {
        "tool_name": current_step_details.get("tool_name"),
        "tool_input": current_step_details.get("tool_input", {})
    }
    logger.info(f"Controller prepared tool call: {tool_call}")
    return {"current_tool_call": tool_call}

# === FINAL ROBUST EXECUTOR NODE ===
async def executor_node(state: GraphState):
    """Executes the tool call, handling both dict and string inputs for sandboxed tools."""
    logger.info("Executing executor_node")
    tool_call = state.get("current_tool_call")
    if not tool_call or not tool_call.get("tool_name"):
        return {"tool_output": "Error: No tool call was provided."}

    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", {})
    tool = TOOL_MAP.get(tool_name)

    if not tool:
        return {"tool_output": f"Error: Tool '{tool_name}' not found."}

    invocation_input = tool_input
    
    # --- Robustness Fix ---
    # For sandboxed tools, ensure the input is a dictionary so we can inject the workspace path.
    if tool_name in SANDBOXED_TOOLS:
        if not isinstance(invocation_input, dict):
            # The planner provided a string (e.g., "hello.py") instead of a dict.
            # We must wrap it in the expected dictionary format.
            # We look at the tool's args_schema to find the right key.
            logger.warning(f"Sandboxed tool '{tool_name}' received non-dict input. Wrapping it.")
            input_key = next(iter(tool.args.keys()), None)
            if input_key:
                invocation_input = {input_key: invocation_input}
            else:
                 # This is a safeguard, should not happen with our current tools.
                return {"tool_output": f"Error: Cannot determine input key for sandboxed tool '{tool_name}'."}

        # Now that we're sure it's a dict, inject the workspace path.
        invocation_input["workspace_path"] = state["workspace_path"]

    try:
        # Standard LangChain tool invocation: pass a single argument for the input.
        logger.info(f"Invoking tool '{tool_name}' with input: {invocation_input}")
        output = await tool.ainvoke(invocation_input)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": str(output)}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}


def evaluator_node(state: GraphState):
    logger.info("Executing evaluator_node")
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

def direct_qa_node(state: GraphState):
    # This node is not currently used in the main agent loop, but kept for routing
    return {"answer": "This query was routed to direct QA."}

def increment_step_node(state: GraphState):
    return {"current_step_index": state["current_step_index"] + 1}

# --- Conditional Routers ---
def intent_classifier(state: GraphState):
    return "structured_planner_node"

def should_continue(state: GraphState):
    tool_output = state.get("tool_output", "")
    if "error" in tool_output.lower() or "failed" in tool_output.lower():
        logger.warning(f"Step failed with output: {tool_output}. Ending execution.")
        return END
    if state["current_step_index"] + 1 >= len(state.get("plan", [])):
        logger.info("Plan is complete. Ending execution.")
        return END
    return "increment_step_node"

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("prepare_inputs", prepare_inputs_node)
    workflow.add_node("direct_qa", direct_qa_node)
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
    logger.info("Advanced agent graph compiled successfully.")
    return agent

agent_graph = create_agent_graph()
