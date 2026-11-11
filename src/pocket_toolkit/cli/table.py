"""Модуль форматирования двумерных таблиц для CLI (CLI Table Formatter).

Предоставляет класс Table и функцию format_table для выравнивания и отрисовки
таблиц в стилях ASCII, Unicode и Markdown с автоподбором ширины колонок и учетом ANSI-кодов.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from pocket_toolkit.cli.colors import strip_ansi


@dataclass(frozen=True, slots=True)
class TableBorderStyle:
    """Символы границ и разделителей таблицы."""

    top_left: str
    top_mid: str
    top_right: str
    mid_left: str
    mid_mid: str
    mid_right: str
    bot_left: str
    bot_mid: str
    bot_right: str
    horiz: str
    vert: str


# Предустановленные стили оформления границ
_STYLES: dict[str, TableBorderStyle] = {
    "unicode": TableBorderStyle(
        top_left="┌",
        top_mid="┬",
        top_right="┐",
        mid_left="├",
        mid_mid="┼",
        mid_right="┤",
        bot_left="└",
        bot_mid="┴",
        bot_right="┘",
        horiz="─",
        vert="│",
    ),
    "ascii": TableBorderStyle(
        top_left="+",
        top_mid="+",
        top_right="+",
        mid_left="+",
        mid_mid="+",
        mid_right="+",
        bot_left="+",
        bot_mid="+",
        bot_right="+",
        horiz="-",
        vert="|",
    ),
    "markdown": TableBorderStyle(
        top_left="",
        top_mid="",
        top_right="",
        mid_left="|",
        mid_mid="|",
        mid_right="|",
        bot_left="",
        bot_mid="",
        bot_right="",
        horiz="-",
        vert="|",
    ),
}


def _visible_length(text: str) -> int:
    """Возвращает видимую длину текста без учета ANSI-кодов."""
    return len(strip_ansi(text))


def _pad_cell(text: str, width: int, align: str) -> str:
    """Дополняет ячейку пробелами с учетом выравнивания и видимой длины."""
    vis_len = _visible_length(text)
    pad = max(0, width - vis_len)

    if align == "right":
        return f"{' ' * pad}{text}"
    if align == "center":
        left = pad // 2
        right = pad - left
        return f"{' ' * left}{text}{' ' * right}"
    return f"{text}{' ' * pad}"


class Table:
    """Конструктор и визуализатор табличных данных для терминала."""

    def __init__(
        self,
        headers: Sequence[str] | None = None,
        style: str = "unicode",
    ) -> None:
        """Инициализирует таблицу с заголовками и выбранным стилем границ."""
        if style not in _STYLES:
            raise ValueError(f"Неизвестный стиль таблицы: {style!r}. Допустимы: {list(_STYLES.keys())}")

        self._headers: list[str] = list(headers) if headers is not None else []
        self._rows: list[list[str]] = []
        self._style_name: str = style
        self._alignments: dict[int, str] = {}

    def add_row(self, *cells: object) -> None:
        """Добавляет одну строку в таблицу."""
        self._rows.append([str(c) for c in cells])

    def add_rows(self, rows: Iterable[Iterable[object]]) -> None:
        """Добавляет коллекцию строк."""
        for row in rows:
            self._rows.append([str(c) for c in row])

    def set_column_align(self, col_index: int, align: str) -> None:
        """Устанавливает выравнивание для колонки ('left', 'center', 'right')."""
        if align not in ("left", "center", "right"):
            raise ValueError(f"Недопустимое выравнивание: {align!r}")
        self._alignments[col_index] = align

    def _calculate_widths(self, num_cols: int) -> list[int]:
        """Вычисляет максимальную видимую ширину для каждой колонки."""
        widths = [0] * num_cols

        for idx, h in enumerate(self._headers):
            if idx < num_cols:
                widths[idx] = max(widths[idx], _visible_length(h))

        for row in self._rows:
            for idx, cell in enumerate(row):
                if idx < num_cols:
                    widths[idx] = max(widths[idx], _visible_length(cell))

        return [max(w, 1) for w in widths]

    def _format_row_line(self, cells: list[str], widths: list[int], border: TableBorderStyle) -> str:
        """Форматирует строку данных таблицы."""
        padded_cells: list[str] = []
        for idx, w in enumerate(widths):
            val = cells[idx] if idx < len(cells) else ""
            align = self._alignments.get(idx, "left")
            padded_cells.append(f" {_pad_cell(val, w, align)} ")

        vert = border.vert
        if self._style_name == "markdown":
            return f"|{'|'.join(padded_cells)}|"
        return f"{vert}{vert.join(padded_cells)}{vert}"

    def _format_border_line(
        self,
        widths: list[int],
        left: str,
        mid: str,
        right: str,
        horiz: str,
    ) -> str:
        """Форматирует разделительную горизонтальную линию таблицы."""
        segments = [horiz * (w + 2) for w in widths]
        return f"{left}{mid.join(segments)}{right}"

    def render(self) -> str:
        """Отрисовывает таблицу в итоговую строку."""
        num_cols = max([len(self._headers)] + [len(r) for r in self._rows] or [0])
        if num_cols == 0:
            return ""

        widths = self._calculate_widths(num_cols)
        border = _STYLES[self._style_name]
        lines: list[str] = []

        if border.top_left and border.top_right:
            lines.append(self._format_border_line(widths, border.top_left, border.top_mid, border.top_right, border.horiz))

        if self._headers:
            lines.append(self._format_row_line(self._headers, widths, border))
            lines.append(self._format_border_line(widths, border.mid_left, border.mid_mid, border.mid_right, border.horiz))

        for row in self._rows:
            lines.append(self._format_row_line(row, widths, border))

        if border.bot_left and border.bot_right:
            lines.append(self._format_border_line(widths, border.bot_left, border.bot_mid, border.bot_right, border.horiz))

        return "\n".join(lines)

    def __str__(self) -> str:
        """Строковое представление таблицы."""
        return self.render()


def format_table(
    rows: Iterable[Iterable[object]],
    headers: Sequence[str] | None = None,
    style: str = "unicode",
    alignments: Sequence[str] | None = None,
) -> str:
    """Удобная функция быстрого форматирования таблицы.

    :param rows: Последовательность строк таблицы.
    :param headers: Заголовки колонок.
    :param style: Стиль границ ('unicode', 'ascii', 'markdown').
    :param alignments: Выравнивание колонок (например, ['left', 'right']).
    :return: Отрендеренная текстовая таблица.
    """
    tbl = Table(headers=headers, style=style)
    if alignments:
        for idx, align in enumerate(alignments):
            tbl.set_column_align(idx, align)
    tbl.add_rows(rows)
    return tbl.render()
