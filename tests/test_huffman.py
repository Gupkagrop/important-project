"""Модульные тесты для модуля сжатия методом Хаффмана (huffman)."""

import pytest
from pocket_toolkit.algorithms.huffman import (
    HuffmanNode,
    HuffmanTree,
    huffman_decode,
    huffman_encode,
)


def test_huffman_node_basics() -> None:
    """Проверка создания и свойств узла дерева Хаффмана."""
    leaf = HuffmanNode(char="a", freq=5)
    assert leaf.is_leaf is True
    assert leaf.char == "a"
    assert leaf.freq == 5

    parent = HuffmanNode(char=None, freq=10, left=leaf)
    assert parent.is_leaf is False
    assert parent.char is None
    assert "HuffmanNode" in repr(leaf)

    # Проверка порядка в куче
    assert leaf < parent


def test_empty_text() -> None:
    """Проверка кодирования и декодирования пустой строки."""
    tree = HuffmanTree.from_text("")
    assert tree.codebook == {}
    assert tree.encode("") == ""
    assert tree.decode("") == ""

    encoded, t = huffman_encode("")
    assert encoded == ""
    assert huffman_decode("", t) == ""

    data, padding = tree.encode_to_bytes("")
    assert data == b""
    assert padding == 0
    assert tree.decode_from_bytes(data, padding) == ""


def test_single_character_repeated() -> None:
    """Проверка строки, состоящей из одного повторяющегося символа."""
    text = "aaaaaa"
    encoded, tree = huffman_encode(text)
    assert encoded == "000000"
    decoded = huffman_decode(encoded, tree)
    assert decoded == text

    # Байтовая упаковка
    data, padding = tree.encode_to_bytes(text)
    assert tree.decode_from_bytes(data, padding) == text


def test_standard_text_roundtrip() -> None:
    """Проверка кодирования и восстановления классических строк."""
    texts = [
        "abracadabra",
        "this is an example of a huffman tree",
        "hello world! 12345",
        "съешь же ещё этих мягких французских булок, да выпей чаю",
    ]

    for text in texts:
        encoded, tree = huffman_encode(text)
        assert len(encoded) > 0
        decoded = huffman_decode(encoded, tree)
        assert decoded == text

        # Проверка байтового кодирования
        raw_bytes, padding = tree.encode_to_bytes(text)
        restored = tree.decode_from_bytes(raw_bytes, padding)
        assert restored == text


def test_unseen_character_error() -> None:
    """Проверка ошибки кодирования символа, отсутствующего в дереве."""
    tree = HuffmanTree.from_text("abc")
    with pytest.raises(KeyError):
        tree.encode("abcd")


def test_corrupted_bit_string_errors() -> None:
    """Проверка обработки некорректных или обрезанных битовых строк."""
    tree = HuffmanTree.from_text("hello")

    # Недопустимый символ в битовой строке
    with pytest.raises(ValueError):
        tree.decode("01201")

    # Обрезанная битовая цепочка (не доходит до листа)
    encoded = tree.encode("hello")
    with pytest.raises(ValueError):
        tree.decode(encoded[:-1])

    # Пустое дерево не может раскодировать непустую строку
    empty_tree = HuffmanTree.from_text("")
    with pytest.raises(ValueError):
        empty_tree.decode("0")
