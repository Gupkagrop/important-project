"""Модульные тесты для структурированного логгера (logger)."""

import io
import json

import pytest

from pocket_toolkit.system.logger import LogLevel, StructuredLogger


def test_logger_text_formatting_and_levels() -> None:
    """Проверка форматирования текста и фильтрации уровней."""
    stream = io.StringIO()
    logger = StructuredLogger(name="test_app", level=LogLevel.INFO, format_mode="text", stream=stream)

    # DEBUG не должен попасть в вывод, так как level=INFO
    debug_res = logger.debug("Отладочное сообщение")
    assert debug_res == ""
    assert stream.getvalue() == ""

    # INFO должно записаться
    info_res = logger.info("Информационное сообщение", user_id=42)
    assert "INFO" in info_res
    assert "[test_app] Информационное сообщение" in info_res
    assert "user_id=42" in info_res
    assert stream.getvalue().endswith("\n")


def test_logger_json_format() -> None:
    """Проверка вывода в формате JSON."""
    stream = io.StringIO()
    logger = StructuredLogger(name="json_service", format_mode="json", stream=stream)

    line = logger.warning("Внимание, высокая нагрузка", cpu_load=92.5)
    parsed = json.loads(line)

    assert parsed["level"] == "WARNING"
    assert parsed["logger"] == "json_service"
    assert parsed["message"] == "Внимание, высокая нагрузка"
    assert parsed["context"] == {"cpu_load": 92.5}
    assert "timestamp" in parsed


def test_logger_context_binding() -> None:
    """Проверка создания дочернего логгера через bind."""
    stream = io.StringIO()
    parent = StructuredLogger(name="api", format_mode="json", stream=stream)
    child = parent.bind(request_id="req-123", client_ip="127.0.0.1")

    child.error("Ошибка авторизации", status_code=401)
    record = json.loads(stream.getvalue().strip())

    assert record["context"]["request_id"] == "req-123"
    assert record["context"]["client_ip"] == "127.0.0.1"
    assert record["context"]["status_code"] == 401


def test_logger_set_level() -> None:
    """Проверка динамического изменения уровня логирования."""
    stream = io.StringIO()
    logger = StructuredLogger(level=LogLevel.ERROR, stream=stream)

    assert logger.info("Не видно") == ""

    logger.set_level("INFO")
    assert logger.level == LogLevel.INFO
    assert "Видно" in logger.info("Видно")

    with pytest.raises(ValueError, match="Неизвестный уровень"):
        logger.set_level("UNSUPPORTED")


def test_logger_validation_errors() -> None:
    """Проверка валидации параметров инициализации."""
    with pytest.raises(ValueError, match="Неподдерживаемый формат"):
        StructuredLogger(format_mode="yaml")
