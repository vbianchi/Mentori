# backend/agents/preload_manager.py
"""
PreloadManager handles automatic model preloading at application startup.

This ensures that configured models are loaded into Ollama memory before
any user requests arrive, providing fast response times for the first query.
"""
import logging
from typing import List, Dict, Any
from backend.agents.models.ollama import OllamaClient
from backend.config import settings

logger = logging.getLogger(__name__)


class PreloadManager:
    """
    Manages automatic preloading of Ollama models at application startup.

    Reads the preloaded_models list from SystemSettings and loads each
    model with keep_alive=-1 (indefinite).
    """

    def __init__(self):
        self.ollama = OllamaClient()
        self._preload_results: List[Dict[str, Any]] = []

    async def startup_preload(self) -> List[Dict[str, Any]]:
        """
        Called during app startup to preload configured models.

        Reads from SystemSettings table and preloads each model.
        Runs in background (non-blocking) via asyncio.create_task().

        Returns:
            List of preload results with status per model
        """
        from sqlmodel import Session, select
        from backend.database import engine
        from backend.models.system_settings import SystemSettings

        # Check if Ollama is available
        if not await self.ollama.check_health():
            logger.warning("Ollama not available, skipping model preload")
            return []

        # Get preload list from SystemSettings
        with Session(engine) as session:
            setting = session.exec(
                select(SystemSettings).where(SystemSettings.key == "preloaded_models")
            ).first()

            if not setting or not setting.value:
                logger.info("No preloaded_models configured, skipping preload")
                return []

            # Handle both list format and dict with "models" key
            preload_config = setting.value
            if isinstance(preload_config, list):
                models = preload_config
            elif isinstance(preload_config, dict):
                models = preload_config.get("models", [])
            else:
                logger.warning(f"Unexpected preloaded_models format: {type(preload_config)}")
                return []

        if not models:
            logger.info("Preloaded models list is empty")
            return []

        logger.info(f"Starting preload of {len(models)} models: {models}")
        results = []

        for model_id in models:
            # Extract model name from "ollama::model" format
            if "::" in model_id:
                _, model_name = model_id.split("::", 1)
            else:
                model_name = model_id

            logger.info(f"Preloading model: {model_name}")
            result = await self.ollama.preload_model(model_name, keep_alive="-1")
            results.append(result)

            if result["status"] == "loaded":
                logger.info(f"Successfully preloaded: {model_name}")
            else:
                logger.warning(f"Failed to preload {model_name}: {result.get('error')}")

        self._preload_results = results
        loaded_count = sum(1 for r in results if r["status"] == "loaded")
        logger.info(f"Preload complete: {loaded_count}/{len(models)} models loaded")

        return results

    def get_last_preload_results(self) -> List[Dict[str, Any]]:
        """Get results from the most recent preload operation."""
        return self._preload_results


# Singleton instance for use in main.py
preload_manager = PreloadManager()
