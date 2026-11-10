"""Модульные тесты для модуля глубокого слияния и патчинга (merge)."""

import pytest
from pocket_toolkit.data.merge import DELETE_FIELD, deep_merge, deep_patch


def test_deep_merge_basic_and_nesting() -> None:
    """Проверка базового и рекурсивного слияния словарей."""
    target = {
        "a": 1,
        "config": {
            "timeout": 30,
            "retries": 3,
        },
    }
    source = {
        "b": 2,
        "config": {
            "timeout": 60,
            "host": "localhost",
        },
    }

    result = deep_merge(target, source)
    expected = {
        "a": 1,
        "b": 2,
        "config": {
            "timeout": 60,
            "retries": 3,
            "host": "localhost",
        },
    }
    assert result == expected

    # Проверка неизменяемости исходных словарей
    assert target["config"]["timeout"] == 30
    assert "host" not in target["config"]


def test_deep_merge_list_strategies() -> None:
    """Проверка различных стратегий обработки списков при слиянии."""
    target = {"tags": ["python", "utils"], "counts": [1, 2]}
    source = {"tags": ["utils", "async"], "counts": [2, 3]}

    # Стратегия replace
    res_replace = deep_merge(target, source, list_strategy="replace")
    assert res_replace["tags"] == ["utils", "async"]

    # Стратегия concat
    res_concat = deep_merge(target, source, list_strategy="concat")
    assert res_concat["tags"] == ["python", "utils", "utils", "async"]

    # Стратегия union
    res_union = deep_merge(target, source, list_strategy="union")
    assert res_union["tags"] == ["python", "utils", "async"]
    assert res_union["counts"] == [1, 2, 3]


def test_deep_merge_validation() -> None:
    """Проверка валидации параметров deep_merge."""
    with pytest.raises(ValueError):
        deep_merge({"a": 1}, {"b": 2}, list_strategy="invalid")

    with pytest.raises(TypeError):
        deep_merge({"a": 1}, [1, 2, 3])  # type: ignore[arg-type]


def test_deep_patch_rfc_7396() -> None:
    """Проверка применения патчей deep_patch."""
    target = {
        "title": "Old Title",
        "description": "To be removed",
        "settings": {
            "mode": "dark",
            "volume": 80,
        },
    }

    patch = {
        "title": "New Title",
        "description": DELETE_FIELD,
        "author": "Denis",
        "settings": {
            "volume": 100,
        },
    }

    patched = deep_patch(target, patch)
    expected = {
        "title": "New Title",
        "author": "Denis",
        "settings": {
            "mode": "dark",
            "volume": 100,
        },
    }
    assert patched == expected
    assert "description" not in patched


def test_deep_patch_custom_delete_marker() -> None:
    """Проверка использования None как маркера удаления в стиле JSON Merge Patch."""
    target = {"a": 1, "b": 2}
    patch = {"b": None, "c": 3}

    patched = deep_patch(target, patch, delete_marker=None)
    assert patched == {"a": 1, "c": 3}
