"""Модульные тесты для модуля потокового CSV (csv_stream)."""

import pytest

from pocket_toolkit.data.csv_stream import (
    CSVParseError,
    generate_csv_from_dicts,
    generate_csv_line,
    generate_csv_stream,
    parse_csv_dicts,
    parse_csv_stream,
)


def test_generate_csv_line() -> None:
    """Проверка генерации строки CSV и экранирования спецсимволов."""
    row = ["Denis", 30, "Moscow, Russia", 'Quote "Test"']
    line = generate_csv_line(row)
    assert line == 'Denis,30,"Moscow, Russia","Quote ""Test"""\r\n'


def test_generate_csv_stream() -> None:
    """Проверка генерации потока строк CSV."""
    rows = [
        ["id", "name"],
        [1, "Alice"],
        [2, "Bob"],
    ]
    stream = list(generate_csv_stream(rows))
    assert len(stream) == 3
    assert stream[0] == "id,name\r\n"
    assert stream[1] == "1,Alice\r\n"
    assert stream[2] == "2,Bob\r\n"


def test_generate_csv_from_dicts() -> None:
    """Проверка генерации CSV из словарей."""
    records = [
        {"id": 1, "title": "First", "extra": "A"},
        {"id": 2, "title": "Second", "extra": "B"},
    ]
    output = "".join(generate_csv_from_dicts(records, fieldnames=["id", "title"]))
    assert output == "id,title\r\n1,First\r\n2,Second\r\n"


def test_parse_csv_stream_basic_and_quotes() -> None:
    """Проверка парсинга потока строк, включая кавычки и запятые."""
    raw_csv = (
        'name,age,city\n'
        'Denis,25,"Saint Petersburg, Russia"\n'
        'Anna,30,"She said ""Hello"""\n'
    )
    rows = list(parse_csv_stream([raw_csv]))
    assert len(rows) == 3
    assert rows[0] == ["name", "age", "city"]
    assert rows[1] == ["Denis", "25", "Saint Petersburg, Russia"]
    assert rows[2] == ["Anna", "30", 'She said "Hello"']


def test_parse_csv_multiline_field() -> None:
    """Проверка парсинга многострочного поля внутри кавычек."""
    raw_csv = 'id,comment\n1,"Line 1\nLine 2"\n2,Done\n'
    rows = list(parse_csv_stream([raw_csv]))
    assert len(rows) == 3
    assert rows[0] == ["id", "comment"]
    assert rows[1] == ["1", "Line 1\nLine 2"]
    assert rows[2] == ["2", "Done"]


def test_parse_csv_dicts() -> None:
    """Проверка преобразования строк CSV в словари."""
    lines = ["name,role\n", "Alice,Developer\n", "Bob,Manager\n"]
    records = list(parse_csv_dicts(lines))
    assert len(records) == 2
    assert records[0] == {"name": "Alice", "role": "Developer"}
    assert records[1] == {"name": "Bob", "role": "Manager"}


def test_parse_csv_unclosed_quotes_error() -> None:
    """Проверка ошибки незакрытых кавычек в потоке."""
    bad_csv = ['id,text\n', '1,"Незакрытая кавычка']
    with pytest.raises(CSVParseError, match="Неожиданный конец потока"):
        list(parse_csv_stream(bad_csv))


def test_csv_validation_errors() -> None:
    """Проверка валидации некорректных типов."""
    with pytest.raises(TypeError):
        generate_csv_line("not-a-sequence-of-columns")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        list(generate_csv_from_dicts(["not-a-dict"]))  # type: ignore[arg-type]
