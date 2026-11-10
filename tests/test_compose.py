"""Модульные тесты для утилит pipe, compose и Pipeline."""

import pytest
from pocket_toolkit.functional.compose import (
    Pipeline,
    compose,
    compose_left,
    pipe,
)


def test_pipe_evaluation() -> None:
    """Проверка последовательной передачи значения через pipe."""
    assert pipe(5) == 5

    res = pipe(
        5,
        lambda x: x + 1,      # 6
        lambda x: x * 2,      # 12
        lambda x: f"num_{x}", # "num_12"
    )
    assert res == "num_12"


def test_compose_right_to_left() -> None:
    """Проверка математической композиции функций справа налево."""
    def add_one(x: int) -> int:
        return x + 1

    def double(x: int) -> int:
        return x * 2

    # (compose(add_one, double))(3) = add_one(double(3)) = 3*2 + 1 = 7
    fn = compose(add_one, double)
    assert fn(3) == 7

    # Поддержка нескольких аргументов в первой функции
    def multiply(a: int, b: int) -> int:
        return a * b

    fn_multi = compose(add_one, multiply)
    assert fn_multi(3, 4) == 13


def test_compose_left() -> None:
    """Проверка композиции функций слева направо."""
    def add_one(x: int) -> int:
        return x + 1

    def double(x: int) -> int:
        return x * 2

    # (compose_left(add_one, double))(3) = double(add_one(3)) = (3 + 1) * 2 = 8
    fn = compose_left(add_one, double)
    assert fn(3) == 8


def test_compose_empty_errors() -> None:
    """Проверка ошибки при пустом наборе функций в compose."""
    with pytest.raises(ValueError):
        compose()
    with pytest.raises(ValueError):
        compose_left()


def test_pipeline_chaining_and_tap() -> None:
    """Проверка объектного конвейера Pipeline и побочных эффектов tap()."""
    tapped: list[int] = []

    result = (
        Pipeline(10)
        .then(lambda x: x + 5)
        .tap(lambda x: tapped.append(x))
        .then(lambda x: x * 2)
        .unwrap()
    )

    assert result == 30
    assert tapped == [15]

    p = Pipeline("test")
    assert "Pipeline('test')" in repr(p)
    assert p.value == "test"
