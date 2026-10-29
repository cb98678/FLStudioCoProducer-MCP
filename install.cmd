@echo off
rem Double-click this file (or run it from PowerShell) to install the co-producer. It runs install.ps1 next to it with
rem Windows PowerShell, whatever the script policy of this computer is. Options are passed on, for example: install.cmd -Models none
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" echo The installer stopped (code %CODE%). The lines above say why.
if not defined COPRODUCER_NO_PAUSE pause
exit /b %CODE%
