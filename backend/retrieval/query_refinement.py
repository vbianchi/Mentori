"""
Query Refinement for RAG

Deterministic query processing to improve retrieval quality.
Extracts proper nouns, builds disjunctive queries, and identifies
query types for optimal tool routing.

This is restored from the old RAG system - it helps with:
- Author name searches (proper noun extraction)
- Building keyword-rich queries for BM25
- Identifying query intent without using LLM
"""

import re
from collections import Counter
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class QueryType:
    """Query type constants."""
    METADATA = "metadata"      # Author, title, date queries
    FACTUAL = "factual"        # Content/fact queries
    COMPLEX = "complex"        # Multi-document, comparison queries
    UNKNOWN = "unknown"


def extract_proper_nouns(text: str, max_terms: int = 30) -> List[str]:
    """
    Extract proper nouns (likely names, titles, organizations) from text.

    Uses capitalization patterns to identify proper nouns without NLP models.

    Args:
        text: Text to analyze
        max_terms: Maximum terms to return

    Returns:
        List of potential proper nouns, prioritized by likelihood
    """
    if not text:
        return []

    # Find proper-noun-like spans (capitalized multi-word phrases)
    # This regex finds sequences of capitalized words
    proper_nouns = re.findall(
        r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b",
        text
    )

    # Filter out common words that happen to be at start of sentences
    common_starts = {
        'The', 'This', 'That', 'These', 'Those', 'What', 'Which', 'Where',
        'When', 'Why', 'How', 'Can', 'Could', 'Would', 'Should', 'Will',
        'Do', 'Does', 'Did', 'Is', 'Are', 'Was', 'Were', 'Have', 'Has',
        'Find', 'Search', 'Look', 'Show', 'Get', 'List', 'Give', 'Tell'
    }

    filtered = [
        noun for noun in proper_nouns
        if noun not in common_starts and len(noun) > 2
    ]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for noun in filtered:
        if noun.lower() not in seen:
            seen.add(noun.lower())
            unique.append(noun)

    return unique[:max_terms]


def extract_keywords(text: str, max_terms: int = 20) -> List[str]:
    """
    Extract significant keywords from text.

    Uses frequency and length heuristics to find important terms.

    Args:
        text: Text to analyze
        max_terms: Maximum keywords to return

    Returns:
        List of keywords, ordered by significance
    """
    if not text:
        return []

    # Extract alphanumeric tokens, ignoring short ones
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())

    # Common stopwords to filter
    stopwords = {
        'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was',
        'were', 'been', 'being', 'have', 'has', 'had', 'having', 'does',
        'did', 'doing', 'would', 'could', 'should', 'will', 'shall', 'can',
        'may', 'might', 'must', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
        'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'only', 'own', 'same', 'than', 'too', 'very', 'just', 'also', 'now',
        'find', 'search', 'look', 'show', 'get', 'list', 'give', 'tell',
        'papers', 'paper', 'article', 'articles', 'document', 'documents',
        'written', 'wrote', 'author', 'authored', 'index', 'query'
    }

    filtered = [t for t in tokens if t not in stopwords and len(t) > 2]

    # Get most common
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(max_terms)]


def classify_query(query: str) -> Tuple[str, Dict]:
    """
    Classify query type to determine optimal retrieval strategy.

    Args:
        query: User query

    Returns:
        Tuple of (query_type, metadata dict with extracted info)
    """
    query_lower = query.lower()
    metadata = {
        "proper_nouns": extract_proper_nouns(query),
        "keywords": extract_keywords(query),
        "original_query": query
    }

    # Check for metadata queries (author, title, filename)
    metadata_patterns = [
        r'\b(papers?|articles?|documents?)\s+(by|from|written\s+by|authored\s+by)\b',
        r'\b(find|search|look\s+for|get|list)\s+.*(by|from)\s+',
        r'\bwho\s+(wrote|authored|is\s+the\s+author)\b',
        r'\bauthor(s|ed)?\s+(of|is|are)\b',
        r'\btitle\s+(of|is|contains?)\b',
        r'\bwritten\s+by\b',
        r'\bby\s+me\b',  # "papers by me"
    ]

    for pattern in metadata_patterns:
        if re.search(pattern, query_lower):
            # Extract the name/entity being searched for
            metadata["query_subtype"] = "author_search"

            # Try to extract the author name
            author_match = re.search(
                r'(?:by|from|written\s+by|authored\s+by)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
                query
            )
            if author_match:
                metadata["target_author"] = author_match.group(1)
            elif metadata["proper_nouns"]:
                metadata["target_author"] = metadata["proper_nouns"][0]

            return QueryType.METADATA, metadata

    # Check for complex research queries
    complex_patterns = [
        r'\b(compare|comparison|contrast|difference|similarities)\b',
        r'\b(analyze|analysis|examine|investigate)\s+(all|each|every)\b',
        r'\b(summarize|summary|overview)\s+(all|the|these)\b',
        r'\b(across|between)\s+(all|the|multiple|different)\b',
        r'\bgap(s)?\s+(in|analysis)\b',
        r'\b(systematic|comprehensive|thorough)\s+(review|analysis)\b',
    ]

    for pattern in complex_patterns:
        if re.search(pattern, query_lower):
            metadata["query_subtype"] = "multi_document_analysis"
            return QueryType.COMPLEX, metadata

    # Check for pure proper noun queries (likely author name searches)
    # E.g., "Valerio Bianchi" or "John Smith" without any other context
    if metadata["proper_nouns"]:
        words = query.split()
        # If query is primarily proper nouns (2-4 words, mostly capitalized)
        if 2 <= len(words) <= 4:
            capitalized_count = sum(1 for w in words if w[0].isupper())
            if capitalized_count / len(words) >= 0.5:
                # Likely a name search
                metadata["query_subtype"] = "author_search"
                metadata["target_author"] = metadata["proper_nouns"][0]
                logger.info(f"Detected pure proper noun query as author search: '{query}'")
                return QueryType.METADATA, metadata

    # Default to factual query
    metadata["query_subtype"] = "content_search"
    return QueryType.FACTUAL, metadata


def build_search_queries(
    query: str,
    context: Optional[str] = None,
    k: int = 5
) -> List[str]:
    """
    Build optimized search queries from user query.

    Creates multiple query variants for better recall:
    - Original query
    - Proper noun focused queries
    - Keyword combinations

    Args:
        query: Original user query
        context: Optional context text for keyword extraction
        k: Number of queries to generate

    Returns:
        List of search query strings
    """
    queries = []

    # Add cleaned original query
    clean_query = re.sub(r'^(find|search|look\s+for|get|list|show)\s+', '', query, flags=re.I)
    clean_query = re.sub(r'\s+(in|from|within)\s+.*$', '', clean_query, flags=re.I)
    if clean_query.strip():
        queries.append(clean_query.strip())

    # Add proper noun queries (exact match)
    proper_nouns = extract_proper_nouns(query)
    for noun in proper_nouns[:3]:
        queries.append(f'"{noun}"')

    # Add keyword queries from context if provided
    if context:
        keywords = extract_keywords(context)
        phrases = [k for k in extract_proper_nouns(context) if ' ' in k]

        # Build disjunctive queries
        for i in range(min(k - len(queries), len(phrases))):
            if i < len(phrases):
                parts = [f'"{phrases[i]}"']
                if i < len(keywords):
                    parts.append(keywords[i])
                queries.append(" OR ".join(parts))

    # Ensure uniqueness
    seen = set()
    unique_queries = []
    for q in queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique_queries.append(q)

    return unique_queries[:k]


def refine_for_bm25(query: str) -> str:
    """
    Refine query for BM25 keyword search.

    Extracts key terms and formats for optimal BM25 matching.

    Args:
        query: Original query

    Returns:
        BM25-optimized query string
    """
    # Extract proper nouns first (highest priority)
    proper_nouns = extract_proper_nouns(query)

    # Then keywords
    keywords = extract_keywords(query)

    # Combine, prioritizing proper nouns
    terms = proper_nouns + [k for k in keywords if k.lower() not in [p.lower() for p in proper_nouns]]

    if not terms:
        return query

    # For short queries with proper nouns, use exact matching
    if proper_nouns and len(query.split()) <= 5:
        return " ".join(f'"{noun}"' for noun in proper_nouns[:3])

    return " ".join(terms[:10])


def suggest_tool(query_type: str, metadata: Dict) -> str:
    """
    Suggest the best RAG tool based on query classification.

    Args:
        query_type: The classified query type
        metadata: Query metadata from classification

    Returns:
        Suggested tool name
    """
    if query_type == QueryType.METADATA:
        return "inspect_document_index"

    if query_type == QueryType.COMPLEX:
        return "deep_research_rlm"

    return "query_documents"


# Convenience function for quick query analysis
def analyze_query(query: str) -> Dict:
    """
    Analyze a query and return all relevant information.

    Args:
        query: User query

    Returns:
        Dict with:
        - type: Query type
        - proper_nouns: Extracted proper nouns
        - keywords: Extracted keywords
        - suggested_tool: Recommended RAG tool
        - refined_query: BM25-optimized query
        - search_queries: Multiple search query variants
    """
    query_type, metadata = classify_query(query)

    return {
        "type": query_type,
        "proper_nouns": metadata.get("proper_nouns", []),
        "keywords": metadata.get("keywords", []),
        "target_author": metadata.get("target_author"),
        "suggested_tool": suggest_tool(query_type, metadata),
        "refined_query": refine_for_bm25(query),
        "search_queries": build_search_queries(query),
    }
