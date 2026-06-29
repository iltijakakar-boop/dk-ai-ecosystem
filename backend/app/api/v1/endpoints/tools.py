from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.response import APIResponse
from ai.tools.tool_registry import tool_registry
from ai.tools.tool_executor import tool_executor
from plugins.runtime.plugin_manager import plugin_manager
from plugins.runtime.plugin_loader import plugin_loader

router = APIRouter()

# Request schemas
class ToolExecuteRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Key-value arguments for tool execution.")
    session_id: Optional[str] = Field(None, description="Optional session/conversation ID.")
    agent_id: Optional[str] = Field(None, description="Optional agent calling the tool.")
    user_id: Optional[int] = Field(None, description="Optional user ID running the execution.")
    permissions: Optional[List[str]] = Field(None, description="Optional list of granted permissions for the execution context.")


class PluginInstallRequest(BaseModel):
    plugin_id: str = Field(..., description="Unique folder/name ID for the plugin.")
    manifest: Dict[str, Any] = Field(..., description="Details corresponding to plugin.json specifications.")
    tools_code: str = Field(..., description="Python source code containing tool classes for tools.py.")


class PluginToggleRequest(BaseModel):
    plugin_id: str = Field(..., description="The plugin ID to enable or disable.")


# Tool Endpoints
@router.get("/tools", response_model=APIResponse[List[Dict[str, Any]]])
def list_tools():
    """
    Returns metadata for all dynamically loaded tools.
    """
    try:
        # Re-trigger discoveries to catch filesystem adjustments
        tool_registry.discover_builtin_tools()
        plugin_loader.discover_and_load_plugins()
        return APIResponse(success=True, data=tool_registry.list_tools())
    except Exception as e:
        return APIResponse(success=False, error=str(e), message="Failed to list tools.")


@router.get("/tools/{tool_id}", response_model=APIResponse[Dict[str, Any]])
def get_tool_metadata(tool_id: str):
    """
    Returns specific tool specifications.
    """
    tool_registry.discover_builtin_tools()
    plugin_loader.discover_and_load_plugins()
    
    tool = tool_registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found or is disabled.")
        
    return APIResponse(
        success=True,
        data={
            "tool_id": tool.tool_id,
            "name": tool.name,
            "version": tool.version,
            "description": tool.description,
            "category": tool.category,
            "enabled": True,
            "author": tool.author,
            "license": tool.license,
            "tags": tool.tags,
            "permissions": tool.permissions,
            "timeout": tool.timeout,
            "parameters": tool.parameters
        }
    )


@router.post("/tools/{tool_id}/execute", response_model=APIResponse[Dict[str, Any]])
def execute_tool_call(tool_id: str, payload: ToolExecuteRequest):
    """
    Executes a specific tool after verifying arguments and permissions.
    """
    tool_registry.discover_builtin_tools()
    plugin_loader.discover_and_load_plugins()

    context = {
        "session_id": payload.session_id,
        "agent_id": payload.agent_id,
        "user_id": payload.user_id,
        "permissions": payload.permissions or []
    }
    
    res = tool_executor.execute_tool(
        tool_id=tool_id,
        arguments=payload.arguments,
        context=context
    )
    
    if not res["success"]:
        return APIResponse(
            success=False,
            error=res.get("error", "Execution failure."),
            message="Tool execution failed."
        )
        
    return APIResponse(
        success=True,
        data={"result": res["result"]},
        message="Tool execution finished successfully."
    )


# Plugin Endpoints
@router.get("/plugins", response_model=APIResponse[List[Dict[str, Any]]])
def list_plugins():
    """
    Returns all installed/loaded plugins.
    """
    try:
        plugins = plugin_manager.list_plugins()
        return APIResponse(success=True, data=plugins)
    except Exception as e:
        return APIResponse(success=False, error=str(e), message="Failed to list plugins.")


@router.post("/plugins/install", response_model=APIResponse[Dict[str, Any]])
def install_new_plugin(payload: PluginInstallRequest):
    """
    Installs a new plugin containing manifest specifications and python tools code.
    """
    success = plugin_manager.install_plugin(
        plugin_id=payload.plugin_id,
        manifest=payload.manifest,
        tools_py_content=payload.tools_code
    )
    if not success:
        return APIResponse(success=False, error="Failed to write plugin files or database entries.")
    return APIResponse(success=True, message=f"Plugin '{payload.plugin_id}' installed successfully.")


@router.post("/plugins/enable", response_model=APIResponse[Dict[str, Any]])
def enable_plugin_runtime(payload: PluginToggleRequest):
    """
    Enables a plugin and its tools.
    """
    success = plugin_manager.set_plugin_status(payload.plugin_id, enabled=True)
    if not success:
        return APIResponse(success=False, error=f"Could not enable plugin '{payload.plugin_id}'.")
    return APIResponse(success=True, message=f"Plugin '{payload.plugin_id}' enabled.")


@router.post("/plugins/disable", response_model=APIResponse[Dict[str, Any]])
def disable_plugin_runtime(payload: PluginToggleRequest):
    """
    Disables a plugin and its tools.
    """
    success = plugin_manager.set_plugin_status(payload.plugin_id, enabled=False)
    if not success:
        return APIResponse(success=False, error=f"Could not disable plugin '{payload.plugin_id}'.")
    return APIResponse(success=True, message=f"Plugin '{payload.plugin_id}' disabled.")


@router.delete("/plugins/{plugin_id}", response_model=APIResponse[Dict[str, Any]])
def uninstall_plugin_runtime(plugin_id: str):
    """
    Uninstalls a plugin and wipes its directory.
    """
    success = plugin_manager.uninstall_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to uninstall plugin '{plugin_id}'.")
    return APIResponse(success=True, message=f"Plugin '{plugin_id}' uninstalled.")
