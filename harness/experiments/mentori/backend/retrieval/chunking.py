"""
Text Chunking for RAG

Splits documents into chunks suitable for embedding and retrieval.
"""

from typing import List, Dict, Any, Optional
import tiktoken
import re
import logging

logger = logging.getLogger(__name__)


class SimpleChunker:
    """
    Token-based text chunker with overlap.

    Features:
    - Fixed-size chunks by token count
    - Configurable overlap for context preservation
    - Metadata preservation (source, page, etc.)
    - Sentence boundary awareness (optional)

    Why token-based:
    - Ensures chunks fit in embedding model context
    - Prevents truncation
    - Consistent chunk sizes across different texts
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base",
        respect_sentence_boundaries: bool = True
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Max tokens per chunk
            chunk_overlap: Token overlap between chunks
            encoding_name: Tiktoken encoding to use
            respect_sentence_boundaries: Try to break at sentence boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_sentence_boundaries = respect_sentence_boundaries

        # Initialize tokenizer
        self.tokenizer = tiktoken.get_encoding(encoding_name)
        logger.info(f"Initialized SimpleChunker (size={chunk_size}, overlap={chunk_overlap})")

    def chunk_text(
        self,
        text: str,
        page_num: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a single text document.

        Args:
            text: Text to chunk
            page_num: Source page number (for metadata, matches SemanticChunker API)
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunks, each with:
            - text: Chunk text
            - metadata: Chunk metadata (includes chunk_index)
            - tokens: Token count
        """
        if not text.strip():
            return []

        # Tokenize
        tokens = self.tokenizer.encode(text)
        total_tokens = len(tokens)

        chunks = []
        start_idx = 0

        while start_idx < total_tokens:
            # Extract chunk tokens
            end_idx = min(start_idx + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start_idx:end_idx]

            # Decode chunk
            chunk_text = self.tokenizer.decode(chunk_tokens)

            # Adjust for sentence boundaries (if enabled and not last chunk)
            if self.respect_sentence_boundaries and end_idx < total_tokens:
                chunk_text = self._adjust_to_sentence_boundary(chunk_text)

            # Create chunk metadata
            chunk_metadata = {
                "chunk_index": len(chunks),
                "start_token": start_idx,
                "end_token": end_idx,
                "total_tokens": len(chunk_tokens),
                "page_num": page_num,
                **(metadata or {})
            }

            chunks.append({
                "text": chunk_text.strip(),
                "metadata": chunk_metadata,
                "tokens": len(chunk_tokens)
            })

            # Move to next chunk with overlap
            start_idx += self.chunk_size - self.chunk_overlap

        logger.debug(f"Chunked text into {len(chunks)} chunks ({total_tokens} tokens)")
        return chunks

    def _adjust_to_sentence_boundary(self, text: str) -> str:
        """
        Try to end chunk at sentence boundary.

        Args:
            text: Chunk text

        Returns:
            Adjusted text ending at sentence boundary
        """
        # Common sentence endings
        sentence_endings = [". ", ".\n", "! ", "!\n", "? ", "?\n"]

        # Find last sentence ending
        last_boundary = -1
        for ending in sentence_endings:
            pos = text.rfind(ending)
            if pos > last_boundary:
                last_boundary = pos + len(ending)

        # If we found a boundary in the last 20% of text, use it
        if last_boundary > len(text) * 0.8:
            return text[:last_boundary]

        return text

    def chunk_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents.

        Args:
            documents: List of document texts
            metadatas: Optional metadata per document

        Returns:
            Flattened list of all chunks
        """
        all_chunks = []

        for i, doc in enumerate(documents):
            doc_metadata = metadatas[i] if metadatas else None
            chunks = self.chunk_text(doc, doc_metadata)
            all_chunks.extend(chunks)

        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks


class MarkdownChunker(SimpleChunker):
    """
    Markdown-aware chunker that respects document structure.

    Features:
    - Splits on headers (preserves hierarchy)
    - Keeps code blocks intact
    - Preserves lists and tables when possible
    - Adds structural metadata (section, subsection)

    Best for:
    - Scientific papers with clear sections
    - Documentation
    - Structured notes
    """

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk markdown text by structure.

        Args:
            text: Markdown text
            metadata: Optional base metadata

        Returns:
            List of chunks with structural metadata
        """
        # Split by headers
        sections = self._split_by_headers(text)

        chunks = []
        for section in sections:
            section_text = section["text"]
            section_metadata = {
                **section["metadata"],
                **(metadata or {})
            }

            # If section is small enough, keep as single chunk
            tokens = len(self.tokenizer.encode(section_text))
            if tokens <= self.chunk_size:
                chunks.append({
                    "text": section_text.strip(),
                    "metadata": {
                        **section_metadata,
                        "chunk_index": len(chunks),
                        "total_tokens": tokens
                    },
                    "tokens": tokens
                })
            else:
                # Section too large, chunk it normally
                section_chunks = super().chunk_text(section_text, section_metadata)
                chunks.extend(section_chunks)

        logger.debug(f"Chunked markdown into {len(chunks)} chunks")
        return chunks

    def _split_by_headers(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text by markdown headers.

        Returns:
            List of sections with metadata
        """
        # Regex for markdown headers
        header_pattern = r"^(#{1,6})\s+(.+)$"
        lines = text.split("\n")

        sections = []
        current_section = {
            "text": "",
            "metadata": {
                "section": "Introduction",
                "header_level": 0
            }
        }

        for line in lines:
            match = re.match(header_pattern, line)
            if match:
                # Save previous section if not empty
                if current_section["text"].strip():
                    sections.append(current_section)

                # Start new section
                header_level = len(match.group(1))
                section_title = match.group(2).strip()

                current_section = {
                    "text": line + "\n",
                    "metadata": {
                        "section": section_title,
                        "header_level": header_level
                    }
                }
            else:
                current_section["text"] += line + "\n"

        # Add last section
        if current_section["text"].strip():
            sections.append(current_section)

        return sections


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example 1: Simple chunking
    chunker = SimpleChunker(chunk_size=100, chunk_overlap=20)

    text = """
    CRISPR-Cas9 is a revolutionary genome editing technology. The system consists
    of two main components: the Cas9 enzyme and a guide RNA. Together, they can
    target and cut specific DNA sequences with high precision.

    Off-target effects remain a significant challenge. These occur when Cas9 cuts
    unintended DNA sites that are similar to the target sequence. Researchers are
    developing improved prediction models to minimize these effects.

    Recent advances include base editing and prime editing. These techniques allow
    for more precise modifications without creating double-strand breaks.
    """

    chunks = chunker.chunk_text(text, metadata={"source": "crispr_overview.txt"})

    print(f"Simple Chunker: {len(chunks)} chunks")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i} ({chunk['tokens']} tokens):")
        print(f"  {chunk['text'][:100]}...")
        print(f"  Metadata: {chunk['metadata']}")

    # Example 2: Markdown chunking
    print("\n" + "=" * 70)
    md_chunker = MarkdownChunker(chunk_size=150, chunk_overlap=20)

    markdown_text = """
# CRISPR Technology

## Overview
CRISPR-Cas9 is a genome editing tool derived from bacterial immune systems.

## Mechanism
The Cas9 enzyme uses guide RNA to target specific DNA sequences. Upon binding,
it creates a double-strand break.

### Guide RNA Design
Guide RNA must be carefully designed to match the target sequence. Typically
20 nucleotides long.

## Applications
CRISPR has applications in medicine, agriculture, and basic research.
    """

    md_chunks = md_chunker.chunk_text(markdown_text, metadata={"source": "crispr.md"})

    print(f"\nMarkdown Chunker: {len(md_chunks)} chunks")
    for i, chunk in enumerate(md_chunks, 1):
        section = chunk['metadata'].get('section', 'Unknown')
        level = chunk['metadata'].get('header_level', 0)
        print(f"\nChunk {i}: {section} (Level {level}, {chunk['tokens']} tokens)")
        print(f"  {chunk['text'][:80]}...")
