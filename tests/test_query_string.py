"""Модульные тесты для модуля парсинга и сборки query-параметров URL (query_string)."""

import pytest

from pocket_toolkit.strings.query_string import (
    QueryParams,
    build_query,
    parse_query,
)


def test_parse_query_basic() -> None:
    """Проверка базового парсинга строки запроса."""
    qs = "?name=Denis&age=25&active=true"
    parsed = parse_query(qs)
    assert parsed == {
        "name": "Denis",
        "age": "25",
        "active": "true",
    }


def test_parse_query_repeated_keys_and_encoding() -> None:
    """Проверка повторяющихся параметров и декодирования процентов."""
    qs = "tag=python&tag=async&city=%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0"
    parsed = parse_query(qs)
    assert parsed["tag"] == ["python", "async"]
    assert parsed["city"] == "Москва"


def test_parse_query_empty_and_blank() -> None:
    """Проверка пустых параметров и пустой строки."""
    assert parse_query("") == {}
    assert parse_query("?") == {}
    assert parse_query("key=&foo=bar", keep_blank_values=True) == {"key": "", "foo": "bar"}
    assert parse_query("key=&foo=bar", keep_blank_values=False) == {"foo": "bar"}


def test_build_query_basic_and_lists() -> None:
    """Проверка формирования query-строки с кодированием и списками."""
    params = {
        "search": "код и тесты",
        "filter": ["open", "pending"],
        "unused": None,
    }
    built = build_query(params, sort_keys=True)
    assert "search=%D0%BA%D0%BE%D0%B4+%D0%B8+%D1%82%D0%B5%D1%81%D1%82%D1%8B" in built
    assert "filter=open&filter=pending" in built
    assert "unused" not in built


def test_query_params_class_operations() -> None:
    """Проверка функциональности класса QueryParams."""
    qp = QueryParams("user=admin&role=editor")
    assert "user" in qp
    assert len(qp) == 2
    assert qp.get("user") == "admin"
    assert qp.get("missing", default="guest") == "guest"

    # Добавление и перезапись
    qp.add("role", "viewer")
    assert qp.get_all("role") == ["editor", "viewer"]

    qp.set("status", "active")
    assert qp.get("status") == "active"

    qp.remove("user")
    assert "user" not in qp

    # Сериализация
    dumped = qp.to_dict()
    assert dumped["role"] == ["editor", "viewer"]
    assert dumped["status"] == "active"

    encoded = qp.to_query_string(sort_keys=True)
    assert "role=editor&role=viewer" in encoded
    assert "status=active" in encoded
    assert str(qp) == qp.to_query_string()


def test_validation_errors() -> None:
    """Проверка валидации входных типов."""
    with pytest.raises(TypeError):
        parse_query(12345)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        build_query("not-a-mapping")  # type: ignore[arg-type]
