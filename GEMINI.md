> [!NOTE]
> Данный файл определяет архитектурный контракт, правила оформления кода, стандарты коммитов и регламент ежедневного инкрементального развития библиотеки `pocket-toolkit`. Все агенты обязаны следовать инструкциям при добавлении новых компонентов.

# Pocket Toolkit — Operational Contract & Guidelines

## 1. Project Overview
`pocket-toolkit` is a modular, zero-dependency Python utility and data structure library built for modern Python (>=3.12).
The project evolves through daily, bite-sized, atomic feature increments tracked in [ROADMAP.md](file:///c:/Users/denis/Documents/antigravity/GitHub%20Activity/ROADMAP.md).

## 2. Tech Stack & Environment
- **Runtime:** Python >= 3.12
- **Package Manager:** `uv`
- **Testing:** `pytest`
- **Git Remote:** `Gupkagrop` (`https://github.com/Gupkagrop/important-project.git`)
- **Main Branch:** `main`

## 3. Code Standards & Architecture
- **Language & Comments:** All code symbols (classes, functions, variables, files) must be in English. All docstrings, inline comments, and annotations MUST be in Russian.
- **Strict Typing:** Every function signature and class attribute must include explicit type hints (`typing.Any` is strictly prohibited). Use generics (`TypeVar`, `Generic`) where appropriate.
- **Complexity & Flat Flow:** Adhere to early returns (maximum 3 levels of nesting).
- **Single Responsibility:** Functions must stay within 30-40 lines; break down complex logic into private helper functions (`_helper_func`).
- **Zero Placeholders:** Never commit mocks, placeholders, or unfinished `TODO` markers. Every added component must be 100% production-ready.

## 4. Daily Increment Workflow (Automation Protocol)
On each automated daily run:
1. Open [ROADMAP.md](file:///c:/Users/denis/Documents/antigravity/GitHub%20Activity/ROADMAP.md) and pick the next uncompleted task `[ ]`.
2. Implement the designated module inside `src/pocket_toolkit/<category>/<module_name>.py`.
3. Export public symbols in `src/pocket_toolkit/__init__.py` and the respective subpackage `__init__.py`.
4. Create comprehensive unit tests in `tests/test_<module_name>.py` covering standard cases, edge cases, and error handling.
5. Run test suite: `uv run pytest`.
6. Mark the task as done `[x]` in `ROADMAP.md`.
7. Commit changes strictly in Russian using Conventional Commits format:
   - Example: `feat(structures): реализовать кольцевой буфер и модульные тесты`
8. Push commits to GitHub: `git push Gupkagrop main`.
