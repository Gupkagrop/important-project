"""Модуль вычисления расстояния Левенштейна и сходства последовательностей.

Предоставляет функции для расчета классического расстояния Левенштейна,
расстояния Дамерау-Левенштейна (с учетом перестановок соседних символов),
коэффициента сходства, полной матрицы динамического программирования,
пошагового выравнивания (edit script) и поиска наиболее похожих кандидатов.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum


class EditOperation(StrEnum):
    """Тип элементарной операции редактирования последовательности."""

    MATCH = "match"
    INSERT = "insert"
    DELETE = "delete"
    SUBSTITUTE = "substitute"
    TRANSPOSITION = "transposition"


@dataclass(frozen=True, slots=True)
class AlignmentStep[T]:
    """Элементарный шаг выравнивания между двумя последовательностями.

    Содержит тип операции и соответствующие элементы из исходной
    и целевой последовательностей (или None при вставке/удалении).
    """

    operation: EditOperation
    source: T | None
    target: T | None


def _validate_weights(weights: tuple[int, int, int]) -> tuple[int, int, int]:
    """Проверяет корректность весов операций (вставка, удаление, замена).

    :param weights: Кортеж стоимости (insert, delete, substitute).
    :return: Проверенный кортеж весов.
    :raises ValueError: Если кортеж имеет неверный размер или содержит отрицательные веса.
    """
    if len(weights) != 3:
        raise ValueError("Кортеж весов должен содержать ровно 3 элемента: (insert, delete, substitute)")

    insert_cost, delete_cost, substitute_cost = weights
    if insert_cost < 0 or delete_cost < 0 or substitute_cost < 0:
        raise ValueError("Стоимость операций редактирования не может быть отрицательной")

    return insert_cost, delete_cost, substitute_cost


def _calculate_max_cost(
    len1: int,
    len2: int,
    insert_cost: int,
    delete_cost: int,
    substitute_cost: int,
) -> int:
    """Вычисляет максимально возможную стоимость преобразования двух последовательностей."""
    if len1 == 0 and len2 == 0:
        return 0

    cost_all_del_ins: int = len1 * delete_cost + len2 * insert_cost
    min_len: int = min(len1, len2)
    diff_len: int = abs(len1 - len2)
    tail_cost: int = diff_len * (insert_cost if len2 > len1 else delete_cost)
    cost_sub_and_tail: int = min_len * substitute_cost + tail_cost

    return min(cost_all_del_ins, cost_sub_and_tail)


def levenshtein_matrix[T](
    s1: Sequence[T],
    s2: Sequence[T],
    *,
    weights: tuple[int, int, int] = (1, 1, 1),
) -> list[list[int]]:
    """Вычисляет полную матрицу динамического программирования расстояния Левенштейна.

    :param s1: Исходная последовательность.
    :param s2: Целевая последовательность.
    :param weights: Кортеж стоимости операций (вставка, удаление, замена).
    :return: Двумерный массив размера (len(s1) + 1) x (len(s2) + 1).
    :raises ValueError: При некорректных весах.
    """
    insert_cost, delete_cost, substitute_cost = _validate_weights(weights)
    len1: int = len(s1)
    len2: int = len(s2)

    matrix: list[list[int]] = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for j in range(len2 + 1):
        matrix[0][j] = j * insert_cost
    for i in range(1, len1 + 1):
        matrix[i][0] = i * delete_cost

    for i in range(1, len1 + 1):
        char1: T = s1[i - 1]
        for j in range(1, len2 + 1):
            char2: T = s2[j - 1]
            sub_cost: int = 0 if char1 == char2 else substitute_cost
            cost_del: int = matrix[i - 1][j] + delete_cost
            cost_ins: int = matrix[i][j - 1] + insert_cost
            cost_sub: int = matrix[i - 1][j - 1] + sub_cost
            matrix[i][j] = min(cost_del, cost_ins, cost_sub)

    return matrix


def levenshtein_distance[T](
    s1: Sequence[T],
    s2: Sequence[T],
    *,
    weights: tuple[int, int, int] = (1, 1, 1),
    max_distance: int | None = None,
) -> int:
    """Вычисляет редакционное расстояние Левенштейна между двумя последовательностями.

    Использует оптимизацию по памяти O(min(len(s1), len(s2))) и раннее завершение,
    если задан порог max_distance.

    :param s1: Первая последовательность (строка, список, кортеж).
    :param s2: Вторая последовательность.
    :param weights: Веса операций (вставка, удаление, замена).
    :param max_distance: Максимальный порог расстояния для раннего выхода.
    :return: Минимальная стоимость преобразования s1 в s2.
    :raises ValueError: Если max_distance отрицателен или веса некорректны.
    """
    insert_cost, delete_cost, substitute_cost = _validate_weights(weights)
    if max_distance is not None and max_distance < 0:
        raise ValueError("Параметр max_distance не может быть отрицательным")

    if s1 == s2:
        return 0

    len1, len2 = len(s1), len(s2)
    if len1 == 0:
        dist: int = len2 * insert_cost
        return dist if max_distance is None or dist <= max_distance else max_distance + 1
    if len2 == 0:
        dist = len1 * delete_cost
        return dist if max_distance is None or dist <= max_distance else max_distance + 1

    # Быстрая проверка минимально возможного изменения длины
    min_possible_cost: int = abs(len1 - len2) * (insert_cost if len2 > len1 else delete_cost)
    if max_distance is not None and min_possible_cost > max_distance:
        return max_distance + 1

    return _compute_distance_rows(s1, s2, insert_cost, delete_cost, substitute_cost, max_distance)


def _compute_distance_rows[T](
    s1: Sequence[T],
    s2: Sequence[T],
    insert_cost: int,
    delete_cost: int,
    substitute_cost: int,
    max_distance: int | None,
) -> int:
    """Инкрементальный расчет расстояния с использованием двух строк."""
    len1, len2 = len(s1), len(s2)
    prev_row: list[int] = [j * insert_cost for j in range(len2 + 1)]
    curr_row: list[int] = [0] * (len2 + 1)

    for i in range(1, len1 + 1):
        curr_row[0] = i * delete_cost
        elem1: T = s1[i - 1]

        for j in range(1, len2 + 1):
            elem2: T = s2[j - 1]
            sub_cost: int = 0 if elem1 == elem2 else substitute_cost
            curr_row[j] = min(
                prev_row[j] + delete_cost,
                curr_row[j - 1] + insert_cost,
                prev_row[j - 1] + sub_cost,
            )

        if max_distance is not None and min(curr_row) > max_distance:
            return max_distance + 1

        prev_row, curr_row = curr_row, prev_row

    final_dist: int = prev_row[len2]
    if max_distance is not None and final_dist > max_distance:
        return max_distance + 1
    return final_dist


def damerau_levenshtein_distance[T](
    s1: Sequence[T],
    s2: Sequence[T],
    *,
    max_distance: int | None = None,
) -> int:
    """Вычисляет расстояние Дамерау-Левенштейна (OSA — Optimal String Alignment).

    Учитывает 4 операции: вставка, удаление, замена и перестановка двух
    соседних элементов с единичными весами.

    :param s1: Исходная последовательность.
    :param s2: Целевая последовательность.
    :param max_distance: Опциональный порог расстояния для раннего выхода.
    :return: Минимальное количество операций.
    :raises ValueError: Если max_distance отрицателен.
    """
    if max_distance is not None and max_distance < 0:
        raise ValueError("Параметр max_distance не может быть отрицательным")

    if s1 == s2:
        return 0

    len1, len2 = len(s1), len(s2)
    if len1 == 0:
        return len2 if max_distance is None or len2 <= max_distance else max_distance + 1
    if len2 == 0:
        return len1 if max_distance is None or len1 <= max_distance else max_distance + 1

    if max_distance is not None and abs(len1 - len2) > max_distance:
        return max_distance + 1

    return _compute_damerau_osa(s1, s2, max_distance)


def _compute_damerau_osa[T](
    s1: Sequence[T],
    s2: Sequence[T],
    max_distance: int | None,
) -> int:
    """Вспомогательный расчет расстояния Дамерау-Левенштейна (OSA)."""
    len1, len2 = len(s1), len(s2)
    row_prev2: list[int] = [0] * (len2 + 1)
    row_prev1: list[int] = list(range(len2 + 1))
    row_curr: list[int] = [0] * (len2 + 1)

    for i in range(1, len1 + 1):
        row_curr[0] = i
        elem1: T = s1[i - 1]

        for j in range(1, len2 + 1):
            elem2: T = s2[j - 1]
            cost: int = 0 if elem1 == elem2 else 1
            best: int = min(
                row_prev1[j] + 1,
                row_curr[j - 1] + 1,
                row_prev1[j - 1] + cost,
            )

            if i > 1 and j > 1 and elem1 == s2[j - 2] and s1[i - 2] == elem2:
                best = min(best, row_prev2[j - 2] + 1)

            row_curr[j] = best

        if max_distance is not None and min(row_curr) > max_distance:
            return max_distance + 1

        row_prev2, row_prev1, row_curr = row_prev1, row_curr, row_prev2

    res: int = row_prev1[len2]
    if max_distance is not None and res > max_distance:
        return max_distance + 1
    return res


def levenshtein_similarity[T](
    s1: Sequence[T],
    s2: Sequence[T],
    *,
    weights: tuple[int, int, int] = (1, 1, 1),
) -> float:
    """Вычисляет нормированный коэффициент сходства двух последовательностей [0.0, 1.0].

    Значение 1.0 означает полное совпадение последовательностей, 0.0 — полное несовпадение.

    :param s1: Первая последовательность.
    :param s2: Вторая последовательность.
    :param weights: Кортеж весов операций (вставка, удаление, замена).
    :return: Коэффициент сходства в диапазоне от 0.0 до 1.0.
    """
    insert_cost, delete_cost, substitute_cost = _validate_weights(weights)
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    max_cost: int = _calculate_max_cost(len1, len2, insert_cost, delete_cost, substitute_cost)
    if max_cost == 0:
        return 1.0

    distance: int = levenshtein_distance(s1, s2, weights=weights)
    similarity: float = 1.0 - (distance / max_cost)
    return max(0.0, min(1.0, round(similarity, 6)))


def levenshtein_alignment[T](
    s1: Sequence[T],
    s2: Sequence[T],
    *,
    weights: tuple[int, int, int] = (1, 1, 1),
) -> list[AlignmentStep[T]]:
    """Строит оптимальную последовательность шагов редактирования (alignment/edit script).

    :param s1: Исходная последовательность.
    :param s2: Целевая последовательность.
    :param weights: Веса операций (вставка, удаление, замена).
    :return: Список шагов выравнивания AlignmentStep от начала к концу.
    """
    insert_cost, delete_cost, substitute_cost = _validate_weights(weights)
    matrix: list[list[int]] = levenshtein_matrix(s1, s2, weights=weights)

    return _backtrack_alignment(s1, s2, matrix, insert_cost, delete_cost, substitute_cost)


def _backtrack_alignment[T](
    s1: Sequence[T],
    s2: Sequence[T],
    matrix: list[list[int]],
    insert_cost: int,
    delete_cost: int,
    substitute_cost: int,
) -> list[AlignmentStep[T]]:
    """Обратный проход по матрице для восстановления выравнивания."""
    steps: list[AlignmentStep[T]] = []
    i: int = len(s1)
    j: int = len(s2)

    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i - 1] == s2[j - 1] and matrix[i][j] == matrix[i - 1][j - 1]:
            steps.append(AlignmentStep(EditOperation.MATCH, s1[i - 1], s2[j - 1]))
            i -= 1
            j -= 1
            continue

        if i > 0 and j > 0 and matrix[i][j] == matrix[i - 1][j - 1] + substitute_cost:
            steps.append(AlignmentStep(EditOperation.SUBSTITUTE, s1[i - 1], s2[j - 1]))
            i -= 1
            j -= 1
            continue

        if i > 0 and matrix[i][j] == matrix[i - 1][j] + delete_cost:
            steps.append(AlignmentStep(EditOperation.DELETE, s1[i - 1], None))
            i -= 1
            continue

        if j > 0 and matrix[i][j] == matrix[i][j - 1] + insert_cost:
            steps.append(AlignmentStep(EditOperation.INSERT, None, s2[j - 1]))
            j -= 1
            continue

        break

    steps.reverse()
    return steps


def find_closest_matches[T: Sequence](
    query: T,
    candidates: Iterable[T],
    *,
    n: int = 3,
    min_similarity: float = 0.0,
    weights: tuple[int, int, int] = (1, 1, 1),
) -> list[tuple[T, float]]:
    """Находит наиболее похожие последовательности среди кандидатов по коэффициенту сходства.

    :param query: Искомая последовательность.
    :param candidates: Итерируемый набор кандидатов.
    :param n: Максимальное количество возвращаемых результатов.
    :param min_similarity: Минимальный порог сходства (от 0.0 до 1.0).
    :param weights: Веса операций редактирования.
    :return: Список пар (кандидат, сходство), отсортированный по убыванию сходства.
    :raises ValueError: Если n отрицателен или min_similarity вне диапазона [0.0, 1.0].
    """
    if n < 0:
        raise ValueError("Количество результатов n не может быть отрицательным")
    if not (0.0 <= min_similarity <= 1.0):
        raise ValueError("Минимальное сходство min_similarity должно быть в диапазоне от 0.0 до 1.0")

    if n == 0:
        return []

    results: list[tuple[T, float]] = []
    for cand in candidates:
        sim: float = levenshtein_similarity(query, cand, weights=weights)
        if sim >= min_similarity:
            results.append((cand, sim))

    # Стабильная сортировка по убыванию сходства
    results.sort(key=lambda item: item[1], reverse=True)
    return results[:n]
