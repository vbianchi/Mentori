# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 4: Executor)
#
# This file now implements the Executor node of the PCEE loop.
#
# Key Changes:
# - GraphState is updated with `tool_output` to store the result of a tool call.
# - A new `executor_node` is created. It finds the tool specified by the
#   controller and executes it with the given input.
# - A tool map is created for efficient lookup of tools by name.
# - The graph flow is updated: controller -> executor, which is now the end.
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
from .prompts import planner_prompt_template, controller_prompt_template

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
# === Updated State for PCEE Loop ===
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    """
    input: str
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    plan: List[str]
    current_step_index: int
    tool_call: Optional[dict]
    tool_output: Optional[str] # New key to store tool results
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
# Create a mapping from tool names to the actual tool objects for fast lookup.
AVAILABLE_TOOLS = get_available_tools()
TOOL_MAP = {tool.name: tool for tool in AVAILABLE_TOOLS}

def format_tools_for_prompt():
    """Formats the available tools for inclusion in a prompt."""
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- Graph Nodes ---
def prepare_inputs_node(state: GraphState):
    logger.info("Executing prepare_inputs_node")
    user_message = state['messages'][-1].content
    return {"input": user_message, "current_step_index": 0}

def planner_node(state: GraphState):
    logger.info("Executing planner_node")
    llm = get_llm("PLANNER_LLM_ID", "gemini::gemini-2.0-flash")
    prompt = planner_prompt_template
    planner_chain = prompt | llm
    response = planner_chain.invoke({"input": state["input"]})
    try:
        match = re.search(r"```python\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        plan_str = match.group(1).strip() if match else response.content.strip()
        plan = ast.literal_eval(plan_str)
        if isinstance(plan, list) and all(isinstance(item, str) for item in plan):
             logger.info(f"Generated plan: {plan}")
             return {"plan": plan}
        raise ValueError("LLM did not return a valid list of strings.")
    except (ValueError, SyntaxError) as e:
        logger.error(f"Error parsing plan from LLM response: {e}\nResponse was:\n{response.content}")
        return {"plan": [f"Error creating plan: {e}"]}

def controller_node(state: GraphState):
    logger.info("Executing controller_node")
    current_step = state["plan"][state["current_step_index"]]
    llm = get_llm("CONTROLLER_LLM_ID", "gemini::gemini-2.0-flash")
    prompt = controller_prompt_template.format(
        tools=format_tools_for_prompt(),
        plan=state["plan"],
        current_step=current_step
    )
    controller_chain = llm
    response = controller_chain.invoke(prompt)
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        tool_call = json.loads(json_str)
        logger.info(f"Controller selected tool: {tool_call}")
        return {"tool_call": tool_call}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing tool call from LLM response: {e}\nResponse was:\n{response.content}")
        return {"tool_call": {"error": "Invalid JSON output from controller."}}

# === New Executor Node ===
async def executor_node(state: GraphState):
    """Executes the tool call selected by the controller."""
    logger.info("Executing executor_node")
    tool_call = state.get("tool_call")
    if not tool_call or "tool_name" not in tool_call:
        return {"tool_output": "Error: No tool call found in state."}

    tool_name = tool_call["tool_name"]
    tool_input = tool_call.get("tool_input", "")
    
    # Look up the tool in our map
    tool = TOOL_MAP.get(tool_name)
    if not tool:
        return {"tool_output": f"Error: Tool '{tool_name}' not found."}

    try:
        logger.info(f"Executing tool '{tool_name}' with input: '{tool_input}'")
        # Use `ainvoke` for async tool execution
        output = await tool.ainvoke(tool_input)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_output": output}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"tool_output": f"An error occurred while executing the tool: {e}"}


def direct_qa_node(state: GraphState):
    logger.info("Executing direct_qa_node")
    llm = get_llm("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

# --- Conditional Routing ---
def intent_classifier(state: GraphState):
    logger.info("Classifying intent")
    llm = get_llm("INTENT_CLASSIFIER_LLM_ID", "gemini::gemini-2.0-flash")
    prompt = f"Classify the user's last message. Respond with 'AGENT_ACTION' for a task, or 'DIRECT_QA' for a simple question.\n\nUser message: '{state['input']}'"
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Intent classified as: {decision}")
    if "AGENT_ACTION" in decision:
        return "planner_node"
    else:
        return "direct_qa_node"

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    # Add nodes
    workflow.add_node("prepare_inputs", prepare_inputs_node)
    workflow.add_node("direct_qa", direct_qa_node)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("controller_node", controller_node)
    workflow.add_node("executor_node", executor_node) # Add new node
    
    # Set entry point
    workflow.set_entry_point("prepare_inputs")
    
    # Add edges
    workflow.add_conditional_edges(
        "prepare_inputs",
        intent_classifier,
        {"direct_qa_node": "direct_qa", "planner_node": "planner_node"},
    )
    workflow.add_edge("planner_node", "controller_node")
    workflow.add_edge("controller_node", "executor_node") # Controller leads to executor
    
    # Add terminal edges
    workflow.add_edge("direct_qa", END)
    workflow.add_edge("executor_node", END) # Executor is the end for now

    agent = workflow.compile()
    logger.info("PCEE agent graph (Executor stage) compiled successfully.")
    return agent

agent_graph = create_agent_graph()
