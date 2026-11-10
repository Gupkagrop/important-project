"""Модульные тесты для модуля поиска подстроки КМП (kmp)."""

from pocket_toolkit.algorithms.kmp import (
    compute_prefix_function,
    kmp_count,
    kmp_find_first,
    kmp_search,
    kmp_search_iter,
    kmp_search_sequence,
)


def test_compute_prefix_function() -> None:
    """Проверка вычисления префикс-функции (массива pi)."""
    assert compute_prefix_function("") == []
    assert compute_prefix_function("A") == [0]
    # "A B A B A C A" -> [0, 0, 1, 2, 3, 0, 1]
    assert compute_prefix_function("ABABACA") == [0, 0, 1, 2, 3, 0, 1]
    # "A A A A A" -> [0, 1, 2, 3, 4]
    assert compute_prefix_function("AAAAA") == [0, 1, 2, 3, 4]


def test_kmp_search_basic() -> None:
    """Проверка базового строкового поиска."""
    text = "ABC ABCDAB ABCDABCDABDE"
    pattern = "ABCDABD"
    assert kmp_search(text, pattern) == [15]

    # Шаблон длиннее текста
    assert kmp_search("short", "very long pattern") == []

    # Пустые аргументы
    assert kmp_search("any text", "") == []
    assert kmp_search("", "pattern") == []
    assert kmp_search("", "") == []


def test_kmp_search_overlapping() -> None:
    """Проверка поиска перекрывающихся вхождений шаблона."""
    text = "AAAAAA"
    pattern = "AAA"
    assert kmp_search(text, pattern) == [0, 1, 2, 3]

    text_aba = "ABABABAB"
    pattern_aba = "ABA"
    assert kmp_search(text_aba, pattern_aba) == [0, 2, 4]


def test_kmp_find_first() -> None:
    """Проверка нахождения первого вхождения."""
    text = "mississippi"
    assert kmp_find_first(text, "issi") == 1
    assert kmp_find_first(text, "pp") == 8
    assert kmp_find_first(text, "world") == -1
    assert kmp_find_first(text, "") == 0


def test_kmp_count() -> None:
    """Проверка подсчета количества вхождений с перекрытиями и без."""
    text = "AAAAAA"  # 6 букв 'A'
    pattern = "AA"

    # С перекрытиями: индексы 0, 1, 2, 3, 4 -> 5 вхождений
    assert kmp_count(text, pattern, allow_overlap=True) == 5
    # Без перекрытий: [0..1], [2..3], [4..5] -> 3 вхождения
    assert kmp_count(text, pattern, allow_overlap=False) == 3

    assert kmp_count("hello", "xyz") == 0


def test_kmp_unicode_russian() -> None:
    """Проверка корректности работы с русскими символами и Unicode."""
    text = "колокол колокола звонит около колокольни"
    pattern = "колокол"
    matches = kmp_search(text, pattern)
    assert matches == [0, 8, 30]


def test_kmp_search_sequence() -> None:
    """Проверка поиска шаблонов в последовательностях чисел и кортежей."""
    nums = [1, 2, 3, 1, 2, 3, 4, 1, 2]
    sub = [1, 2, 3]
    assert kmp_search_sequence(nums, sub) == [0, 3]

    tuples = [(1, "a"), (2, "b"), (1, "a"), (2, "b")]
    assert kmp_search_sequence(tuples, [(1, "a"), (2, "b")]) == [0, 2]


def test_kmp_search_iter() -> None:
    """Проверка потокового генератора kmp_search_iter."""
    stream = iter("ABCABCABC")
    pattern = "BCA"
    results = list(kmp_search_iter(stream, pattern))
    assert results == [1, 4]

    # Пустой шаблон в генераторе
    assert list(kmp_search_iter(iter("abc"), "")) == []
