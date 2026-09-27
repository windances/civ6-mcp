# Strategy presets

Advisor prompt presets for the civ6-orchestrator. Each preset is a complete set
of the four worker prompts; applying one copies it over `prompts/workers/`, which
is the directory the `civ_advisor` route actually reads.

## Switching

```powershell
scripts\use-strategy.ps1              # list presets and show which is active
scripts\use-strategy.ps1 science      # apply
scripts\use-strategy.ps1 balanced     # restore the upstream default
```

```bash
bash scripts/use-strategy.sh science
```

The scripts run the static qualification gate after every change, so a preset
that would break `npm run qualify` is rejected rather than silently applied.
"Active" is determined by comparing file hashes, not by a marker file, so a
hand-edited `prompts/workers/` correctly reports as matching no preset.

**Both destinations are compared, not just `prompts/workers/`.** A preset that
arrived in one of them is not active, it is stale: measured 2026-09-27,
`prompts/workers/` matched `china-conquest` while the `SKILL.md` block was 38 lines
behind it, and the switcher still called it active. `-List` now names that state and
prints the command that resynchronises it, and `tests/test_strategy_block.py` fails
on it.

**A one-off change does not need a preset:** `scripts\set-strategy.ps1 -Text "..."`
(`-File <path>`, `-Show`; `scripts/set-strategy.sh` from Git Bash) writes the block with
the text you give it and puts an `ad-hoc` line first, so a deliberate override is not
mistaken for a preset that drifted. Re-applying a preset rewrites the whole block and
removes that line.

## How a preset is actually applied

Two destinations, and only one of them is read by the running agent:

| File | Read by | Effect |
|---|---|---|
| `<preset>/directive.md` | injected into `.dsh/skills/civ6-orchestrator/SKILL.md` | **the strategy that actually reaches the agent** — loaded at session start |
| `<preset>/<role>.md` ×4 | `prompts/workers/` | currently **inert**: the agent does not read these files |

> **Verified 2026-09-19.** A running session was searched for the word
> `immutable`, which every worker prompt contains and `SKILL.md` does not: **zero
> hits across 4,000+ session lines.** The same session shows the agent inventing
> its own advisor roles (`"You are an empire-development advisor"`,
> `"You are a military/defense advisor"`) instead of the four role files, so the
> role prompts had no influence at all. The skill *was* read — the agent's own
> advisor prompts echo its wording ("NO tools … return JSON only").
>
> The four role files are kept because the static gate checks them, and they cost
> nothing. Put anything you want to actually happen in `directive.md`.

Applying a preset rewrites the `DIRECTIVE:BEGIN`/`DIRECTIVE:END` block inside
`SKILL.md`.

**A switch takes effect on the next turn, not the next session.** The skill is only
read when the agent loads it, so on its own a rewritten block would not reach a
running session. `src/civ_mcp/strategy_directive.py` closes that gap: `end_turn`
appends the current directive to its result whenever the block has changed, and the
agent reads that result every turn. A steady directive costs nothing — the module
reports only on change (and once per process, which covers a session that started
from a stale skill load).

So mid-game changes are live:

```powershell
scripts\use-strategy.ps1 domination   # the agent sees this on the next end_turn
```

## Available presets

| Preset | Victory path | Emphasis |
|---|---|---|
| `balanced` | none — upstream default | No bias. The pristine four prompts. |
| `china-conquest` | Domination | Qin (Unifier): Dynastic Cycle eurekas and wonders, Crouching Tiger paired with melee, Three-Six Stratagems for the human, one siege at a time, no peace ever. **The preset the current match plays.** |
| `expansion` | none yet — wide opening | Four to six cities and universal growth before committing to a victory type; **trade routes may never sit idle**; every form of idle capacity surfaced each turn |
| `science` | Science | Campus adjacency, tall 4–6 cities, Research Alliances, watch rival Spaceports |
| `domination` | Domination | One front at a time, siege against walls, strategic resources, war weariness |
| `religion` | Religious | Great Prophet deadline, Holy Sites everywhere, theological combat, conversion count |

Each preset briefs all four advisors, not just `strategy`, because the roles have
fixed responsibilities: the `military-map` advisor in a science game should
propose only defensive and escort actions, while in a domination game it is the
primary planner.

## How a preset stays compatible

The advisor roster is **fixed at four roles** by
`contracts/worker-proposal.schema.json`, whose `worker` field is an `enum` of
`strategy`, `military-map`, `economy-cities`, `diplomacy-victory`. The static gate
in `scripts/qualify-static.mjs` enforces that enum, requires all four prompt files
to exist, and requires each to contain the phrases `immutable` and
`Do not request tools` and to exceed 100 bytes.

You therefore cannot add a fifth advisor (a dedicated "religion advisor", say)
without changing the schema and the gate. Express a different strategy by
reweighting the four existing roles — including through the `priority` integer
(0–100) that each proposal carries — not by adding roles.

## Adding your own preset

```powershell
mkdir prompts\strategies\my-strategy
copy prompts\workers\*.md prompts\strategies\my-strategy\
# edit the four files, then:
scripts\use-strategy.ps1 my-strategy
```

Keep the two mandatory phrases in each file. `prompts/strategies/balanced` is the
authoritative copy of the upstream prompts — use it as your starting point, and to
recover if an edit goes wrong.

## Scope

These presets only affect how the four advisors reason and what they propose.
They do not change the safety model: the advisors still have an empty tool
allowlist and cannot touch the game, `run_lua` remains removed, and the parent
orchestrator remains the sole writer. Conflict resolution order still lives in
`.dsh/skills/civ6-orchestrator/SKILL.md`.
