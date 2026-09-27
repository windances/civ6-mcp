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

