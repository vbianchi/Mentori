# -----------------------------------------------------------------------------
# HITL Prototype Script (hitl_prototype.py)
#
# Description:
# This script demonstrates a Human-in-the-Loop (HITL) workflow using
# LangGraph's breakpoint/interrupt feature. It simulates the core interaction
# required for Phase 9 of the ResearchAgent project.
#
# Workflow:
# 1.  It defines a simple graph with two nodes: "Architect" and "Execute".
# 2.  The "Architect" node, powered by Google's Gemini model, generates a
#     JSON-based plan from a user's request.
# 3.  The graph is compiled with an `interrupt_after` argument, which
#     explicitly pauses execution immediately after the "Architect" node
#     completes its work.
# 4.  The script then prompts the user (the "human in the loop") via the
#     command line to review the generated plan.
# 5.  The user can either type "approve" to continue with the original plan
#     or paste in a modified JSON plan.
# 6.  Based on the user's input, the script either resumes the graph directly
#     or first updates the graph's state with the modified plan before
#     resuming.
# 7.  The final "Execute" node runs, confirming which plan it received.
#
# How to Run:
# 1.  Make sure you have a .env file in the same directory with your
#     `GOOGLE_API_KEY`.
# 2.  Run the script from your terminal: `python hitl_prototype.py`
# -----------------------------------------------------------------------------

import os
import json
import uuid
from typing import TypedDict, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# --- 1. Environment and Configuration ---
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please add it.")

# --- 2. Graph State Definition ---
class AgentState(TypedDict):
    """Represents the state of our graph."""
    input: str
    plan: List[dict]
    # We will not use messages for this simple prototype, but it's good practice
    messages: list 

# --- 3. Checkpointer for State Management ---
# Persistence is required for interrupts to work.
memory_saver = MemorySaver()

# --- 4. Node Definitions ---

# This is a simplified version of the prompt from our main project
ARCHITECT_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """
You are an expert project planner. Your job is to create a step-by-step execution plan in JSON format.
Keep the plan simple with 2-3 steps.

**User Request:**
{input}

**Instructions:**
- Decompose the request into a sequence of logical steps.
- Your final output must be a single, valid JSON object containing a "plan" key.
- Do not add any conversational fluff or explanation. Your output must ONLY be the JSON object.

**Example Output:**
```json
{{
  "plan": [
    {{
      "step_id": 1,
      "instruction": "First, do step A."
    }},
    {{
      "step_id": 2,
      "instruction": "Then, do step B."
    }}
  ]
}}
```
---
**Begin!**

**Your Output (must be a single JSON object):**
"""
)

def chief_architect_node(state: AgentState) -> dict:
    """
    The "Chief Architect" - Generates a structured plan using Gemini.
    """
    print("--- 🏛️  CHIEF ARCHITECT ---")
    print("Generating a plan for the user's request...")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    prompt = ARCHITECT_PROMPT_TEMPLATE.format(input=state["input"])
    response = llm.invoke(prompt)
    
    # Extract JSON from the response
    try:
        # A simple regex to find the JSON block, robust to ```json prefixes
        json_match = response.content.split('```json')[-1].split('```')[0].strip()
        parsed_json = json.loads(json_match)
        print("✅ Plan generated successfully.")
        return {"plan": parsed_json.get("plan", [])}
    except Exception as e:
        print(f"❌ Error parsing plan: {e}")
        return {"plan": [{"error": f"Failed to create a valid plan. Response: {response.content}"}]}


def execute_plan_node(state: AgentState) -> None:
    """
    A placeholder node to represent the rest of the agent's execution.
    """
    print("\n--- 🚀 EXECUTION ENGINE ---")
    plan = state.get("plan")
    if plan and "error" not in plan[0]:
        print("✅ Human-in-the-Loop approved. Executing the following plan:")
        print(json.dumps(plan, indent=2))
        print("\nExecution complete.")
    else:
        print("❌ Execution halted due to an invalid or unapproved plan.")
    return {}


# --- 5. Graph Construction ---

# Initialize the state graph
workflow = StateGraph(AgentState)

# Add nodes to the graph
workflow.add_node("chief_architect_node", chief_architect_node)
workflow.add_node("execute_plan_node", execute_plan_node)

# Define the edges
workflow.set_entry_point("chief_architect_node")
workflow.add_edge("chief_architect_node", "execute_plan_node")
workflow.add_edge("execute_plan_node", END)

# --- 6. Compile the Graph with an Interrupt ---
# This is the key step for HITL. We tell the graph to pause *after*
# the specified node has executed.
app = workflow.compile(
    checkpointer=memory_saver,
    interrupt_after=["chief_architect_node"] 
)

# --- 7. Main Execution Logic (Simulating HITL) ---
if __name__ == "__main__":
    print("🚀 Starting HITL Prototype...\n")
    
    # Each conversation should have a unique thread_id
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # The initial request that kicks off the agent
    initial_input = {"input": "Write a brief report on the importance of Human-in-the-Loop for AI safety."}

    # Invoke the graph. It will run and then stop at the interrupt.
    print(f"Submitting request: \"{initial_input['input']}\"")
    app.invoke(initial_input, config=config)

    # --- HUMAN-IN-THE-LOOP INTERACTION ---
    print("\n--- ⏸️  EXECUTION PAUSED: HUMAN-IN-THE-LOOP ---")
    
    # Get the current state of the graph after the interruption
    current_state = app.get_state(config)
    generated_plan = current_state.values.get("plan")
    
    print("\nThe 'Chief Architect' has proposed the following plan:")
    print("--------------------------------------------------")
    print(json.dumps(generated_plan, indent=2))
    print("--------------------------------------------------")
    
    print("\nDo you want to proceed?")
    print("  - Type 'approve' to continue with this plan.")
    print("  - Or, paste a new valid JSON plan to modify it.")
    
    user_feedback = input("\nYour decision: ")

    # --- RESUME OR UPDATE AND RESUME ---
    if user_feedback.strip().lower() == "approve":
        print("\n✅ Plan approved. Resuming execution...")
        # To resume, we invoke the graph again with `None` as the input.
        # This tells LangGraph to continue from the last saved state.
        app.invoke(None, config=config)
    else:

        try:
            # Try to parse the user's input as a new plan
            new_plan = json.loads(user_feedback)
            if "plan" in new_plan and isinstance(new_plan["plan"], list):
                print("\n🔄 Plan modified. Updating state and resuming execution...")
                # First, update the state with the user's new plan
                app.update_state(config, {"plan": new_plan["plan"]})
                # Then, invoke to continue with the updated state
                app.invoke(None, config=config)
            else:
                 raise ValueError("JSON must have a 'plan' key with a list of steps.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"\n❌ Invalid input. Could not parse as JSON plan. Error: {e}")
            print("Execution aborted.")

