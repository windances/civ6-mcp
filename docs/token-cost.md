# What the Civ 6 agent costs in tokens (measured, 2026-09-28)

Every model call DSH makes is written to its session log as an `assistant/chunk` whose chunk type is
`usage`, so `.dsh-home/sessions/**/session.jsonl.zstd` is a **complete ledger**, not a sample. The
reader is the local tool `.tools/token-stats.mjs` (untracked, like its siblings `advisor-usage.mjs`
and `china-usage.mjs`; `.tools/` is ignored by design):

```
node .tools/token-stats.mjs                 # totals, roles, models, top sessions
node .tools/token-stats.mjs --tools         # + tool-call histogram and result sizes
node .tools/token-stats.mjs --per-turn      # + tokens per game turn, session by session
node .tools/token-stats.mjs --json          # machine-readable
```

## The record, exactly

| field | meaning |
|---|---|
| `inputTokens` | the **uncached** part of the prompt |
| `cacheReadTokens` | the part of the prompt served from cache |
| `outputTokens` | generated tokens, `reasoningTokens` a subset |
| `totalTokens` | `input + cacheRead + output` (verified against a sample: 11226 + 21120 + 58 = 32404) |

So **prompt tokens = input + cacheRead**, and the money-relevant split is fresh vs cached; this file
counts tokens, not currency, because pricing is a provider setting.

A game turn is counted from `end_turn`'s own result, which opens `Turn 60 -> 61`. Everything spent
since the previous one is that turn's work; an `end_turn` that came back **blocked** advances nothing
and gets no bucket.

## Snapshot at T271 of the China match

114 session files, 95 with usage records, 4,259 model calls, all on `deepseek-official /
deepseek-v4-flash`.

| | tokens |
|---|---|
| prompt total | **911.4M** (fresh **6.07M** + cache-read **905.4M**) |
| output total | **7.01M** (reasoning **5.42M**, i.e. 77%) |
| total as the harness counts it | **918.5M** |
| never-cached (fresh input + output) | **13.08M** |
| cache-read share of prompt | **99.3%** |

Per game turn, averaged over the match: **8.3 model calls**, 18.2 tool calls, **1.78M total tokens**,
11.8k fresh input, 13.6k output (10.5k of it reasoning), ~22k characters of tool results.

| role | sessions | calls | total | fresh in | output | game turns |
|---|---|---|---|---|---|---|
| game-driving sessions | 39 | 3,943 | 898.9M | 5.21M | 5.67M | 515 |
| tooling / authoring sessions | 13 | 273 | 18.1M | 448.5k | 335.8k | 0 |
| advisor subagents | 43 | 43 | 1.44M | 412.1k | 1.00M | 0 |

The advisor layer is **0.16%** of the bill: 43 sessions, one model call each, because the workers are
one-shot JSON proposals over an immutable snapshot and have no tools.

## Cost per turn grows with the game, and the prompt is why

511 turns attributed across the whole match (a turn replayed in an abandoned branch counts again -
the logs are work paid for, not unique turns):

| band | turns | total/turn | prompt/turn | output/turn | reasoning/turn | calls/turn |
|---|---|---|---|---|---|---|
| T1-T30 | 28 | 562.9k | 556.3k | 6.6k | 5.3k | 6.0 |
| T31-T60 | 41 | 573.2k | 563.3k | 10.0k | 8.1k | 6.0 |
| T61-T90 | 130 | 1.19M | 1.18M | 10.1k | 8.1k | 6.6 |
| T91-T120 | 116 | 1.42M | 1.42M | 6.6k | 4.6k | 5.3 |
| T121-T150 | 62 | 1.95M | 1.94M | 8.8k | 6.1k | 6.2 |
| T151-T180 | 54 | 2.42M | 2.40M | 18.0k | 13.8k | 10.8 |
| T181-T210 | 19 | 2.32M | 2.30M | 16.8k | 12.9k | 10.4 |
| T211-T240 | 30 | 2.41M | 2.40M | 11.6k | 8.6k | 8.9 |
| T241-T270 | 30 | 2.35M | 2.34M | 8.4k | 5.3k | 6.9 |

**A turn costs 4.3x what it did in the opening thirty turns**, and the growth is entirely in the
prompt: output per turn stays between 6.6k and 18k. Each model call carries ~214k tokens of context
(99% cache-read), and a turn is 6-11 such calls, so the bill is *context x steps*.

Two consequences, both actionable:

- **Tool output is not the driver.** All tool results together are ~22k characters per turn, roughly
  5.5k tokens - about 0.3% of that turn's prompt. Trimming `get_cities` would not move the number.
- **Steps per turn is the multiplier**, and so is the size of what stays resident between steps. The
  levers are fewer model calls per turn (batch orders, avoid the re-read after a refusal), a smaller
  resident context (this reference is 42 KB and is re-sent every call), and `reasoningEffort`, since
  reasoning is 77% of all generated tokens.

## Caveats, so the numbers are not over-read

- **Cache reads are not free but are not full price either.** 905M of the 918M is cache-read prompt;
  a provider's cache-hit rate is what turns that into money.
- **Replays count.** The abandoned branches re-played T61-T120 (130 and 116 turns in two bands), so
  those bands are "turns played", not "turns of the final timeline".
- **85 `end_turn` calls advanced nothing** (599 calls, 515 attributed turns): blocked turns still cost
  the calls that discovered the block.
- Session-title generation and web-search sub-requests are separate event types; they are not counted
  as their own rows (about 2% of calls, and they run on the same model).
- The tool prints a full method summary with the code, and its numbers move as the live match is
  played - re-run it rather than quoting this file's snapshot.
