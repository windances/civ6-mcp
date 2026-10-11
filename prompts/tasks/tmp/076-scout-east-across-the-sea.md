# TEMP TASK 076 - One scout crosses the sea east to meet more civilizations

added:     2026-10-11 (human instruction: 侦察兵向东渡海探索更多文明，不恋战)
expires:   turn 330 - 40 turn(s) from T290, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 2 civilizations have been met that were not met when this file was published, with each
           meeting and its tile written in the diary, and the scout that made them is still alive.
overrides: the retired scout file, which asked for exploration without a direction: the direction is now east
           and the route crosses water. Task 075 westward rally and task 074 sieges do not touch
           this unit - it is never reassigned to a corps, never used as a screen, and never traded
           for damage.
scope:     one scout-line unit, its eastward route, the sea crossing it makes, the civilizations it meets, and
           the diary record of all of it.

## One scout, and it goes east

1. Exactly one scout-line unit. If none is alive, one is built or taken from the roster - not a party, not a corps. A second scout is not a second contact, it
is a second casualty.
2. The route is east: read the map east of our territory first, then the water beyond it, and name the crossing in the diary before it is attempted - the tile it
embarks from, the chain of water tiles, and the tile it lands on.
3. get_pathing_estimate on the unit gives the game own route; the current turn reachable set already accounts for an embark that spends the whole turn,
so the first water tile may be the only move that turn.
4. A land unit can only embark with Shipbuilding. If a crossing is refused for that reason, the answer is the tech, not a wall - say so and take the long way
round until it is researched.
5. Never begin a crossing whose middle tile cannot be reached and held in one turn: a unit caught at sea is a dead unit.

## Not drawn into a fight - the human words

6. This unit never attacks. Not a barbarian galley, not a scout, not a nearly dead unit. Its value is that it has seen something we have not.
7. It does not fortify in the open next to an enemy, and it does not stand its ground. If something hostile is within reach, it moves away first and reports
after - trading blows with a scout wins nothing and loses the map.
8. If a hostile unit blocks the only route, the answer is a wait out of sight or a longer way round, never a run through it.
9. automate is allowed only when the water and fog ahead hold no sighted enemy unit; otherwise one explicit move per turn. Automate has walked scouts into wars
before, and the file that governs this one forbids the fight it would walk into.

## Contact is the product

10. Each newly met civilization is reported the turn it appears: its name, the tile it was met on, and what get_diplomacy says about it.
11. The cheap courtesies the directive allows are made on first contact - a delegation where it costs us little, because that is gold spent for information.
12. Report each turn: where the scout is, what it sees, how many civilizations it has met since this file was published, and whether a crossing is under way.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "One scout crosses the sea east to meet more civilizations" --slug scout-east-across-the-sea --instruction 侦察兵向东渡海探索更多文明，不恋战 --done-when "count >= 2 civilizations have been met that were not met when this file was published, with each meeting and its tile written in the diary, and the scout that made them is still alive." --overrides "the retired scout file, which asked for exploration without a direction: the direction is now east and the route crosses water. Task 075 westward rally and task 074 sieges do not touch this unit - it is never reassigned to a corps, never used as a screen, and never traded for damage." --scope "one scout-line unit, its eastward route, the sea crossing it makes, the civilizations it meets, and the diary record of all of it." --why "send one scout east across the sea to meet more civilizations and keep it out of fights" --turns 40 --body "## One scout, and it goes east

1. Exactly one scout-line unit. If none is alive, one is built or taken from the roster - not a party, not a corps. A second scout is not a second contact, it
is a second casualty.
2. The route is east: read the map east of our territory first, then the water beyond it, and name the crossing in the diary before it is attempted - the tile it
embarks from, the chain of water tiles, and the tile it lands on.
3. get_pathing_estimate on the unit gives the game own route; the current turn reachable set already accounts for an embark that spends the whole turn,
so the first water tile may be the only move that turn.
4. A land unit can only embark with Shipbuilding. If a crossing is refused for that reason, the answer is the tech, not a wall - say so and take the long way
round until it is researched.
5. Never begin a crossing whose middle tile cannot be reached and held in one turn: a unit caught at sea is a dead unit.

## Not drawn into a fight - the human words

6. This unit never attacks. Not a barbarian galley, not a scout, not a nearly dead unit. Its value is that it has seen something we have not.
7. It does not fortify in the open next to an enemy, and it does not stand its ground. If something hostile is within reach, it moves away first and reports
after - trading blows with a scout wins nothing and loses the map.
8. If a hostile unit blocks the only route, the answer is a wait out of sight or a longer way round, never a run through it.
9. automate is allowed only when the water and fog ahead hold no sighted enemy unit; otherwise one explicit move per turn. Automate has walked scouts into wars
before, and the file that governs this one forbids the fight it would walk into.

## Contact is the product

10. Each newly met civilization is reported the turn it appears: its name, the tile it was met on, and what get_diplomacy says about it.
11. The cheap courtesies the directive allows are made on first contact - a delegation where it costs us little, because that is gold spent for information.
12. Report each turn: where the scout is, what it sees, how many civilizations it has met since this file was published, and whether a crossing is under way.
" --cn "中文备份 - 076-scout-east-across-the-sea.md 的中文版，仅供人阅读，不得作为指令读取。

## 一个侦察兵，向东

1. 只派一个侦察系单位。若已无存活，就造一个或从名册里调一个——不是一队，不是一支军团。第二个侦察兵不是第二份情报，是第二份伤亡。
2. 路线向东：先读我方领土以东的地图，再读其外的水域，渡海之前在日记里点名：从哪一格上船、中间串起哪些水格、在哪一格登陆。
3. 用 get_pathing_estimate 取游戏自己的路线；本回合可达集合已经把上船花掉整回合这件事算进去了，所以第一个水格很可能就是那一回合唯一的移动。
4. 陆军没有造船术不能上船。若因此被拒，答案是科技，不是墙——说明并绕远路，直到研究出来。
5. 绝不开始一次中间那格一回合内到不了、也守不住的渡海：卡在海上的单位就是死单位。

## 不恋战——人类原话

6. 这个单位永不攻击。不打野蛮人桨帆船、不打侦察兵、不打残血单位。它的价值在于它看见了我们没看见的东西。
7. 不在开阔地贴着敌人固守，也不原地硬顶。有敌意单位进入可及范围，先撤走、后报告——侦察兵换血什么都赢不到，只会输掉地图。
8. 若敌意单位堵住唯一通路，答案是在看不见的地方等，或者绕更远的路，绝不是硬冲过去。
9. 只有当前方水域与雾里没有已发现的敌意单位时，才允许用 automate；否则每回合一次明确移动。automate 以前就把侦察兵带进过战争，而本文件禁止的正是那场仗。

## 接触本身就是成果

10. 每遇到一个新文明，当回合就报：名字、遇到的格子、get_diplomacy 对它的说法。
11. 首触时做指令允许的廉价礼节——花得起就派代表团，那是用金币买情报。
12. 每回合报：侦察兵在哪、看见了什么、本文件发布以来接触了几个文明、是否正在渡海。
"
     at: 2026-10-11T12:47:05+08:00
     chinese backup: prompts/tasks/cn/076-scout-east-across-the-sea.cn.md
-->
