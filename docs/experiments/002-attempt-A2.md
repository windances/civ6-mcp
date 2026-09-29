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
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run sacred-garnet-vault-35 --from 1 --to 40 --verdict
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run sacred-garnet-vault-35 --from 1 --to 40 --step 10 --save docs/experiments/A2-T40.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs/experiments/A1-T40.json docs/experiments/A2-T40.json
```

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

| question | answer |
|---|---|
| establishment turn so far (Q1 wants <= T60) | not yet measured |
| the army's start, the siege order, and the first economy order after Engineering (Q2) | not yet measured |
| the economy at T20 / T40, against A1's | not yet measured |
| `carrying-capacity` red turns so far (Q4 allows < 10) | not yet measured |
| contact: has the target been seen, and at what distance does `get_staging_plan` put it | not yet measured |
| verdict so far on Q1-Q4 | not yet measured |

Then one paragraph, and only one: what this window bought that A1's could not, and the single thing the
next stretch changes.
