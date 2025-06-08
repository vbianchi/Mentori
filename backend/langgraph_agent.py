# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Correct Graph Structure)
#
# Correction:
# - The graph structure is fixed. The conditional edge now correctly
#   originates from the `prepare_inputs` node, using the `intent_classifier`
#   function to decide the next step.
# -----------------------------------------------------------------------------

import os
import logging
import ast
import re
from typing import TypedDict, Annotated, Sequence, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END

# --- Local Imports ---
from .prompts import planner_prompt_template

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    input: str
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    plan: List[str]
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

# --- Graph Nodes ---
def prepare_inputs_node(state: GraphState):
    """
    This node takes the initial user message and prepares the `input`
    field in the state for the other nodes to use.
    """
    logger.info("Executing prepare_inputs_node")
    user_message = state['messages'][-1].content
    return {"input": user_message}

def planner_node(state: GraphState):
    """Generates a multi-step plan."""
    logger.info("Executing planner_node")
    llm = get_llm("PLANNER_LLM_ID", "gemini::gemini-2.0-flash")
    prompt = planner_prompt_template
    planner_chain = prompt | llm
    response = planner_chain.invoke({"input": state["input"]})
    try:
        match = re.search(r"```python\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        if match:
            plan_str = match.group(1).strip()
        else:
            plan_str = response.content.strip()
        plan = ast.literal_eval(plan_str)
        if isinstance(plan, list) and all(isinstance(item, str) for item in plan):
             logger.info(f"Generated plan: {plan}")
             return {"plan": plan}
        raise ValueError("LLM did not return a valid list of strings.")
    except (ValueError, SyntaxError) as e:
        logger.error(f"Error parsing plan from LLM response: {e}\nResponse was:\n{response.content}")
        return {"plan": [f"Error creating plan: {e}"]}

def direct_qa_node(state: GraphState):
    """Directly calls an LLM for a simple question."""
    logger.info("Executing direct_qa_node")
    llm = get_llm("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

# --- Conditional Routing ---
def intent_classifier(state: GraphState):
    """
    Classifies the user's intent. This function now ONLY returns a
    routing decision and does not modify the state.
    """
    logger.info("Classifying intent")
    llm = get_llm("INTENT_CLASSIFIER_LLM_ID", "gemini::gemini-1.5-flash")
    prompt = (
        "Classify the user's last message. "
        "Respond with 'AGENT_ACTION' for a task, or 'DIRECT_QA' for a simple question.\n\n"
        f"User message: '{state['input']}'"
    )
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Intent classified as: {decision}")
    if "AGENT_ACTION" in decision:
        return "planner_node"
    else:
        return "direct_qa_node"

# --- Graph Definition ---
def create_agent_graph():
    """Builds the LangGraph."""
    workflow = StateGraph(GraphState)

    # Add all nodes
    workflow.add_node("prepare_inputs", prepare_inputs_node)
    workflow.add_node("direct_qa", direct_qa_node)
    workflow.add_node("planner_node", planner_node)
    
    # Set the entry point
    workflow.set_entry_point("prepare_inputs")
    
    # === FIX: The conditional edge now starts from the `prepare_inputs` node ===
    workflow.add_conditional_edges(
        "prepare_inputs",
        intent_classifier,
        {
            "direct_qa_node": "direct_qa",
            "planner_node": "planner_node",
        },
    )

    # Add terminal edges
    workflow.add_edge("direct_qa", END)
    workflow.add_edge("planner_node", END)

    agent = workflow.compile()
    logger.info("PCEE agent graph (Planner stage v3) compiled successfully.")
    return agent

agent_graph = create_agent_graph()
