# ==============================================================================
# Скрипт ежедневной автоматической фиксации и отправки коммитов на GitHub
# ==============================================================================
# Данный скрипт предназначен для запуска при включении компьютера (входе в Windows).
# Основные возможности:
# 1. Ожидание подключения к сети Интернет (проверка доступности GitHub до 90 сек).
# 2. Защита от повторных запусков в течение одного дня (параметр -Force для игнорирования).
# 3. Режим "Roadmap": запуск Gemini CLI для автономного выполнения очередного этапа
#    из ROADMAP.md по регламенту AGENTS.md, запуск pytest, оформление коммита и push.
# 4. Режим "Activity" (фоллбэк): запись отметки времени в ACTIVITY.md и push.
# 5. Ведение подробного журнала работы в logs/daily_commit.log.
# ==============================================================================

[CmdletBinding()]
param(
    [ValidateSet('Roadmap', 'Activity', 'Auto')]
    [string]$Mode = 'Auto',

    [switch]$Force
)

# Настройка кодировки UTF-8 для корректного отображения кириллицы
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение путей репозитория
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogsDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogsDir "daily_commit.log"
$ActivityFile = Join-Path $ProjectRoot "ACTIVITY.md"

if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('INFO', 'WARN', 'ERROR', 'SUCCESS')]
        [string]$Level = 'INFO'
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry -Encoding UTF8
}

Write-Log "=== Запуск скрипта автоматического коммита ===" "INFO"
Write-Log "Рабочая директория: $ProjectRoot" "INFO"

# 1. Ожидание доступности сети Интернет и GitHub
Write-Log "Проверка сетевого соединения с github.com..." "INFO"
$networkReady = $false
$maxRetries = 18 # 18 попыток по 5 секунд = 90 секунд ожидания
$retryCount = 0

while (-not $networkReady -and $retryCount -lt $maxRetries) {
    try {
        $tcpCheck = Test-NetConnection -ComputerName "github.com" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($tcpCheck) {
            $networkReady = $true
            Write-Log "Соединение с github.com успешно установлено." "SUCCESS"
            break
        }
    }
    catch {
        # Игнорируем сетевые сбои в процессе инициализации сетевых интерфейсов
    }
    $retryCount++
    Write-Log "Ожидание подключения к сети... (попытка $retryCount из $maxRetries)" "WARN"
    Start-Sleep -Seconds 5
}

if (-not $networkReady) {
    Write-Log "Не удалось установить соединение с github.com за 90 секунд. Прерывание работы." "ERROR"
    exit 1
}

# Переход в корень репозитория
Set-Location -Path $ProjectRoot

# Убеждаемся, что локальный Git использует openssl для стабильной работы TLS
git config --local http.sslBackend openssl | Out-Null

# 2. Проверка даты последнего коммита (защита от повторных коммитов за один день)
$todayStr = (Get-Date).ToString("yyyy-MM-dd")
$lastCommitDate = (git log -1 --format="%ad" --date=short 2>$null).Trim()

Write-Log "Дата последнего коммита в репозитории: '$lastCommitDate'. Текущая дата: '$todayStr'." "INFO"

if (($lastCommitDate -eq $todayStr) -and (-not $Force)) {
    Write-Log "Коммит за сегодня ($todayStr) уже существует. Пропуск выполнения. (Используйте флаг -Force для повторного запуска)." "INFO"
    exit 0
}

# 3. Функция выполнения легковесной фиксации активности (Heartbeat)
function Invoke-ActivityPulse {
    Write-Log "Выполнение легковесной фиксации активности (режим Activity)..." "INFO"
    $currentTime = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

    # Инициализация файла активности при его отсутствии
    if (-not (Test-Path $ActivityFile)) {
        $header = "# Журнал активности проекта`r`n`r`nАвтоматический реестр ежедневной активности и запусков системы.`r`n`r`n| Дата и время | Статус | Примечание |`r`n|---|---|---|"
        Set-Content -Path $ActivityFile -Value $header -Encoding UTF8
    }

    # Добавление строки в журнал активности
    $tableRow = "| $currentTime | Успешно | Автоматическая фиксация активности системы при запуске |"
    Add-Content -Path $ActivityFile -Value $tableRow -Encoding UTF8

    git add $ActivityFile
    $commitMsg = "chore(activity): автоматическая фиксация активности от $todayStr"
    git commit -m $commitMsg

    Write-Log "Отправка изменений в удаленный репозиторий Gupkagrop main..." "INFO"
    $pushOutput = git push Gupkagrop main 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Изменения успешно отправлены на GitHub." "SUCCESS"
        return $true
    }
    else {
        Write-Log "Ошибка при отправке git push: $pushOutput" "ERROR"
        return $false
    }
}

# 4. Функция выполнения задачи через Gemini CLI по ROADMAP.md
function Invoke-GeminiRoadmap {
    Write-Log "Поиск установленного Gemini CLI..." "INFO"
    $geminiCmd = Get-Command "gemini.cmd" -ErrorAction SilentlyContinue

    if (-not $geminiCmd) {
        Write-Log "Команда gemini.cmd не найдена в системных путях PATH." "WARN"
        return $false
    }

    Write-Log "Запуск Gemini CLI для реализации очередного дня по ROADMAP.md..." "INFO"
    $prompt = "Прочитай AGENTS.md и ROADMAP.md. Реализуй следующую незавершенную задачу [ ] строго по регламенту Daily Increment Workflow. Создай код в src/pocket_toolkit/, экспорты в __init__.py, модульные тесты в tests/, выполни проверку через 'uv run pytest', отметь выполненную задачу [x] в ROADMAP.md, сделай git коммит на русском языке и отправь изменения командой 'git push Gupkagrop main'."

    $geminiLog = Join-Path $LogsDir "gemini_last_run.log"
    $processArgs = @(
        "--yolo",
        "-p",
        $prompt
    )

    try {
        $proc = Start-Process -FilePath "gemini.cmd" -ArgumentList $processArgs -WorkingDirectory $ProjectRoot -NoNewWindow -PassThru -RedirectStandardOutput $geminiLog -RedirectStandardError (Join-Path $LogsDir "gemini_error.log")
        $proc.WaitForExit()

        Write-Log "Gemini CLI завершил работу с кодом возврата $($proc.ExitCode)." "INFO"

        # Проверяем, появился ли новый коммит за сегодня
        $newCommitDate = (git log -1 --format="%ad" --date=short 2>$null).Trim()
        if ($newCommitDate -eq $todayStr) {
            Write-Log "Gemini CLI успешно создал и отправил коммит за $todayStr." "SUCCESS"
            return $true
        }
        else {
            Write-Log "Коммит не был создан процессом Gemini CLI." "WARN"
            return $false
        }
    }
    catch {
        Write-Log "Исключение при вызове Gemini CLI: $_" "ERROR"
        return $false
    }
}

# 5. Выполнение в зависимости от выбранного режима
$executionSuccess = $false

if ($Mode -eq 'Roadmap') {
    $executionSuccess = Invoke-GeminiRoadmap
}
elseif ($Mode -eq 'Activity') {
    $executionSuccess = Invoke-ActivityPulse
}
elseif ($Mode -eq 'Auto') {
    Write-Log "Режим Auto: попытка выполнения задачи по ROADMAP.md через Gemini CLI..." "INFO"
    $roadmapResult = Invoke-GeminiRoadmap
    if ($roadmapResult) {
        $executionSuccess = $true
    }
    else {
        Write-Log "Переход на резервный режим фиксации активности (Activity Pulse)..." "WARN"
        $executionSuccess = Invoke-ActivityPulse
    }
}

if ($executionSuccess) {
    Write-Log "=== Скрипт успешно завершил работу ===" "SUCCESS"
    exit 0
}
else {
    Write-Log "=== Скрипт завершился с ошибками ===" "ERROR"
    exit 1
}
