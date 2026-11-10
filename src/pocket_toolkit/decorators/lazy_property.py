"""Модуль дескриптора ленивого свойства (Lazy Property Wrapper).

Предоставляет дескриптор `@lazy_property` для отложенного вычисления атрибута
экземпляра класса при первом обращении, с кэшированием результата, поддержкой
потокобезопасности, сброса значения (`del obj.prop`) и совместимости со слотами (`__slots__`).
"""

from collections.abc import Callable
import threading
from typing import Any, Generic, TypeVar, overload

T = TypeVar("T")
R = TypeVar("R")


class lazy_property(Generic[T, R]):
    """Дескриптор лениво вычисляемого свойства класса.

    Вычисляет значение свойства только при первом обращении к нему через экземпляр,
    после чего сохраняет результат и при последующих обращениях возвращает закэшированное значение за O(1).
    Поддерживает удаление `del instance.attr` для принудительного инвалидирования кэша.
    """

    def __init__(self, func: Callable[[T], R]) -> None:
        """Инициализирует дескриптор ленивого свойства.

        :param func: Метод вычисления значения свойства (принимает `self`).
        """
        self.func: Callable[[T], R] = func
        self.attrname: str = func.__name__
        self.__doc__ = func.__doc__
        self._lock: threading.Lock = threading.Lock()
        # Резервное хранилище для классов со __slots__, где нет __dict__
        self._slots_cache: dict[int, R] = {}

    def __set_name__(self, owner: type[T], name: str) -> None:
        """Сохраняет имя атрибута при создании класса."""
        self.attrname = name

    @overload
    def __get__(self, instance: None, owner: type[T] | None = None) -> "lazy_property[T, R]":
        ...

    @overload
    def __get__(self, instance: T, owner: type[T] | None = None) -> R:
        ...

    def __get__(self, instance: T | None, owner: type[T] | None = None) -> "R | lazy_property[T, R]":
        """Возвращает закэшированное значение или вычисляет его при первом обращении."""
        if instance is None:
            return self

        # 1. Если экземпляр имеет __dict__, используем стандартный механизм кэширования в словаре объекта
        if hasattr(instance, "__dict__"):
            inst_dict = instance.__dict__
            if self.attrname in inst_dict:
                return inst_dict[self.attrname]  # type: ignore[no-any-return]

            with self._lock:
                if self.attrname in inst_dict:
                    return inst_dict[self.attrname]  # type: ignore[no-any-return]
                val = self.func(instance)
                inst_dict[self.attrname] = val
                return val

        # 2. Если у класса определены __slots__ и нет __dict__
        inst_id = id(instance)
        with self._lock:
            if inst_id in self._slots_cache:
                return self._slots_cache[inst_id]
            val = self.func(instance)
            self._slots_cache[inst_id] = val
            return val

    def __set__(self, instance: T, value: R) -> None:
        """Позволяет явно перезаписать ленивое свойство."""
        if hasattr(instance, "__dict__"):
            instance.__dict__[self.attrname] = value
        else:
            with self._lock:
                self._slots_cache[id(instance)] = value

    def __delete__(self, instance: T) -> None:
        """Сбрасывает вычисленное значение, заставляя вычислить его повторно при следующем вызове."""
        if hasattr(instance, "__dict__"):
            if self.attrname in instance.__dict__:
                del instance.__dict__[self.attrname]
        else:
            with self._lock:
                self._slots_cache.pop(id(instance), None)
