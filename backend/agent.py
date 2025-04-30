# backend/agent.py
import logging
from langchain import hub # To pull standard prompts
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.memory import BaseMemory
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from typing import List
from backend.config import Settings # Import Settings

logger = logging.getLogger(__name__)

# Modified to accept settings
def create_agent_executor(llm: BaseChatModel, tools: List[BaseTool], memory: BaseMemory, settings: Settings) -> AgentExecutor:
    """Creates and returns a LangChain AgentExecutor with memory and configured settings."""
    logger.info("Creating LangChain agent executor with memory...")

    # Get the ReAct Chat prompt template - requires 'chat_history' input variable
    try:
        prompt = hub.pull("hwchase17/react-chat")
    except Exception as e:
        logger.error(f"Failed to pull prompt 'hwchase17/react-chat' from Langchain Hub: {e}. Using a basic fallback.", exc_info=True)
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
    agent = create_react_agent(llm, tools, prompt)
    logger.info("ReAct chat agent created.")

    # Create the Agent Executor, passing the memory object and using configured settings
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory, # Pass the memory object here
        verbose=True, # Keep verbose for now, could be configurable later
        handle_parsing_errors="Check your output and make sure it conforms!", # Basic error handling
        # --- MODIFIED: Use max_iterations from settings ---
        max_iterations=settings.agent_max_iterations
    )
    logger.info(f"Agent Executor created. Max iterations: {settings.agent_max_iterations}")

    return agent_executor

