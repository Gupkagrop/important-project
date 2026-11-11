"""Модульные тесты для модуля атомарной записи файлов (atomic)."""

from pathlib import Path

import pytest

from pocket_toolkit.system.atomic import (
    AtomicFileWriter,
    atomic_open,
    atomic_write,
)


def test_atomic_write_text_and_binary(tmp_path: Path) -> None:
    """Проверка успешной атомарной записи текста и байтов."""
    target_txt = tmp_path / "test.txt"
    atomic_write(target_txt, "Hello Atomic World!")
    assert target_txt.read_text(encoding="utf-8") == "Hello Atomic World!"

    target_bin = tmp_path / "nested" / "test.bin"
    atomic_write(target_bin, b"\x00\x01\x02\x03", make_parents=True)
    assert target_bin.read_bytes() == b"\x00\x01\x02\x03"


def test_atomic_open_rollback_on_error(tmp_path: Path) -> None:
    """Проверка, что при ошибке исходный файл сохраняется неизменным, а временный удаляется."""
    target = tmp_path / "original.txt"
    target.write_text("Original State", encoding="utf-8")

    with (
        pytest.raises(RuntimeError, match="Имитация сбоя в процессе записи"),
        atomic_open(target, mode="w") as f,
    ):
        f.write("Corrupted State")
        raise RuntimeError("Имитация сбоя в процессе записи")

    # Исходный файл остался в оригинальном состоянии!
    assert target.read_text(encoding="utf-8") == "Original State"

    # Во временной папке не осталось временных файлов
    temp_files = list(tmp_path.glob(".*.tmp_*"))
    assert len(temp_files) == 0


def test_atomic_open_no_overwrite(tmp_path: Path) -> None:
    """Проверка защиты от перезаписи при overwrite=False."""
    target = tmp_path / "locked.txt"
    target.write_text("Locked", encoding="utf-8")

    with (
        pytest.raises(FileExistsError, match="Целевой файл уже существует"),
        atomic_open(target, mode="w", overwrite=False) as f,
    ):
        f.write("New data")


def test_atomic_file_writer_class(tmp_path: Path) -> None:
    """Проверка использования класса AtomicFileWriter напрямую."""
    target = tmp_path / "writer_test.txt"
    writer = AtomicFileWriter(target)
    with writer as f:
        f.write("Written by AtomicFileWriter")

    assert target.read_text() == "Written by AtomicFileWriter"
