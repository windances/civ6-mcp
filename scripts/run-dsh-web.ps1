# Windows launcher for the DSH web interface (project overlay applied).
#
# See run-dsh-headless.ps1 for why this exists instead of the .sh variant
# (on Windows `bash` resolves to WSL, which the README warns against).
#
# Usage:
#   pwsh -File scripts/run-dsh-web.ps1
# Then create a Standard agent and ask it to use the civ6-orchestrator skill.

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$dshBin      = Join-Path $projectRoot 'node_modules\.bin\dsh.cmd'
$uvBin       = Join-Path $projectRoot '.tools\bin\uv.exe'

if (-not (Test-Path $dshBin) -or -not (Test-Path $uvBin)) {
    Write-Error "Dependencies are missing. Run: npm install --ignore-scripts; .\.tools\bin\uv.exe sync"
    exit 2
}

if (-not $env:DEEPSEEK_API_KEY) {
    Write-Warning 'DEEPSEEK_API_KEY is not set. The first model turn will fail with an auth error.'
}

$env:DSH_HOME = Join-Path $projectRoot '.dsh-home'
if (-not $env:DSH_TELEMETRY_MODE) { $env:DSH_TELEMETRY_MODE = 'DISABLED' }
if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = '1' }

Push-Location $projectRoot
try {
    & $dshBin --profile web --patch (Join-Path $projectRoot 'dsh\civ6.cordis.yml') --no-open
}
finally {
    Pop-Location
}
exit $LASTEXITCODE
