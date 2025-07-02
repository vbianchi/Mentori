# backend/langgraph_agent.py
# -----------------------------------------------------------------------------
# ResearchAgent Core Agent (Reverted to Stable Work-Node Version)
#
# This version reverts the graph to the simple, stable state where approving
# a plan leads directly to a single 'work_node'. This is our proven baseline.
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

def work_node(state: GraphState):
    """A placeholder node to represent the entire execution phase."""
    logger.info(f"--- Task '{state.get('task_id')}': Executing simplified 'work_node' ---")
    return {"answer": "The agent has completed the work."}


def editor_node(state: GraphState):
    logger.info(f"Task '{state.get('task_id')}': Reached Editor node for final summary.")
    final_answer = state.get("answer", "The task has concluded.")
    return {"answer": final_answer}

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
        logger.info("--- Final plan approved by user. Starting simplified work process. ---")
        return "start_work"
    else:
        logger.info("--- Final plan rejected by user. Ending task. ---")
        return "end_task"

# --- Graph Definition ---
def create_agent_graph():
    workflow = StateGraph(GraphState)
    
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
    workflow.add_node("work_node", work_node)
    
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

    workflow.add_conditional_edges("human_in_the_loop_final_plan_approval", after_final_plan_approval_router, {
        "start_work": "work_node",
        "end_task": "Editor"
    })
    
    workflow.add_edge("work_node", "Editor")
    workflow.add_edge("Editor", END)
    
    agent = workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=[
            "human_in_the_loop_board_approval",
            "human_in_the_loop_initial_plan_review",
            "human_in_the_loop_final_plan_approval",
        ]
    )
    logger.info("ResearchAgent graph compiled in SIMPLIFIED DEBUG MODE.")
    return agent

agent_graph = create_agent_graph()
