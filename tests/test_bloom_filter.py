"""Модульные тесты для вероятностного фильтра Блума BloomFilter."""

from dataclasses import dataclass

import pytest

from pocket_toolkit.structures.bloom_filter import BloomFilter


def test_bloom_filter_init_valid() -> None:
    """Проверка корректной инициализации фильтра по умолчанию."""
    bf: BloomFilter[str] = BloomFilter(capacity=1000, error_rate=0.01)
    assert bf.capacity == 1000
    assert bf.error_rate == 0.01
    assert bf.size > 0
    assert bf.num_hashes > 0
    assert len(bf) == 0
    assert bf.count == 0
    assert bf.num_bits_set == 0
    assert bf.fill_ratio == 0.0
    assert bf.estimated_elements == 0.0
    assert bf.current_error_rate == 0.0
    assert bf.is_empty() is True
    assert bool(bf) is False
    assert bf.byte_size() == (bf.size + 7) // 8


def test_bloom_filter_init_invalid() -> None:
    """Проверка возбуждения ошибок при некорректных аргументах инициализации."""
    with pytest.raises(ValueError, match="Вместимость фильтра Блума должна быть больше нуля"):
        BloomFilter(capacity=0)

    with pytest.raises(ValueError, match="Вместимость фильтра Блума должна быть больше нуля"):
        BloomFilter(capacity=-10)

    with pytest.raises(ValueError, match="Вероятность ложноположительного срабатывания"):
        BloomFilter(error_rate=0.0)

    with pytest.raises(ValueError, match="Вероятность ложноположительного срабатывания"):
        BloomFilter(error_rate=1.0)

    with pytest.raises(ValueError, match="Вероятность ложноположительного срабатывания"):
        BloomFilter(error_rate=-0.05)

    with pytest.raises(ValueError, match="Вероятность ложноположительного срабатывания"):
        BloomFilter(error_rate=1.5)

    with pytest.raises(ValueError, match="Размер битового массива должен быть больше нуля"):
        BloomFilter(size=0)

    with pytest.raises(ValueError, match="Размер битового массива должен быть больше нуля"):
        BloomFilter(size=-100)

    with pytest.raises(ValueError, match="Количество хеш-функций должно быть больше нуля"):
        BloomFilter(num_hashes=0)

    with pytest.raises(ValueError, match="Количество хеш-функций должно быть больше нуля"):
        BloomFilter(num_hashes=-3)


def test_bloom_filter_init_with_iterable() -> None:
    """Проверка инициализации фильтра начальной коллекцией элементов."""
    items: list[str] = ["яблоко", "банан", "груша"]
    bf: BloomFilter[str] = BloomFilter(capacity=100, iterable=items)
    assert len(bf) == 3
    assert bf.is_empty() is False
    assert bool(bf) is True
    for item in items:
        assert item in bf
    assert "апельсин" not in bf


def test_bloom_filter_custom_size_and_hashes() -> None:
    """Проверка создания фильтра с явно заданными размером и числом хешей."""
    bf: BloomFilter[int] = BloomFilter(capacity=50, size=256, num_hashes=4)
    assert bf.size == 256
    assert bf.num_hashes == 4
    assert bf.byte_size() == 32


def test_bloom_filter_add_and_membership() -> None:
    """Проверка добавления элементов и проверки их принадлежности."""
    bf: BloomFilter[str] = BloomFilter(capacity=500, error_rate=0.01)

    # Первое добавление должно вернуть False (установлены новые биты)
    was_already_set: bool = bf.add("первый")
    assert was_already_set is False
    assert "первый" in bf
    assert "второй" not in bf
    assert len(bf) == 1

    # Повторное добавление того же элемента должно вернуть True (все биты уже взведены)
    was_already_set_again: bool = bf.add("первый")
    assert was_already_set_again is True
    assert len(bf) == 2


def test_bloom_filter_different_data_types() -> None:
    """Проверка поддержки различных стандартных типов данных."""
    bf: BloomFilter[object] = BloomFilter(capacity=200, error_rate=0.01)

    bf.add(42)
    bf.add(3.1415)
    bf.add(b"binary_payload")
    bf.add(True)
    bf.add((1, "кортеж", 2))

    assert 42 in bf
    assert 3.1415 in bf
    assert b"binary_payload" in bf
    assert True in bf
    assert (1, "кортеж", 2) in bf

    assert 999 not in bf
    assert b"other_payload" not in bf


@dataclass(frozen=True)
class UserRecord:
    user_id: int
    username: str


def test_bloom_filter_custom_serializer() -> None:
    """Проверка использования пользовательской функции сериализации."""
    serializer_called: list[str] = []

    def custom_serializer(user: UserRecord) -> bytes:
        serializer_called.append(user.username)
        return f"{user.user_id}:{user.username}".encode()

    bf: BloomFilter[UserRecord] = BloomFilter(
        capacity=100,
        error_rate=0.01,
        serializer=custom_serializer,
    )

    u1: UserRecord = UserRecord(1, "alice")
    u2: UserRecord = UserRecord(2, "bob")
    u3: UserRecord = UserRecord(3, "charlie")

    bf.add(u1)
    bf.add(u2)

    assert u1 in bf
    assert u2 in bf
    assert u3 not in bf
    assert len(serializer_called) >= 3


def test_bloom_filter_extend() -> None:
    """Проверка пакетного добавления элементов через extend."""
    bf: BloomFilter[int] = BloomFilter(capacity=100)
    numbers: range = range(10, 20)
    bf.extend(numbers)

    assert len(bf) == 10
    for num in numbers:
        assert num in bf
    assert 5 not in bf
    assert 25 not in bf


def test_bloom_filter_clear() -> None:
    """Проверка очистки всех установленных бит и сброса счетчиков."""
    bf: BloomFilter[str] = BloomFilter(capacity=100, iterable=["один", "два", "три"])
    assert bf.is_empty() is False
    assert len(bf) == 3

    bf.clear()
    assert bf.is_empty() is True
    assert len(bf) == 0
    assert bf.num_bits_set == 0
    assert bf.fill_ratio == 0.0
    assert bf.estimated_elements == 0.0
    assert "один" not in bf


def test_bloom_filter_copy() -> None:
    """Проверка создания независимой копии фильтра."""
    bf: BloomFilter[str] = BloomFilter(capacity=100, iterable=["alpha", "beta"])
    copied: BloomFilter[str] = bf.copy()

    assert copied == bf
    assert "alpha" in copied
    assert "beta" in copied

    # Модификация копии не влияет на оригинал
    copied.add("gamma")
    assert "gamma" in copied
    assert "gamma" not in bf
    assert len(copied) == 3
    assert len(bf) == 2


def test_bloom_filter_to_and_from_bytes() -> None:
    """Проверка экспорта и восстановления фильтра из сырых байтов."""
    bf: BloomFilter[str] = BloomFilter(capacity=200, error_rate=0.02)
    bf.extend(["тест1", "тест2", "тест3"])

    raw_bytes: bytes = bf.to_bytes()
    assert isinstance(raw_bytes, bytes)
    assert len(raw_bytes) == bf.byte_size()

    restored: BloomFilter[str] = BloomFilter.from_bytes(
        data=raw_bytes,
        capacity=bf.capacity,
        error_rate=bf.error_rate,
        size=bf.size,
        num_hashes=bf.num_hashes,
        count=bf.count,
    )

    assert restored == bf
    assert restored.count == bf.count
    assert "тест1" in restored
    assert "тест2" in restored
    assert "тест3" in restored
    assert "не_существует" not in restored


def test_bloom_filter_from_bytes_invalid_length() -> None:
    """Проверка ошибки при передаче байтов неверного размера."""
    with pytest.raises(ValueError, match="Некорректный размер данных"):
        BloomFilter.from_bytes(
            data=b"too_short",
            capacity=1000,
            error_rate=0.01,
        )


def test_bloom_filter_union_and_or_operators() -> None:
    """Проверка операции объединения фильтров Блума (| и union)."""
    bf1: BloomFilter[str] = BloomFilter(capacity=100, size=500, num_hashes=4)
    bf2: BloomFilter[str] = BloomFilter(capacity=100, size=500, num_hashes=4)

    bf1.extend(["яблоко", "груша"])
    bf2.extend(["вишня", "персик"])

    union_bf: BloomFilter[str] = bf1.union(bf2)
    assert "яблоко" in union_bf
    assert "груша" in union_bf
    assert "вишня" in union_bf
    assert "персик" in union_bf
    assert "ананас" not in union_bf

    # Проверка оператора |
    or_bf: BloomFilter[str] = bf1 | bf2
    assert or_bf == union_bf

    # Проверка оператора |= (in-place)
    bf1 |= bf2
    assert bf1 == union_bf
    assert "вишня" in bf1


def test_bloom_filter_intersection_and_and_operators() -> None:
    """Проверка операции пересечения фильтров Блума (& и intersection)."""
    bf1: BloomFilter[str] = BloomFilter(capacity=100, size=500, num_hashes=4)
    bf2: BloomFilter[str] = BloomFilter(capacity=100, size=500, num_hashes=4)

    bf1.extend(["общий1", "общий2", "уникальный1"])
    bf2.extend(["общий1", "общий2", "уникальный2"])

    intersected: BloomFilter[str] = bf1.intersection(bf2)
    assert "общий1" in intersected
    assert "общий2" in intersected
    assert "уникальный1" not in intersected
    assert "уникальный2" not in intersected

    # Проверка оператора &
    and_bf: BloomFilter[str] = bf1 & bf2
    assert and_bf == intersected

    # Проверка оператора &= (in-place)
    bf1 &= bf2
    assert bf1 == intersected


def test_bloom_filter_incompatible_operations() -> None:
    """Проверка возбуждения ошибок при попытке слияния несовместимых фильтров."""
    bf1: BloomFilter[str] = BloomFilter(capacity=100, size=500, num_hashes=4)
    bf_diff_size: BloomFilter[str] = BloomFilter(capacity=100, size=600, num_hashes=4)
    bf_diff_hashes: BloomFilter[str] = BloomFilter(capacity=100, size=500, num_hashes=5)

    with pytest.raises(ValueError, match="Несовпадающие размеры битовых массивов"):
        _ = bf1.union(bf_diff_size)

    with pytest.raises(ValueError, match="Несовпадающее число хеш-функций"):
        _ = bf1.intersection(bf_diff_hashes)

    with pytest.raises(TypeError, match="Ожидался BloomFilter"):
        _ = bf1.union("не_фильтр")  # type: ignore[arg-type]


def test_bloom_filter_statistics_and_estimation() -> None:
    """Проверка расчета статистических метрик заполненности и оценки мощности."""
    bf: BloomFilter[int] = BloomFilter(capacity=100, error_rate=0.01)
    assert bf.estimated_elements == 0.0

    items_to_add: list[int] = list(range(50))
    bf.extend(items_to_add)

    assert bf.num_bits_set > 0
    assert 0.0 < bf.fill_ratio < 1.0
    assert 0.0 < bf.current_error_rate < 1.0

    # Оценка мощности должна быть близка к реальному числу элементов (50)
    estimated: float = bf.estimated_elements
    assert 30 <= estimated <= 70


def test_bloom_filter_saturated_estimation() -> None:
    """Проверка граничного случая оценки мощности при 100% заполнении."""
    bf: BloomFilter[int] = BloomFilter(capacity=10, size=16, num_hashes=2)
    # Насильно заполняем все биты единицами
    for i in range(len(bf._bit_array)):
        bf._bit_array[i] = 0xFF

    assert bf.fill_ratio == 1.0
    assert bf.estimated_elements == float(bf.size)
    assert bf.current_error_rate == 1.0


def test_bloom_filter_equality_and_repr() -> None:
    """Проверка сравнения фильтров и строкового представления."""
    bf1: BloomFilter[str] = BloomFilter(capacity=50, size=200, num_hashes=3, iterable=["a", "b"])
    bf2: BloomFilter[str] = BloomFilter(capacity=50, size=200, num_hashes=3, iterable=["a", "b"])
    bf3: BloomFilter[str] = BloomFilter(capacity=50, size=200, num_hashes=3, iterable=["a", "c"])

    assert bf1 == bf2
    assert bf1 != bf3
    assert bf1 != "не_фильтр"

    representation: str = repr(bf1)
    assert "BloomFilter(" in representation
    assert "capacity=50" in representation
    assert "size=200" in representation
    assert "hashes=3" in representation


def test_bloom_filter_false_positive_rate() -> None:
    """Проверка того, что процент ложноположительных срабатываний находится в ожидаемых границах."""
    capacity: int = 1000
    target_error_rate: float = 0.05
    bf: BloomFilter[str] = BloomFilter(capacity=capacity, error_rate=target_error_rate)

    # Добавляем capacity элементов
    for i in range(capacity):
        bf.add(f"item_in_filter_{i}")

    # Проверяем отсутствие ложноотрицательных срабатываний (все добавленные элементы должны найтись)
    for i in range(capacity):
        assert f"item_in_filter_{i}" in bf

    # Проверяем процент ложноположительных срабатываний на 1000 других элементах
    false_positives: int = 0
    test_count: int = 1000
    for i in range(test_count):
        if f"absent_item_{i}" in bf:
            false_positives += 1

    observed_error_rate: float = false_positives / test_count
    # Допускаем статистическое отклонение: наблюдаемый процент должен быть в пределах разумного (< 10%)
    assert observed_error_rate < 0.10
