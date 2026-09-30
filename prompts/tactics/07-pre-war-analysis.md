# 7. Pre-war analysis / 战前分析：能不能打、打谁、几回合、损失多大、打完守不守得住（含蛮族营地）

Read before a war is declared, and again whenever a target changes — **and whenever a barbarian camp
is visible near our cities or our Builders.** Files 1-6 are about fighting a war; this one decides
whether to start it, and the same analysis answers whether a camp is worth a raid.

**This file has two target classes, and both are pre-war analysis objects.** An enemy **city** is a
*war*: it has walls, a garrison and an HP pool, and the decision is whether to declare. A **barbarian
camp** is a *raid*: no HP, no walls, no declaration — and the human made it a standing target on
2026-09-26 ("make the barbarian camp a pre-war analysis target and destroy it"), after the camp beside
北京 produced the Spearman that cost 160 gold at T65. A camp is not a footnote to the city procedure;
it is the second object that procedure is run on.

**And this analysis is the first of three phases that run on every target** (human instruction
2026-09-26: 战前分析、攻城前集结、攻城执行适用于所有城市和蛮族营地). One target at a time, in this
order, whichever class it is:

1. **战前分析 — this file.** Read the target in its own numbers and run the gates (five for a city,
   C1–C6 for a camp). The trigger is the target **being attacked**, not every target on the map:
   不用获取所有城市信息才开战 still holds, and reading the rest is not a gate.
2. **攻城前集结 — `prompts/tactics/04-staging-out-of-range.md`**, whose step 3b table is built by
   `get_staging_plan(x, y)` on the **target's own tile**: a camp's tile exactly as a city's. The
   reply names the object (`STAGING PLAN for the camp at x,y`, `WALK-IN OPENS`) and the ring, the
   paths and the distinct-tile assignment are the same for both.
3. **攻城执行 — `prompts/tactics/05-formation-and-screening.md`** and
   **`prompts/tactics/06-assault-composition-and-fire.md`**: formation, order of work, capture. For a
   camp the last step is a walk-in against an object with no HP and no walls, so the pair that
   matters is a shooter and an **unspent** military unit — never a Scout, Builder or Trader.

A raid that skips a phase is how this war lost turns: T159's eight grouped move orders put one of
eight units on 喀山's ring, and no Trebuchet ever fired at it.

The directive's gate is "declare only when the army in place can take the cities". That is a
judgement, and this file is how to make it from numbers rather than from hope. It is **one
procedure in seven steps**, and every step names the query that answers it:

| Step | Question | For a city (the war branch) | For a camp (the raid branch) |
|---|---|---|---|
| 0 | Is there a target to analyse at all? | `get_deal_options`, `get_strategic_map`, the map around our cities | the map around our cities: a tile whose improvement is `IMPROVEMENT_BARBARIAN_CAMP` |
| 1 | What is the target, in numbers? | the city probe (hp / walls / **garrison** / ring) | the camp tile's terrain, and **the guard within two tiles** (camp gate C1) |
| 2 | Do the gates pass? | the **five gates** below | the **six camp gates** below (C1–C6) |
| 3 | How long, and what will it cost? | the formula below, plus the loss asymmetry | the walk-in's movement, plus the units pulled off the plan |
| 4 | What can be bought first? | `get_policies`, `purchase_item`, `upgrade_unit` | the same — a ranged unit is usually the cheapest answer to a guard |
| 5 | Where do we assemble, and when do we move? | `get_pathing_estimate`, the ring walk; the declaration trigger | `get_pathing_estimate`: a tile we hold, one move from the camp |
| 6 | Does anyone come to its rescue? | `get_units` on the enemy, `get_diplomacy` | **yes — the guard itself**, plus what the camp keeps spawning |
| 7 | Can we hold what we take? | loyalty pressure, governor, garrison | the ground we clear, and which city gives up its garrison meanwhile |

**Step 0 has two doors.** Steps 1–7 below are written out for the first: an enemy **city**, which is a
*war* decision with a declaration attached. The second is a **barbarian camp**, which is a *raid* — no
declaration, no walls, no HP pool, and its own gates, in "The other target" after Step 0. A camp that
is spawning units next to one of our cities is a target this file is responsible for, and the human
asked for it in as many words on 2026-09-26.

---

## Step 0 — a visible target, or none of this can start

**No visible candidate city, no analysis.** Everything below is measured against a named city, so the
first pre-war task is often reconnaissance, not arithmetic. Send the scout and the fastest cavalry
toward the likely neighbour, check `get_strategic_map` and `get_pathing_estimate`, and consider an
embassy or a spy for the capital.

Live T99: five cities, gold 173 at +34.8 a turn, and an army already in the doctrine's shape (two
Catapults, four Archers, two Warriors, one Heavy Chariot) — with **no enemy city visible at all**,
only a city-state. Every gate below was unevaluable, and the reports that could still be produced
were about our own army and the barbarian navy two tiles off the coast. An army that is ready and a
target that is not in sight is a war that has not started.

**The cheapest reconnaissance is the trade screen.** `get_deal_options(other_player_id)` hands over a
met civilization's city list with populations, which of those cities is its original capital, its
strategic and luxury stockpiles, and its gold and gold-per-turn — with no open borders, no scout
reaching anything, and no war. Live T99: the scout was stopped dead at the Russian border
(`BLOCKED (foreign territory (俄罗斯) - need Open Borders via propose_trade)`) and the same turn
`get_deal_options(1)` answered that Russia holds three cities — St Petersburg (population 8, its
capital), Moscow (3) and Astrakhan (1) — that they have 37 iron against our none, and that their
economy runs at minus three gold a turn. That satisfied Step 0 and answered a logistics question the
army would otherwise have hit after declaring war: the Swordsman and Knight upgrades need iron we do
not have.

## The other target: a barbarian camp — a raid, not a war

**A camp is a target of this analysis too** (human instruction, 2026-09-26; it supersedes the earlier
directive line "do NOT clear barbarian camps", which valued a camp only as a pool of units for the
Three-Six Stratagems conversion). A camp beside our cities spawns era-appropriate units, and the cost
of leaving it is measured in Builders and trade routes, not in battles: live T65 the camp at (60,30)
had produced the 枪兵 Spearman at (60,29) that stood two tiles from a Builder at (58,29) and forced a
**160-gold Warrior purchase** to cover it.

What a camp is **not** is a city. It has no HP pool, no walls and no garrison bonus — **one military
unit moving onto the camp tile destroys it**. That is the same walk-in mechanic as a capture (Step 2
gate 3, file 06), so the question is never whether the camp *can* be destroyed. It is whether the
walk-in survives the guard, and whether the raid costs more than it buys.

| Gate | Question | Answered by |
|---|---|---|
| C1 guard | how many barbarian units are within 2 tiles, of what class, at what HP | `get_map_area` around the camp, `get_units` |
| C2 ground | terrain and feature of the camp tile, and what the last step costs | the raw tile record (`scripts/probe-tile.py`) |
| C3 force | two attackers with the counter unit, and the one that steps in | the counter table (file 02) |
| C4 approach | a tile we already hold, one move from the camp | `get_pathing_estimate`, hex distance |
| C5 worth | gold, era score, the inspiration, and what it has been spawning | civic boost status, the map |
| C6 hold | what stays behind, and which unit walks home | `get_cities` garrisons |

**C1 — the guard is the enemy, not the camp.** A camp with nothing around it is a free walk-in. The
dangerous shape is the one measured at T65–T67: a camp that had been spawning Spearmen with one of
them parked two tiles away, in reach of a civilian. Count **every** barbarian within two tiles of the
camp and record class, CS and HP, because the class decides the counter in C3.

**C2 — the ground decides the last step.** A camp on hills, or in forest/jungle, is 2 MP and gives the
defender terrain defence; a marsh is 2 MP; a river between the approach tile and the camp spends the
crossing; a camp in a mountain pocket has one lane. Movement is per tile, not per distance (the
T103–T130 war lost five turns to one-tile moves that cost two points), so the walk-in must start from
a tile **adjacent to the camp, held since the turn before**.

**C3 — two attackers, and the right ones.** `mass-on-contact` applies to a raid exactly as to a war:
one attacker trades. Barbarian Spearmen are `PROMOTION_CLASS_ANTI_CAVALRY`, so **cavalry is the wrong
unit against them** — ranged fire (which takes no retaliation) plus a melee unit to step onto the tile
is the cheap pair, and the walk-in must arrive **unspent**, because the camp tile is one move and it
must be that move. Never send a Scout, a Builder or a Trader: a civilian cannot take the tile and will
be captured instead.

**C4 — the approach.** The same rule as a city: choose a rally tile about two tiles out, outside the
guard's reach, reachable in one turn, and hold it the turn before. **`get_staging_plan(camp_x,
camp_y)` builds exactly this ring** — pass the camp's tile, the reply says `STAGING PLAN for the camp
at x,y` and `WALK-IN OPENS`, and the row that must arrive **unspent** is the walk-in. A camp four or
more tiles from the nearest city with no unit nearby is a job for a unit that is already out there,
not a march — say so rather than moving the army.

**C5 — what it is worth.** A cleared camp pays gold, a little era score, and — if `CIVIC_MILITARY_TRADITION`
is not yet inspired — **the inspiration that halves that civic** (its boost is "clear a barbarian
camp"; it read `boosted=True` at T59 in this branch, so here that part is already banked). The real
payoff is what clearing stops: a live camp keeps producing era-appropriate units next to our cities,
and the unit it produced is what the 160 gold at T65 was spent on. Compare that with the raid's cost:
the units pulled off the development plan, and the garrison a city gives up while they are away.

**C6 — hold, and the ability the old rule was protecting.** A camp is also the only source of units for
三十六计 Three-Six Stratagems, which the adapter cannot trigger — the human plays it from the game UI
and it consumes the melee unit. So **before the raid, report any barbarian standing adjacent to one of
our melee units whose type is worth converting**, so the human can convert first if they want it. Then
clear the camp anyway: the ability is an opportunity, not a reason to leave a spawner beside 北京. And
name which city loses its garrison while the raid runs.

---

## Step 1 — read the target: four numbers, in this order

| # | Number | Where | Why it is this order |
|---|---|---|---|
| 1 | **Garrison** — the unit on the city tile, and what it is | `get_map_area` on the city tile lists the units standing there; the city's own strength is the `def N` on `get_diplomacy`'s city line | It decides the fire arithmetic more than walls do (Step 2, gate 1) |
| 2 | **Walls** — `walls none`, or the wall pool's maximum | the same city line: `walls none` / `walls 100` | Decides whether a siege unit is mandatory (gate 4) |
| 3 | **HP pool** | not reported at peace | Always 200 for a city; it is the denominator, not the question |
| 4 | **The ring** — every tile at distance ≤ 2, and which are passable | `get_map_area` radius 2 around the city | It is the ceiling on how many shots a turn you can fire (gate 2) |

**All four are readable at peace**, from `get_diplomacy`'s city line plus one `get_map_area` — and
**`walls none` is a number, not a missing one**: the line prints the wall pool, so silence would mean
the read failed while `walls none` means the city has no outer defences. Reading the absence of a wall
flag as "the tools cannot tell me" is what kept `task 006`'s declaration gate shut from T94 to T115.

A civilian is not a defender (a Great Writer inside 圣彼得堡 did not slow archer fire at all), and a
garrison that is a CS 35 Swordsman roughly **triples** the city's effective defence. Both were
measured; both are invisible if you only read `walls`.

## Step 2 — the five gates

All five must pass **on a named city**. Four of them are checkable before the declaration; the fifth
is checkable the turn the stack forms.

### Gate 1 — net fire > 0, computed against the **garrison**

```
gross   = sum of damage each shooter can do to THIS city (see the table)
healing = 20/turn while the city has a supply line, 0 when all six adjacent hexes are cut
net     = gross - healing        must be > 0, and comfortably so
```

| Shooter | City with a CS 35 garrison | City ungarrisoned |
|---|---|---|
| Archer (RS 25) | **9–11** | **35** |
| Catapult / Trebuchet (Bombard) | **45–52** | **45–52** |

Measured over T103–T130. The consequence is not academic: two Archers at 9–11 are 18–22 gross
against a 20 heal, i.e. **exactly zero progress**, which is what Moscow's first two turns of fire
produced (T107: 9 a shot; T108: 11 a shot). Two Catapults clear the heal on their own.

Two ways to fix a failed gate 1, in order of cost:
- **Catapults** — barely affected by a garrison, and cheaper than waiting.
- **Invite the sortie** — a garrison that attacks out loses the city its bonus for that turn. T109:
  the Swordsman left Moscow, and the same four shooters went from ~11 a shot to **95 in one turn**.

If neither is available, do not declare. Net fire at or below zero is a `SIEGE STALLED` in advance.

### Gate 2 — the ring can hold the shooters

A siege fires as many shots as its **ring** allows, not as many as the army has shooters: a unit
fires only from a tile at distance ≤ 2, with line of sight, reached with movement to spare. Count
before committing:

- **Moscow: 6 usable ring tiles.** Four Archers and two Catapults all fired.
- **圣彼得堡: 3** — (57,41) and (54,42) are impassable mountains.
- **阿斯特拉罕: 3** — its whole east side is mountains, so six shooters meant three shots a turn.

Live T107: the same two tiles of range that let an Archer hit Moscow refused a Catapult `NO_LOS` →
firing positions are per tile **and per unit**, and a tile is only a firing position once a shot from
it has been ordered and not refused.

**This gate is answerable before the declaration now** (2026-09-30): `get_staging_plan(target)` runs on
the tile before any war is declared, and its header counts the ring tiles **with line of sight** while
each shooter's row carries `FIRE` / `FIRE?` / `NO LINE OF SIGHT: <blocker>`. The map's rule is the
manual's (`manual:999`, on the game's own `SightThroughModifier`), and for a gun already standing on a
ring tile the query asks the engine itself (`CANFIRE`), which overrides the map. `FIRE?` is the one
case to settle by ordering the shot.

**Deliverable: the firing list, before the declaration.** Name the tiles at distance ≤ 2 from the
target that our siege units can shoot from — from the plan's per-tile verdict, with `SIEGE POSTURE` as
the in-turn arbiter, never a hand-computed distance — and say which of them the column can reach with a
movement point to spare. Measured at
阿斯特拉罕 (54,40) on T140–T143: **one** Catapult tile worked ((54,38)); (55,38) is distance 2 with no
LOS and (56,38) is distance 3, so three Catapults fired twice a turn and a 200-point pool stood for
three turns. The arithmetic in gate 1 assumes every shooter fires — this list is what makes that
assumption true or false.

**If the ring is smaller than the number of shooters, the siege is longer than the arithmetic says,
by exactly that ratio.** Either accept the longer timetable in the plan, or do not start.

### Gate 3 — a capture-capable unit can be **adjacent at the start of the turn the pool empties**

Melee, anti-cavalry and cavalry can take a city; ranged, siege and support cannot. "In reach" is not
enough — all three of these were violated once in the T103–T130 war:

1. **Adjacent at the start of the turn.** T129: a four-tile order with four movement points reached
   three tiles, and the zone of control refused the last step. T117: a Warrior ordered onto the
   capital from three tiles away walked in the wrong direction.
2. **Unspent.** The capture is a MOVE; attacking spends all remaining movement. T110: Moscow fell
   because the Chariot was ordered to move rather than to attack.
3. **Healthy.** T115: a 9 HP unit died taking a 0/200 city and the city stayed Russian.

This — not the damage — is the gate that decides wars: Moscow was broken to 0 at T120 in the
abandoned line and stood for four turns because nobody was adjacent, and the bombardment had to be
fought again from nothing.

### Gate 4 — walls have an answer

Without a siege unit, ranged fire pays the wall penalty and the assault stalls. Never start against a
walled city without one, and let the wall pool decide **how many**: one gun is enough where the ground
and the ranged line already cover it, two or three when they do not (human instruction 2026-09-30:
攻城使用2或3辆投石车，根据实际情况而定，不写死，当地面和远程部队攻击力够的话，一辆也可以). **No
Siege Tower and no Battering Ram is the answer here** (不生产也不使用撞锤/攻城塔): the Catapult is, and a
melee unit beside a tower we do not field is a melee unit trading blows for nothing.

**Read the walls before assuming.** Every Russian city was wall-less for the entire T103–T130 war
(`walls 0/0` in every probe), which made the Battering Ram a 65-production unit that did nothing for
seventeen turns and made the two Catapults a damage tool rather than a wall-breaker. The reverse
mistake costs more: a city that finishes Ancient Walls mid-siege doubles the job.

### Gate 5 — the approach, and the declaration trigger

- **Walk the route.** Movement is not one point per tile: a river or a hill can cost a unit its whole
  turn, and a ranged attack needs movement left over (`NO_MOVES|Ranged attacks require movement`).
  Five turns were lost to this in one war — twice to a Catapult that moved a single tile and could
  not fire. `get_pathing_estimate` is the check; straight-line distance lies (a Trebuchet at (55,42)
  answered `NO_LOS` to a city two tiles away).
- **Massing on a border is what triggers the declaration.** T103: Peter's border complaint arrived
  the turn the column closed on his frontier, the refusal was taken as the answer, and Russia
  declared with our army two turns short of its staging row. Stage where the army can already fight,
  and treat the enemy declaring first as the expected case rather than the surprise.
- **Who else is watching.** Defensive pacts turn one war into three (`get_diplomacy`), and the
  home garrison has to cover the second front (`one-garrison-per-city`).

## Step 3 — time, and losses

```
turns to break   ~= ceil( (city HP + wall HP) / (damage per turn - 20 if the supply line is open) )
turns to assemble = max( slowest damage unit in position, capture unit ADJACENT and unspent )
the bigger of the two is the answer
```

- Measured anchor, T120–T122 (abandoned line): 200 HP, no walls, supply 4/6 — two Trebuchets and
  three to four Archers did 60–110 a turn, 40–90 net, and the city fell in **three turns**.
- Measured anchor, T103–T130 (this war): Moscow (garrisoned) took seven turns of fire; 圣彼得堡 (no
  garrison) took five turns *including the march*; 阿斯特拉罕 (pop 3, garrisoned) took six.
- **Losses are asymmetric.** Ranged and siege take **no retaliation** — three turns of fire, zero HP
  lost. A garrison inside a city never takes damage while the city is attacked, so it is never a
  reason to spend an attack. An ungarrisoned wall-less city does not retaliate against melee at all
  (36 and 44 damage measured, 0 taken); a city **with** a garrison does, and a melee unit that
  attacks fights the city at full strength no matter its own HP.
- **The real losses come from the field, and from our own carelessness with wounded units.** All
  three units lost in the T103–T130 war were at 9, 23 and 35 HP inside an enemy's reach. Rotate them
  home (20 HP/turn in a city, 15 in friendly territory) instead of leaving them in the line; the end
  of every turn prints `WOUNDED IN REACH` for exactly this.

## Step 4 — pre-war power: policy and gold, not production

Measured at T196 (7 cities, 992 gold, +15.8/turn, 14 fighting units): the whole army could be upgraded
for 2,290 gold, or **1,145 with Professional Army** (Mercenaries' 50% upgrade discount) — so one
policy card is worth more than a thousand gold. Priority order:

| Buy | Cost | Gain |
|---|---|---|
| Professional Army policy card | 0 | halves every upgrade below |
| 4x Archer -> Crossbowman | 250 each (125) | +15 ranged strength each, and ranged is the only zero-retaliation damage |
| 3x Heavy Chariot -> Knight | 320 each (160) | +20 combat strength each, which is what `match-their-melee` complains about |
| Military-leaning government | free on change | more military policy slots |

Free multipliers that are easy to forget: a **Great General** with the stack (+5 CS, +1 movement
within two tiles), religious beliefs such as Crusade where the target follows your religion, a
Militaristic city-state suzerainty, and **Corps/Armies for melee and cavalry only** — merging two
ranged or siege units trades two attacks for one and is a net loss of fire (file 6).

One caveat on upgrades, measured: **only units standing on our own soil can upgrade** (`upgrade_unit`
offered exactly one of five Archers — the one in 北京). Rotating a front-line Archer home is part of
the pre-war plan, not an afterthought.

Producing units is the slowest lever: one Trebuchet is roughly eight to twelve turns in a single
city, so production buys the *next* war while gold and policy buy this one.

## Step 5 — assembly, and the turn the order is given

- Rally **one tile outside the target's range** (a city that has walls shoots at range 2), siege at
  range 2-3 with line of sight confirmed, melee at range 1 ready to walk in. **Melee on the ring,
  shooters one tile behind it, and at least one ring tile left free for the capture move** — at
  阿斯特拉罕 the shooters occupied both adjacent tiles and the melee could not reach the city.
- Do not wait for a straggler: start when the fire is positive and a capture unit is in reach;
  `siege-train`, `ranged-mass` and `melee-screen` say what "enough" means each turn.
- **Anything that has to happen before the declaration happens here**: the upgrades (Step 4), the
  governor for the city you are about to take (Step 7), and the road or the lane the reinforcements
  will use.

## Step 6 — relief: besiege and intercept, or just take the city

- **Besiege and intercept when** the enemy has three or more field units within six to eight tiles of
  the target, or a road that lets relief arrive in one turn. Then hold the *corridor* between the
  enemy's field army and the city, and split the work: cavalry and ranged fight the relief, siege and
  melee keep grinding the city.
- **Do not besiege and intercept when** the field army is already dead or its main body is ten or more
  tiles away — the city falls in two to four turns and they cannot arrive in time. Live T103–T130:
  Russia's entire field army was a Warrior, an Archer, a Swordsman and a Builder; killing three of
  them in the first four turns left the sieges unopposed, and the only interruptions after that were
  a re-garrisoned Swordsman and one wandering Horseman.
- Contact on the march is files 2 and 3: assess, mass, annihilate — and prefer the counter unit
  (`counter-the-cavalry`).

## Step 7 — hold what you take

Loyalty is the quiet loss. Moscow was taken at T112 in the abandoned line and was a Free City by
T116; retaking it cost nine attacks. Measured in this war: a captured pop-3 city next to a pop-9
neighbour read **50 loyalty, −28.5/turn**; with a governor in residence and a garrison on the tile it
went to **−6.8/turn the next turn** and to 100 within ten turns. So before the war ends, decide:
which governor, which garrison unit, and what that garrison costs the next assault. A campaign is a
queue of sieges, and every city kept eats a unit.

## Prohibitions

- Never declare war because the army looks big. Declare when the five gates pass on a named city.
- Never start against a **garrisoned** city on archer fire alone: two Archers do not beat the heal.
- Never assume a tile will take a shot because it is two tiles away — walk the ring and order one
  shot before the assault depends on it.
- Never start against a walled city without a siege unit - and never with a Siege Tower or a Battering
  Ram, which this army neither builds nor fields (human instruction 2026-09-30: 不生产也不使用撞锤/攻城塔).
- Never let a city sit at 0 HP with no capture-capable unit **adjacent and unspent** — that is the
  whole bombardment thrown away.
- Never leave a wounded unit inside an enemy's reach.
- Never spend the gold on new units before checking what a policy card would do to upgrade prices.
- Never merge ranged or siege units into a Corps.
- Never fight a two-front war that the home garrison cannot cover.
- **Never walk a military unit onto a camp tile that a barbarian unit can reach first** — the walk-in
  unit is the raid, and losing it turns a raid into a barbarian unit parked next to a city.
- **Never send a civilian at a camp** (Scout, Builder, Trader). A civilian cannot take the tile and is
  captured on the way, which is the raid's cost with none of its payoff.
- **Never leave a camp alive because its units might be worth converting later.** Report the
  convertible unit, then clear the camp; the spawner does not wait for the human.
- Never clear a camp with one attacker when a second is within reach, and never with cavalry against
  barbarian Spearmen.

## What to report

One block per candidate target, then the decision. Every line is a gate from Step 2:

```
TARGET <city>@(x,y) <owner> | HP n/max, walls n/max | GARRISON <unit> (CS n) or none
RING   <n> tiles at distance 2 usable of <m> checked | LOS tested: yes/no
GATE 1 fire    gross n/turn (archer n + siege n) - heal 20 = net n  -> n turns
GATE 2 ring    shooters available n, firing tiles n  -> ok / n shots a turn
GATE 3 capture <unit> at (x,y), HP n, adjacent: yes/no, unspent: yes/no
GATE 4 walls   walls n/max -> answer: <siege unit / tower> or none needed
GATE 5 approach  path cost n points, lanes free: yes/no | declaration trigger: <what starts it>
ADD    <the two or three purchases that shorten it most, with their cost>
RELIEF field units within 8 tiles: n (their strength vs ours) -> intercept: yes/no
HOLD   loyalty pressure, governor available, garrison needed, units left for the next city
WIN    is it an original capital; how many remain; any rival close to another victory
```

For a **camp**, one block per camp, every line one of the camp gates:

```
CAMP    (x,y) <terrain / feature> — distance to the nearest of our cities n, to our nearest unit n
GUARD   n barbarian units within 2 tiles: <type CS n hp n at (x,y)>; camp tile occupied: yes/no
FORCE   ranged: <unit> at (x,y) | walk-in: <unit> at (x,y), HP n, unspent: yes/no
GROUND  the last step costs n MP from (x,y); river / mountain on the approach: yes/no
WORTH   gold n, era score n, 军事传统 inspired: yes/no, spawned so far: <units seen>
HOLD    city left without a garrison: <name or none>; the unit that walks home: <name>
CONVERT any barbarian adjacent to our melee worth converting: <type or none>
GO      clear it this turn: yes/no — <the one thing missing>
```

## Target selection

**Two kinds of target go through this section**, and the same three questions decide both: *what does
it cost to take*, *what does taking it buy*, and *what does leaving it cost*.

For a **city**:

- **Original capitals first.** Domination means owning every rival's original capital, and a capital
  can be captured but never destroyed. A border city that leads nowhere delays the win. (T99–T130:
  Moscow was the road, 圣彼得堡 was the objective, 阿斯特拉罕 was the formality — in that order, and
  the order was right.)
- **Springboard value**: does taking it shorten the distance to the next target?
- **Defence tier**: population, walls, **the garrison**, and the tech gap decide how many siege units
  it takes.
- **Loyalty pressure**: distance to the nearest *enemy* city and its population.
- **The approach**: chokepoints, river crossings, and whether siege units have line of sight at all.
- **Distance and water decide more than the defence does.** A coastal city within a few tiles of a base
  we hold is the cheap kind of target: 哈勒姆's walls (100) went to 0 under a Frigate alone in six turns
  (T261-T266, about 22 a turn) and the city fell **thirteen turns from Gate 0**. The other ending is
  measured too: an inland target thirty to forty tiles away still had its artillery 13-22 tiles out
  when a thirty-three-turn window expired, with `get_staging_plan` reporting nine units unplaced and
  "0 shooter(s) in position" (021, T237-T270 - the window, not the enemy, is what ended it). **Run
  `get_staging_plan` before the siege task's deadline is written and quote its timetable**: the turn
  the last shooter is in place is the earliest the assault can open, and the march is most of the plan.
  A target that needs more than about fifteen turns of march is a different task with a different
  budget, not the same task with a later date.
- **Who else is watching**: see gate 5.

For a **camp**, the ordering is by what the camp is doing to us, not by geography:

- **What it is next to.** A camp within three tiles of a city, a Builder's work, a road or a trade
  route outranks one in empty ground: it is the one that produces the unit that costs gold or a
  civilian. Measured T65 — the (60,30) camp's Spearman forced a 160-gold Warrior.
- **What it is spawning, and how fast.** Camps upgrade with the era (Warriors → Spearmen → Man-at-Arms),
  so a camp left for twenty turns is not the same raid as a camp taken now. That is the cost of
  *leaving* it, and it grows.
- **How cheap the walk-in is.** A camp with no guard on a tile we can reach in one move is nearly free;
  a camp behind a river in a mountain pocket with two Spearmen around it is a small siege, and the
  same gates apply.
- **What it is worth**: gold, era score, the `CIVIC_MILITARY_TRADITION` inspiration if it is still
  unbanked, and the spawns it stops.
- **What it costs elsewhere**: the units pulled off the development plan, and the garrison a city
  gives up while they are away — say which, and that it comes back.
- **The one thing the old rule protected**: the only source of units for 三十六计 Three-Six
  Stratagems is an adjacent barbarian, converted by the human from the game UI. Report any barbarian
  worth converting **before** the raid (camp gate C6), then clear the camp anyway.
