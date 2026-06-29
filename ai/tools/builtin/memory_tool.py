from typing import Any, Dict, List
from ai.tools.base_tool import BaseTool


class MemoryTool(BaseTool):
    """
    Built-in memory utility tool for saving, retrieving, and deleting state keys.
    """

    # Class-level in-memory key-value store
    _memory_store: Dict[str, Dict[str, Any]] = {}

    @property
    def tool_id(self) -> str:
        return "memory"

    @property
    def name(self) -> str:
        return "Memory Manager"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Allows saving, retrieving, and deleting key-value variables scoped to a session."

    @property
    def category(self) -> str:
        return "utility"

    @property
    def tags(self) -> List[str]:
        return ["memory", "state", "context"]

    @property
    def permissions(self) -> List[str]:
        return []

    @property
    def timeout(self) -> int:
        return 2

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["save", "retrieve", "delete"],
                    "description": "The memory operation to execute.",
                },
                "session_id": {
                    "type": "string",
                    "description": "The unique session identifier.",
                },
                "key": {"type": "string", "description": "The variable key."},
                "value": {
                    "type": "string",
                    "description": "The variable value (required only for 'save' action).",
                },
            },
            "required": ["action", "session_id", "key"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action")
        session_id = kwargs.get("session_id")
        key = kwargs.get("key")
        value = kwargs.get("value")

        if session_id not in self._memory_store:
            self._memory_store[session_id] = {}

        if action == "save":
            if value is None:
                return {
                    "success": False,
                    "error": "Value parameter is required for 'save' action.",
                }
            self._memory_store[session_id][key] = value
            return {
                "success": True,
                "message": f"Saved key '{key}' for session '{session_id}'.",
            }

        elif action == "retrieve":
            val = self._memory_store[session_id].get(key)
            if val is None:
                return {
                    "success": False,
                    "error": f"Key '{key}' not found in session '{session_id}'.",
                }
            return {"success": True, "key": key, "value": val}

        elif action == "delete":
            if key in self._memory_store[session_id]:
                del self._memory_store[session_id][key]
                return {
                    "success": True,
                    "message": f"Deleted key '{key}' from session '{session_id}'.",
                }
            else:
                return {
                    "success": False,
                    "error": f"Key '{key}' not found in session '{session_id}'.",
                }
        else:
            return {"success": False, "error": f"Invalid action: {action}"}
