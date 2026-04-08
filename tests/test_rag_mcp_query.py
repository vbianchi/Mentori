import asyncio
import sys
import uuid
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import engine, init_db
from backend.retrieval.models import UserCollection, IndexStatus
from sqlmodel import Session, select
from backend.mcp.custom.rag_tools import query_documents

async def main():
    # 1. Setup DB Entry to make the index "visible" to the tool
    # We pretend user_id="test_user" owns this index
    user_id = "test_user"
    index_name = "Mentori Papers"
    collection_name_in_chroma = "mentori_documents" # Must match what we ingested into

    print(f"Seeding DB for index '{index_name}' -> '{collection_name_in_chroma}'")
    
    with Session(engine) as session:
        # Check if exists
        idx = session.exec(
            select(UserCollection)
            .where(UserCollection.user_id == user_id, UserCollection.name == index_name)
        ).first()

        if not idx:
            new_index = UserCollection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=index_name,
                status=IndexStatus.READY,
                vector_db_collection_name=collection_name_in_chroma, # Crucial mapping
                file_paths=[],
                metrics={}
            )
            session.add(new_index)
            session.commit()
            print("✓ Created DB entry")
        else:
            print("✓ DB entry already exists")
            # Ensure it points to correct chroma collection
            idx.vector_db_collection_name = collection_name_in_chroma
            idx.status = IndexStatus.READY
            session.add(idx)
            session.commit()

    # 2. Query the index using the Tool
    query = "What is a Recursive Language Model?"
    print(f"\nQuerying: '{query}'")
    
    result = await query_documents(
        query=query,
        index_name=index_name,
        user_id=user_id,
        task_id="test_task",
        max_results=3
    )
    
    print("\n--- Result ---")
    print(result)
    
    if "Recursive Language Model" in result or "RLM" in result:
        print("\n✅ Verification PASSED: Retrieved relevant content.")
    else:
        print("\n❌ Verification FAILED: Content not found.")

if __name__ == "__main__":
    asyncio.run(main())
