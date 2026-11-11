"""Модуль стилизации и раскрашивания консольного текста (ANSI Colorizer & Text Styler).

Предоставляет функции colorize, strip_ansi, шорткаты цветов (red, green, bold и др.)
с автоопределением поддержки ANSI-кодов терминалом (TTY, переменная NO_COLOR).
"""

import os
import re
import sys

# Регулярное выражение для удаления ANSI-последовательностей
_ANSI_STRIP_REGEX: re.Pattern[str] = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Глобальный переключатель активности цветов (None — автоопределение)
_COLORS_OVERRIDE: bool | None = None

# Таблицы кодов ANSI
_FOREGROUNDS: dict[str, int] = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}

_BACKGROUNDS: dict[str, int] = {
    "black": 40,
    "red": 41,
    "green": 42,
    "yellow": 43,
    "blue": 44,
    "magenta": 45,
    "cyan": 46,
    "white": 47,
    "bright_black": 100,
    "bright_red": 101,
    "bright_green": 102,
    "bright_yellow": 103,
    "bright_blue": 104,
    "bright_magenta": 105,
    "bright_cyan": 106,
    "bright_white": 107,
}

_STYLES: dict[str, int] = {
    "bold": 1,
    "dim": 2,
    "italic": 3,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "hidden": 8,
    "strikethrough": 9,
}


def are_colors_enabled() -> bool:
    """Проверяет, включена ли поддержка цветов в текущем окружении."""
    if _COLORS_OVERRIDE is not None:
        return _COLORS_OVERRIDE

    if "NO_COLOR" in os.environ:
        return False

    if os.environ.get("TERM") == "dumb":
        return False

    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def set_colors_enabled(enabled: bool | None) -> None:
    """Принудительно включает или отключает цветной вывод."""
    global _COLORS_OVERRIDE
    _COLORS_OVERRIDE = enabled


def strip_ansi(text: str) -> str:
    """Удаляет все ANSI escape-коды из строки."""
    if not isinstance(text, str):
        raise TypeError(f"Текст должен быть строкой, получено: {type(text).__name__}")
    return _ANSI_STRIP_REGEX.sub("", text)


def colorize(
    text: str,
    color: str | None = None,
    bg: str | None = None,
    bold: bool = False,
    dim: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
) -> str:
    """Оборачивает текст в управляющие последовательности ANSI."""
    if not isinstance(text, str):
        raise TypeError(f"Текст должен быть строкой, получено: {type(text).__name__}")

    if not are_colors_enabled() or not text:
        return text

    codes: list[int] = []

    if color and color.lower() in _FOREGROUNDS:
        codes.append(_FOREGROUNDS[color.lower()])
    if bg and bg.lower() in _BACKGROUNDS:
        codes.append(_BACKGROUNDS[bg.lower()])
    if bold:
        codes.append(_STYLES["bold"])
    if dim:
        codes.append(_STYLES["dim"])
    if italic:
        codes.append(_STYLES["italic"])
    if underline:
        codes.append(_STYLES["underline"])
    if strikethrough:
        codes.append(_STYLES["strikethrough"])

    if not codes:
        return text

    joined_codes = ";".join(str(c) for c in codes)
    return f"\x1b[{joined_codes}m{text}\x1b[0m"


# Удобные функции-шорткаты
def red(text: str, bold: bool = False) -> str:
    """Возвращает красный текст."""
    return colorize(text, color="red", bold=bold)


def green(text: str, bold: bool = False) -> str:
    """Возвращает зеленый текст."""
    return colorize(text, color="green", bold=bold)


def yellow(text: str, bold: bool = False) -> str:
    """Возвращает желтый текст."""
    return colorize(text, color="yellow", bold=bold)


def blue(text: str, bold: bool = False) -> str:
    """Возвращает синий текст."""
    return colorize(text, color="blue", bold=bold)


def magenta(text: str, bold: bool = False) -> str:
    """Возвращает пурпурный текст."""
    return colorize(text, color="magenta", bold=bold)


def cyan(text: str, bold: bool = False) -> str:
    """Возвращает бирюзовый текст."""
    return colorize(text, color="cyan", bold=bold)


def bold(text: str) -> str:
    """Возвращает жирный текст."""
    return colorize(text, bold=True)


def underline(text: str) -> str:
    """Возвращает подчеркнутый текст."""
    return colorize(text, underline=True)
