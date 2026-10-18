"""Утилиты двоичного поиска в отсортированных последовательностях.

Предоставляет функции поиска граничных индексов (lower_bound, upper_bound),
точного диапазона (equal_range), первого и последнего вхождения элемента,
а также поиска в циклически сдвинутых массивах.
"""

from collections.abc import Callable, Sequence
from typing import Protocol, cast


class Comparable(Protocol):
    """Протокол для объектов, поддерживающих оператор строгого сравнения меньше (<)."""

    def __lt__(self, other: "Comparable", /) -> bool:
        """Сравнивает текущий объект с другим объектом на строгое неравенство меньше."""
        ...


def _validate_bounds(length: int, lo: int, hi: int | None) -> tuple[int, int]:
    """Проверяет корректность границ интервала поиска [lo, hi).

    :param length: Длина последовательности.
    :param lo: Начальный индекс.
    :param hi: Конечный индекс (или None для длины последовательности).
    :return: Кортеж валидированных индексов (lo, hi).
    :raises ValueError: Если границы некорректны или выходят за пределы.
    """
    if lo < 0:
        raise ValueError("Нижняя граница lo не может быть отрицательной")

    resolved_hi: int = length if hi is None else hi
    if resolved_hi < 0:
        raise ValueError("Верхняя граница hi не может быть отрицательной")

    if lo > resolved_hi:
        raise ValueError("Нижняя граница lo не может превышать верхнюю границу hi")

    if resolved_hi > length:
        raise ValueError("Верхняя граница hi не может превышать длину последовательности")

    return lo, resolved_hi


def _extract_key[T, K: Comparable](item: T, key: Callable[[T], K] | None) -> K:
    """Извлекает ключ сравнения из элемента с приведением типов.

    :param item: Элемент последовательности.
    :param key: Опциональная функция извлечения ключа.
    :return: Значение ключа для сравнения.
    """
    if key is not None:
        return key(item)
    return cast(K, item)


def _is_equal[K: Comparable](a: K, b: K) -> bool:
    """Проверяет равенство элементов через отношение строгого порядка."""
    return not (a < b) and not (b < a)


def _is_less_or_equal[K: Comparable](a: K, b: K) -> bool:
    """Проверяет условие a <= b через оператор строгого сравнения."""
    return not (b < a)


def lower_bound[T, K: Comparable](
    sequence: Sequence[T],
    target: K,
    *,
    key: Callable[[T], K] | None = None,
    lo: int = 0,
    hi: int | None = None,
) -> int:
    """Находит индекс первого элемента со значением не меньше target (>= target).

    Если все элементы диапазона строго меньше target, возвращает индекс hi.

    :param sequence: Отсортированная последовательность элементов.
    :param target: Искомое пороговое значение.
    :param key: Опциональная функция извлечения ключа сравнения из элемента.
    :param lo: Левая граница диапазона поиска (включительно, по умолчанию 0).
    :param hi: Правая граница диапазона (исключительно, по умолчанию len(sequence)).
    :return: Индекс первого подходящего элемента либо hi.
    :raises ValueError: Если границы диапазона некорректны.
    """
    valid_lo, valid_hi = _validate_bounds(len(sequence), lo, hi)

    while valid_lo < valid_hi:
        mid: int = (valid_lo + valid_hi) // 2
        mid_key: K = _extract_key(sequence[mid], key)
        if mid_key < target:
            valid_lo = mid + 1
        else:
            valid_hi = mid

    return valid_lo


def upper_bound[T, K: Comparable](
    sequence: Sequence[T],
    target: K,
    *,
    key: Callable[[T], K] | None = None,
    lo: int = 0,
    hi: int | None = None,
) -> int:
    """Находит индекс первого элемента со значением строго больше target (> target).

    Если в диапазоне нет элементов больше target, возвращает индекс hi.

    :param sequence: Отсортированная последовательность элементов.
    :param target: Искомое пороговое значение.
    :param key: Опциональная функция извлечения ключа сравнения из элемента.
    :param lo: Левая граница диапазона поиска (включительно, по умолчанию 0).
    :param hi: Правая граница диапазона (исключительно, по умолчанию len(sequence)).
    :return: Индекс первого элемента строго большего target либо hi.
    :raises ValueError: Если границы диапазона некорректны.
    """
    valid_lo, valid_hi = _validate_bounds(len(sequence), lo, hi)

    while valid_lo < valid_hi:
        mid: int = (valid_lo + valid_hi) // 2
        mid_key: K = _extract_key(sequence[mid], key)
        if target < mid_key:
            valid_hi = mid
        else:
            valid_lo = mid + 1

    return valid_lo


def equal_range[T, K: Comparable](
    sequence: Sequence[T],
    target: K,
    *,
    key: Callable[[T], K] | None = None,
    lo: int = 0,
    hi: int | None = None,
) -> tuple[int, int]:
    """Возвращает границы полуинтервала [first, last) элементов, равных target.

    :param sequence: Отсортированная последовательность элементов.
    :param target: Искомое значение.
    :param key: Опциональная функция извлечения ключа сравнения из элемента.
    :param lo: Левая граница диапазона поиска (включительно, по умолчанию 0).
    :param hi: Правая граница диапазона (исключительно, по умолчанию len(sequence)).
    :return: Кортеж (first, last) индексов. При отсутствии элемента first == last.
    :raises ValueError: Если границы диапазона некорректны.
    """
    valid_lo, valid_hi = _validate_bounds(len(sequence), lo, hi)
    first: int = lower_bound(sequence, target, key=key, lo=valid_lo, hi=valid_hi)
    last: int = upper_bound(sequence, target, key=key, lo=first, hi=valid_hi)
    return first, last


def binary_search[T, K: Comparable](
    sequence: Sequence[T],
    target: K,
    *,
    key: Callable[[T], K] | None = None,
    lo: int = 0,
    hi: int | None = None,
) -> int:
    """Выполняет двоичный поиск первого вхождения target в последовательности.

    :param sequence: Отсортированная последовательность элементов.
    :param target: Искомое значение.
    :param key: Опциональная функция извлечения ключа сравнения из элемента.
    :param lo: Левая граница диапазона поиска (включительно, по умолчанию 0).
    :param hi: Правая граница диапазона (исключительно, по умолчанию len(sequence)).
    :return: Индекс первого совпадающего элемента либо -1 при отсутствии.
    :raises ValueError: Если границы диапазона некорректны.
    """
    valid_lo, valid_hi = _validate_bounds(len(sequence), lo, hi)
    idx: int = lower_bound(sequence, target, key=key, lo=valid_lo, hi=valid_hi)
    if idx >= valid_hi:
        return -1

    item_key: K = _extract_key(sequence[idx], key)
    if _is_equal(item_key, target):
        return idx

    return -1


def binary_search_last[T, K: Comparable](
    sequence: Sequence[T],
    target: K,
    *,
    key: Callable[[T], K] | None = None,
    lo: int = 0,
    hi: int | None = None,
) -> int:
    """Выполняет двоичный поиск последнего вхождения target в последовательности.

    :param sequence: Отсортированная последовательность элементов.
    :param target: Искомое значение.
    :param key: Опциональная функция извлечения ключа сравнения из элемента.
    :param lo: Левая граница диапазона поиска (включительно, по умолчанию 0).
    :param hi: Правая граница диапазона (исключительно, по умолчанию len(sequence)).
    :return: Индекс последнего совпадающего элемента либо -1 при отсутствии.
    :raises ValueError: Если границы диапазона некорректны.
    """
    valid_lo, valid_hi = _validate_bounds(len(sequence), lo, hi)
    idx: int = upper_bound(sequence, target, key=key, lo=valid_lo, hi=valid_hi)
    last_idx: int = idx - 1
    if last_idx < valid_lo:
        return -1

    item_key: K = _extract_key(sequence[last_idx], key)
    if _is_equal(item_key, target):
        return last_idx

    return -1


def _search_rotated_range[T, K: Comparable](
    sequence: Sequence[T],
    target: K,
    key: Callable[[T], K] | None,
    left: int,
    right: int,
) -> int:
    """Вспомогательный цикл поиска в циклическом сдвиге диапазона [left, right].

    :param sequence: Последовательность элементов.
    :param target: Искомое значение.
    :param key: Опциональная функция извлечения ключа.
    :param left: Левый индекс (включительно).
    :param right: Правый индекс (включительно).
    :return: Индекс найденного элемента либо -1.
    """
    curr_left: int = left
    curr_right: int = right

    while curr_left <= curr_right:
        mid: int = (curr_left + curr_right) // 2
        mid_key: K = _extract_key(sequence[mid], key)
        if _is_equal(mid_key, target):
            return mid

        right_key: K = _extract_key(sequence[curr_right], key)

        if mid_key < right_key:
            if mid_key < target and _is_less_or_equal(target, right_key):
                curr_left = mid + 1
            else:
                curr_right = mid - 1
            continue

        if right_key < mid_key:
            left_key: K = _extract_key(sequence[curr_left], key)
            if _is_less_or_equal(left_key, target) and target < mid_key:
                curr_right = mid - 1
            else:
                curr_left = mid + 1
            continue

        curr_right -= 1

    return -1


def binary_search_rotated[T, K: Comparable](
    sequence: Sequence[T],
    target: K,
    *,
    key: Callable[[T], K] | None = None,
    lo: int = 0,
    hi: int | None = None,
) -> int:
    """Выполняет двоичный поиск в отсортированном массиве с циклическим сдвигом.

    Поддерживает поиск в массивах, сдвинутых на произвольное количество позиций,
    включая сценарии с повторяющимися элементами.

    :param sequence: Циклически сдвинутая отсортированная последовательность.
    :param target: Искомое значение.
    :param key: Опциональная функция извлечения ключа сравнения из элемента.
    :param lo: Левая граница диапазона поиска (включительно, по умолчанию 0).
    :param hi: Правая граница диапазона (исключительно, по умолчанию len(sequence)).
    :return: Индекс найденного элемента либо -1 при отсутствии.
    :raises ValueError: Если границы диапазона некорректны.
    """
    valid_lo, valid_hi = _validate_bounds(len(sequence), lo, hi)
    if valid_lo >= valid_hi:
        return -1

    return _search_rotated_range(sequence, target, key, valid_lo, valid_hi - 1)
