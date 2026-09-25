# 7. Pre-war analysis / 战前分析：能不能打、打谁、几回合、损失多大、打完守不守得住

Read before a war is declared, and again whenever a target changes. Files 1-6 are about fighting a
war; this one decides whether to start it.

The directive's gate is "declare only when the army in place can take the cities". That is a
judgement, and this file is how to make it from numbers rather than from hope. It is **one
procedure in seven steps**, and every step names the query that answers it:

| Step | Question | Answered by |
|---|---|---|
| 0 | Is there a target to analyse at all? | `get_deal_options`, `get_strategic_map` |
| 1 | What is the target, in four numbers? | the city probe (hp / walls / **garrison** / ring) |
| 2 | Do the **five gates** pass? | the arithmetic below, per gate |
| 3 | How long, and what will it cost? | the formula below, plus the loss asymmetry |
| 4 | What can be bought first? | `get_policies`, `purchase_item`, `upgrade_unit` |
| 5 | Where do we assemble, and when do we declare? | `get_pathing_estimate`, the ring walk |
| 6 | Does anyone come to its rescue? | `get_units` on the enemy, `get_diplomacy` |
| 7 | Can we hold what we take? | loyalty pressure, governor, garrison |

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

## Step 1 — read the target: four numbers, in this order

| # | Number | Where | Why it is this order |
|---|---|---|---|
| 1 | **Garrison** — the unit on the city tile, and what it is | the city probe's `garrison:` field | It decides the fire arithmetic more than walls do (Step 2, gate 1) |
| 2 | **Walls** (`walls n/max` or `none`) | the same line | Decides whether a siege unit is mandatory (gate 4) |
| 3 | **HP pool** | the same line | Always 200 for a city; it is the denominator, not the question |
| 4 | **The ring** — every tile at distance ≤ 2, and which are passable | `Map.GetPlotDistance` per tile | It is the ceiling on how many shots a turn you can fire (gate 2) |

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

Without a siege unit or a Siege Tower (melee ignores walls), ranged fire pays the wall penalty and
the assault stalls. Never start against a walled city without one.

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
| Battering Ram -> Siege Tower | 80 (40) | melee ignores walls — the answer to gate 4 |
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
- Never start against a walled city without a siege unit or a Siege Tower.
- Never let a city sit at 0 HP with no capture-capable unit **adjacent and unspent** — that is the
  whole bombardment thrown away.
- Never leave a wounded unit inside an enemy's reach.
- Never spend the gold on new units before checking what a policy card would do to upgrade prices.
- Never merge ranged or siege units into a Corps.
- Never fight a two-front war that the home garrison cannot cover.

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

## Target selection

- **Original capitals first.** Domination means owning every rival's original capital, and a capital
  can be captured but never destroyed. A border city that leads nowhere delays the win. (T99–T130:
  Moscow was the road, 圣彼得堡 was the objective, 阿斯特拉罕 was the formality — in that order, and
  the order was right.)
- **Springboard value**: does taking it shorten the distance to the next target?
- **Defence tier**: population, walls, **the garrison**, and the tech gap decide how many siege units
  it takes.
- **Loyalty pressure**: distance to the nearest *enemy* city and its population.
- **The approach**: chokepoints, river crossings, and whether siege units have line of sight at all.
- **Who else is watching**: see gate 5.
