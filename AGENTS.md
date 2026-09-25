# Civ 6 MCP — Agent Reference

An MCP server connecting to a live Civilization VI game via FireTuner. You can read full game state and issue commands. All commands respect game rules.

**You only know what you explicitly query.** A human player passively absorbs the score ticker, religion lens, unit health bars — you have none of that. Information you don't ask for simply doesn't enter your world model. The patterns below exist to compensate for this.

## Temporary tasks are files: read `prompts/tasks/tmp/` at the start of every turn

**IN FORCE NOW — read each of these files before planning the turn:**
`007-destroy-russia.md`, `008-destroy-missionaries.md`, `009-city-near-niter.md`.
(`001-clear-the-camp` was retired at T84, `003-two-scouts-explore` at T93, `002-focus-fire-scouts`
expired at T95, `004-city-near-iron` was **done at T101** — 成都 stands at (60,31) with the iron at
(60,32) inside its first ring — `006-prepare-for-russia` was retired at **T110**, its assault
establishment complete on paper but the iron still `0/50` and the target city never read in its four
numbers, and `005-city-near-copper` was retired **EXPIRED at T115** with no copper city founded: the
site at (50,33) was a bonus tile worth about +2 gold and never justified a sixth city, which is
exactly what that file said to do if the ranking came out badly. All six sit in
`prompts/tasks/tmp/done/` with the turn in their name. **This list and that directory are checked
against each other** by `tests/test_temp_tasks.py`, so a retirement that is not recorded here goes red
instead of quietly staying in force.)

Priority: **007 outranks everything else** — it is the objective (消灭俄罗斯) rather than a build order.
Its gates are the directive's own
checklist: **3 Catapults per city** (一城3投石车 — met at T122), a melee unit above the Warrior tier
once the iron stockpile passes 20, and a four-number read of **the first target** before any
declaration — **not of every Russian city** (human instruction 2026-09-26: 不用获取所有城市信息才开战;
the rest are read as the army reaches them, and scouting them is not a gate). **The Battering Ram the
empire already owns joins the assault** (human instruction 2026-09-26: 已经有攻城锤，就参战) — a support
unit beside the melee, where it makes their attacks do full damage against walls; nothing new is built,
and beside a city read as `walls none` it is dead weight. It is also the **only**
file that authorizes the declaration of war on Russia; 006 deliberately did not.

**008 rides along with 007, it does not postpone it**: destroying missionaries is lane-clearing, not a
second war. The verb now exists — `unit_action(action="condemn")` implements the game's own
`UNITCOMMAND_CONDEMN_HERETIC` (added 2026-09-26, live at the next MCP start), reporting every adjacent
candidate before it fires — and **the game itself requires a war declaration** for it, so the case it
serves is a Russian missionary once 007 declares: a civ we are at peace with cannot be condemned by
tool or human (`ERR:REQUIRES_WAR`). Record the reply either way in the diary's `tooling` line.

**009 is third and waits on the war**: a Niter city, with a Settler (80 hammers) allowed in a city that
is **not** the war city, an escort out of the garrison rotation, and nothing pulled off the staging row
or the declaration. Its expiry (T175) is counted from the queue, because 005 expired unused by being
counted from the calendar.

**Expiries must be reachable.** 004 and 005 originally expired at T95, in the same batch as the raid
tasks — but a Settler line alone runs to ~T95, so a T95 expiry made both impossible by design and the
session reported it. 004 was extended to T105 and was in fact **completed at T101**; 005 is T115 and 006
is T110. When writing a task whose finish line needs production, **count the turns from the queue, not
from the calendar of the other tasks**.

**This list is the mechanism, not decoration.** A file added to `prompts/tasks/tmp/` while a session is
already playing reaches it only when that session re-lists the directory; the paragraph below says to do
that every turn, but nothing enforces it, and a task can sit unread for turns (measured: 002 was picked
up within a turn, while 003 and 004 went unnoticed for five turns until this list named them). Changing
this section re-injects it into the running session, so **update the list in the same commit that adds or
retires a task** — the reminder is what carries the news; the files carry the instructions.

A temporary instruction is **a file, not a paragraph in this reference**. A task is finished when its own
`done when:` line holds, at which point the file is moved into `prompts/tasks/tmp/done/` with the turn
number in its name, and the list above is updated to match.

- **Read every `*.md` in `prompts/tasks/tmp/` as part of the turn's first step** — `get_game_overview`
  and then that directory — and again whenever the turn takes a decision a task touches. Not
  `README.md`, and not `done/`. **Nothing else in the loop knows those files exist:** they are not
  checkable rules, they carry no metric, and the MCP cannot see the filesystem, so a task file is
  executed only because the turn loop looked there. An empty directory is the normal state.
- Each file states its own scope (`scope:`), what it outranks (`overrides:`), its observable end
  (`done when:`) and a hard stop (`expires:`). A task that contradicts the standing directive is
  settled by its `overrides:` line — that is what the line is for, so nothing has to be guessed.
- **A file present is an instruction in force; a file absent is a task that no longer exists.** Do not
  leave a finished or expired task in the directory: move it to `done/`, rename it
  `…-done-T<turn>.md` or `…-expired-T<turn>.md`, and record it in the diary's `tooling` line with
  that turn number. An expired task left behind is an instruction that never retires.
- For a task that **is** mechanically checkable, prefer a `once: true` goal in
  `prompts/checks/turn-checks.md` instead: the engine retires that one itself the turn it is
  satisfied (it prints `CHECK ACHIEVED … retired` and deletes the block). A file is for what no metric
  can express.

`end_turn` now runs **empire warnings** automatically — alerts for loyalty crises, idle trade routes, gold deficits, resource caps, scoreboard position, and military imbalance. These compensate for the most common blind spots, but don't replace periodic deep checks (victory progress, religion spread, diplomacy).

## File encoding: a document with Chinese in it carries a UTF-8 BOM

On a zh-CN machine an editor that cannot see a BOM decodes the file as codepage 936 (GBK), so
`游戏应当已经在运行` is shown as `娓告垙搴斿綋宸茬粡鍦ㄨ繍琛` — the bytes are valid UTF-8 and nothing is
corrupt, the viewer guessed wrong. The rule: **a document holding a non-ASCII byte carries a BOM; an
English `.en.` file is pure ASCII and carries none; a Chinese `.zh.` file always carries one.**

**The agent's own `write`/`edit` tools emit plain UTF-8 and silently strip the BOM** (measured on
`prompts/tasks/continue-current.zh.txt` and on `AGENTS.md`). So after editing `AGENTS.md`, a tactics
file or a temporary task file, run:

```
python scripts/fix-text-encoding.py            # put the BOM back
python scripts/fix-text-encoding.py --check     # report only; exit 1 when one is missing
```

`tests/test_text_encoding.py` checks the same rule, so the suite goes red until it is run — the
repair is one command, not a promise. The MCP reads these files as `utf-8-sig`
(`turn_checks.py`, `knowledge.py`, `strategy_directive.py`), so a BOM never reaches a prompt or a
parsed rule.

## Coordinate System

**Hex grid: (X, Y) where higher Y = visually south.**
- Y increases → south (down). Y decreases → north (up).
- X increases → east. X decreases → west.
- Moving from (9,24) to (9,26) is **south**, not north.

## Game Start

Before your first turn:
1. Read your civ's unique abilities, units, and buildings — what is this civ designed to do?
2. Identify the tech/civic that unlocks your unique unit; plan a research path to reach it.
3. Form a working hypothesis for a victory path. Hold it loosely — geography and rivals will clarify things through the Classical era.

Early choices compound. Each decision shapes what's available 20, 40, 60 turns later. A scout reveals the map early; a defensive unit lets your settlers move safely; more cities mean more districts which mean more everything. Religious civs often benefit from Holy Site infrastructure before the Great Prophet pool fills. What you don't build early, you pay for later.

## Turn Loop

Each turn in order:
1. `get_game_overview` — turn, yields, research, score, era score, difficulty. It also carries
   the **TURN START** briefing once per turn: the rules from `prompts/checks/turn-checks.md`
   that are failing, how many turns each has been failing, what the last turn actually bought,
   your own plan quoted back, and a verdict. Read it **before** planning — if it says the plan
   is not being executed, change one thing this turn and say in the diary which turn it lands.
   **Then read the temporary tasks: every `*.md` in `prompts/tasks/tmp/`** (not `README.md`, not
   `done/`) — those files are instructions in force, nothing else in the loop knows they exist, and
   each one carries its own `done when:` and `expires:` so you can retire it and say so.
   If resuming after context compaction, call `get_diary` first.
2. `get_units` — positions, HP, moves, charges, nearby threats
3. `get_map_area` around cities/units — terrain, resources, enemy units
4. Move/action each unit
5. `get_cities` — queues, growth, pillaged districts
6. `get_district_advisor` if placing a new district
7. `set_city_production` / `set_research` if needed
8. Run **Strategic Checkpoints** if it's time
9. `end_turn` — it also evaluates `prompts/checks/turn-checks.md` on **every** turn and
   prints every failing rule in the result (`CHECK FAILED [id]: … (require: …)`). Those are
   not suggestions: they are the strategy directive's checkable rules, measured against the
   units you actually have and this turn's diary row. Fix the gap, or record in the diary
   why it is being accepted — either way it must not pass unnoticed. A rule marked `once: true`
   is a **goal**: when you satisfy it you get one `CHECK ACHIEVED … retired` line and it stops
   being checked for the rest of the game, so a rule disappearing from the list means it was
   done, not that the check broke. The same turn also reports `CHECK FILE PRUNED`: the achieved
   goal is removed from `prompts/checks/turn-checks.md`, after a timestamped copy is written to
   `prompts/checks/archive/`. What stays in the file is exactly what is still outstanding.
   Two of those rules are about **contact on the march**: if enemy units are within two tiles
   of your units while the army is assembling, you are walking past something that will kill the
   siege train — the requirement is `use-your-attacks` (no legal attack may be left unused) plus
   `mass-on-contact` (two or three attackers on the target, not one), and `counter-the-cavalry`
   when the enemy in contact is cavalry with no anti-cavalry unit in the army. Deal with it this
   turn, with the counter unit — or record in the diary why you deliberately let it pass. Two
   more are about **attacks you already have**: `use-your-attacks` fires while a
   legal attack is still unused (`skip_remaining_units` now names those units as it discards
   them), and `finish-the-wounded` fires when an enemy within two tiles is at 20 HP or less and
   nothing attacked — a wounded enemy comes back, and **how fast depends on where it stands**: the
   manual's healing rates are 20 HP/turn in a city, 15 in friendly territory, 10 neutral, 5 in
   enemy territory (naval 2, friendly only). The one that must not be left alive is the enemy
   inside a city; the one to compare against is the enemy in the field at 5–10. The same numbers
   are the reason to rotate **our own** damaged units back across the border: 15/turn at home
   against 5/turn where they were hit. Once a
   war is on, two more apply: `one-garrison-per-city` (one unit per city, everything else at the
   front) and `answer-the-attack` (a unit that was hit gets a response this turn — fight back,
   screen it, or withdraw and say so). When a unit is hit — or the moment enemy forces come into
   contact — the turn result also carries a **BATTLE ASSESSMENT**: every enemy within three tiles
   with its class, strength, HP, distance, and how many of your fighting units are already in
   range. Use it — mass two or three attackers on one target so it dies this turn
   (`mass-on-contact` fails while an enemy is in contact and only one of your units is in range),
   rather than trading one-for-one. Before an assault, the same result carries a **SIEGE POSTURE**
   line per siege unit — distance to the nearest enemy, how far that enemy is from the unit
   screening it, and distance to the nearest enemy city. Form up outside enemy range with the
   melee in front and the siege behind (`screen-the-siege` fails while a siege unit is within two
   tiles of an enemy with nothing closer to that enemy than itself), then advance. When you are
   attacking a city, the result now always carries its numbers — `city hp: N/200, walls: N/100 or
   none` — and the turn result carries a **SIEGE PROGRESS** block with the delta, escalating to
   `SIEGE STALLED` after three recorded turns without a net drop. A city heals about twenty points
   a turn **while it has a supply line** — the manual's rule is that any adjacent hex outside your
   units' zone of control is a supply line, so standing on (or beside) every adjacent hex stops the
   heal outright, which is cheaper than out-damaging it. Fire that neither cuts the supply nor
   out-damages the healing is fire that never happened: fix the assault or break it off.
   **A city only changes hands when a capture-capable unit walks onto its tile** — melee,
   anti-cavalry or cavalry; ranged, siege and support units cannot — and that last step has no
   damage number attached to it, so the turn result carries a **TAKE THE CITY** block whenever an
   enemy city's HP pool is empty: it names the unit in reach and the tile to move it to, and
   `take-the-city` fails while a city at 0 HP is still standing with one of our capture-capable
   units adjacent. Cavalry belonged on that list from the start and was not: live T122 a Heavy
   Chariot took Moscow at 0/200 while the scan reported no capture-capable unit on the tile.
   Two things this fixed in the adapter itself: an enemy city with **no garrison unit**
   in it used to answer `ERR:NO_ENEMY` to `attack` (so a broken city could not be hit at all and
   healed back while the army watched), and a move onto an enemy city tile went out without the
   ATTACK modifier, so the capture move was refused. `attack` and `move` now both resolve a city
   at the target tile through `Cities.GetCityInPlot`, and a unit ordered onto a 0 HP city
   takes it and reports `CITY TAKEN` — resolve it with `city_action` keep/raze.
   **The numbers behind that step, measured over the T103–T130 Russian war (game 13):** the
   capturing unit must **move** (attacking spends all remaining movement — T110 Moscow fell because
   the Chariot was ordered to move), it must be **adjacent at the start of the turn** (T129: a
   four-tile order with four movement points reached three tiles and the zone of control refused the
   last step; T117: a Warrior walked away from the capital for the same reason), and it must have
   **health** (T115: a 9 HP Horseman died taking a 0/200 city). A city at 0 HP heals ~20 a turn
   while it has a supply line, so a failed capture is a re-siege, not a delay. The same war's fire
   arithmetic, which decides how long a siege takes: an Archer does **9–11** against a city holding
   a CS 35 garrison and **35** against the same city ungarrisoned, while a **Catapult does 45–52
   either way** — so a garrisoned city is a Catapult job, and the cheapest way to remove the
   garrison bonus is to invite the sortie (T109: it left Moscow, and four shooters went from ~11 a
   shot to 95 in one turn). An ungarrisoned, wall-less city does **not retaliate against melee**
   (36 and 44 damage measured, 0 taken), and a siege fires only as many shots as its ring of
   distance-2 tiles allows, which mountains and `NO_LOS` reduce per tile.
   Two more rules compare what the enemy fields with what you have. **`match-their-melee`** fails
   while enemy melee within three tiles of the army is CS 35 or better and your front line is
   still Warrior/Spearman tier — an unupgraded line loses every trade with a Swordsman (35) or a
   Man-at-Arms (45), and the `BATTLE ASSESSMENT` block adds a `MATCHUP:` line naming the unit, the
   two combat strengths and the gold an upgrade costs. **`upgrade-the-siege`** fails during a war
   while a siege unit can be upgraded and the treasury covers it, because a Catapult does 45
   against a city where a Trebuchet does 55; the turn result carries an **UPGRADE AVAILABLE**
   block listing each unit, its upgrade target and its price. Massing attackers or doing the
   upgrade both clear these rules — trading one-for-one with a better unit does not.
   **Loyalty can take a city back with no battle at all**, so the turn result carries a
   **LOYALTY WARNING** while any of your cities is below 50 loyalty or losing loyalty: each city's
   pool, its per-turn pressure, **which way the game says it is going** and its
   turns-to-conversion figure — printed together, because that figure is a revolt countdown only
   while the city is *losing* loyalty and counts turns to a full pool while it gains (the game's
   own banner reads the two in one breath, `CityBannerManager.lua:2355-2358`) — the next owner
   while it drains, the governor in residence, the garrison on its tile and the game's own advice
   string. `hold-what-you-take`
   then fails while a low-loyalty city has **no governor in it and no unit on its tile** — the
   state Moscow was in when it revolted (captured T112, a Free City by T116, retaken T121 at a
   cost of nine attacks). Assign a governor (`assign_governor`) or garrison the tile; if the
   governor is needed at the front, say so in the diary.

## Looking things up: `search_knowledge`

You only know what you query, and part of what decides a turn is documentation, not game state —
how a city heals, what a support unit may do, what the doctrine says about screening.
`search_knowledge(query, k=5, doc=None)` searches a local index of the **game manual**, the
**directive and rule file**, `AGENTS.md`, `SETUP-WINDOWS.md` and the retrospectives, and answers
with the source path and line range plus a highlighted snippet. Read those lines (and cite them)
instead of paraphrasing from memory:

```
search_knowledge("city heals supply line zone of control")
search_knowledge("what can a battering ram do", doc="manual")
search_knowledge("城墙 修复", doc="manual")          # Chinese falls back to substring match
```

Build or refresh the index with `python .tools/kb.py index [--source <path>]` (it is per
checkout, and stale after the corpus changes). When a mechanic is in doubt, this is cheaper and
more honest than a guess — and the manual beats the doctrine when they disagree, because the
doctrine is only ever a summary of it.

## Diary

The diary is your persistent memory across sessions. When context compacts or you return to a game, `get_diary` is how you reconstruct where you were and why you made the decisions you did. Entries with specific details — unit names, coordinates, yield numbers, reasoning — are far more useful to your future self than brief summaries.

Reflections are recorded **before** AI processing begins — write what YOU observed and did this turn. Anything that surfaces after `end_turn` (a diplomacy proposal, AI units entering your territory, events in the turn result) belongs in the **next** turn's diary, not this one.

Five reflection fields each turn (all required, non-empty):
- **tactical**: What happened — specific units, tiles, outcomes.
- **strategic**: Standings vs rivals — yields, city count, victory path viability with numbers.
- **tooling**: Tool issues observed, or "No issues".
- **planning**: Concrete actions for the next 5-10 turns — specific builds, moves, research targets with turn estimates.
- **hypothesis**: Specific predictions — attack timing, milestone turns, biggest risks.

## Strategic Checkpoints

Periodic checks worth doing regularly. The game doesn't surface most of this proactively.

### Around every 10 turns:
- **The `end_turn` result carries a `10-TURN REVIEW`** — the MCP measures the window
  (what the last 10 turns bought, per-turn rates), quotes your own plan and prediction from
  10 turns earlier back at you, lists the assault prerequisites the directive requires
  against the units you actually have, flags idle district slots and the gold/turn carrying
  limit, and projects the current rates forward. **Answer its three questions in that turn's
  diary**: (1) was the window efficient, with numbers; (2) which prerequisite for the next
  goal is in place and which is missing; (3) does the planned completion turn still hold,
  and if not, what changes. Ten flat turns are invisible turn by turn — this is where they
  show up.
- `get_empire_resources` — unimproved luxuries and nearby strategics
- Surplus luxuries: duplicates beyond 1 copy provide zero amenity benefit. Trade them via `propose_trade` for GPT, strategic resources, or luxury types you don't own (each new type = +1 amenity to 4 cities). Even 5 GPT per surplus luxury adds up over 30 turns. Use `mode="test"` to check what the AI will accept before sending.
- Gold/faith balance: if either is accumulating with no plan, spend it — `purchase_item`, `purchase_tile`, `patronize_great_person`
- City count vs time in game — if expansion is behind, a settler tends to be the highest-leverage production choice
- `get_trade_routes` — check for idle routes; idle routes are free yields going uncollected
- Government tier — `change_government` when a new tier unlocks (free the first time)
- Era score vs thresholds — shown in `get_game_overview`; a Dark Age is recoverable but costly
- Great People — `get_great_people`; rivals will recruit what you don't

### Around every 20 turns:
- `get_diplomacy` — delegations to new civs, friendships with Friendly civs, alliances if eligible
- `get_victory_progress` — check all 6 victory types, not just your own path
- `get_religion_spread` — religious victory is invisible without active checking; a rival with majority in most civs is a serious threat

### Around every 30 turns:
- `get_strategic_map` — fog per city + unclaimed resources
- `get_global_settle_advisor` — best remaining settle sites
- Wonder scan: `get_city_production` in your best city — wonders that align with your victory path are worth considering
- Victory path check: is your chosen path still viable? Is any rival close to winning something you haven't been tracking?
- Civ kit check: are you building/using your unique units, buildings, or improvements? If not, you're playing a generic civ and giving up your structural advantage. The unique unit often requires a specific tech — if that tech isn't on your current research path, that's a problem.

## Military tactics, by decision

`prompts/tactics/` holds eight files, one per decision, written for the advisors (files 1-7 for
`military-map`, file 8 for `economy-cities`; their prompts name which to read when). Read the
matching one before improvising:

| File | 主题 |
|---|---|
| `tactics/01-unit-production.md` | 部队的生产策略 — the assault establishment, what to build first, what to buy |
| `tactics/02-contact-on-discovery.md` | 发现敌人时的行动 — assess, counter unit, mass or bypass |
| `tactics/03-under-attack.md` | 被攻击时的行动 — assess, mass, annihilate; the withdrawal cases |
| `tactics/04-staging-out-of-range.md` | 攻城前在敌射程外集结 — rally point choice, contact on the march, when to advance |
| `tactics/05-formation-and-screening.md` | 攻城前站位 — screen in front, siege behind at range 2 |
| `tactics/06-assault-composition-and-fire.md` | 开打后的搭配与火力 — order of work, concentration, when to break off |
| `tactics/07-pre-war-analysis.md` | 战前分析 — 能不能打、打谁、几回合、损失多大、打完守不守得住；**蛮族营地也是它的目标**（camp gates：CAMP/GUARD/FORCE/GROUND/WORTH/HOLD/GO） |
| `tactics/08-war-and-the-home-front.md` | 战时内政 — one war city, everything else compounds; gold/turn against the +10 floor |

**Before a war, file 7 comes first, and its own first step is reconnaissance** — Gate 0 is "a
candidate city is actually visible". An army in the right shape with every enemy city still in fog
has no pre-war analysis to make; send the scout and the fastest cavalry, then run the gates. **File 7
has two target classes**: an enemy city (a war) and a barbarian camp (a raid — the camp is a target of
that same analysis, with six camp gates instead of the city's five).

## Strategic Patterns

### Moving Civilians
Before moving a builder, settler, or trader to a new tile, `get_map_area` (radius 2) around the destination is worth the query. Civilians have zero combat strength — a single barbarian scout captures them. The cost of losing a builder (5-7 turns of production + charges) is almost always worse than taking one extra turn to check or escort.

**Water is a wall until `CIVIC`-era tech, and city-state land is a wall even when we are its suzerain.** Two measured movement refusals from the T92–T93 turns of the live replay, both of which look like tool failures and are not:
- **A land unit cannot embark without `TECH_SHIPBUILDING`** — the adapter answers "water tile - land units need Shipbuilding tech to embark", and it blocked five scout orders in two turns. A strait is impassable, an island is unreachable, and a "dark map" may simply be ocean: route scouts along the coast, and do not read the refusal as a hang or a bug.
- **A tile owned by a city-state refused our scout with "need suzerainty or Open Borders" while `get_city_states` listed us as Suzerain with 5 envoys.** Whatever the cause, the practical rule is the same as for a foreign unit parked in a lane: route around it and say so, rather than assuming suzerainty grants passage.

Hills cost 2 movement, forests/jungles cost 2, and they stack (forest-hills = 3+). A settler or builder with 2 base moves arriving on forest-hills uses all movement and can't act until next turn. Route through flat terrain when possible, or plan to arrive one turn early.

`get_pathing_estimate(unit_id, target_x, target_y)` estimates how many turns a unit needs to reach a destination, using the game's actual pathfinding. Use it before committing units to long marches.

### Builder Management
Idle builders are wasted production. `get_builder_tasks` shows all tiles needing improvements across your empire, prioritized (URGENT > HIGH > NORMAL), with the nearest idle builder for each task. Call it once per turn during the builder phase, then dispatch builders top-down by priority.

Don't skip builders that are 3-4 tiles from a task — a few turns of walking is better than sitting idle forever. For long-distance dispatches, use `get_pathing_estimate` to verify the route. Map tiles now show movement cost (`[mv:2]`, `[mv:3]`) and road presence — route builders along roads when possible.

After context compaction, call `get_builder_tasks` again to reconstruct your builder situation. The tool provides a fresh snapshot — no need to remember previous assignments.

### Spending Gold & Faith
Gold and faith sitting idle lose value over time. `purchase_item(city_id, item_type, item_name)` buys units/buildings instantly with gold (or faith via `yield_type="YIELD_FAITH"`). `purchase_tile(city_id, x, y)` buys a specific tile. `patronize_great_person` buys a GP outright. If you're saving, name the item and the turn — otherwise, deploy it.

### Expansion
Each city multiplies your districts, yields, and Great Person generation. The gap between a 3-city and 5-city empire by the Medieval era is hard to recover from. If city count is lagging, a settler is typically the highest-impact production choice — more so than most infrastructure in existing cities. Check loyalty before settling: negative-loyalty sites near rivals need a governor assigned immediately via `assign_governor(governor_type, city_id)` or they'll flip.

### Growth
Stagnant cities fall behind exponentially. If any city has food surplus ≤ 0, that's worth fixing this turn (Farm, Granary, domestic Trade Route, or `set_city_focus(city_id, "FOOD")`). Turns-to-growth over 15 is a signal the city needs food infrastructure.

### Exploration
You can't settle what you can't see, and you can't counter threats you don't know exist. A scout set to `automate` is one of the best investments in the early game. If a scout is lost or stuck, replacing it early keeps the information flow going.

### Diplomacy
Diplomacy generates yield: each alliance +1 favor/turn per alliance level, each suzerainty +1 favor/turn. Government tier also gives favor. This compounds. Friendships don't give favor directly but enable alliances (which do). Delegations (25g) are cheap on first meeting. Friendships open up when a civ is Friendly. Alliances require friendship (30+ turns) and Diplomatic Service civic. Embassies are available once Writing is researched.

If favor is accumulating above 100 with no World Congress imminent, it's worth thinking about whether it could be better deployed in trade or alliance building.

### War Declaration
War declarations take effect for diplomacy immediately but the **combat engine does not sync until the next turn**. After declaring war via `send_diplomatic_action`, units cannot attack the new enemy until the following turn. Plan accordingly: declare war on turn N, position units adjacent to targets, then attack on turn N+1. Do not reload or retry if attacks return `NO_ENEMY` on the declaration turn — this is expected behavior.

### Wartime
During war, keeping a military unit garrisoned in or near each city is worth the tradeoff against offensive strength. Cities with walls can fire at enemies via `city_action(city_id, "attack", target_x, target_y)` (range 2). Cities that fall are expensive to recover — when you capture a city, `city_action` with `keep`, `raze`, or `liberate_founder`/`liberate_previous` resolves the decision. If your military strength is significantly below an enemy's and you're not making progress, `propose_peace(player_id)` — available after a 10-turn cooldown — is usually better than a war of attrition while the rest of the map moves on.

### Military Readiness
Check rival military strength in `get_diplomacy` periodically. A neighbor at 2x+ your strength who isn't a friend or ally is a risk worth taking seriously. Minimum useful peacetime: 1 garrison per city plus a mobile unit. Units become progressively weaker relative to rivals if not upgraded (Slinger→Archer with Archery, Warrior→Swordsman with Iron Working) — use `upgrade_unit`.

### Barbarian Camps
Camps upgrade with the era — an Ancient-era camp spawns Warriors; the same camp in the Medieval era spawns Man-at-Arms. Clearing a camp within a few turns of finding it is almost always easier than fighting the units it produces over many turns.

**A camp is a `tactics/07` target, and it is destroyed by force** (human instruction, 2026-09-26; this replaces the earlier "do not clear camps" rule, under which a camp was valued only as a pool of units for the leader ability). A camp has **no HP, no walls and no garrison bonus** — one military unit **moving onto its tile** destroys it — so the analysis is about the guard, not the camp: count every barbarian within two tiles with its class and HP, read the camp tile's terrain and what the last step costs in movement, pick **two** attackers with the counter unit plus an unspent unit to walk in, confirm the walk-in starts from a tile we already hold, weigh gold/era score/the `CIVIC_MILITARY_TRADITION` inspiration (its boost is "clear a barbarian camp") against the units pulled off the plan, and say which city gives up its garrison. **Locate the camp from the map every time** — a camp can be cleared by someone else and respawn nearby, and a coordinate copied from an old diary has already been wrong once (T65's note said (60,30); the T83 map read put the camp at (60,29)). Barbarian **Spearmen are anti-cavalry** — ranged fire plus a melee walk-in, never cavalry into spears; a Scout, Builder or Trader sent at a camp is captured instead. Report `CAMP / GUARD / FORCE / GROUND / WORTH / HOLD / CONVERT / GO`.

The leader ability 三十六计 Three-Six Stratagems converts an adjacent barbarian, but only from the game UI. So report any barbarian standing next to one of our melee units whose type is worth converting **before** the raid — then clear the camp anyway.

**The raid has a one-command entry point:** `scripts\run-dsh-headless.ps1 -TaskFile prompts\tasks\clear-the-camp.zh.txt` (English: `clear-the-camp.en.txt`). It plays one raid end to end — status check, the six camp gates, the force, the walk-in, the report — without declaring war or changing the development plan.

**A camp is now visible to the rules, and the rule for it ships staged.** `end_turn` computes `camps_within_3` (via `_camps_within_3`, two lines of Python over the existing `get_map_area` — a camp is a tile improvement, `IMPROVEMENT_BARBARIAN_CAMP`, so no new Lua was needed), and the rule `answer-the-camp` lives in `prompts/checks/pending/answer-the-camp.md`, **not** in the live file. That is deliberate: the rule file is re-read every turn but the *metric set* lives in the running MCP server's memory, and `turn_checks.evaluate` raises on an unknown metric — so a live rule naming a metric an older server does not compute reports itself `un-evaluable` every turn, unfixable until that process restarts. Cut the staged block into `turn-checks.md` when the MCP server next starts. (The evaluator also evaluates both sides of `and` eagerly, so no gate ordering can short-circuit around a missing key.)

### Religion
Religious victory is the easiest win condition to miss because it produces no notifications and unfolds slowly. `get_religion_spread` shows the picture. If a rival religion reaches majority in most civs, the window for a response narrows quickly. Religious units bought from a city carry **that city's majority religion** — buy them from cities where your own religion is majority, not a converted city.

To found a religion: build a Holy Site → earn a Great Prophet → `get_religion_beliefs()` to see available beliefs → `found_religion(name, beliefs)`. The Great Prophet pool fills early (roughly half the major civs).

Trade routes spread the origin city's religion to the destination — worth factoring into routing decisions if conversion pressure is a concern.

### Victory Path Viability
Some paths close. It's worth checking periodically via `get_victory_progress`:

- **Science**: Campuses → Universities → Spaceport → 4 space projects. Research Alliances and Great Scientists accelerate.
- **Culture**: Tourism (offense) vs rival domestic tourists (defense). Theater Squares, Great Works, Wonders, Open Borders (+25%), Trade Routes (+25%). Late-game: National Parks, Rock Bands, Seaside Resorts.
- **Religious**: Requires a founded religion (Great Prophet pool fills early). Missionaries spread; Apostles fight theological combat (killing = 250 pressure in 10-tile radius). Buy religious units only from cities where your religion is majority.
- **Diplomatic**: 20 DVP. World Congress resolutions, scored competitions, wonders. Favor from government tier, alliances, suzerainties. If a DVP-stripping resolution targets you, vote Option B on yourself (net 0 vs -2).

## Combat Quick Reference

| Unit | CS | RS | Range |
|------|----|----|-------|
| Warrior | 20 | — | — |
| Slinger | 5 | 15 | 1 |
| Archer | 25 | 25 | 2 |
| Barbarian Warrior | 20 | — | — |

- Ranged attacks don't take damage; melee attacks do
- Forests/mountains block ranged LOS — targets with blocked LOS are filtered from `get_units` attack lists
- Fortified units: +4 defense, heal each turn
- Combat estimates include promotion CS bonuses, flanking (+2 per adjacent friendly to defender), support (+2 per defender's adjacent friendly), and forest/jungle defense (+3)

## Unit Actions Reference

| Action | Effect | Notes |
|--------|--------|-------|
| `move` | Move to tile | target_x, target_y required |
| `attack` | Attack enemy | Shows damage estimate; melee/ranged auto-detected |
| `condemn` | Destroy an adjacent enemy religious unit (Condemn Heretic) | A game **command**, not an attack (`unit_action(action="condemn")`); the engine picks the adjacent Missionary/Apostle/Inquisitor, so the reply names every candidate first. **The game requires a war declaration** (`LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION`), so a friend's missionary cannot be condemned by anyone — a peace-time target comes back `ERR:REQUIRES_WAR`. Added 2026-09-26 for task 008. |
| `fortify` | +4 defense, heals | Military only |
| `heal` | Fortify until full HP | Auto-wakes at full HP |
| `alert` | Sleep, wake on enemy | Sentry use |
| `sleep` | Sleep indefinitely | Manual wake required |
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

Common improvements: `IMPROVEMENT_FARM`, `IMPROVEMENT_MINE`, `IMPROVEMENT_QUARRY`, `IMPROVEMENT_PLANTATION`, `IMPROVEMENT_PASTURE`, `IMPROVEMENT_CAMP`, `IMPROVEMENT_FISHING_BOATS`, `IMPROVEMENT_LUMBER_MILL`

Feature removal: Forest, jungle, and marsh tiles block most improvements (e.g. Farm). Use `remove_feature` to chop/harvest the feature first, then `improve` to build. Lumber Mill and Camp work on forest/jungle without removal. Check `valid_improvements` in `get_units` output — if FARM isn't listed on a tile you expect it, the tile likely has a blocking feature.

Builders repair tile improvements. Pillaged **district buildings** (Workshop, Arena, etc.) are repaired via `set_city_production`.

`get_cities` shows unimproved resource tiles and pillaged improvements/districts per city — use this to prioritize builder work without needing to scan `get_map_area` manually.

Military Engineers (requires Encampment + Armory): `build_route` builds a railroad on the current tile (no charges consumed; costs 1 Iron + 1 Coal per tile). `improve` with `IMPROVEMENT_FORT` or `IMPROVEMENT_AIRSTRIP` uses charges. Building a railroad consumes all movement — one tile per engineer per turn.

| Other unit tools | |
|--------|--------|
| `skip_remaining_units` | Skip all units with remaining moves (useful after diplomacy) |
| `upgrade_unit(unit_id)` | Upgrade to next type (requires tech + resources + gold) |

## End Turn Blockers

`end_turn` resolves blockers before advancing. If it returns a blocker:
- **Units**: unmoved units need orders (move / skip / fortify)
- **Production**: city queue empty — set new production
- **Research/Civic**: completed — choose next
- **Governor**: point available — `get_governors` → `appoint_governor` / `assign_governor(governor_type, city_id)` / `promote_governor(governor_type, promotion_type)`
- **Promotion**: unit has XP — `get_unit_promotions` → `promote_unit`. **A promotion consumes the
  unit's whole turn** (manual, `EXPENDING XPS`), so promote after it has attacked, or while it is
  out of range or healing — never instead of an attack. Match it to the job: melee taking cities
  want the anti-garrison/damage line, ranged want the ranged-strength line.
- **Policy Slot**: empty — `get_policies` → `set_policies`
- **Pantheon/Religion**: faith threshold reached — `get_pantheon_beliefs` → `choose_pantheon`; for founding: `get_religion_beliefs` → `found_religion`
- **Envoys**: tokens available — `get_city_states` → `send_envoy`
- **Dedication**: new era — `get_dedications` → `choose_dedication`
- **City Capture**: conquered or disloyal city — `city_action(city_id, "keep"/"raze"/"liberate_founder"/"liberate_previous")`
- Move responses show the **target tile**, not arrival position (async pathfinding)

## Diplomacy

**Reactive (AI-initiated):** AI encounters block turn progression. Use `get_pending_diplomacy` to check for open sessions, then `respond_to_diplomacy` (POSITIVE/NEGATIVE, 2-3 rounds). Diplomacy sessions do not affect unit movement or orders — continue commanding units normally afterward.

**Proactive:**
- `send_diplomatic_action(action="DIPLOMATIC_DELEGATION")` — 25g, worth sending on first meeting
- `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` — requires Friendly status
- `send_diplomatic_action(action="RESIDENT_EMBASSY")` — requires Writing tech
- `form_alliance(player_id, type)` — types: MILITARY/RESEARCH/CULTURAL/ECONOMIC/RELIGIOUS; requires friendship 30t + Diplomatic Service civic
- `propose_trade(player_id, ...)` — trade gold/GPT/resources/favor/open borders/cities. Use `mode="test"` first to see the AI's counter-offer without committing, then `mode="send"` to finalize. Cities use `city_id` from `get_trade_options`.
- `propose_peace(player_id)` — white peace; 10t war cooldown required
- `get_trade_options(other_player_id)` — see what a civ has available to trade (gold, resources, favor, cities, agreements)
- `get_pending_trades` — check incoming trade offers; `respond_to_trade(player_id, accept)` to accept/reject
- Check `get_diplomacy` for defensive pacts before declaring war
- `get_diplomacy` shows leader agendas — historical agendas are always visible; random agendas require Secret diplomatic visibility (spy in their capital or alliance). Use agendas to predict AI behavior and avoid relationship penalties.

**Espionage:** `get_spies` → `spy_action(spy_id, action, ...)`. Actions: `travel` to a city first, then run operations (steal tech, neutralize governors, etc.). Offensive missions only work after the spy arrives.

**City-states:** `get_city_states` → `send_envoy`. Suzerainty = +1 favor/turn. Types: Scientific/Industrial/Trade/Cultural/Religious/Militaristic.

**Diplomatic Favor:** earned from government tier (base +1, scales with tier), alliances (+1/t per level), suzerainties (+1/t). Spend in World Congress for Diplomatic Victory Points.

## Production & Research

Wonders — high-production cities can slot these between infrastructure. Use `get_wonder_advisor(city_id, wonder_name)` for placement, then `set_city_production` with target_x/y. Science: Great Library, Oxford University, Kilwa Kisiwani. Culture: Chichen Itza, Forbidden City. General: Ancestral Hall, Pyramids.

**Research:** `get_tech_civics` sorts by turns ascending; items ≤ 2 turns are flagged `!! GRAB THIS` — cheap boosted techs are easy to miss and can unblock entire production chains.

**Purchasing:** `purchase_item(city_id, item_type, item_name)` — buy units or buildings instantly with gold (default) or faith (`yield_type="YIELD_FAITH"`). `get_city_production` shows purchasable items and costs.

**Tiles:** `get_purchasable_tiles(city_id)` → `purchase_tile(city_id, x, y)` — buy border tiles with gold for strategic resources or district placement.

## District Placement

Use `get_district_advisor(city_id, district_type)` for ranked tiles. Then `set_city_production` with target_x/y.

| District | Adjacency bonuses |
|----------|------------------|
| Campus | +1 per mountain, +1 per 2 jungles, +2 geothermal/reef |
| Holy Site | +1 per mountain, +1 per 2 forests, +2 natural wonder |
| Industrial Zone | +1 per mine/quarry, +2 aqueduct |
| Commercial Hub | +2 adjacent river, +2 harbor |
| Theater Square | +1 per wonder, +2 Entertainment Complex |
| Encampment | cannot be adjacent to city center |

## Trade Routes

- `get_trade_routes` — see all active routes and idle traders
- `get_trade_destinations(unit_id)` → available destinations
- `unit_action(action='trade_route', target_x, target_y)` → start route
- Domestic routes: food + production to new cities. International: gold.
- Capacity: 1 from Foreign Trade civic, +1 per Market/Lighthouse
- Idle routes are free yields going uncollected

## Great People

- `get_great_people` — candidates, recruitment progress, and costs
- `recruit_great_person(individual_id)` — recruit with accumulated GP points (check `[CAN RECRUIT]`)
- `patronize_great_person(individual_id)` — buy instantly with gold or faith
- `reject_great_person(individual_id)` — pass, advance to next candidate in that class
- Rivals will recruit what you pass on — recruiting quickly tends to be worth it
- **Great Generals and Great Admirals are the exception to activating.** The aura is
  what they are worth: +5 combat strength and +1 movement to land units within range
  (naval units for an Admiral), granted **passively while the unit is alive**.
  `activate` is a *retirement* — it consumes the unit and pays out a one-off.
  `get_great_people` prints both: keep the general with the army and do not activate
  it unless that one-off is what you actually want. Activating a general on the turn
  it is recruited throws away the aura for the rest of the game.
- For every other class, move the GP to its matching completed district and
  `unit_action(action='activate')`
- If activation fails, the error message includes the requirements (district type, buildings needed)
- Don't delete GPs — they show 0 builder charges but that's a different system; they're not consumed until activated (except a general or admiral, which activation retires)

## World Congress

WC fires synchronously inside `end_turn()` — register votes **before** calling end_turn.

**Voting flow:**
1. `get_world_congress()` — when `turns_until_next = 0`, WC fires this turn
2. Review resolutions (options A/B, target list, favor costs)
3. `queue_wc_votes(votes='[{"hash": H, "option": 1, "target": 0, "votes": N}]')`
4. `end_turn()` — handler fires, votes deploy, turn advances

- `hash`: from `get_world_congress`; `option`: 1=A / 2=B; `target`: player_id resolved to list index at runtime; `votes`: max to spend
- 1 free vote per resolution (costs nothing — worth casting)
- Extra votes cost 6/18/36/60/90/126... cumulative favor
- Keeping 50-100 favor in reserve between sessions provides flexibility for the next session
- DVP resolutions: read what each option actually awards before voting. Concentrate favor on the single most impactful resolution rather than spreading thin. Verify your vote blocks the rival, not accidentally helps them

## Victory Conditions

| Victory | Win Condition | Monitor Via |
|---------|---------------|-------------|
| Science | 4 space projects complete | `get_victory_progress` |
| Domination | Own all rival original capitals | military strength in `get_diplomacy` |
| Culture | Foreign tourists > every civ's domestic | tourism in `get_victory_progress` |
| Religious | Your religion majority in ALL civs | `get_religion_spread` regularly |
| Diplomatic | 20 diplomatic victory points | World Congress votes |
| Score | Highest score at turn limit | fallback |

All victories trigger immediately when the condition is met — they do not wait for a turn boundary or WC session. A rival reaching 20 DVP wins before your next turn. The only counter is stripping DVP at a World Congress *before* they reach 20.

`end_turn` runs a victory proximity scan every turn and a full snapshot every 10 turns. These warnings are the primary signal for invisible victories — worth paying attention to.

## Game Recovery

**Ask where the game is before touching anything:**
```
get_game_status   # not_running / starting / in_game / leader_screen / main_menu / loading / tuner_busy
```
It answers with the state, the turn, and a `NEXT:` line, so a recovery does not have to be
inferred from whichever call happened to fail. Two answers change what you do: `in_game`
means a game is already playable (nothing to launch or load), and `tuner_busy` means another
process holds the FireTuner connection — FireTuner serves exactly one, so no call from here
can work while that one lives. Waiting does not help: stop that process with
`scripts\civ6-clean.ps1`, or keep playing in its session.

**MCP autosaves:** `end_turn` automatically saves every turn as `0_MCP_NNNN` (last 5 kept). These are your primary recovery points.

**Two recovery traps, both measured on 2026-09-25 (five crashes/hangs in one session):**

1. **`0_MCP_NNNN` names collide across rolled-back branches, and a rollback does not delete the
   abandoned branch's files.** Loading `0_MCP_0122` by name silently loaded the *other* branch's
   position — same turn number, different board (18 units, two Trebuchets, no Moscow), so the turn
   check passed and only reading the units back caught it. **After any rollback, recover with the
   game's own per-session autosave, `AutoSave_NNNN`** (in `Saves/Single/auto`, OneDrive-redirected
   on Windows: `C:/Users/<user>/OneDrive/文档/My Games/Sid Meier's Civilization VI/Saves/Single/`),
   choosing the newest one at or before the lost turn by modification time. The save-list Lua probe
   (`.tools/probes/save-list.lua`) prints names, paths and times so the two can be told apart.
2. **A turn that will not advance is not necessarily a hang.** Twice it was the game waiting for a
   mouse: once parked on the leader screen after a load (the CONTINUE click was landing on the
   browser, because `_click` injects at screen coordinates and a fullscreen game must be in front —
   fixed by focusing first, `_bring_to_front`), and once behind a natural-disaster popup plus twenty
   `InvitePopup`s. **Read the screen (`.tools/whats-on-screen.py`) before restarting**, and try
   `dismiss_popup` before relaunching.

Launching from a shell may need full filesystem access: the game writes `%LOCALAPPDATA%\Firaxis
Games` and its OneDrive save directory on start, and a confined launch produces no process at all.

**Re-orient in one read: `scripts\orient.py`.** After a rollback (or any cold start) the rule is
"rebuild every fact from the game", and doing that through five separate reads is how one of them
gets skipped. One connection prints the game overview, units, cities, tech/civics, policies,
diplomacy (met civs only), resources, governors, trade routes, builder tasks, city-states,
victory/demographics, religion, great people, pantheon and notifications — compact by default,
`--full` for the raw dataclass dump, `--only a,b` to narrow, `--maps` for the narrated map.
Two companions: `scripts\turn-of-save.py "<path>"` prints the turn a save actually holds *before*
you load it (a manual save carries no turn in its name and the save parser cannot always read one
out of the file — the T59 rollback had to take the game's own filename on faith), and
`scripts\probe-tile.py x,y` prints the raw tile record (terrain, feature, resource, owner, units),
which is what settled that (58,30) held no *visible* resource at all.

**Unattended development turns: `scripts\auto-turns.py --turns N`.** It dispatches Builders along
the task list, keeps every city's queue filled from a per-city plan, advances research and civics
from a priority list, takes the pantheon/dedication/governor offers, buys a Builder above
`--buy-at` gold, and writes the same diary rows the operator writes (with factual, not
interpretive, reflections). It **never** attacks, declares war, clears a barbarian camp, moves
toward an enemy, or touches diplomacy — and it stops and hands back the moment a non-barbarian
enemy is within three tiles or a war starts, which is where the tactics files apply. Run
`--dry-run` first: it prints the orders it would issue and touches nothing.

**Load by name** (preferred — no `list_saves` needed):
```
load_game_save("0_MCP_0079")  # find it in the game's own save list and load it
get_game_overview              # verify load
```
It works from the main menu as well as in-game: with no game loaded the same two calls run in
the game's own FrontEnd load-screen state (`LoadGameMenu`), so nothing has to be clicked and no
window has to be in front. It then lands the load itself — waits for the leader screen, clicks
CONTINUE, and reads the turn back — so the reply names the turn actually loaded and a wrong one
comes back as `WARNING: the game reports turn N, but '<save>' holds turn M`. OCR menu navigation
is the fallback for a save the game's list does not carry.

**When the game hangs** (AI turn loop):
```
restart_and_load("0_MCP_NNNN")   # kill + relaunch + load (~90s)
get_game_overview                 # verify load
```

**Turn regression detection:** If you accidentally load a wrong save (e.g. the T1 scenario save instead of your autosave), `end_turn` will emit a CRITICAL warning with the correct autosave name to reload.

Other tools: `list_saves`, `load_save(index)`, `kill_game`, `launch_game`, `load_save_from_menu(name)`.
Save names omit the extension: `"AutoSave_0221"`. Writing `"AutoSave_0221.Civ6Save"` is accepted
too, and stripped, because the game's own save list carries it.

**One session at a time.** `kill_game` and `restart_and_load` refuse while another session is
playing (they name the pid holding the FireTuner connection or writing a recent heartbeat), so
a recovery cannot throw away a position someone else is mid-turn in. Pass `force=True` only
when you know that session is dead. Loading a save the game is already sitting on is not a
load: `load_game_save` answers "Already loaded" from the current turn instead of clicking
through a main menu that is not on screen.
