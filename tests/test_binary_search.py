"""Модульные тесты для утилит двоичного поиска (binary_search)."""

from dataclasses import dataclass

import pytest

from pocket_toolkit.algorithms.binary_search import (
    Comparable,
    binary_search,
    binary_search_last,
    binary_search_rotated,
    equal_range,
    lower_bound,
    upper_bound,
)


@dataclass(frozen=True)
class ScoreItem:
    """Вспомогательный класс для проверки работы функций с пользовательскими объектами."""

    name: str
    score: int


class CustomComparable:
    """Пользовательский класс, реализующий исключительно протокол Comparable (__lt__)."""

    def __init__(self, value: int) -> None:
        self.value: int = value

    def __lt__(self, other: "Comparable", /) -> bool:
        if isinstance(other, CustomComparable):
            return self.value < other.value
        return NotImplemented


class TestLowerBound:
    """Набор тестов для функции lower_bound."""

    def test_empty_sequence(self) -> None:
        """Проверяет вызов lower_bound на пустой последовательности."""
        assert lower_bound([], 10) == 0

    def test_single_element(self) -> None:
        """Проверяет вызов lower_bound на списке из одного элемента."""
        assert lower_bound([5], 3) == 0
        assert lower_bound([5], 5) == 0
        assert lower_bound([5], 7) == 1

    def test_target_smaller_than_all(self) -> None:
        """Проверяет поиск значения меньше любого элемента."""
        items: list[int] = [10, 20, 30, 40]
        assert lower_bound(items, 5) == 0

    def test_target_greater_than_all(self) -> None:
        """Проверяет поиск значения больше любого элемента."""
        items: list[int] = [10, 20, 30, 40]
        assert lower_bound(items, 50) == 4

    def test_exact_match_unique(self) -> None:
        """Проверяет нахождение точного элемента без дубликатов."""
        items: list[int] = [1, 3, 5, 7, 9]
        assert lower_bound(items, 5) == 2

    def test_exact_match_duplicates(self) -> None:
        """Проверяет, что lower_bound возвращает индекс первого дубликата."""
        items: list[int] = [1, 2, 4, 4, 4, 6, 7]
        assert lower_bound(items, 4) == 2

    def test_element_not_present_intermediate(self) -> None:
        """Проверяет точку вставки для отсутствующего промежуточного элемента."""
        items: list[int] = [10, 20, 30, 40]
        assert lower_bound(items, 25) == 2

    def test_custom_bounds(self) -> None:
        """Проверяет ограничение диапазона поиска параметрами lo и hi."""
        items: list[int] = [1, 3, 5, 7, 9, 11]
        assert lower_bound(items, 7, lo=2, hi=5) == 3
        assert lower_bound(items, 1, lo=2, hi=5) == 2
        assert lower_bound(items, 20, lo=2, hi=5) == 5

    def test_with_key_function(self) -> None:
        """Проверяет работу lower_bound с функцией извлечения ключа."""
        items: list[ScoreItem] = [
            ScoreItem("Alice", 50),
            ScoreItem("Bob", 70),
            ScoreItem("Charlie", 70),
            ScoreItem("Diana", 90),
        ]
        idx: int = lower_bound(items, 70, key=lambda item: item.score)
        assert idx == 1
        assert items[idx].name == "Bob"

    def test_with_custom_comparable(self) -> None:
        """Проверяет работу с объектами, реализующими только __lt__."""
        items: list[CustomComparable] = [
            CustomComparable(2),
            CustomComparable(4),
            CustomComparable(6),
        ]
        target = CustomComparable(4)
        assert lower_bound(items, target) == 1

    def test_tuple_sequence(self) -> None:
        """Проверяет поддержку кортежей как Sequence."""
        items: tuple[int, ...] = (1, 2, 4, 8, 16)
        assert lower_bound(items, 4) == 2


class TestUpperBound:
    """Набор тестов для функции upper_bound."""

    def test_empty_sequence(self) -> None:
        """Проверяет вызов upper_bound на пустой последовательности."""
        assert upper_bound([], 10) == 0

    def test_single_element(self) -> None:
        """Проверяет вызов upper_bound на списке из одного элемента."""
        assert upper_bound([5], 3) == 0
        assert upper_bound([5], 5) == 1
        assert upper_bound([5], 7) == 1

    def test_target_smaller_than_all(self) -> None:
        """Проверяет верхнюю границу для значения меньше всех элементов."""
        items: list[int] = [10, 20, 30, 40]
        assert upper_bound(items, 5) == 0

    def test_target_greater_than_all(self) -> None:
        """Проверяет верхнюю границу для значения больше всех элементов."""
        items: list[int] = [10, 20, 30, 40]
        assert upper_bound(items, 50) == 4

    def test_exact_match_unique(self) -> None:
        """Проверяет верхнюю границу для уникального элемента."""
        items: list[int] = [1, 3, 5, 7, 9]
        assert upper_bound(items, 5) == 3

    def test_exact_match_duplicates(self) -> None:
        """Проверяет, что upper_bound возвращает индекс за последним дубликатом."""
        items: list[int] = [1, 2, 4, 4, 4, 6, 7]
        assert upper_bound(items, 4) == 5

    def test_element_not_present_intermediate(self) -> None:
        """Проверяет верхнюю границу для отсутствующего промежуточного элемента."""
        items: list[int] = [10, 20, 30, 40]
        assert upper_bound(items, 25) == 2

    def test_custom_bounds(self) -> None:
        """Проверяет поиск с явными границами lo и hi."""
        items: list[int] = [1, 3, 5, 7, 9, 11]
        assert upper_bound(items, 7, lo=1, hi=4) == 4
        assert upper_bound(items, 3, lo=2, hi=5) == 2

    def test_with_key_function(self) -> None:
        """Проверяет upper_bound с функцией извлечения ключа."""
        items: list[ScoreItem] = [
            ScoreItem("Alice", 50),
            ScoreItem("Bob", 70),
            ScoreItem("Charlie", 70),
            ScoreItem("Diana", 90),
        ]
        idx: int = upper_bound(items, 70, key=lambda item: item.score)
        assert idx == 3
        assert items[idx].name == "Diana"


class TestEqualRange:
    """Набор тестов для функции equal_range."""

    def test_multiple_occurrences(self) -> None:
        """Проверяет границы диапазона для повторяющихся значений."""
        items: list[int] = [1, 2, 3, 3, 3, 4, 5]
        first, last = equal_range(items, 3)
        assert (first, last) == (2, 5)
        assert items[first:last] == [3, 3, 3]

    def test_single_occurrence(self) -> None:
        """Проверяет границы диапазона для уникального элемента."""
        items: list[int] = [10, 20, 30, 40]
        assert equal_range(items, 30) == (2, 3)

    def test_missing_element(self) -> None:
        """Проверяет, что для отсутствующего элемента first == last."""
        items: list[int] = [10, 20, 30, 40]
        assert equal_range(items, 25) == (2, 2)

    def test_empty_sequence(self) -> None:
        """Проверяет equal_range на пустой последовательности."""
        assert equal_range([], 42) == (0, 0)

    def test_with_key_function(self) -> None:
        """Проверяет equal_range с передачей key."""
        items: list[ScoreItem] = [
            ScoreItem("A", 10),
            ScoreItem("B", 20),
            ScoreItem("C", 20),
            ScoreItem("D", 30),
        ]
        first, last = equal_range(items, 20, key=lambda x: x.score)
        assert (first, last) == (1, 3)


class TestBinarySearch:
    """Набор тестов для функции binary_search."""

    def test_empty_sequence(self) -> None:
        """Проверяет поиск в пустой последовательности."""
        assert binary_search([], 10) == -1

    def test_element_found_unique(self) -> None:
        """Проверяет успешный поиск уникального элемента."""
        items: list[int] = [2, 4, 6, 8, 10]
        assert binary_search(items, 6) == 2
        assert binary_search(items, 2) == 0
        assert binary_search(items, 10) == 4

    def test_element_found_first_occurrence(self) -> None:
        """Проверяет, что binary_search детерминированно возвращает первое вхождение."""
        items: list[int] = [1, 3, 3, 3, 5]
        assert binary_search(items, 3) == 1

    def test_element_not_found(self) -> None:
        """Проверяет возврат -1 при отсутствии элемента."""
        items: list[int] = [10, 20, 30, 40]
        assert binary_search(items, 5) == -1
        assert binary_search(items, 25) == -1
        assert binary_search(items, 50) == -1

    def test_with_custom_bounds(self) -> None:
        """Проверяет поиск с ограничением [lo, hi)."""
        items: list[int] = [1, 2, 3, 4, 5, 6]
        assert binary_search(items, 4, lo=1, hi=4) == 3
        assert binary_search(items, 4, lo=0, hi=3) == -1
        assert binary_search(items, 4, lo=4, hi=6) == -1

    def test_with_key_function(self) -> None:
        """Проверяет binary_search с функцией извлечения ключа."""
        items: list[ScoreItem] = [
            ScoreItem("Anna", 100),
            ScoreItem("Boris", 200),
            ScoreItem("Clara", 300),
        ]
        assert binary_search(items, 200, key=lambda x: x.score) == 1
        assert binary_search(items, 999, key=lambda x: x.score) == -1

    def test_with_custom_comparable(self) -> None:
        """Проверяет binary_search с объектами, реализующими только Comparable."""
        items: list[CustomComparable] = [
            CustomComparable(10),
            CustomComparable(20),
            CustomComparable(30),
        ]
        assert binary_search(items, CustomComparable(20)) == 1
        assert binary_search(items, CustomComparable(25)) == -1


class TestBinarySearchLast:
    """Набор тестов для функции binary_search_last."""

    def test_empty_sequence(self) -> None:
        """Проверяет поиск последнего вхождения в пустом списке."""
        assert binary_search_last([], 5) == -1

    def test_single_occurrence(self) -> None:
        """Проверяет поиск элемента, присутствующего в единственном экземпляре."""
        items: list[int] = [10, 20, 30]
        assert binary_search_last(items, 20) == 1

    def test_multiple_occurrences(self) -> None:
        """Проверяет поиск последнего вхождения при наличии повторяющихся значений."""
        items: list[int] = [1, 3, 3, 3, 5]
        assert binary_search_last(items, 3) == 3

    def test_element_not_found(self) -> None:
        """Проверяет возврат -1 при отсутствии значения."""
        items: list[int] = [2, 4, 6]
        assert binary_search_last(items, 3) == -1
        assert binary_search_last(items, 1) == -1
        assert binary_search_last(items, 10) == -1

    def test_with_custom_bounds(self) -> None:
        """Проверяет поиск последнего элемента в ограниченном диапазоне."""
        items: list[int] = [2, 2, 2, 2, 2]
        assert binary_search_last(items, 2, lo=1, hi=4) == 3

    def test_with_key_function(self) -> None:
        """Проверяет binary_search_last с функцией key."""
        items: list[ScoreItem] = [
            ScoreItem("P1", 10),
            ScoreItem("P2", 20),
            ScoreItem("P3", 20),
            ScoreItem("P4", 30),
        ]
        assert binary_search_last(items, 20, key=lambda x: x.score) == 2


class TestBinarySearchRotated:
    """Набор тестов для поиска в циклически сдвинутом массиве (binary_search_rotated)."""

    def test_empty_sequence(self) -> None:
        """Проверяет поиск в пустой последовательности."""
        assert binary_search_rotated([], 10) == -1

    def test_single_element(self) -> None:
        """Проверяет массив из одного элемента."""
        assert binary_search_rotated([7], 7) == 0
        assert binary_search_rotated([7], 3) == -1

    def test_unrotated_array(self) -> None:
        """Проверяет нормальный отсортированный массив без сдвига."""
        items: list[int] = [1, 2, 3, 4, 5, 6, 7]
        for idx, val in enumerate(items):
            assert binary_search_rotated(items, val) == idx
        assert binary_search_rotated(items, 0) == -1
        assert binary_search_rotated(items, 8) == -1

    def test_various_rotations(self) -> None:
        """Проверяет поиск во всех возможных циклических сдвигах массива."""
        base: list[int] = [0, 1, 2, 3, 4, 5, 6]
        for shift in range(len(base)):
            rotated: list[int] = base[shift:] + base[:shift]
            for target in base:
                found_idx: int = binary_search_rotated(rotated, target)
                assert found_idx != -1
                assert rotated[found_idx] == target
            assert binary_search_rotated(rotated, 99) == -1

    def test_with_duplicates(self) -> None:
        """Проверяет циклически сдвинутые массивы с повторяющимися элементами."""
        arrays: list[list[int]] = [
            [2, 2, 2, 0, 2],
            [2, 0, 2, 2, 2],
            [1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1],
            [3, 3, 0, 3, 3, 3],
        ]
        for arr in arrays:
            assert binary_search_rotated(arr, 0) != -1
            assert arr[binary_search_rotated(arr, 0)] == 0
            assert binary_search_rotated(arr, 999) == -1

        arr_with_one: list[int] = [3, 3, 1, 3, 3, 3]
        assert binary_search_rotated(arr_with_one, 1) == 2

    def test_with_custom_bounds(self) -> None:
        """Проверяет циклический поиск с ограничением [lo, hi)."""
        items: list[int] = [4, 5, 6, 7, 0, 1, 2]
        assert binary_search_rotated(items, 6, lo=1, hi=4) == 2
        assert binary_search_rotated(items, 0, lo=0, hi=3) == -1

    def test_with_key_function(self) -> None:
        """Проверяет циклический поиск с кастомной функцией key."""
        items: list[ScoreItem] = [
            ScoreItem("D", 40),
            ScoreItem("E", 50),
            ScoreItem("A", 10),
            ScoreItem("B", 20),
            ScoreItem("C", 30),
        ]
        found_idx: int = binary_search_rotated(items, 10, key=lambda x: x.score)
        assert found_idx == 2
        assert items[found_idx].name == "A"


class TestBoundsValidation:
    """Набор тестов для валидации граничных аргументов lo и hi."""

    def test_negative_lo(self) -> None:
        """Проверяет исключение при отрицательном lo."""
        items: list[int] = [1, 2, 3]
        with pytest.raises(ValueError, match="lo не может быть отрицательной"):
            lower_bound(items, 2, lo=-1)

    def test_negative_hi(self) -> None:
        """Проверяет исключение при отрицательном hi."""
        items: list[int] = [1, 2, 3]
        with pytest.raises(ValueError, match="hi не может быть отрицательной"):
            upper_bound(items, 2, hi=-1)

    def test_lo_greater_than_hi(self) -> None:
        """Проверяет исключение, когда lo > hi."""
        items: list[int] = [1, 2, 3]
        with pytest.raises(ValueError, match="lo не может превышать"):
            binary_search(items, 2, lo=3, hi=1)

    def test_hi_greater_than_length(self) -> None:
        """Проверяет исключение, когда hi превышает длину последовательности."""
        items: list[int] = [1, 2, 3]
        with pytest.raises(ValueError, match="hi не может превышать длину"):
            equal_range(items, 2, hi=10)

    def test_validation_on_binary_search_rotated(self) -> None:
        """Проверяет валидацию параметров в binary_search_rotated."""
        items: list[int] = [3, 4, 1, 2]
        with pytest.raises(ValueError, match="lo не может превышать"):
            binary_search_rotated(items, 1, lo=3, hi=2)
