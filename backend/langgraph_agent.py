# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Executor Fix)
#
# CORRECTION: The `executor_node` has been completely rewritten to be more
# robust. For sandboxed tools, it now bypasses `tool.ainvoke()` and calls the
# underlying tool function (`.func` or `.coroutine`) directly. This allows it
# to reliably pass the `workspace_path` as a keyword argument without it being
# filtered by the tool's public `args_schema`, definitively fixing the
# persistent `TypeError`.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
import uuid
import asyncio
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
    models: dict

# --- LLM Provider Helper ---
LLM_CACHE = {}
def get_llm(state: GraphState, role: str):
    """Dynamically gets an LLM based on the role and the user's selection in the state."""
    
    default_models = {
        'router': "gemini::gemini-1.5-flash-latest",
        'planner': "gemini::gemini-1.5-flash-latest",
        'controller': "gemini::gemini-1.5-flash-latest",
        'evaluator': "gemini::gemini-1.5-flash-latest",
    }
    
    model_id = state.get("models", {}).get(role, default_models[role])

    if model_id in LLM_CACHE:
        return LLM_CACHE[model_id]

    logger.info(f"Initializing LLM for role '{role}': Model ID={model_id}")
    
    try:
        provider, model_name = model_id.split("::")
        if provider == "gemini":
            llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
        elif provider == "ollama":
            llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        LLM_CACHE[model_id] = llm
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM '{model_id}'. Falling back to default. Error: {e}")
        default_id = default_models['planner']
        if default_id in LLM_CACHE: return LLM_CACHE[default_id]
        provider, model_name = default_id.split("::")
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
        LLM_CACHE[default_id] = llm
        return llm

# --- Tool Management ---
AVAILABLE_TOOLS = get_available_tools()
TOOL_MAP = {tool.name: tool for tool in AVAILABLE_TOOLS}
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files", "workspace_shell"}
def format_tools_for_prompt():
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- Graph Nodes ---
def prepare_inputs_node(state: GraphState):
    """Prepares the initial state, including workspace and model configs."""
    logger.info("Executing prepare_inputs_node")
    
    try:
        payload_str = state['messages'][0].content
        message_payload = json.loads(payload_str)
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(f"Failed to parse initial payload from message content: '{state['messages'][0].content if state['messages'] else 'No messages'}'. Error: {e}")
        return {
            "messages": [HumanMessage(content="Error: Malformed initial payload.")],
            "input": "Error: Malformed initial payload.",
            "plan": [{"error": f"Failed to start. Reason: {e}"}]
        }

    user_prompt = message_payload.get("prompt")
    models_config = message_payload.get("models", {})

    task_id = str(uuid.uuid4())
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)
    logger.info(f"Created sandboxed workspace: {workspace_path}")
    
    return {
        "messages": [HumanMessage(content=user_prompt)],
        "input": user_prompt, 
        "models": models_config,
        "history": [], 
        "current_step_index": 0, 
        "step_outputs": {}, 
        "workspace_path": workspace_path
    }

def structured_planner_node(state: GraphState):
    logger.info("Executing structured_planner_node")
    llm = get_llm(state, 'planner')
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

async def executor_node(state: GraphState):
    """
    Executes the tool call prepared by the controller.
    This node is the robust, definitive fix for the tool invocation errors.
    """
    logger.info("Executing executor_node")
    tool_call = state.get("current_tool_call")
    if not tool_call or not tool_call.get("tool_name"):
        return {"tool_output": "Error: No tool call was provided."}

    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", {})
    tool = TOOL_MAP.get(tool_name)

    if not tool:
        return {"tool_output": f"Error: Tool '{tool_name}' not found."}

    try:
        # This is the new, robust invocation logic
        if tool_name in SANDBOXED_TOOLS:
            # For sandboxed tools, we manually inject the workspace_path and call the
            # underlying function directly, bypassing the flawed `ainvoke` logic.
            kwargs = tool_input.copy()
            kwargs['workspace_path'] = state["workspace_path"]
            logger.info(f"Manually invoking sandboxed tool '{tool_name}' with kwargs: {kwargs}")

            if tool.coroutine:
                output = await tool.coroutine(**kwargs)
            else:
                loop = asyncio.get_running_loop()
                output = await loop.run_in_executor(None, lambda: tool.func(**kwargs))
        else:
            # For non-sandboxed tools (like web search), the standard ainvoke is fine.
            logger.info(f"Invoking standard tool '{tool_name}' with input: {tool_input}")
            output = await tool.ainvoke(tool_input)
        
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": str(output)}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        # Format the error message to be more informative for the evaluator.
        return {"tool_output": f"An error occurred while executing the tool '{tool_name}': {e}"}

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

def increment_step_node(state: GraphState):
    return {"current_step_index": state["current_step_index"] + 1}

def should_continue(state: GraphState):
    tool_output = state.get("tool_output", "")
    plan = state.get("plan", [])
    if any(step.get("error") for step in plan):
        logger.warning(f"An error was found in the plan. Ending execution.")
        return END
    if "error" in tool_output.lower() or "failed" in tool_output.lower():
        logger.warning(f"Step failed with output: {tool_output}. Ending execution.")
        return END
    if state["current_step_index"] + 1 >= len(plan):
        logger.info("Plan is complete. Ending execution.")
        return END
    return "increment_step_node"

# --- Graph Definition ---
def create_agent_graph():
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
    logger.info("Advanced agent graph compiled successfully.")
    return agent

agent_graph = create_agent_graph()
