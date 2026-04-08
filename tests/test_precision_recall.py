"""
Precision-Recall evaluator for Mentori RAG pipeline.

Runs retrieval at k=1,3,5,10 against ground truth, computes precision@k
and recall@k, and optionally compares across embedding models.

Usage:
    uv run pytest tests/test_precision_recall.py -v
    uv run python tests/test_precision_recall.py          # standalone report
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

GROUND_TRUTH_PATH = Path(__file__).parent / "rag_ground_truth.json"


@dataclass
class PRResult:
    """Precision-recall result for a single query at a given k."""
    query_id: str
    k: int
    precision: float
    recall: float
    retrieved_files: List[str] = field(default_factory=list)
    expected_terms_found: int = 0
    expected_terms_total: int = 0


@dataclass
class ModelPRReport:
    """Aggregated precision-recall report for one embedding model."""
    model_name: str
    results_by_k: Dict[int, List[PRResult]] = field(default_factory=dict)

    def avg_precision(self, k: int) -> float:
        results = self.results_by_k.get(k, [])
        if not results:
            return 0.0
        return sum(r.precision for r in results) / len(results)

    def avg_recall(self, k: int) -> float:
        results = self.results_by_k.get(k, [])
        if not results:
            return 0.0
        return sum(r.recall for r in results) / len(results)


class PrecisionRecallEvaluator:
    """
    Evaluates retrieval quality by measuring precision@k and recall@k
    against ground-truth questions from rag_ground_truth.json.
    """

    K_VALUES = [1, 3, 5, 10]

    def __init__(self, collection_name: str, embedding_model: str = None):
        """
        Args:
            collection_name: Name of the vector DB collection to test against.
            embedding_model: HuggingFace model name. If None, uses default.
        """
        self.collection_name = collection_name
        self.embedding_model = embedding_model

    def evaluate(self) -> ModelPRReport:
        """Run the full evaluation and return a report."""
        from backend.retrieval.retriever import SimpleRetriever

        retriever = SimpleRetriever(
            embedding_model=self.embedding_model,
            collection_name=self.collection_name,
        )

        ground_truth = self._load_ground_truth()
        report = ModelPRReport(model_name=self.embedding_model or "default")

        for k in self.K_VALUES:
            report.results_by_k[k] = []

            for item in ground_truth:
                results = retriever.retrieve(
                    query=item["question"],
                    top_k=k,
                    collection_name=self.collection_name,
                )

                pr = self._score_results(item, results, k)
                report.results_by_k[k].append(pr)

        return report

    def _score_results(
        self, item: Dict[str, Any], results: List[Dict], k: int
    ) -> PRResult:
        """Score a single query's results against ground truth."""
        query_id = item["id"]
        expected_file = item.get("source_file", "")
        expected_terms = item.get("expected_in_chunk", [])

        retrieved_files = []
        terms_found = set()

        for res in results:
            meta = res.get("metadata", {})
            file_name = meta.get("file_name", "")
            retrieved_files.append(file_name)
            text_lower = res.get("text", "").lower()
            for term in expected_terms:
                if term.lower() in text_lower:
                    terms_found.add(term)

        # Precision: fraction of retrieved results from the correct source
        if results and expected_file:
            correct = sum(1 for f in retrieved_files if expected_file in f)
            precision = correct / len(results)
        else:
            precision = 0.0

        # Recall: fraction of expected terms found in the retrieved text
        if expected_terms:
            recall = len(terms_found) / len(expected_terms)
        else:
            recall = 1.0 if expected_file and any(expected_file in f for f in retrieved_files) else 0.0

        return PRResult(
            query_id=query_id,
            k=k,
            precision=precision,
            recall=recall,
            retrieved_files=retrieved_files,
            expected_terms_found=len(terms_found),
            expected_terms_total=len(expected_terms),
        )

    def _load_ground_truth(self) -> List[Dict]:
        """Load and flatten ground truth questions that have expected_in_chunk."""
        with open(GROUND_TRUTH_PATH) as f:
            data = json.load(f)

        questions = []
        for cat in data["test_categories"]:
            for q in cat["questions"]:
                if q.get("expected_in_chunk") or q.get("source_file"):
                    questions.append(q)

        return questions

    def print_report(self, report: ModelPRReport):
        """Print a human-readable summary."""
        print(f"\n{'='*60}")
        print(f"Precision-Recall Report: {report.model_name}")
        print(f"{'='*60}")
        print(f"{'k':>4} | {'Precision@k':>12} | {'Recall@k':>10} | {'N queries':>9}")
        print(f"{'-'*4}-+-{'-'*12}-+-{'-'*10}-+-{'-'*9}")

        for k in self.K_VALUES:
            n = len(report.results_by_k.get(k, []))
            print(
                f"{k:>4} | {report.avg_precision(k):>11.3f} | "
                f"{report.avg_recall(k):>9.3f} | {n:>9}"
            )

        print()


# ── pytest integration ────────────────────────────────────────────────────────

def test_precision_recall_default_model(tmp_path):
    """Smoke test: evaluator instantiation and ground-truth loading."""
    evaluator = PrecisionRecallEvaluator(
        collection_name="test_pr_eval",
        embedding_model="all-MiniLM-L6-v2",
    )
    gt = evaluator._load_ground_truth()
    assert len(gt) > 0, "Ground truth should have questions with expected_in_chunk"


# ── standalone entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    collection = sys.argv[1] if len(sys.argv) > 1 else "test_eval"
    models = ["all-MiniLM-L6-v2", "allenai/specter2"]

    for model in models:
        print(f"\nEvaluating model: {model}")
        try:
            ev = PrecisionRecallEvaluator(collection_name=collection, embedding_model=model)
            report = ev.evaluate()
            ev.print_report(report)
        except Exception as e:
            print(f"  Skipped ({e})")
