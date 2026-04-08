# backend/agents/model_router.py
"""
Model Router - Routes requests to the appropriate provider (Ollama, Gemini, etc.)

Model identifiers follow the format: provider::model_name[think:level]
Examples:
    - ollama::llama3.2:latest
    - ollama::gpt-oss:20b[think:high]
    - gemini::gemini-1.5-flash

The think parameter is automatically parsed from the model name by OllamaClient.
"""
from typing import Dict, Any, AsyncGenerator, List, Optional, Union
import httpx
from backend.agents.models.ollama import OllamaClient
from backend.agents.models.gemini import GeminiClient
from backend.agents.models.utils import parse_model_identifier
from backend.models.config import ModelConfig
from sqlmodel import Session, select
from backend.database import engine


class ModelRouter:
    def __init__(self):
        self.ollama = OllamaClient()
        self.gemini = GeminiClient()

    def _parse_model_id(self, model_identifier: str) -> tuple[str, str]:
        """
        Parse model identifier using centralized utility.

        Args:
            model_identifier: Full identifier like "ollama::model[think:high]"

        Returns:
            Tuple of (provider, model_name_with_suffix)
            Note: Returns model name WITH suffix - OllamaClient handles parsing.
        """
        parsed = parse_model_identifier(model_identifier)
        # Return full model name (with suffix if present) for OllamaClient to parse
        # This is extracted from original to preserve the suffix
        if "::" in model_identifier:
            _, model_with_suffix = model_identifier.split("::", 1)
        else:
            model_with_suffix = model_identifier
        return parsed.provider, model_with_suffix

    async def probe_model_capabilities(self, model_identifier: str) -> Dict[str, Any]:
        """
        Probes a model to see if it supports advanced capabilities like "thinking".
        Returns a dict of capabilities, e.g.:
        - {"thinking": True, "thinking_type": "boolean"} for standard thinking models
        - {"thinking": True, "thinking_type": "level"} for GPT-OSS (uses low/medium/high)
        - {"thinking": False, "thinking_type": None} for non-thinking models
        """
        parsed = parse_model_identifier(model_identifier)
        provider = parsed.provider
        model_name = parsed.model_name
        capabilities = {"thinking": False, "thinking_type": None}

        if provider == "ollama":
            # Detect if this is a GPT-OSS model (requires "low"/"medium"/"high" instead of boolean)
            is_gpt_oss = "gpt-oss" in model_name.lower()

            # Also detect known thinking model families by name
            known_thinking_models = ["qwen3", "deepseek-r1", "deepseek-v3"]
            is_known_thinking = any(tm in model_name.lower() for tm in known_thinking_models)

            try:
                # 1. Determine probe strategy based on model type
                if is_gpt_oss:
                    probe_think_param = "low"
                    print(f"Model {model_name} detected as GPT-OSS. Testing with think='low'.")
                else:
                    probe_think_param = True
                    print(f"Model {model_name} testing with think=True.")

                # Send a request with think parameter
                response = await self.ollama.generate_completion(
                    model=model_name,
                    prompt="What is 17 times 23? Think step by step.",
                    think=probe_think_param,
                    options={"num_predict": 100}
                )

                print(f"Probe response for {model_name}: keys={list(response.keys())}")

                # Check for "thinking" field in response
                if "thinking" in response:
                    thinking_content = response["thinking"]
                    thinking_type = "level" if is_gpt_oss else "boolean"
                    if thinking_content:
                        print(f"Model {model_name} supports thinking (field with content). Type: {thinking_type}")
                    else:
                        print(f"Model {model_name} supports thinking (field exists, empty). Type: {thinking_type}")
                    return {"thinking": True, "thinking_type": thinking_type}

                # Check for <think> tags in response content
                content = response.get("response", "")
                if "<think>" in content:
                    thinking_type = "level" if is_gpt_oss else "boolean"
                    print(f"Model {model_name} supports thinking (tags detected). Type: {thinking_type}")
                    return {"thinking": True, "thinking_type": thinking_type}

                # For GPT-OSS: if the call succeeded with think="low", it supports thinking
                if is_gpt_oss:
                    print(f"Model {model_name} accepted think='low' (200 OK). Marking as level-based thinking.")
                    return {"thinking": True, "thinking_type": "level"}

                # For known thinking models, trust the model family
                if is_known_thinking:
                    print(f"Model {model_name} is a known thinking model family. Marking as supported.")
                    return {"thinking": True, "thinking_type": "boolean"}

                print(f"Model {model_name} does not appear to support thinking.")
                return {"thinking": False, "thinking_type": None}

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    print(f"Model {model_name} rejected think={probe_think_param} (400 Bad Request).")
                else:
                    print(f"Probe failed for {model_name}: HTTP {e.response.status_code}")
                    if is_known_thinking:
                        print(f"Model {model_name} is a known thinking model. Marking as supported despite error.")
                        return {"thinking": True, "thinking_type": "level" if is_gpt_oss else "boolean"}
            except Exception as e:
                print(f"Probe failed for {model_name}: {e}")
                if is_known_thinking or is_gpt_oss:
                    print(f"Model {model_name} is a known thinking model. Marking as supported despite error.")
                    return {"thinking": True, "thinking_type": "level" if is_gpt_oss else "boolean"}

            return {"thinking": False, "thinking_type": None}

        return capabilities

    async def list_all_models(self, api_key: str = None) -> List[Dict[str, str]]:
        """
        Returns a unified list of models from all providers.
        Format: [{"id": "ollama::llama3", "name": "llama3", "provider": "ollama"}, ...]
        """
        unified_list = []

        # Ollama
        ollama_models = await self.ollama.list_models()
        for m in ollama_models:
            unified_list.append({
                "id": f"ollama::{m}",
                "name": m,
                "provider": "ollama"
            })

        # Gemini
        gemini_models = await self.gemini.list_models(api_key=api_key)
        for m in gemini_models:
            clean_name = m.replace("models/", "")
            unified_list.append({
                "id": f"gemini::{m}",
                "name": clean_name,
                "provider": "gemini"
            })

        return unified_list

    async def check_model_available(self, model_identifier: str) -> tuple[bool, List[str]]:
        """
        Check if a model is available.

        Args:
            model_identifier: Full identifier like "ollama::model[think:high]"

        Returns:
            Tuple of (is_available, list_of_available_models)
        """
        parsed = parse_model_identifier(model_identifier)

        if parsed.provider == "ollama":
            return await self.ollama.check_model_available(parsed.model_name)
        elif parsed.provider == "gemini":
            models = await self.gemini.list_models()
            return parsed.model_name in models, models
        else:
            return False, []

    async def generate(
        self,
        model_identifier: str,
        prompt: str,
        system: str = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion.

        The think parameter is automatically parsed from model_identifier if not provided.
        Example: "ollama::model[think:high]" -> think="high"

        Args:
            model_identifier: Full identifier with optional [think:...] suffix
            prompt: The prompt text
            system: Optional system message
            options: Provider-specific options
            think: Override for think parameter (auto-parsed if None)
        """
        provider, model_with_suffix = self._parse_model_id(model_identifier)

        if provider == "ollama":
            # Pass full model name with suffix - OllamaClient handles parsing
            return await self.ollama.generate_completion(
                model=model_with_suffix,
                prompt=prompt,
                system=system,
                options=options,
                think=think  # None means "auto-parse from model name"
            )
        elif provider == "gemini":
            parsed = parse_model_identifier(model_identifier)
            return await self.gemini.generate_completion(
                model=parsed.model_name,
                prompt=prompt,
                system=system
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def chat_stream(
        self,
        model_identifier: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion.

        The think parameter is automatically parsed from model_identifier if not provided.

        Args:
            model_identifier: Full identifier with optional [think:...] suffix
            messages: List of message dicts
            tools: Optional tool definitions
            options: Provider-specific options
            think: Override for think parameter (auto-parsed if None)
        """
        provider, model_with_suffix = self._parse_model_id(model_identifier)

        import logging
        logging.getLogger(__name__).info(f"ROUTER chat_stream: {provider} tools={tools is not None}")

        if provider == "ollama":
            async for chunk in self.ollama.chat_completion_stream(
                model=model_with_suffix,
                messages=messages,
                tools=tools,
                options=options,
                think=think
            ):
                yield chunk
        elif provider == "gemini":
            parsed = parse_model_identifier(model_identifier)
            async for chunk in self.gemini.chat_completion_stream(
                model=parsed.model_name,
                messages=messages,
                tools=tools,
                options=options
            ):
                yield chunk
        else:
            yield f"Error: Unknown provider {provider}"

    async def chat(
        self,
        model_identifier: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None
    ) -> Dict[str, Any]:
        """
        Non-streaming chat completion (uses /api/chat endpoint).

        This is the correct method for models that support thinking mode.
        Use this instead of generate() when you need thinking support.

        Args:
            model_identifier: Full identifier with optional [think:...] suffix
            messages: List of message dicts with 'role' and 'content'
            tools: Optional tool definitions
            options: Provider-specific options
            think: Override for think parameter (auto-parsed if None)

        Returns:
            Response dict with 'message' containing assistant's response
        """
        provider, model_with_suffix = self._parse_model_id(model_identifier)

        import logging
        logging.getLogger(__name__).info(f"ROUTER chat: {provider} tools={tools is not None}")

        if provider == "ollama":
            return await self.ollama.chat_completion(
                model=model_with_suffix,
                messages=messages,
                tools=tools,
                options=options,
                think=think
            )
        elif provider == "gemini":
            parsed = parse_model_identifier(model_identifier)
            response = await self.gemini.chat_completion(
                model=parsed.model_name,
                messages=messages,
                tools=tools,
                options=options
            )
            import logging
            logging.getLogger(__name__).info(f"ROUTER: Gemini chat_completion returned: {response}")
            return response
        else:
            raise ValueError(f"Unknown provider: {provider}")
