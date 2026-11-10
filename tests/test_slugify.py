"""Модульные тесты для модуля транслитерации и слагов (slugify)."""

from pocket_toolkit.strings.slugify import slugify, transliterate


def test_transliterate_cyrillic() -> None:
    """Проверка транслитерации кириллицы в латиницу."""
    assert transliterate("") == ""
    assert transliterate("Привет, Мир!") == "Privet, Mir!"
    assert transliterate("Юлия и Яков") == "Yuliya i Yakov"
    assert transliterate("Щука и борщ") == "Shchuka i borshch"


def test_slugify_basic() -> None:
    """Проверка генерации базовых слагов."""
    assert slugify("") == ""
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("   Multiple   Spaces   ") == "multiple-spaces"
    assert slugify("Special @#$% Characters ^&*()") == "special-characters"


def test_slugify_cyrillic() -> None:
    """Проверка генерации слагов из русскоязычного текста."""
    assert slugify("Привет, мир!") == "privet-mir"
    assert slugify("Быстрая разработка ПО в 2026 году") == "bystraya-razrabotka-po-v-2026-godu"


def test_slugify_custom_separator() -> None:
    """Проверка пользовательского разделителя."""
    assert slugify("Hello World", separator="_") == "hello_world"
    assert slugify("Привет Мир", separator=".") == "privet.mir"


def test_slugify_max_length() -> None:
    """Проверка ограничения максимальной длины слага."""
    text = "A very long title that needs to be truncated"
    slug = slugify(text, max_length=15)
    assert len(slug) <= 15
    assert not slug.endswith("-")


def test_slugify_allow_unicode() -> None:
    """Проверка флага сохранения юникода."""
    assert slugify("Привет Мир", allow_unicode=True) == "привет-мир"
