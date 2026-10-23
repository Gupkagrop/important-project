"""Модуль кодирования длин серий (Run-Length Encoding, RLE).

Предоставляет функции для прямого и обратного сжатия последовательностей
произвольных элементов, текстовых строк и байтовых массивов, а также потоковые
генераторы и утилиты оценки коэффициента сжатия.
"""

from collections.abc import Iterable, Iterator


class RLERun[T](tuple[T, int]):
    """Элементарная серия RLE, представляющая собой пару (значение, длина серии).

    Является подклассом `tuple[T, int]`, поэтому поддерживает стандартную распаковку
    и индексацию `run[0]`, `run[1]`, а также именованные свойства `.value` и `.count`.
    """

    def __new__(cls, value: T, count: int) -> "RLERun[T]":
        """Создает новый экземпляр серии RLE.

        :param value: Значение повторяющегося элемента.
        :param count: Количество повторений подряд (> 0).
        :return: Новый экземпляр `RLERun[T]`.
        :raises ValueError: Если длина серии меньше или равна нулю.
        """
        if count <= 0:
            raise ValueError(
                f"Длина серии должна быть строго положительной (> 0), получено: {count}"
            )
        return super().__new__(cls, (value, count))

    @property
    def value(self) -> T:
        """Повторяющееся значение элемента."""
        return self[0]

    @property
    def count(self) -> int:
        """Количество последовательных повторений элемента."""
        return self[1]

    def __repr__(self) -> str:
        """Текстовое представление серии."""
        return f"RLERun(value={self.value!r}, count={self.count})"


def rle_encode_iter[T](iterable: Iterable[T]) -> Iterator[RLERun[T]]:
    """Потоковый генератор серий RLE для произвольной итерируемой последовательности.

    :param iterable: Входная последовательность элементов.
    :yields: Экземпляры `RLERun[T]` по мере обнаружения серий.
    """
    iterator = iter(iterable)
    try:
        current_value: T = next(iterator)
    except StopIteration:
        return

    current_count: int = 1
    for item in iterator:
        if item == current_value:
            current_count += 1
            continue
        yield RLERun(current_value, current_count)
        current_value = item
        current_count = 1

    yield RLERun(current_value, current_count)


def rle_encode[T](sequence: Iterable[T]) -> list[RLERun[T]]:
    """Кодирует последовательность методом длин серий (RLE).

    :param sequence: Входная последовательность элементов.
    :return: Список серий `RLERun[T]` в порядке следования.
    """
    return list(rle_encode_iter(sequence))


def rle_decode_iter[T](runs: Iterable[tuple[T, int] | RLERun[T]]) -> Iterator[T]:
    """Потоковый генератор распаковки серий RLE.

    :param runs: Итерируемый набор пар (значение, количество).
    :yields: Восстановленные элементы последовательности.
    :raises ValueError: Если количество повторений в серии неположительно.
    """
    for entry in runs:
        value: T = entry[0]
        count: int = entry[1]
        if count <= 0:
            raise ValueError(
                f"Количество повторений в серии должно быть строго больше 0, получено: {count}"
            )
        for _ in range(count):
            yield value


def rle_decode[T](runs: Iterable[tuple[T, int] | RLERun[T]]) -> list[T]:
    """Декодирует список или итерируемый набор серий RLE обратно в список элементов.

    :param runs: Набор пар (значение, количество).
    :return: Исходный список элементов.
    :raises ValueError: Если среди серий встречается неположительная длина.
    """
    return list(rle_decode_iter(runs))


def _encode_str_with_delimiter(text: str, delimiter: str) -> str:
    """Кодирует строку с разделителем между сериями вида count:char."""
    if not text:
        return ""
    runs: list[RLERun[str]] = rle_encode(text)
    return delimiter.join(f"{run.count}:{run.value}" for run in runs)


def _encode_str_compact(text: str) -> str:
    """Кодирует строку в компактный формат count+char без разделителя."""
    if not text:
        return ""
    if any(ch.isdigit() for ch in text):
        raise ValueError(
            "Строка содержит цифры. Для однозначного декодирования укажите разделитель "
            "(например, delimiter=',') или используйте rle_encode."
        )
    runs: list[RLERun[str]] = rle_encode(text)
    return "".join(f"{run.count}{run.value}" for run in runs)


def rle_encode_str(text: str, *, delimiter: str | None = None) -> str:
    """Кодирует текстовую строку методом длин серий в компактный вид.

    :param text: Исходная строка.
    :param delimiter: Опциональный разделитель между сериями. Если не указан,
        серии склеиваются в формате '<count><char>' (в строке не должно быть цифр).
        Если указан, серии форматируются как '<count>:<char>', разделенные `delimiter`.
    :return: Закодированная текстовая строка.
    :raises TypeError: Если входные данные не являются строкой.
    :raises ValueError: Если в компактном режиме строка содержит цифры.
    """
    if not isinstance(text, str):
        raise TypeError(f"Ожидалась строка str, получен тип: {type(text).__name__}")
    if delimiter is not None:
        return _encode_str_with_delimiter(text, delimiter)
    return _encode_str_compact(text)


def _decode_str_with_delimiter(encoded: str, delimiter: str) -> str:
    """Декодирует строку с разделителем вида count:char."""
    if not encoded:
        return ""
    parts: list[str] = encoded.split(delimiter)
    result_chars: list[str] = []
    for part in parts:
        if not part:
            raise ValueError("Обнаружен пустой блок между разделителями")
        if ":" not in part:
            raise ValueError(
                f"Некорректный формат блока серии: {part!r}. Ожидался 'count:char'"
            )
        count_str, char_val = part.split(":", 1)
        if not count_str.isdigit():
            raise ValueError(
                f"Длина серии должна быть целым числом, получено: {count_str!r}"
            )
        count: int = int(count_str)
        if count <= 0:
            raise ValueError(f"Длина серии должна быть > 0, получено: {count}")
        result_chars.append(char_val * count)
    return "".join(result_chars)


def _decode_str_compact(encoded: str) -> str:
    """Декодирует строку компактного формата вида '<count><char>'."""
    if not encoded:
        return ""
    result_chars: list[str] = []
    i: int = 0
    n: int = len(encoded)
    while i < n:
        if not encoded[i].isdigit():
            raise ValueError(
                f"Некорректный символ на позиции {i}: ожидалась цифра длины серии, получено {encoded[i]!r}"
            )
        start: int = i
        while i < n and encoded[i].isdigit():
            i += 1
        if i >= n:
            raise ValueError(
                f"Неожиданный конец строки: отсутствует символ после числа {encoded[start:i]}"
            )
        count: int = int(encoded[start:i])
        if count <= 0:
            raise ValueError(f"Длина серии должна быть > 0, получено: {count}")
        char_val: str = encoded[i]
        result_chars.append(char_val * count)
        i += 1
    return "".join(result_chars)


def rle_decode_str(encoded: str, *, delimiter: str | None = None) -> str:
    """Декодирует закодированную строку RLE обратно в исходную строку.

    :param encoded: Закодированная строка.
    :param delimiter: Разделитель, использованный при кодировании (если применялся).
    :return: Исходная раскодированная строка.
    :raises TypeError: Если входные данные не являются строкой.
    :raises ValueError: При нарушении формата закодированной строки.
    """
    if not isinstance(encoded, str):
        raise TypeError(f"Ожидалась строка str, получен тип: {type(encoded).__name__}")
    if delimiter is not None:
        return _decode_str_with_delimiter(encoded, delimiter)
    return _decode_str_compact(encoded)


def rle_encode_bytes(data: bytes | bytearray) -> bytes:
    """Кодирует байтовую последовательность парами (count, byte).

    Каждая непрерывная серия одинаковых байтов разбивается на порции длиной до 255
    и записывается как два байта: [длина_серии (1..255), значение_байта].

    :param data: Исходные байты или bytearray.
    :return: Сжатая байтовая последовательность четной длины.
    :raises TypeError: Если входные данные не являются bytes или bytearray.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(
            f"Ожидались bytes или bytearray, получен тип: {type(data).__name__}"
        )
    if not data:
        return b""

    out: bytearray = bytearray()
    curr_byte: int = data[0]
    curr_count: int = 1

    for b in data[1:]:
        if b == curr_byte and curr_count < 255:
            curr_count += 1
            continue
        out.extend((curr_count, curr_byte))
        curr_byte = b
        curr_count = 1

    out.extend((curr_count, curr_byte))
    return bytes(out)


def rle_decode_bytes(encoded: bytes | bytearray) -> bytes:
    """Декодирует сжатую байтовую последовательность RLE.

    :param encoded: Закодированные байты (пары [длина_серии, байт]).
    :return: Исходная распакованная байтовая последовательность.
    :raises TypeError: Если входные данные не являются bytes или bytearray.
    :raises ValueError: Если длина последовательности нечетная или длина серии равна 0.
    """
    if not isinstance(encoded, (bytes, bytearray)):
        raise TypeError(
            f"Ожидались bytes или bytearray, получен тип: {type(encoded).__name__}"
        )
    if len(encoded) % 2 != 0:
        raise ValueError(
            f"Длина закодированной байтовой последовательности должна быть четной, получено: {len(encoded)}"
        )
    if not encoded:
        return b""

    out: bytearray = bytearray()
    for i in range(0, len(encoded), 2):
        count: int = encoded[i]
        byte_val: int = encoded[i + 1]
        if count == 0:
            raise ValueError(f"Длина серии на позиции {i} не может быть равна 0")
        out.extend([byte_val] * count)

    return bytes(out)


def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
    """Вычисляет коэффициент сжатия (compressed_size / original_size).

    :param original_size: Исходный размер данных.
    :param compressed_size: Размер сжатых данных.
    :return: Отношение сжатого размера к исходному.
    :raises ValueError: Если размеры отрицательны.
    """
    if original_size < 0 or compressed_size < 0:
        raise ValueError("Размеры данных не могут быть отрицательными")
    if original_size == 0:
        return 1.0 if compressed_size == 0 else float("inf")
    return compressed_size / original_size


def calculate_space_saving(original_size: int, compressed_size: int) -> float:
    """Вычисляет процент экономии объема памяти или дискового пространства.

    :param original_size: Исходный размер данных.
    :param compressed_size: Размер сжатых данных.
    :return: Процент экономии от 0% до 100% (может быть отрицательным при раздувании).
    :raises ValueError: Если размеры отрицательны.
    """
    if original_size < 0 or compressed_size < 0:
        raise ValueError("Размеры данных не могут быть отрицательными")
    if original_size == 0:
        return 0.0
    return ((original_size - compressed_size) / original_size) * 100.0
