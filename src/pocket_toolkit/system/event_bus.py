"""Модуль синхронной потокобезопасной шины событий (Event Bus / Observer).

Предоставляет класс EventBus для реализации шаблона издатель-подписчик (Pub/Sub)
с поддержкой типизированных событий (классов), строк-наименований, разовых подписок (once)
и потокобезопасности с помощью RLock.
"""

import threading
from collections.abc import Callable
from typing import TypeVar

E = TypeVar("E")
EventHandler = Callable[[object], None]


class EventBus:
    """Синхронная потокобезопасная шина событий."""

    def __init__(self, propagate_errors: bool = True) -> None:
        """Инициализирует шину событий."""
        self.propagate_errors: bool = propagate_errors
        self._subscribers: dict[object, list[EventHandler]] = {}
        self._lock: threading.RLock = threading.RLock()

    def _get_key(self, event_or_type: object) -> object:
        """Возвращает ключ сопоставления (тип класса или строка)."""
        if isinstance(event_or_type, (str, type)):
            return event_or_type
        return type(event_or_type)

    def subscribe(
        self,
        event_type: object,
        handler: EventHandler,
    ) -> Callable[[], None]:
        """Подписывает обработчик на тип события и возвращает функцию отписки.

        :param event_type: Класс события или строка-наименование.
        :param handler: Функция-обработчик с одним аргументом (событие).
        :return: Замыкание для мгновенной отписки.
        """
        key = self._get_key(event_type)
        with self._lock:
            if key not in self._subscribers:
                self._subscribers[key] = []
            if handler not in self._subscribers[key]:
                self._subscribers[key].append(handler)

        def _unsubscribe() -> None:
            self.unsubscribe(event_type, handler)

        return _unsubscribe

    def subscribe_once(
        self,
        event_type: object,
        handler: EventHandler,
    ) -> Callable[[], None]:
        """Подписывает обработчик ровно на один вызов (после срабатывания отписывается)."""
        unsub_fn: Callable[[], None] | None = None

        def _wrapper(event: object) -> None:
            nonlocal unsub_fn
            if unsub_fn is not None:
                unsub_fn()
            handler(event)

        unsub_fn = self.subscribe(event_type, _wrapper)
        return unsub_fn

    def unsubscribe(self, event_type: object, handler: EventHandler) -> bool:
        """Отписывает обработчик от указанного события."""
        key = self._get_key(event_type)
        with self._lock:
            handlers = self._subscribers.get(key)
            if not handlers or handler not in handlers:
                return False
            handlers.remove(handler)
            if not handlers:
                self._subscribers.pop(key, None)
            return True

    def publish(self, event: object) -> int:
        """Публикует событие и синхронно оповещает всех подписчиков.

        :param event: Экземпляр события или строковый идентификатор.
        :return: Количество успешно вызванных обработчиков.
        """
        key = self._get_key(event)
        with self._lock:
            handlers = list(self._subscribers.get(key, []))

        invoked_count = 0
        for handler in handlers:
            try:
                handler(event)
                invoked_count += 1
            except Exception:
                if self.propagate_errors:
                    raise

        return invoked_count

    def has_subscribers(self, event_type: object) -> bool:
        """Проверяет, зарегистрированы ли подписчики на данный тип события."""
        key = self._get_key(event_type)
        with self._lock:
            return bool(self._subscribers.get(key))

    def clear(self, event_type: object | None = None) -> None:
        """Очищает всех подписчиков (или подписчиков конкретного события)."""
        with self._lock:
            if event_type is None:
                self._subscribers.clear()
            else:
                key = self._get_key(event_type)
                self._subscribers.pop(key, None)

    def on(self, event_type: object) -> Callable[[EventHandler], EventHandler]:
        """Декоратор для удобной регистрации обработчика события."""
        def _decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(event_type, handler)
            return handler

        return _decorator
