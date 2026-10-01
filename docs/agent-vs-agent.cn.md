> 本文件是 `agent-vs-agent.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# 智能体对战智能体：通过单人游戏操控实现多智能体对局

> **状态：提案** —— 设计文档。尚未实现。

## 概述

本文件描述如何让两个（或更多）AI 智能体在同一份单人模式的游戏实例中互相对战《文明 VI》。一个智能体像人类玩家一样正常游玩；另一个智能体则通过拦截 AI 玩家的回合，并借助 GameCore 与临时的本地玩家切换来下达命令，从而“操控”该 AI 玩家。

不需要多人游戏。不需要修改二进制。可在 macOS 和 Windows 上运行。

```
┌─────────────┐     ┌─────────────┐
│   Agent A   │     │   Agent B   │
│ (Player 0)  │     │ (Player 1)  │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │
        ┌──────▼──────┐
        │ Coordinator  │  ← detects whose turn it is, dispatches
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  MCP Server  │  ← single instance, parametrized by player_id
        └──────┬──────┘
               │ TCP :4318
        ┌──────▼──────┐
        │   Civ 6     │  ← single-player, EnableTuner=1
        │  + Lua Mod   │  ← intercepts AI turns
        └─────────────┘
```

## 为什么不用多人游戏？

FireTuner 的 TCP 监听端（端口 4318）在 **C++ 引擎层面被硬性禁用**，对所有多人模式都适用——LAN、互联网和热座。这是有意的反作弊措施，没有已知的配置可以覆盖。Archipelago mod 的开发者独立确认了没有任何变通办法。

通往智能体对战智能体的唯一路径就是单人游戏操控。

---

## 架构

### 组件 1：回合拦截 Mod（Lua）

一个安装在 Mods 文件夹中的《文明 VI》玩法 mod。它的职责：

1. **压制内置 AI** —— 在 `GameEvents.PlayerTurnStartComplete` 上，在 AI 能够行动之前，对目标玩家的所有单位调用 `UnitManager.FinishMoves()`
2. **发出就绪信号** —— 设置一个全局标志，让 MCP 服务器可以轮询得知被操控玩家的回合已经开始
3. **恢复移动力** —— 把移动点数还给单位，以便我们的智能体可以指挥它们
4. **处理回合结束** —— 当智能体发出完成信号时再次调用 `FinishMoves()`

#### 回合事件序列（每个玩家）

```
GameEvents.PlayerTurnStarted(playerID)
    └─ Movement points NOT yet restored

GameEvents.PlayerTurnStartComplete(playerID)    ← HOOK HERE
    └─ Movement points restored
    └─ *** Built-in AI executes between here and next event ***

Events.PlayerTurnActivated(playerID, isFirstTime)
    └─ AI has finished acting

Events.PlayerTurnDeactivated(playerID)
    └─ Player's turn is over
```

关键窗口位于 `PlayerTurnStartComplete` 与 `PlayerTurnActivated` 之间。mod 必须在 `PlayerTurnStartComplete` 中对所有单位调用 `FinishMoves()`，以阻止 AI 行动。

#### Mod 实现

```lua
-- PuppeteerMod/Scripts/Puppeteer.lua (GameplayScript context)

local PUPPET_PLAYER = 1  -- Which player the agent controls

-- Global state readable by FireTuner
__puppet_turn_active = false
__puppet_player_id = PUPPET_PLAYER

function OnPlayerTurnStartComplete(playerID)
    if playerID == PUPPET_PLAYER then
        -- Step 1: Freeze all units (prevents built-in AI from acting)
        local pUnits = Players[playerID]:GetUnits()
        for _, unit in pUnits:Members() do
            UnitManager.FinishMoves(unit)
        end

        -- Step 2: Restore movement (gives our agent control)
        for _, unit in pUnits:Members() do
            UnitManager.RestoreMovement(unit)
        end

        -- Step 3: Signal that puppet turn is ready
        __puppet_turn_active = true
    end
end

function OnPlayerTurnDeactivated(playerID)
    if playerID == PUPPET_PLAYER then
        __puppet_turn_active = false
    end
end

GameEvents.PlayerTurnStartComplete.Add(OnPlayerTurnStartComplete)
Events.PlayerTurnDeactivated.Add(OnPlayerTurnDeactivated)
```

#### Mod 描述文件

```xml
<!-- PuppeteerMod/PuppeteerMod.modinfo -->
<?xml version="1.0" encoding="utf-8"?>
<Mod id="PUPPET_AGENT_MOD" version="1">
  <Properties>
    <Name>Agent Puppeteer</Name>
    <Description>Intercepts AI turns for external agent control</Description>
    <EnabledByDefault>1</EnabledByDefault>
  </Properties>
  <Components>
    <AddGameplayScripts>
      <File>Scripts/Puppeteer.lua</File>
    </AddGameplayScripts>
  </Components>
</Mod>
```

> **待解问题：** `AddGameplayScripts` 运行在 GameCore 上下文中。`Events.PlayerTurnDeactivated` 钩子是一个 UI 事件——它可能需要改为放在 `AddInGameActions` 组件中。需要测试。

---

### 组件 2：MCP 服务器改动

#### 2a. 将 Lua 构造器参数化

目前每个 Lua 查询都硬编码了 `Game.GetLocalPlayer()`。为了操控玩家，查询需要能够接受显式的玩家 ID。

**策略：** 添加一个生成玩家表达式的辅助函数：

```python
# In _helpers.py
def _lua_player_expr(player_id: int | None = None) -> str:
    """Return Lua expression for the target player.

    None → Game.GetLocalPlayer() (normal play)
    int  → literal player ID (puppet mode)
    """
    if player_id is None:
        return "Game.GetLocalPlayer()"
    return str(player_id)
```

更新 `_lua_get_unit` 与 `_lua_get_city`：

```python
def _lua_get_unit(unit_index: int, player_id: int | None = None) -> str:
    return f"""
local me = {_lua_player_expr(player_id)}
local unit = UnitManager.GetUnit(me, {unit_index})
if unit == nil then {_bail("ERR:UNIT_NOT_FOUND")} end
"""
```

然后让 `player_id: int | None = None` 贯穿传递到：
- 所有 `build_*` 函数（11 个模块中共 66 处调用点）
- 所有 `GameState` 方法
- `server.py` 中的所有 MCP 工具定义

**范围：** 这是一次规模大但机械化的重构。每个构造器都会获得 `player_id=None` 参数，并把 `Game.GetLocalPlayer()` 替换为 `{_lua_player_expr(player_id)}`。

#### 2b. 写操作 —— GameCore 与 InGame

对于被操控的玩家，有些操作在 GameCore 中即可完成（适用于任何玩家），另一些则需要临时切换本地玩家。

**GameCore（适用于任何玩家——无需切换）：**

| 操作 | API | 备注 |
|-----------|-----|-------|
| 移动（1 格） | `UnitManager.MoveUnit(unit, plot)` | 寻路不可靠；一次移动 1 格 |
| 跳过/结束 | `UnitManager.FinishMoves(unit)` | |
| 恢复移动力 | `UnitManager.RestoreMovement(unit)` | |
| 消灭单位 | `UnitManager.Kill(unit)` | |
| 创建单位 | `UnitManager.InitUnit(playerID, type, x, y)` | |
| 设置研究 | `pTechs:SetResearchingTech(techID)` | |
| 设置研究进度 | `pTechs:SetResearchProgress(techID, val)` | |
| 触发尤里卡 | `pTechs:TriggerBoost(techID)` | |
| 设置市政进度 | `pCulture:SetCulturalProgress(civicID, val)` | 切勿使用 `SetCivic()`——会永久破坏 AI |
| 瞬间建造 | `bq:CreateIncompleteBuilding(id, plot, 100)` | 作弊级别；瞬间完成 |

**InGame（需要切换本地玩家）：**

| 操作 | API | 为何需要切换 |
|-----------|-----|-------------------|
| 多格移动 | `UnitManager.RequestOperation(MOVE_TO)` | 寻路只对本地玩家有效 |
| 远程攻击 | `UnitManager.RequestOperation(RANGE_ATTACK)` | |
| 近战攻击 | `UnitManager.RequestOperation(MOVE_TO + ATTACK)` | |
| 建立城市 | `UnitManager.RequestOperation(FOUND_CITY)` | |
| 建造改良设施 | `UnitManager.RequestOperation(BUILD_IMPROVEMENT)` | |
| 设置生产 | `CityManager.RequestOperation(BUILD)` | |
| 购买物品 | `CityManager.RequestCommand(PURCHASE)` | |
| 外交 | `DiplomacyManager.RequestSession()` | |
| 晋升单位 | `UnitManager.RequestCommand(PROMOTE)` | 在 InGame 中已损坏；请改用 GameCore 的 `SetPromotion` |
| 升级单位 | `UnitManager.RequestCommand(UPGRADE)` | |

#### 2c. 本地玩家切换

对于被操控玩家的 InGame 操作，临时切换游戏所认为的“本地”玩家：

```python
async def _with_player_context(self, player_id: int, lua_code: str) -> list[str]:
    """Execute InGame Lua as if player_id were the local player."""
    if player_id is None:
        # Normal path — no switching needed
        return await self.conn.execute_write(lua_code)

    switch_lua = f"""
local origPlayer = Game.GetLocalPlayer()
PlayerManager.SetLocalPlayerAndObserver({player_id})
"""
    restore_lua = f"""
PlayerManager.SetLocalPlayerAndObserver(origPlayer)
"""
    wrapped = switch_lua + lua_code + restore_lua
    return await self.conn.execute_write(wrapped)
```

**注意事项：**
- 每次都会造成可见的掉帧卡顿
- 必须是原子的——如果 Lua 在执行中途报错，玩家会保持在被切换的状态（需要 pcall 包裹）
- 应尽快恢复，以避免视觉伪影

**使用 pcall 的更安全版本：**

```python
async def _with_player_context(self, player_id: int, lua_code: str) -> list[str]:
    if player_id is None:
        return await self.conn.execute_write(lua_code)

    wrapped = f"""
local origPlayer = Game.GetLocalPlayer()
PlayerManager.SetLocalPlayerAndObserver({player_id})
local ok, err = pcall(function()
{lua_code}
end)
PlayerManager.SetLocalPlayerAndObserver(origPlayer)
if not ok then print("ERR:PUPPET_ERROR|" .. tostring(err)); print("---END---"); return end
"""
    return await self.conn.execute_write(wrapped)
```

#### 2d. GameCore 移动（单格寻路）

GameCore 中的 `UnitManager.MoveUnit()` 多格寻路不可靠。为了稳健地操控移动，请实现一次移动一格的步进：

```lua
-- Move unit one tile toward target using adjacency
local unit = Players[pid]:GetUnits():FindID(unitIdx)
local ux, uy = unit:GetX(), unit:GetY()
local tx, ty = targetX, targetY

-- Find best adjacent tile (closest to target)
local bestPlot, bestDist = nil, 999
for dir = 0, 5 do
    local adj = Map.GetAdjacentPlot(ux, uy, dir)
    if adj and not adj:IsImpassable() then
        local dx = adj:GetX() - tx
        local dy = adj:GetY() - ty
        local dist = dx*dx + dy*dy
        if dist < bestDist then
            bestDist = dist
            bestPlot = adj
        end
    end
end
if bestPlot then
    UnitManager.MoveUnit(unit, bestPlot)
end
```

这种做法很朴素（没有地形代价加权，也没有 ZOC 处理）。真正正确的实现需要在六边形网格上做带地形代价的 A*。另一种选择是使用本地玩家切换来调用 `RequestOperation(MOVE_TO)`，它具备完整的寻路能力。

**建议：** 移动使用本地玩家切换。由于人类并没有在看被操控玩家的回合，掉帧卡顿是可以接受的。

---

### 组件 3：协调器

协调器管理智能体之间的回合顺序。它作为一个独立进程（或协程）运行，负责：

1. **轮询回合变化** —— 定期查询 `Game.GetLocalPlayer()` 和 `__puppet_turn_active`
2. **分派给智能体** —— 告知智能体 A 或智能体 B 轮到它了
3. **等待完成** —— 智能体发出完成信号，协调器触发回合结束

#### 状态机

```
                    ┌──────────────┐
                    │  WAITING     │
                    │  (polling)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
    ┌─────────────────┐      ┌──────────────────┐
    │ AGENT_A_TURN    │      │ AGENT_B_TURN     │
    │ (player 0)      │      │ (player 1)       │
    │ normal MCP ops  │      │ puppet MCP ops   │
    └────────┬────────┘      └────────┬─────────┘
             │                        │
             ▼                        ▼
    ┌─────────────────┐      ┌──────────────────┐
    │ AGENT_A_END     │      │ AGENT_B_END      │
    │ end_turn()      │      │ finish_moves()   │
    └────────┬────────┘      └────────┬─────────┘
             │                        │
             └────────────┬───────────┘
                          ▼
                    ┌──────────────┐
                    │  WAITING     │
                    └──────────────┘
```

#### 回合检测

```python
async def poll_turn_state(conn: GameConnection) -> tuple[int, bool]:
    """Returns (current_player_turn, is_puppet_ready)."""
    lines = await conn.execute_read("""
local me = Game.GetLocalPlayer()
print("TURN_STATE|" .. Game.GetCurrentGameTurn())
print("LOCAL|" .. me)
print("PUPPET_ACTIVE|" .. tostring(__puppet_turn_active or false))
print("---END---")
""")
    # Parse and return state
    ...
```

#### 协调器循环

```python
async def coordinator_loop(conn, agent_a, agent_b):
    while True:
        turn, puppet_ready = await poll_turn_state(conn)

        if puppet_ready:
            # It's the puppet player's turn — dispatch to Agent B
            await agent_b.play_turn(player_id=PUPPET_PLAYER)
            # Signal done — finish all moves
            await conn.execute_read(f"""
local pUnits = Players[{PUPPET_PLAYER}]:GetUnits()
for _, unit in pUnits:Members() do
    UnitManager.FinishMoves(unit)
end
print("---END---")
""")
        else:
            # Check if it's the human player's turn
            # Agent A plays normally via standard MCP tools
            await agent_a.play_turn(player_id=None)

        await asyncio.sleep(0.5)
```

---

### 组件 4：智能体接口

每个智能体都需要知道：
- 它控制哪个玩家
- 什么时候轮到它
- 有哪些工具可用（被操控玩家的可用操作受限）

#### 方案 A：两个 MCP 客户端，一个服务器

运行两个 Claude Code 会话（或两个由 API 驱动的智能体），两者都连接到同一个 MCP 服务器。每次工具调用都传入 `player_id`。

```
Agent A (Claude session 1) ──► MCP Server ──► Civ 6
Agent B (Claude session 2) ──► MCP Server ──► Civ 6
```

**问题：** MCP 服务器是按客户端划分的。两个 Claude 会话 = 两个 MCP 服务器进程 = 两条 TCP 连接争抢 4318 端口。

#### 方案 B：单一编排进程

一个 Python 进程顺序运行两个智能体：

```python
async def main():
    conn = GameConnection()
    await conn.connect()

    agent_a = Agent(conn, player_id=0, model="claude-sonnet-4-5-20250929")
    agent_b = Agent(conn, player_id=1, model="claude-sonnet-4-5-20250929")

    while True:
        turn_state = await poll_turn_state(conn)

        if turn_state.is_human_turn:
            await agent_a.play_turn()
        elif turn_state.is_puppet_ready:
            await agent_b.play_turn()
        else:
            await asyncio.sleep(0.5)
```

每个 `Agent` 直接使用 Anthropic API（而不是 MCP），并通过共享的 `GameState` 调用游戏函数：

```python
class Agent:
    def __init__(self, conn, player_id, model):
        self.gs = GameState(conn)
        self.player_id = player_id
        self.client = anthropic.AsyncAnthropic()
        self.model = model
        self.messages = []

    async def play_turn(self):
        # Build tool definitions from GameState methods
        # Run agentic loop: observe → decide → act → observe
        overview = await self.gs.get_game_overview(player_id=self.player_id)
        units = await self.gs.get_units(player_id=self.player_id)
        # ... Claude decides actions ...
        # ... execute actions ...
        # ... end turn ...
```

**这是推荐的做法。** 单一进程、单一连接、顺序回合、清晰的隔离。

#### 方案 C：Agent SDK

使用 [Claude Agent SDK](https://github.com/anthropics/agent-sdk) 为每个智能体定义游戏工具：

```python
from agent_sdk import Agent, tool

@tool
async def get_units(player_id: int) -> str:
    """Get all units for the specified player."""
    return await shared_gs.get_units(player_id=player_id)

agent_a = Agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_units, move_unit, attack, ...],
    system="You are playing Civ 6 as player 0. Play to win.",
)

agent_b = Agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_units, move_unit, attack, ...],
    system="You are playing Civ 6 as player 1. Play to win.",
)
```

---

## GameCore API 参考（适用于任何玩家）

### 单位管理

| 方法 | 签名 | 备注 |
|--------|-----------|-------|
| 移动 | `UnitManager.MoveUnit(unit, plot)` | 1 格可靠；多格不可靠 |
| 结束 | `UnitManager.FinishMoves(unit)` | 将移动力清零 |
| 恢复 | `UnitManager.RestoreMovement(unit)` | 恢复全部移动力 |
| 恢复攻击 | `UnitManager.RestoreUnitAttacks(unit)` | |
| 消灭 | `UnitManager.Kill(unit)` | 移除单位 |
| 放置 | `UnitManager.PlaceUnit(unit, plot)` | 传送 |
| 创建 | `UnitManager.InitUnit(playerID, unitType, x, y)` | 生成新单位 |
| 唤醒 | `UnitManager.WakeUnit(unit)` | |

### 研究（PlayerTechs）

| 方法 | 备注 |
|--------|-------|
| `SetResearchingTech(techID)` | 设置当前研究 |
| `SetResearchProgress(techID, progress)` | 设置进度值 |
| `ChangeCurrentResearchProgress(delta)` | 增加 |
| `TriggerBoost(techID)` | 尤里卡 |
| `SetTech(techID, true)` | 立即授予（作弊） |

### 文化（PlayerCulture）

| 方法 | 备注 |
|--------|-------|
| `SetCulturalProgress(civicID, progress)` | 安全——设置进度 |
| `SetCivic(civicID, true)` | **危险**——永久破坏 AI 的市政研究 |

### 建筑（CityBuildQueue）

| 方法 | 备注 |
|--------|-------|
| `CreateIncompleteBuilding(buildingID, plotIdx, percentComplete)` | 作弊；100 = 瞬间完成 |

### 脚本化军事行动（来自 Gedemon 的 GCO）

| 方法 | 备注 |
|--------|-------|
| `pAiMil:StartScriptedOperationWithTargetAndRally(...)` | 为任何玩家创建军事行动 |
| `pAiMil:AddUnitToScriptedOperation(opID, unitID)` | 将单位分配到行动中 |

---

## 局限与取舍

### 效果良好的部分
- **单位移动**（通过本地玩家切换或 GameCore 单格移动）
- **研究/市政选择**（GameCore setter）
- **读取任何玩家的状态**（所有 `Players[N]:Get*()` 查询都能工作）
- **回合拦截**（已由 mod 作者验证）

### 脆弱的部分
- **本地玩家切换** —— 造成掉帧卡顿，必须用 pcall 包裹
- **生产队列** —— 没有 GameCore setter；需要切换或使用瞬间建造作弊
- **外交** —— `DiplomacyManager` 仅限本地玩家；AI 对 AI 的外交没有 API
- **建城** —— 需要 `RequestOperation`，而它需要切换

### 行不通的部分
- **AI 对 AI 的外交** —— 没有已知 API 能让两个 AI 玩家进行谈判
- **对 AI 使用 `SetCivic()`** —— 会永久破坏它们的市政研究；请改用 `SetCulturalProgress()`
- **真正的同步对局** —— 回合是顺序的；智能体交替行动

### 公平性考量
- 智能体 A（人类玩家）拥有完整的 InGame API 访问权——正常游玩
- 智能体 B（被操控玩家）拥有对所有玩家的 GameCore 访问权——可以通过读取战争迷雾、敌方位置等来作弊
- **强制公平：** 协调器应只允许智能体 B 读取自己玩家的可见格。这需要给查询包上可见性检查。
- **生产不对称：** 智能体 A 使用正常队列；智能体 B 要么使用本地玩家切换（公平），要么使用瞬间建造（不公平）。为公平起见请使用切换。

---

## 实现阶段

### 阶段 1：Lua Mod + 回合检测
- 构建 `PuppeteerMod`（Lua 玩法脚本）
- 测试 `FinishMoves` + `RestoreMovement` 能否成功压制并重新启用 AI 单位
- 验证 `__puppet_turn_active` 可从 FireTuner 读取
- 测试 `PlayerManager.SetLocalPlayerAndObserver()` 切换
- **交付物：** 能在玩家 1 的回合中通过 FireTuner 手动为其下达命令

### 阶段 2：将 MCP 服务器参数化
- 为 `_lua_player_expr()`、`_lua_get_unit()`、`_lua_get_city()` 添加 `player_id: int | None = None`
- 贯穿传递到全部 66 处 `build_*` 调用点
- 为 InGame 操作添加 `_with_player_context()` 包装器
- 让 `player_id` 贯穿 `GameState` 方法
- **交付物：** 能调用 `get_units(player_id=1)` 并拿到玩家 1 的单位

### 阶段 3：协调器 + 智能体循环
- 构建轮询回合的协调器
- 接入 Anthropic API 以进行智能体决策
- 为智能体的工具使用定义工具 schema
- 实现顺序回合循环
- **交付物：** 两个智能体在同一局游戏中交替回合对战

### 阶段 4：公平性 + 打磨
- 为被操控玩家的查询添加可见性检查
- 生产/攻击使用本地玩家切换（而不是作弊）
- 添加游戏日志/回放以便分析
- 跑测试对局并迭代智能体提示词
- **交付物：** 带回放日志的公平智能体对战智能体对局

---

## 待解问题

1. **`GameEvents.PlayerTurnStartComplete` 触发得够快吗？** 如果有多个 mod 争抢该事件，AI 可能在我们的钩子运行之前就开始行动。需要测试。

2. **`PlayerManager.SetLocalPlayerAndObserver()` 在 GameCore 上下文中能用吗？** 它可能仅限 InGame。如果是这样，切换 + 命令 + 恢复的序列就需要在 InGame 上下文中进行。

3. **我们能抑制 AI 的城市生产/研究决策吗？** `FinishMoves` 只阻止单位行动。AI 在其回合中仍可能选择生产和研究。我们也许需要事后用 GameCore setter 覆盖它们。

4. **AI 的外交会怎样？** 内置 AI 在其回合处理期间仍可能发送代表团请求、宣布友谊或谴责。这些发生在 C++ 层面，无法从 Lua 拦截。

5. **我们能支持多少个被操控玩家？** 理论上，所有 AI 玩家都可以。实践中，每个被操控回合都会增加延迟（轮询 + 智能体思考 + 命令执行）。若有 7 个被操控玩家，回合可能耗时数分钟。

6. **我们也能对智能体 A 使用 `AutoplayManager` 吗？** 与其让智能体 A 作为人类游玩，我们可以对所有玩家使用 AutoPlay 并操控他们全部。这会让两个智能体受到同等的约束。但 AutoPlay 会把控制权交给内置 AI，这与目的相悖——我们将需要拦截*所有*玩家。
