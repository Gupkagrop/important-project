"""Модульные тесты для модуля алгоритма «протекающее ведро» (leaky_bucket)."""

import pytest
from pocket_toolkit.decorators.leaky_bucket import (
    LeakyBucket,
    LeakyBucketOverflowError,
    leaky_bucket_limit,
)


class MockClock:
    """Имитатор монотонного времени для детерминированного тестирования."""

    def __init__(self, start_time: float = 100.0) -> None:
        self.time: float = start_time

    def now(self) -> float:
        return self.time

    def advance(self, seconds: float) -> None:
        self.time += seconds


def test_leaky_bucket_initialization() -> None:
    """Проверка валидации параметров LeakyBucket."""
    clock = MockClock()
    bucket = LeakyBucket(capacity=10.0, leak_rate=2.0, time_func=clock.now)
    assert bucket.capacity == 10.0
    assert bucket.leak_rate == 2.0
    assert bucket.current_water == 0.0

    with pytest.raises(ValueError):
        LeakyBucket(capacity=0, leak_rate=1)
    with pytest.raises(ValueError):
        LeakyBucket(capacity=5, leak_rate=-1)


def test_leaky_bucket_add_and_leak() -> None:
    """Проверка добавления воды и ее утечки со временем."""
    clock = MockClock()
    bucket = LeakyBucket(capacity=3.0, leak_rate=1.0, time_func=clock.now)

    assert bucket.add(1.0) is True
    assert bucket.add(1.0) is True
    assert bucket.add(1.0) is True
    # Ведро заполнено (3.0 / 3.0), следующее добавление должно вернуть False
    assert bucket.add(1.0) is False

    # Проходит 1.5 секунды -> утекает 1.5 единицы
    clock.advance(1.5)
    assert bucket.current_water == pytest.approx(1.5)
    # Теперь можно добавить 1 единицу
    assert bucket.add(1.0) is True
    assert bucket.current_water == pytest.approx(2.5)


def test_leaky_bucket_wait_and_add() -> None:
    """Проверка ожидания освобождения объема в ведре."""
    clock = MockClock()
    slept: list[float] = []

    def mock_sleep(d: float) -> None:
        slept.append(d)
        clock.advance(d)

    bucket = LeakyBucket(capacity=2.0, leak_rate=2.0, time_func=clock.now)
    assert bucket.add(2.0) is True  # Полное ведро

    # Ожидаем добавления 1 единицы (должно потребоваться 0.5 секунды при leak_rate=2.0)
    ok = bucket.wait_and_add(1.0, timeout=1.0, sleep_fn=mock_sleep)
    assert ok is True
    assert len(slept) == 1
    assert slept[0] == pytest.approx(0.5)


def test_leaky_bucket_limit_decorator() -> None:
    """Проверка декоратора leaky_bucket_limit."""
    clock = MockClock()

    @leaky_bucket_limit(capacity=2, leak_rate=1, block=False, time_func=clock.now)
    def task() -> str:
        return "ok"

    assert task() == "ok"
    assert task() == "ok"

    # Третий вызов вызывает переполнение
    with pytest.raises(LeakyBucketOverflowError):
        task()

    # Сдвигаем время на 1.0 секунду
    clock.advance(1.0)
    assert task() == "ok"


def test_leaky_bucket_limit_per_key() -> None:
    """Проверка раздельного лимитирования по ключам."""
    clock = MockClock()

    @leaky_bucket_limit(
        capacity=1,
        leak_rate=1,
        key_func=lambda client: client,
        time_func=clock.now,
    )
    def request(client: str) -> str:
        return f"res_{client}"

    assert request("client_a") == "res_client_a"
    assert request("client_b") == "res_client_b"

    with pytest.raises(LeakyBucketOverflowError):
        request("client_a")
