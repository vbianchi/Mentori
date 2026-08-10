#!/usr/bin/env python3
"""
Build ground_truth_v4.json by merging all 4 question sources into a unified schema.

Sources:
  - 150 paper-level questions (from 50 draft JSONs in datasets/questions_draft/)
  - 30 cross-document questions (datasets/questions/cross_document_draft.json)
  - 20 synthesis questions (datasets/questions/synthesis_draft.json)
  - 50 out-of-domain questions (datasets/questions/out_of_domain.json)

Output: datasets/ground_truth_v4.json (250 questions)

Usage:
    uv run python tests/experiments_v4/build_ground_truth.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
DRAFTS_DIR = DATASETS_DIR / "questions_draft"
QUESTIONS_DIR = DATASETS_DIR / "questions"
OUTPUT_FILE = DATASETS_DIR / "ground_truth_v4.json"


def _paper_number(paper_id: str) -> int:
    """Extract numeric prefix from paper_id like '01_sarek' → 1."""
    m = re.match(r"(\d+)", paper_id)
    return int(m.group(1)) if m else 0


def _min_core_for_paper(paper_num: int) -> int:
    """Determine min_core level based on paper number."""
    if paper_num <= 5:
        return 5
    elif paper_num <= 10:
        return 10
    elif paper_num <= 20:
        return 20
    else:
        return 50


def load_paper_level() -> list:
    """Load 150 paper-level questions from 50 draft JSONs."""
    questions = []
    draft_files = sorted(DRAFTS_DIR.glob("*_draft.json"))

    for draft_path in draft_files:
        data = json.loads(draft_path.read_text())
        paper_id = data.get("paper_id", "")
        filename = data.get("filename", "")
        paper_num = _paper_number(paper_id)
        min_core = _min_core_for_paper(paper_num)

        for dq in data.get("draft_questions", []):
            # Use corrected_answer if available, otherwise expected_answer
            answer = dq.get("corrected_answer") or dq.get("expected_answer", "")

            questions.append({
                "id": dq["q_id"],
                "question": dq["question"],
                "category": dq["category"],
                "subcategory": None,
                "min_core": min_core,
                "source_files": [filename],
                "expected_answer": answer,
                "expected_concepts": dq.get("expected_concepts", []),
                "difficulty": dq.get("difficulty", "medium"),
                "answerable": True,
            })

    return questions


def load_cross_document() -> list:
    """Load 30 cross-document questions."""
    path = QUESTIONS_DIR / "cross_document_draft.json"
    data = json.loads(path.read_text())
    questions = []

    for q in data.get("questions", []):
        questions.append({
            "id": q["id"],
            "question": q["question"],
            "category": "cross_document",
            "subcategory": q.get("comparison_type"),
            "min_core": q["min_core"],
            "source_files": q.get("source_papers", []),
            "expected_answer": q["expected_answer"],
            "expected_concepts": q.get("expected_concepts", []),
            "difficulty": q.get("difficulty", "hard"),
            "answerable": True,
        })

    return questions


def load_synthesis() -> list:
    """Load 20 synthesis questions."""
    path = QUESTIONS_DIR / "synthesis_draft.json"
    data = json.loads(path.read_text())
    questions = []

    for q in data.get("questions", []):
        questions.append({
            "id": q["id"],
            "question": q["question"],
            "category": "synthesis",
            "subcategory": q.get("synthesis_type"),
            "min_core": q["min_core"],
            "source_files": q.get("source_papers", []),
            "expected_answer": q["expected_answer"],
            "expected_concepts": q.get("expected_concepts", []),
            "difficulty": q.get("difficulty", "hard"),
            "answerable": True,
        })

    return questions


def load_ood() -> list:
    """Load 50 out-of-domain questions."""
    path = QUESTIONS_DIR / "out_of_domain.json"
    data = json.loads(path.read_text())
    questions = []

    for q in data.get("questions", []):
        questions.append({
            "id": q["id"],
            "question": q["question"],
            "category": "out_of_domain",
            "subcategory": q.get("ood_type"),
            "min_core": None,
            "source_files": [],
            "expected_answer": q.get("expected_answer", "NOT_IN_CORPUS"),
            "expected_concepts": [],
            "difficulty": None,
            "answerable": False,
        })

    return questions


def build():
    paper_level = load_paper_level()
    cross_doc = load_cross_document()
    synthesis = load_synthesis()
    ood = load_ood()

    all_questions = paper_level + cross_doc + synthesis + ood

    # Verify counts
    print(f"Paper-level:     {len(paper_level)}")
    print(f"Cross-document:  {len(cross_doc)}")
    print(f"Synthesis:       {len(synthesis)}")
    print(f"Out-of-domain:   {len(ood)}")
    print(f"Total:           {len(all_questions)}")

    # Check for duplicate IDs
    ids = [q["id"] for q in all_questions]
    dupes = [x for x in ids if ids.count(x) > 1]
    if dupes:
        print(f"\nWARNING: Duplicate IDs found: {set(dupes)}")

    # Breakdown by min_core (answerable only)
    answerable = [q for q in all_questions if q["answerable"]]
    by_core = {}
    for q in answerable:
        mc = q["min_core"]
        by_core.setdefault(mc, 0)
        by_core[mc] += 1
    print(f"\nAnswerable by min_core:")
    for mc in sorted(by_core):
        print(f"  min_core={mc:2d}: {by_core[mc]} questions")

    # Breakdown by category
    by_cat = {}
    for q in all_questions:
        cat = q["category"]
        by_cat.setdefault(cat, 0)
        by_cat[cat] += 1
    print(f"\nBy category:")
    for cat in sorted(by_cat):
        print(f"  {cat}: {by_cat[cat]}")

    # Build output
    output = {
        "version": "v4",
        "created_at": datetime.now().isoformat(),
        "total_questions": len(all_questions),
        "answerable_questions": len(answerable),
        "ood_questions": len(ood),
        "by_category": by_cat,
        "by_min_core": {str(k): v for k, v in sorted(by_core.items())},
        "questions": all_questions,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"\nWritten to {OUTPUT_FILE}")


if __name__ == "__main__":
    build()
