# Agent decision and execution efficiency

> **Local addition**, not part of upstream `civ6-mcp`. Produced by measuring the
> orchestrator's own telemetry on a live game; re-run the tool to refresh it.

Measured over **105 turns / 12 orchestrator runs / 13.3 hours** of wall clock on
`china_-1894041591`, from civ6-mcp tool-call telemetry.

## 1. Method

`.tools/efficiency-report.mjs` reads every `log_<civ>_<seed>_<run>.jsonl`, and per
turn computes:

- wall-clock duration and tool-call count;
- query vs mutation split (`category` field);
- **thinking time** — the silent gaps that precede a non-`end_turn` call;
- **waiting time** — the silent gaps that precede an `end_turn` call, i.e. the
  game processing the turn;
- repeated identical calls within one turn (same tool, same arguments);
- per-run throughput (turns/hour), which is only meaningful inside a single run.

## 2. Measurements

| per turn | mean | median | worst |
|---|---|---|---|
| duration | **2m32** | **53s** | 45m27 * |
| tool calls | 10.4 | 7 | 117 * |
| queries | 4.1 | 2 | 65 |
| mutations | 5.2 | 4 | 49 |
| thinking (LLM) | 78s | 19s | 24m44 |
| `end_turn` wait | 73s | 29s | 20m43 |
| longest single thinking gap | 34s | 11s | 9m43 |

\* inflated by cross-run merging — see §6.

**Distribution of counted turn time:** thinking **52%**, waiting on the game **48%**.

**Call mix:** queries 44%, mutations 56%.

**Repeated identical calls inside one turn: 114** out of 1100 calls (**10%**).

| run | turns | span | throughput |
|---|---|---|---|
| `iron-garnet-mesa-39` | 13 | 0.24h | **53.6**/h |
| `penal-pearl-obelisk-10` | 29 | 0.87h | 33.2/h |
| `exalted-ivory-flagship-19` | 15 | 0.52h | 29.0/h |
| `muted-sepia-flagship-68` | 10 | 0.37h | 26.7/h |
| `walled-ochre-siege-59` | 25 | 1.11h | 22.5/h |
| `granite-sienna-ballista-08` | 1 | 0.25h | 4.0/h |

**Planning baseline: 22–34 turns/hour.** A 300-turn Quick game therefore costs
roughly **10–13 hours** of wall clock; ten turns costs 20–30 minutes.

## 3. Diagnosis: the cost is in the tail, not the median

The mean turn is **3x the median** (2m32 vs 53s). Most turns are fast; a few
dominate. Three sources, in order of contribution:

1. **`end_turn` stalls (worst 20m43).** Caused by an un-ordered unit: the game
   refuses to advance and the adapter polled its full ~9-minute budget. **Already
   fixed structurally** in `end_turn.py` (§4.1).
2. **Restarts duplicate work.** Turn 91 appears in **three** different run logs.
   Each restart re-runs a full Phase-1 orientation for the turn it resumes on —
   roughly 15–20 redundant queries. Restarts are not cheap.
3. **Long planning silences.** Turn 51 shows 17 minutes of thinking for 31 calls —
   the parent agent's own long model turn, possibly including advisor waits.

## 4. Optimizations, by payoff

### 4.1 Already landed: structural fix for the stall

`ENDTURN_BLOCKING_UNITS` is now auto-resolved (fortify combat units, then skip the
rest) instead of bouncing the turn. Expected effect after the next restart: the
`end_turn` wait drops from a 73s mean / 20m worst toward 30–40s, and **waiting
falls from 48% of turn time to roughly 20%**.

### 4.2 Stop paying for restarts

Strategy changes no longer need a restart (the directive is re-delivered with the
`end_turn` result), so the only remaining reason to restart is to load code
changes. Batch those. And because the diary is now keyed per game rather than per
run, a resumed session can call `get_diary` instead of re-deriving the whole
situation — worth about 15–20 queries per restart.

### 4.3 Remove the 10% duplicate calls

114 identical calls recurred inside a single turn (verify-after-mutate followed by
a re-query in the next phase). Worth adding to the skill:

> Within a turn, reuse a state query already made, unless a mutation has run since.

Expected effect: ~10% fewer calls and a proportional cut in thinking time.

### 4.4 Decide the advisor layer

Currently the worst of both worlds: two `civ_advisor` calls in 13 hours, with the
parent inventing its own advisor roles (see `SETUP-WINDOWS.md` §10 — the worker
prompt files are never read). The coordination cost is paid; the independent-
perspective benefit is not collected.

| Option | Effect |
|---|---|
| Bind roles to the tool call (so a call cannot arrive without its role) | recovers independent perspectives — e.g. the "imported Iron dies on declaration of war" blind spot is exactly a diplomacy-advisor finding |
| Drop the advisor layer | faster, cheaper planning; accept a single-agent architecture |

The data favours measuring the single-agent configuration first, since the
advisor layer is currently pure cost.

### 4.5 Use throughput for planning

22–34 turns/hour is the measured baseline. Budget 10–13 hours for a full 300-turn
game rather than extrapolating from a few minutes per turn.

## 5. What to re-measure

```powershell
node .tools\efficiency-report.mjs
```

- **Waiting share** — should fall below 20% once the stall fix is loaded.
- **Throughput** — baseline 22–34 turns/hour; sustained 35+ would confirm the
  fixes converted into speed.

## 6. Limits of this measurement

- **Cross-run merging.** Turn numbers repeat across runs, so a turn resumed by
  several runs has its calls merged. Turn 91 (117 calls, 45 minutes) is three runs'
  worth, not one turn's cost. Gaps longer than **900 seconds** are treated as run
  boundaries and excluded from the thinking/waiting split — a heuristic, not a
  fact.
- **Telemetry records completions.** A call's entry carries the completion time,
  so the wait it spent is measured as the gap *before* its entry.
- **Thinking time is not pure model time.** It includes MCP round trips and
  advisor waits that produce no telemetry.
- **Only 105 turns.** The tail is estimated from few samples, so treat the worst
  cases as indicative rather than typical.
