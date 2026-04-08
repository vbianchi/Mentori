import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Citation:
    text: str
    type: str  # 'author-year' or 'numbered'
    start: int
    end: int
    authors: Optional[List[str]] = None
    year: Optional[str] = None
    number: Optional[str] = None

@dataclass
class Reference:
    raw_text: str
    authors: List[str]
    title: Optional[str] = None
    year: Optional[str] = None
    doi: Optional[str] = None
    journal: Optional[str] = None

class CitationExtractor:
    """Extract citations and references from scientific text."""

    # Regex patterns
    # (Smith et al., 2020) or (Smith, 2020) or (Smith & Jones, 2020)
    AUTHOR_YEAR_PATTERN = r'\((?P<authors>[A-Z][a-z]+(?:(?:\s+et\s+al\.)|(?:\s+and\s+[A-Z][a-z]+)|(?:,\s+[A-Z][a-z]+))?),\s+(?P<year>\d{4}[a-z]?)\)'
    
    # [1] or [1, 2] or [1-3]
    NUMBERED_PATTERN = r'\[(?P<numbers>\d+(?:(?:,\s*\d+)|(?:-\d+))*)\]'
    
    # DOI: 10.xxxx/xxxxx
    DOI_PATTERN = r'\b(10\.\d{4,}/[-._;()/:A-Za-z0-9]+)\b'

    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all citations from text.
        
        Returns list of dicts with citation details.
        """
        citations = []
        
        # unique_id to avoid duplicates if needed, but here we return all occurrences
        # for context mapping
        
        # 1. Author-Year
        for match in re.finditer(self.AUTHOR_YEAR_PATTERN, text):
            citation = {
                "text": match.group(0),
                "type": "author-year",
                "start": match.start(),
                "end": match.end(),
                "authors": self._parse_authors(match.group("authors")),
                "year": match.group("year")
            }
            citations.append(citation)
            
        # 2. Numbered
        for match in re.finditer(self.NUMBERED_PATTERN, text):
            citation = {
                "text": match.group(0),
                "type": "numbered",
                "start": match.start(),
                "end": match.end(),
                "numbers": self._parse_numbers(match.group("numbers"))
            }
            citations.append(citation)
            
        return sorted(citations, key=lambda x: x["start"])

    def extract_references(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract full references from the 'References' or 'Bibliography' section.
        
        Returns list of reference dicts.
        """
        # 1. Find the References section
        ref_section = self._find_references_section(text)
        if not ref_section:
            return []
            
        # 2. Split into individual references
        raw_refs = self._split_references(ref_section)
        
        # 3. Parse each reference
        parsed_refs = []
        for i, raw_ref in enumerate(raw_refs):
            parsed = self._parse_reference_text(raw_ref)
            if parsed:
                # Add index if numbered list detected
                parsed["index"] = i + 1
                parsed_refs.append(parsed)
                
        return parsed_refs

    def _find_references_section(self, text: str) -> Optional[str]:
        """Locate the references section at the end of the text."""
        # Common headers
        headers = [
            r'^References\s*$',
            r'^Bibliography\s*$',
            r'^Literature Cited\s*$',
            r'^REFERENCES\s*$',
            r'^BIBLIOGRAPHY\s*$'
        ]
        
        # Search from the end backwards to avoid finding "References" in Table of Contents
        lines = text.split('\n')
        total_lines = len(lines)
        
        # Look in the last 50% of the document
        start_search = total_lines // 2
        
        for i in range(total_lines - 1, start_search, -1):
            line = lines[i].strip()
            for header in headers:
                if re.match(header, line):
                    # Found it! Return everything after this line
                    return '\n'.join(lines[i+1:])
        
        return None

    def _split_references(self, text: str) -> List[str]:
        """Split reference section into individual items."""
        # Heuristic 1: Numbered list [1] ... [2] ...
        if re.search(r'^\s*\[1\]', text, re.MULTILINE):
            return re.split(r'\n+\s*\[\d+\]\s+', text)[1:] # Skip empty first split
            
        # Heuristic 2: Numbered list 1. ... 2. ...
        if re.search(r'^\s*1\.', text, re.MULTILINE):
            return re.split(r'\n+\s*\d+\.\s+', text)[1:]
            
        # Heuristic 3: Unnumbered (hanging indent or blank line separated)
        # For now, assume blank line separation as it's common in txt extraction
        refs = re.split(r'\n\s*\n', text)
        return [r.strip() for r in refs if len(r.strip()) > 20] # Filter distinct items

    def extract_dois(self, text: str) -> List[str]:
        """Extract all DOIs from text."""
        return list(set(re.findall(self.DOI_PATTERN, text)))

    def _parse_reference_text(self, text: str) -> Dict[str, Any]:
        """Parse a single raw reference string."""
        text = text.strip()
        if not text:
            return {}
            
        # Try to extract DOI
        dois = self.extract_dois(text)
        doi = dois[0] if dois else None
        
        # Try to extract year (last 4-digit number enclosed in parens or followed by dot)
        year_match = re.search(r'\((\d{4})\)', text) or re.search(r'\b(\d{4})\.', text)
        year = year_match.group(1) if year_match else None
        
        # Very basic author extraction (everything before the year)
        # This is brittle but a good starting point without ML
        authors_raw = text[:year_match.start()] if year_match else text[:50]
        authors = [a.strip() for a in authors_raw.split(',') if len(a.strip()) > 2]
        
        return {
            "raw_text": text.replace('\n', ' '),
            "authors": authors[:5], # Limit to first 5 detected segments
            "year": year,
            "doi": doi
        }

    def _parse_authors(self, author_str: str) -> List[str]:
        """Parse author string into list of names."""
        if " et al." in author_str:
            return [author_str.replace(" et al.", "").strip()]
        if " and " in author_str:
            return [a.strip() for a in author_str.split(" and ")]
        return [author_str.strip()]

    def _parse_numbers(self, number_str: str) -> List[str]:
        """Parse number string (e.g. '1, 2-4') into list of strings."""
        # Simple implementation - just returning the string representation of ranges for now
        # Ideally expand ranges if needed
        return [n.strip() for n in re.split(r'[,\s]+', number_str) if n.strip()]
