"""
PDF Parser for RAG

Extracts text from PDF files using pymupdf (fitz).
"""

from typing import Dict, Any, List, Optional
import fitz  # pymupdf
import logging
from pathlib import Path

# Add CitationExtractor integration
from backend.retrieval.parsers.citations import CitationExtractor

logger = logging.getLogger(__name__)


class PDFParser:
    """
    Extracts text and metadata from PDF files.

    Features:
    - Page-by-page extraction
    - Metadata extraction (title, author, etc.)
    - Text cleaning
    - Page number tracking
    - Handles multi-column layouts
    - Citation extraction (Phase 1)

    Uses PyMuPDF (fitz) for:
    - Fast extraction
    - Good text quality
    - Metadata access
    """

    def __init__(
        self,
        extract_images: bool = False,
        min_text_length: int = 10,
        extract_citations: bool = True
    ):
        """
        Initialize PDF parser.

        Args:
            extract_images: Whether to extract images (Phase 2+)
            min_text_length: Minimum text length per page to include
            extract_citations: Whether to extract citations (Phase 1)
        """
        self.extract_images = extract_images
        self.min_text_length = min_text_length
        self.extract_citations = extract_citations
        
        if self.extract_citations:
            self.citation_extractor = CitationExtractor()
        else:
            self.citation_extractor = None
        
        self.transcriber = None # Placeholder for type checking/future use

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with:
            - text: Full extracted text
            - pages: List of page texts
            - metadata: PDF metadata (title, author, etc.)
            - citations: Extracted citations (if enabled)
            - num_pages: Page count
            - file_name: File name
            - file_size: File size in bytes
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not path.suffix.lower() == ".pdf":
            raise ValueError(f"Not a PDF file: {file_path}")

        logger.info(f"Parsing PDF: {path.name}")

        try:
            # Open PDF
            doc = fitz.open(file_path)

            # Extract metadata
            metadata = self._extract_metadata(doc)

            # Extract text from all pages
            pages = []
            full_text_list = []
            num_pages = len(doc)  # Get page count before closing

            for page_num in range(num_pages):
                page = doc[page_num]
                page_text = page.get_text()

                # Clean text
                page_text = self._clean_text(page_text)

                # Only include pages with substantial text
                if len(page_text) >= self.min_text_length:
                    pages.append({
                        "page_number": page_num + 1,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                    full_text_list.append(page_text)

            doc.close()
            
            # Combine full text for comprehensive analysis
            full_text = "\n\n".join(full_text_list)
            
            # --- SCANNED PDF DETECTION ---
            # If text density is low (< 50 chars per page average), flag as scanned
            avg_chars_per_page = len(full_text) / num_pages if num_pages > 0 else 0
            is_scanned = avg_chars_per_page < 50
            if is_scanned:
                logger.info(f"Detected scanned PDF or low text density (avg {avg_chars_per_page:.1f} chars/page).")

            # Extract citations if enabled
            citations = []
            dois = []
            references = []
            if self.extract_citations and self.citation_extractor and not is_scanned:
                # Skip citation extraction on scanned docs (garbage text)
                try:
                    citations = self.citation_extractor.extract_citations(full_text)
                    dois = self.citation_extractor.extract_dois(full_text)
                    references = self.citation_extractor.extract_references(full_text)
                except Exception as e:
                    logger.warning(f"Citation extraction failed: {e}")
                
                # Enhance metadata
                metadata["citation_count"] = len(citations)
                metadata["reference_count"] = len(references)
                metadata["doi_count"] = len(dois)
                if dois:
                    metadata["found_dois"] = dois[:5] # Store first 5 for preview
            
            result = {
                "text": full_text,
                "pages": pages,
                "metadata": metadata,
                "citations": citations, 
                "references": references,
                "num_pages": num_pages,
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "is_scanned": is_scanned
            }

            logger.info(f"✓ Parsed {path.name}: {len(pages)} pages, "
                       f"{len(citations)} citations, {len(references)} references")

            return result

        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise

    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """
        Extract PDF metadata.

        Args:
            doc: PyMuPDF document

        Returns:
            Metadata dictionary
        """
        metadata = doc.metadata or {}

        return {
            "title": metadata.get("title", "").strip() or None,
            "author": metadata.get("author", "").strip() or None,
            "subject": metadata.get("subject", "").strip() or None,
            "keywords": metadata.get("keywords", "").strip() or None,
            "creator": metadata.get("creator", "").strip() or None,
            "producer": metadata.get("producer", "").strip() or None,
            "creation_date": metadata.get("creationDate", "").strip() or None,
            "mod_date": metadata.get("modDate", "").strip() or None,
        }

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]

        # Join with single newline
        cleaned = "\n".join(lines)

        return cleaned

    def parse_pages(
        self,
        file_path: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Parse specific pages from PDF.

        Args:
            file_path: Path to PDF file
            page_numbers: List of page numbers (1-indexed). None = all pages.

        Returns:
            List of page dictionaries
        """
        path = Path(file_path)
        doc = fitz.open(file_path)

        # Determine which pages to parse
        if page_numbers is None:
            page_numbers = list(range(1, len(doc) + 1))

        pages = []
        for page_num in page_numbers:
            # Convert to 0-indexed
            idx = page_num - 1

            if idx < 0 or idx >= len(doc):
                logger.warning(f"Page {page_num} out of range, skipping")
                continue

            page = doc[idx]
            page_text = self._clean_text(page.get_text())

            if len(page_text) >= self.min_text_length:
                pages.append({
                    "page_number": page_num,
                    "text": page_text,
                    "char_count": len(page_text)
                })

        doc.close()

        logger.info(f"Parsed {len(pages)} pages from {path.name}")
        return pages


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Initialize parser
    parser = PDFParser(extract_citations=True)

    # Parse PDF
    result = parser.parse(pdf_path)

    # Display results
    print(f"\n{'=' * 70}")
    print(f"PDF: {result['file_name']}")
    print(f"{'=' * 70}")
    print(f"Pages: {result['num_pages']}")
    print(f"File size: {result['file_size'] / 1024:.1f} KB")
    
    print(f"\nMetadata:")
    for key, value in result['metadata'].items():
        if value:
            print(f"  {key}: {value}")
            
    # Display citation stats
    citations = result.get('citations', [])
    references = result.get('references', [])
    print(f"\nInline Citations Found: {len(citations)}")
    print(f"References Found: {len(references)}")
    
    print(f"\nFirst 3 Citations:")
    for i, cit in enumerate(citations[:3], 1):
        print(f"  {i}. {cit['text']} ({cit['type']})")
        
    print(f"\nFirst 3 References:")
    for i, ref in enumerate(references[:3], 1):
        print(f"  {i}. {ref['raw_text'][:100]}...")

    print(f"\nFirst page preview:")
    if result['pages']:
        first_page = result['pages'][0]
        preview = first_page['text'][:500]
        print(f"  {preview}...")
        print(f"  ({first_page['char_count']} characters)")
