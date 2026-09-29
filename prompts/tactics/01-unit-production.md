# 1. Unit production strategy / 部队的生产策略

Read when proposing production, a purchase or an upgrade.

## What the army is for, in one line

Production is not "build units". It is **keeping the establishment the current war needs**:
enough siege to break a city, enough melee to take it, enough ranged to take the city's HP down
(a garrison sitting inside the city takes no damage - see file 6), and
enough screens to keep the siege alive - while every city still keeps one garrison and the
economy keeps compounding.

## The establishment to build toward

| Role | Count for one assault | Types |
|---|---|---|
| Siege | 2 | Catapult → Trebuchet → Bombard |
| Melee | 2 | Warrior → Swordsman → Man-at-Arms |
| **Anti-cavalry** | **1** | Spearman → Pikeman → Pike and Shot |
| Ranged | 4 | Slinger → Archer → Crossbowman, plus China's Crouching Tiger |
| Cavalry | 1 | Horseman → Knight (survivor hunter, reaches past the screen) |
| **Recon** | **1** | Scout → Ranger, or a spare cavalry unit |
| Ram / tower | **only one already owned** | Battering Ram / Siege Tower - never bought (see the production order) |

**Three rows changed after the A2 experiment (2026-09-29), and each one is a measurement rather than a
preference:**

- **`Anti-cavalry` was missing entirely.** `counter-the-cavalry` was red for the whole of A2's assault
  because nothing in the army could answer a Heavy Chariot: the city-state parked one **adjacent to both
  Catapults on every turn**, took a third of one gun's HP, and was never killed. The doctrine's answer to
  a screen breach - *the screen moves up* - is unsatisfiable when the enemy is already adjacent.
- **`Recon` was missing entirely.** A2 built no scout, explored 7% against A1's 14%, and spent
  twenty-six turns unable to read the target's walls, HP or garrison - the numbers `tactics/07`'s gates
  ask for. The first Catapult shot finally produced `walls: none` in one line. A role the table does not
  name is a role the empire does not build.
- **The ram row was unsatisfiable as written.** It asked for one ram while the human instruction two
  paragraphs below forbids buying one, so "the establishment is complete" was a claim no obedient session
  could satisfy: A2 read `siege 2/2, ram 0/1` at its best moment. It is now a *conditional* row - an
  already-owned ram joins the assault, and nothing is bought for that slot.

Peacetime establishment is different and smaller: **one garrison per city plus one mobile unit**.
Once a war is on, that is the cap, not the floor - everything above one unit per city belongs at
the front (`one-garrison-per-city`).

## Production order

1. **Anything the assault is missing, first.** Siege outranks everything that
   is merely nice: the whole point of the train is that it exists *before* the war, not during
   it. A campaign in this game built zero siege units and took ten turns per city. **No ram and
   no tower is bought** (human instruction 2026-09-26: 不用锤，用投石车) — the Catapult is the
   wall-breaker, and a support unit that only helps melee beside a city is production the siege
   could have had. The ram the empire already owns is the exception: it **does** join the assault
   (same day: 已经有攻城锤，就参战).
2. **Then the screens**: melee to hold the front tile, ranged to fire from range 2.
3. **Then the economy buildings** the empire is short of (food first where a city is stalled).

   **One exception, and it is a timing one: while the train is the bottleneck, a feature removal
   (chop or harvest) in a city that is building a unit goes into that unit.** A chop is production
   the city already owns, it arrives in one turn, and the buildings it would otherwise fund are
   worth less than a Catapult that exists five turns earlier. **Governor Magnus in the
   war-production city is what makes this worth doing**: his base ability Groundbreaker
   (`GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER`, `BaseAbility="true"`, +50% to plot
   harvests and feature removals in his city) is held from the moment he is appointed there - it is
   not a promotion to spend, and `promote_governor` on it answers `ERR:ALREADY_PROMOTED`. The
   effect is only banked when the feature actually disappears, and a tile outside the city's owned
   ring is refused, so the record names the city and the tile for every chop. Attempt **A5** is
   this exception measured against the economy it defers.
4. **Wonders only after the war machine is complete.** For China a wonder is a research
   building (Dynastic Cycle grants a Eureka *and* an Inspiration), but a wonder does not break a
   wall.

## Numbers that decide the choice

- Catapult 120 / CS 25 / **45 vs cities** (Engineering, no resource).
- Trebuchet 200 / CS 35 / 45 (Military Engineering, no resource).
- Bombard 280 / CS 45 / 55 (needs Niter - mine it at home; an import ends when you declare war).
- Battering Ram 65 and Siege Tower 100 are support units: they help **melee only**, must stand
  adjacent to the target city, and **both go obsolete at `CIVIC_CIVIL_ENGINEERING`**. They are never
  bought (the production order above), and a ram the empire already owns is the only case in which one
  joins an assault; if a wall has to come down, that is what the siege row is for.
- Upgrades are usually the cheapest strength in the game: Slinger → Archer (Archery),
  Warrior → Swordsman (Iron Working), Horseman → Knight (Stirrups). An old unit at full health
  plus gold is a new unit without the production queue.
- Buy when the wait costs more than the gold: a Catapult bought outright arrives the turn the tech
  lands, and a city that is two turns from falling does not need a 10-turn Trebuchet ordered for it.
- **The Great General is a unit the army has to keep.** Great Generals are earned mostly from
  Encampment districts (`GREAT GENERALS`, p.87), and the general itself is worth
  **+1 movement and +5 combat strength to land units within 2 tiles** - so an Encampment is not
  only defence, it is the cheapest combat bonus the army can buy. Never activate it for the
  one-off (see AGENTS.md): walk it with the stack, stack it with a combat unit for protection, and
  remember it dies if an enemy reaches its tile.
- **Corps and Armies are the late-game scaling lever, and the adapter cannot form them yet.** From
  the Industrial Era, `Nationalism` lets two same-type units combine into a **Corps (+10 combat
  strength)** and `Mobilization` lets three become an **Army (+7 more)**; the highest-experience
  unit's promotions are kept and the formation cannot be split again
  (`CORPS AND ARMIES`, p.156). Two Archer Corps at 35 ranged strength solve exactly the matchup
  problem `match-their-melee` reports. The game exposes it as `UnitCommandTypes.FORM_CORPS` /
  `FORM_ARMY` (`UnitPanel.lua`), but the MCP has no tool for it - so until one exists, either form
  them in the game window and say so, or plan the late war without them.

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
