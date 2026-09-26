# 6. Assault composition and fire discipline / 攻城开始后，部队搭配和攻击策略

Read once the stack is in contact with the target city and the assault is running.

## The composition, and each unit's job

| Role | Count | Job in the assault |
|---|---|---|
| Siege | 2 | Break the walls. Dedicated city damage (Catapult/Trebuchet **45**, Bombard 55) that does not take the ranged-versus-walls penalty. |
| Melee | 2 | The only units that can **take** the city: a melee unit walking in finishes it. One holds the front tile, one is kept for the capture move. |
| Ram / tower | 1 | Support, adjacent to the city, helping **melee only**: the ram makes melee do full damage to walls, the tower lets melee ignore them. Both die at `CIVIC_CIVIL_ENGINEERING`. |
| Ranged | 4 | Take the **city's HP** down (and kill anything that comes out to relieve it). Range 2, no retaliation. Never aim at a garrison that is inside - it takes no damage there. |
| Cavalry | 1 | Hunt survivors and reach the enemy's ranged and siege units. Never the unit holding the front tile. |

## Read the defender before you build the fire plan / 先读守军，再排火力

Every city's HP pool is the same 200 and heals the same ~20 a turn, so the pool is not what decides
how long a siege takes. **The garrison is.** A CS 35 unit inside a city adds a share of its strength
to the city's defence, and the same shooters do roughly a third as much:

| Shooter | Against a city with a CS 35 garrison | Against the same city ungarrisoned |
|---|---|---|
| Archer (RS 25) | **9–11** | **35** |
| Catapult (Bombard 35) | **45–52** | **45–52** |

Measured, T107–T130: Moscow (garrisoned Warrior/Swordsman) took seven turns of fire; 圣彼得堡 (no
garrison) went from first contact to ours in five turns *including the march*, and its pool fell 44
a turn to free melee alone; 阿斯特拉罕 (pop 3, garrisoned Swordsman) took six.

Three consequences, in the order they matter:

1. **Read the garrison before anything else** (`garrison:` on the city line, and what the unit is -
   a Great Writer is not a defender). A city with no garrison and no walls is not a siege, it is an
   attack; a city with a CS 35 garrison is a job for Catapults.
2. **Archer fire is negative against a garrisoned city**: two Archers at 9–11 are 18–22 gross
   against a 20/turn heal. Do not open a siege with archers on a garrisoned city and call the stall
   bad luck - either bring the Catapults (which are barely affected) or take the garrison away.
3. **The cheapest way to take the garrison away is to invite the sortie.** A garrison that attacks
   out loses the city its garrison bonus for that turn, and that is the turn to fire everything.
   T109: the Swordsman left Moscow to hit an Archer, and the same four shooters went from ~11 a shot
   to 95 in one turn. Stand a healthy melee unit next to the city - it is also the capture unit, and
   one movement point from the tile.

## The capture is a combat action, with three requirements / 占领是战斗动作，有三个硬条件

The last step has no damage number attached to it, and every one of these was violated once in the
T103–T130 war:

1. **The capturing unit MOVES onto the tile - it must not attack that turn.** Attacking consumes all
   remaining movement. T110: Moscow fell because the Chariot was ordered to move and not to attack.
2. **It must be ADJACENT at the start of the turn.** T129: a 4-tile order with four movement points
   reached only three tiles, and the last step was refused by the city's zone of control
   (`tile is enemy territory but movement still blocked`). T117: a Warrior ordered onto the capital
   from three tiles away walked in the wrong direction and spent its turn.
3. **It must have health.** T115: a 9 HP Barbarian Horseman died executing the capture of a 0/200
   city and the city stayed Russian. Use a unit above ~40 HP, and keep the wrecked one for garrison
   duty or healing.

A city at 0 HP heals ~20 a turn while it has a supply line, so a failed capture is not a delay, it is
a re-siege. Both failures above cost a full turn each.

## Order of work, every turn

0. **Read the ring before moving anything: which of our tiles can actually shoot?** `SIEGE POSTURE` is
   the arbiter — the `CAN ATTACK:` hint lists targets a Catapult then answers `NO_LOS` to, and hex
   distance cannot be worked out by hand. Measured at 阿斯特拉罕 (54,40): **(54,38) fires, (55,38) is
   distance 2 with no LOS, (56,38) is distance 3**, so a three-Catapult train fired **twice** a turn
   and the 200-point pool took three turns instead of the one the arithmetic promised. Sort the ring
   into "fires" and "dead" *before* the column advances, and stage each siege unit on a tile that has
   been tested. **A siege unit attacks cities and districts only**: ordering one at a unit is refused
   (`ERR:SIEGE_CANNOT_ATTACK_UNITS`) — the old path walked the Catapult at the target and lost the
   whole turn (T140); use a ranged unit (Crossbowman, RS 40) against units.
1. **Siege knocks the walls to 0** (and then the city's HP pool).
2. **Melee (following the Catapult fire, with the ram adjacent when the city has walls) takes the
   city** - and until then it is **also a
   damage dealer, not a place-holder**. A melee unit attacks the city's HP pool from the tile
   adjacent to it: it takes retaliation, and it is the only class that does, which is exactly why
   it is the one that should be standing there. Two rules and one warning:
   - **Healthy melee attacks every turn.** It adds its combat strength to the pool every turn
     *and* it absorbs the city's ranged strike that would otherwise land on the Archers behind it.
     A screen that never attacks is a unit the city has no reason to shoot at and the pool no
     reason to fear.
   - **Wounded melee does not attack a city** - it rotates home and heals (20 a turn inside a
     city of ours, 15 in friendly territory, against 5 in enemy territory). This is the doctrine's
     own warning and it is specific to wounded units: a 9 HP Heavy Chariot attacking a 110 HP city
     was destroyed outright, because a city defends at full strength no matter how much of its HP
     pool is gone.
   - **Live failure, T105-T110 (Moscow)**: three Warriors and a Horseman were assembled for the
     assault and never attacked anything, because the order of work read as "melee = the capture
     move". The pool came down on ranged fire alone - four volleys for 200 HP - and the melee sat
     *behind* the Archers while an enemy Swordsman killed two of them. The same units, attacking
     from the adjacent tile, would have shortened the siege and been the target the city shot at.
3. **Ranged shoots the city's HP** - not the garrison, and not the walls you already have siege
   for. The manual (`GARRISON UNITS IN CITIES`, `manual:1052-1065`) is explicit: a garrisoned unit's combat strength
   is partly *added to the city's*, and **the garrison takes no damage while the city is
   attacked** - it dies only when the city falls. The city is what has an HP pool to remove;
   walls come first, then that pool. A garrison that steps outside is a target like any unit, and
   a garrison that attacks from inside costs the city its garrison bonus - that is the turn to
   punish it. (Live: the old order of work said "shoot the garrison", and eight turns of fire
   traded blows with a unit that was never losing HP.)
4. **When the city HP pool reaches 0, the capture move happens that turn.** The turn result
   carries a `TAKE THE CITY` block naming the tile and the capture-capable unit in reach; the rule
   `take-the-city` fails while a city at 0 HP is still standing with one next to it.
   Melee, anti-cavalry **and cavalry** units can do it, and only from the city's own tile - a
   Battering Ram or Siege Tower is refused (`CAPTURE_MOVE` BLOCKED), and ranged and siege units
   cannot. Cavalry was listed as unable here until T122, when a Heavy Chariot walked into Moscow
   at 0/200 and took it; a chariot parked beside a broken city is the capture unit, so do not
   spend it on attacks. A city with **no garrison unit** in it is still attackable (the adapter
   resolves the city itself through `Cities.GetCityInPlot`): keep firing at the tile, and move
   the unit in - an empty city is not a city that cannot be hit, it is a city that can be
   entered. Two live failures to avoid: a city left at 0 HP heals about twenty points a turn
   and is back to 120/200 six turns later, and a broken city with nobody to walk into it is
   four turns of fire thrown away. **The turn a city falls, put a governor or a garrison on its
   tile** (`hold-what-you-take`) and set its queue — 阿斯特拉罕 came to us at **loyalty 50** with
   `producing: NONE`, which is both a flip risk and an `end_turn` blocker.
   **Reads of a city just after a hit are estimates, not facts**: T140–T142 the same city read
   `200/200` after two connections that had landed, then `85`, then `55`. Judge progress by the
   `SIEGE PROGRESS` delta and by a *later* reading — never conclude from one stale number that the
   attack did nothing.
5. **Re-check before the capture move**: a city only falls to a melee unit; a turn spent firing
   at a 0-wall city from range is a turn not spent finishing it.

## Stop the healing at the source: the supply line

A city's healing is **conditional**, and the condition is one the army can remove. The manual
(`HEALING DAMAGE TO CITIES`, `manual:1066-1085`): "A city heals a small amount every turn, even during combat, **as
long as it has a supply line**. A supply line is any hex adjacent to the city that is not within
an enemy unit's Zone of Control."

So the heal stops when **every** adjacent hex is either occupied by one of our military units or
inside the zone of control of one (i.e. has one of our units next to it). Six hexes, not sixteen
points of damage - and the `SIEGE PROGRESS` block now reports the count on the city being ground
down (`supply line 4/6 cut - the city is still healing`).

- **Prefer cutting to out-damaging.** An assault that must beat a twenty-point heal needs a much
  larger stack than one that does not; two spare units walked around the city are usually cheaper
  than two more Catapults.
- **The screen does double duty.** Units already standing in front of the siege to absorb the
  city's strike are, by standing there, also cutting supply hexes - pick the tiles with that in
  mind.
- **Walls do not heal the same way.** A city can only repair walls through the production queue,
  and only after **three turns of taking no damage** - so wall damage that keeps being renewed
  keeps the repair from ever landing.
- **Say the number.** When the assault is stalling, report how many adjacent hexes are cut and
  whether that is the plan; if the army is too small to surround the city, that is the reason to
  break off, not to keep firing.

## Fire discipline

- **Concentrate.** Every attacker on the same target, in the same turn. A supplied city heals
  about twenty points a turn, so damage spread over several turns and several targets is damage
  that never happened.
- **Judge progress by the city's own numbers**: `city hp: N/200` and `walls: N/100` (or `none`)
  on the attack result, and the `SIEGE PROGRESS` block in the turn result, which reports the
  delta and says `SIEGE STALLED` after three recorded turns without a net drop. Do not judge by
  the damage estimate on a city tile - that estimate describes the unit standing there.
- **Do not ignore the stall warning.** A supplied city heals about twenty points a turn, so an
  assault that does not out-damage the healing is an assault that never happened. Three flat
  turns means cut the supply line first (see above), then fix the fire (siege in position and
  screened, more attackers on the same target, a wall-breaker added) or break it off - and say
  which.
- **Kill what is killable.** An enemy at 20 HP or less is the one attack that is never a bad
  trade; a garrison that survives heals and comes back.
- **Do not feed the train in piecemeal.** A wounded attacker heals or withdraws; it does not take
  one more shot at the wall. Where it heals matters: the manual's rates are **20 HP per turn in a
  city, 15 in friendly territory, 10 neutral, 5 in enemy territory** (`HEALING DAMAGE`, p.89), so a
  wounded attacker that steps back across our own border repairs three times faster than one
  sitting in the field. Rotating a unit home for two turns usually beats leaving it in the line to
  absorb another hit.
- **Promote on a turn that is not an attack turn.** A promotion consumes the unit's whole turn
  (`EXPENDING XPS`, p.89), so the order is: attack first, then promote - or promote while the unit
  is out of range or healing. Match the promotion to the job it is doing in this assault: melee
  taking cities want the anti-garrison/damage line (Charge, Battlecry), ranged want the
  ranged-strength line (Volley, Arrow Storm), siege want anything that speeds a city's walls down.
  A promotion taken instead of an attack is a turn of damage thrown away, and a promotion taken on
  the wrong unit is a permanent one.
- **Keep the Great General with the stack.** A Great General gives **+1 movement and +5 combat
  strength to land units within 2 tiles** (`GREAT GENERALS`, p.87), it may stack with a combat unit
  for protection, and it is **destroyed if an enemy unit enters its tile**. +5 strength on every
  attacker in the assault is larger than most promotions, it is free, and it is lost the moment
  the general is left behind or caught: walk it with the siege train, and treat it as cargo that
  must never be exposed.
- **A second enemy stack arriving is a decision, not a distraction**: either it is killed first
  (files 2 and 3) or the assault breaks off. The siege train is never left between the two.

## When the assault is not working

If the walls have not moved in about three turns - the turn result says `SIEGE STALLED` - or the
garrison is being replaced faster than it is killed, stop and say why: no siege in position, siege
unscreened and dying, too few attackers to out-damage the healing, the siege train dead, or the ram
lost beside a walled target. A stalled
assault is pure cost - war weariness suppresses production while the enemy keeps every city. Fix
the front (bring siege, heal, upgrade, reinforce) or change the target; never negotiate it away
(the directive forbids peace).

## After the capture

- Garrison the captured city with the **cheapest spare unit** - one unit, per
  `one-garrison-per-city`; everything else belongs at the next front.
- **Then hold it.** A captured city can leave the empire with no enemy involved: live, Moscow was
  taken at T112 (pop 3, no governor, no garrison) and was a Free City by T116, which cost nine
  attacks and four turns to undo. The turn result carries a `LOYALTY WARNING` naming each city's
  pool, its per-turn pressure, which way the game says it is going (gaining/losing) and its
  turns-to-conversion figure - the two together, because that figure is a revolt countdown only
  while the city is losing loyalty and counts turns to a full pool while it gains - and the game's
  own advice string; `hold-what-you-take` fails while a city below 50 loyalty has neither a governor
  nor a unit on its tile. `assign_governor` is the cheapest fix (moving a governor is free), and
  a unit on the tile is the other one.
- Keep the stack together and move it on the next city; do not let it disperse into garrisons.
- Report the captured city's loyalty and whether a governor is needed.

## Defending the city you just took - and why the siege rules stop applying to it

The moment the capture move lands, the city is **yours**, and everything above is about a city that
is not. Two consequences, both measured on Moscow at T110-T120, and both easy to get wrong because
the checks keep talking about the assault:

- **The siege formation rules no longer apply around that city.** `screen-the-siege` fires while a
  siege unit is within two tiles of an enemy with nothing in front of it, which is correct while
  advancing on a target and meaningless while defending one: a Catapult has `RangedCombat 0` and
  cannot attack a unit at all, so in a defence it is a liability with no job. Pull it back out of
  the enemy's reach - do not keep chasing the check by screening it on the ring.
- **A newly captured city has no walls, so it has no ranged strike.** `city_action(attack)` answers
  `NO_WALLS|City has no walls - build Ancient Walls first`, while the city *does* retaliate when it
  is attacked (Moscow took 37 HP off a Russian Horseman that came for it). Ancient Walls are
  therefore the first build the city is given (80 production; 320 gold to buy), and until they exist
  the defence is the garrison, the melee in the ring, and the ranged units within range of the ring.
- **Expect the counterattack, and expect it to be cavalry.** Taking the city cuts their territory
  and their field army comes back for it: Moscow drew a Horseman, a Swordsman and a city-state
  Warrior within a few turns of the capture. Without an anti-cavalry unit the Horseman walks past
  the ring to the Catapults (`counter-the-cavalry`), so the defence's order of work is: the melee on
  the ring tiles, the ranged behind them at range 2 - note that a ranged unit at y=35 cannot reach a
  target at y=40, the firing positions *are* the ring tiles - and the cavalry as the mobile answer,
  never the siege train.


## What to report

The target city; for each role, which units are assigned and where they stand; the wall/garrison
numbers if the snapshot has them; the attack order for this turn (which unit hits what); the
capture unit; and anything that makes the assault fail (unscreened siege, missing melee, no
siege, ram lost, a relieving stack). Where a number is missing from the snapshot, name the
missing number rather than filling it in.
