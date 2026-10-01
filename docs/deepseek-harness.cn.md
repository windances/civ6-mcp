> 本文件是 `deepseek-harness.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# Civ6 DeepSeek Harness 编排器

本工作区在 DeepSeek Harness（DSH）下运行现有的 `civ6-mcp` FireTuner 适配器，并增加了一套安全的编排器-工作者运行模型。

第一个里程碑刻意保留了 Python/Lua 适配器。DSH 负责智能体的推理与委派，而唯一的父级编排器始终是唯一能调用会改变状态的 Civ 工具的一方。顾问工作者收到的是一份不可变的文本快照，并且没有工具。

## 目录结构

```text
src/civ_mcp/                     Python MCP environment adapter
dsh/civ6.cordis.yml              DSH MCP and safe-worker overlay
.dsh/skills/civ6-orchestrator/   Orchestrator operating procedure
prompts/workers/                 Specialist worker instructions
contracts/                       Versioned JSON Schemas
baseline/                        Pinned upstream baseline
scripts/                         Bootstrap, launch, and qualification commands
```

## 前提条件

- 带有 Gathering Storm 资料片的 Civilization VI
- 在 TCP 端口 4318 上启用 FireTuner
- Node.js 24 或更新版本
- 环境中或 DSH 凭据中可用的 `DEEPSEEK_API_KEY`

引导脚本会安装项目本地的 `uv`，下载兼容的 Python，并创建 Python 环境。它不会全局安装任何东西。

## 安装配置

```bash
npm run bootstrap
npm run qualify:all
```

## 查看解析后的 DSH 配置

```bash
npm run dsh:dump
```

## 无头运行

启动 Civ VI 并载入一个游戏，然后运行：

```bash
npm run dsh:play -- "Play one complete turn using the civ6-orchestrator skill."
```

该命令使用位于 `.dsh-home/` 的项目本地 DSH 主目录，因此会话、凭据和配置文件状态不会与用户日常的 DSH 环境混在一起。

首次无头模型回合必须设置 `DEEPSEEK_API_KEY`。静态、Python、MCP 协议和 DSH 配置这几项资格检查不需要该密钥，也不需要正在运行的游戏。

## 运行 DSH Web 界面

```bash
npm run dsh:web
```

创建一个 Standard 智能体，并要求它使用 `civ6-orchestrator` 技能。

## 本里程碑中的安全属性

- `run_lua` 已从 MCP 工具清单中移除。
- 工作者的 JSON 在进入行动计划之前会经过模式（schema）校验。
- 未知工具、过期的回合、重复的行动 ID、缺失的实体以及无效坐标都会以失败关闭（fail closed）。
- 冲突以确定性的方式解决，变更通过一个串行化、带验证感知的行动账本执行。
- Civ 遥测与日记仍保存在 `.civ6-mcp-data/` 下。
- 内嵌的 Civ 仪表盘 API 在 DSH 模式下被禁用。
- 通用 subagent、fork、动态 workflow 和 Ralph 路由被 overlay 禁用。
- 专用的 `civ_advisor` 路由以空的工具允许列表启动工作者。
- 顾问深度上限为一层。
- 父级编排器是唯一被允许改动游戏的执行者。
- 面向长时间的 AI 回合，MCP 调用允许 12 分钟超时。
- 除非被显式更改，启动脚本会禁用 DSH 遥测。

完整的实现与资格检查路线图见 [`DSH_ORCHESTRATOR_REWRITE_PLAN.md`](DSH_ORCHESTRATOR_REWRITE_PLAN.md)。

## 当前里程碑

里程碑 1 已经可以运行：DSH 能够加载项目 overlay、启动 MCP 适配器、发现其受限的工具清单，并对外提供一个无工具的顾问路由。契约、工具策略、冲突解决以及唯一写入者账本如今都有了确定性的运行时实现和基于夹具（fixture）的测试。把这个核心接入一个固定的 DSH 插件，以及完成实机对战资格检查，仍是接下来的里程碑。
