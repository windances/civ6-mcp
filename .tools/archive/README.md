# One-off scripts, kept as evidence

Everything in this directory answered **one question about one match, once**. Nothing here is
expected to run again.

They were not deleted because they are evidence: a retrospective or an experiment record often cites
the script that produced a table, and the numbers in `docs/experiments/` are only checkable while
the thing that measured them still exists. If a record points at `.tools/<name>`, look for it here.

## Why they are separated

`.tools/` had grown to 367 top-level files, and the two kinds in it were indistinguishable at a
glance:

    turn-verify.py        a tool that runs again, on any match
    t103.py               one turn of one match, written once and read once
    _amenity_probe.py     one question, answered
    _advisor-brief.md     an input handed to one advisor call

That is how a directory whose whole purpose is "the things I run" stops being readable, and it is
why `tests/test_live_tools_have_no_match_state.py` has to name its live tools explicitly instead of
scanning the directory: **a pattern cannot tell the two kinds apart, so the list has to.**

## The rule for the top level

A file belongs at `.tools/` top level when it takes **live game input** and is **expected to run
again** - on this match or any other. It must then carry no fact about one match: no city name, no
unit id, no player id, no run key. `.tools/_game.py` is the resolver for the run key, and the guard
test holds the list to that rule.

Anything else - scratch, a turn-specific probe, a dump, an advisor brief, a `*-refl.json` - belongs
here.

`.tools/archive-one-offs.py` draws the line: it moves a file only when it matches a dead pattern
(`_`-prefixed, `t<turn>-`-prefixed, `commit-msg-*.txt`, or a bare `.txt`/`.log`/`.png`/`.csv`
output) **and** is not on its explicit live list. Anything ambiguous stays put, because moving a
live tool is worse than leaving a dead one.

## These files are not in version control

`.tools/` is gitignored, so the move changed where they live on disk and nothing else - they were
untracked before and they are untracked here. They will not survive a clean checkout, and they never
would have. A record that depends on one of these numbers should quote the number, not only the
path.
