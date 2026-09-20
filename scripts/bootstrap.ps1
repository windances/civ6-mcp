# Windows bootstrap: the same steps as scripts/bootstrap.sh, without bash.
#
# `scripts/bootstrap.sh` runs under a POSIX shell, and on Windows `bash` on PATH resolves to
# C:\WINDOWS\system32\bash.exe (WSL) - which reads the Windows tree through a Linux view, and on a
# CRLF checkout fails outright with ": invalid option name / line 2: set: pipefail". Invoke this
# through npm instead:
#
#     npm run bootstrap:win
#
# (That npm script passes -ExecutionPolicy Bypass, so it also works on a machine where PowerShell
# refuses to load npm.ps1 with "running scripts is disabled on this system".)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsBin = Join-Path $projectRoot '.tools\bin'
$uv = Join-Path $toolsBin 'uv.exe'

Write-Host "bootstrap: project root $projectRoot"

if (-not (Test-Path $uv)) {
    Write-Host "bootstrap: installing uv into $toolsBin"
    New-Item -ItemType Directory -Force -Path $toolsBin | Out-Null
    $env:UV_INSTALL_DIR = $toolsBin
    # The official Windows installer; it respects UV_INSTALL_DIR and writes uv.exe/uvx.exe there.
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
}

if (-not (Test-Path $uv)) {
    throw "uv was not installed at $uv"
}

Push-Location $projectRoot
try {
    Write-Host 'bootstrap: npm install'
    & npm.cmd install
    if ($LASTEXITCODE -ne 0) { throw "npm install failed ($LASTEXITCODE)" }

    $env:UV_CACHE_DIR = Join-Path $projectRoot '.uv-cache'
    # --extra launcher-windows matters on Windows: the plain `uv sync` in scripts/bootstrap.sh
    # leaves out the winrt packages the game launcher and its OCR tests need, so four launcher
    # tests start failing with "Game launcher requires Windows OCR support".
    Write-Host "bootstrap: uv sync --extra launcher-windows (cache $env:UV_CACHE_DIR)"
    & $uv sync --project $projectRoot --extra launcher-windows
    if ($LASTEXITCODE -ne 0) { throw "uv sync failed ($LASTEXITCODE)" }

    Write-Host 'bootstrap: npm run qualify'
    & npm.cmd run qualify
    if ($LASTEXITCODE -ne 0) { throw "npm run qualify failed ($LASTEXITCODE)" }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Bootstrap complete. Start Civ VI, then run:'
Write-Host '  npm run dsh:play:win -- "Play one complete turn using the civ6-orchestrator skill."'
