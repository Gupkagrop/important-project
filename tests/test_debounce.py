"""Модульные тесты для декоратора debounce."""

import time
from typing import Any
import pytest
from pocket_toolkit.decorators.debounce import debounce


def test_debounce_executes_after_delay() -> None:
    """Проверка выполнения функции после истечения паузы тишины."""
    results: list[int] = []

    @debounce(wait=0.05)
    def push(val: int) -> None:
        results.append(val)

    push(1)
    push(2)
    push(3)

    assert results == []  # Еще не выполнено
    time.sleep(0.1)
    # Выполнился только последний вызов с аргументом 3
    assert results == [3]


def test_debounce_cancel() -> None:
    """Проверка отмены отложенного вызова методом cancel()."""
    executed = False

    @debounce(wait=0.05)
    def action() -> None:
        nonlocal executed
        executed = True

    wrapper: Any = action
    wrapper()
    assert wrapper.is_pending() is True
    wrapper.cancel()
    assert wrapper.is_pending() is False

    time.sleep(0.08)
    assert executed is False


def test_debounce_flush() -> None:
    """Проверка принудительного немедленного выполнения методом flush()."""
    log: list[str] = []

    @debounce(wait=0.5)
    def log_msg(msg: str) -> None:
        log.append(msg)

    wrapper: Any = log_msg
    wrapper("hello")
    assert log == []

    wrapper.flush()
    assert log == ["hello"]
    assert wrapper.is_pending() is False


def test_debounce_max_wait() -> None:
    """Проверка гарантированного срабатывания по max_wait."""
    calls: list[int] = []

    @debounce(wait=0.04, max_wait=0.08)
    def add(x: int) -> None:
        calls.append(x)

    # Непрерывно дергаем функцию быстрее, чем wait=0.04
    for i in range(5):
        add(i)
        time.sleep(0.02)

    # За счет max_wait=0.08 функция должна была гарантированно выполниться
    assert len(calls) >= 1


def test_debounce_validation() -> None:
    """Проверка валидации параметров декоратора debounce."""
    with pytest.raises(ValueError):
        debounce(wait=0)
    with pytest.raises(ValueError):
        debounce(wait=-1)
    with pytest.raises(ValueError):
        debounce(wait=0.5, max_wait=0.2)
