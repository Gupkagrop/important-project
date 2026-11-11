# Pocket Toolkit 🧰

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg)](https://github.com/Gupkagrop/important-project)
[![Tests Passing](https://img.shields.io/badge/tests-623%20passed-brightgreen.svg)](https://github.com/Gupkagrop/important-project)
[![Code style: strict](https://img.shields.io/badge/types-strict-green.svg)](https://docs.python.org/3/library/typing.html)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Модульная, высокопроизводительная библиотека легковесных структур данных, алгоритмов и прикладных утилит на чистом Python ($\ge 3.12$) без внешних зависимостей времени выполнения (Zero-Dependency).

Проект полностью завершен в соответствии с планом [ROADMAP.md](ROADMAP.md) (60 из 60 дней) и покрыт 623 модульными тестами.

---

## 🏛️ Архитектура пакета

Все компоненты библиотеки изолированы по тематическим субпакетам и экспортируются как через корень `pocket_toolkit`, так и через соответствующие подмодули:

```
src/pocket_toolkit/
├── structures/     # 12 структур данных (RingBuffer, LRU/LFU, Trie, RadixTree, кучи, BloomFilter, DisjointSet...)
├── algorithms/     # 12 алгоритмов (поиск, Левенштейн, RLE, KMP, Хаффман, Дейкстра, топосорт, интервалы...)
├── decorators/     # 6 декораторов отказоустойчивости и контроля (Retry, RateLimiter, LeakyBucket, CircuitBreaker...)
├── functional/     # 6 функциональных утилит (Pipe, Compose, Curry, LazyProperty, Profiler, Contracts...)
├── strings/        # 8 строковых утилит (Slugify, Case, Byte/Duration formatters, SemVer 2.0, Template, QueryParams)
├── data/           # 6 утилит работы с данными (Flatten/Unflatten, DeepMerge/Patch, DictDiff, MathAST, CSVStream)
├── cli/            # 4 консольные утилиты (ANSI Colors, Unicode Table, Progress Bar, Argument Parser)
└── system/         # 8 системных утилит (Env Parser, Glob, Temp, MemoryBuffer, AtomicWriter, Logger, EventBus, Diagnostics)
```

---

## 🚀 Примеры использования

### 1. Структуры данных и кэширование
```python
from pocket_toolkit import LRUCache, PriorityQueue, RingBuffer

# Кольцевой буфер фиксированного размера
ring = RingBuffer[int](capacity=3)
ring.extend([1, 2, 3, 4])
print(list(ring))  # [2, 3, 4]

# LRU кэш с константным временем доступа O(1)
cache = LRUCache[str, str](capacity=2)
cache.put("a", "alpha")
cache.put("b", "beta")
cache.get("a")     # обращение обновляет давность
cache.put("c", "gamma")  # вытесняет "b"
```

### 2. Отказоустойчивость и декораторы
```python
import time
from pocket_toolkit import CircuitBreaker, rate_limit, retry

# Повторы с экспоненциальной задержкой и джиттером
@retry(max_attempts=3, base_delay=0.5, backoff_factor=2.0)
def fetch_api() -> dict[str, str]:
    return {"status": "ok"}

# Ограничение частоты вызовов (Token Bucket)
@rate_limit(rate=10, capacity=10)
def send_message(user_id: int) -> None:
    pass

# Паттерн автоматического защитного выключателя
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)

@breaker
def external_call() -> str:
    return "response"
```

### 3. Строки, данные и безопасный калькулятор
```python
from pocket_toolkit import (
    evaluate_math,
    format_bytes,
    format_duration,
    render_template,
    SemanticVersion,
)

# Форматирование объемов и времени
print(format_bytes(1048576 * 2.5))  # "2.50 MiB"
print(format_duration(3665))        # "1ч 1м 5с"

# Безопасный парсер выражений на базе AST (без вызова eval)
res = evaluate_math("2 * (x + 5) ^ 2", variables={"x": 5})  # 200.0

# Семантическое версионирование SemVer 2.0
v1 = SemanticVersion.parse("1.2.3-alpha.1")
v2 = v1.bump_minor()
print(v2)  # "1.3.0"
print(v1 < v2)  # True

# Легковесный шаблонизатор
template = "Привет, {{ user.name }}! {% if is_admin %}Администратор{% endif %}"
output = render_template(template, {"user": {"name": "Денис"}, "is_admin": True})
```

### 4. Консоль и системные операции
```python
from pocket_toolkit import (
    EventBus,
    ProgressBar,
    Table,
    atomic_write,
    green,
    load_env,
)

# Отрисовка таблиц с рамками Unicode/Markdown
table = Table(headers=["Сервис", "Статус"], style="unicode")
table.add_row("API Gateway", green("ONLINE"))
print(table.render())

# Атомарная безопасная запись файлов
atomic_write("config.json", '{"mode": "production"}')

# Потокобезопасная шина событий
bus = EventBus()

@bus.on("user.created")
def notify(event: object) -> None:
    print(f"Новый пользователь: {event}")

bus.publish("user.created")
```

---

## 🛠️ Разработка и тестирование

### Требования
* Python $\ge 3.12$
* Менеджер пакетов [uv](https://docs.astral.sh/uv/)

### Установка и настройка окружения
```bash
# Клонирование репозитория
git clone https://github.com/Gupkagrop/important-project.git
cd important-project

# Синхронизация зависимостей окружения разработки
uv sync
```

### Запуск тестов и линтера
```bash
# Запуск полного набора модульных тестов (623 теста)
uv run pytest

# Проверка качества кода и типизации
uv run ruff check .

# Сборка пакета (Wheel и sdist)
uv build
```

---

## 📜 Лицензия

Проект распространяется под открытой лицензией MIT.
