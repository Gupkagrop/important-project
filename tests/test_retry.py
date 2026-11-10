"""Модульные тесты для декоратора повторных попыток (retry)."""

import random

import pytest

from pocket_toolkit.decorators.retry import (
    RetryExhaustedError,
    calculate_backoff_delay,
    retry,
)


def test_calculate_backoff_delay() -> None:
    """Проверка расчета экспоненциальной задержки."""
    assert calculate_backoff_delay(1, initial_delay=1.0, backoff_factor=2.0) == 1.0
    assert calculate_backoff_delay(2, initial_delay=1.0, backoff_factor=2.0) == 2.0
    assert calculate_backoff_delay(3, initial_delay=1.0, backoff_factor=2.0) == 4.0

    # Проверка максимального потолка задержки
    assert (
        calculate_backoff_delay(4, initial_delay=1.0, backoff_factor=2.0, max_delay=5.0) == 5.0
    )

    # Проверка джиттера с фиксированным RNG
    rng = random.Random(42)
    val = calculate_backoff_delay(2, initial_delay=1.0, jitter=True, rng=rng)
    assert 0.0 <= val <= 2.0


def test_retry_success_first_attempt() -> None:
    """Проверка успешного выполнения функции с первой попытки."""
    calls = 0

    @retry(max_attempts=3)
    def ok_func() -> str:
        nonlocal calls
        calls += 1
        return "success"

    assert ok_func() == "success"
    assert calls == 1


def test_retry_success_after_failures() -> None:
    """Проверка успешного выполнения после нескольких сбоев."""
    attempts = 0
    slept_delays: list[float] = []

    def mock_sleep(d: float) -> None:
        slept_delays.append(d)

    @retry(
        max_attempts=4,
        initial_delay=0.1,
        backoff_factor=2.0,
        sleep_fn=mock_sleep,
    )
    def flaky_func() -> int:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("temporary error")
        return 42

    result = flaky_func()
    assert result == 42
    assert attempts == 3
    assert len(slept_delays) == 2
    assert slept_delays[0] == pytest.approx(0.1)
    assert slept_delays[1] == pytest.approx(0.2)


def test_retry_exhausted_reraise_true() -> None:
    """Проверка выброса исходного исключения при reraise=True."""
    calls = 0

    @retry(max_attempts=3, initial_delay=0.0, sleep_fn=lambda _: None, reraise=True)
    def always_fail() -> None:
        nonlocal calls
        calls += 1
        raise KeyError("always missing")

    with pytest.raises(KeyError):
        always_fail()

    assert calls == 3


def test_retry_exhausted_reraise_false() -> None:
    """Проверка выброса RetryExhaustedError при reraise=False."""
    @retry(max_attempts=2, initial_delay=0.0, sleep_fn=lambda _: None, reraise=False)
    def always_fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RetryExhaustedError) as exc_info:
        always_fail()

    assert isinstance(exc_info.value.last_exception, RuntimeError)


def test_retry_filters_unmatched_exceptions() -> None:
    """Проверка немедленного проброса исключений, не входящих в список перехватываемых."""
    calls = 0

    @retry(
        max_attempts=3,
        exceptions=(ValueError,),
        initial_delay=0.0,
        sleep_fn=lambda _: None,
    )
    def fail_with_type_error() -> None:
        nonlocal calls
        calls += 1
        raise TypeError("wrong type")

    with pytest.raises(TypeError):
        fail_with_type_error()

    # Должен упасть сразу, без повторов
    assert calls == 1


def test_retry_on_retry_callback() -> None:
    """Проверка срабатывания коллбэка оповещения on_retry."""
    callback_logs: list[tuple[int, float]] = []

    def log_retry(err: Exception, attempt: int, delay: float) -> None:
        callback_logs.append((attempt, delay))

    @retry(
        max_attempts=3,
        initial_delay=0.5,
        on_retry=log_retry,
        sleep_fn=lambda _: None,
    )
    def fail_twice() -> str:
        if len(callback_logs) < 2:
            raise ValueError("fail")
        return "ok"

    res = fail_twice()
    assert res == "ok"
    assert len(callback_logs) == 2
    assert callback_logs[0][0] == 1
    assert callback_logs[1][0] == 2


def test_invalid_parameters() -> None:
    """Проверка валидации параметров декоратора."""
    with pytest.raises(ValueError):
        retry(max_attempts=0)
    with pytest.raises(ValueError):
        retry(initial_delay=-1.0)
    with pytest.raises(ValueError):
        retry(backoff_factor=0.5)
