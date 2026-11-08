from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from backend.mcp.decorator import mentori_tool

@mentori_tool(
    category="collaboration",
    agent_role="lead_researcher",
    is_llm_based=False,
)
def ask_user(
    question: str,
    context: str = "",
    options: List[str] = None,
    allow_freeform: bool = True,
) -> str:
    """
    Pause execution and ask the user a question.
    
    This tool should be used when the agent encounters ambiguity, needs a decision,
    or requires user input to proceed. Execution will pause until the user responds.

    Args:
        question: The main question to ask the user
        context: Additional context or background information for the question
        options: Optional list of suggested answers for the user to pick from
        allow_freeform: Whether the user can type a custom answer (default: True)

    Returns:
        User's response (execution pauses until received)
    """
    # This function body is a placeholder. 
    # In the real execution flow, the engine detects this tool call,
    # pauses execution, and waits for a CollaborationResponse via API.
    # The return value here is just what returns if called directly,
    # but the engine intercepts it.
    return "Pending user response..."

@mentori_tool(
    category="collaboration", 
    agent_role="lead_researcher",
    is_llm_based=False
)
def present_plan(
    plan_summary: str,
    steps: List[Dict[str, Any]],
    reasoning: str,
    alternatives: List[str] = None,
) -> Dict[str, Any]:
    """
    Present a plan to the user for approval.
    
    Use this tool before executing a complex plan or after a major replan.
    The user can approve, reject, or modify the plan.

    Args:
        plan_summary: A high-level summary of the plan
        steps: The list of steps proposed
        reasoning: Why this plan was chosen
        alternatives: Alternative approaches considered (optional)

    Returns:
        Dictionary with approval status and feedback
        Ex: {"approved": True} or {"approved": False, "feedback": "Use search instead"}
    """
    return {"status": "pending_approval"}

@mentori_tool(
    category="collaboration", 
    agent_role="lead_researcher",
    is_llm_based=False
)
def share_progress(
    completed_steps: List[str],
    key_findings: List[str],
    remaining_steps: List[str],
    questions_for_user: List[str] = None,
) -> Optional[str]:
    """
    Share a progress update with the user during long tasks.
    
    Use this to keep the user informed after significant milestones or findings.
    The user can optionally provide feedback.

    Args:
        completed_steps: List of steps finished so far
        key_findings: Major findings discovered
        remaining_steps: What is left to do
        questions_for_user: Optional questions to ask alongside the update

    Returns:
        User's optional feedback or additional instructions
    """
    return "Progress shared"

@mentori_tool(
    category="collaboration", 
    agent_role="lead_researcher",
    is_llm_based=False
)
def report_failure(
    step: str,
    attempts: List[Dict[str, Any]],
    error_analysis: str,
    suggestions: List[str],
) -> Dict[str, Any]:
    """
    Report a persistent failure to the user for collaborative resolution.
    
    Use this when a step has failed repeatedly (e.g. after Supervisor retries)
    and you need the user's help to decide what to do next.

    Args:
        step: Description of the step that is failing
        attempts: List of previous attempts details (args, errors)
        error_analysis: Your analysis of why it is failing
        suggestions: Your suggestions for how to proceed (skip, retry, abort, pivot)

    Returns:
        User's decision: {"action": "retry"|"skip"|"replan"|"abort", "user_input": "..."}
    """
    return {"status": "pending_decision"}
