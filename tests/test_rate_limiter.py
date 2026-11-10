"""Модульные тесты для модуля ограничения частоты вызовов (rate_limiter)."""

import pytest
from pocket_toolkit.decorators.rate_limiter import (
    RateLimitExceededError,
    TokenBucket,
    rate_limit,
)


class MockClock:
    """Имитатор монотонного времени для детерминированного тестирования."""

    def __init__(self, start_time: float = 1000.0) -> None:
        self.time: float = start_time

    def now(self) -> float:
        return self.time

    def advance(self, seconds: float) -> None:
        self.time += seconds


def test_token_bucket_initialization() -> None:
    """Проверка параметров инициализации TokenBucket."""
    clock = MockClock()
    bucket = TokenBucket(capacity=5, refill_rate=2, time_func=clock.now)
    assert bucket.capacity == 5.0
    assert bucket.refill_rate == 2.0
    assert bucket.available_tokens == 5.0

    with pytest.raises(ValueError):
        TokenBucket(capacity=0, refill_rate=1)
    with pytest.raises(ValueError):
        TokenBucket(capacity=5, refill_rate=-1)


def test_token_bucket_consume_and_refill() -> None:
    """Проверка списания токенов и их пополнения со временем."""
    clock = MockClock()
    bucket = TokenBucket(capacity=2, refill_rate=1, time_func=clock.now)

    # Списываем 2 токена
    assert bucket.consume(1.0) is True
    assert bucket.consume(1.0) is True
    assert bucket.consume(1.0) is False  # Токены кончились

    # Перемещаем время на 1 секунду вперед (пополняется 1 токен)
    clock.advance(1.0)
    assert bucket.consume(1.0) is True
    assert bucket.consume(1.0) is False

    # Перемещаем время на 10 секунд (пополнение ограничивается capacity=2)
    clock.advance(10.0)
    assert bucket.available_tokens == 2.0


def test_token_bucket_wait_and_consume() -> None:
    """Проверка блокирующего ожидания токенов."""
    clock = MockClock()
    slept: list[float] = []

    def mock_sleep(d: float) -> None:
        slept.append(d)
        clock.advance(d)

    bucket = TokenBucket(capacity=1, refill_rate=2, time_func=clock.now)
    assert bucket.consume(1.0) is True

    # Ожидание 1 токена (требуется 0.5 секунды)
    ok = bucket.wait_and_consume(1.0, timeout=1.0, sleep_fn=mock_sleep)
    assert ok is True
    assert len(slept) == 1
    assert slept[0] == pytest.approx(0.5)

    # Запрос превышает timeout
    clock_timeout = MockClock()
    bucket_timeout = TokenBucket(capacity=1, refill_rate=0.1, time_func=clock_timeout.now)
    assert bucket_timeout.consume(1.0) is True
    assert (
        bucket_timeout.wait_and_consume(
            1.0,
            timeout=0.2,
            sleep_fn=lambda d: clock_timeout.advance(d),
        )
        is False
    )


def test_rate_limit_decorator_non_blocking() -> None:
    """Проверка декоратора в режиме немедленного отклонения при исчерпании лимита."""
    clock = MockClock()

    @rate_limit(rate=2, capacity=2, block=False, time_func=clock.now)
    def action() -> str:
        return "done"

    assert action() == "done"
    assert action() == "done"

    # Третий вызов подряд должен упасть
    with pytest.raises(RateLimitExceededError):
        action()

    # Сдвигаем время на 1 секунду вперед (пополняются 2 токена)
    clock.advance(1.0)
    assert action() == "done"


def test_rate_limit_decorator_with_key_func() -> None:
    """Проверка изолированного лимитирования по пользователям (per-key)."""
    clock = MockClock()

    @rate_limit(
        rate=1,
        capacity=1,
        key_func=lambda user_id: user_id,
        time_func=clock.now,
    )
    def handle_request(user_id: str) -> str:
        return f"ok_{user_id}"

    assert handle_request("alice") == "ok_alice"
    assert handle_request("bob") == "ok_bob"

    # Повторный вызов для alice должен быть отклонен, а для bob тоже отклонен
    with pytest.raises(RateLimitExceededError):
        handle_request("alice")

    with pytest.raises(RateLimitExceededError):
        handle_request("bob")

    # Сдвигаем время
    clock.advance(1.0)
    assert handle_request("alice") == "ok_alice"
