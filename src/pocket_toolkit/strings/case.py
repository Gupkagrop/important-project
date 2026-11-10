"""Модуль преобразования регистров строк (String Case Converters).

Предоставляет функции конвертации идентификаторов и строк между различными стилями именования:
`snake_case`, `camelCase`, `PascalCase`, `kebab-case`, `SCREAMING_SNAKE_CASE` и `Title Case`
с корректной обработкой аббревиатур (HTTP, API, JSON) и чисел.
"""

import re


def split_words(text: str) -> list[str]:
    """Разбивает строку на составляющие слова с учетом camelCase, аббревиатур и разделителей.

    Примеры:
    - 'userProfileId' -> ['user', 'Profile', 'Id']
    - 'getHTTPResponseCode' -> ['get', 'HTTP', 'Response', 'Code']
    - 'kebab-to_snake case' -> ['kebab', 'to', 'snake', 'case']

    :param text: Исходная строка.
    :return: Список распознанных слов.
    """
    if not text:
        return []

    # 1. Заменяем явные разделители (тире, подчеркивания, пробелы, точки) на одиночный пробел
    s = re.sub(r"[\s_\-./\\]+", " ", text).strip()
    if not s:
        return []

    # 2. Регулярное выражение для разделения camelCase и аббревиатур:
    # - [A-Z]+(?=[A-Z][a-z]|\b) находит аббревиатуры (например, 'HTTP' в 'HTTPResponse')
    # - [A-Z][a-z]+ находит слова с заглавной буквы
    # - [a-z]+ находит слова в нижнем регистре
    # - [0-9]+ находит числовые блоки
    pattern = r"[A-Z]+(?=[A-Z][a-z]|\b|\d)|[A-Z]?[a-z]+|[A-Z]|\d+"
    words = re.findall(pattern, s)

    return words


def to_snake_case(text: str) -> str:
    """Преобразует строку в стиль snake_case.

    :param text: Исходная строка.
    :return: Строка вида 'lower_case_words'.
    """
    words = split_words(text)
    return "_".join(w.lower() for w in words)


def to_camel_case(text: str) -> str:
    """Преобразует строку в стиль camelCase.

    :param text: Исходная строка.
    :return: Строка вида 'lowerCamelCase'.
    """
    words = split_words(text)
    if not words:
        return ""
    first = words[0].lower()
    rest = [w.capitalize() for w in words[1:]]
    return first + "".join(rest)


def to_pascal_case(text: str) -> str:
    """Преобразует строку в стиль PascalCase (UpperCamelCase).

    :param text: Исходная строка.
    :return: Строка вида 'UpperPascalCase'.
    """
    words = split_words(text)
    return "".join(w.capitalize() for w in words)


def to_kebab_case(text: str) -> str:
    """Преобразует строку в стиль kebab-case.

    :param text: Исходная строка.
    :return: Строка вида 'kebab-case-words'.
    """
    words = split_words(text)
    return "-".join(w.lower() for w in words)


def to_screaming_snake_case(text: str) -> str:
    """Преобразует строку в стиль констант SCREAMING_SNAKE_CASE.

    :param text: Исходная строка.
    :return: Строка вида 'UPPER_SNAKE_CASE'.
    """
    words = split_words(text)
    return "_".join(w.upper() for w in words)


def to_title_case(text: str) -> str:
    """Преобразует строку в стиль заголовка Title Case (слова через пробел с заглавной).

    :param text: Исходная строка.
    :return: Строка вида 'Title Case Words'.
    """
    words = split_words(text)
    return " ".join(w.capitalize() for w in words)
