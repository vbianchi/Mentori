# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Advanced Architecture - Smart Controller)
#
# This version implements the final piece of the core PCEE architecture:
# a "Smart Controller" that can pass data between steps.
#
# Key Changes:
# - The Controller node can now recognize placeholders (e.g., "{step_1_output}")
#   in a step's `tool_input` and replace them with the output from previous steps.
# - The GraphState now stores a dictionary of `step_outputs` to facilitate this.
# - The Evaluator now records the raw tool output to this dictionary upon success.
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
from .prompts import structured_planner_prompt_template

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    """Represents the state of our graph under the new architecture."""
    input: str
    plan: List[dict]
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    current_step_index: int
    current_tool_call: Optional[dict]
    # === New: A dictionary to store the output of each step ===
    step_outputs: Annotated[Dict[int, str], lambda x, y: {**x, **y}]
    history: Annotated[List[str], lambda x, y: x + y]
    answer: str

# --- LLM Provider Helper ---
LLM_CACHE = {}
def get_llm(llm_id_env_var: str, default_llm_id: str):
    llm_id = os.getenv(llm_id_env_var, default_llm_id)
    if llm_id in LLM_CACHE: return LLM_CACHE[llm_id]
    provider, model_name = llm_id.split("::")
    logger.info(f"Initializing LLM for '{llm_id_env_var}': Provider={provider}, Model={model_name}")
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key: raise ValueError("GOOGLE_API_KEY not set.")
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = ChatOllama(model=model_name, base_url=base_url)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    LLM_CACHE[llm_id] = llm
    return llm

# --- Tool Management ---
AVAILABLE_TOOLS = get_available_tools()
TOOL_MAP = {tool.name: tool for tool in AVAILABLE_TOOLS}
def format_tools_for_prompt():
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- Graph Nodes ---
def prepare_inputs_node(state: GraphState):
    logger.info("Executing prepare_inputs_node")
    user_message = state['messages'][-1].content
    return {"input": user_message, "history": [], "current_step_index": 0, "step_outputs": {}}

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
        logger.error(f"Error parsing structured plan from LLM response: {e}\nResponse was:\n{response.content}")
        return {"plan": [{"error": f"Failed to create a valid plan. Reason: {e}"}]}

# === The Smart Controller ===
def controller_node(state: GraphState):
    """
    Prepares the tool call for the current step and performs data passing.
    """
    step_index = state["current_step_index"]
    plan = state["plan"]
    logger.info(f"Executing controller_node for step {step_index + 1}/{len(plan)}")
    
    if step_index >= len(plan):
        logger.warning("Controller called but plan is complete. Ending.")
        return {"current_tool_call": None}

    current_step_details = plan[step_index]
    
    # --- Data Passing Logic ---
    raw_tool_input = current_step_details.get("tool_input")
    
    # Find placeholders like "{step_1_output}" in the input
    placeholders = re.findall(r"\{step_(\d+)_output\}", str(raw_tool_input))
    
    # Substitute placeholders with actual output from previous steps
    hydrated_tool_input = raw_tool_input
    for step_num_str in placeholders:
        step_num = int(step_num_str)
        if step_num in state["step_outputs"]:
            previous_output = state["step_outputs"][step_num]
            hydrated_tool_input = str(hydrated_tool_input).replace(f"{{step_{step_num}_output}}", previous_output)
    
    tool_call = {
        "tool_name": current_step_details.get("tool_name"),
        "tool_input": hydrated_tool_input
    }
    
    logger.info(f"Controller prepared tool call: {tool_call}")
    return {"current_tool_call": tool_call}

async def executor_node(state: GraphState):
    logger.info("Executing executor_node")
    tool_call = state.get("current_tool_call")
    if not tool_call or not tool_call.get("tool_name"):
        return {"tool_output": "Error: No tool call was provided."}

    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", "")
    tool = TOOL_MAP.get(tool_name)
    if not tool:
        return {"tool_output": f"Error: Tool '{tool_name}' not found."}

    try:
        logger.info(f"Executing tool '{tool_name}' with input: '{str(tool_input)[:200]}...'")
        output = await tool.ainvoke(tool_input)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": str(output)}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}

def evaluator_node(state: GraphState):
    """
    Evaluates the step outcome and stores the output if successful.
    """
    logger.info("Executing evaluator_node")
    tool_output = state.get("tool_output", "")
    is_error = "error" in tool_output.lower() or "failed" in tool_output.lower()
    status = "failure" if is_error else "success"
    current_step_details = state["plan"][state["current_step_index"]]
    history_record = f"--- Step {state['current_step_index'] + 1} ---\nInstruction: {current_step_details.get('instruction')}\nAction: {json.dumps(state.get('current_tool_call'))}\nOutput: {tool_output}\nEvaluation: {status}"
    
    if status == "success":
        # Store the successful output for future steps
        step_id = current_step_details.get("step_id")
        return {"history": [history_record], "step_outputs": {step_id: tool_output}}
    else:
        # Don't store output if the step failed
        return {"history": [history_record]}

def direct_qa_node(state: GraphState):
    logger.info("Executing direct_qa_node")
    llm = get_llm("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

# --- Conditional Routers ---
def intent_classifier(state: GraphState):
    logger.info("Classifying intent")
    llm = get_llm("INTENT_CLASSIFIER_LLM_ID", "gemini::gemini-1.5-flash")
    prompt = f"Classify the user's last message. Respond with 'AGENT_ACTION' for a task, or 'DIRECT_QA' for a simple question.\n\nUser message: '{state['input']}'"
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Intent classified as: {decision}")
    return "structured_planner_node" if "AGENT_ACTION" in decision else "direct_qa_node"

def should_continue(state: GraphState):
    logger.info("Executing should_continue router")
    if "error" in state.get("tool_output", "").lower():
        logger.warning("Step failed. Ending execution.")
        return END
        
    if state["current_step_index"] + 1 >= len(state["plan"]):
        logger.info("Plan is complete. Ending execution.")
        return END
    else:
        logger.info("Plan not yet complete. Looping to next step.")
        return "increment_step_node"

def increment_step_node(state: GraphState):
    logger.info("Incrementing step index")
    return {"current_step_index": state["current_step_index"] + 1}

# --- Graph Definition ---
def create_agent_graph():
    """Builds the advanced PCEE LangGraph."""
    workflow = StateGraph(GraphState)
    # Add nodes
    workflow.add_node("prepare_inputs", prepare_inputs_node)
    workflow.add_node("direct_qa", direct_qa_node)
    workflow.add_node("structured_planner_node", structured_planner_node)
    workflow.add_node("controller_node", controller_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("evaluator_node", evaluator_node)
    workflow.add_node("increment_step_node", increment_step_node)
    
    # Set entry point
    workflow.set_entry_point("prepare_inputs")
    
    # Define edges
    workflow.add_conditional_edges("prepare_inputs", intent_classifier, {"direct_qa_node": "direct_qa", "structured_planner_node": "structured_planner_node"})
    workflow.add_edge("structured_planner_node", "controller_node")
    workflow.add_edge("controller_node", "executor_node")
    workflow.add_edge("executor_node", "evaluator_node")
    workflow.add_edge("increment_step_node", "controller_node")
    workflow.add_conditional_edges("evaluator_node", should_continue, {END: END, "increment_step_node": "increment_step_node"})
    workflow.add_edge("direct_qa", END)

    agent = workflow.compile()
    logger.info("Advanced agent graph (Smart Controller) compiled successfully.")
    return agent

agent_graph = create_agent_graph()
