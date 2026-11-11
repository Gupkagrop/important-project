"""Модуль форматирования и парсинга размеров данных в байтах (Byte Formatter).

Предоставляет функции format_bytes для человекочитаемого представления байтов
в стандартах IEC (1024, KiB/MiB) и SI (1000, kB/MB), а также parse_bytes для обратного парсинга.
"""

import re

IEC_UNITS: tuple[str, ...] = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
SI_UNITS: tuple[str, ...] = ("B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")

# Регулярное выражение для разбора строкового представления размера
_SIZE_PATTERN: re.Pattern[str] = re.compile(
    r"^\s*(?P<sign>[+-]?)(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]*)\s*$"
)

# Словарь единиц измерения для быстрого поиска коэффициента
_UNIT_MULTIPLIERS: dict[str, int] = {
    "b": 1,
    "byte": 1,
    "bytes": 1,
    # Двоичные приставки IEC
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
    "tib": 1024**4,
    "pib": 1024**5,
    "eib": 1024**6,
    "zib": 1024**7,
    "yib": 1024**8,
    # Десятичные приставки SI
    "kb": 1000,
    "mb": 1000**2,
    "gb": 1000**3,
    "tb": 1000**4,
    "pb": 1000**5,
    "eb": 1000**6,
    "zb": 1000**7,
    "yb": 1000**8,
    # Однобуквенные обозначения (по умолчанию трактуются как двоичные)
    "k": 1024,
    "m": 1024**2,
    "g": 1024**3,
    "t": 1024**4,
    "p": 1024**5,
    "e": 1024**6,
}


def _validate_format_arguments(num_bytes: float, standard: str, precision: int) -> None:
    """Проверяет корректность аргументов форматирования байтов."""
    if not isinstance(num_bytes, (int, float)):
        raise TypeError(f"Число байт должно быть int или float, получено: {type(num_bytes).__name__}")
    if precision < 0:
        raise ValueError(f"Точность precision не может быть отрицательной, получено: {precision}")
    if standard.lower() not in ("iec", "si"):
        raise ValueError(f"Неизвестный стандарт: {standard!r}. Допустимы 'iec' или 'si'")


def format_bytes(
    num_bytes: float,
    standard: str = "iec",
    precision: int = 2,
) -> str:
    """Форматирует число байт в читаемую строку с суффиксом единиц измерения.

    :param num_bytes: Количество байт (может быть отрицательным).
    :param standard: Стандарт измерения: 'iec' (основание 1024) или 'si' (основание 1000).
    :param precision: Количество знаков после запятой для дробных величин.
    :return: Читаемая строка (например, '1.50 MiB' или '1.00 kB').
    """
    _validate_format_arguments(num_bytes, standard, precision)

    units = IEC_UNITS if standard.lower() == "iec" else SI_UNITS
    base = 1024.0 if standard.lower() == "iec" else 1000.0

    sign = "-" if num_bytes < 0 else ""
    value = float(abs(num_bytes))

    unit_idx = 0
    max_idx = len(units) - 1

    while value >= base and unit_idx < max_idx:
        value /= base
        unit_idx += 1

    if unit_idx == 0:
        return f"{sign}{int(value)} {units[0]}"

    return f"{sign}{value:.{precision}f} {units[unit_idx]}"


def parse_bytes(size_str: str) -> int:
    """Парсит строковое представление объема данных в точное целое число байт.

    :param size_str: Строка с размером данных (например, '10 MB', '2.5 GiB', '512').
    :return: Объем данных в байтах.
    :raises ValueError: Если строка имеет неверный формат или неизвестную единицу измерения.
    """
    if not isinstance(size_str, str):
        raise TypeError(f"Ожидалась строка, получено: {type(size_str).__name__}")

    match = _SIZE_PATTERN.match(size_str.strip())
    if not match:
        raise ValueError(f"Некорректный формат строки размера: {size_str!r}")

    sign = -1 if match.group("sign") == "-" else 1
    number = float(match.group("number"))
    unit = match.group("unit").lower()

    if not unit:
        return int(sign * number)

    if unit not in _UNIT_MULTIPLIERS:
        raise ValueError(f"Неизвестная единица измерения объема данных: {match.group('unit')!r}")

    multiplier = _UNIT_MULTIPLIERS[unit]
    return round(sign * number * multiplier)
