# Скрипты автоматизации коммитов и автозапуска

Данный каталог содержит комплекс решений для автоматического выполнения коммитов и отправки изменений на GitHub при включении компьютера.

## Состав компонентов

1. **[`daily_commit.ps1`](file:///c:/Users/denis/Documents/antigravity/GitHub%20Activity/scripts/daily_commit.ps1)**  
   Основной сценарий автоматизации.
   - **Ожидание сети:** Опрашивает `github.com` до 90 секунд (на случай долгого подключения Wi-Fi/VPN при старте Windows).
   - **Защита от дублей:** Проверяет дату последнего коммита. Если коммит за сегодня уже существует, повторный запуск пропускается (для принудительного перезапуска передается флаг `-Force`).
   - **Режим `Roadmap`:** Вызывает автономный `Gemini CLI` (`gemini.cmd --yolo`) для реализации следующего незавершенного этапа из `ROADMAP.md` по правилам `AGENTS.md`, прогона `uv run pytest`, оформления коммита и отправки `git push Gupkagrop main`.
   - **Режим `Activity`:** Легковесная фиксация активности системы: добавляет отметку времени в `ACTIVITY.md` и отправляет коммит на GitHub без обращения к нейросети.
   - **Режим `Auto` (по умолчанию):** Сначала пытается запустить задачу через `Gemini CLI`, а при отсутствии ответа или сбое переключается на резервный режим `Activity`.
   - **Логирование:** Все действия с временными метками записываются в `logs/daily_commit.log`.

2. **[`run_silent.vbs`](file:///c:/Users/denis/Documents/antigravity/GitHub%20Activity/scripts/run_silent.vbs)**  
   VBScript-лаунчер для скрытого запуска `daily_commit.ps1` в фоновом режиме (без всплывающего окна терминала/консоли).

3. **[`setup_startup.ps1`](file:///c:/Users/denis/Documents/antigravity/GitHub%20Activity/scripts/setup_startup.ps1)**  
   Скрипт быстрой привязки скрипта к автозагрузке Windows.
   - По умолчанию создает ярлык в папке автозагрузки текущего пользователя (`shell:startup`) — не требует прав администратора.
   - Опционально может зарегистрировать задачу в Планировщике заданий Windows (`Task Scheduler`) с отложенным стартом (`-Target TaskScheduler`).

## Ручной запуск и тестирование

```powershell
# Запуск в штатном режиме (проверит коммит за сегодня, при необходимости выполнит)
powershell -ExecutionPolicy Bypass -File "scripts/daily_commit.ps1"

# Принудительный запуск (даже если сегодня коммит уже был)
powershell -ExecutionPolicy Bypass -File "scripts/daily_commit.ps1" -Force

# Принудительный запуск только в легковесном режиме фиксации активности
powershell -ExecutionPolicy Bypass -File "scripts/daily_commit.ps1" -Mode Activity -Force
```
