"""Модульные тесты для LFUCache."""

import pytest

from pocket_toolkit.structures.lfu_cache import LFUCache, _LFUEntry


def test_lfu_entry_repr() -> None:
    """Проверка строкового представления внутренней записи _LFUEntry."""
    entry: _LFUEntry[str, int] = _LFUEntry("a", 10, freq=2)
    assert repr(entry) == "_LFUEntry(key='a', value=10, freq=2)"


def test_lfu_cache_init_valid() -> None:
    """Проверка создания кэша с корректной вместимостью."""
    cache: LFUCache[str, int] = LFUCache(3)
    assert cache.capacity == 3
    assert cache.size == 0
    assert len(cache) == 0
    assert cache.is_empty() is True
    assert cache.is_full() is False
    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.hit_ratio == 0.0
    assert cache.min_freq == 0


def test_lfu_cache_init_invalid_capacity() -> None:
    """Проверка генерации ошибки при неположительной вместимости кэша."""
    with pytest.raises(ValueError, match="строго больше нуля"):
        LFUCache(0)

    with pytest.raises(ValueError, match="строго больше нуля"):
        LFUCache(-5)


def test_lfu_cache_init_with_initial_items() -> None:
    """Проверка инициализации кэша начальными элементами."""
    initial: list[tuple[str, int]] = [("a", 1), ("b", 2)]
    cache: LFUCache[str, int] = LFUCache(3, initial_items=initial)
    assert len(cache) == 2
    assert cache["a"] == 1
    assert cache["b"] == 2


def test_lfu_cache_init_with_initial_items_exceeding_capacity() -> None:
    """Проверка инициализации кэша набором данных, превышающим вместимость."""
    initial: list[tuple[str, int]] = [("a", 1), ("b", 2), ("c", 3)]
    cache: LFUCache[str, int] = LFUCache(2, initial_items=initial)
    assert len(cache) == 2
    assert "a" not in cache
    assert cache["b"] == 2
    assert cache["c"] == 3


def test_lfu_cache_put_and_get() -> None:
    """Проверка базового сохранения и извлечения элементов с учетом частоты."""
    cache: LFUCache[str, int] = LFUCache(2)
    cache.put("x", 100)
    assert cache.get("x") == 100
    assert cache.get_frequency("x") == 2
    assert cache.hits == 1
    assert cache.misses == 0
    assert cache.hit_ratio == 1.0

    assert cache.get("missing") is None
    assert cache.get("missing", 999) == 999
    assert cache.get_frequency("missing") is None
    assert cache.misses == 2
    assert cache.hits == 1
    assert cache.hit_ratio == pytest.approx(1 / 3)


def test_lfu_cache_update_existing_key() -> None:
    """Проверка обновления существующего ключа и увеличения его частоты."""
    cache: LFUCache[str, str] = LFUCache(2)
    cache.put("k1", "v1")
    cache.put("k2", "v2")
    assert cache.get_frequency("k1") == 1
    assert cache.get_frequency("k2") == 1

    # Обновление k1 увеличивает его частоту до 2
    cache.put("k1", "v1_updated")
    assert len(cache) == 2
    assert cache["k1"] == "v1_updated"
    assert cache.get_frequency("k1") == 3  # put + [] access

    # Добавление k3 вытесняет k2 (частота 1 < частоты 3)
    cache.put("k3", "v3")
    assert "k2" not in cache
    assert "k1" in cache
    assert "k3" in cache


def test_lfu_cache_eviction_policy_by_frequency_and_lru() -> None:
    """Проверка вытеснения по наименьшей частоте и по LRU при равных частотах."""
    cache: LFUCache[str, int] = LFUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    # Частоты: a:1, b:1, c:1 (LRU порядок в баке 1: c (MRU) -> b -> a (LRU))

    # Обращение к 'a' дважды делает его freq=3
    _ = cache.get("a")
    _ = cache.get("a")
    assert cache.get_frequency("a") == 3

    # Обращение к 'b' единожды делает его freq=2
    _ = cache.get("b")
    assert cache.get_frequency("b") == 2

    # 'c' остался с freq=1. При добавлении 'd' именно 'c' вытесняется
    cache.put("d", 4)
    assert cache.is_full() is True
    assert "c" not in cache
    assert "a" in cache
    assert "b" in cache
    assert "d" in cache

    # Теперь freq(a)=3, freq(b)=2, freq(d)=1
    # Добавление 'e' вытеснит 'd' (минимальная частота = 1)
    cache.put("e", 5)
    assert "d" not in cache
    assert "e" in cache

    # 'b' (freq=2) и 'e' (freq=1). Добавление 'f' вытесняет 'e'
    cache.put("f", 6)
    assert "e" not in cache
    assert "f" in cache


def test_lfu_cache_lru_tie_breaking_within_same_frequency() -> None:
    """Проверка вытеснения по правилу LRU при одинаковой частоте нескольких элементов."""
    cache: LFUCache[str, int] = LFUCache(3)
    cache.put("x", 10)
    cache.put("y", 20)
    cache.put("z", 30)
    # Все имеют freq=1. Порядок добавления: x (LRU), y, z (MRU)

    # При добавлении 'w' вытесняется 'x' как наименее недавно использованный с минимальной частотой
    cache.put("w", 40)
    assert "x" not in cache
    assert "y" in cache
    assert "z" in cache
    assert "w" in cache


def test_lfu_cache_peek() -> None:
    """Проверка подглядывания элементов без изменения частот и статистики."""
    cache: LFUCache[str, int] = LFUCache(2)
    cache.put("first", 1)
    cache.put("second", 2)

    assert cache.peek("first") == 1
    assert cache.get_frequency("first") == 1
    assert cache.hits == 0
    assert cache.misses == 0

    assert cache.peek("unknown") is None
    assert cache.peek("unknown", -1) == -1
    assert cache.misses == 0


def test_lfu_cache_peek_lfu() -> None:
    """Проверка инспекции наименее часто используемого кандидата на вытеснение."""
    cache: LFUCache[str, int] = LFUCache(3)
    assert cache.peek_lfu() is None

    cache.put("x", 10)
    cache.put("y", 20)
    # x и y имеют freq=1, x — LRU в баке 1
    assert cache.peek_lfu() == ("x", 10)

    # Обращение к x повышает его частоту
    _ = cache.get("x")
    # Теперь y имеет минимальную частоту 1
    assert cache.peek_lfu() == ("y", 20)


def test_lfu_cache_pop() -> None:
    """Проверка извлечения конкретного элемента по ключу."""
    cache: LFUCache[str, int] = LFUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    _ = cache.get("a")  # freq(a)=2

    val: int = cache.pop("a")
    assert val == 1
    assert "a" not in cache
    assert len(cache) == 2
    assert cache.min_freq == 1

    with pytest.raises(KeyError, match="не найден"):
        cache.pop("non_existent")


def test_lfu_cache_pop_single_min_freq_element() -> None:
    """Проверка обновления min_freq при удалении последнего элемента минимальной частоты."""
    cache: LFUCache[str, int] = LFUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    _ = cache.get("a")  # freq(a)=2, freq(b)=1, min_freq=1

    # Удаляем b (единственный узел с freq=1)
    cache.pop("b")
    # min_freq должен пересчитаться в 2
    assert cache.min_freq == 2

    # Очищаем последний элемент
    cache.pop("a")
    assert cache.min_freq == 0
    assert cache.is_empty() is True


def test_lfu_cache_pop_lfu() -> None:
    """Проверка принудительного извлечения кандидата LFU."""
    cache: LFUCache[str, int] = LFUCache(3)
    with pytest.raises(KeyError, match="кэш пуст"):
        cache.pop_lfu()

    cache.put("low", 1)
    cache.put("high", 2)
    _ = cache.get("high")  # freq=2

    item: tuple[str, int] = cache.pop_lfu()
    assert item == ("low", 1)
    assert "low" not in cache
    assert len(cache) == 1


def test_lfu_cache_delete() -> None:
    """Проверка безопасного удаления элементов по ключу."""
    cache: LFUCache[str, int] = LFUCache(2)
    cache.put("a", 10)

    assert cache.delete("a") is True
    assert "a" not in cache
    assert len(cache) == 0

    assert cache.delete("a") is False
    assert cache.delete("missing") is False


def test_lfu_cache_dict_protocol() -> None:
    """Проверка работы операторов индексации [], in, del."""
    cache: LFUCache[str, int] = LFUCache(2)
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


def test_lfu_cache_resize_shrink() -> None:
    """Проверка уменьшения вместимости с вытеснением LFU элементов."""
    cache: LFUCache[str, int] = LFUCache(5)
    for i in range(1, 6):
        cache.put(f"k{i}", i)

    # Увеличим частоты для k4 и k5
    _ = cache.get("k4")
    _ = cache.get("k5")

    # Уменьшаем размер до 2. Должны вытесниться k1, k2, k3 (freq=1)
    evicted: int = cache.resize(2)
    assert evicted == 3
    assert cache.capacity == 2
    assert len(cache) == 2
    assert set(cache.keys()) == {"k4", "k5"}


def test_lfu_cache_resize_expand_and_invalid() -> None:
    """Проверка увеличения вместимости и валидации аргумента."""
    cache: LFUCache[str, int] = LFUCache(2)
    cache.put("a", 1)

    evicted: int = cache.resize(10)
    assert evicted == 0
    assert cache.capacity == 10
    assert len(cache) == 1

    with pytest.raises(ValueError, match="больше 0"):
        cache.resize(0)

    with pytest.raises(ValueError, match="больше 0"):
        cache.resize(-1)


def test_lfu_cache_clear_and_reset_stats() -> None:
    """Проверка полной очистки кэша и сброса статистики."""
    cache: LFUCache[str, int] = LFUCache(2)
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


def test_lfu_cache_views_and_iteration() -> None:
    """Проверка методов keys, values, items, to_dict и итерирования по частотам."""
    cache: LFUCache[str, int] = LFUCache(3)
    cache.put("low", 1)
    cache.put("mid", 2)
    cache.put("high", 3)

    # Поднимаем частоту high до 3, mid до 2
    _ = cache.get("high")
    _ = cache.get("high")
    _ = cache.get("mid")

    assert cache.keys() == ["high", "mid", "low"]
    assert cache.values() == [3, 2, 1]
    assert cache.items() == [("high", 3), ("mid", 2), ("low", 1)]
    assert cache.to_dict() == {"high": 3, "mid": 2, "low": 1}
    assert list(cache) == ["high", "mid", "low"]


def test_lfu_cache_repr_and_equality() -> None:
    """Проверка строкового представления и сравнения двух кэшей."""
    c1: LFUCache[str, int] = LFUCache(2)
    c1.put("a", 1)
    c1.put("b", 2)
    assert repr(c1) == "LFUCache(capacity=2, size=2)"

    c2: LFUCache[str, int] = LFUCache(2)
    c2.put("a", 1)
    c2.put("b", 2)
    assert c1 == c2

    # Обращение меняет частоты и делает кэши неравными по items()
    _ = c1.get("a")
    assert c1 != c2

    c3: LFUCache[str, int] = LFUCache(5)
    c3.put("a", 1)
    c3.put("b", 2)
    assert c1 != c3

    assert c1 != "not_a_cache"


def test_lfu_cache_single_capacity() -> None:
    """Проверка граничного случая: кэш с вместимостью 1."""
    cache: LFUCache[str, int] = LFUCache(1)
    cache.put("a", 10)
    assert cache.is_full() is True
    assert cache["a"] == 10

    cache.put("b", 20)
    assert "a" not in cache
    assert cache["b"] == 20
    assert len(cache) == 1
