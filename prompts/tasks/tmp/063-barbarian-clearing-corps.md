# TEMP TASK 063 - Clear every barbarian camp and raider with a seven-slot corps

added:     2026-10-10 (human instruction: 两个攻城军团完成后，组建一个野蛮人清剿军团：3个高机动，3个远程部队，1个进程部队。清剿军团成立后，消灭所有野蛮人部队和营地)
expires:   turn 279 - 60 turn(s) from T219, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 barbarian camps and count == 0 barbarian units inside our borders or within three tiles
           of any of our cities and improvements, held for two consecutive turns after the clearing
           corps is complete.
overrides: task 061's restriction on new military production, for the units this corps is missing, and nothing
           else: the two siege corps of task 062 stay intact and are not stripped to fill it, and
           every ship, builder, trader and scout keeps its own orders. The standing no-peace rule is
           untouched.
scope:     the empire's land units that belong to no siege corps, plus the city queues that build what the
           inventory shows missing for a seven-slot clearing corps. No queue is taken from task
           062's shortfall, no city cancels what it is already building, and no siege corps unit is
           re-assigned.

## When this starts

Only after task 062's finish line holds: two siege corps of eight, complete and alive. A third formation
raised early is three half-formations instead of two whole ones, so this file waits.

## Composition

Three fast, three ranged, one melee - seven slots. The instruction's word for the melee slot is a
typo for melee and this file reads it as the melee line. Each slot has one job:

| Slot | Count | What it does here |
|---|---|---|
| fast | 3 | the chasers: raiders run, and only cavalry catch them. Light and heavy cavalry ignore
zones of control, so they cross the ground the raiders use |
| ranged | 3 | the killers from two tiles: a camp has no HP pool and no walls, but its garrison and every
raider in the open die to fire that takes nothing back |
| melee | 1 | the walk-in: a camp is destroyed by moving a military unit onto its tile, and that is the
melee slot's job. A siege unit cannot do it - it cannot attack units at all |

## Steps

1. get_units, get_map_area: inventory the land units that belong to no siege corps, by the three roles
   above, and list every barbarian camp and every barbarian unit we can see. A camp is the tile
   improvement IMPROVEMENT_BARBARIAN_CAMP.
2. Fill the seven slots from those leftovers first. Build only the shortfall: one queue per missing
   unit, nearest the ground it will sweep, without cancelling what any city is already building and
   without taking a queue from task 062's shortfall.
3. Cost discipline, and it is measured on this match: at T219 maintenance was already 119.0 against an
   income of 134.6, i.e. 88 percent, where the directive's army budget is under about 30 percent. So
   where the corps replaces an obsolete unit, the obsolete unit is disbanded rather than kept - a
   Spearman or a Crossbowman that the corps supersedes is maintenance, not strength.
4. Sweep in this order: a camp within three tiles of a city or of a Builder's work first, because that
   is where the raiders come from; then our own borders; then the ring around each border city; then
   what is left in reach.
5. The walk-in is the melee unit and only the melee unit. Ranged fire softens the garrison from two
   tiles first; never walk a scout, a builder or a trader onto a camp tile.
6. A camp respawns in fog, so a global zero is not a thing the map can be asked for. What this file
   asks for is the ground we own and the three-tile ring around it, held clean for two consecutive
   turns - and the diary's tooling line says each turn how many camps and raiders were seen and where.
7. Report a convertible barbarian - one adjacent to our melee - before the raid, so the human can use the
   leader ability from the game UI.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Clear every barbarian camp and raider with a seven-slot corps" --slug barbarian-clearing-corps --instruction 两个攻城军团完成后，组建一个野蛮人清剿军团：3个高机动，3个远程部队，1个进程部队。清剿军团成立后，消灭所有野蛮人部队和营地 --done-when "count == 0 barbarian camps and count == 0 barbarian units inside our borders or within three tiles of any of our cities and improvements, held for two consecutive turns after the clearing corps is complete." --overrides "task 061's restriction on new military production, for the units this corps is missing, and nothing else: the two siege corps of task 062 stay intact and are not stripped to fill it, and every ship, builder, trader and scout keeps its own orders. The standing no-peace rule is untouched." --scope "the empire's land units that belong to no siege corps, plus the city queues that build what the inventory shows missing for a seven-slot clearing corps. No queue is taken from task 062's shortfall, no city cancels what it is already building, and no siege corps unit is re-assigned." --why "form a seven-slot barbarian-clearing corps once the two siege corps are complete, then clear every camp and raider from our ground" --turns 60 --body "## When this starts

Only after task 062's finish line holds: two siege corps of eight, complete and alive. A third formation
raised early is three half-formations instead of two whole ones, so this file waits.

## Composition

Three fast, three ranged, one melee - seven slots. The instruction's word for the melee slot is a
typo for melee and this file reads it as the melee line. Each slot has one job:

| Slot | Count | What it does here |
|---|---|---|
| fast | 3 | the chasers: raiders run, and only cavalry catch them. Light and heavy cavalry ignore
zones of control, so they cross the ground the raiders use |
| ranged | 3 | the killers from two tiles: a camp has no HP pool and no walls, but its garrison and every
raider in the open die to fire that takes nothing back |
| melee | 1 | the walk-in: a camp is destroyed by moving a military unit onto its tile, and that is the
melee slot's job. A siege unit cannot do it - it cannot attack units at all |

## Steps

1. get_units, get_map_area: inventory the land units that belong to no siege corps, by the three roles
   above, and list every barbarian camp and every barbarian unit we can see. A camp is the tile
   improvement IMPROVEMENT_BARBARIAN_CAMP.
2. Fill the seven slots from those leftovers first. Build only the shortfall: one queue per missing
   unit, nearest the ground it will sweep, without cancelling what any city is already building and
   without taking a queue from task 062's shortfall.
3. Cost discipline, and it is measured on this match: at T219 maintenance was already 119.0 against an
   income of 134.6, i.e. 88 percent, where the directive's army budget is under about 30 percent. So
   where the corps replaces an obsolete unit, the obsolete unit is disbanded rather than kept - a
   Spearman or a Crossbowman that the corps supersedes is maintenance, not strength.
4. Sweep in this order: a camp within three tiles of a city or of a Builder's work first, because that
   is where the raiders come from; then our own borders; then the ring around each border city; then
   what is left in reach.
5. The walk-in is the melee unit and only the melee unit. Ranged fire softens the garrison from two
   tiles first; never walk a scout, a builder or a trader onto a camp tile.
6. A camp respawns in fog, so a global zero is not a thing the map can be asked for. What this file
   asks for is the ground we own and the three-tile ring around it, held clean for two consecutive
   turns - and the diary's tooling line says each turn how many camps and raiders were seen and where.
7. Report a convertible barbarian - one adjacent to our melee - before the raid, so the human can use the
   leader ability from the game UI.
" --cn "中文备份 - 063-barbarian-clearing-corps.md 的中文版，仅供人阅读，不得作为指令读取。

两个攻城军团（062）完成后才开始。

## 编成：3 高机动 + 3 远程 + 1 近战（指令里的「进程」是「近战」笔误）

| 位置 | 数量 | 在这里干什么 |
|---|---|---|
| 高机动 | 3 | 追歼：野蛮人会跑，只有骑兵追得上；轻重骑兵无视控制区 |
| 远程 | 3 | 两格外的杀手：营地没有血池也没有城墙，但守军和野外的散兵会被零反击的火力打死 |
| 近战 | 1 | 走进营地：营地靠军事单位踩上格子摧毁，这是近战格的活；攻城单位做不了（它根本不能打单位） |

## 步骤

1. get_units / get_map_area：清点不属于任何攻城军团的陆军，并列出看得见的野蛮人营地与部队（营地＝IMPROVEMENT_BARBARIAN_CAMP）。
2. 先用这些余部填满七格，只生产缺的：每个缺编单位一个队列，不能取消在建项目，不得从 062 的缺编里抢队列。
3. 成本纪律（本局实测）：T219 维护费 119.0 对收入 134.6，占 88%，而 directive 的军队预算是不超过收入约 30%。因此清剿军团顶替掉的过时单位要解散，而不是留着——被顶掉的矛兵或弩手是维护费，不是战力。
4. 清剿顺序：先打离城市或建造者工地三格内的营地（掠夺者从那里出来），再清国境内，再清边境城的环带，最后才是够得着的其余目标。
5. 踩营地只由近战单位做；远程先从两格软化守军；绝不让侦察兵、建造者、商人踩营地。
6. 营地在雾里会重生，所以全局清零不是地图能回答的问题。本文件要的是：我们自己拥有的地面及其三格环带，连续两回合保持干净；每回合的 tooling 行写清看见几个营地、几支野蛮人部队、在哪。
7. 突袭前先报告可招降的野蛮人（紧邻我方近战的那个），人类可在 UI 里使用领袖技能。
"
     at: 2026-10-10T21:35:27+08:00
     chinese backup: prompts/tasks/cn/063-barbarian-clearing-corps.cn.md
-->
