"""Модульные тесты для модуля поиска различий и дельты словарей (diff)."""

import pytest

from pocket_toolkit.data.diff import DictDiff, diff_dict, find_dict_delta


def test_dict_diff_identical() -> None:
    """Проверка сравнения идентичных словарей."""
    data = {"a": 1, "nested": {"b": 2}}
    diff = diff_dict(data, data)

    assert isinstance(diff, DictDiff)
    assert not diff.has_changes
    assert diff.added == {}
    assert diff.removed == {}
    assert diff.changed == {}
    assert "a" in diff.unchanged
    assert "nested.b" in diff.unchanged


def test_dict_diff_added_and_removed() -> None:
    """Проверка фиксации добавленных и удаленных ключей."""
    first = {"a": 1, "b": 2}
    second = {"b": 2, "c": 3}

    diff = diff_dict(first, second)
    assert diff.has_changes
    assert diff.removed == {"a": 1}
    assert diff.added == {"c": 3}
    assert diff.changed == {}
    assert diff.unchanged == {"b": 2}


def test_dict_diff_changed_values() -> None:
    """Проверка фиксации измененных скалярных значений."""
    first = {"status": "pending", "count": 10}
    second = {"status": "active", "count": 10}

    diff = diff_dict(first, second)
    assert diff.has_changes
    assert diff.changed == {"status": ("pending", "active")}
    assert diff.unchanged == {"count": 10}


def test_dict_diff_nested_recursive() -> None:
    """Проверка рекурсивного сравнения глубоко вложенных словарей."""
    first = {
        "server": {
            "host": "localhost",
            "port": 8080,
            "ssl": {"enabled": False},
        }
    }
    second = {
        "server": {
            "host": "example.com",
            "port": 8080,
            "ssl": {"enabled": True, "cert": "cert.pem"},
        }
    }

    diff = diff_dict(first, second, recursive=True, path_separator="/")
    assert diff.has_changes
    assert diff.changed == {
        "server/host": ("localhost", "example.com"),
        "server/ssl/enabled": (False, True),
    }
    assert diff.added == {"server/ssl/cert": "cert.pem"}
    assert diff.unchanged == {"server/port": 8080}


def test_dict_diff_non_recursive() -> None:
    """Проверка нерекурсивного поверхностного сравнения."""
    first = {"meta": {"version": 1}}
    second = {"meta": {"version": 2}}

    diff = diff_dict(first, second, recursive=False)
    assert diff.has_changes
    assert diff.changed == {"meta": ({"version": 1}, {"version": 2})}


def test_dict_diff_to_dict() -> None:
    """Проверка сериализации отчета в словарь через to_dict()."""
    first = {"x": 1, "y": 2}
    second = {"x": 10, "z": 3}

    diff = diff_dict(first, second)
    dumped = diff.to_dict()

    assert dumped["added"] == {"z": 3}
    assert dumped["removed"] == {"y": 2}
    assert dumped["changed"] == {"x": {"old": 1, "new": 10}}
    assert dumped["unchanged"] == {}


def test_dict_diff_invalid_inputs() -> None:
    """Проверка валидации некорректных аргументов."""
    with pytest.raises(TypeError):
        diff_dict([1, 2], {"a": 1})  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        diff_dict({"a": 1}, "not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        diff_dict({"a": 1}, {"b": 2}, path_separator="")


def test_find_dict_delta() -> None:
    """Проверка вычисления дельты (merge-patch совместимый формат)."""
    base = {
        "name": "Service",
        "env": "staging",
        "replicas": 2,
        "logging": {"level": "INFO", "structured": False},
    }
    target = {
        "name": "Service",
        "env": "production",
        # replicas удален
        "logging": {"level": "DEBUG", "structured": False},
        "tracing": True,
    }

    delta = find_dict_delta(base, target)
    expected = {
        "replicas": None,
        "env": "production",
        "logging": {"level": "DEBUG"},
        "tracing": True,
    }
    assert delta == expected


def test_find_dict_delta_empty_and_identical() -> None:
    """Проверка дельты для совпадающих или пустых структур."""
    assert find_dict_delta({}, {}) == {}
    assert find_dict_delta({"a": 1}, {"a": 1}) == {}
