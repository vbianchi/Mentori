# backend/agent.py
import logging
from langchain import hub # To pull standard prompts
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.memory import BaseMemory # Import from langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from typing import List

logger = logging.getLogger(__name__)

# *** MODIFIED: Accepts max_iterations ***
def create_agent_executor(
    llm: BaseChatModel,
    tools: List[BaseTool],
    memory: BaseMemory,
    max_iterations: int # Added parameter
) -> AgentExecutor:
    """Creates and returns a LangChain AgentExecutor with memory and max iterations."""
    logger.info(f"Creating LangChain agent executor with memory (Max Iterations: {max_iterations})...")

    # Get the ReAct Chat prompt template - requires 'chat_history' input variable
    try:
        prompt = hub.pull("hwchase17/react-chat")
        # Check if the pulled prompt supports 'chat_history' if necessary
        if "chat_history" not in prompt.input_variables:
             logger.warning("Pulled 'hwchase17/react-chat' prompt might be missing 'chat_history'. Using fallback.")
             raise ValueError("Prompt missing required 'chat_history' variable.")
    except Exception as e:
        logger.error(f"Failed to pull prompt 'hwchase17/react-chat' from Langchain Hub or it's incompatible: {e}. Using a basic fallback.", exc_info=True)
        # Define a fallback prompt that includes chat_history
        from langchain_core.prompts import PromptTemplate
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

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}"""
        prompt = PromptTemplate.from_template(template)

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