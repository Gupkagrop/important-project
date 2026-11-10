"""Модульные тесты для модуля скользящего окна (sliding_window)."""

import math
import statistics

import pytest

from pocket_toolkit.algorithms.sliding_window import (
    SlidingWindowAggregator,
    sliding_window_extrema,
)


def test_initialization() -> None:
    """Проверка корректной и некорректной инициализации окна."""
    agg = SlidingWindowAggregator(5)
    assert agg.capacity == 5
    assert agg.count == 0
    assert agg.is_empty is True
    assert agg.is_full is False
    assert len(agg) == 0

    with pytest.raises(ValueError):
        SlidingWindowAggregator(0)
    with pytest.raises(ValueError):
        SlidingWindowAggregator(-3)


def test_empty_window_properties() -> None:
    """Проверка выброса исключений при чтении агрегатов пустого окна."""
    agg = SlidingWindowAggregator(3)
    with pytest.raises(ValueError):
        _ = agg.sum
    with pytest.raises(ValueError):
        _ = agg.mean
    with pytest.raises(ValueError):
        _ = agg.min
    with pytest.raises(ValueError):
        _ = agg.max
    with pytest.raises(ValueError):
        _ = agg.variance
    with pytest.raises(ValueError):
        _ = agg.stdev


def test_single_element() -> None:
    """Проверка состояния окна с одним элементом."""
    agg = SlidingWindowAggregator(3)
    agg.append(42)
    assert agg.count == 1
    assert agg.is_empty is False
    assert agg.is_full is False
    assert agg.sum == 42.0
    assert agg.mean == 42.0
    assert agg.min == 42.0
    assert agg.max == 42.0
    assert agg.variance == 0.0
    assert agg.stdev == 0.0


def test_window_filling_and_eviction() -> None:
    """Проверка выталкивания старых элементов при заполнении окна."""
    agg = SlidingWindowAggregator(3)
    agg.extend([10, 20, 30])
    assert agg.count == 3
    assert agg.is_full is True
    assert agg.to_list() == [10.0, 20.0, 30.0]
    assert agg.sum == 60.0
    assert agg.mean == 20.0
    assert agg.min == 10.0
    assert agg.max == 30.0

    # Добавляем 4-й элемент, 10 должно вытесниться
    agg.append(40)
    assert agg.count == 3
    assert agg.to_list() == [20.0, 30.0, 40.0]
    assert agg.sum == 90.0
    assert agg.mean == 30.0
    assert agg.min == 20.0
    assert agg.max == 40.0


def test_min_max_monotonicity() -> None:
    """Проверка поддержания минимума и максимума при произвольных колебаниях."""
    agg = SlidingWindowAggregator(3)
    # Последовательность: [5, 1, 9, 2, 7, 3]
    agg.append(5)
    assert agg.min == 5.0 and agg.max == 5.0

    agg.append(1)
    assert agg.min == 1.0 and agg.max == 5.0

    agg.append(9)  # Окно: [5, 1, 9]
    assert agg.min == 1.0 and agg.max == 9.0

    agg.append(2)  # Окно: [1, 9, 2], вытеснено 5
    assert agg.min == 1.0 and agg.max == 9.0

    agg.append(7)  # Окно: [9, 2, 7], вытеснено 1
    assert agg.min == 2.0 and agg.max == 9.0

    agg.append(3)  # Окно: [2, 7, 3], вытеснено 9
    assert agg.min == 2.0 and agg.max == 7.0


def test_variance_and_stdev() -> None:
    """Проверка расчета выборочной дисперсии и СКО."""
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    agg = SlidingWindowAggregator(len(data))
    agg.extend(data)

    expected_var = statistics.variance(data)
    expected_stdev = statistics.stdev(data)

    assert math.isclose(agg.variance, expected_var, rel_tol=1e-7)
    assert math.isclose(agg.stdev, expected_stdev, rel_tol=1e-7)


def test_clear_and_iteration() -> None:
    """Проверка очистки и итерации по агрегатору."""
    agg = SlidingWindowAggregator(4)
    agg.extend([1, 2, 3])
    assert list(agg) == [1.0, 2.0, 3.0]
    assert "SlidingWindowAggregator" in repr(agg)

    agg.clear()
    assert agg.count == 0
    assert agg.is_empty is True
    assert list(agg) == []


def test_sliding_window_extrema() -> None:
    """Проверка функции вычисления скользящих экстремумов."""
    seq = [1, 3, -1, -3, 5, 3, 6, 7]
    k = 3
    mins, maxs = sliding_window_extrema(seq, k)

    # Длина результатов должна быть n - k + 1 = 6
    assert len(mins) == 6
    assert len(maxs) == 6

    # Окна размера 3:
    # [1, 3, -1] -> min=-1, max=3
    # [3, -1, -3] -> min=-3, max=3
    # [-1, -3, 5] -> min=-3, max=5
    # [-3, 5, 3] -> min=-3, max=5
    # [5, 3, 6] -> min=3, max=6
    # [3, 6, 7] -> min=3, max=7
    assert mins == [-1.0, -3.0, -3.0, -3.0, 3.0, 3.0]
    assert maxs == [3.0, 3.0, 5.0, 5.0, 6.0, 7.0]


def test_sliding_window_extrema_edge_cases() -> None:
    """Проверка граничных случаев для sliding_window_extrema."""
    # Окно размера 1
    mins, maxs = sliding_window_extrema([4, 2, 8], 1)
    assert mins == [4.0, 2.0, 8.0]
    assert maxs == [4.0, 2.0, 8.0]

    # Окно размера N
    mins_full, maxs_full = sliding_window_extrema([4, 2, 8], 3)
    assert mins_full == [2.0]
    assert maxs_full == [8.0]

    # Ошибочные размеры
    with pytest.raises(ValueError):
        sliding_window_extrema([1, 2], 0)
    with pytest.raises(ValueError):
        sliding_window_extrema([1, 2], 3)
