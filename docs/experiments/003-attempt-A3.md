# Attempt A3 - the same doctrine against a walled target

**Status: in progress** - **two sessions so far**, both from the experiment's shared T1 start, started
2026-09-29. Session 1 `flint-indigo-rampart-32` played **T1-T25** and died mid-turn at T25 (20:56:59):
its stderr ends at `dsh: reasoning: H`, its job exited 1, and the log holds 165 rows with the last at
T25's `unit_action` (`CAPTURE_MOVE|43,25|from:45,23|BLOCKED`). The match kept running, so session 2
`crumbling-emerald-parapet-16` was launched into the same position at 20:57:35 - the task file carries a
note (added the same minute) telling it to continue from T25 rather than reload the T1 save, because
replaying would put two A3 branches in one log. The instrument's `--run` filter takes both ids, which is
how the commands below read this attempt. The attempt's instruction is `prompts/tasks/tmp/034-attempt-a3-the-same-doctrine-against-a-walled-target-from-the-shared-t1-start.md`;
the design is section 3 of `docs/experiments/README.md`; A1's and A2's records are
`001-attempt-A1.md` and `002-attempt-A2.md`, and the cross-attempt report is
`RETRO-2026-09-29.md`. This file is A3's record. A session that dies at ~T25 and is resumed is this
project's normal rhythm rather than a failure of the attempt - A2 needed three sessions for T1-T68.

## Settings: the shared start, the corrected table, one variable

| | A2 | A3 |
|---|---|---|
| start | `ATTEMPT-A1-T1-settled.Civ6Save` | **the same save** (loaded at T77 of A2's branch, which stays recoverable as `0_MCP_0077`) |
| doctrine | `tactics/01` as it stood | the **corrected** `tactics/01`: recon 1 and anti-cavalry 1 are required rows, the ram is conditional |
| the one variable | the target's distance | **the target's defences - a city whose wall pool reads above zero** |
| window | to the capture (T68) | `KEEP|` of a walled city, or **T110**; `expires:` T115 |

**A3 differs from A2 in two ways by design, and the record says so**: the establishment table (corrected
after A2) and the target's defences. That is why the capture arithmetic below is compared against A2's T68
with both differences in mind, rather than read as a clean single-variable delta. **And in a third way by
execution: A3's opening is not the pinned one** - measured below, from the log's order sequence, and it
qualifies Q1 and A4's Q2 rather than being waved through.

## The opening build is pinned (the protocol's rule from A3 on)

`SCOUT` -> `SLINGER` -> `SETTLER` -> `BUILDER`, order by order. The pin was published at **20:23:19**
(commit `7fd3132`, which re-published task 034 with it); the first order, the Scout, had already been placed
at 20:16:37, so the pin records that fact rather than pretending to have governed it.

**The executor's opening, as the log holds it - and the pin did not hold:**

| order | promised | the record |
|---|---|---|
| 1 | `UNIT_SCOUT` | **T1** (20:16:37) - matched, and placed before the pin existed (it is the corrected table's recon row: the first attempt in the programme to open with it on purpose) |
| 2 | `UNIT_SLINGER` | **T5** (20:23:03) - matched, 16 s before the pin was published |
| 3 | `UNIT_SETTLER` | **T6** (20:24:05) - matched |
| 4 | `UNIT_BUILDER` | **NOT MATCHED: the 4th order was `UNIT_WARRIOR` at T15 (20:36:21).** The first `BUILDER` is the 6th order, at T19, and it went to the second city (131073); the capital took one at T22 |

Every order from T6 on was placed **with the pin in force**. The session's own T15 `planning` line asks for
"Warrior #2 (melee 2/2), then Slinger, then the Campus when Writing lands" and never mentions the pin - so
the deviation has a doctrine reason, but not the reason the pin requires. This record claimed "matched" for
it until the order sequence was read out of the log order by order; the mid-window line below had it right
even then ("the pin's fourth order (`BUILDER`) not placed at T12").

**What that costs.** A3 differs from A2 in three ways, not two: the corrected table, the target's defences,
and an opening that is not the pinned one. Q1 (the establishment complete by T60) is the verdict that
depends on the opening, so it is read with that qualification, and A4's Q2 - which uses A3's keep turn as
its bound - inherits the caveat. The sink for this is mechanical and it has **landed**: run against this
attempt's own log, `scripts/experiment-report.py` now prints `PIN opening: DEVIATED - opening order 4 was
UNIT_WARRIOR on T15, not UNIT_BUILDER - the pin did not hold` in the ordinary `--verdict` output and in
every snapshot, so no attempt's pin can be glossed in prose again; A4-A7's task files carry the consequence
that a deviated opening is **re-run from the shared start** rather than reasoned about.

**A second difference that is the tool's, not A3's: the pantheon, and it is measured rather than assumed.**
A2's first session could not found a pantheon **at all** - `choose_pantheon` at T21 answered
`ERR:Runtime Error ... operator < is not supported for number < string` on every call - so A2 played its
whole productive window with no pantheon and founded God of the Forge only at **T41**, in its second
session. A3 asked at **T23** (`Error: NOT_ENOUGH_FAITH|faith 17 < 25`) and again at **T25**
(`faith 23 < 25`) - and **founded 锻造之神 at T26** (`PANTHEON_FOUNDED|锻造之神`, the first turn the guard
let it through: session 2 asked again the moment the turn started). The guard is numeric since `37bb7a9`
(the A1/A2 crash is gone), but it compares faith against the **standard-speed** cost of 25 while this match
is **Quick**, where the game's own offer arrives at about 17 - so those two refusals are the tool's
documented conservatism (`src/civ_mcp/lua/religion.py:70` says so itself) and they cost A3 two turns of
asking, not a pantheon. So A3 plays T1-T25 with no pantheon and
**T26 onward with God of the Forge, fifteen turns earlier than A2's T41** - if A3's siege half lands
earlier than A2's T48/T55, the pantheon is one of the reasons and the record says so rather than attributing
it all to the target's defences. (The refusals are in the log as `choose_pantheon` rows with their `ERR:`
text, and that row-level detail is why this paragraph exists: the session's own reasoning said "Pantheon
available - taking God of the Forge" at T25, and the reply it got was a refusal. A call is not a result.)

Research follows A1's and A2's shape: `TECH_MINING` T1, `TECH_THE_WHEEL` T8, **`TECH_ENGINEERING` T22** -
the same turn A2 began it, which is the gate H1 is measured at (A2's landed T48, and the two attempts
started it on the same turn, so the tech timeline is comparable). Civics: Craftsmanship T11, Foreign Trade
T20, State Workforce T24.

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
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run flint-indigo-rampart-32,crumbling-emerald-parapet-16 --from 1 --to 110 --verdict --questions a3
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run flint-indigo-rampart-32,crumbling-emerald-parapet-16 --from 1 --to 110 --step 10 --verdict --questions a3 --save docs/experiments/A3-final.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs/experiments/A2-final.json docs/experiments/A3-final.json
```

## Mid-window review, read out of the instrument at T24

**The instrument is ready for this attempt, and the attribution was rehearsed before the numbers matter.**
A3 re-plays T1-T40, and A1 and A2 wrote diary rows for those same turns on the same game key - three
candidates per turn. Run against the partial log at T12, the report attributes T1-T12 to A3's own rows
(T10: military 21, faith 2.0 - neither A1's 34 nor A2's 31) and **names** T13-T60 as unattributed rather
than borrowing the earlier attempts' rows.

Run at T24 (`--game china_911679432 --run flint-indigo-rampart-32 --from 1 --to 25 --verdict
--questions a3`; the session's own rows are attributed to T1-T24, 30 later turns are named as
unattributed rather than borrowed):

| question | answer at T24 |
|---|---|
| the opening build, against the pin | **NOT matched** - the 4th order was `UNIT_WARRIOR` T15, with the pin in force since 20:23:19 (the section above has the order-by-order table and what it costs) |
| the establishment under the corrected table (Q1 wants <= T60) | **not complete at T24**: `siege 0/2, melee 2/2, anticav 0/1, ranged 2/4, cavalry 0/1, recon 1/1`; screens (melee + anti-cavalry) 2, recon 1; first siege: never |
| the order of asking at the gate (H1's second test) | **measured: HELD at T43** - the section below has the instrument's own line |
| the wall pool: has any city been seen with `walls > 0` | **no** - nothing with a wall pool has been attacked by T24, and the instrument says so in A3's own Q2 line; at T24 the map is 10% revealed (2% at T1) and **no rival has been met**, so there is no city to aim at yet - the same shape A1 hit |
| the economy at T20 / T40 / T60 against A1's and A2's | T24 not measured; the composition and exploration above are the instrument's own reads for this window |
| the gold floor, both measures (Q4 allows < 10 red turns) | **the two measures disagree at T24**: `carrying-capacity` red on **0** turns (it is gated to T60 in this build), while the diary's own `gold_per_turn` is below +10 on **24 of 24** turns - which is the A1/A2 finding repeating, and the reason Q4 names both |
| **the establishment at T45** (Q1's countdown, 15 turns left) | **short `siege 0/2` and `anticav 0/1`**; `screens (melee + anti-cavalry) 2`, `recon 1`. The first Catapult was ordered at T43 and is still building; **no anti-cavalry unit has been asked for at all**, which is A2's own hole repeating - `counter-the-cavalry` was red for A2's entire assault because nothing could answer the Heavy Chariot, and it is the role the correction *added*. A3 ordered a second `UNIT_SCOUT` at T46, so its recon spend is going up while its siege count stands at one |
| the verdict so far on Q1-Q4 | all four `OPEN` at T24 (the deadlines have not arrived): Q2 already carries the warning that the wall phase is unaskable if no `walls > 0` target is attacked - and that is A3's own answer to give, not a failure to report |
| production orders, all of them | `SCOUT` T1, `SLINGER` T5, `SETTLER` T6, `WARRIOR` T15, `SLINGER` T18, `BUILDER` T19 (second city 131073), `SLINGER` T20, `BUILDER` T22 (capital) - 8 units, all of them army roles, and `H5 clean` (no ram, no siege tower ordered or bought) |
| the pre-gate economy orders (H1's own context) | session 2 spent on the economy **before** the gate: `UNIT_TRADER` T30, `BUILDING_WATER_MILL` T33 (capital) and T35 (second city). A2's pre-gate spend was `UNIT_BUILDER` T43 and `UNIT_TRADER` T46 - so A3 arrives at its gate with more economy already bought, and H1's claim is about the **gate turn's** choice, which both attempts had free. The comparison is only fair if the gate turn is read the same way in both, and the instrument does that |
| **the target set, read at T44** (Q2's raw material) | **six city-states plus a free city are known**: 安善 (Scientific), 桑给巴尔 (Trade), **耶路撒冷** (Religious - the one A2 captured), 撒马尔罕 (Trade), 欣盖提 (Religious), and **自由城市 (`player 62`, Unknown)**. Explored **18% of land (241/1323 tiles)** by T44, against A2's **7%** at T68 with no scout ever built. This is the corrected table's recon row doing exactly what the correction was for: A2 met one city-state and Babylon; A3 has seven candidates to read for a wall pool, and `tactics/07`'s Gate 0 - "a candidate city is actually visible" - is satisfiable on this position |

## The Engineering gate, measured - T43, and H1 holds for the second time

**`TECH_ENGINEERING` landed at T43** (the diary row for T43 is the first whose `techs` list carries it; at
T42 the tech read `1 turns`), and the same turn the capital was asked for `UNIT_CATAPULT`. The instrument's
own words, `--questions a2` over both sessions:

```
HELD  Q2 the siege train ordered before any economy order after Engineering
      [Engineering T43; first siege order T43, no economy order since]
```

That is H1's second test and it holds, in the same shape as A2's: **the train is asked for on the gate turn
itself, before anything economic.** The boundary is worth stating because A3 tested it: at **T42**, with
Engineering one turn out, the capital was given `BUILDING_MONUMENT` - an economy order placed while the
tech was still researching, which is what A2 did too (`UNIT_BUILDER` T43, `UNIT_TRADER` T46, both pre-gate).
Read strictly as "no economy order while the tech is imminent", T42 is a near-miss; read as the record has
read it since A2 - **the first order after the tech exists** - it is clean, and the instrument says so in
one line rather than in prose.

**A3's gate is five turns earlier than A2's, and the record says why.** T43 against T48. The cause is
visible in the same log: A3 appointed **平伽拉 (`GOVERNOR_THE_EDUCATOR`)** in 西安 at **T41** and took
`GOVERNOR_PROMOTION_EDUCATOR_RESEARCHER` the same turn, and its science at T42 reads **12.4** against A2's
**5.9** at T40 (A2's reached 13.3 only at T50). So this attempt diverges from A2 in another way that is not
its variable: an economy-and-science line A2 never ran. That makes A3's **siege half arriving before A2's**
attributable to more than the corrected table, and it is the third such difference on this record (the pin,
the pantheon, the governor). None of them is the target's defences, which is what A3 was built to test -
and the delivery of the train is not what A3's questions are about, so the divergence is recorded as
context rather than as a falsification.

## The end table, and the verdict - written when the attempt ends

Not yet. When it does: the snapshot above, the `--compare` row against `A2-final.json`, the wall pool's
turn count, what the assault cost, and one paragraph saying what a walled target changed and what it did
not.
