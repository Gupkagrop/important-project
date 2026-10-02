"""Реализация кэша вытеснения по частоте использования (LFU Cache) с временем доступа O(1)."""

from collections.abc import Iterable, Iterator

from pocket_toolkit.structures.doubly_linked_list import DoublyLinkedList, DoublyNode


class _LFUEntry[K, V]:
    """Внутренний контейнер для хранения ключа, значения и частоты обращения."""

    __slots__ = ("freq", "key", "value")

    def __init__(self, key: K, value: V, freq: int = 1) -> None:
        """Инициализирует запись кэша LFU.

        :param key: Ключ элемента.
        :param value: Значение элемента.
        :param freq: Начальная частота обращения.
        """
        self.key: K = key
        self.value: V = value
        self.freq: int = freq

    def __repr__(self) -> str:
        """Строковое представление записи LFU."""
        return f"_LFUEntry(key={self.key!r}, value={self.value!r}, freq={self.freq})"


class LFUCache[K, V]:
    """Кэш вытеснения по частоте использования (Least Frequently Used Cache).

    Обеспечивает алгоритмическую сложность основных операций O(1) за счет
    комбинации хэш-таблицы (словаря) ключей и словаря двусвязных списков,
    группирующих элементы по частоте их вызова. При равенстве частот
    вытесняется наименее недавно использованный элемент (LRU).
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
        self._lookup: dict[K, DoublyNode[_LFUEntry[K, V]]] = {}
        self._freq_map: dict[int, DoublyLinkedList[_LFUEntry[K, V]]] = {}
        self._min_freq: int = 0
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

    @property
    def min_freq(self) -> int:
        """Возвращает текущую минимальную частоту элементов в кэше."""
        return self._min_freq

    def is_empty(self) -> bool:
        """Проверяет, пуст ли кэш."""
        return len(self._lookup) == 0

    def is_full(self) -> bool:
        """Проверяет, заполнен ли кэш до предельной вместимости."""
        return len(self._lookup) >= self._capacity

    def _increment_freq(self, node: DoublyNode[_LFUEntry[K, V]]) -> None:
        """Вспомогательный метод увеличения частоты обращения к узлу за O(1)."""
        entry: _LFUEntry[K, V] = node.value
        old_freq: int = entry.freq
        freq_list: DoublyLinkedList[_LFUEntry[K, V]] = self._freq_map[old_freq]
        freq_list.unlink(node)

        if freq_list.is_empty():
            del self._freq_map[old_freq]
            if self._min_freq == old_freq:
                self._min_freq += 1

        entry.freq += 1
        new_freq: int = entry.freq
        if new_freq not in self._freq_map:
            self._freq_map[new_freq] = DoublyLinkedList()

        self._freq_map[new_freq].prepend_node(node)

    def _evict_lfu(self) -> _LFUEntry[K, V]:
        """Вспомогательный метод вытеснения наименее часто используемого элемента."""
        freq_list: DoublyLinkedList[_LFUEntry[K, V]] = self._freq_map[self._min_freq]
        evicted_entry: _LFUEntry[K, V] = freq_list.pop()
        del self._lookup[evicted_entry.key]

        if freq_list.is_empty():
            del self._freq_map[self._min_freq]

        return evicted_entry

    def put(self, key: K, value: V) -> None:
        """Помещает пару ключ-значение в кэш.

        Если ключ существует, обновляет значение и увеличивает его частоту.
        Если кэш заполнен, вытесняет элемент с наименьшей частотой (LFU/LRU).

        :param key: Ключ элемента.
        :param value: Значение элемента.
        """
        if key in self._lookup:
            node: DoublyNode[_LFUEntry[K, V]] = self._lookup[key]
            node.value.value = value
            self._increment_freq(node)
            return

        if self.is_full():
            self._evict_lfu()

        entry: _LFUEntry[K, V] = _LFUEntry(key, value, freq=1)
        if 1 not in self._freq_map:
            self._freq_map[1] = DoublyLinkedList()

        new_node: DoublyNode[_LFUEntry[K, V]] = self._freq_map[1].prepend(entry)
        self._lookup[key] = new_node
        self._min_freq = 1

    def get(self, key: K, default: V | None = None) -> V | None:
        """Возвращает значение по ключу, увеличивая счетчик его частоты обращения.

        :param key: Искомый ключ.
        :param default: Значение по умолчанию, если ключ отсутствует.
        :return: Значение элемента или default.
        """
        if key not in self._lookup:
            self._misses += 1
            return default

        node: DoublyNode[_LFUEntry[K, V]] = self._lookup[key]
        self._increment_freq(node)
        self._hits += 1
        return node.value.value

    def get_frequency(self, key: K) -> int | None:
        """Возвращает текущую частоту обращения к ключу.

        :param key: Искомый ключ.
        :return: Частота обращения к ключу или None, если ключ отсутствует.
        """
        if key not in self._lookup:
            return None
        return self._lookup[key].value.freq

    def peek(self, key: K, default: V | None = None) -> V | None:
        """Возвращает значение по ключу без изменения частоты и статистики.

        :param key: Искомый ключ.
        :param default: Значение по умолчанию, если ключ отсутствует.
        :return: Значение элемента или default.
        """
        if key not in self._lookup:
            return default
        return self._lookup[key].value.value

    def peek_lfu(self) -> tuple[K, V] | None:
        """Возвращает парный кандидат на вытеснение (ключ, значение) без его удаления.

        :return: Кортеж (ключ, значение) или None, если кэш пуст.
        """
        if self.is_empty():
            return None
        freq_list: DoublyLinkedList[_LFUEntry[K, V]] = self._freq_map[self._min_freq]
        tail_node: DoublyNode[_LFUEntry[K, V]] | None = freq_list.tail_node
        if tail_node is None:
            return None
        return tail_node.value.key, tail_node.value.value

    def pop(self, key: K) -> V:
        """Извлекает и удаляет элемент по ключу из кэша.

        :param key: Ключ удаляемого элемента.
        :return: Значение удаленного элемента.
        :raises KeyError: Если ключ не найден в кэше.
        """
        if key not in self._lookup:
            raise KeyError(f"Ключ {key!r} не найден в кэше")

        node: DoublyNode[_LFUEntry[K, V]] = self._lookup.pop(key)
        entry: _LFUEntry[K, V] = node.value
        freq_list: DoublyLinkedList[_LFUEntry[K, V]] = self._freq_map[entry.freq]
        freq_list.unlink(node)

        if freq_list.is_empty():
            del self._freq_map[entry.freq]
            if self._min_freq == entry.freq:
                if self._freq_map:
                    self._min_freq = min(self._freq_map.keys())
                else:
                    self._min_freq = 0

        return entry.value

    def pop_lfu(self) -> tuple[K, V]:
        """Удаляет и возвращает наименее часто и наименее недавно использованный элемент.

        :return: Кортеж (ключ, значение) вытесненного элемента.
        :raises KeyError: Если кэш пуст.
        """
        if self.is_empty():
            raise KeyError("Невозможно извлечь элемент: кэш пуст")

        evicted: _LFUEntry[K, V] = self._evict_lfu()
        return evicted.key, evicted.value

    def delete(self, key: K) -> bool:
        """Безопасно удаляет элемент по ключу.

        :param key: Удаляемый ключ.
        :return: True, если элемент присутствовал и был удален; False в противном случае.
        """
        if key not in self._lookup:
            return False
        self.pop(key)
        return True

    def resize(self, new_capacity: int) -> int:
        """Изменяет максимальную вместимость кэша.

        Если новая вместимость меньше текущего размера, вытесняет элементы LFU.

        :param new_capacity: Новая вместимость кэша (строго > 0).
        :return: Количество вытесненных элементов.
        :raises ValueError: Если new_capacity <= 0.
        """
        if new_capacity <= 0:
            raise ValueError("Новая вместимость кэша должна быть больше 0")

        evicted_count: int = 0
        while len(self._lookup) > new_capacity:
            self._evict_lfu()
            evicted_count += 1

        self._capacity = new_capacity
        return evicted_count

    def clear(self, reset_stats: bool = False) -> None:
        """Очищает кэш от всех элементов.

        :param reset_stats: Сбрасывать ли счетчики попаданий и промахов.
        """
        self._lookup.clear()
        self._freq_map.clear()
        self._min_freq = 0
        if reset_stats:
            self.reset_stats()

    def reset_stats(self) -> None:
        """Сбрасывает счетчики попаданий и промахов к нулю."""
        self._hits = 0
        self._misses = 0

    def items(self) -> list[tuple[K, V]]:
        """Возвращает список пар (ключ, значение) по убыванию частоты обращения."""
        result: list[tuple[K, V]] = []
        for freq in sorted(self._freq_map.keys(), reverse=True):
            freq_list: DoublyLinkedList[_LFUEntry[K, V]] = self._freq_map[freq]
            for node in freq_list.iter_nodes():
                result.append((node.value.key, node.value.value))
        return result

    def keys(self) -> list[K]:
        """Возвращает список ключей по убыванию частоты обращения."""
        return [key for key, _ in self.items()]

    def values(self) -> list[V]:
        """Возвращает список значений по убыванию частоты обращения."""
        return [val for _, val in self.items()]

    def to_dict(self) -> dict[K, V]:
        """Преобразует элементы кэша в словарь по убыванию частоты."""
        return dict(self.items())

    def __getitem__(self, key: K) -> V:
        """Возвращает значение по ключу с увеличением частоты через []."""
        if key not in self._lookup:
            self._misses += 1
            raise KeyError(f"Ключ {key!r} не найден в кэше")

        node: DoublyNode[_LFUEntry[K, V]] = self._lookup[key]
        self._increment_freq(node)
        self._hits += 1
        return node.value.value

    def __setitem__(self, key: K, value: V) -> None:
        """Сохраняет пару ключ-значение через []."""
        self.put(key, value)

    def __delitem__(self, key: K) -> None:
        """Удаляет элемент по ключу через del."""
        self.pop(key)

    def __contains__(self, key: object) -> bool:
        """Проверяет наличие ключа в кэше без изменения частоты."""
        return key in self._lookup

    def __len__(self) -> int:
        """Возвращает текущее количество элементов в кэше."""
        return len(self._lookup)

    def __iter__(self) -> Iterator[K]:
        """Итерирует по ключам кэша по убыванию частоты обращения."""
        for key in self.keys():
            yield key

    def __repr__(self) -> str:
        """Возвращает строковое представление кэша."""
        return f"LFUCache(capacity={self._capacity}, size={len(self._lookup)})"

    def __eq__(self, other: object) -> bool:
        """Сравнивает два кэша на равенство по вместимости и элементному составу."""
        if not isinstance(other, LFUCache):
            return False
        if self._capacity != other._capacity:
            return False
        if len(self) != len(other):
            return False
        return self.items() == other.items()
