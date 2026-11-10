"""Модуль декоратора подавления дребезга (Debounce Decorator).

Предоставляет декоратор `@debounce` для откладывания выполнения вызова функции
до тех пор, пока с момента последнего вызова не истечет заданная пауза тишины (`wait`),
с поддержкой принудительного сброса (`flush`), отмены (`cancel`) и предельного времени ожидания (`max_wait`).
"""

from collections.abc import Callable
import functools
import threading
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def debounce(
    wait: float,
    max_wait: float | None = None,
    time_func: Callable[[], float] = time.monotonic,
) -> Callable[[Callable[P, R]], Callable[P, None]]:
    """Декоратор подавления дребезга вызовов функции (Debounce).

    Откладывает фактическое выполнение функции до истечения периода `wait` с момента последнего вызова.
    Поскольку вызов откладывается во времени, возвращаемое значение функции в точке вызова — None.
    Добавляет методы `.flush()`, `.cancel()` и свойство `.pending`.

    :param wait: Время тишины в секундах до выполнения функции (> 0).
    :param max_wait: Максимальное время задержки в секундах до гарантированного выполнения (или None).
    :param time_func: Функция монотонного времени.
    :return: Декорированная функция с методами управления таймером.
    """
    if wait <= 0:
        raise ValueError(f"Время ожидания wait должно быть > 0, получено: {wait}")
    if max_wait is not None and max_wait < wait:
        raise ValueError(
            f"max_wait ({max_wait}) не может быть меньше периода тишины wait ({wait})"
        )

    def decorator(func: Callable[P, R]) -> Callable[P, None]:
        lock = threading.Lock()
        timer: threading.Timer | None = None
        last_args: tuple[object, ...] = ()
        last_kwargs: dict[str, object] = {}
        first_call_time: float | None = None

        def execute() -> None:
            nonlocal timer, first_call_time, last_args, last_kwargs
            with lock:
                args = last_args
                kwargs = last_kwargs
                timer = None
                first_call_time = None
            func(*args, **kwargs)  # type: ignore[arg-type]

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
            nonlocal timer, first_call_time, last_args, last_kwargs
            now = time_func()

            with lock:
                last_args = args
                last_kwargs = kwargs

                if first_call_time is None:
                    first_call_time = now

                # Отменяем предыдущий таймер
                if timer is not None:
                    timer.cancel()
                    timer = None

                delay = wait
                if max_wait is not None:
                    elapsed = now - first_call_time
                    remaining = max_wait - elapsed
                    if remaining <= 0:
                        # Предельное время истекло: вызываем немедленно в текущем потоке
                        args_to_run = last_args
                        kwargs_to_run = last_kwargs
                        first_call_time = None
                        timer = None
                        func(*args_to_run, **kwargs_to_run)  # type: ignore[arg-type]
                        return
                    delay = min(wait, remaining)

                timer = threading.Timer(delay, execute)
                timer.daemon = True
                timer.start()

        def cancel() -> None:
            """Отменяет отложенный вызов без выполнения."""
            nonlocal timer, first_call_time
            with lock:
                if timer is not None:
                    timer.cancel()
                    timer = None
                first_call_time = None

        def flush() -> None:
            """Принудительно выполняет отложенный вызов немедленно (если есть)."""
            nonlocal timer, first_call_time, last_args, last_kwargs
            with lock:
                if timer is None:
                    return
                timer.cancel()
                timer = None
                first_call_time = None
                args = last_args
                kwargs = last_kwargs
            func(*args, **kwargs)  # type: ignore[arg-type]

        def is_pending() -> bool:
            """Проверяет, ожидает ли функция выполнения по таймеру."""
            with lock:
                return timer is not None

        setattr(wrapper, "cancel", cancel)
        setattr(wrapper, "flush", flush)
        setattr(wrapper, "is_pending", is_pending)

        return wrapper

    return decorator
