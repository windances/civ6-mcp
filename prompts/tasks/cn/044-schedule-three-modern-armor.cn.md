> 本文件是 `044-schedule-three-modern-armor.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

## 人类指令原文

不取消当前生产项目，排产3辆现代坦克，生产完成，任务结束

## 为什么是「现代装甲」而不是「坦克」

`UNIT_TANK` **不在任何城市**的建造列表里：它的升级型已经存在，游戏因此把坦克隐藏了。T344 实测，
四个城市的 `get_city_production` 都提供了 `UNIT_MODERN_ARMOR（造价 680，购买 2310g）`，而没有一个
提供 `UNIT_TANK`。帝国当时两者都是 0 辆。所以这三辆是 `UNIT_MODERN_ARMOR` —— 680 生产力、95 战力，
并且**需要 `RESOURCE_URANIUM`（铀）**。

## 「不取消」在机制上意味着什么

`set_city_production` 设置的是城市的**当前**项目。工具无法把它追加到后面 —— Lua 侧只有
`GetBuildQueue`、`GetTurnsLeft`、`GetProductionCost` 和一个 `RemoveAt`，没有任何插入操作。所以装甲
是在**当前项目完成的那一回合才开始造**，绝不是排在它后面，一座城的期限因此是：

    总计 = 当前项目的剩余回合 + 游戏为该装甲报出的回合

## 怎么挑这三座城

先读高产值城市的 `get_city_production(city_id)` —— Abydos、Astrakhan、Chengdu、Beijing —— 因为
T344 时它们的当前项目都只剩 1 到 2 回合，而且造装甲比下面四座快得多。取总计最小的三座。

**要用游戏报出的回合数，不要自己算。** T344 实测：ỉwnw 的 `Prod` 只有 34，却为一个 680 造价的单位
报 14 回合；Yerevan 的 `Prod` 是 32，报 18 回合 —— 说明单位生产加成已经包含在游戏的数字里，而
`造价 / Prod` 恰好会在最要紧的那几座城上把工期算长。

T344 时队列为空（因此唯一真正量到过报价）的四座：

| 城市 | 当前项目 | 装甲报价 | 总计 |
|---|---|---|---|
| Yerevan | WORKSHOP，剩 3t | 18t | 21t |
| Jiaodong | BUILDER，剩 4t | 18t | 22t |
| ỉwnw | INDUSTRIAL_ZONE，剩 10t | 14t | 24t |
| Brussels | COAL_POWER_PLANT，剩 5t | 22t | 27t |

## 这个任务不碰什么

- **太空竞赛的城市，绝不碰。** 西安距 `PROJECT_LAUNCH_MOON_LANDING` 还有 9 回合，圣彼得堡距
  `DISTRICT_SPACEPORT` 还有 26 回合。科学胜利是既定战略；这两座既不能被打断，也不由本任务加入。
- **任何城市的当前项目。** 一个都不替换。当前项目太长的城就不在候选里 —— 换一座。
- **铀。** 在决定第三辆之前读 `get_empire_resources`。现代装甲需要 `RESOURCE_URANIUM`；如果库存不够
  三辆，就造成库存能覆盖的数量，并在日记里说明，而不是把某条队列卡死。
- **金币。** 购买价是每辆 2310g，而金库一直在 700 以下。本任务排的是**生产**，它不授权购买，也不覆盖
  指令里的花钱规则。

## 完成

当 `get_units` 显示三辆 `UNIT_MODERN_ARMOR` 时，任务在那一回合完成 —— 用
`scripts/temp-task.py retire <nnn> --done --turn <N>` 退休它，别做多余的事，并记录是哪三座城造的、
每条队列为此让出了什么。
