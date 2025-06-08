# -----------------------------------------------------------------------------
# ResearchAgent Prompts
#
# This file centralizes all the prompts used by the different nodes in our
# LangGraph agent. Keeping them in one place makes them easier to manage,
# version, and tune.
# -----------------------------------------------------------------------------

from langchain_core.prompts import PromptTemplate

# --- Phase 4: PCEE Loop Prompts ---

# 1. Planner Prompt
# This prompt is used by the Planner node to break down the user's complex
# request into a sequence of smaller, actionable steps.
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

**Example:**
User Request: "Find the latest news about AI and then write a summary to a file named 'ai_news.txt'."
Your Output:
```python
[
    "Search the web for the latest news about AI.",
    "Read the content of the top 3 search results.",
    "Synthesize a summary of the news from the content.",
    "Write the summary to a file named 'ai_news.txt'."
]
```

**Begin!**

**User Request:**
{input}

**Your Output (must be a Python list of strings):**
"""
)


# 2. Controller Prompt
# This prompt is used by the Controller node to select the single best tool
# to execute the current step of the plan.
controller_prompt_template = PromptTemplate.from_template(
    """
You are an expert controller agent. Your job is to select the most appropriate 
tool to execute the given step of a plan.

**Available Tools:**
{tools}

**Plan:**
{plan}

**Current Step:**
{current_step}

**Instructions:**
- Analyze the current step and select the single best tool to accomplish it.
- Your output must be a single, valid JSON object containing the chosen tool's name 
  and the exact input for that tool.
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.

**Example:**
Current Step: "Search the web for the current version of LangChain."
Your Output:
```json
{{
    "tool_name": "tavily_search",
    "tool_input": "current version of LangChain"
}}
```

**Begin!**

**Current Step:**
{current_step}

**Your Output (must be a single JSON object):**
"""
)

