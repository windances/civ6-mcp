# TEMP TASK 028 - development first: science and wonders for fifty turns

added:     2026-09-28 (human instruction: 新任务：发展为主，科技和奇观， 50个回合)
expires:   turn 317 - 50 turn(s) from T267, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **turn 50 of this window - the `expires:` turn the header names - arrives with 西安's 宇航中心 (Spaceport)
           standing and the first space project either finished or under way with its remaining
           turns in the diary, at least one wonder completed inside the window with the Eureka and
           Inspiration it granted written down, every 研究实验室 (Research Lab) and 大学 (University) the
           Campus cities were missing finished, and the development ledger in the diary**: science
           per turn and techs completed against the window's opening reading (361.0 and 53, the last
           snapshot before this file was added, at T266), the wonders finished with their turns and their boosts, the
           builder charges spent, **every city's power load against the sources feeding it** (or the
           dam, renewable or plant queued for the city no plant reaches), and **no war started by us inside the window**. The turn is the
           finish line even when a wonder is still in the queue - the file is a fifty-turn posture,
           not a build order that never ends - and a rival's victory warning, or a war forced on us,
           is reported instead of being absorbed.
overrides: **the directive's conquest posture, for the length of the window and in the empire's own queues.**
           The directive is written for a war of conquest - "Melee to take cities, ranged to soften
           them, siege against walls", one front after another, the army as the first claim on
           production. The human's instruction puts development first for fifty turns, so **inside
           this window the queues belong to the development plan** (districts, their buildings, the
           space chain, a continuous wonder line) and **no new offensive war is declared**. Where
           the two disagree - a queue slot, a gold purchase, a builder charge, a Great Person - the
           development plan wins, and the diary says which build gave way. **It does not override**:
           the checkable rules (`one-garrison-per-city`, `hold-what-you-take`, `use-your-attacks`,
           `finish-the-wounded`, `builder-backlog`, `screen-the-siege`), which stay live and still
           fail the turn when they are broken; **021** (the overseas legion), which is in force
           until its own expiry inside this window, keeps its units and its deadline - this file
           neither borrows from it nor vetoes it; the directive's **no-peace** rule and its refusal
           of every peace offer, because a war forced on us is still fought to the end; and the
           directive's ban on buying religious units. **It does not disband the army**: the standing
           army garrisons, defends and answers whatever attacks it, and a lost garrison is replaced
           - what it stops is *new* military production for a front we do not have, and a war we do
           not need.
scope:     The production queues of our cities and what they build (districts, their buildings, the space
           chain, wonders, and the builders and settlers the development plan needs); the research
           and civic choices; gold and faith spent on development (purchased buildings and units,
           patronized Great People, bought tiles); builder charges and the improvements and Great
           Wall segments they build; the Wonder line and the Eurekas and Inspirations it buys under
           Dynastic Cycle; and the diary that records the window's arithmetic. Not a new war and not
           a new front, not the army's offensive use (it garrisons and defends), not the units or
           the deadline of 021, not the navy's mission beyond what is already queued, not peace, and
           not a religious unit of any kind.

## The instruction, and the position it lands on

「新任务：发展为主，科技和奇观， 50个回合」 - development first: science and wonders, for fifty turns.

The window opens on the first peaceful turn this empire has had in a hundred turns. 荷兰 was
eliminated at T259 and no war is on - the per-turn snapshot lists 腓尼基 and 印度 as the only
other contacts, both at peace - so the standing army of ~1130 has nothing to attack and the
queues are free. The numbers the window starts from, read at T266 - the last snapshot before this file
was added:

| | at the window's open |
|---|---|
| cities / pop | 27 / 243 |
| science / culture per turn | 361.0 / 151.0 |
| gold (per turn) | 227.2 (+39.2) |
| faith (per turn) | 2614.5 (+116.1) |
| techs / civics completed | 53 / 35 |
| districts / improvements | 79 / 151 |
| wonders built | 6 (`Dynastic Cycle: wonders built 6`) |
| space projects | **0/50 VP, 0 spaceports** |
| era / era score | 工业时代 (Industrial) / 158 |

## What "development first" binds

- **The queues are the task.** Every city's production is a development item - a district, its
  building, the space chain, a wonder, or a builder/settler the plan needs. A unit may be built only
  to replace a garrison that was lost; a queue left empty is the one thing `end_turn` will bounce,
  and a queue filled with a unit "because it is cheap" is the posture this file exists to reverse.
- **Research and civics follow the plan, not the mood.** Name the Eureka or Inspiration for the next
  technology and civic before adopting it (China's Dynastic Cycle pays 60% instead of 50%), and read
  `get_tech_civics` once a turn for its `!! GRAB THIS` line - cheap boosted techs are the compounding
  half of this window.
- **Gold and faith are development resources for fifty turns.** At the window's open there is 2615
  faith at +116 a turn and 227 gold at +39: idle faith is the same waste as idle gold. Buy the
  building that is 20 turns away when the treasury allows it without dropping under the directive's
  gold floor, patronize the Great Scientists the space chain wants, keep the tile purchases to what a
  district or a resource needs, and write down what each purchase bought.

## The science half: the space chain is the victory path, and its gate is already named

`get_victory_progress` prints the chain and the gate in the same block. At the window's open it reads
**0/50 VP, 0 spaceports**, and the game's own words after 火箭研究 (Rocketry) finished were:

```
[UNLOCKED] 发射地球卫星 -- tech done, but need to complete prior projects first or build a Spaceport
```

So the window's binding constraint is not research, it is **production**: 西安's 宇航中心 (Spaceport)
was set on the turn it unlocked and reads **43-45 turns** - most of this window - and no space project
can start before it stands. The plan is therefore:

1. **Finish the Spaceport**, and re-count it every ten turns from the city's own production line, not
   from hope. If the arithmetic cannot fit the window, say so in the diary with the number and fix the
   number (production cards, a trade route, a purchased building, a Great Engineer) or say which
   project slips - do not let a 45-turn build sit unexamined for 45 turns.
2. **Then the chain, in the order the block lists it.** The Earth Satellite project is the first; the
   ones after it are the ones the same block names. A project is a queue item like any other.
3. **The Campus line everywhere else.** 研究实验室 (Research Lab) is the last science building and it
   is what turns 365 science into the number that finishes the tree: build it in every city that has a
   Campus, and a 大学 (University) wherever the list still offers one. At the window's open several
   cities were already on it (胶东, 圣彼得堡, 底比斯, and 阿拜多斯 finished one at T258) - finish that
   row rather than starting a new one.

## The wonder half: for China a wonder is a research building

The engine prints the reason itself every ten turns: `Dynastic Cycle: wonders built 6 (for China a
wonder is a research building; zero forfeits the ability)`. A completed wonder pays **one Eureka and
one Inspiration from its era**, and Chinese boosts are worth 60%. That is the whole argument for the
second half of the instruction:

- **The wonder line never goes empty.** From the turn this file is added to its last turn, at least one
  wonder is in some city's queue. When one finishes, the same city or the next starts another - the
  gap is the failure mode, not the choice of wonder.
- **The candidates were already on the list** at the last read: Kilwa Kisiwani (710, 18 turns in the
  city that listed it), Ruhr Valley (1240, 32), Oxford University (1240, 32) and Big Ben (1450, 37).
  Prefer the one whose Eureka or Inspiration
  the empire actually needs next, and prefer the city whose production makes it real: a 132-turn
  wonder is not a plan, it is a monument to optimism.
- **Report each one as three facts**: the wonder, the city and the turn it finished, and the Eureka and
  the Inspiration it granted. "Wonders built: 7" is not a report - the boosts are the payoff, and an
  unrecorded boost is a boost nobody can spend.
- **A wonder is not worth a lost science building.** The Campus line comes first in a Campus city; the
  wonder goes in the city that has production to spare, which is what the "one wonder in the queue"
  rule is for.

## Power: the science push is a power load, and the fuel for it is already being wasted

A city is either **fully powered** or its power-load buildings run at **reduced strength** - there is no
partial state - and the loads are the buildings this window is queueing: **Research Lab 3 power**,
Stock Exchange 3, Broadcast Center 3, Film Studio 3, Factory 2, Stadium 2, Aquatics Center 2, Food
Market 1, Shopping Mall 1, Airport 1 (the game's own `Building_RequiredPower` table). So the fifty-turn
science plan raises its own electricity bill, and an unpowered Campus city is a science building that
does not pay.

The sources, with the numbers the game uses:

| source | power | cost to us |
|---|---|---|
| Coal Power Plant | **1 Coal → 4 power**, for every city within 6 tiles | we are drowning in coal |
| Oil Power Plant | 1 Oil → 4 power, within 6 tiles | oil is short - see below |
| Nuclear Power Plant | 1 Uranium → 16 power, within 6 tiles | needs 核裂变, not researched |
| Hydroelectric Dam | **+6**, free | 发电机 (Electricity) is done; the district is ~81 production |
| Geothermal Plant | +4, free | needs a geothermal vent |
| Solar / Wind / Offshore Wind Farm | +2 each, free | a builder charge each |
| 商人's `RENEWABLE_ENERGY` promotion | +2 on each renewable in that city | one governor promotion |

**The position this window starts from, read on this branch at T256-T272:**

- **Coal is at the cap and being thrown away** - `COAL 70/70 (+12/t)` with `end_turn` printing
  `-- RESOURCE CAP: COAL 70/70 (+12/t) — excess is wasted`. A coal plant is the cheapest way to turn a
  wasted resource into power, and 1 coal buys 4 power.
- **Oil is the scarce one** - 0-4 of 70 with roughly +1 a turn, and the game refused two upgrades for it
  (`资源不足。该类型单位的升级需要1点 石油`). **Oil belongs to the units until the wells are up**:
  (73,10) in 阿纳姆, (73,32) in 塞纳 and (60,44) are unimproved and are what turns the oil line positive.
  精炼 (Refining) is done, so a Builder can raise them now.
- **西安 already has a Coal Power Plant** (with Factory + Research Lab, a load of 5). The question is not
  whether we can make power, it is **which cities the existing plant reaches**: a plant serves cities
  within **6 tiles**, and this empire spans roughly thirty tiles across, so the work is coverage.
- 发电机 (Electricity) completed at T264: the **Hydroelectric Dam** and the oil plant are unlocked.

**So the order of work on this front:**

1. **Cover the clusters with coal plants.** A city needs an **Industrial Zone + Factory** before it can
   take a plant (the plant's prerequisite building is the Factory, and coal/oil/nuclear plants are
   mutually exclusive in one city). Put one in each cluster that has power-load buildings and no plant
   within 6 tiles, and spend the capped coal on it. **The 6-tile ring is the planning unit** - write the
   ring out before queueing, and name the cities it covers.
2. **Dams for the outliers.** A Hydroelectric Dam is +6 with no fuel and no CO2, and it is the largest
   free source in the game. Every river city outside a plant's ring gets one; at 81 production in a low
   -production city it is still a project worth starting early.
3. **Renewables for the rest**: Geothermal Plant +4 on a vent, Solar/Wind/Offshore Wind +2 per charge.
   Put the **商人 governor with `RENEWABLE_ENERGY`** in the city with the most renewable sources - it is
   +2 power and +2 gold on each.
4. **Leave oil alone until the wells are in.** An oil plant is the same 4 power as coal for a fuel we do
   not have; the three unimproved wells are the prerequisite, not the plant.
5. **Record it.** Every ten turns, with the review: each city's **required against available power** and
   the source that closed a gap, or the dam/renewable that is queued for the city no plant reaches. A
   power deficit that is never written down is a science building quietly working at half strength for
   the rest of the window.

**The tool now says so**: `get_cities` prints `Power available/required` per city and a `!! UNPOWERED`
line when the game reports one, and the per-turn city record carries `power_required`,
`power_available` and `powered`. **A server started before that change answers nothing about power
(`Power` absent, not zero) - and in that case the read is the city panel itself, and the diary says
which city was checked by eye.**

## The rest of the development half

- **Builders are the cheapest multiplier and this empire is behind**: 63 builder tasks against 151
  improvements and two idle builders at the last read. **No builder ends a turn idle** - `get_builder_tasks`
  once a turn, dispatch top-down (URGENT first), and remember the Great Wall is built by Builders, not
  by cities: surplus charges go into wall segments on the new frontier.
- **Housing and amenities are hard stops, not warnings.** `housing - pop <= 1` stalls a city for dozens
  of turns; a negative-amenity city loses production exactly when the queues need it. Both are visible
  in `get_cities`; fix them this turn or write down why not.
- **Districts are gated by population** (`districts <= floor(pop / 3)`): check the arithmetic before
  queueing one, and never leave a free specialty slot empty - growth *is* the district plan.

## What must not slip while the queues are busy

- **The rules stay live.** `one-garrison-per-city`, `hold-what-you-take`, `use-your-attacks`,
  `finish-the-wounded`, `builder-backlog` and `screen-the-siege` still fail the turn when they are
  broken, and "development first" is not an excuse for any of them. The `10-TURN REVIEW` arrives five
  times inside this window: answer its three questions each time, in that turn's diary.
- **The army is not disbanded, it is idle.** It garrisons the cities, answers anything that attacks,
  and replaces what it loses. What stops is *new* military production for a front that does not exist
  and a war nobody needs.
- **021 keeps its window.** The overseas legion is in force until its own expiry, inside this one: it
  keeps its units and its deadline, and this file neither borrows from it nor cancels it.
- **A war forced on us is still fought.** The directive's no-peace rule stands: refuse every offer,
  answer every attack, and report the interruption in the diary rather than quietly letting the
  development plan absorb it.

## Report

Every turn: what each city was set to and the arithmetic behind it (cost, production per turn, turns),
which tech or civic was adopted and which boost it had, every purchase in gold or faith and what it
bought, and any builder that could not be given work. Every ten turns: the review's three answers, the
Spaceport's re-count, the wonder line's state, and **the power ledger** - each city's required against
available power, the source that closed a gap, and the plant or renewable queued for the city that no
plant's 6-tile ring reaches. At the window's close: science per turn and techs
against the opening row above, the wonders finished with their turns and their boosts, the space chain's
position and the turn the first project lands, and the ledger of what the fifty turns bought.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "development first: science and wonders for fifty turns" --slug development-science-wonders --instruction @.tmp\dev-instruction.txt --why "development first for fifty turns - science and wonders, on the human's instruction: the empire is at peace and the space chain is the victory path" --done-when @.tmp\dev-done.txt --overrides @.tmp\dev-overrides.txt --scope @.tmp\dev-scope.txt --body-file .tmp\dev-body.md --cn @.tmp\dev-cn.md --turns 50 --no-commit
     at: 2026-09-28T23:50:24+08:00
     chinese backup: prompts/tasks/cn/028-development-science-wonders.cn.md
-->
