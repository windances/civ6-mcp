# TEMP TASK 021 - a siege legion overseas: 组建, 出海, 登陆, 战前分析, and 集火攻城 if it can be won

added:     2026-09-27 (human instruction: 根据攻城经验，组建一支攻城军团，出海，登陆发现其他文明的大陆，并对发现的城市做战前分析，如果打得过，攻城前集结后集火攻城)
expires:   turn 270 - thirty-three turns from T237, where the match stands (`.civ6-mcp-data/heartbeat.json`
           reads `turn 237` and the newest diary entry is T237, the turn 布鲁塞尔 fell). Counted from the
           queue: forming the legion 4-10 (it is mostly drawn from the establishment, plus at most four
           new builds), the voyage and the landing 6-18 (the nearest other landmass is a short voyage -
           the Dutch navy works two to four tiles off our own coast - and embarking from a Harbour keeps
           the unit's movement, `manual:881`), reconnaissance and the pre-war analysis 3-6, the staging
           and the fire 4-10. A hard stop: if by T270 no city has been taken and no verdict has been
           written, retire this file as `021-siege-legion-overseas-expired-T270.md` with the legion's
           position, what it had read, and what blocked it.
done when: **one of the two endings below holds, and the diary carries it**: (a) the legion is ashore on
           a landmass that is **not our home continent**, and a major civilization's city there has been
           read in its **four numbers** - walls / HP pool / garrison / ring, each named with the source
           that produced it - with the `tactics/07` verdict written down; **and then either** that city
           is ours, its own tile at (x,y) reading `[CITY_CENTER]` owned by 中国 with one of the legion's
           units standing on it, its queue set and a governor or a garrison in place
           (`hold-what-you-take`), **or** the written verdict is **"cannot take it"** and names the
           numbers that say so (the walls, the turn count from shots that have landed, the cost, and why
           it cannot be held) with the legion either holding a captured beachhead or back on friendly
           ground. **"If we can win" is the human's own condition, so a measured "no" is a completed
           task and not a failure** - retire either ending as `021-siege-legion-overseas-done-T<n>.md`
           the turn it holds.
overrides: **the "no new unit" line, for this expedition only.** The T230 review and every planning
           block since have said "no new unit and no new gold building until the science line is closed";
           this file is the human's instruction to **form a legion**, so it authorizes: drawing on the
           existing establishment (siege 5, ranged 5, melee 3, cavalry 2, anti-cavalry 1 as read at
           T237), and building **at most four units for it** - a **naval escort** (up to two if the
           analysis says one cannot cover the transports), **one or two melee/anti-cavalry capture
           units**, and **replacements for losses**. Nothing else is built for it; any larger gap is
           reported for `tactics/01` to decide rather than filled silently. **A war declaration is
           authorized on the one target civilization this file's analysis passes** - the unmet majors
           are not at war with us, so contact and a declaration come first, and the directive's own rule
           applies: declare on turn N, position that turn, attack on N+1, and **a war you cannot finish
           is a war you must not start**, which is why the declaration follows the verdict and not a
           hunch. `propose_peace` stays forbidden, so this war has no exit either - that is the price
           and it is accepted knowingly. **019 is a partner and not a source**: the legion uses 019's
           findings (its two Rangers' sea lanes and any contact they make), but those Rangers stay 019's
           instrument and are **not** diverted; if 019 expires at T250 without contact, this file's own
           escort and cavalry take over the search, and that is inside this file's scope. **It does not
           override**: the Dutch war and the eastern-shore defence (塞纳 and 亚历山大, the cities the
           Dutch navy has raided), 布鲁塞尔's garrison and loyalty, `one-garrison-per-city`,
           `use-your-attacks`, the science and housing line outside the legion's port city, or Chichen
           Itza and 布鲁内列斯基's parked charges.
scope:     the legion, its port, the sea lane, the landing, **one or two cities** of **one** target
           civilization on another landmass, and the declaration on that one civilization. Not the
           Netherlands' existing front (their cities stay the directive's business), not a city-state,
           not a barbarian camp, and not a second expedition.

## Why now, and what the sieges already paid for

Measured in the last four turns, all of it transferable to a city on another continent:

| lesson | measurement | source |
|---|---|---|
| a walled city's numbers come from a **result line**, not from a tile read | 布鲁塞尔's city tile printed `[fog]` while its whole ring was visible; the first melee attack produced `walls: 200/200, city hp: 200/200` | T233, T235 |
| **a melee attack against a walled city is worth a Bombard** | the Cavalry's attack took walls 126 -> 76 - **50 points, as much as a Bombard - and took no retaliation** | T236 |
| **a d2 tile is not a d1 tile** | the Cuirassier ordered from (68,30) answered `STOPPED_SHORT ... 2 tiles away`; only (69,28)/(69,30) were real d1 | T237 |
| **a shooter that spends its move arriving cannot fire** | a Bombard that had just arrived at its d2 tile answered `NO_MOVES|Ranged attacks require movement` | T236 |
| **units stop mid-path** | eight units ordered, eight `STOPPED_MID_PATH`, one to three tiles short of the plan | T234 |
| **the post-combat prose is stale; the pooled fields are the record** | `damage dealt:none read (city still 156/200)` on a line whose `walls:`/`city hp:` had clearly moved - and a later read is the fact | T236, T237 |
| **cut the supply line or the city outheals you** | six hexes, 6/6 cut on the capture turn; a city heals about twenty a turn | T235-T237 |
| **siege units cannot attack units at all** | `ERR:SIEGE_CANNOT_ATTACK_UNITS`; levied and garrison units are the ranged and melee's work | 016, 018 |
| `SIEGE FIRE: n/m` is the fastest read of whether the train is in position | it is what turned "the assault opens T+2" into "not yet" | T235 |

## The half the sieges never covered: the sea (manual, not doctrine)

- **Embarked land units are prey.** "In the water, the embarked unit is very slow and helpless. It is
  unable to fight, and any enemy naval vessel can easily destroy it. It's critical to accompany
  embarked land units with a strong naval defense" (`manual:883`). The Dutch navy has already raided
  our own shore (T224: five units damaged, three farms pillaged), so the escort is not optional on a
  contested lane.
- **Embarking spends all movement - except from a Coastal City or a Harbour District** (`manual:881`).
  Launch from a **Harbour** city: 布鲁塞尔 has one (ours since T237, with an Industrial Zone too), and
  a launch in the open sea costs the whole turn.
- Only naval units and embarked land units may enter coast and ocean tiles (`manual:469-471`); ocean
  crossing needs `TECH_CARTOGRAPHY`, held since before T220.
- **A blind `move` can embark a unit with no warning** and an embarked land unit's attack does not fire
  (T225: the order resolved as `MELEE_ATTACK` and the target read unchanged). Read the destination
  tile's own yield line - `F:1 P:0 G:1` is water - before any coastal move.
- **A landing unit cannot attack the turn it lands**: the movement is spent. Land on a tile the enemy
  cannot strike, and let the escort clear the lane first.

## Phase 1 - form the legion in a Harbour (组建)

1. **Read the establishment first** (`get_units`, `get_city_production`): at T237 it was siege 5,
   ranged 5, melee 3, cavalry 2, anti-cavalry 1, plus 圣女贞德 (Great General) and 周达观 (parked).
2. **Draw, do not rebuild.** The legion is an expeditionary slice of that: **siege 2-3** (Bombards, or
   Artillery if `get_city_production` offers the upgrade), **ranged 2** (Field Cannons), **melee 2**
   (Line Infantry - they take cities and, measured T236, they break walls), **anti-cavalry 1**
   (Pike&Shot, for enemy cavalry), **cavalry 1** (fast, can capture, and the legion's own eyes),
   **escort 1-2 naval**, and **圣女贞德 with the column if her aura can reach the landing** - her +5 CS
   and +1 movement are passive while she lives; **never activate her**.
3. **The port is a Harbour city** - prefer 布鲁塞尔 (Harbour, north coast, ours) - and the legion
   gathers there in one stack, on distinct tiles. Note in the diary each unit's port tile and the turn
   it arrives: the sea lane starts from that tile, not from wherever the unit was.
4. **Build only what the list above needs** and only in cities whose queues are not the war front or the
   science line. Four units is the cap; every one of them must have a stated role in the analysis.

## Phase 2 - cross and land (出海, 登陆)

1. **The escort leads and the transports follow**, one move per call with a `get_units` between: an
   embarked column has no defence and cannot shoot back.
2. **Choose the landing from the map, not from hope**: `get_map_area` radius 2 at the destination, and
   land on a tile out of enemy strike range; a city's ranged strike reaches two tiles.
3. **The first city taken is the beachhead**: `city_action keep` the same turn, its queue set, and a
   governor or garrison in it - a city on another continent with no garrison and no governor is a city
   that flips.
4. **No reinforcement route exists**: what sails is what fights. If the column lands under strength,
   that is a reason to write the verdict "cannot take it" rather than to attack anyway.

## Phase 3 - reconnaissance and the pre-war analysis (战前分析), the binding gate

1. **Gate 0 - is a candidate visible?** The four unmet majors have never been seen; a landing may be
   followed by several turns of cavalry scouting before any city is on the map. Report that honestly
   rather than assaulting the first thing that appears.
2. **Read the four numbers** - walls, pool, garrison (the city tile's own unit list, or our own attack
   list while it is fogged - that is how 布鲁塞尔's Builder garrison was found), ring - and name the
   source of each.
3. **Run `tactics/07`'s gates**: defenders by class and HP within two tiles; the turn count computed
   from shots that have landed; the cost; and **can we hold it** - loyalty, a governor, a garrison, and
   no reinforcements. **If the answer is "cannot take it", the legion does not assault**: it writes the
   verdict with the numbers that produced it, and either blockades, takes a weaker second candidate, or
   withdraws to the beachhead. **That verdict is a completed task.**
4. **A declaration is the verdict's consequence, not its substitute**: declare on the target only after
   the gates pass, then position that turn and attack the next - the combat engine does not sync on the
   declaration turn.

## Phase 4 - stage, then concentrate fire (攻城前集结后集火攻城)

1. **`get_staging_plan(city_x, city_y)` first, and write the table** - one row per unit: where it is, its
   movement, the one tile it goes to, the `get_pathing_estimate` cost, its arrival turn, its role, and
   whether it can fire from there. Calling the tool is not writing the table. The three staging rules:
   never two units on one tile, name the corridor, fill the **last** firing tile first
   (`prompts/tactics/04-staging-out-of-range.md` step 3b).
2. **The six measured overrides still bind** (018, re-measured at 020): a siege unit posted at d1 is
   refused; `arrive T+n` does not know our own units jam the corridor; a firing tile is a proposal until
   a shot from it succeeds; a shooter that spends its movement cannot shoot; entering a Zone of Control
   costs that turn's attack; a unit id is not durable across an upgrade.
3. **Concentrate**: every shooter in position fires the same turn, walls first and then the pool, and
   the **melee on d1 adds wall damage equal to a Bombard** while taking no retaliation - so the screen
   is a wall-breaker, not decoration. Nothing sits idle with a legal attack (`use-your-attacks`).
4. **Cut the supply line**, re-read the city a call later rather than trusting the immediate prose, and
   take the city with the d1 unit the turn the pool empties - `city_action` the same turn, one capture
   attack per tile per turn.
5. **Keep the escort between the enemy navy and the transports for the whole siege** - the Dutch, or the
   target's own ships, can end the expedition in one turn otherwise.

## Report when it is done - both endings

The legion's composition, port and the turn each unit reached it; the sea lane and the landing tile; the
target's four numbers with their sources and the `tactics/07` verdict; the staging table with its
overrides; the shots per turn and the tile each came from; the capture resolution and the tile the
capturing unit stood on; the cost in units, turns and gold; and the hold plan (governor, garrison,
queue, loyalty). **The "cannot take it" ending reports exactly the same numbers plus what would have to
change** - more siege, a different target, or a reinforcement route that does not exist yet.

## Why this is a file and not a turn-check rule

No metric the running server computes carries any half of this task: not "a legion exists", not "it is
on another continent", not "a verdict has been written". The checks read local metrics (`camps_within_3`,
a garrison on a tile), and a rule naming a metric the server does not compute reports `un-evaluable`
every turn. What no rule can hold - and what this file therefore exists for - is the human's
**conditional**: form the expedition, land it, analyse the target, **and let the analysis decide whether
the assault happens at all**.
