> 本文件是 `tactics-audit.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

---
title: Can the tactics files actually be executed? - an audit of prompts/tactics/
---

问题（人类，2026-09-30）：「prompts/tactics/ 里的策略是否都能落地被执行？」——`prompts/tactics/` 里的每一条策略是否真的都能落地并被执行？

**答案是：不能，并非全部都能，而且这些失败聚成四类。** 每个文件的核心都是可执行的——它点名的工具确实存在，它引用的区块确实会被打印，它援引的规则确实在生效——但每个文件也都至少带有一条按原文无法落实的关键断言，其中两个（`04`、`07`）只有大约一半可执行。另外，比任何单个文件都更严重的是：**投递机制本身几乎从不运行**，所以教条通常根本到不了智能体那里。

*撰写时的状态（2026-09-30，游戏 T288+）：`prompts/tasks/tmp/` 为空——承载实力（power）一节的任务 028（那段开发窗口）在 T288 到期，已在 `done/` 中。这使得指令、`prompts/tactics/` 与 `prompts/checks/turn-checks.md` 成为运行中的会话里仅存的教条载体，所以这份审计更加重要，而不是更不重要。*

## 本文是如何核查的

四项独立审计，每两项文件一组，每项都把每一条可执行的断言与事实依据交叉核对，而不是与文字描述互证：

- `src/civ_mcp/server.py`——MCP 工具面：文件点名了却不存在的工具就是无法执行的，而援引它的提案会被编排器自身的未知工具检查拒绝；
- `src/civ_mcp/end_turn.py` + `docs/turn-result-blocks.md`——文件叫智能体去读的区块、行或指标是否真的会被产出，以及在什么条件下产出；
- `prompts/checks/turn-checks.md`（现役）对比 `prompts/checks/pending/`（已暂存、未强制执行）；
- `prompts/workers/military-map.md` / `economy-cities.md`——决定一个文件能否到达顾问的触发表；
- `prompts/strategies/china-conquest/directive.md`——同一个智能体所遵循的常设战略，而多个文件与它相矛盾。

针对投递这一半写了两件工具，都是只读的，放在 `.tools/` 下：`tactics-in-briefs.mjs`（某个文件的文本是否曾出现在一次 `civ_advisor` 调用中？）与 `tactics-warnings.mjs`（顾问们对它说了什么？）。下文的每一条发现都给出证明它的代码或转录记录。

## 系统性问题：教条很少能到达顾问

这八个文件不是工具，也没有任何规则会读取它们。编排器必须挑出匹配的文件，并**把它的文本粘贴进** `civ_advisor` 调用；worker 提示词明确这么说（`military-map.md:15-18`，“编排器会传入相关战术文本”），并且要求 worker 在文本缺失时投诉（`military-map.md:17-18`）。

对全部 158 份会话转录的测量结果（`.tools/tactics-in-briefs.mjs`，以每个文件的**标题行**作为检索串，因为仅凭路径会在 `AGENTS.md` 内的引用表中出现）：

| | |
|---|---|
| 会话转录 | 158 |
| 至少调用过一次顾问的会话 | **98**（`civ_advisor` 行：4535） |
| 战术文件自身的文本出现过的会话 | **共 18 个，每个文件 1-7 个** |
| 战术文件**出现在一条 `civ_advisor` 行上**的会话 | **1**（`tactics/04`） |
| `warnings` 中点名某个战术文件的提案行 | **339** |
| `assessment` 中点名某个战术文件的提案行 | 90 |

那 339 条 warning 正是 worker 在做角色提示词要求的事：点名 brief 本应携带的文件。所以顾问层*确实*在被调用（98 个会话、255 次调用——而 `docs/agent-efficiency.md` §4.4 早已指出，这些开销大部分换来甚少），但教条文本一直留在后面。三个具体原因：

1. **没有任何东西把粘贴自动化。** 在 79 个工具的 MCP 工具面里没有 `get_tactics`/`read_tactic` 工具，所以投递每一回合都取决于父智能体的记忆。
2. **两个最重要的文件正是最大的两个**：`04-staging-out-of-range.md` 有 **34.8 KB / 458 行**，`07-pre-war-analysis.md` 有 **30.4 KB / 437 行**——每次粘贴约 9-10k token，而其余文件只有 5-7 KB。README 说得“一次查阅一两个”是实打实的成本。
3. **没有任何测试覆盖投递或一致性。** `tests/test_advisor_brief.py` 检查的是一个演练固件，`test_advisor_proposal.py:72` 检查一份 assessment 是否*以* `prompts/tactics/` *开头*，`test_agents_references.py` 检查 `AGENTS.md` 的表格指向的文件是否存在——没有任何东西检查某个文件的数字是否与它必须满足的规则文件相符。

## 逐文件结论

| 文件 | 结论 | 决定它的那条断言 |
|---|---|---|
| `01-unit-production.md` | 部分可执行（在改善） | 攻城那一行是区间（1-3），不是旧的 2；**反骑兵链现在与规则一致**（2026-09-30：`PIKE_AND_SHOT`、`MODERN_AT` 被加入 `counter-the-cavalry` 和 `end_turn._MELEE_TYPES`）；投石车（Catapult）对城市的数值是游戏里 Bombard 的 35，不是 45；没有组建军团/集团军（Corps/Army）的动作 |
| `02-contact-on-discovery.md` | 部分可执行（在改善） | 它的和平时期蛮族触发器既没有兵种类别、也没有相对单位的距离（两者都只存在于 `BATTLE ASSESSMENT`，而该区块以战争/受损为门槛）；没有只读的估算动作；**`mass-on-contact` 覆盖哪些接触现在已在文件中写明**（2026-09-30） |
| `03-under-attack.md` | 大部分可执行（在改善） | 没有规则禁止它所建议的撤退（`answer-the-attack` 与 `mass-on-contact` 都接受已说明的撤退）；**第 1 步现在指向 `== Events ==` 行以取得我们自己的损伤**（2026-09-30），并说明攻击者是从 `BATTLE ASSESSMENT` 推断出来的，而撤退情形带有 `UNUSED ATTACK` 回弹与 `skip_remaining_units(force=True)`；剩下的问题是“敌人攻击了一座城市”既无事件也无指标，所以只能靠 `get_cities` 的差异比对 |
| `04-staging-out-of-range.md` | 约一半可执行（在改善） | 它所依赖的 RALLY 那一段现在是**活的**（查询会输出一个 d3 集结环，2026-09-30）；**第 6.2 步现在有了判据**——计划会针对每个射手所在格回答 `FIRE` / `FIRE?` / `NO LINE OF SIGHT`，来源既有地图也有引擎；剩下的是移动点路径代价、任何 ZOC 输入，以及一个没有动作可用的劫掠（pillage）阶梯项 |
| `05-formation-and-screening.md` | 大部分可执行（在改善） | **`WOUNDED IN REACH` 现在已被指明是 CLI 脚本的区块，并给出了 MCP 回路中的测试方法**（2026-09-30）；“绝不与*城市*相邻”没有强制手段；屏护的身份没有被报告 |
| `06-assault-composition-and-fire.md` | 部分可执行（在改善） | 编成表已**修正**（攻城是区间，撞车/攻城塔那一行已删除，加入了反骑兵，占领类别已更正，对城市的数值是游戏里 `Bombard` 的强度），而且第 0 行那个移动前的环上 LOS 问题现在有了判据：集结计划对每一格的 `FIRE` / `NO LINE OF SIGHT` 判定，并且自 2026-09-30 起还覆盖了**已用完**的情形（`NO SHOT THIS TURN`，来自引擎的 `CANFIRE ... spent`，它也会把开战回合向后推一回合） |
| `07-pre-war-analysis.md` | 部分可执行（营地分支更弱） | 第 0 步里那个已死的工具名已**修正**（2026-09-30：`get_trade_options`）；**关卡 2（环上 LOS）现在可以在宣战之前回答**，依据是集结计划的地图规则加上引擎的 `CANFIRE`（2026-09-30）；攻城塔的建议与 C3 的说法已**修正**（2026-09-30）；不再从 MCP 回路承诺 `WOUNDED IN REACH` |
| `08-war-and-the-home-front.md` | 大部分可执行（在改善） | 它引用的每一个区块与规则都在生效（`10-TURN REVIEW`、`WAR ECONOMY`、`builder-backlog`、`carrying-capacity`），而且它的实力（power）一节的规则**自 2026-09-30 起也已生效**（既然不可能再有早于该指标的服务器在运行，`power-the-cities` 就被切了进来），所以那个只能由人来看的横幅兜底现在只适用于陈旧的服务器；过期的军力数字（306 -> 282）与已退役的任务路径已**修正**（2026-09-30） |

## 已由人类指示裁定，2026-09-30

四项裁定回答了本审计发现的矛盾，四项现在都已进入智能体真正读取的文件（指令预设**以及**现役 `SKILL.md` 的 DIRECTIVE 区块、现役规则文件、战术文件、worker 提示词、`end_turn` 的编成表以及集结计划打印的上限）。中文备份逐一镜像了其中的每一项。

1. **攻城数量是区间，不是配额**：按算术是 1-3 辆投石车——视情况两辆或三辆，绝不写死，而且当地形与远程火力线已经覆盖城墙血池时，**一辆就够**。写入了 `tactics/01`（那一行与那段算术）、`tactics/06` 的编成表、`tactics/04` 的突击清单与报告模板、`directive.md`（两处）、`turn-checks.md` 的突击编成前言，以及 `end_turn._WAR_TRAIN`——后者现在带有**下限 1**、目标 3，这样一门炮永远不会被报成缺编。
2. **不造也不投入撞车与攻城塔**——包括帝国已经拥有的那种，而指令此前把它留作例外。已从 `directive.md`、`tactics/01`（那一行现在写着“never”）、`tactics/04`（三处）、`tactics/05`（推进顺序）、`tactics/06`（那一行与工作顺序）、`tactics/07`（关卡 4 与各项禁止）、`tactics/README.md` 与 worker 提示词中移除。
3. **袭击算作战争。** `mass-on-contact` 与 `answer-the-attack` 现在会在 `at_war` **或** `camps_within_3` 时触发——没有新指标，所以文件被读取的那一回合改动就已生效——指令的营地段落、`tactics/07` 的 C3 说法与 worker 提示词都这么说。占领类规则（`one-garrison-per-city`、各项升级规则）仍只适用于战时，因为袭击是一场战斗而非占领；三格之内没有营地的蛮族仍然两者都不触发。
4. **蛮族营地要被清剿。** worker 提示词里“不要清剿蛮族营地”那一条——最后一个仍带着已退役规则的地方——现在承载营地教条：六道关卡、远程加一名近战走进去、在袭击**之前**（而不是代替袭击）报告可转化的蛮族。

这些裁定**没有**触及、因而在本审计中仍然未决的是：工具缺口（`pillage` 没有动作；`WOUNDED IN REACH` 仅限 CLI；没有移动点路径代价或 ZOC 输入；禁止清营地是四项中唯一纯属文字的一项），以及投递方面的发现。其中四个缺口此后已被补上——集结那一段、视线判据、`SIEGE POSTURE` 的可用性（均在 2026-09-30，见排序后的修复项）以及 `07` 第 0 步那个已死的工具名。

## 四类失败及其证据

### A. 文件与指令或现役规则相矛盾（自我拆台的教条）

| 发现 | 证据 |
|---|---|
| 攻城编成在 `01:17` 与 `06:9` 里是 **2**，而指令说 3、现役规则要求 `>= 3`（`turn-checks.md:224`）。**2026-09-30 已解决**：那一行现在按算术是 1-3 的区间，规则的下限是 1，`end_turn._WAR_TRAIN` 带有下限 1 / 目标 3。 | 曾让一个听话的会话的 `siege-train` 保持红色；现在不会了 |
| `07:234,288,345` 用“Battering Ram -> Siege Tower”回答关卡 4，`06:11` 保留了一行撞车/攻城塔，与指令的“我们两者都不造”相矛盾。**2026-09-30 已解决**：凡是提到它们的文件，都改成不造也不投入撞车与攻城塔。 | 基于 `07` 的提案曾下令生产一个被禁止的单位 |
| `07:114` 说 `mass-on-contact` 会“完全像一场战争一样”强制营地的集中兵力；而该规则以 `metric(at_war) >= 1` 为门槛（`turn-checks.md:142`），袭击又不构成战争，所以对营地而言**没有任何东西**强制执行“两名攻击者”规则。**2026-09-30 已解决**：规则现在在 `at_war` **或** `camps_within_3` 时触发。 | 实测的规则文本 |
| `06:10` “近战是唯一能夺取城市的单位”——与 `06:104-107` 以及 `take-the-city`（“近战、反骑兵与**骑兵**”，`turn-checks.md:190`）相矛盾。 | 文件自相矛盾 |
| `01:19` 把反骑兵链终止于 Pike and Shot，但 `counter-the-cavalry` 只计 `SPEARMAN, PIKEMAN, AT_CREW`（`turn-checks.md:86`）——`UNIT_PIKE_AND_SHOT` 是后缀不匹配，计数为 0。 | 这条规则无法被文件所推荐的那个单位满足 |
| `military-map.md:104-108` 下令“**不要清剿我们领土附近的蛮族营地**”，而指令已把营地列为目标、`answer-the-camp` 也已生效（`turn-checks.md:353`）。**2026-09-30 已解决**：该条目现在是营地教条，并带有“袭击即战争”一句。 | 顾问的角色文件与它被简报的那份文件相矛盾 |
| `03:36-37` “城市里的敌人绝不能留活口”——指令的驻军规则说的正相反：驻守单位在城市被攻击时**不受伤害**，只有夺取该城才能将其移除（`directive.md:193-201`、`manual.clean.txt:1065`）。 | 文件下令向一个打不痛的目标开火 |

### B. 工具不存在，或无法运行

| 发现 | 证据 |
|---|---|
| **`pillage` 没有动作。** 指令下令劫掠（`directive.md:545`，“劫掠那座圣地……比任何数量的单兵击杀都更值钱”），集结阶梯也把它作为一级提供（“劫掠（骑兵无视 ZOC）”），但 `unit_action` 的动作列表里没有 `pillage`（`server.py:1662`），`src/` 里也不存在任何劫掠代码（只有修复与读取路径）。游戏本身是暴露该动作的（劫掠修正，`Expansion1_Buildings.xml:185-189`）。 | 工具唯一无法执行的那条常设命令。**2026-10-01 已解决**：`unit_action(action="pillage")` 下发游戏自己的 `UNITOPERATION_PILLAGE`（`lua/units.py::build_pillage_unit`），先报告地块上有什么，并对四种失败方式分别拒绝（没有移动力、距离太远、此处无可掠夺、已被掠夺） |
| `07:39,69,74` 第 0 步调用 **`get_deal_options(player_id)`**——这不是 MCP 工具。工具是 `get_trade_options(other_player_id)`（`server.py:1333`）；`get_deal_options` 是内部方法名（`game_state.py:1230`）。编排器的第三阶段校验会拒绝未知工具，所以援引它的提案会被丢弃。 | 实测；而且这扇侦察之门已经死了。**2026-09-30 已解决**：三处调用点都写成 `get_trade_options`，那条“37 铁”的说法也已删除——该工具打印的是资源**种类**，不是数量（`narrate.py:1099-1114`） |
| `07:97` 用 `scripts/probe-tile.py` 回答营地关卡 C2，`04:213,235` 用 `scripts/staging-plan.py`：两者都会**打开自己的 FireTuner 连接**（`probe-tile.py:38-40`、`staging-plan.py:6-8`），在 MCP 会话占着那唯一一个连接时无法运行。MCP 侧的路径是 `get_map_area` 以及 `kill_x/kill_y` / `next_city_x/next_city_y` 参数。 | “一次只能有一个会话” |
| `05:83-88` 与 `07:276` 让智能体去读一个 **`WOUNDED IN REACH`** 区块，而它只存在于 `scripts/play-turn.py:679-684`（及其测试）中——从不在 `src/civ_mcp` 里。在 MCP 回路中这一行永远不会被打印。 | 智能体在等一行永远不会出现的文本 |
| `01:92-99` 解释了何时组建军团或集团军；但没有任何动作可做（`unit_action` 列表；`src/` 里没有 `FORM_CORPS`/`FORM_ARMY` 的任何东西）。只有 `run_lua(context="ingame")` 或人类的 UI。 | 文件承认了这一点并给出兜底方案 |
| `02:80-84` “每种对局估算一次，然后决定”——唯一的估算器运行在 `attack` **内部**（`game_state.py:475-497`），而那会真的发起攻击。没有只读的估算工具。 | 文件自己的测试不付出代价就无法运行 |

### C. 没有任何查询会返回的数据

| 发现 | 证据 |
|---|---|
| **没有视线判据，而有四个文件需要它。** `04:352-355`（逐格测试 LOS）、`05:36`、`06:64-71`（第 0 行：“在第一次移动之前，环上哪些格能开火”）以及 `07:191-214`（关卡 2，“开火清单，在宣战之前”）。集结计划仅凭 `distance == 2` 就标上“`- FIRE from here`”（`staging.py:418`）；`CAN ATTACK:` 是一行 `get_units` 输出，它从不列出城市、并跳过攻城单位（`lua/units.py:86-87,95`）；`SIEGE POSTURE` 不点名任何格。 | 整套教条所围绕的那个突击前问题无法回答。**2026-09-30 已解决**：环上每一行现在带有游戏自己的逐格 `SightThroughModifier`，外加距离为 2 的一对格之间的格子，`civ_mcp/los.py` 应用手册的规则（`manual:999`），每个射手所在行都会打印 `FIRE` / `FIRE?` / `NO LINE OF SIGHT: <blocker>`；对于已经在环上某格的火炮，查询会直接问引擎（`CANFIRE`，即攻击路径所用的同一个 `CanStartOperation(RANGE_ATTACK)`），而该读数会覆盖地图的结论 |
| **RALLY 那一段是死代码。** `_rally_option` 只保留 `distance >= 3` 的环上格（`staging.py:369`），但产出的环是 `d >= 1 and d <= 2`（`lua/units.py:2521`），而选项只对环上格存在——所以 `ASSEMBLY FIRST` / `RALLY`（`staging.py:386-392,409-414`）永远不会打印。钉住它的那个测试构造了一个合成的 `distance=3` 环上格（`tests/test_staging_plan.py:457,466-471`），于是**一个绿色的测试覆盖着一个不可达的特性**，而 `04:53-54` 又禁止手工计算——那是唯一的替代办法。 | `04` 第 1 步按原文无法执行。**2026-09-30 已解决**：查询会在 d3 输出一个真正的 `RALLYRING`（最靠近军队质心的六个格）并带有自己的 `RALLYOPTION` 路径，测试断言的是查询文本而不是合成的环 |
| **`SIEGE FIRE` / `SIEGE POSTURE` 恰恰在触发 `04` 的那种状态下被抑制**：当没有任何东西暴露、且最近的城在 `> 3` 格之外时，该区块返回 `None`（`end_turn.py:1275`），而 `SIEGE FIRE: n/m` 只在有**两个或更多**攻城单位时才打印（`end_turn.py:1291`）——一门炮拿不到那一行，而这是典型的失败案例。`04:363-373` 让智能体在集结点读它。 | 需要这个读数的地方恰恰没有这个读数。**2026-09-30 已解决**：它从五格以内就开始打印并带 `assembling` 表头，对单门炮也打印火炮数量（`1/1` 是被认可的单炮突击） |
| **没有移动点路径代价。** `04:46-54,446` 用移动点计算“集结所需回合数”；`PathingEstimate` 只返回 turns/total_tiles/reachable_this_turn（`lua/models.py:607-614`），而 `turns` 是从第 1 回合起按“每回合多少格”外推出来的（`lua/units.py:2466-2473`）。计划还把放置上限设为 `turns_ahead=2`（`server.py:842`），于是那个慢单位——“通常是更长的那根杆”——会被报成未放置。 | 集结时间表是对一个估算值的估算 |
| **ZOC 是不可见的**（`04:172-175`、`02:17`）：`get_pathing_estimate` 与 `get_staging_plan` 都不对它建模；适配器只在攻击时拒绝（`lua/units.py:539-542`）。 | 一次整回合的停滞从不出现在计划里 |
| 和平时期的接触不可读（这是 `02` 的触发器）：`get_units`/`THREAT:` 打印的距离是量到我们的**城市或单位**的（`lua/units.py:1034-1038`），而 `promotion_class` 以及只针对单位的距离只出现在 `BATTLE ASSESSMENT` 中，该区块在战争/受损之外被抑制（`end_turn.py:2164-2168`）。 | `02` 可能在没有它所依据的数据时被触发 |
| 攻城指标是量到**任何**主要文明最近的可见城市的，无论是否交战（`lua/units.py:1390`），所以 `SIEGE FIRE` 与 `concentrate-the-siege` 可能算在一座比目标更近的中立城市上；屏护的身份从未被报告（`05:90-95`）。 | 几何关系错了，而且没有办法指认屏护 |
| 营地关卡 C1/C2/C5 部分无法回答：`get_map_area` 给出蛮族的类型标签，但没有 CS/HP（`lua/map.py:211-219`）；“营地一直在产出什么”以及它的金币/时代奖励都没有查询；`BOOSTED` 标记从不以 `07:130` 所引用的字面量 `boosted=True` 出现。 | 六道营地关卡中有三道只能靠推断 |
| **`03` 把第 1 步指向了错误的区块，而它的第三个触发器完全没有数据。** `03:9-10` 让智能体去 `BATTLE ASSESSMENT` 找“是谁干的”，但那个区块只列**敌人**（`end_turn.py:2179-2254`）；我们自己的损伤在 `== Events ==` 行里：“`>> Your X (TYPE) took N damage! HP: h/max at (x,y)`”（`game_state.py:1886-1893`，渲染于 `end_turn.py:3754`）。而“敌人攻击了一座城市”（`03:3-4`）**既没有事件也没有指标**——`damaged_this_turn` 统计的是单位（`end_turn.py:2016`）——所以只能靠比对 `get_cities` 的城墙/驻军 HP 才看得见。 | 文件三个触发器中的一个不可观测 |
| **文件漏掉了那个真正卡住回合的关卡。** 一个未使用的合法攻击会让 `end_turn` 以 `UNUSED ATTACK at end_turn ... call skip_remaining_units(force=True)` 回弹（`end_turn.py:759-765`），而 `skip_remaining_units` 在没有 `force` 时会拒绝（`server.py:1763`）。`03:54-57` 建议撤走一个受伤单位，却没有提到在做出那次调用之前撤退会被阻塞。 | 所建议的走法按描述无法执行 |
| **实力（power）读数受部署限制。** 这一节需要的一切都随提交 `8353672` 落地，所以在更早启动的服务器上，Lua 输出的是旧的字段数，`power_reported` 为 false，`get_cities` 打印**没有**任何 power 文本；该节的兜底（“读数就是城市横幅”）是人类的 UI——没有任何工具会返回它。该规则也仍然处于**暂存**状态，所以在它被提升之前，power 方面不会有任何检查失败。 | 在全新的服务器上可执行，在正在玩的那个上不行。**2026-09-30 已解决**：既然不可能再有早于该指标的服务器在运行，`power-the-cities` 已被切进 `turn-checks.md`（`attacks-that-land-nothing` 也一并切进），所以 `unpowered_cities` 现在是一条会失败的检查，带有 `CHECK FAILED` 行，而不再是一个暂存的意图 |

### D. 次要与表面问题（2026-09-30 已修复，附两点说明）

这一批，以及各自的修法：`06:32` 的 `garrison:` 标签其实是 `Gar:`（而且血池是 `Garrison h/max`）——`narrate.py:370-376`；`06:114` 的 `producing: NONE` 其实是 `Building: nothing`（`narrate.py:349-354`）；`06:232` 的 `NO_WALLS` 引文现在带上了代码里的破折号（`lua/cities.py:490`）；`06:190` 的大将光环**同时**引用了手册的两处表述——概述把它说成“在其所在位置的 1 格之内”（`manual.clean.txt:1095`），详细段落说成“在大将 2 格之内”（`:1097`）——并指向游戏自己的能力文本，即 `get_great_people` 打印的那行 `Passive aura (granted while this unit lives)`；`08:34` 的“military 262 -> 306”应为 262 -> 282，也就是它自己表格里的数字；`08:70-71` 引用了已退役的 `prompts/tasks/tmp/done/023-dutch-siege-corps-done-T259.md`。

**攻城伤害数值的错，方向与本审计自己的说法正好相反。** 审计说 `01:75` 与 `directive.md:160` 把*投石机*（Trebuchet）写成 45，而规则说 55。游戏数据说 `UNIT_CATAPULT` 的 Bombard 是 **35**、`UNIT_TREBUCHET` **45**、`UNIT_BOMBARD` **55**、`UNIT_ARTILLERY` **80**（`Base/Assets/Gameplay/Data/Units.xml`）——所以 Trebuchet 的 45 是对的，错的是**投石车（Catapult）**的 45（`directive.md:165`、`01:31,90`、`06:9`），`turn-checks.md` 与 `end_turn.py` 里的那一对也错了（“投石车对城市造成 45，而投石机造成 55”）。现在它们全部带有游戏里 `Bombard` 的强度，并另行说明：一发*射击*对一个 200 HP、CS 35-40 防御的城市大约打出 45-52——两个数字被混淆的正是这里。

仍然未决、且是有意保留的：`enemy_cities_seen` 被计算出来却没有任何东西消费它（`end_turn.py:47,1340`）——作为一个未来规则可用的指标并无害处，而删掉它只会白白搅动指标元组。

**同一次审计还发现了另外两处需要更正的地方，其中一处是我的。** 审计自身的交叉核对抓到了我写进 `tactics/08` 以及当时暂存的 power 规则里的一处事实错误：商人总督的 `RENEWABLE_ENERGY` **不是**“一次总督晋升”——它排在 Tax Collector 之后，而 Tax Collector 又排在 Harbourmaster 或 Foreign Exchange 之后（`Expansion1_Governors.xml:223-228`）。两个文件现在都这么写了。另外，审计说“1 Coal -> 4 Power”的换算率“不在任何 XML 里”是错的：这些比率在游戏的**文本**文件里，而不是在它的玩法数据里——`LOC_BUILDING_COAL_POWER_PLANT_DESCRIPTION`（“1 Coal -> 4 Power”）、核电站的 `LOC_BUILDING_POWER_PLANT_EXPANSION2_DESCRIPTION`（16），以及 `LOC_PEDIA_CONCEPTS_PAGE_POWER_CHAPTER_CONTENT_PARA_4`（“Coal and Oil Power Plants provide 4 Power per resource, while Nuclear provides 16”）。`tactics/08` 里的表格是对的；它的引证应当指明 `Expansion2_Buildings_Text.xml` 与 `Expansion2_Civilopedia_Text.xml`。

## 哪些部分*没有*坏

值得直说，因为上面那份清单读起来比现实更糟：文件所描述的武库是存在且可用的。`get_staging_plan`（包括营地变体与 `WALK-IN OPENS`）、`get_pathing_estimate`、`get_map_area`、`get_units`、`city_action`、`get_trade_options`、带格子与占领单位的 `TAKE THE CITY` 区块、带 `supply line n/6 cut` 与 `SIEGE STALLED` 的 `SIEGE PROGRESS`、`city hp: N/200`、最远优先排序及其 `issue-the-calls-furthest-first` 规则、`STACKING_CONFLICT`、补给六角格指标与 `cut-the-supply` 规则、手册中关于治疗与修墙的段落、`hold-what-you-take`、`take-the-city`、`counter-the-cavalry`、`finish-the-wounded`、`one-garrison-per-city`、`10-TURN REVIEW` 及其 `WAR ECONOMY` 行——以上每一项都被核实为存在且生效。缺口是具体的，不是普遍的。

## 按优先级排序的修复项

**文档中的一行式修改（不涉及代码）：**

1. `01:17` 与 `06:9`：攻城 **2 -> 3**，以及 `04:448` 的 `siege n/2 -> n/3`，与 `directive.md:223`、`turn-checks.md:224`、`staging.py:45` 保持一致。**2026-09-30 被取代**，依人类的裁定：攻城是区间（按算术是 1-3），不是配额——文件现在就是这么说的。
2. `07:39,69,74`：`get_deal_options` -> **`get_trade_options`**，并去掉“37 铁”的说法（`narrate.py:1099-1114` 打印的是种类，不是数量）。**2026-09-30 已应用**。
3. `07:234,288,345` 与 `06:11`：删掉作为关卡 4 答案的攻城塔；把撞车规则只说一次——已拥有的撞车与近战单位同格叠加，什么都不用买。
4. `05:83-88` 与 `07:276`：不要再从 MCP 回路承诺 `WOUNDED IN REACH`（或者把它打印出来）。**2026-09-30 已应用**：两个文件现在都说该区块属于 CLI 脚本，并给出了 MCP 回路中的测试方法（`get_units`：我们的 HP 对照该单位的威胁清单，两格以内 60 HP 或以下）。
5. `07:114` 与 `02:43`：`mass-on-contact` 覆盖不到袭击或和平时期的接触——要么说明这一点，要么限定该规则的范围。**2026-09-30 已应用**：该规则在 `at_war` **或** `camps_within_3` 时触发，`02` 说明了它覆盖哪些接触、哪些是它自己该做的决定。
6. `06:10` 改为“近战、反骑兵与骑兵”；把反骑兵那一行加进 `06` 的表格；`01:19` 的 Pike and Shot 要么加入 `counter-the-cavalry` 的列表，要么让这条链终止于 Pikeman。**2026-09-30 已应用**：那一行已在 `06` 的表格里，规则的列表现在是游戏完整的反骑兵链（`SPEARMAN, PIKEMAN, PIKE_AND_SHOT, AT_CREW, MODERN_AT`，与 `scripts/experiment-report.py:145` 读取的是同一组）——过去一个 Pike and Shot 会被读成*没有*反骑兵单位，从而每回合都让规则失败。`end_turn._MELEE_TYPES` 带有同样的两处新增。
7. `military-map.md:104-108`：把“不要清剿蛮族营地”替换成 `07`、指令与 `answer-the-camp` 已经承载的营地教条。
8. `03:9-10` 把第 1 步指向 `== Events ==` 损伤行；`03:54-57` 加上 `UNUSED ATTACK` 回弹与 `skip_remaining_units(force=True)`；`08:34` 306 -> 282；`08:70-71` 重新指向 `done/023-dutch-siege-corps-done-T259.md`；以及 D 类那一批次要项。**2026-09-30 已应用**，并对本审计自己关于攻城数字的说法作了一处更正（见 D 类）。
9. **本轮已经应用**：`tactics/08` 中以及当时暂存的 `power-the-cities` 规则中 `RENEWABLE_ENERGY` 代价的更正（见下面的 D 类）；该规则本身已于 2026-09-30 **切进**，`attacks-that-land-nothing` 也一并切进，所以 `prompts/checks/pending/` 里又只剩它的 README 了。

**代码（每一项都是新行为，因此每一项都需要测试）：**

10. **`pillage`**：把该动作加入 `unit_action`（`server.py` + 一个 `GameState` 方法 + Lua `UNITOPERATION_PILLAGE`），或者删掉指令里那一行与阶梯项。指令今天在下令劫掠，而没有任何东西能做到。**2026-10-01 已应用**：动词已存在，指令那条常设命令第一次变得可执行。
11. **一个集结环**：给集结 Lua 加上 `d >= 3` 的环（或一个集结查询），让 `_rally_option` 能触发，并让工具能回答 `04` 的第 1 步。**2026-09-30 已应用**（`RALLYRING`/`RALLYOPTION`，提交 `99765a9`）。
12. **每个环上格的视线/开火标记**：单项价值最高的新增——它一次性解开 `04` 第 6.2 步、`05`、`06` 第 0 行与 `07` 关卡 2。**2026-09-30 已应用**：`civ_mcp/los.py`（把手册规则套在游戏的 `SightThroughModifier` 上）、每个环上行的视野事实，以及对于已经就位的火炮由引擎自己的 `CANFIRE` 给出回答（它覆盖地图结论）。
13. **`SIEGE POSTURE` 的可用性**：不要在集结距离上返回 `None`，并且即使只有一个攻城单位也打印火炮数量，好让 `04` 的读数在 `04` 的状态下存在。**2026-09-30 已应用**（提交 `99765a9`）。
14. **一个只读的战斗估算工具**（暴露 `build_combat_estimate_query`），好让 `02:80-84` 在不实际发起攻击的情况下被遵守。
15. **军团/集团军**，或者删掉那段。
16. **投递**：一个 `get_tactics(name)` MCP 工具（或顾问侧注入），让文件文本不再依赖父智能体的记忆——今天测得 158 个会话中只有 1 个。
17. **一个一致性测试**：读取 `turn-checks.md` 的单位列表与数量，断言 `01`/`06` 的编成表与它们一致。这才是持久的修法——正是这类漂移产出了“攻城 2”的发现与 Pike-and-Shot 的不匹配，而今天没有任何东西能抓住它。

**来自战前工作流评审（2026-09-30），而非本审计的四类问题：**

18. **一次战前侦察调用（C3）。** 对 `07` 实际所做之事做的八点评审发现，它的前三道关卡是由对每个目标的三四次分开读取拼起来的，而它需要的三个数字（城墙、城市中心血池、驻军单位）根本不出现在任何指标里。**2026-09-30 已应用**：`get_target_report(target_x, target_y)` 返回格子、其上的城市、**目标**三格以内的可见敌人，以及集结计划——两次查询，在宣战之前，并说明该格是 `visible` / `revealed` / `fog` 中的哪一种。`07` 第 1 步与关卡 1 指向它，`AGENTS.md` 点名它，`tests/test_target_report.py` 钉住解析器、叙述、查询的只读性与编成。
19. **一份增援时间表（C4）。**“缺失的角色哪一回合能到集结点”原本是两个分开的数字——`get_city_production` 的建造回合数与 `get_pathing_estimate` 的行军回合数——没有任何东西把它们合起来。**2026-09-30 已应用**：`get_reinforcements(target_x, target_y)` 读取我们的生产队列（仅军事单位，经由 `bq:GetCurrentProductionTypeHash()` 与 `GetTurnsLeft()`），为每个建造城市挑选最近的集结格，并打印 `ready T+n`、行军、抵达回合，以及计划与队列都没覆盖到的角色。行军这一段是**六角格距离估算**并如实说明：游戏的寻路需要一个单位，而正在建造的单位还不存在——它出现的那一回合，`get_staging_plan` 会精确回答那一段。`07` 第 3 步指向它，`tests/test_reinforcements.py` 钉住解析器、算术、叙述、查询与编成。

## 方法说明与局限

逐文件审计由四个子智能体针对代码运行，而不是针对文字描述；上文每一条断言都带有证明它的文件与行号，两条头条发现由我本人重新核实（`pillage` 没有动作，以及集结那一段不可达是因为测试用的环是合成的）。本审计**不**覆盖的内容：*教条本身*是否是好的战略（那是指令与回顾文件的事），以及 `prompts/tactics/` 之外的任何文件——同一类检查还没有在 `prompts/workers/*.md` 上跑过，而那里已经知道有一处矛盾（上文的营地段落）。
