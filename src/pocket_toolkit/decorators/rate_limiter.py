"""Модуль ограничения частоты вызовов на основе алгоритма корзины токенов (Token Bucket).

Предоставляет класс `TokenBucket` для отслеживания и пополнения токенов,
а также декоратор `@rate_limit` с поддержкой мгновенного отклонения (non-blocking),
ожидания доступности токенов (blocking) и раздельного лимитирования по ключам (key_func).
"""

from collections.abc import Callable, Hashable
import functools
import threading
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class RateLimitExceededError(Exception):
    """Исключение, возникающее при превышении допустимой частоты обращений."""

    def __init__(self, message: str = "Превышен лимит допустимой частоты вызовов") -> None:
        """Инициализирует ошибку превышения лимита."""
        super().__init__(message)


class TokenBucket:
    """Класс корзины токенов для ограничения частоты (Token Bucket).

    Потокобезопасная реализация с монотонным таймером.
    """

    __slots__ = (
        "_capacity",
        "_last_refill",
        "_lock",
        "_refill_rate",
        "_time_func",
        "_tokens",
    )

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        """Инициализирует корзину токенов.

        :param capacity: Максимальная вместимость корзины (всплеск, burst) > 0.
        :param refill_rate: Скорость пополнения (токенов в секунду) > 0.
        :param time_func: Функция получения текущего монотонного времени.
        :raises ValueError: Если вместимость или скорость <= 0.
        """
        if capacity <= 0:
            raise ValueError(f"Вместимость корзины capacity должна быть > 0, получено: {capacity}")
        if refill_rate <= 0:
            raise ValueError(f"Скорость пополнения refill_rate должна быть > 0, получено: {refill_rate}")

        self._capacity: float = float(capacity)
        self._refill_rate: float = float(refill_rate)
        self._time_func: Callable[[], float] = time_func
        self._tokens: float = float(capacity)
        self._last_refill: float = self._time_func()
        self._lock: threading.Lock = threading.Lock()

    @property
    def capacity(self) -> float:
        """Максимальная вместимость корзины."""
        return self._capacity

    @property
    def refill_rate(self) -> float:
        """Скорость пополнения в токенах в секунду."""
        return self._refill_rate

    def _refill(self, now: float) -> None:
        """Пополняет токены пропорционально прошедшему времени."""
        elapsed = now - self._last_refill
        if elapsed > 0:
            added_tokens = elapsed * self._refill_rate
            self._tokens = min(self._capacity, self._tokens + added_tokens)
            self._last_refill = now

    @property
    def available_tokens(self) -> float:
        """Текущее количество доступных токенов в корзине."""
        with self._lock:
            self._refill(self._time_func())
            return self._tokens

    def consume(self, tokens: float = 1.0) -> bool:
        """Пытается списать указанное число токенов без ожидания.

        :param tokens: Количество списываемых токенов (> 0).
        :return: True, если токены успешно списаны, False при их нехватке.
        :raises ValueError: Если запрашиваемое число токенов <= 0.
        """
        if tokens <= 0:
            raise ValueError(f"Число токенов должно быть > 0, получено: {tokens}")

        with self._lock:
            now = self._time_func()
            self._refill(now)

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    def wait_and_consume(
        self,
        tokens: float = 1.0,
        timeout: float | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> bool:
        """Ожидает накопления нужного количества токенов и списывает их.

        :param tokens: Количество токенов для списания.
        :param timeout: Максимальное время ожидания в секундах (или None).
        :param sleep_fn: Функция засыпания.
        :return: True, если токены были получены и списаны, False по истечении timeout.
        """
        if tokens <= 0:
            raise ValueError(f"Число токенов должно быть > 0, получено: {tokens}")
        if tokens > self._capacity:
            return False

        start_time = self._time_func()

        while True:
            with self._lock:
                now = self._time_func()
                self._refill(now)

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                missing = tokens - self._tokens
                wait_time = missing / self._refill_rate

            if timeout is not None:
                elapsed = self._time_func() - start_time
                if elapsed + wait_time > timeout:
                    return False

            sleep_fn(wait_time)


def rate_limit(
    rate: float,
    capacity: float | None = None,
    block: bool = False,
    timeout: float | None = None,
    key_func: Callable[..., Hashable] | None = None,
    time_func: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор ограничения частоты вызовов функции на основе корзины токенов.

    :param rate: Скорость генерации токенов (вызовов в секунду) > 0.
    :param capacity: Максимальный всплеск (по умолчанию равен rate).
    :param block: Если True — ожидает появления токена, иначе выбрасывает RateLimitExceededError.
    :param timeout: Предельное время ожидания при block=True.
    :param key_func: Функция выделения ключа из аргументов для раздельных лимитов (per-key).
    :param time_func: Функция монотонного времени.
    :param sleep_fn: Функция ожидания.
    :return: Декорированная функция.
    """
    effective_capacity = capacity if capacity is not None else rate
    buckets: dict[Hashable, TokenBucket] = {}
    buckets_lock = threading.Lock()

    def get_bucket(*args: P.args, **kwargs: P.kwargs) -> TokenBucket:
        if key_func is None:
            key = None
        else:
            key = key_func(*args, **kwargs)

        with buckets_lock:
            if key not in buckets:
                buckets[key] = TokenBucket(
                    capacity=effective_capacity,
                    refill_rate=rate,
                    time_func=time_func,
                )
            return buckets[key]

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bucket = get_bucket(*args, **kwargs)

            if block:
                acquired = bucket.wait_and_consume(1.0, timeout=timeout, sleep_fn=sleep_fn)
            else:
                acquired = bucket.consume(1.0)

            if not acquired:
                raise RateLimitExceededError(
                    f"Превышен лимит вызовов функции {func.__name__} (rate={rate}/s)"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
