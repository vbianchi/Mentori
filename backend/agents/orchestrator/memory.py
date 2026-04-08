"""
Task Session Memory for Mentori Orchestrator (Phase 2B)

Provides persistent memory across queries within the same task:
- SessionMemory: Record of a single orchestrator session
- TaskMemoryVault: Persistent vault spanning multiple queries
- consolidate_session_memory: Librarian agent for memory distillation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable, Awaitable, TYPE_CHECKING
from pathlib import Path
import json
import logging
import re

if TYPE_CHECKING:
    from backend.agents.orchestrator.schemas import ExecutionPlan, StepResult
    from backend.agents.model_router import ModelRouter

logger = logging.getLogger(__name__)


@dataclass
class SessionMemory:
    """Memory record for a single orchestrator/coder session within a task."""
    session_id: str
    timestamp: datetime
    user_query: str
    user_intent: str
    plan_summary: str
    actions_taken: List[Dict[str, Any]]
    artifacts_created: List[Dict[str, str]]
    documents_accessed: List[Dict[str, str]]
    key_findings: List[str]
    open_questions: List[str]
    token_count: int
    # V2 fields for coder mode
    session_mode: str = "orchestrator"  # "orchestrator" or "coder"
    cell_registry: Optional[Dict[str, Any]] = None  # CellRegistry.to_dict() for coder sessions
    cell_purposes: Optional[Dict[str, str]] = None  # cell_id -> purpose for quick lookup

    def to_markdown(self) -> str:
        """Format session as markdown for context injection."""
        mode_indicator = " [Coder]" if self.session_mode == "coder" else ""
        lines = [
            f"### Session {self.session_id}{mode_indicator} ({self.timestamp.strftime('%H:%M %b %d')})",
            f"**Intent**: {self.user_intent}",
            "",
        ]

        # For coder sessions, show cell purposes for quick lookup
        if self.cell_purposes:
            lines.append("**Cells Created**:")
            for cell_id, purpose in list(self.cell_purposes.items())[:8]:
                lines.append(f"- `{cell_id[:8]}`: {purpose}")
            lines.append("")

        if self.actions_taken:
            lines.append("**Actions**:")
            for action in self.actions_taken[:5]:
                summary = action.get('summary', action.get('tool', 'Unknown action'))
                lines.append(f"- {summary}")

        if self.artifacts_created:
            lines.append("")
            lines.append("**Artifacts Created**:")
            for artifact in self.artifacts_created:
                lines.append(f"- `{artifact.get('path', 'unknown')}`: {artifact.get('description', '')}")

        if self.key_findings:
            lines.append("")
            lines.append("**Key Findings**:")
            for finding in self.key_findings[:5]:
                lines.append(f"- {finding}")

        if self.open_questions:
            lines.append("")
            lines.append("**Open Questions**:")
            for question in self.open_questions:
                lines.append(f"- {question}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "user_query": self.user_query,
            "user_intent": self.user_intent,
            "plan_summary": self.plan_summary,
            "actions_taken": self.actions_taken,
            "artifacts_created": self.artifacts_created,
            "documents_accessed": self.documents_accessed,
            "key_findings": self.key_findings,
            "open_questions": self.open_questions,
            "token_count": self.token_count,
            "session_mode": self.session_mode,
        }
        # Only include cell registry fields if present (coder mode)
        if self.cell_registry is not None:
            data["cell_registry"] = self.cell_registry
        if self.cell_purposes is not None:
            data["cell_purposes"] = self.cell_purposes
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMemory":
        """Create SessionMemory from dictionary."""
        data = data.copy()
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        # Handle optional V2 fields with defaults for backwards compatibility
        data.setdefault("session_mode", "orchestrator")
        data.setdefault("cell_registry", None)
        data.setdefault("cell_purposes", None)
        return cls(**data)


@dataclass
class TaskMemoryVault:
    """Persistent memory vault for a task, spanning multiple queries."""
    task_id: str
    user_id: str
    workspace_path: Path
    sessions: List[SessionMemory] = field(default_factory=list)
    total_token_count: int = 0
    max_context_tokens: int = 8000

    @property
    def vault_dir(self) -> Path:
        return self.workspace_path / ".memory"

    def load(self) -> "TaskMemoryVault":
        """Load vault from disk if exists."""
        metadata_path = self.vault_dir / "vault_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path) as f:
                    meta = json.load(f)
                    self.total_token_count = meta.get("total_token_count", 0)
                    self.max_context_tokens = meta.get("max_context_tokens", 8000)

                # Load sessions
                sessions_dir = self.vault_dir / "sessions"
                if sessions_dir.exists():
                    self.sessions = []
                    for session_file in sorted(sessions_dir.glob("session_*.json")):
                        try:
                            with open(session_file) as f:
                                data = json.load(f)
                                self.sessions.append(SessionMemory.from_dict(data))
                        except Exception as e:
                            logger.warning(f"Failed to load session {session_file}: {e}")

                logger.debug(f"Loaded memory vault: {len(self.sessions)} sessions, {self.total_token_count} tokens")
            except Exception as e:
                logger.warning(f"Failed to load memory vault metadata: {e}")

        return self

    def save_session(self, session: SessionMemory):
        """Save a new session to the vault."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        sessions_dir = self.vault_dir / "sessions"
        sessions_dir.mkdir(exist_ok=True)

        # Save session JSON
        session_path = sessions_dir / f"session_{session.session_id}.json"
        with open(session_path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

        self.sessions.append(session)
        self.total_token_count += session.token_count

        # Update vault summary
        self._update_summary()
        self._save_metadata()

        logger.info(f"Saved session {session.session_id} to memory vault ({session.token_count} tokens)")

    def _update_summary(self):
        """Regenerate the rolling summary for context injection."""
        summary_lines = ["## Previous Work in This Task\n"]

        # Include sessions in reverse order (most recent first), respecting token budget
        tokens_used = 0
        included_count = 0

        for session in reversed(self.sessions):
            session_md = session.to_markdown()
            if tokens_used + session.token_count > self.max_context_tokens:
                if included_count > 0:
                    summary_lines.append("\n*Earlier sessions omitted due to context budget*")
                break
            summary_lines.append(session_md)
            summary_lines.append("")
            tokens_used += session.token_count
            included_count += 1

        if included_count == 0:
            summary_lines = ["(No previous sessions in this task)"]
        else:
            summary_lines.append(f"\n**Memory Context**: ~{tokens_used:,} tokens used of {self.max_context_tokens:,} budget")

        with open(self.vault_dir / "vault_summary.md", "w") as f:
            f.write("\n".join(summary_lines))

    def _save_metadata(self):
        """Save vault metadata."""
        with open(self.vault_dir / "vault_metadata.json", "w") as f:
            json.dump({
                "task_id": self.task_id,
                "user_id": self.user_id,
                "total_token_count": self.total_token_count,
                "max_context_tokens": self.max_context_tokens,
                "session_count": len(self.sessions),
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)

    def get_context_for_injection(self) -> str:
        """Get the summary markdown for injecting into planner context."""
        summary_path = self.vault_dir / "vault_summary.md"
        if summary_path.exists():
            return summary_path.read_text()
        return "(No previous sessions in this task)"

    def save_cell_registry(self, registry_data: Dict[str, Any]) -> None:
        """
        Save cell registry for coder sessions.

        The registry enables instant lookup of cells by keywords/purpose
        in follow-up queries.
        """
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        registry_path = self.vault_dir / "cell_registry.json"
        with open(registry_path, "w") as f:
            json.dump(registry_data, f, indent=2)
        logger.debug(f"Saved cell registry with {len(registry_data.get('entries', {}))} entries")

    def load_cell_registry(self) -> Optional[Dict[str, Any]]:
        """
        Load cell registry from disk.

        Returns None if no registry exists (orchestrator-only task or new task).
        """
        registry_path = self.vault_dir / "cell_registry.json"
        if registry_path.exists():
            try:
                with open(registry_path) as f:
                    data = json.load(f)
                    logger.debug(f"Loaded cell registry with {len(data.get('entries', {}))} entries")
                    return data
            except Exception as e:
                logger.warning(f"Failed to load cell registry: {e}")
        return None

    def get_cell_purposes(self) -> Dict[str, str]:
        """
        Get a quick cell_id -> purpose mapping from all coder sessions.

        Merges cell_purposes from all coder sessions for context injection.
        """
        purposes = {}
        for session in self.sessions:
            if session.cell_purposes:
                purposes.update(session.cell_purposes)
        return purposes

    def find_cells_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Find cells matching a keyword from the registry.

        Returns list of {cell_id, purpose, session_id} dicts.
        """
        keyword_lower = keyword.lower()
        results = []

        # Check registry first
        registry = self.load_cell_registry()
        if registry:
            keyword_index = registry.get("keyword_index", {})
            cell_ids = keyword_index.get(keyword_lower, [])
            entries = registry.get("entries", {})
            for cell_id in cell_ids:
                if cell_id in entries:
                    entry = entries[cell_id]
                    results.append({
                        "cell_id": cell_id,
                        "purpose": entry.get("purpose", ""),
                        "keywords": entry.get("keywords", []),
                        "source": "registry"
                    })

        # Also check session cell_purposes for backup
        for session in self.sessions:
            if session.cell_purposes:
                for cell_id, purpose in session.cell_purposes.items():
                    if keyword_lower in purpose.lower():
                        # Avoid duplicates
                        if not any(r["cell_id"] == cell_id for r in results):
                            results.append({
                                "cell_id": cell_id,
                                "purpose": purpose,
                                "session_id": session.session_id,
                                "source": "session"
                            })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics for UI display."""
        usage_percent = (self.total_token_count / self.max_context_tokens * 100) if self.max_context_tokens > 0 else 0
        return {
            "session_count": len(self.sessions),
            "total_tokens": self.total_token_count,
            "max_tokens": self.max_context_tokens,
            "usage_percent": round(usage_percent, 1),
            "sessions": [
                {
                    "id": s.session_id,
                    "timestamp": s.timestamp.isoformat(),
                    "intent": s.user_intent,
                    "tokens": s.token_count,
                    "artifacts": len(s.artifacts_created),
                    "findings": len(s.key_findings)
                }
                for s in self.sessions
            ]
        }

    def remove_session(self, session_id: str) -> bool:
        """Remove a session from the vault (user-initiated cleanup)."""
        for i, session in enumerate(self.sessions):
            if session.session_id == session_id:
                removed = self.sessions.pop(i)
                self.total_token_count -= removed.token_count

                # Delete session file
                session_path = self.vault_dir / "sessions" / f"session_{session_id}.json"
                if session_path.exists():
                    session_path.unlink()

                self._update_summary()
                self._save_metadata()

                logger.info(f"Removed session {session_id} from memory vault")
                return True

        return False


def _estimate_tokens(text: str) -> int:
    """Rough token estimation (approximately 4 chars per token)."""
    return len(text) // 4


def _extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try direct JSON parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding raw JSON object
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


async def consolidate_session_memory(
    task_id: str,
    user_id: str,
    workspace_path: Path,
    user_query: str,
    plan: Optional["ExecutionPlan"],
    step_results: List[Dict[str, Any]],
    final_answer: str,
    model_router: "ModelRouter",
    librarian_model: str,
    event_callback=None,
) -> Optional[SessionMemory]:
    """
    Run the Librarian agent to consolidate session events into memory.

    This runs in the background after synthesis completes.
    """
    from backend.agents.orchestrator.prompts import LIBRARIAN_CONSOLIDATION_PROMPT

    # Collect structured events
    actions = []
    artifacts = []
    documents = []

    for result in step_results:
        tool_name = result.get("tool_name", "unknown")
        tool_args = result.get("tool_args", {}) if isinstance(result.get("tool_args"), dict) else {}
        result_content = str(result.get("content", ""))
        success = result.get("success", False)

        # Build action summary - prefer execution summary over plan description
        action_summary = result.get("summary") or result.get("step_description") or tool_name

        # For tools with queries/paths, include them in summary for uniqueness
        if tool_name == "web_search" and tool_args.get("query"):
            action_summary = f"Searched web for: {tool_args['query'][:50]}"
        elif tool_name == "write_file" and tool_args.get("path"):
            action_summary = f"{'Wrote' if success else 'Failed to write'} file: {tool_args['path']}"
        elif tool_name == "read_file" and tool_args.get("path"):
            action_summary = f"Read file: {tool_args['path']}"

        action = {
            "tool": tool_name,
            "summary": action_summary,
            "success": success
        }
        actions.append(action)

        # Detect artifacts created from tool results
        if tool_name in ["write_file", "summarize_document_pages", "deep_research_rlm"]:
            if success:
                # For write_file, the path is in tool_args
                if tool_name == "write_file" and tool_args.get("path"):
                    artifacts.append({
                        "path": tool_args["path"],
                        "description": f"File created by {tool_name}"
                    })
                else:
                    # Try to extract file paths from result content
                    path_matches = re.findall(r'(?:saved to|created|wrote to|output[:\s]+)[`\s]*([^\s`\n]+\.\w+)', result_content, re.IGNORECASE)
                    for path in path_matches:
                        artifacts.append({"path": path, "description": f"Output from {tool_name}"})

        # Detect documents/sources accessed
        if tool_name in ["query_documents", "read_document", "deep_research", "inspect_document_index"]:
            index_name = tool_args.get("index_name", "")
            query = tool_args.get("query", "")
            if index_name:
                documents.append({"index": index_name, "query": query[:100] if query else ""})

        # Track web search sources
        if tool_name == "web_search" and success:
            query = tool_args.get("query", "")
            # Extract URLs from result content if present
            urls = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', result_content)
            if urls:
                for title, url in urls[:5]:  # Limit to first 5 sources
                    documents.append({"source": url, "title": title[:50], "type": "web_search"})
            elif query:
                documents.append({"source": "web_search", "query": query[:100], "type": "web_search"})

    # Build prompt for Librarian
    plan_goal = plan.goal if plan else "Direct answer (no plan)"
    plan_steps = "\n".join(f"- {s.description}" for s in plan.steps) if plan and plan.steps else "No steps (direct answer)"
    actions_summary = json.dumps(actions[:10], indent=2) if actions else "No actions taken"
    final_answer_preview = final_answer[:500] + "..." if len(final_answer) > 500 else final_answer

    prompt = LIBRARIAN_CONSOLIDATION_PROMPT.format(
        user_query=user_query,
        plan_goal=plan_goal,
        plan_steps=plan_steps,
        actions_summary=actions_summary,
        final_answer_preview=final_answer_preview
    )

    # Call Librarian model
    try:
        response = await model_router.generate(
            model_identifier=librarian_model,
            prompt=prompt,
            options={"temperature": 0.3, "num_predict": 800}
        )

        # Emit token usage from non-streaming generate() response
        if event_callback and isinstance(response, dict):
            inp = response.get("prompt_eval_count", 0)
            out = response.get("eval_count", 0)
            if inp or out:
                try:
                    await event_callback({
                        "type": "token_usage",
                        "token_usage": {"input": inp, "output": out, "total": inp + out},
                        "source": "memory:consolidation",
                    })
                except Exception:
                    pass

        response_text = response.get("content", "") if isinstance(response, dict) else str(response)
        memory_data = _extract_json_from_response(response_text)

        if not memory_data:
            logger.warning("Librarian response was not valid JSON, using fallback")
            memory_data = {
                "user_intent": user_query[:100],
                "accomplished": ["Query processed"],
                "artifacts": artifacts,
                "key_findings": [],
                "open_questions": []
            }

    except Exception as e:
        logger.error(f"Librarian LLM call failed: {e}")
        memory_data = {
            "user_intent": user_query[:100],
            "accomplished": ["Query processed (memory consolidation failed)"],
            "artifacts": artifacts,
            "key_findings": [],
            "open_questions": []
        }

    # Load existing vault to get next session ID
    vault = TaskMemoryVault(
        task_id=task_id,
        user_id=user_id,
        workspace_path=workspace_path
    ).load()

    # Generate session ID
    session_id = f"{len(vault.sessions) + 1:03d}"

    # Create session memory
    session = SessionMemory(
        session_id=session_id,
        timestamp=datetime.now(),
        user_query=user_query,
        user_intent=memory_data.get("user_intent", user_query[:100]),
        plan_summary=plan_goal,
        actions_taken=actions,
        artifacts_created=memory_data.get("artifacts", artifacts),
        documents_accessed=documents,
        key_findings=memory_data.get("key_findings", []),
        open_questions=memory_data.get("open_questions", []),
        token_count=_estimate_tokens(json.dumps(memory_data))
    )

    # Save to vault
    vault.save_session(session)

    return session
