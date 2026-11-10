"""Модульные тесты для модуля уплощения словарей (flatten)."""

from typing import Any
import pytest
from pocket_toolkit.data.flatten import flatten_dict, unflatten_dict


def test_flatten_empty_dict() -> None:
    """Проверка пустого словаря."""
    assert flatten_dict({}) == {}
    assert unflatten_dict({}) == {}


def test_flatten_simple_nesting() -> None:
    """Проверка уплощения словаря с простой иерархией."""
    data = {
        "user": {
            "name": "Denis",
            "address": {
                "city": "Moscow",
                "zip": 101000,
            },
        },
        "active": True,
    }

    expected = {
        "user.name": "Denis",
        "user.address.city": "Moscow",
        "user.address.zip": 101000,
        "active": True,
    }

    flattened = flatten_dict(data)
    assert flattened == expected
    assert unflatten_dict(flattened) == data


def test_flatten_with_lists() -> None:
    """Проверка уплощения списков и обратного восстановления."""
    data = {
        "project": "pocket-toolkit",
        "tags": ["python", "utils"],
        "tasks": [
            {"id": 1, "title": "init"},
            {"id": 2, "title": "test"},
        ],
    }

    flattened = flatten_dict(data, flatten_lists=True)
    assert flattened["tags.0"] == "python"
    assert flattened["tags.1"] == "utils"
    assert flattened["tasks.0.id"] == 1
    assert flattened["tasks.1.title"] == "test"

    restored = unflatten_dict(flattened, parse_lists=True)
    assert restored == data


def test_flatten_max_depth() -> None:
    """Проверка ограничения глубины уплощения max_depth."""
    data = {
        "level1": {
            "level2": {
                "level3": "deep_value",
            },
        },
    }

    flat_depth_1 = flatten_dict(data, max_depth=1)
    assert flat_depth_1 == {"level1": {"level2": {"level3": "deep_value"}}}

    flat_depth_2 = flatten_dict(data, max_depth=2)
    assert flat_depth_2 == {"level1.level2": {"level3": "deep_value"}}


def test_flatten_custom_separator() -> None:
    """Проверка пользовательского разделителя."""
    data = {"a": {"b": {"c": 42}}}
    flattened_slash = flatten_dict(data, sep="/")
    assert flattened_slash == {"a/b/c": 42}
    assert unflatten_dict(flattened_slash, sep="/") == data


def test_flatten_validation() -> None:
    """Проверка валидации входных аргументов."""
    with pytest.raises(TypeError):
        flatten_dict([1, 2, 3])  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        flatten_dict({"a": 1}, sep="")

    with pytest.raises(TypeError):
        unflatten_dict("not a dict")  # type: ignore[arg-type]
