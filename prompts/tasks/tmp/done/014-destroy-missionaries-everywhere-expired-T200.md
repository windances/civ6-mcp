# TEMP TASK 014 — destroy the missionaries, map-wide (全域消灭传教士)

added:     2026-09-26 (human instruction: 全域消灭传教士)
expires:   turn 200 — counted from the queue, not the calendar. The sweep itself is cheap (one
           `get_map_area` pass per turn over the cities and the units); what costs turns is the war
           that makes a kill **legal**, and the next war is not declared yet — 013 is still looking for
           its target and its own horizon is T195. T200 gives this file five turns past that and no
           more. If by T200 no hostile religious unit has been seen **and** no rival is near a
           religious victory, retire it as `014-destroy-missionaries-everywhere-expired-T200.md` with
           the zero count and the spread reading as the report.
done when: **no hostile religious unit is left anywhere we can see — `count == 0`** over a map-wide
           sweep (every city, every unit, and the roads between them) of MISSIONARY / APOSTLE /
           INQUISITOR belonging to a civ **we are at war with**, with every sighting recorded (type,
           owner, tile, turn) and every legal kill recorded with the tool's reply — **or** the file
           expires at T200 with the count and the reason it could not act (peace with every owner: the
           game refuses both `condemn` and `attack`).
overrides: nothing about gold or production — **013's earmark is untouched, and no religious unit is
           ever bought** (see scope). It authorizes **no declaration of war**: a war needs its own
           `tactics/07` analysis and its own file, and 007's rule that only a task may declare survives
           007's retirement. It authorizes **no chase** that pulls a unit off the front or off a
           garrison, and no movement of the five captured cities' garrisons.
scope:     every religious unit of a civ **we are at war with**, anywhere on the map — our territory,
           our roads, the fog, the far side of it. It is **not** about our own cities' conversion (no
           victory condition in this plan depends on China's religion), **not** about a city-state's or
           a friend's missionaries (at peace they cannot be condemned by tool or by human, and killing
           one is a diplomatic incident), and **not** a licence to build or buy religious units: a
           missionary carries the majority religion of the city it was bought in, and in China that is
           a foreign faith.

## The legal reality, which decides the whole shape of this task

| Situation | What the game does | Evidence |
|---|---|---|
| At peace, `condemn` an adjacent missionary | `ERR:REQUIRES_WAR` — the game's own refusal string is `LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION` | `src/civ_mcp/lua/units.py:1122` |
| At peace, `attack` one | `ERR:NOT_AT_WAR`; a **city strike** against one answers `NO_ENEMY` | directive's Foreign-missionaries bullets |
| Not adjacent, `condemn` | `ERR:NO_RELIGIOUS_TARGET` — "no Missionary, Apostle, Inquisitor or Guru within one tile". **The two attempts this game made were adjacency facts, not tool failures**: the unit was two tiles away | `units.py:1104`; 008's diary |
| **At war with the owner**, an adjacent military unit | `condemn` is **one command** — the engine picks the adjacent religious unit, so the reply names every candidate first; `attack` with an adjacent military unit also kills it | `units.py:1061-1122`; 008's verb |

So in peacetime this task is **surveillance**, and the kill is a war-time action. That is not a
compromise: it is what the engine allows, and pretending otherwise wastes the turn.

## The sweep — the peacetime half, and the only detector there is

1. **A religious unit is invisible to every metric the rules use.** It is `FORMATION_CLASS_RELIGIOUS`
   with `Combat = 0`, so the contact metrics (`enemies_within_1/2/3`, the class counts) never see it,
   and `use-your-attacks` cannot fire on it. It shows up in one place: **the tile's unit list** in
   `get_map_area`.
2. **So sweep on a schedule, map-wide.** `get_map_area` radius 2–3 around every city, around every
   unit that has moved, and along the roads between them; the 全域 half of this instruction is exactly
   that — not only our territory and not only the army's route, which was 008's narrower scope. Record
   **type, owner, tile, turn** and which way it is walking; a missionary that is ignored is a
   missionary that converts a city while nobody looks.
3. **Read the religion once every ~20 turns.** `get_religion_spread` is the only view of the actual
   threat: a rival religious victory, not one missionary. **The trigger to act is one civ holding a
   majority in every other civ**; anything short of that is noise, and conversion of our own cities is
   noise too, because nothing in this plan depends on China's religion.
4. **Report zero as a result.** `count == 0` with the tiles swept is a finding worth writing down. The
   T163–T174 sweeps of 成都, 圣彼得堡, the 喀山 approach and the 阿斯特拉罕 corridor found none, and 008
   retired at T165 with that zero count rather than pretending to have hunted something.

## The kill — the war-time half, and why it is a trap rather than a chase

1. **Mobile units only, and the extras take its neighbours.** A religious unit that sees the column
   steps away, so the units that can close are the ones with movement to spare (3+, and **cavalry
   ignores zones of control**), and the second and third units take its other adjacent tiles so it has
   nowhere to step. `get_staging_plan(kill_x, kill_y)` assigns exactly that job and only to mobile
   units — its `KILL` bucket exists for this.
2. **`condemn` is the cheap kill** — one command, no charges, from an adjacent military unit, and it
   removes the unit outright rather than damaging it. Verify adjacency with the reply before spending
   the turn: the failure mode is `ERR:NO_RELIGIOUS_TARGET` from two tiles away.
3. **One unit, no chase.** A missionary is never worth pulling a unit off the front or off a captured
   city's garrison; the front's job is a city that heals twenty points a turn, and this file's whole
   scope is a Combat-0 unit.
4. **The faith source beats the kill.** If a rival is actually closing on a religious victory, the
   thing worth a turn is the **Holy Site / Lavra that produces their faith** — pillaging it stops the
   stream, which is worth more than any number of individual missionaries.

## Why this is a file and not a turn-check rule

No metric can see it: the rule engine reads our diary row plus `end_turn`'s contact metrics, and those
count **military** classes, so a Combat-0 religious unit is invisible to every rule in
`prompts/checks/turn-checks.md`. The one checkable part — a legal attack left unused — is already
covered by `use-your-attacks` and needs no new rule. What no rule can express is the **objective**:
"the map has been swept and there is nothing left to condemn", which is why it is a file.

## Report when it is done

Every sighting (type, owner, tile, turn) and every kill with the tool's exact reply; the religion
spread reading with the turn; the tiles swept on the final pass; and, if it expires, the count, the
reason it could not act (peace with the owner), and whether any rival was within reach of a religious
victory when it did.

## Report — expired at T200 with a zero count

The count is **0**: no MISSIONARY, APOSTLE or INQUISITOR belonging to a civilisation we are at war with
was seen anywhere we could look over the sweep, so there was nothing to condemn and no kill to record.
The `expires:` line's own retirement condition — "no hostile religious unit has been seen **and** no
rival is near a religious victory" — held, and it is what closed the file: the `done when:`'s **second**
arm is exactly this path ("**or** the file expires at T200 with the count and the reason it could not
act"), which is why this record is `-expired-` rather than `-done-`. What cannot be reached is the
**first** arm, a whole-map sweep that *proves* the zero count: at peace a religious unit cannot be
touched at all (`condemn` answers `ERR:REQUIRES_WAR`), so a count of 0 only ever means "nothing
visible". The spread reading that came with it: **Hinduism (印度教) leads at 2/7
civilisations**, well short of the religious victory's majority in all of them, so no rival was within
reach when the file closed. The sweep itself, the sightings and the final reading are the T200 diary
entry.
