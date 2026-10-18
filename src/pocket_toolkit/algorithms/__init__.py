"""Пакет алгоритмов и вычислительных утилит Pocket Toolkit."""

from pocket_toolkit.algorithms.binary_search import (
    Comparable,
    binary_search,
    binary_search_last,
    binary_search_rotated,
    equal_range,
    lower_bound,
    upper_bound,
)

__all__: list[str] = [
    "Comparable",
    "binary_search",
    "binary_search_last",
    "binary_search_rotated",
    "equal_range",
    "lower_bound",
    "upper_bound",
]
