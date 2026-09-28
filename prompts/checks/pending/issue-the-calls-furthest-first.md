# issue-the-calls-furthest-first - STAGED, do not cut in until a server computes the metric

Written 2026-09-28 (T300, from the T228-T299 review). Staged rather than live because
`prompts/checks/turn-checks.md` is re-read every turn by the *running* process, whose metric set is in
memory: a rule naming `move_stops_this_turn` before a server computes it reports `un-evaluable` every
turn and nobody can satisfy it. The code that computes it ships in the commit that adds this file; the
rule moves up to `../turn-checks.md` once a session running that code has started.

**Metric it needs:** `move_stops_this_turn` - counted by `GameState.note_move_stops` from every tool
result carrying `STOPPED_MID_PATH` / `STOPPED_SHORT`, and reset each turn alongside
`_attacks_this_turn`.

**Why it exists - measured T228-T299.** **232 partial moves across 72 turns** (T257-T259 alone: 15, 17,
19; T234 ordered eight units and took eight stops one to three tiles short), with every staging plan
leaving 6-9 units unplaced (T254: 9 of 10). The plan assigns distinct tiles, but nothing said which
*call* goes first, so a column ordered nearest-first queues behind itself - and the same jam is what
kept the artillery 13-22 tiles out of 021's target until its window expired.

The proposed rule, in the shape `turn-checks.md` uses:

```
<!-- check
id: issue-the-calls-furthest-first
when: metric(move_stops_this_turn) >= 3
require: metric(move_stops_this_turn) <= 2
message: Three or more units were ordered somewhere this turn and stopped short of it: that is the column queueing behind itself, not fighting. `get_staging_plan` prints the order the calls should go in (furthest ring tile first, nearest last) - issue them in that order, one move per call with a `get_units` between them, and re-issue a stopped unit before moving the next. Measured T228-T299: 232 stops in 72 turns, 19 in a single turn, and every staging plan leaving 6-9 units unplaced.
-->
```

Notes for whoever cuts it in:

- Two stops is traffic and the rule stays quiet; three is a column.
- It pairs with the `ISSUE THE MOVE CALLS IN THIS ORDER` line in `src/civ_mcp/staging.py`: the tool
  prints the order, this rule counts whether the order was followed.
- The same escape hatch as its neighbours: a turn that stops three units for a stated reason (a Zone of
  Control entry, a landing, a corridor that only fits one unit) belongs in the diary.
