# 7. Pre-war analysis / 战前分析：能不能打、打谁、几回合、损失多大、打完守不守得住

Read before a war is declared, and again whenever a target changes. Files 1-6 are about fighting a
war; this one decides whether to start it.

The directive's gate is "declare only when the army in place can take the cities". That is a
judgement, and this file is how to make it from numbers rather than from hope. Every item below is
something the adapter can already query.

## The nine questions, in order

1. **Who** - which civilization, and which of its cities first (see Target selection).
2. **Can we** - the three gates: net fire > 0, a capture-capable unit able to stand on the tile the
   turn the pool empties, and a siege answer if the city has walls.
3. **How long** - turns to break, and turns to assemble, and the larger of the two is the answer.
4. **What will it cost** - losses, which are near zero for ranged and mostly come from the field
   army, not the city.
5. **What can we add first** - pre-war power is bought with policy and gold, not with production
   (see Pre-war power).
6. **Assembly and contact** - where the rally point is, and what to do when something walks into
   the march.
7. **Relief** - whether to besiege and intercept, or just take the city.
8. **Afterwards** - loyalty, governor, garrison, and what is left for the next city.
9. **Is it the right war** - original capitals, rival victory progress, and the stop line.

## Target selection

- **Original capitals first.** Domination means owning every rival's original capital, and a capital
  can be captured but never destroyed. A border city that leads nowhere delays the win.
- **Springboard value**: does taking it shorten the distance to the next target?
- **Defence tier**: population, hills, walls, and the tech gap decide how many siege units it takes.
- **Loyalty pressure**: distance to the nearest *enemy* city and its population. Live: Moscow was
  taken at T112 and had become a Free City by T116; retaking it cost nine attacks.
- **The approach**: chokepoints, river crossings, and whether siege units have line of sight at all.
  Live (T120): (56,43) to (54,40) is 12 tiles of pathing over two turns, and a Trebuchet at (55,42)
  answered `NO_LOS` to a city two tiles away. Straight-line distance lies; `get_pathing_estimate`
  does not.
- **Who else is watching**: defensive pacts turn one war into three (`get_diplomacy`), and a second
  front has to be affordable with the units left at home (`one-garrison-per-city`).

## The three gates

1. **Net fire > 0.** `sum(ranged and siege damage that can reach the city) - healing`, where healing
   is twenty points a turn while the city has a supply line and **zero when all six adjacent hexes
   are cut**. Net fire at or below zero is `SIEGE STALLED`: cut the supply line or do not start.
2. **A capture-capable unit can stand on the city tile the turn the pool empties.** Melee,
   anti-cavalry and cavalry can; ranged, siege and support cannot. This - not the damage - is what
   decides the war: Moscow was broken to 0 at T120 and stood for four turns because nobody was
   adjacent, and the bombardment had to be fought again from nothing.
3. **Walls have an answer.** Without a siege unit or a Siege Tower (melee ignores walls), ranged fire
   pays the wall penalty and the assault stalls. Never start against a walled city without one.

## Time, and losses

```
turns to break  ~= ceil( (city HP + wall HP) / (damage per turn - 20 if the supply line is open) )
turns to assemble = max( slowest damage unit in position, capture unit adjacent )
```

- Measured anchor, T120-T122: 200 HP, no walls, supply 4/6 - two Trebuchets and three to four
  Archers did 60-110 a turn, 40-90 net, and the city fell in **three turns**.
- **Losses are asymmetric.** Ranged and siege take **no retaliation** (three turns of fire, zero HP
  lost). A garrison inside takes no damage while the city is attacked and dies only with the city -
  so it is never a reason to spend an attack. A melee unit that *attacks* a city fights it at full
  strength no matter its HP: a 9 HP Heavy Chariot attacking a 110 HP city was destroyed outright.
  **Walking into a city at 0 HP is not a fight.**
- The real losses come from the field: relief units arriving while the siege train is parked. Kill
  them first (`mass-on-contact`), screen the train (`screen-the-siege`), and keep the siege out of
  range 2 of a walled city so it cannot be shot each turn.

## Pre-war power: policy and gold, not production

Measured at T196 (7 cities, 992 gold, +15.8/turn, 14 fighting units): the whole army could be
upgraded for 2,290 gold, or **1,145 with Professional Army** (Mercenaries' 50% upgrade discount) -
so one policy card is worth more than a thousand gold. Priority order:

| Buy | Cost | Gain |
|---|---|---|
| Professional Army policy card | 0 | halves every upgrade below |
| 4x Archer -> Crossbowman | 250 each (125) | +15 ranged strength each, and ranged is the only zero-retaliation damage |
| Battering Ram -> Siege Tower | 80 (40) | melee ignores walls - the answer to gate 3 |
| 3x Heavy Chariot -> Knight | 320 each (160) | +20 combat strength each, which is what `match-their-melee` is complaining about |
| Military-leaning government | free on change | more military policy slots |

Free multipliers that are easy to forget: a **Great General** with the stack (+5 CS, +1 movement
within two tiles), religious beliefs such as Crusade where the target follows your religion, a
Militaristic city-state suzerainty, and **Corps/Armies for melee and cavalry only** - merging two
ranged or siege units trades two attacks for one and is a net loss of fire (see file 6).

Producing units is the slowest lever: one Trebuchet is roughly eight to twelve turns in a
single city, so production buys the *next* war while gold and policy buy this one.

## Assembly, contact, and relief

- Rally **one tile outside the target's range** (a walled city shoots at range 2), siege at range 2-3
  with line of sight confirmed, melee at range 1 ready to walk in.
- Do not wait for a straggler: start when the fire is positive and a capture unit is in reach;
  `siege-train`, `ranged-mass` and `melee-screen` say what "enough" means each turn.
- Contact on the march is files 2 and 3: assess, mass, annihilate - and prefer the counter unit
  (`counter-the-cavalry`).
- **Besiege and intercept when** the enemy has three or more field units within six to eight tiles of
  the target, or a road that lets relief arrive in one turn. Then hold the *corridor* between the
  enemy's field army and the city, and split the work: cavalry and ranged fight the relief, siege and
  melee keep grinding the city. **Do not besiege and intercept when** the field army is already dead
  or its main body is ten or more tiles away - the city falls in two to four turns and they cannot
  arrive in time.

## After the capture, before the next one

Loyalty is the quiet loss (Moscow again): check the new city's pressure and the outcome the game
reports, keep a governor or a garrison in it (`hold-what-you-take`), and count what the garrison
costs the next assault. A campaign is a queue of sieges, and every city kept eats a unit.

## Prohibitions

- Never declare war because the army looks big. Declare when the three gates pass on a named city.
- Never start against a walled city without a siege unit or a Siege Tower.
- Never let a city sit at 0 HP with no capture-capable unit in reach - that is the whole bombardment
  thrown away.
- Never spend the gold on new units before checking what a policy card would do to upgrade prices.
- Never merge ranged or siege units into a Corps.
- Never fight a two-front war that the home garrison cannot cover.

## What to report

One line per candidate target, then the decision:

```
TARGET <city>@(x,y) <owner> | HP n/max, walls n/max, garrison n | nearest friendly city d tiles
GATES  net fire n/turn (heal 20 unless supply 6/6 cut) -> n turns | capture unit in reach: yes/no
       siege answer: yes/none
ADD    <the two or three purchases that shorten it most, with their cost>
RELIEF field units within 8 tiles: n (their strength vs ours) -> intercept: yes/no
HOLD   loyalty pressure, governor available, garrison needed, units left for the next city
WIN    is it an original capital; how many remain; any rival close to another victory
```
