> 本文件是 `054-relieve-arnhem-a-barbarian-is-pillaging-the-eastern-rear.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

## 为什么有这份文件

野蛮人进了我们的领土，已经从一座城上撕走两块地：通知里写着「您在**阿纳姆**的农场遭到了野蛮人的掠夺」与「您位于**阿纳姆**的学院遭到了野蛮人的掠夺」，
城市读数里带着 `- Improvement Pillaged at (75,11)`、`!! PILLAGED TILES: FARM`、`!! PILLAGED: CAMPUS, ... LIBRARY, UNIVERSITY, RESEARCH_LAB`。
阿纳姆在 (75,11)，掠夺发生在东部后方——而我方装甲就停在两格之内。

**没有任何东西把这件事告诉会话**，这就是它没被回应的全部原因，诊断值得留下来：

- 覆盖它的条款在 `prompts/tactics/03-under-attack.md`（"A city was attacked. Garrison it (one unit), repair the walls if they are down ..."），
  而**那个文件是给 `military-map` 顾问读的，不是 orchestrator 的回合循环读的**——循环里没有任何一行会打开它。
- `prompts/checks/turn-checks.md` 里**没有**任何营地/野蛮人规则，而 `answer-the-camp.md` 与 `repair-the-pillaged-district.md` **至今仍躺在 `prompts/checks/pending/`**
  ——**待命规则不会被求值**，所以城市读数里本来已经在打印的 `!! PILLAGED` 从未变成"必须行动"。
- 生效中的任务全部是进攻性质（050 拿城、051 唤醒后方炮群、053 第一次齐射），没有一份 `scope:` 提到本土防御。
- 掠夺**不会抬起回合 blocker**：`get_notifications` 只列了世博会特别会议与一次晋升，回合从来没有被迫停下来。

## 本回合做这些，排在格鲁吉亚前线之前

1. **先找到它。** `get_map_area` 以 (75,11) 为中心（半径 2），加 `get_units`——掠夺者是野地里的野蛮人单位，不是有墙的城市。动任何单位之前先说出它的类型：
   类型决定打法（**营地**是没有 HP、没有墙的地块；**枪兵**是反骑兵）。
2. **用手边最近的兵力打死它。** 我方装甲比任何东西都近：现代装甲 (73,13)（HP 61）、现代装甲 (76,12)（HP 56）、特种部队 (78,13)。
   野蛮人单位要用**近战**攻击解决——不要让它活着再抢第三块地。若目标其实是**营地**，一个军事单位**走上去**即可摧毁（无 HP、无墙、无驻军加成），而且那块地从此清干净。
3. **修回被抢的东西。** (75,11) 的农场需要最近的建造者（`get_builder_tasks`，然后 `improve`）；**区域建筑**——学院、图书馆、大学、研究实验室——通过阿纳姆的 `set_city_production` 修复，
   不是用建造者（`!! PILLAGED: ... (repair via set_city_production)`）。这两半都属于本任务。
4. **然后才是前线。** 如果掠夺者已死、建造者已在路上，053 的第一次齐射与 051 的西调本回合照常执行。**本土防御优先，但它不取消战争。**

## 完成条件

`get_units` 中 (75,11) 三格以内 **`count == 0`** 个野蛮人单位，且阿纳姆被掠夺的区域已在其队列里修复或已恢复。
退役本文件时请报告掠夺者的**类型与坐标**——如果它是营地，说明它是否重新刷新，因为那正是 doctrine 从未覆盖的那一半。
