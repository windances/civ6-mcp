> 本文件是 `game-recovery.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

---
title: Game Recovery — the operational detail
---

本文件于 2026-09-26 从 `AGENTS.md` 中移出，当时该文件超过了 65536 字节的注入预算，其尾部内容不再能到达会话。措辞没有任何改动：这就是那一节当时的样子，而 `AGENTS.md` 只保留了必须每回合摆在会话前面的那三行。

## 游戏恢复

**把对局交给一个新会话只需一条命令，而且它不是 agent 的事：**
```
scripts\resume-game.ps1            # check, tell the human what to do, stop
scripts\resume-game.ps1 -Wait      # ... or wait for the human's load, then launch a session
scripts\resume-game.ps1 -Rollback  # the human deliberately loaded an earlier save
```
它先运行 `civ_mcp.handoff`，后者只读取**被动**信号——进程列表、操作系统 TCP 表中 FireTuner 端口的所有者、心跳文件，以及磁盘上的存档连同每个文件实际持有的回合——因此它可以在任何时候运行，**包括在另一个会话正在游玩的时候**（MCP 自己的 `get_game_status` 会连接并读取屏幕，这在当前进程即将采取行动时是对的，而在发问本身不能干扰答案时是错的）。它以一条判决结束：`not_running`（启动）、`no_match`（加载存档）、`tuner_silent`（启动时没有 EnableTuner）、`tuner_busy`（另一个会话占着 tuner），或者 `in_game`——把它交出去。**它从不启动，也从不加载**——那始终由人决定，所以判决的职责是说清楚谁做什么。当判决是 `in_game` 时，该会话的任务是**由这些事实生成的**（`.civ6-mcp-data/resume-task.en.txt`），所以其中的回合号或存档名都不会过期。

**两个存档家族的编号方式不同，2026-09-26 实测：** `0_MCP_NNNN` 保存的是回合 NNNN，而游戏自己的 **`AutoSave_NNNN` 保存的是回合 NNNN-1**（`0_MCP_0142` 保存 T142，`AutoSave_0142` 保存 T141——核对过三对）。所以“名字里的数字就是回合”只对 MCP 的文件成立；拿已加载的回合去比对自动存档的名字会差一个，而 `scripts\turn-of-save.py "<path>"` 会在存档被加载之前打印出它真正保存的内容。两个家族都重要，但谁都不权威：“Continue Game”恢复的是**按时间最新**的那个文件，所以 handoff 推荐的就是它，而一个较新却*不是*最靠前位置的文件，就是值得标出来的回档气味。

**`0_MCP_NNNN` 在实战中打破了这个不变式，所以现在先问文件本身。** 2026-09-27 在 109 个存档上实测：`AutoSave` 家族在 100 个中 100 个一致（名字 = 回合加一），而**最新的九个 `0_MCP` 文件中有四个名字低了一个回合**——`0_MCP_0206` 保存 T207，`0_MCP_0209` 保存 T210，`0_MCP_0212` 保存 T213，`0_MCP_0215` 保存 T216。原因在 `end_turn` 里：名字是由同一次推进后的读取构建的，而那次读取有时会打印 `Turn 203 -> 203`（T200/203/206/209/212/215 都是如此）。现在有两件事守住了这条线：`end_turn` 读取已保存文件的回合，并在名字不一致时**把它改名**；而 agent 的过期时钟（`tests/test_temp_tasks.game_turn`）和 handoff 都**从文件里**读回合（`handoff.save_turn`，每个存档约十分之一秒），名字只作为后备。

**动手之前先问游戏在哪里：**
```
get_game_status   # not_running / starting / in_game / leader_screen / main_menu / loading / tuner_busy
```
它回答状态、回合，以及一行 `NEXT:`，所以恢复不必再从碰巧失败的那次调用来推断。有两个回答会改变你的做法：`in_game` 意味着游戏已经可玩（无需启动或加载），而 `tuner_busy` 意味着另一个进程占着 FireTuner 连接——FireTuner 只服务一个连接，所以只要那一个还活着，从这里发出的任何调用都不可能成功。等待没有用：用 `scripts\civ6-clean.ps1` 停掉那个进程，或者继续在它的会话里游玩。

**MCP 自动存档：** `end_turn` 每回合自动保存为 `0_MCP_NNNN`（保留最后 5 个）。这些是你主要的恢复点。

**两个恢复陷阱，都在 2026-09-25 实测（一个会话里五次崩溃/卡死）：**

1. **`0_MCP_NNNN` 的名字会在回档后的分支之间碰撞，而回档并不会删除被放弃分支的文件。** 按名字加载 `0_MCP_0122` 会悄悄加载*另一个*分支的局面——同样的回合号，不同的棋盘（18 个单位、两个 Trebuchet、没有 Moscow），所以回合检查通过了，只有把单位读回来才抓到它。**在任何回档之后，用游戏自己的每会话自动存档 `AutoSave_NNNN` 来恢复**（位于 `Saves/Single/auto`，在 Windows 上被 OneDrive 重定向到 `C:/Users/<user>/OneDrive/文档/My Games/Sid Meier's Civilization VI/Saves/Single/`），按修改时间选取丢失回合之前或当回合最新的那个。存档列表 Lua 探针（`.tools/probes/save-list.lua`）会打印名字、路径和时间，好把两者区分开。
2. **一个不推进的回合不一定是卡死。** 有两次是游戏在等鼠标：一次是加载后停在领袖画面上（CONTINUE 点击落在了浏览器上，因为 `_click` 是按屏幕坐标注入的，而全屏游戏必须在最前面——通过先聚焦修好，`_bring_to_front`），另一次是卡在自然灾害弹窗加上二十个 `InvitePopup` 后面。**重启之前先读屏幕（`.tools/whats-on-screen.py`）**，并在重新启动之前先试 `dismiss_popup`。

从 shell 启动可能需要完整的文件系统访问权限：游戏在启动时会写 `%LOCALAPPDATA%\Firaxis Games` 及其 OneDrive 存档目录，而在受限环境下启动根本不会产生进程。

**一次读取就重新定位：`scripts\orient.py`。** 回档（或任何冷启动）之后的规则是“从游戏重建每一个事实”，而分五次读取去做这件事，正是其中一次被跳过的原因。一个连接就打印游戏概览、单位、城市、科技/市政、政策、外交（仅已会面的文明）、资源、总督、贸易路线、建造者任务、城邦、胜利/人口统计、宗教、伟人、万神殿和通知——默认紧凑，`--full` 输出原始 dataclass 转储，`--only a,b` 缩小范围，`--maps` 输出带解说的地图。两个同伴：`scripts\turn-of-save.py "<path>"` 在你加载*之前*打印存档真正保存的回合（手动存档的名字里不带回合，而存档解析器也不总能从文件里读出一个——T59 的回档只能凭信任接受游戏自己的文件名），以及 `scripts\probe-tile.py x,y` 打印原始地块记录（地形、特征、资源、所有者、单位），正是它确定了 (58,30) 上根本没有任何*可见*资源。

**无人值守的发展回合：`scripts\auto-turns.py --turns N`。** 它按任务清单派遣建造者，按每座城市的计划填满每座城市的队列，按优先级列表推进科技和市政，接受万神殿/奉献/总督的选项，在金币高于 `--buy-at` 时购买一个建造者，并写下与操作者所写的相同的日记行（反思是事实性的，而非诠释性的）。它**从不**攻击、宣战、清剿蛮族营地、向敌人移动或碰外交——一旦三格内有非蛮族敌人或战争开始，它就停下并交还控制权，那正是战术文件适用的地方。先运行 `--dry-run`：它会打印将要下达的命令，什么也不碰。

**按名字加载**（首选——不需要 `list_saves`）：
```
load_game_save("0_MCP_0079")  # find it in the game's own save list and load it
get_game_overview              # verify load
```
它既能在游戏内使用，也能从主菜单使用：在没有加载游戏时，同样的两次调用会运行在游戏自己的 FrontEnd 加载屏幕状态（`LoadGameMenu`）中，所以无需点击任何东西，也没有窗口必须在最前面。随后它自己完成加载——等待领袖画面、点击 CONTINUE、并把回合读回来——所以回复会说出实际加载的回合，而加载错了则会返回 `WARNING: the game reports turn N, but '<save>' holds turn M`。OCR 菜单导航是针对游戏列表中没有的存档的后备方案。

**当游戏卡死时**（AI 回合循环）：
```
restart_and_load("0_MCP_NNNN")   # kill + relaunch + load (~90s)
get_game_overview                 # verify load
```

**回合倒退检测：** 如果你不小心加载了错误的存档（例如加载了 T1 场景存档而不是你的自动存档），`end_turn` 会发出 CRITICAL 警告，并给出应重新加载的正确自动存档名。

其他工具：`list_saves`、`load_save(index)`、`kill_game`、`launch_game`、`load_save_from_menu(name)`。存档名省略扩展名：`"AutoSave_0221"`。写成 `"AutoSave_0221.Civ6Save"` 也会被接受，并会被剥掉，因为游戏自己的存档列表里带的就是它。

**一次只允许一个会话。** 当另一个会话正在游玩时，`kill_game` 和 `restart_and_load` 会拒绝（它们会说出持有 FireTuner 连接或正在写最近心跳的那个 pid），所以恢复不会扔别人正玩到一半的局面。只有在你确知那个会话已死时才传 `force=True`。加载游戏已经停留其上的存档不算加载：`load_game_save` 会从当前回合回答 "Already loaded"，而不是去点一个根本不在屏幕上的主菜单。

**而且一次只允许一个*诊断*客户端，这是同一条规则从咬到我们的那一面看。** FireTuner 会把它的监听交给第一个接受它的客户端，所以**你为检查 tuner 而跑的一个探针，会把连接从正在游玩的会话手里拿走。** 2026-09-30 实测：一个会话停在 `phase: playing`，心跳已经过期三分钟，在从外部对游戏反复运行 `list_saves`/状态探针期间始终不推进；探针读到的是一个**空的 Lua 状态列表**（读起来完全就像“tuner 坏了”），而探针一停，会话就自己重连并继续游玩。**会话游玩期间只读文件** - 日志、心跳、`.tools/whats-on-screen.py` - 让会话去做 tuner 调用；如果你需要游戏里的某个事实，去问会话。两条值得记住的推论：探针返回的空状态列表是关于*你的*连接的证据，不是关于游戏的；以及在一次存档加载之后，游戏可能只在 **4319** 上监听，`GameConnection` 现在把它作为后备走一遍（`tuner_port_candidates`，先 4318 再 4319）。

**一个已经落地的加载仍可能被重试十分钟，而那并不是卡死。** 2026-09-30 加载实验的共享开局（尝试 A8）时实测：游戏已经到达**第 1 回合**并停在开局顾问上——`.tools/whats-on-screen.py` 读到 `TURN 1`、`CHOOSE RESEARCH`、`CODE OF LAWS`，没有领袖画面——而 `load_game_save` 还在**九分钟里反复点击 CONTINUE 约九十次**，每次尝试都记录 `Continue: the leader screen is gone (unrecognised (N text boxes)) - the click took`，然后是 `Discovered 0 Lua states (GameCore=None, InGame=None)`，**4318 拒绝而 4319 应答**。它自己返回了，会话也继续游玩。**所以在这个窗口里要做的三件事全都是“什么都不做”：** 不要杀掉会话（它在调用内部，不是卡住了），不要从日志的沉默推断失败（调用只在返回时才记录），也不要启动第二个会话——用 `whats-on-screen.py` 从外部核对局面，它不碰 tuner。**那些点击在真正要紧的情形里也是无害的**：它们瞄准的局面本来就是要加载的那一个，而证据就是会话恢复后自己的第一次读取——`No technology being researched!`——若有一次乱点的点击选了科技，那里就会显示一个。两条要记住的事实：`0 Lua states` 那一行属于*落地*窗口，不属于会话的连接；而一次加载真正的成功信号是屏幕读到的回合，不是调用自己的回复。

**而在一次真正的 `HANG` 之后，一连串失败其实只是同一个画面：领袖开场。** 2026-09-30 在同一尝试的 T6 实测，顺序如下：

- `end_turn` 回答 **`HANG:6:0_MCP_0006`**——AI 回合停摆，不是弹窗；
- `get_game_overview` 回答 **`GameCore_Tuner/InGame states not found`**；
- `load_game_save` 回答 **`FAILED: Could not find 'Load Game' button`**，两次；
- `dismiss_popup` 回答 **`No popups to dismiss`**；
- 而在这一切过程中，游戏一直停在**已加载游戏的领袖开场**（`CHINESE EMPIRE`、`QIN (UNIFIER)`、一个 CONTINUE 按钮）——一个 **Lua 看不见**的画面，所以上面每个工具都在回答一个游戏早已离开的状态。

**什么都没做它就好了**：下一次 `get_game_overview` 读到 `Turn 6 | China (Qin (Unifier))`，游玩继续。所以**那四条消息并不能证明恢复失败** - 那是领袖开场的窗口，也是唯一一个读屏幕不是后备方案而是唯一仪器的状态。`.tools/click-continue.py` **不带 `--click`** 是安全的检查：它用 `PIL.ImageGrab` 抓取像素（不给游戏发送任何东西），从不调用 `SetForegroundWindow`，报告游戏是否停在 CONTINUE 上，并且不改变任何东西。只有当它找到按钮且游戏是前台窗口时才传 `--click`。**而且优先选择先等待**：这个窗口大约五分钟后自己关闭了，所以一个活着且正在恢复中的会话应该让它自己走下去——这个辅助脚本是给它已经停住的情形用的，不是给它很慢的情形用的。

**AI 回合停摆在两分钟时就上报，而且 MCP 不再自己重启游戏（2026-10-04）。** 这个状态就是屏幕上显示的“其他玩家正在操作，请稍后”；`end_turn` 在这段时间里轮询，既没有 blocker、没有外交会话、也没有弹窗，而从 2026-10-04 起它在 `AI_TURN_STALL_REPORT_S` = **120 秒**后放弃，而不是过去的约 590 秒，并回答 `HANG:<turn>:<save>|... Waited <n>s. The game has held the AI-processing state past the two-minute limit, and past that point it does not recover by waiting: it needs a restart.`

- **人的规则（2026-10-04）：在这个状态超过两分钟就重启游戏，由人来重启。** T354 实测：两次停摆（`22:13:34`、`22:56:21`）各烧掉了整个旧预算，而回答在游戏明显停住几分钟之后才到，里面还没有说该做什么。
- **早报告，而不是自己重启。** MCP 过去会在通知任何人之前最多三次杀掉并重新拉起游戏（`server.py` 的 `HANG RECOVERY`）。现在默认关闭：重载会丢掉当前回合已经做完的一切——T354 那次重载把科罗廖夫的启用、西安的发射和建造者指令全部重置了——而且是在没人看着的时候做的。这条分支仍然留在 `CIV_MCP_HANG_SELF_RESTART=1` 后面，供无人值守的运行使用。
- **顺序是固定的：先停会话，再重启，再读档。** 会话不会在重启期间继续重试。收到 `HANG` 消息时：`scripts\stop-agent.py`（它写停止请求，`--wait N` 会兜底执行 `civ6-clean.ps1 -KeepGame`），然后由人重启游戏，再用 `load_game_save("<save>")` 从消息里点名的存档继续。
- **把后台窗口拉回前台仍然会先发生，而那不是重启**：Civ VI 的窗口在后台时不推进 AI 回合，所以 `server.py` 会重新聚焦并重试一次。T354 `22:56:20` 实测：窗口被 Chrome 压在后面（见 `hang_diagnosis.jsonl`），这正是让那次停摆看起来和 AI 卡死一模一样的原因。
- **诊断文件记录的内容没有变**（`hang_diagnosis.jsonl`：窗口矩形、焦点、前台窗口、前若干行 OCR 文本），而在自我重启关闭之后，它现在是停摆时*唯一*会碰游戏的东西——这正是重点：证据留下来了。

**回退也可以按"全新开始"来做（2026-10-05）。** `rollback-to-turn.py` 是刻意*恢复过去*的：边界之前的日记、已经在生效的临时任务、之前就已达成的规则——因为那段历史正是让重打的回合讲得通的东西。当人想要的是相反的做法，同一个已载入的局面、完全不带着"怎么走到这里的记忆"继续打，那就是 `scripts\fresh-start.py <turn>`：

- 它会忘掉本局的日记（run 目录里的那份**以及** `.civ6-mcp-data\` 下的遗留根副本）、达成状态（`runs\<run>\turn-checks-state.json` 与根目录的遗留那份）、run 的会话残留（`heartbeat.json`、`agent-half.txt`、`stop-request.json`），以及 `prompts/checks/turn-checks.md` 里**属于本局**的 `achieved T...` 注释——而且对每一条注释，它都会把规则本体从 `prompts/checks/archive/` 装回去；
- 它把清单里"已打到第几回合"重置为要接着打的回合，于是交接横幅与回合回退检测都从这里开始；
- 它**保留**全部规则本体（包括重新装回的这些）、标着*别的*对局的注释行（这个规则文件是本 checkout 里所有对局共用的）、正在生效的临时任务（只打印提示，不静默撤令——计划里就带着 `temp-task.py retire` 命令），以及 `branches/` 下的全部归档；
- 它忘掉的每一样东西都先整树复制到 `branches\fresh-start-<stamp>\files\...`，并附 `manifest.json` 与 `README.txt`，所以只要把树复制回去就能撤销；
- **会话在跑时它拒绝执行**（用的是 `stop-agent.py` 自己的存活判定），因为那种会话一个回合内就会把日记和心跳写回来——先停会话，再忘，再用 `resume-game.ps1 -Wait` 起新会话。

**为什么注释要"装回规则本体"而不是直接删掉。** 规则文件的契约、以及钉住它的测试套件都要求：一条已退役的规则必须**要么在文件里活着、要么可由注释追溯**——`test_every_retirement_trace_still_resolves_to_its_archived_block` 要求注释不能为空，`..._wonder_obligation_is_live_or_recoverable` 要求奇观那条规则要么活着要么可恢复。所以"清掉达成注释"只能意味着"规则重新生效"——这也正是人类指令的字面读法（注释走，规则本体留）。2026-10-05 实测：只删注释不装回本体，会让七条测试变红（上面两条、读取恢复后文件的那对 ram-tower 测试，以及三条从现行文件里找目标来达成的测试）。有一个后果值得点名：全新开始之后，文件里可能**一条注释都不剩**——本局退役过的规则全都重新生效了——上面第一条测试对这个状态是 `pytest.skip`，所以真正的孤儿注释仍然会被抓到，而一个正确的空文件不会被报成失败。

2026-10-05 实测：那次回退到 T352 之后，会话一直卡在一个只剩 0.2 移动力的单位上；这次全新开始清掉了日记（run 副本里是第 1..287 回合，遗留根副本里是 289..354 回合），删掉两条达成注释并重新装回它们的规则本体——一条带本局 key、一条不带 key，而不带 key 的注释按 `turn_checks.restore_foreign_games` 的读法就是本局的——并保留了三个临时任务。第一次真正执行的 `fresh-start.py 352 --apply` 时只剩一条注释，它被装回（`dynasty-cycle-wonder`），清单重置为 T352，规则文件里最终一条注释都没有——也就是上面那个 skip 覆盖的状态。造它的过程中发现两个缺陷：第一版工具把备份拍平了，于是两个同名的日记文件互相覆盖、只剩最后一个（现在备份按原树结构保存，并有测试钉住）；它的测试套件调用 `main()` 时不传根目录，于是一次测试运行忘掉的是**真实对局**的记忆而不是临时副本的（现在 `main()` 接收根目录，同样有测试钉住）。它删掉的那几段日记仍然可取回：每次运行前留下的那份在 `branches\fresh-start-<stamp>\files\`，而更早的归档（`branches\abandoned-*\backup-*\diary_china_-1894041591.jsonl`）保存着本局 2026-09-20 至 2026-09-28 期间的日记。
