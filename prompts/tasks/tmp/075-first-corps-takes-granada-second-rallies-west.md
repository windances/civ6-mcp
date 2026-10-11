# TEMP TASK 075 - The first corps takes the city the human named, the second rallies west

added:     2026-10-11 (human instruction: 第一攻城军团拿下格拉纳达，第二军团向西集结)
expires:   turn 312 - 25 turn(s) from T287, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 1 city named Granada is ours - resolved with the keep decision and one garrison unit left
           behind - and the second siege corps has assembled at a rally tile west of where it stood,
           named in the diary with the turn each of its units arrives.
overrides: task 074 for these two corps only: corps one no longer picks its own city, because the target is
           named here, and corps two opens no siege of its own this window because its work is the
           westward march and the rally. Everything else stands - the three named calls before any
           volley, the four phases, the taking unit arithmetic, the concentration of fire, no
           battering ram, no siege tower and no peace.
scope:     the first siege corps and the city the human named as its target, and the second siege corps and its
           march west to a rally tile - plus the diary record of both.

## Two orders, one file

1. The FIRST siege corps takes Granada.
2. The SECOND siege corps assembles westward.

The city is named by the human, so the finding half of task 074 is settled for corps one: it does not shop for a target. The name the human
used governs: if the game shows the same city under another spelling, that is the city, and the diary names both.

## Corps one: Granada

1. If Granada is not yet visible, Gate 0 of tactics/07 comes first: send the fastest unit of the corps toward it and run the analysis the turn it
appears. An army that cannot see its target has nothing to analyse.
2. Once it is visible, the three calls are the first three things done, in this order, and all three go in the diary the same turn: get_target_report on
the city, the choice stated, then get_staging_plan on it with its per-tile FIRE verdicts.
3. Then the four phases: the walls to zero, the city centre pool to zero, and the walk-in - a melee unit moves onto the city tile. Ranged and siege units
never capture, and the taking unit attack counts as pool damage.
4. Resolve with the keep decision, leave ONE garrison unit, and report the two pools as read, the arithmetic, the turns of fire, the turn it fell and the
garrison.
5. If the arithmetic says the corps cannot break it, the answer is reinforcements or a longer stage, never a thinner attack: state in the diary what is missing
and when it arrives - task 062 is the file that fills the roster.

## Corps two: west, and assembled

6. Choose the rally tile and write it down: one tile per unit, on or beside a road where there is one, outside the reach of any enemy ranged unit, and
facing the direction of march rather than back the way it came.
7. Write the march table: for each unit, where it is, the tile it goes to, the path cost, and the turn it arrives. Never two units on one tile - a jammed
column arrives a turn late and is bombarded while it waits.
8. The unit that screens is the melee and anti-cavalry line, and it arrives first. Ranged and siege units stage behind them and never lead.
9. The corps fights what it meets on the march - it does not divert to a city and it does not open a siege this window.
10. Report each turn: how many units have arrived, how many are still on the road, and the arrival turn of the last one.

## Standing rules

Never a battering ram, never a siege tower, never peace. One garrison per captured city. Every claim in the diary carries the call that produced it.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "The first corps takes the city the human named, the second rallies west" --slug first-corps-takes-granada-second-rallies-west --instruction 第一攻城军团拿下格拉纳达，第二军团向西集结 --done-when "count == 1 city named Granada is ours - resolved with the keep decision and one garrison unit left behind - and the second siege corps has assembled at a rally tile west of where it stood, named in the diary with the turn each of its units arrives." --overrides "task 074 for these two corps only: corps one no longer picks its own city, because the target is named here, and corps two opens no siege of its own this window because its work is the westward march and the rally. Everything else stands - the three named calls before any volley, the four phases, the taking unit arithmetic, the concentration of fire, no battering ram, no siege tower and no peace." --scope "the first siege corps and the city the human named as its target, and the second siege corps and its march west to a rally tile - plus the diary record of both." --why "have the first siege corps take the city the human named and assemble the second corps westward" --turns 25 --body "## Two orders, one file

1. The FIRST siege corps takes Granada.
2. The SECOND siege corps assembles westward.

The city is named by the human, so the finding half of task 074 is settled for corps one: it does not shop for a target. The name the human
used governs: if the game shows the same city under another spelling, that is the city, and the diary names both.

## Corps one: Granada

1. If Granada is not yet visible, Gate 0 of tactics/07 comes first: send the fastest unit of the corps toward it and run the analysis the turn it
appears. An army that cannot see its target has nothing to analyse.
2. Once it is visible, the three calls are the first three things done, in this order, and all three go in the diary the same turn: get_target_report on
the city, the choice stated, then get_staging_plan on it with its per-tile FIRE verdicts.
3. Then the four phases: the walls to zero, the city centre pool to zero, and the walk-in - a melee unit moves onto the city tile. Ranged and siege units
never capture, and the taking unit attack counts as pool damage.
4. Resolve with the keep decision, leave ONE garrison unit, and report the two pools as read, the arithmetic, the turns of fire, the turn it fell and the
garrison.
5. If the arithmetic says the corps cannot break it, the answer is reinforcements or a longer stage, never a thinner attack: state in the diary what is missing
and when it arrives - task 062 is the file that fills the roster.

## Corps two: west, and assembled

6. Choose the rally tile and write it down: one tile per unit, on or beside a road where there is one, outside the reach of any enemy ranged unit, and
facing the direction of march rather than back the way it came.
7. Write the march table: for each unit, where it is, the tile it goes to, the path cost, and the turn it arrives. Never two units on one tile - a jammed
column arrives a turn late and is bombarded while it waits.
8. The unit that screens is the melee and anti-cavalry line, and it arrives first. Ranged and siege units stage behind them and never lead.
9. The corps fights what it meets on the march - it does not divert to a city and it does not open a siege this window.
10. Report each turn: how many units have arrived, how many are still on the road, and the arrival turn of the last one.

## Standing rules

Never a battering ram, never a siege tower, never peace. One garrison per captured city. Every claim in the diary carries the call that produced it.
" --cn "中文备份 - 075-first-corps-takes-granada-second-rallies-west.md 的中文版，仅供人阅读，不得作为指令读取。

## 两条命令，一个文件

1. **第一攻城军团拿下格拉纳达。**
2. **第二军团向西集结。**

城市由人类点名，所以第一军团不需要自行挑选——074 的发现那一半在此已被定死。人类用的名字为准：若游戏里显示的是同一座城的另一种拼写，那就是那座城，日记里两种名字都写。

## 第一军团：格拉纳达

1. 若格拉纳达尚不可见，先走 tactics/07 的 Gate 0：把军团里最快的单位派过去，它一出现的那一回合就做分析。看不见目标的军队没有可分析的东西。
2. 可见之后，最先做的三件事就是那三个调用，按此顺序，且当回合全部写进日记：对城跑 get_target_report → 写明选择 → 对它跑 get_staging_plan（含逐格 FIRE 判定）。
3. 然后四个阶段：先墙到 0，再中心池到 0，然后走进城——由近战单位移动到城格。远程与攻城永远不能占领，占城部队的攻击计入池伤害。
4. 用 keep 决议结算，留一个驻军，并报告：读到时的两条血条、算术、开火回合数、陷落回合、留下的驻军。
5. 若算术说明打不下，答案是增援或延长集结，绝不是更薄的一次进攻：在日记里写清缺什么、什么时候到——补编成的那份文件是 062。

## 第二军团：向西，并且成建制

6. 选定集结点并写下来：一单位一格、有路就靠路、在敌方远程射程之外、朝向行军方向而不是背向。
7. 写出行军表：每个单位——现在在哪、去哪格、路径代价、第几回合到。绝不两单位一格：堵住的纵队会晚到一回合，并在等待时挨炮。
8. 屏护由近战与反骑线担任，且最先到；远程与攻城在其后集结，绝不走在前面。
9. 军团打它在路上遇到的东西——不为一座城改道，本窗口内不自行开城战。
10. 每回合报告：到了几个、还在路上几个、最后一个的到达回合。

## 常设规则

绝不用撞锤、绝不用攻城塔、绝不求和。每座占领城留一个驻军。日记里每条断言都要带上产生它的那次调用。
"
     at: 2026-10-11T12:14:23+08:00
     chinese backup: prompts/tasks/cn/075-first-corps-takes-granada-second-rallies-west.cn.md
-->
