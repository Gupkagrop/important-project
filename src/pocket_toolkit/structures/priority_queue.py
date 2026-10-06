"""Реализация очереди с приоритетами (Priority Queue) на базе бинарной кучи.

Поддерживает режимы минимального (min-heap) и максимального (max-heap) приоритета,
стабильное разрешение коллизий (FIFO для одинаковых приоритетов), а также работу
с пользовательскими функциями вычисления приоритета key.
"""

from collections.abc import Callable, Iterable, Iterator
from typing import Protocol, cast


class Comparable(Protocol):
    """Протокол для объектов, поддерживающих оператор строгого сравнения меньше (<)."""

    def __lt__(self, other: "Comparable", /) -> bool:
        """Сравнивает текущий объект с другим объектом на строгое неравенство меньше."""
        ...


class PriorityItem[T]:
    """Элемент очереди с приоритетом, содержащий значение и его приоритет.

    Используется для явного представления пары (значение, приоритет).
    """

    __slots__ = ("item", "priority")

    def __init__(self, item: T, priority: Comparable) -> None:
        """Инициализирует пару элемент-приоритет.

        :param item: Полезная нагрузка (хранимый элемент).
        :param priority: Значение приоритета элемента.
        """
        self.item: T = item
        self.priority: Comparable = priority

    def __repr__(self) -> str:
        """Строковое представление элемента очереди с приоритетом."""
        return f"PriorityItem(item={self.item!r}, priority={self.priority!r})"

    def __eq__(self, other: object) -> bool:
        """Проверяет равенство элементов очереди."""
        if not isinstance(other, PriorityItem):
            return False
        return self.item == other.item and self.priority == other.priority


class _HeapEntry[T]:
    """Внутренний контейнер бинарной кучи.

    Хранит вычисленный приоритет, порядковый номер добавления для поддержания
    стабильности (FIFO для равных приоритетов) и сам хранимый элемент.
    """

    __slots__ = ("count", "item", "priority")

    def __init__(self, priority: Comparable, count: int, item: T) -> None:
        """Инициализирует внутреннюю запись бинарной кучи.

        :param priority: Значение приоритета элемента.
        :param count: Монотонно возрастающий счетчик добавления для стабильности.
        :param item: Хранимый элемент.
        """
        self.priority: Comparable = priority
        self.count: int = count
        self.item: T = item

    def __repr__(self) -> str:
        """Строковое представление внутренней записи."""
        return f"_HeapEntry(priority={self.priority!r}, count={self.count}, item={self.item!r})"


class PriorityQueue[T]:
    """Очередь с приоритетами на основе двоичной кучи (Binary Heap).

    Обеспечивает логарифмическую сложность O(log n) для вставки и извлечения,
    константную сложность O(1) для просмотра вершины кучи и линейную сложность O(n)
    для построения кучи из готовой коллекции элементов (heapify).

    Поддерживает:
    - Min-heap (по умолчанию) и Max-heap (max_heap=True);
    - Стабильность очереди (FIFO для элементов с одинаковым приоритетом);
    - Произвольную функцию вычисления приоритета key;
    - Явное задание приоритета при вызове push(item, priority=...);
    - Автоматическое использование самого элемента как приоритета, если он сравним.
    """

    def __init__(
        self,
        items: Iterable[T] | None = None,
        *,
        max_heap: bool = False,
        key: Callable[[T], Comparable] | None = None,
    ) -> None:
        """Инициализирует очередь с приоритетами.

        :param items: Начальная коллекция элементов для заполнения очереди.
        :param max_heap: Если True, очередь работает в режиме max-heap (наибольший
                         приоритет извлекается первым). По умолчанию False (min-heap).
        :param key: Опциональная функция для вычисления приоритета из элемента.
        """
        self._is_max_heap: bool = max_heap
        self._key: Callable[[T], Comparable] | None = key
        self._heap: list[_HeapEntry[T]] = []
        self._entry_counter: int = 0

        if items is not None:
            self._populate_initial_items(items)

    @classmethod
    def from_priorities(
        cls,
        items: Iterable[tuple[T, Comparable]],
        *,
        max_heap: bool = False,
    ) -> "PriorityQueue[T]":
        """Создает очередь из последовательности пар (элемент, приоритет) за O(n).

        :param items: Итерируемая последовательность пар (элемент, приоритет).
        :param max_heap: Флаг режима максимальной кучи.
        :return: Новая инициализированная очередь с приоритетами.
        """
        queue: PriorityQueue[T] = cls(max_heap=max_heap)
        entries: list[_HeapEntry[T]] = []
        counter: int = 0

        for item, priority in items:
            entries.append(_HeapEntry(priority=priority, count=counter, item=item))
            counter += 1

        queue._heap = entries
        queue._entry_counter = counter
        queue._heapify()
        return queue

    @property
    def is_max_heap(self) -> bool:
        """Возвращает True, если очередь функционирует в режиме max-heap."""
        return self._is_max_heap

    @property
    def is_min_heap(self) -> bool:
        """Возвращает True, если очередь функционирует в режиме min-heap."""
        return not self._is_max_heap

    def is_empty(self) -> bool:
        """Проверяет, пуста ли очередь с приоритетами."""
        return len(self._heap) == 0

    def push(self, item: T, priority: Comparable | None = None) -> None:
        """Добавляет элемент в очередь с приоритетом за O(log n).

        :param item: Добавляемый элемент.
        :param priority: Опциональный явный приоритет. Если None, приоритет
                         вычисляется через key или используется сам элемент.
        """
        resolved_priority: Comparable = self._resolve_priority(item, priority)
        entry: _HeapEntry[T] = _HeapEntry(
            priority=resolved_priority,
            count=self._entry_counter,
            item=item,
        )
        self._entry_counter += 1
        self._heap.append(entry)
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> T:
        """Извлекает и возвращает элемент с наивысшим приоритетом за O(log n).

        :return: Хранимый элемент с наивысшим приоритетом.
        :raises IndexError: Если очередь пуста.
        """
        if not self._heap:
            raise IndexError("Очередь с приоритетами пуста")

        root_entry: _HeapEntry[T] = self._heap[0]
        last_entry: _HeapEntry[T] = self._heap.pop()

        if self._heap:
            self._heap[0] = last_entry
            self._sift_down(0)

        return root_entry.item

    def pop_with_priority(self) -> tuple[T, Comparable]:
        """Извлекает пару (элемент, приоритет) с наивысшим приоритетом за O(log n).

        :return: Кортеж (элемент, приоритет).
        :raises IndexError: Если очередь пуста.
        """
        if not self._heap:
            raise IndexError("Очередь с приоритетами пуста")

        root_entry: _HeapEntry[T] = self._heap[0]
        last_entry: _HeapEntry[T] = self._heap.pop()

        if self._heap:
            self._heap[0] = last_entry
            self._sift_down(0)

        return root_entry.item, root_entry.priority

    def pop_item(self) -> PriorityItem[T]:
        """Извлекает объект PriorityItem с наивысшим приоритетом за O(log n).

        :return: Экземпляр PriorityItem(item, priority).
        :raises IndexError: Если очередь пуста.
        """
        item, priority = self.pop_with_priority()
        return PriorityItem(item=item, priority=priority)

    def peek(self) -> T:
        """Возвращает элемент с наивысшим приоритетом без удаления за O(1).

        :return: Хранимый элемент с наивысшим приоритетом.
        :raises IndexError: Если очередь пуста.
        """
        if not self._heap:
            raise IndexError("Очередь с приоритетами пуста")
        return self._heap[0].item

    def peek_with_priority(self) -> tuple[T, Comparable]:
        """Возвращает пару (элемент, приоритет) с наивысшим приоритетом без удаления за O(1).

        :return: Кортеж (элемент, приоритет).
        :raises IndexError: Если очередь пуста.
        """
        if not self._heap:
            raise IndexError("Очередь с приоритетами пуста")
        root_entry: _HeapEntry[T] = self._heap[0]
        return root_entry.item, root_entry.priority

    def peek_item(self) -> PriorityItem[T]:
        """Возвращает объект PriorityItem с наивысшим приоритетом без удаления за O(1).

        :return: Экземпляр PriorityItem(item, priority).
        :raises IndexError: Если очередь пуста.
        """
        item, priority = self.peek_with_priority()
        return PriorityItem(item=item, priority=priority)

    def pushpop(self, item: T, priority: Comparable | None = None) -> T:
        """Добавляет элемент и сразу извлекает элемент с наивысшим приоритетом.

        Оптимизированная операция за один проход O(log n). Если добавляемый элемент
        имеет наивысший приоритет, он сразу же возвращается без модификации кучи.

        :param item: Добавляемый элемент.
        :param priority: Опциональный приоритет элемента.
        :return: Элемент с наивысшим приоритетом.
        """
        resolved_priority: Comparable = self._resolve_priority(item, priority)
        new_entry: _HeapEntry[T] = _HeapEntry(
            priority=resolved_priority,
            count=self._entry_counter,
            item=item,
        )
        self._entry_counter += 1

        if not self._heap:
            return item

        if self._is_higher_priority(new_entry, self._heap[0]):
            return item

        root_item: T = self._heap[0].item
        self._heap[0] = new_entry
        self._sift_down(0)
        return root_item

    def replace(self, item: T, priority: Comparable | None = None) -> T:
        """Извлекает корень кучи и помещает новый элемент на его место за O(log n).

        Размер кучи остается неизменным. В отличие от pushpop(), всегда извлекает
        элемент из ранее заполненной очереди.

        :param item: Добавляемый элемент.
        :param priority: Опциональный приоритет элемента.
        :return: Предыдущий элемент корня кучи.
        :raises IndexError: Если очередь пуста.
        """
        if not self._heap:
            raise IndexError("Очередь с приоритетами пуста")

        resolved_priority: Comparable = self._resolve_priority(item, priority)
        new_entry: _HeapEntry[T] = _HeapEntry(
            priority=resolved_priority,
            count=self._entry_counter,
            item=item,
        )
        self._entry_counter += 1

        old_root_item: T = self._heap[0].item
        self._heap[0] = new_entry
        self._sift_down(0)
        return old_root_item

    def remove(self, item: T) -> bool:
        """Удаляет первое вхождение заданного элемента из очереди за O(n).

        :param item: Элемент для удаления.
        :return: True, если элемент найден и успешно удален, иначе False.
        """
        index: int = self._find_index_by_item(item)
        if index == -1:
            return False

        self._remove_at_index(index)
        return True

    def update_priority(self, item: T, new_priority: Comparable) -> bool:
        """Обновляет приоритет первого найденного элемента за O(n).

        :param item: Элемент, приоритет которого требуется обновить.
        :param new_priority: Новое значение приоритета.
        :return: True, если элемент найден и приоритет обновлен, иначе False.
        """
        index: int = self._find_index_by_item(item)
        if index == -1:
            return False

        entry: _HeapEntry[T] = self._heap[index]
        entry.priority = new_priority
        parent_index: int = (index - 1) // 2

        if index > 0 and self._is_higher_priority(entry, self._heap[parent_index]):
            self._sift_up(index)
            return True

        self._sift_down(index)
        return True

    def clear(self) -> None:
        """Полностью очищает очередь с приоритетами."""
        self._heap.clear()
        self._entry_counter = 0

    def copy(self) -> "PriorityQueue[T]":
        """Создает поверхностную копию очереди с идентичным состоянием кучи."""
        cloned: PriorityQueue[T] = PriorityQueue(
            max_heap=self._is_max_heap,
            key=self._key,
        )
        cloned._heap = list(self._heap)
        cloned._entry_counter = self._entry_counter
        return cloned

    def to_list(self) -> list[T]:
        """Возвращает отсортированный по приоритету список элементов без модификации очереди."""
        cloned: PriorityQueue[T] = self.copy()
        result: list[T] = []
        while not cloned.is_empty():
            result.append(cloned.pop())
        return result

    def to_priority_list(self) -> list[tuple[T, Comparable]]:
        """Возвращает отсортированный по приоритету список пар (элемент, приоритет)."""
        cloned: PriorityQueue[T] = self.copy()
        result: list[tuple[T, Comparable]] = []
        while not cloned.is_empty():
            result.append(cloned.pop_with_priority())
        return result

    def drain(self) -> Iterator[T]:
        """Последовательно извлекает и возвращает все элементы до опустошения очереди."""
        while not self.is_empty():
            yield self.pop()

    def drain_with_priority(self) -> Iterator[tuple[T, Comparable]]:
        """Последовательно извлекает пары (элемент, приоритет) до опустошения очереди."""
        while not self.is_empty():
            yield self.pop_with_priority()

    def _resolve_priority(self, item: T, priority: Comparable | None) -> Comparable:
        """Определяет значение приоритета для элемента."""
        if priority is not None:
            return priority

        if self._key is not None:
            return self._key(item)

        return cast(Comparable, item)

    def _is_higher_priority(self, a: _HeapEntry[T], b: _HeapEntry[T]) -> bool:
        """Сравнивает два элемента кучи на строго большее преимущество в приоритете.

        Обеспечивает FIFO-стабильность: при равенстве приоритетов преимущество
        получает элемент, добавленный в очередь раньше (с меньшим счетчиком count).
        """
        if self._is_max_heap:
            if b.priority < a.priority:
                return True
            if a.priority < b.priority:
                return False
            return a.count < b.count

        if a.priority < b.priority:
            return True
        if b.priority < a.priority:
            return False
        return a.count < b.count

    def _sift_up(self, index: int) -> None:
        """Просеивает элемент вверх по куче до восстановления свойств кучи."""
        entry: _HeapEntry[T] = self._heap[index]
        while index > 0:
            parent_index: int = (index - 1) // 2
            parent_entry: _HeapEntry[T] = self._heap[parent_index]
            if not self._is_higher_priority(entry, parent_entry):
                break
            self._heap[index] = parent_entry
            index = parent_index
        self._heap[index] = entry

    def _sift_down(self, index: int) -> None:
        """Просеивает элемент вниз по куче до восстановления свойств кучи."""
        size: int = len(self._heap)
        entry: _HeapEntry[T] = self._heap[index]

        while True:
            left_index: int = 2 * index + 1
            if left_index >= size:
                break

            best_index: int = left_index
            right_index: int = left_index + 1

            if right_index < size and self._is_higher_priority(
                self._heap[right_index], self._heap[left_index]
            ):
                best_index = right_index

            if not self._is_higher_priority(self._heap[best_index], entry):
                break

            self._heap[index] = self._heap[best_index]
            index = best_index

        self._heap[index] = entry

    def _heapify(self) -> None:
        """Строит корректную структуру двоичной кучи за линейное время O(n)."""
        start_index: int = (len(self._heap) // 2) - 1
        for i in range(start_index, -1, -1):
            self._sift_down(i)

    def _populate_initial_items(self, items: Iterable[T]) -> None:
        """Заполняет кучу начальными элементами и строит кучу за O(n)."""
        for item in items:
            priority: Comparable = self._resolve_priority(item, None)
            self._heap.append(
                _HeapEntry(priority=priority, count=self._entry_counter, item=item)
            )
            self._entry_counter += 1
        self._heapify()

    def _find_index_by_item(self, item: T) -> int:
        """Находит индекс первого совпадения элемента в массиве кучи."""
        for i, entry in enumerate(self._heap):
            if entry.item == item:
                return i
        return -1

    def _remove_at_index(self, index: int) -> None:
        """Удаляет элемент по индексу и восстанавливает инвариант кучи."""
        last_entry: _HeapEntry[T] = self._heap.pop()
        if index == len(self._heap):
            return

        self._heap[index] = last_entry
        parent_index: int = (index - 1) // 2

        if index > 0 and self._is_higher_priority(last_entry, self._heap[parent_index]):
            self._sift_up(index)
            return

        self._sift_down(index)

    def __len__(self) -> int:
        """Возвращает текущее количество элементов в очереди."""
        return len(self._heap)

    def __bool__(self) -> bool:
        """Возвращает True, если очередь содержит хотя бы один элемент."""
        return not self.is_empty()

    def __contains__(self, item: object) -> bool:
        """Проверяет наличие элемента в очереди за O(n)."""
        return any(entry.item == item for entry in self._heap)

    def __iter__(self) -> Iterator[T]:
        """Итерирует по элементам очереди во внутреннем порядке кучи."""
        for entry in self._heap:
            yield entry.item

    def __repr__(self) -> str:
        """Строковое представление очереди с приоритетами."""
        mode: str = "max" if self._is_max_heap else "min"
        return f"PriorityQueue(size={len(self._heap)}, mode={mode!r})"

    def __eq__(self, other: object) -> bool:
        """Проверяет эквивалентность двух очередей с приоритетами."""
        if not isinstance(other, PriorityQueue):
            return False
        if self._is_max_heap != other._is_max_heap:
            return False
        return self.to_priority_list() == other.to_priority_list()
