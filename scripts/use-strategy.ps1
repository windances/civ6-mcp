# Switch the civ6-orchestrator worker prompts between strategy presets.
#
# Each preset in prompts/strategies/<name>/ holds the four advisor prompts and the
# strategy directive. Applying one copies the prompts over prompts/workers/ (inert -
# measured 2026-09-19: the running agent never reads them, but the static gate checks
# them) and rewrites the DIRECTIVE block in
# .dsh/skills/civ6-orchestrator/SKILL.md, which is the copy the agent does read.
# A preset is reported as active only when both destinations agree.
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
$skillPath     = Join-Path $projectRoot '.dsh\skills\civ6-orchestrator\SKILL.md'
# Capture group 1 is the directive body, so one pattern serves both the apply path
# (Replace) and the "which preset is active" comparison (Match).
$marker        = '(?s)<!-- DIRECTIVE:BEGIN -->\s*(.*?)\s*<!-- DIRECTIVE:END -->'
# The first line of an ad-hoc block, written by scripts\set-strategy.ps1. An ad-hoc
# block is neither a preset nor a stale preset, and saying so is the difference between
# "re-apply to resynchronise" and "this override is deliberate".
$adHocMarker   = '<!-- ad-hoc directive from the human, not a preset: switching presets replaces it -->'

# The four roles are fixed by contracts/worker-proposal.schema.json; the static
# gate enforces both this set and the two mandatory phrases below.
$roles = @('strategy', 'military-map', 'economy-cities', 'diplomacy-victory')
$requiredPhrases = @('immutable', 'Do not request tools')

function Get-Presets {
    Get-ChildItem $strategiesDir -Directory -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Name | Sort-Object
}

# The directive block as it currently stands in SKILL.md: the trimmed body, or
# $null when SKILL.md or its marker block cannot be read.
function Get-SkillDirective {
    if (-not (Test-Path $skillPath)) { return $null }
    $match = [regex]::Match([IO.File]::ReadAllText($skillPath), $marker)
    if (-not $match.Success) { return $null }
    return $match.Groups[1].Value.Trim()
}

# A preset is active only when BOTH destinations agree: the four role files in
# prompts/workers/ and the directive block in SKILL.md.
#
# Comparing the role files alone reported a preset as active while the block still
# carried a different strategy: measured 2026-09-27, prompts/workers/ matched
# china-conquest while the block was 38 lines behind it, missing the whole
# three-phase (analysis -> staging -> execution) section. The block is the copy the
# agent reads, so it is the one that decides; a preset that only half-arrived is not
# active, it is stale.
#
# -IgnoreDirective answers the weaker question - which preset are the role files
# from - which is what a near-miss message needs.
function Get-CurrentPreset {
    [CmdletBinding()]
    param([switch] $IgnoreDirective)

    $live = @{}
    foreach ($role in $roles) {
        $path = Join-Path $workersDir "$role.md"
        if (Test-Path $path) { $live[$role] = (Get-FileHash $path -Algorithm SHA256).Hash }
    }
    $liveDirective = if ($IgnoreDirective) { $null } else { Get-SkillDirective }
    foreach ($preset in Get-Presets) {
        $matches = $true
        foreach ($role in $roles) {
            $candidate = Join-Path $strategiesDir "$preset\$role.md"
            if (-not (Test-Path $candidate)) { $matches = $false; break }
            if ($live[$role] -ne (Get-FileHash $candidate -Algorithm SHA256).Hash) {
                $matches = $false; break
            }
        }
        if (-not $matches) { continue }
        if (-not $IgnoreDirective) {
            $candidateDirective = Join-Path $strategiesDir "$preset\directive.md"
            if (Test-Path $candidateDirective) {
                $wanted = ([IO.File]::ReadAllText($candidateDirective)).Trim()
                if ($wanted -ne $liveDirective) { continue }
            }
        }
        return $preset
    }
    return $null
}

function Show-Presets {
    $current = Get-CurrentPreset
    Write-Host 'Available strategy presets:'
    foreach ($preset in Get-Presets) {
        $activeMark = if ($preset -eq $current) { ' <- active' } else { '' }
        Write-Host ("  {0}{1}" -f $preset, $activeMark)
    }
    if ($current) { return }
    Write-Host ''
    $live = Get-SkillDirective
    if ($null -eq $live) {
        Write-Host 'SKILL.md is missing, or has no DIRECTIVE:BEGIN/END block:'
        Write-Host "  $skillPath"
        Write-Host 'No preset can report as active until one is applied to write the block.'
        return
    }
    $rolesOnly = Get-CurrentPreset -IgnoreDirective
    if ($live.StartsWith($adHocMarker)) {
        Write-Host 'The SKILL.md directive block is an ad-hoc directive, not a preset.'
        if ($rolesOnly) { Write-Host "prompts/workers/ still matches '$rolesOnly'." }
        $suggest = if ($rolesOnly) { $rolesOnly } else { 'balanced' }
        Write-Host "Re-apply a preset to replace it: scripts\use-strategy.ps1 $suggest"
        return
    }
    if ($rolesOnly) {
        Write-Host "prompts/workers/ matches '$rolesOnly', but the SKILL.md directive block does not."
        Write-Host 'The block is the copy the agent reads, so both are re-applied together:'
        Write-Host "  scripts\use-strategy.ps1 $rolesOnly"
        return
    }
    Write-Host 'prompts/workers/ matches no preset (hand-edited).'
    Write-Host "Apply one to get back to a known state, e.g.: scripts\use-strategy.ps1 balanced"
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
# $skillPath and $marker are defined once near the top, because the same pattern
# decides which preset is active.
$directivePath = Join-Path $presetDir 'directive.md'

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
        # Write a BOM only when the document holds a non-ASCII byte. A pure-ASCII file carries none -
        # that is the bar AGENTS.md, the skill and the presets are held to - and a file with Chinese
        # in it needs one to stay readable in a zh-CN editor (see scripts/fix-text-encoding.py).
        $encoding = New-Object System.Text.UTF8Encoding ([regex]::IsMatch($skill, '[^\x00-\x7F]'))
        [IO.File]::WriteAllText($skillPath, $skill, $encoding)
        # Read it back: a write that did not land (a sandbox denial, a stale handle)
        # would otherwise be reported as success, and "which preset is active" is
        # computed from the file, so a silent failure shows up as no preset at all.
        if ((Get-SkillDirective) -ne $body) {
            Fail "SKILL.md was written, but its directive block does not read back as '$Name'."
        }
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
