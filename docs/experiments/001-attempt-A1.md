# Attempt A1 - the military production doctrine as written

**Status: in progress** (created 2026-09-29, before the first turn was played).

The experiment this belongs to is `docs/experiments/README.md`; the instruction the session plays
under is `prompts/tasks/tmp/030-military-production-attempt-a1.md`. This file is the attempt's
record: the settings as they were read back from the running game, the one variable, the hypothesis
with its numbers, and - once the attempt ends - the table and the verdict.

## Settings, read back from the game

| Parameter | Value | Where it was read |
|---|---|---|
| Civilisation | China, Qin (Unifier) | `PlayerConfigurations[0]` = `LEADER_QIN_ALT` / `CIVILIZATION_CHINA` |
| Opponents | 2 - Australia (John Curtin), Maori (Kupe) | the only other major players in the read-back |
| Difficulty | Prince | the setup screen read 王子 |
| Map | Pangaea, Small | the setup screen read 盘古大陆 / 小 |
| Speed | Quick | the setup screen read 快速 |
| Ruleset | Gathering Storm | `GameConfiguration.GetValue("RULESET")` = `RULESET_EXPANSION_2` |
| Game key | `china_911679432` | `<civ>_<GAME_SYNC_RANDOM_SEED>` read from the live game - a different seed from the previous match, so the two diaries do not mix |
| Turn 1 save | `evals/saves/ATTEMPT-A1-T1.Civ6Save` | the untouched start: 4000 BC, the Settler still standing, no action taken |
| Shared start | `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` | **the experiment's shared starting position**: turn 1 with the capital founded, so every attempt loads this one and the map, the opponents, the capital site and the difficulty do not move under the variable (`docs/experiments/README.md` section 2) |
| Capital | 西安 at (60,22), founded T1 | the Settler's own tile, because `get_settle_advisor` ranks it **#1 for this start: score 190** against 177 for the runner-up (fresh water, defence 5, MAIZE/SUGAR/STONE/DYES in reach) - the site is the tool's own first answer rather than a choice made here |

**How the match was created, since it is reproducible and was not obvious.** The game was launched
from this checkout (`_launch_game_sync`), which needed full filesystem access - under the workspace
sandbox Civ 6 dies seconds after starting because it must write its own user directory
(`Documents/My Games/...`, outside the workspace; measured: the same write is refused with
`Access to the path ... is denied`). The Create Game screen was then driven by OCR and absolute
clicks, **except** the leader pulldown: it holds 54 entries, shows 11, and scrolls through no channel
this machine offers - the front-end Lua has no `eMouseWheel` handler, there is no scrollbar in the
pulldown's pixels, and arrow keys, PageDown and type-ahead are all inert. The leader, the civilisation
and the opponent count were therefore written into the engine's own pregame model over FireTuner
(`PlayerConfigurations[0]:SetLeaderTypeName("LEADER_QIN_ALT")`,
`:SetCivilizationTypeName("CIVILIZATION_CHINA")`, `:SetSlotStatus(2)` for players 3-9), which the
setup screen then displayed as 秦始皇（大一统）. Difficulty, map size, speed and map type were set
from the screen's own pulldowns, which are short enough to fit.

## The one variable

**None.** This attempt plays `prompts/tactics/01-unit-production.md` as written, so a later attempt
has a baseline. The claims under test (H1-H6) are tabulated in `docs/experiments/README.md`.

## The hypothesis, with the numbers that would falsify it

| # | Prediction | Falsified when |
|---|---|---|
| P1 | The first siege unit is in a city queue by **turn 45** | no Catapult is queued by T45 |
| P2 | The **establishment is complete by turn 60** - siege 2 / melee 2 / ram 1 / ranged 4 / cavalry 1 | the composition at T60 is short in any role |
| P3 | **The first enemy city is kept by turn 80** | T80 arrives with no `KEEP|` in the log |
| P4 | The army is paid for without breaking the economy: `carrying-capacity` (gold/turn >= 10) is red on **fewer than 10 turns** between T1 and T60 | gold/turn is below 10 on 10+ turns before the first city falls |

## The two decisive numbers

Both are computed by the instrument from the record - the diary's `unit_composition` and the
`KEEP|` reply - and the session's diary line is a cross-check on them rather than their source:

1. **the turn the establishment first matches the table**, checked on every turn;
2. **the turn the first enemy city is kept** (never taken from prose).

The match's key is **`china_911679432`** (`<civ>_<GAME_SYNC_RANDOM_SEED>`, read from the running
game), and it is the argument every command below needs.

## What the attempt cost (filled in when it ends)

The report command, whose output goes in the table below:

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --step 10
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --verdict
```

`--verdict` answers P1-P4 from the record. `P1` is the one worth stating carefully: it measures the
turn a siege unit was **ordered** (read from the log's `set_city_production` / `purchase_item` calls)
and falls back to the turn one was **owned** only when the log holds no such order - the label says
which answered. The diary records units, the log records choices, and the doctrine is a claim about
the choosing; the report also prints the first order in each category, the turn the army began, and
the turn the siege train was first asked for.

| field | value |
|---|---|
| establishment complete | not yet measured |
| first city kept | not yet measured |
| economy at T20 / T40 / T60 | not yet measured |
| rule failures (top 3) | not yet measured |
| refusals (`STOPPED_MID_PATH` etc.) | not yet measured |
| verdict on P1-P4 | not yet measured |

## Mid-window review (end of T40) - written when the session stopped there

The session stopped at the end of turn 40 and exited (its process is gone, the game stands at T41, the
diary holds forty rows). Everything below comes from the instrument over its own session
(`--run vigilant-sable-longbow-78`), whose snapshot is `docs/experiments/A1-T40.json`:

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --run vigilant-sable-longbow-78 --from 1 --to 40 --step 10
```

### What the forty turns bought

| turn | science | culture | gold | gold/t | faith | military | pop | cities | districts | improvements |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | 2.5 | 1.3 | 6 | 5 | 0 | 20 | 1 | 1 | 0 | 0 |
| T10 | 3.5 | 1.9 | 51 | 5 | 0 | 34 | 3 | 1 | 0 | 0 |
| T20 | 4.5 | 2.5 | 101 | 5 | 44 | 38 | 5 | 2 | 0 | 0 |
| T30 | 6.5 | 3.1 | 167 | 7 | 109 | 118 | 7 | 2 | 0 | 2 |
| T40 | 7.9 | 4.3 | 236 | 6 | 185 | 139 | 8 | 2 | 1 | 2 |

| window | science | culture | gold | faith | military | pop | cities | districts | improvements | techs | civics |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1-T20 | +2.0 | +1.2 | +95 | +44 | +18 | +4 | **+1** | 0 | 0 | +2 | +1 |
| T21-T40 | **+3.9** | +2.1 | +130 | +135 | **+101** | +4 | **0** | +1 | +1 | +1 | +2 |

So the attempt has a clean shape and it is not the shape the doctrine asked for: **T1-T20 expanded
(one new city, no infrastructure) and T21-T40 built an army - the cheap screens - while expanding not at
all.** Science trebled over the run (2.5 -> 7.9) and the army went 38 -> 139, but the empire is still two
cities, which is the opposite of the directive's "four to six cities, then stop".

**Composition:** `T1 WARRIOR:1` -> `T10 +SCOUT` -> `T20 +BUILDER` -> `T30 SLINGER:4, WARRIOR:2, SCOUT:2,
BUILDER:1` -> `T40 unchanged`. Ten turns of movement and no new unit.

**The establishment at T40:** melee 2/2 and ranged 4/4 are met; **siege 0/2, ram 0/1, cavalry 0/1 are
at zero**, and no siege unit was ever ordered (`first siege: never`). Screens 2, recon 2.

**Rules and refusals:** the only rule that ever fired is `issue-the-calls-furthest-first`, **8 times**.
Refusals: `STOPPED_MID_PATH` 106, `BLOCKED` 38, `NO_MOVES` 6, `STOPPED_SHORT` 2, `ERR:` 2 - and every
stop whose reason the log prints says `(moves exhausted)`, none says another unit was in the way.

**The attempt's own cost:** 274 tool calls over 40 turns = **6.8 a turn**, against the ~39 a turn the
previous match measured at T272-T287. `get_game_overview` was called **5 times in 40 turns**, where the
skill asks for it every turn - the session economised on the TURN START briefing and said so.

**Contact and exploration:** the map went 2% -> 14% revealed, and **by T40 no rival had been met at
all**. There is therefore no city to aim at, and no battle has been fought.

### The verdict, and the two predictions that do not need the clock

| prediction | status at T40 | why |
|---|---|---|
| P1 a siege unit by T45 | **OPEN** | T45 has not arrived; none ordered yet |
| P2 establishment complete by T60 | **OPEN by the clock, already impossible by arithmetic** | Engineering ~T42 + 160 production for two Catapults puts the siege half at T62-T70, before melee/ram/cavalry (see the arithmetic note below) |
| P3 first enemy city kept by T80 | **OPEN by the clock, already impossible by the map** | the only rival capital is 33 tiles west behind five city-states, no rival is met, and the army is 33 tiles from anything it could take (see the map section below) |
| P4 gold floor red on <10 turns | **OPEN** | 0 red turns so far, window still running |

**The executor's honesty is a positive result of this attempt**: the session wrote its
`ESTABLISHMENT:` line at T10, T20, T23, T30 and T40, and the instrument's independent computation
**agrees with all five**. Five boundary checks, five agreements.

### The one thing the next stretch changes

**The target moves inside the window; nothing else changes.** A1's capture half was decided by the map
before the army existed - the only rival capital is 33 tiles away behind five city-states and had not
been met by T40 - so continuing this window would spend another forty turns on a question the map has
already answered. `docs/experiments/README.md` section 3 now re-scopes **A2** to exactly that: the same
save, the same doctrine, the same executor, and the objective is the nearest *city* (a city-state inside
a dozen tiles) instead of the nearest rival capital. The production question - is the establishment
affordable, and does siege really come first when its tech exists - becomes answerable there, and the
plan variations (Encampment timing, chops, buying, two war cities) queue behind it.

Two things stay open for whoever runs A2, and both are written in section 3 rather than left to be
rediscovered: a city-state is a legitimate target for this experiment and not for the standing directive,
which is what the task file's `overrides:` line is for; and the distance is measured with
`get_staging_plan` **before** the deadline is written.

## An arithmetic note before the T40 review: what P2's deadline actually asks for

Written at T10, from the game's own numbers and the attempt's own telemetry, because it changes what a
missed P2 would mean.

| item | base | on Quick (x0.67) | source |
|---|---|---|---|
| `TECH_ENGINEERING` (the Catapult's tech) | 200 | **134** | `Base/Assets/Gameplay/Data/Technologies.xml:96` |
| its eureka - *construct a building: Ancient Walls* | Boost 50 | **67** with the Walls | `Technologies.xml:472`; GS China boosts are 50% (the ruleset note above) |
| one Catapult | 120 | **80 production** | `prompts/tactics/01-unit-production.md` section Numbers |
| **the table's two siege units** | 240 | **160 production** | arithmetic |
| Game speed scales every cost | - | Quick x0.67 | `GameSpeeds.xml` (`GAMESPEED_QUICK`), tabulated at `docs/production-speed.md:79` |

The attempt's own numbers at T10: **science 4.0/turn, one city at pop 3, ~5-8 production**. The siege
half of the table alone therefore costs about **20-26 turns of that city's entire output**, and the rest
of the table (2 melee, 4 ranged, 1 ram, 1 cavalry) sits on top of it, while the Settlers that make the
expansion are built in the same queue.

**So P2 is not a test of whether the doctrine can be executed; it is a test of whether expansion can be
stopped.** Engineering lands around T20-T25 only if the Walls eureka is taken, and paying 160 production
for two Catapults by T60 means the empire stops settling and stops building infrastructure at about T25.
`docs/china-production-by-victory.md` section 1 and task 030 both say the opposite - expansion first, and
this attempt's business includes scouting, settling and infrastructure. **A1's hypothesis was
mis-specified**: the doctrine's establishment table describes what a *war* needs, and a window that also
demands expansion cannot pay for it by T60. The review should judge **H1's ordering** (is the assault
asked for before the merely nice, once an assault is planned) and **the cost**, and it should not read a
missed P2 as the doctrine fails. This note is here so that judgement is made with the arithmetic in
front of it rather than after the fact.

**Sharpened at T24 by the session's own account of itself.** It is *not* taking the Ancient Walls
eureka, and its own estimate is **Engineering at T40-45** (diary, T20 and T24 `hypothesis`), with ranged
4/4 about T33 at two turns per Slinger. Take that seriously and P2 stops being tight and becomes
**impossible**: Engineering ~T42, then two Catapults at 80 production each and ~6-8 production per turn
is a further 20-26 turns, so the siege half of the table lands around **T62-T70** - before the two melee,
four ranged, ram and cavalry that the table also asks for. The window's own telemetry corroborates the
cost side: the ten turns T10-T20 bought one Settler, one Builder, one city and two techs **and 0% of the
establishment** (the session's own words), with expansion compounding science 2.5 -> 5.5 by T24.

So the honest verdict for P2 is not "missed" but "**not askable of a sixty-turn window**" - and the
useful question the experiment can answer is what a *reachable* establishment window is (the session's
own arithmetic suggests siege from about T45 and the screens from T33, which is a T75-T90 establishment,
not a T60 one). That belongs in the next attempt's hypothesis, not in an apology for this one.

## The map makes the T80 deadline unreachable, and that is the experiment's error, not the doctrine's

Read out of the attempt's own map dump at T28 (`.civ6-mcp-data/mapstatic_china_911679432_*.json`, written
by the MCP's map capture), which lists every city that existed at the start:

| | tile | who |
|---|---|---|
| our capital | **(60,22)** 西安 | us |
| **the only rival capital on the map** | **(27,18)** Canberra | Australia (pid 1) |
| the second rival | *no city* | the Maori - Kupe starts at sea with a Settler and two Scouts, so there is no capital to find until he settles |
| between us and Canberra | (50,22) Jerusalem, (42,23) Chinguetti, (37,22) Zanzibar, (31,26) Samarkand, (35,8) Hunza | five city-states |

The map is 74x46. **The nearest major rival is 33 tiles west of us** - and on a hex grid where one step
changes the x coordinate by at most one, **|dx| = 33 is a lower bound on the true distance**, with 37 as
the upper bound if every one of the four rows of offset also had to be walked. The repository's own
`hexdist.py` measures it exactly but needs the tuner, and the playing session holds that connection, so a
bound is what is claimed here rather than a precise number. (Trying to run it is also a small proof of
the rule: it answers `could not connect to FireTuner` while a session plays.)

**Why this is decisive.** `docs/retrospectives/2026-09-28-city-captures-T228-T294.md` is the case record
of exactly this failure: task 021 targeted a city **30-40 tiles inland**, its window expired with the
artillery still 13-22 tiles out, and that retro's own correction was *"target selection: coastal and near
beats inland and far, and a siege deadline is a `get_staging_plan` timetable"*. A1 has re-created that
map with two opponents on a Small Pangaea: **the one target is 33+ tiles away, across five city-states'
territory** - and `AGENTS.md` states the rule this breaks: *"`expires:` must be reachable ... count the
turns from the queue, not from the calendar."* Task 030's T80 came from the calendar. I never measured
the distance to a rival before writing it, and at that moment no rival had even been met.

**So P3 does not need a battle to be decided.** A capture by T80 requires the army to walk 33+ tiles
(ten turns of movement even at three tiles a turn, over terrain that is mv2-mv3 all round the capital),
find a city that lies west of five city-states, break it and hold it - inside eighty turns that must also
pay for the expansion the same task demands. The attempt said this itself at T24, before any of my
arithmetic: *"if the Scout finds only mountains and coast for another ten turns, the attempt's map is a
peninsula and the capture half of A1 becomes impossible for reasons that have nothing to do with the
production doctrine - which the record must state plainly rather than blame on the army."*

**What the next attempt changes, and it is a scenario fix rather than a strategy fix:** measure the
distance to the nearest rival **before** the deadline is written - the map dump and `get_map_area` both
give it, and the ruler is `get_staging_plan` - and then either set the deadline from that number or start
from a position whose nearest rival is inside the window. A window whose capture half is arithmetically
impossible cannot answer a question about production.

## What this attempt already found (2026-09-29, before its first played turn)

- **SETTLED at T32, and the rule is measuring the map: a correction to `issue-the-calls-furthest-first`.**
  The session argued at T24 that its 3 stops were terrain (hills, jungle and forest at mv2-mv3 all round
  the capital) rather than a column queueing behind itself, which is the jam the rule was written for.
  The log decides it, because every refusal carries its reason: over T1-T32 there were **37
  `STOPPED_MID_PATH`, and all 37 read `(moves exhausted)`** - not one names another unit in the way. The
  rest of the refusals are the map as well: 6 `water tile - land units need Shipbuilding tech to embark`,
  4 `impassable mountain`, and only 2 of the ambiguous `tile appears passable - path may be blocked by
  intermediate tiles`. The rate is 37/32 = **1.2 stops a turn**, against 2.6 measured in the previous
  match's T272-T287 window and 3.2 over T228-T299 - on rougher ground, with **fewer** stops, which is
  what terrain-caused stopping looks like (each order stops once, then arrives next turn) rather than
  what queueing looks like (units piling up behind each other).
  **And the rule is the only one that fired**: `CHECK FAILED [issue-the-calls-furthest-first]`, 3 times,
  is the attempt's entire red list. So the one rule that fires is the one whose diagnosis does not fit
  the evidence, while the check's own count cannot tell a map-caused stop from a plan-caused one.
  **The fix belongs after this attempt ends, not during it** - editing `turn-checks.md` now would stop
  the rule firing mid-window and erase the tail of this measurement. The shape of the fix: the metric
  behind the rule has to carry *why* the order stopped (the tool already prints the reason), so that a
  stop caused by mv2-mv3 terrain is exempt and a stop caused by the column's own order is not.
  The upstream retro (`docs/retrospectives/2026-09-28-city-captures-T228-T294.md`) listed this as "the
  stop count is told, not enforced"; the sharper statement is that it was **told by the wrong signal**.

- **The instrument's H6 does not measure the claim it is testing.** `military_city_spread` counts
  *distinct cities asked for a military unit*, and at T30 it reports "2 distinct cities ... (city 65536:
  7, city 131073: 1)". The doctrine's claim (`tactics/08`) is **one war city** - concentration of
  production - not the absence of any military order in a second city, so on these numbers the measure
  reads as a violation when the attempt has built a single unit in its second city. The honest measure is
  the share of military production in the busiest city, or the cities where military orders outnumber
  civilian ones. **Fixed after the attempt, not during it** - the report is the attempt's record.
- **`--run` earns its place.** `--run vigilant-sable-longbow-78` excludes the earlier probe session's
  three read-only rows (`log_china_911679432_eternal-scarlet-catapult-86.jsonl`, from the tool-wrapper
  test), so the doctrine checks count only the attempt's own calls.

- **A turn was taken and reverted, and it found a rules bypass.** To prove the `end_turn` path before
  anyone depends on it, `scripts/auto-turns.py --turns 1` played T1. `end_turn` worked (`Turn 1 -> 2`,
  score 10, the diary row written and labelled `agent_client=script`) - but the same turn founded
  **节庆女神 with `faith_balance 0`**, leaving the empire at **-16 faith**: `choose_pantheon` checked
  only whether a pantheon already existed, and not whether it could be paid for, so the operation went
  through and granted a belief nobody bought. That is a real bypass of a game rule and, worse for this
  experiment, a free benefit A1 would have and later attempts from the same save would not - so the
  turn was reverted (`ATTEMPT-A1-T1-settled` reloaded: turn 1, faith 0, no pantheon, 西安 present) and
  its diary rows were deleted rather than left to be read as part of the attempt. The query now refuses
  below the game's own `RELIGION_PANTHEON_MIN_FAITH` (`GlobalParameters.xml:475`), pinned by
  `tests/test_pantheon_faith_guard.py`.
- **The verdict learned to say "not yet".** Reported against a one-turn attempt, the instrument printed
  `FALSIFIED P2 establishment complete by T60`, which is not a judgement about a hypothesis but a window
  that has not closed. Predictions now carry three states - a met achievement is `HELD`, an unmet one is
  `OPEN` until its deadline and `FALSIFIED` after it, and a *bound* (the gold-floor count) is `HELD`
  only when its window closes. A T1 attempt now reads four `OPEN`s and says so.
- **Founding the capital found a second defect in the same block the syntax error came from.** With 西安
  founded, `get_cities` finally had a real city row to parse - and the row's **power advice arrived full
  of literal `[NEWLINE]` markup**: `"进行发电：[NEWLINE][NEWLINE]在此城或附近城市中建造1座发电厂…"`. The
  query's cleanup replaced *real* control characters, which `GetPowerAdvice()` never returns, so the
  step that looked right did nothing at all. Both the markup and any real breaks are collapsed now, and
  the row reads as one line. **The lesson is about where defects hide**: the syntax error announced
  itself on the first call, and this one could not be seen until a city existed to ask about - the same
  block, found a day apart, by doing the two different things.
- **The city-side surface is clean at T1 once the capital exists**: `get_cities` parses the full row
  (including `power_required` / `power_free` / `power_advice`), and `list_city_production`,
  `get_builder_tasks`, `get_purchasable_tiles`, `get_wonder_advisor`, `get_district_advisor` (which
  answers `CANNOT_PRODUCE` at pop 1, correctly) and `get_units` all answer. A read sweep of all 25
  no-argument queries passed 25/25 in the no-city state before that, so the first turn's whole read
  surface has now been walked.
- **RESOLVED, and the directive was wrong: the boost is 50%, not 60%.** At game start the leader
  screen read: 朝代更替 - "尤里卡和鼓舞提供 **50%** 的科技与市政，而非 **40%**", while
  `prompts/strategies/china-conquest/directive.md` said 60%. The ability's description is **replaced
  per ruleset**, which the earlier audit missed:
  `DLC\Expansion2\Data\Expansion2_Civilizations.xml:73` swaps in
  `LOC_TRAIT_CIVILIZATION_DYNASTIC_CYCLE_EXPANSION2_DESCRIPTION`, and that row
  (`DLC\Expansion2\Text\en_US\Expansion2_ConfigText.xml:543`) reads **"50% of civics and technologies
  instead of 40%"**. The 60% comes from the *base game's* text
  (`Base\Assets\Text\en_US\Civilizations_Text.xml:296`), which does not apply under Gathering Storm -
  the ruleset this match plays. Fixed in the directive (both languages), in `prompts/workers/strategy.md`,
  in `docs/china-production-by-victory.md` and in `docs/strategy-verification.md`; the installed skill
  was re-synced so the session reads the corrected number.
  **What survives**: the delta is +10 points under either ruleset, so "a Chinese boost is worth more
  than anyone else's, never skip one" stands; **what does not** is any arithmetic built on 60%, which
  overstates every boost by ten points of the item's cost. This is the first finding of the experiment,
  and it came from the game's own interface disagreeing with a document - which is the kind of thing
  the attempt's diary is supposed to catch.
