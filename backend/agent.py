# backend/agent.py
import logging
from langchain import hub # To pull standard prompts
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from typing import List

logger = logging.getLogger(__name__)

def create_agent_executor(llm: BaseChatModel, tools: List[BaseTool]) -> AgentExecutor:
    """Creates and returns a LangChain AgentExecutor."""
    logger.info("Creating LangChain agent executor...")

    # Get the ReAct prompt template
    # Ensure you have internet access when the server starts, or pull it manually beforehand
    # You can explore other prompts on Langchain Hub: https://smith.langchain.com/hub
    try:
        # prompt = hub.pull("hwchase17/react") # A common ReAct prompt
        prompt = hub.pull("hwchase17/react-chat") # A chat-optimized ReAct prompt
    except Exception as e:
        logger.error(f"Failed to pull prompt from Langchain Hub: {e}. Using a basic fallback.", exc_info=True)
        # Define a very basic fallback prompt if hub fails
        from langchain_core.prompts import PromptTemplate
        template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
        prompt = PromptTemplate.from_template(template)


    # Create the ReAct agent
    # This agent uses the ReAct framework (Reasoning + Acting)
    agent = create_react_agent(llm, tools, prompt)
    logger.info("ReAct agent created.")

    # Create the Agent Executor
    # verbose=True prints detailed agent steps to the console (good for debugging)
    # handle_parsing_errors=True helps prevent crashes if the LLM output isn't formatted perfectly
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10 # Limit the number of steps to prevent infinite loops
    )
    logger.info("Agent Executor created.")

    return agent_executor

