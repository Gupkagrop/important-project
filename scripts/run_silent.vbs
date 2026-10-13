' ==============================================================================
' Лаунчер для скрытого запуска daily_commit.ps1 без отображения окна консоли
' ==============================================================================
Dim WshShell, fso, scriptDir, psScript, cmdLine

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Определение путей относительно текущего расположения VBS-файла
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "daily_commit.ps1")

' Запуск PowerShell со стилем окна Hidden и обходом ExecutionPolicy
cmdLine = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & psScript & """"
WshShell.Run cmdLine, 0, False
