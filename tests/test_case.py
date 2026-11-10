"""Модульные тесты для модуля конвертеров регистра строк (case)."""

from pocket_toolkit.strings.case import (
    split_words,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_screaming_snake_case,
    to_snake_case,
    to_title_case,
)


def test_split_words_various_styles() -> None:
    """Проверка разбиения строки на слова в разных стилях."""
    assert split_words("") == []
    assert split_words("   ") == []
    assert split_words("simple") == ["simple"]
    assert split_words("camelCaseString") == ["camel", "Case", "String"]
    assert split_words("PascalCaseString") == ["Pascal", "Case", "String"]
    assert split_words("snake_case_string") == ["snake", "case", "string"]
    assert split_words("kebab-case-string") == ["kebab", "case", "string"]
    assert split_words("parseHTTPResponse") == ["parse", "HTTP", "Response"]
    assert split_words("get2Words") == ["get", "2", "Words"]


def test_case_conversions() -> None:
    """Проверка всех конвертаций для стандартного выражения."""
    source = "helloWorldExample"

    assert to_snake_case(source) == "hello_world_example"
    assert to_camel_case(source) == "helloWorldExample"
    assert to_pascal_case(source) == "HelloWorldExample"
    assert to_kebab_case(source) == "hello-world-example"
    assert to_screaming_snake_case(source) == "HELLO_WORLD_EXAMPLE"
    assert to_title_case(source) == "Hello World Example"


def test_acronym_handling() -> None:
    """Проверка корректной обработки акронимов (HTTP, JSON, API)."""
    assert to_snake_case("getHTTPResponse") == "get_http_response"
    assert to_pascal_case("json_api_parser") == "JsonApiParser"
    assert to_kebab_case("parseXMLDocument") == "parse-xml-document"
    assert to_camel_case("MAKE_API_CALL") == "makeApiCall"


def test_mixed_delimiters_and_spaces() -> None:
    """Проверка работы со смешанными разделителями и пробелами."""
    raw = "  mix_of - various.delimiters/and words "
    assert to_snake_case(raw) == "mix_of_various_delimiters_and_words"
    assert to_kebab_case(raw) == "mix-of-various-delimiters-and-words"
    assert to_pascal_case(raw) == "MixOfVariousDelimitersAndWords"


def test_empty_string_conversions() -> None:
    """Проверка граничного случая пустой строки."""
    assert to_snake_case("") == ""
    assert to_camel_case("") == ""
    assert to_pascal_case("") == ""
    assert to_kebab_case("") == ""
    assert to_screaming_snake_case("") == ""
    assert to_title_case("") == ""
