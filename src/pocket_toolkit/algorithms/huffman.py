"""Модуль алгоритма сжатия методом Хаффмана (Huffman Coding).

Предоставляет структуру узла `HuffmanNode`, класс дерева `HuffmanTree`,
а также высокоуровневые функции кодирования и декодирования текстовых строк
в битовые последовательности и упакованные байтовые массивы.
"""

import heapq
from collections import Counter
from collections.abc import Mapping


class HuffmanNode:
    """Узел дерева Хаффмана.

    Поддерживает строгое сравнение по частоте для размещения в очереди с приоритетами.
    """

    __slots__ = ("char", "freq", "left", "right")

    def __init__(
        self,
        char: str | None,
        freq: int,
        left: "HuffmanNode | None" = None,
        right: "HuffmanNode | None" = None,
    ) -> None:
        """Инициализирует узел дерева Хаффмана.

        :param char: Символ (только для листовых узлов, иначе None).
        :param freq: Частота встречаемости символа или суммарная частота поддерева.
        :param left: Левый дочерний узел (символизирует бит '0').
        :param right: Правый дочерний узел (символизирует бит '1').
        """
        self.char: str | None = char
        self.freq: int = freq
        self.left: HuffmanNode | None = left
        self.right: HuffmanNode | None = right

    @property
    def is_leaf(self) -> bool:
        """Проверяет, является ли узел листовым (содержит символ)."""
        return self.left is None and self.right is None

    def __lt__(self, other: "HuffmanNode") -> bool:
        """Сравнивает узлы по возрастанию частоты."""
        return self.freq < other.freq

    def __repr__(self) -> str:
        """Строковое представление узла."""
        return f"HuffmanNode(char={self.char!r}, freq={self.freq})"


class HuffmanTree:
    """Дерево префиксного кодирования Хаффмана."""

    def __init__(self, root: HuffmanNode | None, codebook: dict[str, str]) -> None:
        """Инициализирует дерево Хаффмана.

        :param root: Корневой узел дерева.
        :param codebook: Словарь соответствия символов их битовым кодам.
        """
        self.root: HuffmanNode | None = root
        self.codebook: dict[str, str] = codebook
        self.reverse_codebook: dict[str, str] = {code: char for char, code in codebook.items()}

    @classmethod
    def from_frequencies(cls, frequencies: Mapping[str, int]) -> "HuffmanTree":
        """Строит дерево Хаффмана на основе словаря частот символов.

        :param frequencies: Словарь {символ: частота}.
        :return: Построенный экземпляр `HuffmanTree`.
        """
        if not frequencies:
            return cls(root=None, codebook={})

        # Особый случай: только один уникальный символ
        if len(frequencies) == 1:
            char, freq = next(iter(frequencies.items()))
            root = HuffmanNode(char=char, freq=freq)
            return cls(root=root, codebook={char: "0"})

        # Создаем приоритетную очередь узлов с уникальным счетчиком для разрешения равенства частот
        heap: list[tuple[int, int, HuffmanNode]] = []
        counter: int = 0

        for char, freq in frequencies.items():
            heapq.heappush(heap, (freq, counter, HuffmanNode(char=char, freq=freq)))
            counter += 1

        # Последовательно объединяем два узла с наименьшей частотой
        while len(heap) > 1:
            freq1, _, node1 = heapq.heappop(heap)
            freq2, _, node2 = heapq.heappop(heap)

            merged = HuffmanNode(char=None, freq=freq1 + freq2, left=node1, right=node2)
            heapq.heappush(heap, (merged.freq, counter, merged))
            counter += 1

        root = heap[0][2]
        codebook: dict[str, str] = {}
        cls._build_codebook(root, "", codebook)

        return cls(root=root, codebook=codebook)

    @classmethod
    def from_text(cls, text: str) -> "HuffmanTree":
        """Строит дерево Хаффмана по содержимому исходного текста.

        :param text: Исходная строка.
        :return: Экземпляр `HuffmanTree`.
        """
        freqs = Counter(text)
        return cls.from_frequencies(freqs)

    @staticmethod
    def _build_codebook(node: HuffmanNode | None, current_code: str, codebook: dict[str, str]) -> None:
        """Рекурсивно формирует битовую таблицу кодов."""
        if node is None:
            return

        if node.is_leaf and node.char is not None:
            codebook[node.char] = current_code or "0"
            return

        if node.left is not None:
            HuffmanTree._build_codebook(node.left, current_code + "0", codebook)
        if node.right is not None:
            HuffmanTree._build_codebook(node.right, current_code + "1", codebook)

    def encode(self, text: str) -> str:
        """Кодирует текст в строку битов ('0' и '1').

        :param text: Исходный текст.
        :return: Строка из символов '0' и '1'.
        :raises KeyError: Если текст содержит символ, отсутствующий в таблице кодов.
        """
        if not text:
            return ""

        encoded_parts: list[str] = []
        for char in text:
            if char not in self.codebook:
                raise KeyError(f"Символ {char!r} отсутствует в таблице кодов Хаффмана")
            encoded_parts.append(self.codebook[char])

        return "".join(encoded_parts)

    def decode(self, bit_string: str) -> str:
        """Декодирует строку битов обратно в исходный текст.

        :param bit_string: Строка из '0' и '1'.
        :return: Раскодированный текст.
        :raises ValueError: Если битовая последовательность повреждена или некорректна.
        """
        if not bit_string:
            return ""
        if self.root is None:
            raise ValueError("Невозможно декодировать: дерево Хаффмана пусто")

        # Если дерево состоит только из одного листа
        if self.root.is_leaf:
            if any(bit != "0" for bit in bit_string):
                raise ValueError("Некорректная битовая последовательность для дерева с одним символом")
            char = self.root.char or ""
            return char * len(bit_string)

        result: list[str] = []
        current: HuffmanNode = self.root

        for bit in bit_string:
            if bit == "0":
                if current.left is None:
                    raise ValueError(f"Некорректный бит '0' в текущем узле {current}")
                current = current.left
            elif bit == "1":
                if current.right is None:
                    raise ValueError(f"Некорректный бит '1' в текущем узле {current}")
                current = current.right
            else:
                raise ValueError(f"Недопустимый символ в битовой строке: {bit!r}")

            if current.is_leaf and current.char is not None:
                result.append(current.char)
                current = self.root

        if current is not self.root:
            raise ValueError("Битовая последовательность оборвалась до завершения символа")

        return "".join(result)

    def encode_to_bytes(self, text: str) -> tuple[bytes, int]:
        """Кодирует текст в компактный байтовый массив с указанием количества бит дополнения.

        :param text: Текст для кодирования.
        :return: Кортеж (байты_данных, число_бит_выравнивания).
        """
        bits = self.encode(text)
        if not bits:
            return b"", 0

        padding = (8 - (len(bits) % 8)) % 8
        padded_bits = bits + ("0" * padding)

        byte_arr = bytearray()
        for i in range(0, len(padded_bits), 8):
            byte_chunk = padded_bits[i : i + 8]
            byte_arr.append(int(byte_chunk, 2))

        return bytes(byte_arr), padding

    def decode_from_bytes(self, data: bytes, padding: int) -> str:
        """Декодирует текст из сжатого байтового массива и числа бит выравнивания.

        :param data: Сжатые байты.
        :param padding: Количество добавленных при выравнивании нулевых бит в конце (0..7).
        :return: Восстановленный исходный текст.
        """
        if not data:
            return ""

        bits_parts: list[str] = [f"{b:08b}" for b in data]
        full_bits = "".join(bits_parts)

        if padding > 0:
            full_bits = full_bits[:-padding]

        return self.decode(full_bits)


def huffman_encode(text: str) -> tuple[str, HuffmanTree]:
    """Кодирует исходный текст и возвращает битовую строку вместе с построенным деревом.

    :param text: Исходный текст.
    :return: Кортеж (битовая_строка, дерево_Хаффмана).
    """
    tree = HuffmanTree.from_text(text)
    encoded = tree.encode(text)
    return encoded, tree


def huffman_decode(bit_string: str, tree: HuffmanTree) -> str:
    """Декодирует битовую строку с помощью переданного дерева Хаффмана.

    :param bit_string: Строка бит ('0' и '1').
    :param tree: Дерево Хаффмана с кодовой таблицей.
    :return: Раскодированная строка.
    """
    return tree.decode(bit_string)
