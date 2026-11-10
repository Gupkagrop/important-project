"""Модульные тесты для алгоритма Дейкстры (dijkstra)."""

import math
import pytest
from pocket_toolkit.algorithms.dijkstra import (
    ShortestPathResult,
    dijkstra,
    find_shortest_path,
)


def test_dijkstra_missing_start() -> None:
    """Проверка ошибки при отсутствии стартовой вершины в графе."""
    graph = {"A": {"B": 1}}
    with pytest.raises(KeyError):
        dijkstra(graph, start="Z")


def test_dijkstra_negative_weight() -> None:
    """Проверка ошибки при наличии отрицательных весов."""
    graph = {"A": {"B": -5}, "B": {}}
    with pytest.raises(ValueError):
        dijkstra(graph, start="A")


def test_single_node() -> None:
    """Проверка графа из одной изолированной вершины."""
    graph = {"A": {}}
    result = dijkstra(graph, start="A")
    assert result.distance_to("A") == 0.0
    assert result.has_path_to("A") is True
    assert result.reconstruct_path("A") == ["A"]
    assert result.has_path_to("B") is False
    assert math.isinf(result.distance_to("B"))
    assert result.reconstruct_path("B") is None


def test_linear_graph() -> None:
    """Проверка линейного направленного графа."""
    graph = {
        "A": {"B": 2.5},
        "B": {"C": 1.5},
        "C": {"D": 4.0},
        "D": {},
    }
    result = dijkstra(graph, start="A")
    assert result.distance_to("D") == 8.0
    assert result.reconstruct_path("D") == ["A", "B", "C", "D"]

    path_and_len = find_shortest_path(graph, "A", "D")
    assert path_and_len is not None
    assert path_and_len == (["A", "B", "C", "D"], 8.0)


def test_diamond_graph_shortest_route() -> None:
    """Проверка выбора наикратчайшего пути при ветвлении."""
    graph = {
        "A": {"B": 5, "C": 2},
        "B": {"D": 1},
        "C": {"B": 1, "D": 8},
        "D": {},
    }
    # Путь A -> C -> B -> D равен 2 + 1 + 1 = 4 (короче, чем A -> B -> D = 6)
    result = dijkstra(graph, start="A")
    assert result.distance_to("D") == 4.0
    assert result.reconstruct_path("D") == ["A", "C", "B", "D"]


def test_early_stopping_with_target() -> None:
    """Проверка ранней остановки поиска при достижении target."""
    graph = {
        "A": {"B": 1, "C": 10},
        "B": {"target": 2},
        "target": {},
        "C": {"unreachable": 100},
        "unreachable": {},
    }
    result = dijkstra(graph, start="A", target="target")
    assert result.distance_to("target") == 3.0
    assert result.reconstruct_path("target") == ["A", "B", "target"]


def test_disconnected_graph() -> None:
    """Проверка поведения на несвязном графе."""
    graph = {
        "A": {"B": 2},
        "B": {},
        "X": {"Y": 5},
        "Y": {},
    }
    result = dijkstra(graph, start="A")
    assert result.has_path_to("X") is False
    assert result.reconstruct_path("X") is None
    assert find_shortest_path(graph, "A", "X") is None


def test_tuple_edges_and_numeric_nodes() -> None:
    """Проверка работы со списком кортежей ребер и целочисленными вершинами."""
    graph = {
        1: [(2, 10), (3, 30)],
        2: [(4, 15)],
        3: [(4, 5)],
        4: [],
    }
    res = dijkstra(graph, start=1)
    # 1 -> 2 -> 4 (25) vs 1 -> 3 -> 4 (35)
    assert res.distance_to(4) == 25.0
    assert res.reconstruct_path(4) == [1, 2, 4]
