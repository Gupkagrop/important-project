"""Реализация кэша вытеснения по давности (LRU Cache) с временем доступа O(1)."""

from collections.abc import Iterable, Iterator

from pocket_toolkit.structures.doubly_linked_list import DoublyLinkedList, DoublyNode


class _CacheEntry[K, V]:
    """Внутренний контейнер для хранения ключа и значения в двусвязном списке кэша."""

    __slots__ = ("key", "value")

    def __init__(self, key: K, value: V) -> None:
        """Инициализирует пару ключ-значение кэша.

        :param key: Ключ элемента.
        :param value: Значение элемента.
        """
        self.key: K = key
        self.value: V = value

    def __repr__(self) -> str:
        """Строковое представление внутренней записи кэша."""
        return f"_CacheEntry(key={self.key!r}, value={self.value!r})"


class LRUCache[K, V]:
    """Кэш вытеснения по давности использования (Least Recently Used Cache).

    Обеспечивает алгоритмическую сложность основных операций O(1) за счет
    комбинации хэш-таблицы (словаря) для мгновенного поиска и двусвязного
    списка для поддержания строгого порядка использования элементов.
    """

    def __init__(
        self,
        capacity: int,
        initial_items: Iterable[tuple[K, V]] | None = None,
    ) -> None:
        """Инициализирует кэш заданной максимальной вместимости.

        :param capacity: Максимальное количество элементов (должно быть строго > 0).
        :param initial_items: Опциональная последовательность начальных пар (ключ, значение).
        :raises ValueError: Если вместимость меньше либо равна нулю.
        """
        if capacity <= 0:
            raise ValueError("Вместимость кэша должна быть строго больше нуля")

        self._capacity: int = capacity
        self._lookup: dict[K, DoublyNode[_CacheEntry[K, V]]] = {}
        self._list: DoublyLinkedList[_CacheEntry[K, V]] = DoublyLinkedList()
        self._hits: int = 0
        self._misses: int = 0

        if initial_items is not None:
            for key, value in initial_items:
                self.put(key, value)

    @property
    def capacity(self) -> int:
        """Возвращает максимальную вместимость кэша."""
        return self._capacity

    @property
    def size(self) -> int:
        """Возвращает текущее количество сохраненных элементов."""
        return len(self._lookup)

    @property
    def hits(self) -> int:
        """Возвращает количество успешных обращений к кэшу."""
        return self._hits

    @property
    def misses(self) -> int:
        """Возвращает количество промахов мимо кэша."""
        return self._misses

    @property
    def hit_ratio(self) -> float:
        """Возвращает долю попаданий в кэш от общего числа запросов."""
        total_requests: int = self._hits + self._misses
        if total_requests == 0:
            return 0.0
        return self._hits / total_requests

    def is_empty(self) -> bool:
        """Проверяет, пуст ли кэш."""
        return len(self._lookup) == 0

    def is_full(self) -> bool:
        """Проверяет, заполнен ли кэш до предельной вместимости."""
        return len(self._lookup) >= self._capacity

    def _evict_lru(self) -> _CacheEntry[K, V]:
        """Вспомогательный метод вытеснения наименее востребованного элемента (хвоста)."""
        evicted_entry: _CacheEntry[K, V] = self._list.pop()
        del self._lookup[evicted_entry.key]
        return evicted_entry

    def put(self, key: K, value: V) -> None:
        """Помещает пару ключ-значение в кэш.

        Если ключ уже существует, обновляет значение и перемещает узел в начало (MRU).
        Если кэш заполнен до предела, вытесняет наименее востребованный элемент (LRU).

        :param key: Ключ элемента.
        :param value: Значение элемента.
        """
        if key in self._lookup:
            node: DoublyNode[_CacheEntry[K, V]] = self._lookup[key]
            node.value.value = value
            self._list.move_to_front(node)
            return

        if self.is_full():
            self._evict_lru()

        entry: _CacheEntry[K, V] = _CacheEntry(key, value)
        new_node: DoublyNode[_CacheEntry[K, V]] = self._list.prepend(entry)
        self._lookup[key] = new_node

    def get(self, key: K, default: V | None = None) -> V | None:
        """Возвращает значение по ключу, обновляя его позицию как наиболее свежего (MRU).

        :param key: Искомый ключ.
        :param default: Значение по умолчанию, если ключ отсутствует.
        :return: Значение элемента или default.
        """
        if key not in self._lookup:
            self._misses += 1
            return default

        node: DoublyNode[_CacheEntry[K, V]] = self._lookup[key]
        self._list.move_to_front(node)
        self._hits += 1
        return node.value.value

    def peek(self, key: K, default: V | None = None) -> V | None:
        """Возвращает значение по ключу без перемещения в начало и без учета статистики.

        :param key: Искомый ключ.
        :param default: Значение по умолчанию, если ключ отсутствует.
        :return: Значение элемента или default.
        """
        if key not in self._lookup:
            return default
        return self._lookup[key].value.value

    def peek_lru(self) -> tuple[K, V] | None:
        """Возвращает пару (ключ, значение) наименее востребованного элемента без его удаления.

        :return: Кортеж (ключ, значение) или None, если кэш пуст.
        """
        tail: DoublyNode[_CacheEntry[K, V]] | None = self._list.tail_node
        if tail is None:
            return None
        return tail.value.key, tail.value.value

    def peek_mru(self) -> tuple[K, V] | None:
        """Возвращает пару (ключ, значение) наиболее востребованного элемента без его удаления.

        :return: Кортеж (ключ, значение) или None, если кэш пуст.
        """
        head: DoublyNode[_CacheEntry[K, V]] | None = self._list.head_node
        if head is None:
            return None
        return head.value.key, head.value.value

    def pop(self, key: K) -> V:
        """Извлекает и удаляет элемент по ключу из кэша.

        :param key: Ключ удаляемого элемента.
        :return: Значение удаленного элемента.
        :raises KeyError: Если ключ не найден в кэше.
        """
        if key not in self._lookup:
            raise KeyError(f"Ключ {key!r} не найден в кэше")

        node: DoublyNode[_CacheEntry[K, V]] = self._lookup.pop(key)
        entry: _CacheEntry[K, V] = self._list.unlink(node)
        return entry.value

    def pop_lru(self) -> tuple[K, V]:
        """Удаляет и возвращает наименее востребованный элемент (LRU).

        :return: Кортеж (ключ, значение) вытесненного элемента.
        :raises KeyError: Если кэш пуст.
        """
        if self.is_empty():
            raise KeyError("Невозможно извлечь элемент: кэш пуст")

        evicted: _CacheEntry[K, V] = self._evict_lru()
        return evicted.key, evicted.value

    def pop_mru(self) -> tuple[K, V]:
        """Удаляет и возвращает наиболее востребованный элемент (MRU).

        :return: Кортеж (ключ, значение) извлеченного элемента.
        :raises KeyError: Если кэш пуст.
        """
        if self.is_empty():
            raise KeyError("Невозможно извлечь элемент: кэш пуст")

        entry: _CacheEntry[K, V] = self._list.popleft()
        del self._lookup[entry.key]
        return entry.key, entry.value

    def delete(self, key: K) -> bool:
        """Безопасно удаляет элемент по ключу.

        :param key: Удаляемый ключ.
        :return: True, если элемент присутствовал и был успешно удален; False в противном случае.
        """
        if key not in self._lookup:
            return False

        node: DoublyNode[_CacheEntry[K, V]] = self._lookup.pop(key)
        self._list.unlink(node)
        return True

    def resize(self, new_capacity: int) -> int:
        """Изменяет максимальную вместимость кэша.

        Если новая вместимость меньше текущего количества элементов, последовательно
        вытесняются наименее востребованные элементы до достижения нового лимита.

        :param new_capacity: Новая вместимость кэша (строго > 0).
        :return: Количество вытесненных элементов.
        :raises ValueError: Если new_capacity <= 0.
        """
        if new_capacity <= 0:
            raise ValueError("Новая вместимость кэша должна быть больше 0")

        evicted_count: int = 0
        while len(self._lookup) > new_capacity:
            self._evict_lru()
            evicted_count += 1

        self._capacity = new_capacity
        return evicted_count

    def clear(self, reset_stats: bool = False) -> None:
        """Очищает кэш от всех сохраненных элементов.

        :param reset_stats: Сбрасывать ли счетчики попаданий и промахов.
        """
        self._lookup.clear()
        self._list.clear()
        if reset_stats:
            self.reset_stats()

    def reset_stats(self) -> None:
        """Сбрасывает счетчики попаданий и промахов к нулю."""
        self._hits = 0
        self._misses = 0

    def keys(self) -> list[K]:
        """Возвращает список ключей в порядке от наиболее к наименее востребованным."""
        return [node.value.key for node in self._list.iter_nodes()]

    def values(self) -> list[V]:
        """Возвращает список значений в порядке от наиболее к наименее востребованным."""
        return [node.value.value for node in self._list.iter_nodes()]

    def items(self) -> list[tuple[K, V]]:
        """Возвращает список пар (ключ, значение) в порядке от наиболее к наименее востребованным."""
        return [(node.value.key, node.value.value) for node in self._list.iter_nodes()]

    def to_dict(self) -> dict[K, V]:
        """Преобразует текущие элементы кэша в словарь (от MRU к LRU)."""
        return {node.value.key: node.value.value for node in self._list.iter_nodes()}

    def __getitem__(self, key: K) -> V:
        """Возвращает значение по ключу через синтаксис квадратных скобок.

        :param key: Искомый ключ.
        :return: Хранимое значение.
        :raises KeyError: Если ключ отсутствует в кэше.
        """
        if key not in self._lookup:
            self._misses += 1
            raise KeyError(f"Ключ {key!r} не найден в кэше")

        node: DoublyNode[_CacheEntry[K, V]] = self._lookup[key]
        self._list.move_to_front(node)
        self._hits += 1
        return node.value.value

    def __setitem__(self, key: K, value: V) -> None:
        """Сохраняет пару ключ-значение через синтаксис квадратных скобок."""
        self.put(key, value)

    def __delitem__(self, key: K) -> None:
        """Удаляет элемент по ключу через оператор del."""
        self.pop(key)

    def __contains__(self, key: object) -> bool:
        """Проверяет наличие ключа в кэше без изменения порядка обращения."""
        return key in self._lookup

    def __len__(self) -> int:
        """Возвращает текущее количество элементов в кэше."""
        return len(self._lookup)

    def __iter__(self) -> Iterator[K]:
        """Итерирует по ключам кэша в порядке от наиболее к наименее востребованным."""
        for node in self._list.iter_nodes():
            yield node.value.key

    def __repr__(self) -> str:
        """Возвращает строковое представление кэша."""
        return f"LRUCache(capacity={self._capacity}, size={len(self._lookup)})"

    def __eq__(self, other: object) -> bool:
        """Сравнивает два кэша на равенство по вместимости и содержимому с учетом порядка."""
        if not isinstance(other, LRUCache):
            return False
        if self._capacity != other._capacity:
            return False
        if len(self) != len(other):
            return False
        return self.items() == other.items()
