"""Модуль контекстных менеджеров временных файлов и директорий (Temp Contexts).

Предоставляет контекстные менеджеры temp_dir, temp_file и класс TempWorkspace
для безопасного создания и гарантированной очистки временных ресурсов на диске.
"""

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Self


@contextmanager
def temp_dir(
    prefix: str = "pocket_tmp_",
    suffix: str = "",
    dir: str | Path | None = None,
    cleanup: bool = True,
) -> Iterator[Path]:
    """Контекстный менеджер создания изолированной временной директории.

    :param prefix: Префикс имени папки.
    :param suffix: Суффикс имени папки.
    :param dir: Родительская директория (None — системная временная папка).
    :param cleanup: Удалять ли директорию при выходе из контекста.
    :return: Объект Path созданной директории.
    """
    parent_dir = str(dir) if dir is not None else None
    created_path = Path(tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=parent_dir))
    try:
        yield created_path
    finally:
        if cleanup and created_path.exists():
            shutil.rmtree(created_path, ignore_errors=True)


@contextmanager
def temp_file(
    prefix: str = "pocket_tmp_",
    suffix: str = ".tmp",
    dir: str | Path | None = None,
    initial_data: str | bytes | None = None,
    cleanup: bool = True,
) -> Iterator[Path]:
    """Контекстный менеджер создания изолированного временного файла.

    :param prefix: Префикс имени файла.
    :param suffix: Суффикс имени файла (например, '.json', '.txt').
    :param dir: Родительская директория.
    :param initial_data: Начальные данные для записи в файл.
    :param cleanup: Удалять ли файл при выходе из контекста.
    :return: Объект Path созданного файла.
    """
    parent_dir = str(dir) if dir is not None else None
    fd, path_str = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=parent_dir)
    os.close(fd)
    file_path = Path(path_str)

    if initial_data is not None:
        if isinstance(initial_data, bytes):
            file_path.write_bytes(initial_data)
        else:
            file_path.write_text(str(initial_data), encoding="utf-8")

    try:
        yield file_path
    finally:
        if cleanup and file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass


class TempWorkspace:
    """Удобное временное изолированное рабочее пространство для тестов и генерации файлов."""

    def __init__(
        self,
        prefix: str = "pocket_ws_",
        dir: str | Path | None = None,
        cleanup: bool = True,
    ) -> None:
        """Инициализирует временную рабочую область."""
        self._prefix: str = prefix
        self._dir: str | Path | None = dir
        self._cleanup: bool = cleanup
        self._path: Path | None = None

    @property
    def root(self) -> Path:
        """Возвращает корневой путь к временной папке."""
        if self._path is None:
            raise RuntimeError("Временное пространство еще не инициализировано (используйте 'with')")
        return self._path

    def path(self, relative: str = "") -> Path:
        """Возвращает абсолютный путь к файлу внутри рабочей области."""
        if not relative:
            return self.root
        return self.root / relative

    def write_file(self, relative_path: str, content: str | bytes) -> Path:
        """Создает файл и все промежуточные родительские папки внутри рабочей области."""
        target = self.path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(str(content), encoding="utf-8")
        return target

    def read_file(self, relative_path: str) -> str:
        """Считывает текстовое содержимое файла из рабочей области."""
        return self.path(relative_path).read_text(encoding="utf-8")

    def __enter__(self) -> Self:
        """Создает директорию рабочей области при входе."""
        parent_dir = str(self._dir) if self._dir is not None else None
        self._path = Path(tempfile.mkdtemp(prefix=self._prefix, dir=parent_dir))
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Очищает созданную директорию."""
        if self._cleanup and self._path is not None and self._path.exists():
            shutil.rmtree(self._path, ignore_errors=True)
