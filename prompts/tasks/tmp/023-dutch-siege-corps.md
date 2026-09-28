# TEMP TASK 023 - the Dutch campaign: take every city the Netherlands holds, with the army we have

added:     2026-09-28 (human instruction: 新增任务：利用现有部队，组建攻城兵团，占领所有荷兰的城市)
expires:   turn 335 - fifty-four turns from T281, where the match stands (read from the save): assemble and
           upgrade the corps 2-4, then 6-12 turns per city for the six the Netherlands still holds,
           measured from Haarlem's thirteen turns from Gate 0 - six of them the naval wall phase. A
           hard stop, and the arithmetic is the point: 021 expired because its deadline was set
           without measuring the distance, so re-count this one on the first full turn of the
           campaign and say in the diary whether T335 still holds.
done when: **the Netherlands holds no city.** The proof is `get_diplomacy`'s line for 荷兰 (player 2): it lists
           `Cities (N): name pop P (x,y) walls W` for every city it holds, so the task ends when
           that line names none - and, if the last one falls, when the Netherlands no longer appears
           among the living players. Each city taken is additionally proved on its own tile:
           `[CITY_CENTER]` owned by 中国 with one of our units standing on it, the city in
           `get_cities`, its queue set the same turn and a governor or garrison in place. If any
           Dutch city turns out to be their original capital, the DOMINATION block of
           `get_victory_progress` is the proof of that half. The diary carries the ledger per city:
           the four numbers and which of them came from a probe, the staging table with its
           overrides, the shots per turn and the tile each shot came from, the cost, the loyalty
           reading after the capture, and the turn it fell. Retire it as
           `023-dutch-siege-corps-done-T<n>.md` the turn the last city is ours, or as
           `-expired-T<n>.md` at the hard stop with the cities taken, the cities left, and the
           measured per-city rate.
overrides: **the human's instruction, and the army we already have.** 占领所有荷兰的城市 was given at T281; the file is
           the reason of record for the campaign and the diary records the instruction rather than
           inventing a strategic one, as 016, 020 and 022 did for their cities. **No new unit is
           authorized by this file**: the corps is drawn from the army that exists (table below),
           and the only production it touches is what was already queued for the `siege-train` and
           `ranged-mass` checks. **Gold upgrades of existing units are authorized and expected** -
           an Artillery is 155g under 职业军队 against a treasury at +83 a turn, it is the same unit,
           and `siege-train` is red at 2/3 until it happens. **The Spaceport line is not this file's
           to raid**: 西安's production, its Industrial Zone buildings and its power stay the victory
           plan, and the science and housing queues stay theirs. **The west lane stays a screen**:
           Sumer is at war and is now raiding (沃罗涅什's Campus is pillaged at T281), so the units
           watching that lane are not pulled west-to-east for this campaign; a counter-strike there
           is its own decision. Two overseas expeditions at once caused the T265 bankruptcy - gold
           hit zero at -48/t and two units were disbanded - so this file runs **one** offensive and
           one screen, never two offensives. **It does not override**: `one-garrison-per-city`,
           `use-your-attacks`, `hold-what-you-take`, the directive's ban on `propose_peace` (the
           Dutch war still ends only by taking their cities), or the policies the hold depends on.
           Every city taken is resolved with `city_action keep` - the instruction says 占领, not raze.
scope:     Every Dutch city, in the order the campaign reaches them, their rings, the units defending them, the
           route to each, and the corps this file names. Not the Netherlands' cities once taken
           (they are ours and `hold-what-you-take` owns them), not Sumer or the west lane, not a
           city-state, not a barbarian camp, and not a second offensive anywhere.

## What is known at T281, and the one call that is still missing

| fact | reading | source |
|---|---|---|
| the Netherlands | **7 cities**, military **57**, score 463, at war with us (state 6, grievances -148) | T281 diary snapshot |
| 哈勒姆 | **ours since T271** - the campaign's forward base, five tiles north of 布鲁塞尔 across a narrow strait, coastal, with a city strike | `done/022-take-haarlem-done-T271.md` |
| two of their cities are visible | **格罗宁根** around (69,14)-(69,16) and **提尔堡** around (77,23)/(79,24) | T281 diary, first sight of the Dutch interior |
| their coast battery | a Bombard working (70,19)-(70,20) that has killed **five** of our units; it takes fire from our Battleship at (67,15) and from Haarlem's walls | T276-T281 diary |
| the rest of their city list | **never read** - `get_diplomacy` prints `荷兰: Cities: 7 (all in fog)` until a city is seen | T258, when Haarlem first appeared that way |
| our corps' standards | `siege-train` **2/3** and `ranged-mass` **2/4** are the two red checks; both clear with the Artillery upgrade and the Field Cannon already building | T281 turn result |

**Gate 0 is one call nobody has made for the whole campaign: `get_diplomacy`'s list for 荷兰.**
It prints every city the Netherlands holds as `name pop P (x,y) walls W` (`src/civ_mcp/narrate.py:805-814`),
which is exactly how Haarlem was found at T258 after thirty turns of `7 (all in fog)`. **Write that
list into the diary on the first turn of the campaign, with each city's distance from our nearest
coastal base** - it is the target list *and* the measurement the deadline is re-counted from.

## The corps, drawn from the army we already have (利用现有部队)

| unit | count | role in the corps |
|---|---|---|
| BOMBARD | 2 | the siege train - **upgrade both to Artillery** (155g each under 职业军队) and `siege-train` clears |
| FIELD_CANNON | 3 (+1 building, 10t) | the ranged mass; the fourth clears `ranged-mass` |
| INFANTRY | 2 | the melee that takes cities and, measured at 布鲁塞尔, breaks walls as well as a Bombard |
| LINE_INFANTRY | 2 | second melee / garrison pool for what is taken |
| CAVALRY + CUIRASSIER | 1 + 1 | the fast arm: reconnaissance, the supply hexes, and a capture unit that arrives first |
| AT_CREW | 1 | anti-cavalry cover for the train |
| BATTLESHIP + FRIGATE | 1 + 1 | **the naval battery**: a Frigate alone took Haarlem's 100 walls to 0 in six turns from d2, and the Battleship is the strongest shooter we own |
| RANGER | 1 | eyes ahead of the column |
| GREAT_GENERAL | 2 | **keep both alive, do not activate them**: +5 CS and +1 movement to land units in range, passively |

No new unit is built for this (see `overrides:`). What the corps needs beyond the army is **gold**:
the two Artillery upgrades and, if a city proves to be inland, nothing else - a march is measured
before it is ordered, not paid for.

## What this match's two sieges actually measured

1. **Coastal and near beats inland and far, by a lot.** Haarlem - five tiles away, coastal, walls 100 -
   fell in **thirteen turns from Gate 0**, six of them the naval wall phase. 021's target was thirty to
   forty tiles inland and its artillery was still 13-22 tiles out when its thirty-three-turn window
   expired, with `get_staging_plan` reporting nine units `TOO FAR` and "0 shooter(s) in position".
2. **The naval battery is a first-class siege asset.** Walls 100 -> 0 under Frigate fire alone
   (T261-T266, ~22 a turn). A city on the coast of a sea we control is the cheap kind of target.
3. **A siege unit firing from d1 works**: Haarlem's Bombard resolved `RANGE_ATTACK ... dist:1`. The
   old note that d1 is refused is corrected - what is true is that a **d2 tile is not a d1 tile for
   melee** (T237: `STOPPED_SHORT ... 2 tiles away`).
4. **Walls are permanent; the pool is not.** A city heals about twenty points a turn, so the ring is
   the landing party's first job: Haarlem's supply line was cut 3/6 and still healed while it was
   fired on.
5. **The four numbers are three until a probe** - a city's own tile can stay `[fog]` while its whole
   ring is visible (021's finding). But **we are already at war with the Netherlands**, so our own
   attack list reads the garrison for free, which is how Haarlem's Builder and 布鲁塞尔's were found.
6. **The post-combat prose is stale; the pooled `walls:` / `city hp:` fields are the record**, and a
   later read is the fact.

## Gate 0, per city, as the corps arrives

`get_map_area` radius 3 for the ring and the supply hexes; the four numbers with the source named;
`get_staging_plan(city_x, city_y)` and the written table **before the first `unit_action`**. The six
overrides this map has already paid for live in `prompts/tactics/04-staging-out-of-range.md` step 3b-1 -
read them there rather than restating them, and note that **the d1 note is corrected**: a siege unit
firing from d1 works (measured at 哈勒姆, `RANGE_ATTACK ... dist:1`), while a d2 tile is not a d1 tile
for the capture move.

## Sequencing - and it is a proposal until the list is read

**Nearest and coastal first**, one city at a time, and **each captured city becomes the next forward
base**: Haarlem already is one - it is on their coast, it has a city strike that is the cheapest
damage in the empire (43, no retaliation), and it is where a garrison can heal between phases. Write
the planned order from the actual `(x,y)` coordinates and the measured distances, not from this file's
guess, and re-count the deadline from it (below).

## 集结 and 集火

Run `get_staging_plan(x, y)` and write the table - one row per unit: where it is, its movement, the one
tile it goes to, the `get_pathing_estimate` cost, its arrival turn, its role, whether it can fire from
there. Then, in order:

1. **Cut the supply ring** on the approach - the pool heals about twenty a turn otherwise.
2. **Walls first.** The naval battery and the d2 shooters work them; the wall number comes from the
   first melee attack's result line when the tile is fogged.
3. **The d1 melee is worth a Bombard against walls** (measured T236: 50 off the wall pool, no
   retaliation) and takes the city the turn the pool empties - `city_action keep` the same turn or the
   turn will not end, and **one capture attack per tile per turn**.
4. **Concentrate**: every shooter that can bear fires the same turn; nothing sits idle with a legal
   attack.
5. **Re-read the city a call later** rather than trusting the immediate reply, and keep the pooled
   fields as the ledger.

## Hold - the half Haarlem has not settled

Haarlem at T281 reads **loyalty 44/100 at -0.5 a turn**, with a governor (维克多), an Infantry garrison
and the `殖民地办事处` policy already in place. Every city this campaign takes gets the same treatment
**the turn it falls**: `city_action keep`, its queue set, a governor or a garrison, and the anti-flip
policy where it fits - and its loyalty line is reported every turn afterwards. A city that flips back
is a campaign loss to report with its numbers, not a detail to leave out. **The durable answer to Dutch
loyalty pressure is another Dutch city**, which is also this instruction.

## The deadline is a measurement, not a hope

`expires: turn 335` is fifty-four turns from T281: assembly and the two upgrades 2-4, then **6-12 turns
per city** measured from Haarlem's thirteen (six of them the naval wall phase) for the six the
Netherlands still holds. **021 expired because its deadline was set without measuring the distance**,
and the lesson is written into the task-history for exactly this reason. So: **on the first full turn of
the campaign, after the city list is read, re-count this deadline from the real coordinates and say in
the diary whether T335 still holds.** If it does not, report the measured per-city rate and the cities
left - do not slide the deadline silently.

## Report when it is done

For the campaign: the city list as read, the order taken and why, and the turn each fell. For each
city: its four numbers with their sources, the staging table with its overrides, the shots per turn and
the tile each came from, the capture resolution, the cost, and the loyalty reading after the capture.
At the end: whether the Netherlands still exists, what `get_victory_progress`'s DOMINATION block reads
before and after if their original capital was among them, and the state of the treasury and the two
red checks. If it expires: the cities taken, the cities left, and the measured per-city rate.

## Why this is a file and not a turn-check rule

`siege-train` and `ranged-mass` are the rules and they are red; `tactics/07` owns the analysis and
`tactics/06` the fire. What no rule carries is **the campaign itself** - that every Dutch city is the
objective, that the corps is drawn from the existing army rather than built, that the west lane stays a
screen, and that the deadline is a measurement to be re-counted rather than a date to be trusted.
