"""Модульные тесты для паттерна CircuitBreaker."""

import pytest

from pocket_toolkit.decorators.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


class MockClock:
    """Имитатор монотонного времени."""

    def __init__(self, start_time: float = 1000.0) -> None:
        self.time: float = start_time

    def now(self) -> float:
        return self.time

    def advance(self, seconds: float) -> None:
        self.time += seconds


def test_circuit_breaker_transitions() -> None:
    """Проверка полного жизненного цикла перехода между CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    clock = MockClock()
    cb = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=10.0,
        half_open_success_threshold=2,
        time_func=clock.now,
    )

    assert cb.state == CircuitState.CLOSED

    def faulty(should_fail: bool) -> str:
        if should_fail:
            raise ConnectionError("network down")
        return "ok"

    # Первый сбой
    with pytest.raises(ConnectionError):
        cb.call(faulty, True)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # Второй сбой — достигнут порог, переходит в OPEN
    with pytest.raises(ConnectionError):
        cb.call(faulty, True)
    assert cb.state == CircuitState.OPEN

    # Вызовы в состоянии OPEN немедленно блокируются ошибкой CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(faulty, False)

    # Проходит 10 секунд recovery_timeout — переходит в HALF_OPEN
    clock.advance(10.0)
    assert cb.state == CircuitState.HALF_OPEN

    # Первый пробный успех в HALF_OPEN
    assert cb.call(faulty, False) == "ok"
    assert cb.state == CircuitState.HALF_OPEN

    # Второй пробный успех — выключатель восстанавливается в CLOSED
    assert cb.call(faulty, False) == "ok"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_half_open_failure() -> None:
    """Проверка возврата в состояние OPEN при сбое в режиме HALF_OPEN."""
    clock = MockClock()
    cb = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=5.0,
        time_func=clock.now,
    )

    def faulty() -> None:
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        cb.call(faulty)
    assert cb.state == CircuitState.OPEN

    clock.advance(5.0)
    assert cb.state == CircuitState.HALF_OPEN

    # Сбой в HALF_OPEN должен сразу вернуть в OPEN
    with pytest.raises(RuntimeError):
        cb.call(faulty)
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_fallback() -> None:
    """Проверка срабатывания фоллбэка при сбоях и в открытом состоянии."""
    clock = MockClock()
    cb = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=10.0,
        fallback=lambda *args, **kwargs: "fallback_value",
        time_func=clock.now,
    )

    def failing_service() -> str:
        raise TimeoutError("timeout")

    # При сбое возвращается fallback вместо ошибки
    assert cb.call(failing_service) == "fallback_value"
    assert cb.state == CircuitState.OPEN

    # В состоянии OPEN также возвращается fallback
    assert cb.call(failing_service) == "fallback_value"


def test_circuit_breaker_decorator_and_reset() -> None:
    """Проверка применения выключателя как декоратора и ручного сброса reset()."""
    cb = CircuitBreaker(failure_threshold=1)

    @cb
    def fragile() -> str:
        raise ValueError("broken")

    with pytest.raises(ValueError):
        fragile()
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_validation() -> None:
    """Проверка валидации параметров CircuitBreaker."""
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=0)
    with pytest.raises(ValueError):
        CircuitBreaker(recovery_timeout=0)
    with pytest.raises(ValueError):
        CircuitBreaker(half_open_success_threshold=0)
