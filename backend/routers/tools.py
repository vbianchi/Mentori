from fastapi import APIRouter, HTTPException, Depends
from backend.mcp.registry import registry
from backend.auth import get_current_user
from backend.models.user import User
from pydantic import BaseModel
from typing import Dict, Any, List
import inspect

router = APIRouter(prefix="/tools", tags=["tools"])

# Initial discovery on load (optional, or trigger via admin)
registry.discover_tools()

class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@router.get("/", response_model=List[Dict])
def list_tools(current_user: User = Depends(get_current_user)):
    """
    List all available tools and their schemas.
    """
    # In dev, we might want to auto-discover on every request to see changes
    registry.discover_tools() 
    return registry.list_tools()

@router.post("/execute")
async def execute_tool(
    req: ToolExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a tool.
    Secure access: Checks if tool requires secrets, and injects them from User Settings.
    """
    tool_meta = registry.get_tool(req.tool_name)
    if not tool_meta:
        raise HTTPException(status_code=404, detail=f"Tool '{req.tool_name}' not found")
        
    # Inject Secrets from User Settings
    # Expects user.settings["api_keys"] to contain keys like "TAVILY_API_KEY"
    user_api_keys = current_user.settings.get("api_keys", {})

    # Simple dependency injection for secrets
    # If the function has an argument that matches a secret name, pass it.
    # Note on RFC: "secrets" list in metadata tells us what keys are needed.
    # We can pass them as kwargs if the function signature asks for them.

    # 1. Start with provided arguments
    final_kwargs = req.arguments.copy()

    # 2. Inject requested secrets
    for secret_name in tool_meta.secrets:
        # Check if it's an API key from user settings
        if secret_name in user_api_keys:
            if secret_name not in final_kwargs:
                final_kwargs[secret_name] = user_api_keys[secret_name]
        # Check if it's a context variable (user_id, task_id)
        elif secret_name == "user_id":
            if secret_name not in final_kwargs:
                final_kwargs[secret_name] = current_user.id
        elif secret_name == "task_id":
            # task_id should be provided in the arguments by the agent
            # If not provided, we can't inject it (it's task-specific)
            pass
        else:
            # If a strict requirement, we might fail here?
            # Or let the tool fail.
            pass

    try:
        # Helper to run sync functions in async threadpool if needed
        # For now, just direct call (assuming tools are fast or async? Our decorator wraps sync)
        # To support async tools properly we'd need inspection.
        # For simplicity in this prototype, we run directly.
        if inspect.iscoroutinefunction(tool_meta.func):
            result = await tool_meta.func(**final_kwargs)
        else:
            result = tool_meta.func(**final_kwargs)
            
        return {"status": "success", "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")
