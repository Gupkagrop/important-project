"""Модульные тесты для декоратора профилирования profile_time."""

import pytest
from pocket_toolkit.decorators.profiler import ProfileStats, profile_time


class MockClock:
    """Имитатор таймера высокой точности."""

    def __init__(self) -> None:
        self.time: float = 0.0

    def now(self) -> float:
        return self.time

    def advance(self, delta: float) -> None:
        self.time += delta


def test_profile_time_stats() -> None:
    """Проверка сбора агрегированной статистики времени выполнения."""
    clock = MockClock()
    logs: list[str] = []

    @profile_time(logger=logs.append, label="test_job", time_func=clock.now)
    def task(duration: float) -> str:
        clock.advance(duration)
        return "done"

    assert task(0.1) == "done"
    assert task(0.3) == "done"

    stats: ProfileStats = task.get_stats()
    assert stats.total_calls == 2
    assert stats.total_time == pytest.approx(0.4)
    assert stats.min_time == pytest.approx(0.1)
    assert stats.max_time == pytest.approx(0.3)
    assert stats.mean_time == pytest.approx(0.2)

    assert len(logs) == 2
    assert "[test_job]" in logs[0]
    assert "[test_job]" in logs[1]


def test_profile_time_reset() -> None:
    """Проверка сброса статистики методом reset_stats()."""
    clock = MockClock()

    @profile_time(time_func=clock.now)
    def run() -> None:
        clock.advance(1.0)

    run()
    assert run.get_stats().total_calls == 1
    run.reset_stats()
    empty = run.get_stats()
    assert empty.total_calls == 0
    assert empty.total_time == 0.0
    assert empty.mean_time == 0.0


def test_profile_time_records_exceptions() -> None:
    """Проверка учета времени даже при возникновении исключения."""
    clock = MockClock()

    @profile_time(time_func=clock.now)
    def crash() -> None:
        clock.advance(0.5)
        raise RuntimeError("failed")

    with pytest.raises(RuntimeError):
        crash()

    stats = crash.get_stats()
    assert stats.total_calls == 1
    assert stats.total_time == pytest.approx(0.5)
