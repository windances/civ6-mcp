# TEMP TASK 064 - Raise the cap on every city before building inside it

added:     2026-10-11 (human instruction: 优先解决影响生产力的因数，保持城市健康发展。)
expires:   turn 340 - a hard stop, retired either way on that turn. Extended from turn 300 on turn 291,
           because the four caps are standing work on a nineteen-city empire and not a window: the
           same revision measures progress from the turn it was published, so the finish line does
           not move.
done when: count == 0 cities newly added to any of the four cap lists for five consecutive turns, while each of
           the four lists - housing minus pop <= 1, food surplus <= 0, amenities below 3, pillaged
           districts or buildings - is strictly shorter than on the turn this revision was
           published.
overrides: task 062 and task 063 queues, in any city where one of the four caps is firing: the cap fix goes
           first there. Task 071 and the no-peace rule are untouched.
scope:     the four caps and the queues that lift them - Granary, Water Mill, Aqueduct, Neighbourhood, Sewer,
           farm, or a domestic trade route - plus the Builder charges and the repairs those need, in
           any city where a cap is firing.

## Revision, on the human confirmation

The original finish line asked for all four lists empty by T264. Re-read at T258, that is not reachable: the empire is at war on two
axes and five cities were still at the housing cap when the file was written. So the finish line is now progress measured against
this turn, with a five-turn no-new-entries guard - and the hard stop moves out to T298.

The work itself is unchanged. The four caps are still the four caps:

1. housing minus pop <= 1
2. food surplus <= 0
3. amenities below 3
4. a pillaged district or building

## What to do, in order

5. Run .tools/production-audit.py or get_cities and write the four lists out, with the city names, before choosing any production.
6. Repair a pillaged Industrial Zone, Workshop, Factory or Power Plant first: the power shortage is a production penalty across the
whole empire, not one city's problem.
7. Then the housing cities: Sewer, Granary, Water Mill, Aqueduct, Neighbourhood, or a domestic trade route. Housing is the cap that
stalls growth for dozens of turns, and growth is the district plan - districts <= floor(pop / 3) - so a stalled city is a district slot
nobody can use.
8. Then food, then amenities.
9. Never leave a compounding city's queue empty, and keep the short slots of tasks 062 and 071 in their queues where no cap is firing.
10. Record in the diary each turn: the four counts, what was queued against them, and the turn each fix lands. The five-turn guard is
what this revision is measured by, so the record is the evidence.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --replace --title "Raise the cap on every city before building inside it" --slug fix-what-caps-production --instruction 优先解决影响生产力的因数，保持城市健康发展。 --done-when "count == 0 cities newly added to any of the four cap lists for five consecutive turns, while each of the four lists - housing minus pop <= 1, food surplus <= 0, amenities below 3, pillaged districts or buildings - is strictly shorter than on the turn this revision was published." --overrides "task 062 and task 063 queues, in any city where one of the four caps is firing: the cap fix goes first there. Task 071 and the no-peace rule are untouched." --scope "the four caps and the queues that lift them - Granary, Water Mill, Aqueduct, Neighbourhood, Sewer, farm, or a domestic trade route - plus the Builder charges and the repairs those need, in any city where a cap is firing." --why "fix what caps a city productivity - housing, food, amenities and pillaged ground - and measure progress against the turn this revision was published" --turns 40 --body "## Revision, on the human confirmation

The original finish line asked for all four lists empty by T264. Re-read at T258, that is not reachable: the empire is at war on two
axes and five cities were still at the housing cap when the file was written. So the finish line is now progress measured against
this turn, with a five-turn no-new-entries guard - and the hard stop moves out to T298.

The work itself is unchanged. The four caps are still the four caps:

1. housing minus pop <= 1
2. food surplus <= 0
3. amenities below 3
4. a pillaged district or building

## What to do, in order

5. Run .tools/production-audit.py or get_cities and write the four lists out, with the city names, before choosing any production.
6. Repair a pillaged Industrial Zone, Workshop, Factory or Power Plant first: the power shortage is a production penalty across the
whole empire, not one city's problem.
7. Then the housing cities: Sewer, Granary, Water Mill, Aqueduct, Neighbourhood, or a domestic trade route. Housing is the cap that
stalls growth for dozens of turns, and growth is the district plan - districts <= floor(pop / 3) - so a stalled city is a district slot
nobody can use.
8. Then food, then amenities.
9. Never leave a compounding city's queue empty, and keep the short slots of tasks 062 and 071 in their queues where no cap is firing.
10. Record in the diary each turn: the four counts, what was queued against them, and the turn each fix lands. The five-turn guard is
what this revision is measured by, so the record is the evidence.
" --cn "中文备份 - 064-fix-what-caps-production.md 的中文版，仅供人阅读，不得作为指令读取。

按人类确认修订：原完成线要求 T264 之前四道清单全空，T258 复读时确认不可达（两条战线在打，且文件写成时仍有五座城卡在住房上限）。
新完成线改为按本回合起算的进展 ＋ 连续五回合无新增，硬停点延到 T298。工作内容不变，四道天花板仍是：
1. 住房减人口 <= 1；2. 粮食盈余 <= 0；3. 宜居低于 3；4. 被掠夺的区域或建筑。

顺序：先跑 production-audit.py 或 get_cities 把四张清单连城名写出来 → 先修被掠夺的工业区／车间／工厂／发电厂（电力短缺是全帝国的产能惩罚）→ 再住房（下水道、粮仓、水磨、水渠、社区、国内商路）→ 再粮食 → 再宜居。
复利中的城市队列不许空着；没有踩线的城市里，062 与 071 的缺编队列继续留着。
每回合日记写清：四个计数、针对它们排了什么、修复在第几回合落地——五回合守卫就是这次的验收依据，记录就是证据。
"
     at: 2026-10-11T00:46:11+08:00
     chinese backup: prompts/tasks/cn/064-fix-what-caps-production.cn.md
-->
