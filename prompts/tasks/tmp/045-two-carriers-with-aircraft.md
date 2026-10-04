# TEMP TASK 045 - Two aircraft carriers, each with its full complement of aircraft

added:     2026-10-04 (human instruction: 不取消当前生产项目，以生产2艘航空母舰以及配套的飞机为目标，排产相关的生产项目，目标达成，任务结束)
expires:   turn 424 - 80 turn(s) from T344, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 2 units of type UNIT_AIRCRAFT_CARRIER and count == 4 aircraft (UNIT_JET_FIGHTER,
           UNIT_JET_BOMBER, UNIT_FIGHTER or UNIT_BOMBER) exist on the map, as read by get_units. The
           empire held 0 of either at T344, so these are absolute counts and not deltas; the task is
           finished the turn both hold.
overrides: The directive's build order in the cities this task uses, and only there, until the carriers and
           their aircraft exist - a Research Lab or a Factory in one of those cities waits. It does
           not outrank the space race (a city building a space project is not a candidate at all),
           the war front, the loyalty work, or the directive's spending rules.
scope:     Production scheduling, in the coastal cities that build the carriers plus the one city that builds
           the Aerodrome and its four aircraft - and nowhere else. It authorises the research of
           TECH_COMBINED_ARMS, TECH_LASERS or TECH_STEALTH_TECHNOLOGY if any is missing, because an
           unlocked unit is a precondition of the schedule. It authorises building the Aerodrome
           district, without which no aircraft can be produced. It authorises nothing else - not a
           purchase, not a queue replacement, not a city beyond those.

## The instruction, verbatim

不取消当前生产项目，以生产2艘航空母舰以及配套的飞机为目标，排产相关的生产项目，目标达成，任务结束

## What the three units actually are

| unit | cost | needs | note |
|---|---|---|---|
| `UNIT_AIRCRAFT_CARRIER` | 540 | `RESOURCE_OIL`, `TECH_COMBINED_ARMS` | `Domain=DOMAIN_SEA` - a **coastal** city only - and **`AirSlots="2"`** |
| `UNIT_JET_FIGHTER` | 650 | `RESOURCE_ALUMINUM`, `TECH_LASERS` | `PrereqDistrict="DISTRICT_AERODROME"` |
| `UNIT_JET_BOMBER` | 700 | `RESOURCE_ALUMINUM`, `TECH_STEALTH_TECHNOLOGY` | `PrereqDistrict="DISTRICT_AERODROME"` |

`AirSlots="2"` is where "配套的飞机" gets its number: **two carriers hold exactly four aircraft**. Four
is the complement, and it is read off the unit data rather than chosen.

The two earlier airframes (`UNIT_FIGHTER` 520, `UNIT_BOMBER` 560) are the same domain and cheaper; if
the jets' techs are not in hand, say so in the diary and decide between research and the older pair
rather than stalling. The mix of the four is the caller's judgement - two fighters and two bombers is
the balanced default - and the diary records which was built and why.

## Two hard prerequisites, one of which we do not have

1. **A coastal city for each carrier.** A `DOMAIN_SEA` unit cannot be built inland at all. The cities
   whose read names a harbour building at T344 are the sufficient set: Shanghai (prod 54, and it
   carries a Harbour with a Lighthouse, Shipyard and Seaport), Brussels (27), Utrecht (24), Nippur
   (22), Lagash (16), Tyre (15), Sbrt'n (9). Read the map rather than trusting this list - a coastal
   city with no harbour would not appear in it.
2. **An `Aerodrome`, and we have none.** Measured at T344: **not one of the 37 cities names a
   `HANGAR` or an `AIRPORT`**, so no aircraft can be produced anywhere in the empire until an
   `Aerodrome` is built (`DISTRICT_AERODROME`, `PrereqTech=TECH_FLIGHT`, which is researched).
   Building that district is part of "排产相关的生产项目" and is the first thing this task does - the
   aircraft are unreachable without it. One Aerodrome serves all four aircraft; put it in the
   highest-production city that is not one of the space-race cities.

## The techs

`TECH_COMBINED_ARMS`, `TECH_LASERS` and `TECH_STEALTH_TECHNOLOGY` could not be confirmed from the
record: the game reports 77 techs completed, and the diary's own tech list belongs to a different
position (44 techs, and it says so). **Read `get_tech_civics` before planning** and, if any of the
three is missing, put it on the research path - this task authorises the research as well as the
production, because a unit that is not unlocked cannot be scheduled.

## What "without cancelling" means mechanically

`set_city_production` sets the city's **current** item; the tool cannot append behind it (the Lua has
`GetBuildQueue`, `GetTurnsLeft`, `GetProductionCost` and one `RemoveAt`, and no insert). So every item
below starts **the turn the city's current item completes**, and the deadline is:

    total = the current item's remaining turns + the turns the game quotes for the new item

**Use the game's quoted turns, never `cost / Prod`** - measured at T344, ỉwnw quotes 14 turns for a
680-cost unit on `Prod 34`, so unit-production bonuses are already inside its figure.

## What this task does not touch

- **A space-race city, ever.** Xi'an is 9 turns from `PROJECT_LAUNCH_MOON_LANDING` and St Petersburg
  26 from `DISTRICT_SPACEPORT`. Neither is interrupted and neither is joined.
- **Any current item, anywhere.** Replace nothing; a city whose current item is long is not a
  candidate.
- **Gold.** This task schedules production. It does not authorise buying a carrier or an aircraft,
  and it does not override the directive's spending rules.
- **The war front or the loyalty work.** Both outrank this.

## Finish

When `get_units` shows two `UNIT_AIRCRAFT_CARRIER` and four aircraft, the goal is met in that turn -
retire the task with `scripts/temp-task.py retire <nnn> --done --turn <N>`, and record in the diary
which city built each carrier, where the Aerodrome went, which four airframes were chosen and what
each queue gave up for them.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Two aircraft carriers, each with its full complement of aircraft" --instruction 不取消当前生产项目，以生产2艘航空母舰以及配套的飞机为目标，排产相关的生产项目，目标达成，任务结束 --slug two-carriers-with-aircraft --done-when "count == 2 units of type UNIT_AIRCRAFT_CARRIER and count == 4 aircraft (UNIT_JET_FIGHTER, UNIT_JET_BOMBER, UNIT_FIGHTER or UNIT_BOMBER) exist on the map, as read by get_units. The empire held 0 of either at T344, so these are absolute counts and not deltas; the task is finished the turn both hold." --scope "Production scheduling, in the coastal cities that build the carriers plus the one city that builds the Aerodrome and its four aircraft - and nowhere else. It authorises the research of TECH_COMBINED_ARMS, TECH_LASERS or TECH_STEALTH_TECHNOLOGY if any is missing, because an unlocked unit is a precondition of the schedule. It authorises building the Aerodrome district, without which no aircraft can be produced. It authorises nothing else - not a purchase, not a queue replacement, not a city beyond those." --overrides "The directive's build order in the cities this task uses, and only there, until the carriers and their aircraft exist - a Research Lab or a Factory in one of those cities waits. It does not outrank the space race (a city building a space project is not a candidate at all), the war front, the loyalty work, or the directive's spending rules." --why "two carriers and their full complement of aircraft, scheduled without cancelling any queue" --turns 80 --body-file .tmp/carrier-body.md --cn @.tmp/carrier-cn.md
     at: 2026-10-04T17:02:37+08:00
     chinese backup: prompts/tasks/cn/045-two-carriers-with-aircraft.cn.md
-->
