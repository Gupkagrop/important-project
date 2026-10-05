"""Модульные тесты для сжатого префиксного дерева RadixTree и узла RadixNode."""

import pytest

from pocket_toolkit.structures.radix_tree import RadixNode, RadixTree


def test_radix_node_defaults() -> None:
    """Проверка инициализации узла по умолчанию."""
    node: RadixNode[int] = RadixNode()
    assert node.prefix == ""
    assert node.is_end_of_word is False
    assert node.value is None
    assert node.children == {}
    assert node.has_children is False
    assert node.children_count == 0
    assert "RadixNode" in repr(node)


def test_radix_node_custom_values() -> None:
    """Проверка узла с кастомными параметрами."""
    node: RadixNode[str] = RadixNode(prefix="rom", is_end_of_word=True, value="payload")
    assert node.prefix == "rom"
    assert node.is_end_of_word is True
    assert node.value == "payload"
    assert node.has_children is False
    assert node.children_count == 0

    node.children["a"] = RadixNode(prefix="an")
    assert node.has_children is True
    assert node.children_count == 1
    assert "children_count=1" in repr(node)


def test_radix_tree_init_empty() -> None:
    """Проверка инициализации пустого сжатого префиксного дерева."""
    tree: RadixTree[int] = RadixTree()
    assert len(tree) == 0
    assert tree.size == 0
    assert tree.is_empty() is True
    assert tree.case_sensitive is True
    assert tree.words() == []
    assert tree.keys() == []
    assert tree.items() == []
    assert tree.values() == []
    assert tree.longest_common_prefix() == ""
    assert tree.node_count == 1  # Только корневой узел
    assert repr(tree) == "RadixTree(size=0, node_count=1, case_sensitive=True)"


def test_radix_tree_init_with_words() -> None:
    """Проверка инициализации деревом списком слов."""
    words: list[str] = ["cat", "car", "cart", "dog"]
    tree: RadixTree[None] = RadixTree(words=words)
    assert len(tree) == 4
    assert tree.is_empty() is False
    for word in words:
        assert word in tree
    assert "cow" not in tree


def test_radix_tree_init_with_initial_items() -> None:
    """Проверка инициализации списком пар (ключ, значение)."""
    items: list[tuple[str, int]] = [("apple", 10), ("app", 5), ("banana", 20)]
    tree: RadixTree[int] = RadixTree(initial_items=items)
    assert len(tree) == 3
    assert tree["apple"] == 10
    assert tree["app"] == 5
    assert tree["banana"] == 20


def test_radix_tree_case_insensitive() -> None:
    """Проверка нечувствительности к регистру."""
    tree: RadixTree[int] = RadixTree(case_sensitive=False)
    tree.insert("Apple", 100)
    assert "apple" in tree
    assert "APPLE" in tree
    assert "Apple" in tree
    assert tree.get("aPpLe") == 100
    assert tree.starts_with("AP") is True
    assert tree.autocomplete("ap") == ["apple"]


def test_radix_tree_insert_search_and_contains() -> None:
    """Проверка базовой вставки, поиска и обновления значений."""
    tree: RadixTree[int] = RadixTree()
    tree.insert("python", 42)
    assert tree.search("python") is True
    assert "python" in tree
    assert tree.search("py") is False
    assert "py" not in tree
    assert tree.search("pythons") is False

    # Обновление существующего ключа
    tree.insert("python", 100)
    assert len(tree) == 1
    assert tree.get("python") == 100


def test_radix_tree_prefix_compression_and_node_count() -> None:
    """Проверка сжатия ребер и уменьшения количества узлов по сравнению со стандартным Trie."""
    tree: RadixTree[int] = RadixTree()
    # "test", "tester", "testing"
    # Должны сформировать: root -> "test" (word) -> "er" (word), "ing" (word)
    # Итого: root (1) + "test" (1) + "er" (1) + "ing" (1) = 4 узла
    tree.insert("test", 1)
    tree.insert("tester", 2)
    tree.insert("testing", 3)

    assert len(tree) == 3
    assert tree.node_count == 4
    assert tree["test"] == 1
    assert tree["tester"] == 2
    assert tree["testing"] == 3


def test_radix_tree_branch_splitting() -> None:
    """Проверка расщепления ребер при вставке частично совпадающих строк."""
    tree: RadixTree[int] = RadixTree()
    tree.insert("slow", 1)
    tree.insert("slower", 2)
    tree.insert("sloth", 3)

    # Общий префикс "slo", ответвления: "w" -> "er", "th"
    assert "slow" in tree
    assert "slower" in tree
    assert "sloth" in tree
    assert "slo" not in tree
    assert tree.starts_with("slo") is True
    assert tree.autocomplete("slo") == ["sloth", "slow", "slower"]


def test_radix_tree_empty_string_handling() -> None:
    """Проверка корректной обработки пустой строки."""
    tree: RadixTree[str] = RadixTree()
    assert "" not in tree
    assert tree.starts_with("") is False

    tree.insert("", "root_payload")
    assert len(tree) == 1
    assert "" in tree
    assert tree.get("") == "root_payload"
    assert tree[""] == "root_payload"
    assert tree.starts_with("") is True

    # Удаление пустой строки
    assert tree.remove("") is True
    assert "" not in tree
    assert len(tree) == 0
    assert tree.remove("") is False


def test_radix_tree_type_errors() -> None:
    """Проверка валидации входных типов."""
    tree: RadixTree[int] = RadixTree()

    with pytest.raises(TypeError, match="Ключ должен быть строкой"):
        tree.insert(123)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Ключ должен быть строкой"):
        tree.search(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Ключ должен быть строкой"):
        tree.get(45.6)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Ключ должен быть строкой"):
        tree.remove([1, 2])  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Ключ должен быть строкой"):
        tree.starts_with({"key": "val"})  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Текст должен быть строкой"):
        tree.find_longest_prefix_of(12345)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Лимит выборки не может быть отрицательным"):
        tree.autocomplete("test", limit=-1)

    with pytest.raises(ValueError, match="Лимит выборки не может быть отрицательным"):
        tree.find_items_with_prefix("test", limit=-5)


def test_radix_tree_get_and_getitem() -> None:
    """Проверка методов get и __getitem__."""
    tree: RadixTree[str] = RadixTree()
    tree["admin"] = "role_admin"
    tree["user"] = "role_user"

    assert tree.get("admin") == "role_admin"
    assert tree.get("guest") is None
    assert tree.get("guest", default="fallback") == "fallback"

    assert tree["admin"] == "role_admin"
    assert tree["user"] == "role_user"

    with pytest.raises(KeyError, match="Ключ 'guest' не найден"):
        _ = tree["guest"]

    with pytest.raises(KeyError, match="Ключ '' не найден"):
        _ = tree[""]


def test_radix_tree_remove_and_node_merging() -> None:
    """Проверка удаления слов и сжатия/слияния узлов."""
    tree: RadixTree[int] = RadixTree()
    tree.insert("tester", 1)
    tree.insert("testing", 2)
    # root -> "test" -> "er", "ing" (4 узла)
    assert tree.node_count == 4

    # Удаление листа "testing" должно объединить "test" и "er" в один узел "tester"
    assert tree.remove("testing") is True
    assert len(tree) == 1
    assert "testing" not in tree
    assert "tester" in tree
    # root (1) + "tester" (1) = 2 узла
    assert tree.node_count == 2

    # Удаление оставшегося слова
    assert tree.remove("tester") is True
    assert len(tree) == 0
    assert tree.node_count == 1
    assert tree.is_empty() is True

    # Удаление несуществующего ключа
    assert tree.remove("non_existing") is False


def test_radix_tree_remove_internal_node_merge() -> None:
    """Проверка удаления промежуточного ключевого узла и его слияния с дочерним."""
    tree: RadixTree[int] = RadixTree()
    tree.insert("test", 1)
    tree.insert("tester", 2)
    # root -> "test" (word) -> "er" (word) (3 узла)
    assert tree.node_count == 3

    # Удаление "test" (промежуточного узла с одним потомком "er")
    # Должно слить "test" и "er" в один узел "tester"
    assert tree.remove("test") is True
    assert len(tree) == 1
    assert "test" not in tree
    assert "tester" in tree
    assert tree.node_count == 2
    assert tree["tester"] == 2


def test_radix_tree_delitem() -> None:
    """Проверка оператора del tree[key]."""
    tree: RadixTree[int] = RadixTree()
    tree["alpha"] = 1
    tree["beta"] = 2

    del tree["alpha"]
    assert "alpha" not in tree
    assert len(tree) == 1

    with pytest.raises(KeyError, match="Ключ 'gamma' не найден"):
        del tree["gamma"]


def test_radix_tree_starts_with() -> None:
    """Проверка поиска по префиксу starts_with."""
    tree: RadixTree[int] = RadixTree()
    words: list[str] = ["apple", "application", "banana", "band"]
    for w in words:
        tree.insert(w)

    assert tree.starts_with("app") is True
    assert tree.starts_with("apple") is True
    assert tree.starts_with("appl") is True
    assert tree.starts_with("application") is True
    assert tree.starts_with("b") is True
    assert tree.starts_with("ban") is True
    assert tree.starts_with("band") is True
    assert tree.starts_with("c") is False
    assert tree.starts_with("apps") is False
    assert tree.starts_with("bandage") is False


def test_radix_tree_autocomplete() -> None:
    """Проверка автодополнения слов и работы лимита."""
    tree: RadixTree[int] = RadixTree()
    words: list[str] = ["apple", "app", "application", "apricot", "banana"]
    for idx, w in enumerate(words):
        tree.insert(w, idx)

    # Префикс "ap"
    matches: list[str] = tree.autocomplete("ap")
    assert matches == ["app", "apple", "application", "apricot"]

    # Лимиты
    assert tree.autocomplete("ap", limit=2) == ["app", "apple"]
    assert tree.autocomplete("ap", limit=0) == []
    assert tree.autocomplete("ap", limit=10) == [
        "app",
        "apple",
        "application",
        "apricot",
    ]

    # Несуществующий префикс
    assert tree.autocomplete("cat") == []

    # Псевдоним find_words_with_prefix
    assert tree.find_words_with_prefix("ap", limit=2) == ["app", "apple"]


def test_radix_tree_find_items_with_prefix() -> None:
    """Проверка извлечения пар (ключ, значение) по префиксу."""
    tree: RadixTree[int] = RadixTree()
    tree.insert("car", 10)
    tree.insert("card", 20)
    tree.insert("cart", 30)
    tree.insert("dog", 40)

    items: list[tuple[str, int | None]] = tree.find_items_with_prefix("car")
    assert items == [("car", 10), ("card", 20), ("cart", 30)]

    assert tree.find_items_with_prefix("car", limit=1) == [("car", 10)]
    assert tree.find_items_with_prefix("car", limit=0) == []
    assert tree.find_items_with_prefix("cat") == []


def test_radix_tree_count_words_with_prefix() -> None:
    """Проверка подсчета слов с заданным префиксом."""
    tree: RadixTree[int] = RadixTree()
    for w in ["cat", "car", "cart", "cartoon", "dog"]:
        tree.insert(w)

    assert tree.count_words_with_prefix("car") == 3
    assert tree.count_words_with_prefix("ca") == 4
    assert tree.count_words_with_prefix("cart") == 2
    assert tree.count_words_with_prefix("dog") == 1
    assert tree.count_words_with_prefix("bird") == 0
    assert tree.count_words_with_prefix("") == 5


def test_radix_tree_longest_common_prefix() -> None:
    """Проверка нахождения наибольшего общего префикса."""
    tree: RadixTree[int] = RadixTree()
    assert tree.longest_common_prefix() == ""

    tree.insert("flower")
    tree.insert("flow")
    tree.insert("flight")
    assert tree.longest_common_prefix() == "fl"

    tree.insert("dog")
    assert tree.longest_common_prefix() == ""

    # Если в дереве есть пустая строка, общий префикс пуст
    tree_with_empty: RadixTree[int] = RadixTree()
    tree_with_empty.insert("")
    tree_with_empty.insert("abc")
    assert tree_with_empty.longest_common_prefix() == ""


def test_radix_tree_find_longest_prefix_of() -> None:
    """Проверка нахождения самого длинного сохраненного префикса для текста (роутинг)."""
    tree: RadixTree[str] = RadixTree()
    tree.insert("/api", "api_root")
    tree.insert("/api/v1", "api_v1")
    tree.insert("/api/v1/users", "users_handler")
    tree.insert("/home", "home_page")

    # Сопоставление с путями
    assert tree.find_longest_prefix_of("/api/v1/users/42/profile") == "/api/v1/users"
    assert tree.find_longest_prefix_of("/api/v1/posts") == "/api/v1"
    assert tree.find_longest_prefix_of("/api/v2") == "/api"
    assert tree.find_longest_prefix_of("/unknown") == ""

    # Получение элемента (ключ, значение)
    item = tree.find_longest_prefix_item_of("/api/v1/users/42/profile")
    assert item == ("/api/v1/users", "users_handler")

    assert tree.find_longest_prefix_item_of("/unknown") is None


def test_radix_tree_iteration_and_protocols() -> None:
    """Проверка протоколов итерирования, ключей, значений и сравнения."""
    items: list[tuple[str, int]] = [("banana", 2), ("apple", 1), ("cherry", 3)]
    tree: RadixTree[int] = RadixTree(initial_items=items)

    # Итерация в лексикографическом порядке
    assert list(tree) == ["apple", "banana", "cherry"]
    assert tree.keys() == ["apple", "banana", "cherry"]
    assert tree.words() == ["apple", "banana", "cherry"]
    assert tree.values() == [1, 2, 3]
    assert tree.items() == [("apple", 1), ("banana", 2), ("cherry", 3)]

    # Сравнение с другим деревом и словарем
    tree_clone: RadixTree[int] = RadixTree(initial_items=items)
    assert tree == tree_clone
    assert tree == {"apple": 1, "banana": 2, "cherry": 3}
    assert tree != {"apple": 99}
    assert tree != "not_a_tree"

    # Очистка дерева
    tree.clear()
    assert len(tree) == 0
    assert tree.node_count == 1
    assert tree.is_empty() is True
    assert list(tree) == []
