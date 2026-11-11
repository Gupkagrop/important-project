"""Модуль легковесного структурированного логгера (Structured Logger).

Предоставляет класс StructuredLogger с поддержкой уровней логирования (DEBUG..CRITICAL),
форматирования в JSON и цветной текст, контекстных полей (bind) и перенаправления потоков вывода.
"""

import json
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import IntEnum
from typing import TextIO

from pocket_toolkit.cli.colors import cyan, green, red, yellow


class LogLevel(IntEnum):
    """Уровни важности сообщений логирования."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def from_string(cls, name: str) -> "LogLevel":
        """Преобразует строку с именем уровня в enum LogLevel."""
        clean = name.strip().upper()
        if clean in cls.__members__:
            return cls.__members__[clean]
        raise ValueError(f"Неизвестный уровень логирования: {name!r}")


# Цветовое оформление уровней в консоли
_LEVEL_COLORIZERS = {
    LogLevel.DEBUG: cyan,
    LogLevel.INFO: green,
    LogLevel.WARNING: yellow,
    LogLevel.ERROR: red,
    LogLevel.CRITICAL: lambda t: red(f"[! {t} !]", bold=True),
}


class StructuredLogger:
    """Структурированный логгер сообщений с поддержкой JSON и контекста."""

    def __init__(
        self,
        name: str = "app",
        level: LogLevel = LogLevel.INFO,
        format_mode: str = "text",
        stream: TextIO | None = None,
        context: Mapping[str, object] | None = None,
    ) -> None:
        """Инициализирует структурированный логгер."""
        if format_mode not in ("text", "json"):
            raise ValueError(f"Неподдерживаемый формат: {format_mode!r}. Допустимы 'text' или 'json'")

        self.name: str = name
        self.level: LogLevel = level
        self.format_mode: str = format_mode
        self._stream: TextIO = stream if stream is not None else sys.stdout
        self._context: dict[str, object] = dict(context) if context else {}

    def bind(self, **kwargs: object) -> "StructuredLogger":
        """Создает дочерний логгер с добавленными контекстными полями."""
        new_ctx = dict(self._context)
        new_ctx.update(kwargs)
        return StructuredLogger(
            name=self.name,
            level=self.level,
            format_mode=self.format_mode,
            stream=self._stream,
            context=new_ctx,
        )

    def set_level(self, level: LogLevel | str) -> None:
        """Устанавливает минимальный порог уровня логирования."""
        if isinstance(level, str):
            self.level = LogLevel.from_string(level)
        else:
            self.level = level

    def _format_json(
        self,
        timestamp: str,
        level: LogLevel,
        message: str,
        extra: dict[str, object],
    ) -> str:
        """Сериализует запись лога в формат JSON."""
        payload: dict[str, object] = {
            "timestamp": timestamp,
            "level": level.name,
            "logger": self.name,
            "message": message,
        }
        if extra:
            payload["context"] = extra
        return json.dumps(payload, ensure_ascii=False)

    def _format_text(
        self,
        timestamp: str,
        level: LogLevel,
        message: str,
        extra: dict[str, object],
    ) -> str:
        """Форматирует запись лога в читаемую строку с цветным уровнем."""
        colorizer = _LEVEL_COLORIZERS.get(level, str)
        colored_level = colorizer(f"{level.name:8s}")
        base = f"[{timestamp}] [{colored_level}] [{self.name}] {message}"
        if not extra:
            return base

        extra_str = " ".join(f"{k}={v!r}" for k, v in sorted(extra.items()))
        return f"{base} | {extra_str}"

    def log(self, level: LogLevel, message: str, **kwargs: object) -> str:
        """Логирует сообщение с заданным уровнем и возвращает отформатированную строку."""
        if level < self.level:
            return ""

        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        extra: dict[str, object] = dict(self._context)
        extra.update(kwargs)

        if self.format_mode == "json":
            line = self._format_json(timestamp, level, message, extra)
        else:
            line = self._format_text(timestamp, level, message, extra)

        self._stream.write(f"{line}\n")
        self._stream.flush()
        return line

    def debug(self, message: str, **kwargs: object) -> str:
        """Логирует отладочное сообщение (DEBUG)."""
        return self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: object) -> str:
        """Логирует информационное сообщение (INFO)."""
        return self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: object) -> str:
        """Логирует предупреждение (WARNING)."""
        return self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: object) -> str:
        """Логирует ошибку (ERROR)."""
        return self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: object) -> str:
        """Логирует критическую ошибку (CRITICAL)."""
        return self.log(LogLevel.CRITICAL, message, **kwargs)
