Attempt **A8** of the military-production experiment (`docs/experiments/README.md`, section 3). A7 is
`007-attempt-A7.md` and the cross-attempt report is `RETRO-2026-09-29.md`; the design note this file is
built from is `drafts/A8-A9-city-count.md`, and A9 is registered but **not published** - it waits on this
attempt's result.

**The one variable: three cities, settled first, and the third one is an economy city.** The programme has
held the city count fixed at two in every attempt - no second Settler was ever ordered, and the three
third cities in the record were all **captured**. A8 adds the second Settler and gives the third city a
market queue instead of an army queue. Nothing else changes.

## Start: the shared start

0. `get_game_status`. **This attempt is measured from the experiment's shared start**:
   `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`. If the game does not stand on it, load that save
   (`restart_and_load`, or the save list) and say in the diary which turn the loaded save holds. Playing
   A8 on another position makes its numbers incomparable with A1-A7, which is the one thing the experiment
   cannot afford.
1. Then `get_diary` and one `scripts\orient.py` read.

## The opening is pinned, and the pin's fifth slot is the variable

The first four orders are **unchanged from A3-A7**, so the opening stays comparable:

| order | item | why |
|---|---|---|
| 1 | `UNIT_SCOUT` | the pin's recon slot |
| 2 | `UNIT_SLINGER` | the pin |
| 3 | `UNIT_SETTLER` | the pin - **city #2**, founded about T21 (A7 measured T21 from a T6 order) |
| 4 | `UNIT_BUILDER` | the pin |
| 5 | **`UNIT_SETTLER`** | **the variable.** `UNIT_SETTLER` is 80 base with `COST_PROGRESSION_PREVIOUS_COPIES` +30 per copy, so copy #2 is 110 base / **74 Quick** - about one Catapult's production. Order it the turn the Builder completes, and say in the diary the turn it is ordered and the turn the city is founded |

## The third city: the site is named, and it is far

**Settle (40,26).** Read from `get_global_settle_advisor` at T69 of the A7 continuation - the only
post-second-city read the programme has ever taken - where it is **#1 of ten, score 217, fresh water,
defense 4**, with `STONE, HORSES, COPPER, BANANAS, MAIZE, WHEAT, FURS` in its radius. Nine of that read's
ten sites have fresh water and all ten sit in one block (x 39-42, y 25-29); (40,26) is the best of them and
the only one the file names.

**Carry the distance into the plan, because it is the cost.** (40,26) is about **11 tiles from 耶路撒冷 and
14 from 成都** - this is an **expansion, not a satellite**: it shares no tiles with the core, it needs its
own garrison (`one-garrison-per-city`), its own Builder, and it will be the barbarians' target long before
it is the enemy's. Run `get_pathing_estimate` for the Settler before ordering it and write the arrival turn
into the diary; a Settler that walks eleven turns is eleven turns of the variable.

**And it brings two things the core does not have**: **HORSES**, a strategic resource no A3-A7 city held
(the programme's `cavalry` row was filled by Heavy Chariots, which need none), and a second luxury cluster
(`FURS`, `DYES`) against an empire at `Amenities 5/2/2`.

### Confirm the site with your own read, because that read was taken on an explored map

**(40,26) is a target, not a guarantee, and the difference is fog.** The read it comes from was taken at
**T69**, when the west was already revealed by the scouts; A8 orders its second Settler around **T21**, when
much of that corridor may still be dark. Three things can therefore differ, and each has a stated answer:

- **run `get_global_settle_advisor` yourself on the turn you are about to order the Settler** - it is the
  same tool, and it is cheap. If (40,26) is not in your list, or is not revealed, **take the best legal
  site it does name**, settle that instead, and **record the substitution in the diary with both sites and
  the reason**. The variable is *the number of settled cities and the third one's economy queue*, not the
  tile - a substitution does not weaken the attempt, but an unrecorded one would;
- **send the recon unit down the corridor before the Settler commits.** Gate 0 of `tactics/07` applies to a
  settle site as much as to a city: you cannot settle what you have not seen, and a Settler that walks
  eleven turns into fog and finds the tile taken has spent the variable's whole budget. Say in the diary
  which unit revealed which tiles and on what turn;
- **watch for foreign borders, a camp, and the `PrereqPopulation="2"` gate on the Settler itself** - a
  Settler costs `PopulationCost="1"`, so the city that builds it must be at pop 2 or more and loses one;
  `UNIT_SETTLER` is also `COST_PROGRESSION_PREVIOUS_COPIES`, so the second one is more expensive than the
  first (110 base against 80). Say what it actually cost.

**If the site turns out to be unusable**, the honest outcome is a third city somewhere legal plus the
record of why the intended one failed - not a second city and a quiet redefinition of the attempt.

**The third city's first four orders** (name them in the diary and hold to them): `BUILDING_MONUMENT` ->
`DISTRICT_COMMERCIAL_HUB` (check `get_district_advisor` for the river tile) -> `BUILDING_MARKET` ->
`UNIT_BUILDER`, with the Builder going to the Horses first.

## The claim, and it is about gold

**Hypothesis (falsifiable by numbers): the third city contributes gold before it contributes production,
and the gold buys the second gun.**

**Say which unit is bought and which is built, on every purchase, because A6 and A8 buy different ones.**
A6 bought the **first** siege unit (T46, 320g); **A8 produces the first in the war city and buys the
second**, so the two attempts' purchase columns are not the same act - the compare block's own
`siege_order` caveat says exactly this about A6, and A8 has to state its side of it.

- the number: the **second** siege unit is **in hand by T58** (bought, not built) - A6's first cost
  **320g** out of a 396g treasury (`PURCHASED|UNIT_CATAPULT|cost=320g`), and the programme's arithmetic
  said **two** were impossible before about T70 on the path it was computed from, which is the claim the
  third city's gold is supposed to break;
- and the floor, **taken at T50 and not at T40, because the arithmetic says a third city cannot be paying
  at T40**: `gold_per_turn` at **T50 above A7's 8.1** - A7's own T50 row, read out of the merged A7 report
  (`--game china_911679432 --run divine-amber-outpost-82,stormborn-azure-palisade-94`). The directive's own
  floor is **+10**, and across the programme only **A4** ever stood above it (`gpt_T40 13.9` against A7's
  6.1 and A6's 5.4) - and A4's was bought with Pingala's science, not with markets. **This is the clause
  the third city's market is supposed to move;**
- and a **prediction to check, not a bar to clear**: **`gpt_T40` will be at or below A7's 6.1.** A third
  city founded about T30 has `BUILDING_MONUMENT` -> `DISTRICT_COMMERCIAL_HUB` -> `BUILDING_MARKET` to build
  at a young city's production, so at T40 it is a garrison and a Builder's maintenance with **no market
  yet** - it is *supposed* to cost gold before it pays. If T40 reads above A7's 6.1, say what paid for it,
  because the market cannot have;
- **the confound is already in the record, and it is A7's own curve**: the continuation's merged report
  reads `gpt` **8.1 at T50, 4.1 at T60, 2.1 at T70 and 11.8 at T76** - so **A7 crosses the directive's +10
  on its own, with no market at all**, on the strength of the Campus and eight improved tiles. A8 therefore
  cannot claim the market merely because its `gpt` ends high; **T50 is the discriminator**, because that is
  the window in which A7's own climb has not yet arrived. Judge the market at T50, and if A8 is only ahead
  at T76, say that the market did not do it;
- **falsified** if the second siege unit is not in hand by T58, if it was built rather than bought, or if
  `gpt_T50` is not above A7's 8.1.

If the treasury cannot fund a second purchase, **that is the answer**: say so, name the turn the gold
actually reached 320, and do not sell the plan by building it quietly instead - the attempt exists to
measure the funding arm, and an unaffordable purchase is a measurement, not a failure.

## Held exactly: everything else

- the corrected `tactics/01` establishment, `tactics/04` staging, `tactics/05` screening, `tactics/06`
  fire, and `tactics/08`'s **one war city** - A8 does **not** widen it the way A7 did; the third city's
  queue is economy, so the empire has its war city and its compounding cities;
- the standing directive `prompts/strategies/china-conquest/directive.md`; **never call `propose_peace`**
  and refuse every offer;
- **if the empire changes shape** - a new war, another city taken, a district or unit line the doctrine
  does not already ask for - record it in the diary that turn as a divergence from this file's posture. It
  is not forbidden; it has to be named, because A7 and A9 are compared against this run.

## The wonder obligation is deferred, on purpose, and this is the override

`dynasty-cycle-wonder` (`prompts/checks/turn-checks.md`) is live from T25 and **will print
`CHECK FAILED [dynasty-cycle-wonder]` from that turn on**: the empire holds zero wonders, which the rule
reads as half of China's civilisation ability forfeited. The directive's China section says a wonder is a
*research building* for China, and it is right.

**Accept the rule and build no wonder in this attempt.** A8's variable is the third city's **market**, and
the same city is where a wonder would go; building one here would make the attempt two variables and would
answer neither question. Say so in the diary **the first turn the rule fires**, in one line, and after that
mention it only when it changes something - this is `AGENTS.md`'s rule that a failing check is fixed or
accepted out loud. **The wonder is a real question and it is owed its own attempt**; it is not being
answered by silence here.

## The measurement

The experiment reads the diary's **per-10-turn economy rows**. Keep the five reflection fields every turn
and write the rows for **T10, T20, T30, T40, T50, T60, T70, T80, T90, T100 and T110** - the comparison
needs the same rows A7's continuation writes. What matters at T110, in numbers: `cities` (3 by design),
`pop`, `science`, `gold_per_turn`, `districts`, `improvements`, the turn the third city was founded, the
turn the second siege unit was bought, and the total gold spent on purchases.

## End

The attempt ends the turn **a second siege unit is purchased with gold, or turn 110 is reached**, whichever
comes first. On that turn report:

- the purchase (the item, the price, the treasury before it, and the turn) or that no second purchase
  happened and why;
- the T110 economy row beside A7's, field by field - it is the comparison the two runs exist for;
- the third city's founding turn, its first four orders, and what it had actually produced by T110;
- whether the empire's shape changed anywhere else, with the diary turn;
- whether any wonder was built (the expected answer is none, accepted).

Then retire this task with `--done` or `--expired` - **`--expired` if the window closed without the
purchase** - and hand back to the orchestrator.
