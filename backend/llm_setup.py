# backend/llm_setup.py
import logging
# <<< START MODIFICATION - Import List and BaseCallbackHandler >>>
from typing import Optional, List 
from langchain_core.callbacks.base import BaseCallbackHandler
# <<< END MODIFICATION >>>
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaLLM # Corrected class name
from langchain_core.language_models.base import BaseLanguageModel
from backend.config import Settings 

logger = logging.getLogger(__name__)

def get_llm(
    settings: Settings, 
    provider: str, 
    model_name: str, 
    is_fallback_attempt: bool = False, 
    requested_for_role: Optional[str] = None,
    # <<< START MODIFICATION - Add callbacks parameter >>>
    callbacks: Optional[List[BaseCallbackHandler]] = None 
    # <<< END MODIFICATION >>>
) -> BaseLanguageModel:
    """
    Initializes and returns the appropriate LangChain LLM wrapper.
    If the initial attempt fails and it's not already a fallback attempt,
    it will try to initialize using the system's default LLM settings.
    Now accepts an optional list of callbacks to pass to the LLM constructor.
    """
    role_context = f" for role '{requested_for_role}'" if requested_for_role else ""
    attempt_type = " (Fallback to system default)" if is_fallback_attempt else ""
    logger.info(f"Attempting to initialize LLM{role_context}: Provider='{provider}', Model='{model_name}'{attempt_type}")
    if callbacks:
        logger.debug(f"get_llm received callbacks: {[type(cb).__name__ for cb in callbacks]}")

    try:
        if provider == "gemini":
            if not settings.google_api_key:
                logger.error(f"Cannot initialize Gemini LLM{role_context}: GOOGLE_API_KEY is not set.")
                raise ValueError(f"GOOGLE_API_KEY is required for Gemini provider{role_context}.")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature,
                # <<< START MODIFICATION - Pass callbacks to constructor >>>
                callbacks=callbacks
                # <<< END MODIFICATION >>>
            )
            logger.info(f"Successfully initialized ChatGoogleGenerativeAI{role_context}: Model='{model_name}', Temp='{settings.gemini_temperature}'")
            return llm

        elif provider == "ollama":
            llm = OllamaLLM( # Corrected class name
                base_url=settings.ollama_base_url,
                model=model_name,
                temperature=settings.ollama_temperature,
                # <<< START MODIFICATION - Pass callbacks to constructor >>>
                callbacks=callbacks
                # <<< END MODIFICATION >>>
            )
            logger.info(f"Successfully initialized OllamaLLM{role_context}: Model='{model_name}', URL='{settings.ollama_base_url}', Temp='{settings.ollama_temperature}'")
            return llm

        else:
            logger.error(f"Unsupported LLM provider requested{role_context}: {provider}")
            raise ValueError(f"Unsupported LLM provider requested{role_context}: {provider}")

    except Exception as e:
        logger.warning(f"Failed to initialize LLM '{provider}::{model_name}'{role_context}: {e}")
        if not is_fallback_attempt:
            fallback_role_context = f" (originally for role '{requested_for_role}')" if requested_for_role else ""
            logger.warning(f"Attempting fallback to system default LLM: {settings.default_provider}::{settings.default_model_name}{fallback_role_context}")
            try:
                # When falling back, do not pass the original component's callbacks, 
                # as the fallback is a general system action.
                return get_llm(settings, settings.default_provider, settings.default_model_name, is_fallback_attempt=True, requested_for_role=f"System Default Fallback (was for {requested_for_role or 'Unknown Role'})", callbacks=None)
            except Exception as fallback_e:
                logger.error(f"Fallback LLM initialization failed{fallback_role_context}: {fallback_e}", exc_info=True)
                raise ConnectionError(f"Failed to initialize both primary LLM ('{provider}::{model_name}'{role_context}) and fallback LLM ('{settings.default_provider}::{settings.default_model_name}'). Original error: {e}. Fallback error: {fallback_e}") from fallback_e
        else:
            logger.error(f"Fallback LLM initialization for '{provider}::{model_name}'{role_context} also failed: {e}", exc_info=True)
            raise ConnectionError(f"Fallback LLM initialization failed for '{provider}::{model_name}'{role_context}: {e}") from e

