# TEMP TASK 003 — two scouts out, and find more civilizations

added:     2026-09-26 (human instruction: 派出两个侦察兵，探索地图，找到更多文明)
expires:   turn 95 — retire this file by then whatever happens
done when: two SCOUTs are alive and under exploration orders, and >= 2 major civilizations are met
           (the `has_met` count in `get_diplomacy` — it was **1** when this file was added, Egypt) —
           or turn 95, whichever comes first
overrides: whatever per-city build list is running: a **Scout (30 hammers)** may be inserted ahead of
           the next Builder or Campus in **one** city, and the existing Scout may not be disbanded,
           garrisoned or used as a sentry. Nothing else in the plan changes.
scope:     exploration only. No declaration of war, no fighting with the scouts (they are CS 10 and die
           to anything), no change to research or civics, and no military unit pulled off its post.

## Why this is not a side quest

Exploration is the binding prerequisite for half of this game's plan and nobody can buy it later.
Measured at T83: **1 of 7 major civilizations met** (Egypt, a declared friend), 45 tiles of territory,
and a conquest doctrine that cannot even be scoped — `tactics/07` Step 0 asks for a *visible candidate
city*, and with six rivals unmet there is no rival capital on the map to analyse. Every gate in that
file is unevaluable while the map is dark.

Two more things ride on first contact, and both are worth the 30 hammers:

- **Era score.** T83 sits at **27 against a Dark Age floor of 28** — one point short. Meeting a new
  civilization is a historic moment; so is the first envoy and the first wonder. A scout is the
  cheapest era score in the game right now.
- **The cheapest reconnaissance there is.** `get_deal_options(player_id)` hands over a met
  civilization's city list with populations, which city is its original capital, its strategic and
  luxury stockpiles and its gold per turn — with no open borders, no scout reaching anything, and no
  war. That is `tactics/07` Step 0 answered for free, and it needs a contact first.

## What to do

1. **Get the second Scout.** Build it (30 hammers — about 2 turns in 西安) or buy it (~120 gold; the
   treasury was 76 at +28/t, so affordable around T85). The empire had exactly **one** SCOUT at T83
   (1 Scout, 3 Warriors, 4 Archers, 3 Builders, 1 Trader).
2. **Send them different ways.** One per unexplored direction — do not run both down the same lane.
   Pick the two largest fog boundaries within reach (the north/north-east and the west/south-west were
   the dark quadrants at T83) and split them.
3. **`automate` by default, but read the reveal every turn.** Automation keeps a scout moving without
   spending the turn's attention; it is not a reason to stop looking. If a scout has been circling, is
   standing still, or is walking back through ground it already uncovered, give it a direction instead.
4. **Keep them alive.** A Scout is CS 10 — a single barbarian Warrior removes it, and a lost scout is
   several turns of information plus the 30 hammers. Route around barbarians, do not enter a tile a
   barbarian can reach next turn, and pull back to friendly ground when a barbarian closes. Do not
   escort them with the army and do not send a Builder or Trader along.
5. **On first contact, bank everything it gives.** Report in the diary: who, where, what the contact
   revealed, and whether it was a major civilization or a city-state. Send a **delegation (25 gold)**
   on the first meeting of a major civ. Then call `get_deal_options` for the city list and write down
   their capital and their strategic stockpiles — that is pre-war reconnaissance under `tactics/07`
   Step 0, and it costs nothing.
6. **Do not start anything with them.** First contact is information, not a war: no declaration, no
   aggression, no demand. The directive's rule stands — a war you cannot finish is a war you must not
   start, and the point of finding rivals now is to know which of them is worth planning against later.

## When it is done

When two Scouts are alive and exploring **and** a second major civilization has been met, move this
file to `../tmp/done/003-two-scouts-explore-done-T<turn>.md` and record in the diary's `tooling` line
which civilizations were met, on which turn, by which scout, and what `get_deal_options` revealed. At
**turn 95** retire it regardless, as `003-two-scouts-explore-expired-T95.md`, and say in the diary how
much of the map is still dark and which rival capitals are still unfound.
