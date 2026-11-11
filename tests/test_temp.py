"""Модульные тесты для модуля временных файлов и директорий (temp)."""

from pathlib import Path

import pytest

from pocket_toolkit.system.temp import (
    TempWorkspace,
    temp_dir,
    temp_file,
)


def test_temp_dir_lifecycle() -> None:
    """Проверка создания, использования и автоматической очистки временной папки."""
    captured_path: Path | None = None

    with temp_dir(prefix="test_dir_") as d:
        captured_path = d
        assert d.exists()
        assert d.is_dir()
        test_file = d / "data.txt"
        test_file.write_text("Hello temp", encoding="utf-8")
        assert test_file.exists()

    assert captured_path is not None
    assert not captured_path.exists()


def test_temp_dir_no_cleanup() -> None:
    """Проверка сохранения директории при cleanup=False."""
    with temp_dir(cleanup=False) as d:
        saved_path = d
        assert d.exists()

    try:
        assert saved_path.exists()
    finally:
        import shutil
        shutil.rmtree(saved_path, ignore_errors=True)


def test_temp_file_lifecycle_and_initial_data() -> None:
    """Проверка создания и автоудаления временного файла с начальными данными."""
    captured_path: Path | None = None

    with temp_file(suffix=".json", initial_data='{"status": "ok"}') as f:
        captured_path = f
        assert f.exists()
        assert f.is_file()
        assert f.suffix == ".json"
        assert f.read_text(encoding="utf-8") == '{"status": "ok"}'

    assert captured_path is not None
    assert not captured_path.exists()


def test_temp_workspace_helper() -> None:
    """Проверка удобных методов TempWorkspace."""
    ws = TempWorkspace(prefix="my_ws_")
    with pytest.raises(RuntimeError):
        _ = ws.root

    with ws:
        created_file = ws.write_file("nested/config.yaml", "env: test")
        assert created_file.exists()
        assert ws.read_file("nested/config.yaml") == "env: test"
        assert ws.path("nested/config.yaml").is_file()

    # Проверка очистки
    assert not ws.path().exists()
