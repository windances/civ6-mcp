# Which document a rule belongs in

The long form of the routing rule in `AGENTS.md`, with the measurements behind it.

## Which document a rule belongs in: four layers, one routing test

A rule written in the wrong layer is a rule that gets skipped, and this match has measured that
three times over. The layers, and what each one is actually for:

| Layer | Who reads it | What it can do |
|---|---|---|
| the directive (`prompts/strategies/<name>/directive.md`, delivered as the skill DIRECTIVE) | the session, once per change | states the what and the why |
| `prompts/tactics/` files 01-08 | the advisor named by the prompt, at the decision | states the how |
| a file in `prompts/tasks/tmp/` | the turn loop, and only because it lists that directory | carries an instruction in force with a finish line |
| `prompts/checks/turn-checks.md` | the engine, on **every** `end_turn` | **the only layer that can bounce the turn** |

**The routing test, in order:** a *what or why* goes in the directive; a *how that repeats* goes in
`prompts/tactics/`; *this window's work* goes in a task file; **anything mechanically checkable goes
in `prompts/checks/turn-checks.md`** - a rule the engine evaluates retires itself on the turn it is
achieved and cannot silently expire, which a task file does. Task 073 is the case in point: the
staging table is measurable, so its home is a check, not a file.

### What a task file must carry, or it will be worked around

1. **A named first action.** Measured: task 050 asked for cities to be taken, got 21 calls and
   **zero** `unit_action`; task 053 named the target and the first calls and executed the same turn.
   Task 074 was in force through turns 266-278 with **zero** `get_target_report` readings and **zero**
   captures, while 39 production changes and a 50-unit sweep did the work, until its three calls were
   named in its own text.
2. **A trigger that exists today.** Measured: 074 required an *enemy city* while both surviving
   rivals read `war=False`, so the file waited for a condition nothing would create until the trigger
   became *discovery* and the declaration was authorized.
3. **A finish line a working army can satisfy.** Measured: task 062 required both corps within three
   tiles of a rally tile while tasks 069 and 070 had them in the field - a clause no fighting corps
   can ever meet.
4. **An expiry reachable from the queue**, counted from the current turn, not from another task's
   calendar.

### The four standing rules that keep the layers honest

- **The handover rule.** When a task's *build* half completes, its *maintenance* half is published as
  its own file **before** the first retires. Measured: 062 built the two corps and retired at T284,
  and the half that filled short slots retired with it, so the corps decayed with nobody responsible
  until 077 took that half over.
- **The channel rule.** Task files reach the loop only through the `IN FORCE NOW` line in this
  reference: **add or retire a task and update that line in the same commit**. Measured: tasks have
  sat unread for five turns until the line named them.
- **The tension rule.** A task that must contradict doctrine changes the doctrine, and both land in
  one commit - never a quiet divergence. Measured: the human instruction permitting several wars at
  once landed in `prompts/tactics/08`, in task 074 and in task 077 together.
- **The anti-drift rule.** Cite another document by name and step, do not restate its content. A
  restatement is a second copy, and a second copy goes stale. Measured: 075 quoted 074's wording
  after 074 had been rewritten, and 064 still named tasks 062 and 063 after both had retired.

**The audit is one command**: `temp-task.py status` answers what is in force, the turn the game
stands on, whether the three sources agree, and marks anything `PAST ITS EXPIRY`. Run it as part of
the turn's first step, beside the directory listing.

**And the honest limit.** The directive only informs, a task file only instructs, and neither can
compel: the engine is the one layer a session cannot ignore. So a rule that matters and cannot be
measured will eventually be skipped - measured three times on this match. Guarantee comes from a
metric, the channel and the handover; a task file steers; the doctrine sets the context.

