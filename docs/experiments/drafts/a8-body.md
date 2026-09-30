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

**The third city's first four orders** (name them in the diary and hold to them): `BUILDING_MONUMENT` ->
`DISTRICT_COMMERCIAL_HUB` (check `get_district_advisor` for the river tile) -> `BUILDING_MARKET` ->
`UNIT_BUILDER`, with the Builder going to the Horses first.

## The claim, and it is about gold

**Hypothesis (falsifiable by numbers): the third city contributes gold before it contributes production,
and the gold buys the second siege unit.**

- the number: a **second** siege unit is purchased with gold **before T58** - A6 bought its first at
  **T46** for 320g out of 396g (`PURCHASED|UNIT_CATAPULT|cost=320g`), and the programme's own arithmetic
  said two were impossible before about T70 on the path it was computed from;
- and the floor: **`gpt_T40` above +10**, which A7 missed on **all 60** of its turns (`gpt_T40 6.1`) and
  A6 missed as well (`5.4`), A4's 13.9 being the only attempt above it - bought with Pingala's science
  rather than with markets;
- **falsified** if no second siege unit is purchased by T58, or if `gpt_T50` is no higher than A7's.

The first siege unit is still produced (not bought) unless the treasury allows both; say which, and when.

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
