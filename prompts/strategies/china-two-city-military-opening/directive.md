China (Qin, Unifier): two cities, then the war.

This preset is the measured distillation of the military-production experiment - the protocol is
`docs/experiments/README.md`, the cross-attempt report is `docs/experiments/RETRO-2026-09-29.md`, and
the attempt it is mostly built from is `docs/experiments/008-attempt-A8.md`. **Every turn number below
was measured in that programme**, and the two failures this preset exists to prevent are named with the
attempt that made them. Where a number is a derivation rather than a measurement, it says so.

**The shape: settle TWO cities, and take the third.** The opening's one extra Settler is not spent -
the empire's second city is the pinned one, and the third city arrives by conquest, which is what A7
did to take Jerusalem at T60, the earliest keep in the programme. A settled third city was measured too
(A8, founded T35) and it is a real option - but it is a different strategy, it is priced in section
"Growing past two cities", and it must not be entered by accident.

## The opening, in order

| order | turn | item | note |
|---|---|---|---|
| 1 | T1 | `UNIT_SCOUT` | `tactics/07`'s Gate 0: a city you have not seen has no pre-war analysis to make |
| 2 | T5 | `UNIT_SLINGER` | the pin's ranged slot; it becomes an Archer later |
| 3 | T10 | `UNIT_SETTLER` | **city #2 lands T20-T27** (A8 T20, A7 T21, A6 T27) |
| 4 | T18 | `UNIT_BUILDER` | mine the strategic tiles first |

The instrument certifies this opening as `PIN opening: held` in A4, A5, A6, A7 and A8, so it is the
one part of the attempt that is directly comparable between runs. **Do not add a fifth order before
`ENGINEERING` is owned** - the capital's queue between the Builder and the first Catapult is where
this strategy is won or lost, and section "The capital is the war city" is the whole reason.

## The research line IS the strategy, and it is the first thing to pin

**`MINING` -> ... -> `THE_WHEEL` by about T8 -> `ENGINEERING` by about T22.** A1-A7 all took
`THE_WHEEL` at T8 and owned Engineering around T22, and A3, A4 and A5 each ordered their first
Catapult on **the same turn, T43**.

**A8 is the counter-example and it is the most expensive measurement in the programme.** A8 went
economy-first (`THE_WHEEL` T41, `ENGINEERING` ordered T45), and its establishment question was
**FALSIFIED at T60** - short `anticav 0/1`, `cavalry 0/1` and `ranged 2/4`. The cause was not the
extra city and not the Settler: **it was the research line and the capital's queue**, and the record
proves it, because the pin held and A8's third city was founded by a Settler that cost it almost
nothing.

- **Name the Eureka before you research anything** (Dynastic Cycle below is why), and do not insert an
  economy technology ahead of `ENGINEERING` on a military plan.
- **A task file or a plan should pin the first research choices the way it pins the first four builds.**
  The programme pinned only the builds and lost A8's headline question to an unpinned research order.

## The capital is the war city, and its queue is the budget

One city builds the war; the others compound. Xi'an produces about 10-14 in the early game and 5-7
turns per Catapult; at pop 6 with `Prod ~10` A5 took **7 turns** per Catapult.

**The measured trap: from the moment city #2 exists, every order placed in the capital is an order not
placed on the army.** A8's capital spent **T31-T53** on a Campus, a Granary, a Trader and a Library,
and the first Catapult was not ordered until **T53** - which is why its T60 establishment was short
even though its army was eventually complete (by T90 it was short only `cavalry 0/1`).

- Put the Campus, the Granary and the Trade Route somewhere that is **not** the war city.
- The colony pays for its own buildings: in A8 the third city itself built `BUILDING_MONUMENT` at T35
  and its `DISTRICT_COMMERCIAL_HUB` at T48, out of its own production. **A new city's infrastructure is
  not the capital's problem.**

## The two multipliers, and they are both free if you take them early

- **`BELIEF_GOD_OF_THE_FORGE`**: *"+25% Production toward Ancient and Classical military units"*
  (`Beliefs.xml`). A5, A6 and A7 founded it at **T28, T25 and T23** on **17-19 faith** - the pantheon
  guard was fixed and live-verified, so the flat 25-faith threshold is gone. **A8 took Fertility Rites
  instead and paid 25% more production on every Catapult.**
- **`POLICY_AGOGE`**: +50% toward military units. Stacked with God of the Forge it took a
  120-production Catapult in Xi'an from **11 turns to 6** (A2, measured).

Take the pantheon when the faith arrives; do not hold it for a "better" belief on a military plan.

## The first siege formation

**What the instrument certifies as the corrected establishment**: `siege 2, melee 2, anticav 1, ranged
4, cavalry 1, recon 1`. It was completed at **T53 by A3**, **T54 by A4, A6 and A7**, and **T57 by
A5** - and never by A1, A2 or A8 inside their windows.

**What the doctrine asks for per city** (`prompts/strategies/china-conquest/directive.md`): **3
Catapults**, 2 melee, and 4 ranged (2 Crossbowman at range 2 and 2 Crouching Tiger at range 1), plus 1
cavalry for survivors. **No Battering Ram and no Siege Tower.**

**These two tables disagree about the siege row (2 against 3).** Resolve it by the target, not by the
table:

- **against a city that reads `walls: none`** - which is **every city this programme ever read**, eight
  of them in A3 alone - **2 Catapults, both inside range 2**, is the requirement, and a third is
  insurance;
- **against a city with walls**, build the third, because the wall pool has to come down first.

Everything else in the formation is the same either way: **2 melee** as the screen and the walk-in, **2
ranged at range 2** for the sortie units, **2 Crouching Tiger at range 1** (each with a melee holding
the tile in front of it), **1 anti-cavalry** because the target sorties Heavy Chariots - A2 measured one
adjacent to both Catapults - and **1 cavalry** for survivors. A Heavy Chariot needs no Horses, which
matters because the `cavalry` row is the one A8 never filled.

## The siege arithmetic, which is the most expensive lesson in the programme

- **A Catapult does 45-52 against a city** where an Archer does 9-11 into a CS 35 garrison. **A siege
  unit cannot attack a unit at all** - asking is refused with `ERR:SIEGE_CANNOT_ATTACK_UNITS` - so the
  ranged and melee units are the anti-personnel arm and the Catapults are the city arm.
- **A city heals about twenty points a turn**, and it only heals while any adjacent hex is outside our
  zone of control. The `SIEGE PROGRESS` block reports it as `supply line n/6 cut`.
- **Three Catapults firing together measured about 260 a turn** (Moscow T123: two did 174 in one turn).
  **That is what keeps a siege bounded.**

**A6 is the failure this section exists for.** A6 arrived with a **complete** establishment and had
bought a Catapult with gold, and the target finished the window at **200/200 - not one point of net
damage**: `SIEGE FIRE: 1/2`, **one gun in range**, and the supply line never passed **2/6 cut**.

- **Two guns in range 2 is the minimum that out-damages the heal** (2 x 45-52 against about 20 heals
  back); one gun does not, and it is not a slow siege, it is a siege that does nothing.
- **Cutting the supply line is cheaper than finding twenty extra damage a turn**: stand on or beside
  every adjacent hex.
- **Stage before you declare, never after.** The enemy city's ranged strike reaches 2 tiles, so a train
  fed in piecemeal is a train that dies in pieces.
- **Judge by `city hp: N/200` and `walls: N/100`**, never by the damage estimate - on a city tile that
  estimate describes the unit standing there.

## Growing past two cities

**Do it after the guns, not before, and know the price.** The two extra Settlers a four-city empire
needs cost **221 Quick production in total - about 18 turns of Xi'an's queue, or 3.1 Catapults** -
because `UNIT_SETTLER` is `COST_PROGRESSION_PREVIOUS_COPIES` and each copy is +30 base: Settler #2 is
110 base / 74 Quick and Settler #3 is 140 base / 94 Quick at Quick speed (`CostMultiplier 67`). Each
one also costs **1 population** out of the producing city and needs `PrereqPopulation 2`.

- **Settle on fresh water or do not settle.** `housing - pop <= 1` stalls a city for dozens of turns.
- **Read `get_global_settle_advisor` yourself on the turn you order the Settler**, take the highest
  score, and prefer the nearest site within about 10 score of it. A8's site was score 215, fresh water,
  five hexes from the capital - a satellite, because a two-city position is less restrictive than the
  three-city read the programme had inherited. **The far colony the design note feared did not exist.**
- **The third city by conquest arrives about 25 turns later than a settled one** (A7's keep was T60,
  A8's founding was T35) and it comes with its own infrastructure - A7 finished T110 with **9
  districts** against A8's **8**. **What A8 bought with the Settler was science and population**:
  at T110, science **60.9 against A7's 57.6**, pop **28 against 25**, and `gold_per_turn` **70.7
  against 60.0** - so a settled third city compounds, and it does not pay for the guns that take the
  first one.
- **A fourth city matures past the window this preset optimises for.** A8's third city needed 41 turns
  from founding (T35) to its Market (T76); a fourth lands around T78-T85 and matures past T110. **Four
  cities is a bet on the next hundred turns, not on this one**, and it has never been run: A9 is
  registered and unpublished.

## China's kit, and the half of it the programme never played

- **Dynastic Cycle** (civilisation ability): Eurekas and Inspirations are worth **50% instead of 40%**
  under this ruleset, and **completing ANY wonder grants a random Eureka and Inspiration from that
  wonder's era**. For China **a wonder is a research building** - and **the programme built zero
  wonders across eight attempts and roughly 340 turns**, with A8's `dynasty-cycle-wonder` check firing
  on **100 turns**. **Put one wonder in the plan, in a compounding city, and do not leave it to
  "later"** - later never comes, and the cost is half the civilisation ability.
- **Thirty-Six Stratagems** (leader ability): a melee unit converts an adjacent barbarian to our side
  **at the cost of the melee unit**. **The adapter exposes no action for it, so only the human can
  trigger it** - the agent's job is to **report any barbarian standing next to one of our melee units
  whose type is worth converting**, before the camp is destroyed. Barbarian camps are destroyed by
  force - one military unit moving onto the tile - and an uncleared camp keeps producing era-appropriate
  units next to our cities.
- **Crouching Tiger** (unique unit): Medieval ranged, **Range 1**, high strength. **Range 1 means it
  stands adjacent**, so every Tiger needs a melee unit holding the tile in front of it. It fills part
  of the `ranged 4` row, and no tactic in this repository yet says which tile it takes.
- **Great Wall** (unique improvement): built by **Builders**, costs **no city production**, and returns
  Gold, Culture and Defence along the border. **Surplus Builder charges go to Wall segments** rather
  than expiring unused; it is not part of the military-production budget.

## The gold floor, and where the money actually comes from

The directive's own floor is **+10 gold/turn with the army counted**, and across the whole programme
**only A4 ever stood above it** (`gpt_T40` 13.9, and that came from Pingala's `Researcher` promotion -
5.5 to 13.9 science a turn - not from a market).

- **A distant high reading proves nothing.** A7's own curve reaches **24.4 at T80 and 49.0 at T90 with
  no market and no wonder at all**, on its Campus, its twelve improved tiles and its six districts.
- **A8's own final gold did not come from its Market.** Two policy cards - **Town Charters and Merchant
  Confederation, about +24 gold/turn** - carried the last ten turns, and A8's Market only completed at
  **T76**. **So do not build a Market to fund a war; fund it with trade routes and policy cards.**

## Standing rules that do not change

- **Three phases on every target, city or camp: analysis (`prompts/tactics/07-pre-war-analysis.md`),
  staging (`prompts/tactics/04-staging-out-of-range.md`), execution (`prompts/tactics/05` and
  `prompts/tactics/06`).** Write the staging plan before the first move; never attack a target on the
  turn it is noticed.
- **Never call `propose_peace`**, and refuse every offer - the strategy ends a war by taking the city.
- **Upgrades are cheap power**: A8 made 4 `upgrade_unit` calls from T78. A Slinger into an Archer is
  40 gold.
- **If the empire changes shape** - a new war, a city kept, a district or unit line this preset does not
  ask for - **say so in the diary that turn**. A7's second war city and A8's war with the Maori were
  both real costs that the plan had not budgeted.

## What this preset does not decide, and the honest gaps

- **Walled targets have never been measured.** Every city this programme read said `walls: none`, so
  the wall-breaking half is untested and the ram is forbidden anyway (and `prompts/tactics/01-unit-production.md`
  still lists a ram slot, which makes "the establishment is complete" unsatisfiable as written - A2's
  Q1 was failed by exactly that).
- **The Market arm is not established.** A8 proved a settled third city wins on science and population;
  it did not prove a Market pays for anything.
- **Four cities has never been run.**
- **How many turns a wonder's free Eureka is actually worth has never been measured.**
