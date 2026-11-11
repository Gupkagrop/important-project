"""Модуль разбора и формирования параметров строки запроса URL (Query String Parser & Builder).

Предоставляет класс QueryParams и функции parse_query, build_query для удобной работы
с query-параметрами URL, поддержки повторяющихся ключей, кодирования и декодирования (RFC 3986).
"""

import urllib.parse
from collections.abc import Iterable, Mapping


class QueryParams:
    """Коллекция query-параметров с поддержкой множественных значений для одного ключа."""

    def __init__(self, initial: Mapping[str, object] | str | None = None) -> None:
        """Инициализирует параметры из словаря или сырой query-строки."""
        self._data: dict[str, list[str]] = {}
        if isinstance(initial, str):
            self._parse_raw(initial)
        elif isinstance(initial, Mapping):
            self._load_from_mapping(initial)

    def _parse_raw(self, raw: str) -> None:
        """Парсит сырую строку параметров."""
        cleaned = raw.lstrip("?")
        if not cleaned:
            return

        parsed = urllib.parse.parse_qs(cleaned, keep_blank_values=True)
        for key, values in parsed.items():
            self._data[key] = list(values)

    def _load_from_mapping(self, mapping: Mapping[str, object]) -> None:
        """Загружает параметры из словаря."""
        for key, val in mapping.items():
            if isinstance(val, (list, tuple)):
                self._data[key] = [str(x) for x in val]
            elif val is not None:
                self._data[key] = [str(val)]

    def get(self, key: str, default: str | None = None) -> str | None:
        """Возвращает первое значение по ключу или default."""
        values = self._data.get(key)
        if not values:
            return default
        return values[0]

    def get_all(self, key: str) -> list[str]:
        """Возвращает список всех значений для ключа."""
        return list(self._data.get(key, []))

    def add(self, key: str, value: object) -> None:
        """Добавляет дополнительное значение к существующему ключу."""
        str_val = str(value)
        if key not in self._data:
            self._data[key] = []
        self._data[key].append(str_val)

    def set(self, key: str, value: object) -> None:
        """Устанавливает или перезаписывает значение ключа."""
        self._data[key] = [str(value)]

    def remove(self, key: str) -> None:
        """Удаляет ключ и все его значения."""
        self._data.pop(key, None)

    def keys(self) -> list[str]:
        """Возвращает список уникальных ключей."""
        return list(self._data.keys())

    def to_dict(self, flat: bool = True) -> dict[str, str | list[str]]:
        """Преобразует параметры в стандартный словарь.

        Если flat=True, ключи с одним значением разворачиваются в строку.
        """
        result: dict[str, str | list[str]] = {}
        for k, v in self._data.items():
            if flat and len(v) == 1:
                result[k] = v[0]
            else:
                result[k] = list(v)
        return result

    def to_query_string(self, sort_keys: bool = False) -> str:
        """Собирает параметры в закодированную URL query-строку."""
        pairs: list[tuple[str, str]] = []
        keys = sorted(self._data.keys()) if sort_keys else list(self._data.keys())

        for key in keys:
            for val in self._data[key]:
                pairs.append((key, val))

        return urllib.parse.urlencode(pairs, doseq=True)

    def __str__(self) -> str:
        """Строковое представление параметров."""
        return self.to_query_string()

    def __len__(self) -> int:
        """Возвращает количество уникальных параметров."""
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        """Проверяет наличие параметра в коллекции."""
        return key in self._data


def parse_query(
    query_string: str,
    keep_blank_values: bool = False,
    flat: bool = True,
) -> dict[str, str | list[str]]:
    """Разбирает URL query-строку в словарь параметров.

    :param query_string: Строка запроса (с префиксом '?' или без).
    :param keep_blank_values: Сохранять ли параметры с пустыми значениями.
    :param flat: Разворачивать ли одиночные элементы списков в скалярные строки.
    :return: Словарь параметров.
    """
    if not isinstance(query_string, str):
        raise TypeError(f"query_string должна быть строкой, получено: {type(query_string).__name__}")

    cleaned = query_string.lstrip("?")
    if not cleaned:
        return {}

    parsed = urllib.parse.parse_qs(cleaned, keep_blank_values=keep_blank_values)
    result: dict[str, str | list[str]] = {}

    for k, v in parsed.items():
        if flat and len(v) == 1:
            result[k] = v[0]
        else:
            result[k] = list(v)

    return result


def build_query(
    params: Mapping[str, object],
    sort_keys: bool = False,
) -> str:
    """Формирует URL-закодированную query-строку из словаря параметров.

    :param params: Словарь с параметрами (значения могут быть скалярами или списками).
    :param sort_keys: Сортировать ли ключи в лексикографическом порядке.
    :return: Закодированная строка параметров без начального '?'.
    """
    if not isinstance(params, Mapping):
        raise TypeError(f"params должен быть Mapping, получено: {type(params).__name__}")

    pairs: list[tuple[str, str]] = []
    keys = sorted(params.keys()) if sort_keys else list(params.keys())

    for k in keys:
        val = params[k]
        if val is None:
            continue
        if isinstance(val, (list, tuple)) and not isinstance(val, (str, bytes)) or isinstance(val, Iterable) and not isinstance(val, (str, bytes, Mapping)):
            for item in val:
                pairs.append((k, str(item)))
        else:
            pairs.append((k, str(val)))

    return urllib.parse.urlencode(pairs)
