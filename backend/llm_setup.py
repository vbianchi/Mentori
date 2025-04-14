# backend/llm_setup.py
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain_core.language_models.chat_models import BaseChatModel # For type hinting
from backend.config import Settings

logger = logging.getLogger(__name__)

def get_llm(settings: Settings) -> BaseChatModel:
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
                # Adjust temperature, top_p etc. as needed
                temperature=0.7,
                # Consider safety settings if default is too restrictive
                # convert_system_message_to_human=True # Sometimes needed depending on model/task
            )
            logger.info(f"Initialized ChatGoogleGenerativeAI with model: {settings.gemini_model_name}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Gemini LLM: {e}") from e

    elif provider == "ollama":
        try:
            llm = Ollama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model_name,
                # Adjust temperature, top_k, etc. as needed
                temperature=0.5,
            )
            # Optional: Add a quick check to see if Ollama is reachable
            # try:
            #     llm.invoke("Hi") # Simple test invocation
            # except Exception as ollama_e:
            #      logger.error(f"Failed to connect/invoke Ollama at {settings.ollama_base_url} with model {settings.ollama_model_name}: {ollama_e}")
            #      raise ConnectionError(f"Failed to connect to Ollama: {ollama_e}") from ollama_e

            logger.info(f"Initialized Ollama LLM: Model='{settings.ollama_model_name}', URL='{settings.ollama_base_url}'")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Ollama LLM: {e}") from e

    else:
        logger.error(f"Unsupported AI_PROVIDER: {provider}")
        raise ValueError(f"Unsupported AI_PROVIDER configured: {provider}")

