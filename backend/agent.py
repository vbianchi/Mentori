# backend/agent.py
import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.memory import BaseMemory
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
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
    logger.info(f"Creating LangChain agent executor with memory (Max Iterations: {max_iterations})...") #

    # <<< --- START MODIFIED CODE --- >>>
    template = """Assistant is a large language model trained by Valerio Bianchi.
Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. #
As a language model, Assistant is able to communicate and generate human-like text in response to a wide range of prompts and questions. #
Assistant has access to the following tools:

{tools}

Use the following format for your thought process and actions:

Thought: Do I need to use a tool? Yes
Action: The EXACT name of the tool to take, which MUST be one of [{tool_names}]. Do NOT include any other text or explanation on this line. #
Action Input: The input to the action. This should be on a new line immediately following the 'Action:' line. **If the tool's description (from the initial "Available Tools" list provided in the system prompt when you were initialized) specifies that its input MUST be a JSON string, ensure your Action Input is that exact, complete, and valid JSON string.** #
Observation: The result of the action. #
Thought: Do I need to use a tool? No
Final Answer: (Your entire response for this step, which directly fulfills the 'precise expected output' from the directive, goes here.
If your response is multi-line or contains structured text like Markdown or JSON, ensure the entire response is a single, contiguous block of text immediately following "Final Answer:".
For example, if generating a Markdown table or a JSON object, the entire structure, including all lines and formatting characters like backticks or braces, defines your Final Answer for this thought-cycle.
Avoid any conversational text, preamble, or additional "Thought:" or "Action:" lines after you have stated "Final Answer:" for this thought-cycle. #
The content of your Final Answer should be exactly what the user or the next step in a plan expects to receive.)

**IMPORTANT NOTES ON YOUR OUTPUT:**
1.  **Tool Usage vs. Direct Answer:**
    * If a tool is the best way to achieve the current sub-task's goal, use the `Action: [TOOL_NAME_ONLY]` followed by `Action Input: [INPUT_FOR_TOOL]` format. #
    * If you can fulfill the current sub-task's goal directly with your own knowledge or by processing information already in the `agent_scratchpad` (previous thoughts, actions, observations) or `chat_history`, use the `Final Answer:` format. #
2.  **Content of `Final Answer`:**
    * When providing a `Final Answer`, ensure it directly and completely addresses the current sub-task's directive, especially the 'precise expected output' if provided in the input. #
    * If the sub-task involved using a tool in a *previous turn of this ReAct chain* (i.e., you see an `Observation:` in your `agent_scratchpad` for this current step), and the goal of *this current turn* is to present or process that information, **your `Final Answer` must include the full, relevant information from that `Observation`** unless the directive explicitly asks for a summary or transformation. #
    * Do not just refer to the Observation block implicitly. #
3.  **Strict Formatting:** Adhere strictly to the `Thought:` followed by `Action: ... Action Input: ... Observation: ...` sequence (if using a tool for that thought) OR `Thought:` followed by `Final Answer: ...` (if not using a tool for that thought). #
    * No extra text outside this structure. #

Begin!
Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}"""
    # <<< --- END MODIFIED CODE --- >>>

    try:
        prompt = PromptTemplate.from_template(template)
        logger.info("Using local custom prompt template for ReAct agent.")
    except Exception as e:
        logger.error(f"Failed to create PromptTemplate from local template: {e}", exc_info=True)
        raise RuntimeError(f"Could not create prompt template: {e}")

    try:
        agent = create_react_agent(llm, tools, prompt) #
        logger.info("ReAct chat agent created.")
    except Exception as e:
        logger.error(f"Failed to create ReAct agent: {e}", exc_info=True)
        raise RuntimeError(f"Could not create the agent logic: {e}") from e

    try:
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory, #
            verbose=True,
            handle_parsing_errors="Check your output and make sure it conforms to the specified format!", # More direct error message
            max_iterations=max_iterations,
            # early_stopping_method="generate", # Consider if LLM consistently fails formatting
        )
        logger.info("Agent Executor with memory created.") #
        return agent_executor
    except Exception as e:
        logger.error(f"Failed to create AgentExecutor: {e}", exc_info=True)
        raise RuntimeError(f"Could not create the agent executor: {e}") from e
