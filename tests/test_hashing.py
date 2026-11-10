"""Модульные тесты для модуля некриптографического хеширования (hashing)."""

import binascii
from pocket_toolkit.algorithms.hashing import (
    crc32,
    crc32_hex,
    fnv1a_32,
    fnv1a_32_hex,
    fnv1a_64,
    fnv1a_64_hex,
    hash_stream_crc32,
)


def test_crc32_matches_binascii() -> None:
    """Проверка полного соответствия вычислений CRC32 стандартной библиотеке binascii."""
    test_cases = [
        b"",
        b"123456789",
        b"Hello, World!",
        "Русский текст и UTF-8 символы 🚀",
        b"\x00\xff\x7f\x80\xaa\x55",
        "a" * 1000,
    ]

    for data in test_cases:
        expected = binascii.crc32(data if isinstance(data, bytes) else data.encode("utf-8"))
        actual = crc32(data)
        assert actual == expected
        assert crc32_hex(data) == f"{expected:08x}"


def test_crc32_incremental_stream() -> None:
    """Проверка инкрементального потокового вычисления CRC32."""
    full_text = "The quick brown fox jumps over the lazy dog"
    chunks = ["The quick ", "brown fox ", "jumps over ", "the lazy dog"]

    expected = binascii.crc32(full_text.encode("utf-8"))
    actual_stream = hash_stream_crc32(chunks)
    assert actual_stream == expected


def test_fnv1a_32_known_vectors() -> None:
    """Проверка 32-битного алгоритма FNV-1a по каноническим тестовым векторам."""
    # Тестовые векторы спецификации Fowler-Noll-Vo
    assert fnv1a_32("") == 0x811C9DC5
    assert fnv1a_32("a") == 0xE40C292C
    assert fnv1a_32("foobar") == 0xBF9CF968

    assert fnv1a_32_hex("") == "811c9dc5"
    assert fnv1a_32_hex("a") == "e40c292c"
    assert fnv1a_32_hex("foobar") == "bf9cf968"


def test_fnv1a_64_known_vectors() -> None:
    """Проверка 64-битного алгоритма FNV-1a по каноническим тестовым векторам."""
    # Тестовые векторы спецификации Fowler-Noll-Vo
    assert fnv1a_64("") == 0xCBF29CE484222325
    assert fnv1a_64("a") == 0xAF63DC4C8601EC8C
    assert fnv1a_64("foobar") == 0x85944171F73967E8

    assert fnv1a_64_hex("") == "cbf29ce484222325"
    assert fnv1a_64_hex("a") == "af63dc4c8601ec8c"
    assert fnv1a_64_hex("foobar") == "85944171f73967e8"


def test_bytearray_input() -> None:
    """Проверка корректной обработки данных типа bytearray."""
    arr = bytearray(b"test bytearray")
    assert crc32(arr) == binascii.crc32(arr)
    assert fnv1a_32(arr) == fnv1a_32(b"test bytearray")
    assert fnv1a_64(arr) == fnv1a_64(b"test bytearray")
