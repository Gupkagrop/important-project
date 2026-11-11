"""Модульные тесты для модуля индикатора прогресса (progress)."""

import pytest

from pocket_toolkit.cli.progress import ProgressBar, track_progress


def test_progress_bar_render_and_percentage() -> None:
    """Проверка отрисовки шкалы прогресса и расчета процентов."""
    pb = ProgressBar(total=100, width=10, fill_char="#", empty_char="-", description="Loading", show_eta=False)
    assert "Loading:" in pb.render()
    assert "|----------|" in pb.render()
    assert "0.0%" in pb.render()
    assert not pb.is_finished

    pb.update(50)
    assert pb.percentage == 50.0
    assert "|#####-----|" in pb.render()
    assert "50.0%" in pb.render()
    assert "[50/100]" in pb.render()

    pb.update(50)
    assert pb.percentage == 100.0
    assert pb.is_finished
    assert "|##########|" in pb.render()


def test_progress_bar_set_progress_bounds() -> None:
    """Проверка установки прогресса и защиты от выхода за границы [0, total]."""
    pb = ProgressBar(total=50)
    pb.set_progress(25)
    assert pb.current == 25.0

    # Превышение лимита
    pb.set_progress(100)
    assert pb.current == 50.0
    assert pb.is_finished

    # Отрицательное значение
    pb.set_progress(-10)
    assert pb.current == 0.0


def test_progress_bar_context_manager() -> None:
    """Проверка работы контекстного менеджера."""
    with ProgressBar(total=20) as pb:
        pb.update(5)
        assert pb.current == 5.0
    assert pb.is_finished
    assert pb.current == 20.0


def test_track_progress_generator() -> None:
    """Проверка вспомогательного генератора track_progress."""
    data = [10, 20, 30]
    consumed = list(track_progress(data, description="Iterating"))
    assert consumed == [10, 20, 30]


def test_progress_bar_validation_errors() -> None:
    """Проверка валидации некорректных параметров шкалы."""
    with pytest.raises(ValueError, match="total должен быть строго положительным"):
        ProgressBar(total=0)

    with pytest.raises(ValueError, match="total должен быть строго положительным"):
        ProgressBar(total=-10)

    with pytest.raises(ValueError, match="width должен быть строго положительным"):
        ProgressBar(total=10, width=0)
