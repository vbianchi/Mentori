#!/usr/bin/env python3
"""
Automated Ground Truth Validator for V4 Paper-Level Questions.

For each of the 150 draft questions, uploads the source PDF to Gemini and runs
3 independent answering passes (Phase A), then a single judge call that compares
the 3 answers against the expected answer (Phase B).

Flags questions where:
  - The LLM cannot answer from the document (unanswerable / hallucinated question)
  - The 3 runs contradict each other (ambiguous question)
  - The LLM answers don't cover the expected concepts (wrong expected answer)

Results are saved incrementally — the script is fully resumable.

Usage:
    # Full validation run (150 questions × 4 calls each ≈ 5-10 min)
    uv run python publication/scripts/question_validator.py validate

    # Quick smoke-test (first 5 questions, 1 run each)
    uv run python publication/scripts/question_validator.py validate --limit 5 --n-runs 1

    # Use a specific model
    uv run python publication/scripts/question_validator.py --model gemini-2.5-flash-preview-05-20 validate

    # Show report without re-running
    uv run python publication/scripts/question_validator.py report

    # Export only flagged questions for human review
    uv run python publication/scripts/question_validator.py export-flagged
"""

import argparse
import asyncio
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.experiments_v4.paper_processor import _get_gemini_api_key, DEFAULT_MODEL

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("question_validator")

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────

DATASETS_DIR = PROJECT_ROOT / "datasets"
PAPERS_DIR = DATASETS_DIR / "v4_papers" / "core"
REVIEW_CSV = DATASETS_DIR / "review_paper_questions.csv"
RESULTS_JSON = DATASETS_DIR / "validation_results.json"
VALIDATED_CSV = DATASETS_DIR / "review_paper_questions_validated.csv"

# ─────────────────────────────────────────────────────────────
# Prompts — 3 variants for Phase A to get lexical variety
# ─────────────────────────────────────────────────────────────

ANSWER_PROMPTS = [
    (
        "You are a scientific document expert. Answer the following question strictly "
        "based on the provided paper. If the answer is not in the document, say "
        "'NOT IN DOCUMENT'. Answer in 2-4 sentences.\n\nQuestion: {question}"
    ),
    (
        "Using only information from this research paper, provide a direct answer to "
        "the question below. If the paper does not contain the answer, respond with "
        "'NOT IN DOCUMENT'. Keep your answer to 2-4 sentences.\n\nQuestion: {question}"
    ),
    (
        "Read this scientific paper and answer the question. Base your answer solely "
        "on the document content. If the information is absent, say 'NOT IN DOCUMENT'. "
        "Limit your answer to 2-4 sentences.\n\nQuestion: {question}"
    ),
]

JUDGE_PROMPT = """\
You are evaluating ground truth quality for a scientific RAG benchmark.

Question: {question}

Expected answer (written by the question generator):
{expected_answer}

Expected key concepts (should appear in a correct answer):
{expected_concepts}

The question was posed to an LLM with access to the source paper. Here are the
responses from {n_runs} independent runs:

{runs_block}

Evaluate this ground truth entry and return a JSON object:
{{
  "concepts_covered": <integer: how many expected concepts appear in at least {min_runs} of {n_runs} runs>,
  "total_concepts": <integer: total number of expected concepts>,
  "factual_match": <boolean: do the LLM runs broadly agree with the expected answer?>,
  "consistency": <boolean: are the runs consistent with each other on key facts?>,
  "answerable": <boolean: can the question clearly be answered from the document?>,
  "flag": <boolean: should this question be flagged for human review?>,
  "flag_reason": <string: brief reason if flagged, empty string otherwise>
}}

Flag (set "flag": true) if ANY of the following apply:
- At least one run says "NOT IN DOCUMENT" or similar
- The runs contradict each other on specific facts or numbers
- The expected answer contains specific facts absent from all LLM runs (possible hallucination)
- Fewer than half the expected concepts appear across the runs

Return ONLY the JSON object, no other text.\
"""


# ─────────────────────────────────────────────────────────────
# State management (resumable)
# ─────────────────────────────────────────────────────────────

def _load_results() -> Dict[str, Any]:
    if RESULTS_JSON.exists():
        return json.loads(RESULTS_JSON.read_text())
    return {"validated": {}}


def _save_results(results: Dict[str, Any]) -> None:
    RESULTS_JSON.write_text(json.dumps(results, indent=2))


def _load_questions() -> List[Dict[str, Any]]:
    if not REVIEW_CSV.exists():
        raise FileNotFoundError(f"Review CSV not found: {REVIEW_CSV}\nRun the CSV export step first.")
    with open(REVIEW_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────────────────────
# PDF upload (in-memory cache per session)
# ─────────────────────────────────────────────────────────────

_upload_cache: Dict[str, Any] = {}


async def _upload_pdf(client: Any, pdf_path: Path) -> Optional[Any]:
    key = pdf_path.name
    if key in _upload_cache:
        return _upload_cache[key]

    logger.info(f"  Uploading {pdf_path.name}...")
    try:
        uploaded = client.files.upload(file=str(pdf_path))
        _upload_cache[key] = uploaded
        return uploaded
    except Exception as e:
        logger.error(f"  Upload failed for {pdf_path.name}: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# Core validation logic
# ─────────────────────────────────────────────────────────────

async def _validate_question(
    client: Any,
    model_name: str,
    question_row: Dict[str, Any],
    pdf_file: Any,
    n_runs: int,
) -> Dict[str, Any]:
    """Phase A (n_runs answers) + Phase B (judge call) for one question."""
    from google.genai import types

    question = question_row["question"]
    expected_answer = question_row["expected_answer"]
    expected_concepts = question_row["expected_concepts"]
    q_id = question_row["q_id"]

    # ── Phase A: n_runs independent answers ──────────────────
    runs = []
    for i in range(n_runs):
        prompt = ANSWER_PROMPTS[i % len(ANSWER_PROMPTS)].format(question=question)
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[pdf_file, prompt],
                config=types.GenerateContentConfig(temperature=0.2),
            )
            runs.append(response.text.strip())
        except Exception as e:
            logger.warning(f"    Run {i+1} failed for {q_id}: {e}")
            runs.append("[ERROR: call failed]")
        await asyncio.sleep(1.5)

    # ── Phase B: judge call ───────────────────────────────────
    runs_block = "\n\n".join(f"Run {i+1}: {r}" for i, r in enumerate(runs))
    min_runs = max(1, n_runs // 2 + 1)  # majority: 2 of 3, or 1 of 1

    judge_prompt = JUDGE_PROMPT.format(
        question=question,
        expected_answer=expected_answer,
        expected_concepts=expected_concepts,
        n_runs=n_runs,
        min_runs=min_runs,
        runs_block=runs_block,
    )

    judgment: Dict[str, Any] = {}
    try:
        judge_response = client.models.generate_content(
            model=model_name,
            contents=judge_prompt,
            config=types.GenerateContentConfig(temperature=0.0),
        )
        text = judge_response.text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            judgment = json.loads(text[start:end])
        else:
            raise ValueError("No JSON object in judge response")
    except Exception as e:
        logger.warning(f"    Judge call failed for {q_id}: {e}")
        judgment = {
            "concepts_covered": 0,
            "total_concepts": len(str(expected_concepts).split(",")),
            "factual_match": False,
            "consistency": False,
            "answerable": False,
            "flag": True,
            "flag_reason": f"Judge call failed: {e}",
        }

    await asyncio.sleep(1.5)

    return {
        "q_id": q_id,
        **{f"run_{i+1}": r for i, r in enumerate(runs)},
        **judgment,
    }


# ─────────────────────────────────────────────────────────────
# Main validate command
# ─────────────────────────────────────────────────────────────

async def validate(
    model_name: str = DEFAULT_MODEL,
    n_runs: int = 3,
    limit: Optional[int] = None,
) -> None:
    from google import genai as genai_sdk

    api_key = _get_gemini_api_key()
    client = genai_sdk.Client(api_key=api_key)
    logger.info(f"Model: {model_name} | runs per question: {n_runs}")

    questions = _load_questions()
    if limit:
        questions = questions[:limit]

    results = _load_results()
    already_done = set(results["validated"].keys())
    pending = [q for q in questions if q["q_id"] not in already_done]

    logger.info(
        f"Questions: {len(questions)} total | "
        f"{len(already_done)} already validated | "
        f"{len(pending)} to process"
    )

    if not pending:
        logger.info("Nothing to do — all questions already validated.")
        _print_report(results)
        return

    # Group by paper so each PDF is uploaded once
    by_paper: Dict[str, List[Dict]] = {}
    for q in pending:
        by_paper.setdefault(q["filename"], []).append(q)

    total_processed = 0
    for fname, paper_questions in sorted(by_paper.items()):
        pdf_path = PAPERS_DIR / fname
        if not pdf_path.exists():
            logger.error(f"PDF not found, skipping: {pdf_path}")
            continue

        logger.info(f"\n[{fname}] — {len(paper_questions)} question(s)")
        pdf_file = await _upload_pdf(client, pdf_path)
        if pdf_file is None:
            continue

        for q_row in paper_questions:
            q_id = q_row["q_id"]
            logger.info(f"  {q_id} ({q_row['type']})...")

            result = await _validate_question(
                client=client,
                model_name=model_name,
                question_row=q_row,
                pdf_file=pdf_file,
                n_runs=n_runs,
            )

            results["validated"][q_id] = result
            total_processed += 1
            _save_results(results)  # incremental save

            concepts = f"{result.get('concepts_covered', '?')}/{result.get('total_concepts', '?')}"
            flag_str = " *** FLAGGED ***" if result.get("flag") else ""
            logger.info(
                f"    concepts={concepts} | match={result.get('factual_match')} | "
                f"consistent={result.get('consistency')} | "
                f"answerable={result.get('answerable')}{flag_str}"
            )
            if result.get("flag_reason"):
                logger.info(f"    reason: {result['flag_reason']}")

        await asyncio.sleep(2)  # brief pause between papers

    logger.info(f"\nDone. Processed {total_processed} questions this run.")
    _export_validated_csv(questions, results)
    _print_report(results)


# ─────────────────────────────────────────────────────────────
# Export and reporting
# ─────────────────────────────────────────────────────────────

def _export_validated_csv(
    questions: List[Dict[str, Any]],
    results: Dict[str, Any],
) -> None:
    validated = results.get("validated", {})
    rows = []
    for q in questions:
        q_id = q["q_id"]
        v = validated.get(q_id, {})
        n_runs_done = sum(1 for k in v if k.startswith("run_"))
        rows.append({
            **q,
            **{f"run_{i+1}": v.get(f"run_{i+1}", "") for i in range(3)},
            "concepts_covered": (
                f"{v['concepts_covered']}/{v['total_concepts']}"
                if "concepts_covered" in v else ""
            ),
            "factual_match":  v.get("factual_match", ""),
            "consistency":    v.get("consistency", ""),
            "answerable":     v.get("answerable", ""),
            "flag":           v.get("flag", ""),
            "flag_reason":    v.get("flag_reason", ""),
            "validation_status": (
                "FLAGGED"   if v.get("flag")
                else "OK"   if v
                else "PENDING"
            ),
        })

    with open(VALIDATED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    flagged = sum(1 for r in rows if r["validation_status"] == "FLAGGED")
    logger.info(f"Exported {len(rows)} rows to {VALIDATED_CSV} ({flagged} flagged)")


def _print_report(results: Dict[str, Any]) -> None:
    validated = results.get("validated", {})
    if not validated:
        print("No validation results yet. Run: validate")
        return

    total = len(validated)
    flagged   = sum(1 for v in validated.values() if v.get("flag"))
    answerable = sum(1 for v in validated.values() if v.get("answerable"))
    consistent = sum(1 for v in validated.values() if v.get("consistency"))
    factual    = sum(1 for v in validated.values() if v.get("factual_match"))

    pct = lambda n: f"{100 * n // total}%" if total else "n/a"

    print(f"\n{'='*55}")
    print(f"VALIDATION REPORT  ({total} / 150 questions validated)")
    print(f"{'='*55}")
    print(f"  Answerable from paper :  {answerable:3d} / {total}  ({pct(answerable)})")
    print(f"  Factual match         :  {factual:3d} / {total}  ({pct(factual)})")
    print(f"  Consistent across runs:  {consistent:3d} / {total}  ({pct(consistent)})")
    print(f"  Flagged for review    :  {flagged:3d} / {total}  ({pct(flagged)})")

    if flagged:
        print(f"\n  Flagged questions:")
        for q_id, v in sorted(validated.items()):
            if v.get("flag"):
                reason = v.get("flag_reason") or "no reason recorded"
                print(f"    {q_id}: {reason}")
    print()


def _export_flagged(results: Dict[str, Any], questions: List[Dict[str, Any]]) -> None:
    validated = results.get("validated", {})
    flagged_ids = {q_id for q_id, v in validated.items() if v.get("flag")}

    if not flagged_ids:
        print("No flagged questions found.")
        return

    flagged_rows = []
    for q in questions:
        if q["q_id"] not in flagged_ids:
            continue
        v = validated[q["q_id"]]
        flagged_rows.append({
            **q,
            "flag_reason": v.get("flag_reason", ""),
            "run_1": v.get("run_1", ""),
            "run_2": v.get("run_2", ""),
            "run_3": v.get("run_3", ""),
        })

    out = DATASETS_DIR / "flagged_questions.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flagged_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flagged_rows)

    print(f"Exported {len(flagged_rows)} flagged questions to {out}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automated validator for V4 paper-level ground truth questions"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    val_parser = subparsers.add_parser("validate", help="Run Phase A + B validation")
    val_parser.add_argument(
        "--n-runs", type=int, default=3,
        help="Answer passes per question (default: 3)",
    )
    val_parser.add_argument(
        "--limit", type=int, default=None,
        help="Cap at N questions — useful for smoke-testing",
    )

    subparsers.add_parser("report", help="Print validation statistics")
    subparsers.add_parser("export-flagged", help="Export flagged questions to CSV")

    args = parser.parse_args()

    if args.command == "validate":
        asyncio.run(validate(
            model_name=args.model,
            n_runs=args.n_runs,
            limit=args.limit,
        ))

    elif args.command == "report":
        results = _load_results()
        questions = _load_questions() if REVIEW_CSV.exists() else []
        _print_report(results)
        if questions and results.get("validated"):
            _export_validated_csv(questions, results)

    elif args.command == "export-flagged":
        results = _load_results()
        questions = _load_questions()
        _export_flagged(results, questions)


if __name__ == "__main__":
    main()
