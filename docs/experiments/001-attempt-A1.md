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
| Turn 1 save | `evals/saves/ATTEMPT-A1-T1.Civ6Save` | saved from the live game at 4000 BC, no actions taken - **and this is the experiment's shared starting position: every later attempt loads this same save**, so the map, the opponents and the start do not move under the variable (`docs/experiments/README.md` section 2) |

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

## Mid-window review (end of T40) - written when the session stops there

Task 030 orders the session to stop at the end of **turn 40** and report, and this is where that
review goes. It is written from the instrument, not from the diary's own summary:

```
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --verdict
.venv\Scripts\python.exe scripts/experiment-report.py --game china_911679432 --from 1 --to 40 --step 10
```

| question | answer |
|---|---|
| establishment turn so far (P2 wants <= T60) | not yet measured |
| the army's start - the first order of any role-mapped unit | not yet measured |
| the siege train's first order (P1 wants <= T45) | not yet measured |
| the economy at T20 / T40, against the plan | not yet measured |
| `carrying-capacity` red turns so far (P4 allows < 10) | not yet measured |
| the nearest rival city and its distance in tiles | not yet measured |
| verdict so far on P1-P4 | not yet measured |

Then one paragraph, and only one: what the window actually bought, and **the single thing** the next
stretch changes. A mid-window review that lists five intentions changes nothing.

## What this attempt already found (2026-09-29, before turn 1)

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
