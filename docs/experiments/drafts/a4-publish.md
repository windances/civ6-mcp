# A4 publish note (do this only after A3 has been retired)

A task file dropped into `prompts/tasks/tmp/` is read by the **running** session on its next turn,
so A4 must not be published while A3 (task 034) is still playing. Publish it in the same commit
that retires 034.

Number: **035** (034 is A3).

```
.venv\Scripts\python.exe scripts\temp-task.py add `
  --title "TEMP TASK 035 - attempt A4: the Encampment after the second city, from the shared T1 start" `
  --instruction "继续A3 ~ A7" `
  --slug "attempt-a4-the-encampment-after-the-second-city" `
  --scope "@docs/experiments/drafts/a4-scope.txt" `
  --overrides "@docs/experiments/drafts/a4-overrides.txt" `
  --done-when "@docs/experiments/drafts/a4-done-when.txt" `
  --why "the Encampment's place in the queue, tested from the experiment's shared start" `
  --expires-turn 115 `
  --body-file docs/experiments/drafts/a4-body.md `
  --cn @docs/experiments/drafts/a4-cn.md
```

Notes:
- `--cn` needs the Chinese backup file to exist (`docs/experiments/drafts/a4-cn.md` is written) and the script writes
  the two-line "this is a backup, not an instruction" note itself, so the backup must **not** carry
  that note.
- The script runs the text gate and `tests/test_temp_tasks.py` and commits only when both are green;
  it also rewrites the `IN FORCE NOW` line in `AGENTS.md` and `prompts/tasks/tmp/current_tasks.md`.
- `--why` is ASCII and carries no tile coordinate (the script refuses one that does).
- The body's `expires:` prose must agree with `--expires-turn 115`.

Still to write before publishing: `a4-scope.txt`, `a4-overrides.txt`, `a4-done-when.txt`.

Written: `docs/experiments/drafts/a4-done-when.txt`, `docs/experiments/drafts/a4-overrides.txt`, `docs/experiments/drafts/a4-scope.txt`.

## A5, A6, A7 - the same shape, one at a time (numbers 036, 037, 038)

**Publish each only after the previous attempt is retired.** Every one of these files is read by the
session that is playing, so two of them in force at once is two variables in one attempt.

| number | attempt | body | cn | title | numbers |
|---|---|---|---|---|---|
| 036 | A5 - the chops go into units | `docs/experiments/drafts/a5-body.md` | `docs/experiments/drafts/a5-cn.md` | `TEMP TASK 036 - attempt A5: the chops go into units, from the shared T1 start` | `--turns`/`--expires-turn 75` |
| 037 | A6 - the siege train is bought | `docs/experiments/drafts/a6-body.md` | `docs/experiments/drafts/a6-cn.md` | `TEMP TASK 037 - attempt A6: the siege train is bought with gold, from the shared T1 start` | `--expires-turn 75` |
| 038 | A7 - two war cities | `docs/experiments/drafts/a7-body.md` | `docs/experiments/drafts/a7-cn.md` | `TEMP TASK 038 - attempt A7: two war cities instead of one, from the shared T1 start` | `--expires-turn 115` |

Each takes `--slug attempt-a5-the-chops-go-into-units`, `attempt-a6-the-siege-train-is-bought`,
`attempt-a7-two-war-cities` (or close), `--instruction "继续A3 ~ A7"`, `--added` left to default, and:

- `--scope @docs/experiments/drafts/a5-scope.txt` / `a6-scope.txt` / `a7-scope.txt` - written
- `--overrides @docs/experiments/drafts/a5-overrides.txt` / `a6-overrides.txt` / `a7-overrides.txt` - written
- `--done-when @docs/experiments/drafts/a5-done-when.txt` / `a6-done-when.txt` / `a7-done-when.txt` - written
- `--why` (one ASCII line, no coordinate):
  - A5 `whether the chops belong to the units instead of the buildings, from the experiment's shared start`
  - A6 `whether gold can put the first siege unit in hand earlier than production can, from the shared start`
  - A7 `whether a second war-production city pays for the compounding it costs, from the shared start`

**A6's `overrides:` names the rule it deliberately breaks** (`carrying-capacity` going red is the variable's
measured cost, recorded in the diary each turn it fires, not a blocker). A5 and A7 override nothing.

**A5 depends on the staged doctrine edit** (`docs/experiments/drafts/tactics-01-chop-rule.md`): apply that with the commit that
retires 034, before A5 is published, and re-index (`python .tools/kb.py index`).

