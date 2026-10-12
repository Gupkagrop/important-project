"""Реализация ограниченной двусторонней очереди (Bounded Deque).

Двусторонняя очередь с фиксированной вместимостью и безопасным выталкиванием
вытесняемых элементов при переполнении, а также поддержкой callback-уведомлений.
"""

from collections.abc import Callable, Iterable, Iterator


class BoundedDeque[T]:
    """Ограниченная двусторонняя очередь фиксированной вместимости.

    Обеспечивает константное время O(1) добавления и удаления элементов
    с обоих концов очереди, произвольный доступ по индексу за O(1),
    а также механизм безопасного выталкивания при переполнении.
    """

    def __init__(
        self,
        capacity: int,
        iterable: Iterable[T] | None = None,
        on_evict: Callable[[T], None] | None = None,
    ) -> None:
        """Инициализирует очередь заданной вместимости.

        :param capacity: Максимальная вместимость очереди (строго > 0).
        :param iterable: Начальная последовательность элементов.
        :param on_evict: Функция обратного вызова, вызываемая при выталкивании элемента.
        :raises ValueError: Если вместимость меньше либо равна 0.
        """
        if capacity <= 0:
            raise ValueError("Вместимость ограниченной очереди должна быть больше нуля")

        self._capacity: int = capacity
        self._data: list[T | None] = [None] * capacity
        self._head: int = 0
        self._size: int = 0
        self._on_evict: Callable[[T], None] | None = on_evict

        if iterable is not None:
            self.extend(iterable)

    @property
    def capacity(self) -> int:
        """Возвращает максимальную вместимость очереди."""
        return self._capacity

    @property
    def available_capacity(self) -> int:
        """Возвращает оставшееся свободное место в очереди."""
        return self._capacity - self._size

    def is_empty(self) -> bool:
        """Проверяет, пуста ли очередь."""
        return self._size == 0

    def is_full(self) -> bool:
        """Проверяет, заполнена ли очередь до предела."""
        return self._size == self._capacity

    def append(self, item: T) -> T | None:
        """Добавляет элемент в правый конец очереди (хвост).

        Если очередь заполнена, выталкивает самый старый элемент из начала (головы),
        вызывает callback выталкивания (если задан) и возвращает вытолкнутый элемент.

        :param item: Добавляемый элемент.
        :return: Вытолкнутый элемент при переполнении или None, если место было свободно.
        """
        if self.is_full():
            evicted: T = self._get_item_at_physical(self._head)
            self._data[self._head] = item
            self._head = (self._head + 1) % self._capacity
            self._notify_eviction(evicted)
            return evicted

        tail_index: int = (self._head + self._size) % self._capacity
        self._data[tail_index] = item
        self._size += 1
        return None

    def appendleft(self, item: T) -> T | None:
        """Добавляет элемент в левый конец очереди (голову).

        Если очередь заполнена, выталкивает крайний правый элемент (хвост),
        вызывает callback выталкивания (если задан) и возвращает вытолкнутый элемент.

        :param item: Добавляемый элемент.
        :return: Вытолкнутый элемент при переполнении или None, если место было свободно.
        """
        if self.is_full():
            last_index: int = (self._head + self._size - 1) % self._capacity
            evicted: T = self._get_item_at_physical(last_index)
            self._head = (self._head - 1 + self._capacity) % self._capacity
            self._data[self._head] = item
            self._notify_eviction(evicted)
            return evicted

        self._head = (self._head - 1 + self._capacity) % self._capacity
        self._data[self._head] = item
        self._size += 1
        return None

    def try_append(self, item: T) -> bool:
        """Пытается добавить элемент в правый конец без выталкивания при переполнении.

        :param item: Добавляемый элемент.
        :return: True, если элемент добавлен; False, если очередь уже полна.
        """
        if self.is_full():
            return False

        self.append(item)
        return True

    def try_appendleft(self, item: T) -> bool:
        """Пытается добавить элемент в левый конец без выталкивания при переполнении.

        :param item: Добавляемый элемент.
        :return: True, если элемент добавлен; False, если очередь уже полна.
        """
        if self.is_full():
            return False

        self.appendleft(item)
        return True

    def pop(self) -> T:
        """Извлекает и возвращает элемент из правого конца очереди (хвоста).

        :return: Извлеченный элемент.
        :raises IndexError: Если очередь пуста.
        """
        if self.is_empty():
            raise IndexError("Невозможно извлечь элемент: очередь пуста")

        tail_index: int = (self._head + self._size - 1) % self._capacity
        item: T = self._get_item_at_physical(tail_index)
        self._data[tail_index] = None
        self._size -= 1
        return item

    def popleft(self) -> T:
        """Извлекает и возвращает элемент из левого конца очереди (головы).

        :return: Извлеченный элемент.
        :raises IndexError: Если очередь пуста.
        """
        if self.is_empty():
            raise IndexError("Невозможно извлечь элемент: очередь пуста")

        item: T = self._get_item_at_physical(self._head)
        self._data[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1
        return item

    def peek(self) -> T:
        """Возвращает крайний правый элемент (хвост) без удаления.

        :return: Крайний правый элемент очереди.
        :raises IndexError: Если очередь пуста.
        """
        if self.is_empty():
            raise IndexError("Невозможно просмотреть элемент: очередь пуста")

        tail_index: int = (self._head + self._size - 1) % self._capacity
        return self._get_item_at_physical(tail_index)

    def peekleft(self) -> T:
        """Возвращает крайний левый элемент (голову) без удаления.

        :return: Крайний левый элемент очереди.
        :raises IndexError: Если очередь пуста.
        """
        if self.is_empty():
            raise IndexError("Невозможно просмотреть элемент: очередь пуста")

        return self._get_item_at_physical(self._head)

    def extend(self, iterable: Iterable[T]) -> list[T]:
        """Добавляет все элементы последовательности в правый конец очереди.

        :param iterable: Последовательность элементов для добавления.
        :return: Список всех вытолкнутых элементов в порядке выталкивания.
        """
        evicted_items: list[T] = []
        for item in iterable:
            evicted: T | None = self.append(item)
            if evicted is not None:
                evicted_items.append(evicted)
        return evicted_items

    def extendleft(self, iterable: Iterable[T]) -> list[T]:
        """Добавляет элементы последовательности в левый конец очереди.

        Элементы добавляются поочередно слева, аналогично collections.deque.extendleft.

        :param iterable: Последовательность элементов для добавления.
        :return: Список всех вытолкнутых элементов в порядке выталкивания.
        """
        evicted_items: list[T] = []
        for item in iterable:
            evicted: T | None = self.appendleft(item)
            if evicted is not None:
                evicted_items.append(evicted)
        return evicted_items

    def clear(self) -> None:
        """Очищает очередь, удаляя все элементы."""
        self._data = [None] * self._capacity
        self._head = 0
        self._size = 0

    def rotate(self, steps: int = 1) -> None:
        """Циклически сдвигает элементы очереди на указанное число шагов.

        Положительное значение сдвигает вправо, отрицательное — влево.

        :param steps: Количество шагов циклического сдвига.
        """
        if self._size <= 1:
            return

        effective_steps: int = steps % self._size
        if effective_steps == 0:
            return

        items: list[T] = self.to_list()
        rotated: list[T] = items[-effective_steps:] + items[:-effective_steps]
        for offset, val in enumerate(rotated):
            physical_idx: int = (self._head + offset) % self._capacity
            self._data[physical_idx] = val

    def reverse(self) -> None:
        """Разворачивает порядок элементов в очереди на месте."""
        if self._size <= 1:
            return

        left_idx: int = 0
        right_idx: int = self._size - 1
        while left_idx < right_idx:
            left_phys: int = self._physical_index(left_idx)
            right_phys: int = self._physical_index(right_idx)
            self._data[left_phys], self._data[right_phys] = (
                self._data[right_phys],
                self._data[left_phys],
            )
            left_idx += 1
            right_idx -= 1

    def count(self, value: T) -> int:
        """Возвращает количество вхождений заданного значения в очереди.

        :param value: Искомое значение.
        :return: Количество совпадений.
        """
        match_count: int = 0
        for item in self:
            if item == value:
                match_count += 1
        return match_count

    def index(self, value: T, start: int = 0, stop: int | None = None) -> int:
        """Возвращает логический индекс первого вхождения значения.

        :param value: Искомое значение.
        :param start: Начальный индекс диапазона поиска.
        :param stop: Конечный индекс диапазона поиска (не включая его).
        :return: Логический индекс элемента от начала очереди.
        :raises ValueError: Если элемент не найден в заданном диапазоне.
        """
        start_idx: int = self._normalize_search_index(start, 0)
        default_stop: int = self._size
        stop_idx: int = (
            default_stop
            if stop is None
            else self._normalize_search_index(stop, self._size)
        )

        for log_idx in range(start_idx, stop_idx):
            if self[log_idx] == value:
                return log_idx

        raise ValueError(f"Значение {value!r} не найдено в очереди")

    def remove(self, value: T) -> None:
        """Удаляет первое вхождение значения из очереди.

        :param value: Удаляемое значение.
        :raises ValueError: Если значение отсутствует в очереди.
        """
        found_idx: int = self.index(value)
        del self[found_idx]

    def to_list(self) -> list[T]:
        """Возвращает текущие элементы очереди в виде обычного списка.

        :return: Список элементов от головы к хвосту.
        """
        return list(self)

    def copy(self) -> "BoundedDeque[T]":
        """Создает неглубокую копию текущей очереди.

        :return: Новая ограниченная очередь с теми же элементами и настройками.
        """
        return BoundedDeque(
            capacity=self._capacity,
            iterable=self,
            on_evict=self._on_evict,
        )

    def _resolve_logical_index(self, index: int) -> int:
        """Проверяет и преобразует логический индекс с учетом отрицательных смещений.

        :param index: Логический индекс (может быть отрицательным).
        :return: Нормализованный положительный логический индекс.
        :raises IndexError: Если индекс выходит за допустимые границы очереди.
        """
        normalized: int = index if index >= 0 else index + self._size
        if normalized < 0 or normalized >= self._size:
            raise IndexError("Индекс выходит за границы очереди")
        return normalized

    def _normalize_search_index(self, index: int, default_pos: int) -> int:
        """Нормализует границы среза для поиска без выброса исключения.

        :param index: Указанный индекс.
        :param default_pos: Значение по умолчанию при выходе за пределы.
        :return: Индекс в диапазоне от 0 до размера очереди.
        """
        adjusted: int = index if index >= 0 else index + self._size
        if adjusted < 0:
            return 0
        if adjusted > self._size:
            return self._size
        return adjusted

    def _physical_index(self, logical_index: int) -> int:
        """Вычисляет физический индекс в кольцевом массиве по логическому индексу."""
        return (self._head + logical_index) % self._capacity

    def _get_item_at_physical(self, physical_index: int) -> T:
        """Безопасно извлекает типизированный элемент по физическому индексу."""
        item: T | None = self._data[physical_index]
        assert item is not None
        return item

    def _notify_eviction(self, item: T) -> None:
        """Вызывает пользовательский callback выталкивания при его наличии."""
        if self._on_evict is not None:
            self._on_evict(item)

    def __len__(self) -> int:
        """Возвращает текущее количество элементов в очереди."""
        return self._size

    def __bool__(self) -> bool:
        """Возвращает True, если очередь не пуста."""
        return self._size > 0

    def __iter__(self) -> Iterator[T]:
        """Итерирует по элементам от головы к хвосту."""
        for offset in range(self._size):
            phys_idx: int = (self._head + offset) % self._capacity
            yield self._get_item_at_physical(phys_idx)

    def __reversed__(self) -> Iterator[T]:
        """Итерирует по элементам в обратном порядке от хвоста к голове."""
        for offset in range(self._size - 1, -1, -1):
            phys_idx: int = (self._head + offset) % self._capacity
            yield self._get_item_at_physical(phys_idx)

    def __getitem__(self, index: int) -> T:
        """Возвращает элемент по логическому индексу.

        :param index: Логический индекс (поддерживаются отрицательные индексы).
        :return: Хранимый элемент.
        :raises IndexError: Если индекс выходит за границы.
        """
        log_idx: int = self._resolve_logical_index(index)
        phys_idx: int = self._physical_index(log_idx)
        return self._get_item_at_physical(phys_idx)

    def __setitem__(self, index: int, value: T) -> None:
        """Обновляет элемент по логическому индексу.

        :param index: Логический индекс элемента.
        :param value: Новое значение.
        :raises IndexError: Если индекс выходит за границы.
        """
        log_idx: int = self._resolve_logical_index(index)
        phys_idx: int = self._physical_index(log_idx)
        self._data[phys_idx] = value

    def __delitem__(self, index: int) -> None:
        """Удаляет элемент по логическому индексу, сдвигая последующие элементы.

        :param index: Логический индекс удаляемого элемента.
        :raises IndexError: Если индекс выходит за границы.
        """
        log_idx: int = self._resolve_logical_index(index)
        for i in range(log_idx, self._size - 1):
            curr_phys: int = self._physical_index(i)
            next_phys: int = self._physical_index(i + 1)
            self._data[curr_phys] = self._data[next_phys]

        last_phys: int = self._physical_index(self._size - 1)
        self._data[last_phys] = None
        self._size -= 1

    def __contains__(self, item: object) -> bool:
        """Проверяет наличие элемента в очереди."""
        for existing in self:
            if existing == item:
                return True
        return False

    def __eq__(self, other: object) -> bool:
        """Проверяет эквивалентность содержимого с другой последовательностью."""
        if not isinstance(other, BoundedDeque):
            return False
        if self._size != len(other):
            return False
        return self.to_list() == other.to_list()

    def __repr__(self) -> str:
        """Строковое представление очереди."""
        return f"BoundedDeque({self.to_list()!r}, capacity={self._capacity})"
