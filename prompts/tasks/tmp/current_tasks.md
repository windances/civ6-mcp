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
| `021-siege-legion-overseas.md` | 2026-09-27 | turn 270 | a siege legion overseas - form it, sail it, land on another civilization's continent, analyse the city found there, and assault only if it can be won; at most four new builds | a legion ashore on another landmass, a major civ's city read in its four numbers with the `tactics/07` verdict written, and then either that city is ours or the verdict is "cannot take it" |
| `022-take-haarlem.md` | 2026-09-28 | turn 288 | take Haarlem, the Dutch city the human named; the Dutch war is already on, so no declaration | **Haarlem is ours** - the tile at its own (x,y) reads `[CITY_CENTER]` owned by 中国 with one of our |

Task 020 was retired as `done/020-take-brussels-done-T237.md`: 布鲁塞尔 fell on T237 to
the Bombard and Field Cannon fire from (68,31), (69,31), (70,31), (71,30) and a Line Infantry attack
from (69,28), after a wall probe on T235 read `walls: 200/200` and the capture read
`city hp 200/200 -> 0, walls 200/200 -> 0` across T236-T237. The directory was empty from T216 (task
018 retired) to T220; those retirements and their measurements are in `done/` and
`docs/task-history.md`.

Task 019 was retired as `done/019-two-scouts-to-sea-expired-T250.md`.
