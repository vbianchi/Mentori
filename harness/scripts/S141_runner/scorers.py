"""S141 step 1.6 — scorers, and a citation census that records the pattern rather than a verdict.

The lesson this module is built around cost us three mistakes in one day, one of them mine. A count
whose value depends on which syntactic pattern you look for is a pattern detector, not a count:

  · the archive records `retrieved_passages` as the integer 10 and loses passage identity forever
  · `gemini.py` reads a missing token count as `or 0` and stores a real answer as zero output
  · I counted `[file:page]` citations, found none in the RLM arms, and reported "RLM emits no
    citations" — when RLM cites through `file.pdf, page N` and `[N]`, heavily

So nothing here stores a bare count. Every citation is recorded **with the pattern that matched
it**, and every aggregate is derived from that record. When a definition changes — and the 27
versus 39 disagreement on multi_hop's fabricated pages is exactly a definition disagreement — the
numbers are recomputable from stored data instead of requiring a re-run.

`_evaluate_citations` (`exp1_rlm_vs_singlepass.py`) matches three patterns, and its two aggregates
are fed by different subsets, which is worth stating because it is not obvious and it is Methods
material:

    sources_found     <- pattern 1 (inline) + pattern 3 (source line)
    total_citations   <- pattern 1 (inline) + pattern 2 (numbered marker)

Pattern 3 therefore adds a source without incrementing the count; pattern 2 increments the count
with no source attached. Coverage and density move independently by construction.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

# The archive's three patterns, verbatim from `_evaluate_citations`.
P_INLINE = re.compile(r'\[([^\]]+\.pdf):(?:p(?:age)?)?(\d+)\]', re.IGNORECASE)
P_MARKER = re.compile(r'\[(\d+)\]')
P_SOURCE_LINE = re.compile(r'(\S+\.pdf),?\s*page\s*(\d+)', re.IGNORECASE)
# Not one of the archive's. Citation-shaped strings its patterns miss — `[15:4]`,
# `[source_file:01_sarek.pdf, page 20]`. Recorded separately so it can be included or excluded by a
# later definition, never silently folded into either.
P_MALFORMED = re.compile(r'\[([^\]\[]+?):(?:p(?:age)?)?(\d+)\]')

# Every page the pipeline can supply is 0: `smart_ingestor.py:489` reads `chunk.get('page_num', 0)`
# while `chunking.py:103` writes it inside the chunk's metadata. Verified on the rebuilt index —
# all 778 chunks carry page 0. A non-zero page therefore did not come from retrieval.
PIPELINE_SUPPLIES_PAGE = False


@dataclass
class Citation:
    pattern: str          # inline | marker | source_line | malformed
    source: str | None
    page: int | None
    raw: str


@dataclass
class CitationCensus:
    """Row 21's fields, plus the pattern record that makes any of them recomputable."""

    citations: list[Citation] = field(default_factory=list)
    n_gen_sentences: int = 0
    citation_format: str = "none"
    unique_sources: int = 0
    source_coverage: float | None = None
    marker_residue_rate: float = 0.0

    def counts_by_pattern(self) -> dict[str, int]:
        out = {"inline": 0, "marker": 0, "source_line": 0, "malformed": 0}
        for c in self.citations:
            out[c.pattern] += 1
        return out

    def pages_nonzero(self, patterns: Iterable[str] = ("inline", "source_line")) -> int:
        """Citations carrying a page the pipeline never supplied.

        Default is the archive's own pattern set, which is the definition that aligns with the
        deposited `source_coverage` and `total_citations`. Passing `malformed` in as well gives the
        wider definition; both are computable because the pattern is stored.

        A model could in principle lift a page number out of the passage text, so this is a strong
        indicator rather than a proof for any individual citation.
        """
        return sum(1 for c in self.citations
                   if c.pattern in patterns and c.page is not None and c.page != 0)

    def pages_zero(self, patterns: Iterable[str] = ("inline", "source_line")) -> int:
        return sum(1 for c in self.citations
                   if c.pattern in patterns and c.page == 0)

    def as_row_fields(self) -> dict[str, Any]:
        by = self.counts_by_pattern()
        return {
            "citation_census": {
                "by_pattern": by,
                "citation_format": self.citation_format,
                "unique_sources": self.unique_sources,
                "source_coverage": self.source_coverage,
                "n_gen_sentences": self.n_gen_sentences,
                "marker_residue_rate": round(self.marker_residue_rate, 4),
                # Both definitions, because the pattern is stored and neither needs a re-run.
                "pages_nonzero_archive_patterns": self.pages_nonzero(),
                "pages_nonzero_incl_malformed": self.pages_nonzero(
                    ("inline", "source_line", "malformed")),
                "pages_zero": self.pages_zero(),
                "pipeline_supplies_page": PIPELINE_SUPPLIES_PAGE,
                # The archive's aggregates, reproduced so new rows join old ones.
                "archive_total_citations": by["inline"] + by["marker"],
                "archive_sources_from": ["inline", "source_line"],
                "archive_count_from": ["inline", "marker"],
            },
            "citations": [
                {"pattern": c.pattern, "source": c.source, "page": c.page} for c in self.citations
            ],
        }


def census(answer: str, expected_sources: list[str] | None = None) -> CitationCensus:
    text = answer or ""
    cits: list[Citation] = []
    seen_spans: set[tuple[int, int]] = set()

    for m in P_INLINE.finditer(text):
        seen_spans.add(m.span())
        cits.append(Citation("inline", m.group(1), int(m.group(2)), m.group(0)))
    for m in P_SOURCE_LINE.finditer(text):
        cits.append(Citation("source_line", m.group(1), int(m.group(2)), m.group(0)))
    for m in P_MARKER.finditer(text):
        cits.append(Citation("marker", None, None, m.group(0)))
    for m in P_MALFORMED.finditer(text):
        # Only what the archive's inline pattern did not already claim.
        if m.span() not in seen_spans and not m.group(0).lower().endswith(".pdf]"):
            if not P_INLINE.fullmatch(m.group(0)):
                cits.append(Citation("malformed", m.group(1), int(m.group(2)), m.group(0)))

    sources = {c.source for c in cits if c.pattern in ("inline", "source_line") and c.source}
    by = {p: sum(1 for c in cits if c.pattern == p)
          for p in ("inline", "marker", "source_line", "malformed")}

    if by["inline"] and not by["marker"]:
        fmt = "inline"
    elif by["marker"] and not by["inline"]:
        fmt = "marker"
    elif by["marker"] or by["inline"]:
        fmt = "mixed"
    elif by["source_line"]:
        fmt = "source_line_only"
    else:
        fmt = "none"

    coverage = None
    if expected_sources:
        covered = sum(1 for s in expected_sources
                      if any(s.lower() in f.lower() for f in sources))
        coverage = round(covered / len(expected_sources), 4)

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    words = max(len(text.split()), 1)

    return CitationCensus(
        citations=cits,
        n_gen_sentences=len(sentences),
        citation_format=fmt,
        unique_sources=len(sources),
        source_coverage=coverage,
        marker_residue_rate=by["marker"] / words * 100,
    )


def strip_citations(text: str) -> str:
    """Row 21: number overlap is computed on a citation-stripped answer, so a citation's digits
    cannot inflate it — with every page rendered as 0, that would otherwise add a constant.

    Row 21 also requires that two answers differing only in citation *style* score identically, and
    the naive version failed that. `(\\S+\\.pdf)` consumes an opening parenthesis, because `(` is
    non-whitespace, but nothing consumes the closing one — so `(01_sarek.pdf, page 0)` left a
    dangling `)` while `[01_sarek.pdf:0]` left nothing, and two answers with identical content
    reduced to different strings. The residue is cleaned so the invariance actually holds.
    """
    out = P_INLINE.sub(" ", text or "")
    out = P_SOURCE_LINE.sub(" ", out)
    out = P_MARKER.sub(" ", out)
    out = P_MALFORMED.sub(" ", out)
    out = re.sub(r"\(\s*\)|\[\s*\]", " ", out)          # wrappers emptied by the substitutions
    out = re.sub(r"(?<=\s)[\)\]]", " ", out)            # closer left without its opener
    out = re.sub(r"[\(\[](?=\s*[.,;:])", " ", out)      # opener left without its closer
    out = re.sub(r"\s+([.,;:!?])", r"\1", out)          # space pushed against punctuation
    return re.sub(r"\s+", " ", out).strip()


# ── P5: similarity reads the complete answer ─────────────────────────────────

@dataclass
class ScoreCost:
    """P23: every evaluation signal records what it cost to compute."""

    wall_s: float
    device: str | None = None
    input_tokens: int | None = None
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"wall_s": round(self.wall_s, 4), "device": self.device,
                "input_tokens": self.input_tokens, "note": self.note}


def semantic_similarity(expected: str, generated: str, encoder,
                        truncate_chars: int | None = None) -> tuple[float | None, ScoreCost, dict]:
    """The complete answer, both sides.

    The deposited scorer cut both at 2,000 characters (`exp_v4_deterministic_scorer.py:277-278`,
    and two further copies at `exp_v4_0_objective_metrics.py:111-112` and
    `exp_v4_perturn_analysis.py:240` — the third bypasses the shared helper, so grep the literal
    `[:2000]`, not the function name). `truncate_chars` exists only so the archive state can be
    reproduced deliberately; the new arms pass None.

    Removing the cut makes bge-m3's own 8,192-token limit reachable, so the input length is
    measured and recorded rather than assumed to fit (M23).
    """
    t0 = time.time()
    a = expected if truncate_chars is None else expected[:truncate_chars]
    b = generated if truncate_chars is None else generated[:truncate_chars]
    if not a.strip() or not b.strip():
        return None, ScoreCost(time.time() - t0, note="empty input, unscorable"), {}
    embs = encoder.encode([a, b], normalize_embeddings=True)
    sim = float(embs[0] @ embs[1])
    max_len = getattr(encoder, "max_seq_length", None)

    # Count tokens with the encoder's own tokenizer rather than a chars/N heuristic. Measured on
    # this corpus: answers run 3.82 chars per token, so a heuristic tuned on the judge prompt (7.19,
    # inflated by the repetitive template) would have called this wrong in both directions.
    tokens_a = tokens_b = None
    tokenizer = getattr(encoder, "tokenizer", None)
    if tokenizer is not None:
        try:
            tokens_a = len(tokenizer.encode(a, add_special_tokens=False))
            tokens_b = len(tokenizer.encode(b, add_special_tokens=False))
        except Exception:  # noqa: BLE001
            tokens_a = tokens_b = None

    truncated = bool(max_len and tokens_b is not None and tokens_b > max_len)
    meta = {
        "truncate_chars": truncate_chars,
        "expected_chars": len(a), "generated_chars": len(b),
        "expected_tokens": tokens_a, "generated_tokens": tokens_b,
        "encoder_max_seq_length": max_len,
        # M23: removing the 2,000-character cut does not remove truncation for the longest answers,
        # it moves it to the encoder. Measured on the deposit: 5 of 825 answers exceed bge-m3's
        # 8,192-token limit, all multi_hop, longest 10,708 tokens. Those rows are marked rather than
        # reported as complete-answer scores.
        "encoder_truncated": truncated,
        "encoder_tokens_dropped": (tokens_b - max_len) if truncated else 0,
    }
    return sim, ScoreCost(time.time() - t0, device=str(getattr(encoder, "device", None)),
                          input_tokens=tokens_b), meta


# ── P6: MiniCheck's reference text is named, not assumed ─────────────────────

REFERENCE_KINDS = ("expected_answer", "source_passages", "both")


def minicheck_record(reference_text_kind: str, n_claims: int, n_dropped_fragments: int,
                     wall_s: float, device: str | None, model: str | None) -> dict[str, Any]:
    """CL-73: the deposited run compared each answer against the expert answer key while Methods
    said source passages. The kind is recorded per row so the two can never diverge silently again.

    `n_dropped_fragments` is row 21's field and it matters here: `decompose_to_sentences` drops
    fragments under 20 characters and every markdown table row before anything is scored. That
    decomposition is left as-is on the laptop's ruling — changing it would be a metric definition
    change — so the count is recorded instead.
    """
    if reference_text_kind not in REFERENCE_KINDS:
        raise ValueError(f"reference_text_kind must be one of {REFERENCE_KINDS}")
    return {
        "minicheck": {
            "reference_text_kind": reference_text_kind,
            "n_claims_scored": n_claims,
            "n_dropped_fragments": n_dropped_fragments,
            "model": model,
            "cost": ScoreCost(wall_s, device=device).as_dict(),
            "zero_claims_unscorable": n_claims == 0,   # never 0.0, per row 21
        }
    }
