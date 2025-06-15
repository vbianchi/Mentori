# -----------------------------------------------------------------------------
# ResearchAgent Prompts (Phase 9.1: Three-Track Router)
#
# This file contains the prompts for the ResearchAgent.
#
# 1. New `router_prompt_template`: This is the key addition. It's a more
#    sophisticated prompt that guides a powerful LLM to classify a user's
#    request into one of three specific categories: `DIRECT_QA` for simple
#    questions, `SIMPLE_TOOL_USE` for single commands, or `COMPLEX_PROJECT`
#    for multi-step tasks.
# -----------------------------------------------------------------------------

from langchain_core.prompts import PromptTemplate

# --- NEW: Three-Track Router Prompt ---
router_prompt_template = PromptTemplate.from_template(
    """
You are an expert request router. Your job is to classify the user's request into one of three categories based on its complexity and the tools required.

**Available Tools:**
{tools}

**Categories:**
1.  **DIRECT_QA**: For simple, knowledge-based questions that can be answered directly by a powerful language model without using any tools.
    -   Examples: "What is the capital of France?", "Explain the theory of relativity in simple terms.", "Who wrote 'To Kill a Mockingbird'?"
2.  **SIMPLE_TOOL_USE**: For requests that can be fulfilled with a single tool call. This is for direct commands to use a specific tool.
    -   Examples: "list the files in the current directory", "read the file 'main.py'", "search the web for the latest news on AI"
3.  **COMPLEX_PROJECT**: For requests that require multiple steps, planning, or the use of several tools in a sequence to achieve the final goal.
    -   Examples: "Research the market for electric vehicles and write a summary report.", "Create a python script to fetch data from an API and save it to a CSV file.", "Find the top 3 competitors to LangChain and create a feature comparison table."

**User Request:**
{input}

**Instructions:**
- Analyze the user's request and the list of available tools.
- Based on your analysis, you must respond with ONLY ONE of the following three strings:
  - "DIRECT_QA"
  - "SIMPLE_TOOL_USE"
  - "COMPLEX_PROJECT"
- Do not add any other words, explanation, or punctuation. Your output must be one of the three category names and nothing else.

**Your Output:**
"""
)


# 2. Structured Planner Prompt
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
- CRITICAL: Ensure the final output is a perfectly valid JSON. All strings must use double quotes.
- Any double quotes inside a string must be properly escaped with a backslash (e.g., "This is a \\"quoted\\" string.").
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.
---
**Example Output:**
```json
{{
  "plan": [
    {{
      "step_id": 1,
      "instruction": "Search the web to find the main topic of the user's request.",
      "tool_name": "web_search",
      "tool_input": {{
        "query": "example search query"
      }}
    }},
    {{
      "step_id": 2,
      "instruction": "Write the findings from the web search to a file named 'research_summary.txt'.",
      "tool_name": "write_file",
      "tool_input": {{
        "file": "research_summary.txt",
        "content": "The summary of the research findings will be placed here."
      }}
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

# 3. Controller Prompt
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
**Example Output:**
```json
{{
  "tool_name": "web_search",
  "tool_input": {{
    "query": "what is the latest version of langchain?"
  }}
}}
```
---

**Begin!**

**History of Past Steps:**
{history}

**Current Step:**
{current_step}

**Your Output (must be a single JSON object):**
"""
)

# 4. Evaluator Prompt
evaluator_prompt_template = PromptTemplate.from_template(
    """
You are an expert evaluator.
Your job is to assess the outcome of a tool's
execution and determine if the step was successful.
**Plan Step:**
{current_step}

**Controller's Action (the tool call that was just executed):**
{tool_call}

**Tool's Output:**
{tool_output}

**Instructions:**
- **Critically assess** if the `Tool's Output` **fully and completely satisfies** the `Plan Step`'s instruction.
- **Do not just check for a successful exit code or the presence of output.** You must verify that the *substance* of the output achieves the step's goal.
For example, if the step was to find a specific fact, does the output actually contain that fact?
If not, you must declare it a failure.
- Your output must be a single, valid JSON object containing a "status" key (which can be "success" or "failure") and a "reasoning" key with a brief explanation.
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.
---
**Example Output:**
```json
{{
  "status": "success",
  "reasoning": "The tool output successfully provided the requested information, which was the capital of France."
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

# 5. Final Answer Synthesis Prompt
final_answer_prompt_template = PromptTemplate.from_template(
    """
You are the final, user-facing voice of the ResearchAgent. Your role is to act as an expert editor.
You have been given the user's original request and the complete history of a multi-step plan that was executed to fulfill it.

Your task is to synthesize all the information from the history into a single, comprehensive, and well-written final answer for the user.

**User's Original Request:**
{input}

**Full Execution History:**
{history}

**Instructions:**
1.  Carefully review the entire execution history, including the instructions, actions, and observations for each step.
2.  Identify the key findings and the data gathered throughout the process.
3.  Synthesize this information into a clear and coherent response that directly answers the user's original request.
4.  If the process failed or was unable to find a definitive answer, explain what happened based on the history, and provide the most helpful information you could find.
5.  Format your answer in clean markdown.
6.  Do not output JSON or any other machine-readable format.
Your output must be only the final, human-readable text for the user.
**Begin!**

**Final Answer:**
"""
)

# 6. Correction Planner Prompt
correction_planner_prompt_template = PromptTemplate.from_template(
    """
You are an expert troubleshooter and correction planner. A step in a larger plan has failed.
Your job is to analyze the failure and create a *new, single-step plan* to fix the immediate problem.

**Original Plan:**
{plan}

**Full Execution History:**
{history}

**Failed Step Instruction:**
{failed_step}

**Supervisor's Evaluation of Failure:**
{failure_reason}

**Available Tools:**
{tools}

**Instructions:**
- Analyze the reason for the failure in the context of the history and the original plan.
- Your goal is to formulate a *single, corrective action* to overcome this specific failure.
- This might mean retrying the same tool with different input, or using a different tool to achieve the goal of the failed step.
- Your output must be a single, valid JSON object representing this new, single-step plan. It must follow the exact same format as the original plan's steps.
- Do not add any conversational fluff or explanation. Your output must be ONLY the JSON object.

---
**Example Scenario:**
- **Failed Step:** "Write an article about the new 'Super-Car' to a file named 'car.txt'."
- **Failure Reason:** "The web_search tool was not used, so there is no information about the 'Super-Car' available to write."
- **Example Corrective Output:**
```json
{{
    "step_id": "1-correction",
    "instruction": "The previous attempt to write the file failed because no information was available. First, search the web to gather information about the new 'Super-Car'.",
    "tool_name": "web_search",
    "tool_input": {{
        "query": "information about the new Super-Car"
    }}
}}
```
---

**Begin!**

**Failed Step Instruction:**
{failed_step}

**Supervisor's Evaluation of Failure:**
{failure_reason}

**Your Output (must be a single JSON object for a single corrective step):**
"""
)
