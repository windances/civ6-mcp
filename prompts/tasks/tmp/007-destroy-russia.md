# TEMP TASK 007 — destroy Russia

added:     2026-09-26 (human instruction: 消灭俄罗斯)
expires:   turn 160 — the third Catapult is the gate (一城3投石车) and it lands ~T124, the iron
           stockpile passes 20 ~T121 and the war is four cities at T119 (two of them still in fog)
           at 4-8 turns each plus the march; count from the queue, not the calendar. Retire it early
           if Russia is gone, or as `007-destroy-russia-expired-T160.md` with a report of which
           cities stand and why.
done when: **Russia is eliminated** — `get_diplomacy` **no longer** lists a Russian city, every city
           we took has been resolved with `city_action` keep/raze, and no Russian unit is left inside
           our territory. Report the count of Russian cities taken, counted as you take them (Russia
           held **four** at T119 — 阿斯特拉罕 pop 5 (54,40), 沃罗涅什 pop 2 (50,37) and two in fog —
           not the three this file first recorded), and say which ones were found only on the march.
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

## What is already true, and what is missing (first measured at T115, re-read at T123)

| Piece | Have (T123) | Gate it is for |
|---|---|---|
| siege | **3 Catapults — gate met at T122** | `siege-train` satisfied; Military Engineering (T123) unlocks the **Trebuchet** upgrade for all three, which `upgrade-the-siege` will demand during a war |
| ranged | **3 Crossbowmen** (CS 30 / RS 40), one Archer left | the fourth upgrade is 125 gold |
| melee | **1 Man-at-Arms (CS 45)**; Apprenticeship skipped the Swordsman tier | a second Warrior upgrade is 125 gold; `match-their-melee` is answered by the 45, not by a Swordsman |
| cavalry | 1 Horseman | satisfied; Stirrups (in research at T123) would make it a Knight |
| ram / tower | none, and none wanted | human instruction 2026-09-26: 不用锤，用投石车 |
| iron | **22/50 at +2/t** (was 6 at T114); NITER also revealed at T123 | the melee upgrades are gold-gated now, not iron-gated |
| the target | **four** cities at T119: 阿斯特拉罕 pop 5 (54,40), 沃罗涅什 pop 2 (50,37), **two in fog** (three at T110 — it grows) | see the read below |

**The pre-war read is no longer blocked.** `get_diplomacy`'s city line prints `walls none` /
`walls 100` and `def N` (the wall pool and the city's strength, garrison included), and
`get_map_area` radius 2 gives the ring and any unit standing on the city tile. The four numbers of
`tactics/07` step 1 are all obtainable at peace — `walls none` is a reading, not a missing one.

**The target list is a snapshot, not a constant — and it is not a prerequisite.** Russia stood at
three cities when this file was written and at **four** by T119, two of them in fog, and the session
caught the drift on the turn it read the file. The count matters for the *end* (elimination), not for
the trigger: **the declaration waits on the first target's numbers, not on the whole map** (human
instruction 2026-09-26: 不用获取所有城市信息才开战). Read each remaining city when the army reaches it —
the march finds them better than a scout does, and entry to Russian ground is refused even while
Russia is FRIENDLY with Open Borders signed (measured T96 and T119: an order straight to (50,37) came
back `BLOCKED (foreign ...)`). Count the cities as you take them, the same way a camp coordinate is
re-read from the map rather than trusted from an old diary (T65 said (60,30); T83's read put it at
(60,29)).

## The order of work

1. **Read the FIRST TARGET in four numbers** (garrison / walls / HP / ring) — 阿斯特拉罕 is the
   nearest, two tiles from the watch post at (54,38), so that is the city the gates run on. The four
   numbers are needed for **the city being attacked, not for all of them**: the two still in fog are
   found by the march itself and read the turn the army stands outside them. Keep the Horseman and the
   Scout looking, but they are **not** a gate. The abandoned branch of this map found Moscow at (54,40)
   and 圣彼得堡 at (56,43) — a search direction, not a fact, and this branch has 阿斯特拉罕 on that tile
   instead.
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
