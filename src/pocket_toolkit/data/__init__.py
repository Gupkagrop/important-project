"""Пакет манипуляции структурами данных и словарями Pocket Toolkit."""

from pocket_toolkit.data.diff import (
    DictDiff,
    diff_dict,
    find_dict_delta,
)
from pocket_toolkit.data.flatten import (
    flatten_dict,
    unflatten_dict,
)
from pocket_toolkit.data.math_eval import (
    MathEvaluationError,
    MathSecurityError,
    UndefinedSymbolError,
    evaluate_math,
)
from pocket_toolkit.data.merge import (
    DELETE_FIELD,
    deep_merge,
    deep_patch,
)

__all__: list[str] = [
    "DELETE_FIELD",
    "DictDiff",
    "MathEvaluationError",
    "MathSecurityError",
    "UndefinedSymbolError",
    "deep_merge",
    "deep_patch",
    "diff_dict",
    "evaluate_math",
    "find_dict_delta",
    "flatten_dict",
    "unflatten_dict",
]
