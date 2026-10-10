# TEMP TASK 048 - Four assault corps, built and assembled at the front

added:     2026-10-07 (human instruction: 2026-10-07：人类问"多少个回合能让我们拥有 4 个攻城军团，包括在目标城市前完成集结"，并明确把军事也
           交给会话全权负责（分工撤销）。按 `prompts/tactics/01-unit-production.md` 的编制表建满四个军团，并在 选定的目标城下完成集结后再开打。)
expires:   turn 405 - 30 turn(s) from T382, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: get_units counts >= 12 UNIT_ROCKET_ARTILLERY, >= 4 UNIT_MODERN_AT and >= 8 of
           UNIT_MODERN_ARMOR/UNIT_MECHANIZED_INFANTRY/UNIT_SPEC_OPS, and at least three corps' worth
           of them stand within 3 tiles of an enemy city (get_cities positions)
overrides: the 'one war city, everything else compounds' default: up to 8 cities may build units until the
           corps exist, and one Modern AT may be bought with gold; no other queue is touched
scope:     unit production, purchases and assembly for four assault corps; the target choice still belongs to
           the pre-war gates in tactics/07

## Why this exists

The army at T369 can field **two** assault groups; it cannot field four. Measured from the session's
own reads that turn (45 cities, 1,475 production/turn, 1,571 gold at +151/turn):

| Role | per corps | 4 corps need | at T369 | gap |
|---|---|---|---|---|
| Siege / ranged fire | 3 Rocket Artillery | 12 | 6 | **+6** |
| Screen fire | 2 Machine Gun | 8 | 3 | +5 |
| City-takers | 3 Modern Armor class | 12 | 8 | +4 |
| **Anti-cavalry** | **1 Modern AT** | 4 | **1** | **+3** |
| Recon | 1 (drone or aircraft) | 4 | 0 | +4 |

The anti-cavalry row is the one that has failed before: in the A2 experiment an enemy Heavy Chariot
parked next to both Catapults every turn and nothing in the army could answer it, because the role was
missing from the table entirely. Do not open a corps without its anti-cavalry unit.

## What to build, and where

**Build at the front, not in the east.** The high-production cities are at x 50-75 (Xi'an 74,
St. Petersburg 72, Astrakhan 66, Changsha 65, Chengdu 64) and the targets are at x 3-35, which is
25-45 tiles of march - a unit built in the east arrives no sooner than one built in a 30-production
city beside the front. The western cities are Nippur 34, Tyre 33, Carthage 32, Uruk 30, Kty 22,
Lagash 21, Biruta 20, Kish 15, Sbrt'n 14, Ur 13, Sippar 12, Shuruppak 8.

1. **Anti-cavalry first, because it is the gap that stops a corps from existing at all**: 3 Modern AT,
   one of them bought outright with gold if the treasury allows it (`UNIT_MODERN_AT` is 580 h /
   2,320 g), bought in a western city so it appears beside the front.
2. **Then the guns**: 6 Rocket Artillery (680 h each). The 6 that exist are already western; the new
   ones belong in the western cities too.
3. **Then the screens**: 5 Machine Gun and 4 drones (or leave the air leg to task 045's aircraft).
4. **City-takers last**: 4 more Modern Armor class. Four of the five existing Modern Armor are in the
   north-east at x 58-77 and need 12-17 turns to reach the west unless a Military Engineer lays rail
   (`build_route` is 0.5 movement per tile); decide deliberately: march them, or rebuild in the west.
5. **The economy call is yours to make and to write down.** tactics/08 says one war city and let the
   rest compound - that was learned at 5 cities and 32 science. This match has 45 cities and 1,475
   production, and the science tree is finished (Future Tech), so up to **8 cities** may build units
   until the corps exist while the rest keep compounding. The arithmetic: 8 western cities (~250/turn)
   is ~23 turns for the lean 9-unit gap; adding the top eastern cities and the military-engineer rail
   takes it to ~10-12; a whole-empire build-out would be ~4-7 turns but stops everything else. Pick
   one, say which in the diary, and hold it until the counters below are met.
6. **Chops are the biggest single lever**: while the train is the bottleneck a feature removal in a
   city building a unit goes into that unit, and Magnus (Groundbreaker, no promotion needed) adds 50%
   to it. A 34-production city with one chop produces a 680 h unit in 2-4 turns.

## Assembly

- Mass **outside** the target's two-tile strike range, at range 2-3 from the city: shooters at range 3
  (Rocket Artillery), screens in front (`prompts/tactics/04-staging-out-of-range.md`,
  `prompts/tactics/05-formation-and-screening.md`). A city's ring has about **three** useful firing
  tiles (measured, Moscow T103: six guns, three could fire, six stood idle), so three guns per city is
  the working number and six belong on two cities, not one.
- Use `get_staging_plan(city_x, city_y)` for the table and `get_reinforcements(target_x, target_y)`
  for who arrives when, then `get_target_report` for the walls and the garrison.
- Georgia's cities carry **walls 400** (7 of 10) and want the full 3-gun standard; India's are mostly
  `walls none` and are the cheaper half. The two have a defensive pact, so declaring on one brings the
  other in: plan both fronts before the declaration.

## The standing rules this does not change

No rams and no siege towers, ever (not built, not fielded). Rocket Artillery is the wall-breaker.
Peace is never proposed and every offer is refused - a war ends when the cities are ours. Missionaries
and Apostles at war are destroyed (`condemn`). Never open an assault that cannot win: run
`prompts/tactics/07-pre-war-analysis.md` first.

## Done when

`get_units` counts **12 Rocket Artillery, 4 Modern AT** and at least **8** units of the Modern Armor /
Mechanized Infantry / Spec Ops class, and at least three corps' worth of them stand within 3 tiles of
an enemy city - that is "built and assembled", which is what the human asked for. Retire this file the
turn that holds, and record in the diary how many turns it took against the estimate above.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Four assault corps, built and assembled at the front" --instruction @.tmp/task048-instruction.txt --done-when "get_units counts >= 12 UNIT_ROCKET_ARTILLERY, >= 4 UNIT_MODERN_AT and >= 8 of UNIT_MODERN_ARMOR/UNIT_MECHANIZED_INFANTRY/UNIT_SPEC_OPS, and at least three corps' worth of them stand within 3 tiles of an enemy city (get_cities positions)" --overrides "the 'one war city, everything else compounds' default: up to 8 cities may build units until the corps exist, and one Modern AT may be bought with gold; no other queue is touched" --scope "unit production, purchases and assembly for four assault corps; the target choice still belongs to the pre-war gates in tactics/07" --why "build four assault corps and assemble them at the front" --expires-turn 405 --body @.tmp/task048-body.txt --cn @.tmp/task048-cn.txt --replace --no-commit
     at: 2026-10-07T10:51:20+08:00
     chinese backup: prompts/tasks/cn/048-four-assault-corps-built-and-assembled-at-the-front.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 048 --expired --turn 385 --no-gate --no-commit --note "The match ended in victory at T385 before the corps counters held: the siege row was at twelve guns and the anti-cavalry row met, but the city-taker row stood at seven of the eight the file asked for, and the assembly was only ever completed around the capital that ended the war. Retired because the match is over, not because the goal was met."
     at: 2026-10-07T19:02:24+08:00
     status: expired at T385
     chinese backup: prompts/tasks/cn/048-four-assault-corps-built-and-assembled-at-the-front.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 048 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:28+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/048-four-assault-corps-built-and-assembled-at-the-front.cn.md
-->
