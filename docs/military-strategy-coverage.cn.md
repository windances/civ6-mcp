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
| **宗教**（谴责异端、杀死传教士、攻击信仰收入） | 指令 | 和平时期 `condemn` 回答 `ERR:REQUIRES_WAR`、`attack` 回答 `ERR:NOT_AT_WAR`（1）；**没有任何指标看得见宗教单位**——它是 `FORMATION_CLASS_RELIGIOUS`，Combat 为 0 | 和平时期 **1**，战时 **5** |
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

**G4——让部分教条无法被强制执行的那些指标盲区。** 宗教单位对每一个指标和规则都是不可见的（Combat 0）；控制区（Zone of Control）对两个寻路工具都是不可见的，所以一份计划可能穿过它做路线，而单位就只是停下来；而计划的抵达回合是从移动力外推出来的，而不是真实的逐格代价。那些领域的教条只能手工遵循，而说明这一点的文件又无法被投递（G1）。

## 6. 如何重新跑这次调查

```powershell
node .tools/tactics-in-briefs.mjs      # did each playbook reach an advisor brief
node .tools/rule-census.mjs            # which live rules actually fired, and which never have
python .tools/block-census.py          # which end_turn blocks appear, per session
python .tools/audit-md-language.py     # the document/backup state, for completeness
```
