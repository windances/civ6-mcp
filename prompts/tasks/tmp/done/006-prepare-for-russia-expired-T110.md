# TEMP TASK 006 — prepare to attack Russia

added:     2026-09-26 (human instruction: 为攻打俄罗斯做准备)
expires:   turn 110 — the preparation has a longer clock than the raid tasks; retire it by then
done when: the assault establishment exists — **siege >= 3, ranged >= 4, melee >= 2,
           cavalry >= 1** (no ram or tower — human instruction 2026-09-26: 不用锤，用投石车;
           the siege figure was 2 when this task expired at T110 and the human instruction
           of the same day, 一城3投石车, raised it to 3)
           — **and** Russia's nearest city has been read in four numbers (hp / walls /
           garrison / ring), **and** gold per turn is still about `+10` with the army counted
overrides: the per-city build lists and the Campus/Builder plan: siege units, and the units still
           missing from the establishment list, may be inserted ahead of them in the war city until
           the list is complete. It does **not** authorize a declaration of war — that stays behind
           `tactics/07`'s gates — and it does not touch research or civics.
scope:     preparation only: building, buying, mining, reconnaissance. No declaration, no attack on
           anybody, no peace offer (there is no war yet).

## What "prepared" means — the directive's own checklist

The directive's rule is that the decision to declare is the only decision that matters, and that its
trigger is a checklist rather than a turn number:

1. **a named target** whose walls and garrison can be broken in a bounded number of turns;
2. the **assault establishment already in place** — **3 siege per city** (一城3投石车), 2 melee, 4 ranged,
   1 cavalry, and **no ram or tower** — **before** the declaration, not queued after it;
3. **amenities positive** (war weariness decays 50/turn at war against 200 at peace, and 400 points
   cost an amenity, so a long war suppresses the production that pays for it);
4. **gold per turn about +10 or better** with the army counted.

## Where we are, measured (T90→T91, read from the game)

| Piece | Have | Check rule | Gap |
|---|---|---|---|
| siege | **0** | `siege-train` (fires from T90) | **3 needed (一城3投石车) — the binding gap** |
| ranged | 4 Archers | `ranged-mass` | satisfied; keep alive, upgrade to Crossbowmen at Machinery |
| melee | 3 Warriors + 1 Spearman | `melee-screen` | satisfied; Swordsmen need **iron** |
| ram / tower | **not part of this army** | — | human instruction 2026-09-26: 不用锤，用投石车 — the 1 Battering Ram we own is a garrison unit, and no tower is built |
| cavalry | **0** | — | 1 Horseman (Horseback Riding; horses 32/50) |
| iron | **0/50** | — | task 004's city, then mine (60,32) |
| gold | 159.6, **+28.4/t** | `carrying-capacity` | the army can roughly double before the gate is at risk |
| amenities | positive in all four cities | — | keep it that way into the war |

**Engineering has just completed**, which is the tech that unlocks the **Catapult**: 120 hammers to
build, about 480 gold to buy. That is the single most important purchase or build in the empire right
now, and `siege-train` is failing because of it.

## The order the gaps gate each other

1. **Find Russia before anything else — file 7 Step 0 is "a visible candidate city".** At T90 only
   **Egypt (a declared friend)** and Kabul are known, with six major civilizations unmet. An army in
   the right shape and a target in fog has no pre-war analysis to make. The abandoned branch of this
   same map found Moscow at **(54,40)** and 圣彼得堡 at **(56,43)** — 10–13 tiles south/south-west of
   长沙 — but **that is a search direction, not a fact**: read the map, and the moment contact lands use
   `get_deal_options(player_id)`, which hands over their city list with populations, which of them is
   their original capital, their strategic stockpiles and their gold per turn, with no open borders and
   no war. That is the target read for free.
2. **Two Catapults.** They are the only piece of the establishment that is entirely missing, and they
   are what makes a siege bounded: 45–52 damage a shot against a city, garrison or not (an Archer does
   9–11 against the same city when it holds a CS 35 garrison). Build them in the war city, or buy the
   first at ~480 gold once the treasury allows — gold runs +28/t, so that is roughly T95–T98 without
   touching anything else.
3. **Iron, then the melee line.** Swordsmen (CS 35) are gated on iron: 0 in the stockpile and none
   mined. Task 004 settles (60,32) and mines it; Iron Working's boost is that mine. The melee line is
   what walks into a city, so the siege train without it breaks cities it cannot take.
4. **One Horseman** for survivors and for enemy ranged and siege units: it needs Horseback Riding, and
   the horse stockpile is 32/50 with +2/t.
5. **The Catapults are the wall-breakers, not a ram.** Measured on the abandoned branch of this map:
   **every Russian city read `walls 0/0` from first contact to the last**, so the Battering Ram — 65
   hammers dragged across the map — did nothing for seventeen turns. The human instruction of
   2026-09-26 (不用锤，用投石车) settles it: **no ram and no tower**, the Catapult does 45–52 against a
   city whether or not it is garrisoned, and the melee walks in after the walls are down. Still read
   the target's walls before the declaration — the number decides how many siege shots the city needs,
   not which unit to build.
6. **Do not mass on the border to "be ready".** Measured T103 on the abandoned branch: massing is what
   started the war — Russia declared while our army was two turns short of its rally row. The staging
   discipline (`tactics/04`) puts the rally point where the army can already fight from, and file 7's
   gate 5 owns the declaration trigger.

## What this task is not

It is not a declaration and not a war. **A war you cannot finish is a war you must not start**, and the
preparation is finished when the establishment exists *and* the target has been read — not when the
army looks big. Do not attack Egypt (a declared friend), Kabul (a city-state, and our suzerainty), or a
barbarian camp as a substitute. Task 002 covers scouts; 003 covers exploration; 004 covers the iron;
005 is the copper city and is the lowest priority of the five.

## When it is done

When the establishment list is complete, Russia's nearest city has been read in four numbers, and
gold/turn is still about `+10`, move this file to
`../tmp/done/006-prepare-russia-done-T<turn>.md` and record in the diary's `tooling` line: the counts
(siege / ranged / melee / cavalry — no ram), the target city with its hp, walls, garrison and ring, the
iron stockpile, and gold per turn. Then the war decision belongs to `tactics/07` — not to this file.
At **turn 110** retire it regardless, as `006-prepare-russia-expired-T110.md`, and say which piece of
the establishment is still missing and why.
