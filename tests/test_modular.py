"""Модульные тесты для модуля модулярной арифметики (modular)."""

import pytest

from pocket_toolkit.algorithms.modular import (
    chinese_remainder_theorem,
    extended_gcd,
    fast_power,
    is_coprime,
    mod_add,
    mod_div,
    mod_mul,
    mod_sub,
    modular_inverse,
)


def test_fast_power() -> None:
    """Проверка быстрого бинарного возведения в степень."""
    assert fast_power(2, 0) == 1
    assert fast_power(2, 10) == 1024
    assert fast_power(5, 3) == 125
    assert fast_power(0, 5) == 0

    # С модулем
    assert fast_power(3, 13, 100) == pow(3, 13, 100)
    assert fast_power(7, 256, 13) == pow(7, 256, 13)
    assert fast_power(10, 5, 1) == 0

    # Ошибочные аргументы
    with pytest.raises(ValueError):
        fast_power(2, -1)
    with pytest.raises(ValueError):
        fast_power(2, 5, 0)
    with pytest.raises(ValueError):
        fast_power(2, 5, -10)


def test_extended_gcd() -> None:
    """Проверка расширенного алгоритма Евклида."""
    cases = [(35, 15), (240, 46), (17, 31), (100, 10), (0, 5), (7, 0)]
    for a, b in cases:
        g, x, y = extended_gcd(a, b)
        assert a * x + b * y == g
        if a != 0 or b != 0:
            assert g > 0

    # Нулевой случай
    assert extended_gcd(0, 0) == (0, 0, 0)


def test_is_coprime() -> None:
    """Проверка взаимной простоты чисел."""
    assert is_coprime(14, 15) is True
    assert is_coprime(17, 31) is True
    assert is_coprime(14, 21) is False
    assert is_coprime(100, 25) is False


def test_modular_inverse() -> None:
    """Проверка вычисления мультипликативного обратного по модулю."""
    # 3 * 4 = 12 = 1 (mod 11)
    assert modular_inverse(3, 11) == 4
    # 7 * 8 = 56 = 1 (mod 11)
    assert modular_inverse(7, 11) == 8

    # Проверка (a * inv(a)) % m == 1
    for a in [2, 5, 7, 9, 10]:
        inv = modular_inverse(a, 13)
        assert (a * inv) % 13 == 1

    # Не существует обратного (числа не взаимно просты)
    with pytest.raises(ValueError):
        modular_inverse(6, 9)

    # Некорректный модуль
    with pytest.raises(ValueError):
        modular_inverse(5, 1)
    with pytest.raises(ValueError):
        modular_inverse(5, -5)


def test_modular_basic_operations() -> None:
    """Проверка модульного сложения, вычитания, умножения и деления."""
    m = 17
    assert mod_add(10, 12, m) == (10 + 12) % m
    assert mod_sub(5, 12, m) == (5 - 12) % m
    assert mod_mul(7, 8, m) == (7 * 8) % m

    # Деление: 10 / 2 (mod 17) = 5
    assert mod_div(10, 2, m) == 5
    # (a / b) * b == a (mod m)
    div_res = mod_div(14, 3, m)
    assert (div_res * 3) % m == 14

    with pytest.raises(ValueError):
        mod_add(1, 2, 0)


def test_chinese_remainder_theorem() -> None:
    """Проверка решения систем сравнений по китайской теореме об остатках."""
    # Классическая задача Сунь Цзы:
    # x = 2 (mod 3)
    # x = 3 (mod 5)
    # x = 2 (mod 7)
    # Ответ: x = 23 (mod 105)
    ans = chinese_remainder_theorem([2, 3, 2], [3, 5, 7])
    assert ans == 23
    assert ans % 3 == 2
    assert ans % 5 == 3
    assert ans % 7 == 2

    # Одиночное сравнение
    assert chinese_remainder_theorem([4], [9]) == 4


def test_chinese_remainder_theorem_errors() -> None:
    """Проверка валидации китайской теоремы об остатках."""
    # Несовпадение длин
    with pytest.raises(ValueError):
        chinese_remainder_theorem([1, 2], [3])

    # Пустые входные списки
    with pytest.raises(ValueError):
        chinese_remainder_theorem([], [])

    # Модули не взаимно просты (4 и 6 делятся на 2)
    with pytest.raises(ValueError):
        chinese_remainder_theorem([1, 2], [4, 6])

    # Модуль <= 1
    with pytest.raises(ValueError):
        chinese_remainder_theorem([0], [1])
