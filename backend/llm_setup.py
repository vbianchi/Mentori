# backend/llm_setup.py
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
# *** CORRECTED IMPORT and CLASS NAME: Use OllamaLLM ***
from langchain_ollama import OllamaLLM
# from langchain_community.llms import Ollama # Old import removed
from langchain_core.language_models.base import BaseLanguageModel
from backend.config import Settings

logger = logging.getLogger(__name__)

def get_llm(settings: Settings) -> BaseLanguageModel: # Use BaseLanguageModel for broader compatibility
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
                # convert_system_message_to_human=True # Might be needed for some prompts/models
            )
            logger.info(f"Initialized ChatGoogleGenerativeAI with model: {settings.gemini_model_name}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Gemini LLM: {e}") from e

    elif provider == "ollama":
        try:
            # *** Use the corrected class name OllamaLLM ***
            llm = OllamaLLM(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model_name,
                temperature=0.5,
                # Add other parameters like num_ctx, top_k, top_p if needed
                # num_ctx=4096 # Example context window
            )
            logger.info(f"Initialized OllamaLLM: Model='{settings.ollama_model_name}', URL='{settings.ollama_base_url}'")
            # Optional: Add a quick check here if needed, but the agent call will test it
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize Ollama LLM: {e}") from e

    else:
        logger.error(f"Unsupported AI_PROVIDER: {provider}")
        raise ValueError(f"Unsupported AI_PROVIDER configured: {provider}")

