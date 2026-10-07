# TEMP TASK 052 - Playing on after a victory: an option, not a stall

added:     2026-10-08 (human instruction: 请增加一个选项，游戏胜利后仍然继续玩。（2026-10-07 人类指令：胜利不再是停止条件，要有一个明确的开关让会话继续打。）)
expires:   turn 406 - 20 turn(s) from T386, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 3 tests in tests/test_handoff.py over the victory branch, and scripts/resume-game.ps1
           -AfterVictory -DryRun prints a task whose first paragraph says the match is won and that
           this session continues it
overrides: the 'a victory ends the session' default and the handoff stop condition: with this flag a won match
           is playable work
scope:     src/civ_mcp/handoff.py's victory detection and task_text branch, the scripts/resume-game.ps1 switch,
           their docs and tests; no change to how a live match is handed over

## Why this exists

At T385 the match reported `GAME OVER - VICTORY (Culture)`. Nothing in the tooling noticed:
`scripts/resume-game.ps1` still generated a "play up to 100 turns" task, the session it launched
found the engine would not advance a turn, and the task published for the conquest that followed was
retired as expired minutes later. The victory is in `get_game_overview`'s own output - the preflight
reads the turn off the save and never reads that line.

The human's instruction is that a victory must not be a stop condition: there has to be an explicit
way to keep playing a won match (Civ VI allows it - the victory screen's "one more turn").

## What to build

1. **`src/civ_mcp/handoff.py`**
   - Detect the victory: the probe's `get_game_overview` output carries the `GAME OVER` line; put it
     in the facts/result as its own field (e.g. `result["victory"]`, `None` when the match is live).
   - `task_text(facts, result, turns=100, rollback=False, after_victory=False)`:
     - **victory and not `after_victory`** - the task must say the match is already won, that there is
       nothing to play, and to stop and report. That is the guard the T385 handoff did not have.
     - **victory and `after_victory`** - the task must say the match is won and this session is
       continuing it deliberately, name the likely first obstacle (the victory screen may need
       clearing - `dismiss_popup`, then `.tools/whats-on-screen.py`, then the human clicking "one more
       turn" if the turn still will not advance), and keep the rest of the task unchanged.
   - Prefer the newest save's turn over `None` while you are in this function: measured 2026-10-08 at
     T387, a tuner-busy preflight wrote `found turn None` into the task text although the same report
     had already read `AutoSave_0387 holds T386` (remember the `AutoSave_NNNN` offset of one).
2. **`scripts/resume-game.ps1`** - a switch, e.g. `-AfterVictory`, that (a) reaches `task_text` so the
   generated task carries the paragraph above, and (b) appears in the `-DryRun` preview so the human
   can read what it would hand over. The refusal path must still refuse a `TUNER_BUSY` state, and
   `-DryRun` should mirror the verdict in its exit code rather than always exiting 0.
3. **Docs** - `scripts/README.md` (+ its `.cn.md` backup) documents the switch; `AGENTS.md` (+ the
   `.cn.md` backup) gets one line in Game Recovery: a finished match is reported by the preflight and
   `-AfterVictory` is how a session continues one.
4. **Tests** - `tests/test_handoff.py`: `task_text` with a victory and no flag says stop (and does not
   say "play for up to 100 turns"); with the flag it says continue and names the screen step; a
   `None` probe turn renders the save's turn, never `None`. `tests/test_resume_game_division.py` is the
   pattern for testing the PowerShell switch's appended text.

## Done when

`scripts/resume-game.ps1 -AfterVictory -DryRun` prints a task whose first paragraph says the match is
won and that this session continues it, and `tests/test_handoff.py` holds >= 3 tests over the victory
branch (refuse without the flag, continue with it, and no `None` turn). Retire this file the turn
those hold and record in the diary which turn the victory was reported and whether it cost a session.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Playing on after a victory: an option, not a stall" --instruction @.tmp/task052-instruction.txt --done-when "count >= 3 tests in tests/test_handoff.py over the victory branch, and scripts/resume-game.ps1 -AfterVictory -DryRun prints a task whose first paragraph says the match is won and that this session continues it" --overrides "the 'a victory ends the session' default and the handoff stop condition: with this flag a won match is playable work" --scope "src/civ_mcp/handoff.py's victory detection and task_text branch, the scripts/resume-game.ps1 switch, their docs and tests; no change to how a live match is handed over" --why "add an option to keep playing after a victory" --turns 20 --body @.tmp/task052-body.txt --cn @.tmp/task052-cn.txt
     at: 2026-10-08T00:43:40+08:00
     chinese backup: prompts/tasks/cn/052-playing-on-after-a-victory-an-option-not-a-stall.cn.md
-->
