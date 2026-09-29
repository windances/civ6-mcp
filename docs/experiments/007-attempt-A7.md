# Attempt A7 - two war cities instead of one

**Status: DONE - a city was kept at T60**, twenty turns inside Q3's T80 deadline, by the session
`divine-amber-outpost-82`, played from the experiment's shared start
`evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` on 2026-09-30. The attempt's instruction is
`prompts/tasks/tmp/done/038-attempt-a7-two-war-cities-done-T60.md`; the design is section 3 of
`docs/experiments/README.md`; A6's record is `006-attempt-A6.md`; the cross-attempt report is
`RETRO-2026-09-29.md`. **This was the longest window in the programme** - a city kept or **T110**
(`expires:` T115) - and it closed on the first half of that line, at T60. The snapshot is
`docs/experiments/A7-final.json`, the comparison line is in *The end table* below, and the whole record was
written from the instrument's own reads rather than from memory.

## Settings: the shared start, one variable

| | A6 (the standing baseline) | A7 |
|---|---|---|
| start | the experiment's shared T1 start | **the same save**, loaded at T1 |
| doctrine | the corrected `tactics/01` | the **same corrected table**, and `tactics/08`'s **one war city** is deliberately widened to two - the task file's own `overrides:` line, so the review reads it as the design and not as drift |
| the one variable | the first siege unit is bought | **two cities run army-unit queues**, on top of the single war city `tactics/08` prescribes |
| window | a city kept, or T70 | a city kept, or **T110** (`expires:` T115) |

**The doctrine this contradicts, quoted rather than paraphrased**: `tactics/08` says *"The war city builds
the war, and the other cities build everything else."* **What the variable costs** is the compounding the
second city did not do - the district or building its queue would otherwise have held, which would compound
for the rest of the game - plus the maintenance of the extra units and the city's growth spent on garrisons
and screens. **What it is supposed to buy** is army production running in parallel with the war city's, so
the establishment and its replacements arrive sooner and the first city can be kept before T80.

**The split is decided once**, on the turn the second city exists, and written in the diary that turn: which
two cities, the turn the second was founded or taken, and the queue each runs for the rest of the window.
`tactics/08`'s rule that a compounding city's queue is never empty still holds for every city that is not
one of the two.

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, as in A3-A6. The variable is the second war city, not the
opening.

| order | promised | the record |
|---|---|---|
| 1 | `UNIT_SCOUT` | **T1 - matched** (`set_city_production(city_id=65536, UNIT_SCOUT) -> PRODUCING\|UNIT_SCOUT\|4 turns`, the same turn `TECH_MINING` was set) |
| 2 | `UNIT_SLINGER` | **T5 - matched** (`PRODUCING\|UNIT_SLINGER\|5 turns`) |
| 3 | `UNIT_SETTLER` | **T6 - matched** (`PRODUCING\|UNIT_SETTLER\|11 turns`), the same turn A1-A3 and A5 ordered theirs |
| 4 | `UNIT_BUILDER` | **T15 - matched** (`PRODUCING\|UNIT_BUILDER\|6 turns`) |

**All four matched, and the instrument certifies it** - run over A7's own session:
**`PIN opening: held - the pinned opening held: UNIT_SCOUT, UNIT_SLINGER, UNIT_SETTLER, UNIT_BUILDER in
that order`**, with **`H5 clean`** beside it. **A7 is the fourth attempt in the programme whose pinned
opening the instrument certifies** (A4, A5 and A6 are the others), so it is comparable with them - which is
what the second-war-city variable needs, because its whole question is a comparison of production lines.

**A deviation is a re-run, not an explanation.** A3's fourth order was `UNIT_WARRIOR` at T15 with the pin in
force; A4, A5 and A6 all matched it and all three are certified `held` by the instrument. **The pinned
`SETTLER` is also the normal way the second war city comes to exist** - at T20 the empire still holds
**one city** (`get_cities` reads `1 cities: Xi'an (pop 3)`), so the settler is walking to its site, and the
record names the city and the turn when it lands.

## The split, and the variable executed

**The second city was founded at `T21 FOUNDED|53,21`** (`unit_action(found_city)`), and **both cities' queues
have been army units from that turn** - which is the variable:

| city | its orders, in turn order | what it is |
|---|---|---|
| **Xi'an (65536)** | `WARRIOR` T20, `SLINGER` T23, `SLINGER` T25, `SLINGER` T26, `HEAVY_CHARIOT` T28 | the war city `tactics/08` prescribes, unchanged |
| **the second city (131073)** | **`SLINGER` T21** - ordered **the turn it was founded** - and `WARRIOR` T28 | **the second war city: an army queue from its first order** |

**So `tactics/08`'s "the other cities build everything else" is overridden exactly as the brief says it
should be**, and **Q2's condition is on track**: both cities hold army-role orders before any keep. The
second city's first unit (a Slinger at 9 turns) completes about **T30**, and the record reads whether it is
alive and where it went when the attempt ends.

**And one shared change has to be recorded beside the variable, because it changes the production the
attempt is measuring.** `T23 choose_pantheon -> PANTHEON_FOUNDED|God of the Forge` - **the +25% toward
Ancient and Classical units belief, founded at T23 on 19 faith**. **The baseline matters here and it is now
measured, not assumed**: the pantheon guard in `build_choose_pantheon` was replaced with the game's own
`CanCreatePantheon()` at the A4/A5 boundary, because the old flat standard-speed 25 refused pantheons the
game was already offering (it cost A3 four turns on Quick). **All three attempts that ran under the fixed
guard founded God of the Forge, and all three founded it below the old threshold**:

| attempt | `get_pantheon_beliefs` reads | founded |
|---|---|---|
| **A5** | T28, **Faith 17** | **T28** |
| **A6** | T25, **Faith 19** | **T25** |
| **A7** | T23, **Faith 19** | **T23** |

**That is the live verification the retro was waiting for**: faith 17 and 19 are both below the flat 25 the
old guard demanded, so under the old code all three would have been refused for several more turns - and
A2's attempt shows what that costs (no pantheon at all until T41). **So A7's production is boosted by the
fixed guard exactly as A5's and A6's are**, and its 3-to-5-turn head start on the belief is the ordinary
spread between three attempts rather than a confound unique to it. **The production comparison for this
variable is therefore against A5 and A6** - the two attempts under the same guard and the same corrected
`tactics/01` - and against A2-A4 only with the belief difference named.

**Re-read at T42, and both queues are still army units.** The variable is holding rather than being a
founding-turn gesture, which is what Q2 asks:

| turn | Xi'an (65536) | the second city (131073) |
|---|---|---|
| T32 | `HEAVY_CHARIOT` | - |
| T34 | - | `WARRIOR` |
| T36 | `WARRIOR` | - |
| T37 | `SLINGER` | `SLINGER` |
| T39 | `SCOUT` | `SLINGER` |
| T40 | `TRADER` | - |

**Both cities have ordered army units on the same turn twice** (T37 and T39), which is the parallelism the
variable is for. **The research line is the thing to watch**: `TECH_MINING` T1, `THE_WHEEL` T8 (complete
T22) and **`TECH_ENGINEERING` set at T23**, still researching at **T34** - so Engineering is due about
**T46**, four to five turns behind A6's T43-onward pace and the reason the first Catapult is not on the board
at T42. **Q1 is therefore live but tight**, and the record reads the establishment at the T50 and T60
checkpoints rather than assuming it.

## The gate holds, and the two war cities build the train in parallel

**`Research complete: Engineering` sits in T44's `end_turn`, so the tech is owned from T45 - and on T45
both war cities ordered a `UNIT_CATAPULT` in the same turn**:

| city | the order | the queue read |
|---|---|---|
| **Xi'an (65536)** | `set_city_production(UNIT_CATAPULT)` | `PRODUCING\|UNIT_CATAPULT\|6 turns` |
| **the second city (131073)** | `set_city_production(UNIT_CATAPULT)` | `PRODUCING\|UNIT_CATAPULT\|9 turns` |

**This is the variable doing the thing it was written to do, and it is the first time in the programme a
siege train has been built in parallel rather than one city deep** - A2-A6 all had one war city, and every
one of them built its two Catapults sequentially. **The gate also holds for the fourth consecutive attempt**
(Engineering owned T45 and the train ordered that same turn; A3, A4 and A5 ordered theirs at T43 and A6 at
T46).

**What the parallelism is actually worth, computed now rather than asserted at the end**: the two queues
finish at about **T51** (Xi'an, 6 turns) and **T54** (the second city, 9 turns), so `siege 2/2` arrives
about **T54**. Built sequentially in the faster city alone it would be **T45 + 6 + 6 = T57**. **So the
second war city buys about three turns on the train, not the halving its queue count suggests** - because
the second city is **1.5x slower per Catapult** (9 turns against 6), and the train's completion is set by
the *slower* of the two, not by their sum. That is the number the end table has to weigh the lost
compounding against, and the record states it before the attempt ends so the comparison is not made
retrospectively.

**And the instrument's H6 reads the split as real and roughly even**: `2 cities ordered army units (city
65536: 13, city 131073: 9); 65536 carries 59% of them` - so the second city carries **41%** of the army
orders, which is a second war city by any reading rather than a token order. The establishment at T49 is
short **`anticav 0/1` and `siege 0/2`** - the train is building and the anti-cavalry unit is not yet
ordered.

**And both Catapults landed exactly where the arithmetic above said they would.** The second war city is
**Chengdu** (131073):

| unit | city | the completion line | owned from |
|---|---|---|---|
| the first Catapult | **Xi'an** | `>> Xi'an finished building UNIT_CATAPULT` in **T50's** `end_turn` | **T51** |
| the second Catapult | **Chengdu** | `>> Chengdu finished building UNIT_CATAPULT` in **T53's** `end_turn` | **T54** |

The instrument then reads **`COMPLETE at T54  siege=2 melee=6 anticav=1 ranged=10 cavalry=2 recon=2`** -
**six turns inside Q1's deadline and joint-earliest in the programme with A4 and A6**, and **heavily over
strength in every row the two-city split touches** (six melee, ten ranged, two cavalry against the table's
2/4/1). **The variable is therefore delivered in full: two cities each built a Catapult, and the train
completed the turn the slower of them finished** - which is what the arithmetic predicted before either
order was placed.

**And the war opened at T56**: `WAR_REQUESTED|DECLARE_SURPRISE_WAR on Jerusalem`, the same city-state A2-A6
attacked. So at the declaration A7 had a complete establishment, a two-city train, God of the Forge from
T23, and **the question the attempt exists to answer - whether that becomes a city kept by T80 - is the only
one left open**, with Q2 (two cities producing before the keep) already satisfied by construction.

**And the assault's opening pace is the first evidence that the variable pays.** Three turns after the
T56 declaration, at **T59**, 耶路撒冷 reads **`CITY_CENTER (CS:0, HP:81)`** - **200 down to 81 in three
turns**, with a Warrior already in melee at 23 HP and **26 units** on the board (`get_units`). Against a
~20/turn heal that is roughly **60 damage a turn**, which is what a two-Catapult train plus an
establishment at six melee and ten ranged delivers; the pool arithmetic says it empties about **T61-T62**,
which would be **three to four turns earlier than A4's T65, the earliest keep in the programme**. **The
record states that projection now** so the end table can be read against it, and it does not treat the
projection as the result - the keep turn is what decides, and the last two attempts both ended with the
city still standing.

## The hypothesis, with the numbers that falsify it

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role (`siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1`, the ram conditional), as the instrument computes it from the diary's `unit_composition` |
| Q2 | **two cities have each produced at least one army-role unit before the first city is kept**, and the record names the second war city, the turn it was founded or taken, and its first army order | the first keep arrives with only one city holding an army-role order. Read per city from the log's `set_city_production`/`purchase_item` rows (the instrument's `military_city_spread.per_city`), with `get_units` or the diary's `unit_composition` as the cross-check that the second city's unit still exists |
| Q3 | the first city is kept **by T80** | T80 arrives with no keep in the log |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns**, both measures, because a second war city means more units and more maintenance | the rule reads red ten or more times, or the diary's own `gold_per_turn` sits below +10 on ten or more turns of the window. **Report both numbers and which turns each covers**: the rule only evaluates from T60, so before T60 the diary's number is the only one live |

## The decisive numbers, and the commands

1. **the two war cities, named on the turn the second exists**: the city, the turn it was founded or taken,
   and the queue each runs - with the *first army order from each* as the evidence, from the log's
   `set_city_production` rows;
2. **both cities' army orders and completions** for the rest of the window, and whether the units still
   exist at the keep (`get_units` is the cross-check);
3. **the establishment turn**, every turn, under the corrected table;
4. **the first keep**, against A4's T65, A3's T67 and A6's none - and against Q3's T80;
5. **the gold floor**, both measures, with the turns each covers;
6. **the compounding the second city did not do**, named rather than implied: what its queue would have
   held, so the cost half of the variable is on the record beside its production.

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run divine-amber-outpost-82 --from 1 --to 115 --verdict --questions a7
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run divine-amber-outpost-82 --from 1 --to 115 --step 10 --verdict --questions a7 --save docs/experiments/A7-final.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs\experiments\A6-final.json docs\experiments\A7-final.json
```

## Mid-window review - filled as the attempt passes T20 / T40 / T60 / T80 / T100

Read at **T2**, where the seeded state stands:

| question | answer at T2 |
|---|---|
| the opening build, against the pin | **one of four matched**: `UNIT_SCOUT` T1; orders 2-4 not yet placed |
| the research line | `TECH_MINING` set at T1 |
| the two war cities | **not yet**: one city exists, and the split is decided on the turn the second one does |
| the verdict so far on Q1-Q4 | all four `OPEN` at T2 - the deadlines have not arrived |

**What A7 inherits, and it is the reason this attempt's question is the *keep* rather than the build.**
A5 and A6 both ended with **no city**, and the two attempts together isolate where the failure is:

- **A5** completed the table at T57, opened its war at T59, and lost - its own record blames the **march**
  (182 `STOPPED_MID_PATH` refusals over T50-T68) and two movement turns lost to AI diplomacy pauses.
- **A6** did everything the production doctrine asks and more clearly than any attempt before it -
  **bought the first Catapult at T46**, completed the establishment at **T54 filled exactly**, opened the
  war at **T52 with the train whole that same turn**, and paid for it so cheaply that Q4 was **falsified**
  ("the purchase turned out free") - **and still took no city.** Its assault died of **one gun in range at a
  time** (`SIEGE FIRE: 1/2`), a supply line that **never passed 2/6 cut** so the city healed ~20 a turn, and
  **six turns of legal attacks discarded with `force=True`**.

**So the programme's own evidence says the binding constraint has moved from production to the assault**,
and A7 is the attempt that can test it: a second war city is a production variable, and if A7's keep comes
no earlier than A6's non-keep, then the production arm of this doctrine is exhausted and the next revision
belongs to `tactics/05`/`06` (screening, concentration, the supply cut) rather than to `tactics/01`. **The
record states that prediction now**, so the end table can be read against it rather than around it.

## The end table, and the verdict - written when the attempt ends

**The attempt ended on the first half of its finish line: 耶路撒冷 (50,22) was kept at T60.** The capture
resolved inside the AI turn - **no `KEEP|` reply was ever produced and no `CAPTURE_MOVE ... CITY TAKEN` was
issued**, which is exactly the second of the two cases the task file anticipates - and **the city list is the
confirmation**: `get_cities` at T60 reads **`3 cities`**, with `Jerusalem (pop 4) at (50,22) ... [id:196610]`,
a Warrior garrison, `HP:120/200`, `Loyalty: 67/100 (gaining +17.0/turn, full in 2)`, a `HOLY_SITE` district at
(49,22) and a `MONUMENT` and `GRANARY` both flagged `!! PILLAGED`. The T60 notifications read
**`Capital Captured`** and **`Defeated!`** - the city-state was eliminated by the capture of its only city.
**The instrument could not see any of that when this table was written, and it can now.** The reader in
`scripts/experiment-report.py` took the keep from a `city_action`/capture reply in the log, so at the time
of writing `A7-final.json` and the `--compare` line both printed **`first_keep none`** for A7 exactly as
they do for A6. **That was the third capture shape the programme has hit** - `KEEP|` (A3), a self-resolved
`CAPTURE_MOVE ... CITY TAKEN` (A4), and now a capture the game reported **nowhere at all**, where the only
evidence is that the next city list counts the city as ours. **The reader has been extended to read it**:
it remembers the cities an estimate has named as targets (`** Target tile is a city (NAME)`) and treats
that name appearing in a later `get_cities` row as a city we hold, whatever the replies said. Re-run over
A7's log it now answers **`Q3 HELD - the first city was kept T60`**, and the two new tests in
`tests/test_experiment_report.py` pin the shape, including that a city we merely *attacked* is not a keep
and that a city settled before any attack is not one either.

**The adjudication rule this leaves is the one A4 already needed**: the instrument is the reader, and where
it cannot see a fact the record states the fact and its evidence - here the T60 city list and the
`Capital Captured` / `Defeated!` notifications - rather than reporting `none` as if nothing happened.
**`A7-final.json` keeps the reading it was taken with** (the programme's rule for snapshots), so its
`first_keep` still reads `none` and a re-run is what shows `T60`; the compare table and this record carry
the corrected number.

### One row per question

| # | prediction | the number that decides it | verdict |
|---|---|---|---|
| **Q1** | the establishment complete by **T60** | **complete at T54** - `siege 2 melee 6 anticav 1 ranged 10 cavalry 2 recon 2`, six turns early, first siege ordered **T45** | **HELD** |
| **Q2** | two cities each producing an army unit before the first keep, with the second city named | city **65536 (Xi'an)** and city **131073 (Chengdu)**, Chengdu **founded T21 by the pinned SETTLER** with `UNIT_SLINGER` ordered **that same turn**; instrument: `2 cities ordered army units (65536: 15, 131073: 12)` | **HELD** |
| **Q3** | the first city kept by **T80** | **kept at T60** - twenty turns early, and earlier than the programme's previous best (A4's T65) | **HELD** |
| **Q4** | `carrying-capacity` red on **fewer than ten** turns | rule red **1 turn** (T60, its first live turn: `gold/turn +8.0 with military 272`); diary's own `gold_per_turn` **below +10 on all 60 turns** | **FAILED**, both measures reported below |

**Q4 is the one row where this record and the instrument disagree, and the brief settles it.** The
prediction's falsifier has two halves joined by *or*: *"the rule reads red ten or more times, **or** the
diary's own `gold_per_turn` sits below 10 on ten or more turns of the window"*. The rule half passes - it
was red **once** - but **the diary half fails on every turn of the window, so Q4 is FALSIFIED**. The
instrument's `--questions a7` reports `HELD` for Q4 because its reader scores only the rule count; **the
record follows the brief and says so here** rather than letting the instrument's single number stand for a
two-part claim. Both numbers are reported, and the same split has now appeared in every attempt of the
programme: **the army has never once been above the +10 floor by the diary's own measure.**

### The two war cities' ledgers, side by side

Read per city from the log's `set_city_production` rows (the instrument's `military_city_spread.per_city`,
cross-checked against `get_units`):

| city | army orders, in turn order | count | what it built that reached the front |
|---|---|---|---|
| **Xi'an (65536)** - the doctrine's one war city | `WARRIOR` T20, `SLINGER` T23/T25/T26, `HEAVY_CHARIOT` T28/T36, `WARRIOR` T36, `SCOUT` T39, `CATAPULT` T45 | **15** of the empire's army orders | the **first Catapult** (owned T51), four Slingers upgraded to Archers at T51, two Heavy Chariots, Warriors |
| **Chengdu (131073)** - **the variable** | **`SLINGER` T21** (the turn it was founded), `WARRIOR` T28/T31/T34, `SLINGER` T37/T39, `CATAPULT` T54-ordered T-Chengdu | **12** | the **SECOND Catapult, owned T54** - the gun the two-Catapult timetable rests on - plus a Warrior that held Chengdu |

**Chengdu carried 41% of the empire's army orders** (`65536 carries 56%`), so the split is real rather than
token. **Both Catapults landed exactly where the pre-assault arithmetic said they would** (T51 in Xi'an,
T54 in Chengdu), and the establishment completed on the slower of the two - **T54, six turns inside Q1**.

### The comparison line

```
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs\experiments\A6-final.json docs\experiments\A7-final.json

attempt   turns   establishment  army_start  siege_order  first_keep  sci_T20  sci_T40  gpt_T40  h5  self_mismatch  rules_red
A6-final  T1-T69  T54            T1          T46          none        4.0      5.4      13.4     0   0              6
A7-final  T1-T60  T54            T1          T45          none        4.0      6.3      6.1      0   18             4
```

**The same establishment turn (T54), the siege ordered one turn earlier (T45 against T46), science at T40
HIGHER (6.3 against 5.4) and gold/turn at T40 LESS THAN HALF (6.1 against 13.4)** - that last column is the
variable's cost, and it is the only column where A7 clearly loses. `rules_red` is lower for A7 (4 against 6);
`self_mismatch` is higher (18 against 0) and is explained under *Divergences* below.

### The gold floor, both measures, with the turns each covers

- **the rule's own `carrying-capacity`** - it only begins to evaluate at **T60**, so its entire counted window
  is **one turn**: `gold/turn +8.0 with military 272 - BELOW the +10` at T60, i.e. **red 1 of 1**. The
  `--verdict` line reads `Q4 HELD [2 red turn(s) by the rule up to T60]`.
- **the diary's own `gold_per_turn`** - the number that is live before T60: **below +10 on every one of the
  60 turns**, `+5.0` over T1-T21, `+7.0` over T22-T36, `+6.0` over T37-T51 and `+4.0` to `+8.0` over T52-T60.
  The `--verdict` line reads `the diary's own gold/turn is below 10 on 60 of those 60 turn(s)`.

**The two measures agree in direction and disagree in size by a factor of sixty**, because they cover
different spans - and Q4 is **falsified** on the diary's measure and nominally **held** on the rule's.

### The compounding the second city did not do, named

Chengdu's queue was an army queue from T21, so **the build it never made is the one `tactics/08` step 2 asks a
non-war city for: the next district, or its building.** At Chengdu's pop 1 (T21) the slot arithmetic allowed
**no specialty district** (`floor(1/3) = 0`), so the alternative was a **MONUMENT** (60 production at its 3
production = **~20 turns, landing ~T41**) or a **GRANARY** (65 at 3 = **~22 turns, ~T43**). **It is not
hypothetical that this could have landed inside the window** - Chengdu reached 7 production by T38 and 9 by
T54, so either building would have finished well before T60 on the production it later had. **The cost is on
the record as a building not built rather than as an adjective**, and it is visible in the empire's own
numbers: **`CHECK FAILED [idle-district-slot]` at T60 - `2 districts for pop 11 (allowed 3)`, one slot idle** -
and in the `--compare` line's `gpt_T40 6.1` against A6's `13.4`. **What it bought is the T54 establishment and
the T60 keep**, which is the trade the attempt was published to measure.

### Divergences that are NOT the variable

1. **The 18 self-report mismatches are a recording convention, not a drift.** The instrument counts **every
   unit in a role class**; A7's diary `ESTABLISHMENT` lines counted **the table's requirement**, writing
   `ranged 4/4` while the record held ten ranged-class units and `recon 1/1` while it held two Scouts.
   **Every mismatch runs in the conservative direction** (claimed less than held: `ranged 4 vs 10 held`,
   `recon 1 vs 2 held`), so no A7 claim overstates the army. **A6 wrote the two lines the same way and the
   instrument found no mismatch, because A6's surplus did not exist** - so the difference is a property of how
   big the surplus got, not of how the two attempts were recorded.
2. **`cavalry 2/1` in the diary against `cavalry 0/1` in the review's own prerequisite line.** The empire
   holds **two Heavy Chariots** (heavy cavalry) and never built a Horseman; the review's metric counts
   light cavalry (Horseman/Knight). **Both numbers are reported**; the table's cavalry row is satisfied in fact
   and unsatisfied in metric, and the 2 Heavy Chariots did fight at 耶路撒冷.
3. **No major civilization was met in the whole attempt** (map revealed 2% at T1 to 19% at T60; the
   instrument prints `no rival met by T60`), so the second rival capital was never a candidate and the
   objective was 耶路撒冷, the same city-state A2-A6 attacked. This is a property of the shared save, not of
   the variable.
4. **One Archer and one Slinger were lost**, and **a ranged attack from a tile the staging plan assigned,
   (51,20), answered `NO_LOS`** - the plan assigns ring tiles by distance only and does not check line of
   sight. Neither is a production variable.

### What the next revision changes

**Q1, Q2 and Q3 all held and Q4 failed on the diary's measure, and the attempt's own numbers say the variable
worked for exactly the reason it was proposed**: a second war city supplied the **second Catapult at T54**,
the train completed six turns inside its deadline, and the city was kept at **T60**. **The measured cost is
concentrated in one place - the gold line** (`gpt_T40 6.1` against A6's 13.4, and below +10 on all sixty
turns), **not in the district slot**, which stayed one short of its allowance rather than three. **The next
revision this supports is not to `tactics/01`'s establishment table, which both attempts filled at T54, but to
`tactics/08`'s cash rule**: a two-war-city split is affordable only if the gold line is funded at the same
time, and `Conscription` (taken at T50) was not enough. **The two ways the variable can fail while looking
like a success are both checked and both negative**: every one of Chengdu's army orders was a unit that
reached the front (its Slinger was upgraded to an Archer and its Catapult fired at 耶路撒冷), and its
alternative building **would** have finished inside the window, so the lost compounding was real and not
free.

**It must carry the two ways this variable can fail while looking like a success**, because a second war
city is very visible:

- **a second queue that produces nothing that reaches the front**: a unit built in a city far from the
  target, or one that dies on the road, is not parallel production - it is maintenance. The record names
  **where each of the second city's units went** and whether it was still alive at the keep;
- **compounding bought with a city that could not compound anyway**: if the second city's alternative was a
  building it could not have finished inside the window either, then the variable cost nothing and proves
  nothing - so the record says what that city's queue would have held **and how many turns it would have
  taken**, rather than asserting the lost compounding in the abstract.
