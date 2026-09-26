# TEMP TASK 010 — rescue 成都 (Chengdu)

added:     2026-09-26 (human instruction: 救援成都)
expires:   turn 175 — a defensive task is counted from the attackers' clock, not the calendar:
           成都's Ancient Walls were ordered at T154 (3 turns), the levied Man-at-Arms was standing
           on our iron mine at (60,32) at T155, and a levy runs for 30 turns. Kill or drive both off,
           repair the mine, and retire this file early as `010-rescue-chengdu-done-T<n>.md`. If the
           siege is still on at T175, retire it as `010-rescue-chengdu-expired-T175.md` and say in
           one line what still stands and what it costs.
done when: no hostile unit is within 2 tiles of 成都 (60,31), 成都 reads `walls` >= 1 with a garrison
           on its tile, and the pillaged IRON mine at (60,32) is **no longer** pillaged. Report the
           turn each hostile unit died or left the ring, and the turn the mine was repaired.
overrides: **007's offensive timetable for the units this needs, and nothing else.** Unit survival
           comes before the war aim: a lost city is a re-siege (007 has one precedent — Moscow was a
           Free City four turns after it was taken, and retaking it cost nine attacks). It does **not**
           authorize peace with Russia (007 owns that), **does not** authorize pulling the siege train
           off 圣彼得堡 while that wall phase is running, and **does not** authorize attacking Yerevan
           itself — the targets are the two units, not the city-state.
scope:     成都 (60,31) and its first ring, including the iron mine at (60,32). The enemy in practice
           is **Yerevan's levied units**: Yerevan is Russia's suzerain city-state, so a levied
           Man-at-Arms (CS 45) and a levied Horseman are fighting Russia's war by proxy. They are
           legal targets (we are at war with Russia); Yerevan is not, and taking it advances no
           victory condition. Nothing else in prompts/tasks/tmp/ is relaxed.

## What is measured, and the last coordinates seen

| Fact | Reading | Where |
|---|---|---|
| 成都 | 200/200 HP, no walls until ~T157, a Warrior moved in as garrison at T155 | T154–T155 diary |
| levied Man-at-Arms, CS 45 | on our IRON mine at (60,32) at T155, and it **pillaged it** | T155 diary |
| levied Horseman | 1 HP at (61,32) at T154 (was 52 HP at (61,32) at T153) | T153–T154 diary |
| why the mine matters | Iron is the upgrade resource for the war (`match-their-melee`, Swordsman→Man-at-Arms); a pillaged mine stops the stream | directive, measured T155 |

**Re-read all four before acting — those coordinates are one to three turns old** and a levied unit
moves. `get_map_area` radius 2 around (60,31) and `get_units`, then decide.

## How to fight it, in the order that costs least

1. **The city is a weapon.** Once the walls are up, 成都 fires at range 2 with
   `city_action(city_id, "attack", x, y)`. The Man-at-Arms standing on the mine at (60,32) is
   distance 1 from the city: that is a free shot every turn, and it is the cheapest damage in the
   empire. Before the walls land the city is only a target, so do not sortie to defend it.
2. **Do not trade a Warrior with a CS 45 Man-at-Arms.** The garrison's job is to hold the tile and
   to be the reason the city cannot be entered; a Warrior (CS 20) attacking out of the gate loses
   that trade. The kill belongs to ranged units and to the city's own strike.
3. **`finish-the-wounded` on the 1 HP Horseman.** A wounded unit heals 5/turn in *our* territory
   (enemy territory to them, `manual:1066-1085`) and comes back — but at 1 HP it dies to any single
   ranged attack, and leaving it alive is how a two-unit raid becomes a three-unit one. Kill it the
   turn you can.
4. **Attack from range, or attack before moving — never move-then-attack into contact.** Measured
   T155: a Warrior that stepped beside the Horseman answered `ZOC|Unit entered Zone of Control this
   turn — cannot attack until next turn`. A ranged attack costs movement too, so **order every attack
   before every move**; and `skip_remaining_units` now refuses to discard one (it names the unit).
5. **The mine cannot be repaired under the enemy.** Take the tile back (or kill the unit on it) first,
   then `unit_action(action="repair")` with a Builder on (60,32) — it needs no improvement argument
   and prints `REPAIRING|IMPROVEMENT_MINE at (x,y)`.
6. **Spend only what the defense needs, and name it.** Gold was ~56–95 and rising ~+16/turn: if the
   city would actually fall, buying one ranged unit is cheaper than losing the city, and that is a
   recorded decision, not a reflex. Do not buy a Builder or a district while the ring is hostile.
7. **Keep the war where it is.** 圣彼得堡 is stalled because only one Trebuchet is in range and the
   city heals ~20/turn; that front needs the siege train, not fewer units. If a unit must come east,
   take it from the *reinforcement* column (the second Man-at-Arms walking south, a spare
   Crossbowman), never from the wall phase — and say in the diary which unit and from where.

## Why this is a file and not a turn-check rule

The rules already cover the parts that have metrics — `finish-the-wounded`, `use-your-attacks`,
`hold-what-you-take`, `one-garrison-per-city` — and they fired correctly on this raid. What no rule
expresses is the *priority*: that a city state's levied proxy attack outranks the offensive timetable
for exactly as long as it takes to lift, and that the mine under it is a war resource rather than
scenery. That judgement is what this file carries.

## Report when it is done

One line each: the turn the walls completed, which unit killed each of the two attackers (or the turn
they left), the turn the Warrior arrived as garrison, and the turn the mine was repaired. If the
attackers are still there at expiry, say what holds 成都, what the mine costs us, and whether the
Yerevan levy is still feeding them.
