"""Модуль паттерна защитного выключателя (Circuit Breaker Pattern).

Предоставляет класс `CircuitBreaker` и перечисление `CircuitState` (CLOSED, OPEN, HALF_OPEN)
для предотвращения каскадных сбоев при обращениях к нестабильным внешним сервисам,
с поддержкой экспоненциального восстановления, фоллбэков и потокобезопасности.
"""

from collections.abc import Callable
from enum import Enum
import functools
import threading
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class CircuitState(Enum):
    """Состояния автомата защитного выключателя."""

    CLOSED = "closed"        # Нормальная работа, вызовы разрешены
    OPEN = "open"            # Выключатель разомкнут, вызовы блокируются
    HALF_OPEN = "half_open"  # Пробный режим проверки работоспособности


class CircuitBreakerOpenError(Exception):
    """Исключение, возникающее при попытке вызова через разомкнутый выключатель (OPEN)."""

    def __init__(self, message: str = "Выключатель CircuitBreaker разомкнут (OPEN)") -> None:
        """Инициализирует ошибку разомкнутого выключателя."""
        super().__init__(message)


class CircuitBreaker:
    """Защитный выключатель (Circuit Breaker) для изоляции сбоев.

    Поддерживает использование как в виде объекта вызова `.call()`, так и в качестве декоратора.
    """

    __slots__ = (
        "_exceptions",
        "_failure_count",
        "_failure_threshold",
        "_fallback",
        "_half_open_success_threshold",
        "_last_failure_time",
        "_lock",
        "_recovery_timeout",
        "_state",
        "_success_count",
        "_time_func",
    )

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_success_threshold: int = 2,
        exceptions: type[Exception] | tuple[type[Exception], ...] = (Exception,),
        fallback: Callable[..., object] | None = None,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        """Инициализирует защитный выключатель.

        :param failure_threshold: Число сбоев подряд для перехода в OPEN (> 0).
        :param recovery_timeout: Время нахождения в состоянии OPEN до перехода в HALF_OPEN (> 0).
        :param half_open_success_threshold: Число успехов в HALF_OPEN для возврата в CLOSED (> 0).
        :param exceptions: Тип или кортеж перехватываемых исключений.
        :param fallback: Опциональная функция аварийной замены при блокировке или ошибке.
        :param time_func: Функция получения монотонного времени.
        """
        if failure_threshold < 1:
            raise ValueError(f"failure_threshold должен быть >= 1, получено: {failure_threshold}")
        if recovery_timeout <= 0:
            raise ValueError(f"recovery_timeout должен быть > 0, получено: {recovery_timeout}")
        if half_open_success_threshold < 1:
            raise ValueError(
                f"half_open_success_threshold должен быть >= 1, получено: {half_open_success_threshold}"
            )

        self._failure_threshold: int = failure_threshold
        self._recovery_timeout: float = recovery_timeout
        self._half_open_success_threshold: int = half_open_success_threshold
        self._exceptions: tuple[type[Exception], ...] = (
            exceptions if isinstance(exceptions, tuple) else (exceptions,)
        )
        self._fallback: Callable[..., object] | None = fallback
        self._time_func: Callable[[], float] = time_func

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._success_count: int = 0
        self._last_failure_time: float = 0.0
        self._lock: threading.Lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Текущее состояние выключателя (с проверкой истечения recovery_timeout)."""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def failure_count(self) -> int:
        """Текущее количество последовательных сбоев."""
        with self._lock:
            return self._failure_count

    def _check_state_transition(self) -> None:
        """Внутренний переход из OPEN в HALF_OPEN при истечении таймаута."""
        if self._state == CircuitState.OPEN:
            elapsed = self._time_func() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0

    def _handle_success(self) -> None:
        """Обрабатывает успешный вызов защищаемой функции."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._half_open_success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def _handle_failure(self) -> None:
        """Обрабатывает сбой защищаемой функции."""
        with self._lock:
            self._last_failure_time = self._time_func()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._failure_count = self._failure_threshold
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self._failure_threshold:
                    self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Принудительно сбрасывает состояние выключателя в CLOSED."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = 0.0

    def call(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Вызывает переданную функцию через защитный выключатель.

        :param func: Вызываемая функция.
        :return: Результат выполнения func или фоллбэка.
        :raises CircuitBreakerOpenError: Если выключатель находится в состоянии OPEN и нет фоллбэка.
        """
        with self._lock:
            self._check_state_transition()
            is_open = self._state == CircuitState.OPEN

        if is_open:
            if self._fallback is not None:
                return self._fallback(*args, **kwargs)  # type: ignore[return-value]
            raise CircuitBreakerOpenError(
                f"Вызовы заблокированы: CircuitBreaker в состоянии {self._state.value.upper()}"
            )

        try:
            result = func(*args, **kwargs)
        except self._exceptions as exc:
            self._handle_failure()
            if self._fallback is not None:
                return self._fallback(*args, **kwargs)  # type: ignore[return-value]
            raise exc

        self._handle_success()
        return result

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Позволяет использовать экземпляр CircuitBreaker как декоратор."""
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return self.call(func, *args, **kwargs)

        return wrapper
