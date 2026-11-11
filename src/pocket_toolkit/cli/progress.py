"""Модуль текстового индикатора выполнения (Text Progress Bar).

Предоставляет класс ProgressBar и генератор track_progress для визуализации
прогресса операций в терминале с отображением шкалы, процентов, скорости и оценки оставшегося времени (ETA).
"""

import time
from collections.abc import Iterable, Iterator
from typing import Self


def _format_time_compact(seconds: float) -> str:
    """Форматирует секунды в компактный вид 'ММ:СС' или 'ЧЧ:ММ:СС'."""
    sec = max(0, round(seconds))
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class ProgressBar:
    """Текстовый индикатор прогресса для консольных задач."""

    def __init__(
        self,
        total: float,
        width: int = 25,
        fill_char: str = "█",
        empty_char: str = "░",
        description: str = "",
        show_percent: bool = True,
        show_eta: bool = True,
    ) -> None:
        """Инициализирует индикатор прогресса."""
        if total <= 0:
            raise ValueError(f"total должен быть строго положительным, получено: {total}")
        if width <= 0:
            raise ValueError(f"width должен быть строго положительным, получено: {width}")

        self.total: float = float(total)
        self.current: float = 0.0
        self.width: int = width
        self.fill_char: str = fill_char
        self.empty_char: str = empty_char
        self.description: str = description
        self.show_percent: bool = show_percent
        self.show_eta: bool = show_eta

        self._start_time: float = time.monotonic()
        self._last_update_time: float = self._start_time

    @property
    def percentage(self) -> float:
        """Текущий процент выполнения (от 0.0 до 100.0)."""
        ratio = min(max(self.current / self.total, 0.0), 1.0)
        return ratio * 100.0

    @property
    def is_finished(self) -> bool:
        """Возвращает True, если задача завершена."""
        return self.current >= self.total

    def update(self, advance: float = 1) -> None:
        """Увеличивает текущий прогресс на advance единиц."""
        self.current = min(self.total, max(0.0, self.current + float(advance)))
        self._last_update_time = time.monotonic()

    def set_progress(self, current: float) -> None:
        """Устанавливает абсолютное значение прогресса."""
        self.current = min(self.total, max(0.0, float(current)))
        self._last_update_time = time.monotonic()

    def _calculate_eta_and_rate(self) -> tuple[float, float]:
        """Вычисляет скорость выполнения (ед/сек) и оставшееся время (сек)."""
        elapsed = max(0.001, time.monotonic() - self._start_time)
        rate = self.current / elapsed
        if rate <= 0.0:
            return 0.0, 0.0

        remaining = max(0.0, self.total - self.current)
        eta = remaining / rate
        return rate, eta

    def render(self) -> str:
        """Формирует строковое представление текущего состояния шкалы прогресса."""
        ratio = min(max(self.current / self.total, 0.0), 1.0)
        filled_len = round(self.width * ratio)
        empty_len = self.width - filled_len

        bar = f"{self.fill_char * filled_len}{self.empty_char * empty_len}"
        parts: list[str] = []

        if self.description:
            parts.append(f"{self.description}:")

        parts.append(f"|{bar}|")

        if self.show_percent:
            parts.append(f"{self.percentage:5.1f}%")

        parts.append(f"[{int(self.current)}/{int(self.total)}]")

        if self.show_eta:
            rate, eta = self._calculate_eta_and_rate()
            rate_str = f"{rate:.1f}it/s" if rate >= 1.0 else f"{rate:.2f}it/s"
            parts.append(f"({rate_str}, ETA { _format_time_compact(eta)})")

        return " ".join(parts)

    def __enter__(self) -> Self:
        """Вход в контекстный менеджер."""
        self._start_time = time.monotonic()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Выход из контекстного менеджера."""
        self.current = self.total

    def __str__(self) -> str:
        """Строковое представление шкалы."""
        return self.render()


def track_progress[T](
    iterable: Iterable[T],
    total: int | None = None,
    description: str = "",
    width: int = 25,
) -> Iterator[T]:
    """Итератор с автоматическим обновлением шкалы прогресса для каждого элемента.

    :param iterable: Исходная коллекция или поток элементов.
    :param total: Общее количество элементов (если известно).
    :param description: Описание задачи.
    :param width: Ширина визуальной шкалы.
    :return: Потоковый генератор элементов.
    """
    if total is None and hasattr(iterable, "__len__"):
        total = len(iterable)  # type: ignore[arg-type]

    calc_total = total if total is not None and total > 0 else 1
    bar = ProgressBar(total=calc_total, width=width, description=description)

    for item in iterable:
        yield item
        bar.update(1)
