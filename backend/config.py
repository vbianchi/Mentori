import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper()) # Basic config set early, respects LOG_LEVEL from env
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
        if cleaned_list:
            return cleaned_list
    return default if default is not None else []

@dataclass
class Settings:
    """Holds application configuration settings loaded from environment variables."""

    # --- Required API Keys ---
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv('GOOGLE_API_KEY'))
    entrez_email: Optional[str] = field(default_factory=lambda: os.getenv('ENTREZ_EMAIL'))
    tavily_api_key: Optional[str] = field(default_factory=lambda: os.getenv('TAVILY_API_KEY'))

    # --- Core LLM Configuration ---
    default_llm_id: str = field(default_factory=lambda: os.getenv('DEFAULT_LLM_ID', 'gemini::gemini-1.5-flash'))
    
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
    # --- ADDED: agent_max_step_retries ---
    agent_max_step_retries: int = field(default_factory=lambda: int(os.getenv('AGENT_MAX_STEP_RETRIES', '1')))
    # --- END ADDED ---
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
    default_provider: str = field(init=False)
    default_model_name: str = field(init=False)
    intent_classifier_provider: str = field(init=False)
    intent_classifier_model_name: str = field(init=False)
    planner_provider: str = field(init=False)
    planner_model_name: str = field(init=False)
    controller_provider: str = field(init=False)
    controller_model_name: str = field(init=False)
    executor_default_provider: str = field(init=False)
    executor_default_model_name: str = field(init=False)
    evaluator_provider: str = field(init=False)
    evaluator_model_name: str = field(init=False)


    def _parse_llm_id(self, llm_id_str: Optional[str], role_name_for_log: str, 
                        fallback_provider: str, fallback_model_name: str) -> Tuple[str, str]:
        """
        Helper to parse an LLM ID string (provider::model_name) and handle fallbacks.
        Logs which LLM is being used for the role.
        Validates against available models if provider and model are recognized.
        """
        chosen_id_str = llm_id_str if llm_id_str and llm_id_str.strip() else None
        
        if not chosen_id_str:
            logger.info(f"{role_name_for_log} LLM not set or empty, falling back to default: {fallback_provider}::{fallback_model_name}")
            return fallback_provider, fallback_model_name
        
        try:
            provider, model_name = chosen_id_str.split("::", 1)
            if not provider or not model_name: # Ensure both parts are non-empty
                raise ValueError("Provider or model name missing in ID.")

            is_available = False
            if provider == 'gemini':
                if model_name in self.gemini_available_models:
                    is_available = True
                elif not self.gemini_available_models: 
                    logger.warning(f"GEMINI_AVAILABLE_MODELS list is empty. Cannot validate Gemini model '{model_name}' for {role_name_for_log}. Proceeding with caution.")
                    is_available = True 
            elif provider == 'ollama':
                if model_name in self.ollama_available_models:
                    is_available = True
                elif not self.ollama_available_models:
                    logger.warning(f"OLLAMA_AVAILABLE_MODELS list is empty. Cannot validate Ollama model '{model_name}' for {role_name_for_log}. Proceeding with caution.")
                    is_available = True 
            else:
                logger.warning(f"Unknown provider '{provider}' for {role_name_for_log} LLM ID: '{chosen_id_str}'. Falling back.")
                return fallback_provider, fallback_model_name

            if is_available:
                return provider, model_name
            else:
                logger.warning(f"{role_name_for_log} LLM '{chosen_id_str}' not found in its provider's available models list. Falling back to default: {fallback_provider}::{fallback_model_name}")
                return fallback_provider, fallback_model_name
        except ValueError as e:
            logger.warning(f"Invalid format for {role_name_for_log} LLM ID: '{chosen_id_str}'. Error: {e}. Expected 'provider::model_name'. Falling back to default: {fallback_provider}::{fallback_model_name}")
            return fallback_provider, fallback_model_name

    def __post_init__(self):
        """Validate settings and parse derived values after initialization."""
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.warning(f"Invalid LOG_LEVEL '{self.log_level}', defaulting to INFO.")
            self.log_level = "INFO"
        
        logging.getLogger().setLevel(self.log_level)
        logging.getLogger("backend").setLevel(self.log_level) 

        self.gemini_available_models = parse_comma_separated_list(self._gemini_available_models_str, default=['gemini-1.5-flash'])
        self.ollama_available_models = parse_comma_separated_list(self._ollama_available_models_str, default=['llama3:latest'])

        try:
            provider, model_name = self.default_llm_id.split("::", 1)
            if not provider or not model_name: raise ValueError("Default LLM ID provider or model_name is empty.")
            
            default_is_available = False
            if provider == 'gemini' and model_name in self.gemini_available_models: default_is_available = True
            elif provider == 'ollama' and model_name in self.ollama_available_models: default_is_available = True
            elif provider == 'gemini' and not self.gemini_available_models: 
                logger.warning(f"GEMINI_AVAILABLE_MODELS list is empty. Assuming DEFAULT_LLM_ID '{self.default_llm_id}' is valid.")
                default_is_available = True
            elif provider == 'ollama' and not self.ollama_available_models: 
                logger.warning(f"OLLAMA_AVAILABLE_MODELS list is empty. Assuming DEFAULT_LLM_ID '{self.default_llm_id}' is valid.")
                default_is_available = True

            if not default_is_available:
                logger.error(f"FATAL: DEFAULT_LLM_ID '{self.default_llm_id}' is not listed in its provider's AVAILABLE_MODELS list. Check .env.")
                if self.gemini_available_models:
                    self.default_provider = 'gemini'
                    self.default_model_name = self.gemini_available_models[0]
                    logger.warning(f"Hardcoding ultimate fallback DEFAULT_LLM to gemini::{self.default_model_name}")
                elif self.ollama_available_models:
                    self.default_provider = 'ollama'
                    self.default_model_name = self.ollama_available_models[0]
                    logger.warning(f"Hardcoding ultimate fallback DEFAULT_LLM to ollama::{self.default_model_name}")
                else:
                    logger.critical("FATAL: No available models configured for Gemini or Ollama, and DEFAULT_LLM_ID is invalid. Application cannot proceed.")
                    raise ValueError("No valid LLMs configured and DEFAULT_LLM_ID is also invalid or unavailable.")
            else:
                self.default_provider = provider
                self.default_model_name = model_name
        except ValueError as e:
            logger.critical(f"FATAL: Invalid DEFAULT_LLM_ID format: '{self.default_llm_id}'. Error: {e}. Application cannot proceed.")
            raise

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

        if any(p == 'gemini' for p in [
            self.default_provider, self.intent_classifier_provider, self.planner_provider,
            self.controller_provider, self.executor_default_provider, self.evaluator_provider
        ]) and not self.google_api_key:
            logger.warning("A Gemini model is configured for use, but GOOGLE_API_KEY is not set. Application may fail when trying to use Gemini.")

        if not self.entrez_email:
            logger.warning("ENTREZ_EMAIL is not set. PubMed search tool functionality will be limited or blocked by NCBI.")
        
        if not self.tavily_api_key and any(tool_name == "tavily_search_results_json" for tool_name in os.getenv("ENABLED_TOOLS","").split(",")): 
             logger.warning("TAVILY_API_KEY is not set, but Tavily search might be an intended tool. Functionality will be impaired.")


        logger.info("--- General Configuration Summary ---")
        logger.info(f"System Default LLM ID (Fallback): {self.default_provider}::{self.default_model_name}")
        logger.info(f"Google API Key Loaded: {'Yes' if self.google_api_key else 'No'}")
        logger.info(f"Tavily API Key Loaded: {'Yes' if self.tavily_api_key else 'No'}")
        logger.info(f"Entrez Email Set: {'Yes' if self.entrez_email else 'No (PubMed tool potentially disabled)'}")
        logger.info(f"Ollama Base URL: {self.ollama_base_url}")
        logger.info(f"Available Gemini Models (UI): {self.gemini_available_models}")
        logger.info(f"Available Ollama Models (UI): {self.ollama_available_models}")
        logger.info(f"Agent Max Iterations: {self.agent_max_iterations}")
        logger.info(f"Agent Max Step Retries: {self.agent_max_step_retries}") # Log the new setting
        logger.info(f"Log Level: {self.log_level}")
        logger.info("-----------------------------------")


def load_settings() -> Settings:
    """Loads settings from .env file and environment variables."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        logger.info(f"Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True) 
    else:
        logger.info(f".env file not found at expected location ({env_path}), loading from system environment variables only.")
    
    try:
        return Settings()
    except (ValueError, TypeError) as e:
        logger.critical(f"CRITICAL ERROR creating Settings object: {e}. This usually indicates a problem with .env parsing or type conversion for default values.", exc_info=True)
        logger.critical("Please check your .env file for correct formats (numbers, floats, boolean-like strings if parsed as such) or environment variable definitions.")
        raise SystemExit(f"Configuration Error: {e}") from e

settings = load_settings()

if __name__ == "__main__":
    print("\n--- Configuration Test Access ---")
    print(f"Default Provider: {settings.default_provider}, Model: {settings.default_model_name}")
    print(f"Intent Classifier: {settings.intent_classifier_provider}::{settings.intent_classifier_model_name}")
    print(f"Planner: {settings.planner_provider}::{settings.planner_model_name}")
    print(f"Controller: {settings.controller_provider}::{settings.controller_model_name}")
    print(f"Executor Default: {settings.executor_default_provider}::{settings.executor_default_model_name}")
    print(f"Evaluator: {settings.evaluator_provider}::{settings.evaluator_model_name}")
    print(f"Tavily API Key set: {'Yes' if settings.tavily_api_key else 'No'}")
    print(f"Agent Max Iterations: {settings.agent_max_iterations}")
    print(f"Agent Max Step Retries: {settings.agent_max_step_retries}") # Test print
    print("-------------------------------\n")

