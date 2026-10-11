# TEMP TASK 072 - Count the taking unit attack in the siege arithmetic

added:     2026-10-11 (human instruction: 占城部队也有一定攻击力，也要考虑在内)
expires:   turn 285 - 40 turn(s) from T245, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 1 siege plan in the diary carries the taking unit attack in its per-turn pool arithmetic
           and names which of the two options was chosen - spending that attack to end the pool a
           turn sooner, or holding the unit adjacent with its movement unspent for the walk-in turn.
overrides: nothing. This adds a term to the arithmetic and a sequencing choice; it changes no target, no
           priority and no rule. Tasks 062 067 069 070 and the no-peace rule are untouched.
scope:     the siege arithmetic and the sequencing of the walk-in, for this assault and every later one: the
           taking unit attack counts as pool damage, and the take itself is a move that needs
           movement left.

The full rule is the new section in prompts/tactics/06-assault-composition-and-fire.md, added on the human instruction.

In one line: the melee unit that takes the city also hits it, and its attack damages the CITY CENTRE pool - the one the guns
are breaking - not the walls. So the per-turn arithmetic is the shooters PLUS that attack when it is spent.

And the consequence that matters: the walk-in is a MOVE. A melee unit that attacked this turn cannot enter the city this turn,
so the plan chooses explicitly between spending the attack to end the pool sooner and holding the unit adjacent, unspent, for
the turn the pool reaches zero - and says in the diary which it chose.

Never let the pool reach zero with no melee unit adjacent and holding movement: the city heals about twenty points a turn while
somebody walks over. Read both pools before every volley - get_target_report or get_map_area prints the walls and the centre
pool, and SIEGE PROGRESS and TAKE THE CITY in the end_turn result are the confirmation.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Count the taking unit attack in the siege arithmetic" --slug count-the-taking-unit-attack --instruction 占城部队也有一定攻击力，也要考虑在内 --done-when "count >= 1 siege plan in the diary carries the taking unit attack in its per-turn pool arithmetic and names which of the two options was chosen - spending that attack to end the pool a turn sooner, or holding the unit adjacent with its movement unspent for the walk-in turn." --overrides "nothing. This adds a term to the arithmetic and a sequencing choice; it changes no target, no priority and no rule. Tasks 062 067 069 070 and the no-peace rule are untouched." --scope "the siege arithmetic and the sequencing of the walk-in, for this assault and every later one: the taking unit attack counts as pool damage, and the take itself is a move that needs movement left." --why "count the taking unit attack as pool damage, and choose explicitly between spending it and holding it for the walk-in" --turns 40 --body "The full rule is the new section in prompts/tactics/06-assault-composition-and-fire.md, added on the human instruction.

In one line: the melee unit that takes the city also hits it, and its attack damages the CITY CENTRE pool - the one the guns
are breaking - not the walls. So the per-turn arithmetic is the shooters PLUS that attack when it is spent.

And the consequence that matters: the walk-in is a MOVE. A melee unit that attacked this turn cannot enter the city this turn,
so the plan chooses explicitly between spending the attack to end the pool sooner and holding the unit adjacent, unspent, for
the turn the pool reaches zero - and says in the diary which it chose.

Never let the pool reach zero with no melee unit adjacent and holding movement: the city heals about twenty points a turn while
somebody walks over. Read both pools before every volley - get_target_report or get_map_area prints the walls and the centre
pool, and SIEGE PROGRESS and TAKE THE CITY in the end_turn result are the confirmation.
" --cn "中文备份 - 073-count-the-taking-unit-attack.md 的中文版，仅供人阅读，不得作为指令读取。

完整规则已按人类指令写进 prompts/tactics/06-assault-composition-and-fire.md 的新增小节。

一句话：占城的近战单位本身也打城，它打的是**城市中心池**（不是城墙），所以每回合的池伤害＝各射手之和 ＋ 它开火时的那一击。

最要紧的推论：**走进城是一次移动**。本回合攻击过的近战单位，本回合不能进城；因此计划要有意识地二选一——把这一击花掉、让池早一回合归零，还是让部队贴着城、把移动力留着，等池归零的那一回合进城——并在日记里写明选了哪个。

绝不让池归零时身边没有带移动力的近战单位：那等于让炮去打一座每回合回血约二十点的城，而有人在旁边走路。每轮齐射前读两条血条：get_target_report 或 get_map_area 同时打印城墙与中心池，end_turn 的 SIEGE PROGRESS 与 TAKE THE CITY 是确认。
"
     at: 2026-10-11T00:02:57+08:00
     chinese backup: prompts/tasks/cn/072-count-the-taking-unit-attack.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 072 --expired --turn 287 --note "two turns past its hard stop: the taking unit arithmetic was folded into task 074 own text"
     at: 2026-10-11T12:19:28+08:00
     status: expired at T287
     chinese backup: prompts/tasks/cn/072-count-the-taking-unit-attack.cn.md
-->
