# TEMP TASK 031 - military production experiment, attempt A2

added:     2026-09-29 (human instruction: 你自己启动游戏，开局新游戏，选中国，2个对手，难度适中，小地图，进行以军事为目的的最优生产力策略的调优。记录你所有的尝试，能复盘。)
expires:   turn 90 - 30 turn(s) from T41, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: a city is kept (a city_action reply reads KEEP|) or the game reaches turn 80, whichever comes first
overrides: the standing directive's city-states-are-not-conquest-targets line, for this attempt only, because
           the experiment needs a city its army can reach; the victory path is unchanged
scope:     this match only: the shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save, attempt A2

# Attempt A2 - the same doctrine, with a target inside the window

This is the second attempt of the experiment in `docs/experiments/README.md`, and it exists because of
what A1 measured. **The one variable is the target's distance.** Same save, same doctrine as written,
same executor; the objective moves from the nearest rival *capital* to the nearest *city*.

## Why, in one paragraph

A1 stopped at the end of T40 with its mid-window review written (`docs/experiments/001-attempt-A1.md`).
Its capture half was decided by the map before the army existed: the only rival capital on the map is
**33 tiles west** of 西安, behind five city-states, and by T40 **no rival had been met at all** - while
the siege half of the establishment cannot begin before Engineering, which the attempt's own arithmetic
puts around T42. A window whose capture half is arithmetically impossible cannot answer a question about
production, so this attempt changes the one thing that makes the question answerable and nothing else.

## The target, measured before any deadline is written

- **The nearest city is the city-state 耶路撒冷, ten tiles west of the capital** - the coordinates are in
  this file's sibling record and in `docs/experiments/A1-T40.json`; the ruler is
  `get_staging_plan(city_x, city_y)`, and **its answer is what the deadline is written from**, not the
  calendar. `AGENTS.md`'s existing rule - count the turns from the queue, not from the calendar - applies
  to the target as much as to the build.
- **A city-state is a legitimate target for this experiment and not for the standing directive.** The
  preset says city-states are not conquest targets because a *victory* needs the rival capitals; a
  production experiment needs a city its army can reach. That single line is overridden here for this
  attempt, and the review must read the deviation as the experiment's design rather than as drift.
- **The rival capitals are not forgotten**: if the city-state falls with turns to spare, the same army
  continues west. That is a bonus, not the finish line.

## What this attempt is testing

`prompts/tactics/01-unit-production.md` as written - the establishment table (siege 2 / melee 2 / ram 1 /
ranged 4 / cavalry 1) and its production order, with `tactics/08` for the war economy. **Do not improve
the doctrine mid-attempt**; a changed plan is a different attempt, and the plan variations queue behind
this one precisely because this one holds the plan still.

**The hypothesis, and the numbers that falsify it:**

| # | Prediction | Falsified when |
|---|---|---|
| Q1 | with a target ten tiles away instead of thirty-three, the establishment is complete **by T60** | the composition at T60 is short in any role |
| Q2 | **the siege train is ordered before the economy buildings** once Engineering exists - this is H1, and A1 could not test it because the tech did not exist | a Campus, Granary or other infrastructure order is placed after Engineering and before the second Catapult |
| Q3 | **the first city is kept by T80** | T80 arrives with no `KEEP|` in the log |
| Q4 | the army is paid for without breaking the economy: `carrying-capacity` red on **fewer than 10 turns** | gold/turn is below 10 on ten or more turns before the city falls |

## Every ten turns

Answer the `10-TURN REVIEW`'s three questions in the diary with numbers, and put these lines in the
`strategic` reflection - the instrument cross-checks them against the record, and a claim the record does
not support shows up as a MISMATCH rather than being read as fact:

```
ESTABLISHMENT: siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1 at T<n>
WAR READY: <the turn the establishment was complete, or "not yet">
ENEMY SEEN: <which enemy cities are visible, the distance to the nearest, and its wall/hp reading>
```

## The first stop: the end of turn 40

Play to the end of **turn 40**, then stop and report - the experiment takes its mid-window review there,
and this attempt's first question is whether the wall phase can even open before it. **Stopping is not
retiring**: this file stays in force and the attempt continues from T41.

## The stop

The attempt ends the turn the first city is kept, or at turn 80, whichever comes first. Retire this file
in that turn (`scripts/temp-task.py retire 031 --done --turn N`, or `--expired`), take the attempt's
snapshot **before any later attempt overwrites the diary**
(`scripts/experiment-report.py --game china_911679432 --run <session> --save docs/experiments/A2-T40.json`),
and write the record as `docs/experiments/002-attempt-A2.md`. Then compare it with A1:
`scripts/experiment-report.py --compare docs/experiments/A1-T40.json docs/experiments/A2-T40.json`.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "military production experiment, attempt A2" --instruction @.tmp/task030-instruction.txt --why "military production experiment attempt A2: the same doctrine on a target inside the window, since A1's capture half was decided by the map" --done-when "a city is kept (a city_action reply reads KEEP|) or the game reaches turn 80, whichever comes first" --overrides "the standing directive's city-states-are-not-conquest-targets line, for this attempt only, because the experiment needs a city its army can reach; the victory path is unchanged" --scope "this match only: the shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save, attempt A2" --slug military-production-attempt-a2 --expires-turn 90 --body-file .tmp/task031-body.md --cn @.tmp/task031-cn.md --no-commit --no-gate
     at: 2026-09-29T13:58:59+08:00
     chinese backup: prompts/tasks/cn/031-military-production-attempt-a2.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 031 --done --turn 68
     at: 2026-09-29T17:59:24+08:00
     status: done at T68
     chinese backup: prompts/tasks/cn/031-military-production-attempt-a2.cn.md
-->
