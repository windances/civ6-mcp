# TEMP TASK 017 — take Thebes (68,34): 战前分析, then 战前集结, then the assault

added:     2026-09-27 (human instruction: 攻打底比斯，做好战前分析和战前集结，然后开打)
expires:   turn 204 — counted from the queue, not the calendar. The T194 staging plan already put the
           Trebuchet at (66,34) and a Bombard at (68,36) **this turn**, the third shooter one turn
           behind and the melee at d1, and the pool (190/200) breaks in **two turns** at ~150 a turn —
           so the assault is 3-4 turns from T194. T204 is the margin for the ZOC rule below, a
           withdrawal and casualties. Retire it as `017-attack-thebes-done-T<n>.md` the turn the city is
           ours, or as `017-attack-thebes-expired-T204.md` with where the train stood and what blocked
           it.
done when: **Thebes (68,34) is ours** — the capture resolved with `city_action keep` (or `raze`, and
           the reason), a unit on the tile (`hold-what-you-take`), and the diary carrying the ledger:
           the four numbers re-read **at war** (garrison / walls / pool / ring, naming which came from
           a probe), the staging table with its overrides, the shots per turn, and the cost paid.
           `get_victory_progress` then shows one more Egyptian original capital under our control **if
           Thebes is that capital — read it, do not assume it**.
overrides: **this file names the objective, and ỉwnw (65,32) is not a substitute for it.** The T194
           plan pivoted *to* Thebes because the train stood closer to it, and the next plan may prefer
           the reverse — the human has named Thebes, so ỉwnw is a later target, not a substitute.
           **013's reconnaissance half is answered for this target**: the two Scouts keep sweeping for
           014 and may map the remaining Egyptian cities, but they do not hunt a different objective
           while Thebes stands. **013's gold earmark stands untouched**, and the three upgrades the
           game offered at T194 — Crouching Tiger -> Field Cannon (195g), Spearman -> Pikeman (190g),
           Crossbowman -> Field Cannon (155g) — are **not on 013's list, so this file does not buy
           them**. The one upgrade it wants is 013's own **Trebuchet -> Bombard (85g)**, and measured
           T194 that one is **refused outside friendly territory** (`CANNOT_UPGRADE ... Must be in
           friendly territory`), so bring the Trebuchet home first or fight with it as it is. No peace
           with Egypt: the directive forbids it and the war is already on.
scope:     Thebes (68,34) and the Egyptian units on its ring. Not ỉwnw, not the other Egyptian cities
           still standing, not a city-state, not a camp, and no unit off a city garrison except the
           assault force named below.

## What is already read, and what is not

| # | Number | Reading | Source |
|---|---|---|---|
| 1 | Garrison | **not read** — read the city line before the first melee attack | — |
| 2 | Walls | **`none` at T192** (ỉwnw read `none` too) — a city can finish walls mid-siege, so re-probe | T192 city read |
| 3 | HP pool | **190/200 at T194** — a melee estimate came back `CITY_CENTER (CS:0, HP:190)` | T194 `unit_action` |
| 4 | Ring | 18 ring tiles; the T194 plan assigned 8 units and named 2 unplaced | `get_staging_plan(68,34)` |

**Egypt (player 7) is already at war with us** — three of its cities are ours (Memphis (65,41), Shedet
(66,45), Abydos (68,38)) — so there is **no declaration turn to wait for**: an attack issued this turn
lands this turn. That is the one step of 016's shape this file does not repeat.

## 战前分析 — the gates, before any move

1. **Read Thebes in its four numbers** (`tactics/07`): the city line for garrison and pool, a melee
   probe for the walls, `get_map_area` on the ring for what is standing on it. `walls none` is nine
   turns old and the city has been at war since — assume nothing.
2. **Count the defenders by class and HP within two tiles.** A garrison inside the city takes **no
   damage** (`GARRISON UNITS IN CITIES`) and dies only when the city falls, so the field units are what
   cost turns, and the counter matters: anti-cavalry against cavalry, ranged against melee.
3. **Say the turn count out loud.** Three shooters at ~150 a turn against a 200 pool with no walls is
   **two turns of fire**, then the capture; with walls up, three to four.
4. **`get_victory_progress`** — if Thebes is Egypt's original capital this is Domination progress and
   the file's reason of record says so. If it is not, the reason is the human instruction, and the
   ledger says that instead of inventing a strategic one.

## 战前集结 — the staging, in this order

Run **`get_staging_plan(68,34)`** and write one row per unit — where it is, its movement, the tile it
goes to, the cost, the arrival turn, its role, whether it can fire from there — **before the first
move**. The T194 plan is the starting point and it is a sound one (siege at d2, melee at d1, both
Scouts left out), but **four of its outputs are overridden** by what this map has already measured:

- **a siege unit posted at d1 is refused** — it fires from d2 and dies at d1 (measured T163);
- **`arrive T+n` does not know our own units jam the corridor** — issue **one move per call** and
  re-read `get_units` between them (T159 and T161 both landed units 1-2 tiles short, two of them west
  of their start: the recorded pathfinder drift);
- **a firing tile is a proposal until a shot from it succeeds** — T194's own plan put Bombard #4128794
  on a tile it could not shoot from, so fire one shooter from its assigned tile **before** posting the
  others on theirs;
- **entering a Zone of Control costs the attack this turn** — T194: a Musketman moved into the ring and
  `unit_action` answered `ZOC|Unit entered Zone of Control this turn — cannot attack until next turn`.
  A unit that is meant to attack this turn **starts the turn on its tile**; the ring is entered one
  turn and attacked the next.

The force as read at T194 — **re-read before ordering anything**; a unit's tile from nine turns ago is
not a fact:

| unit | at T194 | role |
|---|---|---|
| Trebuchet #3538967 | (66,35), 2 moves | siege, d2 — the plan fires it from (66,34) |
| Bombard #4128794 | (67,37), 2 moves | siege, d2 |
| Bombard #4325376 | (66,36), 1 move | siege — the third shooter, one turn behind |
| Musketman #3932184 | (67,36), 3 moves | melee at d1, the capture unit |
| Line Infantry #4456464 | (68,37), HP 86/100, in Abydos | melee |
| Knight #3145747 | (66,45), 4 moves | cavalry for survivors, reaches d1 at T+2 |
| Crossbowman #2883591 | (64,38), HP 51/100 | ranged, d2 |
| Spearman #1572878 | (68,38), in Abydos | anti-cavalry and a second walk-in |
| Crouching Tiger #3014657 | (67,37), Range **1** | fires from **d1 only**, with melee holding the tile in front |
| Warrior #1245193 | (63,31) | the farthest melee; it may arrive after the city falls |
| Scout #262146 (66,37) and Scout #1638415 (67,34, HP 34/100) | | **recon only — never a ring tile**: CS 10 dies to the city's strike |

Out of this fight, and not to be pulled in: Crossbowman #2162705 (52,23, d21) and Field Cannon #4784149
(66,43, d9).

## 攻城执行 — the fire order

1. **The train breaks the pool, not the melee.** With no walls the three shooters do ~150 a turn.
   Record each shot's `city hp:` from its own result line: the damage estimate on a city tile describes
   the unit standing there and reads a meaningless `~0` for a non-combatant.
2. **The melee attacks from d1 the turn the pool reaches 0** — and an attack that zeroes the pool
   **captures the city outright** (measured T165), so resolve it with `city_action` the same turn or
   the turn will not end.
3. **Do not aim at the garrison while it sits inside**: it takes no damage and the city keeps its
   bonus. It becomes a target the moment it steps out.
4. **Finish what is wounded** (`finish-the-wounded`) and **cut what heals** (`cut-the-supply`): a
   wounded unit and a city both come back about twenty points a turn.
5. **Hold it on the turn you take it**: a governor or a garrison before the next turn
   (`hold-what-you-take`), and report its loyalty.

## Report when it is done

The four numbers as read at war, naming which came from a probe; the staging table with the four
overrides; the shots per turn; the capture resolution and the tile the capturing unit stood on; the
cost in units, turns and gold; whether Thebes is Egypt's original capital and what that does to the
victory projection. If it expires, say where the train stood, what the walls read, and what blocked
the assault.

## Why this is a file and not a turn-check rule

Every mechanical part of the assault is already a rule — `siege-train`, `screen-the-siege`,
`mass-on-contact`, `take-the-city`, `hold-what-you-take`, `use-your-attacks`, `finish-the-wounded`,
`cut-the-supply`, `upgrade-the-siege`. What no metric carries is **which city is the objective**: a
plan that optimises for the nearest train will pick its own target (at T194 it preferred Thebes over
ỉwnw by two tiles of marching), and the human has named Thebes. That choice, and nothing else, is what
this file exists to hold.
