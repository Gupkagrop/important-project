"""Модульные тесты для ограниченной двусторонней очереди BoundedDeque."""

import pytest

from pocket_toolkit.structures.bounded_deque import BoundedDeque


def test_bounded_deque_init_valid() -> None:
    """Проверка корректной инициализации очереди с допустимой вместимостью."""
    deque: BoundedDeque[int] = BoundedDeque(5)
    assert deque.capacity == 5
    assert deque.available_capacity == 5
    assert len(deque) == 0
    assert deque.is_empty() is True
    assert deque.is_full() is False
    assert bool(deque) is False
    assert deque.to_list() == []


def test_bounded_deque_init_invalid() -> None:
    """Проверка возбуждения ошибки при недопустимой вместимости."""
    with pytest.raises(ValueError, match="должна быть больше нуля"):
        BoundedDeque(0)

    with pytest.raises(ValueError, match="должна быть больше нуля"):
        BoundedDeque(-3)


def test_bounded_deque_init_with_iterable() -> None:
    """Проверка инициализации очереди начальной последовательностью элементов."""
    deque: BoundedDeque[int] = BoundedDeque(3, [1, 2])
    assert deque.to_list() == [1, 2]
    assert len(deque) == 2
    assert deque.available_capacity == 1

    # Инициализация с превышением вместимости (выталкивание старых)
    overflow_deque: BoundedDeque[int] = BoundedDeque(3, [10, 20, 30, 40, 50])
    assert overflow_deque.to_list() == [30, 40, 50]
    assert len(overflow_deque) == 3
    assert overflow_deque.is_full() is True


def test_bounded_deque_append_and_safe_eviction() -> None:
    """Проверка добавления в правый конец и безопасного возврата вытолкнутого элемента."""
    evicted_log: list[str] = []
    deque: BoundedDeque[str] = BoundedDeque(2, on_evict=lambda item: evicted_log.append(item))

    res1: str | None = deque.append("первый")
    assert res1 is None
    assert deque.to_list() == ["первый"]

    res2: str | None = deque.append("второй")
    assert res2 is None
    assert deque.to_list() == ["первый", "второй"]
    assert deque.is_full() is True

    # Переполнение: выталкивается самый левый элемент "первый"
    res3: str | None = deque.append("третий")
    assert res3 == "первый"
    assert deque.to_list() == ["второй", "третий"]
    assert evicted_log == ["первый"]

    res4: str | None = deque.append("четвертый")
    assert res4 == "второй"
    assert deque.to_list() == ["третий", "четвертый"]
    assert evicted_log == ["первый", "второй"]


def test_bounded_deque_appendleft_and_safe_eviction() -> None:
    """Проверка добавления в левый конец и безопасного возврата вытолкнутого элемента."""
    evicted_log: list[int] = []
    deque: BoundedDeque[int] = BoundedDeque(3, on_evict=lambda val: evicted_log.append(val))

    assert deque.appendleft(10) is None
    assert deque.appendleft(20) is None
    assert deque.appendleft(30) is None
    assert deque.to_list() == [30, 20, 10]
    assert deque.is_full() is True

    # Переполнение слева: выталкивается самый правый элемент (хвост) 10
    evicted: int | None = deque.appendleft(40)
    assert evicted == 10
    assert deque.to_list() == [40, 30, 20]
    assert evicted_log == [10]


def test_bounded_deque_try_append_and_try_appendleft() -> None:
    """Проверка безопасного условного добавления без выталкивания."""
    deque: BoundedDeque[int] = BoundedDeque(2)

    assert deque.try_append(1) is True
    assert deque.try_append(2) is True
    # Переполнение: элемент не добавляется, возвращается False
    assert deque.try_append(3) is False
    assert deque.to_list() == [1, 2]

    deque.clear()
    assert deque.try_appendleft(10) is True
    assert deque.try_appendleft(20) is True
    assert deque.try_appendleft(30) is False
    assert deque.to_list() == [20, 10]


def test_bounded_deque_pop_and_popleft() -> None:
    """Проверка извлечения элементов с обоих концов очереди."""
    deque: BoundedDeque[int] = BoundedDeque(3, [100, 200, 300])

    assert deque.pop() == 300
    assert deque.to_list() == [100, 200]
    assert len(deque) == 2

    assert deque.popleft() == 100
    assert deque.to_list() == [200]
    assert len(deque) == 1

    assert deque.pop() == 200
    assert deque.is_empty() is True

    with pytest.raises(IndexError, match="очередь пуста"):
        deque.pop()

    with pytest.raises(IndexError, match="очередь пуста"):
        deque.popleft()


def test_bounded_deque_peek_and_peekleft() -> None:
    """Проверка просмотра крайних элементов без их удаления."""
    deque: BoundedDeque[str] = BoundedDeque(3)

    with pytest.raises(IndexError, match="очередь пуста"):
        deque.peek()

    with pytest.raises(IndexError, match="очередь пуста"):
        deque.peekleft()

    deque.append("A")
    assert deque.peek() == "A"
    assert deque.peekleft() == "A"

    deque.append("B")
    assert deque.peek() == "B"
    assert deque.peekleft() == "A"


def test_bounded_deque_extend_and_extendleft() -> None:
    """Проверка массового добавления элементов с возвратом вытолкнутых значений."""
    deque: BoundedDeque[int] = BoundedDeque(3, [1, 2])

    evicted_right: list[int] = deque.extend([3, 4, 5])
    assert evicted_right == [1, 2]
    assert deque.to_list() == [3, 4, 5]

    deque.clear()
    deque.append(100)
    evicted_left: list[int] = deque.extendleft([200, 300, 400])
    assert evicted_left == [100]
    # extendleft добавляет поочередно слева:
    # 200 -> [200, 100]
    # 300 -> [300, 200, 100]
    # 400 -> выталкивает 100, результат [400, 300, 200]
    assert deque.to_list() == [400, 300, 200]


def test_bounded_deque_indexing_and_mutations() -> None:
    """Проверка прямого доступа по индексу, изменения и удаления элементов."""
    deque: BoundedDeque[str] = BoundedDeque(4, ["a", "b", "c", "d"])

    # Прямой доступ
    assert deque[0] == "a"
    assert deque[3] == "d"
    assert deque[-1] == "d"
    assert deque[-4] == "a"

    with pytest.raises(IndexError):
        _ = deque[4]

    with pytest.raises(IndexError):
        _ = deque[-5]

    # Изменение по индексу
    deque[1] = "beta"
    assert deque[1] == "beta"
    deque[-1] = "delta"
    assert deque[3] == "delta"

    with pytest.raises(IndexError):
        deque[10] = "error"

    # Удаление по индексу
    del deque[1]
    assert deque.to_list() == ["a", "c", "delta"]
    assert len(deque) == 3

    del deque[-1]
    assert deque.to_list() == ["a", "c"]
    assert len(deque) == 2

    with pytest.raises(IndexError):
        del deque[5]


def test_bounded_deque_rotate() -> None:
    """Проверка циклического сдвига элементов вправо и влево."""
    deque: BoundedDeque[int] = BoundedDeque(5, [1, 2, 3, 4, 5])

    deque.rotate(2)
    assert deque.to_list() == [4, 5, 1, 2, 3]

    deque.rotate(-2)
    assert deque.to_list() == [1, 2, 3, 4, 5]

    deque.rotate(0)
    assert deque.to_list() == [1, 2, 3, 4, 5]

    # Пустая очередь и очередь из одного элемента не ломаются
    empty_deque: BoundedDeque[int] = BoundedDeque(3)
    empty_deque.rotate(5)
    assert empty_deque.to_list() == []

    single_deque: BoundedDeque[int] = BoundedDeque(3, [42])
    single_deque.rotate(3)
    assert single_deque.to_list() == [42]


def test_bounded_deque_reverse() -> None:
    """Проверка разворота элементов на месте."""
    deque: BoundedDeque[int] = BoundedDeque(5, [1, 2, 3, 4])
    deque.reverse()
    assert deque.to_list() == [4, 3, 2, 1]

    deque.clear()
    deque.reverse()
    assert deque.to_list() == []


def test_bounded_deque_count_index_remove_contains() -> None:
    """Проверка методов поиска, подсчета и удаления конкретных значений."""
    deque: BoundedDeque[int] = BoundedDeque(5, [10, 20, 30, 20, 40])

    assert deque.count(20) == 2
    assert deque.count(99) == 0
    assert (20 in deque) is True
    assert (99 in deque) is False

    assert deque.index(20) == 1
    assert deque.index(20, start=2) == 3

    with pytest.raises(ValueError, match="не найдено"):
        deque.index(99)

    deque.remove(20)
    assert deque.to_list() == [10, 30, 20, 40]

    with pytest.raises(ValueError, match="не найдено"):
        deque.remove(500)


def test_bounded_deque_iteration_and_reversed() -> None:
    """Проверка прямой и обратной итерации."""
    items: list[int] = [1, 2, 3, 4]
    deque: BoundedDeque[int] = BoundedDeque(6, items)

    assert list(deque) == items
    assert list(reversed(deque)) == [4, 3, 2, 1]


def test_bounded_deque_copy_and_equality() -> None:
    """Проверка поверхностного копирования и операции сравнения."""
    deque1: BoundedDeque[int] = BoundedDeque(4, [1, 2, 3])
    deque2: BoundedDeque[int] = deque1.copy()

    assert deque1 == deque2
    assert deque1 is not deque2
    assert deque2.capacity == deque1.capacity

    deque2.append(4)
    assert deque1 != deque2
    assert (deque1 == "не очередь") is False


def test_bounded_deque_repr() -> None:
    """Проверка строкового представления."""
    deque: BoundedDeque[int] = BoundedDeque(3, [1, 2])
    assert repr(deque) == "BoundedDeque([1, 2], capacity=3)"
