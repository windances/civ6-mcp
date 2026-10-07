> 本文件是 `052-playing-on-after-a-victory-an-option-not-a-stall.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

## 为什么需要这个

T385 那一局报出了 `GAME OVER - VICTORY (Culture)`，而工具链里**没有任何东西注意到它**：
`scripts/resume-game.ps1` 照样生成"打到 100 回合"的任务，它启动的会话随即发现引擎不再推进回合，而紧接着
为征服发布的任务几分钟后就被当作"过期"退役。**胜利就写在 `get_game_overview` 自己的输出里**——预检从存档
读了回合，却从没读那一行。

人类的指令是：**胜利不能是停止条件**，必须有一个明确的继续方式（Civ VI 支持——胜利画面的"再玩一回合"）。

## 要做什么

1. **`src/civ_mcp/handoff.py`**
   - **识别胜利**：probe 的 `get_game_overview` 输出里带 `GAME OVER` 行；把它作为独立字段放进
     facts/result（例如 `result["victory"]`，比赛未结束时为 `None`）。
   - `task_text(facts, result, turns=100, rollback=False, after_victory=False)`：
     - **有胜利且未传 `after_victory`**：任务必须写明"这局已经赢了、没有可打的、停下来报告"——这正是
       T385 那次交接缺失的守卫。
     - **有胜利且传了 `after_victory`**：任务必须写明"这局已赢，本会话是在**有意继续**它"，并点出第一个
       可能的障碍（胜利画面需要清掉——先 `dismiss_popup`，再用 `.tools/whats-on-screen.py` 读屏幕，若回合
       仍不推进就请人类点"再玩一回合"），其余内容不变。
   - 顺手在同一函数里修掉 `None`：probe 读不到回合时用**最新存档的回合**兜底（实测 2026-10-08 的 T387，
     tuner 被占的预检把 `found turn None` 写进了任务文本，而同一份报告早已读到
     `AutoSave_0387 holds T386`——注意 `AutoSave_NNNN` 的命名差一）。
2. **`scripts/resume-game.ps1`** —— 增加开关（例如 `-AfterVictory`）：(a) 透传到 `task_text`，让生成的
   任务带上上面那段；(b) 出现在 `-DryRun` 预览里，人类能看到它会交出什么。**拒绝路径仍必须拒绝
   `TUNER_BUSY`**，并且 `-DryRun` 的退出码应当跟随 verdict，而不是永远 0。
3. **文档** —— `scripts/README.md`（＋`.cn.md` 备份）写明这个开关；`AGENTS.md`（＋`.cn.md` 备份）在
   Game Recovery 里加一行：预检会报告"比赛已结束"，而 `-AfterVictory` 是会话继续它的方式。
4. **测试** —— `tests/test_handoff.py`：有胜利且无开关时 `task_text` 说"停"（且不再说"最多打 100 回合"）；
   带开关时说"继续"并点出清屏那一步；probe 为 `None` 时渲染出存档的回合、绝不出现 `None`。
   PowerShell 开关追加文本的测试照 `tests/test_resume_game_division.py` 的写法。

## 完成条件

`scripts/resume-game.ps1 -AfterVictory -DryRun` 打出的任务第一段写明"这局已赢、本会话有意继续它"，且
`tests/test_handoff.py` 里关于胜利分支有 >= 3 个测试（无开关=拒绝、有开关=继续、以及绝不出现 `None` 回合）。
这些成立的那一回合退役本文件，并在日记里记下胜利是在哪一回合报出的、以及它是否让一个会话白跑。
