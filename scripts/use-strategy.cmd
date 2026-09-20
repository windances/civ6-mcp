@echo off
REM Wrapper for use-strategy.ps1, so the machine execution policy does not block it.
REM
REM Usage (from the project root, in cmd, PowerShell or Git Bash):
REM   scripts\use-strategy.cmd                  list presets, show which is active
REM   scripts\use-strategy.cmd expansion        apply a preset (live, next turn)
REM   scripts\use-strategy.cmd domination
REM   scripts\use-strategy.cmd balanced         restore the upstream default

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0use-strategy.ps1" %*
exit /b %ERRORLEVEL%
