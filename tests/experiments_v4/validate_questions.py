#!/usr/bin/env python3
"""
Question Validation for V4 Experiments.

Validates ground truth questions against the V4 schema:
- Required fields present
- Valid categories and difficulty levels
- Proper min_core assignments
- No duplicate IDs
- Concept coverage checks

Usage:
    # Validate ground truth
    uv run python tests/experiments_v4/validate_questions.py validate

    # Validate specific file
    uv run python tests/experiments_v4/validate_questions.py validate path/to/questions.json

    # Generate validation report
    uv run python tests/experiments_v4/validate_questions.py report

    # Merge question files into ground_truth_v4.json
    uv run python tests/experiments_v4/validate_questions.py merge
"""

import argparse
import json
import logging
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validate_questions")

# Directories
DATASETS_DIR = PROJECT_ROOT / "datasets"
QUESTIONS_DIR = DATASETS_DIR / "questions"
GROUND_TRUTH_FILE = DATASETS_DIR / "ground_truth_v4.json"

# Valid values
VALID_CATEGORIES = {
    "factual_recall",
    "conceptual",
    "technical",
    "cross_document",
    "synthesis",
    "out_of_domain",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}

VALID_MIN_CORE = {5, 10, 20, 50}

# Required fields per question type
REQUIRED_FIELDS = {
    "all": ["id", "question", "category", "answerable"],
    "answerable": ["expected_answer", "expected_concepts", "source_files", "min_core"],
    "unanswerable": [],  # OOD questions have fewer requirements
}


@dataclass
class ValidationError:
    """A single validation error."""
    question_id: str
    field: str
    message: str
    severity: str = "error"  # error, warning


@dataclass
class ValidationResult:
    """Result of validating a question set."""
    total_questions: int = 0
    valid_questions: int = 0
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, q_id: str, field_name: str, message: str) -> None:
        self.errors.append(ValidationError(q_id, field_name, message, "error"))

    def add_warning(self, q_id: str, field_name: str, message: str) -> None:
        self.warnings.append(ValidationError(q_id, field_name, message, "warning"))


def validate_question(question: Dict[str, Any], seen_ids: Set[str]) -> List[ValidationError]:
    """Validate a single question against the schema."""
    errors = []
    q_id = question.get("id", "UNKNOWN")

    # Check required fields for all questions
    for field_name in REQUIRED_FIELDS["all"]:
        if field_name not in question or question[field_name] is None:
            errors.append(ValidationError(q_id, field_name, f"Missing required field: {field_name}"))

    # Check for duplicate IDs
    if q_id in seen_ids:
        errors.append(ValidationError(q_id, "id", f"Duplicate question ID: {q_id}"))
    seen_ids.add(q_id)

    # Validate category
    category = question.get("category")
    if category and category not in VALID_CATEGORIES:
        errors.append(ValidationError(
            q_id, "category",
            f"Invalid category '{category}'. Valid: {VALID_CATEGORIES}"
        ))

    # Validate difficulty if present
    difficulty = question.get("difficulty")
    if difficulty and difficulty not in VALID_DIFFICULTIES:
        errors.append(ValidationError(
            q_id, "difficulty",
            f"Invalid difficulty '{difficulty}'. Valid: {VALID_DIFFICULTIES}"
        ))

    # Check answerable-specific fields
    answerable = question.get("answerable", True)
    if answerable:
        for field_name in REQUIRED_FIELDS["answerable"]:
            if field_name not in question or question[field_name] is None:
                errors.append(ValidationError(
                    q_id, field_name,
                    f"Missing required field for answerable question: {field_name}"
                ))

        # Validate min_core
        min_core = question.get("min_core")
        if min_core is not None and min_core not in VALID_MIN_CORE:
            errors.append(ValidationError(
                q_id, "min_core",
                f"Invalid min_core '{min_core}'. Valid: {VALID_MIN_CORE}"
            ))

        # Validate expected_concepts is a non-empty list
        concepts = question.get("expected_concepts", [])
        if not isinstance(concepts, list) or len(concepts) < 2:
            errors.append(ValidationError(
                q_id, "expected_concepts",
                f"expected_concepts should be a list with at least 2 items"
            ))

        # Validate source_files is a non-empty list
        source_files = question.get("source_files", [])
        if not isinstance(source_files, list) or len(source_files) == 0:
            errors.append(ValidationError(
                q_id, "source_files",
                f"source_files should be a non-empty list"
            ))

        # Validate expected_answer length
        answer = question.get("expected_answer", "")
        if len(answer) < 20:
            errors.append(ValidationError(
                q_id, "expected_answer",
                f"expected_answer is too short ({len(answer)} chars, min 20)"
            ))

    # Validate question text
    question_text = question.get("question", "")
    if not question_text.endswith("?"):
        errors.append(ValidationError(
            q_id, "question",
            "Question should end with a question mark"
        ))

    return errors


def validate_questions_file(file_path: Path) -> ValidationResult:
    """Validate all questions in a file."""
    result = ValidationResult()

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error("FILE", "json", f"Invalid JSON: {e}")
        return result
    except FileNotFoundError:
        result.add_error("FILE", "path", f"File not found: {file_path}")
        return result

    # Handle both formats: {"questions": [...]} or [...]
    questions = data.get("questions", data) if isinstance(data, dict) else data
    if not isinstance(questions, list):
        result.add_error("FILE", "format", "Expected a list of questions")
        return result

    result.total_questions = len(questions)
    seen_ids: Set[str] = set()

    for question in questions:
        errors = validate_question(question, seen_ids)
        if errors:
            for error in errors:
                if error.severity == "error":
                    result.errors.append(error)
                else:
                    result.warnings.append(error)
        else:
            result.valid_questions += 1

    return result


def validate_ground_truth() -> ValidationResult:
    """Validate the main ground truth file."""
    return validate_questions_file(GROUND_TRUTH_FILE)


def generate_report(result: ValidationResult, output_path: Optional[Path] = None) -> str:
    """Generate a validation report."""
    lines = [
        "# V4 Ground Truth Validation Report",
        "",
        f"**Total Questions**: {result.total_questions}",
        f"**Valid Questions**: {result.valid_questions}",
        f"**Errors**: {len(result.errors)}",
        f"**Warnings**: {len(result.warnings)}",
        "",
    ]

    if result.is_valid:
        lines.append("**Status**: PASSED")
    else:
        lines.append("**Status**: FAILED")

    if result.errors:
        lines.extend(["", "## Errors", ""])
        for error in result.errors:
            lines.append(f"- **{error.question_id}** [{error.field}]: {error.message}")

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in result.warnings:
            lines.append(f"- **{warning.question_id}** [{warning.field}]: {warning.message}")

    report = "\n".join(lines)

    if output_path:
        output_path.write_text(report)
        logger.info(f"Report saved to {output_path}")

    return report


def merge_question_files() -> None:
    """Merge all question files into ground_truth_v4.json."""
    all_questions = []
    seen_ids: Set[str] = set()

    # Question file mappings
    files_to_merge = {
        "paper_level.json": {"answerable": True},
        "cross_document.json": {"answerable": True},
        "synthesis.json": {"answerable": True},
        "out_of_domain.json": {"answerable": False},
    }

    for filename, defaults in files_to_merge.items():
        file_path = QUESTIONS_DIR / filename
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        with open(file_path) as f:
            data = json.load(f)

        questions = data.get("questions", data) if isinstance(data, dict) else data

        for q in questions:
            # Apply defaults
            for key, value in defaults.items():
                if key not in q:
                    q[key] = value

            # Check for duplicates
            if q["id"] in seen_ids:
                logger.warning(f"Skipping duplicate ID: {q['id']}")
                continue

            seen_ids.add(q["id"])
            all_questions.append(q)

    # Validate merged result
    seen_ids.clear()
    errors = []
    for q in all_questions:
        errors.extend(validate_question(q, seen_ids))

    if errors:
        logger.error(f"Validation errors in merged result: {len(errors)}")
        for error in errors[:10]:  # Show first 10
            logger.error(f"  {error.question_id}: {error.message}")
        if len(errors) > 10:
            logger.error(f"  ... and {len(errors) - 10} more")

    # Write merged file
    output = {
        "version": "v4",
        "created": str(Path(__file__).name),
        "total_questions": len(all_questions),
        "questions": all_questions,
    }

    with open(GROUND_TRUTH_FILE, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Merged {len(all_questions)} questions into {GROUND_TRUTH_FILE}")

    # Print category distribution
    categories = Counter(q.get("category") for q in all_questions)
    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Print min_core distribution
    min_cores = Counter(q.get("min_core") for q in all_questions if q.get("answerable", True))
    print("\nmin_core distribution (answerable questions):")
    for core, count in sorted(min_cores.items()):
        print(f"  {core}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Validate V4 ground truth questions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate questions")
    validate_parser.add_argument(
        "file_path",
        type=Path,
        nargs="?",
        default=GROUND_TRUTH_FILE,
        help="Path to questions file (default: ground_truth_v4.json)",
    )

    # report command
    report_parser = subparsers.add_parser("report", help="Generate validation report")
    report_parser.add_argument(
        "--output",
        type=Path,
        help="Output path for report",
    )

    # merge command
    subparsers.add_parser("merge", help="Merge question files into ground_truth_v4.json")

    args = parser.parse_args()

    if args.command == "validate":
        result = validate_questions_file(args.file_path)
        print(f"\nValidation {'PASSED' if result.is_valid else 'FAILED'}")
        print(f"  Total: {result.total_questions}")
        print(f"  Valid: {result.valid_questions}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Warnings: {len(result.warnings)}")

        if not result.is_valid:
            print("\nErrors:")
            for error in result.errors[:10]:
                print(f"  - {error.question_id}: {error.message}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more")
            sys.exit(1)

    elif args.command == "report":
        result = validate_questions_file(GROUND_TRUTH_FILE)
        report = generate_report(result, args.output)
        if not args.output:
            print(report)

    elif args.command == "merge":
        merge_question_files()


if __name__ == "__main__":
    main()
