"""
Cell Registry for Notebook Coder V2.

Provides cell-to-purpose mapping with keyword indexing for instant lookup
in follow-up queries.

Example:
    "change the clustering algorithm" -> find cell with keywords ["clustering", "heatmap"]
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class CellRegistryEntry:
    """Registry entry for a single notebook cell."""
    cell_id: str
    algorithm_step: int
    purpose: str                      # From step.description
    expected_output: str              # From step.expected_output
    actual_output_summary: str        # What actually happened
    keywords: List[str]               # Extracted from purpose + outputs
    variables_created: List[str]      # From kernel introspection
    files_created: List[str]          # Detected from outputs
    evaluation_score: int             # 0-100
    created_at: datetime
    cell_type: str = "code"           # "code" or "markdown"
    retry_count: int = 0              # How many retries needed

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cell_id": self.cell_id,
            "algorithm_step": self.algorithm_step,
            "purpose": self.purpose,
            "expected_output": self.expected_output,
            "actual_output_summary": self.actual_output_summary,
            "keywords": self.keywords,
            "variables_created": self.variables_created,
            "files_created": self.files_created,
            "evaluation_score": self.evaluation_score,
            "created_at": self.created_at.isoformat(),
            "cell_type": self.cell_type,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CellRegistryEntry":
        """Deserialize from dictionary."""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def matches_query(self, query: str) -> float:
        """
        Score how well this entry matches a query (0.0 to 1.0).

        Higher score = better match.
        """
        query_lower = query.lower()
        query_words = set(_extract_words(query_lower))

        score = 0.0

        # Check keywords (highest weight)
        keyword_matches = sum(1 for kw in self.keywords if kw.lower() in query_lower)
        if self.keywords:
            score += 0.4 * (keyword_matches / len(self.keywords))

        # Check purpose (medium weight)
        purpose_words = set(_extract_words(self.purpose.lower()))
        purpose_overlap = len(query_words & purpose_words)
        if purpose_words:
            score += 0.3 * (purpose_overlap / len(purpose_words))

        # Check expected output (lower weight)
        output_words = set(_extract_words(self.expected_output.lower()))
        output_overlap = len(query_words & output_words)
        if output_words:
            score += 0.2 * (output_overlap / len(output_words))

        # Check variables created (lowest weight)
        for var in self.variables_created:
            if var.lower() in query_lower:
                score += 0.1
                break

        return min(score, 1.0)


@dataclass
class CellRegistry:
    """
    Registry mapping cells to their purposes with keyword indexing.

    Enables instant lookup for follow-up queries like:
    - "change the clustering algorithm" -> finds cell with clustering code
    - "update the heatmap colors" -> finds cell with heatmap visualization
    """
    entries: Dict[str, CellRegistryEntry] = field(default_factory=dict)
    keyword_index: Dict[str, List[str]] = field(default_factory=dict)

    def add_entry(self, entry: CellRegistryEntry) -> None:
        """Add entry and update keyword index."""
        self.entries[entry.cell_id] = entry

        # Update keyword index
        for keyword in entry.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self.keyword_index:
                self.keyword_index[keyword_lower] = []
            if entry.cell_id not in self.keyword_index[keyword_lower]:
                self.keyword_index[keyword_lower].append(entry.cell_id)

        logger.debug(f"Added cell {entry.cell_id[:8]} to registry with keywords: {entry.keywords}")

    def remove_entry(self, cell_id: str) -> bool:
        """Remove entry and clean up keyword index."""
        if cell_id not in self.entries:
            return False

        entry = self.entries.pop(cell_id)

        # Clean up keyword index
        for keyword in entry.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self.keyword_index:
                if cell_id in self.keyword_index[keyword_lower]:
                    self.keyword_index[keyword_lower].remove(cell_id)
                if not self.keyword_index[keyword_lower]:
                    del self.keyword_index[keyword_lower]

        return True

    def update_entry(self, entry: CellRegistryEntry) -> None:
        """Update existing entry (removes old, adds new)."""
        self.remove_entry(entry.cell_id)
        self.add_entry(entry)

    def get_entry(self, cell_id: str) -> Optional[CellRegistryEntry]:
        """Get entry by cell ID."""
        return self.entries.get(cell_id)

    def get_entry_by_step(self, step_number: int) -> Optional[CellRegistryEntry]:
        """Get entry by algorithm step number."""
        for entry in self.entries.values():
            if entry.algorithm_step == step_number:
                return entry
        return None

    def find_by_keyword(self, keyword: str) -> List[CellRegistryEntry]:
        """Find cells matching a keyword exactly."""
        keyword_lower = keyword.lower()
        cell_ids = self.keyword_index.get(keyword_lower, [])
        return [self.entries[cid] for cid in cell_ids if cid in self.entries]

    def find_by_keywords(self, keywords: List[str]) -> List[CellRegistryEntry]:
        """Find cells matching any of the keywords."""
        matching_ids: Set[str] = set()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            cell_ids = self.keyword_index.get(keyword_lower, [])
            matching_ids.update(cell_ids)
        return [self.entries[cid] for cid in matching_ids if cid in self.entries]

    def find_by_query(self, query: str, min_score: float = 0.2) -> List[CellRegistryEntry]:
        """
        Find cells matching a natural language query.

        Returns entries sorted by relevance score (highest first).
        Only returns entries with score >= min_score.
        """
        scored_entries = []
        for entry in self.entries.values():
            score = entry.matches_query(query)
            if score >= min_score:
                scored_entries.append((score, entry))

        # Sort by score descending
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries]

    def find_by_variable(self, variable_name: str) -> List[CellRegistryEntry]:
        """Find cells that created a specific variable."""
        return [
            entry for entry in self.entries.values()
            if variable_name in entry.variables_created
        ]

    def find_by_file(self, file_path: str) -> List[CellRegistryEntry]:
        """Find cells that created a specific file."""
        file_name = file_path.split("/")[-1]  # Handle both full path and filename
        return [
            entry for entry in self.entries.values()
            if file_path in entry.files_created or file_name in entry.files_created
        ]

    def get_all_keywords(self) -> List[str]:
        """Get all unique keywords in the registry."""
        return list(self.keyword_index.keys())

    def get_all_variables(self) -> List[str]:
        """Get all variables created across all cells."""
        variables: Set[str] = set()
        for entry in self.entries.values():
            variables.update(entry.variables_created)
        return list(variables)

    def get_all_files(self) -> List[str]:
        """Get all files created across all cells."""
        files: Set[str] = set()
        for entry in self.entries.values():
            files.update(entry.files_created)
        return list(files)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            "entries": {cid: entry.to_dict() for cid, entry in self.entries.items()},
            "keyword_index": self.keyword_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CellRegistry":
        """Deserialize from dictionary."""
        registry = cls()

        entries_data = data.get("entries", {})
        for cell_id, entry_data in entries_data.items():
            entry = CellRegistryEntry.from_dict(entry_data)
            registry.entries[cell_id] = entry

        registry.keyword_index = data.get("keyword_index", {})

        return registry

    def to_summary(self) -> str:
        """Generate human-readable summary for LLM context."""
        if not self.entries:
            return "No cells registered yet."

        lines = [f"**Cell Registry** ({len(self.entries)} cells):"]

        # Sort by step number
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda e: e.algorithm_step
        )

        for entry in sorted_entries:
            status = "✅" if entry.evaluation_score >= 70 else "⚠️" if entry.evaluation_score >= 50 else "❌"
            lines.append(
                f"- {status} Step {entry.algorithm_step} ({entry.cell_id[:8]}): "
                f"{entry.purpose[:50]}... | Keywords: {', '.join(entry.keywords[:5])}"
            )

        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.entries)

    def __bool__(self) -> bool:
        return len(self.entries) > 0


def _extract_words(text: str) -> List[str]:
    """Extract words from text, filtering out common stop words."""
    # Split on non-alphanumeric characters
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)

    # Filter stop words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once',
        'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither',
        'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just',
        'this', 'that', 'these', 'those', 'it', 'its', 'all', 'each',
        'cell', 'step', 'output', 'result', 'data', 'file', 'code',
    }

    return [w.lower() for w in words if w.lower() not in stop_words and len(w) > 2]


def extract_keywords(
    step_description: str,
    step_keywords: List[str],
    cell_source: str,
    cell_outputs: List[Dict[str, Any]],
    variables_created: List[str],
) -> List[str]:
    """
    Extract keywords from step and cell for indexing.

    Sources:
    - Step description: "Create clustered heatmap" -> ["heatmap", "clustering"]
    - Step keywords: Explicitly provided keywords
    - Cell source: imports, function calls
    - Cell outputs: file names
    - Variables created: variable names

    Returns deduplicated, lowercase keywords.
    """
    keywords: Set[str] = set()

    # From step keywords (highest priority)
    keywords.update(kw.lower() for kw in step_keywords)

    # From step description
    description_words = _extract_words(step_description)
    # Keep significant words
    significant_words = [
        'heatmap', 'plot', 'chart', 'graph', 'visualization', 'visualize',
        'cluster', 'clustering', 'hierarchical', 'kmeans',
        'correlation', 'regression', 'classification', 'prediction',
        'load', 'read', 'import', 'export', 'save', 'write',
        'clean', 'preprocess', 'transform', 'normalize', 'scale',
        'train', 'test', 'validate', 'evaluate', 'fit', 'predict',
        'dataframe', 'array', 'matrix', 'series', 'tensor',
        'image', 'figure', 'table', 'csv', 'json', 'excel',
        'model', 'network', 'layer', 'neural', 'deep',
        'statistics', 'summary', 'describe', 'aggregate', 'groupby',
        'merge', 'join', 'concat', 'split', 'filter', 'select',
        'pca', 'tsne', 'umap', 'embedding', 'dimension',
        'histogram', 'scatter', 'line', 'bar', 'pie', 'box',
        'seaborn', 'matplotlib', 'plotly', 'pandas', 'numpy', 'sklearn',
    ]
    for word in description_words:
        if word in significant_words or len(word) > 5:
            keywords.add(word)

    # From cell source - extract library/function names
    import_pattern = r'(?:import|from)\s+(\w+)'
    for match in re.finditer(import_pattern, cell_source):
        lib = match.group(1).lower()
        if lib not in {'os', 'sys', 'typing', 're', 'json'}:
            keywords.add(lib)

    # Common visualization function names
    viz_functions = ['heatmap', 'scatter', 'plot', 'bar', 'hist', 'boxplot', 'violinplot', 'pairplot']
    for func in viz_functions:
        if func in cell_source.lower():
            keywords.add(func)

    # From outputs - file names
    for output in cell_outputs:
        if isinstance(output, dict):
            # Check for file paths in text outputs
            text = output.get('text', '') or ''
            file_matches = re.findall(r'[\w/]+\.(png|jpg|csv|xlsx|json|html|pdf)', text, re.IGNORECASE)
            for match in file_matches:
                # Add file extension as keyword
                keywords.add(match.lower())

    # From variables - significant variable names
    for var in variables_created:
        var_lower = var.lower()
        # Skip common generic names
        if var_lower not in {'df', 'data', 'x', 'y', 'i', 'j', 'tmp', 'temp', 'result', 'output'}:
            if len(var) > 3:
                keywords.add(var_lower)

    return list(keywords)
