# Game 13 — China / Qin (Unifier), the Russian war T103–T130

Played through `civ6-mcp` by a DSH-orchestrated agent driving `GameState` directly through
`scripts/play-turn.py` (no MCP tool surface in the loop). This report covers the whole war, from
Russia's declaration to their elimination, and is written from the diary rows T99–T131 plus the
InGame measurements taken at the time. The game continues; this is the war's post-mortem.

**Result: won.** Russia declared at T103, Moscow fell T110, 圣彼得堡 (their original capital) T117,
阿斯特拉罕 T130 — three cities, seventeen turns, **three units lost**, and this empire at eight
cities with both enemy capitals. Russia left the map with no army, no walls on any city, and one
Swordsman that spent the war being re-garrisoned into cities we then took.

---

## The war in numbers

Every figure below is a measured InGame read, not an estimate.

| Turn | Event | Number |
|---|---|---|
| T100 | Reconnaissance of the target | 莫斯科 pop 3, **200/200 hp, walls 0/0**, garrison Warrior 100 HP; 圣彼得堡 and 阿斯特拉罕 **also wall-less**, St Petersburg with no garrison |
| T100 | Russia's field army | Archer (52,38), **Swordsman CS 35** (53,40), Builder, Scout, Missionary |
| T103 | Russia declares war (Peter's border complaint, refused) and 那烂陀 joins as its suzerain | our army was two turns short of its staging row |
| T107 | First siege shot, garrisoned city | Archer does **9** |
| T108 | Same, over a turn cycle | **~11 a shot** against a 20/turn heal — net negative |
| T108 | Firing ring around Moscow enumerated | **6 tiles** at distance 2 |
| T109 | Garrison sorties (bait) → city ungarrisoned | 4 shots = **95 damage** (198 → 103), melee 36 for **0 taken** |
| T112 | 圣彼得堡, no garrison | melee **44 for 0 taken**; archers 35 |
| T115 | 圣彼得堡 pool 59 → 0 | capture **failed**: the 9 HP Horseman died |
| T117 | 圣彼得堡 taken | Heavy Chariot, adjacent, moved in |
| T123 | 阿斯特拉罕 re-garrisoned by a Swordsman | archers back to **~11** |
| T129 | 阿斯特拉罕 pool → 0 | capture **failed**: a 4-tile "walk in" reached only 3 tiles, then ZOC refused the last step |
| T130 | 阿斯特拉罕 taken | Horseman (98 HP, unspent) moved 2 tiles in |

**Rate of fire, by target:** an Archer does 35 against an ungarrisoned wall-less city and 9–11
against one with a CS 35 garrison. A Catapult (Bombard 35) does 45–52 either way. That single pair
of numbers decided every siege in this war.

---

## Five laws this war produced

### 1. The garrison, not the walls, is what makes a city hard — and it is the first thing to read

Moscow and 阿斯特拉罕 (both garrisoned) took 7 and 6 turns of fire respectively; 圣彼得堡 (no
garrison) went from first contact to ours in **five turns including the march**, and its pool fell
44 a turn to free melee alone. A CS 35 unit inside a city cuts archer damage by roughly two thirds
(35 → 9–11) because a share of its strength is added to the city's defence, and the garrison itself
takes no damage while the city is attacked.

**Doctrine result:** `tactics/07-pre-war-analysis.md` now reads the garrison *before* the walls, and
`tactics/06` carries the measured damage table so the fire plan is built on it.

### 2. An ungarrisoned, wall-less city does not retaliate against melee — melee is free damage

Measured twice: Heavy Chariot 36 damage for 0 taken (T109), Horseman 44 for 0 taken (T112). Against
a **garrisoned** city the same melee took 14 (T105).

**Doctrine result:** `tactics/06` order-of-work now says melee attacks the pool every turn when the
city is ungarrisoned and rotates home when wounded — and that the *cheapest* way to make a city
ungarrisoned is to invite the sortie (T109: the Swordsman left, and our damage tripled).

### 3. The capture is a combat action with three requirements, and every one of them was violated once

1. **The capturing unit must MOVE, not attack.** Attacking spends all remaining movement (T110:
   the Chariot was ordered to move precisely because of this).
2. **It must be adjacent at the START of the turn.** T129: a 4-tile order with 4 movement points
   reached only 3 tiles, and the last step was refused by the city's zone of control
   (`tile is enemy territory but movement still blocked`).
3. **It must have health.** T115: a 9 HP Barbarian Horseman died executing the capture and the
   city stayed Russian. T117's Warrior also failed — it walked away, because the path needed 3
   points and it had 2.

**Doctrine result:** all three are now in `tactics/06` as one rule with the turn references, and the
driver refuses nothing here but warns (see law 5).

### 4. The firing ring is the throughput ceiling, and it must be enumerated before the war

Moscow's ring had six usable tiles; 圣彼得堡's had two of its six blocked by mountains (T113:
`BLOCKED (impassable mountain)` on (57,41) and (54,42)); 阿斯特拉罕's east side was mountains, so
for most of that siege only **three** shooters could fire at once (T127). An army of four Archers
and two Catapults fires as many shots as the ring allows, not as many as it has units.

Two further per-tile facts, both measured:

- **LOS is not distance.** (53,35)→(52,37) was refused `NO_LOS` while (52,36)→(53,37) at the same
  range went through; a Catapult refused (54,40) from (55,38) and fired from (52,38) (T107).
- **A one-tile move can cost two movement points.** Five separate siege turns were lost to this:
  (53,37)→(53,38) and both Catapults' single-step moves at T114 (`NO_MOVES|Ranged attacks require
  movement`), and the last step at T129. Ranged attacks need movement in hand, so "move into range
  and fire" is a plan only when the move costs one point.

**Doctrine result:** `tactics/04-staging-out-of-range.md` now requires the ring to be walked and
listed before the declaration, and `tactics/05` requires the approach lanes to stay clear.

### 5. A wounded unit inside an enemy's reach is a unit you have already lost

All three losses of the war are the same event:

| Unit | HP when it died | Where it stood | What killed it |
|---|---|---|---|
| Barbarian Horseman | 9 | ordered onto a 0/200 city | the capture action |
| Warrior [11] | 23 | adjacent to the city | the CS 35 Swordsman |
| Archer [12] | 35 | adjacent to the city | the same Swordsman |

The doctrine already had this rule (`tactics/03`'s BAIT case, and `formation_violations` in
`play-turn.py posture` computes it as "a wounded unit within two tiles of an enemy"). It was not
applied because nothing forced it at the moment the turn was closed.

**Doctrine result:** `play-turn.py end` now prints a **WOUNDED IN REACH** block before it discards
any unit's turn, naming each unit at 60 HP or less that is within two tiles of an enemy — the same
test `posture` already used, moved to where the decision is actually made.

---

## What the war cost, and what it bought

- **Cost:** three units, 15–18 gold per turn handed to maintenance for the last two ten-turn
  windows, and a `carrying-capacity` check that failed from the moment the army was assembled
  (military ~270 against gold per turn under +10). Science went **flat** across the T100–T110
  window (−0.09/turn) while territory and units grew.
- **Bought:** eight cities, both Russian capitals, the domination requirement against Russia
  complete, four strategic resources now inside our borders (coal, iron, amber, uranium), and a
  war that never had to be fought twice — the frozen "no peace" rule was never tested because the
  enemy never held an advantage to trade for.
- **Timing, judged honestly:** the T99 plan said the war would start T105–T106 and Moscow would
  fall T107–T109. Russia declared first, at T103, and Moscow fell T110. The plan was one turn out
  on the city and two turns early on the declaration — and the early declaration is itself the
  lesson: **massing an army on a border is what triggers the war**, so the army must be able to
  fight from where it stands the moment it starts to mass, not from a staging row two turns away.

## What was landed as a result

| Change | Where |
|---|---|
| Garrison read first; the measured damage table (Archer 9–11 garrisoned vs 35 not; Catapult 45–52) | `prompts/tactics/06-assault-composition-and-fire.md` |
| The three capture requirements, with the T110/T115/T117/T129 references | `prompts/tactics/06-assault-composition-and-fire.md` |
| The ring must be walked and enumerated before the declaration; movement costs one or two points | `prompts/tactics/04-staging-out-of-range.md` |
| Approach lanes stay clear; melee on the ring, shooters behind | `prompts/tactics/05-formation-and-screening.md` |
| Pre-war gates: garrison first, ring count, sortie bait | `prompts/tactics/07-pre-war-analysis.md` |
| A wounded unit in reach is printed at the end of every turn | `scripts/play-turn.py` (`end`), with tests |
| The siege arithmetic and the capture laws, in the agent reference | `AGENTS.md` |
