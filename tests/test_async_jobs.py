import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, SQLModel, create_engine
from backend.retrieval.models import UserCollection, IndexStatus
from backend.retrieval.jobs import run_ingestion_job, calculate_estimation
import uuid
import os

# Use file-based DB for sharing state between test and function
TEST_DB = "test_jobs.db"
test_engine = create_engine(f"sqlite:///{TEST_DB}")

@pytest.fixture(name="session")
def session_fixture():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_calculate_estimation():
    # Mock Path.stat to return size
    # We need to mock Path where it is IMPORTED in jobs.py
    with patch("backend.retrieval.jobs.Path") as mock_path:
        # Configure the mock object returned by Path(fp)
        path_instance = mock_path.return_value
        path_instance.exists.return_value = True
        path_instance.stat.return_value.st_size = 1024 * 1024 * 5 # 5 MB
        
        # 3 files * 5 MB = 15 MB
        # Est = (15 * 2.0) + 5.0 = 35 seconds
        files = ["a.pdf", "b.pdf", "c.pdf"]
        est = calculate_estimation(files)
        assert est == 35

@patch("backend.retrieval.jobs.SimpleIngestor")
@patch("backend.retrieval.jobs.engine", new=test_engine) # Patch the engine global var in jobs.py
def test_run_ingestion_job_success(MockIngestor, session):
    # Setup Data
    idx_id = str(uuid.uuid4())
    col = UserCollection(
        id=idx_id, 
        user_id="user1", 
        name="Test Index", 
        status=IndexStatus.PENDING,
        file_paths=["test.pdf"]
    )
    session.add(col)
    session.commit()
    # Close session to flush to DB file so next session picks it up
    session.close()

    # Mock Ingestor behavior
    mock_instance = MockIngestor.return_value
    mock_instance.ingest_file.return_value = {
        "status": "success", "num_chunks": 10
    }
    
    # Needs to patch os.path.exists to True
    with patch("backend.retrieval.jobs.os.path.exists", return_value=True):
        # Run Job
        # It triggers: with Session(engine) as session (USING PATCHED ENGINE)
        run_ingestion_job(idx_id, ["test.pdf"])

    # Verify
    # Open new session to check DB state
    with Session(test_engine) as check_session:
         updated_col = check_session.get(UserCollection, idx_id)
         assert updated_col.status == IndexStatus.READY
         assert updated_col.vector_db_collection_name == f"collection_{idx_id}"
         assert updated_col.metrics["total_chunks"] == 10
