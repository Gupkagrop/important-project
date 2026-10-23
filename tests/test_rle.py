"""Модульные тесты для модуля кодирования длин серий (RLE)."""

import math

import pytest

from pocket_toolkit.algorithms.rle import (
    RLERun,
    calculate_compression_ratio,
    calculate_space_saving,
    rle_decode,
    rle_decode_bytes,
    rle_decode_iter,
    rle_decode_str,
    rle_encode,
    rle_encode_bytes,
    rle_encode_iter,
    rle_encode_str,
)


class TestRLERun:
    """Набор тестов для структуры серии RLERun."""

    def test_init_and_properties(self) -> None:
        """Проверяет создание серии и доступ к атрибутам и индексам."""
        run: RLERun[str] = RLERun("A", 5)
        assert run.value == "A"
        assert run.count == 5
        assert run[0] == "A"
        assert run[1] == 5
        assert len(run) == 2

    def test_unpacking(self) -> None:
        """Проверяет распаковку серии как стандартного кортежа."""
        val, count = RLERun(42, 10)
        assert val == 42
        assert count == 10

    def test_tuple_equality(self) -> None:
        """Проверяет равенство серии стандартному кортежу (value, count)."""
        run: RLERun[str] = RLERun("x", 3)
        assert run == ("x", 3)
        assert ("x", 3) == run

    def test_repr(self) -> None:
        """Проверяет строковое представление серии."""
        run: RLERun[str] = RLERun("abc", 2)
        assert repr(run) == "RLERun(value='abc', count=2)"

    def test_invalid_count_raises(self) -> None:
        """Проверяет генерацию ошибки при неположительной длине серии."""
        with pytest.raises(ValueError, match="строго положительной"):
            RLERun("A", 0)

        with pytest.raises(ValueError, match="строго положительной"):
            RLERun("B", -3)


class TestRLEGenericEncodeDecode:
    """Набор тестов для generic-функций rle_encode и rle_decode."""

    def test_empty_sequence(self) -> None:
        """Проверяет кодирование и декодирование пустой последовательности."""
        assert rle_encode([]) == []
        assert rle_encode(()) == []
        assert rle_encode("") == []
        assert rle_decode([]) == []

    def test_single_element(self) -> None:
        """Проверяет последовательность из одного элемента."""
        encoded: list[RLERun[int]] = rle_encode([99])
        assert encoded == [("99", 1)] or encoded == [(99, 1)]
        assert encoded[0].value == 99
        assert encoded[0].count == 1
        assert rle_decode(encoded) == [99]

    def test_all_identical_elements(self) -> None:
        """Проверяет последовательность из одинаковых элементов."""
        data: list[str] = ["a", "a", "a", "a", "a"]
        encoded: list[RLERun[str]] = rle_encode(data)
        assert len(encoded) == 1
        assert encoded[0] == ("a", 5)
        assert rle_decode(encoded) == data

    def test_all_distinct_elements(self) -> None:
        """Проверяет последовательность, где нет подряд идущих повторов."""
        data: list[int] = [1, 2, 3, 4, 5]
        encoded: list[RLERun[int]] = rle_encode(data)
        assert encoded == [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1)]
        assert rle_decode(encoded) == data

    def test_mixed_sequence_roundtrip(self) -> None:
        """Проверяет циклический тест кодирования и декодирования произвольных данных."""
        data: list[str] = ["A", "A", "B", "C", "C", "C", "A", "A"]
        encoded: list[RLERun[str]] = rle_encode(data)
        assert encoded == [("A", 2), ("B", 1), ("C", 3), ("A", 2)]
        assert rle_decode(encoded) == data

    def test_decode_from_standard_tuples(self) -> None:
        """Проверяет, что rle_decode принимает обычные кортежи."""
        raw_runs: list[tuple[str, int]] = [("foo", 2), ("bar", 1)]
        assert rle_decode(raw_runs) == ["foo", "foo", "bar"]

    def test_decode_invalid_count_raises(self) -> None:
        """Проверяет генерацию ошибки при неположительном значении count."""
        with pytest.raises(ValueError, match="строго больше 0"):
            rle_decode([("A", 2), ("B", 0)])

        with pytest.raises(ValueError, match="строго больше 0"):
            rle_decode([("A", -1)])


class TestRLEIterators:
    """Набор тестов для потоковых генераторов rle_encode_iter и rle_decode_iter."""

    def test_encode_iter_streaming(self) -> None:
        """Проверяет ленивое пошаговое кодирование через итератор."""
        stream = iter([1, 1, 2, 2, 2, 3])
        gen = rle_encode_iter(stream)
        assert next(gen) == (1, 2)
        assert next(gen) == (2, 3)
        assert next(gen) == (3, 1)
        with pytest.raises(StopIteration):
            next(gen)

    def test_encode_iter_empty(self) -> None:
        """Проверяет итератор кодирования для пустого источника."""
        gen = rle_encode_iter([])
        with pytest.raises(StopIteration):
            next(gen)

    def test_decode_iter_streaming(self) -> None:
        """Проверяет ленивое пошаговое декодирование через итератор."""
        runs = [("x", 2), ("y", 1)]
        gen = rle_decode_iter(runs)
        assert list(gen) == ["x", "x", "y"]

    def test_decode_iter_invalid_count_raises(self) -> None:
        """Проверяет генерацию ошибки в генераторе декодирования."""
        gen = rle_decode_iter([("ok", 1), ("bad", 0)])
        assert next(gen) == "ok"
        with pytest.raises(ValueError, match="строго больше 0"):
            next(gen)


class TestRLEString:
    """Набор тестов для строковых функций rle_encode_str и rle_decode_str."""

    def test_empty_string(self) -> None:
        """Проверяет кодирование и декодирование пустой строки."""
        assert rle_encode_str("") == ""
        assert rle_decode_str("") == ""
        assert rle_encode_str("", delimiter=",") == ""
        assert rle_decode_str("", delimiter=",") == ""

    def test_classic_compact_wikipedia_example(self) -> None:
        """Проверяет классический пример RLE со строкой символов W и B."""
        text: str = (
            "WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWWWWWWWWWWWWWWWWWWBWWWWWWWWWWWWWW"
        )
        expected: str = "12W1B12W3B24W1B14W"
        encoded: str = rle_encode_str(text)
        assert encoded == expected
        assert rle_decode_str(encoded) == text

    def test_single_characters(self) -> None:
        """Проверяет строку из единичных неповторяющихся символов."""
        text: str = "ABCXYZ"
        encoded: str = rle_encode_str(text)
        assert encoded == "1A1B1C1X1Y1Z"
        assert rle_decode_str(encoded) == text

    def test_cyrillic_strings(self) -> None:
        """Проверяет корректность работы с символами кириллицы."""
        text: str = "АААББВГГГГ"
        encoded: str = rle_encode_str(text)
        assert encoded == "3А2Б1В4Г"
        assert rle_decode_str(encoded) == text

    def test_compact_mode_raises_on_digits(self) -> None:
        """Проверяет, что компактный режим без разделителя запрещает строки с цифрами."""
        with pytest.raises(ValueError, match="Строка содержит цифры"):
            rle_encode_str("A111B")

    def test_delimiter_mode_with_digits(self) -> None:
        """Проверяет кодирование и декодирование строк с цифрами при наличии разделителя."""
        text: str = "1112223333"
        encoded: str = rle_encode_str(text, delimiter=",")
        assert encoded == "3:1,3:2,4:3"
        assert rle_decode_str(encoded, delimiter=",") == text

    def test_delimiter_mode_with_spaces_and_symbols(self) -> None:
        """Проверяет работу с пробелами, спецсимволами и настраиваемым разделителем."""
        text: str = "   ###$$$"
        encoded: str = rle_encode_str(text, delimiter=";")
        assert encoded == "3: ;3:#;3:$"
        assert rle_decode_str(encoded, delimiter=";") == text

    def test_invalid_type_raises(self) -> None:
        """Проверяет ошибку типов при передаче не-строковых аргументов."""
        with pytest.raises(TypeError, match="Ожидалась строка"):
            rle_encode_str(123)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="Ожидалась строка"):
            rle_decode_str([1, 2, 3])  # type: ignore[arg-type]

    def test_compact_decode_malformed_syntax(self) -> None:
        """Проверяет ошибки декодирования некорректного компактного синтаксиса."""
        # Начинается с буквы вместо цифры
        with pytest.raises(ValueError, match="ожидалась цифра длины серии"):
            rle_decode_str("A3B")

        # Число без символа в конце строки
        with pytest.raises(ValueError, match="отсутствует символ после числа"):
            rle_decode_str("3A5")

        # Длина серии равна 0
        with pytest.raises(ValueError, match="Длина серии должна быть > 0"):
            rle_decode_str("0A")

    def test_delimiter_decode_malformed_syntax(self) -> None:
        """Проверяет ошибки декодирования при неверном формате блоков с разделителем."""
        # Пустой блок между запятыми
        with pytest.raises(ValueError, match="Обнаружен пустой блок"):
            rle_decode_str("2:A,,3:B", delimiter=",")

        # Отсутствует двоеточие
        with pytest.raises(ValueError, match="Ожидался 'count:char'"):
            rle_decode_str("2A,3B", delimiter=",")

        # Нечисловая длина серии
        with pytest.raises(ValueError, match="целым числом"):
            rle_decode_str("x:A,3:B", delimiter=",")

        # Нулевая длина серии
        with pytest.raises(ValueError, match="Длина серии должна быть > 0"):
            rle_decode_str("0:A", delimiter=",")


class TestRLEBytes:
    """Набор тестов для бинарных функций rle_encode_bytes и rle_decode_bytes."""

    def test_empty_bytes(self) -> None:
        """Проверяет обработку пустых байтовых массивов."""
        assert rle_encode_bytes(b"") == b""
        assert rle_decode_bytes(b"") == b""

    def test_bytearray_input(self) -> None:
        """Проверяет поддержку типа bytearray."""
        data = bytearray(b"\x01\x01\x02")
        encoded: bytes = rle_encode_bytes(data)
        assert encoded == bytes([2, 1, 1, 2])
        assert rle_decode_bytes(encoded) == b"\x01\x01\x02"

    def test_standard_byte_runs(self) -> None:
        """Проверяет кодирование последовательности различных байтов."""
        data: bytes = b"\x00\x00\x00\xff\xff\x0a"
        encoded: bytes = rle_encode_bytes(data)
        assert encoded == bytes([3, 0x00, 2, 0xFF, 1, 0x0A])
        assert rle_decode_bytes(encoded) == data

    def test_run_length_exceeding_255(self) -> None:
        """Проверяет разбиение серий длиннее 255 на несколько порций."""
        data: bytes = b"\x42" * 300
        encoded: bytes = rle_encode_bytes(data)
        assert len(encoded) == 4
        assert encoded == bytes([255, 0x42, 45, 0x42])
        assert rle_decode_bytes(encoded) == data

    def test_invalid_bytes_type(self) -> None:
        """Проверяет ошибку при передаче не-байтовых данных."""
        with pytest.raises(TypeError, match="Ожидались bytes или bytearray"):
            rle_encode_bytes("not bytes")  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="Ожидались bytes или bytearray"):
            rle_decode_bytes(123)  # type: ignore[arg-type]

    def test_odd_length_bytes_raises(self) -> None:
        """Проверяет ошибку при нечетной длине закодированных байтов."""
        with pytest.raises(ValueError, match="должна быть четной"):
            rle_decode_bytes(b"\x01\x02\x03")

    def test_zero_count_in_bytes_raises(self) -> None:
        """Проверяет ошибку при нулевой длине серии в байтах."""
        with pytest.raises(ValueError, match="не может быть равна 0"):
            rle_decode_bytes(bytes([0, 0xAA]))


class TestCompressionMetrics:
    """Набор тестов для утилит расчета метрик сжатия."""

    def test_compression_ratio(self) -> None:
        """Проверяет расчет коэффициента сжатия."""
        assert calculate_compression_ratio(100, 50) == 0.5
        assert calculate_compression_ratio(100, 100) == 1.0
        assert calculate_compression_ratio(100, 150) == 1.5

    def test_compression_ratio_zero_size(self) -> None:
        """Проверяет коэффициент сжатия при нулевом исходном размере."""
        assert calculate_compression_ratio(0, 0) == 1.0
        assert math.isinf(calculate_compression_ratio(0, 10))

    def test_space_saving(self) -> None:
        """Проверяет расчет процента экономии места."""
        assert calculate_space_saving(100, 40) == pytest.approx(60.0)
        assert calculate_space_saving(100, 100) == pytest.approx(0.0)
        assert calculate_space_saving(100, 120) == pytest.approx(-20.0)
        assert calculate_space_saving(0, 0) == 0.0

    def test_negative_sizes_raises(self) -> None:
        """Проверяет выброс ошибки при отрицательных размерах."""
        with pytest.raises(ValueError, match="не могут быть отрицательными"):
            calculate_compression_ratio(-1, 10)

        with pytest.raises(ValueError, match="не могут быть отрицательными"):
            calculate_space_saving(10, -5)
