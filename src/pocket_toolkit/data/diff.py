"""Модуль нахождения различий и дельты между словарями (Dict Difference & Delta Finder).

Предоставляет класс DictDiff и функции diff_dict, find_dict_delta для детального
анализа добавленных, удаленных и измененных ключей между двумя иерархическими структурами данных.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DictDiff:
    """Результат сопоставления двух словарей.

    Содержит информацию о добавленных, удаленных, измененных и оставшихся
    без изменений ключах.
    """

    added: dict[str, object] = field(default_factory=dict)
    removed: dict[str, object] = field(default_factory=dict)
    changed: dict[str, tuple[object, object]] = field(default_factory=dict)
    unchanged: dict[str, object] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        """Возвращает True, если между структурами обнаружены какие-либо различия."""
        if bool(self.added):
            return True
        if bool(self.removed):
            return True
        return bool(self.changed)

    def to_dict(self) -> dict[str, dict[str, object]]:
        """Преобразует отчет о различиях в стандартный словарь."""
        serialized_changed: dict[str, object] = {
            key: {"old": val[0], "new": val[1]} for key, val in self.changed.items()
        }
        return {
            "added": dict(self.added),
            "removed": dict(self.removed),
            "changed": serialized_changed,
            "unchanged": dict(self.unchanged),
        }


def _validate_input_mappings(first: object, second: object, sep: str) -> None:
    """Проверяет корректность входных аргументов сравнения."""
    if not isinstance(first, Mapping):
        raise TypeError(f"Первый аргумент должен быть Mapping, получено: {type(first).__name__}")
    if not isinstance(second, Mapping):
        raise TypeError(f"Второй аргумент должен быть Mapping, получено: {type(second).__name__}")
    if not sep:
        raise ValueError("Разделитель путей не может быть пустой строкой")


def _build_path(prefix: str, key: str, sep: str) -> str:
    """Формирует составной путь для вложенного ключа."""
    if not prefix:
        return key
    return f"{prefix}{sep}{key}"


def _process_diff_key(
    key: str,
    prefix: str,
    first_val: object,
    second_val: object,
    sep: str,
    recursive: bool,
    diff: DictDiff,
) -> None:
    """Обрабатывает общий ключ, присутствующий в обоих словарях."""
    path = _build_path(prefix, key, sep)

    if recursive and isinstance(first_val, Mapping) and isinstance(second_val, Mapping):
        _compare_mappings(first_val, second_val, path, sep, recursive, diff)
        return

    if first_val == second_val:
        diff.unchanged[path] = first_val
        return

    diff.changed[path] = (first_val, second_val)


def _compare_mappings(
    first: Mapping[str, object],
    second: Mapping[str, object],
    prefix: str,
    sep: str,
    recursive: bool,
    diff: DictDiff,
) -> None:
    """Рекурсивный обход словарей и заполнение отчета о различиях."""
    first_keys = set(first.keys())
    second_keys = set(second.keys())

    for key in sorted(first_keys - second_keys):
        path = _build_path(prefix, key, sep)
        diff.removed[path] = first[key]

    for key in sorted(second_keys - first_keys):
        path = _build_path(prefix, key, sep)
        diff.added[path] = second[key]

    for key in sorted(first_keys & second_keys):
        _process_diff_key(
            key,
            prefix,
            first[key],
            second[key],
            sep,
            recursive,
            diff,
        )


def diff_dict(
    first: Mapping[str, object],
    second: Mapping[str, object],
    recursive: bool = True,
    path_separator: str = ".",
) -> DictDiff:
    """Сравнивает два словаря и возвращает детальный отчет DictDiff.

    :param first: Исходный словарь (базовое состояние).
    :param second: Целевой словарь (новое состояние).
    :param recursive: Сравнивать ли вложенные словари рекурсивно.
    :param path_separator: Разделитель составных путей в итоговом отчете.
    :return: Объект DictDiff с коллекциями добавленных, удаленных и измененных ключей.
    """
    _validate_input_mappings(first, second, path_separator)
    diff = DictDiff()
    _compare_mappings(first, second, "", path_separator, recursive, diff)
    return diff


def find_dict_delta(
    first: Mapping[str, object],
    second: Mapping[str, object],
) -> dict[str, object]:
    """Вычисляет компактный словарь-дельту для преобразования first в second.

    Удаленные ключи помечаются значением None (в стиле RFC 7396 Merge Patch),
    а вложенные словари обрабатываются рекурсивно.
    """
    _validate_input_mappings(first, second, ".")
    delta: dict[str, object] = {}

    first_keys = set(first.keys())
    second_keys = set(second.keys())

    for key in sorted(first_keys - second_keys):
        delta[key] = None

    for key in sorted(second_keys - first_keys):
        delta[key] = second[key]

    for key in sorted(first_keys & second_keys):
        val1 = first[key]
        val2 = second[key]

        if isinstance(val1, Mapping) and isinstance(val2, Mapping):
            nested_delta = find_dict_delta(val1, val2)
            if nested_delta:
                delta[key] = nested_delta
            continue

        if val1 != val2:
            delta[key] = val2

    return delta
