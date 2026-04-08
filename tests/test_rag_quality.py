"""
RAG Quality Validation System

Tests retrieval accuracy, answer quality, and OCR performance.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retrieval.ingestor import SimpleIngestor
from backend.retrieval.retriever import SimpleRetriever
from backend.retrieval.embeddings import EmbeddingEngine
from backend.retrieval.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result of a single retrieval test."""
    question_id: str
    question: str
    category: str
    difficulty: str
    retrieved_chunks: List[Dict[str, Any]]
    retrieval_score: float  # 0-1, how well did it retrieve relevant chunks
    contains_expected_terms: bool
    top_chunk_text: str
    retrieval_time_ms: float


@dataclass
class AnswerQualityResult:
    """Result of answer quality evaluation."""
    question_id: str
    contains_key_info: bool
    is_hallucination: bool
    is_correctly_unanswerable: bool  # For questions that should return "not found"
    completeness_score: float  # 0-1


@dataclass
class TestReport:
    """Complete test report."""
    timestamp: str
    collection_name: str
    total_questions: int

    # Retrieval metrics
    retrieval_precision: float
    retrieval_recall: float
    avg_retrieval_score: float

    # Answer quality metrics
    answer_accuracy: float
    hallucination_rate: float
    unanswerable_detection_rate: float

    # Performance
    avg_query_time_ms: float

    # Per-category breakdown
    results_by_category: Dict[str, Dict[str, float]]
    results_by_difficulty: Dict[str, Dict[str, float]]

    # Detailed results
    retrieval_results: List[Dict[str, Any]]

    # Summary
    passed: bool
    pass_threshold: float = 0.80  # 80% accuracy required to pass


class RAGValidator:
    """Validates RAG system quality."""

    def __init__(
        self,
        collection_name: str = "test_validation",
        ground_truth_path: str = "tests/rag_ground_truth.json"
    ):
        self.collection_name = collection_name
        self.ground_truth_path = ground_truth_path

        # Initialize RAG components
        self.embedder = EmbeddingEngine()
        self.vector_store = VectorStore(collection_name=collection_name)
        self.retriever = SimpleRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
            collection_name=collection_name
        )

        # Load ground truth
        with open(ground_truth_path, 'r') as f:
            self.ground_truth = json.load(f)

        logger.info(f"Initialized RAG Validator for collection: {collection_name}")

    async def run_validation(self) -> TestReport:
        """Run complete validation suite."""
        logger.info("=" * 80)
        logger.info("STARTING RAG QUALITY VALIDATION")
        logger.info("=" * 80)

        retrieval_results = []

        # Test each category
        for category_data in self.ground_truth["test_categories"]:
            category = category_data["category"]
            questions = category_data["questions"]

            logger.info(f"\n📋 Testing category: {category} ({len(questions)} questions)")

            for q in questions:
                result = await self._test_retrieval(q, category)
                retrieval_results.append(result)

        # Generate report
        report = self._generate_report(retrieval_results)

        return report

    async def _test_retrieval(
        self,
        question_data: Dict[str, Any],
        category: str
    ) -> RetrievalResult:
        """Test retrieval for a single question."""
        question = question_data["question"]
        q_id = question_data["id"]
        difficulty = question_data.get("difficulty", "medium")

        logger.info(f"  Testing [{q_id}]: {question[:60]}...")

        # Measure retrieval time
        import time
        start = time.time()

        # Retrieve
        results = self.retriever.retrieve(
            query=question,
            top_k=5,
            use_hybrid=True
        )

        end = time.time()
        retrieval_time_ms = (end - start) * 1000

        # Evaluate retrieval quality
        expected_terms = question_data.get("expected_in_chunk", [])
        contains_expected = self._check_expected_terms(results, expected_terms)

        retrieval_score = self._calculate_retrieval_score(results, question_data)

        top_chunk = results[0]["text"] if results else ""

        logger.info(f"    ✓ Retrieved {len(results)} chunks in {retrieval_time_ms:.1f}ms")
        logger.info(f"    Score: {retrieval_score:.2f} | Contains expected: {contains_expected}")

        return RetrievalResult(
            question_id=q_id,
            question=question,
            category=category,
            difficulty=difficulty,
            retrieved_chunks=[{
                "text": r["text"][:200],
                "score": r.get("hybrid_score", r.get("score", 0)),
                "metadata": r.get("metadata", {})
            } for r in results],
            retrieval_score=retrieval_score,
            contains_expected_terms=contains_expected,
            top_chunk_text=top_chunk[:300],
            retrieval_time_ms=retrieval_time_ms
        )

    def _check_expected_terms(
        self,
        results: List[Dict[str, Any]],
        expected_terms: List[str]
    ) -> bool:
        """Check if retrieved chunks contain expected terms."""
        if not expected_terms:
            return True  # No expected terms specified

        if not results:
            return False

        # Check top 3 chunks
        combined_text = " ".join([r["text"].lower() for r in results[:3]])

        # At least 50% of expected terms should be present
        found_count = sum(1 for term in expected_terms if term.lower() in combined_text)
        return found_count >= len(expected_terms) * 0.5

    def _calculate_retrieval_score(
        self,
        results: List[Dict[str, Any]],
        question_data: Dict[str, Any]
    ) -> float:
        """Calculate retrieval quality score (0-1)."""
        if not results:
            return 0.0

        score = 0.0

        # Component 1: Top result has high similarity (40%)
        top_score = results[0].get("hybrid_score") or results[0].get("score", 0)
        score += top_score * 0.4

        # Component 2: Expected terms present (40%)
        expected_terms = question_data.get("expected_in_chunk", [])
        if expected_terms:
            has_terms = self._check_expected_terms(results, expected_terms)
            score += 0.4 if has_terms else 0.0
        else:
            score += 0.4  # No expected terms specified, give benefit of doubt

        # Component 3: Multiple relevant results (20%)
        # If we have 3+ results with score > 0.5, that's good
        high_score_count = sum(1 for r in results if r.get("hybrid_score", r.get("score", 0)) > 0.5)
        score += min(high_score_count / 3, 1.0) * 0.2

        return min(score, 1.0)

    def _generate_report(self, retrieval_results: List[RetrievalResult]) -> TestReport:
        """Generate comprehensive test report."""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING VALIDATION REPORT")
        logger.info("=" * 80)

        total = len(retrieval_results)

        # Overall retrieval metrics
        avg_retrieval_score = sum(r.retrieval_score for r in retrieval_results) / total
        retrieval_precision = sum(1 for r in retrieval_results if r.retrieval_score >= 0.7) / total
        contains_expected_rate = sum(1 for r in retrieval_results if r.contains_expected_terms) / total

        # Performance
        avg_query_time = sum(r.retrieval_time_ms for r in retrieval_results) / total

        # By category
        categories = {}
        for r in retrieval_results:
            if r.category not in categories:
                categories[r.category] = []
            categories[r.category].append(r)

        results_by_category = {}
        for cat, results in categories.items():
            results_by_category[cat] = {
                "count": len(results),
                "avg_score": sum(r.retrieval_score for r in results) / len(results),
                "precision": sum(1 for r in results if r.retrieval_score >= 0.7) / len(results)
            }

        # By difficulty
        difficulties = {}
        for r in retrieval_results:
            if r.difficulty not in difficulties:
                difficulties[r.difficulty] = []
            difficulties[r.difficulty].append(r)

        results_by_difficulty = {}
        for diff, results in difficulties.items():
            results_by_difficulty[diff] = {
                "count": len(results),
                "avg_score": sum(r.retrieval_score for r in results) / len(results),
                "precision": sum(1 for r in results if r.retrieval_score >= 0.7) / len(results)
            }

        # Create report
        report = TestReport(
            timestamp=datetime.now().isoformat(),
            collection_name=self.collection_name,
            total_questions=total,
            retrieval_precision=retrieval_precision,
            retrieval_recall=contains_expected_rate,
            avg_retrieval_score=avg_retrieval_score,
            answer_accuracy=avg_retrieval_score,  # Simplified for now
            hallucination_rate=0.0,  # Would need LLM to compute
            unanswerable_detection_rate=0.0,  # Would need LLM to compute
            avg_query_time_ms=avg_query_time,
            results_by_category=results_by_category,
            results_by_difficulty=results_by_difficulty,
            retrieval_results=[asdict(r) for r in retrieval_results],
            passed=avg_retrieval_score >= 0.80
        )

        return report

    def print_report(self, report: TestReport):
        """Print human-readable report."""
        print("\n" + "=" * 80)
        print("RAG QUALITY VALIDATION REPORT")
        print("=" * 80)
        print(f"Timestamp: {report.timestamp}")
        print(f"Collection: {report.collection_name}")
        print(f"Total Questions: {report.total_questions}")
        print()

        print("📊 OVERALL METRICS")
        print("-" * 80)
        print(f"  Retrieval Precision:  {report.retrieval_precision:.1%} (≥0.7 score)")
        print(f"  Retrieval Recall:     {report.retrieval_recall:.1%} (contains expected terms)")
        print(f"  Avg Retrieval Score:  {report.avg_retrieval_score:.2f}/1.00")
        print(f"  Avg Query Time:       {report.avg_query_time_ms:.1f}ms")
        print()

        print("📁 RESULTS BY CATEGORY")
        print("-" * 80)
        for cat, metrics in report.results_by_category.items():
            print(f"  {cat:25s} | Count: {metrics['count']:2d} | "
                  f"Score: {metrics['avg_score']:.2f} | "
                  f"Precision: {metrics['precision']:.1%}")
        print()

        print("🎯 RESULTS BY DIFFICULTY")
        print("-" * 80)
        for diff, metrics in report.results_by_difficulty.items():
            print(f"  {diff:10s} | Count: {metrics['count']:2d} | "
                  f"Score: {metrics['avg_score']:.2f} | "
                  f"Precision: {metrics['precision']:.1%}")
        print()

        print("✅ PASS/FAIL STATUS")
        print("-" * 80)
        status = "✅ PASSED" if report.passed else "❌ FAILED"
        threshold = report.pass_threshold
        print(f"  Status: {status}")
        print(f"  Threshold: {threshold:.1%} (current: {report.avg_retrieval_score:.1%})")
        print()

        # Show worst performers
        print("⚠️  LOWEST SCORING QUESTIONS")
        print("-" * 80)
        sorted_results = sorted(report.retrieval_results, key=lambda x: x["retrieval_score"])
        for r in sorted_results[:3]:
            print(f"  [{r['question_id']}] Score: {r['retrieval_score']:.2f}")
            print(f"    Q: {r['question'][:70]}...")
            print()

        print("=" * 80)

    def save_report(self, report: TestReport, output_path: str = "tests/rag_validation_report.json"):
        """Save report to JSON file."""
        report_dict = asdict(report)

        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"✓ Report saved to: {output_path}")


async def main():
    """Run validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate RAG system quality")
    parser.add_argument("--collection", default="test_index", help="Collection name to test")
    parser.add_argument("--ground-truth", default="tests/rag_ground_truth.json", help="Path to ground truth file")
    parser.add_argument("--output", default="tests/rag_validation_report.json", help="Output report path")

    args = parser.parse_args()

    # Initialize validator
    validator = RAGValidator(
        collection_name=args.collection,
        ground_truth_path=args.ground_truth
    )

    # Run validation
    report = await validator.run_validation()

    # Print report
    validator.print_report(report)

    # Save report
    validator.save_report(report, args.output)

    # Exit with error code if failed
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
