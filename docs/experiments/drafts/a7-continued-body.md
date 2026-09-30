Attempt **A7 continued** to T110. The attempt itself is `007-attempt-A7.md` and it is **over** - a city was
kept at T60, which is what its own `done when:` asked for. What this task does is hold A7's position and
configuration for another forty turns so that the comparison the next two attempts need actually exists:
**A8 and A9 are measured at T110, and a baseline that stops at T60 has no T70-T110 economy row to be
compared against.** Nothing about A7's variable changes, and this continuation introduces no variable of
its own.

## Start: the live match, not the shared start

0. `get_game_status`. **This task continues the match where it stands** - it stood on **T69** when this
   file was written, on A7's own branch. **Do not load `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save` and do
   not restart**: that save is the starting point for **A8 and A9**, and loading it here would destroy the
   comparison this task exists to create.
   - **If the game stands anywhere on this branch from T69 up to the horizon (T110), continue it.** That
     window is deliberately wide because this task may be **resumed**: a session that runs out of its own
     budget hands the match over mid-window, and a resume has to be able to carry on from wherever it
     stopped rather than refuse the position it was handed. Say in the diary which turn you picked it up
     on, and read `get_diary` first - a resumed turn inherits the previous session's plan and its
     half-finished orders.
   - **If it stands before T69, or past T110, or somewhere that is not this branch** - a different save, a
     different match - **say where in the diary and stop**. Do not guess which position the task meant.
1. The position inherited from A7, to be confirmed and not assumed: **three cities** - 西安, the second
   city founded at T21 (the tile is in A7's record and in the diary), and **耶路撒冷, kept at T60**. Read
   `get_cities` and say in the diary whether the reading matches that description, city by city, with the
   population. **On a resume the city count may legitimately have grown or shrunk** - say what it is and
   when it changed rather than treating a difference from three as an error.
2. Then `get_diary` and one `scripts\orient.py` read.

## The first thing to do after orienting: the read A8 is blocked on

**`get_global_settle_advisor`, once, early - do it on the first turn this task runs.** Two cities have
stood for many turns, so this read names every site that is still legal, and it is **the read no attempt
in the programme has ever taken**: the three times the tool was called before (A7 T7, A7 T15, A6 T18) all
predate the second city's founding, so the third site on this start is unknown. A8's publication is
waiting on it.

Report it in the diary **verbatim** - the whole top ten, with each tile's score, whether it has fresh
water, and its resources - and then answer three questions in the same entry:

- how many legal settle sites remain at all;
- do the best of them have fresh water;
- is any site **outside the cluster just west of the capital**, or is the whole list inside it.

Two things to carry into that answer. A site is legal only if the tool lists it - the game refuses a city
within 3 tiles of an existing one, and the exclusion is what makes the ten ranked sites *alternatives*
rather than a plan. And **耶路撒冷 is ours now**, so its exclusion ring is part of this read while it would
not have been part of a read taken when A8 would settle; say so, so the number is read with that in hand
rather than as a clean answer.

## What does not change

A7's configuration is held exactly as it finished:

- the same two army cities, the same queues, the corrected `tactics/01` table;
- `tactics/08`'s one-war-city rule **as A7 widened it** (two army cities - that widening is A7's variable
  and it stays);
- the pinned opening is long past and does not apply;
- the standing directive is `prompts/strategies/china-conquest/directive.md`, and `tactics/01`, `04`,
  `05`, `06` and `08` are read as written.

**No `propose_peace`, ever** - refuse every offer, whether it arrives as a trade or as a session.

**If the empire changes shape** - a new war opened, another city taken, a district or a unit line started
that A7 had not started - **record it in the diary that turn as a divergence from this task's posture**.
It is not forbidden; it is the kind of difference that has to be named rather than discovered later,
because A8 is compared against this run at T110.

## The one override: the wonder obligation is deferred, on purpose

`dynasty-cycle-wonder` (`prompts/checks/turn-checks.md`) is live from T25 and **will print
`CHECK FAILED [dynasty-cycle-wonder]` every turn from here on**: the empire holds zero wonders, which the
rule reads as half of China's civilisation ability forfeited.

**Accept it and build no wonder in this continuation.** A wonder here would be a second variable against
A8, whose arm is the third city's market, and A7 would stop being the baseline it is being extended to be.
Say so in the diary **the first turn it fires** - one line, that it is accepted and why - and after that
mention it only when it changes something. This is `AGENTS.md`'s own rule: a failing check is fixed, or
accepted out loud, and never passed unnoticed.

## The measurement this task exists for

The experiment reads the diary's **per-10-turn economy rows**. Keep the five reflection fields every turn
(`tactical`, `strategic`, `tooling`, `planning`, `hypothesis`) and make sure the rows for **T70, T80, T90,
T100 and T110** are written - they are the comparison's whole output.

What A8's claim will be read against, in numbers: `cities`, `pop`, `science`, `gold_per_turn`,
`districts`, `improvements`, and **whether a second siege unit was ever bought with gold** - A6 bought its
first at T46 for 320g out of 396g and the programme's arithmetic said two of them were impossible before
about T70 on an older path, so the purchase column at T110 is a number worth having.

## End

The task ends the turn **turn 110 is reached** (`get_game_overview` reports turn 110). On that turn report:

- the T110 economy row beside the T60 one, field by field;
- whether the empire's configuration changed, and the diary turn where it did;
- whether any wonder was built - the expected answer is none, accepted, and it belongs on the record
  rather than left as an absence;
- the pre-flight settle-advisor read, if it is somehow not already in the diary.

Then retire this task with `--done` and the turn, and hand back to the orchestrator: **A8 is next, from
the shared T1 start, and the pre-flight read is what publishes it.**
