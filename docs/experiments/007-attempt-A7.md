# Attempt A7 - two war cities instead of one

**Status: in progress** - **one session so far** (`divine-amber-outpost-82`), played from the experiment's
shared start `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`, started 2026-09-30 and standing at **T2** when
this file is seeded. The attempt's instruction is `prompts/tasks/tmp/038-attempt-a7-two-war-cities.md`; the
design is section 3 of `docs/experiments/README.md`; A6's record is `006-attempt-A6.md`; the cross-attempt
report is `RETRO-2026-09-29.md`. **This is the longest window in the programme** - a city kept or **T110**
(`expires:` T115) - and the record is seeded with the settings, the pin and the hypothesis while the attempt
plays, with the measured half filled as it lands.

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

The attempt ends when **a city is kept** - a `city_action` reply reads `KEEP|`, **or** the game resolves the
capture itself and the move's reply reads `CAPTURE_MOVE ... CITY TAKEN` (then no `KEEP|` ever appears and
`resolve_city_capture` answers `NO_PENDING_CITY`; the city list is the confirmation) - or the game reaches
**T110**, whichever comes first (`expires:` T115). When it does, this section carries one row per question
with the number that decides it, **the two war cities' order ledgers side by side**, the snapshot
`docs/experiments/A7-final.json`, the `--compare` line, and the divergences that are **not** the variable.

**It must carry the two ways this variable can fail while looking like a success**, because a second war
city is very visible:

- **a second queue that produces nothing that reaches the front**: a unit built in a city far from the
  target, or one that dies on the road, is not parallel production - it is maintenance. The record names
  **where each of the second city's units went** and whether it was still alive at the keep;
- **compounding bought with a city that could not compound anyway**: if the second city's alternative was a
  building it could not have finished inside the window either, then the variable cost nothing and proves
  nothing - so the record says what that city's queue would have held **and how many turns it would have
  taken**, rather than asserting the lost compounding in the abstract.
