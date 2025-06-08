# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 2: Minimal Graph)
#
# This file defines the core LangGraph agent. For this initial phase, it
# implements a very simple graph with a single node: `direct_qa`. This node
# will take the user's question, pass it to an LLM, and return the answer.
# -----------------------------------------------------------------------------

import os
import logging
from typing import TypedDict
from langchain_core.messages import HumanMessage
# CORRECTED IMPORT: The module name is langchain_google_genai, not langchain_google.
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Agent State Definition ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: The user's question.
        answer: The LLM's answer.
    """
    question: str
    answer: str

# --- LLM Provider Helper ---
def get_llm():
    """
    Factory function to get the appropriate LLM based on environment variables.
    """
    # I have reverted this to your preference as well.
    llm_id = os.getenv("DEFAULT_LLM_ID", "gemini::gemini-2.0-flash")
    provider, model_name = llm_id.split("::")

    logging.info(f"Initializing LLM: Provider={provider}, Model={model_name}")

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        # Ensure temperature is a float
        temp = float(os.getenv("GEMINI_TEMPERATURE", 0.7))
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=temp)
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        temp = float(os.getenv("OLLAMA_TEMPERATURE", 0.5))
        return ChatOllama(model=model_name, base_url=base_url, temperature=temp)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

# --- Graph Nodes ---
async def direct_qa_node(state: GraphState):
    """
    A node that takes the question from the state, asks the LLM,
    and puts the answer back into the state.
    """
    logging.info("Executing direct_qa_node")
    question = state.get('question')
    if not question:
        logging.error("No question found in state for direct_qa_node")
        return {"answer": "Error: No question provided."}

    try:
        llm = get_llm()
        response = await llm.ainvoke([HumanMessage(content=question)])
        answer = response.content
        logging.info(f"LLM generated answer: {answer[:100]}...")
        return {"answer": answer}
    except Exception as e:
        logging.error(f"Error in direct_qa_node: {e}", exc_info=True)
        return {"answer": f"Sorry, an error occurred while processing your question: {e}"}


# --- Graph Definition ---
def create_agent_graph():
    """
    Builds the LangGraph agent.
    """
    workflow = StateGraph(GraphState)
    workflow.add_node("direct_qa", direct_qa_node)
    workflow.set_entry_point("direct_qa")
    workflow.add_edge("direct_qa", END)
    agent = workflow.compile()
    logging.info("Minimal agent graph compiled successfully.")
    return agent

# Create a global instance of the agent to be used by the server
agent_graph = create_agent_graph()
