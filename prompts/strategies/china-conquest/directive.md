China, Qin (Unifier). Play the two abilities this leader actually has, not a
generic domination plan.

**Dynastic Cycle (civilisation ability).** Eurekas and Inspirations are worth 60%
instead of 50%, and completing ANY wonder grants a random Eureka and Inspiration
from that wonder's era. For China a wonder is therefore a *research building*.

- Before researching a technology or adopting a civic, name the Eureka or
  Inspiration that boosts it and the action that triggers the boost. China gains
  more from a boost than any other civilisation, so skipping boosts wastes the
  ability.
- Build cheap Ancient and Classical wonders deliberately, for the boosts, even
  when their own effects are marginal.
- Great Wall segments are built by Builders, not by cities: they cost no city
  production and return Gold, Culture and Defence along the border. Spend surplus
  Builder charges on Wall segments rather than letting charges expire.

**Crouching Tiger (unique unit).** Medieval ranged unit, Range 1, high strength.
Range 1 means it must stand adjacent to its target, so pair every Tiger with a
melee unit that holds the tile in front of it. It is the backbone of a Medieval
defensive line and of any city assault.

**Thirty-Six Stratagems (leader ability) - human-assisted.** A melee unit can
convert an adjacent barbarian unit to your side, at the cost of the melee unit.
The MCP interface exposes no action for this, so the agent cannot trigger it.

- Do NOT clear barbarian camps near your territory. Barbarian units upgrade with
  the era, so a camp left alive is a source of era-appropriate units.
- Suppress camp units with ranged fire rather than clearing the camp, and report
  any barbarian whose type would be worth converting so the human player can
  perform the conversion from the game UI.
- Treat any converted unit that appears as a free reinforcement: it cost no Iron
  and no production.

**Conventional army, which is what the agent actually builds.**

- Mine every strategic resource inside your borders, especially Iron and Niter.
  Never plan around an imported resource: the deal ends the moment you declare
  war.
- Encampment and Barracks in the highest-production city. With no resource-free
  army route available to the agent, unit production time is the binding
  constraint.
- Melee to take cities, ranged to soften them, siege against walls. Never attack
  walls without a siege unit, and attack only at favourable odds.
- Heal damaged units rather than feeding them forward.

**Contact on the march - engage what is in the way, with the counter unit.**

- While the assault force is assembling or marching, **any enemy unit standing
  within two tiles of our units is dealt with this turn, before the column moves
  on.** Walking past an enemy means fighting the city's ranged strike from the
  front and the bypassed unit from behind in the same turn, and the siege train
  is what dies first. What the checks enforce is the measurable form of that:
  **no legal attack may be left unused** (`use-your-attacks`, read the
  `UNUSED ATTACK` line that `skip_remaining_units` prints) and **contact requires
  concentration** (`mass-on-contact`: two of our units in range, not one).
- Pick the target that costs the least: **finish a wounded unit first**
  (`weakest_enemy_hp_within_2`), then the one that threatens the most - a siege
  or ranged enemy unit is worth more than a scout, and a unit we can kill
  outright is worth more than a unit we can only dent.
- **Prefer the counter unit when there is one** (`enemies_cavalry_within_2` and
  friends come from the game's own `PROMOTION_CLASS_*`, not from a name list):
  - **anti-cavalry** (Spearman from Bronze Working, Pikeman) against **cavalry**
    (Horseman, Knight, Heavy Chariot). Cavalry ignores the front line and eats
    the siege train and the ranged line behind it - a Spearman is the cheapest
    answer that exists.
  - **ranged** against **melee**: it takes no retaliation, so a ranged unit can
    grind a melee stack down without healing turns.
  - **cavalry** of our own against **ranged, siege and civilians**: it reaches
    past the screen instead of trading with it.
  - **melee** against **anti-cavalry**; **siege** against cities only. A siege
    unit is nearly helpless against units - never let it hold the front tile.
  - Do not spend a ranged attack on a full-health unit you cannot kill while a
    wounded one is in range.
- The exception, and it must be written down: a lone scout or a barbarian unit
  we are deliberately keeping alive to convert with Thirty-Six Stratagems may be
  ignored - say so in the diary's tactical line so the skipped attack is a
  decision rather than an oversight.
- **"Hold" is not a state a unit with an unused attack may be left in.** A unit
  that has movement points and a legal target either attacks or is explicitly
  parked with a reason; `metric(unused_attacks) > 0` fails the `use-your-attacks`
  rule, and the skip call that closes the turn now prints exactly which units
  threw an attack away. A unit "reserved as the capture unit" (the Heavy Chariot
  at (53,36) from T109 to T116) is still a combat unit: reserving it does not
  mean letting the enemy that killed our Battering Ram and a Warrior walk around
  at 7 HP.
- **A wounded enemy at 20 HP or less must die this turn** (`finish-the-wounded`).
  It heals about twenty points a turn inside a city or after a promotion, so
  leaving it is not a delay, it is a reset. A ranged unit in range kills it for
  free.
- **Test the matchup before writing a unit off.** The Catapult's 8 damage against
  the Russian Swordsman (T109) came from that unit's **Battlcry** promotion
  (`PROMOTION_BATTLECRY`: +7 combat strength *against melee and ranged units*),
  which is why the Swordsman read CS 42 against our ranged fire. That bonus does
  not apply to a cavalry attack, so the Heavy Chariot faced CS 35, not 42 - and
  it was never once estimated. One estimate per matchup, then decide; do not
  generalize one unit's bad result into "the whole army cannot engage this".

**Siege.**

- **The formation, before anything else: assemble outside enemy reach, screen in front, ranged
  and siege behind.** A city's ranged strike reaches two tiles and so does a Catapult; the city
  can absorb the answer and the Catapult cannot. So:
  1. **Stage outside their range** (three tiles or more from the target and from any enemy unit)
     and form up there. `SIEGE POSTURE` in the turn result reports, per siege unit, the distance
     to the nearest visible enemy unit, the distance from that enemy to the front-line unit
     nearest the siege unit, and the distance to the nearest visible enemy city.
  2. **The units that can take a hit stand in front** - melee, anti-cavalry, cavalry - and the
     ranged and siege units stand behind them. The test is not "is something nearby" but "is
     something **closer to the enemy than the siege unit is**": `metric(siege_exposed) > 0` fails
     `screen-the-siege`, and a Catapult at distance 1 from the target has already lost.
  3. **Protect the Catapult's tile above all.** It is the most expensive unit in the stack and
     the least able to survive one turn of attention. If the screen cannot get in front of it,
     the Catapult stays back - never adjacent to the city, never the closest unit to the enemy.
  4. **Advance only when formed.** Marching in one unit at a time is how a siege train is
     destroyed in detail; arrive together, in formation, and open on the same turn.
  5. **On the way, the contact rule outranks the timetable**: the moment a unit discovers an
     enemy or is attacked, assess, mass and annihilate first, then resume the advance. A city is
     patient; a Catapult that walked past an enemy is not.
- Build the siege train *before* the war, not during it. A 170-turn campaign in
  this game built **zero** siege units: St. Petersburg's 100-point walls came
  down roughly ten points per crossbow attack and the city took ten turns.
  Ranged fire is not a substitute for siege.
- The line, with the numbers: Catapult 120 / CS 25 / **45 vs cities** (Engineering,
  no resource) then Trebuchet 200 / CS 35 / **45** (Military Engineering, no
  resource) then Bombard 280 / CS 45 / **55** (needs Niter). That city-damage
  figure is a dedicated bombard value, so it does not take the
  ranged-versus-walls penalty - a Trebuchet breaks walls far faster than any
  Crossbowman.
- Battering Ram (65) and Siege Tower (100) are `FORMATION_CLASS_SUPPORT`: they
  stack with melee and only work from the tile adjacent to the city. The Ram
  makes attacking melee do full damage to Walls; the Tower makes them ignore
  Walls and hit the city directly. Both abilities help **melee only** - a ranged
  or siege unit attacking beside them gets nothing, so a tower sitting next to
  your Crossbowmen is doing no work at all. **Both go obsolete at
  `CIVIC_CIVIL_ENGINEERING`** - build one before that civic lands, because
  afterwards nothing bypasses walls except siege units.
- If the war has already started and you have no siege train: do not grind a
  walled city down with ranged attacks. Either order the siege unit and accept
  the wait - check the production estimate first, and do not order a 10-turn
  Trebuchet for a city you will take in two - or, if a ram or tower is already at
  the front, put your **melee** next to it and take the city that way. Check
  `get_units` for where the melee actually is before assuming this is available.
- Order of work each turn: siege knocks the walls to 0, melee (with the ram or
  tower adjacent) takes the city, ranged shoots the garrison. Do not spend ranged
  attacks on walls you have siege for. **Ranged attacks can never capture a city**
  - once the walls are at 0 the city only falls to a melee unit walking in, so a
  turn spent firing at a 0-wall city from range is a turn not spent finishing it.
- What one city needs: about 2 siege, 2 melee, 1 ram or tower, 4 ranged
  (2 Crossbowman at range 2 and 2 Crouching Tiger at range 1) and 1 cavalry for
  survivors. Every Crouching Tiger needs a melee unit holding the tile in front
  of it.
- Judge an assault by the city's own numbers: `city hp: N/200` and
  `walls: N/100` (or `none`) on the result line, never by the damage estimate -
  on a city tile that estimate describes the unit standing there, and a
  non-combatant makes it read a meaningless `~0`. Every hit on a city also
  records its HP, and the turn result carries a `SIEGE PROGRESS` block with the
  delta; after three recorded turns without a net drop it says `SIEGE STALLED`.
  A city heals about twenty points a turn: if the assault is not out-damaging
  the healing, stop and fix it (siege in position and screened, more attackers
  on one target) or break it off - and say which, in the diary.
- A city's ranged strike reaches 2 tiles. Do not issue `city_attack` from 3 away,
  and do not feed the siege train in piecemeal - stage it adjacent to the target
  before the declaration, not after.

**Development.**

- Four to six cities, then stop expanding. Never train a Settler in a city of
  size one.
- Keep amenities positive before the first war: war weariness suppresses
  production exactly when the army needs it.
- Commercial Hub or Harbour, because unit maintenance scales with army size.
- **Specialty districts are gated by population: `districts <= floor(pop / 3)`**
  (the game's `DISTRICT_POPULATION_REQUIRED_PER = 3`; the Government Plaza and
  Aqueduct do not count against it). Check that arithmetic every time you choose
  production, and never leave a free slot empty - growth *is* the district plan.
  A live example: Changsha sat at pop 3-5 with an unused slot for 30 turns, and
  the capital never built a Campus at all.
- **Builders are the cheapest multiplier in the game, and unimproved tiles are
  the usual reason an empire stalls.** In that same game the empire had 35 tiles
  and **2 improvements at T59**, and the capital of a neighbour sat on 1.8
  production for a hundred turns because its hills were bare. If gold is above
  roughly 300 and any city has unimproved tiles, buy a Builder instead of saving
  for something 15 turns out. Gold above ~300 that is not being saved for a named
  purchase on a named turn is a wasted resource.
- **Build order inside a city:** growth first (Granary, Water Mill, farms), then a
  **Campus** (science compounds), then Commercial Hub, then Government Plaza, then
  Encampment only when a war is actually near. The Campus comes before the army,
  not after it.
- **Housing is a hard stop, not a warning.** If `housing - pop <= 1` the city is
  about to stall for dozens of turns; fix it now with a Granary, a farm, an
  Aqueduct, or a domestic trade route. Settle new cities on fresh water.
- **Do not build a Holy Site unless you are actually racing for a Great Prophet.**
  The pool is small and fills early - all five slots were gone by T151 in that
  game - and an unclaimed Holy Site then produces about one faith per turn for the
  rest of the game. It is a specialty district slot spent on nothing, and it was
  the empire's *first* district.
- **Army budget:** keep unit maintenance under roughly 30% of income, and treat
  **negative GNP as the hard signal that the army is over-built**. A large army is
  not a strategy - it is a cost until there is a siege train and a named target.
  Live example: military 20 -> 101 -> 273 while districts went 0 -> 4 -> 6, gold
  hit -132 per turn, and the war those units were for still took 60 turns.
- **For China a wonder is a research building** (see Dynastic Cycle above): each
  one grants a Eureka *and* an Inspiration, and Chinese boosts are worth 60%. Get
  the first cheap one up in the Classical era: waiting until T170 to build the
  Oracle throws away the ability for the whole game.

**Balance between development and conquest.**

The balance point is not a ratio of peaceful turns to war turns, and it is not a
feeling about how big the army should be. It is three conditions you can check on
the board.

- **Development never stops, including during a war.** Improvements, growth, the
  Campus line, amenities and one wonder are the compounding engine; the army is
  pure cost until it is actually taking cities.
- **Size the army from the target city, not from a target number.** More units is
  not more conquest: the 170-turn empire reached military 596 and the war still
  took 60 turns, because it built **zero** siege units. A stack that cannot break
  the walls in a bounded number of turns is a bill, not a threat.
- **Keep the army inside the economy.** After paying for it, `gold_per_turn` must
  still be about +10 or better. The ceiling is measurable: that empire held
  military 91-241 with gold per turn never below +17 from T60 to T120, then nearly
  doubled the army to 592 by T150 and gold per turn fell to +0.6 - 45 turns of
  income handed to maintenance, for a war that had already stalled. Its carrying
  capacity was a military of roughly **250-300**. Military 596 at -0.1 gold per
  turn is not a stronger position than 156 at +19.8; it is a slower one.

So the only decision that matters is when to start, and the trigger is a checklist
rather than a turn number:

1. A named target whose walls and garrison can be broken in a bounded number of
   turns.
2. The siege train already staged adjacent to it - about 2 siege, 2 melee, 1 ram or
   tower, 4 ranged, 1 cavalry - **before** the declaration, not queued after it.
3. Amenities positive. War weariness decays 50 per turn at war against 200 at
   peace, and 400 points cost an amenity, so a long war suppresses the very
   production that pays for it.
4. `gold_per_turn` still about +10 or better with the army counted.

China tilts this further toward development than most civilisations: there is no
unique unit before the Medieval era, so there is no early window where the army is
disproportionately strong and a generic rush buys nothing; Dynastic Cycle makes a
wonder a research building, so **zero wonders forfeits the civilisation ability for
the whole game** (the 170-turn empire finished at T174 with 0); Great Wall segments
cost Builder charges rather than city production, which weakens the "I need a big
army to feel safe" argument; and units and districts leave the same queue, so every
unit is a district not built. `CIVIC_CIVIL_ENGINEERING` obsoleting the ram and the
tower is a **deadline for the siege toolkit, not a reason to start early**.

What development bought on that same empire: improvements 2 -> 25 and science 7.8
-> 28.1 between T59 and T120, with gold per turn never below +17. Protect that
phase. On this map and this economy the first war belongs after the siege train
exists - realistically T100-T120, not T60.

**Governors and Great Generals.**

Neither was in this plan before, and both multiply everything above for free.
Governor points come from civics and cannot be respent cheaply, so each one should
buy the phase you are actually in - and the governor should move when the phase
ends.

- **平伽拉 / Pingala (GOVERNOR_THE_EDUCATOR) in the highest-population city while
  developing.** Base: +15% science *and* culture in that city. Promotion 研究员
  Researcher adds **+1 science per citizen**; 鉴赏家 Connoisseur is the culture
  twin. On a 9-science empire one pop-4 city adds about +4 science per turn, more
  than any building available at this stage.
- **马格努斯 / Magnus (GOVERNOR_THE_RESOURCE_MANAGER) in the city building the
  Settler, promoted to 给养保障 Provision**: Settlers trained there do not consume
  a population point. He must be established first - an unestablished governor
  grants nothing - and the promotion has to land before the Settler does.
- **梁 / Liang (GOVERNOR_THE_BUILDER) in the city producing Builders.** Her *base*
  ability gives every Builder trained there **+1 charge**, with no promotion
  needed, and 规划委员 Zoning Commissioner adds +20% production toward districts.
  A builder wave is the cheapest yield in the game; this multiplies it.
- **维克多 / Victor (GOVERNOR_THE_DEFENDER) when a war is near or a city must
  hold.** 驻军司令 Garrison Commander gives +5 combat strength to units defending
  in his city's territory and +4 loyalty per turn to other cities within 9 tiles;
  射击孔 Embrasure gives every military unit built there a free promotion. Loyalty
  is what flips a captured city, so a governor plus a garrison is the cheapest way
  to keep one - far cheaper than taking it twice.
- **阿玛尼 / Amani (GOVERNOR_THE_AMBASSADOR) is a city-state tool.** Posted to a
  city-state she counts as 2 envoys, and 幕后主脑 Puppeteer doubles them. That is
  how suzerainty is defended without spending envoy tokens, and suzerainty pays +1
  favour per turn on top of the city-state bonus itself.

**A Great General is a passive aura. Do not activate it.** It grants **+5 combat
strength and +1 movement** to land units in range for as long as the general lives;
a Great Admiral does the same +5/+1 for naval units. `activate` is a *retirement* -
it consumes the general for one one-off effect. Park him with the main stack so the
siege, melee and ranged all sit inside the aura, and retire him only when that
single effect is genuinely what the next ten turns need. +5 strength on every
attacker costs no production, and it makes a siege train break walls faster, which
is the binding constraint in every assault in this game.

**Conquest.**

- One front at a time, weakest neighbour's capital first.
- **One garrison per city, once the war is on.** A second unit standing on a city tile does
  exactly what the first one is already doing, while the front is a unit short. Everything
  above that one garrison belongs at the front: the stack, the siege train, the ranged line.
  `metric(cities_over_garrison) > 0` fails the `one-garrison-per-city` rule. Peacetime is
  different - garrisons *are* the standing army then, and the rule is silent.
- **The moment a unit discovers an enemy - or is attacked - assess, mass, annihilate.** Not a
  trade: a trade is how a war of attrition is lost, because the enemy heals and you do not get
  the unit back. The procedure, every time:
  1. **Assess.** The `BATTLE ASSESSMENT` block in the turn result appears when enemy forces come
     into contact (within three tiles) and when a unit is hit. It lists every enemy with its
     class, combat strength, HP, distance and how many of your fighting units are already within
     two tiles. Name the target before acting: the killable one (HP low enough that the units in
     range finish it), not merely the closest.
  2. **Mass.** Bring the units standing nearby into contact - two or three attackers on one
     target kills it this turn; one attacker trades. `metric(local_superiority) < 2` while an
     enemy is in contact fails `mass-on-contact`, whether or not you attacked. Do not feed units
     in one at a time: that is how the Battering Ram and the Warrior were lost at T109-T111.
  3. **Annihilate.** Concentrate every attacker on the same target so it reaches 0 HP this turn.
     A wounded enemy that survives heals about twenty points a turn and comes back at full
     strength (`finish-the-wounded`). Then keep the stack together and finish the rest of the
     group before returning to the objective - a beaten field force is the only thing that makes
     the next city cheap.
  If there is genuinely nothing to mass, do not trade: withdraw to rough terrain, a city, or out
  of the enemy's reach, and say so in the diary's tactical line. The rule fires on contact; the
  diary is where a deliberate withdrawal is recorded.
- Leave a garrison in every captured city and report its loyalty.
- Great Wall segments along the new frontier make captured ground cheap to hold.
- **No peace, ever.** Once war is declared it ends only when the enemy's cities
  are yours. Never call propose_peace. Refuse every offer of peace - a diplomacy
  session (get_pending_diplomacy, answered with respond_to_diplomacy NEGATIVE) or
  a trade that bundles peace with anything else. This deliberately overrides the
  standing advice in AGENTS.md that peace usually beats a war of attrition: the
  directive is the strategy, so follow it.
- Because there is no way out, the decision to declare is the only decision that
  matters. Declare only on a neighbour whose cities the army already in place can
  take, and only once the siege train and the first reinforcements are in
  position. A war you cannot finish is a war you must not start.
- An unfinished war is pure cost: war weariness suppresses production and unit
  maintenance keeps running while the enemy keeps every city he still holds. If
  the front stalls, fix the front - bring siege, heal, upgrade, reinforce - and
  never negotiate it away.
- Do not park the army after one capture. Garrison the captured city with the
  cheapest spare unit and move the stack straight on to the next city.
- Plan the war before the declaration: target order, the tiles the stack stages
  on, and the reinforcements already queued.

**City-states.**

- City-states are not conquest targets. Domination victory is owning the original
  capitals of the major civilizations, so taking a city-state advances the win by
  nothing, and the capture costs warmonger grievances with everyone who knows it.
- A city-state you already hold as suzerain is worth more alive than owned.
  Kabul's suzerain bonus doubles the experience your units gain from battles they
  initiate, on top of the militaristic envoy bonus (+2 production toward units in
  every city with an Encampment) and +1 diplomatic favour per turn. Annexing it
  deletes all three for one city.
- Defend suzerainty instead: check get_city_states for rival envoy counts and keep
  your tokens ahead. Losing suzerainty hands the whole bonus to a rival, which is
  worse than never having had it.
- The adapter exposes no Levy action, so you cannot call up a city-state's army
  yourself. If war is imminent and a suzerain city-state has units worth having,
  say so explicitly so the human player can levy them from the game UI - levied
  units fight for you for 30 turns for gold.
- Attack a city-state only for a stated reason: a rival is about to take
  suzerainty and permanent denial beats holding the bonus, or the city sits on a
  chokepoint or resource the current war actually needs. Otherwise leave it alone.

**Foreign missionaries.**

- China has no religion of its own: one Holy Site and roughly 1 faith per turn
  cannot buy Apostles or Inquisitors, and the adapter exposes no Condemn Heretics
  action. Assume no religious counterplay is available and never plan around
  religious units you cannot purchase.
- At peace you cannot attack a religious unit at all. Target selection treats a
  Combat-0 unit as a valid target, but the war check then rejects the attack with
  ERR:NOT_AT_WAR. Never declare war over missionaries alone.
- While at war with the owner (currently Russia) any adjacent military unit can
  attack one. Treat that as opportunistic: one unit, no chase, one tile of
  movement at most. A missionary is never worth pulling a unit off the front.
- The real threat is a rival religious victory, not one missionary. Call
  get_religion_spread every ~20 turns - it has never been called in this game, so
  the religious picture is currently unknown. A single civ holding a majority in
  every other civ is the trigger to act; anything short of that is noise.
- Attack faith income instead of missionaries. Russia's faith comes from its
  Lavra, so pillaging that Holy Site during the war stops the stream at its
  source and is worth more than any number of individual kills.
- Never buy a religious unit: a missionary carries the majority religion of the
  city it was bought in, which in China is a foreign faith.
- Ignore the conversion of your own cities. No victory condition in this plan
  depends on China's own religion, so do not spend military turn budget policing
  it.

**Incoming offers.**

Diplomacy arrives while the AI is processing. `end_turn` either pauses and reports
it ("Turn paused — AI diplomatic proposal from ...") or blocks outright ("Cannot end
turn: diplomacy encounter pending"). War declarations against you are auto-dismissed.

- **Peace: always refuse.** A deal goes to respond_to_trade(other_player_id,
  accept=False); a session goes to respond_to_diplomacy(other_player_id,
  "NEGATIVE"). A session runs 2-3 rounds, so answer every round until it closes -
  a half-answered session keeps blocking end_turn.
- **Verify, never assume.** War and peace actions can report success without the
  engine changing state: on 2026-09-20 the T111 declaration returned
  WARN:WAR_UNCERTAIN and the T122 peace returned ACCEPTED, yet Russia was still
  offering peace at T138 - the war had never ended and the agent had been planning
  as if it had. After any war or peace action, call get_diplomacy and confirm the
  WAR/peace flag before building a plan on it.
- Expect the offer to repeat: while at war an AI re-proposes peace roughly every
  3 turns. Refusing is cheap; finishing the war is what stops it.
- **Everything that is not peace: judge on merit, never reflexively.**
  - Sell surplus luxury copies - a second copy of a luxury gives no amenities, so
    take gold or GPT for it.
  - Refuse joint-war requests: a second front breaks "one front at a time".
  - Refuse demands, tribute, and requests to declare on a third party.
  - Buy a strategic resource only when it cannot be mined at home; the deal ends
    the moment you declare war.
- If a session cannot be closed with the tools, say so in plain text so the human
  player can answer it in the game window. Do not let it stall the turn, and do not
  assume the human answered it.
