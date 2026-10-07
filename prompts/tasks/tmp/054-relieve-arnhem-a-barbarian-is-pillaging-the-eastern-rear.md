# TEMP TASK 054 - Relieve Arnhem: a barbarian is pillaging the eastern rear

added:     2026-10-08 (human instruction: 我们被野蛮人攻击，尽快支援，看看为什么没有执行军事策略里支援条款)
expires:   turn 393 - 3 turn(s) from T390, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 barbarian units within three tiles of (75,11) in get_units, and Arnhem's pillaged
           district is under repair in its queue or restored
overrides: the offensive tasks' claim on this turn's unit orders: a barbarian inside our territory and a city
           being pillaged comes first, and the front resumes the same turn the raider is dead
scope:     the armour and Spec Ops near (75,11), the nearest builder, and Arnhem's production queue for its
           pillaged districts; no new war, no peace, no change to the Georgian front's tasks

## Why this file exists

A barbarian is inside our territory and has already taken two tiles from a city: the notifications in
Chinese read "您在**阿纳姆**的农场遭到了野蛮人的掠夺" and "您位于**阿纳姆**的学院遭到了野蛮人的掠夺",
and the city read carries `- Improvement Pillaged at (75,11)`, `!! PILLAGED TILES: FARM`,
`!! PILLAGED: CAMPUS, ... LIBRARY, UNIVERSITY, RESEARCH_LAB`. Arnhem is at (75,11) and the raid is in
the eastern rear, where our own armour is standing two tiles away.

**Nothing carried this to the session** - that is the whole reason it went unanswered, and the
diagnosis is worth keeping:

- The clause that covers it is `prompts/tactics/03-under-attack.md` ("A city was attacked. Garrison
  it (one unit), repair the walls if they are down ..."), and **that file is read by the
  `military-map` advisor, not by the orchestrator's turn loop** - nothing in the loop opens it.
- `prompts/checks/turn-checks.md` has **no** camp or barbarian rule, and both
  `answer-the-camp.md` and `repair-the-pillaged-district.md` are still sitting in
  `prompts/checks/pending/` - **staged rules are not evaluated**, so the `!! PILLAGED` lines the
  city read was already printing never became a "must act".
- Every task in force is offensive (050 take the cities, 051 wake the rear guns, 053 the first
  volley); none of their scopes mentions home defence.
- A raid raises **no turn blocker**: `get_notifications` listed only the World Congress session and a
  promotion, so the turn never had to stop.

## Do this, this turn, before anything on the Georgian front

1. **Find it.** `get_map_area` around (75,11) (radius 2), and `get_units` - the raider is a barbarian
   unit in the open, not a walled city. Name it before you move: its type matters (a Camp is a tile
   with no HP and no walls; a Spearman is anti-cavalry).
2. **Kill it with what is already there.** Our armour is closer than anything else: Modern Armor at
   (73,13) (HP 61), Modern Armor at (76,12) (HP 56), Spec Ops at (78,13). A **melee** attack from
   armour is how a barbarian unit dies - do not leave it alive to pillage a third tile. If what is
   there is a **Camp**, one military unit moving onto its tile destroys it (no HP, no walls, no
   garrison bonus), and the tile is cleared for good.
3. **Repair what it took.** The farm at (75,11) needs the nearest builder (`get_builder_tasks`, then
   `improve`); the **district buildings** - Campus, Library, University, Research Lab - are repaired
   through `set_city_production` in Arnhem, not by a builder (`!! PILLAGED: ... (repair via
   set_city_production)`). Both halves belong to this task.
4. **Then the front.** 053's first volley and 051's march still happen this turn if the raider is
   dead and a builder is on its way. Home defence comes first; it does not cancel the war.

## Done when

`count == 0` barbarian units within three tiles of (75,11) in `get_units`, and Arnhem's pillaged
district is either under repair in its queue or already restored. Report the raider's type and tile
when you retire this file - if it was a Camp, say whether it respawned, because that is the half the
doctrine has never covered.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Relieve Arnhem: a barbarian is pillaging the eastern rear" --instruction 我们被野蛮人攻击，尽快支援，看看为什么没有执行军事策略里支援条款 --done-when "count == 0 barbarian units within three tiles of (75,11) in get_units, and Arnhem's pillaged district is under repair in its queue or restored" --overrides "the offensive tasks' claim on this turn's unit orders: a barbarian inside our territory and a city being pillaged comes first, and the front resumes the same turn the raider is dead" --scope "the armour and Spec Ops near (75,11), the nearest builder, and Arnhem's production queue for its pillaged districts; no new war, no peace, no change to the Georgian front's tasks" --why "relieve the city the barbarian is pillaging and repair what it took" --turns 3 --no-cn --body @.tmp/task054-body.txt
     at: 2026-10-08T02:41:50+08:00
     chinese backup: none (--no-cn)
-->
