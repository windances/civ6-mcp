> 本文件是 `056-stage-ranged-and-siege-units-at-their-own-maximum-range.md` 的中文备份（发布任务时由 `scripts/temp-task.py` 写入，仅供人阅读）。
> civ6 agent 读的是 `prompts/tasks/tmp/` 下的英文任务文件；本文件不在那个目录里，也**不得**作为指令使用。

## 指令（逐字，2026-10-08）

「远程部队攻击位置优先按射程最大来安排，这样减少被攻击风险，比如部分升级后的部队射程4，大于守城部队2的攻击距离。」

**远程单位一律优先站在它自己的最大射程上。** 城市打击恰好是 2 格（`src/civ_mcp/lua/cities.py:595`——"city attack range is 2"），
所以射程 3 或 4 的单位从 3–4 格开火时**完全不吃反击**。晋升就是最具体的例子：带 **Advanced Rangefinding（+1 射程）** 的火箭炮
比它遇到的任何城市都远，而现行 doctrine 还是把它停进城市的打击圈里。

## 现行条文与实际要改成什么（逐行实测）

| 文件 | 现在 | 应改为 |
|---|---|---|
| `prompts/tactics/05-formation-and-screening.md:10,11` | `ranged (range 2)`、`siege (range 2)` | 按**单位自身射程**，2 只是下限 |
| `:16` | "**Ranged and siege stand behind them** at range 2" | 在屏后，站**能开火的最远格** |
| `:21` | "Range 2 is where a Catapult belongs..." | 对未晋升的投石车成立；**对任何 +1 射程的单位是错的** |
| `:42` | "marks `FIRE`, not ... `NO LINE OF SIGHT`（range 2 ...）" | `FIRE` 判定要**按单位自身射程** |
| `prompts/tactics/01-unit-production.md:72` | "ranged to fire from range 2" | 该单位能用的**最远射击位** |
| `prompts/tactics/04-staging-out-of-range.md:392,396` | "inside range 2"、`SIEGE FIRE: n/m` | 按**各自射程**计数 |

要写下的规则：**先填最远的射击位**（这同时取代 `04` 第 3b 步的"fill the **last** firing tile first"）；
只有在更远的格子被占、被视线挡住、或根本不存在时，才退到 2 格；而**近战/反骑兵的屏必须继续贴着城**——只有它们能占城。

## 工具侧：已实测的，与仍待查的一处

- **`end_turn.py:1669`** 把整块框成 `SIEGE POSTURE ... siege behind, at range 2:`，**`:1699`** 计数写的是
  `... inside range 2 of the target`。**所以这个计数会漏掉从 3 格开火的晋升单位**——该块自己的注释（`:1686`）就记着一个实测案例：
  "一门攻城单位在 range 2 内，另两门停在 **距离 4 和 6** 上整整三回合"——那两门在开火或能开火，却没有被计入。
- **`cities.py:593,595`** 把**城市**打击硬编码为 2，这是**正确**的（城市就是打 2 格），不要动它。
- **仍需查（本任务第一步）**：`get_staging_plan` / `get_target_report` 判定 `FIRE` / `FIRE?` / `NO LINE OF SIGHT` 时，
  用的是**每个射手自己的射程**还是一个常数 2。第一遍在 `spatial.py` 里没看到射程处理，所以要找到那个判定函数并改成按单位。
  在那之前，会话读到的计划可能把一个完全合格的 3 格射击位判成 `NO LINE OF SIGHT`。

## 完成条件

`prompts/tactics/` 中把 range 2 当作远程/攻城单位站位规则的句子 **`count == 0`**；staging 与 target 工具按**单位自身射程**给出射击判定；
`SIEGE FIRE` 计数不再写 "inside range 2"。并在退役时记录**一个晋升单位的实测前后**：它的射程、被移到的格、以及城市能否够到它。
