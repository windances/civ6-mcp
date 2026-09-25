# 4. Staging outside enemy range / 攻城前，城外攻击范围外的集结策略

Read when an assault is being planned and the stack is not yet formed.

## The rule

**Assemble outside the enemy's reach, then advance as one body.** A city's ranged strike reaches
**two tiles**, and so does a Catapult - the difference is that the city can absorb the answer and
the Catapult cannot. A column that arrives one unit at a time is defeated one unit at a time.

## Walk the ring before you declare / 宣战前先走一遍"射击圈"

A siege fires as many shots as the **firing ring** allows, not as many as the army has units: a
shooter only fires on a turn it can reach a tile two tiles from the city *with movement left over*,
and ranged attacks need movement (`NO_MOVES|Ranged attacks require movement`). So before the
declaration, and again on the turn the stack forms up:

1. **List every tile at distance ≤ 2 from the city** and mark which are passable. Mountains are not:
   measured T113, two of 圣彼得堡's ring tiles ((57,41), (54,42)) answered
   `BLOCKED (impassable mountain)`, and at 阿斯特拉罕 the whole east side was mountains, so for most
   of that siege only three shooters could fire at once while six stood idle. Moscow's ring had six
   usable tiles and the siege went twice as fast.
2. **Test line of sight per tile, per unit.** LOS is not distance: (53,35)→(52,37) was refused
   `NO_LOS` while (52,36)→(53,37) at the same range went through, and a Catapult refused (54,40)
   from (55,38) yet fired from (52,38) (T107). A tile is only a firing position once a shot from it
   has been *ordered* and not refused.
3. **Count the points of the last move.** A one-tile move can cost **two** movement points (river,
   hill, marsh). Five siege turns were lost to this in the T103–T130 war, twice as
   `NO_MOVES` on a Catapult that had moved one tile that turn. A unit that wants to fire this turn
   must start the turn able to *step into* the ring with one point and still have one to fire with.
4. **Keep the lanes clear.** Our own stack is the most common obstacle to our own ring: at
   阿斯特拉罕 the shooters occupied the only two adjacent ring tiles and the melee could not reach
   the city at all. Put the **melee on the ring and the shooters one tile behind it**, never the
   reverse, and leave at least one approach tile free for the capture move.

## Choosing the rally point

A staging tile is good when it is:

- **three or more tiles** from the target city and from every visible enemy unit
  (`siege_city_distance_min >= 3` while staging; `siege_exposed == 0`);
- outside the reach of **any second enemy city** nearby - check for a second city before
  committing to the approach axis;
- **defensible**: hills, forest or across a river, so the stack can absorb a counterattack while
  it forms;
- **on the approach axis**, with no river crossing or mountain pass between it and the target,
  because the final advance has to happen in one turn;
- **on roads** where roads exist, so reinforcements and the ram/tower arrive with movement left;
- close enough that wounded units can still reach it after healing.

## When to stage

1. **The assault list is complete** first: 2 siege, 2 melee, 1 ram/tower, 4 ranged, 1 cavalry
   (`siege-train`, `ranged-mass`, `melee-screen`, `ram-tower-before-civil-engineering`). Staging
   with a missing role is how a war starts that cannot be finished.
2. **Reinforcements already in motion.** The declaration waits for the formation, not the other
   way round: the directive's rule is that a war you cannot finish is a war you must not start.
3. **Full health.** A stack that arrives wounded spends the first two turns of the war healing;
   heal at the rally point instead, where nothing can reach it.
4. **Nothing left behind that matters.** An enemy left between the rally point and the target
   attacks the siege train from behind - clear the path, or leave a covering force and say so.

## The march itself

- Move in formation, not in a queue: the screen leads, the ranged and siege follow within one
  turn of it, and nothing arrives alone.
- Keep every unit inside the reach of the stack. A unit that outruns the others is the one that
  gets attacked (`answer-the-attack`).
- **Route around enemy units, because their zone of control eats the whole turn.** The manual
  (`ZONES OF CONTROL`, p.73): "When a unit moves into a tile within an enemy's ZOC it expends **all
  of its MPs**. Cavalry units are the exception." So stepping into the hex next to an enemy is not
  a cheap detour - it ends that unit's movement for the turn, even if it never intended to attack.
  Plan the approach around enemy stacks, not through them, and expect the unit that brushes past an
  enemy to arrive a turn late.
- **Our cavalry is the exception too, and that is a tool.** Cavalry ignores enemy ZOC: it can slip
  past a front line to reach the enemy's siege and ranged units, cut a supply hex, or pillage the
  tiles the target city depends on. That is the same property that makes enemy cavalry dangerous to
  us (`counter-the-cavalry`) - use it instead of only defending against it.
- **Contact outranks the timetable.** The moment a unit discovers an enemy or is attacked, the
  answer is file 2 and file 3 - assess, mass, annihilate - and only then resume the advance. A
  city is patient; a Catapult that walked past an enemy is not.
- Re-check on arrival: if the enemy has reinforced the city or moved a field army into the
  approach, the rally point is a decision point again, not a formality.

## Prohibitions

- Do not begin the approach from inside the city's strike range; stage first, then move.
- Do not stage where the stack is split by a river or a mountain on the final approach.
- Do not stage adjacent to a barbarian camp or in reach of a second enemy city.
- Do not stage with the siege train in front or unscreened, even at a safe distance - the
  formation is file 5.
- Do not keep the army parked at the rally point once the formation is complete: an assembled
  army that does not advance is paying maintenance for nothing.

## What to report

The rally tile (coordinates), which units are already there and which are still moving with turn
estimates, what is missing from the assault list, and how far the nearest enemy city and enemy
units are from the rally point. If the snapshot does not show terrain or fog around the proposed
tile, say so and propose a check rather than assuming it is safe.
