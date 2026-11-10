"""Модуль декоратора ограничения частоты вызовов (Throttle Decorator).

Предоставляет декоратор `@throttle` для гарантии вызова функции не чаще одного раза
за заданный временной интервал (`interval`) с настраиваемыми фронтами вызова:
начальным (`leading`) и завершающим (`trailing`).
"""

from collections.abc import Callable
import functools
import threading
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def throttle(
    interval: float,
    leading: bool = True,
    trailing: bool = True,
    time_func: Callable[[], float] = time.monotonic,
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Декоратор ограничения частоты вызовов функции (Throttle).

    Гарантирует выполнение функции не чаще одного раза за период `interval`.

    :param interval: Минимальный интервал между вызовами в секундах (> 0).
    :param leading: Выполнять ли функцию немедленно при первом вызове (передний фронт).
    :param trailing: Выполнять ли функцию по окончании интервала с последними переданными аргументами.
    :param time_func: Функция монотонного времени.
    :return: Декорированная функция.
    :raises ValueError: Если interval <= 0 или оба флага leading и trailing равны False.
    """
    if interval <= 0:
        raise ValueError(f"Интервал interval должен быть строго положительным (> 0), получено: {interval}")
    if not leading and not trailing:
        raise ValueError("Хотя бы один из флагов leading или trailing должен быть True")

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        lock = threading.Lock()
        last_call_time: float = 0.0
        last_result: R | None = None
        trailing_timer: threading.Timer | None = None
        last_args: tuple[object, ...] = ()
        last_kwargs: dict[str, object] = {}

        def execute_trailing() -> None:
            nonlocal last_call_time, last_result, trailing_timer, last_args, last_kwargs
            with lock:
                args = last_args
                kwargs = last_kwargs
                trailing_timer = None
                last_call_time = time_func()
            last_result = func(*args, **kwargs)  # type: ignore[arg-type]

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            nonlocal last_call_time, last_result, trailing_timer, last_args, last_kwargs
            now = time_func()

            with lock:
                last_args = args
                last_kwargs = kwargs
                elapsed = now - last_call_time

                # 1. Первый вызов или прошло достаточно времени с прошлого вызова
                if elapsed >= interval:
                    if leading:
                        last_call_time = now
                        last_result = func(*args, **kwargs)
                        return last_result

                    # Если leading=False, откладываем выполнение на trailing
                    last_call_time = now
                    if trailing and trailing_timer is None:
                        trailing_timer = threading.Timer(interval, execute_trailing)
                        trailing_timer.daemon = True
                        trailing_timer.start()
                    return last_result

                # 2. Вызов совершен внутри интервала: планируем trailing, если он включен
                if trailing and trailing_timer is None:
                    remaining = interval - elapsed
                    trailing_timer = threading.Timer(remaining, execute_trailing)
                    trailing_timer.daemon = True
                    trailing_timer.start()

                return last_result

        def cancel() -> None:
            """Отменяет отложенный trailing-вызов."""
            nonlocal trailing_timer
            with lock:
                if trailing_timer is not None:
                    trailing_timer.cancel()
                    trailing_timer = None

        def flush() -> R | None:
            """Принудительно выполняет отложенный вызов немедленно."""
            nonlocal trailing_timer, last_call_time, last_result
            with lock:
                if trailing_timer is None:
                    return last_result
                trailing_timer.cancel()
                trailing_timer = None
                args = last_args
                kwargs = last_kwargs
                last_call_time = time_func()
            last_result = func(*args, **kwargs)  # type: ignore[arg-type]
            return last_result

        setattr(wrapper, "cancel", cancel)
        setattr(wrapper, "flush", flush)

        return wrapper

    return decorator
