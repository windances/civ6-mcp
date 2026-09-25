# Temporary tasks — one file each, read by the agent, retired by moving the file

This directory is how a **temporary instruction** reaches a session that is already playing, without
editing the strategy directive and without waiting for a restart.

## For the human: how to add one

1. Drop a file in here, e.g. `002-buy-the-barbarian-off.md`. The name is the id; the number orders
   them. Any `*.md` in this directory (except this `README.md`) is an instruction **in force**.
2. Give it the four header lines every task file has — `added:`, `expires:`, `done when:`,
   `overrides:` — and a `scope:` line. They are what lets an agent start, finish and retire it
   without asking:
   - `done when:` must be something the agent can *observe in the game* (`the camp tile no longer
     holds IMPROVEMENT_BARBARIAN_CAMP`), not something it has to argue about.
   - `expires:` is the hard stop. A session that cannot finish the task still retires it and says why.
   - `overrides:` names what the task outranks, so a temporary instruction can contradict the
     standing directive without leaving the agent to guess which one wins.
3. To cancel a task, delete the file. To see what has been done, look in `done/`.

## For the agent: how to consume one

- **Read every `*.md` in this directory at the start of every turn** (with `get_game_overview`), and
  again whenever the turn takes a decision the task touches. Not `README.md`, and not `done/`.
- **Nothing else in the loop knows these files exist.** They are not checkable rules, they carry no
  metric, and the MCP cannot see the filesystem — so a task file is only ever executed because the
  turn loop looked here. An empty directory is the normal state and means no temporary tasks.
- A task is **finished when its `done when:` line holds**. Then move the file into `done/`, renaming
  it to `<nnn>-<slug>-done-T<turn>.md`, and record it in the diary's `tooling` line with that turn
  number. A retired file in `done/` is the proof it ran.
- If a task is still not done at its `expires:` turn, move it to `done/` anyway, rename it with
  `-expired-T<turn>`, and report in the diary why it could not be finished. **Never leave an expired
  task in this directory** — a task file that stays behind is an instruction that never retires.
- If a task file contradicts nothing and is trivially checkable, prefer expressing it as a
  `once: true` goal in `../checks/turn-checks.md` instead: that one retires itself in the engine, and
  a rule is enforced rather than remembered.

## Why files rather than a paragraph in `AGENTS.md`

`AGENTS.md` is re-injected into a running session when it changes, which is what makes it a live
channel — but every temporary instruction written there has to be *deleted again* by hand, and a
reference full of one-off instructions stops being a reference. A file has a lifecycle instead:
present means in force, moved to `done/` means retired, and the standing text in `AGENTS.md` is a
single unchanging pointer to this directory.
