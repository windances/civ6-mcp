# Windows launcher for the headless DSH orchestrator.
#
# scripts/run-dsh-headless.sh is the POSIX entry point, but on Windows `bash`
# resolves to WSL and the README explicitly warns against running civ6-mcp from
# WSL. This script performs the same steps with native Windows paths.
#
# Usage:
#   pwsh -File scripts/run-dsh-headless.ps1
#   pwsh -File scripts/run-dsh-headless.ps1 "Play one complete turn using the civ6-orchestrator skill."
#   pwsh -File scripts/run-dsh-headless.ps1 -TaskFile prompts/tasks/continue-from-t59.zh.txt
#   pwsh -File scripts/run-dsh-headless.ps1 -TaskFile prompts/tasks/continue-from-t59.zh.txt -DryRun
#
# Startup prompts live in prompts/tasks/ as a .zh.txt / .en.txt pair. -TaskFile
# does NOT pass the file's text as the task: it passes a one-line pointer to it,
# and the agent reads the file with its own read tool. That is not a stylistic
# choice, it is the only path that works - see the note on the command-line hop
# below. An inline task argument still works for short one-liners, and is
# rejected outright if it contains a newline or a double quote.

[CmdletBinding()]
param(
    # Position = 0 is load-bearing. With ValueFromRemainingArguments alone,
    # PowerShell excludes this parameter from positional binding, so a bare
    # `run-dsh-headless.ps1 "some task"` bound the text to $TaskFile and failed
    # with "Task file not found". Declaring the position as well makes a bare
    # argument land here, while still allowing several unquoted words.
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]] $Task,

    [string] $TaskFile,

    [switch] $DryRun
)

$ErrorActionPreference = 'Stop'

# Write to stderr and exit deterministically. Write-Error would throw under
# 'Stop' and surface as exit 1, indistinguishable from a crash.
function Fail([string] $message) {
    [Console]::Error.WriteLine("error: $message")
    exit 2
}

# SHA-256 of a string's UTF-8 bytes, uppercase, matching coreutils `sha256sum`.
function Get-Digest([string] $text) {
    $sha = [Security.Cryptography.SHA256]::Create()
    return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))).Replace('-', '')
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$dshBin      = Join-Path $projectRoot 'node_modules\.bin\dsh.cmd'
$uvBin       = Join-Path $projectRoot '.tools\bin\uv.exe'

if (-not (Test-Path $dshBin) -or -not (Test-Path $uvBin)) {
    Fail "Dependencies are missing. Run: npm install --ignore-scripts; .\.tools\bin\uv.exe sync"
}

if (-not $env:DEEPSEEK_API_KEY) {
    Write-Warning 'DEEPSEEK_API_KEY is not set. The first model turn will fail with an auth error.'
}

if ($TaskFile -and $Task) {
    Fail '-TaskFile and a task argument are mutually exclusive; pass one or the other.'
}

# The task reaches dsh as a process argument, and this box corrupts long text on
# that hop in two independent ways. Both were measured with the probes in
# .tools/_argvprobe.cmd and .tools/_argvprobe.mjs, using a 307-character Chinese
# prompt:
#
#   * node_modules\.bin\dsh.cmd is a batch shim, and cmd.exe ends the command
#     line at the first newline. The prompt arrived as 80 characters - its first
#     line only, with no error and no warning.
#   * Bypassing the shim does not fix it. Windows PowerShell does not escape
#     embedded double quotes when it builds a native command line, so the text
#     splits into extra arguments and the CLI rejoins them with spaces
#     (`program.args.join(' ')` in the headless bundle). The prompt arrived as
#     303 characters, with the quoted phrase reflowed.
#
# So a prompt file is never passed as text. -TaskFile passes a one-line pointer
# and the agent reads the file itself - the same channel AGENTS.md and the
# strategy directive already use. A pointer is short, single-line and pure
# ASCII, which makes it byte-exact through both shims, and it removes any
# command-line length limit from the picture.
$pointer = $null
if ($TaskFile) {
    if (-not (Test-Path $TaskFile)) {
        Fail "Task file not found: $TaskFile"
    }
    $path = (Resolve-Path $TaskFile).Path
    # Read with .NET, not Get-Content: PowerShell 5.1 decodes a BOM-less UTF-8
    # file using the ANSI code page, which mangles every non-ASCII character.
    $fileText = [IO.File]::ReadAllText($path).TrimStart([char]0xFEFF)
    if (-not $fileText.Trim()) {
        Fail "Task file is empty: $TaskFile"
    }
    # The agent's working directory is the project root, so reference the file
    # relative to it when we can: shorter, and it reads as a workspace path.
    $reference = $path
    if ($path.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
        $reference = $path.Substring($projectRoot.Length).TrimStart('\', '/')
    }
    $reference = $reference.Replace('\', '/')
    $message = "Read $reference and carry out every instruction in it before doing anything else."
} elseif ($Task) {
    $message = $Task -join ' '
    if ($message -match "[\r\n]") {
        Fail 'A task argument cannot contain a newline: cmd.exe ends the command line there, so dsh would silently receive only the first line. Put the text in a file and pass -TaskFile.'
    }
    if ($message.Contains('"')) {
        Fail 'A task argument cannot contain a double quote: Windows PowerShell does not escape it, so the text would be split into extra arguments. Put the text in a file and pass -TaskFile.'
    }
} else {
    $message = 'Play one complete turn using the civ6-orchestrator skill.'
}

if ($DryRun) {
    if ($TaskFile) {
        Write-Host "task file     $path"
        Write-Host "file bytes    $((Get-Item $path).Length) on disk"
        Write-Host "file text     $($fileText.Length) chars, $([Text.Encoding]::UTF8.GetBytes($fileText).Length) utf-8 bytes (BOM stripped)"
        Write-Host "file sha256   $(Get-Digest $fileText)"
        Write-Host ''
    }
    $taskBytes = [Text.Encoding]::UTF8.GetBytes($message)
    $origin = if ($TaskFile) { '<pointer to the file above>' } else { '<argument>' }
    Write-Host "source        $origin"
    Write-Host "task chars    $($message.Length)"
    Write-Host "task bytes    $($taskBytes.Length)"
    Write-Host "task sha256   $(Get-Digest $message)"
    Write-Host ''
    # The console may still render the text badly even when the string is
    # correct; the digest is the thing to compare.
    Write-Host '--- the entire task handed to dsh (console rendering may be lossy) ---'
    Write-Host $message
    Write-Host '--- dry run: nothing launched ---'
    exit 0
}

# Match the POSIX launcher: project-local DSH home so sessions and credentials
# never mix with the user's normal DSH environment.
$env:DSH_HOME = Join-Path $projectRoot '.dsh-home'
if (-not $env:DSH_TELEMETRY_MODE) { $env:DSH_TELEMETRY_MODE = 'DISABLED' }
if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = '1' }

Push-Location $projectRoot
try {
    & $dshBin --profile headless --patch (Join-Path $projectRoot 'dsh\civ6.cordis.yml') $message
}
finally {
    Pop-Location
}
exit $LASTEXITCODE
