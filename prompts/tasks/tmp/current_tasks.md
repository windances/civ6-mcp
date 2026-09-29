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

Task 020 was retired as `done/020-take-brussels-done-T237.md`: 布鲁塞尔 fell on T237 to
the Bombard and Field Cannon fire from (68,31), (69,31), (70,31), (71,30) and a Line Infantry attack
from (69,28), after a wall probe on T235 read `walls: 200/200` and the capture read
`city hp 200/200 -> 0, walls 200/200 -> 0` across T236-T237. The directory was empty from T216 (task
018 retired) to T220; those retirements and their measurements are in `done/` and
`docs/task-history.md`.

Task 019 was retired as `done/019-two-scouts-to-sea-expired-T250.md`.

Task 021 was retired as `done/021-siege-legion-overseas-expired-T270.md`.

Task 022 was retired as `done/022-take-haarlem-done-T271.md`.

**The retirements listed above are the record of runs that were rolled back.** Two of them: the one
that stood at T281 (it took 布鲁塞尔 at T237 and 哈勒姆 at T271), and the attempt that started from this
same T218 save and reached T301 (it took 布鲁塞尔 at T224 - that is 024). **This position is T218**, where
none of those holds: 布鲁塞尔 is a city-state again, 哈勒姆 is still the Netherlands', and the whole task
set at T218 is being rolled back by `.tools/rollback-tasks.py`.

Task 024 was retired as `done/024-take-brussels-done-T224.md`.

Task 024 was restored by the rollback to T218: it was retired at T224, after the target turn, so its `done when:` is false again there.

**Four more tasks were retired after T218 and were left retired deliberately** (the human's call, asked
and answered on 2026-09-28), because the rollback undid their results but their instructions are not
wanted at this position:

- 019-two-scouts-to-sea.md (retired T250, added T220) - a thirty-turn exploration window that belongs
  to the abandoned attempt; re-opening it would re-arm an expedition nobody asked to repeat.
- 020-take-brussels.md (retired T237, added T232) - **the same objective as the restored 024**, filed
  on the T281 run. 024 is the newer file, its `done when:` is the same proof, and its T241 deadline is
  reachable from T218, so one Brussels task is enough.
- 021-siege-legion-overseas.md (retired T270, added T237) - an overseas expedition whose whole window
  (T237-T270) belongs to an abandoned run.
- 022-take-haarlem.md (retired T271, added T257) - Haarlem is a subset of 023's campaign ("every
  Dutch city"), which stays in force, so the campaign file covers it.

`.tools/rollback-tasks.py 218 --apply --skip 019 --skip 020 --skip 021 --skip 022` is the command that
produced this state; its backup is `.civ6-mcp-data/branches/rollback-tasks-T218-20260928-174858/`.

Task 024 was retired as `done/024-take-brussels-done-T221.md`.

Task 019 was restored by the rollback to T224: it was retired at T250, after the target turn, so its `done when:` is false again there.

Task 020 was restored by the rollback to T224: it was retired at T237, after the target turn, so its `done when:` is false again there.

Task 021 was restored by the rollback to T224: it was retired at T270, after the target turn, so its `done when:` is false again there.

Task 022 was restored by the rollback to T224: it was retired at T271, after the target turn, so its `done when:` is false again there.

Task 020 was retired as done: 布鲁塞尔 (69,29) reads [CITY_CENTER] owned by 中国 with our Cuirassier standing on it, it is in get_cities (pop 7, id 1310739) and it is off get_city_states; the assault ledger is the rolled-back run's (wall probe walls 200/200 at T235, fire from (68,31),(69,31),(70,31),(71,30) plus a Line Infantry attack from (69,28) across T236-T237).

Task 022 was retired as `done/022-take-haarlem-done-T241.md`.

Task 019 was retired as `done/019-two-scouts-to-sea-expired-T250.md`.

Task 025 was retired as `done/025-two-scouts-to-sea-contact-done-T251.md`.

Task 023 was retired as `done/023-dutch-siege-corps-done-T259.md`.

Task 027 was retired as `done/027-kill-apostles-mobile-done-T259.md`.

Task 026 was retired as `done/026-coastal-navy-frigates-done-T261.md`.

Task 021 was retired as `done/021-siege-legion-overseas-expired-T270.md`.

Task 028 was retired as `done/028-development-science-wonders-expired-T288.md`: Superseded: the match this file governed was handed over and a new match was started for the military production experiment; see docs/experiments/README.md.

Task 029 was retired as `done/029-two-scouts-sea-info-expired-T288.md`: Superseded: the match this file governed was handed over and a new match was started for the military production experiment; see docs/experiments/README.md.

Task 030 was retired as `done/030-military-production-attempt-a1-expired-T40.md`: Superseded: A1 stopped at its own T40 review point with the review written; the review re-scoped the target and attempt A2 continues from the same save under task 031. A1's position is preserved in the saves and its numbers in docs/experiments/A1-T40.json.

Task 032 was retired as `done/032-attempt-a2-second-half-t41-to-the-first-siege-order-done-T66.md`: the first siege order was read at T48 (both Catapults, before any economy order); the assault continues under 033

Task 031 was retired as `done/031-military-production-attempt-a2-done-T68.md`.

Task 033 was retired as `done/033-attempt-a2-third-phase-the-assault-on-the-city-state-t66-to-the-attempt-s-end-done-T68.md`.

Task 034 was retired as `done/034-attempt-a3-the-same-doctrine-against-a-walled-target-from-the-shared-t1-start-done-T72.md`.

Task 035 was retired as `done/035-attempt-a4-the-encampment-before-the-second-siege-unit-done-T66.md`.
| `036-attempt-a5-the-chops-go-into-units.md` | 2026-09-30 | turn 75 | whether the chops belong to the units instead of the buildings, from the experiment's shared start | turn 70 is reached, or a city is kept (a city_action reply reads KEEP|, or the move's reply reads |
