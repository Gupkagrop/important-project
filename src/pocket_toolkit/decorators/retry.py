"""Модуль декоратора повторных попыток (Retry with Exponential Backoff).

Предоставляет настраиваемый декоратор `@retry` с поддержкой экспоненциальной задержки,
рандомизированного джиттера (jitter), фильтрации типов исключений и коллбэков оповещения.
"""

from collections.abc import Callable
import functools
import random
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class RetryExhaustedError(Exception):
    """Исключение, возникающее при исчерпании лимита попыток выполнения функции."""

    def __init__(self, message: str, last_exception: Exception | None = None) -> None:
        """Инициализирует ошибку исчерпания попыток.

        :param message: Пояснительное сообщение.
        :param last_exception: Последнее возникшее исключение.
        """
        super().__init__(message)
        self.last_exception: Exception | None = last_exception


def calculate_backoff_delay(
    attempt: int,
    initial_delay: float,
    backoff_factor: float = 2.0,
    max_delay: float | None = None,
    jitter: bool = False,
    rng: random.Random | None = None,
) -> float:
    """Вычисляет длительность паузы перед следующей попыткой.

    :param attempt: Номер текущей завершившейся попытки (1, 2, ...).
    :param initial_delay: Базовая начальная задержка в секундах.
    :param backoff_factor: Множитель экспоненциального роста (>= 1.0).
    :param max_delay: Максимальный верхний предел задержки (или None).
    :param jitter: Добавлять ли случайный шум (full jitter от 0 до delay).
    :param rng: Опциональный генератор случайных чисел.
    :return: Время задержки в секундах.
    """
    delay = initial_delay * (backoff_factor ** (attempt - 1))
    if max_delay is not None and delay > max_delay:
        delay = max_delay

    if jitter:
        rand = rng or random
        delay = rand.uniform(0.0, delay)

    return max(0.0, delay)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 0.05,
    backoff_factor: float = 2.0,
    max_delay: float | None = None,
    jitter: bool = False,
    exceptions: type[Exception] | tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int, float], None] | None = None,
    reraise: bool = True,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор для автоматического повторения вызова функции при возникновении ошибок.

    :param max_attempts: Максимальное количество попыток (>= 1).
    :param initial_delay: Начальная задержка между попытками в секундах (>= 0).
    :param backoff_factor: Множитель экспоненциального нарастания (>= 1.0).
    :param max_delay: Верхний предел задержки в секундах.
    :param jitter: Добавлять ли случайный джиттер.
    :param exceptions: Кортеж или тип перехватываемых исключений.
    :param on_retry: Функция обратного вызова (exception, attempt, delay).
    :param reraise: Пробрасывать ли оригинальное исключение (иначе RetryExhaustedError).
    :param sleep_fn: Функция ожидания (по умолчанию time.sleep).
    :return: Декорированная функция.
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts должен быть >= 1, получено: {max_attempts}")
    if initial_delay < 0:
        raise ValueError(f"initial_delay не может быть отрицательным, получено: {initial_delay}")
    if backoff_factor < 1.0:
        raise ValueError(f"backoff_factor должен быть >= 1.0, получено: {backoff_factor}")

    target_exceptions = exceptions if isinstance(exceptions, tuple) else (exceptions,)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_err: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except target_exceptions as exc:
                    last_err = exc
                    if attempt == max_attempts:
                        break

                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        initial_delay=initial_delay,
                        backoff_factor=backoff_factor,
                        max_delay=max_delay,
                        jitter=jitter,
                    )

                    if on_retry is not None:
                        on_retry(exc, attempt, delay)

                    if delay > 0:
                        sleep_fn(delay)

            # Если попытки исчерпаны
            if reraise and last_err is not None:
                raise last_err

            raise RetryExhaustedError(
                f"Функция {func.__name__} завершилась неудачей после {max_attempts} попыток",
                last_exception=last_err,
            )

        return wrapper

    return decorator
