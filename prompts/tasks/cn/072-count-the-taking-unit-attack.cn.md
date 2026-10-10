> 本文件是 `072-count-the-taking-unit-attack.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

中文备份 - 073-count-the-taking-unit-attack.md 的中文版，仅供人阅读，不得作为指令读取。

完整规则已按人类指令写进 prompts/tactics/06-assault-composition-and-fire.md 的新增小节。

一句话：占城的近战单位本身也打城，它打的是**城市中心池**（不是城墙），所以每回合的池伤害＝各射手之和 ＋ 它开火时的那一击。

最要紧的推论：**走进城是一次移动**。本回合攻击过的近战单位，本回合不能进城；因此计划要有意识地二选一——把这一击花掉、让池早一回合归零，还是让部队贴着城、把移动力留着，等池归零的那一回合进城——并在日记里写明选了哪个。

绝不让池归零时身边没有带移动力的近战单位：那等于让炮去打一座每回合回血约二十点的城，而有人在旁边走路。每轮齐射前读两条血条：get_target_report 或 get_map_area 同时打印城墙与中心池，end_turn 的 SIEGE PROGRESS 与 TAKE THE CITY 是确认。
