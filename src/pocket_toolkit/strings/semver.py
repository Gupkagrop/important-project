"""Модуль парсинга, валидации и сравнения семантических версий (SemVer 2.0).

Предоставляет класс SemanticVersion с поддержкой спецификации Semantic Versioning 2.0.0:
мажорная, минорная и патч-версии, пре-релизы, метаданные сборки, корректное сравнение
приоритетов и методы инкремента версий.
"""

import re
from dataclasses import dataclass
from functools import total_ordering

# Официальное регулярное выражение SemVer 2.0
_SEMVER_REGEX: re.Pattern[str] = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def _compare_identifiers(id1: str, id2: str) -> int:
    """Сравнивает два отдельных идентификатора пре-релиза (числовой или буквенный)."""
    is_num1 = id1.isdigit()
    is_num2 = id2.isdigit()

    if is_num1 and is_num2:
        val1 = int(id1)
        val2 = int(id2)
        if val1 == val2:
            return 0
        return -1 if val1 < val2 else 1

    if is_num1 and not is_num2:
        return -1

    if not is_num1 and is_num2:
        return 1

    if id1 == id2:
        return 0
    return -1 if id1 < id2 else 1


def _compare_prereleases(pre1: str | None, pre2: str | None) -> int:
    """Сравнивает пре-релизные части согласно пункту 11 спецификации SemVer 2.0."""
    if pre1 is None and pre2 is None:
        return 0
    # Обычная версия имеет больший приоритет, чем пре-релизная
    if pre1 is None and pre2 is not None:
        return 1
    if pre1 is not None and pre2 is None:
        return -1

    parts1 = (pre1 or "").split(".")
    parts2 = (pre2 or "").split(".")

    for p1, p2 in zip(parts1, parts2, strict=False):
        cmp = _compare_identifiers(p1, p2)
        if cmp != 0:
            return cmp

    len1, len2 = len(parts1), len(parts2)
    if len1 == len2:
        return 0
    return -1 if len1 < len2 else 1


@total_ordering
@dataclass(frozen=True, slots=True)
class SemanticVersion:
    """Класс семантической версии согласно спецификации SemVer 2.0."""

    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    build: str | None = None

    def __post_init__(self) -> None:
        """Валидирует числовые компоненты версии."""
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Компоненты major, minor и patch должны быть неотрицательными")

    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """Парсит строку в объект SemanticVersion."""
        if not isinstance(version_str, str):
            raise TypeError(f"Ожидалась строка, получено: {type(version_str).__name__}")

        match = _SEMVER_REGEX.match(version_str.strip())
        if not match:
            raise ValueError(f"Некорректная SemVer 2.0 строка: {version_str!r}")

        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
            prerelease=match.group("prerelease"),
            build=match.group("build"),
        )

    @property
    def is_prerelease(self) -> bool:
        """Возвращает True, если текущая версия является пре-релизной."""
        return self.prerelease is not None

    def __str__(self) -> str:
        """Возвращает строковое представление версии."""
        res = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            res = f"{res}-{self.prerelease}"
        if self.build:
            res = f"{res}+{self.build}"
        return res

    def __eq__(self, other: object) -> bool:
        """Проверяет равенство версий по приоритету (build metadata игнорируется)."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented

        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return False

        return self.prerelease == other.prerelease

    def __lt__(self, other: object) -> bool:
        """Проверяет порядок приоритета версий по SemVer 2.0."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented

        self_core = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)

        if self_core != other_core:
            return self_core < other_core

        return _compare_prereleases(self.prerelease, other.prerelease) < 0

    def bump_major(self) -> "SemanticVersion":
        """Возвращает новую версию со сбросом minor и patch и инкрементом major."""
        return SemanticVersion(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> "SemanticVersion":
        """Возвращает новую версию со сбросом patch и инкрементом minor."""
        return SemanticVersion(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> "SemanticVersion":
        """Возвращает новую версию с инкрементом patch."""
        return SemanticVersion(major=self.major, minor=self.minor, patch=self.patch + 1)

    def bump_prerelease(self, tag: str = "alpha") -> "SemanticVersion":
        """Возвращает версию с инкрементом или добавлением пре-релиза."""
        if not self.prerelease:
            return SemanticVersion(
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                prerelease=f"{tag}.1",
            )

        parts = self.prerelease.split(".")
        if parts[-1].isdigit():
            next_num = int(parts[-1]) + 1
            new_pre = ".".join(parts[:-1] + [str(next_num)])
        else:
            new_pre = f"{self.prerelease}.1"

        return SemanticVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=new_pre,
        )


def is_valid_semver(version_str: str) -> bool:
    """Проверяет, соответствует ли строка формату SemVer 2.0."""
    if not isinstance(version_str, str):
        return False
    return bool(_SEMVER_REGEX.match(version_str.strip()))
