# 1. Unit production strategy / 部队的生产策略

Read when proposing production, a purchase or an upgrade.

## What the army is for, in one line

Production is not "build units". It is **keeping the establishment the current war needs**:
enough siege to break a city, enough melee to take it, enough ranged to clear the garrison, and
enough screens to keep the siege alive - while every city still keeps one garrison and the
economy keeps compounding.

## The establishment to build toward

| Role | Count for one assault | Types |
|---|---|---|
| Siege | 2 | Catapult → Trebuchet → Bombard |
| Melee | 2 | Warrior → Swordsman → Man-at-Arms |
| Ram / tower | 1 | Battering Ram (65) or Siege Tower (100) |
| Ranged | 4 | Slinger → Archer → Crossbowman, plus China's Crouching Tiger |
| Cavalry | 1 | Horseman → Knight (survivor hunter, reaches past the screen) |

Peacetime establishment is different and smaller: **one garrison per city plus one mobile unit**.
Once a war is on, that is the cap, not the floor - everything above one unit per city belongs at
the front (`one-garrison-per-city`).

## Production order

1. **Anything the assault is missing, first.** Siege and the ram/tower outrank everything that
   is merely nice: the whole point of the train is that it exists *before* the war, not during
   it. A campaign in this game built zero siege units and took ten turns per city.
2. **Then the screens**: melee to hold the front tile, ranged to fire from range 2.
3. **Then the economy buildings** the empire is short of (food first where a city is stalled).
4. **Wonders only after the war machine is complete.** For China a wonder is a research
   building (Dynastic Cycle grants a Eureka *and* an Inspiration), but a wonder does not break a
   wall.

## Numbers that decide the choice

- Catapult 120 / CS 25 / **45 vs cities** (Engineering, no resource).
- Trebuchet 200 / CS 35 / 45 (Military Engineering, no resource).
- Bombard 280 / CS 45 / 55 (needs Niter - mine it at home; an import ends when you declare war).
- Battering Ram 65 and Siege Tower 100 are support units: they help **melee only**, must stand
  adjacent to the target city, and **both go obsolete at `CIVIC_CIVIL_ENGINEERING`**. Build the
  ram before that civic lands or accept that nothing but siege will ever bypass a wall again.
- Upgrades are usually the cheapest strength in the game: Slinger → Archer (Archery),
  Warrior → Swordsman (Iron Working), Horseman → Knight (Stirrups). An old unit at full health
  plus gold is a new unit without the production queue.
- Buy when the wait costs more than the gold: a 4-turn ram bought for ~260 gold arrives now, and
  a city that is two turns from falling does not need a 10-turn Trebuchet ordered for it.

## Prohibitions

- Do not order units that counter nothing in sight. Cavalry against a walled city is a donation.
- Do not leave a city with an empty production queue: it is the single most common reason a turn
  bounces.
- Do not build a Settler in a size-1 city, and do not expand past the plan while a war is short
  of siege.
- Do not start a war for which the establishment above is not already in place.

## What to report

For each proposed build: the city, the item, the turn estimate, and which role of the table it
fills. Flag the assault role that is still at zero and what it will take (turns or gold) to fix.
If a required unit needs a tech or resource we do not have, say so as a warning rather than
silently proposing it.
