"""Модуль алгоритма Дейкстры (Dijkstra Shortest Path).

Предоставляет алгоритм поиска кратчайших путей во взвешенных ориентированных
и неориентированных графах с неотрицательными весами ребер,
структуру результатов `ShortestPathResult` с восстановлением маршрута,
а также вспомогательные функции прямого поиска пути между двумя вершинами.
"""

from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass
import heapq
import math
from typing import TypeVar

T = TypeVar("T", bound=Hashable)


@dataclass(slots=True)
class ShortestPathResult[T: Hashable]:
    """Результат вычисления кратчайших путей из стартовой вершины."""

    start: T
    distances: dict[T, float]
    predecessors: dict[T, T | None]

    def has_path_to(self, target: T) -> bool:
        """Проверяет, достижима ли целевая вершина из стартовой."""
        return target in self.distances and not math.isinf(self.distances[target])

    def distance_to(self, target: T) -> float:
        """Возвращает расстояние до целевой вершины (или float('inf'), если недостижима)."""
        return self.distances.get(target, float("inf"))

    def reconstruct_path(self, target: T) -> list[T] | None:
        """Восстанавливает последовательность вершин кратчайшего пути от start до target.

        :param target: Целевая вершина.
        :return: Список вершин пути от стартовой до целевой или None, если путь отсутствует.
        """
        if not self.has_path_to(target):
            return None

        path: list[T] = []
        current: T | None = target

        while current is not None:
            path.append(current)
            if current == self.start:
                break
            current = self.predecessors.get(current)

        path.reverse()
        if not path or path[0] != self.start:
            return None

        return path


def _get_neighbors[T: Hashable](
    raw_edges: Mapping[T, float | int] | Iterable[tuple[T, float | int]],
) -> list[tuple[T, float]]:
    """Приводит ребра вершины к нормализованному списку пар (сосед, вес)."""
    if isinstance(raw_edges, Mapping):
        return [(neighbor, float(weight)) for neighbor, weight in raw_edges.items()]
    return [(neighbor, float(weight)) for neighbor, weight in raw_edges]


def dijkstra[T: Hashable](
    graph: Mapping[T, Mapping[T, float | int] | Iterable[tuple[T, float | int]]],
    start: T,
    target: T | None = None,
) -> ShortestPathResult[T]:
    """Вычисляет кратчайшие расстояния от вершины start до всех вершин (или до target).

    :param graph: Словарь смежности графа с весами ребер.
    :param start: Исходная вершина.
    :param target: Опциональная целевая вершина для ранней остановки поиска.
    :return: Объект `ShortestPathResult[T]` с расстояниями и предшественниками.
    :raises KeyError: Если стартовая вершина отсутствует в графе.
    :raises ValueError: Если обнаружено ребро с отрицательным весом.
    """
    if start not in graph:
        raise KeyError(f"Стартовая вершина {start!r} отсутствует в графе")

    distances: dict[T, float] = {start: 0.0}
    predecessors: dict[T, T | None] = {start: None}

    # Приоритетная очередь: (текущее_расстояние, счетчик, вершина)
    pq: list[tuple[float, int, T]] = [(0.0, 0, start)]
    visited: set[T] = set()
    counter: int = 1

    while pq:
        dist, _, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)

        if target is not None and u == target:
            break

        if u not in graph:
            continue

        for v, weight in _get_neighbors(graph[u]):
            if weight < 0:
                raise ValueError(
                    f"Алгоритм Дейкстры не поддерживает отрицательные веса: ребро ({u} -> {v}) с весом {weight}"
                )

            new_dist = dist + weight
            if v not in distances or new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, counter, v))
                counter += 1

    return ShortestPathResult(start=start, distances=distances, predecessors=predecessors)


def find_shortest_path[T: Hashable](
    graph: Mapping[T, Mapping[T, float | int] | Iterable[tuple[T, float | int]]],
    start: T,
    target: T,
) -> tuple[list[T], float] | None:
    """Находит кратчайший путь между вершинами start и target и его суммарный вес.

    :param graph: Граф с весами.
    :param start: Стартовая вершина.
    :param target: Конечная вершина.
    :return: Кортеж (список_вершин_пути, суммарная_длина) или None, если путь не существует.
    """
    result = dijkstra(graph, start=start, target=target)
    path = result.reconstruct_path(target)
    if path is None:
        return None
    return path, result.distance_to(target)
