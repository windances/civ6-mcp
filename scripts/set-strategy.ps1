# Inject an ad-hoc strategy directive without going through a preset.
#
# The orchestrator's strategy is the DIRECTIVE block inside the skill file. The
# MCP server re-reads that block on every end_turn and hands it to the agent when
# it has changed, so an edit here reaches the running game on the next turn - no
# restart, no re-briefing.
#
# Usage:
#   scripts\set-strategy.ps1 -Text "Pursue a science victory; Campus adjacency first."
#   scripts\set-strategy.ps1 -File my-strategy.md
#   scripts\set-strategy.ps1 -Show
#
# Unlike a preset this is a one-off: the next `use-strategy.ps1 <name>` will
# overwrite the block with that preset's directive. The block therefore carries a
# first line saying that it is ad-hoc, so the state is visible rather than looking
# like a preset whose text drifted (tests/test_strategy_block.py).
#
# If PowerShell refuses to run it ("running scripts is disabled"), invoke it as:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\set-strategy.ps1 ...

[CmdletBinding(DefaultParameterSetName = 'Text')]
param(
    [Parameter(ParameterSetName = 'Text', Mandatory = $true, Position = 0)]
    [string] $Text,

    [Parameter(ParameterSetName = 'File', Mandatory = $true)]
    [string] $File,

    [Parameter(ParameterSetName = 'Show', Mandatory = $true)]
    [switch] $Show
)

$ErrorActionPreference = 'Stop'

# Write to stderr and exit deterministically. Write-Error would throw under
# 'Stop' and surface as exit 1, which is indistinguishable from a crash.
function Fail([string] $message) {
    [Console]::Error.WriteLine("error: $message")
    exit 2
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$skillPath   = Join-Path $projectRoot '.dsh\skills\civ6-orchestrator\SKILL.md'
$marker      = '(?s)(<!-- DIRECTIVE:BEGIN -->).*?(<!-- DIRECTIVE:END -->)'
$blockOnly   = '(?s)<!-- DIRECTIVE:BEGIN -->(.*?)<!-- DIRECTIVE:END -->'
# The first line of an ad-hoc block. Read by both switchers (which report it as
# neither a preset nor a stale preset) and by tests/test_strategy_block.py. The exact
# same literal is in scripts/set-strategy.sh.
$adHocMarker = '<!-- ad-hoc directive from the human, not a preset: switching presets replaces it -->'

if (-not (Test-Path $skillPath)) { Fail "SKILL.md not found at $skillPath" }

# Read and write through .NET, never Get-Content/Set-Content: PowerShell 5.1
# decodes a BOM-less UTF-8 file with the ANSI code page, which silently destroys
# Chinese text and em dashes on a cp936 machine and then bakes the damage in.
$skill = [IO.File]::ReadAllText($skillPath)

if ($Show) {
    $m = [regex]::Match($skill, $blockOnly)
    if (-not $m.Success) { Fail 'SKILL.md has no DIRECTIVE:BEGIN/END marker block.' }
    $m.Groups[1].Value.Trim()
    exit 0
}

if (-not [regex]::IsMatch($skill, $marker)) {
    Fail 'SKILL.md has no DIRECTIVE:BEGIN/END marker block; nothing injected.'
}

if ($PSCmdlet.ParameterSetName -eq 'File') {
    if (-not (Test-Path $File)) { Fail "Strategy file not found: $File" }
    $body = ([IO.File]::ReadAllText((Resolve-Path $File).Path)).Trim()
} else {
    $body = $Text.Trim()
}

if (-not $body) { Fail 'Strategy text is empty; refusing to inject an empty directive.' }

# Mark the block as ad-hoc before it is written. Without the line it is
# indistinguishable from a preset whose text drifted, which is the state
# tests/test_strategy_block.py exists to fail on; with it, a deliberate override and a
# silent drift are two different things.
$body = $adHocMarker + "`n`n" + $body

# Script-block replacement so a '$' in the strategy is never read as a regex
# substitution token.
$skill = [regex]::Replace(
    $skill,
    $marker,
    { param($m) $m.Groups[1].Value + "`n" + $body + "`n" + $m.Groups[2].Value }
)
# Write with a BOM: `WriteAllText` without an encoding emits plain UTF-8 and strips the
# BOM this file needs to stay readable in a zh-CN editor (see scripts/fix-text-encoding.py).
# This script had that bug - every ad-hoc directive left SKILL.md BOM-less.
[IO.File]::WriteAllText($skillPath, $skill, (New-Object System.Text.UTF8Encoding($true)))

# Read it back: a write that did not land would otherwise be reported as success, and
# the block is what the running session is handed.
$check = [regex]::Match([IO.File]::ReadAllText($skillPath), $blockOnly)
if (-not $check.Success -or $check.Groups[1].Value.Trim() -ne $body) {
    Fail 'SKILL.md was written, but its directive block does not read back as the injected text.'
}

Write-Host 'Ad-hoc strategy injected into the directive block.'
Write-Host 'The agent sees it on the next end_turn - no restart needed.'
Write-Host ''
Write-Host 'Verify with a distinctive phrase from your text:'
Write-Host '  $s = Get-ChildItem .\.dsh-home\sessions -Recurse -File -Filter session.jsonl.zstd |'
Write-Host '       Sort-Object LastWriteTime -Descending | Select-Object -First 1'
Write-Host '  node .tools\session-grep.mjs $s.FullName "your phrase"'
