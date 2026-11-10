"""Модуль алгоритмов случайной выборки и перемешивания (Sampling & Shuffling).

Предоставляет классический алгоритм выборки из резервуара (Reservoir Sampling / Algorithm R),
взвешенную выборку из потока (A-Res алгоритм Эфраимидиса — Спиракиса),
а также несмещенное тасование массива по схеме Фишера — Йетса (Дуршенфельда).
"""

from collections.abc import Iterable, Sequence
import heapq
import math
import random


def reservoir_sample[T](
    stream: Iterable[T],
    k: int,
    rng: random.Random | None = None,
) -> list[T]:
    """Выбирает k случайных элементов из потока неизвестной или бесконечной длины за O(N).

    Каждый элемент потока имеет строго равную вероятность k / N оказаться в выборке.
    Требует O(k) дополнительной памяти.

    :param stream: Итерируемый поток элементов.
    :param k: Требуемый размер выборки (k >= 0).
    :param rng: Опциональный генератор случайных чисел для детерминированности.
    :return: Список из k случайно отобранных элементов (или меньше, если в потоке < k элементов).
    :raises ValueError: Если k < 0.
    """
    if k < 0:
        raise ValueError(f"Размер выборки k не может быть отрицательным, получено: {k}")
    if k == 0:
        return []

    rand = rng or random

    reservoir: list[T] = []
    iterator = iter(stream)

    # Заполняем начальный резервуар первыми k элементами
    for _ in range(k):
        try:
            reservoir.append(next(iterator))
        except StopIteration:
            return reservoir

    # Обрабатываем оставшиеся элементы потока
    for index, item in enumerate(iterator, start=k):
        # Случайное число в диапазоне [0, index]
        j = rand.randint(0, index)
        if j < k:
            reservoir[j] = item

    return reservoir


def fisher_yates_shuffle[T](
    items: list[T],
    rng: random.Random | None = None,
) -> list[T]:
    """Выполняет несмещенное тасование списка на месте (in-place) за O(n).

    Реализует канонический алгоритм Фишера — Йетса в модификации Дуршенфельда.

    :param items: Мутируемый список элементов.
    :param rng: Опциональный генератор случайных чисел.
    :return: Тот же самый список items после перестановки.
    """
    rand = rng or random
    n = len(items)

    for i in range(n - 1, 0, -1):
        j = rand.randint(0, i)
        items[i], items[j] = items[j], items[i]

    return items


def shuffled[T](
    items: Sequence[T],
    rng: random.Random | None = None,
) -> list[T]:
    """Возвращает новую перетасованную копию последовательности без изменения оригинала.

    :param items: Исходная последовательность.
    :param rng: Опциональный генератор случайных чисел.
    :return: Новый список со случайно переставленными элементами.
    """
    copy_list = list(items)
    return fisher_yates_shuffle(copy_list, rng=rng)


def weighted_reservoir_sample[T](
    stream: Iterable[tuple[T, float]],
    k: int,
    rng: random.Random | None = None,
) -> list[T]:
    """Выбирает k случайных элементов с учетом весов по алгоритму A-Res (Algorithm with Reservoir).

    Каждый элемент stream представляет собой пару (значение, вес), где вес > 0.
    Ключ элемента вычисляется как u ** (1.0 / weight), где u ~ Uniform(0, 1).

    :param stream: Итерируемый поток пар (элемент, вес).
    :param k: Размер выборки (k >= 0).
    :param rng: Опциональный генератор случайных чисел.
    :return: Список выбранных элементов.
    :raises ValueError: Если k < 0 или вес элемента <= 0.
    """
    if k < 0:
        raise ValueError(f"Размер выборки k не может быть отрицательным, получено: {k}")
    if k == 0:
        return []

    rand = rng or random
    # Минимальная куча размера k: (ключ, порядковый_номер, элемент)
    heap: list[tuple[float, int, T]] = []
    counter: int = 0

    for item, weight in stream:
        if weight <= 0:
            raise ValueError(f"Вес элемента должен быть строго положительным (> 0), получено: {weight}")

        u = rand.random()
        # Для исключения math.log(0) гарантируем u > 0
        while u == 0.0:
            u = rand.random()

        key = math.pow(u, 1.0 / weight)

        if len(heap) < k:
            heapq.heappush(heap, (key, counter, item))
        elif key > heap[0][0]:
            heapq.heapreplace(heap, (key, counter, item))
        counter += 1

    return [node[2] for node in heap]
