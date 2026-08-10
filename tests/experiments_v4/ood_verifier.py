#!/usr/bin/env python3
"""
OOD Question Verifier for V4 Experiments.

Checks that out-of-domain questions are NOT answerable from any paper in the
corpus (50 core + 150 noise = 200 papers). Uses Gemini to check each OOD
question against paper summaries.

Strategy:
  - Builds a single corpus summary from all 50 core paper draft JSONs
    (title + research question + key terms per paper)
  - Adds noise paper filenames (we don't have content analysis for noise,
    but their arXiv IDs reveal their topics)
  - Asks Gemini: "Could this question be answered from any of these papers?"
  - Flags any question where Gemini says yes

Usage:
    # Verify all 50 OOD questions
    uv run python tests/experiments_v4/ood_verifier.py verify

    # Verify with a specific model
    uv run python tests/experiments_v4/ood_verifier.py --model gemini-2.5-flash-preview-05-20 verify

    # Show report
    uv run python tests/experiments_v4/ood_verifier.py report
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.experiments_v4.paper_processor import _get_gemini_api_key, DEFAULT_MODEL

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ood_verifier")

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────

DATASETS_DIR = PROJECT_ROOT / "datasets"
OOD_JSON = DATASETS_DIR / "questions" / "out_of_domain.json"
DRAFT_DIR = DATASETS_DIR / "questions_draft"
CORE_DIR = DATASETS_DIR / "v4_papers" / "core"
NOISE_DIR = DATASETS_DIR / "v4_papers" / "noise"
RESULTS_JSON = DATASETS_DIR / "ood_verification_results.json"

# ─────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────

CORPUS_DOMAINS = """\
The corpus contains 200 papers across these domains:
- Bioinformatics / NGS tools (Sarek, Snakemake, nf-core, fastp, MultiQC, STAR, Salmon, DESeq2, SeqKit, Cutadapt)
- Veterinary epidemiology (ASF, HPAI, LSD, bTB, rabies, PPR, brucellosis, FMD)
- Microbiome research (livestock gut, pig MAGs, swine cultivation, chicken microbiome, aquaculture metagenomics, OTU vs ASV, 16S best practices)
- AMR / One Health / Zoonotic disease (AMR surveillance, One Health frameworks, ISSE, ESBL E. coli, Salmonella WGS, Campylobacter WGS)
- Computational biology methods (methylPipe, HTS-flow, MYC oncogene, PDBinder, 4C-seq)
- 150 noise papers from arXiv covering: protein structure prediction, single-cell sequencing, metagenomics, CRISPR, computational drug discovery, phylogenetics, epigenetics, variant calling, ML for protein folding, transcriptomics, network biology, metabolomics, population genetics, structural bioinformatics, long-read sequencing, spatial transcriptomics, immunoinformatics, cancer genomics, chromatin accessibility, genome annotation, bioimage analysis, clinical genomics"""

VERIFY_PROMPTS = [
    (
        "You are verifying whether a question could potentially be answered using "
        "a scientific paper corpus.\n\n"
        "{corpus_domains}\n\n"
        "Here are the 50 core paper summaries:\n{corpus_summary}\n\n"
        "QUESTION: {question}\n\n"
        "Could this question be answered (even partially) using information from "
        "any paper in this corpus? Consider both core and noise papers.\n\n"
        "Return a JSON object:\n"
        '{{"answerable_from_corpus": <boolean>, "potential_papers": [<filenames>], '
        '"confidence": <float 0-1>, "reasoning": "<brief explanation>"}}\n\n'
        "Return ONLY the JSON object."
    ),
    (
        "You are a scientific corpus auditor. Determine whether the following question "
        "could be answered from any of the 200 papers in this corpus.\n\n"
        "{corpus_domains}\n\n"
        "Core paper summaries:\n{corpus_summary}\n\n"
        "QUESTION: {question}\n\n"
        "Be strict: even partial overlap counts. If any paper could provide a "
        "meaningful answer, mark it as answerable.\n\n"
        "Return a JSON object:\n"
        '{{"answerable_from_corpus": <boolean>, "potential_papers": [<filenames>], '
        '"confidence": <float 0-1>, "reasoning": "<brief explanation>"}}\n\n'
        "Return ONLY the JSON object."
    ),
    (
        "You are checking whether a question falls outside the scope of a scientific "
        "paper corpus. Consider both direct answers and tangential coverage.\n\n"
        "{corpus_domains}\n\n"
        "Paper summaries:\n{corpus_summary}\n\n"
        "QUESTION: {question}\n\n"
        "Could ANY paper in this corpus (core or noise) provide even a partial "
        "answer to this question? Think carefully about noise papers too.\n\n"
        "Return a JSON object:\n"
        '{{"answerable_from_corpus": <boolean>, "potential_papers": [<filenames>], '
        '"confidence": <float 0-1>, "reasoning": "<brief explanation>"}}\n\n'
        "Return ONLY the JSON object."
    ),
]

JUDGE_PROMPT = """\
You are judging whether an out-of-domain (OOD) question truly cannot be answered
from a scientific paper corpus. Three independent reviewers checked this question.

QUESTION: {question}
OOD type: {ood_type}

Reviewer results:
{runs_block}

Based on the 3 reviews, determine the final verdict:

Return a JSON object:
{{
  "answerable_from_corpus": <boolean: could any paper answer this? true if ANY reviewer found overlap with high confidence>,
  "consistent": <boolean: do all 3 reviewers agree on the verdict?>,
  "potential_papers": <list: union of all papers mentioned by reviewers>,
  "flag": <boolean: should this be flagged for human review?>,
  "flag_reason": <string: reason if flagged, empty otherwise>
}}

Flag if:
- Reviewers disagree (inconsistent)
- Any reviewer found overlap with confidence >= 0.7
- The question is borderline (partially answerable)

Return ONLY the JSON object.\
"""


# ─────────────────────────────────────────────────────────────
# Build corpus summary
# ─────────────────────────────────────────────────────────────

def _build_corpus_summary() -> str:
    """Build a compact summary of all 50 core papers from draft JSONs."""
    lines = []
    for draft_file in sorted(DRAFT_DIR.glob("*_draft.json")):
        try:
            draft = json.loads(draft_file.read_text())
        except Exception:
            continue

        ca = draft.get("content_analysis", {})
        meta = draft.get("metadata", {})
        title = meta.get("title") or draft.get("paper_id", draft_file.stem)
        filename = draft.get("filename", draft_file.stem)
        rq = ca.get("research_question", "")
        terms = ca.get("technical_terms", [])[:8]

        lines.append(f"[{filename}] {title}")
        lines.append(f"  Topic: {rq}")
        lines.append(f"  Key terms: {', '.join(terms)}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# State management
# ─────────────────────────────────────────────────────────────

def _load_results() -> Dict[str, Any]:
    if RESULTS_JSON.exists():
        return json.loads(RESULTS_JSON.read_text())
    return {"verified": {}}


def _save_results(results: Dict[str, Any]) -> None:
    RESULTS_JSON.write_text(json.dumps(results, indent=2))


def _load_questions() -> List[Dict[str, Any]]:
    if not OOD_JSON.exists():
        raise FileNotFoundError(f"OOD questions not found: {OOD_JSON}")
    data = json.loads(OOD_JSON.read_text())
    return data.get("questions", [])


# ─────────────────────────────────────────────────────────────
# Core verification
# ─────────────────────────────────────────────────────────────

async def _verify_question(
    client: Any,
    model_name: str,
    question: Dict[str, Any],
    corpus_summary: str,
    n_runs: int = 3,
) -> Dict[str, Any]:
    """3 independent checks + judge call for one OOD question."""
    from google.genai import types

    q_text = question["question"]
    q_id = question["id"]
    ood_type = question.get("ood_type", "")

    # ── Phase A: n_runs independent checks ────────────────────
    runs: List[Dict[str, Any]] = []
    for i in range(n_runs):
        prompt = VERIFY_PROMPTS[i % len(VERIFY_PROMPTS)].format(
            corpus_domains=CORPUS_DOMAINS,
            corpus_summary=corpus_summary,
            question=q_text,
        )
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            text = response.text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                run_result = json.loads(text[start:end])
            else:
                raise ValueError("No JSON in response")
        except Exception as e:
            logger.warning(f"    Run {i+1} failed for {q_id}: {e}")
            run_result = {
                "answerable_from_corpus": False,
                "potential_papers": [],
                "confidence": 0.0,
                "reasoning": f"Call failed: {e}",
            }
        runs.append(run_result)
        await asyncio.sleep(1.5)

    # ── Phase B: judge call ───────────────────────────────────
    runs_block = "\n\n".join(
        f"Run {i+1}: answerable={r.get('answerable_from_corpus')} "
        f"confidence={r.get('confidence', 0)} "
        f"papers={r.get('potential_papers', [])} "
        f"reasoning={r.get('reasoning', '')}"
        for i, r in enumerate(runs)
    )

    judge_prompt = JUDGE_PROMPT.format(
        question=q_text,
        ood_type=ood_type,
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
            raise ValueError("No JSON in judge response")
    except Exception as e:
        logger.warning(f"    Judge call failed for {q_id}: {e}")
        judgment = {
            "answerable_from_corpus": any(r.get("answerable_from_corpus") for r in runs),
            "consistent": False,
            "potential_papers": [],
            "flag": True,
            "flag_reason": f"Judge call failed: {e}",
        }

    await asyncio.sleep(1.5)

    return {
        "q_id": q_id,
        "ood_type": ood_type,
        "question": q_text,
        **{f"run_{i+1}_answerable": r.get("answerable_from_corpus") for i, r in enumerate(runs)},
        **{f"run_{i+1}_confidence": r.get("confidence", 0) for i, r in enumerate(runs)},
        **{f"run_{i+1}_reasoning": r.get("reasoning", "") for i, r in enumerate(runs)},
        **{f"run_{i+1}_papers": r.get("potential_papers", []) for i, r in enumerate(runs)},
        **judgment,
    }


# ─────────────────────────────────────────────────────────────
# Main verify command
# ─────────────────────────────────────────────────────────────

async def verify(
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
    already_done = set(results["verified"].keys())
    pending = [q for q in questions if q["id"] not in already_done]

    logger.info(
        f"OOD questions: {len(questions)} total | "
        f"{len(already_done)} already verified | "
        f"{len(pending)} to check"
    )

    if not pending:
        logger.info("All questions already verified.")
        _print_report(results)
        return

    logger.info("Building corpus summary...")
    corpus_summary = _build_corpus_summary()
    logger.info(f"Corpus summary: {len(corpus_summary)} chars from {len(list(DRAFT_DIR.glob('*_draft.json')))} papers")

    for q in pending:
        q_id = q["id"]
        logger.info(f"  [{q_id}] ({q.get('ood_type', '?')}) {q['question'][:80]}...")

        result = await _verify_question(client, model_name, q, corpus_summary, n_runs=n_runs)

        results["verified"][q_id] = result
        _save_results(results)

        flag_str = " *** FLAGGED ***" if result.get("flag") else ""
        status = "OVERLAP" if result.get("answerable_from_corpus") else "OK"
        consistent = result.get("consistent", "?")
        logger.info(f"    {status} | consistent={consistent}{flag_str}")
        if result.get("flag"):
            logger.info(f"    reason: {result.get('flag_reason', '')}")
        if result.get("answerable_from_corpus"):
            papers = result.get("potential_papers", [])
            if papers:
                logger.info(f"    papers: {', '.join(papers)}")

    logger.info(f"\nDone. Verified {len(pending)} questions.")
    _print_report(results)


# ─────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────

def _print_report(results: Dict[str, Any]) -> None:
    verified = results.get("verified", {})
    if not verified:
        print("No verification results yet. Run: verify")
        return

    total = len(verified)
    ok = sum(1 for v in verified.values() if not v.get("answerable_from_corpus"))
    overlap = sum(1 for v in verified.values() if v.get("answerable_from_corpus"))
    flagged = sum(1 for v in verified.values() if v.get("flag"))
    consistent = sum(1 for v in verified.values() if v.get("consistent"))

    by_type: Dict[str, Dict[str, int]] = {}
    for v in verified.values():
        t = v.get("ood_type", "unknown")
        if t not in by_type:
            by_type[t] = {"total": 0, "ok": 0, "overlap": 0, "flagged": 0}
        by_type[t]["total"] += 1
        if v.get("answerable_from_corpus"):
            by_type[t]["overlap"] += 1
        else:
            by_type[t]["ok"] += 1
        if v.get("flag"):
            by_type[t]["flagged"] += 1

    pct = lambda n: f"{100 * n // total}%" if total else "n/a"

    print(f"\n{'='*55}")
    print(f"OOD VERIFICATION REPORT  ({total} questions)")
    print(f"{'='*55}")
    print(f"  Confirmed OOD (OK)     :  {ok:3d} / {total}  ({pct(ok)})")
    print(f"  Potential overlap      :  {overlap:3d} / {total}  ({pct(overlap)})")
    print(f"  Consistent across runs :  {consistent:3d} / {total}  ({pct(consistent)})")
    print(f"  Flagged for review     :  {flagged:3d} / {total}  ({pct(flagged)})")

    print(f"\n  By type:")
    for t in sorted(by_type):
        c = by_type[t]
        print(f"    {t:20s}: {c['ok']}/{c['total']} OK, {c['overlap']} overlap, {c['flagged']} flagged")

    if flagged:
        print(f"\n  Flagged questions:")
        for q_id, v in sorted(verified.items()):
            if v.get("flag"):
                reason = v.get("flag_reason") or "no reason"
                papers = ", ".join(v.get("potential_papers", []))
                print(f"    {q_id}: {reason}")
                if papers:
                    print(f"           Papers: {papers}")
    print()


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify OOD questions are not answerable from corpus"
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Gemini model (default: {DEFAULT_MODEL})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    v_parser = subparsers.add_parser("verify", help="Run verification")
    v_parser.add_argument("--limit", type=int, default=None)
    v_parser.add_argument("--n-runs", type=int, default=3,
                          help="Independent checks per question (default: 3)")

    subparsers.add_parser("report", help="Print report")

    args = parser.parse_args()

    if args.command == "verify":
        asyncio.run(verify(model_name=args.model, n_runs=args.n_runs, limit=args.limit))
    elif args.command == "report":
        results = _load_results()
        _print_report(results)


if __name__ == "__main__":
    main()
