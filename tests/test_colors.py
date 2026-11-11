"""Модульные тесты для модуля стилизации и раскрашивания текста (colors)."""

import pytest

from pocket_toolkit.cli.colors import (
    are_colors_enabled,
    blue,
    bold,
    colorize,
    cyan,
    green,
    magenta,
    red,
    set_colors_enabled,
    strip_ansi,
    underline,
    yellow,
)


@pytest.fixture(autouse=True)
def reset_colors() -> None:
    """Сбрасывает принудительное состояние цветов после каждого теста."""
    yield
    set_colors_enabled(None)


def test_colorize_when_enabled() -> None:
    """Проверка генерации ANSI кодов при включенном режиме цветов."""
    set_colors_enabled(True)
    assert are_colors_enabled() is True

    colored = colorize("Привет", color="red", bold=True)
    assert colored == "\x1b[31;1mПривет\x1b[0m"

    bg_colored = colorize("Фон", bg="blue", underline=True)
    assert bg_colored == "\x1b[44;4mФон\x1b[0m"


def test_color_shortcuts() -> None:
    """Проверка функций-шорткатов для основных цветов и стилей."""
    set_colors_enabled(True)

    assert red("Error") == "\x1b[31mError\x1b[0m"
    assert green("Success") == "\x1b[32mSuccess\x1b[0m"
    assert yellow("Warning") == "\x1b[33mWarning\x1b[0m"
    assert blue("Info") == "\x1b[34mInfo\x1b[0m"
    assert magenta("Debug") == "\x1b[35mDebug\x1b[0m"
    assert cyan("Trace") == "\x1b[36mTrace\x1b[0m"
    assert bold("Important") == "\x1b[1mImportant\x1b[0m"
    assert underline("Link") == "\x1b[4mLink\x1b[0m"


def test_colorize_when_disabled() -> None:
    """Проверка возврата исходного текста при отключенных цветах."""
    set_colors_enabled(False)
    assert are_colors_enabled() is False

    assert colorize("Текст", color="red", bold=True) == "Текст"
    assert red("Error") == "Error"
    assert green("OK") == "OK"


def test_strip_ansi() -> None:
    """Проверка очистки строки от ANSI escape-кодов."""
    set_colors_enabled(True)
    sample = f"{red('Красный')} и {bold('Жирный')} и обычный"
    stripped = strip_ansi(sample)
    assert stripped == "Красный и Жирный и обычный"

    assert strip_ansi("Чистый текст") == "Чистый текст"


def test_validation_errors() -> None:
    """Проверка валидации входных типов данных."""
    with pytest.raises(TypeError):
        colorize(123)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        strip_ansi(None)  # type: ignore[arg-type]
