"""Модульные тесты для модуля алгоритмов выборки и тасования (sampling)."""

import random
from collections import Counter

import pytest

from pocket_toolkit.algorithms.sampling import (
    fisher_yates_shuffle,
    reservoir_sample,
    shuffled,
    weighted_reservoir_sample,
)


def test_reservoir_sample_edge_cases() -> None:
    """Проверка граничных параметров reservoir_sample."""
    with pytest.raises(ValueError):
        reservoir_sample(range(10), -1)

    assert reservoir_sample(range(10), 0) == []
    assert reservoir_sample([], 5) == []

    # Размер выборки больше длины потока
    sample = reservoir_sample([1, 2, 3], 10)
    assert sorted(sample) == [1, 2, 3]


def test_reservoir_sample_reproducibility() -> None:
    """Проверка детерминированности при использовании seed."""
    rng1 = random.Random(42)
    rng2 = random.Random(42)

    sample1 = reservoir_sample(range(100), 5, rng=rng1)
    sample2 = reservoir_sample(range(100), 5, rng=rng2)

    assert sample1 == sample2
    assert len(sample1) == 5


def test_reservoir_sample_uniformity() -> None:
    """Статистическая проверка равномерности выбора из 5 элементов."""
    rng = random.Random(12345)
    counts: Counter[int] = Counter()
    trials = 10000

    for _ in range(trials):
        item = reservoir_sample(range(5), 1, rng=rng)[0]
        counts[item] += 1

    # Для каждого из 5 элементов математическое ожидание равно 2000
    for i in range(5):
        assert 1700 <= counts[i] <= 2300


def test_fisher_yates_shuffle() -> None:
    """Проверка алгоритма тасования Фишера-Йетса."""
    assert fisher_yates_shuffle([]) == []
    assert fisher_yates_shuffle([42]) == [42]

    original = [1, 2, 3, 4, 5]
    mutated = list(original)
    res = fisher_yates_shuffle(mutated, rng=random.Random(99))

    assert res is mutated  # Тасование происходит in-place
    assert sorted(res) == original  # Все элементы сохранены


def test_shuffled_immutability() -> None:
    """Проверка создания новой копии без изменения оригинала в shuffled."""
    original = (10, 20, 30, 40)
    result = shuffled(original, rng=random.Random(123))

    assert isinstance(result, list)
    assert sorted(result) == sorted(original)
    assert original == (10, 20, 30, 40)


def test_weighted_reservoir_sample() -> None:
    """Проверка взвешенной выборки A-Res."""
    with pytest.raises(ValueError):
        weighted_reservoir_sample([(1, 1.0)], -1)

    with pytest.raises(ValueError):
        weighted_reservoir_sample([(1, 0.0)], 1)

    with pytest.raises(ValueError):
        weighted_reservoir_sample([(1, -2.5)], 1)

    assert weighted_reservoir_sample([], 5) == []
    assert weighted_reservoir_sample([(1, 1.0)], 0) == []

    # Элемент с гигантским весом должен выбираться практически всегда
    stream = [("heavy", 1000.0), ("light_1", 0.1), ("light_2", 0.1)]
    rng = random.Random(42)
    selected = weighted_reservoir_sample(stream, 1, rng=rng)
    assert selected == ["heavy"]
