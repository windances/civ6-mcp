# Turn checks — read and evaluated by `end_turn` on **every** turn

They are also evaluated at the **start** of every turn, by `get_game_overview`: the failing
rules with a per-rule streak ("failing for 40 turn(s)"), what the last turn actually bought,
your own plan quoted back, and a verdict. That is the check on whether the plan is being
executed — recomputed for the last forty diary rows, so a rule that has been failing for a
long time says so, and a rule that has just been cleared says that too.

Free prose here is for the human editing this file. Everything the MCP must enforce goes in
a `<!-- check ... -->` block, and every block is evaluated at the end of every turn against
the live unit list and this turn's diary row. A check whose `require` is false is reported in
the turn result, so the agent cannot end a turn without seeing it.

Fields:

| field | meaning |
|---|---|
| `id` | short name used in the report |
| `when` | optional gate — the check only applies while this is true |
| `require` | the assertion that must hold; when false the check fails |
| `message` | what to print on failure (one or more lines) |
| `level` | `warn` (default) or `error` |
| `once` | `true` = a **goal**: the first turn `require` holds it is achieved, reported once as `CHECK ACHIEVED`, and retired for the rest of the game (recorded per game in `.civ6-mcp-data/turn-checks-state.json`). Omit it for a standing rule that must keep holding — a district slot can go idle again, a siege unit can die, so those stay live. |

**An achieved goal is also deleted from this file**, at the end of the turn that achieves it.
The file as it was is copied to `prompts/checks/archive/turn-checks-<YYYYmmdd-HHMMSS>.md`
first, the rule block is replaced by a one-line trace comment naming the goal and the turn it
was achieved on, and the turn result reports `CHECK FILE PRUNED`. So what is listed here is
always still outstanding, and the history of the directive is readable in `archive/`. A goal
that has been achieved and removed comes back only under a new `id`.

Functions: `researched(NAME)`, `units(T1, T2, ...)`, `metric(NAME)`, `turn()`.
Metrics: science, culture, gold_per_turn, military, pop, cities, districts, improvements,
wonders, territory, techs_completed, civics_completed — plus the contact metrics listed under
"Contact on the march" below (enemy distance from our units, and attacks made this turn).
Operators: `+ - * / // %`, comparisons, `and` / `or` / `not`, parentheses.
Expressions are parsed with `ast` against a whitelist — a check file is data, never code.

## The one hard deadline

Both support units go obsolete the moment `CIVIC_CIVIL_ENGINEERING` is adopted: after that
nothing except a siege unit bypasses walls. It is the only prerequisite with a cliff edge.

This rule is a **goal** (`once: true`): the point is to have built one before the window
closes, so once that is true it retires. Keeping a ram alive afterwards is a different
concern, and the every-10-turns review's assault list ("ram/tower 0/1 - MISSING") is what
watches that.

<!-- check
id: ram-tower-before-civil-engineering
when: not researched(CIVIC_CIVIL_ENGINEERING)
once: true
require: units(BATTERING_RAM, SIEGE_TOWER) >= 1
message: No Battering Ram or Siege Tower exists and CIVIC_CIVIL_ENGINEERING is not yet adopted - the window is still open and closes for good. Build one (Ram 65, Tower 100) and give it to the melee; it helps melee only and must stand on the tile adjacent to the target city.
-->

## Contact on the march (engage what is in the way)

An assembling army that walks past an enemy fights two things at once: the city's ranged
strike from the front and the bypassed unit from behind, which is how the siege train dies.
When enemy units are standing within two tiles of our units, the turn is supposed to deal
with them first — and the counter unit is the cheap way to do it.

Metrics for this section, all relative to **our units** (not to our cities) and recomputed
every turn: `enemies_within_1`, `enemies_within_2`, `enemies_within_3`,
`enemies_cavalry_within_2`, `enemies_anti_cavalry_within_2`, `enemies_melee_within_2`,
`enemies_ranged_within_2`, `enemies_siege_within_2`, `weakest_enemy_hp_within_2`,
`attacks_this_turn` (attacks actually executed this turn) and `unused_attacks` (units that
still have moves and a legal attack they have not taken). They read 0 when the scan has no
data, so a rule gated on them switches itself off instead of firing blind. `at_war`,
`damaged_this_turn`, `local_superiority`, `enemies_massed_on`, `garrisoned_units`,
`cities_guarded` and `cities_over_garrison` are described under "War footing" below, and
`siege_units`, `siege_exposed`, `siege_in_city_range`, `siege_city_distance_min` under
"Staging the assault" below that.

Counter table (the game's own `PROMOTION_CLASS_*`): **anti-cavalry** (Spearman, Pikeman)
beats **cavalry** (Horseman, Knight); **ranged** beats **melee** because it takes no
retaliation; **cavalry** beats **ranged, siege and civilians** by reaching past the front
line; **melee** beats **anti-cavalry**; **siege** beats cities and walls but is nearly
helpless against units, so it must never be the unit holding the front tile.

**Why there is no "you must attack the enemy in contact" rule any more.** There was one
(`engage-the-screen`), and it was retired after the T101-T116 siege was replayed against it:
its requirement was "at least one attack this turn", and a turn where two Catapults shelled
Moscow while a 7 HP Swordsman stood one tile away satisfied it. "Did you attack anything" is
the wrong question; "is a legal attack still unused" is the right one, and `use-your-attacks`
asks it globally - including on turns with no enemy anywhere near. `mass-on-contact` covers the
other half (contact and no concentration).

<!-- check
id: counter-the-cavalry
when: turn() >= 60 and metric(enemies_cavalry_within_2) >= 1
require: units(SPEARMAN, PIKEMAN, AT_CREW) >= 1 or metric(attacks_this_turn) >= 1
message: Enemy cavalry is within 2 tiles and the army has no anti-cavalry unit. Cavalry ignores the front line and reaches the siege train and the ranged units behind it, so either add a Spearman/Pikeman (Bronze Working unlocks the Spearman) or engage it this turn with concentrated fire instead of letting it pick its target.
-->

<!-- check
id: use-your-attacks
when: turn() >= 60
require: metric(unused_attacks) <= 0
message: At least one unit still has movement points and a legal attack it did not use. `skip_remaining_units` is about to finish those moves and the attack is gone for the turn - an unused attack cannot be recovered, and a unit standing next to a killable enemy is the cheapest damage in the game. Attack, or say in the diary's tactical line why this one is being left alive.
-->

<!-- check
id: finish-the-wounded
when: turn() >= 60 and metric(weakest_enemy_hp_within_2) >= 1 and metric(weakest_enemy_hp_within_2) <= 20
require: metric(attacks_this_turn) >= 1
message: An enemy within 2 tiles is at 20 HP or less and nothing attacked this turn. A wounded unit heals roughly twenty points a turn inside a city and comes back at full strength - a ranged unit in range kills it for free (ranged attacks take no retaliation), so this is the one attack that is never a bad trade.
-->

## War footing: one garrison per city, and no unit fights alone

Once a war is on, a second unit standing on a city tile is doing exactly what the first one is
already doing, while the front is one unit short - and a unit that was attacked and never
answered invites the next attack. `metric(at_war)` is 1 when this turn's diary row records a
war (diplomatic state 6), so these rules only apply in wartime.

When a unit *is* hit - or the moment enemy forces are discovered in contact - the answer is not
a trade: assess the enemy, mass the units standing nearby, and kill. Every input that decision
needs is in the result - the `BATTLE ASSESSMENT` block lists, for each enemy within three tiles,
its class, combat strength, HP, distance and **how many of your fighting units are within two
tiles** (`local_superiority` is the best of those counts, `enemies_massed_on` how many enemies
already have two or more of yours in range). Two or three attackers on one target kills it this
turn; one attacker trades and then the target heals.

<!-- check
id: one-garrison-per-city
when: metric(at_war) >= 1 and metric(cities_guarded) >= 1
require: metric(cities_over_garrison) <= 0
message: A city is holding more than one unit while the war is on. One garrison per city, everything else belongs at the front - move the surplus out this turn. (Peacetime is different: garrisons are the standing army, and this rule is silent then.)
-->

<!-- check
id: answer-the-attack
when: metric(at_war) >= 1 and metric(damaged_this_turn) >= 1
require: metric(attacks_this_turn) >= 1
message: One of your units was attacked this turn and nothing answered it. Assess the enemy (the BATTLE ASSESSMENT block in the result lists class, strength, HP and how many of your units are in range), mass the nearby units, and kill - fight back at the attacker, close on the wounded unit to screen it, or pull it out of reach. If the answer is a withdrawal or a heal rather than an attack, say so in the diary's tactical line.
-->

<!-- check
id: mass-on-contact
when: metric(at_war) >= 1 and metric(enemies_within_2) >= 1
require: metric(local_superiority) >= 2
message: Enemy units are in contact and only one of your units is within two tiles of them. Do not trade one-for-one - the enemy heals and you do not get the unit back. Assess (the BATTLE ASSESSMENT block lists class, strength, HP and how many of your units are in range), pull the nearby units into contact so that two or three hit the same target, and kill it this turn. If every contacted enemy really can only be faced by one unit - a lone garrison, a unit with nothing within two turns of it - withdraw it to terrain or a city and say so in the diary, rather than leaving it to be defeated in detail.
-->

<!-- check
id: screen-the-siege
when: metric(siege_units) >= 1
require: metric(siege_exposed) <= 0
message: A siege unit is within two tiles of an enemy with nothing in front of it. Catapults and Trebuchets are the most expensive thing in the stack and the least able to take a hit, so the formation is not optional: the front-line unit must be closer to the enemy than the siege unit is, and the siege unit sits at range 2, never adjacent. Pull the screen up first, or move the siege unit back, and only then advance.
-->

## Staging the assault: outside their range, screen in front, siege behind

A city's ranged strike reaches two tiles, and so does a Catapult. The difference is that the
city can take the hit and the Catapult cannot, which is the whole reason the formation is
specified rather than left to taste: **stage outside enemy range, the units that can absorb
fire in front, the ranged and siege units behind, and treat the siege unit's tile as the one
that must be protected.** Advance only once the stack is formed - a column that arrives one
unit at a time is defeated one unit at a time.

`SIEGE POSTURE` in the turn result gives the geometry, measured by the game: for each of our
siege units, the distance to the nearest visible enemy unit, the distance from that enemy to
the front-line unit nearest the siege unit, and the distance to the nearest visible enemy city.
`metric(siege_exposed)` counts the siege units that are within two tiles of an enemy with
nothing closer to that enemy than themselves; `siege_in_city_range` counts those already within
two tiles of a city, and `siege_city_distance_min` is the closest approach to any target.

## The assault train (before any declaration of war)

The directive's list for one city: about 2 siege, 2 melee, 1 ram or tower, 4 ranged, 1
cavalry. Only checked once a war is plausible (turn 90+), because early game it is noise.

<!-- check
id: siege-train
when: turn() >= 90
require: units(CATAPULT, TREBUCHET, BOMBARD, ARTILLERY) >= 2
message: Fewer than 2 siege units. Ranged fire is not a substitute for siege - a Trebuchet breaks walls far faster than any Crossbowman. This is the gap that turned a 170-turn campaign into cities that took ten turns each.
-->

<!-- check
id: ranged-mass
when: turn() >= 90
require: units(SLINGER, ARCHER, CROSSBOWMAN, FIELD_CANNON, CROUCHING_TIGER) >= 4
message: Fewer than 4 ranged units. Machinery unlocks both the Crossbowman (range 2) and China's Crouching Tiger (range 1); every Tiger needs a melee unit holding the tile in front of it.
-->

<!-- check
id: melee-screen
when: turn() >= 90
require: units(WARRIOR, SWORDSMAN, MAN_AT_ARMS, MUSKETMAN, INFANTRY, PIKEMAN, SPEARMAN) >= 2
message: Fewer than 2 melee units. Ranged attacks can never capture a city - only a melee unit walking in takes it - so a stack without melee cannot finish anything it breaks.
-->

## Development rules that are checkable

<!-- check
id: dynasty-cycle-wonder
when: turn() >= 60
once: true
require: metric(wonders) >= 1
message: No wonder built. For China a wonder is a research building (Dynastic Cycle grants a Eureka AND an Inspiration from that era, and Chinese boosts are worth 60%). Zero wonders forfeits the civilisation ability for the whole game.
-->

<!-- check
id: idle-district-slot
when: turn() >= 60
require: metric(districts) >= metric(pop) // 3
message: District slots are being left idle (districts < floor(pop/3)). Growth IS the district plan; never leave a free slot empty.
-->

<!-- check
id: carrying-capacity
when: turn() >= 60
require: metric(gold_per_turn) >= 10
message: gold/turn is below +10 with the army counted. The directive's ceiling is measurable: military 596 at -0.1 gold/turn is not stronger than 156 at +19.8, it is slower.
-->

## Per-turn habits

Deliberately empty of trade routes: `end_turn`'s own empire warnings already report
`IDLE TRADE ROUTE: N unused route capacity`, and a check here printed the same fact twice in
the same result (seen live at T60). A rule added here should be one nothing else covers.

<!-- check
id: builder-backlog
when: turn() >= 60
require: metric(improvements) >= metric(cities) * 3
message: Fewer than three improvements per city. Unimproved tiles are the usual reason an empire stalls, and builders are the cheapest multiplier in the game - if gold is above ~300, buy one instead of saving.
-->
