"""Модульные тесты для модуля форматирования и парсинга размеров байтов (bytes)."""

import pytest

from pocket_toolkit.strings.bytes import IEC_UNITS, SI_UNITS, format_bytes, parse_bytes


def test_format_bytes_iec() -> None:
    """Проверка форматирования по стандарту IEC (основание 1024)."""
    assert format_bytes(0) == "0 B"
    assert format_bytes(500) == "500 B"
    assert format_bytes(1024) == "1.00 KiB"
    assert format_bytes(1536) == "1.50 KiB"
    assert format_bytes(1024 * 1024) == "1.00 MiB"
    assert format_bytes(1024**3 * 2.5) == "2.50 GiB"
    assert format_bytes(1024**4) == "1.00 TiB"


def test_format_bytes_si() -> None:
    """Проверка форматирования по стандарту SI (основание 1000)."""
    assert format_bytes(0, standard="si") == "0 B"
    assert format_bytes(999, standard="si") == "999 B"
    assert format_bytes(1000, standard="si") == "1.00 kB"
    assert format_bytes(1500, standard="si") == "1.50 kB"
    assert format_bytes(1_000_000, standard="si") == "1.00 MB"
    assert format_bytes(1_000_000_000, standard="si") == "1.00 GB"


def test_format_bytes_negative_and_precision() -> None:
    """Проверка отрицательных значений и настраиваемой точности."""
    assert format_bytes(-1024) == "-1.00 KiB"
    assert format_bytes(-1536, precision=1) == "-1.5 KiB"
    assert format_bytes(1234567, precision=3) == "1.177 MiB"
    assert format_bytes(1024 * 1024, precision=0) == "1 MiB"


def test_format_bytes_validation() -> None:
    """Проверка валидации параметров format_bytes."""
    with pytest.raises(TypeError):
        format_bytes("1024")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        format_bytes(1024, standard="custom")

    with pytest.raises(ValueError):
        format_bytes(1024, precision=-1)


def test_parse_bytes_valid_units() -> None:
    """Проверка корректного парсинга строк в байты."""
    assert parse_bytes("0 B") == 0
    assert parse_bytes("1024") == 1024
    assert parse_bytes("1 KiB") == 1024
    assert parse_bytes("1.5 MiB") == 1572864
    assert parse_bytes("2 GB") == 2000000000
    assert parse_bytes("500 mb") == 500000000
    assert parse_bytes("4k") == 4096
    assert parse_bytes("-2.5 GiB") == -2684354560


def test_parse_bytes_validation() -> None:
    """Проверка обработки некорректных строк в parse_bytes."""
    with pytest.raises(TypeError):
        parse_bytes(1024)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        parse_bytes("invalid-string")

    with pytest.raises(ValueError):
        parse_bytes("100 lightyears")


def test_constants_coverage() -> None:
    """Проверка наличия базовых констант единиц измерения."""
    assert "KiB" in IEC_UNITS
    assert "MB" in SI_UNITS
