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
| `019-two-scouts-to-sea.md` | 2026-09-27 | turn 250 | two Scouts to sea, to find the civilizations nobody has met (T220: 32% of the map explored, four living majors `not met`; at T229 the instrument is two Rangers, due ~T238) | two units of the Scout line are alive, each on a water tile, and >= 1 newly met major civilization |

The directory was empty from T216 (task 018 retired) to T220; that retirement and its measurements are
in `done/` and `docs/task-history.md`.
