# 6. Assault composition and fire discipline / 攻城开始后，部队搭配和攻击策略

Read once the stack is in contact with the target city and the assault is running.

## The composition, and each unit's job

| Role | Count | Job in the assault |
|---|---|---|
| Siege | 2 | Break the walls. Dedicated city damage (Catapult/Trebuchet **45**, Bombard 55) that does not take the ranged-versus-walls penalty. |
| Melee | 2 | The only units that can **take** the city: a melee unit walking in finishes it. One holds the front tile, one is kept for the capture move. |
| Ram / tower | 1 | Support, adjacent to the city, helping **melee only**: the ram makes melee do full damage to walls, the tower lets melee ignore them. Both die at `CIVIC_CIVIL_ENGINEERING`. |
| Ranged | 4 | Take the **city's HP** down (and kill anything that comes out to relieve it). Range 2, no retaliation. Never aim at a garrison that is inside - it takes no damage there. |
| Cavalry | 1 | Hunt survivors and reach the enemy's ranged and siege units. Never the unit holding the front tile. |

## Order of work, every turn

1. **Siege knocks the walls to 0.**
2. **Melee (with the ram or tower adjacent) takes the city.**
3. **Ranged shoots the city's HP** - not the garrison, and not the walls you already have siege
   for. The manual (`GARRISON UNITS IN CITIES`) is explicit: a garrisoned unit's combat strength
   is partly *added to the city's*, and **the garrison takes no damage while the city is
   attacked** - it dies only when the city falls. The city is what has an HP pool to remove;
   walls come first, then that pool. A garrison that steps outside is a target like any unit, and
   a garrison that attacks from inside costs the city its garrison bonus - that is the turn to
   punish it. (Live: the old order of work said "shoot the garrison", and eight turns of fire
   traded blows with a unit that was never losing HP.)
4. **When the city HP pool reaches 0, the capture move happens that turn.** The turn result
   carries a `TAKE THE CITY` block naming the tile and the melee unit in reach; the rule
   `take-the-city` fails while a city at 0 HP is still standing with a melee unit next to it.
   Only a melee-class unit can do it and only from the city's own tile - a Battering Ram or
   Siege Tower is refused (`CAPTURE_MOVE` BLOCKED), and cavalry, ranged and siege units cannot
   capture either. A city with **no garrison unit** in it is still attackable (the adapter
   resolves the city itself through `Cities.GetCityInPlot`): keep firing at the tile, and move
   the melee unit in - an empty city is not a city that cannot be hit, it is a city that can be
   entered. Two live failures to avoid: a city left at 0 HP heals about twenty points a turn
   and is back to 120/200 six turns later, and a broken city with nobody to walk into it is
   four turns of fire thrown away.
5. **Re-check before the capture move**: a city only falls to a melee unit; a turn spent firing
   at a 0-wall city from range is a turn not spent finishing it.

## Stop the healing at the source: the supply line

A city's healing is **conditional**, and the condition is one the army can remove. The manual
(`HEALING DAMAGE TO CITIES`): "A city heals a small amount every turn, even during combat, **as
long as it has a supply line**. A supply line is any hex adjacent to the city that is not within
an enemy unit's Zone of Control."

So the heal stops when **every** adjacent hex is either occupied by one of our military units or
inside the zone of control of one (i.e. has one of our units next to it). Six hexes, not sixteen
points of damage - and the `SIEGE PROGRESS` block now reports the count on the city being ground
down (`supply line 4/6 cut - the city is still healing`).

- **Prefer cutting to out-damaging.** An assault that must beat a twenty-point heal needs a much
  larger stack than one that does not; two spare units walked around the city are usually cheaper
  than two more Catapults.
- **The screen does double duty.** Units already standing in front of the siege to absorb the
  city's strike are, by standing there, also cutting supply hexes - pick the tiles with that in
  mind.
- **Walls do not heal the same way.** A city can only repair walls through the production queue,
  and only after **three turns of taking no damage** - so wall damage that keeps being renewed
  keeps the repair from ever landing.
- **Say the number.** When the assault is stalling, report how many adjacent hexes are cut and
  whether that is the plan; if the army is too small to surround the city, that is the reason to
  break off, not to keep firing.

## Fire discipline

- **Concentrate.** Every attacker on the same target, in the same turn. A supplied city heals
  about twenty points a turn, so damage spread over several turns and several targets is damage
  that never happened.
- **Judge progress by the city's own numbers**: `city hp: N/200` and `walls: N/100` (or `none`)
  on the attack result, and the `SIEGE PROGRESS` block in the turn result, which reports the
  delta and says `SIEGE STALLED` after three recorded turns without a net drop. Do not judge by
  the damage estimate on a city tile - that estimate describes the unit standing there.
- **Do not ignore the stall warning.** A supplied city heals about twenty points a turn, so an
  assault that does not out-damage the healing is an assault that never happened. Three flat
  turns means cut the supply line first (see above), then fix the fire (siege in position and
  screened, more attackers on the same target, a wall-breaker added) or break it off - and say
  which.
- **Kill what is killable.** An enemy at 20 HP or less is the one attack that is never a bad
  trade; a garrison that survives heals and comes back.
- **Do not feed the train in piecemeal.** A wounded attacker heals or withdraws; it does not take
  one more shot at the wall.
- **A second enemy stack arriving is a decision, not a distraction**: either it is killed first
  (files 2 and 3) or the assault breaks off. The siege train is never left between the two.

## When the assault is not working

If the walls have not moved in about three turns - the turn result says `SIEGE STALLED` - or the
garrison is being replaced faster than it is killed, stop and say why: no siege in position, siege
unscreened and dying, too few attackers to out-damage the healing, or the ram/tower lost. A stalled
assault is pure cost - war weariness suppresses production while the enemy keeps every city. Fix
the front (bring siege, heal, upgrade, reinforce) or change the target; never negotiate it away
(the directive forbids peace).

## After the capture

- Garrison the captured city with the **cheapest spare unit** - one unit, per
  `one-garrison-per-city`; everything else belongs at the next front.
- **Then hold it.** A captured city can leave the empire with no enemy involved: live, Moscow was
  taken at T112 (pop 3, no governor, no garrison) and was a Free City by T116, which cost nine
  attacks and four turns to undo. The turn result carries a `LOYALTY WARNING` naming each city's
  pool, its per-turn pressure, the game's own turns-to-conversion estimate and the game's own
  advice string; `hold-what-you-take` fails while a city below 50 loyalty has neither a governor
  nor a unit on its tile. `assign_governor` is the cheapest fix (moving a governor is free), and
  a unit on the tile is the other one.
- Keep the stack together and move it on the next city; do not let it disperse into garrisons.
- Report the captured city's loyalty and whether a governor is needed.

## What to report

The target city; for each role, which units are assigned and where they stand; the wall/garrison
numbers if the snapshot has them; the attack order for this turn (which unit hits what); the
capture unit; and anything that makes the assault fail (unscreened siege, missing melee, no
siege, ram lost, a relieving stack). Where a number is missing from the snapshot, name the
missing number rather than filling it in.
