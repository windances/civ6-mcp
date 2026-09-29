# TEMP TASK 035 - TEMP TASK 035 - attempt A4: the Encampment before the second siege unit, from the shared T1 start

added:     2026-09-30 (human instruction: 继续A3 ~ A7)
expires:   turn 115 - 30 turn(s) from T72, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: turn 110 is reached, or a city is kept (a city_action reply reads KEEP|) - whichever comes first
overrides: nothing: the design is docs/experiments/README.md's A4 row and it contradicts neither the directive
           nor A3's record. It does supersede the earlier attempts' stop-turn conventions - A1
           stopped at T40 and A2 ran to its capture - because this attempt's window is written from
           its own queue: Engineering ~T48, the train ~T55, the Encampment built after the second
           city, and the capture inside T110.
scope:     this match only, from the experiment's shared start evals/saves/ATTEMPT-A1-T1-settled.Civ6Save:
           attempt A4 - the same settings, the same pinned opening and the corrected tactics/01,
           with the Encampment's place in the queue (after the second city, where A3 builds it
           before) as the one variable

Attempt **A4** of the military-production experiment (`docs/experiments/README.md`, section 3). A1, A2 and
A3 are `001-attempt-A1.md`, `002-attempt-A2.md` and `003-attempt-A3.md`; the cross-attempt report is
`RETRO-2026-09-29.md`.

## Start: the shared start

0. `get_game_status`. **This attempt is measured from the experiment's shared start**:
   `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`. If the game does not stand on it, load that save
   (`restart_and_load`, or the save list) and say in the diary which turn the loaded save holds. Playing
   A4 on another position makes its numbers incomparable with A1-A3, which is the one thing the experiment
   cannot afford.
1. Then `get_diary` and one `scripts\orient.py` read.

## The one variable: the Encampment is built, in the war city, before the second siege unit

**A4 builds the Encampment - in the war city, and before the second siege unit completes - which is the
`prompts/tactics/08-war-and-the-home-front.md:81` reading of the doctrine, where the directive's build order
puts it last, "Encampment only when a war is actually near".** Everything else is held: the shared start,
the settings, the **corrected** `tactics/01` (recon 1, anti-cavalry 1, the ram conditional, siege 2 /
melee 2 / ranged 4 / cavalry 1), the war plan, and the target class.

**Why the old premise died, and it is a measurement.** This attempt's earlier draft said it built the
Encampment *after* the second city, "where the doctrine and A3 build it before". That is false: **no attempt
has ever built an Encampment at all.** Every session log of this match - `vigilant-sable-longbow-78`,
`sacred-garnet-vault-35`, `pale-pearl-aqueduct-92`, `volcanic-indigo-caravan-23`,
`flint-indigo-rampart-32`, `crumbling-emerald-parapet-16` and `eternal-scarlet-catapult-86` - holds **zero
`set_city_production` orders for `DISTRICT_ENCAMPMENT`**; the one raw mention of the string anywhere in those
logs is a `get_city_production` listing at A2's T68, which is not an order. "Before the second city" was an
arm nobody ran, so the old A4 would have measured its variable against nothing.

**Why nobody built one: the doctrine says two different things.** `tactics/08` gives the Encampment to the
war city - "The war city - the highest-production city - builds units, siege and the Encampment/Barracks, and
nothing else for the duration" (`prompts/tactics/08-war-and-the-home-front.md:81`) - and
`prompts/strategies/china-conquest/directive.md:63` says "Encampment and Barracks in the highest-production
city", with the same split again at `directive.md:331` (the sentence starts at `:330`). But the same
directive's build order says "growth first ..., then a **Campus** ..., then Commercial Hub, then Government
Plaza, then **Encampment only when a war is actually near**" (`:299`). A4 executes the first reading for the
first time.

The claim under test is `tactics/01:74-76` (`prompts/tactics/01-unit-production.md`): Great Generals are
earned mostly from Encampments and a general is **+1 movement and +5 combat strength to land units within
2 tiles**, so "an Encampment is not only defence, it is the cheapest combat bonus the army can buy". A4 asks
what that aura is worth against the turns the district and its general take from the war city's queue.

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, as in A3, and the record states whether the executor
matched them order by order. The variable is the **Encampment's place in the war city's queue**, not the
opening.

**The pin is a condition of comparability, not a preference.** If the first four production orders are not
`SCOUT`, `SLINGER`, `SETTLER`, `BUILDER` in that order, the record states the deviating order and its turn on
this line and the attempt is **not comparable** with A5-A7: it is re-run from the shared start, and the
record says which session is the discarded one and where the re-run begins. A doctrine reason for the
deviation is not enough - **A3's run had one and still broke the pin** (its fourth order was `UNIT_WARRIOR`
at T15, with the pin published and in force, and its `planning` line never mentioned the pin), which is why
this rule now carries the re-run consequence instead of asking for an explanation.

## The hypothesis, with the numbers that falsify it

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | T60 passes with the composition short in any required role |
| Q2 | **the Encampment is completed in the war city before the second siege unit completes**, and the record carries the district's tile, the turn it was ordered, the turn it completed, and the turn the game first offered it (`get_district_advisor` / `get_city_production`, with whatever prerequisite that read names - the tech requirement is read, never asserted here) | the window ends with no `DISTRICT_ENCAMPMENT` completed, or it completes after the second `UNIT_CATAPULT` - an aura that arrives after the train cannot be the thing that changed the assault |
| Q3 | **a Great General is recruited before the war opens, and it is never activated**; the record carries the turn it was recruited and where it stands relative to the siege units | no general is recruited before the first war declaration, or `activate` is called on one. An Encampment that yields no general by the first shot is the claim's mechanism missing, not its cost; and activating a general **retires the aura** (`AGENTS.md`: the aura is worth having while the unit is alive, and `activate` consumes it) - if one is activated, the record says so plainly |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns**, both measures reported, and the capture read against **A3's keep turn** in `003-attempt-A3.md` | the rule reads red ten or more times, or the diary's own `gold_per_turn` is not below the +10 floor (report both, as the two earlier attempts did); the capture half is falsified when A3's keep turn passes with no `KEEP|` in this attempt's log, and if A3 kept no city the record says so and the bound is **T80** |

## What to do, in order

1. **Recon first** (the corrected table's row, and `tactics/07`'s Gate 0): a Scout west and north-west,
   and read every city it finds - `get_map_area` for the tile, the first attack estimate or
   `get_staging_plan` for the pools. **A walled target is preferred** (that is A3's variable, and a walled
   city exercises the train harder), but do not spend the window looking for one: A4's question is the
   Encampment's turns and the aura, so a reachable city is the target.
2. **Found the second city early** - the pinned `SETTLER` is what founds it - and say in the diary which
   site and which turn. It is not the variable: step 3's war city is chosen by production, not by which city
   came first.
3. **Choose the war city and order the Encampment there as soon as the game offers it, and before the
   second `UNIT_CATAPULT`.** The war city is the highest-production city (`tactics/08:81`).
   `get_district_advisor` and `get_city_production` are the reads that say when the district is offered and
   what that read names as its prerequisite; record the turn and the source read for each of the offer, the
   order and the completion, and record the tile the district stands on.
4. **Engineering -> `UNIT_CATAPULT` before any economy building** (H1; it held at A2's T48 and is measured
   again in A3).
5. **March and stage by `tactics/04`/`05`** - screen in front, siege at range 2 - then declare war, position
   that turn, and **fire every turn the train can fire** while the surplus units cut the supply line. Keep
   the general with the stack: the aura reaches land units within 2 tiles, and a general that is activated
   is a general that is gone.
6. **Every ten turns**: `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` and the `10-TURN REVIEW`'s three
   questions, with numbers.

## The finish line, and what to leave behind

- The attempt ends when **a city is kept** (a `city_action` reply reads `KEEP|`) or the game reaches
  **T110**, whichever comes first. `expires:` is T115.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <this session> --from 1 --to <last turn> --step 10 --verdict --questions a3 --save docs/experiments/A4-final.json`
  (`--questions a3` is the instrument-read half - its Q2 reads the wall pool, its Q3 the first keep and its
  Q4 the gold floor - while this attempt's Q2 and Q3 are **record-read**: the Encampment from the log's
  `set_city_production` rows naming `DISTRICT_ENCAMPMENT`, and the general from `get_great_people` and the
  unit read), run
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A3-final.json docs\experiments\A4-final.json`,
  write `docs/experiments/004-attempt-A4.md`, and add A4's half to the retro.
- Then retire this file and record the turn in the diary's `tooling` line.

## Honesty notes the programme has already paid for

- **A reply is not a result**: a landed attack has read `damage dealt:none`, a capture move has answered
  `BLOCKED` while the unit stood on the city. Judge from a later read and the pooled fields.
- **Say which measure a claim uses** - the gold floor has three numbers and they disagree.
- **The diary is shared** with A1-A3; the instrument attributes rows by session time.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "TEMP TASK 035 - attempt A4: the Encampment before the second siege unit, from the shared T1 start" --instruction "继续A3 ~ A7" --slug attempt-a4-the-encampment-before-the-second-siege-unit --scope @docs/experiments/drafts/a4-scope.txt --overrides @docs/experiments/drafts/a4-overrides.txt --done-when @docs/experiments/drafts/a4-done-when.txt --why "the Encampment's place in the war city's queue, tested from the experiment's shared start" --expires-turn 115 --body-file docs/experiments/drafts/a4-body.md --cn @docs/experiments/drafts/a4-cn.md
     at: 2026-09-30T00:48:31+08:00
     chinese backup: prompts/tasks/cn/035-attempt-a4-the-encampment-before-the-second-siege-unit.cn.md
-->
