# backend/agents/models/gemini.py
import asyncio
import logging
from google import genai
from google.genai import types
from typing import List, Dict, Any, AsyncGenerator, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

# Retry config for transient Gemini API errors (500, 503, 429)
MAX_RETRIES = 4
RETRY_BASE_DELAY = 5  # seconds
RETRYABLE_CODES = {"500", "503", "429", "INTERNAL", "UNAVAILABLE", "RESOURCE_EXHAUSTED"}


class GeminiClient:
    # Class-level counters for tracking empty/blocked responses across all instances
    _empty_response_counts: Dict[str, int] = {
        "SAFETY": 0,
        "RECITATION": 0,
        "OTHER": 0,
        "NO_CANDIDATES": 0,
        "EMPTY_CONTENT": 0,
        "total_calls": 0,
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            print("Warning: No Gemini API Key provided.")
            self.client = None

    @classmethod
    def get_empty_response_stats(cls) -> Dict[str, Any]:
        """Return accumulated empty/blocked response statistics."""
        stats = dict(cls._empty_response_counts)
        total = stats["total_calls"]
        blocked = sum(v for k, v in stats.items() if k != "total_calls")
        stats["total_blocked"] = blocked
        stats["block_rate"] = f"{blocked / total * 100:.2f}%" if total > 0 else "n/a"
        return stats

    def _diagnose_empty_response(self, response, method: str) -> str:
        """Log diagnostic info when Gemini returns empty content. Returns the reason."""
        cls = type(self)
        cls._empty_response_counts["total_calls"] += 1
        print(f"[Gemini:{method}] DIAGNOSING EMPTY RESPONSE...")

        # Check prompt feedback (pre-generation block)
        prompt_feedback = getattr(response, "prompt_feedback", None)
        if prompt_feedback:
            block_reason = getattr(prompt_feedback, "block_reason", None)
            safety_ratings = getattr(prompt_feedback, "safety_ratings", None)
            if block_reason:
                reason = str(block_reason)
                bucket = "SAFETY" if "SAFETY" in reason.upper() else "OTHER"
                cls._empty_response_counts[bucket] += 1
                logger.warning(
                    f"[Gemini:{method}] PROMPT BLOCKED: reason={reason}, "
                    f"safety_ratings={safety_ratings}"
                )
                return f"PROMPT_BLOCKED:{reason}"

        # Check candidates
        candidates = getattr(response, "candidates", None)
        if not candidates:
            cls._empty_response_counts["NO_CANDIDATES"] += 1
            logger.warning(
                f"[Gemini:{method}] EMPTY RESPONSE: no candidates returned. "
                f"prompt_feedback={prompt_feedback}"
            )
            return "NO_CANDIDATES"

        candidate = candidates[0]
        finish_reason = getattr(candidate, "finish_reason", None)
        safety_ratings = getattr(candidate, "safety_ratings", None)
        content = getattr(candidate, "content", None)

        # Candidate exists but was blocked
        finish_str = str(finish_reason) if finish_reason else "NONE"
        if finish_reason and "SAFETY" in finish_str.upper():
            cls._empty_response_counts["SAFETY"] += 1
            logger.warning(
                f"[Gemini:{method}] SAFETY BLOCK: finish_reason={finish_str}, "
                f"safety_ratings={safety_ratings}"
            )
            return f"SAFETY:{finish_str}"
        elif finish_reason and "RECITATION" in finish_str.upper():
            cls._empty_response_counts["RECITATION"] += 1
            logger.warning(
                f"[Gemini:{method}] RECITATION BLOCK: finish_reason={finish_str}"
            )
            return f"RECITATION:{finish_str}"
        elif not content or not content.parts:
            cls._empty_response_counts["EMPTY_CONTENT"] += 1
            logger.warning(
                f"[Gemini:{method}] EMPTY CONTENT: finish_reason={finish_str}, "
                f"safety_ratings={safety_ratings}, content={content}"
            )
            return f"EMPTY_CONTENT:{finish_str}"
        else:
            cls._empty_response_counts["OTHER"] += 1
            logger.warning(
                f"[Gemini:{method}] EMPTY BUT HAS PARTS: finish_reason={finish_str}, "
                f"parts_count={len(content.parts)}, safety_ratings={safety_ratings}"
            )
            return f"OTHER:{finish_str}"

    async def list_models(self, api_key: str = None) -> List[str]:
        """Fetches available Gemini models."""
        client = self.client
        if api_key:
            client = genai.Client(api_key=api_key)
        if not client:
            return []
        try:
            models = []
            for m in client.models.list():
                if hasattr(m, 'supported_generation_methods') and 'generateContent' in (m.supported_generation_methods or []):
                    models.append(m.name)
                elif hasattr(m, 'name'):
                    models.append(m.name)
            return models
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")
            return []

    async def generate_completion(
        self,
        model: str,
        prompt: str,
        system: str = None,
        thinking_effort: str = None
    ) -> Dict[str, Any]:
        """Simple non-streaming completion with retry on transient errors."""
        config = types.GenerateContentConfig()
        if system:
            config.system_instruction = system

        # Retry loop for transient errors
        last_exc = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self.client.aio.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config,
                    )
                break  # success
            except Exception as e:
                last_exc = e
                if attempt < MAX_RETRIES and self._is_retryable(e):
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        f"[Gemini:generate_completion] Retryable error (attempt {attempt+1}/{MAX_RETRIES+1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"[Gemini:generate_completion] EXCEPTION after {attempt+1} attempts: {e}")
                return {"error": str(e)}

        try:
            # Diagnose empty responses
            response_text = ""
            try:
                response_text = response.text or ""
            except (ValueError, AttributeError):
                pass

            if not response_text:
                reason = self._diagnose_empty_response(response, "generate_completion")
                result = {"response": "", "raw": response, "empty_reason": reason}
            else:
                type(self)._empty_response_counts["total_calls"] += 1
                result = {"response": response_text, "raw": response}

            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                result["prompt_eval_count"] = getattr(um, "prompt_token_count", 0) or 0
                result["eval_count"] = getattr(um, "candidates_token_count", 0) or 0
            return result
        except Exception as e:
            return {"error": str(e)}

    def _build_tools(self, tools: List[Dict[str, Any]]) -> List[types.Tool]:
        """Convert OpenAI-style tool definitions to Gemini Tool objects."""
        func_declarations = []
        for tool in tools:
            func = tool.get("function", tool) if isinstance(tool, dict) else tool
            if isinstance(func, dict):
                params = func.get("parameters")
                fd = types.FunctionDeclaration(
                    name=func.get("name", ""),
                    description=func.get("description", ""),
                    parameters=params,  # google.genai accepts dicts directly
                )
                func_declarations.append(fd)
        return [types.Tool(function_declarations=func_declarations)] if func_declarations else []

    def _build_contents(self, messages: List[Dict[str, str]]) -> List[types.Content]:
        """Convert OpenAI-style messages to Gemini Content objects.
        
        This preserves _gemini_parts (original Part objects with thought_signature)
        when available, ensuring Gemini 3 models can validate function calls correctly.
        """
        contents = []
        
        for msg in messages:
            parts = []
            text_content = msg.get("content", "")
            role = msg.get("role", "user")
            
            # Map roles
            if role in ("assistant", "system"):
                gemini_role = "model"
            elif role in ("tool", "function"):
                gemini_role = "user"
            else:
                gemini_role = "user"
            
            # If we have preserved Gemini Part objects, use them directly
            gemini_parts = msg.get("_gemini_parts")
            if gemini_parts:
                parts = gemini_parts
            else:
                # Add text content
                if text_content:
                    parts.append(types.Part.from_text(text=text_content))
                
                # Convert tool calls to FunctionCall parts
                if role == "assistant" and "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", tc)
                        fc = types.FunctionCall(
                            name=func.get("name", ""),
                            args=func.get("arguments", {}),
                        )
                        parts.append(types.Part(function_call=fc))
                
                # Convert tool responses to FunctionResponse parts
                if role in ("tool", "function"):
                    parts = [
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=msg.get("name", ""),
                                response={"result": text_content},
                            )
                        )
                    ]
            
            # Gemini requires non-empty parts
            if not parts and gemini_role == "model":
                parts.append(types.Part.from_text(text="[Empty]"))
            elif not parts:
                parts.append(types.Part.from_text(text=text_content or " "))
            
            contents.append(types.Content(role=gemini_role, parts=parts))
        
        return contents

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Check if a Gemini exception is retryable (500/503/429)."""
        err_str = str(exc).upper()
        return any(code in err_str for code in RETRYABLE_CODES)

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Non-streaming chat completion with retry on transient errors."""
        if "gemini" not in model:
            model = model.split("/")[-1]

        # Build config
        config = types.GenerateContentConfig()
        if tools:
            config.tools = self._build_tools(tools)
        if options:
            if "temperature" in options:
                config.temperature = options["temperature"]
            if "num_predict" in options:
                config.max_output_tokens = options["num_predict"]

        # Build contents from messages
        contents = self._build_contents(messages)

        # Retry loop for transient errors
        last_exc = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self.client.aio.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
                break  # success
            except Exception as e:
                last_exc = e
                if attempt < MAX_RETRIES and self._is_retryable(e):
                    delay = RETRY_BASE_DELAY * (2 ** attempt)  # 5, 10, 20, 40s
                    logger.warning(
                        f"[Gemini:chat_completion] Retryable error (attempt {attempt+1}/{MAX_RETRIES+1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                # Non-retryable or max retries exhausted
                logger.error(f"[Gemini:chat_completion] EXCEPTION after {attempt+1} attempts: {e}")
                return {"error": str(e), "empty_reason": f"EXCEPTION:{e}"}

        try:

            # Parse response
            tool_calls = []
            content = ""
            # Preserve raw parts for echoing back (with thought_signature)
            raw_parts = []

            has_parts = (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
            )

            if has_parts:
                for part in response.candidates[0].content.parts:
                    raw_parts.append(part)
                    if part.function_call:
                        func_call = part.function_call
                        args_dict = dict(func_call.args) if func_call.args else {}
                        tool_calls.append({
                            "function": {
                                "name": func_call.name,
                                "arguments": args_dict
                            }
                        })
                    elif part.text:
                        content += part.text

            # Diagnose empty responses
            if not content and not tool_calls:
                reason = self._diagnose_empty_response(response, "chat_completion")
                empty_reason = reason
            else:
                type(self)._empty_response_counts["total_calls"] += 1
                empty_reason = None

            result = {
                "message": {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls,
                    "_gemini_parts": raw_parts,  # Preserve for history reconstruction
                }
            }
            if empty_reason:
                result["empty_reason"] = empty_reason
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                result["prompt_eval_count"] = getattr(um, "prompt_token_count", 0) or 0
                result["eval_count"] = getattr(um, "candidates_token_count", 0) or 0
            return result
        except Exception as e:
            logger.error(f"[Gemini:chat_completion] EXCEPTION: {e}")
            print(f"[Gemini:chat_completion] EXCEPTION: {e}")
            return {"error": str(e), "empty_reason": f"EXCEPTION:{e}"}

    async def chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion."""
        try:
            if "gemini" not in model:
                model = model.split("/")[-1]
            
            # Build config
            config = types.GenerateContentConfig()
            if tools:
                config.tools = self._build_tools(tools)
            if options:
                if "temperature" in options:
                    config.temperature = options["temperature"]
                if "num_predict" in options:
                    config.max_output_tokens = options["num_predict"]

            # Build contents from messages
            contents = self._build_contents(messages)
            
            # Stream the response
            import json
            response_stream = self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )
            
            for chunk in response_stream:
                # Check for function calls
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    tool_calls = []
                    raw_parts = []
                    for part in chunk.candidates[0].content.parts:
                        raw_parts.append(part)
                        if part.function_call:
                            func_call = part.function_call
                            args_dict = dict(func_call.args) if func_call.args else {}
                            tool_calls.append({
                                "function": {
                                    "name": func_call.name,
                                    "arguments": args_dict
                                }
                            })
                    
                    if tool_calls:
                        yield json.dumps({
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": tool_calls,
                                "_gemini_parts": None,  # Can't serialize Part objects to JSON
                            },
                            "done": False
                        })
                        continue

                # Text content
                if chunk.text:
                    yield json.dumps({
                        "message": {
                            "role": "assistant",
                            "content": chunk.text
                        },
                        "done": False
                    })
                
                # Usage metadata
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    usage = {
                        "done": True,
                        "usage": {
                            "prompt_tokens": getattr(chunk.usage_metadata, "prompt_token_count", 0),
                            "completion_tokens": getattr(chunk.usage_metadata, "candidates_token_count", 0),
                            "total_tokens": getattr(chunk.usage_metadata, "total_token_count", 0)
                        }
                    }
                    yield json.dumps(usage)
                    
        except Exception as e:
            yield f"Error: {str(e)}"
