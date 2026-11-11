"""Пакет манипуляции структурами данных и словарями Pocket Toolkit."""

from pocket_toolkit.data.csv_stream import (
    CSVParseError,
    generate_csv_from_dicts,
    generate_csv_line,
    generate_csv_stream,
    parse_csv_dicts,
    parse_csv_stream,
)
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
    "CSVParseError",
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
    "generate_csv_from_dicts",
    "generate_csv_line",
    "generate_csv_stream",
    "parse_csv_dicts",
    "parse_csv_stream",
    "unflatten_dict",
]
