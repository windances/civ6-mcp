# TEMP TASK 042 - Recover the home front's production

added:     2026-10-04 (human instruction: 优先恢复生产)
expires:   turn 321 - 30 turn(s) from T290, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: `.tools/production-recovery.py` reports `0 idle queue(s)`, its pillaged list is empty (no city lists
           a pillaged district or building), and `get_cities` shows every city that read
           `power_required > 0` also reading `power_fully_powered == yes`.
overrides: The directive's Development build order, but only inside the city it applies to: a repair of a
           pillaged district or building, and filling a queue that is empty, both come before any
           new build in that city. It does not outrank the war front, the target order or the siege
           gates.
scope:     The home front's production only: every city's queue, the repair of a pillaged district or building,
           the power supply of a city that reads unpowered, and a Builder's repair of a pillaged
           tile. It authorizes the production and unit actions those need.

## Why the home front comes first now

Measured at T291 with the war column still marching: **two of the empire's three highest-production
cities were unpowered**, and one of them was doing nothing at all.

- Xi'an, pop 16, the science city and the largest single source of research (science 65.1), read
  `power 3.0/0.0/0.0` - **not powered** - because its Industrial Zone and all three of its buildings
  (Workshop, Factory, Coal Power Plant) were standing pillaged. The power-shortage warning had fired
  four times while the queue held a project.
- Shanghai, pop 12, production 27.2 (the highest in the empire), read `power 6.0/0.0/0.0` and its
  queue read `nothing` - a whole city producing at zero.
- Arnhem (production 23.2) and Sobek also had empty queues.

An empty queue and a pillaged production building are the two ways a city produces less than it
should, and neither was visible to any metric before this turn. They are now (`pillaged_districts`,
`pillaged_buildings`, `housing_slack`, `food_stalled`, `amenities_floor`).

## What is already done, so do not redo it

- Shanghai, Arnhem and Sobek were each given a queue (Shanghai an Industrial Zone on its +5 tile,
  Arnhem an Industrial Zone, Sobek a Builder).
- Xi'an's Industrial Zone repair is in flight.
- Two Builders are walking to pillaged tiles (a St. Petersburg Farm and the Shanghai Mine).

## The order of work

1. **A pillaged district or building is repaired before anything new is built in that city.** The
   district comes first: a pillaged building's repair is not even offered while its district is down
   (measured - Xi'an offered only `REPAIR DISTRICT_INDUSTRIAL_ZONE` until it completed).
2. **An empty queue is filled the same turn it is noticed**, with the role the directive assigns that
   city. A city doing nothing is the largest single loss available.
3. **Power first, and measure the reach rather than assuming it.** A fuel plant does supply its
   neighbours, but **not out to the six tiles the power lens suggests**: measured, a city four tiles
   from the empire's only plant drew from it and one five tiles away did not. So do not plan one
   plant per cluster on a six-tile radius. Build one, then read `power_temporary` in the cities
   around it - the tool prints that column - and place the next plant from what the read says.
   `.tools/production-audit.py` distinguishes **durable** supply (`free + temporary > 0`) from a city
   running on a project, which expires; only the durable half counts.
4. **Then the other standing losses**, cheapest first: Novgorod's pillaged Campus (and the Library and
   University behind it), Memphis' Aqueduct/Theater/Neighborhood, Amsterdam's Granary.
5. **A Builder on a pillaged tile repairs it** rather than starting a new improvement - the tile is
   already ours and already improved, so the repair is the cheapest yield in the empire.

## What this task does not authorize

Nothing on the war front. The target order, the marching column, the unit composition and the siege
gates are unchanged and outrank nothing here - this task only decides what the cities the army is not
standing in are building.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Recover the home front's production" --instruction 优先恢复生产 --slug recover-production --scope @.tmp/task-scope.txt --done-when @.tmp/task-done.txt --overrides @.tmp/task-overrides.txt --why "the home front's queues and pillaged districts, before any new build" --body-file .tmp/task-recover-production.body.md --cn @.tmp/task-recover-production.cn.md --expires-turn 321 --no-commit
     at: 2026-10-04T00:05:47+08:00
     chinese backup: prompts/tasks/cn/042-recover-production.cn.md
-->
