"""Модульные тесты для модуля форматирования CLI таблиц (table)."""

import pytest

from pocket_toolkit.cli.colors import red, set_colors_enabled
from pocket_toolkit.cli.table import Table, format_table


def test_table_unicode_basic() -> None:
    """Проверка базового рендеринга Unicode таблицы с рамками."""
    tbl = Table(headers=["ID", "Name", "Role"])
    tbl.add_row(1, "Denis", "Developer")
    tbl.add_row(2, "Alice", "Lead")

    rendered = tbl.render()
    assert "┌" in rendered and "┐" in rendered
    assert "│ ID │ Name  │ Role      │" in rendered
    assert "│ 1  │ Denis │ Developer │" in rendered
    assert "└" in rendered and "┘" in rendered


def test_table_ascii_style() -> None:
    """Проверка рендеринга в ASCII стиле."""
    headers = ["Task", "Status"]
    rows = [["Test", "Pass"], ["Lint", "OK"]]
    rendered = format_table(rows, headers=headers, style="ascii")

    assert "+------+--------+" in rendered
    assert "| Task | Status |" in rendered
    assert "| Test | Pass   |" in rendered


def test_table_markdown_style() -> None:
    """Проверка вывода в стиле Markdown таблицы."""
    headers = ["Metric", "Value"]
    rows = [["CPU", "15%"], ["RAM", "4.2 GB"]]
    rendered = format_table(rows, headers=headers, style="markdown")

    assert "| Metric | Value  |" in rendered
    assert "|--------|--------|" in rendered
    assert "| CPU    | 15%    |" in rendered


def test_table_alignments() -> None:
    """Проверка различных режимов выравнивания ячеек."""
    tbl = Table(headers=["Left", "Center", "Right"])
    tbl.set_column_align(0, "left")
    tbl.set_column_align(1, "center")
    tbl.set_column_align(2, "right")
    tbl.add_row("A", "B", "C")

    rendered = tbl.render()
    # Колонка 2 должна быть выровнена по правому краю
    assert "│ A    │   B    │     C │" in rendered


def test_table_with_ansi_colors() -> None:
    """Проверка корректного вычисления ширины колонок при наличии ANSI-кодов."""
    set_colors_enabled(True)
    try:
        colored_text = red("FAIL")
        tbl = Table(headers=["Service", "Status"])
        tbl.add_row("API", colored_text)
        tbl.add_row("Worker", "OK")

        rendered = tbl.render()
        # Длина "FAIL" без ANSI равна 4 символам.
        assert "│ Service │ Status │" in rendered
    finally:
        set_colors_enabled(None)


def test_table_empty() -> None:
    """Проверка рендеринга пустой таблицы."""
    assert Table().render() == ""
    assert format_table([]) == ""


def test_table_validation_errors() -> None:
    """Проверка обработки некорректных стилей и настроек."""
    with pytest.raises(ValueError, match="Неизвестный стиль таблицы"):
        Table(style="unsupported")

    tbl = Table()
    with pytest.raises(ValueError, match="Недопустимое выравнивание"):
        tbl.set_column_align(0, "diagonal")
