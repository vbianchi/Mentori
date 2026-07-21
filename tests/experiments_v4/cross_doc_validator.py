#!/usr/bin/env python3
"""
Automated Validator for V4 Cross-Document Questions.

For each of the 30 cross-document questions, uploads the 2-4 source PDFs to
Gemini and runs 3 independent answering passes (Phase A), then a single judge
call that compares the 3 answers against the expected answer (Phase B).

Flags questions where:
  - The LLM cannot answer from the documents (unanswerable / hallucinated question)
  - The 3 runs contradict each other (ambiguous question)
  - The LLM answers don't cover the expected concepts (wrong expected answer)
  - The answer doesn't actually require multiple papers (single-paper answerable)

Results are saved incrementally — the script is fully resumable.

Usage:
    # Full validation run (30 questions × 4 calls each ≈ 5-10 min)
    uv run python tests/experiments_v4/cross_doc_validator.py validate

    # Quick smoke-test (first 2 questions, 1 run each)
    uv run python tests/experiments_v4/cross_doc_validator.py validate --limit 2 --n-runs 1

    # Use a specific model
    uv run python tests/experiments_v4/cross_doc_validator.py --model gemini-2.5-flash-preview-05-20 validate

    # Show report without re-running
    uv run python tests/experiments_v4/cross_doc_validator.py report

    # Export only flagged questions for human review
    uv run python tests/experiments_v4/cross_doc_validator.py export-flagged
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
logger = logging.getLogger("cross_doc_validator")

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────

DATASETS_DIR = PROJECT_ROOT / "datasets"
PAPERS_DIR = DATASETS_DIR / "v4_papers" / "core"
INPUT_JSON = DATASETS_DIR / "questions" / "cross_document_draft.json"
RESULTS_JSON = DATASETS_DIR / "cross_doc_validation_results.json"
VALIDATED_CSV = DATASETS_DIR / "review_crossdoc_validated.csv"

# ─────────────────────────────────────────────────────────────
# Prompts — 3 variants for Phase A to get lexical variety
# ─────────────────────────────────────────────────────────────

ANSWER_PROMPTS = [
    (
        "You are a scientific document expert. Answer the following question using "
        "information from ALL the provided papers. The answer requires synthesizing "
        "information across multiple documents. If the answer cannot be found across "
        "the papers, say 'NOT IN DOCUMENTS'. Answer in 3-5 sentences.\n\n"
        "Question: {question}"
    ),
    (
        "Using only the provided research papers, answer the question below. Your "
        "answer must draw on information from multiple papers — no single paper alone "
        "should suffice. If the papers do not contain the answer, respond with "
        "'NOT IN DOCUMENTS'. Keep your answer to 3-5 sentences.\n\n"
        "Question: {question}"
    ),
    (
        "Read all the provided scientific papers and answer the question. Base your "
        "answer on a synthesis of multiple documents — cite specific details from "
        "different papers. If the information is absent, say 'NOT IN DOCUMENTS'. "
        "Limit your answer to 3-5 sentences.\n\n"
        "Question: {question}"
    ),
]

JUDGE_PROMPT = """\
You are evaluating ground truth quality for a scientific RAG benchmark.
This is a CROSS-DOCUMENT question that should require information from multiple papers.

Question: {question}

Source papers referenced: {source_papers}

Expected answer (written by the question generator):
{expected_answer}

Expected key concepts (should appear in a correct answer):
{expected_concepts}

The question was posed to an LLM with access to all source papers. Here are the
responses from {n_runs} independent runs:

{runs_block}

Evaluate this cross-document ground truth entry and return a JSON object:
{{
  "concepts_covered": <integer: how many expected concepts appear in at least {min_runs} of {n_runs} runs>,
  "total_concepts": <integer: total number of expected concepts>,
  "factual_match": <boolean: do the LLM runs broadly agree with the expected answer?>,
  "consistency": <boolean: are the runs consistent with each other on key facts?>,
  "answerable": <boolean: can the question clearly be answered from the provided documents?>,
  "multi_paper_required": <boolean: does answering truly require multiple papers, or could one paper alone suffice?>,
  "flag": <boolean: should this question be flagged for human review?>,
  "flag_reason": <string: brief reason if flagged, empty string otherwise>
}}

Flag (set "flag": true) if ANY of the following apply:
- At least one run says "NOT IN DOCUMENTS" or similar
- The runs contradict each other on specific facts or numbers
- The expected answer contains specific facts absent from all LLM runs (possible hallucination)
- Fewer than half the expected concepts appear across the runs
- The question can clearly be answered from a single paper (multi_paper_required = false)

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
    if not INPUT_JSON.exists():
        raise FileNotFoundError(
            f"Cross-doc questions not found: {INPUT_JSON}\n"
            "Run cross_doc_generator.py generate first."
        )
    data = json.loads(INPUT_JSON.read_text())
    return data.get("questions", [])


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


async def _upload_source_papers(
    client: Any, source_papers: List[str]
) -> List[Any]:
    """Upload all source papers for a question, returning list of file handles."""
    uploaded = []
    for filename in source_papers:
        pdf_path = PAPERS_DIR / filename
        if not pdf_path.exists():
            logger.error(f"  PDF not found: {pdf_path}")
            continue
        pdf_file = await _upload_pdf(client, pdf_path)
        if pdf_file is not None:
            uploaded.append(pdf_file)
    return uploaded


# ─────────────────────────────────────────────────────────────
# Core validation logic
# ─────────────────────────────────────────────────────────────

async def _validate_question(
    client: Any,
    model_name: str,
    question: Dict[str, Any],
    pdf_files: List[Any],
    n_runs: int,
) -> Dict[str, Any]:
    """Phase A (n_runs answers) + Phase B (judge call) for one cross-doc question."""
    from google.genai import types

    q_text = question["question"]
    expected_answer = question["expected_answer"]
    expected_concepts = question.get("expected_concepts", [])
    source_papers = question.get("source_papers", [])
    q_id = question["id"]

    # ── Phase A: n_runs independent answers ──────────────────
    runs = []
    for i in range(n_runs):
        prompt = ANSWER_PROMPTS[i % len(ANSWER_PROMPTS)].format(question=q_text)
        try:
            # Pass all PDFs + prompt as contents
            contents = list(pdf_files) + [prompt]
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            runs.append(response.text.strip())
        except Exception as e:
            logger.warning(f"    Run {i+1} failed for {q_id}: {e}")
            runs.append("[ERROR: call failed]")
        await asyncio.sleep(2)

    # ── Phase B: judge call ───────────────────────────────────
    runs_block = "\n\n".join(f"Run {i+1}: {r}" for i, r in enumerate(runs))
    min_runs = max(1, n_runs // 2 + 1)

    judge_prompt = JUDGE_PROMPT.format(
        question=q_text,
        expected_answer=expected_answer,
        expected_concepts=", ".join(expected_concepts),
        source_papers=", ".join(source_papers),
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
            "total_concepts": len(expected_concepts),
            "factual_match": False,
            "consistency": False,
            "answerable": False,
            "multi_paper_required": False,
            "flag": True,
            "flag_reason": f"Judge call failed: {e}",
        }

    await asyncio.sleep(2)

    return {
        "q_id": q_id,
        "source_papers": source_papers,
        "min_core": question.get("min_core"),
        "comparison_type": question.get("comparison_type"),
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
    total_questions = len(questions)
    if limit:
        questions = questions[:limit]

    results = _load_results()
    already_done = set(results["validated"].keys())
    pending = [q for q in questions if q["id"] not in already_done]

    logger.info(
        f"Questions: {len(questions)} total | "
        f"{len(already_done)} already validated | "
        f"{len(pending)} to process"
    )

    if not pending:
        logger.info("Nothing to do — all questions already validated.")
        _print_report(results, total_questions)
        return

    total_processed = 0
    for q in pending:
        q_id = q["id"]
        source_papers = q.get("source_papers", [])
        logger.info(
            f"\n[{q_id}] min_core={q['min_core']} | "
            f"{q.get('comparison_type', '?')} | "
            f"papers: {', '.join(source_papers)}"
        )

        # Upload all source PDFs
        pdf_files = await _upload_source_papers(client, source_papers)
        if not pdf_files:
            logger.error(f"  No PDFs could be uploaded for {q_id}, skipping")
            continue
        if len(pdf_files) < len(source_papers):
            logger.warning(
                f"  Only {len(pdf_files)}/{len(source_papers)} PDFs uploaded for {q_id}"
            )

        logger.info(f"  Validating with {len(pdf_files)} PDFs...")
        result = await _validate_question(
            client=client,
            model_name=model_name,
            question=q,
            pdf_files=pdf_files,
            n_runs=n_runs,
        )

        results["validated"][q_id] = result
        total_processed += 1
        _save_results(results)  # incremental save

        concepts = (
            f"{result.get('concepts_covered', '?')}/"
            f"{result.get('total_concepts', '?')}"
        )
        multi = result.get("multi_paper_required", "?")
        flag_str = " *** FLAGGED ***" if result.get("flag") else ""
        logger.info(
            f"    concepts={concepts} | match={result.get('factual_match')} | "
            f"consistent={result.get('consistency')} | "
            f"multi_paper={multi}{flag_str}"
        )
        if result.get("flag_reason"):
            logger.info(f"    reason: {result['flag_reason']}")

    logger.info(f"\nDone. Processed {total_processed} questions this run.")
    _export_validated_csv(questions, results)
    _print_report(results, total_questions)


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
        q_id = q["id"]
        v = validated.get(q_id, {})
        rows.append({
            "q_id": q_id,
            "min_core": q["min_core"],
            "source_papers": ", ".join(q.get("source_papers", [])),
            "comparison_type": q.get("comparison_type", ""),
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "expected_concepts": ", ".join(q.get("expected_concepts", [])),
            "difficulty": q.get("difficulty", ""),
            "run_1": v.get("run_1", ""),
            "run_2": v.get("run_2", ""),
            "run_3": v.get("run_3", ""),
            "concepts_covered": (
                f"{v['concepts_covered']}/{v['total_concepts']}"
                if "concepts_covered" in v else ""
            ),
            "factual_match": v.get("factual_match", ""),
            "consistency": v.get("consistency", ""),
            "answerable": v.get("answerable", ""),
            "multi_paper_required": v.get("multi_paper_required", ""),
            "flag": v.get("flag", ""),
            "flag_reason": v.get("flag_reason", ""),
            "validation_status": (
                "FLAGGED" if v.get("flag")
                else "OK" if v
                else "PENDING"
            ),
        })

    with open(VALIDATED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    flagged = sum(1 for r in rows if r["validation_status"] == "FLAGGED")
    logger.info(f"Exported {len(rows)} rows to {VALIDATED_CSV} ({flagged} flagged)")


def _print_report(results: Dict[str, Any], total_expected: int = 30) -> None:
    validated = results.get("validated", {})
    if not validated:
        print("No validation results yet. Run: validate")
        return

    total = len(validated)
    flagged = sum(1 for v in validated.values() if v.get("flag"))
    answerable = sum(1 for v in validated.values() if v.get("answerable"))
    consistent = sum(1 for v in validated.values() if v.get("consistency"))
    factual = sum(1 for v in validated.values() if v.get("factual_match"))
    multi_paper = sum(1 for v in validated.values() if v.get("multi_paper_required"))

    pct = lambda n: f"{100 * n // total}%" if total else "n/a"

    print(f"\n{'='*60}")
    print(f"CROSS-DOC VALIDATION REPORT  ({total} / {total_expected} questions)")
    print(f"{'='*60}")
    print(f"  Answerable from papers  :  {answerable:3d} / {total}  ({pct(answerable)})")
    print(f"  Factual match           :  {factual:3d} / {total}  ({pct(factual)})")
    print(f"  Consistent across runs  :  {consistent:3d} / {total}  ({pct(consistent)})")
    print(f"  Multi-paper required    :  {multi_paper:3d} / {total}  ({pct(multi_paper)})")
    print(f"  Flagged for review      :  {flagged:3d} / {total}  ({pct(flagged)})")

    # Breakdown by min_core
    by_core: Dict[int, Dict[str, int]] = {}
    for q_id, v in validated.items():
        mc = v.get("min_core", 0)
        if mc not in by_core:
            by_core[mc] = {"total": 0, "flagged": 0, "ok": 0}
        by_core[mc]["total"] += 1
        if v.get("flag"):
            by_core[mc]["flagged"] += 1
        else:
            by_core[mc]["ok"] += 1

    if by_core:
        print(f"\n  By min_core:")
        for mc in sorted(by_core):
            c = by_core[mc]
            print(f"    min_core={mc:2d}: {c['ok']}/{c['total']} OK, {c['flagged']} flagged")

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
        if q["id"] not in flagged_ids:
            continue
        v = validated[q["id"]]
        flagged_rows.append({
            "q_id": q["id"],
            "min_core": q["min_core"],
            "source_papers": ", ".join(q.get("source_papers", [])),
            "comparison_type": q.get("comparison_type", ""),
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "expected_concepts": ", ".join(q.get("expected_concepts", [])),
            "flag_reason": v.get("flag_reason", ""),
            "run_1": v.get("run_1", ""),
            "run_2": v.get("run_2", ""),
            "run_3": v.get("run_3", ""),
        })

    out = DATASETS_DIR / "flagged_crossdoc_questions.csv"
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
        description="Automated validator for V4 cross-document ground truth questions"
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
        questions = _load_questions() if INPUT_JSON.exists() else []
        _print_report(results, len(questions))
        if questions and results.get("validated"):
            _export_validated_csv(questions, results)

    elif args.command == "export-flagged":
        results = _load_results()
        questions = _load_questions()
        _export_flagged(results, questions)


if __name__ == "__main__":
    main()
