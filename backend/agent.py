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
    logger.info(f"Creating LangChain agent executor with memory (Max Iterations: {max_iterations})...")

    # <<< --- START MODIFIED CODE --- >>>
    template = """Assistant is a large language model trained by Valerio Bianchi.
Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics.
As a language model, Assistant is able to communicate and generate human-like text in response to a wide range of prompts and questions.
Assistant has access to the following tools:

{tools}

Use the following format for your thought process and actions:

**Format Option 1: Tool Use**
Thought: Do I need to use a tool? Yes
Action: The EXACT name of the tool to take, which MUST be one of [{tool_names}]. Do NOT include any other text or explanation on this line.
Action Input: The input to the action. This should be on a new line immediately following the 'Action:' line. **If the tool's description (from the initial "Available Tools" list provided in the system prompt when you were initialized) specifies that its input MUST be a JSON string, ensure your Action Input is that exact, complete, and valid JSON string.**
Observation: [RESULT_OF_TOOL_ACTION]
Thought: The tool has executed. The goal of this step was to obtain the tool's direct output. Therefore, my Final Answer for this step MUST be the exact content of the 'Observation' above, without any added summarization, commentary, or rephrasing, unless the original 'New input' for this thought-cycle explicitly instructed me to transform or summarize the tool's output.
Final Answer: [THE_EXACT_CONTENT_OF_THE_OBSERVATION_ABOVE]

**Format Option 2: Direct Answer (No Tool Use This Turn)**
Thought: Do I need to use a tool? No. I can answer directly based on the 'New input', 'Previous conversation history', or previous 'Observation' in the scratchpad.
Final Answer: (Your entire response for this step, which directly fulfills the 'precise expected output' from the 'New input' directive, goes here.
If your response is multi-line or contains structured text like Markdown or JSON, ensure the entire response is a single, contiguous block of text immediately following "Final Answer:".
For example, if generating a Markdown table or a JSON object, the entire structure, including all lines and formatting characters like backticks or braces, defines your Final Answer for this thought-cycle.
Avoid any conversational text, preamble, or additional "Thought:" or "Action:" lines after you have stated "Final Answer:" for this thought-cycle.
The content of your Final Answer should be exactly what the user or the next step in a plan expects to receive.)


**IMPORTANT NOTES ON YOUR OUTPUT:**
1.  **Choose a Format:** For each thought-cycle, you must decide if you are using a tool (Format Option 1) or answering directly (Format Option 2).
2.  **Using Tool Output (Format Option 1):**
    * When you use a tool and receive an `Observation`, your *next immediate thought* should be as described in "Format Option 1": acknowledge the tool execution and confirm that the `Observation` content will be your `Final Answer`.
    * Your `Final Answer:` MUST then be the **exact, verbatim content** of the `Observation`. Do not add introductory phrases like "The tool returned:", "Here is the report:", or "The file content is:". Just provide the raw observation.
3.  **Direct Answer (Format Option 2):**
    * Use this if you are *not* calling a tool in the current thought-cycle. Your `Final Answer:` should directly address the 'New input' directive.
    * If the 'New input' asks you to process information from a *previous* `Observation` (visible in your `agent_scratchpad`), your `Final Answer` should include or be based on that information as instructed.
4.  **Strict Formatting:** Adhere strictly to one of the two formats above. No extra text outside this structure for each thought-cycle.

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
        agent = create_react_agent(llm, tools, prompt)
        logger.info("ReAct chat agent created.")
    except Exception as e:
        logger.error(f"Failed to create ReAct agent: {e}", exc_info=True)
        raise RuntimeError(f"Could not create the agent logic: {e}") from e

    try:
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors="Check your output and make sure it conforms to the specified format!",
            max_iterations=max_iterations,
        )
        logger.info("Agent Executor with memory created.")
        return agent_executor
    except Exception as e:
        logger.error(f"Failed to create AgentExecutor: {e}", exc_info=True)
        raise RuntimeError(f"Could not create the agent executor: {e}") from e
