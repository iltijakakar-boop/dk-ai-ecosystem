import os
import json
import importlib
import sys
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from ai.tools.tool_registry import tool_registry
from ai.tools.base_tool import BaseTool

class PluginLoader:
    """
    Scans the plugins folder, parses manifests, checks for duplicate plugins,
    and dynamically registers tool classes exposed by plugins.
    """
    def __init__(self, plugins_dir: Optional[str] = None):
        if plugins_dir is None:
            # Resolves relative to workspace root (c:\Projects\dk-ai-ecosystem\plugins)
            self.plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "plugins"))
        else:
            self.plugins_dir = os.path.abspath(plugins_dir)
            
        self.loaded_plugins: Dict[str, dict] = {}

    def discover_and_load_plugins(self) -> None:
        """
        Scans, validates, and registers plugins.
        """
        logger.info(f"Scanning plugins in: {self.plugins_dir}")
        if not os.path.exists(self.plugins_dir):
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist.")
            return

        # Ensure parent folder of plugins is in sys.path
        parent_dir = os.path.dirname(self.plugins_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        for entry in os.scandir(self.plugins_dir):
            if entry.is_dir() and not entry.name.startswith((".", "__", "runtime")):
                manifest_path = os.path.join(entry.path, "plugin.json")
                tools_file = os.path.join(entry.path, "tools.py")

                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)

                        plugin_id = manifest.get("id")
                        if not plugin_id:
                            logger.error(f"Plugin manifest in directory {entry.name} is missing 'id'.")
                            continue

                        # Check for duplicate registration
                        if plugin_id in self.loaded_plugins:
                            logger.error(f"Duplicate plugin found! Plugin ID '{plugin_id}' already registered.")
                            continue

                        # Check if disabled
                        if not manifest.get("enabled", True):
                            logger.info(f"Plugin '{plugin_id}' is disabled in manifest.")
                            continue

                        # Load tools if tools.py exists
                        tools_count = 0
                        if os.path.exists(tools_file):
                            module_name = f"plugins.{entry.name}.tools"
                            
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
                                    # Register in the global registry
                                    tool_registry.register_tool(tool_instance)
                                    tools_count += 1

                        self.loaded_plugins[plugin_id] = manifest
                        logger.info(f"Plugin '{plugin_id}' loaded successfully with {tools_count} tools.")

                    except Exception as e:
                        logger.exception(f"Failed to load plugin from folder {entry.name}:")

# Global Loader instance
plugin_loader = PluginLoader()
