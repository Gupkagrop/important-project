"""Модуль виртуального потокового буфера данных в памяти (In-Memory File Buffer).

Предоставляет класс MemoryFileBuffer с поддержкой позиционирования курсора (seek/tell),
поблочной записи, чтения, усечения и ограничения максимального размера буфера.
"""

import io
import os
from collections.abc import Iterator
from typing import Self


class BufferOverflowError(Exception):
    """Исключение при превышении лимита размера буфера в памяти."""


class MemoryFileBuffer(io.RawIOBase):
    """Виртуальный файловый буфер в оперативной памяти."""

    def __init__(
        self,
        initial_data: bytes | str | None = None,
        max_size: int | None = None,
    ) -> None:
        """Инициализирует буфер в памяти."""
        super().__init__()
        self._max_size: int | None = max_size
        self._buffer: bytearray = bytearray()
        self._cursor: int = 0
        self._is_closed: bool = False

        if initial_data:
            data_bytes = initial_data.encode("utf-8") if isinstance(initial_data, str) else initial_data
            self.write(data_bytes)
            self._cursor = 0

    def _check_open(self) -> None:
        """Проверяет, открыт ли буфер."""
        if self._is_closed:
            raise ValueError("Операция над закрытым буфером")

    @property
    def is_closed(self) -> bool:
        """Возвращает True, если буфер закрыт."""
        return self._is_closed

    def write(self, data: bytes | bytearray | memoryview | str) -> int:  # type: ignore[override]
        """Записывает данные в текущую позицию курсора."""
        self._check_open()
        raw_bytes = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        length = len(raw_bytes)

        if length == 0:
            return 0

        target_size = max(len(self._buffer), self._cursor + length)
        if self._max_size is not None and target_size > self._max_size:
            raise BufferOverflowError(f"Превышен максимальный размер буфера: {self._max_size} байт")

        if self._cursor > len(self._buffer):
            # Заполняем пропуск нулями
            self._buffer.extend(b"\x00" * (self._cursor - len(self._buffer)))

        # Перезаписываем или дописываем
        overlap = min(length, len(self._buffer) - self._cursor)
        if overlap > 0:
            self._buffer[self._cursor : self._cursor + overlap] = raw_bytes[:overlap]

        if length > overlap:
            self._buffer.extend(raw_bytes[overlap:])

        self._cursor += length
        return length

    def read(self, size: int = -1) -> bytes:
        """Считывает до size байт из текущей позиции курсора."""
        self._check_open()
        if self._cursor >= len(self._buffer):
            return b""

        if size is None or size < 0:
            read_bytes = bytes(self._buffer[self._cursor :])
            self._cursor = len(self._buffer)
            return read_bytes

        end_pos = min(len(self._buffer), self._cursor + size)
        read_bytes = bytes(self._buffer[self._cursor : end_pos])
        self._cursor = end_pos
        return read_bytes

    def read_text(self, encoding: str = "utf-8") -> str:
        """Считывает оставшиеся данные и декодирует их в строку."""
        return self.read().decode(encoding)

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        """Перемещает позицию курсора чтения/записи."""
        self._check_open()
        if whence == os.SEEK_SET:
            new_pos = offset
        elif whence == os.SEEK_CUR:
            new_pos = self._cursor + offset
        elif whence == os.SEEK_END:
            new_pos = len(self._buffer) + offset
        else:
            raise ValueError(f"Недопустимое значение whence: {whence}")

        if new_pos < 0:
            raise ValueError(f"Отрицательная позиция курсора: {new_pos}")

        self._cursor = new_pos
        return self._cursor

    def tell(self) -> int:
        """Возвращает текущую позицию курсора."""
        self._check_open()
        return self._cursor

    def truncate(self, size: int | None = None) -> int:
        """Обрезает размер буфера до указанной величины."""
        self._check_open()
        target_size = self._cursor if size is None else size
        if target_size < 0:
            raise ValueError("Размер усечения не может быть отрицательным")

        if target_size < len(self._buffer):
            del self._buffer[target_size:]
        elif target_size > len(self._buffer):
            if self._max_size is not None and target_size > self._max_size:
                raise BufferOverflowError("Превышен максимальный лимит при расширении")
            self._buffer.extend(b"\x00" * (target_size - len(self._buffer)))

        return target_size

    def getvalue(self) -> bytes:
        """Возвращает все содержимое буфера в виде байтов."""
        self._check_open()
        return bytes(self._buffer)

    def clear(self) -> None:
        """Очищает содержимое и сбрасывает курсор."""
        self._check_open()
        self._buffer.clear()
        self._cursor = 0

    def close(self) -> None:
        """Закрывает буфер и освобождает память."""
        self._is_closed = True
        self._buffer.clear()

    def __enter__(self) -> Self:
        """Вход в контекстный менеджер."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Закрывает буфер при выходе из контекста."""
        self.close()

    def __len__(self) -> int:
        """Возвращает текущий размер содержимого буфера."""
        return len(self._buffer)

    def __iter__(self) -> Iterator[bytes]:
        """Построчный обход содержимого буфера."""
        while line := self.readline():
            yield line
