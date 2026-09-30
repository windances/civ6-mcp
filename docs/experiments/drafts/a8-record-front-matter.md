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

**The variable is ordered, and the site the run read is a satellite - which is the decision paying off.**
At **T22** - the turn the Builder completed - the capital ordered the second `UNIT_SETTLER`
(`PRODUCING|UNIT_SETTLER|9 turns`), and the same turn the session ran
**`get_global_settle_advisor`** (the global one, as the file names) and read:

```
Top 10 settle locations:
  #1 (55,23): Score 215 - F:69 P:29 - fresh water, defense:2
```

**And it founded exactly that site: `T35 FOUNDED|55,23`.** So `F = 35`, the city is a **satellite about
five tiles from 西安** (it is the tile A3 founded its second city on), and its first order - per the file -
is `BUILDING_MONUMENT` (T35, 12 turns).

**`F = 35` fixes both of the claim's turns, and they land on the same one**:

| clause | derivation | the turn |
|---|---|---|
| the purchase deadline | `max(T58, F+25) = max(58, 60)` | **T60** |
| the gold-floor turn | first ten-turn row at or after `F+22 = 57` | **T60** |

**So the attempt is judged at T60 on both of its timed clauses**, and the bar the floor is read against is
**A7's T60 = 4.1** - a dip in A7's own curve (8.1 / 4.1 / 2.1 / 24.4 / 49.0 across T50-T90), not its T50
value of 8.1. **The later founding made the floor easier rather than harder**, which is the property
flagged above showing up concretely: **the floor clause alone is weak here**, and the T110 trio is what
carries the claim. The record will read the floor beside it rather than as the headline, exactly as the
claim's own fourth bullet says.

**And the Market is not even due by T60.** The third city's chain is `BUILDING_MONUMENT` (ordered T35,
12 turns) then `DISTRICT_COMMERCIAL_HUB` then `BUILDING_MARKET`, at a population-one city's production -
so the Market lands around **T67**, seven turns *after* the floor is read. **The T60 floor therefore
measures A8's empire economy and not its market**, which is the sharpest form of the caveat: the clause
the recut added so that a late city would not be scored as a market failure is, for *this* late city, not
about the market by construction. Stating that now rather than at the verdict is the point - at the
verdict it would read as an excuse. **A8's discriminating test is the T110 trio**: `science`, `pop` and
`gold_per_turn` against A7's at the horizon, where both runs hold three cities and the difference is how
the third was obtained.

**(55,23) is in the near-west cluster, about five tiles from 西安** - and it is the same tile A3 founded
its second city on. So the cluster A3-A7 consumed is genuinely open for A8, exactly as the T69 read's
blind spot predicted, and **A8's third city is a satellite rather than the twenty-tile colony the
pre-flight arithmetic assumed**. **A hard-coded `(40,26)` would have marched the Settler twenty tiles west
past an open 215-score site five tiles away**, which is the concrete form of why the site was made a rule.

**And it exposes a property of the derived floor worth stating before the verdict rather than after.**
With `F` around **T31** (ordered T22, nine turns, plus a short walk), `F > 28`, so the gold floor is read
at the ten-turn row at or after `F+22 = T53` - that is **T60**, against **A7's 4.1 at T60**. A7's own
T60 happens to be a low point in its curve (its series reads 8.1 / 4.1 / 2.1 / 24.4 / 49.0 across
T50-T90), so **the floor's discriminating power depends on where `F` falls**: a founding at or before T28
is judged against 8.1, a slightly later one against 4.1. That is not a defect in the rule - the rule says
"against A7 at the same turn", and T60 is the first turn the market can be judged - but it means **the
floor alone cannot carry the claim**, and the record will read it beside the T110 trio rather than as the
headline.

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

## Divergences that are not the variable, kept as a running list

A divergence is not a defect; it is a difference a reader would otherwise discover at review time and
attribute to the variable. Each is recorded the turn it happens.

1. **City #2 went east, to (63,25) at T20**, where A3-A7 all founded west. Recorded above with its
   consequences.
2. **The pantheon is `Fertility Rites` (T29), not `God of the Forge`** - which is what A5 (T28), A6 (T25)
   and A7 (T23) founded after the guard was fixed. **The doctrine does not name a pantheon** (a grep of
   `directive.md` for one returns nothing), so this is a free choice and not a deviation from the
   standing directive. **What it costs is measurable**: from the install's own text,
   `BELIEF_GOD_OF_THE_FORGE` is *"+25% Production toward Ancient and Classical military units"*
   (`Beliefs.xml`, `GOD_OF_THE_FORGE_UNIT_ANCIENT_CLASSICAL_PRODUCTION`) while `BELIEF_FERTILITY_RITES`
   is *"City growth rate is 10% higher."* **So A8 builds Ancient and Classical military units - Catapults
   included - twenty-five per cent slower than A5-A7 did**, on top of founding it six turns later. Any
   establishment-turn comparison against those three carries this, and the record says so wherever it
   appears.
3. **Xi'an ordered its Campus at T31** (`PRODUCING|DISTRICT_CAMPUS|5 turns`, after one refusal at (59,22)
   and an accepted order at (58,21)); A7 ordered its Campus around **T64**. So development is pulled
   earlier in the capital than in the baseline - which is a queue decision inside the doctrine, not a
   shape change, but it competes with the army for the same city's turns.
4. **`military` at T10 is 28 against A7's 34** - six down, within what the T5-T6 barbarian fight
   explains, and noted here so the gap is not credited to the third city later.
5. **The research path is economy-first, and it moved the siege gate itself.** A8 went `MINING` T1 ->
   `POTTERY` T8 -> `WRITING` T13 -> `CURRENCY` T21 -> `ANIMAL_HUSBANDRY` T39 -> **`THE_WHEEL` T41**
   (complete T44), where A1-A7 all took `THE_WHEEL` at **T8** and reached `ENGINEERING` around **T22**.
   Every attempt's
   file pins the *production* opening and none has ever pinned research, so this is a free choice - a grep
   of `directive.md` and `tactics/01` for a prescribed research order finds none, only the Catapult's own
   requirements. **Its consequence is what matters to the verdict**: the assault establishment is built
   behind Engineering, and A8 did not order it until **T45**, so **Q1's T60 deadline and Q3's T60 purchase
   deadline were both exposed to a gate that opened 23 turns late** - a reason that is **not the variable**
   and must be read beside them. The protocol consequence is written into `README.md` section 3: a later
   task file should pin the first research choices the way A3-A8 pin the first four builds.
6. **The empire's first Market is in city #2, not the third city.** `131073` ordered
   `BUILDING_MARKET` at **T50** (11 turns) on the Commercial Hub it took at T42, while the third city was
   still building its own Hub (T48, 14 turns). So the plan's economy is one city ahead of the chain
   `drafts/A8-A9-city-count.md` set out for the *third* city - `BUILDING_MONUMENT` -> Hub -> Market ->
   `UNIT_BUILDER` - and **city #2 is a second economy city the design note does not describe**. It is not
   forbidden (the file prices the third city's queue and says nothing against city #2's) and it is not the
   variable; it is recorded because it is the reason the empire's gold line moves when it does, and the
   claim's floor clause is judged on that line. **The third city's own Market is unaffected by it**: the Hub
   in front of that Market is still the T48 order.

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

## The order chain, read from the log while the run is still going

Every order the attempt has placed, with the city that placed it (`65536` is the capital Xi'an at
`60,22`, `131073` the city founded T20 at `63,25`, `196610` the third city founded T35 at `55,23`):

| turn | city | ordered | the reply |
|---|---|---|---|
| T20 | 131073 | `BUILDING_MONUMENT` | 15 turns |
| T31 | 65536 | `DISTRICT_CAMPUS` at `58,21` | 5 turns |
| T33 | 131073 | `BUILDING_GRANARY` | 12 turns |
| T35 | 196610 | `BUILDING_MONUMENT` | 12 turns |
| T36 | 65536 | `BUILDING_GRANARY` | 4 turns |
| T40 | 65536 | `UNIT_WARRIOR` | 3 turns |
| T42 | 131073 | `DISTRICT_COMMERCIAL_HUB` at `64,25` | 9 turns (the T33 Granary is dropped for it) |
| T43 | 65536 | `UNIT_TRADER` | 3 turns, built T45 |
| T46 | 65536 | `BUILDING_LIBRARY` | 5 turns |
| T48 | 196610 | `DISTRICT_COMMERCIAL_HUB` at `55,24` | 14 turns |
| T50 | 65536 | `UNIT_SLINGER` | 1 turn (after two `SILENT_FAILURE` retries) |
| T50 | 131073 | `BUILDING_MARKET` | 11 turns - **the empire's first Market, and it is in city #2** |
| T51 | 65536 | `UNIT_WARRIOR` | 2 turns |
| T53 | 65536 | `UNIT_CATAPULT` | 6 turns - **the first siege unit, built, due about T59** |

Research, from the same log: `MINING` T1, `POTTERY` T8, `WRITING` T13, `CURRENCY` T21 (the T38 read
is `3 techs, 3 civics` completed, still on Currency), `ANIMAL_HUSBANDRY` T39, **`THE_WHEEL` T41**
(complete T44), **`ENGINEERING` T45**, **`BRONZE_WORKING` T53**, **`ARCHERY` T54**.

**Four readings come out of that table, and they are not all on the same side.**

1. **The third city is on the chain the claim needs, and its clock is longer than the claim's.**
   `196610` took its Monument at T35 (12 turns, so it lands around T47) and its Commercial Hub at T48
   (14 turns, so around T62) - the Hub is the third city's second order, which is the plan the design
   note called for, and a **Market behind a Hub that ends near T62 cannot exist before about T70**.
   That is late for an arm of a claim judged at T60, and it is late because 14 turns is what a
   five-tile colony with fresh water and no production pays for a district. **The record states it
   before the deadline rather than after**: the claim's market arm will be read at the horizon, not at
   its own deadline.
2. **From T36 the capital's queue is economy only** - Granary T36, Trader T43, Library T46, Campus
   before them - with one Warrior at T40 the only military order in that stretch, and **no city
   working toward the siege train while Engineering is still in research**. So the gun is not being
   built early and upgraded, nor being pre-built; it waits for the tech.
3. **The establishment has not moved at all.** At T48 the corrected table reads
   `siege 0/2  melee 2/2  anticav 0/1  ranged 1/4  cavalry 0/1  recon 1/1`, and the army those rows
   count is five units (`WARRIOR:2, SLINGER:1, TRADER:1, SCOUT:1, BUILDER:1`).
4. **Then, inside seven turns, the attempt answers three of the four gaps by itself** - and the
   record has to carry the correction rather than the T48 reading. `BRONZE_WORKING` is ordered T53
   (the anti-cavalry row's tech), `ARCHERY` T54 (the ranged row's), and the **first Catapult is
   ordered T53 in the capital, 6 turns**, with the capital's own read at T55 showing `Sci 15` and
   `UNIT_CATAPULT (4 turns)`. So the tech half of the objection above is being closed by the
   attempt, not by a change of plan - and what is left is production and the clock.

**And the money has arrived, which changes which question is the live one.** The T50 overview reads
**`Gold: 298 (+14/turn)`**, and a Catapult purchase cost A6 320g at T46. So the treasury is one turn's
income short of the price eight turns before the deadline, **`Q3` - the second siege unit bought and
not built by T60 - is fundable and is now the question with something to lose**, where at T48 the
picture was an army that could not reach T60 at all. Two things are true beside it and belong in the
same paragraph: the Market at T50 went into **city #2**, not the third city, so the empire is buying
its economy one city ahead of the design's chain and the third city's own Market is still behind a
14-turn Hub; and **no rival had been met by T48** (`no rival met by T48: there is no city to aim at
yet`), so whatever establishment exists by T60 has no target the record can name.

**The consequence for `Q1`, stated at T48 and corrected at T55**: seven units of the corrected table
are short at T48 and at T55 the army is still `WARRIOR:2, SLINGER:1` plus the Catapult building, with
the other two cities' queues committed to a Market (11 turns) and a Hub (14 turns). **The cause is the
attempt's own plan, not its variable**: the production that would have filled those rows went into
four districts and five buildings, and the opening's tech list is the one every attempt is free to
choose and none has pinned. The
third city itself is **not** implicated - `Q2` is HELD and the pin held - so the honest reading at the
end of this attempt is that `Q1` measures **A8's economy-first opening**, and the third-city variable
is carried by `Q3` (the bought gun) and by `Q4`'s T110 trio. **That distinction is the one thing the
verdict must not blur**, and it is the second time in the programme that a question has been decided
by a divergence the task file never pinned: the pin fixes the first four builds and nothing after
them, so two attempts can hold the same pin and still be asking different questions. It is the same
finding as the research-pin note in `README.md` section 3, one step further along the queue.

## The measurement

`python scripts/experiment-report.py --game china_911679432 --run <sessions> --questions a8` answers the
four questions the claim is made of; `--save docs/experiments/A8-final.json` writes the snapshot the
compare block reads. The diary's **per-10-turn economy rows** are what the comparison uses, and their
presence is verified per turn rather than assumed.

**Verified mid-run at T27, on this attempt's own log rather than on A7's** - the point being to find a
pipeline fault while there are eighty turns left to fix it, not at the verdict:

```
--run volcanic-ochre-catapult-47,tempered-jet-temple-30 --questions a8
  OPEN  Q1 establishment complete by T60   [establishment not reached by T27; ...]
  OPEN  Q2 three cities settled            [foundings beyond the capital: 1 of 2 (T20 at 63,25); ...]
  OPEN  Q3 the second siege unit in hand by T58, bought not built   [deadline T58; bought: no siege unit was bought; ...]
  OPEN  Q4 the gold clause                 [the floor turn T50 has no readable row yet; ...]
  (OPEN means the deadline has not arrived: the attempt stands at T27, so those predictions are undecided, not failed)
```

**Re-read at T40, after the third city was founded, and this is the attempt's first decided question:**

```
  OPEN      Q1 establishment complete by T60   [establishment not reached by T40; ...]
  HELD      Q2 three cities settled            [foundings beyond the capital: 2 of 2 (T20 at 63,25, T35 at 55,23);
                                                the third city is the one founded T35; ...]
  OPEN      Q3 the second siege unit in hand by T60, bought not built
            [deadline T60 (max(T58, F+25) with F=T35); bought: no siege unit was bought; ...]
  OPEN      Q4 the gold clause                 [the floor turn T60 has no readable row yet; ... the draft's own
                                                prediction is gpt at T40 at or below A7's 6.1 and it read +5.3 ...]
```

**So the variable is delivered and the instrument certifies it**: `Q2 three cities settled` is **HELD**,
read from `found_city`'s own acknowledgements rather than from a `cities` count - which is the
discrimination the settlement reader was written for, since A3, A4 and A7 all also ended with three
cities, by conquest.

**Re-read again at T48, on the same command, and this is the reading the record above is built on:**

```
  OPEN      Q1 establishment complete by T60 (corrected table)
            [establishment not reached by T48; ...]        -> NOT complete at T48, short anticav 0/1
                                                              cavalry 0/1  ranged 1/4  siege 0/2
  HELD      Q2 three cities settled            [foundings beyond the capital: 2 of 2 (T20 at 63,25, T35 at 55,23); ...]
  OPEN      Q3 the second siege unit in hand by T60, bought not built
            [deadline T60 (max(T58, F+25) with F=T35); bought: no siege unit was bought;
             built in a city: none; ...]
  OPEN      Q4 the gold clause                 [the floor turn T60 has no readable row yet; ...]
  (the attempt stands at T48; the run is still playing)
```

**And the same command surfaces the thing that decides `Q1` early**: `first siege: never`,
`first anticav: never`, `first cavalry: never`, `ranged 1/4`, beside `map revealed 2% -> 15%` and
**`no rival met by T48: there is no city to aim at yet`**. The establishment is not merely late at
T48; the empire has not met anyone to point it at, and the two facts share one cause - the opening
spent its turns on the colony and its buildings. That is recorded here as the attempt's own shape,
not as a verdict on the third city.

**And the derived deadlines are verified on live data, not only in fixtures**: Q3 now reads `deadline T60
(max(T58, F+25) with F=T35)` - the code path that the whole recut rests on, printing its own derivation
from the founding turn it read out of the log.

**One prediction has held so far**: `gpt_T40` read **+5.3** against A7's 6.1, i.e. **at or below it**,
which is what the draft predicted and why - a third city founded at T35 has no market by T40 and is meant
to cost gold before it pays.

**Three things that check out**: the two-session `--run` resolves A8 as one attempt; **the founding is
read from the log correctly** (`1 of 2, T20 at 63,25`); and the instrument says `OPEN` with the reason
rather than `FALSIFIED` - which is the distinction `_status` exists for. The per-10-turn rows attributed
to A8 are **T10** (`sci 3.5, military 28, pop 3, cities 1`) and **T20** (`sci 4.5, pop 5, cities 2`),
both matching the agent's own diary rows, so the shared-diary attribution is separating A8 from the
attempts that wrote the same turn numbers.

**One early reading worth carrying**: A7's T10 was `military 34` and **A8's T10 is `military 28`** - six
down, which is within the range the barbarian fight at T5-T6 explains, and it is exactly the kind of
divergence that is not the variable and belongs in the record when the run ends.

## The record

*(to be written from the instrument's reads when the attempt reaches T110: the T10-T110 economy rows,
`F` and its two derived turns, the purchase or its absence, the third city's first four orders and what
it actually produced, the verdict on all four questions, and the divergences that are not the variable.)*
