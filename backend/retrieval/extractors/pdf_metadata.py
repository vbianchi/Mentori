"""
VLM-based PDF metadata extractor.

Uses vision model to extract structured metadata from PDF first page.
Falls back to regex patterns if VLM unavailable.
"""

import re
import logging
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path

from backend.retrieval.schema.document import (
    DocumentMetadata, DocumentType, PaperMetadata
)
from backend.retrieval.agents.transcriber import AgentFactory
from backend.retrieval.parsers.pdf import PDFParser

logger = logging.getLogger(__name__)


class PDFMetadataExtractor:
    """
    Extract structured metadata from PDFs.

    Strategy:
    1. Try VLM extraction on first page (most accurate)
    2. Fall back to regex patterns on raw text
    3. Use PyMuPDF metadata as last resort
    """

    VLM_EXTRACTION_PROMPT = '''Analyze this document's first page and extract metadata in this exact format:

DOCUMENT_TYPE: [paper|report|grant|meeting|presentation|other]
TITLE: [Full title of the document]
AUTHORS: [Comma-separated list of author names, e.g., "John Smith, Jane Doe, Bob Wilson"]
DATE: [Publication/creation date if visible, e.g., "2024" or "March 2024"]
JOURNAL: [Journal name if this is a paper]
DOI: [DOI if visible]
ABSTRACT_PRESENT: [yes|no]
HAS_TABLES: [yes|no]
HAS_FIGURES: [yes|no]

Only include fields you can confidently extract. Leave blank if not visible.'''

    def __init__(self, agent_roles: Optional[Dict[str, str]] = None):
        """
        Initialize extractor.

        Args:
            agent_roles: Agent configuration for VLM. If None, uses regex only.
        """
        self.agent_roles = agent_roles
        self.transcriber = None
        self.pdf_parser = PDFParser(extract_citations=True)

    async def extract(
        self,
        pdf_path: str,
        use_vlm: bool = True,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> DocumentMetadata:
        """
        Extract metadata from a PDF.

        Args:
            pdf_path: Path to PDF file
            use_vlm: Whether to use VLM (slower but more accurate)
            collection_name: Collection this document belongs to
            user_id: User who owns this document

        Returns:
            DocumentMetadata object
        """
        path = Path(pdf_path)

        # Parse PDF for basic info and text
        parsed = self.pdf_parser.parse(pdf_path)

        # Compute file hash for deduplication
        file_hash = self._compute_file_hash(pdf_path)

        # Start with base metadata
        metadata = DocumentMetadata(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_hash=file_hash,
            page_count=parsed['num_pages'],
            collection_name=collection_name,
            user_id=user_id,
            doc_type=DocumentType.PAPER,  # Default, may be updated
        )

        # Try VLM extraction first
        vlm_succeeded = False
        if use_vlm and self.agent_roles:
            vlm_metadata = await self._extract_with_vlm(pdf_path)
            if vlm_metadata:
                metadata = self._merge_metadata(metadata, vlm_metadata)
                vlm_succeeded = True
                logger.info(f"VLM extracted: '{metadata.title}' by {metadata.authors}")

        # Fallback to regex if VLM didn't work or didn't get key fields
        if not vlm_succeeded or not metadata.title or not metadata.authors:
            regex_metadata = self._extract_with_regex(
                parsed['text'],
                parsed.get('metadata', {})
            )
            metadata = self._merge_metadata(metadata, regex_metadata, overwrite=False)
            logger.info(f"Regex extracted: '{metadata.title}' by {metadata.authors}")

        # Generate searchable text summary
        metadata.searchable_text = self._build_searchable_text(metadata, parsed)

        # Check for tables/figures in text
        full_text = parsed['text'].lower()
        metadata.has_tables = 'table' in full_text or any(
            f'table {i}' in full_text for i in range(1, 20)
        )
        metadata.has_figures = any(
            word in full_text for word in ['figure', 'fig.', 'fig ', 'graph', 'chart']
        )
        metadata.has_abstract = 'abstract' in full_text[:2000]

        # Extract sections from text
        metadata.sections = self._extract_sections(parsed['text'])

        return metadata

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute MD5 hash of file for deduplication."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def _extract_with_vlm(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Use VLM to extract metadata from first page."""
        try:
            from pdf2image import convert_from_path
            import tempfile
            import os

            # Initialize transcriber if needed
            if not self.transcriber:
                self.transcriber = await AgentFactory.get_transcriber(self.agent_roles)
                if not self.transcriber:
                    logger.warning("VLM transcriber not available, using regex only")
                    return None

            # Convert first page to image
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=1)
                if not images:
                    return None

                page_path = os.path.join(temp_dir, "page_1.png")
                images[0].save(page_path, "PNG")

                # Get VLM response - use the existing transcribe_page method
                # Note: transcribe_page uses a fixed prompt, so we'll work with what it returns
                response = await self.transcriber.transcribe_page(page_path)

                # Parse the response
                return self._parse_vlm_response(response)

        except ImportError:
            logger.warning("pdf2image not installed, skipping VLM extraction")
            return None
        except Exception as e:
            logger.warning(f"VLM extraction failed: {e}")
            return None

    def _parse_vlm_response(self, response: str) -> Dict[str, Any]:
        """Parse VLM response into metadata dict."""
        result = {}

        # The transcriber returns markdown text, so we need to extract metadata differently
        # Look for common patterns in the transcribed text

        lines = response.split('\n')

        # Try to find title (usually near the top, often in a heading or larger font)
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            # Skip empty lines and common headers
            if not line or line.lower() in ['abstract', 'introduction', 'keywords']:
                continue
            # Skip lines that look like author affiliations
            if '@' in line or 'university' in line.lower() or 'department' in line.lower():
                continue
            # Skip very short lines
            if len(line) < 15:
                continue
            # This might be the title
            if len(line) > 20 and len(line) < 300:
                # Remove markdown formatting
                clean_title = re.sub(r'^#+\s*', '', line)  # Remove # headers
                clean_title = re.sub(r'\*+', '', clean_title)  # Remove bold/italic
                result['title'] = clean_title.strip()
                break

        # Try to find authors (often after title, before abstract)
        # Look for patterns like "John Smith1, Jane Doe2" or "John Smith and Jane Doe"
        author_section = '\n'.join(lines[:20])

        # Pattern for multiple authors with superscripts
        # Requires at least 2 chars per name part to filter abbreviations
        # Uses [ \t]+ instead of \s+ to avoid matching across newlines
        author_pattern = r'([A-Z][a-z]{2,}(?:[ \t]+[A-Z]\.?[ \t]*)?(?:[ \t]+[A-Z][a-z]{2,})+)(?:\d|,|[ \t]+and[ \t]+)'
        potential_authors = re.findall(author_pattern, author_section)

        if potential_authors:
            # Comprehensive filter for non-author text
            exclude_terms = [
                'university', 'institute', 'department', 'school', 'college',
                'society', 'association', 'foundation', 'organization', 'academy',
                'open', 'access', 'journal', 'press', 'publishing', 'article',
                'national', 'international', 'european', 'american', 'italian',
                'medicine', 'medical', 'clinical', 'research', 'science',
                'center', 'centre', 'laboratory', 'hospital', 'health',
            ]
            authors = []
            for author in potential_authors:
                author = author.strip()
                author_lower = author.lower()
                # Check for exclude terms
                if any(word in author_lower for word in exclude_terms):
                    continue
                # Reject all-caps words (likely acronyms)
                parts = author.split()
                if any(part.isupper() and len(part) > 1 for part in parts):
                    continue
                authors.append(author)
            if authors:
                result['authors'] = authors[:15]  # Max 15 authors

        # Look for explicit metadata markers (if VLM followed our format)
        patterns = {
            'doc_type': r'DOCUMENT_TYPE:\s*(.+?)(?:\n|$)',
            'title': r'TITLE:\s*(.+?)(?:\n|$)',
            'authors': r'AUTHORS:\s*(.+?)(?:\n|$)',
            'date': r'DATE:\s*(.+?)(?:\n|$)',
            'journal': r'JOURNAL:\s*(.+?)(?:\n|$)',
            'doi': r'DOI:\s*(.+?)(?:\n|$)',
            'has_abstract': r'ABSTRACT_PRESENT:\s*(yes|no)',
            'has_tables': r'HAS_TABLES:\s*(yes|no)',
            'has_figures': r'HAS_FIGURES:\s*(yes|no)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and value.lower() not in ['n/a', 'none', 'not visible', '']:
                    result[key] = value

        # Parse authors from structured format if found
        if 'authors' in result and isinstance(result['authors'], str):
            result['authors'] = [a.strip() for a in result['authors'].split(',') if a.strip()]

        # Parse boolean fields
        for key in ['has_abstract', 'has_tables', 'has_figures']:
            if key in result and isinstance(result[key], str):
                result[key] = result[key].lower() == 'yes'

        # Map doc_type to enum
        if 'doc_type' in result:
            type_map = {
                'paper': DocumentType.PAPER,
                'report': DocumentType.REPORT,
                'grant': DocumentType.GRANT,
                'meeting': DocumentType.MEETING,
                'presentation': DocumentType.PRESENTATION,
            }
            result['doc_type'] = type_map.get(str(result['doc_type']).lower(), DocumentType.PAPER)

        return result

    def _extract_with_regex(self, text: str, pdf_metadata: Dict) -> Dict[str, Any]:
        """Fallback regex extraction from text."""
        result = {}

        # Use PDF metadata if available
        if pdf_metadata.get('title'):
            result['title'] = pdf_metadata['title']
        if pdf_metadata.get('author'):
            # PDF metadata often has ";" or "," separated authors
            authors = re.split(r'[;,]', pdf_metadata['author'])
            result['authors'] = [a.strip() for a in authors if a.strip()]

        # Try to extract from text if PDF metadata didn't have it
        if not result.get('title'):
            result['title'] = self._extract_title_from_text(text)

        if not result.get('authors'):
            result['authors'] = self._extract_authors_from_text(text)

        # Try to extract date
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            r'\d{4}',  # Just year
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text[:1000])
            if match:
                result['date'] = match.group(0)
                break

        # Try to extract DOI
        doi_match = re.search(r'10\.\d{4,}/[^\s]+', text)
        if doi_match:
            result['doi'] = doi_match.group(0).rstrip('.,;')

        return result

    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """Extract title from document text."""
        lines = text.split('\n')[:30]  # Look in first 30 lines

        for line in lines:
            line = line.strip()
            # Skip empty lines and common headers
            if not line:
                continue
            if line.lower() in ['abstract', 'introduction', 'keywords', 'contents']:
                continue
            # Skip lines that look like affiliations
            if any(word in line.lower() for word in ['university', 'department', 'institute', '@', 'email']):
                continue
            # Skip very short or very long lines
            if len(line) < 15 or len(line) > 300:
                continue
            # Skip lines that start with numbers (likely page numbers or references)
            if re.match(r'^\d+[\.\)]?\s', line):
                continue
            # This is probably the title
            return line

        return None

    def _extract_authors_from_text(self, text: str) -> List[str]:
        """Extract author names from document text."""
        # Focus on first 2000 characters
        header_text = text[:2000]

        # Pattern for names (First Last or F. Last)
        # Requires at least 2 chars per word to filter abbreviations like "AR"
        # Uses [ \t]+ instead of \s+ to avoid matching across newlines
        name_pattern = r'\b([A-Z][a-z]{2,}(?:[ \t]+[A-Z]\.?[ \t]*)?(?:[ \t]+[A-Z][a-z]{2,})+)\b'

        # Find all potential names
        potential_names = re.findall(name_pattern, header_text)

        # Comprehensive filter for non-author text
        exclude_words = [
            # Academic institutions
            'university', 'institute', 'department', 'school', 'college',
            'faculty', 'center', 'centre', 'laboratory', 'hospital', 'clinic',
            # Paper sections
            'abstract', 'introduction', 'keywords', 'background', 'methods',
            'results', 'discussion', 'conclusion', 'references', 'acknowledgments',
            'figure', 'table', 'supplementary', 'appendix', 'materials',
            # Publication/access terms
            'open', 'access', 'article', 'journal', 'press', 'publishing',
            'publication', 'published', 'received', 'accepted', 'revised',
            'copyright', 'license', 'creative', 'commons', 'rights', 'reserved',
            # Organizations
            'society', 'association', 'foundation', 'organization', 'committee',
            'academy', 'council', 'board', 'group', 'network', 'consortium',
            # Geographic/national terms often in org names
            'national', 'international', 'european', 'american', 'italian',
            'british', 'german', 'french', 'chinese', 'japanese', 'australian',
            # Publishers
            'biomed', 'plos', 'nature', 'springer', 'elsevier', 'wiley',
            'taylor', 'francis', 'oxford', 'cambridge', 'academic',
            # Science/medical terms
            'medicine', 'medical', 'clinical', 'health', 'science', 'sciences',
            'technology', 'research', 'studies', 'review', 'central',
            # Technical/ML terms (common in paper titles)
            'machine', 'learning', 'deep', 'neural', 'network', 'model',
            'system', 'systems', 'data', 'analysis', 'algorithm', 'algorithms',
            'method', 'approach', 'framework', 'based', 'using', 'novel',
            'computational', 'statistical', 'automatic', 'automated',
            # Other false positive triggers
            'correspondence', 'author', 'email', 'address', 'contact',
            'supplemental', 'online', 'version', 'original', 'article',
        ]

        authors = []
        for name in potential_names:
            name_lower = name.lower()

            # Check for exclude words
            if any(word in name_lower for word in exclude_words):
                continue

            parts = name.split()

            # Must have 2-4 parts (typical name structure)
            if not (2 <= len(parts) <= 4):
                continue

            # Each part must be at least 2 chars (filters "J." style initials in middle)
            # Allow single capital + period as middle initial
            valid_parts = True
            for i, part in enumerate(parts):
                # Skip validation for middle initials (single letter with optional period)
                if i > 0 and i < len(parts) - 1 and re.match(r'^[A-Z]\.?$', part):
                    continue
                # First and last name parts must be at least 2 chars
                if len(part.rstrip('.')) < 2:
                    valid_parts = False
                    break

            if not valid_parts:
                continue

            # Reject if all caps words detected (likely acronyms)
            if any(part.isupper() and len(part) > 1 for part in parts):
                continue

            authors.append(name)

        # Remove duplicates while preserving order
        seen = set()
        unique_authors = []
        for author in authors:
            if author not in seen:
                seen.add(author)
                unique_authors.append(author)

        return unique_authors[:15]  # Max 15 authors

    def _extract_sections(self, text: str) -> List[str]:
        """Extract section headings from text."""
        sections = []

        # Common section heading patterns
        patterns = [
            r'^(\d+\.?\s+[A-Z][^\n]{5,50})$',  # "1. Introduction" or "1 Introduction"
            r'^([A-Z][A-Z\s]{5,30})$',  # "INTRODUCTION" (all caps)
            r'^(Abstract|Introduction|Background|Methods|Materials and Methods|Results|Discussion|Conclusion|References|Acknowledgments)$',
        ]

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    sections.append(line)
                    break

        return sections[:20]  # Max 20 sections

    def _merge_metadata(
        self,
        base: DocumentMetadata,
        updates: Dict[str, Any],
        overwrite: bool = True
    ) -> DocumentMetadata:
        """Merge updates into base metadata."""
        for key, value in updates.items():
            if not value:
                continue

            # Don't overwrite if not allowed and base already has value
            if not overwrite and getattr(base, key, None):
                continue

            if hasattr(base, key):
                setattr(base, key, value)
            elif key == 'journal':
                if base.paper_metadata is None:
                    base.paper_metadata = PaperMetadata()
                base.paper_metadata.journal = value
            elif key == 'doi':
                if base.paper_metadata is None:
                    base.paper_metadata = PaperMetadata()
                base.paper_metadata.doi = value

        return base

    def _build_searchable_text(
        self,
        metadata: DocumentMetadata,
        parsed: Dict
    ) -> str:
        """Build a text summary for embedding and full-text search."""
        parts = []

        if metadata.title:
            parts.append(f"Title: {metadata.title}")

        if metadata.authors:
            # Include all author variants for better search
            all_authors = metadata.get_author_search_variants()
            parts.append(f"Authors: {', '.join(metadata.authors)}")
            parts.append(f"Author variants: {', '.join(all_authors)}")

        if metadata.paper_metadata:
            if metadata.paper_metadata.journal:
                parts.append(f"Journal: {metadata.paper_metadata.journal}")
            if metadata.paper_metadata.abstract:
                parts.append(f"Abstract: {metadata.paper_metadata.abstract}")
            if metadata.paper_metadata.keywords:
                parts.append(f"Keywords: {', '.join(metadata.paper_metadata.keywords)}")

        # Include first 1000 chars of content for context
        if parsed.get('text'):
            parts.append(f"Content preview: {parsed['text'][:1000]}")

        return '\n'.join(parts)
