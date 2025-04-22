# backend/llm_setup.py
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaLLM
from langchain_core.language_models.base import BaseLanguageModel
from backend.config import Settings

logger = logging.getLogger(__name__)

def get_llm(settings: Settings) -> BaseLanguageModel:
    """Initializes and returns the appropriate LangChain LLM wrapper."""
    provider = settings.ai_provider
    logger.info(f"Initializing LangChain LLM for provider: {provider}")

    if provider == "gemini":
        if not settings.google_api_key:
            logger.error("Cannot initialize Gemini LLM: GOOGLE_API_KEY is not set.")
            raise ValueError("GOOGLE_API_KEY is required for Gemini provider.")
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model_name,
                google_api_key=settings.google_api_key,
                temperature=0.7,
                streaming=True, # Explicitly enable streaming
                # convert_system_message_to_human=True # Might be needed for some prompts/models
            )
            logger.info(f"Initialized ChatGoogleGenerativeAI with model: {settings.gemini_model_name} (Streaming enabled)")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Gemini LLM: {e}") from e

    elif provider == "ollama":
        try:
            # Ollama wrapper might handle streaming implicitly via methods,
            # but check documentation if specific param is needed.
            # For now, assume astream method enables it.
            llm = OllamaLLM(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model_name,
                temperature=0.5,
                # Ollama doesn't have a top-level 'streaming' param in constructor usually
            )
            logger.info(f"Initialized OllamaLLM: Model='{settings.ollama_model_name}', URL='{settings.ollama_base_url}' (Streaming enabled via astream)")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Ollama LLM: {e}") from e

    else:
        logger.error(f"Unsupported AI_PROVIDER: {provider}")
        raise ValueError(f"Unsupported AI_PROVIDER configured: {provider}")

