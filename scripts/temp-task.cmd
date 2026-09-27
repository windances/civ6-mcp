@echo off
REM Add, retire and inspect the temporary tasks in prompts/tasks/tmp/.
REM
REM Usage (from the project root, in cmd, PowerShell or Git Bash):
REM   scripts\temp-task.cmd status
REM   scripts\temp-task.cmd add --title "take Brussels: analysis, staging, assault" ^
REM       --instruction @.tmp\instruction.txt --why "take Brussels on the human's instruction" ^
REM       --done-when @.tmp\done-when.txt --overrides @.tmp\overrides.txt --scope @.tmp\scope.txt ^
REM       --body-file .tmp\body.md
REM   scripts\temp-task.cmd retire 021 --expired --turn 270 --note "..."
REM
REM For non-ASCII instruction text prefer --instruction @file: text typed on a Windows command
REM line is re-encoded by the console code page and can arrive mangled. The instruction is written
REM into the task file's added: line as UTF-8 with a BOM, which is what a zh-CN editor needs.
REM
REM The script writes the task file, the register row and AGENTS.md's IN FORCE NOW line together,
REM runs the mandatory text gate and tests/test_temp_tasks.py, and commits only when they are green.

setlocal
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0temp-task.py" %*
exit /b %ERRORLEVEL%
