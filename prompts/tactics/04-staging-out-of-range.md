# 4. Staging outside enemy range / 攻城前，城外攻击范围外的集结策略

Read when an assault is being planned and the stack is not yet formed.

## The rule

**Assemble outside the enemy's reach, then advance as one body.** A city's ranged strike reaches
**two tiles**, and so does a Catapult - the difference is that the city can absorb the answer and
the Catapult cannot. A column that arrives one unit at a time is defeated one unit at a time.

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
