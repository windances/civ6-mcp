# TEMP TASK 055 - Clear every barbarian out of our territory

added:     2026-10-08 (human instruction: 新任务：清剿所有野蛮人)
expires:   turn 412 - 20 turn(s) from T392, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 barbarian units and camps within three tiles of any of our cities, with a full
           get_strategic_map pass behind it, and every PILLAGED line in get_cities under repair or
           restored
overrides: the priority among the offensive tasks, for the units that can reach a raider this turn only: a
           barbarian inside our borders comes before the next Georgian city; the war itself
           continues
scope:     every military unit that can reach a barbarian this turn, the builders that repair the tiles it
           took, and the queues of the cities whose districts it pillaged; no peace, no withdrawal
           from a siege, no change to the Georgian front's tasks

## Why this file exists

A barbarian took a farm and the Campus at Arnhem while a session held the tuner for two turns, and the
reason was structural rather than tactical: the clause that covers it is in
`prompts/tactics/03-under-attack.md`, which the `military-map` advisor reads and the orchestrator's
turn loop does not; `prompts/checks/turn-checks.md` has no camp or barbarian rule, with both
`answer-the-camp.md` and `repair-the-pillaged-district.md` still staged in `prompts/checks/pending/`
(staged rules are not evaluated, so the `!! PILLAGED` lines the city read was already printing never
became a must-act); and every task in force was offensive. This file is the standing instruction that
was missing: **no barbarian is left alive inside our borders, at any point, for any reason.**

## Locate first, every time

A camp can be cleared by someone else and respawn nearby, and a coordinate carried over from an old
diary has already been wrong once (measured on this match). So:

1. `get_strategic_map` - one full pass over our cities and the ground between them, and
   `get_notifications` - the pillage notices name the city that was hit ("您在<city>的...遭到了野蛮人的掠夺").
2. `get_map_area` (radius 2) around each city that was named, and around each `!! PILLAGED` line in
   `get_cities` - the raider itself is what has to die, not only the tile it took.
3. `get_diplomacy` carries a `Barbarian (N unit)` line: when it rises, something is inside our
   territory that we have not seen yet.

## Then kill it, with what is nearest

- **A barbarian unit** dies to a melee attack from the nearest military unit with a move, or to
  ranged fire if nothing melee is in reach. Armour and Mechanized Infantry are the right tools; do not
  march a siege unit at it.
- **A camp** has no HP, no walls and no garrison bonus: **one military unit moving onto its tile
  destroys it.** That is the cheapest permanent answer, and it stops the respawn.
- **Convert before you kill when you can.** A barbarian standing next to one of our melee units can be
  taken by the leader ability (Three-Six Stratagems) instead of destroyed - report that case in the
  turn's diary *before* attacking, so the human can use it from the game UI.
- **Never leave a barbarian adjacent to a city without a garrison.** One unit on the city tile is the
  rule (`one-garrison-per-city`); a city with walls can also strike at range 2 for free damage.
- **Re-check every few turns.** A cleared camp respawns; "there were none last turn" is not a result.

## Repair what was taken

The tiles (FARM, and any other improvement) need the nearest builder - `get_builder_tasks` lists them,
then `improve` on the tile. **The district buildings are not a builder's job**: Campus, Library,
University, Research Lab and the rest are repaired through `set_city_production` in the city that owns
them. Both halves belong to this task; a pillaged Campus sits dead until its queue is set.

## What this outranks, and what it does not

It outranks the offensive tasks (050's next city, 051's march) **only for the units that can reach a
barbarian this turn** - the nearest armour, the nearest ranged unit, and the builder that repairs the
tile. It does not stop the war with Georgia: the front keeps its guns, and nothing here authorizes
peace or a withdrawal from a siege.

## Done when

`count == 0` barbarian units and camps within three tiles of any of our cities, with a full
`get_strategic_map` pass behind it, and every `!! PILLAGED` line in `get_cities` either under repair or
restored. Retire this file then - and say in the diary which rule (if any) was still staged in
`prompts/checks/pending/`, because a barbarian that gets through after this file expires is that gap
opening again.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Clear every barbarian out of our territory" --instruction 新任务：清剿所有野蛮人 --done-when "count == 0 barbarian units and camps within three tiles of any of our cities, with a full get_strategic_map pass behind it, and every PILLAGED line in get_cities under repair or restored" --overrides "the priority among the offensive tasks, for the units that can reach a raider this turn only: a barbarian inside our borders comes before the next Georgian city; the war itself continues" --scope "every military unit that can reach a barbarian this turn, the builders that repair the tiles it took, and the queues of the cities whose districts it pillaged; no peace, no withdrawal from a siege, no change to the Georgian front's tasks" --why "hunt down and destroy every barbarian inside our territory, and repair what they took" --turns 20 --cn @.tmp/task055-cn.txt --body @.tmp/task055-body.txt
     at: 2026-10-08T03:02:33+08:00
     chinese backup: prompts/tasks/cn/055-clear-every-barbarian-out-of-our-territory.cn.md
-->
