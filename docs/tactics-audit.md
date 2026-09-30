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
| `01-unit-production.md` | PARTLY | `01:17` Siege **2** vs live `siege-train` **>= 3** (`turn-checks.md:224`) and the directive's 3; Pike and Shot falls out of `counter-the-cavalry`'s unit list; no Corps/Army verb |
| `02-contact-on-discovery.md` | PARTLY | its peacetime-barbarian trigger has no class or unit-relative distance (both live only in `BATTLE ASSESSMENT`, which is war/damage-gated); no read-only estimate verb |
| `03-under-attack.md` | MOSTLY | no rule forbids the withdrawal it recommends (`answer-the-attack` and `mass-on-contact` both accept a stated one) - but it points step 1 at `BATTLE ASSESSMENT`, which lists **enemies only**; our damage is in the `== Events ==` line, "an enemy attacked a city" has no event or metric at all, and the file never mentions that an unused legal attack **bounces `end_turn`** until `skip_remaining_units(force=True)` |
| `04-staging-out-of-range.md` | ~HALF | the RALLY leg it leans on is **dead code**; `SIEGE FIRE` is suppressed in exactly its trigger state; no movement-point metric; no LOS or ZOC input; a pillage rung with no verb |
| `05-formation-and-screening.md` | MOSTLY | `WOUNDED IN REACH` (`05:83-88`) is printed **only by `scripts/play-turn.py`**, never by the MCP loop; "never adjacent to a *city*" is unenforced; the screen's identity is not reported |
| `06-assault-composition-and-fire.md` | PARTLY | composition table stale (`06:9` Siege 2; a ram/tower row the directive forbids; no anti-cavalry row; "only melee can take the city"); the pre-move ring-LOS step has no oracle |
| `07-pre-war-analysis.md` | PARTLY (camp branch weaker) | Step 0 calls **`get_deal_options`, which is not an MCP tool**; Gate 2 (ring LOS) is impossible pre-declaration; Siege Tower advice against the directive; C3 promises an enforcement that does not exist |
| `08-war-and-the-home-front.md` | MOSTLY | every block and rule it cites is live (`10-TURN REVIEW`, `WAR ECONOMY`, `builder-backlog`, `carrying-capacity`); the new power section is code-complete but its rule is **staged** and a server started before commit `8353672` prints no power at all, leaving a human-only fallback; a stale military figure (`08:34`, 306 vs its own table's 282) and a retired task path (`08:70-71`) |

## The four failure classes, with the evidence

### A. The file contradicts the directive or a live rule (self-defeating doctrine)

| finding | evidence |
|---|---|
| Siege establishment is **2** in `01:17` and `06:9`, while the human instruction and the directive say **3 Catapults per city** (`directive.md:223`) and the live rule requires `units(CATAPULT,TREBUCHET,BOMBARD,ARTILLERY) >= 3` (`turn-checks.md:224`). `06:66` even describes "a three-Catapult train". The staging tool itself is right: `staging.py:45` `_ESTABLISHMENT = {"siege": 3, ...}` and it prints "the assault establishment is **3 siege** ..." (`staging.py:445`). | an obedient session keeps `siege-train` red forever |
| `07:234,288,345` answer gate 4 with "Battering Ram -> Siege Tower", and `06:11` keeps a ram/tower row. The directive forbids both ("we build neither ... no tower is built", `directive.md:171-176`), and `turn-checks.md:217-219` agrees; gate 4's answer is the Catapult. | a 07-based proposal orders a forbidden unit |
| `07:114` says `mass-on-contact` enforces camp concentration "exactly as a war"; the rule is gated `metric(at_war) >= 1` (`turn-checks.md:142`) and a raid sets no war, so **nothing** enforces the two-attacker rule for camps. `02:43` makes the same claim for peacetime barbarian contact. | measured rule text |
| `06:10` "melee are the only units that can take the city" - contradicted by `06:104-107` and by `take-the-city` ("melee, anti-cavalry and **cavalry**", `turn-checks.md:190`). | the file contradicts itself |
| `01:19` ends the anti-cavalry chain at Pike and Shot, but `counter-the-cavalry` counts only `SPEARMAN, PIKEMAN, AT_CREW` (`turn-checks.md:86`) - `UNIT_PIKE_AND_SHOT` is a suffix mismatch and counts 0. | the rule cannot be satisfied by the unit the file recommends |
| `military-map.md:104-108` still orders "**Do not clear barbarian camps near our territory**", while the directive (human instruction 2026-09-26) makes a camp a target, `tactics/07` carries six camp gates, and `answer-the-camp` is live (`turn-checks.md:353`). The advisor's role file contradicts the very tactic file it is briefed with. | the worker is told the opposite of the file |
| `03:36-37` "an enemy inside a city must not be left alive" - the directive's garrison rule says the opposite: a garrisoned unit **takes no damage** while the city is attacked and is removed only by taking the city (`directive.md:193-201`, `manual.clean.txt:1065`). | the file orders fire at a target that cannot be hurt |

### B. A tool that does not exist, or cannot run

| finding | evidence |
|---|---|
| **`pillage` has no verb.** The directive orders it (`directive.md:545`, "pillaging that Holy Site ... is worth more than any number of individual kills") and the staging ladder offers it as a rung ("pillage (cavalry ignores ZOC)"), but `unit_action`'s action list has no `pillage` (`server.py:1662`) and no pillage code exists in `src/` (only repair and read paths). The game exposes the action (pillage modifiers, `Expansion1_Buildings.xml:185-189`). | the one standing order the tool cannot carry out |
| `07:39,69,74` Step 0 calls **`get_deal_options(player_id)`** - not an MCP tool. The tool is `get_trade_options(other_player_id)` (`server.py:1333`); `get_deal_options` is the internal method name (`game_state.py:1230`). The orchestrator's Phase-3 validation rejects unknown tools, so a proposal citing it is discarded. | measured; and the reconnaissance door is dead |
| `07:97` answers camp gate C2 with `scripts/probe-tile.py`, and `04:213,235` with `scripts/staging-plan.py`: both open **their own FireTuner connection** (`probe-tile.py:38-40`, `staging-plan.py:6-8`) and cannot run while the MCP session holds the single one. The MCP-side path is `get_map_area` and the `kill_x/kill_y` / `next_city_x/next_city_y` parameters. | "one session at a time" |
| `05:83-88` and `07:276` tell the agent to read a **`WOUNDED IN REACH`** block, which exists only in `scripts/play-turn.py:679-684` (and its test) - never in `src/civ_mcp`. In the MCP loop the line is never printed. | the agent waits for a line that cannot appear |
| `01:92-99` explains when to form a Corps or Army; there is no verb for it (`unit_action` list; nothing in `src/` for `FORM_CORPS`/`FORM_ARMY`). Only `run_lua(context="ingame")` or the human UI. | the file admits it and gives a fallback |
| `02:80-84` "one estimate per matchup, then decide" - the only estimator runs **inside** `attack` (`game_state.py:475-497`), which commits the attack. There is no read-only estimate tool. | the file's own test cannot be run without paying for it |

### C. Data no query returns

| finding | evidence |
|---|---|
| **No line-of-sight oracle, and four files need one.** `04:352-355` (test LOS per tile), `05:36`, `06:64-71` (row 0: "which ring tiles can shoot, before the first move") and `07:191-214` (Gate 2, "the firing list, before the declaration"). The staging plan marks "`- FIRE from here`" on `distance == 2` alone (`staging.py:418`); `CAN ATTACK:` is a `get_units` line that never lists cities and skips siege units (`lua/units.py:86-87,95`); `SIEGE POSTURE` names no tiles. | the pre-assault question the doctrine is built around cannot be answered |
| **The RALLY leg is dead code.** `_rally_option` keeps only ring tiles with `distance >= 3` (`staging.py:369`), but the production ring is `d >= 1 and d <= 2` (`lua/units.py:2521`) and options exist only for ring tiles - so `ASSEMBLY FIRST` / `RALLY` (`staging.py:386-392,409-414`) can never print. The test that pins it builds a synthetic `distance=3` ring tile (`tests/test_staging_plan.py:457,466-471`), so **a green test covers an unreachable feature**, while `04:53-54` forbids the hand computation that is the only alternative. | `04` step 1 cannot be executed as written |
| **`SIEGE FIRE` / `SIEGE POSTURE` are suppressed in exactly the state `04` is triggered for**: the block returns `None` when nothing is exposed and the closest city is `> 3` tiles away (`end_turn.py:1275`), and `SIEGE FIRE: n/m` prints only with **two or more** siege units (`end_turn.py:1291`) - one gun gets no line, which is the classic failure. `04:363-373` tells the agent to read it at the rally. | the reading does not exist where it is needed |
| **No movement-point path cost.** `04:46-54,446` computes "turns to assemble" from movement points; `PathingEstimate` returns turns/total_tiles/reachable_this_turn only (`lua/models.py:607-614`), and `turns` is a tiles-per-turn extrapolation from turn 1 (`lua/units.py:2466-2473`). The plan also caps placement at `turns_ahead=2` (`server.py:842`), so the slow unit - "usually the longer pole" - is reported unplaced. | the assembly timetable is an estimate of an estimate |
| **ZOC is invisible** (`04:172-175`, `02:17`): neither `get_pathing_estimate` nor `get_staging_plan` models it; the adapter only refuses at attack time (`lua/units.py:539-542`). | a whole-turn stop never appears in a plan |
| Peacetime contact is unreadable (`02`'s trigger): `get_units`/`THREAT:` print a distance measured to our **cities or units** (`lua/units.py:1034-1038`), and `promotion_class` plus the unit-only distance appear only in `BATTLE ASSESSMENT`, which is suppressed outside war/damage (`end_turn.py:2164-2168`). | `02` can be triggered without the data it is written on |
| The siege metrics measure against the nearest visible city of **any** major civ, at war or not (`lua/units.py:1390`), so `SIEGE FIRE` and `concentrate-the-siege` can be computed on a neutral city nearer than the target; the screen's identity is never reported (`05:90-95`). | wrong geometry, and no way to name the screen |
| Camp gates C1/C2/C5 are partly unanswerable: `get_map_area` gives a barbarian's type label but no CS/HP (`lua/map.py:211-219`); "what the camp has been spawning" and its gold/era reward have no query; the `BOOSTED` flag never appears as the literal `boosted=True` that `07:130` quotes. | three of the six camp gates are inference |
| **`03` points step 1 at the wrong block, and its third trigger has no data at all.** `03:9-10` sends the agent to `BATTLE ASSESSMENT` for "who did it", but that block lists **enemies only** (`end_turn.py:2179-2254`); our own damage is in the `== Events ==` line "`>> Your X (TYPE) took N damage! HP: h/max at (x,y)`" (`game_state.py:1886-1893`, rendered `end_turn.py:3754`). And "an enemy attacked a city" (`03:3-4`) has **no event and no metric** - `damaged_this_turn` counts units (`end_turn.py:2016`) - so it is only visible by diffing `get_cities` wall/garrison HP. | one of the file's three triggers is not observable |
| **The file omits the gate that actually stops the turn.** An unused legal attack makes `end_turn` bounce with `UNUSED ATTACK at end_turn ... call skip_remaining_units(force=True)` (`end_turn.py:759-765`) and `skip_remaining_units` refuses without `force` (`server.py:1763`). `03:54-57` recommends withdrawing a hurt unit without mentioning that the withdrawal is blocked until that call. | the recommended move cannot be taken as described |
| **The power read is deployment-gated.** Everything the section needs landed in commit `8353672`, so on a server started earlier the Lua emits the old field count, `power_reported` is false and `get_cities` prints **no** power text; the section's fallback ("the reading is the city banner") is the human's UI - no tool returns it. The rule is also still **staged**, so nothing fails on power until it is promoted. | executable on a fresh server, not on the one now playing |

### D. Minor and cosmetic (worth batching, not blocking)

`06:32` `garrison:` is really `Gar:` / `def N`; `06:114` `producing: NONE` is `Building: nothing`;
`06:230` quotes `NO_WALLS` with a hyphen where the code has an em dash; `01:75` and `directive.md:160`
put the Trebuchet's city damage at 45 while the rule text and `end_turn.py:1670` say 55; `06:185`
attributes the general's +1 movement aura to a manual page that says "one tile" (`manual.clean.txt:1095`)
while the code uses two; `enemy_cities_seen` is computed and consumed by nothing (`end_turn.py:47,1340`);
`08:34` quotes "military 262 -> 306" against its own table's 262 -> 282 (306 is a row from another
game's diary); `08:70-71` cites `prompts/tasks/tmp/023-dutch-siege-corps.md`, retired to
`done/023-dutch-siege-corps-done-T259.md` on 2026-09-28.

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
   `directive.md:223`, `turn-checks.md:224` and `staging.py:45`.
2. `07:39,69,74`: `get_deal_options` -> **`get_trade_options`**, and drop the "37 iron" claim
   (`narrate.py:1099-1114` prints types, not amounts).
3. `07:234,288,345` and `06:11`: delete the Siege Tower as gate 4's answer; state the ram rule once -
   an owned ram stacks with the melee unit, nothing is bought.
4. `05:83-88` and `07:276`: stop promising `WOUNDED IN REACH` from the MCP loop (or print it).
5. `07:114` and `02:43`: `mass-on-contact` does not reach a raid or peacetime contact - either say so
   or scope the rule.
6. `06:10` "melee, anti-cavalry and cavalry"; add the anti-cavalry row to `06`'s table; `01:19`'s
   Pike and Shot either joins `counter-the-cavalry`'s list or the chain ends at Pikeman.
7. `military-map.md:104-108`: replace "do not clear barbarian camps" with the camp doctrine that
   `07`, the directive and `answer-the-camp` already carry.
8. `03:9-10` point step 1 at the `== Events ==` damage line; `03:54-57` add the `UNUSED ATTACK`
   bounce and `skip_remaining_units(force=True)`; `08:34` 306 -> 282; `08:70-71` repoint to
   `done/023-dutch-siege-corps-done-T259.md`; the minor batch from class D.
9. **Already applied in this pass**: the `RENEWABLE_ENERGY` cost correction in `tactics/08` and in
   `prompts/checks/pending/power-the-cities.md` (see class D below).

**Code (each one new behaviour, so each needs tests):**

10. **`pillage`**: add the verb to `unit_action` (`server.py` + a `GameState` method + Lua
    `UNITOPERATION_PILLAGE`), or delete the directive's line and the ladder rung. The directive orders
    it today and nothing can do it.
11. **A rally ring**: extend the staging Lua with a `d >= 3` ring (or a rally query) so
    `_rally_option` can fire, and let the tool answer `04`'s step 1.
12. **A line-of-sight/fire flag per ring tile**: the single highest-value addition - it unblocks
    `04` step 6.2, `05`, `06` row 0 and `07` Gate 2 at once.
13. **`SIEGE POSTURE` availability**: do not return `None` at staging distance, and print the gun
    count even for one siege unit, so `04`'s reading exists in `04`'s state.
14. **A read-only combat estimate tool** (expose `build_combat_estimate_query`), so `02:80-84` can be
    obeyed without committing the attack.
15. **Corps/Army**, or drop the paragraph.
16. **Delivery**: a `get_tactics(name)` MCP tool (or advisor-side injection) so the file text stops
    depending on the parent's memory - measured today at 1 session in 158.
17. **A consistency test**: read `turn-checks.md`'s unit lists and counts and assert that
    `01`/`06`'s establishment table agrees with them. That is the durable fix - it is the class of
    drift that produced the siege-2 finding and the Pike-and-Shot mismatch, and nothing catches it
    today.

## Method note and limits

The per-file audits were run by four subagents against the code, not against the prose; every claim
above carries the file and line that proves it, and the two headline findings I re-verified myself
(`pillage` has no verb, and the rally leg is unreachable because the test ring is synthetic). What
this audit does **not** cover: whether the *doctrine itself* is good strategy (that is the
directive's and the retrospectives' business), and any file outside `prompts/tactics/` - the same
class of check has not been run on `prompts/workers/*.md`, where one contradiction is already known
(the camp paragraph above).
