# backend/config.py
import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logging.basicConfig(level=logging.INFO) # Basic config set early
logger = logging.getLogger(__name__)

def parse_comma_separated_list(env_var: Optional[str], default: Optional[List[str]] = None) -> List[str]:
    """Parses a comma-separated string from env var into a list."""
    if env_var:
        return [item.strip() for item in env_var.split(',') if item.strip()]
    return default if default is not None else []

@dataclass
class Settings:
    """Holds application configuration settings loaded from environment variables."""

    # --- Required Settings ---
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv('GOOGLE_API_KEY'))
    entrez_email: Optional[str] = field(default_factory=lambda: os.getenv('ENTREZ_EMAIL'))

    # --- Core LLM Configuration ---
    default_llm_id: str = field(default_factory=lambda: os.getenv('DEFAULT_LLM_ID', 'gemini::gemini-1.5-flash'))
    ollama_base_url: str = field(default_factory=lambda: os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))

    # --- LLM Model Selection Configuration ---
    # These are parsed into lists in __post_init__
    _gemini_available_models_str: Optional[str] = field(default_factory=lambda: os.getenv('GEMINI_AVAILABLE_MODELS'))
    _ollama_available_models_str: Optional[str] = field(default_factory=lambda: os.getenv('OLLAMA_AVAILABLE_MODELS'))
    gemini_available_models: List[str] = field(default_factory=list, init=False)
    ollama_available_models: List[str] = field(default_factory=list, init=False)

    # --- Agent & LLM Tuning ---
    agent_max_iterations: int = field(default_factory=lambda: int(os.getenv('AGENT_MAX_ITERATIONS', '15')))
    agent_memory_window_k: int = field(default_factory=lambda: int(os.getenv('AGENT_MEMORY_WINDOW_K', '10')))
    gemini_temperature: float = field(default_factory=lambda: float(os.getenv('GEMINI_TEMPERATURE', '0.7')))
    ollama_temperature: float = field(default_factory=lambda: float(os.getenv('OLLAMA_TEMPERATURE', '0.5')))

    # --- Tool Settings ---
    tool_web_reader_max_length: int = field(default_factory=lambda: int(os.getenv('TOOL_WEB_READER_MAX_LENGTH', '4000')))
    tool_web_reader_timeout: float = field(default_factory=lambda: float(os.getenv('TOOL_WEB_READER_TIMEOUT', '15.0')))
    tool_shell_timeout: int = field(default_factory=lambda: int(os.getenv('TOOL_SHELL_TIMEOUT', '60')))
    tool_shell_max_output: int = field(default_factory=lambda: int(os.getenv('TOOL_SHELL_MAX_OUTPUT', '3000')))
    tool_installer_timeout: int = field(default_factory=lambda: int(os.getenv('TOOL_INSTALLER_TIMEOUT', '300')))
    tool_pubmed_default_max_results: int = field(default_factory=lambda: int(os.getenv('TOOL_PUBMED_DEFAULT_MAX_RESULTS', '5')))
    tool_pubmed_max_snippet: int = field(default_factory=lambda: int(os.getenv('TOOL_PUBMED_MAX_SNIPPET', '250')))

    # --- Server Settings ---
    websocket_max_size_bytes: int = field(default_factory=lambda: int(os.getenv('WEBSOCKET_MAX_SIZE_BYTES', '16777216'))) # 16MB
    websocket_ping_interval: int = field(default_factory=lambda: int(os.getenv('WEBSOCKET_PING_INTERVAL', '20')))
    websocket_ping_timeout: int = field(default_factory=lambda: int(os.getenv('WEBSOCKET_PING_TIMEOUT', '30')))
    direct_command_timeout: int = field(default_factory=lambda: int(os.getenv('DIRECT_COMMAND_TIMEOUT', '120')))

    # --- Optional Settings ---
    file_server_hostname: str = field(default_factory=lambda: os.getenv('FILE_SERVER_HOSTNAME', 'localhost'))
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO').upper())

    # --- Parsed/Derived values (not directly from env) ---
    default_provider: str = field(init=False)
    default_model_name: str = field(init=False)

    def __post_init__(self):
        """Validate settings and parse derived values after initialization."""
        # Validate Log Level
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.warning(f"Invalid LOG_LEVEL '{self.log_level}', defaulting to INFO.")
            self.log_level = "INFO"

        # Parse Default LLM ID
        try:
            provider, model_name = self.default_llm_id.split("::", 1)
            if provider not in ['gemini', 'ollama'] or not model_name:
                raise ValueError("Invalid format or missing components.")
            self.default_provider = provider
            self.default_model_name = model_name
        except ValueError:
            logger.error(f"Invalid DEFAULT_LLM_ID format: '{self.default_llm_id}'. Expected 'provider::model_name'. Using fallback 'gemini::gemini-1.5-flash'.")
            self.default_llm_id = 'gemini::gemini-1.5-flash'
            self.default_provider = 'gemini'
            self.default_model_name = 'gemini-1.5-flash'

        # Validate Gemini Key if Gemini is default or available
        # Check requires parsing available models first
        self.gemini_available_models = parse_comma_separated_list(
            self._gemini_available_models_str,
            default=['gemini-1.5-flash', 'gemini-1.5-pro-latest'] # Sensible defaults if not set
        )
        self.ollama_available_models = parse_comma_separated_list(
            self._ollama_available_models_str,
            default=['gemma:2b', 'llama3:latest'] # Sensible defaults if not set
        )

        is_gemini_needed = self.default_provider == 'gemini' or any('gemini' in model_id.lower() for model_id in self.gemini_available_models)
        if is_gemini_needed and not self.google_api_key:
            logger.error("Gemini models are configured but GOOGLE_API_KEY is not set. Application may fail.")
            # raise ValueError("GOOGLE_API_KEY is required when Gemini models are configured.")

        if not self.entrez_email:
            logger.warning("ENTREZ_EMAIL is not set. PubMed search tool functionality will be limited or blocked by NCBI.")


        # Log loaded configuration
        logger.info("--- Configuration Loaded ---")
        logger.info(f"Default LLM ID: {self.default_llm_id} (Provider: {self.default_provider}, Model: {self.default_model_name})")
        logger.info(f"Google API Key Loaded: {'Yes' if self.google_api_key else 'No'}")
        logger.info(f"Entrez Email Set: {'Yes' if self.entrez_email else 'No (PubMed tool potentially disabled)'}")
        logger.info(f"Ollama Base URL: {self.ollama_base_url}")
        logger.info(f"Available Gemini Models: {self.gemini_available_models}")
        logger.info(f"Available Ollama Models: {self.ollama_available_models}")
        logger.info(f"Agent Max Iterations: {self.agent_max_iterations}")
        logger.info(f"Agent Memory Window (K): {self.agent_memory_window_k}")
        logger.info(f"Gemini Temperature: {self.gemini_temperature}")
        logger.info(f"Ollama Temperature: {self.ollama_temperature}")
        logger.info(f"Tool Shell Timeout: {self.tool_shell_timeout}s, Max Output: {self.tool_shell_max_output} chars")
        logger.info(f"Tool Web Reader Timeout: {self.tool_web_reader_timeout}s, Max Length: {self.tool_web_reader_max_length} chars")
        logger.info(f"Tool Installer Timeout: {self.tool_installer_timeout}s")
        logger.info(f"Tool PubMed Defaults: Max Results={self.tool_pubmed_default_max_results}, Max Snippet={self.tool_pubmed_max_snippet} chars")
        logger.info(f"WebSocket Ping Interval: {self.websocket_ping_interval}s, Timeout: {self.websocket_ping_timeout}s, Max Size: {self.websocket_max_size_bytes} bytes")
        logger.info(f"Direct Command Timeout: {self.direct_command_timeout}s")
        logger.info(f"File Server Hostname (for client URLs): {self.file_server_hostname}")
        logger.info(f"Log Level: {self.log_level}")
        logger.info("--------------------------")


def load_settings() -> Settings:
    """Loads settings from .env file and environment variables."""
    # Load environment variables from .env file, if it exists
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Assumes .env is in project root
    if os.path.exists(env_path):
         logger.info(f"Loading environment variables from: {env_path}")
         load_dotenv(dotenv_path=env_path)
    else:
         logger.info(f".env file not found at expected location ({env_path}), loading from environment variables only.")

    # Catch potential errors during Settings instantiation (e.g., invalid int/float)
    try:
        return Settings()
    except (ValueError, TypeError) as e:
        logger.error(f"Error creating Settings object from environment variables: {e}", exc_info=True)
        logger.error("Please check your .env file or environment variables for correct formats (numbers, floats).")
        raise ValueError(f"Configuration Error: {e}") from e

# --- Create and export the global settings instance ---
settings = load_settings()
# ------------------------------------------------------

# Example usage (optional, for testing config loading)
if __name__ == "__main__":
    # Settings instance is already created and loaded above
    print("\n--- Configuration Test Access ---")
    print(f"Default Provider: {settings.default_provider}")
    print(f"Default Model: {settings.default_model_name}")
    print(f"Memory K: {settings.agent_memory_window_k}")
    print(f"Web Reader Timeout: {settings.tool_web_reader_timeout}")
    print(f"Available Ollama: {settings.ollama_available_models}")
    print("-------------------------------\n")