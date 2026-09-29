# Attempt A4 - the Encampment before the second siege unit

**Status: COMPLETE** - **one session** (`molten-sage-compass-31`), played from the experiment's
shared start `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` and finished at **T66**, when the keeper
read three cities and the third was the target city-state. **The variable was executed and every
half of it held**: the Encampment was bought a tile for (35 gold) at T27, ordered the same turn and
complete at **T32** - before any siege unit existed at all - the first siege order followed the
Engineering gate on **T43**, the same turn the tech was owned, the district's own points produced a
Great General who was recruited at **T56** and never activated, and **a city was kept at T65**, two
turns inside A3's T67. The establishment was complete at T54, six turns inside the T60 deadline, and
the instrument reads `HELD` for Q1, Q3 and Q4. **No rival major civilisation was ever met** - the map
was 20% explored at the keep - so every number below is against city-states, as in A2 and A3. The
attempt's instruction is
`prompts/tasks/tmp/035-attempt-a4-the-encampment-before-the-second-siege-unit.md`; the design is
section 3 of `docs/experiments/README.md`; A3's record is `003-attempt-A3.md` and its snapshot is
`docs/experiments/A3-final.json`; the cross-attempt report is `RETRO-2026-09-29.md`. This file is A4's
record. **A4 is the first attempt in the programme to build an Encampment at all**: A1, A2 and A3 built
none, and across all seven session logs of this match - `vigilant-sable-longbow-78`,
`sacred-garnet-vault-35`, `pale-pearl-aqueduct-92`, `volcanic-indigo-caravan-23`,
`flint-indigo-rampart-32`, `crumbling-emerald-parapet-16` and `eternal-scarlet-catapult-86` - there are
**zero** `DISTRICT_ENCAMPMENT` orders.

## Settings: the shared start, one variable

| | A3 | A4 |
|---|---|---|
| start | the experiment's shared T1 start, `ATTEMPT-A1-T1-settled.Civ6Save` | **the same save**, loaded at T1 - no rollback branch, and `molten-sage-compass-31` is the only session so far |
| doctrine | the **corrected** `tactics/01` (recon 1, anti-cavalry 1, the ram conditional, siege 2 / melee 2 / ranged 4 / cavalry 1) | the **same corrected table**, held |
| the one variable | the target's defences - a city whose wall pool reads above zero | **the Encampment is built, in the war city, before the second siege unit completes** - `tactics/08`'s reading of the doctrine executed for the first time in the programme |
| window | a walled city kept, or **T110** | a city kept, or **T110** (`expires:` T115) - and the capture is read against **A3's keep turn, T67** |

**A4 differs from A3 in its variable and in its research line.** Where A1, A2 and A3 went
`TECH_MINING` -> `TECH_THE_WHEEL` -> `TECH_ENGINEERING`, A4 starts `TECH_MINING` T1 and sets
**`TECH_BRONZE_WORKING` T8** - Bronze Working is the Encampment's prerequisite, so the research line
follows the variable rather than holding it. That is a second thing that moved, and the record says so
for the same reason A3 named its own divergences: a later capture turn is compared against A3's T67 with
both the district and the tech line in hand.

**One line of the brief is stale and this record does not follow it.** The task file's `scope:` header
(its line 14-15) still carries the dead premise's phrase - the Encampment's place "after the second
city, where A3 builds it before" - which the same file refutes in its own design section ("Why the old
premise died", lines 38-45): **no attempt has built an Encampment at all**, so "before the second city"
is an arm that does not exist. The record follows the brief's body, "The one variable" (line 30) and
lines 38-45, and README section 3's paragraph "A4's premise was false" - the variable is the Encampment
**before the second siege unit**, in the war city.

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, order by order. The variable is the Encampment's place
in the war city's queue, not the opening, so the pin is the condition the attempt's numbers are
comparable under.

| order | promised | the record |
|---|---|---|
| 1 | `UNIT_SCOUT` | **T1 - matched.** The attempt's first production order, `set_city_production(city_id=65536, UNIT_SCOUT)` |
| 2 | `UNIT_SLINGER` | **T5 - matched.** `PRODUCING\|UNIT_SLINGER\|5 turns`, placed the turn the Scout completed |
| 3 | `UNIT_SETTLER` | **not yet placed at T8** - the log holds two production orders and the Slinger is still building |
| 4 | `UNIT_BUILDER` | **not yet placed at T8** |

**The consequence of a deviation is a re-run, not an explanation** (the brief's own rule): if the first
four orders are not those four in that order, the record states the deviating order and its turn and the
attempt **is not comparable** with A5-A7 - it is re-run from the shared start, and the record says which
session is discarded and where the re-run begins. A doctrine reason does not buy an exemption, and
**A3's measured case is why the rule is written that way**: A3's fourth order was `UNIT_WARRIOR` at
**T15**, with the pin published at 20:23:19 and in force, and its `planning` line never mentioned the
pin - the deviation had a doctrine reason and still broke comparability, so the pin now carries a
mechanical sink rather than a request for an explanation (the section below has it).

## The hypothesis, with the numbers that falsify it

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | T60 passes with the composition short in any required role |
| Q2 | **the Encampment is completed in the war city before the second siege unit completes**; the record carries the district's tile, the turn it was ordered, the turn it completed, and the turn the game first offered it (`get_district_advisor` / `get_city_production`, with whatever prerequisite that read names - the tech requirement is read, never asserted here) | the window ends with no `DISTRICT_ENCAMPMENT` completed, or it completes after the second `UNIT_CATAPULT` - an aura that arrives after the train cannot be the thing that changed the assault |
| Q3 | **a Great General is recruited before the war opens, and it is never activated**; the record carries the turn it was recruited and where it stands relative to the siege units | no general is recruited before the first war declaration, or `activate` is called on one. An Encampment that yields no general by the first shot is the claim's **mechanism missing**, not its cost, and activating a general **retires the aura** (`AGENTS.md`: the aura is worth having while the unit is alive, and `activate` consumes it) - if one is activated, the record says so plainly |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns**, **both measures reported**, and the capture read against **A3's keep turn** in `003-attempt-A3.md` | the rule reads red ten or more times, or the diary's own `gold_per_turn` is not below the +10 floor (both are reported, as A1, A2 and A3 did); the capture half is falsified when **A3's keep turn, T67**, passes with no `KEEP\|` in this attempt's log - A3 kept 耶路撒冷 at T67, so the brief's **T80** bound applies only if A3 had kept nothing and it does not apply here |

## The decisive numbers, measured by the instrument

1. **the establishment turn** (every turn is scanned), under the corrected table;
2. **the Encampment**: the turn the game first offered the district, the turn it was ordered, the turn
   it completed, and the tile it stands on - read from the log's `set_city_production` rows naming
   `DISTRICT_ENCAMPMENT`, with the offer read from `get_district_advisor` / `get_city_production` and
   the prerequisite that read names;
3. **the Great General**: the turn it was recruited, from `get_great_people` and the unit read, and
   whether `activate` was ever called on it;
4. **the first city kept**, from the `KEEP|` reply, read against A3's T67;
5. **the turns under the gold floor**, both measures.

`--questions a3` is the instrument-read half - its Q2 reads the wall pool, its Q3 the first keep and its
Q4 the gold floor - while this attempt's Q2 and Q3 are **record-read**: the Encampment from the log's
`DISTRICT_ENCAMPMENT` rows, and the general from `get_great_people` and the unit read.

**The pin block prints its state in every report and every snapshot, so no attempt's opening can be
glossed in prose again.** It reads `DEVIATED` when an order breaks the pin and names the order and its
turn (`opening order 4 was UNIT_WARRIOR on T15, not UNIT_BUILDER - the pin did not hold`, which is A3's
line), `held` when all four orders match, and **`undecided` while fewer than four are placed** - which
is A4's own state at T8: two of four, and a two-order log is not a match the record can claim.

Commands, with **this attempt's one session** in the log filter - the list grows when a session dies or
is restarted, and a missing id silently drops the rows after it (A3 needed four):

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run molten-sage-compass-31 --from 1 --to 110 --verdict --questions a3
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run molten-sage-compass-31 --from 1 --to 110 --step 10 --verdict --questions a3 --save docs/experiments/A4-final.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs\experiments\A1-T40.json docs\experiments\A2-final.json docs\experiments\A3-final.json docs\experiments\A4-final.json
```

## Mid-window review - filled as the attempt passes T20 / T40 / T60

Read at **T8**, which is the attempt's first reporting point rather than a scheduled checkpoint, so most
rows were honestly empty; **the table is re-read at T46 further down this section, once the variable had
been executed and the gate had passed**, and that later table is the one to read.

| question | answer at T8 |
|---|---|
| the opening build, against the pin | **two of four matched**: `UNIT_SCOUT` T1 and `UNIT_SLINGER` T5. The third and fourth orders (`SETTLER`, `BUILDER`) **had not been placed by T8**, so the instrument reads the pin `undecided` - not matched - and this row moves only when the next two orders land |
| the research line (this attempt's own divergence) | `TECH_MINING` T1, **`TECH_BRONZE_WORKING` T8** - the Encampment's prerequisite, and the reason A4's research differs from A1-A3's The Wheel -> Engineering |
| production orders, all of them | `SCOUT` T1, `SLINGER` T5 - two of the pinned four; nothing else had been placed by T8 |

**The pin held, and the Encampment's first obstacle is placement rather than production** (both read from the
session's own log at T22, and both are the measurements this row exists for):

- **`PIN opening: held`** - the instrument's own line, once all four orders existed:
  `UNIT_SCOUT, UNIT_SLINGER, UNIT_SETTLER, UNIT_BUILDER in that order` (`SCOUT` T1, `SLINGER` T5, `SETTLER`
  T10, `BUILDER` T18). **This is the first attempt in the programme whose pinned opening the instrument
  certifies**, which is what makes A4 a clean baseline for A5-A7 - A3's reads `DEVIATED` and A1/A2 were played
  before the pin existed. The one divergence to keep beside it is a timing one: `SETTLER` was ordered at
  **T10** where A1, A2 and A3 all ordered theirs at **T6**, so every downstream turn in this attempt sits
  four turns later than theirs.
- **`get_district_advisor(city_id=65536, DISTRICT_ENCAMPMENT)` -> `No valid placement tiles for
  DISTRICT_ENCAMPMENT.`**, and the same for the second city (`city_id=131073`) called on the same turn it was
  founded (`FOUNDED|55,21`, T22). So at T22 **neither city can host the Encampment**: the district may not
  touch the city centre and has to stand on a tile the city owns, and the capital's ring does not offer one
  yet. **The variable's cost begins as a placement problem, not a production one** - and the doctrine has no
  fallback written for it (`tactics/08` says the war city builds the Encampment, and says nothing about what
  to do when the war city cannot). The attempt has to solve it with border expansion, a tile purchase or the
  second city's own ring; which of those it does, and what it costs, belongs on this row as it happens.

**And it happened at T27 - the variable's cost is measured, and it is not only production.** The session
**bought a tile**: `purchase_tile(58,22)` answered `TILE_PURCHASED|(58,22)|cost:35`, the same turn's
`get_district_advisor(DISTRICT_ENCAMPMENT)` then offered exactly **1 tile**, and the district was ordered in
the capital the same turn:

```
T27 set_city_production(city_id=65536, DISTRICT_ENCAMPMENT) -> PRODUCING|DISTRICT_ENCAMPMENT|5 turns
```

So **A4 pays 35 gold and five turns of the capital's production for its variable**, and the gold half is the
half the doctrine never mentions: `tactics/08` says the war city builds the Encampment and is silent about the
ring it may not be able to build it on. **The ordering the attempt was built to test is still to come** -
Engineering was set at **T31**, so the Encampment (due about **T32**) will be standing well before any second
siege unit exists, and the question is whether that is worth what it cost. The record will carry the completion
turn, the first and second siege-unit orders, and the Great General beside it.

**And the completion is measured: `T31`.** The log's own line is
`>> Xi'an finished building DISTRICT_ENCAMPMENT. Now: nothing.` - ordered at T27, complete at **T31**, four
turns of the capital's production plus the 35 gold the placement fix cost. **So the ordering A4 was built to
test is satisfied well inside the window: the Encampment exists before any siege unit does.** What is already
visible beside it is the price, and it is not only those 35 gold: **Engineering read 11% and 25 turns at T34**,
where A3's landed at T43 and A2's at T48 - the research line went through Bronze Working for the district, and
the capital then spent T27-T31 on the district and T33 on its Barracks. Whether the general's aura repays that
is what Q2-Q4 are for, and the first hard number is unfavourable: **the siege train cannot exist before about
T59 unless something changes.**

Two more facts this attempt has produced, and the row keeps them:

**The gate is now measured from both sides, and the two readings only disagreed because of a one-turn
offset the record had wrong.** A4's log carries the whole research line as `Research complete` lines -
**Mining T7, Bronze Working T21, The Wheel T30, Masonry T38, Engineering T42** - and the diary lists the
same techs **one turn later** (Mining T8, Bronze Working T22, Masonry T39, **Engineering T43**). **That
offset is the diary's definition, not a disagreement**: a `Research complete` line is reported inside the
`end_turn` *called on* T42, so the tech is **owned from T43** - and the proof is operational, because
`T43 set_city_production(city_id=65536, UNIT_CATAPULT) -> PRODUCING|UNIT_CATAPULT|5 turns` could not have
been accepted otherwise. The same +1 applies down the line: **Engineering was owned at T43**, Mining T8,
Bronze Working T22, The Wheel T31, Masonry T39.

**Three facts in the earlier version of this paragraph were wrong and are corrected here**, because the
gate's turn is what the attempt is compared on:

- **"the last economy order before the gate was the Barracks at T33" is false.** The full order list from
  A4's log (T1 `SCOUT`, T5 `SLINGER`, T10 `SETTLER`, T18 `BUILDER`, T22 `WARRIOR`, T22 `SLINGER`,
  T24 `SLINGER`, T25 `SPEARMAN`, T26 `SLINGER`, **T27 `DISTRICT_ENCAMPMENT`**, T30 `TRADER`,
  T32 `SPEARMAN`, T33 `BARRACKS`, **T35 `MONUMENT`**, **T39 `WALLS`**, T42 `HEAVY_CHARIOT`,
  **T43 `CATAPULT`**, T46 `BUILDER`) puts **`BUILDING_WALLS` at T39** after the Barracks and before the
  gate. The instrument's gate check counts **only `BUILDING`/`DISTRICT` orders placed *since* Engineering**
  (`experiment-report.py:710-717`), and there are none - so the check was never about the Barracks, and
  citing a pre-gate order was beside the point as well as wrong.
- **"Engineering T42" conflates the reporting turn with the owning turn** - see the offset above.
- **The instrument does not fail to see the gate.** The earlier paragraph recorded
  `Engineering has not landed by T42`; re-running it once the attempt had passed T43 answers
  **`HELD  Q2 the siege train ordered before any economy order after Engineering  [Engineering T43; first
  siege order T43, no economy order since]`**, reading A4's *attributed* diary rows. The earlier reading was
  a window artefact (the run then ended at T42), not the shared-diary collision the paragraph blamed, and
  it is corrected rather than left standing.

**So H1's ordering holds for A4 on the record and in the instrument: the siege was asked for first, on the
turn the tech was owned, and no building or district order has followed it.** The shared-diary caveat still
stands for *other* fields - the pid-0 rows at T22 carry another attempt's `TECH_THE_WHEEL`, and the T43-T46
rows interleave attempts - which is why every A4 number in this record that the diary also holds is cited
with its source.

- **`get_great_people` at T32**: `Great General: Trung Trac (Classical Era) - Unclaimed - your points: 0/40`.
  The mechanism Q3 asks about is live and **not yet earned**: the Encampment is standing and has produced no
  general points of its own. What it produced instead is the *offer* of its own project
  (`PROJECT_ENHANCE_DISTRICT_ENCAMPMENT`, cost 25, 3 turns, T33) - which is the lever that would have to be
  pulled for a general to arrive before the war.
- **An Encampment is a queue item again, not a one-off cost**: T33 `BUILDING_BARRACKS` in the capital is the
  Encampment's own building, and it competes with the army for the same city's turns - `tactics/08` lists
  "the Encampment/Barracks" together and prices neither.
**The self-report check fired on this attempt, and the cause is a convention the brief never stated.**
The instrument prints the diary's own `ESTABLISHMENT:` line beside its computation, and **from T43 to T48 -
six turns, the whole span in which the first Catapult was in production - A4's line read
`siege 1/2 (Catapult 1 due ~T48)` while the map held **0** siege units**, so each of those turns is scored
`MISMATCH - siege claimed 1 vs 0 held`. **The session's parenthetical says the unit is still in production**
(T43 read `siege 1/2 building (due ~T48)`), and **the line self-corrected at T49**, the turn the unit existed,
becoming `siege 1/2 (Catapult 2 ~T54)` - which is the convention the instrument wants, with the numerator
counting what is held and the pending unit named in words. **So the defect is bounded and the session found
the right shape on its own; what it needed was the definition, and A3 wrote the same wrong shape on its own
T43** (`siege 1/2 building (due ~T48)`), so this is a brief-level ambiguity two attempts fell into rather
than one session's error. The correction lands on the brief, where it reaches A5-A7 (see the retro's ledger);
**the check itself is unchanged, because a numerator that counts a unit in production is exactly the
over-claim it exists to catch.** The record's own establishment number is the instrument's: **`
COMPLETE at T54`**.

| question | answer at T46 |
|---|---|
| the establishment under the corrected table (Q1 wants <= T60) | **not complete at T46** - `siege 0/2` (the Catapult ordered T43, 5 turns, due ~T48) and `cavalry 0/1` by the map at T45, though the `UNIT_HEAVY_CHARIOT` ordered T42 **completed at T45**; screens (melee + anti-cavalry) 3, ranged 4, recon 1. The instrument: `NOT complete at T45 short: cavalry 0/1 siege 0/2` |
| the Encampment (Q2): offered, ordered, completed, and its tile | **offered T27, ordered T27, complete T31, on (58,22)** - the tile the attempt bought for `cost:35` the same turn, in the capital (the war city by `tactics/08:81`'s highest-production rule). **It completed before any siege unit existed**, so the ordering Q2 tests is satisfied; the cost is 35 gold + four capital turns (T27-T31) + the Barracks it then built (T33, complete T38) |
| the Great General (Q3): recruited, never activated, and where it stands | **not recruited** - `get_great_people` at T32 reads `Trung Trac - Unclaimed - your points: 0/40`, and at T39 `7/40`. The Encampment has earned points of its own (7 by T39) but no general exists and **no `activate` has been called on one**. The lever is the district's own project, offered at T33 (`PROJECT_ENHANCE_DISTRICT_ENCAMPMENT`, cost 25, 3 turns) and **never ordered** |
| the order of asking at the gate (H1's test, Engineering -> first siege order) | **HELD** - Engineering owned **T43**, `UNIT_CATAPULT` ordered **T43**, no `BUILDING`/`DISTRICT` order since. The instrument agrees: `HELD ... [Engineering T43; first siege order T43, no economy order since]` |
| the first keep, against A3's T67 (Q4's capture half) | **not yet measured** - no `KEEP|`, and **no rival met at 16% explored**, so the target is still a city-state |
| the gold floor, both measures (Q4 allows < 10 red turns) | **the two measures still disagree, and both are reported**: `0 red turn(s) by the rule up to T60`, while `the diary's own gold/turn is below 10 on 42 of those 46 turn(s)`. The rule's horizon is the establishment turn, so the diary measure is the one that will decide Q4 once the army is paid for |
| the economy at T20 / T40 / T60 against A1's, A2's and A3's | **partly measured** - `T35 BUILDING_MONUMENT`, `T39 BUILDING_WALLS` (complete T42) and `T42 UNIT_HEAVY_CHARIOT` are the orders between the Barracks and the gate, and the capital spent T27-T31 on the district: the research line paid Bronze Working (T22) for the district and Engineering arrived at T43 where A3's landed at T43 and A2's at T48 |
| the verdict so far on Q1-Q4 | **Q2 satisfied, Q4's rule half green and its diary half red, Q1 and Q3 open** - the instrument prints `HELD` for the gate question and `OPEN` for Q1/Q3/Q4 as the deadlines have not arrived |

**Re-read at T54, and the variable is now decisive rather than merely satisfied.** The earlier note in this
record predicted "the siege train cannot exist before about T59 unless something changes"; **it was wrong, and
the attempt's own log says so**: the first Catapult was ordered T43 (5 turns) and finished inside **T48's**
`end_turn`, and the **second was ordered at T49** in the war city (`set_city_production(city_id=65536,
UNIT_CATAPULT) -> PRODUCING|UNIT_CATAPULT|5 turns`) and finished inside **T53's**. With the one-turn offset
above, the train is **owned from T49 and T54**. So:

- **Q2's ordering is not a near thing: the Encampment completed at T31 and the second siege unit was ordered
  at T49 - eighteen turns apart.** The district cannot have been a consequence of the train, and the train did
  not have to wait on the district. That is exactly what Q2 asked.
- **The first economy order after the gate landed at T53**, and it is a `BUILDING_GRANARY` in **Changsha** (the
  second city, `city_id=131073`) - **ten turns after the gate** (T43 -> T53) and after the second Catapult had
  been ordered. The instrument states both halves on one line: `HELD ... [Engineering T43; first siege order
  T43, first economy order T53]`. **The shape is A2's** - A2's first post-gate order was also a Granary in its
  second city, at T55 - which is the comparison A5's Q3 is built on.
- **The establishment is complete at T54.** At T53 the instrument reads `NOT complete at T53  short: siege
  1/2` with every other row satisfied (`cavalry` first owned T46, `anticav` T33, `recon` T5, ranged 4/4,
  screens 3), and the second Catapult is owned from T54 - so **Q1 is met at T54, one turn after A3's T53 and
  six turns inside the T60 deadline**, subject only to the T54 diary row confirming it. `PIN opening: held`
  still stands.

**One order in this window belongs on the doctrine's own ledger and is recorded rather than glossed.** T54
`set_city_production(city_id=65536, BUILDING_GRANARY)` is an **economy order in the war city** - the city
`tactics/08:81` says builds "units, siege and the Encampment/Barracks, and nothing else for the duration". The
war has not opened, the establishment is complete and the district is standing, so no army is being starved of
turns; but it is the first economy order in the war city after the gate, and the rule that the war city stays
military is a claim A4 can now be measured against instead of assumed.

**And the mechanism Q3 asked about is still missing at the moment the train completes.** The last
`get_great_people` read in the log is **T39, reading `7/40`** (the T32 read was `0/40`), and **no
`PROJECT_ENHANCE_DISTRICT_ENCAMPMENT` order exists** - so the Encampment has earned seven points in eight
turns and no general. With the second Catapult owned from T54 and no war declared, the district is standing
while its presumed payoff is not, which is precisely the case the brief's honesty note says to state plainly:
**the Encampment's cost is measured (35 gold, four capital turns, a research line through Bronze Working) and
its benefit is, so far, zero - the record will not read an unchanged capture turn as the district paying off.**

**And A4 supplies the sharpest measurement yet of a tooling defect the retro carried as owed.** The pantheon
guard compares faith against the **standard-speed** `RELIGION_PANTHEON_MIN_FAITH` (**25**,
`Base/Assets/Gameplay/Data/GlobalParameters.xml:475`) while this match runs **Quick**, where the
`GAMESPEED_QUICK` row's `CostMultiplier` is **67** (25 x 0.67 = 16.75). **A4's own log shows the guard
refusing a pantheon the game had already offered**: at **T19** the game's own end-turn block carried
`* Choose Pantheon` (the `ENDTURN_BLOCKING_PANTHEON` / `NOTIFICATION_CHOOSE_PANTHEON` signal), the T20 read
answered `No pantheon selected. Faith: 23`, and the same turn's `choose_pantheon` answered **`faith 23 < 25`**
- a refusal against a pantheon the game was already offering. A3's session was offered at **T22** with
`Faith: 13` at T21 and refused at T23 on `faith 17`. **The record's own conclusion is that the guard should
key on the game's own blocker rather than on a second copy of the constant**, which is speed-proof; the edit
is deliberately **not** made while this attempt holds FireTuner, for the reason the retro gives, and it is
staged for the A4/A5 boundary.

**Re-read at T60, and two of the four questions are now decided - including the one the Encampment was built
to answer.**

- **Q1 is MET, and the instrument reads it from A4's own attributed rows: `COMPLETE at T54  siege=2 melee=2
  anticav=1 ranged=4 cavalry=1 recon=1`** - one turn after A3's T53 and six turns inside the T60 deadline.
  The T54 block above hedged this ("complete at T54, subject only to the diary row confirming it"); the
  instrument confirms it, so the hedge is discharged rather than amended.
- **Q3's mechanism exists, and this is the first time in the programme that it does.** The Encampment's own
  points ran **0/40 at T32 -> 7/40 at T39 -> 41/40 at T56**, and at **T56** the log reads
  `get_great_people ... Great General: Trung Trac (Classical Era) - China - your points: 41/40 [CAN RECRUIT]`,
  followed the same turn by **`recruit_great_person -> OK:RECRUITED|Trung Trac`**. **No `activate` call exists
  anywhere in this session's log** (checked against every `unit_action` row), and at T60 the general stands at
  **(55,22) with the stack**, inside the aura's 2-tile reach of the siege train - **and no war has been
  declared**, so a general was recruited before the first declaration and never activated: Q3's condition, met
  on both halves. **The `PROJECT_ENHANCE_DISTRICT_ENCAMPMENT` lever was never pulled** - the points are the
  district's own, which is the cheaper half of the mechanism the brief left open.
- **The earlier note that the district's "benefit is, so far, zero" is therefore superseded on the mechanism
  half.** What stays unmeasured is whether the aura changes the arithmetic of the capture: the general exists,
  is unactivated and is in position, and no shot has been fired.
- **At T60 the army is 14 units and staged** - 2 Catapults at (52,24) and (53,21), 2 Warriors, a Spearman at
  (49,25), 3 Archers and a Slinger, the Heavy Chariot and the general; the only hostiles are the barbarians
  around (53,23)-(61,24); **no rival civilisation has been met** and no war is on. The attempt has to T110,
  and A3's T67 bound, to turn the train into a keep.

**And a measurement that decides how the aura may be judged: the combat estimate the session uses does not
contain the general.** `build_combat_estimate_query`'s own docstring lists its inputs - "base CS,
promotions, fortification, terrain (hills, forest/jungle), river crossing, flanking bonus, and support
bonus" (`src/civ_mcp/lua/units.py:668-673`) - and **neither a Great General's aura nor the government's
combat bonus is among them**; the modifier construction in that function carries no general and no
government term at all (checked through `effAttCS = effAttCS + attModTotal`). **A4's own T60 measures what
that costs**: `Warrior id 131073 at (53,22)` - **two tiles from our own general at (55,22), inside the
aura** - is estimated at **`CS:24` with `Modifiers: flank +4`**, i.e. base 20 plus flanking only, where the
engine would also be applying **Oligarchy's +4** (the government has been Oligarchy since T43) and the
**aura's +5**. So during A4's assault every estimate will understate our own attack, and **the aura cannot
be shown to be working, or not working, by the estimate at all** - which matters because Q3 asks whether it
changes the capture. The record therefore will not read a capture turn from the estimate as evidence about
the district: the estimate is a floor, and the engine's own resolution is the fact. The tool fix (query the
engine's `CombatManager.SimulateAttackVersus`, which `units.py:866` already cites as the authority for
flanking) is **not** made while this attempt holds FireTuner, for the same reason as the pantheon guard.

## The end table, and the verdict

**The attempt's finish line was met at T65 - a city was kept - and the record must state how that was
observed, because it was not the shape the brief named.** The melee unit's move answered
`CAPTURE_MOVE|50,22|from:49,23|now_at:50,22|(moved dx:+1 dy:-1)|CITY TAKEN - resolve keep/raze with
city_action`, and then **four** `resolve_city_capture(action="keep")` calls (two at T65, two at T66) each
answered **`Error: NO_PENDING_CITY|No rebelled or captured city pending decision`** - because the game had
**already resolved the capture itself and left nothing to decide**. That no `KEEP|` exists is therefore not
a failed keep: the T66 `get_cities` read **three cities**, including `Jerusalem (pop 6) at (50,22) ...
[id:196610]` with its districts and buildings, and `set_city_production(city_id=196610,
BUILDING_MONUMENT)` was accepted the same turn. **So the keep is A4's, and the evidence is the move's own
line plus the city list.** The instrument had to be taught this shape: `captures()` matched only
`KEEP|`/`RAZE|` and scored A4 as having kept nothing until `CAPTURE_MOVE ... CITY TAKEN` was added to it
(`scripts/experiment-report.py`, pinned by `test_a_capture_the_game_resolved_itself_is_still_a_capture` and
`test_verdict_a7_holds_on_a_capture_the_game_resolved_itself`); **after the fix the instrument reads
`HELD Q3 first enemy city kept by T80 [first keep T65]`.** The attempt's window closes here, at **T66**.

| # | the question | the number that decides it |
|---|---|---|
| **Q1** | the establishment under the corrected table by T60 | **HELD - `COMPLETE at T54`**, `siege=2 melee=2 anticav=1 ranged=4 cavalry=1 recon=1`: one turn after A3's T53, six turns inside the deadline, and **the first attempt in the programme to fill the table exactly**, with no row over strength |
| **Q2** | the Encampment in the war city, completed before the second siege unit | **SATISFIED, and by eighteen turns - not a near thing.** Offered T22 (`get_city_production`), unplaceable at T22 (`get_district_advisor` -> `No valid placement tiles`), the tile bought for 35 gold at T27, ordered T27 and **complete T32 on (58,22)**, after `purchase_tile(58,22)` answered `cost:35`; the **second** `UNIT_CATAPULT` was ordered **T49** and owned T54, and the first was ordered T43 and owned T49. The district was standing before any siege unit existed at all |
| **Q3** | a Great General recruited before the war, and never activated | **MET on both halves, and it is the programme's first general.** The district's own points ran 0/40 (T32) -> 7/40 (T39) -> **41/40 (T56)**, where `get_great_people` read `[CAN RECRUIT]` and **`recruit_great_person -> OK:RECRUITED|Trung Trac`**; **no `activate` call exists anywhere in the session's log**; and at the T62 declaration it stood with the stack at (55,22). **The `PROJECT_ENHANCE_DISTRICT_ENCAMPMENT` lever was never pulled** - the mechanism is the district's own points, which is the cheaper half of what the brief left open |
| **Q4** | the gold floor, both measures, and the capture against A3's T67 | **HELD on both halves.** The rule counted **7 red turns** up to the T65 horizon (limit 10) while the diary's own `gold_per_turn` is below the +10 floor on **46 of those 65 turns** - the two measures still disagree, as they have in every attempt; and **the first city was kept at T65, two turns inside A3's T67 bound and the earliest keep in the programme** |

**Q2 in the instrument's sense - the walled target - is not decided and is not decidable on this map**, and
the attempt says which: no city with a wall pool above zero was ever attacked, the target 耶路撒冷 reading
`walls: none` again, exactly as in A2 and A3. That is a property of the map the experiment is played on, and
it is the reason A3's variable and A4's could not be separated by the wall phase.

```
attempt   turns   establishment  army_start  siege_order  first_keep  sci_T20  sci_T40  gpt_T40  h5  self_mismatch  rules_red
A1-T40    T1-T40  not reached    T1          never        none        4.5      7.9      6.0      0   0              1
A2-final  T1-T68  not reached    T1          T48          T68         4.0      5.9      8.9      0   23             6
A3-final  T1-T72  T53            T1          T43          T67         5.5      6.3      9.8      0   6              7
A4-final  T1-T66  T54            T1          T43          T65         4.0      13.9     6.0      0   7              5
```

Snapshot: `docs/experiments/A4-final.json`. **A4 is the fastest capture in the programme (T65 against A3's
T67 and A2's T68), it is the second attempt to complete the corrected table, and it is the first with a
certified pinned opening and the first with a Great General.**

**The divergences that are not the variable, and they are large enough that the two-turn difference must not
be attributed to the district:**

- **The research line is A4's own** - it went through `TECH_BRONZE_WORKING` (T8, the Encampment's
  prerequisite) and reached Engineering at T43, the same turn as A3's, but its **science at T40 is 13.9
  against A3's 6.3**, the largest gap on the compare table. An attempt with more than twice the science is
  not a controlled comparison for a district that costs queue turns.
- **`SETTLER` was ordered at T10 where A1-A3 all ordered theirs at T6**, so every downstream turn in this
  attempt sits four turns later than theirs.
- **The war opened at T62 and the city fell at T65 - three turns of assault.** A3's assault opened T66 and
  its city fell at T67. The two attempts attacked the same city-state with the same doctrine, so the
  comparison is meaningful; **what cannot be read off it is the aura's share**, because the estimate the
  session judges attacks with does not contain the general (measured above) and no attempt has run without
  one under this programme.
- **The war city took an economy order of its own** (a Granary at T54) - the first in the war city after the
  gate, against `tactics/08`'s "nothing else for the duration".

**The honesty note the brief asked for is answered, and it is answered in the affirmative**: the failure mode
was *an Encampment that yields no Great General by the first shot*, and A4's district **did** yield one - 41
points by T56, recruited two turns before the declaration, never activated. **So the mechanism is not
missing; what remains unmeasured is its size.** The district's cost is fully on the record (35 gold, a
four-turn queue, the Barracks it built next, and a research line through Bronze Working), the general
existed and stood with the train, and the city fell two turns earlier than the same doctrine's previous
attempt - but the programme has no aura-less control arm under identical science, and the tool that would
have shown the aura working is blind to it. **The two-turn difference is a correlation the next attempt
inherits, not a measurement A4 can claim.**
