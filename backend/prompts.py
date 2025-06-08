# -----------------------------------------------------------------------------
# ResearchAgent Prompts (Advanced Architecture)
#
# This file centralizes all the prompts for our new, more sophisticated
# agent architecture.
# -----------------------------------------------------------------------------

from langchain_core.prompts import PromptTemplate

# --- Advanced PCEE Loop Prompts ---

# 1. Structured Planner Prompt
# This is the new "Chief Architect" prompt. It instructs the Planner to
# generate a detailed, structured plan as a JSON object.
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
  - "expected_output": A clear description of what a successful output from the tool should look like or contain. This is for verification.
- Your final output must be a single, valid JSON object containing a "plan" key, which holds a list of these step objects.
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.

**Example:**
User Request: "Find the latest version of LangChain and save it to a file."
Your Output:
```json
{{
    "plan": [
        {{
            "step_id": 1,
            "instruction": "Search the web to find the official PyPI page for LangChain.",
            "tool_name": "tavily_search",
            "tool_input": "LangChain PyPI",
            "expected_output": "A list of search results containing a URL pointing to pypi.org for the langchain package."
        }},
        {{
            "step_id": 2,
            "instruction": "Extract the latest version number from the PyPI page search result.",
            "tool_name": "workspace_shell",
            "tool_input": "echo '0.3.25'",
            "expected_output": "A string containing the version number, e.g., '0.3.25'."
        }},
        {{
            "step_id": 3,
            "instruction": "Write the extracted version number to a file named 'langchain_version.txt'.",
            "tool_name": "workspace_shell",
            "tool_input": "echo '0.3.25' > langchain_version.txt",
            "expected_output": "A confirmation that the shell command executed successfully (exit code 0)."
        }}
    ]
}}
```
---
**Begin!**

**User Request:**
{input}

**Your Output (must be a single JSON object):**
"""
)
