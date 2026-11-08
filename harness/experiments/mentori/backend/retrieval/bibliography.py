from typing import List, Dict, Optional

class BibliographyGenerator:
    """Generate formatting bibliographies for RAG results."""

    def generate(self, references: List[Dict[str, str]], style: str = "apa") -> str:
        """
        Generate a formatted bibliography string.
        
        Args:
            references: List of dicts, each containing:
                - authors (str or List[str])
                - year (str)
                - title (str)
                - journal (str, optional)
                - volume (str, optional)
                - pages (str, optional)
                - doi (str, optional)
            style: Citation style ('apa', 'ieee', 'mla')
            
        Returns:
            Formatted bibliography string
        """
        formatted_refs = []
        
        for i, ref in enumerate(references):
            formatted = ""
            if style.lower() == "apa":
                formatted = self._format_apa(ref)
            elif style.lower() == "ieee":
                formatted = self._format_ieee(ref, i + 1)
            else:
                formatted = self._format_apa(ref) # Default
            
            formatted_refs.append(formatted)
            
        return "\n".join(formatted_refs)

    def _format_apa(self, ref: Dict[str, str]) -> str:
        """Format a single reference in APA style."""
        # Author calculation
        authors = ref.get("authors", "")
        if isinstance(authors, list):
            if len(authors) > 1:
                authors_str = ", ".join(authors[:-1]) + ", & " + authors[-1]
            else:
                authors_str = authors[0]
        else:
            authors_str = str(authors)
            
        year = f"({ref.get('year', 'n.d.')})."
        title = f"{ref.get('title', 'Unknown Title')}."
        
        source = ""
        if ref.get("journal"):
            source += f" *{ref['journal']}*"
            if ref.get("volume"):
                source += f", *{ref['volume']}*"
            if ref.get("pages"):
                source += f", {ref['pages']}"
            source += "."
            
        doi = ""
        if ref.get("doi"):
            doi = f" https://doi.org/{ref['doi']}"
            
        # Combine parts
        parts = [p for p in [authors_str, year, title, source, doi] if p]
        return " ".join(parts)

    def _format_ieee(self, ref: Dict[str, str], number: int) -> str:
        """Format a single reference in IEEE style."""
        authors = ref.get("authors", "")
        if isinstance(authors, list):
            authors_str = ", ".join(authors)
        else:
            authors_str = str(authors)
            
        title = f"\"{ref.get('title', 'Unknown Title')},\""
        
        source = ""
        if ref.get("journal"):
            source = f" in *{ref['journal']}*"
            if ref.get("year"):
                source += f", {ref['year']}"
            source += "."
            
        return f"[{number}] {authors_str}, {title}{source}"
