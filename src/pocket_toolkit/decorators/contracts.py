"""Модуль контрактов и валидации сигнатур (Contracts & Deprecation).

Предоставляет декоратор `@deprecated` для маркировки устаревшего API с генерацией предупреждений
и обновлением docstrings, а также декоратор `@validate_types` для строгой проверки типов
аргументов и возвращаемых значений во время выполнения.
"""

from collections.abc import Callable
import functools
import inspect
from typing import Any, ParamSpec, TypeVar, get_args, get_origin
import warnings

P = ParamSpec("P")
R = TypeVar("R")


def deprecated(
    since: str | None = None,
    removed_in: str | None = None,
    alternative: str | None = None,
    category: type[Warning] = DeprecationWarning,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор для пометки функций и методов как устаревших (deprecated).

    Генерирует предупреждение при вызове и дополняет docstring описанием устаревания.

    :param since: Версия, в которой API объявлен устаревшим.
    :param removed_in: Версия, в которой API будет окончательно удален.
    :param alternative: Рекомендуемая замена или альтернативный метод.
    :param category: Категория предупреждения (по умолчанию DeprecationWarning).
    :return: Декорированная функция.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        message_parts = [f"Функция {func.__name__} устарела"]
        if since:
            message_parts.append(f"начиная с версии {since}")
        if removed_in:
            message_parts.append(f"и будет удалена в версии {removed_in}")
        if alternative:
            message_parts.append(f". Используйте вместо нее {alternative}")
        message = " ".join(message_parts) + "."

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            warnings.warn(message, category=category, stacklevel=2)
            return func(*args, **kwargs)

        doc = wrapper.__doc__ or ""
        deprecation_note = f"\n\n.. deprecated:: {since or ''}\n    {message}"
        wrapper.__doc__ = doc + deprecation_note

        return wrapper

    return decorator


def _check_type(value: object, expected_type: object) -> bool:
    """Рекурсивно проверяет соответствие значения ожидаемому типу/аннотации."""
    if expected_type is Any or expected_type is object:
        return True

    origin = get_origin(expected_type)

    # Обработка Union / | / Optional
    if origin is not None and (origin is type(int | str) or str(origin).endswith("Union")):
        args = get_args(expected_type)
        return any(_check_type(value, arg) for arg in args)

    # Обычный базовый класс или тип
    if isinstance(expected_type, type):
        return isinstance(value, expected_type)

    return True


def validate_types(
    validate_return: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор валидации типов аргументов и возвращаемого значения по аннотациям в runtime.

    :param validate_return: Проверять ли также тип возвращаемого значения.
    :return: Декорированная функция.
    :raises TypeError: При несоответствии типа фактического значения объявленной аннотации.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Валидация входных аргументов
            for name, val in bound.arguments.items():
                param = sig.parameters.get(name)
                if param is not None and param.annotation is not inspect.Parameter.empty:
                    expected = param.annotation
                    if not _check_type(val, expected):
                        raise TypeError(
                            f"Неверный тип аргумента '{name}': ожидался {expected}, "
                            f"получено {type(val).__name__} ({val!r})"
                        )

            result = func(*args, **kwargs)

            # Валидация возвращаемого значения
            if validate_return and sig.return_annotation is not inspect.Signature.empty:
                expected_ret = sig.return_annotation
                if not _check_type(result, expected_ret):
                    raise TypeError(
                        f"Неверный тип возвращаемого значения функции '{func.__name__}': "
                        f"ожидался {expected_ret}, получено {type(result).__name__} ({result!r})"
                    )

            return result

        return wrapper

    return decorator
