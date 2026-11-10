"""Модуль алгоритма поиска подстроки Кнута — Морриса — Пратта (KMP).

Предоставляет функции вычисления префикс-функции (массива pi),
быстрого поиска всех вхождений подстроки за линейное время O(n + m),
поиска первого вхождения, подсчета количества совпадений и обобщенного поиска в последовательностях.
"""

from collections.abc import Iterable, Iterator, Sequence


def compute_prefix_function[T](pattern: Sequence[T]) -> list[int]:
    """Вычисляет префикс-функцию (массив pi) для заданной последовательности/шаблона.

    pi[i] — это длина наибольшего собственного префикса подстроки pattern[0...i],
    который одновременно является ее суффиксом.
    Временная сложность: O(m).

    :param pattern: Искомый шаблон (строка или последовательность элементов).
    :return: Список значений префикс-функции длины len(pattern).
    """
    m = len(pattern)
    if m == 0:
        return []

    pi: list[int] = [0] * m
    k: int = 0

    for i in range(1, m):
        while k > 0 and pattern[k] != pattern[i]:
            k = pi[k - 1]
        if pattern[k] == pattern[i]:
            k += 1
        pi[i] = k

    return pi


def kmp_search_sequence[T](text: Sequence[T], pattern: Sequence[T]) -> list[int]:
    """Находит все начальные индексы вхождений шаблона в последовательность за O(n + m).

    :param text: Исходная последовательность элементов.
    :param pattern: Искомый шаблон.
    :return: Список начальных 0-based индексов всех совпадений (с учетом перекрытий).
    """
    n = len(text)
    m = len(pattern)

    if m == 0:
        return []
    if n < m:
        return []

    pi: list[int] = compute_prefix_function(pattern)
    matches: list[int] = []
    q: int = 0  # Количество совпавших символов шаблона

    for i in range(n):
        while q > 0 and pattern[q] != text[i]:
            q = pi[q - 1]
        if pattern[q] == text[i]:
            q += 1
        if q == m:
            matches.append(i - m + 1)
            q = pi[m - 1]

    return matches


def kmp_search(text: str, pattern: str) -> list[int]:
    """Находит все начальные индексы вхождений шаблона в строку.

    :param text: Текст для поиска.
    :param pattern: Искомый строковый шаблон.
    :return: Список начальных 0-based индексов всех совпадений.
    """
    return kmp_search_sequence(text, pattern)


def kmp_find_first(text: str, pattern: str) -> int:
    """Находит индекс первого вхождения шаблона в строку за линейное время O(n + m).

    :param text: Текст для поиска.
    :param pattern: Искомый строковый шаблон.
    :return: Индекс первого вхождения или -1, если шаблон не найден.
    """
    n = len(text)
    m = len(pattern)

    if m == 0:
        return 0
    if n < m:
        return -1

    pi: list[int] = compute_prefix_function(pattern)
    q: int = 0

    for i in range(n):
        while q > 0 and pattern[q] != text[i]:
            q = pi[q - 1]
        if pattern[q] == text[i]:
            q += 1
        if q == m:
            return i - m + 1

    return -1


def kmp_count(text: str, pattern: str, allow_overlap: bool = True) -> int:
    """Подсчитывает количество вхождений шаблона в текст.

    :param text: Текст для поиска.
    :param pattern: Искомый строковый шаблон.
    :param allow_overlap: Разрешать ли учет перекрывающихся вхождений (по умолчанию True).
    :return: Общее количество найденных вхождений.
    """
    matches = kmp_search(text, pattern)
    if not matches:
        return 0
    if allow_overlap:
        return len(matches)

    # Подсчет без перекрытий
    count = 0
    last_end = -1
    pattern_len = len(pattern)

    for start_idx in matches:
        if start_idx >= last_end:
            count += 1
            last_end = start_idx + pattern_len

    return count


def kmp_search_iter[T](text: Iterable[T], pattern: Sequence[T]) -> Iterator[int]:
    """Потоковый генератор индексов вхождений шаблона в итерируемый поток данных.

    Позволяет обрабатывать потоковые данные произвольной длины без загрузки всего текста в память.

    :param text: Итерируемый поток элементов.
    :param pattern: Искомый шаблон фиксированной длины.
    :return: Итератор начальных индексов совпадений в потоке.
    """
    m = len(pattern)
    if m == 0:
        return

    pi: list[int] = compute_prefix_function(pattern)
    q: int = 0

    for idx, item in enumerate(text):
        while q > 0 and pattern[q] != item:
            q = pi[q - 1]
        if pattern[q] == item:
            q += 1
        if q == m:
            yield idx - m + 1
            q = pi[m - 1]
