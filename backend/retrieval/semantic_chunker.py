"""
Semantic Chunker for RAG

Chunks documents based on semantic boundaries rather than fixed sizes.
Preserves document structure (sections, headings, paragraphs).

This is restored from the old RAG system - it significantly improves
retrieval quality by keeping related content together and preserving
document structure metadata.
"""

import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import spacy, fall back to simple sentence splitting if not available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Using simple sentence splitting.")

# Supported language models
SPACY_MODELS = {
    "en": "en_core_web_sm",
    "nl": "nl_core_news_sm",  # Dutch for WBVR Netherlands
}

# Common Dutch words for language detection
DUTCH_INDICATORS = {
    "de", "het", "een", "van", "en", "in", "is", "dat", "op", "te",
    "voor", "met", "zijn", "niet", "aan", "door", "ook", "als", "maar",
    "bij", "kan", "worden", "naar", "dit", "werd", "deze", "uit", "nog",
    "overheid", "ministerie", "besluit", "artikel", "verordening", "wet"
}

# Try to import PyMuPDF for PDF processing
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available. PDF chunking disabled.")


class SemanticChunker:
    """
    Chunks documents based on semantic boundaries rather than fixed sizes.
    Preserves document structure (sections, paragraphs, figures).

    Key features:
    - Sentence boundary detection (via spaCy or regex fallback)
    - Heading detection based on font size and formatting
    - Overlap between chunks for context continuity
    - Metadata preservation (page numbers, chunk types)

    Why this matters for scientific RAG:
    - Author names in headers are preserved as separate chunks
    - Section boundaries are respected
    - Tables and figures get their own chunks
    - Better retrieval for structural queries ("who wrote this?")
    """

    def __init__(
        self,
        target_chunk_size: int = 1000,
        overlap_sentences: int = 2,
        min_chunk_size: int = 100,
        spacy_model: str = "auto",
        language: str = "auto"
    ):
        """
        Initialize the semantic chunker.

        Args:
            target_chunk_size: Target chunk size in characters
            overlap_sentences: Number of sentences to overlap between chunks
            min_chunk_size: Minimum chunk size (smaller chunks are merged)
            spacy_model: spaCy model to use for sentence detection, or "auto" for language detection
            language: Language code ("en", "nl") or "auto" for detection
        """
        self.target_size = target_chunk_size
        self.overlap_sentences = overlap_sentences
        self.min_chunk_size = min_chunk_size
        self.language = language

        # Load spaCy models
        self.nlp_models = {}
        self.nlp = None  # Current active model

        if SPACY_AVAILABLE:
            if spacy_model != "auto":
                # Load specified model
                try:
                    self.nlp = spacy.load(spacy_model)
                    logger.info(f"Loaded spaCy model: {spacy_model}")
                except OSError:
                    logger.warning(f"spaCy model '{spacy_model}' not found. Using regex fallback.")
            else:
                # Load all available models for auto-detection
                for lang, model_name in SPACY_MODELS.items():
                    try:
                        self.nlp_models[lang] = spacy.load(model_name)
                        logger.info(f"Loaded spaCy model for {lang}: {model_name}")
                    except OSError:
                        logger.debug(f"spaCy model '{model_name}' not available")

                # Default to English if available
                self.nlp = self.nlp_models.get("en")

    def chunk_text(self, text: str, page_num: int = 1, metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Chunk plain text at sentence boundaries.

        Args:
            text: The text to chunk
            page_num: Page number for metadata
            metadata: Additional metadata to include in each chunk

        Returns:
            List of chunks with metadata:
            [
                {
                    "text": "chunk content...",
                    "page_num": 1,
                    "type": "content",
                    "sentence_count": 5,
                    "char_count": 450,
                    ...additional metadata
                },
                ...
            ]
        """
        if not text or not text.strip():
            return []

        # Use sentence-aware chunking
        chunks = self._chunk_at_sentences(text, page_num)

        # Add any additional metadata
        if metadata:
            for chunk in chunks:
                chunk.update(metadata)

        return chunks

    async def chunk_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Chunk PDF preserving semantic structure.

        Detects:
        - Headings (based on font size and formatting)
        - Regular paragraphs
        - Page boundaries

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of chunks with enhanced metadata
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) is required for PDF chunking")

        chunks = []

        with fitz.open(pdf_path) as pdf_doc:
            for page_num, page in enumerate(pdf_doc, start=1):
                # Extract text blocks (preserves layout)
                blocks = page.get_text("dict")["blocks"]

                for block in blocks:
                    if block["type"] == 0:  # Text block
                        text = self._extract_block_text(block)

                        if not text.strip():
                            continue

                        # Detect if heading
                        if self._is_heading(block):
                            chunks.append({
                                'text': text,
                                'page_num': page_num,
                                'type': 'heading',
                                'level': self._get_heading_level(block)
                            })
                        else:
                            # Chunk paragraph at sentence boundaries
                            paragraph_chunks = self._chunk_at_sentences(
                                text,
                                page_num
                            )
                            chunks.extend(paragraph_chunks)

        # Post-process: merge small chunks
        chunks = self._merge_small_chunks(chunks)

        logger.info(f"Chunked PDF into {len(chunks)} chunks")
        return chunks

    def chunk_with_headings(self, text: str, page_num: int = 1) -> List[Dict]:
        """
        Chunk text while detecting and preserving headings.

        Uses heuristics to detect headings:
        - Lines that are short and followed by blank line
        - Lines that start with numbers (1., 1.1, etc.)
        - Lines in ALL CAPS
        - Lines that match common heading patterns

        Args:
            text: Text to chunk
            page_num: Page number

        Returns:
            List of chunks with heading detection
        """
        chunks = []
        lines = text.split('\n')
        current_section = []
        current_heading = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            if self._is_text_heading(stripped, lines, i):
                # Save current section if we have content
                if current_section:
                    section_text = '\n'.join(current_section)
                    section_chunks = self._chunk_at_sentences(section_text, page_num)

                    # Add heading info to first chunk
                    if section_chunks and current_heading:
                        section_chunks[0]['section_heading'] = current_heading

                    chunks.extend(section_chunks)
                    current_section = []

                # Store heading as its own chunk
                if stripped:
                    chunks.append({
                        'text': stripped,
                        'page_num': page_num,
                        'type': 'heading',
                        'level': self._detect_heading_level(stripped)
                    })
                    current_heading = stripped
            else:
                if stripped:
                    current_section.append(stripped)

        # Don't forget the last section
        if current_section:
            section_text = '\n'.join(current_section)
            section_chunks = self._chunk_at_sentences(section_text, page_num)
            if section_chunks and current_heading:
                section_chunks[0]['section_heading'] = current_heading
            chunks.extend(section_chunks)

        return chunks

    def _detect_language(self, text: str) -> str:
        """
        Detect language of text using simple word frequency heuristics.

        Args:
            text: Text to analyze

        Returns:
            Language code ("en", "nl", etc.)
        """
        if self.language != "auto":
            return self.language

        # Tokenize and check for Dutch indicators
        words = set(text.lower().split())
        dutch_count = len(words & DUTCH_INDICATORS)

        # If more than 5 Dutch indicator words, likely Dutch
        if dutch_count >= 5:
            logger.debug(f"Detected Dutch language ({dutch_count} indicator words)")
            return "nl"

        return "en"

    def _get_nlp_for_text(self, text: str):
        """
        Get the appropriate spaCy model for the given text.

        Args:
            text: Text to process

        Returns:
            spaCy nlp model or None
        """
        if not self.nlp_models:
            return self.nlp

        lang = self._detect_language(text)
        if lang in self.nlp_models:
            return self.nlp_models[lang]

        # Fallback to default
        return self.nlp

    def _chunk_at_sentences(self, text: str, page_num: int) -> List[Dict]:
        """
        Chunk text at sentence boundaries.

        Args:
            text: Text to chunk
            page_num: Page number for metadata

        Returns:
            List of content chunks
        """
        # Get appropriate NLP model for this text
        nlp = self._get_nlp_for_text(text)

        # Get sentences
        if nlp:
            doc = nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # Fallback: regex-based sentence splitting
            sentences = self._split_sentences_regex(text)

        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for sent in sentences:
            sent_len = len(sent)

            if current_size + sent_len > self.target_size and current_chunk:
                # Create chunk at sentence boundary
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'page_num': page_num,
                    'type': 'content',
                    'sentence_count': len(current_chunk),
                    'char_count': len(chunk_text)
                })

                # Overlap: keep last N sentences
                overlap_text = current_chunk[-self.overlap_sentences:] if self.overlap_sentences > 0 else []
                current_chunk = overlap_text + [sent]
                current_size = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sent)
                current_size += sent_len

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'page_num': page_num,
                'type': 'content',
                'sentence_count': len(current_chunk),
                'char_count': len(chunk_text)
            })

        return chunks

    def _split_sentences_regex(self, text: str) -> List[str]:
        """
        Split text into sentences using regex (fallback when spaCy unavailable).

        Handles:
        - Standard sentence endings (.!?)
        - Abbreviations (Dr., Mr., etc.)
        - Numbers with decimals
        """
        # Simple sentence splitter - not perfect but works for most cases
        # Avoid splitting on common abbreviations
        text = re.sub(r'([A-Z][a-z]?)\. ', r'\1ABBR ', text)  # Dr. Mr. etc.
        text = re.sub(r'(\d)\. ', r'\1DECIMAL ', text)  # Numbers

        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Restore abbreviations
        sentences = [s.replace('ABBR ', '. ').replace('DECIMAL ', '. ') for s in sentences]

        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _is_heading(self, block: dict) -> bool:
        """
        Detect if a PDF block is a section heading.

        Uses heuristics:
        - Larger font size
        - Bold formatting
        - Short text length
        """
        if not block.get("lines"):
            return False

        try:
            line = block["lines"][0]
            if not line.get("spans"):
                return False

            span = line["spans"][0]
            font_size = span.get("size", 0)
            font_name = span.get("font", "").lower()
            is_bold = "bold" in font_name
            text = self._extract_block_text(block)
            text_length = len(text)

            # Heuristics: larger font, bold, short text
            if font_size > 14 and is_bold and text_length < 100:
                return True
            if font_size > 16 and text_length < 150:
                return True

            return False
        except (KeyError, IndexError):
            return False

    def _is_text_heading(self, line: str, all_lines: List[str], index: int) -> bool:
        """
        Detect if a text line is a heading using heuristics.
        """
        if not line:
            return False

        # Check for numbered headings (1., 1.1., etc.)
        if re.match(r'^\d+\.(\d+\.)*\s+[A-Z]', line):
            return True

        # Check for ALL CAPS short lines
        if line.isupper() and len(line) < 80 and len(line.split()) <= 8:
            return True

        # Check for common heading patterns
        heading_patterns = [
            r'^(Abstract|Introduction|Methods?|Results?|Discussion|Conclusion|References|Acknowledgments?)\s*$',
            r'^(Background|Materials?\s+and\s+Methods?|Data\s+Availability|Author\s+Contributions?)\s*$',
            r'^(Supplementary|Appendix|Figure\s+\d+|Table\s+\d+)\s*',
        ]

        for pattern in heading_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        # Short line followed by empty line or much longer line
        if len(line) < 60 and index < len(all_lines) - 1:
            next_line = all_lines[index + 1].strip()
            if not next_line or (len(next_line) > len(line) * 2):
                # Likely a heading
                return True

        return False

    def _get_heading_level(self, block: dict) -> int:
        """Determine heading level based on font size."""
        try:
            font_size = block["lines"][0]["spans"][0].get("size", 0)

            if font_size >= 20:
                return 1
            elif font_size >= 16:
                return 2
            elif font_size >= 14:
                return 3
            else:
                return 4
        except (KeyError, IndexError):
            return 3

    def _detect_heading_level(self, text: str) -> int:
        """Detect heading level from text patterns."""
        # Numbered heading level
        match = re.match(r'^(\d+)(\.(\d+))*(\.(\d+))*', text)
        if match:
            dots = text.count('.') + 1
            return min(dots, 4)

        # ALL CAPS = level 1
        if text.isupper():
            return 1

        return 2

    def _extract_block_text(self, block: dict) -> str:
        """Extract text from PDF block."""
        lines = block.get("lines", [])
        text_parts = []

        for line in lines:
            for span in line.get("spans", []):
                text_parts.append(span.get("text", ""))

        return " ".join(text_parts).strip()

    def _merge_small_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Merge chunks that are too small.

        Args:
            chunks: List of chunks

        Returns:
            Merged chunks
        """
        if not chunks:
            return chunks

        merged = []
        pending = None

        for chunk in chunks:
            # Don't merge headings
            if chunk.get('type') == 'heading':
                if pending:
                    merged.append(pending)
                    pending = None
                merged.append(chunk)
                continue

            chunk_size = len(chunk.get('text', ''))

            if chunk_size < self.min_chunk_size:
                if pending:
                    # Merge with pending
                    pending['text'] += ' ' + chunk['text']
                    pending['sentence_count'] = pending.get('sentence_count', 1) + chunk.get('sentence_count', 1)
                    pending['char_count'] = len(pending['text'])
                else:
                    pending = chunk
            else:
                if pending:
                    # Add pending to this chunk
                    chunk['text'] = pending['text'] + ' ' + chunk['text']
                    chunk['sentence_count'] = pending.get('sentence_count', 1) + chunk.get('sentence_count', 1)
                    chunk['char_count'] = len(chunk['text'])
                    pending = None
                merged.append(chunk)

        if pending:
            if merged and merged[-1].get('type') != 'heading':
                merged[-1]['text'] += ' ' + pending['text']
                merged[-1]['char_count'] = len(merged[-1]['text'])
            else:
                merged.append(pending)

        return merged


def chunk_document(
    text: str,
    target_size: int = 1000,
    overlap: int = 2,
    preserve_headings: bool = True
) -> List[Dict]:
    """
    Convenience function to chunk a document.

    Args:
        text: Document text
        target_size: Target chunk size in characters
        overlap: Number of sentences to overlap
        preserve_headings: Whether to detect and preserve headings

    Returns:
        List of chunks with metadata
    """
    chunker = SemanticChunker(
        target_chunk_size=target_size,
        overlap_sentences=overlap
    )

    if preserve_headings:
        return chunker.chunk_with_headings(text)
    else:
        return chunker.chunk_text(text)
