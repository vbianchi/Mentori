# backend/llm_setup.py
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaLLM # Corrected import if using OllamaLLM directly
# If using ChatOllama, import that instead:
# from langchain_community.chat_models.ollama import ChatOllama
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
                # Removed 'streaming=True' as it caused warnings and streaming
                # is typically handled by the invoke/stream methods.
                # Alternatively, set disable_streaming=False if needed.
                # convert_system_message_to_human=True # Consider if needed based on prompt/model behavior
            )
            # Updated log message
            logger.info(f"Initialized ChatGoogleGenerativeAI with model: {settings.gemini_model_name} (Streaming enabled via astream/ainvoke)")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}", exc_info=True)
            # Wrap in a more specific error if possible, e.g., ConnectionError
            raise ConnectionError(f"Failed to initialize Gemini LLM: {e}") from e

    elif provider == "ollama":
        try:
            # Use ChatOllama for chat-based interactions if preferred
            # from langchain_community.chat_models.ollama import ChatOllama
            # llm = ChatOllama(...)

            # Using OllamaLLM (base LLM)
            llm = OllamaLLM(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model_name,
                temperature=0.5,
                # Ollama wrapper doesn't have a top-level 'streaming' param usually.
                # Streaming is handled by using .astream() or .ainvoke() methods.
            )
            logger.info(f"Initialized OllamaLLM: Model='{settings.ollama_model_name}', URL='{settings.ollama_base_url}' (Streaming enabled via astream/ainvoke)")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Ollama LLM: {e}") from e

    else:
        logger.error(f"Unsupported AI_PROVIDER: {provider}")
        raise ValueError(f"Unsupported AI_PROVIDER configured: {provider}")

