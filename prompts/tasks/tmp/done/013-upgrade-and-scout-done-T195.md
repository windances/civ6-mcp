# TEMP TASK 013 — save the gold, upgrade the army, and find the next war's target (攒钱升级部队，侦察兵找下一个战前分析目标)

added:     2026-09-26 (human instruction: 攒钱升级部队，侦察兵找下一个战前分析目标)
expires:   turn 195 — counted from the queue, not the calendar. The war upgrades this file names cost
           **425g** (two Musketmen at 85g each, three Bombards at 85g each), the recon upgrade another
           125g, and the treasury held **170g** at T170 with a carrying capacity of **+15.3g/turn**:
           550 − 170 = 380g, about 25 turns. T195 leaves no room for a purchase this file does not
           name; if the gold goes somewhere else, retire it as `013-upgrade-and-scout-expired-T195.md`
           and say what it was spent on instead.
done when: **the war upgrades are paid for and a candidate is read in (x,y)** — `UPGRADE AVAILABLE` no
           longer names a MUSKETMAN or BOMBARD target (both Man-at-Arms and all three Trebuchets
           upgraded with `upgrade_unit`, each recorded with its price and the treasury before and
           after), **and** the reconnaissance half has produced a candidate: a city of a met
           civilisation read in its four numbers from result lines — `(x,y)`, pop, `walls N`/`none`,
           `def N` — or an explicit `no candidate visible` report naming the fog boundary swept and
           the tiles still dark.
overrides: the general "spend accumulated gold rather than let it sit" advice — this gold is
           **earmarked** for the list below — and it forbids one upgrade the block will offer: the
           Battering Ram can become a Siege Tower for 40g, and the standing directive says
           不用锤，用投石车 (**no ram and no tower**), so **do not pay for it**; the Ram we own stays as
           it is. It authorizes **no** declaration of war, **no** peace, **no** barbarian raid, and it
           takes nothing off the garrisons of the five captured cities (`hold-what-you-take` holds).
scope:     the treasury, the upgrade list, and reconnaissance only: the two Scouts (`UNIT_SCOUT`
           #262146 and #1638415) and the Knight (#3145747, 4 moves) as the fast mover. No city's
           build queue changes for this, no unit is bought with the earmarked gold, and nothing moves
           off the front.

## What is measured (T166–T170, from result lines)

| Fact | Reading |
|---|---|
| Treasury | **170g** at T170; `Gold: 115 (+20/turn)` at T166, and the 10-turn review puts the carrying capacity at **+15.3g/turn** with military 569 |
| The empire | 11 cities, science 105–113, culture 55, faith 511, favor 199, score 393, military 575 (T169) |
| Upgrades the game offers | SCOUT #262146 → **SKIRMISHER 125g** · MAN_AT_ARMS #2424835 → **MUSKETMAN 85g** · MAN_AT_ARMS #2949142 → **MUSKETMAN 85g** · TREBUCHET #3211270 → **BOMBARD 85g** · TREBUCHET #3342347 → **BOMBARD 85g** · TREBUCHET #3538967 → **BOMBARD 85g** · BATTERING_RAM #1441804 → SIEGE_TOWER 40g (**forbidden**, see `overrides`) |
| Where the war units stand | Man-at-Arms #2424835 in 诺夫哥罗德 (61,42) at 78/100; #2949142 in 喀山 (58,39); Trebuchets at (58,43), (59,43), (57,37); Knight (57,38); Crouching Tiger (60,40) |
| The scouts | #262146 at (60,39), 89/100, 3 moves — already upgraded-capable; #1638415 at (66,29), 3 moves |
| Who is on the map | 6 civilisations: **4 unmet** (`Unmet Civilization (Unknown Leader) — not met`), one met civ **DENOUNCED (−32)** with **5 cities, all in fog**, military 32 (0.1x), `Can: Declare War`; one met civ NEUTRAL (−8) with 6 cities, only (65,32) visible (`pop 4, walls none`), military 245 (0.5x) |

## Half one — 攒钱升级部队

**The order is not a preference; it is the two failure modes this war measured.** A Man-at-Arms is
the line that loses to a Musketman (CS 45 → 55), and every melee unit that has to stand on a city's
ring is a melee unit that has to survive the city's strike. The Trebuchets become Bombards for the
same reason the Trebuchet existed at all: **the Trebuchet is the wall-breaker** — one shot at
诺夫哥罗德 took the walls `92 -> 34` (58 points) while a bare Man-at-Arms beside the city did 8 —
so the next tier of that tool is the cheapest damage the empire can buy.

1. **Hold a 100g floor.** Do not drop the treasury below 100g: an emergency (an escort for a
   Builder, a wall repair, a panic unit) costs that much, and an upgrade is never urgent enough to
   give up the ability to react. With +15.3g/turn this means buying roughly one upgrade every 6
   turns, and it is why the queue runs to ~T195 rather than ~T180.
2. **The two Musketmen first (170g).** They are the units that will stand in front of the next
   city's walls. Upgrade them **in the captured cities they are garrisoning** (诺夫哥罗德 and 喀山),
   after they have moved for the turn — an upgrade spends the unit's remaining action.
3. **Then the three Bombards (255g).** Keep the three of them together as a train; a Bombard that
   arrives alone is the 圣彼得堡 mistake (three siege units, one firing).
4. **The Skirmisher last (125g), and only if the war upgrades are done.** #262146 is the scout that
   has to walk into fog where a barbarian can end it; the upgrade buys it survival, not a fight. It
   is the first thing to drop if the gold is needed elsewhere, and the file records the drop.
5. **Never the Siege Tower.** The block will offer it for 40g; the directive forbids it (不用锤).
6. **Do not buy units with this gold.** A purchase is a separate decision with its own justification;
   this treasury is the upgrade budget.

## Half two — 侦察兵找下一个战前分析目标

`prompts/tactics/07-pre-war-analysis.md` Step 0 is the gate: **no visible candidate city, no
analysis.** The empire has just closed that gap for Russia and has nothing else: four civilisations
have never been met, and the one that has denounced us keeps **all five of its cities in fog**. So
the recon is not a formality; it is the only thing that can turn "there are rivals out there" into a
pre-war analysis.

1. **The trade screen is the cheapest reconnaissance and costs no unit a move** (`tactics/07` Step 0,
   measured T99): `get_deal_options(player_id)` on both met civilisations returns their city list
   with populations, which city is their original capital, their strategic and luxury stockpiles and
   their gold. Run it on **both** before moving a scout — it may satisfy Step 0 for the civ that has
   denounced us without leaving our borders.
2. **Then the fog, and the scouts own it.** Four unmet civilisations: sweep with #262146 (at (60,39),
   from the 诺夫哥罗德 side) and #1638415 (at (66,29), east), and move the **Knight** (#3145747, 4
   moves) as the fast mover toward whichever side is still dark. `get_strategic_map` names the fog
   boundary per city; use it to choose the direction rather than walking blind.
3. **Three things that look like tool failures and are not** (`AGENTS.md`, measured T92–T93): a land
   unit **cannot embark without `TECH_SHIPBUILDING`** (a strait is a wall); a **city-state's tile
   refuses passage even to its suzerain** (`need suzerainty or Open Borders` with 5 envoys listed) —
   route around and say so; and a **camp or a guard captures a Scout** rather than fighting it, so a
   camp on the route is a detour, not a target (`tactics/07`'s camp branch is a separate raid with
   its own authorization).
4. **Read a candidate in its four numbers, from result lines.** `get_diplomacy`'s city line gives
   `walls N`/`none`, pop and `def N` — and its `walls N` is a **static maximum** (it read `walls 100`
   while 诺夫哥罗德's walls stood at 0), so the walls and the HP pool come from a combat result or
   from `SIEGE PROGRESS` once shooting starts. Tiles come from `get_map_area`/`get_deal_options`.
5. **Report `candidate` or `none`, never a hunch.** If by T195 no candidate city is visible, that is
   a result: name the fog boundary swept, the civilisations met, and what is still dark — an army
   with no target is a war that has not started (`tactics/07` Step 0), not a reason to declare.

## Why this is a file and not a rule

No metric carries "this gold is earmarked" or "the scout has somewhere to be": `end_turn`'s warnings
measure a treasury and a military, not an intention, and the rule file's `gold/turn` floor (the
directive's +10/turn against `tactics/08`) is about the empire's solvency rather than about saving
for a named list of upgrades. What *is* checkable stays in the rules and keeps firing:
`one-garrison-per-city`, `hold-what-you-take`, `use-your-attacks`, and the three phases of the next
war (`tactics/07` → `tactics/04` → `tactics/05`/`06`), which this file feeds rather than replaces.

## Report when it is done

The upgrade ledger: each unit, its target, the price, the treasury before and after, and the turn.
Then the recon half: the civilisations met, the candidate city with its four numbers and its approach
distance, or the `no candidate visible` report with the fog boundary. If it expires, say what the
treasury went on instead and whether any candidate had appeared.

## Outcome — both halves held at T195

**The upgrade half is complete and its five calls are in the session logs** (the `done when:` line's
count — both Man-at-Arms and all three Trebuchets, 5 x 85g = the 425g it named — is exactly what was
bought):

| turn | unit id | upgrade | log |
|---|---|---|---|
| T172 | #2424835 | `UNIT_MAN_AT_ARMS -> UNIT_MUSKETMAN` | `log_..._roaming-emerald-ziggurat-38.jsonl` seq 129 |
| T174 | #2949142 | `UNIT_MAN_AT_ARMS -> UNIT_MUSKETMAN` | `log_..._tidal-slate-armada-31.jsonl` seq 31 |
| T174 | #3211270 | `UNIT_TREBUCHET -> UNIT_BOMBARD` | same log, seq 32 |
| T176 | #3342347 | `UNIT_TREBUCHET -> UNIT_BOMBARD` | same log, seq 104 |
| T195 | #3538967 | `UNIT_TREBUCHET -> UNIT_BOMBARD`, 85g, treasury 242 -> 157 | `log_..._silver-scarlet-parapet-72.jsonl` seq 69 |

The last one is the one that closed the file, and it needed two measured facts to land: the upgrade is
refused **outside friendly territory** (`CANNOT_UPGRADE ... Must be in friendly territory`), so the
Trebuchet had to withdraw from (66,35) to our own (66,36) first; and **`upgrade_unit` changes the unit
id** — #3538967 came back as #4980745, so an id carried in notes across an upgrade names a unit that no
longer exists.

**The reconnaissance half produced a candidate**: `ỉwnw`/Heliopolis **(65,32), pop 6, `walls 100`**, read
from result lines — the first real siege of this war, and the target the T195 plan named next. The other
candidate, Thebes (68,34) pop 5 walls `none`, was taken the same turn (task 017). The Netherlands' six
cities are named by the trade screen but all stand in fog, so they yielded no `(x,y)`.
