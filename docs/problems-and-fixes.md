# Problems, causes and fixes

A living log of what went wrong, why, and what closed it. It exists so a failure already paid for is
recognised in seconds instead of re-derived from a log, and so a new problem has an obvious home.

**How to add an entry - append, never renumber.** An id is a category prefix plus two digits:
`SL` session lifecycle, `DM` the division of labour and whose move, `RB` rollback / memory / state,
`EN` encoding and the document gates, `TL` tooling and data, `PT` working with the human. Put the new
entry at the end of its category and add its index row in the same commit. Every entry carries the
same four lines, and a line that cannot be filled in is a line that has not been measured yet:

- **symptom** - what was seen, with the string or number that was actually on screen.
- **cause** - the mechanism. A guess belongs in the diary, not here.
- **fix** - the commit that closed it, or the file and function that now hold the rule.
- **evidence** - the measurement, test or command that makes the claim checkable by somebody else.

## Index

| id | one line | status |
|---|---|---|
| SL-01 | The AI-turn stall was hidden by a ten-minute poll budget, then "recovered" by killing the game | closed |
| SL-02 | A running session had no input channel, so "stop" could not be delivered | closed |
| SL-03 | The handoff banner reported a turn the run had long passed | closed |
| SL-04 | A qualification run overwrote the live heartbeat with a stub | closed |
| DM-01 | Nothing said whose half of the turn was still open | closed |
| DM-02 | `UI.CanEndTurn()` was read as "the turn can end" | closed |
| DM-03 | The third state carried a caveat that made the session wait for a human who had finished | closed |
| DM-04 | A unit in neither work list disappeared from the report | closed |
| DM-05 | A unit under one movement point held the report on `YOUR MOVE` | closed |
| DM-06 | `skip_remaining_units` swept the human's units under the division | closed |
| DM-07 | `-HumanMilitary -DryRun -TaskFile <missing>` died with a raw PowerShell error | closed |
| RB-01 | A rollback of the game left the branch state inconsistent | closed |
| RB-02 | Two rollbacks to one turn overwrote the earlier branch's only save copies | closed |
| RB-03 | `.tools/archive-branch.py` could not be imported by path | closed |
| RB-04 | No way to play on from a loaded position with no memory of the branch before it | closed |
| RB-05 | Removing the achieved notes alone broke the check file's contract | closed |
| RB-06 | The first fresh-start backup flattened the tree and lost a diary segment | closed |
| RB-07 | The fresh-start test suite wiped the real match | closed |
| EN-01 | The agent's own editor strips the BOM a Chinese document needs | open by design |
| EN-02 | An English edit goes stale in its Chinese backup | open by design |
| EN-03 | AGENTS.md may cite at most four turns, and a new entry can push it over | open by design |
| EN-04 | A shared check file makes one match's retirement another match's silence | closed |
| TL-01 | `.tools/sleeping-units.py` crashed on a missing import | closed |
| TL-02 | `civ6-clean.ps1` ignored heartbeats under `runs/` | closed |
| TL-03 | `stop-agent.py` wrote its request into the wrong data directory | closed |
| TL-04 | `GameCore_Tuner/InGame states not found` usually means another client holds the tuner | open by design |
| TL-05 | A reload resets the whole turn | open by design |
| PT-01 | The division of labour was stated three times, each time narrower | closed |
| PT-02 | The human-done signal needed a definition, not a new marker | closed |
| PT-03 | Several 50/50 calls were the human's, and each one shaped a tool | closed |

## SL - session lifecycle

### SL-01 The AI-turn stall was hidden by a ten-minute poll budget, then "recovered" by killing the game

- **symptom** `end_turn` returned `HANG:354:0_MCP_0354|End turn requested (turn is still 354). AI turn
  processing appears stuck.` minutes after the game had visibly stopped, with nothing in it saying
  what to do; two such stalls in one evening (`22:13:34`, `22:56:21`).
- **cause** Two mechanisms stacked. The poll budget was about 593 s, so the report arrived long after
  the human's own two-minute rule had already been broken; and on `HANG` the MCP killed and relaunched
  the game up to three times before anybody was told, so the report that did arrive was usually the
  recovery's own message rather than the stall's. A reload also throws away the running turn's work.
- **fix** `AI_TURN_STALL_REPORT_S = 120.0` with `next_poll_delay()` trimming the loop to it; the
  `HANG` message now carries the wait, the two-minute rule and the way out; the kill/relaunch recovery
  is off by default behind `server.py::_hang_self_restart_enabled()` and
  `CIV_MCP_HANG_SELF_RESTART=1` restores it. Commit `2e836ba`.
- **evidence** `tests/test_end_turn_stall_budget.py` (22 tests). Live: the next stall reported at
  120 s; `hang_diagnosis.jsonl` also showed the `22:56:20` window was behind Chrome, which is why the
  re-focus retry was kept.

### SL-02 A running session had no input channel, so "stop" could not be delivered

- **symptom** No way to ask a session to stop: `dsh --help` offers only `web` and `plugin`, the
  headless profile is one-shot, and on Windows `Stop-Process -Force` is `TerminateProcess` with no
  usable SIGTERM.
- **cause** The session's only inbound channel is its tool results, and nothing wrote to it.
- **fix** `src/civ_mcp/stop_request.py` plus `_logged` appending a `STOP REQUESTED|` line to every
  successful tool result, with `delivered_at` / `delivered_turn` stamped into
  `stop-request.json`; `scripts/stop-agent.py` asks, reports, cancels, and `--wait N` falls back to
  `civ6-clean.ps1 -KeepGame`. Commit `fccfb6a`.
- **evidence** `tests/test_stop_request.py` (8 tests); live `--note` / `--status` / `--cancel` round
  trip, which also cleaned a request left over from `01:49`.

### SL-03 The handoff banner reported a turn the run had long passed

- **symptom** The session banner kept printing T288 while the game stood at T354, because
  `run.json`'s `last_turn` had frozen.
- **cause** `run_manifest.touch` moved the field only forward and nothing recorded a played turn on
  the ordinary path, so a stale value never corrected itself.
- **fix** `_record_played_turn()` in `src/civ_mcp/server.py`, called from `_logged` and on an
  `end_turn` advance; the stale value was corrected 288 to 354 by hand once.
- **evidence** `tests/test_run_manifest.py`; the handoff check now prints the turn the manifest and
  the game agree on.

### SL-04 A qualification run overwrote the live heartbeat with a stub

- **symptom** `scripts/qualify-mcp.py` left `heartbeat.json` reading a `starting` phase for a match
  that was being played, which reads exactly like a new session.
- **cause** The child MCP inherited `CIV_MCP_DATA_DIR=<cwd>/.civ6-mcp-data`, so it wrote its own
  state into the live run directory.
- **fix** The child gets a temporary data directory. `tests/test_qualify_mcp.py` pins it.
- **evidence** `tests/test_qualify_mcp.py`.

## DM - the division of labour and whose move

### DM-01 Nothing said whose half of the turn was still open

- **symptom** Under `-HumanMilitary` the session had to wait for the human, but the only signal was
  the `ENDTURN_BLOCKING_UNITS` entry, which is up at the start of nearly every turn and says nothing
  about ownership. A session either waited forever or called `end_turn` and swept the human's units.
- **cause** The split existed only in the task text; nothing derived it from the board.
- **fix** `src/civ_mcp/agent_half.py` (`is_the_humans`, `can_still_act`, `verdict`, `render`,
  `summary`), called from `get_notifications`: every call appends a `WHOSE MOVE|` line and writes
  `agent-half.txt` beside the heartbeat. Commit `4c0a7e4`, extended by `c9e67d0` (Great Admirals) and
  `fb17eaa` (Great Scientists and Great Merchants are the agent's).
- **evidence** `tests/test_agent_half.py`; the live `agent-half.txt` reports quoted in this log.

### DM-02 `UI.CanEndTurn()` was read as "the turn can end"

- **symptom** A wait built on `UI.CanEndTurn()` released immediately and handed back
  `_sweep_unmoved_units`'s silent fortify-and-skip.
- **cause** The boolean means "the End Turn button is pressable", and it is true *while* the units
  blocker is up - measured on turn 337, three consecutive reads of `CANEND|true` with
  `ENDTURN_BLOCKING_UNITS` raised.
- **fix** The documented test is the game's own notification entry; commits `c1a79fa` and `1a304f2`.
- **evidence** The turn 337 measurement, quoted in `AGENTS.md` and in the task text
  `scripts/resume-game.ps1` appends.

### DM-03 The third state carried a caveat that made the session wait for a human who had finished

- **symptom** The report said `ready to end` but the caveat "can end is not the same as the human
  having played" kept the session waiting, so the turn never ended.
- **cause** The caveat was written when the state was new and never reconciled with the human's
  definition of done.
- **fix** Commit `3fbd1d7`: `ready to end` **is** the human-done signal, and the caveat is gone. The
  wait is enforced before `end_turn`, not by refusing to call it.
- **evidence** `tests/test_agent_half.py` asserts the third state's text says the turn can end.

### DM-04 A unit in neither work list disappeared from the report

- **symptom** Builder `13107256` stood on an antiquity site at `(36,22)` with 2/2 moves, 2 charges and
  no order in the whole run, and no list or report named it - so nothing ever fixed it.
- **cause** `can_still_act` was false for it, so the whose-move split covered neither side, and it
  raised no units blocker. `get_builder_tasks` had also proposed `build UNKNOWN` on the tile, because
  an antiquity site is an Archaeologist's and not a builder's.
- **fix** `unclaimed()` names such units and the report lists them (commit `c58bde1`); the Lua
  builder-task query was fixed so an antiquity site no longer produces a bogus task. Commit
  `c58bde1`.
- **evidence** `tests/test_agent_half.py` (the measured builder as a fixture) and the
  `tests/test_builder_lua`-style check of the query.

### DM-05 A unit under one movement point held the report on `YOUR MOVE`

- **symptom** A `UNIT_MECHANIZED_INFANTRY` at `(20,32)` with `moves 0.2/4`, an empty activity and
  `ready_to_move` true kept the report answering `YOUR MOVE`, while the game's own units blocker had
  already dropped - so the session waited for a unit that could not enter a tile.
- **cause** `can_still_act` tested `moves_remaining > 0`, and a fraction of a point buys nothing.
- **fix** `MIN_MOVES_TO_ACT = 1.0` in `src/civ_mcp/agent_half.py`: below it a unit is judged as
  skipped, in both `can_still_act` and `unclaimed`. Exactly 1.0 still acts. Commit `c3afbbd`.
- **evidence** `tests/test_agent_half.py` (the boundary at 1.0 included) and
  `tests/test_wait_for_human.py`, whose live ten-unit reading now expects nobody listed.

### DM-06 `skip_remaining_units` swept the human's units under the division

- **symptom** A session that called it anyway (non-force, because nothing had a legal attack) got
  `FORTIFIED|1 fortified, 2 healing; SKIPPED|12`, and two of the twelve were the human's.
- **cause** The tool is empire-wide: it fortifies combat units and skips everything else. `SKILL.md`
  said to call it unconditionally before ending, and the division lives in a task file that the skill
  does not read.
- **fix** Commit `bda3293`: the carve-out in `.dsh/skills/civ6-orchestrator/SKILL.md` (+`.cn` backup),
  the `skip_remaining_units` row in `AGENTS.md`, and the ban stated in the task text
  `scripts/resume-game.ps1` appends.
- **evidence** The measured sweep result above; the carve-out is pinned by the switch contract test
  `tests/test_resume_game_division.py`.

### DM-07 `-HumanMilitary -DryRun -TaskFile <missing>` died with a raw PowerShell error

- **symptom** `Select-String : cannot find path '...does-not-exist.txt'` from inside
  `Add-DivisionOfLabour`, no task preview, exit 1.
- **cause** With `$ErrorActionPreference = 'Stop'` the non-terminating error from `Select-String`
  becomes terminating, and the preview path joins the path without checking it (the launch path
  refuses earlier, at `Resolve-Path`).
- **fix** Commit `9ca1c9a`: a guard before the marker check that refuses with
  `no task file to append the division to: <path> (check -TaskFile / -TaskPath)`, plus
  `tests/test_resume_game_division.py` (13 tests) pinning the switch on both paths.
- **evidence** The two runs, before and after, quoted in the commit message; the 13 tests.

## RB - rollback, memory and state

### RB-01 A rollback of the game left the branch state inconsistent

- **symptom** After loading an earlier save the session still carried the abandoned branch: diary rows
  from turns that no longer existed, temporary tasks retired by a `done when:` the rollback had just
  un-done, and `once: true` rules that had been achieved on the branch the human had just discarded.
  Measured 2026-09-28: the rollback to T218 left `024-take-brussels` retired while Brussels was a
  city-state again.
- **cause** A rollback is five jobs and only the game-loading one was being done.
- **fix** `scripts/rollback-to-turn.py`: archive the future, split the diary
  (`.tools/archive-branch.py`), roll the tasks back (`.tools/rollback-tasks.py`), restore the rules the
  branch retired and forget them in the persisted goal state, then restart the game the right way for
  the state it is in - plus `run_manifest.reset_turn`.
- **evidence** `tests/test_rollback_decisions.py`, `tests/test_handoff.py`; the archived rollback
  folders under `.civ6-mcp-data/branches/rollback-to-T*-*`.

### RB-02 Two rollbacks to one turn overwrote the earlier branch's only save copies

- **symptom** Measured 2026-09-25: a second rollback to T99 reused the folder written by the first and
  replaced the copies of the earlier branch's same-named saves, which were the only copies left.
- **cause** Reuse keyed on the target turn and the span of turns archived, and two different branches
  share both; the live autosaves had already been rewritten by the new branch.
- **fix** `_archive_can_absorb()` in `scripts/rollback-to-turn.py`: a candidate is reused only if every
  save it would receive matches in size and write time; otherwise a new timestamped folder is made and
  neither is touched. The manifest is merged rather than rebuilt.
- **evidence** `tests/test_rollback_decisions.py::TestTheArchiveIsNotClobbered` (5 tests).

### RB-03 `.tools/archive-branch.py` could not be imported by path

- **symptom** `python scripts/rollback-to-turn.py 352 --apply` and `--archive-only` died with
  `ModuleNotFoundError: No module named '_game'` before writing anything, while the plan printed
  normally.
- **cause** Loading a module by path does not put its directory on `sys.path`, and the file imports a
  sibling (`_game`) at import time.
- **fix** `load_archive_branch_module()` appends `.tools` to `sys.path` before `exec_module`. Commit
  `b57329f`.
- **evidence** `tests/test_rollback_decisions.py::test_the_archive_branch_module_loads_with_its_own_siblings`.

### RB-04 No way to play on from a loaded position with no memory of the branch before it

- **symptom** A rollback deliberately restores the past, which is right for a replay and wrong when
  the human wants the loaded position played on with none of the previous information.
- **cause** The only tooling was `rollback-to-turn.py`, whose whole design is to put the past back.
- **fix** `scripts/fresh-start.py <turn> [--apply] [--force]`: forget this match's diary (the run's
  copy and the legacy root copy), the achieved-goal state, and the run's session scratch; re-arm the
  achieved goals' rule bodies; reset the manifest's played-to turn; copy everything to
  `branches/fresh-start-<stamp>/files/` first; refuse while a session is playing. Commit `026381e`.
- **evidence** `tests/test_fresh_start.py` (18 tests) and the first real run, whose plan and result are
  in the commit message.

### RB-05 Removing the achieved notes alone broke the check file's contract

- **symptom** Stripping this match's two `achieved T99` notes without re-arming the rules turned seven
  tests red, including `test_every_retirement_trace_still_resolves_to_its_archived_block` and
  `test_the_china_wonder_obligation_is_live_or_recoverable`.
- **cause** The check file's contract is that a retired goal is either **live** or **traceable**; a
  trace is the only way back to the archived block, so deleting it strands the rule.
- **fix** `fresh-start.py::rearm_traces()` puts the block back from `prompts/checks/archive/` and drops
  the note - the same operation as `turn_checks.restore_achieved`, applied to this match's own
  retirements. The "traces must not be empty" guard became a `pytest.skip`, because an empty list is a
  correct state after a fresh start. Commits `fcf22b0`, `22b1cd6`.
- **evidence** `tests/test_fresh_start.py`, `tests/test_turn_checks.py` (the skip), and the seven-test
  failure before the change.

### RB-06 The first fresh-start backup flattened the tree and lost a diary segment

- **symptom** The backup held one `diary_china_-1894041591.jsonl` where the tree had two - the run's
  copy (turns 1..287) and the legacy root copy (289..354) - so the second overwrote the first.
- **cause** The copy target was `files/<basename>`, and the two sources share a file name.
- **fix** The backup mirrors the source path (`files/.civ6-mcp-data/runs/<run>/diary_...jsonl` versus
  `files/.civ6-mcp-data/diary_...jsonl`), and a test asserts both exist and differ. Commit `026381e`
  (fix landed with the tool's first review).
- **evidence** `tests/test_fresh_start.py::test_everything_forgotten_is_in_the_backup_first`; the older
  copies under `branches/abandoned-*/backup-*/` still hold the segment.

### RB-07 The fresh-start test suite wiped the real match

- **symptom** Three test runs at `00:13:35`, `00:13:53` and `00:14:03` deleted the real match's diary
  and achieved state instead of a temporary copy's.
- **cause** The tests called `main()` with no argument, and `main()` used the module-level checkout
  root - so the "fake checkout" fixture was ignored for the paths that mattered.
- **fix** `main(root=None)` takes its root, tests pass the fixture, and a test asserts the default and
  that the fixture is not the checkout. Everything the accident removed was in
  `branches/fresh-start-20261005-001335/files/`. Commit `026381e`.
- **evidence** `tests/test_fresh_start.py::test_main_defaults_to_the_checkout_root_and_is_never_given_it_by_accident`.

## EN - encoding and the document gates

### EN-01 The agent's own editor strips the BOM a Chinese document needs

- **symptom** After editing a `.zh.` file, `SETUP-WINDOWS.md`, a tactics file or a task file, the
  document opens as mojibake in a GBK viewer; `fix-text-encoding.py --check` fails.
- **cause** The agent's `write`/`edit` tools emit plain UTF-8 and silently drop the BOM. A zh-CN
  editor that cannot see a BOM decodes the file as codepage 936.
- **fix** Run `python scripts/fix-text-encoding.py` after every such edit; the gate is also
  `tests/test_text_encoding.py` and the pre-commit hook.
- **evidence** The gate's own output: `N BOM(s) restored` and `0 document(s) would show as mojibake in
  a GBK viewer`.

### EN-02 An English edit goes stale in its Chinese backup

- **symptom** `tests/test_dsh_documents.py` fails with `does not carry these spans of <name>, so it was
  translated from an older revision`, or with a heading-count mismatch.
- **cause** Every document handed to the model has a `<name>.cn.md` backup beside it, and the backup is
  checked for every inline code span and every heading of the English file.
- **fix** Mirror the new spans and headings by hand in the same commit; never edit the backup as a
  source. Measured twice in this log's own span (`game-recovery.md`, `military-strategy-coverage.md`).
- **evidence** `python -m pytest tests/test_dsh_documents.py`.

### EN-03 AGENTS.md may cite at most four turns, and a new entry can push it over

- **symptom** `AGENTS.md cites 6 turns (limit 4): lines [...]` after two entries were added.
- **cause** A turn number is a fact only this match can use; the reference is meant to stay
  game-agnostic, so the count is capped.
- **fix** Cite the measurement without the turn ("measured on this match") or move the story to a
  retrospective. The cap is in `tests/test_agents_is_game_agnostic.py`.
- **evidence** `python -m pytest tests/test_agents_is_game_agnostic.py`.

### EN-04 A shared check file makes one match's retirement another match's silence

- **symptom** Measured: the A3-A7 experiment replayed a T1 branch of the same save for about 340 turns
  with `dynasty-cycle-wonder` absent from the loop, and all eight sessions built zero wonders.
- **cause** `prompts/checks/turn-checks.md` is one file shared by every match played from this
  checkout, and a `once: true` goal is pruned the turn it is achieved - so one match's achievement
  removed the rule for another.
- **fix** The retirement trace names the match that wrote it, and
  `turn_checks.restore_foreign_games` re-arms another match's goal on load; an un-keyed trace is left
  alone rather than guessed at. A trace keyed to this match stays retired.
- **evidence** `tests/test_turn_checks.py::TestAGoalAnotherMatchAchievedComesBack`.

## TL - tooling and data

### TL-01 `.tools/sleeping-units.py` crashed on a missing import

- **symptom** `NameError: name 'asyncio' is not defined`.
- **cause** The module used `asyncio.run` without importing it.
- **fix** `import asyncio` added.
- **evidence** The tool runs against a live game and lists every unit grouped by activity.

### TL-02 `civ6-clean.ps1` ignored heartbeats under `runs/`

- **symptom** It reported `heartbeat none (already clean)` while a live run heartbeat existed, so a
  session could be left running while the cleaner said the tree was clean.
- **cause** The state list collected only the root heartbeat, which is the pre-runs location.
- **fix** The list collects `runs/**/heartbeat.json` regardless of the root file, and the settled
  check uses what is still present. Commit `4fbc64c`.
- **evidence** `scripts/civ6-clean.ps1 -DryRun` against a run with a stale heartbeat.

### TL-03 `stop-agent.py` wrote its request into the wrong data directory

- **symptom** The first run wrote `stop-request.json` into `~/.civ6-mcp-data` instead of the run
  directory, where no session would ever read it.
- **cause** `stop_request`'s default resolves `CIV_MCP_DATA_DIR`, and a plain shell has none.
- **fix** The CLI passes the run directory explicitly (`run_dir()`), the same rule
  `scripts/rollback-to-turn.py` and `scripts/run.py` were fixed for.
- **evidence** `tests/test_stop_request.py`; a live `--status` that names the run directory.

### TL-04 `GameCore_Tuner/InGame states not found` usually means another client holds the tuner

- **symptom** Every tool call answers `ConnectionError: GameCore_Tuner/InGame states not found`, which
  reads like a broken game.
- **cause** FireTuner serves exactly one client, and a playing session's MCP holds that connection for
  the whole session. A second client connects and then dies.
- **fix** Read files, not the tuner, while a session plays; ask the session for facts; use
  `.tools/whats-on-screen.py`, `stop-agent.py --status`, the heartbeat and the log, none of which need
  the tuner.
- **evidence** Measured with a connection held open, idle and busy - recorded in
  `docs/game-recovery.md`.

### TL-05 A reload resets the whole turn

- **symptom** After the game was restarted and a save loaded, every action of the interrupted turn was
  gone (Korolev's activation, a city's launch project, a builder's orders).
- **cause** That is what loading a save does: the turn's work is not part of the save.
- **fix** Treat a restart as the human's decision, and stop the session first
  (`scripts/stop-agent.py --wait`); the MCP no longer restarts the game on a stall by itself.
- **evidence** The T354 reload, and `2e836ba`.

## PT - working with the human

### PT-01 The division of labour was stated three times, each time narrower

- **symptom** A first version named only "military units"; the human then had to point out that the
  Great Admirals were theirs too, and later that the Great Scientists and Great Merchants were the
  agent's.
- **cause** The division was inferred from the phrase "military" instead of being written down as the
  two named lists.
- **fix** The task text names both classes explicitly (`is_the_humans` matches combat strength above
  zero, or a GENERAL/ADMIRAL unit type), and the "everything else" list names builders, settlers,
  traders, the Great Scientists and the Great Merchants. Commits `c9e67d0`, `fb17eaa`.
- **evidence** `tests/test_agent_half.py` and `tests/test_wait_for_human.py` (a commander is the
  human's despite zero combat strength; a Great Scientist is not).

### PT-02 The human-done signal needed a definition, not a new marker

- **symptom** The agent kept waiting for a signal the human was never going to send.
- **cause** "The human is done" had been treated as something the human reports, and it is something
  the board shows.
- **fix** The human's decision: no separate marker - if the game is in the end-turn state, the human is
  done. That became the third state of the whose-move report. Commit `3fbd1d7`.
- **evidence** The state's own text, asserted in `tests/test_agent_half.py`.

### PT-03 Several 50/50 calls were the human's, and each one shaped a tool

- **symptom** Each of these stalled the work until it was asked: report early or self-restart; who
  restarts the game; how a session is stopped; what "fresh start" clears.
- **cause** They are policy, not engineering: they decide what the human sees and what is allowed to
  happen to their game.
- **fix** Ask, then encode the answer where it is enforced - `2e836ba` (report at 120 s rather than
  self-restart), `fccfb6a` (a stop request file rather than a kill), `026381e` (fresh start scope:
  this match only; notes re-armed, rule bodies kept).
- **evidence** The commit messages quote the instruction each one implements.

## Rules of thumb

1. **A test that writes real state will eventually destroy real state.** Twice in one day: a
   qualification run overwrote the live heartbeat, and a test suite wiped the match's memory. Both are
   fixed by injecting the root or a temp directory, and both now have a test that pins the injection.
2. **Never let a report contradict the engine.** `UI.CanEndTurn()` and a 0.2-movement unit both taught
   this: when the game says one thing and the report says another, the session waits forever. Measure
   the engine's own signal and report that.
3. **A switch needs a contract test.** `-HumanMilitary` is PowerShell, so pytest cannot run it; what can
   be pinned is the text it appends, the paths it appends on, and the guards around it. That found a
   real defect on the first run.
4. **Removing a record is not the same as removing an instruction.** The achieved notes had to be
   replaced by the rule bodies they stood for; the temporary tasks were printed rather than withdrawn.
5. **Back up before forgetting, and mirror the tree when you do.** A flattened backup silently keeps
   one file of two.
6. **Put the rule where it is read.** The division lives in a task file; the rule that enforced it had
   to be written into `AGENTS.md`, `SKILL.md` and the task text together, because none of them is read
   by the others.

## Sources

- `docs/game-recovery.md` - the recovery authority: stalls, loads, the leader-intro window, the save
  list.
- `docs/military-strategy-coverage.md` - the enforcement ladder, and which strategies have teeth.
- `AGENTS.md` - what a session is told, and what it must not do under the division.
- `scripts/README.md` - the operator's view of every script, including `resume-game.ps1
  -HumanMilitary`.
- The gate bar every entry above was landed through: `python scripts/fix-text-encoding.py --check`,
  `python -m pytest -q`, `node --test test/dsh/*.test.mjs`, `npm run qualify`,
  `python scripts/qualify-mcp.py`, `python .tools/audit-md-language.py`,
  `python .tools/check-directive-sync.py`.
