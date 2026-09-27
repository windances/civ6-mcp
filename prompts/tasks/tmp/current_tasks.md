# 当前有效的临时任务 — the live register

This file is the **register**, not an instruction and not a task: it says which temporary tasks are in
force right now, when each one stops, and in one line why it exists. The tasks themselves are the files
next to it, `AGENTS.md` holds the procedure for them, and `docs/task-history.md` holds what the retired
ones measured.

- It is **not** a task file: it carries none of the five header lines (`added:`, `expires:`,
  `done when:`, `overrides:`, `scope:`), it is never moved to `done/`, and `tests/test_temp_tasks.py`
  skips it exactly as it skips `README.md`.
- It is maintained **in the same commit that adds or retires a task**, and the test checks it against
  the directory (`prompts/tasks/tmp/*.md` minus `README.md` and this file), so a retirement that is not
  recorded goes red.
- **The task file is the authority.** The `expires:` column is copied from it and the last column is the
  first line of its `done when:`; when this table disagrees with a file, the file wins and the table is
  stale.
- Only **temporary tasks** are listed. Wars, upgrades, city builds and other standing decisions are the
  strategy directive's business, not this file's.

| task file | added | expires | why it exists, in one line | done when (first line) |
|---|---|---|---|---|
| `018-take-alexandria.md` | 2026-09-27 | turn 235 | 占领亚历山大，先进行侦察，进行战前分析，攻城集结后攻城 — the capital Domination needs, never yet seen, so the search is the first phase | Alexandria is ours (its (x,y) read at capture) |
