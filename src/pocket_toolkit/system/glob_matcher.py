"""Модуль сопоставления путей и файлов по glob-шаблонам (Glob & Path Matcher).

Предоставляет класс GlobPattern и функции glob_match, glob_filter, glob_to_regex
с поддержкой звездочек '*', '**', знака '?' и диапазонов '[a-z]' с нормализацией путей.
"""

import re
from collections.abc import Iterable


def _normalize_path(path: str) -> str:
    """Приводит путь к единообразному виду с прямыми слешами."""
    return path.replace("\\", "/").strip()


def glob_to_regex(pattern: str, case_sensitive: bool = True) -> re.Pattern[str]:
    """Транслирует glob-шаблон в скомпилированное регулярное выражение."""
    if not isinstance(pattern, str):
        raise TypeError(f"Шаблон должен быть строкой, получено: {type(pattern).__name__}")

    norm_pattern = _normalize_path(pattern)
    regex_parts: list[str] = ["^"]
    i = 0
    n = len(norm_pattern)

    while i < n:
        ch = norm_pattern[i]
        if ch == "*":
            # Проверяем двойную звездочку '**'
            if i + 1 < n and norm_pattern[i + 1] == "*":
                i += 2
                # Обработка сегментов вида '/**/'
                if i < n and norm_pattern[i] == "/":
                    i += 1
                    regex_parts.append("(?:.+/)?")
                else:
                    regex_parts.append(".*")
                continue
            regex_parts.append("[^/]*")
            i += 1
            continue

        if ch == "?":
            regex_parts.append("[^/]")
            i += 1
            continue

        if ch == "[":
            j = i + 1
            # Ищем закрывающую скобку
            while j < n and norm_pattern[j] != "]":
                j += 1
            if j < n:
                char_class = norm_pattern[i + 1 : j]
                if char_class.startswith("!"):
                    char_class = "^" + char_class[1:]
                regex_parts.append(f"[{char_class}]")
                i = j + 1
                continue

        regex_parts.append(re.escape(ch))
        i += 1

    regex_parts.append("$")
    regex_str = "".join(regex_parts)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(regex_str, flags)


class GlobPattern:
    """Скомпилированный glob-шаблон для эффективного сопоставления путей."""

    def __init__(self, pattern: str, case_sensitive: bool = True) -> None:
        """Инициализирует и компилирует glob-шаблон."""
        self.pattern: str = pattern
        self.case_sensitive: bool = case_sensitive
        self._regex: re.Pattern[str] = glob_to_regex(pattern, case_sensitive=case_sensitive)

    def match(self, path: str) -> bool:
        """Проверяет, соответствует ли путь текущему glob-шаблону."""
        if not isinstance(path, str):
            raise TypeError(f"Путь должен быть строкой, получено: {type(path).__name__}")
        norm = _normalize_path(path)
        return bool(self._regex.match(norm))

    def filter(self, paths: Iterable[str]) -> list[str]:
        """Фильтрует список путей, возвращая только совпавшие с шаблоном."""
        return [p for p in paths if self.match(p)]

    @property
    def regex(self) -> re.Pattern[str]:
        """Возвращает скомпилированное регулярное выражение."""
        return self._regex

    def __repr__(self) -> str:
        """Строковое представление шаблона."""
        return f"GlobPattern({self.pattern!r}, case_sensitive={self.case_sensitive})"


def glob_match(pattern: str, path: str, case_sensitive: bool = True) -> bool:
    """Проверяет соответствие пути glob-шаблону.

    :param pattern: Шаблон со звездочками '*', '**', '?' (например, 'src/**/*.py').
    :param path: Проверяемый путь (например, 'src/data/diff.py').
    :param case_sensitive: Учитывать ли регистр символов.
    :return: True, если путь соответствует шаблону.
    """
    return GlobPattern(pattern, case_sensitive=case_sensitive).match(path)


def glob_filter(pattern: str, paths: Iterable[str], case_sensitive: bool = True) -> list[str]:
    """Фильтрует пути по glob-шаблону.

    :param pattern: Шаблон сопоставления.
    :param paths: Коллекция путей.
    :param case_sensitive: Учитывать ли регистр.
    :return: Список отфильтрованных путей.
    """
    return GlobPattern(pattern, case_sensitive=case_sensitive).filter(paths)
