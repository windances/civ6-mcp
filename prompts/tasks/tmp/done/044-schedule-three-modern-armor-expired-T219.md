# TEMP TASK 044 - Schedule three Modern Armor without cancelling any queue

added:     2026-10-04 (human instruction: 不取消当前生产项目，排产3辆现代坦克，生产完成，任务结束)
expires:   turn 374 - 30 turn(s) from T344, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 3 units of type UNIT_MODERN_ARMOR exist on the map, as read by get_units. The empire held 0
           at T344, so this is an absolute count and not a delta; the task is finished the turn that
           count reads 3.
overrides: The directive's build order in the three chosen cities, and only there, until the armour exists - a
           Research Lab or a Factory in one of those three waits. It does not outrank the war front,
           the target order, or a space-race item: a city building a space project is not a
           candidate at all.
scope:     Production scheduling, in three cities and nowhere else: it authorises choosing three cities whose
           current item will not be cancelled, and setting their production to UNIT_MODERN_ARMOR the
           turn that item completes. It authorises nothing else - not a purchase, not a queue
           replacement, not a fourth city.

## The instruction, verbatim

不取消当前生产项目，排产3辆现代坦克，生产完成，任务结束

## Why this is Modern Armor and not Tank

`UNIT_TANK` is in **no** city's build list: its upgrade exists, so the game hides it. Measured at
T344, four cities' `get_city_production` reads each offered `UNIT_MODERN_ARMOR (cost 680, buy:
2310g)` and none of them offered `UNIT_TANK`. The empire held 0 of either. So the three units are
`UNIT_MODERN_ARMOR` - 680 production, 95 combat strength, and it needs `RESOURCE_URANIUM`.

## What "without cancelling" means mechanically

`set_city_production` sets the city's **current** item. The tool cannot append behind it - the Lua
has `GetBuildQueue`, `GetTurnsLeft`, `GetProductionCost` and one `RemoveAt`, and no insert. So the
armour is started **the turn the current item completes**, never queued behind it, and the deadline
for a city is:

    total = the current item's remaining turns + the turns the game quotes for the armour

## Choosing the three cities

Read `get_city_production(city_id)` for the high-production cities first - Abydos, Astrakhan,
Chengdu, Beijing - because each had 1 or 2 turns left on its current item at T344 and a much
shorter armour build than the four below. Take the three cities with the smallest total.

**Use the game's quoted turns, never the arithmetic.** Measured at T344: ỉwnw quotes 14 turns for a
680-cost unit on `Prod 34`, and Yerevan quotes 18 on `Prod 32`, so unit-production bonuses are
already inside the game's figure and `cost / Prod` overstates the build in exactly the cities that
matter.

The four queues that were empty at T344, and so the only quotes actually measured:

| city | current item | armour quoted | total |
|---|---|---|---|
| Yerevan | WORKSHOP, 3t left | 18t | 21t |
| Jiaodong | BUILDER, 4t left | 18t | 22t |
| ỉwnw | INDUSTRIAL_ZONE, 10t left | 14t | 24t |
| Brussels | COAL_POWER_PLANT, 5t left | 22t | 27t |

## What this task does not touch

- **A space-race city, ever.** Xi'an is 9 turns from `PROJECT_LAUNCH_MOON_LANDING` and St Petersburg
  26 from `DISTRICT_SPACEPORT`. The science victory is the strategy; neither is interrupted, and
  neither is joined by this task.
- **Any current item, anywhere.** Replace nothing. A city whose current item is long is simply not a
  candidate - pick another one.
- **Uranium.** Read `get_empire_resources` before committing the third unit. Modern Armor needs
  `RESOURCE_URANIUM`; if the stockpile cannot cover three, build what it covers and say so in the
  diary rather than stalling a queue.
- **Gold.** `buy:` is 2310g each and the treasury has been under 700. This task schedules
  production; it does not authorise buying one, and it does not override the directive's spending
  rules.

## Finish

When `get_units` shows three `UNIT_MODERN_ARMOR`, the task is done in that turn - retire it with
`scripts/temp-task.py retire <nnn> --done --turn <N>`, move nothing else, and record which three
cities built them and what each queue gave up for it.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Schedule three Modern Armor without cancelling any queue" --instruction 不取消当前生产项目，排产3辆现代坦克，生产完成，任务结束 --slug schedule-three-modern-armor --done-when "count == 3 units of type UNIT_MODERN_ARMOR exist on the map, as read by get_units. The empire held 0 at T344, so this is an absolute count and not a delta; the task is finished the turn that count reads 3." --scope "Production scheduling, in three cities and nowhere else: it authorises choosing three cities whose current item will not be cancelled, and setting their production to UNIT_MODERN_ARMOR the turn that item completes. It authorises nothing else - not a purchase, not a queue replacement, not a fourth city." --overrides "The directive's build order in the three chosen cities, and only there, until the armour exists - a Research Lab or a Factory in one of those three waits. It does not outrank the war front, the target order, or a space-race item: a city building a space project is not a candidate at all." --why "schedule three Modern Armor without cancelling what a city is already building" --turns 30 --body-file .tmp/armor-body.md --cn @.tmp/armor-cn.md --replace
     at: 2026-10-04T16:52:25+08:00
     chinese backup: prompts/tasks/cn/044-schedule-three-modern-armor.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 044 --done --turn 356
     at: 2026-10-06T21:00:03+08:00
     status: done at T356
     chinese backup: prompts/tasks/cn/044-schedule-three-modern-armor.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 044 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:25+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/044-schedule-three-modern-armor.cn.md
-->
