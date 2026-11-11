"""Модульные тесты для модуля парсера .env файлов и конфигурации (env)."""

from pathlib import Path

import pytest

from pocket_toolkit.system.env import (
    EnvConfig,
    EnvParseError,
    load_env,
    parse_env,
)


def test_parse_env_basic_and_quotes() -> None:
    """Проверка базового парсинга строк, кавычек и комментариев."""
    raw = """
    # Настройки базы данных
    DB_HOST=localhost
    DB_PORT=5432
    export DB_NAME="my_database"
    SECRET_KEY='single-quoted-secret' # встроенный комментарий
    EMPTY_VAL=
    """
    res = parse_env(raw)
    assert res["DB_HOST"] == "localhost"
    assert res["DB_PORT"] == "5432"
    assert res["DB_NAME"] == "my_database"
    assert res["SECRET_KEY"] == "single-quoted-secret"
    assert res["EMPTY_VAL"] == ""


def test_parse_env_interpolation() -> None:
    """Проверка подстановки переменных ${VAR}."""
    raw = """
    BASE_URL=https://api.example.com
    USERS_URL=${BASE_URL}/v1/users
    """
    res = parse_env(raw)
    assert res["USERS_URL"] == "https://api.example.com/v1/users"


def test_env_config_typed_getters() -> None:
    """Проверка строгой типизации методов EnvConfig."""
    data = {
        "DEBUG": "true",
        "PORT": "8080",
        "TIMEOUT": "2.5",
        "TAGS": "python, cli, toolkit",
        "NAME": "Pocket",
    }
    cfg = EnvConfig(data)

    assert cfg.get_bool("DEBUG") is True
    assert cfg.get_bool("UNKNOWN", default=False) is False
    assert cfg.get_int("PORT") == 8080
    assert cfg.get_float("TIMEOUT") == 2.5
    assert cfg.get_str("NAME") == "Pocket"
    assert cfg.get_list("TAGS") == ["python", "cli", "toolkit"]


def test_env_config_type_errors() -> None:
    """Проверка обработки некорректных типов значений в EnvConfig."""
    cfg = EnvConfig({"BAD_INT": "not_int", "BAD_BOOL": "maybe"})

    with pytest.raises(ValueError, match="Невозможно привести BAD_INT"):
        cfg.get_int("BAD_INT")

    with pytest.raises(ValueError, match="Невозможно привести BAD_BOOL"):
        cfg.get_bool("BAD_BOOL")


def test_load_env_file(tmp_path: Path) -> None:
    """Проверка загрузки файла .env с диска и внедрения в environ."""
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=testing\nAPP_PORT=3000\n", encoding="utf-8")

    cfg = load_env(env_file, inject=False)
    assert cfg.get_str("APP_ENV") == "testing"
    assert cfg.get_int("APP_PORT") == 3000

    with pytest.raises(FileNotFoundError):
        load_env(tmp_path / "nonexistent.env")


def test_parse_env_syntax_errors() -> None:
    """Проверка синтаксических ошибок в файле конфигурации."""
    with pytest.raises(EnvParseError, match="отсутствует знак '='"):
        parse_env("INVALID_LINE_WITHOUT_EQUALS")

    with pytest.raises(EnvParseError, match="пустое имя переменной"):
        parse_env("=value_without_key")
