# Attempt A5 - the chops go into units

**Status: in progress** - **one session so far** (`unbroken-cerulean-herald-09`), played from the
experiment's shared start `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`, started 2026-09-30 and standing at
**T29** when this file is seeded. The attempt's instruction is
`prompts/tasks/tmp/036-attempt-a5-the-chops-go-into-units.md`; the design is section 3 of
`docs/experiments/README.md`; A4's record is `004-attempt-A4.md` - **the clean baseline, because its pinned
opening is the first the instrument certified** - and the cross-attempt report is
`RETRO-2026-09-29.md`. This file is A5's record. **The record is seeded with the settings, the pin and the
hypothesis while the attempt plays, and the measured half is filled as it lands** (the attempt's own
session writes its half too; the two are reconciled here).

## Settings: the shared start, one variable

| | A4 (the baseline) | A5 |
|---|---|---|
| start | the experiment's shared T1 start | **the same save**, loaded at T1 |
| doctrine | the corrected `tactics/01` | the **same corrected table**, plus the **new chop exception** that landed at the A4/A5 boundary (item 3 of `## Production order`) |
| the one variable | the Encampment's place in the war city's queue | **the destination of the chops** - feature removals in the war city go into the unit in the queue rather than into infrastructure, with **Magnus** in that city |
| window | a city kept, or T110 | a city kept, or **T70** (`expires:` T75) |
| the comparability gate | pin certified `held` | **pin certified `held`** (below) |

**The variable's cost is stated before it is measured**: builder charges spent on production rather than on
improvements, the features themselves and the yields they would have carried for the rest of the game, and
the turns those builders are away from the tiles the compounding cities need. What it is meant to buy is the
siege half of the establishment **five or more turns earlier than A2's T55**.

## The enabler is recorded, not assumed

`Groundbreaker` is Magnus's level-0 ability (`DLC/Expansion1/Data/Expansion1_Governors.xml:40,151`,
`Level="0" BaseAbility="true"`, +50% to plot harvests and feature removals in his city), so it arrives with
his **appointment** rather than from a governor point. The record carries three turns and the evidence the
ability is in force:

| what | the read that settles it | recorded |
|---|---|---|
| appointed | the `appoint_governor` reply | **T34** - `APPOINT_REQUESTED\|Magnus - verify with get_governors()` |
| assigned to the war city (西安) | the `assign_governor` reply | **T34** - `ASSIGNED\|Magnus to Xi'an` |
| `established=1` there | `get_governors` | **T39** - the read drops the parenthetical and says `Appointed (1): Magnus (GOVERNOR_THE_RESOURCE_MANAGER) - Xi'an (established)`, five turns after the T34 appointment, exactly as the T34 read predicted |
| the ability is in force | `GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER` has dropped off the `GOV_PROMO` list, and `promote_governor` with it answers `ERR:ALREADY_PROMOTED` - **that answer is the record of the ability, not a failure** | **T34, and this is the clean evidence**: the T34 `get_governors` lists Magnus's available promotions as Surplus Logistics, Provision, Industrialist, Black Marketeer and Vertical Integration - **`GROUNDBREAKER` is absent from that list**, which is what a level-0 `BaseAbility` looks like once its holder is appointed. The session has not called `promote_governor` with it, so the `ERR:ALREADY_PROMOTED` half is not on the record; the absence is |

The governor point comes from `CIVIC_STATE_WORKFORCE`, which the session took at **T23** and completed
before T34. **So the variable's precondition is satisfied in the order the brief requires**: Magnus is in the
war city before any chop, because no chop has been made yet - the session is holding every forest and jungle
tile in 西安's ring for the Catapult window, and Engineering has been researching since **T22**.

## The opening build is pinned, and the pin held

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, order by order. The variable is the chops' destination, not
the opening, so the pin is the condition the attempt's numbers are comparable under.

| order | promised | the record |
|---|---|---|
| 1 | `UNIT_SCOUT` | **T1 - matched** |
| 2 | `UNIT_SLINGER` | **T5 - matched**, placed the turn the Scout completed |
| 3 | `UNIT_SETTLER` | **T6 - matched**, and the **first time in the programme a pinned `SETTLER` matches A1-A3's T6** (A4's came at T10, four turns late) |
| 4 | `UNIT_BUILDER` | **T15 - matched** |

The instrument's own line, run over A5's session:
**`PIN opening: held - the pinned opening held: UNIT_SCOUT, UNIT_SLINGER, UNIT_SETTLER, UNIT_BUILDER in that
order`**. **A5 is the second attempt in the programme whose pinned opening the instrument certifies** (A4
was the first), and the first whose `SETTLER` is on time - so A5 and A4 are comparable on their openings,
which is what the chop variable needs.

## The hypothesis, with the numbers that falsify it

`README.md`'s window row is *"the establishment turn against A2's T48/T53/T55, and the economy at T60"*,
bounded by *"a city kept or T70"*. A2's numbers are Engineering and both Catapults ordered **T48**, the
first Catapult completed **T53**, the second **T55**, and its first post-gate economy order at **T55**.

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role (`siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1`), as the instrument computes it from the diary's `unit_composition` |
| Q2 | the establishment arrives at least **5 turns earlier than A2's T55, i.e. by T50** | the instrument's establishment turn is T51 or later, or is never reached inside the window |
| Q3 | the economy is behind by **less than 5 turns**: the first `BUILDING`-or-`DISTRICT` order **after the Engineering gate** lands **by T60** (A2's was T55) | the first post-gate `BUILDING`-or-`DISTRICT` order is T61 or later, or the log holds none. **Post-gate on purpose**: A2's own first non-unit order was a Granary at T28, twenty turns before Engineering existed |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns** | the rule reads red ten or more times. **Both measures are reported** - the rule only evaluates from T60 and this attempt ends at T70, so the diary's own `gold_per_turn` is the one live over the whole window, and A1, A2 and A4 all sat under the +10 floor on most of their turns |

## The decisive numbers, and the commands

1. **every chop, one row each**: the city, the tile, the feature, the turn, **which queue item absorbed the
   production**, and the builder's remaining charges - `remove_feature` is refused outside the city's owned
   ring, and no tool prints the production gained, so the gain is read from the queue's turn count before
   and after, or the record says it could not be read rather than estimating;
2. **the establishment turn**, every turn, under the corrected table;
3. **the gate** (Engineering -> the first siege order), as in A4;
4. **the first post-gate economy order**;
5. **the gold floor**, both measures;
6. **the first keep**, against A4's T65 and A3's T67.

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run unbroken-cerulean-herald-09 --from 1 --to 110 --verdict --questions a5
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run unbroken-cerulean-herald-09 --from 1 --to 110 --step 10 --verdict --questions a5 --save docs/experiments/A5-final.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs\experiments\A4-final.json docs\experiments\A5-final.json
```

## Mid-window review - filled as the attempt passes T20 / T40 / T60

Read at **T29**, which is where the seeded state stands:

| question | answer at T29 |
|---|---|
| the opening build, against the pin | **all four matched, and the instrument certifies `held`**: `UNIT_SCOUT` T1, `UNIT_SLINGER` T5, `UNIT_SETTLER` T6, `UNIT_BUILDER` T15 |
| the second city | **founded at (57,25) on T21** (`FOUNDED\|57,25`), queue set to a Monument on the same turn - the compounding city, with 西安 as the war city |
| the variable so far | **nothing chopped yet, and that is correct**: the chops are held for the Catapult window, and the session's own T20 plan says so - "ALL forest/jungle chops on 西安's tiles are held for the Catapult window", with Magnus to be appointed and assigned "the turn the governor point arrives, recording all three turns" |
| the enabler | **not yet**: `CIVIC_STATE_WORKFORCE` taken at T23 and still researching at T29; no `appoint_governor` in the log |
| production so far | `SCOUT` T1, `SLINGER` T5, `SETTLER` T6, `BUILDER` T15, `SLINGER` T20, `MONUMENT` T21 (city 2), `WARRIOR` T22, `SLINGER` T24, `SLINGER` T26, `SLINGER` T28, `HEAVY_CHARIOT` T29 |
| exploration and contact | 6% at T17 and no rival met - the target will again be a city-state unless the scout finds a major |
| the verdict so far on Q1-Q4 | all four `OPEN` at T29 - the deadlines have not arrived |

**Re-read at T35, and the variable's precondition is met.** The two things that had to happen before a chop
could be legitimate both happened, in the right order:

- **Magnus is in the war city from T34** - appointed and assigned the same turn (the chain above), with
  `Groundbreaker` already held by virtue of being his level-0 ability. He establishes about T39.
- **No chop has been made**, so the enabler preceded the activity it enables. The session is holding every
  forest and jungle tile in 西安's ring, and Engineering has been on the research line since **T22** - the
  Catapult window the chops are waiting for.

The establishment is being built in parallel: 西安 is the war city and its queue has run
`SCOUT` T1, `SLINGER` T5, `SETTLER` T6, `BUILDER` T15, `SLINGER` T20, `WARRIOR` T22, `SLINGER` T24,
`SLINGER` T26, `SLINGER` T28, `HEAVY_CHARIOT` T29, while the second city (founded (57,25) at T21) has been
given a Monument. The next things to look for are the **first `remove_feature`** with its city, tile,
feature, turn and the queue item that absorbed the production, and the **Engineering gate**.

## The chop table - one row per chop

This is the attempt's central evidence, and it carries what the record *can* establish rather than what the
variable is supposed to buy.

| # | turn | city | tile | feature | the queue item that absorbed it | what can be established about the gain |
|---|---|---|---|---|---|---|
| 1 | **T40** | 西安 (65536) | (60,20) | `FEATURE_FOREST` on a **SILK** tile, owned by China | 西安's queue held **`UNIT_WARRIOR`** - the T39 order set it at **2 turns** and the T40 order, issued after the chop, reads **1 turn** | **the gain is not separable, and the record says so rather than estimating**: exactly one turn of ordinary production elapsed between those two reads, so `2 -> 1` is what the queue would have read with no chop at all. What **is** on the record is the tile itself: at T39 it reads `PLAINS FOREST [SILK+] {F:1 P:2 C:1}` and at T42 `PLAINS [SILK+] {F:1 P:1 C:1}` - the forest is gone and the tile's own production fell by one |
| - | T39, twice | 西安 | (60,21) | `FEATURE_JUNGLE` | - | **refused**: `Error: CANNOT_REMOVE\|Cannot remove FEATURE_JUNGLE at (60,21)`. The tile carries **no "(owned by China)"** marker in the map reads, which is the refusal the brief documents; the builder was moved to the owned SILK tile instead |
| - | T42 | 西安 | (59,22) | `FEATURE_JUNGLE` | - | **refused the same way**, and likewise unowned |
| 2 | **T44** | **not established - see below** | (57,24) | `FEATURE_FOREST` on grass, river | **not established**, and this is the row the record is least able to close | **the destination is genuinely ambiguous and the record says so**: the only city read on that turn (T44) shows 西安 building `UNIT_CATAPULT (5 turns)` and **Shenyang `Building: nothing`**, and (57,24) is adjacent to Shenyang at (57,25) - but the same read lists 西安 as still needing a builder on a DYES tile at y=24, so **the owning city is not settled by any read available**, and with it neither is the queue item. The one clean fact beside it: **西安's Catapult fell from `7 turns` at T43 to `5 turns` at T44**, a drop larger than 西安's own ~10/turn production, and the record does **not** attribute that to this chop, because the chop may belong to the other city |

**The gate is now measured for A5, and it held for the third time in the programme.** The log's
`Research complete: Engineering` line sits in **T42's** `end_turn`, so Engineering is owned from **T43** -
and `T43 set_city_production(city_id=65536, UNIT_CATAPULT) -> PRODUCING|UNIT_CATAPULT|7 turns` orders the
siege train in the war city **on that same turn**, with no `BUILDING`/`DISTRICT` order in 西安 before it
(the only post-gate building order in the log so far is a **Water Mill in Shenyang**, the second city, at
T44). **A3, A4 and A5 have all three ordered their first Catapult on T43**, which is why their compare lines
line up on the `siege_order` column.

**And the second chop exposes the sharper version of the measurement problem**: a chop's destination is only
recorded if the record knows **which city owns the tile** and **what that city's queue held**, and the T44
reads settled neither - the map reads print `(owned by China)` on some tiles and not others, and no read ties
a tile to a city. So the record states the ambiguity rather than picking a city. The distinction matters for
the variable: a chop in **Shenyang** is outside it entirely, because Magnus is established in **西安** and
Groundbreaker is `in city`, so a second city's chop carries no +50% and is not the thing A5 exists to test.

**And that exposes the measurement problem the brief only anticipated - now measured**: `remove_feature`
answers `REMOVING_FEATURE\|<feature> at x,y` and names no production, so the queue's turn count is the only
route to the gain - and **a queue item that is two turns out becomes one turn out in one turn with or without
a chop**. A chop into an item with a small remaining count cannot be measured this way at all. The record
will therefore either read a chop against an item with enough turns left that the drop is larger than one, or
it will state that the contribution could not be read; **it will not estimate it**. That is a limitation of
the instrument, not of the session's play - the session chopped an owned feature into a unit queue item with
Magnus established in that city, which is the variable executed.

**One tool finding comes from this window and is on the ledger rather than in this record's results**: at
T20 the session issued `unit_action(unit_id=393217, ...)` for a unit id that **its own `get_units` read did
not list**, and the order was applied to a **different unit** (the Warrior, id 131073). The session caught it
itself and wrote the rule down - ids must be re-read from `get_units` rather than inferred. The measured case
and the staged fix are in `RETRO-2026-09-29.md`'s ledger; the fix is deliberately **not** landed while this
attempt plays, because the helper is on every unit action's path.

## The end table, and the verdict - written when the attempt ends

The attempt ends when **a city is kept** - a `city_action` reply reads `KEEP|`, **or** the game resolves the
capture itself and the move's reply reads `CAPTURE_MOVE ... CITY TAKEN` (then no `KEEP|` ever appears and
`resolve_city_capture` answers `NO_PENDING_CITY`; the city list is the confirmation) - or the game reaches
**T70**, whichever comes first (`expires:` T75). When it does, this section carries one row per question with
the number that decides it, the **chop table** (one row per chop, with the queue item that absorbed it), the
snapshot `docs/experiments/A5-final.json`, the A4-vs-A5 `--compare` line, and the divergences that are **not**
the variable.

**It must carry the two ways this variable can fail while looking successful**, because both are live:

- **a chop whose production went nowhere visible**: if the queue item changed or completed in the same turn,
  the gain is not separable, and the record says so rather than claiming the five-turn advance;
- **an economy that paid for the advance in compounding**: Q3 exists for exactly this, and a fast
  establishment beside a T65 economy is the variable's cost, not a win. The two are reported together or the
  attempt's claim is not made.
