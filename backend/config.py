import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logging.basicConfig(level=logging.INFO) # Basic config set early
logger = logging.getLogger(__name__)

def parse_comma_separated_list(env_var: Optional[str], default: Optional[List[str]] = None) -> List[str]:
    """Parses a comma-separated string from env var into a list, cleaning prefixes."""
    if env_var:
        cleaned_list = []
        for item in env_var.split(','):
            item = item.strip()
            if item:
                # Remove potential provider prefix like "gemini::" or "ollama::"
                if "::" in item:
                    item = item.split("::", 1)[1]
                cleaned_list.append(item)
        return cleaned_list
    return default if default is not None else []

@dataclass
class Settings:
    """Holds application configuration settings loaded from environment variables."""

    # --- Required API Keys ---
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv('GOOGLE_API_KEY'))
    entrez_email: Optional[str] = field(default_factory=lambda: os.getenv('ENTREZ_EMAIL'))

    # --- Core LLM Configuration ---
    default_llm_id: str = field(default_factory=lambda: os.getenv('DEFAULT_LLM_ID', 'gemini::gemini-1.5-flash-latest'))
    
    # --- Role-Specific LLM Configuration (Raw Strings from Env) ---
    _intent_classifier_llm_id_str: Optional[str] = field(default_factory=lambda: os.getenv('INTENT_CLASSIFIER_LLM_ID'))
    _planner_llm_id_str: Optional[str] = field(default_factory=lambda: os.getenv('PLANNER_LLM_ID'))
    _controller_llm_id_str: Optional[str] = field(default_factory=lambda: os.getenv('CONTROLLER_LLM_ID'))
    _executor_default_llm_id_str: Optional[str] = field(default_factory=lambda: os.getenv('EXECUTOR_DEFAULT_LLM_ID'))
    _evaluator_llm_id_str: Optional[str] = field(default_factory=lambda: os.getenv('EVALUATOR_LLM_ID'))

    ollama_base_url: str = field(default_factory=lambda: os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
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
    tool_pdf_reader_warning_length: int = field(default_factory=lambda: int(os.getenv('TOOL_PDF_READER_WARNING_LENGTH', '20000')))

    # --- Server Settings ---
    websocket_max_size_bytes: int = field(default_factory=lambda: int(os.getenv('WEBSOCKET_MAX_SIZE_BYTES', '16777216')))
    websocket_ping_interval: int = field(default_factory=lambda: int(os.getenv('WEBSOCKET_PING_INTERVAL', '20')))
    websocket_ping_timeout: int = field(default_factory=lambda: int(os.getenv('WEBSOCKET_PING_TIMEOUT', '30')))
    direct_command_timeout: int = field(default_factory=lambda: int(os.getenv('DIRECT_COMMAND_TIMEOUT', '120')))
    file_server_hostname: str = field(default_factory=lambda: os.getenv('FILE_SERVER_HOSTNAME', 'localhost'))
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO').upper())

    # --- Parsed/Derived values (not directly from env for roles) ---
    # Default (fallback)
    default_provider: str = field(init=False)
    default_model_name: str = field(init=False)
    # Role-specific parsed values
    intent_classifier_provider: str = field(init=False)
    intent_classifier_model_name: str = field(init=False)
    planner_provider: str = field(init=False)
    planner_model_name: str = field(init=False)
    controller_provider: str = field(init=False)
    controller_model_name: str = field(init=False)
    executor_default_provider: str = field(init=False) # Default for executor if not UI selected
    executor_default_model_name: str = field(init=False)
    evaluator_provider: str = field(init=False)
    evaluator_model_name: str = field(init=False)


    def _parse_llm_id(self, llm_id_str: Optional[str], role_name_for_log: str, 
                        fallback_provider: str, fallback_model_name: str) -> Tuple[str, str]:
        """
        Helper to parse an LLM ID string (provider::model_name) and handle fallbacks.
        Logs which LLM is being used for the role.
        """
        if not llm_id_str or not llm_id_str.strip(): # Handles None or empty string
            logger.info(f"{role_name_for_log} LLM not set or empty, falling back to default: {fallback_provider}::{fallback_model_name}")
            return fallback_provider, fallback_model_name
        
        try:
            provider, model_name = llm_id_str.split("::", 1)
            if provider not in ['gemini', 'ollama'] or not model_name:
                raise ValueError("Invalid format or missing components.")
            
            # Validate if the model is in the available lists for its provider
            is_available = False
            if provider == 'gemini' and model_name in self.gemini_available_models:
                is_available = True
            elif provider == 'ollama' and model_name in self.ollama_available_models:
                is_available = True
            
            if is_available:
                logger.info(f"Using {role_name_for_log} LLM: {provider}::{model_name}")
                return provider, model_name
            else:
                logger.warning(f"{role_name_for_log} LLM '{llm_id_str}' not found in available models. Falling back to default: {fallback_provider}::{fallback_model_name}")
                return fallback_provider, fallback_model_name
        except ValueError:
            logger.warning(f"Invalid format for {role_name_for_log} LLM ID: '{llm_id_str}'. Expected 'provider::model_name'. Falling back to default: {fallback_provider}::{fallback_model_name}")
            return fallback_provider, fallback_model_name

    def __post_init__(self):
        """Validate settings and parse derived values after initialization."""
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.warning(f"Invalid LOG_LEVEL '{self.log_level}', defaulting to INFO.")
            self.log_level = "INFO"

        # Parse available models first, as they are needed for validation
        self.gemini_available_models = parse_comma_separated_list(self._gemini_available_models_str, default=['gemini-1.5-flash-latest'])
        self.ollama_available_models = parse_comma_separated_list(self._ollama_available_models_str, default=['llama3:latest'])

        # Parse Default LLM ID (this is the ultimate fallback)
        try:
            provider, model_name = self.default_llm_id.split("::", 1)
            if provider not in ['gemini', 'ollama'] or not model_name:
                raise ValueError("Invalid format for DEFAULT_LLM_ID.")
            
            # Check if default is available
            default_is_available = False
            if provider == 'gemini' and model_name in self.gemini_available_models:
                default_is_available = True
            elif provider == 'ollama' and model_name in self.ollama_available_models:
                default_is_available = True
            
            if not default_is_available:
                logger.error(f"FATAL: DEFAULT_LLM_ID '{self.default_llm_id}' is not listed in GEMINI_AVAILABLE_MODELS or OLLAMA_AVAILABLE_MODELS. Check .env.")
                # Attempt a hardcoded fallback if even the configured default is bad
                if self.gemini_available_models:
                    self.default_provider = 'gemini'
                    self.default_model_name = self.gemini_available_models[0]
                    logger.warning(f"Hardcoding fallback DEFAULT_LLM_ID to gemini::{self.default_model_name}")
                elif self.ollama_available_models:
                    self.default_provider = 'ollama'
                    self.default_model_name = self.ollama_available_models[0]
                    logger.warning(f"Hardcoding fallback DEFAULT_LLM_ID to ollama::{self.default_model_name}")
                else:
                    # This is a critical failure, no models available at all
                    logger.critical("FATAL: No available models configured for Gemini or Ollama, and DEFAULT_LLM_ID is invalid. Application cannot proceed.")
                    raise ValueError("No valid LLMs configured.")
            else:
                self.default_provider = provider
                self.default_model_name = model_name
        except ValueError as e:
            logger.error(f"FATAL: Invalid DEFAULT_LLM_ID format: '{self.default_llm_id}'. Error: {e}. Application cannot proceed without a valid default LLM.")
            raise # Re-raise to stop application startup if default is critically misconfigured

        # --- Parse Role-Specific LLMs with Fallback to Default ---
        logger.info("--- Effective LLM Configuration for Roles ---")
        self.intent_classifier_provider, self.intent_classifier_model_name = self._parse_llm_id(
            self._intent_classifier_llm_id_str, "Intent Classifier", self.default_provider, self.default_model_name
        )
        self.planner_provider, self.planner_model_name = self._parse_llm_id(
            self._planner_llm_id_str, "Planner", self.default_provider, self.default_model_name
        )
        self.controller_provider, self.controller_model_name = self._parse_llm_id(
            self._controller_llm_id_str, "Controller", self.default_provider, self.default_model_name
        )
        self.executor_default_provider, self.executor_default_model_name = self._parse_llm_id(
            self._executor_default_llm_id_str, "Executor Default", self.default_provider, self.default_model_name
        )
        self.evaluator_provider, self.evaluator_model_name = self._parse_llm_id(
            self._evaluator_llm_id_str, "Evaluator", self.default_provider, self.default_model_name
        )
        logger.info("---------------------------------------------")

        # Validate Gemini Key if any Gemini model is effectively in use
        is_gemini_needed_for_roles = any(p == 'gemini' for p in [
            self.default_provider, self.intent_classifier_provider, self.planner_provider,
            self.controller_provider, self.executor_default_provider, self.evaluator_provider
        ])
        if is_gemini_needed_for_roles and not self.google_api_key:
            logger.error("A Gemini model is configured for use, but GOOGLE_API_KEY is not set. Application may fail.")

        if not self.entrez_email:
            logger.warning("ENTREZ_EMAIL is not set. PubMed search tool functionality will be limited or blocked by NCBI.")

        # Log loaded configuration (summary)
        logger.info("--- General Configuration Summary ---")
        logger.info(f"System Default LLM ID (Fallback): {self.default_provider}::{self.default_model_name}")
        logger.info(f"Google API Key Loaded: {'Yes' if self.google_api_key else 'No'}")
        logger.info(f"Entrez Email Set: {'Yes' if self.entrez_email else 'No (PubMed tool potentially disabled)'}")
        logger.info(f"Ollama Base URL: {self.ollama_base_url}")
        logger.info(f"Available Gemini Models (UI): {self.gemini_available_models}")
        logger.info(f"Available Ollama Models (UI): {self.ollama_available_models}")
        # ... (other logs can be added if needed, role-specific LLMs are logged above)
        logger.info(f"Log Level: {self.log_level}")
        logger.info("-----------------------------------")


def load_settings() -> Settings:
    """Loads settings from .env file and environment variables."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        logger.info(f"Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        logger.info(f".env file not found at expected location ({env_path}), loading from environment variables only.")
    try:
        return Settings()
    except (ValueError, TypeError) as e:
        logger.error(f"Error creating Settings object from environment variables: {e}", exc_info=True)
        logger.error("Please check your .env file or environment variables for correct formats (numbers, floats).")
        raise ValueError(f"Configuration Error: {e}") from e

settings = load_settings()

if __name__ == "__main__":
    print("\n--- Configuration Test Access ---")
    print(f"Default Provider: {settings.default_provider}, Model: {settings.default_model_name}")
    print(f"Intent Classifier: {settings.intent_classifier_provider}::{settings.intent_classifier_model_name}")
    print(f"Planner: {settings.planner_provider}::{settings.planner_model_name}")
    print(f"Controller: {settings.controller_provider}::{settings.controller_model_name}")
    print(f"Executor Default: {settings.executor_default_provider}::{settings.executor_default_model_name}")
    print(f"Evaluator: {settings.evaluator_provider}::{settings.evaluator_model_name}")
    print("-------------------------------\n")
