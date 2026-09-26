# TEMP TASK 012 — the pre-war analysis on 诺夫哥罗德, Russia's last city (最后一个俄罗斯城市的战前分析)

added:     2026-09-26 (human instruction: run the pre-war analysis on the next target)
expires:   turn 175 — counted from the queue, not the calendar. The probe is one turn, the march from
           喀山's ring is six tiles, and the wall phase is one or two volleys once the firing ring is
           held: ~T166 for this analysis to have turned into fire, plus three slips of the kind already
           measured twice (T159's eight-order batch, T161's). 007's own horizon is T185, so this file
           must not outlive the point where only 007 is left. Retire it as
           `012-novgorod-pre-war-analysis-done-T<n>.md` the turn the first volley lands, or as
           `012-novgorod-pre-war-analysis-expired-T175.md` with the four numbers as far as they were
           read and the reason the train never fired.
done when: **诺夫哥罗德 (61,42) is read in its four numbers and the train is firing at its walls** —
           `walls` strictly below the 100 it reads now, from a result line and not from an estimate,
           with the four numbers (garrison / walls / HP pool / ring) written in the diary's `tooling`
           line; or 007's own done-when closes it first because the city fell, in which case report the
           same four numbers and the turn it fell. The reading is the deliverable: the analysis is
           finished when the correction to `city hp: N/200, walls: N/100` has been ordered and seen.
overrides: 007's timetable for the units in this train, and only in the direction of arriving together
           (`tactics/04`) instead of firing piecemeal. It authorizes **no** new declaration (we are
           already at war with Russia), **no** peace, **no** attack on Yerevan or Egypt, and it takes
           **nothing** from the 成都 ring — 011 outranks this file for those units.
scope:     one city, 诺夫哥罗德 (61,42), pop 2, `walls 100`, Russia's last. The wall phase only: the
           four numbers, the five gates of `tactics/07`, the firing ring, the Battering Ram, and the
           supply hexes. The 成都 ring (011), the Niter city (009) and the missionaries (008) are not
           this file's business, and nothing here touches the home front's build queues.

## What is already read, and the one number that is missing

| # | Number | Reading | Where |
|---|---|---|---|
| 1 | **Garrison** | **none** — a Builder and a Great Writer are the only occupants, so no CS is added to the city's defence | T161 diary; `get_diplomacy` line |
| 2 | **Walls** | **100** | `get_diplomacy` city line, T161: `诺夫哥罗德 pop 2 (61,42) walls 100` |
| 3 | **HP pool** | **not read** — no shot has landed on it; a city's pool is 200 and it is the denominator, not the question | missing |
| 4 | **The ring** | 18 tiles within 2; the T161 plan assigned 3 shooters to `(59,43)` d2, `(60,40)` d2, `(60,42)` d1 | `get_staging_plan(61,42)`, T161 |

Also read, and not a number: `loy 100 (-3.7/t)` — Russia loses about 3.7 loyalty a turn there, so the
city revolts to a Free City in roughly **27 turns** (T189). That is *past* 007's T185, so the deadline
is compatible; it is the reason the wall phase is a one-pass job and not a slow grind, because a Free
City would end the war and leave a Russian city standing in everything but name.

## The gate run, with the arithmetic this army actually has

**Gate 1 — net fire > 0.** 3 Trebuchets at 45–55 a shot is **135–165 gross per turn** against a city
that heals ~20 a turn while it has a supply line — the T161 plan puts the supply line at **3/6 cut**,
so cut the remaining hexes and the heal is 0. Either way the net is strongly positive (115–145), and
the Crossbowman that fires from `(60,44)` d2 adds ~21–35 more. **This gate passes on paper; the
`SIEGE FIRE` block is what proves it in the game**, and it is the block measured to stay silent while
the whole train is beyond city-distance 3 (`end_turn.py:1102`) — so read the per-unit `city N` line
instead of waiting for it, and say plainly which shooters are inside range 2.

**Gate 2 — the ring can hold the shooters.** The plan's d2 tiles are the claim; a tile is a firing
position only once a shot from it has been ordered and **not** refused (阿斯特拉罕's `(55,38)` was
distance 2 with `NO_LOS`). Fire the first shot from the assigned tile before moving the other two onto
theirs, so one refusal costs one unit-turn and not three.

**Gate 3 — a capture-capable unit adjacent at the start of the turn the pool empties.** The plan
assigned MaA #2424835 to `(60,43)` d1 and the Spearman #1572878 to `(61,43)` d1, both `T+1`. Two
measured rules apply, both learned the hard way: a d2 melee unit **cannot** close and strike in the
same turn on this ground (T160: the Knight and the Man-at-Arms both came back `STOPPED_SHORT` at d2),
so the pair must be **parked at d1 a turn before** it strikes; and the capture itself is a **move**,
ordered the turn the pool reads 0, from a unit with health left.

**Gate 4 — walls have an answer.** `walls 100` is a number, and the answer this empire already owns is
the three Trebuchets plus the Ram: a bare melee attack does **9** against 100 walls where the same
attack beside the Ram does full damage (T150, measured), and the Ram does nothing for ranged or siege
fire. The Ram must stand on a tile **adjacent to `(61,42)`** before the melee strikes, not merely near
the city.

**Gate 5 — the approach.** Six tiles from 喀山's ring, and the corridor is **one unit wide with our own
units in it**. This is the failure that has already cost this war two turns: at T159 seven of eight
grouped move orders stopped 1–2 tiles from their start, two of them moving in the *wrong direction*,
and only the Knight reached a ring tile. Issue **one move per call, re-read `get_units`, then the
next** — and optimise the turn the **last** shooter is in place, not the first unit's arrival.

## The expected shape, and the honest window

- First full volley: **1–2 turns after the ring is held** (100 walls ÷ ~135–165).
- Pool phase: **2–3 turns** (200 ÷ ~135–165 while the supply line is cut).
- So: **T166–T172** from the T162 board, inside 007's T185.
- The realistic failure is the corridor, not the enemy: Russia's military is **16** against our 507.
  If the first volley has not happened by T170, say so in the diary and name what is in the way,
  rather than reporting a third "almost staged" turn.

**The city shoots back and the screen does not stop it.** Measured T161: two of our units at
`(58,39)`/`(58,40)`, both inside the city's reach, took **13** each — while `SIEGE POSTURE` reads
`screened` for anything whose nearest enemy *unit* is more than 2 tiles away, because the posture
query counts units and not the city's strike (`lua/units.py:1322-1330`, `lua/models.py:757`). So do
not park the train inside range 2 to "wait for the last unit": either fire from there, or stay at
distance 3 until the ring is ready.

## Why this is a file and not a turn-check rule

The mechanics already have rules — `siege-train`, `take-the-city`, `use-your-attacks`,
`screen-the-siege`, `finish-the-wounded` — and they fired correctly through this war. What no metric
carries is the *objective*: "this city is read in its four numbers and the train is firing at its
walls". Two blocks would have carried it and are the ones measured broken: `SIEGE FIRE` is suppressed
exactly when the whole train is beyond city-distance 3, and `get_staging_plan`'s `arrive T+n` does not
know that our own units jam the corridor. Until those are fixed, the reading lives here.

## Report when it is done

The four numbers as read, with the turn and the query that produced each; which tiles the shooters
fired from and which were refused `NO_LOS`; the turn the Ram stood adjacent and the wall damage the
next melee attack did; the supply hexes cut; and the turn the pool reached 0 with the unit that walked
in. If it expires, say what the train's city-distance was on the last read and what blocked it.

## T163 replay notes — read this before the first move (appended after the process died mid-turn)

added: T163. The process holding FireTuner **died during T163** (the second such death; the first was
T159), before `end_turn`, so T163 never completed and **its orders are gone** — the match resumes at the
T163 autosave and every order has to be re-issued. What follows was measured live during that lost turn.

**The four numbers, as read on T163** — from result lines, not estimates:

| # | Number | Reading | Source |
|---|---|---|---|
| 1 | Garrison | **none** — a Russian Builder is the only unit on the tile; the attacking melee took ~0 retaliation | `get_map_area(61,42,3)`; `MELEE_ATTACK` lines |
| 2 | Walls | **100 → 0 in ONE turn** | `MELEE_ATTACK|…|walls: 100/100 → 90/100 → 41/100 → 0/100` |
| 3 | HP pool | **200 → 169** | the same three result lines |
| 4 | Ring | d1 `(60,41) (60,42) (60,43) (61,41) (61,43) (62,42)`; d2 `(59,42) (59,43) (60,40) (60,44) (61,40) (61,44) (62,40) (62,41) (62,43) (62,44)` | `get_staging_plan(61,42)` |

So this file's reading clause (`walls` strictly below 100, from a result line) **is satisfied**; only the
diary line is missing, because the turn never ended.

**The three things that cost the T163 attempt, and what to do instead.**

1. **(59,42) has NO LOS.** The plan lists it as a spare d2 ring tile, but `attack(3342347, 61,42)` from
   there returned `NO_LOS`. **(60,44) is a proven range-2 firing tile** (Crossbowman 2228242 fired from
   it, `range:2 dist:2`). Fire one shooter before posting the others — that is this file's own Gate 2,
   working as written.
2. **The plan posts Trebuchet 3342347 at (60,42) d1 — never execute that.** A siege unit adjacent to the
   city dies. Trust the plan's `FIRE from here` marks ((59,43), (61,44)), not its d1 postings.
3. **A melee unit attacks a city MANY times per turn while it has movement points.** This is the finding
   that matters: Man-at-Arms #2424835 at d1 `(60,41)`, with the Battering Ram at d1 `(60,43)`, attacked
   诺夫哥罗德 four times in a single turn for `walls 100 → 90 → 41 → 0` and `hp 200 → 199 → 194 → 169`,
   at roughly one movement point per attack (3/3 → 2/3 after the first). **The 100-point wall phase this
   file budgeted 1–2 Trebuchet volleys for collapses into one turn of melee attacks**, after which the
   Trebuchets belong to the HP pool. The 20/turn heal is then the only clock.

**Three more readings that correct the doctrine as written.**

- **Ranged fire on a walled city is worth about one point**: the Crossbowman's shot took the city
  `200/200 → 199/200` and left `walls 100/100`. Do not spend bolts on walls.
- **The Ram cannot stack with the melee**: `move(1441804, 60,41)` returned
  `STACKING_CONFLICT|Friendly UNIT_MAN_AT_ARMS already on (60,41). Cannot stack same formation class.`
  It works from `(60,43)`, already d1 adjacent — the game's own text is *"When adjacent to a city,
  attacking melee units do full damage to Walls"*.
- **`get_diplomacy`'s `walls N` is a static maximum, not a live pool**: it still read `walls 100` while
  the walls stood at 0. Read walls and HP from a combat result line, never from the diplomacy line.

**Task 008's tool answer, recorded as its `done when` requires.** A Russian Missionary is annotated on
`(61,31)` alongside our Builder and an Egyptian Trader, and 成都's Warrior at `(60,31)` is adjacent:
`unit_action(1245193, "condemn")` → `ERR:NO_RELIGIOUS_TARGET|No adjacent enemy religious unit to
condemn`; `unit_action(2097162, "attack", 61,31)` from `(59,31)` → `NO_ENEMY|No hostile unit or city at
(61,31)`. Both verbs refuse it, so that Missionary is not removable through this interface — 008 and 011
should be read as `count == 0` of **actionable** hostile religious units, or the objectives must be
retired as unreachable, not as unmet.

**The 成都 ring is nearly clear.** 成都's own 43-damage strike killed the 31 HP levied Man-at-Arms at
`(59,33)` on T163; the radius-2 map of `(60,31)` then holds **no military unit at all**. 011's "ring
empty" is one un-removable religious unit away, not three levied Man-at-Arms.

**Also true at the crash**, for the replay: `CIVIC_DIVINE_RIGHT` was set (the civic slot was empty);
Crossbowman #2228242 was given `PROMOTION_SUPPRESSION` and its estimate then read CS 62 with
VOLLEY/ARROW_STORM/EMPLACEMENT; the barbarian Spearman at `(61,46)` was killed by that Crossbowman; the
Builder #3407876 stands on the pillaged mine at `(61,32)` with 3 charges and needs one turn to `repair`
— note that **010/011's "pillaged mine at (60,32)" is wrong**: `(60,32)` is intact, the pillaged mine is
`(61,32)`.
