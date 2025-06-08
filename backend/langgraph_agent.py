# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Advanced Architecture - Structured Planner)
#
# This is a major refactoring to implement the new, more sophisticated agent
# architecture based on a structured plan.
#
# Key Changes:
# - The Planner is now a "Chief Architect", creating a detailed JSON plan
#   with tool calls and expected outcomes for each step.
# - The GraphState is updated to hold this new `plan` (a list of dictionaries).
# - The `planner_node` is updated to use the new structured prompt and parse JSON.
# - All previous PCEE nodes (Controller, Executor, Evaluator) have been
#   removed to make way for new versions that will work with this structured plan.
# - The graph now stops after the planner, allowing for isolated testing.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
from typing import TypedDict, Annotated, Sequence, List
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
    """
    Represents the state of our graph under the new architecture.

    Attributes:
        input: The initial user request.
        plan: A list of dictionaries, where each dictionary is a detailed
              step in the execution plan (tool, input, expected output).
        messages: The history of messages in the conversation.
        answer: The final answer from a direct QA route.
    """
    input: str
    plan: List[dict]
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
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
def format_tools_for_prompt():
    """Formats the available tools for inclusion in the planner's prompt."""
    return "\n".join([f"  - {tool.name}: {tool.description}" for tool in AVAILABLE_TOOLS])

# --- Graph Nodes ---
def prepare_inputs_node(state: GraphState):
    """Initializes the state for a new run."""
    logger.info("Executing prepare_inputs_node")
    user_message = state['messages'][-1].content
    return {"input": user_message}

def structured_planner_node(state: GraphState):
    """
    Generates a detailed, structured, multi-step plan in JSON format.
    """
    logger.info("Executing structured_planner_node")
    llm = get_llm("PLANNER_LLM_ID", "gemini::gemini-2.5-flash-preview-05-20")
    
    prompt = structured_planner_prompt_template.format(
        input=state["input"],
        tools=format_tools_for_prompt()
    )
    
    response = llm.invoke(prompt)
    
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.content, re.DOTALL)
        json_str = match.group(1).strip() if match else response.content.strip()
        parsed_json = json.loads(json_str)
        
        # Validate the structure of the plan
        if "plan" in parsed_json and isinstance(parsed_json["plan"], list):
            logger.info(f"Generated structured plan: {parsed_json['plan']}")
            return {"plan": parsed_json["plan"]}
        else:
            raise ValueError("The JSON output from the planner is missing the 'plan' key or it is not a list.")
            
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing structured plan from LLM response: {e}\nResponse was:\n{response.content}")
        return {"plan": [{"error": f"Failed to create a valid plan. Reason: {e}"}]}

def direct_qa_node(state: GraphState):
    """Directly calls an LLM for a simple question."""
    logger.info("Executing direct_qa_node")
    llm = get_llm("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

# --- Conditional Routing ---
def intent_classifier(state: GraphState):
    """Routes based on user intent."""
    logger.info("Classifying intent")
    llm = get_llm("INTENT_CLASSIFIER_LLM_ID", "gemini::gemini-1.5-flash")
    prompt = f"Classify the user's last message. Respond with 'AGENT_ACTION' for a task, or 'DIRECT_QA' for a simple question.\n\nUser message: '{state['input']}'"
    response = llm.invoke(prompt)
    decision = response.content.strip()
    logger.info(f"Intent classified as: {decision}")
    return "structured_planner_node" if "AGENT_ACTION" in decision else "direct_qa_node"

# --- Graph Definition ---
def create_agent_graph():
    """Builds the LangGraph with the new structured planner."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("prepare_inputs", prepare_inputs_node)
    workflow.add_node("direct_qa", direct_qa_node)
    workflow.add_node("structured_planner_node", structured_planner_node)
    
    # Set entry point
    workflow.set_entry_point("prepare_inputs")
    
    # Define edges
    workflow.add_conditional_edges(
        "prepare_inputs",
        intent_classifier,
        {
            "direct_qa_node": "direct_qa",
            "structured_planner_node": "structured_planner_node",
        },
    )
    
    # Add terminal edges for this phase
    workflow.add_edge("direct_qa", END)
    workflow.add_edge("structured_planner_node", END)

    agent = workflow.compile()
    logger.info("Advanced agent graph (Structured Planner stage) compiled successfully.")
    return agent

agent_graph = create_agent_graph()
