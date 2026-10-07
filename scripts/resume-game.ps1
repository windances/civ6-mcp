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
#   powershell -NoProfile -File scripts\resume-game.ps1 -HumanMilitary
#
# -DryRun prints the check and the task it would use, and launches nothing, so it is safe
# while a game is being played.
#
# -HumanMilitary appends the division of labour to the task: the human commands the military
# units, the Great Generals and the Great Admirals, and the session owns every other unit and
# the cities, the economy, the wonders and the research. It is a task, not a rule - see
# AGENTS.md ("-HumanMilitary splits the command of the match") for what actually enforces the
# wait, and why the wait cannot be a script the session runs itself.

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
    [string] $TaskPath = ".civ6-mcp-data\resume-task.en.txt",
    # The human commands the military units, the Great Generals and the Great Admirals; the session
    # owns everything else. Appends the division to the generated task - see the block further down.
    [switch] $HumanMilitary,
    # The human's option (2026-10-07): a won match stays playable. Without it a finished match is
    # refused in the task text, because a session launched into one has nothing to play (T385).
    [switch] $AfterVictory
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

function Add-DivisionOfLabour($TaskPath) {
    # The human commands the military units, the Great Generals and the Great Admirals; the session
    # owns every other unit, and the cities, the economy, the wonders and the research.
    #
    # This is a task and not a rule, so it is the weakest rung of the enforcement ladder in
    # `docs/military-strategy-coverage.md`. Nothing mechanically stops a session that ignores it.
    # What the appended text can do, and does, is give the session a **defined place to stop**:
    # `.tools/wait-for-human.py` is that wait made explicit rather than improvised.
    #
    # The text must not claim `end_turn` refuses while a unit has movement - it does not.
    # `src/civ_mcp/end_turn.py:3613-3643` auto-resolves an `ENDTURN_BLOCKING_UNITS` blocker via
    # `_sweep_unmoved_units`, which fortifies combat units and skips the rest, and the turn advances.
    # A session told the opposite would call `end_turn`, lose the human's whole turn to the sweep and
    # never see a warning. The wait is the only guard, so the text says so.
    #
    # Written as ASCII on purpose. The task file is an English one and carries no BOM; this text is
    # pure ASCII, so appending ASCII bytes cannot damage it. PowerShell 5.1's `-Encoding UTF8` is
    # avoided because it emits a BOM on some append paths, which would land mid-file.
    #
    # Returns $true when it appended and $false when the task already carried the block. A real run
    # regenerates the task from the facts first, so the append normally lands on a fresh file; but
    # `-TaskFile` skips that regeneration, and a second run against it would otherwise append a
    # second copy of the same text.
    $marker = '## Division of labour: the human commands the military'
    # Guard the path before `Select-String` sees it: with `$ErrorActionPreference='Stop'` a missing
    # file there is a terminating error from inside the function, so `-DryRun -HumanMilitary
    # -TaskFile <missing>` died with a raw "Select-String : cannot find path" and printed no preview
    # at all (measured 2026-10-05). The real path already refuses earlier, at `Resolve-Path`.
    if (-not (Test-Path $TaskPath)) {
        throw "no task file to append the division to: $TaskPath (check -TaskFile / -TaskPath)"
    }
    if (Select-String -Path $TaskPath -SimpleMatch -Pattern $marker -Quiet) { return $false }
    $division = @'

## Division of labour: the human commands the military

The human directs the military units, the Great Generals and the Great Admirals. The agent is
responsible for every other unit, and for the cities, the economy, the wonders and the research.

**Do not move a military unit. Do not move a Great General or a Great Admiral.** A military unit is
anything with a `combat_strength` above zero; a Great General or a Great Admiral is a Great Person of
that class - and it has no combat strength, so the first test alone does not catch it. Leave them
where they stand and say what they could do.

**Everything else is yours**: builders, settlers, traders, every Great Person that is not a Great
General or a Great Admiral - the Great Scientists and the Great Merchants included - every city's
queue, the economy, the wonders and the research. An idle worker, an empty queue and a treasury nobody
is spending are your failures, not the human's.

**You move first, every turn; the human moves after you.** The turn opens with your half: read the
board, order every unit and every city queue you own, satisfy the rules that are yours, and only then
wait for the human's military units and commanders. Do not wait first and act afterwards - a turn where
you sat on the gate while the human had not moved yet is a turn of yours thrown away. The human's orders
come after yours, so your half has to be finished before you start watching the gate.

**`get_notifications` answers "is my half done?" for you.** Every call appends a `WHOSE MOVE|` line:
the units that can still act, split into the human's (military units, Great Generals, Great Admirals)
and your own. It also writes the same split to `agent-half.txt` in the run directory beside the
heartbeat, which is what the human reads to know when it is their turn. `agent working` means the units
still holding the turn are yours - order or `skip` them. `your move` means your half is finished and
the turn is waiting on the human. **`ready to end` is the third state, and it means the human is done
- end the turn.** No unit on either side can act, so the units blocker is down; any unit that *can*
still act raises that blocker, so its absence is the human's own "I have finished this turn". Call
`end_turn` with the five diary reflections. **`UI.CanEndTurn()` is not this fact**: it is true while
the blocker is still up, so read the blocker.

**A stop request rides your tool results as well, and honouring it is how you exit.** If the human
wants the session to stop, `scripts\stop-agent.py` writes `stop-request.json` beside the heartbeat;
from then on every successful tool result ends with a `STOP REQUESTED|` line, and the file records when
it reached you, so "told and did not stop" is visible from outside rather than guessed. When you see
it: finish your own half, then

  * **if nothing is holding the turn**, `end_turn` with the five diary reflections, and stop;
  * **if the human's units are still holding it**, leave the turn exactly where it is - do not end it
    and do not order their units - and say in your closing message that this turn's reflections could
    not be written, because `end_turn` is what writes them.

Either way: start no new turn, and leave a closing report. A request you do not honour is cleaned up
for you by `scripts\stop-agent.py --wait`, which runs `civ6-clean.ps1 -KeepGame` - and that is a kill,
so the difference between the two paths is exactly the diary entry and the report.

**`end_turn` will not wait for the human - it discards their turn.** An `ENDTURN_BLOCKING_UNITS`
blocker is not bounced: `_sweep_unmoved_units` (`src/civ_mcp/end_turn.py`) fortifies combat units and
skips whatever still has moves, then the turn advances. Any military unit the human has not finished
with is fortified where it stands. There is one exception and it is not a safety net: a unit with a
*legal attack* makes `end_turn` bounce with `UNUSED ATTACK at end_turn: ...`, which only helps while an
attack happens to be pending.

**So the wait is yours to enforce, and it comes before `end_turn`, not after.** Once every unit you own
is ordered, **ask the game whether the turn can end - do not count units.** Poll `get_notifications`:
while any unit still has moves the game raises

    Command Units  ->  Units have moves remaining

and it drops that entry the moment the turn can end. **That entry is the test** - when it is gone, the
turn can end, so call `end_turn`. While it is there, wait **exactly 30 seconds between reads** (human
instruction 2026-10-06): call `get_notifications`, then `Start-Sleep -Seconds 30` in a shell - it costs
nothing and needs no tuner - then call it again, and repeat. That is a fixed 30-second cadence, not a
tighter loop: polling faster buys no information and spends the context this turn still needs, and
waiting longer only delays a turn you are both playing. Re-reading `get_units` is still worth doing,
because that entry covers the human's units **and yours**, and the two need opposite answers: the
human's is waited for, and one of yours is yours to order. `get_units` now marks the units that cannot
act - `[HOLD]` (a `skip`, `ACTIVITY_HOLD`), `[SENTRY]` (`alert`, `ACTIVITY_SENTRY`), `[OPERATION]` (a
route or an improvement), `[fortified n]`, `[cannot act]` - and prints the engine's own `ready_to_move`,
so a unit holding movement is not by itself a unit with something to do. Measured on turn 346: 39 units
held movement and only 14 could still act, so a movement count waits on units that are already
finished.

**A unit under a whole movement point is judged as skipped** (human instruction 2026-10-04): a fraction
of a point buys no tile, so it is in neither half's list and does not hold the turn open. Measured T352,
a `UNIT_MECHANIZED_INFANTRY` at 0.2 moves kept the report saying `YOUR MOVE` after the game's own units
blocker had already dropped - the fraction is the whole reason it looked like somebody's pending work.

**Do not use `UI.CanEndTurn()` as the test.** It is true *while* the units blocker is up - measured on
turn 337, three consecutive reads all read `CANEND|true` with `ENDTURN_BLOCKING_UNITS` raised - because
it means "the End Turn button is pressable", not "no unit has moves". The MCP's own `end_turn` depends
on exactly that (`UI.CanEndTurn()=true despite blockers ... proceeding`). A wait built on it releases
immediately and hands you back the silent sweep. The notification is the signal; that boolean is not.

**Other entries under Action Required are yours, not the human's** - an empty queue, an unspent
promotion, a governor point. Fix them or the turn will not end, and waiting will not clear them.

**Do not try to run the wait as a script.** `.tools/wait-for-human.py` exists for the human and for an
observer, and it **cannot** run inside your session: FireTuner serves one client and your own MCP
server holds it, so a second client connects and then dies with `ConnectionError:
GameCore_Tuner/InGame states not found` (measured, with a connection held open in both an idle and a
busy state). The reads through your own tools are the only view you have of the game, and they are the
ones that work.

**Under this division, never call `skip_remaining_units()` at all - not even without `force=True` -
and never call `end_turn` while a commander can still act.** The tool is empire-wide: it fortifies
combat units and skips everything else, and the human's half is not yours to close. Measured
2026-10-04, a session that called it anyway (non-force, because nothing had a legal attack) got back
`FORTIFIED|1 fortified, 2 healing; SKIPPED|12` - and two of those were the human's units. Order and
`skip` your own units one at a time instead. `end_turn` discards movement silently, which is worse.
Waiting here is the correct action, not a failure to act.

**Gold is held for the front.** Keep the treasury ready and report when an upgrade is available and
affordable; the human decides which unit takes it.
'@
    Add-Content -Path $TaskPath -Value $division -Encoding ASCII
    return $true
}

$state = Get-Handoff
Show-Verdict $state

if ($DryRun) {
    $task = if ($TaskFile) { $TaskFile } else { $TaskPath }
    $taskFull = Join-Path $projectRoot $task
    if (-not $TaskFile) {
        $taskArgs = @($handoff, '--task', $TaskPath, '--turns', $Turns)
    if ($AfterVictory) { $taskArgs += '--after-victory' }
        if ($Rollback) { $taskArgs += '--rollback' }
        $null = & $python @taskArgs 2>$null
    }
    # The preview has to be the task a real run would hand over, division included - otherwise
    # -HumanMilitary -DryRun reports a task the session would never receive.
    if ($HumanMilitary) { $null = Add-DivisionOfLabour $taskFull }
    Write-Host ''
    Write-Host "--- the task this would hand to a session ($task) ---"
    Get-Content $taskFull | ForEach-Object { Write-Host $_ }
    if ($HumanMilitary) {
        Write-Host '--- the division of labour is in the task above ---'
    }
    Write-Host '--- dry run: nothing launched ---'
    # The preview's exit code mirrors the verdict: 0 only when a real run could launch. It used to
    # exit 0 even for TUNER_BUSY, which reads to a scripted caller as a green light (measured
    # 2026-10-08, while another session held the tuner).
    exit $(if ($state.verdict.ready) { 0 } else { 3 })
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
    if ($AfterVictory) { $taskArgs += '--after-victory' }
    if ($Rollback) { $taskArgs += '--rollback' }
    & $python @taskArgs 2>$null | ForEach-Object { Write-Host $_ }
}
$taskFull = (Resolve-Path (Join-Path $projectRoot $taskRelative)).Path
if (-not (Test-Path $taskFull)) { throw "the task was not written: $taskFull" }

if ($HumanMilitary) {
    if (Add-DivisionOfLabour $taskFull) {
        Write-Host 'DIVISION  the human commands the military; the task tells the session to wait for them'
    } else {
        Write-Host 'DIVISION  the task already carried the division; left as it was'
    }
}

Write-Host ''
& $launcher -TaskFile $taskFull
exit $LASTEXITCODE
