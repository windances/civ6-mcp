# TEMP TASK 024 - take Brussels: 战前分析, 攻城集结, then the assault

added:     2026-09-28 (human instruction: 占领布鲁塞尔)
expires:   turn 241 - 21 turn(s) from T220, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **Brussels is ours** - the tile at its own (x,y) reads `[CITY_CENTER]` owned by 中国 with one of our
           units standing on it (`hold-what-you-take`), 布鲁塞尔 appears in `get_cities`, and
           `get_city_states` no longer lists it (its player id read as 19 at T220). The diary
           carries the ledger: the four numbers re-read at war and which of them came from a probe
           attack, the staging table with its overrides, the shots per turn and the tile each shot
           came from, the cost paid, and the hold plan. Retire it as
           `024-take-brussels-done-T<n>.md` the turn the city is ours.
overrides: **the directive's city-state rule, for this one city, on the human's instruction.** The doctrine
           says city-states are not conquest targets and may be attacked only for a stated reason;
           **the human has said otherwise for 布鲁塞尔, and that instruction is the reason of record** -
           the diary records it as such and invents no strategic justification, exactly as 016 did
           for 埃里温. What it unlocks: war on **player 19 and nothing else** (not the Netherlands' own
           cities, not 喀布尔, 格拉纳达 or 哈图沙, not a barbarian camp) and the **siege train plus one melee
           capture unit lent to it**. **It does not override**: `one-garrison-per-city`,
           `use-your-attacks`, `hold-what-you-take`, the directive's ban on `propose_peace` (the
           Dutch war still ends only by taking their cities), the housing and science lines outside
           the cities the assault needs, or the standing 'no new unit' line - the establishment
           already exists (siege 5, ranged 5, melee 3, cavalry 2 as read at T218).
scope:     布鲁塞尔, its ring, any unit the Netherlands levies out of it, the train lent to it, and the route to
           it. Not the Netherlands' own cities (each is its own decision under the directive), not
           another city-state, not a barbarian camp, and not a second front.

## What is known at T218, and the one call nobody has made on this branch

| fact | reading | source |
|---|---|---|
| the city | **city-state 布鲁塞尔 at (69,29)**, player id **19**, **Industrial** (suzerain bonus: +15% production towards wonders in all our cities) | measured on this same T218 save by the previous branch: T219 reconnaissance, T220 `assign_governor` refusal naming id 19, and the game's own files (`Gameplay/Data/Civilizations.xml`) |
| its suzerain | the **Netherlands** - and it is already at war with us (state 6, grievances -66) | T218 diary `diplo_states` |
| so, a declaration? | **none needed**: a city-state follows its suzerain's war state, and the Netherlands is at war. Confirm it with one read rather than assuming it - a refusal that says `NOT_AT_WAR` is the correction | manual `manual:1969`; the previous branch measured the border refusal as `enemy territory` at T231 |
| the four numbers | **never read on this branch** - no walls, pool, garrison or ring figure exists for it here | - |
| our train | **5 Bombard, 4 Field Cannon, 3 Line Infantry, 1 Crossbowman, 1 Cuirassier, 1 Cavalry, 1 Spearman**, plus 圣女贞德 (Great General, aura kept alive - never activate her) | T218 diary `unit_composition` |
| the treasury | **274.5 gold at +14.4/turn**; stockpiles COAL 14, IRON 60, HORSES 60, NITER 60 | T218 diary |
| the discount card | `POLICY_PROFESSIONAL_ARMY` is **not slotted** (Medina Quarter holds the slot), so every upgrade costs double - 310g where 155g would do | T218 diary `policies` |
| the objective's history | **this exact city fell in five turns** on the branch that was abandoned: task added T232, staging plan T234 (8 placed of 9), 13 attacks over T235-T237, `KEEP|布鲁塞尔` at T237 | `prompts/tasks/tmp/done/020-take-brussels-done-T237.md` |

**Two things follow, and both decide the plan.**

1. **The war is already on, so the assault has no declaration step** - but that also means it has no
   exit: the directive forbids peace, and a city-state will not accept one while its suzerain is at
   war with us (`manual:1959`). A half-done assault leaves levied units on our border for the rest of
   the match, which is why the deadline below is a hard stop rather than an intention.
2. **Reconnaissance is not optional even though the city's coordinate is known.** The coordinate is
   from a previous branch's reading of this same save, and a coordinate copied from an old diary has
   already been wrong once (`done/001-clear-the-camp-done-T84.md`). Read it again, and read the ring
   that will hold the train.

## Gate 0 - reconnaissance (侦察), before any move

1. **Read the coordinate and the type this session**: `get_map_area` radius 3 around (69,29) for the
   ring, the terrain and the supply hexes; `get_city_states` for its type and our envoys there.
2. **Read the four numbers, naming the source of each**: walls / HP pool / garrison (the city tile's own
   unit list - or our own attack list while the tile is fogged, which is how 布鲁塞尔's Builder garrison
   was found at T235) / ring. A city-state's figures have to come from the tile read and from **result
   lines**, because `get_diplomacy` lists civilizations and not city-states.
3. **Probe the walls rather than budgeting from a guess.** A city's tile can print `[fog]` while its
   whole ring is visible, and its wall number comes from the **first melee attack's own result line**
   (T235: `walls: 200/200, city hp: 200/200`).
4. **GROUND gate - land or water?** 布鲁塞尔 is on the north coast. If the only approach is by sea, the
   train needs a **lane clear of the Dutch navy** first: an embarked siege unit cannot make a ranged
   attack at all (T225) and a blind `move` embarks with no warning - the destination tile's own yield
   line (`F:1 P:0 G:1`) is the only tell. Report a water-only approach as a blocker rather than
   drowning the train.
5. **Expect a levy.** The suzerain can pay to take control of a city-state's units (`manual:1971-1973`),
   which is how 埃里温's Man-at-Arms came onto our ring. Levied units die when the city falls, so they
   are a cost to absorb: a Bombard **cannot attack them at all** (`ERR:SIEGE_CANNOT_ATTACK_UNITS`) and
   they are the Field Cannons' and the melee's work.

## 战前分析 - the gates, once it is visible (tactics/07)

1. The four numbers above, each with the source that produced it.
2. Defenders by class and HP within two tiles, and the counter for each.
3. The turn count **said out loud from shots that have landed**, not from the plan - and re-count the
   deadline below from the first `get_staging_plan`, saying in the diary whether T239 still holds.
4. Can we hold it? The city arrives with an empty queue (an end-turn blocker), and a governor or a
   garrison goes in the turn it falls (`hold-what-you-take`), with its queue set the same turn.
5. **Write down what the capture deletes**, so the ledger shows it was known: the +15% wonder production
   for both sides, our envoys there, and the Netherlands' suzerainty over it. The human's instruction has
   accepted that price and is the reason of record.

## 攻城集结 - the staging, in this order

Run **`get_staging_plan(69,29)`** and write one row per unit - where it is, its movement, the one tile it
goes to, the `get_pathing_estimate` cost, its arrival turn, its role, and whether it can fire from there -
**before the first `unit_action`**. Calling the tool is not writing the table.

The **four** staging rules and the **six measured traps** this map has already paid for are
`prompts/tactics/04-staging-out-of-range.md` step 3b and step 3b-1 - read them there rather than from
memory. Three of them decided the last assault on this city:

- **Issue the calls furthest-first.** The plan prints the order; 232 `STOPPED_MID_PATH` results across
  T228-T299 came from columns queueing behind themselves (T234: eight units ordered, eight stopped one
  to three tiles short).
- **A siege unit at d1 fires** - the old "d1 is refused" note is corrected; what holds is that a **d2
  tile is not a d1 tile for the capture move** (T237: `STOPPED_SHORT ... 2 tiles away`).
- **A shooter that spends its movement arriving cannot fire** (`NO_MOVES|Ranged attacks require
  movement`, T236).

## 攻城执行 - the fire order

1. **Walls first if there are any, pool second**, and take the wall number from the first melee attack's
   own result line.
2. **The melee on d1 is worth a Bombard against walls**: at this city a Cavalry attack took the wall
   pool `126 -> 76` - 50 points, the same as a Bombard - and took no retaliation (T236).
3. **Record each shot's `city hp:` from its result line, then read the city again a call later.** The
   immediate post-combat prose is stale even when the damage landed (T236/T237: `damage dealt:none read`
   beside a pool that had clearly moved).
4. **Cut what heals, and price the hex against the shooter.** A city heals about twenty points a turn
   with an open supply line; cutting a hex is worth about that, and the unit that walks there gives up
   its own 40-100. When the pool is falling, keep firing and record the accepted partial cut
   (`prompts/tactics/06`, measured at 哈勒姆: 3/6, pool 200 -> 20, never once up).
5. **Take it with the d1 unit the turn the pool empties** - that attack takes the city and moves the unit
   in, so resolve it with `city_action(city_id, "keep")` the same turn or the turn will not end, and make
   **one capture attack per tile per turn** (a second attack after the flip hits our own city, T216).
6. **Every shooter that can bear fires the same turn** (`use-your-attacks`); nothing sits idle with a
   legal attack.

## Hold it, and report

Governor or garrison the turn it falls, set its empty queue the same turn, and report: the four numbers
with their sources, the staging table with its overrides, the shots per turn and the tile each came
from, the capture resolution and the tile the capturing unit stood on, the cost in units and turns, the
loyalty reading afterwards, and what the capture deleted (+15% wonder production, our envoys, the Dutch
suzerainty). If it expires, say where the train stood, what the city read, and what blocked it.

## Why this is a file and not a turn-check rule

Every mechanical half already has a rule or a tactic - `siege-train`, `screen-the-siege`,
`mass-on-contact`, `take-the-city`, `hold-what-you-take`, `use-your-attacks`, `finish-the-wounded`,
`cut-the-supply`, and `tactics/07` for the analysis. What no metric carries is **that this city is an
objective at all**: the standing doctrine says a city-state is not a conquest target and may be attacked
only for a stated reason, the human has said otherwise for 布鲁塞尔, and that reversal has to travel to
the turn loop as a file with the instruction written in it as the reason of record.
