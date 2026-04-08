# backend/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    # Database: Use data/mentori_app.db if available locally, otherwise fallback to root or env
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/mentori_app.db" if os.path.exists(f"{BASE_DIR}/data/mentori_app.db") else f"sqlite:///{BASE_DIR}/mentori_app.db"
    
    # Auth
    JWT_SECRET: str = "please_change_this_secret_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    
    # LLM Services
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GEMINI_API_KEY: Optional[str] = None

    # RAG / Vector DB
    CHROMA_PERSIST_DIRECTORY: str = f"{BASE_DIR}/data/chroma_db" if os.path.exists(f"{BASE_DIR}/data/chroma_db") else f"{BASE_DIR}/chroma_db"
    
    # Tool Server
    TOOL_SERVER_URL: str = "http://tool-server:8777"

    # Backend Internal URL (used by tool-server to POST progress events back)
    BACKEND_INTERNAL_URL: str = "http://localhost:8766"
    
    # Workspace
    # Default to data/workspace locally if exists, else root workspace, allowing override
    _default_ws = f"{BASE_DIR}/data/workspace" if os.path.exists(f"{BASE_DIR}/data/workspace") else f"{BASE_DIR}/workspace"
    WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", _default_ws)
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
