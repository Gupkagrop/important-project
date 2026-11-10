"""Модуль функциональной композиции и конвейерной обработки (Pipe & Compose).

Предоставляет функции `pipe` для последовательной передачи значения через цепочку функций,
`compose` для математической композиции функций справа налево (f ∘ g),
`compose_left` для композиции слева направо, а также класс `Pipeline` для fluent-синтаксиса.
"""

from collections.abc import Callable
import functools
from typing import ParamSpec, TypeVar

T = TypeVar("T")
U = TypeVar("U")
P = ParamSpec("P")
R = TypeVar("R")


def pipe(initial: object, *funcs: Callable[[object], object]) -> object:
    """Пропускает начальное значение через последовательную цепочку функций слева направо.

    :param initial: Исходное значение.
    :param funcs: Функции преобразования, применяемые последовательно.
    :return: Итоговый результат преобразований.
    """
    result = initial
    for fn in funcs:
        result = fn(result)
    return result


def compose(*funcs: Callable[[object], object]) -> Callable[..., object]:
    """Создает новую функцию как математическую композицию переданных функций (справа налево).

    (compose(f, g, h))(x) эквивалентно f(g(h(x))).

    :param funcs: Последовательность функций для композиции.
    :return: Скомпонованная функция.
    :raises ValueError: Если не передано ни одной функции.
    """
    if not funcs:
        raise ValueError("Для композиции compose требуется хотя бы одна функция")

    def composed(*args: object, **kwargs: object) -> object:
        # Самая правая функция может принимать произвольные позиционные и именованные аргументы
        first_func = funcs[-1]
        result = first_func(*args, **kwargs)

        for fn in reversed(funcs[:-1]):
            result = fn(result)

        return result

    return composed


def compose_left(*funcs: Callable[[object], object]) -> Callable[..., object]:
    """Создает новую функцию как композицию переданных функций слева направо.

    (compose_left(f, g, h))(x) эквивалентно h(g(f(x))).

    :param funcs: Последовательность функций.
    :return: Скомпонованная функция.
    :raises ValueError: Если не передано ни одной функции.
    """
    if not funcs:
        raise ValueError("Для композиции compose_left требуется хотя бы одна функция")

    def composed(*args: object, **kwargs: object) -> object:
        first_func = funcs[0]
        result = first_func(*args, **kwargs)

        for fn in funcs[1:]:
            result = fn(result)

        return result

    return composed


class Pipeline[T]:
    """Объектный конвейер преобразования данных с цепочечным синтаксисом (fluent interface)."""

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        """Инициализирует конвейер начальным значением.

        :param value: Исходное значение.
        """
        self._value: T = value

    @property
    def value(self) -> T:
        """Текущее значение конвейера."""
        return self._value

    def unwrap(self) -> T:
        """Извлекает итоговое значение из конвейера."""
        return self._value

    def then[U](self, func: Callable[[T], U]) -> "Pipeline[U]":
        """Применяет функцию преобразования к текущему значению.

        :param func: Функция преобразования T -> U.
        :return: Новый экземпляр Pipeline[U].
        """
        return Pipeline(func(self._value))

    def tap(self, effect: Callable[[T], object]) -> "Pipeline[T]":
        """Выполняет побочный эффект (логирование, инспекция) без изменения значения.

        :param effect: Функция с побочным действием.
        :return: Текущий Pipeline с неизменным значением.
        """
        effect(self._value)
        return self

    def __repr__(self) -> str:
        """Строковое представление конвейера."""
        return f"Pipeline({self._value!r})"
