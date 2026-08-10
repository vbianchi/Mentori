#!/usr/bin/env python3
"""
Cross-Document Question Generator for V4 Experiments.

Reads the content analysis from all 50 paper draft JSONs, then uses Gemini
to generate candidate cross-document questions — questions that require
information from 2-4 papers to answer.

Questions are stratified by min_core level (which papers must be indexed):
  - min_core=5  →  5 questions spanning papers 1-5
  - min_core=10 →  5 questions spanning papers 1-10 (must use ≥1 paper from 6-10)
  - min_core=20 →  8 questions spanning papers 1-20 (must use ≥1 paper from 11-20)
  - min_core=50 → 12 questions spanning papers 1-50 (must use ≥1 paper from 21-50)

Total: 30 cross-document questions.

Usage:
    # Generate all 30 cross-document questions
    uv run python tests/experiments_v4/cross_doc_generator.py generate

    # Generate only a specific min_core level
    uv run python tests/experiments_v4/cross_doc_generator.py generate --min-core 5

    # Export review CSV (after generation)
    uv run python tests/experiments_v4/cross_doc_generator.py export-review

    # Import reviewed CSV
    uv run python tests/experiments_v4/cross_doc_generator.py import-review reviewed_crossdoc.csv

    # Use a different Gemini model
    uv run python tests/experiments_v4/cross_doc_generator.py generate --model gemini-2.0-flash
"""

import argparse
import asyncio
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.experiments_v4.paper_processor import _get_gemini_api_key, DEFAULT_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cross_doc_generator")

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────

DATASETS_DIR = PROJECT_ROOT / "datasets"
CORPUS_METADATA = DATASETS_DIR / "v4_papers" / "corpus_metadata.json"
QUESTIONS_DRAFT_DIR = DATASETS_DIR / "questions_draft"
QUESTIONS_DIR = DATASETS_DIR / "questions"
OUTPUT_FILE = QUESTIONS_DIR / "cross_document_draft.json"
REVIEW_CSV = DATASETS_DIR / "review_crossdoc.csv"

# ─────────────────────────────────────────────────────────────
# Cross-doc targets: {min_core: (paper_ids_pool, count, new_range_label)}
# At each level, questions MUST involve ≥1 paper from the "new" range.
# ─────────────────────────────────────────────────────────────

CROSS_DOC_TARGETS = {
    5:  {"pool": list(range(1, 6)),   "count": 5,  "new_range": (1, 5),   "new_label": "papers 1-5"},
    10: {"pool": list(range(1, 11)),  "count": 5,  "new_range": (6, 10),  "new_label": "papers 6-10"},
    20: {"pool": list(range(1, 21)),  "count": 8,  "new_range": (11, 20), "new_label": "papers 11-20"},
    50: {"pool": list(range(1, 51)),  "count": 12, "new_range": (21, 50), "new_label": "papers 21-50"},
}

# ─────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────

CROSS_DOC_PROMPT = """You are creating cross-document evaluation questions for a scientific RAG (Retrieval-Augmented Generation) system.

REQUIREMENT: Each question MUST require information from exactly 2-4 papers listed below to answer.
No single paper can fully answer the question on its own.
{new_range_instruction}

Available papers (min_core={min_core}):
{paper_summaries}

Generate exactly {count} cross-document questions. Each question must:
1. Require synthesis of information from 2-4 papers (explicitly reference source papers)
2. NOT be answerable from any single paper alone
3. Test meaningful relationships: comparisons, complementary findings, shared methods, contrasting approaches
4. Have a clear, verifiable expected answer grounded in the papers

For each question provide:
- question: clear, specific question text ending with "?"
- source_papers: list of filenames (2-4 papers) required to answer
- expected_answer: 3-5 sentence answer explicitly synthesizing the source papers
- expected_concepts: 4-8 key terms that should appear in a correct answer
- difficulty: "medium" or "hard" (cross-doc questions are never "easy")
- comparison_type: one of "comparison", "complementary", "shared_method", "contrasting", "sequential"

Return as a JSON array of {count} objects:
[
  {{
    "question": "...",
    "source_papers": ["01_sarek.pdf", "03_nfcore_framework.pdf"],
    "expected_answer": "...",
    "expected_concepts": ["term1", "term2", "term3"],
    "difficulty": "hard",
    "comparison_type": "comparison"
  }},
  ...
]

Return ONLY the JSON array, no other text.
"""


def _build_paper_summary(draft: Dict[str, Any]) -> str:
    """Build a compact summary of a paper from its draft JSON."""
    ca = draft.get("content_analysis", {})
    meta = draft.get("metadata", {})

    title = meta.get("title") or draft["paper_id"]
    filename = draft["filename"]
    rq = ca.get("research_question", "")
    methods = ca.get("methods", [])[:4]  # top 4 methods to keep prompt short
    findings = ca.get("findings", [])[:3]  # top 3 findings
    terms = ca.get("technical_terms", [])[:6]

    finding_texts = [f.get("finding", "") for f in findings if isinstance(f, dict)]

    lines = [
        f"[{filename}] {title}",
        f"  Research question: {rq}",
        f"  Methods: {', '.join(methods)}",
        f"  Key findings: {'; '.join(finding_texts)}",
        f"  Key terms: {', '.join(terms)}",
    ]
    return "\n".join(lines)


def _load_paper_summaries() -> Dict[int, Dict[str, Any]]:
    """Load all paper summaries indexed by paper ID."""
    corpus = json.loads(CORPUS_METADATA.read_text())
    paper_list = corpus["paper_list"]

    summaries: Dict[int, Dict[str, Any]] = {}
    for entry in paper_list:
        paper_id = entry["id"]
        # Derive draft filename from the PDF filename stem
        stem = Path(entry["file"]).stem
        draft_file = QUESTIONS_DRAFT_DIR / f"{stem}_draft.json"

        if not draft_file.exists():
            logger.warning(f"Draft not found for paper {paper_id}: {draft_file}")
            continue

        draft = json.loads(draft_file.read_text())
        summaries[paper_id] = {
            "paper_id": draft["paper_id"],
            "filename": draft["filename"],
            "summary_text": _build_paper_summary(draft),
        }

    logger.info(f"Loaded {len(summaries)} paper summaries")
    return summaries


async def _generate_for_level(
    client: Any,
    model_name: str,
    min_core: int,
    pool_ids: List[int],
    count: int,
    new_range: tuple,
    new_label: str,
    summaries: Dict[int, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate cross-doc questions for one min_core level."""
    # Build paper summaries string
    paper_texts = []
    for pid in pool_ids:
        if pid in summaries:
            paper_texts.append(summaries[pid]["summary_text"])

    if not paper_texts:
        logger.error(f"No summaries available for pool {pool_ids}")
        return []

    paper_summaries_str = "\n\n".join(paper_texts)

    # For levels > 5, require questions to involve at least one paper from the new range
    if new_range[0] == 1 and new_range[1] == 5:
        # First level: no restriction, all papers are "new"
        new_range_instruction = (
            f"All questions should draw on papers from the pool (papers 1-5)."
        )
    else:
        new_range_instruction = (
            f"IMPORTANT: Each question MUST involve at least one paper from {new_label} "
            f"(filenames matching IDs {new_range[0]}-{new_range[1]}). "
            f"These are new papers not covered in lower min_core levels."
        )

    prompt = CROSS_DOC_PROMPT.format(
        min_core=min_core,
        count=count,
        paper_summaries=paper_summaries_str,
        new_range_instruction=new_range_instruction,
    )

    logger.info(f"Generating {count} cross-doc questions for min_core={min_core} "
                f"({len(paper_texts)} paper summaries in prompt)...")

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = response.text.strip()

        # Extract JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start < 0 or end <= start:
            logger.error(f"No JSON array found in response for min_core={min_core}")
            logger.debug(f"Response: {text[:500]}")
            return []

        raw_questions = json.loads(text[start:end])

    except Exception as e:
        logger.error(f"Gemini call failed for min_core={min_core}: {e}")
        return []

    # Enrich with metadata and assign IDs
    # Count existing questions to assign sequential IDs
    existing = _load_existing_questions()
    base_id = len(existing) + 1

    questions = []
    for i, q in enumerate(raw_questions[:count]):
        q_id = f"CD_{base_id + i:03d}"
        questions.append({
            "id": q_id,
            "question": q.get("question", ""),
            "category": "cross_document",
            "min_core": min_core,
            "source_papers": q.get("source_papers", []),
            "expected_answer": q.get("expected_answer", ""),
            "expected_concepts": q.get("expected_concepts", []),
            "difficulty": q.get("difficulty", "hard"),
            "comparison_type": q.get("comparison_type", "comparison"),
            "requires_iteration": True,
            "answerable": True,
            "status": "pending",
        })

    logger.info(f"  Generated {len(questions)} questions for min_core={min_core}")
    return questions


def _load_existing_questions() -> List[Dict[str, Any]]:
    """Load already-generated cross-doc questions from disk."""
    if OUTPUT_FILE.exists():
        data = json.loads(OUTPUT_FILE.read_text())
        return data.get("questions", [])
    return []


def _save_questions(questions: List[Dict[str, Any]]) -> None:
    """Save questions to the draft output file."""
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "version": "v4",
        "category": "cross_document",
        "generated_at": datetime.now().isoformat(),
        "total": len(questions),
        "by_min_core": {
            str(mc): len([q for q in questions if q["min_core"] == mc])
            for mc in [5, 10, 20, 50]
        },
        "questions": questions,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    logger.info(f"Saved {len(questions)} questions to {OUTPUT_FILE}")


async def generate(
    min_core_filter: Optional[int] = None,
    model_name: str = DEFAULT_MODEL,
) -> None:
    """Generate cross-document questions for all or a specific min_core level."""
    from google import genai as genai_sdk

    api_key = _get_gemini_api_key()
    client = genai_sdk.Client(api_key=api_key)
    logger.info(f"Initialized Gemini model: {model_name}")

    summaries = _load_paper_summaries()
    existing = _load_existing_questions()

    targets = CROSS_DOC_TARGETS
    if min_core_filter is not None:
        if min_core_filter not in targets:
            raise ValueError(f"Invalid min_core: {min_core_filter}. Choose from {list(targets)}")
        targets = {min_core_filter: targets[min_core_filter]}

    all_questions = list(existing)  # preserve already-generated questions

    for min_core, cfg in sorted(targets.items()):
        # Skip if already generated for this level
        already = [q for q in all_questions if q["min_core"] == min_core]
        if already and min_core_filter is None:
            logger.info(f"Skipping min_core={min_core}: {len(already)} questions already exist")
            continue

        new_questions = await _generate_for_level(
            client=client,
            model_name=model_name,
            min_core=min_core,
            pool_ids=cfg["pool"],
            count=cfg["count"],
            new_range=cfg["new_range"],
            new_label=cfg["new_label"],
            summaries=summaries,
        )

        # Remove old questions for this level if regenerating
        if min_core_filter is not None:
            all_questions = [q for q in all_questions if q["min_core"] != min_core]

        all_questions.extend(new_questions)
        _save_questions(all_questions)

        # Rate limit between levels
        await asyncio.sleep(3)

    print(f"\nDone. Total cross-document questions: {len(all_questions)}")
    _print_summary(all_questions)


def _print_summary(questions: List[Dict[str, Any]]) -> None:
    by_level = {}
    for q in questions:
        mc = q["min_core"]
        by_level.setdefault(mc, []).append(q)

    print("\nBreakdown by min_core:")
    for mc in sorted(by_level):
        qs = by_level[mc]
        print(f"  min_core={mc:2d}: {len(qs):2d} questions")
    print(f"\nOutput: {OUTPUT_FILE}")


def export_review_csv() -> Path:
    """Export cross-doc questions to a review CSV."""
    if not OUTPUT_FILE.exists():
        raise FileNotFoundError(f"No cross-doc questions found. Run 'generate' first.")

    data = json.loads(OUTPUT_FILE.read_text())
    questions = data.get("questions", [])

    rows = []
    for q in questions:
        rows.append({
            "q_id": q["id"],
            "min_core": q["min_core"],
            "source_papers": ", ".join(q.get("source_papers", [])),
            "comparison_type": q.get("comparison_type", ""),
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "expected_concepts": ", ".join(q.get("expected_concepts", [])),
            "difficulty": q["difficulty"],
            "status": "PENDING",
            "reviewer_notes": "",
            "corrected_answer": "",
            "corrected_concepts": "",
            "corrected_source_papers": "",
        })

    REVIEW_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Exported {len(rows)} questions to {REVIEW_CSV}")
    return REVIEW_CSV


def import_review_csv(csv_path: Path) -> None:
    """Import reviewed CSV and update the draft JSON."""
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = {row["q_id"]: row for row in reader}

    data = json.loads(OUTPUT_FILE.read_text())
    questions = data["questions"]

    for q in questions:
        row = rows.get(q["id"])
        if not row:
            continue

        q["status"] = row["status"].lower()
        q["reviewer_notes"] = row.get("reviewer_notes", "")

        if row.get("corrected_answer"):
            q["expected_answer"] = row["corrected_answer"]
        if row.get("corrected_concepts"):
            q["expected_concepts"] = [c.strip() for c in row["corrected_concepts"].split(",")]
        if row.get("corrected_source_papers"):
            q["source_papers"] = [p.strip() for p in row["corrected_source_papers"].split(",")]

    _save_questions(questions)

    accepted = [q for q in questions if q.get("status") in ("accept", "modify")]
    print(f"Imported review: {len(accepted)}/{len(questions)} accepted/modified")


def main():
    parser = argparse.ArgumentParser(description="Generate cross-document questions")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate cross-doc questions")
    gen_parser.add_argument(
        "--min-core",
        type=int,
        choices=[5, 10, 20, 50],
        help="Generate only for this min_core level (default: all levels)",
    )

    # export-review
    subparsers.add_parser("export-review", help="Export questions to review CSV")

    # import-review
    import_parser = subparsers.add_parser("import-review", help="Import reviewed CSV")
    import_parser.add_argument("csv_path", type=Path, help="Path to reviewed CSV")

    # status
    subparsers.add_parser("status", help="Show current generation status")

    args = parser.parse_args()

    if args.command == "generate":
        asyncio.run(generate(
            min_core_filter=args.min_core,
            model_name=args.model,
        ))

    elif args.command == "export-review":
        out = export_review_csv()
        print(f"Review CSV exported to {out}")

    elif args.command == "import-review":
        import_review_csv(args.csv_path)

    elif args.command == "status":
        existing = _load_existing_questions()
        if not existing:
            print("No cross-doc questions generated yet.")
        else:
            _print_summary(existing)
            pending = [q for q in existing if q.get("status") == "pending"]
            accepted = [q for q in existing if q.get("status") in ("accept", "modify")]
            print(f"\nReview status: {len(accepted)} accepted, {len(pending)} pending review")


if __name__ == "__main__":
    main()
