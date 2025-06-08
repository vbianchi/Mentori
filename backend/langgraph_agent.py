# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 3: Tool-Using ReAct Agent)
#
# Correction: This version fixes a KeyError in the `agent_node` by making
# it derive its input directly from the `messages` list. It also correctly
# wraps the agent's output in an AIMessage object.
# -----------------------------------------------------------------------------

import os
import logging
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END

# --- Local Imports ---
from .tools import get_available_tools

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class GraphState(TypedDict):
    input: str
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

# --- ReAct Agent Definition ---
def create_react_agent_executor():
    """Creates the ReAct agent that can use our toolset."""
    tools = get_available_tools()
    if not tools:
        logger.warning("No tools available for the agent.")
    
    llm = get_llm("EXECUTOR_DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    prompt = hub.pull("hwchase17/react-chat")

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )
    return agent_executor

react_agent_executor = create_react_agent_executor()

# --- Graph Nodes ---
def agent_node(state: GraphState):
    """
    Runs the ReAct agent.
    
    This node is now self-contained and derives its inputs directly from the
    state's `messages` list.
    """
    logger.info("Executing agent_node")

    # === FIX 1: Derive input and history from the messages list ===
    # The last message is the user's input, and previous messages are the history.
    agent_input = {
        "input": state["messages"][-1].content,
        "chat_history": state["messages"][:-1]
    }
    
    response = react_agent_executor.invoke(agent_input)

    # === FIX 2: Wrap the agent's string output in an AIMessage object ===
    # This ensures the output matches the expected type for the 'messages' state key.
    return {"messages": [AIMessage(content=response["output"])]}

def direct_qa_node(state: GraphState):
    """Directly calls an LLM for a simple question."""
    logger.info("Executing direct_qa_node")
    llm = get_llm("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    response = llm.invoke(state["messages"])
    return {"answer": response.content}

# --- Conditional Routing ---
def intent_classifier(state: GraphState):
    """
    Classifies the user's intent to decide whether to use tools or not.
    """
    logger.info("Classifying intent")
    llm = get_llm("INTENT_CLASSIFIER_LLM_ID", "gemini::gemini-1.5-flash")
    
    prompt = (
        "Classify the user's last message. "
        "Respond with 'AGENT_ACTION' if the user is asking for a task to be done, "
        "like searching the web, running code, or interacting with files. "
        "Respond with 'DIRECT_QA' if the user is asking a general question "
        "that can be answered without using any tools.\n\n"
        f"User message: '{state['messages'][-1].content}'"
    )
    
    response = llm.invoke(prompt)
    decision = response.content.strip()
    
    logger.info(f"Intent classified as: {decision}")
    
    if "AGENT_ACTION" in decision:
        return "agent_node"
    else:
        return "direct_qa_node"

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("direct_qa", direct_qa_node)
    workflow.add_node("agent_node", agent_node)
    workflow.set_conditional_entry_point(
        intent_classifier,
        {"direct_qa_node": "direct_qa", "agent_node": "agent_node"},
    )
    workflow.add_edge("direct_qa", END)
    workflow.add_edge("agent_node", END)
    agent = workflow.compile()
    logger.info("Tool-using agent graph with conditional routing compiled successfully.")
    return agent

agent_graph = create_agent_graph()
