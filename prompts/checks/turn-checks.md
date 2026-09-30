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

This rule was a **goal** (`once: true`) and it retired at T99. **The ram is no longer part of
the plan at all** (human instruction 2026-09-26: 不用锤，用投石车): the Catapult breaks the
walls, and the assault train is siege / melee / ranged / cavalry.

<!-- achieved T99: ram-tower-before-civil-engineering (original in archive/turn-checks-20260926-012524.md) -->

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
id: issue-the-calls-furthest-first
when: metric(move_stops_this_turn) >= 3
require: metric(move_stops_this_turn) <= 2
message: Three or more units were ordered somewhere this turn and stopped short of it: that is the column queueing behind itself, not fighting. `get_staging_plan` prints the order the calls should go in (furthest ring tile first, nearest last) - issue them in that order, one move per call with a `get_units` between them, and re-issue a stopped unit before moving the next. Measured on the branch this save was rolled back from (T228-T299): 232 stops in 72 turns, 19 in a single turn, and every staging plan leaving 6-9 units unplaced. **The metric counts jams, not movement budgets**: a stop whose own reason is `moves exhausted`, `impassable mountain` or the Shipbuilding refusal is the terrain, not the column (measured over the two experiment attempts, 2026-09-29: 76 stops in A1 and 11 in A2, seven in ten of them terrain, and not one naming another unit - so the raw count was a terrain meter). A turn that stops three units for a stated reason - a Zone of Control entry, a landing, a corridor that fits one unit - belongs in the diary.
-->

<!-- check
id: finish-the-wounded
when: turn() >= 60 and metric(weakest_enemy_hp_within_2) >= 1 and metric(weakest_enemy_hp_within_2) <= 20
require: metric(attacks_this_turn) >= 1
message: An enemy within 2 tiles is at 20 HP or less and nothing attacked this turn. How fast it comes back depends on where it stands (manual, HEALING DAMAGE): 20 HP/turn in a city, 15 in friendly territory, 10 neutral, 5 in enemy territory. Inside a city it heals to full in five turns, so that is the one that must not be left alive; in the field it heals 5-10, which is a tempo decision rather than an emergency - but it still acts first next turn. A ranged unit in range kills it for free (ranged attacks take no retaliation), so this is the attack that is almost never a bad trade.
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

<!-- check
id: concentrate-the-siege
when: metric(siege_firing_alone) >= 1
require: metric(siege_firing_alone) == 0
message: The train is deployed and only one of its guns is inside range 2 of the target. The directive counts units; what takes a city is shots. A Catapult does 45-52 against a city where an Archer does 9-11 into a CS 35 garrison, and a city heals about twenty a turn while any adjacent hex is outside our zone of control - so two guns out-damage the heal and one does not, which is not a slow siege but a siege that lands nothing. Measured in A6: a complete establishment and a Catapult bought with gold left the target at 200/200 with SIEGE FIRE: 1/2 for its whole window. Walk the other guns into the ring before firing again, and remember that a unit which spends its move arriving cannot fire the same turn (a two-tile move, a river or a hill costs both points) - stage a turn early rather than shoot with one.
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

**`siege_firing_alone` is the count that decides whether the siege works at all**: it is 1 when a
train is deployed and only one of its guns is inside range 2, and 0 while the train is still
marching in, when two or more can fire, and when no siege unit is ours. It exists because the
directive counts **units** and the city is taken by **shots** - `siege-train` asks whether three
Catapults exist, and this asks how many of them the target is actually inside range of. `SIEGE
FIRE: n/m` in the `SIEGE POSTURE` block prints the same pair.

## Finishing a city once its HP pool is empty

<!-- check
id: take-the-city
when: metric(capture_ready) >= 1
require: metric(downed_enemy_cities) <= 0
message: An enemy city's HP pool is empty and one of our capture-capable units is adjacent to it - the city falls this turn if that unit is ordered onto its tile, and does not if it is not. Melee, anti-cavalry and cavalry units can take a city (a Battering Ram or Siege Tower is refused with CAPTURE_MOVE BLOCKED, and ranged and siege units cannot), and only from the city's own tile. Cavalry was wrongly listed as unable until T122, when a Heavy Chariot walked into Moscow at 0/200 and took it while the scan called the tile empty - so a chariot parked next to a broken city is a capture waiting to happen, not a spectator. A city heals about twenty points a turn: live, Moscow sat at 0/200 with a Spearman two tiles away, was back to 120/200 six turns later, and the siege had to be fought again from nothing. Move the unit in (unit_action action='move', target_x/target_y of the city), then resolve keep/raze with city_action.
-->

`TAKE THE CITY` in the turn result names every enemy city whose HP pool is empty, the melee unit
in reach of it, and what happens if it is ignored. `metric(capture_ready)` counts the cities that
are takeable this turn; `downed_enemy_cities` counts all of them, reachable or not, and
`enemy_city_hp_min` is the lowest city HP pool we can see.

Every attack on a city tile records that city's HP, so a siege that is not working looks
different from one that is. What has no number attached to it is the last step: **the city only
changes hands when a melee unit walks onto the tile.** Damage can be finished by anything; the
capture cannot.

## The assault train (before any declaration of war)

The directive's list for one city: about 3 siege, 2 melee, 4 ranged, 1
cavalry — **no ram or tower** (human instruction 2026-09-26: 不用锤，用投石车, 一城3投石车). Only checked once a
war is plausible (turn 90+), because early game it is noise.

<!-- check
id: siege-train
when: turn() >= 90
require: units(CATAPULT, TREBUCHET, BOMBARD, ARTILLERY) >= 3
message: Fewer than 3 siege units for one city. Ranged fire is not a substitute for siege - a Trebuchet breaks walls far faster than any Crossbowman, and three Catapults (~260 a turn measured) out-damage a city's ~20/turn heal many times over, which is what keeps a siege bounded. This is the gap that turned a 170-turn campaign into cities that took ten turns each.
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

## Matching what they field, and upgrading what we have

Counting units answers "do we have a front line"; it does not answer "does our front line
survive theirs", and that difference decides the exchange before it starts.

<!-- check
id: match-their-melee
when: metric(strongest_enemy_melee_cs) >= 35
require: units(SWORDSMAN, MAN_AT_ARMS, MUSKETMAN, INFANTRY) >= 1 or metric(attacks_this_turn) >= 1
message: Enemy melee within three tiles of the army is CS 35 or better while our front line is still Warrior/Spearman tier. The mismatch decides the exchange before it starts - live T116-T119 an enemy Man-at-Arms (CS 45) took 11-20 damage from each of our Archers, dealt 79 to a Spearman and 82 to an Archer in single blows, and was removed only by attrition; T101-T116 lost a Battering Ram and a Warrior to one Battlecry Swordsman (effective CS 42). Either upgrade the melee (Iron Working gives the Swordsman, Military Engineering the Man-at-Arms; metric(melee_upgrades_available) of ours can upgrade, the cheapest for metric(min_melee_upgrade_cost) gold) or mass two or three attackers on that one target this turn instead of trading one-for-one.
-->

<!-- check
id: upgrade-the-siege
when: metric(at_war) >= 1 and metric(siege_upgrades_available) >= 1 and metric(gold) >= metric(min_siege_upgrade_cost)
require: metric(siege_upgrades_available) <= 0
message: A siege unit can be upgraded with the gold in hand and the war is on. A Catapult does 45 against a city where a Trebuchet does 55, and the window in which a Catapult is the best you have is exactly the window an assault is being decided: live T105-T121 the army fired Catapults from T106 and Trebuchets only from T120 - eleven turns of the campaign at the lower number, and the same three cities took 64 attacks. Call upgrade_unit on it before the next attack, or say in the diary why the gold is being kept.
-->

<!-- check
id: upgrade-the-unwatched
when: metric(at_war) >= 1 and metric(uncovered_upgrades_available) >= 1 and metric(gold) >= metric(min_uncovered_upgrade_cost) * 2
require: metric(uncovered_upgrades_available) <= 0
message: An affordable upgrade for a ranged, cavalry or anti-cavalry unit is waiting while the war is on, and the treasury can pay for it twice over. No other rule watches this class - match-their-melee covers the melee and anti-cavalry tiers, upgrade-the-siege covers siege - so nothing else will say it. Measured T204-T215: the treasury went 621 -> 768 while a Knight -> Cuirassier (230g) and two Crossbowman -> Field Cannon (310g each) sat unbought for twelve turns, and at T216-T217 two of them were bought at the doubled price the T201 policy window had created when it traded POLICY_PROFESSIONAL_ARMY ('50% discount on all unit upgrades') for housing - 540g where 270g would have done. Upgrade the cheapest one, or say in the diary why the gold is being kept.
-->

<!-- check
id: keep-the-upgrade-discount
when: metric(upgrades_gated_by_discount) >= 1
require: metric(upgrades_gated_by_discount) <= 0
message: An upgrade is affordable at the discount price and not at the price the treasury is quoted, because POLICY_PROFESSIONAL_ARMY ('50% discount on all unit upgrades') is not in the government - every offer has cost double since the T201 free window traded it for housing (measured 115 -> 230, 155 -> 310, 190 -> 380, and 540g paid at T216-T217 where 270g would have done). Put the card back at the next free policy change, or say in the diary which policy is worth more than halving every upgrade.
-->

## Holding what you take

A captured city is not safe because the enemy is gone. Loyalty takes it back with no battle: live
T112 Moscow was taken with pop 3, no governor and no garrison, and the game logs show a Free City
in its place from T116 - T118-T121 and nine attacks went into retaking our own city.

<!-- check
id: hold-what-you-take
when: metric(cities_low_loyalty) >= 1
require: metric(low_loyalty_without_governor) <= 0
message: A city is below 50 loyalty with no governor in it and no military unit on its tile - exactly the state Moscow was in when it revolted (captured T112, a Free City by T116, retaken T121 at a cost of nine attacks). The turn result carries a LOYALTY WARNING with each city's loyalty, its per-turn pressure, which way the game says it is going and how many turns that takes - the figure is a revolt countdown only while the city is losing loyalty, and turns to a full pool while it gains, so read the two together - the next owner while it drains, and the game's own advice string. Assign a governor (assign_governor) or put a unit on the city tile before it flips; if the governor is needed at the front instead, say so in the diary - a city that revolts becomes a Free City and has to be besieged again, with metric(cities_low_loyalty) cities currently at risk and the nearest revolt metric(nearest_loyalty_flip) turns away.
-->

## Development rules that are checkable

<!--
RE-ARMED 2026-09-30, and the reason is the bug this goal walked into. It retired as
`achieved T99` for the match key `china_-1894041591`. A retirement trace carries no match key,
but the persisted state in `.civ6-mcp-data/turn-checks-state.json` is keyed per match - so one
match's achievement deletes the rule from the shared file for every other match, and nothing on
the file can tell that the retirement does not apply. The A3-A7 military-production experiment
(`china_911679432`, eight sessions replayed from one T1 save) therefore ran its whole ~340 turns
with China's wonder obligation absent from the loop: `dynasty-cycle-wonder` appears in **zero**
of the eight session logs, all eight ordered **zero** wonders, and Dynastic Cycle's second clause
- completing a wonder grants a Eureka AND an Inspiration of that era - paid nothing, while the
10-turn review printed `wonders built 0 ... zero forfeits the ability` at every window. The test
suite stayed green throughout because `tests/conftest.py` restores retired goals into its fixture,
so `test_turn_check_hook.py` asserted this rule fires against a file the live game never had.
The gate is moved 60 -> 25 because the decision has to be visible while it can still be acted on:
in a 60-75 turn window a gate at 60 leaves no turns in which to produce a wonder, which is exactly
how the programme read this obligation - as a status line rather than as work. The boost figure is
corrected 60% -> 50% to match `Expansion2_Civilizations.xml:73` and the directive's own correction;
the archived copy still says 60%.
-->
<!-- check
id: dynasty-cycle-wonder
when: turn() >= 25
once: true
require: metric(wonders) >= 1
message: No wonder built. For China a wonder is a research building (Dynastic Cycle grants a Eureka AND an Inspiration from that era, and Chinese boosts are worth 50%). Zero wonders forfeits half the civilisation ability for the whole game - and it is the half that costs no extra unit production, because a second city builds it while the war city builds the army (tactics/08).
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

## Activated 2026-09-26 (staged in `pending/` until a server computed their metrics)

A rule that names a metric the running server does not compute reports itself `un-evaluable` every
turn and cannot be satisfied — the rule file is re-read on every turn, but the *metric set* lives in
the MCP process's memory. Both rules below therefore shipped in `prompts/checks/pending/` and were cut
in here once a server that computes `camps_within_3` and `enemy_supply_uncut_with_idle` was running
(measured T174). Both metrics are in `end_turn._CONTACT_METRIC_KEYS`, so a dead scan zeroes them and
the rule switches itself off rather than firing blind.

<!-- check
id: answer-the-camp
when: metric(camps_within_3) >= 1
require: metric(attacks_this_turn) >= 1
message: A barbarian camp stands within three tiles of one of our cities and nothing attacked this turn. A camp is a tactics/07 target (human instruction 2026-09-26), and it is destroyed by force - one military unit MOVING onto its tile clears it. Run the camp gates and answer them in the diary: CAMP (x,y) terrain; GUARD (every barbarian within two tiles, class/CS/HP); FORCE (two attackers with the counter unit plus the unspent unit that walks in - barbarian Spearmen are anti-cavalry, so ranged plus melee, never cavalry into spears, never a Scout/Builder/Trader); GROUND (what the last step costs, from a tile we already hold); WORTH (gold, era score, the CIVIC_MILITARY_TRADITION inspiration, and what it has been spawning); HOLD (which city gives up its garrison); CONVERT (any barbarian next to our melee worth the human's Three-Six Stratagems play). A camp left alone keeps producing era-appropriate units beside that city - the camp beside 北京 (T83 map read: (60,29); an earlier note said (60,30)) produced the Spearman that cost 160 gold at T65 - so either this turn's attack is on its guard, or the diary says what the raid is waiting for.
-->

<!-- check
id: cut-the-supply
require: metric(enemy_supply_uncut_with_idle) == 0
message: An enemy city has open adjacent hexes - its supply line - while our fighting units within three tiles still have movement. A city heals about twenty points a turn while any adjacent hex is outside our zone of control (manual:1066-1085, HEALING DAMAGE TO CITIES), so a hex that can be cut cheaply is worth cutting. Measured over the T139-T159 Russian war: 沃罗涅什 read `supply line 3/6 cut` and 喀山 read `1/6` for their whole sieges, while spare units "fortified in place because the corridor is jammed" (T155, verbatim) - both pools came back to full and both cities rebuilt their walls; 圣彼得堡 took six turns of fire for the same reason, because the heal was out-damaged rather than cut, and one firing tile could not out-damage it. Order the surplus units - the ones with movement and nothing to shoot at - onto or beside the open hexes, taking the far side of the ring rather than queueing in the corridor; a unit that walks there is out of the firing line that turn, and declining that trade belongs in the diary. **But read the pool before spending a shooter on it**: a partial cut under continuous fire has not let a city out-heal us - 哈勒姆 held a 3/6 cut and its pool went 200 -> 189 -> 86 -> 60 -> 20 over T266-T270, and the next Dutch city went 200 -> 65 with 3-4/6 - so when the pool is falling, keep firing and record the accepted partial cut rather than walking a shooter off the line to close the last hex.
-->

