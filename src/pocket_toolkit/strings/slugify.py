"""Модуль транслитерации и генерации URL-слагов (Slugify & Transliteration).

Предоставляет функцию `transliterate` для транслитерации кириллицы в латиницу
и функцию `slugify` для формирования безопасных, стандартизированных URL-идентификаторов (слагов)
с удалением спецсимволов, нормализацией разделителей и ограничением длины.
"""

import re
import unicodedata

# Таблица транслитерации символов русского алфавита в латиницу
_CYRILLIC_TO_LATIN: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "Yo",
    "Ж": "Zh", "З": "Z", "И": "I", "Й": "Y", "К": "K", "Л": "L", "М": "M",
    "Н": "N", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U",
    "Ф": "F", "Х": "Kh", "Ц": "Ts", "Ч": "Ch", "Ш": "Sh", "Щ": "Shch",
    "Ъ": "", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "Yu", "Я": "Ya",
}


def transliterate(text: str) -> str:
    """Транслитерирует символы кириллицы в латиницу с сохранением регистра.

    :param text: Исходная строка с кириллическими символами.
    :return: Строка с транслитерированными символами.
    """
    if not text:
        return ""

    result: list[str] = []
    for char in text:
        result.append(_CYRILLIC_TO_LATIN.get(char, char))

    return "".join(result)


def slugify(
    text: str,
    separator: str = "-",
    lowercase: bool = True,
    max_length: int | None = None,
    allow_unicode: bool = False,
) -> str:
    """Генерирует чистый и безопасный URL-слаг из произвольного текста.

    :param text: Исходная строка.
    :param separator: Разделитель слов (по умолчанию дефис '-').
    :param lowercase: Приводить ли результат к нижнему регистру (по умолчанию True).
    :param max_length: Максимальная длина слага в символах (или None).
    :param allow_unicode: Разрешать ли сохранение не-ASCII символов без транслитерации.
    :return: Сформированный URL-слаг.
    """
    if not text:
        return ""

    # 1. Транслитерация кириллицы (если allow_unicode=False)
    working_text = text if allow_unicode else transliterate(text)

    # 2. NFKD-нормализация для удаления диакритических знаков (акцентов)
    normalized = unicodedata.normalize("NFKD", working_text)
    if not allow_unicode:
        normalized = normalized.encode("ascii", "ignore").decode("ascii")

    # 3. Приведение к нижнему регистру
    if lowercase:
        normalized = normalized.lower()

    # 4. Замена любых недопустимых символов (пробелы, пунктуация) на разделитель
    if allow_unicode:
        # Разрешаем буквы, цифры и подчеркивания
        pattern = r"[^\w\s-]"
    else:
        pattern = r"[^a-zA-Z0-9\s-]"

    cleaned = re.sub(pattern, " ", normalized)

    # 5. Схлопывание пробелов и дефисов в заданный разделитель
    escaped_sep = re.escape(separator)
    slug = re.sub(r"[\s" + escaped_sep + r"]+", separator, cleaned)

    # 6. Обрезка граничных разделителей
    slug = slug.strip(separator)

    # 7. Ограничение длины
    if max_length is not None and max_length > 0:
        slug = slug[:max_length].rstrip(separator)

    return slug
