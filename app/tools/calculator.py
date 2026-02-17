from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class CalculatorResult:
    ok: bool
    expression: str
    result: float | None = None
    error: str | None = None


_ALLOWED_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a**b,
}

_ALLOWED_UNARY_OPS = {
    ast.UAdd: lambda x: x,
    ast.USub: lambda x: -x,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        value = _eval_node(node.operand)
        return _ALLOWED_UNARY_OPS[type(node.op)](value)

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)

    raise ValueError("Unsupported expression")


def calculate(expression: str) -> CalculatorResult:
    try:
        parsed = ast.parse(expression.strip(), mode="eval")
        value = _eval_node(parsed)
        return CalculatorResult(ok=True, expression=expression, result=value)
    except Exception as exc:
        return CalculatorResult(ok=False, expression=expression, error=str(exc))
