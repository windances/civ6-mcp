# Resume a loaded Civilization VI match with a fresh DSH session.
#
# This is the human's one command for the handoff. It does not launch the game, does not
# load a save and does not click anything: launching and loading are the human's calls,
# because they are how a session ends up playing a different branch. What it does is
# (1) check, passively, whether a session can take over, (2) print exactly what the human
# has to do when it cannot, (3) with -Wait, watch until the game is loaded, and (4) generate
# the session's task from the facts it just read and launch the headless session with it.
#
# Usage:
#   powershell -NoProfile -File scripts\resume-game.ps1
#   powershell -NoProfile -File scripts\resume-game.ps1 -Wait          # wait for the load
#   powershell -NoProfile -File scripts\resume-game.ps1 -Turns 30 -DryRun
#   powershell -NoProfile -File scripts\resume-game.ps1 -TaskFile prompts\tasks\continue-current.en.txt
#
# -DryRun prints the check and the task it would use, and launches nothing, so it is safe
# while a game is being played.

[CmdletBinding()]
param(
    [int] $Turns = 100,
    [switch] $Wait,
    [switch] $DryRun,
    [int] $PollSeconds = 5,
    [int] $TimeoutSeconds = 1800,
    # Override: hand this file to the session instead of the task generated from the facts.
    # The generated one is preferred; the static prompts remain for a handoff the preflight
    # cannot describe.
    [string] $TaskFile,
    # The human deliberately loaded an earlier save: the generated task forbids rolling
    # forward, which is the one scenario that cannot be computed from the facts.
    [switch] $Rollback,
    [string] $TaskPath = ".civ6-mcp-data\resume-task.en.txt"
)

$ErrorActionPreference = 'Stop'

# The report carries Chinese save names - the manual save is named after the leader, in Chinese, and
# that name is part of every line about it. A python child writes its stdout in the *locale* encoding
# (gbk on this machine) while PowerShell 5.1 decodes a child's output with [Console]::OutputEncoding
# (utf-8 in Windows Terminal, cp936 in a legacy console), so the name arrived as garbled bytes
# (measured 2026-09-28, reported as a failed scripts\resume-game.ps1). Make the child speak the
# encoding the host is listening in: the report is the whole point of this script, and one that
# cannot name the save is a report nobody can act on. `:replace` so a character outside that code
# page prints as '?' instead of raising in the middle of the report.
#
# This file stays pure ASCII, like every other script here: PowerShell 5.1 reads a BOM-less file as
# the ANSI code page, so a Chinese character in it would be read as mojibake.
if (-not $env:PYTHONIOENCODING) {
    $env:PYTHONIOENCODING = "cp$([Console]::OutputEncoding.CodePage):replace"
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$handoff = Join-Path $projectRoot 'scripts\handoff.py'
$launcher = Join-Path $projectRoot 'scripts\run-dsh-headless.ps1'

foreach ($required in @($python, $handoff, $launcher)) {
    if (-not (Test-Path $required)) { throw "missing: $required" }
}

function Get-Handoff {
    # The JSON call is the API; the text inside it is what a human reads, so the report and
    # the verdict can never disagree about the same instant. Exit code 1 = not ready yet,
    # which is an answer, not a failure.
    $pyArgs = @($handoff, '--json', '--turns', $Turns)
    if ($Rollback) { $pyArgs += '--rollback' }
    $raw = & $python @pyArgs 2>$null
    if (-not $raw) { throw 'handoff.py produced no output' }
    return ($raw | ConvertFrom-Json)
}

function Show-Verdict($state) {
    $state.text -split "`n" | ForEach-Object { Write-Host $_ }
}

$state = Get-Handoff
Show-Verdict $state

if ($DryRun) {
    $task = if ($TaskFile) { $TaskFile } else { $TaskPath }
    if (-not $TaskFile) {
        $taskArgs = @($handoff, '--task', $TaskPath, '--turns', $Turns)
        if ($Rollback) { $taskArgs += '--rollback' }
        $null = & $python @taskArgs 2>$null
    }
    Write-Host ''
    Write-Host "--- the task this would hand to a session ($task) ---"
    Get-Content (Join-Path $projectRoot $task) | ForEach-Object { Write-Host $_ }
    Write-Host '--- dry run: nothing launched ---'
    exit 0
}

if (-not $state.verdict.ready) {
    Write-Host ''
    Write-Host 'Nothing can take over yet: do what NEEDS says above, then run this again.'
    if (-not $Wait) {
        Write-Host "(-Wait makes this script poll instead, for up to $TimeoutSeconds s.)"
        exit 1
    }
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while (-not $state.verdict.ready) {
    if ((Get-Date) -gt $deadline) {
        Write-Host "Gave up after $TimeoutSeconds s without a loaded game."
        exit 1
    }
    Start-Sleep -Seconds $PollSeconds
    $state = Get-Handoff
    Write-Host ("{0}  {1}  {2}" -f (Get-Date -Format 'HH:mm:ss'), $state.verdict.state,
        ($state.verdict.needs -join '; '))
}

# A ready game still needs a credential before the launch is worth attempting: without one
# the MCP starts, runs for a few seconds and dies with MISSING_CREDENTIAL, leaving a stub
# session directory and a 'starting' heartbeat behind.
if ($state.verdict.blockers.Count -gt 0) {
    Write-Host ''
    foreach ($blocker in $state.verdict.blockers) {
        Write-Host "BLOCKED  $blocker" -ForegroundColor Yellow
    }
    Write-Host 'Set the variable, then run this again:'
    Write-Host '  $env:DEEPSEEK_API_KEY = "sk-..."     # this shell only'
    Write-Host '  [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY","sk-...","User")   # then a NEW shell'
    exit 1
}

$taskRelative = if ($TaskFile) { $TaskFile } else { $TaskPath }
if (-not $TaskFile) {
    Write-Host ''
    Write-Host "READY at T$($state.verdict.turn). Writing the task from these facts."
    $taskArgs = @($handoff, '--task', $TaskPath, '--turns', $Turns)
    if ($Rollback) { $taskArgs += '--rollback' }
    & $python @taskArgs 2>$null | ForEach-Object { Write-Host $_ }
}
$taskFull = (Resolve-Path (Join-Path $projectRoot $taskRelative)).Path
if (-not (Test-Path $taskFull)) { throw "the task was not written: $taskFull" }

Write-Host ''
& $launcher -TaskFile $taskFull
exit $LASTEXITCODE
