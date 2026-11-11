"""Модульные тесты для модуля форматирования и парсинга длительности времени (duration)."""

import pytest

from pocket_toolkit.strings.duration import format_duration, parse_duration


def test_format_duration_ru() -> None:
    """Проверка форматирования на русском языке."""
    assert format_duration(0) == "0с"
    assert format_duration(45) == "45с"
    assert format_duration(125) == "2м 5с"
    assert format_duration(3665) == "1ч 1м 5с"
    assert format_duration(90061) == "1д 1ч 1м"


def test_format_duration_en() -> None:
    """Проверка форматирования на английском языке."""
    assert format_duration(0, lang="en") == "0s"
    assert format_duration(3600, lang="en") == "1h"
    assert format_duration(3665, lang="en") == "1h 1m 5s"
    assert format_duration(86400 * 2, lang="en") == "2d"


def test_format_duration_milliseconds_and_negative() -> None:
    """Проверка малых долей секунд и отрицательных длительностей."""
    assert format_duration(0.25) == "250мс"
    assert format_duration(0.005, lang="en") == "5ms"
    assert format_duration(-120) == "-2м"
    assert format_duration(-3661, lang="en") == "-1h 1m 1s"


def test_format_duration_max_units() -> None:
    """Проверка ограничения количества отображаемых единиц."""
    # 1d 2h 3m 4s -> max_units=2 -> 1д 2ч
    total_seconds = 86400 + 7200 + 180 + 4
    assert format_duration(total_seconds, max_units=2) == "1д 2ч"
    assert format_duration(total_seconds, max_units=1) == "1д"


def test_format_duration_validation() -> None:
    """Проверка валидации параметров в format_duration."""
    with pytest.raises(TypeError):
        format_duration("100")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        format_duration(float("nan"))

    with pytest.raises(ValueError):
        format_duration(10, lang="fr")

    with pytest.raises(ValueError):
        format_duration(10, max_units=0)


def test_parse_duration_ru_and_en() -> None:
    """Проверка парсинга строковых представлений длительности."""
    assert parse_duration("0с") == 0.0
    assert parse_duration("45s") == 45.0
    assert parse_duration("2m 30s") == 150.0
    assert parse_duration("1ч 30мин") == 5400.0
    assert parse_duration("1d 2h") == 86400.0 + 7200.0
    assert parse_duration("500ms") == 0.5
    assert parse_duration("250 мс") == 0.25
    assert parse_duration("-1.5h") == -5400.0


def test_parse_duration_validation() -> None:
    """Проверка обработки некорректных входных строк в parse_duration."""
    with pytest.raises(TypeError):
        parse_duration(123)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        parse_duration("")

    with pytest.raises(ValueError):
        parse_duration("   ")

    with pytest.raises(ValueError):
        parse_duration("100 lightyears")

    with pytest.raises(ValueError):
        parse_duration("abc 123")
