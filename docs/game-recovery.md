---
title: Game Recovery — the operational detail
---

Moved out of `AGENTS.md` on 2026-09-26, when that file crossed the 65536-byte injection budget
and its tail stopped reaching a session. Nothing was reworded: this is the section as it stood,
and `AGENTS.md` keeps only the three lines that must be in front of a session every turn.

## Game Recovery

**Handing the match to a fresh session is one command, and it is not the agent's:**
```
scripts\resume-game.ps1            # check, tell the human what to do, stop
scripts\resume-game.ps1 -Wait      # ... or wait for the human's load, then launch a session
scripts\resume-game.ps1 -Rollback  # the human deliberately loaded an earlier save
```
It runs `civ_mcp.handoff` first, which reads only **passive** signals — the process list, the
OS TCP table's owner for the FireTuner port, the heartbeat file, and the saves on disk with
the turn each file actually holds — so it can be run at any time, **including while another
session is playing** (the MCP's own `get_game_status` connects and reads the screen, which is
right when this process is about to act and wrong when asking must not disturb the answer).
It ends in one verdict: `not_running` (launch), `no_match` (load a save), `tuner_silent`
(started without EnableTuner), `tuner_busy` (another session holds the tuner), or `in_game`
hand it over. **It never launches and never loads** — that stays the human's call, which is
why the verdict's job is to say who does what. When it is `in_game` the session's task is
**generated from those facts** (`.civ6-mcp-data/resume-task.en.txt`), so no turn number or
save name in it can go stale.

**The two save families are numbered differently, measured 2026-09-26:** `0_MCP_NNNN` holds
turn NNNN, and the game's own **`AutoSave_NNNN` holds turn NNNN-1** (`0_MCP_0142` holds T142,
`AutoSave_0142` holds T141 — three pairs checked). So "the number in the name is the turn" is
true only of the MCP's files; comparing a loaded turn against an autosave's name is off by
one, and `scripts\turn-of-save.py "<path>"` prints what a save really holds before it is
loaded. Both families matter and neither is authoritative: "Continue Game" resumes whichever
file is **newest by time**, so that is what the handoff recommends, and a newer file that is
*not* the furthest position is the rollback smell worth flagging.

**`0_MCP_NNNN` broke that invariant in the field, so the file is asked first.**
Measured 2026-09-27 on 109 saves: the `AutoSave` family was consistent in 100 of 100 (name = turn
plus one), while **four of the nine newest `0_MCP` files were named one turn low** —
`0_MCP_0206` holds T207, `0_MCP_0209` holds T210, `0_MCP_0212` holds T213, `0_MCP_0215` holds T216.
The cause is in `end_turn`: the name is built from the same post-advance read that sometimes prints
`Turn 203 -> 203` (T200/203/206/209/212/215 all did). Two things now hold the line: `end_turn`
reads the saved file's turn and **renames it** when the name disagrees, and both the agent's expiry
clock (`tests/test_temp_tasks.game_turn`) and the handoff read the turn **from the file**
(`handoff.save_turn`, about a tenth of a second per save) with the name only as a fallback.

**Ask where the game is before touching anything:**
```
get_game_status   # not_running / starting / in_game / leader_screen / main_menu / loading / tuner_busy
```
It answers with the state, the turn, and a `NEXT:` line, so a recovery does not have to be
inferred from whichever call happened to fail. Two answers change what you do: `in_game`
means a game is already playable (nothing to launch or load), and `tuner_busy` means another
process holds the FireTuner connection — FireTuner serves exactly one, so no call from here
can work while that one lives. Waiting does not help: stop that process with
`scripts\civ6-clean.ps1`, or keep playing in its session.

**MCP autosaves:** `end_turn` automatically saves every turn as `0_MCP_NNNN` (last 5 kept). These are your primary recovery points.

**Two recovery traps, both measured on 2026-09-25 (five crashes/hangs in one session):**

1. **`0_MCP_NNNN` names collide across rolled-back branches, and a rollback does not delete the
   abandoned branch's files.** Loading `0_MCP_0122` by name silently loaded the *other* branch's
   position — same turn number, different board (18 units, two Trebuchets, no Moscow), so the turn
   check passed and only reading the units back caught it. **After any rollback, recover with the
   game's own per-session autosave, `AutoSave_NNNN`** (in `Saves/Single/auto`, OneDrive-redirected
   on Windows: `C:/Users/<user>/OneDrive/文档/My Games/Sid Meier's Civilization VI/Saves/Single/`),
   choosing the newest one at or before the lost turn by modification time. The save-list Lua probe
   (`.tools/probes/save-list.lua`) prints names, paths and times so the two can be told apart.
2. **A turn that will not advance is not necessarily a hang.** Twice it was the game waiting for a
   mouse: once parked on the leader screen after a load (the CONTINUE click was landing on the
   browser, because `_click` injects at screen coordinates and a fullscreen game must be in front —
   fixed by focusing first, `_bring_to_front`), and once behind a natural-disaster popup plus twenty
   `InvitePopup`s. **Read the screen (`.tools/whats-on-screen.py`) before restarting**, and try
   `dismiss_popup` before relaunching.

Launching from a shell may need full filesystem access: the game writes `%LOCALAPPDATA%\Firaxis
Games` and its OneDrive save directory on start, and a confined launch produces no process at all.

**Re-orient in one read: `scripts\orient.py`.** After a rollback (or any cold start) the rule is
"rebuild every fact from the game", and doing that through five separate reads is how one of them
gets skipped. One connection prints the game overview, units, cities, tech/civics, policies,
diplomacy (met civs only), resources, governors, trade routes, builder tasks, city-states,
victory/demographics, religion, great people, pantheon and notifications — compact by default,
`--full` for the raw dataclass dump, `--only a,b` to narrow, `--maps` for the narrated map.
Two companions: `scripts\turn-of-save.py "<path>"` prints the turn a save actually holds *before*
you load it (a manual save carries no turn in its name and the save parser cannot always read one
out of the file — the T59 rollback had to take the game's own filename on faith), and
`scripts\probe-tile.py x,y` prints the raw tile record (terrain, feature, resource, owner, units),
which is what settled that (58,30) held no *visible* resource at all.

**Unattended development turns: `scripts\auto-turns.py --turns N`.** It dispatches Builders along
the task list, keeps every city's queue filled from a per-city plan, advances research and civics
from a priority list, takes the pantheon/dedication/governor offers, buys a Builder above
`--buy-at` gold, and writes the same diary rows the operator writes (with factual, not
interpretive, reflections). It **never** attacks, declares war, clears a barbarian camp, moves
toward an enemy, or touches diplomacy — and it stops and hands back the moment a non-barbarian
enemy is within three tiles or a war starts, which is where the tactics files apply. Run
`--dry-run` first: it prints the orders it would issue and touches nothing.

**Load by name** (preferred — no `list_saves` needed):
```
load_game_save("0_MCP_0079")  # find it in the game's own save list and load it
get_game_overview              # verify load
```
It works from the main menu as well as in-game: with no game loaded the same two calls run in
the game's own FrontEnd load-screen state (`LoadGameMenu`), so nothing has to be clicked and no
window has to be in front. It then lands the load itself — waits for the leader screen, clicks
CONTINUE, and reads the turn back — so the reply names the turn actually loaded and a wrong one
comes back as `WARNING: the game reports turn N, but '<save>' holds turn M`. OCR menu navigation
is the fallback for a save the game's list does not carry.

**When the game hangs** (AI turn loop):
```
restart_and_load("0_MCP_NNNN")   # kill + relaunch + load (~90s)
get_game_overview                 # verify load
```

**Turn regression detection:** If you accidentally load a wrong save (e.g. the T1 scenario save instead of your autosave), `end_turn` will emit a CRITICAL warning with the correct autosave name to reload.

Other tools: `list_saves`, `load_save(index)`, `kill_game`, `launch_game`, `load_save_from_menu(name)`.
Save names omit the extension: `"AutoSave_0221"`. Writing `"AutoSave_0221.Civ6Save"` is accepted
too, and stripped, because the game's own save list carries it.

**One session at a time.** `kill_game` and `restart_and_load` refuse while another session is
playing (they name the pid holding the FireTuner connection or writing a recent heartbeat), so
a recovery cannot throw away a position someone else is mid-turn in. Pass `force=True` only
when you know that session is dead. Loading a save the game is already sitting on is not a
load: `load_game_save` answers "Already loaded" from the current turn instead of clicking
through a main menu that is not on screen.

**And one *diagnostic* client at a time, which is the same rule from the side that bit us.**
FireTuner hands its listener to the first client that accepts it, so **a probe you run to check
the tuner takes the connection away from the session that is playing.** Measured 2026-09-30: a
session sat at `phase: playing` with a heartbeat three minutes stale and would not advance while
repeated `list_saves`/state probes were being run against the game from outside; the probes read
an **empty Lua state list** (which reads exactly like "the tuner is broken"), and the moment the
probing stopped the session reconnected on its own and played. **While a session plays, read files
only** - the log, the heartbeat, `.tools/whats-on-screen.py` - and let the session make the tuner
calls; if you need a fact from the game, ask the session. Two corollaries worth keeping: an empty
state list from a probe is evidence about *your* connection, not about the game; and after a save
load the game may listen on **4319** alone, which `GameConnection` now walks as a fallback
(`tuner_port_candidates`, 4318 then 4319).

**A load that has already landed can still be retried for ten minutes, and that is not a hang.**
Measured 2026-09-30 loading the experiment's shared start (attempt A8): the game reached **turn 1** and
the fresh-start advisor - `.tools/whats-on-screen.py` read `TURN 1`, `CHOOSE RESEARCH`, `CODE OF LAWS`,
no leader screen - while `load_game_save` went on **re-clicking CONTINUE about ninety times over nine
minutes**, each attempt logging `Continue: the leader screen is gone (unrecognised (N text boxes)) - the
click took` and then `Discovered 0 Lua states (GameCore=None, InGame=None)`, with **4318 refusing and
4319 answering**. It returned by itself and the session played. **So the three things to do in that
window are all "nothing":** do not kill the session (it is inside the call, not stuck), do not conclude
failure from the log's silence (the call logs only when it returns), and do not start a second session -
verify the position from outside with `whats-on-screen.py`, which touches no tuner. **The clicks are also
harmless in the case that matters**: the position they were aimed at was already the one being loaded,
and the proof was the session's own first read after recovering - `No technology being researched!` - a
stray click that had chosen a research would have shown one. Two facts to carry: the `0 Lua states` line
belongs to the *landing* window and not to the session's connection, and a load's real success signal is
the turn the screen reads, not the call's own reply.

**And after a real `HANG`, a whole run of failures is one screen: the leader intro.** Measured
2026-09-30 on the same attempt, at T6, in this order:

- `end_turn` answered **`HANG:6:0_MCP_0006`** - the AI-turn stall, not a popup;
- `get_game_overview` answered **`GameCore_Tuner/InGame states not found`**;
- `load_game_save` answered **`FAILED: Could not find 'Load Game' button`**, twice;
- `dismiss_popup` answered **`No popups to dismiss`**;
- and the game was, through all of it, sitting on the **loaded game's leader intro** (`CHINESE EMPIRE`,
  `QIN (UNIFIER)`, a CONTINUE button) - a screen **Lua cannot see**, so every tool above was answering
  about a state the game had already left.

**With nothing done it resolved**: the next `get_game_overview` read `Turn 6 | China (Qin (Unifier))`
and play resumed. So **that quartet of messages is not evidence that a recovery failed** - it is the
leader-intro window, and it is the one state where reading the screen is not a fallback but the only
instrument. `.tools/click-continue.py` **without `--click`** is the safe check: it grabs pixels with
`PIL.ImageGrab` (sending the game nothing), never calls `SetForegroundWindow`, reports whether the game
is parked on CONTINUE, and changes nothing. Pass `--click` only when it finds the button and the game is
the foreground window. **And prefer waiting first**: this window closed by itself in about five minutes,
so a session that is alive and mid-recovery should be left to it - the helper is for the case where it
has stopped, not for the case where it is slow.

**The AI-turn stall is reported at two minutes, and the MCP no longer restarts the game by itself
(2026-10-04).** The state is the one the screen shows as "other players are taking their turn, please
wait"; `end_turn` polls through it with no blocker, no diplomacy session and no popup, and from
2026-10-04 it gives up after `AI_TURN_STALL_REPORT_S` = **120 s** instead of the old ~590 s, answering
`HANG:<turn>:<save>|... Waited <n>s. The game has held the AI-processing state past the two-minute
limit, and past that point it does not recover by waiting: it needs a restart.`

- **Human rule (2026-10-04): two minutes in that state and the game is restarted, by the human.**
  Measured T354: two stalls (`22:13:34`, `22:56:21`) each burned the whole old budget, and the answer
  arrived minutes after the game had visibly stopped with nothing in it saying what to do.
- **Report early rather than self-restart.** The MCP used to kill and relaunch the game up to three
  times before anyone was told (`server.py`, `HANG RECOVERY`). That is off by default now: a reload
  throws away everything the running turn had already done - the T354 reload reset Korolev's
  activation, Xi'an's launch and the builder orders - and it did so while nobody was watching. The
  branch is still there behind `CIV_MCP_HANG_SELF_RESTART=1` for an unattended run.
- **The order is fixed: stop the session first, then restart, then reload.** The session does not
  retry into a restart. On the `HANG` message: `scripts\stop-agent.py` (it writes the stop request,
  and `--wait N` falls back to `civ6-clean.ps1 -KeepGame`), then the game is restarted, then the match
  resumes from the save the message names with `load_game_save("<save>")`.
- **Re-focusing a backgrounded window still happens before any of this**, and it is not a restart:
  Civ VI does not advance an AI turn while its window is in the background, so `server.py`
  re-focuses and retries once. Measured T354 `22:56:20`: the window was behind Chrome
  (`hang_diagnosis.jsonl`), which is what made that stall look identical to a hung AI.
- **What the diagnosis file holds** is unchanged (`hang_diagnosis.jsonl`: window rect, focus,
  foreground window, first OCR lines), and with the self-restart off it is now the *only* thing that
  touches the game on a stall - which is the point: the evidence survives.

**A rollback can also be taken as a fresh start (2026-10-05).** `rollback-to-turn.py` deliberately
*restores the past* - the diary up to the boundary, the tasks already in force, the rules met before
it - because that history is what makes the replayed turns make sense. When the human wants the
opposite, the same loaded position played on with no memory of how it got there, that is
`scripts\fresh-start.py <turn>`:

- it forgets this match's diary (the run's copy **and** the legacy root copy under `.civ6-mcp-data\`),
  the achieved-goal state (`runs\<run>\turn-checks-state.json` and the legacy root one), the run's
  session scratch (`heartbeat.json`, `agent-half.txt`, `stop-request.json`), and the `achieved T...`
  notes in `prompts/checks/turn-checks.md` **that belong to this match** - and for each note it puts
  the rule body back from `prompts/checks/archive/`;
- it resets the manifest's played-to turn to the turn being resumed at, so the handoff banner and the
  turn-regression check start from there;
- it **keeps** every rule body (the re-armed ones included), the notes keyed to *another* match (the
  check file is shared by every match in this checkout), the temporary tasks in force (print, do not
  silently withdraw - the `temp-task.py retire` command is in the plan), and every archive under
  `branches/`;
- everything it forgets is copied first, tree and all, to `branches\fresh-start-<stamp>\files\...`
  with a `manifest.json` and a `README.txt`, so the operation is reversible by copying the tree back;
- **it refuses while a session is playing** (`stop-agent.py`'s own liveness rule), because that session
  rewrites the diary and the heartbeat within one turn - stop it first, then forget, then start the
  session with `resume-game.ps1 -Wait`.

**Why a note is re-armed rather than simply deleted.** The check file's contract, and the suite that
holds it, is that a retired goal is **either live or traceable**: `test_every_retirement_trace_still_resolves_to_its_archived_block` asserts the traces are not empty, and `..._wonder_obligation_is_live_or_recoverable` asserts the wonder goal is live or recoverable. So "the achieved note goes" has to mean "the rule is live again" - which is also the plain reading of the human's instruction (the note goes, the rule body stays). Measured 2026-10-05: stripping the two notes without re-arming turned seven tests red (the two above, the ram-tower pair that reads the restored file, and three that read the shipped file for a goal to achieve). One consequence is worth naming: after a fresh start the file can hold **no trace at all** - every goal this match retired is live again - and that first guard is a `pytest.skip` for exactly that state, so a real orphan is still caught while a correct empty file is not reported as a failure.

Measured 2026-10-05: a rollback to T352 had left the session waiting on one 0.2-movement unit, and the
fresh start cleared the diary (turns 1..287 in the run copy, 289..354 in the legacy root one), removed
two achieved notes and re-armed their rule bodies - one note keyed to this match, one un-keyed, and an
un-keyed note counts as this match's exactly as `turn_checks.restore_foreign_games` reads it - and left
the three temporary tasks in force. The first real run, on the deliberate `fresh-start.py 352 --apply`,
found one note left and re-armed it (`dynasty-cycle-wonder`), reset the manifest to T352, and left the
check file with no trace at all - the state the skip above covers. Two defects were found while building
it: the first version flattened the backup, so two same-named diary files collided and only the last
survived (the backup now mirrors the tree, and a test pins it); and its test suite called `main()` with
no argument, so a test run forgot the real match's memory instead of a temporary copy's (`main()` takes
its root now, and a test pins that too). The diary segments it removed are still recoverable: the copy
taken before each run is in `branches\fresh-start-<stamp>\files\`, and older archives
(`branches\abandoned-*\backup-*\diary_china_-1894041591.jsonl`) hold the match's diary as it stood on
2026-09-20 through 2026-09-28.
