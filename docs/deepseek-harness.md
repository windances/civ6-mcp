# Civ6 DeepSeek Harness Orchestrator

This workspace runs the existing `civ6-mcp` FireTuner adapter under DeepSeek
Harness (DSH) and adds a safe orchestrator–worker operating model.

The first milestone deliberately retains the Python/Lua adapter. DSH owns agent
reasoning and delegation, while one parent orchestrator remains the sole caller
of state-changing Civ tools. Advisor workers receive an immutable text snapshot
and have no tools.

## Layout

```text
src/civ_mcp/                     Python MCP environment adapter
dsh/civ6.cordis.yml              DSH MCP and safe-worker overlay
.dsh/skills/civ6-orchestrator/   Orchestrator operating procedure
prompts/workers/                 Specialist worker instructions
contracts/                       Versioned JSON Schemas
baseline/                        Pinned upstream baseline
scripts/                         Bootstrap, launch, and qualification commands
```

## Prerequisites

- Civilization VI with Gathering Storm
- FireTuner enabled on TCP port 4318
- Node.js 24 or newer
- A `DEEPSEEK_API_KEY` available in the environment or DSH credentials

The bootstrap installs a project-local `uv`, downloads a compatible Python, and
creates the Python environment. It does not install anything globally.

## Setup

```bash
npm run bootstrap
npm run qualify:all
```

## Inspect the resolved DSH configuration

```bash
npm run dsh:dump
```

## Run headless

Start Civ VI and load a game, then run:

```bash
npm run dsh:play -- "Play one complete turn using the civ6-orchestrator skill."
```

The command uses a project-local DSH home at `.dsh-home/`, so sessions,
credentials, and profile state do not mix with a user's normal DSH environment.

`DEEPSEEK_API_KEY` must be set for the first headless model turn. The static,
Python, MCP protocol, and DSH configuration qualifications do not require the
key or a running game.

## Run the DSH web interface

```bash
npm run dsh:web
```

Create a Standard agent and ask it to use the `civ6-orchestrator` skill.

## Safety properties in this milestone

- `run_lua` is removed from the MCP tool inventory.
- Worker JSON is schema-validated before entering the action plan.
- Unknown tools, stale turns, duplicate action IDs, missing entities, and
  invalid coordinates fail closed.
- Conflicts resolve deterministically and mutations execute through a
  serialized, verification-aware action ledger.
- Civ telemetry and diaries remain under `.civ6-mcp-data/`.
- The embedded Civ dashboard API is disabled in DSH mode.
- Generic subagent, fork, dynamic workflow, and Ralph routes are disabled by the
  overlay.
- The dedicated `civ_advisor` route spawns workers with an empty tool allowlist.
- Advisor depth is capped at one.
- The parent orchestrator is the only actor allowed to mutate the game.
- MCP calls allow a 12-minute timeout for long AI turns.
- DSH telemetry is disabled by the launch scripts unless explicitly changed.

The complete implementation and qualification roadmap is in
[`DSH_ORCHESTRATOR_REWRITE_PLAN.md`](DSH_ORCHESTRATOR_REWRITE_PLAN.md).

## Current milestone

Milestone 1 is runnable: DSH can load the project overlay, start the MCP adapter,
discover its restricted tool inventory, and expose a no-tool advisor route.
Contracts, tool policies, conflict resolution, and the sole-writer ledger now
have deterministic runtime implementations and fixture-backed tests. Wiring
this core into a fixed DSH plugin and completing live-game qualification remain
the next milestones.
