# TEMP TASK 065 - Build a coastal fleet of two melee and three ranged ships, and clear the coast as it grows

added:     2026-10-11 (human instruction:
           修正海军军团任务：沿海城市生产海军舰队：2艘近战类军舰，3艘远程攻击军舰。不用等所有军舰都建好，有军舰就编入舰队，执行沿海清剿野蛮人和敌国部队的任务)
expires:   turn 299 - 35 turn(s) from T264, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 5 ships in the fleet - at least two naval melee and three naval ranged - and count == 0
           barbarian or enemy units within three tiles of any of our coastal cities, with the last
           sighting and its tile recorded in the diary.
overrides: the earlier naval file, which asked for two ranged and two melee that waited until all four existed:
           the fleet is now two melee and three ranged, and ships are commissioned the turn they
           appear. Task 064 keeps priority over queues where a cap is firing, and the no-peace rule
           is untouched.
scope:     the coastal cities queues for the five ships, the Harbour and its buildings where a ship needs to
           heal, and the fleet itself - its patrol of our coast, the barbarian and enemy units it
           engages, and its reports.

## What changed

Two things, both from the human instruction:

- The fleet is TWO melee and THREE ranged warships - five, not four.
- A ship joins the fleet the turn it appears. Nobody waits for the last hull. A commissioned ship is already useful, and a fleet
that waits in port is a fleet the enemy gets to choose when to fight.

## The mission, in the human words

Coastal clearance: barbarians and enemy units along our coast. Not city assaults, not blockades of somebody else harbour - those need a
separate task. This file is about the raiders that land on our shore, the barbarian galleys that sit off it, and any enemy unit that
comes within reach of a coastal city.

## Roles

1. Ranged ships (the Frigate line) do the killing: they fire from outside the target reach and take nothing back. Three of them is the
weight of the fleet.
2. Melee ships (the Ironclad line) are the screen and the takers: they stand between the raiders and a coastal city, and they finish what the
range cannot - a barbarian galley at zero health still has to be boarded or sunk at close quarters.
3. Read what the tech tree offers before naming a hull: get_city_production per coastal city. The fleet is the best tier that exists now.

## Operating rules

4. A ship that appears sails for the nearest reported raider or the nearest coastal city under threat. It does not wait in port for company.
5. Ships heal in a Harbour or a coastal city. A ship damaged below half strength goes to the nearest one and comes back - trading a ship for one
raider is a loss.
6. Do not seek a fight with a superior enemy fleet. The job is clearing raiders from our shore, not winning the sea. If an enemy fleet
appears in strength, withdraw into harbour range, report it, and let the task be changed.
7. Report each turn in the diary: how many ships are in the fleet by role, what was sighted, what was engaged, and what got away.
8. Keep the missing hulls in the queues while the fleet works - a fleet that starts short should not stay short.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --replace --title "Build a coastal fleet of two melee and three ranged ships, and clear the coast as it grows" --slug naval-corps --instruction 修正海军军团任务：沿海城市生产海军舰队：2艘近战类军舰，3艘远程攻击军舰。不用等所有军舰都建好，有军舰就编入舰队，执行沿海清剿野蛮人和敌国部队的任务 --done-when "count >= 5 ships in the fleet - at least two naval melee and three naval ranged - and count == 0 barbarian or enemy units within three tiles of any of our coastal cities, with the last sighting and its tile recorded in the diary." --overrides "the earlier naval file, which asked for two ranged and two melee that waited until all four existed: the fleet is now two melee and three ranged, and ships are commissioned the turn they appear. Task 064 keeps priority over queues where a cap is firing, and the no-peace rule is untouched." --scope "the coastal cities queues for the five ships, the Harbour and its buildings where a ship needs to heal, and the fleet itself - its patrol of our coast, the barbarian and enemy units it engages, and its reports." --why "build a fleet of two melee and three ranged warships, commission them as they appear, and clear barbarians and enemy units from our coast" --turns 35 --body "## What changed

Two things, both from the human instruction:

- The fleet is TWO melee and THREE ranged warships - five, not four.
- A ship joins the fleet the turn it appears. Nobody waits for the last hull. A commissioned ship is already useful, and a fleet
that waits in port is a fleet the enemy gets to choose when to fight.

## The mission, in the human words

Coastal clearance: barbarians and enemy units along our coast. Not city assaults, not blockades of somebody else harbour - those need a
separate task. This file is about the raiders that land on our shore, the barbarian galleys that sit off it, and any enemy unit that
comes within reach of a coastal city.

## Roles

1. Ranged ships (the Frigate line) do the killing: they fire from outside the target reach and take nothing back. Three of them is the
weight of the fleet.
2. Melee ships (the Ironclad line) are the screen and the takers: they stand between the raiders and a coastal city, and they finish what the
range cannot - a barbarian galley at zero health still has to be boarded or sunk at close quarters.
3. Read what the tech tree offers before naming a hull: get_city_production per coastal city. The fleet is the best tier that exists now.

## Operating rules

4. A ship that appears sails for the nearest reported raider or the nearest coastal city under threat. It does not wait in port for company.
5. Ships heal in a Harbour or a coastal city. A ship damaged below half strength goes to the nearest one and comes back - trading a ship for one
raider is a loss.
6. Do not seek a fight with a superior enemy fleet. The job is clearing raiders from our shore, not winning the sea. If an enemy fleet
appears in strength, withdraw into harbour range, report it, and let the task be changed.
7. Report each turn in the diary: how many ships are in the fleet by role, what was sighted, what was engaged, and what got away.
8. Keep the missing hulls in the queues while the fleet works - a fleet that starts short should not stay short.
" --cn "中文备份 - 065-naval-corps.md 的中文版，仅供人阅读，不得作为指令读取。

按人类指令修正两处：

- 舰队为**2 艘近战 + 3 艘远程**，共五艘（原来写的是 2+2=4）。
- **军舰造出来当回合即编入舰队**，不等最后一艘。已服役的舰立刻有用；而在港里等的舰队，是把开战时机交给敌人去选。

## 任务（人类原话）

**沿海清剿：野蛮人与敌国部队**。不是攻城，也不是封锁别人的港口——那些需要另行发布任务。本文件管的是：在我们海岸登陆的掠夺者、停在我们近海的野蛮人桨帆船，以及任何进入沿海城市打击范围内的敌军单位。

## 角色

1. 远程舰（护卫舰线）负责击杀：在目标射程之外开火、零反击。三艘是舰队的重心。
2. 近战舰（铁甲舰线）是屏护与收尾：挡在掠夺者与沿海城市之间，处理远程收不掉的目标——零血的野蛮人桨帆船仍须近距离击沉或接舷。
3. 命名船体之前先读科技树：逐沿海城市 get_city_production。舰队用现在这一级里最好的。

## 作战规则

4. 新舰一出现就驶向最近被报告的掠夺者或最近受威胁的沿海城市，**不在港里等同伴**。
5. 舰船在港口或沿海城市回血。低于半血的舰先回港、修好再回来——用一艘舰换一个掠夺者，是亏的。
6. **不与占优的敌舰队硬拼**。任务是清我方海岸的掠夺者，不是争制海权。若敌方舰队强势出现，退入港口打击范围、上报，让任务去改。
7. 每回合日记写清：按角色的舰数、看见了什么、打了什么、什么跑了。
8. 缺的船体继续留在队列里——开局不满编的舰队，不该一直不满编。
"
     at: 2026-10-11T01:08:33+08:00
     chinese backup: prompts/tasks/cn/065-naval-corps.cn.md
-->
