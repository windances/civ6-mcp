# TEMP TASK 041 - attempt A10 - the two-city military opening, executed as measured

added:     2026-09-30 (human instruction: civ6
           agent启动使用china-conquest策略，把china-two-city-military-opening转成一个可加载的任务？)
expires:   turn 80 - 30 turn(s) from T1, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: a city_action reply reports the first enemy city kept (the game's KEEP acknowledgement), or turn 80
           is reached - whichever comes first; the retiring turn reports the founding turn and tile
           of city two, the turn ENGINEERING was owned against the turn the first siege order was
           placed, the corrected table row by row, and how many Catapults were inside range 2 on the
           turn the city fell
overrides: two things, and nothing else. (1) china-conquest's per-city siege row: the directive asks for 3
           Catapults and this attempt runs the corrected tactics/01 table's 2, because every city
           the programme has read said walls: none - eight of them in A3 alone - so the wall phase
           the third gun pays for does not exist on this map. (2) the same directive's 'development
           never stops' as it applies to the war city before the first siege order: no economy
           technology ahead of ENGINEERING and no economy order in the war city ahead of the first
           UNIT_CATAPULT order. Everything else in china-conquest - Dynastic Cycle and its wonder,
           Three-Six Stratagems, the Crouching Tiger, no peace ever, the three phases - stands
           unchanged.
scope:     this match only, from the experiment's shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save:
           attempt A10 - the standing directive prompts/strategies/china-conquest/directive.md is
           unchanged and stays in force, and this file adds the opening measured by A1-A8
           (prompts/strategies/china-two-city-military-opening/directive.md) as the attempt's one
           variable: the research line pinned military-first, and the war city's queue kept on the
           army until the first siege order is placed. It does not touch any earlier attempt's
           position.

# TEMP TASK 041 - attempt A10 - the two-city military opening, executed as measured

Attempt **A10** of the military-production experiment (`docs/experiments/README.md` section 3). The
standing strategy is **`china-conquest`** and it is not being changed; what this file adds is the
opening, taken from `prompts/strategies/china-two-city-military-opening/directive.md`, which is the
measured distillation of A1-A8 (`docs/experiments/RETRO-2026-09-29.md`, section 12, and A8's own record
`docs/experiments/008-attempt-A8.md`). **Read that preset's directive once at the start of the
attempt** - it carries the evidence for every turn number below, and this file is the instruction while
the preset is the reasoning.

## The one variable: the opening's tempo, executed as written

Every attempt from A3 to A7 kept two cities, so the city count is not what changes here. **What changes
is what the empire's first forty-five turns are spent on.**

The doctrine as written is loose about it - "development never stops", name the Eureka, put the Campus
line down early - and A1-A7 were played that way. **A8 was the attempt that broke, and its record says
why**: it went economy-first (`THE_WHEEL` T41, `ENGINEERING` ordered T45), its capital spent **T31-T53**
on a Campus, a Granary, a Trader and a Library, the first Catapult was not ordered until **T53**, and its
establishment question was **FALSIFIED at T60**.

**The variable is the opening template: the research line pinned military-first, and the war city's
queue kept on the army until the first siege order is placed.** Those two are one decision - both are
what the capital does with its first forty-five turns - which is why they are one variable and not two.

## The claim, cut to its numbers

**Hypothesis: the opening the programme measured closes both of the questions it has been splitting.**

- **the establishment**: the corrected table - `siege 2, melee 2, anticav 1, ranged 4, cavalry 1,
  recon 1` - is **complete by T60**. A3 reached it at T53, A4/A6/A7 at T54 and A5 at T57; **A1, A2 and
  A8 never reached it inside their windows**;
- **the keep**: the first enemy city is **kept by T70**. The programme's keeps are A7 **T60**, A4
  **T65**, A3 **T67** and A2 **T68**; **A5, A6 and A8 kept nothing at all**, and A6 did it with a
  complete establishment and a bought gun;
- **falsified** if either misses. Both numbers have to be read from the game, and both are the standard
  the other attempts were judged on, so this is a directly comparable claim and not a new one.

**A prediction to check, not a bar**: the first siege order lands on the same turn `ENGINEERING` is
owned. That is H1 in the protocol and it held for A2, A3, A4, A5 and A7.

## The execution order

| turn | what | why |
|---|---|---|
| T1 | `UNIT_SCOUT` | `tactics/07` Gate 0: a city you have not seen has no pre-war analysis |
| T5 | `UNIT_SLINGER` | the pin's ranged slot |
| T10 | `UNIT_SETTLER` | **city #2 lands T20-T27** (A8 T20, A7 T21, A6 T27) |
| T18 | `UNIT_BUILDER` | strategic tiles first |
| about T8 | `TECH_THE_WHEEL` | A1-A7 all took it at T8 |
| about T22 | `TECH_ENGINEERING` | **no economy technology before this** |
| T23-T28 | `BELIEF_GOD_OF_THE_FORGE` | A5/A6/A7 founded it at T28/T25/T23 on 17-19 faith |
| T43 | first siege order | A3, A4 and A5 all ordered on T43 |
| T53-T57 | the corrected table complete | the measured band |
| T60 | the establishment deadline | the programme's standard |
| T70 | the keep deadline | this attempt's bar |

**Take `POLICY_AGOGE` when it is available** and stack it with God of the Forge: that pair took a
120-production Catapult in the capital from 11 turns to 6 (A2). Take the pantheon when the faith
arrives; do not hold it for a better belief on a military plan.

**No fifth order before `ENGINEERING` is owned.** The capital is the war city, and from the moment city
#2 exists, every order placed in the capital is an order not placed on the army.

## The siege rule, which is this file's only override of the standing strategy

`china-conquest` asks for **3 Catapults per city** (`prompts/strategies/china-conquest/directive.md`).
The corrected `tactics/01` table the instrument checks asks for **2**. **This attempt runs the 2**, and
the reason is measured rather than stylistic: **every city this programme has ever read said
`walls: none`** - eight of them in A3 alone - so the wall phase the third gun pays for does not exist on
this map.

- **Against a city reading `walls: none`: 2 Catapults, and both inside range 2.** A Catapult does 45-52
  against a city where an Archer does 9-11 into a CS 35 garrison, so two guns out-damage the roughly
  twenty points a city heals per turn and one does not. **A6 is the proof**: a complete establishment, a
  gun bought with gold, and the target finished the window at **200/200** with `SIEGE FIRE: 1/2`.
- **A siege unit cannot attack a unit at all** (`ERR:SIEGE_CANNOT_ATTACK_UNITS`), so the anti-personnel
  work is the 2 ranged at range 2 and the 2 Crouching Tiger at range 1, each Tiger with a melee unit
  holding the tile in front of it.
- **Cut the supply line**: stand on or beside every adjacent hex. It is cheaper than finding twenty more
  damage a turn, and `SIEGE PROGRESS` reports it as `supply line n/6 cut`.
- **Stage before the declaration, never after.** The city's ranged strike reaches 2 tiles.
- **Judge by `city hp: N/200` and `walls: N/100`**, never by the damage estimate.

## The standing strategy is otherwise unchanged

`china-conquest` remains in force in full, and nothing below is overridden by this file:

- **Dynastic Cycle**: a wonder is a research building for China. The **programme built zero wonders in
  eight attempts and roughly 340 turns**, so put one in the plan in a compounding city - **but not in
  the war city before the first siege order is placed**, and say in the diary which city is building it
  and when. A wonder that costs the siege order is a divergence and has to be named as one.
- **Thirty-Six Stratagems is human-assisted** (the adapter exposes no action): report any barbarian
  standing next to one of our melee units whose type is worth converting **before** the camp is
  destroyed.
- **Crouching Tiger**: Range 1, so it needs a melee unit in front of it. It fills part of the `ranged 4`
  row, and no tactic in this repository yet says which tile it takes - say in the diary which tile it
  actually got.
- **Never call `propose_peace`** and refuse every offer. A war ends by taking the city.
- **Three phases on every target**: analysis (`tactics/07`), staging (`tactics/04`), execution
  (`tactics/05`/`06`). Write the staging plan before the first move.

## Start: the shared start, and the trap that has already cost this programme a session

**This attempt is measured from the experiment's shared start**:
`evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`. Playing it on another position makes its numbers
incomparable with A1-A9.

**The trap, measured in A5 and again in A8**: `list_saves()` and `load_save(index)` are **two different
lists**. `list_saves()` is the **filesystem** scan capped at the newest 25, and the shared start falls
off it as soon as an attempt has played; `load_save(index)` reads the **game's own Lua list**, whose
order is not the scan's. The recipe that works: touch the save's mtime, drive the Lua list, then
`load_save` by **that** index. **Then verify**: `get_game_overview` must read **turn 1**. If it reads
any other turn, stop and say so.

**And the collision trap, measured 2026-09-30**: `AutoSave_NNNN` names are reused by different branches
of this match - `AutoSave_0108` and `AutoSave_0109` are **A7's** continuation and are three and a half
hours older than A8's `0107`. **Identify a save by its timestamp, never by its name.**

**If the game is already on this key at a turn past 1**, decide from the diary whether it is *this*
attempt's own run in progress (continue from where it stands, load nothing) or a previous attempt's
position (load the shared start over it, and say which position you replaced). **Never play A10 on A3-A8's
position.**

## The measurement

The experiment reads the diary's **per-10-turn economy rows**. Keep the five reflection fields every
turn and write the rows for **T10, T20, T30, T40, T50, T60, T70** - the comparison needs the same rows
the other attempts wrote. Say in the diary, on the turn city #2 is founded, **its tile and its founding
turn**.

The attempt's own instrument command, **with every session id it ran under** - an attempt that spans a
resume and lists only one session reports an attempt that starts at that session's first turn:

```
python scripts/experiment-report.py --game china_911679432 ^
  --run <every session id this attempt ran under> --questions a8 --save docs/experiments/A10-final.json
```

**The turn H1 lands on is the number to watch**: the turn `ENGINEERING` is owned and the turn the first
`UNIT_CATAPULT` is ordered. If they differ, that is the finding.

## End

The attempt ends **the turn the first enemy city is kept**, or **turn 80**, whichever comes first. On
that turn report:

- the founding turn of city #2 and its tile;
- **the turn `ENGINEERING` was owned and the turn the first siege order was placed**, and whether any
  economy technology or war-city economy order was placed before them;
- the corrected table **row by row** at the moment of the report, against `siege 2, melee 2, anticav 1,
  ranged 4, cavalry 1, recon 1`;
- the keep: the turn, the target, its `walls` and HP reading, and the `city_action` reply;
- **which guns were inside range 2 on the turn the city fell**, because that is the number A6 died for;
- whether the empire's shape changed anywhere else, with the diary turn;
- whether a wonder was started, in which city, and what it cost the queue.

Then retire this task with `--done` or `--expired` - **`--expired` if the window closed without a keep**
- and hand back to the orchestrator.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "attempt A10 - the two-city military opening, executed as measured" --instruction "civ6 agent启动使用china-conquest策略，把china-two-city-military-opening转成一个可加载的任务？" --why "execute the opening the experiment measured, from the shared start, with the standing strategy left as it is" --scope "this match only, from the experiment's shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save: attempt A10 - the standing directive prompts/strategies/china-conquest/directive.md is unchanged and stays in force, and this file adds the opening measured by A1-A8 (prompts/strategies/china-two-city-military-opening/directive.md) as the attempt's one variable: the research line pinned military-first, and the war city's queue kept on the army until the first siege order is placed. It does not touch any earlier attempt's position." --overrides "two things, and nothing else. (1) china-conquest's per-city siege row: the directive asks for 3 Catapults and this attempt runs the corrected tactics/01 table's 2, because every city the programme has read said walls: none - eight of them in A3 alone - so the wall phase the third gun pays for does not exist on this map. (2) the same directive's 'development never stops' as it applies to the war city before the first siege order: no economy technology ahead of ENGINEERING and no economy order in the war city ahead of the first UNIT_CATAPULT order. Everything else in china-conquest - Dynastic Cycle and its wonder, Three-Six Stratagems, the Crouching Tiger, no peace ever, the three phases - stands unchanged." --done-when "a city_action reply reports the first enemy city kept (the game's KEEP acknowledgement), or turn 80 is reached - whichever comes first; the retiring turn reports the founding turn and tile of city two, the turn ENGINEERING was owned against the turn the first siege order was placed, the corrected table row by row, and how many Catapults were inside range 2 on the turn the city fell" --expires-turn 80 --slug attempt-a10-the-two-city-military-opening --body-file .tmp/a10-body.md --cn @.tmp/a10-cn.md
     at: 2026-09-30T21:18:19+08:00
     chinese backup: prompts/tasks/cn/041-attempt-a10-the-two-city-military-opening.cn.md
-->
