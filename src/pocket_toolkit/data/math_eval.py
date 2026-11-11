"""Модуль безопасного вычисления математических выражений (Safe Math Evaluator).

Выполняет синтаксический анализ и вычисление арифметических выражений на базе
стандартного модуля ast без использования опасного eval(). Поддерживает базовые операторы,
переменные, вызовы математических функций и скобки.
"""

import ast
import math
import operator
from collections.abc import Callable, Mapping


# Исключения безопасного калькулятора
class MathEvaluationError(Exception):
    """Базовое исключение ошибки вычисления выражения."""


class MathSecurityError(MathEvaluationError):
    """Ошибка безопасности при попытке выполнения запрещенной конструкции AST."""


class UndefinedSymbolError(MathEvaluationError):
    """Ошибка обращения к неизвестной переменной или функции."""


# Разрешенные бинарные операции
_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Разрешенные унарные операции
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Стандартный безопасный набор функций из модуля math
_DEFAULT_FUNCTIONS: dict[str, Callable[..., float]] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
}

# Стандартные математические константы
_DEFAULT_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _eval_binary_op(
    node: ast.BinOp,
    variables: Mapping[str, float],
    functions: Mapping[str, Callable[..., float]],
) -> float:
    """Вычисляет результат бинарной операции."""
    op_type = type(node.op)
    if op_type not in _BINARY_OPERATORS:
        raise MathSecurityError(f"Запрещенный бинарный оператор: {op_type.__name__}")

    left_val = _eval_ast_node(node.left, variables, functions)
    right_val = _eval_ast_node(node.right, variables, functions)

    if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right_val == 0.0:
        raise MathEvaluationError("Деление на ноль")

    return _BINARY_OPERATORS[op_type](left_val, right_val)


def _eval_unary_op(
    node: ast.UnaryOp,
    variables: Mapping[str, float],
    functions: Mapping[str, Callable[..., float]],
) -> float:
    """Вычисляет результат унарной операции."""
    op_type = type(node.op)
    if op_type not in _UNARY_OPERATORS:
        raise MathSecurityError(f"Запрещенный унарный оператор: {op_type.__name__}")

    operand_val = _eval_ast_node(node.operand, variables, functions)
    return _UNARY_OPERATORS[op_type](operand_val)


def _eval_call(
    node: ast.Call,
    variables: Mapping[str, float],
    functions: Mapping[str, Callable[..., float]],
) -> float:
    """Вычисляет вызов разрешенной функции."""
    if not isinstance(node.func, ast.Name):
        raise MathSecurityError("Разрешены только прямые вызовы именованных функций")

    func_name = node.func.id
    if func_name not in functions:
        raise UndefinedSymbolError(f"Неизвестная функция: {func_name!r}")

    args = [_eval_ast_node(arg, variables, functions) for arg in node.args]
    try:
        return float(functions[func_name](*args))
    except Exception as exc:
        raise MathEvaluationError(f"Ошибка выполнения функции {func_name}: {exc}") from exc


def _eval_ast_node(
    node: ast.AST,
    variables: Mapping[str, float],
    functions: Mapping[str, Callable[..., float]],
) -> float:
    """Рекурсивно вычисляет безопасный AST узел."""
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise MathSecurityError(f"Запрещенный тип константы: {type(node.value).__name__}")
        return float(node.value)

    if isinstance(node, ast.Name):
        if node.id in variables:
            return float(variables[node.id])
        raise UndefinedSymbolError(f"Неопределенная переменная: {node.id!r}")

    if isinstance(node, ast.BinOp):
        return _eval_binary_op(node, variables, functions)

    if isinstance(node, ast.UnaryOp):
        return _eval_unary_op(node, variables, functions)

    if isinstance(node, ast.Call):
        return _eval_call(node, variables, functions)

    raise MathSecurityError(f"Недопустимая синтаксическая конструкция: {type(node).__name__}")


def evaluate_math(
    expression: str,
    variables: Mapping[str, float] | None = None,
    functions: Mapping[str, Callable[..., float]] | None = None,
) -> float:
    """Безопасно вычисляет математическое выражение.

    :param expression: Строка выражения (например, '2 * (x + 3) ^ 2' или 'sqrt(16) + 4').
    :param variables: Словарь доступных переменных.
    :param functions: Словарь пользовательских функций.
    :return: Результат вычисления в виде числа с плавающей точкой (float).
    :raises MathEvaluationError: При синтаксических ошибках, делении на ноль или неизвестных переменных.
    """
    if not isinstance(expression, str):
        raise TypeError(f"Выражение должно быть строкой, получено: {type(expression).__name__}")

    cleaned_expr = expression.strip()
    if not cleaned_expr:
        raise MathEvaluationError("Выражение не может быть пустым")

    # Поддержка альтернативного синтаксиса возведения в степень '^'
    normalized_expr = cleaned_expr.replace("^", "**")

    try:
        parsed_tree = ast.parse(normalized_expr, mode="eval")
    except SyntaxError as exc:
        raise MathEvaluationError(f"Синтаксическая ошибка в выражении: {exc.msg}") from exc

    merged_vars: dict[str, float] = dict(_DEFAULT_CONSTANTS)
    if variables:
        for k, v in variables.items():
            merged_vars[k] = float(v)

    merged_funcs: dict[str, Callable[..., float]] = dict(_DEFAULT_FUNCTIONS)
    if functions:
        merged_funcs.update(functions)

    return _eval_ast_node(parsed_tree.body, merged_vars, merged_funcs)
