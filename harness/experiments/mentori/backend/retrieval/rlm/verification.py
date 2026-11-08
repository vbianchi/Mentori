"""
RLM Report Verification - Post-generation claim verification.

Splits a report into sentence-level claims, matches each claim to its
corpus citation(s), and uses an LLM to check whether the cited source
actually supports the claim.

This is an opt-in step (doubles LLM cost) that adds a "Verification
Summary" section to the report.
"""

import re
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from backend.agents.lock_adapter import LockCallError
from experiments.runner import run_context as rc   # on sys.path once lock_adapter is imported

logger = logging.getLogger(__name__)

# Q8 (D68): llm_summarize writes each citation as [paper.pdf:pN]; the verifier reads the same form (it read [k] as
# the k-th corpus citation, a third numbering, rlm F17)
INLINE_CITATION = re.compile(r'\[([^\[\]]+?\.pdf):p(\d+)\]', re.IGNORECASE)


@dataclass
class VerifiedClaim:
    """A single claim from the report with verification status."""
    claim_text: str
    status: str  # "verified", "unverified", "partial", "no_citation", "error" (the verifier's call failed, A5)
    confidence: Optional[float]  # 0.0 - 1.0; None for "error" (A5: a failed call is not a value)
    citation_numbers: List[str] = field(default_factory=list)  # the [paper.pdf:pN] labels of the claim
    evidence: str = ""  # Explanation from verifier
    error: Optional[dict] = None  # status "error": the failed call's record seq, status and error


@dataclass
class VerificationResult:
    """Aggregate verification outcome for a full report."""
    total_claims: int = 0
    verified: int = 0
    unverified: int = 0
    partial: int = 0
    no_citation: int = 0
    errors: int = 0   # A5: claims whose verifier call failed, kept out of every other count and the confidence
    overall_confidence: float = 0.0
    flagged_claims: List[VerifiedClaim] = field(default_factory=list)
    failed_claims: List[VerifiedClaim] = field(default_factory=list)


class ReportVerifier:
    """
    Verifies that claims in an RLM report are supported by their cited sources.

    Pipeline:
    1. Split report text into sentence-level claims
    2. For each claim, identify corpus citations via [N] references
    3. Retrieve the actual source chunk text from RLMContext
    4. LLM call: "Does this source support this claim? YES / NO / PARTIAL"
    5. Return VerificationResult with per-claim confidence
    """

    def __init__(self, model_router, model_identifier: str):
        self.router = model_router
        self.model_identifier = model_identifier

    async def verify_report(
        self,
        report_text: str,
        context,  # RLMContext
    ) -> VerificationResult:
        """
        Verify all claims in a report against their cited sources.

        Args:
            report_text: The final report markdown text
            context: RLMContext with document chunks and citations

        Returns:
            VerificationResult with per-claim verdicts
        """
        from .context import CitationType

        result = VerificationResult()

        # 1. Extract claims (sentences) from the body, skip the Sources section
        body = report_text.split("## Sources")[0] if "## Sources" in report_text else report_text
        claims = self._split_into_claims(body)

        if not claims:
            logger.info("No claims to verify")
            return result

        result.total_claims = len(claims)

        # Corpus citations, looked up by (document, page)
        corpus_citations = [
            c for c in context.citations
            if c.citation_type == CitationType.CORPUS
        ]

        for claim_text in claims:
            # 2. Find the [paper.pdf:pN] citations of this claim (Q8)
            labels = [(doc, int(page)) for doc, page in INLINE_CITATION.findall(claim_text)]
            citation_nums = [f"{doc}:p{page}" for doc, page in labels]

            if not citation_nums:
                # Claim has no corpus citation — note it but don't flag
                vc = VerifiedClaim(
                    claim_text=claim_text,
                    status="no_citation",
                    confidence=0.5,
                )
                result.no_citation += 1
                continue

            # 3. Gather the source text of each citation: every corpus citation of that document and page, each
            # whole (D25, cuts.md verification.py:114: it showed 300 characters of each quote)
            source_texts = []
            ids = []
            for doc, page in labels:
                for cit in corpus_citations:
                    if cit.doc_name.lower() == doc.lower() and cit.page == page:
                        source_texts.append(f"[{cit.doc_name}:p{cit.page}] \"{cit.quote}\"")
                        if cit.chunk_id and cit.chunk_id not in ids:
                            ids.append(cit.chunk_id)

            if not source_texts:
                vc = VerifiedClaim(
                    claim_text=claim_text,
                    status="unverified",
                    confidence=0.0,
                    citation_numbers=citation_nums,
                    evidence="No collected citation for this document and page",
                )
                result.unverified += 1
                result.flagged_claims.append(vc)
                continue

            # 4. LLM verification call; A6/D37: the cited chunks' ids are its passages
            rc.set_passages(ids)
            vc = await self._verify_single_claim(
                claim_text, source_texts, citation_nums
            )

            if vc.status == "verified":
                result.verified += 1
            elif vc.status == "partial":
                result.partial += 1
                result.flagged_claims.append(vc)
            elif vc.status == "error":
                result.errors += 1
                result.failed_claims.append(vc)
            else:
                result.unverified += 1
                result.flagged_claims.append(vc)

        # Overall confidence, over the claims whose verifier call returned (A5)
        denominator = result.total_claims - result.no_citation - result.errors
        if denominator > 0:
            result.overall_confidence = (
                (result.verified + 0.5 * result.partial) / denominator
            )
        else:
            result.overall_confidence = 1.0

        logger.info(
            f"Verification complete: {result.verified}/{result.total_claims} verified, "
            f"{result.unverified} unverified, {result.partial} partial, "
            f"confidence={result.overall_confidence:.2f}"
        )

        return result

    async def _verify_single_claim(
        self,
        claim: str,
        source_texts: List[str],
        citation_nums: List[str],
    ) -> VerifiedClaim:
        """Verify a single claim against its source text via LLM."""
        sources_block = "\n".join(source_texts)

        prompt = f"""You are a fact-checking assistant. Determine whether the source text supports the claim.

CLAIM: {claim}

SOURCE TEXT:
{sources_block}

Answer with exactly one of:
- YES — the source directly supports this claim
- PARTIAL — the source partially supports it or the claim extrapolates slightly
- NO — the source does not support this claim or contradicts it

Then on the next line, write a brief (1 sentence) explanation.

Format:
VERDICT: YES/PARTIAL/NO
REASON: ...
"""

        try:
            # Under the lock at the maker's default (D66: a Mentori component); no options (cuts.md
            # verification.py:192)
            response = await self.router.generate(
                model_identifier=self.model_identifier,
                prompt=prompt,
            )

            result_text = response.get("response", "")

            # Parse verdict
            verdict_match = re.search(r"VERDICT:\s*(YES|PARTIAL|NO)", result_text, re.IGNORECASE)
            reason_match = re.search(r"REASON:\s*(.+)", result_text, re.IGNORECASE)

            if verdict_match:
                raw_verdict = verdict_match.group(1).upper()
                status_map = {"YES": "verified", "PARTIAL": "partial", "NO": "unverified"}
                status = status_map.get(raw_verdict, "unverified")
                confidence_map = {"YES": 1.0, "PARTIAL": 0.5, "NO": 0.0}
                confidence = confidence_map.get(raw_verdict, 0.0)
            else:
                status = "unverified"
                confidence = 0.0

            reason = reason_match.group(1).strip() if reason_match else ""

            return VerifiedClaim(
                claim_text=claim,
                status=status,
                confidence=confidence,
                citation_numbers=citation_nums,
                evidence=reason,
            )

        except LockCallError as e:
            # A5: a failed call is recorded as status "error", never as an unverified claim with confidence 0.
            # A LockError or RunContextError is not caught (Q38).
            logger.error(f"Verification LLM call failed: {e}")
            rec = e.record or {}
            return VerifiedClaim(
                claim_text=claim,
                status="error",
                confidence=None,
                citation_numbers=citation_nums,
                error={"seq": rec.get("seq"), "status": rec.get("status"), "error": rec.get("error")},
            )

    def _split_into_claims(self, text: str) -> List[str]:
        """Split report body into sentence-level claims.

        Skips headings (lines starting with #) and very short fragments.
        """
        # Remove markdown headings
        lines = [
            line for line in text.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        body = " ".join(lines)

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', body)

        # Filter: only keep substantive claims (>30 chars, not just citations)
        claims = []
        for s in sentences:
            s = s.strip()
            if len(s) > 30 and not re.match(r'^\[?\d+\]', s):
                claims.append(s)

        return claims

    def format_summary(self, result: VerificationResult) -> str:
        """Format verification result as a markdown section for the report."""
        lines = [
            "\n---\n## Verification Summary\n",
            f"- **Total claims checked**: {result.total_claims}",
            f"- **Verified**: {result.verified}",
            f"- **Partially supported**: {result.partial}",
            f"- **Unsupported**: {result.unverified}",
            f"- **Without citation**: {result.no_citation}",
            f"- **Overall confidence**: {result.overall_confidence:.0%}",
        ]

        if result.errors:
            lines.append(f"- **Not checked (verifier call failed)**: {result.errors}")

        if result.flagged_claims:
            lines.append("\n### Flagged Claims\n")
            # D25 (cuts.md verification.py:269, :273): every flagged claim, whole (it listed 10, cut to 120)
            for vc in result.flagged_claims:
                status_emoji = {"unverified": "!!", "partial": "~"}
                tag = status_emoji.get(vc.status, "?")
                lines.append(
                    f"- [{tag}] \"{vc.claim_text}\" "
                    f"— {vc.evidence}"
                )

        return "\n".join(lines)

    def record(self, result: VerificationResult) -> dict:
        """The verification pass for the run's record (A6/D37): the counts, the flagged claims and the claims whose
        verifier call failed (with the failed call's record seq)."""
        return asdict(result)
