"""Модульные тесты для кольцевого буфера RingBuffer."""

import pytest

from pocket_toolkit.structures.ring_buffer import RingBuffer


def test_ring_buffer_init_valid() -> None:
    """Проверка корректной инициализации буфера с положительной вместимостью."""
    buffer: RingBuffer[int] = RingBuffer(3)
    assert buffer.capacity == 3
    assert len(buffer) == 0
    assert buffer.is_empty() is True
    assert buffer.is_full() is False


def test_ring_buffer_init_invalid() -> None:
    """Проверка возбуждения ошибки при недопустимой вместимости."""
    with pytest.raises(ValueError, match="должна быть больше 0"):
        RingBuffer(0)

    with pytest.raises(ValueError, match="должна быть больше 0"):
        RingBuffer(-5)


def test_ring_buffer_append_and_peek() -> None:
    """Проверка добавления элементов без переполнения и метода peek."""
    buffer: RingBuffer[str] = RingBuffer(2)
    buffer.append("alpha")
    assert buffer.peek() == "alpha"
    assert len(buffer) == 1
    assert buffer.is_empty() is False

    buffer.append("beta")
    assert buffer.peek() == "alpha"
    assert len(buffer) == 2
    assert buffer.is_full() is True


def test_ring_buffer_overflow_overwrites_oldest() -> None:
    """Проверка перезаписи старых элементов при превышении лимита вместимости."""
    buffer: RingBuffer[int] = RingBuffer(3)
    buffer.append(10)
    buffer.append(20)
    buffer.append(30)
    assert buffer.to_list() == [10, 20, 30]

    # Переполнение: 10 перезаписывается на 40, голова сдвигается на 20
    buffer.append(40)
    assert len(buffer) == 3
    assert buffer.peek() == 20
    assert buffer.to_list() == [20, 30, 40]

    buffer.append(50)
    assert buffer.to_list() == [30, 40, 50]


def test_ring_buffer_popleft() -> None:
    """Проверка последовательного извлечения элементов из буфера."""
    buffer: RingBuffer[int] = RingBuffer(3)
    buffer.append(1)
    buffer.append(2)
    buffer.append(3)

    assert buffer.popleft() == 1
    assert len(buffer) == 2
    assert buffer.peek() == 2

    assert buffer.popleft() == 2
    assert buffer.popleft() == 3
    assert buffer.is_empty() is True

    with pytest.raises(IndexError, match="буфер пуст"):
        buffer.popleft()


def test_ring_buffer_peek_empty_raises() -> None:
    """Проверка возбуждения исключения при вызове peek у пустого буфера."""
    buffer: RingBuffer[str] = RingBuffer(5)
    with pytest.raises(IndexError, match="Буфер пуст"):
        buffer.peek()


def test_ring_buffer_getitem() -> None:
    """Проверка доступа по индексу и обработки некорректных индексов."""
    buffer: RingBuffer[int] = RingBuffer(3)
    buffer.append(100)
    buffer.append(200)

    assert buffer[0] == 100
    assert buffer[1] == 200

    with pytest.raises(IndexError):
        _ = buffer[2]

    with pytest.raises(IndexError):
        _ = buffer[-1]


def test_ring_buffer_iteration_and_clear() -> None:
    """Проверка итератора и метода полной очистки буфера."""
    buffer: RingBuffer[str] = RingBuffer(4)
    items: list[str] = ["a", "b", "c"]
    for item in items:
        buffer.append(item)

    assert list(buffer) == items
    buffer.clear()
    assert len(buffer) == 0
    assert buffer.is_empty() is True
    assert buffer.to_list() == []


def test_ring_buffer_repr() -> None:
    """Проверка строкового представления буфера."""
    buffer: RingBuffer[int] = RingBuffer(2)
    buffer.append(42)
    assert repr(buffer) == "RingBuffer(size=1, capacity=2, items=[42])"
