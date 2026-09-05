# Civ6 MCP Rewrite with DeepSeek Harness

## Orchestrator–Worker Implementation and Qualification Plan

This document describes how to integrate and progressively restructure
[`civ6-mcp`](https://github.com/lmwilki/civ6-mcp) using DeepSeek Harness (DSH)
with an orchestrator–worker architecture. It is intended to be reusable as an
implementation plan, test plan, and release qualification checklist.

## 1. Recommended Architecture

Use two orchestration layers:

1. A **development orchestrator** coordinates DeepSeek workers that implement,
   review, and qualify the system.
2. The delivered **Civ player orchestrator** coordinates read-only specialist
   workers and owns the only state-changing execution path.

Do not initially port the FireTuner and generated-Lua implementation. Keep the
existing Python MCP server as the environment adapter, then migrate components
only when replacement code demonstrates behavioral parity.

```text
DSH Civ Orchestrator
  |
  +-- Strategy worker
  +-- Military/map worker
  +-- Economy/city worker
  +-- Diplomacy/victory worker
  |
  +-- Plan validator and conflict resolver
  +-- Sole-writer action executor
          |
          v
  One shared civ6-mcp process
          |
          v
  Civ VI FireTuner on localhost:4318
```

### Central safety rule

Workers advise; the orchestrator acts. Only the orchestrator/executor may call
state-changing tools or `end_turn`. This prevents parallel workers from issuing
conflicting commands against a changing game state.

## 2. Standard Qualification Model

Every implementation stage must produce four kinds of evidence:

1. **Artifact** — code, configuration, schema, fixture, or report.
2. **Automated evidence** — repeatable tests with machine-readable results.
3. **Runtime evidence** — logs from a real or fixture-backed Civ session.
4. **Exit gate** — explicit pass/fail criteria.

A stage must not be declared complete based only on an agent's written report.
Failed qualification returns the work to the implementation stage; later stages
must not compensate for an unqualified foundation.

## 3. Phase 0 — Establish the Baseline

### Work

Pin the exact versions or revisions of:

- `civ6-mcp`
- DeepSeek Harness
- Python and `uv`
- Node.js and package manager
- Civilization VI and required DLC
- Test save files

Create representative scenarios:

1. Opening turn with units, research, and production.
2. Movement and combat.
3. Diplomacy or an incoming trade.
4. An end-turn blocker.
5. World Congress or a late-game save.
6. Save, reload, and recovery.

Run the original project's unit tests and capture its MCP tool inventory,
latency, errors, and turn behavior.

### Artifacts

- Version manifest
- Scenario/save manifest with hashes
- Baseline test report
- MCP tool inventory
- Baseline telemetry summary

### Qualification gate

- Existing Python tests pass unchanged.
- Exactly the expected MCP tools are discovered; the current baseline is 76.
- Ten consecutive `get_game_overview` calls succeed.
- Representative unit, city, map, research, and diplomacy reads succeed.
- One harmless action is accepted and verified from subsequent game state.
- At least three turns complete without a skipped or duplicated turn.
- Baseline latency, error rate, and token usage are recorded.

If this gate fails, repair the environment before beginning DSH integration.

## 4. Phase 1 — Install and Pin DeepSeek Harness

### Work

Install DSH and the components required for:

- MCP client connectivity
- In-process spawned subagents
- Subagent control
- Workflow execution
- Worker-thread workflow execution
- Structured worker output
- Tool restrictions

Pin all `@deepseek-ai/dsh-*` packages to the same release as the DSH host.
Avoid relying on npm tags that may resolve to incompatible release candidates.

Relevant upstream references:

- [DSH subagent subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/subagent.md)
- [DSH workflow packages](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/workflow)
- [DSH workflow worker](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/workflow/workflow-worker-thread/README.md)

### Artifacts

- Pinned package manifest and lockfile
- DSH composition/profile
- Minimal parallel-worker smoke workflow
- Installation and upgrade instructions

### Qualification gate

- `dsh --version` matches installed plugin versions.
- DSH starts with no unresolved plugin dependencies.
- A parent starts two workers concurrently.
- Both workers return schema-valid JSON.
- Cancellation terminates the workflow and all children.
- A configured depth limit prevents workers from delegating further.

## 5. Phase 2 — Connect DSH to `civ6-mcp`

### Work

Use the official DSH MCP client to launch the existing Python server. A starting
configuration is:

```yaml
- id: mcp-civ6
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: civ6
    transport: stdio
    command: uv
    args:
      - run
      - --directory
      - /absolute/path/to/civ6-mcp
      - civ-mcp
    cwd: /absolute/path/to/civ6-mcp
    env:
      CIV_MCP_DISABLE_LUA: "1"
    toolCallTimeoutMs: 720000
    failOnStartupError: true
```

The long timeout accommodates `end_turn`, which may spend several minutes
waiting for AI civilizations. DSH exposes discovered tools with qualified names,
for example:

```text
mcp__civ6__get_game_overview
mcp__civ6__get_units
mcp__civ6__unit_action
mcp__civ6__end_turn
```

Reference: [`@deepseek-ai/dsh-mcp-client`](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md).

### Artifacts

- DSH MCP configuration
- Tool-inventory comparison script or test
- Connection and reconnection test
- DSH-to-MCP compatibility report

### Qualification gate

- DSH discovers the complete expected tool inventory.
- Input schemas match the direct MCP schemas.
- Representative calls through DSH match direct MCP results.
- Killing the MCP child causes a visible failure and successful reconnection.
- Restarting DSH does not leave a second FireTuner connection.
- `end_turn` is not prematurely cancelled by the MCP timeout.
- `run_lua` is absent when `CIV_MCP_DISABLE_LUA=1`.

## 6. Phase 3 — Prove Single-Agent Parity

### Work

Before introducing workers, run a single DSH agent against the existing MCP
tools using the repository's `AGENTS.md` playbook. This separates integration
failures from orchestration failures.

### Artifacts

- Single-agent DSH persona and instructions
- Tool-call and turn logs
- Parity report against the baseline
- Failure classification report

### Qualification gate

- Complete at least 20 consecutive turns across two scenarios.
- No duplicate action submission occurs.
- No unexplained turn jump occurs.
- Every turn has all five required diary reflections.
- Every blocker is resolved or reported with the correct next action.
- Save/reload preserves the game identity and turn number.
- Tool-call success is at least 99%, excluding expected game-rule rejection.
- Outcomes do not regress materially from the original baseline.

## 7. Phase 4 — Define Canonical Contracts

Define and version three schemas.

### 7.1 Turn snapshot

```json
{
  "version": 1,
  "turn": 42,
  "gameId": "rome_123456",
  "overview": {},
  "units": [],
  "cities": [],
  "map": {},
  "diplomacy": [],
  "victory": {},
  "blockers": [],
  "recentEvents": []
}
```

### 7.2 Worker proposal

```json
{
  "worker": "military",
  "assessment": "Eastern border is exposed.",
  "priority": 80,
  "actions": [
    {
      "actionId": "T42-military-001",
      "tool": "unit_action",
      "arguments": {},
      "preconditions": [],
      "expectedEffects": [],
      "risk": "medium"
    }
  ],
  "warnings": [],
  "confidence": 0.82
}
```

### 7.3 Execution result

```json
{
  "actionId": "T42-military-001",
  "status": "executed",
  "toolResult": "...",
  "verified": true,
  "observedEffects": [],
  "replanRequired": false
}
```

### Artifacts

- Versioned JSON Schemas
- Typed representations
- Valid and invalid fixtures
- Schema migration policy

### Qualification gate

- Schemas are validated at every agent boundary.
- Missing required fields fail closed.
- Unknown tool names are rejected.
- Invalid coordinates and stale turn numbers are rejected.
- Duplicate `actionId` values are rejected.
- Every fixture snapshot round-trips without information loss.
- One hundred malformed-proposal tests produce no game mutation.

## 8. Phase 5 — Build Read-Only Specialist Workers

### Worker roles

| Worker | Responsibility |
| --- | --- |
| Strategy | Victory path, research, civics, and long-term priorities |
| Military/map | Threats, combat, movement, and exploration |
| Economy/cities | Production, growth, districts, builders, and spending |
| Diplomacy/victory | Deals, relations, religion, Congress, and rival victory threats |

### Work

The orchestrator gathers the snapshot once and sends the same immutable snapshot
to every worker. Workers should normally receive no Civ MCP tools. They analyze
the supplied snapshot and return a structured proposal.

Use fresh one-shot workers initially. Evaluate continuable workers later if
domain-specific memory provides measurable value.

Configure:

- Maximum workers per turn: 4
- Maximum delegation depth: 1
- Structured output required
- Per-worker runtime and token budget
- Maximum result size
- Independent timeout handling

### Artifacts

- Four worker personas
- Worker-specific proposal schemas or schema constraints
- Tool restrictions
- Worker unit and prompt-injection tests

### Qualification gate

- Workers cannot see or invoke mutation tools.
- Every worker receives the same snapshot version and turn.
- Every accepted worker result is schema-valid.
- Each worker stays within its assigned domain.
- Replaying a snapshot produces materially consistent priorities.
- A failed worker does not block successful workers.
- Workers cannot create grandchildren.
- No game state changes during the analysis phase.

## 9. Phase 6 — Implement the Orchestrator

### Turn state machine

```text
OBSERVE
  -> FAN OUT
  -> COLLECT
  -> VALIDATE
  -> RESOLVE CONFLICTS
  -> BUILD ORDERED PLAN
  -> EXECUTE
  -> VERIFY
  -> REFLECT
  -> END TURN
```

For a prototype, use the DSH workflow facility and `parallel()`. For production,
prefer a fixed, reviewable plugin or workflow rather than generating a new
orchestration script every turn.

### Deterministic conflict policy

1. Reject proposals for the wrong game or turn.
2. Reject invalid or forbidden tools.
3. Merge compatible read-only recommendations.
4. Detect multiple actions targeting the same unit or city.
5. Prioritize mandatory blockers over optional improvements.
6. Prioritize survival actions over economic optimization.
7. Let the orchestrator model choose only among validated alternatives.
8. Produce one serial action list.

### Artifacts

- Turn state machine
- Fan-out workflow
- Proposal collector and validator
- Deterministic conflict resolver
- Conflict fixtures and decision logs

### Qualification gate

- Exactly one canonical snapshot is created per orchestration cycle.
- At most four workers run per turn.
- Conflict fixtures always produce their expected result.
- The same unit cannot receive two terminal orders.
- A city cannot receive conflicting production orders.
- Worker failure produces degraded operation, not uncontrolled retries.
- Workflow cancellation leaves no child running.
- The final plan contains only allowlisted tools.

## 10. Phase 7 — Add the Sole-Writer Executor

Only the executor may invoke state-changing MCP tools.

### Execution protocol

Before each action:

1. Confirm game identity.
2. Confirm current turn.
3. Check that the action ID has not already executed.
4. Recheck relevant preconditions.
5. Execute the action once.
6. Query affected state.
7. Compare observed and expected effects.
8. Continue, replan, or stop safely.

Civ operations are not generally idempotent. Never blindly retry a timed-out
mutation. First query state to determine whether the original operation took
effect.

### Artifacts

- Mutation allowlist
- Serialized execution queue
- Per-turn action ledger
- Precondition and postcondition checkers
- Replanning interface

### Qualification gate

- Concurrent mutations are serialized.
- Duplicate action IDs never execute twice.
- A simulated timeout after a successful mutation is detected by verification.
- Stale actions are rejected.
- Failed verification stops dependent actions.
- Independent actions continue only when explicitly marked safe.
- Logs link proposal, MCP request, raw result, and verification.

## 11. Phase 8 — Integrate End-Turn Handling

Retain the Python server's end-turn state machine. Treat results as control
signals:

| Result | Orchestrator response |
| --- | --- |
| Production required | Replan city production |
| Research required | Ask strategy worker |
| Promotion required | Ask military worker |
| Diplomacy pending | Ask diplomacy worker |
| World Congress pending | Ask diplomacy/victory worker |
| Hang detected | Allow `civ6-mcp` recovery |
| Game over | Stop the orchestration loop |

### Qualification scenarios

- Empty production queue
- Completed research
- Unmoved unit
- Governor or promotion available
- Incoming diplomacy
- Incoming trade
- World Congress
- Normal AI turn
- Interrupted FireTuner connection
- Autosave recovery

### Qualification gate

- Every blocker routes to the correct worker or handler.
- Retrying `end_turn` does not duplicate the diary entry.
- A pending end-turn request is not sent twice.
- Turn number advances exactly once.
- Recovery reloads the expected identity and turn.
- Game-over state terminates all workers.

## 12. Phase 9 — Harden Security and Isolation

### Work

- Disable `run_lua`.
- Give workers no Civ mutation tools.
- Enforce an executor mutation allowlist.
- Bind the dashboard to `127.0.0.1`, unless remote access is intentional.
- Keep credentials out of prompts and worker environments.
- Limit worker count, depth, tokens, runtime, and result size.
- Record package versions and prompt hashes.
- Treat worker output as untrusted data.

### Qualification gate

- A worker prompt-injection test cannot invoke a Civ tool.
- Arbitrary Lua cannot be called.
- Dashboard endpoints are unreachable through non-loopback interfaces.
- Secret-pattern scanning finds no credentials in logs or diaries.
- Oversized and deeply nested proposals are rejected.
- Cancellation reaches worker and workflow quiescence within the limit.

## 13. Phase 10 — Shadow-Mode Evaluation

Run the orchestrated system without executing its proposals. Compare its plan to
the original single agent's actions.

### Metrics

- Proposal-schema validity
- Conflicting recommendations
- Missed mandatory blockers
- Tactical legality
- Strategic agreement
- Analysis latency
- Token and monetary cost
- Worker failure rate

### Initial qualification targets

- 100% of accepted proposals are schema-valid.
- Zero proposals use forbidden tools.
- Zero mandatory blockers are missed.
- At least 95% of proposed actions are legal.
- Post-resolution conflict rate is below 10%.
- Decision latency is no more than 2x the measured baseline.
- Token cost remains within the agreed budget.

Targets should be adjusted only from measured baseline evidence, with the reason
recorded in the qualification report.

## 14. Phase 11 — Controlled Live Evaluation

Run increasingly difficult live evaluations:

1. Five turns with human approval before every mutation.
2. Twenty-five turns with automatic execution.
3. Three fixed 50-turn scenarios.
4. One complete game.
5. Multiple civilizations and victory strategies.

### Qualification gate

- Zero duplicated mutations.
- Zero unexplained turn skips.
- At least 99% valid tool-call rate.
- All injected game crashes recover from the intended save.
- Every executed action has verification evidence.
- Every completed turn has a valid diary record.
- Strategic outcomes are no worse than the single-agent baseline for survival,
  expansion, yields, and victory progress.
- Additional latency and cost are measured and reported.

## 15. Phase 12 — Rollout with Fallback

Add an explicit operating-mode switch:

```text
CIV_AGENT_MODE=single
CIV_AGENT_MODE=orchestrated-shadow
CIV_AGENT_MODE=orchestrated-live
```

Retain the original single-agent path until the orchestrated implementation has
completed multiple full games successfully.

### Artifacts

- Mode switch and configuration
- Fallback procedure
- Operations runbook
- Release notes and known limitations
- Final qualification report

### Qualification gate

- Modes can be switched without code changes.
- The same save can resume in single-agent mode.
- A worker-system failure causes a controlled stop or configured fallback.
- Telemetry identifies the mode responsible for every decision.
- The release documents pinned versions, setup, limitations, and recovery.

## 16. Development Orchestrator Work Packages

The DeepSeek development orchestrator should delegate bounded work packages:

| Worker | Work package |
| --- | --- |
| Integration worker | DSH composition, MCP connection, version pinning |
| Contract worker | Schemas, personas, tool policies, validation |
| Runtime worker | Orchestration, conflict resolution, executor |
| Qualification worker | Fixtures, fault injection, metrics, reports |

The development orchestrator owns architectural decisions, integrates patches
serially, runs the full qualification suite, and rejects completion claims that
lack test evidence. A worker should not be the sole reviewer of code it authored.

## 17. Required Test Matrix

| Area | Normal case | Failure case | Required evidence |
| --- | --- | --- | --- |
| MCP | Discover and invoke all tools | Server crash/reconnect | Tool inventory and logs |
| Snapshot | Complete consistent state | Missing/malformed field | Schema-test report |
| Workers | Four valid proposals | Timeout, invalid JSON, prompt injection | Worker result ledger |
| Conflicts | Compatible proposals merge | Same unit/city targeted twice | Deterministic fixture results |
| Executor | Action succeeds and verifies | Timeout, stale state, partial effect | Action and verification log |
| End turn | Advances exactly once | Blocker, diplomacy, Congress, hang | Turn-transition log |
| Recovery | Correct autosave reloads | Wrong identity or regressed turn | Identity and turn evidence |
| Security | Read-only worker behavior | Forbidden tool and Lua attempt | Denial/audit logs |
| Performance | Parallel analysis completes | Slow or failed worker | Latency and cost report |

## 18. Definition of Done

The project is complete when all of the following are true:

- One full Civ VI game completes through DSH orchestration.
- No mutation is executed twice.
- No turn is skipped unexpectedly.
- Every action is traceable from proposal through verification.
- All worker boundaries enforce schema and tool restrictions.
- Injected connection and game failures recover correctly.
- Diaries and telemetry allow the game to be replayed and audited.
- Strategic results meet or exceed the single-agent baseline.
- Latency and cost remain within agreed limits.
- The single-agent fallback remains operational.
- Setup, operation, qualification, and recovery are documented.

## 19. Recommended Implementation Order

The dependency-safe implementation order is:

```text
Baseline
  -> DSH installation
  -> MCP integration
  -> Single-agent parity
  -> Schemas
  -> Read-only workers
  -> Orchestrator
  -> Sole-writer executor
  -> End-turn integration
  -> Security hardening
  -> Shadow evaluation
  -> Controlled live evaluation
  -> Rollout
```

Do not start a full FireTuner or TypeScript port until the orchestrated system
has passed live qualification using the existing Python adapter. At that point,
individual adapter domains can be replaced behind contract tests without also
changing the agent architecture.

## 20. Implemented Milestone (2026-09-05)

The workspace now contains a directly runnable Milestone 1 foundation:

- project-local DeepSeek Harness `0.1.2-rc.1` and project-local `uv`;
- upstream `civ6-mcp` pinned at commit
  `dd2019056371b92ea4854e879ddf05a8cad95e8a`;
- a DSH overlay that launches `civ-mcp`, removes `run_lua`, disables general
  delegation routes, and provides one depth-limited no-tool advisor route;
- four specialist prompts, three fail-closed JSON Schemas, and a sole-writer
  orchestration skill;
- headless and web launch commands; and
- static, adapter-unit, MCP-protocol, and resolved-configuration checks.

Run the complete keyless qualification gate with:

```bash
npm run qualify:all
```

This gate qualifies the foundation as follows:

1. `qualify` parses all schemas, checks worker prompts, confirms the overlay's
   safety settings, and compares the MCP inventory against the pinned baseline.
2. `qualify:python` runs the upstream adapter regression tests from the intended
   `tests/` directory.
3. `qualify:mcp` initializes the real adapter over stdio, lists tools, verifies
   that `run_lua` is absent, and checks the required orchestrator tools.
4. `dsh:dump` asks the installed DSH binary to resolve the overlay. Any invalid
   component, patch, or profile fails the command.

For a live qualification, start Civilization VI with FireTuner enabled, export
`DEEPSEEK_API_KEY`, and run:

```bash
npm run dsh:play -- "Play one complete turn using the civ6-orchestrator skill."
```

Milestone 1 is not the final rollout gate. Live parity, fault injection,
multi-turn shadow evaluation, and deterministic code-level enforcement of the
proposal/action ledger remain governed by Phases 3 through 12 above.
