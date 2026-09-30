"""Модульные тесты для двусвязного списка DoublyLinkedList и узла DoublyNode."""

import pytest

from pocket_toolkit.structures.doubly_linked_list import DoublyLinkedList, DoublyNode


def test_doubly_node_creation_and_repr() -> None:
    """Проверка создания двусвязного узла и его строкового представления."""
    node1: DoublyNode[int] = DoublyNode(10)
    assert node1.value == 10
    assert node1.prev is None
    assert node1.next is None
    assert repr(node1) == "DoublyNode(value=10)"

    node2: DoublyNode[int] = DoublyNode(20, prev_node=node1)
    node1.next = node2
    assert node2.value == 20
    assert node2.prev is node1
    assert node1.next is node2


def test_doubly_linked_list_init_empty() -> None:
    """Проверка инициализации пустого двусвязного списка."""
    lst: DoublyLinkedList[int] = DoublyLinkedList()
    assert len(lst) == 0
    assert lst.is_empty() is True
    assert lst.head_node is None
    assert lst.tail_node is None
    assert lst.to_list() == []
    assert lst.to_reverse_list() == []


def test_doubly_linked_list_init_with_iterable() -> None:
    """Проверка инициализации элементами из итерируемого объекта."""
    lst: DoublyLinkedList[str] = DoublyLinkedList(["alpha", "beta", "gamma"])
    assert len(lst) == 3
    assert lst.is_empty() is False
    assert lst.to_list() == ["alpha", "beta", "gamma"]
    assert lst.to_reverse_list() == ["gamma", "beta", "alpha"]
    assert lst.peek_head() == "alpha"
    assert lst.peek_tail() == "gamma"


def test_doubly_linked_list_append_and_prepend() -> None:
    """Проверка добавления элементов в начало и конец двусвязного списка."""
    lst: DoublyLinkedList[int] = DoublyLinkedList()

    node1: DoublyNode[int] = lst.append(2)
    assert len(lst) == 1
    assert lst.head_node is node1
    assert lst.tail_node is node1

    node2: DoublyNode[int] = lst.prepend(1)
    assert len(lst) == 2
    assert lst.head_node is node2
    assert lst.tail_node is node1
    assert node2.next is node1
    assert node1.prev is node2

    node3: DoublyNode[int] = lst.append(3)
    assert len(lst) == 3
    assert lst.tail_node is node3
    assert node1.next is node3
    assert node3.prev is node1
    assert lst.to_list() == [1, 2, 3]


def test_doubly_linked_list_append_node_and_prepend_node() -> None:
    """Проверка ручного присоединения узлов через append_node и prepend_node."""
    lst: DoublyLinkedList[str] = DoublyLinkedList()
    first_node: DoublyNode[str] = DoublyNode("center")
    lst.append_node(first_node)

    left_node: DoublyNode[str] = DoublyNode("left")
    lst.prepend_node(left_node)

    right_node: DoublyNode[str] = DoublyNode("right")
    lst.append_node(right_node)

    assert lst.to_list() == ["left", "center", "right"]
    assert lst.head_node is left_node
    assert lst.tail_node is right_node


def test_doubly_linked_list_peek_empty_raises() -> None:
    """Проверка исключений при чтении пустого списка."""
    lst: DoublyLinkedList[float] = DoublyLinkedList()
    with pytest.raises(IndexError, match="Список пуст"):
        lst.peek_head()

    with pytest.raises(IndexError, match="Список пуст"):
        lst.peek_tail()


def test_doubly_linked_list_popleft() -> None:
    """Проверка удаления элементов из начала списка."""
    lst: DoublyLinkedList[int] = DoublyLinkedList([100, 200, 300])

    assert lst.popleft() == 100
    assert len(lst) == 2
    assert lst.peek_head() == 200
    assert lst.head_node is not None and lst.head_node.prev is None

    assert lst.popleft() == 200
    assert lst.popleft() == 300
    assert len(lst) == 0
    assert lst.is_empty() is True
    assert lst.head_node is None
    assert lst.tail_node is None

    with pytest.raises(IndexError, match="список пуст"):
        lst.popleft()


def test_doubly_linked_list_pop() -> None:
    """Проверка удаления элементов с конца списка."""
    lst: DoublyLinkedList[int] = DoublyLinkedList([10, 20, 30])

    assert lst.pop() == 30
    assert len(lst) == 2
    assert lst.peek_tail() == 20
    assert lst.tail_node is not None and lst.tail_node.next is None

    assert lst.pop() == 20
    assert lst.pop() == 10
    assert len(lst) == 0
    assert lst.is_empty() is True
    assert lst.head_node is None
    assert lst.tail_node is None

    with pytest.raises(IndexError, match="список пуст"):
        lst.pop()


def test_doubly_linked_list_unlink_node_cases() -> None:
    """Проверка отсоединения узлов за O(1) в различных позициях списка."""
    lst: DoublyLinkedList[str] = DoublyLinkedList(["A", "B", "C", "D"])
    nodes: list[DoublyNode[str]] = list(lst.iter_nodes())
    node_a, node_b, node_c, node_d = nodes

    # Удаление промежуточного узла B
    val_b: str = lst.unlink(node_b)
    assert val_b == "B"
    assert len(lst) == 3
    assert lst.to_list() == ["A", "C", "D"]
    assert node_a.next is node_c
    assert node_c.prev is node_a

    # Удаление головы через unlink
    val_a: str = lst.unlink(node_a)
    assert val_a == "A"
    assert lst.to_list() == ["C", "D"]
    assert lst.head_node is node_c

    # Удаление хвоста через unlink
    val_d: str = lst.unlink(node_d)
    assert val_d == "D"
    assert lst.to_list() == ["C"]
    assert lst.tail_node is node_c

    # Удаление единственного оставшегося узла
    val_c: str = lst.unlink(node_c)
    assert val_c == "C"
    assert len(lst) == 0
    assert lst.is_empty() is True

    # Попытка вызвать unlink на пустом списке
    with pytest.raises(ValueError, match="список пуст"):
        lst.unlink(node_a)


def test_doubly_linked_list_unlink_invalid_node_raises() -> None:
    """Проверка исключения при попытке unlink чужого или поврежденного узла."""
    lst: DoublyLinkedList[int] = DoublyLinkedList([1, 2, 3])
    foreign_node: DoublyNode[int] = DoublyNode(999)

    with pytest.raises(ValueError, match="не принадлежит текущему списку"):
        lst.unlink(foreign_node)


def test_doubly_linked_list_move_to_end_and_front() -> None:
    """Проверка перемещения узлов в начало и в конец за O(1)."""
    lst: DoublyLinkedList[int] = DoublyLinkedList([1, 2, 3, 4])
    nodes: list[DoublyNode[int]] = list(lst.iter_nodes())
    _node_1, node_2, _node_3, node_4 = nodes

    # Перемещение 2 в конец -> [1, 3, 4, 2]
    lst.move_to_end(node_2)
    assert lst.to_list() == [1, 3, 4, 2]
    assert lst.tail_node is node_2

    # Перемещение уже последнего узла в конец -> ничего не меняется
    lst.move_to_end(node_2)
    assert lst.to_list() == [1, 3, 4, 2]

    # Перемещение 4 в начало -> [4, 1, 3, 2]
    lst.move_to_front(node_4)
    assert lst.to_list() == [4, 1, 3, 2]
    assert lst.head_node is node_4

    # Перемещение уже первого узла в начало -> ничего не меняется
    lst.move_to_front(node_4)
    assert lst.to_list() == [4, 1, 3, 2]


def test_doubly_linked_list_remove() -> None:
    """Проверка удаления элемента по значению."""
    lst: DoublyLinkedList[int] = DoublyLinkedList([10, 20, 30, 40])

    # Удаление промежуточного элемента
    assert lst.remove(20) is True
    assert lst.to_list() == [10, 30, 40]

    # Удаление головы
    assert lst.remove(10) is True
    assert lst.to_list() == [30, 40]

    # Удаление хвоста
    assert lst.remove(40) is True
    assert lst.to_list() == [30]

    # Удаление отсутствующего элемента
    assert lst.remove(999) is False
    assert lst.to_list() == [30]

    # Удаление последнего элемента
    assert lst.remove(30) is True
    assert len(lst) == 0

    # Удаление из пустого списка
    assert lst.remove(30) is False


def test_doubly_linked_list_clear() -> None:
    """Проверка полной очистки двусвязного списка."""
    lst: DoublyLinkedList[int] = DoublyLinkedList([1, 2, 3])
    lst.clear()
    assert len(lst) == 0
    assert lst.is_empty() is True
    assert lst.head_node is None
    assert lst.tail_node is None
    assert lst.to_list() == []


def test_doubly_linked_list_bidirectional_iteration() -> None:
    """Проверка прямой и обратной итерации."""
    items: list[str] = ["x", "y", "z"]
    lst: DoublyLinkedList[str] = DoublyLinkedList(items)

    assert list(lst) == ["x", "y", "z"]
    assert list(reversed(lst)) == ["z", "y", "x"]

    forward_nodes: list[str] = [n.value for n in lst.iter_nodes()]
    assert forward_nodes == ["x", "y", "z"]

    reverse_nodes: list[str] = [n.value for n in lst.iter_nodes_reversed()]
    assert reverse_nodes == ["z", "y", "x"]


def test_doubly_linked_list_contains() -> None:
    """Проверка работы оператора `in`."""
    lst: DoublyLinkedList[str] = DoublyLinkedList(["cat", "dog", "fox"])
    assert "cat" in lst
    assert "dog" in lst
    assert "fox" in lst
    assert "wolf" not in lst


def test_doubly_linked_list_getitem() -> None:
    """Проверка оптимизированного доступа по индексу (от головы и от хвоста)."""
    lst: DoublyLinkedList[str] = DoublyLinkedList(["0", "1", "2", "3", "4"])

    # Доступ через обход от головы (индексы < 5 // 2, то есть 0, 1)
    assert lst[0] == "0"
    assert lst[1] == "1"

    # Доступ через обход от хвоста (индексы >= 2, то есть 2, 3, 4)
    assert lst[2] == "2"
    assert lst[3] == "3"
    assert lst[4] == "4"

    # Отрицательные индексы
    assert lst[-1] == "4"
    assert lst[-2] == "3"
    assert lst[-5] == "0"

    with pytest.raises(IndexError, match="Индекс выходит за границы"):
        _ = lst[5]

    with pytest.raises(IndexError, match="Индекс выходит за границы"):
        _ = lst[-6]


def test_doubly_linked_list_repr() -> None:
    """Проверка строкового представления списка."""
    empty_lst: DoublyLinkedList[int] = DoublyLinkedList()
    assert repr(empty_lst) == "DoublyLinkedList([])"

    lst: DoublyLinkedList[int] = DoublyLinkedList([10, 20])
    assert repr(lst) == "DoublyLinkedList([10, 20])"
