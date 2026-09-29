# TEMP TASK 038 - TEMP TASK 038 - attempt A7: two war cities instead of one, from the shared T1 start

added:     2026-09-30 (human instruction: 继续A3 ~ A7)
expires:   turn 115 - 30 turn(s) from T72, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: turn 110 is reached, or a city is kept (a city_action reply reads KEEP|, or the move's reply reads
           CAPTURE_MOVE ... CITY TAKEN) - whichever comes first
overrides: tactics/08's one war city: this attempt's variable is a second city whose queue is army units, and
           its whole question is whether that city's production outweighs the compounding it does
           not do. It contradicts nothing else in the directive, and it supersedes the earlier
           attempts' stop-turn conventions because this attempt's window is written from its own
           queue: the second war city founded or taken early, both cities producing army units, and
           the first capture inside T110.
scope:     this match only, from the experiment's shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save:
           attempt A7 - the same settings, the same pinned opening and the corrected tactics/01,
           with the number of war-production cities (two, against the one tactics/08 prescribes) as
           the one variable

Attempt **A7** of the military-production experiment (`docs/experiments/README.md`, section 3). A1-A6 are
`001-attempt-A1.md`, `002-attempt-A2.md`, `003-attempt-A3.md`, `004-attempt-A4.md`, `005-attempt-A5.md`
and `006-attempt-A6.md`; the cross-attempt report is `RETRO-2026-09-29.md`.

## Start: the shared start

0. `get_game_status`. **This attempt is measured from the experiment's shared start**:
   `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`. If the game does not stand on it, load that save
   (`restart_and_load`, or the save list) and say in the diary which turn the loaded save holds. Playing
   A7 on another position makes its numbers incomparable with A1-A6, which is the one thing the experiment
   cannot afford.
1. Then `get_diary` and one `scripts\orient.py` read.

## The one variable: two war cities instead of one

**A7 runs two cities whose queues are army units, on top of the single war city `tactics/08` prescribes:
the second war city is named on the turn it exists, and its queue is army units from then on.** The
`tactics/08` file states the doctrine this contradicts - *"The war city builds the war, and the other
cities build everything else"* - so this file's header carries it as an `overrides:` line, and the review
reads it as the attempt's design rather than as drift. `README.md`'s A7 row states the variable as *"two
war cities instead of one"* and the prediction as *"the second city's production outweighs the lost
compounding"*, and its window row is *"a city kept or T110: the second city has to contribute before the
number exists"*. Everything else is held: the shared start, the settings (China/Qin, Prince, Pangaea
Small, Quick, two opponents), the **corrected** `tactics/01` (siege 2 / melee 2 / anti-cavalry 1 / ranged
4 / cavalry 1 / recon 1, the ram only if one is already owned), and the war plan.

What the variable costs: the compounding the second city did not do, which is what its queue would
otherwise have held - a district or a building that compounds for the rest of the game - plus the
maintenance of the extra units and the city's own growth being spent on garrisons and screens. What it is
supposed to buy: army production running in parallel with the war city's, so the establishment and its
replacements arrive sooner, and so the first city can be kept before T80 by an army that can absorb a loss
and still fire.

The split is decided **once**, at the turn the second city exists, and written in the diary that turn: the
city, the turn it was founded or taken, and the queue each war city runs. `tactics/08`'s rule that a
compounding city's queue is never empty still holds for every city that is not one of the two.

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, as in A3-A6, and the record states whether the executor
matched them order by order.

**The pin is a condition of comparability, not a preference.** If the executor's first four production
orders are not `SCOUT`, `SLINGER`, `SETTLER`, `BUILDER` in that order, the record states the deviating
order and its turn on this line and the attempt is **not comparable** with A4-A7: it is re-run from the
shared start, and the record says which session is the discarded one and where the re-run begins. A
doctrine reason for the deviation is not enough - A3's run had one and still broke the pin. The variable
is the **second war city**, not the opening. (The pinned `SETTLER` is also the normal way the second war
city comes to exist; if the second city is taken instead, the record says which city and which turn.)

## The hypothesis, with the numbers that falsify it

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role (`siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1`, the ram conditional), as the instrument computes it from the diary's own `unit_composition` |
| Q2 | **two cities have each produced at least one army-role unit before the first city is kept**, and the record names the second war city, the turn it was founded or taken, and its first army order | the first `KEEP|` arrives with only one city holding an army-role order. Read per city from the log's `set_city_production` / `purchase_item` rows (the instrument's `military_city_spread.per_city`), with `get_units` or the diary's `unit_composition` as the cross-check that the second city's unit still exists |
| Q3 | the first city is kept **by T80** | T80 arrives with no `KEEP|` in the log |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns**, both measures, because a second war city means more units and more maintenance | the rule reads red ten or more times, or the diary's own `gold_per_turn` sits below 10 on ten or more turns of the window. Report both numbers and which turns each covers: the rule only evaluates from T60 (`prompts/checks/turn-checks.md`), so before T60 the diary's number is the only one live |

## What to do, in order

1. **Recon first** (`tactics/07`'s Gate 0, and the corrected table's recon row): the Scout west and
   north-west, `get_map_area` for the tile and the first attack estimate or `get_staging_plan` for the
   pools, and read the candidate's walls, HP and garrison before the deadline is written. A7's question is
   the keep turn, so a reachable city is the target.
2. **Name the two war cities on the turn the second one exists**, and write the split in the diary in
   these terms: which two cities, the turn the second was founded or taken, and the queue each
   one runs for the rest of the window. `tactics/08`'s "one war city" is deliberately widened here; the
   split is decided once and re-opened only when a ten-turn review says so.
3. **The second war city's queue is army units from that turn**: `set_city_production(city_id, "UNIT",
   ...)` per `tactics/01`'s establishment table, and record its first army order, every unit it completes,
   and - this is the variable's cost - what that queue would have built for the economy instead (the named
   district or building, and its turn estimate).
4. **Every city that is not one of the two war cities compounds** (`tactics/08` step 2): the next district
   or its building, no empty queue, builders keep coming and never follow the stack. Engineering ->
   `UNIT_CATAPULT` before any economy building in a war city (H1; it held at A2's T48).
5. **March and stage by `tactics/04`/`05`, fire by `tactics/06`**: screen in front, siege at range 2, the
   last firing tile filled first, then declare war, position that turn, and fire every turn the train can
   fire while the surplus units cut the supply line.
6. **Every ten turns**: `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` and the `10-TURN REVIEW`'s three
   questions, with numbers, plus `tactics/08` step 6's `WAR ECONOMY:` line (which names our cities building
   civilians while at war - with two war cities, the count is the split being checked). The establishment
   line is read by `SELF_REPORT_RE` in `scripts/experiment-report.py`, which takes **every `role
   held/target` token the line carries** - so write the rows that apply and **every one of them is scored
   against the record**, the two new cities' production included. **The numerator is units held in the
   field** - a unit still in production is not held and goes after the token in its own words
   (`siege 1/2, 1 building due ~T48`), never in the numerator; A3 and A4 both wrote `siege 1/2 building`
   with no siege unit built and were scored as claiming one.

## The finish line, and what to leave behind

- The attempt ends when **a city is kept** - either a `city_action` reply reads `KEEP|`, or the game
  resolves the capture itself and the move's reply reads `CAPTURE_MOVE ... CITY TAKEN` (when that happens
  no `KEEP|` ever appears and `resolve_city_capture` answers `NO_PENDING_CITY`; the city list is the
  confirmation) - or the game reaches
  **turn 110**, whichever comes first. `expires:` is T115.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <this session> --from 1 --to <last turn> --step 10 --verdict --questions a7 --save docs/experiments/A7-final.json`
  (`--questions a7` is this attempt's own four rows above, and the mode is in the instrument - it was added
  and verified before this attempt was published), run
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A6-final.json docs\experiments\A7-final.json`,
  write `docs/experiments/007-attempt-A7.md`, and add A7's half to the retro.
- Then retire this file and record the turn in the diary's `tooling` line.

## Honesty notes the programme has already paid for

- **A reply is not a result**: a landed attack has read `damage dealt:none`, a capture move has answered
  `BLOCKED` while the unit stood on the city. Judge from a later read and the pooled fields.
- **Say which measure a claim uses** - the gold floor has three numbers and they disagree.
- **The diary is shared** with A1-A6; the instrument attributes rows by session time.
- **The second war city's cost is the compounding it did not do**, so the record states what that city's
  queue would have built for the economy instead - the named district or building, and the turn it would
  have landed - rather than leaving the cost as an adjective.
- **The instrument's own `military_city_spread` block is the secondary measure**, beside the plain per-city
  counts: a city counts as a war city only when at least half of everything it was asked to build is
  army-role units (recon and civilian orders excluded, `scripts/experiment-report.py`). The plain count and
  the block disagree on a city that built one army unit and nothing else, and both are reported.
- **A pinned opening has already been broken once** (A3: `UNIT_WARRIOR` as the fourth order at T15, with
  the pin in force and a doctrine reason in the planning line but no mention of the pin), which is why the
  pin now carries the re-run consequence above.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "TEMP TASK 038 - attempt A7: two war cities instead of one, from the shared T1 start" --instruction "继续A3 ~ A7" --slug attempt-a7-two-war-cities --scope @docs/experiments/drafts/a7-scope.txt --overrides @docs/experiments/drafts/a7-overrides.txt --done-when @docs/experiments/drafts/a7-done-when.txt --why "whether a second war-production city pays for the compounding it costs, from the shared start" --expires-turn 115 --body-file docs/experiments/drafts/a7-body.md --cn @docs/experiments/drafts/a7-cn.md
     at: 2026-09-30T06:28:44+08:00
     chinese backup: prompts/tasks/cn/038-attempt-a7-two-war-cities.cn.md
-->
