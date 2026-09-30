# Attempt A8 - three cities, the third one an economy city

**Front matter, written while the attempt plays.** This is the head of `docs/experiments/008-attempt-A8.md`;
it is filled from the published task file (`prompts/tasks/tmp/040-attempt-a8-three-cities-the-third-one-an-economy-city.md`)
and from the instrument's own reads, and the results section is appended when the run reaches T110. It
lives in `drafts/` until then so that a half-record cannot be read as a finished one.

Attempt A8 of the military-production experiment (`docs/experiments/README.md`, section 3). A7 is
`007-attempt-A7.md`, whose window was extended to T110 by task 039 and whose T110 row is the baseline
this attempt is measured against (`docs/experiments/A7-T110.json`); the cross-attempt report is
`RETRO-2026-09-29.md`; the design note is `drafts/A8-A9-city-count.md`.

## Settings: the shared start, one variable

| | A7 (the standing baseline) | A8 |
|---|---|---|
| start | the experiment's shared T1 start | **the same save, loaded at T1** |
| the save | `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` | the same file, **verified bit-identical to the copy the earlier attempts used**: SHA256 `B89AD3EB24CF6D8094616441F761C405DB7F98E397141296E0DB7B6881ED6346`, mtime unchanged at 09-30 06:31, checked *after* the load |
| doctrine | the corrected `tactics/01` table, `tactics/08`'s one war city **widened to two army cities** | the **same corrected table and `tactics/08`'s one war city held exactly**; the third city's queue is economy, not army |
| the one variable | two war cities instead of one | **three cities, with the third one settled and its queue economy** - the programme has held the city count at two in every attempt, and the three third cities in A3/A4/A7 were all **captured** |
| the wonder | the T25-onward `dynasty-cycle-wonder` obligation deferred, recorded as accepted | **the same deferral, and for the same reason** (see below) |
| window | a city kept, or T110 | **T110** - the claim's last number cannot be read earlier |
| sessions | `divine-amber-outpost-82` (T1-T60) + `stormborn-azure-palisade-94` (T69-T110) | `volcanic-ochre-catapult-47` (T1-T6) + `tempered-jet-temple-30` (T6 on) |

## The opening is pinned, and the pin is the attempt's fifth slot

The first four orders are **unchanged from A3-A7**, so the opening stays comparable; **the fifth slot is
the variable** - a second `UNIT_SETTLER`, ordered the turn the Builder completes.

| order | item | promised | the record so far |
|---|---|---|---|
| 1 | `UNIT_SCOUT` | the pin's recon slot | **T1 - matched** (`PRODUCING\|UNIT_SCOUT\|4 turns`, the same turn `TECH_MINING` was set) |
| 2 | `UNIT_SLINGER` | the pin | **T5 - matched** (`PRODUCING\|UNIT_SLINGER\|5 turns`, the same turn A3/A5/A6/A7 ordered theirs) |
| 3 | `UNIT_SETTLER` | the pin - city #2, founded about T21 | **T10 - matched to A4 and A6** (`PRODUCING\|UNIT_SETTLER\|9 turns`; A3/A5/A7 ordered theirs on T6) |
| 4 | `UNIT_BUILDER` | the pin | **T18 - matched to A4 and A6** (`PRODUCING\|UNIT_BUILDER\|4 turns`; A3/A5/A7 ordered theirs on T15) |
| 5 | **`UNIT_SETTLER`** | **the variable** | not yet ordered - it comes the turn the Builder completes |

Research and civics so far: `TECH_MINING` T1, `TECH_POTTERY` T8 (Mining completed T7), `TECH_WRITING`
T13; `CIVIC_CODE_OF_LAWS` T1, `CIVIC_CRAFTSMANSHIP` T11.

**City #2 was founded at T20 - and it went EAST, at (63,25), where every previous attempt went west.**

| attempt | city #2 | founded |
|---|---|---|
| A3 | (55,23) | T19 |
| A4 | (55,21) | T22 |
| A5 | (57,25) | T21 |
| A6 | (54,22) | T27 |
| A7 | (53,21) | T21 |
| **A8** | **(63,25)** | **T20** |

Its own settle read at T17 was the **per-settler** one, whose `#1 (62,25), score 195, no water` it did
not take - (62,25) is inside 西安's three-tile exclusion and would have been refused - so the founded tile
is the legal neighbour of the advisor's first choice. **This is a real divergence and it is not the
variable**: the pin fixes the *order*, not the tile, and no earlier attempt recorded which of the two
lists it read from.

**What it changes is the third city's geography, and that is the point.** The near-west cluster (x 53-57,
y 20-24) that A3-A7's second city consumed is **still open**, because A8's second city is east - and the
T69 pre-flight read, taken with three cities standing, could not see it. So A8's third city may be a
**satellite after all** rather than the twenty-tile colony the pre-flight arithmetic assumed. **Both
cases are already handled by the claim**, which derives its two turns from the founding turn `F`: a
satellite founded about T30 has a Market by T50 and the floor is read there; a colony founded about T48
does not, and the floor moves to `F+22` with the T110 comparison carrying the claim.

## The third city: chosen on the turn the Settler is ordered

**The site is a rule, not a tile**: on the turn the second Settler is ordered, run
`get_global_settle_advisor` and take the highest-scoring legal site, **preferring the nearest one within
about 10 score of the best**, recording the tile, the score, whether it has fresh water and its hex
distance from 西安.

**Why it is a rule.** The only read the programme has from a three-city position (T69 of the A7
continuation) put its whole top ten inside one block, **x 39-42 / y 25-29**, #1 at **(40,26), score 217,
fresh water**, with `STONE, HORSES, COPPER, BANANAS, MAIZE, WHEAT, FURS` in radius and nine of the ten
with fresh water. That read was taken with **three** cities standing, so it is **strictly more
restrictive** than A8's two-city position - a site four to six tiles from 西安 can be legal at T21 and
never have appeared in it. And the site it named is about **20 tiles from the capital**: a two-move
Settler over that ground walks fifteen to twenty turns, which puts the third city at about **T48** and its
**Market at about T70** - after the window a fixed claim would have judged it in. **A satellite founded
about T30 has a Market by T50; a colony founded about T48 does not.**

**And the city brings something the core lacks**: HORSES - a strategic resource no A3-A7 city held (the
programme's `cavalry` row was filled by Heavy Chariots, which need none) - plus a second luxury cluster
(`FURS`, `DYES`).

**The two settle advisors are not the same instrument, and the record says which was used.**
`get_settle_advisor(unit_id)` lists the best sites **near one settler unit** (top five);
`get_global_settle_advisor()` scans **the whole revealed map** (top ten). The task file names the global
one for the third city, and **the pre-flight read's blind-spot argument belongs to the global list**,
because that is what the T69 read was. A8's first read - `get_settle_advisor` at **T17**, returning
`#1 (62,25) Score 195 F:60 P:29 no water` among five - was the **per-settler** one, and it was the right
tool for the question it was answering: the pin's own Settler, deciding where **city #2** goes (matching
A4/A6's T10 order, it is founded about T21). So it is not a deviation. **For the third city, the record
will state which of the two the site was chosen from and how many candidates it ranked** - a site chosen
from the local list is a legitimate choice, but the "the far cluster is not necessarily the only option"
argument was made about the global one and does not transfer without saying so.

**Its first four orders, named in the file**: `BUILDING_MONUMENT` -> `DISTRICT_COMMERCIAL_HUB` ->
`BUILDING_MARKET` -> `UNIT_BUILDER`, the Builder going to the Horses first.

## The claim, cut to its arithmetic

**Hypothesis (falsifiable by numbers): a third city that is settled pays for itself where a third city
that is captured does not - and on the way it funds the second gun.**

- **the two turns are derived from the founding turn `F`, not the calendar.** Purchase deadline
  **`max(T58, F+25)`**; the gold floor is read at **T50 if `F <= 28`**, otherwise at the ten-turn row at
  or after **`F+22`**. **`F` and both turns go in the diary on the turn the city is founded** - a claim
  whose window moves has to fix its window when it moves;
- **the number**: the **second** siege unit is **in hand by the purchase deadline, bought and not built**.
  A6 bought its *first* at T46 for 320g out of 396g; **A8 produces the first and buys the second**, so
  the two attempts' purchase columns are not the same act;
- **the floor**: `gold_per_turn` at the gold-floor turn **above A7's value at that same turn** (A7's
  merged report reads 8.1 at T50, 4.1 at T60, 2.1 at T70, 24.4 at T80, 49.0 at T90);
- **the number that discriminates at the horizon**: at **T110**, A8's **`science`, `pop` and
  `gold_per_turn` each exceed A7's**. Both runs end holding three cities; the difference is **how the
  third was obtained** - A8 pays a Settler, a colony's buildings and a long walk, A7 paid a war;
- **`gpt_T40` is a prediction, not a bar**: at or below A7's 6.1, because a third city founded about T30
  has no market by T40 and is meant to cost gold before it pays.

**Falsified** if the second siege unit is not in hand by the purchase deadline, if it was built rather
than bought, if `gpt` at the gold-floor turn is not above A7's there, or if any of A8's three T110
figures is at or below A7's. **Nothing here depends on the site being near** - a far colony moves the
deadlines out with it and the T110 comparison carries the claim.

## The wonder obligation is deferred, deliberately

`dynasty-cycle-wonder` is live from T25 and fires every turn until a wonder exists: the empire holds zero,
which the rule reads as half of China's civilisation ability forfeited. **A8 builds no wonder**, because
the third city is both this attempt's market city and the natural home for one, and building it would make
the attempt two variables. The rule is **accepted out loud in the diary**, and the wonder is owed its own
attempt rather than answered by silence.

## The recovery record, which belongs to this attempt's tooling

**A8's first six turns cost five separate tool defects and two stalls, and every one of them is written
down because the fixes are what made the run continue.** In order:

1. **the load trap** (T111): `load_game_save` answered `FAILED: 'ATTEMPT-A1-T1-settled' was issued, b...`
   **and the load landed anyway** - the game reached turn 1 while the call reported failure;
2. **a nine-minute retry on a landed load**: the screen read `TURN 1`, `CHOOSE RESEARCH`, `CODE OF LAWS`
   while `load_game_save` re-clicked CONTINUE about ninety times, with **4318 refusing and 4319
   answering `0 Lua states`**. It returned by itself. **The clicks were harmless**, proven by the
   session's own first read after recovering: `No technology being researched!` - a stray click that had
   chosen a research would have shown one;
3. **`HANG:6:0_MCP_0006` at T6**, then `GameCore_Tuner/InGame states not found`, then
   `load_game_save` answering `FAILED: Could not find 'Load Game' button` **twice**, then
   `dismiss_popup` answering `No popups to dismiss` - **and the game was parked on the loaded game's
   leader intro**, a screen Lua cannot see. It resolved by itself in about five minutes;
4. **the same turn hung twice on the same orders**: the log shows the loop exactly - move the Warrior to
   (54,23), `end_turn` hangs, recover, move the same Warrior to the same tile, hang again. Fixed by
   writing a rule (**if the same turn hangs twice, change one thing the turn does before trying a third
   time**) and **relaunching the session**, because a task file is read at the *start* of a turn and a
   recovery instruction cannot reach a session that is stuck inside the call it needs recovering from;
5. **the resumed session took different pathing destinations** (`get_pathing_estimate` on (54,24),
   (54,22) and one reachable) and the turn advanced: **T6 -> T13 with zero hangs**, on the pin.

**Two facts the stall produced, both measured and both now in `docs/game-recovery.md`**: a hang's screen
record distinguishes the two kinds - **A3's T70/T72 carry `PLEASE WAIT`** (the game is processing; a
genuine AI-phase stall) while **A8's T6 carries `NEXT TURN` with no `PLEASE WAIT`** (the game is idle at
the player's turn and the request did not take); and **a load that has already landed can keep retrying
for ten minutes without being a hang**.

**Also worth the record**: the game was restarted more than once during the recovery (its pid moved
28736 -> 23196 -> 5652 and the tuner settled on 4319), and the handoff used `civ6-clean.ps1 -KeepGame`,
which stops the agent and the MCP **and leaves the game**, because the shared start has to be loaded into
a running game. The plain invocation would have killed it.

## The measurement

`python scripts/experiment-report.py --game china_911679432 --run <sessions> --questions a8` answers the
four questions the claim is made of; `--save docs/experiments/A8-final.json` writes the snapshot the
compare block reads. The diary's **per-10-turn economy rows** are what the comparison uses, and their
presence is verified per turn rather than assumed.

## The record

*(to be written from the instrument's reads when the attempt reaches T110: the T10-T110 economy rows,
`F` and its two derived turns, the purchase or its absence, the third city's first four orders and what
it actually produced, the verdict on all four questions, and the divergences that are not the variable.)*
