"""Модуль декоратора мемоизации с ограничением времени жизни (Timed Cache with TTL).

Предоставляет декоратор `@timed_cache` для кэширования результатов вызовов функций
на заданное время жизни (TTL, Time-To-Live) с ограничением максимального размера (LRU вытеснением),
потокобезопасностью и сбором статистики попаданий и промахов.
"""

from collections import OrderedDict
from collections.abc import Callable, Hashable
from dataclasses import dataclass
import functools
import threading
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class CacheInfo:
    """Статистика использования кэша."""

    hits: int
    misses: int
    maxsize: int | None
    currsize: int


@dataclass(slots=True)
class _CacheEntry[V]:
    """Запись кэша со значением и абсолютным временем истечения."""

    value: V
    expires_at: float


def _make_key(
    args: tuple[object, ...],
    kwargs: dict[str, object],
    typed: bool,
) -> tuple[Hashable, ...]:
    """Формирует хэшируемый ключ кэша на основе аргументов функции."""
    key_parts: list[Hashable] = list(args)
    if kwargs:
        for k, v in sorted(kwargs.items()):
            key_parts.append((k, v))
    if typed:
        for arg in args:
            key_parts.append(type(arg))
        for v in kwargs.values():
            key_parts.append(type(v))
    return tuple(key_parts)


def timed_cache(
    ttl: float,
    maxsize: int | None = 128,
    typed: bool = False,
    time_func: Callable[[], float] = time.monotonic,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор кэширования результатов функций с ограничением по времени жизни (TTL).

    :param ttl: Время жизни записи кэша в секундах (> 0).
    :param maxsize: Максимальный размер кэша (или None для неограниченного размера).
    :param typed: Учитывать ли типы переданных аргументов при формировании ключа.
    :param time_func: Функция получения текущего монотонного времени.
    :return: Декорированная функция со встроенными методами управления кэшем.
    """
    if ttl <= 0:
        raise ValueError(f"TTL должен быть строго положительным (> 0), получено: {ttl}")
    if maxsize is not None and maxsize < 1:
        raise ValueError(f"maxsize должен быть >= 1 или None, получено: {maxsize}")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        cache: OrderedDict[tuple[Hashable, ...], _CacheEntry[R]] = OrderedDict()
        lock = threading.Lock()
        hits = 0
        misses = 0

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal hits, misses

            key = _make_key(args, kwargs, typed)
            now = time_func()

            with lock:
                if key in cache:
                    entry = cache[key]
                    if entry.expires_at > now:
                        # Попадание в кэш: перемещаем в конец как недавно использованный
                        cache.move_to_end(key)
                        hits += 1
                        return entry.value
                    # Срок жизни истек — удаляем
                    del cache[key]

                misses += 1

            # Вычисляем новое значение вне блокировки для предотвращения взаимных блокировок
            val = func(*args, **kwargs)
            expires_at = time_func() + ttl

            with lock:
                # Если после вычисления ключ уже успели добавить и он свежий — возвращаем его
                if key in cache and cache[key].expires_at > time_func():
                    return cache[key].value

                cache[key] = _CacheEntry(value=val, expires_at=expires_at)
                cache.move_to_end(key)

                # Вытеснение по LRU при превышении maxsize
                if maxsize is not None and len(cache) > maxsize:
                    cache.popitem(last=False)

            return val

        def cache_info() -> CacheInfo:
            """Возвращает снимок статистики попаданий и промахов кэша."""
            with lock:
                return CacheInfo(
                    hits=hits,
                    misses=misses,
                    maxsize=maxsize,
                    currsize=len(cache),
                )

        def cache_clear() -> None:
            """Полностью очищает кэш и сбрасывает статистику."""
            nonlocal hits, misses
            with lock:
                cache.clear()
                hits = 0
                misses = 0

        def cache_evict_expired() -> int:
            """Принудительно удаляет все устаревшие записи из кэша и возвращает их количество."""
            now = time_func()
            evicted = 0
            with lock:
                expired_keys = [k for k, entry in cache.items() if entry.expires_at <= now]
                for k in expired_keys:
                    del cache[k]
                    evicted += 1
            return evicted

        # Добавляем служебные методы к функции
        setattr(wrapper, "cache_info", cache_info)
        setattr(wrapper, "cache_clear", cache_clear)
        setattr(wrapper, "cache_evict_expired", cache_evict_expired)

        return wrapper

    return decorator
