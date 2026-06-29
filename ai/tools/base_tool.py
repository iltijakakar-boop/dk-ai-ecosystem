import abc
from typing import Any, Dict, List

class BaseTool(abc.ABC):
    """
    Abstract base class for all agent tools/plugins.
    """
    
    @property
    @abc.abstractmethod
    def tool_id(self) -> str:
        """Unique identifier for the tool."""
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable name of the tool."""
        pass

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Tool version string."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """A description of what the tool does and when to use it."""
        pass

    @property
    def category(self) -> str:
        """Category grouping of the tool."""
        return "utility"

    @property
    def enabled(self) -> bool:
        """Whether the tool is enabled."""
        return True

    @property
    @abc.abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema defining the tool's expected input parameters."""
        pass

    @property
    def author(self) -> str:
        """Author of the tool."""
        return "DK AI Ecosystem"

    @property
    def license(self) -> str:
        """License of the tool."""
        return "MIT"

    @property
    def tags(self) -> List[str]:
        """List of descriptive tags."""
        return []

    @property
    def permissions(self) -> List[str]:
        """Required permissions list."""
        return []

    @property
    def timeout(self) -> int:
        """Maximum execution timeout in seconds."""
        return 5

    @abc.abstractmethod
    def execute(self, **kwargs) -> Any:
        """Executes the tool's core logic and returns a result."""
        pass

    def validate(self, arguments: Dict[str, Any]) -> bool:
        """
        Validates the arguments against the parameter JSON Schema.
        """
        # Checks if all required parameters are present in arguments
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})
        
        for r in required:
            if r not in arguments:
                raise ValueError(f"Missing required parameter: {r}")
                
        # Validate parameter types
        for k, v in arguments.items():
            if k in properties:
                expected_type = properties[k].get("type")
                if expected_type == "string" and not isinstance(v, str):
                    raise TypeError(f"Parameter '{k}' must be a string.")
                elif expected_type == "number" and not isinstance(v, (int, float)):
                    raise TypeError(f"Parameter '{k}' must be a number.")
                elif expected_type == "integer" and not isinstance(v, int):
                    raise TypeError(f"Parameter '{k}' must be an integer.")
                elif expected_type == "boolean" and not isinstance(v, bool):
                    raise TypeError(f"Parameter '{k}' must be a boolean.")
                elif expected_type == "object" and not isinstance(v, dict):
                    raise TypeError(f"Parameter '{k}' must be an object.")
                elif expected_type == "array" and not isinstance(v, list):
                    raise TypeError(f"Parameter '{k}' must be an array.")
                    
        return True

    def before_execute(self, *args, **kwargs):
        """Hook executed before running core tool logic."""
        pass

    def after_execute(self, result: Any) -> Any:
        """Hook executed after running core tool logic to process/format the output."""
        return result
