# -----------------------------------------------------------------------------
# ResearchAgent Prompts
#
# Correction: The evaluator prompt is updated to include the `tool_call`
# so it can understand the Controller's intent when assessing the outcome.
# -----------------------------------------------------------------------------

from langchain_core.prompts import PromptTemplate

# 1. Planner Prompt
planner_prompt_template = PromptTemplate.from_template(
    """
You are an expert planner. Your job is to create a clear, step-by-step plan 
to fulfill the user's request.

**User Request:**
{input}

**Instructions:**
- Analyze the user's request and break it down into a sequence of logical steps.
- Each step should be a single, clear action.
- The plan should be a Python list of strings, where each string is a step.
- Do not add any conversational fluff or explanation. Your output must be ONLY the Python list.
---
**Begin!**

**User Request:**
{input}

**Your Output (must be a Python list of strings):**
"""
)

# 2. Controller Prompt (with History)
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


# 3. Evaluator Prompt (Smarter)
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

**Example:**
Plan Step: "Extract the version number and save it."
Controller's Action: {{"tool_name": "workspace_shell", "tool_input": "echo '0.3.25' > version.txt"}}
Tool's Output: "Command finished with exit code 0."
Your Output:
```json
{{
    "status": "success",
    "reasoning": "The controller correctly identified the version number and the shell tool successfully executed the command to save it to a file."
}}
```
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
