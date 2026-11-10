"""Модуль профилирования и замера времени выполнения функций (Profiler Decorator).

Предоставляет декоратор `@profile_time` и структуру `ProfileStats` для точного измерения
времени выполнения функций, логирования вызовов и сбора агрегированной статистики
(общее число вызовов, суммарное, среднее, минимальное и максимальное время).
"""

import functools
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class ProfileStats:
    """Статистика времени выполнения вызовов функции."""

    total_calls: int
    total_time: float
    min_time: float
    max_time: float

    @property
    def mean_time(self) -> float:
        """Среднее время выполнения за один вызов в секундах."""
        if self.total_calls == 0:
            return 0.0
        return self.total_time / self.total_calls


def profile_time(
    logger: Callable[[str], None] | None = None,
    label: str | None = None,
    time_func: Callable[[], float] = time.perf_counter,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор измерения и профилирования времени работы функции.

    :param logger: Опциональная функция логирования сообщений (например, print или logger.info).
    :param label: Пользовательская метка для идентификации в логах.
    :param time_func: Функция замера времени (по умолчанию time.perf_counter).
    :return: Декорированная функция с атрибутами `.stats` и методом `.reset_stats()`.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        tag = label if label is not None else func.__name__
        lock = threading.Lock()

        total_calls = 0
        total_time = 0.0
        min_time = float("inf")
        max_time = 0.0

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal total_calls, total_time, min_time, max_time

            start = time_func()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time_func() - start

                with lock:
                    total_calls += 1
                    total_time += elapsed
                    min_time = min(min_time, elapsed)
                    max_time = max(max_time, elapsed)

                if logger is not None:
                    logger(f"[{tag}] выполнена за {elapsed:.6f} сек.")

        def get_stats() -> ProfileStats:
            """Возвращает текущую статистику профилирования."""
            with lock:
                return ProfileStats(
                    total_calls=total_calls,
                    total_time=total_time,
                    min_time=min_time if total_calls > 0 else 0.0,
                    max_time=max_time,
                )

        def reset_stats() -> None:
            """Сбрасывает накопленную статистику."""
            nonlocal total_calls, total_time, min_time, max_time
            with lock:
                total_calls = 0
                total_time = 0.0
                min_time = float("inf")
                max_time = 0.0

        wrapper.stats = property(lambda self: get_stats()) if False else get_stats
        wrapper.get_stats = get_stats
        wrapper.reset_stats = reset_stats

        return wrapper

    return decorator
