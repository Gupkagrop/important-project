# ==============================================================================
# Скрипт автоматической настройки автозагрузки в Windows
# ==============================================================================
# Позволяет добавить запуск скрипта коммитов:
# 1. В папку автозагрузки текущего пользователя (shell:startup) — по умолчанию, без прав админа.
# 2. В Планировщик заданий Windows (требуются права администратора).
# ==============================================================================

[CmdletBinding()]
param(
    [ValidateSet('StartupFolder', 'TaskScheduler')]
    [string]$Target = 'StartupFolder'
)

$PSScriptRootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$VbsPath = Join-Path $PSScriptRootPath "run_silent.vbs"
$TaskName = "GitHubActivityDailyCommit"

Write-Host "Настройка автозапуска для скрипта: $VbsPath" -ForegroundColor Cyan

if ($Target -eq 'StartupFolder') {
    $startupFolder = [Environment]::GetFolderPath('Startup')
    $shortcutPath = Join-Path $startupFolder "GitHubActivityDailyCommit.lnk"

    Write-Host "Создание ярлыка в папке автозагрузки ($startupFolder)..." -ForegroundColor Yellow

    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "wscript.exe"
    $shortcut.Arguments = "`"$VbsPath`""
    $shortcut.WorkingDirectory = $PSScriptRootPath
    $shortcut.Description = "Ежедневная фиксация и отправка коммита на GitHub"
    $shortcut.Save()

    Write-Host "Ярлык успешно создан: $shortcutPath" -ForegroundColor Green
    Write-Host "Теперь скрипт будет автоматически запускаться при каждом включении компьютера!" -ForegroundColor Green
}
elseif ($Target -eq 'TaskScheduler') {
    Write-Host "Создание задачи в Планировщике заданий Windows..." -ForegroundColor Yellow

    try {
        $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsPath`""
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $trigger.Delay = "PT1M"
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Ежедневная фиксация и отправка коммита на GitHub при включении ПК" -Force -ErrorAction Stop | Out-Null

        Write-Host "Задача '$TaskName' успешно зарегистрирована в Планировщике заданий Windows!" -ForegroundColor Green
        Write-Host "Она будет запускаться через 1 минуту после каждого входа в систему." -ForegroundColor Green
    }
    catch {
        Write-Warning "Не удалось зарегистрировать задачу в Планировщике: $_"
        Write-Warning "Для регистрации задачи в Планировщике запустите консоль от имени Администратора или используйте опцию по умолчанию (-Target StartupFolder)."
    }
}
