import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaLLM 
# from langchain_community.chat_models.ollama import ChatOllama # If you switch to ChatOllama
from langchain_core.language_models.base import BaseLanguageModel
from backend.config import Settings # Import Settings class

logger = logging.getLogger(__name__)

def get_llm(settings: Settings, provider: str, model_name: str, is_fallback_attempt: bool = False) -> BaseLanguageModel:
    """
    Initializes and returns the appropriate LangChain LLM wrapper.
    If the initial attempt fails and it's not already a fallback attempt,
    it will try to initialize using the system's default LLM settings.

    Args:
        settings: The application settings object.
        provider: The primary LLM provider for this attempt (e.g., 'gemini', 'ollama').
        model_name: The primary LLM model name for this attempt.
        is_fallback_attempt: Internal flag to prevent recursive fallbacks.

    Returns:
        An instance of BaseLanguageModel.

    Raises:
        ValueError: If an unsupported provider is requested.
        ConnectionError: If LLM initialization fails even after fallback.
    """
    logger.info(f"Attempting to initialize LLM: Provider='{provider}', Model='{model_name}'" + (" (Fallback to system default)" if is_fallback_attempt else ""))

    try:
        if provider == "gemini":
            if not settings.google_api_key:
                logger.error("Cannot initialize Gemini LLM: GOOGLE_API_KEY is not set.")
                raise ValueError("GOOGLE_API_KEY is required for Gemini provider.")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature,
            )
            logger.info(f"Successfully initialized ChatGoogleGenerativeAI: Model='{model_name}', Temp='{settings.gemini_temperature}'")
            return llm
        
        elif provider == "ollama":
            # Using OllamaLLM (base LLM). If you switch to ChatOllama, adjust instantiation.
            llm = OllamaLLM(
                base_url=settings.ollama_base_url,
                model=model_name,
                temperature=settings.ollama_temperature,
            )
            logger.info(f"Successfully initialized OllamaLLM: Model='{model_name}', URL='{settings.ollama_base_url}', Temp='{settings.ollama_temperature}'")
            return llm
        
        else:
            logger.error(f"Unsupported LLM provider requested: {provider}")
            raise ValueError(f"Unsupported LLM provider requested: {provider}")

    except Exception as e:
        logger.warning(f"Failed to initialize LLM '{provider}::{model_name}': {e}")
        if not is_fallback_attempt:
            logger.warning(f"Attempting fallback to system default LLM: {settings.default_provider}::{settings.default_model_name}")
            try:
                # Recursive call for fallback, ensuring is_fallback_attempt is True
                return get_llm(settings, settings.default_provider, settings.default_model_name, is_fallback_attempt=True)
            except Exception as fallback_e:
                logger.error(f"Fallback LLM initialization failed: {fallback_e}", exc_info=True)
                raise ConnectionError(f"Failed to initialize both primary LLM ('{provider}::{model_name}') and fallback LLM ('{settings.default_provider}::{settings.default_model_name}'). Original error: {e}. Fallback error: {fallback_e}") from fallback_e
        else:
            # This means the fallback attempt itself failed
            logger.error(f"Fallback LLM initialization for '{provider}::{model_name}' also failed: {e}", exc_info=True)
            raise ConnectionError(f"Fallback LLM initialization failed for '{provider}::{model_name}': {e}") from e

