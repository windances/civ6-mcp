# scripts

The command-line tools. Everything here runs from the repository root, and `python` below means the
project virtualenv - `.venv\Scripts\python.exe` on Windows, `.venv/bin/python` elsewhere.

Most of these talk to a live Civilization VI over FireTuner (the "route A" drivers, used when no MCP
session owns the connection). The ones that do not are marked **offline**.

## Where the data lives

Sessions read one playthrough at a time. The data root holds one directory per run and a `current`
pointer; **every script resolves `current` for you**, so no command takes a run argument.

```
.civ6-mcp-data/
  current                     -> china-911679432-a
  runs/
    china-911679432-a/        run.json, diary, retired-goal state, heartbeat, saves/
  branches/                   rollback archives (shared by every run)
  loc-en-names.json           localization table (shared by every run)
```

Every session start prints a `SESSION` line and a `RUN` line naming the playthrough, and compares
the run's expected `(civ, seed)` against the loaded game. A mismatch prints `RUN MISMATCH`, and
`play-turn.py end` refuses to advance the turn unless `--force`. A directory with no `run.json` is
not checked at all, so an un-named setup behaves exactly as it always did.

## Playthroughs

```powershell
python scripts\run.py status                     # what this directory names vs what the game says
python scripts\run.py init --id china-a --label "China conquest A" --from-game
python scripts\run.py touch --turn 116           # record progress (play-turn.py end does this too)
python scripts\run.py clear
#   init flags: --civ --seed --notes --from-game --replace

python scripts\runs.py inventory                 # what is in the data root, grouped by playthrough
python scripts\runs.py plan                      # what a migration would move (no writes)
python scripts\runs.py apply --current china-911679432-a
python scripts\runs.py verify                    # assert the runs do not overlap
```

`--from-game` takes the identity from the loaded game rather than the command line, so a manifest
cannot be written against the wrong save.

## Playing a turn

```powershell
python scripts\orient.py                                  # full orientation; SESSION and RUN lines first
python scripts\orient.py --only diplomacy,units
python scripts\orient.py --full --only governors
python scripts\orient.py --maps --radius 2

python scripts\play-turn.py <verb> ...
```

`play-turn.py` verbs:

| Verb | What it does |
|---|---|
| `units` | every unit with index, type, tile and moves |
| `move <unit> <x> <y>` | order a move, then print where the unit actually ended up |
| `march <TYPE:X,Y> ...` | one unit per order, screen first, siege last |
| `attack <unit> <x> <y>` | attack a tile; a city tile resolves as the city |
| `diplo` / `respond <pid> POSITIVE\|NEGATIVE` | list and answer open diplomacy sessions |
| `dismiss` | clear the popup layer (disaster, invite, tech-completed screens) |
| `scan <x> <y> [radius]` | enemy cities in reach plus the narrated map |
| `civic <CIVIC>` | start a civic |
| `produce <city> <ITEM> [X,Y]` | set production; the category is resolved for you |
| `purchase <city> [ITEM]` | buy with gold, or `--faith`; no ITEM lists what is affordable |
| `improve <unit> <IMPROVEMENT>` | builder or military engineer work |
| `order <unit\|all> <fortify\|heal\|alert\|sleep\|skip\|auto>` | unit orders |
| `governor`, `dedication`, `research`, `pantheon` | the other end-of-turn blockers |
| `clear`, `posture` | policy slots; siege formation report |
| `end [--force]` | end the turn, with the unused-attack and formation guards |

A city may be given by `city_id` (as the tools print it, e.g. `65536`) or by name.

```powershell
python scripts\target-report.py 53 14 [--reinforcements] [--radius N]
python scripts\staging-plan.py 58 39 [--next] [--turns N] [--kill]
python scripts\probe-tile.py 58,30 57,27
```

- `target-report.py` - the pre-war gates for a city or camp in one call: the tile and city (walls,
  pool, garrison, defence), visible enemies within three tiles, and the staging plan with per-tile
  `FIRE` / `NO LINE OF SIGHT`. `--reinforcements` adds which turn each queued unit reaches the rally.
- `staging-plan.py` - the staging table alone. `--next` continues to the next objective.
- `probe-tile.py` - raw `TileInfo` for one or more tiles.

## Recording the diary

`play-turn.py end` does **not** append a diary row; this does. It is a missed step, not a missing
capability, and the `SESSION` line's `NOTE` names it when the diary falls behind.

```powershell
python scripts\record-turn.py --reflections t99.json     # the five contract fields, all non-empty
python scripts\record-turn.py --show
python scripts\record-turn.py --retro
```

## Rollback

```powershell
python scripts\rollback-to-turn.py 59                  # plan only
python scripts\rollback-to-turn.py 59 --apply          # archive the future, restore the past
python scripts\rollback-to-turn.py 59 --archive-only
python scripts\rollback-to-turn.py 59 --force
#   also: --save <name> --no-checks --no-diary --no-tasks

python scripts\turn-of-save.py --list                  # which turn each save holds
python scripts\turn-of-save.py "<path>.Civ6Save"       # one save, without loading it
```

A rollback is five jobs: archive the autosaves after the target, split the diary at the boundary,
bring back temporary tasks retired after it, restore the `once: true` rules it retired **and** forget
them in the persisted goal state, then restart the game the right way for the state it is in. It also
moves the run's recorded progress back to the target turn.

## Handing a match to a fresh session

```powershell
scripts\resume-game.ps1 [-DryRun] [-Wait] [-Rollback]
#   also: -TaskFile <f> -TaskPath <f> -Turns N -TimeoutSeconds N -PollSeconds N

python scripts\handoff.py [--json] [--task <path>]
scripts\civ6-clean.ps1 [-DryRun] [-KeepGame] [-Force] [-PID N] [-TunerPort N] [-WebGuiPort N]
scripts\run-dsh-headless.ps1 -TaskFile <f> [-Task <t>] [-DryRun]
```

`civ6-clean.ps1` counts a stale heartbeat under `runs/` as "not settled", not just the root one.

## Tasks and document gates

```powershell
python scripts\temp-task.py status
python scripts\temp-task.py add --title "..." --instruction "..." --expires-turn N
python scripts\temp-task.py retire 020 --done --turn 237 --note "..."

python scripts\fix-text-encoding.py [--check]     # the mandatory BOM / mojibake gate
python scripts\repair-text.py [--apply] [--verbose]
python scripts\install-hooks.py [--revert]
```

## Localization

The table is built once per machine from the game's own text files and read by every run. It keeps
tool output English whichever language the game is set to, resolving a name from the type code beside
it or from a tag-space-specific reverse map; a name it cannot resolve is left exactly as the game
returned it. A missing table is not an error.

```powershell
python scripts\build-loc-names.py            # build or refresh
python scripts\build-loc-names.py --check    # report only
#   also: --game <install path> --out <path>
```

## Strategy and advisor briefs

```powershell
scripts\use-strategy.ps1 -Name <preset> [-List] [-IgnoreDirective]
scripts\set-strategy.ps1 -File <f> | -Text | -Show

python scripts\advisor-brief.py --role military-map --tactics 04,05,06
#   also: --preset <f> --snapshot <f> --signals <f> --out <f> --check
```

## Qualification, diagnosis and analysis

```powershell
python scripts\qualify-mcp.py                  # keyless MCP launch and tool discovery
node scripts\qualify-static.mjs                # static checks over the shipped artifacts

python scripts\test_connection.py [host] [port]
python scripts\test_game_state.py [--map <x> <y>] [--radius N] [--map-only]
python scripts\test_queries.py

python scripts\experiment-report.py --game china_911679432 [--step N] [--json] [--verdict] [--compare]
```

## Launchers, saves and batch tooling

```powershell
python scripts\launch_save.py [AutoSave_0221] [--kill-first] [--no-launch]
python scripts\install_saves.py [--force] [--dry-run]
python scripts\menu_audit.py [--save <name>] [--skip-launch]
python scripts\parse_save.py <save> [-o out.jsonl] [--csv] [--player N] [--raw]

python scripts\orchestrator.py launch|resume|preflight|logs|kill-all|abandon [...]
python scripts\convex_sync.py --prod [--upload <dir>] [--cloud <url>] [--watch]
python scripts\analyze.py <subcommand> [--game-id ...] [--model ...] [...]
```

## Every file in this directory

| Script | Kind | Purpose |
|---|---|---|
| `advisor-brief.py` | offline | assemble an advisor's brief from the doctrine and a snapshot |
| `analyze.py` | offline | CivBench analysis CLI: tool-calling patterns, strategy, evaluation |
| `auto-turns.py` | live | play routine development turns unattended |
| `bootstrap.ps1` / `bootstrap.sh` | offline | one-time environment setup |
| `build-loc-names.py` | offline | build the localization table from the game install |
| `civ6-clean.ps1` | offline | stop the game, the tuner listener and stale heartbeats |
| `civbench_data.py` | offline | data access library for notebooks and collaborators |
| `convex_sync.py` | offline | sync JSONL telemetry to Convex |
| `dump-dsh-config.sh` | offline | print the DSH overlay configuration |
| `experiment-report.py` | offline | one experiment's numbers, read from the raw record |
| `extract_tool_docs.py` | offline | extract MCP tool metadata for the docs site |
| `fix-text-encoding.py` | offline | the mandatory BOM / mojibake gate |
| `generate_sas_token.py` | offline | read-only SAS token for collaborator data access |
| `handoff.py` | offline | can a fresh session take this match over, and from which save |
| `install-hooks.py` | offline | install or revert the repository's git hooks |
| `install_saves.py` | offline | install eval saves into the Civ 6 save directory |
| `launch_save.py` | offline | launch Civ 6 and load a save by OCR-guided menu navigation |
| `menu_audit.py` | live | screenshot and OCR each menu stage |
| `orchestrator.py` | offline | dispatch, monitor and manage benchmark runs |
| `orient.py` | live | one full re-orientation read |
| `parse_save.py` | offline | per-player, per-turn timelines out of a `.Civ6Save` |
| `play-turn.py` | live | issue one order or read one scan, without an MCP session |
| `probe-tile.py` | live | raw `TileInfo` for named tiles |
| `publish_hf_dataset.py` | offline | publish the benchmark to Hugging Face Datasets |
| `qualify-mcp.py` | offline | keyless MCP launch and tool discovery |
| `qualify-static.mjs` | offline | static qualification of the shipped artifacts |
| `record-turn.py` | live | append this turn's diary rows from a direct session |
| `repair-text.py` | offline | repair text a PowerShell round trip damaged |
| `resume-game.ps1` | offline | check and hand a paused match to a fresh session |
| `rollback-to-turn.py` | offline | roll the game back to a chosen turn |
| `run-dsh-headless.ps1` / `.sh` | offline | run one DSH session headless |
| `run-dsh-web.ps1` / `.sh` | offline | start the DSH web GUI |
| `run.py` | live | name this playthrough and assert the loaded game matches it |
| `runs.py` | offline | organise and verify the per-playthrough data directories |
| `scrape_wiki_images.py` | offline | leader portraits and civilization symbols |
| `set-strategy.ps1` / `.sh` / `.cmd` | offline | write the directive text into the skill |
| `split_game_log.py` | offline | one-off: split `game_log.jsonl` per session |
| `staging-plan.py` | live | the staging table for a target |
| `target-report.py` | live | the pre-war gates for a city or camp |
| `temp-task.py` / `.sh` / `.cmd` | offline | add, retire and inspect temporary tasks |
| `test_connection.py` | live | smoke test the FireTuner connection |
| `test_game_state.py` | live | exercise every `GameState` reader |
| `test_queries.py` | live | exercise every Lua query builder and parser |
| `turn-of-save.py` | offline | the turn a save holds, without loading it |
| `use-strategy.ps1` / `.sh` / `.cmd` | offline | load a strategy preset into the skill |
