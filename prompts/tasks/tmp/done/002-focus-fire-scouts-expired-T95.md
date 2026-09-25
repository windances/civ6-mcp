# TEMP TASK 002 — focus fire on enemy scouts

added:     2026-09-26 (human instruction: 集火敌人侦察兵)
expires:   turn 95 — retire this file by then whatever happens
done when: no hostile **SCOUT** is within 3 tiles (count == 0) of our units or our cities for 3
           consecutive turns — i.e. the scouting pressure is over. Read it from `get_threat_scan`
           plus `get_map_area` around whatever the scan points at.
overrides: `tactics/02`'s "harmless and immobile → ignore it deliberately" and the directive's "a lone
           scout … may be ignored" — for a **SCOUT** those no longer apply, and it is a target this
           turn. It does **not** override the ban on declaring war: a scout of a civ or city-state we
           are not at war with stays untouchable.
scope:     one target class. No declaration of war, no chase, no change to the development plan. When
           001 (the camp raid) is also in force, the scout is killed first if it is killable this turn.

## What

An enemy scout is the cheapest kill in the game and the one that costs us the most information: it is
the unit that finds the army, the Builder and the settler route, and it dies to two shots. When a
hostile scout is inside three tiles of our units or our cities, **kill it this turn**, with everything
already in range.

This is a **standing order for its window, not a one-shot**: it stays in force until the scouting
pressure has been quiet for three consecutive turns (see "When it is done"), so if no hostile scout is
visible on the turn you read this, there is nothing to do yet — keep the file and watch for one.

## Which scouts are fair game

- **Barbarian scouts** — always at war, always a target. (The camp beside 北京 started as exactly this
  kind of pressure: a barbarian unit reaching our Builders.)
- **Scouts of a civ or city-state we are already at war with** — a target.
- **Everything else is untouchable**: Egypt (declared friend), Kabul, any civ at peace. Civ VI will not
  even let a unit attack at peace, and **this task never justifies a declaration of war** — a scout is
  not worth a war, exactly as a missionary is not. If one is parked where we want to be, say so in the
  diary and route around it.

## How

- **Two or three attackers on the same scout, this turn** (`mass-on-contact`). One attacker trades, and
  the scout heals 5–10 a turn in the field and 20 inside a city.
- **Ranged first** — it takes no retaliation — **then cavalry** if it has to be finished at range 1.
  A scout has **3 movement**: chasing one with a Warrior or Swordsman is how a whole turn is thrown
  away, and a Scout, Builder or Trader sent after it is captured instead of killing it.
- **No chase.** At most one tile of movement to reach a shot. Out of reach this turn? Note it and let
  it come back — a scout that is being shot at is not scouting.
- **A wounded scout is a dead scout** (`finish-the-wounded`): at 20 HP or less and in range, it dies
  now rather than healing and returning.
- **Do not satisfy the checks cosmetically.** Firing at a distant galley or an archer's worth of
  nothing just to make `attacks_this_turn >= 1` true — while a wounded scout lives two tiles away — is
  the failure mode this task exists to prevent. Measured live at T84: a 9 HP barbarian scout at
  (55,34), our own Scout two tiles short because terrain ate its movement, and the operator reasoning
  about shooting galleys to satisfy the rule. If the scout cannot be reached this turn, the diary says
  so in one line; the check is satisfied by a stated reason, never by a wasted shot.
- **Report a convertible barbarian first.** If a barbarian scout stands adjacent to one of our melee
  units, write that in the diary before shooting — 三十六计 is a human action played from the game UI
  and it consumes the melee unit — then kill the scout anyway.

## When it is done

Retire this file when **three consecutive turns have passed with no hostile scout within three tiles**
of anything of ours — that is the pressure being over, and it is written as the `done when:` line so
the judgement is not a matter of taste. Move it to `../tmp/done/002-focus-fire-scouts-done-T<turn>.md`
and record in the diary's `tooling` line which scouts were killed, where, and with how many attackers.
At **turn 95** retire it regardless, as `002-focus-fire-scouts-expired-T95.md`, and say in the diary
whether any scout survived and why.

If this order has proved its worth by then, the right place for it is `prompts/tactics/02` as a
permanent rule rather than another temporary file — say so in the diary instead of re-adding it.
