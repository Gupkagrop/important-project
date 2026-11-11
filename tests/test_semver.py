"""Модульные тесты для модуля семантического версионирования SemVer 2.0 (semver)."""

import pytest

from pocket_toolkit.strings.semver import SemanticVersion, is_valid_semver


def test_semver_parse_and_str() -> None:
    """Проверка парсинга и строкового форматирования SemVer."""
    v1 = SemanticVersion.parse("1.2.3")
    assert v1.major == 1
    assert v1.minor == 2
    assert v1.patch == 3
    assert v1.prerelease is None
    assert v1.build is None
    assert str(v1) == "1.2.3"
    assert not v1.is_prerelease

    v2 = SemanticVersion.parse("2.0.1-alpha.1+build.123")
    assert v2.major == 2
    assert v2.minor == 0
    assert v2.patch == 1
    assert v2.prerelease == "alpha.1"
    assert v2.build == "build.123"
    assert str(v2) == "2.0.1-alpha.1+build.123"
    assert v2.is_prerelease


def test_semver_precedence_and_comparisons() -> None:
    """Проверка порядка старшинства версий по спецификации SemVer 2.0."""
    v1 = SemanticVersion.parse("1.0.0-alpha")
    v2 = SemanticVersion.parse("1.0.0-alpha.1")
    v3 = SemanticVersion.parse("1.0.0-beta.2")
    v4 = SemanticVersion.parse("1.0.0-beta.11")
    v5 = SemanticVersion.parse("1.0.0-rc.1")
    v6 = SemanticVersion.parse("1.0.0")
    v7 = SemanticVersion.parse("1.0.1")
    v8 = SemanticVersion.parse("1.1.0")
    v9 = SemanticVersion.parse("2.0.0")

    assert v1 < v2 < v3 < v4 < v5 < v6 < v7 < v8 < v9
    assert v6 > v5
    assert v6 >= v5
    assert v1 <= v2


def test_semver_build_metadata_ignored_in_precedence() -> None:
    """Проверка, что метаданные сборки игнорируются при сравнении."""
    v1 = SemanticVersion.parse("1.0.0+20130313144700")
    v2 = SemanticVersion.parse("1.0.0+exp.sha.5114f85")
    assert v1 == v2
    assert not (v1 < v2)
    assert not (v1 > v2)


def test_semver_bumping() -> None:
    """Проверка инкрементов major, minor, patch и prerelease."""
    v = SemanticVersion.parse("1.2.3-alpha.1")

    assert str(v.bump_patch()) == "1.2.4"
    assert str(v.bump_minor()) == "1.3.0"
    assert str(v.bump_major()) == "2.0.0"

    v_pre = SemanticVersion.parse("1.0.0")
    bumped_pre1 = v_pre.bump_prerelease("beta")
    assert str(bumped_pre1) == "1.0.0-beta.1"

    bumped_pre2 = bumped_pre1.bump_prerelease("beta")
    assert str(bumped_pre2) == "1.0.0-beta.2"


def test_semver_validation_and_errors() -> None:
    """Проверка валидатора и обработки некорректных значений."""
    assert is_valid_semver("1.0.0")
    assert is_valid_semver("0.1.0-alpha+001")
    assert not is_valid_semver("1.0")
    assert not is_valid_semver("v1.0.0")
    assert not is_valid_semver("1.0.0.0")
    assert not is_valid_semver(123)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        SemanticVersion.parse(123)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        SemanticVersion.parse("not.a.version")

    with pytest.raises(ValueError):
        SemanticVersion(major=-1, minor=0, patch=0)
