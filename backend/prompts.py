# -----------------------------------------------------------------------------
# ResearchAgent Prompts (Complete)
#
# This file contains the complete set of prompts required by the current
# version of the langgraph_agent.py file, including the Planner,
# Controller, and Evaluator prompts.
# -----------------------------------------------------------------------------

from langchain_core.prompts import PromptTemplate

# 1. Structured Planner Prompt
structured_planner_prompt_template = PromptTemplate.from_template(
    """
You are an expert architect and planner. Your job is to create a detailed,
step-by-step execution plan in JSON format to fulfill the user's request.

**User Request:**
{input}

**Available Tools:**
{tools}

**Instructions:**
- Analyze the user's request and the available tools.
- Decompose the request into a sequence of logical steps.
- For each step, you must specify:
  - "step_id": A unique integer for the step (e.g., 1, 2, 3).
  - "instruction": A clear, natural language description of what to do in this step.
  - "tool_name": The single most appropriate tool from the "Available Tools" list to accomplish this step.
  - "tool_input": The precise input to provide to the chosen tool.
- Your final output must be a single, valid JSON object containing a "plan" key, which holds a list of these step objects.
- CRITICAL: Ensure the final output is a perfectly valid JSON. All strings must use double quotes. Any double quotes inside a string must be properly escaped with a backslash (e.g., "This is a \\"quoted\\" string.").
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.
---
**Begin!**

**User Request:**
{input}

**Your Output (must be a single JSON object):**
"""
)

# === RESTORED: Controller Prompt ===
controller_prompt_template = PromptTemplate.from_template(
    """
You are an expert controller agent. Your job is to select the most appropriate 
tool to execute the given step of a plan, based on the history of previous steps.

**Available Tools:**
{tools}

**Plan:**
{plan}

**History of Past Steps:**
{history}

**Current Step:**
{current_step}

**Instructions:**
- Analyze the current step in the context of the plan and the history of past actions.
- Your output must be a single, valid JSON object containing the chosen tool's name 
  and the exact input for that tool.
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.
---
**Begin!**

**History of Past Steps:**
{history}

**Current Step:**
{current_step}

**Your Output (must be a single JSON object):**
"""
)

# === RESTORED: Evaluator Prompt ===
evaluator_prompt_template = PromptTemplate.from_template(
    """
You are an expert evaluator. Your job is to assess the outcome of a tool's 
execution and determine if the step was successful.

**Plan Step:**
{current_step}

**Controller's Action (the tool call that was just executed):**
{tool_call}

**Tool's Output:**
{tool_output}

**Instructions:**
- Analyze the tool's output in the context of both the Plan Step and the Controller's Action.
- Determine if the step was successfully completed. The goal is to see if the Controller's Action successfully addressed the Plan Step.
- Your output must be a single, valid JSON object containing a "status" key, 
  which can be "success" or "failure", and a "reasoning" key with a brief explanation.
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.
---
**Begin!**

**Plan Step:**
{current_step}

**Controller's Action:**
{tool_call}

**Tool's Output:**
{tool_output}

**Your Output (must be a single JSON object):**
"""
)
