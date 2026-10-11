# TEMP TASK 077 - Keep the two siege corps at strength: a roster each turn and a source for every shortfall

added:     2026-10-11 (human instruction: ok（同意补一条军团维护文件：每回合两份名册、缺编指定城市排产、大将随军、一次一仗）)
expires:   turn 419 - 120 turn(s) from T299, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 2 corps rosters appear in the diary on the same turn - each naming the corps, its tile, its
           count of ranged, melee and fast, and which slot is short - and every shortfall named that
           way has a city queue or a unit named for it before that corps next attacks.
overrides: task 064 queues, where a cap is firing: the cap fix keeps the queue. Task 074 three named calls and
           four phases, task 075 named target and march, task 065 and the no-peace rule are all
           untouched. This file only decides who maintains the rosters - it never chooses a target.
scope:     the two siege corps as rosters - who belongs, which role each unit fills, which slot is short - the
           city queues that fill a short role, the Great General or Admiral that travels with a
           corps, and the diary record of both rosters.

## What this file takes over

Task 062 built the two corps and retired at turn 284 with the establishment declared complete. It also carried the maintenance half - fill the short slots, keep the
roles - and that half retired with it, which left the corps decaying with nobody responsible. This file is that half, and only that half. Measured when it
was written: corps one carried a Line Infantry at 55 of 100 and a Cavalry at 72; corps two stood at five units - three shooters, one cavalry, one melee - with no
anti-cavalry slot and no screen at all.

## The roster, every turn

1. Both rosters go in the diary on the same turn, and each one names: the corps, the tile it stands on, how many ranged, how many melee and how many fast are ALIVE
and assigned, and which slot is short. That roster is the only durable record that a unit belongs to a corps - the game has no such attribute, and nothing else in the loop
can recover the grouping once the diary is silent.
2. A corps is at establishment at four ranged, two melee and two fast. Anything above that is spare and belongs to the other corps or the home front.
3. A unit under half strength, and the last garrison of a city we just took, are not counted in the roster until they are healed or replaced. Eight on paper and six in the
field is not a corps.

## Filling a short slot

4. Every shortfall named in the roster gets a place to come from the same turn it is named: a city queue, a unit already in the army, or a purchase. Name the city and the
turn the unit is due. A shortfall with no source named is a shortfall that will still be there in twenty turns.
5. get_reinforcements answers the deadline half: which queued military unit reaches the rally and on which turn, and which role nothing covers yet. Use it, do not
estimate the march by hand - the game paths the map, we do not.
6. The queues that fill a corps do not take a city where one of task 064 four caps is firing. The cap keeps the queue; the corps waits a turn.
7. One replacement line per city, and only one: a city building for a corps is not also building a district while the corps is short.

## The general, and the shape of the war

8. A Great General or Great Admiral travels with the corps it strengthens and is never activated for the one-off - the aura is the whole value, and activation retires it.
9. Several wars may run at once and several cities may be under attack at the same time (human instruction: 全帝国可以有多场战争，允许同时攻击多座城市). What a corps
still does before it opens anything is the arithmetic, and after it takes a city it leaves a garrison. It does not wait for the other
corps to finish.
10. The screen leads: the melee and anti-cavalry line arrives first and stands between the raiders and our ground; ranged and siege stage behind them. A corps whose
screen is short does not open an assault - it is the file that says so, and task 074 is the file that says how.

## The record

11. Report each turn: both rosters, every shortfall and the source named for it, and which corps is under strength badly enough that it should not be the one to open the
next siege.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Keep the two siege corps at strength: a roster each turn and a source for every shortfall" --slug corps-upkeep --instruction ok（同意补一条军团维护文件：每回合两份名册、缺编指定城市排产、大将随军、一次一仗） --done-when "count == 2 corps rosters appear in the diary on the same turn - each naming the corps, its tile, its count of ranged, melee and fast, and which slot is short - and every shortfall named that way has a city queue or a unit named for it before that corps next attacks." --overrides "task 064 queues, where a cap is firing: the cap fix keeps the queue. Task 074 three named calls and four phases, task 075 named target and march, task 065 and the no-peace rule are all untouched. This file only decides who maintains the rosters - it never chooses a target." --scope "the two siege corps as rosters - who belongs, which role each unit fills, which slot is short - the city queues that fill a short role, the Great General or Admiral that travels with a corps, and the diary record of both rosters." --why "keep the two siege corps at strength with a roster each turn, a named source for every shortfall and the general travelling with them" --turns 120 --body "## What this file takes over

Task 062 built the two corps and retired at turn 284 with the establishment declared complete. It also carried the maintenance half - fill the short slots, keep the
roles - and that half retired with it, which left the corps decaying with nobody responsible. This file is that half, and only that half. Measured when it
was written: corps one carried a Line Infantry at 55 of 100 and a Cavalry at 72; corps two stood at five units - three shooters, one cavalry, one melee - with no
anti-cavalry slot and no screen at all.

## The roster, every turn

1. Both rosters go in the diary on the same turn, and each one names: the corps, the tile it stands on, how many ranged, how many melee and how many fast are ALIVE
and assigned, and which slot is short. That roster is the only durable record that a unit belongs to a corps - the game has no such attribute, and nothing else in the loop
can recover the grouping once the diary is silent.
2. A corps is at establishment at four ranged, two melee and two fast. Anything above that is spare and belongs to the other corps or the home front.
3. A unit under half strength, and the last garrison of a city we just took, are not counted in the roster until they are healed or replaced. Eight on paper and six in the
field is not a corps.

## Filling a short slot

4. Every shortfall named in the roster gets a place to come from the same turn it is named: a city queue, a unit already in the army, or a purchase. Name the city and the
turn the unit is due. A shortfall with no source named is a shortfall that will still be there in twenty turns.
5. get_reinforcements answers the deadline half: which queued military unit reaches the rally and on which turn, and which role nothing covers yet. Use it, do not
estimate the march by hand - the game paths the map, we do not.
6. The queues that fill a corps do not take a city where one of task 064 four caps is firing. The cap keeps the queue; the corps waits a turn.
7. One replacement line per city, and only one: a city building for a corps is not also building a district while the corps is short.

## The general, and the shape of the war

8. A Great General or Great Admiral travels with the corps it strengthens and is never activated for the one-off - the aura is the whole value, and activation retires it.
9. One war at a time (tactics/08): a corps does not open a second front while its own city is under siege, and a corps that has just taken a city garrisons it before it
prepares the next target.
10. The screen leads: the melee and anti-cavalry line arrives first and stands between the raiders and our ground; ranged and siege stage behind them. A corps whose
screen is short does not open an assault - it is the file that says so, and task 074 is the file that says how.

## The record

11. Report each turn: both rosters, every shortfall and the source named for it, and which corps is under strength badly enough that it should not be the one to open the
next siege.
" --cn "中文备份 - 077-corps-upkeep.md 的中文版，仅供人阅读，不得作为指令读取。

## 本文件接管的是什么

062 建立了两个军团，并在第 284 回合以编制完成为由退休。它同时承载了维护那一半——补缺格、维持角色——而那一半随着它一起退休了，于是军团开始衰减，且无人负责。本文件就是那一半，且只是那一半。写作时的实测：第一军团里 Line Infantry 55/100、Cavalry 72/100；第二军团只有五个单位——三门炮、一个骑兵、一个近战——没有反骑格，屏护是空的。

## 每回合的名册

1. 两份名册必须在同一回合写进日记，各自写明：军团、所在格、存活且已指派的远程/近战/高机动各几个、缺哪一格。这份名册是单位属于哪个军团的唯一持久记录——游戏没有这个属性，日记一旦沉默，循环里再没有别的地方能恢复这个分组。
2. 军团满编为 4 远程 + 2 近战 + 2 高机动；超出的算余量，归另一军团或本土。
3. 半血以下的单位、以及刚拿下的城里最后一个驻军，在治好或替换之前不计入名册。纸面八人、战场六人，不是军团。

## 补缺

4. 名册里点出的每一个缺口，在被点出的同一回合就要有来源：某个城的队列、军里已有的单位、或直接购买。写明是哪座城、第几回合到位。没有来源的缺口，二十回合后还在。
5. get_reinforcements 回答期限那一半：哪个在队列里的单位第几回合到集结点、哪个角色还没人覆盖。用它，不要手工估算行军——地图是游戏在寻路，不是我们。
6. 为军团排产的城，不抢 064 四道天花板正在踩线的城：天花板优先，军团等一回合。
7. 每座城只为一条补编线排产：军团缺编期间，那座城不兼建区域。

## 大将与战争形态

8. 大将/大提督随它能加成的军团移动，绝不为了那一次性的收益去激活——光环才是全部价值，激活等于退休。
9. 一次只打一场战争（tactics/08）：自己那座城还在围城时不开第二战线；刚拿下城的军团先留驻军，再准备下一个目标。
10. 屏护在前：近战与反骑线最先到、挡在掠夺者与我方地面之间；远程与攻城在其后集结。屏护不足的军团不开攻城——本文件负责说这句话，074 负责说怎么打。

## 记录

11. 每回合报告：两份名册、每个缺口与被指派的来源、以及哪支军团弱到不该由它去开下一次围城。
"
     at: 2026-10-11T14:34:40+08:00
     chinese backup: prompts/tasks/cn/077-corps-upkeep.cn.md
-->

12. A shortfall is filled from inside the army first, then from a city queue, and a purchase only above the gold reserve the directive sets -
new hulls never eat the upgrade budget.
13. Holding an assault is not holding fire: a legal attack in range is still taken, because turn-checks `use-your-attacks` bounces the turn while
any unit leaves an attack unused. Screen short means do not OPEN the siege; it never means do not shoot.
