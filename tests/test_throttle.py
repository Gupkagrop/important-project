"""Модульные тесты для декоратора throttle."""

import time
from typing import Any

import pytest

from pocket_toolkit.decorators.throttle import throttle


def test_throttle_leading_execution() -> None:
    """Проверка немедленного выполнения первого вызова при leading=True."""
    calls: list[int] = []

    @throttle(interval=0.08, leading=True, trailing=False)
    def fn(x: int) -> int:
        calls.append(x)
        return x

    assert fn(1) == 1
    # Повторный вызов внутри 80 мс игнорируется и возвращает результат первого вызова
    assert fn(2) == 1
    assert calls == [1]

    time.sleep(0.1)
    # По прошествии интервала вызов снова выполняется
    assert fn(3) == 3
    assert calls == [1, 3]


def test_throttle_trailing_execution() -> None:
    """Проверка выполнения отложенного вызова trailing по окончании интервала."""
    calls: list[int] = []

    @throttle(interval=0.06, leading=True, trailing=True)
    def fn(x: int) -> int:
        calls.append(x)
        return x

    assert fn(1) == 1  # leading
    fn(2)  # trailing запланирован
    fn(3)  # trailing обновлен аргументом 3

    assert calls == [1]

    time.sleep(0.09)
    # trailing выполнился с последним аргументом 3
    assert calls == [1, 3]


def test_throttle_leading_false() -> None:
    """Проверка работы при leading=False и trailing=True."""
    calls: list[int] = []

    @throttle(interval=0.06, leading=False, trailing=True)
    def fn(x: int) -> int:
        calls.append(x)
        return x

    assert fn(10) is None
    assert calls == []

    time.sleep(0.09)
    assert calls == [10]


def test_throttle_cancel_and_flush() -> None:
    """Проверка методов cancel() и flush()."""
    calls: list[int] = []

    @throttle(interval=0.5, leading=True, trailing=True)
    def fn(x: int) -> int:
        calls.append(x)
        return x

    wrapper: Any = fn
    wrapper(1)  # leading
    wrapper(2)  # trailing

    assert calls == [1]
    wrapper.cancel()
    time.sleep(0.05)
    assert calls == [1]  # trailing был отменен

    # Проверка flush
    wrapper(3)
    wrapper.flush()
    assert calls == [1, 3]


def test_throttle_validation() -> None:
    """Проверка валидации аргументов throttle."""
    with pytest.raises(ValueError):
        throttle(interval=0)
    with pytest.raises(ValueError):
        throttle(interval=-1)
    with pytest.raises(ValueError):
        throttle(interval=0.1, leading=False, trailing=False)
