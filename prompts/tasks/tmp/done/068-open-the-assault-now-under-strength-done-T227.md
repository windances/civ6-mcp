# TEMP TASK 068 - Open the assault now, with both corps at whatever strength they stand

added:     2026-10-10 (human instruction: 目前第一军团兵力可以开打，第二军团也可参与，即使不满编)
expires:   turn 266 - 40 turn(s) from T226, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 1 assault is open - the first corps has fired on its target this turn or stands adjacent to
           it with a legal attack - and the diary names, role by role, the strength each corps
           entered the fight with, including which slots were short.
overrides: tasks 062 and 066 and 067, on the strength precondition and on one establishment at a time: the
           human has released both siege corps to fight now, under strength, and the second corps
           may take part as well. Nothing else is lifted - the pre-war arithmetic still decides
           whether a siege can be won, the three phases still run in order, the composition of each
           corps is unchanged, and no peace is proposed.
scope:     the first and the second siege corps of task 062, both released to fight before they are whole, plus
           the city queues that finish their missing slots while they fight. The first corps keeps
           the target task 066 named; the second either joins that fight or proceeds to the target
           task 067 defines.

## What changed

The corps no longer wait to be eight of eight. A corps that fights at seven of eight while the eighth is in a city
queue is worth more than a corps that arrives complete thirty turns after the moment passed. Both corps are released, and
the second may take part in the same fight.

## What did NOT change

The strength gate was the only thing released. Everything that decides whether a fight is worth opening still stands:
the pre-war analysis with its arithmetic, the staging table, the concentration of fire, the three phases in order, no
battering ram and no siege tower, and no peace ever. An under-strength corps that walks into a siege the arithmetic
says it cannot win is still the one mistake this match does not need to repeat.

## Steps

1. get_units: state the strength of each corps ROLE BY ROLE - how many ranged, how many melee, how many fast, and
which slots are short. That list goes in the diary before the first move, because it is what the human just released and it
is also what the plan has to work around.
2. Work around the missing role, do not ignore it: with no anti-cavalry, screen with the fast pair; with fewer ranged than
four, the fire takes more turns and the arithmetic in step 3 has to show that it still breaks the wall pool.
3. Run the pre-war arithmetic on the target as it actually stands, with the units actually present. If the number says the
siege cannot be won, this file does not open it - say so, and say which single unit would change the answer.
4. Staging still runs before the first move: get_staging_plan, the farthest firing tile filled first, each shooter at its own
range, never two units on one tile, melee and anti-cavalry in front of the guns.
5. Two corps on one city is allowed now. What is not allowed is fire split so thin that neither target dies: if both
corps engage the same city, both fire at it in the same turn. If the second corps takes its own target from task 067,
check that each group still has enough shooters to break its own wall pool before splitting them.
6. Every shooter fires every turn. Read SIEGE POSTURE and its SIEGE FIRE count: a number below the shooters present is an
unused attack, and UNUSED ATTACK names the unit.
7. The melee takes the tile, the capture is resolved with the keep decision, and one garrison unit stays in it.
8. Keep the missing slots in the queues while the fight runs - the corps that starts short should not stay short.

## The record

The diary carries: the strength each corps entered with, role by role; the arithmetic that justified opening; the staging
table; and the SIEGE FIRE count per turn. The human released a precondition - the record is what shows the release was
used well rather than simply used.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Open the assault now, with both corps at whatever strength they stand" --slug open-the-assault-now-under-strength --instruction 目前第一军团兵力可以开打，第二军团也可参与，即使不满编 --done-when "count >= 1 assault is open - the first corps has fired on its target this turn or stands adjacent to it with a legal attack - and the diary names, role by role, the strength each corps entered the fight with, including which slots were short." --overrides "tasks 062 and 066 and 067, on the strength precondition and on one establishment at a time: the human has released both siege corps to fight now, under strength, and the second corps may take part as well. Nothing else is lifted - the pre-war arithmetic still decides whether a siege can be won, the three phases still run in order, the composition of each corps is unchanged, and no peace is proposed." --scope "the first and the second siege corps of task 062, both released to fight before they are whole, plus the city queues that finish their missing slots while they fight. The first corps keeps the target task 066 named; the second either joins that fight or proceeds to the target task 067 defines." --why "release both siege corps to fight now, under strength, on the human instruction" --turns 40 --body "## What changed

The corps no longer wait to be eight of eight. A corps that fights at seven of eight while the eighth is in a city
queue is worth more than a corps that arrives complete thirty turns after the moment passed. Both corps are released, and
the second may take part in the same fight.

## What did NOT change

The strength gate was the only thing released. Everything that decides whether a fight is worth opening still stands:
the pre-war analysis with its arithmetic, the staging table, the concentration of fire, the three phases in order, no
battering ram and no siege tower, and no peace ever. An under-strength corps that walks into a siege the arithmetic
says it cannot win is still the one mistake this match does not need to repeat.

## Steps

1. get_units: state the strength of each corps ROLE BY ROLE - how many ranged, how many melee, how many fast, and
which slots are short. That list goes in the diary before the first move, because it is what the human just released and it
is also what the plan has to work around.
2. Work around the missing role, do not ignore it: with no anti-cavalry, screen with the fast pair; with fewer ranged than
four, the fire takes more turns and the arithmetic in step 3 has to show that it still breaks the wall pool.
3. Run the pre-war arithmetic on the target as it actually stands, with the units actually present. If the number says the
siege cannot be won, this file does not open it - say so, and say which single unit would change the answer.
4. Staging still runs before the first move: get_staging_plan, the farthest firing tile filled first, each shooter at its own
range, never two units on one tile, melee and anti-cavalry in front of the guns.
5. Two corps on one city is allowed now. What is not allowed is fire split so thin that neither target dies: if both
corps engage the same city, both fire at it in the same turn. If the second corps takes its own target from task 067,
check that each group still has enough shooters to break its own wall pool before splitting them.
6. Every shooter fires every turn. Read SIEGE POSTURE and its SIEGE FIRE count: a number below the shooters present is an
unused attack, and UNUSED ATTACK names the unit.
7. The melee takes the tile, the capture is resolved with the keep decision, and one garrison unit stays in it.
8. Keep the missing slots in the queues while the fight runs - the corps that starts short should not stay short.

## The record

The diary carries: the strength each corps entered with, role by role; the arithmetic that justified opening; the staging
table; and the SIEGE FIRE count per turn. The human released a precondition - the record is what shows the release was
used well rather than simply used.
" --cn "中文备份 - 068-open-the-assault-now-under-strength.md 的中文版，仅供人阅读，不得作为指令读取。

## 变了什么

军团不再等八格齐。七个半打，比三十回合后才到齐更值。两个军团都放行，第二军团可以参与同一场战斗。

## 没变什么

只放行了兵力门槛。决定一场攻城值不值得开打的东西全部照旧：战前分析与算术、集结表、集火、三阶段顺序、不用撞锤与攻城塔、绝不求和。兵力不足却冲进算术说打不下的围城，仍是本局最不需要重演的错误。

## 步骤

1. get_units：**按角色**报出两个军团各自的兵力——几个远程、几个近战、几个高机动、缺哪一格。这份清单在第一次移动之前写进日记：它既是人类刚放行的东西，也是计划必须绕开的现实。
2. 绕过缺口，而不是无视它：没有反骑就用高机动那对做屏护；远程不足四个，开火就要更多回合，第 3 步的算术必须证明它仍能打破城墙池。
3. 用**实际在场的单位**对目标跑战前算术。若算术说打不下，本文件不开打——说明它，并说明**再补哪一个单位**就能改变答案。
4. 集结仍然先于第一次移动：get_staging_plan、最远的射击位先填、每个射手按自己的射程、绝不两单位一格、近战与反骑在炮前面。
5. 现在允许两个军团打同一座城。不允许的是火力分散到两个目标都打不死：两军团打同一城，就同回合一起打它；第二军团若走 067 自己的目标，先确认两组各自的射手仍足以打破各自面对的城墙池。
6. 每回合每个射手都要开火。读 SIEGE POSTURE 与 SIEGE FIRE 计数：低于在场射手数就是浪费攻击，UNUSED ATTACK 会点名。
7. 近战占城、用 keep 决议结算、留一个驻军。
8. 打的同时把缺的那几格留在队列里——开局就不满编的军团，不该一直不满编。

## 记录

日记要带：两军团进场时**按角色**的兵力；开打的算术依据；集结表；每回合 SIEGE FIRE 计数。人类放行了一条前置——记录是用来证明这条放行**被用好**，而不只是被用掉。
"
     at: 2026-10-10T22:39:01+08:00
     chinese backup: prompts/tasks/cn/068-open-the-assault-now-under-strength.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 068 --done --turn 227 --note "an assault opened under strength: corps A entered at 8 of 8 with its five Bombards attached, corps B at 2 of 8 alive (ranged 1, melee 1, fast 0, with 3 ranged / 1 melee / 2 fast still in queues); Brussels fell at T227 on the T226-T227 fire, with the role-by-role strength recorded in the T226 and T227 diary entries"
     at: 2026-10-10T22:48:18+08:00
     status: done at T227
     chinese backup: prompts/tasks/cn/068-open-the-assault-now-under-strength.cn.md
-->
