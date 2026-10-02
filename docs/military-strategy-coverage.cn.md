> 本文件是 `military-strategy-coverage.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# 军事策略：模型能看到什么，以及什么真正被强制执行

写于 2026-10-01，回答的问题是"所有军事策略都是可见的吗，它们是否保证会被执行"。这里的每一条主张都以代码或已记录的会话为对照进行了测量——仪器和它们的数字在出现时会被点名，因此这个答案可以重新跑一遍，而不是重新争论一遍。

**简短的回答。** 教条中*作战行为*那一半是可见而且响亮的：27 条 live 规则里有 21 条是关于陆军的（如果把 `hold-what-you-take` 所夺取的城市也计入，就是 22 条，剩下的五条纯粹属于内政），它们每回合都会被评估，它们的失败会被打印出来并计数。而*按决策划分的行动手册*——`prompts/tactics/01`-`08`，那些决定造什么、在哪里集结、何时推进的文件——实际上是**不可见的**：没有任何工具读取它们，顾问按设计完全没有工具，而在 158 个已记录的会话中，八份里有七份从未进入过任何一份顾问简报。在这个系统里，除了下面两级硬性阶梯之外，没有任何东西是在"agent 无法不这样做"的意义上*保证*被执行的；其他一切都是响亮的，而响亮可以用一行日记就被忽略掉。

## 1. 一个策略可以行走的六条通道

| # | 通道 | 载体 | 模型何时看到它 | 测量结果 |
|---|---|---|---|---|
| A | **指令（directive）** | `.dsh/skills/civ6-orchestrator/SKILL.md` 的 DIRECTIVE 块（42,179 字符） | 附加在 `end_turn` 结果上，**每次变更一次**，另加进程内第一次调用时的一次（`src/civ_mcp/server.py:2493`、`strategy_directive.py:53`） | 投递是代码，不是习惯：只要 `end_turn` 被调用，它就不可能被跳过 |
| B | **Live 规则** | `prompts/checks/turn-checks.md`，27 条规则（21 条与军队有关） | 失败期间每次 `end_turn` 都打印 `CHECK FAILED [id] ... (require: ...)`；追加在同一个结果里的 `TURN START` 简报会补上连续失败次数 | 158 份转录中有 43 份曾有一条 live 规则失败；27 条规则中有 21 条至少触发过一次（`node .tools/rule-census.mjs`）；简报本身几乎能到达每一个真的在打回合的会话——66 份显示了回合推进的转录中有 44 份带有它，而另外未带简报的 22 份里有 21 份早于这个功能（`cc1c4a1`，2026-09-21） |
| C | **回合结果块** | `end_turn` 自身的输出 | 当块的条件成立时，就在那一回合 | 在适配器日志上：BATTLE ASSESSMENT 195、SIEGE POSTURE 131、SIEGE PROGRESS 147、SIEGE FIRE 74、SIEGE STALLED 2、LOYALTY WARNING 34、UPGRADE AVAILABLE 154、WAR ECONOMY 18、10-TURN REVIEW 94、MATCHUP 5（`python .tools/block-census.py`） |
| D | **工具拒绝** | `src/civ_mcp/lua/*.py` 里的 `ERR:` 集合 | 只在命令被下达的那一刻 | 18 个与军事相关的代码：`SIEGE_CANNOT_ATTACK_UNITS`、`MELEE_CANNOT_ATTACK_AT_SEA`、`NO_LOS`、`OUT_OF_RANGE`、`NO_MOVES`、`STACKING_CONFLICT`、`ZOC`、`REQUIRES_WAR`、`NOT_AT_WAR`、`NO_WALLS`、`ALREADY_FIRED`、`ATTACK_BLOCKED`、`CANNOT_ATTACK`、`NO_TARGETS`、`CANNOT_CONDEMN`、`NO_CONDEMN_COMMAND`、`STOPPED_SHORT`、`NOT_YOUR_TERRITORY` |
| E | **战术行动手册** | `prompts/tactics/01`-`08` | 只有当编排者读取了该文件**并把它的文本粘贴进** `civ_advisor` 调用时 | **八份里有七份从未出现在简报中**；`04` 出现在 1 个会话里（3 行顾问输出）。被读取过的文件：01 在 7 个会话，04 在 3 个，05/06/07/08 在 1-2 个，而 02/03 在**零个**（`node .tools/tactics-in-briefs.mjs`） |
| F | **参考文件** | `AGENTS.md`（每个会话注入）、经由 `search_knowledge` 的 `docs/turn-result-blocks.md` 和 `docs/game-recovery.md` | 会话开始时，或按需 | `AGENTS.md` 由 harness 注入；那些文档只差一次查询，并且 `AGENTS.md` 在使用它们的地方引用了它们 |

**E 为什么失败是结构性的，而不是偶然的。** DSH overlay 给顾问这条路线的**工具为零**——`dsh/civ6.cordis.yml:45-46`、`toolFilter.allow: []`，并带有注释"advisors can reason over snapshots but cannot invoke any tool or create descendants"。所以顾问自己无法读取行动手册；唯一的路径是编排者读取它并粘贴文本，而 skill 在散文中要求这样做（`SKILL.md:673`），测量结果则说这几乎从未发生。

## 2. 强制执行阶梯

"保证"不是一件事。五级阶梯，最强的在前：

1. **被拒绝（Refused）**——命令无法被执行。agent 收到一个 `ERR:`，什么也没有发生。
2. **被阻塞（Blocked）**——在有事情完成之前回合不会结束（`end_turn` 返回一个 blocker：未移动的单位、空的生产队列，以及当一次合法攻击会被丢弃时的 `UNUSED ATTACK`）。
3. **每回合报告直到修复**——一条 live 规则失败，连续失败次数出现在下一次 `TURN START` 简报中。响亮，但 agent 可以在日记里记录原因来接受它。
4. **条件持续期间报告**——`end_turn` 结果中的一个块：数字和被点名的单位，没有持续的连续计数。
5. **仅教条（Doctrine only）**——在决策的那一刻没有任何东西把它浮现出来。只有当恰好正确的文件在上下文中时它才起作用。

## 3. 军事策略，按领域划分

| 决策领域 | 教条在哪里 | 什么强制执行它 | 阶梯 |
|---|---|---|---|
| **生产与编成**（1-3 门炮、2 近战、4 远程、1 反骑兵、1 骑兵） | `tactics/01`，指令 `:229` | `siege-train`、`ranged-mass`、`melee-screen`、`counter-the-cavalry`、`upgrade-the-siege`、`upgrade-the-unwatched`、`keep-the-upgrade-discount`、`match-their-melee` | **3** |
| **发现即接触**（评估、克制、集中或绕过） | `tactics/02` | `mass-on-contact`（3）；BATTLE ASSESSMENT 中的 `counter:` 行（4）；"评估后再投入"是散文 | **3/4**，评估本身 **5** |
| **遭受攻击**（评估、集中、歼灭；何时撤退） | `tactics/03` | `answer-the-attack`、`finish-the-wounded`、`use-your-attacks`（3）+ `UNUSED ATTACK` blocker（2） | **2/3** |
| **集结与集结点**（先在 d3 集合，然后作为一个整体推进） | `tactics/04` | `issue-the-calls-furthest-first` 覆盖*交通*（3）；集结点本身由 `get_staging_plan` 打印（`ASSEMBLY FIRST`、`RALLY x,y d3`），而且没有任何东西检查它 | 打印是 **4**，而"军队必须先集合"这条规则是 **5** |
| **阵形与掩护**（前方掩护，攻城单位在射程 2 的后方） | `tactics/05` | `screen-the-siege`（3）+ `SIEGE POSTURE` 点名每个暴露的单位（4） | **3/4** |
| **突击编成与开火**（工作顺序、集中、不用撞城锤/攻城塔、晋升时机） | `tactics/06` | `concentrate-the-siege`、`take-the-city`、`cover-the-capture`（3）；`SIEGE FIRE`、`SIEGE PROGRESS`、`SIEGE STALLED`（4）；撞城锤/攻城塔的**禁令**自 `ram-tower-before-civil-engineering` 在 T99 退役后已无规则——只有一个支援单位会被拒绝执行占领移动（1） | **3/4**，禁令是 **5** |
| **战前分析**（宣战前的 0-5 号门） | `tactics/07` | 没有任何东西阻塞宣战；`get_target_report` 按需提供 0-3 号门的数据（4）；营地分支有 `answer-the-camp`（3） | **4/5** |
| **战争与大后方**（一座战争城市、+10 金币下限、建造者复利） | `tactics/08` | `carrying-capacity`、`builder-backlog`、`hold-what-you-take`、`one-garrison-per-city`（3）；`WAR ECONOMY` 和 `10-TURN REVIEW`（4） | **3/4**，"一座战争城市"是 **5** |
| **蛮族营地**（突袭或放着不管，六道门） | `tactics/07` 营地分支，指令 `:35` | `answer-the-camp`（3）+ `camps_within_3`；对营地格子调用 `get_staging_plan` 会打印 `WALK-IN OPENS`（4）；面向人类的"报告一个可转化的蛮族"是散文 | **3/4** |
| **宗教**（谴责异端、杀死传教士、攻击信仰收入） | 指令 | 和平时期 `condemn` 回答 `ERR:REQUIRES_WAR`、`attack` 回答 `ERR:NOT_AT_WAR`（1 级）；自 2026-10-01 起 `FOREIGN RELIGIOUS UNITS` 块会点名三格以内的每个单位并给出对应情形的学说（4 级），`religious_at_war_within_2` 是一条暂存规则（提升后为 3 级），而 `unit_action(action="pillage")` 已存在——那正是"攻击信仰收入"一直以来的意思 | 和平时期 **1**，战时 **3/4** |
| **和平**（绝不提出，拒绝每一份提议） | 指令 | 什么都没有：`propose_peace` 是一个会真的执行它的 live 工具；拒绝一份送来的提议是 agent 必须自己选择的 `respond_to_*` 调用 | **5** |
| **移动与交通**（一格一单位、ZOC、移动力、呼叫顺序） | `tactics/04`、`AGENTS.md` | `STACKING_CONFLICT`、`ZOC`、`NO_MOVES`、`OUT_OF_RANGE`（1）；`STOPPED_SHORT` 警告 + `MOVE JAMS` + `issue-the-calls-furthest-first`（3/4） | **1/3** |

## 4. 这些测量说明了什么

**规则。** 27 条 live，其中 21 条关于陆军（加上 `hold-what-you-take` 是 22 条；另外五条是内政：一个奇观、一个区域槽位、金币、建造者、电力）。21 条在已记录的游玩中至少触发过一次；6 条从未触发过：
`concentrate-the-siege`、`attacks-that-land-nothing` 和 `power-the-cities` 是在
2026-09-30/10-01 才加入的，所以零是预料之中的；`take-the-city`、`cover-the-capture` 和 `answer-the-camp` 更老，却仍然从未被观察到失败过。`take-the-city` 的门槛是一座 0 HP 的城市、且我们一个有占领能力的单位相邻——这是一种按设计转瞬即逝的状态，因为城市会在同一回合陷落。它为之存在的那个陷阱（莫斯科处于 `0/200`、一个 Spearman 在两格外，而它治疗回到了 `120/200`）在它自己的注释中被引用，并且早于这个指标，所以**这道守卫从未被看到抓住过任何东西**。

**块。** 战斗的块在战争会话中不断说话——一个漫长的战争会话记录到 BATTLE ASSESSMENT 12、SIEGE PROGRESS 11、SIEGE FIRE 1、LOYALTY WARNING 13。`TAKE THE CITY` 和 `UNUSED ATTACK` 在适配器普查中完全没有被观察到，这与上面的规则普查相符：一次突击的最后一步是被测量得最少的一步。

**行动手册。** 158 个会话中有 98 个至少调用过一次顾问（4,535 行 `civ_advisor`），而顾问文本正是按决策划分的教条本该到达的地方。它到过了一次。

## 5. 缺口，以及各自的修复办法

**G1——行动手册在决策时不可见（最大的一个）。** 教条存在于在需要它的那一刻没有任何东西读取的文件里，而顾问无法自己去取它们。修复办法，从最便宜的开始：

1. **一个 `get_tactics` 工具**：用一个名字调用它（`get_tactics("04")`），或者什么都不传——在后一种情况下，它点名当前指标所指的文件并返回它们的文本。这把"读取文件、记得粘贴它"变成一次调用，而调用的结果*就是*简报材料。这是审计项 16，同一个工具也可以正是 skill 的顾问步骤所点名的东西。
2. **把决定性的数字折进规则里**，规则本来就已经被投递了：攻城区间在 `siege-train` 里，补给杠杆在 `cut-the-supply` 里，阵形在 `screen-the-siege` 里。这是修复办法中持久的那一半，而且已经部分完成。
3. **给顾问路线只读的文件访问权限**（overlay 的 `toolFilter` 里的 `read`/`glob`/`grep`）。这是一个安全决策而不是工程决策：空的 allowlist 是刻意的，而这次调查不建议在没有人类发话的情况下改动它。

**G2——只有散文的教条，而行动是可能的、也没有任何东西阻止它。** 不满足门就宣战；建造或投入撞城锤/攻城塔（它的规则在 T99 退役，此后禁令只活在指令里）；提出和平；"一座战争城市"；战时的宗教僵局。每一项都是一条规则或一次拒绝的候选——最便宜的是撞城锤/攻城塔（一条生产侧规则是可能的：任何队列里都不允许有 `BATTERING_RAM`/`SIEGE_TOWER`）和宣战（一个 `once: true` 门，或者一条在军队处于战备状态却没有任何可见目标时失败的规则）。

**G3——从未开口的守卫。** `take-the-city`、`cover-the-capture` 以及 `TAKE THE CITY` 块从未被观察到触发。要么这种状态在游玩中确实罕见，要么这个指标不可达；区分二者的办法是在下一场战争中有针对性地检查一次——`SIEGE PROGRESS` 块本来就会读出 `city hp: N/200`，所以如果某一回合它读出 0、我们的近战单位相邻、却没有 `TAKE THE CITY` 块，那就是一个指标 bug，值得用一行日记记录下来。

**G4——让部分教条无法被强制执行的那些指标盲区。** 控制区（Zone of Control）对两个寻路工具都是不可见的，所以一份计划可能穿过它做路线，而单位就只是停下来；而计划的抵达回合是从移动力外推出来的，而不是真实的逐格代价。那些领域的教条只能手工遵循，而说明这一点的文件又无法被投递（G1）。**其中"宗教单位"这一半已在 2026-10-01 补上**——见第 7 节——而补它的过程还暴露出文档沿用数月之久的判据本身是错的：游戏数据里根本不存在 `FORMATION_CLASS_RELIGIOUS`。

## 6. 2026-10-01 改了什么：发现这条链路

问题里要的那个实例推演（"一个侦察兵发现了一座城市——agent 是怎么知道的？"）最后发现没有可用的答案，于是把它建了出来。旧的链路是：一次移动只回报地格（`MOVING_TO|58,42|from:54,40`），唯一会说出*内容*的那个块被限制在**本会话**首次揭示的地块上，而在 158 份有记录的会话里它一次都没有报告过城市或营地；`end_turn` 里也没有任何东西对"一座城市出现"作出反应——`enemy_cities_seen` 被算出来而**没有任何规则读它**，占领相关的块在血池归零之前一直沉默。发现只能靠拉：`get_map_area` 给出地格与归属者（`[CITY_CENTER]`，没有名字），`get_trade_options` 给出已接触文明的城市名，`get_target_report` 给出一切。

三处改动，都属于"投递"而不是新的分析：

1. **移动时的 `IN SIGHT`**（`narrate_sight`、`game_state.move_unit`）：每一次成功落地的移动现在都会报告该单位从停下的位置能看到什么——外国城市（带归属者）、蛮族营地、敌方单位——完全不依赖"是否首次揭示"。已揭示但当前不可见的城市会被排除，所以一座记忆中的首都不会每回合重新自我宣布。
2. **发现的那一行带着学说**：城市那一行以 `get_target_report(x,y)` 和要粘进顾问简报的 `prompts/tactics/07-pre-war-analysis.md` 结尾；营地那一行点名 `tactics/07` 的营地闸门。这两次后续调用与"看见"同行抵达，这是对 G1 的"学说从不抵达"最便宜的修复。
3. **`end_turn` 里的 `NEW TARGET`**：一座外国城市第一次可见的那一回合，它会在结果里被点名，带上归属者、人口、是否原始首都以及战争状态，外加同样两次后续调用。这份比较保存在进程内，而且**第一次扫描只用来播种**，所以新会话不会把整张地图宣布一遍。这正是每一次遇见邻居却什么都没说的会话里本该触发的那项检查。

   测试：`tests/test_discovery_delivery.py`（19 项）——IN SIGHT 块的四种情形、扫描新增的两个字段、对九字段旧行的向后兼容、移动集成，以及 `NEW TARGET` 的差分（播种、每座城市只报一次、城市离开又回来后不重复报告）。

**这没有修复的**：顾问仍然读不到行动手册（overlay 不给它任何工具），所以粘贴仍然是编排者的决定——修复之处在于这个决定现在随着"发现"一起到达。G3 与 G4 未受影响。

### 2026-10-01 第二轮：G4 中"宗教单位"这一半

"对于非敌国的宗教单位我们怎么办"这个问题，答案是有学说、没机器。学说：和平时期碰不了它（`attack` → `ERR:NOT_AT_WAR`、`condemn` → `ERR:REQUIRES_WAR`、城市打击 → `NO_ENEMY`），绝不为了传教士单独宣战，不管自家城市被转化，每约 20 回合看 `get_religion_spread` 判断是否真有宗教胜利威胁，并在下一场战争里打它的**信仰来源**。机器：没有——那个单位是隐形的（见下），规则集一句话都没有，而学说自己给出的答案（劫掠圣地）根本没有动词。

- **文档沿用的判据是错的。** 游戏数据里没有 `FORMATION_CLASS_RELIGIOUS`：传教士是 `FORMATION_CLASS_CIVILIAN`、带 `ReligiousStrength="100"`、而且完全没有 `PromotionClass`（使徒 350、审判官 200、上师 200——`Base/Assets/Gameplay/Data/Units.xml`）。威胁扫描按 `Combat > 0 or RangedCombat > 0` 过滤，于是它在任何指标能计数之前就被丢掉了。已在 `AGENTS.md`、其中文备份和本调查中修正。
- **现在能看见它们了**：扫描打印 `RELIGIOUS|` 行（判据 `ReligiousStrength > 0`），`end_turn` 带上一块 `FOREIGN RELIGIOUS UNITS`，逐条点名三格以内的每个单位并说明对应情形的学说，两个计数 `religious_within_3` / `religious_at_war_within_2` 也进了 `_CONTACT_METRIC_KEYS`。战时那一半是一条**暂存**规则（`answer-the-missionary`，在 `prompts/checks/pending/`），因为那个元组是导入期读取的；和平那一半刻意**不成规则**——"忽略它、盯胜利计数"无法表达成 require，而一条无法满足的规则比没有更糟。
- **`pillage` 存在了**（`unit_action(action="pillage")`、`UNITOPERATION_PILLAGE`）：指令从第一版就在要求的动词，也是审计第 10 项。它会先报告地块上有什么，并对四种常见错误分别拒绝（没有移动力、距离太远、此处无可掠夺、已经处于被掠夺状态），并告诉调用者如何验证。
- **和平期的杠杆是地图，不是那个单位**：外国单位不能进入我方占据的地块，没有开放边界则根本进不了我们的领土——所以在中立通道上的传教士可以用站到它前面的方式堵住。这条已写入指令（并附"绝不为此把单位从前线抽走"），因为这是和平时期除监控之外唯一具体的可行手段。

测试：`tests/test_religious_units.py`（18 项）——判据、两个解析器、块的两情形、指标、暂存规则的形状与暂存边界，以及 pillage 动词的操作、诊断与派发。

## 7. 如何重新跑这次调查

```powershell
node .tools/tactics-in-briefs.mjs      # did each playbook reach an advisor brief
node .tools/rule-census.mjs            # which live rules actually fired, and which never have
python .tools/block-census.py          # which end_turn blocks appear, per session
python .tools/audit-md-language.py     # the document/backup state, for completeness
```
