from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from backend.main import app
from backend.database import get_session
from backend.auth import get_current_user
from backend.models.user import User
from backend.retrieval.models import UserCollection # Import to register tables
from unittest.mock import patch
import pytest
import os
import uuid

# Setup Test DB
TEST_DB = "test_api.db"
test_engine = create_engine(f"sqlite:///{TEST_DB}")

def get_session_override():
    with Session(test_engine) as session:
        yield session

def get_current_user_override():
    return User(id="test_user_1", email="test@example.com", full_name="Test User", hash_password="xxx")

# App Dependency Overrides
app.dependency_overrides[get_session] = get_session_override
app.dependency_overrides[get_current_user] = get_current_user_override

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    test_engine.dispose()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    SQLModel.metadata.create_all(test_engine)
    yield
    test_engine.dispose()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@patch("backend.retrieval.jobs.engine", test_engine)
def test_create_and_list_index():
    # 1. Create Index
    payload = {
        "name": "My Research",
        "file_paths": ["/tmp/paper1.pdf", "/tmp/paper2.pdf"]
    }
    # Mock Ingestor so we don't actually run heavy logic in integration test
    with patch("backend.retrieval.jobs.SimpleIngestor") as MockIngestor:
         mock_inst = MockIngestor.return_value
         mock_inst.ingest_file.return_value = {"status": "success"}
         
         with patch("backend.retrieval.jobs.os.path.exists", return_value=True):
            response = client.post("/rag/indexes/", json=payload)
    
    # Assert Accepted
    assert response.status_code == 202
    data = response.json()
    assert data["name"] == "My Research"
    
    # 2. List Indexes
    response = client.get("/rag/indexes/")
    assert response.status_code == 200
    res_list = response.json()
    assert len(res_list) >= 1

def test_delete_index():
    # Create manually in DB
    idx_id = str(uuid.uuid4())
    
    with Session(test_engine) as session:
        from backend.retrieval.models import UserCollection, IndexStatus
        idx = UserCollection(
            id=idx_id,
            user_id="test_user_1",
            name="To Delete",
            status=IndexStatus.READY
        )
        session.add(idx)
        session.commit()
    
    # Delete
    response = client.delete(f"/rag/indexes/{idx_id}")
    assert response.status_code == 200
    
    # Verify Gone
    response = client.get("/rag/indexes/")
    # User might have other indexes from previous tests if DB not cleared?
    # Fixture creates fresh DB per session, autouse=True runs per function? 
    # Yes default scope is function.
    res_list = response.json()
    assert len(res_list) == 0
