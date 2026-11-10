"""Модуль некриптографического хеширования и контрольных сумм (Hashing).

Предоставляет реализацию алгоритма CRC-32 (IEEE 802.3) с предварительно вычисленной
таблицей замен, а также 32-битный и 64-битный варианты алгоритма хеширования Fowler–Noll–Vo (FNV-1a)
с поддержкой потокового инкрементального расчета.
"""

from collections.abc import Iterable


def _build_crc32_table() -> tuple[int, ...]:
    """Генерирует статическую 256-элементную таблицу для полинома IEEE 802.3 (0xEDB88320)."""
    table: list[int] = []
    polynomial: int = 0xEDB88320
    for byte in range(256):
        crc = byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ polynomial
            else:
                crc >>= 1
        table.append(crc & 0xFFFFFFFF)
    return tuple(table)


_CRC32_TABLE: tuple[int, ...] = _build_crc32_table()

# Константы для FNV-1a
_FNV_32_PRIME: int = 0x01000193
_FNV_32_OFFSET_BASIS: int = 0x811C9DC5
_FNV_32_MASK: int = 0xFFFFFFFF

_FNV_64_PRIME: int = 0x100000001B3
_FNV_64_OFFSET_BASIS: int = 0xCBF29CE484222325
_FNV_64_MASK: int = 0xFFFFFFFFFFFFFFFF


def _to_bytes(data: bytes | bytearray | str) -> bytes:
    """Приводит входные строковые или байтовые данные к типу bytes (UTF-8)."""
    if isinstance(data, str):
        return data.encode("utf-8")
    return bytes(data)


def crc32(data: bytes | bytearray | str, initial: int = 0) -> int:
    """Вычисляет контрольную сумму CRC-32 для переданных данных.

    Соответствует стандарту IEEE 802.3 и функции binascii.crc32.

    :param data: Входные байты или строка (кодируется в UTF-8).
    :param initial: Начальное значение контрольной суммы (для цепочечных вычислений).
    :return: 32-битное беззнаковое целое число.
    """
    byte_data = _to_bytes(data)
    crc = initial ^ 0xFFFFFFFF

    for b in byte_data:
        crc = (crc >> 8) ^ _CRC32_TABLE[(crc ^ b) & 0xFF]

    return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF


def crc32_hex(data: bytes | bytearray | str) -> str:
    """Вычисляет CRC-32 и возвращает шестнадцатеричную строку из 8 символов в нижнем регистре."""
    return f"{crc32(data):08x}"


def fnv1a_32(data: bytes | bytearray | str, initial: int = _FNV_32_OFFSET_BASIS) -> int:
    """Вычисляет 32-битный хеш FNV-1a.

    :param data: Входные байты или строка (UTF-8).
    :param initial: Начальное значение хеша (по умолчанию FNV-1a 32 offset basis).
    :return: 32-битное целое число без знака.
    """
    byte_data = _to_bytes(data)
    hash_val: int = initial & _FNV_32_MASK

    for b in byte_data:
        hash_val ^= b
        hash_val = (hash_val * _FNV_32_PRIME) & _FNV_32_MASK

    return hash_val


def fnv1a_32_hex(data: bytes | bytearray | str) -> str:
    """Вычисляет 32-битный FNV-1a и возвращает 8-символьную hex-строку."""
    return f"{fnv1a_32(data):08x}"


def fnv1a_64(data: bytes | bytearray | str, initial: int = _FNV_64_OFFSET_BASIS) -> int:
    """Вычисляет 64-битный хеш FNV-1a.

    :param data: Входные байты или строка (UTF-8).
    :param initial: Начальное значение хеша (по умолчанию FNV-1a 64 offset basis).
    :return: 64-битное целое число без знака.
    """
    byte_data = _to_bytes(data)
    hash_val: int = initial & _FNV_64_MASK

    for b in byte_data:
        hash_val ^= b
        hash_val = (hash_val * _FNV_64_PRIME) & _FNV_64_MASK

    return hash_val


def fnv1a_64_hex(data: bytes | bytearray | str) -> str:
    """Вычисляет 64-битный FNV-1a и возвращает 16-символьную hex-строку."""
    return f"{fnv1a_64(data):016x}"


def hash_stream_crc32(chunks: Iterable[bytes | bytearray | str]) -> int:
    """Вычисляет итоговый CRC-32 для потока порций (чанков) данных.

    :param chunks: Итерируемый набор порций данных.
    :return: Итоговая 32-битная контрольная сумма.
    """
    current_crc = 0
    for chunk in chunks:
        current_crc = crc32(chunk, initial=current_crc)
    return current_crc
