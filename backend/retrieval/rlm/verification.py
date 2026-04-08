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
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class VerifiedClaim:
    """A single claim from the report with verification status."""
    claim_text: str
    status: str  # "verified", "unverified", "partial", "no_citation"
    confidence: float  # 0.0 - 1.0
    citation_numbers: List[int] = field(default_factory=list)
    evidence: str = ""  # Explanation from verifier


@dataclass
class VerificationResult:
    """Aggregate verification outcome for a full report."""
    total_claims: int = 0
    verified: int = 0
    unverified: int = 0
    partial: int = 0
    no_citation: int = 0
    overall_confidence: float = 0.0
    flagged_claims: List[VerifiedClaim] = field(default_factory=list)


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

        # Build lookup: citation number → Citation object
        corpus_citations = [
            c for c in context.citations
            if c.citation_type == CitationType.CORPUS
        ]

        for claim_text in claims:
            # 2. Find citation numbers referenced in this claim
            citation_nums = [int(n) for n in re.findall(r'\[(\d+)\]', claim_text)]

            if not citation_nums:
                # Claim has no corpus citation — note it but don't flag
                vc = VerifiedClaim(
                    claim_text=claim_text,
                    status="no_citation",
                    confidence=0.5,
                )
                result.no_citation += 1
                continue

            # 3. Gather source text for each cited number
            source_texts = []
            for num in citation_nums:
                idx = num - 1  # citations are 1-indexed
                if 0 <= idx < len(corpus_citations):
                    cit = corpus_citations[idx]
                    source_texts.append(
                        f"[{num}] {cit.doc_name}, page {cit.page}: \"{cit.quote[:300]}\""
                    )

            if not source_texts:
                vc = VerifiedClaim(
                    claim_text=claim_text,
                    status="unverified",
                    confidence=0.0,
                    citation_numbers=citation_nums,
                    evidence="Citation number(s) out of range",
                )
                result.unverified += 1
                result.flagged_claims.append(vc)
                continue

            # 4. LLM verification call
            vc = await self._verify_single_claim(
                claim_text, source_texts, citation_nums
            )

            if vc.status == "verified":
                result.verified += 1
            elif vc.status == "partial":
                result.partial += 1
                result.flagged_claims.append(vc)
            else:
                result.unverified += 1
                result.flagged_claims.append(vc)

        # Overall confidence
        denominator = result.total_claims - result.no_citation
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
        citation_nums: List[int],
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
            response = await self.router.generate(
                model_identifier=self.model_identifier,
                prompt=prompt,
                options={"temperature": 0.0, "num_predict": 200, "num_ctx": 24576},
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

        except Exception as e:
            logger.error(f"Verification LLM call failed: {e}")
            return VerifiedClaim(
                claim_text=claim,
                status="unverified",
                confidence=0.0,
                citation_numbers=citation_nums,
                evidence=f"Verification failed: {e}",
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

        if result.flagged_claims:
            lines.append("\n### Flagged Claims\n")
            for vc in result.flagged_claims[:10]:  # Limit output
                status_emoji = {"unverified": "!!", "partial": "~"}
                tag = status_emoji.get(vc.status, "?")
                lines.append(
                    f"- [{tag}] \"{vc.claim_text[:120]}...\" "
                    f"— {vc.evidence}"
                )

        return "\n".join(lines)
