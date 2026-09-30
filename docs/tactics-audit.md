---
title: Can the tactics files actually be executed? - an audit of prompts/tactics/
---

The question (human, 2026-09-30): 「prompts/tactics/ 里的策略是否都能落地被执行？」 - can every
strategy in `prompts/tactics/` actually be landed and executed?

**The answer is no, not all of them, and the failures cluster into four classes.** Every file's core
is executable - the tools it names exist, the blocks it quotes are printed, the rules it cites are
live - but each file also carries at least one load-bearing claim that cannot be carried out as
written, and two of them (`04`, `07`) are only about half executable. Separately, and more seriously
than any single file: **the delivery mechanism itself almost never runs**, so the doctrine usually
does not reach the agent at all.

*Status when written (2026-09-30, game T288+): `prompts/tasks/tmp/` is empty - task 028, the
development window that carried the power section, expired at T288 and is in `done/`. That leaves the
directive, `prompts/tactics/` and `prompts/checks/turn-checks.md` as the only carriers of doctrine in a
running session, which is why this audit matters more, not less.*

## How this was checked

Four independent audits, one per pair of files, each cross-checking every actionable claim against
ground truth rather than against prose:

- `src/civ_mcp/server.py` - the MCP tool surface: a tool a file names that is not there is
  un-executable, and a proposal citing it is rejected by the orchestrator's own unknown-tool check;
- `src/civ_mcp/end_turn.py` + `docs/turn-result-blocks.md` - whether the block, line or metric a file
  tells the agent to read is really produced, and under which condition;
- `prompts/checks/turn-checks.md` (live) vs `prompts/checks/pending/` (staged, unenforced);
- `prompts/workers/military-map.md` / `economy-cities.md` - the trigger table that decides whether a
  file reaches an advisor at all;
- `prompts/strategies/china-conquest/directive.md` - the standing strategy the same agent follows,
  which several files contradict.

Two instruments were written for the delivery half, both read-only and in `.tools/`:
`tactics-in-briefs.mjs` (does a file's text ever appear in a `civ_advisor` call?) and
`tactics-warnings.mjs` (what do the advisors say about it?). Every finding below cites the code or
the transcript that proves it.

## The systemic finding: the doctrine rarely reaches the advisor

The eight files are not tools and no rule reads them. The orchestrator has to pick the matching file
and **paste its text** into the `civ_advisor` call; the worker prompt says so explicitly
(`military-map.md:15-18`, "the orchestrator passes the relevant tactic text"), and tells the worker to
complain when it is missing (`military-map.md:17-18`).

Measured over all 158 session transcripts (`.tools/tactics-in-briefs.mjs`, using each file's **title
line** as the needle, because the path alone appears in the reference table inside `AGENTS.md`):

| | |
|---|---|
| transcripts | 158 |
| sessions that called an advisor at all | **98** (`civ_advisor` lines: 4535) |
| sessions in which a tactics file's own text appears | **18 total, 1-7 per file** |
| sessions in which a tactics file appears **on a `civ_advisor` line** | **1** (`tactics/04`) |
| proposal lines whose `warnings` name a tactics file | **339** |
| proposal lines whose `assessment` names a tactics file | 90 |

The 339 warnings are the workers doing what the role prompt asks: naming the file the brief should
have carried. So the advisor layer *is* being called (98 sessions, 255 calls - and
`docs/agent-efficiency.md` §4.4 already flagged that most of the cost is paid for little benefit),
but the doctrine text stays behind. Three concrete reasons:

1. **Nothing automates the paste.** There is no `get_tactics`/`read_tactic` tool in the 79-tool MCP
   surface, so delivery depends on the parent agent's memory every turn.
2. **The two most important files are the two largest**: `04-staging-out-of-range.md` is **34.8 KB /
   458 lines** and `07-pre-war-analysis.md` **30.4 KB / 437 lines** - about 9-10k tokens each to paste,
   against files of 5-7 KB for the rest. The README's "consult one or two at a time" is a real cost.
3. **No test covers the delivery or the consistency.** `tests/test_advisor_brief.py` checks a
   rehearsal fixture, `test_advisor_proposal.py:72` checks that an assessment *starts with*
   `prompts/tactics/`, and `test_agents_references.py` checks that `AGENTS.md`'s table points at files
   that exist - nothing checks that a file's numbers agree with the rule file they must satisfy.

## Per-file verdict

| file | verdict | the claim that decides it |
|---|---|---|
| `01-unit-production.md` | PARTLY (rising) | the siege row is the band (1-3), not the old 2; **the anti-cavalry chain now matches the rule** (2026-09-30: `PIKE_AND_SHOT`, `MODERN_AT` added to `counter-the-cavalry` and to `end_turn._MELEE_TYPES`); the Catapult's city figure is the game's Bombard 35, not 45; no Corps/Army verb |
| `02-contact-on-discovery.md` | PARTLY (rising) | its peacetime-barbarian trigger has no class or unit-relative distance (both live only in `BATTLE ASSESSMENT`, which is war/damage-gated); no read-only estimate verb; **which contacts `mass-on-contact` reaches is now stated in the file** (2026-09-30) |
| `03-under-attack.md` | MOSTLY (rising) | no rule forbids the withdrawal it recommends (`answer-the-attack` and `mass-on-contact` both accept a stated one); **step 1 now points at the `== Events ==` line for our own damage** (2026-09-30) and says the attacker is an inference from `BATTLE ASSESSMENT`, and the withdrawal case carries the `UNUSED ATTACK` bounce with `skip_remaining_units(force=True)`; what remains is that "an enemy attacked a city" has no event and no metric, so it is a `get_cities` diff |
| `04-staging-out-of-range.md` | ~HALF (rising) | the RALLY leg it leans on is now **live** (the query emits a d3 assembly ring, 2026-09-30); **step 6.2 now has an oracle** - the plan answers `FIRE` / `FIRE?` / `NO LINE OF SIGHT` per shooter tile, from the map and from the engine; what remains is the movement-point path cost, any ZOC input, and a pillage rung with no verb |
| `05-formation-and-screening.md` | MOSTLY (rising) | **`WOUNDED IN REACH` is now named as the CLI script's block, with the MCP-loop test given** (2026-09-30); "never adjacent to a *city*" is unenforced; the screen's identity is not reported |
| `06-assault-composition-and-fire.md` | PARTLY (rising) | the composition table is **fixed** (siege is a band, the ram/tower row is gone, anti-cavalry added, capture classes corrected, and the city figures are the game's `Bombard` strengths) and row 0's pre-move ring-LOS question now has an oracle - the staging plan's per-tile `FIRE` / `NO LINE OF SIGHT` verdict (2026-09-30); what remains is the command-level "which of these guns has already fired" |
| `07-pre-war-analysis.md` | PARTLY (camp branch weaker) | Step 0's dead tool name is **fixed** (2026-09-30: `get_trade_options`); **Gate 2 (ring LOS) is now answerable before the declaration** from the staging plan's map rule plus the engine's `CANFIRE` (2026-09-30); the Siege Tower advice and the C3 claim are **fixed** (2026-09-30); `WOUNDED IN REACH` is no longer promised from the MCP loop |
| `08-war-and-the-home-front.md` | MOSTLY | every block and rule it cites is live (`10-TURN REVIEW`, `WAR ECONOMY`, `builder-backlog`, `carrying-capacity`); the new power section is code-complete but its rule is **staged** and a server started before commit `8353672` prints no power at all, leaving a human-only fallback; the stale military figure (306 -> 282) and the retired task path are **fixed** (2026-09-30) |

## Resolved by human instruction, 2026-09-30

Four rulings answered the contradictions this audit found, and all four are now in the files the
agent actually reads (the directive preset **and** the live `SKILL.md` DIRECTIVE block, the live rule
file, the tactics files, the worker prompt, `end_turn`'s establishment table and the staging plan's
printed cap). The Chinese backups mirror each one.

1. **The siege count is a band, not a quota**: 1-3 Catapults by the arithmetic - two or three by the
   situation, never hard-coded, and **one is enough** when the ground and the ranged line already
   cover the wall pool. Written into `tactics/01` (the row and the arithmetic), `tactics/06`'s
   composition table, `tactics/04`'s assault list and report template, `directive.md` (twice),
   `turn-checks.md`'s assault-train preamble, and `end_turn._WAR_TRAIN`, which now carries a **floor
   of one** and a target of three so that one gun is never reported as a deficiency.
2. **No ram and no tower, built or fielded** - including one the empire already owns, which the
   directive previously kept as an exception. Removed from `directive.md`, `tactics/01` (the row now
   reads "never"), `tactics/04` (three places), `tactics/05` (the advance order), `tactics/06`
   (the row and the order of work), `tactics/07` (gate 4 and the prohibitions), `tactics/README.md`
   and the worker prompt.
3. **A raid counts as a war.** `mass-on-contact` and `answer-the-attack` now fire on
   `at_war` **or** `camps_within_3` - no new metric, so the change is live the turn the file is read -
   and the directive's camp paragraph, `tactics/07`'s C3 claim and the worker prompt all say the same.
   The occupancy rules (`one-garrison-per-city`, the upgrade rules) stay wartime-only, because a raid
   is a fight and not an occupation; a barbarian with no camp within three tiles still sets neither.
4. **Barbarian camps are cleared.** The worker prompt's "Do not clear barbarian camps" bullet - the
   last place still carrying the retired rule - now carries the camp doctrine: the six gates, ranged
   plus a melee walk-in, the convertible reported before the raid and not instead of it.

What the rulings did **not** touch, and what therefore remains open from this audit: the tooling gaps
(`pillage` has no verb; `WOUNDED IN REACH` CLI-only; no
movement-point path cost or ZOC input; the camp-prohibition was the only one of the four that was pure
prose), and the delivery finding. Four of those gaps have since been closed - the rally leg, the
line-of-sight oracle, `SIEGE POSTURE`'s availability (all 2026-09-30, see the ranked fixes) and `07`'s
dead Step-0 tool name.

## The four failure classes, with the evidence

### A. The file contradicts the directive or a live rule (self-defeating doctrine)

| finding | evidence |
|---|---|
| Siege establishment was **2** in `01:17` and `06:9` while the directive said 3 and the live rule required `>= 3` (`turn-checks.md:224`). **Resolved 2026-09-30**: the row is now a band of 1-3 by the arithmetic, the rule's floor is 1, and `end_turn._WAR_TRAIN` carries floor 1 / target 3. | kept an obedient session's `siege-train` red; now it cannot |
| `07:234,288,345` answered gate 4 with "Battering Ram -> Siege Tower", and `06:11` kept a ram/tower row, against the directive's "we build neither". **Resolved 2026-09-30**: no ram and no tower, built or fielded, in every file that mentioned them. | a 07-based proposal used to order a forbidden unit |
| `07:114` said `mass-on-contact` enforces camp concentration "exactly as a war"; the rule was gated `metric(at_war) >= 1` (`turn-checks.md:142`) and a raid sets no war, so **nothing** enforced the two-attacker rule for camps. **Resolved 2026-09-30**: the rule now fires on `at_war` **or** `camps_within_3`. | measured rule text |
| `06:10` "melee are the only units that can take the city" - contradicted by `06:104-107` and by `take-the-city` ("melee, anti-cavalry and **cavalry**", `turn-checks.md:190`). | the file contradicts itself |
| `01:19` ends the anti-cavalry chain at Pike and Shot, but `counter-the-cavalry` counts only `SPEARMAN, PIKEMAN, AT_CREW` (`turn-checks.md:86`) - `UNIT_PIKE_AND_SHOT` is a suffix mismatch and counts 0. | the rule cannot be satisfied by the unit the file recommends |
| `military-map.md:104-108` ordered "**Do not clear barbarian camps near our territory**", while the directive made a camp a target and `answer-the-camp` was live (`turn-checks.md:353`). **Resolved 2026-09-30**: the bullet is now the camp doctrine, with the raid-as-war line. | the advisor's role file contradicted the file it was briefed with |
| `03:36-37` "an enemy inside a city must not be left alive" - the directive's garrison rule says the opposite: a garrisoned unit **takes no damage** while the city is attacked and is removed only by taking the city (`directive.md:193-201`, `manual.clean.txt:1065`). | the file orders fire at a target that cannot be hurt |

### B. A tool that does not exist, or cannot run

| finding | evidence |
|---|---|
| **`pillage` has no verb.** The directive orders it (`directive.md:545`, "pillaging that Holy Site ... is worth more than any number of individual kills") and the staging ladder offers it as a rung ("pillage (cavalry ignores ZOC)"), but `unit_action`'s action list has no `pillage` (`server.py:1662`) and no pillage code exists in `src/` (only repair and read paths). The game exposes the action (pillage modifiers, `Expansion1_Buildings.xml:185-189`). | the one standing order the tool cannot carry out |
| `07:39,69,74` Step 0 calls **`get_deal_options(player_id)`** - not an MCP tool. The tool is `get_trade_options(other_player_id)` (`server.py:1333`); `get_deal_options` is the internal method name (`game_state.py:1230`). The orchestrator's Phase-3 validation rejects unknown tools, so a proposal citing it is discarded. | measured; and the reconnaissance door is dead. **Resolved 2026-09-30**: all three call sites say `get_trade_options`, and the "37 iron" claim is gone - the tool prints resource **types**, not amounts (`narrate.py:1099-1114`) |
| `07:97` answers camp gate C2 with `scripts/probe-tile.py`, and `04:213,235` with `scripts/staging-plan.py`: both open **their own FireTuner connection** (`probe-tile.py:38-40`, `staging-plan.py:6-8`) and cannot run while the MCP session holds the single one. The MCP-side path is `get_map_area` and the `kill_x/kill_y` / `next_city_x/next_city_y` parameters. | "one session at a time" |
| `05:83-88` and `07:276` tell the agent to read a **`WOUNDED IN REACH`** block, which exists only in `scripts/play-turn.py:679-684` (and its test) - never in `src/civ_mcp`. In the MCP loop the line is never printed. | the agent waits for a line that cannot appear |
| `01:92-99` explains when to form a Corps or Army; there is no verb for it (`unit_action` list; nothing in `src/` for `FORM_CORPS`/`FORM_ARMY`). Only `run_lua(context="ingame")` or the human UI. | the file admits it and gives a fallback |
| `02:80-84` "one estimate per matchup, then decide" - the only estimator runs **inside** `attack` (`game_state.py:475-497`), which commits the attack. There is no read-only estimate tool. | the file's own test cannot be run without paying for it |

### C. Data no query returns

| finding | evidence |
|---|---|
| **No line-of-sight oracle, and four files need one.** `04:352-355` (test LOS per tile), `05:36`, `06:64-71` (row 0: "which ring tiles can shoot, before the first move") and `07:191-214` (Gate 2, "the firing list, before the declaration"). The staging plan marks "`- FIRE from here`" on `distance == 2` alone (`staging.py:418`); `CAN ATTACK:` is a `get_units` line that never lists cities and skips siege units (`lua/units.py:86-87,95`); `SIEGE POSTURE` names no tiles. | the pre-assault question the doctrine is built around cannot be answered. **Resolved 2026-09-30**: the ring row now carries the game's own `SightThroughModifier` per tile plus the tiles between a distance-2 pair, `civ_mcp/los.py` applies the manual's rule (`manual:999`), and every shooter's row prints `FIRE` / `FIRE?` / `NO LINE OF SIGHT: <blocker>`; for a gun already on a ring tile the query asks the engine directly (`CANFIRE`, the same `CanStartOperation(RANGE_ATTACK)` the attack path uses) and that reading overrides the map's |
| **The RALLY leg is dead code.** `_rally_option` keeps only ring tiles with `distance >= 3` (`staging.py:369`), but the production ring is `d >= 1 and d <= 2` (`lua/units.py:2521`) and options exist only for ring tiles - so `ASSEMBLY FIRST` / `RALLY` (`staging.py:386-392,409-414`) can never print. The test that pins it builds a synthetic `distance=3` ring tile (`tests/test_staging_plan.py:457,466-471`), so **a green test covers an unreachable feature**, while `04:53-54` forbids the hand computation that is the only alternative. | `04` step 1 cannot be executed as written. **Resolved 2026-09-30**: the query emits a real `RALLYRING` at d3 (six tiles nearest the army centroid) with its own `RALLYOPTION` paths, and the tests assert the query text rather than a synthetic ring |
| **`SIEGE FIRE` / `SIEGE POSTURE` are suppressed in exactly the state `04` is triggered for**: the block returns `None` when nothing is exposed and the closest city is `> 3` tiles away (`end_turn.py:1275`), and `SIEGE FIRE: n/m` prints only with **two or more** siege units (`end_turn.py:1291`) - one gun gets no line, which is the classic failure. `04:363-373` tells the agent to read it at the rally. | the reading does not exist where it is needed. **Resolved 2026-09-30**: it prints from five tiles in with an `assembling` header, and prints the gun count for a single gun (`1/1` is the sanctioned single-gun assault) |
| **No movement-point path cost.** `04:46-54,446` computes "turns to assemble" from movement points; `PathingEstimate` returns turns/total_tiles/reachable_this_turn only (`lua/models.py:607-614`), and `turns` is a tiles-per-turn extrapolation from turn 1 (`lua/units.py:2466-2473`). The plan also caps placement at `turns_ahead=2` (`server.py:842`), so the slow unit - "usually the longer pole" - is reported unplaced. | the assembly timetable is an estimate of an estimate |
| **ZOC is invisible** (`04:172-175`, `02:17`): neither `get_pathing_estimate` nor `get_staging_plan` models it; the adapter only refuses at attack time (`lua/units.py:539-542`). | a whole-turn stop never appears in a plan |
| Peacetime contact is unreadable (`02`'s trigger): `get_units`/`THREAT:` print a distance measured to our **cities or units** (`lua/units.py:1034-1038`), and `promotion_class` plus the unit-only distance appear only in `BATTLE ASSESSMENT`, which is suppressed outside war/damage (`end_turn.py:2164-2168`). | `02` can be triggered without the data it is written on |
| The siege metrics measure against the nearest visible city of **any** major civ, at war or not (`lua/units.py:1390`), so `SIEGE FIRE` and `concentrate-the-siege` can be computed on a neutral city nearer than the target; the screen's identity is never reported (`05:90-95`). | wrong geometry, and no way to name the screen |
| Camp gates C1/C2/C5 are partly unanswerable: `get_map_area` gives a barbarian's type label but no CS/HP (`lua/map.py:211-219`); "what the camp has been spawning" and its gold/era reward have no query; the `BOOSTED` flag never appears as the literal `boosted=True` that `07:130` quotes. | three of the six camp gates are inference |
| **`03` points step 1 at the wrong block, and its third trigger has no data at all.** `03:9-10` sends the agent to `BATTLE ASSESSMENT` for "who did it", but that block lists **enemies only** (`end_turn.py:2179-2254`); our own damage is in the `== Events ==` line "`>> Your X (TYPE) took N damage! HP: h/max at (x,y)`" (`game_state.py:1886-1893`, rendered `end_turn.py:3754`). And "an enemy attacked a city" (`03:3-4`) has **no event and no metric** - `damaged_this_turn` counts units (`end_turn.py:2016`) - so it is only visible by diffing `get_cities` wall/garrison HP. | one of the file's three triggers is not observable |
| **The file omits the gate that actually stops the turn.** An unused legal attack makes `end_turn` bounce with `UNUSED ATTACK at end_turn ... call skip_remaining_units(force=True)` (`end_turn.py:759-765`) and `skip_remaining_units` refuses without `force` (`server.py:1763`). `03:54-57` recommends withdrawing a hurt unit without mentioning that the withdrawal is blocked until that call. | the recommended move cannot be taken as described |
| **The power read is deployment-gated.** Everything the section needs landed in commit `8353672`, so on a server started earlier the Lua emits the old field count, `power_reported` is false and `get_cities` prints **no** power text; the section's fallback ("the reading is the city banner") is the human's UI - no tool returns it. The rule is also still **staged**, so nothing fails on power until it is promoted. | executable on a fresh server, not on the one now playing |

### D. Minor and cosmetic (fixed 2026-09-30, with two notes)

The batch, and what the fix was: `06:32`'s `garrison:` label is `Gar:` (and the pool is
`Garrison h/max`) - `narrate.py:370-376`; `06:114`'s `producing: NONE` is `Building: nothing`
(`narrate.py:349-354`); `06:232`'s `NO_WALLS` quote now carries the code's em dash
(`lua/cities.py:490`); `06:190`'s general aura cites **both** manual statements - the summary puts it
at "within one tile of their location" (`manual.clean.txt:1095`) and the detailed paragraph at
"within 2 tiles of the General" (`:1097`) - and points at the game's own ability text, which is the
`Passive aura (granted while this unit lives)` line `get_great_people` prints; `08:34`'s
"military 262 -> 306" is 262 -> 282, its own table's figure; `08:70-71` cites the retired
`prompts/tasks/tmp/done/023-dutch-siege-corps-done-T259.md`.

**The siege-damage figure was wrong in the opposite direction from this audit's own claim.** The
audit said `01:75` and `directive.md:160` put the *Trebuchet* at 45 where the rule says 55. The
game's data says `UNIT_CATAPULT` Bombard **35**, `UNIT_TREBUCHET` **45**, `UNIT_BOMBARD` **55**,
`UNIT_ARTILLERY` **80** (`Base/Assets/Gameplay/Data/Units.xml`) - so the Trebuchet's 45 was right and
the **Catapult's** 45 (`directive.md:165`, `01:31,90`, `06:9`) was the error, as was the pair in
`turn-checks.md` and `end_turn.py` ("a Catapult does 45 against a city where a Trebuchet does 55").
All of them now carry the game's `Bombard` strengths and say separately that a *shot* lands about
45-52 against a 200-HP city with a CS 35-40 defence, which is where the two numbers were being
confused.

Still open, and deliberately: `enemy_cities_seen` is computed and consumed by nothing
(`end_turn.py:47,1340`) - harmless as a metric a future rule can use, and deleting it would churn
the metric tuple for no gain.

**Two corrections found by the same audit, one of them mine.** The audit's own cross-check caught a
factual error I had written into `tactics/08` and the pending power rule: the Merchant governor's
`RENEWABLE_ENERGY` is **not** "one governor promotion" - it sits behind Tax Collector, which sits behind
Harbourmaster or Foreign Exchange (`Expansion1_Governors.xml:223-228`). Both files now say so. And the
audit's claim that the 1 Coal -> 4 Power rate is "in no XML" is wrong: the rates are in the game's
**text** files, not its gameplay data - `LOC_BUILDING_COAL_POWER_PLANT_DESCRIPTION` ("1 Coal -> 4
Power"), the nuclear plant's `LOC_BUILDING_POWER_PLANT_EXPANSION2_DESCRIPTION` (16), and
`LOC_PEDIA_CONCEPTS_PAGE_POWER_CHAPTER_CONTENT_PARA_4` ("Coal and Oil Power Plants provide 4 Power per
resource, while Nuclear provides 16"). The table in `tactics/08` is right; its citation should name
`Expansion2_Buildings_Text.xml` and `Expansion2_Civilopedia_Text.xml`.

## What is *not* broken

Worth saying plainly, because the list above reads worse than the reality: the armoury the files
describe exists and works. `get_staging_plan` (including the camp variant and `WALK-IN OPENS`),
`get_pathing_estimate`, `get_map_area`, `get_units`, `city_action`, `get_trade_options`, the
`TAKE THE CITY` block with its tile and capture unit, `SIEGE PROGRESS` with `supply line n/6 cut` and
`SIEGE STALLED`, `city hp: N/200`, the furthest-first ordering and its `issue-the-calls-furthest-first`
rule, `STACKING_CONFLICT`, the supply-hex metric and the `cut-the-supply` rule, the healing and
wall-repair manual passages, `hold-what-you-take`, `take-the-city`, `counter-the-cavalry`,
`finish-the-wounded`, `one-garrison-per-city`, the `10-TURN REVIEW` and its `WAR ECONOMY` line - every
one of those was verified present and live. The gaps are specific, not general.

## Ranked fixes

**One-liners in the documents (no code):**

1. `01:17` and `06:9`: Siege **2 -> 3**, and `04:448`'s `siege n/2 -> n/3`, matching
   `directive.md:223`, `turn-checks.md:224` and `staging.py:45`. **Superseded 2026-09-30** by the
   human's ruling: siege is a band (1-3 by the arithmetic), not a quota - the files now say so.
2. `07:39,69,74`: `get_deal_options` -> **`get_trade_options`**, and drop the "37 iron" claim
   (`narrate.py:1099-1114` prints types, not amounts). **Applied 2026-09-30**.
3. `07:234,288,345` and `06:11`: delete the Siege Tower as gate 4's answer; state the ram rule once -
   an owned ram stacks with the melee unit, nothing is bought.
4. `05:83-88` and `07:276`: stop promising `WOUNDED IN REACH` from the MCP loop (or print it).
   **Applied 2026-09-30**: both files now say the block is the CLI script's, and give the MCP-loop
   test (`get_units`: our HP against that unit's threat list, 60 HP or less within two tiles).
5. `07:114` and `02:43`: `mass-on-contact` does not reach a raid or peacetime contact - either say so
   or scope the rule. **Applied 2026-09-30**: the rule fires on `at_war` **or** `camps_within_3`, and
   `02` says which contacts it reaches and which are this file's own decision.
6. `06:10` "melee, anti-cavalry and cavalry"; add the anti-cavalry row to `06`'s table; `01:19`'s
   Pike and Shot either joins `counter-the-cavalry`'s list or the chain ends at Pikeman.
   **Applied 2026-09-30**: the row is in `06`'s table, and the rule's list is now the game's whole
   anti-cavalry chain (`SPEARMAN, PIKEMAN, PIKE_AND_SHOT, AT_CREW, MODERN_AT`, the same set
   `scripts/experiment-report.py:145` reads) - a Pike and Shot used to read as *no* anti-cavalry
   unit and fail the rule every turn. `end_turn._MELEE_TYPES` carries the same two additions.
7. `military-map.md:104-108`: replace "do not clear barbarian camps" with the camp doctrine that
   `07`, the directive and `answer-the-camp` already carry.
8. `03:9-10` point step 1 at the `== Events ==` damage line; `03:54-57` add the `UNUSED ATTACK`
   bounce and `skip_remaining_units(force=True)`; `08:34` 306 -> 282; `08:70-71` repoint to
   `done/023-dutch-siege-corps-done-T259.md`; the minor batch from class D. **Applied 2026-09-30**,
   with one correction to this audit's own claim about the siege numbers (see class D).
9. **Already applied in this pass**: the `RENEWABLE_ENERGY` cost correction in `tactics/08` and in
   `prompts/checks/pending/power-the-cities.md` (see class D below).

**Code (each one new behaviour, so each needs tests):**

10. **`pillage`**: add the verb to `unit_action` (`server.py` + a `GameState` method + Lua
    `UNITOPERATION_PILLAGE`), or delete the directive's line and the ladder rung. The directive orders
    it today and nothing can do it.
11. **A rally ring**: extend the staging Lua with a `d >= 3` ring (or a rally query) so
    `_rally_option` can fire, and let the tool answer `04`'s step 1. **Applied 2026-09-30**
    (`RALLYRING`/`RALLYOPTION`, commit `99765a9`).
12. **A line-of-sight/fire flag per ring tile**: the single highest-value addition - it unblocks
    `04` step 6.2, `05`, `06` row 0 and `07` Gate 2 at once. **Applied 2026-09-30**: `civ_mcp/los.py`
    (the manual's rule on the game's `SightThroughModifier`), the sight facts on every ring row, and
    the engine's own `CANFIRE` answer for a gun already in position, which overrides the map.
13. **`SIEGE POSTURE` availability**: do not return `None` at staging distance, and print the gun
    count even for one siege unit, so `04`'s reading exists in `04`'s state. **Applied 2026-09-30**
    (commit `99765a9`).
14. **A read-only combat estimate tool** (expose `build_combat_estimate_query`), so `02:80-84` can be
    obeyed without committing the attack.
15. **Corps/Army**, or drop the paragraph.
16. **Delivery**: a `get_tactics(name)` MCP tool (or advisor-side injection) so the file text stops
    depending on the parent's memory - measured today at 1 session in 158.
17. **A consistency test**: read `turn-checks.md`'s unit lists and counts and assert that
    `01`/`06`'s establishment table agrees with them. That is the durable fix - it is the class of
    drift that produced the siege-2 finding and the Pike-and-Shot mismatch, and nothing catches it
    today.

**From the pre-war workflow review (2026-09-30), not from this audit's four classes:**

18. **One pre-war reconnaissance call (C3).** The eight-point review of what `07` actually does found
    that its first three gates were assembled from three or four separate reads per target, and that
    three of the numbers it needs (walls, the city centre pool, the garrison unit) appear in no
    metric at all. **Applied 2026-09-30**: `get_target_report(target_x, target_y)` returns the tile,
    the city on it, the visible enemies within three tiles of the **target**, and the staging plan -
    in two queries, before a declaration, and saying which of `visible` / `revealed` / `fog` the tile
    is. `07` Step 1 and Gate 1 point at it, `AGENTS.md` names it, and `tests/test_target_report.py`
    pins the parser, the narration, the query's read-only-ness and the composition.
19. **A reinforcement schedule (C4).** "Which turn does the missing role reach the rally" was two
    separate numbers - `get_city_production`'s turns-to-build and `get_pathing_estimate`'s
    turns-to-march - and nothing joined them. **Applied 2026-09-30**:
    `get_reinforcements(target_x, target_y)` reads our queues (military units only, via
    `bq:GetCurrentProductionTypeHash()` and `GetTurnsLeft()`), picks the assembly tile nearest each
    building city, and prints `ready T+n`, the march, the arrival turn, and any role covered by
    neither the plan nor a queue. The march leg is a **hex-distance estimate** and says so: the
    game's pathfinding needs a unit and the unit being built does not exist yet - the turn it
    appears, `get_staging_plan` answers that leg exactly. `07` Step 3 points at it and
    `tests/test_reinforcements.py` pins the parser, the arithmetic, the narration, the query and the
    composition.

## Method note and limits

The per-file audits were run by four subagents against the code, not against the prose; every claim
above carries the file and line that proves it, and the two headline findings I re-verified myself
(`pillage` has no verb, and the rally leg is unreachable because the test ring is synthetic). What
this audit does **not** cover: whether the *doctrine itself* is good strategy (that is the
directive's and the retrospectives' business), and any file outside `prompts/tactics/` - the same
class of check has not been run on `prompts/workers/*.md`, where one contradiction is already known
(the camp paragraph above).
