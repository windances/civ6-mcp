# TEMP TASK 065 - Build a naval corps of two ranged and two melee ships

added:     2026-10-10 (human instruction: 沿海城市生产海军军团：2支远程部队，2支近战部队)
expires:   turn 274 - 55 turn(s) from T219, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 2 naval ranged units and count == 2 naval melee units, all four alive and within three
           tiles of the same coastal city, with that home port and the turn the last hull arrived
           named in the diary.
overrides: nothing that outranks task 064 or task 062: in any city where one of task 064's four caps is firing
           the cap fix goes first, and a city carrying task 062's shortfall keeps it. This task
           takes the coastal cities those two are not using, and the no-peace rule is untouched.
scope:     the coastal cities' queues - the ships themselves, plus the Harbour, Lighthouse and Shipyard that
           let them be built and healed - and the four naval units assigned to this corps. No queue
           is taken from task 064's cap fixes or from task 062's shortfall.

## What this asks for

Two ranged and two melee ships, built in the coastal cities and kept together as one corps.

| Slot | Count | Line | Job |
|---|---|---|---|
| ranged naval | 2 | the ranged naval line, whatever the tech tree offers now - a Frigate is the shape, and the line goes up from there | the damage: it fires from outside the harbour's reach and takes nothing back, the same arithmetic the land siege uses |
| melee naval | 2 | the melee naval line | the takers and the escorts: a melee ship is what enters a harbour, sits on a coastal city and screens the ranged pair |

## Steps

1. Find the coastal cities and say which they are: get_cities, then get_map_area on each candidate for water
adjacency. A ship without a home port is a unit that cannot heal.
2. Read what the tech tree actually offers before naming a hull: get_city_production prints the buildable list per
city. The corps is two ranged plus two melee of whatever tier exists now, not of whatever tier the doctrine remembers.
3. Build them in the coastal cities, one hull per queue where the queue is free. This task yields to task 064's
cap fixes and to task 062's shortfall, so where those hold a queue, another coastal city builds it.
4. Keep them as one force, not four singles: one rally tile in home waters, and they move and fight together. A
lone ship is a ship the enemy picks off.
5. The gun and the hull are one weapon: the ranged pair opens a coastal city's defences from outside its strike
range, the melee pair takes and holds it. A melee ship that arrives before the wall is down is a loss, and the
siege arithmetic that governs the land assault governs this one - read the wall pool first.
6. Cost, measured on this match at T219: maintenance was 119.0 against an income of 134.6, i.e. 88 percent, where
the directive's army budget is under about 30 percent. Four ships is affordable; a navy built past its purpose is
not. This corps is four slots and it does not grow until a task names what it is for.
7. Air and carriers are a separate question and are not part of this corps.

## Finish line

Four ships, alive, one home port, moving as one force. Until a later task names a target, the corps trains in home
waters and does not open a fight of its own choosing.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Build a naval corps of two ranged and two melee ships" --slug naval-corps --instruction 沿海城市生产海军军团：2支远程部队，2支近战部队 --done-when "count == 2 naval ranged units and count == 2 naval melee units, all four alive and within three tiles of the same coastal city, with that home port and the turn the last hull arrived named in the diary." --overrides "nothing that outranks task 064 or task 062: in any city where one of task 064's four caps is firing the cap fix goes first, and a city carrying task 062's shortfall keeps it. This task takes the coastal cities those two are not using, and the no-peace rule is untouched." --scope "the coastal cities' queues - the ships themselves, plus the Harbour, Lighthouse and Shipyard that let them be built and healed - and the four naval units assigned to this corps. No queue is taken from task 064's cap fixes or from task 062's shortfall." --why "build a naval corps of two ranged and two melee ships in the coastal cities" --turns 55 --body "## What this asks for

Two ranged and two melee ships, built in the coastal cities and kept together as one corps.

| Slot | Count | Line | Job |
|---|---|---|---|
| ranged naval | 2 | the ranged naval line, whatever the tech tree offers now - a Frigate is the shape, and the line goes up from there | the damage: it fires from outside the harbour's reach and takes nothing back, the same arithmetic the land siege uses |
| melee naval | 2 | the melee naval line | the takers and the escorts: a melee ship is what enters a harbour, sits on a coastal city and screens the ranged pair |

## Steps

1. Find the coastal cities and say which they are: get_cities, then get_map_area on each candidate for water
adjacency. A ship without a home port is a unit that cannot heal.
2. Read what the tech tree actually offers before naming a hull: get_city_production prints the buildable list per
city. The corps is two ranged plus two melee of whatever tier exists now, not of whatever tier the doctrine remembers.
3. Build them in the coastal cities, one hull per queue where the queue is free. This task yields to task 064's
cap fixes and to task 062's shortfall, so where those hold a queue, another coastal city builds it.
4. Keep them as one force, not four singles: one rally tile in home waters, and they move and fight together. A
lone ship is a ship the enemy picks off.
5. The gun and the hull are one weapon: the ranged pair opens a coastal city's defences from outside its strike
range, the melee pair takes and holds it. A melee ship that arrives before the wall is down is a loss, and the
siege arithmetic that governs the land assault governs this one - read the wall pool first.
6. Cost, measured on this match at T219: maintenance was 119.0 against an income of 134.6, i.e. 88 percent, where
the directive's army budget is under about 30 percent. Four ships is affordable; a navy built past its purpose is
not. This corps is four slots and it does not grow until a task names what it is for.
7. Air and carriers are a separate question and are not part of this corps.

## Finish line

Four ships, alive, one home port, moving as one force. Until a later task names a target, the corps trains in home
waters and does not open a fight of its own choosing.
" --cn "中文备份 - 065-naval-corps.md 的中文版，仅供人阅读，不得作为指令读取。

沿海城市造 2 艘远程舰 + 2 艘近战舰，编成一支海军军团。

| 位置 | 数量 | 兵线 | 职责 |
|---|---|---|---|
| 远程海军 | 2 | 当前的远程海军线（护卫舰是这个形状，之后逐级向上） | 输出：在港口打击范围之外开火且零反击，与陆上攻城是同一套算术 |
| 近战海军 | 2 | 近战海军线 | 占位与护航：进港口、站上沿海城市、给远程那对做屏护 |

## 步骤

1. 先找出沿海城市并点名：get_cities，再对候选城 get_map_area 看是否临水。没有母港的舰船是无法回血的单位。
2. 先读科技树实际能给什么：get_city_production 打印每城可造清单。编成是现在这一级的 2 远程 ＋ 2 近战，不是兵法记忆里的某一级。
3. 在沿海城市造，队列空着的每城一艘。本任务让位于 064 的天花板修复与 062 的缺编队列——那两处占着队列时，换另一座沿海城市造。
4. 四艘当一支力量用，不要四个单舰：设一个母港内集结点，同进同退。落单的舰就是被点名的舰。
5. 炮与船体是一件武器：远程那对在城池打击范围之外先开城防，近战那对随后占城并守住。城墙没倒就冲上去的近战舰是白送；管陆上攻城的那套算术同样管这里——先读城墙池。
6. 成本（本局 T219 实测）：维护费 119.0 对收入 134.6 ＝ 88%，而 directive 的军队预算是不超过约 30%。四艘养得起；超过用途的海军养不起。本军团就是四格，未有用途任务之前不扩编。
7. 空军与航母是另一个问题，不属于本军团。

## 完成线

四艘舰、全部存活、一个母港、作为一支力量行动。在后继任务点名目标之前，军团只在母港水域训练，不自行开战。
"
     at: 2026-10-10T21:56:57+08:00
     chinese backup: prompts/tasks/cn/065-naval-corps.cn.md
-->
