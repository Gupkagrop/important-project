"""Модуль каррирования функций (Function Currying).

Предоставляет утилиту `curry` для преобразования функции от N аргументов в цепочку
одноместных или частичных функций, сохраняющих аргументы до достижения необходимой арности,
а также обратную утилиту `uncurry`.
"""

from collections.abc import Callable
import functools
import inspect
from typing import Any


def _get_required_arity(func: Callable[..., object]) -> int:
    """Определяет количество обязательных позиционных аргументов функции через inspect.signature."""
    sig = inspect.signature(func)
    arity = 0
    for param in sig.parameters.values():
        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            if param.default is inspect.Parameter.empty:
                arity += 1
    return arity


class Curried:
    """Обертка каррированной функции, поддерживающая пошаговое применение аргументов."""

    __slots__ = ("_args", "_arity", "_doc", "_func", "_kwargs", "_name")

    def __init__(
        self,
        func: Callable[..., object],
        arity: int,
        args: tuple[object, ...] = (),
        kwargs: dict[str, object] | None = None,
    ) -> None:
        """Инициализирует каррированную функцию.

        :param func: Целевая функция.
        :param arity: Требуемое количество аргументов для выполнения.
        :param args: Уже накопленные позиционные аргументы.
        :param kwargs: Уже накопленные именованные аргументы.
        """
        self._func: Callable[..., object] = func
        self._arity: int = arity
        self._args: tuple[object, ...] = args
        self._kwargs: dict[str, object] = dict(kwargs) if kwargs is not None else {}
        self._doc: str | None = getattr(func, "__doc__", None)
        self._name: str = getattr(func, "__name__", "curried")

    @property
    def __doc__(self) -> str | None:
        """Документация исходной функции."""
        return self._doc

    @property
    def __name__(self) -> str:
        """Имя исходной функции."""
        return self._name

    @property
    def arity(self) -> int:
        """Целевая арность функции."""
        return self._arity

    def __call__(self, *more_args: object, **more_kwargs: object) -> object:
        """Принимает порцию аргументов.

        Если суммарное число позиционных и переданных именованных аргументов достигает arity,
        вызывает целевую функцию. Иначе возвращает новый экземпляр Curried с накопленными данными.
        """
        new_args = self._args + more_args
        new_kwargs = dict(self._kwargs)
        new_kwargs.update(more_kwargs)

        total_args_count = len(new_args) + len(new_kwargs)

        if total_args_count >= self._arity:
            return self._func(*new_args, **new_kwargs)

        return Curried(self._func, self._arity, new_args, new_kwargs)

    def __repr__(self) -> str:
        """Строковое представление каррированной функции."""
        accumulated = len(self._args) + len(self._kwargs)
        return f"Curried({self._func.__name__}, arity={self._arity}, accumulated={accumulated})"


def curry(func: Callable[..., object], arity: int | None = None) -> Curried:
    """Преобразует функцию многих аргументов в каррированную функцию.

    :param func: Исходная функция.
    :param arity: Явно заданная арность (если None, определяется автоматически по сигнатуре).
    :return: Экземпляр `Curried`.
    :raises ValueError: Если арность меньше 1.
    """
    effective_arity = arity if arity is not None else _get_required_arity(func)
    if effective_arity < 1:
        raise ValueError(
            f"Арность функции должна быть >= 1, определено/получено: {effective_arity}"
        )

    return Curried(func, effective_arity)


def uncurry(func: Callable[..., object]) -> Callable[[tuple[object, ...]], object]:
    """Преобразует каррированную функцию в функцию, принимающую кортеж аргументов.

    :param func: Каррированная функция.
    :return: Обертка, принимающая кортеж `args_tuple` и разворачивающая его в вызов func.
    """
    def uncurried(args_tuple: tuple[object, ...]) -> object:
        current: object = func
        for arg in args_tuple:
            if callable(current):
                current = current(arg)
            else:
                break
        return current

    return uncurried
