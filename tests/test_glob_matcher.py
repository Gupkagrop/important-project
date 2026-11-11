"""Модульные тесты для модуля сопоставления путей по glob-шаблонам (glob_matcher)."""

import pytest

from pocket_toolkit.system.glob_matcher import (
    GlobPattern,
    glob_filter,
    glob_match,
    glob_to_regex,
)


def test_glob_match_star() -> None:
    """Проверка сопоставления одиночной звездочки '*' внутри сегмента пути."""
    assert glob_match("*.py", "main.py")
    assert glob_match("src/*.py", "src/utils.py")
    assert not glob_match("src/*.py", "src/sub/utils.py")
    assert glob_match("test_*.py", "test_app.py")


def test_glob_match_double_star() -> None:
    """Проверка сопоставления двойной звездочки '**' рекурсивно."""
    assert glob_match("**/*.py", "main.py")
    assert glob_match("**/*.py", "src/deep/nested/module.py")
    assert glob_match("src/**/test.py", "src/a/b/c/test.py")
    assert glob_match("docs/**", "docs/guide/index.html")


def test_glob_match_question_mark() -> None:
    """Проверка символа '?' (одиночный символ, кроме разделителя)."""
    assert glob_match("file?.txt", "file1.txt")
    assert glob_match("file?.txt", "fileA.txt")
    assert not glob_match("file?.txt", "file10.txt")
    assert not glob_match("a?b", "a/b")


def test_glob_match_character_classes() -> None:
    """Проверка диапазонов и множеств символов в квадратных скобках."""
    assert glob_match("log_[0-9].txt", "log_5.txt")
    assert not glob_match("log_[0-9].txt", "log_x.txt")
    assert glob_match("img.[png|jpg]", "img.p")
    assert glob_match("file[!0-9].txt", "fileA.txt")
    assert not glob_match("file[!0-9].txt", "file1.txt")


def test_path_normalization_windows_separators() -> None:
    """Проверка нормализации обратных слешей Windows."""
    assert glob_match("src/**/*.py", r"src\data\diff.py")
    assert glob_match(r"src\**\*.py", "src/data/diff.py")


def test_case_sensitivity() -> None:
    """Проверка флага учета регистра символов."""
    assert glob_match("*.PNG", "image.png", case_sensitive=False)
    assert not glob_match("*.PNG", "image.png", case_sensitive=True)


def test_glob_filter_and_pattern_class() -> None:
    """Проверка вспомогательной функции glob_filter и методов класса GlobPattern."""
    paths = [
        "src/app.py",
        "src/utils.py",
        "tests/test_app.py",
        "README.md",
    ]
    pattern = GlobPattern("src/*.py")
    assert repr(pattern) == "GlobPattern('src/*.py', case_sensitive=True)"

    filtered = pattern.filter(paths)
    assert filtered == ["src/app.py", "src/utils.py"]

    filtered_func = glob_filter("*.md", paths)
    assert filtered_func == ["README.md"]


def test_validation_errors() -> None:
    """Проверка валидации входных типов данных."""
    with pytest.raises(TypeError):
        glob_to_regex(123)  # type: ignore[arg-type]

    pattern = GlobPattern("*.py")
    with pytest.raises(TypeError):
        pattern.match(None)  # type: ignore[arg-type]
