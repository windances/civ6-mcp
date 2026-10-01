---
title: What the turn result tells you, block by block
---

Moved out of `AGENTS.md`'s Turn Loop on 2026-09-26, when that file crossed the 65536-byte
injection budget. Nothing was reworded: this is step 9 as it stood, and it is the reference for
every block `end_turn` prints — SIEGE POSTURE and SIEGE FIRE, BATTLE ASSESSMENT, SIEGE PROGRESS,
TAKE THE CITY, LOYALTY WARNING, UPGRADE AVAILABLE, UNUSED ATTACK — with the measurement behind
each one. The three blocks that until 2026-09-27 were described only in `AGENTS.md` are here too,
added the same day that file was cut back to the running-game loop: **the 10-TURN REVIEW** (and the
**WAR ECONOMY** line it carries while a war is on) and the **empire warnings**.

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
   legal attack is still unused, and since 2026-09-26 **neither the tool nor `end_turn` will
   discard one for you** — `skip_remaining_units` refuses and names the units, and the
   "a unit still has moves" blocker bounces with the attack listed instead of sweeping it.
   That is a measured change, not a preference: over the T139–T152 Russian war four attacks
   were swept away invisibly, each costing a unit-turn (a Crossbowman pair on the galley at
   (50,23) on T145, a Horseman adjacent to its target at (56,42) on T148, and a Man-at-Arms
   twice — the second one a real second attack, which is what `ELITE_GUARD`'s extra attack
   per turn means: when a unit that already attacked a city is still listed, that is a second
   shot, not a double count). Order the attack; `skip_remaining_units(force=True)` is the
   deliberate discard. And `finish-the-wounded` fires when an enemy within two tiles is at 20 HP or less and
   nothing attacked — a wounded enemy comes back, and **how fast depends on where it stands**: the
   manual's healing rates are 20 HP/turn in a city, 15 in friendly territory, 10 neutral, 5 in
   enemy territory (naval 2, friendly only). Those numbers come from `manual:1066-1085`
   §HEALING DAMAGE TO CITIES — `search_knowledge("city heals a small amount supply line",
   doc="manual")` prints the lines if one of them is ever in doubt. The one that must not be left alive is the enemy
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
   screening it, and distance to the nearest enemy city. **Read it before moving any siege unit: it is
   the only reliable answer to "can this tile shoot?"** The `CAN ATTACK:` hint lists targets a
   Catapult then answers `NO_LOS` to, and hex distance cannot be derived by hand — measured on
   阿斯特拉罕 (54,40): (54,38) fires (LOS), (55,38) is distance 2 with no LOS, (56,38) is distance 3.
   A siege that arrives without knowing which of its ring tiles actually fire gets one or two shots a
   turn instead of three, which is the difference between a one-turn pool and a three-turn one.
   Form up outside enemy range with the
   melee in front and the siege behind (`screen-the-siege` fails while a siege unit is within two
   tiles of an enemy with nothing closer to that enemy than itself), then advance. When you are
   attacking a city, the result now always carries its numbers — `city hp: N/200, walls: N/100 or
   none` — and the turn result carries a **SIEGE PROGRESS** block with the delta, escalating to
   `SIEGE STALLED` after three recorded turns without a net drop. **Walls are learned from a
   result line, never from an estimate**: the estimate reads `CITY_CENTER (CS:0, HP:200)` for a
   walled and an unwalled city alike, and 圣彼得堡 read `walls none` on the way in and answered
   `walls: 100/100` to the first melee attack (T149) — so probe with one cheap attack before the
   train commits, and treat one city's `walls none` as a snapshot, not a property of the map. A
   bare melee attack does **9** against 100 walls where the same attack beside the Battering Ram
   does full damage; that number is why the Ram travels with the melee (T150, measured). A city heals about twenty points
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

**The first turn a foreign city is visible, the result carries a `NEW TARGET` block** (2026-10-01):
the city's name, its owner, its population, whether it is an original capital, whether a war is
already on, and the two calls that answer it — `get_target_report(x,y)` for the walls, the city pool,
the garrison and the firing ring, and `prompts/tactics/07-pre-war-analysis.md` to paste into the
advisor brief. It exists because the ordinary event had no reporter anywhere else: the metric set
counts visible enemy cities (`enemy_cities_seen`) and **no rule reads it**, and the capture blocks
stay silent until a pool is empty. The comparison is held per process and its **first scan only
seeds** it, so a fresh session does not announce every city it can already see — only the ones that
become visible after it. The same information arrives the moment a unit moves: the move reply ends
with an `IN SIGHT from (x,y)` block naming any foreign city, barbarian camp or enemy unit the unit
can see from where it stopped, and the city line carries the same two follow-ups. The
novelty-gated `Revealed N new tiles` block beside it reports only tiles never seen before *in this
session* — measured over 158 recorded sessions it never once reported a city or a camp, which is why
the sight block does not depend on novelty.

**Every tenth turn, `end_turn` also prints a 10-TURN REVIEW** — the window measured rather than
remembered: what the last 10 turns bought and at what per-turn rates, your own plan and prediction from
ten turns earlier quoted back at you, the assault prerequisites the directive requires against the
units you actually have, the idle district slots, the gold/turn carrying limit, and a projection of the
current rates forward. **While a war is on it carries a `WAR ECONOMY` line as well** — how many of your
cities are building civilians (Builder, Settler, Trader, religious unit) and which ones. That line is
advisory, not a rule: it is `tactics/08`'s one-war-city question asked in the turn it matters, and a
task's Settler in a compounding city is a legitimate answer to it.

The review ends with three questions, and they belong in that turn's diary, not in your head: (1) was
the window efficient, with numbers; (2) which prerequisite for the next goal is in place and which is
missing; (3) does the planned completion turn still hold, and if not, what changes. **Ten flat turns are
invisible turn by turn — this block is where they show up.**

**Empire warnings** are the other standing block, and they arrive every turn rather than every tenth:
loyalty crises, idle trade routes, a gold deficit, resource caps, scoreboard position and military
imbalance. They cover the blind spots a turn-by-turn reader does not notice, and they substitute for
nothing — the periodic deep checks (victory progress, religion spread, diplomacy) still have to be made.
