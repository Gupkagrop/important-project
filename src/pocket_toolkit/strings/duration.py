"""Модуль форматирования и парсинга временных интервалов (Time Duration Formatter).

Предоставляет функции format_duration для преобразования секунд в компактный
человекочитаемый вид (например, '2ч 15м 30с' или '2h 15m 30s'), а также
parse_duration для обратного парсинга строк в секунды.
"""

import math
import re

# Поддерживаемые языковые суффиксы для единиц времени
_UNITS_RU: tuple[tuple[str, float], ...] = (
    ("д", 86400.0),
    ("ч", 3600.0),
    ("м", 60.0),
    ("с", 1.0),
    ("мс", 0.001),
)

_UNITS_EN: tuple[tuple[str, float], ...] = (
    ("d", 86400.0),
    ("h", 3600.0),
    ("m", 60.0),
    ("s", 1.0),
    ("ms", 0.001),
)

# Регулярное выражение для извлечения пар (число, единица) из строки
_DURATION_CHUNK_PATTERN: re.Pattern[str] = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Zа-яА-Я]+)"
)

# Таблица коэффициентов перевода единиц измерения в секунды
_DURATION_MULTIPLIERS: dict[str, float] = {
    # Дни
    "d": 86400.0,
    "day": 86400.0,
    "days": 86400.0,
    "д": 86400.0,
    "дн": 86400.0,
    "день": 86400.0,
    "дня": 86400.0,
    "дней": 86400.0,
    # Часы
    "h": 3600.0,
    "hr": 3600.0,
    "hrs": 3600.0,
    "hour": 3600.0,
    "hours": 3600.0,
    "ч": 3600.0,
    "час": 3600.0,
    "часа": 3600.0,
    "часов": 3600.0,
    # Минуты
    "m": 60.0,
    "min": 60.0,
    "mins": 60.0,
    "minute": 60.0,
    "minutes": 60.0,
    "м": 60.0,
    "мин": 60.0,
    "минута": 60.0,
    "минуты": 60.0,
    "минут": 60.0,
    # Секунды
    "s": 1.0,
    "sec": 1.0,
    "secs": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "с": 1.0,
    "сек": 1.0,
    "секунда": 1.0,
    "секунды": 1.0,
    "секунд": 1.0,
    # Миллисекунды
    "ms": 0.001,
    "msec": 0.001,
    "millisecond": 0.001,
    "milliseconds": 0.001,
    "мс": 0.001,
    "мсек": 0.001,
}


def _validate_format_params(seconds: float, lang: str, max_units: int) -> None:
    """Проверяет корректность аргументов format_duration."""
    if not isinstance(seconds, (int, float)):
        raise TypeError(f"Количество секунд должно быть числом, получено: {type(seconds).__name__}")
    if math.isnan(seconds) or math.isinf(seconds):
        raise ValueError("Значение секунд не может быть NaN или бесконечностью")
    if lang.lower() not in ("ru", "en"):
        raise ValueError(f"Неподдерживаемый язык: {lang!r}. Допустимы 'ru' или 'en'")
    if max_units <= 0:
        raise ValueError(f"Параметр max_units должен быть положительным, получено: {max_units}")


def _collect_duration_parts(
    remaining_ms: int,
    units: tuple[tuple[str, float], ...],
    max_units: int,
) -> list[str]:
    """Разбивает миллисекунды на строковые компоненты согласно таблице единиц."""
    parts: list[str] = []

    for suffix, factor in units:
        factor_ms = round(factor * 1000)
        if factor_ms <= 0:
            continue

        count = remaining_ms // factor_ms
        if count > 0:
            parts.append(f"{count}{suffix}")
            remaining_ms %= factor_ms

        if len(parts) >= max_units:
            break

    return parts


def format_duration(
    seconds: float,
    lang: str = "ru",
    max_units: int = 3,
) -> str:
    """Преобразует секунды в компактный человекочитаемый вид.

    :param seconds: Длительность в секундах (может быть отрицательной или дробной).
    :param lang: Язык единиц: 'ru' ('2ч 15м 30с') или 'en' ('2h 15m 30s').
    :param max_units: Максимальное число старших отображаемых компонентов.
    :return: Читаемая строка длительности.
    """
    _validate_format_params(seconds, lang, max_units)

    sign = "-" if seconds < 0 else ""
    abs_seconds = abs(seconds)
    units = _UNITS_RU if lang.lower() == "ru" else _UNITS_EN
    zero_unit = "с" if lang.lower() == "ru" else "s"

    if abs_seconds == 0.0:
        return f"0{zero_unit}"

    total_ms = round(abs_seconds * 1000)
    if total_ms == 0:
        return f"0{zero_unit}"

    parts = _collect_duration_parts(total_ms, units, max_units)
    if not parts:
        ms_suffix = "мс" if lang.lower() == "ru" else "ms"
        return f"{sign}{total_ms}{ms_suffix}"

    return f"{sign}{' '.join(parts)}"


def parse_duration(duration_str: str) -> float:
    """Парсит строку с длительностью во время в секундах (float).

    :param duration_str: Входная строка вида '1d 2h 30m', '45с', '500ms', '-1.5h'.
    :return: Длительность в секундах.
    :raises ValueError: При некорректном формате или неизвестных единицах.
    """
    if not isinstance(duration_str, str):
        raise TypeError(f"Ожидалась строка, получено: {type(duration_str).__name__}")

    stripped = duration_str.strip()
    if not stripped:
        raise ValueError("Строка длительности не может быть пустой")

    sign = -1.0 if stripped.startswith("-") else 1.0
    unsigned_str = stripped[1:].strip() if stripped.startswith(("-", "+")) else stripped

    matches = list(_DURATION_CHUNK_PATTERN.finditer(unsigned_str))
    if not matches:
        raise ValueError(f"Не удалось распознать компоненты длительности: {duration_str!r}")

    # Проверяем, что вся строка покрыта валидными совпадениями
    reconstructed = "".join(m.group(0) for m in matches).replace(" ", "")
    cleaned_source = unsigned_str.replace(" ", "")
    if reconstructed != cleaned_source:
        raise ValueError(f"Обнаружены некорректные символы в строке длительности: {duration_str!r}")

    total_seconds = 0.0
    for match in matches:
        val = float(match.group("value"))
        unit = match.group("unit").lower()
        if unit not in _DURATION_MULTIPLIERS:
            raise ValueError(f"Неизвестная единица измерения времени: {match.group('unit')!r}")
        total_seconds += val * _DURATION_MULTIPLIERS[unit]

    return sign * total_seconds
