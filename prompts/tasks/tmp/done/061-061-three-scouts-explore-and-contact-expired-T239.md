# TEMP TASK 061 - Keep three scouts exploring the map and making contact

added:     2026-10-10 (human instruction: 保持3个侦查兵探索地图，发现更多文明，不恋战，探索为主。)
expires:   turn 249 - 30 turn(s) from T219, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 3 scout-line units are alive and outside our own territory with a move or automate order in
           the turn this is read, and at least one civilization that was unmet when this file was
           published now appears in get_diplomacy (a scout that dies is replaced, not merely noted).
overrides: the standing conquest directive, for the scout-line units only: they do not join a fight, do not
           besiege, and are not recalled for one. Nothing else in force is changed, and the
           directive's no-peace rule is untouched.
scope:     the empire's scout-line units - up to three at any time, replaced from the nearest city whenever one
           dies - plus the one city queue that builds a replacement. No new military production, no
           war declaration, no other city queue.

## What this asks for

Three scouts on the map at all times, looking for civilizations we have not met, and a hard rule
against being drawn into a fight.

## Steps

1. `get_units`: count the scout-line units (Scout, Ranger, and whatever the tech tree has upgraded
   them to). Fewer than three alive means a replacement is this turn's production - the nearest
   city with a queue free, scout-line first, the fastest available hull otherwise. Three is the floor
   for the whole life of this task, not just for one turn.
2. `get_diplomacy` and `get_city_states`: name the civilizations and city-states still unmet. That
   list is the search target, and it is what makes a destination worth choosing.
3. Every turn, give each scout one destination in the fog, preferring coastlines and land we have
   never seen: `get_map_area` on the tiles around it, then move. A scout that has run out of
   unexplored ground near home is the one to send across water - embarking needs
   `TECH_SHIPBUILDING`, so a strait is impassable until that tech is in.
4. Contact is the deliverable: when a new civilization or city-state appears, record its name, its
   leader and where it was first seen in the diary, and read `get_diplomacy` again the same turn.
5. Do not fight. No attack orders, no fortifying in place for more than one turn, no joining a siege
   or a screen. If a scout is attacked, withdraw rather than trade blows; a scout is worth more
   alive and moving than dead and having killed something. If one is trapped, `automate` it and say
   so rather than walking it into a stack.
6. Nine tiles of water and an unmet civilization are the two cases worth the diary's `tooling` line:
   say each turn how many scouts are alive, where the newest contact was, and what is still unmet.

## Why it is worth a standing instruction

Exploration is the one thing the empire cannot buy later: an unmet civilization is a diplomacy
screen, a trade partner, a tech boost and a war we cannot see coming. Keeping three scouts moving
and refusing every fight is cheaper than replacing them one at a time.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Keep three scouts exploring the map and making contact" --slug 061-three-scouts-explore-and-contact --instruction 保持3个侦查兵探索地图，发现更多文明，不恋战，探索为主。 --done-when "count >= 3 scout-line units are alive and outside our own territory with a move or automate order in the turn this is read, and at least one civilization that was unmet when this file was published now appears in get_diplomacy (a scout that dies is replaced, not merely noted)." --overrides "the standing conquest directive, for the scout-line units only: they do not join a fight, do not besiege, and are not recalled for one. Nothing else in force is changed, and the directive's no-peace rule is untouched." --scope "the empire's scout-line units - up to three at any time, replaced from the nearest city whenever one dies - plus the one city queue that builds a replacement. No new military production, no war declaration, no other city queue." --why "keep three scouts exploring and making contact, and do not let them be drawn into a fight" --turns 30 --body "## What this asks for

Three scouts on the map at all times, looking for civilizations we have not met, and a hard rule
against being drawn into a fight.

## Steps

1. `get_units`: count the scout-line units (Scout, Ranger, and whatever the tech tree has upgraded
   them to). Fewer than three alive means a replacement is this turn's production - the nearest
   city with a queue free, scout-line first, the fastest available hull otherwise. Three is the floor
   for the whole life of this task, not just for one turn.
2. `get_diplomacy` and `get_city_states`: name the civilizations and city-states still unmet. That
   list is the search target, and it is what makes a destination worth choosing.
3. Every turn, give each scout one destination in the fog, preferring coastlines and land we have
   never seen: `get_map_area` on the tiles around it, then move. A scout that has run out of
   unexplored ground near home is the one to send across water - embarking needs
   `TECH_SHIPBUILDING`, so a strait is impassable until that tech is in.
4. Contact is the deliverable: when a new civilization or city-state appears, record its name, its
   leader and where it was first seen in the diary, and read `get_diplomacy` again the same turn.
5. Do not fight. No attack orders, no fortifying in place for more than one turn, no joining a siege
   or a screen. If a scout is attacked, withdraw rather than trade blows; a scout is worth more
   alive and moving than dead and having killed something. If one is trapped, `automate` it and say
   so rather than walking it into a stack.
6. Nine tiles of water and an unmet civilization are the two cases worth the diary's `tooling` line:
   say each turn how many scouts are alive, where the newest contact was, and what is still unmet.

## Why it is worth a standing instruction

Exploration is the one thing the empire cannot buy later: an unmet civilization is a diplomacy
screen, a trade partner, a tech boost and a war we cannot see coming. Keeping three scouts moving
and refusing every fight is cheaper than replacing them one at a time." --cn "中文备份 - 061-three-scouts-explore-and-contact.md 的中文版，仅供人阅读，不得作为指令读取。

## 这个任务要什么

地图上**始终保持三个侦查兵**，去找我们还没遇到的文明，并且**硬性禁止被拖进战斗**。

## 步骤

1. `get_units`：数一数侦察系单位（Scout、Ranger，以及科技升级后的同类）。**活着的少于三个**，就
   把补充生产当作本回合的生产任务——找最近一个队列空着的城市，优先侦察系，其次当前能造的**最快船体**。
   **三个是底线，不是某一回合的要求。**
2. `get_diplomacy` 与 `get_city_states`：列出**还没遇到的文明与城邦**。那份清单就是搜索目标，也是
   判断往哪走值得的依据。
3. 每回合给每个侦察兵**一个雾里的目的地**，优先海岸线与从未见过的陆地：先 `get_map_area` 看周围，
   再移动。近处已探完的侦察兵，就是该**过海**的那个——上船需要 `TECH_SHIPBUILDING`，没有这条科技时
   海峡是不可通行的。
4. **接触本身就是交付物**：新文明或城邦一出现，就把它的名字、领袖、以及首次看见的位置写进日记，
   并在同一回合再读一次 `get_diplomacy`。
5. **不要打**。不下攻击令，不在原地固守超过一回合，不参加围城或屏护。被打了就**撤**，不要对拼——
   活着的侦察兵比打死过东西的侦察兵值钱。被堵住了就 `automate` 并说明，而不是把它推进人堆。
6. 日记的 `tooling` 行里，每回合说清三件事：**几个侦察兵还活着**、**最新接触在哪**、**还有什么没遇到**。

## 为什么值得作为常设指令

探索是帝国**后来买不到**的东西：一个没遇到的文明，意味着一个外交界面、一个贸易伙伴、一次科技加速，
以及一场**我们看不见的战争**。让三个侦察兵一直走、并且拒绝每一场战斗，比一次次重新造它们便宜。"
     at: 2026-10-10T13:29:22+08:00
     chinese backup: prompts/tasks/cn/061-061-three-scouts-explore-and-contact.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 061 --expired --turn 239 --note "replaced by 071: one scout instead of three, on the human instruction"
     at: 2026-10-10T23:44:43+08:00
     status: expired at T239
     chinese backup: prompts/tasks/cn/061-061-three-scouts-explore-and-contact.cn.md
-->
