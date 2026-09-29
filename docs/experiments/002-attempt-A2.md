# Attempt A2 - the same doctrine, with a target inside the window

**Status: in progress** (the session `sacred-garnet-vault-35` is playing it; started 2026-09-29 14:02).

The experiment is `docs/experiments/README.md`; the instruction is
`prompts/tasks/tmp/031-military-production-attempt-a2.md`; A1's record and its T40 review are
`docs/experiments/001-attempt-A1.md`. This file is A2's record - the settings, the one variable, the
hypothesis with its numbers, and (when it ends) the table and the verdict.

## Settings: everything A1 had, and one thing changed

| | A1 | A2 |
|---|---|---|
| start | `ATTEMPT-A1-T1-settled.Civ6Save` | **the same save** |
| doctrine | `tactics/01` + `tactics/08` as written | the same, unchanged |
| executor | a DSH session under task 030 | a DSH session under task 031 |
| game key | `china_911679432` | the same key, so the same diary and the same log family |
| **the one variable** | - | **the target's distance** |

**The target, and how far it is.** A1's objective was the nearest rival *capital*: Canberra at
(27,18), **33 tiles west** of 西安 (60,22), behind five city-states, and by A1's T40 **no rival had been
met at all**. A2's objective is the nearest *city*: the city-state 耶路撒冷 at (50,22) - the same row as
the capital, so the hex distance is exactly **10**, read off the map dump rather than guessed
(`.civ6-mcp-data/mapstatic_china_911679432_*.json`, the same source that gave A1 its 33).

**A city-state is a legitimate target here and not under the standing directive**, which says
city-states are not conquest targets because a *victory* needs the rival capitals. Task 031's
`overrides:` line carries that single exception, and the review must read it as the experiment's design
rather than as drift: a production experiment needs a city its army can reach.

**One consequence of the shared key, verified before A2 started.** Both attempts write
`diary_china_911679432.jsonl`, and the diary keeps the **last write per turn** - so A2's rows for T1-T40
overwrite A1's as it plays them. That is why A1's numbers were snapshotted **before** A2 launched
(`docs/experiments/A1-T40.json`), and it is the protocol's "snapshot while it is the current attempt"
rule doing its job rather than a theory.

**And it was a real trap, not a caution.** With A2 at T10, re-extracting A1 - `--run` naming A1's
session - reported A2's T10 row (military 31, tourism 0, era 4) where A1's own row says 34, 8, 2: the
`--run` filter scoped the log rows but not the diary, and a diary row carries no session. The instrument
now attributes each diary row to the run whose log window covers it (sessions cannot overlap - FireTuner
serves one connection at a time), per turn when the log has that turn and by the session span otherwise,
and **names and discards** a turn two attempts wrote inside one window instead of guessing (`d3ebb51`).
Re-extracting A1 reproduces the pre-A2 snapshot field for field, and the same check reads both attempts'
own T10 rows side by side. The snapshot rule stays - it keeps the record independent of the instrument -
but a snapshot lost to an overwrite is now recoverable rather than lost.

**The same-start check, measured.** A2's T1 row is identical to A1's on every economy field (science
2.5, culture 1.3, gold 6, GPT 5, faith 0, military 20, pop 1, one city, exploration 2%), so the "one
variable" claim is read off the record instead of asserted; the first divergence the record shows is the
T10 military figure, **34 for A1 against 31 for A2**.

**The measured deviation from "one variable".** The two sessions ran the same doctrine and still opened
differently (read from each run's own `set_city_production` rows):

| | A1 | A2 |
|---|---|---|
| the first six orders | `SCOUT T1, SLINGER T5, SETTLER T6, BUILDER T15, GRANARY T18, WARRIOR T20` | `WARRIOR T1, SLINGER T7, SETTLER T11, BUILDER T18` |

Same kinds in the same order except that **A2's first build is a second Warrior, not the Scout** - so the
attempt has **no recon unit at all** (4 units at T18: Warrior (60,22), Warrior (56,23) at 31 HP, Slinger
(60,22), Settler (60,22)) - and every later slot is 1-5 turns later. The doctrine fixes the army's
composition, not the city's first order, so this is a property of the doctrine rather than a slip: the
protocol now pins the opening build from A3 on. The consequence to carry into the T40 review is concrete:
`tactics/07`'s Gate 0 is *a candidate city is actually visible*, the target is still in fog, and this
attempt's only westward unit is a wounded Warrior - so Q3's deadline is exposed to a failure mode A1's
window never tested.

## The hypothesis, with the numbers that falsify it

| # | Prediction | Falsified when |
|---|---|---|
| Q1 | with a target ten tiles away, the establishment is complete **by T60** | the composition at T60 is short in any role |
| Q2 | **once Engineering exists, the siege train is ordered before economy buildings** - this is H1, which A1 could not test because the tech did not exist | a Campus, Granary or other infrastructure order is placed after Engineering and before the second Catapult |
| Q3 | **the first city is kept by T80** | T80 arrives with no `KEEP|` in the log |
| Q4 | the army is paid for: `carrying-capacity` red on **fewer than 10 turns** | gold/turn is below 10 on ten or more turns before the city falls |

Q2 is the sharpest of the four, because it is the first test of H1 the experiment has been able to run:
A1's order of asking was `recon T1 -> ranged T5 -> melee T20` with **no siege order ever**, and the
reason was structural (Engineering did not exist), which is exactly what A1's arithmetic note says makes
P2 unaskable rather than missed. A2 inherits the same tech timeline and the same terrain; what changes is
that the army now has somewhere to go.

## The decisive numbers, measured by the instrument

1. **the establishment turn** (every turn is scanned, not every tenth);
2. **the turn the first siege unit was *ordered***, and where it sits relative to the first economy
   building ordered after Engineering - `--verdict` prints the order of asking and the order table
   reads the log's own production calls;
3. **the turn the first enemy city is kept**, from the `KEEP|` reply;
4. **the turns under the gold floor**.

Commands, with A2's own session in the log filter:

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run sacred-garnet-vault-35,pale-pearl-aqueduct-92 --from 1 --to 40 --verdict --questions a2
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run sacred-garnet-vault-35 --from 1 --to 40 --step 10 --save docs/experiments/A2-T40.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs/experiments/A1-T40.json docs/experiments/A2-T40.json
```

`--questions a2` answers **this attempt's** four questions from the record. Its `--ids` sibling only
relabels the four generic slots, and A2's questions do not sit in those slots: its **Q1** is the
establishment deadline (the generic slot 2), its **Q2** is the ordering after Engineering, which no
generic slot measures at all, and only Q3/Q4 line up with slots 3/4. The final snapshot of the second
half (`pale-pearl-aqueduct-92`, whose T1-T40 rows belong to `sacred-garnet-vault-35`) carries the same
flag.

## One instrument change between the two attempts, and why it does not break the compare

The H6 measure (`tactics/08`: *one war city, everything else compounds*) was a **count of cities that
ordered any army unit**, which a single stray Warrior in a second city satisfies - so H6 could go green
without the concentration the rule is about. It was rewritten to count **army-role orders per city**
(recon and civilian orders excluded), report the busiest city's share, and name the cities where army
orders are at least half of that city's orders. A1's snapshot was regenerated with the new shape, so both
attempts are read by the same instrument; under either reading A1 is **one** war city carrying 100% of its
six army orders (`131073` ordered five things and none of them military), so A1's T40 conclusion is
unchanged - the record was re-measured, not reinterpreted. The old blunt count stays in the record beside
the new one.

## Mid-window review (end of T40) - written when the session stops there

Written at the T40 stop from `docs/experiments/A2-T40.json` and from the session's own diary rows.
A1's figures beside A2's come from the same instrument over `A1-T40.json`.

| question | answer |
|---|---|
| establishment turn so far (Q1 wants <= T60) | **not reached at T40.** The record reads **siege 0/2**, melee 2/2 (four Warriors held), ram 0/1, ranged **4/4**, **cavalry 1/1** (first cavalry **T38**), recon 0/2. The screens were complete on **T28**, and the siege half is at zero with Engineering still ~10 turns out. **The diary's own `ESTABLISHMENT:` lines disagree with the record 11 times** (T29-T40, always `melee claimed 2 vs 3-4 held`). One column of that disagreement was the **instrument's** fault and is now fixed: the role map did not know `UNIT_HEAVY_CHARIOT`, so the Heavy Chariot was invisible to every role and the executor's own `cavalry 1` was scored against a map reading 0 - the game's own `UNITTYPE_CAVALRY` rows in `Units.xml` are the authority, the map now carries the unit, and re-measuring A2's T40 snapshot moved the cavalry slot from `0/1` to `1/1` and dropped the cavalry entries from the mismatch list. The eleven that remain are the executor's: it under-counted its own melee, and the line follows task 031's table where melee is a target of 2. The record wins; the next stretch's line must print both the table count and the held count. |
| the army's start, the siege order, and the first economy order after Engineering (Q2) | army start **T1** (`UNIT_WARRIOR`); first siege order **never**; first building order `BUILDING_GRANARY T28` - and it was **refused** (`CANNOT_PRODUCE`, Pottery was never researched), so the log holds an order and the city holds no building. Nothing was ordered after Engineering because Engineering has not landed: **Q2 is untested at T40, not violated.** |
| the economy at T20 / T40, against A1's | T20: science **4.0 vs A1 4.5**, gold/turn 5.0 vs 5.0. T40: science **5.9 vs 7.9**, gold/turn **8.9 vs 6.0**, culture 6.0 vs 4.3, military **156 vs 139**, pop 9 vs 8, cities 2 vs 2, **improvements 5 vs 2**, **districts 0 vs 1**. A2 is behind on science and ahead on gold, improvements and army - it bought screens and mines where A1 bought a Campus. |
| `carrying-capacity` red turns so far (Q4 allows < 10) | **The criterion named a measure that cannot fire in its own window, and the substance is the opposite of what a zero suggests.** `carrying-capacity` is gated `when: turn() >= 60` in `prompts/checks/turn-checks.md`, and Q4's horizon is T60 - so the rule's count is **0 by construction** (it appears in no `CHECK FAILED` line in either attempt's log). The other two measures of the same floor disagree with that zero and agree with each other: `end_turn`'s 10-turn review printed `carrying capacity: gold/turn +5.0 with military 38 - BELOW the +10 the directive requires with the army counted` at **T19**, and `+7.0`/military 118 and `+6.0`/military 139 at **T29**/**T39**; the diary's own `gold_per_turn` is below 10 on **every one of the forty turns** (5.0 rising to 8.9). So the army was **not** paid for to the directive's +10 standard in that window - Q4's "held so far" was an artefact of the gate, and this row previously recorded it as held. The rule's own window (T60-T80) is still ahead of the attempt and will answer it on its own terms. |
| contact: has the target been seen, and at what distance does `get_staging_plan` put it | 耶路撒冷 **(50,22) was seen at T10** and met (Religious city-state, player 6, one envoy held); it is ~5-6 tiles from A2's forward units and 10 from 西安. At T40 `get_staging_plan(50,22)` returned **18 ring tiles, 1 placed, 3 unplaced**, the Heavy Chariot and two Slingers `TOO FAR (d9-d12)`, **`supply hexes cut 0/6`**, and **`ASSAULT OPENS ... with 0 shooter(s) in position`**. Its `arrive T+1` column is not credible (it prints T+1 for a unit 5-6 tiles out), so the deadline is written from the ring distances and not from that column. Walls, HP and garrison: **still unread by any tool** after 40 turns. |
| verdict so far on Q1-Q4 | **OPEN / untested so far / OPEN / mis-specified.** Q1 is open on the clock and dead by arithmetic (a first Catapult ~T60 leaves no second one inside the attempt); **Q2 is untested so far**, not violated - Engineering had not landed by T40 (`techs_completed` 2 = Mining and The Wheel; the session's own T30 hypothesis put Engineering at T44-T48), and this T40 row is a **mid-window checkpoint, not the attempt's end**: task 031 runs to *a city is kept, or T80* with `expires: T90`, so Q2's answer arrives around T60-T70. Q3 is open but was never approached (no recon unit, exploration 7%, `ASSAULT OPENS ... with 0 shooter(s) in position`); **Q4 was answered by a measure that could not fire** - the rule it named starts at T60 and the horizon is T60, while the review's own line and the diary's own number both put the economy under the floor on every turn. |

**The one paragraph.** What this window bought that A1's could not is a **testable Q2 and a completed
screen establishment**: at T40 A2 holds four Slingers, four Warriors, a Heavy Chariot, five improvements
and a second city on the army's axis, against A1's four Slingers, two Warriors, one Campus and two
improvements - and, the point of the attempt, it has a named city **ten tiles away, seen and met**, where
A1 had met nobody at all and was 33 tiles from its objective. What it did not buy is the siege half, for
the reason A1's arithmetic predicted and this target could not change: Engineering is a 134-science gate
with no eureka in this plan, science runs at 5-6/t, and two Catapults then cost about twenty turns of one
city's output. **So the one thing the next stretch changes is the sequencing: the march starts at ~T45,
before the siege exists, toward a rally point three tiles east of 耶路撒冷's ring, so the army is formed
and the shooting opens the turn the Catapults arrive** instead of ten turns after it. The target's
distance was never the constraint; the Engineering beeline is - and that is the answer A2 was built to
be able to give.

## The gate, answered in play: Engineering T48, both Catapults ordered the same turn

This is Q2's answer, written the turn it happened rather than reconstructed afterwards. The three turns
the task asked for:

| what | turn | evidence |
|---|---|---|
| **Engineering completed** | **T48** | the T47 -> T48 result carried `>> Research complete: 工程!`; the tech read `98%, 1 turns` at T47 and `None` was pending after the completion |
| **西安 ordered UNIT_CATAPULT** | **T48** | `PRODUCING|UNIT_CATAPULT|6 turns` (~T54) |
| **太原 ordered UNIT_CATAPULT** | **T48** | `PRODUCING|UNIT_CATAPULT|8 turns` (~T56); 太原's Water Mill finished the same turn, so its queue was free |
| **first economy order after Engineering** | **T55, `BUILDING_GRANARY` in 太原** | `PRODUCING|BUILDING_GRANARY|5 turns`, placed the same turn 太原's Catapult completed (`>> 太原 finished building UNIT_CATAPULT`). The order therefore came **after the second Catapult existed**, seven turns after Engineering, with two Catapults built and a third already queued in 西安. **Q2 is not falsified.** |

**The second Catapult, and the shape of the siege half when the gate closed.** 太原's Catapult completed
at **T55** (`New unit: 石弩 (UNIT_CATAPULT) at (55,23)`) - the turn the attempt first holds **2/2 siege
units** - and a third was already in production in 西安 (ordered T53, ~5 turns). The whole gap between
Engineering (T48) and the second Catapult (T55) was filled with military orders only, and the first
economy order waited until the second Catapult existed. Two facts belong beside it: the Catapults were
built at **+75%** (Agoge + God of the Forge), and a siege unit **cannot attack units at all**
(`SIEGE_CANNOT_ATTACK_UNITS` returned at T55 when one was ordered onto a barbarian Archer at range 2),
so the question this record still owes is whether a Catapult can fire at range 2 **at a city** - the only
target it will ever have.

**The blocker the attempt hit at T60, and it is a tooling one, not a doctrine one.** With the
establishment complete and two Catapults standing on the firing tiles (50,24) and (51,23) at distance 2
from 耶路撒冷, the declaration could not be made. `send_diplomatic_action(6, DECLARE_SURPRISE_WAR)`
answered `WARN:WAR_UNCERTAIN|... session completed but war state not yet confirmed`, twice, and
`DECLARE_FORMAL_WAR` answered the same; `get_diplomacy` then showed no war, a move onto the ring answered
`CAPTURE_MOVE|BLOCKED (city-state territory (耶路撒冷) - need suzerainty or Open Borders)`, and an attack
on the city tile answered `NOT_AT_WAR`. The cause is in `src/civ_mcp/lua/diplomacy.py`: every war action is
delivered by opening a **diplomacy session** (`DiplomacyManager.RequestSession`) and adding responses to
it, and **a city-state has no diplomacy session to open** - `FindOpenSessionID` returns nothing,
`sessionCompleted` stays false, and control falls through to the `WARN:WAR_UNCERTAIN` branch, which is
indistinguishable from a genuine uncertain success. The diagnostic in `src/civ_mcp/lua/units.py` (line
301) confirms it independently: the border refusal is printed only on the `not atWar` branch. **So this
attempt's capture half is blocked by the tool, not by the map, the doctrine or the production** - the
exact inversion of A1, whose capture half was decided by the map. The army is staged and ready; what it
needs is a declaration the tooling cannot make, and the answer is the human's UI.

**What the refusal did buy.** The rejected attack printed the target's pool on its estimate line -
`UNIT_CATAPULT (CS:35, HP:100) vs CITY_CENTER (CS:0, HP:200)` - so **耶路撒冷's HP pool is 200**, the
first HP figure any tool has ever produced for it. No `walls:` value has appeared on any line yet, so the
wall question is still open and still the one prerequisite unread at the end of the window.

The order of asking is the measurement, so it is recorded with what was deliberately *not* done: no
Granary, Campus, Water Mill or Trader order was placed after Engineering and before the second Catapult.
The one economy order that was in flight at the gate - 西安's Trader - had been placed at **T46**, two
turns before the tech existed. That is the reason 西安 was building a Trader rather than the Granary the
directive's own build order would have put next: the bridge item was chosen at T41 to be cheap and
strictly pre-gate, so that the gate turn had a free choice in it rather than a nearly-finished building.

**The multiplier is visible in the estimates.** Unmodified, a 120-production Catapult is 11 turns in 西安
(11 production) and 17 in 太原 (7) - the tool answers **6** and **8**. POLICY_AGOGE (+50% to Ancient and
Classical military units) has been in the military slot since the first half, and T41 added God of the
Forge (+25% to the same class), so +75% is stacked on the siege half for the first time in either attempt.
Q1's deadline - "the establishment is complete by T60" - is therefore measured against **T54 and T56**.

## The war opens at T60, and the one thing still unread

The army staged onto the target's ring first and declared war second:

| turn | what the record holds |
|---|---|
| T57 | `get_staging_plan(50,22)` - **18 ring tile(s), 4 unit(s) placed, 4 unplaced**, `ISSUE THE MOVE ...` |
| T59 | the army is in place: two Catapults at **(50,24)** and **(51,23)** - within range 2 of 耶路撒冷 (50,22) - three Warriors at (52,21)/(52,22)/(54,22), an Archer at (53,21), the Heavy Chariot at (54,24), the third Catapult at (58,23) still coming |
| T60 | `send_diplomatic_action(other_player_id=6, action="DECLARE_SURPRISE_WAR")` - answered `WARN:WAR_UNCERTAIN\|... war state not yet confirmed for 耶路撒冷. Check next turn.` - then the same call again, then `DECLARE_FORMAL_WAR`, all three with the same warning |

Player 6 is 耶路撒冷 (the city-state read at T10 as `Religious, 1 envoys [player 6]`), so the target is the
one task 031's `overrides:` line names. Two things belong in the record beside it:

- **Three declarations in one turn, because the warning invites a retry.** `WARN:WAR_UNCERTAIN` says the
  state will be confirmed next turn; `AGENTS.md`'s war rule says the same thing for the engine (*declare on
  turn N, position that turn, attack on N+1*), and the session read the warning as a failure and escalated
  the declaration form twice. Nothing was broken by it - a city-state cannot be more declared-at - but a
  warning that reads like an error is a tool-shaped trap, and this is the count.
- **The target's walls, HP and garrison still have not been read by any tool.** Six turns of staging, and
  the reads near (50,22) are `get_map_area` terrain from T41-T42 and the ring census. `tactics/07`'s first
  gate is that a candidate city is visible; the army standing at its gate with the wall numbers unknown is
  where the attempt's last open question - *can two Catapults and three Warriors take it before T80* - will
  be answered.

## Why the declaration did not stick, and what it cost

The three declarations above were not a session mistake - **the tool cannot declare war on a city-state**,
and the attempt's capture half was blocked by that from T60 to T66. The session verified it four ways over
three turns: surprise war twice and formal war all answering `WARN:WAR_UNCERTAIN`; `get_diplomacy` showing
no war; a move onto the ring answering `BLOCKED (city-state territory (耶路撒冷) - need suzerainty or Open
Borders)`; and a Catapult ordered onto the city answering `NOT_AT_WAR` (whose estimate did reveal the city
pool: **200 HP**).

The cause is in this repo, not in the game. Every war action goes through a **diplomacy session**
(`src/civ_mcp/lua/diplomacy.py:414-427`: `RequestSession` -> `FindOpenSessionID`), and a city-state has no
session to open - so `sid` is nil, `sessionCompleted` stays false, and the code falls through to a
`WARN:WAR_UNCERTAIN` message that was written for the benign "the engine has not synced yet" case. The
warning hid "the session never opened".

**The game's own answer was in its UI Lua.** `Base/Assets/UI/Popups/DeclareWarPopup.lua:76-82` declares war
with a **player operation** on the branch that has no casus belli - which is the branch a city-state always
takes:

```lua
parameters[PlayerOperations.PARAM_PLAYER_ONE] = eAttackingPlayer
parameters[PlayerOperations.PARAM_PLAYER_TWO] = eDefendingPlayer
UI.RequestPlayerOperation(eAttackingPlayer, PlayerOperations.DIPLOMACY_DECLARE_WAR, parameters)
```

Run against this position through the FireTuner connection at T66, with the session stopped:
`IsAtWarWith(6)` went **false -> true** and `CanDeclareWarOn(6)` **true -> false**. The war this attempt
needed is therefore **on**, and the tool is fixed with it: `build_send_diplo_action` now declares a
city-state war through that operation and returns `OK:WAR_REQUESTED|...` instead of the uncertain warning,
with `tests/test_city_state_war_declaration.py` pinning the branch, the gate and the early return.

The honest shape of the two attempts' capture halves is therefore a mirror image: **A1's was decided by the
map** (33 tiles, no rival met), **A2's was decided by a tool** (a declaration that silently did nothing),
and in neither case by the production the experiment set out to measure.

## The first shots, and the last unread number

The resumed session (`volcanic-indigo-caravan-23`) opened fire at **T66**: both forward Catapults attacked
the city from range 2, and the result line carries the fact that no tool had been able to read for
twenty-six turns:

```
RANGE_ATTACK|target:耶路撒冷 (city) at (50,22)|pre_hp:200/200|your HP:100|range:2 dist:2|
damage dealt:none read (city still 200/200)|city hp: 200/200, walls: none
```

**耶路撒冷 has no walls.** That is the number `tactics/07`'s gates wanted and neither attempt could get,
and it changes the arithmetic Q3 turns on: with no wall pool to break first, the Catapults' damage goes
straight into the 200-point city pool, so a two- or three-Catapult train firing every turn is a matter of
a few turns rather than a wall-breaking siege - provided the army survives what the city-state sortied
against it (five units at T66, one of them a Heavy Chariot **adjacent to both Catapults**).

Both shots also read `city still 200/200` on the immediate reply, which is the documented stale read
(`AGENTS.md`: judge a city's progress from `SIEGE PROGRESS` and a later read, never from the reply) - and
the third time this attempt met that trap, after the melee no-op at T35 and the ranged `pre_hp` echo.

**And the authoritative block agrees with the stale read: after two Catapult shots the pool has not
moved.** The `end_turn` that closed T66 printed:

```
>> SIEGE PROGRESS (T67):
 耶路撒冷: city hp 200/200; supply line 5/6 cut - the city is still healing
-- SIEGE POSTURE (T67) ...
 SIEGE FIRE: 2/3 siege unit(s) inside range 2 of the target - OUT OF RANGE: UNIT_CATAPULT at distance 5
```

with `use-your-attacks`, `screen-the-siege`, `cut-the-supply` and `carrying-capacity` all failing in the
same result. So the position at the end of the first war turn is: two of three Catapults in range, both
fired, the city at **200/200**, one adjacent hex (`49,22`) still open, and - per `cut-the-supply`'s own
text, citing the manual - *a city heals about twenty points a turn while any adjacent hex is outside our
zone of control*. Two shots that each deliver less than ten points are therefore indistinguishable from
zero after healing, and **no tool will say how much a shot delivers**: the attack reply prints
`Est damage to defender: n/a (the city is the target, not this unit)` by design, and the pool is the only
feedback. That is the gap to watch for the rest of the assault - if the pool keeps reading 200 while two
Catapults fire every turn, the train cannot out-damage the heal and Q3 fails for an arithmetic reason no
tool surfaced in advance; if it falls, the same block will show it.

## One tooling finding A2 produced, with its numbers

At T35 a melee attack was ordered from an adjacent tile and the reply began `enemy HP:72 -> 72/100` - the
**pre-attack** value echoed back - while the read immediately after also showed 72 HP and still offered
`>> CAN ATTACK`. The session concluded the attack had silently failed, could not close the turn past the
pending-attack gate, and ended it with `skip_remaining_units(force=True)`, **discarding a legal attack**.
The next turns' reads show the damage had landed: the barbarian Warrior went `72 -> 50 -> 20 -> dead`
(the 20 HP is what the T37 attack killed). So this is not a lost attack but a **reply that cannot be read
as a result**: `AGENTS.md` already says a post-combat read is an estimate, and this is the same trap one
layer earlier, in the reply line itself. What the record owes the next session is either the post-attack
HP or a label on the number it prints; what it owes the *review* is the count - one attack order was
thrown away and the turn closed on a discarded legal action.

## Four more findings from the same session, and what each became

- **The pantheon could not be founded at all, and the fix does not reach the session that found it**
  (T21): every `choose_pantheon` call returned `ERR:Runtime Error: ... operator < is not supported for
  number < string`. The 2026-09-29 faith guard - added after A1's free-pantheon measurement - reads
  `GameInfo.GlobalParameters["RELIGION_PANTHEON_MIN_FAITH"].Value`, which is a **string** in this build,
  and compares it to faith without `tonumber()`. A guard that refuses everything is not a guard: A2 played
  the whole window with **no pantheon**, losing the belief it had chosen (God of the Forge, +25% toward
  Ancient and Classical military units) while faith ran on unspent to 57. Fixed in
  `src/civ_mcp/lua/religion.py`, with the speed caveat written beside it (the standard-speed 25 is
  conservative on Quick, where the game itself offered the pantheon at 17 faith);
  `tests/test_pantheon_faith_guard.py` is green. **The running server held the old Lua**, so the fix
  belongs to the next session - and the lost belief belongs in A2's verdict, because no play could avoid
  it.
  **Verified in play at T41**, which is what makes the first half's loss a fact rather than a suspicion:
  the resumed session `pale-pearl-aqueduct-92` called
  `choose_pantheon(belief_type="BELIEF_GOD_OF_THE_FORGE")` with 56 faith banked and the tool answered
  `PANTHEON_FOUNDED|锻造之神` - the belief the first half chose and could not have. So the guard is fixed
  in the Lua a session loads, and the T40 checkpoint stands as a **no-pantheon baseline**: the first
  half's army was built without the +25% it had planned for.
  **The same read carried the era, and it lands on the second half, not on the comparison.** Both
  attempts' T40 checkpoints are `age=NORMAL` / `ERA_ANCIENT` (A1: era score 11; A2: 5), so the T40
  tables above are the same age and remain comparable. At **T41 the era advanced to Classical and the
  age became Dark** - era score 5 against Dark 13 / Golden 26 - and the resumed session answered the
  dedication with `DEDICATION_CHOSEN|COMMEMORATION_SCIENTIFIC`. Whatever the second half produces is
  therefore built under a Dark Age that A1's window never saw, and the final compare has to say so.
- **A jungle hill the builder board recommends cannot be improved or cleared** (T26):
  `get_builder_tasks` lists `(60,21): build MINE` as NORMAL, `improve` answers `tile has
  FEATURE_JUNGLE (use remove_feature first)`, and `remove_feature` answers
  `CANNOT_REMOVE|Cannot remove FEATURE_JUNGLE`. One turn of builder movement was spent on the
  contradiction.
- **`skip_remaining_units` clears standing multi-turn move orders** (T18-T20): a Settler ordered to a
  distant tile ended its turn where it stood and did not move again until the order was re-issued on the
  turn it was to move. Every move in this attempt after T20 is issued on its own turn.
- **An off-ledger gain the production ledger cannot see** (T37): the barbarian field force at (54,25)
  was destroyed and its **captured Builder was recaptured with three charges** - a unit no city ever
  produced. It is part of why improvements reach 5 at T40, so any comparison of "production spent per
  improvement" between attempts has to name it or it will credit A2 with production it never spent.
