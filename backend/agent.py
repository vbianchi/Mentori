# backend/agent.py
import logging
# *** REMOVED: hub import is no longer needed ***
# from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.memory import BaseMemory
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
# *** ADDED: Import PromptTemplate ***
from langchain_core.prompts import PromptTemplate
from typing import List

logger = logging.getLogger(__name__)

def create_agent_executor(
    llm: BaseChatModel,
    tools: List[BaseTool],
    memory: BaseMemory,
    max_iterations: int
) -> AgentExecutor:
    """Creates and returns a LangChain AgentExecutor with memory and max iterations."""
    logger.info(f"Creating LangChain agent executor with memory (Max Iterations: {max_iterations})...")

    # --- MODIFIED: Always use the local custom prompt template ---
    # Define the prompt template directly
    template = """Assistant is a large language model trained by Google.

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to communicate and generate human-like text in response to a wide range of prompts and questions.

Assistant has access to the following tools:

{tools}

Use the following format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
Thought: Do I need to use a tool? No
Final Answer: [your response here]

**IMPORTANT:** If you used a tool to find information (like search results or file content), **always include the full information found** in your Final Answer. Do not just summarize that you found it or refer to the Observation block.

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}"""
    try:
        prompt = PromptTemplate.from_template(template)
        logger.info("Using local custom prompt template.")
    except Exception as e:
        logger.error(f"Failed to create PromptTemplate from local template: {e}", exc_info=True)
        # If even the local template fails, something is fundamentally wrong
        raise RuntimeError(f"Could not create prompt template: {e}") from e
    # --- END MODIFIED SECTION ---


    # Create the ReAct agent
    try:
        agent = create_react_agent(llm, tools, prompt)
        logger.info("ReAct chat agent created.")
    except Exception as e:
        logger.error(f"Failed to create ReAct agent: {e}", exc_info=True)
        raise RuntimeError(f"Could not create the agent logic: {e}") from e

    # Create the Agent Executor, passing the memory object and max_iterations
    try:
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory, # Pass the memory object here
            verbose=True, # Consider making this configurable later
            handle_parsing_errors="Check your output and make sure it conforms!", # Or provide a more robust handler
            max_iterations=max_iterations # Use the passed value
        )
        logger.info("Agent Executor with memory created.")
        return agent_executor
    except Exception as e:
        logger.error(f"Failed to create AgentExecutor: {e}", exc_info=True)
        raise RuntimeError(f"Could not create the agent executor: {e}") from e
