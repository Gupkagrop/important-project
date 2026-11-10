"""Модуль алгоритмов топологической сортировки графов.

Предоставляет алгоритм Кана (Kahn's algorithm) и обход в глубину (DFS)
для топологического упорядочивания вершин в направленных ациклических графах (DAG),
а также вспомогательные функции проверки на ацикличность и вычисления полустепеней захода.
"""

from collections import deque
from collections.abc import Hashable, Iterable, Iterator, Mapping, Sequence
from typing import TypeVar

T = TypeVar("T", bound=Hashable)


class CyclicDependencyError(ValueError):
    """Исключение, возникающее при обнаружении цикла в графе зависимостей."""

    def __init__(self, message: str, cycle_nodes: Sequence[Hashable] | None = None) -> None:
        """Инициализирует ошибку обнаружения цикла.

        :param message: Пояснительное сообщение об ошибке.
        :param cycle_nodes: Список вершин, образующих или вовлеченных в цикл.
        """
        super().__init__(message)
        self.cycle_nodes: tuple[Hashable, ...] = tuple(cycle_nodes) if cycle_nodes is not None else ()


def calculate_in_degrees[T: Hashable](graph: Mapping[T, Iterable[T]]) -> dict[T, int]:
    """Вычисляет полустепень захода (in-degree) для всех вершин графа.

    :param graph: Словарь смежности {исходная_вершина: [целевые_вершины]}.
    :return: Словарь со счетчиком входящих ребер для каждой вершины.
    """
    in_degrees: dict[T, int] = {node: 0 for node in graph}

    for neighbors in graph.values():
        for neighbor in neighbors:
            if neighbor not in in_degrees:
                in_degrees[neighbor] = 0
            in_degrees[neighbor] += 1

    return in_degrees


def topological_sort[T: Hashable](graph: Mapping[T, Iterable[T]]) -> list[T]:
    """Выполняет топологическую сортировку вершин графа с использованием алгоритма Кана.

    Граф задается в виде словаря смежности, где ребро `u -> v` означает,
    что вершина `u` должна предшествовать вершине `v` (или `v` зависит от `u`).

    :param graph: Словарь смежности графа.
    :return: Список вершин в топологическом порядке.
    :raises CyclicDependencyError: Если граф содержит хотя бы один направленный цикл.
    """
    if not graph:
        return []

    in_degrees: dict[T, int] = calculate_in_degrees(graph)
    queue: deque[T] = deque([node for node, degree in in_degrees.items() if degree == 0])
    result: list[T] = []

    # Обрабатываем вершины без входящих зависимостей
    while queue:
        current: T = queue.popleft()
        result.append(current)

        for neighbor in graph.get(current, ()):
            in_degrees[neighbor] -= 1
            if in_degrees[neighbor] == 0:
                queue.append(neighbor)

    # Проверка на наличие оставшихся зависимостей (наличие цикла)
    if len(result) < len(in_degrees):
        unresolved: list[T] = [node for node, degree in in_degrees.items() if degree > 0]
        raise CyclicDependencyError(
            f"Граф содержит цикл. Неразрешенные вершины: {unresolved}",
            cycle_nodes=unresolved,
        )

    return result


def topological_sort_dfs[T: Hashable](graph: Mapping[T, Iterable[T]]) -> list[T]:
    """Выполняет топологическую сортировку графа с помощью поиска в глубину (DFS).

    Использует цветовую раскраску (0 - белый/непосещен, 1 - серый/в процессе, 2 - черный/завершен)
    для надежного обнаружения циклов.

    :param graph: Словарь смежности графа.
    :return: Список вершин в топологическом порядке.
    :raises CyclicDependencyError: Если граф содержит направленный цикл.
    """
    if not graph:
        return []

    # Собираем множество всех существующих вершин (включая листовые)
    all_nodes: set[T] = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)

    # 0 = unvisited, 1 = visiting, 2 = visited
    state: dict[T, int] = {node: 0 for node in all_nodes}
    order: list[T] = []
    cycle_path: list[T] = []

    def dfs(node: T) -> None:
        state[node] = 1  # visiting
        cycle_path.append(node)

        for neighbor in graph.get(node, ()):
            if state[neighbor] == 1:
                # Обнаружен цикл
                cycle_start_idx = cycle_path.index(neighbor)
                cycle_slice = cycle_path[cycle_start_idx:] + [neighbor]
                raise CyclicDependencyError(
                    f"Обнаружен цикл в графе: {' -> '.join(str(n) for n in cycle_slice)}",
                    cycle_nodes=cycle_slice,
                )
            if state[neighbor] == 0:
                dfs(neighbor)

        cycle_path.pop()
        state[node] = 2  # visited
        order.append(node)

    for node in all_nodes:
        if state[node] == 0:
            dfs(node)

    order.reverse()
    return order


def is_dag[T: Hashable](graph: Mapping[T, Iterable[T]]) -> bool:
    """Проверяет, является ли направленный граф ациклическим (DAG).

    :param graph: Словарь смежности графа.
    :return: True, если в графе отсутствуют циклы, иначе False.
    """
    try:
        topological_sort(graph)
        return True
    except CyclicDependencyError:
        return False
