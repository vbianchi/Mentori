"""
Mentori Orchestrator - Multi-Agent Orchestration System

This module implements a structured, transparent orchestration system
for scientific AI workflows. It replaces the legacy chat_loop.py with
a proper state machine that provides:

- Full audit trail (all thinking saved to history)
- Multi-agent coordination with role-based model assignment
- Visible reasoning at every phase
- Direct answer mode for simple queries
- Plan-based execution for complex tasks

Main entry point: orchestrated_chat() in engine.py
"""

from backend.agents.orchestrator.engine import orchestrated_chat
from backend.agents.orchestrator.schemas import (
    ExecutionPlan,
    PlanStep,
    OrchestratorState,
    StepResult,
    AnalysisResult,
    EvaluationResult,
    PlanStatus,
    StepStatus,
    # Phase 2A: Supervisor schemas
    SupervisorEvaluation,
    MicroAdjustment,
)
from backend.agents.orchestrator.supervisor import (
    evaluate_step_quality,
    suggest_micro_adjustment,
    should_trigger_reflection,
    update_supervisor_tracking,
)

__all__ = [
    "orchestrated_chat",
    "ExecutionPlan",
    "PlanStep",
    "OrchestratorState",
    "StepResult",
    "AnalysisResult",
    "EvaluationResult",
    "PlanStatus",
    "StepStatus",
    # Phase 2A: Supervisor exports
    "SupervisorEvaluation",
    "MicroAdjustment",
    "evaluate_step_quality",
    "suggest_micro_adjustment",
    "should_trigger_reflection",
    "update_supervisor_tracking",
]
