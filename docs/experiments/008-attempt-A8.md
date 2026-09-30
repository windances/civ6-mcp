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

**A8 spans four sessions, and the final snapshot's `--run` must name all four** - this is the trap that
cut A7's own snapshot short, where a `--run` naming one session made the report start at that session's
first turn and call everything before it unattributed:

```
python scripts/experiment-report.py --game china_911679432 ^
  --run volcanic-ochre-catapult-47,tempered-jet-temple-30,silver-vermil-pennant-47,zealous-sepia-catapult-56 ^
  --questions a8 --save docs/experiments/A8-final.json
```

| session | turns | why it ended |
|---|---|---|
| `volcanic-ochre-catapult-47` | T1-T6 | stopped on the double T6 hang; recovered by a relaunch |
| `tempered-jet-temple-30` | T6-T77 | **its own context budget**, at T77, with the position clean |
| `silver-vermil-pennant-47` | T77-T107 | the game stalled on the World Congress result at T106 and then crashed to the main menu; recovered from `AutoSave_0107` |
| `zealous-sepia-catapult-56` | T107- | the continuation that carries the attempt to T110 |

`--questions a8` answers the four questions the claim is made of and `--save` writes the snapshot the
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

## T60: the deadline turns, and three of the four questions are decided

Read at T60, on the same command as before:

```
  FALSIFIED Q1 establishment complete by T60 (corrected table)
            [establishment not reached by T60; falsified when T60 passes with a role still short]
  HELD      Q2 three cities settled            [foundings beyond the capital: 2 of 2 (T20 at 63,25, T35 at 55,23); ...]
  HELD      Q3 the second siege unit in hand by T60, bought not built
            [deadline T60 (max(T58, F+25) with F=T35); bought: T59 UNIT_CATAPULT; built in a city: T53;
             the siege row reached 2 on T59; ...]
  OPEN      Q4 the gold clause - the floor at its own turn, and the T110 trio against A7's
            [gpt at T60 +12.0 against A7's 4.1; T110 not readable yet; ...]
```

**`Q1` is falsified and the table says exactly how far off it was.** At T60 the empire holds
`WARRIOR:3, SLINGER:2, CATAPULT:2, TRADER:1, SCOUT:1, BUILDER:1`, which fills `siege 2/2`,
`melee 3/2` and `recon 1/1` and leaves **`anticav 0/1`, `cavalry 0/1`, `ranged 2/4`** short. The reason
is the one this record named at T48 and revised at T55, and it is **not** the variable: the
establishment's producing city spent T31-T53 on a Campus, a Granary, a Trader and a Library while the
other two cities built a Hub each and a Market, and the siege gate itself opened when Engineering was
ordered at T45 against the baseline's T22. **The pin held** (`UNIT_SCOUT, UNIT_SLINGER, UNIT_SETTLER,
UNIT_BUILDER`) and **`Q2` held**, so the third city is not implicated in the falsification. `Q1`
measures A8's economy-first opening.

**`Q3` held, one turn inside its own deadline, and the shape of A8's plan is visible in the error it
produced.** `PURCHASED|UNIT_CATAPULT|cost=320g (had 446g)` at **T59** against a deadline of
**`max(T58, F+25) = T60`** with `F = T35` - and the first attempt at the purchase was **refused**:

```
  Error: STACKING_CONFLICT|Cannot purchase UNIT_CATAPULT - UNIT_CATAPULT (unit_id=851976)
  is on the city tile. Move it with unit_action(...) first, then retry.
```

The gun that blocked it was the one Xi'an had **built at T58**. So the plan "the war city produces the
first and buys the second" carries a cost no earlier attempt met: the bought unit cannot be placed
while the built one stands on the city centre, and the purchase is not a single call. The record keeps
the refusal, the move and the retry, because the claim's number is "the second siege unit is in hand
by the deadline" and *in hand* took three calls on the deadline minus one.

**And the instrument read that refusal as a second purchase** - it counted `purchase_item` rows by the
unit name in their parameters, and a refused call carries the same name as the one that works, so the
T59 line printed `bought: T59 UNIT_CATAPULT, T59 UNIT_CATAPULT`. `siege_purchases` now keys on the
game's own acknowledgement (`PURCHASED|`, the same style as `FOUNDED|`), with
`test_siege_purchases_counts_only_what_the_game_acknowledged` pinning the T59 pair, and the read above
is from after the fix. It is the second reader in this programme to mistake a refusal for the act.

**`Q4`'s floor clause is answered and its mechanism is not, and the difference is the whole point of
the clause.** The floor turn is T60 (`F = T35 > 28`), and `gpt` there is **+12.0 against A7's 4.1** -
above A7, and above the directive's own **+10**, which across the programme only A4 had ever exceeded
(and A4's came from Pingala's science, not a market). **But one turn is not a mechanism, and the record
will not credit the Market with it**: Beijing's Market finished at **T59** - the turn before the
reading - while Beijing's Commercial Hub landed T49, Xi'an's Trade Route opened from the T45 Trader,
and Xi'an's Library landed T49. A single turn cannot separate four things that landed inside it, and
A7's own curve reaches 24.4 by T80 **with no market at all**, which is the confound the task file
names in its own text. The floor clause is therefore **satisfied and unproven**, and `Q4` as a whole
stays OPEN on the T110 trio - the pair of numbers the two runs exist for.

**One more thing the log shows that the plan paid for**: Xi'an's Library was **pillaged at T54**, five
turns after it was built, and the `BUILDING_LIBRARY ... 1 turns` order at T59 is the **repair** that
finished the same turn it was placed. The log carries both lines and they read like a city building
the same unique building twice; they are the build and the repair, and the pillage is the price of
running four districts and five buildings' worth of queue on a five-unit army. Farms were pillaged at
T36/T37 and again at T60.

**Contact arrived late and the shape of the world is in the T60 snapshot**: the first rival met was
**Māori at T57**, 20% of the map is revealed, and the demography reads China **3 cities, Sci 22,
Mil 149, Gold +12** against Māori **4 cities, Sci 13, Mil 102, Gold +15**. So at T60 the empire is
ahead on science and soldiers, behind on cities and income, and **there is still no enemy city the
record can name as a target** - which is the other half of what `Q1` measures.

## T70: the like-for-like table, and the claim is live on all three measures

**The pipeline was verified before T110 rather than at it** - the retro's own lesson, since a fault found
at the verdict cannot be fixed. The command above, run while A8 had only its first two sessions,
resolved A8's economy rows at **T1, T10, T20, T30, T40, T50, T60, T70 and T73** - every ten-turn row the
claim needs, including the ones written while the two attempts shared the diary - so the final snapshot
will have its numbers once the third session id is added to `--run`. The same command run for A7's two
sessions reaches **T110**, and the two arrays put side by side are the comparison the claim is made of:

| turn | A8 science | A7 science | A8 `gpt` | A7 `gpt` | A8 pop | A7 pop | A8 districts | A7 districts |
|---|---|---|---|---|---|---|---|---|
| T40 | **7.7** | 6.3 | 5.3 | 6.1 | **9** | 8 | **1** | 0 |
| T50 | **20.0** | 14.4 | **13.6** | 8.1 | **12** | 10 | **3** | 0 |
| T60 | **22.5** | 15.7 | **12.0** | 4.1 | **16** | 14 | **4** | 1 |
| T70 | **21.1** | 19.4 | **13.0** | 2.1 | **17** | 14 | **4** | 2 |

**A8 leads on all three of the claim's measures at every turn they can be compared**, and the shape of
the lead is the interesting part. `gold_per_turn` is not close - **13.0 against 2.1 at T70** - which is
the market-and-library economy doing what the design note said a settled third city would do, and it is
the one column where the lead is *widening*. `pop` leads 17-14 and `districts` 4-2. **`science` is the
one that is narrowing**: A8 went **22.5 -> 21.1** across T60-T70 while A7 went **15.7 -> 19.4**, so the
same lead shrank from +6.8 to +1.7 in ten turns. The T80 row will say whether that is the pillaged
Library and the absence of a second Campus (A8 has one, with a Library) or the beginning of A7's Campus
run overtaking it.

**A7's own curve is the confound and it is now visible turn by turn**: from T70 A7 has 40 turns to reach
its T110 figures - **57.6 science, 25 pop, 60.0 `gpt`** - and it does that with **no market and no
wonder at all**. So A8's +12 at T70 is not the claim; the claim is the three numbers at T110, and the
record states the arithmetic it has to beat in advance: **science 57.6, pop 25.0, `gpt` 60.0.**

## T77: the first session hands over, and what it left in the log

**The session that played T6-T77 ended on its own context budget, not on the claim**: it reported at
T77 with the position clean (all units ordered, all queues set, the game auto-saved), and the
continuation is the same task file - 040's own `done when:` is T110 and its `expires:` is T115, and its
step 0 case 2 is written for exactly this ("is the position A8's own run in progress? ... continue from
where it stands, say which turn you picked it up on and what had already been spent, and do not load
anything").

**What it confirms, in its own words, and what it adds.** The start was **case 5**, not a fresh T1:
`get_game_status` found the game parked on China/Qin's leader intro, the diary and `hang_diagnosis.jsonl`
showed **A8 already in progress at T6** with two `HANG:6:0_MCP_0006` stalls, and the session recovered
it and continued rather than loading the shared start. That is the recovery this record already
carries, reported from the other side.

- **The site is a satellite, and the pre-flight was taken properly** - read at **T22 with two cities
  standing**, `Taiyuan (55,23)`, **score 215, fresh water, defence 2, five hexes from Xi'an**, the whole
  top ten in one cluster (x54-57 / y22-25). So the design note's fear of a fifteen-to-twenty-turn walk
  to a far colony is refuted on this map, exactly as its corrected section 3b predicted, and the third
  city's cost is its own production rather than distance.
- **The third city's four orders ran as written** - `BUILDING_MONUMENT` T35, `DISTRICT_COMMERCIAL_HUB`
  T48, `BUILDING_MARKET`, `UNIT_BUILDER` - and **the Market completed at T76**. The chain the design note
  set out for the third city exists in the log, in order, for the first time in the programme.
- **The purchase and the floor stand as recorded**, and the session flagged the same caveat this record
  did, independently: `PURCHASED|UNIT_CATAPULT|cost=320g (had 446g)` at **T59**, the floor **+12.0 at
  T60 against A7's 4.1**, and - its own words - the Market **did not** move that number, because it
  arrived at T76. Two independent readings of the same fact is the strongest form this caveat can take.
- **Its `gpt_T40` read is 5.0 where this record says 5.3.** The instrument reads the diary's per-10-turn
  row (5.3); the session was reading the live turn-start figure. Both are at or below A7's 6.1, which is
  the prediction, and the record keeps the instrument's number and names the other.
- **State at T77**: three cities, **pop 19**, **science 21.3**, **gold ~280 at +10-13/t**, **4 districts
  plus a Government Plaza**; the establishment reads **`siege 2/3`** (a third Catapult), **`melee 4/2`**,
  **`ranged 4/4`**, `cavalry 0/1`. So the empire is now **over strength in three rows** and short only
  the cavalry row - which is what `Q1` was about, ten turns after the deadline it missed.
- **Zhang Heng was recruited at T66** (Great Scientist, three free tech boosts) and **is still on the
  map unactivated** - the session's own handover lists it, and a record that leaves a Great Person idle
  is a yield left uncollected, so it goes in the open work.

**Two things outside the claim that the continuation must carry.**

1. **Contact became war-adjacent.** Māori were met at **T57**, and at **T64 a Māori Heavy Chariot
   damaged a Catapult to 40/100**; two AI diplomatic sessions arrived (Māori T66, Australia T71) and
   both were answered `POSITIVE`, which is not a peace offer and so is not the directive's refusal.
   **And Australia stands at `science 44.8`, `score 197` against China's 21.3 and 156** - the session
   named it as the standing risk. It is not this attempt's variable and it is the largest unknown
   beside the claim, because `Q4`'s T110 trio is a comparison against **A7**, not against a rival who is
   out-researching both runs.
2. **The open work it hands forward**, recorded so the continuation does not have to rediscover it: the
   **T80/T90/T100/T110 rows** (each naming `F = 35` and both deadlines) and the final report; an
   outstanding **envoy**; an unspent **governor title**; **Zhang Heng's activation**; the idle **trade
   routes**; and the **Builders** on unimproved tiles. **No wonder was built** - the file's override,
   accepted out loud in the diary the first turn it fired (T25).

## T90: the gold lead has reversed, and the T110 trio is stated before it lands

**The three-session `--run` is verified working** (`volcanic-ochre-catapult-47,
tempered-jet-temple-30,silver-vermil-pennant-47`), A8 resolves to **T1 -> T90 over ten rows**, and every
ten-turn row the claim needs is present. The arrays again, now with the two rows that decide the shape:

| turn | A8 science | A7 science | A8 `gpt` | A7 `gpt` | A8 pop | A7 pop | A8 districts | A7 districts |
|---|---|---|---|---|---|---|---|---|
| T70 | **21.1** | 19.4 | **13.0** | 2.1 | **17** | 14 | **4** | 2 |
| T80 | **31.3** | 29.4 | 8.8 | **24.4** | **20** | 18 | **6** | 5 |
| T90 | **45.2** | 37.1 | 21.9 | **49.0** | **22** | 20 | **7** | 6 |

**Two of the three measures still favour A8 and one has gone decisively the other way.**

- **`science` is winning and the lead is widening again**: A8's own line is **21.1 -> 31.3 -> 45.2**, a
  doubling in twenty turns, and it went from **+1.7 ahead at T70 to +8.1 ahead at T90**. Whatever the
  pillaged Library cost, the settled third city and its buildings have more than made it back on this
  measure.
- **`pop` is winning and holding**: **22 against 20**, with A8 ahead at every row since T40.
- **`gold_per_turn` has reversed, and it reversed hard.** A8 read **13.0 against 2.1 at T70** - the
  widest lead of the run - and then **8.8 against 24.4 at T80** and **21.9 against 49.0 at T90**. A7's
  gold roughly **doubles every ten turns** from T70 with **no market and no wonder** (2.1 -> 24.4 ->
  49.0), and A8's own market economy does not keep up.

**So the arithmetic the T110 verdict turns on, written down before the row exists**: A8 needs to beat
**`gpt` 60.0** at T110 and stands at **21.9 at T90** - it would have to nearly triple in ten turns,
while A7's own path is 49.0 -> 60.0. On the two rows measured, **A8's T110 `gpt` is very unlikely to
clear A7's**, and since the claim requires **all three** measures to exceed A7's, the shape of the
likely verdict is **`science` and `pop` won, `gold_per_turn` lost, `Q4` FALSIFIED** - a settled third
city that compounds in science and people and a captured one that compounds in gold. **If that is how
it lands, it is a result and not a failure**: it is the first measurement in the programme of what a
settled third city actually does to the three curves, and it says the design note's premise - a settled
city pays where a captured one does not - is **half right**, and the half it gets wrong is the one the
claim was named for.

**And the establishment finished the journey it missed the deadline on**: at **T90 the corrected table
is short only `cavalry 0/1`** - `siege 2/2`, `melee 3/2`, `ranged 5/4`, `anticav 1/1` (the T65
Spearman), `recon 1/1`. So `Q1`'s falsification is a **timing** verdict and not a capacity one: this
opening does build the whole table, thirty turns after the turn the attempt was judged on.

## T107: the game crashed to the main menu, and the Lua path recovered it

**The continuation played T77 -> T106 and then the game stopped taking turns.** The session's own
report is precise about where: the turn would not advance at **T106**, on
**`LOC_NOTIFICATION_WORLD_CONGRESS_RESULTS_MESSAGE`** after the World Congress had resolved, and every
documented remedy came back empty - `get_world_congress` twice, `dismiss_popup` ("No popups to
dismiss"), `get_pending_diplomacy`, `get_pending_trades`, `skip_remaining_units`, `get_notifications`,
repeated `end_turn`. That is the **third** distinct stall this programme has met and the second that no
Lua query can see, after A3's T70/T72 `PLEASE WAIT` stalls.

**The recovery did not go as documented.** `restart_and_load` relaunched the game (pid 5652 -> **24724**)
but left it at the **main menu with nothing loaded**, and both `load_game_save("AutoSave_0107")` and
`load_save_from_menu("AutoSave_0107")` answered `FAILED: Could not find 'Load Game' button`. The MCP's
own log shows why the menu route cannot work here:

```
  OCR: found 'Single Player' at (1759,1008) [99x17] - clicking (1759,1008)
  Click: screen=(1759,1008) abs=(15010,30583) vscreen=(0,0)+7680x2160
```

**`abs=(15010,30583)` is not a position on a 3840x2160 window** - the menu clicker's coordinate
translation is wrong at this resolution and DPI, so every menu click lands nowhere and the "Load Game"
button is never reached. The session also reported `.tools/whats-on-screen.py` and
`.tools/click-continue.py` as unusable for it (`ModuleNotFoundError: No module named 'win32gui'`),
which is true for its interpreter and **not** true for the orchestrator's - the same helper ran fine
from this side, which is how the screen was read at all.

**What recovered it was the Lua path with no menu clicks**, which is what `.tmp/lua-load.py` exists for
(its docstring: "the menu-driven recovery drives the game's UI with synthetic clicks. In this
environment those clicks never arrive"). Run as the orchestrator:

```
.venv\Scripts\python.exe .tmp\lua-load.py AutoSave_0107      # silent, ~5 min, then the leader intro
.venv\Scripts\python.exe .tools\click-continue.py            # report only: the CONTINUE box is below the OCR region
.venv\Scripts\python.exe .tools\click-text.py "CONTINUE" --at 1677,1406 --wait 10
```

The first call returned nothing for five minutes - **which is the documented signature of a load in
flight, not a failure** - and the third command's screen-after read is the proof it landed:
`NATURAL DISASTER OCCURRING`, `MAJOR FLOOD`, and the T107 HUD. **The position was never lost**: the
game's own autosave had it, and the crash cost wall-clock only.

**And the collision trap fired while identifying the save.** `AutoSave_0108` and `AutoSave_0109` exist
and are **older** than `0107` - `14:42` and `14:45` against A8's `18:26` - because **A7's continuation
played to T110 this afternoon and wrote autosaves at the same turn numbers**. A resume that picked "the
newest" by name instead of by time would load A7's branch. The saves that matter, with what they are:

| save | written | it is |
|---|---|---|
| `0_MCP_0105` | 18:22:58 | A8, T105, the newest MCP autosave |
| `AutoSave_0106` | 18:22:54 | A8, T106 |
| **`AutoSave_0107`** | **18:26:00** | **A8, T107 - the position recovered** |
| `AutoSave_0108` | **14:42:59** | **A7's continuation**, same turn number, three and a half hours older |
| `AutoSave_0109` | **14:45:10** | **A7's continuation** |

**What the crashed session had already measured at T106, and it changes the T110 forecast.** Its last
verified read, three turns short of the horizon:

| figure | A8 at T106 | A7's T110 bar | |
|---|---|---|---|
| `science` | **69.1** | 57.6 | above by 11.5 |
| `pop` | **27** | 25 | above by 2 |
| `gold_per_turn` | **+62.0** (income 88, maintenance -26) | 60.0 | above by 2.0 |

**All three of the claim's measures were already above A7's T110 figures at T106** - which is the
opposite of what the T90 row projected, and the record has to say why it moved. **The gold did not come
from the third city's Market.** The session named the lever itself: **two policy cards, Town Charters
and Merchant Confederation, worth about +24 gold/turn.** That is precisely the confound the task file
warned about in its own text - "A7 crosses the directive's +10 on its own, with no market at all ...
**if A8 is only ahead later, say the market did not do it**" - and here it is in the executor's own
words: the market did not do it. **Taiyuan's Market had arrived at T76 and the gold crossed the bar on
policy cards after that.** So the honest form of the likely `Q4` verdict is that the settled third city
**cleared the bar**, and that the mechanism the claim named is **not** what cleared it.

**One more reading the crash makes worth stating**: the three T110 figures at T106 are a read three
turns short of the turn the claim names. They are recorded here as the session's last verified numbers
and **not** as the T110 row - the row still has to be read at T110, which is what the continuation is
for.

## The record

**Attempt A8 is complete at T110. Three of its four questions are HELD and one is FALSIFIED**, and the
one that failed is the one this record predicted would fail, for the reason it predicted, ten turns
before the deadline it failed on.

```
  FALSIFIED Q1 establishment complete by T60 (corrected table)
  HELD      Q2 three cities settled - two foundings beyond the capital
  HELD      Q3 the second siege unit in hand by T60, bought not built
  HELD      Q4 the gold clause - the floor at its own turn, and the T110 trio against A7's
```

### The four answers

- **Q1 FALSIFIED.** At T60 the corrected establishment was short `anticav 0/1`, `cavalry 0/1` and
  `ranged 2/4`, against `siege 2/2`, `melee 3/2` and `recon 1/1` filled. **The reason is the attempt's
  own opening and not its variable**: the capital spent T31-T53 on a Campus, a Granary, a Trader and a
  Library while the other two cities built a Hub each, and the siege gate opened when `ENGINEERING` was
  ordered at **T45** against the baseline's T22. The pin held (`UNIT_SCOUT, UNIT_SLINGER,
  UNIT_SETTLER, UNIT_BUILDER`) and Q2 held, so the third city did not cause it. **And it is a timing
  verdict, not a capacity one**: by T90 the table was short only `cavalry 0/1`, and at T108 the empire
  stood at `siege 2, melee 3, anticav 1, ranged 6, cavalry 0, recon 1`.
- **Q2 HELD - the variable, delivered.** Two foundings beyond the capital: **T20 at (63,25)** and
  **T35 at (55,23)**, read from `found_city`'s own acknowledgements rather than from a city count. This
  is the first time in the programme that an attempt has held three cities **without taking one**; A3,
  A4 and A7 all reached three by conquest.
- **Q3 HELD, one turn inside its own deadline.** `PURCHASED|UNIT_CATAPULT|cost=320g (had 446g)` at
  **T59**, against a deadline of **`max(T58, F+25) = T60`** with **`F = 35`**; the first Catapult was
  ordered at T53 and **built** in Xi'an at T58, so A8's purchase column is the *second* gun where A6's
  320g bought its *first*. **The first purchase call was refused** - `STACKING_CONFLICT`, because the
  gun the capital had just built was standing on the city tile - so "in hand by the deadline" took a
  move, a retry and three calls.
- **Q4 HELD, with its mechanism explicitly disowned.** The floor turn was T60 (`F = 35 > 28`) and `gpt`
  there read **+12.0 against A7's 4.1**; at **T110** the trio read **`science` 60.9, `pop` 28,
  `gold_per_turn` +70.7 against A7's 57.6, 25 and 60.0** - all three above, which is the discriminating
  test the claim was cut to. **The two sources agree on that row**: the diary's T110 row reads
  `gold_per_turn 70.7` and the game's own T110 `get_game_overview`, read live, reads `+71.0` - and
  `A8-final.json` carries the diary's. **And the Market did not do it.** The session that played the end
  of the run named the lever itself: **two policy cards, Town Charters and Merchant Confederation, worth
  about +24 gold/turn.** Taiyuan's Market arrived at T76 and the gold crossed the bar after that, on
  cards. This is precisely the confound the task file wrote into its own text - *"if A8 is only ahead
  later, say the market did not do it"* - and the honest form of the verdict is that the **settled third
  city cleared the bar and the mechanism the claim named is not what cleared it.**

### The two runs, field by field

`A7-T110.json` and `A8-final.json`, the same columns at the same turns (A7's own T110 figures are
`science 57.6, pop 25, gold_per_turn 60.0`, with `districts 9` and `wonders 0`):

| turn | A8 science | A7 science | A8 `gpt` | A7 `gpt` | A8 pop | A7 pop | A8 districts | A7 districts |
|---|---|---|---|---|---|---|---|---|
| T40 | **7.7** | 6.3 | 5.3 | 6.1 | **9** | 8 | **1** | 0 |
| T50 | **20.0** | 14.4 | **13.6** | 8.1 | **12** | 10 | **3** | 0 |
| T60 | **22.5** | 15.7 | **12.0** | 4.1 | **16** | 14 | **4** | 1 |
| T70 | **21.1** | 19.4 | **13.0** | 2.1 | **17** | 14 | **4** | 2 |
| T80 | **31.3** | 29.4 | 8.8 | **24.4** | **20** | 18 | **6** | 5 |
| T90 | **45.2** | 37.1 | 21.9 | **49.0** | **22** | 20 | **7** | 6 |
| T100 | **56.0** | 52.1 | 45.8 | **49.3** | **26** | 22 | 8 | **9** |
| **T110** | **60.9** | 57.6 | **70.7** | 60.0 | **28** | 25 | 8 | **9** |

**What the table says, and it is not a victory lap.** A8 leads the science and population columns at
**every** row from T40 on - the settled city compounds in people and in research, and it does so
early: +3.3 science and +3 pop at the horizon, with the lead on science having been as wide as +8.1 at
T90. **The gold column is a different story and it is the interesting one**: A8 led it at T50-T70
(+13.6/+12.0/+13.0 against 8.1/4.1/2.1), **lost it for thirty turns** (8.8 vs 24.4, 21.9 vs 49.0, 45.8
vs 49.3) and won it back only at the horizon (+70.7 vs 60.0). **A7's war-and-Campus economy out-earns
a settled city's market economy for the middle third of the run**, and what closes the gap in the last
ten turns is **policy cards, not buildings**. Districts finish **8 against A7's 9** - the captured city
came with its own.

### What the attempt cost and what it bought

- **981 tool calls over 108 turns (9.1/turn)**, across **four sessions**; the run's own tooling cost
  included a double hang at T6, a World-Congress stall at T106 and a crash to the main menu that was
  recovered from `AutoSave_0107`.
- `dynasty-cycle-wonder` fired **100 turns** by the file's own count: the empire built **zero
  wonders**, which was the task file's deliberate, accepted override, and the record says again that
  the wonder is **owed its own attempt**.
- **The pin held** (`UNIT_SCOUT T1, UNIT_SLINGER T5, UNIT_SETTLER T10, UNIT_BUILDER T18`), `H5` is
  clean (no ram, no tower), and the self-report has no `ESTABLISHMENT` line - the diary never printed
  the table it is asked for every ten turns, which is a reporting gap this attempt carries.
- **The third city's four orders ran as written** - `BUILDING_MONUMENT` T35 -> `DISTRICT_COMMERCIAL_HUB`
  T48 -> `BUILDING_MARKET` (complete T76) -> `UNIT_BUILDER` - for the first time in the programme.
- **The raids were the price of the queue.** Xi'an's Library was **pillaged at T54**, five turns after
  it finished, and repaired at T59; farms were pillaged at T36/T37 and T60; `carrying-capacity` read
  red at the T59 review (`gold/turn +8.0 with military 272`).
- **The empire changed shape twice**, both recorded in the diary: **Māori declared war at T87** (still
  open at T106, no city exchanged) and **defensive walls were bought** in Beijing (T87) and Taiyuan
  (T99). Neither is the variable and both are real costs the third-city plan did not budget.

### The divergences that are not the variable, in one place

Six were recorded as they happened and all six stand: the **research path is economy-first**
(`THE_WHEEL` T41 against every other attempt's T8, `ENGINEERING` T45 against about T22, so the siege
gate opened 23 turns late); the empire's **first Market went into city #2** at T50 rather than the
third city; the **pantheon is Fertility Rites T29** where A5-A7 took God of the Forge (`+25%` Ancient
and Classical military production forfeited, so A8's Catapults cost 25% more); Xi'an's **Campus came at
T31** where A7's came about T64; **`military` at T10 is 28 against A7's 34**; and the **third city is
a satellite** - `Taiyuan (55,23)`, score 215, fresh water, five hexes from Xi'an - which refutes the
far-colony cost the design note feared.

### What A8 leaves behind

1. **The settled third city is real and measurable**: three cities held without a conquest, a market
   chain executed in order, and a horizon lead on **science (+3.3) and population (+3)** against a
   baseline that took its third city by war.
2. **The claim's gold mechanism is not established.** The bar was cleared by policy cards; the
   market's own contribution is not separated from the Hub, the Library, the Traders, Pingala and the
   Caravansaries that landed around it. **A market-first claim needs an attempt that holds the cards
   constant**, which is the honest successor to this one.
3. **The establishment question was decided by the opening, not by the variable**, and the programme
   still pins only the first four builds: A8 is the second attempt in a row whose headline question was
   settled by a divergence no task file pinned. The fix is in `README.md` section 3 - **pin the first
   research choices and the queue after the pin**, not only the opening four units.
4. **A9 (four cities) has its answer for the settlement half and not for the gold half**: section 10 of
   `drafts/A8-A9-city-count.md` carries the arithmetic, and whether it runs is the human's call.

