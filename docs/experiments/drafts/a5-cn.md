军事生产力实验的**第五次尝试 A5**（设计见 `docs/experiments/README.md` 第 3 节）。A1-A4 的记录是 `001-attempt-A1.md`、`002-attempt-A2.md`、`003-attempt-A3.md` 和 `004-attempt-A4.md`；跨尝试报告是 `RETRO-2026-09-29.md`。

## 开局：共享起点

0. `get_game_status`。**本次尝试必须从实验的共享起点测量**：`evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`。如果棋局不在它上面，**就读入这个存档**（`restart_and_load` 或存档列表），并在日记里写明读入的存档停在哪一回合。在别的位置上跑 A5，它的数字就与 A1-A4 不可比——那是实验唯一承受不起的事。
1. 然后 `get_diary` 与一次 `scripts\orient.py` 读取。

## 唯一变量：砍伐的去向

**A5 把砍伐送进单位而不是基础设施：`tactics/01` 与 `tactics/08` 的地貌移除，全部花在战争生产城的军队队列上，由拥有 `Groundbreaker` 能力的马格努斯总督主持（在他就任的城市里，地块收获与地貌移除的产出 +50%），而在别的情况下，同样的建造者次数会花在那座城的基础设施上。** `README.md` 的 A5 行把这个变量写成*"马格努斯的 Groundbreaker：砍伐进入单位而不是基础设施"*，把预测写成*"编成提前 5 回合以上到达，且 T60 时经济落后不到 5 回合"*。其余全部保持不变：共享起点、设置（中国/秦始皇、王子、盘古小图、快速、两个对手）、**修正后**的 `tactics/01`（siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1，撞车仅在已拥有时参战），以及战争计划。

这个变量的代价是：建造者次数花在产能而不是改良设施上、地貌本身以及它们本会在余下整局里持续带来的产出，还有建造者离开复利城市所需地块的那些回合。它应当买到的：编成的攻城一半比 A2 的 T55 早五个回合以上到位，因为一次砍伐就是队列不必等待的产能。

**这个前提条件必须记录，不能假定。** `Groundbreaker` 是马格努斯的 0 级能力（`DLC/Expansion1/Data/Expansion1_Governors.xml:40` 与 `:151`，`Level="0" BaseAbility="true"`，描述为 "+50% yields from plot harvests and feature removals in city"），所以它随任命一起到来，而不来自总督点数。记录里要写明 `appoint_governor` 回执的那一回合、`assign_governor` 把他放进战争城的那一回合，以及 `get_governors` 在那里读到 `established=1` 的那一回合。`get_governors` 打印的 `GOV_PROMO` 行只列出尚未拥有的晋升，所以该能力已经生效的证据是 `GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER` 已从那个列表消失，且用它调用 `promote_governor` 回答 `ERR:ALREADY_PROMOTED`——那是这个能力的记录，而不是一次需要报告的失败。

## 开局建造被钉死

`SCOUT` → `SLINGER` → `SETTLER` → `BUILDER`，与 A3、A4 相同，记录必须逐条写明执行者是否照做。

**这条钉死是可比较性的条件，不是偏好。** 如果执行者的前四个生产订单不是按该顺序的 `SCOUT`、`SLINGER`、`SETTLER`、`BUILDER`，记录就在这一行写明偏离的订单及其回合，并且本次尝试与 A4-A7 **不可比**：它要从共享起点重跑，记录还要写明哪一个是作废的会话、重跑从哪里开始。为偏离给出学说上的理由并不够——A3 的那次跑就有一个，仍然破坏了钉死。变量是**砍伐的投向**，不是开局。

## 假设，以及证伪它的数字

`README.md` 为本次尝试写的窗口行是*"编成回合对照 A2 的 T48/T53/T55，以及 T60 时的经济"*，上界是*"拿下一座城或 T70"*。A2 的三个数字是：工程学与两门弩炮都在 **T48** 下单，第一门弩炮 **T53** 完成，第二门 **T55**（`002-attempt-A2.md`），而 A2 的第一个经济订单出现在 **T55**。

| # | 预测 | 何时被证伪 |
|---|---|---|
| Q1 | 在修正后的表下，编成 **T60 前完整** | T60 时的编成在任一必需名额上不足（`siege 2 / melee 2 / anti-cavalry 1 / ranged 4 / cavalry 1 / recon 1`，撞车条件式），由插桩从日记自己的 `unit_composition` 算出 |
| Q2 | 编成至少比 A2 的 T55 完成早 **5 个回合，即在 T50 前**到位 | 插桩读出的编成回合（每回合从日记的 `unit_composition` 读）是 T51 或更晚，或它在窗口内从未达到 |
| Q3 | 经济落后 **不到 5 个回合**：**工程学闸门之后**第一个 `BUILDING` 或 `DISTRICT` 订单在 **T60 前**落地（A2 的是 T55，即它 T48 闸门之后排的粮仓） | 日志里闸门之后第一个 `BUILDING` 或 `DISTRICT` 订单是 T61 或更晚，或日志里一个都没有。**这个度量刻意取在闸门之后**：A2 自己的第一个非单位订单是 T28 的粮仓，比工程学存在早了二十个回合，把问题读成"第一个非单位订单"就会把它当成经济的答案（插桩曾经如此，直到 `test_a5_q3_reads_the_economy_after_the_gate_not_before_it` 把它钉住）。日志记录的是城市被要求造什么；日记的 `cities`/`districts` 两列是交叉核对 |
| Q4 | 军费付得起：`carrying-capacity` 红回合 **少于十次** | 规则红十次以上。同时报告日记自己的 `gold_per_turn`，因为两个度量彼此不一致：规则只从 T60 起评估（`prompts/checks/turn-checks.md`），而本次尝试在 T70 结束，所以日记的数字才是覆盖整个窗口的那一个，而 A1 与 A2 在它们自己的每一回合都低于 +10 地板 |

## 按顺序做什么

1. **先侦察**（`tactics/07` 的 Gate 0，也是修正表的侦察行）：Scout 向西、向西北，用 `get_map_area` 看地块，第一次攻击估值或 `get_staging_plan` 看池子。A5 的问题就是编成回合，所以只要城够得着就行；城墙读到什么就是什么。
2. **在第一次砍伐之前把马格努斯放进战争城。** 先 `get_governors`（它会打印描述为 `+50% yields from plot harvests and feature removals in city` 的那条 `GOV_PROMO` 行），再 `appoint_governor("GOVERNOR_THE_RESOURCE_MANAGER")`，然后 `assign_governor(...)` 到战争城，并记录任命回合、派遣回合，以及读到 `established=1` 的回合。窗口内他不离开那座城。
3. **工程学 → `UNIT_CATAPULT`，早于任何经济建筑**（H1；它在 A2 的 T48 成立），并让战争城的队列在**整个砍伐窗口**里始终装着一个**单位**：砍伐把产能存入队列当时装着的东西，所以 `tactics/08` 的分工就是框架——战争城造军队，其余每座城复利——记录要写明每次砍伐时在生产的是什么。
4. **把砍伐送进军队，每一次砍伐单独一行记录**：城市、地块、地貌、回合、产能进了哪个队列项，以及建造者剩余的次数。`remove_feature` 在所属城市环之外的地块上会被拒绝，所以每次砍伐都要写明城市与地块，并在每次之后重读编成表。
5. **按 `tactics/04`/`05` 行军与集结，按 `tactics/06` 开火**：屏护在前、攻城在射程 2、最后填满开火格，然后宣战、当回合站位，在序列能开火的每一回合都开火，同时用富余单位剪断供给线。
6. **每十回合**：写 `ESTABLISHMENT:` / `WAR READY:` / `ENEMY SEEN:`，并用数字回答 `10-TURN REVIEW` 的三个问题。按插桩解析的形状写编成行（`scripts/experiment-report.py` 里的 `SELF_REPORT_RE`）：`ESTABLISHMENT: siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1 at T<n>`，并在旁边写上修正表另外两行，写成 `(anticav x/1, recon y/1)`。即使撞车是条件式的，`ram c/1` 这一格也要留着——没有它的行根本不会被读取——而解析器不读 anticav 与 recon，所以那两行只是报告，不计分。

## 终点，以及要留下什么

- 尝试在**拿下一座城**（`city_action` 回执读到 `KEEP|`）或棋局到达 **T70** 时结束，以先到者为准。`expires:` 为 T75。
- 结束时取快照：
  `.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 --run <本会话> --from 1 --to <最后一回合> --step 10 --verdict --questions a5 --save docs/experiments/A5-final.json`
  （`--questions a5` 就是本次尝试上面自己的四行，而且这个模式已经在插桩里了——它是在本次尝试发布之前加好并验证过的），跑
  `.venv\Scripts\python.exe scripts\experiment-report.py --compare docs\experiments\A4-final.json docs\experiments\A5-final.json`，
  写 `docs/experiments/005-attempt-A5.md`，并把 A5 的半程写进复盘。
- 然后退役本文件，并在日记的 `tooling` 行写明结束于哪一回合。

## 这个项目已经付过代价的诚实条款

- **回执不是结果**：命中的攻击写过 `damage dealt:none`，攻占移动在单位已站上城格时回过 `BLOCKED`。要看之后的读取与汇总字段。
- **说清一个主张用的是哪个度量**——金币地板有三个数，彼此不一致。
- **日记与 A1-A4 共享**；插桩按会话时间归属行。
- **一次砍伐的产能只有在地貌真的消失时才入账**，而在城市所属环之外的地块上 `remove_feature` 会被拒绝，所以记录要为每次砍伐写明城市与地块。没有工具会打印入账的多少：`remove_feature` 回答 `OK:REMOVING_FEATURE|<feature> at x,y`，所以获得的产能要从该项目前后的回合数读出，否则记录就说它读不到，而不是去估算。
- **被钉死的开局已经被破坏过一次**（A3：把 `UNIT_WARRIOR` 作为 T15 的第四个订单，当时钉死已经生效，`planning` 行里给了学说上的理由，却完全没提这条钉死），这就是为什么现在这条钉死带着上面那条重跑后果。
