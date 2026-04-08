import os
import importlib.util
import inspect
from typing import Dict, List, Optional
from backend.mcp.decorator import ToolMetadata

class ToolRegistry:
    def __init__(self, tools_dir: str):
        self.tools_dir = tools_dir
        self.tools: Dict[str, ToolMetadata] = {}

    def discover_tools(self, force: bool = False):
        """
        Scans the tools directory for python files and loads them.
        Finds any function with _mentori_metadata attached.
        Results are cached after the first run; pass force=True to re-scan.
        """
        if self.tools and not force:
            return  # Already discovered — skip expensive reimport

        self.tools = {} # Reset

        if not os.path.exists(self.tools_dir):
            os.makedirs(self.tools_dir)

        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                file_path = os.path.join(self.tools_dir, filename)
                self._load_module(module_name, file_path)
                
    def _load_module(self, module_name: str, file_path: str):
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Inspect module attributes
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and hasattr(obj, "_mentori_metadata"):
                        metadata: ToolMetadata = obj._mentori_metadata
                        # Register tool
                        # ID format: filename_functionname to avoid collisions? 
                        # Or just function name if we want simplicity. Let's use function name for now.
                        self.tools[metadata.name] = metadata
                        print(f"Registered tool: {metadata.name} [{metadata.category}]")
                        
        except Exception as e:
            print(f"Failed to load tool {module_name}: {str(e)}")

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "schema": t.schema,
                "secrets": t.secrets
            }
            for t in self.tools.values()
        ]

# Global Registry Instance
# Points to 'backend/mcp/custom' relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_TOOLS_DIR = os.path.join(BASE_DIR, "mcp", "custom")

registry = ToolRegistry(CUSTOM_TOOLS_DIR)
