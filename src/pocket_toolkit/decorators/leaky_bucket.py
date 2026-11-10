"""Модуль алгоритма ограничения трафика и вызовов «протекающее ведро» (Leaky Bucket).

Предоставляет класс `LeakyBucket` для сглаживания всплесков нагрузки и обеспечения
постоянной скорости обработки, а также декоратор `@leaky_bucket_limit` с поддержкой
режима мгновенного сброса (overflow) и режима сглаживания/ожидания.
"""

from collections.abc import Callable, Hashable
import functools
import threading
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class LeakyBucketOverflowError(Exception):
    """Исключение, возникающее при переполнении емкости протекающего ведра."""

    def __init__(self, message: str = "Переполнение лимита вызовов (Leaky Bucket Overflow)") -> None:
        """Инициализирует ошибку переполнения ведра."""
        super().__init__(message)


class LeakyBucket:
    """Класс ограничителя «протекающее ведро» (Leaky Bucket).

    Потокобезопасная реализация со сглаживанием трафика и фиксацией постоянной скорости утечки.
    """

    __slots__ = (
        "_capacity",
        "_last_leak",
        "_leak_rate",
        "_lock",
        "_time_func",
        "_water",
    )

    def __init__(
        self,
        capacity: float,
        leak_rate: float,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        """Инициализирует протекающее ведро.

        :param capacity: Максимальная вместимость ведра (емкость буфера) > 0.
        :param leak_rate: Скорость утечки (единиц/вызовов в секунду) > 0.
        :param time_func: Функция получения монотонного времени.
        :raises ValueError: Если вместимость или скорость утечки <= 0.
        """
        if capacity <= 0:
            raise ValueError(f"Вместимость capacity должна быть > 0, получено: {capacity}")
        if leak_rate <= 0:
            raise ValueError(f"Скорость утечки leak_rate должна быть > 0, получено: {leak_rate}")

        self._capacity: float = float(capacity)
        self._leak_rate: float = float(leak_rate)
        self._time_func: Callable[[], float] = time_func
        self._water: float = 0.0
        self._last_leak: float = self._time_func()
        self._lock: threading.Lock = threading.Lock()

    @property
    def capacity(self) -> float:
        """Максимальная вместимость ведра."""
        return self._capacity

    @property
    def leak_rate(self) -> float:
        """Скорость утечки в единицах в секунду."""
        return self._leak_rate

    def _leak(self, now: float) -> None:
        """Уменьшает уровень воды пропорционально истекшему времени."""
        elapsed = now - self._last_leak
        if elapsed > 0:
            leaked = elapsed * self._leak_rate
            self._water = max(0.0, self._water - leaked)
            self._last_leak = now

    @property
    def current_water(self) -> float:
        """Текущий уровень воды (заполненности) в ведре."""
        with self._lock:
            self._leak(self._time_func())
            return self._water

    def add(self, amount: float = 1.0) -> bool:
        """Пытается добавить объем воды (вызов) в ведро без ожидания.

        :param amount: Добавляемый объем (> 0).
        :return: True, если вода поместилась в ведро, False при переполнении.
        :raises ValueError: Если amount <= 0.
        """
        if amount <= 0:
            raise ValueError(f"Добавляемый объем должен быть > 0, получено: {amount}")

        with self._lock:
            now = self._time_func()
            self._leak(now)

            if self._water + amount <= self._capacity:
                self._water += amount
                return True

            return False

    def wait_and_add(
        self,
        amount: float = 1.0,
        timeout: float | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> bool:
        """Ожидает освобождения места в ведре и добавляет объем.

        :param amount: Добавляемый объем (> 0).
        :param timeout: Максимальное время ожидания в секундах (или None).
        :param sleep_fn: Функция ожидания.
        :return: True, если объем успешно добавлен, False по истечении таймаута.
        """
        if amount <= 0:
            raise ValueError(f"Добавляемый объем должен быть > 0, получено: {amount}")
        if amount > self._capacity:
            return False

        start_time = self._time_func()

        while True:
            with self._lock:
                now = self._time_func()
                self._leak(now)

                if self._water + amount <= self._capacity:
                    self._water += amount
                    return True

                excess = (self._water + amount) - self._capacity
                wait_time = excess / self._leak_rate

            if timeout is not None:
                elapsed = self._time_func() - start_time
                if elapsed + wait_time > timeout:
                    return False

            sleep_fn(wait_time)


def leaky_bucket_limit(
    capacity: float,
    leak_rate: float,
    block: bool = False,
    timeout: float | None = None,
    key_func: Callable[..., Hashable] | None = None,
    time_func: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор ограничения частоты вызовов по алгоритму Leaky Bucket.

    :param capacity: Вместимость ведра (буфер максимального всплеска) > 0.
    :param leak_rate: Скорость обработки/утечки (вызовов в секунду) > 0.
    :param block: Если True — ожидает утечки из ведра, иначе выбрасывает LeakyBucketOverflowError.
    :param timeout: Максимальный таймаут ожидания при block=True.
    :param key_func: Опциональная функция вычисления ключа разделения лимитов.
    :param time_func: Функция монотонного времени.
    :param sleep_fn: Функция засыпания.
    :return: Декорированная функция.
    """
    buckets: dict[Hashable, LeakyBucket] = {}
    buckets_lock = threading.Lock()

    def get_bucket(*args: P.args, **kwargs: P.kwargs) -> LeakyBucket:
        key = None if key_func is None else key_func(*args, **kwargs)

        with buckets_lock:
            if key not in buckets:
                buckets[key] = LeakyBucket(
                    capacity=capacity,
                    leak_rate=leak_rate,
                    time_func=time_func,
                )
            return buckets[key]

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bucket = get_bucket(*args, **kwargs)

            if block:
                accepted = bucket.wait_and_add(1.0, timeout=timeout, sleep_fn=sleep_fn)
            else:
                accepted = bucket.add(1.0)

            if not accepted:
                raise LeakyBucketOverflowError(
                    f"Переполнение буфера вызовов для функции {func.__name__} (capacity={capacity})"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
