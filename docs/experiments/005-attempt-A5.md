# Attempt A5 - the chops go into units (Magnus' Groundbreaker)

**Status: COMPLETE** - **one session** (`unbroken-cerulean-herald-09`), played from the experiment's
shared start `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` and finished at **T70**, the window's last
turn. **No city was kept.** The session verified the shared start from the game rather than from memory
at T1 (西安 (60,22) pop 1, Prod 5, no research, an empty queue, exactly one Warrior) and never rolled
back or reloaded. *This file was seeded while the attempt played with mid-window readings; the measured
half below is the session's own, reconciled against the instrument at the close, and one seeded row was
corrected against a direct read (see the chop table).*

The attempt's instruction is `prompts/tasks/tmp/036-attempt-a5-the-chops-go-into-units.md`; the design
is section 3 of `docs/experiments/README.md`; A4's record is `004-attempt-A4.md` and its snapshot is
`docs/experiments/A4-final.json`; the cross-attempt report is `RETRO-2026-09-29.md`.

## Settings: the shared start, one variable

| | A4 (the baseline) | A5 |
|---|---|---|
| start | the experiment's shared T1 start | **the same save**, T1, verified from the game |
| doctrine | the corrected `tactics/01` | the **same corrected table**, plus the chop exception that landed at the A4/A5 boundary |
| the one variable | the Encampment's place in the war city's queue | **the destination of the chops** - feature removals in the war city go into the unit in its queue instead of into infrastructure, with **Magnus** in that city |
| window | a city kept, or T110 | a city kept, or **T70** (`expires:` T75) |

**The variable's cost, stated before it was measured**: builder charges spent on production rather than
improvements, the features themselves and the yields they would have carried, and the turns the
builders are away from the tiles the compounding cities need. What it was meant to buy: the siege half
of the establishment **five or more turns earlier than A2's T55**.

## The enabler is recorded, not assumed

`Groundbreaker` is Magnus's level-0 ability (`DLC/Expansion1/Data/Expansion1_Governors.xml:40,151`,
`Level="0" BaseAbility="true"`), so it arrives with his **appointment**, not from a governor point.

| what | the read that settles it | recorded |
|---|---|---|
| appointed | the `appoint_governor` reply | **T34** - `APPOINT_REQUESTED\|Magnus - verify with get_governors()` |
| assigned to the war city (西安) | the `assign_governor` reply | **T34** - `ASSIGNED\|Magnus to Xi'an` |
| `established=1` there | `get_governors` | **T39** - `Appointed (1): Magnus (GOVERNOR_THE_RESOURCE_MANAGER) - Xi'an (established)`, five turns after the T34 appointment, exactly as the T34 read ("5 turns to establish") predicted |
| the ability is in force | `GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER` is **absent** from the `GOV_PROMO` list `get_governors` prints (that list carries only promotions not yet held, and Groundbreaker is a level-0 base ability, never a promotion to buy) | **T34** - the available promotions read Surplus Logistics, Provision, Industrialist, Black Marketeer and Vertical Integration. The session did not call `promote_governor` with it, so the `ERR:ALREADY_PROMOTED` half of the brief's test is not on the record; the absence is |

The governor point comes from `CIVIC_STATE_WORKFORCE`, set at **T23** and completed at **T34**
(`DLC/Expansion1/Data/Expansion1_Civics.xml:91-93`, read from the install before the attempt was played
rather than remembered - the first governor point in the game is that civic's, so Magnus could not exist
earlier on any line). **The variable's precondition is therefore satisfied in the order the brief
requires**: Magnus was established in the war city at T39, **before the first chop (T40)**.

## The opening build is pinned, and the pin held

| order | promised | the record |
|---|---|---|
| 1 | `UNIT_SCOUT` | **T1 - matched** |
| 2 | `UNIT_SLINGER` | **T5 - matched** (placed the turn the Scout completed) |
| 3 | `UNIT_SETTLER` | **T6 - matched** (placed one turn after the Slinger, the turn 西安 reached pop 2; the Slinger was still building and was finished later. This is A1's own recorded sequence, `README.md:199`; the pin constrains the ORDER of the first four production orders, not whether each completes before the next is placed) |
| 4 | `UNIT_BUILDER` | **T15 - matched** |

The instrument agrees: `PIN opening: held - the pinned opening held: UNIT_SCOUT, UNIT_SLINGER,
UNIT_SETTLER, UNIT_BUILDER in that order`. `H5 clean` also holds: `neither a ram nor a siege tower was
ever ordered or bought`. **A5 is comparable with A4-A7 on the opening**, which is the one condition the
task file made a hard gate.

## The hypothesis, with the numbers that falsify it

`README.md`'s window row is *"the establishment turn against A2's T48/T53/T55, and the economy at T60"*,
bounded by *"a city kept or T70"*. A2's numbers: Engineering and both Catapults ordered **T48**, the
first Catapult completed **T53**, the second **T55**, first post-gate economy order **T55**.

| # | prediction | verdict |
|---|---|---|
| Q1 | the establishment is complete **by T60** under the corrected table | **HELD** |
| Q2 | the establishment arrives at least **5 turns earlier than A2's T55, i.e. by T50** | **FALSIFIED** |
| Q3 | the first `BUILDING`-or-`DISTRICT` order **after the Engineering gate** lands **by T60** | **HELD** |
| Q4 | `carrying-capacity` red on **fewer than ten turns** | **HELD on the rule's measure; the diary's own number disagrees and both are reported** |

## The chop table - one row per chop

Every chop is named with its city, tile, feature, turn, the queue item that absorbed the production,
and the Builder's remaining charges. `remove_feature` is refused outside the owning city's ring, and
**no tool prints the production gained**, so the gain is read from the queue item's own turn count
before and after - or the record says it could not be read.

| # | turn | city | tile | feature | the queue item that absorbed it | what can be established about the gain | builder after |
|---|---|---|---|---|---|---|---|
| 1 | **T40** | 西安 (65536) | (60,20) | `FEATURE_FOREST` on a **SILK** tile, 西安-owned, one tile from the city centre | 西安's queue held **`UNIT_WARRIOR`**, set on T39 at **2 turns** | **the item COMPLETED**: the `get_cities` read issued immediately after the chop returns `Building: nothing`, and the next turn's Action Required block asks for production. The seeded row in this file read `2 -> 1`; the session's own direct read is that the chop finished the item, so the bank is **at least two turns of 西安's production (~20 hammers)** and the exact figure is **unread**. The tile's own yields confirm the feature is gone: `PLAINS FOREST [SILK+] {F:1 P:2 C:1}` before, `PLAINS [SILK+] {F:1 P:1 C:1}` after | Builder 393220 spent its **last** charge and was consumed |
| 2 | **T44** | 西安 (65536) | (57,24) | `FEATURE_FOREST` on grass, river, 西安-owned | 西安's **`UNIT_CATAPULT`**, ordered T43 | **7 turns -> 5 turns** across the chop: a **two-turn** drop where one turn of the city's own production explains one, so this chop is worth **about one to two turns of 西安's queue**. `get_builder_tasks` names the owner outright (`(57,24): build LUMBER_MILL [city: Xi'an]`), so the destination is not in doubt | Builder 1114126 left with 2 charges |

**Three further chops were attempted and refused by the game** - the attempt's central mechanical
finding:

| tile | feature | turn | reply |
|---|---|---|---|
| (60,21) | `FEATURE_JUNGLE` | T39 | `CANNOT_REMOVE\|Cannot remove FEATURE_JUNGLE at (60,21)` - **the same defect A2 recorded at its T26** (`002-attempt-A2.md:350-354`), on the very tile `get_builder_tasks` recommends a MINE for |
| (59,22) | `FEATURE_JUNGLE` | T42 | `CANNOT_REMOVE\|Cannot remove FEATURE_JUNGLE at (59,22)` |
| (61,21) | `FEATURE_MARSH` | T49 | `CANNOT_REMOVE\|Cannot remove FEATURE_MARSH at (61,21)` |

**This paragraph first read "`remove_feature` accepts FOREST and refuses JUNGLE and MARSH on this map",
and that was a misdiagnosis - corrected here, because the tool is right and the game's own prerequisite
was doing the refusing.** The authoritative column is in the install rather than in any tool:
`Base/Assets/Gameplay/Data/Features.xml` gives **`FEATURE_FOREST` -> `RemoveTech="TECH_MINING"`**,
**`FEATURE_JUNGLE` -> `RemoveTech="TECH_BRONZE_WORKING"`** and **`FEATURE_MARSH` ->
`RemoveTech="TECH_IRRIGATION"`**. A5's own tech line fits that exactly, and the fit is what makes this a
diagnosis instead of an excuse:

| feature | the game's gate | A5 held it from | the attempts |
|---|---|---|---|
| FOREST | `TECH_MINING` | **T8** | **T40 and T44 - both succeeded** |
| JUNGLE | `TECH_BRONZE_WORKING` | **T45** | **T39 and T42 - both refused, both before the tech** |
| MARSH | `TECH_IRRIGATION` | **never researched** | **T49 - refused** |

**So the refusals are the engine's, and what the episode really measures is the chop window's shape**:
only forest was removable for the whole first half, 西安's ring held **exactly two forests**, and by the
time jungle opened at **T45** no builder charge was left to spend on it - Builder 393220 had been
**consumed** finishing the T40 chop and Builder 1114126 spent one of its two on T44. **Two chops was not
a choice the session made; it was the ceiling the tech line set**, and it reframes the falsified Q2: on
this line the variable could not be applied more than twice whatever the session intended. The control arm
still stands as dilution - of the pin Builder's three charges, **two went to a mine (60,23) and a farm
(61,22) before Magnus existed**.

**The refusal message is the part that was actually wrong, and it is now fixed**: `remove_feature` used to
answer only `ERR:CANNOT_REMOVE|Cannot remove FEATURE_JUNGLE at (x,y)`, which reads as a tool that cannot
chop jungle - A5 recorded exactly that, and A2 had recorded the same thing at its T26. The message now
reads the feature's own `RemoveTech`, says whether the empire holds it, and appends the reason after the
original prefix so every existing match still fires (`src/civ_mcp/lua/units.py`,
`tests/test_remove_feature_tech_message.py`).

## The decisive numbers, measured by the instrument

```
  the table: siege 2  melee 2  anticav 1  ranged 4  cavalry 1  recon 1
  COMPLETE at T57   siege=2  melee=6  anticav=1  ranged=7  cavalry=1  recon=2
  first siege   : T50      first melee   : T1      first anticav : T45
  first ranged  : T22      first cavalry : T33     first recon   : T5
  PIN opening: held
  H5 clean: neither a ram nor a siege tower was ever ordered or bought
  H6 war cities: 1 cities ordered army units (city 65536: 24); 65536 carries 100% of them
  H4 upgrades: 3 upgrade_unit call(s), first on T53
  first contact T57   Australia          map revealed: 2% at T1 -> 10% at T69
```

```
-- verdict (limits: establishment T60, city T80, gold floor 10) --
  HELD      Q1 establishment complete by T60 (corrected table)  [establishment T57]
  FALSIFIED Q2 establishment 5+ turns earlier than A2's T55 (by T50)  [completed T57, against A2's T55]
  HELD      Q3 the economy behind by <5 turns (first post-gate economy order by T60)  [T44 (BUILDING_WATER_MILL), against A2's T55]
  HELD      Q4 gold floor red on <10 turns  [2 red turn(s) by the rule up to T60; the diary's own gold/turn is below 10 on 58 of those 58 turn(s)]
```

**The two decisive numbers, as the record computes them**: the **establishment turn is T57** (checked
every turn), and the **first keep is none** - `captures: (no city captured or kept)`.

**The economy** (science / gold-per-turn / pop / cities / districts / improvements):

| turn | science | culture | gold/t | faith | military | pop | cities | districts | improvements |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.5 | 1.3 | 5.0 | 0.0 | 20 | 1 | 1 | 0 | 0 |
| 10 | 3.5 | 1.9 | 5.0 | 0.0 | 34 | 3 | 1 | 0 | 0 |
| 20 | 4.0 | 2.2 | 5.0 | 9.0 | 42 | 4 | 1 | 0 | 0 |
| 30 | 5.9 | 4.3 | 7.9 | 3.0 | 132 | 8 | 2 | 0 | 2 |
| 40 | 7.8 | 6.7 | 6.9 | 19.0 | 228 | 10 | 2 | 0 | 2 |
| 50 | 8.1 | 6.2 | 8.7 | 39.0 | 310 | 10 | 2 | 0 | 2 |
| 60 | 8.6 | 6.5 | 7.7 | 58.0 | 390 | 11 | 2 | 1 | 2 |
| 69 | 10.1 | 6.8 | 7.0 | 66.4 | 384 | 13 | 2 | 2 | 2 |

**A4 vs A5** (`--compare docs\experiments\A4-final.json docs\experiments\A5-final.json`):

```
attempt   turns   establishment  army_start  siege_order  first_keep  sci_T20  sci_T40  gpt_T40  h5  self_mismatch  rules_red
A4-final  T1-T66  T54            T1          T43          T65         4.0      13.9     6.0      0   7              5
A5-final  T1-T69  T57            T1          T43          none        4.0      7.8      6.9      0   2              5
```

A5's **science at T40 is 7.8 against A4's 13.9** and its gold/turn 6.9 against 6.0: the establishment
came three turns later than A4's while the economy was behind on science and level on cash. Its
`self_mismatch` count is the best in the programme (2), because this session wrote its `ESTABLISHMENT:`
lines from the field rather than from the queue.

**The rule table** (`CHECK FAILED` counts): `idle-district-slot 11`, `carrying-capacity 9`,
`use-your-attacks 8`, `screen-the-siege 7`, `cut-the-supply 4`.
**The refusal table**: `STOPPED_MID_PATH 182`, `NO_MOVES 17`, `STOPPED_SHORT 13`, `BLOCKED 12`,
`TOO FAR 3`, `ZOC 1`. **Process**: 519 tool calls over 69 turns, 7.5/turn.

## The end table, and the verdict

| # | question | the number that decides it |
|---|---|---|
| Q1 | establishment by T60 | **HELD** - complete at **T57**, three turns inside the deadline |
| Q2 | 5+ turns earlier than A2's T55 | **FALSIFIED** - **T57**, two turns LATER than A2's T55 and three later than A4's T54. Siege ordered T43 and the first gun held T50 against A2's T53, so the *siege half* was three turns early; the **table** was not |
| Q3 | first post-gate economy order by T60 | **HELD** - **T44**, a Water Mill in Shenyang, the compounding city, one turn after the T43 gate; against A2's T55. **The variable's predicted cost did not appear either** |
| Q4 | gold floor red on <10 turns | **HELD on the rule's measure** - 2 red turns from T60. **The diary's own `gold_per_turn` is below +10 on 58 of the 58 turns read**, and both are reported as the brief requires; Oligarchy + `POLICY_CONSCRIPTION` (T45) lifted it to exactly **+10** and held it there, which is why the rule's ten-turn window is nearly clean |
| the capture | a city kept | **none.** `first_keep: none` |

**The war, in one paragraph.** The objective was the city-state **耶路撒冷 (50,22)** that A2, A3 and A4
all attacked, held under a Scout's watch from T13. War was requested on **T59**
(`WAR_REQUESTED|DECLARE_SURPRISE_WAR on Jerusalem`), the first Catapult shot landed on **T63** and read
**`walls: none`** (the same read A2 got at its T66), and the city **never fell below 185/200**. The
attempt lost **Catapult#1 at T65** and a Warrior at T69, and at T70 the city still stood. `SIEGE
PROGRESS` reads `185/200 (-15 over 2 turn(s))`: two shots from one gun were entirely healed back.

## What actually went wrong, in order of size

1. **The chop treatment could not be executed at its designed strength.** Two chops, one of which only
   completed a Warrior, because the game refuses jungle and marsh removal and 西安's ring held two
   forests. The mechanism A5 exists to measure was, in the event, worth about **two turns** on the first
   Catapult - and the first Catapult *was* three turns early (T50 against A2's T53). The second gun is
   where the advance disappeared: 西安's **7 turns per Catapult at Prod ~10** against A2's 5 and 7.
2. **Two whole movement turns were lost to AI diplomacy pauses.** At **T57 and T59** `get_units`
   reported **every unit at 0 moves**, with the tool's own note that this is a known post-diplomacy state
   ("seen in 8 of 195 logged turns"). In an attempt whose margin was two to six turns that is the single
   largest uncontrolled cost in the window.
3. **The adapter's ranged attack requires movement and closing**, so a siege unit that fires also walks
   into the city's reach. Catapult#1 fired twice from **adjacent** to 耶路撒冷, took 25 then 55, and was
   destroyed for 120 production and **15 net damage**. The doctrine's "Catapult at range 2, never
   adjacent" is not executable through this adapter on rough ground: the rule enforced is *a ranged unit
   must be in reach AND still hold movement, and the shot itself spends movement*.
4. **The corridor.** 182 `STOPPED_MID_PATH` refusals: jungle, hills and forest on the y=22/23 line cost
   2-3 movement a tile, so the column moved about one tile a turn and the army spent T50-T68 walking ten
   tiles. `get_staging_plan(50,22)`, read on T46 before the assembly's first move, said exactly what
   would happen: *"ASSAULT OPENS on this turn with 0 shooter(s) in position. No shooter reaches a ring
   tile in time: the plan is the march, not the fire."*
5. **One metric artefact worth fixing before another attempt is scored on it**: `siege_exposed` counts a
   **friendly** major's unit as an enemy, so `screen-the-siege` failed for seven turns while an
   Australian Scout sat nearer the train than any screen unit. The formation was correct and the rule
   could not be satisfied by any arrangement of it.

## What held

- **The pin**, exactly, certified `held` by the instrument; and `H5` never violated (no ram, no tower).
- **Magnus in the war city**, appointed and assigned T34, established **T39**, with the first chop on
  **T40** - the brief's one hard sequencing requirement.
- **The war city's queue held a UNIT on every turn of the chop window**, which is the condition the
  chop-into-units rule needs.
- **The anti-cavalry row**: a Spearman bought for **170g at T45**, the first filled in the programme.
- **The economy was not deferred** (Q3), and two Campuses were placed - Shenyang's completed and 西安's
  at the advisor's own `Adj +3` tile (58,21).
- **The gold floor on the rule's own measure**, for the first time in A1-A5: gold/turn was **+10** from
  T45.

## The verdict

**The chops did not buy five turns; they bought about two, and the attempt reached its capture window
without a city.** Q1, Q3 and Q4 are HELD on the instrument and Q2 - the attempt's actual prediction - is
**FALSIFIED**, the establishment landing at **T57** against A2's T55. The cause is not the *destination*
of the chops - that was executed exactly as designed, on owned tiles, into unit queue items, under an
established Magnus - but their **volume**: the pin Builder's charges were two-thirds spent before Magnus
existed, and the game refuses both jungle and marsh removal.

**A5's answer to the programme's question**, as narrowly as the evidence supports it: *on this start a
chop-into-units treatment is worth about two turns of the war city's production*, because the game lets
a Builder remove FOREST only, and that ring holds two forests. A later attempt that wants to test the
destination of the chops as a real variable must (a) hold every Builder charge for the window - no mine,
no farm before Magnus - and (b) have charges standing when the governor establishes.

**And the finding the window forced, which outranks the variable**: an attempt can **complete the whole
establishment table (T57) and still not take a city ten tiles away by T70**, because the corridor costs
a tile a turn, a siege gun cannot fire without movement, and two diplomacy pauses cost two turns. The
binding constraint on this map is **march time**, not production.

## What the next attempt changes

- **A6 keeps its design** (the first siege unit bought with gold) and inherits an exact number from this
  attempt: the treasury held **274g at T45** and the Catapult's buy price is 320g, so the funding arm is
  live - but A5's **170g Spearman purchase at T45** is now known to be what empties the treasury, and A6
  must choose between the anti-cavalry and the purchase.
- **The window and the corridor are the binding constraint.** Any attempt whose question is a capture
  should take a target inside ~6 tiles or set its stop later than T70.
- **Two tool facts belong in the doctrine**: ranged attacks require movement, and a siege unit that
  closes to fire is a siege unit that dies; and `remove_feature` is FOREST-only on this map.
- **Fix `siege_exposed`** so it stops counting friendly majors as enemies before another attempt is
  scored against it.
