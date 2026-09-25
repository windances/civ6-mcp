# TEMP TASK 007 — destroy Russia

added:     2026-09-26 (human instruction: 消灭俄罗斯)
expires:   turn 160 — the third Catapult is the gate (一城3投石车) and it lands ~T125, the iron
           stockpile reaches a Swordsman ~T122 and the war is three or more cities at 4-8 turns each
           plus the march; count from the queue, not the calendar. Retire it early if Russia is gone,
           or as `007-destroy-russia-expired-T160.md` with a report of which cities stand and why.
done when: **Russia is eliminated** — `get_diplomacy` **no longer** lists a Russian city, every city
           we took has been resolved with `city_action` keep/raze, and no Russian unit is left inside
           our territory. Report the count of Russian cities taken (>= 3 expected: 阿斯特拉罕 (54,40),
           沃罗涅什 (50,37) and the one still in fog).
overrides: the per-city build lists, the Campus/Builder plan and the last temporary task's copper line:
           anything the assault establishment is missing comes first, and **this task authorizes a
           declaration of war on Russia** once `tactics/07`'s gates pass — 006 deliberately did not,
           and that is the one thing that changed. It authorizes nobody else and it does not authorize
           peace with Russia while Russia stands.
scope:     one enemy: Russia (player 1). No declaration on Egypt (a declared friend), Kabul (our
           suzerainty) or 那烂陀 (Scientific), no barbarian camp as a substitute, and no peace offer
           to Russia: a war of annihilation ends with their last city, not with a white peace.

## Why this is a file and not a turn-check rule

Every other instruction in this directory has a metric behind it, and AGENTS.md says a mechanically
checkable task belongs in `prompts/checks/turn-checks.md` as a `once: true` goal instead. **Eliminating
a civilisation has no metric**: `metric()` reaches our own diary row plus the combat metrics
(`end_turn._CONTACT_METRIC_KEYS`), and nothing there counts another player's cities. So the standing
instruction lives here, and the checkable *parts* of it are already rules: `siege-train`, `take-the-city`,
`hold-what-you-take`, `use-your-attacks`, `mass-on-contact`. If a rival-city-count metric ever lands,
convert this file to a goal with `metric(<rival cities>) == 0`.

## What is already true, and what is missing (measured at T115)

| Piece | Have | Gate it is for |
|---|---|---|
| siege | **2 Catapults** | `siege-train` wants **3 per city** (一城3投石车) — the binding item |
| ranged | 4 Archers | upgrade to Crossbowmen for 500 gold once 职业军队 Professional Army lands (Mercenaries) |
| melee | 4 (Warrior/Spearman tier) | **iron is 6/50 at +2/t**: a Swordsman is buildable past 20 (~T122), and the front line is Warrior-tier until then (`match-their-melee`) |
| cavalry | 1 Horseman | satisfied |
| ram / tower | none, and none wanted | human instruction 2026-09-26: 不用锤，用投石车 |
| the target | 阿斯特拉罕 (54,40) pop 3, 沃罗涅什 (50,37) pop 1, **one city still in fog** | see the read below |

**The pre-war read is no longer blocked.** `get_diplomacy`'s city line prints `walls none` /
`walls 100` and `def N` (the wall pool and the city's strength, garrison included), and
`get_map_area` radius 2 gives the ring and any unit standing on the city tile. The four numbers of
`tactics/07` step 1 are all obtainable at peace — `walls none` is a reading, not a missing one.

## The order of work

1. **Read every Russian city in four numbers** (garrison / walls / HP / ring) — 阿斯特拉罕 first, it is
   two tiles from the watch post at (54,38). **Find the third city**: Russia holds three and only two
   are visible, so a scout or the fastest cavalry goes looking before the plan is called complete. The
   abandoned branch of this map found Moscow at (54,40) and 圣彼得堡 at (56,43) — a search direction,
   not a fact, and this branch has 阿斯特拉罕 on that tile instead.
2. **Finish the establishment** (file 7's checklist, directive): the **third Catapult**, a Swordsman
   once iron passes 20, the four Crossbowman upgrades after Professional Army. Do not declare before
   it is in place: 006's whole lesson is that a war you cannot finish is a war you must not start.
3. **Run `tactics/07`'s five gates on the first target**, and only then send the declaration with
   `send_diplomatic_action`. The combat engine does not sync until the next turn, so position on the
   declaration turn and attack on the one after.
4. **Take the cities with the doctrine, not with improvisation**: stage outside enemy range
   (`tactics/04`), melee in front and siege behind at range 2 (`tactics/05`), siege knocks the walls,
   ranged shoots the pool, a capture-capable unit **moves** onto a 0 HP city the same turn (`tactics/06`,
   `take-the-city`). Three Catapults do ~260 a turn against a city that heals ~20.
5. **Hold what you take, on the turn you take it**: assign a governor or garrison the tile before the
   next turn (`hold-what-you-take`). In the abandoned branch Moscow was captured at T112 and was a Free
   City by T116 — retaking it cost nine attacks.
6. **Then the next city, and the one in fog.** Elimination means their **last** city; a crippled Russia
   left standing rebuilds while the rest of the map moves on.

## What this task is not

Not a war on Egypt (a declared friend), Kabul (our suzerainty) or 那烂陀, not a raid on a barbarian
camp as a substitute, and not a declaration that skips the gates because the army "looks big". It is
also not a licence to park: 006's failure mode was preparing for fifty turns and never declaring; this
task's failure mode is declaring and then stopping at one city.
