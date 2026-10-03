"""Модульные тесты для префиксного дерева Trie и узла TrieNode."""

import pytest

from pocket_toolkit.structures.trie import Trie, TrieNode


def test_trie_node_defaults() -> None:
    """Проверка инициализации узла по умолчанию."""
    node: TrieNode[int] = TrieNode()
    assert node.is_end_of_word is False
    assert node.value is None
    assert node.children == {}
    assert node.has_children is False
    assert "TrieNode" in repr(node)


def test_trie_node_custom_values() -> None:
    """Проверка узла с кастомными параметрами."""
    node: TrieNode[str] = TrieNode(is_end_of_word=True, value="test_payload")
    assert node.is_end_of_word is True
    assert node.value == "test_payload"
    assert node.has_children is False

    node.children["a"] = TrieNode()
    assert node.has_children is True
    assert "children_count=1" in repr(node)


def test_trie_init_empty() -> None:
    """Проверка инициализации пустого префиксного дерева."""
    trie: Trie[int] = Trie()
    assert len(trie) == 0
    assert trie.is_empty() is True
    assert trie.case_sensitive is True
    assert trie.words() == []
    assert trie.items() == []
    assert trie.values() == []
    assert trie.longest_common_prefix() == ""
    assert repr(trie) == "Trie(size=0, case_sensitive=True)"


def test_trie_init_with_words() -> None:
    """Проверка инициализации деревом списком слов."""
    words: list[str] = ["cat", "car", "cart", "dog"]
    trie: Trie[None] = Trie(words=words)
    assert len(trie) == 4
    assert trie.is_empty() is False
    for word in words:
        assert word in trie


def test_trie_init_with_initial_items() -> None:
    """Проверка инициализации деревом списком пар (ключ, значение)."""
    items: list[tuple[str, int]] = [("apple", 10), ("app", 5), ("banana", 20)]
    trie: Trie[int] = Trie(initial_items=items)
    assert len(trie) == 3
    assert trie["apple"] == 10
    assert trie["app"] == 5
    assert trie["banana"] == 20


def test_trie_case_insensitive() -> None:
    """Проверка нечувствительности к регистру."""
    trie: Trie[int] = Trie(case_sensitive=False)
    trie.insert("Apple", 100)
    assert "apple" in trie
    assert "APPLE" in trie
    assert "Apple" in trie
    assert trie.get("aPpLe") == 100
    assert trie.starts_with("AP") is True
    assert trie.autocomplete("ap") == ["apple"]


def test_trie_insert_search_and_contains() -> None:
    """Проверка базовой вставки и поиска слов."""
    trie: Trie[int] = Trie()
    trie.insert("python", 42)
    assert trie.search("python") is True
    assert "python" in trie
    assert trie.search("py") is False
    assert "py" not in trie
    assert trie.search("pythons") is False

    # Повторная вставка обновляет значение и не увеличивает размер
    trie.insert("python", 100)
    assert len(trie) == 1
    assert trie.get("python") == 100


def test_trie_empty_string_handling() -> None:
    """Проверка корректной обработки пустой строки."""
    trie: Trie[str] = Trie()
    assert "" not in trie
    assert trie.starts_with("") is False

    trie.insert("", "root_val")
    assert len(trie) == 1
    assert "" in trie
    assert trie.get("") == "root_val"
    assert trie.starts_with("") is True

    removed: bool = trie.remove("")
    assert removed is True
    assert len(trie) == 0
    assert "" not in trie


def test_trie_starts_with() -> None:
    """Проверка метода starts_with."""
    trie: Trie[None] = Trie(words=["algorithm", "algebra", "alien"])
    assert trie.starts_with("al") is True
    assert trie.starts_with("alg") is True
    assert trie.starts_with("alien") is True
    assert trie.starts_with("aliens") is False
    assert trie.starts_with("beta") is False


def test_trie_dict_like_access() -> None:
    """Проверка доступа по ключу через квадратные скобки."""
    trie: Trie[int] = Trie()
    trie["key1"] = 10
    trie["key2"] = 20

    assert trie["key1"] == 10
    assert trie["key2"] == 20
    assert trie.get("key1") == 10
    assert trie.get("missing", 999) == 999

    with pytest.raises(KeyError):
        _ = trie["missing"]


def test_trie_remove_leaf_word() -> None:
    """Проверка удаления листового слова с очисткой узлов."""
    trie: Trie[None] = Trie(words=["car", "carpet"])
    assert len(trie) == 2

    # Узел 'carpet' является продолжением 'car'
    assert trie.remove("carpet") is True
    assert len(trie) == 1
    assert "carpet" not in trie
    assert "car" in trie

    # Проверяем, что узлы 'p', 'e', 't' были удалены
    r_node: TrieNode[None] | None = trie.root.children["c"].children["a"].children["r"]
    assert r_node is not None
    assert "p" not in r_node.children


def test_trie_remove_prefix_word() -> None:
    """Проверка удаления слова, являющегося префиксом другого слова."""
    trie: Trie[None] = Trie(words=["car", "carpet"])
    assert trie.remove("car") is True
    assert len(trie) == 1
    assert "car" not in trie
    assert "carpet" in trie
    assert trie.search("carpet") is True


def test_trie_remove_nonexistent_and_delitem() -> None:
    """Проверка удаления несуществующих слов и оператора del."""
    trie: Trie[int] = Trie()
    trie["hello"] = 1

    assert trie.remove("world") is False
    assert trie.remove("hell") is False

    del trie["hello"]
    assert "hello" not in trie
    assert len(trie) == 0

    with pytest.raises(KeyError):
        del trie["missing"]


def test_trie_autocomplete_and_find_words() -> None:
    """Проверка автодополнения и поиска по префиксу."""
    words: list[str] = ["band", "banana", "banner", "bat", "apple"]
    trie: Trie[None] = Trie(words=words)

    ban_words: list[str] = trie.autocomplete("ban")
    assert ban_words == ["banana", "band", "banner"]

    all_words: list[str] = trie.autocomplete("")
    assert all_words == ["apple", "banana", "band", "banner", "bat"]

    assert trie.find_words_with_prefix("ba", limit=2) == ["banana", "band"]
    assert trie.autocomplete("xyz") == []
    assert trie.autocomplete("ban", limit=0) == []

    with pytest.raises(ValueError):
        trie.autocomplete("ban", limit=-1)


def test_trie_find_items_with_prefix() -> None:
    """Проверка получения элементов (слово, значение) по префиксу."""
    trie: Trie[int] = Trie()
    trie["apple"] = 1
    trie["app"] = 2
    trie["apricot"] = 3
    trie["banana"] = 4

    items: list[tuple[str, int | None]] = trie.find_items_with_prefix("ap")
    assert items == [("app", 2), ("apple", 1), ("apricot", 3)]

    limited_items: list[tuple[str, int | None]] = trie.find_items_with_prefix("ap", limit=2)
    assert limited_items == [("app", 2), ("apple", 1)]

    assert trie.find_items_with_prefix("none") == []
    assert trie.find_items_with_prefix("ap", limit=0) == []

    with pytest.raises(ValueError):
        trie.find_items_with_prefix("ap", limit=-5)


def test_trie_count_words_with_prefix() -> None:
    """Проверка подсчета слов с заданным префиксом."""
    words: list[str] = ["cat", "car", "cart", "carpet", "dog"]
    trie: Trie[None] = Trie(words=words)

    assert trie.count_words_with_prefix("c") == 4
    assert trie.count_words_with_prefix("car") == 3
    assert trie.count_words_with_prefix("cart") == 1
    assert trie.count_words_with_prefix("d") == 1
    assert trie.count_words_with_prefix("z") == 0
    assert trie.count_words_with_prefix("") == 5


def test_trie_longest_common_prefix() -> None:
    """Проверка вычисления наибольшего общего префикса."""
    trie1: Trie[None] = Trie(words=["flower", "flow", "flight"])
    assert trie1.longest_common_prefix() == "fl"

    trie2: Trie[None] = Trie(words=["interspecies", "interstellar", "interstate"])
    assert trie2.longest_common_prefix() == "inters"

    trie3: Trie[None] = Trie(words=["dog", "racecar", "car"])
    assert trie3.longest_common_prefix() == ""

    trie4: Trie[None] = Trie(words=["solo"])
    assert trie4.longest_common_prefix() == "solo"

    trie5: Trie[None] = Trie(words=["prefix", "prefix_longer"])
    assert trie5.longest_common_prefix() == "prefix"

    trie6: Trie[None] = Trie()
    assert trie6.longest_common_prefix() == ""

    trie7: Trie[None] = Trie(words=[""])
    assert trie7.longest_common_prefix() == ""

    trie8: Trie[None] = Trie(words=["", "abc"])
    assert trie8.longest_common_prefix() == ""
    assert isinstance(trie8.root, TrieNode)


def test_trie_iteration_and_clear() -> None:
    """Проверка итератора, методов items/values и очистки дерева."""
    trie: Trie[int] = Trie()
    trie["c"] = 3
    trie["a"] = 1
    trie["b"] = 2

    # Итератор возвращает слова в лексикографическом порядке
    assert list(trie) == ["a", "b", "c"]
    assert trie.values() == [1, 2, 3]
    assert trie.items() == [("a", 1), ("b", 2), ("c", 3)]

    trie.clear()
    assert len(trie) == 0
    assert trie.is_empty() is True
    assert list(trie) == []
    assert trie.root.children == {}


def test_trie_type_validation() -> None:
    """Проверка валидации некорректных типов аргументов."""
    trie: Trie[int] = Trie()

    # Нестроковые ключи должны вызывать TypeError
    with pytest.raises(TypeError):
        # pyright: ignore
        trie.insert(123)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        # pyright: ignore
        _ = 123 in trie  # type: ignore[operator]

    with pytest.raises(TypeError):
        # pyright: ignore
        trie.starts_with(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        # pyright: ignore
        trie.get(12.34)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        # pyright: ignore
        trie.remove([])  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        # pyright: ignore
        trie.count_words_with_prefix(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        # pyright: ignore
        trie.autocomplete(set())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        # pyright: ignore
        trie.find_items_with_prefix(b"bytes")  # type: ignore[arg-type]
