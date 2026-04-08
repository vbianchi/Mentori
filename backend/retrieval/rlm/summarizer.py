"""
Citation-Grounded Summarizer - Ensures every claim is backed by source material.

This module implements a two-stage summarization process:
1. EXTRACT: Pull facts from chunks with explicit source references
2. SYNTHESIZE: Write summary using ONLY extracted facts

This prevents hallucination by forcing all claims through the extraction stage.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .context import ChunkResult, Citation
from backend.agents.prompts import get_summarizer_prompt

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFact:
    """A fact extracted from source material with provenance."""
    fact: str
    source_chunks: List[int]  # Which chunks this came from
    quotes: List[str]  # Supporting quotes
    confidence: float = 1.0


@dataclass
class SummaryResult:
    """Result of a grounded summarization."""
    text: str
    citations: List[Citation]
    uncited_claims: List[str]
    extracted_facts: List[ExtractedFact] = field(default_factory=list)
    verification_score: float = 1.0  # 1.0 = all claims cited


class CitationGroundedSummarizer:
    """
    Two-stage summarizer that prevents hallucination through explicit fact extraction.

    Stage 1 (Extract): LLM identifies facts in chunks and notes source
    Stage 2 (Synthesize): LLM writes summary using ONLY extracted facts

    Note: Prompts are now centralized in backend/agents/prompts.py
    """

    def __init__(self, model_router, model_identifier: str):
        """
        Initialize the summarizer.

        Args:
            model_router: ModelRouter for LLM calls
            model_identifier: Model to use
        """
        self.router = model_router
        self.model_identifier = model_identifier

    async def summarize(
        self,
        chunks: List[ChunkResult],
        task: str,
        cite_fn,  # Function to register citations
        max_tokens: int = 1000
    ) -> SummaryResult:
        """
        Perform grounded summarization with citation tracking.

        Args:
            chunks: Source chunks to summarize
            task: What to summarize (e.g., "methods", "findings")
            cite_fn: Function to register citations in context
            max_tokens: Max summary length

        Returns:
            SummaryResult with text, citations, and any uncited claims
        """
        if not chunks:
            return SummaryResult(
                text="No source material provided.",
                citations=[],
                uncited_claims=[]
            )

        # Stage 1: Extract facts
        logger.info(f"Stage 1: Extracting facts from {len(chunks)} chunks")
        extracted = await self._extract_facts(chunks, task)

        if not extracted.get("facts"):
            return SummaryResult(
                text="No relevant facts could be extracted from the source material.",
                citations=[],
                uncited_claims=[],
                extracted_facts=[]
            )

        # Stage 2: Synthesize from facts
        logger.info(f"Stage 2: Synthesizing from {len(extracted['facts'])} facts")
        summary = await self._synthesize(extracted, task, max_tokens)

        # Create citations for all referenced chunks
        citations = []
        chunk_map = {i + 1: c for i, c in enumerate(chunks)}

        for fact in extracted.get("facts", []):
            for chunk_id in fact.get("chunk_ids", []):
                if chunk_id in chunk_map:
                    chunk = chunk_map[chunk_id]
                    citation = cite_fn(
                        doc_name=chunk.doc_name,
                        page=chunk.page,
                        quote=fact.get("quote", chunk.text[:100]),
                        chunk_idx=chunk.chunk_idx
                    )
                    citations.append(citation)

        # Verify citations in summary
        uncited = self._find_uncited_claims(summary)

        # Calculate verification score
        total_sentences = len(re.split(r'[.!?]+', summary))
        cited_sentences = sum(1 for s in re.split(r'[.!?]+', summary) if '[' in s)
        verification_score = cited_sentences / max(total_sentences, 1)

        # Convert to ExtractedFact objects
        extracted_facts = [
            ExtractedFact(
                fact=f["fact"],
                source_chunks=f.get("chunk_ids", []),
                quotes=f.get("quote", "").split('"') if isinstance(f.get("quote"), str) else [f.get("quote", "")]
            )
            for f in extracted.get("facts", [])
        ]

        return SummaryResult(
            text=summary,
            citations=citations,
            uncited_claims=uncited,
            extracted_facts=extracted_facts,
            verification_score=verification_score
        )

    async def _extract_facts(self, chunks: List[ChunkResult], task: str) -> Dict[str, Any]:
        """Stage 1: Extract facts with source references."""

        # Build chunks text with IDs
        chunks_text = []
        for i, chunk in enumerate(chunks):
            chunks_text.append(
                f"[CHUNK {i + 1}] (Source: {chunk.doc_name}, Page {chunk.page})\n{chunk.text}"
            )

        prompt = get_summarizer_prompt("extraction").format(
            chunks_with_ids="\n\n---\n\n".join(chunks_text),
            task=task
        )

        try:
            response = await self.router.generate(
                model_identifier=self.model_identifier,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 8192, "num_ctx": 24576}
            )

            result_text = response.get("response", "{}")

            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning("Failed to parse extraction JSON, using raw response")

            # Fallback: try to extract facts manually
            return {"facts": [], "missing_info": ["Extraction parsing failed"]}

        except Exception as e:
            logger.error(f"Fact extraction failed: {e}")
            return {"facts": [], "missing_info": [str(e)]}

    async def _synthesize(self, extracted: Dict[str, Any], task: str, max_tokens: int) -> str:
        """Stage 2: Write summary from extracted facts only."""

        facts_json = json.dumps(extracted.get("facts", []), indent=2)
        missing_info = extracted.get("missing_info", [])

        prompt = get_summarizer_prompt("synthesis").format(
            facts_json=facts_json,
            missing_info=", ".join(missing_info) if missing_info else "None",
            task=task
        )

        try:
            response = await self.router.generate(
                model_identifier=self.model_identifier,
                prompt=prompt,
                options={"temperature": 0.2, "num_predict": max_tokens, "num_ctx": 24576}
            )

            return response.get("response", "Synthesis failed.")

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return f"Error during synthesis: {str(e)}"

    def _find_uncited_claims(self, text: str) -> List[str]:
        """Find sentences that might be claims but lack citations."""
        uncited = []

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            sentence = sentence.strip()

            # Skip short sentences
            if len(sentence) < 30:
                continue

            # Skip sentences that are questions or meta-statements
            if sentence.startswith(("This summary", "The", "Note:", "Not found")):
                continue

            # Check if sentence has a citation
            if '[' not in sentence:
                # Check if it looks like a factual claim
                claim_indicators = [
                    "found", "showed", "demonstrated", "concluded",
                    "reported", "observed", "indicates", "suggests",
                    "increased", "decreased", "significant", "results",
                    "study", "research", "evidence", "data"
                ]
                if any(ind in sentence.lower() for ind in claim_indicators):
                    uncited.append(sentence)

        return uncited[:10]  # Limit to 10


class ChapterSummarizer:
    """
    Specialized summarizer for long documents with chapter structure.

    Processes each chapter/section independently to maintain context
    and generate comprehensive, citation-backed summaries.
    """

    def __init__(self, model_router, model_identifier: str):
        self.base_summarizer = CitationGroundedSummarizer(model_router, model_identifier)
        self.router = model_router
        self.model_identifier = model_identifier

    async def summarize_chapters(
        self,
        context,  # RLMContext
        doc_name: str,
        preserve_tables: bool = True,
        preserve_figures: bool = True
    ) -> Dict[str, SummaryResult]:
        """
        Summarize each chapter of a document.

        Args:
            context: RLMContext with loaded documents
            doc_name: Document to summarize
            preserve_tables: Whether to extract and describe tables
            preserve_figures: Whether to extract and describe figures

        Returns:
            Dict mapping chapter/section names to SummaryResult
        """
        structure = context.get_document_structure(doc_name)

        if "error" in structure:
            return {"error": SummaryResult(text=structure["error"], citations=[], uncited_claims=[])}

        # Get all pages/sections
        pages = structure.get("pages", [])

        chapter_summaries = {}

        # Process page by page (could be enhanced with TOC parsing)
        current_chapter = "Document"
        current_chunks = []

        for page_info in pages:
            page = page_info["page"]
            chunks = context.get_chunks_by_page(doc_name, page)

            # Check if this starts a new chapter (heuristic: headers)
            for chunk in chunks:
                # Simple chapter detection - look for header patterns
                if self._looks_like_chapter_header(chunk.text):
                    # Summarize previous chapter
                    if current_chunks:
                        task = f"Summarize the main content of '{current_chapter}'"
                        if preserve_tables:
                            task += ", describing any tables in detail"
                        if preserve_figures:
                            task += ", explaining any figures or diagrams"

                        result = await self.base_summarizer.summarize(
                            current_chunks,
                            task=task,
                            cite_fn=context.cite
                        )
                        chapter_summaries[current_chapter] = result

                    # Start new chapter
                    current_chapter = self._extract_chapter_title(chunk.text)
                    current_chunks = []

            current_chunks.extend(chunks)

        # Summarize last chapter
        if current_chunks:
            task = f"Summarize the main content of '{current_chapter}'"
            result = await self.base_summarizer.summarize(
                current_chunks,
                task=task,
                cite_fn=context.cite
            )
            chapter_summaries[current_chapter] = result

        return chapter_summaries

    def _looks_like_chapter_header(self, text: str) -> bool:
        """Check if text looks like a chapter/section header."""
        first_line = text.split('\n')[0].strip()

        # Common patterns
        patterns = [
            r'^(Chapter|Section|Part)\s+\d+',
            r'^\d+\.\s+[A-Z]',  # "1. Introduction"
            r'^[A-Z][A-Z\s]{5,}$',  # ALL CAPS header
            r'^(Introduction|Methods|Results|Discussion|Conclusion|Abstract|Background)',
        ]

        for pattern in patterns:
            if re.match(pattern, first_line, re.IGNORECASE):
                return True

        return False

    def _extract_chapter_title(self, text: str) -> str:
        """Extract chapter title from text."""
        first_line = text.split('\n')[0].strip()
        # Clean up
        title = re.sub(r'^(Chapter|Section|Part)\s+\d+[:\s]*', '', first_line)
        title = re.sub(r'^\d+\.\s*', '', title)
        return title[:100] or "Untitled Section"


@dataclass
class PageSummaryOutput:
    """Output from page-by-page summarization."""
    page: int
    summary: str
    citations: List[Citation]
    chunk_count: int
    word_count: int


class PageSummarizer:
    """
    Deterministic page-by-page summarizer.

    Processes EVERY page sequentially - no LLM decision making about what to process.
    This ensures:
    - Complete coverage (every page summarized)
    - Predictable cost (N pages = N LLM calls)
    - Reproducible results
    """

    def __init__(self, model_router, model_identifier: str):
        self.base_summarizer = CitationGroundedSummarizer(model_router, model_identifier)
        self.router = model_router
        self.model_identifier = model_identifier

    async def _direct_summarize(
        self,
        chunks: List[ChunkResult],
        task: str,
        cite_fn,
        max_tokens: int = 500
    ) -> SummaryResult:
        """
        Direct single-stage summarization (simpler, more reliable than two-stage).

        This bypasses the fact-extraction stage and directly summarizes the content.
        Better for general documents where the two-stage approach might be too strict.
        """
        if not chunks:
            return SummaryResult(
                text="No content available.",
                citations=[],
                uncited_claims=[]
            )

        # Build context from chunks
        chunks_text = []
        for i, chunk in enumerate(chunks):
            chunks_text.append(
                f"[Source {i + 1}: {chunk.doc_name}, Page {chunk.page}]\n{chunk.text}"
            )

        prompt = get_summarizer_prompt("direct_summarize").format(
            task=task,
            chunks_text=chr(10).join(chunks_text)
        )

        try:
            # Use generous token limit - summaries need room
            response = await self.router.chat(
                model_identifier=self.model_identifier,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3, "num_predict": max(max_tokens, 1000), "num_ctx": 24576},
                think=False
            )
            logger.info(f"Direct summarize response length: {len(response.get('message', {}).get('content', ''))}")

            summary_text = response.get("message", {}).get("content", "Summary generation failed.")

            # Create citations for referenced sources
            citations = []
            for i, chunk in enumerate(chunks):
                if f"[Source {i + 1}]" in summary_text or f"[{i + 1}]" in summary_text:
                    citation = cite_fn(
                        doc_name=chunk.doc_name,
                        page=chunk.page,
                        quote=chunk.text[:200],
                        chunk_idx=chunk.chunk_idx
                    )
                    citations.append(citation)

            return SummaryResult(
                text=summary_text,
                citations=citations,
                uncited_claims=[]
            )

        except Exception as e:
            logger.error(f"Direct summarization failed: {e}")
            return SummaryResult(
                text=f"Summarization failed: {str(e)}",
                citations=[],
                uncited_claims=[]
            )

    async def summarize_pages(
        self,
        context,  # RLMContext
        doc_name: str,
        pages: Optional[List[int]] = None,  # None = all pages
        words_per_page: int = 200,
        include_context_overlap: bool = True,
        output_dir: Optional[str] = None,
        use_chunk_pagination: bool = False,  # Use chunk-based virtual pages
        chunks_per_page: int = 5  # Chunks per virtual page when using chunk pagination
    ) -> Dict[str, Any]:
        """
        Summarize document page by page (or chunk-group by chunk-group).

        Args:
            context: RLMContext with loaded documents
            doc_name: Document to summarize
            pages: Specific pages to process (None = all)
            words_per_page: Target word count per page summary
            include_context_overlap: Include last chunk from prev page for continuity
            output_dir: Directory to save individual page summaries
            use_chunk_pagination: If True, use chunk-based virtual pages instead of actual pages
            chunks_per_page: Number of chunks per virtual page

        Returns:
            Dict with:
            - summaries: List[PageSummaryOutput]
            - full_summary: str (stitched together)
            - statistics: processing stats
            - output_files: paths to saved files (if output_dir provided)
        """
        import os
        from datetime import datetime

        structure = context.get_document_structure(doc_name)

        if "error" in structure:
            return {"error": structure["error"]}

        total_pages = structure.get("total_pages", 0)
        total_chunks = structure.get("total_chunks", 0)

        # Check if we should use chunk-based pagination
        # This handles documents where page metadata wasn't properly extracted
        if structure.get("virtual_pages") or (total_pages <= 1 and total_chunks > 10):
            use_chunk_pagination = True
            chunks_per_page = structure.get("chunks_per_page", 5)
            total_pages = (total_chunks + chunks_per_page - 1) // chunks_per_page
            logger.info(f"Using chunk-based pagination: {total_chunks} chunks -> {total_pages} virtual pages")

        # Determine pages to process
        if pages is None:
            pages_to_process = list(range(1, total_pages + 1))
        else:
            pages_to_process = [p for p in pages if 1 <= p <= total_pages]

        if not pages_to_process:
            return {"error": f"No valid pages to process. Document has {total_pages} pages."}

        logger.info(f"PageSummarizer: Processing {len(pages_to_process)} {'virtual ' if use_chunk_pagination else ''}pages of '{doc_name}'")

        # Setup output directory if specified
        output_files = {}
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(os.path.join(output_dir, "pages"), exist_ok=True)

            # Write metadata
            metadata = {
                "doc_name": doc_name,
                "total_pages": total_pages,
                "pages_processed": pages_to_process,
                "words_per_page": words_per_page,
                "started_at": datetime.utcnow().isoformat(),
                "model": self.model_identifier
            }
            metadata_path = os.path.join(output_dir, "metadata.json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            output_files["metadata"] = metadata_path

        # Process each page
        summaries = []
        previous_last_chunk = None
        all_citations = []

        for page_num in pages_to_process:
            logger.info(f"PageSummarizer: Processing {'virtual ' if use_chunk_pagination else ''}page {page_num}/{total_pages}")

            # Get chunks for this page
            if use_chunk_pagination:
                # Chunk-based pagination: get chunk range for this virtual page
                start_chunk = (page_num - 1) * chunks_per_page
                end_chunk = min(start_chunk + chunks_per_page, total_chunks)
                chunks = context.get_chunks_range(doc_name, start_chunk, end_chunk)
                logger.info(f"  Chunks {start_chunk}-{end_chunk} for virtual page {page_num}")
            else:
                # Normal page-based: get chunks by page number
                chunks = context.get_chunks_by_page(doc_name, page_num)

            if not chunks:
                # Empty page - skip but note it
                summaries.append(PageSummaryOutput(
                    page=page_num,
                    summary=f"*Page {page_num}: No text content*",
                    citations=[],
                    chunk_count=0,
                    word_count=0
                ))
                continue

            # Add context overlap from previous page
            if include_context_overlap and previous_last_chunk:
                chunks_with_context = [previous_last_chunk] + chunks
            else:
                chunks_with_context = chunks

            # Remember last chunk for next page's context
            previous_last_chunk = chunks[-1] if chunks else None

            # Summarize this page using direct summarization (simpler, more reliable)
            task = f"Summarize the content in approximately {words_per_page} words. Preserve key findings, data points, and important details."

            result = await self._direct_summarize(
                chunks_with_context,
                task=task,
                cite_fn=context.cite,
                max_tokens=words_per_page * 2
            )

            page_summary = PageSummaryOutput(
                page=page_num,
                summary=result.text,
                citations=result.citations,
                chunk_count=len(chunks),
                word_count=len(result.text.split())
            )
            summaries.append(page_summary)
            all_citations.extend(result.citations)

            # Save individual page summary if output_dir specified
            if output_dir:
                page_path = os.path.join(output_dir, "pages", f"page_{page_num:03d}.md")
                with open(page_path, "w") as f:
                    f.write(f"# Page {page_num}\n\n")
                    f.write(result.text)
                    f.write(f"\n\n---\n*Chunks processed: {len(chunks)}*\n")
                output_files[f"page_{page_num}"] = page_path

        # Build full stitched summary
        full_summary_parts = [f"# Summary of {doc_name}\n"]
        full_summary_parts.append(f"*Document condensed from {total_pages} pages to {len(summaries)} summaries*\n")
        full_summary_parts.append(f"*Note: This is a condensed version. Each page has been summarized to ~{words_per_page} words.*\n\n")

        for ps in summaries:
            full_summary_parts.append(f"## Page {ps.page}\n")
            full_summary_parts.append(ps.summary)
            full_summary_parts.append("\n\n")

        # Add references section
        full_summary_parts.append("---\n## References\n")
        seen_refs = set()
        for cit in all_citations:
            key = (cit.doc_name, cit.page)
            if key not in seen_refs:
                seen_refs.add(key)
                full_summary_parts.append(f"- {cit.doc_name}, page {cit.page}\n")

        full_summary = "".join(full_summary_parts)

        # Save full summary if output_dir specified
        if output_dir:
            full_path = os.path.join(output_dir, "full_summary.md")
            with open(full_path, "w") as f:
                f.write(full_summary)
            output_files["full_summary"] = full_path

            # Save citations
            citations_path = os.path.join(output_dir, "citations.json")
            citations_data = [
                {"doc_name": c.doc_name, "page": c.page, "quote": c.quote[:200]}
                for c in all_citations
            ]
            with open(citations_path, "w") as f:
                json.dump(citations_data, f, indent=2)
            output_files["citations"] = citations_path

            # Update metadata with completion
            metadata["completed_at"] = datetime.utcnow().isoformat()
            metadata["total_citations"] = len(all_citations)
            metadata["total_words"] = sum(ps.word_count for ps in summaries)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

        # Build statistics
        statistics = {
            "pages_processed": len(summaries),
            "total_chunks": sum(ps.chunk_count for ps in summaries),
            "total_words": sum(ps.word_count for ps in summaries),
            "total_citations": len(all_citations),
            "llm_calls": len([s for s in summaries if s.chunk_count > 0])  # Only pages with content
        }

        return {
            "summaries": summaries,
            "full_summary": full_summary,
            "statistics": statistics,
            "output_files": output_files if output_dir else None
        }
