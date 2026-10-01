> 本文件是 `observability.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# 可观测性：日记、日志与空间追踪

MCP 服务器在对局过程中记录三条并行的数据流，全部以 JSONL（每行一个 JSON 对象）写入 `~/.civ6-mcp/`。它们共同记录了*游戏当时是什么样子*、*智能体做了什么*以及*智能体看向哪里*。

```
~/.civ6-mcp/
  diary_korea_-879712000.jsonl           # per-turn game state + agent reflections
  diary_korea_-879712000_cities.jsonl    # per-turn per-city detail
  log_korea_-879712000.jsonl             # every tool call with timing and results
  spatial_korea_-879712000.jsonl         # tile-level attention tracking
```

所有文件都以 `{civ}_{seed}` 为键（例如 `korea_-879712000`），由文明类型和对局的随机种子推导而来。多个同时进行的对局会产生各自独立的文件集合。

---

## 日记

**文件：** `diary_{civ}_{seed}.jsonl` + `diary_{civ}_{seed}_cities.jsonl`

日记是智能体的持久记忆。它每回合捕获一份完整的游戏状态快照，以及智能体自己的反思，在回合推进之前写入。当上下文被压缩，或智能体在新会话中重新接续一局游戏时，`get_diary` 会依据这些条目重建战略上下文。

### 记录的内容

**每个玩家一行**（每回合每个存活文明一行）：
- 得分、人口、城市数量
- 产出：科技、文化、金币、信仰、外交支持（含每回合速率）
- 军事实力与单位构成
- 已完成的科技/市政列表与当前研究
- 区域、奇观与巨作数量
- 领土面积、改良设施数量、探索百分比
- 政体、政策、时代、时代得分、时代类别
- 万神殿、宗教与宗教信条
- 胜利进度（科技胜利点、外交胜利点、旅游业绩、国内游客）
- 资源储备与奢侈品数量

**智能体行**（本地玩家的附加字段）：
- 与所有已知文明的外交状态（状态索引、同盟类型/等级、怨愤）
- 城邦使者与宗主关系
- 总督任命与晋升
- 贸易路线利用情况
- 伟人点数累积
- 五个反思字段（见下文）
- MCP 客户端身份与模型 ID

**城市行**（单独的文件，每回合每座城市一行）：
- 人口、全部六种产出、住房、宜居度
- 区域列表、当前生产
- 忠诚度与每回合忠诚度

### 反思

智能体在每次调用 `end_turn` 时写入五个必填字段：

| 字段 | 用途 |
|-------|---------|
| `tactical` | 本回合发生了什么：具体的单位、地块、战斗结果 |
| `strategic` | 与对手的相对态势：产出、城市数量、胜利路线的可行性 |
| `tooling` | 观察到的工具问题，或 "No issues" |
| `planning` | 未来 5-10 回合的具体行动 |
| `hypothesis` | 预测：进攻时机、里程碑、风险 |

反思记录在 AI 处理开始*之前*。在 `end_turn` 之后才浮现的事件（外交提议、AI 的移动）属于下一回合的日记。

如果 `end_turn` 被阻塞（外交、世界议会）并重试，新的反思会以 `" | "` 分隔符合并进该回合已有的条目，而不是新建一条重复记录。

### 读取

`get_diary` 工具会读回日记条目，并过滤为仅剩智能体行：

```
get_diary(last_n=5)           # most recent 5 entries
get_diary(turn=100)           # single turn
get_diary(from_turn=80, to_turn=120)  # range
```

输出格式为易读的 markdown，包含产出、资源以及全部五个反思字段。

### 格式

```json
{
  "v": 1,
  "turn": 145,
  "game": "korea_-879712000",
  "timestamp": "2026-02-26T18:30:45.123456+00:00",
  "is_agent": true,
  "pid": 0,
  "civ": "CIVILIZATION_KOREA",
  "leader": "Seondeok",
  "score": 742,
  "cities": 5,
  "science": 89.5,
  "gold_per_turn": 18.5,
  "reflections": {
    "tactical": "Established Campus in Seoul...",
    "strategic": "Currently 2nd in science...",
    "tooling": "No issues.",
    "planning": "Build Library in Busan...",
    "hypothesis": "Poland likely to declare friendship..."
  },
  "agent_model": "claude-opus-4-6"
}
```

（为简洁起见省略了许多字段——完整的 schema 每个玩家行有 95+ 个字段。）

---

## 工具日志

**文件：** `log_{civ}_{seed}.jsonl`

每一次 MCP 工具调用都会连同完整的耗时、参数和结果一起记录。这是关于智能体做了什么、以及花了多长时间的权威记录。

### 记录的内容

每条记录包含：
- 工具名称与类别（`query` / `action` / `turn`）
- 输入参数
- 完整的叙述性结果文本
- 结果摘要（前 200 个字符，便于快速分析）
- 成功/失败标志
- 实际耗时（毫秒）
- 回合数、时间戳、每局内的序号
- 会话 ID（每个 MCP 服务器进程唯一）
- 智能体模型 ID

对局结束的条目包含一个 `outcome` 对象，其中有胜者、胜利类型，以及智能体是否存活。

### 格式

```json
{
  "game": "korea_-879712000",
  "session": "a1b2c3d4",
  "ts": 1708981845.123,
  "turn": 145,
  "seq": 2847,
  "type": "tool_call",
  "tool": "get_units",
  "category": "query",
  "params": {},
  "result_summary": "4 units:\n  Crossbowman (UNIT_CROSSBOW...",
  "result": "4 units:\n  Crossbowman (UNIT_CROSSBOWMAN) at (43,6)...",
  "duration_ms": 342,
  "success": true,
  "agent_model": "claude-opus-4-6"
}
```

### 典型大小

每局完整对局（400 回合）为 10-50 MB。`result` 字段保存完整的叙述文本，它主导了文件体积。

---

## 空间注意力追踪器

**文件：** `spatial_{civ}_{seed}.jsonl`

这是一套研究用的埋点，记录智能体通过每次工具调用观察到哪些地图地块。它不会反馈给智能体——它的存在是为了度量“感知域效应”（人类玩家被动看到的内容与智能体显式查询的内容之间的差距）。

### 动机

人类玩家扫一眼小地图，就注意到领土在变色。他们看到得分刻度条往上跳。他们发现某个单位的血条掉了一格。智能体被动地得不到其中任何一项——每一条空间信息都必须显式查询。空间追踪器度量智能体的注意力落在*哪里*和*何时*，从而可以分析盲区与注意力衰减。

### 地块如何被提取

每次工具调用有两个来源：

1. **结果文本** —— 正则表达式 `\((\d+),(\d+)\)` 从叙述性输出中提取所有坐标对。每个叙述函数都一致地使用这种格式。
2. **输入参数** —— `target_x`/`target_y`、`x`/`y`，或针对 `get_map_area` 由 `center_x`/`center_y`/`radius` 计算得出。

### 注意力类型

每条观察记录按智能体是如何看到那些地块来分类：

| 类型 | 工具 | 含义 |
|------|-------|---------------|
| `deliberate_scan` | `get_map_area`, `get_settle_advisor`, `get_district_advisor`, `get_wonder_advisor`, `get_purchasable_tiles`, `get_pathing_estimate` | 智能体选择查看某一特定区域 |
| `deliberate_action` | `unit_action`, `city_action`, `spy_action`, `set_city_production`, `purchase_tile` | 智能体对某一特定地块采取了行动 |
| `survey` | `get_strategic_map`, `get_global_settle_advisor`, `get_empire_resources` | 跨地图或帝国的广泛扫描 |
| `peripheral` | `get_units`, `get_cities`, `get_spies`, `get_diplomacy`, `get_trade_routes`, `get_trade_destinations` | 在状态查询的附带结果中看到的坐标 |
| `reactive` | `get_notifications` | 来自游戏推送警报的坐标 |

没有空间数据的工具（研究、政策、总督等）会被静默跳过。

### 格式

```json
{
  "game": "korea_-879712000",
  "turn": 208,
  "tool": "get_map_area",
  "type": "deliberate_scan",
  "tiles": [[42,5],[42,6],[42,7],[43,5],[43,6],[43,7],[44,5],[44,6],[44,7]],
  "n_tiles": 9,
  "ts": 1772134312.095,
  "ms": 364
}
```

### 典型大小

每局完整对局约 1 MB（标准地图 400 回合）。大致是工具日志体积的 2-5%。

### 分析思路

这些数据支持若干种事后分析：

- **注意力热力图**：对每个地块，它最后一次被观察到是什么时候？哪些地块从未被观察到？
- **注意力衰减**：智能体移开之后，某个区域的观察频率下降得有多快？
- **被动还是主动**：智能体是系统地勘察，还是只在威胁已经出现的地方查看？
- **盲区相关性**：当智能体损失一个单位，或漏看对手的胜利时，相关区域是否未被观察？
- **工具效用**：哪些工具扩展了空间覆盖，哪些只是在冗余地重复观察已知地块？
- **覆盖率**：智能体每回合观察到已揭示地图地块的多大比例？每 10 回合呢？

---

## 共有模式

三个系统共享同一套架构：

**无界缓冲模式。** 每个追踪器一开始是未绑定的（没有对局标识）。工具调用先缓冲在内存中。当 `get_game_overview` 首次运行时，它会调用 `get_game_identity()` 确定文明与种子，然后绑定全部三个追踪器。缓冲的条目会带着此时已知的标识刷写到磁盘。

**对局标识。** 由一段 Lua 查询确定，它读取 `PlayerConfigurations[me]:GetCivilizationTypeName()` 和 `GameConfiguration.GetValue("GAME_SYNC_RANDOM_SEED")`。文明名称会被转为小写，并去掉 `CIVILIZATION_` 前缀。

**回合追踪。** 所有追踪器都维护一个 `_turn` 字段，在四个时点更新：
1. `get_game_overview` —— 每回合的主要入口
2. `end_turn` 的日记捕获 —— 如果跳过了 overview，它让回合数保持同步
3. `end_turn` 的结果解析 —— 在 `"Turn X -> Y"` 之后前进到新的回合数

**JSONL 格式。** 每行一个 JSON 对象，紧凑分隔符（`(",":")`），没有数组包裹。文件可以被 tail、grep 或流式读取，而无需解析整个文件。

**挂载点。** 所有工具调用都经过 `server.py` 中的 `_logged()`，它：
1. 为执行计时
2. 捕获错误
3. 调用 `logger.log_tool_call()` —— 写入工具日志
4. 调用 `spatial.record()` —— 写入空间日志（try/except，绝不中断游戏）
5. 把叙述性结果返回给智能体

```
Agent ─── MCP Tool Call ──→ _logged() ──→ fn() ──→ narrated result
                               │                        │
                               ├─ logger.log_tool_call() ← result + timing
                               └─ spatial.record()       ← result + params
                                                          ↓
                               Diary written separately by end_turn()
```

---

## 文件大小估算（400 回合，标准地图）

| 文件 | 典型大小 | 主要影响因素 |
|------|-------------|-----------|
| `diary_*.jsonl` | 2-5 MB | 玩家数量、字段数量 |
| `diary_*_cities.jsonl` | 1-3 MB | 城市数量、已进行的回合数 |
| `log_*.jsonl` | 10-50 MB | 每回合的工具调用次数、结果文本长度 |
| `spatial_*.jsonl` | 0.5-1.5 MB | 每回合的空间工具调用次数、地块数量 |
| **每局总计** | **~15-60 MB** | |
