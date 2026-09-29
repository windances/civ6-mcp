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

## The one variable: when the Encampment is built

**A4 builds the Encampment *after* the second city, where the doctrine and A3 build it before.** Everything
else is held: the shared start, the settings, the **corrected** `tactics/01` (recon 1, anti-cavalry 1, the
ram conditional, siege 2 / melee 2 / ranged 4 / cavalry 1), the war plan, and the target class.

The claim being tested is `tactics/01`'s: *"an Encampment is not only defence, it is the cheapest combat
bonus the army can buy"*, because Great Generals come mostly from Encampments and a general is **+1
movement and +5 combat strength to land units within 2 tiles**. A4 asks whether that aura is worth more
than the turns the Encampment takes from the second city.

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, as in A3, and the record states whether the executor
matched them order by order. The variable is the **Encampment's place in the queue**, not the opening.

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
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role |
| Q2 | **two cities' compounding beats the earlier general's aura**: the first city is kept **no later than A3's capture turn** | A3's keep turn passes with no `KEEP|` in this attempt's log. A3's number is in `003-attempt-A3.md`; if A3 could not keep a city at all, say so and use T80 as the bound |
| Q3 | the first city is kept **by T80** | T80 arrives with no `KEEP|` |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns** | the rule reads red ten or more times; report the diary's own `gold_per_turn` beside it, as the two earlier attempts did |

## What to do, in order

1. **Recon first** (the corrected table's row, and `tactics/07`'s Gate 0): a Scout west and north-west,
   and read every city it finds - `get_map_area` for the tile, the first attack estimate or
   `get_staging_plan` for the pools. **A walled target is preferred** (that is A3's variable, and a walled
   city exercises the train harder), but do not spend the window looking for one: A4's question is the
   capture turn, so a reachable city is the target.
2. **Found the second city early** - that is the variable's other half: the Encampment waits for it. Say in
   the diary which site, which turn, and what the Encampment would have cost there.
3. **Build the Encampment after the second city**, and record the turn it was *available* versus the turn
   it was started - the difference is the variable's cost.
4. **Engineering -> `UNIT_CATAPULT` before any economy building** (H1; it held at A2's T48 and is measured
   again in A3).
5. **March and stage by `tactics/04`/`05`** - screen in front, siege at range 2 - then declare war, position
   that turn, and **fire every turn the train can fire** while the surplus units cut the supply line.
6. **Every ten turns**: `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` and the `10-TURN REVIEW`'s three
   questions, with numbers.

## The finish line, and what to leave behind

- The attempt ends when **a city is kept** (a `city_action` reply reads `KEEP|`) or the game reaches
  **turn 110**, whichever comes first. `expires:` is T115.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <this session> --from 1 --to <last turn> --step 10 --verdict --questions a3 --save docs/experiments/A4-final.json`
  (`--questions a3` is the closest question set - its Q2 reads the wall pool and its Q3 the first keep;
  A4's own Q2, the capture turn against A3's, is read off the two records), run
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A3-final.json docs\experiments\A4-final.json`,
  write `docs/experiments/004-attempt-A4.md`, and add A4's half to the retro.
- Then retire this file and record the turn in the diary's `tooling` line.

## Honesty notes the programme has already paid for

- **A reply is not a result**: a landed attack has read `damage dealt:none`, a capture move has answered
  `BLOCKED` while the unit stood on the city. Judge from a later read and the pooled fields.
- **Say which measure a claim uses** - the gold floor has three numbers and they disagree.
- **The diary is shared** with A1-A3; the instrument attributes rows by session time.
