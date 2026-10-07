"""Модульные тесты для структуры непересекающихся множеств DisjointSet."""

import pytest

from pocket_toolkit.structures.disjoint_set import DisjointSet


def test_disjoint_set_empty_state() -> None:
    """Проверка начального состояния пустой структуры DisjointSet."""
    dsu: DisjointSet[int] = DisjointSet()
    assert len(dsu) == 0
    assert dsu.num_elements == 0
    assert dsu.num_sets == 0
    assert bool(dsu) is False
    assert list(dsu) == []
    assert dsu.subsets() == []
    assert dsu.subsets_dict() == {}
    assert dsu.roots() == set()
    assert repr(dsu) == "DisjointSet(elements=0, sets=0)"


def test_disjoint_set_init_with_elements_and_pairs() -> None:
    """Проверка инициализации начальным набором элементов и парами связей."""
    dsu: DisjointSet[str] = DisjointSet(
        elements=["a", "b", "c", "d"],
        pairs=[("a", "b"), ("c", "d")],
    )
    assert len(dsu) == 4
    assert dsu.num_sets == 2
    assert dsu.connected("a", "b") is True
    assert dsu.connected("c", "d") is True
    assert dsu.connected("a", "c") is False


def test_disjoint_set_make_set_and_add() -> None:
    """Проверка создания единичных множеств через make_set и add."""
    dsu: DisjointSet[int] = DisjointSet()
    assert dsu.make_set(1) is True
    assert dsu.add(2) is True
    assert 1 in dsu
    assert 2 in dsu
    assert 3 not in dsu
    assert len(dsu) == 2
    assert dsu.num_sets == 2

    # Повторное добавление должно возвращать False
    assert dsu.make_set(1) is False
    assert dsu.add(2) is False
    assert len(dsu) == 2
    assert dsu.num_sets == 2


def test_disjoint_set_update() -> None:
    """Проверка массового добавления элементов через метод update."""
    dsu: DisjointSet[int] = DisjointSet()
    dsu.update([10, 20, 30, 20])
    assert len(dsu) == 3
    assert dsu.num_sets == 3
    assert {10, 20, 30}.issubset(set(dsu))


def test_disjoint_set_find_and_path_compression() -> None:
    """Проверка поиска представителя и работы эвристики сжатия путей."""
    dsu: DisjointSet[int] = DisjointSet([1, 2, 3, 4])
    dsu.union(1, 2)
    dsu.union(2, 3)
    dsu.union(3, 4)

    root = dsu.find(4)
    assert root == dsu.find(1)
    assert root == dsu.find(2)
    assert root == dsu.find(3)

    # После find(4) все узлы должны указывать непосредственно на root в _parent
    assert dsu._parent[4] == root
    assert dsu._parent[3] == root
    assert dsu._parent[2] == root
    assert dsu._parent[1] == root


def test_disjoint_set_find_missing_raises_key_error() -> None:
    """Проверка вызова KeyError при вызове find для несуществующего элемента."""
    dsu: DisjointSet[str] = DisjointSet(["alpha"])
    with pytest.raises(KeyError, match="не зарегистрирован"):
        dsu.find("beta")


def test_disjoint_set_union_by_rank() -> None:
    """Проверка объединения подмножеств с учетом рангов деревьев."""
    dsu: DisjointSet[int] = DisjointSet([1, 2, 3, 4])

    # Объединяем (1, 2): ранги были 0, станут: у корня 1, у дочернего 0
    assert dsu.union(1, 2) is True
    root_12 = dsu.find(1)
    assert dsu.get_rank(root_12) == 1
    assert dsu.set_size(1) == 2

    # Объединяем (3, 4): ранг у корня 1
    assert dsu.union(3, 4) is True
    root_34 = dsu.find(3)
    assert dsu.get_rank(root_34) == 1
    assert dsu.set_size(3) == 2

    # Объединяем два множества с одинаковым рангом 1 -> ранг нового корня должен стать 2
    assert dsu.union(1, 3) is True
    final_root = dsu.find(1)
    assert dsu.get_rank(final_root) == 2
    assert dsu.set_size(1) == 4
    assert dsu.num_sets == 1

    # Повторное объединение уже связанных элементов
    assert dsu.union(2, 4) is False
    assert dsu.num_sets == 1


def test_disjoint_set_union_asymmetric_ranks() -> None:
    """Проверка подвязки дерева меньшего ранга к дереву большего ранга."""
    dsu: DisjointSet[int] = DisjointSet([1, 2, 3])
    dsu.union(1, 2)  # дерево {1, 2} имеет ранг 1
    tree_root = dsu.find(1)

    # 3 имеет ранг 0. Подвязываем 3 к дереву {1, 2}
    dsu.union(tree_root, 3)
    # Ранг дерева большего размера не должен измениться
    assert dsu.find(3) == tree_root
    assert dsu.get_rank(tree_root) == 1
    assert dsu.set_size(tree_root) == 3


def test_disjoint_set_union_with_create_missing() -> None:
    """Проверка флага create_missing при объединении."""
    dsu: DisjointSet[str] = DisjointSet()
    assert dsu.union("x", "y", create_missing=True) is True
    assert len(dsu) == 2
    assert dsu.connected("x", "y") is True

    # Без флага create_missing должно выбрасываться исключение
    with pytest.raises(KeyError, match="не зарегистрирован"):
        dsu.union("x", "missing_node")


def test_disjoint_set_connected_and_is_connected() -> None:
    """Проверка проверки связности элементов."""
    dsu: DisjointSet[int] = DisjointSet([1, 2, 3])
    dsu.union(1, 2)

    assert dsu.connected(1, 2) is True
    assert dsu.is_connected(2, 1) is True
    assert dsu.connected(1, 3) is False
    assert dsu.is_connected(2, 3) is False

    with pytest.raises(KeyError, match="не зарегистрирован"):
        dsu.connected(1, 999)


def test_disjoint_set_size_and_get_set() -> None:
    """Проверка получения размера подмножества и выборки всех элементов компоненты."""
    dsu: DisjointSet[str] = DisjointSet(["a", "b", "c", "d", "e"])
    dsu.union("a", "b")
    dsu.union("b", "c")

    assert dsu.set_size("a") == 3
    assert dsu.get_set_size("b") == 3
    assert dsu.get_set_size("c") == 3
    assert dsu.set_size("d") == 1

    assert dsu.get_set("a") == {"a", "b", "c"}
    assert dsu.get_set("b") == {"a", "b", "c"}
    assert dsu.get_set("d") == {"d"}

    with pytest.raises(KeyError):
        dsu.set_size("missing")
    with pytest.raises(KeyError):
        dsu.get_rank("missing")
    with pytest.raises(KeyError):
        dsu.get_set("missing")


def test_disjoint_set_subsets_and_roots() -> None:
    """Проверка получения словаря подмножеств, списка компонент и множества корней."""
    dsu: DisjointSet[int] = DisjointSet([1, 2, 3, 4, 5])
    dsu.union(1, 2)
    dsu.union(3, 4)

    roots = dsu.roots()
    assert len(roots) == 3
    assert dsu.find(1) in roots
    assert dsu.find(3) in roots
    assert dsu.find(5) in roots

    groups = dsu.subsets_dict()
    assert len(groups) == 3
    assert groups[dsu.find(1)] == {1, 2}
    assert groups[dsu.find(3)] == {3, 4}
    assert groups[dsu.find(5)] == {5}

    subsets = dsu.subsets()
    assert len(subsets) == 3
    canonical = {frozenset(s) for s in subsets}
    assert canonical == {frozenset({1, 2}), frozenset({3, 4}), frozenset({5})}


def test_disjoint_set_clear() -> None:
    """Проверка полной очистки структуры."""
    dsu: DisjointSet[int] = DisjointSet([1, 2, 3], pairs=[(1, 2)])
    assert len(dsu) == 3
    assert dsu.num_sets == 2

    dsu.clear()
    assert len(dsu) == 0
    assert dsu.num_sets == 0
    assert bool(dsu) is False
    assert dsu.subsets() == []


def test_disjoint_set_copy() -> None:
    """Проверка независимости созданной копии."""
    dsu: DisjointSet[str] = DisjointSet(["a", "b", "c"], pairs=[("a", "b")])
    clone = dsu.copy()

    assert clone == dsu
    assert clone.num_sets == dsu.num_sets
    assert clone.connected("a", "b") is True

    # Модификация копии не затрагивает оригинал
    clone.union("b", "c")
    assert clone.num_sets == 1
    assert dsu.num_sets == 2
    assert dsu.connected("a", "c") is False
    assert clone.connected("a", "c") is True


def test_disjoint_set_equality() -> None:
    """Проверка оператора сравнения на равенство (__eq__)."""
    dsu1: DisjointSet[int] = DisjointSet([1, 2, 3, 4], pairs=[(1, 2), (3, 4)])
    dsu2: DisjointSet[int] = DisjointSet([1, 2, 3, 4], pairs=[(2, 1), (4, 3)])
    dsu3: DisjointSet[int] = DisjointSet([1, 2, 3, 4], pairs=[(1, 3), (2, 4)])
    dsu4: DisjointSet[int] = DisjointSet([1, 2, 3])

    assert dsu1 == dsu2
    assert dsu1 != dsu3
    assert dsu1 != dsu4
    assert (dsu1 == "not_a_dsu") is False


def test_disjoint_set_stress_large_chain() -> None:
    """Нагрузочный тест на глубокую цепочку для проверки отсутствия RecursionError."""
    n: int = 1000
    elements = list(range(n))
    dsu: DisjointSet[int] = DisjointSet(elements)

    # Последовательно объединяем в длинную цепочку
    for i in range(n - 1):
        dsu.union(i, i + 1)

    assert dsu.num_sets == 1
    assert len(dsu) == n
    assert dsu.set_size(0) == n

    # Проверяем, что все элементы связаны
    for i in range(n):
        assert dsu.connected(0, i) is True
