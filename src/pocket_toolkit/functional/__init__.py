"""Пакет функциональных утилит и комбинаторов Pocket Toolkit."""

from pocket_toolkit.functional.compose import (
    Pipeline,
    compose,
    compose_left,
    pipe,
)

__all__: list[str] = [
    "Pipeline",
    "compose",
    "compose_left",
    "pipe",
]
