# TEMP TASK 066 - The first siege corps takes Brussels, with the three phases on the record

added:     2026-10-10 (human instruction: 第一攻城军团拿下布鲁塞尔，注意是否执行相关攻城策略，比如战前分析，战前集结，攻城站位集火)
expires:   turn 280 - 60 turn(s) from T220, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 1 city named Brussels owned by us, with at least four of the corps' shooters having fired
           on the turn it fell, one garrison unit left in it, and the diary carrying all three
           phases for it - the analysis, the staging table and the fire.
overrides: task 062's rule that a corps does not open a siege of its own choosing, for the first corps only:
           this file is the task that names its target. The second corps stays where 062 leaves it,
           and task 063 does not start until this assault is resolved - never two establishments at
           once. Task 064's cap fixes and task 061 keep their places, and the no-peace rule is
           untouched.
scope:     the first siege corps of task 062 - its eight slots - and the war with the city-state this file
           names, the declaration included if none is in force, plus the one city queue that
           replaces a corps unit lost in the assault.

## The target is named, the coordinate is read

The city-state the human named, Brussels. Its tile is read fresh from get_city_states every time this task is
worked - a coordinate carried forward from an earlier file, an earlier session or a note has already been wrong once
on this match, and a city-state can be taken by somebody else.

## Phase one - the pre-war analysis, before a single unit moves

1. get_city_states: Brussels' tile, its owner, its military strength, and whether we are its Suzerain.
2. The suzerain gate, and it is the one that costs a war: if Brussels has a Suzerain, read that civilisation's
diplomacy for a defensive pact. A pact means the Suzerain joins the war the turn we declare, and that is a different
war than the one this file asks for - say so in the diary before declaring.
3. get_target_report on its tile: the walls and their pool, the city centre pool, the garrison unit, the defence
strength, the visible enemy units within three tiles, and the per-tile FIRE and NO LINE OF SIGHT verdicts. It works
before a declaration and in fog.
4. The arithmetic, in the diary and not in the head: what the walls are, what each gun does per turn against that
pool, against the city's heal, what the ranged line adds, how many turns that is, and what it costs. If the number
says the siege cannot be won, this task's answer is the one task 058 gave: do not open it.
5. get_reinforcements: which turn a corps unit still in a queue reaches the rally, and which roles nothing covers.

## Phase two - the staging, before the first move

6. The corps must be eight of eight. A corps short a role waits; five of eight is not a corps.
7. get_staging_plan on the city's tile: one row per unit - where it is, its movement, the one tile it goes to, the
path cost, the turn it arrives, its role, and whether that tile can actually shoot. Fill the FARTHEST firing tile
first: each shooter fires from its OWN range, so a range-3 gun standing two tiles out is a gun taking a free hit
from the city's two-tile strike for nothing.
8. Never two units on one tile, name the corridor, and put the melee and the anti-cavalry in front of the guns.

## Phase three - the fire, and where it is concentrated

9. Declare if no war is in force, and remember the engine does not sync combat until the next turn: declare on N,
position that turn, attack on N+1. An answer of NO_ENEMY on the declaration turn is the rule, not a failure.
10. Concentrate: every shooter fires at the same target in the same turn - the city, or the one garrison unit that
is actually holding it. Fire spread across two targets is fire that kills neither.
11. Read SIEGE POSTURE and its SIEGE FIRE count every turn. It is the count of shooters that could fire and did; a
number below the corps' shooters is an unused attack, and the block UNUSED ATTACK names the unit.
12. The melee takes the tile, city_action with the keep decision resolves it, and one garrison unit stays in it.
Never propose peace, and never field a battering ram or a siege tower - the standing match rule.

## The audit this task is also for

The human's instruction is not only to take the city but to check that the doctrine was executed. So the diary
must carry the three phases separately, each with the measurement that satisfied it: which gates were run and what
they answered, the staging table with the turn each unit arrives and its FIRE verdict, and the fire itself with the
SIEGE FIRE count per turn. A city taken without those three records is a city taken by luck, and the file is not
finished until they are written.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "The first siege corps takes Brussels, with the three phases on the record" --slug first-corps-takes-brussels --instruction 第一攻城军团拿下布鲁塞尔，注意是否执行相关攻城策略，比如战前分析，战前集结，攻城站位集火 --done-when "count == 1 city named Brussels owned by us, with at least four of the corps' shooters having fired on the turn it fell, one garrison unit left in it, and the diary carrying all three phases for it - the analysis, the staging table and the fire." --overrides "task 062's rule that a corps does not open a siege of its own choosing, for the first corps only: this file is the task that names its target. The second corps stays where 062 leaves it, and task 063 does not start until this assault is resolved - never two establishments at once. Task 064's cap fixes and task 061 keep their places, and the no-peace rule is untouched." --scope "the first siege corps of task 062 - its eight slots - and the war with the city-state this file names, the declaration included if none is in force, plus the one city queue that replaces a corps unit lost in the assault." --why "take the city-state the human named with the first siege corps, and run the pre-war analysis, the staging and the concentrated fire in that order" --turns 60 --body "## The target is named, the coordinate is read

The city-state the human named, Brussels. Its tile is read fresh from get_city_states every time this task is
worked - a coordinate carried forward from an earlier file, an earlier session or a note has already been wrong once
on this match, and a city-state can be taken by somebody else.

## Phase one - the pre-war analysis, before a single unit moves

1. get_city_states: Brussels' tile, its owner, its military strength, and whether we are its Suzerain.
2. The suzerain gate, and it is the one that costs a war: if Brussels has a Suzerain, read that civilisation's
diplomacy for a defensive pact. A pact means the Suzerain joins the war the turn we declare, and that is a different
war than the one this file asks for - say so in the diary before declaring.
3. get_target_report on its tile: the walls and their pool, the city centre pool, the garrison unit, the defence
strength, the visible enemy units within three tiles, and the per-tile FIRE and NO LINE OF SIGHT verdicts. It works
before a declaration and in fog.
4. The arithmetic, in the diary and not in the head: what the walls are, what each gun does per turn against that
pool, against the city's heal, what the ranged line adds, how many turns that is, and what it costs. If the number
says the siege cannot be won, this task's answer is the one task 058 gave: do not open it.
5. get_reinforcements: which turn a corps unit still in a queue reaches the rally, and which roles nothing covers.

## Phase two - the staging, before the first move

6. The corps must be eight of eight. A corps short a role waits; five of eight is not a corps.
7. get_staging_plan on the city's tile: one row per unit - where it is, its movement, the one tile it goes to, the
path cost, the turn it arrives, its role, and whether that tile can actually shoot. Fill the FARTHEST firing tile
first: each shooter fires from its OWN range, so a range-3 gun standing two tiles out is a gun taking a free hit
from the city's two-tile strike for nothing.
8. Never two units on one tile, name the corridor, and put the melee and the anti-cavalry in front of the guns.

## Phase three - the fire, and where it is concentrated

9. Declare if no war is in force, and remember the engine does not sync combat until the next turn: declare on N,
position that turn, attack on N+1. An answer of NO_ENEMY on the declaration turn is the rule, not a failure.
10. Concentrate: every shooter fires at the same target in the same turn - the city, or the one garrison unit that
is actually holding it. Fire spread across two targets is fire that kills neither.
11. Read SIEGE POSTURE and its SIEGE FIRE count every turn. It is the count of shooters that could fire and did; a
number below the corps' shooters is an unused attack, and the block UNUSED ATTACK names the unit.
12. The melee takes the tile, city_action with the keep decision resolves it, and one garrison unit stays in it.
Never propose peace, and never field a battering ram or a siege tower - the standing match rule.

## The audit this task is also for

The human's instruction is not only to take the city but to check that the doctrine was executed. So the diary
must carry the three phases separately, each with the measurement that satisfied it: which gates were run and what
they answered, the staging table with the turn each unit arrives and its FIRE verdict, and the fire itself with the
SIEGE FIRE count per turn. A city taken without those three records is a city taken by luck, and the file is not
finished until they are written.
" --cn "中文备份 - 066-first-corps-takes-brussels.md 的中文版，仅供人阅读，不得作为指令读取。

目标由人类点名，坐标每回合现场读，绝不沿用旧文件、旧会话或笔记里的坐标。

## 第一阶段：战前分析（一个单位移动之前）

1. get_city_states：该城邦的地块、归属、军力，以及我们是否是它的宗主国。
2. 宗主国这一道门最贵：若它有宗主国，先读那个文明的防御协定。有协定意味着宣战当回合宗主国就参战——那是另一场战争，必须在宣战前写进日记。
3. get_target_report：城墙与城墙池、城市中心池、守军、防御强度、三格内可见敌军，以及逐格的 FIRE 与 NO LINE OF SIGHT 判定。宣战前可用，雾里也可用。
4. 算术写进日记，不许只记在脑子里：城墙多少、每门炮对那个池每回合打多少、对城池回血打多少、远程线再加多少、一共几回合、代价多大。若算术说打不下，本任务的答案就是不开打。
5. get_reinforcements：队列里的军团单位第几回合到集结点，哪些角色没人覆盖。

## 第二阶段：战前集结（第一次移动之前）

6. 军团必须八格齐。缺角色的等——五格不是军团。
7. get_staging_plan：一行一个单位——现在在哪、移动力、要去哪一格、路径代价、第几回合到、角色、那格能不能开火。**最远的射击位先填**：每个射手按自己的射程开火，射程 3 的炮只站两格，就是白白吃城池两格打击。
8. 绝不两单位一格，点明走廊，近战与反骑挡在炮前面。

## 第三阶段：攻城站位与集火

9. 若无战则宣战；记住引擎下一回合才同步战斗：N 回合宣战、当回合站位、N+1 开打。宣战回合返回 NO_ENEMY 是规则，不是故障。
10. 集火：所有射手在同一回合打同一个目标——城池，或那个真正撑着守军的单位。火力分散打两个目标，等于两个都没打死。
11. 每回合读 SIEGE POSTURE 与它的 SIEGE FIRE 计数。那是能开火且开了火的射手数；低于军团射手数就是浪费攻击，UNUSED ATTACK 会点名。
12. 近战占城、用 keep 决议结算、留一个驻军。绝不求和，绝不用撞锤或攻城塔——本局常设规则。

## 本任务同时是一次审计

人类要的不只是拿下城，还要核查兵法是否被执行。所以日记必须把三个阶段分开写，各自带上满足它的实测：跑了哪几道门、它们怎么回答；集结表逐行（到达回合与 FIRE 判定）；以及每回合 SIEGE FIRE 的开火数。没有这三份记录的城池是运气拿下的，本文件在那三份记录写完之前不算完成。
"
     at: 2026-10-10T22:21:23+08:00
     chinese backup: prompts/tasks/cn/066-first-corps-takes-brussels.cn.md
-->
