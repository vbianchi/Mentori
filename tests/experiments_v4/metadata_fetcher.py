#!/usr/bin/env python3
"""
Paper Metadata Fetcher for V4 Experiments.

Fetches structured metadata from external APIs:
- arXiv: arxiv ID, title, authors, abstract, categories
- PubMed (Entrez): PMID, title, authors, abstract, journal, MeSH terms
- Crossref: DOI lookup, references, citations
- Semantic Scholar: citation counts, TLDR, influential citations

Usage:
    # Fetch metadata for a single paper
    uv run python tests/experiments_v4/metadata_fetcher.py fetch paper.pdf

    # Fetch metadata for all papers in a directory
    uv run python tests/experiments_v4/metadata_fetcher.py fetch-all datasets/core_papers/

    # Export metadata summary
    uv run python tests/experiments_v4/metadata_fetcher.py export
"""

import argparse
import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metadata_fetcher")

# Output directory
METADATA_DIR = PROJECT_ROOT / "datasets" / "paper_metadata"


@dataclass
class PaperMetadata:
    """Structured metadata for a scientific paper."""
    paper_id: str
    filename: str
    doi: Optional[str] = None
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    journal: Optional[str] = None
    date: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    arxiv_id: Optional[str] = None
    pmid: Optional[str] = None
    s2_id: Optional[str] = None
    citation_count: Optional[int] = None
    source_apis: List[str] = field(default_factory=list)
    extraction_confidence: float = 0.0


class MetadataFetcher:
    """Fetches paper metadata from external APIs."""

    def __init__(self, email: str = "research@example.com"):
        """Initialize fetcher with email for API compliance."""
        self.email = email
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_paper_metadata(self, pdf_path: Path) -> PaperMetadata:
        """
        Full pipeline: extract identifiers → query APIs → merge results.

        1. Try to extract DOI from PDF filename or content
        2. If DOI found → Crossref lookup
        3. Extract title → search arXiv, PubMed, Semantic Scholar
        4. Merge results, prefer structured API data
        """
        paper_id = pdf_path.stem
        metadata = PaperMetadata(paper_id=paper_id, filename=pdf_path.name)

        # Try to extract DOI from filename patterns
        doi = self._extract_doi_from_filename(pdf_path.name)
        if doi:
            metadata.doi = doi
            crossref_data = await self.lookup_crossref(doi)
            if crossref_data:
                self._merge_metadata(metadata, crossref_data, "crossref")

        # Extract title from PDF (simplified - would use PyMuPDF in production)
        title = self._extract_title_from_filename(pdf_path.name)

        if title and not metadata.title:
            # Try arXiv search
            arxiv_data = await self.search_arxiv(title)
            if arxiv_data:
                self._merge_metadata(metadata, arxiv_data, "arxiv")

            # Try PubMed search
            pubmed_data = await self.search_pubmed(title)
            if pubmed_data:
                self._merge_metadata(metadata, pubmed_data, "pubmed")

            # Try Semantic Scholar
            s2_data = await self.search_semantic_scholar(metadata.title or title)
            if s2_data:
                self._merge_metadata(metadata, s2_data, "semantic_scholar")

        # Calculate confidence based on source coverage
        metadata.extraction_confidence = self._calculate_confidence(metadata)

        return metadata

    def _extract_doi_from_filename(self, filename: str) -> Optional[str]:
        """Extract DOI from common filename patterns."""
        # Pattern: 10.XXXX/something
        doi_pattern = r'10\.\d{4,}/[^\s]+'
        match = re.search(doi_pattern, filename)
        if match:
            return match.group(0)

        # Pattern: s12345-... (Springer)
        if filename.startswith("s") and "-" in filename:
            # Could construct DOI from pattern
            pass

        return None

    def _extract_title_from_filename(self, filename: str) -> Optional[str]:
        """Extract potential title from filename."""
        # Remove extension and clean up
        name = Path(filename).stem
        # Replace underscores and hyphens with spaces
        name = re.sub(r'[_-]', ' ', name)
        # Remove common prefixes/suffixes
        name = re.sub(r'^(s\d+|1\d+|pmc\d+)\s*', '', name, flags=re.I)
        name = re.sub(r'\s*(main|final|preprint|v\d+)$', '', name, flags=re.I)
        return name.strip() if len(name) > 10 else None

    async def search_arxiv(self, title: str) -> Optional[Dict[str, Any]]:
        """Search arXiv by title, return metadata if found."""
        try:
            import arxiv
        except ImportError:
            logger.warning("arxiv package not installed. Run: uv pip install arxiv")
            return None

        try:
            search = arxiv.Search(
                query=f'ti:"{title}"',
                max_results=3,
                sort_by=arxiv.SortCriterion.Relevance
            )
            for result in search.results():
                if self._title_similarity(result.title, title) > 0.7:
                    return {
                        "arxiv_id": result.entry_id.split("/")[-1],
                        "title": result.title,
                        "authors": [a.name for a in result.authors],
                        "abstract": result.summary,
                        "categories": result.categories,
                        "date": result.published.isoformat() if result.published else None,
                    }
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}")

        return None

    async def search_pubmed(self, title: str) -> Optional[Dict[str, Any]]:
        """Search PubMed by title, return metadata if found."""
        try:
            from Bio import Entrez
        except ImportError:
            logger.warning("biopython not installed. Run: uv pip install biopython")
            return None

        try:
            Entrez.email = self.email

            # Search
            handle = Entrez.esearch(db="pubmed", term=f'"{title}"[Title]', retmax=3)
            record = Entrez.read(handle)
            handle.close()

            if not record.get("IdList"):
                return None

            # Fetch details
            pmid = record["IdList"][0]
            handle = Entrez.efetch(db="pubmed", id=pmid, rettype="xml")
            records = Entrez.read(handle)
            handle.close()

            if not records.get("PubmedArticle"):
                return None

            article = records["PubmedArticle"][0]["MedlineCitation"]["Article"]
            return {
                "pmid": pmid,
                "title": str(article.get("ArticleTitle", "")),
                "authors": [
                    f"{a.get('LastName', '')} {a.get('ForeName', '')}"
                    for a in article.get("AuthorList", [])
                    if isinstance(a, dict)
                ],
                "abstract": str(article.get("Abstract", {}).get("AbstractText", [""])[0]),
                "journal": str(article.get("Journal", {}).get("Title", "")),
                "date": article.get("ArticleDate", [{}])[0].get("Year", "")
                       if article.get("ArticleDate") else "",
            }
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")

        return None

    async def lookup_crossref(self, doi: str) -> Optional[Dict[str, Any]]:
        """Lookup DOI in Crossref, return metadata."""
        try:
            url = f"https://api.crossref.org/works/{doi}"
            headers = {"User-Agent": f"MetadataFetcher/1.0 (mailto:{self.email})"}
            resp = await self.client.get(url, headers=headers)

            if resp.status_code != 200:
                return None

            data = resp.json().get("message", {})
            return {
                "doi": doi,
                "title": data.get("title", [""])[0],
                "authors": [
                    f"{a.get('family', '')} {a.get('given', '')}"
                    for a in data.get("author", [])
                ],
                "journal": data.get("container-title", [""])[0],
                "date": "-".join(
                    map(str, data.get("published", {}).get("date-parts", [[]])[0])
                ),
                "citation_count": data.get("is-referenced-by-count", 0),
            }
        except Exception as e:
            logger.warning(f"Crossref lookup failed for {doi}: {e}")

        return None

    async def search_semantic_scholar(self, title: str) -> Optional[Dict[str, Any]]:
        """Search Semantic Scholar, return metadata with citations."""
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": title,
                "limit": 3,
                "fields": "title,authors,abstract,citationCount,influentialCitationCount,tldr"
            }
            resp = await self.client.get(url, params=params)

            if resp.status_code != 200:
                return None

            data = resp.json()
            if not data.get("data"):
                return None

            paper = data["data"][0]
            if self._title_similarity(paper.get("title", ""), title) < 0.7:
                return None

            return {
                "s2_id": paper.get("paperId"),
                "title": paper.get("title"),
                "authors": [a.get("name") for a in paper.get("authors", [])],
                "abstract": paper.get("abstract"),
                "citation_count": paper.get("citationCount", 0),
                "tldr": paper.get("tldr", {}).get("text") if paper.get("tldr") else None,
            }
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")

        return None

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate simple title similarity (Jaccard)."""
        if not title1 or not title2:
            return 0.0

        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _merge_metadata(
        self,
        target: PaperMetadata,
        source: Dict[str, Any],
        source_name: str,
    ) -> None:
        """Merge source data into target, preferring existing values."""
        if source_name not in target.source_apis:
            target.source_apis.append(source_name)

        # Update fields if not already set
        if not target.title and source.get("title"):
            target.title = source["title"]
        if not target.abstract and source.get("abstract"):
            target.abstract = source["abstract"]
        if not target.authors and source.get("authors"):
            target.authors = source["authors"]
        if not target.journal and source.get("journal"):
            target.journal = source["journal"]
        if not target.date and source.get("date"):
            target.date = source["date"]
        if not target.doi and source.get("doi"):
            target.doi = source["doi"]
        if not target.arxiv_id and source.get("arxiv_id"):
            target.arxiv_id = source["arxiv_id"]
        if not target.pmid and source.get("pmid"):
            target.pmid = source["pmid"]
        if not target.s2_id and source.get("s2_id"):
            target.s2_id = source["s2_id"]
        if target.citation_count is None and source.get("citation_count"):
            target.citation_count = source["citation_count"]

        # Merge keywords
        if source.get("categories"):
            target.keywords.extend(source["categories"])
        target.keywords = list(set(target.keywords))

    def _calculate_confidence(self, metadata: PaperMetadata) -> float:
        """Calculate extraction confidence based on field coverage."""
        required_fields = ["title", "authors", "abstract"]
        optional_fields = ["doi", "journal", "date", "pmid", "arxiv_id"]

        required_score = sum(1 for f in required_fields if getattr(metadata, f))
        optional_score = sum(0.5 for f in optional_fields if getattr(metadata, f))
        api_bonus = min(len(metadata.source_apis) * 0.1, 0.3)

        total = (required_score / len(required_fields)) * 0.7 + \
                (optional_score / len(optional_fields)) * 0.2 + \
                api_bonus

        return round(min(total, 1.0), 2)


async def fetch_single(pdf_path: Path) -> PaperMetadata:
    """Fetch metadata for a single PDF."""
    fetcher = MetadataFetcher()
    try:
        metadata = await fetcher.fetch_paper_metadata(pdf_path)
        return metadata
    finally:
        await fetcher.close()


async def fetch_all(directory: Path) -> List[PaperMetadata]:
    """Fetch metadata for all PDFs in a directory."""
    pdf_files = list(directory.rglob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

    fetcher = MetadataFetcher()
    results = []

    try:
        for i, pdf_path in enumerate(pdf_files):
            logger.info(f"[{i+1}/{len(pdf_files)}] Processing {pdf_path.name}")
            try:
                metadata = await fetcher.fetch_paper_metadata(pdf_path)
                results.append(metadata)

                # Save individual metadata file
                METADATA_DIR.mkdir(parents=True, exist_ok=True)
                meta_file = METADATA_DIR / f"{metadata.paper_id}_meta.json"
                with open(meta_file, "w") as f:
                    json.dump(asdict(metadata), f, indent=2)

                # Rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to process {pdf_path.name}: {e}")

    finally:
        await fetcher.close()

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch paper metadata from APIs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch metadata for a single paper")
    fetch_parser.add_argument("pdf_path", type=Path, help="Path to PDF file")

    # fetch-all command
    fetch_all_parser = subparsers.add_parser("fetch-all", help="Fetch metadata for all papers")
    fetch_all_parser.add_argument("directory", type=Path, help="Directory containing PDFs")

    # export command
    subparsers.add_parser("export", help="Export metadata summary")

    args = parser.parse_args()

    if args.command == "fetch":
        metadata = asyncio.run(fetch_single(args.pdf_path))
        print(json.dumps(asdict(metadata), indent=2))

    elif args.command == "fetch-all":
        results = asyncio.run(fetch_all(args.directory))
        print(f"\nProcessed {len(results)} papers")
        print(f"Metadata saved to {METADATA_DIR}")

        # Summary stats
        with_title = sum(1 for r in results if r.title)
        with_doi = sum(1 for r in results if r.doi)
        with_abstract = sum(1 for r in results if r.abstract)
        print(f"  With title: {with_title}/{len(results)}")
        print(f"  With DOI: {with_doi}/{len(results)}")
        print(f"  With abstract: {with_abstract}/{len(results)}")

    elif args.command == "export":
        if not METADATA_DIR.exists():
            print("No metadata found. Run fetch-all first.")
            return

        all_metadata = []
        for meta_file in METADATA_DIR.glob("*_meta.json"):
            with open(meta_file) as f:
                all_metadata.append(json.load(f))

        # Export summary
        summary_file = METADATA_DIR / "metadata_summary.json"
        with open(summary_file, "w") as f:
            json.dump(all_metadata, f, indent=2)

        print(f"Exported {len(all_metadata)} paper metadata to {summary_file}")


if __name__ == "__main__":
    main()
