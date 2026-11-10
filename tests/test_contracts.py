"""Модульные тесты для модуля контрактов и депрекации (contracts)."""

import warnings

import pytest

from pocket_toolkit.decorators.contracts import deprecated, validate_types


def test_deprecated_warning_and_docstring() -> None:
    """Проверка генерации предупреждения и обновления docstring при @deprecated."""
    @deprecated(since="1.2.0", removed_in="2.0.0", alternative="new_func")
    def old_func() -> str:
        """Старая функция."""
        return "result"

    assert "deprecated" in (old_func.__doc__ or "")
    assert "new_func" in (old_func.__doc__ or "")

    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        res = old_func()
        assert res == "result"
        assert len(recorded) == 1
        assert issubclass(recorded[0].category, DeprecationWarning)
        assert "old_func устарела" in str(recorded[0].message)


def test_validate_types_success() -> None:
    """Проверка успешного прохождения вызова с корректными типами."""
    @validate_types()
    def add(a: int, b: int) -> int:
        return a + b

    assert add(10, 20) == 30


def test_validate_types_argument_mismatch() -> None:
    """Проверка выброса TypeError при несоответствии типа аргумента."""
    @validate_types()
    def multiply(x: int, y: int) -> int:
        return x * y

    with pytest.raises(TypeError) as exc_info:
        multiply("10", 2)  # type: ignore[arg-type]

    assert "Неверный тип аргумента 'x'" in str(exc_info.value)


def test_validate_types_return_mismatch() -> None:
    """Проверка выброса TypeError при несоответствии типа возвращаемого значения."""
    @validate_types(validate_return=True)
    def bad_return() -> int:
        return "not an int"  # type: ignore[return-value]

    with pytest.raises(TypeError) as exc_info:
        bad_return()

    assert "Неверный тип возвращаемого значения" in str(exc_info.value)


def test_validate_types_union() -> None:
    """Проверка поддержки Union / объединения типов (A | B)."""
    @validate_types()
    def format_val(val: int | str) -> str:
        return str(val)

    assert format_val(123) == "123"
    assert format_val("abc") == "abc"

    with pytest.raises(TypeError):
        format_val(12.34)  # type: ignore[arg-type]
