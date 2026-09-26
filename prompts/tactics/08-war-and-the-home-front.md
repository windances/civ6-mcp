# 8. The war and the home front / 战时内政，其他城市和单位的发展策略

Read from the declaration of war to the last city, and whenever a `10-TURN REVIEW` arrives inside
one. For the `economy-cities` advisor: the other seven files answer "what does the army do this
turn", and this one answers "what do the cities the army is not standing in do".

**Coarse by design.** The split below is decided **once, at the declaration**, and re-opened only
when the review says so. A home front that is re-planned every turn is a home front that produces
nothing — and the war is exactly when nobody is looking at it.

## Why the question needs its own answer

In the T103–T130 Russian war the army's turns were planned to the movement point and the other five
cities were decided turn by turn. The military result was fine. The measurable cost was cash: this
is the empire's own per-turn record, T99 (last pre-war turn) to T130 (Russia eliminated).

| | T99 (pre-war) | T110 (Moscow) | T117 (St Petersburg) | T130 (done) | Δ T99→T130 |
|---|---|---|---|---|---|
| science | 32.3 | 34.9 | 41.9 | **57.3** | **+25.0** |
| culture | 37.9 | 37.9 | 40.6 | 46.7 | +8.8 |
| **gold/turn** | **+34.8** | **+18.8** | **+0.4** | **+4.9** | **−29.9** |
| districts | 5 | 10 | 15 | 16 | +11 |
| improvements | 20 | 20 | 28 | 30 | +10 |
| pop | 29 | 37 | 45 | 53 | +24 |
| territory | 58 | 75 | 100 | 122 | +64 |
| military | 262 | 298 | 276 | 282 | +20 |

Both halves of that table are the point, and they are **not** in tension:

- **The compounding line went up during the war** — districts +11, improvements +10, science +25 in
  twenty-seven turns. Development did not have to stop, and it did not.
- **The cash line went to the floor** — gold/turn +34.8 → +0.4, a 99% fall, and the rule
  `carrying-capacity` (gold/turn ≥ +10 with the army counted) failed from T111 for the remaining
  nineteen turns of the war. The army went 262 → 306 military and took ~34 gold/turn of income with
  it; the last ~18 of that was handed over in the seven turns between Moscow and St Petersburg.

So the wartime home front is not a trade-off between "build" and "fight". **The production
compounds; the income pays for the army.** What a war actually costs the home front is units and
gold, not districts — and the two failure modes are the two flat windows, not the whole war:

- **T103→T110, the war's first seven turns: science 35.4 → 34.9, i.e. negative.** The Campus line had
  been ordered but not finished (districts 7 → 10), so nothing was compounding yet. Expect one flat
  window at the start of a war and say so in the diary instead of being surprised by it.
- **T110→T117, the war's best window: districts +5 and improvements +8 landed while gold/turn fell
  18.8 → 0.4 and `carrying-capacity` was failing every single turn.** That is what "development does
  not stop for the war" looks like in numbers, and it is compatible with a red check.

## Step 1 — price the war before declaring, and set the floor

```
wartime gold/turn = peace gold/turn − (army maintenance added by the units being built)
the floor is the directive's: gold/turn >= +10 with the army counted
```

If the projection takes gold/turn below +10, **the thing that is wrong is the size of the army or the
length of the war, not the home front** — that is what `carrying-capacity` is measuring, and it is
the one number in the war that never recovered. Two things are cheaper than the alternative: fewer
units than the plan's round number, and a shorter war (file 7's gates).

Also name the one purchase the war will need and the turn it is needed, because war gold has a
destination: measured T109, **250 gold went to one Archer → Crossbowman upgrade** and the treasury
went 418 → 188 in a single turn. That was the right purchase — it is the upgrade that takes an
Archer's 9–11 against a CS 35 garrison to 35 — and holding 300 "for later" would not have been.

**The war city builds the war, and the other cities build everything else.** Measured T142: four of
five cities were producing Builders (~320 hammers of civilian production) with a war running, a
Catapult lost and the Trebuchet upgrade still on the table — and one of those four was 西安, the city
the assault establishment came from. Builders, Settlers and Traders belong in the cities the army is
not fighting from; the war city's queue is siege, melee, upgrades and its own walls.

## Step 2 — split the cities once: one war city, everything else compounds

- **The war city** — the highest-production city — builds units, siege and the Encampment/Barracks,
  and nothing else for the duration. That is the queue the whole army comes out of.
- **Every other city builds the next district, or its building.** In this war: 西安 Campus (5t),
  北京 Campus, 长沙 Campus (13t) and 上海 Commercial Hub (10t), all ordered while the front was at
  Moscow. That is where districts 5 → 16 and science 32 → 57 came from.
- **Choose the district by the slot arithmetic, never by taste:** specialty districts are gated by
  `districts <= floor(pop / 3)`. A free slot is a district not built (`idle-district-slot`), and this
  war produced both halves of the counter-example — 长沙 sat at pop 3–5 with an unused slot for thirty
  turns, and the capital went most of the game with no Campus at all while it was the highest-pop city
  in the empire.
- **Never leave a compounding city's queue empty.** An empty queue costs a turn of compounding in a
  city nobody is watching; that is the single most common way a war window goes flat.

## Step 3 — the units the war does not need still have jobs

- **Builders keep coming, and they never follow the stack.** +10 improvements during this war is the
  `builder-backlog` requirement (≥ 3 per city). A builder has zero combat strength: it works the tiles
  the compounding cities need, inside our own borders, where the front cannot reach it.
- **Trade routes never sit idle.** Capacity comes from the Market or Commercial Hub the compounding
  cities are building, so the two halves of this file feed each other. An idle route is income the war
  has already paid for.
- **Settlers only for a resource the army needs.** The measured miss of this war: Iron Working was
  researched at T104 and the iron at (60,32)/(57,42) was **still unmined at T130**, while the horse
  cap sat at 50/50 throwing away +2/turn — so no Swordsman (CS 35) and no Knight (CS 50) was ever
  buildable in the whole campaign. One Settler or one tile purchase would have changed the army's
  ceiling.
- **Exactly one garrison per city** (`one-garrison-per-city`), and it is drawn from the cheapest
  spare unit — never from a compounding city's builder and never from the front.

## Step 4 — governors buy the phase, and moving one is free

Three governors were established in this war and each was doing a specific job:

- **Victor (`GOVERNOR_THE_DEFENDER`) in the captured capital.** Moscow sat at 33 loyalty and
  −1.9/turn — an eighteen-turn runway — with him in it, and it did not revolt a second time. That is
  `hold-what-you-take` bought with a governor rather than with a unit off the front.
- **Pingala (`GOVERNOR_THE_EDUCATOR`) in the highest-population city while developing.** Base is
  +15% science and culture there and 研究员 Researcher adds **+1 science per citizen** — on a pop-10
  city that is +10 science, more than any building available at this stage.
- **Magnus (`GOVERNOR_THE_RESOURCE_MANAGER`) in the city that builds Settlers**, promoted to 给养保障
  Provision so the Settler does not consume a population point.

`assign_governor` costs nothing to move, so a governor sitting where the phase has ended is a bonus
being thrown away — but the one that must not move is the one holding a low-loyalty city.

## Step 5 — the priority order when a turn is short

Coarse, and in this order:

1. **the war's own rules** — a turn lost at the front is a city that heals twenty points;
2. **the compounding cities' district or building queue** (an empty queue is a lost turn;
   `idle-district-slot` is the check);
3. **builders on URGENT tiles**;
4. **everything else** — a wonder, a tile purchase, an upgrade that is not needed this turn.

Notice what is not on the list: re-planning the split. Step 2 was decided at the declaration.

## Step 6 — the review gate

The `10-TURN REVIEW` asks three questions, and during a war two of them are this file's:

- **did districts / improvements / science move in the window** — with the numbers; and
- **is gold/turn still above +10 with the army counted.**

Answer both in that turn's diary. The two windows read differently and the difference is diagnostic:

- rising districts and **gold/turn under +10** → the war is affordable but the army is at its carrying
  capacity; the next unit has to be paid for by conquest or by a Market, not by savings;
- falling districts and **rising gold/turn** → the army has stopped being paid for and the compounding
  has stopped with it; that is the window that costs the next ten turns.

## Prohibitions

- **Do not stop development for the war.** Districts and improvements compete with the front for
  exactly one thing — the war city's queue — and for nothing else.
- **Do not re-plan the city split every turn.** Decide it at the declaration and change it at a review.
- **Do not build a unit in a city that has a free district slot and the population for it**, unless
  that city is the war city.
- **Do not spend the front's upgrade gold on a Builder, a tile or a wonder.** Name the purchase and
  the turn it is for; unplanned gold above ~300 is the only gold that is wasted.
- **Do not let gold/turn go negative** — the directive treats negative GNP as the hard signal that the
  army is over-built, and it is the one number that did not recover in this war.
- **Do not leave a strategic resource unmined inside our borders** (measured: iron, all war, with Iron
  Working already researched), and do not leave a resource cap full (+2/turn discarded).
- **Do not move the governor out of a low-loyalty city** to make a number in a compounding city look
  better; a city that revolts has to be besieged again.
- **Do not pull a builder or a trader toward the front** to "help": they have no combat strength, they
  cannot repair under fire, and losing one costs more than the turn it would have saved.

## What to report

```
WAR CITY   <city> — queue, production n/turn, what it is building for the front
COMPOUND   for every other city: <city — next district/building, n turns>; empty queues: <list or none>
SLOTS      districts n vs floor(pop/3) n; cities with a free slot: <list or none>
CASH       gold n, gold/turn n (floor +10), military n; the next named purchase: <item, turn>
UNITS      builders n (charges n, nearest URGENT tile), idle trade routes n, settlers n
GOVERNORS  <governor -> city> and which phase each is buying
REVIEW     did districts/improvements/science move this window: yes/no with the numbers;
           gold/turn above +10: yes/no; the one change this window implies
```

If the snapshot does not carry the per-city queues or the district/population pair, say so and name
the query that would answer it rather than guessing the split.
