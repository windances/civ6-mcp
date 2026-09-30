# Military production experiments — the protocol

**One question:** for a China game played to a military victory, what is the *optimal production
strategy*? The doctrine already answers it in prose (`prompts/tactics/01-unit-production.md`,
`docs/china-production-by-victory.md` under the military section, `docs/production-strategy.md`).
This directory is where those answers are **tested against a match and corrected**, one variable at
a time, with every attempt kept so a later attempt can be compared to it.

Nothing here is a new instrument. The loop already writes everything an attempt is judged on:

| raw record | what it holds |
|---|---|
| `.civ6-mcp-data/diary_<game>.jsonl` | one snapshot row per civilisation per turn - the whole economy |
| `.civ6-mcp-data/log_<game>_<run>.jsonl` | every tool call with the tool's own reply - the rules that failed, the orders refused, the city kept |
| the turn-1 save in `evals/saves/` | the attempt itself, replayable |
| `prompts/tasks/tmp/` | what the session was told to do |

**Two things about that log that cost three probes to learn** (measured 2026-09-29, driving the server's
own tool wrappers outside a session):

- **It only starts once the game is bound, and `get_game_overview` is what binds it.** `LocalSink`
  buffers every event until `bind_game()`, so a run of read tools that never calls the overview logs
  nothing to disk at all - the calls succeed and the file simply is not there.
- **It only goes to `CIV_MCP_DATA_DIR`.** That is `LOCAL_DIR`, read once at import; a real session gets
  it from `dsh/civ6.cordis.yml:18` as `process.cwd()/.civ6-mcp-data`, and anything driving the wrappers
  by hand has to set it or the rows land in `~/.civ6-mcp` where nothing expects them.

Both matter because **the doctrine checks read this log, not the diary**: which unit was ordered, whether
a ram was ever bought, how many cities were asked for units. The diary holds what the empire has; the log
holds what it asked for. A run that produces diary rows but no log rows - `scripts/auto-turns.py` calls
`GameState` directly, so that is exactly what it does - can be judged on the economy and the army it
ended up with, and **not** on the ordering the doctrine is about.

## 1. The settings, fixed for every attempt

| Parameter | Value | Why this value |
|---|---|---|
| Civilisation | China, Qin (Unifier) | the doctrine under test is written for this kit (Great Wall, Crouching Tiger, Dynastic Cycle) |
| Map | Pangaea, **Small** | one landmass, so a conquest is walkable; small keeps the distances inside a window (the 021 expedition died of distance, 30-40 tiles) |
| Opponents | **2** | as instructed; 3 players total, so a single conquest is a real step toward the victory |
| Difficulty | **Prince** | "moderate" is the middle of the eight levels, and it is the repo's Ground Control baseline, so the numbers are comparable |
| Speed | Quick | the repo's other captures are Quick |
| Victory | Domination only | one measurable goal; nothing else can end the attempt early |
| Start era | Ancient | the compounding decisions are the point |
| Barbarians | On | a camp is a target in the doctrine, and its units are a cost |
| City-states | Default for map size | suzerainty and envoys are part of the production picture |
| Game modes | None | - |

Recorded per attempt: the seed, the turn-1 save name, and the settings actually used (read back
from the game, not from this table - the table is the intent).

## 2. One starting position for every attempt

**Every attempt starts from the same save**: `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`, taken at
turn 1 immediately after the capital was founded. A fresh match per attempt would put a different map,
different neighbours and different land under the variable being tested, and a difference in the
outcome would then have two candidate causes with no way to separate them. Loading the same save holds
the map, the start position, the capital site, the opponents and the difficulty constant, so the only
thing that moves between attempts is the thing the attempt changed.

**Why the capital is already founded in that save.** Where the first city goes is the largest early
decision there is, so it must not be one of the variables. It is also not a contentious one: the game's
own `get_settle_advisor` ranks the Settler's tile **first** for this start - `(60,22)` at **score 190**
against 177 for the runner-up, fresh water, defence 5, with MAIZE, SUGAR, STONE and DYES in reach - so
founding in place is the tool's own first answer, and every attempt inherits it. 西安 was founded there
on 2026-09-29, and `ATTEMPT-A1-T1.Civ6Save` (the position *before* that, settler still standing) is kept
beside it as the record of the untouched start.

**How an attempt is started** (the loading is the human's call, like every other load in this repo):

1. load `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` in the game;
2. publish the attempt's own task file (`scripts/temp-task.py add ...`) - the `IN FORCE NOW` line is
   what carries it into a running session, not the file's presence;
3. the session plays to that attempt's stop, and the report is taken from the record as in section 4.

**The residual confound, written down so nobody forgets it.** The seed fixes the map, not the history:
after turn 1 the AI's choices and the combat rolls diverge from the previous attempt, and a run that
meets a barbarian camp the last one missed is not a worse strategy. A finding therefore rests on the
**process** metrics - the establishment turn, the order the parts of the army were asked for, the
turns under the gold floor - and on the economy at fixed turns, **not on the final outcome**. "It lost
the city" is not a datum about a production doctrine unless the process numbers explain why.

**One consequence of sharing a save, which bites if it is forgotten.** Attempts share a game key -
`<civ>_<seed>` - so they share `diary_<game>.jsonl`, and **each attempt overwrites the turn rows the
last one wrote**. An attempt's numbers therefore have to be snapshotted *while it is the current one*:

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run <session> --save A1.json
```

`--save` writes the whole report as JSON - it is the attempt's record, so the review quotes it rather
than re-deriving anything later; `--compare A1.json A2.json` prints one line per attempt on the same
columns; `--run` narrows the log to one session, which is how the doctrine checks stay inside the
attempt they belong to. The diary itself is not attempt-scoped and cannot be made so.

## 3. The one variable per attempt

An attempt changes **exactly one** thing. Everything else is the doctrine as written, so a
difference between two attempts has one candidate cause.

The doctrine's testable claims, each with the file that makes it:

| # | Claim | Written in |
|---|---|---|
| H1 | **Siege first**: "anything the assault is missing, first" - the train exists before the war | `tactics/01` §Production order 1-2 |
| H2 | **Establishment**: siege 2 / melee 2 / **anti-cavalry 1** / ranged 4 / cavalry 1 / **recon 1** - and the ram only if one is already owned | `tactics/01` §The establishment (**corrected 2026-09-29 after A2**: the ram left the required table because the same file forbids buying one, so its slot made "complete" unsatisfiable; recon and anti-cavalry entered it because Gate 0 needs a city actually seen and a Heavy Chariot next to the train needs an answer) |
| H3 | **Encampment early** - it is the cheapest combat bonus (the general's +1 MP / +5 CS aura) | `tactics/01` §Numbers |
| H4 | **Upgrade beats build** - an old unit at full health plus gold is a new unit without a queue | `tactics/01` §Numbers |
| H5 | **No ram or tower is bought** - the Catapult is the wall-breaker | `tactics/01` §Production order 1 (human instruction) |
| H6 | **One war city**; everything else compounds | `tactics/08` |

| Attempt | The one variable | Hypothesis to falsify |
|---|---|---|
| **A1** | none - the doctrine as written | the establishment is complete by T60 and the first city falls by T80 |
| **A2** | **the target's distance alone** - same save, same doctrine, but the objective is the nearest *city* (a city-state inside a dozen tiles) instead of the nearest rival capital, which this map puts 33 tiles away | the siege half becomes reachable inside a sixty-turn window once the target is inside ~12 tiles: siege 2/2 and the first city kept by T80 |
| **A3** | **the target's defences** - a *walled* city, everything else held (same doctrine, same save family, the corrected table) | the train's wall phase, which A2 never ran because its target read `walls: none`, changes the arithmetic in a measurable way: the first city kept **no earlier** than A2's T68 and **no later than T80**, with the wall pool's turn count on the record |
| **A4** | **the Encampment is built, in the war city, before the second siege unit** - the doctrine's own prescription executed for the first time | the aura pays for the district: the first city falls **no later than A3's keep turn**, with a Great General recruited (and never activated) before the war opens |
| **A5** | **Magnus in the war city** - his base ability Groundbreaker (+50% to feature removals) with the chops going into units instead of infrastructure | the establishment arrives 5+ turns earlier than A2's T55 completion and the economy is behind by less than 5 turns at T60 |
| **A6** | **the first siege unit is bought with gold, not produced** - the arithmetic below allows no more than one | the first siege unit is in hand before A2's T53 completion, funded deliberately out of a treasury that reached 243 at T40 and 274 at T50 against a 320g price; the train is complete no later than A2's T55, and the purchase's cost shows as a longer negative `carrying-capacity` window |
| **A7** | two war cities instead of one | the second city's production outweighs the lost compounding |
| **A8** *(published 2026-09-30 as task 040; in progress)* | **the city count: three cities, settled first** - the pinned opening is overridden to a second Settler and the third city's queue is economy, not army. The programme has held the city count fixed at two in every attempt: **no second Settler was ever ordered**, and the three third cities in A3/A4/A7 were all **captured** | **a third city that is settled pays for itself where one that is captured does not, and on the way it funds the second gun.** The **site is chosen on the turn the Settler is ordered** - the best legal one, nearest within ~10 score of it - because the only pre-flight read was taken with **three** cities standing and is therefore stricter than A8's two-city position; the far cluster it named is **20 tiles from the capital**, which is a fifteen-to-twenty-turn walk. **The two turns are derived from the founding turn `F`, not the calendar**: the purchase deadline is `max(T58, F+25)` and the gold floor is read at **T50 if `F <= 28`**, else at the ten-turn row at or after `F+22`, against A7's value at that same turn (A7: 8.1 / 4.1 / 2.1 / 24.4 at T50/T60/T70/T80). **And the number that discriminates at the horizon**: at **T110**, A8's `science`, `pop` and `gold_per_turn` each exceed A7's - both runs end holding three cities, and the difference is **how the third was obtained**. **`gpt_T40` is a prediction, not a bar** (at or below A7's 6.1). Falsified if the purchase misses its deadline, if it was built rather than bought, if `gpt` at the gold-floor turn is not above A7's there, or if any T110 figure is at or below A7's. **The pre-flight that unblocked this row was taken at T69 of the A7 continuation**; A3-A7's own ledger is `drafts/A8-A9-city-count.md` and the task draft is `drafts/a8-body.md` |
| **A9** *(proposed 2026-09-30, published only if A8 runs)* | **the city count, one more dose: four cities, settled first** | the fourth city's first army-relevant order arrives **before** the third city's, and `gpt_T50` is at least **3** above A8's - i.e. the curve has not yet turned. Falsified if city #4's first army order is later than city #3's, or if the fourth site is dry. **The pre-flight arithmetic predicts A8 and A9 both lose the first keep** - three Settlers cost more queue time than the whole siege train, and the settle advisor's top ten is one cluster at a time (the T15 near cluster is exhausted by our own cities; the T69 read's cluster is 11-14 tiles west) - which is why what they are worth if they fail is the **response curve**: the programme has one point (two cities) and no slope. **What the pre-flight corrected: the land does not kill the dose-response, distance does** - and A8's own correction is the sharper form of it: the third city may not be a satellite at all, so its claim is carried by the T110 comparison rather than by a T50 reading |

**A6's claim was cut to its arithmetic before the attempt was published** (2026-09-29), and the cut is part
of the finding. The design's first form - "the siege train is bought with gold" - cannot happen on this
start: `UNIT_CATAPULT` is 120 production and **buy: 320g** (A2's own T68 production read), while A2's
treasury reached **243.4 at T40** and **274.4 at T50** - and **never held 320 at all** (its peak inside the
window was 294.8 at T68) - on 5-9 g/turn with no improved luxury to sell. So one purchase is **not
reachable on A2's own path**, and buying one by T50 means this attempt's treasury has to run ahead of A2's:
that is the variable's first half (fund the purchase deliberately - buy nothing else, keep the army's
maintenance down - and state the turn the price is actually reached). **Two (640g) are arithmetically
impossible before about T70.** A6 therefore buys the **first** unit and produces the second, and its claim
is a five-turn gain on one unit - if the funding can be found at all - rather than a five-turn-earlier war.
This is A1's "P2 impossible by arithmetic" arriving one attempt later and one level down, and it was found by
pre-flight arithmetic rather than at hour three. **A3 then measured the funding arm for real** (T48 of its own
run): its treasury held **347g**, and it bought a Catapult for **`cost=320g (had 347g)`** - so on this start
the price *is* payable around T48 once the treasury is not spent elsewhere, and A6's prediction (bought by
T50) is a live question rather than an impossibility. A6's variable stays distinct because **A3 bought the
second unit where A6 buys the first**, and A3's record notes the overlap: an attempt that has already
exercised a purchase is not a clean "production-only" baseline for the attempt that varies purchasing.
**A4-A7 also
compare a war's opening turn against the previous attempt, not against A2**: A2's T60 included six turns
lost to the city-state war-declaration bug that `0f214eb` fixed before A3 ran, so A2 is no longer a clean
war-timing baseline - the fixed tool is part of what A3 onward plays with.

**A4's premise was false, and the measurement is the finding** (2026-09-29, found before publication the same
way A6's arithmetic was). A4's first form said it would build the Encampment *after* the second city "where
the doctrine and A3 build it before". **No attempt has ever built an Encampment at all**: across all seven
session logs of this match - A1, A2, A3 and the abandoned branches - there are **zero** `DISTRICT_ENCAMPMENT`
orders. So the "before the second city" arm does not exist and the old A4 would have measured its variable
against nothing. What does exist is the doctrine's own prescription, stated **twice with different timings**:
`tactics/08:81` puts the Encampment *in the war city's war queue* ("builds units, siege and the
Encampment/Barracks, and nothing else for the duration") while the directive's build order puts it **last**
("then Encampment only when a war is actually near", `directive.md:299`) even as the same file also lists it
with the war city's queue (`:63`, `:331`). **A4 therefore executes `tactics/08`'s reading for the first
time** - the Encampment completed in the war city before the second siege unit - and its mechanism question
is separate on purpose: an Encampment that yields no Great General by the first shot is the claim's mechanism
missing (`tactics/01:74-76`: +1 movement and +5 combat strength to land units within 2 tiles), not its cost.
**The contradiction itself is owed a reconciliation** - the same class as the two establishment tables that
still disagree - because an obedient session reading `tactics/08` and one reading the directive's build order
will do different things, which is why three attempts did neither.

**A3 was re-scoped after A2** (2026-09-29), and for the same reason A2 was re-scoped after A1: the
question the attempt was built to ask must be *askable*. A2 held H1 and took its city, but its target had
no walls, so the wall phase - the reason the train exists - never executed, and what defended the city
instead (a garrison that moved in on the final turn, a six-unit field army, ~20 HP of healing a turn while
a hex stayed open) are three things `tactics/01`'s table had no slot for. The Encampment variation moved
down the queue behind the one the experiment has not yet measured; a variable is only worth an attempt if
its hypothesis can be falsified by a number, and "the wall phase" is not yet a number.

A variable is only worth an attempt if the hypothesis can be **falsified by a number** in section 4.
An attempt whose hypothesis cannot fail is not run.

**Each attempt's window is written from its own question, and four of the remaining five can stop early.**
Playing from the shared T1 start costs roughly seventy turns before the siege train exists, so the window
is the expensive part of an attempt and it should be no longer than the question:

| attempt | what it measures | the window its task file sets |
|---|---|---|
| A3 | the wall phase: the wall pool's turn count, and the keep inside T68-T80 | a walled city kept, or **T110** (the walled target may not exist before then) |
| A4 | the capture turn, Encampment before vs after the second city | a city kept, or **T110** - its number *is* the capture turn |
| A5 | the establishment turn against A2's T48/T53/T55, and the economy at T60 | a city kept or **T70**: both numbers exist by the establishment plus one ten-turn review |
| A6 | **the turn the first siege unit is bought**, and the train's completion against A2's T55 | a city kept or **T70**: the question is answered the turn the first Catapult is bought |
| A7 | whether a second war city's production outweighs the lost compounding | a city kept or **T110**: the second city has to contribute before the number exists |
| A8 | the third city's contribution arm - the second siege unit bought with gold and in hand by **its derived deadline** `max(T58, F+25)`, the gold floor at **T50 or `F+22`**, and the T110 trio against A7's | **T110** - the claim's last number (A8's `science`, `pop` and `gold_per_turn` against A7's at the same turn) cannot be read before then, so the attempt runs to the horizon and the purchase is recorded on the way. Both of the claim's turns are derived from the third city's founding turn `F`, because a city that lands late cannot have a Market by T50 and a fixed window would score it as a failure of the market rather than of the site |
| A9 | the fourth city's contribution turn against the third city's | a second purchase or **T110**: city #4's first army order lands around **T64** by the measured lag, so a shorter window would end before the variable reports |

A window shorter than the question is what A1's arithmetic note and A2's T40 checkpoint both caught; a
window longer than the question is only wall-clock, and the programme has five attempts to run.

**A2 was re-scoped at T37 of A1, and that is the experiment working rather than changing its mind.**
A1's mid-window finding is that **the map, not the plan, decides whether the capture half is answerable
at all**: the only rival capital is 33 tiles west behind five city-states, no rival has been met by T37,
and the siege half of the establishment cannot start before Engineering lands around T42 - so no amount
of production discipline inside A1 could produce a city by T80 (the evidence is in
`001-attempt-A1.md`). Running a *plan* variation next would stack a second unanswerable window on the
first. A2 therefore changes **one thing that makes the question answerable** - the target's distance -
and holds everything else: the same save, the same doctrine as written, the same executor. Where the
plan variations go is after the question is answerable, not before.

**The variable is not the only thing that moves, and that is measured rather than assumed.** A1 and A2
ran under "the same doctrine as written" and their opening builds still differ: A1 asked for `SCOUT T1,
SLINGER T5, SETTLER T6, BUILDER T15, GRANARY T18, WARRIOR T20`, A2 for `WARRIOR T1, SLINGER T7, SETTLER
T11, BUILDER T18` - the same kinds in the same order **except the recon unit replaced by a second melee**,
and every later slot 1-5 turns later. By T10 the two attempts already differ in composition (military 34
against 31), before the target has had any effect at all. The doctrine fixes *what the army is made of*
(H2's table) and not *what the city is asked for first*, so "one variable" needs the opening written down:
**from A3 on the task file pins the first four production orders, and the attempt's record says whether
the executor matched them.** A2 carries the deviation and reads its verdicts with it in hand - which is
why a difference between A1 and A2 is a candidate cause, not a single cause.

Two consequences to write into A2's task file rather than discover in it:

- **A city-state is a legitimate target for this experiment and not for the standing directive.** The
  preset says city-states are not conquest targets because a *victory* needs the rival capitals; a
  production experiment needs a city it can reach. That is exactly what a task file's `overrides:` line
  is for, so A2's file must say so explicitly, and the review must not read the deviation as drift.
- **The nearest city has to be measured first, not assumed.** `get_map_area` and the map dump both give
  the coordinates; the ruler for "how many turns away" is `get_staging_plan`, and the deadline is
  written from its answer. That is `AGENTS.md`'s existing rule - *count the turns from the queue, not
  from the calendar* - applied to the target instead of to the build.

## 4. What is measured, and when

Every attempt reports the same table, extracted by the same command:

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --step 10
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --verdict
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --from 1 --to 60 --json
```

* **The two decisive numbers.** The report computes them itself, from the record: **the establishment
  turn** - checked on *every* turn, because a table that fills on T47 must not be reported as filling
  on T50 - and **the turn the first enemy city was kept**, read from the tool reply. The session's own
  diary line is a cross-check on those, not their source: an instrument that measures beats an agent
  reporting on itself.
* **The verdict** - `--verdict` answers the attempt's predictions from the record. Its limits are
  passed in (`--expect-est`, `--expect-city`, `--expect-gold-red`), never baked in, because a later
  attempt states its own numbers and a window *inside* an attempt is not the attempt's end. Two
  honesties it prints for itself: `P1` measures the turn a siege unit was **ordered** - read from the
  log's own production calls, because the doctrine is a claim about the choosing, falling back to the
  turn one was **owned** when the log holds no such order, and the label says which answered - and a
  shortfall that is only the **ram** is flagged, because ram and siege tower both go obsolete at
  `CIVIC_CIVIL_ENGINEERING` and after that the table's ram line cannot be filled at all.
* **The production orders** - the first order in each category, the turn the army began, and the turn
  the siege train was first asked for. The diary holds what the empire *has*; the log holds what it
  *chose*, and the doctrine is about the choosing. **One offset to carry when the two are compared: a
  `Research complete` line is reported inside the `end_turn` called on turn N, so the diary first lists
  the tech at N+1** - measured on A4 across the whole line (Mining T7 -> T8, Bronze Working T21 -> T22,
  Masonry T38 -> T39, Engineering T42 -> T43), and the T43 `UNIT_CATAPULT` order proves the tech was
  owned by then. A record that compares the log's line with the diary's list without the offset reads a
  disagreement that is not there. **The offset is not a tech rule - it is what an `end_turn` result *is*,
  so it applies to every completion line**, and A4 measured it twice more on the same attempt: a
  `>> Xi'an finished building DISTRICT_ENCAMPMENT` line inside the `Turn 31 -> 32` result means the
  district **stands from T32** (and the order's own `5 turns` at T27 ends in exactly that transition),
  while the same attempt's `UNIT_CATAPULT` completion inside `Turn 48 -> 49` is why the instrument reads
  `first siege: T49`. **Write the turn the thing exists, and cite the reporting turn beside it when the
  two are compared** - A4's record had the district at T31 in four places until the session's own closing
  summary forced the correction.
* **The doctrine checks** - the claims in `tactics/01` that a log can settle without a judgement call:
  **H5** (no ram and no tower is ever bought - the human's instruction, so a single order of one is a
  violation with a turn on it), **H6** (how many distinct cities were asked for military units),
  **H4** (upgrades against new builds), and **H1/H2** (the order the roles were first asked for).
  Alongside them, **the diary's own `ESTABLISHMENT:` line is printed next to the record's numbers for
  the same turn**: a claim the record does not support comes out as `MISMATCH - siege claimed 2 vs 1
  held` rather than being read as fact. The line is requested every ten turns, so a turn without one
  is not a failure. **The numerator is units held in the field, which is what "the diary holds what the
  empire has" means above** - a unit still in production is not held, and it is written after the token
  in its own words (`siege 1/2, 1 building due ~T48`), never in the numerator. **A3 and A4 both wrote
  `siege 1/2 building` with zero siege units built**, so the ambiguity is a property of the brief and
  not of one session; the definition is stated here and in each attempt's brief so it cannot recur.
* **The economy at T20 / T40 / T60** - science, culture, gold/turn, pop, cities, districts,
  improvements. This is what the military build cost.
* **The rule table** - `CHECK FAILED` counts per rule. A doctrine that keeps its own rules red is
  being violated by its own execution; that is a finding, not noise.
* **The refusal table** - `STOPPED_MID_PATH` and friends: production is not the only cost, orders
  that do not land are.
* **The process table** - tool calls per turn, so an attempt's own cost is on the record.

**Cadence.** The turn-1 save is kept before any action. The session answers the `10-TURN REVIEW`'s
three questions in the diary each time it fires. The attempt ends at the **first captured enemy
city**, or at **T80**, whichever comes first - the question is how the army was paid for, not how
the war ended.

## 5. What is written down

| File | Contents |
|---|---|
| `NNN-<slug>.md` | one attempt: settings + seed, the one variable, the hypothesis **with numbers**, the report table, the verdict (hypothesis held / falsified), and what the next attempt changes |
| `RETRO-<date>.md` | the comparison across attempts: which claim survived, which was corrected, and **which artifact each correction became** |
| `CHINA-KIT-AUDIT.md` | a cross-attempt **audit**: one question asked of the whole programme (`did the civilisation's own kit get played?`), answered from the session logs and the install's own data files rather than from a new attempt. It is not an attempt, so it carries no number and no variable |
| `prompts/tasks/tmp/NNN-*.md` | the instruction the session played under, retired to `done/` when the attempt ends |

The rules that keep this honest:

1. **Every number names its source** - a diary turn, a log line, or a file:line. An estimate is
   never written as a measurement.
2. **The verdict is a comparison, not a narrative.** "H1 held" is only allowed next to the two
   numbers it is claimed for.
3. **Where the two records disagree, the record wins.** The diary is the agent's own account of the
   turn and the log is what the tool answered; when the self-report and the instrument part company,
   the review says so and quotes both, because "the claim was plausible" is not evidence.
4. **A finding that changes the doctrine goes into the doctrine**, not only into this directory:
   `prompts/tactics/01` for a production rule, `turn-checks.md` for a rule the engine can enforce,
   `pending/` when its metric does not exist yet, a task file for a bounded objective. This is the
   same ladder `docs/retrospectives/` uses; a finding that lands nowhere is a diary entry and will
   be lost.
5. **The diary keeps the last write per turn.** After a rollback, the early turns belong to the
   abandoned branch while the logs still hold both. An attempt that was rolled back says so at the
   top of its record, or its numbers will be read as one continuous game.
6. **A rule that is not in the shipped file is not in force, and a `once: true` goal leaves it silently.**
   `prompts/checks/turn-checks.md` is shared by every match, but **which goals have been retired is not
   per match in the file**: a goal achieved in one match is pruned from the file with a trace that names
   no match, while the persisted state (`.civ6-mcp-data/turn-checks-state.json`) *is* keyed per match. **Measured 2026-09-30**: A3-A7
   replayed a T1 branch of a save whose other branch had retired `dynasty-cycle-wonder` at T99, so
   China's wonder obligation was absent for eight sessions and ~340 turns - **zero wonders**, with the
   10-turn review printing the forfeit 29 times and the test suite green throughout, because
   `tests/conftest.py` restores retired goals into its fixtures. **So an attempt's first step is to say
   which of the directive's standing goals are live in the shipped file**, and a goal restored by hand
   is restored before the attempt's first decision, not after. `docs/experiments/CHINA-KIT-AUDIT.md`
   is the case; the class-level fix is staged in the retro's section 5.
