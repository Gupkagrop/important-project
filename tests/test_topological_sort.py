"""Модульные тесты для модуля топологической сортировки (topological_sort)."""

import pytest
from pocket_toolkit.algorithms.topological_sort import (
    CyclicDependencyError,
    calculate_in_degrees,
    is_dag,
    topological_sort,
    topological_sort_dfs,
)


def _validate_order[T](graph: dict[T, list[T]], order: list[T]) -> bool:
    """Вспомогательная функция проверки корректности топологического порядка."""
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)

    if set(order) != all_nodes:
        return False
    if len(order) != len(all_nodes):
        return False

    indices = {node: idx for idx, node in enumerate(order)}
    for u, neighbors in graph.items():
        for v in neighbors:
            if indices[u] >= indices[v]:
                return False
    return True


def test_empty_graph() -> None:
    """Проверка сортировки пустого графа."""
    assert topological_sort({}) == []
    assert topological_sort_dfs({}) == []
    assert is_dag({}) is True
    assert calculate_in_degrees({}) == {}


def test_single_node() -> None:
    """Проверка сортировки графа из одной вершины."""
    graph = {"A": []}
    assert topological_sort(graph) == ["A"]
    assert topological_sort_dfs(graph) == ["A"]
    assert is_dag(graph) is True
    assert calculate_in_degrees(graph) == {"A": 0}


def test_linear_chain() -> None:
    """Проверка сортировки линейной цепочки зависимостей."""
    graph = {"A": ["B"], "B": ["C"], "C": ["D"], "D": []}
    expected = ["A", "B", "C", "D"]
    order_kahn = topological_sort(graph)
    order_dfs = topological_sort_dfs(graph)

    assert order_kahn == expected
    assert order_dfs == expected
    assert _validate_order(graph, order_kahn)
    assert _validate_order(graph, order_dfs)
    assert is_dag(graph) is True


def test_diamond_dag() -> None:
    """Проверка ромбовидного направленного графа."""
    graph = {
        "build": ["test_unit", "test_integration"],
        "test_unit": ["package"],
        "test_integration": ["package"],
        "package": [],
    }
    order_kahn = topological_sort(graph)
    order_dfs = topological_sort_dfs(graph)

    assert _validate_order(graph, order_kahn)
    assert _validate_order(graph, order_dfs)
    assert is_dag(graph) is True


def test_disconnected_components() -> None:
    """Проверка графа с несвязными компонентами."""
    graph = {
        "A": ["B"],
        "C": ["D"],
        "E": [],
    }
    order_kahn = topological_sort(graph)
    order_dfs = topological_sort_dfs(graph)

    assert _validate_order(graph, order_kahn)
    assert _validate_order(graph, order_dfs)
    assert is_dag(graph) is True


def test_cycle_detection_self_loop() -> None:
    """Проверка обнаружения петли на одной вершине."""
    graph = {"A": ["A"]}

    with pytest.raises(CyclicDependencyError) as exc_kahn:
        topological_sort(graph)
    assert "A" in exc_kahn.value.cycle_nodes

    with pytest.raises(CyclicDependencyError) as exc_dfs:
        topological_sort_dfs(graph)
    assert "A" in exc_dfs.value.cycle_nodes

    assert is_dag(graph) is False


def test_cycle_detection_simple() -> None:
    """Проверка обнаружения простого двухвершинного цикла."""
    graph = {"A": ["B"], "B": ["A"]}

    with pytest.raises(CyclicDependencyError):
        topological_sort(graph)

    with pytest.raises(CyclicDependencyError) as exc_dfs:
        topological_sort_dfs(graph)
    assert len(exc_dfs.value.cycle_nodes) > 1

    assert is_dag(graph) is False


def test_cycle_detection_in_larger_graph() -> None:
    """Проверка обнаружения цикла внутри большего графа."""
    graph = {
        "start": ["A"],
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],
        "end": [],
    }

    with pytest.raises(CyclicDependencyError):
        topological_sort(graph)

    with pytest.raises(CyclicDependencyError):
        topological_sort_dfs(graph)

    assert is_dag(graph) is False


def test_integer_and_tuple_nodes() -> None:
    """Проверка работы с целочисленными вершинами и кортежами."""
    graph_int = {1: [2, 3], 2: [4], 3: [4], 4: []}
    order = topological_sort(graph_int)
    assert _validate_order(graph_int, order)

    graph_tuples = {(0, 0): [(0, 1), (1, 0)], (0, 1): [(1, 1)], (1, 0): [(1, 1)], (1, 1): []}
    order_tuple = topological_sort(graph_tuples)
    assert _validate_order(graph_tuples, order_tuple)
