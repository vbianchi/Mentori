# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 4: Complete PCEE with Smarter Evaluator)
#
# This file implements the full PCEE loop with memory and a more
# context-aware Evaluator.
#
# Key Changes:
# - The `evaluator_node` now receives the `tool_call` as context.
# - It uses the `EVALUATOR_LLM_ID` to leverage a more powerful model for
#   the complex task of assessing step success based on intent.
# -----------------------------------------------------------------------------

import os
import logging
import ast
import re
import json
from typing import TypedDict, Annotated, Sequence, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END

# --- Local Imports ---
from .tools import get_available_tools
from .prompts import planner_prompt_template, controller_prompt_template, evaluator_prompt_template

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    """Represents the state of our graph."""
    input: str
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    plan: List[str]
    current_step_index: int
    tool_call: Optional[dict]
    tool_output: Optional[str]
    history: Annotated[List[str], lambda x, y: x + y]
    step_evaluation: Optional[dict]
    answer: str

# --- LLM Provider Helper ---
LLM_CACHE = {}
def get_llm(llm_id_env_var: str, default_llm_id: str):
    llm_id = os.getenv(llm_id_env_var, default_llm_id)
    if llm_id in LLM_CACHE:
        return LLM_CACHE[llm_id]
    provider, model_name = llm_id.split("::")
    logger.info(f"Initializing LLM for '{llm_id_env_var}': Provider={provider}, Model={model_name}")
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key: raise ValueError("GOOGLE_API_KEY not set.")
        temp = float(os.getenv("GEMINI_TEMPERATURE", 0.7))
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=temp)
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        temp = float(os.getenv("OLLAMA_TEMPERATURE", 0.5))
        llm = ChatOllama(model=model_name, base_url=base_url, temperature=temp)
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
    return {"input": user_message, "current_step_index": 0, "history": []}

def planner_node(state: GraphState):
    logger.info("Executing planner_node")
    llm = get_llm("PLANNER_LLM_ID", "gemini::gemini-2.5-flash-preview-05-20")
    prompt = planner_prompt_template
    planner_chain = prompt | llm
    response = planner_chain.invoke({"input": state["input"]})
    try:
        match = re.search(r"```python\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        plan_str = match.group(1).strip() if match else response.content.strip()
        plan = ast.literal_eval(plan_str)
        logger.info(f"Generated plan: {plan}")
        return {"plan": plan}
    except (ValueError, SyntaxError) as e:
        logger.error(f"Error parsing plan from LLM response: {e}\nResponse was:\n{response.content}")
        return {"plan": [f"Error creating plan: {e}"]}

def controller_node(state: GraphState):
    logger.info(f"Executing controller_node for step {state['current_step_index']}")
    current_step = state["plan"][state["current_step_index"]]
    history_str = "\n".join(state["history"]) if state.get("history") else "No history yet."
    llm = get_llm("CONTROLLER_LLM_ID", "gemini::gemini-2.0-flash")
    prompt = controller_prompt_template.format(tools=format_tools_for_prompt(), plan=state["plan"], history=history_str, current_step=current_step)
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str)
        logger.info(f"Controller selected tool: {tool_call}")
        return {"tool_call": tool_call}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing tool call from LLM response: {e}\nResponse was:\n{response.content}")
        return {"tool_call": {"error": "Invalid JSON output from controller."}}

async def executor_node(state: GraphState):
    logger.info("Executing executor_node")
    tool_call = state.get("tool_call")
    if not tool_call or "tool_name" not in tool_call: return {"tool_output": "Error: No tool call found."}
    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", "")
    tool = TOOL_MAP.get(tool_name)
    if not tool: return {"tool_output": f"Error: Tool '{tool_name}' not found."}
    try:
        logger.info(f"Executing tool '{tool_name}' with input: '{tool_input}'")
        output = await tool.ainvoke(tool_input)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": output}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}

def evaluator_node(state: GraphState):
    """Assesses the outcome and records it to history."""
    logger.info("Executing evaluator_node")
    current_step = state["plan"][state["current_step_index"]]
    tool_output = state.get("tool_output", "No output from tool.")
    tool_call = state.get("tool_call", {})

    # === Use the smarter, more powerful LLM for evaluation ===
    llm = get_llm("EVALUATOR_LLM_ID", "gemini::gemini-2.5-flash-preview-05-20")
    
    # === Pass the Controller's action to the prompt for more context ===
    prompt = evaluator_prompt_template.format(
        current_step=current_step,
        tool_call=json.dumps(tool_call),
        tool_output=tool_output
    )
    
    response = llm.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        evaluation = json.loads(json_str)
        logger.info(f"Step evaluation: {evaluation}")
        
        history_record = (
            f"--- Step {state['current_step_index'] + 1} ---\n"
            f"Instruction: {current_step}\n"
            f"Action: {json.dumps(tool_call)}\n"
            f"Tool Output:\n{tool_output}\n"
            f"Evaluation: {evaluation.get('status', 'unknown')} - {evaluation.get('reasoning', 'N/A')}"
        )
        
        return {"step_evaluation": evaluation, "history": [history_record]}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing evaluation from LLM response: {e}\nResponse was:\n{response.content}")
        return {"step_evaluation": {"status": "failure", "reasoning": "Could not parse evaluator output."}}

def increment_step_node(state: GraphState):
    logger.info("Incrementing step index")
    return {"current_step_index": state["current_step_index"] + 1}

def direct_qa_node(state: GraphState):
    logger.info("Executing direct_qa_node")
    llm = get_llm("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

# --- Conditional Routing ---
def intent_classifier(state: GraphState):
    logger.info("Classifying intent")
    llm = get_llm("INTENT_CLASSIFIER_LLM_ID", "gemini::gemini-1.5-flash")
    prompt = f"Classify the user's last message. Respond with 'AGENT_ACTION' for a task, or 'DIRECT_QA' for a simple question.\n\nUser message: '{state['input']}'"
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Intent classified as: {decision}")
    return "planner_node" if "AGENT_ACTION" in decision else "direct_qa_node"

def should_continue(state: GraphState):
    """Determines whether to continue the loop or end."""
    logger.info("Executing should_continue router")
    evaluation = state.get("step_evaluation", {})
    if evaluation.get("status") == "failure":
        logger.warning(f"Step failed. Reason: {evaluation.get('reasoning', 'N/A')}. Ending execution.")
        return END
    
    if state["current_step_index"] + 1 < len(state["plan"]):
        logger.info("Plan not yet complete. Looping back to controller.")
        return "increment_step_node"
    else:
        logger.info("Plan is complete. Ending execution.")
        return END

# --- Graph Definition ---
def create_agent_graph():
    """Builds the LangGraph."""
    workflow = StateGraph(GraphState)
    # Add nodes
    workflow.add_node("prepare_inputs", prepare_inputs_node)
    workflow.add_node("direct_qa", direct_qa_node)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("controller_node", controller_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("evaluator_node", evaluator_node)
    workflow.add_node("increment_step_node", increment_step_node)
    
    # Set entry point and define edges
    workflow.set_entry_point("prepare_inputs")
    workflow.add_conditional_edges("prepare_inputs", intent_classifier, {"direct_qa_node": "direct_qa", "planner_node": "planner_node"})
    workflow.add_edge("planner_node", "controller_node")
    workflow.add_edge("controller_node", "executor_node")
    workflow.add_edge("executor_node", "evaluator_node")
    workflow.add_edge("increment_step_node", "controller_node")
    workflow.add_conditional_edges("evaluator_node", should_continue, {END: END, "increment_step_node": "increment_step_node"})
    workflow.add_edge("direct_qa", END)

    agent = workflow.compile()
    logger.info("PCEE agent graph (Smarter Evaluator) compiled successfully.")
    return agent

agent_graph = create_agent_graph()
