# TEMP TASK 033 - attempt A2, third phase: the assault on the city-state, T66 to the attempt's end

added:     2026-09-29 (human instruction: 继续)
expires:   turn 85 - 30 turn(s) from T66, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: turn 80 is reached, or a city_action reply reads KEEP| - whichever comes first
overrides: task 032, whose finish line was met at T48 when the first siege order was read, and task 031's
           stop-at-T40 instruction, consumed long ago. 031's scope, its target and its own finish
           line (a city kept, or T80) stay in force, and this file adds no other exception.
scope:     this match only: attempt A2's assault on the city-state 031 names, from the position the game stands
           on (T66, at war with player 6)

## WHERE YOU ARE (read this first)

The game stands at **T66** and **you are at war with 耶路撒冷 (player 6)**. That war was declared by a
player operation - the fix for the defect this attempt found: `send_diplomatic_action` opened a
diplomacy session to declare war, a city-state has none to open, and the reply read
`WARN:WAR_UNCERTAIN` while nothing happened. `build_send_diplo_action` now declares a minor civ's war
the way the game's own declare-war popup does, and the state was verified from the game:
`IsAtWarWith(6)` is true.

What the army is and what is left:

- **Three Catapults** (西安's, 太原's and one more), four Warriors, three Archers, a Heavy Chariot.
  When the war was declared the two leading Catapults stood on the firing tiles (50,24) and (51,23) -
  distance 2 from the city - with the melee on the ring and the Archers in support.
- **The target's HP pool reads 200**; its **walls have never been read by any tool**. Read them with the
  first shot and put the number in the diary.
- The attempt ends when **a city is kept** or the game reaches **T80**.

## The one measurement left

Q3 - *the first city kept by T80* - is the experiment's last open question. The others are answered: Q1
falsified at T60 (on the table's `ram` and `ranged` slots), Q2 held at T48, Q4's gate opened at T60. So:
fire the siege train every turn it can fire, keep a screen in front of it (`screen-the-siege` was
failing - `tactics/05` owns that rule), judge damage from `SIEGE PROGRESS` and a later read rather than
from the immediate reply, and resolve the city with `city_action` when the pool empties.

## Start

1. `get_game_status` - it must answer `in_game`. Never launch the game and never load a save; both are
   the human's calls. Then `get_diary` and one `scripts\orient.py` read.
2. **The T41 blockers are already cleared** (dedication `COMMEMORATION_SCIENTIFIC`, the pantheon
   锻造之神 founded at T41, and the volcano's damage healed and repaired). Do not re-do them. The
   pantheon guard is fixed in the Lua this session loads.
3. Still owed from the earlier half, if it is cheap: the target's walls/HP/garrison read, and the
   `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` lines every ten turns with the `10-TURN REVIEW`'s
   three questions answered in the diary.

## The finish line, and what to leave behind

- The attempt ends exactly as task 031 says: **a city is kept** (`city_action` reply reads `KEEP|`) or
  the game reaches **T80**. `expires:` is T85.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run sacred-garnet-vault-35,pale-pearl-aqueduct-92,<this session> --from 1 --to <last turn> --step 10 --verdict --questions a2 --save docs/experiments/A2-final.json`
  **Every session name is needed**: this attempt spans a resume (T1-T40 in `sacred-garnet-vault-35`,
  T41-T65 in `pale-pearl-aqueduct-92`, and this one from T66), and the instrument attributes diary rows
  by session time - naming only the current session drops every earlier turn and the report starts at
  T66. `--questions a2` answers this attempt's own Q1-Q4. Then
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A1-T40.json docs\experiments\A2-final.json`,
  complete `docs/experiments/002-attempt-A2.md` (the T40 table and the T48 section stay; the end table
  goes below them) and update `docs/experiments/RETRO-2026-09-29.md` with A2's final half - whether the
  city was taken, what the walls read, and what the assault cost.
- Then retire **this file and 031 together** (031's window ends with the attempt - a city kept or T80),
  and say in the diary's `tooling` line which turn each ended on.

## Honesty notes this attempt has already paid for

- The combat reply prints the **pre-attack** HP (`enemy HP:72 -> 72/100` on a landed hit): never
  conclude from the reply that an attack failed, and never re-issue an attack on the strength of it -
  one legal attack was thrown away earlier in this attempt with `force=True`.
- Judge a city's progress from `SIEGE PROGRESS` and from a **later** read, never from the immediate
  reply; the blocks also say what the walls are.
- Your own `ESTABLISHMENT:` line is checked against the record: write **both** numbers
  (`melee 2 target / 4 held`) so a target-vs-held confusion is not scored as a mistake.
- The diary is shared with A1 and the instrument attributes rows by session time, so a turn your session
  did not play is not yours to describe.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "attempt A2, third phase: the assault on the city-state, T66 to the attempt's end" --instruction 继续 --why "take the city-state the attempt has besieged since the war was unblocked" --done-when "turn 80 is reached, or a city_action reply reads KEEP| - whichever comes first" --overrides "task 032, whose finish line was met at T48 when the first siege order was read, and task 031's stop-at-T40 instruction, consumed long ago. 031's scope, its target and its own finish line (a city kept, or T80) stay in force, and this file adds no other exception." --scope "this match only: attempt A2's assault on the city-state 031 names, from the position the game stands on (T66, at war with player 6)" --expires-turn 85 --body-file .tmp\a2-assault-body.md --cn @.tmp\a2-assault-cn.md
     at: 2026-09-29T17:33:35+08:00
     chinese backup: prompts/tasks/cn/033-attempt-a2-third-phase-the-assault-on-the-city-state-t66-to-the-attempt-s-end.cn.md
-->
