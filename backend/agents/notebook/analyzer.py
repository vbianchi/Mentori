"""
Request Analyzer for Notebook Coder V2.

Determines if a request is trivial (direct execution), needs modification
of existing cells, requires full algorithm planning, or needs clarification.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agents.model_router import ModelRouter
    from backend.agents.notebook.schema import NotebookState
    from backend.agents.notebook.cell_registry import CellRegistry

from backend.agents.notebook.prompts_v2 import (
    ANALYSIS_PROMPT,
    build_notebook_summary,
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of request analysis."""
    classification: str  # "trivial", "modify", "complex", "clarification"
    detected_intent: str
    relevant_cells: List[str]  # Cell IDs that are relevant to this request
    modification_target: Optional[str]  # Cell ID to modify if classification is "modify"
    clarification_question: Optional[str]  # Question to ask if classification is "clarification"
    confidence: float  # 0.0 to 1.0

    @property
    def is_trivial(self) -> bool:
        return self.classification == "trivial"

    @property
    def is_modify(self) -> bool:
        return self.classification == "modify"

    @property
    def is_complex(self) -> bool:
        return self.classification == "complex"

    @property
    def needs_clarification(self) -> bool:
        return self.classification == "clarification"


async def analyze_request(
    user_request: str,
    notebook_state: Optional[Dict[str, Any]],
    memory_context: str,
    cell_registry: Optional["CellRegistry"],
    model_router: "ModelRouter",
    model_identifier: str,
) -> AnalysisResult:
    """
    Analyze a user request to determine how to handle it.

    Returns:
        AnalysisResult with classification and relevant context.
    """
    # First, try rule-based classification for obvious cases
    rule_based = _rule_based_analysis(user_request, notebook_state, cell_registry)
    if rule_based is not None:
        logger.info(f"Request classified by rules: {rule_based.classification}")
        return rule_based

    # Build context for LLM analysis
    notebook_summary = build_notebook_summary(notebook_state) if notebook_state else "Empty notebook"
    cell_registry_summary = cell_registry.to_summary() if cell_registry else "No cells registered"

    prompt = ANALYSIS_PROMPT.format(
        user_request=user_request,
        notebook_summary=notebook_summary,
        memory_context=memory_context or "(No previous work)",
        cell_registry_summary=cell_registry_summary,
    )

    try:
        response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,
                "num_predict": 500,
            }
        )

        logger.info(f"ANALYSIS RAW: {response}")

        # Extract response text
        response_text = _extract_response_text(response)
        result = _parse_analysis_response(response_text, cell_registry)

        logger.info(f"Request classified by LLM: {result.classification} (confidence: {result.confidence})")
        return result

    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}, falling back to complex")
        return AnalysisResult(
            classification="complex",
            detected_intent=user_request[:100],
            relevant_cells=[],
            modification_target=None,
            clarification_question=None,
            confidence=0.5,
        )


def _rule_based_analysis(
    user_request: str,
    notebook_state: Optional[Dict[str, Any]],
    cell_registry: Optional["CellRegistry"],
) -> Optional[AnalysisResult]:
    """
    Apply rule-based heuristics for obvious classifications.

    Returns None if LLM analysis is needed.
    """
    request_lower = user_request.lower().strip()

    # Trivial: run/execute specific cell
    run_cell_patterns = [
        r"^run\s+cell\s*(\d+|[a-f0-9-]+)",
        r"^execute\s+cell\s*(\d+|[a-f0-9-]+)",
        r"^re-?run\s+(the\s+)?(last|previous)\s+cell",
        r"^run\s+(the\s+)?(last|previous)\s+cell",
        r"^run\s+it\s+again",
    ]
    for pattern in run_cell_patterns:
        if re.match(pattern, request_lower):
            return AnalysisResult(
                classification="trivial",
                detected_intent="Execute cell",
                relevant_cells=_extract_cell_reference(request_lower, notebook_state),
                modification_target=None,
                clarification_question=None,
                confidence=0.95,
            )

    # Trivial: show/display something simple
    show_patterns = [
        r"^show\s+(me\s+)?(the\s+)?(first|last)\s+\d+\s+rows",
        r"^display\s+(the\s+)?dataframe",
        r"^print\s+(the\s+)?",
        r"^show\s+(the\s+)?shape",
        r"^what('s|\s+is)\s+the\s+shape",
    ]
    for pattern in show_patterns:
        if re.match(pattern, request_lower):
            return AnalysisResult(
                classification="trivial",
                detected_intent="Display data",
                relevant_cells=[],
                modification_target=None,
                clarification_question=None,
                confidence=0.9,
            )

    # Modify: explicit change requests with keywords
    modify_keywords = [
        "change", "modify", "update", "replace", "switch", "use instead",
        "different", "another", "instead of",
        # Natural language modification phrases
        "make it", "make the", "turn it into", "convert it to", "convert to",
        "add to the", "remove from the", "adjust the", "tweak the",
        "try with", "use a", "use the", "with a different",
        # Visualization-specific modification phrases
        "clustered", "cluster", "sort by", "color by", "group by",
        "add title", "add label", "add legend", "remove title", "resize",
        "change color", "change size", "change style",
    ]
    has_modify_keyword = any(kw in request_lower for kw in modify_keywords)

    if has_modify_keyword and cell_registry:
        # Try to find relevant cells
        relevant = cell_registry.find_by_query(user_request, min_score=0.3)
        if relevant:
            return AnalysisResult(
                classification="modify",
                detected_intent=f"Modify existing cell",
                relevant_cells=[e.cell_id for e in relevant[:3]],
                modification_target=relevant[0].cell_id,
                clarification_question=None,
                confidence=0.8,
            )

    # Too vague: needs clarification
    vague_patterns = [
        r"^(do|make|help)\s+(it|something|things?)(\s+better)?$",
        r"^analyze\s*(it|this|the\s+data)?$",
        r"^fix\s*(it)?$",
        r"^improve\s*(it|this)?$",
    ]
    for pattern in vague_patterns:
        if re.match(pattern, request_lower):
            return AnalysisResult(
                classification="clarification",
                detected_intent="Unclear request",
                relevant_cells=[],
                modification_target=None,
                clarification_question="Could you be more specific? What would you like me to analyze or improve?",
                confidence=0.85,
            )

    # Let LLM handle the rest
    return None


def _extract_cell_reference(request: str, notebook_state: Optional[Dict[str, Any]]) -> List[str]:
    """Extract cell ID or index from request."""
    if not notebook_state:
        return []

    cells = notebook_state.get("cells_summary", [])
    if not cells:
        return []

    # Check for "last" or "previous"
    if "last" in request or "previous" in request:
        return [cells[-1].get("id", "")] if cells else []

    # Check for cell number
    match = re.search(r"cell\s*(\d+)", request)
    if match:
        idx = int(match.group(1)) - 1  # 1-indexed to 0-indexed
        if 0 <= idx < len(cells):
            return [cells[idx].get("id", "")]

    # Check for cell ID
    match = re.search(r"cell\s*([a-f0-9-]{8,})", request)
    if match:
        cell_id_prefix = match.group(1)
        for cell in cells:
            if cell.get("id", "").startswith(cell_id_prefix):
                return [cell.get("id", "")]

    return []


def _extract_response_text(response: Any) -> str:
    """Extract text from various response formats."""
    if isinstance(response, dict):
        if "message" in response and "content" in response["message"]:
            return response["message"]["content"]
        elif "response" in response:
            return response["response"]
        elif "content" in response:
            return response["content"]
        return str(response)
    elif hasattr(response, "content"):
        return response.content
    return str(response)


def _parse_analysis_response(
    response_text: str,
    cell_registry: Optional["CellRegistry"],
) -> AnalysisResult:
    """Parse LLM response into AnalysisResult."""
    # Try to extract JSON
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response_text)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            data = {}
    else:
        # Try direct JSON parse
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = {}
        except json.JSONDecodeError:
            data = {}

    classification = data.get("classification", "complex").lower()
    if classification not in ["trivial", "modify", "complex", "clarification"]:
        classification = "complex"

    # Validate relevant_cells exist in registry
    relevant_cells = data.get("relevant_cells", [])
    if cell_registry and relevant_cells:
        valid_cells = []
        for cell_id in relevant_cells:
            # Check if cell exists (full or partial ID)
            if cell_registry.get_entry(cell_id):
                valid_cells.append(cell_id)
            else:
                # Try partial match
                for entry_id in cell_registry.entries.keys():
                    if entry_id.startswith(cell_id) or cell_id.startswith(entry_id[:8]):
                        valid_cells.append(entry_id)
                        break
        relevant_cells = valid_cells

    return AnalysisResult(
        classification=classification,
        detected_intent=data.get("detected_intent", "Process request"),
        relevant_cells=relevant_cells,
        modification_target=data.get("modification_target"),
        clarification_question=data.get("clarification_question"),
        confidence=0.7,  # LLM-based classification gets moderate confidence
    )


