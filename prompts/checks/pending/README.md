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
  the metric it depends on, and the code that has to ship first.
- A rule that needs no new metric does not belong here: write it straight into `../turn-checks.md`.
