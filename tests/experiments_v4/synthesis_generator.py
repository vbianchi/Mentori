#!/usr/bin/env python3
"""
Synthesis Question Generator for V4 Experiments.

Reads content analysis from all 50 paper draft JSONs, then uses Gemini
to generate synthesis questions — questions requiring integration of 3+
papers to form novel summaries, identify themes, or draw meta-conclusions.

Questions are stratified by min_core level:
  - min_core=5  →  2 questions spanning papers 1-5
  - min_core=10 →  2 questions spanning papers 1-10 (must use ≥1 from 6-10)
  - min_core=20 →  6 questions spanning papers 1-20 (must use ≥1 from 11-20)
  - min_core=50 → 10 questions spanning papers 1-50 (must use ≥1 from 21-50)

Total: 20 synthesis questions.

Usage:
    uv run python tests/experiments_v4/synthesis_generator.py generate
    uv run python tests/experiments_v4/synthesis_generator.py --model gemini-3-flash-preview generate
    uv run python tests/experiments_v4/synthesis_generator.py generate --min-core 5
    uv run python tests/experiments_v4/synthesis_generator.py status
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.experiments_v4.paper_processor import _get_gemini_api_key, DEFAULT_MODEL
from tests.experiments_v4.cross_doc_generator import _build_paper_summary, _load_paper_summaries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("synthesis_generator")

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────

DATASETS_DIR = PROJECT_ROOT / "datasets"
QUESTIONS_DIR = DATASETS_DIR / "questions"
OUTPUT_FILE = QUESTIONS_DIR / "synthesis_draft.json"

# ─────────────────────────────────────────────────────────────
# Targets
# ─────────────────────────────────────────────────────────────

SYNTHESIS_TARGETS = {
    5:  {"pool": list(range(1, 6)),   "count": 2,  "new_range": (1, 5),   "new_label": "papers 1-5"},
    10: {"pool": list(range(1, 11)),  "count": 2,  "new_range": (6, 10),  "new_label": "papers 6-10"},
    20: {"pool": list(range(1, 21)),  "count": 6,  "new_range": (11, 20), "new_label": "papers 11-20"},
    50: {"pool": list(range(1, 51)),  "count": 10, "new_range": (21, 50), "new_label": "papers 21-50"},
}

# ─────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """You are creating SYNTHESIS evaluation questions for a scientific RAG system.

Synthesis questions are DIFFERENT from cross-document comparison questions:
- They require integrating information from 3-6 papers (not just comparing 2)
- They test the ability to identify THEMES, TRENDS, and META-CONCLUSIONS across the corpus
- The answer should be a novel synthesis that no single paper states explicitly
- They go BEYOND pairwise comparison to corpus-wide integration

{new_range_instruction}

Available papers (min_core={min_core}):
{paper_summaries}

Generate exactly {count} synthesis questions. Each question must:
1. Require integration of 3-6 papers to answer (list all source papers)
2. NOT be answerable from any single paper or pair of papers alone
3. Test one of these synthesis types:
   - theme_analysis: Identify a recurring theme across multiple papers
   - methodology_comparison: Compare how different papers approach similar problems
   - trend_identification: Identify trends or patterns across the corpus
   - meta_conclusion: Draw a conclusion that emerges from multiple papers together
   - gap_analysis: Identify gaps or limitations visible only when viewing multiple papers
4. Require actual SYNTHESIS — not just listing facts from each paper

For each question provide:
- question: clear, specific question ending with "?"
- source_papers: list of filenames (3-6 papers) required to answer
- expected_answer: 4-6 sentence answer that genuinely synthesizes across papers
- expected_concepts: 5-8 key terms from multiple papers
- difficulty: "hard" (synthesis questions are always hard)
- synthesis_type: one of "theme_analysis", "methodology_comparison", "trend_identification", "meta_conclusion", "gap_analysis"

Return as a JSON array of {count} objects:
[
  {{
    "question": "...",
    "source_papers": ["01_sarek.pdf", "02_snakemake.pdf", "03_nfcore_framework.pdf"],
    "expected_answer": "...",
    "expected_concepts": ["term1", "term2", "term3"],
    "difficulty": "hard",
    "synthesis_type": "theme_analysis"
  }},
  ...
]

Return ONLY the JSON array, no other text.
"""


# ─────────────────────────────────────────────────────────────
# Generation
# ─────────────────────────────────────────────────────────────

def _load_existing_questions() -> List[Dict[str, Any]]:
    if OUTPUT_FILE.exists():
        data = json.loads(OUTPUT_FILE.read_text())
        return data.get("questions", [])
    return []


def _save_questions(questions: List[Dict[str, Any]]) -> None:
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "version": "v4",
        "category": "synthesis",
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
    """Generate synthesis questions for one min_core level."""
    paper_texts = []
    for pid in pool_ids:
        if pid in summaries:
            paper_texts.append(summaries[pid]["summary_text"])

    if not paper_texts:
        logger.error(f"No summaries available for pool {pool_ids}")
        return []

    paper_summaries_str = "\n\n".join(paper_texts)

    if new_range[0] == 1 and new_range[1] == 5:
        new_range_instruction = (
            "All questions should draw on papers from the pool (papers 1-5). "
            "Each question must span at least 3 papers."
        )
    else:
        new_range_instruction = (
            f"IMPORTANT: Each question MUST involve at least one paper from {new_label} "
            f"(filenames matching IDs {new_range[0]}-{new_range[1]}). "
            f"Each question must span at least 3 papers."
        )

    prompt = SYNTHESIS_PROMPT.format(
        min_core=min_core,
        count=count,
        paper_summaries=paper_summaries_str,
        new_range_instruction=new_range_instruction,
    )

    logger.info(f"Generating {count} synthesis questions for min_core={min_core} "
                f"({len(paper_texts)} paper summaries in prompt)...")

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = response.text.strip()

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

    existing = _load_existing_questions()
    base_id = len(existing) + 1

    questions = []
    for i, q in enumerate(raw_questions[:count]):
        q_id = f"SY_{base_id + i:03d}"
        questions.append({
            "id": q_id,
            "question": q.get("question", ""),
            "category": "synthesis",
            "min_core": min_core,
            "source_papers": q.get("source_papers", []),
            "expected_answer": q.get("expected_answer", ""),
            "expected_concepts": q.get("expected_concepts", []),
            "difficulty": "hard",
            "synthesis_type": q.get("synthesis_type", "theme_analysis"),
            "requires_iteration": True,
            "answerable": True,
            "status": "pending",
        })

    logger.info(f"  Generated {len(questions)} questions for min_core={min_core}")
    return questions


async def generate(
    min_core_filter: Optional[int] = None,
    model_name: str = DEFAULT_MODEL,
) -> None:
    from google import genai as genai_sdk

    api_key = _get_gemini_api_key()
    client = genai_sdk.Client(api_key=api_key)
    logger.info(f"Initialized Gemini model: {model_name}")

    summaries = _load_paper_summaries()
    existing = _load_existing_questions()

    targets = SYNTHESIS_TARGETS
    if min_core_filter is not None:
        if min_core_filter not in targets:
            raise ValueError(f"Invalid min_core: {min_core_filter}. Choose from {list(targets)}")
        targets = {min_core_filter: targets[min_core_filter]}

    all_questions = list(existing)

    for min_core, cfg in sorted(targets.items()):
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

        if min_core_filter is not None:
            all_questions = [q for q in all_questions if q["min_core"] != min_core]

        all_questions.extend(new_questions)
        _save_questions(all_questions)

        await asyncio.sleep(3)

    print(f"\nDone. Total synthesis questions: {len(all_questions)}")
    _print_summary(all_questions)


def _print_summary(questions: List[Dict[str, Any]]) -> None:
    by_level = {}
    for q in questions:
        mc = q["min_core"]
        by_level.setdefault(mc, []).append(q)

    print("\nBreakdown by min_core:")
    for mc in sorted(by_level):
        qs = by_level[mc]
        types = {}
        for q in qs:
            t = q.get("synthesis_type", "unknown")
            types[t] = types.get(t, 0) + 1
        type_str = ", ".join(f"{t}={c}" for t, c in sorted(types.items()))
        print(f"  min_core={mc:2d}: {len(qs):2d} questions ({type_str})")
    print(f"\nOutput: {OUTPUT_FILE}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate synthesis questions")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate", help="Generate synthesis questions")
    gen_parser.add_argument(
        "--min-core", type=int, choices=[5, 10, 20, 50],
        help="Generate only for this min_core level",
    )

    subparsers.add_parser("status", help="Show current generation status")

    args = parser.parse_args()

    if args.command == "generate":
        asyncio.run(generate(
            min_core_filter=args.min_core,
            model_name=args.model,
        ))
    elif args.command == "status":
        existing = _load_existing_questions()
        if not existing:
            print("No synthesis questions generated yet.")
        else:
            _print_summary(existing)
            pending = [q for q in existing if q.get("status") == "pending"]
            accepted = [q for q in existing if q.get("status") in ("accept", "modify")]
            print(f"\nReview status: {len(accepted)} accepted, {len(pending)} pending review")


if __name__ == "__main__":
    main()
