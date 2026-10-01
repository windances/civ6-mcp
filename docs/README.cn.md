> 本文件是 `README.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# 文档

## 面向用户

- [快速开始](../README.md#quick-start) — 安装配置与第一局游戏
- [工具参考](https://civbench.vercel.app/docs/tools) — 全部 76 个 MCP 工具（网页版）

## 面向开发者

- [架构](architecture-diagrams.md) — 从工具调用到游戏引擎的完整技术栈、通信协议、Lua 上下文
- [可观测性](observability.md) — 日记、工具日志与空间注意力追踪
- [存档文件格式](save-file-format.md) — 逆向工程得到的 .Civ6Save 结构
- [绕过 Aspyr 启动器](research/bypassing_aspyr_launcher.md) — macOS 启动自动化

## 评估与基准

- [基准场景](paper/scenario-spec.md) — 三个评估场景（Ground Control、Snowflake、Cry Havoc）
- [对局报告](devlog/) — 12 份完整对局日志，附战略复盘
- [跨对局分析](cross-game-analysis.md) — 对局 1–4 中反复出现的失败模式

## 设计与研究

- [智能体对智能体](agent-vs-agent.md) — 多智能体对局设计（提案，尚未实现）
- [军事策略覆盖](military-strategy-coverage.md) — 哪些军事策略能被模型看到，哪些真正被强制执行
- [功能构想](feature-ideas.md) — 带状态标记的规划功能
- [MCP 设计报告](research/game_mcp_design_report.md) — 初期设计研究与最佳实践

## 随笔

- [胜任的幻觉](agent-essays/the-hallucination-of-competence.md) — Gemini 对战略叙事偏误的自我分析（第 12 局）

## 归档

- [构想研究](research/idea_research.md) — 实现前的研究（2025），已被[架构](architecture-diagrams.md)取代

## 中文备份

本目录下的每一份文档（以及 `prompts/workers/` 里的顾问角色文件）旁边都有一份中文备份
`<name>.cn.md`，**由英文文件翻译而来，供人阅读**（人类指令 2026-10-01）。英文文件才是来源：先改英文，
再把备份同步回来——对角色文件而言，这意味着先重新应用预设（`scripts/use-strategy.ps1`），再重新同步
`prompts/workers/<role>.cn.md`，因为切换脚本按文件名复制英文文件，而把备份留在原地。
备份永远不是来源——没有任何代码读它或写它，DSH 也加载不了它（它不是 `AGENTS.md`，
而技能必须是恰好名为 `SKILL.md` 的文件）。

`tests/test_dsh_documents.py` 把两套备份都按同样四条规则检查：备份以
`> 本文件是 \`<name>\` 的中文备份...` 开头的横幅开头；带 UTF-8 BOM（因为含中文）；是翻译而不是
摘要（按正文行数计算的中文量、整篇字节长度、以及与英文相同的章节数）；并且逐字保留英文里每一个
行内 `` `code span` ``（代码片段）。想直接看状态而不是只看结论时，运行
`python .tools/audit-md-language.py`，它会按角色分类打印整棵语料库。
