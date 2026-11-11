"""Модуль тестов для виртуального буфера в памяти (buffer)."""

import os

import pytest

from pocket_toolkit.system.buffer import (
    BufferOverflowError,
    MemoryFileBuffer,
)


def test_buffer_basic_write_read() -> None:
    """Проверка базовой записи и последовательного чтения из буфера."""
    buf = MemoryFileBuffer()
    assert len(buf) == 0

    written = buf.write("Hello, World!")
    assert written == 13
    assert len(buf) == 13
    assert buf.tell() == 13

    # Перемещаемся в начало и читаем
    buf.seek(0)
    assert buf.tell() == 0
    assert buf.read(5) == b"Hello"
    assert buf.tell() == 5
    assert buf.read_text() == ", World!"


def test_buffer_seeking_modes() -> None:
    """Проверка режимов перемещения курсора (SEEK_SET, SEEK_CUR, SEEK_END)."""
    buf = MemoryFileBuffer(b"0123456789")

    # SEEK_SET
    buf.seek(3, os.SEEK_SET)
    assert buf.read(2) == b"34"

    # SEEK_CUR
    buf.seek(2, os.SEEK_CUR)
    assert buf.read(1) == b"7"

    # SEEK_END
    buf.seek(-2, os.SEEK_END)
    assert buf.read(2) == b"89"


def test_buffer_overwrite() -> None:
    """Проверка перезаписи байтов при смещении курсора назад."""
    buf = MemoryFileBuffer(b"Hello Python")
    buf.seek(6)
    buf.write(b"World!")

    assert buf.getvalue() == b"Hello World!"


def test_buffer_truncate_and_clear() -> None:
    """Проверка усечения и полной очистки буфера."""
    buf = MemoryFileBuffer(b"1234567890")
    buf.truncate(5)
    assert buf.getvalue() == b"12345"

    buf.clear()
    assert buf.getvalue() == b""
    assert buf.tell() == 0


def test_buffer_max_size_overflow() -> None:
    """Проверка генерации исключения при превышении лимита размера буфера."""
    buf = MemoryFileBuffer(max_size=10)
    buf.write(b"12345")

    with pytest.raises(BufferOverflowError, match="Превышен максимальный размер"):
        buf.write(b"678901")  # 5 + 6 = 11 > 10


def test_buffer_close_lifecycle() -> None:
    """Проверка закрытия и использования буфера в контекстном менеджере."""
    with MemoryFileBuffer(b"active") as buf:
        assert not buf.is_closed
        assert buf.read() == b"active"

    assert buf.is_closed
    with pytest.raises(ValueError, match="Операция над закрытым буфером"):
        buf.read()
