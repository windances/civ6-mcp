> 本文件是 `035-attempt-a4-the-encampment-before-the-second-siege-unit.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

军事生产力实验的**第四次尝试 A4**（设计见 `docs/experiments/README.md` 第 3 节；A1、A2、A3 的记录是 `001-attempt-A1.md`、`002-attempt-A2.md`、`003-attempt-A3.md`，跨尝试报告是 `RETRO-2026-09-29.md`）。

## 开局：用共享起点，而不是棋局碰巧停在的位置

0. `get_game_status`。**本次尝试必须从实验的共享起点测量**：`evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`。如果棋局不在它上面，**就读入这个存档**（`restart_and_load` 或存档列表），并在日记里写明读入的存档停在哪一回合。在别的位置上跑 A4，它的数字就与 A1-A3 不可比——那是实验唯一承受不起的事。
1. 然后 `get_diary` 与一次 `scripts\orient.py` 读取。

## 唯一变量：营地在战争城、在第二门攻城单位完成之前造出来

**A4 把营地造出来——造在战争城，并且在第二门攻城单位完成之前——这是 `prompts/tactics/08-war-and-the-home-front.md:81` 的读法，而 directive 的建造顺序把它排在最后，"Encampment only when a war is actually near"。** 其余全部保持不变：同一存档、同一设置、**修正后**的 `tactics/01`（侦察 1、反骑兵 1、撞车条件式、siege 2 / melee 2 / ranged 4 / cavalry 1）、同一套战争计划、同一类目标。

**旧前提为什么死了，而且这是一次测量。** 本次尝试早先的草稿说它在第二座城*之后*才造营地，"而学说与 A3 是在它之前造"。这是假的：**整个项目里没有任何一次尝试造过营地。** 本局每一份会话日志——`vigilant-sable-longbow-78`、`sacred-garnet-vault-35`、`pale-pearl-aqueduct-92`、`volcanic-indigo-caravan-23`、`flint-indigo-rampart-32`、`crumbling-emerald-parapet-16` 和 `eternal-scarlet-catapult-86`——里 **`set_city_production` 对 `DISTRICT_ENCAMPMENT` 的订单数为零**；这些日志里唯一一次出现这个字符串原文的，是 A2 在 T68 的一条 `get_city_production` 列表，那不是订单。"第二座城之前"是一条谁也没跑过的分支，所以旧的 A4 会拿它的变量去跟"什么都没有"比。

**为什么没人造：学说自己说了两套话。** `tactics/08` 把营地给战争城——"The war city - the highest-production city - builds units, siege and the Encampment/Barracks, and nothing else for the duration"（`prompts/tactics/08-war-and-the-home-front.md:81`）——而 `prompts/strategies/china-conquest/directive.md:63` 说 "Encampment and Barracks in the highest-production city"，同一套分工又见 `directive.md:331`（那句话从 `:330` 开始）。但同一条 directive 的建造顺序说的是 "growth first ..., then a **Campus** ..., then Commercial Hub, then Government Plaza, then **Encampment only when a war is actually near**"（`:299`）。A4 第一次执行前一种读法。

被测的主张来自 `tactics/01:74-76`（`prompts/tactics/01-unit-production.md`）：大将军主要出自营地，而大将军给 2 格内的陆军 **+1 movement and +5 combat strength to land units within 2 tiles**，所以"营地不只是防御，它是军队能买到的最便宜的战斗力加成"。A4 问的是：这道光环，值不值营地和它的大将军从战争城队列里拿走的那几回合。

## 开局建造被钉死

`SCOUT` → `SLINGER` → `SETTLER` → `BUILDER`，与 A3 相同，记录必须逐条写明执行者是否照做。变量是**营地在战争城队列里的位置**，不是开局。

**这条钉死是可比性的条件，不是偏好。** 如果前四个生产订单不是按 `SCOUT`、`SLINGER`、`SETTLER`、`BUILDER` 的顺序下的，记录就要在这一行写明偏离的是哪个订单、在第几回合，并且这次尝试与 A5-A7 **不可比**：它要从共享起点重跑，记录要写明哪个会话是被丢弃的那次、重跑从哪里开始。只给一个学说上的理由是**不够**的——**A3 就给了理由，却仍然违反了钉死**（它的第 4 个订单是 T15 的 `UNIT_WARRIOR`，当时钉死已经发布并生效，而它的 `planning` 行从头到尾没提过钉死），所以这条规则现在带的是重跑后果，而不再是"请你解释"。

## 假设，以及证伪它的数字

| # | 预测 | 何时被证伪 |
|---|---|---|
| Q1 | 在修正后的表下，编成 **T60 前完整** | T60 到来时任一必需名额不足 |
| Q2 | **营地在战争城完成，并且在第二门攻城单位完成之前**，记录要带上：地区所在地块、下单回合、完成回合，以及游戏**第一次**允许建造它的回合（`get_district_advisor` / `get_city_production`，连那次读取自己报出的前置条件一起记——科技要求是读出来的，本文件不作断言） | 窗口结束时没有任何 `DISTRICT_ENCAMPMENT` 完成，或它在第二门 `UNIT_CATAPULT` 之后才完成——在攻城组之后才到的光环，不可能是改变进攻的那件东西 |
| Q3 | **战争开打之前招到一位大将军，并且从不激活它**；记录要写明招到它的回合，以及它相对攻城单位站在哪里 | 第一次宣战之前没有招到任何大将军，或对其中一位调用了 `activate`。到第一次开火时还没出大将军的营地，是这个主张的机制缺席，而不是它的代价；而激活大将军会**注销光环**（`AGENTS.md`：光环的价值在于单位活着，`activate` 会消耗它）——若真的激活了，记录要明说 |
| Q4 | 军费付得起：`carrying-capacity` 红回合 **少于十次**，两个度量都报告，并把攻占对照 **A3 的攻占回合**（`003-attempt-A3.md`） | 规则红十次以上，或日记自己的 `gold_per_turn` 不低于 +10 地板（两个都报，如前两次尝试那样）；攻占这一半则在 A3 的攻占回合过去而本次日志里没有 `KEEP|` 时被证伪——若 A3 根本没能拿下城，记录就写明，并改用 **T80** 作界 |

## 按顺序做什么

1. **先侦察**（修正表的侦察行，也是 `tactics/07` 的 Gate 0）：Scout 向西、向西北，把它找到的每个城都读一遍——`get_map_area` 看地块，第一次攻击估值或 `get_staging_plan` 看池子。**有城墙的目标优先**（那是 A3 的变量，有墙的城也更费攻城组），但不要为找它花掉窗口：A4 的问题是营地的回合数与那道光环，所以只要城够得着就行。
2. **尽早建第二座城**——由被钉死的 `SETTLER` 去建——并在日记里写明选址与回合。它不是变量：第 3 步的战争城是按产能选的，不是按哪座城先来。
3. **选定战争城，并在游戏一允许就把营地排在那里，而且早于第二门 `UNIT_CATAPULT`。** 战争城就是产能最高的那座城（`tactics/08:81`）。`get_district_advisor` 与 `get_city_production` 是回答"游戏什么时候允许建造、那次读取报出的前置条件是什么"的读取；"允许建造"、"下单"、"完成"三件事各自都要记录回合与来源读取，并记录地区所在地块。
4. **工程学 → `UNIT_CATAPULT`，早于任何经济建筑**（H1；它在 A2 的 T48 成立，A3 再测一次）。
5. **按 `tactics/04`/`05` 行军与集结**——屏护在前、攻城在射程 2——然后宣战、当回合站位，**能开火的每回合都开火**，同时用富余单位剪断供给线。让大将军跟着堆叠走：光环只覆盖 2 格内的陆军，而被激活的大将军就是不在了的大将军。
6. **每十回合**：写 `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:`，并用数字回答 `10-TURN REVIEW` 的三个问题。`ESTABLISHMENT:` 行里每个角色的分子是**已在场的单位**——仪器会拿它与地图对照，不一致就判 `MISMATCH`。**还在生产中的单位不算持有**：把它写在记号后面、用自己的话说明（`siege 1/2, 1 building due ~T48`），**不要写进分子**。已有两次尝试把 `siege 1/2 building` 写成分子、而实际一门攻城单位都没造成，被判为虚报。

## 终点，以及要留下什么

- 尝试在**拿下城**时结束——要么 `city_action` 回执读到 `KEEP|`，要么游戏自己结算了攻占、移动回执读到 `CAPTURE_MOVE ... CITY TAKEN`（这种情况下永远不会出现 `KEEP|`，`resolve_city_capture` 会回 `NO_PENDING_CITY`；以城市列表为确认）——或棋局到达 **T110** 时结束，以先到者为准。`expires:` 为 T115。
- 结束时取快照：
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <本会话> --from 1 --to <最后一回合> --step 10 --verdict --questions a3 --save docs/experiments/A4-final.json`
  （`--questions a3` 是**插桩读**的那一半——它的 Q2 读城墙池、Q3 读第一次 `KEEP|`、Q4 读金币地板；而本次尝试的 Q2 与 Q3 是**记录读**：营地从日志里具名 `DISTRICT_ENCAMPMENT` 的 `set_city_production` 行读，大将军从 `get_great_people` 与单位读取读），跑
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A3-final.json docs\experiments\A4-final.json`，
  写 `docs/experiments/004-attempt-A4.md`，并把 A4 的半程写进复盘。
- 然后退役本文件，并在日记的 `tooling` 行写明结束于哪一回合。

## 这个项目已经付过代价的诚实条款

- **回执不是结果**：命中的攻击写过 `damage dealt:none`；攻占移动在单位已站上城格时回过 `BLOCKED`。要看之后的读取与汇总字段。
- **说清一个主张用的是哪个度量**——金币地板有三个数，彼此不一致。
- **日记与 A1-A3 共享**；插桩按会话时间归属行。
