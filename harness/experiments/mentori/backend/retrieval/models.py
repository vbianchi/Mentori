from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from enum import Enum
import json

class IndexStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class UserCollection(SQLModel, table=True):
    __tablename__ = "user_collections"

    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    name: str
    description: Optional[str] = Field(default=None)  # User-provided description of the index
    status: IndexStatus = Field(default=IndexStatus.PENDING)
    
    # Storing lists/dicts as JSON strings for SQLite compatibility
    file_paths_json: str = Field(default="[]") 
    metrics_json: str = Field(default="{}")
    
    estimated_time_seconds: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    vector_db_collection_name: Optional[str] = Field(default=None)

    # Ingestion strategy metadata
    ocr_tool: Optional[str] = Field(default=None)  # e.g., "tesseract", "None"
    transcriber_model: Optional[str] = Field(default=None)  # e.g., "deepseek-ocr:3b", "None"

    # User-configurable ingestion settings
    use_vlm: bool = Field(default=False)  # Whether to use VLM for page analysis
    chunk_size: int = Field(default=512)  # Target chunk size in tokens (V2-3: simple_512 MRR=0.988)
    chunk_overlap: int = Field(default=2)  # Number of overlapping sentences between chunks
    chunking_strategy: str = Field(default="simple")  # "simple" or "semantic" (V2-3: simple wins)
    embedding_model: str = Field(default="BAAI/bge-m3")  # V2-1: BGE-M3 wins decisively; SPECTER2 collapses at scale

    error_message: Optional[str] = Field(default=None)

    @property
    def file_paths(self) -> list:
        try:
            return json.loads(self.file_paths_json)
        except:
            return []

    @file_paths.setter
    def file_paths(self, value: list):
        self.file_paths_json = json.dumps(value)

    @property
    def metrics(self) -> dict:
        try:
            return json.loads(self.metrics_json)
        except:
            return {}

    @metrics.setter
    def metrics(self, value: dict):
        self.metrics_json = json.dumps(value)
