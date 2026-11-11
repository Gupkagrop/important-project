"""Модульные тесты для модуля шаблонизатора (template)."""

import pytest

from pocket_toolkit.strings.template import (
    Template,
    TemplateSyntaxError,
    render_template,
)


def test_variable_interpolation() -> None:
    """Проверка подстановки переменных и вложенных путей."""
    tmpl = "Привет, {{ name }}! Твой город: {{ user.address.city }}."
    ctx = {
        "name": "Денис",
        "user": {
            "address": {
                "city": "Москва",
            }
        },
    }
    result = render_template(tmpl, ctx)
    assert result == "Привет, Денис! Твой город: Москва."


def test_missing_variables_render_empty() -> None:
    """Проверка рендеринга отсутствующих переменных в пустую строку."""
    assert render_template("Hello, {{ unknown }}!") == "Hello, !"
    assert render_template("Value: {{ user.none_field }}", {"user": {"none_field": None}}) == "Value: "


def test_conditionals_if_else() -> None:
    """Проверка работы условных блоков if и else."""
    tmpl = "{% if is_admin %}Панель администратора{% else %}Личный кабинет{% endif %}"
    assert render_template(tmpl, {"is_admin": True}) == "Панель администратора"
    assert render_template(tmpl, {"is_admin": False}) == "Личный кабинет"
    assert render_template(tmpl, {}) == "Личный кабинет"


def test_conditionals_not() -> None:
    """Проверка инвертированного условия 'not'."""
    tmpl = "{% if not is_guest %}Добро пожаловать обратно!{% endif %}"
    assert render_template(tmpl, {"is_guest": False}) == "Добро пожаловать обратно!"
    assert render_template(tmpl, {"is_guest": True}) == ""


def test_for_loops() -> None:
    """Проверка итерации по коллекциям."""
    tmpl = "Список:{% for item in items %} [{{ item }}]{% endfor %}"
    res = render_template(tmpl, {"items": ["яблоко", "банан", "груша"]})
    assert res == "Список: [яблоко] [банан] [груша]"


def test_nested_loops_and_conditionals() -> None:
    """Проверка комбинирования условий внутри циклов."""
    tmpl = (
        "{% for user in users %}"
        "{{ user.name }}: {% if user.active %}АКТИВЕН{% else %}ОТКЛЮЧЕН{% endif %}\n"
        "{% endfor %}"
    )
    users = [
        {"name": "Алиса", "active": True},
        {"name": "Боб", "active": False},
    ]
    res = render_template(tmpl, {"users": users})
    assert "Алиса: АКТИВЕН" in res
    assert "Боб: ОТКЛЮЧЕН" in res


def test_syntax_errors_unbalanced_tags() -> None:
    """Проверка обнаружения несбалансированных тегов."""
    with pytest.raises(TemplateSyntaxError, match="Несбалансированные теги if"):
        Template("{% if cond %}Текст без закрытия")

    with pytest.raises(TemplateSyntaxError, match="Несбалансированные теги for"):
        Template("{% for x in list %}Текст")


def test_template_instance_reuse() -> None:
    """Проверка повторного использования объекта Template."""
    t = Template("Пользователь: {{ name }} ({{ role }})")
    assert t.render(name="Иван", role="Разработчик") == "Пользователь: Иван (Разработчик)"
    assert t.render(name="Анна", role="Дизайнер") == "Пользователь: Анна (Дизайнер)"

    with pytest.raises(TypeError):
        Template(12345)  # type: ignore[arg-type]
