# backend/llm_setup.py
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaLLM # Corrected import if using OllamaLLM directly
# If using ChatOllama, import that instead:
# from langchain_community.chat_models.ollama import ChatOllama
from langchain_core.language_models.base import BaseLanguageModel
from backend.config import Settings # Import Settings class

logger = logging.getLogger(__name__)

# *** MODIFIED: Accepts provider and model_name ***
def get_llm(settings: Settings, provider: str, model_name: str) -> BaseLanguageModel:
    """Initializes and returns the appropriate LangChain LLM wrapper based on arguments."""
    logger.info(f"Initializing LangChain LLM for provider: {provider}, model: {model_name}")

    if provider == "gemini":
        if not settings.google_api_key:
            logger.error("Cannot initialize Gemini LLM: GOOGLE_API_KEY is not set.")
            raise ValueError("GOOGLE_API_KEY is required for Gemini provider.")
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name, # Use passed model_name
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature, # Use temperature from settings
                # convert_system_message_to_human=True # Consider if needed based on prompt/model behavior
            )
            logger.info(f"Initialized ChatGoogleGenerativeAI with model: {model_name} (Temp: {settings.gemini_temperature})")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM ({model_name}): {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Gemini LLM: {e}") from e

    elif provider == "ollama":
        try:
            # Using OllamaLLM (base LLM)
            llm = OllamaLLM(
                base_url=settings.ollama_base_url,
                model=model_name, # Use passed model_name
                temperature=settings.ollama_temperature, # Use temperature from settings
            )
            logger.info(f"Initialized OllamaLLM: Model='{model_name}', URL='{settings.ollama_base_url}' (Temp: {settings.ollama_temperature})")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM ({model_name}): {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Ollama LLM: {e}") from e

    else:
        logger.error(f"Unsupported LLM provider requested: {provider}")
        raise ValueError(f"Unsupported LLM provider requested: {provider}")