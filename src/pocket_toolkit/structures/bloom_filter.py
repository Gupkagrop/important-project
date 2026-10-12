"""Реализация вероятностного фильтра Блума (Bloom Filter).

Компактная структура данных для быстрой вероятностной проверки принадлежности
элемента множеству с настраиваемой вероятностью ложноположительного срабатывания
и использованием двойного хеширования Кирша-Митценмахера.
"""

import hashlib
import math
from collections.abc import Callable, Iterable


class BloomFilter[T]:
    """Вероятностный фильтр Блума с независимыми хеш-функциями.

    Обеспечивает константное время O(k) добавления и проверки элементов,
    где k — количество хеш-функций. Гарантирует отсутствие ложноотрицательных
    срабатываний (если элемент в фильтре — он гарантированно не будет пропущен),
    допуская контролируемый процент ложноположительных срабатываний.
    """

    def __init__(
        self,
        capacity: int = 1000,
        error_rate: float = 0.01,
        iterable: Iterable[T] | None = None,
        *,
        size: int | None = None,
        num_hashes: int | None = None,
        serializer: Callable[[T], bytes] | None = None,
    ) -> None:
        """Инициализирует фильтр Блума с заданными параметрами.

        :param capacity: Ожидаемое количество элементов (вместимость > 0).
        :param error_rate: Допустимая вероятность ложноположительного срабатывания (0 < p < 1).
        :param iterable: Начальная последовательность элементов для добавления.
        :param size: Явный размер битового массива в битах (если не задан, рассчитывается оптимальный).
        :param num_hashes: Явное количество хеш-функций (если не задано, рассчитывается оптимальное).
        :param serializer: Пользовательская функция преобразования элементов в байты.
        :raises ValueError: При некорректных параметрах вместимости, вероятности ошибки или размера.
        """
        if capacity <= 0:
            raise ValueError("Вместимость фильтра Блума должна быть больше нуля")
        if not (0.0 < error_rate < 1.0):
            raise ValueError("Вероятность ложноположительного срабатывания должна быть в диапазоне (0, 1)")
        if size is not None and size <= 0:
            raise ValueError("Размер битового массива должен быть больше нуля")
        if num_hashes is not None and num_hashes <= 0:
            raise ValueError("Количество хеш-функций должно быть больше нуля")

        self._capacity: int = capacity
        self._error_rate: float = error_rate
        self._serializer: Callable[[T], bytes] | None = serializer
        self._count: int = 0

        optimal_size: int = self._calculate_optimal_size(capacity, error_rate) if size is None else size
        self._size: int = optimal_size

        optimal_hashes: int = (
            self._calculate_optimal_hashes(self._size, capacity) if num_hashes is None else num_hashes
        )
        self._num_hashes: int = optimal_hashes

        num_bytes: int = (self._size + 7) // 8
        self._bit_array: bytearray = bytearray(num_bytes)

        if iterable is not None:
            self.extend(iterable)

    @staticmethod
    def _calculate_optimal_size(capacity: int, error_rate: float) -> int:
        """Вычисляет оптимальный размер битового массива m по формуле Блума.

        :param capacity: Ожидаемое количество элементов n.
        :param error_rate: Допустимая вероятность ошибки p.
        :return: Минимальное количество бит m.
        """
        numerator: float = -capacity * math.log(error_rate)
        denominator: float = math.log(2.0) ** 2
        calculated: int = math.ceil(numerator / denominator)
        return max(8, calculated)

    @staticmethod
    def _calculate_optimal_hashes(size: int, capacity: int) -> int:
        """Вычисляет оптимальное число хеш-функций k.

        :param size: Размер битового массива m.
        :param capacity: Ожидаемое количество элементов n.
        :return: Оптимальное количество хеш-функций k.
        """
        calculated: int = round((size / capacity) * math.log(2.0))
        return max(1, calculated)

    @property
    def capacity(self) -> int:
        """Возвращает проектную вместимость фильтра."""
        return self._capacity

    @property
    def error_rate(self) -> float:
        """Возвращает целевую вероятность ложноположительного срабатывания."""
        return self._error_rate

    @property
    def size(self) -> int:
        """Возвращает общий размер битового массива в битах."""
        return self._size

    @property
    def num_hashes(self) -> int:
        """Возвращает количество используемых хеш-функций."""
        return self._num_hashes

    @property
    def count(self) -> int:
        """Возвращает количество выполненных операций добавления."""
        return self._count

    @property
    def num_bits_set(self) -> int:
        """Возвращает количество установленных в единицу бит."""
        return sum(byte_val.bit_count() for byte_val in self._bit_array)

    @property
    def fill_ratio(self) -> float:
        """Возвращает долю установленных бит в диапазоне от 0.0 до 1.0."""
        if self._size == 0:
            return 0.0
        return self.num_bits_set / self._size

    @property
    def estimated_elements(self) -> float:
        """Оценивает число уникальных элементов в фильтре по доле заполненных бит.

        Использует формулу оценки мощности:
        n* = - (m / k) * ln(1 - X / m), где X — число установленных бит.
        """
        bits_set: int = self.num_bits_set
        if bits_set == 0:
            return 0.0
        if bits_set >= self._size:
            return float(self._size)

        fraction_zero: float = 1.0 - (bits_set / self._size)
        if fraction_zero <= 0.0:
            return float(self._size)

        estimated: float = -(self._size / self._num_hashes) * math.log(fraction_zero)
        return max(0.0, estimated)

    @property
    def current_error_rate(self) -> float:
        """Вычисляет текущую теоретическую вероятность ложноположительного ответа."""
        ratio: float = self.fill_ratio
        if ratio <= 0.0:
            return 0.0
        return ratio**self._num_hashes

    def is_empty(self) -> bool:
        """Проверяет, пуст ли фильтр (отсутствуют ли установленные биты)."""
        return self.num_bits_set == 0

    def byte_size(self) -> int:
        """Возвращает объем памяти битового массива в байтах."""
        return len(self._bit_array)

    def add(self, item: T) -> bool:
        """Добавляет элемент в фильтр Блума.

        :param item: Добавляемый элемент.
        :return: True, если все биты уже были установлены; False, если хотя бы один бит был новым.
        """
        indices: list[int] = self._get_hash_indices(item)
        all_bits_were_set: bool = True
        for bit_index in indices:
            is_new_bit: bool = self._set_bit(bit_index)
            if is_new_bit:
                all_bits_were_set = False

        self._count += 1
        return all_bits_were_set

    def extend(self, items: Iterable[T]) -> None:
        """Добавляет последовательность элементов в фильтр Блума.

        :param items: Итерируемая коллекция элементов.
        """
        for item in items:
            self.add(item)

    def clear(self) -> None:
        """Сбрасывает все биты фильтра в ноль и обнуляет счетчик элементов."""
        for byte_idx in range(len(self._bit_array)):
            self._bit_array[byte_idx] = 0
        self._count = 0

    def copy(self) -> "BloomFilter[T]":
        """Создает независимую копию текущего фильтра Блума.

        :return: Новый экземпляр BloomFilter с идентичным состоянием.
        """
        clone: BloomFilter[T] = BloomFilter(
            capacity=self._capacity,
            error_rate=self._error_rate,
            size=self._size,
            num_hashes=self._num_hashes,
            serializer=self._serializer,
        )
        clone._bit_array = bytearray(self._bit_array)
        clone._count = self._count
        return clone

    def to_bytes(self) -> bytes:
        """Экспортирует сырой битовый массив фильтра в неизменяемую байтовую строку.

        :return: Байтовая строка с текущим состоянием битов.
        """
        return bytes(self._bit_array)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        capacity: int = 1000,
        error_rate: float = 0.01,
        *,
        size: int | None = None,
        num_hashes: int | None = None,
        count: int = 0,
        serializer: Callable[[T], bytes] | None = None,
    ) -> "BloomFilter[T]":
        """Восстанавливает фильтр Блума из экспортированных байтов.

        :param data: Сырые байты битового массива.
        :param capacity: Ожидаемая вместимость.
        :param error_rate: Допустимая вероятность ошибки.
        :param size: Размер битового массива в битах.
        :param num_hashes: Число хеш-функций.
        :param count: Число ранее добавленных элементов.
        :param serializer: Пользовательский сериализатор.
        :return: Восстановленный фильтр Блума.
        :raises ValueError: При несоответствии длины байтов расчетному размеру.
        """
        instance: BloomFilter[T] = cls(
            capacity=capacity,
            error_rate=error_rate,
            size=size,
            num_hashes=num_hashes,
            serializer=serializer,
        )
        expected_byte_count: int = (instance.size + 7) // 8
        if len(data) != expected_byte_count:
            raise ValueError(
                f"Некорректный размер данных: ожидалось {expected_byte_count} байт, получено {len(data)}"
            )

        instance._bit_array = bytearray(data)
        instance._count = max(0, count)
        return instance

    def union(self, other: "BloomFilter[T]") -> "BloomFilter[T]":
        """Возвращает объединение двух совместимых фильтров Блума (логическое ИЛИ).

        :param other: Другой совместимый фильтр.
        :return: Новый объединенный фильтр Блума.
        """
        self._validate_compatible(other)
        merged: BloomFilter[T] = self.copy()
        for idx in range(len(merged._bit_array)):
            merged._bit_array[idx] |= other._bit_array[idx]
        merged._count = max(self._count, other._count)
        return merged

    def intersection(self, other: "BloomFilter[T]") -> "BloomFilter[T]":
        """Возвращает пересечение двух совместимых фильтров Блума (логическое И).

        :param other: Другой совместимый фильтр.
        :return: Новый фильтр с пересечением битов.
        """
        self._validate_compatible(other)
        intersected: BloomFilter[T] = self.copy()
        for idx in range(len(intersected._bit_array)):
            intersected._bit_array[idx] &= other._bit_array[idx]
        intersected._count = min(self._count, other._count)
        return intersected

    def _validate_compatible(self, other: "BloomFilter[T]") -> None:
        """Проверяет идентичность параметров конфигурации двух фильтров.

        :param other: Сравниваемый фильтр.
        :raises TypeError: Если передан объект другого типа.
        :raises ValueError: Если размеры или число хеш-функций не совпадают.
        """
        if not isinstance(other, BloomFilter):
            raise TypeError(f"Ожидался BloomFilter, получен {type(other).__name__}")
        if self._size != other._size:
            raise ValueError(f"Несовпадающие размеры битовых массивов: {self._size} != {other._size}")
        if self._num_hashes != other._num_hashes:
            raise ValueError(f"Несовпадающее число хеш-функций: {self._num_hashes} != {other._num_hashes}")

    def _set_bit(self, index: int) -> bool:
        """Устанавливает бит в 1 и сообщает, был ли он новым.

        :param index: Номер бита в диапазоне [0, size - 1].
        :return: True, если бит был установлен впервые; False, если уже был 1.
        """
        byte_index: int = index // 8
        bit_offset: int = index % 8
        bit_mask: int = 1 << bit_offset
        already_set: bool = (self._bit_array[byte_index] & bit_mask) != 0
        if not already_set:
            self._bit_array[byte_index] |= bit_mask
            return True
        return False

    def _check_bit(self, index: int) -> bool:
        """Проверяет значение конкретного бита.

        :param index: Номер бита в диапазоне [0, size - 1].
        :return: True, если бит установлен в 1; False, если 0.
        """
        byte_index: int = index // 8
        bit_offset: int = index % 8
        bit_mask: int = 1 << bit_offset
        return (self._bit_array[byte_index] & bit_mask) != 0

    def _get_hash_indices(self, item: object) -> list[int]:
        """Генерирует k индексов бит с помощью двойного хеширования Кирша-Митценмахера.

        Формула: g_i(x) = (h1 + i * h2 + i^2) % m.

        :param item: Объект для хеширования.
        :return: Список индексов бит.
        """
        raw_bytes: bytes = self._serialize_item(item)
        digest: bytes = hashlib.sha256(raw_bytes).digest()
        h1: int = int.from_bytes(digest[0:8], byteorder="big")
        h2: int = int.from_bytes(digest[8:16], byteorder="big")
        if h2 == 0:
            h2 = 1

        indices: list[int] = []
        for step in range(self._num_hashes):
            bit_idx: int = (h1 + step * h2 + step * step) % self._size
            indices.append(bit_idx)
        return indices

    def _serialize_item(self, item: object) -> bytes:
        """Преобразует произвольный объект в байтовую строку.

        :param item: Входной объект.
        :return: Байтовое представление.
        """
        if self._serializer is not None:
            try:
                return self._serializer(item)  # type: ignore[arg-type]
            except (TypeError, ValueError, AttributeError):
                return self._default_serialize(item)
        return self._default_serialize(item)

    @staticmethod
    def _default_serialize(item: object) -> bytes:
        """Сериализует базовые типы данных в байты."""
        if isinstance(item, (bytes, bytearray, memoryview)):
            return bytes(item)
        if isinstance(item, str):
            return item.encode("utf-8")
        if isinstance(item, (int, float, bool)):
            return str(item).encode("utf-8")
        return repr(item).encode("utf-8")

    def __contains__(self, item: object) -> bool:
        """Проверяет вероятностное наличие элемента в фильтре Блума.

        :param item: Проверяемый объект.
        :return: False, если элемента гарантированно нет; True, если вероятно присутствует.
        """
        indices: list[int] = self._get_hash_indices(item)
        for bit_index in indices:
            if not self._check_bit(bit_index):
                return False
        return True

    def __or__(self, other: "BloomFilter[T]") -> "BloomFilter[T]":
        """Побитовое объединение фильтров (|)."""
        return self.union(other)

    def __ior__(self, other: "BloomFilter[T]") -> "BloomFilter[T]":
        """Побитовое объединение фильтров на месте (|=)."""
        self._validate_compatible(other)
        for idx in range(len(self._bit_array)):
            self._bit_array[idx] |= other._bit_array[idx]
        self._count = max(self._count, other._count)
        return self

    def __and__(self, other: "BloomFilter[T]") -> "BloomFilter[T]":
        """Побитовое пересечение фильтров (&)."""
        return self.intersection(other)

    def __iand__(self, other: "BloomFilter[T]") -> "BloomFilter[T]":
        """Побитовое пересечение фильтров на месте (&=)."""
        self._validate_compatible(other)
        for idx in range(len(self._bit_array)):
            self._bit_array[idx] &= other._bit_array[idx]
        self._count = min(self._count, other._count)
        return self

    def __len__(self) -> int:
        """Возвращает число добавлений в фильтр."""
        return self._count

    def __bool__(self) -> bool:
        """Возвращает True, если в фильтре установлен хотя бы один бит."""
        return not self.is_empty()

    def __eq__(self, other: object) -> bool:
        """Проверяет равенство конфигурации и битового содержимого двух фильтров."""
        if not isinstance(other, BloomFilter):
            return False
        if self._size != other._size:
            return False
        if self._num_hashes != other._num_hashes:
            return False
        return self._bit_array == other._bit_array

    def __repr__(self) -> str:
        """Строковое представление характеристик фильтра Блума."""
        return (
            f"BloomFilter(capacity={self._capacity}, "
            f"error_rate={self._error_rate:.4f}, "
            f"size={self._size}, "
            f"hashes={self._num_hashes}, "
            f"count={self._count}, "
            f"fill_ratio={self.fill_ratio:.2%})"
        )
