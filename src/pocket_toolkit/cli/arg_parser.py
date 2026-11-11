"""Модуль минималистичного типобезопасного парсера аргументов командной строки (CLI Argument Parser).

Предоставляет класс ArgumentParser для декларативного описания позиционных аргументов,
флагов, именованных параметров с автоприведением типов, валидацией и генерацией справки.
"""

import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass


class ArgumentError(Exception):
    """Исключение при ошибке разбора аргументов командной строки."""


@dataclass(slots=True)
class _ArgumentSpec:
    """Спецификация одного аргумента."""

    name: str
    aliases: list[str]
    type_converter: Callable[[str], object]
    default: object
    required: bool
    help_text: str
    action: str
    is_positional: bool


class Namespace:
    """Контейнер для хранения распарсенных аргументов командной строки."""

    def __init__(self, **kwargs: object) -> None:
        """Инициализирует контейнер значениями."""
        self.__dict__.update(kwargs)

    def as_dict(self) -> dict[str, object]:
        """Возвращает значения аргументов в виде словаря."""
        return dict(self.__dict__)

    def __getattr__(self, name: str) -> object:
        """Возвращает значение по имени аргумента."""
        try:
            return self.__dict__[name]
        except KeyError as exc:
            raise AttributeError(f"Аргумент {name!r} не определен") from exc

    def __getitem__(self, name: str) -> object:
        """Словарный доступ к значениям."""
        return self.__dict__[name]

    def __contains__(self, name: str) -> bool:
        """Проверка наличия аргумента."""
        return name in self.__dict__

    def __repr__(self) -> str:
        """Строковое представление Namespace."""
        items = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Namespace({items})"


class ArgumentParser:
    """Минималистичный парсер аргументов командной строки."""

    def __init__(self, description: str = "", prog: str = "") -> None:
        """Инициализирует парсер с описанием программы."""
        self.prog: str = prog or (sys.argv[0] if sys.argv else "app")
        self.description: str = description
        self._specs: list[_ArgumentSpec] = []
        self._opt_map: dict[str, _ArgumentSpec] = {}

    def add_argument(
        self,
        name: str,
        *aliases: str,
        type: Callable[[str], object] = str,
        default: object = None,
        required: bool = False,
        help: str = "",
        action: str = "store",
    ) -> None:
        """Регистрирует аргумент в парсере."""
        if not name:
            raise ValueError("Имя аргумента не может быть пустым")

        is_pos = not name.startswith("-")
        clean_name = name.lstrip("-").replace("-", "_")
        all_aliases = [name] + list(aliases)

        spec = _ArgumentSpec(
            name=clean_name,
            aliases=all_aliases,
            type_converter=type,
            default=default,
            required=required,
            help_text=help,
            action=action,
            is_positional=is_pos,
        )
        self._specs.append(spec)

        for alias in all_aliases:
            if alias.startswith("-"):
                self._opt_map[alias] = spec

    def _parse_options(
        self,
        tokens: Sequence[str],
        result: dict[str, object],
    ) -> list[str]:
        """Разбирает флаги и именованные параметры, возвращая оставшиеся позиционные токены."""
        pos_tokens: list[str] = []
        idx = 0
        total = len(tokens)

        while idx < total:
            token = tokens[idx]
            if token == "--":
                pos_tokens.extend(tokens[idx + 1 :])
                break

            if token.startswith("--") and "=" in token:
                opt, raw_val = token.split("=", 1)
                self._apply_option_value(opt, raw_val, result)
                idx += 1
                continue

            if token in self._opt_map:
                spec = self._opt_map[token]
                idx = self._handle_opt_match(spec, token, tokens, idx, result)
                continue

            if token.startswith("-") and len(token) > 2 and not token.startswith("--"):
                # Пачка коротких флагов, например -abc
                for ch in token[1:]:
                    alias = f"-{ch}"
                    if alias not in self._opt_map:
                        raise ArgumentError(f"Неизвестный флаг: {alias}")
                    self._handle_opt_match(self._opt_map[alias], alias, tokens, idx, result)
                idx += 1
                continue

            if token.startswith("-") and token != "-":
                raise ArgumentError(f"Неизвестный параметр: {token}")

            pos_tokens.append(token)
            idx += 1

        return pos_tokens

    def _handle_opt_match(
        self,
        spec: _ArgumentSpec,
        token: str,
        tokens: Sequence[str],
        idx: int,
        result: dict[str, object],
    ) -> int:
        """Применяет найденную опцию."""
        if spec.action == "store_true":
            result[spec.name] = True
            return idx + 1
        if spec.action == "store_false":
            result[spec.name] = False
            return idx + 1

        if idx + 1 >= len(tokens):
            raise ArgumentError(f"Для параметра {token} ожидалось значение")

        val = tokens[idx + 1]
        self._apply_option_value(token, val, result)
        return idx + 2

    def _apply_option_value(self, opt: str, raw_val: str, result: dict[str, object]) -> None:
        """Конвертирует и записывает значение опции."""
        spec = self._opt_map.get(opt)
        if not spec:
            raise ArgumentError(f"Неизвестный параметр: {opt}")

        try:
            converted = spec.type_converter(raw_val)
        except Exception as exc:
            raise ArgumentError(f"Ошибка типа для {opt} ({raw_val!r}): {exc}") from exc

        if spec.action == "append":
            current_list = result.get(spec.name)
            if not isinstance(current_list, list):
                current_list = []
                result[spec.name] = current_list
            current_list.append(converted)
        else:
            result[spec.name] = converted

    def _apply_positionals(self, pos_tokens: list[str], result: dict[str, object]) -> None:
        """Сопоставляет позиционные токены со спецификациями."""
        pos_specs = [s for s in self._specs if s.is_positional]

        if len(pos_tokens) < len([s for s in pos_specs if s.required]):
            raise ArgumentError("Не переданы все обязательные позиционные аргументы")

        for idx, spec in enumerate(pos_specs):
            if idx < len(pos_tokens):
                raw = pos_tokens[idx]
                try:
                    result[spec.name] = spec.type_converter(raw)
                except Exception as exc:
                    raise ArgumentError(f"Неверный тип позиционного аргумента {spec.name}: {exc}") from exc
            elif spec.required:
                raise ArgumentError(f"Отсутствует обязательный позиционный аргумент: {spec.name}")

    def parse_args(self, args: Sequence[str] | None = None) -> Namespace:
        """Разбирает список строковых аргументов (по умолчанию sys.argv[1:])."""
        tokens = list(args) if args is not None else sys.argv[1:]
        result: dict[str, object] = {}

        # Инициализация дефолтных значений
        for spec in self._specs:
            if spec.action == "store_true":
                result[spec.name] = False if spec.default is None else spec.default
            elif spec.action == "store_false":
                result[spec.name] = True if spec.default is None else spec.default
            else:
                result[spec.name] = spec.default

        pos_tokens = self._parse_options(tokens, result)
        self._apply_positionals(pos_tokens, result)

        for spec in self._specs:
            if spec.required and result.get(spec.name) is None:
                raise ArgumentError(f"Обязательный параметр {spec.name} не передан")

        return Namespace(**result)

    def format_help(self) -> str:
        """Формирует текст справки по аргументам."""
        lines: list[str] = []
        if self.description:
            lines.append(f"{self.description}\n")

        lines.append(f"Использование: {self.prog} [ОПЦИИ]")
        lines.append("\nАргументы:")

        for spec in self._specs:
            aliases_str = ", ".join(spec.aliases)
            help_part = f" — {spec.help_text}" if spec.help_text else ""
            default_part = f" (по умолчанию: {spec.default})" if spec.default is not None else ""
            lines.append(f"  {aliases_str:20s}{help_part}{default_part}")

        return "\n".join(lines)
