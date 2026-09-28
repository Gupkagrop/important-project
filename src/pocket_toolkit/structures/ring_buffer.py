"""Реализация кольцевого буфера фиксированного размера."""

from collections.abc import Iterator


class RingBuffer[T]:
    """Кольцевой буфер (циклический буфер) с фиксированной максимальной вместимостью.

    При переполнении буфера добавление новых элементов приводит к перезаписи
    наиболее старых элементов без выделения дополнительной памяти.
    """

    def __init__(self, capacity: int) -> None:
        """Инициализирует буфер заданной вместимости.

        :param capacity: Максимальное количество элементов (должно быть строго > 0).
        :raises ValueError: Если вместимость меньше либо равна нулю.
        """
        if capacity <= 0:
            raise ValueError("Вместимость кольцевого буфера должна быть больше 0")

        self._capacity: int = capacity
        self._data: list[T | None] = [None] * capacity
        self._head: int = 0
        self._size: int = 0

    @property
    def capacity(self) -> int:
        """Возвращает максимальную вместимость буфера."""
        return self._capacity

    def is_empty(self) -> bool:
        """Проверяет, пуст ли буфер."""
        return self._size == 0

    def is_full(self) -> bool:
        """Проверяет, заполнен ли буфер до предела."""
        return self._size == self._capacity

    def append(self, item: T) -> None:
        """Добавляет элемент в конец буфера.

        Если буфер полон, перезаписывает самый старый элемент и сдвигает указатель головы.
        """
        if self.is_full():
            self._data[self._head] = item
            self._head = (self._head + 1) % self._capacity
            return

        tail_index: int = (self._head + self._size) % self._capacity
        self._data[tail_index] = item
        self._size += 1

    def popleft(self) -> T:
        """Извлекает и возвращает самый старый элемент из начала буфера.

        :raises IndexError: Если буфер пуст.
        """
        if self.is_empty():
            raise IndexError("Невозможно извлечь элемент: буфер пуст")

        item: T | None = self._data[self._head]
        self._data[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1

        # Гарантируем корректность типа после проверки непустого состояния
        assert item is not None
        return item

    def peek(self) -> T:
        """Возвращает самый старый элемент без его удаления.

        :raises IndexError: Если буфер пуст.
        """
        if self.is_empty():
            raise IndexError("Буфер пуст")

        item: T | None = self._data[self._head]
        assert item is not None
        return item

    def clear(self) -> None:
        """Сбрасывает состояние буфера, очищая все элементы."""
        self._data = [None] * self._capacity
        self._head = 0
        self._size = 0

    def to_list(self) -> list[T]:
        """Возвращает текущие элементы буфера в виде списка от старых к новым."""
        return list(self)

    def __len__(self) -> int:
        """Возвращает текущее количество элементов в буфере."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Итерирует по элементам буфера в хронологическом порядке."""
        for offset in range(self._size):
            actual_index: int = (self._head + offset) % self._capacity
            item: T | None = self._data[actual_index]
            assert item is not None
            yield item

    def __getitem__(self, index: int) -> T:
        """Возвращает элемент по логическому индексу от 0 до size - 1.

        :raises IndexError: При выходе индекса за границы диапазона.
        """
        if index < 0 or index >= self._size:
            raise IndexError("Индекс выходит за границы диапазона элементов буфера")

        actual_index: int = (self._head + index) % self._capacity
        item: T | None = self._data[actual_index]
        assert item is not None
        return item

    def __repr__(self) -> str:
        """Строковое представление состояния буфера."""
        return f"RingBuffer(size={self._size}, capacity={self._capacity}, items={self.to_list()})"
