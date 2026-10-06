> 本文件是 `problems-and-fixes.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# 问题、起因与解决方案

一份持续追加的日志：出过什么问题、为什么、以及是什么把它关掉的。它的作用是让已经付过代价的故障能在
几秒钟内被认出来，而不是从日志里重新推导；同时让新问题有一个明确的落点。

**如何追加条目——只追加，永不重编号。** 编号是"类别前缀 + 两位数字"：`SL` 会话生命周期，`DM` 分工与
"轮到谁"，`RB` 回退 / 记忆 / 状态，`EN` 编码与文档门禁，`TL` 工具与数据，`PT` 与人类协作。新条目放在
它所属类别的末尾，并在**同一次提交**里补上索引行。每个条目都带同样的四行，写不出来的那一行意味着这件事
还没有被测量过：

- **症状（symptom）**——看到的到底是什么，连同当时屏幕上真实的字符串或数字。
- **起因（cause）**——机制，而不是猜测。猜测属于日记，不属于这里。
- **解决（fix）**——关掉它的那次提交，或者现在承载这条规则的文件与函数。
- **证据（evidence）**——让这个说法可以被别人复核的测量、测试或命令。

## 索引

| 编号 | 一句话 | 状态 |
|---|---|---|
| SL-01 | AI 回合停摆被十分钟的轮询预算藏住，然后靠杀掉游戏来"恢复" | 已关闭 |
| SL-02 | 正在跑的会话没有任何输入通道，"停止"送不进去 | 已关闭 |
| SL-03 | 交接横幅报告的是 run 早就走过的回合 | 已关闭 |
| SL-04 | 一次资格测试把活的心跳覆盖成了桩 | 已关闭 |
| DM-01 | 没有任何东西说明"这个回合还开着的是哪一半" | 已关闭 |
| DM-02 | `UI.CanEndTurn()` 被当成了"回合可以结束" | 已关闭 |
| DM-03 | 第三态带着一句注解，让会话去等一个早已做完的人类 | 已关闭 |
| DM-04 | 两份工作清单都不覆盖的单位从报告里消失了 | 已关闭 |
| DM-05 | 不足一个移动力的单位把报告顶在 `YOUR MOVE` | 已关闭 |
| DM-06 | 分工之下 `skip_remaining_units` 把人类的单位也扫了 | 已关闭 |
| DM-07 | `-HumanMilitary -DryRun -TaskFile <missing>` 死在一条原始 PowerShell 报错上 | 已关闭 |
| RB-01 | 回退游戏之后，分支状态不一致 | 已关闭 |
| RB-02 | 两次回退到同一回合，覆盖了更早分支唯一的存档副本 | 已关闭 |
| RB-03 | `.tools/archive-branch.py` 无法按路径导入 | 已关闭 |
| RB-04 | 没有办法"不带走之前记忆"地从载入位置继续打 | 已关闭 |
| RB-05 | 只删掉达成注释，破坏了规则文件的契约 | 已关闭 |
| RB-06 | 第一版 fresh-start 备份把目录拍平，丢了一段日记 | 已关闭 |
| RB-07 | fresh-start 的测试套件把真实对局清了 | 已关闭 |
| RB-08 | 全新开始仍然带着正在生效的临时任务 | 已关闭 |
| EN-01 | agent 自己的编辑器会把中文文档需要的 BOM 去掉 | 设计如此，未关闭 |
| EN-02 | 英文改动会让它的中文备份过期 | 设计如此，未关闭 |
| EN-03 | AGENTS.md 最多只能引用四个回合，新条目可能把它顶超 | 设计如此，未关闭 |
| EN-04 | 共享的规则文件让一局的退役变成另一局的沉默 | 已关闭 |
| TL-01 | `.tools/sleeping-units.py` 因为少一个导入而崩溃 | 已关闭 |
| TL-02 | `civ6-clean.ps1` 忽略了 `runs/` 下的心跳 | 已关闭 |
| TL-03 | `stop-agent.py` 把请求写进了错误的数据目录 | 已关闭 |
| TL-04 | `GameCore_Tuner/InGame states not found` 通常意味着另一个客户端占着 tuner | 设计如此，未关闭 |
| TL-05 | 一次重载会把整个回合重置 | 设计如此，未关闭 |
| TL-06 | route-A 驱动去数据根目录找 run 清单 | 已关闭 |
| PT-01 | 分工被说了三次，一次比一次窄 | 已关闭 |
| PT-02 | "人类做完了"这个信号需要的是定义，而不是新标记 | 已关闭 |
| PT-03 | 几个五五开的选择属于人类，而每一个都塑造了一件工具 | 已关闭 |

## SL —— 会话生命周期

### SL-01 AI 回合停摆被十分钟的轮询预算藏住，然后靠杀掉游戏来"恢复"

- **症状** 游戏明显停住几分钟之后，`end_turn` 才返回 `HANG:354:0_MCP_0354|End turn requested (turn is
  still 354). AI turn processing appears stuck.`，里面没有任何一句说该做什么；一个晚上出现了两次
  （`22:13:34`、`22:56:21`）。
- **起因** 两个机制叠在一起。轮询预算约 593 秒，所以报告到达时早就违反人类自己的"两分钟"规则；而收到
  `HANG` 时，MCP 会在通知任何人之前最多三次杀掉并重新拉起游戏——于是真到了手上的报告通常是恢复流程
  自己的消息，而不是停摆的。重载还会丢掉当前回合已经做完的工作。
- **解决** `AI_TURN_STALL_REPORT_S = 120.0`，并用 `next_poll_delay()` 把循环修剪到该预算；`HANG`
  消息现在带上等待时长、两分钟规则和出路；kill/relaunch 恢复默认关闭，藏在
  `server.py::_hang_self_restart_enabled()` 后面，`CIV_MCP_HANG_SELF_RESTART=1` 可以恢复它。提交
  `2e836ba`。
- **证据** `tests/test_end_turn_stall_budget.py`（22 项）。实测：下一次停摆在 120 秒时就上报；
  `hang_diagnosis.jsonl` 还显示 `22:56:20` 那次窗口被压在 Chrome 后面，这就是保留"拉回前台重试"的原因。

### SL-02 正在跑的会话没有任何输入通道，"停止"送不进去

- **症状** 没有办法请一个会话停下：`dsh --help` 只有 `web` 和 `plugin`，headless profile 是一次性的，
  而在 Windows 上 `Stop-Process -Force` 就是 `TerminateProcess`，没有可用的 SIGTERM。
- **起因** 会话唯一的入站通道是它的工具结果，而没有任何东西往那里写。
- **解决** `src/civ_mcp/stop_request.py`，加上 `_logged` 给每个成功工具结果追加一行
  `STOP REQUESTED|`，并把 `delivered_at` / `delivered_turn` 盖进 `stop-request.json`；
  `scripts/stop-agent.py` 负责请求、查看、撤回，`--wait N` 兜底执行 `civ6-clean.ps1 -KeepGame`。提交
  `fccfb6a`。
- **证据** `tests/test_stop_request.py`（8 项）；实测 `--note` / `--status` / `--cancel` 往返，顺带
  清掉了 `01:49` 遗留的一条请求。

### SL-03 交接横幅报告的是 run 早就走过的回合

- **症状** 游戏已经站在 T354，会话横幅却一直打印 T288，因为 `run.json` 的 `last_turn` 冻住了。
- **起因** `run_manifest.touch` 只把字段往前推，而常规路径上没有任何东西记录"打过的回合"，于是陈旧值
  永远不会自我纠正。
- **解决** `src/civ_mcp/server.py` 里的 `_record_played_turn()`，由 `_logged` 以及 `end_turn` 推进时
  调用；那个陈旧值（288）曾被手工改成 354。
- **证据** `tests/test_run_manifest.py`；现在交接检查会打印清单与游戏一致的那个回合。

### SL-04 一次资格测试把活的心跳覆盖成了桩

- **症状** `scripts/qualify-mcp.py` 让一个正在打的 `heartbeat.json` 变成 `starting` 阶段，读起来
  和一个新会话一模一样。
- **起因** 子进程继承了 `CIV_MCP_DATA_DIR=<cwd>/.civ6-mcp-data`，于是它把自己的状态写进了活的 run
  目录。
- **解决** 子进程改用临时数据目录。`tests/test_qualify_mcp.py` 把它钉住。
- **证据** `tests/test_qualify_mcp.py`。

## DM —— 分工与"轮到谁"

### DM-01 没有任何东西说明"这个回合还开着的是哪一半"

- **症状** 在 `-HumanMilitary` 之下，会话必须等人类，但唯一的信号是 `ENDTURN_BLOCKING_UNITS` 那条
  目，而它几乎每个回合开头都在，且完全不说明归属。于是会话要么永远等下去，要么调用 `end_turn` 把人类的
  单位扫掉。
- **起因** 划分只存在于任务文本里，没有任何东西从盘面推导它。
- **解决** `src/civ_mcp/agent_half.py`（`is_the_humans`、`can_still_act`、`verdict`、`render`、
  `summary`），由 `get_notifications` 调用：每次调用追加一行 `WHOSE MOVE|`，并把 `agent-half.txt`
  写进心跳文件旁边。提交 `4c0a7e4`，其后由 `c9e67d0`（大海军统帅）与 `fb17eaa`（大科学家与大商人属于
  agent）扩展。
- **证据** `tests/test_agent_half.py`；本日志里引用的活 `agent-half.txt` 报告。

### DM-02 `UI.CanEndTurn()` 被当成了"回合可以结束"

- **症状** 建在 `UI.CanEndTurn()` 上的等待会立刻放行，然后把 `_sweep_unmoved_units` 的"静默设防并跳过"
  交回给你。
- **起因** 这个布尔值的含义是"结束回合按钮可以按"，而它在 units blocker 还在时就是 true——第 337 回合
  实测：连续三次读到 `CANEND|true`，而 `ENDTURN_BLOCKING_UNITS` 仍然挂着。
- **解决** 文档规定的测试改成游戏自己的通知条目；提交 `c1a79fa` 与 `1a304f2`。
- **证据** 第 337 回合的测量，被引用在 `AGENTS.md` 与 `scripts/resume-game.ps1` 追加的任务文本里。

### DM-03 第三态带着一句注解，让会话去等一个早已做完的人类

- **症状** 报告已经写着 `ready to end`，但"能结束不等于人类已经操作过"这句注解让会话继续等，于是回合
  永远不结束。
- **起因** 这句注解是在第三态刚出现时写的，从未与人类对"做完"的定义对齐。
- **解决** 提交 `3fbd1d7`：`ready to end` **就是** human-done 信号，注解删掉。等待要在 `end_turn`
  之前守住，而不是靠"不调用它"。
- **证据** `tests/test_agent_half.py` 断言第三态的文本说明回合可以结束。

### DM-04 两份工作清单都不覆盖的单位从报告里消失了

- **症状** 建造者 `13107256` 站在 `(36,22)` 的古迹地块上，2/2 移动力、2 充能，而且整个 run 里没有
  任何一条命令点名过它；没有任何清单或报告提到它，所以永远没人处理。
- **起因** 对它而言 `can_still_act` 为假，于是"轮到谁"的划分两边都不覆盖；它也不会顶起 units
  blocker。`get_builder_tasks` 还把该地块提议成 `build UNKNOWN`，因为古迹是考古学家的活，不是建造者的。
- **解决** `unclaimed()` 点名这类单位，报告把他们列出来（提交 `c58bde1`）；同时修了 Lua 的建造者任务
  查询，让古迹地块不再产生伪任务。提交 `c58bde1`。
- **证据** `tests/test_agent_half.py`（把那个实测建造者做成 fixture），以及对查询的
  `tests/test_builder_lua` 式检查。

### DM-05 不足一个移动力的单位把报告顶在 `YOUR MOVE`

- **症状** 一辆在 `(20,32)` 的 `UNIT_MECHANIZED_INFANTRY`，`moves 0.2/4`、activity 为空、
  `ready_to_move` 为 true，让报告一直回答 `YOUR MOVE`，而游戏自己的 units blocker 早已落下——会话于是
  在等一个连一格都进不去的单位。
- **起因** `can_still_act` 判的是 `moves_remaining > 0`，而零点几个移动力什么也买不下。
- **解决** `src/civ_mcp/agent_half.py` 里的 `MIN_MOVES_TO_ACT = 1.0`：低于它就判为跳过，
  `can_still_act` 与 `unclaimed` 都这样判。正好 1.0 仍然可以行动。提交 `c3afbbd`。
- **证据** `tests/test_agent_half.py`（含 1.0 边界）以及 `tests/test_wait_for_human.py`——它那条
  "live 十单位读数"现在期望一个都不列。

### DM-06 分工之下 `skip_remaining_units` 把人类的单位也扫了

- **症状** 一个照样调用它的会话（非 force，因为没有任何单位有合法攻击）拿到
  `FORTIFIED|1 fortified, 2 healing; SKIPPED|12`，而那十二个里有两个是人类的。
- **起因** 这个工具是全局的：它把战斗单位设防、把其余全部跳过。`SKILL.md` 说"结束前无条件调用它"，
  而分工活在一个 skill 根本不读的任务文件里。
- **解决** 提交 `bda3293`：`.dsh/skills/civ6-orchestrator/SKILL.md`（+`.cn` 备份）里的例外条款、
  `AGENTS.md` 里的 `skip_remaining_units` 表格行，以及 `scripts/resume-game.ps1` 追加的任务文本里
  明令禁止。
- **证据** 上面那次实测的扫除结果；例外条款由开关契约测试 `tests/test_resume_game_division.py` 钉住。

### DM-07 `-HumanMilitary -DryRun -TaskFile <missing>` 死在一条原始 PowerShell 报错上

- **症状** 从 `Add-DivisionOfLabour` 里抛出 `Select-String : cannot find path '...does-not-exist.txt'`，
  没有任务预览，退出码 1。
- **起因** `$ErrorActionPreference = 'Stop'` 之下，`Select-String` 的非终止错误会变成终止错误；而预览
  路径直接拼接路径、不做检查（启动路径更早一步就在 `Resolve-Path` 处拒绝了）。
- **解决** 提交 `9ca1c9a`：在 marker 检查之前加守卫，拒绝时给出
  `no task file to append the division to: <path> (check -TaskFile / -TaskPath)`，并新增
  `tests/test_resume_game_division.py`（13 项）把开关在两条路径上都钉住。
- **证据** 提交信息里前后各一次运行的引用；以及那 13 项测试。

## RB —— 回退、记忆与状态

### RB-01 回退游戏之后，分支状态不一致

- **症状** 载入更早的存档后，会话仍然带着被放弃的那条分支：已经不存在的回合的日记行、因为 `done when:`
  刚被回退而本不该退役的临时任务、以及人类刚刚丢弃的那条分支上达成的 `once: true` 规则。2026-09-28
  实测：回退到 T218 之后，布鲁塞尔又变回城邦，而 `024-take-brussels` 却还是退役状态。
- **起因** 回退是五件事，而当时只做了"载入游戏"这一件。
- **解决** `scripts/rollback-to-turn.py`：归档未来、切开日记（`.tools/archive-branch.py`）、回滚任务
  （`.tools/rollback-tasks.py`）、恢复该分支退役的规则并在持久目标状态里遗忘它们，然后按游戏当前状态
  正确地重启——再加上 `run_manifest.reset_turn`。
- **证据** `tests/test_rollback_decisions.py`、`tests/test_handoff.py`；以及
  `.civ6-mcp-data/branches/rollback-to-T*-*` 下的归档文件夹。

### RB-02 两次回退到同一回合，覆盖了更早分支唯一的存档副本

- **症状** 2026-09-25 实测：第二次回退到 T99 复用了第一次写的文件夹，并替换了更早分支同名存档的副本，
  而那是它们仅存的副本。
- **起因** 复用只按"目标回合 + 归档的回合区间"来判定，而两条不同分支可以完全共享这两者；此时 live
  目录里的 autosave 早被新分支改写了。
- **解决** `scripts/rollback-to-turn.py` 里的 `_archive_can_absorb()`：只有当候选归档要接收的每个存档
  在**大小与写入时间**上都吻合时才复用；否则另开一个带时间戳的新文件夹，两边都不动。清单是合并而不是
  重建。
- **证据** `tests/test_rollback_decisions.py::TestTheArchiveIsNotClobbered`（5 项）。

### RB-03 `.tools/archive-branch.py` 无法按路径导入

- **症状** `python scripts/rollback-to-turn.py 352 --apply` 与 `--archive-only` 在写出任何东西之前就
  死于 `ModuleNotFoundError: No module named '_game'`，而计划本身打印正常。
- **起因** 按路径加载模块不会把它的目录放进 `sys.path`，而这个文件在导入时就引用了兄弟模块 `_game`。
- **解决** `load_archive_branch_module()` 在 `exec_module` 之前把 `.tools` 加进 `sys.path`。提交
  `b57329f`。
- **证据** `tests/test_rollback_decisions.py::test_the_archive_branch_module_loads_with_its_own_siblings`。

### RB-04 没有办法"不带走之前记忆"地从载入位置继续打

- **症状** 回退是刻意恢复过去的，这对"重打一遍"是对的，而对"从载入的位置继续、一点旧信息都不要"是错的。
- **起因** 唯一的工具是 `rollback-to-turn.py`，而它的全部设计就是把过去放回去。
- **解决** `scripts/fresh-start.py <turn> [--apply] [--force]`：忘掉本局日记（run 副本与遗留根副本）、
  达成状态、run 的会话残留；把已达成目标的规则本体装回去；重置清单里"已打到第几回合"；先把所有东西复制
  到 `branches/fresh-start-<stamp>/files/`；会话在跑时拒绝执行。提交 `026381e`。
- **证据** `tests/test_fresh_start.py`（18 项）以及第一次真实运行——它的计划和结果都写在提交信息里。

### RB-05 只删掉达成注释，破坏了规则文件的契约

- **症状** 把本局那两条 `achieved T99` 注释删掉却不装回规则，会让七条测试变红，其中包括
  `test_every_retirement_trace_still_resolves_to_its_archived_block` 与
  `test_the_china_wonder_obligation_is_live_or_recoverable`。
- **起因** 规则文件的契约是：一条已退役的规则必须**要么活着、要么可追溯**；注释是回到归档块的唯一路径，
  删掉它就把规则搁浅了。
- **解决** `fresh-start.py::rearm_traces()` 把归档块装回 `prompts/checks/archive/` 所指的位置并删掉
  注释——这正是 `turn_checks.restore_achieved` 的同一操作，只是作用在本局自己的退役记录上。"注释不能
  为空"那条守卫改成 `pytest.skip`，因为全新开始之后空列表是一个正确状态。提交 `fcf22b0`、`22b1cd6`。
- **证据** `tests/test_fresh_start.py`、`tests/test_turn_checks.py`（那条 skip），以及改动前的七条红色。

### RB-06 第一版 fresh-start 备份把目录拍平，丢了一段日记

- **症状** 树上本来有两个 `diary_china_-1894041591.jsonl`——run 副本（第 1..287 回合）与遗留根副本
  （289..354 回合）——而备份里只有一个，于是后者覆盖了前者。
- **起因** 复制目标是 `files/<basename>`，而这两个来源同名。
- **解决** 备份改为镜像源路径（`files/.civ6-mcp-data/runs/<run>/diary_...jsonl` 与
  `files/.civ6-mcp-data/diary_...jsonl`），并有测试断言两份都存在且内容不同。提交 `026381e`（修复随工具
  的第一次复查一起落地）。
- **证据** `tests/test_fresh_start.py::test_everything_forgotten_is_in_the_backup_first`；更早的副本
  仍在 `branches/abandoned-*/backup-*/` 下保存着那一段。

### RB-07 fresh-start 的测试套件把真实对局清了

- **症状** `00:13:35`、`00:13:53`、`00:14:03` 三次测试运行删掉的是**真实对局**的日记与达成状态，而不是
  临时副本的。
- **起因** 测试调用 `main()` 时不传参数，而 `main()` 用的是模块级的 checkout 根目录——于是"假 checkout"
  fixture 在真正要紧的那些路径上被忽略了。
- **解决** `main(root=None)` 接收根目录，测试传自己的 fixture，并且有测试断言默认值、断言 fixture 不是
  checkout。事故删掉的一切都在 `branches/fresh-start-20261005-001335/files/` 里。提交 `026381e`。
- **证据** `tests/test_fresh_start.py::test_main_defaults_to_the_checkout_root_and_is_never_given_it_by_accident`。

### RB-08 全新开始仍然带着正在生效的临时任务

- **症状** `fresh-start.py 352 --apply` 之后，新会话仍要读并执行三个临时任务——
  `044-schedule-three-modern-armor.md`、`045-two-carriers-with-aircraft.md` 与
  `046-use-the-two-great-merchants-or-record-why-this-match-cannot.md`，每个都写着
  `added: 2026-10-04`，截止回合按 T344 或 T352 计算，正文里带本局的城市、计数与坐标。"不带任何过往信息"
  对日记和达成状态成立，对这些**指令**并不成立。
- **起因** 工具是**故意**保留它们的：任务是指令而不是记忆，而静默撤令正是登记册、`AGENTS.md` 与
  `tests/test_temp_tasks.py` 存在的意义。于是唯一的出路是操作者手工敲三条 `temp-task.py retire`
  命令——而这恰恰是"重新开始"这个动作不该要求的。
- **解决** `fresh-start.py --tasks` 会通过 `scripts/temp-task.py` 自己的 `cmd_retire`
  （`--expired --turn <resume> --no-commit`）把它们全部撤掉：每个文件移入
  `prompts/tasks/tmp/done/<stem>-expired-T<n>.md`，它在登记册里的行被删掉并留下退役说明，
  `AGENTS.md` 的 `IN FORCE NOW` 行随之重建。每个任务文件在移动之前先复制进本 run 的备份；被拒绝的
  撤令会打印成 `! NOT withdrawn` 而不是被吞掉；默认行为仍然是保留。
- **证据** `tests/test_fresh_start.py::TestWithdrawingTheTasks`（5 项：计划、默认行为、移动加登记册与
  `AGENTS.md`、备份、以及一次模拟拒绝后任务仍在生效）。

## EN —— 编码与文档门禁

### EN-01 agent 自己的编辑器会把中文文档需要的 BOM 去掉

- **症状** 编辑过 `.zh.` 文件、`SETUP-WINDOWS.md`、战术文件或任务文件之后，文档在 GBK 查看器里是乱码；
  `fix-text-encoding.py --check` 失败。
- **起因** agent 的 `write`/`edit` 工具输出纯 UTF-8，并会静默丢掉 BOM。看不到 BOM 的 zh-CN 编辑器会把
  文件按代码页 936 解码。
- **解决** 每次这类编辑之后运行 `python scripts/fix-text-encoding.py`；这道门禁同时也是
  `tests/test_text_encoding.py` 与 pre-commit 钩子。
- **证据** 门禁自己的输出：`N BOM(s) restored` 与
  `0 document(s) would show as mojibake in a GBK viewer`。

### EN-02 英文改动会让它的中文备份过期

- **症状** `tests/test_dsh_documents.py` 报
  `does not carry these spans of <name>, so it was translated from an older revision`，或者标题数量
  不匹配。
- **起因** 每个交给模型的文档旁边都有一份 `<name>.cn.md` 备份，而备份会被检查：英文文件里每一个行内代码
  片段、以及每一个标题，都必须出现在备份里。
- **解决** 在同一次提交里手工把新增片段与标题补进备份；永远不要把备份当源文件编辑。本日志本身就被抓过两次
  （`game-recovery.md`、`military-strategy-coverage.md`）。
- **证据** `python -m pytest tests/test_dsh_documents.py`。

### EN-03 AGENTS.md 最多只能引用四个回合，新条目可能把它顶超

- **症状** 加了两条之后出现 `AGENTS.md cites 6 turns (limit 4): lines [...]`。
- **起因** 回合号是只有本局能用的信息；这份参考要保持与具体对局无关，所以数量被封顶。
- **解决** 说法保留、回合号去掉（写成"measured on this match"），或者把故事移到 retrospective。上限在
  `tests/test_agents_is_game_agnostic.py` 里。
- **证据** `python -m pytest tests/test_agents_is_game_agnostic.py`。

### EN-04 共享的规则文件让一局的退役变成另一局的沉默

- **症状** 实测：A3-A7 实验重放了同一存档的 T1 分支大约 340 回合，`dynasty-cycle-wonder` 一直不在循环
  里，八次会话全部造出 0 个奇观。
- **起因** `prompts/checks/turn-checks.md` 是这个 checkout 里所有对局共用的一份文件，而 `once: true`
  目标在达成的那一回合就被清除——于一局的达成删掉了另一局的规则。
- **解决** 退役注释带上写下它的对局 key，`turn_checks.restore_foreign_games` 在载入时把别的对局的目标
  装回去；不带 key 的旧注释原样保留、不去猜。标着本局的注释则保持退役。
- **证据** `tests/test_turn_checks.py::TestAGoalAnotherMatchAchievedComesBack`。

## TL —— 工具与数据

### TL-01 `.tools/sleeping-units.py` 因为少一个导入而崩溃

- **症状** `NameError: name 'asyncio' is not defined`。
- **起因** 模块用了 `asyncio.run` 却没有导入它。
- **解决** 补上 `import asyncio`。
- **证据** 该工具对着活的游戏运行，按 activity 分组列出每一个单位。

### TL-02 `civ6-clean.ps1` 忽略了 `runs/` 下的心跳

- **症状** 明明有活的 run 心跳，它却报告 `heartbeat none (already clean)`，于是清洁器说树是干净的，而
  会话可能还在跑。
- **起因** 状态清单只收集根目录那份心跳，那是迁移到 runs/ 之前的位置。
- **解决** 清单无论根目录有没有文件，都会收集 `runs/**/heartbeat.json`；settled 判定改为看"现在还剩下
  什么"。提交 `4fbc64c`。
- **证据** 对一个带过期心跳的 run 运行 `scripts/civ6-clean.ps1 -DryRun`。

### TL-03 `stop-agent.py` 把请求写进了错误的数据目录

- **症状** 第一次运行把 `stop-request.json` 写进 `~/.civ6-mcp-data`，而不是 run 目录——没有任何会话会
  读那个位置。
- **起因** `stop_request` 的默认值解析 `CIV_MCP_DATA_DIR`，而普通 shell 里没有这个变量。
- **解决** CLI 显式传入 run 目录（`run_dir()`），这与 `scripts/rollback-to-turn.py`、`scripts/run.py`
  当初修的是同一条规则。
- **证据** `tests/test_stop_request.py`；以及一次点明 run 目录的实测 `--status`。

### TL-04 `GameCore_Tuner/InGame states not found` 通常意味着另一个客户端占着 tuner

- **症状** 每个工具调用都回 `ConnectionError: GameCore_Tuner/InGame states not found`，读起来像是游戏坏了。
- **起因** FireTuner 只服务一个客户端，而正在打的会话的 MCP 会在整个会话期间握着这个连接。第二个客户端
  能连上，然后死掉。
- **解决** 会话在跑时读文件、不碰 tuner；需要事实就问会话；用 `.tools/whats-on-screen.py`、
  `stop-agent.py --status`、心跳和日志——这些都不需要 tuner。
- **证据** 在连接被持有、空闲与忙碌两种状态下实测过；记录在 `docs/game-recovery.md`。

### TL-05 一次重载会把整个回合重置

- **症状** 游戏重启并载入存档之后，被打断那个回合的所有动作都没了（科罗廖夫的启用、一座城市的发射项目、
  建造者的指令）。
- **起因** 载入存档就是这个语义：回合内的工作不属于存档的一部分。
- **解决** 把重启当作人类的决定，并先停会话（`scripts/stop-agent.py --wait`）；MCP 不再在停摆时自己重启
  游戏。
- **证据** T354 那次重载，以及 `2e836ba`。

### TL-06 route-A 驱动去数据根目录找 run 清单

- **症状** `orient.py` 与 `play-turn.py end` 对一个明明有清单的 run 打印
  `RUN no run manifest - this session is unlabelled, so nothing checks which playthrough the game
  belongs to (scripts/run.py init --id <name> --label <text>)`；同时那道唯一能阻止"把回合写进另一局
  的日记、退役目标与存档"的 `RUN MISMATCH` 守卫**从未触发**。
- **起因** `run_manifest.path()` 与 `load()` 的默认目录是 `CIV_MCP_DATA_DIR` **本身**，而清单实际住在
  解析后的 run 目录里（`runs/<run>/run.json`）。`session_info.banner` 与 `play-turn.py` 调用时都没传
  目录；`play-turn.py` 的 `run_manifest.touch(...)` 也因此是个静默空操作。所有先解析 run 的调用者
  （`handoff.py`、`server.py`、`fresh-start.py`、`rollback-to-turn.py`）本来就是对的，所以只有这两个
  驱动暴露了问题。
- **解决** 先解析 run 目录再取清单，和 `diary_path`、`turn_checks.state_path` 一直以来的做法一致：
  在 `session_info.banner` 里用 `run_manifest.resolve_data_dir()`，在 `play-turn.py` 里用一个局部
  `run_dir` 供 `verify` 与 `touch` 共用。
- **证据** `tests/test_session_info.py::TestTheRunLineFindsTheManifest`（会点名 run 并带上已打到的
  回合；另一局的清单仍然是响亮的 mismatch），以及实测横幅——它现在读作
  `RUN china--1894041591 "migrated from china_-1894041591"  (civ/seed match, played to T352)`，
  而此前是 `RUN no run manifest`。

## PT —— 与人类协作

### PT-01 分工被说了三次，一次比一次窄

- **症状** 第一版只写了"军事单位"；随后人类不得不指出大海军统帅也是他的，之后又指出大科学家与大商人是
  agent 的。
- **起因** 分工是从"military"这个词推断出来的，而不是把两份名单写下来。
- **解决** 任务文本显式点名两类（`is_the_humans` 匹配战斗强度大于零，或者单位类型含 GENERAL/ADMIRAL），
  而"其余一切"那份名单点名建造者、开拓者、商人、大科学家与大商人。提交 `c9e67d0`、`fb17eaa`。
- **证据** `tests/test_agent_half.py` 与 `tests/test_wait_for_human.py`（战斗强度为零的统帅仍属于人类；
  大科学家不属于）。

### PT-02 "人类做完了"这个信号需要的是定义，而不是新标记

- **症状** agent 一直在等一个人类根本不会发出的信号。
- **起因** 一直把"人类做完了"当成人类要报告的事情，而它其实是盘面显示出来的事情。
- **解决** 人类的决定：不要单独的标记——游戏处于"结束回合"状态，就说明人类做完了。这成了"轮到谁"报告的
  第三态。提交 `3fbd1d7`。
- **证据** 第三态自己的文本，由 `tests/test_agent_half.py` 断言。

### PT-03 几个五五开的选择属于人类，而每一个都塑造了一件工具

- **症状** 每一个都让工作停住，直到问出来为止：早报告还是自己重启；谁负责重启游戏；怎么停一个会话；
  "全新开始"到底清掉什么。
- **起因** 这些是政策而不是工程：它们决定人类看到什么、以及允许对他的游戏做什么。
- **解决** 先问，再把答案写进真正执行它的地方——`2e836ba`（120 秒报告而不是自己重启）、`fccfb6a`
  （停止用请求文件而不是 kill）、`026381e`（全新开始的范围：只清本局；注释装回、规则本体保留）。
- **证据** 每条提交信息都引用了它实现的那句指令。

## 经验法则

1. **会写真实状态的测试，迟早会毁掉真实状态。** 一天之内两次：一次资格测试覆盖了活的心跳，一次测试套件
   清掉了对局的记忆。两处都通过注入根目录或临时目录修好，并且各自有一条测试钉住注入。
2. **绝不让报告与引擎互相矛盾。** `UI.CanEndTurn()` 和那个 0.2 移动力的单位都教了同一件事：当游戏说一套、
   报告说另一套时，会话会永远等下去。测量引擎自己的信号，然后报告它。
3. **一个开关需要契约测试。** `-HumanMilitary` 是 PowerShell，pytest 跑不了它；能钉住的是它追加的文本、
   它在哪些路径上追加、以及它周围的守卫。第一次跑就因此找出了一个真实缺陷。
4. **删掉一条记录不等于删掉一条指令。** 达成注释必须被它代表的规则本体替换；临时任务是打印出来而不是
   静默撤掉。
5. **先备份再遗忘，而且备份要镜像目录树。** 拍平的备份会悄悄把两个文件合成一个。
6. **把规则写在会被读到的地方。** 分工活在任务文件里；执行它的规则必须同时写进 `AGENTS.md`、
   `SKILL.md` 和任务文本，因为它们彼此都不读对方。

## 出处

- `docs/game-recovery.md`——恢复的权威：停摆、载入、领袖开场窗口、存档清单。
- `docs/military-strategy-coverage.md`——强制力阶梯，以及哪些策略真的有牙齿。
- `AGENTS.md`——会话被交代了什么，以及分工下它绝不能做什么。
- `scripts/README.md`——运维视角的每个脚本，包括 `resume-game.ps1 -HumanMilitary`。
- 上面每一条落地时都过的那套门禁：`python scripts/fix-text-encoding.py --check`、
  `python -m pytest -q`、`node --test test/dsh/*.test.mjs`、`npm run qualify`、
  `python scripts/qualify-mcp.py`、`python .tools/audit-md-language.py`、
  `python .tools/check-directive-sync.py`。
