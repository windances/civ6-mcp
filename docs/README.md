# Documentation

## For Users

- [Getting Started](../README.md#quick-start) — Setup and first game
- [Tool Reference](https://civbench.vercel.app/docs/tools) — All 76 MCP tools (web)

## For Developers

- [Architecture](architecture-diagrams.md) — Full stack from tool call to game engine, wire protocol, Lua contexts
- [Observability](observability.md) — Diary, tool logging, and spatial attention tracking
- [Save File Format](save-file-format.md) — Reverse-engineered .Civ6Save structure
- [Bypassing the Aspyr Launcher](research/bypassing_aspyr_launcher.md) — macOS launch automation

## Evaluation & Benchmarks

- [Benchmark Scenarios](paper/scenario-spec.md) — Three eval scenarios (Ground Control, Snowflake, Cry Havoc)
- [Game Reports](devlog/) — 12 full game logs with strategic post-mortems
- [Cross-Game Analysis](cross-game-analysis.md) — Recurring failure patterns across games 1–4

## Design & Research

- [Agent vs Agent](agent-vs-agent.md) — Multi-agent play design (proposal, not implemented)
- [Military Strategy Coverage](military-strategy-coverage.md) — Which military strategies the model can see, and which are actually enforced
- [Feature Ideas](feature-ideas.md) — Planned features with status markers
- [MCP Design Report](research/game_mcp_design_report.md) — Initial design research and best practices

## Essays

- [The Hallucination of Competence](agent-essays/the-hallucination-of-competence.md) — Gemini's self-analysis of strategic narrative bias (Game 12)

## Archive

- [Idea Research](research/idea_research.md) — Pre-implementation research (2025), superseded by [Architecture](architecture-diagrams.md)

## Chinese backups

Every document in this directory (and the advisor role files in `prompts/workers/`) has a Chinese
backup beside it, `<name>.cn.md`, **generated from the English file for a human reader** (human
instruction 2026-10-01). The English file is the source: edit it, then bring the backup back in step -
for a role file that means re-applying the preset (`scripts/use-strategy.ps1`) and then re-syncing
`prompts/workers/<role>.cn.md`, because the switcher copies the English file by name and leaves the
backup where it is.
A backup is never a source - nothing reads or writes it, and DSH cannot load it (it is not
`AGENTS.md`, and a skill has to be a file named exactly `SKILL.md`).

`tests/test_dsh_documents.py` holds both sets to the same four rules: the backup opens with a
`> 本文件是 \`<name>\` 的中文备份...` banner, carries a UTF-8 BOM (it holds Chinese), is a
translation rather than a stub (Chinese enough per prose line, the whole document's byte length, and
the same sections as the English), and carries every inline `` `code span` `` of the English
verbatim. `python .tools/audit-md-language.py` prints the whole corpus classified by role when you
want to see the state rather than the verdict.
