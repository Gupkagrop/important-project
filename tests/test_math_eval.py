"""Модульные тесты для модуля безопасного вычисления математических выражений (math_eval)."""

import math

import pytest

from pocket_toolkit.data.math_eval import (
    MathEvaluationError,
    MathSecurityError,
    UndefinedSymbolError,
    evaluate_math,
)


def test_basic_arithmetic() -> None:
    """Проверка базовых арифметических операций и приоритета."""
    assert evaluate_math("2 + 3 * 4") == 14.0
    assert evaluate_math("(2 + 3) * 4") == 20.0
    assert evaluate_math("10 / 2 + 1") == 6.0
    assert evaluate_math("10 // 3") == 3.0
    assert evaluate_math("10 % 3") == 1.0
    assert evaluate_math("2 ** 3") == 8.0
    assert evaluate_math("2 ^ 3") == 8.0
    assert evaluate_math("-5 + +3") == -2.0


def test_variables_and_constants() -> None:
    """Проверка подстановки переменных и встроенных констант."""
    assert evaluate_math("2 * x + y", variables={"x": 5, "y": 3}) == 13.0
    assert evaluate_math("pi * r ^ 2", variables={"r": 2}) == pytest.approx(math.pi * 4)
    assert evaluate_math("e + 1") == pytest.approx(math.e + 1)


def test_functions_and_custom_functions() -> None:
    """Проверка встроенных и пользовательских функций."""
    assert evaluate_math("sqrt(16) + abs(-4)") == 8.0
    assert evaluate_math("min(10, 5, 20)") == 5.0
    assert evaluate_math("max(10, 5, 20)") == 20.0
    assert evaluate_math("round(3.7)") == 4.0

    # Пользовательская функция
    custom_funcs = {"double": lambda x: x * 2}
    assert evaluate_math("double(7) + 1", functions=custom_funcs) == 15.0


def test_division_by_zero() -> None:
    """Проверка деления на ноль."""
    with pytest.raises(MathEvaluationError, match="Деление на ноль"):
        evaluate_math("10 / 0")

    with pytest.raises(MathEvaluationError, match="Деление на ноль"):
        evaluate_math("10 // 0")

    with pytest.raises(MathEvaluationError, match="Деление на ноль"):
        evaluate_math("10 % 0")


def test_undefined_symbols() -> None:
    """Проверка обращения к необъявленным переменным или функциям."""
    with pytest.raises(UndefinedSymbolError, match="Неопределенная переменная: 'unknown_var'"):
        evaluate_math("unknown_var + 1")

    with pytest.raises(UndefinedSymbolError, match="Неизвестная функция: 'unknown_func'"):
        evaluate_math("unknown_func(1)")


def test_security_restrictions() -> None:
    """Проверка блокировки опасных конструкций (Security)."""
    # Запрет строковых литералов
    with pytest.raises(MathSecurityError):
        evaluate_math("'hello' + 'world'")

    # Запрет доступа к атрибутам
    with pytest.raises(MathSecurityError):
        evaluate_math("x.__class__", variables={"x": 10})

    # Запрет списков и генераторов
    with pytest.raises(MathSecurityError):
        evaluate_math("[x for x in (1, 2)]")

    # Запрет вызова произвольных объектов (например lambda или chained calls)
    with pytest.raises(MathSecurityError):
        evaluate_math("(lambda x: x)(1)")


def test_syntax_and_input_validation() -> None:
    """Проверка синтаксических ошибок и валидации аргументов."""
    with pytest.raises(TypeError):
        evaluate_math(123)  # type: ignore[arg-type]

    with pytest.raises(MathEvaluationError):
        evaluate_math("")

    with pytest.raises(MathEvaluationError):
        evaluate_math("2 +* 3")
