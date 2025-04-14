# backend/config.py
import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Settings:
    """Holds application configuration settings."""
    # AI Provider ('gemini' or 'ollama')
    ai_provider: str = field(default_factory=lambda: os.getenv('AI_PROVIDER', 'gemini').lower())

    # Gemini Settings
    google_api_key: str | None = field(default_factory=lambda: os.getenv('GOOGLE_API_KEY'))
    gemini_model_name: str = field(default_factory=lambda: os.getenv('GEMINI_MODEL', 'gemini-1.5-flash-latest')) # Use a known recent model

    # Ollama Settings
    ollama_base_url: str = field(default_factory=lambda: os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
    ollama_model_name: str = field(default_factory=lambda: os.getenv('OLLAMA_MODEL', 'gemma:2b')) # A smaller default model

    def __post_init__(self):
        """Validate settings after initialization."""
        if self.ai_provider == 'gemini' and not self.google_api_key:
            logger.warning("AI_PROVIDER is 'gemini' but GOOGLE_API_KEY is not set in environment or .env file.")
            # You might want to raise an error here depending on desired behavior
            # raise ValueError("GOOGLE_API_KEY is required when AI_PROVIDER is 'gemini'")

        logger.info(f"Configuration loaded: AI Provider = {self.ai_provider}")
        if self.ai_provider == 'gemini':
            logger.info(f"Gemini Model = {self.gemini_model_name}")
            logger.info(f"Google API Key Loaded: {'Yes' if self.google_api_key else 'No'}")
        elif self.ai_provider == 'ollama':
            logger.info(f"Ollama Model = {self.ollama_model_name}")
            logger.info(f"Ollama Base URL = {self.ollama_base_url}")


def load_settings() -> Settings:
    """Loads settings from .env file and environment variables."""
    # Load environment variables from .env file, if it exists
    # find_dotenv() searches for the .env file in parent directories
    # load_dotenv(find_dotenv()) # Use this if .env might be elsewhere
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Assumes .env is in project root
    if os.path.exists(env_path):
         logger.info(f"Loading environment variables from: {env_path}")
         load_dotenv(dotenv_path=env_path)
    else:
         logger.info(".env file not found, loading from environment variables only.")

    return Settings()

# Example usage (optional, for testing config loading)
if __name__ == "__main__":
    settings = load_settings()
    print("\n--- Configuration ---")
    print(f"AI Provider: {settings.ai_provider}")
    print(f"Google API Key: {'Loaded' if settings.google_api_key else 'Not Set'}")
    print(f"Gemini Model: {settings.gemini_model_name}")
    print(f"Ollama Base URL: {settings.ollama_base_url}")
    print(f"Ollama Model: {settings.ollama_model_name}")
    print("---------------------\n")

