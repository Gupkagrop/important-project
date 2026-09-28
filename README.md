# Pocket Toolkit 🧰

[![CI](https://github.com/Gupkagrop/important-project/actions/workflows/ci.yml/badge.svg)](https://github.com/Gupkagrop/important-project/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: strict](https://img.shields.io/badge/types-strict-green.svg)](https://docs.python.org/3/library/typing.html)

Модульная библиотека легковесных структур данных, алгоритмов и утилит на чистом Python без внешних зависимостей времени выполнения.

Проект развивается в инкрементальном режиме с ежедневным добавлением новых изолированных компонентов, строгой статической типизацией и 100% покрытием модульными тестами.

---

## Архитектура пакета

```
src/pocket_toolkit/
├── structures/     # Структуры данных (кольцевой буфер, LRU кэш, Trie, очереди)
├── algorithms/     # Алгоритмы (поиск, сжатие RLE, топологическая сортировка)
├── decorators/     # Декораторы (retry, rate limiter, throttle, circuit breaker)
├── data/           # Утилиты обработки данных (JSON flatten, diff, slugify)
└── cli/            # Консольные утилиты и форматирование вывода
```

Полный план ежедневного развития доступен в файле [ROADMAP.md](ROADMAP.md).

---

## Требования

- Python >= 3.12
- Менеджер пакетов [uv](https://docs.astral.sh/uv/)

---

## Установка и запуск тестов

Клонирование репозитория:
```bash
git clone https://github.com/Gupkagrop/important-project.git
cd important-project
```

Синхронизация зависимостей и запуск тестов через `uv`:
```bash
uv sync
uv run pytest
```
