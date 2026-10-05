# Military strategy: what the model can see, and what is actually enforced

Written 2026-10-01, answering the question "are all the military strategies visible, and are they
guaranteed to be carried out". Every claim here is measured against the code or against the recorded
sessions - the instruments and their numbers are named as they come up, so the answer can be re-run
rather than re-argued.

**The short answer.** The *combat conduct* half of the doctrine is visible and loud: 21 of the 27
live rules are about the army (`hold-what-you-take` makes 22 if the cities it takes are counted, and
the remaining five are purely domestic), they are evaluated every turn, and their failures are
printed and counted. The *per-decision playbooks* - `prompts/tactics/01`-`08`, the files that decide
what to build, where to stage and when to advance - are effectively **invisible**: no tool reads
them, the advisors have no tools at all by design, and in 158 recorded sessions seven of the eight
never reached a single advisor brief. Nothing in this system is *guaranteed* to be executed in the
sense of "the agent cannot do otherwise" except the two hard rungs below; everything else is loud,
and loud can be ignored with a diary line.

## 1. The six channels a strategy can travel on

| # | Channel | Carrier | When the model sees it | Measured |
|---|---|---|---|---|
| A | **The directive** | the DIRECTIVE block of `.dsh/skills/civ6-orchestrator/SKILL.md` (42,179 chars) | appended to the `end_turn` result **once per change**, plus once on the first call in a process (`src/civ_mcp/server.py:2493`, `strategy_directive.py:53`) | delivery is code, not habit: it cannot be skipped while `end_turn` is called |
| B | **Live rules** | `prompts/checks/turn-checks.md`, 27 rules (21 about the army) | `CHECK FAILED [id] ... (require: ...)` on every `end_turn` while failing; the `TURN START` briefing appended to the same result adds the streak | 43 of 158 transcripts had a live rule fail; 21 of 27 rules have fired at least once (`node .tools/rule-census.mjs`); the briefing itself reaches essentially every session that plays a turn - 44 of the 66 transcripts showing a turn advance, and 21 of the other 22 predate the feature (`cc1c4a1`, 2026-09-21) |
| C | **Turn-result blocks** | `end_turn`'s own output | when the block's condition holds, that turn | over the adapter logs: BATTLE ASSESSMENT 195, SIEGE POSTURE 131, SIEGE PROGRESS 147, SIEGE FIRE 74, SIEGE STALLED 2, LOYALTY WARNING 34, UPGRADE AVAILABLE 154, WAR ECONOMY 18, 10-TURN REVIEW 94, MATCHUP 5 (`python .tools/block-census.py`). Since 2026-10-01 it also carries `NEW TARGET`, the one block that reacts to a city becoming visible, and a resolving move appends an `IN SIGHT` block to its own reply - section 7 |
| D | **Tool refusals** | the `ERR:` set in `src/civ_mcp/lua/*.py` | only at the moment the order is issued | 18 military-relevant codes: `SIEGE_CANNOT_ATTACK_UNITS`, `MELEE_CANNOT_ATTACK_AT_SEA`, `NO_LOS`, `OUT_OF_RANGE`, `NO_MOVES`, `STACKING_CONFLICT`, `ZOC`, `REQUIRES_WAR`, `NOT_AT_WAR`, `NO_WALLS`, `ALREADY_FIRED`, `ATTACK_BLOCKED`, `CANNOT_ATTACK`, `NO_TARGETS`, `CANNOT_CONDEMN`, `NO_CONDEMN_COMMAND`, `STOPPED_SHORT`, `NOT_YOUR_TERRITORY` |
| E | **The tactics playbooks** | `prompts/tactics/01`-`08` | only if the orchestrator reads the file **and pastes its text** into the `civ_advisor` call | **seven of eight never appeared in a brief**; `04` appeared in 1 session (3 advisor lines). Files read at all: 01 in 7 sessions, 04 in 3, 05/06/07/08 in 1-2, and 02/03 in **none** (`node .tools/tactics-in-briefs.mjs`) |
| F | **The reference** | `AGENTS.md` (injected every session), `docs/turn-result-blocks.md` and `docs/game-recovery.md` via `search_knowledge` | session start, or on demand | `AGENTS.md` is injected by the harness; the docs are one query away and are cited by `AGENTS.md` at the point of use |

**Why E fails is structural, not accidental.** The DSH overlay gives the advisor route **no tools at
all** - `dsh/civ6.cordis.yml:45-46`, `toolFilter.allow: []`, with the comment "advisors can reason
over snapshots but cannot invoke any tool or create descendants". So an advisor cannot read the
playbook itself; the only path is the orchestrator reading it and pasting the text, which the skill
asks for in prose (`SKILL.md:673`) and which the measurement says almost never happens.

## 2. The enforcement ladder

"Guaranteed" is not one thing. Five rungs, strongest first:

1. **Refused** - the order cannot be carried out. The agent gets an `ERR:` and nothing happens.
2. **Blocked** - the turn will not end until something is done (`end_turn` returns a blocker:
   unmoved units, an empty queue, and `UNUSED ATTACK` when a legal attack would be discarded).
3. **Reported every turn until fixed** - a live rule fails, and the streak is in the next
   `TURN START` briefing. Loud, but the agent may accept it by recording why in the diary.
4. **Reported while the condition holds** - a block in the `end_turn` result: the numbers and the
   named units, no persistent streak.
5. **Doctrine only** - nothing surfaces it at the moment of the decision. It works only if the
   right file happens to be in context.

## 3. The military strategies, area by area

| Decision area | Where the doctrine lives | What enforces it | Rung |
|---|---|---|---|
| **Production & the establishment** (1-3 guns, 2 melee, 4 ranged, 1 anti-cavalry, 1 cavalry) | `tactics/01`, directive `:229` | `siege-train`, `ranged-mass`, `melee-screen`, `counter-the-cavalry`, `upgrade-the-siege`, `upgrade-the-unwatched`, `keep-the-upgrade-discount`, `match-their-melee` | **3** |
| **Contact on discovery** (assess, counter, mass or bypass) | `tactics/02` | `mass-on-contact` (3); the `counter:` lines in BATTLE ASSESSMENT (4); "assess before committing" is prose | **3/4**, assessment itself **5** |
| **Under attack** (assess, mass, annihilate; when to withdraw) | `tactics/03` | `answer-the-attack`, `finish-the-wounded`, `use-your-attacks` (3) + the `UNUSED ATTACK` blocker (2) | **2/3** |
| **Staging & the rally** (assemble at d3 first, then advance as one body) | `tactics/04` | `issue-the-calls-furthest-first` covers the *traffic* (3); the rally itself is printed by `get_staging_plan` (`ASSEMBLY FIRST`, `RALLY x,y d3`) and checked by nothing | **4** for the print, **5** for the rule that the army must gather first |
| **Formation & screening** (screen in front, siege behind at range 2) | `tactics/05` | `screen-the-siege` (3) + `SIEGE POSTURE` naming each exposed unit (4) | **3/4** |
| **Assault composition & fire** (order of work, concentration, no ram/tower, promotion timing) | `tactics/06` | `concentrate-the-siege`, `take-the-city`, `cover-the-capture` (3); `SIEGE FIRE`, `SIEGE PROGRESS`, `SIEGE STALLED` (4); the ram/tower **ban** has no rule since `ram-tower-before-civil-engineering` retired at T99 - only the capture move is refused for a support unit (1) | **3/4**, ban **5** |
| **Pre-war analysis** (gates 0-5 before declaring) | `tactics/07` | nothing blocks a declaration; `get_target_report` supplies gates 0-3's data on demand (4); the camp branch has `answer-the-camp` (3) | **4/5** |
| **War & the home front** (one war city, +10 gold floor, builders compound) | `tactics/08` | `carrying-capacity`, `builder-backlog`, `hold-what-you-take`, `one-garrison-per-city` (3); `WAR ECONOMY` and `10-TURN REVIEW` (4) | **3/4**, "one war city" **5** |
| **Barbarian camps** (raid or leave, the six gates) | `tactics/07` camp branch, directive `:35` | `answer-the-camp` (3) + `camps_within_3`; `get_staging_plan` on the camp tile prints `WALK-IN OPENS` (4); the human-facing "report a convertible barbarian" is prose | **3/4** |
| **Religion** (condemn heretics, kill missionaries, attack faith income) | directive | `condemn` answers `ERR:REQUIRES_WAR` and `attack` answers `ERR:NOT_AT_WAR` at peace (1); since 2026-10-01 a `FOREIGN RELIGIOUS UNITS` block names every sighting within three tiles with the doctrine for its case (4), `religious_at_war_within_2` is a staged rule (3 once promoted), and `unit_action(action="pillage")` exists, which is what "attack the faith income" always meant | **1** at peace, **3/4** in war |
| **Peace** (never propose it, refuse every offer) | directive | `propose_peace` is in the orchestrator's `FORBIDDEN_TOOLS` (`dsh/orchestrator/contracts.mjs`), so the sole writer gets `forbidden_tool` instead of a peace (1); refusing an incoming offer is a `respond_to_*` call the agent still has to choose | **1/5** |
| **Movement & traffic** (one unit per tile, ZOC, movement points, call order) | `tactics/04`, `AGENTS.md` | `STACKING_CONFLICT`, `ZOC`, `NO_MOVES`, `OUT_OF_RANGE` (1); `STOPPED_SHORT` warnings + `MOVE JAMS` + `issue-the-calls-furthest-first` (3/4) | **1/3** |
| **The command split** (the human commands the military, the session everything else) | the division block `resume-game.ps1 -HumanMilitary` appends to the task | the appended task text (5); the per-turn whose-move split - `get_notifications` appends `WHOSE MOVE` and writes `agent-half.txt` beside the heartbeat (4); `SKILL.md`'s carve-out on `skip_remaining_units` (5) | **4/5** |

## 4. What the measurements say

**Rules.** 27 live, 21 of them about the army (22 with `hold-what-you-take`; the other five are
domestic: a wonder, a district slot, gold, builders, power). 21 have fired at least once in recorded
play; 6 never have:
`concentrate-the-siege`, `attacks-that-land-nothing` and `power-the-cities` were cut in on
2026-09-30/10-01, so zero is expected; `take-the-city`, `cover-the-capture` and `answer-the-camp`
are older and have still never been observed failing. `take-the-city`'s gate is a city at 0 HP with
one of our capture-capable units adjacent - a state that is transient by design, because the city
falls the same turn. The catch it exists for (Moscow at `0/200` with a Spearman two tiles away,
which healed back to `120/200`) is cited in its own comment and predates the metric, so **the guard
has never been seen to catch anything**.

**Blocks.** The fight's blocks speak constantly in war sessions - one long war session records
BATTLE ASSESSMENT 12, SIEGE PROGRESS 11, SIEGE FIRE 1, LOYALTY WARNING 13. `TAKE THE CITY` and
`UNUSED ATTACK` have not been observed at all in the adapter census, which matches the rule census
above: the final step of an assault is the least-instrumented one.

**Playbooks.** 98 of 158 sessions called an advisor at all (4,535 `civ_advisor` lines), and the
advisor text is where the per-decision doctrine is supposed to arrive. It did once.

## 5. The gaps, and the fix for each

**G1 - the playbooks are invisible at the decision (the big one).** The doctrine lives in files that
nothing reads at the moment it is needed, and the advisor cannot fetch them itself. Fixes, cheapest
first:
1. **A `get_tactics` tool**: call it with a name (`get_tactics("04")`) or with nothing, in which
   case it names the file(s) the current metrics point at and returns their text. That turns "read
   the file, remember to paste it" into one call whose result *is* the brief material. This is
   audit item 16, and the same tool can be what the skill's advisor step names.
2. **Fold the decisive numbers into the rules**, which are already delivered: the siege band is in
   `siege-train`, the supply lever in `cut-the-supply`, the formation in `screen-the-siege`. This is
   the durable half of the fix and it is partly done.
3. **Give the advisor route read-only file access** (`read`/`glob`/`grep` in the overlay's
   `toolFilter`). That is a safety decision rather than an engineering one: the empty allowlist is
   deliberate, and this survey does not recommend changing it without the human's word.

**G2 - doctrine that is only prose, where the action is possible and nothing stops it.** Declaring a
war without the gates; building or fielding a ram/tower (its rule retired at T99 and the ban then
lived only in the directive); proposing peace; "one war city"; the religion standoff in war. Each is
a candidate for a rule or a refusal - the cheapest are the ram/tower (a production-side rule is
possible: no `BATTERING_RAM`/`SIEGE_TOWER` in any queue) and the declaration (a `once: true` gate or
a rule that fails while an army is at war-footing with no visible target).

**G3 - guards that have never spoken.** `take-the-city`, `cover-the-capture`, and the `TAKE THE
CITY` block have never been observed firing. Either the state is genuinely rare in play or the
metric is unreachable; the way to tell them apart is one targeted check in the next war - the
`SIEGE PROGRESS` block already reads `city hp: N/200`, so a turn where it reads 0 with our melee
adjacent and no `TAKE THE CITY` block is a metric bug, and that is worth one diary line to record.

**G4 - the metric blind spots that make part of the doctrine unenforceable.** Zone of Control was
invisible to both pathing tools, so a plan could route through it and the unit just stopped; and the
plan's arrival turns were extrapolated from movement points rather than the real per-tile cost. Both
halves are now closed - the religious-unit half on 2026-10-01 (section 6) and the movement half on
2026-10-02 (section 7) - and closing the religious half also exposed that the predicate the docs had
carried for months was wrong: there is no `FORMATION_CLASS_RELIGIOUS` in the game's data at all.

## 6. What changed on 2026-10-01: the discovery path

The worked example the question asked for ("a scout discovers a city - how does the agent find
out?") turned out to have no working answer, so it was built. The old chain: a move returned only
tiles (`MOVING_TO|58,42|from:54,40`), the one block that named *content* was gated on tiles revealed
for the first time **in this session** and fired zero times for a city or a camp in 158 recorded
sessions, and nothing in `end_turn` reacted to a city appearing - `enemy_cities_seen` is computed and
**no rule reads it**, and the capture blocks stay silent until a pool is empty. Discovery was a pull:
`get_map_area` gives the tile and its owner (`[CITY_CENTER]`, no name), `get_trade_options` gives a
met civ's city names, `get_target_report` gives everything.

Three changes, all of them delivery rather than new analysis:

1. **`IN SIGHT` on the move** (`narrate_sight`, `game_state.move_unit`): every move that resolves now
   reports what the unit can see from where it stopped - a foreign city (with its owner), a barbarian
   camp, enemy units - with no dependence on novelty. A revealed-but-not-currently-visible city is
   excluded, so a remembered capital does not re-announce itself every turn.
2. **The discovery line carries the doctrine**: a city line ends with `get_target_report(x,y)` and
   `prompts/tactics/07-pre-war-analysis.md` to paste into the advisor brief; a camp line names
   `tactics/07`'s camp gates. The two follow-ups ride in the same message as the sighting, which is
   the cheapest possible fix for G1's "the doctrine never arrives".
3. **`NEW TARGET` in `end_turn`**: the first turn a foreign city is visible it is named in the result
   with its owner, population, capital flag and war state, plus the same two follow-ups. The
   comparison is per process and its **first scan only seeds**, so a fresh session does not announce
   the whole map. This is the check that would have fired in every session that met a neighbour and
   said nothing.

   Tests: `tests/test_discovery_delivery.py` (19) - the sight block's four cases, the scan's two new
   fields, back-compat with a nine-field row, the move integration, and the `NEW TARGET` diff
   (seeding, one report per city, no re-report after a city leaves and returns).

**What this does not fix**: the advisor still cannot read a playbook (the overlay gives it no tools),
so the paste is still the orchestrator's decision - the fix is that the decision now arrives with the
discovery. G3 and G4 are untouched.

### 2026-10-01, second pass: the religious-unit half of G4

The question "what do we do about a religious unit of a civ we are *not* at war with" turned out to
have a doctrine and no machinery. The doctrine: at peace nothing can touch it (`attack` →
`ERR:NOT_AT_WAR`, `condemn` → `ERR:REQUIRES_WAR`, a city strike → `NO_ENEMY`), never declare war over
missionaries alone, do not police conversions of our own cities, watch `get_religion_spread` for a
real victory run, and hit the *faith income* at its source in the next war. The machinery: none - the
unit was invisible (see below), the rule set said nothing, and the doctrine's own answer
(pillage the Holy Site) had no verb.

- **The predicate the docs carried was wrong.** There is no `FORMATION_CLASS_RELIGIOUS` in the game's
  data: a Missionary is `FORMATION_CLASS_CIVILIAN` with `ReligiousStrength="100"` and no
  `PromotionClass` at all (Apostle 350, Inquisitor 200, Guru 200 - `Base/Assets/Gameplay/Data/Units.xml`).
  The threat scan filtered on `Combat > 0 or RangedCombat > 0`, so it dropped every one of them before
  any metric could count it. Fixed in `AGENTS.md`, its backup, and this survey.
- **They are visible now**: the scan prints `RELIGIOUS|` rows (predicate `ReligiousStrength > 0`),
  `end_turn` carries a `FOREIGN RELIGIOUS UNITS` block naming each one within three tiles and stating
  the doctrine for its case, and the two counts `religious_within_3` / `religious_at_war_within_2` are
  in `_CONTACT_METRIC_KEYS`. The war-time half is a **staged** rule (`answer-the-missionary`, in
  `prompts/checks/pending/`) because the tuple is read at import time; the peace-time half is
  deliberately not a rule - "ignore it and watch the victory count" cannot be expressed as a
  requirement, and a rule that cannot be satisfied is worse than none.
- **`pillage` exists** (`unit_action(action="pillage")`, `UNITOPERATION_PILLAGE`): the verb the
  directive has been ordering since its first draft, and audit item 10. It reports what is on the
  tile first, refuses the four ways it goes wrong (no moves, out of range, nothing there, already
  pillaged), and tells the caller how to verify.
- **The peace-time lever is the map**: a foreign unit cannot enter a tile ours occupies, and without
  open borders it cannot enter our territory at all - so a neutral-lane missionary can be blocked by
  standing in its way. Now written into the directive (with "never pull a unit off the front for it"),
  because it is the one concrete thing peace allows besides monitoring.

Tests: `tests/test_religious_units.py` (18) - the predicate, both parsers, the block's two cases, the
metrics, the staged rule's shape and the staging boundary, and the pillage verb's operation,
diagnosis and dispatch.

## 7. What changed on 2026-10-02: the movement half of G4

The other half of G4 was two facts no plan could see: **which tiles an enemy's zone of control
covers**, and **what a path actually costs to walk**. The old arrival turn was
`ceil((#path - reach) / reach)` - a tile count extrapolated from movement points - so a route that
climbed hills or clipped an enemy ZOC was scheduled as if it were flat and empty, and the stop
arrived as a surprise (`STOPPED_MID_PATH`, 232 of them over T228-T299, measured).

- **The walk** is one shared Lua helper (`_MARCH_HELPER` in `src/civ_mcp/lua/units.py`), embedded in
  `get_pathing_estimate` and `build_staging_plan_query` alike: it walks the route tile by tile,
  paying each tile what the map says (`plot:GetMovementCost()`), follows the engine's own reachable
  set for the current turn (`UnitManager.GetReachableMovement` already knows terrain, rivers and
  ZOC) and the unit's own `GetMaxMoves()` for the turns after it.
- **The ZOC stop** comes from the game's own flag, `GameInfo.Units[type].ZoneOfControl`: `true` for
  the melee, cavalry and anti-cavalry line and `false` for every ranged and siege unit, so the scan
  marks the tiles around the units that really project one. Entering such a tile spends the rest of
  that turn's movement (manual:875), light and heavy cavalry excepted (manual:735-737). Every option
  now carries `cost: N` and `zoc:N`, the reply names the first stop as `ZOC STOP at (x,y) on turn +k`,
  the plan prefers a route that does not stop when two tiles would arrive on the same turn, and
  `arrive T+n` counts the lost turn instead of reporting it afterwards.
- **The edges are stated, not hidden.** An enemy in fog cannot be known, so `zoc:0` means "none
  visible on this route"; a river crossing or an embark after the first turn is not modelled
  (manual:73); and a game that will not report `GetMaxMoves()` keeps the old tile-count arithmetic
  and says so (`cost:-1`, `zoc:-1` - "not known", never "clear").

Tests: `tests/test_march_route.py` (36) - the flag and the cavalry exemption, the fallback, both
parsers with and without the new fields, the tie-break, the rendered row, the narration, and a real
Lua parse of all four emitted chunks (`luaparser`, now in the dev group in `pyproject.toml`).

### 2026-10-02, second pass: four mechanisms that had no teeth

An adversarial review of the preset looked for rules whose machinery does not do what the strategy
says. Four were real, and each fix has a test:

- **`concentrate-the-siege` fired in peacetime, and counted a friend's city.** Its `when` had no war
  gate, and `siege_in_city_range` was measured against the nearest city of *any* major civilisation -
  so the moment a second gun existed the rule failed every turn until two guns stood outside
  somebody's walls, which is the opposite of "build the siege train before the war". `SIEGE POSTURE`
  now reports `city_distance` (any city: the assembly's reference, which is meaningful before a
  declaration) and `war_city_distance` (a city of a civ we are at war with), the metric counts the
  second, and the rule is gated on `metric(at_war) >= 1`.
- **`propose_peace` sat in the sole writer's allowlist.** Both presets forbid peace and the ban was
  prose with a live tool behind it: `dsh/orchestrator/contracts.mjs` now carries `FORBIDDEN_TOOLS`,
  the tool is out of every allowlist, and the refusal is a `forbidden_tool` error that names the
  directive.
- **A `once: true` goal one match achieved was gone for every other match.** The check file is shared
  and the sweep that prunes achieved goals edits it in place; the trace named no match, so a new
  match inherited the deletion - measured, A3-A7 ran ~340 turns with `dynasty-cycle-wonder` absent
  from the loop and all eight sessions ordered zero wonders. The trace now records the match, and
  `turn_checks.restore_foreign_games` puts another match's goal back on load; an unattributable old
  trace is left alone rather than guessed at.
- **The English-only gate did not cover the two documents that reach a model without `use-strategy`
  naming them.** Every `message:` line of `prompts/checks/turn-checks.md` is printed to the
  orchestrator the moment its rule fails, and `prompts/workers/*.md` is the brief an advisor is
  handed; both carried Chinese the gate could not see, because `ASCII_ONLY` listed three basenames.
  They are covered now (nine Chinese lines in the rule file and two in `military-map.md` are
  English), a test pins the playbooks' bilingual exception against that, and another asserts the
  worker briefs stay byte-identical to a preset's copy - they are copies, and nothing compared the
  two trees.

**Still open from that review, because they are decisions and not defects**: the war-end condition
("it ends only when the enemy's cities are yours" against a domination victory that needs capitals),
what a war we did not start is for, the abort case for a target nothing can reach, what to do with a
city that flips by loyalty, and whether the establishment should name the anti-cavalry slot that
`counter-the-cavalry` already requires.

## 8. How to re-run this survey

```powershell
node .tools/tactics-in-briefs.mjs      # did each playbook reach an advisor brief
node .tools/rule-census.mjs            # which live rules actually fired, and which never have
python .tools/block-census.py          # which end_turn blocks appear, per session
python .tools/audit-md-language.py     # the document/backup state, for completeness
```
