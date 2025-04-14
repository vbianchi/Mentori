# backend/llm_planners.py
import logging
import httpx # For Ollama async requests
import google.generativeai as genai # For Gemini
from typing import Protocol, runtime_checkable
from backend.config import Settings # Import the Settings dataclass

logger = logging.getLogger(__name__)

# Define a common interface using Protocol
@runtime_checkable
class LLMPlanner(Protocol):
    """Protocol defining the interface for LLM planners."""
    async def generate_plan(self, task_description: str) -> str:
        """Generates a step-by-step plan for the given task."""
        ...

# --- Gemini Planner Implementation ---
class GeminiPlanner:
    """LLM Planner implementation using Google Gemini."""
    def __init__(self, settings: Settings):
        self.api_key = settings.google_api_key
        self.model_name = settings.gemini_model_name
        if not self.api_key:
            raise ValueError("Gemini API key is required for GeminiPlanner.")
        try:
            genai.configure(api_key=self.api_key)
            # Configure safety settings to be less restrictive if needed, but be cautious
            # Example: Allow all categories (use with care)
            # safety_settings = [
            #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            #     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            #     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            # ]
            # self.model = genai.GenerativeModel(self.model_name, safety_settings=safety_settings)
            self.model = genai.GenerativeModel(self.model_name) # Default safety settings
            logger.info(f"GeminiPlanner initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}", exc_info=True)
            raise ConnectionError(f"Failed to configure Gemini: {e}") from e

    async def generate_plan(self, task_description: str) -> str:
        """Generates a plan using the configured Gemini model."""
        # *** REFINED PROMPT ***
        prompt = f"""
        Analyze the following task and generate a sequence of executable commands (primarily shell commands for now) to accomplish it.

        RULES:
        - Output ONLY the raw commands, one command per line.
        - Do NOT include explanations, descriptions, comments, numbering, backticks, or any text other than the commands themselves.
        - If a step doesn't translate directly to a shell command, represent it as a clear action phrase (but prioritize shell commands if possible).

        Task: "{task_description}"

        Commands:
        """
        logger.info(f"Generating plan for task: '{task_description[:50]}...' using Gemini model {self.model_name}")
        try:
            # Use generate_content_async for async operation
            # Consider adding generation_config for temperature, max_output_tokens etc. if needed
            response = await self.model.generate_content_async(prompt)

            # Accessing response text might differ slightly based on version/response structure
            # Check response object structure if errors occur here
            plan = response.text.strip()

            # Check for potential safety blocks or empty responses
            if not plan:
                 # Check if the response was blocked
                 try:
                      if response.prompt_feedback.block_reason:
                           block_reason = response.prompt_feedback.block_reason
                           logger.warning(f"Gemini plan generation blocked. Reason: {block_reason}")
                           return f"Error: Plan generation blocked due to safety settings ({block_reason})."
                 except (AttributeError, ValueError):
                      # If prompt_feedback or block_reason doesn't exist or isn't as expected
                      pass # Continue to check if plan is just empty

                 logger.warning("Gemini returned an empty plan.")
                 return "Error: AI returned an empty plan."


            logger.info("Plan generated successfully by Gemini.")
            # Basic validation (already done)
            if "error" in plan.lower() or "unable to" in plan.lower():
                 logger.warning(f"Gemini may have returned a problematic plan: {plan}")
                 # Return it anyway for now, let execution fail if needed
            return plan
        except Exception as e:
            logger.error(f"Error during Gemini plan generation: {e}", exc_info=True)
            error_message = f"Error generating plan with Gemini: {type(e).__name__} - {e}"
            if "API key not valid" in str(e):
                 error_message = "Error: Invalid Google API Key."
            # Check for permission errors (e.g., related to API enablement)
            elif "permission denied" in str(e).lower() or "api not enabled" in str(e).lower():
                 error_message = "Error: Permission denied or API not enabled for Google AI."
            return f"Error: Failed to generate plan using Gemini ({error_message})"


# --- Ollama Planner Implementation ---
class OllamaPlanner:
    """LLM Planner implementation using a local Ollama instance."""
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url.rstrip('/')
        self.model_name = settings.ollama_model_name
        self.api_url = f"{self.base_url}/api/generate"
        logger.info(f"OllamaPlanner initialized: URL='{self.api_url}', Model='{self.model_name}'")

    async def generate_plan(self, task_description: str) -> str:
        """Generates a plan using the configured Ollama model via HTTP API."""
        # *** REFINED PROMPT ***
        prompt = f"""
        Analyze the following task and generate a sequence of executable commands (primarily shell commands for now) to accomplish it.

        RULES:
        - Output ONLY the raw commands, one command per line.
        - Do NOT include explanations, descriptions, comments, numbering, backticks, or any text other than the commands themselves.
        - If a step doesn't translate directly to a shell command, represent it as a clear action phrase (but prioritize shell commands if possible).

        Task: "{task_description}"

        Commands:
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            # Add options if needed, e.g., temperature, stop sequences
            "options": {
                 "temperature": 0.5 # Example: lower temperature for more deterministic output
            }
        }
        logger.info(f"Generating plan for task: '{task_description[:50]}...' using Ollama model {self.model_name}")

        try:
            async with httpx.AsyncClient(timeout=90.0) as client: # Slightly longer timeout for local models
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()

            response_data = response.json()
            plan = response_data.get("response", "").strip()
            logger.info("Plan generated successfully by Ollama.")
            if not plan:
                 logger.warning("Ollama returned an empty plan.")
                 return "Error: AI returned an empty plan."
            # Basic validation
            if "error" in plan.lower() or "unable to" in plan.lower():
                 logger.warning(f"Ollama may have returned a problematic plan: {plan}")
            return plan
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Ollama at {self.api_url}: {e}", exc_info=True)
            return f"Error: Could not connect to Ollama at {self.base_url}. Is Ollama running?"
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama returned an error status {e.response.status_code}: {e.response.text}", exc_info=True)
            error_detail = e.response.text[:200]
            if "model not found" in error_detail.lower():
                 return f"Error: Ollama model '{self.model_name}' not found. Make sure it's pulled."
            return f"Error: Ollama returned status {e.response.status_code}. {error_detail}"
        except Exception as e:
            logger.error(f"Error during Ollama plan generation: {e}", exc_info=True)
            return f"Error: Failed to generate plan using Ollama ({type(e).__name__})"


# --- Factory function to get the configured planner ---
def get_planner(settings: Settings) -> LLMPlanner:
    """Instantiates and returns the appropriate LLM planner based on settings."""
    provider = settings.ai_provider
    logger.info(f"Creating planner for provider: {provider}")
    if provider == "gemini":
        # Add check for API key before attempting to create
        if not settings.google_api_key:
             logger.error("Cannot create GeminiPlanner: GOOGLE_API_KEY is not set.")
             # Fallback to EchoPlanner if key is missing
             class EchoPlanner:
                 async def generate_plan(self, task_description: str) -> str:
                     logger.warning("Using EchoPlanner: GOOGLE_API_KEY missing.")
                     return f"Error: GOOGLE_API_KEY not configured."
             return EchoPlanner()
        return GeminiPlanner(settings)
    elif provider == "ollama":
        return OllamaPlanner(settings)
    else:
        logger.error(f"Unsupported AI_PROVIDER configured: {provider}. Falling back to basic echo.")
        class EchoPlanner:
             async def generate_plan(self, task_description: str) -> str:
                 logger.warning("Using EchoPlanner due to invalid AI_PROVIDER.")
                 return f"Echo: Task received - '{task_description}'. No AI configured."
        return EchoPlanner()

