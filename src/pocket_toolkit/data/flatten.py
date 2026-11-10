"""Модуль уплощения и восстановления вложенных структур данных (Flatten & Unflatten).

Предоставляет функции `flatten_dict` для преобразования произвольно вложенных словарей и списков
в плоский словарь вида `{"user.address.city": "Moscow", "items.0.id": 1}` с настраиваемым разделителем,
и `unflatten_dict` для обратного восстановления оригинальной иерархической структуры.
"""

from collections.abc import Mapping
from typing import Any


def flatten_dict(
    data: Mapping[str, Any],
    sep: str = ".",
    max_depth: int | None = None,
    flatten_lists: bool = True,
) -> dict[str, Any]:
    """Преобразует глубоко вложенный словарь в плоский словарь с составными ключами.

    :param data: Вложенный словарь данных.
    :param sep: Символ или строка-разделитель вложенности (по умолчанию '.').
    :param max_depth: Максимальная глубина уплощения (None — без ограничений).
    :param flatten_lists: Уплощать ли элементы списков с индексами 'key.0', 'key.1'.
    :return: Плоский словарь {составной_ключ: скалярное_значение}.
    """
    if not isinstance(data, Mapping):
        raise TypeError(f"Ожидался Mapping (словарь), получено: {type(data).__name__}")
    if not sep:
        raise ValueError("Разделитель sep не может быть пустой строкой")

    result: dict[str, Any] = {}

    def _flatten(current: Any, prefix: str, depth: int) -> None:
        reached_limit = max_depth is not None and depth >= max_depth

        if isinstance(current, Mapping) and current and not reached_limit:
            for k, v in current.items():
                str_key = str(k)
                new_prefix = f"{prefix}{sep}{str_key}" if prefix else str_key
                _flatten(v, new_prefix, depth + 1)
            return

        if flatten_lists and isinstance(current, (list, tuple)) and current and not reached_limit:
            for idx, item in enumerate(current):
                new_prefix = f"{prefix}{sep}{idx}" if prefix else str(idx)
                _flatten(item, new_prefix, depth + 1)
            return

        # Листовое значение (скаляр, пустое множество/список или превышена глубина)
        result[prefix] = current

    if not data:
        return {}

    _flatten(data, "", 0)
    return result


def _convert_contiguous_numeric_keys(obj: Any) -> Any:
    """Рекурсивно преобразует словари с непрерывными целочисленными ключами '0', '1', ... в списки."""
    if not isinstance(obj, dict):
        return obj

    # Сначала рекурсивно обрабатываем детей
    for k, v in list(obj.items()):
        obj[k] = _convert_contiguous_numeric_keys(v)

    # Проверяем, являются ли все ключи числами от 0 до N-1
    keys = list(obj.keys())
    if not keys:
        return obj

    try:
        int_keys = [int(k) for k in keys]
    except ValueError:
        return obj

    # Проверяем непрерывность 0, 1, ..., N-1
    if sorted(int_keys) == list(range(len(keys))):
        sorted_pairs = sorted(zip(int_keys, (obj[str(k)] for k in int_keys), strict=False))
        return [pair[1] for pair in sorted_pairs]

    return obj


def unflatten_dict(
    flat_data: Mapping[str, Any],
    sep: str = ".",
    parse_lists: bool = True,
) -> dict[str, Any]:
    """Восстанавливает иерархический вложенный словарь из плоского словаря.

    :param flat_data: Плоский словарь с составными ключами.
    :param sep: Разделитель уровней иерархии.
    :param parse_lists: Преобразовывать ли числовые цепочки '0', '1' обратно в списки.
    :return: Восстановленный вложенный словарь (с вложенными списками, если parse_lists=True).
    """
    if not isinstance(flat_data, Mapping):
        raise TypeError(f"Ожидался Mapping (словарь), получено: {type(flat_data).__name__}")
    if not sep:
        raise ValueError("Разделитель sep не может быть пустой строкой")

    root: dict[str, Any] = {}

    for composite_key, value in flat_data.items():
        parts = composite_key.split(sep)
        current = root

        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    if parse_lists:
        res = _convert_contiguous_numeric_keys(root)
        return res if isinstance(res, dict) else root

    return root
