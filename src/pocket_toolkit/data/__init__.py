"""Пакет манипуляции структурами данных и словарями Pocket Toolkit."""

from pocket_toolkit.data.flatten import (
    flatten_dict,
    unflatten_dict,
)
from pocket_toolkit.data.merge import (
    DELETE_FIELD,
    deep_merge,
    deep_patch,
)

__all__: list[str] = [
    "DELETE_FIELD",
    "deep_merge",
    "deep_patch",
    "flatten_dict",
    "unflatten_dict",
]
