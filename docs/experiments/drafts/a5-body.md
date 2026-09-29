Attempt **A5** of the military-production experiment (`docs/experiments/README.md`, section 3). A1-A4 are
`001-attempt-A1.md`, `002-attempt-A2.md`, `003-attempt-A3.md` and `004-attempt-A4.md`; the cross-attempt
report is `RETRO-2026-09-29.md`.

## Start: the shared start

0. `get_game_status`. **This attempt is measured from the experiment's shared start**:
   `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`. If the game does not stand on it, load that save
   (`restart_and_load`, or the save list) and say in the diary which turn the loaded save holds. Playing
   A5 on another position makes its numbers incomparable with A1-A4, which is the one thing the experiment
   cannot afford.
1. Then `get_diary` and one `scripts\orient.py` read.

## The one variable: where the chops go

**A5 sends the chops into units instead of infrastructure: `tactics/01`'s and `tactics/08`'s feature
removals are spent on the war-production city's army queue, under Governor Magnus with his `Groundbreaker`
ability (+50% yields from plot harvests and feature removals in the city he is established in), where the
same builder charges would otherwise be spent on that city's infrastructure.** `README.md`'s A5
row states the variable as *"Magnus' Groundbreaker: chops go into units instead of infrastructure"* and the
prediction as *"the establishment arrives 5+ turns earlier and the economy is behind by less than 5 turns
at T60"*. Everything else is held: the shared start, the settings (China/Qin, Prince, Pangaea Small, Quick,
two opponents), the **corrected** `tactics/01` (siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 /
recon 1, the ram only if one is already owned), and the war plan.

What the variable costs: builder charges spent on production rather than on improvements, the features
themselves and the yields they would have carried for the rest of the game, and the turns the builders are
away from the tiles the compounding cities need. What it is supposed to buy: the siege half of the
establishment five or more turns earlier than A2's T55, because a chop is production the queue does not
have to wait for.

**The enabler has to be recorded, not assumed.** `Groundbreaker` is Magnus's level-0 ability
(`DLC/Expansion1/Data/Expansion1_Governors.xml:40` and `:151`, `Level="0" BaseAbility="true"`, described as
"+50% yields from plot harvests and feature removals in city"), so it arrives with his appointment rather
than from a governor point. The record states the turn `appoint_governor` answered, the turn
`assign_governor` put him in the war city, and the turn `get_governors` reads `established=1` there. The
`GOV_PROMO` lines `get_governors` prints list only promotions not yet held, so the evidence that the
ability is in force is that `GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER` has dropped off that list
and that `promote_governor` with it answers `ERR:ALREADY_PROMOTED` - which is the record of the ability,
not a failure to report.

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, as in A3 and A4, and the record states whether the
executor matched them order by order.

**The pin is a condition of comparability, not a preference.** If the executor's first four production
orders are not `SCOUT`, `SLINGER`, `SETTLER`, `BUILDER` in that order, the record states the deviating
order and its turn on this line and the attempt is **not comparable** with A4-A7: it is re-run from the
shared start, and the record says which session is the discarded one and where the re-run begins. A
doctrine reason for the deviation is not enough - A3's run had one and still broke the pin. The variable
is the **destination of the chops**, not the opening.

## The hypothesis, with the numbers that falsify it

`README.md`'s window row for this attempt is *"the establishment turn against A2's T48/T53/T55, and the
economy at T60"*, bounded by *"a city kept or T70"*. A2's three numbers are Engineering and both Catapults
ordered on **T48**, the first Catapult completed **T53**, the second **T55** (`002-attempt-A2.md`), and
A2's first economy order came at **T55**.

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role (`siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1`, the ram conditional), as the instrument computes it from the diary's own `unit_composition` |
| Q2 | the establishment arrives at least **5 turns earlier than A2's T55 completion, i.e. by T50** | the instrument's establishment turn (read on every turn from the diary's `unit_composition`) is T51 or later, or it is never reached inside the window |
| Q3 | the economy is behind by **less than 5 turns**: the first non-unit production order lands **by T60** (A2's first economy order was T55) | the first `BUILDING`-or-`DISTRICT` order in the log is T61 or later, or the log holds none. The log records what the cities were asked for; the diary's `cities`/`districts` columns are the cross-check |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than ten turns** | the rule reads red ten or more times. Report the diary's own `gold_per_turn` beside it, because the two measures disagree: the rule only evaluates from T60 (`prompts/checks/turn-checks.md`) and this attempt ends at T70, so the diary's number is the one live over the whole window, and A1 and A2 sat under the +10 floor on every turn of theirs |

## What to do, in order

1. **Recon first** (`tactics/07`'s Gate 0, and the corrected table's recon row): the Scout west and
   north-west, with `get_map_area` for the tile and the first attack estimate or `get_staging_plan` for the
   pools. A5's question is the establishment turn, so a reachable city is the target; the walls are read
   when they are read.
2. **Put Magnus in the war city before the first chop.** `get_governors` first (it prints the `GOV_PROMO`
   line whose description is `+50% yields from plot harvests and feature removals in city`),
   `appoint_governor("GOVERNOR_THE_RESOURCE_MANAGER")`, then `assign_governor(...)` to the war city, and
   record the appointment turn, the assignment turn and the turn it reads `established=1`. He does not
   move off that city inside the window.
3. **Engineering -> `UNIT_CATAPULT` before any economy building** (H1; it held at A2's T48), and keep the
   war city's queue holding a **unit** for the whole chopping window: a chop banks production into whatever
   that queue holds, so `tactics/08`'s split is the frame - the war city builds the army, every other city
   compounds - and the record names the item in production at every chop.
4. **Chop into the army, and record each chop on its own line**: the city, the tile, the feature, the turn,
   the queue item the production went into, and the builder's remaining charges. `remove_feature` is
   refused on a tile outside the owning city's ring, so the city and the tile are named for every chop, and
   the establishment table is read again after each one.
5. **March and stage by `tactics/04`/`05`, fire by `tactics/06`**: screen in front, siege at range 2, the
   last firing tile filled first, then declare war, position that turn, and fire every turn the train can
   fire while the surplus units cut the supply line.
6. **Every ten turns**: `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` and the `10-TURN REVIEW`'s three
   questions, with numbers. Write the establishment line in the shape the instrument parses
   (`SELF_REPORT_RE` in `scripts/experiment-report.py`): `ESTABLISHMENT: siege a/2 melee b/2 ram c/1
   ranged d/4 cavalry e/1 at T<n>`, with the corrected table's other two rows beside it as `(anticav x/1,
   recon y/1)`. The `ram c/1` slot stays even though the ram is conditional - a line without it is not
   read at all - and the parser does not read anticav or recon, so those two are reported but not scored.

## The finish line, and what to leave behind

- The attempt ends when **a city is kept** (a `city_action` reply reads `KEEP|`) or the game reaches
  **turn 70**, whichever comes first. `expires:` is T75.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <this session> --from 1 --to <last turn> --step 10 --verdict --questions a5 --save docs/experiments/A5-final.json`
  (`--questions a5` is this attempt's own four rows above; if that mode is not in
  `scripts/experiment-report.py` yet - its `--questions` choices are `generic`, `a2`, `a3` today - add it
  with them, as `a2` and `a3` were added for theirs), run
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A4-final.json docs\experiments\A5-final.json`,
  write `docs/experiments/005-attempt-A5.md`, and add A5's half to the retro.
- Then retire this file and record the turn in the diary's `tooling` line.

## Honesty notes the programme has already paid for

- **A reply is not a result**: a landed attack has read `damage dealt:none`, a capture move has answered
  `BLOCKED` while the unit stood on the city. Judge from a later read and the pooled fields.
- **Say which measure a claim uses** - the gold floor has three numbers and they disagree.
- **The diary is shared** with A1-A4; the instrument attributes rows by session time.
- **A chop's production is only banked when the feature actually disappears**, and `remove_feature` on a
  tile outside the city's owned ring is refused, so the record names the city and the tile for every chop.
  No tool prints the size of the bank: `remove_feature` answers `OK:REMOVING_FEATURE|<feature> at x,y`, so
  the production gained is read from the item's turn count before and after, or the record says it is
  unread rather than estimating it.
- **A pinned opening has already been broken once** (A3: `UNIT_WARRIOR` as the fourth order at T15, with
  the pin in force and a doctrine reason in the planning line but no mention of the pin), which is why the
  pin now carries the re-run consequence above.
