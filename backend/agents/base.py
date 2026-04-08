
from typing import List, Dict, Any, Optional
import asyncio
import inspect
import json
from backend.agents.model_router import ModelRouter
from backend.agents.session_context import get_logger, get_session_context

logger = get_logger(__name__)

class AsyncAgent:
    def __init__(self, name: str, model: str, system_prompt: str, tools: List[Dict] = None):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.history: List[Dict] = [{"role": "system", "content": system_prompt}]
        self.model_router = ModelRouter()

    async def run(self, user_input: str) -> str:
        """
        Executes a single turn (Thinking -> Tool Call -> Tool Result -> Answer).
        Returns the final answer string.
        
        NOTE: This is a simplified non-streaming run for internal agents (Specialists).
        The Top-Level Coordinator will stream its own thoughts, but might wait for specialists.
        Alternatively, specialists could stream too, but that adds complexity to the Coordinator's UI.
        For MVP Integration, specialists will be 'atomic' operations from the Coordinator's POVs.
        """
        self.history.append({"role": "user", "content": user_input})
        
        max_turns = 10
        current_turn = 0
        
        while current_turn < max_turns:
            current_turn += 1
            logger.info(f"[{self.name}] Turn {current_turn}...")
            
            # Simple accumulation of the stream
            full_content = ""
            tool_calls = []

            async for chunk in self.model_router.chat_stream(
                model_identifier=self.model,
                messages=self.history,
                tools=self.tools,
                think=False # Specialists usually don't need 'think' block visualization for now
            ):
                try:
                    data = json.loads(chunk)
                    if "message" in data:
                        delta = data["message"]
                        if "content" in delta:
                            full_content += delta["content"]
                        if "tool_calls" in delta:
                            tool_calls.extend(delta["tool_calls"])
                except (json.JSONDecodeError, TypeError) as e:
                    # Non-JSON chunks (e.g., raw text from some providers) - log at debug level
                    logger.debug(f"Non-JSON chunk received: {chunk[:100] if chunk else 'empty'}")
            
            # Add Assistant message to history
            self.history.append({
                "role": "assistant",
                "content": full_content,
                "tool_calls": tool_calls if tool_calls else None
            })

            if not tool_calls:
                # Done, return final answer
                return full_content
            
            # Execute Tools
            # Note: In the real backend, we'd need a way to execute tools. 
            # For now, we assume the tools passed in are 'local' functions or handled by a registry.
            # But wait, `chat_loop` uses MCP. 
            # For Internal Agents, maybe we just use local python functions?
            # YES, for this integration, the Specialists (Coder, Handyman) use Python functions defined in their module.
            
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                
                # Find matching tool in self.tools list? 
                # Actually we need the callable. 
                # We'll expect self.tools to be a list of dicts, but we also need a map to callables.
                # Let's subclass to handle this.
                result = f"Error: Tool {func_name} not found"
                if hasattr(self, "tool_map") and func_name in self.tool_map:
                     try:
                         tool_fn = self.tool_map[func_name]
                         # Handle both sync and async tool functions
                         if inspect.iscoroutinefunction(tool_fn):
                             result = await tool_fn(**args)
                         else:
                             result = tool_fn(**args)
                     except Exception as e:
                         logger.error(f"Error executing {func_name}: {e}", exc_info=True)
                         result = f"Error executing {func_name}: {e}"
                
                self.history.append({
                    "role": "tool",
                    "name": func_name,
                    "content": str(result)
                })
        
        return "Max turns reached."
