# TEMP TASK 051 - Wake the sleeping half of the corps and march it to the front

added:     2026-10-08 (human instruction: 唤醒他们加入战斗。（2026-10-07 人类指令：把东边睡着的军团叫醒，全部投入前线。）)
expires:   turn 401 - 15 turn(s) from T386, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 of UNIT_ROCKET_ARTILLERY, UNIT_MODERN_AT and UNIT_MODERN_ARMOR carry [SENTRY] or [HOLD]
           in get_units, i.e. every gun and every anti-tank is awake and at or on its way to the
           front
overrides: the routine-development default: waking and marching these units outranks city builds and builder
           dispatch until they are at the front
scope:     the rear half of the assault corps only - the three sleeping Rocket Artillery, three Modern AT, four
           Modern Armor and the spare Machine Gun; nothing else changes

## What the T386 read found

The front is winning with half the army: six Rocket Artillery, three Machine Gun, two Mechanized
Infantry (both standing **inside captured cities** - Tbilisi and Chennai), two Modern AT and one
Modern Armor are at x 10-25, and three enemy cities have already fallen. The other half is asleep in
the rear:

| Unit | Where | Flag |
|---|---|---|
| Rocket Artillery | (49,35), (50,29), (55,29), (70,36), (72,20), (56,45) | the last three carry `[SENTRY] [fortified 2] [cannot act]` |
| Modern Armor | (56,18) hp68, (58,20), (74,12) hp79, (76,12) hp56 | one `[OPERATION]`, one `[HOLD]` |
| **Modern AT** | (61,42), (63,37), (69,29) | **all three `[SENTRY]`**, parked in Novgorod, Yerevan and Brussels |

A unit under `[SENTRY]` or `[HOLD]` **will never move on its own** - `[cannot act]` is literal. Six
guns and the whole anti-cavalry row are therefore out of the war while the front fights without them.

## The order

1. **Wake every one of them and send them west**, to the Georgia/India front (x 10-35): giving a
   sleeping unit a move order is what wakes it - `play-turn.py move <index> <x> <y>` for each, or
   `play-turn.py march ...` for a convoy.
2. **Do not park the corps on sentry while a war is on.** `[SENTRY]`/`[HOLD]` is for a frontier with
   no enemy; for the assault establishment the correct idle state is a staging tile within reach of
   the next target (or `heal` when damaged).
3. **The anti-cavalry travels with the guns** - that is the whole reason the row exists (the A2
   failure: an enemy Heavy Chariot parked beside the Catapults and nothing could answer it). Three
   Modern AT asleep in the rear is that failure waiting to repeat.
4. **Damaged units heal on the way** rather than arriving at 56 HP: (74,12) at 79 and (76,12) at 56
   should heal a turn or two, then march.
5. **Bring the spare Machine Gun and any replacement armour forward too** once the new production
   completes - the front has two firing positions per city, not six.

## Done when

`count == 0` of UNIT_ROCKET_ARTILLERY, UNIT_MODERN_AT and UNIT_MODERN_ARMOR carry `[SENTRY]` or
`[HOLD]` in `get_units` - every gun and anti-tank awake and on its way to, or standing at, the front.
Retire this file that turn and record in the diary how many turns the wake-up cost the war.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Wake the sleeping half of the corps and march it to the front" --instruction @.tmp/task051-instruction.txt --done-when "count == 0 of UNIT_ROCKET_ARTILLERY, UNIT_MODERN_AT and UNIT_MODERN_ARMOR carry [SENTRY] or [HOLD] in get_units, i.e. every gun and every anti-tank is awake and at or on its way to the front" --overrides "the routine-development default: waking and marching these units outranks city builds and builder dispatch until they are at the front" --scope "the rear half of the assault corps only - the three sleeping Rocket Artillery, three Modern AT, four Modern Armor and the spare Machine Gun; nothing else changes" --why "wake the sleeping rear units and march them to the front" --turns 15 --body @.tmp/task051-body.txt --cn @.tmp/task051-cn.txt
     at: 2026-10-08T00:22:12+08:00
     chinese backup: prompts/tasks/cn/051-wake-the-sleeping-half-of-the-corps-and-march-it-to-the-front.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 051 --done --turn 399
     at: 2026-10-08T08:44:39+08:00
     status: done at T399
     chinese backup: prompts/tasks/cn/051-wake-the-sleeping-half-of-the-corps-and-march-it-to-the-front.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 051 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:31+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/051-wake-the-sleeping-half-of-the-corps-and-march-it-to-the-front.cn.md
-->
