"""Модуль безопасной атомарной записи файлов (Atomic File Writer).

Предоставляет контекстный менеджер atomic_open, класс AtomicFileWriter и функцию atomic_write
для гарантированно безопасной записи файлов через временный файл в той же директории с атомарным переименованием (os.replace).
"""

import io
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class AtomicFileWriter:
    """Контекстный менеджер атомарной записи в файл через временный буфер."""

    def __init__(
        self,
        path: str | Path,
        mode: str = "w",
        encoding: str | None = None,
        overwrite: bool = True,
        make_parents: bool = True,
    ) -> None:
        """Инициализирует атомарный писатель файлов."""
        self.target_path: Path = Path(path).resolve()
        self.mode: str = mode
        self.encoding: str | None = encoding if "b" not in mode else None
        self.overwrite: bool = overwrite
        self.make_parents: bool = make_parents

        self._temp_path: Path | None = None
        self._file_obj: io.IOBase | None = None

    def __enter__(self) -> io.IOBase:
        """Создает временный файл в целевой папке и открывает его на запись."""
        if not self.overwrite and self.target_path.exists():
            raise FileExistsError(f"Целевой файл уже существует: {self.target_path}")

        parent_dir = self.target_path.parent
        if self.make_parents:
            parent_dir.mkdir(parents=True, exist_ok=True)

        prefix = f".{self.target_path.name}.tmp_"
        fd, temp_str = tempfile.mkstemp(prefix=prefix, dir=parent_dir)
        self._temp_path = Path(temp_str)

        open_mode = self.mode if self.mode.startswith("w") else "w" + self.mode.replace("w", "")
        self._file_obj = open(fd, mode=open_mode, encoding=self.encoding)
        return self._file_obj

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Закрывает и атомарно заменяет целевой файл либо удаляет временный при ошибке."""
        if self._file_obj is not None and not self._file_obj.closed:
            self._file_obj.flush()
            os.fsync(self._file_obj.fileno())
            self._file_obj.close()

        if exc_type is not None:
            # Произошла ошибка — удаляем временный файл
            if self._temp_path is not None and self._temp_path.exists():
                try:
                    self._temp_path.unlink()
                except OSError:
                    pass
            return

        # Успешное завершение — атомарная замена
        if self._temp_path is not None and self._temp_path.exists():
            os.replace(self._temp_path, self.target_path)


@contextmanager
def atomic_open(
    path: str | Path,
    mode: str = "w",
    encoding: str | None = None,
    overwrite: bool = True,
    make_parents: bool = True,
) -> Iterator[io.IOBase]:
    """Удобный контекстный менеджер безопасного открытия файла для атомарной записи."""
    writer = AtomicFileWriter(
        path=path,
        mode=mode,
        encoding=encoding,
        overwrite=overwrite,
        make_parents=make_parents,
    )
    with writer as f:
        yield f


def atomic_write(
    path: str | Path,
    content: str | bytes,
    encoding: str = "utf-8",
    overwrite: bool = True,
    make_parents: bool = True,
) -> Path:
    """Атомарно записывает текстовое или бинарное содержимое в файл.

    :param path: Путь к целевому файлу.
    :param content: Строка или байты для записи.
    :param encoding: Кодировка текста (если content — str).
    :param overwrite: Перезаписывать ли существующий файл.
    :param make_parents: Создавать ли недостающие родительские папки.
    :return: Объект Path созданного файла.
    """
    mode = "wb" if isinstance(content, bytes) else "w"
    enc = None if isinstance(content, bytes) else encoding

    with atomic_open(
        path=path,
        mode=mode,
        encoding=enc,
        overwrite=overwrite,
        make_parents=make_parents,
    ) as f:
        f.write(content)  # type: ignore[arg-type]

    return Path(path)
