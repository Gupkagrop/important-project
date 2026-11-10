"""Модуль работы с диапазонами и интервалами (Intervals).

Предоставляет класс `Interval` для представления отрезков [start, end],
а также алгоритмы слияния перекрывающихся интервалов, поиска взаимных пересечений,
вставки нового отрезка и нахождения общего пересечения множества интервалов.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TypeVar

from pocket_toolkit.algorithms.binary_search import Comparable

T = TypeVar("T", bound=Comparable)


@dataclass(frozen=True, slots=True)
class Interval[T: Comparable]:
    """Неизменяемый замкнутый интервал [start, end].

    Поддерживает сравнение, проверку принадлежности точки и взаимного перекрытия.
    """

    start: T
    end: T

    def __post_init__(self) -> None:
        """Проверяет корректность границ отрезка."""
        if self.end < self.start:
            raise ValueError(
                f"Конец интервала ({self.end}) не может быть меньше начала ({self.start})"
            )

    def contains(self, point: T) -> bool:
        """Проверяет, попадает ли точка внутрь интервала [start, end].

        :param point: Проверяемое значение.
        :return: True, если point принадлежит [start, end], иначе False.
        """
        if point < self.start:
            return False
        return not (self.end < point)

    def contains_interval(self, other: "Interval[T]") -> bool:
        """Проверяет, полностью ли текущий интервал содержит другой интервал.

        :param other: Другой интервал.
        :return: True, если other целиком лежит внутри self.
        """
        if other.start < self.start:
            return False
        return not (self.end < other.end)

    def overlaps(self, other: "Interval[T]") -> bool:
        """Проверяет наличие непустого пересечения с другим отрезком.

        :param other: Другой интервал.
        :return: True, если отрезки пересекаются хотя бы в одной точке.
        """
        if self.end < other.start:
            return False
        return not (other.end < self.start)

    def intersection(self, other: "Interval[T]") -> "Interval[T] | None":
        """Находит пересечение текущего интервала с другим интервалом.

        :param other: Другой интервал.
        :return: Новый отрезок пересечения или None, если пересечение пусто.
        """
        if not self.overlaps(other):
            return None

        # max(self.start, other.start)
        new_start: T = max(self.start, other.start)
        # min(self.end, other.end)
        new_end: T = min(other.end, self.end)

        return Interval(start=new_start, end=new_end)

    def __lt__(self, other: "Interval[T]") -> bool:
        """Сравнивает интервалы по начальной точке, а при равенстве — по конечной."""
        if self.start < other.start:
            return True
        if other.start < self.start:
            return False
        return self.end < other.end


def merge_intervals[T: Comparable](intervals: Iterable[Interval[T]]) -> list[Interval[T]]:
    """Объединяет перекрывающиеся или смежные интервалы в упорядоченный список.

    Временная сложность: O(n log n) из-за предварительной сортировки.

    :param intervals: Последовательность интервалов.
    :return: Список объединенных неперекрывающихся интервалов.
    """
    sorted_intervals: list[Interval[T]] = sorted(intervals)
    if not sorted_intervals:
        return []

    merged: list[Interval[T]] = [sorted_intervals[0]]

    for current in sorted_intervals[1:]:
        last: Interval[T] = merged[-1]
        if current.start < last.end or current.start == last.end:
            # Интервалы пересекаются или касаются: расширяем правый конец
            new_end: T = max(last.end, current.end)
            merged[-1] = Interval(start=last.start, end=new_end)
        else:
            merged.append(current)

    return merged


def insert_interval[T: Comparable](
    intervals: Sequence[Interval[T]],
    new_interval: Interval[T],
) -> list[Interval[T]]:
    """Вставляет новый интервал в отсортированный список непересекающихся отрезков со слиянием.

    Временная сложность: O(n).

    :param intervals: Отсортированная последовательность непересекающихся интервалов.
    :param new_interval: Добавляемый интервал.
    :return: Новый список интервалов после вставки и слияния.
    """
    result: list[Interval[T]] = []
    i: int = 0
    total: int = len(intervals)

    # 1. Добавляем все интервалы, которые заканчиваются строго до начала new_interval
    while i < total and intervals[i].end < new_interval.start:
        result.append(intervals[i])
        i += 1

    # 2. Сливаем все интервалы, которые перекрываются с new_interval
    cur_start: T = new_interval.start
    cur_end: T = new_interval.end

    while i < total and not (cur_end < intervals[i].start):
        cur_start = min(cur_start, intervals[i].start)
        cur_end = max(cur_end, intervals[i].end)
        i += 1

    result.append(Interval(start=cur_start, end=cur_end))

    # 3. Добавляем оставшиеся интервалы
    while i < total:
        result.append(intervals[i])
        i += 1

    return result


def intersect_interval_lists[T: Comparable](
    first: Sequence[Interval[T]],
    second: Sequence[Interval[T]],
) -> list[Interval[T]]:
    """Вычисляет попарные пересечения двух отсортированных списков непересекающихся интервалов.

    Временная сложность: O(n + m).

    :param first: Первый список отсортированных интервалов.
    :param second: Второй список отсортированных интервалов.
    :return: Список взаимных пересечений.
    """
    result: list[Interval[T]] = []
    i: int = 0
    j: int = 0

    while i < len(first) and j < len(second):
        inter: Interval[T] | None = first[i].intersection(second[j])
        if inter is not None:
            result.append(inter)

        # Продвигаем указатель того интервала, который заканчивается раньше
        if first[i].end < second[j].end:
            i += 1
        else:
            j += 1

    return result


def common_intersection[T: Comparable](
    intervals: Iterable[Interval[T]],
) -> Interval[T] | None:
    """Находит общее пересечение всех переданных интервалов.

    :param intervals: Последовательность интервалов.
    :return: Интервал общего пересечения или None, если хотя бы два не пересекаются.
    """
    iterator = iter(intervals)
    try:
        common: Interval[T] = next(iterator)
    except StopIteration:
        return None

    for item in iterator:
        intersected: Interval[T] | None = common.intersection(item)
        if intersected is None:
            return None
        common = intersected

    return common
