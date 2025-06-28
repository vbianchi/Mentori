# backend/board_of_experts_graph.py
# -----------------------------------------------------------------------------
# Board of Experts (BoE) Track - Phase 2: LLM-Powered Proposals
#
# This version replaces the placeholder logic in the `propose_experts_node`
# with a live LLM call.
#
# Key Architectural Changes:
# 1. Pydantic Models: A `ProposedExpert` model and a `BoardOfExperts` model
#    are defined using Pydantic. This allows us to request structured JSON
#    output from the LLM, ensuring the data is clean and predictable.
# 2. Dynamic Persona Generation: The `propose_experts_node` now uses the
#    `ChatGoogleGenerativeAI` model with the `.with_structured_output()`
#    method. It sends a prompt based on the user's request and parses the
#    LLM's response directly into our Pydantic model.
# 3. State Update: The node now returns a list of `ProposedExpert`
#    dictionaries, which will be used to render the approval card in the UI.
# -----------------------------------------------------------------------------

import logging
from typing import TypedDict, Annotated, List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

# Assuming get_llm is available from the parent context, but for standalone clarity:
from langchain_google_genai import ChatGoogleGenerativeAI
import os


logger = logging.getLogger(__name__)

# --- Pydantic Models for Structured LLM Output ---

class ProposedExpert(BaseModel):
    """A single proposed expert for the advisory board."""
    title: str = Field(description="The expert's job title (e.g., 'Forensic Accountant').")
    qualities: str = Field(description="A brief, one-sentence summary of their key skills and relevance to the task.")

class BoardOfExperts(BaseModel):
    """The full board of proposed experts."""
    experts: List[ProposedExpert] = Field(description="A list of 3-4 diverse, relevant experts for the board.")


# --- State Definition for the BoE Track ---
class BoardOfExpertsState(TypedDict):
    user_request: str
    proposed_experts: List[dict]
    approved_experts: Optional[List[dict]]
    initial_plan: List[dict]
    critiques: Annotated[List[str], lambda x, y: x + y]
    final_plan: List[dict]
    execution_history: Annotated[List[str], lambda x, y: x + y]
    checkpoint_report: Optional[str]
    user_guidance: Optional[str]
    board_decision: Optional[str]

# --- Prompts ---

propose_experts_prompt_template = PromptTemplate.from_template(
"""
You are a master project manager. Based on the user's request, your job is to assemble a small, elite "Board of Experts" to oversee the project.

**User Request:**
{user_request}

**Instructions:**
1.  Analyze the user's request to understand the core domains of expertise required.
2.  Propose a board of 3 to 4 diverse and relevant expert personas.
3.  For each expert, provide a clear title and a concise summary of their essential qualities.
4.  Return the board as a structured JSON object.

**Example:**
*User Request:* "Analyze 'transactions.csv' for financial fraud and write a report."
*Your Output (JSON):*
{{
  "experts": [
    {{
      "title": "Forensic Accountant",
      "qualities": "Experienced in identifying financial anomalies and patterns indicative of corporate fraud."
    }},
    {{
      "title": "Data Scientist",
      "qualities": "Specializes in using machine learning algorithms for anomaly detection in large datasets."
    }}
  ]
}}
"""
)


# --- Graph Nodes ---

def propose_experts_node(state: BoardOfExpertsState):
    """
    This node now uses an LLM to dynamically propose a board of experts
    based on the user's request.
    """
    logger.info("--- (BoE) Executing: propose_experts_node (LLM Call) ---")
    
    # In a real graph, the LLM would be passed in or retrieved from state.
    # For now, we initialize it here for clarity.
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=os.getenv("GOOGLE_API_KEY"))
    structured_llm = llm.with_structured_output(BoardOfExperts)

    prompt = propose_experts_prompt_template.format(user_request=state["user_request"])
    
    try:
        response: BoardOfExperts = structured_llm.invoke(prompt)
        proposed_experts = [expert.dict() for expert in response.experts]
        logger.info(f"LLM proposed {len(proposed_experts)} experts.")
        return {"proposed_experts": proposed_experts}
    except Exception as e:
        logger.error(f"Failed to get structured output for experts: {e}", exc_info=True)
        # Fallback to a default board on failure
        return {"proposed_experts": [{"title": "General Analyst", "qualities": "A default expert due to a generation error."}]}


# --- (Other placeholder nodes remain unchanged for now) ---

def chair_initial_plan_node(state: BoardOfExpertsState):
    logger.info("--- (BoE) Executing Placeholder: chair_initial_plan_node ---")
    plan = [
        {"step": 1, "instruction": "Analyze 'q2_earnings.csv' for anomalies.", "tool": "placeholder_tool"},
        {"step": 2, "instruction": "Checkpoint: Review initial findings.", "tool": "checkpoint"},
        {"step": 3, "instruction": "Generate final PDF report.", "tool": "placeholder_tool"},
    ]
    return {"initial_plan": plan, "final_plan": plan}

def expert_critique_node(state: BoardOfExpertsState):
    logger.info("--- (BoE) Executing Placeholder: expert_critique_node ---")
    critique = "The plan is a good start, but lacks a data scaling step before analysis."
    new_plan = state['final_plan'][:]
    new_step = {"step": "1a", "instruction": "NEW: Scale numerical data.", "tool": "placeholder_tool"}
    new_plan.insert(1, new_step)
    return {"critiques": [critique], "final_plan": new_plan}

def chair_final_review_node(state: BoardOfExpertsState):
    logger.info("--- (BoE) Executing Placeholder: chair_final_review_node ---")
    logger.info(f"Final plan presented with {len(state['final_plan'])} steps.")
    return {}

def company_execution_node(state: BoardOfExpertsState):
    logger.info("--- (BoE) Executing Placeholder: company_execution_node ---")
    return {"execution_history": ["Step 1 completed successfully."]}

def editor_checkpoint_report_node(state: BoardOfExpertsState):
    logger.info("--- (BoE) Executing Placeholder: editor_checkpoint_report_node ---")
    report = "Checkpoint reached. Initial analysis found 15 anomalies. The board must now review."
    return {"checkpoint_report": report}

def board_checkpoint_review_node(state: BoardOfExpertsState):
    logger.info("--- (BoE) Executing Placeholder: board_checkpoint_review_node ---")
    decision = "escalate" 
    logger.info(f"Board has decided to: {decision}")
    return {"board_decision": decision}


# --- Conditional Edges ---

def should_loop_for_critique(state: BoardOfExpertsState) -> str:
    logger.info("--- (BoE) Checking: should_loop_for_critique ---")
    if len(state.get("critiques", [])) < 1:
        return "continue_critique"
    else:
        return "finalize_plan"
        
def after_checkpoint_router(state: BoardOfExpertsState) -> str:
    logger.info("--- (BoE) Checking: after_checkpoint_router ---")
    decision = state.get("board_decision")
    if decision == "adapt":
        return "adapt_plan"
    if decision == "escalate":
        return "request_user_guidance"
    return "continue_execution"


# --- Graph Definition ---

def create_board_of_experts_graph():
    boe_graph = StateGraph(BoardOfExpertsState)
    boe_graph.add_node("propose_experts_node", propose_experts_node)
    boe_graph.add_node("chair_initial_plan_node", chair_initial_plan_node)
    boe_graph.add_node("expert_critique_node", expert_critique_node)
    boe_graph.add_node("chair_final_review_node", chair_final_review_node)
    boe_graph.add_node("company_execution_node", company_execution_node)
    boe_graph.add_node("editor_checkpoint_report_node", editor_checkpoint_report_node)
    boe_graph.add_node("board_checkpoint_review_node", board_checkpoint_review_node)

    boe_graph.set_entry_point("propose_experts_node")
    
    # --- MODIFIED: Interrupt after proposing experts for user approval ---
    # We will configure the interrupt in the main agent graph compilation.
    # For now, the edge just connects to the next step.
    boe_graph.add_edge("propose_experts_node", "chair_initial_plan_node")
    
    boe_graph.add_edge("chair_initial_plan_node", "expert_critique_node")
    
    boe_graph.add_conditional_edges(
        "expert_critique_node",
        should_loop_for_critique,
        {
            "continue_critique": "expert_critique_node",
            "finalize_plan": "chair_final_review_node"
        }
    )
    
    # --- MODIFIED: Interrupt after final plan review for user approval ---
    boe_graph.add_edge("chair_final_review_node", "company_execution_node")

    boe_graph.add_edge("company_execution_node", "editor_checkpoint_report_node")
    boe_graph.add_edge("editor_checkpoint_report_node", "board_checkpoint_review_node")

    boe_graph.add_conditional_edges(
        "board_checkpoint_review_node",
        after_checkpoint_router,
        {
            "adapt_plan": "chair_initial_plan_node", 
            "continue_execution": "company_execution_node",
            "request_user_guidance": END 
        }
    )
    
    logger.info("Board of Experts graph created with LLM-powered proposal node.")
    return boe_graph

