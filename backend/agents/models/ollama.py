# backend/agents/models/ollama.py
"""
Ollama Client with automatic model identifier parsing.

Model identifiers can include thinking mode in the name:
    - "llama3.2:latest"           -> No thinking
    - "qwen3:8b[think:true]"      -> Boolean thinking
    - "gpt-oss:20b[think:high]"   -> Level thinking ("low", "medium", "high")

The client automatically parses these suffixes and passes the correct `think`
parameter to Ollama. You can also override by passing `think` explicitly.
"""
import httpx
from typing import List, Dict, Any, AsyncGenerator, Union
from backend.config import settings
from backend.agents.models.utils import parse_model_identifier


class OllamaClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    def _ensure_num_ctx(self, options: Dict[str, Any] | None) -> Dict[str, Any]:
        """Inject num_ctx if not already provided.

        Ollama defaults to 2048 tokens — far below what modern models support.
        We use 24576 (24K) as default — sufficient for RLM turns and judge scoring,
        while keeping KV cache memory reasonable for multi-instance setups.

        WARNING: Do NOT use admin min_context_window here (128K → 98304 tokens).
        That causes Ollama to pre-allocate ~42 GB per instance (vs ~20 GB at 24K),
        leading to kernel panics on multi-instance setups.
        """
        opts = dict(options) if options else {}
        if "num_ctx" not in opts:
            opts["num_ctx"] = 24576
        return opts

    def _parse_model(self, model: str, think_override: Union[bool, str, None] = None) -> tuple[str, Union[bool, str]]:
        """
        Parse model identifier and extract think parameter.

        Args:
            model: Model name, possibly with [think:...] suffix
            think_override: If provided, overrides the parsed think value

        Returns:
            Tuple of (clean_model_name, think_param)
        """
        parsed = parse_model_identifier(model)
        clean_name = parsed.model_name

        # Use override if provided, otherwise use parsed value
        if think_override is not None:
            think = think_override
        else:
            think = parsed.think if parsed.think is not None else False

        return clean_name, think

    async def list_models(self) -> List[str]:
        """Auto-discovery: Fetches available models from Ollama."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [model["name"] for model in data.get("models", [])]
            except Exception as e:
                print(f"Error fetching Ollama models: {e}")
                return []

    async def check_model_available(self, model: str) -> tuple[bool, List[str]]:
        """
        Check if a model is available in Ollama.

        Args:
            model: Model name (with or without [think:...] suffix)

        Returns:
            Tuple of (is_available, list_of_available_models)
        """
        clean_name, _ = self._parse_model(model)
        available = await self.list_models()

        # Direct match
        if clean_name in available:
            return True, available

        # Try without :latest suffix
        base_name = clean_name.replace(":latest", "")
        for m in available:
            if m.startswith(base_name):
                return True, available

        return False, available

    async def generate_completion(
        self,
        model: str,
        prompt: str,
        system: str = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Simple non-streaming completion.

        The model name can include thinking mode:
            - "llama3.2:latest" -> think=False
            - "qwen3:8b[think:true]" -> think=True
            - "gpt-oss:20b[think:high]" -> think="high"

        Args:
            model: Model name (with optional [think:...] suffix)
            prompt: The prompt text
            system: Optional system message
            options: Ollama options (temperature, etc.)
            think: Override for think parameter (if None, parsed from model name)
            timeout: Request timeout in seconds. Default 300s for long-running tasks.

        Returns:
            Ollama response dict
        """
        clean_model, think_param = self._parse_model(model, think)

        payload = {
            "model": clean_model,
            "prompt": prompt,
            "stream": False,
            "options": self._ensure_num_ctx(options),
            "keep_alive": "120m",
        }
        if system:
            payload["system"] = system
        if think_param is not None:
            payload["think"] = think_param

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            if resp.status_code != 200:
                # Capture the actual error message from Ollama
                try:
                    error_detail = resp.json().get("error", resp.text)
                except Exception:
                    error_detail = resp.text
                raise httpx.HTTPStatusError(
                    f"Ollama error ({resp.status_code}): {error_detail}",
                    request=resp.request,
                    response=resp
                )
            return resp.json()

    async def chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None,
        timeout: float = 300.0
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat completion generator.

        The model name can include thinking mode:
            - "llama3.2:latest" -> think=False
            - "qwen3:8b[think:true]" -> think=True
            - "gpt-oss:20b[think:high]" -> think="high"

        Args:
            model: Model name (with optional [think:...] suffix)
            messages: List of message dicts
            tools: Optional tool definitions
            options: Ollama options
            think: Override for think parameter (if None, parsed from model name)
            timeout: Request timeout in seconds. Default 300s.

        Yields:
            JSON strings from Ollama stream
        """
        clean_model, think_param = self._parse_model(model, think)

        payload = {
            "model": clean_model,
            "messages": messages,
            "stream": True,
            "options": self._ensure_num_ctx(options),
            "keep_alive": "120m",
        }
        if tools:
            payload["tools"] = tools
        if think_param is not None:
            payload["think"] = think_param

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for chunk in response.aiter_lines():
                    if chunk:
                        yield chunk

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        options: Dict[str, Any] = None,
        think: Union[bool, str, None] = None,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Non-streaming chat completion (uses /api/chat with stream=false).

        This is the correct endpoint for models that support thinking mode.
        Use this instead of generate_completion() when you need thinking support.

        Args:
            model: Model name (with optional [think:...] suffix)
            messages: List of message dicts with 'role' and 'content'
            tools: Optional tool definitions
            options: Ollama options
            think: Override for think parameter (if None, parsed from model name)
            timeout: Request timeout in seconds. Default 300s.

        Returns:
            Ollama response dict with 'message' containing the assistant's response
        """
        clean_model, think_param = self._parse_model(model, think)

        payload = {
            "model": clean_model,
            "messages": messages,
            "stream": False,
            "options": self._ensure_num_ctx(options),
            "keep_alive": "120m",
        }
        if tools:
            payload["tools"] = tools
        if think_param is not None:
            payload["think"] = think_param

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            if resp.status_code != 200:
                try:
                    error_detail = resp.json().get("error", resp.text)
                except Exception:
                    error_detail = resp.text
                raise httpx.HTTPStatusError(
                    f"Ollama error ({resp.status_code}): {error_detail}",
                    request=resp.request,
                    response=resp
                )
            return resp.json()

    # ============================================================
    # Model Management Methods (for Admin Panel)
    # ============================================================

    async def get_running_models(self) -> List[Dict[str, Any]]:
        """
        Query Ollama /api/ps endpoint for currently loaded models.

        Returns:
            List of model info dicts with keys:
            - name: Model name (e.g., "llama3.2:latest")
            - model: Model identifier
            - size: Total size in bytes
            - size_vram: VRAM usage in bytes
            - digest: Model digest
            - details: Model details dict
            - expires_at: ISO timestamp when model will be unloaded (if keep_alive is set)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/api/ps")
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("models", [])
                else:
                    print(f"Error fetching running models: HTTP {resp.status_code}")
                    return []
            except Exception as e:
                print(f"Error fetching running models: {e}")
                return []

    async def preload_model(
        self,
        model: str,
        keep_alive: str = "-1"
    ) -> Dict[str, Any]:
        """
        Preload a model into Ollama memory by sending an empty chat request.

        This is the standard Ollama approach for warming up models.
        Setting keep_alive="-1" keeps the model loaded indefinitely.

        Args:
            model: Model name (without provider prefix, e.g., "llama3.2:latest")
            keep_alive: Duration to keep model loaded:
                - "-1" = forever (until manually unloaded)
                - "0" = unload immediately after request
                - "5m", "1h", "24h" = duration strings

        Returns:
            Dict with "status" ("loaded" or "failed") and optional "error" message
        """
        # Strip provider prefix if present (e.g., "ollama::llama3" -> "llama3")
        clean_model, _ = self._parse_model(model)

        payload = {
            "model": clean_model,
            "messages": [{"role": "user", "content": ""}],  # Empty message just loads model
            "keep_alive": keep_alive,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    return {"status": "loaded", "error": None, "model": clean_model}
                else:
                    try:
                        error_detail = resp.json().get("error", resp.text)
                    except Exception:
                        error_detail = resp.text
                    return {"status": "failed", "error": error_detail, "model": clean_model}
        except httpx.TimeoutException:
            return {"status": "failed", "error": "Timeout loading model (>120s)", "model": clean_model}
        except Exception as e:
            return {"status": "failed", "error": str(e), "model": clean_model}

    async def unload_model(self, model: str) -> Dict[str, Any]:
        """
        Unload a model from Ollama memory by sending keep_alive=0.

        Args:
            model: Model name to unload

        Returns:
            Dict with "status" ("unloaded" or "failed") and optional "error" message
        """
        clean_model, _ = self._parse_model(model)

        payload = {
            "model": clean_model,
            "messages": [],
            "keep_alive": "0",  # Immediately unload
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                # Ollama may return 200 or other status for unload
                return {"status": "unloaded", "error": None, "model": clean_model}
        except Exception as e:
            return {"status": "failed", "error": str(e), "model": clean_model}

    async def check_health(self) -> bool:
        """
        Check if Ollama is running and responsive.

        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
