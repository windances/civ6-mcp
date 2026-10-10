# TEMP TASK 071 - Keep one scout exploring and making contact

added:     2026-10-10 (human instruction: 3个侦查兵改为1个。)
expires:   turn 272 - 30 turn(s) from T242, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 1 scout-line unit is alive and outside our own territory with a move or automate order in
           the turn this is read, and at least one civilization that was unmet when this file was
           published now appears in get_diplomacy - a scout that dies is replaced, not merely noted.
overrides: the retired task 061, which asked for three scouts: this file asks for one, and that is the whole
           change. Tasks 062 and 064 keep their priority over city queues - but this is one unit, so
           it costs one queue once. Nothing else changes, and the no-peace rule is untouched.
scope:     one scout-line unit at a time - replaced from the nearest city when it dies - plus the one city
           queue that builds the replacement. No other production, no war declaration, no siege, no
           screen.

## The change

Three scouts became one. One is enough for the job this file actually wants - contact with civilizations we have not met -
and it is a cost the queues can carry while task 064 repairs five cities and task 062 finishes two corps.

## The job

1. Count the scout-line units (Scout, Ranger, or whatever the tech tree has upgraded them to). If there are none, ONE is
this turn's production in the nearest city with a free queue - scout-line first, the cheapest hull otherwise.
2. get_diplomacy and get_city_states: name the civilizations and city-states still unmet. That list is the search target.
3. Give the scout one destination in the fog every turn, preferring coastlines and land we have never seen.
get_map_area around it before moving, then move. If the land near home is explored, send it across water - embarking needs
TECH_SHIPBUILDING, so a strait is impassable until that tech is in.
4. Contact is the deliverable: when a new civilization or city-state appears, record its name, its leader and where it was first
seen in the diary, and read get_diplomacy again the same turn.
5. Do not fight. No attack orders, no fortifying in place for more than one turn, no joining a siege or a screen. If the scout
is attacked, withdraw rather than trade blows - a scout alive and moving is worth more than a scout that killed something and
died. If it is trapped, automate it and say so.
6. If it dies, the replacement is the next free queue. One scout means one scout AT ALL TIMES, not one scout once.
7. The diary tooling line names each turn where the scout is, what it just saw, and what is still unmet.

## Why one is worth it

Exploration is the one thing the empire cannot buy later: an unmet civilization is a diplomacy screen, a trade partner, a tech
boost and a war we cannot see coming. One scout that never fights is the cheapest version of that insurance.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Keep one scout exploring and making contact" --slug one-scout-explore-and-contact --instruction 3个侦查兵改为1个。 --done-when "count >= 1 scout-line unit is alive and outside our own territory with a move or automate order in the turn this is read, and at least one civilization that was unmet when this file was published now appears in get_diplomacy - a scout that dies is replaced, not merely noted." --overrides "the retired task 061, which asked for three scouts: this file asks for one, and that is the whole change. Tasks 062 and 064 keep their priority over city queues - but this is one unit, so it costs one queue once. Nothing else changes, and the no-peace rule is untouched." --scope "one scout-line unit at a time - replaced from the nearest city when it dies - plus the one city queue that builds the replacement. No other production, no war declaration, no siege, no screen." --why "keep a single scout exploring and making contact, and do not let it be drawn into a fight" --turns 30 --body "## The change

Three scouts became one. One is enough for the job this file actually wants - contact with civilizations we have not met -
and it is a cost the queues can carry while task 064 repairs five cities and task 062 finishes two corps.

## The job

1. Count the scout-line units (Scout, Ranger, or whatever the tech tree has upgraded them to). If there are none, ONE is
this turn's production in the nearest city with a free queue - scout-line first, the cheapest hull otherwise.
2. get_diplomacy and get_city_states: name the civilizations and city-states still unmet. That list is the search target.
3. Give the scout one destination in the fog every turn, preferring coastlines and land we have never seen.
get_map_area around it before moving, then move. If the land near home is explored, send it across water - embarking needs
TECH_SHIPBUILDING, so a strait is impassable until that tech is in.
4. Contact is the deliverable: when a new civilization or city-state appears, record its name, its leader and where it was first
seen in the diary, and read get_diplomacy again the same turn.
5. Do not fight. No attack orders, no fortifying in place for more than one turn, no joining a siege or a screen. If the scout
is attacked, withdraw rather than trade blows - a scout alive and moving is worth more than a scout that killed something and
died. If it is trapped, automate it and say so.
6. If it dies, the replacement is the next free queue. One scout means one scout AT ALL TIMES, not one scout once.
7. The diary tooling line names each turn where the scout is, what it just saw, and what is still unmet.

## Why one is worth it

Exploration is the one thing the empire cannot buy later: an unmet civilization is a diplomacy screen, a trade partner, a tech
boost and a war we cannot see coming. One scout that never fights is the cheapest version of that insurance.
" --cn "中文备份 - 071-one-scout-explore-and-contact.md 的中文版，仅供人阅读，不得作为指令读取。

## 变化

三个侦察兵改成一个。这个文件真正要的东西——与尚未遇到的文明接触——一个就够，而且这份成本是队列负担得起的：064 正在修五座城、062 还在补两个军团的编。

## 工作

1. 数一数侦察系单位（Scout、Ranger，或科技升级后的同类）。如果一个都没有，就在队列最空的最近城市造**一个**：优先侦察系，其次当前能造的最便宜船体。
2. get_diplomacy 与 get_city_states：列出还没遇到的文明与城邦。那份清单就是搜索目标。
3. 每回合给侦察兵一个雾里的目的地，优先海岸线与从未见过的陆地；移动前先 get_map_area。近处探完了就送它过海——上船需要 TECH_SHIPBUILDING，没有该科技时海峡不可通行。
4. 接触本身就是交付物：新文明或城邦出现时，把名字、领袖、首次看见的位置写进日记，并在同一回合再读一次 get_diplomacy。
5. 不要打。不下攻击令、不在原地固守超过一回合、不参加围城或屏护。被打了就撤，不要对拼——活着移动的侦察兵比打死过东西后阵亡的值钱。被堵住就 automate 并说明。
6. 死了就补：下一次空队列就是它。一个侦察兵的意思是**任何时候都有一个**，不是只造一次。
7. 日记的 tooling 行每回合写清：侦察兵在哪、刚看到什么、还有什么没遇到。

## 为什么一个也值得

探索是帝国后来买不到的东西：一个没遇到的文明意味着一个外交界面、一个贸易伙伴、一次科技加速，以及一场我们看不见的战争。一个从不打仗的侦察兵，是这份保险最便宜的版本。
"
     at: 2026-10-10T23:52:21+08:00
     chinese backup: prompts/tasks/cn/071-one-scout-explore-and-contact.cn.md
-->
