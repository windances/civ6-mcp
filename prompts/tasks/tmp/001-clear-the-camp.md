# TEMP TASK 001 — clear the barbarian camp beside 北京

added:     2026-09-26 (human instruction; "make the camp a pre-war analysis target and destroy it")
expires:   turn 95 — retire this file by then whatever happens
done when: the camp tile no longer holds `IMPROVEMENT_BARBARIAN_CAMP`
overrides: the strategy directive's "Do NOT clear barbarian camps" line, which is superseded; the
           leader ability 三十六计 note about keeping camps as a conversion pool is answered by the
           `CONVERT` step below and does not defer the raid
scope:     one raid. No declaration of war, no second front, and no change to the development plan
           (research, civics, districts, builder tasks and the Temple of Artemis carry on untouched).

## What

Destroy the nearest barbarian camp using the war strategy, and answer
`prompts/tactics/07-pre-war-analysis.md`'s **camp gates by name** in the diary:
`CAMP / GUARD / FORCE / GROUND / WORTH / HOLD / CONVERT / GO`.

## First move, this turn

Read the camp's neighbourhood (`get_map_area` around **(60,30)** — the camp that has been producing
Spearmen beside 北京) and write the `GUARD` line: how many barbarians stand within two tiles, with
their class, combat strength and HP. That is the one fact the raid is planned from and the only thing
still missing. Do not move anything onto the camp tile before that line exists.

## The rules the raid runs on

- **A camp is not a city.** No HP pool, no walls, no garrison bonus: one military unit **MOVING**
  onto its tile clears it. The last act is a MOVE, not an attack (attacking spends the unit's
  movement), and the moving unit must arrive **unspent from a tile we already held last turn**.
- **The guard is the enemy.** The analysis is the barbarians within two tiles, not the camp.
- **Two attackers, with the counter unit.** Barbarian **Spearmen are anti-cavalry → cavalry is the
  wrong unit**; ranged fire first (it takes no retaliation), then a melee walk-in. One attacker
  trades. Never send a Scout, Builder or Trader — a civilian is captured instead of clearing it.
- **`CONVERT` before you clear.** Report any barbarian standing next to one of our melee units whose
  type is worth the human's 三十六计 conversion, so the human can play it from the game UI — then
  clear the camp anyway. Do not keep a camp alive as a conversion farm.
- **`WORTH` and `HOLD`.** Record gold, era score, the `CIVIC_MILITARY_TRADITION` inspiration (its
  boost is "clear a barbarian camp") and what the camp has already spawned; say which city gives up
  its garrison for the raid, and that it gets it back.

## When it is done

Move this file to `../tmp/done/001-clear-the-camp-done-T<turn>.md`, say so in the diary's `tooling`
line with the turn number and the camp's coordinates, and resume the normal turn loop. If the camp is
somehow still standing at turn 95, move it to `done/001-clear-the-camp-expired-T95.md` and report why
in the diary rather than leaving it here.
