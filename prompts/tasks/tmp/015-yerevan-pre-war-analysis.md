# TEMP TASK 015 — the pre-war analysis of Yerevan, with the scouts close in (战前分析埃里温，侦察兵贴近侦察)

added:     2026-09-26 (human instruction: 战前分析埃里温，侦察兵贴近侦察)
expires:   turn 190 — counted from the queue. The read is reconnaissance, not production: two Scouts
           and a Knight cross the map's eastern half in about ten turns, and each reading is one turn.
           T190 gives that plus margin for a stopped-and-resumed game. If nothing is found by then,
           retire it as `015-yerevan-pre-war-analysis-expired-T190.md` with the tiles swept and the fog
           boundary still dark.
done when: **Yerevan is read in its four numbers with the scouts standing next to it — tile `(x,y)`,
           pop, `walls N`/`none`, garrison, ring** — with its own `(x,y)` located on the map, its pop
           and walls read from a result line, the garrison named (or `none`), and the ring walked at
           d1/d2 — **and** the analysis ends in the verdict the directive demands of a city-state
           (`directive.md:512-514`): a **stated reason**
           to attack it (a rival about to take its suzerainty, or a chokepoint/resource the next war
           needs), or the explicit verdict **`leave it alone`**, which closes this task just as
           cleanly. Name what could not be read and why.
overrides: **011's "no attack on Yerevan itself" is suspended for reconnaissance only** — the scouts
           may stand on the tiles adjacent to Yerevan and `get_deal_options(8)` may be used — while
           **nothing else changes**: no declaration of war on Yerevan, no attack on its units or its
           city, no peace, no unit pulled off a garrison or off the front, no gold spent on it. The war
           decision is a **new human instruction**, not this file's, and the cost of getting it wrong is
           named below: annexing a city-state deletes the bonus we could hold instead.
           `AGENTS.md`'s attack rules and the three phases do not change: if a war is ever declared on
           Yerevan, it starts with this analysis, then `tactics/04` staging, then `tactics/05`/`06`.
scope:     Yerevan only — **player 8, Religious**, the former Russian suzerain city-state whose levy
           pillaged our 成都 iron mine — and the reconnaissance of its city: the two Scouts
           (`UNIT_SCOUT` #262146 and #1638415) plus the Knight (#3145747) as the fast mover. No other
           city-state (那烂陀 Scientific, 喀布尔 Militaristic, the Industrial one and the Unknown one are
           out of scope), no barbarian camp, no city queue and no purchase.

## What is known, and the one fact that is missing

| Fact | Reading | Source |
|---|---|---|
| Yerevan | **player 8, Religious**, 0 envoys, `[can send]` | `get_city_states` T165 |
| Its suzerain | **none at T165** — the slot read `Suzerain: 俄罗斯` at T163 and was empty once Russia was eliminated | `get_city_states` T163/T165 |
| Our envoy | we held **1 token** at T165 and sent it that turn; **the destination is not in the log**, so re-read `get_city_states` before planning anything | T165 log |
| What it did to us | its **levy** raided 成都 for ~ten turns: three Man-at-Arms on the ring, our **IRON mine pillaged**, and it also fought at 喀山 | T153–T165 diary; 010/011 |
| Its units, last seen | **(62,38)** and **(62,39)** on T165 — and they are now a *city-state's* units, not a levy, because Russia's elimination dissolved the levy | T165 diary |
| **Its city tile** | **not recorded anywhere** — no diary row, no map read gives Yerevan's own `(x,y)`. That missing fact is what this task exists to produce |  |

So this is `tactics/07` **Step 0** in its pure form: *no visible candidate city, no analysis*. The army
is in the right shape; the target has never been looked at.

## The reconnaissance — 贴近侦察, in this order

1. **The trade screen costs nothing and comes first.** `get_deal_options(8)` is the cheapest read in
   the game (`tactics/07` Step 0, measured T99 on Russia: it hands over the city list with
   populations, which city is the original capital, stockpiles and gold — with no open borders and no
   war). A city-state may refuse it; **record the reply either way**, because a refusal is a fact about
   what this analysis can and cannot read at peace.
2. **Start where its units were**: (62,38)–(63,41), i.e. **east/southeast of 喀山 (58,39)** and east of
   诺夫哥罗德 (61,42). Those units are now unlevied and belong to Yerevan, so they are either walking
   home or standing where Yerevan's own ground begins — either way they point the way.
3. **A city-state's border refuses passage even to its suzerain** (measured T92–T93: our own scout was
   answered `need suzerainty or Open Borders` while `get_city_states` listed us as Suzerain with five
   envoys). So 贴近侦察 does **not** mean standing on Yerevan's tile: it means standing on the nearest
   tile we *can* occupy and reading `get_map_area` radius 2–3 from there, then doing it again from the
   far side. Route around the refusal and say so rather than reading it as a tool failure.
4. **The Knight sweeps the outside (4 moves), the two Scouts walk the ring.** Record per tile: terrain,
   feature, hills/river (the ring's movement costs), what the tile print gives about the city, the
   garrison, and every unit within two tiles. Keep both Scouts out of a barbarian camp's reach — a
   Scout sent at a camp is captured, not repelled.
5. **If the wounds read walls, say so explicitly.** `get_city_states` gives a city-state's type and
   envoys and **no city statistics**, and `get_diplomacy` lists civilisations rather than city-states —
   so the wall number may not be readable at peace at all. The measured precedent is `圣彼得堡`: it
   read `walls none` on the way in and answered `walls: 100/100` to the first melee attack, which is why
   `tactics/07` gate 4 says to **probe with one cheap attack before the train commits**. Write which of
   the four numbers came from a result line and which one is `unreadable at peace` — an honest gap beats
   a guessed wall.

## The verdict this task must reach

The directive's rule for a city-state is not "is it takable" but **"is there a stated reason"**
(`directive.md:495-514`):

- **City-states are not conquest targets.** Domination is owning the major civilisations' original
  capitals, so Yerevan advances that victory by nothing, and taking it costs grievances with everyone
  who knows it.
- **A city-state you hold as suzerain is worth more alive than owned.** Yerevan has **0 envoys and no
  suzerain** right now — one envoy token would take it, with its Religious suzerain bonus on top of
  +1 favour/turn. Annexing it deletes that for one city.
- **Attack it only for a stated reason**: a rival is about to take suzerainty and permanent denial beats
  holding the bonus, **or** the city sits on a chokepoint or a resource the next war actually needs.
- **Defend suzerainty instead**: check `get_city_states` for rival envoy counts. Losing suzerainty hands
  the bonus to a rival, which is worse than never having had it.

So the analysis ends in one of exactly two lines: **a stated reason, with the numbers that support it**
— in which case the next step is a *new instruction*, not a declaration this file can make — or
**`leave it alone`**, with what its suzerainty is worth and what one envoy would buy. Both are results.
The third possibility, "it looks weak, so let us take it", is the one the directive rules out.

## Why this is a file and not a turn-check rule

No metric carries it: `end_turn`'s checks read our own diary row and the combat metrics, and none of
them knows what a city-state's suzerainty is worth or whether a stated reason exists. The checkable
parts that do exist stay where they are — `one-garrison-per-city`, `hold-what-you-take`, and the three
phases of any war this analysis might one day feed.

## Report when it is done

Yerevan's tile and the four numbers, each with the query that produced it; the tiles the scouts stood on
and every refusal they met; its envoy count and suzerain at the time of the read (and ours); what its
suzerain bonus is worth against one envoy token; and the verdict line — the stated reason, or
`leave it alone`. If it expires, say how far the scouts got and where the fog still is.
