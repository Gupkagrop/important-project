"""Модуль агрегации данных в скользящем окне (Sliding Window Aggregator).

Предоставляет структуру данных `SlidingWindowAggregator` для поддержания статистических
показателей (сумма, среднее, минимум, максимум, дисперсия) за фиксированный размер окна
с константным или амортизированным константным временем обновления O(1),
а также вспомогательные функции вычисления скользящих экстремумов.
"""

import math
from collections import deque
from collections.abc import Iterable, Iterator, Sequence


class SlidingWindowAggregator:
    """Агрегатор метрик в скользящем окне фиксированного размера.

    Поддерживает добавление элементов за O(1) и вычисление текущих агрегатов:
    - Сумма: O(1)
    - Среднее: O(1)
    - Минимум: O(1) амортизированно (с использованием монотонной деки)
    - Максимум: O(1) амортизированно (с использованием монотонной деки)
    - Дисперсия и стандартное отклонение: O(1)
    """

    __slots__ = (
        "_capacity",
        "_data",
        "_max_deque",
        "_min_deque",
        "_sum",
        "_sum_squares",
    )

    def __init__(self, capacity: int) -> None:
        """Инициализирует скользящее окно заданной вместимости.

        :param capacity: Максимальный размер окна (> 0).
        :raises ValueError: Если вместимость меньше единицы.
        """
        if capacity <= 0:
            raise ValueError(f"Вместимость окна должна быть строго положительной (> 0), получено: {capacity}")

        self._capacity: int = capacity
        self._data: deque[float] = deque()
        self._min_deque: deque[float] = deque()
        self._max_deque: deque[float] = deque()
        self._sum: float = 0.0
        self._sum_squares: float = 0.0

    @property
    def capacity(self) -> int:
        """Максимальная вместимость скользящего окна."""
        return self._capacity

    @property
    def count(self) -> int:
        """Текущее количество элементов в окне."""
        return len(self._data)

    @property
    def is_full(self) -> bool:
        """Проверяет, заполнено ли окно до максимальной вместимости."""
        return len(self._data) == self._capacity

    @property
    def is_empty(self) -> bool:
        """Проверяет, пусто ли окно."""
        return len(self._data) == 0

    def append(self, value: float) -> None:
        """Добавляет новое значение в скользящее окно.

        Если окно уже заполнено, старейший элемент автоматически выталкивается.

        :param value: Числовое значение для добавления.
        """
        val = float(value)

        # Если окно заполнено, удаляем старейший элемент
        if len(self._data) == self._capacity:
            old_val = self._data.popleft()
            self._sum -= old_val
            self._sum_squares -= old_val * old_val

            # Обновляем монотонные очереди экстремумов
            if self._min_deque and self._min_deque[0] == old_val:
                self._min_deque.popleft()
            if self._max_deque and self._max_deque[0] == old_val:
                self._max_deque.popleft()

        # Добавляем новый элемент в буфер
        self._data.append(val)
        self._sum += val
        self._sum_squares += val * val

        # Поддерживаем монотонность очереди минимумов (возрастающая)
        while self._min_deque and self._min_deque[-1] > val:
            self._min_deque.pop()
        self._min_deque.append(val)

        # Поддерживаем монотонность очереди максимумов (убывающая)
        while self._max_deque and self._max_deque[-1] < val:
            self._max_deque.pop()
        self._max_deque.append(val)

    def extend(self, values: Iterable[float | int]) -> None:
        """Добавляет последовательность элементов в окно.

        :param values: Итерируемый источник числовых значений.
        """
        for val in values:
            self.append(val)

    def clear(self) -> None:
        """Очищает окно от всех накопленных данных."""
        self._data.clear()
        self._min_deque.clear()
        self._max_deque.clear()
        self._sum = 0.0
        self._sum_squares = 0.0

    @property
    def sum(self) -> float:
        """Текущая сумма элементов в окне.

        :raises ValueError: Если окно пусто.
        """
        if not self._data:
            raise ValueError("Окно пусто, невозможно вычислить сумму")
        return self._sum

    @property
    def mean(self) -> float:
        """Текущее среднее арифметическое элементов окна.

        :raises ValueError: Если окно пусто.
        """
        if not self._data:
            raise ValueError("Окно пусто, невозможно вычислить среднее")
        return self._sum / len(self._data)

    @property
    def min(self) -> float:
        """Текущий минимум среди элементов окна.

        :raises ValueError: Если окно пусто.
        """
        if not self._data:
            raise ValueError("Окно пусто, невозможно получить минимум")
        return self._min_deque[0]

    @property
    def max(self) -> float:
        """Текущий максимум среди элементов окна.

        :raises ValueError: Если окно пусто.
        """
        if not self._data:
            raise ValueError("Окно пусто, невозможно получить максимум")
        return self._max_deque[0]

    @property
    def variance(self) -> float:
        """Выборочная дисперсия элементов окна (несмещенная, деление на N - 1).

        Если в окне ровно 1 элемент, возвращается 0.0.

        :raises ValueError: Если окно пусто.
        """
        n = len(self._data)
        if n == 0:
            raise ValueError("Окно пусто, невозможно вычислить дисперсию")
        if n == 1:
            return 0.0

        mean_val = self._sum / n
        raw_variance = (self._sum_squares - (self._sum * mean_val)) / (n - 1)
        return max(0.0, raw_variance)

    @property
    def stdev(self) -> float:
        """Выборочное стандартное отклонение элементов окна.

        :raises ValueError: Если окно пусто.
        """
        return math.sqrt(self.variance)

    def to_list(self) -> list[float]:
        """Возвращает снимок текущих элементов окна в порядке поступления."""
        return list(self._data)

    def __iter__(self) -> Iterator[float]:
        """Возвращает итератор по текущим элементам окна."""
        return iter(self._data)

    def __len__(self) -> int:
        """Возвращает текущее количество элементов."""
        return len(self._data)

    def __repr__(self) -> str:
        """Строковое представление агрегатора."""
        return f"SlidingWindowAggregator(capacity={self._capacity}, count={len(self._data)})"


def sliding_window_extrema(
    sequence: Sequence[float | int],
    window_size: int,
) -> tuple[list[float], list[float]]:
    """Вычисляет скользящие минимумы и максимумы для всей последовательности за время O(n).

    :param sequence: Входная последовательность чисел.
    :param window_size: Размер скользящего окна (> 0).
    :return: Кортеж из двух списков: (список_минимумов, список_максимумов).
    :raises ValueError: Если размер окна меньше 1 или больше длины последовательности.
    """
    n = len(sequence)
    if window_size <= 0:
        raise ValueError(f"Размер окна должен быть строго положительным, получено: {window_size}")
    if window_size > n:
        raise ValueError(f"Размер окна ({window_size}) превышает длину последовательности ({n})")

    mins: list[float] = []
    maxs: list[float] = []

    min_idx_deque: deque[int] = deque()
    max_idx_deque: deque[int] = deque()

    for idx, raw_val in enumerate(sequence):
        val = float(raw_val)

        # Удаляем индексы за пределами текущего окна
        boundary = idx - window_size + 1
        while min_idx_deque and min_idx_deque[0] < boundary:
            min_idx_deque.popleft()
        while max_idx_deque and max_idx_deque[0] < boundary:
            max_idx_deque.popleft()

        # Поддерживаем монотонность min_idx_deque
        while min_idx_deque and sequence[min_idx_deque[-1]] >= val:
            min_idx_deque.pop()
        min_idx_deque.append(idx)

        # Поддерживаем монотонность max_idx_deque
        while max_idx_deque and sequence[max_idx_deque[-1]] <= val:
            max_idx_deque.pop()
        max_idx_deque.append(idx)

        # Сохраняем экстремумы при достижении полной ширины окна
        if idx >= window_size - 1:
            mins.append(float(sequence[min_idx_deque[0]]))
            maxs.append(float(sequence[max_idx_deque[0]]))

    return mins, maxs
