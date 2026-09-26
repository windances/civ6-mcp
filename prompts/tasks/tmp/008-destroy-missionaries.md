# TEMP TASK 008 — destroy the missionaries

added:     2026-09-26 (human instruction: 消灭传教士)
expires:   turn 185 — **extended at T160 with 007, whose horizon this file explicitly borrows**
           ("its `expires` is 007's"). The extension is not a claim that missionaries are still a
           problem: repeated `get_map_area` sweeps of 成都, 圣彼得堡, the 喀山 approach and the
           阿斯特拉罕 corridor through T160 have shown **no hostile religious unit at all**, and the
           `condemn` verb has therefore never had a legal target to exercise. The file stays in force
           so that the sweep keeps happening while the war is on and so the tool's answer can still
           be recorded the first time a Russian missionary does appear; if none appears by T185 it
           retires as `008-destroy-missionaries-expired-T185.md` with that zero count as the report.
           Retire it early once no hostile religious unit is left anywhere we can see, or as
           `008-destroy-missionaries-expired-T185.md` with a count of what was killed and what is
           still walking around.
done when: **no hostile religious unit stands in our territory or on a road the army uses** — a
           `get_map_area` sweep of our cities, the 阿斯特拉罕 approach and the roads between them shows
           `count == 0` of MISSIONARY / APOSTLE / INQUISITOR belonging to a civ we are at war with —
           and the tool's answer to the `condemn` is recorded either way (see below).
overrides: the march and the city queues: a unit adjacent to a hostile religious unit may spend its
           attack on it instead of moving, and 007's staging tolerates a one-turn delay for that. It
           does **not** authorize a declaration of war on anybody (007 owns that), and it does **not**
           authorize killing the religious units of a civ we are at peace with — Egypt is a declared
           friend, and a condemned missionary is a diplomatic incident.
scope:     hostile religious units only: Missionaries first, Apostles and Inquisitors if they are the
           ones in the way. No city attacks, no pillaging, no change to research or civics, no peace
           offer, and nothing done to our own religious units (we have none — religion is `NONE`).

## Why this is a file and not a turn-check rule

There is no metric for "a religious unit is standing there": `metric()` reaches our own diary row plus
the combat metrics, and those count **military** classes (`enemies_melee_within_2` and friends). A
Missionary is `FORMATION_CLASS_RELIGIOUS` with `Combat = 0`, so it is invisible to every rule — and a
religious unit parked on a one-tile lane is exactly the thing that cost this campaign two turns before
(a Russian Missionary at (57,32) and an Egyptian Scout at (58,32) closed the x=57 corridor at T101).
The instruction therefore lives here, and the checkable part (the `use-your-attacks` rule) already
exists once a legal attack exists.

## What the tool can and cannot do — verified in the game's own files

`unit_action(action="condemn", unit_id=…)` implements this (added 2026-09-26, live at the next MCP
start). It is the game's own **command**, not an attack:

* the command is `UNITCOMMAND_CONDEMN_HERETIC` (`Base/Assets/Gameplay/Data/UnitCommands.xml`);
* the game issues it as `UnitManager.RequestCommand(unit, UnitCommandTypes.CONDEMN_HERETIC)` and
  pre-checks it with `UnitManager.CanStartCommand(unit, command, nil, true)` — the same pair the
  game's own UnitPanel uses (`UnitPanel.lua:419`);
* **there is no target parameter**: the engine picks the adjacent religious unit, so the tool prints
  every candidate it can see before it fires;
* and **the game itself requires a war declaration** — its own refusal string is
  `LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION`: "A Religious unit in this tile belongs
  to a player you are not at war with."

So the honest position: **a missionary of a civ we are at peace with cannot be destroyed — not by
this tool, not by a human playing the same game.** `attack` reaches the unit but refuses with
`ERR:NOT_AT_WAR` (`src/civ_mcp/lua/units.py:411`), and `condemn` answers `ERR:REQUIRES_WAR` for the
same reason. The case this task serves is the war: Russian religious units once 007 declares.

1. **Use `condemn` on the first hostile religious unit adjacent to one of our military units** and
   copy the reply into the diary's `tooling` line:
   * `CONDEMNED|… | tile (x,y) now empty` → the kill, confirmed by a re-read of the tile.
   * `CONDEMNED|… | STILL THERE: …` → the request went out but the engine still shows the unit;
     re-read next turn before assuming anything.
   * `ERR:REQUIRES_WAR` → we are at peace with the owner; 007's declaration is the unlock.
   * `ERR:NO_RELIGIOUS_TARGET` / `ERR:CANNOT_CONDEMN` → nothing adjacent, or the engine will not
     start the command (already acted, no charges left).
2. **Russia first.** Once 007's declaration is sent, Russian religious units are legal targets.
3. **Do not touch Egypt's or a city-state's.** A friend's missionary cannot be condemned anyway.

## The order of work

1. **Find them.** A religious unit shows up in `get_map_area` (units on the tile) and in `get_units`
   if it is ours, but **not** in the BATTLE ASSESSMENT counts — so the sweep is the map read around
   each city, the 阿斯特拉罕 approach and the corridor roads, once every few turns while this is in
   force. They walk; a clean sweep last turn says nothing about this turn.
2. **Kill the one in the way, not the one that is convenient.** Priority is a missionary that blocks a
   lane the army or a Builder needs, or that stands inside our territory; a missionary wandering in
   open ground far from the route can wait.
3. **Attack with an adjacent military unit**, from the tile that does not expose it (a missionary of a
   civ we are at war with may have an escort — check `get_map_area` radius 1 before spending the
   attack, and prefer a ranged unit at range 1-2, which takes no retaliation).
4. **Record it**: unit type, owner, tile, turn, and the exact tool reply — including a refusal. A
   refusal recorded is worth more than a kill unrecorded, because it is what tells the next session
   whether the tool can do this at all.
5. **Then back to 007.** This task never postpones the war: it is a lane-clearing chore that rides
   along with it, and its `expires` is 007's.

## What this task is not

Not a religious strategy: we have no religion (`religion: NONE`, 0 cities converted) and this task
does not ask for one — it is about the missionaries that are in the way, not about spreading or
defending a faith. It is not a licence to attack Egypt, a city-state, or a barbarian unit, and it is
not a reason to leave the siege train unscreened while a unit goes hunting.
