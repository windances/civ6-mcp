# TEMP TASK 011 — destroy the enemy ring around 成都 (消灭成都外围部队)

added:     2026-09-26 (human instruction: 消灭成都外围部队)
expires:   turn 180 — counted from the attackers' clock, not the calendar, exactly as 010 is: the
           levy that feeds this ring runs for 30 turns, 成都's walls landed ~T157, and the empire
           already has the tools (the city's own 43-damage strike, one Crossbowman on the way, the
           mobile surplus). **010 is the floor; 011 is the clearance** — while both are in force,
           010's `done when` is the intermediate checkpoint (the city is safe) and this file's is
           the objective (the ring is empty). Retire it early as
           `011-destroy-chengdu-ring-done-T<n>.md`; if Yerevan is still feeding units at T180,
           retire it as `011-destroy-chengdu-ring-expired-T180.md` and say what is left, what it is
           costing, and whether a standing garrison plus walls is the honest answer.
done when: **no hostile unit is within 3 tiles of 成都 (60,31)** — the ring the levied units use to
           reach our mine at (60,32), our borders and the city — with the pillaged IRON mine at
           (60,32) repaired, and 成都 reading `walls` >= 1 with a garrison on its tile. Report every
           kill with its turn and the unit type, and whether the levy is still producing.
overrides: 010's *hold* posture for the units this needs, and 007's offensive timetable for those
           same units — nothing else. It does **not** authorize peace with Russia (007 owns that),
           **does not** authorize attacking Yerevan itself (it is a city-state, taking it advances
           no victory condition and spends the suzerainty we may want later), and **does not**
           authorize pulling the siege train off 喀山 or 圣彼得堡. If the two collide — the ring is
           still alive and 007's clock is expiring — the city holds with what is already there and
           the diary says so in one line; the siege train does not turn around.
scope:     成都 (60,31) and the ring out to **3 tiles** — that covers the iron mine at (60,32), the
           approach tiles the levied units stage on ((60,33)/(62,33)/(60,34) were the last read),
           and the city's own strike range (2). The enemy in practice is **Yerevan's levied units**:
           Yerevan is Russia's suzerain city-state, so its levy is fighting Russia's war by proxy.
           They are legal targets — we are at war with Russia — and **the city-state is not**.
           Nothing else in `prompts/tasks/tmp/` is relaxed, and 008 (condemn the missionary) still
           rides along with 007 rather than with this.

## What is measured, and the last coordinates seen

| Fact | Reading | Where |
|---|---|---|
| 成都 | walls 100/100, Def 45, a Warrior garrison, **its city strike did 43 damage** — the strongest single attack in the empire at that moment | T157 diary |
| the ring | **three levied Man-at-Arms** at (60,32) 77 HP on our pillaged mine, (60,33) 100 HP, (62,33) 100 HP; a Horseman at 16 HP; an **Archer at (60,34)** | T156–T157 diary |
| the mine | IRON at (60,32): pillaged, and it cannot be repaired while a levied unit stands on or beside it | T155–T157 diary |
| the reinforcement | Crossbowman 2097162 pulled out of 长沙 (a rear-area garrison) and moving east; 010 authorized it and nothing came off the wall phase | T156–T157 diary |

**Re-read before acting** — `get_map_area` radius 3 around (60,31) plus `get_units`. The levy moves,
and the 1 HP Horseman seen at T154 was already gone by T156.

## How to clear it, in the order that costs least

1. **The city is the main weapon and it costs nothing.** 成都's ranged strike (range 2) did **43**
   against a levied Man-at-Arms — more than a Crossbowman's ~27 at that point. Fire it every turn,
   at the unit standing on our mine first (it is also the one blocking the repair).
2. **Never sortie the Warrior.** A CS 20 Warrior attacking a CS 45 Man-at-Arms read
   `Est damage to attacker: ~120 -> WARNING: attacker likely dies` (T155). The garrison's job is to
   hold the tile and to satisfy `hold-what-you-take`.
3. **Concentrate — the rule is two or three attackers on one target.** `mass-on-contact` fires while
   an enemy is in contact and only one of our units is in range, and a levied Man-at-Arms at 100 HP
   survives a single Crossbowman. Ranged first (no retaliation), then a melee attack only against a
   target the same turn's fire has already reduced; and a **wounded** levied unit is a
   `finish-the-wounded` target (it heals in our territory at 5/turn, so it comes back slowly but it
   does come back).
4. **The mobile surplus hunts what the walls cannot reach** (human instruction 2026-09-26:
   多余部队里机动性高的部队还可以集火消灭传教士 / this ring): anything 3+ moves — cavalry above all —
   takes the tiles beside a levied unit that is out of the city's 2-tile reach, so it cannot
   withdraw and re-pillage. `get_staging_plan --kill x,y` assigns exactly that, and only to mobile
   units.
5. **Repair the mine the turn the tile clears** — `unit_action(action="repair")` with a Builder, no
   improvement argument. Iron is what every melee upgrade in this war runs on; leaving it pillaged
   is a cost paid every turn in `match-their-melee`.
6. **Do not chase to Yerevan's borders.** The ring is 3 tiles around 成都; a levied unit that leaves
   it is not this task's problem, and 007's clock is the thing that pays for a chase.
7. **Watch the levy.** Yerevan's levy is finite but renewable: if the ring refills after it is
   cleared, say so — that is a different problem (an envoy war or a suzerain flip) and it belongs in
   the diary, not in a longer chase.

## Why this is a file and not a turn-check rule

The rules cover the parts with metrics — `use-your-attacks`, `mass-on-contact`, `finish-the-wounded`,
`hold-what-you-take` — and they fired correctly on this raid. What no rule expresses is the
*objective*: 010 says "the city is safe", and this file says "**the ring is empty**", which is a
larger claim about tiles 2–3 out, and about a mine that has to end up repaired. That gap is what the
file carries, and it is why the human instruction is a new task rather than an edit to 010.

## Report when it is done

One line per kill (turn, unit type, tile, what killed it), the turn the ring read zero, the turn the
mine was repaired, and whether the levy refilled after that. If it expires, say which units are
still inside the 3-tile ring, what they have pillaged, and whether 成都's own strike plus its
garrison is holding them without further help.
