
import sys
import os

# Ensure backend modules are found
sys.path.append("/app")

from backend.config import settings
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.embeddings import EmbeddingEngine

print(f"--- Chroma Debug info ---")
print(f"Persist Dir: {settings.CHROMA_PERSIST_DIRECTORY}")
print(f"Exists: {os.path.exists(settings.CHROMA_PERSIST_DIRECTORY)}")
if os.path.exists(settings.CHROMA_PERSIST_DIRECTORY):
    print(f"Contents: {os.listdir(settings.CHROMA_PERSIST_DIRECTORY)}")

try:
    store = VectorStore(persist_directory=settings.CHROMA_PERSIST_DIRECTORY)
    cols = store.list_collections()
    print(f"\nCollections found: {cols}")

    embedder = EmbeddingEngine()
    
    for c in cols:
        count = store.count(c)
        print(f"Collection '{c}': {count} documents")
        
        # Try a query
        if count > 0:
            print(f"  Attempting query on '{c}'...")
            q_vec = embedder.embed_query("HTS")
            res = store.search(q_vec, n_results=1, collection_name=c)
            print(f"  Result: {len(res['documents'][0])} matches found.")
            print(f"  Top match: {res['documents'][0][0][:50]}...")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
