import os
from typing import Any, Dict, List
from ai.tools.base_tool import BaseTool


class FileTool(BaseTool):
    """
    Built-in tool for secure file operations within the workspace root.
    """

    @property
    def tool_id(self) -> str:
        return "file_tool"

    @property
    def name(self) -> str:
        return "File Management Tool"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Allows reading, writing, creating folders, and deleting files within the workspace root."

    @property
    def category(self) -> str:
        return "system"

    @property
    def tags(self) -> List[str]:
        return ["file", "io", "directory"]

    @property
    def permissions(self) -> List[str]:
        # Minimum permission required to execute the tool
        return ["file_access"]

    @property
    def timeout(self) -> int:
        return 5

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "create_folder", "delete"],
                    "description": "The file action to perform.",
                },
                "path": {
                    "type": "string",
                    "description": "Relative path to the file or directory.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (required only for write action).",
                },
            },
            "required": ["action", "path"],
        }

    def _resolve_safe_path(self, relative_path: str) -> str:
        workspace_root = os.path.abspath("c:\\Projects\\dk-ai-ecosystem")
        target_path = os.path.abspath(os.path.join(workspace_root, relative_path))
        if not target_path.startswith(workspace_root):
            raise PermissionError("Access denied: path is outside the workspace root.")
        return target_path

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action")
        rel_path = kwargs.get("path", "")
        content = kwargs.get("content", "")

        target_path = self._resolve_safe_path(rel_path)

        if action == "read":
            if not os.path.exists(target_path):
                raise FileNotFoundError(f"File '{rel_path}' does not exist.")
            if os.path.isdir(target_path):
                raise IsADirectoryError("Path points to a directory, not a file.")
            with open(target_path, "r", encoding="utf-8") as f:
                data = f.read()
            return {"content": data}

        elif action == "write":
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"message": f"Successfully wrote to file '{rel_path}'."}

        elif action == "create_folder":
            os.makedirs(target_path, exist_ok=True)
            return {"message": f"Successfully created folder '{rel_path}'."}

        elif action == "delete":
            if not os.path.exists(target_path):
                raise FileNotFoundError(f"Path '{rel_path}' does not exist.")

            if os.path.isdir(target_path):
                os.rmdir(target_path)
                return {"message": f"Successfully deleted directory '{rel_path}'."}
            else:
                os.remove(target_path)
                return {"message": f"Successfully deleted file '{rel_path}'."}
        else:
            raise ValueError(f"Unsupported action '{action}'.")
