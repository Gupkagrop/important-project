"""Модуль модульной арифметики и быстрого возведения в степень (Modular Arithmetic).

Предоставляет функции бинарного возведения в степень за O(log n),
расширенного алгоритма Евклида (Extended GCD), вычисления мультипликативного
обратного по модулю, решения систем сравнений по китайской теореме об остатках (CRT)
и базовых операций модулярной арифметики.
"""

import math
from collections.abc import Sequence


def fast_power(base: int, exp: int, modulus: int | None = None) -> int:
    """Вычисляет (base ** exp) или (base ** exp) % modulus с помощью бинарного возведения в степень.

    Временная сложность: O(log exp).

    :param base: Основание степени.
    :param exp: Показатель степени (должен быть >= 0).
    :param modulus: Опциональный модуль (> 0).
    :return: Результат возведения в степень.
    :raises ValueError: Если показатель отрицательный или модуль <= 0.
    """
    if exp < 0:
        raise ValueError(f"Показатель степени exp должен быть неотрицательным (>= 0), получено: {exp}")
    if modulus is not None and modulus <= 0:
        raise ValueError(f"Модуль должен быть строго положительным (> 0), получено: {modulus}")

    if modulus == 1:
        return 0

    result: int = 1
    current_base: int = base if modulus is None else (base % modulus)
    current_exp: int = exp

    while current_exp > 0:
        if current_exp & 1:
            result = (result * current_base) if modulus is None else ((result * current_base) % modulus)
        current_base = (
            (current_base * current_base)
            if modulus is None
            else ((current_base * current_base) % modulus)
        )
        current_exp >>= 1

    return result


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Вычисляет расширенный наибольший общий делитель: a * x + b * y = gcd(a, b).

    :param a: Первое целое число.
    :param b: Второе целое число.
    :return: Кортеж (g, x, y), где g = gcd(a, b), а x и y — коэффициенты Безу.
    """
    if a == 0 and b == 0:
        return 0, 0, 0

    x0, x1 = 1, 0
    y0, y1 = 0, 1

    curr_a, curr_b = abs(a), abs(b)

    while curr_b != 0:
        q = curr_a // curr_b
        curr_a, curr_b = curr_b, curr_a % curr_b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1

    # Корректируем знаки коэффициентов в соответствии с исходными знаками a и b
    final_x = x0 if a >= 0 else -x0
    final_y = y0 if b >= 0 else -y0

    return curr_a, final_x, final_y


def is_coprime(a: int, b: int) -> bool:
    """Проверяет, являются ли числа a и b взаимно простыми (gcd == 1)."""
    return math.gcd(a, b) == 1


def modular_inverse(a: int, modulus: int) -> int:
    """Вычисляет мультипликативный обратный элемент a^(-1) по модулю modulus.

    Находит целое x в диапазоне [0, modulus - 1], такое что (a * x) % modulus == 1.

    :param a: Исходное число.
    :param modulus: Модуль (должен быть > 1).
    :return: Обратный элемент по модулю.
    :raises ValueError: Если модуль <= 1 или числа a и modulus не взаимно просты.
    """
    if modulus <= 1:
        raise ValueError(f"Модуль должен быть строго больше 1, получено: {modulus}")

    g, x, _ = extended_gcd(a, modulus)
    if g != 1:
        raise ValueError(f"Число {a} не имеет обратного по модулю {modulus}: gcd({a}, {modulus}) = {g} != 1")

    return x % modulus


def mod_add(a: int, b: int, modulus: int) -> int:
    """Модульное сложение: (a + b) % modulus."""
    if modulus <= 0:
        raise ValueError("Модуль должен быть строго больше нуля")
    return (a + b) % modulus


def mod_sub(a: int, b: int, modulus: int) -> int:
    """Модульное вычитание: (a - b) % modulus."""
    if modulus <= 0:
        raise ValueError("Модуль должен быть строго больше нуля")
    return (a - b) % modulus


def mod_mul(a: int, b: int, modulus: int) -> int:
    """Модульное умножение: (a * b) % modulus."""
    if modulus <= 0:
        raise ValueError("Модуль должен быть строго больше нуля")
    return (a * b) % modulus


def mod_div(a: int, b: int, modulus: int) -> int:
    """Модульное деление: (a * b^(-1)) % modulus.

    :raises ValueError: Если делитель b не обратим по модулю modulus.
    """
    inv_b = modular_inverse(b, modulus)
    return (a * inv_b) % modulus


def chinese_remainder_theorem(remainders: Sequence[int], moduli: Sequence[int]) -> int:
    """Решает систему сравнений x = remainders[i] (mod moduli[i]) по китайской теореме об остатках.

    Все модули должны быть попарно взаимно просты и строго больше единицы.

    :param remainders: Список остатков r_i.
    :param moduli: Список попарно взаимно простых модулей m_i.
    :return: Минимальное неотрицательное решение x.
    :raises ValueError: При несовпадении длин списков или если модули не взаимно просты.
    """
    if len(remainders) != len(moduli):
        raise ValueError(
            f"Количество остатков ({len(remainders)}) должно совпадать с числом модулей ({len(moduli)})"
        )
    if not moduli:
        raise ValueError("Списки остатков и модулей не могут быть пустыми")

    # Проверяем корректность модулей и их попарную простоту
    for i in range(len(moduli)):
        if moduli[i] <= 1:
            raise ValueError(f"Все модули должны быть строго больше 1, получено: {moduli[i]}")
        for j in range(i + 1, len(moduli)):
            if math.gcd(moduli[i], moduli[j]) != 1:
                raise ValueError(
                    f"Модули должны быть попарно взаимно простыми: gcd({moduli[i]}, {moduli[j]}) != 1"
                )

    # Вычисляем произведение всех модулей M = m_1 * m_2 * ... * m_k
    total_m: int = 1
    for m in moduli:
        total_m *= m

    x: int = 0
    for r, m in zip(remainders, moduli, strict=True):
        m_i = total_m // m
        y_i = modular_inverse(m_i, m)
        x = (x + r * m_i * y_i) % total_m

    return x
