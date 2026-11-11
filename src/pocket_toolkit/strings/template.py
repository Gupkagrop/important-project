"""Модуль легковесного текстового шаблонизатора (Simple Template Engine).

Предоставляет класс Template и функцию render_template для рендеринга строк с поддержкой
подстановки переменных `{{ var }}`, `{{ user.name }}`, условных выражений `{% if condition %} ... {% else %} ... {% endif %}`
и циклов `{% for item in items %} ... {% endfor %}`.
"""

import re
from collections.abc import Iterable, Mapping


# Исключения шаблонизатора
class TemplateError(Exception):
    """Базовое исключение шаблонизатора."""


class TemplateSyntaxError(TemplateError):
    """Синтаксическая ошибка в разметке шаблона."""


def _get_nested_value(context: Mapping[str, object], path: str) -> object:
    """Извлекает значение из словаря по составному точечному пути 'user.address.city'."""
    parts = path.strip().split(".")
    current: object = context

    for part in parts:
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return ""

    return current


def _evaluate_condition(condition_str: str, context: Mapping[str, object]) -> bool:
    """Вычисляет логическое значение условия (поддерживает 'not variable')."""
    cond = condition_str.strip()
    if not cond:
        return False

    is_inverted = cond.startswith("not ")
    var_name = cond[4:].strip() if is_inverted else cond

    val = _get_nested_value(context, var_name)
    truthiness = bool(val)

    return not truthiness if is_inverted else truthiness


def _render_variables(text: str, context: Mapping[str, object]) -> str:
    """Заменяет переменные вида {{ path.to.var }} на их строковые значения."""
    var_pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")

    def _replace_var(match: re.Match[str]) -> str:
        var_name = match.group(1)
        val = _get_nested_value(context, var_name)
        return "" if val is None else str(val)

    return var_pattern.sub(_replace_var, text)


def _render_conditionals(text: str, context: Mapping[str, object]) -> str:
    """Обрабатывает условные блоки {% if cond %} ... {% else %} ... {% endif %}."""
    if_pattern = re.compile(
        r"\{%\s*if\s+(?P<cond>[^%]+?)\s*%\}"
        r"(?P<then_branch>.*?)"
        r"(?:\{%\s*else\s*%\}(?P<else_branch>.*?))?"
        r"\{%\s*endif\s*%\}",
        re.DOTALL,
    )

    def _replace_if(match: re.Match[str]) -> str:
        condition_str = match.group("cond")
        then_content = match.group("then_branch")
        else_content = match.group("else_branch") or ""

        if _evaluate_condition(condition_str, context):
            return then_content
        return else_content

    return if_pattern.sub(_replace_if, text)


def _render_for_loops(text: str, context: Mapping[str, object]) -> str:
    """Обрабатывает циклы {% for item in items %} ... {% endfor %}."""
    for_pattern = re.compile(
        r"\{%\s*for\s+(?P<var>[a-zA-Z0-9_]+)\s+in\s+(?P<iter>[a-zA-Z0-9_.]+)\s*%\}"
        r"(?P<body>.*?)"
        r"\{%\s*endfor\s*%\}",
        re.DOTALL,
    )

    def _replace_for(match: re.Match[str]) -> str:
        var_name = match.group("var")
        iter_name = match.group("iter")
        body = match.group("body")

        iterable_obj = _get_nested_value(context, iter_name)
        if not isinstance(iterable_obj, Iterable) or isinstance(iterable_obj, (str, bytes)):
            return ""

        output_chunks: list[str] = []
        for item in iterable_obj:
            loop_context = dict(context)
            loop_context[var_name] = item
            output_chunks.append(_render_recursive(body, loop_context))

        return "".join(output_chunks)

    return for_pattern.sub(_replace_for, text)


def _validate_balanced_tags(text: str) -> None:
    """Проверяет баланс открывающих и закрывающих тегов шаблонизатора."""
    if_count = len(re.findall(r"\{%\s*if\b", text))
    endif_count = len(re.findall(r"\{%\s*endif\s*%\}", text))
    if if_count != endif_count:
        raise TemplateSyntaxError(f"Несбалансированные теги if ({if_count}) и endif ({endif_count})")

    for_count = len(re.findall(r"\{%\s*for\b", text))
    endfor_count = len(re.findall(r"\{%\s*endfor\s*%\}", text))
    if for_count != endfor_count:
        raise TemplateSyntaxError(f"Несбалансированные теги for ({for_count}) и endfor ({endfor_count})")


def _render_recursive(text: str, context: Mapping[str, object]) -> str:
    """Последовательно применяет трансформации циклов, условий и переменных."""
    with_for = _render_for_loops(text, context)
    with_if = _render_conditionals(with_for, context)
    return _render_variables(with_if, context)


class Template:
    """Шаблон текста для многократного рендеринга."""

    def __init__(self, template_str: str) -> None:
        """Инициализирует шаблон и валидирует синтаксис."""
        if not isinstance(template_str, str):
            raise TypeError(f"Текст шаблона должен быть строкой, получено: {type(template_str).__name__}")
        _validate_balanced_tags(template_str)
        self._raw_template: str = template_str

    def render(self, context: Mapping[str, object] | None = None, **kwargs: object) -> str:
        """Рендерит шаблон с переданным контекстом данных."""
        full_context: dict[str, object] = {}
        if context:
            full_context.update(context)
        if kwargs:
            full_context.update(kwargs)

        return _render_recursive(self._raw_template, full_context)


def render_template(
    template_str: str,
    context: Mapping[str, object] | None = None,
    **kwargs: object,
) -> str:
    """Удобная функция единовременного рендеринга шаблона.

    :param template_str: Строка шаблона.
    :param context: Словарь с переменными.
    :param kwargs: Дополнительные именованные переменные контекста.
    :return: Итоговая отрендеренная строка.
    """
    return Template(template_str).render(context=context, **kwargs)
