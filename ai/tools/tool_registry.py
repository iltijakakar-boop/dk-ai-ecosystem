import os
import importlib
import sys
from typing import Dict, Any, List, Optional
from ai.tools.base_tool import BaseTool
from app.config.settings import settings
from app.core.logging import logger

class ToolRegistry:
    """
    Manages loading, validating, and registering built-in and plugin tools.
    """
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._disabled_tools: set[str] = set()

    def register_tool(self, tool: BaseTool) -> None:
        """
        Validates metadata and registers a tool instance.
        """
        # Validate required metadata properties
        required_metadata = [
            "tool_id", "name", "version", "description", "category",
            "author", "license", "tags", "permissions", "timeout", "parameters"
        ]
        
        for field in required_metadata:
            if not hasattr(tool, field):
                raise ValueError(f"Tool {tool.__class__.__name__} is missing required metadata field '{field}'")
            
        # Validate metadata types
        if not isinstance(tool.tool_id, str) or not tool.tool_id:
            raise ValueError(f"Tool tool_id must be a non-empty string in {tool.__class__.__name__}")
        if not isinstance(tool.version, str) or not tool.version:
            raise ValueError(f"Tool version must be a non-empty string in {tool.__class__.__name__}")
        if not isinstance(tool.author, str) or not tool.author:
            raise ValueError(f"Tool author must be a non-empty string in {tool.__class__.__name__}")
        if not isinstance(tool.license, str) or not tool.license:
            raise ValueError(f"Tool license must be a non-empty string in {tool.__class__.__name__}")
        if not isinstance(tool.tags, list):
            raise ValueError(f"Tool tags must be a list in {tool.__class__.__name__}")
        if not isinstance(tool.permissions, list):
            raise ValueError(f"Tool permissions must be a list in {tool.__class__.__name__}")
        if not isinstance(tool.timeout, int) or tool.timeout <= 0:
            raise ValueError(f"Tool timeout must be a positive integer in {tool.__class__.__name__}")
        if not isinstance(tool.parameters, dict):
            raise ValueError(f"Tool parameters must be a dictionary in {tool.__class__.__name__}")

        self.tools[tool.tool_id] = tool
        logger.info(f"Registered tool '{tool.tool_id}' successfully.")

    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """Gets a tool by ID if enabled."""
        if tool_id in self._disabled_tools:
            return None
        return self.tools.get(tool_id)

    def enable_tool(self, tool_id: str) -> None:
        """Enables a registered tool."""
        self._disabled_tools.discard(tool_id)

    def disable_tool(self, tool_id: str) -> None:
        """Disables a registered tool."""
        self._disabled_tools.add(tool_id)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns details for all enabled tools."""
        return [
            {
                "tool_id": t.tool_id,
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "category": t.category,
                "enabled": t.tool_id not in self._disabled_tools,
                "author": t.author,
                "license": t.license,
                "tags": t.tags,
                "permissions": t.permissions,
                "timeout": t.timeout,
                "parameters": t.parameters
            }
            for t in self.tools.values()
        ]

    def discover_builtin_tools(self) -> None:
        """
        Dynamically imports and registers built-in tools from the 'builtin' subfolder.
        """
        builtin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "builtin"))
        logger.info(f"Discovering built-in tools in: {builtin_dir}")
        
        if not os.path.exists(builtin_dir):
            logger.warning("Built-in tools folder does not exist.")
            return

        # Ensure the parent folders are in sys.path
        parent_dir = os.path.dirname(os.path.dirname(builtin_dir))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        for entry in os.scandir(builtin_dir):
            if entry.is_file() and entry.name.endswith(".py") and not entry.name.startswith("__"):
                module_name = f"ai.tools.builtin.{entry.name[:-3]}"
                try:
                    if module_name in sys.modules:
                        module = importlib.reload(sys.modules[module_name])
                    else:
                        module = importlib.import_module(module_name)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseTool)
                            and attr is not BaseTool
                        ):
                            tool_instance = attr()
                            self.register_tool(tool_instance)
                except Exception as e:
                    logger.exception(f"Failed to load built-in tool {entry.name}:")

# Global Registry instance
tool_registry = ToolRegistry()
