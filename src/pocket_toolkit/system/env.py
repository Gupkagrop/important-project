"""Модуль парсинга .env файлов и типобезопасной конфигурации (Env & Config Parser).

Предоставляет класс EnvConfig и функции parse_env, load_env для чтения переменных окружения,
раскрытия интерполяций ${VAR}, поддержки кавычек, комментариев и строгой конвертации типов.
"""

import os
import re
from collections.abc import Mapping
from pathlib import Path

_TRUE_VALUES: frozenset[str] = frozenset({"1", "true", "yes", "on", "t", "y"})
_FALSE_VALUES: frozenset[str] = frozenset({"0", "false", "no", "off", "f", "n"})

_VAR_INTERPOLATION_REGEX: re.Pattern[str] = re.compile(r"\$\{([a-zA-Z0-9_]+)\}")


class EnvParseError(Exception):
    """Исключение при ошибке синтаксического разбора файла .env."""


def _strip_comment(line: str) -> str:
    """Удаляет комментарии (#), находящиеся вне кавычек."""
    in_quote: str | None = None
    chars: list[str] = []

    for ch in line:
        if ch in ('"', "'"):
            if in_quote == ch:
                in_quote = None
            elif in_quote is None:
                in_quote = ch
            chars.append(ch)
            continue

        if ch == "#" and in_quote is None:
            break

        chars.append(ch)

    return "".join(chars).strip()


def _unwrap_quoted_value(val: str) -> str:
    """Снимает одинарные или двойные кавычки со значения, если они присутствуют."""
    s = val.strip()
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        unquoted = s[1:-1]
        if s[0] == '"':
            unquoted = unquoted.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
        return unquoted
    return s


def _interpolate_variables(val: str, env_vars: Mapping[str, str]) -> str:
    """Раскрывает переменные вида ${VAR} на основе уже прочитанных значений."""
    def _sub(match: re.Match[str]) -> str:
        var_name = match.group(1)
        if var_name in env_vars:
            return env_vars[var_name]
        return os.environ.get(var_name, "")

    return _VAR_INTERPOLATION_REGEX.sub(_sub, val)


def parse_env(content: str, interpolate: bool = True) -> dict[str, str]:
    """Парсит текстовое содержимое .env в словарь строк.

    :param content: Сырой текст файла .env.
    :param interpolate: Раскрывать ли переменные ${VAR}.
    :return: Словарь прочитанных ключей и значений.
    """
    if not isinstance(content, str):
        raise TypeError(f"content должен быть строкой, получено: {type(content).__name__}")

    result: dict[str, str] = {}
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        cleaned = _strip_comment(line)
        if not cleaned:
            continue

        # Поддержка префикса 'export KEY=VAL'
        if cleaned.startswith("export "):
            cleaned = cleaned[7:].strip()

        if "=" not in cleaned:
            raise EnvParseError(f"Строка {line_num}: отсутствует знак '=' в строке: {line!r}")

        key_part, val_part = cleaned.split("=", 1)
        key = key_part.strip()
        if not key:
            raise EnvParseError(f"Строка {line_num}: пустое имя переменной")

        raw_val = _unwrap_quoted_value(val_part.strip())
        final_val = _interpolate_variables(raw_val, result) if interpolate else raw_val
        result[key] = final_val

    return result


class EnvConfig:
    """Типобезопасная обертка над словарем конфигурации переменных окружения."""

    def __init__(self, data: Mapping[str, str] | None = None) -> None:
        """Инициализирует хранилище конфигурации."""
        self._data: dict[str, str] = dict(data) if data is not None else {}

    def get(self, key: str, default: str | None = None) -> str | None:
        """Возвращает строковое значение или default."""
        return self._data.get(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        """Возвращает строковое значение."""
        val = self._data.get(key)
        return default if val is None else val

    def get_int(self, key: str, default: int = 0) -> int:
        """Возвращает целочисленное значение."""
        val = self._data.get(key)
        if val is None or val == "":
            return default
        try:
            return int(val)
        except ValueError as exc:
            raise ValueError(f"Невозможно привести {key}={val!r} к типу int") from exc

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Возвращает вещественное значение."""
        val = self._data.get(key)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except ValueError as exc:
            raise ValueError(f"Невозможно привести {key}={val!r} к типу float") from exc

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Возвращает булево значение."""
        val = self._data.get(key)
        if val is None or val == "":
            return default

        lower_val = val.strip().lower()
        if lower_val in _TRUE_VALUES:
            return True
        if lower_val in _FALSE_VALUES:
            return False

        raise ValueError(f"Невозможно привести {key}={val!r} к типу bool")

    def get_list(self, key: str, delimiter: str = ",", default: list[str] | None = None) -> list[str]:
        """Возвращает список строк, разделенных указанным разделителем."""
        val = self._data.get(key)
        if val is None or val == "":
            return [] if default is None else list(default)
        return [part.strip() for part in val.split(delimiter) if part.strip()]

    def as_dict(self) -> dict[str, str]:
        """Возвращает копию всех настроек в виде словаря."""
        return dict(self._data)

    def inject_to_environ(self, override: bool = False) -> None:
        """Внедряет прочитанные настройки в os.environ."""
        for k, v in self._data.items():
            if override or k not in os.environ:
                os.environ[k] = v


def load_env(
    path: str | Path,
    interpolate: bool = True,
    inject: bool = False,
    override: bool = False,
) -> EnvConfig:
    """Загружает файл конфигурации .env с диска.

    :param path: Путь к файлу .env.
    :param interpolate: Раскрывать ли переменные ${VAR}.
    :param inject: Внедрять ли переменные в os.environ.
    :param override: Перезаписывать ли существующие в os.environ переменные при inject.
    :return: Объект EnvConfig.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Файл окружения не найден: {path}")

    content = file_path.read_text(encoding="utf-8")
    parsed = parse_env(content, interpolate=interpolate)
    cfg = EnvConfig(parsed)

    if inject:
        cfg.inject_to_environ(override=override)

    return cfg
