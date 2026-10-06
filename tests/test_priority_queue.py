"""Модульные тесты для очереди с приоритетами PriorityQueue."""

import pytest

from pocket_toolkit.structures.priority_queue import (
    Comparable,
    PriorityItem,
    PriorityQueue,
)


def test_priority_queue_empty_state() -> None:
    """Проверка начального состояния пустой очереди по умолчанию (min-heap)."""
    pq: PriorityQueue[int] = PriorityQueue()
    assert len(pq) == 0
    assert pq.is_empty() is True
    assert bool(pq) is False
    assert pq.is_min_heap is True
    assert pq.is_max_heap is False
    assert pq.to_list() == []
    assert pq.to_priority_list() == []
    assert repr(pq) == "PriorityQueue(size=0, mode='min')"


def test_priority_queue_empty_operations_raise() -> None:
    """Проверка возбуждения IndexError при вызове операций на пустой очереди."""
    pq: PriorityQueue[str] = PriorityQueue()

    with pytest.raises(IndexError, match="пуста"):
        pq.pop()

    with pytest.raises(IndexError, match="пуста"):
        pq.pop_with_priority()

    with pytest.raises(IndexError, match="пуста"):
        pq.pop_item()

    with pytest.raises(IndexError, match="пуста"):
        pq.peek()

    with pytest.raises(IndexError, match="пуста"):
        pq.peek_with_priority()

    with pytest.raises(IndexError, match="пуста"):
        pq.peek_item()

    with pytest.raises(IndexError, match="пуста"):
        pq.replace("fallback")


def test_min_heap_natural_ordering() -> None:
    """Проверка извлечения элементов в порядке возрастания в min-heap."""
    pq: PriorityQueue[int] = PriorityQueue()
    items: list[int] = [5, 3, 9, 1, 7, 2, 8]
    for item in items:
        pq.push(item)

    assert len(pq) == 7
    assert pq.peek() == 1
    assert pq.is_empty() is False

    extracted: list[int] = [pq.pop() for _ in range(len(items))]
    assert extracted == [1, 2, 3, 5, 7, 8, 9]
    assert pq.is_empty() is True


def test_max_heap_natural_ordering() -> None:
    """Проверка извлечения элементов в порядке убывания в max-heap."""
    pq: PriorityQueue[int] = PriorityQueue(max_heap=True)
    assert pq.is_max_heap is True
    assert pq.is_min_heap is False
    assert repr(pq) == "PriorityQueue(size=0, mode='max')"

    items: list[int] = [5, 3, 9, 1, 7, 2, 8]
    for item in items:
        pq.push(item)

    assert pq.peek() == 9
    extracted: list[int] = [pq.pop() for _ in range(len(items))]
    assert extracted == [9, 8, 7, 5, 3, 2, 1]


def test_explicit_priority_and_pop_with_priority() -> None:
    """Проверка работы с явно заданными приоритетами и методами pop_with_priority/pop_item."""
    pq: PriorityQueue[str] = PriorityQueue()
    pq.push("task_c", priority=30)
    pq.push("task_a", priority=10)
    pq.push("task_b", priority=20)

    assert pq.peek() == "task_a"
    assert pq.peek_with_priority() == ("task_a", 10)
    assert pq.peek_item() == PriorityItem("task_a", 10)

    item, priority = pq.pop_with_priority()
    assert item == "task_a"
    assert priority == 10

    priority_item: PriorityItem[str] = pq.pop_item()
    assert priority_item.item == "task_b"
    assert priority_item.priority == 20

    assert pq.pop() == "task_c"


def test_fifo_stability_for_equal_priorities_min_heap() -> None:
    """Проверка сохранения порядка добавления (FIFO) при совпадении приоритетов в min-heap."""
    pq: PriorityQueue[str] = PriorityQueue()
    pq.push("alpha", priority=2)
    pq.push("first_high", priority=1)
    pq.push("beta", priority=2)
    pq.push("second_high", priority=1)
    pq.push("gamma", priority=2)

    assert pq.pop() == "first_high"
    assert pq.pop() == "second_high"
    assert pq.pop() == "alpha"
    assert pq.pop() == "beta"
    assert pq.pop() == "gamma"


def test_fifo_stability_for_equal_priorities_max_heap() -> None:
    """Проверка сохранения порядка добавления (FIFO) при совпадении приоритетов в max-heap."""
    pq: PriorityQueue[str] = PriorityQueue(max_heap=True)
    pq.push("doc_1", priority=100)
    pq.push("doc_2", priority=200)
    pq.push("doc_3", priority=200)
    pq.push("doc_4", priority=100)

    assert pq.pop() == "doc_2"
    assert pq.pop() == "doc_3"
    assert pq.pop() == "doc_1"
    assert pq.pop() == "doc_4"


def test_custom_key_function() -> None:
    """Проверка работы очереди с пользовательской функцией key."""
    words: list[str] = ["banana", "pie", "apple", "fig", "elderberry"]
    min_pq: PriorityQueue[str] = PriorityQueue(words, key=len)
    assert min_pq.pop() == "pie"
    assert min_pq.pop() == "fig"
    assert min_pq.pop() == "apple"
    assert min_pq.pop() == "banana"
    assert min_pq.pop() == "elderberry"

    max_pq: PriorityQueue[str] = PriorityQueue(words, max_heap=True, key=len)
    assert max_pq.pop() == "elderberry"
    assert max_pq.pop() == "banana"
    assert max_pq.pop() == "apple"
    assert max_pq.pop() == "pie"
    assert max_pq.pop() == "fig"


def test_initial_items_heapify_min_and_max() -> None:
    """Проверка корректности начального заполнения кучи за O(n) через heapify."""
    numbers: list[int] = [14, 8, 22, 1, 9, 3, 17, 0, 5]
    min_pq: PriorityQueue[int] = PriorityQueue(numbers)
    assert min_pq.to_list() == sorted(numbers)

    max_pq: PriorityQueue[int] = PriorityQueue(numbers, max_heap=True)
    assert max_pq.to_list() == sorted(numbers, reverse=True)


def test_from_priorities_classmethod() -> None:
    """Проверка создания очереди через метод from_priorities."""
    pairs: list[tuple[str, int]] = [("medium", 2), ("low", 3), ("urgent", 1)]
    pq_min: PriorityQueue[str] = PriorityQueue.from_priorities(pairs)
    assert pq_min.pop() == "urgent"
    assert pq_min.pop() == "medium"
    assert pq_min.pop() == "low"

    pq_max: PriorityQueue[str] = PriorityQueue.from_priorities(pairs, max_heap=True)
    assert pq_max.pop() == "low"
    assert pq_max.pop() == "medium"
    assert pq_max.pop() == "urgent"


def test_pushpop_behavior() -> None:
    """Проверка метода pushpop в различных граничных условиях."""
    pq: PriorityQueue[int] = PriorityQueue()

    # На пустой очереди pushpop возвращает переданный элемент
    assert pq.pushpop(42) == 42
    assert pq.is_empty() is True

    pq.push(10)
    pq.push(20)

    # Добавляемый элемент приоритетнее корня min-heap (5 < 10)
    assert pq.pushpop(5) == 5
    assert len(pq) == 2
    assert pq.peek() == 10

    # Добавляемый элемент менее приоритетен (15 > 10)
    assert pq.pushpop(15) == 10
    assert len(pq) == 2
    assert pq.peek() == 15
    assert pq.pop() == 15
    assert pq.pop() == 20


def test_pushpop_max_heap() -> None:
    """Проверка метода pushpop для max-heap."""
    pq: PriorityQueue[int] = PriorityQueue(max_heap=True)
    pq.push(50)
    pq.push(30)

    # Новый элемент больше корня max-heap (60 > 50)
    assert pq.pushpop(60) == 60
    assert len(pq) == 2
    assert pq.peek() == 50

    # Новый элемент меньше корня (40 < 50)
    assert pq.pushpop(40) == 50
    assert len(pq) == 2
    assert pq.peek() == 40


def test_replace_behavior() -> None:
    """Проверка метода replace (извлечение корня с заменой)."""
    pq: PriorityQueue[int] = PriorityQueue([10, 20, 30])
    old_root: int = pq.replace(5)
    assert old_root == 10
    assert len(pq) == 3
    assert pq.peek() == 5

    old_root = pq.replace(100)
    assert old_root == 5
    assert len(pq) == 3
    assert pq.to_list() == [20, 30, 100]


def test_remove_element() -> None:
    """Проверка удаления элемента по значению из очереди."""
    pq: PriorityQueue[str] = PriorityQueue()
    pq.push("a", priority=1)
    pq.push("b", priority=2)
    pq.push("c", priority=3)
    pq.push("d", priority=4)

    # Удаление отсутствующего элемента
    assert pq.remove("unknown") is False
    assert len(pq) == 4

    # Удаление внутреннего элемента
    assert pq.remove("b") is True
    assert len(pq) == 3
    assert "b" not in pq
    assert pq.to_list() == ["a", "c", "d"]

    # Удаление корня
    assert pq.remove("a") is True
    assert pq.peek() == "c"

    # Удаление последнего оставшегося элемента
    assert pq.remove("c") is True
    assert pq.remove("d") is True
    assert pq.is_empty() is True
    assert pq.remove("d") is False


def test_update_priority() -> None:
    """Проверка динамического обновления приоритета элемента."""
    pq: PriorityQueue[str] = PriorityQueue()
    pq.push("job1", priority=10)
    pq.push("job2", priority=20)
    pq.push("job3", priority=30)

    assert pq.update_priority("nonexistent", 5) is False

    # Повышение приоритета в min-heap (sift up): 30 -> 1
    assert pq.update_priority("job3", 1) is True
    assert pq.peek() == "job3"
    assert pq.peek_with_priority() == ("job3", 1)

    # Понижение приоритета в min-heap (sift down): 1 -> 50
    assert pq.update_priority("job3", 50) is True
    assert pq.peek() == "job1"
    assert pq.to_list() == ["job1", "job2", "job3"]


def test_update_priority_max_heap() -> None:
    """Проверка динамического обновления приоритета в max-heap."""
    pq: PriorityQueue[str] = PriorityQueue(max_heap=True)
    pq.push("a", priority=10)
    pq.push("b", priority=20)
    pq.push("c", priority=30)

    # Повышение приоритета в max-heap: a (10 -> 40)
    assert pq.update_priority("a", 40) is True
    assert pq.peek() == "a"

    # Понижение приоритета в max-heap: a (40 -> 5)
    assert pq.update_priority("a", 5) is True
    assert pq.peek() == "c"


def test_to_list_and_to_priority_list_non_destructive() -> None:
    """Проверка неразрушающего экспорта отсортированных данных."""
    pq: PriorityQueue[str] = PriorityQueue()
    pq.push("low", priority=3)
    pq.push("high", priority=1)
    pq.push("medium", priority=2)

    assert pq.to_list() == ["high", "medium", "low"]
    assert pq.to_priority_list() == [("high", 1), ("medium", 2), ("low", 3)]
    assert len(pq) == 3
    assert pq.peek() == "high"


def test_drain_and_drain_with_priority() -> None:
    """Проверка генераторов опустошения очереди drain и drain_with_priority."""
    pq1: PriorityQueue[int] = PriorityQueue([30, 10, 20])
    drained_items: list[int] = list(pq1.drain())
    assert drained_items == [10, 20, 30]
    assert pq1.is_empty() is True

    pq2: PriorityQueue[str] = PriorityQueue.from_priorities([("x", 2), ("y", 1)])
    drained_pairs: list[tuple[str, Comparable]] = list(pq2.drain_with_priority())
    assert drained_pairs == [("y", 1), ("x", 2)]
    assert pq2.is_empty() is True


def test_clear_and_copy() -> None:
    """Проверка методов clear и copy."""
    original: PriorityQueue[int] = PriorityQueue([5, 1, 9], max_heap=True)
    cloned: PriorityQueue[int] = original.copy()

    assert cloned == original
    assert cloned.is_max_heap is True

    # Модификация копии не влияет на оригинал
    cloned.pop()
    assert len(cloned) == 2
    assert len(original) == 3

    original.clear()
    assert original.is_empty() is True
    assert len(original) == 0
    assert len(cloned) == 2


def test_contains_and_iteration() -> None:
    """Проверка оператора 'in' (__contains__) и итерации (__iter__)."""
    pq: PriorityQueue[str] = PriorityQueue(["apple", "banana", "cherry"])
    assert "banana" in pq
    assert "orange" not in pq

    items_in_iter: list[str] = list(pq)
    assert len(items_in_iter) == 3
    assert set(items_in_iter) == {"apple", "banana", "cherry"}
    assert len(pq) == 3


def test_equality() -> None:
    """Проверка оператора равенства __eq__."""
    pq1: PriorityQueue[int] = PriorityQueue([3, 1, 2])
    pq2: PriorityQueue[int] = PriorityQueue([1, 2, 3])
    pq_max: PriorityQueue[int] = PriorityQueue([1, 2, 3], max_heap=True)

    assert pq1 == pq2
    assert pq1 != pq_max
    assert pq1 != [1, 2, 3]  # Сравнение с другим типом


def test_incomparable_objects_with_explicit_priority() -> None:
    """Проверка хранения несравнимых объектов (например, словарей) с явным приоритетом."""
    pq: PriorityQueue[dict[str, str]] = PriorityQueue()
    d1: dict[str, str] = {"id": "1"}
    d2: dict[str, str] = {"id": "2"}
    d3: dict[str, str] = {"id": "3"}

    pq.push(d1, priority=10)
    pq.push(d2, priority=5)
    pq.push(d3, priority=5)  # Одинаковый приоритет -> FIFO

    assert pq.pop() == d2
    assert pq.pop() == d3
    assert pq.pop() == d1


def test_incomparable_objects_without_priority_raises() -> None:
    """Проверка возбуждения TypeError при сравнении несравнимых объектов без явного приоритета."""
    pq: PriorityQueue[dict[str, str]] = PriorityQueue()
    pq.push({"id": "first"})

    # При вставке второго элемента куча пытается сравнить элементы
    with pytest.raises(TypeError, match="not supported between instances"):
        pq.push({"id": "second"})


def test_priority_item_representation_and_equality() -> None:
    """Проверка поведения вспомогательного класса PriorityItem."""
    item1: PriorityItem[str] = PriorityItem("task", 1)
    item2: PriorityItem[str] = PriorityItem("task", 1)
    item3: PriorityItem[str] = PriorityItem("task", 2)

    assert repr(item1) == "PriorityItem(item='task', priority=1)"
    assert item1 == item2
    assert item1 != item3
    assert item1 != "task"
