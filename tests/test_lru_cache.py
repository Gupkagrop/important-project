"""Модульные тесты для LRUCache."""

import pytest

from pocket_toolkit.structures.lru_cache import LRUCache


def test_lru_cache_init_valid() -> None:
    """Проверка создания кэша с корректной вместимостью."""
    cache: LRUCache[str, int] = LRUCache(3)
    assert cache.capacity == 3
    assert cache.size == 0
    assert len(cache) == 0
    assert cache.is_empty() is True
    assert cache.is_full() is False
    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.hit_ratio == 0.0


def test_lru_cache_init_invalid_capacity() -> None:
    """Проверка генерации ошибки при неположительной вместимости кэша."""
    with pytest.raises(ValueError, match="строго больше нуля"):
        LRUCache(0)

    with pytest.raises(ValueError, match="строго больше нуля"):
        LRUCache(-10)


def test_lru_cache_init_with_initial_items() -> None:
    """Проверка инициализации кэша начальными элементами."""
    initial: list[tuple[str, int]] = [("a", 1), ("b", 2)]
    cache: LRUCache[str, int] = LRUCache(3, initial_items=initial)
    assert len(cache) == 2
    assert cache["a"] == 1
    assert cache["b"] == 2


def test_lru_cache_init_with_initial_items_exceeding_capacity() -> None:
    """Проверка инициализации кэша набором данных, превышающим вместимость."""
    initial: list[tuple[str, int]] = [("a", 1), ("b", 2), ("c", 3)]
    cache: LRUCache[str, int] = LRUCache(2, initial_items=initial)
    assert len(cache) == 2
    assert "a" not in cache
    assert cache["b"] == 2
    assert cache["c"] == 3


def test_lru_cache_put_and_get() -> None:
    """Проверка базового сохранения и извлечения элементов."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("x", 100)
    assert cache.get("x") == 100
    assert cache.hits == 1
    assert cache.misses == 0
    assert cache.hit_ratio == 1.0

    assert cache.get("missing") is None
    assert cache.get("missing", 999) == 999
    assert cache.misses == 2
    assert cache.hits == 1
    assert cache.hit_ratio == pytest.approx(1 / 3)


def test_lru_cache_update_existing_key() -> None:
    """Проверка обновления существующего ключа без увеличения размера кэша."""
    cache: LRUCache[str, str] = LRUCache(2)
    cache.put("k1", "v1")
    cache.put("k2", "v2")
    assert len(cache) == 2

    # Обновление k1 перемещает его в MRU
    cache.put("k1", "v1_updated")
    assert len(cache) == 2
    assert cache["k1"] == "v1_updated"

    # Добавление k3 должно вытеснить k2, так как k1 недавно обновлялся
    cache.put("k3", "v3")
    assert "k2" not in cache
    assert "k1" in cache
    assert "k3" in cache


def test_lru_cache_eviction_policy() -> None:
    """Проверка строгого порядка вытеснения наименее востребованных элементов."""
    cache: LRUCache[str, int] = LRUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    # Порядок (MRU -> LRU): c, b, a

    assert cache.keys() == ["c", "b", "a"]

    # Обращение к "a" поднимает его на вершину (MRU)
    _ = cache.get("a")
    # Новый порядок: a, c, b
    assert cache.keys() == ["a", "c", "b"]

    # Добавление нового ключа должно вытеснить "b"
    cache.put("d", 4)
    assert cache.is_full() is True
    assert "b" not in cache
    assert cache.keys() == ["d", "a", "c"]


def test_lru_cache_peek() -> None:
    """Проверка подглядывания значений без изменения порядка и статистики."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("first", 1)
    cache.put("second", 2)

    assert cache.peek("first") == 1
    assert cache.hits == 0
    assert cache.misses == 0
    # Порядок не изменился: second все еще MRU
    assert cache.keys() == ["second", "first"]

    assert cache.peek("unknown") is None
    assert cache.peek("unknown", -1) == -1
    assert cache.misses == 0


def test_lru_cache_peek_lru_and_mru() -> None:
    """Проверка инспекции краевых элементов (MRU и LRU)."""
    cache: LRUCache[str, int] = LRUCache(3)
    assert cache.peek_lru() is None
    assert cache.peek_mru() is None

    cache.put("x", 10)
    assert cache.peek_lru() == ("x", 10)
    assert cache.peek_mru() == ("x", 10)

    cache.put("y", 20)
    assert cache.peek_mru() == ("y", 20)
    assert cache.peek_lru() == ("x", 10)


def test_lru_cache_pop() -> None:
    """Проверка извлечения конкретного элемента по ключу."""
    cache: LRUCache[str, int] = LRUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)

    val: int = cache.pop("a")
    assert val == 1
    assert "a" not in cache
    assert len(cache) == 1

    with pytest.raises(KeyError, match="не найден"):
        cache.pop("non_existent")


def test_lru_cache_pop_lru_and_pop_mru() -> None:
    """Проверка удаления и извлечения краевых элементов LRU и MRU."""
    cache: LRUCache[str, int] = LRUCache(3)
    with pytest.raises(KeyError, match="кэш пуст"):
        cache.pop_lru()

    with pytest.raises(KeyError, match="кэш пуст"):
        cache.pop_mru()

    cache.put("low", 1)
    cache.put("mid", 2)
    cache.put("high", 3)
    # MRU: high, LRU: low

    lru_item: tuple[str, int] = cache.pop_lru()
    assert lru_item == ("low", 1)
    assert "low" not in cache
    assert len(cache) == 2

    mru_item: tuple[str, int] = cache.pop_mru()
    assert mru_item == ("high", 3)
    assert "high" not in cache
    assert len(cache) == 1
    assert cache.keys() == ["mid"]


def test_lru_cache_delete() -> None:
    """Проверка безопасного удаления элементов по ключу."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 10)

    assert cache.delete("a") is True
    assert "a" not in cache
    assert len(cache) == 0

    assert cache.delete("a") is False
    assert cache.delete("missing") is False


def test_lru_cache_dict_protocol() -> None:
    """Проверка работы операторов индексации [], in, del."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache["one"] = 1
    cache["two"] = 2

    assert cache["one"] == 1
    assert "one" in cache
    assert "three" not in cache

    with pytest.raises(KeyError):
        _ = cache["unknown"]

    del cache["one"]
    assert "one" not in cache
    assert len(cache) == 1

    with pytest.raises(KeyError):
        del cache["one"]


def test_lru_cache_resize_shrink() -> None:
    """Проверка уменьшения вместимости с вытеснением старых элементов."""
    cache: LRUCache[str, int] = LRUCache(5)
    for i in range(1, 6):
        cache.put(f"k{i}", i)
    assert len(cache) == 5

    # Уменьшаем вместимость до 2, должны быть вытеснены k1, k2, k3
    evicted: int = cache.resize(2)
    assert evicted == 3
    assert cache.capacity == 2
    assert len(cache) == 2
    assert cache.keys() == ["k5", "k4"]


def test_lru_cache_resize_expand_and_invalid() -> None:
    """Проверка увеличения вместимости и передачи некорректного значения."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)

    evicted: int = cache.resize(10)
    assert evicted == 0
    assert cache.capacity == 10
    assert len(cache) == 1

    with pytest.raises(ValueError, match="больше 0"):
        cache.resize(0)

    with pytest.raises(ValueError, match="больше 0"):
        cache.resize(-1)


def test_lru_cache_clear_and_reset_stats() -> None:
    """Проверка полной очистки кэша и сброса статистики."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)
    _ = cache.get("a")
    _ = cache.get("b")
    assert cache.hits == 1
    assert cache.misses == 1

    cache.clear(reset_stats=False)
    assert len(cache) == 0
    assert cache.is_empty() is True
    assert cache.hits == 1
    assert cache.misses == 1

    cache.reset_stats()
    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.hit_ratio == 0.0

    cache.put("x", 10)
    _ = cache.get("x")
    cache.clear(reset_stats=True)
    assert len(cache) == 0
    assert cache.hits == 0
    assert cache.misses == 0


def test_lru_cache_views_and_iteration() -> None:
    """Проверка методов keys, values, items, to_dict и итератора."""
    cache: LRUCache[str, int] = LRUCache(3)
    cache.put("first", 1)
    cache.put("second", 2)
    cache.put("third", 3)

    assert cache.keys() == ["third", "second", "first"]
    assert cache.values() == [3, 2, 1]
    assert cache.items() == [("third", 3), ("second", 2), ("first", 1)]
    assert cache.to_dict() == {"third": 3, "second": 2, "first": 1}
    assert list(cache) == ["third", "second", "first"]


def test_lru_cache_repr_and_equality() -> None:
    """Проверка строкового представления и сравнения на равенство."""
    c1: LRUCache[str, int] = LRUCache(2)
    c1.put("a", 1)
    c1.put("b", 2)
    assert repr(c1) == "LRUCache(capacity=2, size=2)"

    c2: LRUCache[str, int] = LRUCache(2)
    c2.put("a", 1)
    c2.put("b", 2)
    assert c1 == c2

    # Разный порядок обращений делает их не равными
    _ = c1.get("a")
    assert c1 != c2

    c3: LRUCache[str, int] = LRUCache(5)
    c3.put("a", 1)
    c3.put("b", 2)
    assert c1 != c3

    assert c1 != "not_a_cache"


def test_lru_cache_single_capacity() -> None:
    """Проверка граничного случая: кэш с вместимостью 1."""
    cache: LRUCache[str, int] = LRUCache(1)
    cache.put("a", 10)
    assert cache.is_full() is True
    assert cache["a"] == 10

    cache.put("b", 20)
    assert "a" not in cache
    assert cache["b"] == 20
    assert len(cache) == 1

    cache.put("b", 25)
    assert cache["b"] == 25
    assert len(cache) == 1
