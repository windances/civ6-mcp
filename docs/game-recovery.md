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
