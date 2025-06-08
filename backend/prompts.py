# -----------------------------------------------------------------------------
# ResearchAgent Prompts (Advanced Architecture)
#
# Correction: Added an explicit instruction to the planner to use double
# quotes and escape internal quotes to ensure valid JSON output.
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
  - "expected_output": A clear description of what a successful output from the tool should look like or contain.
- Your final output must be a single, valid JSON object containing a "plan" key, which holds a list of these step objects.
- **CRITICAL:** Ensure the final output is a perfectly valid JSON. All strings must use double quotes. Any double quotes inside a string must be properly escaped with a backslash (e.g., "This is a \\"quoted\\" string.").
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.

---
**Begin!**

**User Request:**
{input}

**Your Output (must be a single, valid JSON object):**
"""
)
