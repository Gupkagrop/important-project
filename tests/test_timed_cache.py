"""Модульные тесты для декоратора timed_cache."""

from typing import Any
import pytest
from pocket_toolkit.decorators.timed_cache import CacheInfo, timed_cache


class MockClock:
    """Имитатор монотонного времени."""

    def __init__(self, start_time: float = 100.0) -> None:
        self.time: float = start_time

    def now(self) -> float:
        return self.time

    def advance(self, seconds: float) -> None:
        self.time += seconds


def test_timed_cache_hits_and_misses() -> None:
    """Проверка учета попаданий и промахов в кэш."""
    clock = MockClock()
    calls = 0

    @timed_cache(ttl=10.0, time_func=clock.now)
    def compute(x: int) -> int:
        nonlocal calls
        calls += 1
        return x * 2

    wrapper: Any = compute
    assert wrapper(5) == 10
    assert calls == 1
    assert wrapper(5) == 10
    assert calls == 1

    info = wrapper.cache_info()
    assert info == CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)


def test_timed_cache_ttl_expiration() -> None:
    """Проверка истечения времени жизни TTL."""
    clock = MockClock()
    calls = 0

    @timed_cache(ttl=5.0, time_func=clock.now)
    def get_data(key: str) -> str:
        nonlocal calls
        calls += 1
        return f"{key}_{calls}"

    wrapper: Any = get_data
    assert wrapper("a") == "a_1"
    assert wrapper("a") == "a_1"

    # Сдвигаем время на 4 секунды — кэш еще валиден
    clock.advance(4.0)
    assert wrapper("a") == "a_1"
    assert calls == 1

    # Сдвигаем время еще на 1.5 секунды (всего 5.5 > 5.0) — запись истекла
    clock.advance(1.5)
    assert wrapper("a") == "a_2"
    assert calls == 2


def test_timed_cache_lru_eviction() -> None:
    """Проверка LRU вытеснения при заполнении maxsize."""
    clock = MockClock()
    calls = 0

    @timed_cache(ttl=60.0, maxsize=2, time_func=clock.now)
    def square(n: int) -> int:
        nonlocal calls
        calls += 1
        return n * n

    wrapper: Any = square
    assert wrapper(1) == 1
    assert wrapper(2) == 4
    # Кэш содержит {1, 2}
    # Обращаемся к 1, делая 2 наименее востребованным
    assert wrapper(1) == 1

    # Добавляем 3: элемент 2 должен вытесниться
    assert wrapper(3) == 9
    assert wrapper.cache_info().currsize == 2

    # Элемент 1 в кэше (попадание)
    assert wrapper(1) == 1
    # Элемент 2 вытеснен (промах и повторный расчет)
    assert wrapper(2) == 4
    assert calls == 4


def test_timed_cache_clear_and_evict_expired() -> None:
    """Проверка ручной очистки кэша и удаления устаревших записей."""
    clock = MockClock()

    @timed_cache(ttl=10.0, time_func=clock.now)
    def fetch(x: int) -> int:
        return x

    wrapper: Any = fetch
    wrapper(1)
    wrapper(2)
    assert wrapper.cache_info().currsize == 2

    # Сдвигаем время и вызываем cache_evict_expired
    clock.advance(15.0)
    evicted = wrapper.cache_evict_expired()
    assert evicted == 2
    assert wrapper.cache_info().currsize == 0

    # Проверка cache_clear
    wrapper(3)
    assert wrapper.cache_info().currsize == 1
    wrapper.cache_clear()
    assert wrapper.cache_info().currsize == 0
    assert wrapper.cache_info().hits == 0
    assert wrapper.cache_info().misses == 0


def test_timed_cache_typed() -> None:
    """Проверка разграничения ключей по типам аргументов при typed=True."""
    clock = MockClock()
    calls = 0

    @timed_cache(ttl=10.0, typed=True, time_func=clock.now)
    def stringify(x: object) -> str:
        nonlocal calls
        calls += 1
        return str(x)

    wrapper: Any = stringify
    wrapper(1)
    wrapper(1.0)
    assert calls == 2
    assert wrapper.cache_info().currsize == 2


def test_timed_cache_validation() -> None:
    """Проверка валидации параметров декоратора timed_cache."""
    with pytest.raises(ValueError):
        timed_cache(ttl=0)
    with pytest.raises(ValueError):
        timed_cache(ttl=-5)
    with pytest.raises(ValueError):
        timed_cache(ttl=10, maxsize=0)
