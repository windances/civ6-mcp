> 本文件是 `030-030-military-production-attempt-a1.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

# 尝试 A1——按原文执行军事生产力教条

这是 `docs/experiments/README.md` 定义的实验的第一次尝试。**本次唯一变量是"没有变量"**：完全按
`prompts/tactics/01-unit-production.md` 的编制表与生产顺序打，让后面的尝试有一个可移动的基线。

## 设置（从运行中的游戏回读，不是从设置界面抄）

| 参数 | 值 | 读数来源 |
|---|---|---|
| 文明 | 中国，秦始皇（大一统） | `PlayerConfigurations[0]` = `LEADER_QIN_ALT` / `CIVILIZATION_CHINA` |
| 对手 | 2 个：澳大利亚（约翰·柯廷）、毛利（库佩） | 玩家 1、2 是仅有的其他主要文明 |
| 难度 | 王子 | 设置界面 |
| 地图 | 盘古大陆，小 | 设置界面；槽位只有六个座位 |
| 速度 | 快速 | 设置界面 |
| 规则集 | 风云变幻 | `RULESET_EXPANSION_2` |
| 起始 | 第 1 回合、公元前 4000 年、未做任何操作 | `Game.GetCurrentGameTurn()` = 1 |
| 可重放 | `evals/saves/ATTEMPT-A1-T1.Civ6Save` | 第 1 回合从实机存出 |

## 本次要测什么

被测教条是 `prompts/tactics/01-unit-production.md`（编制表 + 生产顺序），战争经济看
`prompts/tactics/08`。它的可证伪主张是 `docs/experiments/README.md` 里的 H1-H6。**本次照原文打**，
中途不许"顺手优化"——改了变量就是另一次尝试。

**判定的两个数字**，都要写进日记并带上发生的回合：

1. **军队首次满足编制的回合**（攻城 2 / 近战 2 / 撞车 1 / 远程 4 / 骑兵 1，从日记的
   `unit_composition` 读）；
2. **第一座敌城被保留（keep）的回合**（`city_action` 回包里读 `KEEP|`）。

## 每十回合

在日记里用数字回答 `10-TURN REVIEW` 的三问，并在 `strategic` 里加两行：

```
ESTABLISHMENT: siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1 at T<n>
WAR READY: <编制补齐的回合，或 not yet>
```

## 结束条件

第一座敌城被保留的那回合结束；到第 80 回合仍未得手也结束。结束当回合退役本文件
（`scripts/temp-task.py retire 030 --done --turn N`，或 `--expired`），并用
`scripts/experiment-report.py --game china_<seed> --step 10` 的输出写出
`docs/experiments/001-attempt-A1.md`。

第一座城拿下之前不开第二场战争。侦察、铺城、基建和军队一样是本次的任务：要回答的问题是"这支
军队让帝国付出了什么"，而只有帝国把该做的事也做了，这个问题才答得出来。
