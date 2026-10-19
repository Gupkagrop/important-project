"""Модульные тесты для модуля расстояния Левенштейна и текстового сходства."""

import pytest

from pocket_toolkit.algorithms.levenshtein import (
    AlignmentStep,
    EditOperation,
    damerau_levenshtein_distance,
    find_closest_matches,
    levenshtein_alignment,
    levenshtein_distance,
    levenshtein_matrix,
    levenshtein_similarity,
)


class TestLevenshteinDistance:
    """Набор тестов для функции levenshtein_distance."""

    def test_identical_strings(self) -> None:
        """Проверяет расстояние для идентичных строк."""
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("kitten", "kitten") == 0
        assert levenshtein_distance("алгоритм", "алгоритм") == 0

    def test_one_empty_string(self) -> None:
        """Проверяет расстояние при одной пустой строке."""
        assert levenshtein_distance("", "abc") == 3
        assert levenshtein_distance("hello", "") == 5

    def test_classic_textbook_pairs(self) -> None:
        """Проверяет классические хрестоматийные примеры редакционного расстояния."""
        assert levenshtein_distance("kitten", "sitting") == 3
        assert levenshtein_distance("flaw", "lawn") == 2
        assert levenshtein_distance("saturday", "sunday") == 3
        assert levenshtein_distance("rosettacode", "raisethysword") == 8

    def test_single_operations(self) -> None:
        """Проверяет единичные операции вставки, удаления и замены."""
        # Замена
        assert levenshtein_distance("cat", "bat") == 1
        # Вставка
        assert levenshtein_distance("cat", "cats") == 1
        # Удаление
        assert levenshtein_distance("cats", "cat") == 1

    def test_custom_weights(self) -> None:
        """Проверяет вычисление с нестандартными весами операций."""
        # Дешевая замена (1) при дорогой вставке/удалении (5, 5)
        assert levenshtein_distance("cat", "bat", weights=(5, 5, 1)) == 1
        # Дорогая замена (10) выгоднее сделать через delete (2) + insert (2) = 4
        assert levenshtein_distance("cat", "bat", weights=(2, 2, 10)) == 4
        # Нулевые веса
        assert levenshtein_distance("abc", "def", weights=(0, 0, 0)) == 0

    def test_invalid_weights_raises_error(self) -> None:
        """Проверяет валидацию отрицательных весов и некорректной длины кортежа."""
        with pytest.raises(ValueError, match="не может быть отрицательной"):
            levenshtein_distance("a", "b", weights=(-1, 1, 1))

        with pytest.raises(ValueError, match="не может быть отрицательной"):
            levenshtein_distance("a", "b", weights=(1, -1, 1))

        with pytest.raises(ValueError, match="не может быть отрицательной"):
            levenshtein_distance("a", "b", weights=(1, 1, -1))

        with pytest.raises(ValueError, match="ровно 3 элемента"):
            # noinspection PyTypeChecker
            levenshtein_distance("a", "b", weights=(1, 1))  # type: ignore[arg-type]

    def test_max_distance_limit(self) -> None:
        """Проверяет отсечение по max_distance."""
        # Точный расчет укладывается в лимит
        assert levenshtein_distance("kitten", "sitting", max_distance=3) == 3
        assert levenshtein_distance("kitten", "sitting", max_distance=4) == 3

        # Лимит превышен — возврат max_distance + 1
        assert levenshtein_distance("kitten", "sitting", max_distance=2) == 3
        assert levenshtein_distance("kitten", "sitting", max_distance=1) == 2

        # Случай, когда минимум в последней строке меньше лимита, но итоговый dist > max_distance
        assert levenshtein_distance("abc", "axcyz", max_distance=2) == 3

    def test_max_distance_early_exit_by_length(self) -> None:
        """Проверяет немедленное отсечение при очевидной разнице длин."""
        # Разница длин 5, а лимит 2 -> ранний выход без вычисления DP
        assert levenshtein_distance("a", "abcdef", max_distance=2) == 3
        assert levenshtein_distance("abcdef", "", max_distance=3) == 4
        assert levenshtein_distance("", "abcdef", max_distance=3) == 4

    def test_negative_max_distance_raises_error(self) -> None:
        """Проверяет исключение при отрицательном значении max_distance."""
        with pytest.raises(ValueError, match="не может быть отрицательным"):
            levenshtein_distance("a", "b", max_distance=-1)

    def test_non_string_sequences(self) -> None:
        """Проверяет работу с произвольными последовательностями (списки, кортежи)."""
        nums1: list[int] = [1, 2, 3, 4]
        nums2: list[int] = [1, 5, 3, 4]
        assert levenshtein_distance(nums1, nums2) == 1

        tokens1: tuple[str, ...] = ("import", "sys", "exit")
        tokens2: tuple[str, ...] = ("import", "os", "exit")
        assert levenshtein_distance(tokens1, tokens2) == 1


class TestDamerauLevenshteinDistance:
    """Набор тестов для функции damerau_levenshtein_distance (OSA)."""

    def test_identical_sequences(self) -> None:
        """Проверяет расстояние Дамерау для идентичных строк."""
        assert damerau_levenshtein_distance("", "") == 0
        assert damerau_levenshtein_distance("hello", "hello") == 0

    def test_empty_sequences(self) -> None:
        """Проверяет расстояние Дамерау при пустых аргументах."""
        assert damerau_levenshtein_distance("", "test") == 4
        assert damerau_levenshtein_distance("word", "") == 4

    def test_adjacent_transpositions(self) -> None:
        """Проверяет обработку перестановок двух соседних элементов."""
        # Для обычного Левенштейна расстояние "ab" -> "ba" равно 2 (замена двух символов).
        # Для Дамерау-Левенштейна это 1 операция перестановки.
        assert levenshtein_distance("ab", "ba") == 2
        assert damerau_levenshtein_distance("ab", "ba") == 1

        assert damerau_levenshtein_distance("tehs", "thes") == 1
        assert damerau_levenshtein_distance("ca", "abc") == 3

    def test_complex_damerau_cases(self) -> None:
        """Проверяет комбинацию перестановок с вставками и удалениями."""
        # "abcd" -> "badc" (две независимые перестановки: "ab" -> "ba", "cd" -> "dc")
        assert damerau_levenshtein_distance("abcd", "badc") == 2

    def test_damerau_max_distance(self) -> None:
        """Проверяет ограничение max_distance для Дамерау-Левенштейна."""
        assert damerau_levenshtein_distance("ab", "ba", max_distance=1) == 1
        assert damerau_levenshtein_distance("ab", "ba", max_distance=0) == 1
        assert damerau_levenshtein_distance("a", "abcdef", max_distance=2) == 3
        # Случай, когда минимум последней строки <= max_distance, но итоговый результат больше
        assert damerau_levenshtein_distance("abc", "axcyz", max_distance=2) == 3

        with pytest.raises(ValueError, match="не может быть отрицательным"):
            damerau_levenshtein_distance("a", "b", max_distance=-1)

    def test_damerau_generic_sequences(self) -> None:
        """Проверяет вычисление для списков чисел."""
        assert damerau_levenshtein_distance([1, 2, 3], [2, 1, 3]) == 1

    def test_edit_operation_enum_values(self) -> None:
        """Проверяет строковые значения элементов перечисления EditOperation."""
        assert EditOperation.MATCH == "match"
        assert EditOperation.INSERT == "insert"
        assert EditOperation.DELETE == "delete"
        assert EditOperation.SUBSTITUTE == "substitute"
        assert EditOperation.TRANSPOSITION == "transposition"


class TestLevenshteinMatrix:
    """Набор тестов для функции levenshtein_matrix."""

    def test_matrix_dimensions_and_boundary(self) -> None:
        """Проверяет размерность и граничные значения матрицы."""
        s1: str = "cat"
        s2: str = "hats"
        matrix: list[list[int]] = levenshtein_matrix(s1, s2)

        # Размеры (len(s1) + 1) x (len(s2) + 1) -> 4 x 5
        assert len(matrix) == 4
        assert len(matrix[0]) == 5

        # Первая строка: 0, 1, 2, 3, 4
        assert matrix[0] == [0, 1, 2, 3, 4]
        # Первый столбец: 0, 1, 2, 3
        assert [matrix[i][0] for i in range(4)] == [0, 1, 2, 3]

        # Правый нижний угол совпадает с расстоянием Левенштейна
        assert matrix[3][4] == levenshtein_distance(s1, s2)

    def test_empty_strings_matrix(self) -> None:
        """Проверяет матрицу для двух пустых строк."""
        matrix: list[list[int]] = levenshtein_matrix("", "")
        assert matrix == [[0]]

    def test_matrix_with_custom_weights(self) -> None:
        """Проверяет корректность матрицы с заданными весами."""
        matrix: list[list[int]] = levenshtein_matrix("a", "b", weights=(3, 2, 4))
        # [0, 3]
        # [2, 4] (замена: 0 + 4 = 4; удалить+вставить: 2 + 3 = 5 -> минимум 4)
        assert matrix[0] == [0, 3]
        assert matrix[1] == [2, 4]

    def test_invalid_weights_in_matrix(self) -> None:
        """Проверяет валидацию весов при генерации матрицы."""
        with pytest.raises(ValueError, match="не может быть отрицательной"):
            levenshtein_matrix("a", "b", weights=(-1, 1, 1))


class TestLevenshteinSimilarity:
    """Набор тестов для функции levenshtein_similarity."""

    def test_identical_sequences(self) -> None:
        """Проверяет сходство равных строк."""
        assert levenshtein_similarity("", "") == 1.0
        assert levenshtein_similarity("python", "python") == 1.0
        assert levenshtein_similarity([1, 2, 3], [1, 2, 3]) == 1.0

    def test_completely_different_strings(self) -> None:
        """Проверяет сходство полностью несовпадающих строк."""
        assert levenshtein_similarity("a", "b") == 0.0
        assert levenshtein_similarity("abc", "") == 0.0
        assert levenshtein_similarity("", "xyz") == 0.0

    def test_partial_similarity(self) -> None:
        """Проверяет вычисление промежуточных значений сходства."""
        # "kitten" (6) vs "sitting" (7), distance 3, max_cost 7 -> 1.0 - 3/7 = 0.571429
        sim: float = levenshtein_similarity("kitten", "sitting")
        assert 0.57 < sim < 0.58

        # 1 символ разницы из 4
        assert levenshtein_similarity("word", "lord") == 0.75

    def test_custom_weights_similarity(self) -> None:
        """Проверяет вычисление сходства с пользовательскими весами."""
        sim: float = levenshtein_similarity("cat", "bat", weights=(1, 1, 1))
        assert sim == 2.0 / 3.0 or round(sim, 2) == 0.67

    def test_zero_weights_return_one(self) -> None:
        """Проверяет случай нулевых весов."""
        assert levenshtein_similarity("abc", "xyz", weights=(0, 0, 0)) == 1.0


class TestLevenshteinAlignment:
    """Набор тестов для функции levenshtein_alignment (пошаговое выравнивание)."""

    def test_empty_alignment(self) -> None:
        """Проверяет выравнивание для пустых строк."""
        steps: list[AlignmentStep[str]] = levenshtein_alignment("", "")
        assert steps == []

    def test_identical_alignment(self) -> None:
        """Проверяет выравнивание одинаковых строк."""
        steps: list[AlignmentStep[str]] = levenshtein_alignment("abc", "abc")
        assert len(steps) == 3
        for step in steps:
            assert step.operation == EditOperation.MATCH
            assert step.source == step.target

    def test_insertion_only(self) -> None:
        """Проверяет выравнивание при вставках."""
        steps: list[AlignmentStep[str]] = levenshtein_alignment("", "abc")
        assert len(steps) == 3
        for idx, char in enumerate("abc"):
            assert steps[idx].operation == EditOperation.INSERT
            assert steps[idx].source is None
            assert steps[idx].target == char

    def test_deletion_only(self) -> None:
        """Проверяет выравнивание при удалениях."""
        steps: list[AlignmentStep[str]] = levenshtein_alignment("abc", "")
        assert len(steps) == 3
        for idx, char in enumerate("abc"):
            assert steps[idx].operation == EditOperation.DELETE
            assert steps[idx].source == char
            assert steps[idx].target is None

    def test_mixed_alignment_reconstruction(self) -> None:
        """Проверяет, что применение шагов выравнивания корректно преобразует s1 в s2."""
        s1: str = "kitten"
        s2: str = "sitting"
        steps: list[AlignmentStep[str]] = levenshtein_alignment(s1, s2)

        reconstructed: list[str] = []
        source_idx: int = 0

        for step in steps:
            if step.operation in (EditOperation.MATCH, EditOperation.SUBSTITUTE):
                assert step.source == s1[source_idx]
                assert step.target is not None
                reconstructed.append(step.target)
                source_idx += 1
            elif step.operation == EditOperation.DELETE:
                assert step.source == s1[source_idx]
                assert step.target is None
                source_idx += 1
            elif step.operation == EditOperation.INSERT:
                assert step.source is None
                assert step.target is not None
                reconstructed.append(step.target)

        assert "".join(reconstructed) == s2
        assert source_idx == len(s1)


class TestFindClosestMatches:
    """Набор тестов для функции find_closest_matches."""

    def test_find_best_matches(self) -> None:
        """Проверяет нахождение наиболее близких кандидатов."""
        candidates: list[str] = ["apple", "apply", "app", "banana", "application", "apricot"]
        matches: list[tuple[str, float]] = find_closest_matches("appl", candidates, n=3)

        assert len(matches) == 3
        # Топ кандидаты: "apple" (дистанция 1, similarity 4/5=0.8), "apply" (0.8), "app" (дистанция 1, similarity 3/4=0.75)
        top_words: list[str] = [word for word, _ in matches]
        assert "apple" in top_words
        assert "apply" in top_words
        assert "app" in top_words

        # Сходство упорядочено по убыванию
        assert matches[0][1] >= matches[1][1] >= matches[2][1]

    def test_empty_candidates(self) -> None:
        """Проверяет работу с пустым набором кандидатов."""
        assert find_closest_matches("hello", []) == []

    def test_n_zero(self) -> None:
        """Проверяет запрос с n=0."""
        assert find_closest_matches("hello", ["hello", "world"], n=0) == []

    def test_negative_n_raises_error(self) -> None:
        """Проверяет ошибку при отрицательном n."""
        with pytest.raises(ValueError, match="не может быть отрицательным"):
            find_closest_matches("hello", ["hello"], n=-1)

    def test_invalid_min_similarity_raises_error(self) -> None:
        """Проверяет валидацию min_similarity вне диапазона [0.0, 1.0]."""
        with pytest.raises(ValueError, match="диапазоне от 0.0 до 1.0"):
            find_closest_matches("hello", ["hello"], min_similarity=-0.1)

        with pytest.raises(ValueError, match="диапазоне от 0.0 до 1.0"):
            find_closest_matches("hello", ["hello"], min_similarity=1.1)

    def test_min_similarity_filter(self) -> None:
        """Проверяет отсечение кандидатов ниже порога схожести."""
        candidates: list[str] = ["cat", "bat", "elephant"]
        matches: list[tuple[str, float]] = find_closest_matches("cat", candidates, min_similarity=0.6)
        matched_words: list[str] = [word for word, _ in matches]

        assert "cat" in matched_words
        assert "bat" in matched_words
        assert "elephant" not in matched_words

    def test_find_closest_matches_with_weights(self) -> None:
        """Проверяет поиск совпадений с кастомными весами."""
        candidates: list[str] = ["cat", "bat", "car"]
        # С весом замены 10 замена дорогая
        matches = find_closest_matches("cat", candidates, weights=(1, 1, 10))
        assert len(matches) == 3
        assert matches[0][0] == "cat"
        assert matches[0][1] == 1.0
