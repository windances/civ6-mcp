# civ6-mcp

一个让 LLM agent 打完整局《文明 VI》的 MCP 服务器。

把任何兼容 MCP 的客户端——Claude Code、Codex、Gemini CLI，或你自己写的——接到正在运行的《文明 VI》上。
agent 读取游戏状态、移动单位、管理城市、进行外交并结束回合，全程走游戏自己那套**会执行规则**的 API。
不作弊，也不需要视觉模型。

## DeepSeek Harness 编排器

这个 fork 附带一个可直接运行的
[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
编排器。父 agent 独占与游戏的连接，并把一份**不可变的回合快照**分发给四个专家顾问：

| 顾问 | 职责 |
|---------|----------------|
| 战略 | 长期优先级、科技、市政与胜利路线 |
| 军事与地图 | 战斗、单位安全、探索与开拓 |
| 经济与城市 | 生产、成长、区划、贸易与花费 |
| 外交与胜利 | 关系、协议、世界议会与胜利威胁 |

顾问 worker **没有任何工具**，改不了游戏。它们把建议动作交回父 agent，由父 agent 校验冲突并**独占写入权**。

### 用 DeepSeek Harness 运行

前置条件：

- Node.js 24 或更高
- 已启用 FireTuner 的《文明 VI》，监听 TCP 4318
- 在 shell 里导出 `DEEPSEEK_API_KEY`

Bootstrap 会把 DSH、`uv` 和 Python 装进项目本地目录：

```bash
git clone https://github.com/windances/civ6-mcp.git
cd civ6-mcp
npm run bootstrap
```

启动《文明 VI》、载入一局，然后启动无头编排器：

```bash
export DEEPSEEK_API_KEY="your-key"
npm run dsh:play -- \
  "Play one complete turn using the civ6-orchestrator skill."
```

改用 DSH 的 web 界面：

```bash
npm run dsh:web
```

### 资质校验

完整的无密钥门禁会跑：schema 与 prompt 检查、确定性的编排器测试、Python 回归套件、一次真实的
MCP stdio 握手、受限的工具发现，以及 DSH overlay 解析：

```bash
npm run qualify:all
```

这道门禁不需要 DeepSeek 密钥，也不需要游戏在跑。**实时回合**的资质校验两者都需要。

当前里程碑中的安全控制包括：

- 从 DSH 的 MCP 清单中**移除**了任意 `run_lua` 访问；
- 关闭了通用的 subagent、fork、workflow 与 Ralph 路由；
- 只保留一条有深度限制、工具白名单为空的顾问路由；
- 可执行的提案校验、确定性的冲突消解，以及**只追加**的每回合动作台账；
- 串行化的变更执行，带过期状态、前置条件、后置条件与超时歧义处理；
- 文明遥测、日记、DSH 状态与依赖缓存全部留在工作区内；
- 无头模式下关闭内嵌的文明仪表盘。

目录布局与运维见 [DSH 快速上手](docs/deepseek-harness.md)。
[实现与资质计划](docs/DSH_ORCHESTRATOR_REWRITE_PLAN.md)
记录了每个阶段、验收门禁、故障测试与剩余里程碑。

<!-- TODO: Add screenshot or GIF of agent playing -->

## 能力

覆盖完整游戏循环的 80 个工具：

- **单位** —— 列出、移动、攻击、固守、建城、建造改良、晋升、升级
- **城市** —— 查看、设置生产、用金币购买单位/建筑、管理侧重
- **地图** —— 探索地形、资源、战争迷雾；给出开拓与区划选址建议
- **科研** —— 浏览科技与市政树、设置研究目标
- **外交** —— 关系、修正项、代表团、大使馆、同盟、和平协议
- **贸易** —— 发起与回应协议、管理商路与目的地
- **政体** —— 更换政策卡、更换政体、选择时代纪念
- **总督** —— 任命、派驻城市、晋升
- **宗教** —— 创立万神殿与宗教、选择信条、跟踪传播
- **伟人** —— 招募、赞助、拒绝
- **世界议会** —— 对决议投票、管理外交支持
- **胜利** —— 跟踪全部胜利条件的进度
- **游戏生命周期** —— 存档、载入、启动、重启、结束进程

每个回合，`end_turn` 都会取前后快照并报告发生了什么：哪些单位受伤、哪些城市成长、什么生产完成、
以及在你城市附近发现了什么威胁。

## 快速开始

### 1. 配置《文明 VI》

启用 FireTuner 调试接口并配置推荐设置：

| 设置 | 值 | 原因 |
|---------|-------|-----|
| **Tuner** | 启用 | **必需** —— 打开 MCP 服务器要连接的 TCP 调试端口。会禁用成就。 |
| **Auto End Turn** | 禁用 | 回合何时结束由 agent 控制。自动结束会干扰阻塞项的解决流程。 |
| **窗口模式** | 推荐 | 让你能在 agent 打的时候看着游戏。基于 OCR 的载入存档也依赖它。 |

**Windows：** 三项都能在游戏内 Options 菜单里找到。Tuner 这一项在 gameplay options 下显示为
"Tuner (disables achievements)"。

**macOS：** 菜单里没有暴露 Tuner 设置。直接编辑 `AppOptions.txt`，设 `EnableTuner 1`：

```
~/Library/Application Support/Sid Meier's Civilization VI/Firaxis Games/Sid Meier's Civilization VI/AppOptions.txt
```

**Linux：** 与 macOS 相同 —— 直接编辑 `AppOptions.txt`，设 `EnableTuner 1`：

```
~/.local/share/aspyr-media/Sid Meier's Civilization VI/AppOptions.txt
```

<details>
<summary><strong>Windows：额外设置</strong></summary>

**安装 Civ 6 SDK** —— tuner server 属于 SDK，不属于基础游戏：
1. 在 Steam 里进入 库 → 按 工具 筛选
2. 找到并安装 "Sid Meier's Civilization VI SDK"

**重要提醒：**
- 运行 civ6-mcp 之前先关掉 `FireTuner.exe`（SDK 的图形工具）—— 游戏**同一时刻只允许一个** tuner 连接
- **不要**从 WSL 里运行 —— WSL2 与 Windows 之间的网络桥接不可靠，tuner server 在连接失败后会锁死
- 如果连接失败，**重启游戏** —— tuner 在一次糟糕的握手之后常常挂起，不回收进程就不会恢复
</details>

<details>
<summary><strong>Linux：额外说明</strong></summary>

- 必须是 **Linux 原生版本** —— FireTuner 调试接口编译在原生二进制里。Proton/Wine 版本不暴露它。
- 游戏是单个 `Civ6` 进程，通过 Steam Linux Runtime（scout-on-soldier）启动。
- GUI 自动化（基于 OCR 的菜单导航）需要 **X11**。在 Wayland 下游戏通常跑在 XWayland 里，一般可用，
  但原生 X11 会话最可靠。
</details>

重启《文明 VI》。游戏会监听 TCP 4318 等待连接。

### 2. 安装

```bash
git clone https://github.com/windances/civ6-mcp.git
cd civ6-mcp
uv sync
```

要用 GUI 自动化功能（截图、基于 OCR 的菜单导航）：

```bash
# macOS
uv pip install 'civ6-mcp[launcher-macos]'

# Windows（使用 Windows 自带的 OCR —— 不需要外部二进制）
uv pip install 'civ6-mcp[launcher-windows]'

# Linux (Ubuntu/Debian)
sudo apt install xdotool tesseract-ocr
uv pip install 'civ6-mcp[launcher-linux]'
```

### 3. 测试连接

在《文明 VI》运行且已载入一局的情况下：

```bash
uv run python scripts/test_connection.py
```

应当看到一次成功的握手，以及一份 Lua 状态列表（GameCore_Tuner、InGame 等）。

### 4. 配置你的 MCP 客户端

服务器走 stdio。把你的客户端指向它：

<details>
<summary><strong>Claude Code</strong></summary>

仓库自带 `.mcp.json` —— 会被自动检测：

```bash
cd civ6-mcp
claude
```
</details>

<details>
<summary><strong>Claude Desktop</strong></summary>

加进你的配置文件：
- macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows：`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "civ6": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/civ6-mcp", "civ-mcp"]
    }
  }
}
```
</details>

<details>
<summary><strong>Codex</strong></summary>

加进项目根目录的 `.codex/config.toml`：

```toml
[mcp_servers.civ6]
command = "uv"
args = ["run", "--directory", "/path/to/civ6-mcp", "civ-mcp"]
```
</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

加进项目根目录的 `.gemini/settings.json`：

```json
{
  "mcpServers": {
    "civ6": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/civ6-mcp", "civ-mcp"]
    }
  }
}
```
</details>

<details>
<summary><strong>其他 MCP 客户端</strong></summary>

服务器讲 stdio JSON-RPC：

```bash
uv run civ-mcp
```
</details>

### 5. 开始打

在《文明 VI》里载入一局、连上客户端，然后试：

```
Play my Civ 6 game. Start by getting an overview, then check units and
cities, and play through the turn.
```

agent 会用 `get_game_overview` 定位，扫描地图找威胁，移动单位，设置生产与研究，处理外交，然后结束回合。

## 开局：一个开局一个数据目录

多个开局可以并存而互不共享任何东西。数据根目录下每个开局一个子目录，外加一个 `current` 指针，
而且**每个脚本都会替你解析 `current`** —— 没有任何命令需要传 run 参数。

```
.civ6-mcp-data/
  current                        -> china-911679432-a
  runs/
    china-911679432-a/           run.json、日记、退役目标状态、心跳、saves/
    china--1894041591/           ...
  branches/                      回滚归档（共用）
  loc-en-names.json              本地化表（共用）
```

每个 run 的 `run.json` 声明这一局的身份，以及它期望的 `(civ, seed)`。每次会话开始都会把它与载入的游戏比对，
所以"游戏在会话底下被换掉了"会被**报告出来**，而不是继续把回合写进另一个 run 的日记：

```
SESSION  data_dir=.../runs/china-911679432-a  match=china_911679432  diary=last_agent_turn=110 ...
RUN      china-911679432-a "China conquest, first line"  (civ/seed match, played to T110)
```

不匹配时打印 `RUN MISMATCH`，且 `play-turn.py end` **拒绝推进回合**（除非 `--force`）。
目录里没有清单时不做任何校验，所以未命名的环境行为与从前完全一致。

```powershell
# 命名本局，身份取自载入的游戏
.venv\Scripts\python.exe scripts\run.py init --id china-a --label "China conquest A" --from-game

.venv\Scripts\python.exe scripts\run.py status          # 本目录声明的身份 vs 游戏实际的身份
.venv\Scripts\python.exe scripts\run.py touch --turn 116
.venv\Scripts\python.exe scripts\run.py clear

# 把已有的扁平数据目录整理进 runs/（先看计划，再 apply，再 verify）
.venv\Scripts\python.exe scripts\runs.py inventory
.venv\Scripts\python.exe scripts\runs.py plan
.venv\Scripts\python.exe scripts\runs.py apply --current china-911679432-a
.venv\Scripts\python.exe scripts\runs.py verify
```

本地化表每台机器从游戏自己的文本文件建一次，所有开局共用。无论游戏设成什么语言，它都让工具输出保持英文，
并负责解析旁边没有类型码的名字（城市名尤其如此）。**表不存在不是错误** —— 一切都按游戏返回的原样打印。

```powershell
.venv\Scripts\python.exe scripts\build-loc-names.py            # 建立或刷新
.venv\Scripts\python.exe scripts\build-loc-names.py --check    # 只报告
```

## 命令参考

每个脚本的用法都在 [`scripts/README.md`](scripts/README.md)：开局与数据目录布局、路线 A 的回合循环、
回滚、日记、本地化，以及每个文件一行说明。

## 作为一个基准

《文明 VI》是评测 LLM 战略推理的极佳环境。一局 300 个以上的回合，决策不断累积，信息不完整，
多个目标互相竞争 —— 比单回合或短视界的任务高出一个量级。

- **多回合规划** —— 决策在数百回合中累积，回报延迟
- **信息不完整** —— 战争迷雾、隐藏的 AI 意图、未探索的地图
- **资源管理** —— 在金币、生产、科研、文化、信仰与军事之间取舍
- **对手建模** —— 解读外交信号、预判 AI 行为
- **战略适应** —— 应对威胁、在局中调整优先级

MCP 接口提供了一个干净的抽象：模型收到叙述式的游戏状态文本，并以工具调用作答。所有游戏规则由引擎执行。
配套的 web 应用可以逐回合回放对局。

## 工作原理

```
Claude / Any MCP Client
    |  stdio (JSON-RPC)
    v
MCP Server (Python)    <- 80 tools
    |
    |  Generates Lua code at runtime
    |  TCP :4318
    v
Civilization VI        <- Game is the TCP server
```

服务器通过 FireTuner 调试协议与《文明 VI》保持一条长连接。它生成 Lua 代码，在游戏的两个 Lua 虚拟机里执行
（GameCore 用于读状态，InGame 用于下指令），解析输出，并把叙述式文本返回给 LLM。

仓库附带一份 [AGENTS.md](AGENTS.md) playbook（以 `CLAUDE.md` 软链接给 Claude Code 用），里面有给 agent 的
详细说明：回合循环、战斗、外交、常见陷阱。完整开发历程见 [devlog](docs/devlog/)，包括逆向 FireTuner 协议
以及一路上发现的大量 API 怪癖。

## 环境要求

- **macOS、Windows 或 Linux**，装有《文明 VI》（Steam 版，含风云变幻 DLC）
- **Python 3.12+** 与 [uv](https://docs.astral.sh/uv/)
- 一个 **MCP 客户端**（Claude Code、Codex、Gemini CLI，或任何兼容 MCP 的客户端）

## 许可

MIT
