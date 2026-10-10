# TEMP TASK 064 - Raise the cap on every city before building inside it

added:     2026-10-10 (human instruction: 优先解决影响生产力的因数，保持城市健康发展。)
expires:   turn 264 - 45 turn(s) from T219, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 cities where housing minus pop is <= 1, count == 0 cities with food_surplus <= 0, count
           == 0 cities with amenities below 3, and count == 0 pillaged districts or buildings - all
           four holding in the same read, on a turn after the T219 list of them is empty.
overrides: task 062's shortfall queues and task 063's queues, in the cities where one of the four caps is
           firing: a city that cannot grow pays for the unit with production it does not have, so
           the housing, food, amenity or repair build goes first. Task 061's production restriction
           stays in force, and the no-peace rule is untouched.
scope:     the four caps and the queues that lift them - a Granary, Water Mill, Aqueduct, Neighbourhood, farm,
           or a domestic trade route, plus the Builder charges those need - in any city where
           housing minus pop is <= 1, food_surplus <= 0, amenities are low, or a district or
           building is pillaged. Also the gold spent on Builders and tiles for the same reason.

## What this asks for

Raise the ceiling each city is under before building anything new inside it. Productivity here is not a
choice - it is capped by four things, and every one of them is measurable:

1. housing minus pop
2. food surplus
3. amenities
4. a pillaged district or building

## The list, measured at T219

Read it fresh every turn and never carry it forward. At T219 the cap was firing in five cities: Beijing at housing
minus pop of -1, and Xi'an, Shanghai, Changsha and Jiaodong at 0. Kazan sat at 1 amenity and five more cities at
2. Four cities were growing slower than 30 turns (Shanghai 78, Changsha 55, Yerevan 37, Jiaodong 30). One building
was pillaged (a Water Mill).

## Steps

1. Run the read that ranks this: .tools/production-audit.py prints, per city, the production it is losing right
now, its queue, its pillaged list, its power demand and whether that power is durable or only a project,
housing against pop, and its free district slots. get_cities carries the same fields.
2. Work the list in order of what it costs the empire: a pillaged Industrial Zone, Workshop, Factory or Power
Plant first, because a power shortage is a production penalty across every city, not one city's problem. Then
housing, then food, then amenities.
3. Growth is not a preference, it is the district plan: specialty districts are gated by
districts <= floor(pop / 3), so a stalled city is a district slot nobody can use. A city with housing minus pop
<= 1 or food_surplus <= 0 gets a Granary, a Water Mill, an Aqueduct, a farm or a domestic trade route this turn.
4. Never leave a compounding city's queue empty. An empty queue costs a turn of compounding in the city whose
whole value is compounding.
5. Gold above roughly 300 with unimproved tiles in any city is a Builder, not savings. Buy the Builder.
6. Do not add units to fix this: at T219 maintenance was 119.0 against an income of 134.6, i.e. 88 percent,
where the directive's army budget is under about 30 percent. A bigger army is a smaller production.
7. Keep an unbroken record: the diary's tooling line names which caps were firing this turn, what was queued
against them, and the turn each fix lands.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Raise the cap on every city before building inside it" --slug fix-what-caps-production --instruction 优先解决影响生产力的因数，保持城市健康发展。 --done-when "count == 0 cities where housing minus pop is <= 1, count == 0 cities with food_surplus <= 0, count == 0 cities with amenities below 3, and count == 0 pillaged districts or buildings - all four holding in the same read, on a turn after the T219 list of them is empty." --overrides "task 062's shortfall queues and task 063's queues, in the cities where one of the four caps is firing: a city that cannot grow pays for the unit with production it does not have, so the housing, food, amenity or repair build goes first. Task 061's production restriction stays in force, and the no-peace rule is untouched." --scope "the four caps and the queues that lift them - a Granary, Water Mill, Aqueduct, Neighbourhood, farm, or a domestic trade route, plus the Builder charges those need - in any city where housing minus pop is <= 1, food_surplus <= 0, amenities are low, or a district or building is pillaged. Also the gold spent on Builders and tiles for the same reason." --why "fix what caps a city's productivity - housing, food, amenities and pillaged ground - before anything new is built" --turns 45 --body "## What this asks for

Raise the ceiling each city is under before building anything new inside it. Productivity here is not a
choice - it is capped by four things, and every one of them is measurable:

1. housing minus pop
2. food surplus
3. amenities
4. a pillaged district or building

## The list, measured at T219

Read it fresh every turn and never carry it forward. At T219 the cap was firing in five cities: Beijing at housing
minus pop of -1, and Xi'an, Shanghai, Changsha and Jiaodong at 0. Kazan sat at 1 amenity and five more cities at
2. Four cities were growing slower than 30 turns (Shanghai 78, Changsha 55, Yerevan 37, Jiaodong 30). One building
was pillaged (a Water Mill).

## Steps

1. Run the read that ranks this: .tools/production-audit.py prints, per city, the production it is losing right
now, its queue, its pillaged list, its power demand and whether that power is durable or only a project,
housing against pop, and its free district slots. get_cities carries the same fields.
2. Work the list in order of what it costs the empire: a pillaged Industrial Zone, Workshop, Factory or Power
Plant first, because a power shortage is a production penalty across every city, not one city's problem. Then
housing, then food, then amenities.
3. Growth is not a preference, it is the district plan: specialty districts are gated by
districts <= floor(pop / 3), so a stalled city is a district slot nobody can use. A city with housing minus pop
<= 1 or food_surplus <= 0 gets a Granary, a Water Mill, an Aqueduct, a farm or a domestic trade route this turn.
4. Never leave a compounding city's queue empty. An empty queue costs a turn of compounding in the city whose
whole value is compounding.
5. Gold above roughly 300 with unimproved tiles in any city is a Builder, not savings. Buy the Builder.
6. Do not add units to fix this: at T219 maintenance was 119.0 against an income of 134.6, i.e. 88 percent,
where the directive's army budget is under about 30 percent. A bigger army is a smaller production.
7. Keep an unbroken record: the diary's tooling line names which caps were firing this turn, what was queued
against them, and the turn each fix lands.
" --cn "中文备份 - 064-fix-what-caps-production.md 的中文版，仅供人阅读，不得作为指令读取。

在每座城市里，先把压着它的天花板抬高，再谈新建。产能不是选出来的，是被四件事卡住的，而四件都可测量：
1. 住房减人口；2. 粮食盈余；3. 宜居度；4. 被掠夺的区域或建筑。

## T219 实测的清单（每回合重新读，绝不沿用）

五座城踩线：Beijing 住房减人口 ＝ -1；Xi'an、Shanghai、Changsha、Jiaodong ＝ 0。Kazan 宜居仅 1，另五座城宜居 2。
四座城成长慢于 30 回合（Shanghai 78、Changsha 55、Yerevan 37、Jiaodong 30）。一处建筑被掠夺（水磨）。

## 步骤

1. 用 .tools/production-audit.py 排名：逐城打印此刻正在损失的产能、队列、被掠夺清单、电力需求及是否持久、住房对人口、空闲区域槽；get_cities 给同样的字段。
2. 按对帝国的代价排序：先修被掠夺的工业区／车间／工厂／发电厂（电力短缺是全帝国的产能惩罚），再住房、再粮食、再宜居。
3. 成长不是偏好，而是区域计划：专业区域受 districts <= floor(pop/3) 门控，停滞的城市＝没人用得上的区域槽。住房减人口 <= 1 或粮食盈余 <= 0 的城，本回合就上粮仓／水磨／水渠／农场／国内商路。
4. 绝不让复利中的城市队列空着——空一回合就是少一回合复利。
5. 金超过约 300 而还有未开发地块，就买建造者，不要存着。
6. 不许靠加兵来解决：T219 维护费 119.0 对收入 134.6 ＝ 88%，而 directive 的军队预算是不超过约 30%。军队越大，产能越小。
7. 每回合的 tooling 行写清：这回合哪几项踩线、针对它们排了什么、修复在第几回合落地。
"
     at: 2026-10-10T21:48:53+08:00
     chinese backup: prompts/tasks/cn/064-fix-what-caps-production.cn.md
-->
