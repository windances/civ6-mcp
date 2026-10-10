# TEMP TASK 029 - two scouts to sea: find the one civilization still unmet, information only

added:     2026-09-29 (human instruction: 新任务：2个侦察兵出海探索其他文明，不恋战，获取信息即可，30个回合)
expires:   turn 301 - 30 turn(s) from T271, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **`get_diplomacy` no longer prints `Unmet Civilization`** - it names three civilizations and prints
           that line for the fourth on the turn this file was added - **and the diary carries the
           first meeting it took to get there**: the name and the leader, the turn, the tile the
           scout stood on, and the first read of that civilization's cities, army and wars; the
           contact report also says which of the two scouts made it and how many turns it had been
           at sea. **Hard stop at the `expires:` turn** (thirty turns from this file's `added:`
           turn), retired either way: if the window closes with the fourth civilization still unmet,
           the file is retired anyway and the diary says how much water was covered, where both
           scouts ended up, and what stopped them. A scout lost on the way is reported with its last
           tile, and the window continues with the survivor and the replacement this file authorizes
           - the contact, not the pair, is the finish line.
overrides: **the directive's contact rule and the `use-your-attacks` rule, for the two scout-line units this
           file lends, and for nothing else.** The directive says any enemy within two tiles of our
           units "is dealt with this turn, before the column moves on", and the checkable rule fails
           a turn that ends with a legal attack unused. The human's instruction says the opposite
           for these two - 不恋战, no fighting, the information is the whole objective - so **they
           break contact and keep moving**. The directive already carries the exception this file
           leans on: "a lone scout or a barbarian unit we are deliberately keeping alive ... may be
           ignored - say so in the diary's tactical line so the skipped attack is a decision rather
           than an oversight". Every ignored attack is therefore written down with the unit, the
           tile and what it walked past, and a `skip_remaining_units` reply that refuses while a
           legal attack exists is that decision recorded, not a bug to force through. **The
           exception is exactly two units wide**: it does not travel to any other unit in the
           empire, and an enemy that attacks a scout is still answered by whatever the rules already
           require elsewhere. **It also overrides 028 for exactly one build.** 028 owns every city
           queue for its fifty-turn development window and stops new military production; this file
           needs a replacement if a scout is lost, so it may order **one scout-line unit (Scout or
           Ranger) per scout lost**, in the city whose production makes it fastest, and the diary
           names the city whose development queue gave way and for how many turns. Nothing else in
           any queue changes. **It does not override**: the directive's ban on `propose_peace` and
           its refusal of every peace offer - a first meeting can open a diplomacy session, and that
           session is answered in the turn it arrives so it cannot stall the turn; the rule that no
           war is declared over exploration (this file never declares one); and the standing rule
           that no warship is built for it - **an escort is allowed only if a warship is already
           afloat with nothing else to do**, and then it is the escort's own mission that is
           reported, not a new build.
scope:     The two units of the scout line named in the body, and any replacement built under this file: their
           movement (including embarking, the water they cross and the tiles they reveal), the
           `get_map_area` and `get_strategic_map` reads that direct them, one scout-line replacement
           per loss, and the contact report that ends the file. Not combat - they do not attack and
           they do not garrison, and they are not lent to any siege or front. Not any city's queue
           except the single replacement above. Not a war, not a peace, not a new warship, not the
           navy's existing mission, and not the development plan 028 is running in the cities.

## The instruction, and what is actually still missing

「新任务：2个侦察兵出海探索其他文明，不恋战，获取信息即可，30个回合」 - two scouts to sea to explore the
other civilizations; do not get drawn into a fight; information is the objective. Thirty turns.

**One civilization is still unmet, and the file names it.** On the turn before this file was written,
`get_diplomacy` counted **four civilizations and printed `Unmet Civilization (Unknown Leader) — not
met` for one of them**, while it named 苏美尔 (吉尔伽美什), 腓尼基 (狄多) and 印度 (甘地). The
scoreboard tracker, which runs every turn whether or not we have met anybody, carries a row for that
same player with **8 cities and a score level with ours** - and the civilization name on that row has
read **格鲁吉亚 (塔玛丽)** since the earliest snapshots of this branch, with `GEORGIAN_KHEVSURETI` in its
unit list. **No `get_diplomacy` result anywhere in this branch's run logs has ever printed that name.**
So the target is precise: a civilization whose name and city count the tracker already knows and whose
territory, leader and capital we have never seen.

The empire at the window's open (T271, the last snapshot):

| | at the window's open |
|---|---|
| cities / population | 27 |
| science per turn | 397.7 |
| exploration | **47% of the map** |
| score | 1226 |
| era | 工业时代 (Industrial) |
| military | 1147 |

And the fog is where it has always been: `get_strategic_map`'s boundaries put the unknown at **N/NE
across the water** for the western cities (capital 西安 N:15 NE:8, 胶东 NE:5) and at **S/SE** for the
eastern ones (塞纳 SE:3, 亚历山大 SE:3, 索贝克 SE:3/S:4). The two scouts take the two ends; the map is
half-explored and one of those half-maps holds the last civilization.

## The two units

At the last unit read (T262) both units of the scout line were alive and idle, and these are the ids
the report should use:

| unit | tile then | moves then | note |
|---|---|---|---|
| 游骑兵 `UNIT_RANGER` id 6815776 | the southern coast, near our Egyptian cities | 0/3, out of moves that turn | the western scout |
| 游骑兵 `UNIT_RANGER` id 6946850 | the eastern coast, by 亚历山大 | 0/3, out of moves that turn | the eastern scout |

**Re-read `get_units` before acting: this table is a reading, not the board.** If one of them is dead,
say so with its last known tile and build the replacement this file authorizes; if a third scout-line
unit exists (a Scout that was never lost), it is not lent - two is what the human asked for, and the
others stay where they are.

## Gate 0 - read the fog before the first move

1. `get_strategic_map` once: it prints, per city, the distance to unexplored ground in each direction
   and marks the shortest with `<- EXPLORE`. Take the two ends the empire's own numbers point at.
2. `get_map_area` radius 3-4 around each scout and at the far edge of the last revealed tile in its
   direction: the tile list says `[fog]` where the map ends, and the coast around it says which way the
   water runs.
3. **Write the route before the first move**, one row per scout: current tile, movement allowance,
   the next three tiles, whether the water is `COAST` or `OCEAN`, and the turn each leg lands. A scout
   with no written route is a scout that will spend the window in a bay.

## Conduct - 不恋战 is a rule, not a mood

- **They do not attack, and they do not trade shots.** An enemy within two tiles is walked past or
  avoided, not engaged; the fire a Ranger can give is not worth the three turns of healing it costs
  when the same unit could have revealed a coastline. Every skipped attack goes in the diary with the
  unit, the tile and the target, because the directive's own exception is written that way.
- **They do not stand still to heal if standing still is the loss.** A scout at half HP with a hostile
  in reach moves away and heals out of contact; one already out of contact `fortify`s and heals.
- **They never garrison and never join a fight** - not even a barbarian camp raid that is close by, and
  not as a spare body on a city tile. Two scouts are worth more to this empire as eyes than as garrisons.
- **They do not stop for goody huts unless the hut is on the route**, and they do not detour for a
  barbarian camp they could clear: the objective is the civilization, not the loot.
- **Keeping them alive is the mission.** A dead scout reveals nothing, and the ocean is where this
  empire's units die unseen (the last two losses to barbarians were a Builder and a Great Engineer in
  our own border).

## What to bring back - the contact report

The moment a scout sees the unmet civilization's territory or unit, the meeting is a fact and the
report has six parts:

1. **Who** - the civilization and the leader, exactly as `get_diplomacy` prints them after the meeting.
2. **Where** - the tile the meeting happened on, and the first city tile of theirs that came into view.
3. **What** - the first read of their cities, army and techs (`get_diplomacy` gives the city count,
   the military figure and the visible agendas; `get_map_area` gives the ground).
4. **Which scout** - its id, and how many turns it had been at sea.
5. **Their wars** - whether they are at war with anybody we know, which is the one fact that decides
   whether the meeting is an opportunity or a warning.
6. **The session** - a first meeting often opens a diplomacy session and blocks `end_turn`; it is
   answered in the turn it arrives under the directive's rules (peace offers refused; anything else
   judged on merit), and the answer is recorded.

## What this file is not

It is not a war, not a raid, and not a second front. It is not a licence for the other ~1150 points of
army: the exception it writes is exactly two units wide, and no other unit in the empire changes what
it was doing. It is not a navy programme - the ships 026 built keep their own missions, and a warship
escorts only if it is already afloat with nothing else to do. And it is not a detour from 028: the
cities keep building the development plan, with the single exception of one scout-line replacement per
scout lost.

## Report

Every turn: where each scout is, what it revealed (tiles, coast, resources, other civs' borders), what
it walked past and why, and the turn its current leg lands. At the meeting: the six parts above. At the
window's close, if the meeting did not happen: both scouts' positions and health, the water each one
covered, the exploration percentage against the 47% this window opened at, and the reason the fourth
civilization is still unmet - what the fog did, not that nobody looked.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "two scouts to sea: find the one civilization still unmet, information only" --slug two-scouts-sea-info --instruction @.tmp\scout-instruction.txt --why "two scout-line units to sea to find the one civilization still unmet, information only and no fighting, on the human's instruction" --done-when @.tmp\scout-done.txt --overrides @.tmp\scout-overrides.txt --scope @.tmp\scout-scope.txt --body-file .tmp\scout-body.md --cn @.tmp\scout-cn.md --turns 30 --no-commit
     at: 2026-09-29T00:01:49+08:00
     chinese backup: prompts/tasks/cn/029-two-scouts-sea-info.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 029 --expired --turn 288 --note "Superseded: the match this file governed was handed over and a new match was started for the military production experiment; see docs/experiments/README.md." --no-commit
     at: 2026-09-29T03:33:37+08:00
     status: expired at T288
     chinese backup: prompts/tasks/cn/029-two-scouts-sea-info.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 029 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:23+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/029-two-scouts-sea-info.cn.md
-->
