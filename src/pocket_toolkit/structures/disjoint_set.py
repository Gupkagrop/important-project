"""Реализация структуры непересекающихся множеств (Disjoint Set / Union-Find).

Поддерживает эвристики сжатия путей (path compression) и объединения по рангу
(union by rank), обеспечивая практически константное амортизированное время
выполнения операций O(α(n)), где α — обратная функция Аккермана.
"""

from collections.abc import Iterable, Iterator


class DisjointSet[T]:
    """Структура данных непересекающихся множеств (Disjoint-Set / Union-Find).

    Позволяет эффективно объединять множества и определять, принадлежат ли
    элементы одному и тому же подмножеству (компоненте связности).

    Особенности реализации:
    - Эвристика сжатия путей (Path Compression) при операции find;
    - Эвристика объединения по рангу (Union by Rank) при операции union;
    - Отслеживание размера каждого подмножества и общего числа компонент связности;
    - Итеративный алгоритм find, исключающий переполнение стека вызовов;
    - Поддержка произвольных хэшируемых типов элементов.
    """

    def __init__(
        self,
        elements: Iterable[T] | None = None,
        pairs: Iterable[tuple[T, T]] | None = None,
    ) -> None:
        """Инициализирует структуру непересекающихся множеств.

        :param elements: Опциональная коллекция начальных элементов (создаются как синглтоны).
        :param pairs: Опциональная последовательность пар элементов для начального объединения.
        """
        self._parent: dict[T, T] = {}
        self._rank: dict[T, int] = {}
        self._size: dict[T, int] = {}
        self._num_sets: int = 0

        if elements is not None:
            for item in elements:
                self.make_set(item)

        if pairs is not None:
            for first, second in pairs:
                self.union(first, second, create_missing=True)

    @property
    def num_sets(self) -> int:
        """Возвращает текущее количество непересекающихся множеств (компонент)."""
        return self._num_sets

    @property
    def num_elements(self) -> int:
        """Возвращает общее количество зарегистрированных элементов."""
        return len(self._parent)

    def make_set(self, item: T) -> bool:
        """Создает новое изолированное множество, содержащее единственный элемент item.

        Если элемент уже присутствует в структуре, операция игнорируется.

        :param item: Элемент для добавления.
        :return: True, если элемент был успешно добавлен как новое множество;
                 False, если элемент уже присутствовал.
        """
        if item in self._parent:
            return False

        self._parent[item] = item
        self._rank[item] = 0
        self._size[item] = 1
        self._num_sets += 1
        return True

    def add(self, item: T) -> bool:
        """Алиас для метода make_set."""
        return self.make_set(item)

    def update(self, items: Iterable[T]) -> None:
        """Добавляет множество элементов в качестве изолированных синглтон-множеств.

        :param items: Коллекция элементов для добавления.
        """
        for item in items:
            self.make_set(item)

    def find(self, item: T) -> T:
        """Находит канонического представителя (корень) множества, содержащего элемент.

        Применяет двухпроходное сжатие путей (path compression), перенаправляя
        все узлы на пути обхода непосредственно на корень.

        :param item: Элемент, для которого определяется представитель множества.
        :return: Канонический представитель (корень) множества.
        :raises KeyError: Если элемент не был зарегистрирован в структуре.
        """
        if item not in self._parent:
            raise KeyError(
                f"Элемент {item!r} не зарегистрирован в структуре DisjointSet."
            )

        # Первый проход: нахождение корня дерева
        root: T = item
        while root != self._parent[root]:
            root = self._parent[root]

        # Второй проход: сжатие пути (path compression)
        curr: T = item
        while curr != root:
            next_node: T = self._parent[curr]
            self._parent[curr] = root
            curr = next_node

        return root

    def union(self, x: T, y: T, *, create_missing: bool = False) -> bool:
        """Объединяет множества, содержащие элементы x и y, используя эвристику рангов.

        :param x: Первый элемент.
        :param y: Второй элемент.
        :param create_missing: Если True, отсутствующие элементы автоматически
                               добавляются перед объединением. Если False,
                               будет выброшено исключение KeyError при их отсутствии.
        :return: True, если множества были успешно объединены;
                 False, если x и y уже принадлежали одному множеству.
        :raises KeyError: Если create_missing=False и хотя бы один элемент отсутствует.
        """
        if create_missing:
            self.make_set(x)
            self.make_set(y)

        root_x: T = self.find(x)
        root_y: T = self.find(y)

        if root_x == root_y:
            return False

        self._link_roots(root_x, root_y)
        self._num_sets -= 1
        return True

    def _link_roots(self, root_x: T, root_y: T) -> None:
        """Связывает два корня в соответствии с эвристикой объединения по рангу.

        Корень с меньшим рангом подвязывается к корню с большим рангом.
        При равенстве рангов один становится родителем, а его ранг увеличивается на 1.
        Размеры компонент суммируются у нового общего корня.

        :param root_x: Первый корень дерева.
        :param root_y: Второй корень дерева.
        """
        rank_x: int = self._rank[root_x]
        rank_y: int = self._rank[root_y]

        if rank_x < rank_y:
            self._parent[root_x] = root_y
            self._size[root_y] += self._size[root_x]
            return

        if rank_x > rank_y:
            self._parent[root_y] = root_x
            self._size[root_x] += self._size[root_y]
            return

        # Ранги равны: выбираем root_x родителем и увеличиваем его ранг
        self._parent[root_y] = root_x
        self._rank[root_x] += 1
        self._size[root_x] += self._size[root_y]

    def connected(self, x: T, y: T) -> bool:
        """Проверяет, принадлежат ли элементы x и y одному множеству (компоненте).

        :param x: Первый элемент.
        :param y: Второй элемент.
        :return: True, если элементы находятся в одном множестве; иначе False.
        :raises KeyError: Если хотя бы один из элементов не зарегистрирован.
        """
        return self.find(x) == self.find(y)

    def is_connected(self, x: T, y: T) -> bool:
        """Алиас для метода connected."""
        return self.connected(x, y)

    def set_size(self, item: T) -> int:
        """Возвращает количество элементов в множестве, содержащем указанный элемент.

        :param item: Элемент множества.
        :return: Размер компоненты связности.
        :raises KeyError: Если элемент не зарегистрирован.
        """
        root: T = self.find(item)
        return self._size[root]

    def get_set_size(self, item: T) -> int:
        """Алиас для метода set_size."""
        return self.set_size(item)

    def get_rank(self, item: T) -> int:
        """Возвращает ранг канонического корня множества, содержащего указанный элемент.

        :param item: Элемент множества.
        :return: Ранг корня дерева.
        :raises KeyError: Если элемент не зарегистрирован.
        """
        root: T = self.find(item)
        return self._rank[root]

    def get_set(self, item: T) -> set[T]:
        """Возвращает множество всех элементов, находящихся в одной компоненте с item.

        :param item: Элемент для выборки компонентов.
        :return: Множество элементов того же подмножества.
        :raises KeyError: Если элемент не зарегистрирован.
        """
        root: T = self.find(item)
        return {element for element in self._parent if self.find(element) == root}

    def subsets_dict(self) -> dict[T, set[T]]:
        """Группирует все элементы по их каноническим представителям (корням).

        :return: Словарь, сопоставляющий корень множества со всеми его элементами.
        """
        groups: dict[T, set[T]] = {}
        for element in self._parent:
            root: T = self.find(element)
            if root not in groups:
                groups[root] = set()
            groups[root].add(element)
        return groups

    def subsets(self) -> list[set[T]]:
        """Возвращает список всех непересекающихся подмножеств.

        :return: Список множеств элементов для каждой компоненты связности.
        """
        return list(self.subsets_dict().values())

    def roots(self) -> set[T]:
        """Возвращает множество всех канонических представителей (корней).

        :return: Множество корней активных подмножеств.
        """
        return {self.find(element) for element in self._parent}

    def clear(self) -> None:
        """Полностью очищает структуру непересекающихся множеств."""
        self._parent.clear()
        self._rank.clear()
        self._size.clear()
        self._num_sets = 0

    def copy(self) -> "DisjointSet[T]":
        """Создает независимую копию структуры непересекающихся множеств.

        :return: Новый экземпляр DisjointSet с аналогичным состоянием.
        """
        cloned: DisjointSet[T] = DisjointSet()
        cloned._parent = self._parent.copy()
        cloned._rank = self._rank.copy()
        cloned._size = self._size.copy()
        cloned._num_sets = self._num_sets
        return cloned

    def _canonical_partition(self) -> set[frozenset[T]]:
        """Возвращает каноническое представление разбиения для проверки эквивалентности.

        :return: Множество неизменяемых подмножеств (frozenset).
        """
        return {frozenset(subset) for subset in self.subsets()}

    def __len__(self) -> int:
        """Возвращает общее количество зарегистрированных элементов."""
        return len(self._parent)

    def __contains__(self, item: object) -> bool:
        """Проверяет наличие элемента в структуре."""
        return item in self._parent

    def __iter__(self) -> Iterator[T]:
        """Возвращает итератор по всем элементам структуры."""
        return iter(self._parent)

    def __bool__(self) -> bool:
        """Возвращает True, если структура содержит хотя бы один элемент."""
        return len(self._parent) > 0

    def __repr__(self) -> str:
        """Возвращает строковое представление структуры."""
        return f"DisjointSet(elements={self.num_elements}, sets={self.num_sets})"

    def __eq__(self, other: object) -> bool:
        """Сравнивает две структуры непересекающихся множеств на эквивалентность разбиения.

        Две структуры считаются равными, если они содержат один и тот же набор
        элементов и разбивают их на одинаковые подмножества (классы эквивалентности).
        """
        if not isinstance(other, DisjointSet):
            return False
        if len(self) != len(other) or self.num_sets != other.num_sets:
            return False
        if set(self._parent.keys()) != set(other._parent.keys()):
            return False
        return self._canonical_partition() == other._canonical_partition()
