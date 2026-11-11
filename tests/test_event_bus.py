"""Модуль модульных тестов для шины событий (event_bus)."""

import threading
from dataclasses import dataclass

import pytest

from pocket_toolkit.system.event_bus import EventBus


@dataclass(frozen=True)
class UserRegisteredEvent:
    """Событие успешной регистрации пользователя."""

    user_id: int
    username: str


def test_event_bus_typed_subscription() -> None:
    """Проверка подписки на класс события."""
    bus = EventBus()
    received: list[UserRegisteredEvent] = []

    def handle_user(event: object) -> None:
        if isinstance(event, UserRegisteredEvent):
            received.append(event)

    unsub = bus.subscribe(UserRegisteredEvent, handle_user)
    assert bus.has_subscribers(UserRegisteredEvent)

    count = bus.publish(UserRegisteredEvent(user_id=1, username="denis"))
    assert count == 1
    assert len(received) == 1
    assert received[0].username == "denis"

    # Отписка через возвращенную функцию
    unsub()
    assert not bus.has_subscribers(UserRegisteredEvent)
    bus.publish(UserRegisteredEvent(user_id=2, username="alice"))
    assert len(received) == 1


def test_event_bus_string_events() -> None:
    """Проверка событий, идентифицируемых строковым именем."""
    bus = EventBus()
    notifications: list[str] = []

    @bus.on("cache.invalidated")
    def on_cache(event: object) -> None:
        notifications.append(str(event))

    bus.publish("cache.invalidated")
    assert notifications == ["cache.invalidated"]


def test_event_bus_subscribe_once() -> None:
    """Проверка разовой подписки subscribe_once."""
    bus = EventBus()
    calls: list[int] = []

    bus.subscribe_once("tick", lambda ev: calls.append(1))

    bus.publish("tick")
    bus.publish("tick")
    assert calls == [1]
    assert not bus.has_subscribers("tick")


def test_event_bus_error_propagation() -> None:
    """Проверка политик распространения исключений в обработчиках."""
    # По умолчанию propagate_errors=True
    strict_bus = EventBus(propagate_errors=True)

    def failing_handler(_: object) -> None:
        raise ValueError("Ошибка в подписчике")

    strict_bus.subscribe("error_event", failing_handler)
    with pytest.raises(ValueError, match="Ошибка в подписчике"):
        strict_bus.publish("error_event")

    # Игнорирование ошибок при propagate_errors=False
    lenient_bus = EventBus(propagate_errors=False)
    lenient_bus.subscribe("error_event", failing_handler)
    assert lenient_bus.publish("error_event") == 0


def test_event_bus_thread_safety() -> None:
    """Проверка потокобезопасности при конкурентной публикации и подписке."""
    bus = EventBus()
    counter = 0
    lock = threading.Lock()

    def worker_handler(_: object) -> None:
        nonlocal counter
        with lock:
            counter += 1

    bus.subscribe("job", worker_handler)

    threads: list[threading.Thread] = []
    for _ in range(10):
        t = threading.Thread(target=lambda: [bus.publish("job") for _ in range(20)])
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert counter == 200
