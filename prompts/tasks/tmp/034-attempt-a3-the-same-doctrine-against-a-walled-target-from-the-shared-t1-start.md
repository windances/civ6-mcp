# TEMP TASK 034 - attempt A3: the same doctrine against a walled target, from the shared T1 start

added:     2026-09-29 (human instruction: 继续A3 ~ A7)
expires:   turn 115 - 30 turn(s) from T4, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: turn 110 is reached, or a city whose wall pool read above zero is kept (a city_action reply reads
           KEEP|) - whichever comes first
overrides: nothing: the design is docs/experiments/README.md's A3 row and it contradicts neither the directive
           nor A1/A2's records. It does supersede their stop-turn conventions - A1 stopped at T40
           and A2 ran to its capture - because this attempt's window is written from its own queue:
           Engineering ~T48, the train ~T55, and a walled target found and attacked inside T80.
scope:     this match only, from the experiment's shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save:
           attempt A3 - the same settings and the corrected tactics/01, with the assault target's
           defences as the one variable

Attempt **A3** of the military-production experiment (`docs/experiments/README.md`). Its row there is the
authority on the design; this file is the instruction for playing it. A1 and A2 are
`001-attempt-A1.md` and `002-attempt-A2.md`; the cross-attempt report is `RETRO-2026-09-29.md`.

## Start: the shared start, not the position the game happens to hold

0. `get_game_status`. **This attempt is measured from the experiment's shared start**:
   `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` (the settled T1 position A1 and A2 both ran from). If the
   game does not stand on it - it is at T77 of the branch A2's capture ended on, or anywhere else - **load
   that save** (`restart_and_load`, or the save list) and say in the diary which turn the loaded save
   holds. The T77 position is not lost: the MCP keeps `0_MCP_NNNN` per turn, and `0_MCP_0077` holds it.
   Playing A3 on any other position makes its numbers incomparable with A1 and A2, which is the one thing
   the experiment cannot afford.
1. Then `get_diary` (it holds A1's and A2's history on this save) and one `scripts\orient.py` read.

## The opening build is pinned (the protocol's rule from A3 on)

`docs/experiments/README.md` requires it of every attempt from A3: the doctrine fixes what the army is
made of and **not** what the city is asked for first, so A1 and A2 opened differently and their compare
had two candidate causes. These four orders are therefore fixed:

| order | item | why |
|---|---|---|
| 1 | `UNIT_SCOUT` | the corrected table's **recon** row - `tactics/07`'s Gate 0 needs a city seen |
| 2 | `UNIT_SLINGER` | the ranged line (Slinger → Archer → Crossbowman) |
| 3 | `UNIT_SETTLER` | the second city; both earlier attempts built one early and the economy compounds from it |
| 4 | `UNIT_BUILDER` | improvements feed the production the train needs |

**The attempt's record must say whether the executor matched them**, order by order, and a deviation is
allowed only with the reason in the diary's `planning` line. (A3's first order was the Scout: the pin
arrives after it, so the record notes that the pin starts from an opening that already matched it.)

## The one variable: the target's defences

**The assault target must be a city that actually has walls** - a wall pool greater than zero, read from
the attack reply's `walls: N/100` or the `SIEGE PROGRESS` block, not assumed. A2's target read
`walls: none`, so its whole wall phase - the reason the siege train exists - never ran; A3 exists to run
it. Everything else is held:

- the same save and settings (China/Qin, Prince, Small Pangaea, Quick);
- the **corrected** `tactics/01` (this is the one thing that changed since A2 and the record must say so:
  A3 differs from A2 in **two** ways - the table, and the target's defences - so its capture arithmetic is
  compared against A2's T68 with that in mind);
- the corrected table is now the standard: **1 Scout (or a spare cavalry unit) for recon**, **1
  anti-cavalry**, siege 2, melee 2, ranged 4, cavalry 1, and **no ram is bought** (an already-owned one
  joins). `tactics/07`'s Gate 0 is that a candidate city is *visible* with its walls, HP and garrison
  read - the recon unit is what makes that possible, and A2 spent twenty-six turns without it.

## The hypothesis, with the numbers that falsify it

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table (recon and anti-cavalry included) | the composition at T60 is short in any required role |
| Q2 | **a walled target changes the arithmetic measurably**: the wall pool's turn count is on the record and the city is kept **no earlier than T68** (A2's capture) and **no later than T80** | no city with `walls > 0` is found and attacked inside the window (report the reads that prove it - that is *unaskable*, not a miss), or the city falls before T68, or T80 passes without a `KEEP|` |
| Q3 | the **first city is kept by T80** | T80 arrives with no `KEEP|` in the log |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns** | the rule reads red on ten or more turns. Report the diary's own `gold_per_turn` too: both A1 and A2 sat under the +10 floor on every single turn, and that is a finding about the doctrine's ceiling, not about a session's spending |

**Q2 is the attempt.** A walled city is the case the train was built for, and no attempt has measured it.
If no walled target exists in the window, that is the answer - with the reads - and the attempt says so
rather than attacking an unwalled one and calling it a wall test.

## What to do, in order

1. **Recon before anything else** (`tactics/07` Gate 0). Build the Scout from the corrected table, send it
   west and north-west with `automate` or explicit moves, and read every city-state and rival city it
   finds: `get_map_area` for the tile, and the first attack estimate or `get_staging_plan` for the pools.
   Ancient Walls appear after Masonry and cost production - a city-state that has not walled by T70 may
   wall later, so re-read the ones you have already seen.
2. **The production order is `tactics/01`'s**: when Engineering lands, order `UNIT_CATAPULT` before any
   economy building (H1 held at A2's T48 - this attempt is the second test of it, and the first under the
   corrected table). Keep one anti-cavalry unit with the army: A2's Heavy-Chariot problem was that nothing
   could answer it.
3. **March and stage by `tactics/04`/`05`**: the screen in front, the siege at range 2, the last firing
   tile filled first. `screen-the-siege` and `counter-the-cavalry` are the rules that watch this; if they
   go red, fix the formation or say in the diary why it cannot be fixed.
4. **Declare war** on the walled target's owner (`send_diplomatic_action`) - a city-state is declared on
   by player operation now, and the reply says `OK:WAR_REQUESTED`. Then position that turn and attack the
   next.
5. **Fire every turn the train can fire, and cut the supply line** - a city heals about twenty points a
   turn while any adjacent hex is outside our zone of control, so the surplus units close the ring while
   the Catapults work. Judge progress from `SIEGE PROGRESS` and from a **later** read: the attack reply's
   own damage line is stale and has been recorded misleading three times.
6. **Every ten turns**: the `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` lines, and the `10-TURN
   REVIEW`'s three questions answered in the diary with numbers.

## The finish line, and what to leave behind

- The attempt ends when **a city whose wall pool read above zero is kept** (a `city_action` reply reads
  `KEEP|`) or the game reaches **turn 110**, whichever comes first. `expires:` is T115.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <this session> --from 1 --to <last turn> --step 10 --verdict --save docs/experiments/A3-final.json`
  (if the instrument has grown an `--questions a3` by then, use it and say so), run
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A2-final.json docs\experiments\A3-final.json`,
  write the attempt's record as `docs/experiments/003-attempt-A3.md` (settings, the one variable, the four
  questions, the wall pool's turn count, the cost, and the 10-turn tables), and add A3's half to
  `docs/experiments/RETRO-2026-09-29.md`.
- Then retire this file, and say in the diary's `tooling` line which turn it ended on.

## Honesty notes the programme has already paid for

- **A reply is not a result.** A landed city attack has printed `damage dealt:none read`; a capture move
  has answered `BLOCKED (city-state territory)` while the unit stood on the city. Judge from a later read
  and from the pooled fields.
- **Say which measure a claim uses.** The gold floor has three numbers (the rule, the review's line, the
  diary's own) and they disagree; Q4 above names two of them for that reason.
- **A role the table does not name is a role the empire does not build.** That is why recon and
  anti-cavalry are rows now.
- **The diary is shared** with A1 and A2 on this key; the instrument attributes rows by session time, so
  a turn your session did not play is not yours to describe.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --replace --title "attempt A3: the same doctrine against a walled target, from the shared T1 start" --instruction "继续A3 ~ A7" --why "the wall phase no attempt has measured, on a target whose wall pool is above zero" --done-when "turn 110 is reached, or a city whose wall pool read above zero is kept (a city_action reply reads KEEP|) - whichever comes first" --overrides "nothing: the design is docs/experiments/README.md's A3 row and it contradicts neither the directive nor A1/A2's records. It does supersede their stop-turn conventions - A1 stopped at T40 and A2 ran to its capture - because this attempt's window is written from its own queue: Engineering ~T48, the train ~T55, and a walled target found and attacked inside T80." --scope "this match only, from the experiment's shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save: attempt A3 - the same settings and the corrected tactics/01, with the assault target's defences as the one variable" --expires-turn 115 --body-file .tmp\a3-body.md --cn @.tmp\a3-cn.md
     at: 2026-09-29T20:22:06+08:00
     chinese backup: prompts/tasks/cn/034-attempt-a3-the-same-doctrine-against-a-walled-target-from-the-shared-t1-start.cn.md
-->
