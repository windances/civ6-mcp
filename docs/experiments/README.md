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
| **A3** | Encampment after the second city instead of before it | two cities' compounding beats the earlier general's aura: first city falls no later than A2 |
| **A4** | Magnus' Groundbreaker: chops go into units instead of infrastructure | the establishment arrives 5+ turns earlier and the economy is behind by less than 5 turns at T60 |
| **A5** | the siege train is bought with gold, not produced | the war opens 5+ turns earlier at the cost of a negative `carrying-capacity` window |
| **A6** | two war cities instead of one | the second city's production outweighs the lost compounding |

A variable is only worth an attempt if the hypothesis can be **falsified by a number** in section 4.
An attempt whose hypothesis cannot fail is not run.

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
  *chose*, and the doctrine is about the choosing.
* **The doctrine checks** - the claims in `tactics/01` that a log can settle without a judgement call:
  **H5** (no ram and no tower is ever bought - the human's instruction, so a single order of one is a
  violation with a turn on it), **H6** (how many distinct cities were asked for military units),
  **H4** (upgrades against new builds), and **H1/H2** (the order the roles were first asked for).
  Alongside them, **the diary's own `ESTABLISHMENT:` line is printed next to the record's numbers for
  the same turn**: a claim the record does not support comes out as `MISMATCH - siege claimed 2 vs 1
  held` rather than being read as fact. The line is requested every ten turns, so a turn without one
  is not a failure.
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
