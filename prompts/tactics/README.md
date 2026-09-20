# Military tactics for the `military-map` advisor / 军事worker 战术手册

Six files, one per decision the human asked to have separated. The `military-map` worker is
read-only and sees only the immutable snapshot, so each file is written as **triggers →
assessment → decision → prohibitions → what to report**. Read only the files the current
snapshot calls for; they are meant to be consulted one or two at a time, not all at once.

| # | File | 主题 | Read it when |
|---|---|---|---|
| 1 | `01-unit-production.md` | 部队的生产策略 | proposing production, purchases or upgrades |
| 2 | `02-contact-on-discovery.md` | 部队发现敌人，对敌行动策略 | any enemy is visible within 3 tiles of our units |
| 3 | `03-under-attack.md` | 部队被攻击时，对敌人行动策略 | any of our units lost HP during the AI turn |
| 4 | `04-staging-out-of-range.md` | 攻城前，城外攻击范围外的集结策略 | an assault is being planned but the stack is not formed |
| 5 | `05-formation-and-screening.md` | 攻城前，部队站位策略 | the stack is formed and about to advance |
| 6 | `06-assault-composition-and-fire.md` | 攻城开始后，部队搭配和攻击策略 | the stack is in contact with the target city |

## Shared vocabulary

These names are the same ones the MCP prints in the turn result, so a proposal can quote them
instead of arguing from feeling:

- **Contact metrics**: `enemies_within_1/2/3`, `enemies_cavalry_within_2`,
  `enemies_melee_within_2`, `enemies_ranged_within_2`, `enemies_siege_within_2`,
  `weakest_enemy_hp_within_2`, `attacks_this_turn`, `unused_attacks`, `local_superiority`,
  `enemies_massed_on`, `damaged_this_turn`, `at_war`.
- **Staging metrics**: `siege_units`, `siege_exposed`, `siege_in_city_range`,
  `siege_city_distance_min` (from the `SIEGE POSTURE` scan: distance from each siege unit to
  the nearest enemy unit, from that enemy to the unit screening it, and to the nearest city).
- **Check rules** the orchestrator is held to, which a proposal can cite:
  `siege-train`, `ranged-mass`, `melee-screen`, `ram-tower-before-civil-engineering`,
  `counter-the-cavalry`, `use-your-attacks`, `finish-the-wounded`,
  `mass-on-contact`, `screen-the-siege`, `one-garrison-per-city`, `answer-the-attack`.
  (`engage-the-screen` was retired after the T101-T116 siege replay: "did you attack anything"
  passed while a 7 HP enemy stood one tile away. `use-your-attacks` replaced it.)
- **Blocks in the turn result**: `BATTLE ASSESSMENT` (enemy in contact, what is killable, how
  many of our units are in range) and `SIEGE POSTURE` (the formation geometry).

## Rules that hold in every file

- **Assess before proposing.** Name the units, tiles and numbers from the snapshot. If the
  snapshot lacks the number, report the gap as a warning instead of inventing it.
- **Never trade one-for-one.** Two or three attackers on one target kill; one attacker trades
  and the target heals about twenty points a turn.
- **A siege unit is never the unit that takes the hit**, and never stands adjacent to what it
  is bombarding (range 2).
- **Ranged cannot capture a city.** Only a melee unit walking in finishes it.
- **Proposals, not orders.** Return only JSON matching `contracts/worker-proposal.schema.json`,
  with `worker: "military-map"`. Do not request tools and do not assume access to the live
  game: the snapshot is immutable.
- **Several of our units on one tile is normal when that tile is one of our cities.** Civ VI
  reports the units inside a city at the city's own coordinates, and a city centre can hold more
  than one of them (the *field* is one unit per tile). `get_units` marks these `[IN <city>]`, and
  the snapshot lists our cities with coordinates - so read a multi-unit tile against the city
  list before calling it an impossible stack or asking for the roster to be re-read. A stack on a
  tile that is **not** a city is the real anomaly, and it is worth a warning because it makes
  every distance-based judgement suspect.
