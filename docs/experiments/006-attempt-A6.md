# Attempt A6 - the first siege unit is bought with gold

**Status: in progress** - **one session so far** (`phantom-mahogany-phalanx-89`), played from the
experiment's shared start `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`, started 2026-09-30 and standing at
**T4** when this file is seeded. The attempt's instruction is
`prompts/tasks/tmp/037-attempt-a6-the-first-siege-unit-is-bought.md`; the design is section 3 of
`docs/experiments/README.md`; A5's record is `005-attempt-A5.md`; the cross-attempt report is
`RETRO-2026-09-29.md`. **The record is seeded with the settings, the pin and the hypothesis while the
attempt plays, and the measured half is filled as it lands** - the attempt's own session writes its half
too, and the two are reconciled here.

## Settings: the shared start, one variable

| | A5 (the standing baseline) | A6 |
|---|---|---|
| start | the experiment's shared T1 start | **the same save**, loaded at T1 |
| doctrine | the corrected `tactics/01` plus the chop exception | the **same corrected table**; the chop exception is available and is **not** this attempt's variable |
| the one variable | the destination of the chops | **the first siege unit is bought, not built** - `purchase_item(city_id, "UNIT", "UNIT_CATAPULT")` where A1-A5 produced theirs; the **second** Catapult is still produced, because the arithmetic allows one purchase and no more |
| window | a city kept, or T70 | a city kept, or **T70** (`expires:` T75) |

**The variable has two halves and both are on the record**: the gold is **raised** deliberately (nothing
else is bought inside the funding window, the treasury is not spent on anything) and then **spent in one
purchase**. What it costs is the treasury and the upgrades and tiles that gold would otherwise have bought;
what it is supposed to buy is the first Catapult **four or five turns earlier than A2's T53 completion**,
because a purchase arrives the turn the gold exists and the queue does not have to be waited out.

## The arithmetic, stated before anything is spent

The prices and balances below are A2's and A3's own, quoted rather than re-derived; **the record reads them
again in this attempt's own position and says so if they differ**.

- One `UNIT_CATAPULT` costs **120 production** and **320 gold** - A2's own `get_city_production` reply at
  T68.
- A2's treasury ran T1 6, T10 51, T20 101, T30 160.8, **T40 243.4**, **T50 274.4**, T60 229.8, T68 294.8,
  at +5.0 to +8.9 gold/turn. **A2's peak never reached 320**, so on A2's own path the purchase was never
  possible - which is why the funding arm is a real variable and not a formality.
- **A3 measured the other half**: at **T48** its treasury held **347 gold** and it bought a Catapult,
  `PURCHASED|UNIT_CATAPULT|cost=320g (had 347g)`. So the price **is** payable on this start once the
  treasury is not spent elsewhere. **A6's job is to buy the first unit rather than the second**, and the
  record carries A3's purchase as the evidence the funding arm exists - while noting that A3 is therefore
  **not** a production-only baseline.
- **Q2's number is the turn this attempt's treasury crosses 320.**

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, as in A3-A5. The variable is the first siege unit's gold,
not the opening, so the pin is the condition the attempt's numbers are comparable under.

| order | promised | the record |
|---|---|---|
| 1 | `UNIT_SCOUT` | **T1 - matched** (`set_city_production(city_id=65536, UNIT_SCOUT) -> PRODUCING\|UNIT_SCOUT\|4 turns`, the same turn `TECH_MINING` was set) |
| 2 | `UNIT_SLINGER` | **T5 - matched** (`PRODUCING\|UNIT_SLINGER\|5 turns`) |
| 3 | `UNIT_SETTLER` | **T10 - matched** (`PRODUCING\|UNIT_SETTLER\|9 turns`) |
| 4 | `UNIT_BUILDER` | **T18 - matched** (`PRODUCING\|UNIT_BUILDER\|3 turns`) |

**All four matched, and the instrument certifies it** - run over A6's own session at T19:
**`PIN opening: held - the pinned opening held: UNIT_SCOUT, UNIT_SLINGER, UNIT_SETTLER, UNIT_BUILDER in
that order`**, with **`H5 clean`** beside it (no ram, no tower). **A6 is the third attempt in the programme
whose pinned opening the instrument certifies** (A4 and A5 are the others), so it is comparable with them
on the opening - which is the condition the purchase variable needs.

**A deviation is a re-run, not an explanation** (the brief's own rule): A3's fourth order was
`UNIT_WARRIOR` at T15 with the pin in force, so the pin now carries a mechanical sink rather than a request
for a reason. A4 and A5 both matched it, and both are certified `held` by the instrument.

## The hypothesis, with the numbers that falsify it

`README.md`'s window row is *"the turn the war opens (the train paid for with gold)"*, bounded by *"a city
kept or T70"*. A2's numbers beside it are the first Catapult completed **T53**, the second **T55** and the
war opening **T60**; the baseline for the **war's opening turn is A3's**, not A2's T60, because A2's T60
includes six turns lost to the city-state war-declaration bug that was fixed before A3 ran.

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role (`siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1`, the ram conditional) as the instrument computes it from the diary's `unit_composition` - **bought and produced units count alike** |
| Q2 | **the first siege unit is bought by T50**, against A2's first Catapult completing T53 | the train arrives with **no siege purchase row at all**, or the first purchase turn is later than T50. The row names the city id, the reply's `cost=N (had M)` and the balance the purchase left |
| Q3 | the train is complete (**siege 2/2**) no later than A2's T55, and the war opens as early as the train and the march allow, **against A3's opening turn** | the second Catapult completes after T55, or the war opens later than A3's opening turn. If A3 opened no war inside its window, the record says so and uses the train's completion turn as the bound |
| Q4 | **the accepted cost**: the purchase empties the treasury and `carrying-capacity` goes red on **more turns than A2's ten**, with the diary's `gold_per_turn` below the +10 floor over the funding window - **both measures reported** | the rule's red count is not above A2's ten, or the diary's own `gold_per_turn` is not below the floor over the funding window. The rule is gated `when: turn() >= 60`, so inside a T70 window its count has a ceiling of eleven; the diary's number is the measure live over the whole funding window, which starts the turn the gold is raised |

## The decisive numbers, and the commands

1. **the purchase**: the city id, the purchase turn, the reply's `cost=N (had M)`, the balance left, and the
   turn the treasury first crossed 320;
2. **nothing else bought in the funding window** - the log's `purchase_item` and `purchase_tile` rows are
   the evidence, and the record lists every one of them;
3. **the second Catapult produced**: the order turn and the completion line;
4. **the establishment turn**, every turn, under the corrected table;
5. **the war's opening turn**, against A3's;
6. **the gold floor**, both measures;
7. **the first keep**, against A4's T65, A3's T67 and A5's none.

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run phantom-mahogany-phalanx-89 --from 1 --to 110 --verdict --questions a6
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run phantom-mahogany-phalanx-89 --from 1 --to 110 --step 10 --verdict --questions a6 --save docs/experiments/A6-final.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs\experiments\A5-final.json docs\experiments\A6-final.json
```

## Mid-window review - filled as the attempt passes T20 / T40 / T60

Read at **T4**, which is where the seeded state stands and is therefore mostly empty:

| question | answer at T4 |
|---|---|
| the opening build, against the pin | at T4 **one of four matched**; **by T19 all four are matched and the instrument certifies it** - see the pin table and the re-read below |
| the research line | `TECH_MINING` set at T1 |
| the treasury | T1 read `Gold: 6 (+5/turn)`; the funding window has not started |
| the purchase | **not yet** - it waits on Engineering and on 320 gold |
| the verdict so far on Q1-Q4 | all four `OPEN` at T4 - the deadlines have not arrived |

**Two facts from A5 that this attempt should carry rather than rediscover**, both measured and both on the
retro's ledger:

- **The war's opening turn is set by the march, not by the train.** A5's `get_staging_plan(50,22)` said on
  T46 *"ASSAULT OPENS on this turn with 0 shooter(s) in position ... the plan is the march, not the fire"*,
  and its assault spent T50-T68 walking ten tiles through 182 `STOPPED_MID_PATH` refusals. **A purchase that
  puts the first gun in hand earlier buys nothing if the column is still on the road** - so the record reads
  the war's opening turn against the march as well as against A3, and says which of the two bound it.
- **Two whole movement turns can be lost to AI diplomacy pauses** (A5 lost T57 and T59, every unit at 0
  moves). In an attempt whose margin is a handful of turns, that is the largest uncontrolled cost in the
  window, and it should be recorded as such rather than absorbed.

**Re-read at T19, and the funding half has an early warning on it.** The pin is complete and certified (the
table above). The treasury, read from this attempt's own `get_game_overview` rows:

| turn | gold | gold/turn |
|---|---|---|
| T1 | **6** | +5 |
| T9 | **72** | +5 |
| T12 | **87** | +5 |
| **T20** | **139** | **+7** |

**At +5/turn the treasury would need about forty-seven more turns from T12 to reach the 320 a Catapult
costs** - about **T59**, nine turns past Q2's T50 deadline. **But income rose to +7/turn by T20**, and from
T20's 139 that is about **twenty-six more turns, i.e. about T46** - inside the deadline with four turns to
spare, before counting the trade route, the second city and any luxury the empire sells. **So the warning
stands as a warning and not as a verdict, and the number moved the right way between T12 and T20**, which
is what the checkpoint is for: the funding half is **feasible on arithmetic if income holds or improves**,
and the record reads the treasury at every checkpoint so the turn it crosses 320 (or the turn it becomes
clear it will not) is on the page. **A3 reached 347 by T48 on this same start**, so the route is not
hypothetical.

## The end table, and the verdict - written when the attempt ends

The attempt ends when **a city is kept** - a `city_action` reply reads `KEEP|`, **or** the game resolves the
capture itself and the move's reply reads `CAPTURE_MOVE ... CITY TAKEN` (then no `KEEP|` ever appears and
`resolve_city_capture` answers `NO_PENDING_CITY`; the city list is the confirmation) - or the game reaches
**T70**, whichever comes first (`expires:` T75). When it does, this section carries one row per question
with the number that decides it, the purchase row, the gold ledger over the funding window, the snapshot
`docs/experiments/A6-final.json`, the `--compare` line, and the divergences that are **not** the variable.

**It must carry the two ways this variable can fail while looking like a success**, because a purchase is a
very visible act:

- **gold that was never actually raised**: if the treasury is replenished by a trade, a luxury sale or a
  lucky goody hut rather than by restraint and income, then the funding half of the variable was not
  executed - and the record lists **every** `purchase_item`/`purchase_tile` row and every trade, so that is
  checkable rather than asserted;
- **a train that arrives early and a war that does not**: Q3 is deliberately about the train *and* the
  opening, and A5 is the cautionary case - its first Catapult was three turns early and its war still
  opened late enough that the city was never taken. A fast purchase beside a late war is the variable's
  cost without its benefit.
