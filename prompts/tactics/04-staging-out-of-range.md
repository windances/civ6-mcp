# 4. Staging outside enemy range / 攻城前，城外攻击范围外的集结策略

Read when an assault is being planned and the stack is not yet formed.

## The rule

**Assemble outside the enemy's reach, then advance as one body.** A city's ranged strike reaches
**two tiles**, and so does a Catapult — the difference is that the city can absorb the answer and the
Catapult cannot. A column that arrives one unit at a time is defeated one unit at a time.

It is **one procedure in seven steps**, and the binding constraint is almost never the siege — it is
getting the siege there:

| Step | Question | Answered by |
|---|---|---|
| 1 | Where is the rally point? | the tile criteria below + `get_map_area` |
| 2 | **How long does the assembly take?** | `get_pathing_estimate`, per unit, slowest wins |
| 3 | What must be true before the column moves? | the completeness list below |
| 4 | How does the column move? | the march discipline below |
| 5 | **What if the column meets something before it is complete?** | the contact procedure below |
| 6 | Does the ring exist when we arrive? | the ring walk below |
| 7 | When do we go in? | the go/no-go below, and the declaration trigger |

## Step 1 — the rally point

A staging tile is good when it is:

- **three or more tiles** from the target city and from every visible enemy unit
  (`siege_city_distance_min >= 3` while staging; `siege_exposed == 0`);
- outside the reach of **any second enemy city** nearby — check for a second city before
  committing to the approach axis;
- **one turn's run from the ring**: no river crossing or mountain pass between it and the target,
  because the final advance has to happen in one turn, and a one-tile move can cost a unit its whole
  allowance (river, hill, marsh — five turns lost to this in the T103–T130 war);
- **not a lane a foreign unit is standing in.** At peace you cannot enter a tile held by another
  civ's unit, and it does not have to be a soldier: a Russian Missionary at (57,32) and an Egyptian
  Scout at (58,32) closed the x=57 lane for two full turns (T101) while a Catapult and an Archer sat
  and waited. Check `get_map_area` for whose units are parked in the corridor;
- **defensible**: hills, forest or across a river, so the stack can absorb a counterattack while
  it forms;
- **on roads** where roads exist, so reinforcements and the siege train arrive with movement left;
- close enough that wounded units can still reach it after healing.

## Step 2 — time the assembly; it is usually the longer pole

```
turns to assemble = the slowest unit's path cost to its RING tile, in movement points / its MP per turn
turns to break    = see file 7
the bigger of the two is the war's start date
```

Measure it **per unit and to the ring tile, not to the rally point**: a unit that reaches the rally
point and stops is not assembled, it is one turn short. `get_pathing_estimate` is the query; straight
line distance is not (hand-computed hex distances were wrong four times in one war).

**Stage the march, do not steer it.** The adapter stops a unit at its intermediate tile
(`STOPPED_MID_PATH`) and it stays there until it is ordered again, so a column that is "steered" every
turn costs one order per unit per turn — measured T128–T139, twelve turns of re-ordering ten units
before contact. Give each unit a **phase target** (rally → ring tile) and re-order only when it has
arrived; a phase that is still in progress needs no decision.

Measured anchor, T99–T105: 长沙 (52,30) to the staging row (54,37) is **11 movement points** through
a corridor whose first three tiles are 2-cost jungle — **six turns at 2 MP**, for every Archer and
Catapult in the army. The plan that said "the Catapults are 5–7 turns from the border" was right for
the Catapults and wrong for the timetable, because everything shared the same funnel.

Two consequences that decide whether the assembly finishes on schedule:

- **A narrow corridor serialises the column.** When one lane exists, units queue: the second unit
  cannot enter the tile the first is standing on, so it waits a turn. Count the lanes, and expect the
  column to need (units ÷ lanes) turns to pass a 2-cost stretch.
- **Arrive with fuel.** A unit that spends its last point reaching the rally point cannot fire, step
  into the ring, or capture on the following turn — `NO_MOVES|Ranged attacks require movement` is the
  message, and it cost three Catapult turns in one war. The assembly is complete when units are at
  the rally point **with movement left**, and the advance happens on the next turn.

## Step 3 — what must be true before the column moves

1. **The assault list is complete** first: **3 siege per city** (一城3投石车), 2 melee, 4 ranged,
   1 cavalry
   (`siege-train`, `ranged-mass`, `melee-screen`) — **no ram and no tower** (human instruction
   2026-09-26: 不用锤，用投石车). Staging
   with a missing role is how a war starts that cannot be finished.
2. **The composition is justified by THIS target.** Every Russian
   city in the T103–T130 war read `walls 0/0` from first contact to the last, so the Battering Ram —
   65 production, dragged across the map — did nothing for seventeen turns, and the Catapult is a
   damage tool rather than a wall-breaker. Read the walls (file 7, gate 4) before deciding what to
   bring; leave the ram at home when the answer is "no walls".
3. **Reinforcements already in motion.** The declaration waits for the formation, not the other way
   round: the directive's rule is that a war you cannot finish is a war you must not start.
4. **Full health.** A stack that arrives wounded spends the first two turns of the war healing; heal
   at the rally point instead, where nothing can reach it. The rates matter here: 20 HP/turn inside a
   city of ours, 15 in friendly territory, 10 neutral, 5 in enemy territory.
5. **Nothing left behind that matters.** An enemy left between the rally point and the target attacks
   the siege train from behind — clear the path, or leave a covering force and say so.
6. **A capture-capable unit with health in the plan.** Walking into a 0 HP city is a combat action
   (file 7, gate 3): whoever is nominated has to arrive unspent and above ~40 HP, and that unit
   should not be the one doing the attacking.

## Step 3b — the staging plan, written before the first move

**Human instruction, 2026-09-26: 在集结前，规划集结方案，不能被堵住，不同部队移动力不一样，找到最优集结方案后，才开始执行.**
No unit moves until this table exists. It is not a note in the diary's tactical line — it is the
order of march, written down, and it is what the 10-turn review quotes back.

| column | what goes in it |
|---|---|
| unit | type + id (ids change on upgrade — re-read after every `upgrade_unit`) |
| from | its tile **now**, from `get_units`, not from memory |
| moves | its movement allowance: Catapult/Trebuchet 2, Crossbowman 2, Tiger 2, Ram 2, Warrior/Spearman/Man-at-Arms 2–3, Horseman 4, Knight 4–5 (`PURSUIT` +1). **They are not equal, and the plan is wrong the moment it treats them as equal.** |
| to | one tile, and a **different** tile from every other unit's |
| cost | `get_pathing_estimate(unit_id, x, y)` — the game's own pathfinding. Never hand-compute: this war paid twice for that ((55,42) is not adjacent to (56,43); (54,41) is distance 3 from (56,43), not 2) |
| arrive | the turn it is there, counted from the pathing estimate |
| role | screen / melee / capture / siege / ranged |
| fires | yes / no / **unknown until a shot is ordered** — count only `yes` when you state the turn's expected shots |

Build it, then hold it to these three rules:

1. **No two units may be sent to the same tile.** A second order onto an occupied tile is refused
   `STACKING_CONFLICT` and the unit spends the turn where it was. A plan with a shared tile is not a
   plan, it is two wasted unit-turns and a re-plan next turn.
2. **The corridor is the binding constraint, so the plan must name it.** Approaches are one or two
   tiles wide — the 圣彼得堡 approach was the `(56,40)→(56,39)→(57,38)` corridor between mountains and
   the river, and on T155 that produced, verbatim, “`Catapult 1769485` and `Xbow 2752533` fortified in
   place because the corridor is jammed”. Two answers, and the plan picks one deliberately: **stagger
   the arrivals by one turn** (the unit that cannot fit stays at the rally point and moves next turn),
   or **route the surplus round the far side**, which is also the order that cuts the city's supply
   line. Queueing in the corridor and hoping is the third option and it is the one this war took.
3. **Optimise the turn the siege opens, not the first arrival.** The plan is optimal when the *last*
   firing tile is occupied and the screen is in front on the same turn — that is the first turn the
   train fires as a train. Concretely: reserve the distance-2 tiles for shooters, keep at least one
   adjacent tile for the capture unit (our own stack is the usual thing standing on it), put the
   screen on the tile nearest the enemy, and move the shooters that have **≥2 movement points left
   after arriving** so they can fire the turn they land. A shooter that spends both points walking
   fires next turn — measured four turns running, T155–T158.

**A unit with no tile in the plan is not left idle.** It is given the rear of the ring: occupying the
hexes the city still draws its supply line from (the `SIEGE PROGRESS` block counts them — 沃罗涅什
`3/6`, 喀山 `1/6`). That is how the same army both cuts the ~20/turn heal and stops queueing behind
itself.

### 3b-2 — what the surplus does (human instruction 2026-09-26: 攻城部队确定后，如果还有多余部队，如何安排)

One city's assault needs **3 siege, 2 melee, 4 ranged and 1 cavalry** (the directive's
establishment; `get_staging_plan` counts the cavalry inside the melee bucket, because both are
capture-capable front-line units). Everything above that is surplus, and surplus is spent in this
order — it is a ladder, not a preference:

1. **The supply hexes.** The manual's rule is that a city heals while *any* adjacent hex is outside
   our zone of control, and a hex is cut when one of our fighting units stands **on it or beside
   it** — so one unit covers up to three hexes and **three units close a six-hex ring**. Measured:
   our sieges left it at `3/6` and `1/6`, and both cities healed back to full. This is first because
   it is the only job that makes the siege's own fire count.
2. **The road the enemy's reinforcements use.** Russia rebuilt from 13 military to 105 during this
   war and produced a Man-at-Arms that took our Knight from 52 to 6 in one blow (T151). A unit on
   the approach kills them one at a time instead of letting them arrive together.
3. **Depth behind the ring, out of the city's two-tile strike.** Not decoration: the stack loses a
   screen unit every few turns (T154: our only Horseman died attacking the city), and a replacement
   already standing behind the ring keeps the shooters at full fire.
4. **The garrison of a city we have just taken** — one unit, no more (`one-garrison-per-city`), and
   it is what `hold-what-you-take` asks for. 阿斯特拉罕 needed it at −23.5 loyalty/turn; 成都 was
   raided precisely because it had none (T153–T155).
5. **Pillage, with cavalry.** Cavalry ignores zones of control, so it is the one unit that can reach
   the enemy's Lavra, mines and roads behind the front. Russia's faith comes from its Lavra:
   pillaging it stops the stream at source, worth more than any number of missionary kills.
6. **Nothing is last.** A unit with none of the above is still not parked: it joins the depth line or
   it is re-tasked to the next objective. “Fortified in place because the corridor is jammed”
   (T155, verbatim) is a queue, not a plan.

**Who may take a ring hex, and who may not.** Those hexes are *adjacent* to the city, so they are
inside its ranged strike: send **melee, anti-cavalry or cavalry** — units that can take a hit, and
whose presence is also what creates the zone of control that does the cutting. Never send ranged or
siege units to a supply hex (a walled city's strike destroyed a 55 HP Horseman outright at T154),
and never send a Builder, Settler or Trader near an enemy city. Two operational notes: a unit
standing on a supply hex that also holds the enemy garrison can be listed by `use-your-attacks` (the
adapter counts the city tile's unit as a target) — attack if there is a legal attack, otherwise
record the refusal in the diary; and walking to a supply hex spends the move, so the hex is taken
**before** the turn the fire matters, never during it.

## Step 4 — the march

- Move in formation, not in a queue: the screen leads, the ranged and siege follow within one
  turn of it, and nothing arrives alone.
- Keep every unit inside the reach of the stack. A unit that outruns the others is the one that
  gets attacked (`answer-the-attack`).
- **Route around enemy units, because their zone of control eats the whole turn.** The manual
  (`ZONES OF CONTROL`, p.73): "When a unit moves into a tile within an enemy's ZOC it expends **all
  of its MPs**. Cavalry units are the exception." So stepping into the hex next to an enemy is not
  a cheap detour — it ends that unit's movement for the turn, even if it never intended to attack.
- **Our cavalry is the exception too, and that is a tool.** Cavalry ignores enemy ZOC: it can slip
  past a front line to reach the enemy's siege and ranged units, cut a supply hex, or pillage the
  tiles the target city depends on. That is the same property that makes enemy cavalry dangerous to
  us (`counter-the-cavalry`) — use it instead of only defending against it.
- **Contact outranks the timetable, and during an assembly it has its own procedure: step 5.** The
  moment a unit discovers an enemy or is attacked, the answer is step 5 first and the march second.
  A city is patient; a Catapult that walked past an enemy is not.
- Re-check on arrival: if the enemy has reinforced the city or moved a field army into the
  approach, the rally point is a decision point again, not a formality.

## Step 5 — contact before the stack is complete

The march discipline above describes the **last** turn, when everything arrives together. During the
assembly it cannot: units arrive one at a time — that is what an assembly is — so the column has a
front and a tail, and the enemy decides which of them it touches. Three answers, in this order. The
measured sequence T103–T106 is what it costs when they are not asked.

**1. Does the contact invalidate the rally point?** The rally point was chosen against the enemies we
had *seen*, and reconnaissance keeps finding the field army after the choice was made. T99 chose the
row (53,37)/(54,37)/(55,37) at three-plus tiles from Moscow; T100 found the Russian Archer at (52,38)
reaching (53,37) at distance 2 and a CS 35 Swordsman at (53,40) that could move 2 and strike — half
the row was inside an enemy's reach on the turn the plan named it. So re-run step 1 against the
**field army**, not only the city, every turn the snapshot changes, and move the rally point while
moving it is still free. A row that is safe only because the enemy is not currently looking at it is
not a rally point.

**2. Can the units already forward kill it without spending a ring tile?** This is a kill, not a
detour, and the price is paid in volleys. T104: a 那烂陀 Warrior walked onto our launch pad at
(53,37); two Archers shot it (28 from (53,35), 22 from (52,36) — it survived both) while a third put
52 into the Russian Archer at (52,38), and the first volley on Moscow slid from T105 to **T107**.
Three rules keep that bill small:

- **The screen takes the contact; the shooters shoot; the siege does not.** Melee, anti-cavalry and
  cavalry answer. A siege unit is nearly helpless against a unit and never holds a front tile.
- **A shooter fires from the tile it is already standing on, with LOS — it does not walk to a firing
  position on a contact turn.** T105: the finishing shot at a 12 HP Archer was ordered from (53,35),
  answered `NO_LOS`, and the retry **walked the unit instead of firing**, so the Archer survived,
  healed, and got its own turn. Order one shot and read the refusal; never discover LOS by walking.
- **An attack is the unit's whole turn** — the manual (p.81): "Most units use up all of their
  movement when attacking". Answering contact therefore suspends that unit's march, so the *wrong*
  unit answering costs a turn of the timetable, not merely a turn of HP. Give the contact to the
  unit whose arrival the assembly can most afford to lose; that is the screen, not the siege or the
  archer that is one tile from its ring pad.

**3. Does the timetable now belong to the enemy?** Yes, from the moment they declare — and they
declare **on the assembly**, not after it. T103: Peter's border complaint arrived, the refusal was
taken as the answer, and Russia declared with our army two turns short of its row. From that turn the
procedure is files 02 and 03 and the assembly continues **under fire**; what changes is the order of
work — **clear the field first, then fill the pads and fire.** T106 killed the last two enemy units
in contact (a 33 HP Archer killed a wounded Russian Archer and took nothing; a Warrior finished the
那烂陀 Warrior) and T107 was the first volley on the city. Arriving together is no longer available
once contact starts, so arrive in the order that is still useful: pads go to whoever is nearest, and
shooters fire from where they stand.

Two more shapes of contact belong here, because they are different decisions:

- **The enemy has taken a rally tile.** The sharpest form of contact in an assembly, and it is a kill
  rather than a re-route: **you can move a column, you cannot move a ring.** A usable distance-2 tile
  of the target in the enemy's hands is worth two attackers' turns to take back, every time.
- **A foreign unit is standing in the lane, at peace.** That is contact too, and it cannot be
  attacked. T101: a Russian Missionary at (57,32) and an Egyptian Scout at (58,32) closed the x=57
  lane outright — a military unit may not enter a tile held by a foreign unit at peace — which left a
  Catapult the choice between waiting and the western route at 21 MP against 13. Re-route, count it
  in the LANES line, and do not declare a war over a missionary.

**The bypassed enemy is this rule, not a separate one.** "Clear the path first" is not advice about a
later turn: the unit you walked past moves at your speed, the siege train is at the tail, and the
Battering Ram and a Warrior were lost on consecutive turns (T109–T111) while the column was still
not formed.

## Step 6 — the ring walk, on arrival and before the advance

A siege fires as many shots as the **firing ring** allows, not as many as the army has units. Walk it
before the declaration and again the turn the stack forms:

1. **List every tile at distance ≤ 2 from the city** and mark which are passable. Mountains are not:
   measured T113, two of 圣彼得堡's ring tiles ((57,41), (54,42)) answered
   `BLOCKED (impassable mountain)`, and at 阿斯特拉罕 the whole east side was mountains, so for most
   of that siege only three shooters could fire at once while six stood idle. Moscow's ring had six
   usable tiles and the siege went twice as fast.
2. **Test line of sight per tile, per unit.** LOS is not distance: (53,35)→(52,37) was refused
   `NO_LOS` while (52,36)→(53,37) at the same range went through, and a Catapult refused (54,40)
   from (55,38) yet fired from (52,38) (T107). A tile is only a firing position once a shot from it
   has been *ordered* and not refused.
3. **Assign tiles by role, and keep the two sets apart: melee goes ADJACENT (distance 1) to the city,
   shooters go on the ring (distance 2), and at least one adjacent tile stays free for the capture
   move.** Our own stack is the most common obstacle to our own ring: at 阿斯特拉罕 the shooters
   occupied both adjacent tiles — the only ones the melee could have used — and the assault had no
   unit able to reach the city until they moved.
4. **Write the order of arrival down** — which unit takes which tile on which turn — because the
   move-cost arithmetic above decides whether the ring fills in one turn or three.
5. **Count shots, not units. This is the measurement the whole step exists for.** Three siege units
   is a roster; the city only feels the ones inside range 2 with LOS. Measured over the T139–T159
   war: 阿斯特拉罕 had **one** distance-2 tile with LOS out of three candidates, 沃罗涅什 fired from
   two, 圣彼得堡 spent T151–T152 with **one** siege unit in range while the other two stood at
   distance 4 and 6, and 喀山 opened on T159 with all three at distance **3, 4 and 4** — zero shots.
   `SIEGE POSTURE` now ends with a `SIEGE FIRE: n/m siege units inside range 2` line and names the
   out-of-range ones: **read it before writing the turn's plan, and if n < m the plan is to walk the
   others in, not to fire again.** A unit that spends its move arriving fires **next** turn — a
   two-tile move, a river crossing or a hill each cost both movement points (measured four turns
   running, T155–T158: `NO_MOVES|Ranged attacks require movement`), so a shooter either starts the
   turn in the ring or is a turn late by construction.
6. **Fill the ring from the rear, and give the spare units the far side.** Two things follow from a
   ring that is one tile wide. First, **the heal**: an enemy city heals ~20/turn while any adjacent
   hex is outside our zone of control, and the `SIEGE PROGRESS` block counts it — 沃罗涅什 read
   `supply line 3/6 cut` and 喀山 read `1/6` on the turn it was first fired on, which is why both
   pools came back. A unit with nothing to shoot at is not idle: send it round the back to occupy
   the uncut hexes. Second, **the jam**: the corridor at 圣彼得堡 was so narrow that on T155
   `Catapult 1769485 and Xbow 2752533 were fortified in place because the corridor is jammed`, i.e.
   two shooters spent a turn queued behind their own army. Approaches are one or two tiles wide;
   send the surplus round the other side on the *march*, not on the turn the ring has to be filled.
7. **Do not bring the ram or the melee forward piecemeal to fill a gap.** A bare melee attack did
   **9** against 100 walls (T150) where the same attack beside the Battering Ram does full damage,
   and a 55 HP Horseman attacking a walled, garrisoned city was destroyed outright (T154) — the
   ring is filled by units that can survive on it, in the order that lets them support each other.

## Step 7 — the go/no-go

Advance when all of these are true in the same turn:

- the shooters are on ring tiles **with movement left**, or one point from them;
- a capture-capable unit is adjacent (or one point from adjacent) and unspent;
- the walls answer is in position, if the target has walls;
- the field army in contact is dealt with (step 5, and files 2 and 3).

**The declaration trigger, measured T103:** massing on a border is what starts the war. Peter's
border complaint arrived the turn the column closed on his frontier, the refusal was taken as the
answer, and Russia declared with our army **two turns short** of its staging row. So treat "the enemy
declares when they see the stack" as the expected case: build the rally point where the army can
already fight from where it stands, not where it would like to be in three turns. A rally point that
is only safe *because* the war has not started is not a rally point.

## Prohibitions

- Do not begin the approach from inside the city's strike range; stage first, then move.
- Do not stage where the stack is split by a river or a mountain on the final approach.
- Do not stage adjacent to a barbarian camp or in reach of a second enemy city.
- Do not put two **military** units on one rally tile: the adapter refuses it with
  `STACKING_CONFLICT|... Cannot stack same formation class` (measured T132 — the Man-at-Arms was
  refused onto (55,36) because a Catapult stood there). Melee and siege each need their own tile;
  only a **support** unit (the ram) may share a tile with a military one, and that is how it is
  meant to work. When the rally row is written down, give every military unit its own hex.
- **Do not assume you choose the start date.** Twice now (T103 on the abandoned branch, and T139–T140
  on this one) forming up inside the enemy's sight produced **their** declaration while our line was
  still one or two turns from complete — the Archer appears, the war starts, and the first turn is
  spent re-screening instead of firing. Either assemble out of sight and advance as one, or accept the
  enemy's timing and make the arrival order defensive (melee front, siege behind, screen already in
  place). Both are plans; drifting into contact is not.
- Do not stage with the siege train in front or unscreened, even at a safe distance — the
  formation is file 5.
- Do not drag the ram toward a city read as `walls none`: it only helps melee against walls, so it
  earns its place beside a walled target and stays behind otherwise. The ram we own **does** come on
  the march (human instruction 2026-09-26: 已经有攻城锤，就参战), but no tower and no second ram is
  built (same day: 不用锤，用投石车).
- Do not order a unit to fire on the turn it must spend two points to enter the ring: it arrives with
  nothing left, and the attack is refused.
- Do not keep the army parked at the rally point once the formation is complete: an assembled
  army that does not advance is paying maintenance for nothing.
- **Do not answer contact during the assembly with the unit whose arrival the assembly needs most.**
  The screen fights; a shooter that walks to a firing position on a contact turn loses both the shot
  and the pad it was standing on. T105 traded a 12 HP Archer kill for a wasted Archer turn.
- **Do not abandon a rally tile the enemy has walked onto.** Take it back — a distance-2 tile of the
  target is not replaceable the way a march route is.
- **Do not let a contact turn consume a ring tile.** Every shooter that steps off the ring to chase
  something costs a shot on every following turn of the siege, not one shot.
- **Do not declare war on a foreign unit parked in a lane.** At peace it cannot be attacked anyway;
  re-route and add it to the LANES line.
- Do not treat a stalled assembly as a march problem when it is a contact problem: if units that
  should be walking are not, read the snapshot for an enemy that is standing where they are going.

## What to report

```
RALLY  (x,y) — distance to the city n, to the nearest enemy unit n, second city within reach: yes/no
FUEL   slowest unit n tiles / n movement points / n turns out (path, not straight line)
LANES  n lanes through the corridor; tiles held by foreign units: <list or none>
READY  assault list: siege n/2, melee n/2, ram n/1, ranged n/4, cavalry n/1
       composition justified: walls <n/max or none> -> ram needed: yes/no
HEALTH units below full: <list with HP and where they heal>
RING   n usable tiles at distance 2 of m checked; assigned: <unit -> tile>; free tiles: n
CONTACT whoever is in contact, what killing it costs (which units, how many turns off the
       timetable), whether the rally point still holds, and which comes first: clearance or advance
GO     advance this turn: yes/no — <the one thing missing, if no>
```

If the snapshot does not show terrain or fog around the proposed tile, say so and propose a check
rather than assuming it is safe.
