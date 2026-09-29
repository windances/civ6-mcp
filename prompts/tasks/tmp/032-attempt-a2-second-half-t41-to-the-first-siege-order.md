# TEMP TASK 032 - attempt A2, second half: T41 to the first siege order

added:     2026-09-29 (human instruction: 继续)
expires:   turn 85 - 30 turn(s) from T41, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: turn 80 is reached, or a set_city_production reply reads PRODUCING|UNIT_CATAPULT (with that turn
           written into docs/experiments/002-attempt-A2.md), or a city_action reply reads KEEP| -
           whichever comes first
overrides: task 031's stop-at-the-end-of-T40 instruction, and only that: the checkpoint it names is behind the
           game, which stands at T41. 031's scope, its finish line and its target stay in force, and
           this file adds no other exception.
scope:     this match only: attempt A2 continued from the position the game stands on (T41, save 0_MCP_0041),
           running 031's settings, doctrine and target unchanged

The T40 checkpoint is behind the game - it stands at **T41**, and task 031's stop
instruction has been consumed. This half exists to answer the one question the checkpoint
could not: **H1/Q2, the first real test of "siege first"**. Nothing else in the attempt
changes: the settings, the save, the doctrine (`tactics/01` + `tactics/08`) and the target
(耶路撒冷, the city-state ten tiles west) are 031's, unchanged.

## Start

1. `get_game_status` - it must answer `in_game`. Never launch the game and never load a
   save; both are the human's calls. Then `get_diary` and one `scripts\orient.py` read.
2. **Clear the two T41 blockers before anything else**: an era **dedication** is pending
   (`get_dedications` -> `choose_dedication`), and the volcano inside 西安's borders
   erupted at the start of T41 (a Warrior and two Slingers damaged). Heal, repair, or
   replace - and say in the diary which you chose and why.
3. **The pantheon is available in this session.** The guard that made
   `choose_pantheon` fail for every call in the first half is fixed in the Lua this
   session loads (`src/civ_mcp/lua/religion.py`, `tonumber`), and the attempt has ~54
   faith unspent. The belief the first half intended was **God of the Forge** (+25%
   toward Ancient and Classical military units), which is this experiment's own subject -
   found it, and record the turn and the belief in the diary and in the record. If the
   guard still refuses at 25 faith, say so in the diary rather than working around it.

## The one measurement this half is for

**When Engineering lands, the siege train is ordered before any economy building.**
Engineering was in progress from T22 and the executor's own estimate put it at T44-T48;
it is the gate that both attempts died on.

- The turn Engineering completes, order **`UNIT_CATAPULT` x2** - in 西安 first, the
  second in 太原 if 西安's queue is long - **before** any Granary/Monument/Water
  Mill/Campus order.
- Write down, in the diary and in `docs/experiments/002-attempt-A2.md`: the turn
  Engineering completed, the turn each Catapult was ordered, and the first economy order
  after Engineering. **Those three turns are Q2's answer**, whether it holds or breaks.
- If gold allows and the queue is the constraint, buying a Catapult counts as ordering
  it - record which it was.

## The march, and the thing the checkpoint found missing

- The target is met but **its walls, HP and garrison have never been read by any tool**.
  Read them at first contact and put the numbers in the diary.
- Recon: this attempt built **no** recon unit and explored 7% against A1's 14%, so
  `tactics/07`'s Gate 0 stayed unsatisfied for a target it had already met. A scout or a
  spare cavalry unit working west is worth more than a sixth Slinger.
- The march: from ~T45 move the army to a rally point three tiles east of the target's
  ring so the shooting opens the turn the Catapults arrive. `get_staging_plan(50,22)`
  gives a usable ring census, distances and `TOO FAR` verdicts - **its `arrive T+1`
  column is not credible** (measured at T40: `arrive T+1` for a unit five tiles out) and
  no deadline is written from it.
- Every ten turns: the `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` lines, and the
  three questions of the `10-TURN REVIEW` answered in the diary with numbers.

## The finish line, and what to leave behind

- The attempt ends when a city is kept (`city_action` reply reads `KEEP|`) or the game
  reaches **T80**, whichever comes first. `expires:` is T85.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <this session> --from 1 --to <last turn> --step 10 --save docs/experiments/A2-final.json`,
  run `--compare docs/experiments/A1-T40.json docs/experiments/A2-final.json`, complete
  `docs/experiments/002-attempt-A2.md` (the T40 table stays as the checkpoint; the end
  table goes below it) and update `docs/experiments/RETRO-2026-09-29.md` with A2's final
  half - including whether H1 was held, broken, or still unaskable.
- Then retire **this file and 031 together** (031's window ends with the attempt), and say
  in the diary's `tooling` line which turn each ended on.

## Honesty notes this attempt has already paid for

- The combat reply prints the **pre-attack** HP (`enemy HP:72 -> 72/100` on a landed hit):
  never conclude from the reply that an attack failed, and never re-issue an attack on the
  strength of it - one legal attack was thrown away in the first half with `force=True`.
- Your own `ESTABLISHMENT:` line is checked against the record: write **both** numbers
  (`melee 2 target / 4 held`) so a target-vs-held confusion is not scored as a mistake.
- The diary is shared with A1 and the instrument attributes rows by session time, so a
  turn your session did not play is not yours to describe.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "attempt A2, second half: T41 to the first siege order" --instruction 继续 --why "resume attempt A2 past its mid-window checkpoint so the first siege order can be read" --done-when "turn 80 is reached, or a set_city_production reply reads PRODUCING|UNIT_CATAPULT (with that turn written into docs/experiments/002-attempt-A2.md), or a city_action reply reads KEEP| - whichever comes first" --overrides "task 031's stop-at-the-end-of-T40 instruction, and only that: the checkpoint it names is behind the game, which stands at T41. 031's scope, its finish line and its target stay in force, and this file adds no other exception." --scope "this match only: attempt A2 continued from the position the game stands on (T41, save 0_MCP_0041), running 031's settings, doctrine and target unchanged" --expires-turn 85 --body-file .tmp\a2-resume-body.md --cn @.tmp\a2-resume-cn.md
     at: 2026-09-29T16:29:08+08:00
     chinese backup: prompts/tasks/cn/032-attempt-a2-second-half-t41-to-the-first-siege-order.cn.md
-->
