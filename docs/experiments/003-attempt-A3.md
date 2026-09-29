# Attempt A3 - the same doctrine against a walled target

**Status: in progress** (session `flint-indigo-rampart-32`, from the experiment's shared T1 start; started
2026-09-29). The attempt's instruction is `prompts/tasks/tmp/034-attempt-a3-the-same-doctrine-against-a-walled-target-from-the-shared-t1-start.md`;
the design is section 3 of `docs/experiments/README.md`; A1's and A2's records are
`001-attempt-A1.md` and `002-attempt-A2.md`, and the cross-attempt report is
`RETRO-2026-09-29.md`. This file is A3's record.

## Settings: the shared start, the corrected table, one variable

| | A2 | A3 |
|---|---|---|
| start | `ATTEMPT-A1-T1-settled.Civ6Save` | **the same save** (loaded at T77 of A2's branch, which stays recoverable as `0_MCP_0077`) |
| doctrine | `tactics/01` as it stood | the **corrected** `tactics/01`: recon 1 and anti-cavalry 1 are required rows, the ram is conditional |
| the one variable | the target's distance | **the target's defences - a city whose wall pool reads above zero** |
| window | to the capture (T68) | `KEEP|` of a walled city, or **T110**; `expires:` T115 |

**A3 differs from A2 in two ways, and the record says so**: the establishment table (corrected after A2)
and the target's defences. That is why the capture arithmetic below is compared against A2's T68 with
both differences in mind, rather than read as a clean single-variable delta.

## The opening build is pinned (the protocol's rule from A3 on)

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, and the record states whether the executor matched them
order by order. The pin was added at T3 (the first order, the Scout, had already matched it), because the
protocol requires it of A3 and the file went out without it.

**The executor's opening, as the log holds it:**

| order | promised | the record |
|---|---|---|
| 1 | `UNIT_SCOUT` | **T1** - matched (and it is the corrected table's recon row: the first attempt in the programme to open with it on purpose) |
| 2 | `UNIT_SLINGER` | **T5** - matched |
| 3 | `UNIT_SETTLER` | **T6** - matched |
| 4 | `UNIT_BUILDER` | not placed yet at T9 |

Research follows A1's and A2's shape: `TECH_MINING` T1, `TECH_THE_WHEEL` T8 - the beeline A2 rode to
Engineering at T48, which is the gate H1 is measured at.

## The hypothesis, with the numbers that falsify it

| # | prediction | falsified when |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | the composition at T60 is short in any required role |
| Q2 | **a walled target changes the arithmetic measurably**: the wall pool's turn count is on the record and the city is kept **no earlier than T68** and **no later than T80** | no city with `walls > 0` is found and attacked inside the window (unaskable - report the reads), or the city falls before T68, or T80 passes with no `KEEP|` |
| Q3 | the **first city is kept by T80** | T80 arrives with no `KEEP|` |
| Q4 | `carrying-capacity` red on **fewer than ten turns** | the rule reads red ten or more times |

## The decisive numbers, measured by the instrument

1. **the establishment turn** (every turn is scanned), under the corrected table;
2. **the wall pool**: the first turn a city's `walls:` read above zero, the turn it read zero, and the
   turn the city was kept - `--questions a3` answers this from the attack replies;
3. **the turn the first city is kept**, from the `KEEP|` reply;
4. **the turns under the gold floor**, both measures.

Commands, with A3's own session in the log filter:

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run flint-indigo-rampart-32 --from 1 --to 110 --verdict --questions a3
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run flint-indigo-rampart-32 --from 1 --to 110 --step 10 --verdict --questions a3 --save docs/experiments/A3-final.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs/experiments/A2-final.json docs/experiments/A3-final.json
```

## Mid-window review (end of T40 / T60) - filled as the attempt passes them

| question | answer |
|---|---|
| the opening build, against the pin | not yet measured |
| the establishment under the corrected table (Q1 wants <= T60) | not yet measured |
| the order of asking at the gate (H1's second test) | not yet measured |
| the wall pool: has any city been seen with `walls > 0` | **no city with a wall pool has been attacked yet** (checked at T77 of the previous branch: our three cities and the one met city-state all read `walls: 0/0`) |
| the economy at T20 / T40 / T60 against A1's and A2's | not yet measured |
| the gold floor, both measures (Q4 allows < 10 red turns) | not yet measured |
| the verdict so far on Q1-Q4 | not yet measured |

## The end table, and the verdict - written when the attempt ends

Not yet. When it does: the snapshot above, the `--compare` row against `A2-final.json`, the wall pool's
turn count, what the assault cost, and one paragraph saying what a walled target changed and what it did
not.
