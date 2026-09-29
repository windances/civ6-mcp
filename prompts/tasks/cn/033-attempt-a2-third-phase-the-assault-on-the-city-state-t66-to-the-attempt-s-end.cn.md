> 本文件是 `033-attempt-a2-third-phase-the-assault-on-the-city-state-t66-to-the-attempt-s-end.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

## 你现在在哪（先读这段）

棋局停在 **T66**，而且**你已经与 耶路撒冷（player 6）处于战争状态**。这场仗是用玩家操作宣告的——正是本次尝试发现的那个缺陷的修复：`send_diplomatic_action` 用外交会话来宣战，而城邦没有会话可开，于是回执只写 `WARN:WAR_UNCERTAIN`、实际什么都没发生。现在 `build_send_diplo_action` 按游戏自己的宣战弹窗那条路（无宣战理由分支）宣告城邦战争，并且已从游戏里验证：`IsAtWarWith(6)` 为真。

军队与剩余工作：

- **三台弩炮**（西安、太原各一，另有一台）、四个勇士、三个弓箭手、一辆重战车。宣战时前两台弩炮分别站在开火格 (50,24) 与 (51,23)——距城 2 格——近战在环上，弓箭手支援。
- **目标血量池读作 200**；它的**城墙从未被任何工具读到过**。第一炮时读出来，把数字写进日记。
- 本次尝试在**拿下城池**或棋局到达 **T80** 时结束。

## 唯一还没测的东西

Q3——*T80 前拿下第一座城*——是本实验最后一个开放问题。其余已有答案：Q1 在 T60 被证伪（卡在表格的 `ram` 与 `ranged` 两个名额），Q2 在 T48 成立，Q4 的门在 T60 打开。所以：能开火就每回合开火，攻城单位前面始终留屏护（`screen-the-siege` 一直在报错，该规则归 `tactics/05`），伤害要从 `SIEGE PROGRESS` 与**之后**的读取判断而不是从即时回执，血量池空了就用 `city_action` 处理城池。

## 开始

1. `get_game_status` —— 必须回答 `in_game`。**绝不启动游戏、绝不读档**，那是人类的决定。然后 `get_diary`，再用一次 `scripts\orient.py`。
2. **T41 的待办已经清完**（着力点 `COMMEMORATION_SCIENTIFIC`、T41 已立 锻造之神、火山损伤已治疗与修复）。不要重做。万神殿守卫在本会话加载的 Lua 里已修好。
3. 前半程若还便宜可补：目标城墙/HP/驻军读数，以及每十回合的 `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:` 三行与 `10-TURN REVIEW` 的三个问题（用数字回答）。

## 终点，以及要留下什么

- 尝试的终点与任务 031 一致：**拿下城池**（`city_action` 回执读到 `KEEP|`）或棋局到达 **T80**。`expires:` 为 T85。
- 结束时取快照：
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run sacred-garnet-vault-35,pale-pearl-aqueduct-92,<本会话> --from 1 --to <最后一回合> --step 10 --verdict --questions a2 --save docs/experiments/A2-final.json`
  **每个会话名都要写**：这次尝试跨了两次续跑（T1–T40 在 `sacred-garnet-vault-35`、T41–T65 在 `pale-pearl-aqueduct-92`、本会话自 T66 起），插桩按会话时间归属日记行——只写当前会话会丢掉此前所有回合。然后跑 `--compare docs\experiments\A1-T40.json docs\experiments\A2-final.json`，补完 `002-attempt-A2.md`（T40 表与 T48 一节保留，终点表写在其下），并把 A2 的后半程更新进 `RETRO-2026-09-29.md`——城池是否拿下、城墙读作多少、这场攻坚的代价。
- 然后**把本文件与 031 一起退役**，并在日记的 `tooling` 行写明各自结束于哪一回合。

## 这次尝试已经付过代价的诚实条款

- 战斗回执印的是**攻击前** HP（命中时也写 `enemy HP:72 -> 72/100`）：不要据回执判定攻击失败，也不要据此重发攻击——本次尝试已因此用 `force=True` 丢掉过一次合法攻击。
- 城池进度看 `SIEGE PROGRESS` 与**之后**的读取，不看即时回执；那些块也会给出城墙数值。
- 你自己的 `ESTABLISHMENT:` 行会被与记录对照：**两个数字都写**（`melee 2 target / 4 held`）。
- 日记与 A1 共享，插桩按会话时间归属行；不是你这一会话打过的回合，就不该由你描述。
