# 4. Staging outside enemy range / 攻城前，城外攻击范围外的集结策略

Read when an assault is being planned and the stack is not yet formed.

## The rule

**Assemble outside the enemy's reach, then advance as one body.** A city's ranged strike reaches
**two tiles**, and so does a Catapult — the difference is that the city can absorb the answer and the
Catapult cannot. A column that arrives one unit at a time is defeated one unit at a time.

It is **one procedure in six steps**, and the binding constraint is almost never the siege — it is
getting the siege there:

| Step | Question | Answered by |
|---|---|---|
| 1 | Where is the rally point? | the tile criteria below + `get_map_area` |
| 2 | **How long does the assembly take?** | `get_pathing_estimate`, per unit, slowest wins |
| 3 | What must be true before the column moves? | the completeness list below |
| 4 | How does the column move? | the march discipline below |
| 5 | Does the ring exist when we arrive? | the ring walk below |
| 6 | When do we go in? | the go/no-go below, and the declaration trigger |

## Step 1 — the rally point

A staging tile is good when it is:

- **three or more tiles** from the target city and from every visible enemy unit
  (`siege_city_distance_min >= 3` while staging; `siege_exposed == 0`);
- outside the reach of **any second enemy city** nearby — check for a second city before
  committing to the approach axis;
- **one turn's run from the ring**: no river crossing or mountain pass between it and the target,
  because the final advance has to happen in one turn, and a one-tile move can cost a unit its whole
  allowance (river, hill, marsh — five turns lost to this in the T103–T130 war);
- **not a lane a foreign unit is standing in.** At peace you cannot enter a tile held by another
  civ's unit, and it does not have to be a soldier: a Russian Missionary at (57,32) and an Egyptian
  Scout at (58,32) closed the x=57 lane for two full turns (T101) while a Catapult and an Archer sat
  and waited. Check `get_map_area` for whose units are parked in the corridor;
- **defensible**: hills, forest or across a river, so the stack can absorb a counterattack while
  it forms;
- **on roads** where roads exist, so reinforcements and the ram/tower arrive with movement left;
- close enough that wounded units can still reach it after healing.

## Step 2 — time the assembly; it is usually the longer pole

```
turns to assemble = the slowest unit's path cost to its RING tile, in movement points / its MP per turn
turns to break    = see file 7
the bigger of the two is the war's start date
```

Measure it **per unit and to the ring tile, not to the rally point**: a unit that reaches the rally
point and stops is not assembled, it is one turn short. `get_pathing_estimate` is the query; straight
line distance is not (hand-computed hex distances were wrong four times in one war).

Measured anchor, T99–T105: 长沙 (52,30) to the staging row (54,37) is **11 movement points** through
a corridor whose first three tiles are 2-cost jungle — **six turns at 2 MP**, for every Archer and
Catapult in the army. The plan that said "the Catapults are 5–7 turns from the border" was right for
the Catapults and wrong for the timetable, because everything shared the same funnel.

Two consequences that decide whether the assembly finishes on schedule:

- **A narrow corridor serialises the column.** When one lane exists, units queue: the second unit
  cannot enter the tile the first is standing on, so it waits a turn. Count the lanes, and expect the
  column to need (units ÷ lanes) turns to pass a 2-cost stretch.
- **Arrive with fuel.** A unit that spends its last point reaching the rally point cannot fire, step
  into the ring, or capture on the following turn — `NO_MOVES|Ranged attacks require movement` is the
  message, and it cost three Catapult turns in one war. The assembly is complete when units are at
  the rally point **with movement left**, and the advance happens on the next turn.

## Step 3 — what must be true before the column moves

1. **The assault list is complete** first: 2 siege, 2 melee, 1 ram/tower, 4 ranged, 1 cavalry
   (`siege-train`, `ranged-mass`, `melee-screen`, `ram-tower-before-civil-engineering`). Staging
   with a missing role is how a war starts that cannot be finished.
2. **The composition is justified by THIS target.** The ram and tower exist for walls: every Russian
   city in the T103–T130 war read `walls 0/0` from first contact to the last, so the Battering Ram —
   65 production, dragged across the map — did nothing for seventeen turns, and the Catapults became a
   damage tool rather than a wall-breaker. Read the walls (file 7, gate 4) before deciding what to
   bring; leave the ram at home when the answer is "no walls".
3. **Reinforcements already in motion.** The declaration waits for the formation, not the other way
   round: the directive's rule is that a war you cannot finish is a war you must not start.
4. **Full health.** A stack that arrives wounded spends the first two turns of the war healing; heal
   at the rally point instead, where nothing can reach it. The rates matter here: 20 HP/turn inside a
   city of ours, 15 in friendly territory, 10 neutral, 5 in enemy territory.
5. **Nothing left behind that matters.** An enemy left between the rally point and the target attacks
   the siege train from behind — clear the path, or leave a covering force and say so.
6. **A capture-capable unit with health in the plan.** Walking into a 0 HP city is a combat action
   (file 7, gate 3): whoever is nominated has to arrive unspent and above ~40 HP, and that unit
   should not be the one doing the attacking.

## Step 4 — the march

- Move in formation, not in a queue: the screen leads, the ranged and siege follow within one
  turn of it, and nothing arrives alone.
- Keep every unit inside the reach of the stack. A unit that outruns the others is the one that
  gets attacked (`answer-the-attack`).
- **Route around enemy units, because their zone of control eats the whole turn.** The manual
  (`ZONES OF CONTROL`, p.73): "When a unit moves into a tile within an enemy's ZOC it expends **all
  of its MPs**. Cavalry units are the exception." So stepping into the hex next to an enemy is not
  a cheap detour — it ends that unit's movement for the turn, even if it never intended to attack.
- **Our cavalry is the exception too, and that is a tool.** Cavalry ignores enemy ZOC: it can slip
  past a front line to reach the enemy's siege and ranged units, cut a supply hex, or pillage the
  tiles the target city depends on. That is the same property that makes enemy cavalry dangerous to
  us (`counter-the-cavalry`) — use it instead of only defending against it.
- **Contact outranks the timetable.** The moment a unit discovers an enemy or is attacked, the
  answer is file 2 and file 3 — assess, mass, annihilate — and only then resume the advance. A
  city is patient; a Catapult that walked past an enemy is not.
- Re-check on arrival: if the enemy has reinforced the city or moved a field army into the
  approach, the rally point is a decision point again, not a formality.

## Step 5 — the ring walk, on arrival and before the advance

A siege fires as many shots as the **firing ring** allows, not as many as the army has units. Walk it
before the declaration and again the turn the stack forms:

1. **List every tile at distance ≤ 2 from the city** and mark which are passable. Mountains are not:
   measured T113, two of 圣彼得堡's ring tiles ((57,41), (54,42)) answered
   `BLOCKED (impassable mountain)`, and at 阿斯特拉罕 the whole east side was mountains, so for most
   of that siege only three shooters could fire at once while six stood idle. Moscow's ring had six
   usable tiles and the siege went twice as fast.
2. **Test line of sight per tile, per unit.** LOS is not distance: (53,35)→(52,37) was refused
   `NO_LOS` while (52,36)→(53,37) at the same range went through, and a Catapult refused (54,40)
   from (55,38) yet fired from (52,38) (T107). A tile is only a firing position once a shot from it
   has been *ordered* and not refused.
3. **Assign tiles by role, and keep the two sets apart: melee goes ADJACENT (distance 1) to the city,
   shooters go on the ring (distance 2), and at least one adjacent tile stays free for the capture
   move.** Our own stack is the most common obstacle to our own ring: at 阿斯特拉罕 the shooters
   occupied both adjacent tiles — the only ones the melee could have used — and the assault had no
   unit able to reach the city until they moved.
4. **Write the order of arrival down** — which unit takes which tile on which turn — because the
   move-cost arithmetic above decides whether the ring fills in one turn or three.

## Step 6 — the go/no-go

Advance when all of these are true in the same turn:

- the shooters are on ring tiles **with movement left**, or one point from them;
- a capture-capable unit is adjacent (or one point from adjacent) and unspent;
- the walls answer is in position, if the target has walls;
- the field army in contact is dealt with (files 2 and 3).

**The declaration trigger, measured T103:** massing on a border is what starts the war. Peter's
border complaint arrived the turn the column closed on his frontier, the refusal was taken as the
answer, and Russia declared with our army **two turns short** of its staging row. So treat "the enemy
declares when they see the stack" as the expected case: build the rally point where the army can
already fight from where it stands, not where it would like to be in three turns. A rally point that
is only safe *because* the war has not started is not a rally point.

## Prohibitions

- Do not begin the approach from inside the city's strike range; stage first, then move.
- Do not stage where the stack is split by a river or a mountain on the final approach.
- Do not stage adjacent to a barbarian camp or in reach of a second enemy city.
- Do not stage with the siege train in front or unscreened, even at a safe distance — the
  formation is file 5.
- Do not drag a ram or tower toward a city whose walls have been read as `none`.
- Do not order a unit to fire on the turn it must spend two points to enter the ring: it arrives with
  nothing left, and the attack is refused.
- Do not keep the army parked at the rally point once the formation is complete: an assembled
  army that does not advance is paying maintenance for nothing.

## What to report

```
RALLY  (x,y) — distance to the city n, to the nearest enemy unit n, second city within reach: yes/no
FUEL   slowest unit n tiles / n movement points / n turns out (path, not straight line)
LANES  n lanes through the corridor; tiles held by foreign units: <list or none>
READY  assault list: siege n/2, melee n/2, ram n/1, ranged n/4, cavalry n/1
       composition justified: walls <n/max or none> -> ram needed: yes/no
HEALTH units below full: <list with HP and where they heal>
RING   n usable tiles at distance 2 of m checked; assigned: <unit -> tile>; free tiles: n
GO     advance this turn: yes/no — <the one thing missing, if no>
```

If the snapshot does not show terrain or fog around the proposed tile, say so and propose a check
rather than assuming it is safe.
