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
from pocket_toolkit.algorithms.levenshtein import (
    AlignmentStep,
    EditOperation,
    damerau_levenshtein_distance,
    find_closest_matches,
    levenshtein_alignment,
    levenshtein_distance,
    levenshtein_matrix,
    levenshtein_similarity,
)

__all__: list[str] = [
    "AlignmentStep",
    "Comparable",
    "EditOperation",
    "binary_search",
    "binary_search_last",
    "binary_search_rotated",
    "damerau_levenshtein_distance",
    "equal_range",
    "find_closest_matches",
    "levenshtein_alignment",
    "levenshtein_distance",
    "levenshtein_matrix",
    "levenshtein_similarity",
    "lower_bound",
    "upper_bound",
]
