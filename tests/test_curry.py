"""Модульные тесты для модуля каррирования функций (curry)."""

import pytest
from pocket_toolkit.functional.curry import Curried, curry, uncurry


def test_curry_binary_function() -> None:
    """Проверка каррирования функции двух переменных."""
    def add(a: int, b: int) -> int:
        return a + b

    curried_add = curry(add)
    assert curried_add.arity == 2

    # Пошаговый вызов
    add_five = curried_add(5)
    assert isinstance(add_five, Curried)
    assert add_five(3) == 8

    # Прямой вызов с несколькими аргументами
    assert curried_add(10, 20) == 30


def test_curry_ternary_function_combinations() -> None:
    """Проверка различных комбинаций передачи аргументов в функцию трех переменных."""
    def volume(l: int, w: int, h: int) -> int:
        return l * w * h

    curried_vol = curry(volume)
    assert curried_vol.arity == 3

    assert curried_vol(2)(3)(4) == 24
    assert curried_vol(2, 3)(4) == 24
    assert curried_vol(2)(3, 4) == 24
    assert curried_vol(2, 3, 4) == 24


def test_curry_with_kwargs() -> None:
    """Проверка работы с именованными аргументами."""
    def greet(greeting: str, name: str) -> str:
        return f"{greeting}, {name}!"

    curried_greet = curry(greet)
    say_hello = curried_greet("Hello")
    assert say_hello(name="World") == "Hello, World!"


def test_curry_explicit_arity() -> None:
    """Проверка явного задания арности для функций с переменным числом аргументов."""
    def sum_all(*args: int) -> int:
        return sum(args)

    curried_sum = curry(sum_all, arity=3)
    assert curried_sum(1)(2)(3) == 6


def test_uncurry() -> None:
    """Проверка функции uncurry."""
    def multiply(x: int, y: int) -> int:
        return x * y

    curried_mul = curry(multiply)
    uncurried_mul = uncurry(curried_mul)

    assert uncurried_mul((3, 7)) == 21


def test_curry_validation() -> None:
    """Проверка валидации арности."""
    def no_args() -> str:
        return "empty"

    with pytest.raises(ValueError):
        curry(no_args)
    with pytest.raises(ValueError):
        curry(lambda x: x, arity=0)
