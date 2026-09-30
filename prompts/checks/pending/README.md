# Staged rules — written here, cut in only when the server can compute the metric

`prompts/checks/turn-checks.md` is re-read by `end_turn` on every turn, but **the metric set lives in
the running MCP process's memory**: `turn_checks.evaluate` raises on a metric it does not know. A rule
cut into `turn-checks.md` before a server computing its metric is running therefore reports itself
`un-evaluable` on every turn and nobody can satisfy it — a rule that looks alive and is not.

So a new rule is staged **here** first, as `<rule-id>.md`, and moved up to `../turn-checks.md` in the
same commit that ships the code computing its metric. That is the staging that worked for
`answer-the-camp` (metric `camps_within_3`, computed by `_camps_within_3` from `get_map_area`) and
`cut-the-supply` (metric `enemy_supply_uncut_with_idle`, from the `idle3:` field of the
capture-readiness scan): both were cut in at T174, once a server computing their metrics was running.

- This directory is **empty in the normal state**. Its being empty says nothing about whether
  `../turn-checks.md` is complete — `tests/test_camp_rules.py` asserts the two rules above are live
  there rather than staged here.
- A staged file states the rule's id, its `require:` expression in the same shape as `turn-checks.md`,
  the metric it depends on, and the code that has to ship first. **It must also state a `message:`** -
  `turn_checks.parse_checks` skips a block that has no `require` *or* no `message` (silently, at
  `log.debug` level, because the parser cannot tell it from an example written inside prose). A promoted
  block without one therefore sits in `turn-checks.md`, reads as in force, and never fires - the exact
  failure this directory exists to prevent, reintroduced by the staging format itself. Measured
  2026-09-30: both staged files here were written without a `message:` and would have been dropped on
  promotion; `tests/test_pending_rules.py` now holds every staged rule to the promotable shape.
- **A staged file's `level:` is not automatically the live convention.** All **24** rules in
  `../turn-checks.md` are `warn`, and **none of them declares a `level:` line at all** (measured
  2026-09-30, the day the third rule was promoted), while both staged files here say `level: error`. The
  only thing `level` does is sort the reported failures - `end_turn.py:1093` reads
  `priority=1 if check.level == "error" else 2` - so promoting a staged block verbatim would introduce
  the file's first `error` rules and quietly change what the agent reads first. Decide it on purpose:
  carry the `level:` over, or drop it to match the file. `concentrate-the-siege` was promoted as `warn`.
- A rule that needs no new metric does not belong here: write it straight into `../turn-checks.md`.
