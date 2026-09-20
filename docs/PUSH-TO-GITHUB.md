# Getting this checkout onto GitHub, and pulling changes back

## Pulling changes down

The branch was created here, so it starts with **no upstream**: `git status -sb` prints `## main`
with no `...origin/main`. Set the tracking once, then `pull` works without arguments:

```powershell
git push -u origin main         # pushes and records the upstream in one step
git pull --ff-only              # afterwards: fast-forward only, never a surprise merge
```

Without the `-u`, name the branch explicitly: `git pull --ff-only origin main`.

See what is waiting before taking it:

```powershell
git fetch origin
git status -sb                          # "behind N" / "ahead M"
git --no-pager log --oneline HEAD..origin/main    # in the remote, not here yet
git --no-pager diff --stat HEAD..origin/main
```

If the pull refuses with *"Your local changes would be overwritten"*, park them first:

```powershell
git stash -u
git pull --ff-only origin main
git stash pop
```

In a clone that still has CRLF shell scripts (the `npm run bootstrap` failure), fix the working
copy once after pulling - `.gitattributes` only applies to files git rewrites:

```powershell
git add --renormalize .
git checkout -- '*.sh' '*.bash'
```

Then rebuild and re-verify: `npm run bootstrap:win`, `npm run qualify`,
`.\.venv\Scripts\python.exe -m pytest tests -q`.

Two warnings for **this** directory specifically: it is the game session's working tree, and
`prompts/checks/turn-checks.md` plus the skill are read per turn - so pull at a turn boundary, not
mid-turn. And the Python environment must be re-synced after a pull that changes `pyproject.toml`
(`npm run bootstrap:win` does that).

## Getting this checkout onto GitHub

This working copy arrived as a **zip**, not a clone, so there is no history to push from: the
repository had to be initialised here, and the commit that captures the work is a **root commit**
(unrelated to `origin/main`). Because of that a plain `git push` is rejected as a
non-fast-forward, and `git push --force` would **replace the upstream history** - do not use it.
(That step is already done: `cc1c4a1` is on `origin/main`; the paragraph stays for the next time
this has to be repeated from a zip.)

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

# 4. Commit on top of upstream. The snapshot commit's full message is kept in
#    .git/COMMIT_MSG.txt, so it does not matter which hash it had before the reset.
git commit -F .git/COMMIT_MSG.txt

# 5. Push.
git push origin main
```

If step 3 shows upstream files being reverted that this work never touched, do not commit: say so
and re-take the zip from a fresh clone instead.

## Line endings: `*.sh` must stay LF

`npm run bootstrap` runs `bash scripts/bootstrap.sh`, and on Windows `bash` resolves to
`C:\WINDOWS\system32\bash.exe` (WSL). A CRLF checkout makes bash read the last token as
`pipefail\r`, which fails with `: invalid option name` / `line 2: set: pipefail`. Git for Windows
ships `core.autocrlf=true`, so without a `.gitattributes` every clone rewrites the scripts and
every bash entry point breaks. The policy is pinned in `.gitattributes` (`*.sh`, `*.bash` = LF;
`*.cmd`, `*.bat`, `*.ps1` = CRLF).

In a clone that already has CRLF scripts, rewrite them from the index once:

```powershell
git add --renormalize .          # index: LF for the scripts
git checkout -- '*.sh' '*.bash'  # working tree: rewritten with LF
```

`git config --global core.autocrlf input` prevents the class of problem for every repository on
this machine; it is worth setting on a Windows box that runs POSIX shell scripts.

## What the snapshot commit contains

*Turn the strategy directive into an enforced, auditable contract*: the MCP-side turn
checks and their feedback (goal retirement and file sweep, contact metrics, `BATTLE ASSESSMENT`,
`SIEGE POSTURE`, `SIEGE PROGRESS` / `SIEGE STALLED`, unused-attack reporting, city HP on every
attack, our own losses reported from an `ACTION_ENDTURN` baseline, `[IN <city>]` marking), the six
tactic files under `prompts/tactics/`, the advisor brief/validate/trace contract in the skill, and
509 tests.

`.tools/` is git-ignored in this repository; the five verification scripts the docs reference
(`advisor-rehearsal.py`, `verify-advisor-proposal.py`, `siege-retro.py`, `goal-status.py`,
`show-check-prune.py`) were force-added so those references are not dangling.
