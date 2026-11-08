import inspect
from typing import Callable, Any, List, Dict, get_type_hints
from functools import wraps

class ToolMetadata:
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        category: str = "general",
        secrets: List[str] = None,
        agent_role: str = None,
        is_llm_based: bool = False
    ):
        self.name = name
        self.description = description
        self.func = func
        self.category = category
        self.secrets = secrets or []
        self.agent_role = agent_role  # Which agent role model to use (e.g., "vision", "coder", "handyman")
        self.is_llm_based = is_llm_based  # True if tool invokes an LLM internally
        self.schema = self._generate_schema(func)

    def _generate_schema(self, func: Callable) -> Dict[str, Any]:
        """
        Generates a JSON Schema for the function arguments based on type hints.
        """
        type_hints = get_type_hints(func)
        # Remove return type from schema
        if 'return' in type_hints:
            del type_hints['return']
            
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        sig = inspect.signature(func)
        
        for param_name, param_type in type_hints.items():
            # Skip secrets
            if param_name in self.secrets:
                continue

            # Basic type mapping
            json_type = "string"
            if param_type == int:
                json_type = "integer"
            elif param_type == float:
                json_type = "number"
            elif param_type == bool:
                json_type = "boolean"
            elif param_type == list or getattr(param_type, "__origin__", None) == list:
                json_type = "array"
            elif param_type == dict or getattr(param_type, "__origin__", None) == dict:
                json_type = "object"
            
            parameters["properties"][param_name] = {
                "type": json_type,
                "description": f"Argument {param_name}" # ideally we parse docstring for per-arg desc
            }
            
            # Check for default value
            param = sig.parameters.get(param_name)
            if param and param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
                
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": parameters
        }

def mentori_tool(
    category: str = "general",
    secrets: List[str] = None,
    agent_role: str = None,
    is_llm_based: bool = False
):
    """
    Decorator to mark a function as a Mentori Tool.

    Args:
        category: Tool category (e.g., "filesystem", "vision", "code")
        secrets: List of parameter names to inject from session context
        agent_role: The agent role whose model should execute this tool
                   (e.g., "vision", "coder", "handyman", "editor")
                   If None, tool is deterministic and uses no LLM.
        is_llm_based: True if the tool invokes an LLM internally.
                      Used for display purposes in tool cards.
    """
    def decorator(func: Callable):
        # Extract name and docstring
        name = func.__name__
        description = (func.__doc__ or "").strip()

        # Create async-aware wrapper that preserves signature
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            wrapper = async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper = sync_wrapper

        # Preserve original function signature for secret injection
        wrapper.__signature__ = inspect.signature(func)

        # Attach metadata to the wrapper (not the original func)
        # This ensures the registry uses the correct wrapped version
        wrapper._mentori_metadata = ToolMetadata(
            name=name,
            description=description,
            func=wrapper,  # Store the wrapper, not the original func
            category=category,
            secrets=secrets,
            agent_role=agent_role,
            is_llm_based=is_llm_based
        )

        return wrapper
    return decorator
