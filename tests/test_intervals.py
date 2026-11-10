"""Модульные тесты для модуля работы с интервалами (intervals)."""

import pytest

from pocket_toolkit.algorithms.intervals import (
    Interval,
    common_intersection,
    insert_interval,
    intersect_interval_lists,
    merge_intervals,
)


def test_interval_creation_and_validation() -> None:
    """Проверка создания корректных и некорректных интервалов."""
    inter = Interval(1, 5)
    assert inter.start == 1
    assert inter.end == 5

    # Вырожденный интервал-точка
    point_inter = Interval(3, 3)
    assert point_inter.start == 3
    assert point_inter.end == 3

    # Некорректный интервал: start > end
    with pytest.raises(ValueError):
        Interval(10, 5)


def test_interval_contains_point() -> None:
    """Проверка попадания точки в отрезок."""
    inter = Interval(2, 8)
    assert inter.contains(2) is True
    assert inter.contains(5) is True
    assert inter.contains(8) is True
    assert inter.contains(1) is False
    assert inter.contains(9) is False


def test_interval_contains_interval() -> None:
    """Проверка вложенности интервалов."""
    outer = Interval(0, 10)
    inner = Interval(2, 5)
    exact = Interval(0, 10)
    overlapping = Interval(5, 12)
    disjoint = Interval(15, 20)

    assert outer.contains_interval(inner) is True
    assert outer.contains_interval(exact) is True
    assert outer.contains_interval(overlapping) is False
    assert outer.contains_interval(disjoint) is False
    assert inner.contains_interval(outer) is False


def test_interval_overlaps_and_intersection() -> None:
    """Проверка пересечения интервалов."""
    a = Interval(1, 6)
    b = Interval(4, 10)
    c = Interval(6, 12)  # Касание в точке 6
    d = Interval(7, 12)  # Не пересекаются

    assert a.overlaps(b) is True
    assert a.intersection(b) == Interval(4, 6)

    assert a.overlaps(c) is True
    assert a.intersection(c) == Interval(6, 6)

    assert a.overlaps(d) is False
    assert a.intersection(d) is None


def test_interval_sorting() -> None:
    """Проверка упорядочивания интервалов."""
    intervals = [Interval(5, 7), Interval(1, 3), Interval(1, 2), Interval(3, 4)]
    sorted_intervals = sorted(intervals)
    assert sorted_intervals == [Interval(1, 2), Interval(1, 3), Interval(3, 4), Interval(5, 7)]


def test_merge_intervals() -> None:
    """Проверка объединения перекрывающихся интервалов."""
    assert merge_intervals([]) == []
    assert merge_intervals([Interval(1, 4)]) == [Interval(1, 4)]

    # Смешанные интервалы с перекрытиями и касаниями
    data = [
        Interval(1, 3),
        Interval(2, 6),
        Interval(8, 10),
        Interval(15, 18),
        Interval(6, 7),
    ]
    merged = merge_intervals(data)
    assert merged == [Interval(1, 7), Interval(8, 10), Interval(15, 18)]

    # Полное поглощение
    data_nested = [Interval(1, 10), Interval(2, 3), Interval(4, 8)]
    assert merge_intervals(data_nested) == [Interval(1, 10)]


def test_insert_interval() -> None:
    """Проверка вставки нового интервала."""
    existing = [Interval(1, 2), Interval(3, 5), Interval(6, 7), Interval(8, 10), Interval(12, 16)]

    # Вставка с поглощением нескольких интервалов
    inserted = insert_interval(existing, Interval(4, 8))
    assert inserted == [Interval(1, 2), Interval(3, 10), Interval(12, 16)]

    # Вставка в самое начало без перекрытия
    inserted_start = insert_interval([Interval(3, 5)], Interval(0, 1))
    assert inserted_start == [Interval(0, 1), Interval(3, 5)]

    # Вставка в самый конец без перекрытия
    inserted_end = insert_interval([Interval(3, 5)], Interval(7, 9))
    assert inserted_end == [Interval(3, 5), Interval(7, 9)]

    # Вставка в пустой список
    assert insert_interval([], Interval(1, 5)) == [Interval(1, 5)]


def test_intersect_interval_lists() -> None:
    """Проверка попарного пересечения двух списков интервалов."""
    list1 = [Interval(0, 2), Interval(5, 10), Interval(13, 23), Interval(24, 25)]
    list2 = [Interval(1, 5), Interval(8, 12), Interval(15, 24), Interval(25, 26)]

    result = intersect_interval_lists(list1, list2)
    expected = [
        Interval(1, 2),
        Interval(5, 5),
        Interval(8, 10),
        Interval(15, 23),
        Interval(24, 24),
        Interval(25, 25),
    ]
    assert result == expected

    # Случаи с пустыми списками
    assert intersect_interval_lists([], list2) == []
    assert intersect_interval_lists(list1, []) == []


def test_common_intersection() -> None:
    """Проверка нахождения общего пересечения для набора интервалов."""
    assert common_intersection([]) is None
    assert common_intersection([Interval(1, 10)]) == Interval(1, 10)

    # Общее непустое пересечение
    all_overlap = [Interval(0, 10), Interval(2, 8), Interval(3, 12), Interval(1, 6)]
    assert common_intersection(all_overlap) == Interval(3, 6)

    # Одно непересекающееся условие
    one_disjoint = [Interval(0, 5), Interval(2, 6), Interval(7, 10)]
    assert common_intersection(one_disjoint) is None


def test_string_and_float_intervals() -> None:
    """Проверка работы интервалов с плавающей точкой и строками."""
    float_a = Interval(1.5, 3.5)
    float_b = Interval(2.0, 4.0)
    assert float_a.intersection(float_b) == Interval(2.0, 3.5)

    str_a = Interval("b", "d")
    str_b = Interval("c", "f")
    assert str_a.intersection(str_b) == Interval("c", "d")
