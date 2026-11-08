"""
Document Aggregator - Merges per-page VLM analysis into unified DocumentMetadata.

Takes PageAnalysisResult objects from PageAnalyzer and:
1. Merges metadata from all pages (handles weird papers where title isn't on page 1)
2. Collects all figures, tables, equations, references
3. Validates VLM extractions against OCR text for confidence scoring
4. Produces final DocumentMetadata with extraction confidence scores
"""

import logging
import re
from typing import List, Optional, Dict, Any, Tuple
from collections import Counter
from difflib import SequenceMatcher

from backend.retrieval.schema.document import (
    DocumentMetadata,
    DocumentType,
    PaperMetadata,
    PageAnalysisResult,
    FigureDescription,
    TableDescription,
    EquationDescription,
    Reference,
    ExtractionConfidence,
)

logger = logging.getLogger(__name__)


class DocumentAggregator:
    """
    Aggregates per-page VLM analysis into unified document metadata.

    Handles:
    - Metadata that might appear on any page (not just page 1)
    - Duplicate detection for figures/tables across pages
    - OCR validation with confidence scoring
    - Reference deduplication and normalization
    """

    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize the aggregator.

        Args:
            similarity_threshold: Minimum similarity ratio for OCR validation (0-1)
        """
        self.similarity_threshold = similarity_threshold

    def aggregate(
        self,
        page_results: List[PageAnalysisResult],
        file_path: str,
        file_name: str,
        vlm_model: Optional[str] = None,
        file_hash: Optional[str] = None,
        user_id: Optional[str] = None,
        collection_name: Optional[str] = None
    ) -> DocumentMetadata:
        """
        Aggregate page analysis results into unified DocumentMetadata.

        Args:
            page_results: List of PageAnalysisResult from PageAnalyzer
            file_path: Path to the original document
            file_name: Name of the file
            vlm_model: VLM model used for analysis
            file_hash: Hash for deduplication
            user_id: User ID for the document
            collection_name: Collection name

        Returns:
            Aggregated DocumentMetadata with confidence scores
        """
        if not page_results:
            return DocumentMetadata(
                file_path=file_path,
                file_name=file_name,
                doc_type=DocumentType.UNKNOWN,
                user_id=user_id,
                collection_name=collection_name,
                vlm_model=vlm_model,
                file_hash=file_hash,
                extraction_confidence=ExtractionConfidence(
                    title=0.0, authors=0.0, abstract=0.0,
                    figures=0.0, tables=0.0, references=0.0,
                    overall=0.0
                )
            )

        # Extract and merge metadata from all pages
        title, title_confidence = self._extract_title(page_results)
        authors, authors_confidence = self._extract_authors(page_results)
        abstract, abstract_confidence = self._extract_abstract(page_results)
        keywords = self._extract_keywords(page_results)
        journal = self._extract_journal(page_results)
        doi = self._extract_doi(page_results)
        date = self._extract_date(page_results)

        # Collect all structured content
        figures = self._collect_figures(page_results)
        tables = self._collect_tables(page_results)
        equations = self._collect_equations(page_results)
        references, refs_confidence = self._collect_references(page_results)

        # Collect section headings in order
        sections = self._collect_sections(page_results)

        # Determine document type
        doc_type = self._infer_document_type(page_results, sections)

        # Build paper metadata if it's a paper
        paper_metadata = None
        if doc_type == DocumentType.PAPER:
            paper_metadata = PaperMetadata(
                journal=journal,
                doi=doi,
                abstract=abstract,
                keywords=keywords,
                publication_date=date
            )

        # Calculate overall confidence
        confidence = ExtractionConfidence(
            title=title_confidence,
            authors=authors_confidence,
            abstract=abstract_confidence,
            figures=1.0,  # VLM-only, always trusted
            tables=1.0,
            references=refs_confidence,
            overall=self._calculate_overall_confidence(
                title_confidence, authors_confidence, abstract_confidence, refs_confidence
            )
        )

        # Build final metadata
        metadata = DocumentMetadata(
            file_path=file_path,
            file_name=file_name,
            file_hash=file_hash,
            doc_type=doc_type,
            title=title,
            authors=authors,
            date=date,
            page_count=len(page_results),
            sections=sections,
            has_abstract=bool(abstract),
            has_tables=len(tables) > 0,
            has_figures=len(figures) > 0,
            paper_metadata=paper_metadata,
            user_id=user_id,
            collection_name=collection_name,
            figures=figures,
            tables=tables,
            equations=equations,
            references=references,
            vlm_model=vlm_model,
            extraction_confidence=confidence,
            page_analyses=page_results
        )

        # Generate searchable text summary
        metadata.searchable_text = self._generate_searchable_text(metadata)

        logger.info(
            f"Aggregated {len(page_results)} pages: "
            f"title={bool(title)}, authors={len(authors)}, "
            f"figs={len(figures)}, tables={len(tables)}, refs={len(references)}, "
            f"confidence={confidence.overall:.2f}"
        )

        return metadata

    def _extract_title(self, pages: List[PageAnalysisResult]) -> Tuple[Optional[str], float]:
        """
        Extract title from pages, preferring earlier pages but checking all.

        Returns tuple of (title, confidence_score).
        """
        titles = []
        for page in pages:
            if page.title:
                titles.append((page.page_number, page.title, page.ocr_text))

        if not titles:
            return None, 0.0

        # Prefer title from earliest page
        titles.sort(key=lambda x: x[0])
        best_page, best_title, ocr_text = titles[0]

        # Validate against OCR if available
        confidence = self._validate_against_ocr(best_title, ocr_text)

        # If multiple pages have title, check consistency
        if len(titles) > 1:
            # Check if titles match
            other_titles = [t[1] for t in titles[1:]]
            for other in other_titles:
                if self._string_similarity(best_title, other) > 0.9:
                    confidence = min(1.0, confidence + 0.1)  # Boost confidence if consistent

        return best_title, confidence

    def _extract_authors(self, pages: List[PageAnalysisResult]) -> Tuple[List[str], float]:
        """
        Extract authors from pages, merging and deduplicating.

        Returns tuple of (authors_list, confidence_score).
        """
        all_authors = []
        ocr_texts = []

        for page in pages:
            if page.authors:
                all_authors.extend(page.authors)
                if page.ocr_text:
                    ocr_texts.append(page.ocr_text)

        if not all_authors:
            return [], 0.0

        # Deduplicate authors (fuzzy matching for variations)
        unique_authors = self._deduplicate_authors(all_authors)

        # Validate against OCR
        ocr_combined = " ".join(ocr_texts)
        validated_count = 0
        for author in unique_authors:
            # Check if author name appears in OCR text
            if self._author_in_text(author, ocr_combined):
                validated_count += 1

        confidence = validated_count / len(unique_authors) if unique_authors else 0.0

        return unique_authors, confidence

    def _extract_abstract(self, pages: List[PageAnalysisResult]) -> Tuple[Optional[str], float]:
        """Extract abstract, typically from first few pages."""
        for page in pages[:5]:  # Check first 5 pages
            if page.abstract:
                confidence = self._validate_against_ocr(page.abstract, page.ocr_text)
                return page.abstract, confidence

        return None, 0.0

    def _extract_keywords(self, pages: List[PageAnalysisResult]) -> List[str]:
        """Collect keywords from all pages."""
        keywords = set()
        for page in pages:
            keywords.update(page.keywords)
        return list(keywords)

    def _extract_journal(self, pages: List[PageAnalysisResult]) -> Optional[str]:
        """Extract journal name, typically from first page."""
        for page in pages[:3]:
            if page.journal:
                return page.journal
        return None

    def _extract_doi(self, pages: List[PageAnalysisResult]) -> Optional[str]:
        """Extract DOI, validating format."""
        for page in pages:
            if page.doi:
                # Validate DOI format
                if self._is_valid_doi(page.doi):
                    return page.doi
        return None

    def _extract_date(self, pages: List[PageAnalysisResult]) -> Optional[str]:
        """Extract publication date."""
        for page in pages[:3]:
            if page.date:
                return page.date
        return None

    def _collect_figures(self, pages: List[PageAnalysisResult]) -> List[FigureDescription]:
        """Collect all figures, deduplicating across pages."""
        figures = []
        seen_ids = set()

        for page in pages:
            for fig in page.figures:
                # Normalize figure ID
                normalized_id = self._normalize_figure_id(fig.figure_id)

                if normalized_id not in seen_ids:
                    seen_ids.add(normalized_id)
                    figures.append(fig)
                else:
                    # If duplicate, keep the one with more content
                    for i, existing in enumerate(figures):
                        if self._normalize_figure_id(existing.figure_id) == normalized_id:
                            if len(fig.description) > len(existing.description):
                                figures[i] = fig
                            break

        return figures

    def _collect_tables(self, pages: List[PageAnalysisResult]) -> List[TableDescription]:
        """Collect all tables, deduplicating across pages."""
        tables = []
        seen_ids = set()

        for page in pages:
            for table in page.tables:
                normalized_id = self._normalize_table_id(table.table_id)

                if normalized_id not in seen_ids:
                    seen_ids.add(normalized_id)
                    tables.append(table)
                else:
                    # Keep table with more content
                    for i, existing in enumerate(tables):
                        if self._normalize_table_id(existing.table_id) == normalized_id:
                            if len(table.description) > len(existing.description):
                                tables[i] = table
                            break

        return tables

    def _collect_equations(self, pages: List[PageAnalysisResult]) -> List[EquationDescription]:
        """Collect all equations."""
        equations = []
        seen_ids = set()

        for page in pages:
            for eq in page.equations:
                normalized_id = self._normalize_equation_id(eq.equation_id)

                if normalized_id not in seen_ids:
                    seen_ids.add(normalized_id)
                    equations.append(eq)

        return equations

    def _collect_references(self, pages: List[PageAnalysisResult]) -> Tuple[List[Reference], float]:
        """
        Collect all references, merging duplicates and validating.

        Returns tuple of (references_list, confidence_score).
        """
        references = []
        seen_ids = set()

        for page in pages:
            for ref in page.references:
                # Normalize reference ID
                normalized_id = self._normalize_ref_id(ref.ref_id)

                if normalized_id not in seen_ids:
                    seen_ids.add(normalized_id)
                    references.append(ref)
                else:
                    # Merge with existing reference if more complete
                    for i, existing in enumerate(references):
                        if self._normalize_ref_id(existing.ref_id) == normalized_id:
                            references[i] = self._merge_references(existing, ref)
                            break

        # Sort references by ID number if possible
        references = self._sort_references(references)

        # Calculate confidence based on completeness
        if not references:
            return [], 0.0

        completeness_scores = []
        for ref in references:
            score = self._reference_completeness(ref)
            completeness_scores.append(score)

        confidence = sum(completeness_scores) / len(completeness_scores)

        return references, confidence

    def _collect_sections(self, pages: List[PageAnalysisResult]) -> List[str]:
        """Collect section headings in document order."""
        sections = []
        seen = set()

        for page in sorted(pages, key=lambda p: p.page_number):
            for heading in page.section_headings:
                # Normalize heading
                normalized = heading.strip()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    sections.append(normalized)

        return sections

    def _infer_document_type(
        self,
        pages: List[PageAnalysisResult],
        sections: List[str]
    ) -> DocumentType:
        """Infer document type from content analysis."""
        # Check page types
        page_types = Counter(p.page_type for p in pages)

        # Check sections for paper-like structure
        section_lower = [s.lower() for s in sections]

        paper_sections = {'abstract', 'introduction', 'methods', 'results',
                         'discussion', 'conclusion', 'references'}
        matching_sections = sum(1 for s in section_lower if any(ps in s for ps in paper_sections))

        # Has references section?
        has_refs = any(p.references for p in pages) or 'references' in page_types

        # Has abstract?
        has_abstract = any(p.abstract for p in pages)

        # Score for being a paper
        paper_score = 0
        if has_refs:
            paper_score += 2
        if has_abstract:
            paper_score += 2
        paper_score += matching_sections

        if paper_score >= 3:
            return DocumentType.PAPER

        # Check for other types based on content
        if 'grant' in ' '.join(section_lower):
            return DocumentType.GRANT

        if 'meeting' in ' '.join(section_lower) or 'minutes' in ' '.join(section_lower):
            return DocumentType.MEETING

        return DocumentType.UNKNOWN

    # =========================================================================
    # Validation and Confidence
    # =========================================================================

    def _validate_against_ocr(self, extracted: str, ocr_text: Optional[str]) -> float:
        """
        Validate extracted text against OCR.

        Returns confidence score 0-1.
        """
        if not ocr_text or not extracted:
            return 0.5  # Neutral confidence without OCR

        # Check if extracted text appears in OCR
        extracted_clean = self._normalize_text(extracted)
        ocr_clean = self._normalize_text(ocr_text)

        # Exact substring match
        if extracted_clean in ocr_clean:
            return 1.0

        # Fuzzy match - find best matching substring
        similarity = self._find_best_substring_match(extracted_clean, ocr_clean)

        return similarity

    def _find_best_substring_match(self, needle: str, haystack: str) -> float:
        """Find best matching substring similarity."""
        if len(needle) > len(haystack):
            return 0.0

        best_ratio = 0.0
        window_size = len(needle)

        # Slide window over haystack
        for i in range(len(haystack) - window_size + 1):
            window = haystack[i:i + window_size]
            ratio = SequenceMatcher(None, needle, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio

        return best_ratio

    def _author_in_text(self, author: str, text: str) -> bool:
        """Check if author name appears in text (fuzzy)."""
        if not text:
            return False

        text_lower = text.lower()
        author_lower = author.lower()

        # Check full name
        if author_lower in text_lower:
            return True

        # Check last name
        parts = author.split()
        if parts:
            last_name = parts[-1].lower()
            if last_name in text_lower:
                return True

        return False

    def _calculate_overall_confidence(
        self,
        title_conf: float,
        authors_conf: float,
        abstract_conf: float,
        refs_conf: float
    ) -> float:
        """Calculate weighted overall confidence score."""
        # Title and authors are most important
        weights = {
            'title': 0.3,
            'authors': 0.3,
            'abstract': 0.2,
            'references': 0.2
        }

        return (
            weights['title'] * title_conf +
            weights['authors'] * authors_conf +
            weights['abstract'] * abstract_conf +
            weights['references'] * refs_conf
        )

    # =========================================================================
    # Normalization Helpers
    # =========================================================================

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove extra whitespace, lowercase
        return ' '.join(text.lower().split())

    def _string_similarity(self, a: str, b: str) -> float:
        """Calculate string similarity ratio."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _normalize_figure_id(self, fig_id: str) -> str:
        """Normalize figure ID for deduplication."""
        # Extract number from "Figure 1", "Fig. 1", "Fig 1a", etc.
        match = re.search(r'(\d+[a-z]?)', fig_id, re.IGNORECASE)
        if match:
            return f"fig_{match.group(1).lower()}"
        return fig_id.lower().replace(' ', '_')

    def _normalize_table_id(self, table_id: str) -> str:
        """Normalize table ID for deduplication."""
        match = re.search(r'(\d+[a-z]?)', table_id, re.IGNORECASE)
        if match:
            return f"table_{match.group(1).lower()}"
        return table_id.lower().replace(' ', '_')

    def _normalize_equation_id(self, eq_id: str) -> str:
        """Normalize equation ID."""
        match = re.search(r'(\d+[a-z]?)', eq_id)
        if match:
            return f"eq_{match.group(1).lower()}"
        return eq_id.lower().replace(' ', '_')

    def _normalize_ref_id(self, ref_id: str) -> str:
        """Normalize reference ID."""
        # Extract number from "[1]", "(1)", "1.", etc.
        match = re.search(r'(\d+)', ref_id)
        if match:
            return match.group(1)
        return ref_id.strip().lower()

    def _deduplicate_authors(self, authors: List[str]) -> List[str]:
        """Deduplicate author list with fuzzy matching."""
        unique = []

        for author in authors:
            author_clean = author.strip()
            if not author_clean:
                continue

            # Check if similar author already exists
            is_duplicate = False
            for existing in unique:
                if self._are_same_author(author_clean, existing):
                    # Keep the longer/more complete name
                    if len(author_clean) > len(existing):
                        unique.remove(existing)
                        unique.append(author_clean)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(author_clean)

        return unique

    def _are_same_author(self, a: str, b: str) -> bool:
        """Check if two author strings refer to the same person."""
        # Exact match
        if a.lower() == b.lower():
            return True

        # Extract last names
        a_parts = a.split()
        b_parts = b.split()

        if not a_parts or not b_parts:
            return False

        a_last = a_parts[-1].lower()
        b_last = b_parts[-1].lower()

        # Same last name
        if a_last == b_last:
            # Check first initial matches
            a_first = a_parts[0][0].lower() if a_parts else ''
            b_first = b_parts[0][0].lower() if b_parts else ''

            if a_first == b_first:
                return True

        return False

    def _merge_references(self, ref1: Reference, ref2: Reference) -> Reference:
        """Merge two references, keeping most complete info."""
        return Reference(
            ref_id=ref1.ref_id,
            authors=ref1.authors if ref1.authors else ref2.authors,
            title=ref1.title or ref2.title,
            journal=ref1.journal or ref2.journal,
            year=ref1.year or ref2.year,
            volume=ref1.volume or ref2.volume,
            pages=ref1.pages or ref2.pages,
            doi=ref1.doi or ref2.doi,
            pmid=ref1.pmid or ref2.pmid,
            raw_text=ref1.raw_text or ref2.raw_text
        )

    def _sort_references(self, references: List[Reference]) -> List[Reference]:
        """Sort references by ID number."""
        def get_ref_number(ref: Reference) -> int:
            match = re.search(r'(\d+)', ref.ref_id)
            return int(match.group(1)) if match else 999999

        return sorted(references, key=get_ref_number)

    def _reference_completeness(self, ref: Reference) -> float:
        """Calculate completeness score for a reference."""
        fields = [
            bool(ref.authors),
            bool(ref.title),
            bool(ref.journal),
            bool(ref.year),
            bool(ref.doi or ref.pmid)
        ]
        return sum(fields) / len(fields)

    def _is_valid_doi(self, doi: str) -> bool:
        """Validate DOI format."""
        # DOI format: 10.xxxx/...
        return bool(re.match(r'^10\.\d{4,}/', doi))

    def _generate_searchable_text(self, metadata: DocumentMetadata) -> str:
        """Generate searchable text summary for embedding."""
        parts = []

        if metadata.title:
            parts.append(f"Title: {metadata.title}")

        if metadata.authors:
            parts.append(f"Authors: {', '.join(metadata.authors)}")

        if metadata.paper_metadata and metadata.paper_metadata.abstract:
            parts.append(f"Abstract: {metadata.paper_metadata.abstract}")

        if metadata.paper_metadata and metadata.paper_metadata.keywords:
            parts.append(f"Keywords: {', '.join(metadata.paper_metadata.keywords)}")

        if metadata.figures:
            fig_desc = "; ".join(f.description for f in metadata.figures if f.description)
            if fig_desc:
                parts.append(f"Figures: {fig_desc[:500]}")

        if metadata.tables:
            table_desc = "; ".join(t.description for t in metadata.tables if t.description)
            if table_desc:
                parts.append(f"Tables: {table_desc[:500]}")

        return "\n".join(parts)
