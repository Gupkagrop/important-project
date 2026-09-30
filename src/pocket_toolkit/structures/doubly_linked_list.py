"""Реализация двусвязного списка с быстрым удалением узлов за O(1)."""

from collections.abc import Iterable, Iterator


class DoublyNode[T]:
    """Узел двусвязного списка.

    Содержит хранимое значение, а также ссылки на предыдущий и следующий узлы.
    """

    __slots__ = ("next", "prev", "value")

    def __init__(
        self,
        value: T,
        prev_node: "DoublyNode[T] | None" = None,
        next_node: "DoublyNode[T] | None" = None,
    ) -> None:
        """Инициализирует узел двусвязного списка.

        :param value: Полезная нагрузка узла.
        :param prev_node: Ссылка на предыдущий узел цепочки.
        :param next_node: Ссылка на следующий узел цепочки.
        """
        self.value: T = value
        self.prev: DoublyNode[T] | None = prev_node
        self.next: DoublyNode[T] | None = next_node

    def __repr__(self) -> str:
        """Строковое представление узла."""
        return f"DoublyNode(value={self.value!r})"


class DoublyLinkedList[T]:
    """Двусвязный список с поддержкой двусторонней итерации и O(1) удаления узлов."""

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        """Инициализирует пустой двусвязный список или наполняет его элементами.

        :param iterable: Опциональная последовательность начальных элементов.
        """
        self._head: DoublyNode[T] | None = None
        self._tail: DoublyNode[T] | None = None
        self._size: int = 0

        if iterable is not None:
            for item in iterable:
                self.append(item)

    @property
    def head_node(self) -> DoublyNode[T] | None:
        """Возвращает первый узел списка или None, если список пуст."""
        return self._head

    @property
    def tail_node(self) -> DoublyNode[T] | None:
        """Возвращает последний узел списка или None, если список пуст."""
        return self._tail

    def is_empty(self) -> bool:
        """Проверяет, пуст ли список."""
        return self._size == 0

    def append_node(self, node: DoublyNode[T]) -> None:
        """Вставляет свободный узел в конец списка за O(1).

        :param node: Добавляемый узел.
        """
        node.prev = self._tail
        node.next = None

        if self._tail is None:
            self._head = node
            self._tail = node
            self._size += 1
            return

        self._tail.next = node
        self._tail = node
        self._size += 1

    def prepend_node(self, node: DoublyNode[T]) -> None:
        """Вставляет свободный узел в начало списка за O(1).

        :param node: Добавляемый узел.
        """
        node.prev = None
        node.next = self._head

        if self._head is None:
            self._head = node
            self._tail = node
            self._size += 1
            return

        self._head.prev = node
        self._head = node
        self._size += 1

    def append(self, item: T) -> DoublyNode[T]:
        """Создает новый узел со значением и добавляет его в конец списка за O(1).

        :param item: Добавляемое значение.
        :return: Созданный узел списка.
        """
        node: DoublyNode[T] = DoublyNode(item)
        self.append_node(node)
        return node

    def prepend(self, item: T) -> DoublyNode[T]:
        """Создает новый узел со значением и добавляет его в начало списка за O(1).

        :param item: Добавляемое значение.
        :return: Созданный узел списка.
        """
        node: DoublyNode[T] = DoublyNode(item)
        self.prepend_node(node)
        return node

    def popleft(self) -> T:
        """Удаляет и возвращает первый элемент списка за O(1).

        :return: Значение удаленного первого элемента.
        :raises IndexError: Если список пуст.
        """
        if self._head is None:
            raise IndexError("Невозможно извлечь элемент: список пуст")

        target: DoublyNode[T] = self._head
        self._head = target.next

        if self._head is not None:
            self._head.prev = None
        else:
            self._tail = None

        target.prev = None
        target.next = None
        self._size -= 1
        return target.value

    def pop(self) -> T:
        """Удаляет и возвращает последний элемент списка за O(1).

        :return: Значение удаленного последнего элемента.
        :raises IndexError: Если список пуст.
        """
        if self._tail is None:
            raise IndexError("Невозможно извлечь элемент: список пуст")

        target: DoublyNode[T] = self._tail
        self._tail = target.prev

        if self._tail is not None:
            self._tail.next = None
        else:
            self._head = None

        target.prev = None
        target.next = None
        self._size -= 1
        return target.value

    def peek_head(self) -> T:
        """Возвращает значение первого элемента без его удаления.

        :return: Значение первого узла.
        :raises IndexError: Если список пуст.
        """
        if self._head is None:
            raise IndexError("Список пуст")
        return self._head.value

    def peek_tail(self) -> T:
        """Возвращает значение последнего элемента без его удаления.

        :return: Значение последнего узла.
        :raises IndexError: Если список пуст.
        """
        if self._tail is None:
            raise IndexError("Список пуст")
        return self._tail.value

    def unlink(self, node: DoublyNode[T]) -> T:
        """Удаляет указанный узел из списка за O(1).

        :param node: Целевой узел для отсоединения.
        :return: Значение отсоединенного узла.
        :raises ValueError: Если список пуст или узел поврежден/не принадлежит списку.
        """
        if self._size == 0:
            raise ValueError("Невозможно отсоединить узел: список пуст")

        if node is self._head:
            return self.popleft()

        if node is self._tail:
            return self.pop()

        prev_node: DoublyNode[T] | None = node.prev
        next_node: DoublyNode[T] | None = node.next

        if prev_node is None or next_node is None:
            raise ValueError("Узел не принадлежит текущему списку или уже отсоединен")

        prev_node.next = next_node
        next_node.prev = prev_node

        node.prev = None
        node.next = None
        self._size -= 1
        return node.value

    def move_to_end(self, node: DoublyNode[T]) -> None:
        """Перемещает существующий узел в конец списка за O(1).

        :param node: Перемещаемый узел.
        """
        if node is self._tail:
            return
        self.unlink(node)
        self.append_node(node)

    def move_to_front(self, node: DoublyNode[T]) -> None:
        """Перемещает существующий узел в начало списка за O(1).

        :param node: Перемещаемый узел.
        """
        if node is self._head:
            return
        self.unlink(node)
        self.prepend_node(node)

    def remove(self, item: T) -> bool:
        """Удаляет первое вхождение элемента по значению.

        :param item: Искомое значение для удаления.
        :return: True, если элемент найден и удален; False в противном случае.
        """
        for node in self.iter_nodes():
            if node.value == item:
                self.unlink(node)
                return True
        return False

    def clear(self) -> None:
        """Очищает список и разрывает связи между узлами."""
        current: DoublyNode[T] | None = self._head
        while current is not None:
            next_node: DoublyNode[T] | None = current.next
            current.prev = None
            current.next = None
            current = next_node

        self._head = None
        self._tail = None
        self._size = 0

    def to_list(self) -> list[T]:
        """Возвращает элементы списка в прямом порядке (от головы к хвосту)."""
        return list(self)

    def to_reverse_list(self) -> list[T]:
        """Возвращает элементы списка в обратном порядке (от хвоста к голове)."""
        return list(reversed(self))

    def _get_node_at(self, index: int) -> DoublyNode[T]:
        """Возвращает узел по нормализованному индексу, оптимизируя направление обхода.

        :param index: Скорректированный неотрицательный индекс.
        :return: Целевой узел цепочки.
        """
        if index < self._size // 2:
            current: DoublyNode[T] | None = self._head
            assert current is not None
            for _ in range(index):
                assert current.next is not None
                current = current.next
            return current

        current = self._tail
        assert current is not None
        for _ in range(self._size - 1 - index):
            assert current.prev is not None
            current = current.prev
        return current

    def iter_nodes(self) -> Iterator[DoublyNode[T]]:
        """Итерирует по объектам узлов от головы к хвосту."""
        current: DoublyNode[T] | None = self._head
        while current is not None:
            yield current
            current = current.next

    def iter_nodes_reversed(self) -> Iterator[DoublyNode[T]]:
        """Итерирует по объектам узлов от хвоста к голове."""
        current: DoublyNode[T] | None = self._tail
        while current is not None:
            yield current
            current = current.prev

    def __len__(self) -> int:
        """Возвращает общее количество элементов в списке."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Прямой обход значений элементов списка от головы к хвосту."""
        for node in self.iter_nodes():
            yield node.value

    def __reversed__(self) -> Iterator[T]:
        """Обратный обход значений элементов списка от хвоста к голове."""
        for node in self.iter_nodes_reversed():
            yield node.value

    def __contains__(self, item: object) -> bool:
        """Проверяет наличие элемента в списке."""
        for value in self:
            if value == item:
                return True
        return False

    def __getitem__(self, index: int) -> T:
        """Возвращает элемент по индексу (поддерживает отрицательные индексы).

        :param index: Индекс элемента.
        :return: Значение узла.
        :raises IndexError: Если индекс выходит за границы списка.
        """
        normalized_index: int = index if index >= 0 else index + self._size
        if normalized_index < 0 or normalized_index >= self._size:
            raise IndexError("Индекс выходит за границы двусвязного списка")

        return self._get_node_at(normalized_index).value

    def __repr__(self) -> str:
        """Строковое представление списка."""
        return f"DoublyLinkedList({self.to_list()!r})"
