# TEMP TASK 016 — stage the assault and destroy Yerevan (战前集结，消灭埃里温)

added:     2026-09-26 (human instruction: 战前集结，消灭埃里温)
expires:   turn 190 — counted from the queue, not the calendar. The army is already on Yerevan's
           doorstep (nearest units at (61,40)/(60,40), the siege train at (58,43)/(59,43)), so the
           assembly is **2–3 turns**; the wall phase is one probe plus one to three volleys, the pool
           two to three turns at ~135–165 a turn, plus casualties and the declaration turn the engine
           does not sync on. That is 8–12 turns from T177. T190 gives the margin. Retire it as
           `016-destroy-yerevan-done-T<n>.md` the turn the city is ours, or as
           `016-destroy-yerevan-expired-T190.md` with the assault's state and what held it up.
done when: **Yerevan (63,37) is ours** — the capture is resolved with `city_action keep` (or `raze`,
           and the reason), a unit holds the tile (`hold-what-you-take`), and the diary carries the
           ledger: the four numbers read at war (the wall number from the **probe attack**, not from
           peace), the staging table from `get_staging_plan(63,37)` with its overrides, the declaration
           turn, the shots per turn, and the cost paid. `get_city_states` no longer lists Yerevan as
           player 8's, and no Yerevan unit is left standing on its former ring.
overrides: **015's verdict `leave it alone` is overridden by this instruction**, and so is the
           directive's city-state rule **for this one city** (`directive.md:497-499`: annexing a
           city-state advances Domination by nothing and costs warmonger grievances with everyone who
           knows it). The **reason of record is the human instruction itself** — do not invent a
           strategic justification for it in the diary, and do record the cost actually paid (the
           suzerainty Egypt holds and what contesting it would have cost, the grievances, the units and
           turns spent). It authorizes **the declaration of war on Yerevan (player 8) and nothing
           else**: no war with Egypt (which holds Yerevan's suzerainty), no peace with anyone, no second
           city-state, no barbarian camp, and no unit pulled off a city garrison except the assault
           force named below. **013's gold earmark stands** — upgrades are bought from its list, in its
           order, and the run-down below says which one this war needs.
scope:     Yerevan only — its city at **(63,37)** and the units defending it: an **ARCHER** garrison and
           a Trader on the city tile, a **HORSEMAN** at (63,38), a **WARRIOR** at (63,39) (015, T177).
           Not Egypt, not 那烂陀, not 喀布尔, not the Industrial or the Unknown city-state, and not the
           barbarian camp that `answer-the-camp` watches for on its own.

## What 015 read at peace, and what is still unread

| # | Number | Reading at T177 | Source |
|---|---|---|---|
| 1 | Garrison | **ARCHER**, with a Trader on the city tile — no melee inside | 015's trade-screen read |
| 2 | Walls | **unreadable at peace** — `get_city_states` gives a city-state's type and envoys and no city statistics | 015 |
| 3 | HP pool | **not read** — it is 200 unless a probe says otherwise | — |
| 4 | Ring | 015 walked it with the scouts; the firing list is **not yet proven per tile** | 015's scouts |
| — | Pop | **10** (from the city-state's own trade screen) | `get_deal_options(8)` |
| — | Field units | **HORSEMAN (63,38)**, **WARRIOR (63,39)** | 015 |
| — | Suzerain | **Egypt** — so the bonus is contested, not ours, and declares cost grievances | 015 |

Pop 10 in the late Medieval era almost certainly means walls; **the file assumes walls until a probe
says otherwise**, and gate 4's rule is the reason: a city that finishes walls mid-siege doubles the job.

## 战前集结 — the staging task, in this order

1. **Build the table before the first move** (`tactics/04` step 3b): run **`get_staging_plan(63,37)`**
   and write one row per unit — where it is now, its own movement, the one tile it goes to, the cost,
   the arrival turn, its role, whether it can fire from there. **Three of its outputs are overridden**
   by measurements this game paid for:
   - a **Crouching Tiger posted at d2 is wrong** — the Tiger has **Range 1** and cannot fire from
     there; it needs a d1 tile it can reach with a movement point spare (measured T176–T177);
   - **a siege unit posted at d1 is refused** — a Trebuchet/Bombard at d1 dies to the city's strike;
     it fires from d2 (measured T163, and the plan does it);
   - **`arrive T+n` does not know our own units jam the corridor** — issue **one move per call** and
     re-read `get_units` between them (T159 and T161 both landed units 1–2 tiles short, two of them in
     the wrong direction; the recorded pathfinder signature is that it **drifts west**).
2. **The force is the field army, and it is already assembled** (T176): **2 Bombards** (#4325376 at
   (59,43) and #4128794 at (58,43)) plus **1 Trebuchet** (#3538967 at (58,35)) — the third shooter is
   85g from being a Bombard and is the one upgrade this war actually wants (**first** in 013's list) —
   two **Musketmen** (#3932184 at (61,40), #4063257 in 喀山), a **Knight** (57,39), the **Battering Ram**
   and a **Spearman** at (61,41), the **Crouching Tiger** (60,40) and several **Crossbowmen** around 喀山
   and 诺夫哥罗德. **The Ram joins the melee** (human instruction: 已经有攻城锤，就参战) — and its
   measured warning travels with it: at 诺夫哥罗德 it did **not** give full wall damage from a
   non-stacked tile, so **stack it with the attacker and re-measure on the first hit** before trusting
   it.
3. **Stage outside the city's 2-tile strike, then open when the last shooter is in place** — not when
   the first unit arrives. The assault opens with the train inside range 2 and the melee at d1, and a
   unit that spends its move arriving cannot fire the same turn.
4. **Prove each firing tile.** A tile is a firing position only once a shot from it has been ordered
   and **not** refused: 阿斯特拉罕's (55,38) was d2 with `NO_LOS` and 诺夫哥罗德's (59,42) likewise. Fire
   one shooter from the assigned tile **before** posting the others on theirs, so a refusal costs one
   unit-turn instead of three.
5. **Declare, wait a turn, then attack.** The engine does not sync the war on the declaration turn
   (measured, twice): position on the declaration turn, attack on the next. **Before declaring**, read
   `get_diplomacy` for Egypt's state and any pact and record it — this file authorizes no war with
   Egypt, and if Egypt declares on us the standing rules take over.
6. **Kill the field units first, together.** The **Horseman at (63,38)** is cavalry and its charge
   reaches past the front line — the counter is anti-cavalry (the Spearman) or ranged fire, and
   `counter-the-cavalry` fires while it is in contact with no anti-cavalry unit in the army. Two or
   three attackers on one target (`mass-on-contact`), and a wounded unit is finished this turn
   (`finish-the-wounded`).
7. **The wall phase is the Trebuchet's job, not the melee's.** Measured at 诺夫哥罗德: one Trebuchet
   shot took the walls `92 -> 34` (**58 points**) while a bare melee attack did **8**; a Bombard is the
   next tier of the same tool. **Probe with the first melee attack to read the walls** (gate 4), then
   let the train break them; a melee unit that reduces the pool to 0 **captures the city outright** —
   no separate walk-in is needed (measured T165).
8. **Hold it on the turn you take it**: a governor or a garrison before the next turn
   (`hold-what-you-take`), and resolve the capture with `city_action` immediately.

## What this costs, stated plainly for the diary

- **The suzerainty is Egypt's**, so this does not take a bonus away from us — it removes the bonus from
  the board for both of us, and it is one envoy token that decides the contest either way (015's
  arithmetic).
- **Grievances with every civilisation that knows Yerevan**, and a city-state advances Domination by
  nothing (`directive.md:497-499`). The ledger should say so rather than implying a prize.
- **The window is cheap right now, which is the real argument for doing it**: gold 194 at **+31/turn**,
  the train already on the doorstep, and the only competing task (013's recon) is a march, not a
  battle. That is the honest version of "why now" — the human's instruction is the reason of record.

## Why this is a file and not a turn-check rule

No metric carries "attack this city-state now": the rule file deliberately has no city-state rule, the
directive says the opposite of what this file does, and the decision is a **human override of an
analysis** — which is exactly the class of instruction a file exists for. Every mechanical part of the
assault stays where it is: `siege-train`, `screen-the-siege`, `mass-on-contact`, `take-the-city`,
`hold-what-you-take`, `use-your-attacks`, and the `SIEGE PROGRESS` / `SIEGE FIRE` blocks.

## Report when it is done

The staging table with its three overrides; the four numbers as read **at war**, naming the probe that
produced the wall number; the declaration turn and the turn the first volley landed; the shots per
turn and the supply line; the capture resolution; and the cost — units lost, gold spent (and which
line of 013's earmark it came from), grievances and Egypt's reaction. If it expires, say where the
train stood, what the walls read when probed, and what blocked the assault.
