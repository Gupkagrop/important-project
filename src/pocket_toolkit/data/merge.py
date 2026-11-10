"""Модуль глубокого рекурсивного слияния словарей и дельта-патчей (Deep Merge & Patch).

Предоставляет функцию `deep_merge` для рекурсивного объединения нескольких словарей
с настраиваемой стратегией обработки списков (replace, concat, union),
а также функцию `deep_patch` для применения JSON-like дельта-патчей (RFC 7396).
"""

from collections.abc import Mapping, Sequence
import copy
from typing import Any

# Специальный объект-маркер для явного удаления ключей в deep_patch
DELETE_FIELD: object = object()


def deep_merge(
    target: Mapping[str, Any],
    *sources: Mapping[str, Any],
    list_strategy: str = "replace",
) -> dict[str, Any]:
    """Рекурсивно объединяет несколько словарей в новый словарь без мутации исходных.

    :param target: Базовый словарь.
    :param sources: Последовательность словарей-источников, накатываемых поверх target.
    :param list_strategy: Стратегия разрешения конфликтов списков:
        - 'replace': список из source заменяет список target (по умолчанию).
        - 'concat': списки объединяются последовательно (target + source).
        - 'union': объединение уникальных элементов с сохранением порядка.
    :return: Новый объединенный словарь.
    :raises ValueError: При передаче неподдерживаемой стратегии list_strategy.
    """
    valid_strategies = ("replace", "concat", "union")
    if list_strategy not in valid_strategies:
        raise ValueError(
            f"Неподдерживаемая стратегия list_strategy: {list_strategy!r}. "
            f"Допустимы: {', '.join(valid_strategies)}"
        )

    result: dict[str, Any] = copy.deepcopy(dict(target))

    for source in sources:
        if not isinstance(source, Mapping):
            raise TypeError(f"Все источники должны быть Mapping, получено: {type(source).__name__}")

        for key, val in source.items():
            if key in result and isinstance(result[key], Mapping) and isinstance(val, Mapping):
                # Рекурсивно сливаем вложенные словари
                result[key] = deep_merge(result[key], val, list_strategy=list_strategy)
            elif key in result and isinstance(result[key], list) and isinstance(val, list):
                # Обработка списков согласно выбранной стратегии
                if list_strategy == "replace":
                    result[key] = copy.deepcopy(val)
                elif list_strategy == "concat":
                    result[key] = copy.deepcopy(result[key] + val)
                elif list_strategy == "union":
                    combined: list[Any] = []
                    seen: set[Any] = set()
                    for item in result[key] + val:
                        # Для хешируемых типов используем seen, для нехешируемых — линейную проверку
                        try:
                            if item not in seen:
                                seen.add(item)
                                combined.append(copy.deepcopy(item))
                        except TypeError:
                            if item not in combined:
                                combined.append(copy.deepcopy(item))
                    result[key] = combined
            else:
                result[key] = copy.deepcopy(val)

    return result


def deep_patch(
    target: Mapping[str, Any],
    patch: Mapping[str, Any],
    delete_marker: Any = DELETE_FIELD,
) -> dict[str, Any]:
    """Применяет дельта-патч к словарю по стандарту RFC 7396 JSON Merge Patch.

    Если значение ключа в patch равно delete_marker (по умолчанию DELETE_FIELD),
    ключ удаляется из результирующего словаря.
    Если и в target, и в patch значение является словарем, происходит рекурсивное применение патча.
    В остальных случаях значение из patch заменяет значение в target.

    :param target: Исходный словарь.
    :param patch: Словарь изменений (дельта).
    :param delete_marker: Значение, сигнализирующее об удалении ключа (по умолчанию DELETE_FIELD).
    :return: Новый словарь с примененным патчем.
    """
    if not isinstance(target, Mapping) or not isinstance(patch, Mapping):
        raise TypeError("target и patch должны быть типа Mapping")

    result: dict[str, Any] = copy.deepcopy(dict(target))

    for key, val in patch.items():
        if val is delete_marker:
            result.pop(key, None)
        elif key in result and isinstance(result[key], Mapping) and isinstance(val, Mapping):
            result[key] = deep_patch(result[key], val, delete_marker=delete_marker)
        else:
            result[key] = copy.deepcopy(val)

    return result
