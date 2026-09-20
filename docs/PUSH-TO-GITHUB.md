# Getting this checkout onto GitHub

This working copy arrived as a **zip**, not a clone, so there is no history to push from: the
repository had to be initialised here, and the commit that captures the work is a **root commit**
(unrelated to `origin/main`). Because of that a plain `git push` is rejected as a
non-fast-forward, and `git push --force` would **replace the upstream history** - do not use it.

Land the work on top of upstream instead, from a terminal that has network access (the sandboxed
shell this repository is maintained from has no outbound HTTPS at all, and Git's credential
helper cannot run there either - it needs pipes the sandbox denies):

```powershell
cd C:\mine\mine\ws_dsh\civ6

# 1. Get upstream history. Reviewed: this commit is a snapshot of the whole tree, so the diff
#    against upstream is only "our changes" if the zip was taken from (or near) this commit.
git fetch origin main

# 2. Move this branch onto upstream, keeping the working tree. The index still holds our
#    snapshot, so the next diff is exactly our changes vs upstream.
git reset --soft origin/main

# 3. REVIEW before committing. Anything upstream changed since the zip was taken shows up here
#    as a change of ours - look at it, because it is the one thing that can go wrong.
git status --short
git --no-pager diff --stat --cached origin/main

# 4. Commit on top of upstream, reusing the message of the snapshot commit.
git commit -C dbf1e50

# 5. Push.
git push origin main
```

If step 3 shows upstream files being reverted that this work never touched, do not commit: say so
and re-take the zip from a fresh clone instead.

## What the snapshot commit contains

`dbf1e50` - *Turn the strategy directive into an enforced, auditable contract*: the MCP-side turn
checks and their feedback (goal retirement and file sweep, contact metrics, `BATTLE ASSESSMENT`,
`SIEGE POSTURE`, `SIEGE PROGRESS` / `SIEGE STALLED`, unused-attack reporting, city HP on every
attack, our own losses reported from an `ACTION_ENDTURN` baseline, `[IN <city>]` marking), the six
tactic files under `prompts/tactics/`, the advisor brief/validate/trace contract in the skill, and
509 tests.

`.tools/` is git-ignored in this repository; the five verification scripts the docs reference
(`advisor-rehearsal.py`, `verify-advisor-proposal.py`, `siege-retro.py`, `goal-status.py`,
`show-check-prune.py`) were force-added so those references are not dangling.
