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

Commands, with **every session this attempt has used** in the log filter - the list grows when a session
dies or is restarted, and a missing id silently drops the rows after it (session 3 started at T60, so two
ids would have hidden the whole assault):

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run flint-indigo-rampart-32,crumbling-emerald-parapet-16,marble-ebony-pennant-56 --from 1 --to 110 --verdict --questions a3
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run flint-indigo-rampart-32,crumbling-emerald-parapet-16,marble-ebony-pennant-56 --from 1 --to 110 --step 10 --verdict --questions a3 --save docs/experiments/A3-final.json
.venv\Scripts\python.exe scripts/experiment-report.py --compare docs/experiments/A1-T40.json docs/experiments/A2-final.json docs/experiments/A3-final.json
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
| **the establishment at T49** (11 turns left of Q1) | **`siege 2/2` in hand, and half of it was bought.** The first Catapult (ordered **T43**, the gate turn, `6 turns`) was **built at T48**; the second was **bought at T48** in the second city: `purchase_item(city_id=131073, UNIT_CATAPULT, YIELD_GOLD)` answered **`PURCHASED\|UNIT_CATAPULT\|cost=320g (had 347g)`**. At **T49 two Spearmen were ordered, one in each city** - the corrected table's **anti-cavalry row being filled for the first time in the programme**: A2 never built one and `counter-the-cavalry` was red for its whole assault. The instrument's order sequence reads `recon T1, ranged T5, melee T15, cavalry T26, siege T43, anticav T49`; screens 2, recon 2 (a second Scout at T46). **The purchase reaches past this attempt**: 320g is the exact price A6's arithmetic was rebuilt on, and A3's treasury held **347g at T48** - so A6's funding arm is a *measured* possibility on this start rather than a predicted one, while A6's variable stays distinct (it buys the **first** unit; A3 bought the **second**). **Correction, and it is why this row was rewritten twice:** its first version said one Catapult had been ordered, read off the tail of the log - the T48 purchase row was there all along. A list read by its tail is the failure this record exists to catch, and the correction is kept visible rather than silently overwritten |

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

## Q1 is answered - the corrected table is complete at T53, the first time in the programme

The instrument, run over both of A3's sessions at T54:

```
COMPLETE at T53   siege=2  melee=2  anticav=2  ranged=4  cavalry=1  recon=2
screens (melee + anti-cavalry): 4   recon: 2
first siege   : T48
first anticav : T53
HELD      Q1 establishment complete by T60 (corrected table)  [establishment T53]
```

**Seven turns inside the deadline, and it is the first attempt in the programme to complete the table.**
A1 never had the tech inside its window; A2's corrected-table establishment is `not reached` in its own
snapshot (`A2-final.json`: `"turn": null`), because it was short `ram 0/1` and `ranged 3/4` at T60 - and the
ram row is now conditional, so what A2 actually missed was ranged and the two rows the correction added.
A3 has all six, and **two of them over strength**: `anticav 2/1` (two Spearmen, T49) and `recon 2/1` (two
Scouts, T1 and T46). Over-strength is A2's own pattern repeating - it fielded three Catapults against a
table of two - and the record names it rather than counting it as a clean completion.

**The two rows the correction added are the ones that moved.** `first anticav T53` is the first
anti-cavalry unit this programme has ever fielded; `recon` was already A3's opening order. That is the
correction doing what it was written for (`counter-the-cavalry` was red for the whole of A2's assault, with
nothing in the army able to answer a Heavy Chariot), and it is worth stating plainly because **A3 is the
attempt that had to carry the correction's own confound**: its table is not the table A2 was measured
against.

**The gold floor, at the same read** (Q4, and the two measures still disagree): `0 red turn(s) by the rule
up to T60` because the rule is gated `when: turn() >= 60`, while the diary's own `gold_per_turn` is below
+10 on **47 of 52** turns. Q4 therefore stays `OPEN` until the gate opens, and the substantive number is
the diary's - which is the same finding A1 and A2 produced.

## The war declaration failed twice, and the fix that was supposed to make it work was dead code

**Measured at T59 and T60, before anything else about this attempt's assault can be read:**

```
T59 send_diplomatic_action -> WARN:WAR_UNCERTAIN|DECLARE_SURPRISE_WAR session completed but war state
                              not yet confirmed for 耶路撒冷. Check next turn.
T59 unit_action            -> MOVED_TO|50,21|...|BLOCKED (city-state territory (耶路撒冷) - need
                              suzerainty or Open Borders)
T60 send_diplomatic_action -> WARN:WAR_UNCERTAIN|... (the same reply, a turn later)
```

This is **A2's T60-T66 waste repeating**, and the cause is not the session's: the city-state branch in
`build_send_diplo_action` (`src/civ_mcp/lua/diplomacy.py`) tested
`Players[target]:IsMinorCiv()` **inside a `pcall`**. That accessor **does not exist in the InGame state** -
this project recorded that fact once already - so the pcall swallowed the error, the flag stayed `false`,
and control fell through to the diplomacy-session path the branch was written to avoid. The branch was
**dead code on every call**, and its fallback is exactly the `WARN:WAR_UNCERTAIN` message written for the
benign "not synced yet" case.

**The test that shipped with the fix is why nobody noticed**: `tests/test_city_state_war_declaration.py`
asserted that the string `Players[target]:IsMinorCiv()` appeared in the generated Lua, and that the branch
sat before `RequestSession`. Both were true - of a call that could never succeed. A test that pins a
*string* where the claim is about a *runtime path* is not a check; the retro's own ladder says an
unverifiable assertion is a workaround. (And the retro's row on the fix said "verified live" - which was
true of the player operation, verified by its own probe, and never true of the tool's guard.)

**The fix, and why this one can be checked**: the discriminator is the **session's own outcome**, which the
code already reads - a war action where `sessionCompleted` is false had no session to declare through, and
that is what a city-state is. The player operation runs in that case, `WARN:WAR_UNCERTAIN` is kept for the
case where a session *did* open (a major civilization, where the same-frame read is genuinely stale), and
neither accessor nor `pcall` is involved. `tests/test_city_state_war_declaration.py` now asserts the
outcome-based gate and that the uncertain wording belongs only to the session case; 6 tests pass.

**The session was restarted to load it, and that is part of this attempt's record.** A running `civ-mcp`
holds the modules it imported, so the fix cannot reach the session that was already playing - the same
constraint the retro records for the pantheon guard. A3's window is the one the fix exists for, so session 2
(`crumbling-emerald-parapet-16`, T25-T60) was stopped with `scripts\civ6-clean.ps1 -KeepGame` - the game
was left running, at **T60**, with the tuner ports still listening - and session 3
**`marble-ebony-pennant-56`** was launched into the same position. Every command in this record must
therefore name **three** sessions, and the live verification of the fix is the next declaration this attempt
places: an `OK:WAR_REQUESTED` reply is the fix working, and another `WARN:WAR_UNCERTAIN` means the branch is
still dead and the attempt's capture half is blocked by the tool for the second time in the programme.

**What this costs the comparison**: A3 lost T59-T60 to the failed declarations, and its assault opens two or
more turns later than the army was ready. That is a tool cost, not a production one, and the end table says
so - A1's capture half was decided by the map, A2's by a tool, and A3's by a tool *twice*.

**Verified live at T61, and it is what this attempt's assault rests on.** Session 3's declaration answered

```
WAR_REQUESTED|DECLARE_SURPRISE_WAR on 耶路撒冷 - no diplomacy session exists for this player, so the war is
requested through the same player operation the game's own declare-war popup uses, not by a session; the war
state settles on the next frame, so confirm it with get_diplomacy
```

and the war is real, not merely requested: at the same turn a Catapult took a **city** estimate
(`UNIT_CATAPULT vs CITY_CENTER (CS:0, HP:200)`) and fired - `RANGE_ATTACK|target:耶路撒冷 (city) at (50,22)`
- where under the blocked state the same order answered `NOT_AT_WAR` and a move answered `BLOCKED
(city-state territory)`. **So the two lost turns were the tool's, and the branch is now exercised by the
attempt it exists for.**

## Q2's evidence: every city this attempt has read says `walls: none`

**The wall phase is unaskable on this map, and the reads say so rather than an assumption.** As of T61:

| city | read | source |
|---|---|---|
| 耶路撒冷 (the target, city-state) | **`city hp: 200/200, walls: none`** | the first range attack, T61 |
| 霍巴特 (Australia's capital, pop 5) | `walls none` | `get_diplomacy`, T60 and T61 |
| 特赫基昂加-努伊-阿-库珀 (Maori, pop 4) | `walls none` | `get_diplomacy`, T60 and T61 |

Our own city, by contrast, is **offered** walls - `get_city_production` at T61 lists
`BUILDING_WALLS (cost 80, 5 turns, buy: 210g)` - so this is not a game where walls do not exist; it is a
position where no city being attacked has built one by T61. `tactics/07`'s Gate 0 was satisfiable (seven
candidates were known by T44), and the answer Gate 0 produced is that none of them is walled.

**Two consequences, and the record keeps them apart.** Q2's own falsifier is "no city with `walls > 0` is
found and attacked inside the window (unaskable - report the reads)", so A3's Q2 will be answered in the
terms the design allowed, with the table above as the evidence. But that also means **the programme's
central question is still unmeasured after two attempts** - A2's target read `walls: none` too - and the
honest conclusion is narrower than "the train works against walls": *on this start, at this tech level,
nothing attacked had walls*. A city-state builds Ancient Walls after Masonry and out of its own production,
so a later read could differ; the reads above are stamped T60-T61, and the brief requires re-reading cities
seen earlier, which is why this table names its turns.

## The assault's pool progression, read off the attack replies

The pool below is the **pre-attack** value on each turn's range attack, and it falls every turn - which is
the number that says the supply line is cut well enough that healing is not out-pacing the train (the
`cut-the-supply` rule fired at T61, one turn after the war opened):

| turn | pool before the shot |
|---|---|
| T61 | 200/200 |
| T62 | 175/200 |
| T63 | 158/200 |
| T64 | **129/200** |

Extrapolated, that is a city kept around **T69-T71** - inside Q2's own T68-T80 window and inside Q3's T80
deadline - and it is against `walls: none`, so the fall is the train's raw damage rather than a wall phase.
The record keeps the two facts apart: **A3 keeps a city on schedule, and it is not the city the attempt was
designed around.**

## The finish line is not met by this capture, and the attempt says so itself

A3's brief ends the attempt when **a city whose wall pool read above zero is kept**, or at **T110**. 耶路撒冷
is `walls: none`, so the capture does **not** end it: the attempt continues to look for a walled target inside
its T80 window and then to T110, re-reading cities already seen (Ancient Walls appear after Masonry and cost a
city-state its own production, so a city unwalled at T61 may wall later). **The session reached that
conclusion on its own** - its T66 diary reasons that "since 耶路撒冷 is unwalled, the attempt continues to T110
or until a walled city is kept" - which is the brief working as written rather than a session overrunning.

That has two consequences the record states plainly:

- **Q2's answer is neither "no" nor "yes"**: the instrument reports it `UNASKABLE` once this capture is on the
  log (the terminal status added for exactly this case), and the evidence is the `walls: none` reads and any
  later ones.
- **The window after the capture is not padding**: it is where a walled target would have to appear for the
  attempt's own question to be measurable at all. If the attempt reaches T110 with no `walls > 0` read, the
  honest conclusion is the narrow one already recorded - *on this start, at this tech level, nothing attacked
  had walls* - and the programme's central question goes into A4-A7 unanswered.

## The first city is kept at T67 - three of the four questions have answers

The capture, in the log's own words: `unit_action(move 50,22)` answered
`CAPTURE_MOVE|50,22|from:50,24|now_at:50,22|...|CITY TAKEN - resolve keep/raze with city_action`, the first
`resolve_city_capture(keep)` answered **`NO_PENDING_CITY|No rebelled or captured city pending decision`**, and
the retry answered **`KEEP|耶路撒冷 (pop 5, id:196610, captured)`**. The failed first call is the documented
shape of this tool - a capture reply is not the state - and the record keeps it because a reader comparing
this attempt's log with A2's will see the same race.

The instrument over all three sessions at T67:

```
HELD      Q1 establishment complete by T60 (corrected table)   [establishment T53]
OPEN      Q2 a walled target changes the arithmetic measurably [no city with a wall pool above zero was
                                                               attacked by T67 - unaskable on this map]
HELD      Q3 first enemy city kept by T80                      [first keep T67]
HELD      Q4 gold floor red on <10 turns                       [7 red turn(s) by the rule up to T67;
                                                                the diary's own gold/turn is below 10 on
                                                                48 of those 62 turn(s)]
```

**Q3's number is T67: one turn earlier than A2's T68**, inside Q2's own band, and **it is now A4's Q2 bound** -
A4's brief compares its capture turn against this one. **Q2 stays `OPEN` on purpose** while the attempt hunts
for a walled target, and turns `UNASKABLE` once T80 passes with none; the terminal status keys on the
question's own bound rather than on "a city was kept", because this keep was of an unwalled city and the
attempt is still looking (`b0fcb6f`).

**Q4's `HELD` is a window artifact, and the record says so rather than banking it.** The rule the criterion
names is gated `when: turn() >= 60` and the floor's horizon is the first keep, so T67 gave it **8 evaluated
turns** - and going red on 7 of 8 is under the allowance almost by construction. The diary's own measure,
which is live over the whole window, says the opposite of health: below the +10 floor on **48 of 62 turns**,
which is exactly what A1 and A2 showed. This is the mirror image of A1/A2's zero-evaluated-turns problem (their
horizon was T60, so the rule could never fire) and it is the reason Q4 names two measures: **a criterion whose
window opens at T60 and closes at T67 cannot decide whether the army was paid for.**

## T70: the turn stalled, and the recovery sequence as it happened

`end_turn` at **T70** answered, after about ten minutes of silence,

```
HANG:70:0_MCP_0070|End turn requested (turn is still 70). AI turn processing appears stuck.
```

The session then ran the sequence `docs/game-recovery.md` prescribes, in order, and each call came back empty:
`get_pending_diplomacy` (no sessions), `get_pending_trades` (no deals), `dismiss_popup` (**No popups to
dismiss**) - so **nothing in Lua saw a blocker**. The screen was then read with `.tools/whats-on-screen.py`,
which reported the game on **Turn 70/330** with an ordinary HUD, **no dialog and no leader screen**, and
**the game was not the foreground window** (a browser window was). That is trap 2 of the recovery document
almost exactly - "a fullscreen game must be in front" - so the game window was brought to the front
(a focus change; **no click, and no game action**), and the documented next step for a genuine AI-turn stall
is `restart_and_load("0_MCP_0070")`, the autosave the HANG line names.

**This is a tooling event and the record files it as one**: it consumed turns rather than measuring them, in
the same column as A2's six war-declaration turns and A3's own T59-T60. The resolution and its cost are in the
end table below.

**The cause is not the World Congress, and this paragraph first said it was - corrected here.** Reading the
MCP's own `end_turn` log for the retry shows `WC fires this turn with **0 resolutions** - auto-proceeding`, so
there were no votes to register and the Congress cannot have been the blocker; the first version of this note
inferred a cause from `get_world_congress`'s warning line and was wrong.

**What the MCP's own diagnosis recorded is the window, not the turn.** `.civ6-mcp-data/hang_diagnosis.jsonl`
holds three entries for T70, one per `end_turn`, each with the same shape:

```
{"turn": 70, "iso": "2026-09-29 22:47:26", "window": {..., "foreground": false,
 "foreground_window": "... DSH Local Build - Google Chrome"}}
```

- `22:47:26`, `23:00:47`, `23:15:55` - **all three with `foreground: false`**, and the window holding the
  foreground in every one of them is **the harness's own browser**, the UI this agent is driven through. The
  MCP re-focuses the game and retries before any restart (that is what its `HANG DIAGNOSIS` line does), and the
  focus goes back to the browser between attempts.

**And then it was not a focus problem either.** The human, watching the screen, reported the game sitting in
its **"Please wait" AI-turn phase for a long time** - a genuine stall in the game's own turn processing, not a
dialog and not a lost focus. On their call the game and the session were killed (`scripts\civ6-clean.ps1`, all
three of game, mcp and agent) and the position was left where it is safe: **`0_MCP_0070`**, written 22:36:21,
with the game's own `AutoSave_0070` beside it.

**The recovery has a step the tools do not cover, and it is worth recording.** The game was relaunched through
Steam (the raw EXE exits with code 53 - Steam's DRM needs Steam to start it: `steam://rungameid/289070`), and
the menu was in Chinese, where the MCP's OCR path looks for an English `Load Game`; the human changed the game
language to English. Even then **synthetic clicks do not reach the game**: `.tools/click-text.py` and a manual
`SetCursorPos` + `mouse_event` pair both reported a successful click with the game verified foreground, and the
menu did not move, while `.tools/drive-load.py` refused to navigate ("main menu not up yet ... not navigating
blind"). The most likely cause is the game running with a token that makes Windows drop injected input from
this non-elevated process. **So the load is done by hand**, and the attempt resumes from T70 when it is. What
this costs the attempt is wall-clock, not state: the T67 capture and every verdict that rests on it are already
in the log and in this record.

### The load does have a click-free path, and it works

Before asking a human for the three menu clicks, the input block was measured rather than assumed, and it is
total: `SetCursorPos(1917, 1016)` **returns False** and leaves the cursor at the user's own position
`(5055, 1366)`; `mouse_event` with `MOUSEEVENTF_MOVE|ABSOLUTE` moves nothing; `SendInput` reports **1** for a
mouse move (accepted) with the cursor still unmoved, and **0** for a keystroke (nothing sent). `.tools/click-text.py`
uses the same calls and therefore reports "clicked" while the menu does not move - the failure is in this
environment's input channel, not in the menu coordinates (the desktop metrics explain the rest: the primary
display is **2560x1440 logical** while the game window is 3840x2160 at (0,0), so a DPI-unaware caller would also
be off-target).

**What does work is Lua, and it needs no clicking at all.** The module carries a menu-load tier built for
exactly this - `game_lifecycle.load_game_save` asks the game's own FrontEnd states for the save list and calls
`Network.LoadGame` on the entry - and it was driven directly, outside the MCP, with a twenty-line script
(`.tmp/lua-load.py`, which is scratch and deliberately not committed):

```
=== list_saves ===
  1. 0_MCP_0070
  ... (filesystem scan, sorted by date)
=== load_save(1) ===
Network.LeaveGame(); Network.LoadGame(...)
```

The game then went through its loading screen and put up **"CHINESE EMPIRE JOINS THE WORLD STAGE"** - the
leader-introduction screen, which is the one step that still wants a person, since it is dismissed by input
and input is what this environment cannot inject. Two further facts worth carrying: `game_lifecycle.load_save`
(the index-based call) is **InGame-only** and answers `GameCore_Tuner/InGame states not found` from the main
menu, so the working call is `load_game_save(name)`, not `load_save(index)`; and **after a load the game's
tuner moved from 4318 to 4319** while `GameConnection` is hardcoded to 4318 - a mismatch that will bite any
MCP session started right after a recovery load, and one to check with
`Get-NetTCPConnection -State Listen | ? LocalPort -in 4318,4319` before blaming the session.

## The end table, and the verdict - written when the attempt ends

Not yet. When it does: the snapshot above, the `--compare` row against `A2-final.json`, the wall pool's
turn count, what the assault cost, and one paragraph saying what a walled target changed and what it did
not.
