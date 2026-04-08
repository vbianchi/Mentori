from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
import os
import aiohttp
import json

# Configure logging
logger = logging.getLogger(__name__)

class TranscriberAgent(ABC):
    """
    Abstract base class for the Transcriber Agent role.
    Responsible for converting visual documents (images) into structured Markdown.
    """
    
    @abstractmethod
    async def transcribe_page(self, image_path: str) -> str:
        """
        Transcribe a single page image into Markdown.
        
        Args:
            image_path: Absolute path to the image file.
            
        Returns:
            str: Markdown content describing the page.
        """
        pass
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """
        Check if the underlying model is available/healthy.
        """
        pass

class DeepSeekTranscriber(TranscriberAgent):
    """
    Concrete implementation using DeepSeek-OCR (or compatible VLM) via Ollama.
    """
    def __init__(self, model_name: str, ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self._available = False
        # Token tracking for LLM usage reporting
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def get_token_usage(self) -> Dict[str, int]:
        """Get accumulated token usage from all transcribe_page calls."""
        return {
            "input": self._total_input_tokens,
            "output": self._total_output_tokens,
            "total": self._total_input_tokens + self._total_output_tokens
        }

    def reset_token_usage(self):
        """Reset token counters (call before starting a new document)."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    async def check_availability(self) -> bool:
        """Check if the specific model exists in Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status != 200:
                        logger.error(f"Ollama health check failed: {response.status}")
                        return False
                    
                    data = await response.json()
                    models = [m['name'] for m in data.get('models', [])]
                    
                    # Check exact match or match with :latest
                    is_found = any(self.model_name in m for m in models)
                    
                    if is_found:
                        self._available = True
                        logger.info(f"Transcriber Agent online: {self.model_name}")
                        return True
                    else:
                        logger.warning(f"Transcriber model '{self.model_name}' not found in Ollama.")
                        return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False

    async def transcribe_page(self, image_path: str) -> str:
        if not self._available:
             # Try one last check in case it came online
             if not await self.check_availability():
                 raise RuntimeError(f"Transcriber model {self.model_name} is unavailable.")

        import base64
        
        # Read and encode image
        try:
            with open(image_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to read image for transcription: {e}")
            raise

        prompt = (
            "Transcribe this document page into Markdown. "
            "Preserve all tables, headers, and lists. "
            "Describe any figures or charts in detail."
        )

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [b64_image],
            "stream": False,
            "options": {
                "temperature": 0.1 # Low temp for factual transcription
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama generation failed: {error_text}")

                    result = await response.json()

                    # Track token usage from ollama response
                    input_tokens = result.get("prompt_eval_count", 0)
                    output_tokens = result.get("eval_count", 0)
                    self._total_input_tokens += input_tokens
                    self._total_output_tokens += output_tokens
                    logger.debug(f"[TRANSCRIBER] Page tokens: in={input_tokens}, out={output_tokens}")

                    return result.get("response", "")
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

class AgentFactory:
    """
    Factory to instantiate agents based on configuration.
    """
    @staticmethod
    async def get_transcriber(agent_config: Dict[str, str]) -> Optional[TranscriberAgent]:
        """
        Creates a TranscriberAgent if configured and available.
        
        Args:
            agent_config: Dictionary from user.settings["agent_roles"].
                          Example: {"transcriber": "ollama::deepseek-ocr:3b"}
        
        Returns:
            TranscriberAgent or None
        """
        model_identifier = agent_config.get("transcriber")
        if not model_identifier:
            logger.info("No Transcriber Agent configured.")
            return None
            
        # Parse identifier (provider::model)
        if "::" in model_identifier:
            provider, model_name = model_identifier.split("::", 1)
        else:
            # Default to ollama if no provider specified, or handle legacy
            provider = "ollama"
            model_name = model_identifier
            
        if provider.lower() == "ollama":
            # Get Ollama URL from environment or use default
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            logger.info(f"Connecting to Ollama at: {ollama_url}")

            agent = DeepSeekTranscriber(model_name=model_name, ollama_url=ollama_url)

            # Perform health check
            if await agent.check_availability():
                return agent
            else:
                logger.warning(f"Configured Transcriber '{model_name}' is unavailable.")
        
        # Fallback to DEFAULT role
        logger.warning("Failing over to DEFAULT role for Transcriber.")
        default_model = agent_config.get("default")
        if default_model:
            if "::" in default_model:
                provider, model_name = default_model.split("::", 1)
            else:
                provider = "ollama"
                model_name = default_model
            
            if provider.lower() == "ollama":
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                agent = DeepSeekTranscriber(model_name=model_name, ollama_url=ollama_url)
                if await agent.check_availability():
                    logger.info(f"Using DEFAULT role for Transcriber: {model_name}")
                    return agent
        
        logger.warning(f"Unsupported provider for Transcriber: {provider}")
        return None
