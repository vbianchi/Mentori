# backend/langgraph_agent.py
# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Phase 17 - Compile Argument Fix)
#
# This version fixes a TypeError crash during graph compilation.
#
# Key Architectural Changes:
# 1. COMPILE FIX: The `recursion_limit` keyword argument, which is a runtime
#    setting, has been correctly removed from the `workflow.compile()` call.
#    This resolves the TypeError and allows the application to start.
# -----------------------------------------------------------------------------

import os
import logging
import json
import re
import asyncio
from typing import TypedDict, Annotated, Sequence, List, Optional, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from google.api_core.exceptions import ResourceExhausted
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


from .tools import get_available_tools
from .prompts import (
    router_prompt_template,
    handyman_prompt_template,
    structured_planner_prompt_template,
    controller_prompt_template,
    evaluator_prompt_template,
    final_answer_prompt_template,
    correction_planner_prompt_template,
    summarizer_prompt_template,
    memory_updater_prompt_template
)

# --- Logging Setup ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
HISTORY_SUMMARY_THRESHOLD = 10
HISTORY_SUMMARY_KEEP_RECENT = 4
SANDBOXED_TOOLS = {"write_file", "read_file", "list_files", "workspace_shell", "pip_install", "query_files", "critique_document"}


# --- Data Models ---
class UserProfile(TypedDict, total=False): persona: dict; preferences: dict
class KnowledgeGraphConcept(TypedDict, total=False): id: str; name: str; type: str; properties: dict
class KnowledgeGraphRelationship(TypedDict, total=False): source: str; target: str; label: str
class KnowledgeGraph(TypedDict, total=False): concepts: List[KnowledgeGraphConcept]; relationships: List[KnowledgeGraphRelationship]
class EventOrTask(TypedDict, total=False): description: str; date: str
class WorkspaceFileSummary(TypedDict, total=False): filename: str; summary: str; status: str
class MemoryVault(TypedDict, total=False): user_profile: UserProfile; knowledge_graph: KnowledgeGraph; events_and_tasks: List[EventOrTask]; workspace_summary: List[WorkspaceFileSummary]; key_observations_and_facts: List[str]

class ProposedExpert(BaseModel):
    title: str = Field(description="The expert's job title (e.g., 'Forensic Accountant').")
    qualities: str = Field(description="A brief, one-sentence summary of their key skills and relevance to the task.")

class BoardOfExperts(BaseModel):
    experts: List[ProposedExpert] = Field(description="A list of 3-4 diverse, relevant experts for the board.")

class Step(BaseModel):
    instruction: str = Field(description="The high-level instruction for this step.")
    tool: str = Field(description="The suggested tool for this step (e.g., 'workspace_shell', 'query_files', 'checkpoint').")

class Plan(BaseModel):
    plan: List[Step] = Field(description="A list of steps to accomplish the user's goal.")

class CritiqueAndPlan(BaseModel):
    critique: str = Field(description="The detailed, constructive critique from the expert's point of view. Explain WHY you are making changes.")
    updated_plan: List[Step] = Field(description="The complete, revised step-by-step plan. This should be the full plan, not just the changed parts.")


class GraphState(TypedDict):
    input: str
    task_id: str
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    llm_config: Dict[str, str]
    workspace_path: str
    memory_vault: MemoryVault
    enabled_tools: List[str]
    route: str
    current_track: str
    answer: str
    plan: List[dict]
    current_step_index: int
    current_tool_call: Optional[dict]
    tool_output: Optional[str]
    history: Annotated[List[str], lambda x, y: x + y]
    step_outputs: Annotated[Dict[int, str], lambda x, y: {**x, **y}]
    step_evaluation: Optional[dict]
    max_retries: int
    step_retries: int
    plan_retries: int
    user_feedback: Optional[str]
    proposed_experts: Optional[List[dict]]
    board_approved: Optional[bool]
    approved_experts: Optional[List[dict]]
    initial_plan: Optional[List[dict]]
    expert_critique_index: int
    critiques: Optional[List[dict]]
    refined_plan: Optional[List[dict]]
    strategic_plan: Optional[List[dict]]
    strategic_step_index: int
    tactical_plan: Optional[List[dict]]
    tactical_step_index: int
    execution_history: Optional[List[str]]
    checkpoint_report: Optional[str]
    user_guidance: Optional[str]
    board_decision: Optional[str]

# --- Prompts ---
propose_experts_prompt_template = PromptTemplate.from_template(
"""You are a master project manager. Based on the user's request, your job is to assemble a small, elite "Board of Experts" to oversee the project.
**User Request:**
{user_request}
**Instructions:**
1. Analyze the user's request to understand the core domains of expertise required.
2. Propose a board of 3 to 4 diverse and relevant expert personas.
3. For each expert, provide a clear title and a concise summary of their essential qualities.
4. Return the board as a structured JSON object."""
)

chair_initial_plan_prompt_template = PromptTemplate.from_template(
"""You are the Chair of a Board of Experts. Your role is to create a high-level, strategic plan to address the user's request. You must consider the expertise of your board members.

**User's Request:**
{user_request}

**Your Approved Board of Experts:**
{experts}

**Available Tools:**
{tools}

**Instructions:**
1. Create a step-by-step plan to fulfill the user's request.
2. The plan should be strategic and high-level. The "Company Model" will handle the low-level execution details.
3. Incorporate at least one `checkpoint` step at a logical point for the board to review progress before proceeding.
4. Your output must be a valid JSON object conforming to the "Plan" schema, containing a "plan" key.
"""
)

expert_critique_prompt_template = PromptTemplate.from_template(
"""You are a world-class expert with a specific persona. Your task is to critique a proposed plan and improve it.
**Your Expert Persona:**
{expert_persona}

**The Original User Request:**
{user_request}

**The Current Plan (Draft):**
{current_plan}

**Instructions:**
1.  Review the `Current Plan` from the perspective of your `Expert Persona`.
2.  Identify weaknesses, missing steps, or potential improvements. Can you make it more efficient, robust, or secure?
3.  Provide a concise, constructive `critique` explaining your reasoning.
4.  Create an `updated_plan` that incorporates your suggestions. You MUST return the *entire* plan, not just the changes.
5.  If the plan is already perfect from your perspective, state that in the critique and return the original plan unchanged.
6.  Your final output MUST be a single, valid JSON object that conforms to the `CritiqueAndPlan` schema.
"""
)

chair_final_review_prompt_template = PromptTemplate.from_template(
"""You are the Chair of the Board of Experts. Your team of specialists has finished their sequential review of the initial plan.
Your final responsibility is to perform a sanity check and produce the definitive, final version of the plan for user approval.

**The Original User Request:**
{user_request}

**The Full History of Board Critiques:**
{critiques}

**The Sequentially Refined Plan (after the last expert's review):**
{refined_plan}

**Your Task:**
1.  Review the `Sequentially Refined Plan` and ensure it is coherent and logically sound after all the modifications.
2.  Read through the `Board Critiques` to ensure the spirit of all the experts' suggestions has been incorporated.
3.  **Perform one final check:** Are there any other logical places to insert a `checkpoint`? A checkpoint is wise after a major data analysis step or before a step that generates a critical final output.
4.  Return the final, validated plan. Your output must be a single, valid JSON object conforming to the `Plan` schema.
"""
)

# --- Helper Functions ---
LLM_CACHE = {}
def get_llm(state: GraphState, role_env_var: str, default_llm_id: str):
    run_config = state.get("llm_config", {}); llm_id = run_config.get(role_env_var) or os.getenv(role_env_var, default_llm_id)
    if llm_id in LLM_CACHE: return LLM_CACHE[llm_id]
    provider, model_name = llm_id.split("::"); logger.info(f"Task '{state.get('task_id')}': Initializing LLM for '{role_env_var}': {llm_id}")
    if provider == "gemini": llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif provider == "ollama": llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
    else: raise ValueError(f"Unsupported LLM provider: {provider}")
    LLM_CACHE[llm_id] = llm; return llm

def _invoke_llm_with_fallback(llm, prompt: str, state: GraphState):
    try: return llm.invoke(prompt)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return AIMessage(content=f"Error: {e}")

def format_tools_for_prompt(state: GraphState):
    all_tools = get_available_tools(); enabled_tool_names = state.get("enabled_tools")
    active_tools = [t for t in all_tools if t.name in enabled_tool_names] if enabled_tool_names is not None else all_tools
    tool_strings = [f"  - {t.name}: {t.description}" for t in active_tools]
    return "\n".join(tool_strings) if tool_strings else "No tools are available for this task."

def _format_messages(messages: Sequence[BaseMessage], is_for_summary=False) -> str:
    formatted_messages = []; start_index = 0
    if not is_for_summary:
        first_human_message_index = next((i for i, msg in enumerate(messages) if isinstance(msg, HumanMessage)), -1)
        if first_human_message_index != -1: start_index = first_human_message_index
    for msg in messages[start_index:]:
        role = "System Summary" if isinstance(msg, SystemMessage) else "Human" if isinstance(msg, HumanMessage) else "AI"
        formatted_messages.append(f"{role}: {msg.content}")
    if not is_for_summary: return "\n".join(formatted_messages[:-1]) if len(formatted_messages) > 1 else "No prior conversation history."
    return "\n".join(formatted_messages)

async def _create_venv_if_not_exists(workspace_path: str, task_id: str):
    venv_path = os.path.join(workspace_path, ".venv")
    if not os.path.isdir(venv_path):
        logger.info(f"Task '{task_id}': Creating venv in '{workspace_path}'")
        process = await asyncio.create_subprocess_exec("uv", "venv", cwd=workspace_path)
        await process.wait()

# --- Graph Nodes ---
async def task_setup_node(state: GraphState):
    task_id = state["task_id"]; logger.info(f"Task '{task_id}': Executing Task_Setup and resetting state.")
    workspace_path = f"/app/workspace/{task_id}"; os.makedirs(workspace_path, exist_ok=True); await _create_venv_if_not_exists(workspace_path, task_id)
    return {
        "input": state['messages'][-1].content, "history": [], "current_step_index": 0,
        "step_outputs": {}, "workspace_path": workspace_path, "llm_config": state.get("llm_config", {}),
        "max_retries": 3, "step_retries": 0, "plan_retries": 0, "user_feedback": None,
        "memory_vault": {}, "enabled_tools": state.get("enabled_tools"), "proposed_experts": None,
        "board_approved": None, "approved_experts": None, "initial_plan": None,
        "critiques": [], "refined_plan": None, "strategic_plan": None, "expert_critique_index": 0,
        "execution_history": [], "checkpoint_report": None, "user_guidance": None, "board_decision": None,
        "strategic_step_index": 0, "tactical_plan": None, "tactical_step_index": 0,
    }

def memory_updater_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Executing memory_updater_node.")
    return {}

def summarize_history_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Executing summarize_history_node.")
    return {}

def initial_router_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"Task '{task_id}': Executing Four-Track Router.")
    if "@experts" in state["input"].lower():
        logger.info(f"Task '{task_id}': Routing to Propose_Experts.")
        return {"route": "Propose_Experts", "current_track": "BOARD_OF_EXPERTS_PROJECT"}
    return {"route": "Editor", "current_track": "DIRECT_QA"}

def propose_experts_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing propose_experts_node ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest")
    structured_llm = llm.with_structured_output(BoardOfExperts)
    prompt = propose_experts_prompt_template.format(user_request=state["input"])
    try:
        response = structured_llm.invoke(prompt)
        return {"proposed_experts": [expert.dict() for expert in response.experts]}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to propose experts: {e}")
        return {"proposed_experts": [{"title": "Error", "qualities": "Failed to generate."}]}

def human_in_the_loop_board_approval(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for Board of Experts Approval ---")
    return {}

def chair_initial_plan_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing chair_initial_plan_node ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest")
    structured_llm = llm.with_structured_output(Plan)
    prompt = chair_initial_plan_prompt_template.format(user_request=state["input"], experts=json.dumps(state.get("approved_experts"), indent=2), tools=format_tools_for_prompt(state))
    try:
        response = structured_llm.invoke(prompt)
        plan_steps = [step.dict() for step in response.plan]
        logger.info(f"Chair created an initial plan with {len(plan_steps)} steps.")
        return {"initial_plan": plan_steps, "refined_plan": plan_steps}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to create initial plan: {e}")
        return {"initial_plan": [{"instruction": "Error: Failed to generate a plan.", "tool": "error"}]}

def human_in_the_loop_initial_plan_review(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for Initial Plan Review ---")
    return {}

def expert_critique_node(state: GraphState):
    task_id = state.get("task_id")
    critique_index = state["expert_critique_index"]
    expert = state["approved_experts"][critique_index]
    logger.info(f"--- (BoE) Task '{task_id}': Executing expert_critique_node for '{expert['title']}' ({critique_index + 1}/{len(state['approved_experts'])}) ---")

    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest")
    structured_llm = llm.with_structured_output(CritiqueAndPlan)
    
    prompt = expert_critique_prompt_template.format(
        expert_persona=json.dumps(expert, indent=2),
        user_request=state["input"],
        current_plan=json.dumps(state["refined_plan"], indent=2)
    )

    try:
        response = structured_llm.invoke(prompt)
        updated_plan_steps = [step.dict() for step in response.updated_plan]
        critique_with_context = {
            "title": expert["title"],
            "critique": response.critique,
            "plan_after_critique": updated_plan_steps
        }

        logger.info(f"Critique from '{expert['title']}': {response.critique[:100]}...")
        current_critiques = state.get("critiques", [])
        return {
            "critiques": current_critiques + [critique_with_context],
            "refined_plan": updated_plan_steps,
            "expert_critique_index": critique_index + 1
        }
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed to get critique from '{expert['title']}': {e}")
        error_critique = { "title": expert["title"], "critique": f"Error: Could not generate a critique. {e}", "plan_after_critique": state["refined_plan"] }
        current_critiques = state.get("critiques", [])
        return {"critiques": current_critiques + [error_critique], "expert_critique_index": critique_index + 1}

def chair_final_review_node(state: GraphState):
    task_id = state.get("task_id"); logger.info(f"--- (BoE) Task '{task_id}': Executing chair_final_review_node (Synthesis) ---")
    llm = get_llm(state, "CHIEF_ARCHITECT_LLM_ID", "gemini::gemini-1.5-pro-latest")
    structured_llm = llm.with_structured_output(Plan)

    critique_texts = [f"Critique from {c['title']}:\n{c['critique']}" for c in state['critiques']]

    prompt = chair_final_review_prompt_template.format(
        user_request=state["input"],
        critiques="\n\n".join(critique_texts),
        refined_plan=json.dumps(state['refined_plan'], indent=2)
    )
    
    try:
        response = structured_llm.invoke(prompt)
        final_plan_steps = [step.dict() for step in response.plan]
        logger.info(f"Chair synthesized a final plan with {len(final_plan_steps)} steps.")
        return {"strategic_plan": final_plan_steps}
    except Exception as e:
        logger.error(f"Task '{task_id}': Failed during Chair's final synthesis: {e}")
        return {"strategic_plan": state["refined_plan"]}

def human_in_the_loop_final_plan_approval(state: GraphState):
    logger.info(f"--- Task '{state.get('task_id')}': Paused for Final Plan Approval ---")
    return {}

# --- Placeholder Execution Nodes ---
def chief_architect_node(state: GraphState):
    task_id = state.get("task_id")
    strategic_step = state["strategic_plan"][state["strategic_step_index"]]
    logger.info(f"--- (EXEC) Task '{task_id}': Chief Architect expanding strategic step: '{strategic_step['instruction']}' ---")
    
    fake_tactical_plan = [
        {"tool": "placeholder_tool_1", "instruction": f"Do first tactical thing for '{strategic_step['instruction']}'"},
        {"tool": "placeholder_tool_2", "instruction": "Do second tactical thing"}
    ]
    return {"tactical_plan": fake_tactical_plan, "tactical_step_index": 0}

def site_foreman_node(state: GraphState):
    task_id = state.get("task_id")
    tactical_step = state["tactical_plan"][state["tactical_step_index"]]
    logger.info(f"--- (EXEC) Task '{task_id}': Site Foreman preparing tactical step: '{tactical_step['instruction']}' ---")
    return {"current_tool_call": tactical_step}

def worker_node(state: GraphState):
    task_id = state.get("task_id")
    tool_call = state["current_tool_call"]
    logger.info(f"--- (EXEC) Task '{task_id}': Worker executing tool: '{tool_call['tool']}' ---")
    return {"tool_output": f"Placeholder success from tool '{tool_call['tool']}'"}

def project_supervisor_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"--- (EXEC) Task '{task_id}': Project Supervisor evaluating last step's output ---")
    return {"step_evaluation": {"status": "success", "reasoning": "Placeholder evaluation: The step was successful."}}

def editor_checkpoint_report_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"--- (EXEC) Task '{task_id}': Editor compiling checkpoint report ---")
    return {"checkpoint_report": "Checkpoint report: All preceding steps completed successfully."}

def board_checkpoint_review_node(state: GraphState):
    task_id = state.get("task_id")
    logger.info(f"--- (EXEC) Task '{task_id}': Board reviewing checkpoint report ---")
    return {"board_decision": "continue"}

def handyman_node(state: GraphState): 
    logger.info(f"Task '{state.get('task_id')}': Track 2 -> Handyman (Placeholder)")
    return {}
    
def human_in_the_loop_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Paused for Architect Plan Approval")
    return {}

def editor_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Reached Editor node for final summary.")
    return {"answer": "The agent has successfully completed all steps of the strategic plan."}

# --- Conditional Routers ---
def after_board_approval_router(state: GraphState) -> str:
    logger.info(f"--- (BoE) Checking user approval for the board ---")
    if state.get("board_approved"):
        logger.info("Board approved. Proceeding to set experts.")
        return "set_approved_experts"
    else:
        logger.info("Board rejected. Routing to Editor.")
        return "Editor"

def set_approved_experts_node(state: GraphState) -> dict:
    logger.info(f"--- (BoE) Caching approved experts in state ---")
    return {"approved_experts": state.get("proposed_experts")}

def should_continue_critique(state: GraphState) -> str:
    logger.info("--- (BoE) Checking: should_continue_critique ---")
    if state["expert_critique_index"] < len(state["approved_experts"]):
        logger.info("More experts to critique. Looping back.")
        return "continue_critique"
    else:
        logger.info("All experts have provided critiques. Finalizing plan.")
        return "finalize_plan"

def route_logic(state: GraphState) -> str: return state.get("route", "Editor")

def after_final_plan_approval_router(state: GraphState) -> str:
    if state.get("user_feedback") == 'approve':
        logger.info("--- Final plan approved by user. Starting main execution loop. ---")
        return "start_execution"
    else:
        logger.info("--- Final plan rejected by user. Ending task. ---")
        return "end_task"

def master_router_logic(state: GraphState) -> str:
    logger.info("--- (EXEC) Master Router deciding next strategic action ---")
    if state["strategic_step_index"] < len(state["strategic_plan"]):
        current_strategic_step = state["strategic_plan"][state["strategic_step_index"]]
        if current_strategic_step.get("tool") == "checkpoint":
             logger.info("--- (EXEC) Master Router: Strategic step is a checkpoint. Routing to review. ---")
             return "checkpoint_review"
        else:
            logger.info("--- (EXEC) Master Router: More strategic steps remain. Routing to Chief Architect. ---")
            return "continue_execution"
    else:
        logger.info("--- (EXEC) Master Router: All strategic steps are complete. Routing to Editor. ---")
        return "all_steps_complete"

def master_router_node(state: GraphState) -> dict:
    return {}

def tactical_step_router_logic(state: GraphState) -> str:
    logger.info("--- (EXEC) Tactical Router deciding next tactical action ---")
    if state["tactical_step_index"] < len(state["tactical_plan"]):
        logger.info("--- (EXEC) Tactical Router: More tactical steps remain. Continuing. ---")
        return "continue_tactical_plan"
    else:
        logger.info("--- (EXEC) Tactical Router: Tactical plan complete. Returning to Master Router. ---")
        return "tactical_plan_complete"

def tactical_step_router_node(state: GraphState) -> dict:
    return {}


def after_checkpoint_review_router(state: GraphState) -> str:
    logger.info("--- (EXEC) Checkpoint review complete. Returning to Master Router. ---")
    return "continue_strategic_plan"

def increment_strategic_step_node(state: GraphState) -> dict:
    logger.info("--- (EXEC) Incrementing strategic step index. ---")
    return {"strategic_step_index": state["strategic_step_index"] + 1}

def tactical_step_incrementer(state: GraphState) -> dict:
    logger.info("--- (EXEC) Incrementing tactical step index. ---")
    return {"tactical_step_index": state["tactical_step_index"] + 1}

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    
    # Original Nodes
    workflow.add_node("Task_Setup", task_setup_node)
    workflow.add_node("Memory_Updater", memory_updater_node)
    workflow.add_node("initial_router_node", initial_router_node)
    workflow.add_node("Editor", editor_node)
    workflow.add_node("Propose_Experts", propose_experts_node)
    workflow.add_node("human_in_the_loop_board_approval", human_in_the_loop_board_approval)
    workflow.add_node("set_approved_experts_node", set_approved_experts_node)
    workflow.add_node("chair_initial_plan_node", chair_initial_plan_node)
    workflow.add_node("human_in_the_loop_initial_plan_review", human_in_the_loop_initial_plan_review)
    workflow.add_node("expert_critique_node", expert_critique_node)
    workflow.add_node("chair_final_review_node", chair_final_review_node)
    workflow.add_node("human_in_the_loop_final_plan_approval", human_in_the_loop_final_plan_approval)
    
    # New Placeholder Execution Nodes
    workflow.add_node("master_router", master_router_node)
    workflow.add_node("chief_architect_node", chief_architect_node)
    workflow.add_node("site_foreman_node", site_foreman_node)
    workflow.add_node("worker_node", worker_node)
    workflow.add_node("project_supervisor_node", project_supervisor_node)
    workflow.add_node("tactical_step_router", tactical_step_router_node)
    workflow.add_node("tactical_step_incrementer", tactical_step_incrementer)
    workflow.add_node("increment_strategic_step_node", increment_strategic_step_node)
    workflow.add_node("editor_checkpoint_report_node", editor_checkpoint_report_node)
    workflow.add_node("board_checkpoint_review_node", board_checkpoint_review_node)
    
    # --- Graph Wiring ---
    
    # Entry and BoE Flow
    workflow.set_entry_point("Task_Setup")
    workflow.add_edge("Task_Setup", "Memory_Updater")
    workflow.add_edge("Memory_Updater", "initial_router_node")
    workflow.add_conditional_edges("initial_router_node", route_logic, { "Editor": "Editor", "Propose_Experts": "Propose_Experts" })
    workflow.add_edge("Propose_Experts", "human_in_the_loop_board_approval")
    workflow.add_conditional_edges("human_in_the_loop_board_approval", after_board_approval_router, { "set_approved_experts": "set_approved_experts_node", "Editor": "Editor" })
    workflow.add_edge("set_approved_experts_node", "chair_initial_plan_node")
    workflow.add_edge("chair_initial_plan_node", "human_in_the_loop_initial_plan_review")
    workflow.add_edge("human_in_the_loop_initial_plan_review", "expert_critique_node")
    workflow.add_conditional_edges("expert_critique_node", should_continue_critique, { "continue_critique": "expert_critique_node", "finalize_plan": "chair_final_review_node" })
    workflow.add_edge("chair_final_review_node", "human_in_the_loop_final_plan_approval")

    # Execution Flow
    workflow.add_conditional_edges("human_in_the_loop_final_plan_approval", after_final_plan_approval_router, {
        "start_execution": "master_router",
        "end_task": "Editor"
    })
    
    workflow.add_conditional_edges( "master_router", master_router_logic, {
            "continue_execution": "chief_architect_node",
            "checkpoint_review": "editor_checkpoint_report_node",
            "all_steps_complete": "Editor"
        }
    )

    workflow.add_edge("chief_architect_node", "site_foreman_node")
    workflow.add_edge("site_foreman_node", "worker_node")
    workflow.add_edge("worker_node", "project_supervisor_node")
    workflow.add_edge("project_supervisor_node", "tactical_step_incrementer")
    workflow.add_edge("tactical_step_incrementer", "tactical_step_router")

    workflow.add_conditional_edges("tactical_step_router", tactical_step_router_logic, {
        "continue_tactical_plan": "site_foreman_node",
        "tactical_plan_complete": "increment_strategic_step_node"
    })
    
    workflow.add_edge("increment_strategic_step_node", "master_router")

    # Checkpoint Review Loop
    workflow.add_edge("editor_checkpoint_report_node", "board_checkpoint_review_node")
    workflow.add_conditional_edges("board_checkpoint_review_node", after_checkpoint_review_router, {
        "continue_strategic_plan": "increment_strategic_step_node"
    })

    workflow.add_edge("Editor", END)
    
    agent = workflow.compile(
        checkpointer=MemorySaver(),
        # --- MODIFIED: Removed invalid argument ---
        interrupt_before=[
            "human_in_the_loop_board_approval",
            "human_in_the_loop_initial_plan_review",
            "human_in_the_loop_final_plan_approval",
        ]
    )
    logger.info("ResearchAgent graph compiled with compile fix.")
    return agent

agent_graph = create_agent_graph()
