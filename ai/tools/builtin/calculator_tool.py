import ast
import operator
from typing import Any, Dict, List
from ai.tools.base_tool import BaseTool


class CalculatorTool(BaseTool):
    """
    Built-in safe mathematical calculator tool.
    """

    # Map AST operators to safe callables
    _ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    @property
    def tool_id(self) -> str:
        return "calculator"

    @property
    def name(self) -> str:
        return "Math Calculator"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Calculates basic mathematical expressions safely (supports +, -, *, /, **)."

    @property
    def category(self) -> str:
        return "utility"

    @property
    def tags(self) -> List[str]:
        return ["math", "calculator", "eval"]

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
                "expression": {
                    "type": "string",
                    "description": "The math expression string to calculate (e.g. '2 * (3 + 4)').",
                }
            },
            "required": ["expression"],
        }

    def _safe_eval(self, node: ast.AST) -> float:
        if isinstance(node, ast.Num):  # compatibility python < 3.8
            return node.n
        elif isinstance(node, ast.Constant):  # python >= 3.8
            if not isinstance(node.value, (int, float)):
                raise TypeError(f"Constant value '{node.value}' must be a number.")
            return node.value
        elif isinstance(node, ast.BinOp):
            op_cls = type(node.op)
            if op_cls not in self._ALLOWED_OPERATORS:
                raise NotImplementedError(
                    f"Unsupported math operator: {op_cls.__name__}"
                )
            left_val = self._safe_eval(node.left)
            right_val = self._safe_eval(node.right)

            # Prevent DivisionByZero or execution size overflow
            if op_cls == ast.Div and right_val == 0:
                raise ZeroDivisionError("Division by zero is not allowed.")
            if op_cls == ast.Pow and (abs(left_val) > 1000 or abs(right_val) > 100):
                raise ValueError(
                    "Exponentiation limits exceeded to prevent CPU overflow."
                )

            return self._ALLOWED_OPERATORS[op_cls](left_val, right_val)
        elif isinstance(node, ast.UnaryOp):
            op_cls = type(node.op)
            if op_cls not in self._ALLOWED_OPERATORS:
                raise NotImplementedError(
                    f"Unsupported unary operator: {op_cls.__name__}"
                )
            operand_val = self._safe_eval(node.operand)
            return self._ALLOWED_OPERATORS[op_cls](operand_val)
        else:
            raise TypeError(f"Invalid syntax node detected: {type(node).__name__}")

    def execute(self, **kwargs) -> Dict[str, Any]:
        expression = kwargs.get("expression", "")
        if not expression:
            raise ValueError("Expression parameter is empty.")

        # Remove spaces
        expr_stripped = "".join(expression.split())
        tree = ast.parse(expr_stripped, mode="eval")
        res_val = self._safe_eval(tree.body)
        return {"expression": expression, "result": res_val}
