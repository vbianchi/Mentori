"""
Transcriber agent: page images to Markdown.

Every model call goes through backend.agents.lock_adapter under experiments/LOCK.toml (A1, D67; calls.md F3 B3,
O1.3). The model is the run context's "transcriber" agent role (run_context.agent_model, the one lookup every tool
uses), never the database's; a call outside a run, or in a run that names no transcriber model, raises.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
import json

from backend.agents import lock_adapter as la
from backend.agents.models.utils import parse_model_identifier

from experiments.runner import run_context as rc  # importable once lock_adapter has put the repository on sys.path

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
    Concrete implementation using DeepSeek-OCR (or compatible VLM) through the lock adapter.
    """
    def __init__(self, model_identifier: str):
        self.model_identifier = model_identifier          # provider::name[think:x], as the run context names it
        self.model_name = parse_model_identifier(model_identifier).model_name
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
        """Check that the run allows the model as a generator (Mentori's components run as generators, D66).
        Raises LockError when it does not; the runner checks the server's tag and digest on every call."""
        rc.check_model(self.model_name, "generator")
        self._available = True
        logger.info(f"Transcriber Agent allowed by the run: {self.model_identifier}")
        return True

    async def transcribe_page(self, image_path: str) -> str:
        if not self._available:
             # Check that the run allows the model (raises LockError when it does not)
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

        try:
            # One completion through the lock adapter, with the page image; settings come from the lock and the
            # run context. The option Mentori set here is recorded in caller_asked, never sent. The record keeps
            # the image's sha256, never its data.
            result = await la.agenerate(self.model_identifier, prompt, images=[b64_image],
                                        options={"temperature": 0.1})

            # Track token usage from the adapter result (the record's prompt_tokens and output_tokens)
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
    async def get_transcriber(agent_config: Optional[Dict[str, str]] = None) -> Optional[TranscriberAgent]:
        """
        Creates the run's TranscriberAgent.

        Args:
            agent_config: Not read (the callers in the copy pass user.settings["agent_roles"]): the model is the
                          run context's "transcriber" agent role (run_context.agent_model), with no database
                          or default-role fallback.

        Returns:
            TranscriberAgent. Raises outside a run, when the run names no transcriber model, and when the run
            does not allow that model as a generator.
        """
        agent = DeepSeekTranscriber(model_identifier=rc.agent_model("transcriber"))
        await agent.check_availability()
        return agent
