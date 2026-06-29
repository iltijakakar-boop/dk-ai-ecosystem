import os
import shutil
import json
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from app.config.settings import settings
from plugins.runtime.plugin_loader import plugin_loader
from ai.tools.tool_registry import tool_registry

class PluginManager:
    """
    Manages installing, uninstalling, enabling, disabling, and checking health of plugins,
    persisting states in the database.
    """
    
    def _get_db(self):
        from app.db.session import SessionLocal
        return SessionLocal()

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        Returns all discovered plugins with statuses merged from database.
        """
        # Discover latest in plugins folder
        plugin_loader.discover_and_load_plugins()
        
        db = self._get_db()
        db_statuses = {}
        try:
            from app.models.tool_model import Plugin as DBPlugin
            plugins = db.query(DBPlugin).all()
            db_statuses = {p.plugin_id: p.status for p in plugins}
        except Exception as e:
            logger.error(f"Failed to query plugins from database: {e}")
        finally:
            db.close()

        result = []
        for pid, manifest in plugin_loader.loaded_plugins.items():
            status = db_statuses.get(pid, "active" if manifest.get("enabled", True) else "disabled")
            result.append({
                "id": pid,
                "name": manifest.get("name", pid),
                "version": manifest.get("version", "1.0.0"),
                "author": manifest.get("author", "unknown"),
                "description": manifest.get("description", ""),
                "enabled": status == "active",
                "status": status,
                "dependencies": manifest.get("dependencies", []),
                "permissions": manifest.get("permissions", [])
            })
        return result

    def install_plugin(self, plugin_id: str, manifest: Dict[str, Any], tools_py_content: str) -> bool:
        """
        Creates a new plugin directory, writes manifest and tools.py, and registers in DB.
        """
        plugins_dir = plugin_loader.plugins_dir
        plugin_folder = os.path.join(plugins_dir, plugin_id)
        
        if os.path.exists(plugin_folder):
            logger.warning(f"Plugin folder '{plugin_id}' already exists.")
            return False

        try:
            os.makedirs(plugin_folder, exist_ok=True)
            
            # Write plugin.json
            with open(os.path.join(plugin_folder, "plugin.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
                
            # Write tools.py
            with open(os.path.join(plugin_folder, "tools.py"), "w", encoding="utf-8") as f:
                f.write(tools_py_content)
                
            # Write README.md
            with open(os.path.join(plugin_folder, "README.md"), "w", encoding="utf-8") as f:
                f.write(f"# {manifest.get('name', plugin_id)}\n\n{manifest.get('description', '')}")

            # Register in Database
            db = self._get_db()
            try:
                from app.models.tool_model import Plugin as DBPlugin
                db_plugin = db.query(DBPlugin).filter(DBPlugin.plugin_id == plugin_id).first()
                if not db_plugin:
                    db_plugin = DBPlugin(
                        plugin_id=plugin_id,
                        version=manifest.get("version", "1.0.0"),
                        status="active"
                    )
                    db.add(db_plugin)
                else:
                    db_plugin.status = "active"
                db.commit()
            except Exception as dbe:
                db.rollback()
                logger.error(f"Failed to record plugin install in DB: {dbe}")
            finally:
                db.close()

            # Reload plugins
            plugin_loader.discover_and_load_plugins()
            return True
            
        except Exception as e:
            logger.exception(f"Failed to install plugin '{plugin_id}':")
            # Cleanup folder on failure
            if os.path.exists(plugin_folder):
                shutil.rmtree(plugin_folder)
            return False

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """
        Removes plugin directory and unregisters the database status record.
        """
        plugin_folder = os.path.join(plugin_loader.plugins_dir, plugin_id)
        if not os.path.exists(plugin_folder):
            logger.warning(f"Plugin folder '{plugin_id}' not found.")
            return False

        try:
            # Delete folder
            shutil.rmtree(plugin_folder)
            
            # Remove from Loader cache
            plugin_loader.loaded_plugins.pop(plugin_id, None)

            # Delete from DB
            db = self._get_db()
            try:
                from app.models.tool_model import Plugin as DBPlugin
                db_plugin = db.query(DBPlugin).filter(DBPlugin.plugin_id == plugin_id).first()
                if db_plugin:
                    db.delete(db_plugin)
                    db.commit()
            except Exception as dbe:
                db.rollback()
                logger.error(f"Failed to delete plugin from DB: {dbe}")
            finally:
                db.close()

            # Re-discover to update registries
            plugin_loader.discover_and_load_plugins()
            return True
        except Exception as e:
            logger.exception(f"Failed to uninstall plugin '{plugin_id}':")
            return False

    def set_plugin_status(self, plugin_id: str, enabled: bool) -> bool:
        """
        Enables or disables plugin tools in memory registry and updates database state.
        """
        manifest = plugin_loader.loaded_plugins.get(plugin_id)
        if not manifest:
            logger.warning(f"Plugin '{plugin_id}' not loaded.")
            return False

        # Load tools from tools.py to identify which tools to enable/disable
        plugin_folder = os.path.join(plugin_loader.plugins_dir, plugin_id)
        tools_file = os.path.join(plugin_folder, "tools.py")
        
        tool_ids = []
        if os.path.exists(tools_file):
            # Read tool_id declarations by parsing file lines (simulated lookup)
            try:
                with open(tools_file, "r", encoding="utf-8") as tf:
                    content = tf.read()
                # Find occurrences of tool_id = "..." or return tool_id
                import re
                matches = re.findall(r'tool_id\s*[:=]\s*[\'"]([^\'"]+)[\'"]', content)
                tool_ids = list(set(matches))
            except Exception as parse_err:
                logger.error(f"Failed to parse tools file: {parse_err}")

        # Update Tool Registry enabled status
        for tid in tool_ids:
            if enabled:
                tool_registry.enable_tool(tid)
            else:
                tool_registry.disable_tool(tid)

        # Update Database
        db = self._get_db()
        try:
            from app.models.tool_model import Plugin as DBPlugin
            db_plugin = db.query(DBPlugin).filter(DBPlugin.plugin_id == plugin_id).first()
            target_status = "active" if enabled else "disabled"
            if db_plugin:
                db_plugin.status = target_status
            else:
                db_plugin = DBPlugin(
                    plugin_id=plugin_id,
                    version=manifest.get("version", "1.0.0"),
                    status=target_status
                )
                db.add(db_plugin)
            db.commit()
            
            # Sync manifest in-memory config
            plugin_loader.loaded_plugins[plugin_id]["enabled"] = enabled
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to toggle plugin status in DB: {e}")
            return False
        finally:
            db.close()

# Global Manager instance
plugin_manager = PluginManager()
