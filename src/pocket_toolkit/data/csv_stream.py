"""Модуль потокового парсинга и генерации CSV данных (Streaming CSV).

Предоставляет функции parse_csv_stream, parse_csv_dicts для потокового разбора строк
с поддержкой кавычек, экранирования и многострочных полей, а также generate_csv_stream
и generate_csv_from_dicts для потокового формирования CSV.
"""

import io
from collections.abc import Iterable, Iterator, Mapping


class CSVParseError(Exception):
    """Исключение при ошибке синтаксического разбора CSV."""


def _escape_csv_field(field_val: object, delimiter: str, quotechar: str) -> str:
    """Форматирует и при необходимости экранирует отдельное поле CSV."""
    s = "" if field_val is None else str(field_val)
    need_quote = delimiter in s or quotechar in s or "\n" in s or "\r" in s

    if not need_quote:
        return s

    escaped = s.replace(quotechar, quotechar + quotechar)
    return f"{quotechar}{escaped}{quotechar}"


def generate_csv_line(
    row: Iterable[object],
    delimiter: str = ",",
    quotechar: str = '"',
) -> str:
    """Генерирует одну строку CSV из последовательности значений.

    :param row: Коллекция значений колонок.
    :param delimiter: Символ-разделитель (по умолчанию ',').
    :param quotechar: Символ обрамления (по умолчанию '"').
    :return: Сформированная строка с переводом строки '\r\n'.
    """
    if not isinstance(row, Iterable) or isinstance(row, (str, bytes)):
        raise TypeError(f"Строка данных должна быть итерируемым объектом, получено: {type(row).__name__}")

    fields = [_escape_csv_field(val, delimiter, quotechar) for val in row]
    return f"{delimiter.join(fields)}\r\n"


def generate_csv_stream(
    rows: Iterable[Iterable[object]],
    delimiter: str = ",",
    quotechar: str = '"',
) -> Iterator[str]:
    """Генерирует поток строк CSV."""
    for row in rows:
        yield generate_csv_line(row, delimiter=delimiter, quotechar=quotechar)


def generate_csv_from_dicts(
    records: Iterable[Mapping[str, object]],
    fieldnames: list[str] | None = None,
    delimiter: str = ",",
    quotechar: str = '"',
) -> Iterator[str]:
    """Генерирует поток CSV из последовательности словарей с опциональным заголовком."""
    headers = list(fieldnames) if fieldnames is not None else None
    first_record = True

    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError(f"Каждая запись должна быть Mapping, получено: {type(record).__name__}")

        if first_record and headers is None:
            headers = list(record.keys())
            yield generate_csv_line(headers, delimiter=delimiter, quotechar=quotechar)
            first_record = False
        elif first_record and headers is not None:
            yield generate_csv_line(headers, delimiter=delimiter, quotechar=quotechar)
            first_record = False

        row_values = [record.get(col, "") for col in (headers or [])]
        yield generate_csv_line(row_values, delimiter=delimiter, quotechar=quotechar)


def _parse_csv_row_from_reader(
    stream: io.StringIO,
    delimiter: str,
    quotechar: str,
) -> list[str] | None:
    """Парсит одну логическую строку (с учетом переносов строк внутри кавычек)."""
    fields: list[str] = []
    current_chars: list[str] = []
    inside_quotes = False
    has_read_any = False

    while True:
        ch = stream.read(1)
        if not ch:
            if inside_quotes:
                raise CSVParseError("Неожиданный конец потока внутри открытых кавычек")
            if not has_read_any and not fields and not current_chars:
                return None
            fields.append("".join(current_chars))
            return fields

        has_read_any = True

        if ch == quotechar:
            if inside_quotes:
                # Проверяем, экранирована ли кавычка
                next_ch = stream.read(1)
                if next_ch == quotechar:
                    current_chars.append(quotechar)
                else:
                    inside_quotes = False
                    if next_ch:
                        stream.seek(stream.tell() - 1)
            else:
                inside_quotes = True
            continue

        if not inside_quotes:
            if ch == delimiter:
                fields.append("".join(current_chars))
                current_chars = []
                continue
            if ch == "\r":
                next_ch = stream.read(1)
                if next_ch != "\n" and next_ch:
                    stream.seek(stream.tell() - 1)
                fields.append("".join(current_chars))
                return fields
            if ch == "\n":
                fields.append("".join(current_chars))
                return fields

        current_chars.append(ch)


def parse_csv_stream(
    lines: Iterable[str],
    delimiter: str = ",",
    quotechar: str = '"',
    skip_header: bool = False,
) -> Iterator[list[str]]:
    """Потоково разбирает итерируемый источник строк в списки колонок.

    :param lines: Поток строк (например, файл или список строк).
    :param delimiter: Разделитель колонок.
    :param quotechar: Символ обрамления.
    :param skip_header: Пропускать ли первую строку заголовка.
    :return: Итератор списков значений колонок.
    """
    buffer = io.StringIO("".join(lines))
    is_first = True

    while True:
        row = _parse_csv_row_from_reader(buffer, delimiter, quotechar)
        if row is None:
            break
        if is_first and skip_header:
            is_first = False
            continue
        is_first = False
        yield row


def parse_csv_dicts(
    lines: Iterable[str],
    delimiter: str = ",",
    quotechar: str = '"',
) -> Iterator[dict[str, str]]:
    """Потоково разбирает CSV в словари, используя первую строку в качестве ключей."""
    stream = parse_csv_stream(lines, delimiter=delimiter, quotechar=quotechar)
    try:
        headers = next(stream)
    except StopIteration:
        return

    for row in stream:
        record: dict[str, str] = {}
        for idx, col_name in enumerate(headers):
            record[col_name] = row[idx] if idx < len(row) else ""
        yield record
