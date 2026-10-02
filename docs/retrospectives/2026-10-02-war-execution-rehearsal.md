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
| P1 | 城市第一次可见的那次**移动回复**里出现 `IN SIGHT ... [City: 名字] ... get_target_report(x,y)` | `narrate.narrate_sight` | ⚠️ **路线 A 观测不到** | 不是功能坏了：`IN SIGHT` 挂在 `GameState.spatial` 上（`game_state.py:469` 的 `_revealed_seeded` 门），而 `SpatialTracker` **只在 `server.py:318` 构造**。`play-turn.py` 用 `GameState(conn)`，`spatial is None` → 整个 post-move 可见性块被跳过。T95 侦察兵移到 (64,25)、与毛利重战车相邻，移动回复里没有任何 `IN SIGHT`。要观测这条只能走 orchestrator（路线 B） |
| P2 | 同一回合的 `end_turn` 出现**且只出现一次** `NEW TARGET (T<n>) ...` | `end_turn` 的进程内差分（首次扫描只播种） | | |
| P3 | **未宣战**状态下 `get_target_report` 就能给出 `walls N/100`、`city HP N/200`、驻军、三格内敌军，以及每格的 `FIRE` / `FIRE?` / `NO LINE OF SIGHT` | 工具；Gate 1-3 | ⏳ 待测 | 本轮没有可用的**外国城市**格（Anshan 城本身在雾里，见 P7），所以还没有一次真正的 target report |
| P4 | 若目标格只是 `revealed`（已揭示但不当前可见），报告会明说"不是读数"，且**不给**墙/池/驻军 | `narrate.narrate_target_report` | | |
| P5 | 宣战前 `get_staging_plan` / `get_pathing_estimate` 的 `arrive T+n` **已含地形代价**（`cost N mp`），但**不含敌方 ZOC 停顿** | `_marchZoc` 只扫 `IsAtWarWith` 的玩家 | | |
| P6 | 宣战后**同一个环位**的 `arrive T+n` 可能 +1，并出现 `ZOC STOP at (x,y) on turn +k` | 同上；本轮新加的输出 | | |
| P7 | 和平期 `SIEGE POSTURE` 报 `city_distance`（集结参照），`war_city_distance` 为 999；`SIEGE FIRE: n/m` 在宣战前不具约束力 | 本轮修复（战争门 + 敌城口径） | ✅ **确认（更强）** | T96 的 `SIEGE POSTURE` 三行全是 `city - (no visible enemy city)`：**连 Anshan 的城都在雾里**，所以战争状态与城市可见性是两件事。三门投石车因此既没有 `SIEGE FIRE` 也没有目标可算 |
| P8 | 宣战前 `concentrate-the-siege`、`upgrade-the-siege`、`upgrade-the-unwatched`、`one-garrison-per-city` **静默**；宣战那一刻起可红 | 规则里的 `metric(at_war) >= 1` | | |
| P9 | `siege-train` / `ranged-mass` / `melee-screen` / `counter-the-cavalry` 在 T90 之后**和平期也会红**（盯编制，不盯战争） | 规则的 `when` 无战争门 | ✅ 确认，且**本轮它们全安静** | T96 的红灯是 `use-your-attacks`、`screen-the-siege`、`match-their-melee`、`dynasty-cycle-wonder`。编制类没红是因为队伍本来就是满的（3 投石车 / 4 近战 / 1 长矛 / 4 远程 / 1 重战车）——**规则红不红取决于缺口，不取决于是否在打仗**，这正是 P9 想说的那一半 |
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
| **T95** | `orient --only overview,diplomacy` → 唯一已知文明 **Māori**（NEUTRAL，不战）；`units`/`cities` 读到 4 城 / 16 单位；`play-turn scan 63 23 5` → 发现 `**[Māori HEAVY_CHARIOT]**` @(63,25) | `turn=95 gold=13.7 gpt=+6.2 sci=27.4 ... unit_breakdown={'Warrior': 4, 'Catapult': 3, 'Archer': 3, ...}`；地图行 `(63,25): GRASS FLOODPLAINS_GRASSLAND River {F:3 P:0} **[Māori HEAVY_CHARIOT]**` | 未读（本轮没有取 end 结果） | 探索：侦察兵南下找毛利城市 |
| T95 | `play-turn move 0 64 26` | `MOVING_TO\|64,26\|from:63,23\|now_at:64,25\|(moved dx:+1 dy:+2)\|STOPPED_MID_PATH (moves exhausted)`，随后 `read back: ... mv1.0` | 无 | **P1 观测不到**（见上）；`STOPPED_MID_PATH` 与"还剩 1.0 移动力"同时出现，是引擎的量化行为，不是 bug |
| T95 | `play-turn attack 0 63 25`（打毛利） | `REFUSING: no legal attack on (63, 25) from (64, 25) ... Legal targets from here: none` | 无 | 脚本在调用引擎前先自查合法性，所以**看不到 `ERR:` 原文**；于是用适配器直调（下一条） |
| T95 | 直调 `gs.attack_unit(0, 63, 25)` | `Error: NOT_AT_WAR\|Cannot attack UNIT_HEAVY_CHARIOT — you are at peace with Māori Empire. Declare war first or target a different unit.` | 无 | 和平期攻击的**工具级**拒绝确认；这正是指令里"和平期什么都动不了"的那一条 |
| T95 | `play-turn attack 14 51 14`（弓手打 Anshan 剑士） | `RANGE_ATTACK\|target:UNIT_SWORDSMAN at (51,14)\|pre_hp:100/100\|range:2 dist:1\|est damage dealt:~13` → `Post-combat: ~87/100` | 无 | 远程不吃反击，安全的一击 |
| T95 | `play-turn attack 11 59 13`（重战车打蛮族战船） | `Error: MELEE_CANNOT_ATTACK_AT_SEA\|UNIT_GALLEY is at sea ... manual:723`（脚本先印了 `- REFUSED BY THE RULES:` 说明） | 无 | **发现 1**：`unused_attacks` 把这个攻击列为"可用"，攻击路径却直接拒绝 |
| T95 | 直调 `gs.city_attack(262147, 59, 13)`（奥克兰港里的战船） | `Error: NO_WALLS\|City has no walls — build Ancient Walls first` | 无 | **发现 2**：AGENTS.md 说"有城墙的城市"能打出最便宜的一击；奥克兰没有墙，所以这一击根本不存在 |
| T95 | `play-turn attack 18 54 9`（轻骑兵打 Anshan 重装步兵 CS 48） | `Est damage to defender: ~3` / `Est damage to attacker: ~177` / `-> WARNING: attacker likely dies!`，然后 `RANGE_ATTACK ... est damage dealt:~3` | 无 | **发现 3**：远程攻击印的是 `Combat Estimate (Melee)`，连"攻击者可能阵亡"的警告都是错的（远程不吃反击） |
| T95 | `play-turn end` → `end --force` | 守卫先拒：4 个未用攻击；`--force` 后适配器仍回 `REFUSED\|UNUSED ATTACK (4 unit(s)) ... Nothing was swept.`，但**回合照常推进**：`Turn 95 -> 96` | 无（本回合） | 用 `--force` 丢弃：两个近战对 CS 35 剑士是必亏交换，一个是打不到的战船。理由写进日记行 |
| **T96** | `end` 结果（同上一条的输出） | 敌方回合：`Your Skirmisher (UNIT_SKIRMISHER) took 52 damage! HP: 20/100`；7 条 `THREAT:`（Anshan 2 剑士 + 2 弩手、蛮族战船 + 重装步兵、毛利重战车）；`CHECK FAILED`：`use-your-attacks`、`screen-the-siege`、`match-their-melee`、`dynasty-cycle-wonder`；`BATTLE ASSESSMENT` 列出两队各单位与"concentration: 3 of your units are within 2 tiles ... enough for a kill"；`MATCHUP: their UNIT_MAN_AT_ARMS is CS 45 against our best front-line unit at CS 25`；`SIEGE POSTURE`：两门有屏卫、**一门 EXPOSED**；三单位自愈（Warrior 42→52、Chariot 49→69、Spearman 70→80） | 见左 | 决策交给人类：Anshan 是城邦（指令说城邦不是征服目标），但它已经在我们领土里；2026-10-02 的"不是我们发起的战争就是征服"那条要不要套在城邦上 |
| T96 | `orient --only overview,units` | `turn=96 gold=18.1 gpt=+4.4`；Skirmisher `hp20/100`；侦察兵 100/100；三门投石车 100/100 | — | 下一回合的首要动作：把 Skirmisher 撤出接触、给暴露的投石车补屏卫、用远程火力消耗 Anshan（指令：绝不一对一交换） |
| T96 | 北口袋的纵队后撤（按地形只有一条出路）：`move 16 56 11` → `move 19 56 10` → `move 18 55 10` → `move 21 56 12` | 四次都成功，各 `read back ... mv0.0`（丘陵/森林每格 2–3 点） | 无 | 唯一出口 (56,11) 是一格宽的山口——**正是 `tactics/04` 说的"列队堵自己"**；一次只能挪一格 |
| T96 | `attack 14 51 14`（弓手再打剑士）、`move 7 50 22`（伤兵进耶路撒冷）、`move 17 50 20`、`move 4 54 21` | 剑士 100→84→73（两回合共 27）；Warrior[7] `moved (51,20) -> (50,21) STOPPED_MID_PATH` | 无 | 远程消耗 + 近战不接战（CS 20/25 对 CS 35 是必亏交换） |
| **T96** | **`end` 连续两次都报同一句 `Turn 95 -> 96`，而 `orient` 读到的回合在 95/96 之间摆动** | `REFUSED\|UNUSED ATTACK (3 unit(s)...)`；事件里 `Your Skirmisher took 54 damage! HP: 18/100`；`UNIT_MAN_AT_ARMS CS:45 HP:88/100` | 无（回合没有真正推进） | **发现 4**：回合被弹窗卡住。`whats-on-screen.py` 读到 `NATURAL DISASTER OCCURRING` + `CATASTROPHIC ERUPTION`；`dismiss_popup` 一次清掉 **23 个** 弹窗：`cinematic_camera, NaturalDisasterPopup, InvitePopup ×20`。路线 A 的驱动器**没有** dismiss 命令 |
| T96 | 清完弹窗后重读 | `turn=96`（稳定），全员移动力恢复满格，位置却保留了我刚才的移动结果 | — | **发现 5**：弹窗阻塞期间的读数不一致——同一回合内 Skirmisher 的 HP 读到过 **20 / 72 / 18**，侦察兵的格子读到过 **(64,25)** 与 **(63,23)**；一次 `move 0 65 28` 被解释成"从 (63,23) 走到 (64,25)"（原地），白白花掉移动力 |
| T96 | `attack 18 54 9`（轻骑兵打重装步兵）、`end` → `end --force` | `Est damage to attacker: ~302` / `-> WARNING: attacker likely dies!`，实际 `est damage dealt:~2`；守卫只剩 2 条**打不到**的攻击（两条都是对港内战船的近战）；`--force` 后进入 T97 | 下一回合的 `Action Required`：**Unit available for promotion / Choose a Technology / Choose Production** | 用 `--force` 结束（唯一出口），理由：剩下两条是 `MELEE_CANNOT_ATTACK_AT_SEA`，工具自己会拒绝 |
| **T97** | `orient --only overview,units` | `turn=97 gold=17.1 gpt=+4.5 research=None`；**Skirmisher 已不在编成里**（`Unit Killed`）；Archer[14] `hp39/100`（被 Anshan 弩手 RS40 打掉）；MAA `62/100`（它杀掉轻骑兵时吃了反击）；三辆投石车 100/100、已退出北口袋 | 待读（下一回合开始） | 结论：**A+C 的第一轮代价 = 一辆轻骑兵 + 一个弓手重伤**，换来投石车全部生还、Anshan 两台剑士掉血、重装步兵掉 38 |


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
- **2026-10-02 23:40 起的现场情况**：Civ6 已启动（pid 33900），FireTuner 在 127.0.0.1:4318 监听，
  但**尚未载入对局**：`game_status` 报 `main_menu`，并给出下一步
  `load_game_save("AutoSave_0095")`（最新存档 T95；Continue Game 也是这一档）。
  `game_launcher.load_save_from_menu("AutoSave_0095")` 的菜单导航**只走了一半**：界面已到
  Load Game → Autosaves 列表（`AutoSave_0095` 在第一行），随后在找底部的 Load Game 按钮时报
  `FAILED: Could not find 'Load Game' button`。记下来是因为它本身就是本轮要观察的现象之一：
  **载入流程是可观测的薄弱环节**，与 `docs/game-recovery.md` 那串"看起来像恢复失败、其实是
  载入窗口"的清单同源。
- 本次打法：**路线 A**（不走 MCP，直接用仓库的直连驱动器：`orient.py` / `target-report.py` /
  `staging-plan.py` / `play-turn.py`）。因此第 2 节的 **P14（`tactics/07` 有没有进顾问简报）
  本次无法观测**，会标为"未观测"，不算通过；**P1（`IN SIGHT`）同样观测不到**（见上表）。
- **T97 的现场**：回合 97，金币 17.1 / 每回合 +4.5（低于 +10 底线 → `carrying-capacity` 会红），
  科技待选（Castles 已完成），4 城 28 人口，编成 4 近战 / 3 投石车 / 3 弓手 / 1 投石手 / 1 长矛 /
  1 重战车 / 1 侦察兵 / 1 商队。敌方：**Anshan**（城邦，交战中）2 剑士 84/100、弩手 ×2；
  **蛮族** 重装步兵 62/100、港内战船 100/100；**毛利** 重战车（未交战）。
  待办阻断：`Unit available for promotion`、`Choose a Technology`、`Choose Production`。


---

## 8. 首日现场发现（T95–T96，路线 A）

三条都是**工具行为与它自己的说明不一致**，不是策略问题；它们只有在对局里才会露出来，这也是
这次预演存在的理由。

1. **`unused_attacks` 会把打不到的攻击算作"可用"。** 蛮族战船停在奥克兰港 (59,13)，我们两栖
   单位紧邻它，`end` 的守卫因此每回合拒绝结束回合（`REFUSED|UNUSED ATTACK ... UNIT_HEAVY_CHARIOT@60,14
   -> UNIT_GALLEY@59,13`），而真正去攻击时 `attack_unit` 直接回
   `ERR:MELEE_CANNOT_ATTACK_AT_SEA`（manual:723）。也就是说：**一个合法攻击列表里的条目，工具自己
   永远不会执行**，而唯一的出口是 `--force`（它一次丢掉全部未用攻击，包括真正可打的那几个）。
   **已修（`a68ee9b`）**：两处扫描——`build_unused_attack_query` 与 `build_units_query` 的
   `>> CAN ATTACK` 提示（后者是同一句"两处判据完全一致"的第三次落空）——现在都套用攻击路径自己的
   判据：攻击者是陆上近战（`rs == 0` 且 `Domain == "DOMAIN_LAND"`）、目标在海上
   （`Domain == "DOMAIN_SEA"`）时清掉既有的 LOS 标志。修完当场复验：守卫只剩
   `UNIT_ARCHER@50,14 -> UNIT_CROSSBOWMAN@50,12;UNIT_SWORDSMAN@51,14;UNIT_CROSSBOWMAN@51,15`
   ——一个真能打的目标列表，而不是那艘谁都不碰不到的战船。
2. **城墙是城市打击的前提，而文档把它写成了普遍手段。** `AGENTS.md` 的 Wartime 段说"有城墙的城市"
   能打 2 格内敌人（实测 43 伤害、不吃反击，是帝国里最便宜的伤害）；奥克兰（我们打下来的城邦，
   只有港口）回的是 `ERR:NO_WALLS|City has no walls — build Ancient Walls first`。这条限制是对的
   （手册如此），但"最便宜的伤害"在无墙城市上不存在——措辞需要收紧，否则计划会把它算进输出。
3. **远程攻击印的是近战估计。** 弓手与轻骑兵的 `RANGE_ATTACK` 前面都有一段
   `Combat Estimate (Melee)`，其中"Est damage to attacker"（三次分别读到 **44 / 177 / 302**）以及
   "attacker likely dies!" 对远程单位毫无意义（远程不吃反击，三次都只结算了 `est damage dealt`，
   分别 13 / 11 / 2）。一个只按错误模型给出的估计，比没有估计更容易误导下一条命令。
4. **一个弹窗栈能把整个回合卡住，而路线 A 没有任何东西去关它。** T96 的 `end` 连续两次都回同一句
   `Turn 95 -> 96`，回合号在两次 `orient` 之间摆动；屏幕读到的是
   `NATURAL DISASTER OCCURRING / CATASTROPHIC ERUPTION`。`dismiss_popup` 一次清掉 23 个弹窗
   （`cinematic_camera`、`NaturalDisasterPopup`、**`InvitePopup` ×20**），清完回合号立刻稳定在 96。
   在正常的 MCP 会话里这些由后台 watcher 顺手关掉，`play-turn.py` 里没有对应命令——**任何自然灾害、
   邀请或过场动画都可能让一个直连会话看起来"回合不前进"**。
   **已修（`13e459a`）**：`play-turn.py` 新增 `dismiss` 动词（最多三轮、遇到"没有弹窗"就停，逐轮打印
   清掉了什么；刻意不做无限循环——`end_turn.py` 里就记着"AI 处理期间反复 dismiss 会把 AI 回合挂死"）；
   同时 `end_turn` 的失败路径不再只留一句"still at turn N"，而是**把弹窗层的答案写进 `HANG:` 与最终
   提示**，层上什么都没有时也明说"Lua 看不见游戏窗口之外的对话框"。修完当场又抓到一次：
   `TechCivicCompletedPopup` + `InvitePopup` ×20 正等在那里。
5. **弹窗阻塞期间的读数是不能信的。** 同一回合内：轻骑兵 HP 读到过 **20 / 72 / 18**；侦察兵的格子读到过
   **(64,25)** 与 **(63,23)**；一次 `move 0 65 28` 被当成"从 (63,23) 走到 (64,25)"（原地）而白白花掉
   移动力；清完弹窗后**全员的移动力又都是满的**，位置却保留了我之前下的移动。也就是说：**在回合边界
   被打断时，先读到的那一份快照可能是上一回合的**——计划基于它做，就会像这次一样把移动力花在空气上。
   `AGENTS.md` 已经为城市读数写过"post-combat 读数是估计不是事实"；这一条是它在**单位与回合边界**上的
   同族现象，值得同样写进去。
