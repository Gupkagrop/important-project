"""Модульные тесты для дескриптора lazy_property."""

from pocket_toolkit.decorators.lazy_property import lazy_property


def test_lazy_property_computation_once() -> None:
    """Проверка однократного ленивого вычисления значения."""
    calls = 0

    class Service:
        @lazy_property
        def heavy_resource(self) -> str:
            """Документация тяжелого ресурса."""
            nonlocal calls
            calls += 1
            return "expensive_result"

    # Доступ через класс возвращает сам дескриптор
    assert isinstance(Service.heavy_resource, lazy_property)
    assert Service.heavy_resource.__doc__ == "Документация тяжелого ресурса."

    svc = Service()
    assert calls == 0

    # Первый доступ — вычисление
    assert svc.heavy_resource == "expensive_result"
    assert calls == 1

    # Повторные доступы — мгновенный возврат закэшированного значения
    assert svc.heavy_resource == "expensive_result"
    assert svc.heavy_resource == "expensive_result"
    assert calls == 1


def test_lazy_property_deletion_and_recomputation() -> None:
    """Проверка сброса значения через del и повторного вычисления."""
    counter = 0

    class CounterBox:
        @lazy_property
        def value(self) -> int:
            nonlocal counter
            counter += 1
            return counter

    box = CounterBox()
    assert box.value == 1
    assert box.value == 1

    # Инвалидация через del
    del box.value
    assert box.value == 2
    assert box.value == 2


def test_lazy_property_assignment() -> None:
    """Проверка явной перезаписи значения свойства."""
    class Person:
        @lazy_property
        def name(self) -> str:
            return "Default"

    p = Person()
    assert p.name == "Default"
    p.name = "Custom"
    assert p.name == "Custom"


def test_lazy_property_with_slots() -> None:
    """Проверка работы с классами, использующими __slots__ без __dict__."""
    invocations = 0

    class SlottedClass:
        __slots__ = ("_id",)

        def __init__(self, item_id: int) -> None:
            self._id = item_id

        @lazy_property
        def token(self) -> str:
            nonlocal invocations
            invocations += 1
            return f"token_{self._id}"

    obj = SlottedClass(100)
    assert invocations == 0
    assert obj.token == "token_100"
    assert invocations == 1
    assert obj.token == "token_100"
    assert invocations == 1

    # Проверка del в slotted
    del obj.token
    assert obj.token == "token_100"
    assert invocations == 2
