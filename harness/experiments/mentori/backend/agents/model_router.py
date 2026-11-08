# backend/agents/model_router.py
"""
Model Router - Routes requests to the appropriate provider (Ollama, Gemini, etc.)

Model identifiers follow the format: provider::model_name[think:level]
Examples:
    - ollama::llama3.2:latest
    - ollama::gpt-oss:20b[think:high]
    - gemini::gemini-1.5-flash

generate, chat and chat_stream send every call through backend.agents.lock_adapter, which runs it with
experiments/runner under experiments/LOCK.toml inside the run's context (A1, D67). The [think:level] suffix and
the options and think arguments are recorded as caller_asked and never sent.
"""
import json
from typing import Dict, Any, AsyncGenerator, List, Optional, Union
from backend.agents import lock_adapter
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
        Generate a completion under the lock (lock_adapter.generate).

        Args:
            model_identifier: Full identifier; the [think:...] suffix is recorded, never sent
            prompt: The prompt text
            system: Must be None (a caller system prompt is refused)
            options: Recorded as caller_asked, never sent
            think: Recorded as caller_asked, never sent

        Returns:
            {"response", "thinking", "done_reason", "prompt_eval_count", "eval_count", "lock_record"}
        """
        return await lock_adapter.agenerate(model_identifier, prompt, system=system, options=options, think=think)

    async def chat_stream(
        self,
        model_identifier: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None
    ) -> AsyncGenerator[str, None]:
        """
        Chat under the lock (lock_adapter.chat), run to completion, then yielded as two Ollama-format JSON lines:
        {"message": {"role", "content", "thinking" (only when non-empty), "tool_calls"}}, then
        {"done": true, "done_reason", "prompt_eval_count", "eval_count"}.

        Args:
            model_identifier: Full identifier; the [think:...] suffix is recorded, never sent
            messages: List of message dicts
            tools: Optional tool definitions
            options: Recorded as caller_asked, never sent
            think: Recorded as caller_asked, never sent
        """
        out = await lock_adapter.achat(model_identifier, messages, tools=tools, options=options, think=think,
                                       _method="chat_stream")
        msg = out["message"]
        line = {"role": msg["role"], "content": msg["content"]}
        if msg["thinking"]:
            line["thinking"] = msg["thinking"]
        line["tool_calls"] = msg["tool_calls"]
        yield json.dumps({"message": line})
        yield json.dumps({"done": True, "done_reason": out["done_reason"],
                          "prompt_eval_count": out["prompt_eval_count"], "eval_count": out["eval_count"]})

    async def chat(
        self,
        model_identifier: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None
    ) -> Dict[str, Any]:
        """
        Non-streaming chat completion under the lock (lock_adapter.chat).

        Args:
            model_identifier: Full identifier; the [think:...] suffix is recorded, never sent
            messages: List of message dicts with 'role' and 'content'
            tools: Optional tool definitions
            options: Recorded as caller_asked, never sent
            think: Recorded as caller_asked, never sent

        Returns:
            {"message": {"role", "content", "thinking", "tool_calls"[, "_gemini_parts"]}, "response",
             "done_reason", "prompt_eval_count", "eval_count", "lock_record"}
        """
        return await lock_adapter.achat(model_identifier, messages, tools=tools, options=options, think=think)
