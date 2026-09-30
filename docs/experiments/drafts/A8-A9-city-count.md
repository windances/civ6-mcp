# A8 / A9 - the city count as the variable (three cities, then four)

**Status: design note, not published.** Neither attempt has a task file, and neither should get one
until the pre-flight in section 7 has been run - no attempt in the programme has ever read the settle
advisor *after* its second city existed, so the third and fourth sites on this start are unknown. This
note exists so that when the pre-flight is taken the claim is already written and can be cut to its
arithmetic the way A6's and A4's were, before ~70 turns are spent playing it.

## 1. What is genuinely untested

**A second Settler has never been ordered.** Across all eight A3-A7 sessions the only `UNIT_SETTLER`
order is the one the pinned opening asks for (slot 3: T6 in A3/A5/A7, T10 in A4/A6). Every attempt
therefore sits at **two cities** through T50, and the third city is always a **capture**:

| attempt | T20 | T30 | T40 | T50 | third city |
|---|---|---|---|---|---|
| A3 | 2 | 2 | 2 | 2 | 耶路撒冷, taken T67 |
| A4 | 1 | 2 | 2 | 2 | 耶路撒冷, taken T65 |
| A5 | 1 | 2 | 2 | 2 | none |
| A6 | 1 | 2 | 2 | 2 | none |
| A7 | 1 | 2 | 2 | 2 | 耶路撒冷, taken T60 |

*(`cities` per row, from each `A*-final.json`'s `economy` array.)* So "three cities" and "four cities"
are not variations on something the programme has measured - they are the one arm of the empire that
five attempts held fixed. The settle advisor was read **three times in eight sessions** (A7 T7, A7 T15,
A6 T18) and **all three reads precede the second city's founding** (A7 T21, A6 T27).

## 2. The pre-flight arithmetic

`UNIT_SETTLER` (`Base/Assets/Gameplay/Data/Units.xml`) is `Cost="80"` with
`CostProgressionModel="COST_PROGRESSION_PREVIOUS_COPIES"` and `CostProgressionParam1="30"` - **+30 base
production per Settler already built** - plus `PopulationCost="1"` and `PrereqPopulation="2"`. Quick
speed is `CostMultiplier 67` (`GameSpeeds.xml:46-47`), so:

| cities to hold | Settlers needed | base production | Quick production | population taken | queue turns in 西安 |
|---|---|---|---|---|---|
| 2 (what A1-A7 all did) | 1 | 80 | 54 | 1 | 11 (T6 order, measured) |
| **3 (A8)** | 2 | 190 | 127 | 2 | +8 |
| **4 (A9)** | 3 | 330 | **221** | 3 | +18 |

The comparison that decides the shape of the claim: `UNIT_CATAPULT` is 120 base / **80 Quick**, and
A7's 西安 built one in **6** and one in **5** turns (T45, T53). The **two extra Settlers A9 needs cost
about 18 turns of 西安's queue - more than the 11 turns that built the entire two-Catapult siege
train.** In `POLICY_AGOGE` terms (which a civilian unit does not receive) the extra 167 Quick
production is **3.1 Catapults**.

The capital is the city that pays this, and the capital is the war city. A5 already measured what it
costs to lean on it: 西安 at `pop 6` with `SLOW GROWTH: 24 turns to next pop`, `Prod ~10`, seven turns
per Catapult - and A5's establishment was the programme's slowest (T57). Each Settler also takes a
**population point** out of that city, which is the same city's production.

## 3. The land is the harder constraint

A7's T15 read is the only pre-founding ranking the programme has, and its top ten is **one cluster**:

```
#1 (53,21) 215   #2 (54,22) 204   #3 (55,22) 200   #4 (54,21) 193   #5 (55,21) 192
#6 (53,20) 182   #7 (56,22) 177   #8 (54,23) 176   #9 (56,23) 170   #10 (53,23) 168
```

Every one of the ten falls inside **x 53-56, y 20-23** - a 4x4 block - and they are *alternatives*,
not a plan: the advisor excludes any tile within 3 tiles of a city
(`src/civ_mcp/lua/map.py:59`, and the game's own refusal it mirrors, *"Too close to ... need > 3"*,
`:389`). A6 took its T18 **#1** (54,22) and A7 took its T15 **#1** (53,21) - two tiles apart, so only
one of them could ever have been founded. **The good land supports about two cities, and the third
site is somewhere the advisor has never been asked about.**

This is a land finding, not a production one, and it is why the pre-flight comes first: if the best
remaining legal site has no fresh water or scores far below the cluster, A9 is dead before it starts -
exactly the class of pre-publication falsification that killed A4's first form (*"No attempt has ever
built an Encampment at all"*) and cut A6's claim to one purchase.

### 3b. The pre-flight was taken, and it corrects the paragraph above

**Measured 2026-09-30, T69 of the A7 continuation** (`stormborn-azure-palisade-94`) - the read no attempt
had ever taken, with three cities standing. Its top ten is **not** the cluster above, and it is not a
worse list:

```
#1 (40,26) 217  fresh water  STONE, HORSES, COPPER, BANANAS, MAIZE, WHEAT, FURS
#2 (40,28) 211  fresh water  COPPER, BANANAS, MAIZE, WHEAT, DYES, HORSES
#3 (39,29) 207  fresh water  BANANAS, WHEAT, MAIZE, FURS, HORSES, DYES
#4 (39,25) 205  fresh water  ...   #5 (41,27) 203   #6 (41,28) 202   #7 (42,27) 202 **no water**
#8 (40,27) 202  fresh water  ...   #9 (40,29) 200   #10 (39,27) 197
```

**What this corrects.** The T15 cluster is gone from the list because it is now *excluded* - Chengdu
(53,21), 成都 and 西安 sit on it - so the near land really is used up, exactly as section 3 said. **But a
second cluster of the same quality exists**, at **x 39-42 / y 25-29**, and **nine of its ten sites have
fresh water** (only #7 does not), where the old cluster's top ten had three dry sites. It is a *better*
list, not a worse one, and its #1 scores **217** against the 215 that A7 actually settled on.

**So the land does not kill A8, and the constraint is not land at all - it is distance.** (40,26) is about
**11 tiles from 耶路撒冷 and 14 from 成都**: the third city is an **expansion, not a satellite**. It shares no
tiles with the core, it needs its own garrison and its own Builder, and the Settler's walk is turns taken
out of the window before the city even exists. Section 4's timeline does not include that walk; **it has to
be added to it** (a two-move Settler over eleven tiles of hills and forest is roughly ten to fourteen
turns, and `get_pathing_estimate` is the tool that says which).

The second correction is a tool one: **the advisor returns a top ten, not a census**, so the question this
section's pre-flight asked - *how many legal sites remain at all* - is **not answerable from its output**.
What can be said is what the read shows: the best ten are one cluster, and anything closer than x 43 scores
below 197.

## 4. The timeline, from the one second city measured

A7's Chengdu (founded **T21**) is the only data point for what a new city contributes:

| | Chengdu (131073) | 西安 (65536) |
|---|---|---|
| first order | T21 `UNIT_SLINGER`, **9 turns** | - |
| first Catapult ordered | **T45 - 24 turns after founding** | T45, 6 turns |
| second Catapult | T57, **9 turns** | T53, **5 turns** |
| share of the empire's army orders | **41%** | 59% |

*(A7's log, every `set_city_production` by city id.)* A new city therefore needs **~24 turns** before
it contributes anything siege-relevant, and it does so at **~1.5x the capital's turn cost**.

Chained from the same measured rates, the dose-response looks like this:

| | founded | first army order | first Catapult ordered | reaches the first train? |
|---|---|---|---|---|
| city #2 (both attempts) | T21 | T21 | T45 | yes - it built one of the two |
| city #3 (A8) | ~T28 | ~T30 | ~T52 | marginal |
| city #4 (A9) | ~T40 | ~T50 | ~T64, complete **~T72** | **no** |

The programme's keeps landed at **T60 (A7), T65 (A4), T67 (A3), T68 (A2)**. **City #4 cannot affect
any of them.** Both attempts must therefore be judged on the T70-T110 horizon and on the economy, not
on the first keep.

## 5. The claims, cut to their arithmetic

**A8 - three cities, and the third one is an economy city.** One variable against the shared start: the
pinned opening is overridden to a second Settler (settle-first), and the third city's queue is markets
and routes, not army.

> **Hypothesis (falsifiable by numbers):** the third city's *first* contribution is gold, not
> production - it buys the **second** Catapult. The number is the **second** siege unit **in hand by
> T58, bought and not built**, against A6's single purchase at T46 (`PURCHASED|UNIT_CATAPULT|cost=320g
> (had 396g)`) - A6 bought the *first*, A8 produces the first and buys the second, and the compare
> block already carries that caveat for A6's `siege_order` column. The floor is **`gpt_T50` above A7's
> 8.1**, which is the clause a market is supposed to move; **`gpt_T40` is a prediction and not a bar** -
> it is expected at or below A7's 6.1, because a third city founded about T30 has no market by T40 and
> is meant to cost gold before it pays. Falsified if the second siege unit is not in hand by T58, if it
> was built rather than bought, or if `gpt_T50` is not above 8.1.

**A9 - four cities, and it answers A8's open end.** Same variable, one more dose: if A8 shows the third
city paying, A9 shows whether it scales; if A8 shows it not paying, A9 locates the turn the curve goes
negative - which is a number the programme does not have for any city.

> **Hypothesis:** the fourth city's first army-relevant order arrives **before** the third city's, and
> `gpt_T50` is at least **3** above A8's. Falsified if city #4's first army order is later than city
> #3's, or if the fourth city never reaches fresh water.

**Why A9 is sequenced behind A8.** Not because it is weaker - because A8's result is what gives A9's
claim its meaning, and each attempt costs ~70 turns of play. The protocol has done this before: the
Encampment variation was moved down the queue behind the wall-phase attempt for the same reason
(`README.md:166-168`). **A9 is published only if A8 runs.**

## 6. Why the outcome is likely to be a falsification, and what that is worth

The arithmetic in sections 2-4 says both attempts **lose the first keep**: three Settlers cost more
queue time than the whole siege train, the good land holds about two cities, and city #4 lands after
every keep the programme has ever taken. That is not an argument against running them - it is the
argument for writing the claim *before* running them, which is how A6's claim was cut and how A4's
premise was found false.

What they are worth if they fail is the **response curve**: the programme currently has one point (two
cities, keep T60-T68) and no idea what the third and fourth cities are worth. A8 and A9 are the only
way to get the second and third points, and the curve is what a future doctrine (`tactics/08`'s "the
war city builds the war, everything else compounds") actually needs - it currently asserts a direction
with no measured slope.

## 7. The pre-flight, before either attempt is published

1. **Read the settle advisor again with two cities standing** - the read no attempt has taken. A7's T15
   ranking is pre-founding and is therefore about a map with one city on it; the third site must be
   named on the map as it will be, with its water and its own score.
2. **Name the third city's site and its first four orders in the task file**, the way the pinned opening
   is named, or the attempt is two variables again (README section 3's pinning rule).
3. **Write the `overrides:` line**, because "settle first" contradicts H1 (*siege first*) and replaces
   the pinned opening. That is legitimate - A7 widened `tactics/08` the same way - but it has to be in
   the file or the review reads it as drift.
4. **State the window from the queue, not the calendar**: city #4 completes its first Catapult around
   T72, so the window is A7's **T110**, and `expires:` must be reachable from that.

## 8. The collision that has to be decided in the file

`dynasty-cycle-wonder` is now live from **T25** (`prompts/checks/turn-checks.md`) and fires every turn
until a wonder exists. The third city - the compounding city in `tactics/08`'s own split - is the
natural place to build one, and **it is the same city A8 wants for markets**. A wonder pays a Eureka
*and* an Inspiration of its era (`Expansion2_Civilizations.xml:73`); a market pays gold toward the
320g that buys a Catapult. Both are "the city that is not the war city", so **A8's task file has to say
which one it is and why the other was dropped** - otherwise the attempt answers neither question, and
the audit in `CHINA-KIT-AUDIT.md` ends up recording a second programme that tracked China's kit and did
not play it.

## 9. The handoff from the A7 continuation to A8, verified before it is needed

**FireTuner serves exactly one connection**, so A8 cannot attach while the A7 continuation holds it. The
tool for the handoff is `scripts\civ6-clean.ps1`, and **the switch matters more than anything else here**:

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1 -DryRun      # report only
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1 -KeepGame    # <-- the handoff
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1              # ALSO KILLS THE GAME
```

**`-KeepGame` is the one to use, and the plain invocation is a footgun**: it stops the game as well, and
A8 needs Civilization VI *running* to load the shared start - killing it means a Steam relaunch before
anything can be measured.

Measured 2026-09-30 with `-DryRun` while the continuation was live, so the plan below is what the tool
actually resolves rather than what it is documented to do:

```
plan
  game       28736:CivilizationVI_DX12
  mcp        20696:python
  agent      4588:node, 25548:node
  node?      none
state
  delete       heartbeat.json  {"phase": "playing", "turn": 91, ... "run_id": "stormborn-azure-palisade-94" ...}
```

So `-KeepGame` stops **the MCP and the agent** and deletes the stale heartbeat, and leaves the game. The
Web GUI is found by its port and excluded from every kill list (`protected: ..., 4992 on :3080, ...`), so
cleaning a game session cannot take down the interface driving it.

**The order, then**: A7 reaches T110 -> the session retires task 039
(`python scripts/temp-task.py retire 039 --done --turn 110 --note "..."`, which has its own `--dry-run`)
-> if anything still holds the tuner, `civ6-clean.ps1 -KeepGame` -> publish task 040 -> launch A8 from the
shared T1 start. **The stale heartbeat is the trap this order removes**: left in place it describes a run
that no longer exists, and a `"phase": "playing", "turn": N` from a dead session is exactly what makes a
stopped game look live.

