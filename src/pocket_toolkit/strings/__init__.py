"""Пакет строковых утилит и текстовых трансформаций Pocket Toolkit."""

from pocket_toolkit.strings.bytes import (
    IEC_UNITS,
    SI_UNITS,
    format_bytes,
    parse_bytes,
)
from pocket_toolkit.strings.case import (
    split_words,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_screaming_snake_case,
    to_snake_case,
    to_title_case,
)
from pocket_toolkit.strings.duration import (
    format_duration,
    parse_duration,
)
from pocket_toolkit.strings.semver import (
    SemanticVersion,
    is_valid_semver,
)
from pocket_toolkit.strings.slugify import (
    slugify,
    transliterate,
)
from pocket_toolkit.strings.template import (
    Template,
    TemplateError,
    TemplateSyntaxError,
    render_template,
)

__all__: list[str] = [
    "IEC_UNITS",
    "SI_UNITS",
    "SemanticVersion",
    "Template",
    "TemplateError",
    "TemplateSyntaxError",
    "format_bytes",
    "format_duration",
    "is_valid_semver",
    "parse_bytes",
    "parse_duration",
    "render_template",
    "slugify",
    "split_words",
    "to_camel_case",
    "to_kebab_case",
    "to_pascal_case",
    "to_screaming_snake_case",
    "to_snake_case",
    "to_title_case",
    "transliterate",
]
