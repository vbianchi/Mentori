#!/usr/bin/env python3
"""
CLI tool for ingesting documents into RAG system.

Usage:
    python scripts/ingest_documents.py <file_or_directory>
    python scripts/ingest_documents.py tests/test_files_rag/papers/
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.retrieval.ingestor import SimpleIngestor


import asyncio

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_documents.py <file_or_directory>")
        print("\nExamples:")
        print("  python scripts/ingest_documents.py tests/test_files_rag/papers/")
        print("  python scripts/ingest_documents.py paper.pdf")
        sys.exit(1)

    target = sys.argv[1]
    path = Path(target)

    if not path.exists():
        print(f"Error: {target} not found")
        sys.exit(1)

    # Initialize ingestor with persistent storage
    from backend.config import settings
    collection_name = "mentori_documents"
    persist_dir = Path(settings.CHROMA_PERSIST_DIRECTORY) # Align with Backend Config
    persist_dir.mkdir(parents=True, exist_ok=True)

    print(f"Initializing ingestor (collection: {collection_name})...")
    print(f"Storage: {persist_dir}")

    from backend.retrieval.embeddings import EmbeddingEngine
    from backend.retrieval.vector_store import VectorStore
    from backend.retrieval.chunking import SimpleChunker

    embedder = EmbeddingEngine()
    vector_store = VectorStore(persist_directory=str(persist_dir))
    chunker = SimpleChunker()

    ingestor = SimpleIngestor(
        embedder=embedder,
        vector_store=vector_store,
        chunker=chunker,
        collection_name=collection_name
    )

    # Ingest
    if path.is_file():
        print(f"\nIngesting file: {path.name}")
        result = await ingestor.ingest_file(str(path))

        if result['status'] == 'success':
            print(f"✓ Success!")
            print(f"  - Chunks: {result['num_chunks']}")
            print(f"  - Tokens: {result['total_tokens']}")
            if result.get('num_pages', 0) > 0:
                print(f"  - Pages: {result['num_pages']}")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    elif path.is_dir():
        print(f"\nIngesting directory: {path.name}")
        # Note: ingest_directory involves multiple calls, simple version here might not be fully async optimized 
        # but ingest_directory in SimpleIngestor isn't async? Let's check. 
        # SimpleIngestor.ingest_directory calls ingest_file which IS async. 
        # So ingest_directory needs to be updated or we loop here. 
        # The provided ingest_directory code (Step 41) is synchronous and loops calling self.ingest_file.
        # But wait, step 41 ingest_directory calls: result = self.ingest_file(...)
        # It does NOT await it. This means ingest_directory is BROKEN in the codebase too!
        # I should fix ingest_directory in ingestor.py as well? Or just loop here.
        # Let's loop here for safety.
        
        files = list(path.glob("*.pdf"))
        print(f"Found {len(files)} PDFs")
        
        results = []
        for file_path in files:
            res = await ingestor.ingest_file(str(file_path))
            results.append(res)
            
        successful = [r for r in results if r["status"] == "success"]
        print(f"✓ Completed! {len(successful)}/{len(files)} files.")

    else:
        print(f"Error: {target} is neither a file nor directory")
        sys.exit(1)

    # Show final stats
    stats = ingestor.get_ingestion_stats()
    print(f"\n📊 Collection Statistics:")
    print(f"  - Collection: {stats['collection']}")
    # print(f"  - Total chunks: {stats['total_chunks']}") # This might be blocking? 
    # vector_store.count is sync.
    print(f"  - Model: {stats['model_name']}")


if __name__ == "__main__":
    asyncio.run(main())

