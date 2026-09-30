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
3. **No support unit at all**: neither a ram nor a tower is built or fielded (human instruction
   2026-09-30: 不生产也不使用撞锤/攻城塔), including any ram the empire already owns - it stays a garrison
   unit. A support only works from the tile adjacent to the city and only for melee, so the tile it
   would have taken is a firing tile the siege wants; the Catapult does the wall work.
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
- **Never leave a wounded unit inside an enemy's reach.** A unit at 60 HP or less within two tiles
  of an enemy is a unit you have already lost: it attacks for proportionally less (manual p.88) and
  dies to one blow. All three losses of the T103–T130 war were exactly this - a Barbarian Horseman
  at 9 HP ordered onto a 0/200 city, a Warrior at 23 HP left adjacent to a CS 35 Swordsman, and an
  Archer at 35 HP one tile from the same unit. Withdraw it to a city (20 HP/turn) or friendly
  territory (15) - never leave it where it is because the attack is convenient.
- **Keep one approach lane free.** The formation is not only about who screens whom: our own stack
  is the most common obstacle to our own ring and to the capture move. Two distances are easy to
  confuse here — melee belongs **adjacent** to the city (distance 1, where it attacks and where the
  capture happens), shooters belong **on the ring** at distance 2. At 阿斯特拉罕 the shooters sat on
  both adjacent tiles, which are the only ones the melee could have used, and the assault had no unit
  able to reach the city until they moved. Leave at least one adjacent tile free.

## The end-of-turn warning that enforces the first of those

`scripts/play-turn.py end` prints a **WOUNDED IN REACH** block before it discards any unit's turn,
naming every unit at 60 HP or less that is within two tiles of an enemy. It is the same test
`posture` already computed (`formation_violations`), moved to the moment the decision is made,
because the rule above was in the doctrine throughout the war and was still broken three times.

## What to report

The tile you propose for each unit by role, the distances that make the formation correct (siege
to enemy, screen to that same enemy, siege to city), and which unit is the screen for which
siege unit. If a siege unit cannot be screened this turn, propose it holds or falls back, and say
what has to move before the advance can start.
