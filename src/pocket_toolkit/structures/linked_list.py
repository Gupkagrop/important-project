"""Реализация односвязного списка."""

from collections.abc import Iterable, Iterator


class Node[T]:
    """Узел односвязного списка.

    Содержит хранимое значение и ссылку на следующий узел.
    """

    __slots__ = ("next", "value")

    def __init__(self, value: T, next_node: "Node[T] | None" = None) -> None:
        """Инициализирует узел со значением и опциональным указателем на следующий.

        :param value: Полезная нагрузка узла.
        :param next_node: Ссылка на следующий узел цепочки.
        """
        self.value: T = value
        self.next: Node[T] | None = next_node

    def __repr__(self) -> str:
        """Строковое представление узла."""
        return f"Node(value={self.value!r})"


class LinkedList[T]:
    """Односвязный список с поддержкой быстрого добавления в начало и конец.

    Поддерживает вставку за O(1), удаление по значению, доступ по индексу и обход.
    """

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        """Создает пустой список или наполняет его элементами из переданной последовательности.

        :param iterable: Опциональная последовательность начальных элементов.
        """
        self._head: Node[T] | None = None
        self._tail: Node[T] | None = None
        self._size: int = 0

        if iterable is not None:
            for item in iterable:
                self.append(item)

    def is_empty(self) -> bool:
        """Проверяет, пуст ли список."""
        return self._size == 0

    def append(self, item: T) -> None:
        """Добавляет элемент в конец списка за O(1).

        :param item: Добавляемое значение.
        """
        new_node: Node[T] = Node(item)
        if self._tail is None:
            self._head = new_node
            self._tail = new_node
            self._size += 1
            return

        self._tail.next = new_node
        self._tail = new_node
        self._size += 1

    def prepend(self, item: T) -> None:
        """Добавляет элемент в начало списка за O(1).

        :param item: Добавляемое значение.
        """
        new_node: Node[T] = Node(item, next_node=self._head)
        self._head = new_node
        if self._tail is None:
            self._tail = new_node
        self._size += 1

    def popleft(self) -> T:
        """Удаляет и возвращает первый элемент списка за O(1).

        :return: Извлеченный элемент.
        :raises IndexError: Если список пуст.
        """
        if self._head is None:
            raise IndexError("Невозможно извлечь элемент: список пуст")

        target: Node[T] = self._head
        self._head = target.next
        self._size -= 1

        if self._head is None:
            self._tail = None

        return target.value

    def pop(self) -> T:
        """Удаляет и возвращает последний элемент списка за O(n).

        :return: Извлеченный элемент.
        :raises IndexError: Если список пуст.
        """
        if self._head is None:
            raise IndexError("Невозможно извлечь элемент: список пуст")

        if self._head is self._tail:
            value: T = self._head.value
            self._head = None
            self._tail = None
            self._size = 0
            return value

        current: Node[T] = self._head
        while current.next is not None and current.next is not self._tail:
            current = current.next

        assert self._tail is not None
        last_value: T = self._tail.value
        current.next = None
        self._tail = current
        self._size -= 1
        return last_value

    def peek_head(self) -> T:
        """Возвращает первый элемент без его удаления.

        :return: Значение первого узла.
        :raises IndexError: Если список пуст.
        """
        if self._head is None:
            raise IndexError("Список пуст")
        return self._head.value

    def peek_tail(self) -> T:
        """Возвращает последний элемент без его удаления.

        :return: Значение последнего узла.
        :raises IndexError: Если список пуст.
        """
        if self._tail is None:
            raise IndexError("Список пуст")
        return self._tail.value

    def remove(self, item: T) -> bool:
        """Удаляет первое вхождение элемента по значению.

        :param item: Искомое значение для удаления.
        :return: True, если узел найден и удален; False в противном случае.
        """
        if self._head is None:
            return False

        if self._head.value == item:
            self.popleft()
            return True

        prev: Node[T] = self._head
        curr: Node[T] | None = self._head.next

        while curr is not None:
            if curr.value == item:
                prev.next = curr.next
                if curr is self._tail:
                    self._tail = prev
                self._size -= 1
                return True
            prev = curr
            curr = curr.next

        return False

    def clear(self) -> None:
        """Очищает список, сбрасывая ссылки на узлы и счетчик длины."""
        self._head = None
        self._tail = None
        self._size = 0

    def to_list(self) -> list[T]:
        """Преобразует элементы списка в стандартный список Python."""
        return list(self)

    def _get_node_at(self, index: int) -> Node[T]:
        """Возвращает узел по нормализованному индексу.

        :param index: Скорректированный неотрицательный индекс.
        :return: Целевой узел цепочки.
        """
        current: Node[T] | None = self._head
        assert current is not None
        for _ in range(index):
            assert current.next is not None
            current = current.next
        return current

    def __len__(self) -> int:
        """Возвращает общее количество узлов в списке."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Прямой обход элементов списка от головы к хвосту."""
        current: Node[T] | None = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __contains__(self, item: object) -> bool:
        """Проверяет наличие элемента в списке."""
        for val in self:
            if val == item:
                return True
        return False

    def __getitem__(self, index: int) -> T:
        """Возвращает элемент по индексу (поддерживает отрицательные индексы).

        :param index: Индекс элемента.
        :return: Значение узла.
        :raises IndexError: Если индекс выходит за границы.
        """
        normalized_index: int = index if index >= 0 else index + self._size
        if normalized_index < 0 or normalized_index >= self._size:
            raise IndexError("Индекс выходит за границы связного списка")

        return self._get_node_at(normalized_index).value

    def __repr__(self) -> str:
        """Строковое представление списка."""
        return f"LinkedList({self.to_list()!r})"
