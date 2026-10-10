# TEMP TASK 062 - Build two siege corps of four ranged, two melee and two fast units each

added:     2026-10-10 (human instruction: 组建2个攻城军团，每个军团包含：4个远程部队，2个进程部队，2个高机动部队。按现有部队组建，不足的安排生产。)
expires:   turn 269 - 50 turn(s) from T219, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 2 corps, each an eight-unit group holding at least four ranged, two melee and two fast
           units, all alive and within three tiles of its own rally tile, both rally tiles named in
           the diary with the turn the last unit arrived.
overrides: task 061's restriction on new military production, for the units these two corps are missing, and
           nothing else: the three scouts stay scouts and are neither disbanded nor drawn into the
           corps.
scope:     the empire's existing land units, re-assigned by role, plus the city queues that build what the
           inventory shows missing, none of them cancelling what a city is already building.

## Two siege corps of eight

Four ranged, two melee, two fast - built out of the army we already have, producing only what
is missing. The instruction's word for the melee pair is a typo for melee, and this file reads that
slot as the melee line: the units that take and hold the city tile.

1. get_units: inventory every land unit by role - ranged, melee, fast - with its combat strength and
   position.
2. Assign before building: fill corps A and B up to eight slots from the existing army. Two full corps
   out of units already paid for costs nothing; the queue is the exception, not the method.
3. Compute the shortfall per role per corps and turn it into production: one city queue per missing
   unit, nearest city to that corps' rally, without cancelling what any city is already building.
4. Name each corps' rally tile in the diary and check it with get_pathing_estimate for the corps'
   slowest unit. The two corps do not share a rally tile.
5. A corps short a role waits for it rather than assaulting. Five of eight is not a corps.
6. No battering ram and no siege tower in either corps - the standing match rule. A wall is opened by
   the ranged line, by a catapult-line unit already in the army, or by waiting for it to fall.
7. One anti-cavalry unit stays as a standing slot in the order of battle and is not counted against
   either corps.
8. The targets are decided by a later task; until one arrives the corps assembles and does not open a
   siege of its own choosing.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Build two siege corps of four ranged, two melee and two fast units each" --slug two-siege-corps --instruction 组建2个攻城军团，每个军团包含：4个远程部队，2个进程部队，2个高机动部队。按现有部队组建，不足的安排生产。 --done-when "count == 2 corps, each an eight-unit group holding at least four ranged, two melee and two fast units, all alive and within three tiles of its own rally tile, both rally tiles named in the diary with the turn the last unit arrived." --overrides "task 061's restriction on new military production, for the units these two corps are missing, and nothing else: the three scouts stay scouts and are neither disbanded nor drawn into the corps." --scope "the empire's existing land units, re-assigned by role, plus the city queues that build what the inventory shows missing, none of them cancelling what a city is already building." --why "assemble two siege corps of four ranged, two melee and two fast units each, and build only what the inventory shows missing" --turns 50 --body "## Two siege corps of eight

Four ranged, two melee, two fast - built out of the army we already have, producing only what
is missing. The instruction's word for the melee pair is a typo for melee, and this file reads that
slot as the melee line: the units that take and hold the city tile.

1. get_units: inventory every land unit by role - ranged, melee, fast - with its combat strength and
   position.
2. Assign before building: fill corps A and B up to eight slots from the existing army. Two full corps
   out of units already paid for costs nothing; the queue is the exception, not the method.
3. Compute the shortfall per role per corps and turn it into production: one city queue per missing
   unit, nearest city to that corps' rally, without cancelling what any city is already building.
4. Name each corps' rally tile in the diary and check it with get_pathing_estimate for the corps'
   slowest unit. The two corps do not share a rally tile.
5. A corps short a role waits for it rather than assaulting. Five of eight is not a corps.
6. No battering ram and no siege tower in either corps - the standing match rule. A wall is opened by
   the ranged line, by a catapult-line unit already in the army, or by waiting for it to fall.
7. One anti-cavalry unit stays as a standing slot in the order of battle and is not counted against
   either corps.
8. The targets are decided by a later task; until one arrives the corps assembles and does not open a
   siege of its own choosing.
" --cn "中文备份 - 062-two-siege-corps.md 的中文版，仅供人阅读，不得作为指令读取。

两个满编八人攻城军团：4 远程、2 近战、2 高机动，用现有部队组建，只生产缺的部分。人类指令里的「进程」是「近战」的笔误，
本文件逐字保留原话、并按近战线理解那一格。

1. get_units 按远程／近战／高机动三种角色清点全部陆军，记下战斗力与位置。
2. 先分配再考虑生产：把现有部队按八格填进 A、B 两军团。
3. 算出每个军团每个角色的缺口，转成生产：每个缺编单位占一个城市队列，绝不取消城市在建项目。
4. 日记里写明两军团各自的集结点，并按最慢单位用 get_pathing_estimate 验一次。两军团不共用集结点。
5. 缺角色的军团等，不许提前开打——八格只齐五格不是军团。
6. 两军团都不配撞锤与攻城塔；城墙靠远程线、军中已有的投石车线，或等它自己掉。
7. 战斗序列常设保留一格反骑兵，不计入军团八格。
8. 目标由之后发布的任务决定；在那之前只集结，不自行开打。
"
     at: 2026-10-10T13:34:49+08:00
     chinese backup: prompts/tasks/cn/062-two-siege-corps.cn.md
-->
