"""
Data schemas for the Orchestrator system.

These dataclasses define the structure of plans, steps, and state
used throughout the orchestration process.

"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid
import json
import asyncio

# Mentori's counts, kept and stated in Methods (limits.md #134 to #136 and F11; Figure 4): a step whose supervisor
# score is below 70 is retried while it has had fewer than MAX_STEP_RETRIES retries (engine.py, supervisor.py), and
# MAX_CONSECUTIVE_FAILURES escalations in a row end execution (OrchestratorState.max_failures). Synthesis still runs
# after that, and the answer records plan_status "failed".
MAX_STEP_RETRIES = 3
MAX_CONSECUTIVE_FAILURES = 3

# D52 (Figure 4) and D75 (Q82 to Q87): the orchestrator switches a set-up may set (SessionContext.orchestrator_switches).
# A key left out is Mentori as built, the first value of its row. Meanings (engine.py, executor.py):
#   analyser     "off": no analyser call; every question goes to the planner and the tools (Q83 a).
#                "factual_to_documents": the analyser runs with ANALYZER_FACTUAL_TO_DOCUMENTS (prompts.py), whose
#                direct-answer list keeps only greetings, meta questions and clarifications (Q87 b)
#   planner      "off": no planner call; a fixed one-step plan, smart_query(query=the question, index_name=the session's
#                index) by the editor role, at smart_query's default mode "auto" (Q84 a)
#   supervisor   "off": no evaluation, no micro-adjustment, no retry; each step runs once and the plan moves on. The
#                text pre-check's verdict is recorded and not acted on (Q85 a)
#   synthesiser  "off": no synthesis call; the answer is format_steps_with_results, the text synthesis would have read
#                (each step's last attempt, its content as stored, in plan order) (Q86 b)
#   distiller    "off": no step output is distilled; "F1": exp_04b's prompt F1 (D52)
#   distiller_trigger  "every_step": the distiller runs on every non-empty step output, not only above Mentori's
#                threshold; a stress condition, not Mentori's default (Q82)
ORCHESTRATOR_SWITCHES: Dict[str, tuple] = {
    "analyser": ("on", "off", "factual_to_documents"),
    "planner": ("on", "off"),
    "supervisor": ("on", "off"),
    "synthesiser": ("on", "off"),
    "distiller": ("on", "off", "F1"),
    "distiller_trigger": ("threshold", "every_step"),
}


class SwitchError(ValueError):
    """A set-up names an orchestrator switch or value that ORCHESTRATOR_SWITCHES does not define."""


def resolve_switches(switches: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Every switch with its value for this set-up (Mentori's for a key left out). An unknown key or value raises
    SwitchError: a set-up that misnames a switch would otherwise run as Mentori as built under another name."""
    switches = dict(switches or {})
    unknown = sorted(k for k in switches if k not in ORCHESTRATOR_SWITCHES)
    if unknown:
        raise SwitchError(f"unknown orchestrator switch {unknown}; defined: {sorted(ORCHESTRATOR_SWITCHES)}")
    for key, value in switches.items():
        if value not in ORCHESTRATOR_SWITCHES[key]:
            raise SwitchError(f"orchestrator switch {key}={value!r}; its values are {ORCHESTRATOR_SWITCHES[key]}")
    return {key: switches.get(key, values[0]) for key, values in ORCHESTRATOR_SWITCHES.items()}

class PlanStatus(Enum):
    """Status of the overall execution plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_USER = "awaiting_user"


class StepStatus(Enum):
    """Status of individual plan steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """
    A single step in the execution plan.

    Each step represents one tool call to be executed by a specific agent.
    """
    step_id: str                              # "step_1", "step_2", etc.
    description: str                          # Human-readable description
    agent_role: str                           # "handyman", "coder", "vision", "editor"
    tool_name: str                            # Specific tool to call
    tool_args: Dict[str, Any]                 # Arguments for the tool
    expected_output: str                      # What we expect to get back
    reasoning: str                            # Why this step is needed

    # Runtime fields (set during execution)
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None              # Tool result
    error: Optional[str] = None               # Error message if failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0                      # Number of retry attempts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "agent_role": self.agent_role,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "expected_output": self.expected_output,
            "reasoning": self.reasoning,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        """Create PlanStep from dictionary."""
        return cls(
            step_id=data["step_id"],
            description=data["description"],
            agent_role=data["agent_role"],
            tool_name=data["tool_name"],
            tool_args=data.get("tool_args", {}),
            expected_output=data.get("expected_output", ""),
            reasoning=data.get("reasoning", ""),
            status=StepStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class ExecutionPlan:
    """
    The complete execution plan generated by the orchestrator.

    Contains the goal, reasoning, and ordered list of steps to execute.
    """
    plan_id: str                              # UUID
    goal: str                                 # What we're trying to achieve
    steps: List[PlanStep]                     # Ordered steps to execute
    reasoning: str                            # Orchestrator's reasoning for this plan

    # Metadata
    status: PlanStatus = PlanStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    requires_confirmation: bool = False       # True if high-risk operations

    # Runtime tracking
    current_step_index: int = 0
    replan_count: int = 0                     # How many times we've replanned

    # How the plan came to be (limits.md Class X, planner.py): "ok", "error" (the planner's call failed, Mentori's
    # empty plan follows) or "unparsed" (no JSON plan in the reply, Mentori's empty plan follows); with the error
    generation_status: str = "ok"
    generation_error: Optional[str] = None

    def current_step(self) -> Optional[PlanStep]:
        """Get the current step to execute."""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self) -> bool:
        """Move to next step. Returns False if no more steps."""
        self.current_step_index += 1
        return self.current_step_index < len(self.steps)

    def is_complete(self) -> bool:
        """Check if all steps are done."""
        return self.current_step_index >= len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "reasoning": self.reasoning,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "requires_confirmation": self.requires_confirmation,
            "current_step_index": self.current_step_index,
            "replan_count": self.replan_count,
            "generation_status": self.generation_status,
            "generation_error": self.generation_error,
        }

    def to_markdown(self) -> str:
        """Convert plan to human-readable markdown."""
        lines = [
            f"**Goal:** {self.goal}",
            "",
            "**Steps:**",
        ]
        for i, step in enumerate(self.steps, 1):
            status_icon = {
                StepStatus.PENDING: "⏳",
                StepStatus.IN_PROGRESS: "🔄",
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️",
            }.get(step.status, "")
            lines.append(f"{i}. {status_icon} **{step.description}**")
            lines.append(f"   - Agent: `{step.agent_role}` → Tool: `{step.tool_name}`")
        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPlan":
        """Create ExecutionPlan from dictionary (e.g., from LLM JSON output)."""
        steps = [PlanStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            plan_id=data.get("plan_id", str(uuid.uuid4())),
            goal=data.get("goal", ""),
            steps=steps,
            reasoning=data.get("reasoning", ""),
            status=PlanStatus(data.get("status", "pending")),
            requires_confirmation=data.get("requires_confirmation", False),
        )


@dataclass
class AnalysisResult:
    """
    Result of the query analysis phase (Phase 0).

    Determines whether to answer directly or create a plan.
    """
    decision: str                             # "direct_answer" or "needs_plan"
    reasoning: str                            # Why this decision was made
    complexity: str                           # "trivial", "simple", "moderate", "complex"
    thinking: str = ""                        # Full thinking content for audit trail
    # limits.md Class X (planner.py): "ok", "error" (the call failed; Mentori then plans) or "unparsed" (no JSON;
    # Mentori then guesses the decision from the reply's text), with the error
    status: str = "ok"
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], thinking: str = "") -> "AnalysisResult":
        """Create from LLM JSON output."""
        return cls(
            decision=data.get("decision", "needs_plan"),
            reasoning=data.get("reasoning", ""),
            complexity=data.get("complexity", "simple"),
            thinking=thinking,
        )


@dataclass
class ToolObservation:
    """
    Structured representation of a tool's output — P1-E-2 Context Engineering.

    Separates the compact context-window version (summary + key_findings) from
    the full raw output, which is preserved for UI display and audit trail but
    NOT injected into subsequent LLM context.

    Fields:
        summary: ≤400-word distilled version injected into the context window
        key_findings: Bullet points extracted from the observation
        citations: Source filenames / page numbers mentioned in the output
        confidence: Tool-reported confidence (0.0–1.0) if available
        raw_saved_to: Path or event key where the full raw output can be found
        raw_content: Full original tool output (not injected into context)
    """
    summary: str
    key_findings: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    raw_saved_to: Optional[str] = None       # e.g. "tool_result event" or workspace path
    raw_content: Optional[str] = None

    def to_context_string(self) -> str:
        """Return the compact string to inject into the LLM context window."""
        parts = [self.summary]
        if self.key_findings:
            parts.append("\nKey findings:")
            parts.extend(f"  - {f}" for f in self.key_findings)
        if self.citations:
            parts.append("\nSources: " + "; ".join(self.citations))
        return "\n".join(parts)


@dataclass
class StepResult:
    """
    Result of executing a single plan step.

    Captures the tool output, agent thinking, and success status.

    Context engineering note (P1-E-2):
      `content` holds the distilled observation (≤2 000 chars) injected into
      subsequent LLM context.  `raw_content` holds the full original output
      for UI display only — it is NOT re-injected into context windows.
    """
    step_id: str
    success: bool
    content: str                              # Distilled tool result (context window)
    summary: str                              # Agent's summary of the result
    agent_thinking: str = ""                  # Agent's thinking during execution
    error: Optional[str] = None               # Error message if failed
    token_usage: Optional[Dict[str, int]] = None  # Token usage from tool
    raw_content: Optional[str] = None         # Full original tool output (UI only)

    # The step's record (records.md F14, F15; A6, D37; Q23, Q25, Q39), filled by the executor and the engine
    attempt_no: int = 1                       # 1 for a step's first run, 2 after the supervisor's first retry, ...
    tool_args: Optional[Dict[str, Any]] = None  # the arguments the plan gave, after {{step_N.result}} resolution
    injected: List[str] = field(default_factory=list)   # names of the session values injected (never their values)
    is_error: bool = False                    # the MCP result's isError (a tool exception, Q39)
    distilled: bool = False                   # content is the distiller's output, not the tool's
    distill: Optional[Dict[str, Any]] = None  # the distiller's outcome when it was asked (observation_distiller)
    routing: Optional[Dict[str, Any]] = None  # smart_query's route (rag_tools.py, limits.md #34/#110)
    passage_ids: List[str] = field(default_factory=list)   # passages the tool output carries whole (query_documents)
    retrievals: List[Dict[str, Any]] = field(default_factory=list)   # the retrieve() records made inside the tool
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)   # the model calls made inside the tool (Q39)
    executions: List[Dict[str, Any]] = field(default_factory=list)   # a coder step: each execute_python run (code,
                                                                     # is_error, whole output; coder.py)
    # Q90 (D75): the role whose model the step was looked up under; "default" when the plan named a role the run does
    # not know (the role as written stays in the step's agent_role)
    agent_role_used: Optional[str] = None
    # Q91 (D75): Mentori's soft-failure check (executor._detect_error_in_result) decides success and is kept; beside it,
    # the truth: tool_error_text, the tool's text starts with "[Error]" (after smart_query's "**Strategy**" prefix);
    # short_phrase_fired, the check's short-phrase pattern decided the label; error_check_pattern, which pattern of the
    # check fired ("prefix", "http", "short_phrase", "near_empty"), None when none did
    tool_error_text: bool = False
    short_phrase_fired: bool = False
    error_check_pattern: Optional[str] = None
    # Q82 (D75): the step's output passed Mentori's distiller threshold (209,712 characters), whatever the switch
    over_distill_threshold: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage. Carries what later phases read: content (never raw_content), the
        attempt, and which passages the content holds whole (for run_records.passages_carried)."""
        return {
            "step_id": self.step_id,
            "success": self.success,
            "content": self.content,
            "summary": self.summary,
            "agent_thinking": self.agent_thinking,
            "error": self.error,
            "token_usage": self.token_usage,
            # raw_content intentionally omitted — not needed in serialized state
            "attempt_no": self.attempt_no,
            "distilled": self.distilled,
            "passage_ids": list(self.passage_ids),
        }

    def to_record(self) -> Dict[str, Any]:
        """The step attempt as the answer's record stores it (records.md F14): the whole tool output and what later
        phases read, with the tool, its arguments, its routing and the model calls made inside it. The display
        summary is left out (Q24: no prompt reads it)."""
        return {
            "step_id": self.step_id,
            "attempt_no": self.attempt_no,
            "success": self.success,
            "error": self.error,
            "is_error": self.is_error,
            "tool_args": self.tool_args,
            "injected": list(self.injected),
            "routing": self.routing,
            "raw_content": self.raw_content,
            "content": self.content,
            "distilled": self.distilled,
            "distill": self.distill,
            # Q25 (D68): the distiller was asked and failed or returned nothing, so content is the whole tool output
            "distill_failed": bool(self.distill and self.distill.get("status") in ("failed", "empty")),
            "passage_ids": list(self.passage_ids),
            "retrievals": list(self.retrievals),
            "tool_calls": list(self.tool_calls),
            "executions": list(self.executions),
            # D89 (Q145 O2), D90, LIST.md Rule 10: a Gemini empty or blocked reply returns to the step as empty
            # text, a recitation, malformed_function_call or malformed_response reply with the text it held
            # (lock_adapter._finish, _returned); each counts here as a failed call (Figure 4 is exp_03's)
            "failed_tool_calls": sum(1 for c in self.tool_calls
                                     if c.get("status") not in ("ok", "length")),
            "token_usage": self.token_usage,
            "agent_role_used": self.agent_role_used,
            "tool_error_text": self.tool_error_text,
            "short_phrase_fired": self.short_phrase_fired,
            "error_check_pattern": self.error_check_pattern,
            "over_distill_threshold": self.over_distill_threshold,
        }


@dataclass
class EvaluationResult:
    """
    Result of the orchestrator's evaluation of a step result.

    Determines whether to continue, retry, or fail.
    """
    success: bool                             # Did the step achieve its goal?
    summary: str                              # Brief summary of outcome
    should_continue: bool                     # Should we proceed to next step?
    reasoning: str                            # Why this decision was made
    issues: List[str] = field(default_factory=list)  # Any issues found
    thinking: str = ""                        # Full thinking for audit trail

    @classmethod
    def from_dict(cls, data: Dict[str, Any], thinking: str = "") -> "EvaluationResult":
        """Create from LLM JSON output."""
        return cls(
            success=data.get("success", False),
            summary=data.get("summary", ""),
            should_continue=data.get("should_continue", False),
            reasoning=data.get("reasoning", ""),
            issues=data.get("issues", []),
            thinking=thinking,
        )


@dataclass
class OrchestratorState:
    """
    Complete state of the orchestration process.

    This is the single source of truth for the entire execution.
    Tracks all phases, results, and history.
    """
    # Identity
    task_id: str
    user_query: str

    # Plan (set after planning phase)
    plan: Optional[ExecutionPlan] = None

    # Execution tracking
    phase: str = "analyzing"                  # "analyzing", "planning", "executing", "synthesizing", "complete", "error", "awaiting_user"
    step_results: List[Dict[str, Any]] = field(default_factory=list)

    # Context accumulation
    orchestrator_messages: List[Dict[str, str]] = field(default_factory=list)

    # Error recovery tracking
    consecutive_failures: int = 0
    max_failures: int = MAX_CONSECUTIVE_FAILURES

    # User interaction
    pending_question: Optional[str] = None
    pending_collaboration: Optional[Dict[str, Any]] = None  # {tool, args, ...}
    collaboration_response: Optional[Any] = None

    # Final output
    final_answer: Optional[str] = None

    # Token tracking
    total_tokens: int = 0

    # Supervisor tracking (Phase 2A)
    steps_since_reflection: int = 0           # Steps completed since last reflection
    consecutive_low_quality: int = 0          # Consecutive steps with quality < threshold
    same_tool_streak: int = 0                 # Consecutive calls to same tool
    last_tool_name: Optional[str] = None      # Last tool called (for streak tracking)

    def add_step_result(self, result: StepResult) -> None:
        """Add a step result and track tokens."""
        self.step_results.append(result.to_dict())
        if result.token_usage:
            self.total_tokens += result.token_usage.get("total", 0)

    def get_step_result(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific step result by ID."""
        for result in self.step_results:
            if result.get("step_id") == step_id:
                return result
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for debugging/logging."""
        return {
            "task_id": self.task_id,
            "user_query": self.user_query,
            "phase": self.phase,
            "plan": self.plan.to_dict() if self.plan else None,
            "step_results": self.step_results,
            "consecutive_failures": self.consecutive_failures,
            "pending_question": self.pending_question,
            "pending_collaboration": self.pending_collaboration,
            "final_answer_length": len(self.final_answer) if self.final_answer else 0,
            "total_tokens": self.total_tokens,
            "steps_since_reflection": self.steps_since_reflection,
            "consecutive_low_quality": self.consecutive_low_quality,
            "same_tool_streak": self.same_tool_streak,
        }


# =============================================================================
# Phase 2A: Supervisor Agent Schemas
# =============================================================================

@dataclass
class SupervisorEvaluation:
    """
    Result of the Supervisor Agent's quality evaluation of a step result.

    The Supervisor goes beyond pass/fail to assess:
    - Quality: Is this result actually useful?
    - Goal alignment: Does this advance us toward the objective?
    - Issues: What problems were identified?
    - Action: Should we retry, continue, or escalate?
    """
    quality_score: int                        # 0-100 quality assessment
    issues: List[str]                         # Problems identified
    suggestion: Optional[str]                 # Micro-adjustment suggestion if quality < threshold
    should_retry: bool                        # Should we retry this step?
    should_escalate: bool                     # Should we escalate to user? (Phase 2B)
    reasoning: str                            # Explanation for the user
    thinking: str = ""                        # Full thinking for audit trail
    # Where quality_score came from (limits.md Class X, supervisor.py; A5): "ok" (the supervisor's JSON), "heuristic"
    # (Mentori's pre-check, no model call), "error" (the call failed) or "unparsed" (no JSON, or no quality_score in
    # it). For "error" and "unparsed" quality_score is the value Mentori's control flow uses (50, 60, or from_dict's
    # 50); the record reports it as control_score and quality_score None, so it is never read as the model's score.
    status: str = "ok"
    error: Optional[str] = None

    # Quality thresholds
    QUALITY_THRESHOLD_GOOD: int = 70          # Above this = proceed
    QUALITY_THRESHOLD_ACCEPTABLE: int = 50    # Above this = maybe retry
    # Below ACCEPTABLE = definitely retry or escalate

    def is_good_quality(self) -> bool:
        """Check if quality is good enough to proceed without retry."""
        return self.quality_score >= self.QUALITY_THRESHOLD_GOOD

    def is_acceptable_quality(self) -> bool:
        """Check if quality is acceptable (might proceed with caveats)."""
        return self.quality_score >= self.QUALITY_THRESHOLD_ACCEPTABLE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization. quality_score is the model's (or the pre-check's) score,
        None when the evaluation failed or was unparsed; control_score is the value the control flow used."""
        return {
            "quality_score": self.quality_score if self.status in ("ok", "heuristic") else None,
            "control_score": self.quality_score,
            "status": self.status,
            "error": self.error,
            "issues": self.issues,
            "suggestion": self.suggestion,
            "should_retry": self.should_retry,
            "should_escalate": self.should_escalate,
            "reasoning": self.reasoning,
            "thinking": self.thinking,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], thinking: str = "") -> "SupervisorEvaluation":
        """Create from LLM JSON output."""
        return cls(
            quality_score=data.get("quality_score", 50),
            issues=data.get("issues", []),
            suggestion=data.get("suggestion"),
            should_retry=data.get("should_retry", False),
            should_escalate=data.get("should_escalate", False),
            reasoning=data.get("reasoning", ""),
            thinking=thinking,
        )


@dataclass
class MicroAdjustment:
    """
    A small adjustment to step parameters suggested by the Supervisor.

    Micro-adjustments are tried before escalating to full replan or user intervention.
    Examples:
    - Broaden/narrow search query
    - Try different index
    - Increase result limit
    - Change tool parameters
    """
    original_args: Dict[str, Any]             # Original tool arguments
    adjusted_args: Dict[str, Any]             # Adjusted tool arguments
    adjustment_reasoning: str                 # Why this adjustment might help
    attempt_number: int                       # Which retry attempt this is (1, 2, or 3)
    adjustment_type: str = "parameter_tweak"  # Type: "parameter_tweak", "query_broadening", "fallback_tool"
    # limits.md Class X: "ok", "error" (the call failed) or "unparsed"; Mentori then retries with the same arguments
    status: str = "ok"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "original_args": self.original_args,
            "adjusted_args": self.adjusted_args,
            "adjustment_reasoning": self.adjustment_reasoning,
            "attempt_number": self.attempt_number,
            "adjustment_type": self.adjustment_type,
            "status": self.status,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MicroAdjustment":
        """Create from LLM JSON output."""
        return cls(
            original_args=data.get("original_args", {}),
            adjusted_args=data.get("adjusted_args", {}),
            adjustment_reasoning=data.get("adjustment_reasoning", ""),
            attempt_number=data.get("attempt_number", 1),
            adjustment_type=data.get("adjustment_type", "parameter_tweak"),
        )


# =============================================================================
# Phase 2C: Collaboration Schemas
# =============================================================================

@dataclass
class CollaborationResponse:
    """
    Response from the user for a pending collaboration request.
    
    Used when the agent pauses execution to ask the user something,
    and the user responds via the UI.
    """
    response: Any                             # The actual response content
    tool_name: str                            # The tool that requested input
    task_id: str                              # The task ID
    action: Optional[str] = None              # "approve", "reject", "modify", "reply", "abort"
    modifications: Optional[Dict[str, Any]] = None  # If modifying a plan/step

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "tool_name": self.tool_name,
            "task_id": self.task_id,
            "action": self.action,
            "modifications": self.modifications,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollaborationResponse":
        return cls(
            response=data.get("response"),
            tool_name=data.get("tool_name", ""),
            task_id=data.get("task_id", ""),
            action=data.get("action"),
            modifications=data.get("modifications"),
        )


@dataclass
class CollaborationContext:
    """
    Shared context for handling Human-in-the-Loop interactions.
    
    Passed from TaskManager to Orchestrator to allow pausing execution
    and waiting for user input without blocking the thread.
    """
    response_ready: asyncio.Event = field(default_factory=asyncio.Event)
    pending_response: Optional[CollaborationResponse] = None
    
    def reset(self):
        """Reset the context for the next interaction."""
        self.response_ready.clear()
        self.pending_response = None
