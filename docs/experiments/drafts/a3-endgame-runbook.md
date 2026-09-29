# A3 end-game runbook - the moment attempt A3 ends

The attempt ends when a city is kept (a `city_action` reply reads `KEEP|`) or the game reaches **T110**,
whichever comes first (`expires:` T115). When it does, these are the steps in order. Nothing here is
judgement - the judgements live in `docs/experiments/003-attempt-A3.md` and the retro.

## 0. Stop the clock, then confirm the end

- The session stops by itself when its brief's finish line holds. If it is still running after the end
  condition, let it retire the task in its own `tooling` line; only `scripts\civ6-clean.ps1` stops a live
  session, and FireTuner serves exactly one connection, so **do not launch anything else while it plays**.
- Read the end from the log, not from the session's prose: `KEEP|` in a `resolve_city_capture` reply, or
  the last turn.
- **Write down every session id this attempt used.** A3 has two already
  (`flint-indigo-rampart-32` for T1-T25, `crumbling-emerald-parapet-16` from T25 on) and a session that
  dies mid-attempt is this project's normal rhythm. Every command below takes the whole list.

## 1. The snapshot (the attempt's own numbers)

```
.venv\Scripts\python.exe scripts\experiment-report.py --game china_911679432 ^
  --run flint-indigo-rampart-32,crumbling-emerald-parapet-16 ^
  --from 1 --to <last turn> --step 10 --verdict --questions a3 ^
  --save docs/experiments/A3-final.json
```

`--questions a3` answers A3's own four questions and prints the wall phase. **Snapshots keep the
measuring definitions they were taken with** - `A1-T40.json` and `A2-final.json` were taken before the
self-report reader and the `ESTABLISHMENT` table were corrected, so a re-run of those logs is not
comparable to them. That is the protocol, not a defect; the retro says so.

## 2. The three-way compare (one command, one line per attempt)

```
.venv\Scripts\python.exe scripts\experiment-report.py --compare ^
  docs\experiments\A1-T40.json docs\experiments\A2-final.json docs\experiments\A3-final.json
```

`--compare` is N-ary by design, so A4-A7 get appended to the same command rather than written a second
time. Read it with the divergences in hand: A3's pin broke at T15, its pantheon arrived T26 against A2's
T41, and it ran Pingala from T41 - none of which is the target's defences.

## 3. The wall phase, whether it happened or not

- If a city with a wall pool above zero was attacked: record the **first turn the pool read above zero**,
  the turn it read zero (**the breach**), the turn the city was kept, and the pool's arithmetic between
  them. Those are the numbers A2 never produced, because its target read `walls: none`.
- If no such city was found or attacked: **that is the attempt's answer**, and the record quotes the
  instrument's own line (`no city with a wall pool above zero was attacked by T<n> - the wall phase is
  unaskable on this map`) beside the list of cities actually read. An unaskable question reported as
  unaskable is a result; a walled city's absence is not a reason to call the attempt a failure.
- A city-state's walls appear after Masonry and cost production, so **a city read early must be re-read
  later** in the window - the record says which reads it rests on.

## 4. Fill the record

`docs/experiments/003-attempt-A3.md`: the end table, the verdict on Q1-Q4, the wall paragraph, the cost of
the assault (units lost, turns spent), and the answer to the one question the attempt exists for - **what a
walled target changed and what it did not**.

## 5. Fill the retro

- A3's row in `RETRO-2026-09-29.md`'s "the attempts since A2, one row each".
- Any finding this attempt produced, with its **sink** (code + test / a check rule / the task file / the
  directive / the tactics file / this retro), in the ladder the retro's section 2 uses.
- The owed list, if A3 closed or opened something on it.

## 6. Retire 034 and publish A4 - one commit, in this order

Publishing A4 while 034 is still in force puts **two variables in one attempt**, so the two move together:

```
.venv\Scripts\python.exe scripts\temp-task.py retire 034 --done --turn <the turn A3 ended on>
.venv\Scripts\python.exe scripts\temp-task.py add ^
  --title "TEMP TASK 035 - attempt A4: the Encampment after the second city, from the shared T1 start" ^
  --instruction "继续A3 ~ A7" --slug "attempt-a4-the-encampment-after-the-second-city" ^
  --scope "@docs/experiments/drafts/a4-scope.txt" ^
  --overrides "@docs/experiments/drafts/a4-overrides.txt" ^
  --done-when "@docs/experiments/drafts/a4-done-when.txt" ^
  --why "the Encampment's place in the queue, tested from the experiment's shared start" ^
  --expires-turn 115 --body-file docs/experiments/drafts/a4-body.md ^
  --cn @docs/experiments/drafts/a4-cn.md
```

Then `python scripts/fix-text-encoding.py` and `python .tools/kb.py index` (the index is derived and goes
stale the moment the task files change). `docs/experiments/drafts/a4-publish.md` carries the A5-A7 commands
and the per-attempt header fragments.

## 7. The staged doctrine edit

`.tmp`-era note kept in `docs/experiments/drafts/tactics-01-chop-rule.md`: the chop-into-units rule for
`prompts/tactics/01-unit-production.md` is A5's tested claim and must land **with the commit that retires
034**, before A5 is published - never during a live session, because the advisors read that file every turn.
