> 本文件是 `047-re-order-the-three-builders-that-could-not-start-on-their-tile.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

## 为什么有这个任务

本局 T360 实测：21 条建造者指令里，5 条当天就开工，7 条还在走路（`STOPPED_MID_PATH (moves exhausted)`），
而**3 条被拒绝**——

```
id:12648465  IMPROVEMENT_MINE  -> Error: CANNOT_IMPROVE|Builder has no moves remaining this turn
id:13172742  IMPROVEMENT_CAMP  -> Error: CANNOT_IMPROVE|Builder has no moves remaining this turn
id:13238329  IMPROVEMENT_FARM  -> Error: CANNOT_IMPROVE|Builder has no moves remaining this turn
```

这三名建造者都是刚走到被指派的地块、把 2 点移动力用光；Civ VI 不允许 0 移动力的建造者开工，于是地块空着、
UI 上看起来它们站着不动。

## 下一回合要做什么

1. 照常先读 `get_builder_tasks`。这三块地会以**0 格距离**的空闲建造者出现——那正是"人已经站在地块上、
   只差一条指令"的信号。
2. 在派新工之前，先把这三条 `improve` 重下：`(61,35)` 的 `MINE`、`(28,9)` 的 `CAMP`、`(79,18)` 的
   `FARM`。站在自己的地块上、有 2/2 移动力的建造者当天就能开工，所以这三条会立刻生效。
3. 然后照旧按表往下派（URGENT > HIGH > NORMAL，就近的空闲建造者优先）。

## 这条任务要替代的规则

下 `improve` 之前，先看 `get_units` 里该建造者的 `moves`：

- **`moves >= 1`**——立刻下开工指令，本回合就开始。
- **`moves 0`**——不要下。它要么在走路（别管它，下一回合会带着移动力到达），要么已经站在地块上
  （下一回合的 `get_builder_tasks` 会以 0 格点名它）。对 0 移动力下 `improve` 是必然被拒的调用，
  每回合三次就是把上下文花在什么也做不了的调用上。

## 完成条件

这三块地带上各自的改良设施——`get_map_area` 读到 `(61,35)` 的 `MINE`、`(28,9)` 的 `CAMP`、
`(79,18)` 的 `FARM`——或者 `get_builder_tasks` 不再把这三块地列为"0 格空闲建造者"的任务。
