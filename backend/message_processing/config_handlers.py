# backend/message_processing/config_handlers.py
import logging
from typing import Dict, Any, Callable, Coroutine

# Project Imports
from backend.config import settings # For default LLM settings and available models

logger = logging.getLogger(__name__)

# Type Hints for Passed-in Functions
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]


async def process_set_llm(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    llm_id = data.get("llm_id")
    if llm_id and isinstance(llm_id, str):
        try:
            provider, model_name_from_id = llm_id.split("::", 1)
            is_valid = False
            if provider == 'gemini' and model_name_from_id in settings.gemini_available_models:
                is_valid = True
            elif provider == 'ollama' and model_name_from_id in settings.ollama_available_models:
                is_valid = True

            if is_valid:
                session_data_entry["selected_llm_provider"] = provider
                session_data_entry["selected_llm_model_name"] = model_name_from_id
                logger.info(f"[{session_id}] Session LLM (for Executor/DirectQA) set to: {provider}::{model_name_from_id}")
                await add_monitor_log_func(f"Session LLM (for Executor/DirectQA) set to {provider}::{model_name_from_id}", "system_llm_set")
            else: # User selected an empty value (e.g. "Use System Default (Executor)") or invalid
                session_data_entry["selected_llm_provider"] = settings.executor_default_provider
                session_data_entry["selected_llm_model_name"] = settings.executor_default_model_name
                logger.info(f"[{session_id}] Session LLM (for Executor/DirectQA) reset to system default: {settings.executor_default_provider}::{settings.executor_default_model_name} due to invalid/empty selection: {llm_id}")
                await add_monitor_log_func(f"Session LLM (for Executor/DirectQA) reset to system default (invalid selection: {llm_id}).", "system_llm_set")

        except ValueError: # Handles if llm_id is not in "provider::model" format
            logger.warning(f"[{session_id}] Invalid LLM ID format in set_llm: {llm_id}. Resetting to executor default.")
            session_data_entry["selected_llm_provider"] = settings.executor_default_provider
            session_data_entry["selected_llm_model_name"] = settings.executor_default_model_name
            await add_monitor_log_func(f"Received invalid session LLM ID format: {llm_id}. Reset to default.", "error_llm_set")
    elif llm_id == "": # Explicitly chosen "Use System Default (Executor)"
        session_data_entry["selected_llm_provider"] = settings.executor_default_provider
        session_data_entry["selected_llm_model_name"] = settings.executor_default_model_name
        logger.info(f"[{session_id}] Session LLM (for Executor/DirectQA) explicitly set to system default: {settings.executor_default_provider}::{settings.executor_default_model_name}")
        await add_monitor_log_func(f"Session LLM (for Executor/DirectQA) set to system default.", "system_llm_set")
    else:
        logger.warning(f"[{session_id}] Received invalid 'set_llm' message content: {data}")


async def process_get_available_models(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    logger.info(f"[{session_id}] Received request for available models.")
    # These defaults are for UI display and initial selection guidance
    role_llm_defaults = {
        "intent_classifier": f"{settings.intent_classifier_provider}::{settings.intent_classifier_model_name}",
        "planner": f"{settings.planner_provider}::{settings.planner_model_name}",
        "controller": f"{settings.controller_provider}::{settings.controller_model_name}",
        "evaluator": f"{settings.evaluator_provider}::{settings.evaluator_model_name}",
    }
    await send_ws_message_func("available_models", {
        "gemini": settings.gemini_available_models,
        "ollama": settings.ollama_available_models,
        "default_executor_llm_id": f"{settings.executor_default_provider}::{settings.executor_default_model_name}",
        "role_llm_defaults": role_llm_defaults
    })

async def process_set_session_role_llm(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    role = data.get("role")
    llm_id_override = data.get("llm_id")

    if not role or role not in ["intent_classifier", "planner", "controller", "evaluator"]:
        logger.warning(f"[{session_id}] Invalid or missing 'role' in set_session_role_llm: {role}")
        await add_monitor_log_func(f"Error: Invalid role specified for LLM override: {role}", "error_system")
        return

    session_override_key = f"session_{role}_llm_id" # e.g., session_planner_llm_id

    if llm_id_override == "": # User selected "Use System Default"
        session_data_entry[session_override_key] = None # Clear the override
        logger.info(f"[{session_id}] Cleared session LLM override for role '{role}'. Will use system default.")
        await add_monitor_log_func(f"Session LLM for role '{role}' reset to system default.", "system_llm_set")
    elif llm_id_override and isinstance(llm_id_override, str):
        try:
            provider, model_name = llm_id_override.split("::", 1)
            is_valid = False
            # Validate against available models from settings
            if provider == 'gemini' and model_name in settings.gemini_available_models:
                is_valid = True
            elif provider == 'ollama' and model_name in settings.ollama_available_models:
                is_valid = True

            if is_valid:
                session_data_entry[session_override_key] = llm_id_override
                logger.info(f"[{session_id}] Session LLM override for role '{role}' set to: {llm_id_override}")
                await add_monitor_log_func(f"Session LLM for role '{role}' overridden to {llm_id_override}.", "system_llm_set")
            else: # Invalid/unavailable model selected
                logger.warning(f"[{session_id}] Attempt to set invalid/unavailable LLM ID '{llm_id_override}' for role '{role}'. Override not applied. Role will use system default.")
                session_data_entry[session_override_key] = None # Fallback to system default for this role
                await add_monitor_log_func(f"Attempt to set invalid LLM '{llm_id_override}' for role '{role}' ignored. Using system default for this role.", "error_llm_set")
        except ValueError: # llm_id was not in "provider::model" format
            logger.warning(f"[{session_id}] Invalid LLM ID format for role '{role}': {llm_id_override}. Override not applied. Role will use system default.")
            session_data_entry[session_override_key] = None # Fallback
            await add_monitor_log_func(f"Invalid LLM ID format for role '{role}': {llm_id_override}. Using system default for this role.", "error_llm_set")
    else:
        logger.warning(f"[{session_id}] Invalid 'llm_id' in set_session_role_llm for role '{role}': {llm_id_override}")
        # Potentially reset to default if llm_id is invalid type
        session_data_entry[session_override_key] = None
        await add_monitor_log_func(f"Invalid LLM ID type for role '{role}'. Using system default for this role.", "error_llm_set")

