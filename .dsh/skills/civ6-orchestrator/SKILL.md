---
name: civ6-orchestrator
description: Safely play Civilization VI through civ6-mcp using one sole-writer orchestrator and read-only specialist advisors.
---

# Civ6 Orchestrator

Use this procedure whenever controlling a live Civ VI game.

## Phase 1: Orient

1. Call `mcp__civ6__get_diary` when resuming an existing game or compacted
   context.
2. Call `mcp__civ6__get_game_overview` and record the game identity and turn.
3. Gather units, cities, relevant map areas, diplomacy, victory progress, and
   notifications. Avoid broad periodic queries when they are not due.
4. Construct one canonical textual snapshot. Do not let workers query the live
   game independently.

## Phase 2: Delegate analysis

Read the four role files under `prompts/workers/`. Start each role through
`civ_advisor` with the complete canonical snapshot and its role instructions.
Workers have no tools. Ask each worker to return only JSON matching
`contracts/worker-proposal.schema.json`.

When background execution is available, start all applicable advisors before
collecting their results. Use no more than four advisors per turn.

## Phase 3: Validate and synthesize

Reject a proposal if it:

- names the wrong game or turn;
- is not valid JSON;
- contains an unknown or forbidden tool;
- references a missing unit or city;
- violates an explicit game-state precondition; or
- duplicates an action identifier.

Resolve conflicts in this order:

1. Mandatory end-turn blockers
2. City or unit survival
3. Forced combat and tactical safety
4. Production, research, growth, and spending
5. Diplomacy and victory-path advancement
6. Exploration and optional optimization

Build one ordered action list. Never schedule conflicting terminal orders for
the same unit or city.

## Phase 4: Execute as sole writer

For every action:

1. Confirm the current turn still matches the plan.
2. Confirm the action has not already executed.
3. Recheck its preconditions.
4. Call the mutation tool once.
5. Query the affected unit, city, or global state.
6. Compare observed effects with expected effects.
7. Stop dependent actions and replan if verification fails.

Never retry a timed-out mutation without querying state first.

## Phase 5: End the turn

Prepare all five non-empty diary reflections: tactical, strategic, tooling,
planning, and hypothesis. Call `mcp__civ6__end_turn` once.

If it reports a blocker, resolve the blocker and retry according to the MCP
server's instructions. Do not repeat or replace the original reflections merely
because a blocker required another call.

Treat the end-turn result as the beginning of the next turn's observations.
Stop immediately on game-over, identity mismatch, turn regression, or failed
recovery.
