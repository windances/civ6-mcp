# TEMP TASK 018 — take Alexandria, Egypt's original capital: 侦察, 战前分析, 攻城集结, then the assault

added:     2026-09-27 (human instruction: 占领亚历山大，先进行侦察，进行战前分析，攻城集结后攻城)
expires:   turn 235 — counted from the queue, not the calendar, and the three phases are not equal
           here. **Reconnaissance is the unknown**: the north-east arc was ridden for ten turns and
           found nothing, both Scouts are dead, and the city has never been seen. The march is real:
           the siege train stands at the 底比斯 / ỉwnw front, at least ten tiles from any fog bearing.
           And the objective is a **capital**, which may be walled. Budget: recon 5-10 turns, march and
           staging 5-8, siege 3-5, plus a margin — T235 is that sum, and it is a hard stop. If it has
           not fallen by then, retire it as `018-take-alexandria-expired-T235.md` with where the train
           stood, what the capital read, and what blocked it.
done when: **Alexandria is ours** — its own (x,y) read from the city list at the moment of capture, a
           unit on the tile (`hold-what-you-take`), **and `get_victory_progress`'s DOMINATION block no
           longer reading `埃及: holds own capital`** — that line, not the city's name, is what proves
           the city taken was the capital. The diary carries the ledger: the four numbers re-read at
           war (garrison / walls / pool / ring, naming which came from a probe), the staging table with
           its overrides, the shots per turn and the tile each shot came from, and the cost paid.
           Retire it as `018-take-alexandria-done-T<n>.md` the turn the city is ours.
overrides: **the reconnaissance units are lent to this file.** Cavalry #5177368 and Crossbowman
           #2883591 sweep until the capital is located; that outranks a general map sweep, a wonder for
           era score, and any other errand those two units would otherwise run. It does **not**
           override `one-garrison-per-city`, the home defence against the Netherlands (already at war),
           or `use-your-attacks`. **The train belongs to Alexandria once it is located**: the siege
           pieces are not spent on a third Egyptian city, a city-state or a camp while the capital
           stands. **No declaration of war is needed or authorized** — Egypt (player 7) is already at
           war, so an attack issued the turn the target is seen lands that turn; and no other civ is
           opened as a front. **No peace**: the directive forbids `propose_peace` outright. **013 is
           retired and its gold earmark with it** — upgrades are the directive's business
           (`upgrade-the-siege` still applies), so this file authorizes only what the assault itself
           needs. It re-opens nothing: 底比斯 and ỉwnw are taken, and 014 is closed.
scope:     Alexandria and the Egyptian units on its ring, plus the two units lent to the search for it.
           Not the Netherlands front, not a city-state, not a barbarian camp, and not Egypt's other
           cities — taking those may be how the map opens, but they are their own decision, and this
           file's objective is the capital.

## Gate 0 — it is not located, and that is the first phase (侦察)

**A capital in fog has no pre-war analysis to make.** `tactics/07`'s Gate 0 is "a candidate city is
actually visible", and this candidate has never been seen by anyone. The count is exact and it fell
because of us: T194 `get_diplomacy` read Egypt holding 4 cities, T195 read `Cities (3): 赫利奥波利斯
pop 6 (65,32) walls 100 + 2 in fog`, 底比斯 fell that turn and ỉwnw at T199 (our own count went
15 -> 16 -> 17), so **Egypt is down to two cities and by T209 neither has been read** — one of those
two is the original capital, which `get_victory_progress` confirms Egypt still holds. The name is
known — the diary has called it Alexandria since T194 — but **a name is not a coordinate**, and a fog
city read as Egyptian is not automatically the capital.

- **The bearings, as last read** (T195 `get_strategic_map`, the newest one on record): `底比斯 (68,34):
  N:7 NE:3 SE:4`, `阿拜多斯 (68,38): NE:4 SE:3`, `索贝克 (66,45): NE:6 SE:3 S:4`, `孟斐斯 (65,41):
  SE:5`. The Egyptian remnant is most likely **north-east or south-east of 底比斯**, and the T209 diary
  records the north-east arc as ridden out — so **open a new bearing**, do not push the same line.
- **The north coast is water**: the Dutch Caravel was shadowing it at (67,24)-(67,25) at T207. A
  coastal capital is reachable by ranged fire and a city strike, **not by melee**: measured T207, three
  `attack` calls from Cavalry #5177368 against that Caravel each returned `LIKELY KILL` with
  `est damage dealt:~57`, while the Caravel stayed at 57/100 and the Cavalry kept all 3/3 movement.
  **A land unit's listed attack on a naval unit never executes.**
- **Verify the name before the train moves.** The tell is `get_victory_progress`'s DOMINATION block:
  while Egypt holds its own capital it reads `埃及: holds own capital`, and the capital is the city
  whose capture changes that line. A city called Alexandria in a diary and a city that is Egypt's
  original capital are two claims, and only the second one is the objective.

| # | Number | Reading | Source |
|---|---|---|---|
| 1 | Location | **not known** — never read; the bearings above are the only lead | T195 `get_strategic_map` |
| 2 | Is it the capital | **Egypt still holds its own capital** (`埃及: holds own capital`); the block does not name it | T195 `get_victory_progress` |
| 3 | Garrison | **not read** — read the city tile's own unit list, which is where a garrison shows | — |
| 4 | Walls | **not read** — an original capital at war since T178 is assumed **walled** until a shot's result line says otherwise | — |
| 5 | HP pool | **not read** | — |
| 6 | Ring | **not read** — `get_staging_plan` needs the city's tile, so it cannot run until the city is visible | — |

The reconnaissance assets, **as read at T209 — re-read before ordering anything**:

| unit | at T209 | note |
|---|---|---|
| Cavalry #5177368 | north of ỉwnw, full HP after a T208 promotion | the only unit that has seen fog; the north-east arc is exhausted |
| Crossbowman #2883591 | (64,37), idle for ten turns | the second set of eyes the T208-T209 diary asked for — the south-east arc |
| Scouts | **both dead** | a replacement is a production decision, not this file's |
| Spy | none | — |

## 战前分析 — the gates, once it is visible, before any move

1. **Read it in its four numbers** (`tactics/07`): the city line for pool and walls, **the city tile's
   own unit list for the garrison** (`get_map_area` prints it; at 底比斯 it held a Great Writer, i.e.
   nothing that fights), and the ring for what is standing on it. `walls none` is worth re-probing
   every turn — a city can finish walls mid-siege, and this one has had a war's worth of turns.
2. **Count the defenders by class and HP within two tiles.** A garrison inside the city takes **no
   damage** (`GARRISON UNITS IN CITIES`) and dies only when the city falls, so the field units are
   what cost turns, and the counter matters: anti-cavalry against cavalry, ranged against melee.
3. **Say the turn count out loud, from shots that landed rather than from the plan.** 底比斯 taught
   the arithmetic the hard way: T194 fired one shot for 31 while two shooters dealt nothing, so count
   shooters that can actually bear on the city. A walled capital is **walls first, then the pool**.
4. **`get_victory_progress` is a gate, not a suggestion** — here it is also the **reason of record**:
   Domination needs the *original* capital, and this is the file that says so. Read it before the
   assault, so the ledger can say what the capture bought.
5. **Can we hold it?** A captured city arrives with an **empty production queue** (an end-turn
   blocker) at low loyalty, and a governor swings loyalty the turn it arrives — measured: Victor took
   阿拜多斯 from -3.6/turn to +10.2/turn, and 底比斯 began at 50/100 losing 16.1/turn. Plan the
   governor or the garrison **before** the city falls, not after.

## 攻城集结 — the staging, in this order

Run **`get_staging_plan(city_x, city_y)`** and write one row per unit — where it is, its movement, the
tile it goes to, the cost, the arrival turn, its role, whether it can fire from there — **before the
first `unit_action`**. The table is not the tool's output: calling the tool is not writing the table,
and measured T194 the tool was called once while 36 `unit_action` calls followed with no table written
anywhere. **Six of the plan's outputs are overridden** by what this map has already measured, and each
one has already cost a real turn:

- **a siege unit posted at d1 is refused** — it fires from d2 and dies at d1 (measured T163);
- **`arrive T+n` does not know our own units jam the corridor** — issue **one move per call** and
  re-read `get_units` between them (T159/T161 landed units 1-2 tiles short, two of them west of their
  start; at T194 a Scout answered `BLOCKED` and a Line Infantry `STOPPED_MID_PATH`);
- **a firing tile is a proposal until a shot from it succeeds — and a refusal is not a verdict on the
  tile.** The plan's `SPARE RING TILES` line is not LOS-checked (T194 offered (67,36)); that tile then
  refused `NO_LOS` twice and **fired normally from the same Bombard the next turn**, so re-test a
  refused tile on a later turn before writing it off;
- **a shooter that spends its movement cannot shoot at all** — T194: Bombard #4325376 moved one tile
  onto a hill and its attack answered `NO_MOVES|... Ranged attacks require movement`. `arrive this
  turn - FIRE from here` holds only when the move ends with a movement point left; check the terrain
  cost (`[mv:2]`, `[mv:3]`) before posting a 2-move siege unit;
- **entering a Zone of Control costs that turn's attack** — T194: `ZOC|Unit entered Zone of Control
  this turn — cannot attack until next turn`. A unit meant to attack this turn **starts the turn on
  its tile**; the ring is entered one turn and attacked the next;
- **a unit id is not durable across an upgrade** — T200: an order aimed at the upgraded ex-Musketman
  (id 3932184) was executed by the brand-new Cavalry standing at (52,24). **Re-read `get_units` ids
  after every `upgrade_unit`**, or the order moves the wrong unit.

Two more measured states that decide a staging table in enemy land: **a unit standing in enemy
territory cannot fortify or heal** (T194: `CANNOT_FORTIFY` / `CANNOT_HEAL`, which is a state and not a
tool failure), and **`get_units`' `>> CAN ATTACK:` list is not authoritative** — it listed a target
that answered `NO_LOS`.

## 攻城执行 — the fire order

1. **Walls first if there are any.** The `SIEGE POSTURE` block and each shot's result line carry
   `walls: N/100`; the pool is not the target while a wall stands.
2. **The train breaks the pool, not the melee.** Record each shot's `city hp:` from its own result
   line — and read the city again a call **later**, because the immediate post-combat line can say
   `read unchanged` after the damage landed (T194: 200/200, then 169).
3. **The melee attacks from d1 the turn the pool reaches 0** — and an attack that zeroes the pool
   **captures the city outright and moves the unit in** (measured T195 at 底比斯: the follow-up `move`
   answered `STACKING_CONFLICT|Friendly UNIT_MUSKETMAN already on (68,34)`), so resolve it with
   `city_action` the same turn or the turn will not end.
4. **Do not aim at the garrison while it sits inside**: it takes no damage and the city keeps its
   bonus. It becomes a target the moment it steps out.
5. **Finish what is wounded** and **cut what heals**: a city heals about twenty points a turn with an
   uncut supply line — 底比斯 went 169 -> 200 overnight at T195 while only four of six hexes were cut.
6. **Hold it on the turn you take it**: a governor or a garrison before the next turn
   (`hold-what-you-take`), **set its empty queue the same turn**, and report its loyalty.

## Report when it is done

The four numbers as read at war, naming which came from a probe; the staging table with the six
overrides and the tile each shot came from; the shots per turn and what they took off the walls and
the pool; the capture resolution and the tile the capturing unit stood on; the cost in units, turns
and gold; and **the DOMINATION line before and after**, so the ledger shows the capital changing
hands rather than asserting it. If it expires, say where the train stood, what the capital read, and
what blocked it — and whether the capital was ever actually located.

## Why this is a file and not a turn-check rule

Every mechanical part of the assault is already a rule — `siege-train`, `screen-the-siege`,
`mass-on-contact`, `take-the-city`, `hold-what-you-take`, `use-your-attacks`, `finish-the-wounded`,
`cut-the-supply`, `upgrade-the-siege` — and the reconnaissance half is `tactics/07` Gate 0. What no
metric carries is **which city is the objective and that it must be found first**: the map is large,
the capital has never been seen, the two units that could find it have other errands, and a plan that
optimises locally will keep taking the nearest Egyptian city instead. That choice, and the search that
has to precede it, is what this file exists to hold.
