# TEMP TASK 030 - military production experiment, attempt A1

added:     2026-09-29 (human instruction: 你自己启动游戏，开局新游戏，选中国，2个对手，难度适中，小地图，进行以军事为目的的最优生产力策略的调优。记录你所有的尝试，能复盘。)
expires:   turn 90 - 30 turn(s) from T1, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: an enemy city is kept (a city_action reply reads KEEP|) or the game reaches turn 80, whichever comes
           first
overrides: nothing - this file is the whole instruction for this match; the standing directive supplies posture
           only
scope:     this match only: the Pangaea/Small/Prince match whose turn-1 save is
           evals/saves/ATTEMPT-A1-T1.Civ6Save

# Attempt A1 - the military production doctrine as written

This is the first attempt of the experiment defined in `docs/experiments/README.md`. **The one
variable is nothing**: play the production doctrine exactly as written, so later attempts have a
baseline to move away from.

## The settings, read back from the running game (not from the setup screen)

| Parameter | Value | How it was read |
|---|---|---|
| Civilisation | China, Qin (Unifier) | `PlayerConfigurations[0]` = `LEADER_QIN_ALT` / `CIVILIZATION_CHINA` |
| Opponents | 2 - Australia (John Curtin) and the Maori (Kupe) | players 1 and 2 are the only other majors |
| Difficulty | Prince | the setup screen read 王子 |
| Map | Pangaea, Small | the setup screen read 盘古大陆 / 小; the slots show six seats |
| Speed | Quick | the setup screen read 快速 |
| Ruleset | Gathering Storm | `GameConfiguration.GetValue("RULESET")` = `RULESET_EXPANSION_2` |
| Start | turn 1, 4000 BC, no actions taken | `Game.GetCurrentGameTurn()` = 1 |
| Replay | `evals/saves/ATTEMPT-A1-T1.Civ6Save` | saved from the live game at turn 1 |

## What this attempt is testing

The doctrine under test is `prompts/tactics/01-unit-production.md` - the establishment table and the
production order - with `prompts/tactics/08-war-and-the-home-front.md` for the war economy. Its
testable claims are H1-H6 in `docs/experiments/README.md`. Play them as written; do not improve them
mid-attempt, because a changed variable is a different attempt.

**The two numbers this attempt is judged on**, both to be reported in the diary with the turn they
happened:

1. **the turn the army first matches the establishment** - siege 2 / melee 2 / ram 1 / ranged 4 /
   cavalry 1, readable from the diary's `unit_composition`;
2. **the turn the first enemy city is kept** - the `city_action` reply that reads `KEEP|`.

## Every ten turns

Answer the `10-TURN REVIEW`'s three questions in the diary with numbers, and add these two lines to
the `strategic` reflection:

```
ESTABLISHMENT: siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1 at T<n>
WAR READY: <the turn the establishment was complete, or "not yet">
```

## The first stop: the end of turn 40

Play to the end of **turn 40**, then stop and report - do not carry on past it. The experiment takes
its mid-window review at T40, and the review needs the attempt to stop at a known turn for the
numbers to line up with the stretch that follows. **Stopping is not retiring**: this file stays in
force, the attempt continues after the review, and the session that resumes it starts from T41.

What the report at T40 must put in the diary's `strategic` line, so the review can be written without
re-reading the whole log:

```
T40: cities n, pop n, science n, culture n, gold n (+n/t), military n
ESTABLISHMENT: siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1 at T<n>
WAR READY: <the turn the establishment was complete, or "not yet">
ENEMY SEEN: <which rival cities are visible, and the distance in tiles to the nearest one>
```

## The stop

The attempt ends the turn the first enemy city is kept, or at turn 80, whichever comes first. Retire
this file in that turn (`scripts/temp-task.py retire 030 --done --turn N`, or `--expired`), and write
the attempt's record as `docs/experiments/001-attempt-A1.md` from the output of
`scripts/experiment-report.py --game china_911679432 --step 10` (add `--verdict` for P1-P4; the
report computes the two decisive numbers itself, so quote it rather than the diary's own summary).

Do not open a second war before the first city is kept. Scouting, settling and infrastructure are
this attempt's business as much as the army is: the question is what the army cost the empire, and
that is only answerable if the empire did the rest of its job too.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "military production experiment, attempt A1" --instruction @.tmp/task030-instruction.txt --why "military production experiment attempt A1: play the production doctrine as written and record the two decisive turns" --done-when "an enemy city is kept (a city_action reply reads KEEP|) or the game reaches turn 80, whichever comes first" --overrides "nothing - this file is the whole instruction for this match; the standing directive supplies posture only" --scope "this match only: the Pangaea/Small/Prince match whose turn-1 save is evals/saves/ATTEMPT-A1-T1.Civ6Save" --slug 030-military-production-attempt-a1 --expires-turn 90 --body-file .tmp/task030-body.md --cn @.tmp/task030-cn.md --no-commit --no-gate
     at: 2026-09-29T03:34:58+08:00
     chinese backup: prompts/tasks/cn/030-030-military-production-attempt-a1.cn.md
-->
