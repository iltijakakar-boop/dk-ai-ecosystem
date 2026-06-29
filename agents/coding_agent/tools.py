from ai.tools.base_tool import BaseTool
from typing import Any, Dict


class CodeLinterTool(BaseTool):
    """
    Validates Python syntax.
    """

    @property
    def tool_id(self) -> str:
        return "code_linter"

    @property
    def name(self) -> str:
        return "code_linter"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Checks a Python snippet for compile-time errors/warnings."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python source code to check.",
                }
            },
            "required": ["code"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        code = kwargs.get("code", "")
        if not code:
            return {"valid": False, "error": "No code provided."}
        try:
            compile(code, "<string>", "exec")
            return {"valid": True, "message": "Code compiled successfully."}
        except SyntaxError as e:
            return {"valid": False, "error": f"SyntaxError: {str(e)}"}
        except Exception as e:
            return {"valid": False, "error": f"Unknown compiler error: {str(e)}"}
