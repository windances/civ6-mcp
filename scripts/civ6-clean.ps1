# Stop a civ6-mcp game session and leave the runtime environment clean.
#
# Ctrl+C on the dsh console stops the agent, but three things outlive it:
#
#   * the Civilization VI process, which keeps the tuner ports open;
#   * any civ6-mcp server process still attached to that tuner, which will retry a
#     dead connection forever;
#   * heartbeat.json, which then describes a run that no longer exists - a stale
#     "phase": "playing", "turn": N is exactly what makes a stopped game look like
#     a live one.
#
# This stops them in the right order (game first, so the MCP stops retrying) and
# then verifies the result instead of assuming it.
#
# The DSH Web GUI is never touched. It is found by the process listening on
# -WebGuiPort, and that pid is excluded from every kill list, so cleaning up a game
# session cannot take down the interface you are driving it from.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1 -DryRun
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1 -KeepGame
#
# -DryRun reports and changes nothing. -KeepGame stops only the agent and the MCP.
# -Force additionally kills node processes that merely look like a dsh agent, for
# use when the process table cannot be read and the agent has to go anyway.

[CmdletBinding()]
param(
    [switch] $DryRun,

    [switch] $KeepGame,

    [switch] $Force,

    [int[]] $TunerPort = @(4318, 4319),

    [int] $WebGuiPort = 3080,

    # How long to wait for large processes to finish exiting before reporting.
    [int] $WaitSeconds = 20
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$dataDir     = Join-Path $projectRoot '.civ6-mcp-data'
$heartbeat   = Join-Path $dataDir 'heartbeat.json'

function Say([string] $text, [string] $colour = 'Gray') {
    Write-Host $text -ForegroundColor $colour
}

# --- what is running ---------------------------------------------------------

# netstat rather than Get-NetTCPConnection: the cmdlet is missing on some hosts and
# silently returns nothing, which would read as "nothing is listening".
function Get-PortMap {
    $listening = @{}
    $established = @{}
    foreach ($line in (netstat -ano | Select-String 'LISTENING|ESTABLISHED')) {
        $fields = ($line.ToString().Trim() -split '\s+')
        if ($fields.Length -lt 5) { continue }
        $localPort  = [int](($fields[1] -split ':')[-1])
        $remotePort = [int](($fields[2] -split ':')[-1])
        $owner      = [int]$fields[4]
        if ($line.ToString() -match 'LISTENING') {
            if (-not $listening.ContainsKey($localPort)) { $listening[$localPort] = @() }
            $listening[$localPort] += $owner
        } else {
            foreach ($port in @($localPort, $remotePort)) {
                if ($TunerPort -notcontains $port) { continue }
                if (-not $established.ContainsKey($owner)) { $established[$owner] = @() }
                $established[$owner] += $port
            }
        }
    }
    return @{ listening = $listening; established = $established }
}

# Command lines make the classification exact. Without them the script falls back
# to image names and port ownership, and says so rather than guessing.
function Get-ProcessIndex {
    try {
        $rows = Get-CimInstance Win32_Process -ErrorAction Stop
    } catch {
        return @{ ok = $false; byId = @{} }
    }
    $byId = @{}
    foreach ($row in $rows) { $byId[[int]$row.ProcessId] = $row }
    return @{ ok = $true; byId = $byId }
}

$ports = Get-PortMap
$index = Get-ProcessIndex

function Get-Cmdline([int] $processId) {
    if (-not $index.ok) { return '' }
    if (-not $index.byId.ContainsKey($processId)) { return '' }
    return [string]$index.byId[$processId].CommandLine
}

# The Web GUI and this script's own process tree must survive whatever else happens.
$protected = New-Object 'System.Collections.Generic.HashSet[int]'
[void]$protected.Add($PID)
if ($ports.listening.ContainsKey($WebGuiPort)) {
    foreach ($owner in $ports.listening[$WebGuiPort]) { [void]$protected.Add($owner) }
}
if ($index.ok) {
    $cursor = $PID
    for ($hop = 0; $hop -lt 6; $hop++) {
        if (-not $index.byId.ContainsKey($cursor)) { break }
        $cursor = [int]$index.byId[$cursor].ParentProcessId
        if ($cursor -le 0) { break }
        [void]$protected.Add($cursor)
    }
}

Say ''
Say "civ6 cleanup  (project $projectRoot)"
Say ("  command lines readable : {0}" -f $(if ($index.ok) { 'yes' } else { 'no - falling back to image names and ports' }))
Say ("  protected              : {0}" -f (($protected | Sort-Object) -join ', '))
if ($ports.listening.ContainsKey($WebGuiPort)) {
    Say ("  web gui                : pid {0} on :{1} (never killed)" -f ($ports.listening[$WebGuiPort] -join ','), $WebGuiPort)
}

# --- classify ----------------------------------------------------------------

$gamePids = @()
foreach ($name in 'CivilizationVI_DX12', 'CivilizationVI', 'CivilizationVI_DX11') {
    $gamePids += (Get-Process -Name $name -ErrorAction SilentlyContinue).Id
}
# The tuner listener belongs to the game whatever the executable is called.
foreach ($port in $TunerPort) {
    if ($ports.listening.ContainsKey($port)) { $gamePids += $ports.listening[$port] }
}
$gamePids = @($gamePids | Sort-Object -Unique | Where-Object { -not $protected.Contains($_) })

$mcpPids = @()
foreach ($process in (Get-Process -ErrorAction SilentlyContinue)) {
    if ($protected.Contains($process.Id)) { continue }
    $cmdline = Get-Cmdline $process.Id
    $isPython = $process.ProcessName -like 'python*'
    if (-not $isPython) { continue }
    if ($cmdline -match 'civ_mcp|civ6-mcp|\.civ6-mcp' -or $ports.established.ContainsKey($process.Id)) {
        $mcpPids += $process.Id
    }
}
$mcpPids = @($mcpPids | Sort-Object -Unique)

$agentPids = @()
foreach ($process in (Get-Process -Name 'node' -ErrorAction SilentlyContinue)) {
    if ($protected.Contains($process.Id)) { continue }
    $cmdline = Get-Cmdline $process.Id
    if ($cmdline -and ($cmdline -match [regex]::Escape($projectRoot) -or $cmdline -match '--profile\s+(headless|web)')) {
        $agentPids += $process.Id
    }
}
$agentPids = @($agentPids | Sort-Object -Unique)

$suspectPids = @()
if (-not $index.ok) {
    # No command lines: a node process that is neither the Web GUI nor a transient
    # helper cannot be told from the agent, so these are only killed with -Force.
    foreach ($process in (Get-Process -Name 'node' -ErrorAction SilentlyContinue)) {
        if ($protected.Contains($process.Id)) { continue }
        if ($agentPids -contains $process.Id) { continue }
        $suspectPids += $process.Id
    }
    $suspectPids = @($suspectPids | Sort-Object -Unique)
}

function Show-Plan([string] $label, [int[]] $pids, [string] $note = '') {
    if (-not $pids -or $pids.Count -eq 0) {
        Say ("  {0,-10} none" -f $label)
        return
    }
    $detail = ($pids | ForEach-Object {
        $process = Get-Process -Id $_ -ErrorAction SilentlyContinue
        if ($process) { "{0}:{1}" -f $_, $process.ProcessName } else { "$_" }
    }) -join ', '
    Say ("  {0,-10} {1}{2}" -f $label, $detail, $(if ($note) { "   $note" } else { '' }))
}

Say ''
Say 'plan'
if ($KeepGame) {
    Show-Plan 'game' @() '(-KeepGame: left running)'
} else {
    Show-Plan 'game' $gamePids
}
Show-Plan 'mcp' $mcpPids
Show-Plan 'agent' $agentPids
if ($index.ok) {
    Show-Plan 'node?' $suspectPids 'not classified'
} else {
    if ($Force) {
        Show-Plan 'agent?' $suspectPids '-Force: will be killed'
    } else {
        Show-Plan 'agent?' $suspectPids 'unknown identity - rerun with -Force to kill them'
    }
}

$stateFiles = @()
if (Test-Path $heartbeat) {
    $stateFiles += $heartbeat
}

Say ''
Say 'state'
if ($stateFiles.Count -eq 0) {
    Say '  heartbeat    none (already clean)'
} else {
    foreach ($file in $stateFiles) {
        $body = ''
        try { $body = ([IO.File]::ReadAllText($file) -replace '\s+', ' ').Trim() } catch { $body = '<unreadable>' }
        Say ("  delete       {0}" -f (Split-Path $file -Leaf)) 
        Say ("               {0}" -f $body, 'DarkGray')
    }
}

if ($DryRun) {
    Say ''
    Say 'dry run: nothing stopped, nothing deleted' 'Yellow'
    exit 0
}

# --- act ---------------------------------------------------------------------

Say ''
Say 'acting'

$killed = @()
function Stop-These([int[]] $pids, [string] $label) {
    foreach ($processId in $pids) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if (-not $process) { continue }
        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Say ("  stopped      {0} {1} ({2})" -f $label, $processId, $process.ProcessName) 'Yellow'
            $script:killed += $processId
        } catch {
            Say ("  FAILED       {0} {1}: {2}" -f $label, $processId, $_.Exception.Message) 'Red'
        }
    }
}

# Game first: with the tuner gone the MCP stops retrying instead of reconnecting
# while we are killing it.
if (-not $KeepGame) { Stop-These $gamePids 'game' }
Stop-These $mcpPids 'mcp'
Stop-These $agentPids 'agent'
if ($Force) { Stop-These $suspectPids 'agent?' }

foreach ($file in $stateFiles) {
    try {
        Remove-Item $file -Force -ErrorAction Stop
        Say ("  deleted      {0}" -f (Split-Path $file -Leaf)) 'Yellow'
    } catch {
        Say ("  FAILED       delete {0}: {1}" -f (Split-Path $file -Leaf), $_.Exception.Message) 'Red'
    }
}

# --- verify ------------------------------------------------------------------

# Poll rather than sample once: stopping a several-gigabyte game process is not
# instantaneous, and a slow exit would otherwise be reported as a failed kill.
# Something appearing during the wait is a real failure - it means a respawn.
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$after = Get-PortMap
$stillGame = @()
$stillMcp = @()
while ($true) {
    $after = Get-PortMap
    $stillGame = @()
    foreach ($name in 'CivilizationVI_DX12', 'CivilizationVI', 'CivilizationVI_DX11') {
        $stillGame += (Get-Process -Name $name -ErrorAction SilentlyContinue).Id
    }
    foreach ($port in $TunerPort) {
        if ($after.listening.ContainsKey($port)) { $stillGame += $after.listening[$port] }
    }
    $stillGame = @($stillGame | Sort-Object -Unique)

    $stillMcp = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -like 'python*' -and -not $protected.Contains($_.Id) -and
        ((Get-Cmdline $_.Id) -match 'civ_mcp|civ6-mcp' -or $after.established.ContainsKey($_.Id))
    })

    $settled = ($KeepGame -or $stillGame.Count -eq 0) -and $stillMcp.Count -eq 0 -and -not (Test-Path $heartbeat)
    if ($settled -or (Get-Date) -ge $deadline) { break }
    Start-Sleep -Milliseconds 500
}

Say ''
Say 'verify'
$leftover = @()
if (-not $KeepGame -and $stillGame.Count -gt 0) {
    $leftover += "game still running: $($stillGame -join ', ')"
}
foreach ($port in $TunerPort) {
    if ($after.listening.ContainsKey($port)) {
        $leftover += ("tuner :{0} still listening (pid {1})" -f $port, ($after.listening[$port] -join ','))
    }
}
if ($stillMcp.Count -gt 0) { $leftover += "mcp still running: $($stillMcp.Id -join ', ')" }
if (Test-Path $heartbeat) { $leftover += 'heartbeat.json still present' }

if ($leftover.Count -eq 0) {
    Say '  clean: no game, no tuner listener, no mcp, no heartbeat' 'Green'
    exit 0
}

foreach ($item in $leftover) { Say ("  {0}" -f $item) 'Red' }
exit 1
