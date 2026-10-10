# TEMP TASK 059 - All-out on wonders: claim what is still unbuilt, without starving the corps

added:     2026-10-09 (human instruction: 新任务：全力建造奇观。)
expires:   turn 473 - 30 turn(s) from T443, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 3 wonders completed in our cities since this file was published, each named with its city
           and completion turn, and no front-line city's queue diverted from the war
overrides: the ordinary production order in the cities the war is not using: a wonder that compounds outranks a
           building there, while a front-line queue stays on the war
scope:     which wonders are still unbuilt, their prerequisites and placement, the queues of the cities the war
           does not need, the builders that prepare their tiles, and the Great Engineers that can
           rush them; no front-line queue is touched

## The instruction (verbatim, 2026-10-08)

"新任务：全力建造奇观。"

All-out on wonders. The empire has the production for it - 50-plus cities, three of them over 50
production and the capital near 90 - and a wonder is the one build whose value **compounds** every
turn afterwards: science, culture, gold, amenities, or a discount on everything that follows. What
"all-out" must not mean is the two mistakes this file exists to prevent - **building into a wonder a
rival already finished**, and **starving the siege corps for it**.

## Before a single wonder is queued

1. **What is still available**: `get_city_production(city_id)` in the two or three highest-production
   cities lists what can actually be built there, with the wonder and its turn count. A wonder a
   rival has completed is not on that list, and that is the check - do not infer it from the tech
   tree.
2. **Prerequisites**: a wonder needs its tech or civic and a **valid tile**. `get_wonder_advisor(
   city_id, wonder_name)` names the tiles that qualify. Never queue one whose placement does not
   exist yet.
3. **Order by value, not by price**: first the ones that compound the fastest - science and culture
   multipliers, then production, then the rest. A 12-turn wonder in the capital beats a 4-turn one in
   a city that has nothing else to do, but a 4-turn wonder that is **one of a kind and nearly done**
   beats both.
4. **Great Engineers are the wonder multiplier**: `get_great_people` each turn; a Great Engineer can
   finish a wonder outright. `recruit_great_person` when the points are there, `patronize_great_person`
   with gold or faith when the wonder is the one you cannot lose.

## Rules for the queue

- **The corps comes first in the front cities.** Nothing in this task authorizes pulling a siege
  unit, a screen or a reinforcement out of a queue that the war tasks (058 especially) are waiting
  on. Wonders go into the cities the war is not using - and the empire has plenty of those.
- **One queue slot per wonder, one wonder per city at a time.** A city at 0 growth and no district
  left to build is the right host; a city that still needs its Campus does not get a wonder first.
- **Keep a builder on hand** for the wonder that needs a tile prepared (a feature cleared, a farm, a
  mine): `get_builder_tasks` lists what is bare, and **check `moves` before ordering `improve`** - a
  builder with 0 moves wastes the turn (measured T434: 3 of 4 builder orders died that way).
- **Report each completion the turn it happens**: which wonder, which city, which turn. A wonder
  finished silently is a wonder whose effect nobody plans around.

## Done when

`count >= 3` wonders completed in our cities since this file was published, each named with its city
and its completion turn, and no front-line city's queue diverted from the war to get them. Retire the
file then; if a rival took one we were building, say which and on which turn, because that is a
decision the next window needs.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "All-out on wonders: claim what is still unbuilt, without starving the corps" --instruction 新任务：全力建造奇观。 --done-when "count >= 3 wonders completed in our cities since this file was published, each named with its city and completion turn, and no front-line city's queue diverted from the war" --overrides "the ordinary production order in the cities the war is not using: a wonder that compounds outranks a building there, while a front-line queue stays on the war" --scope "which wonders are still unbuilt, their prerequisites and placement, the queues of the cities the war does not need, the builders that prepare their tiles, and the Great Engineers that can rush them; no front-line queue is touched" --why "claim the wonders that are still unbuilt, because they compound every turn and the empire has the production" --turns 30 --cn @.tmp/task059-cn.txt --body @.tmp/task059-body.txt
     at: 2026-10-09T04:52:01+08:00
     chinese backup: prompts/tasks/cn/059-all-out-on-wonders-claim-what-is-still-unbuilt-without-starving-the-corps.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 059 --expired --turn 219 --note "cleared by the human after the rollback to T218: the file assumed a fifty-city empire"
     at: 2026-10-10T12:44:03+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/059-all-out-on-wonders-claim-what-is-still-unbuilt-without-starving-the-corps.cn.md
-->
