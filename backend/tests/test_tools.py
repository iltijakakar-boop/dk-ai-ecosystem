from ai.tools.tool_executor import tool_executor
from ai.tools.tool_registry import tool_registry
from fastapi.testclient import TestClient


def test_builtin_tool_discovery():
    """Verifies that all built-in tools are discovered and metadata is loaded."""
    tool_registry.discover_builtin_tools()
    tools = tool_registry.list_tools()
    tool_ids = [t["tool_id"] for t in tools]

    assert "web_search" in tool_ids
    assert "file_tool" in tool_ids
    assert "python_tool" in tool_ids
    assert "calculator" in tool_ids
    assert "datetime" in tool_ids
    assert "memory" in tool_ids


def test_calculator_tool_execution():
    """Tests basic math equations and zero-division error handling in CalculatorTool."""
    # Addition and Multiplication
    res = tool_executor.execute_tool("calculator", {"expression": "12 + 6 * 3"})
    assert res["success"] is True
    assert res["result"]["result"] == 30.0

    # Division by Zero
    res_zero = tool_executor.execute_tool("calculator", {"expression": "10 / 0"})
    assert res_zero["success"] is False
    assert "ZeroDivisionError" in res_zero["error"]


def test_python_tool_sandbox_execution():
    """Tests subprocess-based python environment output
    capture and timeout protections."""
    # Successful execution
    res = tool_executor.execute_tool(
        "python_tool",
        {"code": "print('Subprocess output works!')"},
        context={"permissions": ["execute_code"]},
    )
    assert res["success"] is True
    assert "Subprocess output works!" in res["result"]["stdout"]

    # Execution Timeout trigger
    res_sleep = tool_executor.execute_tool(
        "python_tool",
        {"code": "import time\ntime.sleep(0.5)\nprint('Done')"},
        context={"permissions": ["execute_code"]},
    )
    assert res_sleep["success"] is True
    assert "Done" in res_sleep["result"]["stdout"]


def test_file_tool_boundary_checks():
    """Tests read/write/delete permissions and directory traversal restrictions."""
    # Write file
    res_write = tool_executor.execute_tool(
        "file_tool",
        {
            "action": "write",
            "path": "scratch/pytest_io.txt",
            "content": "Ecosystem I/O test data",
        },
        context={"permissions": ["file_access"]},
    )
    assert res_write["success"] is True

    # Read file
    res_read = tool_executor.execute_tool(
        "file_tool",
        {"action": "read", "path": "scratch/pytest_io.txt"},
        context={"permissions": ["file_access"]},
    )
    assert res_read["success"] is True
    assert res_read["result"]["content"] == "Ecosystem I/O test data"

    # Directory Traversal Attempt outside Workspace
    res_traverse = tool_executor.execute_tool(
        "file_tool",
        {"action": "read", "path": "../../../sensitive.txt"},
        context={"permissions": ["file_access"]},
    )
    assert res_traverse["success"] is False
    assert "Access denied" in res_traverse["error"]

    # Delete file
    res_del = tool_executor.execute_tool(
        "file_tool",
        {"action": "delete", "path": "scratch/pytest_io.txt"},
        context={"permissions": ["file_access"]},
    )
    assert res_del["success"] is True


def test_permission_validation():
    """Verifies that permissions in context allow or block tool executions."""
    # Attempting to call WebSearchTool without search permission in context
    res_denied = tool_executor.execute_tool(
        "web_search", {"query": "quantum computing"}, context={"permissions": []}
    )
    assert res_denied["success"] is False
    assert "Permission denied" in res_denied["error"]

    # With search permission
    res_ok = tool_executor.execute_tool(
        "web_search",
        {"query": "quantum computing"},
        context={"permissions": ["search"]},
    )
    assert res_ok["success"] is True


def test_memory_systems_tool():
    """Tests stateful retrieval, creation, and deletion via MemoryTool."""
    # Save Key
    res_save = tool_executor.execute_tool(
        "memory",
        {
            "action": "save",
            "session_id": "test_sess_t",
            "key": "color",
            "value": "blue",
        },
    )
    assert res_save["success"] is True

    # Retrieve Key
    res_get = tool_executor.execute_tool(
        "memory", {"action": "retrieve", "session_id": "test_sess_t", "key": "color"}
    )
    assert res_get["success"] is True
    assert res_get["result"]["value"] == "blue"

    # Delete Key
    res_del = tool_executor.execute_tool(
        "memory", {"action": "delete", "session_id": "test_sess_t", "key": "color"}
    )
    assert res_del["success"] is True


def test_mcp_adapter():
    """Tests translation adapter formats to ensure MCP standard compatibility."""
    from ai.mcp.mcp_adapter import MCPAdapter

    tool = tool_registry.get_tool("calculator")
    assert tool is not None

    mcp_rep = MCPAdapter.to_mcp_tool(tool)
    assert mcp_rep.name == "calculator"
    assert mcp_rep.description == tool.description
    assert "expression" in mcp_rep.inputSchema["properties"]


def test_api_endpoints_tools_and_plugins(client: TestClient, db):
    """Tests API routes for tools discovery, execution,
    plugin installer, and controls."""
    # 1. GET /api/v1/tools
    res_list = client.get("/api/v1/tools")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["success"] is True
    tool_ids = [t["tool_id"] for t in list_data["data"]]
    assert "calculator" in tool_ids

    # 2. POST /api/v1/tools/calculator/execute
    res_exec = client.post(
        "/api/v1/tools/calculator/execute", json={"arguments": {"expression": "2 ** 5"}}
    )
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["success"] is True
    assert exec_data["data"]["result"]["result"] == 32

    # 3. POST /api/v1/plugins/install
    manifest = {
        "id": "test_plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "author": "DK AI Ecosystem",
        "description": "Mock plugin description.",
        "permissions": [],
        "dependencies": [],
        "enabled": True,
        "entry_point": "tools.py",
    }
    tools_code = """
from ai.tools.base_tool import BaseTool
from typing import Any, Dict

class TestPluginTool(BaseTool):
    @property
    def tool_id(self) -> str:
        return "plugin_test_tool"
    @property
    def name(self) -> str:
        return "Plugin Test Tool"
    @property
    def version(self) -> str:
        return "1.0.0"
    @property
    def description(self) -> str:
        return "Dynamic test tool."
    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}
    def execute(self, **kwargs) -> str:
        return "success"
"""
    res_inst = client.post(
        "/api/v1/plugins/install",
        json={
            "plugin_id": "test_plugin",
            "manifest": manifest,
            "tools_code": tools_code,
        },
    )
    assert res_inst.status_code == 200
    assert res_inst.json()["success"] is True

    # 4. GET /api/v1/plugins
    res_plugs = client.get("/api/v1/plugins")
    assert res_plugs.status_code == 200
    plugs_data = res_plugs.json()
    assert plugs_data["success"] is True
    plugin_ids = [p["id"] for p in plugs_data["data"]]
    assert "test_plugin" in plugin_ids

    # 5. POST /api/v1/plugins/disable
    res_disable = client.post(
        "/api/v1/plugins/disable", json={"plugin_id": "test_plugin"}
    )
    assert res_disable.status_code == 200
    assert res_disable.json()["success"] is True

    # 6. POST /api/v1/plugins/enable
    res_enable = client.post(
        "/api/v1/plugins/enable", json={"plugin_id": "test_plugin"}
    )
    assert res_enable.status_code == 200
    assert res_enable.json()["success"] is True

    # 7. DELETE /api/v1/plugins/test_plugin
    res_uninstall = client.delete("/api/v1/plugins/test_plugin")
    assert res_uninstall.status_code == 200
    assert res_uninstall.json()["success"] is True
