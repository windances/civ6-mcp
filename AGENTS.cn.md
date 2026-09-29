> 本文件是 `AGENTS.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# Civ 6 MCP - Agent 参考手册

一个通过 FireTuner 连接到正在运行的《文明 VI》游戏的 MCP 服务器。你可以读取完整的游戏状态，
并下达指令。所有指令都遵守游戏规则。开一局**新**游戏——文明套件、科研路线、第一个胜利假说——见
`docs/new-game.md`；本参考手册讲的是进行中的游戏循环。用中文给出的人类指令在这里以英文引用；逐字
原文在 `prompts/tasks/tmp/` 下的任务文件里，以及 `docs/task-history.md` 中。

**你只知道你显式查询过的东西。** 人类玩家会被动吸收计分条、宗教滤镜、单位血条——这些你一概没有。
你没有主动询问的信息根本不会进入你的世界模型。下面这些模式的存在就是为了补偿这一点。

## 临时任务就是文件：每回合开始时读 `prompts/tasks/tmp/`

**IN FORCE NOW:** `023-dutch-siege-corps.md`（按人类指令，用现有军队拿下每一座荷兰城池；西线只留一道屏护）以及 `024-take-brussels.md`（take Brussels——由回退到第 218 回合恢复；行动前先重读文件）以及 `025-two-scouts-to-sea-contact.md`（两个侦察兵出海，按人类指令：接触我们还没遇到的文明，且不要被卷入战斗）。

临时指令是**一个文件，而不是本参考手册里的一段话**。本节讲的是处理它们的*流程*：如何拿到它们、
如何读一个任务、如何判断哪些仍在生效，以及细节住在哪里。它既记录任务的内容，也不记录任务的退役
——**文件就是任务**，`prompts/tasks/tmp/current_tasks.md` 是实时登记册，`docs/task-history.md` 是
记录档案。

### 任务如何抵达当前回合

- **把 `prompts/tasks/tmp/` 下的每个 `*.md` 都作为本回合第一步的一部分读一遍**——
  先 `get_game_overview`，再读那个目录——并且每当本回合要做一个任务涉及的决定时就再读一遍。
  不读 `README.md`，不读 `current_tasks.md`，也不读 `done/`。目录为空是正常状态。
- **循环里没有别的东西知道这些文件存在：** 它们不是可检查的规则，不携带任何度量，而 MCP 看不到文件
  系统，所以一个任务文件之所以会被执行，只是因为回合循环去那里看过。**上面那行 `IN FORCE NOW` 就是
  让新到达的文件变得可见的通道**——在一个会话已经在进行时丢进来的文件，只有等该会话重新列出这个目录
  才会被它读到，而任务曾经在无人阅读的状态下放了五个回合，直到那行点名了它们（实测）。改动这一行会把
  整节内容重新注入正在运行的会话，所以**要在添加或退役任务的同一个提交里更新它**——提醒才是传递消息的
  载体；文件承载的是指令。

### 怎么读一个任务

- 每个文件都写明自己的作用域（`scope:`）、它压过什么（`overrides:`）、它可观测的终点
  （`done when:`）和硬性截止（`expires:`），外加 `added:` 表示它来自哪条指令。一个与现行指令相冲突的
  任务由它的 `overrides:` 行来裁定——那一行就是干这个用的，所以不需要猜。
- **一个需要 agent 去争论的 `done when:` 就是一个永远不会退役的任务。** 要求它点名游戏能被查询到的
  东西：一个地块、一个计数、一个度量或一个回合。
  `tests/test_temp_tasks.py` 要求每个任务文件都具备全部五个头部行、一个可观测的
  `done when:`，以及一个点名了回合的 `expires:`。
- **`expires:` 必须是可达的**——当终点线需要生产力时，按队列里的回合数来数，而不是按其他任务的日历
  来数。
- 对于一个**确实**可机械检查的任务，优先改用 `prompts/checks/turn-checks.md` 里的 `once: true` 目标：
  引擎会在它被满足的那一回合自行让它退役（它会打印 `CHECK ACHIEVED ... retired` 并删除该块）。文件
  是留给没有任何度量能表达的东西的。

### 哪些任务正在生效

- **正在生效的就是目录列表本身。** 存在的文件就是一条生效的指令；不存在的文件就是一个不再存在的
  任务。`prompts/tasks/tmp/done/` 存放已退役的任务，其文件名带上回合号
  （`...-done-T<turn>.md`、`...-expired-T<turn>.md`）。
- **一个任务何时结束写在它自己的 `done when:` 和 `expires:` 行里**——二者之一成立的那一回合它就完成
  了，不是读到它的时候，也不是因为本节这么说。
- `prompts/tasks/tmp/current_tasks.md` 是实时登记册：每个生效任务一行，带上它的 `expires:`，这样当前
  工作的形状一眼可见。它是一个索引——**文件才是任务的权威**——而 `docs/task-history.md` 是散文式
  历史，不是指令。

### 细节本身

- **任务文件就是细节。** 它的 `scope:` 和 `overrides:` 界定了它授权做什么，它的编号步骤就是工作
  顺序，它的 `done when:` 是唯一的终点线。
- **在它结束的那一回合让它退役**：把它移到 `done/`，按上面的方式重命名，在同一个提交里更新
  `IN FORCE NOW` 和 `current_tasks.md`，并在日记的 `tooling` 行里记下那个回合。一个被留在原地的过期
  任务就是一条永不退役的指令。
- **机械的那一半是一条命令**：`python scripts/temp-task.py add ...` 会把任务文件、登记册行和这份
  清单一起写好，运行强制的文本闸门和 `tests/test_temp_tasks.py`，并且只在两者都绿时才提交；
  **`--why` 是英文，且不携带任何地块坐标**——它是任务文件里唯一会落进*本*参考手册的部分，所以用文字
  点名目标（"文件点名的那个城邦"），把坐标留在任务文件里、留在属于本局对战状态的地方，而脚本会拒绝
  携带坐标的 `--why`；`... retire <nnn> --done`（或 `--expired`）`--turn N` 会把文件移进 `done/`，
  并重新同步登记册和这份清单；`... status` 打印当前生效的是什么、游戏处在哪个回合，以及三个来源是否
  一致。`scripts\temp-task.cmd`（cmd 和 PowerShell）和 `bash scripts/temp-task.sh`（Git Bash 和任何
  POSIX shell）是同一个命令，只是不带解释器路径。它**不**写的是日记的 `tooling` 行和
  `docs/task-history.md`——那些仍然归你。
- **它还会为每个任务保留一份中文备份**（`--cn`），写进 `prompts/tasks/cn/`，并且**刻意不**写进这个
  目录：回合循环会读 `prompts/tasks/tmp/` 下每个 `*.md`，所以放在任务旁边的备份会被当成第二条指令。
  `--no-cn` 是刻意跳过它，而任务文件会把这个选择记下来。**发布时用的命令也会被记录**：任务文件末尾
  有一段 HTML 注释（退役时再追加一段），方便核查这个文件是怎么来的——这也意味着用同一个 slug 再次
  发布必须加 `--replace`，否则第二次发布会另起一个重复任务，而不是更新你想更新的那个。
- `IN FORCE NOW` 那一行与目录由 `tests/test_temp_tasks.py` 相互核对，所以一次没有记录的退役会变红，
  而不是悄无声息地继续生效。

## 文件编码：含中文的文档要带 UTF-8 BOM

在 zh-CN 机器上，一个看不到 BOM 的编辑器会把文件按代码页 936（GBK）解码，于是对字节本身是合法
UTF-8 的文本显示出乱码。规则是：**含有非 ASCII 字节的文档带 BOM；英文 `.en.` 文件是纯 ASCII，不带
BOM；中文 `.zh.` 文件始终带 BOM。** **本参考手册受英文标准约束**（人类指令 2026-09-27：它只用
英文），所以它是纯 ASCII 且**不**带 BOM——这里出现一个非 ASCII 字符，要么是有人开了个头的翻译，要么
是一个像 em dash 这样的符号，下面那道闸门和 `tests/test_text_encoding.py` 都会因为它而失败。agent
自己的 `write`/`edit` 工具输出的是纯 UTF-8，并且**会悄悄剥掉 BOM**，所以在编辑了 `.zh.` 文件、
`SETUP-WINDOWS.md`、某个战术文件或某个临时任务文件之后，运行：

```
python scripts/fix-text-encoding.py             # put the BOM back, normalise this file's marks
python scripts/fix-text-encoding.py --check     # report only; exit 1 when one is missing
```

**DSH 交给模型的每一份文档都只用英文**（人类指令 2026-09-28）：本参考手册、
`.dsh/skills/civ6-orchestrator/SKILL.md`，以及被 `scripts/use-strategy.ps1` 复制进该技能 DIRECTIVE
块的预设 `prompts/strategies/<name>/directive.md`。这三者都是纯 ASCII 且无 BOM，把它们约束在那里的
就是 `civ_mcp.text_encoding.ASCII_ONLY`，所以 `--check` 会在其中任何一份出现中文行时失败。**当一项
改动带着中文时，把它翻译成英文，并写英文**——这些文件里出现一行中文就是一次失败，而不是一份草稿。
**每一份旁边都有一个中文备份，`<name>.cn.md`**（`AGENTS.cn.md`、`SKILL.cn.md`、
`directive.cn.md`）：它是从英文文件为人类读者生成的，从不被编辑，也从不是来源，而 DSH 无法加载
它——harness 读取的是 `AGENTS.md` / `CLAUDE.md`，而一个技能必须是名字恰为 `SKILL.md` 的文件。
`scripts/set-strategy.ps1 -Text` 出于同样的理由拒绝非 ASCII 输入，而 `tests/test_dsh_documents.py`
会在一行中文上、在一个 DSH 可能加载的备份上，或者在一个缺失的备份上失败。

**这道检查是强制性的，而且它不只是查 BOM**：BOM 说明不了字符是否还是当初有人写下的那些，所以闸门还会
对每个文件 grep 一遍 GBK 往返转换留下的损伤。它在 `git commit` 中运行（`.githooks/pre-commit`，由
`python scripts/install-hooks.py` 每个克隆安装一次），而 `tests/test_text_encoding.py` 运行同一套
检查，所以一份受损的文档会让测试套件变红，而不是抵达某个 prompt。**绝不要通过
`Get-Content | Set-Content` 往返来编辑这些文档**——那正是这道闸门存在要阻止的那一件事。整套机制、修复
工具和豁免清单都在 `SETUP-WINDOWS.md` 里（"the BOM is load-bearing"，第 634 行）。

**一批文档编辑会让两样派生物过期，而两者都是同一条命令：**

```
python scripts/fix-text-encoding.py --check   # the mandatory gate: BOMs + GBK round-trip damage
python .tools/kb.py index                     # the knowledge index
```

索引是*派生*的：对着一份过期的索引查询，它会自信地拿已经不存在的文本作答。

## 坐标系

**六边形网格：(X, Y)，其中 Y 越大 = 视觉上越靠南。**
- Y 增大 -> 南（下）。Y 减小 -> 北（上）。
- X 增大 -> 东。X 减小 -> 西。
- 从 (9,24) 移动到 (9,26) 是**向南**，不是向北。

## 回合循环

每回合按顺序：
1. `get_game_overview`——回合、产出、科研、分数、时代分数、难度。它每回合还携带一次
   **TURN START** 简报：`prompts/checks/turn-checks.md` 中正在失败的规则、每条已经失败了多少个回合、
   上一回合实际买到了什么、把你自己的计划引用回来，以及一个裁定。要在做计划**之前**读它——如果它说
   计划没有被执行，就在本回合改一件事，并在日记里说明它落在哪个回合。**然后读临时任务：
   `prompts/tasks/tmp/` 下的每一个 `*.md`**（不是 `README.md`，不是 `current_tasks.md`，不是
   `done/`）——那些文件是生效的指令，循环里没有别的东西知道它们存在，而每一个都带有自己的
   `done when:` 和 `expires:`，好让你能把它退役并说明。如果是在上下文压缩之后恢复，先调用
   `get_diary`。
2. `get_units`——位置、HP、移动力、充能、附近的威胁
3. 在城池/单位周围 `get_map_area`——地形、资源、敌方单位
4. 移动/操作每个单位。**在集合体的第一次移动之前，写下集结计划**（人类指令 2026-09-26：在第一次移动
   之前规划集合——纵队不能堵死，各单位移动力不同，在找到最佳计划之前什么都不动）：
   每个单位一行——它现在在哪里、它的移动力上限、它要去的那一个地块、`get_pathing_estimate` 的代价、
   它抵达的回合、它的角色，以及它能否从那里开火。
   **`get_staging_plan(city_x, city_y)` 会为你构建那张表**，用的是游戏自己的寻路：区分开的地块、
   被点名的冲突，以及突击开始的回合。三条集结规则——绝不让两个单位占同一个地块、点名走廊、先填
   **最后**一个开火位——是 `prompts/tactics/04-staging-out-of-range.md` 第 3b 步。**同样的三个阶段
   ——分析（`tactics/07`）、集结（`tactics/04` + 这个工具）、执行（`tactics/05`/`06`）——在每一座
   敌方城池和每一个蛮族营地上都要跑**（人类指令 2026-09-26），所以传**营地**的地块就跟你传城池的地块
   完全一样：环形与任务分配是一样的，回复会说 `STAGING PLAN
   for the camp at x,y` 和 `WALK-IN OPENS`，而且没有补给线要切断。
5. `get_cities`——队列、成长、被掠夺的区域
6. 如果要放置新区域，就用 `get_district_advisor`
7. 如有需要，`set_city_production` / `set_research`
8. 到点就跑**战略检查点**
9. `end_turn`——它会在**每一个**回合评估 `prompts/checks/turn-checks.md`，并打印每一条失败的规则
   （`CHECK FAILED [id] ... (require: ...)`）；一条 `once: true` 规则是一个会自行退役的目标，而一个
   已达成的目标会在带时间戳的副本送进 `prompts/checks/archive/` 之后从文件中剪除。补上缺口，或者在
   日记里记下为什么接受它——无论哪种方式，它都不能无人注意地过去。同一个结果还携带决定一场战斗的那些
   块——`SIEGE POSTURE`（以 `SIEGE FIRE: n/m` 结尾）、`BATTLE ASSESSMENT`、`SIEGE PROGRESS`、
   `TAKE THE CITY`、`LOYALTY WARNING`、`UPGRADE AVAILABLE`、`UNUSED ATTACK`——外加每回合的
   **帝国警告**（忠诚危机、闲置贸易路线、金币赤字、资源上限、排行榜位置、军力失衡）——而且它们每一个
   都挂着一条规则。**每个块意味着什么、是哪个度量产生了它，见 `docs/turn-result-blocks.md`**；在对
   一个你没见过的块采取行动之前先读那份文档。
   **战略指令是每次变更投递一次，而不是每回合一次**——`take_update()` 在指令未变时什么也不返回，而它
   会在一个进程里的第一次调用时上报，以覆盖过期的技能加载。在一次 `end_turn` 结果里看到它，并不证明它
   会重复；按它会重复来预算上下文，会把一次长跑的成本高估一个数量级。由此推出给旁观会话的人的规则：
   **会话正在游玩时，不要改写技能的 DIRECTIVE 块**——改动会落进它下一次的 `end_turn` 结果。

## 查资料：`search_knowledge`

你只知道你查询过的东西，而决定一个回合的部分内容是文档，不是游戏状态——城池如何治疗、支援单位可以做
什么、学说对掩护是怎么说的。`search_knowledge(query, k=5, doc=None)` 搜索一个本地索引，覆盖**游戏
手册**、**指令与规则文件**、`AGENTS.md`、`SETUP-WINDOWS.md` 和回顾文档，并给出源路径、行号范围以及
一段高亮摘录。要读那些行（并引用它们），而不是凭记忆转述：

```
search_knowledge("city heals supply line zone of control")
search_knowledge("what can a battering ram do", doc="manual")
search_knowledge("<a Chinese phrase>", doc="manual")   # a CJK query falls back to substring match
```

用 `python .tools/kb.py index` 构建或刷新索引（它是按检出目录的，语料变化之后就会过期）。默认语料是
`prompts/`、`docs/`、`AGENTS.md`、`SETUP-WINDOWS.md` **以及提取出来的手册**
`.tools/manuals/manual.clean.txt`——`--source` 是**替换**那个列表而不是往里追加，所以手工只传一个
来源会构建出一个丢掉了其余全部的索引（实测 2026-09-26：一次不带 `--source` 的重建悄悄丢掉了手册，
100 份文档而不是 104 份，手册完全不在里面）。当一个机制存疑时，这比猜更便宜也更诚实——而且手册与学说
冲突时以手册为准，因为学说永远只是它的摘要。**手册没有覆盖的机制由游戏自己的文件来回答**，而不是靠
记忆：游戏安装目录的 `Base/Assets/Gameplay/Data/*.xml` 和 `Base/Assets/Text/en_US/*.xml` 携带权威
裁定（`UNITCOMMAND_CONDEMN_HERETIC` 及其
`LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION` 就是在那里找到的）。

## 日记

日记是你跨会话的持久记忆。当上下文压缩、或者你回到一局游戏时，`get_diary` 是你重建自己曾在哪里、以及
为什么做那些决定的方式。带具体细节的条目——单位名字、坐标、产出数字、推理——对你未来的自己远比对简短
的总结有用。

反思是在 AI 处理开始**之前**记录的——写下你本回合观察到和做了什么。任何在 `end_turn` 之后才浮现的
东西（一份外交提议、AI 单位进入你的领土、回合结果里的事件）属于**下一个**回合的日记，不属于这一个
回合。

每回合五个反思字段（全部必填、不得为空）：
- **tactical**：发生了什么——具体的单位、地块、结果。
- **strategic**：与对手的相对态势——产出、城池数量、带数字的胜利路线可行性。
- **tooling**：观察到的工具问题，或 "No issues"。
- **planning**：接下来 5-10 个回合的具体行动——具体的建造、移动、科研目标，附带回合估计。
- **hypothesis**：具体预测——进攻时机、里程碑回合、最大的风险。

## 战略检查点

值得定期做的周期性检查。这些东西大部分游戏不会主动呈现。

### 大约每 10 回合：
- **`end_turn` 结果携带一份 `10-TURN REVIEW`**，开战期间还有一条 `WAR ECONOMY` 行：读一读这个窗口
  实际买到了什么，并**在该回合的日记里回答它的三个问题**——这个窗口是否高效，要带数字；下一个目标的
  前置条件哪一个已就位、哪一个还缺；计划中的完成回合是否仍然成立，如果不成立，有什么要变。那些块各自
  度量的是什么，见 `docs/turn-result-blocks.md`。
- `get_empire_resources`——未开发的奢侈品和附近的战略资源
- 盈余奢侈品：超过 1 份的重复份提供零宜居度收益。通过 `propose_trade` 把它们换成 GPT、战略资源，或你
  不拥有的奢侈品类型（每多一种新类型 = 给 4 座城池 +1 宜居度）。即使每份盈余奢侈品只换 5 GPT，
  30 个回合下来也很可观。发之前先用 `mode="test"` 探一下 AI 会接受什么。
- 金币/信仰余额：如果任一在没有任何计划的情况下累积，就把它花掉——`purchase_item`、`purchase_tile`、
  `patronize_great_person`
- 城池数量对游戏时间——如果扩张落后，开拓者往往是最具杠杆的生产选择
- `get_trade_routes`——检查闲置路线；闲置路线是白白没收的免费产出
- 政体层级——新层级解锁时 `change_government`（第一次免费）
- 时代分数对阈值——在 `get_game_overview` 中显示；黑暗时代可以恢复，但代价高昂
- 伟人——`get_great_people`；对手会招募你没招募的

### 大约每 20 回合：
- `get_diplomacy`——向新文明派代表团、与友好文明建交、符合条件时结盟
- `get_victory_progress`——检查全部 6 种胜利类型，不只是你自己的路线
- `get_religion_spread`——不主动检查的话宗教胜利是隐形的；一个在多数文明里占多数的对手是严重威胁

### 大约每 30 回合：
- `get_strategic_map`——每座城池的迷雾 + 无人认领的资源
- `get_global_settle_advisor`——剩余最好的建城点
- 奇观扫描：在你这座最好的城池里 `get_city_production`——与你的胜利路线契合的奇观值得考虑
- 胜利路线检查：你选的路线还可行吗？有没有对手接近赢下某个你一直没在追踪的东西？
- 文明套件检查：你在建造/使用你的特色单位、建筑或改良设施吗？如果没有，那你就是在玩一个通用文明，
  白白放弃你的结构性优势。特色单位往往需要一项特定的科技——如果那项科技不在你当前的科研路线上，
  那是个问题。

## 军事战术，按决策划分

`prompts/tactics/` 里有八个文件，每个决策一个，是给顾问写的（文件 1-7 给 `military-map`，文件 8 给
`economy-cities`；它们的 prompt 会说明何时该读哪一个）。在临场发挥之前读匹配的那一个：

| 文件 | 它决定什么 |
|---|---|
| `tactics/01-unit-production.md` | 单位生产——突击编制、先造什么、买什么 |
| `tactics/02-contact-on-discovery.md` | 发现即接触——评估、克制单位、集结或绕过 |
| `tactics/03-under-attack.md` | 遭到攻击——评估、集结、歼灭；以及撤退的那几种情形 |
| `tactics/04-staging-out-of-range.md` | 在敌方射程外集结——集结点选择、行军途中接触、何时推进 |
| `tactics/05-formation-and-screening.md` | 阵型与掩护——掩护在前，攻城单位在后、距离 2 |
| `tactics/06-assault-composition-and-fire.md` | 突击编成与开火——工作顺序、集中、何时脱战 |
| `tactics/07-pre-war-analysis.md` | 战前分析——我们打不打得起、打谁、多少个回合、代价多少、能不能守住；**蛮族营地也是目标**（营地闸门：CAMP/GUARD/FORCE/GROUND/WORTH/HOLD/GO） |
| `tactics/08-war-and-the-home-front.md` | 战争与大后方——一座战争城池，其余一切复利增长；每回合金币对 +10 的地板 |

**开战之前，文件 7 排第一，而它自己的第一步是侦察**——闸门 0 是"一座候选城池确实可见"。一支形状正确、
但敌方城池全在迷雾里的军队没有什么战前分析可做；先派侦察兵和最快的骑兵，然后再跑闸门。**文件 7 有两类
目标**：敌方城池（一场战争）和蛮族营地（一次突袭——营地是同一套分析的目标，只是用六道营地闸门代替城池
的五道）。

## 战略模式

**接口事实和实测的陷阱，不是学说。** 战略是指令文件，由 orchestrator 技能每次会话加载；按决策划分的
playbook 是 `prompts/tactics/`，由顾问 prompt 携带。这里该放的是工具做了哪些显而易见读法会搞错的事；
当某个话题另有归属时，本节会指过去，然后停下。

### 移动平民
在一个建造者、开拓者或商人的目的地周围做 `get_map_area`（半径 2）值得这一查：平民的战斗强度为零，
损失一个的代价是 5-7 个回合的生产外加它的充能。**有两种拒绝看起来像工具故障，但不是**（实测
T92-T93）：**没有 `TECH_SHIPBUILDING` 时陆军单位无法登船**（"water tile - land units need
Shipbuilding tech to embark"），所以一道海峡不可通行，而一张"黑掉的地图"可能只是海洋；以及一块由
**城邦拥有的地块拒绝了我们的侦察兵，而 `get_city_states` 把我们列为它的宗主国、有 5 个使节**，所以
要绕开它，而不是假定宗主权授予通行权。丘陵、森林和丛林各消耗 2 点移动力并且叠加（森林-丘陵 3+），
所以一个 2 移动力的平民落在森林-丘陵上时，要到下个回合才能行动。
`get_pathing_estimate(unit_id, target_x, target_y)` 使用的是游戏自己的寻路。

### 建造者
`get_builder_tasks` 列出每一块需要工作的地块，按优先级排序（URGENT > HIGH > NORMAL），并为每一块给出
最近的闲置建造者：每回合调用一次，从上往下派活。3-4 个地块外的建造者也值得走这一趟，而地图地块会打印
移动力消耗（`[mv:2]`、`[mv:3]`）和道路，所以沿着它们走。

### 成长与建城
这些阈值，是硬性停摆而不是警告：**food surplus <= 0** 值得本回合就修（农场、粮仓、国内贸易路线、
`set_city_focus(city_id, "FOOD")`），而**turns-to-growth > 15** 说明这座城池需要食物基础设施；
**`housing - pop <= 1`** 会让一座城池停摆几十个回合，所以现在就修，或者把下一座城建在淡水边；一块
忠诚度为负的建城点需要在它建立的那一回合 `assign_governor` 或派一支驻军，否则它会翻过去。

### 探索
你没见过的东西，你既无法定居也无法反制。一个设为 `automate` 的侦察兵让信息流保持流动，而早点补上一个
损失掉的侦察兵，比盲着过的那些回合更便宜。

### 宣战
战争在外交上立即生效，但**战斗引擎要到下一个回合才同步**：在第 N 回合宣战，那一回合布置位置，在 N+1
回合进攻。当进攻在宣战回合回答 `NO_ENEMY` 时，不要重载或重试。

### 战时
有城墙的城池可以射击 2 格内的敌人（`city_action(city_id, "attack", target_x,
target_y)`）——实测
43 点伤害、无反击，这是帝国里最便宜的伤害——而被攻占的城池要用 `city_action`（`keep`、`raze`、
`liberate_founder`、`liberate_previous`）来处理，否则回合不会结束。**和平是指令文件的事，不是本参考
手册的事**：它彻底禁止 `propose_peace`，而每一份到来的提议都被拒绝，所以在那套战略下，一场战争只有当
它的城池归你时才结束。

### 军事准备
`get_diplomacy` 携带对手的军力，而一个实力是你两倍、既不是朋友也不是盟友的邻居，是值得追踪的风险。
落后于自己层级的单位会输掉本来能赢的战斗——`upgrade_unit` 需要科技、资源和金币。开战期间的驻军是规则
`one-garrison-per-city`；和平时期的常备军是指令文件的决定。

### 蛮族营地——学说没有覆盖的那一半
营地学说是技能的和 `tactics/07` 的：六道闸门 C1-C6、"no HP, no walls, no garrison bonus, one
military unit moving onto its tile destroys it"、Spearmen 是反骑兵的，以及在突袭之前转化一个相邻
的蛮族。只有工具相关的内容在这里。

- **每次都要从地图上定位营地。** 营地可能被别人清掉并在附近重生，而从旧日记里抄来的坐标已经错过一次
  （实测：一条日记记录和下一次地图读取把它放在不同的地块上——案例是
  `prompts/tasks/tmp/done/001-clear-the-camp-done-T84.md`）。
- **突袭有一个单命令入口：** `scripts\run-dsh-headless.ps1 -TaskFile
  prompts\tasks\clear-the-camp.zh.txt`（英文：`clear-the-camp.en.txt`）——一次突袭从头跑到尾，不宣战，
  也不改变发展计划。
- **营地对规则是可见的。** `end_turn` 从 `get_map_area` 计算 `camps_within_3`（营地就是地块改良设施
  `IMPROVEMENT_BARBARIAN_CAMP`，所以不需要新的 Lua），而 `answer-the-camp` 已在
  `prompts/checks/turn-checks.md` 中生效。**一条点名了运行中的服务器并不计算的度量的规则，每回合都会
  报 `un-evaluable`，没人能满足它**，这就是为什么新规则会先暂存在 `prompts/checks/pending/`，直到有
  服务器在计算它的度量。
- 报告 `CAMP / GUARD / FORCE / GROUND / WORTH / HOLD / CONVERT / GO`，并在突袭**之前**报告一个可
  转化的蛮族——一个紧挨着我们近战单位的——好让人类能从游戏 UI 里使用领袖能力（Three-Six Stratagems）。

### 宗教——没有任何度量能看到的那一个事实
一个宗教单位是 `FORMATION_CLASS_RELIGIOUS` 且 `Combat = 0`，所以**每一个接触度量和每一条规则对它都是
盲的，`get_map_area` 里该地块的单位列表是唯一的探测器**。对它们的战略是指令文件的
（`prompts/strategies/china-conquest/directive.md`）：和平时期根本碰不了它（`condemn` 回答
`ERR:REQUIRES_WAR`，`attack` 回答 `ERR:NOT_AT_WAR`，城池打击返回 `NO_ENEMY`），所以改为在源头打击信仰
收入。`get_religion_spread` 的节奏在下面的**战略检查点**里。

## 战斗速查

- 远程攻击不受伤害；近战攻击会受到伤害
- 森林/山脉阻挡远程视线——视线被挡的目标会从 `get_units` 的攻击列表中被过滤掉
- 设防单位：+4 防御，每回合治疗
- 战斗估算包含晋升的战斗强度加成、夹击（防御者每有一个相邻友军 +2）、支援（防御者每有一个相邻友军
  +2），以及森林/丛林防御（+3）

## 单位行动参考

| 行动 | 效果 | 备注 |
|--------|--------|-------|
| `move` | 移动到地块 | 需要 target_x、target_y |
| `attack` | 攻击敌人 | 显示伤害估算；近战/远程自动检测。**攻城单位（Catapult/Trebuchet/Bombard）不能攻击单位**——它只攻击城池和区域，要求它打一个单位会返回 `ERR:SIEGE_CANNOT_ATTACK_UNITS`；对单位请用远程单位（Crossbowman）。 |
| `condemn` | 摧毁一个相邻的敌方宗教单位（Condemn Heretic） | 一个游戏**命令**，不是攻击（`unit_action(action="condemn")`）；引擎会挑选相邻的 Missionary/Apostle/Inquisitor，所以回复会先点名每一个候选。**游戏要求宣战**（`LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION`），所以朋友的传教士谁也不能谴责——和平时期的目标会返回 `ERR:REQUIRES_WAR`。为任务 008 于 2026-09-26 加入。 |
| `fortify` | +4 防御，治疗 | 仅限军事单位 |
| `heal` | 设防直到满 HP | 满 HP 时自动唤醒 |
| `alert` | 睡眠，遇敌唤醒 | 哨戒用途 |
| `skip` | 结束单位的回合 | 总是有效 |
| `automate` | 自动探索 | 仅限侦察兵 |
| `delete` | 解散单位 | 移除维护费 |
| `found_city` | 建城 | 仅限开拓者 |
| `improve` | 建造改良设施 | 建造者和军事工程师；见下面的改良设施 |
| `remove_feature` | 砍伐/收获地貌 | 仅限建造者；从地块移除森林、丛林或沼泽 |
| `build_route` | 修筑道路/铁路 | 仅限军事工程师；在当前地块上；不使用充能 |
| `trade_route` | 开始路线 | 商人；目的地城池的 target_x/y |
| `teleport` | 移动闲置商人 | 仅限商人；城池的 target_x/y |
| `activate` | 使用伟人 | 必须位于已建成的匹配区域上 |
| `spread_religion` | 传播宗教 | Missionaries/Apostles |

常用改良设施：`IMPROVEMENT_FARM`、`IMPROVEMENT_MINE`、`IMPROVEMENT_QUARRY`、
`IMPROVEMENT_PLANTATION`、`IMPROVEMENT_PASTURE`、`IMPROVEMENT_CAMP`、`IMPROVEMENT_FISHING_BOATS`、
`IMPROVEMENT_LUMBER_MILL`

地貌移除：森林、丛林和沼泽地块阻挡大多数改良设施（例如农场）。先用 `remove_feature` 砍伐/收获地貌，
再用 `improve` 建造。伐木场和营地在森林/丛林上工作无需移除。检查 `get_units` 输出里的
`valid_improvements`——如果一块你预期有 FARM 的地块上没有列出它，该地块很可能有一个阻挡性的地貌。

建造者修理地块改良设施。被掠夺的**区域建筑**（Workshop、Arena 等）通过 `set_city_production`
修理。

`get_cities` 按城池显示未改良的资源地块和被掠夺的改良设施/区域——用它来给建造者工作排优先级，不必手工
扫描 `get_map_area`。

军事工程师（需要 Encampment + Armory）：`build_route` 在当前地块上修筑铁路（不消耗充能；每格花费
1 Iron + 1 Coal）。`improve` 配合 `IMPROVEMENT_FORT` 或 `IMPROVEMENT_AIRSTRIP` 会使用充能。修筑
铁路消耗全部移动力——每个工程师每回合一格。

| 其他单位工具 | |
|--------|--------|
| `skip_remaining_units` | 跳过所有还有剩余移动力的单位（外交之后有用）。**只要有任何一个单位还有合法攻击，它就拒绝并点名那些单位**——传 `force=True` 来有意放弃它们 |
| `upgrade_unit(unit_id)` | 升级到下一类型（需要科技 + 资源 + 金币） |

## 结束回合的阻塞项

`end_turn` 在推进之前解决阻塞项。如果它返回一个阻塞项：
- **单位**：未移动的单位需要指令（move / skip / fortify）
- **生产**：城池队列为空——设置新的生产
- **科研/市政**：已完成——选择下一个
- **总督**：有点数可用——`get_governors` -> `appoint_governor` /
  `assign_governor(governor_type, city_id)` / `promote_governor(governor_type, promotion_type)`
- **晋升**：单位有 XP——`get_unit_promotions` -> `promote_unit`。**一次晋升消耗该单位的整个回合**
  （手册，`EXPENDING XPS`，`manual:704-713`），所以在它已经攻击之后晋升，或者在它不在射程内、或在
  治疗时晋升——绝不要用晋升代替一次攻击。让它匹配任务：攻坚的近战单位要反驻军/伤害那条线，远程单位要
  远程强度那条线。
- **政策槽位**：空——`get_policies` -> `set_policies`
- **万神殿/宗教**：达到信仰阈值——`get_pantheon_beliefs` -> `choose_pantheon`；创教用：
  `get_religion_beliefs` -> `found_religion`
- **使节**：有代币可用——`get_city_states` -> `send_envoy`
- **奉献**：新纪元——`get_dedications` -> `choose_dedication`
- **城池占领**：被征服或忠诚度不足的城池——
  `city_action(city_id, "keep"/"raze"/"liberate_founder"/"liberate_previous")`
- 移动回复显示的是**目标地块**，不是抵达位置（异步寻路）。**一次报告 `STOPPED_SHORT` 或
  `STOPPED_MID_PATH` 的移动或攻击可能已经生效**——实测 T141，一个 Horseman 的攻击报告"无法抵达
  目标"，而目标被留在了 26 HP。在重新下达任何报告了短距离或部分移动的指令之前，用 `get_units` 重读
  一遍。
- **战斗后的城池读取是估算，不是事实**（实测）。结果行可能报告 `read unchanged`，或者池子没动，
  **而伤害已经打进去了**——包括打下城池的那一击。从 `SIEGE PROGRESS` 块、以及*更晚*的一次读取来判断
  进展，绝不从即时回复判断——也不要从一个过期的数字得出攻击毫无作用的结论。案例记录是
  `docs/retrospectives/2026-09-27-thebes-alexandria-T194-T218.md`。
- **一个不肯推进的回合通常是在等一个答复，不是在等一个弹窗。** 当一个 AI 外交会话或一份到来的贸易协议
  打开时，`end_turn` 会回答 `Turn paused ...`，而这两者都归你处理：先 `get_pending_diplomacy` 再
  `respond_to_diplomacy`，先 `get_pending_trades` 再 `respond_to_trade`。只有在那两个都返回空之后才
  去用 `dismiss_popup`。它清掉弹窗层——奇观、时代、加速和灾难画面、一个领袖场景、一个还在跑的过场
  摄像机——并且会回答 `PENDING|DiplomacyActionView` 或 `PENDING|DiplomacyDealView`，而不是关闭其中
  任何一个，因为从 Lua 关闭一个会话会让回合处理挂起，而关闭一个协议视图会悄悄拒绝一份你从未看过的提议。
  大多数弹窗根本不需要这个调用：一个后台观察者会在非关键弹窗出现约一秒后把它们关掉，Windows 崩溃
  对话框也会替你点掉。**Lua 里没有任何东西能看到游戏之外的对话框**——如果 `dismiss_popup` 什么也没
  报告而回合仍然卡住，在断定游戏挂死之前用 `.tools/whats-on-screen.py` 读一下屏幕
  （`docs/game-recovery.md`）。

## 外交

**被动（AI 发起）：** AI 接触会阻塞回合推进。用 `get_pending_diplomacy` 检查是否有打开的会话，然后
`respond_to_diplomacy`（POSITIVE/NEGATIVE，2-3 轮）。外交会话不影响单位移动或指令——之后照常继续指挥
单位。

**主动：**
- `send_diplomatic_action(action="DIPLOMATIC_DELEGATION")`——25g，首次见面时值得送出
- `send_diplomatic_action(action="DECLARE_FRIENDSHIP")`——需要 Friendly 状态
- `send_diplomatic_action(action="RESIDENT_EMBASSY")`——需要 Writing 科技
- `form_alliance(player_id, type)`——类型：MILITARY/RESEARCH/CULTURAL/ECONOMIC/RELIGIOUS；需要
  30t 友谊 + Diplomatic Service 市政
- `propose_trade(player_id, ...)`——交易金币/GPT/资源/影响力/开放边境/城池。先用 `mode="test"` 看
  AI 的还价而不作承诺，再用 `mode="send"` 敲定。城池用 `get_trade_options` 里的 `city_id`。
- `propose_peace(player_id)`——白色和平；需要 10t 战争冷却。**指令文件禁止它**：永不调用，并拒绝
  每一份提议，无论它是以贸易还是以会话的形式到来
- `get_trade_options(other_player_id)`——看一个文明有什么可供交易（金币、资源、影响力、城池、协议）
- `get_pending_trades`——检查到来的贸易提议；`respond_to_trade(player_id, accept)` 来接受/拒绝
- 宣战前在 `get_diplomacy` 里检查防御协定
- `get_diplomacy` 显示领袖议程——历史议程始终可见；随机议程需要秘密外交可见度（间谍进驻其首都或
  结盟）。用议程预测 AI 行为并避免关系惩罚。

**间谍活动：** `get_spies` -> `spy_action(spy_id, action, ...)`。行动：先 `travel` 到一座城池，然后
执行任务（窃取科技、让总督失效等）。进攻性任务只有在间谍抵达之后才有效。

**城邦：** `get_city_states` -> `send_envoy`。宗主权 = +1 影响力/回合。类型：
Scientific/Industrial/Trade/Cultural/Religious/Militaristic。

**外交影响力：** 来自政体层级（基础 +1，随层级缩放）、同盟（每级 +1/t）、宗主权（+1/t）。在世界议会
里花掉以换外交胜利点数；在没有即将召开的议会时，超过约 100 的影响力与其存着，不如用在一笔交易里。

## 生产与科研

奇观——高生产的城池可以把它们插在基础设施之间。用 `get_wonder_advisor(city_id, wonder_name)` 选
位置，然后用 `set_city_production` 指定 target_x/y。科学：Great Library、Oxford University、
Kilwa Kisiwani。文化：Chichen Itza、Forbidden City。通用：Ancestral Hall、Pyramids。

**科研：** `get_tech_civics` 按回合数升序排序；还有 2 个回合或更少的条目会被标上 `!! GRAB THIS`
——便宜且已被加速的科技很容易错过，而它们能解锁整条生产链。

**购买：** `purchase_item(city_id, item_type, item_name)`——用金币（默认）或信仰
（`yield_type="YIELD_FAITH"`）立即购买单位或建筑。`get_city_production` 显示可购买的条目和花费。

**地块：** `get_purchasable_tiles(city_id)` -> `purchase_tile(city_id, x, y)`——用金币买边境地块，
以获取战略资源或放置区域。

## 区域放置

用 `get_district_advisor(city_id, district_type)` 获取排名后的地块。然后用 `set_city_production`
指定 target_x/y。

| 区域 | 相邻加成 |
|----------|------------------|
| Campus | 每座山脉 +1，每 2 片丛林 +1，地热/礁石 +2 |
| Holy Site | 每座山脉 +1，每 2 片森林 +1，自然奇观 +2 |
| Industrial Zone | 每个矿场/采石场 +1，水渠 +2 |
| Commercial Hub | 相邻河流 +2，港口 +2 |
| Theater Square | 每个奇观 +1，娱乐中心 +2 |
| Encampment | 不能与城池中心相邻 |

## 贸易路线

- `get_trade_routes`——查看所有进行中的路线和闲置的商人
- `get_trade_destinations(unit_id)` -> 可用的目的地
- `unit_action(action='trade_route', target_x, target_y)` -> 开始路线
- 国内路线：给新城池送食物 + 生产。国际路线：金币。
- 容量：来自 Foreign Trade 市政 1 条，每个 Market/Lighthouse +1
- 闲置路线是白白没收的免费产出

## 伟人

- `get_great_people`——候选人、招募进度和花费
- `recruit_great_person(individual_id)`——用累积的伟人点数招募（检查 `[CAN RECRUIT]`）
- `patronize_great_person(individual_id)`——用金币或信仰立即买下
- `reject_great_person(individual_id)`——放弃，推进到该类别里的下一个候选人
- 对手会招募你放弃的——尽快招募往往是值得的
- **Great General 和 Great Admiral 是"激活"这条规则的例外。** 光环才是他们的价值所在：给射程内的
  陆军单位 +5 战斗强度和 +1 移动力（Great Admiral 给海军单位），**在该单位存活期间被动提供**。
  `activate` 是一次*退役*——它消耗掉这个单位并一次性兑现。
  `get_great_people` 会把两者都打印出来：让将军跟着军队，不要激活它，除非那笔一次性的兑现正是你真正
  想要的。在一个 Great General 被招募的那一回合就激活它，等于把光环在剩下的整局游戏里扔掉。
- 对于其他每一个类别，把伟人移到它匹配的、已建成的区域上，然后
  `unit_action(action='activate')`
- 如果激活失败，错误信息里会包含要求（区域类型、需要的建筑）
- 不要删除伟人——它们显示 0 建造者充能，但那是另一套系统；它们在被激活之前不会被消耗（Great General
  或 Great Admiral 除外，激活会让它们退役）

## 世界议会

WC 在 `end_turn()` 内部同步触发——要在调用 end_turn **之前**登记选票。

**投票流程：**
1. `get_world_congress()`——当 `turns_until_next = 0` 时，WC 在本回合触发
2. 审阅决议（选项 A/B、目标列表、影响力花费）
3. `queue_wc_votes(votes='[{"hash": H, "option": 1, "target": 0, "votes": N}]')`
4. `end_turn()`——处理器触发，选票部署，回合推进

- `hash`：来自 `get_world_congress`；`option`：1=A / 2=B；`target`：player_id 在运行时解析为列表
  下标；`votes`：最多花多少
- 每项决议 1 张免费票（不花任何东西——值得投出）
- **如果你一张票都不登记，`end_turn` 会替你投出免费票**——每项决议一张，0 影响力，选项和目标按
  决议逐项从游戏自己的决议数据里选取（哪一边是禁令、哪一边是增益，以及目标是否应该是你）——而它的结果
  会点名它投了什么。那是一张网，不是一个决定：这个回退有意被限制在免费票上，所以当这次会议重要时自己
  调用 `queue_wc_votes`，因为只有你能给目标排序，也只有超出免费票的那些票才花费影响力。
- 额外选票的花费是 6/18/36/60/90/126... 累积影响力
- 在两次会议之间保留 50-100 影响力作为储备，为下一次会议留出灵活性
- DVP 决议：投票前先读清每个选项实际给的是什么。把影响力集中在单项最有冲击力的决议上，而不是摊薄。
  确认你的票是挡住了对手，而不是不小心帮了他们

## 胜利条件

| 胜利 | 胜利条件 | 通过什么监控 |
|---------|---------------|-------------|
| 科技 | 4 个太空项目完成 | `get_victory_progress` |
| 统治 | 拥有所有对手的原始首都 | `get_diplomacy` 里的军力 |
| 文化 | 外国游客 > 每个文明的国内游客 | `get_victory_progress` 里的旅游业绩 |
| 宗教 | 你的宗教在**所有**文明中占多数 | 定期 `get_religion_spread` |
| 外交 | 20 点外交胜利点数 | 世界议会投票 |
| 分数 | 回合上限时分数最高 | 兜底 |

所有胜利在条件达成时立即触发——它们不会等一个回合边界或一次 WC 会议。一个达到 20 DVP 的对手会在你
下一回合之前获胜。唯一的反制是在世界议会上、*在他们达到 20 之前*削掉 DVP。

`end_turn` 每回合跑一次胜利临近扫描，每 10 回合跑一次完整快照。这些警告是隐形胜利的主要信号——值得
留意。

## 游戏恢复

**在碰任何东西之前先问游戏在哪里：`get_game_status`**——`not_running` / `starting` / `in_game` /
`leader_screen` / `main_menu` / `loading` / `tuner_busy`，外加回合和一个 `NEXT:` 行。要从那次调用
推断状态，绝不从恰好失败的那次调用的措辞去推断。

**同一时间只有一个会话。** FireTuner 只服务一个连接。当另一个会话正在游戏时，`kill_game` 和
`restart_and_load` 会拒绝（它们会点名 pid），而只要那个会话还活着，第二个 MCP 就无法附加上去——等待
改变不了任何事。用 `scripts\civ6-clean.ps1` 停掉它，或者继续在它的会话里玩。

**把这局对战交给一个新会话是一条命令，而且它不是 agent 的命令：**
`scripts\resume-game.ps1`（检查并报告）、`-Wait`（等人类加载完，然后启动）、`-Rollback`、`-DryRun`。
它只读取被动信号，从不启动也从不加载，并根据它刚读到的事实生成该会话的任务。

**其余一切都在 `docs/game-recovery.md`**——那两种恢复陷阱、跨回滚分支的 `0_MCP_NNNN` 文件名冲突、
`AutoSave_NNNN` 偏移、`orient.py`、`turn-of-save.py`、`auto-turns.py`、按名字加载、挂起恢复和存档
列表。在做任何恢复之前读它：它就是以前住在这里、原样搬走的那一节，而且它仍然是权威。
