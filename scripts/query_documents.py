#!/usr/bin/env python3
"""
CLI tool for querying documents in RAG system.

Usage:
    python scripts/query_documents.py "your query here"
    python scripts/query_documents.py "CRISPR mechanism" --top-k 5
"""

import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.retrieval.embeddings import EmbeddingEngine
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.retriever import SimpleRetriever


def main():
    parser = argparse.ArgumentParser(
        description="Query documents in RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/query_documents.py "How does CRISPR work?"
  python scripts/query_documents.py "machine learning methods" --top-k 10
  python scripts/query_documents.py "gene editing" --no-hybrid
        """
    )

    parser.add_argument(
        "query",
        help="Search query"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--collection",
        default="mentori_documents",
        help="Collection name (default: mentori_documents)"
    )
    parser.add_argument(
        "--no-hybrid",
        action="store_true",
        help="Disable hybrid search (use dense-only)"
    )
    parser.add_argument(
        "--show-metadata",
        action="store_true",
        help="Show full metadata for results"
    )

    args = parser.parse_args()

    # Initialize retriever with persistent storage
    persist_dir = Path.home() / ".mentori" / "chroma_db"

    if not persist_dir.exists():
        print(f"\n⚠️  Storage directory not found: {persist_dir}")
        print("Ingest some documents first using:")
        print("  python scripts/ingest_documents.py <file_or_directory>")
        sys.exit(1)

    print(f"Initializing retriever (collection: {args.collection})...")
    print(f"Storage: {persist_dir}")

    embedder = EmbeddingEngine()
    vector_store = VectorStore(persist_directory=str(persist_dir))
    retriever = SimpleRetriever(
        embedder=embedder,
        vector_store=vector_store,
        collection_name=args.collection
    )

    # Check if collection has documents
    count = vector_store.count(args.collection)
    if count == 0:
        print(f"\n⚠️  Collection '{args.collection}' is empty!")
        print("Ingest some documents first using:")
        print("  python scripts/ingest_documents.py <file_or_directory>")
        sys.exit(1)

    print(f"Found {count} chunks in collection\n")

    # Perform search
    print(f"Query: '{args.query}'")
    print(f"Settings: top_k={args.top_k}, hybrid={'disabled' if args.no_hybrid else 'enabled'}")
    print("=" * 80)

    results = retriever.retrieve(
        query=args.query,
        top_k=args.top_k,
        use_hybrid=not args.no_hybrid
    )

    if not results:
        print("No results found.")
        sys.exit(0)

    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n{i}. ", end="")

        # Show scores
        if 'hybrid_score' in result:
            print(f"[Hybrid: {result['hybrid_score']:.3f} | "
                  f"Dense: {result['dense_score']:.3f} | "
                  f"Sparse: {result['sparse_score']:.3f}]")
        else:
            print(f"[Score: {result['score']:.3f}]")

        # Show text (truncated)
        text = result['text']
        if len(text) > 200:
            text = text[:200] + "..."
        print(f"   {text}")

        # Show metadata if requested
        if args.show_metadata:
            metadata = result.get('metadata', {})
            print(f"   Metadata: {metadata}")

    print("\n" + "=" * 80)
    print(f"Returned {len(results)} results")


if __name__ == "__main__":
    main()
