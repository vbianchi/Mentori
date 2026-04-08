import logging
import uvicorn
from mcp.server.fastmcp import FastMCP
from backend.mcp.registry import registry

# Configure logging
# Configure logging
from backend.logging_config import setup_logging
logger = setup_logging()

# Initialize Registry
registry.discover_tools()
logger.info(f"Discovered {len(registry.tools)} tools.")

# Read admin-disabled tools from the shared SQLite DB
def _get_disabled_tools() -> set:
    """Return the set of admin-disabled tool names from SystemSettings."""
    try:
        from sqlmodel import Session, select
        from backend.database import engine
        from backend.models.system_settings import SystemSettings
        with Session(engine) as session:
            setting = session.exec(
                select(SystemSettings).where(SystemSettings.key == "tool_config")
            ).first()
            if setting and isinstance(setting.value, dict):
                return set(setting.value.get("disabled_tools", []))
    except Exception as e:
        logger.warning(f"Failed to read disabled tools config: {e}")
    return set()

disabled_tools = _get_disabled_tools()
if disabled_tools:
    logger.info(f"Admin-disabled tools (will not be registered): {sorted(disabled_tools)}")

# Initialize FastMCP with Host/Port to ensure correct binding and allowed_hosts configuration
mcp = FastMCP(
    "Mentori Tool Server",
    host="0.0.0.0",
    port=8777
)

# Register Tools (skipping admin-disabled ones)
for name, meta in registry.tools.items():
    if name in disabled_tools:
        logger.info(f"Skipping disabled tool: {name}")
        continue
    logger.info(f"Registering MCP tool: {name}")
    mcp.tool(name=name, description=meta.description)(meta.func)

if __name__ == "__main__":
    logger.info("Starting Mentori MCP Server on port 8777...")
    # Use built-in run method which respects init arguments
    mcp.run(transport='sse')
