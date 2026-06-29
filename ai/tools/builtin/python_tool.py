import abc
import subprocess
import sys
from typing import Any, Dict, List, Optional
from ai.tools.base_tool import BaseTool


class BasePythonSandbox(abc.ABC):
    """
    Abstract interface for Python sandbox execution environments.
    """

    @abc.abstractmethod
    def run(self, code: str, timeout: int = 5) -> Dict[str, Any]:
        """
        Executes Python code and returns output and execution status.
        """
        pass


class SubprocessPythonSandbox(BasePythonSandbox):
    """
    Concrete sandbox implementation executing Python code in an isolated subprocess.
    """

    def run(self, code: str, timeout: int = 5) -> Dict[str, Any]:
        try:
            # Run code in a separate process using the same python executable
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "success": proc.returncode == 0,
            }
        except subprocess.TimeoutExpired as te:
            return {
                "stdout": te.stdout or "",
                "stderr": te.stderr or "",
                "exit_code": -1,
                "success": False,
                "error": f"Execution timed out after {timeout} seconds.",
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "success": False,
                "error": f"Subprocess execution error: {str(e)}",
            }


class PythonTool(BaseTool):
    """
    Built-in tool for executing Python scripts in an isolated sandbox.
    """

    def __init__(self, sandbox: Optional[BasePythonSandbox] = None):
        self.sandbox = sandbox or SubprocessPythonSandbox()

    @property
    def tool_id(self) -> str:
        return "python_tool"

    @property
    def name(self) -> str:
        return "Python Code Executor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes a Python code snippet inside a separate process sandbox and returns stdout/stderr."

    @property
    def category(self) -> str:
        return "development"

    @property
    def tags(self) -> List[str]:
        return ["python", "code", "run", "sandbox"]

    @property
    def permissions(self) -> List[str]:
        return ["execute_code"]

    @property
    def timeout(self) -> int:
        return 10

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python source code to execute.",
                }
            },
            "required": ["code"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        code = kwargs.get("code", "")
        if not code:
            return {"success": False, "error": "No Python code provided."}

        # Execute using the sandboxed runner
        return self.sandbox.run(code, timeout=self.timeout)
