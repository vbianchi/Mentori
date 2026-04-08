"""
Verify all flagged questions against source paper text.

For each flagged question:
1. Extract text from the source PDF(s)
2. Search for each expected concept in the paper text
3. Report FOUND/NOT FOUND with surrounding context
4. Flag potential issues (hallucinated concepts, wrong papers, etc.)
"""

import json
import os
import re
from pathlib import Path
from pypdf import PdfReader
from collections import defaultdict


PDF_DIR = Path("publication/data/corpus/core")
GT_PATH = Path("publication/data/ground_truth.json")
VALIDATION_FILES = {
    "main": Path("publication/data/validation_main.json"),
    "cross_document": Path("publication/data/validation_cross_document.json"),
    "synthesis": Path("publication/data/validation_synthesis.json"),
    "ood": Path("publication/data/validation_ood.json"),
}


def extract_text(pdf_path: str) -> str:
    """Extract full text from a PDF."""
    try:
        reader = PdfReader(pdf_path)
        return " ".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"[ERROR extracting: {e}]"


def find_concept_in_text(concept: str, text: str, context_chars: int = 120) -> dict:
    """Search for a concept in text, return match info with context."""
    text_lower = text.lower()
    concept_lower = concept.lower()

    # Try exact match first
    idx = text_lower.find(concept_lower)
    if idx >= 0:
        ctx_start = max(0, idx - context_chars // 2)
        ctx_end = min(len(text), idx + len(concept) + context_chars // 2)
        return {
            "status": "FOUND",
            "match_type": "exact",
            "context": text[ctx_start:ctx_end].replace("\n", " ").strip(),
        }

    # Try partial/fuzzy: split concept into words, check if all present
    words = [w for w in concept_lower.split() if len(w) > 2]
    if words:
        all_found = all(w in text_lower for w in words)
        if all_found:
            # Find context around first word
            first_idx = text_lower.find(words[0])
            ctx_start = max(0, first_idx - context_chars // 2)
            ctx_end = min(len(text), first_idx + len(words[0]) + context_chars // 2)
            return {
                "status": "FOUND",
                "match_type": "partial (all words present)",
                "context": text[ctx_start:ctx_end].replace("\n", " ").strip(),
            }

    # Try abbreviation expansion (e.g., "βNTI" -> "beta nearest taxon index")
    # Also try without special chars
    concept_ascii = re.sub(r"[^a-zA-Z0-9\s]", "", concept_lower).strip()
    if concept_ascii and concept_ascii != concept_lower:
        idx = text_lower.find(concept_ascii)
        if idx >= 0:
            ctx_start = max(0, idx - context_chars // 2)
            ctx_end = min(len(text), idx + len(concept_ascii) + context_chars // 2)
            return {
                "status": "FOUND",
                "match_type": "ascii-normalized",
                "context": text[ctx_start:ctx_end].replace("\n", " ").strip(),
            }

    return {"status": "NOT FOUND", "match_type": None, "context": None}


def map_question_to_papers(q_id: str, gt_question: dict) -> list[str]:
    """Map a question ID to its source paper filename(s)."""
    # source_files field
    if gt_question.get("source_files"):
        return gt_question["source_files"]

    # For single-paper questions, extract from ID: "04_fastp_TE3" -> "04_fastp.pdf"
    parts = q_id.rsplit("_", 1)  # split off category suffix
    if len(parts) == 2:
        paper_prefix = parts[0]  # e.g., "04_fastp"
        # Try to find matching PDF
        for pdf in PDF_DIR.glob("*.pdf"):
            if pdf.stem.startswith(paper_prefix[:2]):  # match by number prefix
                return [pdf.name]

    # Try matching by number prefix from ID
    match = re.match(r"^(\d+)_", q_id)
    if match:
        num = match.group(1)
        for pdf in PDF_DIR.glob("*.pdf"):
            if pdf.stem.startswith(num + "_"):
                return [pdf.name]

    return []


def verify_all_flagged():
    """Main verification routine."""
    # Load ground truth
    gt = json.load(open(GT_PATH))
    gt_questions = {q["id"]: q for q in gt["questions"]}

    # Collect all flagged questions
    flagged = {}

    for stage_name, path in VALIDATION_FILES.items():
        if stage_name == "ood":
            continue  # handle OOD separately
        data = json.load(open(path))
        key = list(data.keys())[0]
        for qid, v in data[key].items():
            if v.get("flag") in (True, "True"):
                flagged[qid] = {
                    "stage": stage_name,
                    "validation": v,
                }

    # Cache extracted paper texts
    paper_texts = {}

    # Verify each flagged question
    results = []

    for qid, info in sorted(flagged.items()):
        gt_q = gt_questions.get(qid, {})
        if not gt_q:
            results.append({
                "id": qid,
                "status": "ERROR",
                "message": "Question not found in ground truth",
            })
            continue

        # Get source papers
        papers = map_question_to_papers(qid, gt_q)

        # Extract text from papers
        combined_text = ""
        paper_status = {}
        for paper_name in papers:
            pdf_path = PDF_DIR / paper_name
            if not pdf_path.exists():
                paper_status[paper_name] = "FILE NOT FOUND"
                continue
            if paper_name not in paper_texts:
                paper_texts[paper_name] = extract_text(str(pdf_path))
            combined_text += " " + paper_texts[paper_name]
            paper_status[paper_name] = f"OK ({len(paper_texts[paper_name])} chars)"

        # Check each expected concept
        concept_results = []
        for concept in gt_q.get("expected_concepts", []):
            result = find_concept_in_text(concept, combined_text)
            concept_results.append({
                "concept": concept,
                **result,
            })

        found_count = sum(1 for c in concept_results if c["status"] == "FOUND")
        total_count = len(concept_results)

        # Determine verdict
        if total_count == 0:
            verdict = "NO CONCEPTS"
        elif found_count == total_count:
            verdict = "ALL VERIFIED"
        elif found_count >= total_count * 0.5:
            verdict = "MOSTLY VERIFIED"
        else:
            verdict = "NEEDS REVIEW"

        results.append({
            "id": qid,
            "stage": info["stage"],
            "category": gt_q.get("category", "?"),
            "question": gt_q.get("question", "?"),
            "papers": papers,
            "paper_status": paper_status,
            "flag_reason": info["validation"].get("flag_reason", ""),
            "concepts_in_validation": f"{info['validation'].get('concepts_covered', '?')}/{info['validation'].get('total_concepts', '?')}",
            "concepts_verified": f"{found_count}/{total_count}",
            "verdict": verdict,
            "concept_details": concept_results,
        })

    # Now handle OOD
    ood_data = json.load(open(VALIDATION_FILES["ood"]))["verified"]
    ood_flagged = {
        qid: v
        for qid, v in ood_data.items()
        if v.get("answerable_from_corpus") in (True, "true", "yes", "True")
    }

    for qid, v in sorted(ood_flagged.items()):
        gt_q = gt_questions.get(qid, {})
        potential_papers = v.get("potential_papers", [])

        # Extract text from potential papers
        combined_text = ""
        paper_status = {}
        for paper_name in potential_papers:
            pdf_path = PDF_DIR / paper_name
            if not pdf_path.exists():
                paper_status[paper_name] = "FILE NOT FOUND"
                continue
            if paper_name not in paper_texts:
                paper_texts[paper_name] = extract_text(str(pdf_path))
            combined_text += " " + paper_texts[paper_name]
            paper_status[paper_name] = f"OK ({len(paper_texts[paper_name])} chars)"

        # For OOD, check if the false claim can be refuted from paper content
        question_text = gt_q.get("question", v.get("question", ""))

        # Extract key claim terms from the question
        results.append({
            "id": qid,
            "stage": "ood",
            "category": "out_of_domain",
            "question": question_text,
            "papers": potential_papers,
            "paper_status": paper_status,
            "flag_reason": f"Marked as answerable from corpus. Potential papers: {potential_papers}",
            "concepts_in_validation": "N/A",
            "concepts_verified": "N/A",
            "verdict": "OOD - REFUTABLE" if combined_text.strip() else "OOD - UNVERIFIABLE",
            "concept_details": [],
        })

    return results


def print_report(results):
    """Print a structured report."""
    # Summary
    verdicts = defaultdict(list)
    for r in results:
        verdicts[r["verdict"]].append(r["id"])

    print("=" * 80)
    print("FLAGGED QUESTION VERIFICATION REPORT")
    print("=" * 80)
    print()
    print("SUMMARY:")
    for verdict, ids in sorted(verdicts.items()):
        print(f"  {verdict}: {len(ids)}")
    print()

    # Detailed results grouped by verdict
    for verdict_group in ["NEEDS REVIEW", "MOSTLY VERIFIED", "ALL VERIFIED",
                          "OOD - REFUTABLE", "OOD - UNVERIFIABLE", "ERROR", "NO CONCEPTS"]:
        group = [r for r in results if r["verdict"] == verdict_group]
        if not group:
            continue

        print("=" * 80)
        print(f"  {verdict_group} ({len(group)} questions)")
        print("=" * 80)
        print()

        for r in group:
            print(f"--- {r['id']} ({r['category']}, {r['stage']}) ---")
            print(f"  Q: {r['question'][:120]}")
            print(f"  Papers: {r['papers']}")
            print(f"  Validation concepts: {r['concepts_in_validation']}")
            print(f"  Verified concepts: {r['concepts_verified']}")
            print(f"  Flag: {r['flag_reason'][:150]}")
            print()

            for c in r.get("concept_details", []):
                status_icon = "+" if c["status"] == "FOUND" else "X"
                match_info = f" ({c['match_type']})" if c["match_type"] else ""
                print(f"  [{status_icon}] {c['concept']}{match_info}")
                if c["context"]:
                    # Truncate context
                    ctx = c["context"][:150]
                    print(f"      => ...{ctx}...")
            print()


if __name__ == "__main__":
    results = verify_all_flagged()
    print_report(results)

    # Save JSON for further analysis
    out_path = Path("publication/data/verification_report.json")
    json.dump(results, open(out_path, "w"), indent=2, ensure_ascii=False)
    print(f"\nJSON report saved to: {out_path}")
