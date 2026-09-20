# Switch the civ6-orchestrator worker prompts between strategy presets.
#
# Each preset in prompts/strategies/<name>/ holds the four advisor prompts.
# Applying one copies them over prompts/workers/, which is the directory the
# advisor route actually reads.
#
# Usage:
#   pwsh -File scripts/use-strategy.ps1                 # list presets + current
#   pwsh -File scripts/use-strategy.ps1 -List           # same
#   pwsh -File scripts/use-strategy.ps1 science         # apply a preset
#   pwsh -File scripts/use-strategy.ps1 balanced        # restore upstream default
#
# The static qualification gate is run after every change, so a preset that
# would break `npm run qualify` is rejected instead of silently applied.

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $Name,

    [switch] $List
)

$ErrorActionPreference = 'Stop'

# Write to stderr and exit deterministically. Write-Error would throw under
# 'Stop' and surface as exit 1, indistinguishable from a crash.
function Fail([string] $message) {
    [Console]::Error.WriteLine("error: $message")
    exit 2
}

$projectRoot   = Split-Path -Parent $PSScriptRoot
$strategiesDir = Join-Path $projectRoot 'prompts\strategies'
$workersDir    = Join-Path $projectRoot 'prompts\workers'
$gateScript    = Join-Path $projectRoot 'scripts\qualify-static.mjs'

# The four roles are fixed by contracts/worker-proposal.schema.json; the static
# gate enforces both this set and the two mandatory phrases below.
$roles = @('strategy', 'military-map', 'economy-cities', 'diplomacy-victory')
$requiredPhrases = @('immutable', 'Do not request tools')

function Get-Presets {
    Get-ChildItem $strategiesDir -Directory -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Name | Sort-Object
}

function Get-CurrentPreset {
    $live = @{}
    foreach ($role in $roles) {
        $path = Join-Path $workersDir "$role.md"
        if (Test-Path $path) { $live[$role] = (Get-FileHash $path -Algorithm SHA256).Hash }
    }
    foreach ($preset in Get-Presets) {
        $matches = $true
        foreach ($role in $roles) {
            $candidate = Join-Path $strategiesDir "$preset\$role.md"
            if (-not (Test-Path $candidate)) { $matches = $false; break }
            if ($live[$role] -ne (Get-FileHash $candidate -Algorithm SHA256).Hash) {
                $matches = $false; break
            }
        }
        if ($matches) { return $preset }
    }
    return $null
}

function Show-Presets {
    $current = Get-CurrentPreset
    Write-Host 'Available strategy presets:'
    foreach ($preset in Get-Presets) {
        $marker = if ($preset -eq $current) { ' <- active' } else { '' }
        Write-Host ("  {0}{1}" -f $preset, $marker)
    }
    if (-not $current) {
        Write-Host ''
        Write-Host 'prompts/workers/ matches no preset (hand-edited).'
        Write-Host "Apply one to get back to a known state, e.g.: scripts\use-strategy.ps1 balanced"
    }
}

if ($List -or -not $Name) {
    Show-Presets
    exit 0
}

$presetDir = Join-Path $strategiesDir $Name
if (-not (Test-Path $presetDir)) {
    Fail "No such preset '$Name'. Available: $((Get-Presets) -join ', ')"
}

# Validate before touching prompts/workers/, so a bad preset cannot leave the
# repository in a state that fails the gate.
$problems = @()
foreach ($role in $roles) {
    $path = Join-Path $presetDir "$role.md"
    if (-not (Test-Path $path)) {
        $problems += "missing file: $role.md"
        continue
    }
    $text   = Get-Content $path -Raw
    $length = (Get-Item $path).Length
    if ($length -le 100) { $problems += "$role.md is only $length bytes (gate needs > 100)" }
    foreach ($phrase in $requiredPhrases) {
        if ($text -notmatch [regex]::Escape($phrase)) {
            $problems += "$role.md must contain the phrase '$phrase'"
        }
    }
}
if ($problems.Count) {
    Write-Host "Preset '$Name' is not valid:" -ForegroundColor Red
    $problems | ForEach-Object { Write-Host "  - $_" }
    exit 2
}

foreach ($role in $roles) {
    Copy-Item (Join-Path $presetDir "$role.md") (Join-Path $workersDir "$role.md") -Force
}

# The strategy directive goes into SKILL.md, not only into prompts/workers/.
# Verified 2026-09-19: the running agent never reads prompts/workers/*.md (a
# session-wide search for the word "immutable", which every worker prompt
# contains, returned zero hits), so presets applied only there had no effect.
# The skill IS read, so that is where the directive has to live.
$skillPath     = Join-Path $projectRoot '.dsh\skills\civ6-orchestrator\SKILL.md'
$directivePath = Join-Path $presetDir 'directive.md'
$marker        = '(?s)<!-- DIRECTIVE:BEGIN.*?<!-- DIRECTIVE:END -->'

if (-not (Test-Path $directivePath)) {
    Write-Warning "Preset '$Name' has no directive.md; SKILL.md left unchanged."
} elseif (-not (Test-Path $skillPath)) {
    Write-Warning "SKILL.md not found at $skillPath; strategy directive not injected."
} else {
    # Read with .NET, not Get-Content: PowerShell 5.1's Get-Content decodes a
    # BOM-less UTF-8 file using the ANSI code page, which silently mangles every
    # em dash on a cp936 machine and then bakes the damage in on write.
    $skill = [IO.File]::ReadAllText($skillPath)
    if ($skill -notmatch $marker) {
        Write-Warning 'SKILL.md has no DIRECTIVE:BEGIN/END marker block; strategy not injected.'
    } else {
        $body  = ([IO.File]::ReadAllText($directivePath)).Trim()
        $block = "<!-- DIRECTIVE:BEGIN -->`n" + $body + "`n<!-- DIRECTIVE:END -->"
        # Script-block replacement so that a '$' inside the directive is never
        # interpreted as a regex substitution token.
        $skill = [regex]::Replace($skill, $marker, { param($m) $block })
        [IO.File]::WriteAllText($skillPath, $skill)
        Write-Host "Strategy directive injected into SKILL.md."
    }
}
Write-Host "Applied strategy preset: $Name"
Write-Host ''

# Prove the gate still passes rather than assuming it.
$node = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $node) { $node = 'C:\Program Files\nodejs\node.exe' }
if (Test-Path $gateScript) {
    & $node $gateScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host ''
        Write-Host 'The static gate FAILED after applying this preset.' -ForegroundColor Red
        exit $LASTEXITCODE
    }
} else {
    Write-Warning "Gate script not found at $gateScript; skipped verification."
}
