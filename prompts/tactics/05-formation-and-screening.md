# 5. Formation and screening / 攻城前，部队站位策略

Read when the stack is formed and about to advance on the target.

## The formation

```
        [ target city ]            city ranged strike: 2 tiles
          melee / anti-cav / cavalry     <-- front line, adjacent to the city
              ranged (range 2)           <-- behind the melee, 2 tiles from the city
                 siege (range 2)         <-- behind the melee, 2 tiles: the tile to protect
```

- **The units that can take a hit stand in front**: melee, anti-cavalry, cavalry. They hold the
  tile the enemy can reach first.
- **Ranged and siege stand behind them** at range 2. A Catapult is the most expensive unit in
  the stack and the least able to survive one turn of attention; its tile is the one the
  formation exists to protect.
- **Never adjacent.** A siege unit adjacent to the city takes the city's strike and the
  garrison's counterattack at the same time, and it does that with the lowest HP pool in the
  army. Range 2 is where a Catapult belongs, and it is the range it was built for.
- **China's Crouching Tiger (range 1)** is the exception that proves the rule: it has to stand
  adjacent to what it shoots, so a melee unit must hold the tile in front of it, always.

## The test, not the intention

"Something is nearby" is not a screen. The screen must be **closer to the enemy than the siege
unit is**:

- `screen-the-siege` fails while a siege unit is within two tiles of an enemy with nothing
  **strictly closer** to that enemy than itself (`siege_exposed > 0`).
- A front-line unit standing exactly as close as the Catapult is not cover: it is a second
  target.
- The turn result's `SIEGE POSTURE` block reports, per siege unit, the distance to the nearest
  enemy, the distance from that enemy to the unit screening it, and the distance to the nearest
  enemy city. Use those three numbers in the proposal.

## Order of advance

1. **Screen first**: the melee moves to the tile adjacent to the city (or to the enemy stack).
2. **Then the ranged and siege** move to their range-2 tiles behind it.
3. **The ram or tower moves with the melee** it is supporting - support units only work from the
   tile adjacent to the city and only for melee.
4. **The cavalry stays mobile** behind the line: its job is survivors and enemy ranged/siege
   units, not holding ground.
5. If the screen cannot get in front of the siege this turn, the siege stays back. Arriving one
   turn later is cheaper than arriving dead.

## What went wrong when this was ignored (T105-T116, live)

- Both Catapults were parked on tiles **adjacent** to Moscow (`dist:1`), where they took 28-52
  estimated retaliation per shot and lost HP every turn; one sat at 86/100 doing nothing.
- The formation had no melee in front of the siege, so the city and its garrison chose their
  target freely.
- The stack traded with the garrison for eight turns while the city's HP was never the target,
  and the Battering Ram was destroyed in the middle of the column.

None of it was a rules problem - it was geometry, and it is measurable.

## Prohibitions

- Never advance the siege train before its screen is in place.
- Never leave a siege unit adjacent to a city, a fortification or an enemy melee unit.
- Never put two support units (ram + tower) where one is doing no work, and never park a tower
  beside the ranged line - it helps melee only.
- Never advance into range 2 of a second enemy city while the first one is unscreened.
- Never let the formation break to chase a scout or a civilian.

## What to report

The tile you propose for each unit by role, the distances that make the formation correct (siege
to enemy, screen to that same enemy, siege to city), and which unit is the screen for which
siege unit. If a siege unit cannot be screened this turn, propose it holds or falls back, and say
what has to move before the advance can start.
