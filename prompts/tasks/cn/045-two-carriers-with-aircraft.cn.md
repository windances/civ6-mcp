> 本文件是 `045-two-carriers-with-aircraft.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

## 人类指令原文

不取消当前生产项目，以生产2艘航空母舰以及配套的飞机为目标，排产相关的生产项目，目标达成，任务结束

## 这三个单位到底是什么

| 单位 | 造价 | 需要 | 说明 |
|---|---|---|---|
| `UNIT_AIRCRAFT_CARRIER` 航空母舰 | 540 | `RESOURCE_OIL`（石油）、`TECH_COMBINED_ARMS` | `Domain=DOMAIN_SEA` —— **只能在内陆以外的沿海城市造** —— 而且 **`AirSlots="2"`** |
| `UNIT_JET_FIGHTER` 喷气战斗机 | 650 | `RESOURCE_ALUMINUM`（铝）、`TECH_LASERS` | `PrereqDistrict="DISTRICT_AERODROME"` |
| `UNIT_JET_BOMBER` 喷气轰炸机 | 700 | `RESOURCE_ALUMINUM`（铝）、`TECH_STEALTH_TECHNOLOGY` | `PrereqDistrict="DISTRICT_AERODROME"` |

**`AirSlots="2"` 就是「配套的飞机」那个数字的来源：两艘航母正好装四架飞机。** 四是**从单位数据里读出来
的**，不是随便定的。

更早的两款机型（`UNIT_FIGHTER` 520、`UNIT_BOMBER` 560）同属空军且更便宜；如果喷气机的科技还没到手，
就在日记里说明，并在「先研究」和「用旧机型」之间做决定，而不是把任务卡住。四架里怎么分配是执行者的判断
—— 两战斗两轰炸是均衡的默认 —— 日记要记录造了哪种、为什么。

## 两个硬前置，其中一个我们没有

1. **每艘航母都需要一座沿海城市。** `DOMAIN_SEA` 单位在内陆城市根本造不了。T344 读数里**提到港口建筑**的
   城市是充分集合：Shanghai（生产 54，而且它的港口带灯塔、船坞、海港）、Brussels（27）、Utrecht（24）、
   Nippur（22）、Lagash（16）、Tyre（15）、Sbrt'n（9）。**要读地图来确认，别只信这张表** —— 一座沿海但没有
   港口建筑的城市不会出现在里面。
2. **需要一座 `Aerodrome`（机场区），而我们现在没有。** T344 实测：**37 座城里没有任何一座提到 `HANGAR` 或
   `AIRPORT`**，所以在建出机场区之前，全帝国**造不出任何飞机**（`DISTRICT_AERODROME`，`PrereqTech=TECH_FLIGHT`，
   而这个科技已经有了）。建这座区域本身就是「排产相关的生产项目」的一部分，也是本任务要做的第一件事 ——
   没有它，飞机不可达。**一座机场区就够四架飞机用**；把它放在生产力最高、且**不是太空竞赛**的那座城。

## 科技

`TECH_COMBINED_ARMS`、`TECH_LASERS`、`TECH_STEALTH_TECHNOLOGY` **无法从记录里确认**：游戏报 77 个科技已完成，
而日记自己的科技表属于另一个局面（44 个，而且它自己也这么说）。**先读 `get_tech_civics` 再规划**；三个里缺
哪一个就把它排进研究路径 —— 本任务同时授权研究与生产，因为**没解锁的单位无法排产**。

## 「不取消」在机制上意味着什么

`set_city_production` 设置的是城市的**当前**项目；工具无法追加（Lua 只有 `GetBuildQueue`、
`GetTurnsLeft`、`GetProductionCost` 和一个 `RemoveAt`，没有插入）。所以下面每一项都是在**当前项目完成的那一
回合才开始造**，期限是：

    总计 = 当前项目的剩余回合 + 游戏为新项目报出的回合

**要用游戏报出的回合数，不要用 `造价 / Prod`** —— T344 实测：ỉwnw 的 `Prod` 是 34，却为一个 680 造价的单位
报 14 回合，说明单位生产加成已经在它的数字里。

## 这个任务不碰什么

- **太空竞赛的城市，绝不碰。** 西安距 `PROJECT_LAUNCH_MOON_LANDING` 还有 9 回合，圣彼得堡距
  `DISTRICT_SPACEPORT` 还有 26 回合。都不打断，也都不加入。
- **任何城市的当前项目。** 一个都不替换；当前项目太长的城就不在候选里。
- **金币。** 本任务排的是生产。它不授权购买航母或飞机，也不覆盖指令里的花钱规则。
- **战争前线与忠诚度工作。** 两者都优先于本任务。

## 完成

当 `get_units` 显示两艘 `UNIT_AIRCRAFT_CARRIER` 和四架飞机时，目标在那一回合达成 —— 用
`scripts/temp-task.py retire <nnn> --done --turn <N>` 退休它，并在日记里记录：每艘航母是哪座城造的、
机场区建在哪、选了哪四架机型、以及每条队列为此让出了什么。
