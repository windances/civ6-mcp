# Civ 6 MCP - Agent Reference

An MCP server connecting to a live Civilization VI game via FireTuner. You can read full game state
and issue commands. All commands respect game rules. Starting a **new** game - the civ kit, the
research path, the first victory hypothesis - is `docs/new-game.md`; this reference is the
running-game loop. Human instructions given in Chinese are quoted here in English; the verbatim
originals are in the task files under `prompts/tasks/tmp/` and in `docs/task-history.md`.

**You only know what you explicitly query.** A human player passively absorbs the score ticker,
religion lens, unit health bars - you have none of that. Information you don't ask for simply
doesn't enter your world model. The patterns below exist to compensate for this.

## Temporary tasks are files: read `prompts/tasks/tmp/` at the start of every turn

**IN FORCE NOW:** `023-dutch-siege-corps.md` (take every Dutch city with the existing army, on the human's instruction; the west lane stays a screen) and `025-two-scouts-to-sea-contact.md` (two scouts to sea, on the human's instruction: make contact with civilizations we have not met, and do not get drawn into a fight).

A temporary instruction is **a file, not a paragraph in this reference**. This section is the
*procedure* for them: how to obtain them, how to read one, how to tell which are still in force, and
where the detail lives. It records neither a task's content nor its retirement - **the file is the
task**, `prompts/tasks/tmp/current_tasks.md` is the live register, and `docs/task-history.md` is the
record.

### How a task reaches the turn

- **Read every `*.md` in `prompts/tasks/tmp/` as part of the turn's first step** -
  `get_game_overview` and then that directory - and again whenever the turn takes a decision a task
  touches. Not `README.md`, not `current_tasks.md`, and not `done/`. An empty directory is the
  normal state.
- **Nothing else in the loop knows those files exist:** they are not checkable rules, they carry no
  metric, and the MCP cannot see the filesystem, so a task file is executed only because the turn
  loop looked there. **The `IN FORCE NOW` line above is the channel that makes a newly arrived file
  visible** - a file dropped in while a session is already playing reaches it only when that session
  re-lists the directory, and tasks have sat unread for five turns until the line named them
  (measured). Changing the line re-injects this whole section into the running session, so **update
  it in the same commit that adds or retires a task** - the reminder is what carries the news; the
  files carry the instructions.

### How to read a task

- Each file states its own scope (`scope:`), what it outranks (`overrides:`), its observable end
  (`done when:`) and a hard stop (`expires:`), plus `added:` for the instruction it came from. A
  task that contradicts the standing directive is settled by its `overrides:` line - that is what
  the line is for, so nothing has to be guessed.
- **A `done when:` an agent has to argue about is a task that never retires.** Require it to name
  something the game can be queried for: a tile, a count, a metric or a turn.
  `tests/test_temp_tasks.py` holds every task file to all five header lines, to an observable
  `done when:` and to an `expires:` that names a turn.
- **`expires:` must be reachable** - when the finish line needs production, count the turns from the
  queue, not from the calendar of the other tasks.
- For a task that **is** mechanically checkable, prefer a `once: true` goal in
  `prompts/checks/turn-checks.md` instead: the engine retires that one itself the turn it is
  satisfied (it prints `CHECK ACHIEVED ... retired` and deletes the block). A file is for what no
  metric can express.

### Which tasks are in force

- **What is in force is the directory listing.** A file present is an instruction in force; a file
  absent is a task that no longer exists. `prompts/tasks/tmp/done/` holds the retired ones, its
  names carrying the turn (`...-done-T<turn>.md`, `...-expired-T<turn>.md`).
- **When a task ends is in the file's own `done when:` and `expires:` lines** - it is finished the
  turn one of them holds, not when it has been read and not because this section says so.
- `prompts/tasks/tmp/current_tasks.md` is the live register: one line per in-force task with its
  `expires:`, so the shape of the current work is visible at a glance. It is an index - **the file
  is the authority on the task** - and `docs/task-history.md` is prose history, which is not an
  instruction.

### The detail itself

- **The task file is the detail.** Its `scope:` and `overrides:` bound what it authorizes, its
  numbered steps are the order of work, and its `done when:` is the only finish line.
- **Retire it in the turn it ends**: move it to `done/`, rename it as above, update `IN FORCE NOW` and
  `current_tasks.md` in the same commit, and record that turn in the diary's `tooling` line. An expired
  task left behind is an instruction that never retires.
- **The mechanical half is one command**: `python scripts/temp-task.py add ...` writes the task file, the
  register row and this list together, runs the mandatory text gate and `tests/test_temp_tasks.py`, and
  commits only when both are green; **`--why` is English and carries no tile coordinate** - it is the
  one part of a task file that lands in *this* reference, so name the target in words ("the
  city-state the file names"), leave the coordinate in the task file where this match's state
  belongs, and the script refuses a `--why` that carries one; `... retire <nnn> --done` (or `--expired`) `--turn N` moves the file
  into `done/` and re-syncs the register and this list; `... status` prints what is in force, what turn
  the game stands on and whether the three sources agree. `scripts\temp-task.cmd` (cmd and PowerShell)
  and `bash scripts/temp-task.sh` (Git Bash and any POSIX shell) are the same command without the
  interpreter path. What it does **not** write is the diary's `tooling` line and
  `docs/task-history.md` - those stay yours.
- **It also keeps a Chinese backup of every task** (`--cn`), written to `prompts/tasks/cn/` and
  deliberately **not** into this directory: the turn loop reads every `*.md` in `prompts/tasks/tmp/`,
  so a backup placed beside the task would be read as a second instruction. `--no-cn` skips it on
  purpose, and the task file records that. **The command it was published with is recorded too**, as an
  HTML comment at the end of the task file (and one more when it is retired), so a reader can check how
  the file was made - which also means re-publishing the same slug needs `--replace`, or a second
  publish files a duplicate task instead of updating the one you meant.
- The `IN FORCE NOW` line and the directory are checked against each other by `tests/test_temp_tasks.py`,
  so a retirement that is not recorded goes red instead of quietly staying in force.

## File encoding: a document with Chinese in it carries a UTF-8 BOM

On a zh-CN machine an editor that cannot see a BOM decodes the file as codepage 936 (GBK) and shows
mojibake for text whose bytes are valid UTF-8. The rule: **a document holding a non-ASCII byte
carries a BOM; an English `.en.` file is pure ASCII and carries none; a Chinese `.zh.` file always
carries one.** **This reference is held to the English bar** (human instruction 2026-09-27: it is
English only), so it is pure ASCII and carries **no** BOM - a non-ASCII character here is a
translation somebody started, or a mark like an em dash, and both the gate below and
`tests/test_text_encoding.py` fail on it. The agent's own `write`/`edit` tools emit plain UTF-8 and
**silently strip the BOM**, so after editing a `.zh.` file, `SETUP-WINDOWS.md`, a tactics file, or a
temporary task file, run:

```
python scripts/fix-text-encoding.py             # put the BOM back, normalise this file's marks
python scripts/fix-text-encoding.py --check     # report only; exit 1 when one is missing
```

**Every document DSH hands the model is English only** (human instruction 2026-09-28): this reference,
`.dsh/skills/civ6-orchestrator/SKILL.md`, and the preset `prompts/strategies/<name>/directive.md` that
`scripts/use-strategy.ps1` copies into that skill's DIRECTIVE block. All three are pure ASCII with no
BOM, and `civ_mcp.text_encoding.ASCII_ONLY` is what holds them there, so `--check` fails on a Chinese
line in any of them. **When a change carries Chinese, translate it into English and write the
English** - a Chinese line in one of these files is a failure, not a draft. **Each one has a Chinese
backup beside it, `<name>.cn.md`** (`AGENTS.cn.md`, `SKILL.cn.md`, `directive.cn.md`): it is generated
from the English file for a human reader, never edited and never a source, and DSH cannot load it -
the harness reads `AGENTS.md` / `CLAUDE.md`, and a skill has to be a file named exactly `SKILL.md`.
`scripts/set-strategy.ps1 -Text` refuses non-ASCII input for the same reason, and
`tests/test_dsh_documents.py` fails on a Chinese line, on a backup DSH could load, or on a backup that
is missing.

**The check is mandatory, and it is more than the BOM**: a BOM says nothing about whether the
characters are still the ones somebody wrote, so the gate also greps every file for the damage a GBK
round trip leaves behind. It runs in `git commit` (`.githooks/pre-commit`, installed once per clone
by `python scripts/install-hooks.py`), and `tests/test_text_encoding.py` runs the same check, so a
damaged document turns the suite red instead of reaching a prompt. **Never edit these documents
through a `Get-Content | Set-Content` round trip** - that is the one thing the gate exists to stop.
The whole mechanism, the repair tool and the exemption list are `SETUP-WINDOWS.md` ("the BOM is
load-bearing", line 634).

**A batch of document edits leaves two derived things stale, and both are one command:**

```
python scripts/fix-text-encoding.py --check   # the mandatory gate: BOMs + GBK round-trip damage
python .tools/kb.py index                     # the knowledge index
```

The index is *derived*: a query against a stale one answers confidently with text that no longer
exists.

## Coordinate System

**Hex grid: (X, Y) where higher Y = visually south.**
- Y increases -> south (down). Y decreases -> north (up).
- X increases -> east. X decreases -> west.
- Moving from (9,24) to (9,26) is **south**, not north.

## Turn Loop

Each turn in order:
1. `get_game_overview` - turn, yields, research, score, era score, difficulty. It also carries the
   **TURN START** briefing once per turn: the rules from `prompts/checks/turn-checks.md` that are
   failing, how many turns each has been failing, what the last turn actually bought, your own plan
   quoted back, and a verdict. Read it **before** planning - if it says the plan is not being
   executed, change one thing this turn and say in the diary which turn it lands. **Then read the
   temporary tasks: every `*.md` in `prompts/tasks/tmp/`** (not `README.md`, not `current_tasks.md`,
   not `done/`) - those files are instructions in force, nothing else in the loop knows they exist,
   and each one carries its own `done when:` and `expires:` so you can retire it and say so. If
   resuming after context compaction, call `get_diary` first.
2. `get_units` - positions, HP, moves, charges, nearby threats
3. `get_map_area` around cities/units - terrain, resources, enemy units
4. Move/action each unit. **Before the assembly's first move, write the staging plan** (human
   instruction 2026-09-26: plan the assembly before the first move - the column must not jam,
   units have different movement allowances, and nothing moves until the best plan is found):
   one row per unit - where it is now, its movement allowance, the one tile it goes to, the
   `get_pathing_estimate` cost, the turn it arrives, its role, and whether it can fire from there.
   **`get_staging_plan(city_x, city_y)` builds that table for you** from the game's own pathfinding:
   distinct tiles, the conflicts named, and the turn the assault opens. The three staging rules - never two
   units on one tile, name the corridor, and fill the **last** firing tile first - are
   `prompts/tactics/04-staging-out-of-range.md` step 3b. **The same three phases - analysis
   (`tactics/07`), staging (`tactics/04` + this tool), execution (`tactics/05`/`06`) - run on every
   enemy city and every barbarian camp** (human instruction 2026-09-26), so pass a **camp's** tile
   exactly as you pass a city's: the ring and the assignment are the same, the reply says `STAGING PLAN
   for the camp at x,y` and `WALK-IN OPENS`, and there is no supply line to cut.
5. `get_cities` - queues, growth, pillaged districts
6. `get_district_advisor` if placing a new district
7. `set_city_production` / `set_research` if needed
8. Run **Strategic Checkpoints** if it's time
9. `end_turn` - it evaluates `prompts/checks/turn-checks.md` on **every** turn and prints every
   failing rule (`CHECK FAILED [id] ... (require: ...)`); a `once: true` rule is a goal that retires
   itself, and an achieved goal is pruned from the file after a timestamped copy goes to
   `prompts/checks/archive/`. Fix the gap, or record in the diary why it is being accepted - either
   way it must not pass unnoticed. The same result carries the blocks that decide a fight -
   `SIEGE POSTURE` (ending in `SIEGE FIRE: n/m`), `BATTLE ASSESSMENT`, `SIEGE PROGRESS`,
   `TAKE THE CITY`, `LOYALTY WARNING`, `UPGRADE AVAILABLE`, `UNUSED ATTACK` - plus **empire
   warnings** every turn (loyalty crises, idle trade routes, gold deficits, resource caps,
   scoreboard position, military imbalance) - and every one of them has a rule attached. **What each
   block means, and which measurement produced it, is `docs/turn-result-blocks.md`**; read that
   before acting on a block you have not seen before.

## Looking things up: `search_knowledge`

You only know what you query, and part of what decides a turn is documentation, not game state -
how a city heals, what a support unit may do, what the doctrine says about screening.
`search_knowledge(query, k=5, doc=None)` searches a local index of the **game manual**, the
**directive and rule file**, `AGENTS.md`, `SETUP-WINDOWS.md` and the retrospectives, and answers
with the source path and line range plus a highlighted snippet. Read those lines (and cite them)
instead of paraphrasing from memory:

```
search_knowledge("city heals supply line zone of control")
search_knowledge("what can a battering ram do", doc="manual")
search_knowledge("<a Chinese phrase>", doc="manual")   # a CJK query falls back to substring match
```

Build or refresh the index with `python .tools/kb.py index` (it is per checkout, and stale after the
corpus changes). The default corpus is `prompts/`, `docs/`, `AGENTS.md`, `SETUP-WINDOWS.md` **and
the extracted manual** `.tools/manuals/manual.clean.txt` - `--source` **replaces** that list rather
than adding to it, so passing one source by hand builds an index that has lost the rest (measured
2026-09-26: a rebuild with no `--source` silently dropped the manual, 100 docs instead of 104 and no
manual at all). When a mechanic is in doubt, this is cheaper and more honest than a guess - and the
manual beats the doctrine when they disagree, because the doctrine is only ever a summary of it. **A
mechanic the manual does not cover is answered by the game's own files**, not by memory: the
install's `Base/Assets/Gameplay/Data/*.xml` and `Base/Assets/Text/en_US/*.xml` carry the
authoritative rulings (that is where `UNITCOMMAND_CONDEMN_HERETIC` and its
`LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION` were found).

## Diary

The diary is your persistent memory across sessions. When context compacts or you return to a game,
`get_diary` is how you reconstruct where you were and why you made the decisions you did. Entries
with specific details - unit names, coordinates, yield numbers, reasoning - are far more useful to
your future self than brief summaries.

Reflections are recorded **before** AI processing begins - write what YOU observed and did this
turn. Anything that surfaces after `end_turn` (a diplomacy proposal, AI units entering your
territory, events in the turn result) belongs in the **next** turn's diary, not this one.

Five reflection fields each turn (all required, non-empty):
- **tactical**: What happened - specific units, tiles, outcomes.
- **strategic**: Standings vs rivals - yields, city count, victory path viability with numbers.
- **tooling**: Tool issues observed, or "No issues".
- **planning**: Concrete actions for the next 5-10 turns - specific builds, moves, research targets
  with turn estimates.
- **hypothesis**: Specific predictions - attack timing, milestone turns, biggest risks.

## Strategic Checkpoints

Periodic checks worth doing regularly. The game doesn't surface most of this proactively.

### Around every 10 turns:
- **The `end_turn` result carries a `10-TURN REVIEW`**, and a `WAR ECONOMY` line while a war is on:
  read what the window actually bought, and **answer its three questions in that turn's diary** -
  was the window efficient, with numbers; which prerequisite for the next goal is in place and which
  is missing; does the planned completion turn still hold, and if not, what changes. What each of
  those blocks measures is `docs/turn-result-blocks.md`.
- `get_empire_resources` - unimproved luxuries and nearby strategics
- Surplus luxuries: duplicates beyond 1 copy provide zero amenity benefit. Trade them via
  `propose_trade` for GPT, strategic resources, or luxury types you don't own (each new type = +1
  amenity to 4 cities). Even 5 GPT per surplus luxury adds up over 30 turns. Use `mode="test"` to
  check what the AI will accept before sending.
- Gold/faith balance: if either is accumulating with no plan, spend it - `purchase_item`,
  `purchase_tile`, `patronize_great_person`
- City count vs time in game - if expansion is behind, a settler tends to be the highest-leverage
  production choice
- `get_trade_routes` - check for idle routes; idle routes are free yields going uncollected
- Government tier - `change_government` when a new tier unlocks (free the first time)
- Era score vs thresholds - shown in `get_game_overview`; a Dark Age is recoverable but costly
- Great People - `get_great_people`; rivals will recruit what you don't

### Around every 20 turns:
- `get_diplomacy` - delegations to new civs, friendships with Friendly civs, alliances if eligible
- `get_victory_progress` - check all 6 victory types, not just your own path
- `get_religion_spread` - religious victory is invisible without active checking; a rival with
  majority in most civs is a serious threat

### Around every 30 turns:
- `get_strategic_map` - fog per city + unclaimed resources
- `get_global_settle_advisor` - best remaining settle sites
- Wonder scan: `get_city_production` in your best city - wonders that align with your victory path
  are worth considering
- Victory path check: is your chosen path still viable? Is any rival close to winning something you
  haven't been tracking?
- Civ kit check: are you building/using your unique units, buildings, or improvements? If not,
  you're playing a generic civ and giving up your structural advantage. The unique unit often
  requires a specific tech - if that tech isn't on your current research path, that's a problem.

## Military tactics, by decision

`prompts/tactics/` holds eight files, one per decision, written for the advisors (files 1-7 for
`military-map`, file 8 for `economy-cities`; their prompts name which to read when). Read the
matching one before improvising:

| File | What it decides |
|---|---|
| `tactics/01-unit-production.md` | Unit production - the assault establishment, what to build first, what to buy |
| `tactics/02-contact-on-discovery.md` | Contact on discovery - assess, counter unit, mass or bypass |
| `tactics/03-under-attack.md` | Under attack - assess, mass, annihilate; the withdrawal cases |
| `tactics/04-staging-out-of-range.md` | Staging outside enemy range - rally point choice, contact on the march, when to advance |
| `tactics/05-formation-and-screening.md` | Formation and screening - screen in front, siege behind at range 2 |
| `tactics/06-assault-composition-and-fire.md` | Assault composition and fire - order of work, concentration, when to break off |
| `tactics/07-pre-war-analysis.md` | Pre-war analysis - can we take it, whom, in how many turns, at what cost, and can we hold it; **a barbarian camp is a target too** (camp gates: CAMP/GUARD/FORCE/GROUND/WORTH/HOLD/GO) |
| `tactics/08-war-and-the-home-front.md` | War and the home front - one war city, everything else compounds; gold/turn against the +10 floor |

**Before a war, file 7 comes first, and its own first step is reconnaissance** - Gate 0 is "a
candidate city is actually visible". An army in the right shape with every enemy city still in fog
has no pre-war analysis to make; send the scout and the fastest cavalry, then run the gates. **File
7 has two target classes**: an enemy city (a war) and a barbarian camp (a raid - the camp is a
target of that same analysis, with six camp gates instead of the city's five).

## Strategic Patterns

**Interface facts and measured traps, not doctrine.** The strategy is the directive, which the
orchestrator skill loads every session; the per-decision playbooks are `prompts/tactics/`, which the
advisor prompts carry. What belongs here is what a tool does that the obvious reading gets wrong,
and where a topic is owned elsewhere this section points at it and stops.

### Moving civilians
`get_map_area` (radius 2) around a builder's, settler's or trader's destination is worth the query:
civilians have zero combat strength and losing one costs 5-7 turns of production plus its charges.
**Two refusals look like tool failures and are not** (measured T92-T93): a **land unit cannot embark
without `TECH_SHIPBUILDING`** ("water tile - land units need Shipbuilding tech to embark"), so a
strait is impassable and a "dark map" may simply be ocean; and a tile owned by a **city-state
refused our scout while `get_city_states` listed us as its Suzerain with 5 envoys**, so route around
it rather than assume suzerainty grants passage. Hills, forests and jungles cost 2 movement each and
stack (forest-hills 3+), so a 2-move civilian that lands on forest-hills cannot act until the next
turn. `get_pathing_estimate(unit_id, target_x, target_y)` uses the game's own pathfinding.

### Builders
`get_builder_tasks` lists every tile that needs work, prioritized (URGENT > HIGH > NORMAL) with the
nearest idle builder for each: call it once per turn and dispatch top-down. A builder 3-4 tiles away
is still worth the walk, and map tiles print movement cost (`[mv:2]`, `[mv:3]`) and roads, so route
along them.

### Growth and settling
The thresholds, which are hard stops rather than warnings: **food surplus <= 0** is worth fixing
this turn (Farm, Granary, domestic Trade Route, `set_city_focus(city_id, "FOOD")`) and
**turns-to-growth > 15** says the city needs food infrastructure; **`housing - pop <= 1`** stalls a
city for dozens of turns, so fix it now or settle the next city on fresh water; a negative-loyalty
site needs `assign_governor` or a garrison the turn it is founded or it flips.

### Exploration
You cannot settle or counter what you have not seen. A scout on `automate` keeps the information
flow going, and replacing a lost scout early is cheaper than the turns spent blind.

### War declaration
War takes effect in diplomacy immediately, but **the combat engine does not sync until the next
turn**: declare on turn N, position that turn, attack on N+1. Do not reload or retry when attacks
answer `NO_ENEMY` on the declaration turn.

### Wartime
A city with walls can fire at an enemy within 2 tiles (`city_action(city_id, "attack", target_x,
target_y)`) - measured 43 damage, no retaliation, which is the cheapest damage in the empire - and a
captured city is resolved with `city_action` (`keep`, `raze`, `liberate_founder`, `liberate_previous`)
or the turn will not end. **Peace is the directive's business, not this reference's**: it forbids
`propose_peace` outright, and every offer that arrives is refused, so under that strategy a war ends
only when its cities are yours.

### Military readiness
`get_diplomacy` carries rival military strength, and a neighbor at twice your strength that is
neither a friend nor an ally is the risk worth tracking. Units that fall behind their tier lose
fights they would have won - `upgrade_unit` needs tech, resources and gold. Garrisons while a war is
on are the rule `one-garrison-per-city`; the peacetime standing army is the directive's call.

### Barbarian camps - the half the doctrine does not cover
The camp doctrine is the skill's and `tactics/07`'s: the six gates C1-C6, "no HP, no walls, no
garrison bonus, one military unit moving onto its tile destroys it", Spearmen are anti-cavalry, and
convert an adjacent barbarian before the raid. What is only here is the tooling.

- **Locate the camp from the map every time.** A camp can be cleared by someone else and respawn
  nearby, and a coordinate copied from an old diary has already been wrong once (measured: a diary
  note and the next map read put it on different tiles - the case is
  `prompts/tasks/tmp/done/001-clear-the-camp-done-T84.md`).
- **The raid has a one-command entry point:** `scripts\run-dsh-headless.ps1 -TaskFile
  prompts\tasks\clear-the-camp.zh.txt` (English: `clear-the-camp.en.txt`) - one raid end to end, without
  declaring war and without changing the development plan.
- **A camp is visible to the rules.** `end_turn` computes `camps_within_3` from `get_map_area` (a
  camp is the tile improvement `IMPROVEMENT_BARBARIAN_CAMP`, so no new Lua was needed) and
  `answer-the-camp` is live in `prompts/checks/turn-checks.md`. **A rule naming a metric the running
  server does not compute reports `un-evaluable` every turn and nobody can satisfy it**, which is
  why a new rule is staged in `prompts/checks/pending/` until a server computing its metric is
  running.
- Report `CAMP / GUARD / FORCE / GROUND / WORTH / HOLD / CONVERT / GO`, and report a convertible
  barbarian - one next to our melee units - **before** the raid, so the human can
  use the leader ability (Three-Six Stratagems) from the game UI.

### Religion - the one fact no metric can see
A religious unit is `FORMATION_CLASS_RELIGIOUS` with `Combat = 0`, so **every contact metric and
every rule is blind to it, and the tile's unit list in `get_map_area` is the only detector**. The
strategy on them is the directive's (`prompts/strategies/china-conquest/directive.md`): at peace one
cannot be touched at all (`condemn` answers `ERR:REQUIRES_WAR`, `attack` answers `ERR:NOT_AT_WAR`, a
city strike returns `NO_ENEMY`), and faith income is attacked at its source instead. The
`get_religion_spread` cadence is in **Strategic Checkpoints** below.

## Combat Quick Reference

- Ranged attacks don't take damage; melee attacks do
- Forests/mountains block ranged LOS - targets with blocked LOS are filtered from `get_units` attack
  lists
- Fortified units: +4 defense, heal each turn
- Combat estimates include promotion CS bonuses, flanking (+2 per adjacent friendly to defender),
  support (+2 per defender's adjacent friendly), and forest/jungle defense (+3)

## Unit Actions Reference

| Action | Effect | Notes |
|--------|--------|-------|
| `move` | Move to tile | target_x, target_y required |
| `attack` | Attack enemy | Shows damage estimate; melee/ranged auto-detected. **A siege unit (Catapult/Trebuchet/Bombard) cannot attack units** - it attacks cities and districts only, and asking it to hit a unit comes back `ERR:SIEGE_CANNOT_ATTACK_UNITS`; use a ranged unit (Crossbowman) against units. |
| `condemn` | Destroy an adjacent enemy religious unit (Condemn Heretic) | A game **command**, not an attack (`unit_action(action="condemn")`); the engine picks the adjacent Missionary/Apostle/Inquisitor, so the reply names every candidate first. **The game requires a war declaration** (`LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION`), so a friend's missionary cannot be condemned by anyone - a peace-time target comes back `ERR:REQUIRES_WAR`. Added 2026-09-26 for task 008. |
| `fortify` | +4 defense, heals | Military only |
| `heal` | Fortify until full HP | Auto-wakes at full HP |
| `alert` | Sleep, wake on enemy | Sentry use |
| `skip` | End unit's turn | Always works |
| `automate` | Auto-explore | Scouts only |
| `delete` | Disband unit | Removes maintenance |
| `found_city` | Settle | Settlers only |
| `improve` | Build improvement | Builders and Military Engineers; see improvements below |
| `remove_feature` | Chop/harvest feature | Builders only; removes forest, jungle, or marsh from tile |
| `build_route` | Build road/railroad | Military Engineers only; on current tile; no charges used |
| `trade_route` | Start route | Traders; target_x/y of destination city |
| `teleport` | Move idle trader | Traders only; target_x/y of city |
| `activate` | Use Great Person | Must be on completed matching district |
| `spread_religion` | Spread religion | Missionaries/Apostles |

Common improvements: `IMPROVEMENT_FARM`, `IMPROVEMENT_MINE`, `IMPROVEMENT_QUARRY`,
`IMPROVEMENT_PLANTATION`, `IMPROVEMENT_PASTURE`, `IMPROVEMENT_CAMP`, `IMPROVEMENT_FISHING_BOATS`,
`IMPROVEMENT_LUMBER_MILL`

Feature removal: Forest, jungle, and marsh tiles block most improvements (e.g. Farm). Use
`remove_feature` to chop/harvest the feature first, then `improve` to build. Lumber Mill and Camp
work on forest/jungle without removal. Check `valid_improvements` in `get_units` output - if FARM
isn't listed on a tile you expect it, the tile likely has a blocking feature.

Builders repair tile improvements. Pillaged **district buildings** (Workshop, Arena, etc.) are
repaired via `set_city_production`.

`get_cities` shows unimproved resource tiles and pillaged improvements/districts per city - use this
to prioritize builder work without needing to scan `get_map_area` manually.

Military Engineers (requires Encampment + Armory): `build_route` builds a railroad on the current
tile (no charges consumed; costs 1 Iron + 1 Coal per tile). `improve` with `IMPROVEMENT_FORT` or
`IMPROVEMENT_AIRSTRIP` uses charges. Building a railroad consumes all movement - one tile per
engineer per turn.

| Other unit tools | |
|--------|--------|
| `skip_remaining_units` | Skip all units with remaining moves (useful after diplomacy). **Refuses and names the units while any has a legal attack** - pass `force=True` to discard them deliberately |
| `upgrade_unit(unit_id)` | Upgrade to next type (requires tech + resources + gold) |

## End Turn Blockers

`end_turn` resolves blockers before advancing. If it returns a blocker:
- **Units**: unmoved units need orders (move / skip / fortify)
- **Production**: city queue empty - set new production
- **Research/Civic**: completed - choose next
- **Governor**: point available - `get_governors` -> `appoint_governor` /
  `assign_governor(governor_type, city_id)` / `promote_governor(governor_type, promotion_type)`
- **Promotion**: unit has XP - `get_unit_promotions` -> `promote_unit`. **A promotion consumes the
  unit's whole turn** (manual, `EXPENDING XPS`, `manual:704-713`), so promote after it has attacked,
  or while it is out of range or healing - never instead of an attack. Match it to the job: melee
  taking cities want the anti-garrison/damage line, ranged want the ranged-strength line.
- **Policy Slot**: empty - `get_policies` -> `set_policies`
- **Pantheon/Religion**: faith threshold reached - `get_pantheon_beliefs` -> `choose_pantheon`; for
  founding: `get_religion_beliefs` -> `found_religion`
- **Envoys**: tokens available - `get_city_states` -> `send_envoy`
- **Dedication**: new era - `get_dedications` -> `choose_dedication`
- **City Capture**: conquered or disloyal city -
  `city_action(city_id, "keep"/"raze"/"liberate_founder"/"liberate_previous")`
- Move responses show the **target tile**, not arrival position (async pathfinding). **A move or
  attack that reports `STOPPED_SHORT` or `STOPPED_MID_PATH` may still have taken effect** - measured
  T141, a Horseman's attack reported "could not reach target" while the target was left at 26 HP.
  Re-read with `get_units` before re-ordering anything that reports a short or partial movement.
- **A post-combat city read is an estimate, not a fact** (measured). The result line can report
  `read unchanged`, or the pool unmoved, **after the damage has landed** - including on the blow
  that takes the city. Judge progress from the `SIEGE PROGRESS` block and from a *later* read, never
  from the immediate reply - and do not conclude from one stale number that the attack did nothing.
  The case record is `docs/retrospectives/2026-09-27-thebes-alexandria-T194-T218.md`.
- **A turn that will not advance is usually waiting for an answer, not for a popup.** `end_turn`
  answers `Turn paused ...` when an AI diplomacy session or an incoming trade deal is open, and both
  are yours to settle: `get_pending_diplomacy` then `respond_to_diplomacy`, and `get_pending_trades`
  then `respond_to_trade`. Reach for `dismiss_popup` only after those two come back empty. It clears
  the popup layer - wonder, era, boost and disaster screens, a leader scene, a cinematic camera left
  running - and answers `PENDING|DiplomacyActionView` or `PENDING|DiplomacyDealView` instead of
  closing either, because closing a session from Lua hangs turn processing and dismissing a deal
  view silently rejects an offer you never saw. Most popups never need the call at all: a background
  watcher dismisses the non-critical ones about a second after they appear, and the Windows crash
  dialogs are clicked away for you. **Nothing in Lua can see a dialog outside the game** - if
  `dismiss_popup` reports nothing and the turn is still stuck, read the screen with
  `.tools/whats-on-screen.py` before concluding the game is hung (`docs/game-recovery.md`).

## Diplomacy

**Reactive (AI-initiated):** AI encounters block turn progression. Use `get_pending_diplomacy` to
check for open sessions, then `respond_to_diplomacy` (POSITIVE/NEGATIVE, 2-3 rounds). Diplomacy
sessions do not affect unit movement or orders - continue commanding units normally afterward.

**Proactive:**
- `send_diplomatic_action(action="DIPLOMATIC_DELEGATION")` - 25g, worth sending on first meeting
- `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` - requires Friendly status
- `send_diplomatic_action(action="RESIDENT_EMBASSY")` - requires Writing tech
- `form_alliance(player_id, type)` - types: MILITARY/RESEARCH/CULTURAL/ECONOMIC/RELIGIOUS; requires
  friendship 30t + Diplomatic Service civic
- `propose_trade(player_id, ...)` - trade gold/GPT/resources/favor/open borders/cities. Use
  `mode="test"` first to see the AI's counter-offer without committing, then `mode="send"` to
  finalize. Cities use `city_id` from `get_trade_options`.
- `propose_peace(player_id)` - white peace; 10t war cooldown required. **The directive forbids it**:
  never call it, and refuse every offer, whether it arrives as a trade or as a session
- `get_trade_options(other_player_id)` - see what a civ has available to trade (gold, resources,
  favor, cities, agreements)
- `get_pending_trades` - check incoming trade offers; `respond_to_trade(player_id, accept)` to
  accept/reject
- Check `get_diplomacy` for defensive pacts before declaring war
- `get_diplomacy` shows leader agendas - historical agendas are always visible; random agendas
  require Secret diplomatic visibility (spy in their capital or alliance). Use agendas to predict AI
  behavior and avoid relationship penalties.

**Espionage:** `get_spies` -> `spy_action(spy_id, action, ...)`. Actions: `travel` to a city first,
then run operations (steal tech, neutralize governors, etc.). Offensive missions only work after the
spy arrives.

**City-states:** `get_city_states` -> `send_envoy`. Suzerainty = +1 favor/turn. Types:
Scientific/Industrial/Trade/Cultural/Religious/Militaristic.

**Diplomatic Favor:** earned from government tier (base +1, scales with tier), alliances (+1/t per
level), suzerainties (+1/t). Spend in World Congress for Diplomatic Victory Points; favor above ~100
with no congress imminent is better deployed in a trade than banked.

## Production & Research

Wonders - high-production cities can slot these between infrastructure. Use
`get_wonder_advisor(city_id, wonder_name)` for placement, then `set_city_production` with
target_x/y. Science: Great Library, Oxford University, Kilwa Kisiwani. Culture: Chichen Itza,
Forbidden City. General: Ancestral Hall, Pyramids.

**Research:** `get_tech_civics` sorts by turns ascending; items 2 turns away or less are flagged
`!! GRAB THIS` - cheap boosted techs are easy to miss and can unblock entire production chains.

**Purchasing:** `purchase_item(city_id, item_type, item_name)` - buy units or buildings instantly
with gold (default) or faith (`yield_type="YIELD_FAITH"`). `get_city_production` shows purchasable
items and costs.

**Tiles:** `get_purchasable_tiles(city_id)` -> `purchase_tile(city_id, x, y)` - buy border tiles
with gold for strategic resources or district placement.

## District Placement

Use `get_district_advisor(city_id, district_type)` for ranked tiles. Then `set_city_production` with
target_x/y.

| District | Adjacency bonuses |
|----------|------------------|
| Campus | +1 per mountain, +1 per 2 jungles, +2 geothermal/reef |
| Holy Site | +1 per mountain, +1 per 2 forests, +2 natural wonder |
| Industrial Zone | +1 per mine/quarry, +2 aqueduct |
| Commercial Hub | +2 adjacent river, +2 harbor |
| Theater Square | +1 per wonder, +2 Entertainment Complex |
| Encampment | cannot be adjacent to city center |

## Trade Routes

- `get_trade_routes` - see all active routes and idle traders
- `get_trade_destinations(unit_id)` -> available destinations
- `unit_action(action='trade_route', target_x, target_y)` -> start route
- Domestic routes: food + production to new cities. International: gold.
- Capacity: 1 from Foreign Trade civic, +1 per Market/Lighthouse
- Idle routes are free yields going uncollected

## Great People

- `get_great_people` - candidates, recruitment progress, and costs
- `recruit_great_person(individual_id)` - recruit with accumulated GP points (check `[CAN RECRUIT]`)
- `patronize_great_person(individual_id)` - buy instantly with gold or faith
- `reject_great_person(individual_id)` - pass, advance to next candidate in that class
- Rivals will recruit what you pass on - recruiting quickly tends to be worth it
- **Great Generals and Great Admirals are the exception to activating.** The aura is
  what they are worth: +5 combat strength and +1 movement to land units within range
  (naval units for an Admiral), granted **passively while the unit is alive**.
  `activate` is a *retirement* - it consumes the unit and pays out a one-off.
  `get_great_people` prints both: keep the general with the army and do not activate
  it unless that one-off is what you actually want. Activating a general on the turn
  it is recruited throws away the aura for the rest of the game.
- For every other class, move the GP to its matching completed district and
  `unit_action(action='activate')`
- If activation fails, the error message includes the requirements (district type, buildings needed)
- Don't delete GPs - they show 0 builder charges but that's a different system; they're not consumed
  until activated (except a general or admiral, which activation retires)

## World Congress

WC fires synchronously inside `end_turn()` - register votes **before** calling end_turn.

**Voting flow:**
1. `get_world_congress()` - when `turns_until_next = 0`, WC fires this turn
2. Review resolutions (options A/B, target list, favor costs)
3. `queue_wc_votes(votes='[{"hash": H, "option": 1, "target": 0, "votes": N}]')`
4. `end_turn()` - handler fires, votes deploy, turn advances

- `hash`: from `get_world_congress`; `option`: 1=A / 2=B; `target`: player_id resolved to list index
  at runtime; `votes`: max to spend
- 1 free vote per resolution (costs nothing - worth casting)
- **If you register no votes at all, `end_turn` casts the free ones for you** - one vote per
  resolution, 0 favor, with the option and the target chosen per resolution from the game's own
  resolution data (which side is the ban and which is the buff, and whether the target should be
  you) - and its result names what it cast. That is a net, not a decision: the fallback is capped at
  the free vote on purpose, so when the session matters call `queue_wc_votes` yourself, because only
  you can rank the targets and only votes beyond the free one spend favor.
- Extra votes cost 6/18/36/60/90/126... cumulative favor
- Keeping 50-100 favor in reserve between sessions provides flexibility for the next session
- DVP resolutions: read what each option actually awards before voting. Concentrate favor on the
  single most impactful resolution rather than spreading thin. Verify your vote blocks the rival,
  not accidentally helps them

## Victory Conditions

| Victory | Win Condition | Monitor Via |
|---------|---------------|-------------|
| Science | 4 space projects complete | `get_victory_progress` |
| Domination | Own all rival original capitals | military strength in `get_diplomacy` |
| Culture | Foreign tourists > every civ's domestic | tourism in `get_victory_progress` |
| Religious | Your religion majority in ALL civs | `get_religion_spread` regularly |
| Diplomatic | 20 diplomatic victory points | World Congress votes |
| Score | Highest score at turn limit | fallback |

All victories trigger immediately when the condition is met - they do not wait for a turn boundary
or WC session. A rival reaching 20 DVP wins before your next turn. The only counter is stripping DVP
at a World Congress *before* they reach 20.

`end_turn` runs a victory proximity scan every turn and a full snapshot every 10 turns. These
warnings are the primary signal for invisible victories - worth paying attention to.

## Game Recovery

**Ask where the game is before touching anything: `get_game_status`** - `not_running` / `starting` /
`in_game` / `leader_screen` / `main_menu` / `loading` / `tuner_busy`, plus the turn and a `NEXT:`
line. Infer the state from that call, never from the wording of whichever call happened to fail.

**One session at a time.** FireTuner serves exactly one connection. `kill_game` and
`restart_and_load` refuse while another session is playing (they name the pid), and a second MCP
cannot attach while that one lives - waiting changes nothing. Stop it with `scripts\civ6-clean.ps1`,
or keep playing in its session.

**Handing the match to a fresh session is one command, and it is not the agent's:**
`scripts\resume-game.ps1` (check and report), `-Wait` (wait for the human's load, then launch),
`-Rollback`, `-DryRun`. It reads only passive signals, never launches and never loads, and generates
the session's task from the facts it just read.

**Everything else is `docs/game-recovery.md`** - the two recovery traps, the `0_MCP_NNNN` name
collisions across rolled-back branches, the `AutoSave_NNNN` offset, `orient.py`, `turn-of-save.py`,
`auto-turns.py`, loading by name, the hang recovery and the save list. Read it before any recovery:
it is the section that used to live here, unchanged, and it is still the authority.
