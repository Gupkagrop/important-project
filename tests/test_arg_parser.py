"""Модульные тесты для модуля парсера аргументов командной строки (arg_parser)."""

import pytest

from pocket_toolkit.cli.arg_parser import ArgumentError, ArgumentParser, Namespace


def test_argument_parser_positionals() -> None:
    """Проверка обработки позиционных аргументов и приведения типов."""
    parser = ArgumentParser(description="File Processor")
    parser.add_argument("source", help="Исходный файл")
    parser.add_argument("count", type=int, default=1, help="Количество копий")

    args = parser.parse_args(["input.txt", "5"])
    assert args.source == "input.txt"
    assert args.count == 5
    assert args["source"] == "input.txt"


def test_argument_parser_flags_and_options() -> None:
    """Проверка флагов, длинных и коротких опций со значениями."""
    parser = ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--port", "-p", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")

    # Передача через пробел и через знак =
    args = parser.parse_args(["-v", "--port=9090", "--host", "0.0.0.0"])
    assert args.verbose is True
    assert args.port == 9090
    assert args.host == "0.0.0.0"


def test_argument_parser_flag_bundling() -> None:
    """Проверка объединения коротких флагов (-abc)."""
    parser = ArgumentParser()
    parser.add_argument("-a", action="store_true")
    parser.add_argument("-b", action="store_true")
    parser.add_argument("-c", action="store_true")

    args = parser.parse_args(["-abc"])
    assert args.a is True
    assert args.b is True
    assert args.c is True


def test_argument_parser_append_action() -> None:
    """Проверка накопления нескольких значений в список (action='append')."""
    parser = ArgumentParser()
    parser.add_argument("--tag", "-t", action="append")

    args = parser.parse_args(["-t", "python", "--tag=cli", "-t", "toolkit"])
    assert args.tag == ["python", "cli", "toolkit"]


def test_argument_parser_dash_dash_separator() -> None:
    """Проверка разделителя '--' для принудительной трактовки параметров как позиционных."""
    parser = ArgumentParser()
    parser.add_argument("filename")

    args = parser.parse_args(["--", "-not-a-flag.txt"])
    assert args.filename == "-not-a-flag.txt"


def test_argument_parser_format_help() -> None:
    """Проверка формирования текста справки."""
    parser = ArgumentParser(description="CLI Tool Test", prog="mycli")
    parser.add_argument("--config", "-c", help="Путь к конфигу", default="config.yaml")

    help_text = parser.format_help()
    assert "CLI Tool Test" in help_text
    assert "Использование: mycli" in help_text
    assert "--config, -c" in help_text
    assert "по умолчанию: config.yaml" in help_text


def test_argument_parser_errors() -> None:
    """Проверка генерации исключений ArgumentError при ошибках ввода."""
    parser = ArgumentParser()
    parser.add_argument("req_pos", required=True)
    parser.add_argument("--number", type=int)

    with pytest.raises(ArgumentError, match="Не переданы все обязательные позиционные"):
        parser.parse_args([])

    with pytest.raises(ArgumentError, match="Ошибка типа"):
        parser.parse_args(["file.txt", "--number", "not-a-number"])

    with pytest.raises(ArgumentError, match="Для параметра --number ожидалось значение"):
        parser.parse_args(["file.txt", "--number"])

    with pytest.raises(ArgumentError, match="Неизвестный параметр"):
        parser.parse_args(["file.txt", "--unknown-opt"])


def test_namespace_container() -> None:
    """Проверка функциональности объекта Namespace."""
    ns = Namespace(name="test", count=42)
    assert ns.as_dict() == {"name": "test", "count": 42}
    assert "name" in ns
    assert repr(ns) == "Namespace(name='test', count=42)"

    with pytest.raises(AttributeError):
        _ = ns.nonexistent
