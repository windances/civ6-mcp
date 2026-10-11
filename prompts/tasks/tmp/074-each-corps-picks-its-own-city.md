# TEMP TASK 074 - Every newly discovered civilization is a target, prepared for before it is attacked

added:     2026-10-11 (human instruction: 074修改：发现的新文明不论是否是敌国，都作为占领目标，进入战前准备。 两个攻城军团，各自挑选敌国目标城市，并占领)
expires:   turn 359 - 60 turn(s) from T299, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 2 enemy cities have been captured since this file was published, at least one by each siege
           corps, each with its get_target_report reading and its staging table written in the diary
           on or before the turn its first volley was fired, and the first of them preceded by a
           written pre-war preparation of a newly discovered civilization.
overrides: task 074 as it stood, which waited for an existing enemy city and therefore could not run while the
           empire was at peace: discovery is now the trigger, any newly discovered civilization is a
           target, and preparation runs at peace. For executing this file the war declaration on a
           target it selects is authorized - the corps names the civilization in the diary, the
           declaration goes in on the turn the staging table is ready, and the first volley lands
           the next turn because the combat engine only syncs then. Task 075 second half, task 065,
           task 076 and the no-peace rule are untouched.
scope:     both siege corps - the civilizations they discover, the pre-war preparation on them, the city each
           corps chooses from one of them, the siege - plus the city queues that finish the slots
           they are short of.

## Discovery is the trigger

1. Any civilization newly discovered - friend, neutral or enemy - becomes a capture target and enters pre-war preparation. The state of the relationship is not a
filter: NEUTRAL and UNFRIENDLY civilizations are targets exactly as an enemy is, and a civilization we have never met cannot be one until the scout meets it.
2. Preparation is the three calls, in this order, and all three go in the diary the same turn: get_target_report on that civilization nearest city, the choice stated
with its reason, then get_staging_plan on the chosen city with its per-tile FIRE verdicts.
3. Preparation runs at peace. It does not wait for a war: the analysis, the staging table, the reinforcement list from get_reinforcements and the march times are all
produced while the state is still NEUTRAL, which is the whole point of the change.
4. The war follows the preparation, not the other way round: the declaration goes in on the turn the staging table is ready and the corps is in the ring, so the first
volley lands the NEXT turn - the combat engine does not sync until then, and attacks on the declaration turn answer NO_ENEMY.
5. A civilization already at war needs no declaration; its preparation starts the turn it is seen.

## Which city

6. Read the two pools before choosing: get_target_report prints the walls and their pool, the city centre pool, the garrison, the defence strength and the visible enemy
units within three tiles. A city is a candidate only if the arithmetic on those numbers says the corps can break it.
7. The pick is the nearest city that passes step 6. Distance decides among the winnable, never over them.
8. Read the defensive pacts before the declaration and name them, because one war can become two.
9. Once the first volley is fired the target is frozen. No shopping for a better city mid-siege.
10. The two corps pick different cities unless only one is worth taking. Two thin attacks kill neither.

## One war at a time

11. The empire fights one war at a time (tactics/08): a corps does not open a second front while the first city is still under siege, and a corps that has taken its city
garrisons it before it prepares the next one.

## Then the four phases, every time

12. The walls to zero, then the city centre pool to zero, then the walk-in: a melee unit moves onto the city tile. Ranged and siege units never capture.
13. The taking unit attack counts as pool damage and the walk-in needs movement left - the choice is written out in task 072.

## The record, per city

14. The two get_target_report readings, the reason the city was chosen, the staging table with its FIRE verdicts, the SIEGE FIRE count per turn, the turn it fell,
the garrison left behind, and which corps took it. A city taken without that record does not count for this file.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --replace --title "Every newly discovered civilization is a target, prepared for before it is attacked" --slug each-corps-picks-its-own-city --instruction "074修改：发现的新文明不论是否是敌国，都作为占领目标，进入战前准备。 两个攻城军团，各自挑选敌国目标城市，并占领" --done-when "count >= 2 enemy cities have been captured since this file was published, at least one by each siege corps, each with its get_target_report reading and its staging table written in the diary on or before the turn its first volley was fired, and the first of them preceded by a written pre-war preparation of a newly discovered civilization." --overrides "task 074 as it stood, which waited for an existing enemy city and therefore could not run while the empire was at peace: discovery is now the trigger, any newly discovered civilization is a target, and preparation runs at peace. For executing this file the war declaration on a target it selects is authorized - the corps names the civilization in the diary, the declaration goes in on the turn the staging table is ready, and the first volley lands the next turn because the combat engine only syncs then. Task 075 second half, task 065, task 076 and the no-peace rule are untouched." --scope "both siege corps - the civilizations they discover, the pre-war preparation on them, the city each corps chooses from one of them, the siege - plus the city queues that finish the slots they are short of." --why "make every newly discovered civilization a capture target that enters pre-war preparation" --turns 60 --body "## Discovery is the trigger

1. Any civilization newly discovered - friend, neutral or enemy - becomes a capture target and enters pre-war preparation. The state of the relationship is not a
filter: NEUTRAL and UNFRIENDLY civilizations are targets exactly as an enemy is, and a civilization we have never met cannot be one until the scout meets it.
2. Preparation is the three calls, in this order, and all three go in the diary the same turn: get_target_report on that civilization nearest city, the choice stated
with its reason, then get_staging_plan on the chosen city with its per-tile FIRE verdicts.
3. Preparation runs at peace. It does not wait for a war: the analysis, the staging table, the reinforcement list from get_reinforcements and the march times are all
produced while the state is still NEUTRAL, which is the whole point of the change.
4. The war follows the preparation, not the other way round: the declaration goes in on the turn the staging table is ready and the corps is in the ring, so the first
volley lands the NEXT turn - the combat engine does not sync until then, and attacks on the declaration turn answer NO_ENEMY.
5. A civilization already at war needs no declaration; its preparation starts the turn it is seen.

## Which city

6. Read the two pools before choosing: get_target_report prints the walls and their pool, the city centre pool, the garrison, the defence strength and the visible enemy
units within three tiles. A city is a candidate only if the arithmetic on those numbers says the corps can break it.
7. The pick is the nearest city that passes step 6. Distance decides among the winnable, never over them.
8. Read the defensive pacts before the declaration and name them, because one war can become two.
9. Once the first volley is fired the target is frozen. No shopping for a better city mid-siege.
10. The two corps pick different cities unless only one is worth taking. Two thin attacks kill neither.

## One war at a time

11. The empire fights one war at a time (tactics/08): a corps does not open a second front while the first city is still under siege, and a corps that has taken its city
garrisons it before it prepares the next one.

## Then the four phases, every time

12. The walls to zero, then the city centre pool to zero, then the walk-in: a melee unit moves onto the city tile. Ranged and siege units never capture.
13. The taking unit attack counts as pool damage and the walk-in needs movement left - the choice is written out in task 072.

## The record, per city

14. The two get_target_report readings, the reason the city was chosen, the staging table with its FIRE verdicts, the SIEGE FIRE count per turn, the turn it fell,
the garrison left behind, and which corps took it. A city taken without that record does not count for this file.
" --cn "中文备份 - 074-each-corps-picks-its-own-city.md 的中文版，仅供人阅读，不得作为指令读取。

## 发现即触发（人类指令）

1. 任何新发现的文明——友好、中立或敌对——都成为占领目标并进入战前准备。关系状态不是筛选条件：中立与不友善的文明和敌国一样是目标；而我们从未见过的文明，在侦察兵见到它之前不算。
2. 准备的三个调用，按此顺序，且当回合全部写进日记：对该文明最近的城市跑 get_target_report → 写明选择及理由 → 对选定城市跑 get_staging_plan（含逐格 FIRE）。
3. 准备在和平期进行。它不等战争：两条血条、集结表、增援表（get_reinforcements）与行军时间全部在仍为 NEUTRAL 时产出——这正是本次改动的要点。
4. 战争跟在准备后面，而不是反过来：集结表就绪且军团进入环上的那一回合才宣战，第一轮齐射落在**下一回合**——战斗引擎届时才同步，宣战当回合的攻击会答 NO_ENEMY。
5. 已经交战的文明不需要宣战，见到即开始准备。

## 挑哪座城

6. 选择之前先读两条血条：城墙池、城市中心池、守军、防御强度、三格内可见敌军。只有算术说打得下，那座城才是候选。
7. 在通过第 6 步的城市里挑最近的。距离只在打得下的范围里决定，绝不越过它。
8. 宣战前读出防御协定并点名——一场战争可能变成两场。
9. 第一轮齐射之后目标冻结，不在围城途中换城。
10. 两个军团挑不同的城，除非只有一座值得打。两路薄攻，两路都打不死。

## 一次只打一场战争

11. 帝国一次只打一场战争（tactics/08）：前一城仍在围城时，军团不开第二战线；拿下城的军团先留驻军，再准备下一个目标。

## 然后每次都走四个阶段

12. 先墙到 0，再中心池到 0，然后走进城：由近战单位移动到城格。远程与攻城永远不能占领。
13. 占城部队的攻击计入池伤害，进城需要留有移动力——选择写在 072 里。

## 每座城的记录

14. 两行 get_target_report 读数、选它的理由、逐格 FIRE 的集结表、每回合 SIEGE FIRE 计数、陷落回合、留下的驻军、以及是哪支军团拿下的。没有这份记录的城，本文件不计。
"
     at: 2026-10-11T14:18:50+08:00
     chinese backup: prompts/tasks/cn/074-each-corps-picks-its-own-city.cn.md
-->
