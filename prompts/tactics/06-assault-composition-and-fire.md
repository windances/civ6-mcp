# 6. Assault composition and fire discipline / 攻城开始后，部队搭配和攻击策略

Read once the stack is in contact with the target city and the assault is running.

## The composition, and each unit's job

| Role | Count | Job in the assault |
|---|---|---|
| Siege | 2 | Break the walls. Dedicated city damage (Catapult/Trebuchet **45**, Bombard 55) that does not take the ranged-versus-walls penalty. |
| Melee | 2 | The only units that can **take** the city: a melee unit walking in finishes it. One holds the front tile, one is kept for the capture move. |
| Ram / tower | 1 | Support, adjacent to the city, helping **melee only**: the ram makes melee do full damage to walls, the tower lets melee ignore them. Both die at `CIVIC_CIVIL_ENGINEERING`. |
| Ranged | 4 | Kill the garrison and anything that comes to relieve the city. Range 2, no retaliation. |
| Cavalry | 1 | Hunt survivors and reach the enemy's ranged and siege units. Never the unit holding the front tile. |

## Order of work, every turn

1. **Siege knocks the walls to 0.**
2. **Melee (with the ram or tower adjacent) takes the city.**
3. **Ranged shoots the garrison** - not the walls you already have siege for.
4. **Re-check before the capture move**: a city only falls to a melee unit; a turn spent firing
   at a 0-wall city from range is a turn not spent finishing it.

## Fire discipline

- **Concentrate.** Every attacker on the same target, in the same turn. A city heals about
  twenty points a turn, so damage spread over several turns and several targets is damage that
  never happened.
- **Judge progress by the city's own numbers**: `city hp: N/200` and `walls: N/100` (or `none`)
  on the attack result, and the `SIEGE PROGRESS` block in the turn result, which reports the
  delta and says `SIEGE STALLED` after three recorded turns without a net drop. Do not judge by
  the damage estimate on a city tile - that estimate describes the unit standing there.
- **Do not ignore the stall warning.** A city heals about twenty points a turn, so an assault
  that does not out-damage the healing is an assault that never happened. Three flat turns means
  fix it (siege in position and screened, more attackers on the same target, a wall-breaker added)
  or break it off - and say which.
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
- Keep the stack together and move it on the next city; do not let it disperse into garrisons.
- Report the captured city's loyalty and whether a governor is needed.

## What to report

The target city; for each role, which units are assigned and where they stand; the wall/garrison
numbers if the snapshot has them; the attack order for this turn (which unit hits what); the
capture unit; and anything that makes the assault fail (unscreened siege, missing melee, no
siege, ram lost, a relieving stack). Where a number is missing from the snapshot, name the
missing number rather than filling it in.
