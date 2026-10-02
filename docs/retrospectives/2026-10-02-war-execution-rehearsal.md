# 战争执行预演记录 — 写于开战之前（2026-10-02）

**这份文件的用途**：在**开战之前**把"发现一座未宣战的外国城市之后，执行会怎么走"写成可勾选的预测，
然后按那份预测逐回合观察实战。**对不上的地方才是收获**——它说明机制与文件说的不一样，或者我们
漏了一条必须靠人手记住的东西。

它不是 doctrine，也不是给下一局抄的参考；它是**这一次战争的对照表**。执行时每一回合往第 3 节
的日志里填一行；打完之后用第 5 节的工具重跑统计，再做判定。

**前提**：没有游戏在跑（检查过：没有 Civilization VI、没有 FireTuner、没有 python 进程）。
需要先加载存档 / 交接会话，然后本文件才进入使用状态。

预测里引用的每一条都能在代码里指到出处；工具名、块名、规则 id 都是运行时打印的字面量。

---

## 1. 场景

侦察兵在视野里第一次出现一座**未宣战**的外国城市（本例以俄罗斯的城市为模板）。触发点不是"宣战"，
而是"看见"。

---

## 2. 预测（每条都要能被证伪）

勾选栏留给实战：`✅` 一致 / `❌` 不一致 / `⚠️` 部分一致（并写下差异）。

| # | 预测 | 出处 | 结果 | 差异记录 |
|---|---|---|---|---|
| P1 | 城市第一次可见的那次**移动回复**里出现 `IN SIGHT ... [City: 名字] ... get_target_report(x,y)` | `narrate.narrate_sight` | | |
| P2 | 同一回合的 `end_turn` 出现**且只出现一次** `NEW TARGET (T<n>) ...` | `end_turn` 的进程内差分（首次扫描只播种） | | |
| P3 | **未宣战**状态下 `get_target_report` 就能给出 `walls N/100`、`city HP N/200`、驻军、三格内敌军，以及每格的 `FIRE` / `FIRE?` / `NO LINE OF SIGHT` | 工具；Gate 1-3 | | |
| P4 | 若目标格只是 `revealed`（已揭示但不当前可见），报告会明说"不是读数"，且**不给**墙/池/驻军 | `narrate.narrate_target_report` | | |
| P5 | 宣战前 `get_staging_plan` / `get_pathing_estimate` 的 `arrive T+n` **已含地形代价**（`cost N mp`），但**不含敌方 ZOC 停顿** | `_marchZoc` 只扫 `IsAtWarWith` 的玩家 | | |
| P6 | 宣战后**同一个环位**的 `arrive T+n` 可能 +1，并出现 `ZOC STOP at (x,y) on turn +k` | 同上；本轮新加的输出 | | |
| P7 | 和平期 `SIEGE POSTURE` 报 `city_distance`（集结参照），`war_city_distance` 为 999；`SIEGE FIRE: n/m` 在宣战前不具约束力 | 本轮修复（战争门 + 敌城口径） | | |
| P8 | 宣战前 `concentrate-the-siege`、`upgrade-the-siege`、`upgrade-the-unwatched`、`one-garrison-per-city` **静默**；宣战那一刻起可红 | 规则里的 `metric(at_war) >= 1` | | |
| P9 | `siege-train` / `ranged-mass` / `melee-screen` / `counter-the-cavalry` 在 T90 之后**和平期也会红**（盯编制，不盯战争） | 规则的 `when` 无战争门 | | |
| P10 | 和平期把单位 `move` 进对方领土会被游戏拒绝（`BLOCKED`，领土 / 开放边界），所以"宣战前集结"只能落在可合法进入的格子 | 游戏侧；实测有先例 | | |
| P11 | 宣战回合的攻击回 `NO_ENEMY`（战斗引擎下一回合才同步）；宣战回合只做占位 | `AGENTS.md`「War declaration」 | | |
| P12 | 宣战动作是 `send_diplomatic_action(id, "DECLARE_WAR")`，动作名由 `get_diplomacy` 的 `ACTIONS\|` 行给出；不可宣战时是 `ERR:CANNOT_DECLARE_WAR` | 工具 | | |
| P13 | **清单四项未满足就宣战，没有任何工具或规则会阻止** —— 这是整条链上最薄的一环 | 无出处（正是缺口） | | |
| P14 | `prompts/tactics/07-pre-war-analysis.md` 正文是否真的进了 `civ_advisor` 简报（历史：八个 playbook 里只有 `04` 进过 1 次） | `.tools/tactics-in-briefs.mjs` | | |
| P15 | 城破当回合 `take-the-city` 是否终于触发（历史 0 次）；池空却无人可进时 `cover-the-capture` 是否触发 | 规则普查（G3） | | |
| P16 | 目标无法抵达（海峡无 `TECH_SHIPBUILDING` / 第三方挡住要道 / 控制区锁路）时，换**同一邻居**的下一座可到达城市，且日记写下原因 | directive 2026-10-02 裁决 | | |

---

## 3. 逐回合观察日志（实战填写）

每回合一行，四列都要有内容；**"工具说了什么"与"规则说了什么"分开记**，因为两者的失败模式不同。

| 回合 | 关键调用（工具 + 目标） | 工具打印的关键行（照抄） | 当回合红的规则 / 阻断 | 决定与理由（谁定的） |
|---|---|---|---|---|
| T | | | | |
| T+1 | | | | |
| T+2 | | | | |

要顺手留下的东西（打完之后没有它们就没法复查）：

- 每一回合的 `end_turn` 结果（`CHECK FAILED` / `TURN START` / 各战斗块都在里面）。
- 日记行（tactical 列里应出现"哪座城、哪一步、为什么"）。
- 宣战那一回合的 `get_diplomacy` 原始输出（确认 WAR 标志，不靠假设）。

---

## 4. 执行顺序（照着走，别跳）

1. `get_game_overview` → 读 **TURN START**；再读 `prompts/tasks/tmp/*.md`。
2. `get_units` + `get_map_area`。
3. 看到 `IN SIGHT` / `NEW TARGET` **立刻** `get_target_report(x,y)`（未宣战也能跑）。
4. `get_reinforcements(x,y)` 补"哪一回合能到"。
5. `get_staging_plan(x,y)`：拿 `RALLY x,y d3`、`ASSEMBLY FIRST`、`arrive T+n`、`ASSAULT OPENS on T+n`。
6. 过**清单四项**：命名目标可打穿 / 攻城器械已集结（1-3 门按算术、2 近战、1 反骑兵、4 远程、1 骑兵，
   不造也不上阵撞锤与攻城塔）/ 宜居度为正 / `gold_per_turn` ≥ +10。
   再套 2026-10-02 的裁决：**打不赢的攻城战不开打，等攻城部队集结后开始**。
7. 集结：远环位先发，最近的最后；每条 move 之间重读 `get_units`；`STOPPED_MID_PATH` 先重发该单位。
8. 宣战（`DECLARE_WAR`）→ **当回合只占位**。
9. 下一回合开火：攻城砸墙 → 远程打血池 → 近战/骑兵走进去；池空当回合入城。

---

## 5. 打完之后怎么判定

```
node .tools/rule-census.mjs         # 哪些规则真的红了，哪些仍然从未触发
python .tools/block-census.py       # SIEGE POSTURE / SIEGE FIRE / TAKE THE CITY 等块的出现情况
node .tools/tactics-in-briefs.mjs   # 有没有任何 playbook 真的进了顾问简报
python scripts/fix-text-encoding.py --check
```

判定要回答的五个问题（每一问都必须给数字或原文，不能给印象）：

1. **发现有没有抵达？** `IN SIGHT` 与 `NEW TARGET` 各出现了几次、在哪一回合。
2. **学说有没有抵达？** `tactics/07` 进顾问简报了吗（P14）；如果没进，是哪一环断的。
3. **集结在宣战之前完成了吗？** `ASSAULT OPENS on T+n` 的 n，与宣战回合的差；有没有 `ZOC STOP` 把
   n 推后（P6）。
4. **规则抓到了什么、漏了什么？** 把当回合红过的规则列出来，与"这一回合真正做错的事"对照；特别是
   P13（没有任何东西阻止一次没准备好的宣战）与 P15（占领那一步是否终于有护栏触发）。
5. **清单四项是否被真正使用？** 拿日记与 `get_target_report` 的输出对照：四个数字有没有出现在决定之前。

---

## 6. 已知的失败模式（观察时优先盯这些）

- **发现被当成了开战信号**：`NEW TARGET` 的尾句已经写明"看见它开始的是分析，不是战争"，但没有任何
  规则拦得住一次过早的宣战（P13）。
- **"宣战前集结"落在进不去的格子上**（P10），于是集结其实发生在宣战之后，时间表整体后移。
- **ZOC 把时间表吃掉一回合**（P6）——本轮之前这件事只能在事后从 `STOPPED_MID_PATH` 里看出来。
- **编制规则在和平期一直红**（P9），被误读成"该开战了"；它们说的其实是"队伍没配齐"。
- **占领那一步无人看管**（P15）：池空之后没有可占领单位相邻，城市回血，整轮火力白打。

---

## 7. 状态

- 本文件写在开战之前；第 2 节的勾选栏与第 3 节的日志为空。
- 开局之后、确定目标之前，先用 `scripts/temp-task.py` 把这次的**作战对象**立成一个临时任务
  （五行列头 + `done when:` + `expires:`），这样它在会话里是"in force"，而不是又一份躺在
  `docs/` 里没人读的记录。
