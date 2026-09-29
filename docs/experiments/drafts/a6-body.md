Attempt **A6** of the military-production experiment (`docs/experiments/README.md`, section 3). A1-A5 are
`001-attempt-A1.md`, `002-attempt-A2.md`, `003-attempt-A3.md`, `004-attempt-A4.md` and
`005-attempt-A5.md`; the cross-attempt report is `RETRO-2026-09-29.md`.

## Start: the shared start

0. `get_game_status`. **This attempt is measured from the experiment's shared start**:
   `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`. If the game does not stand on it, load that save
   (`restart_and_load`, or the save list) and say in the diary which turn the loaded save holds. Playing
   A6 on another position makes its numbers incomparable with A1-A5, which is the one thing the experiment
   cannot afford.
1. Then `get_diary` and one `scripts\orient.py` read.

## The one variable: the first siege unit is bought, not built

**A6 buys the first siege unit with gold instead of waiting for a queue:
`purchase_item(city_id, "UNIT", "UNIT_CATAPULT")`, where A1-A5 produced theirs; the second Catapult is
produced as before, because the arithmetic below does not allow more than one purchase.** The variable has
two halves and both are on the record: the gold is **raised** deliberately (nothing else is bought, the
treasury is not spent) and then **spent in one purchase**. Everything else is held: the shared start, the
settings (China/Qin, Prince, Pangaea Small, Quick, two opponents), the **corrected** `tactics/01`
(siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1, the ram only if one is already
owned), and the war plan.

What the variable costs: the treasury, and nothing else is bought with it. What it is supposed to buy: the
first Catapult four or five turns earlier than A2's T53 completion, because a purchase arrives the turn the
gold exists and the queue does not have to be waited out.

`README.md`'s A6 row states the variable as *"the siege train is bought with gold, not produced"* and the
prediction as *"the war opens 5+ turns earlier at the cost of a negative `carrying-capacity` window"*. The
arithmetic below restates the second half of that claim: on this start the money buys **one** Catapult, not
a train, and the war's opening turn is compared against **A3's**, not against A2's T60 (see Q3).

### The arithmetic the attempt must state before it spends anything

The prices and balances below are A2's own, quoted rather than re-derived; they are the attempt's pre-flight
estimate and not its facts - **the record reads them again in its own position and says so if they differ**.

- One `UNIT_CATAPULT` costs **120 production** and **320 gold** to buy - A2's own `get_city_production`
  reply at T68 (`.civ6-mcp-data/log_china_911679432_volcanic-indigo-caravan-23.jsonl`).
- A2's treasury: T1 6, T10 51, T20 101, T30 160.8, **T40 243.4**, **T50 274.4**, T60 229.8, T68 294.8, at
  +5.0, +5.0, +6.3, +8.9, +6.1, +8.0 and +6.0 gold/turn (`docs/experiments/A2-final.json`, the `economy`
  rows).
- A2 ordered both Catapults on **T48** in two different cities and they completed **T53** and **T55**.
- A2 had no improved luxury resource to sell (its T20-T30 diary rows carry `luxuries={}`), so the funding
  route is income and not spending, not trade.
- Therefore **two purchased Catapults (640 gold) by T50 is arithmetically impossible on this start**, and
  one (320 gold) is only just reachable, the prediction putting it at about **T48-T50**: on A2's own path
  the 320th gold is never on hand at all (the peak is 294.8 at T68, and the T60 row falls back to 229.8), so
  a purchase inside the window means this attempt's own treasury runs ahead of A2's - which is what the
  variable's first half is for. The record states the turn the treasury reaches 320, and that turn is Q2's
  number.
- **A3 has since measured the other half, and it is the reason this prediction is live rather than
  impossible**: at **T48** its treasury held **347 gold** and it bought a Catapult, the reply reading
  `PURCHASED|UNIT_CATAPULT|cost=320g (had 347g)`. So the price *is* payable on this start once the treasury
  is not spent elsewhere - no trade, no luxury sale, just income and restraint. What A6 adds is buying the
  **first** unit rather than the second, and the record should read A3's purchase as the evidence that the
  funding arm exists while noting that A3 is therefore not a production-only baseline.

## The opening build is pinned

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, as in A3-A5, and the record states whether the executor
matched them order by order.

**The pin is a condition of comparability, not a preference.** If the executor's first four production
orders are not `SCOUT`, `SLINGER`, `SETTLER`, `BUILDER` in that order, the record states the deviating
order and its turn on this line and the attempt is **not comparable** with A4-A7: it is re-run from the
shared start, and the record says which session is the discarded one and where the re-run begins. A
doctrine reason for the deviation is not enough - A3's run had one and still broke the pin. The variable is
the **first siege unit's gold**, not the opening.

## The hypothesis, with the numbers that falsify it

`README.md`'s window row for this attempt is *"the turn the war opens (the train paid for with gold)"*,
bounded by *"a city kept or T70"*. A2's numbers beside it are the first Catapult completed **T53**, the
second **T55**, and the war opening **T60** (`002-attempt-A2.md`); the arithmetic above is why the second
unit stays in the queue, and `0f214eb` is why the war is compared against A3 rather than against that T60.

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role (`siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1`, the ram conditional), as the instrument computes it from the diary's own `unit_composition` - bought and produced units count alike |
| Q2 | **the first siege unit is bought**, with the arithmetic on the record: the price (320 gold), the treasury on the purchase turn, the income at that moment, and the purchase turn the reply prints as `cost=N (had M)`. Prediction: bought **by T50**, against A2's first Catapult completing T53 | the train arrives with no siege purchase row at all (it was produced), or the first purchase turn is later than T50. The row names the city id, the reply's `cost=N (had M)`, and the balance the purchase left |
| Q3 | **the train is complete (siege 2/2) no later than A2's T55** - the second unit is still produced in parallel - and the war opens as early as the train and the march allow, with **A3's war-opening turn as the baseline** | the second Catapult completes after T55 (read from the log's `set_city_production` order and the completion line), or the war opens later than A3's opening turn. A3's number is in `003-attempt-A3.md`; if A3 opened no war inside its window, say so and use the train's completion turn as the bound. The baseline is A3 and not A2 because **A2's T60 included the six turns lost to the city-state war-declaration tool bug that `0f214eb` fixed before A3 ran**, so any attempt after that fix is compared against A3 |
| Q4 | the accepted cost: the purchase empties the treasury within a few turns of the price being reached, so `carrying-capacity` red on **more turns than A2's ten** and the diary's `gold_per_turn` below the +10 floor over the funding window - report both measures | the rule's red count is not above A2's ten (the count up to T68 in `002-attempt-A2.md` and `A2-final.json`; the retro's six is that same rule counted over T59-T64 - two windows of one measure, not two measures), or the diary's own `gold_per_turn` is not below the floor over the funding window. The rule is gated `when: turn() >= 60` (`prompts/checks/turn-checks.md`) and can go red at most once a turn, so inside this attempt's T70 window its count has a ceiling of eleven - the diary's number is the measure live over the whole funding window, which starts the turn the gold is raised |

## What to do, in order

1. **Recon first** (`tactics/07`'s Gate 0, and the corrected table's recon row): the Scout west and
   north-west, `get_map_area` on the tile and the first attack estimate or `get_staging_plan` for the
   pools. A6's question is the war's opening turn, so a reachable city is the target.
2. **Take the shortest line to Engineering and hold the war city's queue for the siege half.** When the
   tech lands, buy rather than build: `purchase_item(city_id, "UNIT", "UNIT_CATAPULT")`, and record the
   turn, the city id and the reply's `cost=N (had M)`. The variable's first half is the funding: if the
   treasury is short, record the shortfall and the turn the gold crosses the price, and buy nothing else
   while that is being waited for.
3. **One purchase, and it is the first gun**: the corrected table's siege row is 2, so the second Catapult
   is still produced (`tactics/01` production order 1) while the bought one arrives - the record states the
   purchase turn and the treasury at it, and the turn the produced one completes. The screens are built,
   not bought (`tactics/01` production order 2), and nothing else is bought while the first Catapult is
   unbought.
4. **The home front runs on `tactics/08`'s split** - the war city keeps the army queue, every other city
   compounds and nothing leaves a queue empty. The gold belongs to the one purchase and to nothing else
   inside the funding window, which is the variable's second half; `tactics/01`'s named upgrade waits
   behind it, or the record says why it did not.
5. **March and stage by `tactics/04`/`05`, fire by `tactics/06`**: screen in front, siege at range 2, the
   last firing tile filled first; declare war, position that turn, attack the next, and fire every turn
   the train can fire while the surplus units cut the supply line.
6. **Every ten turns**: `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` and the `10-TURN REVIEW`'s three
   questions, with numbers. The establishment line is read by `SELF_REPORT_RE` in
   `scripts/experiment-report.py`, which takes **every `role held/target` token the line carries** - so
   write the rows that apply (`siege`, `melee`, `ranged`, `cavalry`, `anticav`, `recon`, and `ram` when the
   empire owns one) and **every one of them is scored against the record**. A bought unit counts in its
   role exactly as a produced one does, which matters here: the purchase is the variable and the line is
   where a reader sees whether the train it bought is the train on the table. **The numerator is units
   held in the field** - a unit still in production is not held and goes after the token in its own words
   (`siege 1/2, 1 building due ~T48`), never in the numerator; A3 and A4 both wrote `siege 1/2 building`
   with no siege unit built and were scored as claiming one.

## The finish line, and what to leave behind

- The attempt ends when **a city is kept** - either a `city_action` reply reads `KEEP|`, or the game
  resolves the capture itself and the move's reply reads `CAPTURE_MOVE ... CITY TAKEN` (when that happens
  no `KEEP|` ever appears and `resolve_city_capture` answers `NO_PENDING_CITY`; the city list is the
  confirmation) - or the game reaches
  **turn 70**, whichever comes first. `expires:` is T75.
- At the end: take the snapshot with
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <this session> --from 1 --to <last turn> --step 10 --verdict --questions a6 --save docs/experiments/A6-final.json`
  (`--questions a6` is this attempt's own four rows above, and the mode is in the instrument - it was added
  and verified before this attempt was published), run
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A5-final.json docs\experiments\A6-final.json`,
  write `docs/experiments/006-attempt-A6.md`, and add A6's half to the retro.
- Then retire this file and record the turn in the diary's `tooling` line.

## Honesty notes the programme has already paid for

- **A reply is not a result**: a landed attack has read `damage dealt:none`, a capture move has answered
  `BLOCKED` while the unit stood on the city. Judge from a later read and the pooled fields.
- **Say which measure a claim uses** - the gold floor has three numbers and they disagree.
- **The diary is shared** with A1-A5; the instrument attributes rows by session time.
- **Gold spent on a unit is gold not spent on anything else**, so the treasury is recorded at every
  purchase and each purchase is named with its city id: `purchase_item` itself answers
  `OK:PURCHASED|<item>|cost=N (had M)`, which is the record of both numbers, and the diary's own `gold`
  for that turn is the cross-check.
- **Buying a unit does not exempt it from the establishment table's counts.** The establishment reads the
  units the empire holds, whatever produced them, and the instrument counts `purchase_item` as a production
  order, so a bought Catapult fills the siege slot and appears in the same order table as a built one.
- **A pinned opening has already been broken once** (A3: `UNIT_WARRIOR` as the fourth order at T15, with
  the pin in force and a doctrine reason in the planning line but no mention of the pin), which is why the
  pin now carries the re-run consequence above.
