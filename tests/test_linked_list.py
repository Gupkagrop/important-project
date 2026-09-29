"""Модульные тесты для односвязного списка LinkedList и узла Node."""

import pytest

from pocket_toolkit.structures.linked_list import LinkedList, Node


def test_node_creation_and_repr() -> None:
    """Проверка создания узла и его строкового представления."""
    node: Node[int] = Node(10)
    assert node.value == 10
    assert node.next is None
    assert repr(node) == "Node(value=10)"

    child_node: Node[int] = Node(20, node)
    assert child_node.value == 20
    assert child_node.next is node


def test_linked_list_init_empty() -> None:
    """Проверка инициализации пустого списка."""
    lst: LinkedList[int] = LinkedList()
    assert len(lst) == 0
    assert lst.is_empty() is True
    assert lst.to_list() == []


def test_linked_list_init_with_iterable() -> None:
    """Проверка инициализации элементами из итерируемого объекта."""
    lst: LinkedList[str] = LinkedList(["apple", "banana", "cherry"])
    assert len(lst) == 3
    assert lst.is_empty() is False
    assert lst.to_list() == ["apple", "banana", "cherry"]
    assert lst.peek_head() == "apple"
    assert lst.peek_tail() == "cherry"


def test_linked_list_append() -> None:
    """Проверка добавления элементов в конец списка."""
    lst: LinkedList[int] = LinkedList()
    lst.append(1)
    assert len(lst) == 1
    assert lst.peek_head() == 1
    assert lst.peek_tail() == 1

    lst.append(2)
    assert len(lst) == 2
    assert lst.peek_head() == 1
    assert lst.peek_tail() == 2
    assert lst.to_list() == [1, 2]


def test_linked_list_prepend() -> None:
    """Проверка добавления элементов в начало списка."""
    lst: LinkedList[int] = LinkedList()
    lst.prepend(10)
    assert len(lst) == 1
    assert lst.peek_head() == 10
    assert lst.peek_tail() == 10

    lst.prepend(20)
    assert len(lst) == 2
    assert lst.peek_head() == 20
    assert lst.peek_tail() == 10
    assert lst.to_list() == [20, 10]


def test_linked_list_peek_empty_raises() -> None:
    """Проверка исключений при вызове peek_head и peek_tail для пустого списка."""
    lst: LinkedList[float] = LinkedList()
    with pytest.raises(IndexError, match="Список пуст"):
        lst.peek_head()

    with pytest.raises(IndexError, match="Список пуст"):
        lst.peek_tail()


def test_linked_list_popleft() -> None:
    """Проверка удаления элементов из начала списка."""
    lst: LinkedList[int] = LinkedList([10, 20, 30])
    assert lst.popleft() == 10
    assert len(lst) == 2
    assert lst.peek_head() == 20

    assert lst.popleft() == 20
    assert lst.popleft() == 30
    assert len(lst) == 0
    assert lst.is_empty() is True

    with pytest.raises(IndexError, match="список пуст"):
        lst.popleft()


def test_linked_list_pop() -> None:
    """Проверка удаления элементов с конца списка."""
    lst: LinkedList[str] = LinkedList(["first", "second", "third"])
    assert lst.pop() == "third"
    assert len(lst) == 2
    assert lst.peek_tail() == "second"

    assert lst.pop() == "second"
    assert len(lst) == 1
    assert lst.peek_head() == "first"
    assert lst.peek_tail() == "first"

    assert lst.pop() == "first"
    assert len(lst) == 0
    assert lst.is_empty() is True

    with pytest.raises(IndexError, match="список пуст"):
        lst.pop()


def test_linked_list_remove_head() -> None:
    """Проверка удаления первого элемента списка через remove."""
    lst: LinkedList[int] = LinkedList([1, 2, 3])
    assert lst.remove(1) is True
    assert lst.to_list() == [2, 3]
    assert lst.peek_head() == 2
    assert len(lst) == 2


def test_linked_list_remove_middle() -> None:
    """Проверка удаления промежуточного элемента списка через remove."""
    lst: LinkedList[int] = LinkedList([1, 2, 3])
    assert lst.remove(2) is True
    assert lst.to_list() == [1, 3]
    assert len(lst) == 2
    assert lst.peek_head() == 1
    assert lst.peek_tail() == 3


def test_linked_list_remove_tail() -> None:
    """Проверка удаления последнего элемента списка через remove."""
    lst: LinkedList[int] = LinkedList([1, 2, 3])
    assert lst.remove(3) is True
    assert lst.to_list() == [1, 2]
    assert lst.peek_tail() == 2
    assert len(lst) == 2


def test_linked_list_remove_single_item() -> None:
    """Проверка удаления единственного элемента в списке."""
    lst: LinkedList[int] = LinkedList([99])
    assert lst.remove(99) is True
    assert len(lst) == 0
    assert lst.is_empty() is True
    assert lst.to_list() == []


def test_linked_list_remove_missing_and_empty() -> None:
    """Проверка попытки удаления несуществующего элемента."""
    empty_lst: LinkedList[int] = LinkedList()
    assert empty_lst.remove(42) is False

    lst: LinkedList[int] = LinkedList([1, 2, 3])
    assert lst.remove(999) is False
    assert len(lst) == 3


def test_linked_list_clear() -> None:
    """Проверка очистки связного списка."""
    lst: LinkedList[int] = LinkedList([1, 2, 3, 4])
    lst.clear()
    assert len(lst) == 0
    assert lst.is_empty() is True
    assert lst.to_list() == []


def test_linked_list_contains() -> None:
    """Проверка оператора принадлежности `in`."""
    lst: LinkedList[str] = LinkedList(["alpha", "beta", "gamma"])
    assert "alpha" in lst
    assert "beta" in lst
    assert "delta" not in lst


def test_linked_list_iteration() -> None:
    """Проверка прямого обхода списка."""
    raw_data: list[int] = [10, 20, 30, 40]
    lst: LinkedList[int] = LinkedList(raw_data)
    collected: list[int] = [item for item in lst]
    assert collected == raw_data


def test_linked_list_getitem() -> None:
    """Проверка доступа по положительному и отрицательному индексу."""
    lst: LinkedList[str] = LinkedList(["a", "b", "c", "d"])
    assert lst[0] == "a"
    assert lst[1] == "b"
    assert lst[3] == "d"
    assert lst[-1] == "d"
    assert lst[-4] == "a"

    with pytest.raises(IndexError, match="Индекс выходит за границы"):
        _ = lst[4]

    with pytest.raises(IndexError, match="Индекс выходит за границы"):
        _ = lst[-5]


def test_linked_list_repr() -> None:
    """Проверка строкового представления списка."""
    empty_lst: LinkedList[int] = LinkedList()
    assert repr(empty_lst) == "LinkedList([])"

    populated_lst: LinkedList[int] = LinkedList([1, 2, 3])
    assert repr(populated_lst) == "LinkedList([1, 2, 3])"
