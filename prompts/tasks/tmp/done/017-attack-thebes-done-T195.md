# TEMP TASK 017 — take Thebes (68,34): 战前分析, then 战前集结, then the assault

added:     2026-09-27 (human instruction: 攻打底比斯，做好战前分析和战前集结，然后开打)
expires:   turn 204 — counted from the queue, not the calendar, and **re-derived from T194's own shots**
           rather than from the plan. T194 fired **one** shot that landed — the Trebuchet, 31 damage
           (the pool read 200/200 on the result line, then 169 on the next read) — and the other two
           shooters dealt nothing: one had already spent its movement (`NO_MOVES`) and one stood on
           (67,36) and answered `NO_LOS` twice. So 169 left is five to six turns of one shooter, or two
           turns once all three fire from tiles that have **proven** they can. T204 is the margin for the
           ZOC rule below, a withdrawal and casualties. Retire it as `017-attack-thebes-done-T<n>.md` the
           turn the city is ours, or as `017-attack-thebes-expired-T204.md` with where the train stood and
           what blocked it.
done when: **Thebes (68,34) is ours** — the capture resolved with `city_action keep` (or `raze`, and
           the reason), a unit on the tile (`hold-what-you-take`), and the diary carrying the ledger:
           the four numbers re-read **at war** (garrison / walls / pool / ring, naming which came from
           a probe), the staging table with its overrides — **written out before the first `unit_action`
           of the turn**, one row per unit, not merely requested from `get_staging_plan` — the shots per
           turn and the tile each one came from, and the cost paid.
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
           friendly territory`), so bring the Trebuchet home first or fight with it as it is.
           **013's clock runs out at T195, and this file does not extend it**: either the Trebuchet walks
           onto our own ground at T195 and 013 buys the upgrade, or 013 retires as
           `013-upgrade-and-scout-expired-T195.md` and **this file fights with the Trebuchet as it is**
           (36/100 HP, healing at (66,35) at the end of T194). No peace
           with Egypt: the directive forbids it and the war is already on.
scope:     Thebes (68,34) and the Egyptian units on its ring. Not ỉwnw, not the other Egyptian cities
           still standing, not a city-state, not a camp, and no unit off a city garrison except the
           assault force named below.

## What is already read, and what is not

| # | Number | Reading | Source |
|---|---|---|---|
| 1 | Garrison | **read at T194, and there is no military garrison**: the city tile's unit list reads `[CITY_CENTER] ... **[<name> GREAT_WRITER]**` — a civilian, which does not defend. Re-read the tile's list at T195, because a defender can still arrive in the AI turn | T194 `get_map_area(68,34,2)` |
| 2 | Walls | **`none`, re-read at T194** — the shot's own result line printed `city hp: 200/200, walls: none` (ỉwnw read `none` too). A city can finish walls mid-siege, so re-probe | T194 `unit_action` |
| 3 | HP pool | **200/200 before T194's shot, 169 after it** — the result line said `200/200 (read unchanged)` and the **next** read said `HP:169`, so the shot did land: **31 damage, and the immediate post-combat read lied** (the `End Turn Blockers` trap, `AGENTS.md`) | T194 `unit_action` |
| 4 | Ring | 18 ring tiles; the T194 plan assigned 8 units and named 2 unplaced — **but its `SPARE RING TILES` list is not LOS-checked**: (67,36) is on that list and answered `NO_LOS` twice | `get_staging_plan(68,34)` |

**Egypt (player 7) is already at war with us** — three of its cities are ours (Memphis (65,41), Shedet
(66,45), Abydos (68,38)) — so there is **no declaration turn to wait for**: an attack issued this turn
lands this turn. That is the one step of 016's shape this file does not repeat.

## 战前分析 — the gates, before any move

1. **Read Thebes in its four numbers** (`tactics/07`): the city line for pool and walls, **the city
   tile's own unit list for the garrison** (`get_map_area` prints it; measured T194 it held a Great
   Writer, i.e. nothing that fights), and the ring for what is standing on it. `walls none` is worth
   re-probing every turn — a city can finish walls mid-siege.
2. **Count the defenders by class and HP within two tiles.** A garrison inside the city takes **no
   damage** (`GARRISON UNITS IN CITIES`) and dies only when the city falls, so the field units are what
   cost turns, and the counter matters: anti-cavalry against cavalry, ranged against melee.
3. **Say the turn count out loud, from shots that landed rather than from the plan.** T194 fired one
   shot, for 31: the pool is now 169. Three shooters that all bear on the city do on the order of 100
   a turn, so two to three turns of fire and then the capture; with only the Trebuchet's tile proven,
   five to six. With walls up, add two.
4. **`get_victory_progress` is a gate, not a suggestion — and it is the one gate T194 never ran**
   (measured: 0 calls in that session's log, while it already held that Egypt's original capital is
   Alexandria, still in fog). If Thebes is that capital this is Domination progress and the file's
   reason of record says so; if it is not, the reason is the human instruction, and the ledger says
   that instead of inventing a strategic one. Read it this turn.

## 战前集结 — the staging, in this order

Run **`get_staging_plan(68,34)`** and write one row per unit — where it is, its movement, the tile it
goes to, the cost, the arrival turn, its role, whether it can fire from there — **before the first
move**. The T194 plan is the starting point and it is a sound one (siege at d2, melee at d1, both
Scouts left out), but **six of its outputs are overridden** by what this map has already measured —
and **the table is not the tool's output**. Call `get_staging_plan`, then **write the seven columns out
yourself before the first `unit_action` of the turn**: where it is, its movement allowance, the one
tile it goes to, the `get_pathing_estimate` cost, the turn it arrives, its role, whether it can fire
from there. Measured T194: the tool was called once and 36 `unit_action` calls followed with no table
written anywhere, and both of the plan's siege proposals failed for reasons the table would have shown.

- **a siege unit posted at d1 is refused** — it fires from d2 and dies at d1 (measured T163);
- **`arrive T+n` does not know our own units jam the corridor** — issue **one move per call** and
  re-read `get_units` between them (T159 and T161 both landed units 1-2 tiles short, two of them west
  of their start: the recorded pathfinder drift);
- **a firing tile is a proposal until a shot from it succeeds** — T194's own plan put Bombard #4128794
  on a tile it could not shoot from, so fire one shooter from its assigned tile **before** posting the
  others on theirs. The plan's `SPARE RING TILES` line is **not LOS-checked at all**: it offered
  (67,36), and a Bombard standing there answered `NO_LOS` twice.
- **a shooter that spends its movement cannot shoot at all** — T194: Bombard #4325376 moved one tile,
  and its attack came back `NO_MOVES|Unit has no movement points for ranged attack. Ranged attacks
  require movement`. That turn's shot was simply lost. The plan's `arrive this turn - FIRE from here`
  is true only when the move ends with a movement point left; measure that, or budget the extra turn.
- **entering a Zone of Control costs the attack this turn** — T194: a Musketman moved into the ring and
  `unit_action` answered `ZOC|Unit entered Zone of Control this turn — cannot attack until next turn`.
  A unit that is meant to attack this turn **starts the turn on its tile**; the ring is entered one
  turn and attacked the next.

**Where the train stands after T194** — the state a T195 move order has to start from, and **re-read
before ordering anything**; a unit's tile from one turn ago is not a fact:

| unit | at the start of T194 | ended T194 | role |
|---|---|---|---|
| Trebuchet #3538967 | (66,35), 2 moves, HP 36 | (66,35), **fired for 31**, then `heal` | siege, d2 — its tile is the **only** one that has produced a shot on Thebes |
| Bombard #4128794 | (67,37), 2 moves, HP 88 | (67,36) — `NO_LOS` twice, then `heal` | siege, d2 |
| Bombard #4325376 | (65,37), 2 moves, HP 100 | (66,37) — moved, then `NO_MOVES`, promoted `PROMOTION_GRAPE_SHOT`, fortified | siege — the shot was lost, the tile was not the problem |
| Musketman #3932184 | (67,36), 3 moves | **(67,34) d1, fortified** — the capture unit is already on the ring | melee |
| Line Infantry #4456464 | (66,39), HP 86 | (68,37), `STOPPED_MID_PATH`; `CANNOT_HEAL` then `CANNOT_FORTIFY` both refused | melee |
| Knight #3145747 | (66,45), 4 moves | (67,43), `STOPPED_MID_PATH`, fortified | cavalry for survivors |
| Crossbowman #2883591 | (64,38), HP 51 | unchanged, `heal` | ranged, d2 |
| Spearman #1572878 | (68,38), in Abydos | unchanged, already fortified 2 turns | anti-cavalry and a second walk-in |
| Crouching Tiger #3014657 | (67,38), Range **1** | **(68,36), fortified** | fires from **d1 only**, with melee holding the tile in front |
| Warrior #1245193 | (62,31) | moved to (64,31), then **killed in the AI turn** (`end_turn` T194: "Your Warrior was killed - last seen at (62,31)"; that coordinate is the stale one — confirm in T195's `get_units`) | **gone** |
| Scout #262146 | (66,37) | (66,38), then (65,38) | **recon only — never a ring tile**: CS 10 dies to the city's strike |
| Scout #1638415 | (66,36), HP 34 | `BLOCKED` — did not move | recon only |

Out of this fight, and not to be pulled in: Crossbowman #2162705 (52,23, d21) and Field Cannon #4784149
(66,43, now (67,42), d9).

## 攻城执行 — the fire order

1. **The train breaks the pool, not the melee.** T194's measured rate was **31 damage from one shot and
   zero from the other two**, so count shots that landed, not shooters on the board. Record each shot's
   `city hp:` from its own result line — and read the city again a call **later**, because the
   immediate post-combat line can say `read unchanged` after the damage landed (T194: 200/200, then
   169). The damage estimate on a city tile describes the unit standing there and reads a meaningless
   `~0` for a non-combatant.
2. **The melee attacks from d1 the turn the pool reaches 0** — and an attack that zeroes the pool
   **captures the city outright** (measured T165), so resolve it with `city_action` the same turn or
   the turn will not end.
3. **Do not aim at the garrison while it sits inside**: it takes no damage and the city keeps its
   bonus. It becomes a target the moment it steps out.
4. **Finish what is wounded** (`finish-the-wounded`) and **cut what heals** (`cut-the-supply`): a
   wounded unit and a city both come back about twenty points a turn.
5. **Hold it on the turn you take it**: a governor or a garrison before the next turn
   (`hold-what-you-take`), and report its loyalty. **The governor lever may already be spent by then**:
   T194 read `Governor Points: 0 available, 8 spent`, and at T195 the one available governor went to
   Abydos (68,38) instead — loyalty 47/100, losing 3.6/turn, revolting in 14, and it is the city this
   assault marches past. So the lever for Thebes is a **unit on its tile**, and Abydos has to be
   watched: Moscow was captured at T112, revolted by T116 and retaken at T121. Losing a city we already
   hold while taking Thebes is the way this war is actually lost.

## Report when it is done

The four numbers as read at war, naming which came from a probe; the staging table with the six
overrides and the **tile each shot came from**; the shots per turn and what they actually took off the
pool; the capture resolution and the tile the capturing unit stood on; the cost in units, turns and
gold; whether Thebes is Egypt's original capital and what that does to the victory projection; and the
loyalty of both Thebes and Abydos. If it expires, say where the train stood, what the walls read, and
what blocked the assault.

## Why this is a file and not a turn-check rule

Every mechanical part of the assault is already a rule — `siege-train`, `screen-the-siege`,
`mass-on-contact`, `take-the-city`, `hold-what-you-take`, `use-your-attacks`, `finish-the-wounded`,
`cut-the-supply`, `upgrade-the-siege`. What no metric carries is **which city is the objective**: a
plan that optimises for the nearest train will pick its own target (at T194 it preferred Thebes over
ỉwnw by two tiles of marching), and the human has named Thebes. That choice, and nothing else, is what
this file exists to hold.

## Outcome — taken at T195, and one correction to the text above

The `done when:` held at T195: the Musketman #3932184 attacked from (67,34) d1, its attack zeroed the
pool **and moved it onto the city tile** — the follow-up `move` answered `STACKING_CONFLICT|Friendly
UNIT_MUSKETMAN already on (68,34)`, which is what a capture looks like from the outside — and Thebes
is ours: city id **1048591**, pop 3, garrison Musketman 87/100 fortified. A governor was assigned the
same turn and the city's empty queue set to a Monument. The filled ledger (the four numbers, each shot
with the tile it came from, the cost — the Warrior #1245193 was killed in the AI turn — and the new
city's loyalty at 50/100 losing 16.1/turn, revolting in 4) is the T195 diary entry; the calls are in
`.civ6-mcp-data/log_china_-1894041591_silver-scarlet-parapet-72.jsonl`, whose own `seq` field runs
0-98 across the two turns (T194 0-61, T195 62-98).

**Correction — `NO_LOS` is a reading of the moment, not a verdict on the tile.** The three places above
that describe (67,36) as a tile that "answered `NO_LOS` twice" are true of T194 and **wrong as a
conclusion**: at T195 the same Bombard #4128794 fired from that same tile and took the city 189 -> 125.
So the refusal at T194 was stale (the reply's own wording allows it — "LOS blocked **or unit already
attacked this turn**"), and a firing tile refused once has to be re-tested on a later turn before it is
written off. This file's own override — "a firing tile is a proposal until a shot from it succeeds" —
cuts both ways, and the T194 note that read two `NO_LOS` replies as a dead corridor drew a conclusion
the next turn refuted.
