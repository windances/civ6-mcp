---
title: Temporary-task record — the task prose that used to sit in AGENTS.md
---

Moved out of `AGENTS.md` on 2026-09-26, when that section was cut back to the procedure alone.
`AGENTS.md` now says only how to find the temporary tasks, how to read one, how to tell which are in
force and where the detail lives, and names no task's content. Nothing here was reworded: this is that
section as it stood at **T178**, with the twelve retired tasks, the three tasks that were in force that
turn and the Russian war's measurements. **It is a record, not an instruction** — the tasks are the
files in `prompts/tasks/tmp/`, the live register is `prompts/tasks/tmp/current_tasks.md`, the procedure
is `AGENTS.md`, and the mechanics these tasks measured live in the directive and `prompts/tactics/`.

## The section as it stood at T178 (verbatim)

**IN FORCE NOW — read each of these files before planning the turn:**
`013-upgrade-and-scout.md`, `014-destroy-missionaries-everywhere.md`, `016-destroy-yerevan.md`.
(**015-yerevan-pre-war-analysis** was **done at T177**: Yerevan is at **(63,37)**, pop **10** read from
the city-state's own trade screen, an **ARCHER** garrison and a Trader on the city tile, a HORSEMAN at
(63,38) and a WARRIOR at (63,39), walls **unreadable at peace** — and the verdict is **`leave it
alone`**, because Egypt already holds its suzerainty, one envoy token contests it more cheaply than an
army, and a city-state advances Domination by nothing. `001-clear-the-camp` was retired at T84, `003-two-scouts-explore` at T93, `002-focus-fire-scouts`
expired at T95, `004-city-near-iron` was **done at T101** — 成都 stands at (60,31) with the iron at
(60,32) inside its first ring — `006-prepare-for-russia` was retired at **T110**, its assault
establishment complete on paper but the iron still `0/50` and the target city never read in its four
numbers, and `005-city-near-copper` was retired **EXPIRED at T115** with no copper city founded: the
site at (50,33) was a bonus tile worth about +2 gold and never justified a sixth city, which is
exactly what that file said to do if the ranking came out badly. Then the war ended: at **T165**
`007-destroy-russia` was **done** (Russia is eliminated), `008-destroy-missionaries` was **done with a
zero count** (no hostile religious unit anywhere we could see, both `condemn` refusals recorded) and
`012-novgorod-pre-war-analysis` was **done** (诺夫哥罗德 read in its four numbers and taken); at
**T166** `010-rescue-chengdu` and `011-destroy-chengdu-ring` were both **done** — 成都 reads walls
100/100 with a Warrior garrison, a radius-3 sweep holds **no hostile unit at all**, and the pillaged
IRON mine is repaired; and at **T168** `009-city-near-niter` was **done** — 胶东 (54,21) owns the
NITER at (53,21) and a Builder mined it. All **twelve** sit in `prompts/tasks/tmp/done/` with the turn
in their name. **This list and that directory are checked against each other** by
`tests/test_temp_tasks.py`, so a retirement that is not recorded here goes red instead of quietly
staying in force.)

**The Russian war is over (T165) and the conquest task is retired with it.** Russia is eliminated:
诺夫哥罗德 (61,42) was its last city, taken at T165, and the five cities we took — 阿斯特拉罕 (54,40),
沃罗涅什 (50,37), 圣彼得堡 (56,43, its former capital), 喀山 (58,39) and 诺夫哥罗德 — are all resolved
with `city_action keep` and all garrisoned. The **file** is gone; the **directive's conquest rules are
not** — no peace with anyone while a war stands, one garrison per captured city, and the same three
phases (战前分析 `tactics/07`, 集结 `tactics/04`, 执行 `tactics/05`/`06`) before the next war. What this
war measured, so the next one does not have to rediscover it:

- **The Trebuchet is the wall-breaker — not the melee, and not the Battering Ram.** One Trebuchet shot
  at 诺夫哥罗德 took the walls `92 -> 34` (**58 points**), while a Man-at-Arms standing on a tile
  adjacent to the city, with the Ram on another adjacent tile, did **8** on its first hit — the bare
  number the doctrine quotes as the no-Ram case. The Ram's text says "when adjacent to a city, attacking
  melee units do full damage to Walls"; it did not apply from `(61,41)` with the Ram at `(60,43)`, so
  **stack it with the attacker and re-measure before trusting it**. Once the walls read 0 the same melee
  hits took **23–48** off the HP pool.
- **A melee attack that reduces a city to 0 captures it outright.** No separate walk-in move is needed:
  the attack's own estimate read `CITY_CENTER (CS:0, HP:-156)` and the city was ours, with the attacker
  standing on its tile (the follow-up `move` answered `STACKING_CONFLICT ... already on (61,42)`).
- **A combat reply that repeats byte-identically is a phantom attack.** The adapter kept offering a
  legal attack the engine had stopped accepting; a `move` onto the city tile settled it by answering
  `CAPTURE_MOVE|BLOCKED`. Verify with a different call instead of repeating the same one.
- **`get_diplomacy`'s `walls N` is a static maximum.** It still read `walls 100` while the walls stood
  at 0. Read walls and HP from a combat result line or from `SIEGE PROGRESS`, never from that line.
- **`get_staging_plan` will post a Crouching Tiger at a d2 tile labelled "short-ranged".** The Tiger has
  **Range 1** and cannot fire from there; it needs a d1 tile it can reach with a movement point spare.

**008 rides along with 007, and both are now retired** — kept here only for the verb: destroying
missionaries is lane-clearing, not a second war. `unit_action(action="condemn")` implements the game's own
`UNITCOMMAND_CONDEMN_HERETIC` and **the game itself requires a war declaration** for it, so a civ we are
at peace with cannot be condemned by tool or human (`ERR:REQUIRES_WAR`). Both attempts in this game
returned `ERR:NO_RELIGIOUS_TARGET`, and it was **an adjacency fact, not a tool failure**: the unit had to
be within one tile of the missionary, and it was two. Record the reply either way in the diary's
`tooling` line.

**009 retired at T168** and was the cleanest of the twelve: 胶东 (54,21) was founded with the NITER at
**(53,21)** inside its border, 上海's Builder walked there, and `IMPROVEMENT_MINE` went in — no feature
to clear first, no escort needed, and no delay to the war it was told to stay out of. The one lesson it
carries is the one that let it work: **its expiry was written from the queue, not the calendar**, which
is exactly why 005 expired unused and this one closed early.

**013 is the peacetime task** (human instruction 2026-09-26: 攒钱升级部队，侦察兵找下一个战前分析目标),
and it is one file because the two halves answer to each other: the gold is earmarked for a named
upgrade list, and the scouts go find the target that list exists for. **The list is exact** — two
Man-at-Arms → MUSKETMAN at 85g each, three Trebuchets → BOMBARD at 85g each (a Trebuchet shot took
诺夫哥罗德's walls `92 -> 34`, so the next tier of that tool is the empire's cheapest damage), and the
Scout → SKIRMISHER at 125g last and droppable. **The Siege Tower is not on the list even though the
game offers it for 40g**: 不用锤，用投石车 forbids it, and the file says so in its `overrides:` line. It
holds a **100g floor** so an emergency purchase stays possible, which is why 425g of war upgrades runs
to ~T195 at +15.3g/turn. The recon half is `tactics/07` **Step 0** — `get_deal_options` on both met
civs first (no unit moves), then the two Scouts and the Knight into the fog that hides **four unmet
civilisations** and all five cities of the civ that has denounced us — and it ends in either a
candidate read in its four numbers or an explicit `no candidate visible` report. It authorizes no
declaration, no peace and no raid; it produces the *input* to the next 战前分析.

**014 is the missionary task, map-wide** (human instruction 2026-09-26: 全域消灭传教士), and it
generalises the retired 008 from "our territory and the army's roads" to **the whole map** — while
keeping 008's measured legality in front of the reader, because that is what decides the shape of the
task: at peace a religious unit **cannot be touched at all** (`condemn` answers `ERR:REQUIRES_WAR`,
`attack` answers `ERR:NOT_AT_WAR`, a city strike returns `NO_ENEMY`), and `condemn` needs an
**adjacent** military unit, so two tiles away is `ERR:NO_RELIGIOUS_TARGET` — the two attempts this game
made were adjacency facts, not tool failures. The kill is therefore a **war-time** action and the
peacetime half is the sweep: a religious unit is `FORMATION_CLASS_RELIGIOUS` with `Combat = 0`, so every
contact metric and every rule is blind to it and **the tile's unit list in `get_map_area` is the only
detector**. It ends in `count == 0` with the tiles swept, or in an expiry that says the owners were all
at peace; the chase, when a war comes, is `get_staging_plan(kill_x, kill_y)`'s mobile-only `KILL`
bucket, and the thing worth more than any single kill is the **faith source** — pillage the Holy Site
that produces it.

**016 is the assault on Yerevan itself** (human instruction 2026-09-26: 战前集结，消灭埃里温), and it is
the one instruction in this game that **overrides a completed analysis**: 015 read the city in its four
numbers and returned `leave it alone`, and the human has said otherwise — so the `overrides:` line names
015's verdict **and** the directive's city-state rule (`directive.md:497-499`) **for this one city**, the
declaration is authorized on **player 8 and nothing else** (not Egypt, which holds the suzerainty, not a
second city-state, not a camp), and the diary must record the human instruction as the **reason of
record** rather than inventing a strategic one. What it carries: `get_staging_plan(63,37)` with **three
overrides** this map paid for (a Crouching Tiger posted at d2 is wrong — Range 1; a siege unit posted at
d1 is refused; `arrive T+n` does not know our own units jam the corridor, so **one move per call** and
re-read); the force already on the doorstep (2 Bombards, 1 Trebuchet — the third shooter is 013's first
upgrade at 85g — 2 Musketmen, a Knight, the Ram with its "stack it with the attacker" warning, a
Spearman, the Tiger, the Crossbowmen); **probe-then-train** on the walls, because a city-state's walls
are **unreadable at peace** and the wall number has to come from the first melee attack; declare, wait a
turn, then attack; the **Horseman at (63,38)** countered by anti-cavalry or ranged fire, because cavalry
reaches past the line; and the honest ledger — Egypt holds the suzerainty, so this removes the bonus from
the board for both of us rather than taking it, the grievances land with everyone who knows Yerevan, and
a city-state advances Domination by nothing. Its expiry is written from the queue (2–3 turns of assembly
plus the wall and pool phases), not from the calendar.

**015 is the pre-war analysis of Yerevan, with the scouts close in** (human instruction 2026-09-26:
战前分析埃里温，侦察兵贴近侦察). Yerevan is **player 8, Religious**, and the one fact nobody has is its own
tile: the diary records what its *levy* did to us — three Man-at-Arms on 成都's ring, our IRON mine
pillaged, and its units fighting at 喀山, last seen at **(62,38)/(62,39)** on T165 — but no row anywhere
gives the city's `(x,y)`. So this is `tactics/07` **Step 0** in its pure form, and the recon starts
where its units were. Its suzerain slot was **empty at T165** (it read `Suzerain: 俄罗斯` at T163, and
Russia's elimination cleared it) with **0 envoys**, so one token would take it — which is exactly what
the verdict has to weigh, because the directive says a city-state is **not** a conquest target and is
attacked only for a **stated reason** (a rival about to take the suzerainty, or a chokepoint/resource
the next war needs): `leave it alone` is as much a result as a reason is. It suspends 011's "no attack
on Yerevan itself" **for reconnaissance only** — scouts may stand adjacent, `get_deal_options(8)` may be
used — and authorizes no declaration, no attack, no gold. Two measured traps are written into it: a
city-state's border refuses passage **even to its suzerain** (T92–T93), so 贴近侦察 means reading
`get_map_area` from the nearest tile we *can* occupy; and a city-state's **walls may be unreadable at
peace** (`get_city_states` gives type and envoys, `get_diplomacy` lists civilisations not city-states),
so the honest report says which of the four numbers came from a result line and which one has to wait
for a probe attack.

**010 and 011 retired together at T166, and their one durable correction is a coordinate.** Both files
named **成都's IRON mine at (60,32)** as the pillaged tile; the tool proved otherwise — `repair` there
answered `NOT_PILLAGED`, and the map showed `(60,32)` intact with the pillage on **(61,32)**, the tile
the levied Man-at-Arms was standing on. The city's own row prints `!! PILLAGED TILES: MINE, 32` with the
**y coordinate only**, which is exactly how both files came to name the wrong hex; a tile-level read
settles it, and a y-only narration never should. What the raid itself taught: **the city's ranged strike
is the cheapest weapon in the empire** (43 damage, no retaliation, and it killed a levied Horseman and a
levied Man-at-Arms outright), **the Warrior never sorties** (a CS 20 attack into a CS 45 Man-at-Arms
reads `attacker likely dies`, and the garrison's job is to hold the tile for `hold-what-you-take`), and
**a hostile religious unit is not always removable** — `condemn` needs one tile of adjacency, not two,
and city strikes return `NO_ENEMY` against a Missionary. The ring emptied not because we cleared it but
because **Russia's destruction dissolved the Yerevan levy**, and we took Yerevan's suzerainty the turn
after: an enemy that is a city-state's proxy dies with the suzerain.

**012 is retired (T165) and what survives is the reading habit it carried.** The requirement it existed
to enforce still holds for any walled target: **read the target in its four numbers — garrison / walls /
HP pool / ring — from result lines, never from `get_diplomacy`** (whose `walls N` is a static maximum:
it still read `walls 100` while 诺夫哥罗德's walls stood at 0). Two further traps it named are now
confirmed: `get_staging_plan` will post a **Crouching Tiger** at a d2 tile labelled "short-ranged", and
the Tiger has **Range 1** and cannot fire from there at all; and **the pathfinder drifts west** — orders
for a Knight at (58,35) and a Trebuchet at (58,36) both resolved to tiles *west* of their start
((57,38) and (57,37)), the same signature as the T159 eight-order batch. The two blocks the file was
written for were indeed the broken ones: `SIEGE FIRE` speaks only once a shooter is inside range 2, and
`get_staging_plan`'s `arrive T+n` does not know that our own units jam the corridor.

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

## `018-take-alexandria` — done at T216

The file is `prompts/tasks/tmp/done/018-take-alexandria-done-T216.md`. It was the last temporary task in
force and the directory is now empty.

- **Its `done when:` held in full.** Alexandria is at **(72,36)** (read from the Egyptian city list at
  capture: `亚历山大 pop 11 (72,36) walls 200`), a unit stands on the tile — the Cavalry that took it,
  garrisoning it — and `get_victory_progress`'s DOMINATION block moved from `埃及: holds own capital` to
  **`埃及: CAPITAL LOST`**. That line, not the city's name, is the proof the city taken was the capital:
  it was, and Egypt is now down to one city (塞纳 (74,32) pop 5, walls 200).
- **The four numbers at war**: location (72,36); walls **200** static (T213 `get_diplomacy`); pool
  **199/200** after the first T215 volley; garrison **`UNIT_GREAT_WRITER`** — a non-combatant, and the
  only way to read it was our own attack lists, because the city tile itself printed `[fog]` in
  `get_map_area`; ring read at radius 3 (Government Plaza (71,36), Campus (71,37), Sphinxes, river, the
  NITER farm at (72,34)).
- **What the T216 volley measured**: Bombard #4325376 from (71,34) `walls 95/200`; Bombard #4980745 from
  (70,36) `walls 43/200`; Line Infantry #5111819 melee from (71,35) `walls 4/200`. **Walls and pool both
  fall to the same shots** — the pools moved in step (`city hp 162 -> 130 -> 94`), so a walled city is not
  a two-stage problem once three siege pieces bear on it.
- **A melee attack that zeroes the pool captures outright** — this is the second time the game has said
  so (the first was 诺夫哥罗德 at T165). The Cavalry #5177368 attacked from (73,36) at d1 and the city
  was ours, with the game reporting `夺得外国首都` / `首都被占领 at (72,36)` and the Cavalry standing on
  the tile at 62/100. **No separate walk-in move was issued and none was needed.**
- **`get_staging_plan` works again** — the T213 crash (`invalid literal for int() with base 10: '1.5'`)
  did not recur once no unit carried a fractional movement point. It assigned distinct ring tiles, named
  the supply hexes (`4/6 cut`) and warned that a shooter which spends its movement cannot fire. It was
  still wrong about one thing: it posted Bombard #4128794 to (70,35) as "arrive this turn - FIRE from
  here", and the move consumed both movement points, so the shot answered `NO_MOVES`. **The plan's
  `FIRE from here` is a proposal, not a promise.**
- **The city-heal arithmetic is real and the supply cut is what beats it**: 6 adjacent hexes, and the
  city heals about twenty a turn while any is open.
- **Cost**: two turns of marching (T213-T215), one Builder captured and recaptured (`CAPTURE_MOVE` at
  (70,36)), and 11 damage on a Bombard plus 11 on the Cavalry from the city's strike. No unit was lost.

## `019-two-scouts-to-sea` — expired at T250

The file is `prompts/tasks/tmp/done/019-two-scouts-to-sea-expired-T250.md`. It was added on 2026-09-27
from the human instruction to send two Scouts to sea, find more civilizations, end the exploration task
after thirty turns and return to the default strategy, with a hard stop at T250 counted from the T220
clock. **It retired half-done, and the task file's own `expires:` line is what makes that the correct
ending.**

- **The instrument was two Rangers, not two Scouts.** `UNIT_SCOUT` is CS 10 and dies to the first thing
  afloat, so the T223 session took the Scout line's upgrade instead and the file was amended at T229 to
  name the line rather than the unit: 上海's Ranger #7077923 and 阿拜多斯's #7143460, both due about
  T238.
- **The first half held from T240.** Both Rangers were verified on water tiles by their own tile lines
  in `get_map_area` - #7077923 on a COAST REEF at (49,21), #7143460 on COAST at (75,32) - and they were
  afloat on the T244-T249 turns as well. An embarked unit keeps a naval movement allowance: under the
  Industrial-era Exploration dedication they read **7/7 moves**, about four to seven tiles a turn.
- **The second half never came.** Four living majors (Georgia, Sumer, Phoenicia, India) were `not met`
  at T220 and all four were still `not met` at T250. Across six turns of sweeping, explored land went
  34% to 34%.
- **What actually blocked it, measured.** The **east bearing is closed by 威尼斯**, the Trade city-state
  whose suzerain is the Netherlands: moves to (84,34), (84,35), (84,36), (85,14) and (86,40) all came
  back `BLOCKED`, and the first named the reason - `tile is enemy territory` - which is how (88,36)
  revealed 威尼斯's city centre at (90,36) and its Commercial Hub at (89,37) without a unit entering
  its borders. **A refusal is a reconnaissance read.** Only the north along x=82 stayed open, and it
  ran to (82,9) with nothing in it.
- **The west bearing found land but no civilization**: a desert coast at (34,18)-(36,22) carrying
  ALUMINUM at (36,18) and ANTIQUITY_SITEs at (35,18) and (36,22). That is the west Ranger's real
  deliverable to 021's escort.
- **`use-your-attacks` outranks this task.** 019's own `overrides:` line keeps `use-your-attacks` in
  force, so when the west Ranger disembarked onto the desert at (35,20) beside a barbarian MAN_AT_ARMS
  at (35,19) it fired - twice, across T247-T248, taking it from 100 to about 7/100 and clearing the
  tile - rather than staying a pure observer. `mass-on-contact` could not be met either time (one unit
  in contact, nothing within two turns of it), which is the rule's own withdrawal case.
- **The lesson for a task of this shape**: two embarked reconnaissance units are enough to cross water
  and not enough to *find* anything, because the search space is the whole map and the clock is counted
  in turns of sailing. 021's escort and cavalry inherit the search.

## `021-siege-legion-overseas` — expired at T270

The file is `prompts/tasks/tmp/done/021-siege-legion-overseas-expired-T270.md`. It was added on
2026-09-27 from the human instruction to build a siege legion, sail it, land on another civilization's
continent, run a pre-war analysis on the city found there, and concentrate fire on it if it could be
won. **It retired on its hard stop with the verdict written and the legion back on the sea lane.**

- **The target was found late and it was the wrong one.** Sumer was met at T252, twenty-eight turns
  after the task began, and its nearest city **西巴尔 (27,24)** was read from `get_map_area` with
  **walls 400** from `get_diplomacy`'s city list. The legion's leading four units reached the Sumerian
  water at T262 and one Line Infantry was **ashore on the unowned land at (29,22)** - the task's first
  condition, met once.
- **The four numbers could not be completed, and that is the finding.** Walls came from
  `get_diplomacy` (a static maximum of 400); the **ring** came from `get_map_area` - (28,22) a
  Commercial Hub, (26,23) a Diplomatic Quarter, (26,25) a Campus, (28,24) AMBER fishing boats; but the
  **pool and the garrison were never read**, because the city tile prints `[CENTER] ... [fog]` even
  from two tiles away at (29,22), and the only other route - our own attack list, which is how
  布鲁塞尔's Builder garrison was found at T235 - requires a war declaration that the verdict had not
  authorised.
- **The verdict is "cannot take it inside the window", and the numbers are distance, not walls.**
  Four Bombards and two Field Cannons do roughly 300 a turn against a city, so 400 walls and a
  200-point pool are a two-to-three-turn problem once staged. What could not be done was the staging:
  `get_staging_plan(27,24)` reported nine units `TOO FAR` with the nearest siege **35 tiles** out and
  closed with "ASSAULT OPENS on this turn with 0 shooter(s) in position"; the artillery was still
  13-22 tiles east when the file expired.
- **The lesson is about the clock, not the army.** The task's own `expires:` was counted from the
  queue - "forming the legion 4-10, the voyage and the landing 6-18" - but nobody measured the voyage
  before the deadline was set: the target turned out to be thirty to forty tiles away across a
  landmass that pushed the land units onto roads and the embarked ones into a bay. **A distance is a
  measurement, and this file assumed a short voyage.**
- **What the sea leg actually cost**: two Frigates bought for 1120 gold each (one for this task, one
  for 022), a 310-gold anti-cavalry upgrade, and a carrying-capacity failure that reached **bankruptcy
  at T265** - gold hit zero, the turn result printed `DEFICIT: Gold -48/t ... bankrupt in ~0 turns`,
  and two units were disbanded. It was repaired inside one turn by policy (`商队旅馆` and `统治`), by
  activating three Great People and by deleting a retired Ranger. **Two overseas expeditions at once
  is what the gold/turn line cannot carry**, which is the directive's own ceiling rule.
- **The withdrawal and the retirement.** On T263 a Sumerian Cuirassier appeared one tile from the
  beachhead, and the four landed units were ordered east rather than reinforced; by T270 they were
  back on the lane at (38,22)-(46,24). The file was retired with
  `scripts/temp-task.py retire 021 --expired --turn 270`, the register and the IN FORCE NOW line were
  rewritten, `tests/test_temp_tasks.py` passed 15/15 and the text gate was clean.
- **One measured trap from this task is worth carrying forward**: a city's own tile can stay `[fog]`
  at two tiles' range while its whole ring is visible, so **the four numbers are only ever three**
  until a probe attack lands - and a probe attack means a war.

## `022-take-haarlem` — done at T271

The file is `prompts/tasks/tmp/done/022-take-haarlem-done-T271.md`. It was added on 2026-09-28 from
the human instruction 增加任务：占领哈勒姆 and retired **fifteen turns early** with its `done when:`
satisfied in full. It is the only task of the session that ended in a captured city.

- **Gate 0 was one call this session had never made for the Netherlands.** For thirty turns
  `get_diplomacy` had printed `荷兰: Cities: 7 (all in fog)`; at T258, the turn after 021's Frigate
  sailed west, it printed **`哈勒姆 pop 6 (71,22) walls 100 + 6 in fog`**. The city turned out to be
  five tiles north of 布鲁塞尔 across a narrow strait.
- **The four numbers**: walls **100/100** static from `get_diplomacy`, falling to **0** under fire;
  pool **200/200** then **20** at the last read before the capture; **garrison `UNIT_BUILDER`** - a
  non-combatant found through our own attack list, the third time this map has used that route
  (布鲁塞尔 T235, Alexandria T215); **ring** read at radius 3 - (70,22), (71,23) GRASS MARSH [RICE],
  (72,23) with an ALCAZAR, (70,21) an incense plantation, (70,20) a road, and 哈图沙's centre at
  (68,20) two tiles west.
- **The staging table was built before the first assault order and it was right about the geometry.**
  `get_staging_plan(71,22)` named 18 ring tiles, posted Frigate #7929900 to (69,23) as a d2 firing
  tile, and gave the three **d2 LAND** tiles the shooters could use - (69,21), (70,20), (71,20) - so
  the train never had to fight from d1. It also named the supply hexes, cut **3/6**.
- **What actually broke the city, in order**: the Frigate alone did ~22 wall points a turn from d2
  (T261-T266, `walls 100 -> 78 -> 57 -> 41 -> 21 -> 5 -> 0`); the Bombard landed on **d1 at (71,23)**
  and added ~46 a turn to the pool; and **a siege unit firing from d1 works** - it resolved
  `RANGE_ATTACK ... dist:1`, which corrects the standing note that a siege unit at d1 is "refused".
  The pool went 200 -> 189 -> 132 -> 86 -> 60 -> 20 over five turns while the city healed about twenty
  a turn with three of six hexes cut.
- **The cost**: two Field Cannons and a third lost to barbarian ships during the operation, a
  310-gold Battleship upgrade, and the bankruptcy of T265 (gold 0, `DEFICIT: Gold -48/t`, two units
  disbanded) which was repaired inside one turn by policy and by cashing in three Great People.
- **The hold is the live risk and it is not solved by the capture.** Haarlem arrived at
  **loyalty 40/100 losing -10.3 a turn with a four-turn revolt timer**, `HP 120/200`, `Def 0`,
  production 1, and both its Monument and its Granary pillaged. The turn it fell it was given a
  garrison (the Infantry that took it), a governor (维克多) and two policies - `边防军` for the
  garrison and **`殖民地办事处`, which is the one written for exactly this case** (+3 loyalty a turn
  in a city not on the capital's continent). Whether that out-runs the Dutch population around it is
  the next window's question.
- **Two lessons for the next named-city task.** First, **a coastal enemy city five tiles away is
  cheaper than an inland one thirty tiles away**: 022 succeeded in thirteen turns from Gate 0 while
  021, given a thirty-three-turn window, never got its artillery into range. Second, **the walls and
  the pool are separate problems and only the walls are permanent** - the pool heals about twenty a
  turn and the only cheap answer is the supply cut, so a landing party's first job is the ring, not
  more fire.

## `024-take-brussels` — done at T224

**The record of the run that is playing now**, which was handed the T218 save after 021-022's run was
rolled back: it stands at T226, 哈勒姆 is still the Netherlands', and this is the only city it has
taken. The file is `prompts/tasks/tmp/done/024-take-brussels-done-T224.md`, added 2026-09-28 at T220
from the human instruction 占领布鲁塞尔 with `expires: turn 241` - retired **four turns after it was
filed and nineteen turns inside its own stop**, the fastest task of the three campaigns.

- **The staging plan was written on the turn the task was filed, and the fire came from the tiles it
  named.** `get_staging_plan(69,29)` at T220 reported *18 ring tile(s), 8 unit(s) placed, 1 unplaced*
  and posted the three Bombards to (68,31), (70,31) and (69,31) - all d2 - with a Line Infantry on d1
  at (68,29). Every shot below came from one of those tiles.
- **The wall pool was 100, and one Bombard shot took all of it.** T223, Bombard #5636108 from d2:
  `pre_hp:200/200 ... damage dealt:33 | city hp: 167/200, walls: 0/100`. A siege unit's work is on the
  walls; the city's own pool is the second problem.
- **Three shots read `damage dealt:none read` while the damage had landed** - T222's, T223's second and
  T224's first. The T224 shot opened on `pre_hp:54/200`, so **113 points had come off behind the stale
  prose**. That is the trap `docs/turn-result-blocks.md` describes, and here it cost nothing only
  because the train kept firing; calling the fire off on the first "none" would have cost a turn.
- **The capture was a move, not an attack.** T224: Bombard #5636108 took the pool to `0/200`; Line
  Infantry #5111819 moved (69,28) -> (69,29) and the log carries
  `CAPTURE_MOVE|69,29|from:69,28|CITY TAKEN`; the tile then read `[CITY_CENTER] ... (owned by 中国)`,
  `get_cities` went **19 -> 20**, and the Harbour at (70,28) was ours with it. A builder was walking to
  the **NITER at (68,31)** - the city-state's own resource tile - on T225.
- **Three attacks were fired at a city already at 0/200** after the pool emptied (two Bombards and the
  Field Cannon), and T223's `end_turn` recorded `CHECK FAILED [use-your-attacks]`. The rule cannot say
  it, so it is here: **an attack on a city whose pool reads zero buys nothing - the turn belongs to the
  capture move.** The pool is in the `pre_hp:` of the next shot, not in the prose of the last one.
- **The cost**: four turns, no unit lost in the operation, and the Line Infantry that took the city was
  at **57/100** after counter-battery fire at (71,28) and (69,28) on T221-T222 - it made the capture
  move anyway. Compare 022's thirteen turns from Gate 0 and three units lost to barbarian ships for the
  same class of coastal target: the difference is that here **the train was already assembled and its
  staging plan written on the turn the instruction arrived**, so the campaign spent its four turns
  firing rather than marching.

## The T218 rollback: the task set follows the game

`scripts/rollback-to-turn.py 218 --apply` archived the saves after T218
(`branches/rollback-to-T218-from-T219-T301-20260928-171348/`), split the diary at the boundary
(`branches/abandoned-T219-T298/`), and restored the rules that attempt had retired. It now also rolls
the **temporary tasks** back (`.tools/rollback-tasks.py`, job 3 of five) - which is how this was found:

- **Five tasks had been retired after T218** - 019 (T250), 020 (T237), 021 (T270), 022 (T271) and 024
  (T224) - and every one of them recorded a `done when:` the rollback had just un-done. Left alone, 024
  would have sat in `done/` while 布鲁塞尔 was an independent city-state again: a human instruction with
  no carrier anywhere.
- **024 was restored**, because 布鲁塞尔 is a city-state at T218, its T241 deadline is reachable from
  there, and it is the newer of the two Brussels files. The command is
  `.tools/rollback-tasks.py 218 --apply --skip 019 --skip 020 --skip 021 --skip 022`, its backup is
  `branches/rollback-tasks-T218-20260928-174858/`, and the register says what it did.
- **019, 020, 021 and 022 were left retired deliberately** (the human's call, 2026-09-28): 020 is the
  same objective as 024, 022 (哈勒姆) is a subset of 023's campaign, and 019/021 are thirty-turn windows
  that belong to abandoned runs. That decision is written into `current_tasks.md` rather than left
  implicit - a skip nobody records is the same silent withdrawal this job exists to prevent.
- **023 was kept** although it was added after T218: a human instruction is not the game's to withdraw.
  What it needed was re-reading, and its deadline was re-counted from T218 to **T272**.


## T221 - 024-take-brussels retired (done)

布鲁塞尔 (69,29) 在 T221 落入我手，比 expires (T241) 早二十回合。Gate 0 的数字：walls 100/100、
city hp 200/200、守军是一支商人 (UNIT_TRADER，非战斗单位，从我们自己的攻击列表读出)、ring 18 格、
supply line 6/6 全被切断（城市因此不再回血）。三发攻城火力（射石炮 #4128794 在 (68,31) d2、
#4325376 在 (69,31) d2、#4980745 在 (69,30) d1）把城防池从 100 打到 0、城市血量打到 131；
随后胸甲骑兵 #6029340 (70,29) d1 与线列步兵 #4456464 (70,30) d1 的近战攻击把血量清零并直接占领
（第三次实测：近战攻击清空城防池即占领，攻击者进入城市）。city_action keep -> 布鲁塞尔 pop 7
(id 1310739)，忠诚 50/100 且 +14/回合；get_city_states 不再列它，empire 19 -> 20 城。
代价：线列步兵在 T220 的城防火力中掉 10 血 (57/100)，无单位损失。三条教训：(1) 射石炮移动后
不能开火（NO_MOVES|Ranged attacks require movement），staging plan 的 "arrive this turn -
FIRE from here" 对移动满格抵达的单位不成立；(2) 线列步兵 #5111819 被一条长移动指令带下水
(71,28)，再次证明 024 的 GROUND gate 警告——一条盲目的 move 会无声地让陆军登船；(3) (74,23)
的 CAPTURE_MOVE|BLOCKED 说明那里有一个可俘获的敌方平民，但海路被阻断。


## T224 - 020-take-brussels retired (done), and the takeover that found it

The human rolled the match back to T224 a second time (after the T218 rollback above), and the first
thing the new session did was rebuild every fact from the game rather than from the notes. That is
how 020 ended: **布鲁塞尔 is already ours at T224.** `get_cities` lists it (pop 7, id 1310739), the
tile at (69,29) reads `PLAINS FLOODPLAINS_PLAINS River Coast (Road) [CITY_CENTER] (owned by 中国)
[my: CUIRASSIER]`, and `get_city_states` no longer lists 布鲁塞尔 among the five city-states. All
three of 020's own conditions therefore hold, and the file was retired as
`done/020-take-brussels-done-T224.md` by `scripts/temp-task.py retire 020 --done --turn 224`.

- **The register had it wrong, and the game was the authority.** `current_tasks.md` carried the
  rollback script's note that 020 "was restored by the rollback to T224 ... its `done when:` is false
  again there". That note is a heuristic - the script restores any task retired *after* the rollback
  turn - and at T224 布鲁塞尔 is ours. The lesson is the one this repo keeps relearning: **a task's
  state is what the game says, not what the rollback bookkeeping predicted.**
- **The assault ledger is the rolled-back run's, not this one's**: T235's wall probe read
  `walls: 200/200`, fire came from (68,31), (69,31), (70,31), (71,30), and a Line Infantry attack from
  (69,28) took the city across T236-T237 (`city hp 200/200 -> 0, walls 200/200 -> 0`). This session
  inherited the city, not the fight, and says so rather than claiming the capture.
- **The four Chinese backups the rollback had left missing** (019, 020, 021, 022) were written by hand
  in the same turn; `tests/test_temp_tasks.py` + `tests/test_text_encoding.py` then read **41 passed**
  and `scripts/fix-text-encoding.py --check` exits 0.

### What the T224-T235 session measured

Three movement rules were added to the toolkit by this run, none of them in `AGENTS.md`:

1. **An embarked land unit cannot move onto enemy-owned land.** Cavalry #5177368 at (75,25) was
   refused `BLOCKED (tile is enemy territory but movement still blocked - check path)` for both
   (75,24) and (76,24) while unowned (77,25) was accepted - so a sea-borne invasion must land on
   neutral or friendly ground and walk in.
2. **A move onto foreign soil spends the unit's whole turn.** A Field Cannon with 5/5 movement stepped
   one tile onto Dutch land and then answered `NO_MOVES|Unit has no movement points for ranged
   attack`. This is the missing half of the `BLOCKED` message above: the refusal is a price the unit
   cannot pay, not a prohibition - the same Cavalry entered (76,24) without trouble at full movement.
3. **A melee land unit cannot attack a unit at sea** (`MELEE_CANNOT_ATTACK_AT_SEA`, manual:723), but
   **a ranged unit can** - and `get_units` lists the attack for both, so the long-recorded "phantom
   attack" is an unfiltered list, not a game bug. A Field Cannon did ~24 to a Caravel, ~4 and then ~11
   to 乌得勒支's walls.

The campaign itself did not take a city. 乌得勒支 (74,23) read `city hp 200/200, walls 185/200,
supply line 3/6 cut` at T235 with a **Builder** as its garrison, and the siege block read
`STAGNANT (+0 over 3 turns)` - a Field Cannon's wall damage is far too slow, the Bombard that would
fix it cannot share the single d1 firing tile and must cross five contested steps, and the Dutch
replaced every Caravel the water cost them. That is the record 023's expiry should be read against.

### What the new match and the production experiment are (2026-09-29)

The China match that tasks 028 and 029 governed was handed over at T288, and both files were retired
as **superseded** rather than done or expired: a new match was started for the military production
experiment, and a task file left in `prompts/tasks/tmp/` is read as an instruction for whatever game
is running. Their content is preserved in `prompts/tasks/tmp/done/`, and either can be re-published
with `scripts/temp-task.py add ... --replace`.

The new match - China, Qin (Unifier), against Australia and the Maori, Pangaea/Small, Prince, Quick,
Gathering Storm, turn-1 save `evals/saves/ATTEMPT-A1-T1.Civ6Save` - exists to **test** the production
doctrine in `prompts/tactics/01-unit-production.md`, not to be won. The experiment, its fixed
settings, its one-variable-per-attempt rule, and the tool that extracts an attempt's numbers from the
diary and the call log are `docs/experiments/README.md` and `scripts/experiment-report.py`; attempt A1
is `docs/experiments/001-attempt-A1.md`, and its instruction is task 030.

**Two things the creation of that match measured**, both of which cost time and are worth not
rediscovering:

1. **Civ 6 cannot start inside the workspace file sandbox.** Launch it with full access: with writes
   confined to the checkout, the game process appears and dies within seconds, writes nothing to its
   own user directory, opens no window, and `content_log.txt` never records an app launch. The same
   hold is visible directly - writing a file into `Documents/My Games/Sid Meier's Civilization VI`
   is refused.
2. **The Create Game leader pulldown cannot be scrolled by any input this toolchain can synthesise.**
   It lists 54 entries in an 11-row panel; the front-end Lua has no `eMouseWheel` handler, the popup
   has no scrollbar in its pixels, and arrow keys, PageDown, type-ahead, wheel events (posted and
   injected) and drags on five different parts of the panel all leave the list where it started. The
   leader, the civilisation and the opponent count were written into the engine's pregame model over
   FireTuner instead (`PlayerConfigurations[i]:SetLeaderTypeName` / `:SetCivilizationTypeName` /
   `:SetSlotStatus`), which the screen then displayed correctly; difficulty, map size, speed and map
   type come from the screen's own short pulldowns, which do fit.

## T68 - `031` and `033` retired (done): A2 took its city, and the attempt ends there

Attempt A2's finish line was met at **T68** - twelve turns inside the T80 deadline - and both files were
retired the same turn: `031-military-production-attempt-a2` and
`033-attempt-a2-third-phase-the-assault-on-the-city-state-t66-to-the-attempt-s-end`, by
`scripts/temp-task.py retire <nnn> --done --turn 68`. The capture itself is one line:

```
KEEP|耶路撒冷 (pop 5, id:196610, captured)
```

Run by three sessions in sequence - `sacred-garnet-vault-35` (T1-T40), `pale-pearl-aqueduct-92`
(T41-T65) and `volcanic-indigo-caravan-23` (T66-T68) - which is why the snapshot has to name all three:
the instrument attributes diary rows by session time, and naming only the last one drops every turn
before T66.

**The walls read `none`.** Twenty-six turns of staging, six of them spent at the gate, had produced no
wall value from any tool; the first Catapult shot printed `city hp: 200/200, walls: none`, and 耶路撒冷
never had a wall pool at any point. **The doctrine's entire wall phase - the reason the siege train
exists - therefore never ran.** What the city defended itself with were its garrison (an Archer that
moved into the city tile on the last turn), its sortied field army (six units at peak, a Heavy Chariot
among them) and its healing, about 20 a turn while any one of its six adjacent hexes stayed outside our
zone of control.

**The two turns of fire, in the city's own numbers:** 200 -> 130 (T66, two Catapults) -> 24 (T67, two
Catapults) -> 44 at the top of T68 (it healed 20 back while one hex was open) -> 0 (one Catapult hit).
The cost: **Warrior 655367 killed on the ring at (51,22)**, Catapult 1310723 down to 25/100 (the enemy
Heavy Chariot was adjacent to both forward guns on every turn and was never screened, because no tile of
ours can be *strictly closer* to an enemy that is already adjacent), Catapult 1245188 to 80/100, and the
capturing Warrior to 39/100.

**Four tool findings from the two assault turns, all of the same family - a reply that cannot be read as
a result:**

1. **`damage dealt:none read (city still N/200)` is not a damage reading.** Both T66 shots printed it
   while doing ~70 between them; the adapter only reports a delta when the follow-up read lands after the
   hit, and for a city attack there is no estimate to fall back on.
2. **`SIEGE PROGRESS` replays a recorded read, not a live one** (`end_turn.py` builds it from the history
   the attack follow-ups write), so T67's block still printed `200/200` while the pool was at 130. The
   trustworthy live number is the attack estimate line - `vs CITY_CENTER (CS:0, HP:N)` - which is where
   130, 24, 44 and 0 all came from.
3. **The capture move's reply is stale too, and this one nearly cost the attempt its result.** The T68
   move answered `CAPTURE_MOVE|50,22|from:49,21|now_at:49,21|BLOCKED (city-state territory (耶路撒冷) -
   need suzerainty or Open Borders)` - the pre-war border refusal - while the unit was in fact standing
   on (50,22) and the city-state had been eliminated. `now_at` is read before the asynchronous move
   resolves and the border diagnostic runs against the pre-move plot. Only the follow-up `get_units` read
   showed the capture had happened; without it the attempt would have been recorded as blocked by a tool
   when it had actually won.
4. **The ZOC rule invalidates an attack the tool still lists.** `HasMovedIntoZOC` refused Warrior
   131073's T67 attack on the city (`ZOC|Unit entered Zone of Control this turn - cannot attack until
   next turn`) while `get_units` showed the same target under `CAN ATTACK`, so `use-your-attacks` can
   fail on an order the engine will not accept.

**The verdict, as the instrument prints it** (`--questions a2`, `--expect-est 60 --expect-city 80`):
**Q1 falsified** (the table reads `ram 0/1, ranged 3/4` - and the ram slot is unsatisfiable as
`tactics/01` is written, which is why its zero is a statement about the table rather than the session);
**Q2 held** (`Engineering T48; first siege order T48, first economy order T55` - the experiment's
headline and the first test H1 has ever had); **Q3 held** (`first keep T68`, the first city either
attempt has taken); **Q4 falsified** (the gold floor red on every turn the rule has run, and below +10 on
the diary's own number on all 68 turns).

The records are `docs/experiments/A2-final.json` (the snapshot), the end table and verdict at the foot of
`docs/experiments/002-attempt-A2.md`, and section 6 of `docs/experiments/RETRO-2026-09-29.md`.

## Task 036 - A5, the chops go into units: retired `--expired --turn 70`

**`036-attempt-a5-the-chops-go-into-units.md` expired at T70** and was retired to
`prompts/tasks/tmp/done/036-attempt-a5-the-chops-go-into-units-expired-T70.md`
(`python scripts/temp-task.py retire 036 --expired --turn 70`), which re-synced
`prompts/tasks/tmp/current_tasks.md` and the `IN FORCE NOW` line - **none in force** after it. The
script's own auto-commit did not run (it shells out to a Python without `pytest`; the protocol suite
is green under the repo venv, `21 passed`), so the retirement was committed by hand with the text
gate and `tests/test_temp_tasks.py` run explicitly.

**The attempt ran T1-T70 in one session** (`unbroken-cerulean-herald-09`) from the experiment's shared
start and **kept no city**. Its window's `done when:` - "turn 70 is reached, or a city is kept" - was
met by the turn, not the capture. The instrument's verdict is `HELD / FALSIFIED / HELD / HELD`:

- **the establishment was complete at T57** (Q1 held), two turns LATER than A2's T55 (Q2 falsified) -
  the chops did not buy the five-turn advance the variable predicted;
- **the economy was not deferred** (Q3 held): the first post-gate `BUILDING` order is a Water Mill in
  the compounding city at T44, one turn after the T43 gate;
- **the gold floor was met on the rule's measure for the first time in the programme** (Q4 held, 2 red
  turns from T60), on Oligarchy plus `POLICY_CONSCRIPTION`.

**Two things this task measured that belong in the doctrine rather than only in its record:**

1. **`remove_feature` accepts FOREST and refuses JUNGLE and MARSH on this map.** Three chops were
   attempted and refused (`(60,21)` and `(59,22)` jungle, `(61,21)` marsh - and `(60,21)` is the tile
   `get_builder_tasks` recommends a MINE for). 西安's ring held exactly two removable forests and both
   were chopped, so the chop-into-units treatment is worth **about two turns** of the war city's
   production here, not the five the design assumed.
2. **A ranged attack requires movement, and the adapter's approach path spends it**, so a siege unit
   ordered onto a city walks into the city's reach and dies: Catapult#1 fired twice from adjacent,
   took 25 then 55, and was destroyed for 120 production and 15 net damage while 耶路撒冷 healed back
   to 185/200. `screen-the-siege` cannot be satisfied by any formation under that rule - and it also
   counts a **friendly** major's unit as an enemy, which kept it red for seven turns.

**And the finding that outranks the variable:** an attempt can complete the whole establishment table
and still not take a city ten tiles away inside its window, because the march corridor costs a tile a
turn (182 `STOPPED_MID_PATH` refusals) and **two entire movement turns were lost to AI diplomacy
pauses** (T57 and T59, every unit at 0 moves). The binding constraint on this map is march time, not
production.

The records are `docs/experiments/A5-final.json` (the snapshot), `docs/experiments/005-attempt-A5.md`
(the attempt), and section 7 of `docs/experiments/RETRO-2026-09-29.md` (the comparison with A4).

## Task 038 - A7, two war cities instead of one: retired `--done --turn 60`

**The attempt ended on the first half of its own finish line: 耶路撒冷 was KEPT at T60**, twenty turns
inside Q3's T80 and earlier than A4's T65, which had been the programme's previous best. The capture
resolved inside the AI turn, so no `KEEP|` and no `CAPTURE_MOVE ... CITY TAKEN` ever entered the log -
**the city list is the confirmation** (`get_cities` at T60 reads `3 cities`, with `Jerusalem (pop 4)
[id:196610]`, a Warrior garrison, loyalty 67/100 at +17.0/turn, a `HOLY_SITE` at (49,22) and a pillaged
`MONUMENT`+`GRANARY`), and the T60 notifications read `Capital Captured` and `Defeated!`. **The
instrument cannot see any of that**: `experiment-report.py` reads the keep from a capture reply, so
`A7-final.json` and the `--compare` line both print `first_keep none` for A7 - and A6's identical
`none` must be read the same way, as "no reply in the log".

**The variable did what it was proposed to do.** Chengdu (131073), founded **T21** by the pinned
Settler with `UNIT_SLINGER` ordered **the same turn**, ran an army queue from its first order and
carried **12 of the empire's 27 army orders (41%, against Xi'an's 15)**. The train was therefore built
in parallel for the first time in the programme: **first Catapult owned T51 (Xi'an), second owned T54
(Chengdu)**, and the corrected table was **COMPLETE at T54** - `siege 2 melee 6 anticav 1 ranged 10
cavalry 2 recon 2`, six turns inside Q1's T60 and **joint-earliest with A4 and A6**. The parallelism
was worth **about three turns, not half**: built sequentially in the faster city alone the train would
have landed `T45 + 6 + 6 = T57`, and it landed T54, because Chengdu's Catapult took 9 turns against
Xi'an's 6 and the date is set by the slower gun - **which is what the attempt predicted before either
order was placed.**

**The verdict is `HELD / HELD / HELD / FAILED`** on Q1-Q4 (with Q4 nominally held on the rule's own
measure and failed on the diary's): the establishment completed T54, both cities held army-role orders
before the keep, the city was kept at T60, and the gold floor read below +10 on **all sixty turns** of
the diary's measure (the rule's own `carrying-capacity` only begins at T60 and was red 1 of 1:
`gold/turn +8.0 with military 272`). **The cost landed in exactly one place**: science at T40 was
*higher* than A6's (6.3 against 5.4 - Pingala's `Researcher` promotion, taken T44, moved Engineering to
T45, one turn before A6's T46 siege order) but **gold/turn at T40 was 6.1 against A6's 13.4, less than
half**, and `Conscription` (-1 gold maintenance per unit, taken T50) was not enough. The lost
compounding is real rather than asserted - Chengdu's alternative was a Monument (~20 turns at its T21
production, ~T41) or a Granary (~22 turns, ~T43) and it had the production to finish either inside the
window - and the empire ended with `CHECK FAILED [idle-district-slot]`, 2 districts for pop 11 against
3 allowed.

**Why the assault succeeded where A5's and A6's failed**, both of which had attacked the same city and
both of which found `walls: none` too: **two guns on the ring rather than one** (A6's signature failure
was `SIEGE FIRE: 1/2` on most firing turns - A7's pool fell monotonically, `200 -> 186 (T56-T58) -> 99
(T59) -> 81 (T60) -> kept`); **a melee unit kept adjacent and attacking the city every turn**, which on
a wall-less city reads `Est damage to attacker: ~0`; and **four Slinger -> Archer upgrades for 40 gold
each at T51**, which is the cheapest power in the record, because a Slinger adjacent to its target is
resolved as a **melee attack at CS 5** and dies (measured at T45, when one did exactly that).

**What it does not fix, and hands on.** The supply line never passed **3/6 cut** (`CHECK FAILED
[cut-the-supply]` fired every turn, naming (49,21), (49,22), (49,23)) - A7 simply out-damaged the ~20
heal, which the rule itself calls the more expensive route. **`get_staging_plan` assigns ring tiles by
distance and not by line of sight**: the d2 tile **(51,20) answered `NO_LOS`**, so one of the four
pre-war firing positions was dead ground. Losses were one Archer (killed in the AI turn at (51,21)) and
one Slinger. **The 18 self-report mismatches the instrument reports are a convention and not a drift** -
the diary wrote `ranged 4/4` while the record held ten ranged units and `recon 1/1` while it held two
Scouts, and **every mismatch runs in the conservative direction**, so no A7 claim overstates the army;
A6 had no surplus to under-count and so recorded zero.

**What the programme knows after A7.** The production half of the doctrine is answered on two axes
rather than one: A6 showed gold can buy the first gun earlier than production can, and A7 shows a second
war city can build the second gun in parallel - for a joint-earliest establishment (T54) and the
programme's first city kept (T60). **The next variable is not another production arm**: A7's ledger puts
the cost on the cash line and its siege log puts the remaining inefficiency in the supply cut and the
ring's line of sight, so **the revision this supports is `tactics/08`'s cash rule and `tactics/04`'s LOS
check, not `tactics/01`'s table**, which three consecutive attempts have now filled on exactly T54.

The records are `docs/experiments/A7-final.json` (the snapshot), `docs/experiments/007-attempt-A7.md`
(the attempt), and section 9 of `docs/experiments/RETRO-2026-09-29.md` (the comparison with A6).

**Note on this file's coverage:** the entry above A7's is A5's (task 036); **A6 (task 037) has no
history entry here**, so the file jumps from A5 to A7. A6's measurements are in
`docs/experiments/006-attempt-A6.md`, `docs/experiments/A6-final.json` and section 8 of the retro, and
this gap is recorded rather than papered over.
