> 本文件是 `feature-ideas.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# 功能构想

## ELO 排行榜：增加难度等级追踪

**状态：** 受阻 —— 需要运行中的游戏才能测试 Lua API

**问题：** 目前的 ELO 排行榜是把单个 AI 领袖（图拉真、克利奥帕特拉等）与 LLM 模型对战来排名的。但 AI 领袖本身没有固有难度 —— 难度是全局的游戏设置（Settler → Deity），对所有 AI 玩家一视同仁。排行榜应该排名**难度等级**（例如 "Deity AI"、"Emperor AI"），而不是单个领袖。

**需要做的工作：**

1. **Lua 查询** —— 在 `src/civ_mcp/lua/overview.py` 的 `build_overview_query()` 中调用 `GameDifficulty.GetCurrentDifficulty()`（或等价的调用）
2. **GameOverview 模型** —— 在 `src/civ_mcp/lua/models.py` 的数据类中加入 `difficulty` 字段
3. **叙述文本** —— 在 `src/civ_mcp/narrate.py` 的输出中包含难度
4. **日记 JSONL** —— 为 PlayerRow 条目加入 `difficulty` 字段（agent 行和 rival 行都要）
5. **Web 类型定义** —— 在 `web/src/lib/diary-types.ts` 的 `PlayerRow` 中加入 `difficulty`
6. **ELO API** —— 修改 `web/src/app/api/elo/route.ts`，用 `"difficulty:<level>"` 作为 AI 参与者 ID，而不是 `"ai:<leader>"`
7. **排行榜组件** —— 更新 `web/src/components/model-leaderboard.tsx` 的显示
8. **示例数据** —— 给 `~/.civ6-mcp/diary_demo_elo*.jsonl` 文件补上 difficulty 字段

**Civ 6 难度等级：** Settler、Chieftain、Warlord、Prince、King、Emperor、Immortal、Deity

---

## N 人 LLM 竞技场（Agent 对 Agent）

**状态：** 设计已完成 —— 见 `docs/agent-vs-agent.md`

**问题：** MCP 服务器目前只支持单个 LLM agent 与 Civ 6 内置 AI 对战。目标是让 N 个 LLM agent 在同一局游戏里互相对战，并保证战争迷雾下的公平性。

**关键约束：** FireTuner 在 Civ 6 的多人/热座模式下被硬性禁用（反作弊）。方案是**单人局傀儡化** —— 用一个 Lua gameplay 模组拦截 AI 玩家的回合，把控制权交给 LLM agent。

**架构：**
```
Agent 0 (Player 0)  Agent 1 (Player 1)  Agent N (Player N)
        \                 |                  /
         └────── Coordinator ──────────┘
                      |
                 GameState(player_id=X)   ← per-player instances
                      |
                 GameConnection           ← shared, serialized
                      |  TCP :4318
                 Civ 6 + PuppeteerMod     ← single-player game
```

**实现阶段：**

### 阶段 1：PuppeteerMod（Lua gameplay 模组）
- 创建 `PuppeteerMod/` —— 一个 Lua 模组，拦截 N 个可配置 AI 玩家的回合
- 挂钩 `GameEvents.PlayerTurnStartComplete`：用 `FinishMoves` 冻结单位、恢复移动力、设置就绪标志
- 协调器轮询 `__puppet_turn_active[playerID]`，以此判断当前轮到谁

### 阶段 2：Lua 构建器参数化
- 为 12 个 Lua 模块中的全部 106 个 `build_*` 函数加上 `player_id: int | None = None`
- 把 72 处硬编码的 `Game.GetLocalPlayer()` 调用替换为 `_lua_player_expr(player_id)`
- 向后兼容：`player_id=None` 保持现有的单 agent 行为不变

### 阶段 3：战争迷雾强制
- 现有的 `PlayersVisibility[me]` 检查在阶段 2 之后会自动作用于正确的玩家
- 为威胁扫描（敌方单位）和外交（敌方城市）加上可见性检查
- 创建 `fog_filter.py`，用于纵深防御式审计

### 阶段 4：本地玩家切换
- 在 `game_state.py` 中加入 `_with_player_context(player_id, lua_code)`
- 把 InGame 操作包在 `PlayerManager.SetLocalPlayerAndObserver()` + pcall + 还原之中
- 需要的场景：移动、攻击、建城、生产、购买、外交

### 阶段 5：协调器 + 傀儡结束回合
- 创建 `coordinator.py` —— 回合检测、N 个 agent 的调度、超时处理
- 创建 `puppet_end_turn.py` —— 简化版结束回合（用 `FinishMoves` 代替 `ACTION_ENDTURN`）
- 回合顺序：玩家 0 结束回合 → 傀儡玩家依次被拦截 → AI 处理 → 重复

### 阶段 6：Agent 接口 + CLI
- 创建 `agent.py` —— 通过 Anthropic API 进行带工具调用（tool-use）的 Claude 对话循环
- 创建 `tool_schemas.py` —— 与 `server.py` 对应的工具定义
- 创建 `arena.py` —— CLI 入口：`civ-arena --players 0:model-a,1:model-b --max-turns 200`
- 每个玩家各自的日记，上下文窗口管理（滑动窗口 + 日记摘要）

**文件：** 新增 8 个，修改 16 个

---

## 实时对局串流到 Web 仪表盘

**状态：** 尚未开始

**问题：** Web 仪表盘目前展示的是对局结束后的数据（日记回放、ELO 评分）。没有任何办法在 agent 对局进行时实时观看。

**方案：** 在 MCP 服务器的 FastAPI 后端（端口 8000）上加入 WebSocket 串流，把实时的游戏状态更新推送到 Next.js 仪表盘。

**为什么用 WebSocket 而不是视频采集：** MCP 服务器本来就有结构化的游戏状态（总览、单位、城市、地图格、外交），而且 `GameLogger` 会记录每一次工具调用及其耗时。串流这些数据带宽占用低、可以远程工作，还能让观看者获得 agent 的视角 —— 它查询了什么、决定了什么、以及为什么。视频采集（OBS/FFmpeg）以后可以作为补充叠加进来。

**需要做的工作：**

1. **WebSocket 端点** —— 在 `src/civ_mcp/web_api.py` 中用 FastAPI 的 WebSocket 支持加入 `/ws/game`。在每次工具调用或每个回合之后广播游戏状态差异。
2. **事件总线** —— 挂钩 `GameLogger`，或创建一个轻量的发布/订阅机制，让工具调用、回合切换和结束回合快照向已连接的 WebSocket 客户端发出事件。
3. **实时仪表盘页面** —— 在 `web/` 中新增 `/live` 页面，连接 WebSocket 并渲染：
   - 实时更新的游戏总览（回合、产出、得分）
   - 简化的六边形地图，显示单位位置和城市位置
   - Agent 动作流（工具调用连同耗时一起流式进入）
   - 当前日记条目 / agent 的推理
4. **地图渲染** —— 在浏览器中用 Canvas 或 SVG 渲染简化的六边形网格，根据 `get_map_area` 数据展示地形、单位、城市和战争迷雾。
5. **断线重连处理** —— WebSocket 自动重连，连接时做完整状态同步（而不只是差异）。
6. **可选：视频流嵌入** —— 增加一个视频播放器组件，可以在数据可视化旁边嵌入游戏窗口的 HLS/WebRTC 流。
