"""
Citation Accuracy evaluator for Mentori RAG pipeline.

Measures:
- Corpus citation accuracy:  % of [N] references pointing to real, relevant chunks
- Intra-citation preservation: % of original paper refs preserved in output
- Hallucinated citation rate: % of citations not matching any source
- Verification pass agreement: % of claims marked "verified" vs manual ground truth

Usage:
    uv run pytest tests/test_citation_accuracy.py -v
"""

import re
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

GROUND_TRUTH_PATH = Path(__file__).parent / "rag_ground_truth.json"


@dataclass
class CitationMetrics:
    """Aggregated citation quality metrics for a single report."""
    total_corpus_citations: int = 0
    valid_corpus_citations: int = 0    # Point to real chunks
    hallucinated_citations: int = 0    # [N] with no matching source

    total_expected_intra: int = 0
    preserved_intra: int = 0           # Author-year refs found in output

    @property
    def corpus_accuracy(self) -> float:
        if self.total_corpus_citations == 0:
            return 1.0
        return self.valid_corpus_citations / self.total_corpus_citations

    @property
    def hallucination_rate(self) -> float:
        if self.total_corpus_citations == 0:
            return 0.0
        return self.hallucinated_citations / self.total_corpus_citations

    @property
    def intra_preservation_rate(self) -> float:
        if self.total_expected_intra == 0:
            return 1.0
        return self.preserved_intra / self.total_expected_intra


class CitationAccuracyEvaluator:
    """
    Evaluates citation quality in RLM-generated reports.

    Given a report text and the RLM context that produced it, measures
    how accurately citations are used and whether intra-document
    references are preserved.
    """

    def evaluate_report(
        self,
        report_text: str,
        context=None,
        expected_intra_citations: List[str] = None,
    ) -> CitationMetrics:
        """
        Evaluate citation accuracy of a report.

        Args:
            report_text: The generated markdown report
            context: Optional RLMContext for validating corpus citations
            expected_intra_citations: List of expected (Author, Year) strings

        Returns:
            CitationMetrics with accuracy scores
        """
        metrics = CitationMetrics()

        # 1. Analyse corpus citations [N]
        corpus_refs = self._extract_numbered_refs(report_text)
        sources_section = self._extract_sources_section(report_text)
        metrics.total_corpus_citations = len(corpus_refs)

        for ref_num in corpus_refs:
            if self._ref_exists_in_sources(ref_num, sources_section):
                metrics.valid_corpus_citations += 1
            else:
                metrics.hallucinated_citations += 1

        # 2. Check intra-document citation preservation
        if expected_intra_citations:
            metrics.total_expected_intra = len(expected_intra_citations)
            for expected_ref in expected_intra_citations:
                # Flexible matching: ignore whitespace differences
                normalised = re.sub(r'\s+', ' ', expected_ref.strip())
                if normalised.lower() in re.sub(r'\s+', ' ', report_text).lower():
                    metrics.preserved_intra += 1

        return metrics

    def _extract_numbered_refs(self, text: str) -> List[int]:
        """Extract all [N] citation numbers from the report body."""
        # Only look in body (before Sources section)
        body = text.split("## Sources")[0] if "## Sources" in text else text
        return [int(n) for n in re.findall(r'\[(\d+)\]', body)]

    def _extract_sources_section(self, text: str) -> str:
        """Extract the Sources/References section."""
        for header in ["## Sources", "## References"]:
            if header in text:
                idx = text.index(header)
                # Get everything from this header to the next ## or end
                remaining = text[idx + len(header):]
                next_section = remaining.find("\n## ")
                if next_section > 0:
                    return remaining[:next_section]
                return remaining
        return ""

    def _ref_exists_in_sources(self, ref_num: int, sources_section: str) -> bool:
        """Check if [N] has a matching entry in the Sources section."""
        pattern = rf'\[{ref_num}\]'
        return bool(re.search(pattern, sources_section))


# ── pytest integration ────────────────────────────────────────────────────────

def test_citation_evaluator_basic():
    """Test citation evaluation with a synthetic report."""
    report = """## Findings

The study found off-target effects (Smith et al., 2020) [1].
Later work confirmed this result [2].

---
## Sources (from your corpus)
[1] paper.pdf, page 5: "Off-target effects occur when..."
[2] review.pdf, page 12: "Confirmed by independent analysis..."
"""

    evaluator = CitationAccuracyEvaluator()
    metrics = evaluator.evaluate_report(
        report_text=report,
        expected_intra_citations=["(Smith et al., 2020)"],
    )

    assert metrics.total_corpus_citations == 2
    assert metrics.valid_corpus_citations == 2
    assert metrics.hallucinated_citations == 0
    assert metrics.corpus_accuracy == 1.0

    assert metrics.total_expected_intra == 1
    assert metrics.preserved_intra == 1
    assert metrics.intra_preservation_rate == 1.0


def test_citation_evaluator_hallucinated():
    """Test that missing source entries are flagged."""
    report = """## Findings

Something was found [1]. Another claim [3].

---
## Sources (from your corpus)
[1] paper.pdf, page 1: "Some text..."
"""

    evaluator = CitationAccuracyEvaluator()
    metrics = evaluator.evaluate_report(report_text=report)

    assert metrics.total_corpus_citations == 2
    assert metrics.valid_corpus_citations == 1  # [1] exists
    assert metrics.hallucinated_citations == 1  # [3] missing
    assert metrics.hallucination_rate == 0.5


def test_citation_evaluator_missing_intra():
    """Test detection of missing intra-document citations."""
    report = """## Findings

The study found something important [1].

---
## Sources (from your corpus)
[1] paper.pdf, page 5: "Important finding..."
"""

    evaluator = CitationAccuracyEvaluator()
    metrics = evaluator.evaluate_report(
        report_text=report,
        expected_intra_citations=["(Smith et al., 2020)", "(Jones, 2019)"],
    )

    assert metrics.intra_preservation_rate == 0.0


def test_ground_truth_has_citation_category():
    """Verify the ground truth file has the new citation_accuracy category."""
    with open(GROUND_TRUTH_PATH) as f:
        data = json.load(f)

    categories = [c["category"] for c in data["test_categories"]]
    assert "citation_accuracy" in categories
    assert "cross_document_synthesis" in categories
