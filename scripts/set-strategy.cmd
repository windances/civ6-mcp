@echo off
REM Ad-hoc strategy injection without fighting the PowerShell execution policy.
REM
REM Usage (from the project root, in cmd, PowerShell or Git Bash):
REM   scripts\set-strategy.cmd -Show
REM   scripts\set-strategy.cmd -File my-strategy.md
REM   scripts\set-strategy.cmd -Text "Pursue a science victory."
REM
REM For non-ASCII strategy text prefer -File: text written on a Windows command
REM line is re-encoded by the console code page and can arrive mangled.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0set-strategy.ps1" %*
exit /b %ERRORLEVEL%
